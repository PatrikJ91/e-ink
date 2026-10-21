"""Live weather via Open-Meteo (free, no API key).

One request delivers current values + 4-day forecast. Results are cached
for 10 min; on API failure the last good data is kept, or OFFLINE
(outdoor None) if there is none yet. The layouts show that visibly,
never fake values.
"""
import json
import time
import urllib.request
from datetime import date

LAT, LON = 48.71838, 9.11792  # 70565 Dürrlewang (Stuttgart)
CACHE_TTL = 600
FORECAST_DAYS = 4  # starting today; the most any layout shows

URL = ("https://api.open-meteo.com/v1/forecast"
       "?latitude=%.5f&longitude=%.5f" % (LAT, LON) +
       "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
       "weather_code,wind_speed_10m"
       "&daily=weather_code,temperature_2m_max,temperature_2m_min"
       "&timezone=Europe%%2FBerlin&forecast_days=%d" % FORECAST_DAYS)

_CACHE = {"ts": 0.0, "data": None}
OFFLINE = {"outdoor": None, "forecast": []}


def _wmo(code):
    """WMO weather code -> (icon, german text). Icons: see GLYPHS in draw."""
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
    if code in (71, 73, 75, 77, 85, 86):
        return ("snow", "Schnee")
    return ("storm", "Gewitter")


def _fetch():
    with urllib.request.urlopen(URL, timeout=10) as resp:
        payload = json.load(resp)
    cur = payload["current"]
    daily = payload["daily"]
    icon, cond = _wmo(cur["weather_code"])
    forecast = []
    for i in range(len(daily["time"])):
        dicon, dcond = _wmo(daily["weather_code"][i])
        forecast.append({
            "date": date.fromisoformat(daily["time"][i]),
            "icon": dicon,
            "cond": dcond,
            "hi": daily["temperature_2m_max"][i],
            "lo": daily["temperature_2m_min"][i],
        })
    return {
        "outdoor": {
            "temp": cur["temperature_2m"],
            "feels": cur["apparent_temperature"],
            "wind": cur["wind_speed_10m"],
            "icon": icon,
            "cond": cond,
        },
        "forecast": forecast,
    }


def get_weather():
    """{"outdoor": dict or None, "forecast": [dict]}; cached, falls back
    to the last good data, then OFFLINE."""
    if time.time() - _CACHE["ts"] < CACHE_TTL and _CACHE["data"]:
        return _CACHE["data"]
    try:
        _CACHE["data"] = _fetch()
        _CACHE["ts"] = time.time()
    except Exception:
        if _CACHE["data"] is None:
            _CACHE["data"] = OFFLINE
        _CACHE["ts"] = time.time()  # Negativ-Caching: kein Retry-Storm
    return _CACHE["data"]


if __name__ == "__main__":
    print(json.dumps(get_weather(), indent=1, ensure_ascii=False, default=str))
