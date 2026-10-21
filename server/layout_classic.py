"""Classic layout (V1, display/mockup_dashboard_v1.png): four quarters.

Indoor and outdoor temperature on the left, 3-day forecast top right,
4 events bottom right, date in the footer.
"""
from draw import W, WEEKDAYS, WEEKDAYS_SHORT, decimal, fit, font, icon

M = 16
DIV_Y = 222  # horizontal dividers left and right share this height


def _indoor(indoor):
    if indoor["temp"] is None:
        return decimal(None, " °C"), "Keine Sensordaten"
    return (decimal(indoor["temp"], " °C"),
            "Luftfeuchte %d %% · Batt %d %%" % (round(indoor["hum"]), indoor["batt"]))


def _outdoor(outdoor):
    if outdoor is None:
        return decimal(None, " °C"), "Wetterdienst nicht erreichbar"
    return (decimal(outdoor["temp"], " °C"),
            "%s · gefühlt %s · %.0f km/h" % (
                outdoor["cond"], decimal(outdoor["feels"], " °C"), outdoor["wind"]))


def _event_rows(events):
    """-> [(date, time, title)] as the classic event table shows them."""
    if events is None:
        return [("", "", "Kalender nicht erreichbar")]
    if not events:
        return [("", "", "Keine Termine")]
    rows = []
    for ev in events[:4]:
        day = ev["date"]
        title = ev["title"]
        if ev["location"]:
            title += " | %s" % ev["location"]
        rows.append(("%s %02d.%02d." % (WEEKDAYS_SHORT[day.weekday()], day.day, day.month),
                     ev["time"] or "ganztägig",
                     title))
    return rows


def draw(d, data, now):
    F_label = font(22, True)
    F_sub = font(22)
    F_day = font(24, True)
    F_body = font(24)
    F_foot = font(18)

    def rule(x0, y, x1, w=3):
        d.line([(x0, y), (x1, y)], fill=0, width=w)

    # Left: temperatures (no header anymore: everything moved up)
    in_temp, in_sub = _indoor(data["indoor"])
    y = 20
    d.text((M, y), "INNEN  ·  %s" % data["indoor"]["label"], font=F_label, fill=0)
    d.text((M, y + 32), in_temp, font=fit(d, in_temp, 368, 100, True), fill=0)
    d.text((M, y + 148), in_sub, font=F_sub, fill=0)
    rule(M, DIV_Y, M + 368)

    out_temp, out_sub = _outdoor(data["outdoor"])
    y2 = DIV_Y + 14
    d.text((M, y2), "AUSSEN", font=F_label, fill=0)
    d.text((M, y2 + 32), out_temp, font=fit(d, out_temp, 368, 100, True), fill=0)
    d.text((M, y2 + 148), out_sub, font=fit(d, out_sub, 368, 22), fill=0)

    d.line([(400, 20), (400, 436)], fill=0, width=3)

    # Right: forecast. Icons from the bundled Weather Icons font,
    # left-aligned with the day label. Small enough to clear the
    # temperatures below (rain glyphs extend far below the baseline).
    RX = 416
    RW = W - M - RX
    d.text((RX, 20), "VORHERSAGE", font=F_label, fill=0)
    cell_w = RW // 3
    for i, fc in enumerate(data["forecast"][:3]):
        cx = RX + i * cell_w
        d.text((cx, 52), WEEKDAYS_SHORT[fc["date"].weekday()], font=F_day, fill=0)
        icon(d, fc["icon"], cx, 80, 50)
        d.text((cx, 152), "%d°/%d°" % (round(fc["hi"]), round(fc["lo"])), font=F_body, fill=0)
        d.text((cx, 182), fc["cond"], font=fit(d, fc["cond"], cell_w - 4, 20), fill=0)
    rule(RX, DIV_Y, RX + RW)

    # Right bottom: events in 3 columns (date, time, name).
    # Date/time use a smaller font and tight gaps so the name column
    # gets maximum width; column starts are measured so nothing overlaps.
    F_ev = font(18, True)
    events = _event_rows(data["events"])
    date_x = RX
    time_x = date_x + max(d.textlength(day, font=F_ev) for day, _, _ in events) + 10
    title_x = time_x + max(d.textlength(t, font=F_ev) for _, t, _ in events) + 10
    title_w = RX + RW - title_x
    yt = DIV_Y + 14
    d.text((RX, yt), "TERMINE", font=F_label, fill=0)
    yy = yt + 36
    for day, t, title in events:
        d.text((date_x, yy), day, font=F_ev, fill=0)
        d.text((time_x, yy), t, font=F_ev, fill=0)
        d.text((title_x, yy), title, font=fit(d, title, title_w, 22), fill=0)
        yy += 36

    # Footer: weekday + date only, small, bottom left.
    rule(M, 448, W - M)
    d.text((M, 454), "%s, %02d.%02d." % (
        WEEKDAYS[now.weekday()], now.day, now.month), font=F_foot, fill=0)
