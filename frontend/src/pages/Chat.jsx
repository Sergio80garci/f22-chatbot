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
      <div className="chat-page-body">
        <ChatWindow
          suggestedQuestions={suggestedQuestions}
          loadingQuestions={loadingQuestions}
        />
      </div>
    </div>
  )
}
