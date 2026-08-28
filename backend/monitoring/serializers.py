import os
import logging
from django.conf import settings
from django.core.cache import cache
from rest_framework import serializers

from .models import Zone
from .services import classify_risk

logger = logging.getLogger(__name__)

# Map real NER seeded zone names to representative Landslide4Sense test HDF5 images
DEMO_IMAGE_MAPPING = {
    "Sohra (Cherrapunji)": "image_241.h5",
    "Mangan": "image_1851.h5",
    "Aizawl": "image_3557.h5",
    "Haflong": "image_1561.h5",
    "Gangtok": "image_1554.h5",
}

class ZoneSerializer(serializers.ModelSerializer):
    rainfall_24h_mm = serializers.SerializerMethodField()
    risk = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()
    ml_enabled = serializers.SerializerMethodField()
    ml_prediction = serializers.SerializerMethodField()

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "state",
            "latitude",
            "longitude",
            "rainfall_24h_mm",
            "risk",
            "last_updated",
            "series",
            "ml_enabled",
            "ml_prediction",
        ]

    def _latest_reading(self, zone):
        # cached on the instance per-request to avoid repeat queries
        if not hasattr(zone, "_latest_reading_cache"):
            zone._latest_reading_cache = zone.readings.order_by("-date").first()
        return zone._latest_reading_cache

    def get_rainfall_24h_mm(self, zone):
        reading = self._latest_reading(zone)
        return reading.precipitation_mm if reading else None

    def get_risk(self, zone):
        reading = self._latest_reading(zone)
        return classify_risk(reading.precipitation_mm if reading else None)

    def get_last_updated(self, zone):
        reading = self._latest_reading(zone)
        return reading.fetched_at if reading else None

    def get_series(self, zone):
        return [
            {"date": r.date, "precipitation_mm": r.precipitation_mm}
            for r in zone.readings.order_by("date")
        ]

    def get_ml_enabled(self, zone):
        # Enable ML only in Demo/Dev mode and if a mapped HDF5 file exists
        if not getattr(settings, "SLIDEALERT_DEMO_MODE", False):
            return False
            
        matched_name = None
        for key in DEMO_IMAGE_MAPPING:
            if key.lower() in zone.name.lower() or zone.name.lower() in key.lower():
                matched_name = key
                break
                
        if not matched_name:
            return False
            
        img_name = DEMO_IMAGE_MAPPING[matched_name]
        img_path = os.path.join(settings.BASE_DIR, "..", "dataset", "Landslide4Sense", "TrainData", "img", img_name)
        return os.path.exists(img_path)

    def get_ml_prediction(self, zone):
        if not self.get_ml_enabled(zone):
            return None

        cache_key = f"ml_pred_{zone.id}"
        cached_val = cache.get(cache_key)
        if cached_val is not None:
            return cached_val

        # Retrieve 14-day rainfall series
        series = self.get_series(zone)
        if not series:
            return None

        matched_name = None
        for key in DEMO_IMAGE_MAPPING:
            if key.lower() in zone.name.lower() or zone.name.lower() in key.lower():
                matched_name = key
                break
                
        # Build path to image file
        img_name = DEMO_IMAGE_MAPPING[matched_name]
        img_path = os.path.join(settings.BASE_DIR, "..", "dataset", "Landslide4Sense", "TrainData", "img", img_name)

        try:
            # Import pipeline dynamically to ensure sys.path is initialized
            from ai_ml.inference.slidealert_predictor import get_ml_prediction as run_ml_pred
            pred_res = run_ml_pred(img_path, series)
            ml_payload = pred_res["ml_prediction"]
            
            # Cache the result for 30 minutes
            cache.set(cache_key, ml_payload, timeout=settings.RAINFALL_CACHE_MINUTES * 60)
            return ml_payload
        except Exception as e:
            logger.exception("AI/ML prediction failed for zone %s: %s", zone.name, e)
            return None
