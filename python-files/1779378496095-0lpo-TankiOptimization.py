import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

def run_as_admin():
    """Запрашивает права администратора"""
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("🔐 Для работы скрипта нужны права администратора.")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except Exception as e:
        print(f"Ошибка при проверке прав: {e}")
        sys.exit(1)

def optimize_wot_preferences(preferences_path):
    """Непосредственно изменяет файл настроек WoT для максимальной производительности"""
    
    # Параметры, которые мы будем менять, и их минимальные значения
    # Основано на анализе рекомендаций с форумов и гайдов [citation:10]
    graphics_settings = {
        'graphicsQuality': '0',        # Минимальное качество
        'presetValues': '0',           # Пресет "Минимальный"
        'windowedWidth': '1280',       # Низкое разрешение для FPS
        'windowedHeight': '720',
        'fullscreenWidth': '1280',
        'fullscreenHeight': '720',
        'fullscreen': '1',             # Полный экран
        'windowed': '0',
        'borderless': '0',
        'vertSync': '0',               # Отключить верт. синхронизацию
        'tripleBuffering': '0',        # Отключить тройную буферизацию
        'antiAliasing': '0',           # Отключить сглаживание
        'postProcessing': '0',         # Отключить постобработку
        'shadowQuality': '0',          # Минимальные тени
        'textureQuality': '0',         # Минимальное качество текстур
        'lightingQuality': '0',        # Минимальное освещение
        'effectsQuality': '0',         # Минимальные эффекты
        'floraQuality': '0',           # Трава и растительность на минимум
        'waterQuality': '0',           # Минимальное качество воды
        'terrainQuality': '0',         # Минимальное качество ландшафта
        'decalsQuality': '0',          # Минимальное качество декалей
        'objectLOD': '0',              # Минимальная детализация объектов
        'speedTreeQuality': '0',       # Минимальное качество растительности (SpeedTree)
    }

    try:
        tree = ET.parse(preferences_path)
        root = tree.getroot()
        
        print(f"   📄 Изменяю настройки в файле: {preferences_path}")
        
        settings_modified = 0
        # Ищем все теги в XML и применяем наши настройки
        for elem in root.iter():
            tag = elem.tag
            if tag in graphics_settings:
                new_value = graphics_settings[tag]
                if elem.text != new_value:
                    print(f"      - {tag}: {elem.text} -> {new_value}")
                    elem.text = new_value
                    settings_modified += 1
        
        if settings_modified > 0:
            # Сохраняем изменения
            tree.write(preferences_path, encoding='utf-8', xml_declaration=True)
            print(f"   ✅ Успешно изменено {settings_modified} настроек.")
        else:
            print("   ℹ️  Настройки уже на минимальных значениях. Изменения не требуются.")
        return True

    except Exception as e:
        print(f"   ❌ Ошибка при изменении XML: {e}")
        return False

def main():
    run_as_admin()
    
    print("=" * 50)
    print("🎮 ОПТИМИЗАЦИЯ WORLD OF TANKS ДЛЯ СЛАБЫХ ПК")
    print("=" * 50)
    print()

    # Ищем стандартные пути установки игры
    possible_paths = [
        Path("C:/Games/World_of_Tanks"),
        Path("D:/Games/World_of_Tanks"),
        Path("E:/Games/World_of_Tanks"),
        Path("C:/Program Files/World_of_Tanks"),
        Path("C:/Program Files (x86)/World_of_Tanks"),
        Path(os.environ.get('APPDATA', '')) / "Wargaming.net/WorldOfTanks",
    ]
    
    wot_path = None
    for p in possible_paths:
        if p.exists():
            wot_path = p
            break

    if not wot_path:
        print("⚠️  Не удалось найти папку с игрой автоматически.")
        manual_path = input("Введи путь к папке с игрой вручную (например, D:\\Games\\World_of_Tanks): ")
        if manual_path and Path(manual_path).exists():
            wot_path = Path(manual_path)
        else:
            print("❌ Указанная папка не существует. Выход.")
            input("\nНажми Enter для выхода...")
            return

    print(f"✅ Найдена папка с игрой: {wot_path}")
    
    # Ищем файл настроек preferences.xml
    preferences_file = wot_path / "preferences.xml"
    if not preferences_file.exists():
        # Иногда он лежит в другом месте
        alt_pref_path = Path(os.environ.get('APPDATA', '')) / "Wargaming.net/WorldOfTanks/preferences.xml"
        if alt_pref_path.exists():
            preferences_file = alt_pref_path
            print(f"   Найден альтернативный файл настроек: {preferences_file}")
        else:
            print("❌ Файл preferences.xml не найден. Убедись, что игра хотя бы раз запускалась.")
            input("\nНажми Enter для выхода...")
            return
    
    # Создаем резервную копию файла настроек
    backup_file = str(preferences_file) + ".backup"
    try:
        shutil.copy2(preferences_file, backup_file)
        print(f"📋 Резервная копия настроек сохранена в: {backup_file}")
    except Exception as e:
        print(f"❌ Не удалось создать резервную копию: {e}")
        input("\nНажми Enter для выхода...")
        return
    
    # Оптимизируем настройки
    if optimize_wot_preferences(preferences_file):
        print("\n" + "=" * 50)
        print("💡 ДОПОЛНИТЕЛЬНЫЕ РЕКОМЕНДАЦИИ:")
        print("- Установи в лаунчере игры 'SD-клиент' вместо HD.") [citation:3]
        print("- Закрой все фоновые программы (браузер, Discord).")
        print("- В драйверах видеокарты выбери режим 'Производительность'.")
        print("- Если FPS всё ещё низкий — нужно обновить железо.") [citation:6]
        print("=" * 50)
        
        launch = input("\n🚀 Запустить игру прямо сейчас? (y/n): ").lower()
        if launch == 'y':
            # Пытаемся найти исполняемый файл игры
            exe_path = wot_path / "win64/worldoftanks.exe"
            if not exe_path.exists():
                exe_path = wot_path / "win32/worldoftanks.exe"
            if exe_path.exists():
                print(f"   Запускаю {exe_path}...")
                try:
                    subprocess.Popen([str(exe_path)])
                except Exception as e:
                    print(f"   Не удалось запустить игру: {e}")
            else:
                print("   Не удалось найти исполняемый файл игры. Запусти её вручную.")
    
    input("\nНажми Enter для выхода...")

if __name__ == "__main__":
    main()