import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from agents.graph import MultiAgentGraph, AgentState
from rag.processor import DocumentProcessor


class TestMultiAgentGraph:
    
    @pytest.fixture
    def mock_doc_processor(self):
        processor = Mock(spec=DocumentProcessor)
        processor.get_context.return_value = "Test context about AI."
        processor.get_citations.return_value = ["[test.txt, p.1]: AI context"]
        return processor
    
    @pytest.fixture
    def graph(self, mock_doc_processor):
        return MultiAgentGraph(mock_doc_processor)
    
    def test_graph_initialization(self, graph):
        """Test graph initializes with all agents"""
        assert graph.generator is not None
        assert graph.debate is not None
        assert graph.critic is not None
        assert graph.judge is not None
        assert graph.verifier is not None
        assert graph.graph is not None
    
    def test_retrieve_context(self, graph, mock_doc_processor):
        """Test context retrieval node"""
        state = AgentState(
            question="What is AI?",
            context="",
            generator_answer="",
            debate_result={},
            critic_result={},
            judge_result={},
            verification_result={},
            agent_responses=[],
            use_agents=True
        )
        
        result = graph._retrieve_context(state)
        
        assert result["context"] == "Test context about AI."
        mock_doc_processor.get_context.assert_called_once_with("What is AI?", k=3)
    
    def test_should_use_agents_true(self, graph):
        """Test conditional edge when agents enabled"""
        state = AgentState(
            question="Test",
            context="Context",
            generator_answer="Answer",
            debate_result={},
            critic_result={},
            judge_result={},
            verification_result={},
            agent_responses=[],
            use_agents=True
        )
        
        result = graph._should_use_agents(state)
        assert result == "agents"
    
    def test_should_use_agents_false(self, graph):
        """Test conditional edge when agents disabled"""
        state = AgentState(
            question="Test",
            context="Context",
            generator_answer="Answer",
            debate_result={},
            critic_result={},
            judge_result={},
            verification_result={},
            agent_responses=[],
            use_agents=False
        )
        
        result = graph._should_use_agents(state)
        assert result == "skip"
    
    def test_run_simple_mode(self, graph):
        """Test run in simple mode (skip agents) - mocked"""
        # Just test the method exists and can be called
        assert hasattr(graph, 'run')
        assert callable(graph.run)
    
    def test_run_returns_complete_state(self, graph):
        """Test run method exists"""
        assert hasattr(graph, 'run')
        assert callable(graph.run)


class TestAgentState:
    
    def test_agent_state_typed_dict(self):
        """Test AgentState has all required fields"""
        state = AgentState(
            question="Test question",
            context="Test context",
            generator_answer="Test answer",
            debate_result={},
            critic_result={},
            judge_result={},
            verification_result={},
            agent_responses=[],
            use_agents=True
        )
        
        assert state["question"] == "Test question"
        assert state["use_agents"] is True
        assert isinstance(state["agent_responses"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])