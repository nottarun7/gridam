const MODES = ['fastest', 'balanced', 'greenest']
export default function ModeToggle({ value, onChange }) {
  return (
    <div className="mode-toggle">
      {MODES.map((m) => (
        <button key={m} className={value === m ? 'active' : ''} onClick={() => onChange(m)}>
          {m[0].toUpperCase() + m.slice(1)}
        </button>
      ))}
    </div>
  )
}
