import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap, Polyline, Circle, Rectangle } from "react-leaflet";
import { riskClass, getEffectiveRisk } from "../config.js";

const COLORS = { high: "#e2492f", medium: "#e8a33d", low: "#4fae7a", unknown: "#5c766f" };

function PanTo({ lat, lon }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lon != null) map.panTo([lat, lon]);
  }, [lat, lon, map]);
  return null;
}

export default function MapPane({ zones, selected, onSelect, roadsData }) {
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
            const cls = riskClass(getEffectiveRisk(z));
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

        {/* Draw 5 km Boundary for Selected Zone */}
        {selected && (
          <Circle
            center={[selected.latitude, selected.longitude]}
            radius={5000}
            pathOptions={{
              color: "#7a8e9e",
              fillColor: "#7a8e9e",
              fillOpacity: 0.03,
              weight: 1.5,
              dashArray: "5, 5"
            }}
          />
        )}

        {/* Draw Hazard Scan Bounding Box if ML is enabled */}
        {roadsData && roadsData.ml_enabled && roadsData.hazard_bbox && (
          <Rectangle
            bounds={[
              [roadsData.hazard_bbox.lat_min, roadsData.hazard_bbox.lon_min],
              [roadsData.hazard_bbox.lat_max, roadsData.hazard_bbox.lon_max]
            ]}
            pathOptions={{
              color: "#e2492f",
              fillColor: "#e2492f",
              fillOpacity: 0.08,
              weight: 1.2,
              dashArray: "3, 3"
            }}
          >
            <Tooltip permanent={false}>U-Net Scanned Hazard Area</Tooltip>
          </Rectangle>
        )}

        {/* Draw Affected Roads */}
        {roadsData && roadsData.roads &&
          roadsData.roads.map((road, idx) => {
            const positions = road.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
            let color = "#4fae7a"; // low risk default
            let weight = 3;
            if (road.risk_level === "high") {
              color = "#e2492f"; // red
              weight = 4.5;
            } else if (road.risk_level === "moderate") {
              color = "#e8a33d"; // orange
              weight = 3.5;
            }
            return (
              <Polyline
                key={idx}
                positions={positions}
                pathOptions={{ color, weight, opacity: 0.85 }}
              >
                <Tooltip sticky>
                  <div>
                    <strong>{road.name}</strong><br />
                    Risk Level: <span style={{ color, fontWeight: 'bold' }}>{road.risk_level.toUpperCase()}</span> ({road.status.toUpperCase()})<br />
                    Distance to Center: {road.distance_km} km
                  </div>
                </Tooltip>
              </Polyline>
            );
          })}

        {selected && <PanTo lat={selected.latitude} lon={selected.longitude} />}
      </MapContainer>
      <div className="map-legend" style={{ gap: '8px 12px', flexWrap: 'wrap' }}>
        <div className="legend-item"><span className="dot high"></span>High</div>
        <div className="legend-item"><span className="dot medium"></span>Moderate</div>
        <div className="legend-item"><span className="dot low"></span>Low</div>
        <div className="legend-item"><span className="dot unknown"></span>No data</div>
        <div className="legend-item" style={{ borderLeft: '1px solid #3c4b57', paddingLeft: '8px' }}>
          <span style={{ display: 'inline-block', width: '12px', height: '3px', backgroundColor: '#e2492f', marginRight: '5px' }}></span>Road: Avoid
        </div>
        <div className="legend-item">
          <span style={{ display: 'inline-block', width: '12px', height: '3px', backgroundColor: '#e8a33d', marginRight: '5px' }}></span>Road: Caution
        </div>
        <div className="legend-item">
          <span style={{ display: 'inline-block', width: '12px', height: '3px', backgroundColor: '#4fae7a', marginRight: '5px' }}></span>Road: Low Risk
        </div>
        <div className="legend-item">
          <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', border: '1.5px dashed #7a8e9e', marginRight: '5px' }}></span>5km Range
        </div>
      </div>
    </div>
  );
}
