import Icon from './Icon.jsx'
export default function SearchBar({ value, onChange, results, onPick }) {
  return (
    <div className="searchbar">
      <span className="s-ico"><Icon name="search" /></span>
      <input value={value} onChange={(e) => onChange(e.target.value)}
        placeholder="Search a place in Kerala…" />
      {results.length > 0 && (
        <div className="search-results">
          {results.map((r, i) => (
            <button key={i} onClick={() => onPick(r)}>
              {r.name}<small>{r.full_name}</small>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
