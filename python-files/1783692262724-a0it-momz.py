# memz_light.pyw — безопасная имитация MeMz, только визуальный троллинг
# Запускать через pythonw.exe (без окна консоли) или переименовать в .pyw

import random
import time
import threading
import ctypes
import os
import sys
from ctypes import wintypes

# ===== pywin32 импорты =====
try:
    import win32api
    import win32con
    import win32gui
    import win32ui
    import pywintypes
except ImportError:
    # Если нет pywin32, выдаём ошибку и инструкцию
    print("[!] Установи pywin32: pip install pywin32")
    sys.exit(1)

# ===== Скрываем консоль (если запущено через python.exe) =====
ctypes.windll.kernel32.FreeConsole()

# ===== Вспомогательные функции для эффектов =====

def set_wallpaper_color(rgb_tuple):
    """Установить обои сплошным цветом (безопасно)"""
    try:
        import ctypes
        SPI_SETDESKWALLPAPER = 20
        # Создаём BMP 1x1 нужного цвета в памяти
        from PIL import Image
        import io
        img = Image.new('RGB', (1, 1), color=rgb_tuple)
        with io.BytesIO() as output:
            img.save(output, format='BMP')
            data = output.getvalue()
        # Записываем во временный файл
        temp_path = os.path.join(os.environ['TEMP'], 'wall.bmp')
        with open(temp_path, 'wb') as f:
            f.write(data)
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, temp_path, 3)
    except:
        pass

def open_notepad_with_text(text):
    """Открыть блокнот с текстом"""
    try:
        import subprocess
        # Создаём временный .txt
        temp_txt = os.path.join(os.environ['TEMP'], 'memz_msg.txt')
        with open(temp_txt, 'w', encoding='utf-8') as f:
            f.write(text)
        subprocess.Popen(['notepad.exe', temp_txt], shell=True)
    except:
        pass

def message_box_loop(count=3):
    """Показать несколько MessageBox с юморным текстом"""
    messages = [
        "Твой комп теперь мой, лошок!",
        "MeMz Lite приветствует тебя!",
        "Эффекты будут повторяться каждые 15 минут",
        "Ничего опасного, просто троллинг",
        "Наслаждайся представлением, сука!"
    ]
    for _ in range(count):
        msg = random.choice(messages)
        ctypes.windll.user32.MessageBoxW(0, msg, "NetErrror", 0x40 | 0x0)  # MB_ICONINFORMATION
        time.sleep(0.5)

def move_mouse_randomly(duration=30):
    """Дёргать мышь случайным образом в течение duration секунд"""
    start = time.time()
    while time.time() - start < duration:
        x = random.randint(0, 1920)
        y = random.randint(0, 1080)
        win32api.SetCursorPos((x, y))
        time.sleep(random.uniform(0.05, 0.3))

def invert_screen():
    """Инвертировать цвета экрана (через SetDisplayConfig или через Magnification API) — упрощённо через инверсию рабочего стола"""
    # Используем SPI_SETDESKWALLPAPER, но можно через инверсию GDI — проще через цветовой фильтр Windows (не везде)
    # Вместо инверсии сделаем мерцание через смену обоев
    pass

def flash_windows():
    """Найти все окна и заставить их мигать (FlashWindowEx)"""
    def enum_callback(hwnd, lparam):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            # Мигаем
            win32gui.FlashWindow(hwnd, True)
            time.sleep(0.01)
        return True
    win32gui.EnumWindows(enum_callback, None)

def open_many_windows():
    """Открыть 5-10 окон блокнота с разным текстом"""
    for i in range(random.randint(5, 10)):
        threading.Thread(target=open_notepad_with_text, args=(f"MeMz Light - окно #{i+1}",)).start()
        time.sleep(0.2)

def random_sound():
    """Воспроизвести случайный системный звук (безопасно)"""
    import winsound
    sounds = [win32con.MB_ICONASTERISK, win32con.MB_ICONEXCLAMATION, win32con.MB_ICONHAND, win32con.MB_ICONQUESTION]
    winsound.MessageBeep(random.choice(sounds))

# ===== Основной набор эффектов (выполняется 30 секунд) =====
def run_effects():
    print("[*] Эффекты запущены")  # будет видно, если запущено с консолью, но мы скрыли
    # Засекаем время
    start_time = time.time()
    # Список эффектов, которые будут выполняться параллельно
    threads = []
    
    # Эффект 1: открыть много окон
    t1 = threading.Thread(target=open_many_windows)
    threads.append(t1)
    t1.start()
    
    # Эффект 2: дёргать мышь (в отдельном потоке)
    t2 = threading.Thread(target=move_mouse_randomly, args=(30,))
    threads.append(t2)
    t2.start()
    
    # Эффект 3: показать MessageBox (несколько)
    t3 = threading.Thread(target=message_box_loop, args=(2,))
    threads.append(t3)
    t3.start()
    
    # Эффект 4: мигать окнами (в отдельном потоке)
    t4 = threading.Thread(target=flash_windows)
    threads.append(t4)
    t4.start()
    
    # Эффект 5: менять обои каждые 3 секунды на случайный цвет
    def wallpaper_changer():
        colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255), (0,0,0), (255,255,255)]
        end = time.time() + 30
        while time.time() < end:
            set_wallpaper_color(random.choice(colors))
            time.sleep(3)
    t5 = threading.Thread(target=wallpaper_changer)
    threads.append(t5)
    t5.start()
    
    # Эффект 6: случайные звуки
    def beep_loop():
        end = time.time() + 30
        while time.time() < end:
            random_sound()
            time.sleep(random.uniform(1, 3))
    t6 = threading.Thread(target=beep_loop)
    threads.append(t6)
    t6.start()
    
    # Ждём 30 секунд
    time.sleep(30)
    # (можно прервать потоки, но проще дать им завершиться самим, поскольку они имеют свои таймауты)
    # Дожидаемся завершения (или прерываем)
    for t in threads:
        try:
            t.join(timeout=0.5)
        except:
            pass
    # Восстанавливаем обои (на случайный цвет)
    set_wallpaper_color((0, 0, 0))  # чёрный, но можно сохранить старые

# ===== Главный цикл =====
def main():
    print("[MeMz Light] Запущен, жди эффектов...")
    while True:
        # Пауза перед эффектами: 5-15 сек
        delay = random.randint(5, 15)
        print(f"[*] Ожидание {delay} сек...")
        time.sleep(delay)
        
        # Эффекты 30 сек
        run_effects()
        
        # Пауза 15 минут
        print("[*] Эффекты завершены. Следующий цикл через 15 минут.")
        time.sleep(15 * 60)  # 900 секунд

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Для завершения по Ctrl+C (если запущено в консоли)
        sys.exit(0)
    except Exception as e:
        # Логируем ошибки (можно в файл)
        with open(os.path.join(os.environ['TEMP'], 'memz_light_error.txt'), 'a') as f:
            f.write(f"{time.ctime()}: {e}\n")