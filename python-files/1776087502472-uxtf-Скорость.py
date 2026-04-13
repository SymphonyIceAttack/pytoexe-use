import tkinter as tk
import random

root = tk.Tk()
root.title("Измеритель")
root.geometry("320x260")
root.configure(bg="#0b3d91")  # насыщенный синий

# --- Функции ---
def start():
    display_var.set("----")

def result():
    value = round(random.uniform(12.2, 12.8), 1)
    display_var.set(f"{value:.1f}")

def reset():
    display_var.set("")

def close_app():
    root.destroy()

# --- Табло ---
display_var = tk.StringVar()

display_frame = tk.Frame(root, bg="black", bd=5, relief="sunken")
display_frame.pack(pady=20)

display = tk.Label(
    display_frame,
    textvariable=display_var,
    font=("DS-Digital", 42),  # если нет — заменится
    bg="black",
    fg="#00ff66",
    width=6
)
display.pack()

# fallback шрифт если DS-Digital нет
display.config(font=("Courier", 42, "bold"))

# --- Кнопки ---
btn_frame = tk.Frame(root, bg="#0b3d91")
btn_frame.pack(pady=10)

btn_style = {"font": ("Arial", 10, "bold"), "width": 10, "height": 1}

start_btn = tk.Button(btn_frame, text="СТАРТ", bg="#28a745", fg="white", command=start, **btn_style)
start_btn.grid(row=0, column=0, padx=5)

result_btn = tk.Button(btn_frame, text="РЕЗУЛЬТАТ", bg="#ffc107", fg="black", command=result, **btn_style)
result_btn.grid(row=0, column=1, padx=5)

reset_btn = tk.Button(btn_frame, text="СБРОС", bg="#dc3545", fg="white", command=reset, **btn_style)
reset_btn.grid(row=0, column=2, padx=5)

# --- Закрыть ---
close_btn = tk.Button(root, text="Закрыть", command=close_app, width=15)
close_btn.pack(pady=10)

root.mainloop()