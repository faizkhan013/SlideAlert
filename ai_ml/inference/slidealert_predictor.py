"""
slidealert_predictor.py - Production-style high-level integration adapter for SlideAlert backend.
"""
import os
import sys
from datetime import datetime, timezone

# Ensure slideland root is in search path
sys.path.append("D:/slideland")

from ai_ml.inference.predictor import SlideAlertPredictor
from ai_ml.risk_model.risk_engine import LandslideRiskEngine

class SlideAlertMLAdapter:
    """
    Adapter class called directly by Django Views / Serializers.
    Integrates the spatial U-Net predictions with temporal rainfall features.
    """
    def __init__(self, model_path=None):
        self.predictor = SlideAlertPredictor(model_path=model_path)
        self.risk_engine = LandslideRiskEngine()

    def evaluate_zone(self, image_numpy_or_path, rainfall_series, threshold=0.5):
        """
        Runs the full SlideAlert AI/ML pipeline for a specific zone.
        
        image_numpy_or_path: Path to HDF5 file or raw image numpy array.
        rainfall_series: Rainfall series in SlideAlert format: [{'date': '...', 'precipitation_mm': ...}]
        threshold: Configurable segmentation threshold (default: 0.5)
        """
        # Step 1: Spatial Landslide Segmentation
        seg_res = self.predictor.predict_image(image_numpy_or_path, threshold=threshold)
        
        # Step 2: Risk Scoring & Factor Assessment
        risk_res = self.risk_engine.compute_risk(
            landslide_probability=seg_res["landslide_probability"],
            landslide_area_percent=seg_res["landslide_area_percent"],
            rainfall_series=rainfall_series
        )
        
        # Step 3: Format payload for Django backward-compatible API
        predicted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        return {
            "ml_enabled": True,
            "ml_prediction": {
                "landslide_probability": float(round(risk_res["landslide_probability"], 4)),
                "landslide_area_percent": float(round(risk_res["landslide_area_percent"], 2)),
                "confidence": float(round(risk_res["confidence"], 2)),
                "risk_score": int(risk_res["risk_score"]),
                "risk_factors": risk_res["risk_factors"],
                "ml_risk_level": risk_res["risk_level"],
                "predicted_at": predicted_at
            }
        }

# Global helper function for simple function call integration
_ADAPTER_INSTANCE = None

def get_ml_prediction(image_path_or_array, rainfall_series, threshold=0.5):
    """
    Global helper function to easily run predictions from Django backend.
    Caches the adapter instance to prevent repeating model weight loads on every call.
    """
    global _ADAPTER_INSTANCE
    if _ADAPTER_INSTANCE is None:
        _ADAPTER_INSTANCE = SlideAlertMLAdapter()
    return _ADAPTER_INSTANCE.evaluate_zone(image_path_or_array, rainfall_series, threshold=threshold)
