import Icon from './Icon.jsx'

function buildWeek(series) {
  const by = {}
  series.forEach((s) => {
    const label = new Date(s.date).toLocaleDateString('en', { weekday: 'short' })
    if (!by[label]) by[label] = { kwh: 0, clean: true }
    by[label].kwh += s.kwh
    if (s.co2_kg / Math.max(s.kwh, 0.1) > 0.6) by[label].clean = false
  })
  return Object.entries(by).map(([label, v]) => ({ label, kwh: v.kwh, clean: v.clean }))
}

export default function ImpactPanel({ data }) {
  if (!data) return <div className="spin" style={{ margin: '40px auto' }} />
  const t = data.totals || {}, x = data.extended || {}
  const week = buildWeek(data.series || [])
  const max = Math.max(1, ...week.map((d) => d.kwh))
  return (
    <div className="impact">
      <div className="impact-head"><h1>Carbon footprint</h1></div>
      <div className="hero-card">
        <div className="hero-top"><span className="hero-ico"><Icon name="bolt" /></span> CO₂ saved vs. petrol</div>
        <div className="hero-num">{t.co2_saved_vs_petrol_kg ?? 0}<small>kg</small></div>
        <div className="muted">≈ {data.equivalents?.trees_planted ?? 0} trees planted 🌱</div>
      </div>
      <div className="metric-row">
        <div className="metric"><b>{Math.round(t.kwh_charged ?? 0)}</b><span>kWh charged</span></div>
        <div className="metric"><b className="warn">{Math.round(t.co2_emitted_kg ?? 0)}</b><span>kg CO₂ emitted</span></div>
        <div className="metric"><b className="good">{Math.round(t.clean_charging_pct ?? 0)}%</b><span>clean charging</span></div>
      </div>
      <div className="panel">
        <h3>This week</h3>
        <div className="muted small">Green bars = clean-energy charges</div>
        <div className="bar-chart">
          {week.map((d, i) => (
            <div className="bar-col" key={i}>
              <div className="bar-track">
                <div className="bar" style={{ height: `${(d.kwh / max) * 100}%`, background: d.clean ? 'linear-gradient(180deg,#5bffb0,#00e676)' : 'linear-gradient(180deg,#ffc24b,#ff5a5f)' }} />
              </div>
              <span>{d.label}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="section-label">More stats</div>
      <div className="stat-grid">
        <div className="gs"><b>₹{x.money_saved_inr ?? 0}</b><span>money saved</span></div>
        <div className="gs"><b>{t.sessions ?? 0}</b><span>total charges</span></div>
        <div className="gs"><b className="warn">{x.avg_co2_per_charge_kg ?? 0}</b><span>kg CO₂ / charge</span></div>
        <div className="gs"><b className="good">{x.cleanest_charge_gco2 ?? 0}</b><span>cleanest (gCO₂)</span></div>
      </div>
      <div className="nudge"><Icon name="bolt" /><span>Charging around midday cuts your carbon by ~30% — the grid runs on more solar.</span></div>
    </div>
  )
}
