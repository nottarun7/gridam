// Same-origin API (nginx proxies to the backend in prod; vite proxies in dev).
async function j(path, opts) {
  const r = await fetch('/api' + path, opts)
  if (!r.ok) throw new Error(`${path} → ${r.status}`)
  return r.json()
}
const post = (path, body) =>
  j(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const getConfig = () => j('/config')
export const getStations = (lat, lng, distance) =>
  j(`/charging-stations?lat=${lat}&lng=${lng}&distance=${distance}`)
export const scoreStations = (body) => post('/score', body)
export const gridBatch = (ids) => post('/grid/batch', { station_ids: ids })
export const getRoute = (body) => post('/route', body)
export const geocode = (q) => j(`/geocode?q=${encodeURIComponent(q)}`)
export const logSession = (body) => post('/sessions', body)
export const getFootprint = () => j('/footprint/summary')
export const addStation = (body) => post('/stations', body)

const put = (path, body) => j(path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
export const getProfile = () => j('/profile')
export const saveProfile = (body) => put('/profile', body)
export const getForecast = (stationId = 'ocm-1', chargeHours = 2) => j(`/forecast?station_id=${stationId}&charge_hours=${chargeHours}`)
export const getRecycling = () => j('/recycling')
export const chat = (messages, context) => post('/chat', { messages, context })
export const getOperator = () => j('/operator/summary')
