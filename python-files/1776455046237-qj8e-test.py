import os
import shutil
import time
from datetime import datetime, timedelta
import hashlib
import platform

# ============================================
#     ОНЕВАЛЬВ - ОЧИСТКА СИСТЕМЫ
#     ONEVALVE.RU - Ваш системный помощник
#          ПОЛНАЯ ВЕРСИЯ
# ============================================

def show_header():
    """Красивое отображение шапки сайта"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 70)
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║     ██████╗ ███╗   ██╗███████╗██╗   ██╗ █████╗ ██╗     ██╗   ██╗███████╗║
    ║    ██╔═══██╗████╗  ██║██╔════╝██║   ██║██╔══██╗██║     ██║   ██║██╔════╝║
    ║    ██║   ██║██╔██╗ ██║█████╗  ██║   ██║███████║██║     ██║   ██║█████╗  ║
    ║    ██║   ██║██║╚██╗██║██╔══╝  ╚██╗ ██╔╝██╔══██║██║     ██║   ██║██╔══╝  ║
    ║    ╚██████╔╝██║ ╚████║███████╗ ╚████╔╝ ██║  ██║███████╗╚██████╔╝███████╗║
    ║     ╚═════╝ ╚═╝  ╚═══╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝║
    ║                                                                      ║
    ║              ⭐⭐⭐ СИСТЕМНЫЙ ОЧИСТИТЕЛЬ ПРО ⭐⭐⭐                     ║
    ║                                                                      ║
    ║                      🚀 WWW.ONEVALVE.RU 🚀                           ║
    ║                    Ваш надёжный цифровой помощник                     ║
    ║                      Профессиональная версия                          ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    print("=" * 70)
    print(f"  📅 Дата и время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"  💻 Операционная система: {platform.system()} {platform.release()}")
    print(f"  👤 Пользователь: {os.getlogin()}")
    print("=" * 70)

def show_menu():
    """Главное меню программы"""
    print("\n" + " " * 25 + "🔧 ГЛАВНОЕ МЕНЮ 🔧")
    print("-" * 70)
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║   📋 ОСНОВНЫЕ ФУНКЦИИ:                                              ║
    ║                                                                      ║
    ║      1. 🗑️  ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ                                ║
    ║      2. 📁  ОЧИСТКА ПАПКИ ЗАГРУЗКИ                                  ║
    ║      3. 🔄  УДАЛЕНИЕ ДУБЛИКАТОВ ФАЙЛОВ                              ║
    ║      4. 📊  ОЧИСТКА СТАРЫХ ФАЙЛОВ (по дням)                         ║
    ║      5. 🧹  ПОЛНАЯ ОЧИСТКА СИСТЕМЫ                                  ║
    ║      6. 🗑️  ОЧИСТКА КОРЗИНЫ                                         ║
    ║      7. 🌐  ОЧИСТКА КЭША БРАУЗЕРОВ                                  ║
    ║                                                                      ║
    ║   📊 ИНФОРМАЦИЯ:                                                    ║
    ║                                                                      ║
    ║      8. 📈  ПОКАЗАТЬ СТАТИСТИКУ ДИСКА                                ║
    ║      9. ℹ️  О ПРОГРАММЕ                                             ║
    ║      0. 🚪  ВЫХОД                                                    ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    print("-" * 70)

def get_size(path):
    """Получение размера папки или файла"""
    total = 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_size(entry.path)
    except:
        pass
    return total

def format_size(size):
    """Форматирование размера в читаемый вид"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} ТБ"

def clean_temp_files():
    """Очистка временных файлов"""
    print("\n" + "=" * 70)
    print("🗑️  ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ")
    print("=" * 70)
    
    temp_folders = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.path.expanduser('~\\AppData\\Local\\Temp'),
        'C:\\Windows\\Temp',
        os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\INetCache')
    ]
    
    extensions = ['.tmp', '.log', '.cache', '.temp', '.old', '.bak', '.gid', '.chk']
    deleted_count = 0
    deleted_size = 0
    
    for folder in temp_folders:
        if folder and os.path.exists(folder):
            print(f"\n📂 Сканирую: {folder}")
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        try:
                            file_path = os.path.join(root, file)
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            deleted_size += file_size
                            print(f"   ✅ Удалён: {file} ({format_size(file_size)})")
                        except:
                            pass
    
    print(f"\n{'='*70}")
    print(f"📊 РЕЗУЛЬТАТЫ ОЧИСТКИ:")
    print(f"   ✅ Удалено файлов: {deleted_count}")
    print(f"   💾 Освобождено места: {format_size(deleted_size)}")
    print("=" * 70)
    input("\n🔘 Нажмите Enter для продолжения...")

def clean_downloads():
    """Очистка папки загрузок"""
    print("\n" + "=" * 70)
    print("📁 ОЧИСТКА ПАПКИ ЗАГРУЗКИ")
    print("=" * 70)
    
    downloads = os.path.expanduser('~\\Downloads')
    extensions_to_delete = ['.exe', '.msi', '.tmp', '.crdownload', '.part', '.download']
    
    if os.path.exists(downloads):
        total_size = 0
        deleted = 0
        
        print(f"\n📂 Папка: {downloads}")
        
        for file in os.listdir(downloads):
            if any(file.lower().endswith(ext) for ext in extensions_to_delete):
                try:
                    file_path = os.path.join(downloads, file)
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted += 1
                    total_size += file_size
                    print(f"   ✅ Удалён: {file} ({format_size(file_size)})")
                except:
                    print(f"   ⚠️ Не удалось удалить: {file}")
        
        print(f"\n{'='*70}")
        print(f"📊 РЕЗУЛЬТАТЫ ОЧИСТКИ:")
        print(f"   ✅ Удалено файлов: {deleted}")
        print(f"   💾 Освобождено места: {format_size(total_size)}")
    else:
        print("\n❌ Папка загрузок не найдена!")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def clean_duplicates():
    """Удаление дубликатов файлов"""
    print("\n" + "=" * 70)
    print("🔄 ПОИСК И УДАЛЕНИЕ ДУБЛИКАТОВ")
    print("=" * 70)
    
    folder = input("\n📂 Введите путь к папке (Enter для рабочего стола): ")
    if not folder:
        folder = os.path.expanduser('~\\Desktop')
    
    if os.path.exists(folder):
        print(f"\n🔍 Поиск дубликатов в: {folder}")
        print("⏳ Это может занять некоторое время...")
        
        hashes = {}
        duplicates = []
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash in hashes:
                        duplicates.append((file_path, hashes[file_hash]))
                        print(f"   🔄 Найден дубликат: {file}")
                    else:
                        hashes[file_hash] = file_path
                except:
                    pass
        
        if duplicates:
            print(f"\n📊 Найдено дубликатов: {len(duplicates)}")
            delete = input("\n❓ Удалить дубликаты? (y/n): ")
            
            if delete.lower() == 'y':
                deleted = 0
                for dup, original in duplicates:
                    try:
                        os.remove(dup)
                        deleted += 1
                        print(f"   ✅ Удалён дубликат: {os.path.basename(dup)}")
                    except:
                        print(f"   ⚠️ Не удалось удалить: {os.path.basename(dup)}")
                
                print(f"\n✅ Удалено дубликатов: {deleted}")
            else:
                print("\n❌ Удаление отменено")
        else:
            print("\n✅ Дубликатов не найдено!")
    else:
        print("\n❌ Папка не найдена!")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def clean_old_files():
    """Очистка старых файлов"""
    print("\n" + "=" * 70)
    print("📊 ОЧИСТКА СТАРЫХ ФАЙЛОВ")
    print("=" * 70)
    
    try:
        days = int(input("\n📅 Удалять файлы старше (дней): "))
        folder = input("📂 Путь к папке (Enter для Downloads): ")
        
        if not folder:
            folder = os.path.expanduser('~\\Downloads')
        
        if os.path.exists(folder):
            now = time.time()
            deleted = 0
            total_size = 0
            
            print(f"\n🔍 Поиск файлов старше {days} дней...")
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_time = os.path.getmtime(file_path)
                        file_age = (now - file_time) / (24 * 3600)
                        
                        if file_age > days:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted += 1
                            total_size += file_size
                            print(f"   ✅ Удалён: {file} ({format_size(file_size)}, {file_age:.1f} дней)")
                    except:
                        pass
            
            print(f"\n{'='*70}")
            print(f"📊 РЕЗУЛЬТАТЫ ОЧИСТКИ:")
            print(f"   ✅ Удалено файлов: {deleted}")
            print(f"   💾 Освобождено места: {format_size(total_size)}")
        else:
            print("\n❌ Папка не найдена!")
    except ValueError:
        print("\n❌ Ошибка: Введите корректное число!")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def full_clean():
    """Полная очистка системы"""
    print("\n" + "=" * 70)
    print("🧹 ПОЛНАЯ ОЧИСТКА СИСТЕМЫ")
    print("=" * 70)
    
    print("\n⚠️  ВНИМАНИЕ! Будет выполнена полная очистка системы!")
    print("   - Временные файлы")
    print("   - Папка загрузки (установщики)")
    print("   - Корзина")
    print("   - Кэш браузеров")
    
    confirm = input("\n❓ Продолжить? (y/n): ")
    
    if confirm.lower() == 'y':
        print("\n🚀 Начинаю полную очистку...\n")
        clean_temp_files()
        clean_downloads()
        clean_recycle_bin()
        clean_browser_cache()
        print("\n✅ ПОЛНАЯ ОЧИСТКА ЗАВЕРШЕНА!")
    else:
        print("\n❌ Очистка отменена")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def clean_recycle_bin():
    """Очистка корзины"""
    print("\n" + "=" * 70)
    print("🗑️  ОЧИСТКА КОРЗИНЫ")
    print("=" * 70)
    
    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
        print("\n✅ Корзина успешно очищена!")
    except:
        print("\n❌ Не удалось очистить корзину!")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def clean_browser_cache():
    """Очистка кэша браузеров"""
    print("\n" + "=" * 70)
    print("🌐 ОЧИСТКА КЭША БРАУЗЕРОВ")
    print("=" * 70)
    
    browsers = {
        "Google Chrome": os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'),
        "Mozilla Firefox": os.path.expanduser('~\\AppData\\Local\\Mozilla\\Firefox\\Profiles'),
        "Microsoft Edge": os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache'),
        "Opera": os.path.expanduser('~\\AppData\\Local\\Opera Software\\Opera Stable\\Cache')
    }
    
    for browser, path in browsers.items():
        if os.path.exists(path):
            try:
                size_before = get_size(path)
                shutil.rmtree(path, ignore_errors=True)
                print(f"   ✅ Кэш {browser} очищен ({format_size(size_before)})")
            except:
                print(f"   ⚠️ Не удалось очистить кэш {browser}")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def show_disk_stats():
    """Показать статистику диска"""
    print("\n" + "=" * 70)
    print("📈 СТАТИСТИКА ДИСКА")
    print("=" * 70)
    
    try:
        import shutil
        
        print("\n📊 ИНФОРМАЦИЯ О ДИСКАХ:\n")
        
        for drive in range(65, 91):  # A: до Z:
            drive_letter = chr(drive) + ":\\"
            if os.path.exists(drive_letter):
                try:
                    total, used, free = shutil.disk_usage(drive_letter)
                    used_percent = (used / total) * 100
                    
                    print(f"💾 Диск {drive_letter}")
                    print(f"   📦 Всего: {format_size(total)}")
                    print(f"   📁 Занято: {format_size(used)} ({used_percent:.1f}%)")
                    print(f"   🆓 Свободно: {format_size(free)}")
                    
                    # График заполнения
                    bar_length = 50
                    filled = int(bar_length * used_percent / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    print(f"   [{bar}] {used_percent:.1f}%")
                    print()
                except:
                    pass
    except:
        print("❌ Не удалось получить информацию о дисках!")
    
    input("\n🔘 Нажмите Enter для продолжения...")

def show_about():
    """Информация о программе"""
    print("\n" + "=" * 70)
    print("ℹ️  О ПРОГРАММЕ")
    print("=" * 70)
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   📱 ПРОГРАММА: Системный Очиститель ONEVALVE              ║
    ║   🚀 ВЕРСИЯ: 2.0 Профессиональная                           ║
    ║   🌐 САЙТ: WWW.ONEVALVE.RU                                  ║
    ║   📧 EMAIL: support@onevalve.ru                             ║
    ║   📅 ДАТА ВЫПУСКА: 2024                                     ║
    ║                                                              ║
    ║   ⚡ ОСОБЕННОСТИ:                                           ║
    ║   • Полная очистка временных файлов                         ║
    ║   • Удаление дубликатов                                     ║
    ║   • Очистка кэша браузеров                                  ║
    ║   • Мониторинг дискового пространства                       ║
    ║   • Интуитивно понятный интерфейс                           ║
    ║                                                              ║
    ║   ⭐ ONEVALVE.RU - Ваш надёжный цифровой помощник!          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    input("\n🔘 Нажмите Enter для продолжения...")

# ============================================
#              ГЛАВНАЯ ПРОГРАММА
# ============================================

def main():
    """Основная функция программы"""
    while True:
        show_header()
        show_menu()
        
        choice = input("\n🔽 ВЫБЕРИТЕ ПУНКТ МЕНЮ (0-9): ")
        
        if choice == '1':
            clean_temp_files()
        elif choice == '2':
            clean_downloads()
        elif choice == '3':
            clean_duplicates()
        elif choice == '4':
            clean_old_files()
        elif choice == '5':
            full_clean()
        elif choice == '6':
            clean_recycle_bin()
        elif choice == '7':
            clean_browser_cache()
        elif choice == '8':
            show_disk_stats()
        elif choice == '9':
            show_about()
        elif choice == '0':
            print("\n" + "=" * 70)
            print("   Спасибо за использование ONEVALVE.RU!")
            print("   До новых встреч! 🚀")
            print("=" * 70)
            time.sleep(2)
            break
        else:
            print("\n❌ ОШИБКА: Неверный выбор! Попробуйте снова.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🚪 Программа прервана пользователем")
        print("Спасибо за использование ONEVALVE.RU!")
        time.sleep(1)
