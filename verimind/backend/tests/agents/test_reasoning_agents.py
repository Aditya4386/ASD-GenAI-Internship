import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.reasoning_agents import AnswerGeneratorAgent, DebateAgent, CriticAgent, JudgeAgent


class TestAnswerGeneratorAgent:
    
    @pytest.fixture
    def agent(self):
        return AnswerGeneratorAgent()
    
    @pytest.fixture
    def state(self):
        return {
            "question": "What is AI?",
            "context": "AI stands for Artificial Intelligence. It refers to computer systems that can perform tasks requiring human intelligence.",
            "agent_responses": []
        }
    
    def test_get_prompt(self, agent):
        """Test prompt template is created"""
        prompt = agent.get_prompt()
        assert prompt is not None
    
    def test_process_returns_answer(self, agent, state):
        """Test process returns answer in state"""
        with patch.object(agent, 'create_chain') as mock_chain:
            mock_chain.return_value.invoke.return_value = "AI is Artificial Intelligence."
            
            result = agent.process(state)
            
            assert "generator_answer" in result
            assert result["generator_answer"] == "AI is Artificial Intelligence."
            assert len(result["agent_responses"]) == 1
            assert result["agent_responses"][0].agent_name == "AnswerGenerator"


class TestDebateAgent:
    
    @pytest.fixture
    def agent(self):
        return DebateAgent()
    
    @pytest.fixture
    def state(self):
        return {
            "question": "What is AI?",
            "context": "AI is Artificial Intelligence.",
            "generator_answer": "AI is Artificial Intelligence used for many tasks.",
            "agent_responses": []
        }
    
    def test_process_parses_debate_output(self, agent, state):
        """Test debate output parsing"""
        debate_output = """AGREEMENTS:
- AI definition is correct
DISAGREEMENTS:
- Missing mention of ML
KEY POINTS:
- AI performs human-like tasks
SUMMARY:
Good answer with minor omissions"""
        
        with patch.object(agent, 'create_chain') as mock_chain:
            mock_chain.return_value.invoke.return_value = debate_output
            
            result = agent.process(state)
            
            assert "debate_result" in result
            assert len(result["debate_result"]["agreements"]) == 1
            assert len(result["debate_result"]["disagreements"]) == 1
            assert len(result["debate_result"]["key_points"]) == 1
            assert "Good answer" in result["debate_result"]["summary"]


class TestCriticAgent:
    
    @pytest.fixture
    def agent(self):
        return CriticAgent()
    
    @pytest.fixture
    def state(self):
        return {
            "question": "What is AI?",
            "context": "AI is Artificial Intelligence.",
            "generator_answer": "AI is Artificial Intelligence.",
            "debate_result": {"summary": "Good answer"},
            "agent_responses": []
        }
    
    def test_process_parses_critic_output(self, agent, state):
        """Test critic output parsing"""
        critic_output = """ISSUES:
- No mention of ML subset
SUGGESTIONS:
- Add ML context
SCORE: 8.5/10"""
        
        with patch.object(agent, 'create_chain') as mock_chain:
            mock_chain.return_value.invoke.return_value = critic_output
            
            result = agent.process(state)
            
            assert "critic_result" in result
            assert len(result["critic_result"]["issues"]) == 1
            assert len(result["critic_result"]["suggestions"]) == 1
            assert result["critic_result"]["score"] == 8.5


class TestJudgeAgent:
    
    @pytest.fixture
    def agent(self):
        return JudgeAgent()
    
    @pytest.fixture
    def state(self):
        return {
            "question": "What is AI?",
            "context": "AI is Artificial Intelligence.",
            "generator_answer": "AI is Artificial Intelligence.",
            "debate_result": {"summary": "Good answer"},
            "critic_result": {"issues": [], "score": 9.0},
            "agent_responses": []
        }
    
    def test_process_parses_judge_output(self, agent, state):
        """Test judge output parsing"""
        judge_output = """SELECTED ANSWER:
AI is Artificial Intelligence used for various tasks.
REASONING:
Answer is accurate and comprehensive.
CONFIDENCE: 0.95"""
        
        with patch.object(agent, 'create_chain') as mock_chain:
            mock_chain.return_value.invoke.return_value = judge_output
            
            result = agent.process(state)
            
            assert "judge_result" in result
            assert "AI is Artificial Intelligence" in result["judge_result"]["selected_answer"]
            assert result["judge_result"]["confidence"] == 0.95
            assert "comprehensive" in result["judge_result"]["reasoning"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])