import tkinter as tk
from pynput import keyboard
from datetime import datetime
import threading
import ctypes
import pystray
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import os
import sys
import winreg

active = False
only_numlock = True

counts = {str(i): 0 for i in range(10)}
counts['enter'] = 0

# ---------------- NumLock ----------------
def is_numlock_on():
    return ctypes.windll.user32.GetKeyState(0x90) & 1

# ---------------- Key Listener ----------------
def on_press(key):
    global active

    if not active:
        return

    if only_numlock and not is_numlock_on():
        return

    try:
        if key.char in counts:
            counts[key.char] += 1
    except AttributeError:
        if key == keyboard.Key.enter:
            counts['enter'] += 1

def start_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# ---------------- UI Actions ----------------
def toggle():
    global active
    active = not active
    status_label.config(text="Durum: AÇIK" if active else "Durum: KAPALI")

def save_log():
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now()} ---\n")
        for k, v in counts.items():
            f.write(f"{k}: {v}\n")

def show_graph():
    plt.figure()
    plt.bar(list(counts.keys()), list(counts.values()))
    plt.title("NumPad Kullanım")
    plt.show()

def update_labels():
    for k in counts:
        labels[k].config(text=f"{k}: {counts[k]}")
    root.after(300, update_labels)

# ---------------- Startup ----------------
def add_to_startup():
    exe_path = sys.executable
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "NumPadCounter", 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)

# ---------------- Tray ----------------
def create_image():
    img = Image.new('RGB', (64, 64), color='black')
    d = ImageDraw.Draw(img)
    d.text((10, 20), "NP", fill='white')
    return img

def quit_app(icon, item):
    icon.stop()
    root.quit()

def show_window(icon, item):
    root.after(0, root.deiconify)

def hide_window():
    root.withdraw()
    threading.Thread(target=icon.run, daemon=True).start()

icon = pystray.Icon("numpad", create_image(), menu=pystray.Menu(
    pystray.MenuItem("Aç", show_window),
    pystray.MenuItem("Çıkış", quit_app)
))

# ---------------- GUI ----------------
root = tk.Tk()
root.title("NumPad Sayaç")

status_label = tk.Label(root, text="Durum: KAPALI")
status_label.pack()

frame = tk.Frame(root)
frame.pack()

labels = {}
for k in counts:
    lbl = tk.Label(frame, text=f"{k}: 0")
    lbl.pack()
    labels[k] = lbl

tk.Button(root, text="Başlat / Durdur", command=toggle).pack(pady=5)
tk.Button(root, text="Grafik", command=show_graph).pack(pady=5)
tk.Button(root, text="Log Kaydet", command=save_log).pack(pady=5)
tk.Button(root, text="Başlangıçta Çalıştır", command=add_to_startup).pack(pady=5)
tk.Button(root, text="Tepsiye Küçült", command=hide_window).pack(pady=5)

threading.Thread(target=start_listener, daemon=True).start()

update_labels()
root.mainloop()