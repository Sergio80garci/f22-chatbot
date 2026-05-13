import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'

const PAGE_INFO = {
  '/': {
    title: 'Asistente F22',
    subtitle: 'Información oficial sobre el Formulario 22 de Declaración de Renta',
  },
  '/chat': {
    title: 'Consulta sobre F22',
    subtitle: 'Las respuestas se generan exclusivamente desde documentos oficiales del SII',
  },
  '/documentos': {
    title: 'Documentos indexados',
    subtitle: 'Fuentes oficiales del Formulario 22 disponibles para consulta',
  },
  '/todio': {
    title: 'Arquitectura del sistema',
    subtitle: 'Blueprint de los componentes del Asistente F22',
  },
}

const styles = {
  nav: {
    background: 'var(--sii-azul)',
    padding: '0 clamp(0.75rem, 2vw, 1.5rem)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '56px',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    boxShadow: '0 2px 6px rgba(0,0,0,0.25)',
    flexWrap: 'wrap',
  },
  brand: {
    color: '#fff',
    fontWeight: 700,
    fontSize: 'clamp(0.85rem, 2vw, 1.05rem)',
    letterSpacing: '0.01em',
    display: 'flex',
    alignItems: 'center',
    gap: 'clamp(0.4rem, 1vw, 0.65rem)',
    textDecoration: 'none',
  },
  links: {
    display: 'flex',
    alignItems: 'center',
    gap: 'clamp(0.1rem, 1vw, 0.25rem)',
    listStyle: 'none',
  },
  link: {
    color: 'rgba(255,255,255,0.85)',
    padding: 'clamp(0.3rem, 1vw, 0.4rem) clamp(0.5rem, 1.5vw, 0.85rem)',
    fontSize: 'clamp(0.8rem, 1.5vw, 0.9rem)',
    transition: 'background 0.15s',
    borderRadius: '2px',
    whiteSpace: 'nowrap',
  },
  linkActive: {
    color: '#fff',
    background: 'rgba(255,255,255,0.15)',
  },
  cta: {
    background: 'var(--sii-naranja)',
    color: '#fff',
    border: 'none',
    padding: 'clamp(0.3rem, 1vw, 0.4rem) clamp(0.7rem, 1.5vw, 1rem)',
    fontSize: 'clamp(0.75rem, 1.5vw, 0.88rem)',
    fontWeight: 600,
    marginLeft: 'clamp(0.3rem, 1vw, 0.5rem)',
    transition: 'background 0.15s',
    borderRadius: '2px',
    whiteSpace: 'nowrap',
    cursor: 'pointer',
  },
  hamburger: {
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: '1.4rem',
    lineHeight: 1,
    cursor: 'pointer',
    padding: '0.25rem',
  },
  mobileMenu: {
    position: 'absolute',
    top: '56px',
    left: 0,
    right: 0,
    background: 'var(--sii-azul)',
    flexDirection: 'column',
    gap: 0,
    padding: '0.5rem 0',
    boxShadow: '0 4px 6px rgba(0,0,0,0.15)',
  },
}


export default function Navbar() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { pathname } = useLocation()
  // Match exacto, sino fallback al prefijo de primer segmento (ej. /todio/xyz → /todio)
  const matchKey = PAGE_INFO[pathname]
    ? pathname
    : Object.keys(PAGE_INFO).find(k => k !== '/' && pathname.startsWith(k + '/'))
  const page = PAGE_INFO[matchKey] || PAGE_INFO['/']

  const linkStyle = ({ isActive }) => ({
    ...styles.link,
    ...(isActive ? styles.linkActive : {}),
  })

  return (
    <>
      <nav style={styles.nav}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(0.5rem, 1.5vw, 0.9rem)', minWidth: 0, flex: 1 }}>
          <NavLink to="/" style={{ ...styles.brand, background: '#fff', borderRadius: '4px', padding: '3px 8px', maxHeight: '46px', boxSizing: 'border-box', flexShrink: 0 }}>
            <img
              src={`${import.meta.env.BASE_URL}sii-logo.png`}
              alt="Servicio de Impuestos Internos"
              style={{ height: '32px', maxHeight: '32px', width: 'auto', display: 'block', objectFit: 'contain' }}
            />
          </NavLink>
          <div className="nav-page-info" style={{ color: '#fff', minWidth: 0, overflow: 'hidden' }}>
            <div style={{ fontSize: 'clamp(0.85rem, 1.8vw, 1rem)', fontWeight: 700, lineHeight: 1.2, whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {page.title}
            </div>
            <div style={{ fontSize: 'clamp(0.65rem, 1.3vw, 0.75rem)', opacity: 0.75, marginTop: '2px', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {page.subtitle}
            </div>
          </div>
        </div>

        {/* Desktop menu */}
        <ul className="nav-desktop" style={styles.links}>
          <li><NavLink to="/" style={linkStyle} end>Inicio</NavLink></li>
          <li><NavLink to="/chat" style={linkStyle}>Chatbot</NavLink></li>
          <li><NavLink to="/documentos" style={linkStyle}>Documentos</NavLink></li>
          <li>
            <button
              style={styles.cta}
              onClick={() => navigate('/chat')}
              onMouseEnter={e => e.target.style.background = '#C04828'}
              onMouseLeave={e => e.target.style.background = 'var(--sii-naranja)'}
            >
              Consultar
            </button>
          </li>
        </ul>

        {/* Mobile hamburger */}
        <button
          className="nav-hamburger"
          style={styles.hamburger}
          onClick={() => setOpen(!open)}
          aria-label="Menú"
        >
          ☰
        </button>
      </nav>

      {open && (
        <ul style={{ ...styles.mobileMenu, display: 'flex', width: '100%' }}>
          <li style={{ width: '100%' }}>
            <NavLink to="/" style={linkStyle} onClick={() => setOpen(false)} end>
              <span style={{ display: 'block', padding: '0.6rem 1rem' }}>Inicio</span>
            </NavLink>
          </li>
          <li style={{ width: '100%' }}>
            <NavLink to="/chat" style={linkStyle} onClick={() => setOpen(false)}>
              <span style={{ display: 'block', padding: '0.6rem 1rem' }}>Chatbot F22</span>
            </NavLink>
          </li>
          <li style={{ width: '100%' }}>
            <NavLink to="/documentos" style={linkStyle} onClick={() => setOpen(false)}>
              <span style={{ display: 'block', padding: '0.6rem 1rem' }}>Documentos</span>
            </NavLink>
          </li>
          <li style={{ width: '100%' }}>
            <button
              style={{ ...styles.cta, width: '100%', marginLeft: 0, borderRadius: 0 }}
              onClick={() => { navigate('/chat'); setOpen(false) }}
            >
              Consultar ahora
            </button>
          </li>
        </ul>
      )}
    </>
  )
}
