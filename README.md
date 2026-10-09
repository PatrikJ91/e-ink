# E-Ink Dashboard

Hobbyprojekt: Ein E-Ink-Display zeigt Wetter, Termine und weitere Infos an.

Aufbau:
- `display/`: ESP32 mit E-Ink-Display, zeigt die vom Server gelieferte Anzeige an.
- `server/`: Raspberry Pi 3B als Info-Quelle, liefert auch direkt das Layout.

## Komplett-Setup von Grund auf (ohne KI, Reihenfolge beachten)

1. Pi per SSH einrichten: Key/Config siehe `server/README.md` („Zugriff").
2. Server deployen + starten: siehe `server/README.md` („Betrieb").
   Prüfen: `curl http://192.168.178.40:8080/health` → `ok`,
   `/display.bmp` im Browser ansehen.
3. ESP flashen: `secrets.h` anlegen, Sketch hochladen, seriellen
   Monitor prüfen — siehe `display/README.md` („Dashboard-Sketch").
4. Fertig, wenn das Display das Dashboard zeigt und die „Stand"-Zeit
   aktuell ist (neues Bild alle 10 Min automatisch).

## Checkliste

- [x] Hardware bestellt
- [x] Leeres Repository erzeugt
- [x] Server-Grundgerüst (Mock-Daten, Bild per HTTP)
- [x] Display-Grundgerüst (Hello + Dashboard-Sketch)
- [x] Erste Anzeige Ende-zu-Ende
- [ ] Echte Daten (Sensor, Wetter-API, Google Kalender)
