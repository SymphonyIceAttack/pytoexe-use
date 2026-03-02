import tkinter as tk
from datetime import datetime, date
import urllib.request
import threading
import re
import math
import calendar

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
            ).read().decode("utf-8","ignore")

            t = re.findall(r"\d{2}:\d{2}:\d{2}", html)

            if t:
                return t[0]
        except:
            pass

    return "offline"


# =============================
# ТОЧНЫЙ ВОЗРАСТ
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

    text = re.sub(r"[,/ -]", ".", text)

    try:
        d,m,y = map(int,text.split("."))
        return date(y,m,d)
    except:
        return None


# =============================
# WINDOW
# =============================
root = tk.Tk()
root.title("Возраст и точное время")
root.geometry("520x520")
root.configure(bg="#070b14")
root.resizable(False, False)


# =============================
# TITLE
# =============================
tk.Label(
    root,
    text="NEON AGE CLOCK",
    fg="#00ffe5",
    bg="#070b14",
    font=("Segoe UI",20,"bold")
).pack(pady=10)


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
canvas.pack()

center=130
radius=105
angle=0


def neon_clock():
    global angle

    canvas.delete("all")

    # glow rings
    for w in range(6,1,-1):
        canvas.create_oval(
            20,20,240,240,
            outline="#00ffe5",
            width=w
        )

    x=center+radius*math.cos(math.radians(angle))
    y=center+radius*math.sin(math.radians(angle))

    canvas.create_line(
        center,center,x,y,
        fill="#ff00ff",
        width=4
    )

    angle+=4
    root.after(30,neon_clock)


# =============================
# INPUT
# =============================
frame=tk.Frame(root,bg="#070b14")
frame.pack(pady=10)

entry=tk.Entry(
    frame,
    font=("Segoe UI",14),
    justify="center",
    width=18,
    bg="#111827",
    fg="white",
    insertbackground="white",
    relief="flat"
)
entry.pack(side="left",ipady=6)

tk.Label(
    frame,
    text="дд.мм.гггг",
    fg="gray",
    bg="#070b14"
).pack(side="left",padx=8)


# =============================
# RESULT
# =============================
result=tk.Label(
    root,
    text="",
    fg="#00ffe5",
    bg="#070b14",
    font=("Consolas",14),
    justify="center"
)
result.pack(pady=20)

net_time="--:--:--"


def update_net():
    global net_time
    net_time=get_net_time()


# =============================
# UPDATE LOOP
# =============================
def update():

    threading.Thread(
        target=update_net,
        daemon=True
    ).start()

    pc=datetime.now().strftime("%H:%M:%S")

    b=parse_date(entry.get())

    if b:
        y,m,d=calc_age(b)

        txt=f"""
Возраст:
{y} лет
{m} месяцев
{d} дней

Время ПК: {pc}
Интернет: {net_time}
"""
    else:
        txt=f"""
Время ПК: {pc}
Интернет: {net_time}
"""

    result.config(text=txt)

    root.after(1000,update)


neon_clock()
update()

root.mainloop()