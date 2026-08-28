import { riskClass } from "../config.js";

// alerts = zones with risk != low, sorted by severity (derived client-side
// from /api/zones/ in App.jsx). Swap this prop for a fetchServerAlerts()
// result if you'd rather the backend's /api/alerts/ own the filtering.
export default function AlertsPanel({ alerts }) {
  return (
    <div className="panel-block">
      <h2>Active Alerts</h2>
      {alerts && alerts.length === 0 && (
        <div className="empty-state">No zones above low risk right now.</div>
      )}
      {!alerts && <div className="loading-text">Loading…</div>}
      {alerts &&
        alerts.map((z) => (
          <div className="alert-item" key={z.id}>
            <span className={"sev " + riskClass(z.risk)}></span>
            <div>
              <div className="txt">
                {z.name}, {z.state} — {z.risk} risk ({z.rainfall_24h_mm} mm / 24h)
              </div>
              <div className="meta">
                {z.last_updated ? new Date(z.last_updated).toLocaleString("en-IN", { hour12: false }) : "—"}
              </div>
            </div>
          </div>
        ))}
    </div>
  );
}
