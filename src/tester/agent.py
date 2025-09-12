from langchain.agents import initialize_agent
from langchain.llms import LlamaCpp
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

from tester.runtime.runtime import Runtime
import tester.tools.basic_tools as basic_tools
from tester.utils.logger import logger
from tester.config import *

class Agent:
    def __init__(self):
        load_dotenv()
        if AGENT_SOURCE == "LOCAL":
            self.llm = LlamaCpp(
                model_path=AGENT_MODEL_PATH,
                temperature=0
            )
        elif AGENT_SOURCE == "GOOGLE":
            self.llm = ChatGoogleGenerativeAI(
                temperature=0,
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                max_retries=1
            )
        elif AGENT_SOURCE == "OPENAI":
            from langchain.chat_models import ChatOpenAI
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported AGENT_SOURCE: {AGENT_SOURCE}")
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