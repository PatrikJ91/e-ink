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
