import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

# ------------------- Trade Table -------------------
trade_table = [
    ["01:00:00 prepare","01:00:30","01:01:00 go trade"],
    ["01:01:30 prepare","01:02:00","01:02:30 go trade"],
    ["01:03:00 prepare","01:03:30","01:04:00 go trade"],
    ["01:04:30 prepare","01:05:00","01:05:30 go trade"],
    ["01:06:00 prepare","01:06:30","01:07:00 go trade"],
    ["01:07:30 prepare","01:08:00","01:08:30 go trade"],
    ["01:09:00 prepare","01:09:30","01:10:00 go trade"],
    ["01:10:30 prepare","01:11:00","01:11:30 go trade"],
    ["01:12:00 prepare","01:12:30","01:13:00 go trade"],
    ["01:13:30 prepare","01:14:00","01:14:30 go trade"],
    ["01:15:00 prepare","01:15:30","01:16:00 go trade"],
    ["01:16:30 prepare","01:17:00","01:17:30 go trade"],
    ["01:18:00 prepare","01:18:30","01:19:00 go trade"],
    ["01:19:30 prepare","01:20:00","01:20:30 go trade"],
    ["01:21:00 prepare","01:21:30","01:22:00 go trade"],
    ["01:22:30 prepare","01:23:00","01:23:30 go trade"],
    ["01:24:00 prepare","01:24:30","01:25:00 go trade"],
    ["01:25:30 prepare","01:26:00","01:26:30 go trade"],
    ["01:27:00 prepare","01:27:30","01:28:00 go trade"],
    ["01:28:30 prepare","01:29:00","01:29:30 go trade"],
    ["01:30:00 prepare","01:30:30","01:31:00 go trade"],
    ["01:31:30 prepare","01:32:00","01:32:30 go trade"],
    ["01:33:00 prepare","01:33:30","01:34:00 go trade"],
    ["01:34:30 prepare","01:35:00","01:35:30 go trade"],
    ["01:36:00 prepare","01:36:30","01:37:00 go trade"],
    ["01:37:30 prepare","01:38:00","01:38:30 go trade"],
    ["01:39:00 prepare","01:39:30","01:40:00 go trade"],
    ["01:40:30 prepare","01:41:00","01:41:30 go trade"],
    ["01:42:00 prepare","01:42:30","01:43:00 go trade"],
    ["01:43:30 prepare","01:44:00","01:44:30 go trade"],
    ["01:45:00 prepare","01:45:30","01:46:00 go trade"],
    ["01:46:30 prepare","01:47:00","01:47:30 go trade"],
    ["01:48:00 prepare","01:48:30","01:49:00 go trade"],
    ["01:49:30 prepare","01:50:00","01:50:30 go trade"],
    ["01:51:00 prepare","01:51:30","01:52:00 go trade"],
    ["01:52:30 prepare","01:53:00","01:53:30 go trade"],
    ["01:54:00 prepare","01:54:30","01:55:00 go trade"],
    ["01:55:30 prepare","01:56:00","01:56:30 go trade"],
    ["01:57:00 prepare","01:57:30","01:58:00 go trade"],
    ["01:58:30 prepare","01:59:00","01:59:30 go trade"]
]

# ------------------- Globals -------------------
BASE_FONT = 14
current_font = "Segoe UI"
current_group_idx = 0
ai_enabled = False
timer_visible = True
ai_after_id = None
timer_after_id = None

# ------------------- Themes Data -------------------
THEMES = {
    "Classic": {"bg": "white", "fg": "black", "btn_bg": "#f0f0f0", "text_bg": "white", "accent": "red"},
    "Modern Dark": {"bg": "#1e1e2e", "fg": "#cdd6f4", "btn_bg": "#313244", "text_bg": "#181825", "accent": "#f38ba8"},
    "Blue Sky": {"bg": "#e0f2fe", "fg": "#0369a1", "btn_bg": "#bae6fd", "text_bg": "#f0f9ff", "accent": "#e11d48"},
    "Cyberpunk": {"bg": "#2b213a", "fg": "#00ff9f", "btn_bg": "#44335e", "text_bg": "#1a1a2e", "accent": "#ff0055"}
}

# ------------------- Logic -------------------
def parse_time_str(s):
    try: return datetime.strptime(s.split()[0], "%H:%M:%S").time()
    except: return None

def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    output.config(state="normal")
    output.delete("1.0", tk.END)
    for l in trade_table[idx]:
        output.insert(tk.END, l+"\n")
    output.config(state="disabled")

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
        timer_label.config(text=f"{diff}s prepare", fg="red")
    elif -10 <= diff <= 0:
        timer_label.config(text="GO", fg="orange")
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
            minute = int(entry.get().split(":")[0])
            for i, g in enumerate(trade_table):
                if parse_time_str(g[0]).minute >= minute:
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
    t = THEMES[name]
    root.config(bg=t["bg"])
    top_frame.config(bg=t["bg"])
    control_frame.config(bg=t["bg"])
    entry.config(bg=t["text_bg"], fg=t["fg"], insertbackground=t["fg"])
    output.config(bg=t["text_bg"], fg=t["fg"])
    timer_label.config(bg=t["bg"])
    for b in [btn_gen, btn_clr, btn_pre, btn_nxt]:
        b.config(bg=t["btn_bg"], fg=t["fg"])
    draw_ai_lamp()

def open_theme_popup():
    pop = tk.Toplevel(root)
    pop.title("Select Theme")
    pop.geometry("200x250")
    pop.grab_set() # تجعل النافذة فوق الأساسية
    tk.Label(pop, text="Choose a Template:", pady=10).pack()
    for t_name in THEMES.keys():
        tk.Button(pop, text=t_name, width=15, 
                  command=lambda n=t_name: [apply_theme(n), pop.destroy()]).pack(pady=5)

def open_scale():
    win = tk.Toplevel(root); win.title("Scale")
    def change(v):
        s = int(float(v))
        entry.config(font=(current_font, s+6))
        for b in [btn_gen, btn_clr, btn_pre, btn_nxt]: b.config(font=(current_font, int(s*0.7)))
        output.config(font=(current_font, s))
        timer_label.config(font=(current_font, int(s*0.9), "bold"))
        root.geometry(f"{int(400 * (s/14))}x{int(450 * (s/14))}")
    tk.Scale(win, from_=10, to=28, orient="horizontal", command=change, length=150).pack(padx=20, pady=20)

# ------------------- Main UI -------------------
root = tk.Tk()
root.title("Trading Assistant Pro")
root.geometry("400x450")
root.attributes("-topmost", True)

top_frame = tk.Frame(root); top_frame.pack(pady=5)
entry = tk.Entry(top_frame, justify="center", font=(current_font, 20), width=10, relief="flat"); entry.pack()
entry.insert(0, "0")

control_frame = tk.Frame(root); control_frame.pack(pady=2)
btn_gen = tk.Button(control_frame, text="Generate", command=on_generate, relief="flat", padx=5)
btn_gen.pack(side="left", padx=2)
btn_clr = tk.Button(control_frame, text="Clear", command=lambda: [output.config(state="normal"), output.delete("1.0", tk.END), output.config(state="disabled")], relief="flat", padx=5)
btn_clr.pack(side="left", padx=2)
btn_pre = tk.Button(control_frame, text="◀", command=lambda: display_group(current_group_idx-1), relief="flat", padx=5)
btn_pre.pack(side="left", padx=2)
btn_nxt = tk.Button(control_frame, text="▶", command=lambda: display_group(current_group_idx+1), relief="flat", padx=5)
btn_nxt.pack(side="left", padx=2)

ai_canvas = tk.Canvas(control_frame, width=15, height=15, bd=0, highlightthickness=0); ai_canvas.pack(side="left", padx=5)
def draw_ai_lamp():
    ai_canvas.delete("all")
    color = "green" if ai_enabled else "red"
    ai_canvas.config(bg=root.cget("bg"))
    ai_canvas.create_oval(2, 2, 13, 13, fill=color, outline=color)

timer_label = tk.Label(root, text="", font=(current_font, 13, "bold"), fg="red"); timer_label.pack(pady=2)

output = tk.Text(root, font=(current_font, BASE_FONT), height=8, state="disabled", relief="flat", padx=10, pady=5); output.pack(expand=True, fill="both", padx=10, pady=5)

# ------------------- Menubar -------------------
menubar = tk.Menu(root)
file_m = tk.Menu(menubar, tearoff=0)
file_m.add_command(label="Pin/Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_m.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_m)

view_m = tk.Menu(menubar, tearoff=0)
view_m.add_command(label="Change Theme (Pop-up)", command=open_theme_popup)
view_m.add_command(label="Scale Control", command=open_scale)
view_m.add_command(label="Opacity Toggle", command=lambda: root.attributes("-alpha", 0.7 if root.attributes("-alpha")==1.0 else 1.0))
menubar.add_cascade(label="View", menu=view_m)

ai_m = tk.Menu(menubar, tearoff=0)
ai_m.add_command(label="AI ON/OFF", command=toggle_ai)
ai_m.add_command(label="Timer/GO ON-OFF", command=lambda: [globals().update(timer_visible=not timer_visible)])
menubar.add_cascade(label="AI", menu=ai_m)

root.config(menu=menubar)
apply_theme("Classic") # يبدأ بالشكل القديم تلقائياً
root.mainloop()