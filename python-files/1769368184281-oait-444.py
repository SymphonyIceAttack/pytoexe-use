import tkinter as tk
from tkinter import messagebox
import json
import os
from pypresence import Presence
import time
import threading

# === Настройки ===
CONFIG_FILE = "config.json"  # Файл для сохранения Application ID
rpc = None
connected = False
client_id = ""

# === Загрузка сохранённого ID ===
def load_config():
    global client_id
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                client_id = data.get("client_id", "")
                entry_id.insert(0, client_id)
        except Exception as e:
            messagebox.showwarning("Предупреждение", f"Не удалось загрузить настройки:\n{e}")

# === Сохранение ID ===
def save_client_id():
    global client_id
    user_input = entry_id.get().strip()
    if not user_input.isdigit():
        messagebox.showerror("Ошибка", "Application ID должен содержать только цифры!")
        return
    client_id = user_input
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"client_id": client_id}, f)
        messagebox.showinfo("Успех", "✅ Application ID сохранён!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить ID:\n{e}")

# === Подключение RPC ===
def connect_rpc():
    global rpc, connected
    if not client_id:
        messagebox.showwarning("Внимание", "Сначала введите и сохраните Application ID!")
        return

    try:
        rpc = Presence(client_id)
        rpc.connect()
        connected = True

        rpc.update(
            state="🎮 Баннер включён!",
            details="Управляется через .exe",
            large_image="banner_bg",
            large_text="Кастом активность",
            small_image="discord_logo",
            small_text="Discord RPC",
            buttons=[{"label": "Мой профиль", "url": "https://discord.com/users/123456789"}]
        )
        messagebox.showinfo("Готово", "✅ Активность включена!")
    except Exception as e:
        if "Invalid Client ID" in str(e):
            messagebox.showerror("Ошибка", "❌ Неверный Application ID. Проверь ID и иконки в Discord Dev.")
        else:
            messagebox.showerror("Ошибка", f"Не удалось подключиться:\n{e}")
        connected = False

# === Включить активность ===
def start_activity():
    global connected
    if connected:
        messagebox.showinfo("Статус", "Активность уже включена!")
        return
    thread = threading.Thread(target=connect_rpc, daemon=True)
    thread.start()

# === Выключить активность ===
def stop_activity():
    global connected, rpc
    if not connected:
        messagebox.showinfo("Статус", "Активность и так выключена.")
        return
    try:
        rpc.clear()
        rpc.close()
        connected = False
        messagebox.showinfo("Готово", "❌ Активность выключена.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при отключении:\n{e}")

# === Создание интерфейса ===
app = tk.Tk()
app.title("Discord Баннер")
app.geometry("350x300")
app.resizable(False, False)

# === Заголовок ===
tk.Label(app, text="Discord Баннер Активности", font=("Arial", 14, "bold")).pack(pady=10)

# === Поле ввода ID ===
frame_id = tk.Frame(app)
frame_id.pack(pady=5)
tk.Label(frame_id, text="Application ID:").pack(anchor="w")
entry_id = tk.Entry(frame_id, width=40)
entry_id.pack(pady=2)
tk.Button(frame_id, text="Сохранить ID", command=save_client_id).pack(pady=5)

# === Управление активностью ===
tk.Label(app, text="Управление активностью:", font=("Arial", 10)).pack(pady=10)

btn_frame = tk.Frame(app)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="✅ Включить", width=15, command=start_activity).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="❌ Выключить", width=15, command=stop_activity).grid(row=0, column=1, padx=5)

# === Статус подключения ===
status_label = tk.Label(app, text="💡 Введите Application ID и сохраните", fg="gray")
status_label.pack(pady=10)

# === Загружаем сохранённый ID при запуске ===
load_config()

# === Запуск ===
app.mainloop()
