import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime

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

# ------------------- NEXT & GO Times -------------------
NEXT_TIMES = [
    "01:02:00","01:03:30","01:05:00","01:06:30","01:08:00","01:09:30",
    "01:11:00","01:12:30","01:14:00","01:15:30","01:17:00","01:18:30",
    "01:20:00","01:21:30","01:23:00","01:24:30","01:26:00","01:27:30",
    "01:29:00","01:30:30","01:32:00","01:33:30","01:35:00","01:36:30",
    "01:38:00","01:39:30","01:41:00","01:42:30","01:44:00","01:45:30",
    "01:47:00","01:48:30","01:50:00","01:51:30","01:53:00","01:54:30",
    "01:56:00","01:57:30","01:59:00"
]

GO_TIMES = [
    "01:01:00","01:02:30","01:04:00","01:05:30","01:07:00","01:08:30",
    "01:10:00","01:11:30","01:13:00","01:14:30","01:16:00","01:17:30",
    "01:19:00","01:20:30","01:22:00","01:23:30","01:25:00","01:26:30",
    "01:28:00","01:29:30","01:31:00","01:32:30","01:34:00","01:35:30",
    "01:37:00","01:38:30","01:40:00","01:41:30","01:43:00","01:44:30",
    "01:46:00","01:47:30","01:49:00","01:50:30","01:52:00","01:53:30",
    "01:55:00","01:56:30","01:58:00","01:59:30"
]

next_timer_active = False
next_seconds_left = 0
go_active = False
go_seconds_left = 0
adjust_value = 0  # Slider adjust value in seconds

# ------------------- Globals -------------------
BASE_FONT = 14
current_font = "Segoe UI"
dark_mode = False
topmost = True
current_group_idx = 0
ai_enabled = False
ai_after_id = None
main_font = None

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + AI + View")
root.geometry("520x500")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)
main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- UI -------------------
entry = tk.Entry(root)
entry.pack()

output = tk.Text(root, height=15)
output.pack()

# ------------------- Display Function -------------------
def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    output.config(state="normal")
    output.delete("1.0", tk.END)
    for l in trade_table[idx]:
        output.insert(tk.END, l+"\n")
    output.config(state="disabled")

# ------------------- NEXT Timer -------------------
def check_timers():
    global next_timer_active, next_seconds_left, go_active, go_seconds_left, adjust_value

    if not ai_enabled:
        return

    now = datetime.now().strftime("%H:%M:%S")

    # NEXT
    if now in NEXT_TIMES and not next_timer_active:
        next_timer_active = True
        next_seconds_left = 30 + adjust_value
        output.config(state="normal")
        output.insert(tk.END,f"\nnext {next_seconds_left}s\n")
        output.config(state="disabled")
        run_next_timer()

    # GO
    if now in GO_TIMES and not go_active:
        go_active = True
        go_seconds_left = 25 + adjust_value
        output.config(state="normal")
        output.insert(tk.END,f"\ngo trade {go_seconds_left}s\n")
        output.config(state="disabled")
        run_go_timer()

def run_next_timer():
    global next_timer_active, next_seconds_left

    if next_seconds_left <= 0:
        next_timer_active = False
        output.config(state="normal")
        output.delete("end-2l", "end")
        output.config(state="disabled")
        return

    next_seconds_left -= 1
    output.config(state="normal")
    output.delete("end-2l","end")
    output.insert(tk.END,f"next {next_seconds_left}s\n")
    output.config(state="disabled")
    root.after(1000, run_next_timer)

def run_go_timer():
    global go_active, go_seconds_left

    if go_seconds_left <= 0:
        go_active = False
        output.config(state="normal")
        output.delete("end-2l","end")
        output.config(state="disabled")
        return

    go_seconds_left -= 1
    output.config(state="normal")
    output.delete("end-2l","end")
    output.insert(tk.END,f"go trade {go_seconds_left}s\n")
    output.config(state="disabled")
    root.after(1000, run_go_timer)

# ------------------- AI Loop -------------------
def ai_loop():
    global ai_after_id
    if not ai_enabled:
        return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0,str(now.minute))
    check_timers()
    ai_after_id = root.after(1000, ai_loop)

# ------------------- Toggle AI -------------------
def toggle_ai():
    global ai_enabled
    ai_enabled = not ai_enabled
    if ai_enabled:
        ai_loop()

btn = tk.Button(root, text="AI ON / OFF", command=toggle_ai)
btn.pack()

# ------------------- Edit Timer Menu -------------------
def open_edit_timer():
    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Timer")
    edit_win.geometry("400x150")

    slider = tk.Scale(edit_win, from_=-60, to=60, orient="horizontal", label="Adjust Timer (seconds)")
    slider.set(adjust_value)
    slider.pack(pady=10, fill="x", padx=20)

    def plus10(): slider.set(slider.get()+10)
    def minus10(): slider.set(slider.get()-10)

    tk.Button(edit_win, text="+10", command=plus10).pack(side="left", padx=20)
    tk.Button(edit_win, text="-10", command=minus10).pack(side="right", padx=20)

    def save_adjust():
        global adjust_value
        adjust_value = slider.get()
        edit_win.destroy()

    tk.Button(edit_win, text="OK", command=save_adjust).pack(pady=10)

menubar = tk.Menu(root)
edit_menu = tk.Menu(menubar, tearoff=0)
edit_menu.add_command(label="Edit Timer", command=open_edit_timer)
menubar.add_cascade(label="Edit", menu=edit_menu)
root.config(menu=menubar)

display_group(0)
root.mainloop()