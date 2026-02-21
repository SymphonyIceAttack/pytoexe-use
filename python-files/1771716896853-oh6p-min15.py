import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from datetime import datetime
import re

# ================== TRADE TABLE ==================
trade_table = [
    ["01:00:00","01:00:30 prepare trade","01:01:00 go trade"],
    ["01:01:30","01:02:00 prepare trade","01:02:30 go trade"],
    ["01:03:00","01:03:30 prepare trade","01:04:00 go trade"],
    ["01:04:30","01:05:00 prepare trade","01:05:30 go trade"],
    ["01:06:00","01:06:30 prepare trade","01:07:00 go trade"],
    ["01:07:30","01:08:00 prepare trade","01:08:30 go trade"],
    ["01:09:00","01:09:30 prepare trade","01:10:00 go trade"],
    ["01:10:30","01:11:00 prepare trade","01:11:30 go trade"],
    ["01:12:00","01:12:30 prepare trade","01:13:00 go trade"],
    ["01:13:30","01:14:00 prepare trade","01:14:30 go trade"],
    ["01:15:00","01:15:30 prepare trade","01:16:00 go trade"],
    ["01:16:30","01:17:00 prepare trade","01:17:30 go trade"],
    ["01:18:00","01:18:30 prepare trade","01:19:00 go trade"],
    ["01:19:30","01:20:00 prepare trade","01:20:30 go trade"],
    ["01:21:00","01:21:30 prepare trade","01:22:00 go trade"],
    ["01:22:30","01:23:00 prepare trade","01:23:30 go trade"],
    ["01:24:00","01:24:30 prepare trade","01:25:00 go trade"],
    ["01:25:30","01:26:00 prepare trade","01:26:30 go trade"],
    ["01:27:00","01:27:30 prepare trade","01:28:00 go trade"],
    ["01:28:30","01:29:00 prepare trade","01:29:30 go trade"],
    ["01:30:00","01:30:30 prepare trade","01:31:00 go trade"],
    ["01:31:30","01:32:00 prepare trade","01:32:30 go trade"],
    ["01:33:00","01:33:30 prepare trade","01:34:00 go trade"],
    ["01:34:30","01:35:00 prepare trade","01:35:30 go trade"],
    ["01:36:00","01:36:30 prepare trade","01:37:00 go trade"],
    ["01:37:30","01:38:00 prepare trade","01:38:30 go trade"],
    ["01:39:00","01:39:30 prepare trade","01:40:00 go trade"],
    ["01:40:30","01:41:00 prepare trade","01:41:30 go trade"],
    ["01:42:00","01:42:30 prepare trade","01:43:00 go trade"],
    ["01:43:30","01:44:00 prepare trade","01:44:30 go trade"],
    ["01:45:00","01:45:30 prepare trade","01:46:00 go trade"],
    ["01:46:30","01:47:00 prepare trade","01:47:30 go trade"],
    ["01:48:00","01:48:30 prepare trade","01:49:00 go trade"],
    ["01:49:30","01:50:00 prepare trade","01:50:30 go trade"],
    ["01:51:00","01:51:30 prepare trade","01:52:00 go trade"],
    ["01:52:30","01:53:00 prepare trade","01:53:30 go trade"],
    ["01:54:00","01:54:30 prepare trade","01:55:00 go trade"],
    ["01:55:30","01:56:00 prepare trade","01:56:30 go trade"],
    ["01:57:00","01:57:30 prepare trade","01:58:00 go trade"],
    ["01:58:30","01:59:00 prepare trade","01:59:30 go trade"]
]

# ================== STATE ==================
current_index = None
dark_mode = False

# ================== ROOT ==================
root = tk.Tk()
root.title("Trade Time Navigator")
root.geometry("520x400")
root.attributes("-topmost", True)

font_main = tkfont.Font(family="Segoe UI", size=15)

# ================== STYLE ==================
style = ttk.Style()
style.configure("TButton", padding=5, relief="flat", font=("Segoe UI", 13))
style.map("TButton", background=[('active','#d0d0d0')])

# ================== FUNCTIONS ==================
def show_group(index):
    global current_index
    if 0 <= index < len(trade_table):
        current_index = index
        output.config(state="normal")
        output.delete("1.0", tk.END)
        for line in trade_table[index]:
            output.insert(tk.END, line+"\n")
        output.config(state="disabled")

def search_time():
    text = entry.get().strip()
    if not re.fullmatch(r"\d{1,2}:(00|30)", text):
        messagebox.showerror("Error", "Use MM:00 or MM:30 only")
        return
    minute, second = text.split(":")
    target = f"01:{int(minute):02d}:{second}"
    for i, group in enumerate(trade_table):
        if group[0] == target:
            show_group(i)
            return
    messagebox.showinfo("Not Found", "No matching group")

def live_time_once():
    now = datetime.now()
    m, s = now.minute, now.second
    sec = "00" if s < 30 else "30"
    target = f"01:{m:02d}:{sec}"
    for i, group in enumerate(trade_table):
        if group[0] == target:
            show_group(i)
            entry.delete(0, tk.END)
            entry.insert(0, f"{m}:{sec}")
            return

def prev_group(event=None):
    if current_index is not None:
        show_group(current_index-1)

def next_group(event=None):
    if current_index is not None:
        show_group(current_index+1)

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#222222" if dark_mode else "#f8f8f8"
    fg = "white" if dark_mode else "black"
    entry.config(bg=bg, fg=fg, insertbackground=fg)
    output.config(bg=bg, fg=fg)
    root.config(bg=bg)
    nav_frame.config(bg=bg)

# ================== UI ==================
frame_top = tk.Frame(root, bg="#f8f8f8")
frame_top.pack(pady=8, fill="x")

entry = tk.Entry(frame_top, font=font_main, justify="center", width=10, relief="flat", bd=2)
entry.pack(side="left", padx=5)
entry.insert(0, "13:30")

btn_find = ttk.Button(frame_top, text="Find", command=search_time)
btn_find.pack(side="left", padx=5)

btn_live = ttk.Button(frame_top, text="⏱ Live", command=live_time_once)
btn_live.pack(side="left", padx=5)

btn_theme = ttk.Button(frame_top, text="🌙", command=toggle_theme)
btn_theme.pack(side="left", padx=5)

output = tk.Text(root, font=font_main, height=8, state="disabled", bd=2, relief="flat")
output.pack(fill="both", expand=True, padx=10, pady=10)

nav_frame = tk.Frame(root, bg="#f8f8f8")
nav_frame.pack(pady=5)

btn_prev = ttk.Button(nav_frame, text="◀", command=prev_group)
btn_prev.pack(side="left", padx=10)

btn_next = ttk.Button(nav_frame, text="▶", command=next_group)
btn_next.pack(side="left", padx=10)

# ================== KEYBOARD ==================
root.bind("<Left>", prev_group)
root.bind("<Right>", next_group)

# ================== START ==================
toggle_theme()  # يبدأ بوضع Light mode

root.mainloop()