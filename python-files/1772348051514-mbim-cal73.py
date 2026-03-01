import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from datetime import datetime
import os
import time

# ================== RANGE CALCULATOR (الإعدادات العامة) ==================
LIMITS_FILE = "limits.txt"
TIMER_SAVE_FILE = "timer_last_time.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}
AI_NEXT_VALUES = {2, 8, 14, 20, 26, 32, 38, 44, 50, 56}

topmost = True
dark_mode = False
ai_mode = False
current_group_idx = 0
ai_delay_sec = 0 

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

root = tk.Tk()
root.title("Range Calculator Pro")
root.geometry("520x450")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= THEME ENGINE (تحسين شامل) =================
def apply_theme(target_root, mode="light", is_timer=False):
    """تطبيق الثيمات مع معالجة ملاحظات الأداء والأخطاء"""
    
    # تعريف العناصر الاستثنائية (التي لا تتأثر بالثيم العام)
    result_labels = []
    if not is_timer:
        result_labels = [left_lbl, middle_lbl, right_lbl]

    if mode == "original":
        bg = "SystemButtonFace" if not is_timer else "white"
        target_root.config(bg=bg)
        for widget in target_root.winfo_children():
            w_class = widget.winfo_class()
            if w_class == "Button":
                widget.config(bg="SystemButtonFace", fg="black", relief="raised", bd=2)
            elif w_class == "Entry":
                widget.config(bg="white", fg="black", relief="sunken", bd=2)
            elif w_class == "Frame":
                widget.config(bg=bg)
                for child in widget.winfo_children():
                    if child.winfo_class() == "Label" and child not in result_labels:
                        child.config(bg=bg, fg="black")
        return

    if mode == "retro":
        bg_retro = "#C0C0C0"
        target_root.config(bg=bg_retro)
        for widget in target_root.winfo_children():
            w_type = widget.winfo_class()
            if w_type == "Button":
                widget.config(bg="#C0C0C0", fg="black", relief="raised", bd=4, font=("Courier", 10, "bold"))
            elif w_type == "Entry":
                widget.config(bg="white", fg="black", relief="sunken", bd=3)
            elif w_type == "Frame":
                widget.config(bg=bg_retro)
                for child in widget.winfo_children():
                    if child.winfo_class() == "Label" and child not in result_labels:
                        child.config(bg=bg_retro, fg="black", font=("Courier", 10, "bold"))
                    elif child.winfo_class() == "Button":
                        child.config(bg="#C0C0C0", fg="black", relief="raised", bd=4)
        return

    # One UI Logic
    bg_color = "#f4f4f4" if mode == "light" else "#121212"
    card_color = "white" if mode == "light" else "#1e1e1e"
    text_color = "black" if mode == "light" else "#e0e0e0"
    accent_blue = "#0376f2"

    target_root.config(bg=bg_color)
    for widget in target_root.winfo_children():
        w_type = widget.winfo_class()
        if w_type == "Frame":
            widget.config(bg=bg_color)
            for child in widget.winfo_children():
                if child.winfo_class() == "Label" and child not in result_labels:
                    child.config(bg=bg_color, fg=text_color)
                if child.winfo_class() == "Button":
                    child.config(bg=accent_blue, fg="white", relief="flat", bd=0)
        elif w_type == "Label" and widget not in result_labels:
            widget.config(bg=bg_color, fg=text_color)
        elif w_type == "Entry":
            widget.config(bg=card_color, fg=text_color, relief="flat", bd=1)
        elif w_type == "Button":
            widget.config(bg=accent_blue, fg="white", relief="flat", bd=0)

def show_theme_picker(target_root, is_timer=False):
    pop = tk.Toplevel(target_root)
    pop.title("Themes")
    pop.geometry("250x280")
    pop.attributes("-topmost", True)
    tk.Label(pop, text="Select Style", font=("Segoe UI", 11, "bold")).pack(pady=10)
    
    modes = [("Original", "original"), ("One UI Light", "light"), 
             ("One UI Dark", "dark"), ("Retro Blocks", "retro")]
    
    for text, m in modes:
        tk.Button(pop, text=text, width=20, 
                  command=lambda mode=m: [apply_theme(target_root, mode, is_timer), pop.destroy()]).pack(pady=5)

# ================= TIMER LOGIC (الرئيسي) =================
timer_lbl = tk.Label(root, font=(current_font, int(BASE_FONT*0.9)), fg="blue")
timer_running = False
timer_after_id = None

def start_timer_main(delay_sec=0):
    global timer_running
    if timer_running: return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    root.after(int(delay_sec*1000), _countdown, 60)

def stop_timer_main():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id: root.after_cancel(timer_after_id)
    timer_after_id = None
    timer_lbl.pack_forget()

def _countdown(sec):
    global timer_after_id, timer_running
    if not timer_running: return
    if sec <= 0:
        stop_timer_main()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000, _countdown, sec-1)

# ================= CALCULATE & AI =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2: return
    v = int(txt)
    
    l, r = 0, 0
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    
    m = l + 3
    left_lbl.config(text=l)
    right_lbl.config(text=r)
    
    # تحديث الـ Middle Label بناءً على القواعد
    if ai_mode and v in AI_NEXT_VALUES:
        middle_lbl.config(text=f"{v} <\nNext", bg=ai_bg)
        start_timer_main(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer_main()
    else:
        char = '<' if v < m else '>' if v > m else '='
        middle_lbl.config(text=f"{m} {char}", bg="white")
        stop_timer_main()

def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode: auto_update()

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, "end")
    entry.insert(0, (now.hour*60 + now.minute) % 60)
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.5)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, size+2, size+2, fill=color, outline="black")

# ================= UI ELEMENTS =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns_frame = tk.Frame(root)
btns_frame.pack(pady=5)

calc_btn = tk.Button(btns_frame, text="Generate", command=calculate)
calc_btn.pack(side="left", padx=3)

clear_btn = tk.Button(btns_frame, text="Clear", command=lambda: entry.delete(0, "end"))
clear_btn.pack(side="left", padx=3)

prev_btn = tk.Button(btns_frame, text="◀", command=lambda: navigate_group(-1))
prev_btn.pack(side="left", padx=3)

next_btn = tk.Button(btns_frame, text="▶", command=lambda: navigate_group(1))
next_btn.pack(side="left", padx=3)

ai_canvas = tk.Canvas(btns_frame, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

def navigate_group(step):
    global current_group_idx
    current_group_idx = (current_group_idx + step) % (len(limits)-1)
    entry.delete(0, "end")
    entry.insert(0, limits[current_group_idx])
    calculate()

res_frame = tk.Frame(root)
res_frame.pack(pady=10)
left_lbl = tk.Label(res_frame, width=6, bg="red", fg="white", font=(current_font, BASE_FONT))
middle_lbl = tk.Label(res_frame, width=6, bg="white", font=(current_font, BASE_FONT))
right_lbl = tk.Label(res_frame, width=6, bg="green", fg="white", font=(current_font, BASE_FONT))
left_lbl.pack(side="left", padx=2); middle_lbl.pack(side="left", padx=2); right_lbl.pack(side="left", padx=2)

# ================= TIMERPRO WINDOW (التحسينات المطلوبة) =================
class TimerProWindow:
    def __init__(self, parent):
        self.root = parent
        self.root.title("Timer Pro")
        self.root.geometry("400x350")
        self.root.attributes("-topmost", True)
        
        self.timer_running = False
        self.timer_seconds = self.load_time()
        self.last_seconds = self.timer_seconds if self.timer_seconds > 0 else 300
        self.end_time = 0
        self.after_id = None

        # المنيو
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Styles", command=lambda: show_theme_picker(self.root, True))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        self.setup_ui()
        self.update_display()

    def load_time(self):
        if os.path.exists(TIMER_SAVE_FILE):
            try:
                with open(TIMER_SAVE_FILE, "r") as f: return float(f.read().strip())
            except: return 0
        return 0

    def save_time(self):
        with open(TIMER_SAVE_FILE, "w") as f:
            f.write(str(round(self.timer_seconds, 2)))

    def setup_ui(self):
        self.lbl = tk.Label(self.root, text="00:00", font=("Segoe UI", 40, "bold"))
        self.lbl.pack(pady=15)
        
        entry_f = tk.Frame(self.root)
        entry_f.pack()
        self.ent = tk.Entry(entry_f, width=10, justify="center")
        self.ent.pack(side="left", padx=5)
        
        presets = tk.Frame(self.root)
        presets.pack(pady=10)
        for s in [390, 300, 180]:
            m, sc = divmod(s, 60)
            tk.Button(presets, text=f"{m:02d}:{sc:02d}", command=lambda v=s: self.set_val(v)).pack(side="left", padx=2)

        self.canvas = tk.Canvas(self.root, height=8, bg="#ddd", highlightthickness=0)
        self.canvas.pack(fill="x", padx=30, pady=10)
        self.bar = self.canvas.create_rectangle(0, 0, 0, 8, fill="#2196F3", outline="")

        ctrls = tk.Frame(self.root)
        ctrls.pack(pady=10)
        tk.Button(ctrls, text="START", bg="green", fg="white", width=10, command=self.start).pack(side="left", padx=5)
        tk.Button(ctrls, text="STOP", bg="red", fg="white", width=10, command=self.stop).pack(side="left", padx=5)

    def set_val(self, s):
        self.stop()
        self.timer_seconds = self.last_seconds = float(s)
        self.save_time()
        self.update_display()

    def update_display(self):
        m, s = divmod(int(self.timer_seconds), 60)
        self.lbl.config(text=f"{m:02d}:{s:02d}")
        # Progress Bar Logic
        w = self.canvas.winfo_width()
        if w < 10: w = 340 # Default
        ratio = (self.timer_seconds / self.last_seconds) if self.last_seconds > 0 else 0
        ratio = max(0, min(1, ratio))
        self.canvas.coords(self.bar, 0, 0, w * ratio, 8)

    def tick(self):
        if self.timer_running:
            rem = self.end_time - time.time()
            if rem > 0:
                self.timer_seconds = rem
                self.update_display()
                # 250ms is better for CPU than 100ms
                self.after_id = self.root.after(250, self.tick)
            else:
                self.timer_seconds = 0
                self.update_display()
                self.stop()

    def start(self):
        if not self.timer_running:
            if self.ent.get():
                try: self.timer_seconds = self.last_seconds = float(self.ent.get()) * 60
                except: pass
            if self.timer_seconds > 0:
                self.timer_running = True
                self.end_time = time.time() + self.timer_seconds
                self.tick()

    def stop(self):
        self.timer_running = False
        if self.after_id: self.root.after_cancel(self.after_id)
        self.save_time()

# ================= EXTRA UTILS (Scale, Alpha, Move) =================
def open_control_popup(mode):
    p = tk.Toplevel(root)
    p.title(mode)
    p.geometry("300x100")
    p.attributes("-topmost", True)
    
    if mode == "Scale":
        s = tk.Scale(p, from_=0.5, to=2.0, resolution=0.1, orient="horizontal", label="Font Scale")
        s.set(current_scale)
        s.config(command=lambda v: apply_global_scale(v))
        s.pack(fill="x", padx=20)
    else:
        s = tk.Scale(p, from_=0.1, to=1.0, resolution=0.05, orient="horizontal", label="Transparency")
        s.set(root.attributes("-alpha"))
        s.config(command=lambda v: root.attributes("-alpha", float(v)))
        s.pack(fill="x", padx=20)

def apply_global_scale(val):
    global current_scale
    current_scale = float(val)
    new_size = int(BASE_FONT * current_scale)
    entry.config(font=(current_font, new_size))
    for btn in [calc_btn, clear_btn, prev_btn, next_btn]:
        btn.config(font=(current_font, int(new_size*0.7)))
    for lbl in [left_lbl, middle_lbl, right_lbl]:
        lbl.config(font=(current_font, new_size))
    draw_ai_lamp()

def enable_move():
    root.config(cursor="fleur")
    def start_move(e): root._x, root._y = e.x, e.y
    def do_move(e): root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

# ================== MENUS ==================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_m = tk.Menu(menubar, tearoff=0)
file_m.add_command(label="Pin/Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_m.add_command(label="Move Mode", command=enable_move)
menubar.add_cascade(label="File", menu=file_m)

view_m = tk.Menu(menubar, tearoff=0)
view_m.add_command(label="Themes", command=lambda: show_theme_picker(root, False))
view_m.add_command(label="Scale Window", command=lambda: open_control_popup("Scale"))
view_m.add_command(label="Transparency", command=lambda: open_control_popup("Alpha"))
menubar.add_cascade(label="View", menu=view_m)

timer_m = tk.Menu(menubar, tearoff=0)
timer_m.add_command(label="Timer Pro", command=lambda: TimerProWindow(tk.Toplevel(root)))
menubar.add_cascade(label="Timer", menu=timer_m)

ai_m = tk.Menu(menubar, tearoff=0)
ai_m.add_command(label="Toggle AI", command=toggle_ai)
menubar.add_cascade(label="AI", menu=ai_m)

draw_ai_lamp()
root.mainloop()