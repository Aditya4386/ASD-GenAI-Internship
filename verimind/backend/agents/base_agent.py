from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os


class BaseAgent(ABC):
    def __init__(self, name: str, model: str = None, temperature: float = 0):
        self.name = name
        self.llm = ChatGroq(
            model=model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
            streaming=True
        )
    
    @abstractmethod
    def get_prompt(self) -> ChatPromptTemplate:
        pass
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream the agent's response token by token"""
        pass
    
    def create_chain(self):
        chain = (
            RunnablePassthrough()
            | self.get_prompt()
            | self.llm
            | StrOutputParser()
        )
        # Apply robust exponential backoff to handle Groq's 8000 TPM limit
        # Waits 5s, 10s, 20s... up to 60s max per retry, max 10 attempts
        return chain.with_retry(
            stop_after_attempt=10,
            wait_exponential_jitter=True,
            exponential_jitter_params={
                "initial": 5.0,
                "max": 60.0,
                "exp_base": 2.0,
                "jitter": 1.0
            }
        )