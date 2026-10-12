"""Indoor climate from the Xiaomi LYWSD03MMC with PVVX custom firmware.

The sensor broadcasts unencrypted advertisements (service UUID 0x181A):
MAC[6] + temp int16LE/100 + humidity uint16LE/100 + battery mV uint16LE
+ battery % + packet counter + flags (15 bytes total).

Polling runs in a background thread every 5 min so HTTP requests never
wait for a BLE scan. Values older than 1 h fall back to MOCK.
"""
import asyncio
import struct
import threading
import time

from bleak import BleakScanner

from render import MOCK

SVC_UUID = "0000181a-0000-1000-8000-00805f9b34fb"
POLL_INTERVAL = 300
SCAN_SECONDS = 10
MAX_AGE = 3600

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


async def _scan_once():
    found = []
    devs = await BleakScanner.discover(timeout=SCAN_SECONDS, return_adv=True)
    for addr, (dev, adv) in devs.items():
        name = adv.local_name or ""
        if name.startswith("ATC_") and SVC_UUID in adv.service_data:
            parsed = _parse(bytes(adv.service_data[SVC_UUID]))
            if parsed:
                found.append((adv.rssi or -999, parsed))
    if not found:
        return None
    found.sort(reverse=True)
    return found[0][1]


def _loop():
    while True:
        try:
            data = asyncio.run(_scan_once())
            if data:
                with _lock:
                    _CACHE.update(ts=data["ts"], data=data)
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)


def get_indoor():
    """Live indoor dict (MOCK-compatible); falls back to MOCK."""
    global _started
    if not _started:
        _started = True
        threading.Thread(target=_loop, daemon=True).start()
    with _lock:
        data = _CACHE["data"] if time.time() - _CACHE["ts"] < MAX_AGE else None
    if data is None:
        return MOCK["indoor"]
    return {
        "label": MOCK["indoor"]["label"],
        "temp": ("%.1f" % data["temp"]).replace(".", ",") + " °C",
        "humidity": "Luftfeuchte %d %% · Batt %d %%" % (round(data["hum"]), data["batt"]),
    }


if __name__ == "__main__":
    print("warte auf ersten Scan (ca. 15 s) ...")
    time.sleep(SCAN_SECONDS + 5)
    print(get_indoor())
