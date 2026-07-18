import Icon from './Icon.jsx'

export default function NavPanel({ station, route, onBack }) {
  return (
    <div className="navpanel">
      <button className="back-link" onClick={onBack}><Icon name="back" size={16} /> Back</button>
      <h2 style={{ fontSize: 18, fontWeight: 700 }}>{station.name}</h2>
      <div className="navsum">
        <div><b>{route.duration_min}</b><span>min ETA</span></div>
        <div><b>{route.distance_km}</b><span>km</span></div>
        <div><b className="good">clean route</b><span>&nbsp;</span></div>
      </div>
      <div className="section-label">Turn-by-turn</div>
      <div className="steps">
        {route.steps.map((st, i) => (
          <div key={i} className="step">
            <span className="snum">{i + 1}</span>
            <span>{st.instruction}</span>
            <span className="sdist">{st.distance_m} m</span>
          </div>
        ))}
      </div>
    </div>
  )
}
