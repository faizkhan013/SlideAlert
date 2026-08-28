"""
risk_engine.py - Heuristic risk scoring engine for combining ML and weather triggers.
"""
import numpy as np
from ai_ml.features.rainfall import extract_rainfall_features

class LandslideRiskEngine:
    """
    Computes diagnostic landslide risk scores and levels.
    Uses configurable, domain-informed weights for spatial ML masks and temporal weather data.
    """
    def __init__(self, 
                 ml_weight=0.5, 
                 rain_weight=0.5,
                 prob_threshold_high=0.70,
                 area_threshold_large=5.0,
                 rain_24h_threshold_heavy=64.5,
                 rain_3d_threshold_high=100.0,
                 rain_7d_threshold_high=150.0,
                 rain_14d_threshold_high=250.0):
        
        self.ml_weight = ml_weight
        self.rain_weight = rain_weight
        
        # Thresholds for generating risk factor warnings
        self.prob_threshold_high = prob_threshold_high
        self.area_threshold_large = area_threshold_large
        self.rain_24h_threshold_heavy = rain_24h_threshold_heavy
        self.rain_3d_threshold_high = rain_3d_threshold_high
        self.rain_7d_threshold_high = rain_7d_threshold_high
        self.rain_14d_threshold_high = rain_14d_threshold_high

    def compute_risk(self, landslide_probability, landslide_area_percent, rainfall_series):
        """
        Combines spatial ML indicators and rainfall time series into a 0-100 score.
        
        landslide_probability: Maximum probability from U-Net (0.0 to 1.0)
        landslide_area_percent: Spatial area fraction predicted as landslide (0.0 to 100.0)
        rainfall_series: 14-day rainfall list (floats or dicts)
        """
        # 1. Extract rainfall features
        rain_feats = extract_rainfall_features(rainfall_series)
        
        # 2. Compute ML Segmentation Score (Max 50 points)
        # Probability gets 25 points max (scaled linearly)
        ml_prob_points = landslide_probability * 25.0
        
        # Area percentage gets 25 points max (capped at 15.0% landslide area to trigger max points)
        ml_area_points = min(landslide_area_percent / 15.0, 1.0) * 25.0
        
        ml_score = ml_prob_points + ml_area_points
        
        # 3. Compute Rainfall Score (Max 50 points)
        # We assign weights to different time intervals:
        # - 24h Rainfall: Max 15 points (Capped at 80 mm)
        rain_24h_points = min(rain_feats["rainfall_24h_mm"] / 80.0, 1.0) * 15.0
        
        # - 3d Cumulative: Max 15 points (Capped at 150 mm)
        rain_3d_points = min(rain_feats["rainfall_3d_mm"] / 150.0, 1.0) * 15.0
        
        # - 7d Cumulative: Max 10 points (Capped at 250 mm)
        rain_7d_points = min(rain_feats["rainfall_7d_mm"] / 250.0, 1.0) * 10.0
        
        # - 14d Cumulative: Max 10 points (Capped at 350 mm)
        rain_14d_points = min(rain_feats["rainfall_14d_mm"] / 350.0, 1.0) * 10.0
        
        rain_score = rain_24h_points + rain_3d_points + rain_7d_points + rain_14d_points
        
        # 4. Sum and Normalize (Max 100 points)
        raw_score = (ml_score * (self.ml_weight / 0.5)) + (rain_score * (self.rain_weight / 0.5))
        risk_score = int(min(max(round(raw_score), 0), 100))
        
        # 5. Map to React-compatible Categorical Risk Level
        if risk_score >= 75:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "moderate"
        else:
            risk_level = "low"
            
        # 6. Generate Human-Readable Risk Factors
        risk_factors = []
        if landslide_probability >= self.prob_threshold_high:
            risk_factors.append("High landslide probability")
        if landslide_area_percent >= self.area_threshold_large:
            risk_factors.append("Large predicted landslide area")
        if rain_feats["rainfall_24h_mm"] >= self.rain_24h_threshold_heavy:
            risk_factors.append("Heavy 24-hour rainfall")
        if rain_feats["rainfall_3d_mm"] >= self.rain_3d_threshold_high:
            risk_factors.append("High 3-day cumulative rainfall")
        if rain_feats["rainfall_7d_mm"] >= self.rain_7d_threshold_high:
            risk_factors.append("High 7-day cumulative rainfall")
        if rain_feats["rainfall_14d_mm"] >= self.rain_14d_threshold_high:
            risk_factors.append("High antecedent 14-day rainfall")
            
        if not risk_factors:
            risk_factors.append("Stable terrain indices and low precipitation")
            
        # 7. Diagnostic Confidence Metric
        # Defined as the distance of U-Net predictions from the ambiguous 0.5 decision boundary
        confidence = float(0.5 + abs(landslide_probability - 0.5) * 0.8)
        confidence = min(max(round(confidence, 2), 0.0), 1.0)
        
        return {
            "landslide_probability": float(round(landslide_probability, 4)),
            "landslide_area_percent": float(round(landslide_area_percent, 2)),
            "rainfall_features": rain_feats,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "confidence": confidence
        }
