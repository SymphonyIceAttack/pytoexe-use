import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT_SIZE = 16
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}
AI_NEXT_VALUES = {2, 8, 14, 20, 26, 32, 38, 44, 50, 56}
EXTRA_TRIGGER_VALUES = {4, 10, 16, 22, 28, 34, 40, 46, 52, 58}

ai_mode = False
extra_timers_enabled = False   # يتحكم به من قايمة AI -> Extra Timers
ai_delay_sec = 0

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calc")
root.geometry("420x380")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

# ================= UI SETUP (اعمدة النتائج) =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT_SIZE))
entry.pack(pady=10)
entry.bind("<Return>", lambda e: calculate())

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Generate", command=lambda: calculate()).pack(side="left", padx=2)
tk.Button(btn_frame, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=2)
tk.Button(btn_frame, text="◀", command=lambda: navigate(-1)).pack(side="left", padx=2)
tk.Button(btn_frame, text="▶", command=lambda: navigate(1)).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btn_frame, width=20, height=20, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

res_frame = tk.Frame(root)
res_frame.pack(pady=6, fill="x")

left_lbl = tk.Label(res_frame, width=6, height=2, bg="red", fg="black", font=(current_font, BASE_FONT_SIZE))
middle_lbl = tk.Label(res_frame, width=6, height=2, bg="white", fg="black", font=(current_font, BASE_FONT_SIZE))
right_lbl = tk.Label(res_frame, width=6, height=2, bg="green", fg="black", font=(current_font, BASE_FONT_SIZE))

# اجعلهم في سطر واحد وعلى اليسار (مش في منتصف الشاشة)
left_lbl.pack(side="left", padx=2, anchor="w")
middle_lbl.pack(side="left", padx=2, anchor="w")
right_lbl.pack(side="left", padx=2, anchor="w")

# ================ SINGLE TIMER (في سطر واحد، CENTRED تحت المربعات) ================
timers_row = tk.Frame(root)
timers_row.pack(fill="x", padx=8, pady=6)

# تايمر واحد فقط، بدون لون خلفية ظاهر (يتبع خلفية الإطار)
timer_lbl = tk.Label(timers_row, text="", width=20, relief="flat", anchor="center", font=(current_font, BASE_FONT_SIZE))
timer_lbl.pack()  # مركز افتراضياً داخل fill="x"

# ================= after ID و حالة التتابع =================
t_after_id = None
seq_stage = 0  # 0=idle, 1=timer1, 2=timer2, 3=timer3

def cancel_after():
    global t_after_id
    if t_after_id:
        try:
            root.after_cancel(t_after_id)
        except Exception:
            pass
        t_after_id = None

# ================= TIMERS SEQUENCE LOGIC =================
def run_stage(stage, sec):
    """
    stage: 1,2,3
    عند انتهاء كل stage ينتقل للمرحلة التالية فقط إذا extra_timers_enabled وكان مطلوب
    لا يعيد التشغيل تلقائياً بعد انتهاء التتابع.
    """
    global t_after_id, seq_stage
    cancel_after()
    seq_stage = stage

    # لو خلصت العدّاغ
    if sec < 0:
        # أخفي النص
        timer_lbl.config(text="", bg=timer_lbl.master.cget("bg"))
        # قرر الانتقال
        if stage == 1:
            if extra_timers_enabled:
                # انتقل للـ 2
                run_stage(2, 60)
            else:
                seq_stage = 0
        elif stage == 2:
            if extra_timers_enabled:
                run_stage(3, 60)
            else:
                seq_stage = 0
        else:
            seq_stage = 0
        return

    m, s = divmod(sec, 60)
    # خلفية التايمر لا تظهر لون - نجعلها نفس خلفية الإطار
    timer_lbl.config(text=f"Timer{stage} {m:02d}:{s:02d}", bg=timer_lbl.master.cget("bg"))
    t_after_id = root.after(1000, lambda: run_stage(stage, sec - 1))

def start_sequence(start_stage=1):
    """
    ابدأ التتابع من مرحلة محددة:
    - start_stage=1: تشغيل Timer1 ثم (اختياري) 2 ثم 3
    - start_stage=2: تشغيل Timer2 ثم (اختياري) 3
    - start_stage=3: تشغيل Timer3 فقط
    ملاحظة: المراحل 2 و3 تعمل فقط إذا extra_timers_enabled True
    """
    # منع التشغيل إذا المرحلة غير مسموح بها
    if start_stage not in (1,2,3):
        start_stage = 1
    if start_stage > 1 and not extra_timers_enabled:
        return
    # إلغاء أي تايمر شغال
    cancel_after()
    run_stage(start_stage, 60)

def stop_sequence():
    cancel_after()
    timer_lbl.config(text="", bg=timer_lbl.master.cget("bg"))
    global seq_stage
    seq_stage = 0

# ================= CALCULATE / NAVIGATION =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit():
        return
    v = int(txt)

    l, r = 0, 0
    for i in range(len(limits) - 1):
        if limits[i] <= v < limits[i + 1]:
            l, r = limits[i], limits[i + 1]
            break
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    if ai_mode:
        # سلوك AI محفوظ كما كان
        if v in AI_NEXT_VALUES:
            sign = "<" if v < m else ">" if v > m else "="
            middle_lbl.config(text=f"{v} {sign}\nNext", bg="#ADD8E6")
            # شغّل التتابع ابتداءً من Timer1 (لن يعيد نفسه تلقائياً بعد الانتهاء)
            start_sequence(1)

        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            # إذا Extra مفعل، ابدأ من Timer2
            if extra_timers_enabled:
                start_sequence(2)

        elif v in EXTRA_TRIGGER_VALUES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            # إذا Extra مفعل، ابدأ من Timer3
            if extra_timers_enabled:
                start_sequence(3)

        else:
            middle_lbl.config(text=f"{m} {'<' if v < m else '>' if v > m else '='}", bg="white")
    else:
        bg_col = "orange" if v in SPECIAL_MIDDLES else "white"
        middle_lbl.config(text=f"{m} {'<' if v < m else '>' if v > m else '='}", bg=bg_col)

def navigate(step):
    try:
        val = int(entry.get())
    except:
        val = 0
    entry.delete(0, tk.END)
    entry.insert(0, str((val + step) % 60))
    calculate()

# ================= AI & MENUS =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()
    else:
        # لا نوقف التتابع تلقائياً عند إطفاء AI (اتركته كما كان)
        pass

def toggle_extra():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    if not extra_timers_enabled:
        # لو طفيت Extra توقف أي مراحل 2/3 إن كانت شغالة
        if seq_stage in (2,3):
            stop_sequence()
    messagebox.showinfo("Extra Timers", "ON" if extra_timers_enabled else "OFF")

def auto_update():
    if not ai_mode:
        return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0, str(now.minute))
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black")

# ================= MENU FUNCTIONS (حافظ على كل الخصائص كما هي) =================
def toggle_mode():
    # Day / Night toggle — نحتفظ بالخيار
    is_dark = root.cget("bg") != "white"
    if is_dark:
        new_bg = "white"; new_fg = "black"
        entry.config(bg="white", fg="black", insertbackground="black")
    else:
        new_bg = "#2E2E2E"; new_fg = "white"
        entry.config(bg="#444", fg="white", insertbackground="white")

    root.config(bg=new_bg)
    btn_frame.config(bg=new_bg)
    res_frame.config(bg=new_bg)
    timers_row.config(bg=new_bg)
    for lbl in [left_lbl, middle_lbl, right_lbl]:
        lbl.config(fg=new_fg)

def set_delay(v):
    global ai_delay_sec
    ai_delay_sec = int(float(v))

def apply_scale(v):
    global current_scale
    current_scale = float(v)
    sz = int(BASE_FONT_SIZE * current_scale)
    entry.config(font=(current_font, sz))
    for lbl in [left_lbl, middle_lbl, right_lbl, timer_lbl]:
        lbl.config(font=(current_font, sz))

def enable_move():
    def start_move(e):
        root._x, root._y = e.x, e.y
    def do_move(e):
        root.geometry(f"+{e.x_root - root._x}+{e.y_root - root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)
    root.config(cursor="fleur")

def open_popup(title, f, t, cmd):
    p = tk.Toplevel(root)
    p.title(title)
    tk.Scale(p, from_=f, to=t, resolution=0.05 if f < 1 else 1, orient="horizontal", command=cmd).pack(padx=20, pady=20)

# ================= MENUS (ماشية زي ما طلبت) =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=enable_move)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_command(label="Scale", command=lambda: open_popup("Scale", 0.7, 1.5, apply_scale))
view_menu.add_command(label="Transparency", command=lambda: open_popup("Alpha", 0.3, 1.0, lambda v: root.attributes("-alpha", float(v))))
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Extra Timers", command=toggle_extra)
ai_menu.add_command(label="Edit Timer 1", command=lambda: open_popup("Delay", -5, 5, set_delay))
menubar.add_cascade(label="AI", menu=ai_menu)

# ================ بداية التشغيل: لا نشغل أي تايمر تلقائياً (إلا لو أردت) ================
# إذا تحب تشغيل Timer1 عند فتح البرنامج: فك التعليق على السطر التالي
# start_sequence(1)

draw_ai_lamp()
root.mainloop()