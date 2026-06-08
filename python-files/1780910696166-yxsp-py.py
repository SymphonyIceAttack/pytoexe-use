import pyautogui
import time
import random
import sys
import os
import json
import keyboard  # Модуль для отслеживания клавиш в фоне

# 🌈 RGB-БАННЕР
BANNER = """
╔═══╗╔══╗╔╗──╔╗╔══╗╔╗─╔╗───╔═══╗╔═══╗╔══╗
║╔═╗║║╔╗║║║──║║║╔╗║║╚═╝║───║╔═╗║║╔═╗║║╔╗║
║╚═╝║║║║║║╚╗╔╝║║╚╝║║╔╗─║───║╚═╝║║╚═╝║║║║║
║╔╗╔╝║║║║║╔╗╔╗║║╔╗║║║╚╗║───║╔══╝║╔╗╔╝║║║║
║║║║─║╚╝║║║╚╝║║║║║║║║─║║───║║───║║║║─║╚╝║
╚╝╚╝─╚══╝╚╝──╚╝╚╝╚╝╚╝─╚╝───╚╝───╚╝╚╝─╚══╝
"""

CONFIG_FILE = "camera_config.json"

# Настройки по умолчанию (используются только при самом первом запуске)
DEFAULT_CONFIG = {
    "cameras": {
        "1": [710, 290],
        "2": [1015, 290],
        "3": [708, 526],
        "4": [1020, 520]
    },
    "exit": [1242, 600]
}

pyautogui.PAUSE = 0.15          # Базовая задержка pyautogui
pyautogui.FAILSAFE = True       # Экстренная остановка: курсор в (0,0)

def load_config():
    """Загружает координаты из файла или возвращает стандартные"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            print("⚠️ Файл конфигурации поврежден, используются настройки по умолчанию.")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    """Сохраняет координаты в файл"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def print_rgb_banner(text):
    """Выводит текст с плавным переливающимся RGB градиентом"""
    lines = text.strip().split('\n')
    total_lines = len(lines)
    
    for i, line in enumerate(lines):
        hue = (i / total_lines) * 360
        c = 255
        x = c * (1 - abs((hue / 60) % 2 - 1))
        
        if 0 <= hue < 60: r, g, b = c, x, 0
        elif 60 <= hue < 120: r, g, b = x, c, 0
        elif 120 <= hue < 180: r, g, b = 0, c, x
        elif 180 <= hue < 240: r, g, b = 0, x, c
        elif 240 <= hue < 300: r, g, b = x, 0, c
        else: r, g, b = c, 0, x
        
        print(f"\033[38;2;{int(r)};{int(g)};{int(b)}m{line}\033[0m")

def loading_animation(duration=1.0):
    """Анимация загрузки с прогресс-баром"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    bar_width = 30
    start_time = time.time()
    idx = 0
    
    while True:
        elapsed = time.time() - start_time
        if elapsed >= duration:
            break
        
        progress = elapsed / duration
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        spinner = frames[idx % len(frames)]
        
        percent = int(progress * 100)
        sys.stdout.write(f"\r {spinner} [{bar}] {percent}%")
        sys.stdout.flush()
        
        idx += 1
        time.sleep(0.05)
    
    sys.stdout.write("\r" + " " * (bar_width + 15) + "\r")
    sys.stdout.flush()

def human_move_click(x, y, move_duration=None):
    """Плавное движение мыши + микро-смещение + анимация"""
    if move_duration is None:
        move_duration = random.uniform(0.7, 1.4)

    loading_animation(duration=0.8)

    offset_x = random.uniform(-3, 3)
    offset_y = random.uniform(-3, 3)
    target_x, target_y = x + offset_x, y + offset_y

    pyautogui.moveTo(target_x, target_y, duration=move_duration, tween=pyautogui.easeInOutQuad)
    time.sleep(random.uniform(0.2, 0.5))
    pyautogui.click()

def setup_coordinates():
    """Умный режим настройки: показывает текущие координаты и позволяет обновить только нужные"""
    print("\n" + "="*60)
    print(" 🛠️ РЕЖИМ НАСТРОЙКИ КООРДИНАТ")
    print("="*60)
    print("💡 Инструкция:")
    print("  1. Наведите курсор мыши на нужную точку на экране.")
    print("  2. Нажмите 'S', чтобы ОБНОВИТЬ координаты этой точки.")
    print("  3. Нажмите 'Пробел' (Space), чтобы ОСТАВИТЬ текущие координаты.")
    print("  4. Нажмите 'Esc', чтобы отменить настройку и выйти.")
    print("="*60)
    print("⚠️ ВАЖНО: Скрипт должен быть запущен от имени Администратора!")
    
    print("👉 Нажмите Enter, чтобы начать настройку...")
    input()
    
    # Даем 1 секунду, чтобы пользователь убрал палец с клавиши Enter
    time.sleep(1.0) 

    config = load_config()
    new_config = {"cameras": {}, "exit": config.get("exit", [0, 0])}

    def get_or_keep_coordinate(point_name, current_pos):
        print(f"\n📍 Наведите мышь на: {point_name}")
        print(f"   💾 Текущие координаты: {current_pos}")
        print("   [ 'S' = обновить | 'Пробел' = оставить | 'Esc' = отмена ]")
        
        while True:
            if keyboard.is_pressed('esc'):
                print("\n❌ Настройка отменена пользователем.")
                return None
            if keyboard.is_pressed('space'):
                print(f"   ⏭️ Пропущено, оставляем: {current_pos}")
                time.sleep(0.5)  # Защита от двойного срабатывания
                return current_pos
            if keyboard.is_pressed('s'):
                x, y = pyautogui.position()
                print(f"   ✅ Обновлено: ({x}, {y})")
                time.sleep(0.5)  # Защита от двойного срабатывания
                return [int(x), int(y)]
            time.sleep(0.1)

    # Настройка 4 камер
    for i in range(1, 5):
        current_cam_pos = config["cameras"].get(str(i), [0, 0])
        pos = get_or_keep_coordinate(f"Камера {i}", current_cam_pos)
        if pos is None:
            return  # Выход из функции при отмене
        new_config["cameras"][str(i)] = pos

    # Настройка выхода
    current_exit_pos = config.get("exit", [0, 0])
    exit_pos = get_or_keep_coordinate("Кнопка выхода из камер", current_exit_pos)
    if exit_pos is None:
        return

    # Сохранение нового конфига
    save_config(new_config)
    
    print("\n✨ Конфигурация успешно сохранена в файл 'camera_config.json'!")
    print("💡 При следующем запуске скрипт автоматически использует эти координаты.")
    input("👉 Нажмите Enter для возврата в главное меню...")

def run_automation():
    """Основной цикл работы скрипта"""
    # Автоматически загружаем последние сохраненные координаты
    config = load_config()
    cameras = {k: tuple(v) for k, v in config["cameras"].items()}
    exit_coords = tuple(config["exit"])

    print("\n🟢 Скрипт запущен. У вас 5 секунд, чтобы подготовить интерфейс.")
    print("💡 Для экстренной остановки резко отведите мышь в левый верхний угол (0,0)")
    print(f"📂 Используется конфигурация из: {CONFIG_FILE}")
    print("⏳ Запуск через 5 секунд...")
    time.sleep(5)

    cycle = 1
    try:
        while True:
            cam_id, coords = random.choice(list(cameras.items()))
            print(f"\n📹 Цикл #{cycle} | Открываю камеру {cam_id} ({coords[0]}, {coords[1]})")
            human_move_click(coords[0], coords[1])

            watch_time = random.uniform(30, 120)
            print(f"⏳ Просмотр камеры: {watch_time:.1f} сек...")
            time.sleep(watch_time)

            print(f"🔴 Выхожу с камеры...")
            human_move_click(exit_coords[0], exit_coords[1])

            pause_time = random.uniform(10, 60)
            print(f"☕ Ожидание перед следующей камерой: {pause_time:.1f} сек...")
            time.sleep(pause_time)

            cycle += 1
    except KeyboardInterrupt:
        print("\n\n✅ Скрипт остановлен вручную (Ctrl+C). Возврат в меню...")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")

def main_menu():
    """Главное меню с выбором"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_rgb_banner(BANNER)
        
        print("\n" + "="*48)
        print(" 1 🚀 Запустить скрипт (с текущими настройками)")
        print(" 2 🛠️ Настроить координаты (обновить при необходимости)")
        print(" 3 🚪 Выйти")
        print("="*48)
        
        choice = input("Выберите действие (1/2/3): ").strip()
        
        if choice == "1":
            run_automation()
        elif choice == "2":
            setup_coordinates()
        elif choice == "3":
            print("\n👋 Завершение работы...")
            sys.exit(0)
        else:
            print("❌ Неверный ввод. Введите 1, 2 или 3.")
            time.sleep(1.5)

if __name__ == "__main__":
    # Проверка наличия модуля keyboard при старте
    try:
        import keyboard
    except ImportError:
        print("❌ ОШИБКА: Не установлен модуль 'keyboard'.")
        print("💡 Установите его командой: pip install keyboard")
        print("⚠️ Не забудьте запустить скрипт от имени Администратора!")
        sys.exit(1)
        
    main_menu()