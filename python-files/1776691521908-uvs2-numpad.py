import tkinter as tk
from pynput import keyboard
from datetime import datetime
import threading
import ctypes
import matplotlib.pyplot as plt

# ---------------- STATE ----------------
active = False
only_numlock = True

counts = {str(i): 0 for i in range(10)}
counts["enter"] = 0

# ---------------- NUMLOCK CHECK ----------------
def is_numlock_on():
    return ctypes.windll.user32.GetKeyState(0x90) & 1

# ---------------- KEY HANDLER ----------------
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
            counts["enter"] += 1

# ---------------- LISTENER THREAD ----------------
def start_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# ---------------- UI FUNCTIONS ----------------
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
    plt.title("NumPad Kullanım Grafiği")
    plt.xlabel("Tuş")
    plt.ylabel("Basım")
    plt.show()

def update_ui():
    for k in counts:
        labels[k].config(text=f"{k}: {counts[k]}")
    root.after(300, update_ui)

# ---------------- GUI ----------------
root = tk.Tk()
root.title("NumPad Tracker")

status_label = tk.Label(root, text="Durum: KAPALI", font=("Arial", 12))
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

# ---------------- START THREAD ----------------
threading.Thread(target=start_listener, daemon=True).start()

update_ui()
root.mainloop()