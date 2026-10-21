"""Indoor climate from the Xiaomi LYWSD03MMC with PVVX custom firmware.

The sensor broadcasts unencrypted advertisements (service UUID 0x181A):
MAC[6] + temp int16LE/100 + humidity uint16LE/100 + battery mV uint16LE
+ battery % + packet counter + flags (15 bytes total).

Polling runs in a background thread every 5 min so HTTP requests never
wait for a BLE scan. Values older than 1 h (or none yet) come back as
None, which the layouts show as a visible "–,–" placeholder instead of
plausible-looking fake values.

The event loop lives for the whole process, not one per scan: each
asyncio.run() left a dead D-Bus connection behind, and after ~24 h of
scans dbus-daemon refuses new clients (BleakDBusError AccessDenied),
which silently switched the display to fallback values.
"""
import asyncio
import struct
import threading
import time
from pathlib import Path

from bleak import BleakScanner

BASE_DIR = Path(__file__).resolve().parent
MAC_FILE = BASE_DIR / "sensor.mac"  # auto-pinned on first sighting (gitignored)
SVC_UUID = "0000181a-0000-1000-8000-00805f9b34fb"
POLL_INTERVAL = 300
SCAN_SECONDS = 10
MAX_AGE = 3600
LABEL = "Wohnzimmer"

_CACHE = {"ts": 0.0, "data": None}
_started = False
_lock = threading.Lock()


def _parse(payload):
    if len(payload) != 15:
        return None
    mac = ":".join("%02X" % b for b in payload[5::-1])
    temp, hum, _, batt = struct.unpack("<hHHB", payload[6:13])
    return {"mac": mac, "temp": temp / 100, "hum": hum / 100,
            "batt": batt, "ts": time.time()}


def _pinned_mac():
    try:
        return MAC_FILE.read_text().strip().upper() or None
    except OSError:
        return None


async def _scan_once():
    pinned = _pinned_mac()
    found = []
    devs = await BleakScanner.discover(timeout=SCAN_SECONDS, return_adv=True)
    for addr, (dev, adv) in devs.items():
        name = adv.local_name or ""
        if name.startswith("ATC_") and SVC_UUID in adv.service_data:
            parsed = _parse(bytes(adv.service_data[SVC_UUID]))
            if parsed is None:
                continue
            if pinned and parsed["mac"] != pinned:
                continue  # foreign sensor (e.g. neighbour's)
            found.append((adv.rssi or -999, parsed))
    if not found:
        return None
    found.sort(key=lambda x: x[0], reverse=True)
    best = found[0][1]
    if not pinned:
        try:
            MAC_FILE.write_text(best["mac"])  # pin for all future scans
        except OSError:
            pass
    return best


def _loop():
    # One long-lived event loop for all scans: an asyncio.run() per scan
    # leaks a D-Bus connection each time and kills the broker within a day.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            data = loop.run_until_complete(_scan_once())
            if data:
                with _lock:
                    _CACHE.update(ts=data["ts"], data=data)
        except Exception as e:
            # write the reason into server.log; without it any scan
            # problem only ever shows as "Keine Sensordaten" on display
            print("[%s] scan failed: %s: %s" % (time.strftime("%m-%d %H:%M:%S"),
                                                type(e).__name__, e),
                  flush=True)
        time.sleep(POLL_INTERVAL)


def get_indoor():
    """{"label", "temp", "hum", "batt"}; values are None without fresh data."""
    global _started
    if not _started:
        _started = True
        threading.Thread(target=_loop, daemon=True).start()
    with _lock:
        data = _CACHE["data"] if time.time() - _CACHE["ts"] < MAX_AGE else None
    if data is None:
        return {"label": LABEL, "temp": None, "hum": None, "batt": None}
    return {"label": LABEL, "temp": data["temp"], "hum": data["hum"], "batt": data["batt"]}


if __name__ == "__main__":
    print("warte auf ersten Scan (ca. 15 s) ...")
    time.sleep(SCAN_SECONDS + 5)
    print(get_indoor())
