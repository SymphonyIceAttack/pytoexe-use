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

# ================= UI SETUP (اعمدة النتائج + تايمرز في سطر واحد) =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT_SIZE))
entry.pack(pady=10)
# زرار generate بـ Enter
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

# ================ TIMERS ROW (كل التايمرات على سطر واحد، من غير ما أحطهم فوق) ================
timers_row = tk.Frame(root)
timers_row.pack(fill="x", padx=8, pady=6, anchor="w")   # يظهر على اليسار وليس في نص الشاشة

timer1_lbl = tk.Label(timers_row, text="", width=12, relief="groove", anchor="w", font=(current_font, BASE_FONT_SIZE))
timer2_lbl = tk.Label(timers_row, text="", width=12, relief="groove", anchor="w", font=(current_font, BASE_FONT_SIZE))
timer3_lbl = tk.Label(timers_row, text="", width=12, relief="groove", anchor="w", font=(current_font, BASE_FONT_SIZE))

# رتبهم أفقياً — وتأكد أنهم يظهروا على سطر واحد
timer1_lbl.pack(side="left", padx=(0,6))
timer2_lbl.pack(side="left", padx=(0,6))
timer3_lbl.pack(side="left", padx=(0,6))

# ================= after IDs لكل تايمر =================
t1_after_id = None
t2_after_id = None
t3_after_id = None

# وظائف مساعدة لإلغاء أي after موجود
def cancel_after(ref_name):
    aid = globals().get(ref_name)
    if aid:
        try:
            root.after_cancel(aid)
        except Exception:
            pass
        globals()[ref_name] = None

# ================= TIMERS SEQUENCE LOGIC =================
# timer1 دائمًا يُشغّل (يبدأ عند تشغيل البرنامج) — و عند انتهاءه: يختفي ثم (لو Extra ON) يبدأ timer2، وإلا يرجع timer1
def run_timer1(sec):
    global t1_after_id
    cancel_after("t1_after_id")
    if sec < 0:
        # انتهاء timer1: امسح نصه واذهب للتالى إذا مفعل
        timer1_lbl.config(text="", bg=timer1_lbl.master.cget("bg"))
        if extra_timers_enabled:
            # ابدأ التايمر الثاني
            start_timer2()
        else:
            # ابدأ timer1 من أول جديد (حلقة مستمرة)
            start_timer1(ai_delay_sec)
        return

    # عرض الوقت و تمييزه كـ running
    m, s = divmod(sec, 60)
    timer1_lbl.config(text=f"Timer1 {m:02d}:{s:02d}", bg="#fff8b3")  # مصفر خفيف للتأشير
    t1_after_id = root.after(1000, lambda: run_timer1(sec - 1))

def start_timer1(delay=0):
    # cancel أي instance
    cancel_after("t1_after_id")
    # ابدء بعد التأخير المحدد (delay بالثواني)
    if delay and delay > 0:
        t = int(delay * 1000)
        cancel_after("t1_after_id")
        t1_after_id = root.after(t, lambda: run_timer1(60))
        globals()["t1_after_id"] = t1_after_id
    else:
        run_timer1(60)

def stop_timer1():
    cancel_after("t1_after_id")
    timer1_lbl.config(text="", bg=timer1_lbl.master.cget("bg"))

# التايمر الثاني: يظهر بعد انتهاء الأول (لو Extra ON) ثم يختفي ويبدأ الثالث (لو Extra ON)
def run_timer2(sec):
    global t2_after_id
    cancel_after("t2_after_id")
    if sec < 0:
        timer2_lbl.config(text="", bg=timer2_lbl.master.cget("bg"))
        # بعد انتهاء الثانية ابدأ الثالثة فقط إذا Extra ON
        if extra_timers_enabled:
            start_timer3()
        else:
            # ارجع الأول
            start_timer1(0)
        return

    m, s = divmod(sec, 60)
    timer2_lbl.config(text=f"Timer2 {m:02d}:{s:02d}", bg="#d0f0d0")
    t2_after_id = root.after(1000, lambda: run_timer2(sec - 1))

def start_timer2():
    # فقط لو Extra مُفعل
    if not extra_timers_enabled:
        return
    cancel_after("t2_after_id")
    run_timer2(60)

def stop_timer2():
    cancel_after("t2_after_id")
    timer2_lbl.config(text="", bg=timer2_lbl.master.cget("bg"))

# التايمر الثالث: يظهر بعد الثانية ثم يرجع للأول
def run_timer3(sec):
    global t3_after_id
    cancel_after("t3_after_id")
    if sec < 0:
        timer3_lbl.config(text="", bg=timer3_lbl.master.cget("bg"))
        # بعد انتهاء third ارجع الأول
        start_timer1(0)
        return

    m, s = divmod(sec, 60)
    timer3_lbl.config(text=f"Timer3 {m:02d}:{s:02d}", bg="#e6d0f0")
    t3_after_id = root.after(1000, lambda: run_timer3(sec - 1))

def start_timer3():
    if not extra_timers_enabled:
        return
    cancel_after("t3_after_id")
    run_timer3(60)

def stop_timer3():
    cancel_after("t3_after_id")
    timer3_lbl.config(text="", bg=timer3_lbl.master.cget("bg"))

def stop_all_extra():
    stop_timer2()
    stop_timer3()

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
        # في حالة AI: نتحكم بعرض middle وبتشغيل timer1 / 2 /3 وفق القيم
        if v in AI_NEXT_VALUES:
            sign = "<" if v < m else ">" if v > m else "="
            middle_lbl.config(text=f"{v} {sign}\nNext", bg="#ADD8E6")
            # هنا نترك timer1 يعمل بشكل مستقل (مبدئياً يعمل تلقائياً)
            # إذا أردت تشغيله عند شروط معينة، يمكن تعديل هذا السطر
            start_timer1(ai_delay_sec)

        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            # SPECIAL triggers timer2 (لكن لن يعمل إذا Extra OFF)
            if extra_timers_enabled:
                start_timer2()

        elif v in EXTRA_TRIGGER_VALUES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            # EXTRA_TRIGGER => شغل تايمر3 فقط إذا Extra ON
            if extra_timers_enabled:
                start_timer3()

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
        # عند إيقاف AI نوقف أي تحديث تلقائي لكن نسمح لتسلسل التايمرز بالاستمرار
        # إذا أردت أن إيقاف AI يوقف التايمرز قم بإلغاء التعليق التالي:
        # stop_timer1(); stop_all_extra()
        pass

def toggle_extra():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    if not extra_timers_enabled:
        # اذا طفيت Extra لازم نتأكد ان timer2/3 ماتشتغلش ونرجع timer1 يشتغل
        stop_all_extra()
        # إذا كان timer1 مخفي (لأنه انتهى وكان ينتظر extra) نعيد تشغيله
        if not t1_after_id:
            start_timer1(0)
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
    # Day / Night toggle — نحتفظ بالخيار كما طلبت
    is_dark = root.cget("bg") != "white"
    if is_dark:
        # إلى يومي
        new_bg = "white"
        new_fg = "black"
        entry.config(bg="white", fg="black", insertbackground="black")
    else:
        # إلى داكن
        new_bg = "#2E2E2E"
        new_fg = "white"
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
    for lbl in [left_lbl, middle_lbl, right_lbl, timer1_lbl, timer2_lbl, timer3_lbl]:
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

# ================ بدء التشغيل: شغّل Timer1 تلقائياً كما طلبت ================
draw_ai_lamp()
start_timer1(ai_delay_sec)

root.mainloop()