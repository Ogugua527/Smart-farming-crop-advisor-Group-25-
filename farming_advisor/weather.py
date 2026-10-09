import re

import requests


class WeatherLookupError(Exception):
    """Raised when a location or weather response cannot be retrieved."""


LOCATION_PATTERN = re.compile(r"^[\w\s.,'-]{2,80}$", re.UNICODE)


def validate_location(location: str) -> str:
    cleaned = location.strip()
    if not LOCATION_PATTERN.fullmatch(cleaned) or not any(char.isalpha() for char in cleaned):
        raise ValueError("Enter a valid place name, between 2 and 80 characters.")
    return cleaned


def _get_json(url: str, params: dict) -> dict:
    response = requests.get(url, params=params, timeout=12)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise WeatherLookupError("The weather service returned invalid data.")
    return payload


def get_weather(location: str) -> dict:
    """Find a location and return current conditions plus today's forecast."""
    place = validate_location(location)
    try:
        geocoding = _get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": place, "count": 1, "language": "en", "format": "json"},
        )
        matches = geocoding.get("results") or []
        if not matches:
            raise WeatherLookupError("No matching location was found. Check the spelling and try again.")
        match = matches[0]
        latitude = match.get("latitude")
        longitude = match.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise WeatherLookupError("The location service returned incomplete coordinates.")

        forecast = _get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code",
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )
        current = forecast.get("current") or {}
        daily = forecast.get("daily") or {}
        temperature = current.get("temperature_2m")
        precipitation = (daily.get("precipitation_sum") or [None])[0]
        if not isinstance(temperature, (int, float)) or not isinstance(precipitation, (int, float)):
            raise WeatherLookupError("The weather service did not return complete conditions.")

        return {
            "place": ", ".join(filter(None, [match.get("name"), match.get("admin1"), match.get("country")])),
            "temperature_c": float(temperature),
            "precipitation_mm": float(precipitation),
            "weather_code": current.get("weather_code"),
        }
    except WeatherLookupError:
        raise
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as error:
        raise WeatherLookupError("Weather information could not be retrieved. Check your connection and try again.") from error


def weather_description(code: int | None) -> str:
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Conditions unavailable")
