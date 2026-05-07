import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const TYPE_COLORS = {
  pdf:  { bg: '#E6F1FB', color: '#0B4C8C', label: 'PDF' },
  docx: { bg: '#f0f0f0', color: '#5F5E5A', label: 'Word' },
  xlsx: { bg: '#e6f4ea', color: '#1a6b2e', label: 'Excel' },
}

function TypeBadge({ type }) {
  const t = TYPE_COLORS[type] || { bg: '#eee', color: '#555', label: type.toUpperCase() }
  return (
    <span style={{
      background: t.bg, color: t.color, fontSize: '0.72rem',
      fontWeight: 700, padding: '2px 7px', marginLeft: '0.4rem',
    }}>
      {t.label}
    </span>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const [docs, setDocs] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)

  useEffect(() => {
    axios.get('/api/documents')
      .then(r => setDocs(r.data))
      .catch(() => setDocs([]))
      .finally(() => setDocsLoading(false))
  }, [])

  return (
    <main>
      {/* Hero */}
      <section style={{
        background: 'linear-gradient(135deg, var(--sii-azul) 60%, var(--sii-azul-medio))',
        color: '#fff', padding: '5rem 2rem 4rem', textAlign: 'center',
      }}>
        <p style={{ fontSize: '0.85rem', letterSpacing: '0.12em', opacity: 0.75, marginBottom: '0.75rem' }}>
          SERVICIO DE IMPUESTOS INTERNOS — CHILE
        </p>
        <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.8rem)', fontWeight: 700, lineHeight: 1.2, marginBottom: '1rem' }}>
          Formulario 22 — Declaración de Renta
        </h1>
        <p style={{ fontSize: '1.1rem', opacity: 0.88, maxWidth: '560px', margin: '0 auto 2rem' }}>
          Consulta inteligente basada en documentos oficiales del SII.
          Respuestas precisas con referencia a la sección exacta del formulario.
        </p>
        <button
          onClick={() => navigate('/chat')}
          style={{
            background: 'var(--sii-naranja)', color: '#fff', border: 'none',
            padding: '0.75rem 2rem', fontSize: '1rem', fontWeight: 600,
          }}
          onMouseEnter={e => e.target.style.background = '#C04828'}
          onMouseLeave={e => e.target.style.background = 'var(--sii-naranja)'}
        >
          Hacer una consulta →
        </button>
      </section>

      {/* Qué es el F22 */}
      <section style={{ padding: '3.5rem 2rem', maxWidth: '900px', margin: '0 auto' }}>
        <h2 style={{ color: 'var(--sii-azul)', marginBottom: '1.5rem', fontSize: '1.4rem' }}>
          ¿Qué es el Formulario 22?
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {[
            {
              icon: '📋',
              title: 'Declaración Anual',
              desc: 'Documento oficial donde los contribuyentes declaran sus rentas anuales ante el SII de Chile.',
            },
            {
              icon: '🔢',
              title: 'Códigos de Línea',
              desc: 'Contiene secciones numeradas con códigos de línea (ej: línea 1, código 159) para cada tipo de renta.',
            },
            {
              icon: '📅',
              title: 'Plazo Anual',
              desc: 'El proceso de declaración se realiza cada año durante el período de renta establecido por el SII.',
            },
            {
              icon: '⚖️',
              title: 'Obligación Tributaria',
              desc: 'Incluye instrucciones, ejemplos y tablas de referencia para el correcto llenado del formulario.',
            },
          ].map(c => (
            <div key={c.title} style={{
              background: '#fff', padding: '1.25rem 1.5rem',
              borderLeft: '3px solid var(--sii-azul)',
              boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
            }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{c.icon}</div>
              <h3 style={{ color: 'var(--sii-azul)', marginBottom: '0.4rem', fontSize: '1rem' }}>{c.title}</h3>
              <p style={{ color: 'var(--sii-gris)', fontSize: '0.9rem' }}>{c.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Cómo funciona */}
      <section style={{ background: 'var(--sii-gris-claro)', padding: '3.5rem 2rem' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <h2 style={{ color: 'var(--sii-azul)', marginBottom: '2rem', fontSize: '1.4rem' }}>
            ¿Cómo funciona el chatbot?
          </h2>
          <div style={{ display: 'flex', gap: '0', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            {[
              { n: '1', title: 'Escribe tu pregunta', desc: 'Ingresa tu consulta sobre el F22 en lenguaje natural.' },
              { n: '2', title: 'Búsqueda semántica', desc: 'El sistema busca en los documentos oficiales los fragmentos más relevantes.' },
              { n: '3', title: 'Respuesta con fuente', desc: 'Recibe una respuesta precisa con la referencia exacta al documento.' },
            ].map((step, i) => (
              <div key={step.n} style={{ display: 'flex', alignItems: 'flex-start', flex: '1 1 200px' }}>
                <div style={{ textAlign: 'center', minWidth: '180px' }}>
                  <div style={{
                    width: '48px', height: '48px', background: 'var(--sii-azul)',
                    color: '#fff', fontSize: '1.3rem', fontWeight: 700,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 0.75rem',
                  }}>
                    {step.n}
                  </div>
                  <h3 style={{ color: 'var(--sii-azul)', fontSize: '0.95rem', marginBottom: '0.4rem' }}>{step.title}</h3>
                  <p style={{ color: 'var(--sii-gris)', fontSize: '0.85rem' }}>{step.desc}</p>
                </div>
                {i < 2 && (
                  <div style={{ flex: 1, height: '2px', background: 'var(--sii-azul)', marginTop: '24px', opacity: 0.3 }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Documentos disponibles */}
      <section style={{ padding: '3.5rem 2rem', maxWidth: '900px', margin: '0 auto' }}>
        <h2 style={{ color: 'var(--sii-azul)', marginBottom: '1.5rem', fontSize: '1.4rem' }}>
          Documentos indexados ({docs.length})
        </h2>
        {docsLoading ? (
          <p style={{ color: 'var(--sii-gris)' }}>Cargando documentos...</p>
        ) : docs.length === 0 ? (
          <p style={{ color: 'var(--sii-gris)' }}>No hay documentos. Ejecute /ingest primero.</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.5rem' }}>
            {docs.map(d => (
              <div key={d.filename} style={{
                background: '#fff', padding: '0.6rem 0.9rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                borderLeft: '3px solid var(--sii-azul-claro)',
                fontSize: '0.85rem',
              }}>
                <span style={{ color: '#333', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '200px' }}>
                  {d.filename}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexShrink: 0 }}>
                  <TypeBadge type={d.file_type} />
                  <span style={{ color: 'var(--sii-gris)', fontSize: '0.75rem' }}>{d.chunk_count} chunks</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer style={{
        background: '#07305A', color: 'rgba(255,255,255,0.65)',
        textAlign: 'center', padding: '1.25rem', fontSize: '0.83rem',
      }}>
        Sistema basado en documentos oficiales SII · Solo para uso interno
      </footer>
    </main>
  )
}
