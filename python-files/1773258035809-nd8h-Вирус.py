import tkinter as tk

CORRECT_PASSWORD = "Zachet"

def check_password():
    entered_password = password_entry.get()
    if entered_password == CORRECT_PASSWORD:
        root.destroy()
    else:
        status_label.config(text="Неверный пароль! Попробуйте ещё раз.", fg="red")

def prevent_close():
    return

root = tk.Tk()

# Настоящий полноэкранный режим (с рамкой)
root.attributes('-fullscreen', True)

main_frame = tk.Frame(root, bg="black")
main_frame.pack(fill="both", expand=True)

title_label = tk.Label(
    main_frame,
    text="ХАХАХХАХАХХАХА! Чтобы расблокировать доступ ПК поставте зачёт!",
    font=("Helvetica", 32, "bold"),
    fg="white",
    bg="black"
)
title_label.pack(pady=100)

password_entry = tk.Entry(
    main_frame,
    font=("Helvetica", 24),
    show="*",
    width=20,
    justify="center"
)
password_entry.pack(pady=20)

submit_button = tk.Button(
    main_frame,
    text="Подтвердить",
    font=("Helvetica", 18),
    command=check_password,
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10
)
submit_button.pack(pady=10)

status_label = tk.Label(
    main_frame,
    text="",
    font=("Helvetica", 16),
    fg="white",
    bg="black"
)
status_label.pack(pady=20)

password_entry.focus()
root.protocol("WM_DELETE_WINDOW", prevent_close)
root.bind('<Escape>', lambda e: root.destroy())

root.mainloop()