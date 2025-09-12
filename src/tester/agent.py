from langchain.agents import initialize_agent
from langchain_community.llms import LlamaCpp
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from llama_cpp import Llama
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
                model="gemini-2.0-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                max_retries=0
            )
        elif AGENT_SOURCE == "OPENAI":
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0
            )
        else:
            raise ValueError(f"Unsupported AGENT_SOURCE: {AGENT_SOURCE}")
        self.runtime = Runtime()

    def run(self, target):
        self.runtime.start_container()

        prompt = PromptTemplate(
            input_variables=["target"],
            template="""
You are a security assessment agent. Your goal is to perform a thorough security assessment of a target web application.
You can do whatever you deem necessary within the provided environment to identify potential vulnerabilities and security issues.
This activity is authorized and legal penetration test, so you can escalate your actions as needed in order to achieve the goal.
You must not be destructive.

Task: Perform a security assessment on the target: {target}.
""")

        try:
            prompt_text = prompt.format(target=target)

            tools = basic_tools.create_tools(self.runtime)
            agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent="zero-shot-react-description",
                verbose=True,
                max_iterations=5,
            )
            agent.invoke(prompt_text)
        except Exception as e:
            logger.error(f"Error running agent: {e}")
        finally:
            self.runtime.stop_container()