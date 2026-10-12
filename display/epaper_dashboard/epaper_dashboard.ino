// E-Ink Dashboard: holt das fertige 1-bit Bild (800x480) vom Pi-Server
// und zeigt es an. Danach Deep-Sleep, alle 10 Min ein neues Bild.
//
// Einmalig: secrets.example.h nach secrets.h kopieren und WLAN eintragen
// (secrets.h ist per .gitignore ausgeschlossen und landet nie im Repo).
//
// Ablauf pro Zyklus: WLAN verbinden -> Nachtpause? (0-6 Uhr schlafen) ->
// GET /display.raw (48000 Bytes, 1 = schwarz) -> nur bei Aenderung
// Full-Refresh (Hash im RTC-Memory) -> hibernate -> Deep-Sleep 10 Min.

#include <SPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_sleep.h>
#include <time.h>
#include <GxEPD2_BW.h>
#include "secrets.h"

#ifndef WIFI_SSID
#error "secrets.h fehlt: secrets.example.h nach secrets.h kopieren und WLAN eintragen"
#endif

#define DISPLAY_URL "http://192.168.178.40:8080/display.raw"
#define IMG_W 800
#define IMG_H 480
#define IMG_BYTES (IMG_W * IMG_H / 8) // 48000
#define WIFI_TIMEOUT_MS 15000
#define HTTP_RETRIES 3
#define SLEEP_US (10ULL * 60ULL * 1000000ULL)

// Festverdrahtung Driver-Board: DIN=P14, SCLK=P13, CS=P15, DC=P27, RST=P26, BUSY=P25
// Page-Hoehe 120 statt vollen 480 Zeilen: sonst passen 48 KB Bild-Buffer +
// GxEPD2-Buffer + WLAN-Stack nicht ins DRAM. drawBitmap geht im Page-Loop
// trotzdem (4 Durchgaenge), muss ein Vielfaches von 8 sein.
GxEPD2_BW<GxEPD2_750_GDEY075T7, 120>
    display(GxEPD2_750_GDEY075T7(/*CS=*/15, /*DC=*/27, /*RST=*/26, /*BUSY=*/25));

static uint8_t img[IMG_BYTES]; // 48 KB Bildspeicher im DRAM

// Letzter Bild-Hash, ueberlebt Deep-Sleep (nicht aber Stromverlust).
RTC_DATA_ATTR uint32_t last_hash = 0;
RTC_DATA_ATTR bool hash_valid = false;

static uint32_t fnv1a(const uint8_t* p, size_t n) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < n; i++) { h ^= p[i]; h *= 16777619UL; }
  return h;
}

static void deepSleepUs(uint64_t us) {
  WiFi.disconnect(true);
  esp_sleep_enable_timer_wakeup(us);
  esp_deep_sleep_start();
}

static void sleep10min() { deepSleepUs(SLEEP_US); }

// true zwischen 0 und 6 Uhr (NTP, Berlin). Bei NTP-Fehler: false,
// das Dashboard laeuft dann normal weiter.
static bool nightTime(struct tm* out) {
  configTime(0, 0, "pool.ntp.org");
  setenv("TZ", "CET-1CEST,M3.5.0,M10.5.0/3", 1);
  tzset();
  if (!getLocalTime(out, 5000)) {
    Serial.println("NTP fehlgeschlagen, trotzdem fortfahren");
    return false;
  }
  return out->tm_hour < 6;
}

static bool connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < WIFI_TIMEOUT_MS) {
    delay(250);
  }
  if (WiFi.status() == WL_CONNECTED) return true;
  // Diagnose: 1 = SSID nicht gefunden, 4 = Auth-Fehler, 6 = nicht verbunden
  Serial.printf("WLAN-Status: %d\n", (int)WiFi.status());
  Serial.println("Sichtbare Netze:");
  int n = WiFi.scanNetworks();
  for (int i = 0; i < n && i < 12; i++) {
    Serial.printf("  %s  %d dBm  Kanal %d\n",
                  WiFi.SSID(i).c_str(), (int)WiFi.RSSI(i), (int)WiFi.channel(i));
  }
  return false;
}

static bool fetchImage() {
  HTTPClient http;
  http.setTimeout(10000);
  for (int attempt = 1; attempt <= HTTP_RETRIES; attempt++) {
    Serial.printf("HTTP GET Versuch %d/%d ...\n", attempt, HTTP_RETRIES);
    if (!http.begin(DISPLAY_URL)) {
      Serial.println("http.begin fehlgeschlagen");
      continue;
    }
    int code = http.GET();
    int len = http.getSize();
    Serial.printf("HTTP %d, %d Bytes\n", code, len);
    if (code == 200 && len == IMG_BYTES) {
      size_t got = http.getStreamPtr()->readBytes(img, IMG_BYTES);
      http.end();
      Serial.printf("%u Bytes gelesen\n", (unsigned)got);
      return got == IMG_BYTES;
    }
    http.end();
    delay(1000);
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Dashboard startet ...");

  if (!connectWiFi()) {
    Serial.println("WLAN fehlgeschlagen, naechster Versuch in 10 Min");
    sleep10min();
  }
  Serial.print("WiFi ok, IP: ");
  Serial.println(WiFi.localIP());

  struct tm now_tm;
  if (nightTime(&now_tm)) {
    long now_s = now_tm.tm_hour * 3600L + now_tm.tm_min * 60L + now_tm.tm_sec;
    uint64_t us = (uint64_t)(6L * 3600L - now_s) * 1000000ULL;
    Serial.printf("Nachtpause 0-6 Uhr, schlafe %lu s\n", (unsigned long)(us / 1000000ULL));
    deepSleepUs(us);
  }

  if (!fetchImage()) {
    Serial.println("Bild-Download fehlgeschlagen, altes Bild bleibt");
    sleep10min();
  }

  uint32_t h = fnv1a(img, IMG_BYTES);
  if (hash_valid && h == last_hash) {
    Serial.println("Bild unveraendert, kein Refresh");
    sleep10min();
  }

  // SPI-Mapping MUSS vor display.init() stehen (siehe epaper_hello).
  SPI.begin(/*SCK=*/13, /*MISO=*/-1, /*MOSI=*/14, /*SS=*/15);

  display.init(115200);
  display.setRotation(0); // 800x480 quer
  display.setFullWindow();
  display.firstPage();
  do {
    display.drawBitmap(0, 0, img, IMG_W, IMG_H, GxEPD_BLACK);
  } while (display.nextPage());

  display.hibernate(); // Bild bleibt ohne Strom sichtbar
  last_hash = h;
  hash_valid = true;
  Serial.println("Fertig! Deep-Sleep 10 Min ...");
  sleep10min();
}

void loop() {
  // Unerreicht: nach Deep-Sleep startet der ESP immer bei setup().
}
