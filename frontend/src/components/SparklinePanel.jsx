import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

export default function SparklinePanel({ zone }) {
  if (!zone) return null;

  const series = zone.series || [];
  const chartData = {
    labels: series.map((p) => p.date),
    datasets: [
      {
        label: "Precipitation (mm)",
        data: series.map((p) => p.precipitation_mm),
        borderColor: "#6fbfa0",
        backgroundColor: "rgba(111,191,160,0.15)",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        ticks: { color: "#a9c2b8", font: { family: "JetBrains Mono", size: 9 }, maxTicksLimit: 6 },
        grid: { display: false },
      },
      y: {
        ticks: { color: "#a9c2b8", font: { family: "JetBrains Mono", size: 9 } },
        grid: { color: "rgba(111,191,160,0.08)" },
      },
    },
  };

  return (
    <div className="panel-block">
      <h2>14-Day Precipitation — {zone.name}</h2>
      <div className="source-note">from zone.series (Open-Meteo, cached server-side)</div>
      {series.length === 0 ? (
        <div className="empty-state">No series data returned for this zone.</div>
      ) : (
        <div style={{ height: 150 }}>
          <Line data={chartData} options={options} />
        </div>
      )}
    </div>
  );
}
