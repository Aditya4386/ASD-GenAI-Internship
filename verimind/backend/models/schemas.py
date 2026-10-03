from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"


class DocumentInfo(BaseModel):
    filename: str
    file_type: DocumentType
    upload_time: datetime = Field(default_factory=datetime.now)
    num_pages: Optional[int] = None
    num_chunks: int = 0
    file_size: int = 0


class Chunk(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class AgentResponse(BaseModel):
    agent_name: str
    content: str
    confidence: float = 0.0
    reasoning: Optional[str] = None
    citations: List[str] = []


class DebateResult(BaseModel):
    agreements: List[str] = []
    disagreements: List[str] = []
    key_points: List[str] = []
    summary: str = ""


class CriticResult(BaseModel):
    issues: List[str] = []
    suggestions: List[str] = []
    score: float = 0.0


class VerificationResult(BaseModel):
    verified: bool = False
    confidence_score: float = 0.0
    evidence: List[str] = []
    citations: List[str] = []
    contradictions: List[str] = []


class JudgeResult(BaseModel):
    selected_answer: str = ""
    reasoning: str = ""
    confidence: float = 0.0


class QuestionRequest(BaseModel):
    question: str
    use_agents: bool = True


class QuestionResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    citations: List[str] = []
    evidence: List[str] = []
    agent_trace: List[AgentResponse] = []
    debate_summary: Optional[str] = None
    processing_time: float = 0.0


class UploadResponse(BaseModel):
    message: str
    document: DocumentInfo
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    agents_active: int = 5