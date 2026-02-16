import tkinter as tk
import tkinter.font as tkfont
from datetime import timedelta

def generate_table():
    output.delete("1.0", tk.END)

    try:
        start_minutes = int(entry_minutes.get().strip())
    except ValueError:
        output.insert(tk.END, "Invalid minutes\n")
        return

    current = timedelta(minutes=start_minutes)
    end_time = current + timedelta(hours=1)

    while current < end_time:
        t0 = str(current)
        t1 = str(current + timedelta(seconds=30))
        t2 = str(current + timedelta(seconds=60))

        # format HH:MM:SS
        t0 = t0.zfill(8)
        t1 = t1.zfill(8)
        t2 = t2.zfill(8)

        output.insert(tk.END, f"{t0}\n")
        output.insert(tk.END, f"{t1} prepare trade\n")
        output.insert(tk.END, f"{t2} go trade\n\n")

        current += timedelta(seconds=30)

# -------- Zoom Window --------
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

# -------- App --------
root = tk.Tk()
root.title("Trade Time Table")
root.geometry("540x620")

main_font = tkfont.Font(family="Consolas", size=12)
zoom_win = None

# -------- Menu --------
menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Zoom", command=open_zoom)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# -------- UI --------
tk.Label(root, text="Enter start minutes", font=main_font).pack(pady=5)

entry_minutes = tk.Entry(root, justify="center", font=main_font)
entry_minutes.pack(pady=5)
entry_minutes.insert(0, "60")

tk.Button(root, text="Generate Table", command=generate_table, font=main_font).pack(pady=10)

output = tk.Text(root, font=main_font)
output.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
