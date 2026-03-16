"""
weather_summary.py
Fetches current NYC weather from Open-Meteo (free, no API key needed).
"""

import json
import urllib.request

# NYC coordinates
_LAT = 40.7128
_LON = -74.0060
_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={_LAT}&longitude={_LON}"
    f"&current=temperature_2m,weathercode,precipitation_probability"
    f"&temperature_unit=fahrenheit"
    f"&timezone=America%2FNew_York"
)

_WEATHER_CODES = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Foggy 🌫️",
    48: "Foggy 🌫️",
    51: "Light drizzle 🌦️",
    53: "Drizzle 🌦️",
    55: "Heavy drizzle 🌧️",
    61: "Light rain 🌧️",
    63: "Rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Light snow 🌨️",
    73: "Snow 🌨️",
    75: "Heavy snow ❄️",
    80: "Rain showers 🌦️",
    81: "Rain showers 🌧️",
    82: "Violent showers ⛈️",
    95: "Thunderstorm ⛈️",
    96: "Thunderstorm ⛈️",
    99: "Thunderstorm ⛈️",
}


def get_weather():
    """
    Return dict with temp (°F), description, and precipitation probability.
    Returns None on error.
    """
    try:
        with urllib.request.urlopen(_URL, timeout=5) as resp:
            data = json.loads(resp.read())
        current = data["current"]
        code = current.get("weathercode", 0)
        return {
            "temp": round(current["temperature_2m"]),
            "description": _WEATHER_CODES.get(code, "Unknown"),
            "precip": current.get("precipitation_probability", 0),
        }
    except Exception:
        return None
