import tkinter as tk
import random

root = tk.Tk()
root.title("nuddle.exe")
root.geometry("500x300")
root.configure(bg="black")

label = tk.Label(root, text="Initializing...", fg="lime", bg="black", font=("Consolas", 16))
label.pack(pady=40)

progress = tk.Label(root, text="0%", fg="white", bg="black", font=("Consolas", 14))
progress.pack()

messages = [
    "Connecting to server...",
    "Bypassing firewall...",
    "Injecting payload...",
    "Downloading data...",
    "Access granted...",
    "Sending packets...",
    "Decrypting files..."
]

percent = 0

def update():
    global percent

    if percent < 100:
        percent += random.randint(1, 8)

        if percent > 100:
            percent = 100

        progress.config(text=str(percent) + "%")
        label.config(text=random.choice(messages))

        root.after(random.randint(100, 400), update)
    else:
        label.config(text="😈 YOU GOT NUDDLED 😈")
        progress.config(text="PRANK SUCCESS 😂")

update()

root.mainloop()