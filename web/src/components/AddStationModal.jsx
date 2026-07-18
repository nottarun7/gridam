import { useState, useEffect } from 'react'
import Icon from './Icon.jsx'

export default function AddStationModal({ prefill, onClose, onSubmit, onPickOnMap }) {
  const [name, setName] = useState('')
  const [connector, setConnector] = useState('CCS2')
  const [lat, setLat] = useState('')
  const [lng, setLng] = useState('')
  useEffect(() => {
    if (prefill) { setLat(prefill.lat.toFixed(5)); setLng(prefill.lng.toFixed(5)) }
  }, [prefill])

  const submit = () => {
    const la = parseFloat(lat), ln = parseFloat(lng)
    if (!name.trim() || isNaN(la) || isNaN(ln)) return
    onSubmit({ name: name.trim(), lat: la, lng: ln, connector })
  }
  return (
    <div className="modal-wrap" onClick={(e) => { if (e.target.className === 'modal-wrap') onClose() }}>
      <div className="modal">
        <div className="modal-head">
          <h3>Add a charging station</h3>
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={16} /></button>
        </div>
        <p className="muted small">Fill the details, or drop a pin on the map.</p>
        <label>Name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Marine Drive Charger" /></label>
        <label>Connector
          <select value={connector} onChange={(e) => setConnector(e.target.value)}>
            {['CCS2', 'Type 2', 'CHAdeMO', 'Bharat AC-001', 'Bharat DC-001'].map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <div className="coord-row">
          <label>Lat<input value={lat} onChange={(e) => setLat(e.target.value)} inputMode="decimal" /></label>
          <label>Lng<input value={lng} onChange={(e) => setLng(e.target.value)} inputMode="decimal" /></label>
        </div>
        <button className="btn ghost full" style={{ marginTop: 12 }} onClick={onPickOnMap}>
          <Icon name="pin" size={16} /> Pick on map
        </button>
        <button className="btn primary full" style={{ marginTop: 10 }} onClick={submit}>
          <Icon name="plus" size={16} /> Register station
        </button>
      </div>
    </div>
  )
}
