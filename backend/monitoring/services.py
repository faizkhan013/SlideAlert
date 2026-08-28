"""
Live rainfall data + risk classification.

This module is the one place that talks to Open-Meteo and the one place
that decides what "risk" means. The API views and the admin both go
through here, so there's a single source of truth — no risk numbers are
invented anywhere else in the backend.
"""

import logging

import requests
from django.conf import settings
from django.utils import timezone

from .models import RainfallReading, Zone

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_PAST_DAYS = 14


def classify_risk(precipitation_mm):
    """
    Map a 24h rainfall figure to a risk tier using IMD's rainfall
    intensity classification:
      Low            < 15.6 mm
      Moderate    15.6 – 64.4 mm
      High        64.5 – 115.5 mm
      Critical      > 115.5 mm

    This is rainfall-intensity-only. It is not a full landslide
    susceptibility model — terrain slope, soil type, and historical
    incident data aren't factored in yet (see README).
    """
    if precipitation_mm is None:
        return "unknown"
    if precipitation_mm > 115.5:
        return "critical"
    if precipitation_mm >= 64.5:
        return "high"
    if precipitation_mm >= 15.6:
        return "moderate"
    return "low"


def fetch_and_cache_zone(zone: Zone, past_days: int = DEFAULT_PAST_DAYS):
    """
    Pull live daily precipitation for a zone from Open-Meteo and upsert
    it into RainfallReading. Raises on network/HTTP failure — callers
    decide whether to fall back to cached data or surface the error.
    """
    params = {
        "latitude": zone.latitude,
        "longitude": zone.longitude,
        "daily": "precipitation_sum",
        "past_days": past_days,
        "forecast_days": 0,
        "timezone": "auto",
    }
    response = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    dates = payload["daily"]["time"]
    values = payload["daily"]["precipitation_sum"]

    readings = []
    for day, value in zip(dates, values):
        reading, _ = RainfallReading.objects.update_or_create(
            zone=zone, date=day, defaults={"precipitation_mm": value}
        )
        readings.append(reading)
    return readings


def is_stale(zone: Zone) -> bool:
    """Whether the zone's cached readings are missing or old enough to refresh."""
    latest = zone.readings.order_by("-date").first()
    if latest is None:
        return True
    max_age = timezone.timedelta(minutes=settings.RAINFALL_CACHE_MINUTES)
    return timezone.now() - latest.fetched_at > max_age


def ensure_fresh(zone: Zone):
    """
    Refresh a zone's rainfall cache if it's stale. Swallows upstream
    errors on purpose: if Open-Meteo is briefly unreachable, we keep
    serving whatever's cached rather than breaking the dashboard. If
    there's no cache at all yet, the zone will simply report as
    'unknown' until a fetch succeeds.
    """
    if not is_stale(zone):
        return
    try:
        fetch_and_cache_zone(zone)
    except (requests.RequestException, KeyError, ValueError) as exc:
        logger.warning("Rainfall fetch failed for zone %s: %s", zone, exc)
