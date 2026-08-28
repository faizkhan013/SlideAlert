import { useState, useEffect, useCallback } from "react";
import { API_BASE } from "../config.js";

/**
 * GET /api/zones/
 * All zones, live rainfall + computed risk + 14-day series.
 * This is the single call boot() makes — it feeds the map markers,
 * alerts, stat cards, sensor grid, and every sparkline.
 * Polls every 5 minutes; the backend itself caches Open-Meteo for 30 min.
 */
export function useZones(pollMs = 5 * 60 * 1000) {
  const [zones, setZones] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchZones = useCallback(() => {
    fetch(`${API_BASE}/zones/`)
      .then((r) => {
        if (!r.ok) throw new Error("zones/ " + r.status);
        return r.json();
      })
      .then((data) => {
        setZones(data);
        setError(null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchZones();
    const t = setInterval(fetchZones, pollMs);
    return () => clearInterval(t);
  }, [fetchZones, pollMs]);

  return { zones, error, loading, refetch: fetchZones };
}

/**
 * POST /api/zones/:id/refresh/
 * Forces a live re-fetch from Open-Meteo for one zone, bypassing the
 * 30-minute cache. Wired to a manual "Refresh" button on the detail panel.
 */
export function useZoneRefresh(onRefreshed) {
  const [refreshingId, setRefreshingId] = useState(null);
  const [error, setError] = useState(null);

  const refreshZone = useCallback(
    (id) => {
      setRefreshingId(id);
      setError(null);
      fetch(`${API_BASE}/zones/${id}/refresh/`, { method: "POST" })
        .then((r) => {
          if (!r.ok) throw new Error("refresh " + r.status);
          return r.json();
        })
        .then((data) => onRefreshed && onRefreshed(data))
        .catch((e) => setError(e.message))
        .finally(() => setRefreshingId(null));
    },
    [onRefreshed]
  );

  return { refreshZone, refreshingId, error };
}

/**
 * GET /api/zones/:id/
 * Same shape as a single item from /zones/. Not used by boot(), but
 * handy for a per-zone detail route if you build one later.
 */
export function fetchZoneDetail(id) {
  return fetch(`${API_BASE}/zones/${id}/`).then((r) => {
    if (!r.ok) throw new Error("zones/" + id + " " + r.status);
    return r.json();
  });
}

/**
 * GET /api/alerts/ — server-computed version of the alert list (zones with
 * risk != low, pre-sorted by severity). The frontend currently derives this
 * client-side from /zones/ (see deriveAlerts in App.jsx) so this hook isn't
 * called by default — swap useZones-derived alerts for this if you'd rather
 * the backend own that logic.
 */
export function fetchServerAlerts() {
  return fetch(`${API_BASE}/alerts/`).then((r) => {
    if (!r.ok) throw new Error("alerts/ " + r.status);
    return r.json();
  });
}

/**
 * GET /api/stats/ — server-computed summary counts. Same story as above:
 * the frontend currently derives stats client-side from /zones/
 * (see deriveStats in App.jsx); this is the drop-in server-side swap.
 */
export function fetchServerStats() {
  return fetch(`${API_BASE}/stats/`).then((r) => {
    if (!r.ok) throw new Error("stats/ " + r.status);
    return r.json();
  });
}
