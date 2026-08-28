from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Zone
from .serializers import ZoneSerializer
from .services import ensure_fresh, fetch_and_cache_zone

import requests


class ZoneListView(APIView):
    """GET /api/zones/ — every monitored zone with live rainfall + computed risk."""

    def get(self, request):
        zones = list(Zone.objects.all())
        for zone in zones:
            ensure_fresh(zone)
        serializer = ZoneSerializer(zones, many=True)
        return Response(serializer.data)


class ZoneDetailView(APIView):
    """GET /api/zones/<id>/ — a single zone, including its full 14-day series."""

    def get(self, request, pk):
        zone = get_object_or_404(Zone, pk=pk)
        ensure_fresh(zone)
        serializer = ZoneSerializer(zone)
        return Response(serializer.data)


class ZoneRefreshView(APIView):
    """POST /api/zones/<id>/refresh/ — force a live re-fetch from Open-Meteo now."""

    def post(self, request, pk):
        zone = get_object_or_404(Zone, pk=pk)
        try:
            fetch_and_cache_zone(zone)
        except requests.RequestException as exc:
            return Response(
                {"error": f"Upstream fetch failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        serializer = ZoneSerializer(zone)
        return Response(serializer.data)


class AlertListView(APIView):
    """GET /api/alerts/ — zones currently above the 'low' risk tier, most severe first."""

    def get(self, request):
        zones = list(Zone.objects.all())
        for zone in zones:
            ensure_fresh(zone)
        data = ZoneSerializer(zones, many=True).data

        severity = {"critical": 0, "high": 1, "moderate": 2}
        alerts = [z for z in data if z["risk"] in severity]
        alerts.sort(key=lambda z: severity[z["risk"]])
        return Response(alerts)


class StatsView(APIView):
    """GET /api/stats/ — summary numbers for the dashboard's stat cards."""

    def get(self, request):
        zones = list(Zone.objects.all())
        for zone in zones:
            ensure_fresh(zone)
        data = ZoneSerializer(zones, many=True).data

        reporting = [z for z in data if z["rainfall_24h_mm"] is not None]
        high_or_critical = [z for z in data if z["risk"] in ("critical", "high")]
        avg_rainfall = (
            round(sum(z["rainfall_24h_mm"] for z in reporting) / len(reporting), 1)
            if reporting
            else None
        )

        return Response(
            {
                "zones_monitored": len(data),
                "states_covered": len({z["state"] for z in data}),
                "high_critical_count": len(high_or_critical),
                "avg_rainfall_24h_mm": avg_rainfall,
                "zones_reporting": len(reporting),
            }
        )
