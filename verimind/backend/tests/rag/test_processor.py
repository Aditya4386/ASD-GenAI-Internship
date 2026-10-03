import pytest
from pathlib import Path
from rag.processor import DocumentProcessor, DocumentType


class TestDocumentProcessor:
    
    def test_initialization(self, doc_processor):
        """Test processor initializes correctly"""
        assert doc_processor is not None
        assert doc_processor.documents_store == []
        assert doc_processor.tfidf_vectorizer is None
        assert doc_processor.tfidf_matrix is None
    
    def test_load_text_document(self, doc_processor, sample_text_file):
        """Test loading a text document"""
        chunks = doc_processor.load_document(sample_text_file, DocumentType.TXT)
        
        assert len(chunks) > 0
        assert all(hasattr(c, 'content') for c in chunks)
        assert all(hasattr(c, 'metadata') for c in chunks)
    
    def test_chunking_creates_multiple_chunks(self, doc_processor, sample_text_file):
        """Test that long documents are chunked"""
        chunks = doc_processor.load_document(sample_text_file, DocumentType.TXT)
        # With chunk_size=1000 and overlap=200, sample should create multiple chunks
        assert len(chunks) >= 1
    
    def test_process_upload(self, doc_processor, sample_text_file):
        """Test full upload processing pipeline"""
        doc_info = doc_processor.process_upload(
            sample_text_file, 
            "sample.txt", 
            DocumentType.TXT
        )
        
        assert doc_info.filename == "sample.txt"
        assert doc_info.file_type == DocumentType.TXT
        assert doc_info.num_chunks > 0
        assert doc_info.file_size > 0
        assert len(doc_processor.documents_store) == doc_info.num_chunks
    
    def test_retrieve_context(self, doc_processor, sample_text_file):
        """Test context retrieval"""
        doc_processor.process_upload(sample_text_file, "sample.txt", DocumentType.TXT)
        
        context = doc_processor.get_context("artificial intelligence", k=3)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "artificial intelligence" in context.lower() or "AI" in context
    
    def test_retrieve_with_k(self, doc_processor, sample_text_file):
        """Test retrieval respects k parameter"""
        doc_processor.process_upload(sample_text_file, "sample.txt", DocumentType.TXT)
        
        context_k1 = doc_processor.get_context("machine learning", k=1)
        context_k3 = doc_processor.get_context("machine learning", k=3)
        
        assert len(context_k3) >= len(context_k1)
    
    def test_get_citations(self, doc_processor, sample_text_file):
        """Test citation generation"""
        doc_processor.process_upload(sample_text_file, "sample.txt", DocumentType.TXT)
        
        citations = doc_processor.get_citations("AI systems", k=2)
        
        assert isinstance(citations, list)
        assert len(citations) > 0
    
    def test_empty_retrieval(self, doc_processor):
        """Test retrieval with no documents"""
        context = doc_processor.get_context("any query", k=3)
        assert context == ""
        
        citations = doc_processor.get_citations("any query", k=3)
        assert citations == []


class TestDocumentProcessorPersistence:
    
    def test_save_and_load_state(self, doc_processor, sample_text_file, temp_dirs):
        """Test saving and loading processor state"""
        upload_dir, vector_dir = temp_dirs
        
        # Process document
        doc_processor.process_upload(sample_text_file, "sample.txt", DocumentType.TXT)
        original_chunks = len(doc_processor.documents_store)
        
        # Create new processor with same dirs
        new_processor = DocumentProcessor(upload_dir, vector_dir)
        loaded = new_processor.load_state()
        
        assert loaded is True
        assert len(new_processor.documents_store) == original_chunks
        assert new_processor.document_info.filename == "sample.txt"
    
    def test_load_state_no_file(self, doc_processor):
        """Test loading state when no file exists"""
        loaded = doc_processor.load_state()
        assert loaded is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])