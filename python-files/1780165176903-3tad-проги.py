import customtkinter as ctk
import keyboard
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Состояние программы (по умолчанию включена)
is_active = True

# ------------------------
# ТВОИ ДАННЫЕ
# ------------------------

TEXTS = {
    "NUMPAD7": "control folders",
    "NUMPAD8": "ТУТ_ВСТАВЬ_СВОЙ_DOOMSDAY_ТЕКСТ",
    "NUMPAD9": "ТУТ_ВСТАВЬ_СВОЙ_EVERSING_ТЕКСТ",
    "NUMPAD4": "ТУТ_ВСТАВЬ_СВОЙ_EVERSING_CFG_ТЕКСТ"
}

PROGRAMS = {
    "Everything": "https://www.voidtools.com/Everything-1.5.0.1404a.x64.zip",
    "Injgen": "https://github.com/NotRequiem/InjGen/releases/tag/v2.0",
    "ShellBag": "https://privazer.com/ru/download-shellbag-analyzer-shellbag-cleaner.php",
    "System Informer": "https://systeminformer.com/",
    "LastActivityView": "https://www.nirsoft.net/utils/computer_activity_view.html",
    "USBDriveLog": "https://www.nirsoft.net/utils/usb_drive_log.html",
    "HolyChack": "https://mods.holyworld.me/mods-review"
}

# ------------------------
# КОПИРОВАНИЕ
# ------------------------

def copy_text(text):
    root.clipboard_clear()
    root.clipboard_append(text)

def hotkey_copy(key):
    # Сработает только если программа активна
    if is_active and key in TEXTS:
        copy_text(TEXTS[key])

# ------------------------
# ОКНО С ПРОГРАММАМИ
# ------------------------

def open_programs():
    # Сработает только если программа активна
    if not is_active:
        return

    win = ctk.CTkToplevel(root)
    win.title("Программы")
    win.geometry("350x300")
    win.attributes("-topmost", True)

    frame = ctk.CTkFrame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    for name, link in PROGRAMS.items():
        def click(l=link):
            copy_text(l)
            win.destroy()

        btn = ctk.CTkButton(
            frame,
            text=name,
            command=click,
            height=35
        )
        btn.pack(fill="x", pady=3)

# ------------------------
# ПЕРЕКЛЮЧЕНИЕ СОСТОЯНИЯ (DELETE)
# ------------------------

def toggle_program():
    global is_active
    is_active = not is_active
    
    # Визуально меняем текст в окне, чтобы ты видел, работает оно или нет
    if is_active:
        status_label.configure(text="СТАТУС: ВКЛ", text_color="green")
    else:
        status_label.configure(text="СТАТУС: ВЫКЛ", text_color="red")

# ------------------------
# GUI
# ------------------------

root = ctk.CTk()
root.title("Overlay")
root.geometry("320x220") # Немного увеличил высоту для индикатора статуса
root.attributes("-topmost", True)

title = ctk.CTkLabel(
    root,
    text="AnyDesk Overlay",
    font=("Segoe UI", 22, "bold")
)
title.pack(pady=5)

# Индикатор работы программы
status_label = ctk.CTkLabel(
    root,
    text="СТАТУС: ВКЛ",
    font=("Segoe UI", 14, "bold"),
    text_color="green"
)
status_label.pack()

info = ctk.CTkLabel(
    root,
    text="""
Num7  - невидм текст
Num8  - c.doomsday
Num9  - c.eversing
Num4  - c.eversing cfg
Num1  - программы
--------------------
Delete - ВКЛ / ВЫКЛ
"""
)
info.pack(pady=5)

# ------------------------
# HOTKEYS
# ------------------------

keyboard.add_hotkey("num 7", lambda: hotkey_copy("NUMPAD7"))
keyboard.add_hotkey("num 8", lambda: hotkey_copy("NUMPAD8"))
keyboard.add_hotkey("num 9", lambda: hotkey_copy("NUMPAD9"))
keyboard.add_hotkey("num 4", lambda: hotkey_copy("NUMPAD4"))
keyboard.add_hotkey("num 1", open_programs)

# Горячая клавиша для включения/выключения
keyboard.add_hotkey("delete", toggle_program)

root.mainloop()