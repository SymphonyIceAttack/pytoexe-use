import psutil
import subprocess
import time
import sys
import os
from pynput import keyboard

def find_process_id(process_name):
    """Находит PID процесса по имени"""
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def kill_explorer():
    """Завершает процесс explorer.exe"""
    try:
        pid = find_process_id('explorer.exe')
        if pid:
            proc = psutil.Process(pid)
            proc.terminate()  # Пытаемся завершить мягко
            # Если не завершился за 3 секунды, убиваем принудительно
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
            print("[OK] Explorer завершен")
        else:
            print("[!] Explorer не найден")
    except Exception as e:
        print(f"[!] Ошибка при завершении Explorer: {e}")

def start_explorer():
    """Запускает explorer.exe"""
    try:
        if find_process_id('explorer.exe') is None:
            explorer_path = os.path.join(os.environ['WINDIR'], 'explorer.exe')
            if os.path.exists(explorer_path):
                subprocess.Popen(explorer_path)
                print("[OK] Explorer запущен")
            else:
                print("[!] Не удалось найти explorer.exe")
        else:
            print("[!] Explorer уже запущен")
    except Exception as e:
        print(f"[!] Ошибка при запуске Explorer: {e}")

def on_press(key):
    """Обработчик нажатий клавиш"""
    try:
        if key == keyboard.Key.page_up:
            kill_explorer()
        elif key == keyboard.Key.page_down:
            start_explorer()
        elif key == keyboard.Key.esc:
            print("\n[!] Выход из программы")
            return False  # Останавливает слушатель
    except Exception as e:
        print(f"[!] Ошибка: {e}")

def main():
    print("Explorer Switcher (Python версия)")
    print("PG UP - закрыть, PG DOWN - открыть, ESC - выход\n")
    
    # Проверяем наличие psutil
    try:
        import psutil
    except ImportError:
        print("[!] Ошибка: Не установлен модуль psutil")
        print("Установите его командой: pip install psutil")
        input("Нажмите Enter для выхода...")
        return
    
    # Проверяем наличие pynput
    try:
        from pynput import keyboard
    except ImportError:
        print("[!] Ошибка: Не установлен модуль pynput")
        print("Установите его командой: pip install pynput")
        input("Нажмите Enter для выхода...")
        return
    
    # Запускаем слушатель клавиатуры
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()