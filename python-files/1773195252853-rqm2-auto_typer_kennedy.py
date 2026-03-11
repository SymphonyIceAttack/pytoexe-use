import tkinter as tk
from tkinter import ttk, filedialog
import pyautogui
import threading
import keyboard
import time

running = False

def start_typing():
    global running
    running = True

    text = text_box.get("1.0", tk.END)
    speed = float(speed_entry.get())

    repeat_value = repeat_entry.get()

    def typing():
        global running
        time.sleep(3)

        if repeat_value == "∞":
            while running:
                pyautogui.write(text, interval=speed)
        else:
            for i in range(int(repeat_value)):
                if not running:
                    break
                pyautogui.write(text, interval=speed)

    threading.Thread(target=typing).start()


def stop_typing():
    global running
    running = False


def clear_text():
    text_box.delete("1.0", tk.END)


def copy_text():
    root.clipboard_clear()
    root.clipboard_append(text_box.get("1.0", tk.END))


def save_template():
    file = filedialog.asksaveasfilename(defaultextension=".txt")
    if file:
        with open(file, "w", encoding="utf-8") as f:
            f.write(text_box.get("1.0", tk.END))


def load_template():
    file = filedialog.askopenfilename()
    if file:
        with open(file, "r", encoding="utf-8") as f:
            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, f.read())


def update_stats(event=None):
    text = text_box.get("1.0", tk.END)
    chars = len(text)
    words = len(text.split())

    stats_label.config(text=f"حروف: {chars} | كلمات: {words}")


root = tk.Tk()
root.title("Auto Typer Kennedy")
root.geometry("750x500")
root.configure(bg="#111")

title = tk.Label(root, text="Auto Typer Kennedy", fg="red", bg="#111", font=("Arial", 22, "bold"))
title.pack(pady=10)

frame = tk.Frame(root, bg="#111")
frame.pack()

text_box = tk.Text(frame, width=80, height=8, bg="#222", fg="white", insertbackground="white")
text_box.grid(row=0, column=0, columnspan=4, pady=10)
text_box.bind("<KeyRelease>", update_stats)

tk.Label(frame, text="السرعة", fg="red", bg="#111").grid(row=1, column=0)
speed_entry = tk.Entry(frame)
speed_entry.insert(0, "0.05")
speed_entry.grid(row=1, column=1)

tk.Label(frame, text="عدد التكرار", fg="red", bg="#111").grid(row=1, column=2)
repeat_entry = tk.Entry(frame)
repeat_entry.insert(0, "1")
repeat_entry.grid(row=1, column=3)

buttons = tk.Frame(root, bg="#111")
buttons.pack(pady=20)

tk.Button(buttons, text="ابدأ", command=start_typing, bg="red", fg="white", width=12).grid(row=0, column=0, padx=5)
tk.Button(buttons, text="إيقاف", command=stop_typing, bg="#222", fg="white", width=12).grid(row=0, column=1, padx=5)
tk.Button(buttons, text="نسخ", command=copy_text, bg="#222", fg="white", width=12).grid(row=0, column=2, padx=5)
tk.Button(buttons, text="مسح", command=clear_text, bg="#222", fg="white", width=12).grid(row=0, column=3, padx=5)

tk.Button(buttons, text="حفظ قالب", command=save_template, bg="#222", fg="white", width=12).grid(row=1, column=0, pady=5)
tk.Button(buttons, text="تحميل قالب", command=load_template, bg="#222", fg="white", width=12).grid(row=1, column=1, pady=5)

stats_label = tk.Label(root, text="حروف: 0 | كلمات: 0", fg="red", bg="#111")
stats_label.pack()

copyright_label = tk.Label(root, text="© Auto Typer Kennedy", fg="gray", bg="#111")
copyright_label.pack(side="bottom", pady=10)

keyboard.add_hotkey("F8", start_typing)
keyboard.add_hotkey("F9", stop_typing)

root.mainloop()