import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from rag.processor import DocumentProcessor
from agents.graph import create_multi_agent_graph


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary upload and vector directories"""
    upload_dir = tmp_path / "uploads"
    vector_dir = tmp_path / "vectorstore"
    upload_dir.mkdir()
    vector_dir.mkdir()
    return upload_dir, vector_dir


@pytest.fixture
def doc_processor(temp_dirs):
    """Create DocumentProcessor instance with temp dirs"""
    upload_dir, vector_dir = temp_dirs
    return DocumentProcessor(upload_dir, vector_dir)


@pytest.fixture
def sample_text_file(temp_dirs):
    """Create a sample text file for testing"""
    upload_dir, _ = temp_dirs
    file_path = upload_dir / "sample.txt"
    content = """
    This is a sample document for testing VeriMind.
    It contains multiple paragraphs with information.
    
    The document discusses artificial intelligence and machine learning.
    AI systems can process natural language and generate responses.
    
    Multi-agent systems use multiple AI agents working together.
    Each agent has a specific role in the pipeline.
    """
    file_path.write_text(content.strip())
    return file_path


@pytest.fixture
def multi_agent_graph(doc_processor):
    """Create multi-agent graph for testing"""
    return create_multi_agent_graph(doc_processor)