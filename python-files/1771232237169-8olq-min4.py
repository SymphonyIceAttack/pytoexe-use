import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta

def generate_times():
    output.delete("1.0", tk.END)

    try:
        minute = int(entry_minutes.get().strip())
        if minute < 0 or minute > 59:
            raise ValueError
    except ValueError:
        output.insert(tk.END, "Enter minute from 0 to 59\n")
        return

    # base time: 01:MM:30
    base = datetime.strptime(f"01:{minute:02d}:30", "%H:%M:%S")

    t0 = base.strftime("%H:%M:%S")
    t1 = (base + timedelta(seconds=30)).strftime("%H:%M:%S")
    t2 = (base + timedelta(seconds=60)).strftime("%H:%M:%S")

    output.insert(tk.END, f"{t0}\n")
    output.insert(tk.END, f"{t1} prepare trade\n")
    output.insert(tk.END, f"{t2} go trade\n")

# ---------- Zoom Window ----------
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

    scale = tk.Scale(
        zoom_win,
        from_=10,
        to=28,
        orient="horizontal",
        label="Font Size",
        command=on_zoom
    )
    scale.set(main_font.cget("size"))
    scale.pack(fill="x", padx=10, pady=10)

# ---------- App ----------
root = tk.Tk()
root.title("Trade Time Generator")
root.geometry("520x420")

main_font = tkfont.Font(family="Consolas", size=12)
zoom_win = None

# ---------- Menu ----------
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Zoom", command=open_zoom)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# ---------- UI ----------
tk.Label(root, text="Enter minute (0–59)", font=main_font).pack(pady=5)

entry_minutes = tk.Entry(root, justify="center", font=main_font)
entry_minutes.pack(pady=5)
entry_minutes.insert(0, "37")

tk.Button(root, text="Generate", command=generate_times, font=main_font).pack(pady=10)

output = tk.Text(root, font=main_font, height=6)
output.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
