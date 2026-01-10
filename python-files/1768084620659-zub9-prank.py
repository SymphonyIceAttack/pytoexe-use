# -*- coding: utf-8 -*-
import os, time, sys, threading, signal, ctypes, winsound, random, msvcrt
import tkinter as tk

# ================= НАСТРОЙКИ =================
running = True
fake_seconds_left = 5 * 60
fake_encrypt_progress = 0
show_bsod = False
# ============================================

# ---------- ЗАПРЕТ CTRL+C ----------
try:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGBREAK, signal.SIG_IGN)
except:
    pass

# ---------- СЕКРЕТНЫЙ ВЫХОД ----------
def secret_exit():
    global running
    while running:
        if msvcrt.kbhit():
            k = msvcrt.getch()
            if k in (b'\x00', b'\xe0'):
                k = msvcrt.getch()
                if k == b';':  # F1
                    running = False
                    os._exit(0)
        time.sleep(0.05)

# ---------- КРЕСТИК ----------
def disable_close():
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        hMenu = user32.GetSystemMenu(hwnd, False)
        user32.DeleteMenu(hMenu, 0xF060, 0)

# ---------- МИГАНИЕ ----------
def blink_colors():
    colors = ["4F", "1F"]
    i = 0
    while running:
        os.system("color " + colors[i % 2])
        i += 1
        time.sleep(0.15)

# ---------- МЫШЬ ----------
def flying_mouse():
    user32 = ctypes.windll.user32
    cx = user32.GetSystemMetrics(0) // 2
    cy = user32.GetSystemMetrics(1) // 2
    while running:
        user32.SetCursorPos(cx, cy)
        time.sleep(0.01)

# ---------- ФЕЙК ТАЙМЕР ----------
def fake_timer():
    global fake_seconds_left, show_bsod
    while running and fake_seconds_left > 0:
        time.sleep(1)
        fake_seconds_left -= 1
    time.sleep(2)
    show_bsod = True

# ---------- ФЕЙК ШИФРОВКА ----------
def fake_encrypt():
    global fake_encrypt_progress
    while running and fake_encrypt_progress < 100:
        time.sleep(random.uniform(0.3, 0.7))
        fake_encrypt_progress += random.randint(1, 4)
        fake_encrypt_progress = min(fake_encrypt_progress, 100)

# ---------- ЛЕТАЮЩИЕ ОКНА ----------
def flying_errors():
    root = tk.Tk()
    root.withdraw()

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    wins = []

    for _ in range(4):
        w = tk.Toplevel()
        w.title("Windows Error")
        w.attributes("-topmost", True)
        w.geometry("320x120+200+200")
        tk.Label(
            w,
            text="Critical system error.\nMemory access violation.",
            fg="red",
            font=("Arial", 10, "bold")
        ).pack(expand=True)
        wins.append([w, random.choice([-6,6]), random.choice([-5,5])])

    while running:
        for item in wins:
            w, dx, dy = item
            x = w.winfo_x() + dx
            y = w.winfo_y() + dy
            if x < 0 or x > sw - 320: item[1] *= -1
            if y < 0 or y > sh - 120: item[2] *= -1
            w.geometry(f"+{x}+{y}")
        root.update()
        time.sleep(0.02)

# ---------- КОНСОЛЬ ----------
def setup_console():
    user32 = ctypes.windll.user32
    sx = user32.GetSystemMetrics(0)
    sy = user32.GetSystemMetrics(1)

    os.system(f"mode con: cols={sx//8} lines={sy//16}")
    os.system("title SYSTEM LOCKED")
    os.system("color 4F")

    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    user32.ShowWindow(hwnd, 3)  # FULLSCREEN
    disable_close()

# ---------- ОТРИСОВКА ----------
def draw():
    mins = fake_seconds_left // 60
    secs = fake_seconds_left % 60
    os.system("cls")
    print("############################################################")
    print("#   SYSTEM LOCKED                                          #")
    print("#                                                          #")
    print(f"#   FILES WILL BE DELETED IN: {mins:02d}:{secs:02d}            #")
    print("#                                                          #")
    print(f"#   Uploading encryption key... {fake_encrypt_progress:3d}%        #")
    print("#                                                          #")
    print("#   Windows will shut down in 30 seconds                   #")
    print("############################################################")

# ---------- ФЕЙК BSOD ----------
def fake_bsod():
    os.system("cls")
    os.system("color 1F")
    print("\n\n:(\n")
    print("Your PC ran into a problem and needs to restart.")
    print("Stop code: CRITICAL_PROCESS_DIED")
    print("\nPress F1 to exit")
    while True:
        time.sleep(1)

# ---------- MAIN ----------
def main():
    setup_console()

    threading.Thread(target=blink_colors, daemon=True).start()
    threading.Thread(target=flying_mouse, daemon=True).start()
    threading.Thread(target=fake_timer, daemon=True).start()
    threading.Thread(target=fake_encrypt, daemon=True).start()
    threading.Thread(target=flying_errors, daemon=True).start()
    threading.Thread(target=secret_exit, daemon=True).start()

    while running and not show_bsod:
        draw()
        time.sleep(0.3)

    if show_bsod:
        fake_bsod()

if __name__ == "__main__":
    main()
