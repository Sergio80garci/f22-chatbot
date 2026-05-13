import { useState, useEffect } from 'react'
import { api } from '../api'
import ChatWindow from '../components/ChatWindow'

const FALLBACK_POOL = [
  '¿Cómo declaro mis honorarios en el F22?',
  '¿Qué es el código 159 del F22?',
  '¿Cuándo vence el plazo para declarar la renta?',
  '¿Qué es el crédito por gastos de educación?',
  '¿Cómo declaro rentas de arriendo?',
  '¿Qué es el préstamo solidario del Estado?',
  '¿Cómo se declaran las cotizaciones previsionales?',
  '¿Qué pasa si no declaro a tiempo el F22?',
  '¿Cómo funciona el crédito por donaciones?',
  '¿Qué documentos necesito para declarar el F22?',
]

function pickRandom(arr, n) {
  return [...arr].sort(() => Math.random() - 0.5).slice(0, n)
}

export default function Chat() {
  const [suggestedQuestions, setSuggestedQuestions] = useState([])
  const [loadingQuestions, setLoadingQuestions] = useState(true)

  useEffect(() => {
    async function fetchSuggestedQuestions() {
      try {
        const res = await api.get(`/api/suggested-questions?t=${Date.now()}`)
        const pool = Array.isArray(res.data) && res.data.length > 0 ? res.data : FALLBACK_POOL
        setSuggestedQuestions(pickRandom(pool, 3))
      } catch {
        setSuggestedQuestions(pickRandom(FALLBACK_POOL, 3))
      } finally {
        setLoadingQuestions(false)
      }
    }
    fetchSuggestedQuestions()
  }, [])

  return (
    <div className="chat-page-outer">
      <header style={{
        background: 'var(--sii-azul)',
        color: '#fff',
        padding: 'clamp(0.75rem, 2vw, 1rem) clamp(0.75rem, 2vw, 1.5rem)',
        flexShrink: 0,
      }}>
        <h1 style={{ fontSize: 'clamp(0.95rem, 3vw, 1.1rem)', fontWeight: 700 }}>
          Consulta sobre F22
        </h1>
        <p style={{ fontSize: 'clamp(0.75rem, 2vw, 0.82rem)', opacity: 0.75, marginTop: '0.2rem' }}>
          Las respuestas se generan exclusivamente desde documentos oficiales del SII
        </p>
      </header>

      <div className="chat-page-body">
        <ChatWindow
          suggestedQuestions={suggestedQuestions}
          loadingQuestions={loadingQuestions}
        />
      </div>
    </div>
  )
}
