import { riskClass } from "../config.js";
import { useZoneRefresh } from "../hooks/useApi.js";

export default function ZoneDetailPanel({ zone, onRefreshed }) {
  const { refreshZone, refreshingId, error } = useZoneRefresh(onRefreshed);

  if (!zone) {
    return (
      <div className="panel-block">
        <h2>Zone Detail</h2>
        <div className="empty-state">Select a zone on the map or sidebar to see its live reading.</div>
      </div>
    );
  }

  const isRefreshing = refreshingId === zone.id;

  return (
    <div className="panel-block">
      <h2>{zone.name}, {zone.state}</h2>
      <div className="risk-readout">
        <span className={"risk-badge " + riskClass(zone.risk)}>{zone.risk}</span>
        <span className="risk-score">{zone.rainfall_24h_mm} mm rainfall / 24h</span>
      </div>
      <div className="zone-meta-row">
        <span className="mono-note">
          last updated {zone.last_updated ? new Date(zone.last_updated).toLocaleString("en-IN", { hour12: false }) : "—"}
        </span>
        <button className="btn" onClick={() => refreshZone(zone.id)} disabled={isRefreshing}>
          {isRefreshing ? "Refreshing…" : "Force refresh"}
        </button>
      </div>
      {error && <div className="empty-state" style={{ marginTop: 10 }}>Refresh failed ({error}).</div>}
    </div>
  );
}
