import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os
import time

# ================== RANGE CALCULATOR (البرنامج الرئيسي كما أرسلته) ==================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
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
root.geometry("520x400")   # لم أغير هذه الأبعاد كما طلبت
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMER (الموجود في مشروعك الأصلي — أتركته كما هو) =================
timer_lbl = tk.Label(root,font=(current_font,int(BASE_FONT*0.9)),fg="blue")
timer_running=False
timer_after_id=None

def start_timer(delay_sec=0):
    global timer_running
    if timer_running:
        return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    root.after(delay_sec*1000,_countdown,60)

def stop_timer():
    global timer_running,timer_after_id
    timer_running=False
    if timer_after_id:
        root.after_cancel(timer_after_id)
    timer_after_id=None
    timer_lbl.pack_forget()

def _countdown(sec):
    global timer_after_id,timer_running
    if not timer_running: return
    if sec<=0:
        stop_timer()
        return
    m,s=divmod(sec,60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id=root.after(1000,_countdown,sec-1)

# ================= CALCULATE =================
def calculate(event=None):
    txt=entry.get().strip()
    if not txt.isdigit() or len(txt)>2: return
    v=int(txt)
    for i in range(len(limits)-1):
        if limits[i]<=v<=limits[i+1]:
            l,r=limits[i],limits[i+1]
            break
    else:
        l,r=0,0
    m=l+3

    left_lbl.config(text=l)
    right_lbl.config(text=r)
    middle_lbl.config(font=(current_font,int(BASE_FONT*current_scale*1.05)),pady=1,anchor="center")

    # AI behavior
    if ai_mode and v in AI_NEXT_VALUES:
        sign="<" if v<m else ">" if v>m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        start_timer(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
    else:
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg="white")
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
    entry.delete(0,"end")
    entry.insert(0,(now.hour*60 + now.minute)%60)
    calculate()
    root.after(1000,auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size=int(BASE_FONT*current_scale*0.45*1.23) # 23% أكبر
    ai_canvas.config(width=size+4,height=size+4)
    color="green" if ai_mode else "red"
    ai_canvas.create_oval(2,2,2+size,2+size,fill=color,outline="black")

# ================= MANUAL NAV =================
def prev_group(event=None):
    global current_group_idx
    current_group_idx=(current_group_idx-1)%(len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

def next_group(event=None):
    global current_group_idx
    current_group_idx=(current_group_idx+1)%(len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

# ================= UI =================
entry=tk.Entry(root,justify="center",font=(current_font,BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>",calculate)

btns=tk.Frame(root)
btns.pack(pady=2)
btn_width=int(BASE_FONT*current_scale*0.9*0.88) # 12% أصغر
calc_btn=tk.Button(btns,text="Generate",command=calculate)
calc_btn.pack(side="left",padx=3)
clear_btn=tk.Button(btns,text="Clear",command=lambda: entry.delete(0,"end"))
clear_btn.pack(side="left",padx=3)
prev_btn=tk.Button(btns,text="◀",command=prev_group)
prev_btn.pack(side="left",padx=3)
next_btn=tk.Button(btns,text="▶",command=next_group)
next_btn.pack(side="left",padx=3)
ai_canvas=tk.Canvas(btns,bd=0,highlightthickness=0)
ai_canvas.pack(side="left",padx=4)
draw_ai_lamp()

res=tk.Frame(root)
res.pack(pady=3)
left_lbl=tk.Label(res,width=6,bg="red",fg="black",font=(current_font,int(BASE_FONT*1.05)))
middle_lbl=tk.Label(res,width=6,bg="white",font=(current_font,int(BASE_FONT*1.05)))
right_lbl=tk.Label(res,width=6,bg="green",fg="black",font=(current_font,int(BASE_FONT*1.05)))
left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

# ================= AI MENU (سنترك مكانها كما هو) =================
def edit_ai_timer():
    def apply_delay(val):
        global ai_delay_sec
        ai_delay_sec=int(val)
    p=tk.Toplevel(root)
    p.title("Edit Timer 1")
    p.geometry("300x100")
    tk.Label(p,text="Delay seconds (-5 to +5)").pack()
    scale=tk.Scale(p,from_=-5,to=5,orient="horizontal",command=apply_delay)
    scale.set(0)
    scale.pack(fill="x")
    tk.Button(p,text="X",command=p.destroy).pack()

# ================= SCALE / TRANSPARENCY =================
def apply_scale(val):
    global current_scale
    current_scale=float(val)
    size=int(BASE_FONT*current_scale)
    for w in [entry,calc_btn,clear_btn,prev_btn,next_btn,left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,int(size*1.05)))
    draw_ai_lamp()

def open_scale_popup():
    p=tk.Toplevel(root)
    tk.Scale(p,from_=0.7,to=1.5,resolution=0.05,orient="horizontal",command=apply_scale).pack(fill="x")

def apply_alpha(val):
    root.attributes("-alpha",float(val))

def open_alpha_popup():
    p=tk.Toplevel(root)
    tk.Label(p,text="Transparency").pack()
    tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha).pack(fill="x")
    tk.Button(p,text="X",command=p.destroy).pack()

# ================= MOVE WINDOW =================
def enable_move():
    root.config(cursor="fleur")
    def start_move(e):
        root._x=e.x
        root._y=e.y
    def do_move(e):
        root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")
    root.bind("<Button-1>",start_move)
    root.bind("<B1-Motion>",do_move)

# ================= MODES =================
def toggle_mode():
    global dark_mode
    dark_mode=not dark_mode
    bg=night_bg if dark_mode else day_bg
    fg="white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    middle_lbl.config(bg="white")

root.bind("<Left>",prev_group)
root.bind("<Right>",next_group)

# ================== TIMERPRO CLASS (نافذة التايمر المنفصلة) ==================
# هذه نسخة مستقلة من التايمر التي طلبتها — سنستخدمها داخل Toplevel
TIMER_SAVE_FILE = "timer_last_time.txt"

class TimerProWindow:
    def __init__(self, parent):
        # parent expected to be a tk.Toplevel instance
        self.root = parent
        self.root.title("Timer 1")
        # لا نغير خصائص البرنامج الرئيسي — هنا نافذة منفصلة صغيرة
        self.root.geometry("400x300")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # State
        self.timer_running = False
        self.timer_seconds = self.load_time()
        self.last_seconds = self.timer_seconds
        self.end_time = 0
        self.after_id = None
        self.blink_state = False
        self.mini_mode = False
        self.current_scale = 1.0
        self.current_font = "Segoe UI"

        # Key Bindings
        self.root.bind("<Escape>", lambda e: self.stop_timer())
        self.root.bind("<space>", lambda e: self.toggle_timer())

        # build UI
        self.setup_ui()

        # ensure we stop timer when closed
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def save_time(self, sec):
        try:
            with open(TIMER_SAVE_FILE, "w") as f:
                f.write(str(sec))
        except: pass

    def load_time(self):
        if os.path.exists(TIMER_SAVE_FILE):
            try:
                with open(TIMER_SAVE_FILE) as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    def setup_ui(self):
        # Timer Label
        self.timer_lbl = tk.Label(self.root, text="00:00", font=(self.current_font, 36, "bold"))
        self.timer_lbl.pack(pady=12)

        # Entry
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(pady=6)
        tk.Label(entry_frame, text="M or M:S").pack(side="left", padx=6)
        self.time_entry = tk.Entry(entry_frame, width=8, justify="center", font=(self.current_font, 12))
        self.time_entry.pack(side="left")
        self.time_entry.bind("<Return>", self.start_timer)

        # Presets
        presets_frame = tk.Frame(self.root)
        presets_frame.pack(pady=8)
        presets = [6*60+30, 6*60, 5*60, 3*60]
        for s in presets:
            m, sec = divmod(s, 60)
            btn = tk.Button(presets_frame, text=f"{m:02d}:{sec:02d}", width=6, command=lambda ss=s: self.set_time(ss))
            btn.pack(side="left", padx=3)

        # Progress
        self.progress_canvas = tk.Canvas(self.root, height=6, bg="#eee", highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=20, pady=8)
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 6, fill="#2196F3", outline="")

        # Controls + Close
        controls = tk.Frame(self.root)
        controls.pack(pady=8)
        tk.Button(controls, text="Start (Space)", command=self.start_timer, width=10, bg="#4CAF50", fg="white").pack(side="left", padx=4)
        tk.Button(controls, text="Stop (Esc)", command=self.stop_timer, width=10, bg="#F44336", fg="white").pack(side="left", padx=4)
        tk.Button(controls, text="Reset", command=self.reset_timer, width=8).pack(side="left", padx=4)
        tk.Button(controls, text="Close", command=self.close, width=8).pack(side="left", padx=6)

    def update_timer_display(self):
        # show integer mm:ss
        m, s = divmod(int(self.timer_seconds), 60) if self.timer_seconds>=0 else (0,0)
        self.timer_lbl.config(text=f"{m:02d}:{s:02d}")

        w = self.progress_canvas.winfo_width() or 360
        ratio = (self.timer_seconds / self.last_seconds) if self.last_seconds > 0 else 0
        self.progress_canvas.coords(self.progress_bar, 0, 0, w * ratio, 6)

        if self.timer_running and self.timer_seconds <= 10 and self.timer_seconds > 0:
            color = "red" if int(time.time() * 2) % 2 == 0 else "black"
            self.timer_lbl.config(fg=color)
        else:
            self.timer_lbl.config(fg="black")

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
        # use after-based flashing (no sleep)
        def flash(count):
            if count < 8:
                color = "red" if count % 2 == 0 else "black"
                self.timer_lbl.config(fg=color)
                self.root.after(150, lambda: flash(count+1))
            else:
                self.timer_lbl.config(fg="black")
        flash(0)

    def start_timer(self, event=None):
        # validation: M or M:S
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
                    self.set_time(m*60 + s)
                else:
                    m = int(val)
                    if m < 0: raise ValueError
                    self.set_time(m*60)
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

    def toggle_timer(self, event=None):
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def reset_timer(self):
        self.stop_timer()
        self.timer_seconds = self.last_seconds
        self.update_timer_display()

    def set_time(self, sec):
        self.stop_timer()
        self.timer_seconds = float(sec)
        self.last_seconds = float(sec)
        self.update_timer_display()
        self.save_time(int(sec))

    def close(self):
        # stop timer and destroy window
        self.stop_timer()
        try:
            self.root.destroy()
        except:
            pass

# ================== Hook menu item "Timer 1" to open TimerProWindow ==================
# Keep reference to avoid garbage collection and to prevent multiple windows
_timer1_window = None
_timer1_app = None

def open_timer1_window():
    global _timer1_window, _timer1_app
    # If window exists and not destroyed, focus it
    if _timer1_window and tk.Toplevel.winfo_exists(_timer1_window):
        _timer1_window.lift()
        return
    # create Toplevel and instantiate TimerProWindow inside it
    _timer1_window = tk.Toplevel(root)
    _timer1_app = TimerProWindow(_timer1_window)
    # ensure the created timer window follows a reasonable size and position
    try:
        _timer1_window.geometry("400x300")
    except:
        pass

# ================== MENUS (File, View, Timer, AI) — order preserved as requested ==================
menubar = tk.Menu(root)
root.config(menu=menubar)

# File (same as your program)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin",command=lambda:root.attributes("-topmost",not root.attributes("-topmost")))
file_menu.add_command(label="Move Window",command=lambda:enable_move())
menubar.add_cascade(label="File",menu=file_menu)

# View (same as your program)
view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night",command=lambda:toggle_mode())
view_menu.add_command(label="Scale",command=lambda:open_scale_popup())
view_menu.add_command(label="Transparency",command=lambda:open_alpha_popup())
menubar.add_cascade(label="View",menu=view_menu)

# Timer (new menu requested) — contains "Timer 1" item
timer_menu = tk.Menu(menubar, tearoff=0)
timer_menu.add_command(label="Timer 1", command=open_timer1_window)
menubar.add_cascade(label="Timer", menu=timer_menu)

# AI (as in your program)
ai_menu = tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI",command=toggle_ai)
ai_menu.add_command(label="Edit Timer 1",command=edit_ai_timer)
menubar.add_cascade(label="AI",menu=ai_menu)

# ================== START MAINLOOP ==================
root.mainloop()