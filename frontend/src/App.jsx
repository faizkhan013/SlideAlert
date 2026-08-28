import { useState, useMemo, useEffect } from "react";
import { RISK_SEVERITY, getEffectiveRisk } from "./config.js";
import { useZones, useAffectedRoads } from "./hooks/useApi.js";

import Sidebar from "./components/Sidebar.jsx";
import MapPane from "./components/MapPane.jsx";
import Clock from "./components/Clock.jsx";
import Ticker from "./components/Ticker.jsx";
import StatCards from "./components/StatCards.jsx";
import SensorGrid from "./components/SensorGrid.jsx";
import ZoneDetailPanel from "./components/ZoneDetailPanel.jsx";
import SparklinePanel from "./components/SparklinePanel.jsx";
import AlertsPanel from "./components/AlertsPanel.jsx";

// Client-side derivation of /api/stats/ from the /api/zones/ payload.
// Swap for fetchServerStats() if you'd rather the backend compute this.
function deriveStats(zones) {
  if (!zones) return null;
  const counts = { low: 0, moderate: 0, high: 0, severe: 0 };
  let lastUpdated = "";
  zones.forEach((z) => {
    let k = (getEffectiveRisk(z) || "").toLowerCase();
    if (k === "severe" || k === "critical") k = "high";
    if (k === "medium") k = "moderate";
    if (counts[k] !== undefined) counts[k]++;
    if (z.last_updated && z.last_updated > lastUpdated) lastUpdated = z.last_updated;
  });
  return { total: zones.length, counts, lastUpdated };
}

// Client-side derivation of /api/alerts/ from the /api/zones/ payload.
// Swap for fetchServerAlerts() if you'd rather the backend own the filtering.
function deriveAlerts(zones) {
  if (!zones) return null;
  return [...zones]
    .filter((z) => (getEffectiveRisk(z) || "").toLowerCase() !== "low")
    .sort((a, b) => {
      const sa = RISK_SEVERITY[(getEffectiveRisk(a) || "").toLowerCase()] ?? -1;
      const sb = RISK_SEVERITY[(getEffectiveRisk(b) || "").toLowerCase()] ?? -1;
      return sb - sa;
    });
}

export default function App() {
  // boot(): the only call this app makes on load — GET /api/zones/
  const { zones, error, loading, refetch } = useZones();
  const [selectedId, setSelectedId] = useState(null);

  const connection = loading ? "checking" : error ? "err" : "ok";
  const stats = useMemo(() => deriveStats(zones), [zones]);
  const alerts = useMemo(() => deriveAlerts(zones), [zones]);

  const selected = useMemo(() => {
    if (!zones) return null;
    return zones.find((z) => z.id === selectedId) || zones[0] || null;
  }, [zones, selectedId]);

  const { data: roadsData, loading: roadsLoading } = useAffectedRoads(selected?.id);

  useEffect(() => {
    if (!selectedId && zones && zones.length > 0) setSelectedId(zones[0].id);
  }, [zones, selectedId]);

  return (
    <div className="contour-bg-wrapper">
      <div className="contour-bg"></div>
      <div className="app">
        <Sidebar zones={zones} selected={selected} onSelect={(z) => setSelectedId(z.id)} connection={connection} />
        <div className="main">
          <div className="topbar">
            <div>
              <h1>North Eastern Region — Landslide Early Warning</h1>
              <span className="region">{selected ? `Viewing: ${selected.name}, ${selected.state}` : "Loading zones…"}</span>
            </div>
            <Clock />
          </div>

          <Ticker alerts={alerts} />

          {error && (
            <div className="panel-block">
              <div className="empty-state">
                <b>Could not reach the backend.</b><br />
                GET <code>/api/zones/</code> failed ({error}). Check <code>API_BASE</code> in{" "}
                <code>src/config.js</code> and that the Django server is running.
              </div>
            </div>
          )}

          <div className="panel-block" style={{ paddingBottom: 0 }}>
            <StatCards stats={stats} />
          </div>

          <div className="grid">
            <MapPane zones={zones} selected={selected} onSelect={(z) => setSelectedId(z.id)} roadsData={roadsData} />
            <div className="detail-pane">
              <ZoneDetailPanel zone={selected} onRefreshed={refetch} roadsData={roadsData} roadsLoading={roadsLoading} />
              <SparklinePanel zone={selected} />
              <AlertsPanel alerts={alerts} />
            </div>
          </div>

          <SensorGrid zones={zones} selected={selected} onSelect={(z) => setSelectedId(z.id)} />
        </div>
      </div>
    </div>
  );
}
