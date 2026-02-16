import tkinter as tk
import tkinter.font as tkfont
from tkinter import simpledialog

# -------- Fixed trade table --------
trade_table = [
    ["01:00:00", "01:00:30 prepare trade", "01:01:00 go trade"],
    ["01:01:30", "01:02:00 prepare trade", "01:02:30 go trade"],
    ["01:03:00", "01:03:30 prepare trade", "01:04:00 go trade"],
    ["01:04:30", "01:05:00 prepare trade", "01:05:30 go trade"],
    ["01:06:00", "01:06:30 prepare trade", "01:07:00 go trade"],
    ["01:07:30", "01:08:00 prepare trade", "01:08:30 go trade"],
    ["01:09:00", "01:09:30 prepare trade", "01:10:00 go trade"],
    ["01:10:30", "01:11:00 prepare trade", "01:11:30 go trade"],
    ["01:12:00", "01:12:30 prepare trade", "01:13:00 go trade"],
    ["01:13:30", "01:14:00 prepare trade", "01:14:30 go trade"],
    ["01:15:00", "01:15:30 prepare trade", "01:16:00 go trade"],
    ["01:16:30", "01:17:00 prepare trade", "01:17:30 go trade"],
    ["01:18:00", "01:18:30 prepare trade", "01:19:00 go trade"],
    ["01:19:30", "01:20:00 prepare trade", "01:20:30 go trade"],
    ["01:21:00", "01:21:30 prepare trade", "01:22:00 go trade"],
    ["01:22:30", "01:23:00 prepare trade", "01:23:30 go trade"],
    ["01:24:00", "01:24:30 prepare trade", "01:25:00 go trade"],
    ["01:25:30", "01:26:00 prepare trade", "01:26:30 go trade"],
    ["01:27:00", "01:27:30 prepare trade", "01:28:00 go trade"],
    ["01:28:30", "01:29:00 prepare trade", "01:29:30 go trade"],
    ["01:30:00", "01:30:30 prepare trade", "01:31:00 go trade"],
    ["01:31:30", "01:32:00 prepare trade", "01:32:30 go trade"],
    ["01:33:00", "01:33:30 prepare trade", "01:34:00 go trade"],
    ["01:34:30", "01:35:00 prepare trade", "01:35:30 go trade"],
    ["01:36:00", "01:36:30 prepare trade", "01:37:00 go trade"],
    ["01:37:30", "01:38:00 prepare trade", "01:38:30 go trade"],
    ["01:39:00", "01:39:30 prepare trade", "01:40:00 go trade"],
    ["01:40:30", "01:41:00 prepare trade", "01:41:30 go trade"],
    ["01:42:00", "01:42:30 prepare trade", "01:43:00 go trade"],
    ["01:43:30", "01:44:00 prepare trade", "01:44:30 go trade"],
    ["01:45:00", "01:45:30 prepare trade", "01:46:00 go trade"],
    ["01:46:30", "01:47:00 prepare trade", "01:47:30 go trade"],
    ["01:48:00", "01:48:30 prepare trade", "01:49:00 go trade"],
    ["01:49:30", "01:50:00 prepare trade", "01:50:30 go trade"],
    ["01:51:00", "01:51:30 prepare trade", "01:52:00 go trade"],
    ["01:52:30", "01:53:00 prepare trade", "01:53:30 go trade"],
    ["01:54:00", "01:54:30 prepare trade", "01:55:00 go trade"],
    ["01:55:30", "01:56:00 prepare trade", "01:56:30 go trade"],
    ["01:57:00", "01:57:30 prepare trade", "01:58:00 go trade"],
    ["01:58:30", "01:59:00 prepare trade", "01:59:30 go trade"]
]

# -------- GUI --------
root = tk.Tk()
root.title("Trade Lookup")
root.geometry("550x400")
main_font = tkfont.Font(family="Consolas", size=12)
zoom_win = None
theme_day = {"bg": "white", "fg": "black"}
theme_night = {"bg": "black", "fg": "white"}
theme = theme_day
move_mode = False
move_offset = (0, 0)
minimal_mode = False

# -------- Functions --------
def show_trade(event=None):
    output.delete("1.0", tk.END)
    try:
        mins = int(entry_minutes.get().strip())
    except ValueError:
        output.insert(tk.END, "Invalid input\n")
        return
    for group in trade_table:
        for val in group:
            parts = val.split(":")
            if len(parts) == 3 and int(parts[1]) == mins:
                for line in group:
                    output.insert(tk.END, line + "\n")
                return
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

def select_font():
    fonts = ["Consolas", "Courier", "Arial", "Times New Roman", "Verdana"]
    choice = simpledialog.askstring("Select Font", f"Choose font:\n{', '.join(fonts)}")
    if choice and choice in fonts:
        main_font.configure(family=choice)

def enable_move():
    global move_mode
    move_mode = True
    output.insert(tk.END, "Move Mode Enabled: Drag window anywhere\n")

def start_move(event):
    global move_offset
    if move_mode:
        move_offset = (event.x_root - root.winfo_x(), event.y_root - root.winfo_y())

def do_move(event):
    if move_mode:
        x = event.x_root - move_offset[0]
        y = event.y_root - move_offset[1]
        root.geometry(f"+{x}+{y}")

def stop_move(event):
    global move_mode
    move_mode = False
    output.insert(tk.END, "Move Mode Disabled\n")

def toggle_minimal():
    global minimal_mode
    minimal_mode = not minimal_mode
    if minimal_mode:
        frame_top.pack_forget()
        menu.entryconfig("File", state="disabled")
    else:
        frame_top.pack(pady=5)
        menu.entryconfig("File", state="normal")

# -------- Menu --------
menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Zoom", command=open_zoom)
file_menu.add_command(label="Day/Night", command=toggle_theme)
file_menu.add_command(label="Pin App", command=pin_app)
file_menu.add_separator()
file_menu.add_command(label="Font", command=select_font)
file_menu.add_separator()
file_menu.add_command(label="Move App", command=enable_move)
file_menu.add_separator()
file_menu.add_command(label="Minimal / Focus Mode", command=toggle_minimal)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# -------- UI --------
frame_top = tk.Frame(root)
frame_top.pack(pady=5)

entry_minutes = tk.Entry(frame_top, justify="center", font=main_font, width=10)
entry_minutes.pack(side="left", padx=5)
entry_minutes.bind("<Return>", show_trade)
entry_minutes.insert(0, "0")

btn_generate = tk.Button(frame_top, text="Generate", font=main_font, command=show_trade, width=8)
btn_generate.pack(side="left", padx=5)

btn_clear = tk.Button(frame_top, text="Clear", font=main_font, command=clear_output, width=8)
btn_clear.pack(side="left", padx=5)

# Text with Scrollbars
frame_text = tk.Frame(root)
frame_text.pack(expand=True, fill="both", padx=10, pady=10)
scroll_y = tk.Scrollbar(frame_text, orient="vertical")
scroll_y.pack(side="right", fill="y")
scroll_x = tk.Scrollbar(frame_text, orient="horizontal")
scroll_x.pack(side="bottom", fill="x")
output = tk.Text(frame_text, font=main_font, wrap="none",
                 xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
output.pack(expand=True, fill="both")
scroll_y.config(command=output.yview)
scroll_x.config(command=output.xview)

# Bind move
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", do_move)
root.bind("<ButtonRelease-1>", stop_move)

root.mainloop()
