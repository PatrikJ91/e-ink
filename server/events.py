"""Live calendar via Google's secret iCal URL (read-only, revocable).

The URL lives in calendar.url next to this file (chmod 600, never logged,
never committed). Events are cached for 10 min; on failure the last good
events are kept, or None ("not reachable") if there are none yet. The
layouts show that visibly, never fake events that could pass for real ones.
"""
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from icalendar import Calendar
from recurring_ical_events import of

from draw import TZ

BASE_DIR = Path(__file__).resolve().parent
WINDOW_DAYS = 14  # wide enough that all rows usually fill up
MAX_ROWS = 4  # the most any layout shows
CACHE_TTL = 600

_CACHE = {"ts": 0.0, "data": None}


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
        location = " ".join(str(ev.get("LOCATION") or "").split())
        rows.append((start, {
            "date": start.date(),
            "time": None if allday else "%02d:%02d" % (start.hour, start.minute),
            "title": " ".join(str(ev.get("SUMMARY", "(ohne Titel)")).split()),
            "location": location or None,
        }))
    rows.sort(key=lambda r: (r[0], r[1]["title"]))
    return [ev for _, ev in rows[:MAX_ROWS]]


def get_events():
    """Upcoming events as dicts (date, time or None = all-day, title,
    location or None); [] = no events, None = calendar not reachable."""
    if time.time() - _CACHE["ts"] < CACHE_TTL:
        return _CACHE["data"]
    try:
        _CACHE["data"] = _fetch()
    except Exception:
        pass  # keep the last good events (or None)
    _CACHE["ts"] = time.time()  # also on failure: Negativ-Caching, kein Retry-Storm
    return _CACHE["data"]


if __name__ == "__main__":
    for ev in get_events() or []:
        print("%s | %s | %.40s" % (ev["date"], ev["time"] or "ganztägig", ev["title"]))
