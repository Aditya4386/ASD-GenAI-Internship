from typing import Dict, Any, List, TypedDict, AsyncGenerator
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.reasoning_agents import AnswerGeneratorAgent, DebateAgent, CriticAgent, JudgeAgent
from agents.verification_agent import VerificationAgent
from rag.processor import DocumentProcessor
from models.schemas import AgentResponse


class AgentState(TypedDict):
    question: str
    context: str
    generator_answer: str
    debate_result: Dict[str, Any]
    critic_result: Dict[str, Any]
    judge_result: Dict[str, Any]
    verification_result: Dict[str, Any]
    agent_responses: List[AgentResponse]
    use_agents: bool


class MultiAgentGraph:
    def __init__(self, doc_processor: DocumentProcessor):
        self.doc_processor = doc_processor
        self.generator = AnswerGeneratorAgent()
        self.debate = DebateAgent()
        self.critic = CriticAgent()
        self.judge = JudgeAgent()
        self.verifier = VerificationAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("generate", self._generate_answer)
        workflow.add_node("debate", self._run_debate)
        workflow.add_node("critic", self._run_critic)
        workflow.add_node("judge", self._run_judge)
        workflow.add_node("verify", self._run_verification)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_conditional_edges(
            "generate",
            self._should_use_agents,
            {"agents": "debate", "skip": "verify"}
        )
        workflow.add_edge("debate", "critic")
        workflow.add_edge("critic", "judge")
        workflow.add_edge("judge", "verify")
        workflow.add_edge("verify", END)
        return workflow.compile(checkpointer=MemorySaver())

    def _should_use_agents(self, state: AgentState) -> str:
        return "agents" if state.get("use_agents", True) else "skip"

    def _retrieve_context(self, state: AgentState) -> AgentState:
        context = self.doc_processor.get_context(state["question"], k=3)
        return {**state, "context": context}

    def _generate_answer(self, state: AgentState) -> AgentState:
        return self.generator.process(state)

    def _run_debate(self, state: AgentState) -> AgentState:
        return self.debate.process(state)

    def _run_critic(self, state: AgentState) -> AgentState:
        return self.critic.process(state)

    def _run_judge(self, state: AgentState) -> AgentState:
        return self.judge.process(state)

    def _run_verification(self, state: AgentState) -> AgentState:
        return self.verifier.process(state)

    def run(self, question: str, use_agents: bool = True, thread_id: str = "default") -> Dict[str, Any]:
        initial_state = AgentState(
            question=question,
            context="",
            generator_answer="",
            debate_result={},
            critic_result={},
            judge_result={},
            verification_result={},
            agent_responses=[],
            use_agents=use_agents
        )
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(initial_state, config)

    async def run_stream(self, question: str, use_agents: bool = True) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream only pipeline STATUS events (started / completed per agent).
        No token-by-token streaming — this keeps the frontend simple and avoids
        displaying raw markdown during generation.
        A single 'complete' event with the full structured answer is emitted at the end.
        """
        start_time = time.time()

        # ── Retrieve ─────────────────────────────────────────────────────────
        yield {"stage": "retrieve", "status": "started", "message": "Retrieving relevant context..."}
        context = self.doc_processor.get_context(question, k=3)
        yield {"stage": "retrieve", "status": "completed"}

        state: Dict[str, Any] = {
            "question": question,
            "context": context,
            "generator_answer": "",
            "debate_result": {},
            "critic_result": {},
            "judge_result": {},
            "verification_result": {},
            "agent_responses": [],
            "use_agents": use_agents
        }

        # Choose which agents to run
        if use_agents:
            agents = [
                ("generate", self.generator, "AnswerGenerator", "Generating initial answer..."),
                ("debate",   self.debate,    "DebateAgent",     "Analyzing agreements & disagreements..."),
                ("critic",   self.critic,    "CriticAgent",     "Checking for issues & hallucinations..."),
                ("judge",    self.judge,     "JudgeAgent",      "Selecting the best answer..."),
                ("verify",   self.verifier,  "VerificationAgent","Fact-checking & scoring confidence..."),
            ]
        else:
            agents = [
                ("generate", self.generator, "AnswerGenerator",  "Generating answer..."),
                ("verify",   self.verifier,  "VerificationAgent","Verifying answer..."),
            ]

        # ── Run each agent, emit only started / completed ────────────────────
        for stage, agent, agent_name, message in agents:
            yield {"stage": stage, "status": "started", "agent": agent_name, "message": message}
            try:
                # Consume the async stream so that state is updated in-place,
                # but do NOT forward individual tokens to the client.
                async for chunk in agent.process_stream(state):
                    if "[DONE:" in chunk:
                        break
                    # tokens discarded — we only care about state side-effects
            except Exception as e:
                yield {"stage": "error", "agent": agent_name, "error": str(e)}
                return
            yield {"stage": stage, "status": "completed", "agent": agent_name}

        # ── Emit final structured answer ─────────────────────────────────────
        final_answer = (
            state.get("judge_result", {}).get("selected_answer")
            or state.get("generator_answer", "")
        )
        verification = state.get("verification_result", {})
        confidence = verification.get(
            "confidence_score",
            state.get("judge_result", {}).get("confidence", 0.5)
        )
        citations = verification.get("citations", [])
        if not citations:
            citations = self.doc_processor.get_citations(question)
        evidence = verification.get("evidence", [])
        agent_trace = [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in state.get("agent_responses", [])
        ]
        debate_summary = state.get("debate_result", {}).get("summary", "")

        yield {
            "stage": "complete",
            "answer": final_answer,
            "confidence": confidence,
            "citations": citations,
            "evidence": evidence,
            "agent_trace": agent_trace,
            "debate_summary": debate_summary,
            "processing_time": round(time.time() - start_time, 2),
        }


def create_multi_agent_graph(doc_processor: DocumentProcessor) -> MultiAgentGraph:
    return MultiAgentGraph(doc_processor)