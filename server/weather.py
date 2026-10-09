"""Live weather via Open-Meteo (free, no API key).

One request delivers current values + 3-day forecast. Results are cached
for 10 min; on API failure the last good data (or MOCK) is served so the
display always has something to show.
"""
import json
import time
import urllib.request
from datetime import date

from render import MOCK

LAT, LON = 48.71838, 9.11792  # 70565 Dürrlewang (Stuttgart)
LOCATION = "DÜRRLEWANG · 70565"
CACHE_TTL = 600

URL = ("https://api.open-meteo.com/v1/forecast"
       "?latitude=%.5f&longitude=%.5f" % (LAT, LON) +
       "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
       "weather_code,wind_speed_10m"
       "&daily=weather_code,temperature_2m_max,temperature_2m_min"
       "&timezone=Europe%2FBerlin&forecast_days=3")

_CACHE = {"ts": 0.0, "data": None}
WEEKDAYS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _wmo(code):
    """WMO weather code -> (icon, german text). Icons: see GLYPHS in render."""
    if code == 0:
        return ("sun", "Klar")
    if code in (1, 2):
        return ("partly", "Meist klar" if code == 1 else "Wechselhaft")
    if code == 3:
        return ("cloud", "Bedeckt")
    if code in (45, 48):
        return ("fog", "Nebel")
    if code in (51, 53, 55, 56, 57):
        return ("drizzle", "Niesel")
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return ("rain", "Regen")
    if code in (71, 73, 75, 77):
        return ("snow", "Schnee")
    return ("storm", "Gewitter")


def _celsius(value):
    return ("%.1f" % value).replace(".", ",") + " °C"


def _fetch():
    with urllib.request.urlopen(URL, timeout=10) as resp:
        payload = json.load(resp)
    cur = payload["current"]
    daily = payload["daily"]
    icon, cond = _wmo(cur["weather_code"])
    forecast = []
    for i in range(3):
        dicon, dcond = _wmo(daily["weather_code"][i])
        day = date.fromisoformat(daily["time"][i])
        forecast.append({
            "day": WEEKDAYS_SHORT[day.weekday()],
            "icon": dicon,
            "temps": "%d°/%d°" % (round(daily["temperature_2m_max"][i]),
                                  round(daily["temperature_2m_min"][i])),
            "cond": dcond,
        })
    return {
        "location": LOCATION,
        "indoor": MOCK["indoor"],  # sensor comes later
        "outdoor": {
            "label": "",
            "temp": _celsius(cur["temperature_2m"]),
            "sub": "%s · gefühlt %s · %.0f km/h" % (
                cond, _celsius(cur["apparent_temperature"]),
                cur["wind_speed_10m"]),
        },
        "forecast": forecast,
        "events": MOCK["events"],  # calendar comes later
    }


def get_weather():
    """Live data with cache; falls back to last good data, then MOCK."""
    if time.time() - _CACHE["ts"] < CACHE_TTL and _CACHE["data"]:
        return _CACHE["data"]
    try:
        _CACHE["data"] = _fetch()
        _CACHE["ts"] = time.time()
    except Exception:
        if _CACHE["data"] is None:
            fallback = dict(MOCK)
            fallback["location"] = LOCATION
            _CACHE["data"] = fallback
    return _CACHE["data"]


if __name__ == "__main__":
    print(json.dumps(get_weather(), indent=1, ensure_ascii=False))
