# Display

## Gekaufte Hardware

- Waveshare 7.5inch E-Ink Raw Display, 800x480, Schwarz/Weiß (WS13187)
- Waveshare Universal e-Paper Raw Panel Driver Board mit ESP32, WLAN/Bluetooth (WS15823)
- Verbindung lötfrei per Flachbandkabel, Stromversorgung über USB-Kabel.

## Aufgabe des ESP32

Der ESP32 macht kein eigenes Layout und sammelt keine Daten.
Er holt nur die vom Server generierte Anzeige ab und reicht sie an das Display durch.
Zwischen den Aktualisierungen schläft er.
