"""
rainfall.py - Feature extraction from Open-Meteo precipitation series data.
"""
import numpy as np

def extract_rainfall_features(precipitation_series, heavy_rain_threshold=15.6):
    """
    Computes cumulative rainfall indicators from the SlideAlert backend precipitation series.
    
    precipitation_series: Can be:
      - A list of floats representing daily rainfall in mm (ordered chronologically)
      - A list of dicts: [{'date': 'YYYY-MM-DD', 'precipitation_mm': float}]
    heavy_rain_threshold: Rainfall in mm above which a day is classified as 'heavy rain' (default: 15.6mm IMD threshold)
    """
    # 1. Parse inputs to a clean list of floats
    clean_series = []
    if isinstance(precipitation_series, list):
        for item in precipitation_series:
            if isinstance(item, dict):
                val = item.get("precipitation_mm")
                if val is not None:
                    clean_series.append(float(val))
            elif isinstance(item, (int, float)):
                clean_series.append(float(item))
            elif item is None:
                clean_series.append(0.0)
    elif isinstance(precipitation_series, (np.ndarray, list)):
        clean_series = [float(x) if x is not None else 0.0 for x in precipitation_series]

    # Handle missing/empty series safely
    if not clean_series:
        return {
            "rainfall_24h_mm": 0.0,
            "rainfall_3d_mm": 0.0,
            "rainfall_7d_mm": 0.0,
            "rainfall_14d_mm": 0.0,
            "max_rainfall_14d_mm": 0.0,
            "mean_rainfall_14d_mm": 0.0,
            "heavy_rain_days": 0
        }

    # 2. Extract values based on chronologically sorted series (latest element = most recent day)
    series_len = len(clean_series)
    
    rainfall_24h = clean_series[-1]
    rainfall_3d = sum(clean_series[-3:]) if series_len >= 3 else sum(clean_series)
    rainfall_7d = sum(clean_series[-7:]) if series_len >= 7 else sum(clean_series)
    rainfall_14d = sum(clean_series[-14:]) if series_len >= 14 else sum(clean_series)
    
    max_rainfall_14d = max(clean_series)
    mean_rainfall_14d = sum(clean_series) / len(clean_series)
    
    # Calculate heavy rain days (exceeding configurable threshold)
    heavy_rain_days = sum(1 for x in clean_series if x >= heavy_rain_threshold)
    
    return {
        "rainfall_24h_mm": float(round(rainfall_24h, 2)),
        "rainfall_3d_mm": float(round(rainfall_3d, 2)),
        "rainfall_7d_mm": float(round(rainfall_7d, 2)),
        "rainfall_14d_mm": float(round(rainfall_14d, 2)),
        "max_rainfall_14d_mm": float(round(max_rainfall_14d, 2)),
        "mean_rainfall_14d_mm": float(round(mean_rainfall_14d, 2)),
        "heavy_rain_days": int(heavy_rain_days)
    }
