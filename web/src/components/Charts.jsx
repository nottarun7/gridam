// Minimal dependency-free SVG charts, neon-themed.

export function AreaChart({ points, height = 120, color = '#00e676' }) {
  const w = 300, h = height, pad = 6
  const ys = points.length ? points : [0]
  const max = Math.max(1, ...ys), min = Math.min(0, ...ys)
  const nx = (i) => pad + (i / Math.max(1, ys.length - 1)) * (w - pad * 2)
  const ny = (v) => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2)
  const line = ys.map((v, i) => `${i ? 'L' : 'M'}${nx(i).toFixed(1)} ${ny(v).toFixed(1)}`).join(' ')
  const area = `${line} L${nx(ys.length - 1)} ${h - pad} L${nx(0)} ${h - pad} Z`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h} preserveAspectRatio="none">
      <defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={color} stopOpacity="0.35" /><stop offset="1" stopColor={color} stopOpacity="0" />
      </linearGradient></defs>
      <path d={area} fill="url(#ag)" />
      <path d={line} fill="none" stroke={color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

export function Bars({ data, height = 120, color = '#00e676' }) {
  const w = 300, h = height, pad = 6
  const max = Math.max(1, ...data.map((d) => d.value))
  const bw = (w - pad * 2) / data.length
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h}>
      {data.map((d, i) => {
        const bh = (d.value / max) * (h - pad * 2 - 14)
        return <rect key={i} x={pad + i * bw + bw * 0.18} y={h - pad - bh - 12}
          width={bw * 0.64} height={Math.max(2, bh)} rx="3" fill={color} opacity={0.55 + 0.45 * (d.value / max)} />
      })}
    </svg>
  )
}

export function Donut({ segments, size = 150 }) {
  const total = segments.reduce((a, s) => a + s.value, 0) || 1
  const r = size / 2 - 12, cx = size / 2, cy = size / 2, C = 2 * Math.PI * r
  let acc = 0
  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#213029" strokeWidth="14" />
      {segments.map((s, i) => {
        const frac = s.value / total, dash = `${(frac * C).toFixed(1)} ${C.toFixed(1)}`
        const off = -acc * C; acc += frac
        return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth="14"
          strokeDasharray={dash} strokeDashoffset={off} transform={`rotate(-90 ${cx} ${cy})`} strokeLinecap="butt" />
      })}
      <text x={cx} y={cy - 2} textAnchor="middle" fill="#f1fbf6" fontSize="20" fontWeight="700">{Math.round(total)}</text>
      <text x={cx} y={cy + 16} textAnchor="middle" fill="#8fa39a" fontSize="10">kWh total</text>
    </svg>
  )
}

// 24h forecast: carbon area + price line + highlighted recommended window.
export function ForecastChart({ points, recStart, recHours = 2, height = 170 }) {
  const w = 320, h = height, pad = 8, axis = 16
  const carbons = points.map((p) => p.carbon)
  const prices = points.map((p) => p.price)
  const cmax = Math.max(...carbons), cmin = Math.min(...carbons)
  const pmax = Math.max(...prices), pmin = Math.min(...prices)
  const n = points.length
  const nx = (i) => pad + (i / (n - 1)) * (w - pad * 2)
  const cy = (v) => (h - axis) - pad - ((v - cmin) / (cmax - cmin || 1)) * (h - axis - pad * 2)
  const py = (v) => (h - axis) - pad - ((v - pmin) / (pmax - pmin || 1)) * (h - axis - pad * 2)
  const cline = points.map((p, i) => `${i ? 'L' : 'M'}${nx(i).toFixed(1)} ${cy(p.carbon).toFixed(1)}`).join(' ')
  const carea = `${cline} L${nx(n - 1)} ${h - axis} L${nx(0)} ${h - axis} Z`
  const pline = points.map((p, i) => `${i ? 'L' : 'M'}${nx(i).toFixed(1)} ${py(p.price).toFixed(1)}`).join(' ')
  const recI = points.findIndex((p) => p.hour === recStart)
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height={h}>
      <defs><linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#ff5a5f" stopOpacity="0.28" /><stop offset="1" stopColor="#00e676" stopOpacity="0.05" />
      </linearGradient></defs>
      {recI >= 0 && (
        <rect x={nx(recI)} y={pad} width={Math.max(6, nx(Math.min(n - 1, recI + recHours)) - nx(recI))}
          height={h - axis - pad} fill="#00e676" opacity="0.14" rx="4" />
      )}
      <path d={carea} fill="url(#fg)" />
      <path d={cline} fill="none" stroke="#ff9e6b" strokeWidth="2" />
      <path d={pline} fill="none" stroke="#3d8bff" strokeWidth="1.6" strokeDasharray="3 3" opacity="0.8" />
      {points.map((p, i) => i % 4 === 0 && (
        <text key={i} x={nx(i)} y={h - 4} fill="#5c6b63" fontSize="9" textAnchor="middle">{p.hour}h</text>
      ))}
    </svg>
  )
}
