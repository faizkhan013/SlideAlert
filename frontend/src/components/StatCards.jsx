export default function StatCards({ stats }) {
  if (!stats) return null;
  const { total, counts, lastUpdated } = stats;
  return (
    <div className="stat-cards-row">
      <div className="stat-card">
        <div className="label">Zones monitored</div>
        <div className="val">{total}</div>
      </div>
      <div className="stat-card">
        <div className="label">High risk</div>
        <div className="val risk-high-text">{counts.high || 0}</div>
      </div>
      <div className="stat-card">
        <div className="label">Moderate risk</div>
        <div className="val risk-med-text">{counts.moderate || 0}</div>
      </div>
      <div className="stat-card">
        <div className="label">Low risk</div>
        <div className="val risk-low-text">{counts.low || 0}</div>
      </div>
      <div className="stat-card">
        <div className="label">Last sync</div>
        <div className="val mono-val">
          {lastUpdated ? new Date(lastUpdated).toLocaleTimeString("en-IN", { hour12: false }) : "—"}
        </div>
      </div>
    </div>
  );
}
