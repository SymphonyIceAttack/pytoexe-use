import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os
import time

# =========================
# Range Calculator (main)
# =========================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 0.7  # default scale as requested (0.3 - 1.0), start at 0.7
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}
AI_NEXT_VALUES = {2,8,14,20,26,32,38,44,50,56}

topmost = True
dark_mode = False
ai_mode = False
current_group_idx = 0
ai_delay_sec = 0  # default delay in seconds

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("520x400")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMER label used by Range Calculator AI timer =================
timer_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.9)), fg="blue")
timer_running = False
timer_after_id = None

def start_timer(delay_sec=0):
    global timer_running
    if timer_running:
        return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    root.after(delay_sec*1000, _countdown, 60)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id:
        root.after_cancel(timer_after_id)
    timer_after_id = None
    timer_lbl.pack_forget()

def _countdown(sec):
    global timer_after_id, timer_running
    if not timer_running:
        return
    if sec <= 0:
        stop_timer()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000, _countdown, sec-1)

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        return
    v = int(txt)
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    else:
        l, r = 0, 0
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)
    middle_lbl.config(font=(current_font,int(BASE_FONT*current_scale*1.05)), pady=1, anchor="center")

    # AI behavior
    if ai_mode and v in AI_NEXT_VALUES:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        start_timer(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
    else:
        middle_lbl.config(text=f"{m} {'<' if v < m else '>' if v > m else '='}", bg="white")
        stop_timer()

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, "end")
    entry.insert(0, (now.hour*60 + now.minute) % 60)
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.45 * 1.23) # 23% bigger
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2,2,2+size,2+size, fill=color, outline="black")

# ================= MANUAL NAV =================
def prev_group(event=None):
    global current_group_idx
    current_group_idx = (current_group_idx - 1) % (len(limits)-1)
    entry.delete(0, "end")
    entry.insert(0, limits[current_group_idx])
    calculate()

def next_group(event=None):
    global current_group_idx
    current_group_idx = (current_group_idx + 1) % (len(limits)-1)
    entry.delete(0, "end")
    entry.insert(0, limits[current_group_idx])
    calculate()

# ================= UI =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=2)
btn_width = int(BASE_FONT * current_scale * 0.9 * 0.88) # 12% smaller
calc_btn = tk.Button(btns, text="Generate", command=calculate)
calc_btn.pack(side="left", padx=3)
clear_btn = tk.Button(btns, text="Clear", command=lambda: entry.delete(0, "end"))
clear_btn.pack(side="left", padx=3)
prev_btn = tk.Button(btns, text="◀", command=prev_group)
prev_btn.pack(side="left", padx=3)
next_btn = tk.Button(btns, text="▶", command=next_group)
next_btn.pack(side="left", padx=3)
ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=4)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=3)
left_lbl = tk.Label(res, width=6, bg="red", fg="black", font=(current_font, int(BASE_FONT*1.05)))
middle_lbl = tk.Label(res, width=6, bg="white", font=(current_font, int(BASE_FONT*1.05)))
right_lbl = tk.Label(res, width=6, bg="green", fg="black", font=(current_font, int(BASE_FONT*1.05)))
left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

# ================= AI MENU =================
def edit_ai_timer():
    def apply_delay(val):
        global ai_delay_sec
        ai_delay_sec = int(val)
    p = tk.Toplevel(root)
    p.title("Edit Timer 1")
    p.geometry("300x100")
    tk.Label(p, text="Delay seconds (-5 to +5)").pack()
    scale = tk.Scale(p, from_=-5, to=5, orient="horizontal", command=apply_delay)
    scale.set(0)
    scale.pack(fill="x")
    tk.Button(p, text="X", command=p.destroy).pack()

# ================= TimerPro class (used for separate Timer window) =================
SAVE_FILE = "last_time.txt"
BASE_FONT_SIZE = 48
BASE_BTN_FONT = 10
BASE_WIDTH_T = 420
BASE_HEIGHT_T = 380

class TimerPro:
    def __init__(self, window):
        # window can be Tk or Toplevel
        self.root = window
        self.root.title("Timer Pro")
        self.root.geometry(f"{BASE_WIDTH_T}x{BASE_HEIGHT_T}")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # ================= STATE =================
        self.timer_running = False
        self.timer_seconds = self.load_time()
        self.last_seconds = self.timer_seconds
        self.end_time = 0
        self.after_id = None
        self.mini_mode = False

        self.current_scale = 0.7   # default as requested
        self.current_font = "Segoe UI"
        self.dark_mode = False

        # ================= BINDINGS =================
        self.root.bind("<Escape>", lambda e: self.stop_timer())
        self.root.bind("<space>", lambda e: self.toggle_timer())
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.setup_ui()
        self.apply_scaling(self.current_scale)
        self.update_timer_display()

    # Persistence
    def save_time(self, sec):
        try:
            with open(SAVE_FILE, "w") as f:
                f.write(str(int(sec)))
        except:
            pass

    def load_time(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    # UI
    def setup_ui(self):
        self.timer_lbl = tk.Label(self.root, text="00:00", font=(self.current_font, BASE_FONT_SIZE, "bold"))
        self.timer_lbl.pack(pady=15)

        self.entry_frame = tk.Frame(self.root)
        self.entry_frame.pack(pady=5)

        self.entry_lbl = tk.Label(self.entry_frame, text="M:S or Min:", font=(self.current_font, 10))
        self.entry_lbl.pack(side="left", padx=5)

        self.time_entry = tk.Entry(self.entry_frame, width=8, font=(self.current_font, 14), justify="center")
        self.time_entry.pack(side="left")
        self.time_entry.bind("<Return>", self.start_timer)

        self.presets_frame = tk.Frame(self.root)
        self.presets_frame.pack(pady=10)

        self.preset_buttons = []
        for sec in [390, 360, 300, 60]:
            m, s = divmod(sec, 60)
            b = tk.Button(self.presets_frame, text=f"{m:02d}:{s:02d}", width=6,
                          command=lambda x=sec: self.set_time(x))
            b.pack(side="left", padx=3)
            self.preset_buttons.append(b)

        self.progress_canvas = tk.Canvas(self.root, height=6, bg="#eee", highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=30, pady=15)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 6, fill="#2196F3", outline="")

        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(pady=10)

        self.btn_start = tk.Button(self.controls_frame, text="START", width=12, command=self.start_timer)
        self.btn_stop  = tk.Button(self.controls_frame, text="STOP",  width=12, command=self.stop_timer)
        self.btn_reset = tk.Button(self.controls_frame, text="RESET", width=10, command=self.reset_timer)

        for b in (self.btn_start, self.btn_stop, self.btn_reset):
            b.pack(side="left", padx=5)

        self.control_buttons = [self.btn_start, self.btn_stop, self.btn_reset]
        self.main_widgets = [self.entry_frame, self.presets_frame, self.progress_canvas, self.controls_frame]

        # Menu inside TimerPro (keeps minimal)
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Mini Mode", command=self.toggle_mini)
        view_menu.add_command(label="Scale Window", command=self.open_scale_popup)
        menubar.add_cascade(label="View", menu=view_menu)

    # Timer core
    def update_timer_display(self):
        m, s = divmod(int(self.timer_seconds), 60)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
        self.root.update_idletasks()
        w = self.progress_canvas.winfo_width()
        ratio = (self.timer_seconds / self.last_seconds) if self.last_seconds else 0
        self.progress_canvas.coords(self.progress_bar, 0, 0, w * ratio, 6)

    def tick(self):
        if self.timer_running:
            now = time.time()
            remaining = self.end_time - now
            if remaining > 0:
                self.timer_seconds = remaining
                self.update_timer_display()
                self.after_id = self.root.after(100, self.tick)
            else:
                self.timer_running = False
                self.timer_seconds = 0
                self.update_timer_display()
                self.finished_flash()

    def finished_flash(self):
        for i in range(8):
            color = "red" if i % 2 == 0 else "black"
            self.timer_lbl.config(fg=color)
            self.root.update()
            time.sleep(0.15)
        self.timer_lbl.config(fg="black")

    def toggle_timer(self, event=None):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self, event=None):
        val = self.time_entry.get().strip()
        if val:
            try:
                if ":" in val:
                    parts = val.split(":")
                    if len(parts) != 2:
                        raise ValueError
                    m, s = int(parts[0]), int(parts[1])
                    if s < 0 or s >= 60 or m < 0:
                        raise ValueError
                    self.set_time(m * 60 + s)
                else:
                    m = int(val)
                    if m < 0:
                        raise ValueError
                    self.set_time(m * 60)
            except ValueError:
                self.time_entry.delete(0, tk.END)
                return
            self.time_entry.delete(0, tk.END)

        if self.timer_seconds > 0 and not self.timer_running:
            self.timer_running = True
            self.end_time = time.time() + self.timer_seconds
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.tick()

    def stop_timer(self, event=None):
        self.timer_running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def reset_timer(self):
        self.stop_timer()
        self.timer_seconds = self.last_seconds
        self.update_timer_display()

    def set_time(self, sec):
        self.stop_timer()
        self.timer_seconds = sec
        self.last_seconds = sec
        self.save_time(sec)
        self.update_timer_display()

    # View features for TimerPro
    def toggle_day_night(self):
        self.dark_mode = not self.dark_mode
        bg = "#2E2E2E" if self.dark_mode else "white"
        fg = "white" if self.dark_mode else "black"
        self.root.config(bg=bg)
        self.timer_lbl.config(bg=bg, fg=fg)

    def open_alpha_popup(self):
        p = tk.Toplevel(self.root)
        p.title("Transparency")
        tk.Scale(p, from_=0.3, to=1.0, resolution=0.05,
                 orient="horizontal",
                 command=lambda v: self.root.attributes("-alpha", float(v))).pack(fill="x")
        tk.Button(p, text="Close", command=p.destroy).pack()

    def open_scale_popup(self):
        p = tk.Toplevel(self.root)
        p.title("Scale")
        sc = tk.Scale(
            p,
            from_=0.3,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            command=lambda v: self.apply_scaling(float(v))
        )
        sc.set(self.current_scale)
        sc.pack(fill="x", padx=10)
        tk.Button(p, text="Close", command=p.destroy).pack()

    def apply_scaling(self, scale):
        self.current_scale = scale
        tf = int(BASE_FONT_SIZE * scale)
        uf = int(BASE_BTN_FONT * scale)
        self.timer_lbl.config(font=(self.current_font, tf, "bold"))
        for b in self.preset_buttons + self.control_buttons:
            b.config(font=(self.current_font, uf))
        if not self.mini_mode:
            for w in self.main_widgets:
                w.pack_configure(pady=int(5*scale))
            self.root.geometry(f"{int(BASE_WIDTH_T*scale)}x{int(BASE_HEIGHT_T*scale)}")
        else:
            self.root.geometry(f"{int(220*scale)}x{int(100*scale)}")

    # Move
    def start_move(self, event):
        self.root._x = event.x
        self.root._y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.root._x)
        y = self.root.winfo_y() + (event.y - self.root._y)
        self.root.geometry(f"+{x}+{y}")

    def toggle_mini(self):
        self.mini_mode = not self.mini_mode
        if self.mini_mode:
            for w in self.main_widgets:
                w.pack_forget()
            self.root.geometry(f"{int(220*self.current_scale)}x{int(100*self.current_scale)}")
        else:
            self.apply_scaling(self.current_scale)

# ================= MENU FUNCTIONS for Range Calculator =================
# open_timer1 will create one TimerPro Toplevel and avoid duplicates
_timer1_window = None
def open_timer1():
    global _timer1_window
    try:
        if _timer1_window and tk.Toplevel.winfo_exists(_timer1_window):
            _timer1_window.lift()
            return
    except:
        pass
    _timer1_window = tk.Toplevel(root)
    TimerPro(_timer1_window)

# ================= MENU for Range Calculator =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=lambda: enable_move())
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=lambda: toggle_mode())
view_menu.add_command(label="Scale", command=lambda: open_scale_popup())
view_menu.add_command(label="Transparency", command=lambda: open_alpha_popup())
menubar.add_cascade(label="View", menu=view_menu)

# Extra (Timer) menu placed after View and before AI
extra_menu = tk.Menu(menubar, tearoff=0)
extra_menu.add_command(label="Timer 1", command=open_timer1)
menubar.add_cascade(label="Extra", menu=extra_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Edit Timer 1", command=edit_ai_timer)
menubar.add_cascade(label="AI", menu=ai_menu)

# ================= SCALE / TRANSPARENCY for Range Calculator =================
def apply_scale(val):
    global current_scale
    current_scale = float(val)
    size = int(BASE_FONT * current_scale)
    for w in [entry, calc_btn, clear_btn, prev_btn, next_btn, left_lbl, middle_lbl, right_lbl]:
        try:
            w.config(font=(current_font, int(size*1.05)))
        except:
            pass
    draw_ai_lamp()

def open_scale_popup():
    p = tk.Toplevel(root)
    p.title("Scale")
    sc = tk.Scale(p, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", command=apply_scale)
    sc.set(current_scale)
    sc.pack(fill="x")
    tk.Button(p, text="Close", command=p.destroy).pack()

def apply_alpha(val):
    root.attributes("-alpha", float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.title("Transparency")
    tk.Label(p, text="Transparency").pack()
    sc = tk.Scale(p, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", command=apply_alpha)
    sc.set(float(root.attributes("-alpha") if isinstance(root.attributes("-alpha"), str) else 0.95))
    sc.pack(fill="x")
    tk.Button(p, text="X", command=p.destroy).pack()

# ================= MOVE WINDOW for Range Calculator =================
def enable_move():
    root.config(cursor="fleur")
    def start_move(e):
        root._x = e.x
        root._y = e.y
    def do_move(e):
        root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

# ================= MODES =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)
    middle_lbl.config(bg="white")

# ================= KEY BINDINGS =================
root.bind("<Left>", prev_group)
root.bind("<Right>", next_group)

# ================= START =================
if __name__ == "__main__":
    root.mainloop()