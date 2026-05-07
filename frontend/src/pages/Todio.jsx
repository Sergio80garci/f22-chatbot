import { useNavigate } from 'react-router-dom'
import { useState, useMemo } from 'react'
import '../todio.css'

// ── Genera el path SVG de un engranaje centrado en (0,0) ──
function gearPath(teeth, innerR, outerR) {
  const f = n => n.toFixed(2)
  const step = (Math.PI * 2) / teeth
  const tw = step * 0.42
  let d = ''
  for (let i = 0; i < teeth; i++) {
    const a    = i * step - Math.PI / 2
    const aEnd = a + tw
    const ix0 = innerR * Math.cos(a),            iy0 = innerR * Math.sin(a)
    const ox0 = outerR * Math.cos(a + 0.06),     oy0 = outerR * Math.sin(a + 0.06)
    const ox1 = outerR * Math.cos(aEnd - 0.06),  oy1 = outerR * Math.sin(aEnd - 0.06)
    const ix1 = innerR * Math.cos(aEnd),          iy1 = innerR * Math.sin(aEnd)
    if (i === 0) d += `M ${f(ix0)} ${f(iy0)}`
    else         d += ` A ${innerR} ${innerR} 0 0 1 ${f(ix0)} ${f(iy0)}`
    d += ` L ${f(ox0)} ${f(oy0)} L ${f(ox1)} ${f(oy1)} L ${f(ix1)} ${f(iy1)}`
  }
  const sx = f(innerR * Math.cos(-Math.PI / 2))
  const sy = f(innerR * Math.sin(-Math.PI / 2))
  return d + ` A ${innerR} ${innerR} 0 0 1 ${sx} ${sy} Z`
}

// ── Paleta "Blueprint Profesional":  7 colores distintos ──
// ── Más oscuro = más central/importante en la arquitectura ─
export const COMPONENTES = {
  langchain: {
    id: 'langchain', nombre: 'LangChain', version: '>=0.2', rol: 'Orquestador RAG',
    descripcion: 'Orquesta el pipeline RAG completo. Conecta ChromaDB, Ollama y los prompts del F22 para generar respuestas citadas con referencia exacta al documento fuente.',
    color: '#1B3F7A',     // Navy profundo — núcleo del sistema
    accentColor: '#1B3F7A',
    detalles: [
      ['Chain',    'RetrievalQA'],
      ['Retriever','ChromaDB top-5'],
      ['LLM',      'Ollama llama3.2'],
      ['Prompt',   'Template SII personalizado'],
      ['Idioma',   'Español chileno'],
    ],
    relacionados: ['ollama', 'chromadb', 'fastapi'],
    gear: { teeth: 12, outerR: 65, innerR: 50, holeR: 18, speed: 28, cw: true,  cx: 0,    cy: 0   },
  },
  fastapi: {
    id: 'fastapi', nombre: 'FastAPI', version: 'latest', rol: 'Backend API REST',
    descripcion: 'Expone el chatbot como servicio HTTP con validación Pydantic, CORS y documentación automática en /docs. Sirve /chat, /documents y /suggested-questions.',
    color: '#1B6B3A',     // Verde bosque — API/backend
    accentColor: '#1B6B3A',
    detalles: [
      ['Puerto',    '8001'],
      ['Endpoints', '/chat, /documents, /suggested-questions'],
      ['Validación','Pydantic v2'],
      ['Docs',      'localhost:8001/docs'],
      ['Middleware','CORS + logging'],
    ],
    relacionados: ['langchain', 'react'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: 115,  cy: 0   },
  },
  ollama: {
    id: 'ollama', nombre: 'Ollama + LLM', version: 'latest', rol: 'Motor LLM Local',
    descripcion: 'Ejecuta llama3.2 y nomic-embed-text completamente en local. Sin costo de API, sin datos enviados a la nube. Privacidad total de los documentos tributarios.',
    color: '#B03A00',     // Naranja tostado — motor IA
    accentColor: '#B03A00',
    detalles: [
      ['Modelo LLM', 'llama3.2:latest (2.0 GB)'],
      ['Embeddings', 'nomic-embed-text (274 MB)'],
      ['Puerto',     '11434'],
      ['Inferencia', '100% local'],
      ['Privacidad', 'Datos nunca salen del equipo'],
    ],
    relacionados: ['langchain', 'nomic'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: 58,   cy: -100 },
  },
  chromadb: {
    id: 'chromadb', nombre: 'ChromaDB', version: '>=0.5', rol: 'Base Vectorial',
    descripcion: 'Almacena embeddings de los documentos F22. Ante cada consulta busca los 5 chunks más similares semánticamente y los entrega como contexto al LLM.',
    color: '#6B1B6B',     // Púrpura oscuro — base de datos
    accentColor: '#6B1B6B',
    detalles: [
      ['Versión',   '>=0.5'],
      ['Ruta',      './data/chroma_db'],
      ['Búsqueda',  'Similitud coseno'],
      ['Top-K',     '5 chunks más relevantes'],
      ['Colección', 'f22_documentos'],
    ],
    relacionados: ['langchain', 'nomic'],
    gear: { teeth: 8,  outerR: 45, innerR: 34, holeR: 12, speed: 23, cw: false, cx: -55,  cy: -95  },
  },
  react: {
    id: 'react', nombre: 'React + Vite', version: 'v18 + v5.4', rol: 'Frontend SPA',
    descripcion: 'Aplicación de página única con estilo SII. Chatbot integrado, visor de documentos fuente, página informativa del F22 y esta página de arquitectura.',
    color: '#006699',     // Azul acero — frontend tech
    accentColor: '#006699',
    detalles: [
      ['React',  'v18'],
      ['Vite',   'v5.4.21'],
      ['Puerto', '5173 (dev)'],
      ['Proxy',  '→ localhost:8001'],
      ['Rutas',  '/, /chat, /documentos, /todio'],
    ],
    relacionados: ['fastapi'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: -115, cy: 0   },
  },
  nomic: {
    id: 'nomic', nombre: 'nomic-embed', version: 'latest', rol: 'Motor Embeddings',
    descripcion: 'Convierte texto en vectores de 768 dimensiones vía Ollama. Usado en la ingestión del F22 y en cada consulta para la búsqueda semántica en tiempo real.',
    color: '#007070',     // Teal — ML/embeddings
    accentColor: '#007070',
    detalles: [
      ['Tamaño',     '274 MB'],
      ['Dimensiones','768'],
      ['Vía',        'Ollama API'],
      ['Uso',        'Ingestión + búsqueda en tiempo real'],
      ['Cobertura',  'Multilingüe (español incluido)'],
    ],
    relacionados: ['ollama', 'chromadb'],
    gear: { teeth: 8,  outerR: 45, innerR: 34, holeR: 12, speed: 23, cw: false, cx: -55,  cy: 95   },
  },
  python: {
    id: 'python', nombre: 'Python + OCR', version: '3.11.9', rol: 'Runtime + Ingestión',
    descripcion: 'Runtime del backend y pipeline de ingestión. Tesseract OCR extrae texto de PDFs e imágenes del F22. Soporta PDF, Word (.docx), Excel (.xlsx) y PNG/JPG.',
    color: '#7A5200',     // Ámbar oscuro — desarrollo/runtime
    accentColor: '#7A5200',
    detalles: [
      ['Versión',  '3.11.9'],
      ['OCR',      'Tesseract 5 + pytesseract'],
      ['Idioma',   'Español (spa)'],
      ['Formatos', 'PDF, DOCX, XLSX, PNG, JPG'],
      ['Librerías','FastAPI, LangChain, ChromaDB'],
    ],
    relacionados: ['fastapi', 'langchain'],
    gear: { teeth: 8,  outerR: 43, innerR: 32, holeR: 12, speed: 23, cw: false, cx: 54,   cy: 94   },
  },
  netlify: {
    id: 'netlify', nombre: 'Netlify', version: 'Free Tier', rol: 'Hosting Frontend',
    descripcion: 'Plataforma de hosting estático que sirve el frontend React en producción. Deploy automático desde GitHub, CDN global con más de 100 edge locations, HTTPS automático con Let\'s Encrypt y dominio personalizable. Reemplaza al localhost:5173 del entorno local — sin servidor que mantener.',
    color: '#00AD9F',
    accentColor: '#00AD9F',
    detalles: [
      ['Plan',       'Free (100 GB bandwidth/mes)'],
      ['Deploy',     'Git push → build → live automático'],
      ['CDN',        'Edge global · 99+ nodos'],
      ['HTTPS',      'Certificado Let\'s Encrypt automático'],
      ['Build',      'npm run build · publish: dist/'],
      ['URL',        'tu-app.netlify.app (o dominio propio)'],
    ],
    relacionados: ['react', 'railway'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: true, cx: 0, cy: 0 },
  },
  railway: {
    id: 'railway', nombre: 'Railway', version: '$5 crédito/mes', rol: 'Hosting Backend',
    descripcion: 'Plataforma cloud que ejecuta el backend FastAPI con ChromaDB persistente. Detecta Python automáticamente vía requirements.txt, soporta variables de entorno seguras y volúmenes de disco para mantener la base vectorial entre deploys. Reemplaza al localhost:8001 local.',
    color: '#7C3AED',
    accentColor: '#7C3AED',
    detalles: [
      ['Plan',       '$5 crédito gratis/mes (suficiente para demo)'],
      ['Runtime',    'Python 3.11 · detectado automático'],
      ['Start',      'uvicorn backend.api.main:app --host 0.0.0.0'],
      ['Volumen',    'Persistencia ChromaDB entre deploys'],
      ['Variables',  'GROQ_API_KEY, CHROMA_PATH, DOCS_PATH'],
      ['URL',        'tu-app.railway.app'],
    ],
    relacionados: ['fastapi', 'chromadb', 'groq'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 22, cw: false, cx: 0, cy: 0 },
  },
  groq: {
    id: 'groq', nombre: 'Groq API', version: 'Free Tier', rol: 'LLM en la Nube',
    descripcion: 'API gratuita que reemplaza a Ollama en el deploy cloud. Ejecuta Llama 3.2 (el mismo modelo) en hardware especializado LPU de Groq. Sin GPU local requerida, sin costo de inferencia y aproximadamente 10 veces más rápido que Ollama en CPU, con latencia de ~200ms en primera respuesta.',
    color: '#F97316',
    accentColor: '#F97316',
    detalles: [
      ['Modelos',    'llama3-8b-8192 · llama3-70b-8192'],
      ['Plan',       'Gratuito · rate limits generosos'],
      ['Latencia',   '~200ms primera respuesta (LPU)'],
      ['Reemplaza',  'Ollama llama3.2 · misma calidad'],
      ['Cambio',     'OLLAMA_BASE_URL → GROQ_API_KEY en .env'],
      ['API Key',    'console.groq.com → gratuita'],
    ],
    relacionados: ['langchain', 'railway'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: true, cx: 0, cy: 0 },
  },
}

export const ORDER = ['langchain','fastapi','ollama','chromadb','react','nomic','python']

const ABBR = { langchain:'LC', fastapi:'FA', ollama:'OL', chromadb:'CH', react:'RX', nomic:'NE', python:'PY', netlify:'NL', railway:'RW', groq:'GQ' }

// ── Calcula posición de etiqueta FUERA del cluster ────────
function labelPos(gear) {
  if (gear.cx === 0 && gear.cy === 0) {
    return { x: 0, y: gear.outerR + 22, anchor: 'middle' }
  }
  const mag   = Math.sqrt(gear.cx ** 2 + gear.cy ** 2)
  const nx    = gear.cx / mag
  const ny    = gear.cy / mag
  const pad   = gear.outerR + 20
  const anchor = nx > 0.45 ? 'start' : nx < -0.45 ? 'end' : 'middle'
  return { x: nx * pad, y: ny * pad, anchor }
}

// ── Engranaje SVG individual ──────────────────────────────
function Gear({ comp, hovered, onHover, onClick }) {
  const { gear, color, nombre, rol } = comp
  const path   = useMemo(
    () => gearPath(gear.teeth, gear.innerR, gear.outerR),
    [gear.teeth, gear.innerR, gear.outerR]
  )
  const isHov  = hovered === comp.id
  const lp     = labelPos(gear)

  return (
    <g
      transform={`translate(${gear.cx}, ${gear.cy})`}
      onMouseEnter={() => onHover(comp.id)}
      onMouseLeave={() => onHover(null)}
      onClick={() => onClick(comp.id)}
      style={{ cursor: 'pointer' }}
    >
      {/* Zona de click invisible (algo mayor que el engranaje) */}
      <circle r={gear.outerR + 6} fill="transparent" />

      {/* Engranaje escalable en hover */}
      <g style={{
        transform: isHov ? 'scale(1.12)' : 'scale(1)',
        transformBox: 'fill-box',
        transformOrigin: 'center',
        transition: 'transform 0.25s cubic-bezier(0.34,1.56,0.64,1)',
      }}>
        <g
          className={gear.cw ? 'gear-spin-cw' : 'gear-spin-ccw'}
          style={{ animationDuration: `${gear.speed}s`, transformOrigin: '0px 0px' }}
        >
          <path
            d={path}
            fill={color}
            style={{
              filter: isHov
                ? `drop-shadow(0 4px 12px ${color}90) drop-shadow(0 0 20px ${color}50)`
                : `drop-shadow(0 2px 4px ${color}40)`,
              transition: 'filter 0.25s',
            }}
          />
          {/* Anillo interior decorativo */}
          <circle r={gear.holeR + 4} fill="none" stroke={color} strokeWidth="1.5" opacity="0.3" />
          {/* Agujero */}
          <circle r={gear.holeR} fill="#ffffff" />
          <circle r={gear.holeR * 0.5} fill={color} opacity="0.12" />
          {/* Abreviación */}
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fill={color}
            fontSize={gear.holeR * 0.65}
            fontWeight="900"
            fontStyle="italic"
            style={{ userSelect: 'none' }}
          >
            {ABBR[comp.id]}
          </text>
        </g>
      </g>

      {/* Etiqueta posicionada HACIA FUERA del cluster */}
      <text
        x={lp.x} y={lp.y}
        textAnchor={lp.anchor}
        paintOrder="stroke"
        stroke="#ffffff"
        strokeWidth="4"
        strokeLinejoin="round"
        fill={isHov ? color : '#374151'}
        fontSize="11.5"
        fontWeight="800"
        fontStyle="italic"
        style={{ transition: 'fill 0.25s', pointerEvents: 'none', userSelect: 'none' }}
      >
        {nombre}
      </text>
      <text
        x={lp.x} y={lp.y + 14}
        textAnchor={lp.anchor}
        paintOrder="stroke"
        stroke="#ffffff"
        strokeWidth="3"
        strokeLinejoin="round"
        fill={isHov ? color : '#9e9c98'}
        fontSize="9"
        style={{ transition: 'fill 0.25s', pointerEvents: 'none', userSelect: 'none' }}
      >
        {rol}
      </text>

      {/* Indicador "click" — solo en hover */}
      {isHov && (
        <text
          x={lp.x} y={lp.y + 26}
          textAnchor={lp.anchor}
          fill={color}
          fontSize="8"
          fontWeight="700"
          style={{ pointerEvents: 'none', userSelect: 'none' }}
        >
          Ver detalles →
        </text>
      )}
    </g>
  )
}

// ── Personaje TODIO ───────────────────────────────────────
function TodioCharacter() {
  return (
    <svg viewBox="-82 -98 164 212" className="todio-drop" aria-label="TODIO">
      <defs>
        <radialGradient id="tdBodyGrad" cx="32%" cy="22%" r="72%">
          <stop offset="0%"   stopColor="#bfdbfe" />
          <stop offset="45%"  stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#1e3a8a" />
        </radialGradient>
        <radialGradient id="tdEyeGrad" cx="30%" cy="25%" r="70%">
          <stop offset="0%"   stopColor="#1e40af" />
          <stop offset="100%" stopColor="#0f172a" />
        </radialGradient>
      </defs>
      <path d="M 0 -90 C -28 -62 -64 -12 -64 24 C -64 62 -34 88 0 88 C 34 88 64 62 64 24 C 64 -12 28 -62 0 -90 Z"
        fill="url(#tdBodyGrad)" />
      {/* Camisa semi-formal */}
      <path d="M -38 56 L -14 48 L 0 60 L 14 48 L 38 56 L 42 88 L -42 88 Z" fill="white" opacity="0.92" />
      <path d="M -38 56 L -14 48 L 0 60" fill="white" stroke="#d1d5db" strokeWidth="0.8" />
      <path d="M 38 56 L 14 48 L 0 60"  fill="white" stroke="#d1d5db" strokeWidth="0.8" />
      <line x1="0" y1="62" x2="0" y2="84" stroke="#d1d5db" strokeWidth="0.7" />
      <circle cx="0" cy="69" r="1.8" fill="#9ca3af" />
      <circle cx="0" cy="77" r="1.8" fill="#9ca3af" />
      {/* Ojos */}
      <ellipse cx="-20" cy="10" rx="12" ry="14" fill="white" />
      <ellipse cx="20"  cy="10" rx="12" ry="14" fill="white" />
      <circle cx="-17" cy="12" r="8"   fill="url(#tdEyeGrad)" />
      <circle cx="23"  cy="12" r="8"   fill="url(#tdEyeGrad)" />
      <circle cx="-13" cy="8"  r="3.5" fill="white" opacity="0.92" />
      <circle cx="27"  cy="8"  r="3.5" fill="white" opacity="0.92" />
      <circle cx="-20" cy="16" r="1.5" fill="white" opacity="0.45" />
      <circle cx="16"  cy="16" r="1.5" fill="white" opacity="0.45" />
      {/* Cejas */}
      <path d="M -28 -3 Q -20 -9 -10 -3" stroke="#1e3a8a" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      <path d="M 10  -3 Q  20 -9  28 -3" stroke="#1e3a8a" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {/* Sonrisa */}
      <path d="M -16 36 Q 0 50 16 36" stroke="#0f172a" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* Mejillas */}
      <ellipse cx="-30" cy="30" rx="8" ry="5" fill="#fca5a5" opacity="0.30" />
      <ellipse cx="30"  cy="30" rx="8" ry="5" fill="#fca5a5" opacity="0.30" />
      <ellipse cx="-28" cy="-20" rx="10" ry="22" fill="white" opacity="0.13"
        transform="rotate(-22 -28 -20)" />
    </svg>
  )
}

// ── Página principal ──────────────────────────────────────
export default function Todio() {
  const navigate = useNavigate()
  const [hovered, setHovered] = useState(null)

  const BADGES = [
    { bg: '#E8593C', icon: '⚙️', label: 'Motor LLM Local',    sub: 'Ollama + Llama 3.2'    },
    { bg: '#1B3F7A', icon: '🔗', label: 'Orquestador RAG',    sub: 'LangChain Pipeline'     },
    { bg: '#1B6B3A', icon: '⚡', label: 'API REST Backend',   sub: 'FastAPI · Puerto 8001'  },
    { bg: '#5F5E5A', icon: '🔍', label: 'Búsqueda Semántica', sub: 'ChromaDB · Cos. sim.'   },
  ]

  const hovComp = hovered ? COMPONENTES[hovered] : null

  return (
    <div className="todio-page">

      <button className="todio-volver" onClick={() => navigate(-1)}>← Volver</button>

      <div className="todio-header">
        <h1 className="todio-title">AGENTES DE <span>TODIO</span></h1>
        <p className="todio-tagline">Arquitectura F22 · RAG Local · SII Chile</p>
      </div>

      <div className="todio-main">

        {/* ── Card personaje ─────────────────────── */}
        <div className="todio-char-card">
          <TodioCharacter />
          <div className="todio-name-block">
            <span className="todio-name">TODIO</span>
            <span className="todio-version-badge">v1.0</span>
          </div>
          <p className="todio-desc">
            Superordenador local de IA<br />para el Formulario 22 — SII Chile
          </p>
          <div className="todio-badges">
            {BADGES.map(b => (
              <div key={b.label} className="todio-badge">
                <div className="badge-pentagon" style={{ background: b.bg }}>
                  <span style={{ fontSize: '1rem', lineHeight: 1 }}>{b.icon}</span>
                </div>
                <div>
                  <div className="badge-text">{b.label}</div>
                  <div style={{ color: '#9e9c98', fontSize: '0.68rem', marginTop: 1 }}>{b.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Card engranajes ────────────────────── */}
        <div className="todio-gear-section">
          <p className="gear-hint">
            {hovComp
              ? `${hovComp.nombre} — haz click para ver detalles técnicos`
              : 'Pasa el cursor sobre un engranaje y haz click para explorar'}
          </p>

          <svg viewBox="-230 -210 460 430" className="gear-svg"
            role="img" aria-label="Arquitectura del sistema F22">

            {/* Líneas de flujo */}
            {ORDER.filter(id => id !== 'langchain').map(id => {
              const g = COMPONENTES[id].gear
              return (
                <line key={id}
                  x1="0" y1="0" x2={g.cx} y2={g.cy}
                  stroke="#dde4ed"
                  strokeWidth="1.5"
                  strokeDasharray="4 6"
                />
              )
            })}

            {ORDER.map(id => (
              <Gear
                key={id}
                comp={COMPONENTES[id]}
                hovered={hovered}
                onHover={setHovered}
                onClick={id => navigate(`/todio/${id}`)}
              />
            ))}
          </svg>

          {/* Descripción del engranaje al hacer hover */}
          <div className={`gear-desc-card ${hovComp ? 'gear-desc-card--visible' : ''}`}
            style={{ borderLeftColor: hovComp?.color || '#dde4ed' }}>
            {hovComp ? (
              <>
                <span className="gear-desc-nombre" style={{ color: hovComp.color }}>
                  {hovComp.nombre}
                  <span className="gear-desc-version">{hovComp.version}</span>
                </span>
                <p className="gear-desc-text">{hovComp.descripcion}</p>
              </>
            ) : (
              <p className="gear-desc-placeholder">
                Selecciona un engranaje para ver su descripción
              </p>
            )}
          </div>
        </div>

      </div>

      {/* ── Deploy en la Nube ──────────────────────────────── */}
      <section className="todio-cloud-section">

        <div>
          <div className="cloud-section-label">☁️ Deploy en la Nube</div>
          <h2 className="cloud-section-title">Arquitectura Netlify + Railway + Groq</h2>
          <p className="cloud-section-subtitle">
            Alternativa cloud para que el sistema funcione completamente en internet sin depender
            de una máquina local. Netlify sirve el frontend React, Railway ejecuta FastAPI con
            ChromaDB persistente, y Groq reemplaza a Ollama con el mismo modelo Llama 3.2 — gratis.
          </p>
        </div>

        {/* Diagrama de flujo */}
        <div className="cloud-flow">
          <div className="cloud-node cloud-node--user">
            <div className="cn-icon">👤</div>
            <div className="cn-label">Usuario</div>
            <div className="cn-sub">Navegador web</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#00AD9F' }}
            onClick={() => navigate('/todio/netlify')}>
            <div className="cn-icon">⚡</div>
            <div className="cn-badge" style={{ background: '#00AD9F' }}>Netlify</div>
            <div className="cn-label">Frontend React</div>
            <div className="cn-sub">CDN Global · HTTPS</div>
            <div className="cn-detail">tu-app.netlify.app</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#7C3AED' }}
            onClick={() => navigate('/todio/railway')}>
            <div className="cn-icon">🚀</div>
            <div className="cn-badge" style={{ background: '#7C3AED' }}>Railway</div>
            <div className="cn-label">FastAPI + ChromaDB</div>
            <div className="cn-sub">Python 3.11 · Volumen</div>
            <div className="cn-detail">tu-app.railway.app</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#F97316' }}
            onClick={() => navigate('/todio/groq')}>
            <div className="cn-icon">🧠</div>
            <div className="cn-badge" style={{ background: '#F97316' }}>Groq API</div>
            <div className="cn-label">Llama 3.2 · Gratis</div>
            <div className="cn-sub">~200ms · LPU Hardware</div>
            <div className="cn-detail">console.groq.com</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>
        </div>

        {/* Pasos de deploy */}
        <div className="cloud-steps">
          {[
            {
              n: '1', color: '#F97316',
              title: 'Cuenta Groq API',
              desc: 'Registrarse en console.groq.com y crear una API Key gratuita. Reemplaza a Ollama usando el mismo modelo Llama 3.2, sin GPU local ni costo de inferencia.',
            },
            {
              n: '2', color: '#7C3AED',
              title: 'Backend en Railway',
              desc: 'Conectar el repositorio GitHub a Railway. Detecta Python automáticamente. Agregar GROQ_API_KEY, CHROMA_PATH y demás variables de entorno. Crear volumen para ChromaDB.',
            },
            {
              n: '3', color: '#00AD9F',
              title: 'Frontend en Netlify',
              desc: 'Importar el repo en netlify.com. Build command: npm run build. Publish directory: dist. Agregar variable VITE_API_URL apuntando al dominio del backend Railway.',
            },
            {
              n: '4', color: '#1B6B3A',
              title: 'CORS + Ingestión',
              desc: 'Actualizar allow_origins en main.py con el dominio Netlify. Ejecutar ingestión de documentos en Railway para cargar ChromaDB en la nube. Sistema listo.',
            },
          ].map(step => (
            <div key={step.n} className="cloud-step">
              <div className="cs-num" style={{ background: step.color }}>{step.n}</div>
              <div>
                <div className="cs-title">{step.title}</div>
                <div className="cs-desc">{step.desc}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Comparativa local vs nube */}
        <div className="cloud-compare">
          <div className="compare-col">
            <div className="compare-header compare-header--local">🖥️ Arquitectura Local</div>
            {[
              ['Frontend',    'localhost:5173'],
              ['Backend',     'localhost:8001'],
              ['LLM',         'Ollama llama3.2 (2 GB local)'],
              ['Embeddings',  'nomic-embed · Ollama local'],
              ['Vector DB',   './data/chroma_db · filesystem'],
              ['Costo',       '$0 · solo electricidad'],
              ['Requisito',   'PC encendida + Ollama corriendo'],
            ].map(([k, v]) => (
              <div key={k} className="compare-row">
                <span className="compare-key">{k}</span>
                <span className="compare-val">{v}</span>
              </div>
            ))}
          </div>
          <div className="compare-col">
            <div className="compare-header compare-header--cloud">☁️ Arquitectura Nube</div>
            {[
              ['Frontend',    'tu-app.netlify.app'],
              ['Backend',     'tu-app.railway.app'],
              ['LLM',         'Groq API · Llama 3.2 (gratis)'],
              ['Embeddings',  'nomic-embed · Railway server'],
              ['Vector DB',   'ChromaDB · volumen Railway'],
              ['Costo',       '~$0–$5/mes · Railway crédito'],
              ['Requisito',   'Solo GitHub + cuentas cloud'],
            ].map(([k, v]) => (
              <div key={k} className="compare-row">
                <span className="compare-key">{k}</span>
                <span className="compare-val compare-val--cloud">{v}</span>
              </div>
            ))}
          </div>
        </div>

      </section>

    </div>
  )
}
