import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import time
from flask import Flask, send_file
import threading
import os

URL = "https://www.forexfactory.com/calendar"
HEADERS = {"User-Agent": "Mozilla/5.0"}

UTC = pytz.utc
MSK = pytz.timezone("Europe/Moscow")

OUT_FILE = "news_week.txt"

app = Flask(__name__)

def get_week_dates():
    today = datetime.utcnow().date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end

def parse_forexfactory():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    rows = soup.find_all("tr", class_="calendar__row")

    start, end = get_week_dates()
    events = []

    current_date = None

    for row in rows:
        date_td = row.find("td", class_="calendar__date")
        if date_td and date_td.text.strip():
            current_date = datetime.strptime(date_td.text.strip(), "%b %d").replace(
                year=datetime.utcnow().year
            ).date()

        if not current_date or not (start <= current_date <= end):
            continue

        impact_td = row.find("td", class_="impact")
        if not impact_td:
            continue

        impact_span = impact_td.find("span")
        if not impact_span:
            continue

        impact_class = impact_span.get("class", [])
        if "medium" in impact_class:
            impact = 2
        elif "high" in impact_class:
            impact = 3
        else:
            continue

        time_td = row.find("td", class_="calendar__time")
        currency_td = row.find("td", class_="calendar__currency")
        event_td = row.find("td", class_="calendar__event")

        if not time_td or not currency_td or not event_td:
            continue

        if time_td.text.strip() in ("", "All Day"):
            continue

        event_time = datetime.strptime(
            f"{current_date} {time_td.text.strip()}",
            "%Y-%m-%d %H:%M"
        )

        event_utc = UTC.localize(event_time)
        event_msk = event_utc.astimezone(MSK)

        events.append(
            f"{event_msk.strftime('%Y-%m-%d %H:%M')}|"
            f"{currency_td.text.strip()}|"
            f"{impact}|"
            f"{event_td.text.strip()}"
        )

    return events

def update_file_loop():
    while True:
        try:
            events = parse_forexfactory()
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                for e in events:
                    f.write(e + "\n")
            print(f"[OK] Updated {len(events)} events")
        except Exception as e:
            print("[ERROR]", e)

        time.sleep(1800)  # ���������� ��� � 30 �����

@app.route("/news")
def serve_news():
    return send_file(OUT_FILE, mimetype="text/plain")

def start_http():
    app.run(host="127.0.0.1", port=5000)

if __name__ == "__main__":
    threading.Thread(target=update_file_loop, daemon=True).start()
    start_http()
