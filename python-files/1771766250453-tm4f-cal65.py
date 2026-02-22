import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}
AI_NEXT_VALUES = {2,8,14,20,26,32,38,44,50,56}
LOSS_TRIGGERS = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
current_group_idx = 0
ai_mode = False
ai_delay_sec = 0  # delay for AI timer

# ================= TIMER FLAGS =================
timer_running = False
timer_after_id = None

loss_prep_running = False
loss_prep_after_id = None

loss_main_running = False
loss_main_after_id = None

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("500x400")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMERS =================
timer_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.9)), fg="blue")
loss_prep_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.85)), fg="darkorange")
loss_main_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.85)), fg="purple")

# ---- AI normal timer ----
def start_timer(delay=0):
    global timer_running
    if timer_running:
        return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    root.after(delay*1000, lambda: _countdown(60))

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
    m,s = divmod(sec,60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000,_countdown,sec-1)

# ---- Loss prep & main timers ----
def start_loss_prep(skip_target):
    global loss_prep_running
    if loss_prep_running:
        return
    loss_prep_running = True
    loss_prep_lbl.config(text="Loss prep: 01:00")
    loss_prep_lbl.pack(pady=1)
    _loss_prep_countdown(60, skip_target)

def stop_loss_prep():
    global loss_prep_running, loss_prep_after_id
    loss_prep_running = False
    if loss_prep_after_id:
        root.after_cancel(loss_prep_after_id)
    loss_prep_after_id = None
    loss_prep_lbl.pack_forget()

def _loss_prep_countdown(sec, skip_target):
    global loss_prep_after_id, loss_prep_running
    if not loss_prep_running:
        return
    if sec <=0:
        stop_loss_prep()
        start_loss_main(skip_target)
        return
    m,s = divmod(sec,60)
    loss_prep_lbl.config(text=f"Loss prep: {m:02d}:{s:02d}")
    loss_prep_after_id = root.after(1000,_loss_prep_countdown,sec-1,skip_target)

def start_loss_main(skip_target):
    global loss_main_running
    left = skip_target - 3
    mid = skip_target
    right = skip_target + 3
    left_lbl.config(text=left)
    middle_lbl.config(text=f"{mid} =", bg=ai_bg)
    right_lbl.config(text=right)

    now = datetime.now()
    current_mod = (now.hour*60 + now.minute)%60
    target_mod = skip_target%60
    delta_minutes = (target_mod - current_mod)%60
    secs_to_target = delta_minutes*60 - now.second
    if secs_to_target <0: secs_to_target=0

    loss_main_running = True
    loss_main_lbl.config(text=_format_mmss(secs_to_target))
    loss_main_lbl.pack(pady=1)
    _loss_main_countdown(secs_to_target,skip_target)

def stop_loss_main():
    global loss_main_running, loss_main_after_id
    loss_main_running = False
    if loss_main_after_id:
        root.after_cancel(loss_main_after_id)
    loss_main_after_id = None
    loss_main_lbl.pack_forget()

def _loss_main_countdown(sec, skip_target):
    global loss_main_after_id, loss_main_running
    if not loss_main_running:
        return
    if sec<=0:
        stop_loss_main()
        entry.delete(0,"end")
        entry.insert(0,str(skip_target))
        calculate()
        return
    loss_main_lbl.config(text=_format_mmss(sec))
    loss_main_after_id = root.after(1000,_loss_main_countdown,sec-1,skip_target)

def _format_mmss(total_seconds):
    m,s = divmod(int(total_seconds),60)
    return f"{m:02d}:{s:02d}"

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt)>2:
        return
    v=int(txt)
    for i in range(len(limits)-1):
        if limits[i]<=v<=limits[i+1]:
            l,r=limits[i],limits[i+1]
            break
    else:
        l,r=0,0
    m = l+3

    left_lbl.config(text=l)
    right_lbl.config(text=r)
    middle_lbl.config(font=(current_font,int(BASE_FONT*current_scale*1.05)),anchor="center",pady=1)
    middle_lbl.config(bg="white")  # افتراضي أبيض

    # AI behavior
    if ai_mode and v in AI_NEXT_VALUES:
        middle_lbl.config(text=f"{v} >\nNext", bg=ai_bg)
        start_timer(ai_delay_sec)
    elif v==m and v in SPECIAL_MIDDLES:
        stop_timer()
        middle_lbl.config(text=f"{m} =", bg="orange")
    else:
        stop_timer()
        sign = "<" if v<m else ">" if v>m else "="
        middle_lbl.config(text=f"{m} {sign}")

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()

def auto_update():
    if not ai_mode:
        return
    now=datetime.now()
    entry.delete(0,"end")
    entry.insert(0,(now.hour*60 + now.minute)%60)
    calculate()
    root.after(1000,auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size=int(BASE_FONT*current_scale*0.45*1.3)  # تكبير 30%
    ai_canvas.config(width=size+4,height=size+4)
    color="green" if ai_mode else "red"
    ai_canvas.create_oval(2,2,2+size,2+size,fill=color,outline="black")

# ================= LOSS =================
def loss_action():
    txt = entry.get().strip()
    if not txt.isdigit():
        messagebox.showinfo("Loss","أدخل قيمة صحيحة في الحقل ثم اضغط Loss.")
        return
    v=int(txt)
    if v not in LOSS_TRIGGERS:
        messagebox.showinfo("Loss",f"الـ Loss يعمل فقط عند القيم: {sorted(LOSS_TRIGGERS)}. القيمة الحالية: {v}")
        return
    skip_target = v+6
    stop_loss_prep()
    stop_loss_main()
    start_loss_prep(skip_target)
    messagebox.showinfo("Loss",f"Loss started: prep 01:00 → target {skip_target}")

# ================= MODES =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg="white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    middle_lbl.config(bg=bg)

def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

# ================= SCALE =================
def apply_scale(val):
    global current_scale
    current_scale=float(val)
    size=int(BASE_FONT*current_scale)
    btn_font_size = int(size*0.8)  # تصغير 20% لأزرار
    for w in [calc_btn, clear_btn, prev_btn, next_btn]:
        w.config(font=(current_font, btn_font_size))
    for w in [entry, left_lbl, middle_lbl, right_lbl]:
        w.config(font=(current_font,int(size*1.05)))
    lamp_size = int(size*0.45*1.3)  # تكبير لمبة 30%
    ai_canvas.config(width=lamp_size+4,height=lamp_size+4)
    draw_ai_lamp()

def open_scale_popup():
    p=tk.Toplevel(root)
    tk.Scale(p,from_=0.7,to=1.5,resolution=0.05,orient="horizontal",command=apply_scale).pack(fill="x")

# ================= GROUP NAV =================
def navigate(step):
    global current_group_idx
    current_group_idx=(current_group_idx+step)%(len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

# ================= AI TIMER DELAY =================
def edit_timer_popup():
    global ai_delay_sec
    p = tk.Toplevel(root)
    p.title("Edit Timer 1")
    tk.Label(p,text="Set AI Timer Delay (seconds)").pack()
    options = [-5,-4,-3,-2,-1,0,1,2,3,4,5]
    delay_var = tk.IntVar(value=ai_delay_sec)
    tk.OptionMenu(p,delay_var,*options).pack(pady=5)
    def save_delay():
        global ai_delay_sec
        ai_delay_sec = delay_var.get()
        p.destroy()
    tk.Button(p,text="Save",command=save_delay).pack(pady=5)

# ================= UI =================
entry = tk.Entry(root, justify="center", font=(current_font,BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>",calculate)

btns = tk.Frame(root)
btns.pack(pady=2)
calc_btn = tk.Button(btns,text="Generate",command=calculate)
calc_btn.pack(side="left",padx=3)
clear_btn = tk.Button(btns,text="Clear",command=lambda: entry.delete(0,"end"))
clear_btn.pack(side="left",padx=3)
prev_btn = tk.Button(btns,text="◀",command=lambda: navigate(-1))
prev_btn.pack(side="left",padx=3)
next_btn = tk.Button(btns,text="▶",command=lambda: navigate(1))
next_btn.pack(side="left",padx=3)
ai_canvas = tk.Canvas(btns,bd=0,highlightthickness=0)
ai_canvas.pack(side="left",padx=5)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=3)
left_lbl = tk.Label(res,width=6,bg="red",fg="black",font=(current_font,int(BASE_FONT*1.05)))
middle_lbl = tk.Label(res,width=6,bg="white",font=(current_font,int(BASE_FONT*1.05)))
right_lbl = tk.Label(res,width=6,bg="green",fg="black",font=(current_font,int(BASE_FONT*1.05)))
left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

# ================= MENU =================
menubar=tk.Menu(root)
root.config(menu=menubar)

file_menu=tk.Menu(menubar,tearoff=0)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="Move Window",command=lambda: enable_move())
menubar.add_cascade(label="File",menu=file_menu)

view_menu=tk.Menu(menubar,tearoff=0)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_command(label="Scale",command=open_scale_popup)
view_menu.add_command(label="Transparency",command=lambda: open_alpha_popup())
menubar.add_cascade(label="View",menu=view_menu)

ai_menu=tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI",command=toggle_ai)
ai_menu.add_command(label="Loss",command=loss_action)
ai_menu.add_command(label="Edit Timer 1",command=edit_timer_popup)
menubar.add_cascade(label="AI",menu=ai_menu)

# ================= TRANSPARENCY =================
def apply_alpha(val):
    root.attributes("-alpha",float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.title("Transparency")
    s = tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha)
    s.set(root.attributes("-alpha"))
    s.pack()
    tk.Button(p,text="Close",command=p.destroy).pack(pady=3)

# ================= MOVE =================
move_mode = False
def enable_move():
    global move_mode
    move_mode = True
    root.config(cursor="fleur")

def start_move(e):
    if move_mode:
        root._x = e.x
        root._y = e.y

def move_window(e):
    if move_mode:
        root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")

def stop_move(e):
    global move_mode
    move_mode = False
    root.config(cursor="")

root.bind("<Button-1>",start_move)
root.bind("<B1-Motion>",move_window)
root.bind("<ButtonRelease-1>",stop_move)
root.bind("<Left>",lambda e: navigate(-1))
root.bind("<Right>",lambda e: navigate(1))

root.mainloop()