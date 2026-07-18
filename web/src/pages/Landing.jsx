import { useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import evCar from '../assets/EV_CAR.webp'

const NETWORKS = ['Open Charge Map', 'ChargeMOD', 'Zeon', 'Tata Power', 'Statiq', 'KSEB', 'Community']
const FEATURES = [
  ['pin', 'Unified live map', 'Every charger from Open Charge Map plus Indian networks, colored by live carbon intensity.'],
  ['clock', 'Charge Right scheduler', 'A 24-hour grid forecast finds the greenest and cheapest window to plug in — and reminds you.'],
  ['nav', 'Smart routing', 'Turn-by-turn directions with a live drive simulation and ETA to your chosen charger.'],
  ['chart', 'Carbon & money dashboard', 'CO₂ saved vs. petrol, energy mix, km driven electric, and rupees saved — with real charts.'],
  ['battery', 'Battery health & second-life', 'A health estimate, a smart-charging coach, and a map of recycling / second-life centers.'],
  ['bolt', 'Grid-aware ranking', 'Greenest / Fastest / Balanced — rank stations by what matters, powered by live grid data.'],
]
const FORMULAS = [
  ['Carbon intensity', 'gCO₂ per kWh at a station now — falls with renewable share, rises under peak load.'],
  ['Recommendation score', 'Weighted blend of proximity, low grid load, low carbon, and availability; the mode changes the weights.'],
  ['CO₂ per charge', 'kWh charged × the station’s live carbon intensity.'],
  ['Money saved', 'Petrol fuel cost for the same distance (your mileage × petrol price) minus your charging cost.'],
  ['Charge Right window', 'The 2-hour slot over the next 24h that minimises 0.6 × carbon + 0.4 × price.'],
]

export default function Landing() {
  const nav = useNavigate()
  const launch = () => nav('/app')
  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  return (
    <div className="landing">
      <nav className="lnav">
        <span className="brand">GRI<span className="brand-mal">ഢം</span></span>
        <div className="lnav-links">
          <button onClick={() => scrollTo('about')}>About</button>
          <button onClick={() => scrollTo('features')}>Features</button>
          <button onClick={() => scrollTo('how')}>Under the Hood</button>
          <button onClick={() => scrollTo('contact')}>Contact</button>
          <button onClick={() => nav('/operator')}>For operators</button>
        </div>
        <button className="btn primary" onClick={launch}><Icon name="bolt" size={15} /> Launch app</button>
      </nav>

      {/* HERO */}
      <header className="hero">
        <div className="hero-glow" />
        <div className="hero-left">
          <div className="pill-badge"><span className="live"><i /></span> Live grid · Kochi, Kerala</div>
          <h1>Charge right.<br /><span className="grad">Drive clean.</span></h1>
          <p className="lead">GRIഢം is a grid-aware EV charging companion. It doesn’t just find you a charger — it tells you the greenest and cheapest time and place to plug in, turning EVs from a strain on the grid into support for it.</p>
          <div className="hero-cta">
            <button className="btn primary lg" onClick={launch}><Icon name="bolt" size={18} /> Launch the app</button>
            <button className="btn ghost lg" onClick={() => scrollTo('how')}>How it works</button>
          </div>
          <div className="hero-stats">
            <div><b>7</b><span>charging networks</span></div>
            <div><b>24h</b><span>grid forecast</span></div>
            <div><b>3</b><span>ranking modes</span></div>
          </div>
        </div>
        <div className="hero-right">
          <AppPreview />
        </div>
      </header>

      {/* ABOUT */}
      <section id="about" className="lsec">
        <div className="lsec-grid">
          <div>
            <div className="eyebrow">About GRIഢം</div>
            <h2>EVs are only as clean as the grid they charge on.</h2>
            <p>When everyone charges at the evening peak, they strain the grid — and that peak power is the dirtiest, most expensive electricity of the day. GRIഢം gives drivers the missing visibility: live carbon, live cost, and the exact moment to charge. Every driver who charges right shaves the peak, cuts carbon, and saves money — and at city scale that’s real infrastructure impact.</p>
            <div className="net-row">{NETWORKS.map((n) => <span className="chip" key={n}>{n}</span>)}</div>
          </div>
          <CarArt />
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="lsec">
        <div className="eyebrow center">Features</div>
        <h2 className="center">Everything you need to charge smarter</h2>
        <div className="feat-grid">
          {FEATURES.map(([ic, t, d]) => (
            <div className="feat-card" key={t}>
              <span className="feat-ic"><Icon name={ic} size={20} /></span>
              <h3>{t}</h3><p>{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* UNDER THE HOOD */}
      <section id="how" className="lsec how">
        <div className="eyebrow center">Under the Hood</div>
        <h2 className="center">How GRIഢം works</h2>
        <p className="center sub">Real data where it exists, an honest synthetic model where it doesn’t — built to swap in live feeds.</p>
        <div className="how-grid">
          <div className="how-card">
            <h3><Icon name="pin" size={16} /> Data sources</h3>
            <ul>
              <li><b>Chargers:</b> Open Charge Map + ChargeMOD, Zeon, Tata Power, Statiq, KSEB, and community adds.</li>
              <li><b>Map:</b> MapTiler / OpenStreetMap.</li>
              <li><b>Routing:</b> OpenRouteService (turn-by-turn + ETA).</li>
              <li><b>Search:</b> Nominatim geocoding.</li>
              <li><b>Carbon:</b> Electricity Maps (live, Southern-India grid).</li>
            </ul>
          </div>
          <div className="how-card">
            <h3><Icon name="bolt" size={16} /> The grid model</h3>
            <p>Carbon intensity and renewable share are <b>live from Electricity Maps</b> for the Southern-India grid (zone IN-SO), so they vary hour-to-hour with real conditions. Grid load is modelled, calibrated to real Kerala figures — a ~5,600 MW peak, the 7–11pm evening peak, KSEB’s 90% hydro + 10% solar generation, and ~70% coal-heavy imports. If the live feed is unavailable, the calibrated model steps in automatically — one interface, real or modelled.</p>
          </div>
          <div className="how-card wide">
            <h3><Icon name="chart" size={16} /> How the metrics are calculated</h3>
            <div className="formula-grid">
              {FORMULAS.map(([k, v]) => <div key={k}><b>{k}</b><span>{v}</span></div>)}
            </div>
          </div>
        </div>
      </section>

      {/* CONTACT */}
      <section id="contact" className="lsec contact">
        <div className="eyebrow center">Contact</div>
        <h2 className="center">Let’s charge right, together.</h2>
        <p className="center sub">Built for the hackathon — grid-aware EV charging for Kerala and India.</p>
        <div className="contact-actions">
          <button className="btn primary lg" onClick={launch}><Icon name="bolt" size={18} /> Try the live app</button>
          <a className="btn ghost lg" href="mailto:hello@gridam.app"><Icon name="mail" size={16} /> Get in touch</a>
        </div>
      </section>

      <footer className="lfoot">
        <span className="brand">GRI<span className="brand-mal">ഢം</span></span>
        <span className="muted small">Charge right. Drive clean. · Kochi, Kerala</span>
      </footer>
    </div>
  )
}

function AppPreview() {
  return (
    <div className="preview">
      <div className="preview-top"><span className="live"><i /></span> Kochi · live</div>
      <div className="preview-map">
        <svg viewBox="0 0 260 180" width="100%" height="100%" preserveAspectRatio="none">
          {[...Array(7)].map((_, i) => <line key={'v' + i} x1={i * 40} y1="0" x2={i * 40} y2="180" stroke="#213029" strokeWidth="1" />)}
          {[...Array(5)].map((_, i) => <line key={'h' + i} x1="0" y1={i * 40} x2="260" y2={i * 40} stroke="#213029" strokeWidth="1" />)}
          <path d="M60 150 L120 90 L140 100" stroke="#3d8bff" strokeWidth="4" fill="none" strokeLinecap="round" />
        </svg>
        <span className="preview-pin best" /><span className="preview-pin p1" /><span className="preview-pin p2" />
        <div className="preview-chip"><Icon name="clock" size={13} /> Charge Right · best window</div>
      </div>
      <div className="preview-modes">
        <span>Greenest</span><span>Fastest</span><span>Balanced</span>
      </div>
    </div>
  )
}

function CarArt() {
  return (
    <div className="carart">
      <img src={evCar} alt="Electric vehicle charging" className="carart-img" />
      <div className="carart-cap"><span className="chip">⚡ 100% electric</span><span className="chip">🌿 grid-aware</span></div>
    </div>
  )
}
