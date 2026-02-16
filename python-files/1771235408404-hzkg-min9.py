import tkinter as tk
import tkinter.font as tkfont

# -------- Fixed trade table 0-59 --------
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
    40: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    41: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    42: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    43: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    44: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    45: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    46: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    47: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    48: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    49: ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"],
    50: ["01:50:00", "01:50:30 prepare trade", "01:51:00 go trade"],
    51: ["01:51:30", "01:52:00 prepare trade", "01:52:30 go trade"],
    52: ["01:53:00", "01:53:30 prepare trade", "01:54:00 go trade"],
    53: ["01:54:30", "01:55:00 prepare trade", "01:55:30 go trade"],
    54: ["01:56:00", "01:56:30 prepare trade", "01:57:00 go trade"],
    55: ["01:57:30", "01:58:00 prepare trade", "01:58:30 go trade"],
    56: ["01:59:00", "01:59:30 prepare trade", "01:59:30 go trade"],
    57: ["01:59:00", "01:59:30 prepare trade", "01:59:30 go trade"],
    58: ["01:59:00", "01:59:30 prepare trade", "01:59:30 go trade"],
    59: ["01:59:00", "01:59:30 prepare trade", "01:59:30 go trade"],
}

# -------- GUI --------
root = tk.Tk()
root.title("Trade Lookup")
root.geometry("500x400")
main_font = tkfont.Font(family="Consolas", size=12)
zoom_win = None
theme_day = {"bg": "white", "fg": "black"}
theme_night = {"bg": "black", "fg": "white"}
theme = theme_day

# -------- Functions --------
def show_trade(event=None):
    output.delete("1.0", tk.END)
    try:
        mins = int(entry_minutes.get().strip())
    except ValueError:
        output.insert(tk.END, "Invalid input\n")
        return
    if mins in trade_table:
        for line in trade_table[mins]:
            output.insert(tk.END, line + "\n")
    else:
        output.insert(tk.END, "Not found\n")

def clear_output():
    output.delete("1.0", tk.END)

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
    theme = theme_night if theme == theme_day else theme_day
    root.configure(bg=theme["bg"])
    entry_minutes.configure(bg=theme["bg"], fg=theme["fg"])
    output.configure(bg=theme["bg"], fg=theme["fg"])

def pin_app():
    root.attributes("-topmost", not root.attributes("-topmost"))

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
tk.Label(root, text="Enter minutes:", font=main_font).pack(pady=5)
entry_minutes = tk.Entry(root, justify="center", font=main_font)
entry_minutes.pack(pady=5)
entry_minutes.bind("<Return>", show_trade)
entry_minutes.insert(0, "0")

tk.Button(root, text="Generate", font=main_font, command=show_trade).pack(pady=5)
tk.Button(root, text="Clear", font=main_font, command=clear_output).pack(pady=5)

output = tk.Text(root, font=main_font)
output.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
