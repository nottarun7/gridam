import { useEffect, useState } from 'react'
import Icon from './Icon.jsx'
import * as api from '../api.js'
import { AreaChart, Bars, Donut } from './Charts.jsx'
import BatteryHealth from './BatteryHealth.jsx'

export default function ProfilePage({ onClose, onEditVehicle, refreshKey }) {
  const [data, setData] = useState(null)
  useEffect(() => { api.getProfile().then(setData).catch(() => {}) }, [refreshKey])
  if (!data) return <div className="page"><div className="spin" style={{ margin: '80px auto' }} /></div>

  const p = data.profile, s = data.stats, ser = data.series
  const cum = ser.cumulative_saved.map((x) => x.kg)
  const daily = ser.daily.map((d) => ({ label: d.date, value: d.kwh }))
  const mix = [
    { label: 'Clean', value: ser.energy_mix.clean, color: '#00e676' },
    { label: 'Mixed', value: ser.energy_mix.mixed, color: '#ffc24b' },
    { label: 'Dirty', value: ser.energy_mix.dirty, color: '#ff5a5f' },
  ]

  return (
    <div className="page">
      <div className="page-bar">
        <button className="icon-btn" onClick={onClose}><Icon name="back" size={16} /></button>
        <h2>Profile</h2>
        <button className="mini" style={{ marginLeft: 'auto' }} onClick={onEditVehicle}><Icon name="bolt" size={14} /> Edit vehicle</button>
      </div>
      <div className="page-body">
        <div className="profile-head">
          <div className="avatar">{(p.name || 'EV').slice(0, 2).toUpperCase()}</div>
          <div>
            <h2 style={{ fontSize: 22 }}>{p.name}</h2>
            <div className="muted small">{p.vehicle} · {p.battery_kwh} kWh · {p.efficiency_km_kwh} km/kWh</div>
            <div className="muted small">Kochi · member since 2026</div>
          </div>
        </div>

        <div className="pp-grid">
          <div className="pp-card big"><span className="muted small">Distance driven electric</span><b>{s.km_driven.toLocaleString()} km</b></div>
          <div className="pp-card"><span className="muted small">Petrol cost avoided</span><b>₹{s.petrol_cost_avoided_inr.toLocaleString()}</b></div>
          <div className="pp-card"><span className="muted small">Net money saved</span><b className="good">₹{s.money_saved_inr.toLocaleString()}</b></div>
        </div>

        <div className="panel">
          <h3>CO₂ saved over time</h3>
          <div className="muted small">Cumulative kg vs. an equivalent petrol car</div>
          <AreaChart points={cum} height={130} />
          <div className="pp-foot"><span className="muted small">Total</span><b className="good">{s.co2_saved_kg} kg saved</b></div>
        </div>

        <div className="two-col">
          <div className="panel">
            <h3>Energy mix</h3>
            <div className="donut-wrap"><Donut segments={mix} /></div>
            <div className="legend">
              <span><i style={{ background: '#00e676' }} />Clean</span>
              <span><i style={{ background: '#ffc24b' }} />Mixed</span>
              <span><i style={{ background: '#ff5a5f' }} />Dirty</span>
            </div>
          </div>
          <div className="panel">
            <h3>kWh per charge</h3>
            <Bars data={daily} height={150} />
            <div className="pp-foot"><span className="muted small">{s.sessions} charges</span><b>{s.kwh_charged} kWh</b></div>
          </div>
        </div>

        <BatteryHealth profile={p} stats={s} />

        <div className="section-label">Lifetime</div>
        <div className="stat-grid">
          <div className="gs"><b>{s.sessions}</b><span>charges</span></div>
          <div className="gs"><b>{s.days_active}</b><span>days active</span></div>
          <div className="gs"><b className="good">{s.clean_charging_pct}%</b><span>clean charging</span></div>
          <div className="gs"><b>{s.trees_planted}</b><span>trees planted 🌱</span></div>
          <div className="gs"><b className="warn">{s.avg_co2_per_charge_kg}</b><span>kg CO₂ / charge</span></div>
          <div className="gs"><b className="good">{s.cleanest_charge_gco2}</b><span>cleanest (gCO₂)</span></div>
          <div className="gs wide"><b style={{ fontSize: 15 }}>{s.most_used_station}</b><span>most-used station</span></div>
        </div>
      </div>
    </div>
  )
}
