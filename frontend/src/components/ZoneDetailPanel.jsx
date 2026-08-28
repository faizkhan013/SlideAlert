import { riskClass, getEffectiveRisk } from "../config.js";
import { useZoneRefresh } from "../hooks/useApi.js";

export default function ZoneDetailPanel({ zone, onRefreshed, roadsData, roadsLoading }) {
  const { refreshZone, refreshingId, error } = useZoneRefresh(onRefreshed);
  console.log("ZoneDetailPanel rendering for:", zone?.name, "ml_enabled:", zone?.ml_enabled, "roadsData:", roadsData, "roadsLoading:", roadsLoading);

  if (!zone) {
    return (
      <div className="panel-block">
        <h2>Zone Detail</h2>
        <div className="empty-state">Select a zone on the map or sidebar to see its live reading.</div>
      </div>
    );
  }

  const isRefreshing = refreshingId === zone.id;
  const effectiveRisk = getEffectiveRisk(zone);
  const ml = zone.ml_prediction;

  return (
    <div className="panel-block">
      <h2>{zone.name}, {zone.state}</h2>
      <div className="risk-readout">
        <span className={"risk-badge " + riskClass(effectiveRisk)}>{effectiveRisk}</span>
        <span className="risk-score">{zone.rainfall_24h_mm} mm rainfall / 24h</span>
      </div>
      <div className="zone-meta-row">
        <span className="mono-note">
          last updated {zone.last_updated ? new Date(zone.last_updated).toLocaleString("en-IN", { hour12: false }) : "—"}
        </span>
        <button className="btn" onClick={() => refreshZone(zone.id)} disabled={isRefreshing}>
          {isRefreshing ? "Refreshing…" : "Force refresh"}
        </button>
      </div>

      {zone.ml_enabled && ml ? (
        <div className="ml-section" style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #3c4b57' }}>
          <h3 style={{ fontSize: '13px', margin: '0 0 10px 0', color: '#889eb0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>AI/ML Prediction</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 15px', fontSize: '13px', margin: '5px 0 12px 0' }}>
            <div><strong>Risk Score:</strong> <span className="mono-val">{ml.risk_score} / 100</span></div>
            <div><strong>Risk Level:</strong> <span className="mono-val" style={{ fontWeight: 'bold', textTransform: 'uppercase' }}>{ml.ml_risk_level}</span></div>
            <div><strong>Landslide Probability:</strong> <span className="mono-val">{Math.round(ml.landslide_probability * 100)}%</span></div>
            <div><strong>Predicted Landslide Area:</strong> <span className="mono-val">{Math.round(ml.landslide_area_percent)}%</span></div>
            <div><strong>Confidence:</strong> <span className="mono-val">{Math.round(ml.confidence * 100)}%</span></div>
          </div>

          {ml.risk_factors && ml.risk_factors.length > 0 && (
            <div className="risk-factors" style={{ fontSize: '13px', margin: '8px 0 0 0' }}>
              <strong>Risk Factors:</strong>
              <ul style={{ margin: '5px 0 0 0', paddingLeft: '20px', color: '#a0b3c2', lineHeight: '1.4' }}>
                {ml.risk_factors.map((f, idx) => (
                  <li key={idx}>{f}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="ml-section" style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #3c4b57', fontSize: '12px', color: '#7a8e9e', fontStyle: 'italic' }}>
          AI/ML prediction unavailable for this zone.
        </div>
      )}

      {/* 5 KM AFFECTED ROADS section */}
      {roadsData && (
        <div className="roads-section" style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #3c4b57' }}>
          <h3 style={{ fontSize: '13px', margin: '0 0 10px 0', color: '#889eb0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            5 KM Affected Roads
          </h3>
          
          {roadsLoading && <div className="loading-text" style={{ fontSize: '12px', color: '#7a8e9e' }}>Loading road network data…</div>}
          
          {!roadsLoading && (!roadsData.roads || roadsData.roads.length === 0) && (
            <div style={{ fontSize: '12px', color: '#7a8e9e', fontStyle: 'italic' }}>
              No road network data available for this zone.
            </div>
          )}

          {!roadsLoading && roadsData.roads && roadsData.roads.length > 0 && (
            <>
              {/* Safety warning based on actual returned road risk levels */}
              {(() => {
                const hasHigh = roadsData.roads.some((r) => r.risk_level === "high");
                if (hasHigh) {
                  return (
                    <div style={{
                      backgroundColor: 'rgba(226, 73, 47, 0.1)',
                      borderLeft: '3px solid #e2492f',
                      padding: '8px 10px',
                      borderRadius: '3px',
                      fontSize: '12px',
                      lineHeight: '1.4',
                      color: '#f38170',
                      marginBottom: '12px'
                    }}>
                      <strong>Safety Advisory:</strong> High-risk road segments detected within 5 km. Avoid highlighted red roads and follow official travel advisories.
                    </div>
                  );
                } else {
                  return (
                    <div style={{
                      backgroundColor: 'rgba(79, 174, 122, 0.1)',
                      borderLeft: '3px solid #4fae7a',
                      padding: '8px 10px',
                      borderRadius: '3px',
                      fontSize: '12px',
                      lineHeight: '1.4',
                      color: '#65cf96',
                      marginBottom: '12px'
                    }}>
                      <strong>Safety Advisory:</strong> No high-risk road segments detected within 5 km. Continue to follow official travel advisories.
                    </div>
                  );
                }
              })()}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
                {roadsData.roads.map((road, idx) => {
                  let badgeColor = '#4fae7a';
                  if (road.risk_level === 'high') badgeColor = '#e2492f';
                  else if (road.risk_level === 'moderate') badgeColor = '#e8a33d';

                  return (
                    <div key={idx} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '12px',
                      backgroundColor: '#27343f',
                      padding: '6px 10px',
                      borderRadius: '4px'
                    }}>
                      <div style={{ flex: 1, marginRight: '10px' }}>
                        <div style={{ fontWeight: '500', color: '#e8ecef' }}>{road.name}</div>
                        <div style={{ fontSize: '11px', color: '#7a8e9e' }}>Distance: {road.distance_km} km</div>
                      </div>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{
                          fontSize: '9px',
                          fontWeight: 'bold',
                          textTransform: 'uppercase',
                          color: badgeColor,
                          backgroundColor: `rgba(${road.risk_level === 'high' ? '226, 73, 47' : road.risk_level === 'moderate' ? '232, 163, 61' : '79, 174, 122'}, 0.08)`,
                          padding: '2px 6px',
                          borderRadius: '3px',
                          border: `1px solid ${badgeColor}`
                        }}>
                          {road.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      )}

      {error && <div className="empty-state" style={{ marginTop: 10 }}>Refresh failed ({error}).</div>}
    </div>
  );
}
