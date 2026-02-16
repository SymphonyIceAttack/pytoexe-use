# trade_minute_converter.py
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime, timedelta
import sys
import os

def resource_path(relative):
    """When frozen by PyInstaller this finds the real path to bundled files.
       Safe to call even when not frozen."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # pyinstaller temporary folder
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative)

def calculate():
    s = entry_minutes.get().strip()
    try:
        mins = int(s)
    except ValueError:
        show_invalid()
        return

    # start from midnight and add minutes (wraps within 24h)
    base_time = datetime.strptime("00:00:00", "%H:%M:%S") + timedelta(minutes=mins)
    t90 = (base_time - timedelta(seconds=90)).strftime("%H:%M:%S")
    t60 = (base_time - timedelta(seconds=60)).strftime("%H:%M:%S")
    t30 = (base_time - timedelta(seconds=30)).strftime("%H:%M:%S")

    out1_var.set(t90)
    out2_var.set(f"{t60}    prepare trade")
    out3_var.set(f"{t30}    go trade")

def show_invalid():
    out1_var.set("Invalid minutes")
    out2_var.set("")
    out3_var.set("")

def toggle_top():
    current = bool(root.attributes("-topmost"))
    root.attributes("-topmost", not current)

def toggle_theme():
    global dark
    dark = not dark
    apply_theme()

def apply_theme():
    bg = "#1e1e1e" if dark else "#f0f0f0"
    fg = "white" if dark else "black"
    entry_bg = "#2b2b2b" if dark else "white"

    root.config(bg=bg)
    panel.config(bg=bg)
    controls_frame.config(bg=bg)
    for w in all_widgets:
        try:
            w.config(bg=bg, fg=fg)
        except Exception:
            # some widgets (like Scale on some platforms) don't like these keys
            try:
                w.config(foreground=fg)
            except Exception:
                pass
    # entries need explicit background/foreground
    try:
        entry_minutes.config(bg=entry_bg, fg=fg, insertbackground=fg)
    except Exception:
        pass

def scale_ui(val):
    size = int(float(val))
    main_font.configure(size=size)

def toggle_panel():
    if panel.winfo_ismapped():
        panel.pack_forget()
        toggle_btn.config(text="Show Panel")
    else:
        panel.pack(pady=10)
        toggle_btn.config(text="Hide Panel")

def on_enter_key(event):
    calculate()

def main():
    global root, panel, entry_minutes, out1_var, out2_var, out3_var
    global all_widgets, main_font, controls_frame, toggle_btn, dark

    dark = False

    root = tk.Tk()
    root.title("Trade Minute Converter")
    root.geometry("460x360")

    # font object so scaling updates everywhere
    main_font = tkfont.Font(family="Arial", size=14)

    # Menu
    menu = tk.Menu(root)
    root.config(menu=menu)
    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Pin App", command=toggle_top)
    file_menu.add_command(label="Day / Night", command=toggle_theme)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    # Panel (input + outputs)
    panel = tk.Frame(root)
    panel.pack(pady=10, fill="x")

    lbl = tk.Label(panel, text="Enter minutes (integer):", font=main_font)
    lbl.pack()

    entry_minutes = tk.Entry(panel, justify="center", font=main_font)
    entry_minutes.pack(padx=10, pady=6)
    entry_minutes.bind("<Return>", on_enter_key)

    btn = tk.Button(panel, text="Calculate", command=calculate, font=main_font)
    btn.pack(pady=6)

    out1_var = tk.StringVar(value="")
    out2_var = tk.StringVar(value="")
    out3_var = tk.StringVar(value="")

    out1 = tk.Label(panel, textvariable=out1_var, font=main_font)
    out1.pack(pady=2)
    out2 = tk.Label(panel, textvariable=out2_var, font=main_font)
    out2.pack(pady=2)
    out3 = tk.Label(panel, textvariable=out3_var, font=main_font)
    out3.pack(pady=2)

    # Controls frame (scale + toggle)
    controls_frame = tk.Frame(root)
    controls_frame.pack(fill="x", padx=10)

    scale = tk.Scale(controls_frame, from_=10, to=26, orient="horizontal",
                     label="Zoom (font size)", command=scale_ui)
    scale.set(14)
    scale.pack(side="left", fill="x", expand=True, padx=5)

    toggle_btn = tk.Button(controls_frame, text="Hide Panel", command=toggle_panel, font=main_font)
    toggle_btn.pack(side="right", padx=5)

    # collect widgets for theme/scaling updates
    all_widgets = [lbl, entry_minutes, btn, out1, out2, out3, scale, toggle_btn, panel, controls_frame]

    apply_theme()  # initial theme

    # start
    root.mainloop()

if __name__ == "__main__":
    main()
