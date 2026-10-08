# Server

Läuft auf dem vorhandenen Raspberry Pi 3B.

Aufgaben:
- Sammelt die anzuzeigenden Informationen (z. B. Wetter, Termine).
- Erzeugt daraus direkt das fertige Layout für das Display.
- Stellt es dem ESP32 zum Abholen bereit.

## Zugriff (SSH)

- Host: `192.168.178.40` (`raspberrypi.fritz.box`), Benutzer: `patrik`
- Kurzform (SSH-Config auf dem Mac): `ssh eink-raspi`
- Key: `~/.ssh/eink_raspi_ed25519` (Public Key liegt auf dem Pi in `~/.ssh/authorized_keys`)
- Falls Key neu einrichten nötig: `ssh-copy-id -i ~/.ssh/eink_raspi_ed25519.pub eink-raspi`
- Falls „No route to host" nur in OpenCode, aber Terminal geht: Systemeinstellungen → Datenschutz & Sicherheit → Lokales Netzwerk → `OpenCode` aktivieren und OpenCode neu starten.
