"""Bands layout: three full-width bands.

1. indoor | outdoor temperature (large), date top right   200 px
2. 4-day forecast starting today                          140 px
3. next 3 events, one line each                           140 px
"""
from draw import W, WEEKDAYS, WEEKDAYS_SHORT, decimal, ellipsize, fit, font, icon

M = 20
FC_Y = 200  # top of the forecast band
EV_Y = 340  # top of the events band
MID = W // 2
OUT_X = MID + 20
TEMP_SIZE = 116  # shrinks via fit() for wide values like "-12,4°"


def _rtext(d, x_right, y, text, f):
    d.text((x_right - d.textlength(text, font=f), y), text, font=f, fill=0)


def _day_label(day, today):
    delta = (day - today).days
    if delta <= 0:  # also multi-day events that started earlier
        return "Heute"
    if delta == 1:
        return "Morgen"
    return "%s %02d.%02d." % (WEEKDAYS_SHORT[day.weekday()], day.day, day.month)


def _temps(d, indoor, outdoor, now):
    F_lbl = font(18, True)
    F_sub = font(20)

    d.text((M, 12), "INNEN  ·  %s" % indoor["label"].upper(), font=F_lbl, fill=0)
    temp = decimal(indoor["temp"], "°")
    d.text((M, 30), temp, font=fit(d, temp, MID - M - 16, TEMP_SIZE, True), fill=0)
    if indoor["hum"] is None:
        sub = "Keine Sensordaten"
    else:
        sub = "Luftfeuchte %d %%  ·  Batterie %d %%" % (round(indoor["hum"]), indoor["batt"])
    d.text((M, 164), sub, font=F_sub, fill=0)

    d.line([(MID, 14), (MID, FC_Y - 14)], fill=0, width=2)

    d.text((OUT_X, 12), "AUSSEN", font=F_lbl, fill=0)
    _rtext(d, W - M, 12, "%s, %02d.%02d." % (WEEKDAYS[now.weekday()], now.day, now.month), F_lbl)
    sub_x = OUT_X
    if outdoor is None:
        temp, sub = decimal(None, "°"), "Wetterdienst nicht erreichbar"
    else:
        temp = decimal(outdoor["temp"], "°")
        sub = "%s · gefühlt %d° · %d km/h" % (
            outdoor["cond"], round(outdoor["feels"]), round(outdoor["wind"]))
        # small icon in front of the text, so the temperature gets the full width
        icon(d, outdoor["icon"], OUT_X, 162, 26, top=True)
        sub_x = OUT_X + 36
    d.text((OUT_X, 30), temp, font=fit(d, temp, W - M - OUT_X, TEMP_SIZE, True), fill=0)
    d.text((sub_x, 164), ellipsize(d, sub, F_sub, W - M - sub_x), font=F_sub, fill=0)


def _forecast(d, forecast, today):
    y0 = FC_Y
    if not forecast:
        d.text((M, y0 + 52), "Keine Vorhersage verfügbar", font=font(26), fill=0)
        return
    F_day, F_hi, F_lo, F_cond = font(22, True), font(34, True), font(24), font(20)
    cw = (W - 2 * M) // 4  # cell borders at 210/400/590: the middle one meets MID
    for n, fc in enumerate(forecast[:4]):
        cx = M
        if n:
            border = M + n * cw
            d.line([(border, y0 + 14), (border, EV_Y - 14)], fill=0, width=2)
            cx = border + 20  # same inset as the outdoor block (OUT_X = MID + 20)
        label = "Heute" if fc["date"] == today else WEEKDAYS_SHORT[fc["date"].weekday()]
        d.text((cx, y0 + 10), label, font=F_day, fill=0)
        icon(d, fc["icon"], cx, y0 + 42, 48, top=True)
        d.text((cx + 80, y0 + 36), "%d°" % round(fc["hi"]), font=F_hi, fill=0)
        d.text((cx + 80, y0 + 74), "%d°" % round(fc["lo"]), font=F_lo, fill=0)
        d.text((cx, y0 + 108), ellipsize(d, fc["cond"], F_cond, cw - 24), font=F_cond, fill=0)


def _events(d, events, today):
    y = EV_Y + 12
    F_b, F_r, F_loc = font(28, True), font(28), font(22)
    if not events:
        msg = "Kalender nicht erreichbar" if events is None else "Keine Termine"
        d.text((M, y), msg, font=F_r, fill=0)
        return
    events = events[:3]
    labels = [_day_label(ev["date"], today) for ev in events]
    # Columns are measured so long labels ("Fr 23.10.") never overlap.
    time_x = M + max(d.textlength(lbl, font=F_b) for lbl in labels) + 20
    title_x = time_x + d.textlength("00:00", font=F_b) + 20
    title_w = W - M - title_x
    prev = None
    for ev, label in zip(events, labels):
        if label != prev:  # repeat the day only when it changes
            d.text((M, y), label, font=F_b, fill=0)
        prev = label
        if ev["time"]:
            d.text((time_x, y), ev["time"], font=F_b, fill=0)
        else:
            d.rectangle([time_x + 2, y + 9, time_x + 16, y + 23], fill=0)  # all-day
        title = ellipsize(d, ev["title"], F_r, title_w)
        d.text((title_x, y), title, font=F_r, fill=0)
        if ev["location"]:
            loc_x = title_x + d.textlength(title, font=F_r) + 14
            if W - M - loc_x > 80:
                d.text((loc_x, y + 5), ellipsize(d, "· " + ev["location"], F_loc, W - M - loc_x),
                       font=F_loc, fill=0)
        y += 42


def draw(d, data, now):
    today = now.date()
    _temps(d, data["indoor"], data["outdoor"], now)
    d.line([(M, FC_Y), (W - M, FC_Y)], fill=0, width=3)
    _forecast(d, data["forecast"], today)
    d.line([(M, EV_Y), (W - M, EV_Y)], fill=0, width=3)
    _events(d, data["events"], today)
