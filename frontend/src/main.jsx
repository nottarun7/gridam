import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  Activity,
  AlertTriangle,
  BatteryCharging,
  Bot,
  Car,
  ChevronRight,
  Gauge,
  Leaf,
  MapPin,
  Navigation,
  PanelRightOpen,
  PlugZap,
  RefreshCw,
  Route as RouteIcon,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  UserRound,
  Zap,
} from "lucide-react";
import "./styles.css";

const kochi = { lat: 9.9312, lng: 76.2673 };
const modes = [
  { id: "balanced", label: "Balanced", detail: "distance + grid" },
  { id: "greenest", label: "Greenest", detail: "lowest carbon" },
  { id: "fastest", label: "Fastest", detail: "power + proximity" },
];
const navItems = [
  { to: "/app", label: "Map", icon: MapPin },
  { to: "/app/recommendation", label: "Smart", icon: Sparkles },
  { to: "/app/dashboard", label: "Dashboard", icon: Activity },
  { to: "/app/profile", label: "Profile", icon: UserRound },
];

async function api(path, options = {}) {
  const res = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  if (!res.ok) throw new Error(`${path} failed`);
  return res.json();
}

function useAppData() {
  const [config, setConfig] = useState(null);
  const [stations, setStations] = useState([]);
  const [mode, setMode] = useState("balanced");
  const [center, setCenter] = useState(kochi);
  const [selected, setSelected] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [impact, setImpact] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");

  const loadStations = async (nextMode = mode, nextCenter = center) => {
    setLoading(true);
    try {
      const data = await api(`/charging-stations?lat=${nextCenter.lat}&lng=${nextCenter.lng}&distance=40&mode=${nextMode}`);
      setStations(data);
      setSelected((current) => (current && data.some((s) => s.id === current.id) ? current : data[0] || null));
      setNotice("");
    } catch {
      setNotice("Station feeds are offline. Showing the last available view.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api("/config")
      .then(setConfig)
      .catch(() => setConfig({ center: kochi, carbon_source: "kerala-model", map_style_url: "https://demotiles.maplibre.org/style.json", zone: "IN-SO" }));
    api("/footprint/summary").then(setImpact).catch(() => {});
  }, []);

  useEffect(() => {
    loadStations(mode, center);
  }, [mode, center.lat, center.lng]);

  useEffect(() => {
    if (!selected) return;
    setForecast(null);
    api(`/forecast?station_id=${selected.id}&charge_hours=2.5`).then(setForecast).catch(() => {});
  }, [selected?.id]);

  return { config, stations, mode, setMode, center, setCenter, selected, setSelected, forecast, impact, loading, notice, setNotice, refresh: loadStations };
}

function cx(...items) {
  return items.filter(Boolean).join(" ");
}

function AppShell() {
  const state = useAppData();
  const [route, setRoute] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  const context = useMemo(
    () => ({ stations: state.stations.slice(0, 6), selected: state.selected, forecast: state.forecast, mode: state.mode }),
    [state.stations, state.selected, state.forecast, state.mode],
  );

  const navigateToSelected = async () => {
    if (!state.selected) return;
    try {
      const data = await api("/route", { method: "POST", body: JSON.stringify({ start: state.center, end: { lat: state.selected.lat, lng: state.selected.lng } }) });
      setRoute(data);
      state.setNotice(`Route ready via ${data.source}.`);
    } catch {
      state.setNotice("Routing is unavailable right now.");
    }
  };

  const recordCharge = async () => {
    if (!state.selected) return;
    await api("/sessions", {
      method: "POST",
      body: JSON.stringify({
        station_id: state.selected.id,
        station_name: state.selected.name,
        kwh: 18,
        carbon_intensity: state.selected.carbon_intensity_gco2_kwh,
        cost_inr: 144,
      }),
    });
    state.setNotice("Charging session recorded. Dashboard metrics are refreshed.");
  };

  return (
    <main className="app-grid">
      <CommandRail activePath={location.pathname} config={state.config} />
      <FinderPanel state={state} />
      <section className="map-stage" aria-label="Charging map workspace">
        <MapView config={state.config} stations={state.stations} selected={state.selected} setSelected={state.setSelected} center={state.center} route={route} />
        <TopStatus state={state} />
        {state.notice && <Toast message={state.notice} tone={state.notice.includes("offline") || state.notice.includes("unavailable") ? "warning" : "success"} />}
        <StationDetails station={state.selected} forecast={state.forecast} onNavigate={navigateToSelected} onRecord={recordCharge} onSmart={() => navigate("/app/recommendation")} />
        <Routes>
          <Route path="/" element={null} />
          <Route path="recommendation" element={<SmartRecommendation station={state.selected} forecast={state.forecast} mode={state.mode} setMode={state.setMode} />} />
          <Route path="dashboard" element={<DriverDashboard impact={state.impact} stations={state.stations} forecast={state.forecast} />} />
          <Route path="profile" element={<Profile />} />
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Routes>
      </section>
      <Assistant context={context} onAction={(action) => action?.open?.page && navigate(`/app/${action.open.page}`)} />
    </main>
  );
}

function CommandRail({ activePath, config }) {
  return (
    <aside className="command-rail" aria-label="Primary navigation">
      <Link to="/app" className="brand-mark" aria-label="GRIDAM charging map">
        <span>G</span>
      </Link>
      <nav>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.to === "/app" ? activePath === "/app" : activePath.startsWith(item.to);
          return (
            <Link key={item.to} to={item.to} className={cx("rail-button", active && "active")} title={item.label} aria-label={item.label}>
              <Icon size={20} />
            </Link>
          );
        })}
        <Link to="/operator" className="rail-button" title="Operator dashboard" aria-label="Operator dashboard">
          <Gauge size={20} />
        </Link>
      </nav>
      <div className="rail-source" title={`Grid zone ${config?.zone || "IN-SO"}`}>
        <Leaf size={16} />
      </div>
    </aside>
  );
}

function FinderPanel({ state }) {
  const best = state.stations[0];
  return (
    <aside className="finder-panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Kochi launch grid</p>
          <h1>GRIDAM</h1>
        </div>
        <button className="icon-button" onClick={() => state.refresh()} title="Refresh stations" aria-label="Refresh stations">
          <RefreshCw size={18} />
        </button>
      </div>

      <label className="search-box">
        <Search size={18} />
        <input placeholder="Search charger, area, network" onKeyDown={(e) => e.key === "Enter" && state.setCenter(kochi)} aria-label="Search chargers" />
      </label>

      <div className="mode-switch" role="tablist" aria-label="Ranking mode">
        {modes.map((m) => (
          <button key={m.id} className={cx(state.mode === m.id && "active")} onClick={() => state.setMode(m.id)} role="tab" aria-selected={state.mode === m.id}>
            <span>{m.label}</span>
            <small>{m.detail}</small>
          </button>
        ))}
      </div>

      {best && (
        <article className="best-card">
          <div className="orbital-score">{Math.round(best.score)}</div>
          <div>
            <p className="eyebrow">Best pick now</p>
            <h2>{best.name}</h2>
            <p>{best.distance_km} km away with {best.available}/{best.plugs} plugs free</p>
          </div>
        </article>
      )}

      <StationList stations={state.stations} selected={state.selected} setSelected={state.setSelected} loading={state.loading} />
    </aside>
  );
}

function MapView({ config, stations, selected, setSelected, center, route }) {
  const ref = useRef(null);
  const map = useRef(null);
  const markers = useRef([]);

  useEffect(() => {
    if (!ref.current || map.current || !config) return;
    map.current = new maplibregl.Map({
      container: ref.current,
      style: config.map_style_url,
      center: [center.lng, center.lat],
      zoom: 11.6,
      pitch: 38,
      bearing: -12,
    });
    map.current.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
  }, [config]);

  useEffect(() => {
    if (!map.current) return;
    markers.current.forEach((m) => m.remove());
    markers.current = stations.map((s) => {
      const el = document.createElement("button");
      const level = s.carbon_intensity_gco2_kwh < 420 ? "clean" : s.carbon_intensity_gco2_kwh < 620 ? "mid" : "dirty";
      el.className = `map-pin ${level} ${selected?.id === s.id ? "active" : ""}`;
      el.title = `${s.name}, score ${s.score}`;
      el.setAttribute("aria-label", s.name);
      el.onclick = () => setSelected(s);
      return new maplibregl.Marker({ element: el }).setLngLat([s.lng, s.lat]).addTo(map.current);
    });
  }, [stations, selected?.id]);

  useEffect(() => {
    if (!map.current || !route) return;
    const id = "gridam-route";
    const source = map.current.getSource(id);
    const data = { type: "Feature", geometry: route.geometry, properties: {} };
    if (source) source.setData(data);
    else {
      map.current.addSource(id, { type: "geojson", data });
      map.current.addLayer({ id, type: "line", source: id, paint: { "line-color": "#32ff8f", "line-width": 5, "line-blur": 1.5, "line-opacity": 0.92 } });
    }
  }, [route]);

  return <div className="map-canvas" ref={ref} />;
}

function TopStatus({ state }) {
  return (
    <div className="top-status">
      <StatusPill icon={ShieldCheck} label="Source" value={state.config?.carbon_source || "loading"} />
      <StatusPill icon={Gauge} label="Zone" value={state.config?.zone || "IN-SO"} />
      <StatusPill icon={PlugZap} label="Chargers" value={state.loading ? "syncing" : String(state.stations.length)} />
    </div>
  );
}

function StatusPill({ icon: Icon, label, value }) {
  return (
    <div className="status-pill">
      <Icon size={16} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function StationList({ stations, selected, setSelected, loading }) {
  if (loading && !stations.length) return <SkeletonList />;
  if (!stations.length) return <EmptyState icon={MapPin} title="No chargers in range" body="Try refreshing or widening the search radius after station feeds return." />;
  return (
    <div className="station-stack">
      {stations.map((s, index) => (
        <button key={s.id} className={cx("station-row", selected?.id === s.id && "selected")} onClick={() => setSelected(s)}>
          <span className="rank">{String(index + 1).padStart(2, "0")}</span>
          <span className="station-copy">
            <strong>{s.name}</strong>
            <small>{s.operator} / {s.connector} / {s.power_kw} kW</small>
          </span>
          <span className="score-chip">{Math.round(s.score)}</span>
        </button>
      ))}
    </div>
  );
}

function StationDetails({ station, forecast, onNavigate, onRecord, onSmart }) {
  if (!station) return null;
  return (
    <section className="station-sheet" aria-label="Station details">
      <div className="sheet-main">
        <div>
          <p className="eyebrow">Station details</p>
          <h2>{station.name}</h2>
          <p>{station.operator} / {station.connector} / {station.source}</p>
        </div>
        <div className="score-ring">
          <span>{Math.round(station.score)}</span>
          <small>score</small>
        </div>
      </div>
      <MetricGrid>
        <Metric label="Carbon" value={station.carbon_intensity_gco2_kwh} suffix="g/kWh" />
        <Metric label="Renewable" value={station.renewable_share_pct} suffix="%" />
        <Metric label="Grid load" value={station.grid_load_pct} suffix="%" />
        <Metric label="Available" value={`${station.available}/${station.plugs}`} suffix="plugs" />
      </MetricGrid>
      <div className="action-row">
        <button className="primary-action" onClick={onNavigate}><Navigation size={18} /> Navigate</button>
        <button onClick={onSmart}><Sparkles size={18} /> Smart plan</button>
        <button onClick={onRecord}><BatteryCharging size={18} /> I charged</button>
      </div>
      {forecast && <RecommendationStrip forecast={forecast} />}
    </section>
  );
}

function SmartRecommendation({ station, forecast, mode, setMode }) {
  return (
    <Overlay title="Smart Recommendation" icon={Sparkles}>
      {!station ? (
        <EmptyState icon={Zap} title="Select a station first" body="Recommendation quality improves once a charger is selected from the map." />
      ) : (
        <>
          <div className="recommend-hero">
            <div>
              <p className="eyebrow">Charge plan</p>
              <h2>{station.name}</h2>
              <p>Balanced against carbon intensity, tariff, grid load, distance, and plug availability.</p>
            </div>
            <div className="neon-window">
              <strong>{forecast?.recommended?.hour ?? "--"}:00</strong>
              <span>best start</span>
            </div>
          </div>
          <div className="mode-switch compact">
            {modes.map((m) => <button key={m.id} className={cx(mode === m.id && "active")} onClick={() => setMode(m.id)}>{m.label}</button>)}
          </div>
          <ForecastPanel forecast={forecast} />
          <div className="explain-grid">
            <DecisionCard icon={Leaf} title="Cleaner window" value={`${forecast?.greenest?.carbon ?? station.carbon_intensity_gco2_kwh} g/kWh`} body="Prioritizes midday solar and avoids evening demand peaks." />
            <DecisionCard icon={RouteIcon} title="Trip fit" value={`${station.distance_km} km`} body={`${station.power_kw} kW charger with ${station.available} available plug${station.available === 1 ? "" : "s"}.`} />
            <DecisionCard icon={Zap} title="Cost guardrail" value={`INR ${forecast?.cheapest?.price ?? 8}/kWh`} body="Keeps tariff spikes visible before committing to the session." />
          </div>
        </>
      )}
    </Overlay>
  );
}

function DriverDashboard({ impact, stations, forecast }) {
  return (
    <Overlay title="Driver Dashboard" icon={Activity}>
      {!impact ? (
        <SkeletonList />
      ) : (
        <>
          <MetricGrid>
            <Metric label="Energy" value={impact.total_kwh} suffix="kWh" />
            <Metric label="CO2 saved" value={impact.co2_saved_kg} suffix="kg" />
            <Metric label="Money saved" value={`INR ${impact.money_saved_inr}`} suffix="" />
            <Metric label="Sessions" value={impact.sessions} suffix="total" />
          </MetricGrid>
          <div className="dashboard-grid">
            <Panel title="Recent charging">
              <BarSeries data={impact.recent || []} />
            </Panel>
            <Panel title="Network pulse">
              <ForecastPanel forecast={forecast} condensed />
            </Panel>
          </div>
          <Panel title="Top stations">
            <div className="table-list">
              {stations.slice(0, 5).map((s) => (
                <div key={s.id}><span>{s.name}</span><strong>{Math.round(s.score)}</strong><small>{s.carbon_intensity_gco2_kwh} g/kWh</small></div>
              ))}
            </div>
          </Panel>
        </>
      )}
    </Overlay>
  );
}

function Profile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ vehicle: "", battery_kwh: "", efficiency_km_kwh: "" });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api("/profile").then((data) => {
      setProfile(data);
      setForm({ vehicle: data.vehicle, battery_kwh: data.battery_kwh, efficiency_km_kwh: data.efficiency_km_kwh });
    }).catch(() => {});
  }, []);

  const save = async () => {
    const updated = await api("/profile", { method: "PUT", body: JSON.stringify(form) });
    setProfile(updated);
    setSaved(true);
    window.setTimeout(() => setSaved(false), 2000);
  };

  return (
    <Overlay title="Profile" icon={UserRound}>
      {!profile ? <SkeletonList /> : (
        <div className="profile-grid">
          <Panel title="Vehicle">
            {["vehicle", "battery_kwh", "efficiency_km_kwh"].map((key) => (
              <label className="field" key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <input value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
              </label>
            ))}
            <button className="primary-action full" onClick={save}><Settings size={18} /> {saved ? "Saved" : "Save profile"}</button>
          </Panel>
          <Panel title="Impact profile">
            <MetricGrid>
              <Metric label="EV distance" value={profile.analytics.ev_km} suffix="km" />
              <Metric label="Avg carbon" value={profile.analytics.avg_carbon} suffix="g/kWh" />
            </MetricGrid>
          </Panel>
        </div>
      )}
    </Overlay>
  );
}

function Operator() {
  const [data, setData] = useState(null);
  useEffect(() => { api("/operator/summary").then(setData).catch(() => {}); }, []);
  return (
    <main className="operator-page">
      <header className="operator-top">
        <Link to="/app" className="brand-word">GRIDAM</Link>
        <Link to="/app" className="launch-link"><MapPin size={18} /> Charging map</Link>
      </header>
      {!data ? <section className="operator-shell"><SkeletonList /></section> : (
        <section className="operator-shell">
          <div className="operator-hero">
            <div>
              <p className="eyebrow">Operator dashboard</p>
              <h1>Network control room</h1>
              <p>Demo telemetry for station load, plug availability, carbon source, and shiftable demand.</p>
            </div>
            <StatusPill icon={ShieldCheck} label="Carbon source" value={data.carbon_source} />
          </div>
          <MetricGrid>
            <Metric label="Network load" value={data.network_load_pct} suffix="%" />
            <Metric label="Stations" value={data.station_count} suffix="sites" />
            <Metric label="Free plugs" value={data.available_plugs} suffix="now" />
            <Metric label="DR window" value="18-22" suffix="peak" />
          </MetricGrid>
          <div className="dashboard-grid">
            <Panel title="Demand curve"><Curve data={data.curve} /></Panel>
            <Panel title="Operator mix"><OperatorMix data={data.by_operator} /></Panel>
          </div>
          <Panel title="Station status">
            <div className="operator-table">
              {data.stations.slice(0, 10).map((s) => (
                <div key={s.id}><span>{s.name}</span><span>{s.operator}</span><strong>{s.available}/{s.plugs}</strong><small>{s.carbon_intensity_gco2_kwh} g/kWh</small></div>
              ))}
            </div>
          </Panel>
        </section>
      )}
    </main>
  );
}

function Assistant({ context, onAction }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([{ role: "assistant", text: "Ask for the cleanest charger, a cheaper start time, or a route-ready station." }]);

  const send = async () => {
    if (!message.trim() || busy) return;
    const userText = message.trim();
    setMessage("");
    setBusy(true);
    setLog((items) => [...items, { role: "user", text: userText }]);
    try {
      const res = await api("/chat", { method: "POST", body: JSON.stringify({ message: userText, context }) });
      setLog((items) => [...items, { role: "assistant", text: res.reply || "I found a recommendation." }]);
      if (res.action) onAction(res.action);
    } catch {
      setLog((items) => [...items, { role: "assistant", text: "Assistant service is offline, but charger ranking and forecasts are still available." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className={cx("assistant-dock", open && "open")}>
      <button className="assistant-toggle" onClick={() => setOpen(!open)} aria-label="Open AI assistant">
        {open ? <PanelRightOpen size={20} /> : <Bot size={20} />}
      </button>
      {open && (
        <div className="assistant-panel">
          <div className="assistant-head"><Bot size={20} /><div><strong>GRIDAM AI</strong><span>Grounded in current grid context</span></div></div>
          <div className="chat-log">{log.map((item, i) => <p key={i} className={item.role}>{item.text}</p>)}</div>
          <div className="chat-input">
            <input value={message} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask when to charge" />
            <button onClick={send} disabled={busy} aria-label="Send message"><Send size={18} /></button>
          </div>
        </div>
      )}
    </aside>
  );
}

function ForecastPanel({ forecast, condensed = false }) {
  if (!forecast) return <EmptyState icon={Activity} title="Forecast loading" body="The 24-hour grid and tariff curve will appear here." />;
  const max = Math.max(...forecast.points.map((p) => p.carbon));
  const min = Math.min(...forecast.points.map((p) => p.carbon));
  const points = forecast.points.map((p, i) => {
    const x = 4 + (i / Math.max(forecast.points.length - 1, 1)) * 92;
    const y = 86 - ((p.carbon - min) / Math.max(max - min, 1)) * 66;
    return `${x},${y}`;
  }).join(" ");
  return (
    <div className={cx("forecast-panel", condensed && "condensed")}>
      <div className="forecast-head">
        <span>{forecast.source}</span>
        <strong>{forecast.charge_hours}h charge window</strong>
      </div>
      <svg viewBox="0 0 100 100" role="img" aria-label="24 hour carbon forecast">
        <polyline points={points} fill="none" stroke="var(--neon)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        {forecast.points.map((p, i) => <rect key={`${p.time}-${i}`} x={4 + i * 3.8} y={92 - p.price * 4.4} width="1.8" height={p.price * 4.4} rx="0.8" fill="var(--cyan)" opacity="0.45" />)}
      </svg>
      {!condensed && <RecommendationStrip forecast={forecast} />}
    </div>
  );
}

function RecommendationStrip({ forecast }) {
  return (
    <div className="recommend-strip">
      <Metric label="Greenest" value={`${forecast.greenest.hour}:00`} suffix={`${forecast.greenest.carbon} g/kWh`} />
      <Metric label="Cheapest" value={`${forecast.cheapest.hour}:00`} suffix={`INR ${forecast.cheapest.price}/kWh`} />
      <Metric label="Recommended" value={`${forecast.recommended.hour}:00`} suffix="carbon + tariff" />
    </div>
  );
}

function MetricGrid({ children }) {
  return <div className="metric-grid">{children}</div>;
}

function Metric({ label, value, suffix }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {suffix && <small>{suffix}</small>}
    </div>
  );
}

function DecisionCard({ icon: Icon, title, value, body }) {
  return (
    <article className="decision-card">
      <Icon size={20} />
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{body}</p>
    </article>
  );
}

function Panel({ title, children }) {
  return <section className="data-panel"><h3>{title}</h3>{children}</section>;
}

function Overlay({ title, icon: Icon, children }) {
  return (
    <div className="screen-overlay">
      <section className="screen-panel">
        <div className="overlay-head"><div><Icon size={20} /><h2>{title}</h2></div><Link to="/app" aria-label="Close panel">Close</Link></div>
        {children}
      </section>
    </div>
  );
}

function EmptyState({ icon: Icon, title, body }) {
  return <div className="empty-state"><Icon size={24} /><strong>{title}</strong><p>{body}</p></div>;
}

function SkeletonList() {
  return <div className="skeleton-stack">{Array.from({ length: 5 }).map((_, i) => <span key={i} />)}</div>;
}

function Toast({ message, tone }) {
  return <div className={cx("toast", tone)}><AlertTriangle size={16} />{message}</div>;
}

function BarSeries({ data }) {
  const max = Math.max(...data.map((d) => d.kwh || 0), 1);
  return <div className="bar-series">{data.map((d) => <span key={d.id} style={{ height: `${24 + ((d.kwh || 0) / max) * 112}px` }} title={d.station_name} />)}</div>;
}

function Curve({ data }) {
  const max = Math.max(...data.map((d) => d.load), 1);
  return <div className="curve-bars">{data.map((d, i) => <span key={`${d.hour}-${i}`} style={{ height: `${22 + (d.load / max) * 130}px` }}><small>{d.hour}</small></span>)}</div>;
}

function OperatorMix({ data }) {
  return <div className="operator-mix">{Object.entries(data).map(([name, count]) => <div key={name}><span>{name}</span><strong>{count}</strong></div>)}</div>;
}

function Landing() {
  const features = [
    { icon: MapPin, title: "Charging map", body: "Find Kochi chargers with live availability signals, connector details, distance, and source labels." },
    { icon: Leaf, title: "Carbon-aware ranking", body: "Compare Greenest, Fastest, and Balanced scores before choosing where to plug in." },
    { icon: BatteryCharging, title: "Charge Right forecast", body: "Plan a charging window using 24-hour carbon intensity, grid load, and time-of-use tariff curves." },
    { icon: Bot, title: "Grounded assistant", body: "Ask the AI for station choices or cleaner start times based on the active map and forecast context." },
  ];

  const mechanics = [
    { label: "Distance", value: "30%", body: "Haversine distance is normalized across nearby chargers so closer stations score higher." },
    { label: "Carbon", value: "30-45%", body: "Carbon intensity comes from Electricity Maps for IN-SO when available, then falls back to a Kerala-calibrated model." },
    { label: "Grid load", value: "15-30%", body: "Synthetic load curves penalize the evening peak and reward midday or late-night charging windows." },
    { label: "Availability", value: "10-20%", body: "Free plug ratio and charger power keep recommendations realistic for a driver who needs to charge now." },
  ];

  return (
    <main className="landing-page">
      <nav className="landing-nav" aria-label="Landing navigation">
        <Link to="/" className="brand-word">GRIDAM</Link>
        <div>
          <a href="#about">About</a>
          <a href="#features">Features</a>
          <a href="#under-hood">Under the hood</a>
          <a href="#contact">Contact</a>
          <Link className="launch-link" to="/app"><MapPin size={18} /> Open app</Link>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="hero-map-scene" aria-hidden="true">
          <span className="route-line one" />
          <span className="route-line two" />
          <span className="hero-pin primary" />
          <span className="hero-pin secondary" />
          <span className="hero-pin tertiary" />
          <div className="hero-dashboard-card main">
            <p className="eyebrow">Best charger now</p>
            <strong>KSEB EV Hub - MG Road</strong>
            <span>412 g/kWh / 2.8 km / 3 plugs</span>
          </div>
          <div className="hero-dashboard-card mini">
            <Leaf size={18} />
            <span>Green window 13:00</span>
          </div>
        </div>
        <div className="hero-copy">
          <p className="eyebrow">Grid-aware EV charging for Kochi</p>
          <h1>Charge where the grid is cleanest.</h1>
          <p>
            GRIDAM ranks EV chargers using carbon intensity, grid load, distance, availability, and tariff timing so drivers can make cleaner charging decisions without slowing down.
          </p>
          <div className="hero-actions">
            <Link className="hero-primary" to="/app"><Zap size={20} /> Launch charging map</Link>
            <a className="hero-secondary" href="#under-hood">See the calculations <ChevronRight size={18} /></a>
          </div>
          <div className="hero-stats" aria-label="GRIDAM demo statistics">
            <Metric label="Launch zone" value="IN-SO" suffix="Kerala grid" />
            <Metric label="Forecast" value="24h" suffix="carbon + tariff" />
            <Metric label="Modes" value="3" suffix="ranking strategies" />
          </div>
        </div>
      </section>

      <section id="about" className="landing-section split-section">
        <div>
          <p className="eyebrow">About</p>
          <h2>Built for the moment before a driver plugs in.</h2>
        </div>
        <p>
          Most charging apps show where chargers are. GRIDAM adds when and why: it turns station data, modeled grid behavior, and user impact into a clean recommendation layer for Kochi's EV drivers and operators.
        </p>
      </section>

      <section id="features" className="landing-section">
        <div className="section-heading">
          <p className="eyebrow">Features</p>
          <h2>Everything the demo needs, kept focused.</h2>
        </div>
        <div className="landing-card-grid">
          {features.map((item) => <LandingCard key={item.title} {...item} />)}
        </div>
      </section>

      <section id="under-hood" className="landing-section under-hood">
        <div className="section-heading">
          <p className="eyebrow">Under the hood</p>
          <h2>How the statistics and recommendations work.</h2>
          <p>Scores are transparent enough for a hackathon judge to follow and practical enough for a driver to trust.</p>
        </div>
        <div className="formula-panel">
          <div>
            <span>Balanced score</span>
            <strong>0.30 distance + 0.30 carbon + 0.25 grid + 0.15 availability</strong>
            <p>Greenest increases carbon weight to 45%. Fastest increases proximity weight to 55% and still protects against overloaded or unavailable stations.</p>
          </div>
          <Gauge size={46} />
        </div>
        <div className="landing-card-grid mechanics">
          {mechanics.map((item) => <article key={item.label} className="mechanic-card"><span>{item.label}</span><strong>{item.value}</strong><p>{item.body}</p></article>)}
        </div>
      </section>

      <section id="contact" className="landing-section contact-section">
        <div>
          <p className="eyebrow">Contact us</p>
          <h2>Want to pilot greener charging decisions?</h2>
          <p>Use GRIDAM for demos, operator walkthroughs, or partner-data conversations around Kerala's EV charging network.</p>
        </div>
        <div className="contact-actions">
          <a className="hero-primary" href="mailto:hello@gridam.local"><Send size={18} /> hello@gridam.local</a>
          <Link className="hero-secondary" to="/operator">View operator dashboard <ChevronRight size={18} /></Link>
        </div>
      </section>
    </main>
  );
}

function LandingCard({ icon: Icon, title, body }) {
  return (
    <article className="landing-card">
      <Icon size={22} />
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}

function Root() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app/*" element={<AppShell />} />
        <Route path="/operator" element={<Operator />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")).render(<Root />);
