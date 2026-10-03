import os
import time
import shutil
import json
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from rag.processor import DocumentProcessor
from agents.graph import create_multi_agent_graph
from models.schemas import (
    QuestionRequest, QuestionResponse, UploadResponse,
    HealthResponse, DocumentInfo, DocumentType
)

load_dotenv()

UPLOAD_DIR = Path("uploads")
VECTOR_DIR = Path("vectorstore")
UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_DIR.mkdir(exist_ok=True)

doc_processor = DocumentProcessor(UPLOAD_DIR, VECTOR_DIR)
multi_agent_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global multi_agent_graph
    doc_processor.load_state()
    multi_agent_graph = create_multi_agent_graph(doc_processor)
    yield


app = FastAPI(
    title="VeriMind API",
    description="Multi-Agent Document Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# -----------------------------------------------------------------
# CORS — Bug Fix #4:
# allow_credentials=True is INVALID with allow_origins=["*"].
# Use an env-var ALLOWED_ORIGINS for production, fall back to "*" for dev.
# Credentials are only needed if you add cookie-based auth later.
# -----------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
if _raw_origins == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,     # must be False when using wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        agents_active=5
    )


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ext = file.filename.split(".")[-1].lower()
    if ext == "pdf":
        file_type = DocumentType.PDF
    elif ext == "txt":
        file_type = DocumentType.TXT
    elif ext == "docx":
        file_type = DocumentType.DOCX
    else:
        raise HTTPException(400, "Supported formats: PDF, TXT, DOCX")

    try:
        doc_info = doc_processor.process_upload(file_path, file.filename, file_type)
        return UploadResponse(
            message=f"Successfully uploaded {file.filename}",
            document=doc_info,
            chunks_created=doc_info.num_chunks
        )
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")


async def stream_agent_response(question: str, use_agents: bool):
    """Stream agent responses as they complete using the graph's streaming method"""
    global multi_agent_graph

    if multi_agent_graph is None:
        multi_agent_graph = create_multi_agent_graph(doc_processor)

    if not doc_processor.documents_store and not doc_processor.load_state():
        yield f"data: {json.dumps({'error': 'No document uploaded yet'})}\\n\\n"
        return

    try:
        async for event in multi_agent_graph.run_stream(question, use_agents):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'stage': 'error', 'error': str(e)})}\n\n"


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    global multi_agent_graph

    if multi_agent_graph is None:
        multi_agent_graph = create_multi_agent_graph(doc_processor)

    if not doc_processor.documents_store and not doc_processor.load_state():
        raise HTTPException(400, "No document uploaded yet. Please upload a document first.")

    start_time = time.time()

    try:
        result = multi_agent_graph.run(
            question=request.question,
            use_agents=request.use_agents
        )

        processing_time = time.time() - start_time

        final_answer = result.get("judge_result", {}).get("selected_answer",
                    result.get("generator_answer", ""))

        verification = result.get("verification_result", {})
        confidence = verification.get("confidence_score",
                    result.get("judge_result", {}).get("confidence", 0.5))

        citations = verification.get("citations", [])
        if not citations:
            citations = doc_processor.get_citations(request.question)

        evidence = verification.get("evidence", [])

        return QuestionResponse(
            question=request.question,
            answer=final_answer,
            confidence=confidence,
            citations=citations,
            evidence=evidence,
            agent_trace=result.get("agent_responses", []),
            debate_summary=result.get("debate_result", {}).get("summary"),
            processing_time=processing_time
        )

    except Exception as e:
        raise HTTPException(500, f"Question processing failed: {str(e)}")


# -----------------------------------------------------------------
# Bug Fix #2 & #8: /ask/stream supports BOTH POST (JSON body) and
# GET (query params).  The browser's native EventSource API only
# sends GET requests, so we expose a GET variant here so that the
# frontend EventSource works without switching to fetch().
# The POST variant is kept for programmatic / curl usage.
# -----------------------------------------------------------------

@app.post("/ask/stream")
async def ask_question_stream_post(request: QuestionRequest):
    """Stream agent responses via Server-Sent Events (POST — for fetch/curl clients)"""
    return StreamingResponse(
        stream_agent_response(request.question, request.use_agents),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/ask/stream")
async def ask_question_stream_get(
    question: str = Query(..., description="The question to ask"),
    use_agents: bool = Query(True, description="Whether to use the full multi-agent pipeline")
):
    """Stream agent responses via Server-Sent Events (GET — for browser EventSource)"""
    if not question.strip():
        raise HTTPException(400, "Question cannot be empty")

    return StreamingResponse(
        stream_agent_response(question, use_agents),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/document/info")
def get_document_info():
    if doc_processor.document_info:
        return doc_processor.document_info
    raise HTTPException(404, "No document loaded")


@app.delete("/document")
async def clear_document():
    global doc_processor
    doc_processor.documents_store = []
    doc_processor.document_info = None
    doc_processor.tfidf_vectorizer = None
    doc_processor.tfidf_matrix = None

    state_path = VECTOR_DIR / "state.pkl"
    if state_path.exists():
        state_path.unlink()

    for f in UPLOAD_DIR.glob("*"):
        f.unlink()

    return {"message": "Document cleared successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))