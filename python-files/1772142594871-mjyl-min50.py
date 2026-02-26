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
dark_mode = False
current_group_idx = 0
ai_enabled = False
ai_after_id = None
main_font = None
history = []
history_win = None
history_text = None

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + AI + View")
root.geometry("520x420")

try:
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.95)
except:
    pass

main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- Helpers -------------------
def parse_time_str(s):
    try:
        return datetime.strptime(s.split()[0], "%H:%M:%S").time()
    except:
        return None

def display_group(idx):
    global current_group_idx
    idx %= len(trade_table)
    current_group_idx = idx
    output.config(state="normal")
    output.delete("1.0", tk.END)
    for l in trade_table[idx]:
        output.insert(tk.END, l + "\n")
    output.config(state="disabled")

# ------------------- CORE FIX -------------------
def find_group_by_minute(minute=None):
    """
    تحديد المجموعة بدقة دقيقة + ثانية
    أول ما الوقت يعدي end بثانية واحدة → ينتقل للمجموعة التالية فورًا
    """
    now = datetime.now()
    current = (now.minute, now.second)

    for i in range(len(trade_table)):
        t_end = parse_time_str(trade_table[i][2])
        end_min_sec = (t_end.minute, t_end.second)

        if current <= end_min_sec:
            return i

    return len(trade_table) - 1

# ------------------- AI -------------------
def ai_loop():
    global ai_after_id
    if not ai_enabled:
        return

    now = datetime.now()
    manual_value = f"{now.minute:02d}:{now.second:02d}"

    entry.delete(0, tk.END)
    entry.insert(0, manual_value)

    idx = find_group_by_minute()
    if idx is not None:
        display_group(idx)

    ai_after_id = root.after(1000, ai_loop)

def toggle_ai():
    global ai_enabled, ai_after_id
    ai_enabled = not ai_enabled
    if ai_enabled:
        ai_loop()
    else:
        if ai_after_id:
            root.after_cancel(ai_after_id)
            ai_after_id = None

# ------------------- UI -------------------
top_frame = tk.Frame(root)
top_frame.pack(pady=2)

entry = tk.Entry(top_frame, justify="center", font=(current_font, int(BASE_FONT*1.2)), width=10)
entry.pack()
entry.insert(0, "00:00")

control_frame = tk.Frame(root)
control_frame.pack(pady=2)

tk.Button(control_frame, text="Generate", command=lambda: display_group(find_group_by_minute())).pack(side="left", padx=2)
tk.Button(control_frame, text="AI ON / OFF", command=toggle_ai).pack(side="left", padx=2)

output = tk.Text(root, font=main_font, height=8)
output.pack(expand=True, fill="both", padx=10, pady=6)
output.config(state="disabled")

display_group(0)
root.mainloop()