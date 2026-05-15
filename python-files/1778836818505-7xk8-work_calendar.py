# work_calendar.py
import csv
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
import calendar

DB_FILE = Path("work_calendar.csv")
TYPES_FILE = Path("work_types.csv")
FIELDNAMES = ["id","client","service_type","service","date","time","duration_min","worker","status","notes","created_at","updated_at"]

def ensure_db():
    if not DB_FILE.exists():
        with DB_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
    if not TYPES_FILE.exists():
        with TYPES_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["type_id","type_name","notes"])
            writer.writeheader()

def read_all():
    ensure_db()
    with DB_FILE.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_all(rows):
    with DB_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

def read_types():
    ensure_db()
    with TYPES_FILE.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_types(rows):
    with TYPES_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["type_id","type_name","notes"])
        writer.writeheader()
        writer.writerows(rows)

def next_id(rows):
    ids = [int(r["id"]) for r in rows if r["id"].isdigit()]
    return str(max(ids)+1 if ids else 1)

def next_type_id(rows):
    ids = [int(r["type_id"]) for r in rows if r["type_id"].isdigit()]
    return str(max(ids)+1 if ids else 1)

def add_entry(client, service_type, service, date_str, time_str, duration_min, worker, status="planned", notes=""):
    rows = read_all()
    now = datetime.utcnow().isoformat()
    entry = {
        "id": next_id(rows),
        "client": client,
        "service_type": service_type,   # id from types
        "service": service,
        "date": date_str,      # YYYY-MM-DD
        "time": time_str,      # HH:MM (24h)
        "duration_min": str(duration_min),
        "worker": worker,
        "status": status,
        "notes": notes,
        "created_at": now,
        "updated_at": now
    }
    rows.append(entry)
    write_all(rows)
    return entry

def find_by_date(start_date, end_date=None):
    rows = read_all()
    sd = datetime.fromisoformat(start_date)
    ed = datetime.fromisoformat(end_date) if end_date else sd
    result = []
    for r in rows:
        try:
            d = datetime.fromisoformat(r["date"])
        except Exception:
            continue
        if sd.date() <= d.date() <= ed.date():
            result.append(r)
    return result

def update_entry(entry_id, **fields):
    rows = read_all()
    updated = False
    for r in rows:
        if r["id"] == str(entry_id):
            for k,v in fields.items():
                if k in FIELDNAMES and v is not None:
                    r[k] = str(v)
            r["updated_at"] = datetime.utcnow().isoformat()
            updated = True
            break
    if updated:
        write_all(rows)
    return updated

def delete_entry(entry_id):
    rows = read_all()
    new = [r for r in rows if r["id"] != str(entry_id)]
    if len(new) == len(rows):
        return False
    write_all(new)
    return True

def format_row(r, types_map=None):
    tname = types_map.get(r["service_type"], r["service_type"]) if types_map else r.get("service_type","")
    return f"{r['id']}. {r['date']} {r['time']} ({r['duration_min']}m) | {r['client']} — [{tname}] {r['service']} | {r['worker']} | {r['status']}"

# --- types management ---
def add_type(type_name, notes=""):
    rows = read_types()
    t = {"type_id": next_type_id(rows), "type_name": type_name, "notes": notes}
    rows.append(t)
    write_types(rows)
    return t

def list_types():
    return read_types()

def delete_type(type_id):
    rows = read_types()
    new = [r for r in rows if r["type_id"] != str(type_id)]
    if len(new) == len(rows):
        return False
    write_types(new)
    return True

# --- calendar view ---
def month_calendar(year, month):
    # returns dict: day -> list(entries)
    rows = read_all()
    types = {t["type_id"]: t["type_name"] for t in read_types()}
    cal = {}
    for r in rows:
        try:
            d = datetime.fromisoformat(r["date"]).date()
        except Exception:
            continue
        if d.year == year and d.month == month:
            cal.setdefault(d.day, []).append(r)
    # sort each day's entries by time
    for k in cal:
        cal[k].sort(key=lambda x: x.get("time",""))
    return cal, types

def print_month(year, month):
    cal_obj = calendar.Calendar(firstweekday=0)
    month_name = calendar.month_name[month]
    print(f"{month_name} {year}".center(20))
    print("Mo Tu We Th Fr Sa Su")
    month_days = cal_obj.monthdayscalendar(year, month)
    cal, types = month_calendar(year, month)
    for week in month_days:
        line = []
        for d in week:
            if d == 0:
                line.append("  ")
            else:
                mark = "*" if d in cal else " "
                line.append(f"{str(d).rjust(2)}{mark}")
        print(" ".join(line))
    print("\n* — день с записями\n")
    # show brief per-day
    for day in sorted(cal.keys()):
        print(f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}:")
        for r in cal[day]:
            print("  -", format_row(r, types_map=types))

# --- CLI commands ---
def print_help():
    print("""Команды:
 add <client>;<service_type_id>;<service>;<YYYY-MM-DD>;<HH:MM>;<duration_min>;<worker>[;<notes>]
 list <YYYY-MM-DD> [<YYYY-MM-DD>]
 update <id> <field>=<value> [<field>=<value> ...]
 delete <id>
 export <file.csv>
 import <file.csv>
 types add <type_name>[;<notes>]
 types list
 types delete <type_id>
 cal month <YYYY> <MM>
 cal year <YYYY>
 help
 exit
Поля для update: client,service_type,service,date,time,duration_min,worker,status,notes
""")

def cmd_add(args):
    parts = args.split(";", maxsplit=8)
    if len(parts) < 7:
        print("Неправильный формат add. См. help.")
        return
    client,stype,service,date_s,time_s,dur,worker = [p.strip() for p in parts[:7]]
    notes = parts[7].strip() if len(parts) >=8 else ""
    try:
        datetime.fromisoformat(date_s)
        datetime.fromisoformat(f"{date_s}T{time_s}")
    except Exception:
        print("Неверный формат даты/времени. Используйте YYYY-MM-DD и HH:MM.")
        return
    entry = add_entry(client,stype,service,date_s,time_s,int(dur),worker,"planned",notes)
    types = {t["type_id"]: t["type_name"] for t in read_types()}
    print("Добавлено:", format_row(entry, types_map=types))

def cmd_list(args):
    parts = args.split()
    if not parts:
        print("Укажите дату: list YYYY-MM-DD [YYYY-MM-DD]")
        return
    start = parts[0]
    end = parts[1] if len(parts) >1 else None
    try:
        rows = find_by_date(start,end)
    except Exception:
        print("Неверный формат даты.")
        return
    if not rows:
        print("Записей нет.")
        return
    types = {t["type_id"]: t["type_name"] for t in read_types()}
    rows.sort(key=lambda r: (r["date"], r["time"]))
    for r in rows:
        print(format_row(r, types_map=types))

def cmd_update(args):
    parts = args.split()
    if len(parts) < 2:
        print("Использование: update <id> field=value ...")
        return
    eid = parts[0]
    updates = {}
    for fv in parts[1:]:
        if "=" not in fv: continue
        k,v = fv.split("=",1)
        updates[k] = v
    ok = update_entry(eid, **updates)
    print("Обновлено." if ok else "Не найден id.")

def cmd_delete(args):
    if not args:
        print("Укажите id.")
        return
    ok = delete_entry(args.strip())
    print("Удалено." if ok else "Не найден id.")

def cmd_export(args):
    fname = args.strip() or "export.csv"
    rows = read_all()
    with open(fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print("Экспортировано в", fname)

def cmd_import(args):
    fname = args.strip()
    if not fname or not Path(fname).exists():
        print("Файл не найден.")
        return
    with open(fname, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    write_all(rows)
    print("Импортировано.")

def cmd_types(args):
    parts = args.split(" ",1)
    act = parts[0] if parts else ""
    rest = parts[1] if len(parts)>1 else ""
    if act == "add":
        p = rest.split(";",1)
        name = p[0].strip()
        notes = p[1].strip() if len(p)>1 else ""
        t = add_type(name,notes)
        print("Добавлен тип:", t["type_id"], t["type_name"])
    elif act == "list":
        for t in read_types():
            print(f"{t['type_id']}. {t['type_name']} — {t['notes']}")
    elif act == "delete":
        if not rest:
            print("Укажите type_id")
            return
        ok = delete_type(rest.strip())
        print("Удалено." if ok else "Не найден type_id.")
    else:
        print("Использование: types add/list/delete. См. help.")

def cmd_cal(args):
    parts = args.split()
    if not parts:
        print("cal month <YYYY> <MM>  или  cal year <YYYY>")
        return
    if parts[0] == "month" and len(parts) >=3:
        y = int(parts[1]); m = int(parts[2])
        print_month(y,m)
    elif parts[0] == "year" and len(parts) >=2:
        y = int(parts[1])
        for m in range(1,13):
            print_month(y,m)
            print("-"*20)
    else:
        print("Неверные параметры. См. help.")

def main():
    ensure_db()
    print("Календарь производства работ — help для команд.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line: continue
        cmd, *rest = line.split(" ",1)
        args = rest[0] if rest else ""
        if cmd == "add":
            cmd_add(args)
        elif cmd == "list":
            cmd_list(args)
        elif cmd == "update":
            cmd_update(args)
        elif cmd == "delete":
            cmd_delete(args)
        elif cmd == "export":
            cmd_export(args)
        elif cmd == "import":
            cmd_import(args)
        elif cmd == "types":
            cmd_types(args)
        elif cmd == "cal":
            cmd_cal(args)
        elif cmd in ("help","h"):
            print_help()
        elif cmd in ("exit","quit"):
            break
        else:
            print("Неизвестная команда. help.")

if __name__ == "__main__":
    main()
