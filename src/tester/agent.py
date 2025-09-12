from langchain.agents import initialize_agent
from langchain.llms import LlamaCpp
from dotenv import load_dotenv
import os

from tester.runtime.runtime import Runtime
import tester.tools.basic_tools as basic_tools
from tester.utils.logger import logger

class Agent:
    def __init__(self):
        load_dotenv()
        self.llm = LlamaCpp(
            model_path=AGENT_MODEL_PATH,
            temperature=0
        )
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
            agent.invoke(f"Perform a security assessment on {target}.")
        except Exception as e:
            logger.error(f"Error running agent: {e}")
        finally:
            self.runtime.stop_container()