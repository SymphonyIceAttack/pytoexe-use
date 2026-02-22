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
AI_SPECIALS = {2,8,14,20,26,32,38,44,50,56}

topmost = True
dark_mode = False
history = []
move_mode = False
current_group_idx = 0
ai_mode = False

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("500x300")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

# ================= FUNCTIONS =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        return

    v = int(txt)
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break

    m = l + 3
    
    # Default middle text and color
    middle_text = f"{m} {'=' if v==m else '<' if v<m else '>'}"
    middle_bg = night_bg if dark_mode else "white"
    middle_font = (current_font, int(BASE_FONT*current_scale*1.05))
    middle_lbl.config(pady=0)  # إعادة الوضع الطبيعي

    # AI-specific display
    if ai_mode and v in AI_SPECIALS:
        # الرقم + علامة أصغر + next أصغر + مسافة أقل
        scaled_size = int(BASE_FONT * current_scale * 1.5 * 0.8)  # تصغير 20%
        middle_text = f"{v} <\nnext"
        middle_font = (current_font, scaled_size)
        middle_bg = "#ADD8E6"  # لبني فاتح
        middle_lbl.config(pady=2)  # قلل المسافة بين الرقم و next

    # Manual special middles
    elif v == m and v in SPECIAL_MIDDLES:
        middle_bg = "orange"

    middle_lbl.config(text=middle_text, bg=middle_bg, justify="center", font=middle_font)
    left_lbl.config(text=l)
    right_lbl.config(text=r)

    add_history(v,l,m,r)

# ================= HISTORY =================
def add_history(v,l,m,r):
    ts = datetime.now().strftime("%H:%M:%S")
    history.append(f"{v} → {l}-{m}-{r} | {ts}")

def open_history():
    w = tk.Toplevel(root)
    w.title("History")
    t = tk.Text(w)
    t.pack(fill="both",expand=True)
    for h in history:
        t.insert("end",h+"\n")

# ================= MODES =================
night_bg = "#2E2E2E"
day_bg = "white"

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"

    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    middle_lbl.config(bg="white")
    draw_ai_lamp()

def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

# ================= SCALE =================
def apply_scale(val):
    global current_scale
    current_scale = float(val)
    size = int(BASE_FONT*current_scale)

    entry.config(font=(current_font,size))
    for w in [calc_btn, clear_btn, prev_btn, next_btn]:
        w.config(font=(current_font,int(size*0.8)))

    for w in [left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,int(size*1.05)))

    draw_ai_lamp()

def open_scale_popup():
    p = tk.Toplevel(root)
    tk.Scale(
        p,
        from_=0.7,
        to=1.5,
        resolution=0.05,
        orient="horizontal",
        command=apply_scale
    ).pack(fill="x")

# ================= GROUP NAV =================
def prev_group(event=None):
    global current_group_idx
    current_group_idx = (current_group_idx - 1) % (len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

def next_group(event=None):
    global current_group_idx
    current_group_idx = (current_group_idx + 1) % (len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.45 * 1.3)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2,2,2+size,2+size,fill=color,outline="black")

def auto_update():
    if not ai_mode:
        return
    now = datetime.now()
    entry.delete(0,"end")
    entry.insert(0,(now.hour*60 + now.minute) % 60)
    calculate()
    root.after(1000, auto_update)

# ================= UI =================
entry = tk.Entry(root, justify="center", font=(current_font,BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=2)

calc_btn = tk.Button(btns,text="Generate",command=calculate)
calc_btn.pack(side="left",padx=3)

clear_btn = tk.Button(btns,text="Clear",command=lambda: entry.delete(0,"end"))
clear_btn.pack(side="left",padx=3)

prev_btn = tk.Button(btns,text="◀",command=prev_group)
prev_btn.pack(side="left",padx=3)

next_btn = tk.Button(btns,text="▶",command=next_group)
next_btn.pack(side="left",padx=3)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left",padx=4)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=5)

left_lbl = tk.Label(res,width=6,bg="red",fg="white")
middle_lbl = tk.Label(res,width=6,bg="white")
right_lbl = tk.Label(res,width=6,bg="green",fg="white")

left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar,tearoff=0)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="History",command=open_history)
menubar.add_cascade(label="File",menu=file_menu)

view_menu = tk.Menu(menubar,tearoff=0)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_command(label="Scale",command=open_scale_popup)
menubar.add_cascade(label="View",menu=view_menu)

ai_menu = tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI",command=toggle_ai)
menubar.add_cascade(label="AI",menu=ai_menu)

root.bind("<Left>",prev_group)
root.bind("<Right>",next_group)

root.mainloop()