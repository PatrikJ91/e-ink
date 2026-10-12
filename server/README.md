# Server

Läuft auf dem vorhandenen Raspberry Pi 3B.

Aufgaben:
- Sammelt die anzuzeigenden Informationen (z. B. Wetter, Termine).
- Erzeugt daraus direkt das fertige Layout für das Display.
- Stellt es dem ESP32 zum Abholen bereit.

## Betrieb (Mock-Stand)

- `render.py`: erzeugt das 800×480 1-bit Bild (V1-Layout) aus dem `MOCK`-Dict. `server.py`: stdlib-HTTP auf Port 8080 (`/health`, `/display.raw` = 48.000 Bytes, 1 = schwarz, `/display.hash` = md5 dieser Bytes, `/display.bmp` zur Kontrolle im Browser).
- Das Bild wird **nicht** pro Request gerendert: ein Hintergrund-Thread rendert alle 2 Min (`REFRESH_INTERVAL`), die Requests liefern nur den fertigen Snapshot aus. Darum antworten sie in Millisekunden, auch wenn Wetter-/Kalender-Abruf hängt — wichtig, weil der ESP nur 5 s (Hash) bzw. 10 s (Raw) wartet. Daten frühestens nach `REFRESH_INTERVAL` im Bild.
- Abhängigkeiten (einmalig auf dem Pi): `pip3 install -r requirements.txt` (Datei vorher mit deployen; Pillow kommt aus dem System und steht nicht drin).
- Deploy: `scp server/*.py server/requirements.txt eink-raspi:~/e-ink/server/ && scp server/assets/weather-icons.ttf eink-raspi:~/e-ink/server/assets/` (vorher einmal `ssh eink-raspi "mkdir -p ~/e-ink/server/assets"`). Achtung: `calendar.url`/`sensor.mac` nie mitkopieren — liegen nur auf dem Pi.
- Start auf dem Pi: `ssh eink-raspi "cd ~/e-ink/server && setsid python3 server.py < /dev/null > server.log 2>&1 &"` (danach SSH einfach zumachen, läuft weiter).
- Stopp: `ssh eink-raspi "fuser -k 8080/tcp"` (nötig nach Code-Änderung, der Server lädt den Code nur beim Start).
- Test vom Mac: `curl http://192.168.178.40:8080/health` → `ok`; raw muss 48.000 Bytes haben. Hash prüfen: `curl -s .../display.hash` muss gleich `curl -s .../display.raw | md5sum` sein.
- Lokal testen (Mac): Port 8080 ist oft belegt, `PORT` in `server.py` z. B. auf 18080 ändern.
- Falsches Datum im Footer: der Render-Code nutzt fest `Europe/Berlin`
  (unabhängig von der Pi-Systemzeit) — prüfen, ob `render.py` aktuell
  deployed ist und der Server danach neugestartet wurde.
- Bild muss eine reine Funktion der Daten bleiben (keine Uhrzeit/Zufall
  im Layout), sonst ändert sich der Hash ständig und der ESP macht bei
  jedem Zyklus einen Full-Refresh.
- Pillow fehlt (eigentlich vorinstalliert): prüfen mit
  `python3 -c "import PIL; print(PIL.__version__)"`.

## Zugriff (SSH)

- Host: `192.168.178.40` (`raspberrypi.fritz.box`), Benutzer: `patrik`
- Kurzform (SSH-Config auf dem Mac): `ssh eink-raspi`
- Key: `~/.ssh/eink_raspi_ed25519` (Public Key liegt auf dem Pi in `~/.ssh/authorized_keys`)
- Falls Key neu einrichten nötig: `ssh-copy-id -i ~/.ssh/eink_raspi_ed25519.pub eink-raspi`
- Falls „No route to host" nur in OpenCode, aber Terminal geht: Systemeinstellungen → Datenschutz & Sicherheit → Lokales Netzwerk → `OpenCode` aktivieren und OpenCode neu starten.
