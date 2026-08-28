// Point this at your Django backend.
export const API_BASE = "http://127.0.0.1:8000/api";
// zone.risk comes back as "low" | "moderate" | "high" (possibly "severe").
// This maps it to the CSS/risk-badge classes used across the UI.
export function riskClass(risk) {
  if (!risk) return "unknown";
  const r = risk.toLowerCase();
  if (r === "low") return "low";
  if (r === "moderate" || r === "medium") return "medium";
  if (r === "high" || r === "severe") return "high";
  return "unknown";
}

// Used to sort alerts by severity, worst first.
export const RISK_SEVERITY = { low: 0, moderate: 1, medium: 1, high: 2, severe: 3 };
