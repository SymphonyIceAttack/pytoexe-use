import tkinter as tk
from datetime import datetime, timedelta

# ---------- Logic ----------
def calculate():
    try:
        mins = int(entry_minutes.get())
        base_time = datetime.strptime("00:00:00", "%H:%M:%S") + timedelta(minutes=mins)

        t1 = (base_time - timedelta(seconds=90)).strftime("%H:%M:%S")
        t2 = (base_time - timedelta(seconds=60)).strftime("%H:%M:%S")
        t3 = (base_time - timedelta(seconds=30)).strftime("%H:%M:%S")

        out1.config(text=t1)
        out2.config(text=f"{t2}  prepare trade")
        out3.config(text=f"{t3}  go trade")

    except:
        out1.config(text="Invalid")
        out2.config(text="")
        out3.config(text="")

# ---------- UI Controls ----------
def toggle_top():
    root.attributes("-topmost", not root.attributes("-topmost"))

def toggle_theme():
    global dark
    dark = not dark
    bg = "#1e1e1e" if dark else "#f0f0f0"
    fg = "white" if dark else "black"

    root.config(bg=bg)
    for w in widgets:
        w.config(bg=bg, fg=fg)

def scale_ui(val):
    size = int(val)
    for w in widgets:
        w.config(font=("Arial", size))

def toggle_panel():
    if panel.winfo_viewable():
        panel.pack_forget()
    else:
        panel.pack(pady=10)

# ---------- Window ----------
root = tk.Tk()
root.title("Trade Minute Converter")
root.geometry("420x360")

dark = False

# ---------- Menu ----------
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin App", command=toggle_top)
file_menu.add_command(label="Day / Night", command=toggle_theme)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# ---------- Content ----------
panel = tk.Frame(root)
panel.pack(pady=10)

lbl = tk.Label(panel, text="Enter Minutes")
lbl.pack()

entry_minutes = tk.Entry(panel, justify="center")
entry_minutes.pack()

btn = tk.Button(panel, text="Calculate", command=calculate)
btn.pack(pady=5)

out1 = tk.Label(panel)
out1.pack()

out2 = tk.Label(panel)
out2.pack()

out3 = tk.Label(panel)
out3.pack()

# ---------- Scale ----------
scale = tk.Scale(root, from_=10, to=26, orient="horizontal", label="Zoom", command=scale_ui)
scale.set(14)
scale.pack(fill="x", padx=10)

toggle_btn = tk.Button(root, text="Hide / Show Panel", command=toggle_panel)
toggle_btn.pack(pady=5)

widgets = [lbl, entry_minutes, btn, out1, out2, out3, toggle_btn]

root.mainloop()
