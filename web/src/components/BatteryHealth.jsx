import Icon from './Icon.jsx'

const TIPS = [
  'Charge to 80% for daily driving — top up to 100% only before long trips.',
  'Prefer AC/slow charging; frequent DC fast-charging in heat ages the pack faster.',
  'Avoid draining below ~15% — deep discharges stress the cells.',
  'Charge in the cool, green part of the day (see Charge Right) — better for the battery and the grid.',
]

export default function BatteryHealth({ profile, stats }) {
  const battery = profile?.battery_kwh || 40
  const cycles = Math.round(300 + (stats?.kwh_charged || 0) / battery)   // assumed prior + measured
  const soh = Math.max(80, Math.round((100 - (cycles / 1500) * 20) * 10) / 10)
  const color = soh > 92 ? '#00e676' : soh > 85 ? '#ffc24b' : '#ff5a5f'
  return (
    <div className="panel">
      <h3><Icon name="battery" size={16} /> Battery health</h3>
      <div className="bh-row">
        <div className="bh-num" style={{ color }}>{soh}%</div>
        <div>
          <div className="muted small">estimated state of health</div>
          <div className="muted small">~{cycles} cycles · {battery} kWh pack</div>
        </div>
      </div>
      <div className="bh-bar"><span style={{ width: `${soh}%`, background: color }} /></div>
      <div className="section-label" style={{ marginTop: 14 }}>Smart-charging coach</div>
      <ul className="tips">{TIPS.map((t, i) => <li key={i}><Icon name="bolt" size={13} /> {t}</li>)}</ul>
    </div>
  )
}
