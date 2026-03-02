import tkinter as tk
from datetime import datetime, date
import urllib.request
import json
import re
import threading
import os
import sys

# =============================
# НАСТРОЙКИ
# =============================
SETTINGS_FILE = "settings.json"

LANG_DATA = {
    "RU": {
        "title": "Возраст и время",
        "hint": "день.месяц.год",
        "age": "Возраст",
        "pc": "Время ПК",
        "net": "Интернет время"
    },
    "EN": {
        "title": "Age & Time",
        "hint": "day.month.year",
        "age": "Age",
        "pc": "PC Time",
        "net": "Internet Time"
    }
}


# =============================
# SAFE EXECUTION
# =============================
def safe(f):
    def w(*a, **k):
        try:
            return f(*a, **k)
        except:
            return None
    return w


# =============================
# ПЕРВЫЙ ЗАПУСК
# =============================
def choose_language():

    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)["lang"]

    win = tk.Tk()
    win.title("Language")
    win.geometry("280x150")
    win.resizable(False, False)

    lang = {"value": "RU"}

    def select(l):
        lang["value"] = l
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"lang": l}, f)
        win.destroy()

    tk.Label(
        win,
        text="Выберите язык / Select language",
        font=("Segoe UI", 10)
    ).pack(pady=15)

    tk.Button(win, text="Русский",
              width=18,
              command=lambda: select("RU")).pack(pady=5)

    tk.Button(win, text="English",
              width=18,
              command=lambda: select("EN")).pack()

    win.mainloop()

    return lang["value"]


LANG = choose_language()
TXT = LANG_DATA[LANG]


# =============================
# TIME SYNC
# =============================
@safe
def time100():
    req = urllib.request.Request(
        "https://time100.ru/",
        headers={"User-Agent": "Mozilla"}
    )
    html = urllib.request.urlopen(req, timeout=4)\
        .read().decode("utf-8", "ignore")

    t = re.findall(r"\d{2}:\d{2}:\d{2}", html)
    return t[0]


@safe
def yandex_time():
    req = urllib.request.Request(
        "https://yandex.ru/time",
        headers={"User-Agent": "Mozilla"}
    )
    html = urllib.request.urlopen(req, timeout=4)\
        .read().decode("utf-8", "ignore")

    t = re.findall(r"\d{2}:\d{2}:\d{2}", html)
    return t[0]


def sync_time():
    for s in (time100, yandex_time):
        t = s()
        if t:
            return t
    return "offline"


# =============================
# DATE PARSER
# =============================
def parse_date(text):

    text = re.sub(r"[,/ -]", ".", text)

    try:
        d, m, y = map(int, text.split("."))
        return date(y, m, d)
    except:
        return None


def calc_age(b):
    t = date.today()

    y = t.year - b.year
    m = t.month - b.month
    d = t.day - b.day

    if d < 0:
        m -= 1
        d += 30

    if m < 0:
        y -= 1
        m += 12

    return y, m, d


# =============================
# WINDOWS 11 STYLE UI
# =============================
root = tk.Tk()
root.title(TXT["title"])
root.geometry("460x420")
root.configure(bg="#f0f2f5")
root.resizable(False, False)

# ===== Card =====
card = tk.Frame(
    root,
    bg="white",
    highlightthickness=0
)
card.place(relx=0.5, rely=0.5,
           anchor="center",
           width=380,
           height=320)

# имитация закругления
card.config(bd=0)

title = tk.Label(
    card,
    text=TXT["title"],
    font=("Segoe UI", 16, "bold"),
    bg="white"
)
title.pack(pady=15)

row = tk.Frame(card, bg="white")
row.pack()

entry = tk.Entry(
    row,
    font=("Segoe UI", 13),
    justify="center",
    width=18,
    relief="flat",
    bg="#f3f3f3"
)
entry.pack(side="left", ipady=6)

hint = tk.Label(
    row,
    text=TXT["hint"],
    fg="gray",
    bg="white"
)
hint.pack(side="left", padx=8)

result = tk.Label(
    card,
    text="",
    bg="white",
    font=("Segoe UI", 12),
    justify="center"
)
result.pack(pady=20)

net = "--:--:--"


def update_net():
    global net
    net = sync_time()


def update():

    threading.Thread(
        target=update_net,
        daemon=True
    ).start()

    pc = datetime.now().strftime("%H:%M:%S")

    b = parse_date(entry.get())

    if b:
        y, m, d = calc_age(b)

        txt = f"""
{TXT['age']}:
{y} / {m} / {d}

{TXT['pc']}: {pc}
{TXT['net']}: {net}
"""
    else:
        txt = f"""
{TXT['pc']}: {pc}
{TXT['net']}: {net}
"""

    result.config(text=txt)

    root.after(1000, update)


root.after(400, update)
root.mainloop()