"""Minimal dashboard server: renders the 1-bit display image per request.

Stdlib only. Run on the Pi with:  python3 server.py  (serves on :8080)
"""
from http.server import BaseHTTPRequestHandler, HTTPServer

from render import render, render_bmp, render_raw

PORT = 8080


class Handler(BaseHTTPRequestHandler):
    server_version = "EInkMock/1"

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
            self._send(200, "application/octet-stream", render_raw())
        elif self.path == "/display.bmp":
            self._send(200, "image/bmp", render_bmp())
        else:
            self._send(404, "text/plain", b"unknown path")

    def log_message(self, *args):
        pass  # stay quiet on the little Pi


if __name__ == "__main__":
    print("serving on :%d ..." % PORT)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
