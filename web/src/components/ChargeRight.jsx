import { useEffect, useState } from 'react'
import Icon from './Icon.jsx'
import * as api from '../api.js'
import { ForecastChart } from './Charts.jsx'

const h12 = (h) => `${((h + 11) % 12) + 1}${h < 12 ? 'am' : 'pm'}`

export default function ChargeRight({ stationId = 'ocm-1', battery = 40, onClose }) {
  const [fc, setFc] = useState(null)
  const [scheduled, setScheduled] = useState(false)
  const [evs, setEvs] = useState(20000)
  useEffect(() => { api.getForecast(stationId, 2).then(setFc).catch(() => {}) }, [stationId])

  function schedule() {
    setScheduled(true)
    if ('Notification' in window) {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') setTimeout(() => new Notification('GRIഢം — time to charge ⚡', {
          body: `The grid is at its greenest now (${fc?.recommended.carbon} gCO₂/kWh). Plug in to charge right.`,
        }), 4000)
      })
    }
  }

  // demand-response impact model
  const avgKwh = 30, peakCarbon = 820, offCarbon = 480, coincidence = 0.3, charger = 7
  const peakShavedMW = Math.round((evs * charger * coincidence) / 1000)
  const co2Tonnes = Math.round((evs * avgKwh * (peakCarbon - offCarbon)) / 1e6)
  const homes = Math.round(peakShavedMW * 1000 / 3)

  if (!fc) return <div className="page"><div className="spin" style={{ margin: '80px auto' }} /></div>
  const r = fc.recommended
  return (
    <div className="page">
      <div className="page-bar">
        <button className="icon-btn" onClick={onClose}><Icon name="back" size={16} /></button>
        <h2>Charge Right</h2>
      </div>
      <div className="page-body">
        <div className="cr-hero">
          <div className="muted small">Best time to charge in the next 24h</div>
          <div className="cr-time">{h12(r.start_hour)}<span>–{h12((r.start_hour + r.hours) % 24)}</span></div>
          <div className="cr-tags">
            <span className="chip">🌿 {Math.round(r.carbon)} gCO₂/kWh</span>
            <span className="chip">₹{r.price}/kWh</span>
          </div>
          {!scheduled
            ? <button className="btn primary full" onClick={schedule}><Icon name="bolt" size={16} /> Schedule + remind me</button>
            : <div className="cr-scheduled"><Icon name="check" size={16} /> Scheduled — we'll remind you when the grid is greenest</div>}
        </div>

        <div className="metric-row" style={{ marginTop: 14 }}>
          <div className="metric"><b className="good">{fc.greenest.hour}h</b><span>greenest hour</span></div>
          <div className="metric"><b>{fc.cheapest.hour}h</b><span>cheapest hour</span></div>
          <div className="metric"><b className="warn">18–22h</b><span>avoid (peak)</span></div>
        </div>

        <div className="panel">
          <h3>Next 24 hours</h3>
          <div className="muted small">Carbon intensity (line) · price (dashed) · green band = charge now</div>
          <ForecastChart points={fc.points} recStart={r.start_hour} recHours={r.hours} />
        </div>

        <div className="panel">
          <h3>Your charge, shifted</h3>
          <div className="muted small">If you charge in the green window vs. the evening peak</div>
          <div className="cr-savemsg">
            You'd cut <b className="good">~{Math.round((peakCarbon - r.carbon) * battery * 0.6 / 1000)} kg CO₂</b> and
            save <b className="good">₹{Math.round((11 - r.price) * battery * 0.6)}</b> on this one charge.
          </div>
        </div>

        <div className="panel gi">
          <h3>Grid impact at scale</h3>
          <div className="muted small">If Kochi EV drivers shifted to off-peak charging</div>
          <div className="gi-slider">
            <input type="range" min="1000" max="100000" step="1000" value={evs} onChange={(e) => setEvs(Number(e.target.value))} />
            <span>{(evs / 1000).toFixed(0)}k EVs</span>
          </div>
          <div className="metric-row">
            <div className="metric"><b className="good">{peakShavedMW} MW</b><span>peak shaved</span></div>
            <div className="metric"><b className="good">{co2Tonnes} t</b><span>CO₂ avoided / day</span></div>
            <div className="metric"><b>{homes.toLocaleString()}</b><span>homes' worth of peak</span></div>
          </div>
          <div className="muted small" style={{ marginTop: 8 }}>Smart charging turns EVs from a grid problem into grid support — the core of GRIഢം.</div>
        </div>
      </div>
    </div>
  )
}
