"""Shared drawing helpers for the layouts: fonts, icons, text fitting.

Kept separate from render.py so the layout modules and data sources can
import it without circular imports.
"""
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import ImageFont

BASE_DIR = Path(__file__).resolve().parent

W, H = 800, 480

# Display stands in Berlin: explicit timezone, independent of the Pi's
# system timezone (which may be e.g. London/BST).
TZ = ZoneInfo("Europe/Berlin")

# No locale dependency: German names hardcoded (Pi locale may be C/POSIX).
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"]
WEEKDAYS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# Weather Icons by Erik Flowers (SIL Open Font License 1.1),
# bundled in assets/. Day variants match the reference style.
GLYPHS = {
    # Sun-free variants so the icon matches the text (no sun in "Regen").
    "sun": "",      # day-sunny
    "partly": "",   # day-cloudy
    "cloud": "",    # cloud
    "fog": "",      # fog
    "drizzle": "",  # showers (no sun)
    "rain": "",     # rain (no sun)
    "snow": "",     # snow (no sun)
    "storm": "",    # storm-showers (no sun)
}

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans{bold}.ttf",  # Raspberry Pi OS
    "/System/Library/Fonts/Helvetica.ttc",  # macOS dev machine (face 1 = bold)
    "DejaVuSans{bold}.ttf",
]


@lru_cache(maxsize=None)  # fonts never change at runtime
def font(size, bold=False):
    for pattern in _FONT_PATHS:
        path = pattern.format(bold="-Bold" if bold and "DejaVu" in pattern else "")
        index = 1 if bold and path.endswith(".ttc") else 0
        try:
            return ImageFont.truetype(path, size, index=index)
        except Exception:
            continue
    return ImageFont.load_default()


@lru_cache(maxsize=None)
def weather_font(size):
    for path in (BASE_DIR / "assets" / "weather-icons.ttf",
                 Path("/usr/share/fonts/truetype/weather-icons/weather-icons.ttf")):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    raise RuntimeError("weather icon font not found in assets/")


def icon(d, key, x, y, size, top=False):
    """Draw a weather glyph with its left edge at x.

    top=True also aligns the glyph's visible top with y (otherwise y is
    the font's text origin, like a normal d.text call).
    """
    f = weather_font(size)
    glyph = GLYPHS.get(key, GLYPHS["cloud"])
    bb = d.textbbox((0, 0), glyph, font=f)
    d.text((x - bb[0], y - (bb[1] if top else 0)), glyph, font=f, fill=0)


def fit(d, text, max_w, start, bold=False):
    """Largest font (from start, step 2) that fits text into max_w."""
    size = start
    while size > 10:
        f = font(size, bold)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(10, bold)


def ellipsize(d, text, f, max_w):
    """Shorten text with '…' until it fits into max_w (font stays the same)."""
    if d.textlength(text, font=f) <= max_w:
        return text
    while text and d.textlength(text + "…", font=f) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


def decimal(value, unit=""):
    """12.43 -> '12,4' + unit; None (no data) -> '–,–' + unit."""
    if value is None:
        return "–,–" + unit
    return ("%.1f" % value).replace(".", ",") + unit
