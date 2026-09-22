"""Live keyless weather skill backed by Open-Meteo."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODING_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
MAX_RESPONSE_BYTES = 2_000_000
USER_AGENT = "UniversalSkillForge-Weather/1.0 (+local portfolio project)"
CURRENT_FIELDS = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
)

WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


class WeatherError(RuntimeError):
    """Raised when live weather cannot be resolved reliably."""


def _fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise WeatherError(f"Open-Meteo request failed: {exc}") from exc
    if len(body) > MAX_RESPONSE_BYTES:
        raise WeatherError("Open-Meteo response exceeded the 2 MB safety limit")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WeatherError("Open-Meteo returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise WeatherError("Open-Meteo returned an unexpected response shape")
    if payload.get("error"):
        raise WeatherError(f"Open-Meteo rejected the request: {payload.get('reason', 'unknown reason')}")
    return payload


def _geocode(city: str, language: str) -> tuple[dict[str, Any], str]:
    url = f"{GEOCODING_ENDPOINT}?{urlencode({'name': city, 'count': 1, 'language': language, 'format': 'json'})}"
    payload = _fetch_json(url)
    results = payload.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise WeatherError(f"city was not found by Open-Meteo geocoding: {city}")
    location = results[0]
    if not isinstance(location.get("latitude"), (int, float)) or not isinstance(
        location.get("longitude"), (int, float)
    ):
        raise WeatherError("Open-Meteo geocoding result has no valid coordinates")
    return location, url


def _current_weather(location: dict[str, Any]) -> tuple[dict[str, Any], str]:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": ",".join(CURRENT_FIELDS),
        "timezone": "auto",
    }
    url = f"{FORECAST_ENDPOINT}?{urlencode(params)}"
    payload = _fetch_json(url)
    current = payload.get("current")
    if not isinstance(current, dict):
        raise WeatherError("Open-Meteo response has no current weather block")
    missing = [field for field in ("time", "temperature_2m", "weather_code") if field not in current]
    if missing:
        raise WeatherError(f"Open-Meteo current weather is missing: {', '.join(missing)}")
    return payload, url


def handle(args: dict[str, Any]) -> dict[str, Any]:
    city = str(args.get("city", "")).strip()
    language = str(args.get("language", "ru")).strip().lower()
    if not city:
        raise WeatherError("city cannot be empty")
    if len(language) != 2 or not language.isalpha() or not language.isascii():
        raise WeatherError("language must be a two-letter ISO code")

    location, geocoding_url = _geocode(city, language)
    forecast, forecast_url = _current_weather(location)
    current = forecast["current"]
    units = forecast.get("current_units", {})
    code = current["weather_code"]
    try:
        normalized_code = int(code)
    except (TypeError, ValueError) as exc:
        raise WeatherError(f"invalid WMO weather code: {code!r}") from exc

    return {
        "requested_city": city,
        "city": location.get("name", city),
        "country": location.get("country"),
        "admin1": location.get("admin1"),
        "coordinates": {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        },
        "timezone": forecast.get("timezone") or location.get("timezone"),
        "observed_at": current["time"],
        "temperature_c": current["temperature_2m"],
        "condition": WEATHER_CODES.get(normalized_code, f"WMO code {normalized_code}"),
        "current": current,
        "units": units,
        "provenance": {
            "provider": "Open-Meteo",
            "attribution": "Weather data by Open-Meteo.com",
            "provider_url": "https://open-meteo.com/",
            "geocoding_request_url": geocoding_url,
            "forecast_request_url": forecast_url,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_note": "Current conditions are based on Open-Meteo weather model data.",
        },
    }
