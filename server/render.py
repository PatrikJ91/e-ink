"""Render the 800x480 1-bit dashboard image (V1 layout).

Layout matches display/mockup_dashboard_v1.png. Data comes in as a plain
dict so mocked data can later be replaced 1:1 by real sensor/API/calendar
sources without touching the drawing code.
"""
import io
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

W, H = 800, 480
M = 16
DIV_Y = 268  # horizontal dividers left and right share this height

# Display stands in Berlin: explicit timezone, independent of the Pi's
# system timezone (which may be e.g. London/BST).
TZ = ZoneInfo("Europe/Berlin")

# No locale dependency: German names hardcoded (Pi locale may be C/POSIX).
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
            "Freitag", "Samstag", "Sonntag"]
MONTHS = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"]

MOCK = {
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

    # Header
    d.text((M, 12), "E-INK DASHBOARD", font=F_title, fill=0)
    stand = "Fr %02d.%02d.  Stand %02d:%02d" % (now.day, now.month, now.hour, now.minute)
    bb = d.textbbox((0, 0), stand, font=F_meta)
    d.text((W - M - (bb[2] - bb[0]), 20), stand, font=F_meta, fill=0)
    rule(M, 66, W - M)

    # Forecast icons (shaded so they survive 1-bit dithering)
    def icon_sun(x, y):
        cx, cy, r = x + 30, y + 26, 17
        for k in range(8):
            a = math.pi * k / 4 + math.pi / 8
            x0 = cx + int((r + 4) * math.cos(a))
            y0 = cy + int((r + 4) * math.sin(a))
            x1 = cx + int((r + 10) * math.cos(a))
            y1 = cy + int((r + 10) * math.sin(a))
            d.line([(x0, y0), (x1, y1)], fill=0, width=3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=150, outline=0, width=3)
        d.ellipse([x + 2, y + 32, x + 26, y + 54], fill=255, outline=0, width=3)
        d.ellipse([x + 18, y + 26, x + 46, y + 50], fill=255, outline=0, width=3)
        d.line([(x + 2, y + 52), (x + 50, y + 52)], fill=0, width=3)

    def icon_cloud(x, y):
        d.ellipse([x + 4, y + 14, x + 32, y + 42], fill=255, outline=0, width=3)
        d.ellipse([x + 24, y + 4, x + 54, y + 36], fill=255, outline=0, width=3)
        d.ellipse([x + 12, y + 20, x + 30, y + 38], fill=200, outline=0)
        d.line([(x + 4, y + 40), (x + 56, y + 40)], fill=0, width=3)

    def icon_rain(x, y):
        d.ellipse([x + 6, y + 4, x + 30, y + 26], fill=255, outline=0, width=3)
        d.ellipse([x + 24, y, x + 50, y + 22], fill=255, outline=0, width=3)
        d.line([(x + 6, y + 24), (x + 52, y + 24)], fill=0, width=3)
        for dx in (14, 28, 42):
            d.line([(x + dx, y + 30), (x + dx - 5, y + 44)], fill=0, width=3)
            d.line([(x + dx, y + 48), (x + dx - 5, y + 58)], fill=0, width=3)

    icons = {"sun": icon_sun, "cloud": icon_cloud, "rain": icon_rain}

    # Left: temperatures
    indoor, outdoor = data["indoor"], data["outdoor"]
    y = 84
    d.text((M, y), "INNEN  ·  %s" % indoor["label"], font=F_label, fill=0)
    d.text((M, y + 30), indoor["temp"], font=fit(indoor["temp"], 368, 88, True), fill=0)
    d.text((M, y + 130), indoor["humidity"], font=F_sub, fill=0)
    rule(M, DIV_Y, M + 368)

    y2 = DIV_Y + 12
    d.text((M, y2), "AUSSEN  ·  %s" % outdoor["label"], font=F_label, fill=0)
    d.text((M, y2 + 30), outdoor["temp"], font=fit(outdoor["temp"], 368, 88, True), fill=0)
    d.text((M, y2 + 130), outdoor["sub"], font=F_sub, fill=0)

    d.line([(400, 80), (400, 436)], fill=0, width=3)

    # Right: forecast
    RX = 416
    RW = W - M - RX
    d.text((RX, 84), "WETTER  ·  Vorhersage", font=F_label, fill=0)
    cell_w = RW // 3
    for i, fc in enumerate(data["forecast"][:3]):
        cx = RX + i * cell_w
        d.text((cx, 116), fc["day"], font=F_day, fill=0)
        icons.get(fc["icon"], icon_cloud)(cx, 146)
        d.text((cx, 212), fc["temps"], font=F_body, fill=0)
        d.text((cx, 240), fc["cond"], font=F_small, fill=0)
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
    d.text((M, 454), "Update alle 10 Min · Beispielwerte", font=F_foot, fill=0)

    return img.convert("1")


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
