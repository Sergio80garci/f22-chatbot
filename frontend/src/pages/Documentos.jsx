import { useEffect, useState } from 'react'
import axios from 'axios'

const TYPE_STYLE = {
  pdf:  { bg: '#E6F1FB', color: '#0B4C8C' },
  docx: { bg: '#f0f0f0', color: '#5F5E5A' },
  xlsx: { bg: '#e6f4ea', color: '#1a6b2e' },
}

export default function Documentos() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios.get('/api/documents')
      .then(r => setDocs(r.data))
      .catch(() => setError('No se pudo conectar con el backend.'))
      .finally(() => setLoading(false))
  }, [])

  const totalChunks = docs.reduce((s, d) => s + d.chunk_count, 0)

  return (
    <main className="page-container" style={{ height: '100%', overflowY: 'auto' }}>
      <h1 style={{ color: 'var(--sii-azul)', fontSize: 'clamp(1.2rem, 4vw, 1.4rem)', marginBottom: '0.4rem' }}>
        Documentos indexados
      </h1>
      {!loading && !error && (
        <p style={{ color: 'var(--sii-gris)', fontSize: 'clamp(0.75rem, 2vw, 0.88rem)', marginBottom: '1.5rem' }}>
          {docs.length} documentos · {totalChunks} chunks almacenados en ChromaDB
        </p>
      )}

      {loading && <p style={{ color: 'var(--sii-gris)' }}>Cargando...</p>}
      {error && (
        <p style={{ color: 'var(--sii-naranja)', background: 'var(--sii-naranja-cl)', padding: 'clamp(0.5rem, 2vw, 0.75rem) 1rem', borderRadius: '4px' }}>
          ⚠️ {error}
        </p>
      )}

      {!loading && !error && docs.length === 0 && (
        <p style={{ color: 'var(--sii-gris)' }}>
          No hay documentos indexados. Ejecute <code>/ingest</code> primero.
        </p>
      )}

      {!loading && docs.length > 0 && (
        <div style={{ overflowX: 'auto', width: '100%' }}>
          <table className="responsive-table">
            <thead>
              <tr style={{ background: 'var(--sii-azul)', color: '#fff' }}>
                <th style={{ padding: 'clamp(0.5rem, 1vw, 0.65rem) clamp(0.5rem, 1vw, 1rem)', textAlign: 'left', fontWeight: 600 }}>Nombre</th>
                <th style={{ padding: 'clamp(0.5rem, 1vw, 0.65rem) clamp(0.3rem, 1vw, 0.75rem)', textAlign: 'center', fontWeight: 600 }}>Tipo</th>
                <th style={{ padding: 'clamp(0.5rem, 1vw, 0.65rem) clamp(0.5rem, 1vw, 1rem)', textAlign: 'right', fontWeight: 600 }}>Chunks</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d, i) => {
                const ts = TYPE_STYLE[d.file_type] || { bg: '#eee', color: '#555' }
                return (
                  <tr
                    key={d.filename}
                    style={{ background: i % 2 === 0 ? '#fff' : 'var(--sii-gris-claro)' }}
                  >
                    <td style={{ padding: 'clamp(0.4rem, 1vw, 0.55rem) clamp(0.5rem, 1vw, 1rem)', color: '#222', wordBreak: 'break-word', overflowWrap: 'break-word' }}>
                      <div>{d.filename}</div>
                      <div style={{ color: 'var(--sii-gris)', fontSize: 'clamp(0.7rem, 1.5vw, 0.8rem)', marginTop: '0.25rem' }}>
                        {d.summary || 'Generando resumen...'}
                      </div>
                    </td>
                    <td style={{ padding: 'clamp(0.4rem, 1vw, 0.55rem) clamp(0.3rem, 1vw, 0.75rem)', textAlign: 'center' }}>
                      <span style={{
                        background: ts.bg, color: ts.color,
                        fontSize: 'clamp(0.65rem, 1.5vw, 0.72rem)', fontWeight: 700, padding: '2px 8px', borderRadius: '3px',
                      }}>
                        {d.file_type.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: 'clamp(0.4rem, 1vw, 0.55rem) clamp(0.5rem, 1vw, 1rem)', textAlign: 'right', color: 'var(--sii-gris)' }}>
                      {d.chunk_count}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
