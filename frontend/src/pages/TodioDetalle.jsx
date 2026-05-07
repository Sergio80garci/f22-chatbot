import { useNavigate, useParams } from 'react-router-dom'
import { useMemo } from 'react'
import { COMPONENTES } from './Todio'
import '../todio.css'

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

export default function TodioDetalle() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const comp     = COMPONENTES[id]

  if (!comp) return (
    <div className="todio-detalle">
      <button className="todio-back" onClick={() => navigate('/todio')}>
        ← Volver a TODIO
      </button>
      <p style={{ color: '#64748b', marginTop: 40 }}>Componente no encontrado.</p>
    </div>
  )

  const { gear, color, accentColor } = comp

  // Escalar el engranaje para la vista de detalle
  const DETAIL_R = 90
  const scale    = DETAIL_R / gear.outerR
  const dInnerR  = gear.innerR * scale
  const dOuterR  = gear.outerR * scale
  const dHoleR   = gear.holeR  * scale
  const vb       = dOuterR + 12

  const path = useMemo(
    () => gearPath(gear.teeth, dInnerR, dOuterR),
    [gear.teeth, dInnerR, dOuterR]
  )

  return (
    <div className="todio-detalle">
      <button className="todio-back" onClick={() => navigate('/todio')}>
        ← Volver a TODIO
      </button>

      <div className="detalle-main">
        {/* Engranaje grande animado */}
        <div className="detalle-gear-col">
          <svg
            viewBox={`${-vb} ${-vb} ${vb * 2} ${vb * 2}`}
            width="240"
            height="240"
            style={{ overflow: 'visible' }}
          >
            <g
              className={gear.cw ? 'gear-spin-cw' : 'gear-spin-ccw'}
              style={{ animationDuration: `${gear.speed}s`, transformOrigin: '0px 0px' }}
            >
              <path
                d={path}
                fill={color}
                style={{
                  filter: `drop-shadow(0 4px 12px ${color}60)`,
                }}
              />
              <circle r={dHoleR}        fill="#ffffff" />
              <circle r={dHoleR * 0.6}  fill={color}   opacity="0.15" />
              <text
                textAnchor="middle"
                dominantBaseline="central"
                fill={color}
                fontSize={dHoleR * 0.65}
                fontWeight="900"
                fontStyle="italic"
                style={{ userSelect: 'none' }}
              >
                {comp.nombre.slice(0, 2).toUpperCase()}
              </text>
            </g>
          </svg>
          <div className="detalle-gear-label" style={{ color: accentColor }}>
            {gear.cw ? '↻ horario' : '↺ anti-horario'}
          </div>
        </div>

        {/* Información técnica */}
        <div className="detalle-info-col">
          <div className="detalle-version" style={{ color: accentColor }}>{comp.version}</div>
          <h2 className="detalle-nombre">{comp.nombre}</h2>
          <p className="detalle-rol" style={{ color: accentColor }}>{comp.rol}</p>
          <p className="detalle-desc">{comp.descripcion}</p>

          <table className="detalle-tabla">
            <tbody>
              {comp.detalles.map(([k, v]) => (
                <tr key={k}>
                  <td className="detalle-key">{k}</td>
                  <td className="detalle-val">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {comp.relacionados.length > 0 && (
            <div className="detalle-relacionados">
              <span className="rel-label">Relacionado con:</span>
              <div className="rel-btns">
                {comp.relacionados.map(rid => (
                  <button
                    key={rid}
                    className="rel-btn"
                    style={{
                      borderColor: COMPONENTES[rid].accentColor,
                      color:       COMPONENTES[rid].accentColor,
                    }}
                    onClick={() => navigate(`/todio/${rid}`)}
                  >
                    {COMPONENTES[rid].nombre}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
