import { useState, useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: 'Hola, soy el asistente del Formulario 22. ¿En qué puedo ayudarte hoy?',
  sources: [],
}

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function ChatWindow({ suggestedQuestions = [], loadingQuestions = false }) {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text) {
    const msg = (text || input).trim()
    if (!msg || loading) return

    setInput('')
    setLoading(true)

    // Agregar mensaje del usuario y placeholder del asistente
    setMessages(prev => [
      ...prev,
      { role: 'user', content: msg, sources: [] },
      { role: 'assistant', content: '', sources: [], streaming: true },
    ])

    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // Guardar línea incompleta para el siguiente ciclo

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            handleStreamEvent(event)
          } catch {
            // Ignorar líneas mal formadas
          }
        }
      }
    } catch (err) {
      setMessages(prev => {
        const msgs = [...prev]
        msgs[msgs.length - 1] = {
          role: 'assistant',
          content: '⚠️ Error de conexión con el servidor. Intenta nuevamente.',
          sources: [],
          streaming: false,
        }
        return msgs
      })
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  async function fetchFallbackQuestions() {
    try {
      const res = await fetch(`${API_BASE}/api/suggested-questions?t=${Date.now()}`)
      if (!res.ok) return []
      const data = await res.json()
      return Array.isArray(data) ? data.slice(0, 3) : []
    } catch {
      return []
    }
  }

  function handleStreamEvent(event) {
    setMessages(prev => {
      const msgs = [...prev]
      const last = msgs[msgs.length - 1]

      if (event.type === 'token') {
        msgs[msgs.length - 1] = { ...last, content: last.content + event.content }
      } else if (event.type === 'sources') {
        msgs[msgs.length - 1] = { ...last, sources: event.sources }
      } else if (event.type === 'done') {
        const related = event.related_questions || []
        msgs[msgs.length - 1] = {
          ...last,
          streaming: false,
          related_questions: related,
        }
        if (related.length === 0) {
          const idx = msgs.length - 1
          fetchFallbackQuestions().then(fallback => {
            if (fallback.length > 0) {
              setMessages(curr => {
                const copy = [...curr]
                if (copy[idx]) {
                  copy[idx] = { ...copy[idx], related_questions: fallback }
                }
                return copy
              })
            }
          })
        }
      } else if (event.type === 'error') {
        msgs[msgs.length - 1] = {
          role: 'assistant',
          content: `⚠️ ${event.content}`,
          sources: [],
          streaming: false,
        }
      }

      return msgs
    })
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <MessageBubble
            key={i}
            role={m.role}
            content={m.content}
            sources={m.sources}
            relatedQuestions={m.related_questions}
            streaming={m.streaming}
            onSendMessage={sendMessage}
          />
        ))}

        {messages.length === 1 && loadingQuestions && (
          <div className="suggested-questions">
            <p className="questions-loading-label">
              <span className="pulse">⏳</span> Cargando preguntas sugeridas...
            </p>
            <div className="questions-skeleton">
              <div className="question-skeleton-item" />
              <div className="question-skeleton-item" />
              <div className="question-skeleton-item" />
            </div>
          </div>
        )}

        {messages.length === 1 && !loadingQuestions && suggestedQuestions.length > 0 && (
          <div className="suggested-questions">
            <p className="suggested-questions-label">Preguntas sugeridas:</p>
            <div className="suggested-questions-list">
              {suggestedQuestions.map(q => (
                <button key={q} onClick={() => sendMessage(q)} className="suggested-question-btn">
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Escribe tu consulta sobre el F22..."
          rows={1}
          className="chat-textarea"
          disabled={loading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="chat-send-btn"
          style={{ background: input.trim() && !loading ? 'var(--sii-azul)' : '#b0bac8' }}
        >
          {loading ? '...' : 'Enviar'}
        </button>
      </div>
    </div>
  )
}
