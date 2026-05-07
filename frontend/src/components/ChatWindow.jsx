import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import MessageBubble from './MessageBubble'

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: 'Hola, soy el asistente del Formulario 22. ¿En qué puedo ayudarte hoy?',
  sources: [],
}

export default function ChatWindow({ suggestedQuestions = [], loadingQuestions = false }) {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text) {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, sources: [] }])
    setLoading(true)

    try {
      const res = await axios.post('/api/chat', { message: msg, session_id: sessionId })
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: res.data.answer, sources: res.data.sources || [], related_questions: res.data.related_questions || [] },
      ])
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Error de conexión con el servidor.'
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `⚠️ ${errMsg}`, sources: [] },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="chat-container">
      {/* Messages area */}
      <div className="chat-messages">
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} sources={m.sources} relatedQuestions={m.related_questions} onSendMessage={sendMessage} />
        ))}

        {loading && (
          <div className="loading-indicator">
            <span className="pulse">⏳</span>
            Buscando en documentos F22...
          </div>
        )}

        {/* Suggested questions (only on empty state) */}
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
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="suggested-question-btn"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-bar">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Escribe tu consulta sobre el F22..."
          rows={1}
          className="chat-textarea"
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
          className="chat-send-btn"
          style={{
            background: input.trim() && !loading ? 'var(--sii-azul)' : '#b0bac8',
          }}
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
