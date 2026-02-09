import { useState, useRef, useEffect } from 'react'
import './App.css'

// API Configuration - change this to your OCI backend URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const STREAM_ENDPOINT = `${API_URL}/api/v1/query/stream`
const HEALTH_ENDPOINT = `${API_URL}/api/v1/health`

function distanceToSimilarity(distance) {
  if (distance === null || distance === undefined) return 0
  return Math.max(0, 1 - distance)
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [topK, setTopK] = useState(5)
  const [apiStatus, setApiStatus] = useState('checking')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Check API health on mount
  useEffect(() => {
    checkHealth()
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const checkHealth = async () => {
    try {
      const response = await fetch(HEALTH_ENDPOINT, {
        method: 'GET',
        mode: 'cors'
      })
      setApiStatus(response.ok ? 'connected' : 'error')
    } catch (error) {
      setApiStatus('disconnected')
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input.trim(), sources: null }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Add placeholder for assistant response
    const assistantMessage = { role: 'assistant', content: '', sources: [], isStreaming: true }
    setMessages(prev => [...prev, assistantMessage])

    try {
      const response = await fetch(STREAM_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content, top_k: topK }),
        mode: 'cors'
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let fullResponse = ''
      let sources = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.error) {
                throw new Error(data.error)
              }

              if (data.token) {
                fullResponse += data.token
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: fullResponse
                  }
                  return updated
                })
              }

              if (data.done) {
                sources = data.sources || []
              }
            } catch (parseError) {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }

      // Finalize message with sources
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: fullResponse,
          sources: sources,
          isStreaming: false
        }
        return updated
      })

    } catch (error) {
      console.error('Stream error:', error)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: `❌ Błąd: ${error.message}`,
          sources: [],
          isStreaming: false
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const clearHistory = () => {
    setMessages([])
  }

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="icon">⚖️</span>
          <span>RAG Lex</span>
        </div>

        <div className="info-box">
          System wykorzystuje technikę RAG (Retrieval-Augmented Generation),
          aby odpowiadać na pytania w oparciu o bazę aktów prawnych Sejmu.
        </div>

        <div className="settings-section">
          <h3>Ustawienia</h3>
          <div className="slider-container">
            <label htmlFor="topk">Liczba dokumentów źródłowych</label>
            <input
              type="range"
              id="topk"
              min="1"
              max="10"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
            />
            <span className="slider-value">top_k: {topK}</span>
          </div>
        </div>

        <button className="clear-btn" onClick={clearHistory}>
          🗑️ Wyczyść historię czatu
        </button>

        <div className={`status-indicator ${apiStatus}`}>
          {apiStatus === 'connected' && '✅ Połączono z API'}
          {apiStatus === 'disconnected' && '❌ Brak połączenia z API'}
          {apiStatus === 'checking' && '🔄 Sprawdzanie...'}
          {apiStatus === 'error' && '⚠️ Błąd API'}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="chat-header">
          <h1>⚖️ RAG Lex - Inteligentny Asystent Prawny</h1>
          <p>Zadaj pytanie dotyczące polskich ustaw z 2020 roku.</p>
        </header>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="empty-state">
              <p>Zadaj pytanie, aby rozpocząć rozmowę...</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <Message key={index} message={msg} />
          ))}

          <div ref={messagesEndRef} />
        </div>

        <form className="input-container" onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="O co chcesz zapytać?"
              rows={1}
              disabled={isLoading}
            />
            <button
              type="submit"
              className="send-btn"
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}

function Message({ message }) {
  const [showSources, setShowSources] = useState(false)

  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {message.content || (message.isStreaming && <LoadingDots />)}
      </div>

      {message.sources && message.sources.length > 0 && (
        <>
          <button
            className="sources-toggle"
            onClick={() => setShowSources(!showSources)}
          >
            📚 {showSources ? 'Ukryj' : 'Zobacz'} źródła ({message.sources.length})
          </button>

          {showSources && (
            <div className="sources-list">
              {message.sources.map((source, idx) => (
                <div key={idx} className="source-item">
                  <div className="source-header">
                    {source.url ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-citation"
                      >
                        🔗 {source.citation}
                      </a>
                    ) : (
                      <span className="source-citation">{source.citation}</span>
                    )}
                    <span className="source-score">
                      Similarity: {(distanceToSimilarity(source.score) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="source-text">
                    {source.text?.slice(0, 500)}...
                  </p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function LoadingDots() {
  return (
    <div className="loading-dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
  )
}

export default App
