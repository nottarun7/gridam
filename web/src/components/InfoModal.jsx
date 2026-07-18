import Icon from './Icon.jsx'

const ROWS = [
  ['Grid load %', 'How busy the local grid feeder is right now. Lower = your charge is less likely to strain the grid. Peaks in the morning (~9am) and evening (~8pm). (Modelled — not published per-station.)'],
  ['Carbon intensity', 'Grams of CO₂ per kWh of electricity right now — LIVE from Electricity Maps for the Southern-India grid (zone IN-SO). Lower when the grid runs on hydro/solar, higher when it leans on coal.'],
  ['Renewable %', 'Share of the current electricity mix from renewables — also live from Electricity Maps.'],
  ['Recommendation score', 'Each station is ranked by a weighted blend of proximity, low grid load, low carbon, and availability. Fastest / Balanced / Greenest just changes the weights.'],
  ['CO₂ per charge', 'kWh you charge × the grid carbon intensity at that moment.'],
  ['CO₂ / money saved', 'Compared to driving the same distance in an equivalent petrol car (your vehicle settings drive this).'],
]

export default function InfoModal({ onClose }) {
  return (
    <div className="modal-wrap" onClick={(e) => { if (e.target.className === 'modal-wrap') onClose() }}>
      <div className="modal" style={{ maxWidth: 460 }}>
        <div className="modal-head">
          <h3>How the metrics work</h3>
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={16} /></button>
        </div>
        <div className="info-list">
          {ROWS.map(([k, v]) => (
            <div className="info-row" key={k}><b>{k}</b><p className="muted small">{v}</p></div>
          ))}
        </div>
        <div className="info-note">
          <b className="good">Where does the grid data come from?</b>
          <p className="muted small">
            <b>Carbon intensity and renewable share are live</b> from <b>Electricity Maps</b> (Southern-India
            zone, IN-SO) — so they vary hour-to-hour and day-to-day with real grid conditions. If the feed is
            unavailable, GRIഢം falls back to a synthetic model <b>calibrated to real Kerala figures</b> (~5,600 MW
            peak, 90% hydro / 10% solar own generation, ~70% coal imports, Southern-grid CEA factor
            ~809 gCO₂/kWh). Grid load % and time-of-use price are still modelled, since they aren't published
            per-station in India yet.
          </p>
        </div>
      </div>
    </div>
  )
}
