import sys
import subprocess
from pathlib import Path
import shlex

# Цвета ANSI
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

print(RED + r'''
██████╗ ██╗    ██╗███╗   ██╗██████╗ ██████╗ 
██╔══██╗██║    ██║████╗  ██║██╔══██╗██╔══██╗
██████╔╝██║ █╗ ██║██╔██╗ ██║██║  ██║██████╔╝
██╔═══╝ ██║███╗██║██║╚██╗██║██║  ██║██╔══██╗
██║     ╚███╔███╔╝██║ ╚████║██████╔╝██████╔╝
╚═╝      ╚══╝╚══╝ ╚═╝  ╚═══╝╚═════╝ ╚═════╝ 
''' + RESET)

print(RED + r'''
PROFESSIONAL SOFT V2.2 by PwnDB
''' + RESET)

def list_py_files():
    cwd = Path.cwd()
    files = sorted(p for p in cwd.glob("*.py"))
    try:
        me = Path(__file__).resolve()
        files = [f for f in files if f.resolve() != me]
    except NameError:
        pass
    return files

def print_menu(files):
    if not files:
        print(f"{RED}  (иди нахуй){RESET}")
    else:
        for i, f in enumerate(files, 1):
            print(f"{GREEN}  {i}. {f.stem}{RESET}")

def run_file(path, extra_args=None):
    cmd = [sys.executable, str(path)]
    if extra_args:
        cmd += extra_args
    try:
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print(f"\nПроцесс завершился с кодом: {res.returncode}")
    except KeyboardInterrupt:
        print("\nЗапуск прерван пользователем (Ctrl+C).")
    except Exception as e:
        print(f"\nОшибка при запуске: {e}")

def main():
    while True:
        files = list_py_files()
        print_menu(files)
        choice = input("> ").strip()
        if choice.lower() in ("e", "quit", "exit"):
            print("Выход.")
            break
        if choice.lower() == "r":
            continue
        if not files:
            print("иди нахуй.")
            continue
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                path = files[idx]
                run_file(path, [])
            else:
                print("Неверный номер.")
            continue
        parts = shlex.split(choice)
        if parts and parts[0].isdigit():
            idx = int(parts[0]) - 1
            if 0 <= idx < len(files):
                path = files[idx]
                extra = parts[1:]
                run_file(path, extra)
            else:
                print("Неверный номер.")
            continue
        print("Неизвестная команда.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")