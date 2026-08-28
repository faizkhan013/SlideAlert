from rest_framework import serializers

from .models import Zone
from .services import classify_risk


class ZoneSerializer(serializers.ModelSerializer):
    rainfall_24h_mm = serializers.SerializerMethodField()
    risk = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()

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
