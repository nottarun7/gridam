import Icon from './Icon.jsx'

export default function Intro({ onEnter }) {
  return (
    <div className="intro">
      <div className="intro-glow" />
      <div className="intro-inner">
        <div className="intro-badge"><span className="live"><i /></span> Kochi · live grid</div>
        <h1 className="intro-title">GRI<span className="brand-mal">ഢം</span></h1>
        <p className="intro-tag">Charge right. Drive clean.</p>
        <p className="intro-sub">Grid-aware EV charging — find chargers, pick the greenest &amp; cheapest time to plug in, and cut your carbon and cost while helping flatten the grid.</p>
        <div className="intro-feats">
          <span><Icon name="pin" size={14} /> Live charger map</span>
          <span><Icon name="clock" size={14} /> Charge Right scheduler</span>
          <span><Icon name="chart" size={14} /> Carbon dashboard</span>
          <span><Icon name="recycle" size={14} /> Battery second-life</span>
        </div>
        <button className="btn primary" style={{ padding: '14px 34px', fontSize: 16 }} onClick={onEnter}>
          <Icon name="bolt" size={18} /> Enter GRIഢം
        </button>
      </div>
    </div>
  )
}
