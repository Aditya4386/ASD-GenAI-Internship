import { useState, useRef, useEffect } from 'react'
import { marked } from 'marked'
import axios from 'axios'
import './App.css'

// ── API URL: read from env var in production, fall back to localhost ──────────
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Configure marked for GitHub-Flavoured Markdown ────────────────────────────
marked.use({ breaks: true, gfm: true })

/**
 * renderMarkdown(text)
 * Normalises escaped newlines from JSON transport then renders
 * the text as GitHub-Flavoured Markdown via `marked`.
 */
function renderMarkdown(raw) {
  if (!raw) return ''
  // Normalise literal \n escape sequences that may survive JSON serialisation
  const text = raw.replace(/\\n/g, '\n').replace(/\n{3,}/g, '\n\n')
  return marked.parse(text)
}

// ── Agent definitions ─────────────────────────────────────────────────────────
const AGENTS = [
  { id: 'retrieve', name: 'Retrieve', icon: '🔍', desc: 'Find context'  },
  { id: 'generate', name: 'Generate', icon: '🤖', desc: 'Draft answer'  },
  { id: 'debate',   name: 'Debate',   icon: '⚔️',  desc: 'Cross-check'  },
  { id: 'critic',   name: 'Critic',   icon: '🔬',  desc: 'QA review'    },
  { id: 'judge',    name: 'Judge',    icon: '⚖️',  desc: 'Select best'  },
  { id: 'verify',   name: 'Verify',   icon: '✅',   desc: 'Fact-check'  },
]

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [file,            setFile]            = useState(null)
  const [uploading,       setUploading]       = useState(false)
  const [uploadMsg,       setUploadMsg]       = useState(null)
  const [docInfo,         setDocInfo]         = useState(null)
  const [question,        setQuestion]        = useState('')
  const [answer,          setAnswer]          = useState(null)   // null = no answer yet
  const [loading,         setLoading]         = useState(false)
  const [activeAgent,     setActiveAgent]     = useState(null)
  const [completedAgents, setCompletedAgents] = useState(new Set())
  const [statusMsg,       setStatusMsg]       = useState('')
  const [useAgents,       setUseAgents]       = useState(true)
  const esRef = useRef(null)

  // ── Cleanup EventSource on unmount ─────────────────────────────────────────
  useEffect(() => () => closeES(), [])

  function closeES() {
    if (esRef.current) { esRef.current.close(); esRef.current = null }
  }

  // ── Upload handler ─────────────────────────────────────────────────────────
  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setUploadMsg(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await axios.post(`${API_URL}/upload`, fd)
      setUploadMsg({ text: `✅ ${res.data.message} — ${res.data.chunks_created} chunks indexed`, type: 'success' })
      setDocInfo(res.data.document)
    } catch (err) {
      setUploadMsg({ text: `❌ ${err.response?.data?.detail || err.message}`, type: 'error' })
    } finally {
      setUploading(false)
    }
  }

  // ── Ask handler — SSE streaming for pipeline status, answer at end ─────────
  function handleAsk() {
    if (!question.trim() || !docInfo || loading) return
    closeES()
    setLoading(true)
    setAnswer(null)
    setCompletedAgents(new Set())
    setActiveAgent('retrieve')
    setStatusMsg('Connecting to pipeline…')

    const params = new URLSearchParams({ question: question.trim(), use_agents: String(useAgents) })
    const es = new EventSource(`${API_URL}/ask/stream?${params}`)
    esRef.current = es

    es.onmessage = (e) => {
      let data
      try { data = JSON.parse(e.data) } catch { return }

      // ── Error from backend ────────────────────────────────────────────────
      if (data.error) {
        setAnswer({ isError: true, errorMsg: data.error })
        setLoading(false)
        setActiveAgent(null)
        setStatusMsg('')
        closeES()
        return
      }

      const { stage, status, message, agent } = data

      // ── Per-agent status updates ──────────────────────────────────────────
      if (status === 'started') {
        setActiveAgent(stage)
        setStatusMsg(message || `${agent} running…`)
      } else if (status === 'completed') {
        setCompletedAgents(prev => new Set([...prev, stage]))
      }

      // ── Final complete event with full answer ─────────────────────────────
      if (stage === 'complete') {
        setCompletedAgents(new Set(AGENTS.map(a => a.id)))
        setActiveAgent(null)
        setStatusMsg('')
        setAnswer(data)
        setLoading(false)
        closeES()
      }
    }

    es.onerror = () => {
      setAnswer({ isError: true, errorMsg: 'Connection lost. Please try again.' })
      setLoading(false)
      setActiveAgent(null)
      setStatusMsg('')
      closeES()
    }
  }

  // ── Agent box status ───────────────────────────────────────────────────────
  function agentStatus(id) {
    if (completedAgents.has(id)) return 'completed'
    if (activeAgent === id)      return 'active'
    return 'pending'
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="app">
      <header className="site-header">
        <span className="logo-icon">⚡</span>
        <div>
          <h1>VeriMind</h1>
          <p>Multi-Agent Document Intelligence Platform</p>
        </div>
      </header>

      <main className="main">

        {/* ── Document Upload ─────────────────────────────────────────────── */}
        <section className="card">
          <h2 className="card-title">📄 Document</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <label className="file-label">
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={e => { setFile(e.target.files[0]); setUploadMsg(null) }}
                disabled={uploading}
              />
              <span className="file-label-text">
                {file ? file.name : 'Choose PDF, TXT or DOCX…'}
              </span>
            </label>
            <button className="btn btn-primary" type="submit" disabled={uploading || !file}>
              {uploading ? '⏳ Processing…' : 'Upload'}
            </button>
          </form>

          {uploadMsg && <div className={`msg ${uploadMsg.type}`}>{uploadMsg.text}</div>}

          {docInfo && (
            <div className="doc-meta">
              <span>📄 {docInfo.filename}</span>
              <span>📊 {docInfo.num_chunks} chunks</span>
              <span>💾 {(docInfo.file_size / 1024).toFixed(1)} KB</span>
            </div>
          )}
        </section>

        {/* ── Agent Pipeline ──────────────────────────────────────────────── */}
        <section className="card">
          <div className="card-row">
            <h2 className="card-title">🤖 Agent Pipeline</h2>
            <label className="toggle-pill">
              <input
                type="checkbox"
                checked={useAgents}
                onChange={e => setUseAgents(e.target.checked)}
                disabled={loading}
              />
              <span className="toggle-track"><span className="toggle-thumb" /></span>
              <span className="toggle-label">Full pipeline</span>
            </label>
          </div>

          <div className="pipeline">
            {AGENTS.map((ag, i) => (
              <div key={ag.id} className="pipeline-item">
                <div className={`agent-box status-${agentStatus(ag.id)}`}>
                  <span className="agent-icon">{ag.icon}</span>
                  <span className="agent-name">{ag.name}</span>
                  <span className="agent-desc">{ag.desc}</span>
                </div>
                {i < AGENTS.length - 1 && <span className="pipeline-arrow">›</span>}
              </div>
            ))}
          </div>

          {loading && statusMsg && (
            <div className="status-bar">
              <span className="dot-spinner" />
              <span>{statusMsg}</span>
            </div>
          )}
        </section>

        {/* ── Ask ─────────────────────────────────────────────────────────── */}
        <section className="card">
          <h2 className="card-title">❓ Ask a Question</h2>

          {!docInfo && (
            <div className="msg warning">⚠️ Please upload a document first.</div>
          )}

          <textarea
            className="question-input"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="What does this document say about…?"
            rows={3}
            disabled={loading || !docInfo}
            onKeyDown={e => e.key === 'Enter' && (e.ctrlKey || e.metaKey) && handleAsk()}
          />
          <div className="ask-footer">
            <span className="hint">Ctrl + Enter to submit</span>
            <button
              className="btn btn-primary"
              onClick={handleAsk}
              disabled={loading || !question.trim() || !docInfo}
            >
              {loading ? '⏳ Running pipeline…' : 'Ask Agents →'}
            </button>
          </div>
        </section>

        {/* ── Answer ──────────────────────────────────────────────────────── */}
        {answer && (
          <section className="card answer-card">
            {answer.isError ? (
              <div className="error-box">
                <h3>⚠️ Something went wrong</h3>
                <p>{answer.errorMsg}</p>
                {answer.errorMsg?.includes('rate_limit') && (
                  <p className="hint-text">
                    💡 Tip: Your Groq free-tier has a low token-per-minute limit.
                    Wait 30s and try again, or switch to a model with higher limits
                    like <code>llama-3.1-8b-instant</code> in your <code>.env</code>.
                  </p>
                )}
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="answer-header">
                  <h2 className="card-title">💡 Answer</h2>
                  <span className={`confidence-badge conf-${confidenceClass(answer.confidence)}`}>
                    {(answer.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>

                {/* ── Main answer body — proper markdown rendering ──────────── */}
                <div
                  className="answer-body markdown"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(answer.answer) }}
                />

                {/* Debate summary */}
                {answer.debate_summary && (
                  <div className="answer-section">
                    <h4>🤔 Debate Summary</h4>
                    <p className="muted-text">{answer.debate_summary}</p>
                  </div>
                )}

                {/* Citations */}
                {answer.citations?.length > 0 && (
                  <div className="answer-section">
                    <h4>📚 Citations</h4>
                    <ul className="cite-list">
                      {answer.citations.map((c, i) => (
                        <li key={i} dangerouslySetInnerHTML={{ __html: formatCitation(c) }} />
                      ))}
                    </ul>
                  </div>
                )}

                {/* Evidence */}
                {answer.evidence?.length > 0 && (
                  <div className="answer-section">
                    <h4>🔍 Supporting Evidence</h4>
                    <ul className="cite-list">
                      {answer.evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                    </ul>
                  </div>
                )}

                {/* Agent trace (collapsed by default) */}
                {answer.agent_trace?.length > 0 && (
                  <details className="trace-details">
                    <summary>🔬 Agent Trace ({answer.agent_trace.length} agents)</summary>
                    <div className="trace-body">
                      {answer.agent_trace.map((t, i) => (
                        <div key={i} className="trace-row">
                          <strong>{t.agent_name}</strong>
                          <span>{t.reasoning}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                <div className="answer-meta">
                  Processed in {answer.processing_time?.toFixed(2)}s
                </div>
              </>
            )}
          </section>
        )}

      </main>
    </div>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function confidenceClass(conf) {
  if (conf >= 0.8) return 'high'
  if (conf >= 0.5) return 'medium'
  return 'low'
}

function formatCitation(text) {
  if (!text) return ''
  // Safely escape, then bold the [source, p.N]: prefix
  const safe = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  return safe.replace(/(\[.*?\]:)/, '<strong>$1</strong>')
}