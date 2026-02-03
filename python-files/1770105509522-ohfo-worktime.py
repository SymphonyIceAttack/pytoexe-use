import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "arbeitszeiten")
os.makedirs(DATA_DIR, exist_ok=True)


def parse_time(t):
    try:
        return datetime.strptime(t, "%H:%M")
    except ValueError:
        return None


def load_day(date):
    path = os.path.join(DATA_DIR, f"{date}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": date, "actions": [], "pauses": []}


def save_day(date, data):
    path = os.path.join(DATA_DIR, f"{date}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def overlaps(start, end, entries):
    for e in entries:
        e_start = parse_time(e["from"])
        e_end = parse_time(e["to"])
        if start < e_end and end > e_start:
            return True
    return False


def ask_time_range(data):
    while True:
        s = input("Von (HH:MM): ")
        e = input("Bis (HH:MM): ")

        start = parse_time(s)
        end = parse_time(e)

        if not start or not end:
            print("❌ Ungültiges Zeitformat.")
            continue

        if start >= end:
            print("❌ Startzeit muss vor Endzeit liegen.")
            continue

        if overlaps(start, end, data["actions"]) or overlaps(start, end, data["pauses"]):
            print("❌ Zeit überschneidet sich mit bestehendem Eintrag.")
            continue

        return s, e


def finalize_day(date, data):
    if not data["actions"]:
        print("❌ Keine Arbeitsaktionen vorhanden.")
        return

    start = min(parse_time(a["from"]) for a in data["actions"])
    end = max(parse_time(a["to"]) for a in data["actions"])

    total = end - start

    pause_time = timedelta()
    for p in data["pauses"]:
        pause_time += parse_time(p["to"]) - parse_time(p["from"])

    work_time = total - pause_time

    txt_path = os.path.join(DATA_DIR, f"{date}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Arbeitszeit für {date}\n")
        f.write("=" * 35 + "\n\n")
        f.write(f"Arbeitsbeginn: {start.strftime('%H:%M')}\n")
        f.write(f"Arbeitsende:   {end.strftime('%H:%M')}\n")
        f.write(f"Arbeitszeit:  {work_time}\n\n")

        if data["pauses"]:
            f.write("Pausen:\n")
            for p in data["pauses"]:
                f.write(f" - {p['from']} bis {p['to']}\n")
            f.write("\n")

        f.write("Tätigkeiten:\n")
        for a in data["actions"]:
            f.write(f" - {a['from']}–{a['to']}: {a['text']}\n")

    print(f"\n✅ Tag abgeschlossen → {txt_path}")


def enter_actions(date):
    data = load_day(date)

    while True:
        text = input("\nWas machst du? (leer = Tag abschließen): ").strip()
        if not text:
            break

        start, end = ask_time_range(data)

        if text.lower() == "pause":
            data["pauses"].append({"from": start, "to": end})
        else:
            data["actions"].append({"text": text, "from": start, "to": end})

        save_day(date, data)

    finalize_day(date, data)


def main():
    date = input("Datum (TT.MM.JJJJ): ").strip()
    enter_actions(date)


if __name__ == "__main__":
    main()
