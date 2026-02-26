import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

# ------------------- Trade Table -------------------
trade_table = [["01:00:00 prepare", "01:00:30", "01:01:00 go trade"], ["01:01:30 prepare", "01:02:00", "01:02:30 go trade"], ["01:03:00 prepare", "01:03:30", "01:04:00 go trade"], ["01:04:30 prepare", "01:05:00", "01:05:30 go trade"], ["01:06:00 prepare", "01:06:30", "01:07:00 go trade"], ["01:07:30 prepare", "01:08:00", "01:08:30 go trade"], ["01:09:00 prepare", "01:09:30", "01:10:00 go trade"], ["01:10:30 prepare", "01:11:00", "01:11:30 go trade"], ["01:12:00 prepare", "01:12:30", "01:13:00 go trade"], ["01:13:30 prepare", "01:14:00", "01:14:30 go trade"]] # عينة مختصرة للجدول

# ------------------- Themes -------------------
THEMES = {
    "Classic": {"bg": "#F0F0F0", "card": "white", "fg": "black", "btn": "#E1E1E1", "acc": "red"},
    "Dark Pro": {"bg": "#121212", "card": "#1E1E1E", "fg": "#E0E0E0", "btn": "#333", "acc": "#FF5252"},
    "Royal": {"bg": "#0D0D0D", "card": "#1A1A1A", "fg": "#D4AF37", "btn": "#262626", "acc": "#FFD700"},
    "Cyber": {"bg": "#000814", "card": "#001D3D", "fg": "#00F5D4", "btn": "#003566", "acc": "#F15BB5"}
}

# ------------------- Globals -------------------
curr_theme = "Classic"
ai_enabled = False
timer_visible = True
current_group_idx = 0
ai_after_id = None
timer_after_id = None

# ------------------- Logic -------------------
def parse_time_str(s):
    try: return datetime.strptime(s.split()[0], "%H:%M:%S").time()
    except: return None

def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    card1.config(text=trade_table[idx][0].split()[0]) # عرض الوقت فقط للاختصار
    card2.config(text=trade_table[idx][1])
    card3.config(text="GO" if "go" in trade_table[idx][2].lower() else trade_table[idx][2])

def update_timer_logic():
    global timer_after_id
    if not ai_enabled or not timer_visible:
        timer_label.config(text="")
        return
    now = datetime.now()
    curr_total = now.minute * 60 + now.second
    t_go = parse_time_str(trade_table[current_group_idx][2])
    target_go = t_go.minute * 60 + t_go.second
    diff = target_go - curr_total
    
    if 0 < diff <= 30:
        timer_label.config(text=f"Prep: {diff}s", fg="red")
    elif -10 <= diff <= 0:
        timer_label.config(text="GO!!", fg="orange")
    else:
        timer_label.config(text="")
    timer_after_id = root.after(1000, update_timer_logic)

def on_generate(event=None):
    if ai_enabled:
        now = datetime.now()
        curr = now.minute * 60 + now.second
        idx = 0
        for i, g in enumerate(trade_table):
            if curr <= (parse_time_str(g[2]).minute * 60 + parse_time_str(g[2]).second):
                idx = i; break
        display_group(idx)
    else:
        try:
            m = int(entry.get().split(":")[0])
            for i, g in enumerate(trade_table):
                if parse_time_str(g[0]).minute >= m:
                    display_group(i); break
        except: pass
    return "break"

def toggle_ai():
    global ai_enabled, ai_after_id
    ai_enabled = not ai_enabled
    draw_ai_lamp()
    if ai_enabled:
        def loop():
            now = datetime.now()
            entry.delete(0, tk.END)
            entry.insert(0, f"{now.minute:02d}:{now.second:02d}")
            on_generate(); update_timer_logic()
            global ai_after_id
            ai_after_id = root.after(1000, loop)
        loop()
    else:
        if ai_after_id: root.after_cancel(ai_after_id)
        if timer_after_id: root.after_cancel(timer_after_id)
        timer_label.config(text=""); entry.delete(0, tk.END); entry.insert(0, "0")

# ------------------- UI -------------------
def apply_theme(name):
    global curr_theme
    curr_theme = name
    t = THEMES[name]
    root.config(bg=t["bg"])
    for f in [top_f, ctrl_f, display_f]: f.config(bg=t["bg"])
    entry.config(bg=t["card"], fg=t["fg"], insertbackground=t["fg"])
    timer_label.config(bg=t["bg"])
    for c in [card1, card2, card3]: c.config(bg=t["card"], fg=t["fg"])
    for b in [btn_gen, btn_clr, btn_pre, btn_nxt]: b.config(bg=t["btn"], fg=t["fg"])
    draw_ai_lamp()

def open_scale():
    win = tk.Toplevel(root); win.title("Scale")
    def change(v):
        s = int(float(v))
        entry.config(font=("Segoe UI", s+4))
        for c in [card1, card2, card3]: c.config(font=("Segoe UI", max(8, s-4), "bold"))
        timer_label.config(font=("Segoe UI", max(8, s-4), "bold"))
        root.geometry(f"{int(380 * (s/14))}x{int(220 * (s/14))}") # حجم صغير جداً
    tk.Scale(win, from_=8, to=24, orient="horizontal", command=change).pack(padx=20, pady=10)

root = tk.Tk()
root.title("Mini Bot")
root.geometry("380x220") # البداية بحجم صغير جداً
root.attributes("-topmost", True)

top_f = tk.Frame(root); top_f.pack(pady=2)
entry = tk.Entry(top_f, justify="center", font=("Segoe UI", 16), width=12); entry.pack()
entry.bind("<Return>", on_generate)
entry.insert(0, "0")

ctrl_f = tk.Frame(root); ctrl_f.pack(pady=2)
btn_gen = tk.Button(ctrl_f, text="Gen", command=on_generate, font=("Segoe UI", 9)); btn_gen.pack(side="left", padx=1)
btn_clr = tk.Button(ctrl_f, text="C", command=lambda: [c.config(text="") for c in [card1, card2, card3]], font=("Segoe UI", 9)); btn_clr.pack(side="left", padx=1)
btn_pre = tk.Button(ctrl_f, text="◀", command=lambda: display_group(current_group_idx-1)); btn_pre.pack(side="left", padx=1)
btn_nxt = tk.Button(ctrl_f, text="▶", command=lambda: display_group(current_group_idx+1)); btn_nxt.pack(side="left", padx=1)

ai_canvas = tk.Canvas(ctrl_f, width=12, height=12, bd=0, highlightthickness=0); ai_canvas.pack(side="left", padx=3)
def draw_ai_lamp():
    ai_canvas.delete("all"); ai_canvas.config(bg=THEMES[curr_theme]["bg"])
    ai_canvas.create_oval(2, 2, 10, 10, fill="green" if ai_enabled else "red")

timer_label = tk.Label(root, text="", font=("Segoe UI", 10, "bold")); timer_label.pack()

display_f = tk.Frame(root); display_f.pack(expand=True, fill="x", padx=10, pady=2)
card1 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), relief="groove", width=10); card1.grid(row=0, column=0, padx=1)
card2 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), relief="groove", width=10); card2.grid(row=0, column=1, padx=1)
card3 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), relief="groove", width=10); card3.grid(row=0, column=2, padx=1)
display_f.columnconfigure((0,1,2), weight=1)

# Menus
m = tk.Menu(root)
f_m = tk.Menu(m, tearoff=0); f_m.add_command(label="Pin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost"))); f_m.add_command(label="Exit", command=root.quit); m.add_cascade(label="File", menu=f_m)
v_m = tk.Menu(m, tearoff=0); v_m.add_command(label="Theme", command=lambda: [apply_theme("Dark Pro") if curr_theme=="Classic" else apply_theme("Classic")]); v_m.add_command(label="Scale", command=open_scale); m.add_cascade(label="View", menu=v_m)
a_m = tk.Menu(m, tearoff=0); a_m.add_command(label="AI", command=toggle_ai); m.add_cascade(label="AI", menu=a_m)
root.config(menu=m)

apply_theme("Classic")
root.mainloop()