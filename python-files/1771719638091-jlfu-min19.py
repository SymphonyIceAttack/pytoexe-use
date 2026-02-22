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
current_index = None
BASE_FONT = 14
current_font = "Segoe UI"
zoom_win = None
scale2_win = None
dark_mode = False
topmost = True
history = []
history_win = None
history_text = None

# ------------------- Root -------------------
root = tk.Tk()
root.title("Trade Lookup + View")
root.geometry("520x400")
root.attributes("-topmost", True)
root.attributes("-alpha",0.95)
main_font = tkfont.Font(family=current_font, size=BASE_FONT)

# ------------------- Functions -------------------
def show_group(index):
    global current_index
    if 0 <= index < len(trade_table):
        current_index = index
        output.config(state="normal")
        output.delete("1.0", tk.END)
        for line in trade_table[index]:
            output.insert(tk.END,line+"\n")
        output.config(state="disabled")

def round_seconds(sec):
    return 0 if sec<15 else 30 if sec<45 else 0, 1  # إذا عدت 30 ارجع +1 دقيقة

def search_trade(event=None):
    """Generate button / Enter"""
    global current_index
    text = entry_minutes.get().strip()
    if not text:  # Live mode
        now = datetime.now()
        mins = now.minute
        sec_raw = now.second
        if sec_raw <15: secs = 0
        elif sec_raw<45: secs=30
        else: 
            secs=0
            mins +=1
    else:
        if ":" not in text:
            messagebox.showerror("Error","Enter MM:SS format")
            return
        try:
            mins, secs = map(int,text.split(":"))
            if secs not in [0,30]:
                messagebox.showerror("Error","Seconds must be 00 or 30")
                return
        except:
            messagebox.showerror("Error","Invalid input")
            return

    target = f"01:{mins:02d}:{secs:02d}"
    for i, group in enumerate(trade_table):
        if group[0]==target:
            show_group(i)
            return
    messagebox.showinfo("Not Found","No matching trade group")

def prev_group(event=None):
    if current_index is not None:
        show_group(current_index-1)

def next_group(event=None):
    if current_index is not None:
        show_group(current_index+1)

def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost",topmost)

def clear_output():
    output.config(state="normal")
    output.delete("1.0", tk.END)
    output.config(state="disabled")

# ------------------- Scale2 -------------------
def open_scale2():
    global scale2_win
    if scale2_win and scale2_win.winfo_exists():
        scale2_win.lift()
        return
    scale2_win = tk.Toplevel(root)
    scale2_win.title("Scale 2")
    scale2_win.geometry("300x80")
    scale2_win.resizable(False, False)

    def on_entry_scale(val):
        entry_minutes.config(font=(current_font,int(float(val))))

    scale = tk.Scale(scale2_win, from_=8, to=28, orient="horizontal", label="Entry Font Size", command=on_entry_scale)
    scale.set(BASE_FONT)
    scale.pack(fill="x", padx=10, pady=10)
    # X لإغلاق
    tk.Button(scale2_win, text="X", command=scale2_win.destroy).pack(pady=2)

# ------------------- UI -------------------
frame_top = tk.Frame(root)
frame_top.pack(pady=5)

entry_minutes = tk.Entry(frame_top,justify="center", font=main_font, width=10)
entry_minutes.pack(pady=5)

# -------- Buttons ◀ ▶ Generate Clear --------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

btn_prev = tk.Button(btn_frame,text="◀", font=main_font, width=5, command=prev_group)
btn_prev.pack(side="left", padx=2)

btn_next = tk.Button(btn_frame,text="▶", font=main_font, width=5, command=next_group)
btn_next.pack(side="left", padx=2)

btn_generate = tk.Button(btn_frame,text="Generate", font=main_font, width=10, command=search_trade)
btn_generate.pack(side="left", padx=5)

btn_clear = tk.Button(btn_frame,text="Clear", font=main_font, width=10, command=clear_output)
btn_clear.pack(side="left", padx=5)

# -------- Output Text --------
output = tk.Text(root,font=main_font, height=6)
output.pack(expand=True, fill="both", padx=10, pady=5)

# ------------------- Menu -------------------
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="History")
file_menu.add_separator()
file_menu.add_command(label="Exit",command=root.quit)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Day / Night")
view_menu.add_separator()
view_menu.add_command(label="Scale", command=open_zoom)
view_menu.add_command(label="Scale 2", command=open_scale2)

# ------------------- Keyboard -------------------
root.bind("<Left>", lambda e: prev_group())
root.bind("<Right>", lambda e: next_group())
root.bind("<Return>", search_trade)

root.mainloop()