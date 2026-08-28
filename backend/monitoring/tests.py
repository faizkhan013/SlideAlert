import json
import numpy as np
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from monitoring.models import Zone, RainfallReading

class ZoneAPITests(APITestCase):
    def setUp(self):
        # Create a zone that is mapped for ML demo
        self.ml_zone = Zone.objects.create(
            name="Sohra (Cherrapunji)",
            state="Meghalaya",
            latitude=25.285,
            longitude=91.7362
        )
        # Create a zone that is NOT mapped for ML
        self.non_ml_zone = Zone.objects.create(
            name="Imphal",
            state="Manipur",
            latitude=24.817,
            longitude=93.937
        )
        
        # Populate readings for the ML zone so it has a valid series
        for day in range(1, 15):
            RainfallReading.objects.create(
                zone=self.ml_zone,
                date=f"2026-08-{day:02d}",
                precipitation_mm=5.0
            )

    def test_zone_list_fields_and_integrity(self):
        """Verify GET /api/zones/ returns all expected baseline and ML fields."""
        url = reverse("zone-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        
        # Find Sohri and Imphal in response
        ml_zone_data = next(z for z in data if z["id"] == self.ml_zone.id)
        non_ml_zone_data = next(z for z in data if z["id"] == self.non_ml_zone.id)
        
        # 1. Check baseline field preservation
        for key in ["id", "name", "state", "latitude", "longitude", "rainfall_24h_mm", "risk", "last_updated", "series"]:
            self.assertIn(key, ml_zone_data)
            self.assertIn(key, non_ml_zone_data)
            
        # 2. Check ML field extension
        self.assertIn("ml_enabled", ml_zone_data)
        self.assertIn("ml_prediction", ml_zone_data)
        
        self.assertTrue(ml_zone_data["ml_enabled"])
        self.assertIsNotNone(ml_zone_data["ml_prediction"])
        
        # 3. Check null safety for unmapped zones
        self.assertFalse(non_ml_zone_data["ml_enabled"])
        self.assertIsNone(non_ml_zone_data["ml_prediction"])

    def test_ml_prediction_payload_format(self):
        """Verify the nested keys in ml_prediction."""
        url = reverse("zone-detail", kwargs={"pk": self.ml_zone.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        pred = data["ml_prediction"]
        
        self.assertIsNotNone(pred)
        self.assertIn("landslide_probability", pred)
        self.assertIn("landslide_area_percent", pred)
        self.assertIn("confidence", pred)
        self.assertIn("risk_score", pred)
        self.assertIn("risk_factors", pred)
        self.assertIn("ml_risk_level", pred)
        self.assertIn("predicted_at", pred)
        
        # Validate compatibility: risk string must be low/moderate/high/critical
        self.assertIn(pred["ml_risk_level"], ["low", "moderate", "high", "critical"])

    def test_stats_and_alerts_endpoints(self):
        """Verify GET /api/stats/ and GET /api/alerts/ run without errors."""
        stats_url = reverse("stats")
        stats_res = self.client.get(stats_url)
        self.assertEqual(stats_res.status_code, status.HTTP_200_OK)
        self.assertIn("zones_monitored", stats_res.json())
        
        alerts_url = reverse("alert-list")
        alerts_res = self.client.get(alerts_url)
        self.assertEqual(alerts_res.status_code, status.HTTP_200_OK)

    def test_affected_roads_api_and_classification(self):
        """Mock Overpass elements and verify GeoJSON formatting and classifications."""
        from unittest.mock import patch
        
        # Mock Overpass API returning 3 ways:
        # Way 1: High risk (passes through landslide center 25.285, 91.7362)
        # Way 2: Moderate risk (within 1km of center)
        # Way 3: Low risk (far away, 4.5km)
        mock_elements = [
            {
                "id": 101,
                "type": "way",
                "geometry": [
                    {"lat": 25.285, "lon": 91.7362},
                    {"lat": 25.2855, "lon": 91.7367}
                ],
                "tags": {
                    "name": "Main Highway",
                    "highway": "primary"
                }
            },
            {
                "id": 102,
                "type": "way",
                "geometry": [
                    {"lat": 25.300, "lon": 91.750},
                    {"lat": 25.301, "lon": 91.751}
                ],
                "tags": {
                    "name": "Local Link",
                    "highway": "secondary"
                }
            },
            {
                "id": 103,
                "type": "way",
                "geometry": [
                    {"lat": 25.320, "lon": 91.760},
                    {"lat": 25.321, "lon": 91.761}
                ],
                "tags": {
                    "highway": "residential"
                }
            }
        ]
        
        url = reverse("zone-affected-roads", kwargs={"pk": self.ml_zone.id})
        
        with patch("requests.post") as mock_post, \
             patch("monitoring.serializers.ZoneSerializer.get_ml_prediction") as mock_ml_pred:
            
            # Mock Overpass response
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"elements": mock_elements}
            mock_post.return_value = MockResponse()
            
            # Mock overall ML risk payload
            mock_ml_pred.return_value = {
                "ml_risk_level": "high",
                "risk_score": 69,
                "landslide_probability": 0.99,
                "landslide_area_percent": 15.0,
                "confidence": 0.9,
                "risk_factors": ["High risk"],
                "predicted_at": "2026-08-28T17:17:39Z"
            }
            
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            
            self.assertEqual(data["zone_id"], self.ml_zone.id)
            self.assertTrue(data["ml_enabled"])
            self.assertIsNotNone(data["hazard_bbox"])
            
            roads = data["roads"]
            self.assertEqual(len(roads), 3)
            
            # Check high-risk road
            r_high = next(r for r in roads if r["name"] == "Main Highway")
            self.assertEqual(r_high["risk_level"], "high")
            self.assertEqual(r_high["status"], "avoid")
            self.assertEqual(r_high["geometry"]["type"], "LineString")
            self.assertEqual(r_high["geometry"]["coordinates"][0], [91.7362, 25.285])
            
            # Check moderate-risk road
            r_mod = next(r for r in roads if r["name"] == "Local Link")
            self.assertEqual(r_mod["risk_level"], "moderate")
            self.assertEqual(r_mod["status"], "caution")
            
            # Check low-risk road
            r_low = next(r for r in roads if r["name"] == "Unnamed Residential Road")
            self.assertEqual(r_low["risk_level"], "low")
            self.assertEqual(r_low["status"], "low risk")

    def test_affected_roads_unmapped_zone(self):
        """Verify unmapped zone returns empty or low-risk list without crashing."""
        from unittest.mock import patch
        url = reverse("zone-affected-roads", kwargs={"pk": self.non_ml_zone.id})
        with patch("requests.post") as mock_post:
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"elements": []}
            mock_post.return_value = MockResponse()
            
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertFalse(data["ml_enabled"])
            self.assertEqual(len(data["roads"]), 0)
