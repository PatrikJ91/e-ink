"""Minimal dashboard server: serves a pre-rendered 1-bit display image.

Stdlib only. Run on the Pi with:  python3 server.py  (serves on :8080)
"""
import hashlib
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from render import LAYOUT, render, render_bmp, render_raw
from weather import get_weather
from events import get_events
from sensor import get_indoor

PORT = 8080
# A background thread re-renders this often, so requests never wait for
# a weather/calendar fetch (those have their own 10 min caches anyway).
REFRESH_INTERVAL = 120


def _dashboard():
    # new dict: get_weather() returns its cache, which must stay untouched
    return dict(get_weather(), events=get_events(), indoor=get_indoor())


# The ESP asks for /display.hash and then /display.raw a moment later.
# Both must describe the *same* image, so image, raw bytes and md5 are
# swapped in as one immutable tuple. Readers only ever hold the lock for
# that swap, never across a render, so a slow render (weather/calendar
# fetch) can't stall a request past the ESP's 5 s timeout.
_LOCK = threading.Lock()
_SNAPSHOT = None  # (ts, img, raw, hash) or None until the first render


def _refresh():
    """Render once and publish image + raw bytes + hash atomically."""
    global _SNAPSHOT
    img = render(_dashboard())
    raw = render_raw(img)
    snap = (time.time(), img, raw, hashlib.md5(raw).hexdigest().encode())
    with _LOCK:
        _SNAPSHOT = snap
    return snap


def _cached():
    """Current (ts, img, raw, hash); renders inline only on a cold start."""
    with _LOCK:
        snap = _SNAPSHOT
    return snap if snap is not None else _refresh()


def _refresh_loop():
    while True:
        try:
            _refresh()
        except Exception:
            # Keep the last good image and stay alive: a dead refresher
            # would freeze the display until the next manual restart.
            traceback.print_exc()
        time.sleep(REFRESH_INTERVAL)


def start_refresher():
    threading.Thread(target=_refresh_loop, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = "EInk/1"

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, "text/plain", b"ok")
        elif self.path == "/display.raw":
            _, _, raw, _ = _cached()
            self._send(200, "application/octet-stream", raw)
        elif self.path == "/display.bmp":
            _, img, _, _ = _cached()
            self._send(200, "image/bmp", render_bmp(img))
        elif self.path == "/display.hash":
            # The ESP fetches this first and skips the 48 KB download +
            # refresh when it matches the hash of the displayed image.
            _, _, _, h = _cached()
            self._send(200, "text/plain", h)
        else:
            self._send(404, "text/plain", b"unknown path")

    def log_message(self, *args):
        pass  # stay quiet on the little Pi


if __name__ == "__main__":
    try:
        _refresh()  # first image before the port opens
    except Exception:
        traceback.print_exc()
    start_refresher()
    print("serving on :%d (layout: %s) ..." % (PORT, LAYOUT), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
