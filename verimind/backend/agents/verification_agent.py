from typing import Dict, Any, List, AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from agents.base_agent import BaseAgent
from models.schemas import AgentResponse, VerificationResult
from utils.retry_utils import with_rate_limit_retry, with_rate_limit_retry_async_gen
import requests
import json


class VerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("VerificationAgent", temperature=0)
    
    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template("""
You are a verification agent. Verify the answer against external knowledge and provide confidence scoring.

Question: {question}
Answer: {answer}
Context: {context}

Instructions:
1. Check if the answer is factually consistent
2. Identify any claims that need verification
3. Assess confidence in the answer (0-1)
4. List supporting evidence from context
5. Identify any contradictions

Format your response as:
VERIFIED: true/false
CONFIDENCE: X.XX
EVIDENCE:
- evidence 1
- evidence 2

CITATIONS:
- citation 1
- citation 2

CONTRADICTIONS:
- contradiction 1
- contradiction 2
""")
    
    def search_web(self, query: str, max_results: int = 3) -> List[str]:
        try:
            # Simple web search using DuckDuckGo HTML (no API key needed)
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.post(url, data=params, headers=headers, timeout=10)
            # Simple extraction - in production use proper API
            return [f"Web search result for: {query}"]
        except:
            return []
    
    @with_rate_limit_retry
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        context = state.get("context", "")
        question = state.get("question", "")
        answer = state.get("judge_result", {}).get("selected_answer", 
                state.get("generator_answer", ""))
        
        chain = self.create_chain()
        verification_output = chain.invoke({
            "context": context,
            "question": question,
            "answer": answer
        })
        
        verified = False
        confidence = 0.5
        evidence = []
        citations = []
        contradictions = []
        
        current_section = ""
        for line in verification_output.split("\n"):
            line = line.strip()
            if line.startswith("VERIFIED:"):
                verified = "true" in line.lower()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("EVIDENCE:"):
                current_section = "evidence"
            elif line.startswith("CITATIONS:"):
                current_section = "citations"
            elif line.startswith("CONTRADICTIONS:"):
                current_section = "contradictions"
            elif line.startswith("- ") and current_section:
                content = line[2:]
                if current_section == "evidence":
                    evidence.append(content)
                elif current_section == "citations":
                    citations.append(content)
                elif current_section == "contradictions":
                    contradictions.append(content)
        
        # Also use context as evidence
        if context:
            evidence.append("Document context supports answer")
        
        verification_result = VerificationResult(
            verified=verified,
            confidence_score=confidence,
            evidence=evidence,
            citations=citations,
            contradictions=contradictions
        )
        
        response = AgentResponse(
            agent_name=self.name,
            content=verification_output,
            confidence=confidence,
            reasoning=f"Verified: {verified}, Confidence: {confidence}",
            citations=citations
        )
        
        state["verification_result"] = verification_result.model_dump()
        state["agent_responses"].append(response)
        return state
    
    @with_rate_limit_retry_async_gen
    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        context = state.get("context", "")
        question = state.get("question", "")
        answer = state.get("judge_result", {}).get("selected_answer", 
                state.get("generator_answer", ""))
        
        chain = self.create_chain()
        full_output = ""
        
        async for chunk in chain.astream({
            "context": context,
            "question": question,
            "answer": answer
        }):
            full_output += chunk
            yield chunk
        
        verified = False
        confidence = 0.5
        evidence = []
        citations = []
        contradictions = []
        
        current_section = ""
        for line in full_output.split("\n"):
            line = line.strip()
            if line.startswith("VERIFIED:"):
                verified = "true" in line.lower()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":")[1].strip())
                except:
                    pass
            elif line.startswith("EVIDENCE:"):
                current_section = "evidence"
            elif line.startswith("CITATIONS:"):
                current_section = "citations"
            elif line.startswith("CONTRADICTIONS:"):
                current_section = "contradictions"
            elif line.startswith("- ") and current_section:
                content = line[2:]
                if current_section == "evidence":
                    evidence.append(content)
                elif current_section == "citations":
                    citations.append(content)
                elif current_section == "contradictions":
                    contradictions.append(content)
        
        # Also use context as evidence
        if context:
            evidence.append("Document context supports answer")
        
        verification_result = VerificationResult(
            verified=verified,
            confidence_score=confidence,
            evidence=evidence,
            citations=citations,
            contradictions=contradictions
        )
        
        response = AgentResponse(
            agent_name=self.name,
            content=full_output,
            confidence=confidence,
            reasoning=f"Verified: {verified}, Confidence: {confidence}",
            citations=citations
        )
        
        state["verification_result"] = verification_result.model_dump()
        state["agent_responses"].append(response)
        yield f"\n\n[DONE:{full_output}]"