import { useEffect, useState } from 'react'
import { api } from '../api'

const FRONTEND_VERSION = '2.1.0'

export default function Footer() {
  const [backendVersion, setBackendVersion] = useState(null)

  useEffect(() => {
    api.get('/api/version')
      .then(r => setBackendVersion(r.data))
      .catch(() => setBackendVersion(null))
  }, [])

  return (
    <footer style={{
      background: 'var(--sii-azul)',
      color: 'rgba(255,255,255,0.65)',
      fontSize: '0.72rem',
      padding: '0.6rem clamp(0.75rem, 2vw, 1.5rem)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '0.4rem',
      flexShrink: 0,
    }}>
      <span>© {new Date().getFullYear()} Servicio de Impuestos Internos — Asistente F22</span>
      <span style={{ display: 'flex', gap: '1rem' }}>
        <span>Frontend v{FRONTEND_VERSION}</span>
        {backendVersion
          ? <span>Backend v{backendVersion.version} · {backendVersion.release_date}</span>
          : <span>Backend —</span>
        }
      </span>
    </footer>
  )
}
