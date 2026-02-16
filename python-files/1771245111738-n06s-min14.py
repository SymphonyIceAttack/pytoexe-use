import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from tkinter import simpledialog, messagebox

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
current_scale = 1.0
zoom_win = None
dark_mode = False
topmost = True
history = []
history_win = None
history_text = None
move_mode = False

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + View")
root.geometry("520x400")
root.attributes("-topmost", True)
root.attributes("-alpha",0.95)
main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- Functions -------------------
def show_trade(event=None):
    output.delete("1.0", tk.END)
    try:
        mins = int(entry_minutes.get().strip())
    except ValueError:
        output.insert(tk.END,"Invalid input\n")
        return
    # البحث في الجدول عن أي مجموعة تحتوي الدقيقة
    for group in trade_table:
        for val in group:
            parts = val.split(":")
            if len(parts)==3 and int(parts[1])==mins:
                for line in group:
                    output.insert(tk.END,line+"\n")
                return
    output.insert(tk.END,"Not found\n")

def clear_output():
    output.delete("1.0", tk.END)

# ------------------- HISTORY -------------------
def add_history(minute):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(f"{len(history)+1}. Minute: {minute} | {ts}")
    update_history()

def update_history():
    if history_win and history_win.winfo_exists():
        history_text.config(state="normal")
        history_text.delete("1.0", tk.END)
        for h in history:
            history_text.insert(tk.END,h+"\n")
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
    history_text = tk.Text(history_win,state="disabled")
    history_text.pack(fill="both",expand=True)
    tk.Button(history_win,text="Clear History",command=clear_history).pack(pady=5)
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
    zoom_win.resizable(False,False)
    def on_zoom(val):
        main_font.configure(size=int(float(val)))
    scale = tk.Scale(zoom_win, from_=10, to=28, orient="horizontal", label="Font Size", command=on_zoom)
    scale.set(main_font.cget("size"))
    scale.pack(fill="x", padx=10, pady=10)

# ------------------- Day/Night -------------------
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "black" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry_minutes.config(bg=bg, fg=fg)
    output.config(bg=bg, fg=fg)

# ------------------- Pin -------------------
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost",topmost)

# ------------------- UI -------------------
frame_top = tk.Frame(root)
frame_top.pack(pady=5)

entry_minutes = tk.Entry(frame_top,justify="center", font=main_font, width=10)
entry_minutes.pack(side="left", padx=5)
entry_minutes.bind("<Return>", show_trade)
entry_minutes.insert(0,"0")

btn_generate = tk.Button(frame_top,text="Generate", font=main_font, command=show_trade, width=10)
btn_generate.pack(side="left", padx=5)

btn_clear = tk.Button(frame_top,text="Clear", font=main_font, command=clear_output, width=10)
btn_clear.pack(side="left", padx=5)

output = tk.Text(root,font=main_font)
output.pack(expand=True, fill="both", padx=10, pady=10)

# ------------------- Menu -------------------
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="History",command=open_history)
file_menu.add_separator()
file_menu.add_command(label="Exit",command=root.quit)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Scale",command=open_zoom)

root.mainloop()
