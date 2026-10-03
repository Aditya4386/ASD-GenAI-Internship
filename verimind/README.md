# VeriMind - Multi-Agent Document Intelligence Platform

A production-ready AI-powered document question-answering platform featuring a **LangGraph-based multi-agent architecture** with 6 specialized agents working in sequence to provide verified, high-confidence answers with full traceability.

## 🏗️ Architecture Overview

```
┌─────────────┐    ┌──────────────┐    ┌────────────┐    ┌───────────┐    ┌──────────┐    ┌────────────┐
│  Retrieve   │───▶│  Generator   │───▶│   Debate   │───▶│  Critic   │───▶│  Judge   │───▶│  Verify    │
│  (TF-IDF)   │    │  (Groq LLM)  │    │  (Analyze) │    │ (Critique)│    │ (Select) │    │ (Fact-chk) │
└─────────────┘    └──────────────┘    └────────────┘    └───────────┘    └──────────┘    └────────────┘
                                                                                                      │
                                                                                                      ▼
                                                            ┌─────────────────────────────────────────────────┐
                                                            │              Final Verified Answer               │
                                                            │  • Answer + Confidence Score (0-100%)           │
                                                            │  • Citations & Evidence                         │
                                                            │  • Agent Trace (Full Reasoning Transparency)    │
                                                            │  • Debate Summary                               │
                                                            └─────────────────────────────────────────────────┘
```

## ✨ Features

### 🤖 Multi-Agent Pipeline (LangGraph)
| Agent | Role | Description |
|-------|------|-------------|
| **Retrieve** | Context Retrieval | TF-IDF + Cosine Similarity for relevant chunk retrieval |
| **Generator** | Answer Generation | Groq LLM (openai/oss/120b) generates initial answer |
| **Debate** | Reasoning Analysis | Identifies agreements, disagreements, key points |
| **Critic** | Quality Assurance | Detects hallucinations, logical gaps, missing info |
| **Judge** | Answer Selection | Selects best answer based on all feedback |
| **Verify** | Fact Verification | Confidence scoring, evidence collection, citations |

### 📄 Document Processing
- **Supported Formats**: PDF, TXT, DOCX
- **Smart Chunking**: RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
- **OCR Ready**: pdfplumber + pytesseract integration for scanned docs
- **Persistent Storage**: Pickle-based state for session persistence

### 🔍 Transparency & Trust
- **Confidence Scoring**: 0-100% per answer
- **Citations**: Source references with page numbers
- **Evidence**: Supporting context snippets
- **Agent Trace**: Full reasoning chain visible
- **Debate Summary**: Multi-perspective analysis

### 🚀 Deployment Ready
- **Backend**: FastAPI + Uvicorn (port 8000)
- **Frontend**: React 18 + Vite (port 5173)
- **CORS Enabled**: For seamless frontend-backend integration
- **Health Checks**: `/health` endpoint for monitoring

## 📁 Project Structure

```
verimind/
├── backend/                    # FastAPI Backend
│   ├── agents/                 # Multi-Agent System
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Abstract base agent
│   │   ├── reasoning_agents.py # Generator, Debate, Critic, Judge
│   │   ├── verification_agent.py # Fact verification
│   │   └── graph.py            # LangGraph workflow
│   ├── rag/                    # RAG Pipeline
│   │   └── processor.py        # Document loading, chunking, retrieval
│   ├── models/                 # Pydantic Schemas
│   │   └── schemas.py          # Request/Response models
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt
│   └── .env                    # API Keys (GROQ_API_KEY, etc.)
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx             # Main application
│   │   ├── App.css             # Styling with agent visualization
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   └── vite.config.js
├── .env                        # Root environment file
└── README.md
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Setup Backend
```bash
cd verimind/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Start server
python main.py
# Server runs at http://localhost:8000
```

### 2. Setup Frontend
```bash
cd verimind/frontend

# Install dependencies
npm install

# Start development server
npm run dev
# App runs at http://localhost:5173
```

### 3. Use the App
1. Open http://localhost:5173
2. Upload a PDF/TXT/DOCX document
3. Ask questions about the document
4. Watch the multi-agent pipeline visualize in real-time
5. View answer with confidence, citations, and agent trace

## 🔧 Configuration

### Environment Variables (`.env`)
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=openai/oss/120b
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload document (PDF/TXT/DOCX) |
| POST | `/ask` | Ask question with multi-agent pipeline |
| GET | `/document/info` | Get loaded document metadata |
| DELETE | `/document` | Clear current document |

### Request/Response Examples

**Upload Document**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

**Ask Question**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings?", "use_agents": true}'
```

**Response**
```json
{
  "question": "What are the key findings?",
  "answer": "Based on the document, the key findings are...",
  "confidence": 0.92,
  "citations": ["[document.pdf, p.1]: The study found...", "..."],
  "evidence": ["Document context supports answer", "..."],
  "agent_trace": [
    {"agent_name": "Generator", "reasoning": "Generated initial answer..."},
    {"agent_name": "Debate", "reasoning": "Found 3 agreements, 1 disagreement..."},
    {"agent_name": "Critic", "reasoning": "Identified 2 issues, score: 8.5/10..."},
    {"agent_name": "Judge", "reasoning": "Selected answer with high confidence..."},
    {"agent_name": "Verify", "reasoning": "Verified: true, Confidence: 0.92..."}
  ],
  "debate_summary": "All agents agreed on main findings...",
  "processing_time": 3.45
}
```

## 🧪 Testing the Multi-Agent Flow

```python
# Test directly in Python
from rag.processor import DocumentProcessor
from agents.graph import create_multi_agent_graph
from pathlib import Path

processor = DocumentProcessor(Path("uploads"), Path("vectorstore"))
# ... upload document first ...

graph = create_multi_agent_graph(processor)
result = graph.run("What is this document about?", use_agents=True)

print("Final Answer:", result["judge_result"]["selected_answer"])
print("Confidence:", result["verification_result"]["confidence_score"])
print("Agent Trace:", [a.agent_name for a in result["agent_responses"]])
```

## 🔑 Key Design Decisions

### Why LangGraph?
- **Stateful Workflows**: Maintains context across agents
- **Checkpointing**: Resume from any agent
- **Visual Debugging**: `graph.get_graph().draw_mermaid()` for architecture docs
- **Production Ready**: Built for scaling with Redis/Postgres checkpointers

### Why TF-IDF over Vector Embeddings?
- **Zero External Dependencies**: No HuggingFace, no torch, no GPU
- **Fast & Lightweight**: ~50ms retrieval vs 500ms+ for embeddings
- **Surprisingly Effective**: Works well for document Q&A with good chunking
- **Easy to Debug**: Human-readable term weights

### Agent Temperature Settings
| Agent | Temperature | Rationale |
|-------|-------------|-----------|
| Generator | 0.1 | Creative but grounded |
| Debate | 0.2 | Analytical reasoning |
| Critic | 0.1 | Precise critique |
| Judge | 0.0 | Deterministic selection |
| Verify | 0.0 | Factual verification |

## 🚢 Deployment

### Docker (Recommended)
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

### Production Checklist
- [ ] Use Redis checkpointer for LangGraph (`langgraph.checkpoint.redis`)
- [ ] Add authentication (JWT/OAuth)
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Use PostgreSQL for document metadata
- [ ] Add FAISS/Chroma for production-scale vectors

## 📚 Extending the Platform

### Add New Agent
```python
# agents/custom_agent.py
from agents.base_agent import BaseAgent
from langchain_core.prompts import ChatPromptTemplate

class CustomAgent(BaseAgent):
    def get_prompt(self):
        return ChatPromptTemplate.from_template("Your prompt here")
    
    def process(self, state):
        # Your logic
        return state
```

### Add to Graph
```python
# agents/graph.py
workflow.add_node("custom", custom_agent.process)
workflow.add_edge("judge", "custom")
workflow.add_edge("custom", "verify")
```

### Use Different LLM
```python
# In any agent __init__
self.llm = ChatGroq(model="llama-3.3-70b-versatile", ...)  # Or other Groq models
# Or use ChatOpenAI, ChatAnthropic, etc.
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: langchain_community` | `pip install langchain-community` |
| `ImportError: sentence_transformers` | Use TF-IDF (default) or install `sentence-transformers` with compatible torch |
| Groq API 429 Rate Limit | Add retry logic or use `groq` client directly with backoff |
| Frontend can't connect to backend | Check CORS, ensure backend on port 8000 |
| Document not found after restart | Check `vectorstore/state.pkl` exists and permissions |

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-agent`
3. Commit changes: `git commit -m 'Add amazing agent'`
4. Push: `git push origin feature/amazing-agent`
5. Open Pull Request

## 📄 License

MIT License - Feel free to use for learning, research, or production.

## 🙏 Acknowledgments

- **LangGraph** for the elegant agent orchestration framework
- **Groq** for blazing-fast LLM inference
- **LangChain** for the RAG and agent building blocks
- **scikit-learn** for lightweight TF-IDF retrieval

---

**Built for the ASD GenAI Internship** | Demonstrating production-grade multi-agent AI systems