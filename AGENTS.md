# AGENTS.md

## Project

E-Ink Dashboard (private hobby project): ESP32 + Waveshare 7.5" B/W display (`display/`) renders layouts served by a Raspberry Pi 3B (`server/`). The ESP32 only fetches and displays; no layout logic on the device.

Scope: keep it simple and pragmatic — a working hobby solution beats a corporate-grade one. No enterprise patterns (no microservices, no CI/CD pipelines, no heavy abstraction layers) unless explicitly requested.

## Commands

- Display: Arduino IDE 2.x, board `ESP32 Dev Module`, libs `GxEPD2` + `Adafruit GFX Library`. Sketch: `display/epaper_hello/epaper_hello.ino`. No CLI build yet.
- Server: no build/test/lint commands configured yet (see `server/README.md`). Do not invent tooling.
- Pi health check: `ssh -o BatchMode=yes eink-raspi "echo ok"`

## Server access (Raspberry Pi)

- Always use `ssh eink-raspi` (`HostName 192.168.178.40`, `User patrik`, `IdentityFile ~/.ssh/eink_raspi_ed25519`).
- On `No route to host`: the macOS `Local Network` permission for OpenCode is missing — ask the user to enable it and restart OpenCode.

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
