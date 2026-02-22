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

# ------------------- Globals -------------------
BASE_FONT = 14
current_font = "Segoe UI"
dark_mode = False
topmost = True
current_group_idx = 0
ai_enabled = False
ai_after_id = None

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + AI")
root.geometry("520x420")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- Logic -------------------
def find_group_by_minute(minute):
    for i, g in enumerate(trade_table):
        for v in g:
            try:
                if int(v.split(":")[1]) == minute:
                    return i
            except:
                pass
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

def on_generate(event=None):
    try:
        minute = int(entry.get())
    except:
        return "break"
    idx = find_group_by_minute(minute)
    if idx is not None:
        display_group(idx)
    return "break"

def clear_output():
    output.config(state="normal")
    output.delete("1.0", tk.END)
    output.config(state="disabled")

def prev_group(event=None):
    display_group(current_group_idx - 1)
    return "break"

def next_group(event=None):
    display_group(current_group_idx + 1)
    return "break"

# ------------------- AI -------------------
def ai_loop():
    global ai_after_id
    if not ai_enabled:
        return
    minute = datetime.now().minute
    entry.delete(0, tk.END)
    entry.insert(0, str(minute))
    on_generate()
    ai_after_id = root.after(1000, ai_loop)

def toggle_ai():
    global ai_enabled, ai_after_id
    ai_enabled = not ai_enabled
    draw_ai_lamp()
    if ai_enabled:
        ai_loop()
    else:
        if ai_after_id:
            root.after_cancel(ai_after_id)
            ai_after_id = None

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(main_font.cget("size") * 0.9)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_enabled else "red"
    ai_canvas.create_oval(2,2,size,size, fill=color, outline="black")

# ------------------- UI -------------------
top_frame = tk.Frame(root)
top_frame.pack(pady=2)

entry = tk.Entry(top_frame, justify="center", font=(current_font, int(BASE_FONT*1.2)), width=10)
entry.pack()
entry.insert(0,"0")
entry.bind("<Return>", on_generate)

control = tk.Frame(root)
control.pack(pady=2)

btn_generate = tk.Button(control, text="Generate", font=(current_font, int(BASE_FONT*0.7)), command=on_generate)
btn_generate.pack(side="left", padx=2)

btn_clear = tk.Button(control, text="Clear", font=(current_font, int(BASE_FONT*0.7)), command=clear_output)
btn_clear.pack(side="left", padx=2)

btn_prev = tk.Button(control, text="◀", font=(current_font, int(BASE_FONT*0.7)), command=prev_group)
btn_prev.pack(side="left", padx=2)

btn_next = tk.Button(control, text="▶", font=(current_font, int(BASE_FONT*0.7)), command=next_group)
btn_next.pack(side="left", padx=2)

ai_canvas = tk.Canvas(control, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=4)
draw_ai_lamp()

output = tk.Text(root, font=main_font, height=8)
output.pack(expand=True, fill="both", padx=10, pady=6)
output.config(state="disabled")

# ------------------- Menu -------------------
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Scale +", command=lambda: main_font.configure(size=main_font.cget("size")+1))
view_menu.add_command(label="Scale -", command=lambda: main_font.configure(size=main_font.cget("size")-1))
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="AI ON / OFF", command=toggle_ai)
menubar.add_cascade(label="AI", menu=ai_menu)

# ------------------- Keys -------------------
root.bind("<Left>", prev_group)
root.bind("<Right>", next_group)

display_group(0)
root.mainloop()