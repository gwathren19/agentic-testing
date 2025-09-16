from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_community.llms import LlamaCpp
from dotenv import load_dotenv

from tester.runtime.runtime import Runtime
import tester.tools.basic_tools.basic_tools as basic_tools
from tester.utils.logger import logger
from tester.utils.config import config

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class Agent:
    def __init__(self):
        load_dotenv()
        self.runtime = Runtime()    

        if config.agent.source == "GOOGLE":
            self.llm = ChatGoogleGenerativeAI(model=config.agent.google_model, temperature=0)
        elif config.agent.source == "OPENAI":
            self.llm = ChatOpenAI(model=config.agent.openai_model, temperature=0)
        elif config.agent.source == "LOCAL":
            self.llm = LlamaCpp(model_path=config.agent.model_path, n_ctx=2048, n_threads=8, temperature=0.2)
        else:
            raise ValueError(f"Unsupported AGENT_SOURCE: {config.agent.source}")

    def build_graph(self) -> StateGraph:
        tools = basic_tools.create_tools(self.runtime)
        
        llm = self.llm.bind_tools(tools)

        def routing_condtion(state: AgentState) -> str:
            last = state["messages"][-1]
            
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tools"
            
            if last.type == "ai":
                content = last.content.strip().lower()
                if "assessment complete" in content or "no more actions" in content:
                    return "__end__"
                else:
                    return "agent"
            return "agent"

        def call_model(state: AgentState) -> AgentState:
            logger.info(f"Calling LLM with messages: {state['messages']}")
            response = llm.invoke(state["messages"])
            return {"messages": state["messages"] + [response]}

        def human_tool_review(state: AgentState) -> AgentState:
            tool_calls = [m for m in state["messages"] if m.type == "ai"][-1].tool_calls
            if not tool_calls:
                return state

            tool_call = tool_calls[0]
            print(f"\nProposed tool call: {tool_call}\n")

            action = input("Approve this call? [y/n/edit]: ").strip().lower()

            if action == "y":
                print("Approved")
                return state

            elif action == "edit":
                print("Current args:", tool_call["args"])
                for k, v in tool_call["args"].items():
                    new_val = input(f"Enter new value for '{k}' (or press Enter to keep '{v}'): ")
                    if new_val:
                        tool_call["args"][k] = new_val
                state["messages"][-1].tool_calls[0] = tool_call
                print("Edited and approved")
                return state

            else:
                print("Rejected - skipping tool execution")
                state["messages"][-1].tool_calls = []
                return state


        workflow = StateGraph(AgentState)

        workflow.add_node("agent", call_model)
        workflow.add_node("human_tool_review", human_tool_review)
        workflow.add_node("tools", ToolNode(tools))
        
        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            routing_condtion,
            {"tools": "human_tool_review", "agent": "agent", "__end__": END},
        )
        workflow.add_edge("human_tool_review", "tools")
        workflow.add_edge("tools", "agent")

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