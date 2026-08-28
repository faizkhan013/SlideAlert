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


class ZoneAffectedRoadsView(APIView):
    """GET /api/zones/<id>/affected-roads/ — returns road segments and their ML risk level."""

    def get(self, request, pk):
        import os
        import math
        import logging
        import numpy as np
        from django.core.cache import cache
        from .serializers import DEMO_IMAGE_MAPPING
        from django.conf import settings
        from ai_ml.inference.predictor import SlideAlertPredictor

        logger = logging.getLogger(__name__)
        zone = get_object_or_404(Zone, pk=pk)

        # 1. Check if ML is enabled (robust substring match)
        demo_mode = getattr(settings, "SLIDEALERT_DEMO_MODE", False)
        matched_name = None
        for key in DEMO_IMAGE_MAPPING:
            if key.lower() in zone.name.lower() or zone.name.lower() in key.lower():
                matched_name = key
                break
        ml_enabled = demo_mode and (matched_name is not None)

        roads_list = []
        
        # Hazard bounding box bounds for visualization helper
        delta_lat = 0.00575
        cos_lat = math.cos(math.radians(zone.latitude))
        delta_lon = 0.00575 / cos_lat
        
        hazard_bbox = {
            "lat_min": zone.latitude - delta_lat,
            "lat_max": zone.latitude + delta_lat,
            "lon_min": zone.longitude - delta_lon,
            "lon_max": zone.longitude + delta_lon
        }

        if ml_enabled:
            # 2. Retrieve U-Net predictions
            img_name = DEMO_IMAGE_MAPPING[matched_name]
            img_path = os.path.join(settings.BASE_DIR, "..", "dataset", "Landslide4Sense", "TrainData", "img", img_name)
            
            try:
                predictor = SlideAlertPredictor()
                res = predictor.predict_image(img_path, threshold=0.5)
                binary_mask = res["binary_mask"]  # shape (128, 128), np.uint8
            except Exception as e:
                logger.exception("Failed to run U-Net inference for affected roads: %s", e)
                binary_mask = None
        else:
            binary_mask = None

        # 3. Retrieve road network within 5 km from cache or Overpass API
        cache_key = f"osm_roads_{zone.id}"
        elements = cache.get(cache_key)
        
        if elements is None:
            url = "https://overpass-api.de/api/interpreter"
            query = f'[out:json];way(around:5000, {zone.latitude}, {zone.longitude})[highway~"^(motorway|trunk|primary|secondary|tertiary)$"];out geom;'
            headers = {'User-Agent': 'SlideAlert/1.0 (manis.prusty@sih.gov.in) python-requests/2.34.0'}
            try:
                response = requests.post(url, data={'data': query}, headers=headers, timeout=10) # 10s timeout
                if response.status_code == 200:
                    elements = response.json().get("elements", [])
                    cache.set(cache_key, elements, timeout=24 * 3600)
                else:
                    elements = []
                    logger.warning("Overpass API returned status code %s", response.status_code)
            except Exception as e:
                logger.exception("Failed to query Overpass API: %s", e)
                elements = []
                
        if not elements and ml_enabled:
            # Fallback local road network for demo safety when Overpass API is offline or timeout
            elements = [
                {
                    "id": 201,
                    "type": "way",
                    "geometry": [
                        {"lat": zone.latitude - 0.03, "lon": zone.longitude - 0.01},
                        {"lat": zone.latitude - 0.01, "lon": zone.longitude - 0.005},
                        {"lat": zone.latitude, "lon": zone.longitude},
                        {"lat": zone.latitude + 0.02, "lon": zone.longitude + 0.01},
                        {"lat": zone.latitude + 0.04, "lon": zone.longitude + 0.02}
                    ],
                    "tags": {
                        "name": f"{zone.name}–Shillong Road",
                        "highway": "primary"
                    }
                },
                {
                    "id": 202,
                    "type": "way",
                    "geometry": [
                        {"lat": zone.latitude - 0.015, "lon": zone.longitude - 0.02},
                        {"lat": zone.latitude - 0.004, "lon": zone.longitude - 0.004},
                        {"lat": zone.latitude + 0.004, "lon": zone.longitude + 0.004},
                        {"lat": zone.latitude + 0.015, "lon": zone.longitude + 0.02}
                    ],
                    "tags": {
                        "name": f"{zone.name}–Jowai Road",
                        "highway": "secondary"
                    }
                },
                {
                    "id": 203,
                    "type": "way",
                    "geometry": [
                        {"lat": zone.latitude - 0.02, "lon": zone.longitude + 0.02},
                        {"lat": zone.latitude - 0.008, "lon": zone.longitude + 0.008},
                        {"lat": zone.latitude + 0.008, "lon": zone.longitude - 0.008},
                        {"lat": zone.latitude + 0.02, "lon": zone.longitude - 0.02}
                    ],
                    "tags": {
                        "name": f"{zone.name}–Mawsmai Road",
                        "highway": "tertiary"
                    }
                },
                {
                    "id": 204,
                    "type": "way",
                    "geometry": [
                        {"lat": zone.latitude + 0.03, "lon": zone.longitude - 0.03},
                        {"lat": zone.latitude + 0.02, "lon": zone.longitude - 0.02},
                        {"lat": zone.latitude + 0.018, "lon": zone.longitude - 0.018},
                        {"lat": zone.latitude + 0.025, "lon": zone.longitude - 0.025}
                    ],
                    "tags": {
                        "name": f"{zone.name}–Mawphlang Road",
                        "highway": "secondary"
                    }
                }
            ]
        
        # 4. Classify each road segment (DEMO-mode spatial approximation using model output and distance)
        from .serializers import ZoneSerializer
        serializer = ZoneSerializer()
        ml_pred = serializer.get_ml_prediction(zone)
        
        if ml_pred:
            zone_risk = ml_pred.get("ml_risk_level", "low").lower()
        else:
            zone_risk = "low"

        for elem in elements:
            geometry = elem.get("geometry")
            if not geometry or len(geometry) < 2:
                continue

            tags = elem.get("tags", {})
            highway_type = tags.get("highway", "road")
            road_name = tags.get("name", f"Unnamed {highway_type.capitalize()} Road")
            
            # Default classification: low risk
            risk_level = "low"
            status_desc = "low risk"
            min_dist_to_center = 999999.0
            
            # Extract coordinates for GeoJSON
            coords = []
            
            for pt in geometry:
                pt_lat = pt["lat"]
                pt_lon = pt["lon"]
                coords.append([pt_lon, pt_lat]) # GeoJSON uses [longitude, latitude]
                
                # Compute distance to center (Haversine formula approximation for short distances)
                d_lat = math.radians(pt_lat - zone.latitude)
                d_lon = math.radians(pt_lon - zone.longitude)
                a = math.sin(d_lat/2)**2 + math.cos(math.radians(zone.latitude)) * math.cos(math.radians(pt_lat)) * math.sin(d_lon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                dist = 6371.0 * c # distance in km
                if dist < min_dist_to_center:
                    min_dist_to_center = dist
            
            # DEMO-mode spatial approximation rules:
            # - If zone overall risk is high/critical:
            #   - Roads within 1.0 km -> HIGH / avoid (RED)
            #   - Roads between 1.0 km and 2.5 km -> MODERATE / caution (ORANGE)
            #   - Roads beyond 2.5 km -> LOW / low risk (GREEN)
            # - If zone overall risk is moderate:
            #   - Roads within 2.0 km -> MODERATE / caution (ORANGE)
            #   - Roads beyond 2.0 km -> LOW / low risk (GREEN)
            # - If zone overall risk is low:
            #   - All roads are LOW / low risk (GREEN)
            if ml_enabled:
                if zone_risk in ["high", "critical"]:
                    if min_dist_to_center <= 1.0:
                        risk_level = "high"
                        status_desc = "avoid"
                    elif min_dist_to_center <= 2.5:
                        risk_level = "moderate"
                        status_desc = "caution"
                elif zone_risk == "moderate":
                    if min_dist_to_center <= 2.0:
                        risk_level = "moderate"
                        status_desc = "caution"

            roads_list.append({
                "name": road_name,
                "risk_level": risk_level,
                "status": status_desc,
                "distance_km": round(min_dist_to_center, 2),
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })

        # Sort roads: High risk first, then moderate, then low
        sort_order = {"high": 0, "moderate": 1, "low": 2}
        roads_list.sort(key=lambda r: (sort_order[r["risk_level"]], r["distance_km"]))

        return Response({
            "zone_id": zone.id,
            "zone_name": zone.name,
            "radius_km": 5,
            "ml_enabled": ml_enabled,
            "hazard_bbox": hazard_bbox if ml_enabled else None,
            "roads": roads_list
        })
