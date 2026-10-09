"""Render the 800x480 1-bit dashboard image (V1 layout).

Layout matches display/mockup_dashboard_v1.png. Data comes in as a plain
dict so mocked data can later be replaced 1:1 by real sensor/API/calendar
sources without touching the drawing code.
"""
import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent

# Weather Icons by Erik Flowers (SIL Open Font License 1.1),
# bundled in assets/. Day variants match the reference style.
GLYPHS = {
    # Sun-free variants so the icon matches the text (no sun in "Regen").
    "sun": "\uf00d",      # day-sunny
    "partly": "\uf002",   # day-cloudy
    "cloud": "\uf041",    # cloud
    "fog": "\uf014",      # fog
    "drizzle": "\uf01a",  # showers (no sun)
    "rain": "\uf019",     # rain (no sun)
    "snow": "\uf01b",     # snow (no sun)
    "storm": "\uf01e",    # storm-showers (no sun)
}


def _weather_font(size):
    for path in (BASE_DIR / "assets" / "weather-icons.ttf",
                 Path("/usr/share/fonts/truetype/weather-icons/weather-icons.ttf")):
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    raise RuntimeError("weather icon font not found in assets/")

W, H = 800, 480
M = 16
DIV_Y = 268  # horizontal dividers left and right share this height
# Fixed threshold instead of Floyd-Steinberg dithering: our content is
# already black-on-white, so a threshold keeps edges crisp without
# scattered pixels around fine icon strokes.
BLACK_THRESHOLD = 160

# Display stands in Berlin: explicit timezone, independent of the Pi's
# system timezone (which may be e.g. London/BST).
TZ = ZoneInfo("Europe/Berlin")

# No locale dependency: German names hardcoded (Pi locale may be C/POSIX).
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"]
MONTHS = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]

MOCK = {
    "location": "DÜRRLEWANG · 70565",
    "indoor": {"label": "Wohnzimmer", "temp": "21,5 °C", "humidity": "Luftfeuchte 45 %"},
    "outdoor": {"label": "Berlin", "temp": "14,2 °C", "sub": "Bewölkt · gefühlt 12 °C"},
    "forecast": [
        {"day": "Fr", "icon": "sun", "temps": "15°/9°", "cond": "Sonne"},
        {"day": "Sa", "icon": "cloud", "temps": "13°/8°", "cond": "Wolken"},
        {"day": "So", "icon": "rain", "temps": "12°/7°", "cond": "Regen"},
    ],
    "events": [
        ("14:00", "Zahnarzt"),
        ("16:30", "Anruf Mama"),
        ("19:00", "Sport"),
        ("Mo 09:00", "Standup"),
    ],
}

_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans{bold}.ttf",  # Raspberry Pi OS
    "/System/Library/Fonts/Helvetica.ttc",  # macOS dev machine
    "DejaVuSans{bold}.ttf",
]


def _font(size, bold=False):
    for pattern in _FONT_PATHS:
        path = pattern.format(bold="-Bold" if bold and "DejaVu" in pattern else "")
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render(data=None, now=None):
    """Draw the dashboard, return a 1-bit PIL image."""
    data = data or MOCK
    now = now or datetime.now(TZ)
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)

    F_title = _font(34, True)
    F_meta = _font(22)
    F_label = _font(22, True)
    F_big = _font(88, True)
    F_sub = _font(22)
    F_day = _font(24, True)
    F_body = _font(24)
    F_small = _font(20)
    F_foot = _font(18)

    def fit(text, max_w, start, bold=False):
        size = start
        while size > 10:
            f = _font(size, bold)
            if d.textlength(text, font=f) <= max_w:
                return f
            size -= 2
        return _font(10, bold)

    def rule(x0, y, x1, w=3):
        d.line([(x0, y), (x1, y)], fill=0, width=w)

    # Header: location instead of a generic title
    loc = data.get("location", "")
    d.text((M, 12), loc, font=fit(loc, W - 2 * M - 330, 34, True), fill=0)
    stand = "%s %02d.%02d.  Stand %02d:%02d" % (
        WEEKDAYS[now.weekday()][:2], now.day, now.month, now.hour, now.minute)
    bb = d.textbbox((0, 0), stand, font=F_meta)
    d.text((W - M - (bb[2] - bb[0]), 20), stand, font=F_meta, fill=0)
    rule(M, 66, W - M)

    # Forecast icons from the bundled Weather Icons font, left-aligned
    # with the day label (centering pushed them too far right).
    # Small enough to leave a clear gap above the temperatures.
    F_icon = _weather_font(48)

    def draw_icon(key, cx, y):
        glyph = GLYPHS.get(key, GLYPHS["cloud"])
        bb = d.textbbox((0, 0), glyph, font=F_icon)
        d.text((cx - bb[0], y), glyph, font=F_icon, fill=0)

    # Left: temperatures
    indoor, outdoor = data["indoor"], data["outdoor"]
    y = 84
    d.text((M, y), "INNEN  ·  %s" % indoor["label"], font=F_label, fill=0)
    d.text((M, y + 30), indoor["temp"], font=fit(indoor["temp"], 368, 88, True), fill=0)
    d.text((M, y + 130), indoor["humidity"], font=F_sub, fill=0)
    rule(M, DIV_Y, M + 368)

    y2 = DIV_Y + 12
    outside_title = "AUSSEN" + ("  ·  " + outdoor["label"] if outdoor["label"] else "")
    d.text((M, y2), outside_title, font=F_label, fill=0)
    d.text((M, y2 + 30), outdoor["temp"], font=fit(outdoor["temp"], 368, 88, True), fill=0)
    d.text((M, y2 + 130), outdoor["sub"], font=fit(outdoor["sub"], 368, 22), fill=0)

    d.line([(400, 80), (400, 436)], fill=0, width=3)

    # Right: forecast
    RX = 416
    RW = W - M - RX
    d.text((RX, 84), "VORHERSAGE", font=F_label, fill=0)
    cell_w = RW // 3
    for i, fc in enumerate(data["forecast"][:3]):
        cx = RX + i * cell_w
        d.text((cx, 116), fc["day"], font=F_day, fill=0)
        draw_icon(fc["icon"], cx, 142)
        d.text((cx, 212), fc["temps"], font=F_body, fill=0)
        d.text((cx, 240), fc["cond"], font=fit(fc["cond"], cell_w - 4, 20), fill=0)
    rule(RX, DIV_Y, RX + RW)

    # Right bottom: events (title column starts after the widest time)
    events = data["events"][:4]
    title_x = RX + max(d.textlength(t, font=F_day) for t, _ in events) + 12
    yt = DIV_Y + 12
    d.text((RX, yt), "TERMINE  ·  Heute", font=F_label, fill=0)
    yy = yt + 34
    for t, title in events:
        d.text((RX, yy), t, font=F_day, fill=0)
        d.text((title_x, yy), title, font=fit(title, RX + RW - title_x, 24), fill=0)
        yy += 32

    # Footer
    rule(M, 448, W - M)
    d.text((M, 454), "Update alle 10 Min · Wetter: Open-Meteo", font=F_foot, fill=0)

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
    print("saved preview.png")
