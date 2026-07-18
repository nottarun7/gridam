export default function Filters({ filters, connectors, onChange }) {
  return (
    <div className="filters">
      <div className="field">
        <label>Connector</label>
        <select value={filters.connector} onChange={(e) => onChange({ connector: e.target.value })}>
          <option value="all">All connectors</option>
          {connectors.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div className="field">
        <label>Search radius: {filters.radius} km</label>
        <div className="rowline">
          <input type="range" min="2" max="30" step="1" value={filters.radius} onChange={(e) => onChange({ radius: Number(e.target.value) })} />
        </div>
      </div>
    </div>
  )
}
