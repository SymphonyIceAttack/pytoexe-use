import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from tkinter import messagebox

# ------------------- Trade Table -------------------
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

# ------------------- Globals -------------------
BASE_FONT = 14
current_font = "Segoe UI"
zoom_win = None
dark_mode = False
topmost = True
history = []
history_win = None
history_text = None
main_font = None
current_group_idx = 0

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + View")
root.geometry("520x420")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)
main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- Helper: parse minute -------------------
def parse_minute(s):
    s = s.strip()
    if s == "":
        return None
    # try plain integer
    try:
        return int(s)
    except:
        pass
    # try HH:MM or H:MM:SS etc.
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except:
            return None
    return None

# ------------------- Search group by minute -------------------
def find_group_by_minute(minute):
    """Return (index, group) if found, else (None, None)."""
    if minute is None:
        return (None, None)
    for idx, group in enumerate(trade_table):
        for val in group:
            # split on ':' and check minute field (second element)
            parts = val.split(":")
            if len(parts) >= 2:
                # parts[1] should be the minute as digits (e.g., '45')
                try:
                    part_min = int(parts[1])
                except:
                    continue
                if part_min == minute:
                    return (idx, group)
    return (None, None)

# ------------------- Display group -------------------
def display_group_by_index(idx):
    """Safely display group at index idx and update current_group_idx and history."""
    global current_group_idx
    if idx is None:
        return
    if idx < 0 or idx >= len(trade_table):
        return
    current_group_idx = idx
    output.config(state="normal")
    output.delete("1.0", tk.END)
    for line in trade_table[idx]:
        output.insert(tk.END, line + "\n")
    output.config(state="disabled")
    add_history_group(idx)

# ------------------- Generate / Enter handler -------------------
def on_generate(event=None):
    """Called by Generate button or Enter key. Finds group by minute entered and displays it."""
    raw = entry_minutes.get()
    minute = parse_minute(raw)
    if minute is None or minute < 0 or minute > 59:
        output.config(state="normal")
        output.delete("1.0", tk.END)
        output.insert(tk.END, "Invalid input — اكتب رقم دقيقة من 0 إلى 59 أو وقت بصيغة HH:MM:SS\n")
        output.config(state="disabled")
        return "break"
    idx, group = find_group_by_minute(minute)
    if idx is None:
        output.config(state="normal")
        output.delete("1.0", tk.END)
        output.insert(tk.END, "Not found\n")
        output.config(state="disabled")
    else:
        display_group_by_index(idx)
    return "break"

# ------------------- Clear output -------------------
def clear_output():
    output.config(state="normal")
    output.delete("1.0", tk.END)
    output.config(state="disabled")

# ------------------- History -------------------
def add_history_group(idx):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # record group number (1-based) and the minute of first item for convenience
    first = trade_table[idx][0] if trade_table[idx] else ""
    history.append(f"{len(history)+1}. Group {idx+1} | {first} | {ts}")
    update_history()

def update_history():
    if history_win and history_win.winfo_exists():
        history_text.config(state="normal")
        history_text.delete("1.0", tk.END)
        for h in history:
            history_text.insert(tk.END, h + "\n")
        history_text.config(state="disabled")

def clear_history():
    history.clear()
    update_history()

def open_history():
    global history_win, history_text
    if history_win and history_win.winfo_exists():
        history_win.lift()
        return
    history_win = tk.Toplevel(root)
    history_win.title("History")
    history_win.geometry("520x300")
    history_text = tk.Text(history_win, state="disabled", font=main_font)
    history_text.pack(fill="both", expand=True)
    tk.Button(history_win, text="Clear History", command=clear_history).pack(pady=5)
    update_history()

# ------------------- Zoom -------------------
def open_zoom():
    global zoom_win
    if zoom_win and zoom_win.winfo_exists():
        zoom_win.lift()
        return
    zoom_win = tk.Toplevel(root)
    zoom_win.title("Zoom")
    zoom_win.geometry("300x80")
    zoom_win.resizable(False, False)
    def on_zoom(val):
        main_font.configure(size=int(float(val)))
    scale = tk.Scale(zoom_win, from_=10, to=28, orient="horizontal", label="Font Size", command=on_zoom)
    scale.set(main_font.cget("size"))
    scale.pack(fill="x", padx=10, pady=10)

# ------------------- Day / Night -------------------
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "black" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    # apply to main widgets
    root.config(bg=bg)
    top_frame.config(bg=bg)
    control_frame.config(bg=bg)
    entry_minutes.config(bg=bg, fg=fg, insertbackground=fg)
    btn_generate.config(bg=bg, fg=fg)
    btn_clear.config(bg=bg, fg=fg)
    btn_prev.config(bg=bg, fg=fg)
    btn_next.config(bg=bg, fg=fg)
    output.config(bg=bg, fg=fg)

# ------------------- Pin -------------------
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

# ------------------- Navigation prev/next -------------------
def prev_group(event=None):
    global current_group_idx
    if current_group_idx > 0:
        display_group_by_index(current_group_idx - 1)
    # ensure key presses don't propagate / don't do anything else
    return "break"

def next_group(event=None):
    global current_group_idx
    if current_group_idx < len(trade_table) - 1:
        display_group_by_index(current_group_idx + 1)
    return "break"

# ------------------- UI Layout -------------------
top_frame = tk.Frame(root)
top_frame.pack(pady=6)

entry_minutes = tk.Entry(top_frame, justify="center", font=main_font, width=12)
entry_minutes.pack()
entry_minutes.insert(0, "0")
# Enter should trigger Generate
entry_minutes.bind("<Return>", on_generate)

# controls row under entry: Generate | Clear | ◀ | ▶
control_frame = tk.Frame(root)
control_frame.pack(pady=6)

btn_generate = tk.Button(control_frame, text="Generate", font=main_font, width=10, command=lambda: on_generate())
btn_generate.pack(side="left", padx=6)

btn_clear = tk.Button(control_frame, text="Clear", font=main_font, width=10, command=clear_output)
btn_clear.pack(side="left", padx=6)

btn_prev = tk.Button(control_frame, text="◀", font=main_font, width=5, command=prev_group)
btn_prev.pack(side="left", padx=12)

btn_next = tk.Button(control_frame, text="▶", font=main_font, width=5, command=next_group)
btn_next.pack(side="left", padx=6)

# output box under the controls, shows three lines vertically
output = tk.Text(root, font=main_font, height=8)
output.pack(expand=True, fill="both", padx=10, pady=8)
output.config(state="disabled")

# ------------------- Menu -------------------
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="History", command=open_history)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Scale", command=open_zoom)

# ------------------- Key bindings for arrows (only move groups) -------------------
# Bind to root so arrow keys work regardless of focus.
root.bind("<Left>", prev_group)
root.bind("<Right>", next_group)

# Ensure that clicking arrow keys does not trigger default widget navigation
# (handlers above return "break").

# ------------------- Initialize display with first group -------------------
display_group_by_index(0)

# Start
root.mainloop()