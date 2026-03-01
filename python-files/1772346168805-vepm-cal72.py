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
ai_delay_sec = 0  

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

# ================= THEME ENGINE (New) =================
# ألوان سامسونج One UI
SAMSUNG_BLUE = "#0371F1"
SAMSUNG_LIGHT_BG = "#F2F2F7"
SAMSUNG_DARK_BG = "#121212"
SAMSUNG_CARD_DARK = "#1C1C1E"

def apply_original_theme():
    root.config(bg="SystemButtonFace" if os.name == 'nt' else "white")
    entry.config(bg="white", fg="black", relief="sunken", bd=2)
    for btn in [calc_btn, clear_btn, prev_btn, next_btn]:
        btn.config(bg="SystemButtonFace", fg="black", relief="raised", bd=2)
    res.config(bg="SystemButtonFace")
    middle_lbl.config(bg="white", fg="black")

def apply_one_ui_light():
    root.config(bg=SAMSUNG_LIGHT_BG)
    entry.config(bg="white", fg="black", relief="flat", highlightthickness=1, highlightbackground="#D1D1D6")
    style_one_ui_btns(SAMSUNG_BLUE, "white")
    res.config(bg=SAMSUNG_LIGHT_BG)
    middle_lbl.config(bg="white", fg="black")

def apply_one_ui_dark():
    root.config(bg=SAMSUNG_DARK_BG)
    entry.config(bg=SAMSUNG_CARD_DARK, fg="white", relief="flat", highlightthickness=1, highlightbackground="#3A3A3C")
    style_one_ui_btns(SAMSUNG_BLUE, "white")
    res.config(bg=SAMSUNG_DARK_BG)
    middle_lbl.config(bg=SAMSUNG_CARD_DARK, fg="white")

def style_one_ui_btns(bg_color, fg_color):
    for btn in [calc_btn, clear_btn, prev_btn, next_btn]:
        btn.config(bg=bg_color, fg=fg_color, relief="flat", activebackground="#0056b3")

def open_themes_popup():
    p = tk.Toplevel(root)
    p.title("Themes")
    p.geometry("250x200")
    p.attributes("-topmost", True)
    tk.Label(p, text="Select UI Theme", font=("Segoe UI", 12, "bold")).pack(pady=10)
    
    tk.Button(p, text="Original Theme", width=20, command=apply_original_theme).pack(pady=5)
    tk.Button(p, text="One UI Light", width=20, bg="white", command=apply_one_ui_light).pack(pady=5)
    tk.Button(p, text="One UI Dark", width=20, bg="#121212", fg="white", command=apply_one_ui_dark).pack(pady=5)

# ================= TIMER (الموجود في مشروعك الأصلي) =================
timer_lbl = tk.Label(root,font=(current_font,int(BASE_FONT*0.9)),fg="blue")
timer_running=False
timer_after_id=None

def start_timer(delay_sec=0):
    global timer_running
    if timer_running: return
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
    else: l,r=0,0
    m=l+3

    left_lbl.config(text=l)
    right_lbl.config(text=r)
    middle_lbl.config(font=(current_font,int(BASE_FONT*current_scale*1.05)),pady=1,anchor="center")

    if ai_mode and v in AI_NEXT_VALUES:
        sign="<" if v<m else ">" if v>m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        start_timer(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
    else:
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}")
        stop_timer()

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode: auto_update()

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0,"end")
    entry.insert(0,(now.hour*60 + now.minute)%60)
    calculate()
    root.after(1000,auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size=int(BASE_FONT*current_scale*0.45*1.23) 
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

# ================= FUNCTIONS FOR SCALE/ALPHA =================
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
    tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha).pack(fill="x")

def enable_move():
    root.config(cursor="fleur")
    def start_move(e): root._x=e.x; root._y=e.y
    def do_move(e): root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")
    root.bind("<Button-1>",start_move)
    root.bind("<B1-Motion>",do_move)

def toggle_mode():
    global dark_mode
    dark_mode=not dark_mode
    bg=night_bg if dark_mode else day_bg
    fg="white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)

# ================== TIMERPRO CLASS (نافذة التايمر المنفصلة) ==================
class TimerProWindow:
    def __init__(self, parent):
        self.root = parent
        self.root.title("Timer 1")
        self.root.geometry("400x320")
        self.root.attributes("-topmost", True)
        self.timer_running = False
        self.timer_seconds = 0
        self.last_seconds = 0
        self.end_time = 0
        self.after_id = None
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        self.timer_lbl = tk.Label(self.main_frame, text="00:00", font=("Segoe UI", 36, "bold"))
        self.timer_lbl.pack(pady=12)
        
        self.time_entry = tk.Entry(self.main_frame, width=8, justify="center")
        self.time_entry.pack(pady=5)
        
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(pady=5)
        self.start_btn = tk.Button(btn_frame, text="Start", bg="#4CAF50", fg="white", command=self.start_timer)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(btn_frame, text="Stop", bg="#F44336", fg="white", command=self.stop_timer)
        self.stop_btn.pack(side="left", padx=5)
        
        tk.Button(self.main_frame, text="Timer Themes", command=self.open_timer_themes).pack(pady=5)

    def apply_timer_one_ui(self, dark=False):
        bg = SAMSUNG_DARK_BG if dark else SAMSUNG_LIGHT_BG
        fg = "white" if dark else "black"
        self.main_frame.config(bg=bg)
        self.timer_lbl.config(bg=bg, fg=fg)
        self.time_entry.config(bg=SAMSUNG_CARD_DARK if dark else "white", fg=fg)

    def open_timer_themes(self):
        tp = tk.Toplevel(self.root)
        tk.Button(tp, text="Original", command=lambda: self.apply_timer_one_ui(False)).pack(pady=2)
        tk.Button(tp, text="One UI Light", command=lambda: self.apply_timer_one_ui(False)).pack(pady=2)
        tk.Button(tp, text="One UI Dark", command=lambda: self.apply_timer_one_ui(True)).pack(pady=2)

    def start_timer(self):
        try:
            self.timer_seconds = int(self.time_entry.get()) * 60
            self.last_seconds = self.timer_seconds
            self.timer_running = True
            self.end_time = time.time() + self.timer_seconds
            self.tick()
        except: pass

    def tick(self):
        if self.timer_running:
            rem = self.end_time - time.time()
            if rem > 0:
                m, s = divmod(int(rem), 60)
                self.timer_lbl.config(text=f"{m:02d}:{s:02d}")
                self.after_id = self.root.after(100, self.tick)
            else: self.stop_timer()

    def stop_timer(self):
        self.timer_running = False
        if self.after_id: self.root.after_cancel(self.after_id)

    def close(self):
        self.stop_timer()
        self.root.destroy()

_timer1_window = None
def open_timer1_window():
    global _timer1_window
    if _timer1_window and tk.Toplevel.winfo_exists(_timer1_window):
        _timer1_window.lift()
        return
    _timer1_window = tk.Toplevel(root)
    TimerProWindow(_timer1_window)

# ================== MENUS ==================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda:root.attributes("-topmost",not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=enable_move)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_command(label="Themes", command=open_themes_popup)
view_menu.add_command(label="Scale", command=open_scale_popup)
view_menu.add_command(label="Transparency", command=open_alpha_popup)
menubar.add_cascade(label="View", menu=view_menu)

timer_menu = tk.Menu(menubar, tearoff=0)
timer_menu.add_command(label="Timer 1", command=open_timer1_window)
menubar.add_cascade(label="Timer", menu=timer_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
menubar.add_cascade(label="AI", menu=ai_menu)

root.mainloop()