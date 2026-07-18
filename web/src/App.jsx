import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import * as api from './api.js'
import Icon from './components/Icon.jsx'
import MapView from './components/MapView.jsx'
import SearchBar from './components/SearchBar.jsx'
import ModeToggle from './components/ModeToggle.jsx'
import Filters from './components/Filters.jsx'
import StationList from './components/StationList.jsx'
import StationDetail from './components/StationDetail.jsx'
import NavPanel from './components/NavPanel.jsx'
import ImpactPanel from './components/ImpactPanel.jsx'
import ProfilePage from './components/ProfilePage.jsx'
import VehicleSetup from './components/VehicleSetup.jsx'
import ChargeRight from './components/ChargeRight.jsx'
import InfoModal from './components/InfoModal.jsx'
import AddStationModal from './components/AddStationModal.jsx'
import Chat from './components/Chat.jsx'
import Toast from './components/Toast.jsx'

export default function App() {
  const nav = useNavigate()
  const loc = useLocation()
  const sub = loc.pathname.replace(/^\/app\/?/, '')
  const go = (r) => nav(r ? `/app/${r}` : '/app')

  const [config, setConfig] = useState(null)
  const [tab, setTab] = useState('explore')
  const [profile, setProfile] = useState(null)
  const [profileRefresh, setProfileRefresh] = useState(0)
  const [infoOpen, setInfoOpen] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [stations, setStations] = useState([])
  const [liveGrid, setLiveGrid] = useState({})
  const [rankInfo, setRankInfo] = useState({})
  const [bestId, setBestId] = useState(null)
  const [mode, setMode] = useState('greenest')
  const [filters, setFilters] = useState({ connector: 'all', radius: 15 })
  const [selectedId, setSelectedId] = useState(null)
  const [userLoc, setUserLoc] = useState(null)
  const [startLabel, setStartLabel] = useState('Kochi centre')
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [routeData, setRouteData] = useState(null)
  const [routing, setRouting] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [footprint, setFootprint] = useState(null)
  const [recycling, setRecycling] = useState([])
  const [showRecycling, setShowRecycling] = useState(false)
  const [selectedRec, setSelectedRec] = useState(null)
  const [addOpen, setAddOpen] = useState(false)
  const [mapPick, setMapPick] = useState(null)
  const [pickedCoord, setPickedCoord] = useState(null)
  const [toast, setToast] = useState('')

  const notify = (m) => { setToast(m); clearTimeout(notify._t); notify._t = setTimeout(() => setToast(''), 2600) }

  useEffect(() => {
    api.getConfig().then((c) => { setConfig(c); setUserLoc(c.center); loadStations(c.center, filters.radius) }).catch(() => notify('Backend not reachable'))
    api.getProfile().then((d) => setProfile(d.profile)).catch(() => {})
    api.getRecycling().then((d) => setRecycling(d.centers || [])).catch(() => {})
  }, [])

  async function loadStations(l, radius) {
    try { const d = await api.getStations(l.lat, l.lng, radius); setStations(d.stations || []) }
    catch { notify('Could not load stations') }
  }

  useEffect(() => {
    if (!stations.length || !userLoc) return
    let cands = stations
    if (filters.connector !== 'all') cands = cands.filter((s) => (s.connectors || []).some((c) => c.includes(filters.connector)))
    api.scoreStations({ user_lat: userLoc.lat, user_lng: userLoc.lng, mode, candidates: cands.map((s) => ({ station_id: s.station_id, name: s.name, lat: s.lat, lng: s.lng, availability: 0.6 })) })
      .then((res) => { const info = {}; res.ranked.forEach((r) => { info[r.station_id] = { distance_km: r.distance_km, score: r.score } }); setRankInfo(info); setBestId(res.best?.station_id || null) })
      .catch(() => {})
  }, [stations, mode, filters.connector, userLoc])

  useEffect(() => {
    if (!stations.length) return
    const ids = stations.map((s) => s.station_id); let alive = true
    const poll = () => api.gridBatch(ids).then((d) => { if (!alive) return; const m = {}; d.grid.forEach((g) => { m[g.station_id] = g }); setLiveGrid(m) }).catch(() => {})
    poll(); const t = setInterval(poll, 6000)
    return () => { alive = false; clearInterval(t) }
  }, [stations])

  useEffect(() => {
    if (searchQ.trim().length < 3) { setSearchResults([]); return }
    const t = setTimeout(() => api.geocode(searchQ).then((d) => setSearchResults(d.results || [])).catch(() => {}), 400)
    return () => clearTimeout(t)
  }, [searchQ])

  function pickPlace(r) {
    const l = { lat: r.lat, lng: r.lng }
    setUserLoc(l); setStartLabel(r.name); setSearchResults([]); setSearchQ('')
    setSelectedId(null); setNavOpen(false); setRouteData(null); loadStations(l, filters.radius); notify('Start set: ' + r.name)
  }
  function useGps() {
    if (!navigator.geolocation) return notify('Geolocation not available')
    navigator.geolocation.getCurrentPosition((p) => { const l = { lat: p.coords.latitude, lng: p.coords.longitude }; setUserLoc(l); setStartLabel('Your location'); loadStations(l, filters.radius); notify('Using your location') }, () => notify('Location blocked'))
  }

  useEffect(() => { if (tab === 'impact') api.getFootprint().then(setFootprint).catch(() => {}) }, [tab])

  const displayStations = useMemo(() => {
    let list = stations.map((s) => {
      const lv = liveGrid[s.station_id]
      const m = lv ? { ...s, carbon_intensity_gco2_kwh: lv.carbon_intensity_gco2_kwh, grid_load_pct: lv.grid_load_pct, renewable_share_pct: lv.renewable_share_pct } : s
      const rk = rankInfo[s.station_id]
      return rk ? { ...m, distance_km: rk.distance_km, score: rk.score } : m
    })
    if (filters.connector !== 'all') list = list.filter((s) => (s.connectors || []).some((c) => c.includes(filters.connector)))
    list.sort((a, b) => (b.score ?? -1) - (a.score ?? -1) || (a.distance_km ?? 999) - (b.distance_km ?? 999))
    return list
  }, [stations, liveGrid, rankInfo, filters.connector])

  const selected = displayStations.find((s) => s.station_id === selectedId) || stations.find((s) => s.station_id === selectedId)

  function onFilters(patch) { const next = { ...filters, ...patch }; setFilters(next); if (patch.radius != null && userLoc) loadStations(userLoc, next.radius) }

  async function navigate() {
    if (!selected || !userLoc) return
    setRouting(true)
    try { const r = await api.getRoute({ start_lat: userLoc.lat, start_lng: userLoc.lng, end_lat: selected.lat, end_lng: selected.lng }); setRouteData(r); setNavOpen(true) }
    catch { notify('Routing needs the ORS key + internet') } finally { setRouting(false) }
  }

  async function charged() {
    if (!selected) return
    try { await api.logSession({ station_id: selected.station_id, station_name: selected.name, kwh: 20 }); notify('Logged 20 kWh — see Impact'); api.getFootprint().then(setFootprint); setProfileRefresh((n) => n + 1) }
    catch { notify('Could not log session') }
  }
  async function submitStation(payload) {
    try { await api.addStation(payload); setAddOpen(false); setPickedCoord(null); notify('Station added 🎉'); if (userLoc) loadStations(userLoc, filters.radius) }
    catch { notify('Could not add station') }
  }
  function onMapClick(lngLat) {
    if (mapPick === 'start') { const l = { lat: lngLat.lat, lng: lngLat.lng }; setUserLoc(l); setStartLabel('Custom pin'); setMapPick(null); loadStations(l, filters.radius); notify('Start location set') }
    else if (mapPick === 'station') { setPickedCoord({ lat: lngLat.lat, lng: lngLat.lng }); setMapPick(null); setAddOpen(true) }
  }
  function backToList() { setSelectedId(null); setNavOpen(false); setRouteData(null) }
  const chargeStation = bestId || selected?.station_id || 'ocm-1'

  // ---- assistant context + actions ----
  function getContext() {
    const trim = (s) => ({ station_id: s.station_id, name: s.name, distance_km: s.distance_km, carbon_intensity_gco2_kwh: s.carbon_intensity_gco2_kwh, grid_load_pct: s.grid_load_pct, connectors: s.connectors, power_kw: s.power_kw })
    const best = displayStations.find((s) => s.station_id === bestId)
    return { mode, best: best ? trim(best) : null, stations: displayStations.slice(0, 8).map(trim), profile }
  }
  function onAction(a) {
    if (!a || !a.type) return
    if (a.type === 'select_station' && a.id) { setTab('explore'); setSelectedId(a.id) }
    else if (a.type === 'set_mode' && ['greenest', 'fastest', 'balanced'].includes(a.mode)) { setMode(a.mode); notify('Mode: ' + a.mode) }
    else if (a.type === 'open') {
      if (a.page === 'charge') go('charge')
      else if (a.page === 'impact') setTab('impact')
      else if (a.page === 'profile') go('profile')
      else if (a.page === 'operator') nav('/operator')
    }
  }

  let body
  if (tab === 'impact') body = <ImpactPanel data={footprint} />
  else if (navOpen && routeData && selected) body = <NavPanel station={selected} route={routeData} onBack={backToList} />
  else if (selected) body = <StationDetail station={selected} mode={mode} profile={profile} isBest={selected.station_id === bestId} onBack={backToList} onNavigate={navigate} onCharged={charged} routing={routing} />
  else body = (
    <>
      <button className="cr-cta" onClick={() => go('charge')}>
        <div><b>⚡ Charge Right</b><span>Best time to charge in the next 24h</span></div>
        <Icon name="clock" size={20} />
      </button>
      <SearchBar value={searchQ} onChange={setSearchQ} results={searchResults} onPick={pickPlace} />
      <button className={'filters-toggle' + (showFilters ? ' open' : '')} onClick={() => setShowFilters((v) => !v)}>
        <span><Icon name="layers" size={14} /> Start &amp; filters</span>
        <span className="muted small">{startLabel} · {filters.radius}km{filters.connector !== 'all' ? ' · ' + filters.connector : ''}</span>
      </button>
      {showFilters && (
        <div className="collapsible">
          <div className="start-card">
            <div><div className="section-label" style={{ margin: 0 }}>Start location</div><div className="start-val"><Icon name="pin" size={14} /> {startLabel}</div></div>
            <div className="start-btns">
              <button className="mini" onClick={useGps}><Icon name="locate" size={14} /> GPS</button>
              <button className={'mini' + (mapPick === 'start' ? ' on' : '')} onClick={() => setMapPick(mapPick === 'start' ? null : 'start')}><Icon name="pin" size={14} /> Map</button>
            </div>
          </div>
          <Filters filters={filters} connectors={connectorList(stations)} onChange={onFilters} />
        </div>
      )}
      <div className="section-label">Rank by</div>
      <ModeToggle value={mode} onChange={setMode} />
      <div className="section-label">{displayStations.length} stations near you</div>
      <StationList stations={displayStations} bestId={bestId} selectedId={selectedId} onSelect={(s) => setSelectedId(s.station_id)} />
    </>
  )

  return (
    <>
      <div className="shell">
        <aside className="sidebar">
          <div className="side-header">
            <div className="grabber" />
            <div className="brand-row">
              <button className="brand brand-btn" onClick={() => nav('/')} title="Home">GRI<span className="brand-mal">ഢം</span></button>
              <div className="head-actions">
                <button className="ic-btn" title="Operator console" onClick={() => nav('/operator')}><Icon name="chart" size={14} /></button>
                <button className="ic-btn" title="Under the Hood" onClick={() => setInfoOpen(true)}><b>i</b></button>
                <span className="region"><span className="live"><i /></span>{config?.region?.split(',')[0] || 'Kochi'}{config?.carbon_source === 'electricitymaps' ? ' · live CO₂' : ''}</span>
                <button className="avatar sm" title="Profile" onClick={() => go('profile')}>{(profile?.name || 'EV').slice(0, 2).toUpperCase()}</button>
              </div>
            </div>
            <div className="seg">
              <button className={tab === 'explore' ? 'active' : ''} onClick={() => setTab('explore')}>Explore</button>
              <button className={tab === 'impact' ? 'active' : ''} onClick={() => setTab('impact')}>Impact</button>
            </div>
          </div>
          <div className="side-body">{body}</div>
        </aside>

        <div className="map-pane">
          {config && (
            <MapView styleUrl={config.map_style_url} center={config.center} stations={displayStations} selectedId={selectedId} bestId={bestId} userLoc={userLoc} routeGeometry={routeData?.geometry}
              recycling={showRecycling ? recycling : []} onRecyclingSelect={setSelectedRec}
              onSelect={(s) => { setTab('explore'); setSelectedId(s.station_id) }} onMapClick={onMapClick} pickMode={mapPick !== null} />
          )}
          <div className="map-chips">
            <button className={'chip-btn' + (showRecycling ? ' on' : '')} onClick={() => { setShowRecycling((v) => !v); setSelectedRec(null) }}><Icon name="recycle" size={14} /> Recycling</button>
          </div>
          <div className="map-fabs"><button className="fab accent" title="My location" onClick={useGps}><Icon name="locate" size={20} /></button></div>
          <button className="add-fab" onClick={() => setAddOpen(true)}><Icon name="plus" size={18} /> Add station</button>
          {selectedRec && (
            <div className="rec-card">
              <button className="icon-btn" style={{ position: 'absolute', top: 12, right: 12 }} onClick={() => setSelectedRec(null)}><Icon name="x" size={14} /></button>
              <div className="tag" style={{ background: 'var(--green-dim)' }}>♲ {selectedRec.type}</div>
              <h3 style={{ margin: '8px 0 4px' }}>{selectedRec.name}</h3>
              <div className="muted small">Accepts: {selectedRec.accepts.join(', ')}</div>
              <div className="muted small">☎ {selectedRec.phone}</div>
            </div>
          )}
          {mapPick && <div className="toast" style={{ top: 20, bottom: 'auto' }}>Tap the map to set {mapPick === 'start' ? 'your start location' : 'the station'}</div>}
        </div>
      </div>

      <Chat getContext={getContext} onAction={onAction} />

      {sub === 'charge' && <ChargeRight stationId={chargeStation} battery={profile?.battery_kwh || 40} onClose={() => go('')} />}
      {sub === 'profile' && <ProfilePage refreshKey={profileRefresh} onClose={() => go('')} onEditVehicle={() => go('vehicle')} />}
      {sub === 'vehicle' && <VehicleSetup profile={profile} onClose={() => go('profile')} onSaved={(pr) => { setProfile(pr); setProfileRefresh((n) => n + 1); notify('Settings saved'); go('profile') }} />}
      {infoOpen && <InfoModal onClose={() => setInfoOpen(false)} />}
      {addOpen && <AddStationModal prefill={pickedCoord} onClose={() => setAddOpen(false)} onSubmit={submitStation} onPickOnMap={() => { setAddOpen(false); setMapPick('station') }} />}
      <Toast message={toast} />
    </>
  )
}

function connectorList(stations) { const set = new Set(); stations.forEach((s) => (s.connectors || []).forEach((c) => set.add(c))); return [...set].sort() }
