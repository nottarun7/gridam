// Charge time + cost estimate for a chosen battery, from 20%→80%.
export function chargeEstimate(powerKw, batteryKwh, fromPct = 20, toPct = 80, ratePerKwh = 18) {
  const p = powerKw > 0 ? powerKw : 50
  const kwh = (batteryKwh * (toPct - fromPct)) / 100
  const minutes = Math.round((kwh / p) * 60)
  const cost = Math.round(kwh * ratePerKwh)
  return { minutes, cost, kwh: Math.round(kwh), power: p }
}

// Haversine km — used for client-side distance when scoring hasn't run yet.
export function distanceKm(a, b) {
  const R = 6371, toR = (d) => (d * Math.PI) / 180
  const dLat = toR(b.lat - a.lat), dLng = toR(b.lng - a.lng)
  const s = Math.sin(dLat / 2) ** 2 +
    Math.cos(toR(a.lat)) * Math.cos(toR(b.lat)) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.asin(Math.sqrt(s))
}

export const carbonColor = (c) => (c < 550 ? '#00e676' : c < 720 ? '#ffc24b' : '#ff5a5f')
export const loadColor = (l) => (l < 45 ? '#00e676' : l < 70 ? '#ffc24b' : '#ff5a5f')
