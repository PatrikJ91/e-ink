"""Render the 800x480 1-bit dashboard image in the configured layout.

Layouts (switch with the environment variable EINK_LAYOUT, read once at
server start):
  bands    three full-width bands: temperatures, forecast, events (default)
  classic  the V1 four-quarter layout (display/mockup_dashboard_v1.png)

Data comes in as a plain dict of raw values (numbers, dates; None = no
data); each layout does its own formatting.
"""
import io
import os
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

import layout_bands
import layout_classic
from draw import H, TZ, W

LAYOUTS = {"bands": layout_bands.draw, "classic": layout_classic.draw}
DEFAULT_LAYOUT = "bands"

# Fixed threshold instead of Floyd-Steinberg dithering: our content is
# already black-on-white, so a threshold keeps edges crisp without
# scattered pixels around fine icon strokes.
BLACK_THRESHOLD = 160


def _configured_layout():
    name = (os.environ.get("EINK_LAYOUT") or DEFAULT_LAYOUT).strip().lower()
    if name not in LAYOUTS:
        # A typo must not take the display down: warn into server.log
        # and keep going with the default.
        print("unknown EINK_LAYOUT=%r, using %r (known: %s)"
              % (name, DEFAULT_LAYOUT, ", ".join(sorted(LAYOUTS))), flush=True)
        return DEFAULT_LAYOUT
    return name


LAYOUT = _configured_layout()


def sample_data(today):
    """Plausible demo data for previews (python3 render.py)."""
    day = lambda n: today + timedelta(days=n)
    return {
        "indoor": {"label": "Wohnzimmer", "temp": 21.5, "hum": 45, "batt": 87},
        "outdoor": {"temp": 12.4, "feels": 10.1, "wind": 14.2,
                    "icon": "partly", "cond": "Wechselhaft"},
        "forecast": [
            {"date": day(0), "icon": "partly", "cond": "Wechselhaft", "hi": 13.2, "lo": 8.6},
            {"date": day(1), "icon": "rain", "cond": "Regen", "hi": 12.8, "lo": 7.9},
            {"date": day(2), "icon": "cloud", "cond": "Bedeckt", "hi": 11.1, "lo": 6.3},
            {"date": day(3), "icon": "sun", "cond": "Klar", "hi": 14.4, "lo": 4.8},
        ],
        "events": [
            {"date": day(0), "time": "18:30", "title": "Volleyball",
             "location": "Sporthalle Dürrlewang"},
            {"date": day(1), "time": None, "title": "Papiertonne rausstellen",
             "location": None},
            {"date": day(1), "time": "09:00", "title": "Zahnarzt Dr. Weber",
             "location": "Vaihingen, Hauptstr. 12"},
            {"date": day(1), "time": "19:00", "title": "Abendessen mit Lena und Tom",
             "location": None},
        ],
    }


def render(data=None, now=None, layout=None):
    """Draw the dashboard, return a 1-bit PIL image."""
    now = now or datetime.now(TZ)
    data = data or sample_data(now.date())
    # Stale forecast (API down for a while) must not show past days.
    data = dict(data, forecast=[f for f in data["forecast"] if f["date"] >= now.date()])
    img = Image.new("L", (W, H), 255)
    LAYOUTS[layout or LAYOUT](ImageDraw.Draw(img), data, now)
    return img.point(lambda p: 255 if p >= BLACK_THRESHOLD else 0, mode="1")


def render_raw(img=None):
    """48.000 bytes, row-major top-down, MSB first, 1 = black.

    Matches GxEPD2/Adafruit drawBitmap(buffer, w, h, GxEPD_BLACK):
    a set bit draws a black pixel.
    """
    img = img or render()
    return bytes(b ^ 0xFF for b in img.tobytes())


def render_bmp(img=None):
    img = img or render()
    buf = io.BytesIO()
    img.save(buf, "BMP")
    return buf.getvalue()


if __name__ == "__main__":
    render().save("preview.png")
    print("saved preview.png (layout: %s)" % LAYOUT)
