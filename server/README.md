# Server

Läuft auf dem vorhandenen Raspberry Pi 3B.

Aufgaben:
- Sammelt die anzuzeigenden Informationen (z. B. Wetter, Termine).
- Erzeugt daraus direkt das fertige Layout für das Display.
- Stellt es dem ESP32 zum Abholen bereit.

## Betrieb (Mock-Stand)

- `render.py`: erzeugt das 800×480 1-bit Bild (V1-Layout) aus dem `MOCK`-Dict. `server.py`: stdlib-HTTP auf Port 8080 (`/health`, `/display.raw` = 48.000 Bytes, 1 = schwarz, `/display.bmp` zur Kontrolle im Browser).
- Deploy: `scp server/render.py server/server.py eink-raspi:~/e-ink/server/`
- Start auf dem Pi: `ssh eink-raspi "cd ~/e-ink/server && setsid python3 server.py < /dev/null > server.log 2>&1 &"` (danach SSH einfach zumachen, läuft weiter).
- Stopp: `ssh eink-raspi "fuser -k 8080/tcp"` (nötig nach Code-Änderung, der Server lädt den Code nur beim Start).
- Test vom Mac: `curl http://192.168.178.40:8080/health` → `ok`; raw muss 48.000 Bytes haben.

## Zugriff (SSH)

- Host: `192.168.178.40` (`raspberrypi.fritz.box`), Benutzer: `patrik`
- Kurzform (SSH-Config auf dem Mac): `ssh eink-raspi`
- Key: `~/.ssh/eink_raspi_ed25519` (Public Key liegt auf dem Pi in `~/.ssh/authorized_keys`)
- Falls Key neu einrichten nötig: `ssh-copy-id -i ~/.ssh/eink_raspi_ed25519.pub eink-raspi`
- Falls „No route to host" nur in OpenCode, aber Terminal geht: Systemeinstellungen → Datenschutz & Sicherheit → Lokales Netzwerk → `OpenCode` aktivieren und OpenCode neu starten.
