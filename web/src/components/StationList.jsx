import { loadColor } from '../lib/estimate.js'
export default function StationList({ stations, bestId, selectedId, onSelect }) {
  if (!stations.length) return <p className="muted small">No stations in range. Try a wider radius.</p>
  return (
    <div className="station-list">
      {stations.map((s) => (
        <div key={s.station_id}
          className={'station-item' + (s.station_id === selectedId ? ' sel' : '')}
          onClick={() => onSelect(s)}>
          <div className="si-top">
            <h4>{s.name}</h4>
            {s.station_id === bestId && <span className="badge-best">BEST</span>}
          </div>
          <div className="si-meta">
            {s.distance_km != null && <span>{s.distance_km} km</span>}
            <span style={{ color: loadColor(s.grid_load_pct) }}>● {Math.round(s.carbon_intensity_gco2_kwh)} gCO₂</span>
            <span>{Math.round(s.renewable_share_pct)}% renew</span>
            {s.power_kw > 0 && <span>{Math.round(s.power_kw)} kW</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
