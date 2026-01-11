import tkinter as tk
from tkinter import messagebox
import minecraft_launcher_lib
import subprocess

def draw_gradient(canvas, w, h, color1, color2):
    limit = h
    (r1, g1, b1) = canvas.winfo_rgb(color1)
    (r2, g2, b2) = canvas.winfo_rgb(color2)
    r1, g1, b1 = r1 >> 8, g1 >> 8, b1 >> 8
    r2, g2, b2 = r2 >> 8, g2 >> 8, b2 >> 8

    for i in range(limit):
        t = i / float(limit - 1) if limit > 1 else 0
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(0, i, w, i, fill=color)

def launch_minecraft():
    version = version_var.get().strip()
    username = username_var.get().strip()

    if not version:
        messagebox.showerror("Ошибка", "Укажите версию Minecraft.")
        return
    if not username:
        messagebox.showerror("Ошибка", "Укажите свой никнейм.")
        return

    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory().replace('minecraft', 'nexuslauncher')

    try:
        minecraft_launcher_lib.install.install_minecraft_version(version=version, minecraft_directory=minecraft_directory)
    except Exception as e:
        messagebox.showerror("Ошибка установки", f"Не удалось установить версию: {e}")
        return

    options = {
        'username': username,
        'uuid': '',
        'token': ''
    }

    try:
        cmd = minecraft_launcher_lib.command.get_minecraft_command(version=version, minecraft_directory=minecraft_directory, options=options)
        subprocess.call(cmd)
    except Exception as e:
        messagebox.showerror("Ошибка запуска", f"Не удалось запустить Minecraft: {e}")

root = tk.Tk()
root.title("Nexus Launcher")
root.geometry("600x400")
root.resizable(False, False)
canvas = tk.Canvas(root, width=600, height=400, highlightthickness=0)
canvas.pack(fill="both", expand=True)

draw_gradient(canvas, 600, 400, "#0a5b20", "#000000")

container_width = 400
container_height = 250

version_var = tk.StringVar()
username_var = tk.StringVar()

version_label = tk.Label(text="Версия Minecraft:", bg="#000000", fg="#aaffaa")
version_entry = tk.Entry(textvariable=version_var, width=30)

username_label = tk.Label(text="Никнейм:", bg="#000000", fg="#aaffaa")
username_entry = tk.Entry(textvariable=username_var, width=30)

launch_btn = tk.Button(text="Запустить Minecraft", command=launch_minecraft, bg="#4CAF50", fg="white", width=25)

hint = tk.Label(text="NEXUS LAUNCHER", fg="white", bg="#000000")

canvas.create_window(300, 150, window=version_label, width=180, height=25)  # Центрируем
canvas.create_window(300, 185, window=version_entry)
canvas.create_window(300, 220, window=username_label, width=180, height=25)
canvas.create_window(300, 255, window=username_entry)
canvas.create_window(300, 290, window=launch_btn)
canvas.create_window(300, 330, window=hint, width=380)

root.mainloop()