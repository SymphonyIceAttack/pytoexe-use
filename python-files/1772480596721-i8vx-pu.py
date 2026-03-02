import tkinter as tk
from datetime import datetime, date
import urllib.request
import threading
import re
import math
import calendar

# =============================
# SETTINGS
# =============================
LANG = "RU"

TEXT = {
    "RU": {
        "title": "NEON AGE CLOCK",
        "format": "дд.мм.гггг",
        "age": "Возраст:",
        "years": "лет",
        "months": "месяцев",
        "days": "дней",
        "pc_time": "Время ПК:",
        "net_time": "Интернет:"
    },
    "EN": {
        "title": "NEON AGE CLOCK",
        "format": "dd.mm.yyyy",
        "age": "Age:",
        "years": "years",
        "months": "months",
        "days": "days",
        "pc_time": "PC Time:",
        "net_time": "Internet:"
    }
}

net_time = "--:--:--"


# =============================
# SAFE
# =============================
def safe(func):
    def wrapper(*a, **k):
        try:
            return func(*a, **k)
        except:
            return None
    return wrapper


# =============================
# INTERNET TIME
# =============================
@safe
def get_net_time():
    urls = [
        "https://time100.ru/",
        "https://yandex.ru/time"
    ]

    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla"}
            )

            html = urllib.request.urlopen(
                req,
                timeout=4
            ).read().decode("utf-8", "ignore")

            t = re.findall(r"\d{2}:\d{2}:\d{2}", html)
            if t:
                return t[0]
        except:
            pass

    return "offline"


def update_net():
    global net_time
    net_time = get_net_time()
    root.after(30000, lambda: threading.Thread(target=update_net, daemon=True).start())


# =============================
# AGE
# =============================
def calc_age(b):
    today = date.today()

    years = today.year - b.year
    months = today.month - b.month
    days = today.day - b.day

    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month != 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]

    if months < 0:
        years -= 1
        months += 12

    return years, months, days


def parse_date(text):
    text = re.sub(r"[,/ -]", ".", text.strip())
    parts = text.split(".")

    if len(parts) != 3:
        return None

    try:
        d, m, y = map(int, parts)
        return date(y, m, d)
    except:
        return None


# =============================
# WINDOW
# =============================
root = tk.Tk()
root.title("Neon Age Clock")
root.geometry("560x640")
root.configure(bg="#070b14")
root.resizable(False, False)


# =============================
# TITLE
# =============================
title_label = tk.Label(
    root,
    text=TEXT[LANG]["title"],
    fg="#00ffe5",
    bg="#070b14",
    font=("Segoe UI", 22, "bold")
)
title_label.pack(pady=10)


# =============================
# LANGUAGE SWITCH
# =============================
def switch_lang():
    global LANG
    LANG = "EN" if LANG == "RU" else "RU"
    refresh_text()


lang_btn = tk.Button(
    root,
    text="RU / EN",
    command=switch_lang,
    bg="#111827",
    fg="white",
    relief="flat"
)
lang_btn.pack(pady=5)


# =============================
# NEON CLOCK
# =============================
canvas = tk.Canvas(
    root,
    width=260,
    height=260,
    bg="#070b14",
    highlightthickness=0
)
canvas.pack(pady=10)

center = 130
radius = 105
angle = 0


def neon_clock():
    global angle

    canvas.delete("all")

    for w in range(6, 1, -1):
        canvas.create_oval(
            20, 20, 240, 240,
            outline="#00ffe5",
            width=w
        )

    x = center + radius * math.cos(math.radians(angle))
    y = center + radius * math.sin(math.radians(angle))

    canvas.create_line(
        center, center, x, y,
        fill="#ff00ff",
        width=4
    )

    angle += 4
    root.after(30, neon_clock)


# =============================
# INPUT
# =============================
frame = tk.Frame(root, bg="#070b14")
frame.pack(pady=15)

entry = tk.Entry(
    frame,
    font=("Segoe UI", 14),
    justify="center",
    width=18,
    bg="#111827",
    fg="white",
    insertbackground="white",
    relief="flat"
)
entry.pack(side="left", ipady=6)

format_label = tk.Label(
    frame,
    text=TEXT[LANG]["format"],
    fg="gray",
    bg="#070b14"
)
format_label.pack(side="left", padx=8)


# =============================
# RESULT
# =============================
result = tk.Label(
    root,
    text="",
    fg="#00ffe5",
    bg="#070b14",
    font=("Consolas", 14),
    justify="center"
)
result.pack(pady=20)


# =============================
# UPDATE
# =============================
def update():
    pc = datetime.now().strftime("%H:%M:%S")
    b = parse_date(entry.get())

    if b:
        y, m, d = calc_age(b)

        txt = f"""
{TEXT[LANG]["age"]}
{y} {TEXT[LANG]["years"]}
{m} {TEXT[LANG]["months"]}
{d} {TEXT[LANG]["days"]}

{TEXT[LANG]["pc_time"]} {pc}
{TEXT[LANG]["net_time"]} {net_time}
"""
    else:
        txt = f"""
{TEXT[LANG]["pc_time"]} {pc}
{TEXT[LANG]["net_time"]} {net_time}
"""

    result.config(text=txt)
    root.after(1000, update)


def refresh_text():
    title_label.config(text=TEXT[LANG]["title"])
    format_label.config(text=TEXT[LANG]["format"])


# =============================
# START
# =============================
neon_clock()
threading.Thread(target=update_net, daemon=True).start()
update()

root.mainloop()