import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from models.schemas import Chunk, DocumentInfo, DocumentType


class DocumentProcessor:
    def __init__(self, upload_dir: Path, vector_dir: Path):
        self.upload_dir = upload_dir
        self.vector_dir = vector_dir
        self.upload_dir.mkdir(exist_ok=True)
        self.vector_dir.mkdir(exist_ok=True)
        
        self.documents_store: List[Chunk] = []
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.document_info: Optional[DocumentInfo] = None
        
    def load_document(self, file_path: Path, file_type: DocumentType) -> List[Chunk]:
        if file_type == DocumentType.PDF:
            loader = PyPDFLoader(str(file_path))
        elif file_type == DocumentType.TXT:
            loader = TextLoader(str(file_path))
        elif file_type == DocumentType.DOCX:
            loader = UnstructuredWordDocumentLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        documents = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        
        result = []
        for i, chunk in enumerate(chunks):
            result.append(Chunk(
                content=chunk.page_content,
                metadata={
                    "source": str(file_path),
                    "chunk_index": i,
                    "page": chunk.metadata.get("page", 0),
                    **chunk.metadata
                }
            ))
        return result
    
    def process_upload(self, file_path: Path, filename: str, file_type: DocumentType) -> DocumentInfo:
        chunks = self.load_document(file_path, file_type)
        
        self.documents_store = chunks
        self._rebuild_index()
        
        doc_info = DocumentInfo(
            filename=filename,
            file_type=file_type,
            num_chunks=len(chunks),
            file_size=file_path.stat().st_size
        )
        self.document_info = doc_info
        
        self._save_state()
        
        return doc_info
    
    def _rebuild_index(self):
        if self.documents_store:
            texts = [chunk.content for chunk in self.documents_store]
            self.tfidf_vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,
                ngram_range=(1, 2)
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
    
    def retrieve(self, query: str, k: int = 3) -> List[Chunk]:
        if self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            return []
        
        query_vec = self.tfidf_vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            # Lowered threshold: 0.001 so generic queries ("explain this paper")
            # still retrieve relevant chunks even when query terms don't
            # appear verbatim in the document.
            if similarities[idx] > 0.001:
                chunk = self.documents_store[idx]
                chunk.metadata["similarity_score"] = float(similarities[idx])
                results.append(chunk)
        
        # Fallback: if TF-IDF found nothing useful (very generic query),
        # always return the first 2 chunks which are typically the
        # abstract / introduction — the most context-rich part of any paper.
        if not results and self.documents_store:
            results = self.documents_store[:2]
        
        return results
    
    def _save_state(self):
        state = {
            "documents_store": self.documents_store,
            "document_info": self.document_info.model_dump() if self.document_info else None
        }
        with open(self.vector_dir / "state.pkl", "wb") as f:
            pickle.dump(state, f)
    
    def load_state(self) -> bool:
        state_path = self.vector_dir / "state.pkl"
        if state_path.exists():
            with open(state_path, "rb") as f:
                state = pickle.load(f)
            self.documents_store = state.get("documents_store", [])
            if state.get("document_info"):
                self.document_info = DocumentInfo(**state["document_info"])
            self._rebuild_index()
            return True
        return False
    
    def get_context(self, query: str, k: int = 3, max_chars: int = 3000) -> str:
        chunks = self.retrieve(query, k)
        context = "\n\n".join([chunk.content for chunk in chunks])
        # Truncate to avoid hitting LLM token rate limits
        return context[:max_chars] if len(context) > max_chars else context
    
    def get_citations(self, query: str, k: int = 3) -> List[str]:
        chunks = self.retrieve(query, k)
        citations = []
        for chunk in chunks:
            page = chunk.metadata.get("page", "N/A")
            source = Path(chunk.metadata.get("source", "")).name
            citations.append(f"[{source}, p.{page}]: {chunk.content[:200]}...")
        return citations


# OCR support (optional)
def extract_text_from_image(image_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except ImportError:
        return ""


def extract_text_from_scanned_pdf(pdf_path: Path) -> str:
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    # Try OCR on page image
                    im = page.to_image(resolution=300)
                    text += extract_text_from_image(im.original) + "\n"
        return text
    except ImportError:
        return ""