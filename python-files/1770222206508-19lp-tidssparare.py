import tkinter as tk
from datetime import datetime

def save_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("saved_time.txt", "a") as file:
        file.write(current_time + "\n")
    status_label.config(text=f"Tiden sparad: {current_time}")

def update_time():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_label.config(text=now)
    root.after(1000, update_time)  # Uppdaterar varje sekund

root = tk.Tk()
root.title("Tidssparare")

time_label = tk.Label(root, text="", font=("Helvetica", 24))
time_label.pack(pady=20)

save_button = tk.Button(root, text="Spara tid", font=("Helvetica", 16), command=save_time)
save_button.pack(pady=10)

status_label = tk.Label(root, text="", font=("Helvetica", 12))
status_label.pack(pady=10)

update_time()
root.mainloop()
