import tkinter as tk
from datetime import datetime, date
import urllib.request
import re
import math
import threading
import sys

# ================= SAFE TIME100 =================
def get_time100_safe():
    try:
        req = urllib.request.Request(
            "https://time100.ru/",
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=4) as r:
            html = r.read().decode("utf-8", errors="ignore")

        t = re.findall(r"\d{2}:\d{2}:\d{2}", html)

        if t:
            return t[0]

    except:
        pass

    return "нет сети"


# ================= AGE =================
def calculate_age(b):
    today = date.today()

    y = today.year - b.year
    m = today.month - b.month
    d = today.day - b.day

    if d < 0:
        m -= 1
        d += 30

    if m < 0:
        y -= 1
        m += 12

    return y, m, d


# ================= WINDOW =================
root = tk.Tk()
root.title("Возраст и точное время")
root.geometry("480x520")
root.configure(bg="#070b1a")
root.resizable(False, False)

# ================= TITLE =================
title = tk.Label(
    root,
    text="CYBER AGE TIMER",
    fg="#00ffee",
    bg="#070b1a",
    font=("Segoe UI", 20, "bold")
)
title.pack(pady=10)

# ================= CLOCK =================
canvas = tk.Canvas(
    root,
    width=220,
    height=220,
    bg="#070b1a",
    highlightthickness=0
)
canvas.pack()

center = 110
radius = 90
angle = 0


def animate():
    global angle

    canvas.delete("all")

    canvas.create_oval(
        20, 20, 200, 200,
        outline="#00ffee",
        width=3
    )

    x = center + radius * math.cos(math.radians(angle))
    y = center + radius * math.sin(math.radians(angle))

    canvas.create_line(
        center, center,
        x, y,
        fill="#ff00ff",
        width=4
    )

    angle += 5
    root.after(40, animate)


# ================= INPUT =================
entry = tk.Entry(
    root,
    font=("Segoe UI", 14),
    justify="center",
    width=20
)
entry.pack(pady=15)

entry.insert(0, "01.01.2000")

# ================= RESULT =================
result = tk.Label(
    root,
    text="Загрузка...",
    fg="white",
    bg="#070b1a",
    font=("Consolas", 13),
    justify="center"
)
result.pack(pady=20)

internet_time = "--:--:--"


def update_net():
    global internet_time
    internet_time = get_time100_safe()


# ================= UPDATE LOOP =================
def update():

    pc = datetime.now().strftime("%H:%M:%S")

    threading.Thread(
        target=update_net,
        daemon=True
    ).start()

    try:
        birth = datetime.strptime(
            entry.get(),
            "%d.%m.%Y"
        ).date()

        y, m, d = calculate_age(birth)

        txt = f"""
Возраст:
{y} лет {m} мес {d} дней

Время ПК: {pc}
time100.ru: {internet_time}
"""

    except:
        txt = f"""
Время ПК: {pc}
time100.ru: {internet_time}
"""

    result.config(text=txt)

    root.after(1000, update)


# ================= START SAFE =================
def start():
    animate()
    update()


root.after(100, start)

try:
    root.mainloop()
except:
    sys.exit()