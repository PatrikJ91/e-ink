# AGENTS.md

## Project

E-Ink Dashboard (private hobby project): ESP32 + Waveshare 7.5" B/W display (`display/`) renders layouts served by a Raspberry Pi 3B (`server/`). The ESP32 only fetches and displays; no layout logic on the device.

Scope: keep it simple and pragmatic — a working hobby solution beats a corporate-grade one. No enterprise patterns (no microservices, no CI/CD pipelines, no heavy abstraction layers) unless explicitly requested.

## Commands

- Display: `arduino-cli compile --fqbn esp32:esp32:esp32 display/epaper_dashboard`, upload adds `-p /dev/cu.usbmodem5B140745161`, monitor via `arduino-cli monitor -p ... -c baudrate=115200`. (Arduino IDE 2.x also works: board `ESP32 Dev Module`, libs `GxEPD2` + `Adafruit GFX Library`.)
- Sketches: `display/epaper_hello/` (display-only test), `display/epaper_dashboard/` (fetches `/display.raw` from the Pi, Deep-Sleep 10 min). Dashboard needs `secrets.h` (copied from `secrets.example.h`, gitignored); a dummy file is enough for a compile-only check — the user enters real WiFi credentials.
- ESP32 constraints: a 48 KB image buffer + WiFi overflows DRAM with full-height GxEPD2 pages — keep page height small (120, must be a multiple of 8). `drawBitmap(x, y, buf, w, h, color)` — the buffer is the 3rd arg.
- Server: deploy with `scp server/render.py server/server.py eink-raspi:~/e-ink/server/`; restart with `fuser -k 8080/tcp` + detached start (see `server/README.md`). Never `pkill -f` with a pattern that also matches your own ssh command line. The server loads code only at startup.
- Contract: `GET http://192.168.178.40:8080/display.raw` returns exactly 48000 bytes, 1 = black, for `drawBitmap(..., GxEPD_BLACK)`.
- Pi health check: `ssh -o BatchMode=yes eink-raspi "echo ok"`

## Server access (Raspberry Pi)

- Always use `ssh eink-raspi` (`HostName 192.168.178.40`, `User patrik`, `IdentityFile ~/.ssh/eink_raspi_ed25519`).
- On `No route to host`: the macOS `Local Network` permission for OpenCode is missing — ask the user to enable it and restart OpenCode.
- If the ESP serial port is busy, the Arduino IDE serial monitor is holding it — ask the user to close it.

## Conventions

- Keep changes scoped to the request; follow existing patterns instead of adding architecture, libs, or formatting.
- Conventional Commits, e.g. `feat:`, `fix:`, `docs:`.
- Sparse comments, only for non-obvious logic.

## Boundaries

- Never commit secrets or SSH keys.
- Never commit, push, or open PRs unless explicitly asked.
- Never run destructive commands (`git reset --hard`, `git checkout --`, broad `rm`) or revert user edits unless explicitly asked.

## Verification

- Run the narrowest useful check (tests/typecheck/lint if configured; serial monitor at 115200 baud for display changes).
- Say why in the final summary if verification was skipped.
