import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import time

# ================= CONFIG =================
BASE_FONT = 32
current_scale = 1.0
current_font = "Arial"

AI_START = {2,8,14,20,26,32,38,44,50,56}
AI_END   = {3,9,15,21,27,33,39,45,51,57}

# ================= MAIN APP =================
root = tk.Tk()
root.title("AI Timer Smart System")
root.geometry("420x520")
root.configure(bg="white")

# ================= STATE =================
ai_mode = True
timer_running = False
timer_value = 60

# ================= FONTS =================
big_font = (current_font, int(BASE_FONT * current_scale))
mid_font = (current_font, int(BASE_FONT * current_scale * 0.9))
small_font = (current_font, int(BASE_FONT * current_scale * 0.45))

# ================= UI =================
top = tk.Frame(root, bg="white")
top.pack(pady=10)

left_lbl  = tk.Label(top, text="0", font=big_font, bg="white")
mid_lbl   = tk.Label(top, text="", font=big_font, bg="white", justify="center")
right_lbl = tk.Label(top, text="0", font=big_font, bg="white")

left_lbl.grid(row=0, column=0, padx=15)
mid_lbl.grid(row=0, column=1, padx=15)
right_lbl.grid(row=0, column=2, padx=15)

# 🔹 تقليل المسافة بين الرقم و Next (من غير تغيير حجم)
mid_lbl.configure(pady=2)

# ================= TIMER =================
timer_lbl = tk.Label(
    root,
    text="",
    font=small_font,
    fg="red",
    bg="white"
)
timer_lbl.pack(pady=2)  # 🔹 مسافة قصيرة جدًا من البوكسات
timer_lbl.pack_forget()

# ================= INPUT =================
entry = tk.Entry(root, font=("Arial", 20), justify="center")
entry.pack(pady=15)

# ================= LOGIC =================
def start_timer():
    global timer_running, timer_value
    timer_running = True
    timer_value = 60
    timer_lbl.pack()

    def run():
        global timer_running, timer_value
        while timer_value > 0 and timer_running:
            timer_lbl.config(text=f"{timer_value}s")
            time.sleep(1)
            timer_value -= 1
        timer_lbl.pack_forget()
        timer_running = False

    threading.Thread(target=run, daemon=True).start()

def stop_timer():
    global timer_running
    timer_running = False
    timer_lbl.pack_forget()

def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit():
        return

    v = int(txt)

    left_lbl.config(text=str(v-1))
    right_lbl.config(text=str(v+1))

    # ===== AI MODE =====
    if ai_mode and v in AI_START:
        mid_lbl.config(
            text=f"{v} <\nNext",
            bg="#ADD8E6",
            font=mid_font
        )
        if not timer_running:
            start_timer()

    elif ai_mode and v in AI_END:
        mid_lbl.config(
            text=str(v),
            bg="white",
            font=big_font
        )
        stop_timer()

    else:
        mid_lbl.config(
            text=str(v),
            bg="white",
            font=big_font
        )

# ================= EVENTS =================
entry.bind("<KeyRelease>", calculate)

# ================= RUN =================
root.mainloop()