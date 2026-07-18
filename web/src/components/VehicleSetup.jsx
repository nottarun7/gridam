import { useEffect, useState } from 'react'
import Icon from './Icon.jsx'
import * as api from '../api.js'

const FIELDS = [
  ['vehicle', 'Vehicle', 'text'],
  ['battery_kwh', 'Battery size (kWh)', 'number'],
  ['efficiency_km_kwh', 'Efficiency (km per kWh)', 'number'],
  ['mileage_kmpl', 'Equivalent petrol car (km/L)', 'number'],
  ['petrol_price', 'Petrol price (₹/L)', 'number'],
  ['tariff', 'Charging tariff (₹/kWh)', 'number'],
]

export default function VehicleSetup({ profile, onSaved, onClose }) {
  const [form, setForm] = useState(profile || {})
  useEffect(() => { if (profile) setForm(profile) }, [profile])
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  async function save() {
    const payload = { ...form }
    for (const [k, , t] of FIELDS) if (t === 'number') payload[k] = parseFloat(payload[k]) || 0
    payload.name = form.name || 'EV Driver'
    const res = await api.saveProfile(payload)
    onSaved?.(res.profile)
  }

  return (
    <div className="page">
      <div className="page-bar">
        <button className="icon-btn" onClick={onClose}><Icon name="back" size={16} /></button>
        <h2>Vehicle & settings</h2>
      </div>
      <div className="page-body">
        <p className="muted small">These drive your charge-time, cost, and savings estimates.</p>
        <label className="fld">Your name<input value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></label>
        {FIELDS.map(([k, label, type]) => (
          <label className="fld" key={k}>{label}
            <input type={type} step="any" value={form[k] ?? ''} onChange={(e) => set(k, e.target.value)} />
          </label>
        ))}
        <label className="fld">Preferred connector
          <select value={form.connector_pref || 'CCS2'} onChange={(e) => set('connector_pref', e.target.value)}>
            {['CCS2', 'Type 2', 'CHAdeMO', 'Bharat AC-001', 'Bharat DC-001'].map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <button className="btn primary full" style={{ marginTop: 18 }} onClick={save}><Icon name="bolt" size={16} /> Save settings</button>
      </div>
    </div>
  )
}
