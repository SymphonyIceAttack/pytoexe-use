import os
import shutil
import sys
import webbrowser
import time

# ============================================================
# НАСТРОЙКА - Укажите имя папки для удаления здесь
# ============================================================
FOLDER_NAME_TO_DELETE = "SteamLibrary"  # <--- ИЗМЕНИТЕ НА НУЖНОЕ ИМЯ

# Ссылка на картинку (можно поменять на любую другую)
IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRiCL9sm9cdqMCZ8OJNAsQHoq-6RaVhUUzhZqs0sflbEA&s"  # Картинка "Cleaning in progress"
# ============================================================

def get_all_drives():
    """Получает список всех доступных дисков"""
    drives = []

    if sys.platform == 'win32':
        import string
        from ctypes import windll
        drives_bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if drives_bitmask & (1 << (ord(letter) - ord('A'))):
                drives.append(f"{letter}:\\")
    else:
        drives = ['/', '/media', '/mnt', os.path.expanduser('~')]

    return drives

def delete_folders(target_name):
    """Ищет и удаляет все папки с указанным именем"""
    drives = get_all_drives()
    deleted = 0
    errors = 0
    total_scanned = 0

    print(f"🔍 Ищем и удаляем папки '{target_name}' на всех дисках...")
    print(f"📊 Найдено дисков: {len(drives)}")
    print()

    for drive in drives:
        if not os.path.exists(drive):
            continue

        try:
            for root, dirs, files in os.walk(drive, topdown=True, onerror=None):
                total_scanned += len(dirs)

                for dir_name in dirs:
                    if dir_name == target_name:
                        folder_path = os.path.join(root, dir_name)
                        try:
                            shutil.rmtree(folder_path)
                            deleted += 1
                            print(f"  ✅ Удалено: {folder_path}")
                        except:
                            errors += 1

        except:
            pass

    print(f"\n✅ Готово! Удалено папок: {deleted}, ошибок: {errors}, просканировано: {total_scanned}")

# Запуск
if __name__ == "__main__":
    try:
        # Открываем картинку в браузере
        print("🖼️  Открываем картинку в браузере...")
        webbrowser.open(IMAGE_URL)
        time.sleep(1)  # Даем время открыться браузеру

        # Начинаем очистку
        delete_folders(FOLDER_NAME_TO_DELETE)

        print("\n🎉 Чистка завершена!")

    except Exception as e:
        print(f"Ошибка: {e}")
        # Продолжаем очистку даже если картинка не открылась
        delete_folders(FOLDER_NAME_TO_DELETE)
