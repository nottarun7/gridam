import Icon from './Icon.jsx'

export default function ProfilePanel({ data }) {
  if (!data) return <div className="spin" style={{ margin: '40px auto' }} />
  const t = data.totals || {}, x = data.extended || {}
  return (
    <div className="profile">
      <div className="profile-head">
        <div className="avatar">EV</div>
        <div>
          <h2>EV Driver</h2>
          <div className="muted small">Tata Nexon EV · 40 kWh</div>
          <div className="muted small">Member since 2026 · Kochi</div>
        </div>
      </div>

      <div className="hero-card" style={{ marginTop: 16 }}>
        <div className="hero-top"><span className="hero-ico"><Icon name="bolt" /></span> Money saved vs. petrol</div>
        <div className="hero-num">₹{x.money_saved_inr ?? 0}</div>
        <div className="muted">{t.co2_saved_vs_petrol_kg ?? 0} kg CO₂ avoided · {data.equivalents?.trees_planted ?? 0} trees 🌱</div>
      </div>

      <div className="section-label">Lifetime stats</div>
      <div className="stat-grid">
        <div className="gs"><b>{t.sessions ?? 0}</b><span>charges</span></div>
        <div className="gs"><b>{Math.round(t.kwh_charged ?? 0)}</b><span>kWh charged</span></div>
        <div className="gs"><b>{x.days_active ?? 0}</b><span>days active</span></div>
        <div className="gs"><b className="good">{Math.round(t.clean_charging_pct ?? 0)}%</b><span>clean charging</span></div>
        <div className="gs"><b>{x.avg_kwh_per_charge ?? 0}</b><span>kWh / charge</span></div>
        <div className="gs"><b className="warn">{x.avg_co2_per_charge_kg ?? 0}</b><span>kg CO₂ / charge</span></div>
        <div className="gs"><b className="good">{x.cleanest_charge_gco2 ?? 0}</b><span>cleanest (gCO₂)</span></div>
        <div className="gs wide"><b style={{ fontSize: 15 }}>{x.most_used_station ?? '—'}</b><span>most-used station</span></div>
      </div>
    </div>
  )
}
