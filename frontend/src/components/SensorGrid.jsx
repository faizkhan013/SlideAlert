import { riskClass } from "../config.js";

export default function SensorGrid({ zones, selected, onSelect }) {
  return (
    <div className="panel-block">
      <h2>Zone Sensor Grid</h2>
      {!zones && <div className="loading-text">Loading zones…</div>}
      <div className="sensor-grid">
        {zones &&
          zones.map((z) => (
            <div
              key={z.id}
              className={"sensor-card" + (selected?.id === z.id ? " active" : "")}
              onClick={() => onSelect(z)}
            >
              <div className="sensor-card-top">
                <span className="sensor-name">{z.name}</span>
                <span className={"risk-badge small " + riskClass(z.risk)}>{z.risk}</span>
              </div>
              <div className="sensor-card-meta">{z.state}</div>
              <div className="sensor-card-rain">{z.rainfall_24h_mm} mm <span>/ 24h</span></div>
              <div className="sensor-card-updated">
                {z.last_updated ? new Date(z.last_updated).toLocaleTimeString("en-IN", { hour12: false }) : "—"}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}
