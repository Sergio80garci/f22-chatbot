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
    id: 'langchain', nombre: 'LangChain', version: '1.x', rol: 'Orquestador RAG',
    descripcion: 'Orquesta el pipeline RAG completo. Streaming SSE, prompt templates anti-injection, filtrado por relevancia y construcción del contexto con citas exactas al documento F22 de origen.',
    color: '#1B3F7A',     // Navy profundo — núcleo del sistema
    accentColor: '#1B3F7A',
    detalles: [
      ['Pipeline',   'stream_rag (SSE async)'],
      ['Retriever',  'ChromaDB top-3 + threshold 0.68'],
      ['LLM',        'Cerebras llama3.1-8b'],
      ['Prompt',     'System anti-injection + RAG'],
      ['Citas',      'Filter por nombre de archivo'],
    ],
    relacionados: ['cerebras', 'chromadb', 'fastapi', 'security'],
    gear: { teeth: 12, outerR: 65, innerR: 50, holeR: 18, speed: 28, cw: true,  cx: 0,    cy: 0   },
  },
  fastapi: {
    id: 'fastapi', nombre: 'FastAPI', version: '0.111+', rol: 'Backend API REST',
    descripcion: 'Expone el chatbot como servicio HTTP con streaming SSE, validación Pydantic, CORS controlado y manejo robusto de errores. Corre en Cloud Run (us-central1) detrás de HTTPS con auto-scaling 0-2.',
    color: '#1B6B3A',     // Verde bosque — API/backend
    accentColor: '#1B6B3A',
    detalles: [
      ['Host prod',  'Cloud Run · us-central1'],
      ['Puerto',     '8080 (prod) · 8001 (dev)'],
      ['Endpoints',  '/chat/stream · /documents · /suggested-questions'],
      ['Stream',     'Server-Sent Events (SSE)'],
      ['Memoria',    '2 GiB · 2 vCPU · timeout 300s'],
    ],
    relacionados: ['langchain', 'react', 'security'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: 115,  cy: 0   },
  },
  cerebras: {
    id: 'cerebras', nombre: 'Cerebras Cloud', version: 'llama3.1-8b', rol: 'Motor LLM',
    descripcion: 'API de inferencia ultra-rápida (~2000 tokens/seg) sobre Llama 3.1 8B. Free tier de ~1M TPM, 14k req/día. Hot-swap con Groq o Ollama vía LLM_PROVIDER env var.',
    color: '#B03A00',     // Naranja tostado — motor IA
    accentColor: '#B03A00',
    detalles: [
      ['Modelo',     'llama3.1-8b (Cerebras free tier)'],
      ['Velocidad',  '~2000 tokens/seg (LPU)'],
      ['Free tier',  '~1M TPM · 14k req/día'],
      ['Fallback',   'Groq llama-3.1-8b-instant'],
      ['Local',      'Ollama llama3.1:8b para dev'],
    ],
    relacionados: ['langchain'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: 58,   cy: -100 },
  },
  chromadb: {
    id: 'chromadb', nombre: 'ChromaDB', version: '1.5+', rol: 'Base Vectorial',
    descripcion: 'Almacena 854 chunks de 76 documentos oficiales del SII (Recuadros, líneas e instrucciones F22). Búsqueda por similitud coseno con umbral de relevancia 0.68 para descartar consultas off-topic.',
    color: '#6B1B6B',     // Púrpura oscuro — base de datos
    accentColor: '#6B1B6B',
    detalles: [
      ['Chunks',     '854 (76 documentos F22)'],
      ['Colección',  'f22_knowledge_base'],
      ['Distancia',  'Cosine similarity'],
      ['Top-K',      '3 chunks por consulta'],
      ['Umbral',     '0.68 mínimo (off-topic filter)'],
    ],
    relacionados: ['langchain', 'hfembed'],
    gear: { teeth: 8,  outerR: 45, innerR: 34, holeR: 12, speed: 23, cw: false, cx: -55,  cy: -95  },
  },
  react: {
    id: 'react', nombre: 'React + Vite', version: '18 + 5.4', rol: 'Frontend SPA',
    descripcion: 'SPA con estilo SII desplegado en GitHub Pages bajo /f22-chatbot/. Streaming SSE en tiempo real, fallback de preguntas sugeridas, navbar con título dinámico, footer con versiones.',
    color: '#006699',     // Azul acero — frontend tech
    accentColor: '#006699',
    detalles: [
      ['Host prod',  'GitHub Pages (sergio80garci.github.io/f22-chatbot)'],
      ['Build',      'Vite 5.4 · base /f22-chatbot/'],
      ['Routing',    '/ · /chat · /documentos · /todio'],
      ['Markdown',   'react-markdown (sin rehype-raw → seguro)'],
      ['SPA fallback','404.html → index.html (deep-links)'],
    ],
    relacionados: ['fastapi'],
    gear: { teeth: 9,  outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: -115, cy: 0   },
  },
  hfembed: {
    id: 'hfembed', nombre: 'HF Embeddings', version: 'nomic v1.5', rol: 'Motor Embeddings',
    descripcion: 'Sentence-transformers en-proceso con nomic-embed-text-v1.5 (768 dim). Carga al startup (~40s cold start) y queda en memoria. Sin servicio externo → sin red ni rate limit.',
    color: '#007070',     // Teal — ML/embeddings
    accentColor: '#007070',
    detalles: [
      ['Modelo',     'nomic-ai/nomic-embed-text-v1.5'],
      ['Dimensiones','768'],
      ['Prefijos',   'search_query: / search_document:'],
      ['Tamaño',     '~550 MB en memoria'],
      ['Ejecución',  'CPU in-process · 0 latencia red'],
    ],
    relacionados: ['chromadb'],
    gear: { teeth: 8,  outerR: 45, innerR: 34, holeR: 12, speed: 23, cw: false, cx: -55,  cy: 95   },
  },
  security: {
    id: 'security', nombre: 'Security Shield', version: '1.0', rol: 'Defensa Multi-Capa',
    descripcion: 'Módulo backend/rag/security.py que filtra prompt injection, jailbreaks, exfiltración y leak del system prompt. 6 categorías de input + 3 de output. Logging estructurado con hash del mensaje.',
    color: '#7A1A1A',     // Rojo bordeaux — defensa
    accentColor: '#7A1A1A',
    detalles: [
      ['Input filters', '6 (injection · roleplay · exfil · prompt_leak · encoding · syntax)'],
      ['Output filters','3 (prompt_leak · dangerous_topic · hallucinated_session)'],
      ['Normalización','Unicode NFKC + zero-width strip'],
      ['3-strikes',    'Reset de sesión tras 3 ataques'],
      ['Logging',      'SHA-256 hash · no expone contenido'],
    ],
    relacionados: ['langchain', 'fastapi'],
    gear: { teeth: 8,  outerR: 43, innerR: 32, holeR: 12, speed: 23, cw: false, cx: 54,   cy: 94   },
  },
  cloudrun: {
    id: 'cloudrun', nombre: 'Google Cloud Run', version: 'serverless', rol: 'Hosting Backend',
    descripcion: 'Contenedor serverless que ejecuta FastAPI + ChromaDB + sentence-transformers. Auto-scaling 0→2 instancias, deploy desde GitHub vía Cloud Build trigger, HTTPS automático, ~$0 con free tier en uso bajo.',
    color: '#4285F4',
    accentColor: '#4285F4',
    detalles: [
      ['Región',     'us-central1 (Iowa)'],
      ['Recursos',   '2 vCPU · 2 GiB RAM · timeout 300s'],
      ['Scaling',    'min 0 · max 2 instancias'],
      ['Deploy',     'Push a main → Cloud Build → Artifact Registry'],
      ['Free tier',  '2M req/mes · 360k GB-s/mes'],
      ['URL',        'f22-chatbot-backend-6544735158.us-central1.run.app'],
    ],
    relacionados: ['fastapi', 'chromadb', 'cerebras'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: true, cx: 0, cy: 0 },
  },
  ghpages: {
    id: 'ghpages', nombre: 'GitHub Pages', version: 'Actions deploy', rol: 'Hosting Frontend',
    descripcion: 'Hosting estático del frontend React. Workflow GitHub Actions construye con Vite y publica bajo /f22-chatbot/. SPA fallback con 404.html, CORS automático con Cloud Run y secret VITE_API_URL para el endpoint.',
    color: '#181717',
    accentColor: '#181717',
    detalles: [
      ['Plan',       'Gratis (repo público)'],
      ['Workflow',   '.github/workflows/deploy-pages.yml'],
      ['Build',      'Vite 5 · base /f22-chatbot/'],
      ['CDN',        'Fastly global'],
      ['HTTPS',      'Automático · cert managed'],
      ['URL',        'sergio80garci.github.io/f22-chatbot'],
    ],
    relacionados: ['react', 'cloudrun'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 22, cw: false, cx: 0, cy: 0 },
  },
  groq: {
    id: 'groq', nombre: 'Groq API', version: 'Fallback', rol: 'LLM Cloud (fallback)',
    descripcion: 'Provider LLM alternativo. Configurable vía LLM_PROVIDER=groq en Cloud Run. Free tier de 500k TPD con llama-3.1-8b-instant. Se usa si Cerebras está saturado o no disponible.',
    color: '#F97316',
    accentColor: '#F97316',
    detalles: [
      ['Modelo',     'llama-3.1-8b-instant'],
      ['Free tier',  '500k tokens/día (TPD)'],
      ['Velocidad',  '~250 tokens/seg'],
      ['Uso actual', 'Fallback de Cerebras'],
      ['Switch',     'LLM_PROVIDER env var'],
    ],
    relacionados: ['langchain', 'cerebras'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: true, cx: 0, cy: 0 },
  },
  ollama: {
    id: 'ollama', nombre: 'Ollama (dev)', version: 'local-only', rol: 'LLM para dev',
    descripcion: 'Provider LLM para desarrollo local. llama3.1:8b corriendo en el equipo del dev. Cero costo, cero rate limit, ideal para iteración rápida. NO se usa en producción.',
    color: '#666666',
    accentColor: '#666666',
    detalles: [
      ['Modelo',     'llama3.1:8b (local)'],
      ['Puerto',     '11434'],
      ['Costo',      '$0 (solo electricidad)'],
      ['Privacidad', 'Datos nunca salen del equipo'],
      ['Velocidad',  '~50 tokens/seg (CPU)'],
    ],
    relacionados: ['langchain'],
    gear: { teeth: 9, outerR: 50, innerR: 38, holeR: 14, speed: 19, cw: false, cx: 0, cy: 0 },
  },
}

export const ORDER = ['langchain','fastapi','cerebras','chromadb','react','hfembed','security']

const ABBR = {
  langchain:'LC', fastapi:'FA', cerebras:'CB', chromadb:'CH', react:'RX',
  hfembed:'HF', security:'SC', cloudrun:'CR', ghpages:'GH', groq:'GQ', ollama:'OL',
}

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
    { bg: '#B03A00', icon: '⚡', label: 'Motor LLM Cloud',    sub: 'Cerebras · llama3.1-8b'    },
    { bg: '#1B3F7A', icon: '🔗', label: 'Orquestador RAG',    sub: 'LangChain Pipeline'       },
    { bg: '#4285F4', icon: '☁️', label: 'Hosting Backend',    sub: 'Google Cloud Run'          },
    { bg: '#6B1B6B', icon: '🔍', label: 'Base Vectorial',     sub: 'ChromaDB · 854 chunks'    },
    { bg: '#7A1A1A', icon: '🛡️', label: 'Security Shield',    sub: '6 filtros input · 3 output'},
    { bg: '#181717', icon: '📦', label: 'Hosting Frontend',   sub: 'GitHub Pages · Actions'    },
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

      {/* ── Deploy en la Nube (stack actual) ────────────────── */}
      <section className="todio-cloud-section">

        <div>
          <div className="cloud-section-label">☁️ Deploy en producción</div>
          <h2 className="cloud-section-title">GitHub Pages + Cloud Run + Cerebras</h2>
          <p className="cloud-section-subtitle">
            Stack actual en vivo. GitHub Pages sirve el frontend React bajo /f22-chatbot/.
            Google Cloud Run ejecuta FastAPI + ChromaDB + sentence-transformers en un
            contenedor con 2 vCPU / 2 GiB. Cerebras Cloud entrega inferencia LLM a
            ~2000 tokens/seg con free tier de 1M TPM.
          </p>
        </div>

        {/* Diagrama de flujo */}
        <div className="cloud-flow">
          <div className="cloud-node cloud-node--user">
            <div className="cn-icon">👤</div>
            <div className="cn-label">Usuario</div>
            <div className="cn-sub">Navegador</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#181717' }}
            onClick={() => navigate('/todio/ghpages')}>
            <div className="cn-icon">📦</div>
            <div className="cn-badge" style={{ background: '#181717' }}>GitHub Pages</div>
            <div className="cn-label">Frontend React</div>
            <div className="cn-sub">Vite build · CDN Fastly</div>
            <div className="cn-detail">sergio80garci.github.io/f22-chatbot</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#4285F4' }}
            onClick={() => navigate('/todio/cloudrun')}>
            <div className="cn-icon">☁️</div>
            <div className="cn-badge" style={{ background: '#4285F4' }}>Cloud Run</div>
            <div className="cn-label">FastAPI + ChromaDB + HF</div>
            <div className="cn-sub">us-central1 · 2 vCPU · 2 GiB</div>
            <div className="cn-detail">f22-chatbot-backend-...run.app</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>

          <div className="cloud-arrow">→</div>

          <div className="cloud-node cloud-node--service" style={{ borderTopColor: '#B03A00' }}
            onClick={() => navigate('/todio/cerebras')}>
            <div className="cn-icon">🧠</div>
            <div className="cn-badge" style={{ background: '#B03A00' }}>Cerebras</div>
            <div className="cn-label">llama3.1-8b · 2000 tok/s</div>
            <div className="cn-sub">Free tier ~1M TPM</div>
            <div className="cn-detail">cloud.cerebras.ai</div>
            <div className="cn-hint">Ver detalles →</div>
          </div>
        </div>

        {/* Pasos de deploy */}
        <div className="cloud-steps">
          {[
            {
              n: '1', color: '#B03A00',
              title: 'Cerebras API Key',
              desc: 'Registro gratis en cloud.cerebras.ai con Google. Generar API Key (csk-...). Modelo llama3.1-8b disponible en free tier con ~1M TPM y 14k requests/día.',
            },
            {
              n: '2', color: '#4285F4',
              title: 'Backend en Cloud Run',
              desc: 'Habilitar APIs: Cloud Run + Cloud Build + Artifact Registry. Crear servicio desde GitHub repo. Cloud Build construye desde Dockerfile, deploy automático en cada push a main. Env vars: CEREBRAS_API_KEY, EMBEDDING_PROVIDER=hf, ALLOWED_ORIGINS, etc.',
            },
            {
              n: '3', color: '#181717',
              title: 'Frontend en GitHub Pages',
              desc: 'Settings → Pages → Source: GitHub Actions. Workflow .github/workflows/deploy-pages.yml construye Vite y publica bajo /f22-chatbot/. Secret VITE_API_URL apunta al backend Cloud Run.',
            },
            {
              n: '4', color: '#7A1A1A',
              title: 'CORS + Security Shield',
              desc: 'ALLOWED_ORIGINS incluye https://sergio80garci.github.io. Backend integra security.py con 6 filtros de input contra prompt injection, jailbreaks y exfiltración. Sistema listo en producción.',
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
            <div className="compare-header compare-header--local">🖥️ Entorno de desarrollo</div>
            {[
              ['Frontend',    'localhost:5173 (Vite HMR)'],
              ['Backend',     'localhost:8001 (uvicorn --reload)'],
              ['LLM',         'Ollama llama3.1:8b (local)'],
              ['Embeddings',  'sentence-transformers HF (in-process)'],
              ['Vector DB',   './data/chroma_db (854 chunks)'],
              ['Hot reload',  'Sí · Vite + uvicorn reload'],
              ['Costo',       '$0 (solo electricidad)'],
            ].map(([k, v]) => (
              <div key={k} className="compare-row">
                <span className="compare-key">{k}</span>
                <span className="compare-val">{v}</span>
              </div>
            ))}
          </div>
          <div className="compare-col">
            <div className="compare-header compare-header--cloud">☁️ Producción</div>
            {[
              ['Frontend',    'sergio80garci.github.io/f22-chatbot'],
              ['Backend',     'f22-chatbot-backend-...run.app'],
              ['LLM',         'Cerebras llama3.1-8b (free tier)'],
              ['Embeddings',  'sentence-transformers HF (in-image)'],
              ['Vector DB',   'ChromaDB en imagen Docker (854 chunks)'],
              ['Cold start',  '~40s (carga modelo HF en memoria)'],
              ['Costo',       '~$0/mes (free tier en uso bajo)'],
            ].map(([k, v]) => (
              <div key={k} className="compare-row">
                <span className="compare-key">{k}</span>
                <span className="compare-val compare-val--cloud">{v}</span>
              </div>
            ))}
          </div>
        </div>

      </section>

      {/* ── Skills de Claude Code ────────────────────────────── */}
      <section className="todio-skills-section">
        <div>
          <div className="cloud-section-label">🤖 Skills de Claude Code</div>
          <h2 className="cloud-section-title">8 comandos para mantener el proyecto</h2>
          <p className="cloud-section-subtitle">
            Skills personalizados que viven en <code>.claude/commands/</code>. Cada uno
            ejecuta un workflow completo (ingestión, build, deploy, auditoría). Se invocan
            tipeando <code>/nombre</code> en el chat de Claude Code dentro del proyecto.
          </p>
        </div>

        <div className="skills-grid">
          {[
            { id: 'ingest', icon: '📥', cat: 'Construcción', catColor: '#1B6B3A',
              title: '/ingest',
              subtitle: 'Procesamiento de documentos F22',
              desc: 'Lee PDFs, DOCX, XLSX e imágenes desde data/f22/raw, aplica OCR (Tesseract+spa), chunking semántico y embedea con HF nomic-embed-text-v1.5. Resulta en 854 chunks listos para RAG.' },
            { id: 'build-backend', icon: '⚙️', cat: 'Construcción', catColor: '#1B6B3A',
              title: '/build-backend',
              subtitle: 'FastAPI + RAG Pipeline',
              desc: 'Construye el backend completo: routers, modelos Pydantic, pipeline RAG con stream_rag, retriever con umbral 0.68, integración LLM multi-provider y health checks.' },
            { id: 'build-frontend', icon: '🎨', cat: 'Construcción', catColor: '#1B6B3A',
              title: '/build-frontend',
              subtitle: 'Sitio web + chatbot React',
              desc: 'Genera la SPA con estilo SII: chat con SSE streaming, página de documentos con resúmenes, footer con versiones, navbar dinámico, logo oficial SII.' },
            { id: 'deploy', icon: '🚀', cat: 'Operación', catColor: '#4285F4',
              title: '/deploy',
              subtitle: 'Despliegue completo del sistema',
              desc: 'Levanta backend + frontend (Docker Compose en local, Cloud Run + GitHub Pages en prod). Verifica health checks y CORS. Útil para arranque rápido.' },
            { id: 'security-audit', icon: '🔍', cat: 'Seguridad', catColor: '#7A1A1A',
              title: '/security-audit',
              subtitle: 'Checklist genérico de seguridad',
              desc: 'Auditoría en 7 áreas: env vars, validación de input, info sensible, CORS/headers, datos, dependencias, autenticación. Devuelve checklist con [ ] / [x].' },
            { id: 'security-shield', icon: '🛡️', cat: 'Seguridad', catColor: '#7A1A1A',
              title: '/security-shield',
              subtitle: 'Read-only security sweep',
              desc: 'Auditoría profunda en 3 fases: detección de secretos (12 proveedores), vulnerabilidades del backend (CORS, path traversal, rate limit) y log hygiene. Sugiere diffs.' },
            { id: 'responsive-design', icon: '📱', cat: 'UX/UI', catColor: '#006699',
              title: '/responsive-design',
              subtitle: 'Mobile-first responsive',
              desc: 'Guía para hacer cualquier componente React responsive: breakpoints, clamp(), grid auto-fit, hamburger menu. Mobile-first sin frameworks pesados.' },
            { id: 'chat-ui-centrado', icon: '💬', cat: 'UX/UI', catColor: '#006699',
              title: '/chat-ui-centrado',
              subtitle: 'Chat centrado + skeleton + preguntas',
              desc: 'Corrige UX del chat en pantallas grandes: contenedor centrado, skeleton loader, preguntas sugeridas aleatorias rotativas desde questions_pool.json.' },
          ].map(skill => (
            <div key={skill.id} className="skill-card" style={{ borderLeftColor: skill.catColor }}>
              <div className="skill-header">
                <div className="skill-icon" style={{ background: skill.catColor }}>
                  {skill.icon}
                </div>
                <div className="skill-cat" style={{ color: skill.catColor }}>{skill.cat}</div>
              </div>
              <div className="skill-title">{skill.title}</div>
              <div className="skill-subtitle">{skill.subtitle}</div>
              <p className="skill-desc">{skill.desc}</p>
            </div>
          ))}
        </div>

        <div className="skills-stats">
          <div className="skills-stat">
            <div className="stat-num" style={{ color: '#1B6B3A' }}>3</div>
            <div className="stat-label">Construcción</div>
          </div>
          <div className="skills-stat">
            <div className="stat-num" style={{ color: '#4285F4' }}>1</div>
            <div className="stat-label">Operación</div>
          </div>
          <div className="skills-stat">
            <div className="stat-num" style={{ color: '#7A1A1A' }}>2</div>
            <div className="stat-label">Seguridad</div>
          </div>
          <div className="skills-stat">
            <div className="stat-num" style={{ color: '#006699' }}>2</div>
            <div className="stat-label">UX / UI</div>
          </div>
        </div>
      </section>

    </div>
  )
}
