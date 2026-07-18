import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import * as api from '../api.js'
import { AreaChart, Bars } from '../components/Charts.jsx'

const h12 = (h) => `${((h + 11) % 12) + 1}${h < 12 ? 'am' : 'pm'}`

export default function Operator() {
  const nav = useNavigate()
  const [d, setD] = useState(null)
  const [shift, setShift] = useState(30)
  useEffect(() => { api.getOperator().then(setD).catch(() => {}) }, [])
  const dr = useMemo(() => {
    if (!d) return null
    const loads = d.hourly.map((h) => h.load)
    const peak = Math.max(...loads), off = Math.min(...loads)
    const newPeak = peak - (peak - off) * shift / 100
    const carbons = d.hourly.map((h) => h.carbon)
    const co2 = Math.round(d.network.stations * 40 * (shift / 100) * (Math.max(...carbons) - Math.min(...carbons)) / 1000)
    return { peak: Math.round(peak), newPeak: Math.round(newPeak), reduced: Math.round(peak - newPeak), co2 }
  }, [d, shift])

  if (!d) return <div className="page"><div className="spin" style={{ margin: '80px auto' }} /></div>
  const n = d.network
  return (
    <div className="page">
      <div className="page-bar">
        <button className="icon-btn" onClick={() => nav('/')}><Icon name="back" size={16} /></button>
        <div><h2>Operator console</h2><div className="muted small">Network view · demand response · Kochi</div></div>
        <button className="mini" style={{ marginLeft: 'auto' }} onClick={() => nav('/app')}>Open driver app</button>
      </div>
      <div className="page-body">
        <div className="pp-grid">
          <div className="pp-card"><span className="muted small">Stations</span><b>{n.stations}</b></div>
          <div className="pp-card"><span className="muted small">Operators</span><b>{n.operators}</b></div>
          <div className="pp-card"><span className="muted small">Avg grid load</span><b style={{ color: n.avg_load > 60 ? '#ffc24b' : '#00e676' }}>{n.avg_load}%</b></div>
          <div className="pp-card"><span className="muted small">Busy now</span><b className="warn">{n.busy}</b></div>
        </div>

        <div className="panel">
          <h3>Network load · next 24h</h3>
          <div className="muted small">Peak around {h12(n.peak_hour)} · lightest around {h12(n.offpeak_hour)}</div>
          <AreaChart points={d.hourly.map((h) => h.load)} height={140} color="#3d8bff" />
        </div>

        <div className="panel gi">
          <h3>Demand response</h3>
          <div className="muted small">Shift this share of peak-hour charging to off-peak</div>
          <div className="gi-slider">
            <input type="range" min="0" max="80" step="5" value={shift} onChange={(e) => setShift(Number(e.target.value))} />
            <span>{shift}%</span>
          </div>
          <div className="metric-row">
            <div className="metric"><b className="good">−{dr.reduced}%</b><span>peak load cut</span></div>
            <div className="metric"><b className="good">{dr.co2} kg</b><span>CO₂ saved / day</span></div>
            <div className="metric"><b>{dr.newPeak}%</b><span>new peak load</span></div>
          </div>
          <div className="muted small" style={{ marginTop: 8 }}>Nudge drivers to off-peak with cheaper tariffs — the grid relief is real revenue and lower strain.</div>
        </div>

        <div className="panel">
          <h3>By operator</h3>
          <Bars data={d.by_operator.map((o) => ({ label: o.operator, value: o.count }))} height={120} color="#00e676" />
          <div className="legend" style={{ flexWrap: 'wrap', gap: 10 }}>
            {d.by_operator.map((o) => <span key={o.operator}>{o.operator} · {o.count}</span>)}
          </div>
        </div>

        <div className="section-label">Station status</div>
        <div className="op-table">
          <div className="op-row op-head"><span>Station</span><span>Operator</span><span>Load</span><span>gCO₂</span><span>Status</span></div>
          {d.stations.map((s, i) => (
            <div className="op-row" key={i}>
              <span className="op-name">{s.name}</span>
              <span className="muted">{s.operator}</span>
              <span>{s.load}%</span>
              <span>{s.carbon}</span>
              <span className={'op-badge ' + s.status}>{s.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
