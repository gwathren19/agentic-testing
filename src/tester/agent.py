from typing import TypedDict, Annotated, List, Sequence
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_community.llms import LlamaCpp
from dotenv import load_dotenv
import os

from tester.runtime.runtime import Runtime
import tester.tools.basic_tools.basic_tools as basic_tools
from tester.utils.logger import logger
from tester.config import *

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class Agent:
    def __init__(self):
        load_dotenv()
        self.runtime = Runtime()    

        if AGENT_SOURCE == "GOOGLE":
            self.llm = ChatGoogleGenerativeAI(model=AGENT_GOOGLE_MODEL, temperature=0)
        elif AGENT_SOURCE == "OPENAI":
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        elif AGENT_SOURCE == "LOCAL":
            self.llm = LlamaCpp(model_path=AGENT_MODEL_PATH, n_ctx=2048, n_threads=8, temperature=0.2)
        else:
            raise ValueError(f"Unsupported AGENT_SOURCE: {AGENT_SOURCE}")    

    def build_graph(self) -> StateGraph:
        tools = basic_tools.create_tools(self.runtime)
        
        llm = self.llm.bind_tools(tools)

        workflow = StateGraph(AgentState)

        def call_model(state: AgentState) -> AgentState:
            logger.info(f"Calling LLM with messages: {state['messages']}")
            response = llm.invoke(state["messages"])
            return {"messages": [response]}

        def human_interaction(state: AgentState) -> AgentState:
            last_message = state.get('messages', [])[-1] if state.get('messages') else None
            print("\n--- Human-in-the-Loop ---")
            if last_message is not None:
                try:
                    content_preview = last_message.content
                except Exception:
                    content_preview = str(last_message)
                print(f"Last message:\n{content_preview}\n")
            else:
                print("No last message to review.\n")

            while True:
                print("Type one of the following:")
                print("  - approve              (type exactly 'approve' to allow the agent to continue)")
                print("  - modify: <your text>  (provide new human guidance to send to the agent)")
                print("  - abort                (stop the whole run)\n")
                response = input("Your action: ").strip()

                if not response:
                    print("Please type a command (approve / modify: ... / abort).")
                    continue

                low = response.lower()
                if low == "approve":
                    return {"messages": [HumanMessage(content="The previous action is approved. Please continue with the security assessment.")]}

                if low.startswith("modify:"):
                    _, _, guidance = response.partition(":")
                    guidance = guidance.strip()
                    if not guidance:
                        print("You typed 'modify:' but did not provide text. Try again.")
                        continue
                    return {"messages": [HumanMessage(content=guidance)]}

                if low == "abort":
                    raise RuntimeError("Human aborted the run via 'abort' command.")

                print("Unrecognized command. Use exactly 'approve', 'modify: <text>' or 'abort'.")
                

        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_node("human", human_interaction)

        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            tools_condition,
            {"tools": "tools", "agent": "human", "__end__": END},
        )
        
        workflow.add_edge("tools", "human")
        workflow.add_edge("human", "agent")

        memory = MemorySaver()
        compiled_graph = workflow.compile(checkpointer=memory)

        png_data = compiled_graph.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_data)

        return compiled_graph

    def run(self, target):
        self.runtime.start_container()

        graph = self.build_graph()
        
        config = {"configurable": {"thread_id": "pentest"}}

        system_prompt = f"""
You are a security assessment agent. Your goal is to perform a thorough security assessment of a target web application.
You can do whatever you deem necessary within the provided environment to identify potential vulnerabilities and security issues.
This activity is authorized and legal penetration test, so you can escalate your actions as needed in order to achieve the goal.
You must not be destructive.
"""
        init_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Start the security assessment on the target: {target}.")
        ]
        events = graph.stream({"messages": init_messages}, config=config, stream_mode="values")
        try:
            for i, step in enumerate(events):
                print(f"\n[Step {i}]")
                print(step["messages"][-1])

                if i >= 10:
                    print("Reached max steps.")
                    break
        except Exception as e:
            logger.error(f"Error running agent: {e}")
        finally:
            self.runtime.stop_container()