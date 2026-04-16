
import tkinter as tk
import json
import os

clicks = 0
per_click = 1
auto_clickers = 0

SAVE_FILE = "click_save.json"

def save():
    data = {
        "clicks": clicks,
        "per_click": per_click,
        "auto_clickers": auto_clickers
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load():
    global clicks, per_click, auto_clickers
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
                clicks = data.get("clicks", 0)
                per_click = data.get("per_click", 1)
                auto_clickers = data.get("auto_clickers", 0)
        except:
            pass

def update_ui():
    clicks_label.config(text=f"Clicks: {clicks}")
    per_click_label.config(text=f"Per Click: {per_click}")
    auto_label.config(text=f"Auto Clickers: {auto_clickers}")

def click():
    global clicks
    clicks += per_click
    update_ui()

def buy_upgrade():
    global clicks, per_click
    cost = per_click * 25
    if clicks >= cost:
        clicks -= cost
        per_click += 1
        update_ui()

def buy_auto():
    global clicks, auto_clickers
    cost = 100 + auto_clickers * 50
    if clicks >= cost:
        clicks -= cost
        auto_clickers += 1
        update_ui()

def auto_loop():
    global clicks
    clicks += auto_clickers
    update_ui()
    root.after(1000, auto_loop)

def on_close():
    save()
    root.destroy()

root = tk.Tk()
root.title("Click Simulator")
root.geometry("420x340")

title = tk.Label(root, text="CLICK SIMULATOR", font=("Arial", 18, "bold"))
title.pack(pady=10)

clicks_label = tk.Label(root, text="Clicks: 0", font=("Arial", 14))
clicks_label.pack()

per_click_label = tk.Label(root, text="Per Click: 1", font=("Arial", 12))
per_click_label.pack()

auto_label = tk.Label(root, text="Auto Clickers: 0", font=("Arial", 12))
auto_label.pack()

click_btn = tk.Button(root, text="CLICK!", font=("Arial", 16), width=14, height=2, command=click)
click_btn.pack(pady=10)

upgrade_btn = tk.Button(root, text="Upgrade Click (+1)", command=buy_upgrade)
upgrade_btn.pack(pady=5)

auto_btn = tk.Button(root, text="Buy Auto Clicker", command=buy_auto)
auto_btn.pack(pady=5)

load()
update_ui()

root.after(1000, auto_loop)
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
