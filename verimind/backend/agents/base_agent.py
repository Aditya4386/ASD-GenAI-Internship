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
        return (
            RunnablePassthrough()
            | self.get_prompt()
            | self.llm
            | StrOutputParser()
        )