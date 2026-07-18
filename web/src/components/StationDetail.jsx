import Icon from './Icon.jsx'
import { chargeEstimate, loadColor } from '../lib/estimate.js'

export default function StationDetail({ station, mode, profile, isBest, onBack, onNavigate, onCharged, routing }) {
  const s = station
  const battery = profile?.battery_kwh || 40
  const tariff = profile?.tariff || 18
  const est = chargeEstimate(s.power_kw, battery, 20, 80, tariff)
  return (
    <div className="detail">
      <button className="back-link" onClick={onBack}><Icon name="back" size={16} /> All stations</button>
      <div className="muted" style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        {isBest && <span className="badge-best">BEST FOR {mode.toUpperCase()}</span>}
        {s.distance_km != null && <span>{s.distance_km} km away</span>}
        <span className="live"><i /> live</span>
      </div>
      <h2>{s.name}</h2>
      {s.operator && <div className="muted small">{s.operator}</div>}
      <div className="chips">
        {(s.connectors?.length ? s.connectors : ['EV charger']).map((c, i) => <span className="chip" key={i}>{c}</span>)}
        {s.power_kw > 0 && <span className="chip">{Math.round(s.power_kw)} kW</span>}
      </div>
      <div className="stat-row">
        <div className="stat live"><b style={{ color: loadColor(s.carbon_intensity_gco2_kwh) }}>{Math.round(s.carbon_intensity_gco2_kwh)}</b><span>gCO₂/kWh</span></div>
        <div className="stat live"><b className="good">{Math.round(s.renewable_share_pct)}%</b><span>renewable</span></div>
        <div className="stat live"><b style={{ color: loadColor(s.grid_load_pct) }}>{Math.round(s.grid_load_pct)}%</b><span>grid load</span></div>
      </div>
      <div className="est">
        <div className="er"><span className="muted">Charge 20→80% ({est.kwh} kWh)</span><b>~{est.minutes} min</b></div>
        <div className="er"><span className="muted">Est. cost @ ₹{tariff}/kWh</span><b>₹{est.cost}</b></div>
        <div className="er"><span className="muted">Charger power · your battery</span><b>{est.power} kW · {battery} kWh</b></div>
      </div>
      <div className="detail-actions">
        <button className="btn ghost" onClick={onCharged}><Icon name="bolt" size={16} /> I charged here</button>
        <button className="btn primary full" onClick={onNavigate} disabled={routing}>
          {routing ? <span className="spin" /> : <><Icon name="nav" size={16} /> Navigate</>}
        </button>
      </div>
    </div>
  )
}
