import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
from flask import Flask, send_file
import threading
import os
import sys

# =============================
# ���������� ���������� EXE / PY
# =============================
def app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = app_dir()
OUT_FILE = os.path.join(BASE_DIR, "news_week.txt")
LOG_FILE = os.path.join(BASE_DIR, "service.log")

# =============================
# ���������
# =============================
URL = "https://www.forexfactory.com/calendar"
HEADERS = {"User-Agent": "Mozilla/5.0"}

UTC = pytz.utc
MSK = pytz.timezone("Europe/Moscow")

REFRESH_SEC = 1800  # 30 �����

# =============================
# Flask
# =============================
app = Flask(__name__)

# =============================
# �����������
# =============================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

# =============================
# ������� ������
# =============================
def get_week_range():
    today = datetime.utcnow().date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end

# =============================
# ������ ForexFactory
# =============================
def parse_forexfactory():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    rows = soup.find_all("tr", class_="calendar__row")

    start, end = get_week_range()
    events = []

    current_date = None

    for row in rows:
        date_td = row.find("td", class_="calendar__date")
        if date_td and date_td.text.strip():
            current_date = datetime.strptime(
                date_td.text.strip(), "%b %d"
            ).replace(year=datetime.utcnow().year).date()

        if not current_date or not (start <= current_date <= end):
            continue

        impact_td = row.find("td", class_="impact")
        if not impact_td:
            continue

        span = impact_td.find("span")
        if not span:
            continue

        classes = span.get("class", [])
        if "medium" in classes:
            impact = 2
        elif "high" in classes:
            impact = 3
        else:
            continue

        time_td = row.find("td", class_="calendar__time")
        currency_td = row.find("td", class_="calendar__currency")
        event_td = row.find("td", class_="calendar__event")

        if not time_td or not currency_td or not event_td:
            continue

        time_txt = time_td.text.strip()
        if time_txt in ("", "All Day"):
            continue

        try:
            dt_utc = datetime.strptime(
                f"{current_date} {time_txt}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            continue

        dt_utc = UTC.localize(dt_utc)
        dt_msk = dt_utc.astimezone(MSK)

        events.append(
            f"{dt_msk.strftime('%Y-%m-%d %H:%M')}|"
            f"{currency_td.text.strip()}|"
            f"{impact}|"
            f"{event_td.text.strip()}"
        )

    return events

# =============================
# ���������� �����
# =============================
def update_loop():
    while True:
        try:
            events = parse_forexfactory()
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                for e in events:
                    f.write(e + "\n")

            log(f"UPDATED {len(events)} EVENTS")
        except Exception as e:
            log(f"ERROR {e}")

        time.sleep(REFRESH_SEC)

# =============================
# HTTP endpoint
# =============================
@app.route("/news")
def serve_news():
    return send_file(OUT_FILE, mimetype="text/plain")

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    log("SERVICE STARTED")

    threading.Thread(
        target=update_loop,
        daemon=True
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        threaded=True
    )
