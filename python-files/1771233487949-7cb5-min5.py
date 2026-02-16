import tkinter as tk
import tkinter.font as tkfont

# -------- جدول ثابت لكل الدقائق 0-59 --------
trade_table = {
    0: ["01:00:00", "01:00:30 prepare trade", "01:01:00 go trade"],
    1: ["01:01:30", "01:02:00 prepare trade", "01:02:30 go trade"],
    2: ["01:03:00", "01:03:30 prepare trade", "01:04:00 go trade"],
    3: ["01:04:30", "01:05:00 prepare trade", "01:05:30 go trade"],
    4: ["01:06:00", "01:06:30 prepare trade", "01:07:00 go trade"],
    5: ["01:07:30", "01:08:00 prepare trade", "01:08:30 go trade"],
    6: ["01:09:00", "01:09:30 prepare trade", "01:10:00 go trade"],
    7: ["01:10:30", "01:11:00 prepare trade", "01:11:30 go trade"],
    8: ["01:12:00", "01:12:30 prepare trade", "01:13:00 go trade"],
    9: ["01:13:30", "01:14:00 prepare trade", "01:14:30 go trade"],
    10: ["01:15:00", "01:15:30 prepare trade", "01:16:00 go trade"],
    11: ["01:16:30", "01:17:00 prepare trade", "01:17:30 go trade"],
    12: ["01:18:00", "01:18:30 prepare trade", "01:19:00 go trade"],
    13: ["01:19:30", "01:20:00 prepare trade", "01:20:30 go trade"],
    14: ["01:21:00", "01:21:30 prepare trade", "01:22:00 go trade"],
    15: ["01:22:30", "01:23:00 prepare trade", "01:23:30 go trade"],
    16: ["01:24:00", "01:24:30 prepare trade", "01:25:00 go trade"],
    17: ["01:25:30", "01:26:00 prepare trade", "01:26:30 go trade"],
    18: ["01:27:00", "01:27:30 prepare trade", "01:28:00 go trade"],
    19: ["01:28:30", "01:29:00 prepare trade", "01:29:30 go trade"],
    20: ["01:30:00", "01:30:30 prepare trade", "01:31:00 go trade"],
    21: ["01:31:30", "01:32:00 prepare trade", "01:32:30 go trade"],
    22: ["01:33:00", "01:33:30 prepare trade", "01:34:00 go trade"],
    23: ["01:34:30", "01:35:00 prepare trade", "01:35:30 go trade"],
    24: ["01:36:00", "01:36:30 prepare trade", "01:37:00 go trade"],
    25: ["01:37:30", "01:38:00 prepare trade", "01:38:30 go trade"],
    26: ["01:39:00", "01:39:30 prepare trade", "01:40:00 go trade"],
    27: ["01:40:30", "01:41:00 prepare trade", "01:41:30 go trade"],
    28: ["01:42:00", "01:42:30 prepare trade", "01:43:00 go trade"],
    29: ["01:43:30", "01:44:00 prepare trade", "01:44:30 go trade"],
    30: ["01:45:00", "01:45:30 prepare trade", "01:46:00 go trade"],
    31: ["01:46:30", "01:47:00 prepare trade", "01:47:30 go trade"],
    32: ["01:48:00", "01:48:30 prepare trade", "01:49:00 go trade"],
    33: ["01:49:30", "01:50:00 prepare trade", "01:50:30 go trade"],
    34: ["01:51:00", "01:51:30 prepare trade", "01:52:00 go trade"],
    35: ["01:52:30", "01:53:00 prepare trade", "01:53:30 go trade"],
    36: ["01:54:00", "01:54:30 prepare trade", "01:55:00 go trade"],
    37: ["01:55:30", "01:56:00 prepare trade", "01:56:30 go trade"],
    38: ["01:57:00", "01:57:30 prepare trade", "01:58:00 go trade"],
    39: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
}

# -------- متغيرات --------
zoom_win = None
main_font = tkfont.Font(family="Consolas", size=12)
day_theme = {"bg":"white", "fg":"black"}
night_theme = {"bg":"black", "fg":"white"}

# -------- وظائف --------
def show_trade():
    try:
        mins = int(entry.get().strip())
    except ValueError:
        set_output("Invalid input")
        return
    if mins in trade_table:
        values = trade_table[mins]
        set_output(values)
    else:
        set_output("Not found")

def set_output(values):
    if isinstance(values, list):
        out1_var.set(values[0])
        out2_var.set(values[1])
        out3_var.set(values[2])
    else:
        out1_var.set(values)
        out2_var.set("")
        out3_var.set("")

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

def toggle_theme():
    global theme
    theme = night_theme if theme==day_theme else day_theme
    root.configure(bg=theme["bg"])
    for w in [entry, out1_entry, out2_entry, out3_entry]:
        w.configure(bg=theme["bg"], fg=theme["fg"])

def pin_app():
    root.attributes("-topmost", not root.attributes("-topmost"))

# -------- GUI --------
root = tk.Tk()
root.title("Trade Lookup")
root.geometry("500x300")
theme = day_theme
root.configure(bg=theme["bg"])

# -------- Menu --------
menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Zoom", command=open_zoom)
file_menu.add_command(label="Day/Night", command=toggle_theme)
file_menu.add_command(label="Pin App", command=pin_app)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# -------- UI --------
tk.Label(root, text="Enter Minutes:", font=main_font, bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
entry = tk.Entry(root, font=main_font, justify="center", bg=theme["bg"], fg=theme["fg"])
entry.pack(pady=5)
tk.Button(root, text="Show Trade", font=main_font, command=show_trade).pack(pady=10)

# -------- Output الثلاث مربعات --------
out1_var = tk.StringVar()
out2_var = tk.StringVar()
out3_var = tk.StringVar()

out_frame = tk.Frame(root)
out_frame.pack(pady=5, fill="x", padx=20)

out1_entry = tk.Entry(out_frame, textvariable=out1_var, font=main_font, justify="center", state="readonly", bg="red")
out1_entry.pack(side="left", expand=True, fill="both", padx=2)
out2_entry = tk.Entry(out_frame, textvariable=out2_var, font=main_font, justify="center", state="readonly", bg="white")
out2_entry.pack(side="left", expand=True, fill="both", padx=2)
out3_entry = tk.Entry(out_frame, textvariable=out3_var, font=main_font, justify="center", state="readonly", bg="green")
out3_entry.pack(side="left", expand=True, fill="both", padx=2)

root.mainloop()
