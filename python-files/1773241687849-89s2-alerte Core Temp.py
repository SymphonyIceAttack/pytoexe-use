import tkinter as tk

def update_countdown():
    global count
    label_count.config(text=f"Arrêt dans : {count} s")
    if count > 0:
        count -= 1
        root.after(1000, update_countdown)

def close_window(event=None):
    root.destroy()

root = tk.Tk()
root.title("Alerte système")
root.attributes("-fullscreen", True)
root.configure(bg="#0078D7")

root.bind("<Escape>", close_window)  # touche echap pour fermer

frame = tk.Frame(root, bg="#0078D7")
frame.pack(expand=True)

label_icon = tk.Label(
    frame,
    text="⚠",
    font=("Segoe UI", 90),
    fg="white",
    bg="#0078D7"
)
label_icon.pack(pady=20)

label_text = tk.Label(
    frame,
    text="ALERTE CORE TEMP\nVotre PC va se mettre en veille profonde",
    font=("Segoe UI", 30),
    fg="white",
    bg="#0078D7",
    justify="center"
)
label_text.pack(pady=20)

count = 30

label_count = tk.Label(
    frame,
    text="",
    font=("Segoe UI", 50),
    fg="white",
    bg="#0078D7"
)
label_count.pack(pady=40)

update_countdown()

root.mainloop()