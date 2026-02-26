import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

# ------------------- Trade Table -------------------
trade_table = [
    ["01:00:00 prepare", "01:00:30", "01:01:00 go trade"],
    ["01:01:30 prepare", "01:02:00", "01:02:30 go trade"],
    ["01:03:00 prepare", "01:03:30", "01:04:00 go trade"],
    ["01:04:30 prepare", "01:05:00", "01:05:30 go trade"],
    ["01:06:00 prepare", "01:06:30", "01:07:00 go trade"],
    ["01:07:30 prepare", "01:08:00", "01:08:30 go trade"],
    ["01:09:00 prepare", "01:09:30", "01:10:00 go trade"],
    ["01:10:30 prepare", "01:11:00", "01:11:30 go trade"],
    ["01:12:00 prepare", "01:12:30", "01:13:00 go trade"],
    ["01:13:30 prepare", "01:14:00", "01:14:30 go trade"],
    ["01:15:00 prepare", "01:15:30", "01:16:00 go trade"],
    ["01:16:30 prepare", "01:17:00", "01:17:30 go trade"],
    ["01:18:00 prepare", "01:18:30", "01:19:00 go trade"],
    ["01:19:30 prepare", "01:20:00", "01:20:30 go trade"],
    ["01:21:00 prepare", "01:21:30", "01:22:00 go trade"],
    ["01:22:30 prepare", "01:23:00", "01:23:30 go trade"],
    ["01:24:00 prepare", "01:24:30", "01:25:00 go trade"],
    ["01:25:30 prepare", "01:26:00", "01:26:30 go trade"],
    ["01:27:00 prepare", "01:27:30", "01:28:00 go trade"],
    ["01:28:30 prepare", "01:29:00", "01:29:30 go trade"],
    ["01:30:00 prepare", "01:30:30", "01:31:00 go trade"],
    ["01:31:30 prepare", "01:32:00", "01:32:30 go trade"],
    ["01:33:00 prepare", "01:33:30", "01:34:00 go trade"],
    ["01:34:30 prepare", "01:35:00", "01:35:30 go trade"],
    ["01:36:00 prepare", "01:36:30", "01:37:00 go trade"],
    ["01:37:30 prepare", "01:38:00", "01:38:30 go trade"],
    ["01:39:00 prepare", "01:39:30", "01:40:00 go trade"],
    ["01:40:30 prepare", "01:41:00", "01:41:30 go trade"],
    ["01:42:00 prepare", "01:42:30", "01:43:00 go trade"],
    ["01:43:30 prepare", "01:44:00", "01:44:30 go trade"],
    ["01:45:00 prepare", "01:45:30", "01:46:00 go trade"],
    ["01:46:30 prepare", "01:47:00", "01:47:30 go trade"],
    ["01:48:00 prepare", "01:48:30", "01:49:00 go trade"],
    ["01:49:30 prepare", "01:50:00", "01:50:30 go trade"],
    ["01:51:00 prepare", "01:51:30", "01:52:00 go trade"],
    ["01:52:30 prepare", "01:53:00", "01:53:30 go trade"],
    ["01:54:00 prepare", "01:54:30", "01:55:00 go trade"],
    ["01:55:30 prepare", "01:56:00", "01:56:30 go trade"],
    ["01:57:00 prepare", "01:57:30", "01:58:00 go trade"],
    ["01:58:30 prepare", "01:59:00", "01:59:30 go trade"]
]

THEMES = {
    "Classic": {"bg": "#F5F5F5", "card": "white", "fg": "black", "btn": "#E0E0E0", "acc": "red", "lbl": "#333"},
    "Dark Pro": {"bg": "#121212", "card": "#1E1E1E", "fg": "#E0E0E0", "btn": "#333", "acc": "#FF5252", "lbl": "#BB86FC"},
    "Royal": {"bg": "#0D0D0D", "card": "#1A1A1A", "fg": "#D4AF37", "btn": "#262626", "acc": "#FFD700", "lbl": "#D4AF37"},
    "Cyber": {"bg": "#000814", "card": "#001D3D", "fg": "#00F5D4", "btn": "#003566", "acc": "#F15BB5", "lbl": "#9B5DE5"}
}

curr_theme = "Classic"
ai_enabled = False
timer_visible = True
current_group_idx = 0
ai_after_id = None
timer_after_id = None

def parse_time_str(s):
    try: return datetime.strptime(s.split()[0], "%H:%M:%S").time()
    except: return None

def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    card1.config(text=trade_table[idx][0])
    card2.config(text=trade_table[idx][1])
    card3.config(text=trade_table[idx][2])

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
        timer_label.config(text=f"PREP: {diff}s", fg=THEMES[curr_theme]["acc"])
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
            val = entry.get().split(":")[0]
            m = int(val)
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
            on_generate()
            update_timer_logic()
            global ai_after_id
            ai_after_id = root.after(1000, loop)
        loop()
    else:
        if ai_after_id: root.after_cancel(ai_after_id)
        if timer_after_id: root.after_cancel(timer_after_id)
        timer_label.config(text="")
        entry.delete(0, tk.END); entry.insert(0, "0")

def apply_theme(name):
    global curr_theme
    curr_theme = name
    t = THEMES[name]
    root.config(bg=t["bg"])
    top_f.config(bg=t["bg"])
    ctrl_f.config(bg=t["bg"])
    display_f.config(bg=t["bg"])
    entry.config(bg=t["card"], fg=t["fg"], insertbackground=t["fg"])
    timer_label.config(bg=t["bg"])
    for c in [card1, card2, card3]:
        c.config(bg=t["card"], fg=t["fg"], highlightbackground=t["lbl"])
    for b in [btn_gen, btn_clr, btn_pre, btn_nxt]:
        b.config(bg=t["btn"], fg=t["fg"], activebackground=t["acc"])
    draw_ai_lamp()

def open_theme_picker():
    pop = tk.Toplevel(root)
    pop.title("Themes")
    for tn in THEMES.keys():
        tk.Button(pop, text=tn, width=15, command=lambda n=tn: [apply_theme(n), pop.destroy()]).pack(pady=2)

def open_scale():
    win = tk.Toplevel(root); win.title("Scale")
    def change(v):
        s = int(float(v))
        entry.config(font=("Segoe UI", s+4))
        for c in [card1, card2, card3]: c.config(font=("Segoe UI", max(6, s-2), "bold"))
        timer_label.config(font=("Segoe UI", max(8, s-1), "bold"))
        # تعديل ديناميكي للنافذة لتصغيرها جداً
        root.geometry(f"{int(380 * (s/14))}x{int(220 * (s/14))}")
    # السكيل يبدأ من 6 للسماح بتصغير فائق
    tk.Scale(win, from_=6, to=24, orient="horizontal", command=change).pack(padx=20, pady=10)

root = tk.Tk()
root.title("Lite Bot")
root.geometry("380x220") # البداية بحجم ملموم جداً
root.attributes("-topmost", True)

# --- Top Section (Compact) ---
top_f = tk.Frame(root)
top_f.pack(pady=2)
entry = tk.Entry(top_f, justify="center", font=("Segoe UI", 16), width=8, relief="flat")
entry.pack()
entry.insert(0, "0")
entry.bind("<Return>", on_generate)

# --- Control Section (Compact) ---
ctrl_f = tk.Frame(root)
ctrl_f.pack(pady=2)
btn_gen = tk.Button(ctrl_f, text="Gen", command=on_generate, relief="flat", padx=5)
btn_gen.pack(side="left", padx=1)
btn_clr = tk.Button(ctrl_f, text="Cl", command=lambda: [c.config(text="") for c in [card1, card2, card3]], relief="flat")
btn_clr.pack(side="left", padx=1)
btn_pre = tk.Button(ctrl_f, text="◀", command=lambda: display_group(current_group_idx-1), relief="flat")
btn_pre.pack(side="left", padx=1)
btn_nxt = tk.Button(ctrl_f, text="▶", command=lambda: display_group(current_group_idx+1), relief="flat")
btn_nxt.pack(side="left", padx=1)

ai_canvas = tk.Canvas(ctrl_f, width=12, height=12, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=3)
def draw_ai_lamp():
    ai_canvas.delete("all")
    ai_canvas.config(bg=THEMES[curr_theme]["bg"])
    ai_canvas.create_oval(2, 2, 10, 10, fill="green" if ai_enabled else "red", outline=THEMES[curr_theme]["fg"])

# --- Timer (Very Compact) ---
timer_label = tk.Label(root, text="", font=("Segoe UI", 11, "bold"))
timer_label.pack(pady=0)

# --- Display Section (Horizontal & Close) ---
display_f = tk.Frame(root)
display_f.pack(expand=True, fill="x", padx=10, pady=2)

card1 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), pady=5, width=12, relief="groove", bd=1)
card1.grid(row=0, column=0, padx=1, sticky="ew")
card2 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), pady=5, width=12, relief="groove", bd=1)
card2.grid(row=0, column=1, padx=1, sticky="ew")
card3 = tk.Label(display_f, text="", font=("Segoe UI", 10, "bold"), pady=5, width=12, relief="groove", bd=1)
card3.grid(row=0, column=2, padx=1, sticky="ew")

display_f.columnconfigure(0, weight=1)
display_f.columnconfigure(1, weight=1)
display_f.columnconfigure(2, weight=1)

# --- Menubar ---
menubar = tk.Menu(root)
view_m = tk.Menu(menubar, tearoff=0)
view_m.add_command(label="Themes", command=open_theme_picker)
view_m.add_command(label="Scale", command=open_scale)
menubar.add_cascade(label="View", menu=view_m)
root.config(menu=menubar)

apply_theme("Classic")
root.mainloop()