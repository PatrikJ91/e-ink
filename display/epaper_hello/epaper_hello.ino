// Erster Display-Test: Waveshare 7.5" s/w (800x480) auf dem
// Universal e-Paper ESP32 Driver Board (WS15823).
//
// Vorbereitung in der Arduino IDE (Werkzeuge -> Bibliotheken verwalten):
//   1. "GxEPD2" von Jean-Marc Zingg installieren
//   2. "Adafruit GFX Library" installieren (Abhaengigkeit von GxEPD2)
//
// Einstellungen: Board "ESP32 Dev Module", Schalter 1 auf B, Schalter 2 auf ON.
// Der volle Refresh dauert ca. 4-5 s (Display flackert schwarz/weiss, normal).
//
// Falls das Display weiss bleibt:
//   - Verkabelung/FFC-Sitz pruefen, Schalter 1 auf A testen, Upload-Speed 115200.
//   - Aeltere Panel-Revision? Dann unten GxEPD2_750_GDEY075T7 gegen
//     GxEPD2_750_T7 tauschen (Header <GxEPD2_750_T7.h> aus src/gdeh einbinden).

#include <SPI.h>
#include <GxEPD2_BW.h>

// Festverdrahtung auf dem Driver-Board (muss nicht verkabelt werden):
//   DIN=P14, SCLK=P13, CS=P15, DC=P27, RST=P26, BUSY=P25
GxEPD2_BW<GxEPD2_750_GDEY075T7, GxEPD2_750_GDEY075T7::HEIGHT>
    display(GxEPD2_750_GDEY075T7(/*CS=*/15, /*DC=*/27, /*RST=*/26, /*BUSY=*/25));

void setup() {
  Serial.begin(115200);
  Serial.println("E-Paper-Test startet ...");

  // SPI-Pins ans Board-Layout anpassen. MUSS vor display.init() stehen:
  // (display.init() ruft SPI.begin() ohne Parameter, das ist als
  // zweiter Aufruf wirkungslos und uebernimmt dieses Mapping.)
  SPI.begin(/*SCK=*/13, /*MISO=*/-1, /*MOSI=*/14, /*SS=*/15);

  display.init(115200);
  display.setRotation(0); // 800x480 quer
  display.setTextColor(GxEPD_BLACK);

  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    display.setTextSize(4);
    display.setCursor(40, 70);
    display.println("Hallo E-Ink!");
    display.setTextSize(2);
    display.setCursor(40, 150);
    display.println("Waveshare 7.5\" s/w, 800x480");
    display.setCursor(40, 190);
    display.println("ESP32 Driver Board WS15823");
    display.setCursor(40, 250);
    display.print("Millis: ");
    display.println(millis());
  } while (display.nextPage());

  display.hibernate(); // Display schlafen legen, Bild bleibt sichtbar
  Serial.println("Fertig! Das Bild bleibt auch ohne Strom sichtbar.");
}

void loop() {
  delay(10000); // nichts mehr zu tun
}
