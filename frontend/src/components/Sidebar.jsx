import { riskClass } from "../config.js";

export default function Sidebar({ zones, selected, onSelect, connection }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="mark">TERRAIN WATCH</span>
        <span className="sub">SIH26001 · MDoNER</span>
      </div>
      <div>
        <div className="nav-label">Zones</div>
        <div className="station-list">
          {!zones && <div className="loading-text">Loading zones…</div>}
          {zones &&
            zones.map((z) => (
              <div
                key={z.id}
                className={"station-item" + (selected?.id === z.id ? " active" : "")}
                onClick={() => onSelect(z)}
              >
                <span>{z.name}</span>
                <span className={"dot " + riskClass(z.risk)}></span>
              </div>
            ))}
        </div>
      </div>
      <div className={"conn-status " + connection}>
        <span className="pulse"></span>
        {connection === "checking" && "Connecting to /api/zones/…"}
        {connection === "ok" && "Backend online"}
        {connection === "err" && "Backend unreachable — set API_BASE"}
      </div>
    </aside>
  );
}
