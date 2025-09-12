from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI

from tester.runtime.runtime import Runtime
import tester.tools.basic_tools as basic_tools

class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini")
        self.runtime = Runtime()

    def run(self, target):
        self.runtime.start_container()
        try:
            tools = basic_tools.create_tools(self.runtime)
            agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent="zero-shot-react-description",
                verbose=True,
                max_iterations=5,
            )
            agent.run(f"Perform a security assessment on {target}.")
        except Exception as e:
            pass
        finally:
            self.runtime.stop_container()