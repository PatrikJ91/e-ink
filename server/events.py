"""Live calendar via Google's secret iCal URL (read-only, revocable).

The URL lives in calendar.url next to this file (chmod 600, never logged,
never committed). Events are cached for 10 min; on failure the last good
events are kept, or a visible "not reachable" row if there are none yet
(never fake events that could pass for real ones).
"""
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar
from recurring_ical_events import of

from render import TZ, WEEKDAYS

BASE_DIR = Path(__file__).resolve().parent
WINDOW_DAYS = 14  # wide enough that all 4 rows usually fill up
MAX_ROWS = 4
CACHE_TTL = 600

_CACHE = {"ts": 0.0, "data": None}
OFFLINE = [("", "", "Kalender nicht erreichbar")]
WEEKDAYS_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _as_berlin(value):
    if isinstance(value, datetime):
        # Google exports single events in UTC ("...Z"): convert, otherwise
        # the display shows the UTC hour (and near midnight the wrong day).
        return value.astimezone(TZ) if value.tzinfo else value.replace(tzinfo=TZ)
    return datetime(value.year, value.month, value.day, tzinfo=TZ)


def _fetch():
    url = (BASE_DIR / "calendar.url").read_text().strip()
    with urllib.request.urlopen(url, timeout=10) as resp:
        cal = Calendar.from_ical(resp.read())
    now = datetime.now(TZ)
    rows = []
    for ev in of(cal).between(now - timedelta(days=1), now + timedelta(days=WINDOW_DAYS)):
        start_raw = ev.get("DTSTART")
        end_raw = ev.get("DTEND")
        if start_raw is None:
            continue
        start, end = _as_berlin(start_raw.dt), _as_berlin(end_raw.dt) if end_raw else None
        if end is not None and end <= now:
            continue  # already over
        allday = isinstance(start_raw.dt, date) and not isinstance(start_raw.dt, datetime)
        title = str(ev.get("SUMMARY", "(ohne Titel)"))
        location = ev.get("LOCATION")
        if location:
            title += " | %s" % location
        rows.append((
            start,
            "%s %02d.%02d." % (WEEKDAYS_SHORT[start.weekday()], start.day, start.month),
            "ganztägig" if allday else "%02d:%02d" % (start.hour, start.minute),
            " ".join(title.split()),
        ))
    rows.sort()
    out = [(d, t, title) for _, d, t, title in rows[:MAX_ROWS]]
    return out or [("", "", "Keine Termine")]


def get_events():
    """Live rows as (date, time, title); falls back to OFFLINE on failure."""
    if time.time() - _CACHE["ts"] < CACHE_TTL and _CACHE["data"]:
        return _CACHE["data"]
    try:
        _CACHE["data"] = _fetch()
        _CACHE["ts"] = time.time()
    except Exception:
        if _CACHE["data"] is None:
            _CACHE["data"] = list(OFFLINE)
        _CACHE["ts"] = time.time()  # Negativ-Caching: kein Retry-Storm
    return _CACHE["data"]


if __name__ == "__main__":
    for row in get_events():
        print("%s | %s | %.40s..." % (row[0], row[1], row[2]))
