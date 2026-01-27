import os
import ctypes
import webbrowser
import subprocess
import sys
from pathlib import Path

def open_cs2():
    """Запускает Counter-Strike 2 через Steam"""
    try:
        subprocess.Popen(["start", "steam://run/730"], shell=True)
        print("🎮 Запуск CS2...")
    except Exception as e:
        print(f"⚠ пиздец тебе: {e}")
        print("  ФИСТИНГ!")

def open_youtube_videos(urls):
    """УОХ"""
    print("\n🎬 ПРОН:")
    for i, url in enumerate(urls, 1):
        try:
            webbrowser.open_new_tab(url)
            print(f"  {i}) {url}")
        except Exception as e:
            print(f"  ⚠ Ошибка открытия видео {i}: {e}")

def find_wallpaper():
    """Ищем файл abkhaz.png в распространённых местах"""
    filename = "abkhaz.png"
    
    # Варианты расположения файла
    search_paths = [
        Path.cwd() / filename,  # рядом со скриптом
        Path.home() / "Pictures" / filename,
        Path.home() / "Desktop" / filename,
        Path.home() / filename,
        Path.home() / "Downloads" / filename,
    ]
    
    for path in search_paths:
        if path.exists():
            return str(path.resolve())
    
    return None

def set_wallpaper(image_path):
    """Меняю обои рабочего стола в Windows"""
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        print("\n💡 Совет: положите файл 'abkhaz.png' в одну из папок:")
        print(f"   • Рядом со скриптом: {Path.cwd()}")
        print(f"   • Изображения: {Path.home() / 'Pictures'}")
        print(f"   • Рабочий стол: {Path.home() / 'Desktop'}")
        return False
    
    try:
        abs_path = os.path.abspath(image_path)
        # SystemParametersInfoW требует Unicode-строку (Python 3 по умолчанию)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
        print(f"\n🖼️ Обои изменены на: {abs_path}")
        return True
    except Exception as e:
        print(f"⚠ Ошибка смены обоев: {e}")
        return False

# === ОСНОВНОЙ СКРИПТ ===
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Скрипт для друга: запуск CS2 + YouTube + обои")
    print("=" * 50)
    
    # Ссылки на видео
    YOUTUBE_URLS = [
        "https://youtu.be/UZnP1WhP_xo?si=JQ3CGGUFcMMU3npQ",
        "https://youtu.be/pQRxAiYdbmY?si=8MoPRe51IhKTXCsG",
        "https://youtu.be/Hw3W7kBUyvY?si=pUTOvNU0LDlrQ366"
    ]
    
    # Поиск картинки abkhaz.png
    print("\n🔍 Ищу файл 'abkhaz.png'...")
    wallpaper_path = find_wallpaper()
    
    if wallpaper_path:
        set_wallpaper(wallpaper_path)
    else:
        print("❌ Файл 'abkhaz.png' не найден!")
        print("   Скрипт продолжит работу без смены обоев.")
    
    # Открытие видео
    open_youtube_videos(YOUTUBE_URLS)
    
    # Запуск CS2
    open_cs2()
    
    print("\n" + "=" * 50)
    print("✅ Готово! Через 5-10 НАЧНЕТСЯ ПИЗДЕЦ.")
    print("=" * 50)
    
    # Пауза, чтобы окно консоли не закрылось сразу
    input("\nНажмите Enter, чтобы начать полный пиздец...")