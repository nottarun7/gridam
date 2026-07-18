import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { carbonColor } from '../lib/estimate.js'

export default function MapView({
  styleUrl, center, stations, selectedId, bestId, userLoc,
  routeGeometry, carPos, recycling = [], onSelect, onRecyclingSelect, onMapClick, pickMode,
}) {
  const ref = useRef(null)
  const map = useRef(null)
  const ready = useRef(false)
  const markers = useRef(new Map())
  const recMarkers = useRef(new Map())
  const meMarker = useRef(null)
  const carMarker = useRef(null)
  const cbSelect = useRef(onSelect)
  const cbRec = useRef(onRecyclingSelect)
  const cbClick = useRef(onMapClick)
  const pick = useRef(pickMode)
  cbSelect.current = onSelect; cbRec.current = onRecyclingSelect
  cbClick.current = onMapClick; pick.current = pickMode

  useEffect(() => {
    if (map.current) return
    map.current = new maplibregl.Map({
      container: ref.current, style: styleUrl || 'https://demotiles.maplibre.org/style.json',
      center: [center.lng, center.lat], zoom: 12.4, attributionControl: false,
    })
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }))
    map.current.on('load', () => { ready.current = true })
    map.current.on('click', (e) => { if (pick.current) cbClick.current?.(e.lngLat) })
    return () => { map.current?.remove(); map.current = null }
  }, []) // eslint-disable-line

  useEffect(() => {
    if (!map.current) return
    const seen = new Set()
    stations.forEach((s) => {
      seen.add(s.station_id)
      let m = markers.current.get(s.station_id)
      if (!m) {
        const el = document.createElement('div'); el.className = 'pin'
        el.addEventListener('click', (ev) => { ev.stopPropagation(); cbSelect.current?.(s) })
        m = new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([s.lng, s.lat]).addTo(map.current)
        markers.current.set(s.station_id, m)
      }
      m.getElement().style.background = carbonColor(s.carbon_intensity_gco2_kwh)
      m.getElement().classList.toggle('best', s.station_id === bestId)
      m.getElement().classList.toggle('sel', s.station_id === selectedId)
    })
    markers.current.forEach((m, id) => { if (!seen.has(id)) { m.remove(); markers.current.delete(id) } })
  }, [stations, bestId, selectedId])

  // recycling markers
  useEffect(() => {
    if (!map.current) return
    const seen = new Set()
    recycling.forEach((rc) => {
      seen.add(rc.id)
      let m = recMarkers.current.get(rc.id)
      if (!m) {
        const el = document.createElement('div'); el.className = 'recpin'
        el.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#04120b" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 19H4.8a2 2 0 01-1.7-3l2.3-4M11 5.8L12.9 2.6a2 2 0 013.4 0l2 3.4M17 19l3-1.7a2 2 0 00.6-2.9l-2-3.4"/></svg>'
        el.addEventListener('click', (ev) => { ev.stopPropagation(); cbRec.current?.(rc) })
        m = new maplibregl.Marker({ element: el }).setLngLat([rc.lng, rc.lat]).addTo(map.current)
        recMarkers.current.set(rc.id, m)
      }
    })
    recMarkers.current.forEach((m, id) => { if (!seen.has(id)) { m.remove(); recMarkers.current.delete(id) } })
  }, [recycling])

  useEffect(() => {
    if (!map.current || !userLoc) return
    if (!meMarker.current) { const el = document.createElement('div'); el.className = 'pin me'; meMarker.current = new maplibregl.Marker({ element: el }) }
    meMarker.current.setLngLat([userLoc.lng, userLoc.lat]).addTo(map.current)
  }, [userLoc])

  useEffect(() => {
    if (!map.current || !selectedId) return
    const s = stations.find((x) => x.station_id === selectedId)
    if (s) map.current.flyTo({ center: [s.lng, s.lat], zoom: 13.5, speed: 0.8 })
  }, [selectedId]) // eslint-disable-line

  useEffect(() => {
    if (!map.current) return
    const draw = () => {
      const src = map.current.getSource('route')
      if (!routeGeometry) { if (src) { map.current.removeLayer('route'); map.current.removeSource('route') } return }
      const data = { type: 'Feature', geometry: routeGeometry, properties: {} }
      if (src) src.setData(data)
      else {
        map.current.addSource('route', { type: 'geojson', data })
        map.current.addLayer({ id: 'route', type: 'line', source: 'route', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#3d8bff', 'line-width': 5, 'line-opacity': 0.9 } })
      }
      const c = routeGeometry.coordinates
      if (c && c.length) { const b = c.reduce((bb, p) => bb.extend(p), new maplibregl.LngLatBounds(c[0], c[0])); map.current.fitBounds(b, { padding: 70, maxZoom: 15, duration: 700 }) }
    }
    if (ready.current) draw(); else map.current.once('load', draw)
  }, [routeGeometry])

  useEffect(() => {
    if (!map.current) return
    if (!carPos) { carMarker.current?.remove(); carMarker.current = null; return }
    if (!carMarker.current) {
      const el = document.createElement('div'); el.className = 'car'
      el.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#04120b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l19-9-9 19-2-8-8-2z"/></svg>'
      carMarker.current = new maplibregl.Marker({ element: el })
    }
    carMarker.current.setLngLat([carPos.lng, carPos.lat]).addTo(map.current)
    map.current.panTo([carPos.lng, carPos.lat], { duration: 400 })
  }, [carPos])

  return <div id="map" ref={ref} />
}
