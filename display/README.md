# Display

## Gekaufte Hardware

- Waveshare 7.5inch E-Ink Raw Display, 800x480, Schwarz/Weiß (WS13187)
- Waveshare Universal e-Paper Raw Panel Driver Board mit ESP32, WLAN/Bluetooth (WS15823)
- Verbindung lötfrei per Flachbandkabel, Stromversorgung über USB-Kabel.

## Aufgabe des ESP32

Der ESP32 macht kein eigenes Layout und sammelt keine Daten.
Er holt nur die vom Server generierte Anzeige ab und reicht sie an das Display durch.
Zwischen den Aktualisierungen schläft er.

## Anleitung: Sketch aufspielen (MacBook)

Hardware: USB-C-Datenkabel direkt an den Mac (Achtung: reines Ladekabel geht nicht).
Schalter am Driver-Board: Nr. 1 auf B (7,5" s/w), Nr. 2 auf ON (sonst kein Upload).

1. Arduino IDE 2.x öffnen, Boardpaket „esp32 by Espressif Systems" installieren.
2. Board: „ESP32 Dev Module".
3. Port: `/dev/cu.usbmodem5B140745161`
   (Board meldet sich als „USB Single Serial", Hersteller-ID 0x1a86 = WCH/CH343.
   Falls der Port fehlt: Treiber CH343 installieren, in Datenschutz & Sicherheit
   freigeben, Mac neu starten.)
4. Bibliotheken installieren (Bibliotheken verwalten): „GxEPD2" + „Adafruit GFX Library".
5. Sketch `epaper_hello/epaper_hello.ino` öffnen und hochladen.
   Bei hängendem „Connecting...": BOOT-Taste halten, ggf. Upload-Speed auf 115200 senken.
6. Seriellen Monitor auf 115200 Baud: Nach dem Refresh steht dort „Fertig!",
   das Display zeigt „Hallo E-Ink!" und behält das Bild ohne Strom.

## Dashboard-Sketch (Server-Bild anzeigen)

Sketch `epaper_dashboard/epaper_dashboard.ino`: holt alle 10 Min das fertige
Bild vom Pi (`GET http://192.168.178.40:8080/display.raw`), Full-Refresh,
danach Deep-Sleep. `epaper_hello` bleibt als reiner Display-Test erhalten.

1. `cp display/epaper_dashboard/secrets.example.h display/epaper_dashboard/secrets.h`,
   WLAN eintragen (bleibt lokal, `secrets.h` ist per `.gitignore` ausgeschlossen).
2. Hochladen wie oben (Board, Port, Schalter identisch).
3. Serieller Monitor 115200: `WiFi ok`, `HTTP 200`, `48000 Bytes gelesen`, `Fertig!`.

## Alternative ohne Arduino IDE: arduino-cli (MacBook)

Einmalig: `brew install arduino-cli`, dann ESP32-Boardpaket einrichten:

```bash
arduino-cli config init --overwrite
arduino-cli config add board_manager.additional_urls \
  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

Die Libs (`GxEPD2`, `Adafruit GFX Library`) werden aus `~/Documents/Arduino/libraries`
übernommen, falls sie dort schon per Arduino IDE installiert sind.

Kompilieren, hochladen, mithören (Sketch-Verzeichnis als Pfad):

```bash
arduino-cli compile --fqbn esp32:esp32:esp32 display/epaper_dashboard
arduino-cli upload -p /dev/cu.usbmodem5B140745161 --fqbn esp32:esp32:esp32 display/epaper_dashboard
arduino-cli monitor -p /dev/cu.usbmodem5B140745161 -c baudrate=115200
```

Hinweis: Der Sketch nutzt Page-Höhe 120 statt 480 — sonst passen 48 KB
Bild-Buffer + WLAN-Stack nicht ins DRAM (Linker-Fehler `dram0_0_seg overflowed`).

## Troubleshooting

- `WLAN fehlgeschlagen` + Statuscode: `1` = SSID falsch/nicht gefunden
  (Tippfehler? 5-GHz-only SSID? ESP kann nur 2,4 GHz),
  `4` = Passwort falsch. Danach listet der ESP sichtbare Netze mit
  Empfangsstärke — prüfen, ob das eigene dabei ist.
- Nur `???` im Monitor: Baudrate auf 115200 stellen.
- Port belegt (`Resource busy`): Serial Monitor der Arduino IDE schließen —
  nur ein Programm kann den Port gleichzeitig nutzen.
- Nach Upload läuft der ESP sofort los; wer den Start verpasst, drückt
  die RST-Taste am Board bei laufendem Monitor.
- Display zeigt altes Bild: Sketch ist noch nie erfolgreich durchgelaufen
  (WLAN/HTTP-Fehler im Monitor suchen).
