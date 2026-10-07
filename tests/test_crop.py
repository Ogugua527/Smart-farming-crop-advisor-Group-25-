import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import crop  # noqa: E402


class TestCropSelection(unittest.TestCase):
    def test_supported_list(self):
        self.assertEqual(crop.get_supported_crops(), ["cassava", "maize", "rice", "tomato"])

    def test_normalize_valid(self):
        cases = {"maize": "maize", " MAIZE ": "maize", "Corn": "maize",
                 "tomatoes": "tomato", "Tomato!": "tomato", "manioc": "cassava",
                 "paddy rice": "rice", "  rice  ": "rice"}
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(crop.normalize_crop_name(raw), expected)

    def test_normalize_invalid(self):
        for raw in ["yam", "", "   ", "123", None, 42, "maizee"]:
            with self.subTest(raw=raw):
                self.assertIsNone(crop.normalize_crop_name(raw))
                self.assertFalse(crop.is_supported_crop(raw))

    def test_validate_raises_friendly_message(self):
        with self.assertRaises(crop.UnsupportedCropError) as ctx:
            crop.validate_crop("yam")
        self.assertIn("Maize", str(ctx.exception))
        self.assertIn("yam", str(ctx.exception))


class TestCropData(unittest.TestCase):
    def test_json_serialisable_and_sane(self):
        for name in crop.get_supported_crops():
            with self.subTest(crop=name):
                data = crop.get_crop_data(name)
                self.assertEqual(json.loads(json.dumps(data)), data)
                self.assertLess(data["temp_min_c"], data["temp_max_c"])
                self.assertLess(data["rainfall_min_mm"], data["rainfall_max_mm"])
                self.assertLess(data["growth_days_min"], data["growth_days_max"])
                self.assertTrue(data["common_pests"] and data["common_diseases"])

    def test_prompt_context(self):
        text = crop.get_crop_prompt_context("rice")
        for part in ("Rice", "Oryza sativa", "mm"):
            self.assertIn(part, text)


class TestWeatherSuitability(unittest.TestCase):
    def test_too_hot(self):
        r = crop.check_weather_suitability("tomato", {"temperature_c": 40})
        self.assertIs(r["suitable"], False)
        self.assertTrue(r["warnings"])

    def test_good_conditions(self):
        r = crop.check_weather_suitability("maize", {"temperature_c": 26, "rainfall_mm": 5})
        self.assertIs(r["suitable"], True)

    def test_heavy_rain_warning(self):
        r = crop.check_weather_suitability("maize", {"rainfall_mm": 150})
        self.assertTrue(any("waterlog" in w for w in r["warnings"]))

    def test_missing_or_bad_input_does_not_crash(self):
        self.assertIsNone(crop.check_weather_suitability("rice", {})["suitable"])
        self.assertIsNone(crop.check_weather_suitability("rice", None)["suitable"])


if __name__ == "__main__":
    unittest.main()