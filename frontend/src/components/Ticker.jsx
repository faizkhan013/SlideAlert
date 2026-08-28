export default function Ticker({ alerts }) {
  if (!alerts || alerts.length === 0) return null;
  const text = alerts
    .map((z) => `⚠ ${z.name}, ${z.state}: ${z.risk} risk — ${z.rainfall_24h_mm}mm/24h`)
    .join("     •     ");
  return <div className="alert-ticker">{text}</div>;
}
