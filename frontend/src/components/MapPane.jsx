import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from "react-leaflet";
import { riskClass } from "../config.js";

const COLORS = { high: "#e2492f", medium: "#e8a33d", low: "#4fae7a", unknown: "#5c766f" };

function PanTo({ lat, lon }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lon != null) map.panTo([lat, lon]);
  }, [lat, lon, map]);
  return null;
}

export default function MapPane({ zones, selected, onSelect }) {
  return (
    <div className="map-pane">
      <MapContainer center={[25.8, 92.5]} zoom={6.3} className="leaflet-container">
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={18}
        />
        {zones &&
          zones.map((z) => {
            const cls = riskClass(z.risk);
            const color = COLORS[cls];
            return (
              <CircleMarker
                key={z.id}
                center={[z.latitude, z.longitude]}
                radius={8}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.85, weight: 2 }}
                eventHandlers={{ click: () => onSelect(z) }}
              >
                <Tooltip direction="top">
                  {z.name} — {z.rainfall_24h_mm} mm / 24h
                </Tooltip>
              </CircleMarker>
            );
          })}
        {selected && <PanTo lat={selected.latitude} lon={selected.longitude} />}
      </MapContainer>
      <div className="map-legend">
        <div className="legend-item"><span className="dot high"></span>High</div>
        <div className="legend-item"><span className="dot medium"></span>Moderate</div>
        <div className="legend-item"><span className="dot low"></span>Low</div>
        <div className="legend-item"><span className="dot unknown"></span>No data</div>
      </div>
    </div>
  );
}
