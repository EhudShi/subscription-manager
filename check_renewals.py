import calendar
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "subscriptions.json")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DAYS_BEFORE = 2  # alert this many days before renewal


def parse_date(s):
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def add_months(d, months):
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def add_years(d, years):
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)  # Feb 29 edge case


def next_renewal(renewal_date_str, cycle):
    d = parse_date(renewal_date_str)
    today = date.today()
    guard = 0
    while d < today and guard < 600:
        d = add_months(d, 1) if cycle == "monthly" else add_years(d, 1)
        guard += 1
    return d


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        print("Telegram response status:", resp.status)


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables.")
        sys.exit(1)

    with open(DATA_FILE, encoding="utf-8") as f:
        subs = json.load(f)

    today = date.today()
    due = []
    for s in subs:
        nr = next_renewal(s["renewalDate"], s["cycle"])
        days_until = (nr - today).days
        if days_until == DAYS_BEFORE:
            due.append((s, nr))

    if not due:
        print("No renewals due for notification today.")
        return

    lines = ["🔔 מנויים שמתחדשים בעוד יומיים:", ""]
    for s, nr in due:
        cycle_label = "לחודש" if s["cycle"] == "monthly" else "לשנה"
        lines.append(f'• {s["name"]} ({s["category"]}) — {s["cost"]}₪ {cycle_label} — מתחדש {nr.isoformat()}')

    send_telegram("\n".join(lines))


if __name__ == "__main__":
    main()
