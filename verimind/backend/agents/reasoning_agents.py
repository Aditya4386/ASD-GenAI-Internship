from typing import Dict, Any, List, AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate
from agents.base_agent import BaseAgent
from models.schemas import AgentResponse


# ── Shared markdown formatting instruction injected into every prompt ──────────
_MARKDOWN_RULES = """
CRITICAL OUTPUT FORMAT — FOLLOW EXACTLY:
- Write your answer using **Markdown formatting** — this is mandatory.
- Start with a 1–2 sentence plain-English summary.
- Use ## for major section headings, ### for sub-section headings.
- Use bullet lists  (- item)  for facts, features, components, or attributes.
- Use numbered lists  (1. item)  for steps, sequences, or ranked items.
- Use **bold** to highlight key terms and concepts.
- Use | tables | when comparing multiple items side by side.
- Use > blockquotes for key definitions or important takeaways.
- NEVER write a wall of text — always break content into labelled sections.
- Every section MUST have a heading. No heading = no section.
"""


def _parse_sections(text: str, labels: List[str]) -> Dict[str, str]:
    """
    Generic section parser that preserves all whitespace / newlines inside
    each section.  `labels` is an ordered list of section-header strings,
    e.g. ["SELECTED ANSWER:", "REASONING:", "CONFIDENCE:"].
    Returns a dict keyed by label (without the colon).
    """
    result = {lbl.rstrip(":"): "" for lbl in labels}
    current = None

    for raw_line in text.split("\n"):
        stripped = raw_line.strip()
        matched = False
        for lbl in labels:
            if stripped.upper().startswith(lbl.upper()):
                current = lbl.rstrip(":")
                # anything after the label on the same line
                inline = stripped[len(lbl):].strip()
                if inline:
                    result[current] += inline + "\n"
                matched = True
                break
        if not matched and current is not None:
            result[current] += raw_line + "\n"

    # strip trailing whitespace from each section
    return {k: v.strip() for k, v in result.items()}


# ─────────────────────────────────────────────────────────────────────────────
class AnswerGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnswerGenerator", temperature=0.1)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(
            """You are an expert document analyst. Answer the question using ONLY the provided context.
{markdown_rules}
Context:
{context}

Question: {question}

Rules:
- Answer must contain AT LEAST one ## heading and one bullet list.
- If the context does not contain enough information, say:
  "**Based on the provided context, I cannot fully answer this question.**"
  and explain what is missing.

Answer:"""
        )

    def _build_inputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "context": state.get("context", ""),
            "question": state.get("question", ""),
            "markdown_rules": _MARKDOWN_RULES,
        }

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        chain = self.create_chain()
        answer = chain.invoke(self._build_inputs(state))

        response = AgentResponse(
            agent_name=self.name,
            content=answer,
            confidence=0.7,
            reasoning="Generated initial answer from retrieved context",
        )

        state["generator_answer"] = answer
        state["agent_responses"].append(response)
        return state

    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        chain = self.create_chain()
        full_answer = ""

        async for chunk in chain.astream(self._build_inputs(state)):
            full_answer += chunk
            yield chunk

        response = AgentResponse(
            agent_name=self.name,
            content=full_answer,
            confidence=0.7,
            reasoning="Generated initial answer from retrieved context",
        )

        state["generator_answer"] = full_answer
        state["agent_responses"].append(response)
        yield f"\n\n[DONE:{full_answer}]"


# ─────────────────────────────────────────────────────────────────────────────
class DebateAgent(BaseAgent):
    def __init__(self):
        super().__init__("DebateAgent", temperature=0.2)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(
            """You are a debate agent that critically evaluates an answer.

Question: {question}
Answer: {answer}
Context: {context}

Analyse the answer and respond EXACTLY in this format (no deviations):

AGREEMENTS:
- <what is well-supported by context>

DISAGREEMENTS:
- <what might be incorrect or unsupported>

KEY POINTS:
- <key takeaway from the answer>

SUMMARY:
<2-3 sentence summary of the debate analysis>"""
        )

    def _parse(self, text: str) -> Dict[str, Any]:
        sections = _parse_sections(text, ["AGREEMENTS:", "DISAGREEMENTS:", "KEY POINTS:", "SUMMARY:"])

        def extract_bullets(s: str) -> List[str]:
            return [ln.lstrip("- ").strip() for ln in s.splitlines() if ln.strip().startswith("-")]

        return {
            "agreements":    extract_bullets(sections.get("AGREEMENTS", "")),
            "disagreements": extract_bullets(sections.get("DISAGREEMENTS", "")),
            "key_points":    extract_bullets(sections.get("KEY POINTS", "")),
            "summary":       sections.get("SUMMARY", ""),
        }

    def _build_inputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "context":  state.get("context", ""),
            "question": state.get("question", ""),
            "answer":   state.get("generator_answer", ""),
        }

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        chain = self.create_chain()
        debate_output = chain.invoke(self._build_inputs(state))
        debate_result = self._parse(debate_output)

        response = AgentResponse(
            agent_name=self.name,
            content=debate_output,
            confidence=0.8,
            reasoning=f"Found {len(debate_result['agreements'])} agreements, "
                      f"{len(debate_result['disagreements'])} disagreements",
        )

        state["debate_result"] = debate_result
        state["agent_responses"].append(response)
        return state

    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        chain = self.create_chain()
        full_output = ""

        async for chunk in chain.astream(self._build_inputs(state)):
            full_output += chunk
            yield chunk

        debate_result = self._parse(full_output)

        response = AgentResponse(
            agent_name=self.name,
            content=full_output,
            confidence=0.8,
            reasoning=f"Found {len(debate_result['agreements'])} agreements, "
                      f"{len(debate_result['disagreements'])} disagreements",
        )

        state["debate_result"] = debate_result
        state["agent_responses"].append(response)
        yield f"\n\n[DONE:{full_output}]"


# ─────────────────────────────────────────────────────────────────────────────
class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__("CriticAgent", temperature=0.1)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(
            """You are a critic agent that checks for hallucinations and logical errors.

Question: {question}
Answer: {answer}
Context: {context}
Debate Summary: {debate_summary}

Respond EXACTLY in this format:

ISSUES:
- <issue or hallucination found — or "None" if none>

SUGGESTIONS:
- <specific improvement suggestion>

SCORE: <integer 1-10>"""
        )

    def _parse(self, text: str) -> Dict[str, Any]:
        sections = _parse_sections(text, ["ISSUES:", "SUGGESTIONS:", "SCORE:"])

        def extract_bullets(s: str) -> List[str]:
            return [ln.lstrip("- ").strip() for ln in s.splitlines() if ln.strip().startswith("-")]

        score = 5.0
        score_text = sections.get("SCORE", "5").strip()
        raw_score = score_text.split()[0].replace("/10", "") if score_text else "5"
        try:
            score = float(raw_score)
        except ValueError:
            pass

        return {
            "issues":      extract_bullets(sections.get("ISSUES", "")),
            "suggestions": extract_bullets(sections.get("SUGGESTIONS", "")),
            "score":       score,
        }

    def _build_inputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "context":       state.get("context", ""),
            "question":      state.get("question", ""),
            "answer":        state.get("generator_answer", ""),
            "debate_summary": state.get("debate_result", {}).get("summary", ""),
        }

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        chain = self.create_chain()
        critic_output = chain.invoke(self._build_inputs(state))
        critic_result = self._parse(critic_output)

        response = AgentResponse(
            agent_name=self.name,
            content=critic_output,
            confidence=0.85,
            reasoning=f"Identified {len(critic_result['issues'])} issues, "
                      f"score: {critic_result['score']}/10",
        )

        state["critic_result"] = critic_result
        state["agent_responses"].append(response)
        return state

    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        chain = self.create_chain()
        full_output = ""

        async for chunk in chain.astream(self._build_inputs(state)):
            full_output += chunk
            yield chunk

        critic_result = self._parse(full_output)

        response = AgentResponse(
            agent_name=self.name,
            content=full_output,
            confidence=0.85,
            reasoning=f"Identified {len(critic_result['issues'])} issues, "
                      f"score: {critic_result['score']}/10",
        )

        state["critic_result"] = critic_result
        state["agent_responses"].append(response)
        yield f"\n\n[DONE:{full_output}]"


# ─────────────────────────────────────────────────────────────────────────────
class JudgeAgent(BaseAgent):
    def __init__(self):
        super().__init__("JudgeAgent", temperature=0)

    def get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(
            """You are a judge agent. Produce the single best final answer by combining and refining the original answer using the critic's feedback.
{markdown_rules}
Question: {question}
Original Answer:
{answer}

Debate Summary: {debate_summary}
Critic Issues: {critic_issues}
Critic Score: {critic_score}/10
Context: {context}

Instructions:
1. Fix every issue the critic raised.
2. Keep all accurate information from the original answer.
3. Make the final answer MORE structured and detailed than the original.
4. Output CONFIDENCE as a decimal between 0.0 and 1.0.

Respond EXACTLY in this format:

SELECTED ANSWER:
<your full markdown-formatted answer — must have ## headings and bullet lists>

REASONING:
<1-2 sentences explaining your selection>

CONFIDENCE: <0.0–1.0>"""
        )

    def _parse(self, text: str) -> Dict[str, Any]:
        sections = _parse_sections(
            text, ["SELECTED ANSWER:", "REASONING:", "CONFIDENCE:"]
        )

        confidence = 0.7
        conf_text = sections.get("CONFIDENCE", "0.7").strip()
        raw_conf = conf_text.split()[0] if conf_text else "0.7"
        try:
            confidence = max(0.0, min(1.0, float(raw_conf)))
        except ValueError:
            pass

        return {
            "selected_answer": sections.get("SELECTED ANSWER", ""),
            "reasoning":       sections.get("REASONING", ""),
            "confidence":      confidence,
        }

    def _build_inputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        critic = state.get("critic_result", {})
        return {
            "context":        state.get("context", ""),
            "question":       state.get("question", ""),
            "answer":         state.get("generator_answer", ""),
            "debate_summary": state.get("debate_result", {}).get("summary", ""),
            "critic_issues":  "; ".join(critic.get("issues", [])) or "None",
            "critic_score":   critic.get("score", 5.0),
            "markdown_rules": _MARKDOWN_RULES,
        }

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        chain = self.create_chain()
        judge_output = chain.invoke(self._build_inputs(state))
        judge_result = self._parse(judge_output)

        response = AgentResponse(
            agent_name=self.name,
            content=judge_output,
            confidence=judge_result["confidence"],
            reasoning=judge_result["reasoning"],
        )

        state["judge_result"] = judge_result
        state["agent_responses"].append(response)
        return state

    async def process_stream(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        chain = self.create_chain()
        full_output = ""

        async for chunk in chain.astream(self._build_inputs(state)):
            full_output += chunk
            yield chunk

        judge_result = self._parse(full_output)

        response = AgentResponse(
            agent_name=self.name,
            content=full_output,
            confidence=judge_result["confidence"],
            reasoning=judge_result["reasoning"],
        )

        state["judge_result"] = judge_result
        state["agent_responses"].append(response)
        yield f"\n\n[DONE:{full_output}]"