"""
test_risk_engine.py - Unit tests for LandslideRiskEngine boundary conditions and edge cases.
"""
import sys
import unittest
import numpy as np

sys.path.append("D:/slideland")

from ai_ml.risk_model.risk_engine import LandslideRiskEngine

class TestLandslideRiskEngine(unittest.TestCase):
    def setUp(self):
        self.engine = LandslideRiskEngine()

    def test_zero_inputs(self):
        """Test with completely dry weather and zero landslide indicators."""
        res = self.engine.compute_risk(0.0, 0.0, [])
        self.assertEqual(res["risk_score"], 0)
        self.assertEqual(res["risk_level"], "low")
        self.assertEqual(res["confidence"], 0.90)
        self.assertIn("Stable terrain indices and low precipitation", res["risk_factors"])

    def test_maximum_inputs(self):
        """Test with extreme landslide area and catastrophic rainfall."""
        extreme_rain = [200.0] * 14  # 200mm daily rain
        res = self.engine.compute_risk(1.0, 100.0, extreme_rain)
        self.assertEqual(res["risk_score"], 100)
        self.assertEqual(res["risk_level"], "critical")
        self.assertEqual(res["confidence"], 0.90)
        self.assertIn("High landslide probability", res["risk_factors"])
        self.assertIn("Large predicted landslide area", res["risk_factors"])
        self.assertIn("Heavy 24-hour rainfall", res["risk_factors"])

    def test_empty_rainfall_series(self):
        """Test when rainfall series is empty or missing."""
        res = self.engine.compute_risk(0.8, 12.0, [])
        self.assertTrue(0 <= res["risk_score"] <= 100)
        self.assertIn(res["risk_level"], ["low", "moderate", "high", "critical"])
        self.assertIn("High landslide probability", res["risk_factors"])

    def test_high_rainfall_only(self):
        """Test with high rainfall but zero landslide presence indices."""
        heavy_rain = [0.0]*13 + [120.0]
        res = self.engine.compute_risk(0.0, 0.0, heavy_rain)
        self.assertTrue(res["risk_score"] > 0)
        self.assertIn("Heavy 24-hour rainfall", res["risk_factors"])
        self.assertNotIn("High landslide probability", res["risk_factors"])

    def test_high_ml_only(self):
        """Test with strong ML alerts but completely dry weather."""
        res = self.engine.compute_risk(1.0, 20.0, [0.0]*14)
        # ML counts for max 50 points, so score should be exactly 50 (when weights are 50% each)
        self.assertEqual(res["risk_score"], 50)
        self.assertEqual(res["risk_level"], "high")
        self.assertIn("High landslide probability", res["risk_factors"])
        self.assertIn("Large predicted landslide area", res["risk_factors"])
        self.assertNotIn("Heavy 24-hour rainfall", res["risk_factors"])

    def test_valid_risk_levels(self):
        """Ensure risk levels are always one of the React-compatible strings."""
        valid_levels = {"low", "moderate", "high", "critical"}
        
        # Grid search over inputs
        for prob in [0.0, 0.3, 0.5, 0.8, 1.0]:
            for area in [0.0, 2.0, 10.0, 50.0]:
                for rain in [[0.0]*14, [10.0]*14, [100.0]*14]:
                    res = self.engine.compute_risk(prob, area, rain)
                    self.assertTrue(0 <= res["risk_score"] <= 100)
                    self.assertIn(res["risk_level"], valid_levels)
                    self.assertFalse(np.isnan(res["risk_score"]))

if __name__ == "__main__":
    unittest.main()
