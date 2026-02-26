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
BASE_FONT_SIZE = 14
current_font_family = "Segoe UI"
dark_mode = False
ai_enabled = False
current_group_idx = 0
ai_after_id = None
timer_after_id = None

# ------------------- Functions -------------------
def parse_time_str(s):
    try: return datetime.strptime(s.split()[0], "%H:%M:%S").time()
    except: return None

def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    output.config(state="normal")
    output.delete("1.0", tk.END)
    for line in trade_table[idx]:
        output.insert(tk.END, line + "\n")
    output.config(state="disabled")
    start_logic_timer(idx)

def start_logic_timer(idx):
    global timer_after_id
    if timer_after_id: root.after_cancel(timer_after_id)
    
    def tick():
        global timer_after_id
        now = datetime.now()
        curr_total = now.minute * 60 + now.second
        
        t_prep = parse_time_str(trade_table[idx][0])
        t_mid  = parse_time_str(trade_table[idx][1])
        t_go   = parse_time_str(trade_table[idx][2])
        
        target_mid = t_mid.minute * 60 + t_mid.second
        target_go  = t_go.minute * 60 + t_go.second

        if curr_total < target_mid:
            diff = target_mid - curr_total
            timer_label.config(text=f"{diff}s prepare", fg="#D2B48C")
        elif curr_total < target_go:
            diff = target_go - curr_total
            timer_label.config(text=f"{diff}s GO TRADE", fg="orange")
        else:
            timer_label.config(text="Done / Waiting", fg="gray")
        
        timer_after_id = root.after(1000, tick)
    tick()

def on_generate(event=None):
    if ai_enabled:
        now = datetime.now()
        curr_sec = now.minute * 60 + now.second
        idx = 0
        for i, g in enumerate(trade_table):
            if curr_sec <= (parse_time_str(g[2]).minute * 60 + parse_time_str(g[2]).second):
                idx = i; break
    else:
        try:
            val = entry.get()
            minute = int(val.split(":")[0]) if ":" in val else int(val)
            idx = next((i for i, g in enumerate(trade_table) if parse_time_str(g[0]).minute >= minute), 0)
        except: return "break"
    display_group(idx)
    return "break"

def toggle_ai():
    global ai_enabled, ai_after_id
    ai_enabled = not ai_enabled
    draw_ai_lamp()
    if ai_enabled:
        entry.config(state="disabled")
        def loop():
            on_generate(); global ai_after_id
            ai_after_id = root.after(5000, loop)
        loop()
    else:
        if ai_after_id: root.after_cancel(ai_after_id)
        entry.config(state="normal")

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#1e1e1e" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    top_frame.config(bg=bg)
    control_frame.config(bg=bg)
    output.config(bg="#2d2d2d" if dark_mode else "white", fg=fg)
    timer_label.config(bg=bg)
    for b in [btn_gen, btn_clr, btn_pre, btn_nxt]: b.config(bg=bg, fg=fg)
    draw_ai_lamp()

def set_opacity(val):
    root.attributes("-alpha", float(val))

def change_font_size(val):
    new_size = int(float(val))
    main_font.configure(size=new_size)
    output.config(font=main_font)
    timer_label.config(font=(current_font_family, int(new_size*1.2), "bold"))

# ------------------- UI Setup -------------------
root = tk.Tk()
root.title("Trade Bot Pro")
root.geometry("450x550")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

main_font = tkfont.Font(family=current_font_family, size=BASE_FONT_SIZE)

top_frame = tk.Frame(root); top_frame.pack(pady=5)
entry = tk.Entry(top_frame, justify="center", font=(current_font_family, 16), width=10)
entry.pack(); entry.insert(0, "0")
entry.bind("<Return>", on_generate)

control_frame = tk.Frame(root); control_frame.pack(pady=5)
btn_gen = tk.Button(control_frame, text="Generate", command=on_generate); btn_gen.pack(side="left", padx=2)
btn_clr = tk.Button(control_frame, text="Clear", command=lambda: [output.config(state="normal"), output.delete("1.0", tk.END), output.config(state="disabled")]); btn_clr.pack(side="left", padx=2)
btn_pre = tk.Button(control_frame, text="◀", command=lambda: display_group(current_group_idx-1)); btn_pre.pack(side="left", padx=2)
btn_nxt = tk.Button(control_frame, text="▶", command=lambda: display_group(current_group_idx+1)); btn_nxt.pack(side="left", padx=2)

ai_canvas = tk.Canvas(control_frame, width=15, height=15, bd=0, highlightthickness=0); ai_canvas.pack(side="left", padx=5)
def draw_ai_lamp():
    ai_canvas.delete("all")
    ai_canvas.create_oval(2, 2, 13, 13, fill="green" if ai_enabled else "red")

output = tk.Text(root, font=main_font, height=10, state="disabled"); output.pack(expand=True, fill="both", padx=10)
timer_label = tk.Label(root, text="", font=(current_font_family, 18, "bold")); timer_label.pack(pady=10)

# ------------------- Menus -------------------
menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin/Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day/Night", command=toggle_mode)
view_menu.add_separator()
# إضافة Scale داخل المنيو عبر نافذة فرعية
def open_settings():
    win = tk.Toplevel(root); win.title("Settings")
    tk.Label(win, text="Opacity:").pack()
    s1 = tk.Scale(win, from_=0.3, to=1.0, resolution=0.1, orient="horizontal", command=set_opacity)
    s1.set(root.attributes("-alpha")); s1.pack()
    tk.Label(win, text="Font Size:").pack()
    s2 = tk.Scale(win, from_=10, to=30, orient="horizontal", command=change_font_size)
    s2.set(BASE_FONT_SIZE); s2.pack()

view_menu.add_command(label="Size & Opacity", command=open_settings)
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
menubar.add_cascade(label="AI", menu=ai_menu)

root.config(menu=menubar)
draw_ai_lamp()
display_group(0)
root.mainloop()