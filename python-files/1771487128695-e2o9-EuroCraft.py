import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import subprocess
import minecraft_launcher_lib as mll
import random

# ------------------ Папки лаунчера ------------------
BASE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "EuroCraft")
VERSIONS_DIR = os.path.join(BASE_DIR, "Versions")
MODS_DIR = os.path.join(BASE_DIR, "Mods")
RESOURCES_DIR = os.path.join(BASE_DIR, "ResourcePacks")
SHADERS_DIR = os.path.join(BASE_DIR, "Shaders")
SAVES_DIR = os.path.join(BASE_DIR, "Saves")
PROFILES_DIR = os.path.join(BASE_DIR, "Profiles")
SKINS_DIR = os.path.join(BASE_DIR, "Skins")
DEFAULT_SKINS_DIR = os.path.join(BASE_DIR, "default_skins")

for folder in [VERSIONS_DIR, MODS_DIR, RESOURCES_DIR, SHADERS_DIR, SAVES_DIR, PROFILES_DIR, SKINS_DIR, DEFAULT_SKINS_DIR]:
    os.makedirs(folder, exist_ok=True)

# ------------------ Авто ник ------------------
COUNTER_FILE = os.path.join(BASE_DIR, "counter.txt")
if os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "r") as f:
        counter = int(f.read().strip())
else:
    counter = 1
default_nick = f"{counter:04d}_Player"
with open(COUNTER_FILE, "w") as f:
    f.write(str(counter+1))

# ------------------ Профили ------------------
PROFILES_FILE = os.path.join(PROFILES_DIR, "profiles.txt")
if os.path.exists(PROFILES_FILE):
    with open(PROFILES_FILE, "r") as f:
        profiles = [line.strip() for line in f.readlines()]
else:
    profiles = [default_nick]
    with open(PROFILES_FILE, "w") as f:
        f.write(default_nick + "\n")

# ------------------ Скины ------------------
profile_skins_file = os.path.join(SKINS_DIR, "profile_skins.txt")
if os.path.exists(profile_skins_file):
    with open(profile_skins_file, "r") as f:
        profile_skins = dict(line.strip().split("::") for line in f.readlines())
else:
    profile_skins = {}

def load_skin_image(profile):
    """Загрузить скин текущего профиля или случайный"""
    path = profile_skins.get(profile)
    if path and os.path.exists(path):
        img = Image.open(path)
    else:
        # Рандомные стандартные скины
        default_skin = random.choice(["steve.png", "alex.png"])
        img_path = os.path.join(DEFAULT_SKINS_DIR, default_skin)
        if not os.path.exists(img_path):
            # Если файлов нет, создаём заглушку
            img = Image.new("RGB", (64,64), (128,128,128))
        else:
            img = Image.open(img_path)
    img = img.resize((64,64))
    return ImageTk.PhotoImage(img)

def change_skin():
    profile = profile_box.get()
    file_path = filedialog.askopenfilename(
        title="Выберите скин PNG",
        filetypes=[("PNG images", "*.png")]
    )
    if file_path:
        profile_skins[profile] = file_path
        with open(profile_skins_file, "w") as f:
            for p, s in profile_skins.items():
                f.write(f"{p}::{s}\n")
        skin_image = load_skin_image(profile)
        skin_label.config(image=skin_image)
        skin_label.image = skin_image
        messagebox.showinfo("EuroCraft", f"Скин для профиля '{profile}' изменён!")

# ------------------ Список версий ------------------
all_versions = mll.utils.get_version_list()
versions = [v["id"] for v in all_versions]

# ------------------ Функции ------------------
def launch():
    version_id = version_box.get()
    nick = nick_entry.get().strip()
    if nick == "":
        nick = default_nick

    options = {
        "username": nick,
        "uuid": "offline",
        "token": "",
        "game_directory": BASE_DIR
    }

    def run():
        try:
            status_label.config(text=f"Скачивание версии {version_id}...")
            mll.install.install_minecraft_version(version_id, VERSIONS_DIR)
            status_label.config(text="Запуск Minecraft...")

            cmd = mll.command.get_minecraft_command(version_id, VERSIONS_DIR, options)
            subprocess.Popen(cmd)
            status_label.config(text="Minecraft запущен 🎮")

        except Exception as e:
            status_label.config(text=f"Ошибка: {e}")

    threading.Thread(target=run).start()

def add_profile():
    new_nick = simpledialog.askstring("Новый профиль", "Введите ник:")
    if new_nick and new_nick not in profiles:
        profiles.append(new_nick)
        with open(PROFILES_FILE, "a") as f:
            f.write(new_nick + "\n")
        update_profiles()
        messagebox.showinfo("EuroCraft", f"Профиль '{new_nick}' добавлен!")

def update_profiles():
    profile_box['values'] = profiles
    if profiles:
        profile_box.set(profiles[-1])

def change_profile(event):
    nick_entry.delete(0, tk.END)
    nick_entry.insert(0, profile_box.get())
    # обновляем скин
    profile = profile_box.get()
    skin_img = load_skin_image(profile)
    skin_label.config(image=skin_img)
    skin_label.image = skin_img

# ------------------ GUI ------------------
root = tk.Tk()
root.title("EuroCraft Launcher")
root.geometry("550x540")
root.resizable(False, False)

# Заголовок
title_label = tk.Label(root, text="EuroCraft Launcher", font=("Arial", 20, "bold"))
title_label.pack(pady=10)

# Профили
profile_frame = tk.Frame(root)
profile_frame.pack(pady=5)
profile_box = ttk.Combobox(profile_frame, values=profiles, width=25)
profile_box.pack(side=tk.LEFT)
profile_box.bind("<<ComboboxSelected>>", change_profile)
add_profile_btn = tk.Button(profile_frame, text="Создать/сменить профиль", command=add_profile)
add_profile_btn.pack(side=tk.LEFT, padx=5)

# Версии
version_label = tk.Label(root, text="Выберите версию Minecraft:")
version_label.pack(pady=5)
version_box = ttk.Combobox(root, values=versions, width=25)
version_box.pack()
version_box.set(versions[-1])

# Ник
nick_label = tk.Label(root, text="Ник (offline):")
nick_label.pack(pady=5)
nick_entry = tk.Entry(root)
nick_entry.pack()
nick_entry.insert(0, default_nick)

# Скины
skin_frame = tk.Frame(root)
skin_frame.pack(pady=5)
skin_label = tk.Label(skin_frame)
skin_label.pack(side=tk.LEFT)
change_skin_btn = tk.Button(skin_frame, text="Сменить скин", command=change_skin)
change_skin_btn.pack(side=tk.LEFT, padx=5)
update_profiles()
change_profile(None)

# Кнопка запуска
launch_btn = tk.Button(root, text="▶ Запустить Minecraft", command=launch, bg="#4CAF50", fg="white")
launch_btn.pack(pady=10)

# Статус
status_label = tk.Label(root, text="Готово", anchor="w")
status_label.pack(fill=tk.X, pady=5)

# Моды (список для будущей интеграции)
mods_frame = tk.LabelFrame(root, text="Моды (Fabric/FML)", padx=5, pady=5)
mods_frame.pack(fill="both", expand=True, padx=10, pady=5)

mods_listbox = tk.Listbox(mods_frame, selectmode=tk.MULTIPLE, height=10)
mods_listbox.pack(side=tk.LEFT, fill="both", expand=True)
mods_scroll = tk.Scrollbar(mods_frame, orient="vertical")
mods_scroll.config(command=mods_listbox.yview)
mods_listbox.config(yscrollcommand=mods_scroll.set)
mods_scroll.pack(side=tk.RIGHT, fill="y")

# Прогресс-бар
progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate")
progress.pack(pady=5)

root.mainloop()
