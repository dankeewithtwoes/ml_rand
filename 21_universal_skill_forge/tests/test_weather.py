"""Contract tests for the live weather skill; HTTP is mocked."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "weather_handler_under_test", ROOT / "skills" / "weather" / "handler.py"
)
weather = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(weather)


class Response:
    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body


class WeatherSkillTests(unittest.TestCase):
    @patch.object(weather, "urlopen")
    def test_values_come_from_open_meteo_with_provenance(self, mocked_open):
        mocked_open.side_effect = [
            Response({"results": [{
                "name": "Волгоград",
                "country": "Россия",
                "admin1": "Волгоградская область",
                "latitude": 48.7194,
                "longitude": 44.5018,
            }]}),
            Response({
                "timezone": "Europe/Volgograd",
                "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"},
                "current": {
                    "time": "2026-07-19T12:00",
                    "temperature_2m": 31.7,
                    "relative_humidity_2m": 27,
                    "apparent_temperature": 30.1,
                    "precipitation": 0,
                    "weather_code": 2,
                    "cloud_cover": 36,
                    "surface_pressure": 1002.4,
                    "wind_speed_10m": 14.2,
                    "wind_direction_10m": 75,
                },
            }),
        ]
        result = weather.handle({"city": "Волгоград", "language": "ru"})
        self.assertEqual(31.7, result["temperature_c"])
        self.assertEqual("partly cloudy", result["condition"])
        self.assertEqual("Open-Meteo", result["provenance"]["provider"])
        self.assertIn("Weather data by Open-Meteo.com", result["provenance"]["attribution"])
        self.assertEqual("Europe/Volgograd", result["timezone"])
        geocode_request = mocked_open.call_args_list[0].args[0]
        forecast_request = mocked_open.call_args_list[1].args[0]
        self.assertIn("name=%D0%92%D0%BE%D0%BB%D0%B3%D0%BE%D0%B3%D1%80%D0%B0%D0%B4", geocode_request.full_url)
        self.assertIn("temperature_2m", forecast_request.full_url)

    @patch.object(weather, "urlopen", return_value=Response({"results": []}))
    def test_unknown_city_is_explicit(self, _mocked_open):
        with self.assertRaisesRegex(weather.WeatherError, "city was not found"):
            weather.handle({"city": "definitely-not-a-city"})

    @patch.object(weather, "urlopen", side_effect=URLError("offline"))
    def test_network_failure_is_explicit(self, _mocked_open):
        with self.assertRaisesRegex(weather.WeatherError, "request failed"):
            weather.handle({"city": "Moscow"})

    def test_empty_city_is_rejected_before_network(self):
        with self.assertRaisesRegex(weather.WeatherError, "cannot be empty"):
            weather.handle({"city": "   "})


if __name__ == "__main__":
    unittest.main()
