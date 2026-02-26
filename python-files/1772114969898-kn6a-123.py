import os
import shutil
import ctypes
import subprocess
import sys
import tempfile
from datetime import datetime

# Для прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Цветной вывод
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(message, color=Colors.RESET):
    print(f"{color}{message}{Colors.RESET}")
    # Пишем в лог файл
    with open('cleaner_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")

def print_progress(current, total):
    """Прогресс бар"""
    percent = (current / total) * 100
    bar = '█' * int(percent // 4) + '░' * (25 - int(percent // 4))
    print(f"\r{Colors.CYAN}[{bar}] {percent:.0f}%{Colors.RESET}", end='')
    if current == total:
        print()

def clear_ram():
    """Очистка RAM через EmptyWorkingSet"""
    log("[1/6] Очистка оперативной памяти...", Colors.CYAN)
    try:
        kernel32 = ctypes.windll.kernel32
        process = kernel32.GetCurrentProcess()
        result = kernel32.SetProcessWorkingSetSize(process, ctypes.c_size_t(-1), ctypes.c_size_t(-1))
        if result:
            log("  ✓ RAM очищена", Colors.GREEN)
            return True
        else:
            log("  ✗ Ошибка при очистке RAM", Colors.RED)
            return False
    except Exception as e:
        log(f"  ✗ Ошибка: {e}", Colors.RED)
        return False

def clear_temp_folders():
    """Очистка временных папок"""
    log("[2/6] Очистка временных файлов...", Colors.CYAN)
    
    temp_paths = [
        tempfile.gettempdir(),
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        'C:\\Windows\\Temp',
        os.path.expandvars('%LOCALAPPDATA%\\Temp'),
        os.path.expandvars('%USERPROFILE%\\AppData\\Local\\Temp')
    ]
    
    deleted_count = 0
    error_count = 0
    total_files = 0
    
    # Подсчет файлов
    for temp_path in set(temp_paths):
        if not temp_path or not os.path.exists(temp_path):
            continue
        for root, dirs, files in os.walk(temp_path, topdown=False):
            total_files += len(files)
    
    if total_files == 0:
        log("  Нет файлов для очистки", Colors.BLUE)
        return True
    
    current_file = 0
    for temp_path in set(temp_paths):
        if not temp_path or not os.path.exists(temp_path):
            continue
            
        log(f"  Очистка: {temp_path}", Colors.BLUE)
        
        try:
            for root, dirs, files in os.walk(temp_path, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        deleted_count += 1
                    except:
                        error_count += 1
                    current_file += 1
                    print_progress(current_file, total_files)
                
                for dir in dirs:
                    try:
                        dir_path = os.path.join(root, dir)
                        shutil.rmtree(dir_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    print()
    log(f"  ✓ Удалено файлов: {deleted_count}, ошибок: {error_count}", Colors.GREEN)
    return True

def clear_icon_cache():
    """Очистка кэша иконок и thumbnails"""
    log("[3/6] Очистка кэша иконок...", Colors.CYAN)
    
    import glob
    import time
    
    explorer_path = os.path.expandvars('%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer')
    icon_paths = [
        os.path.expandvars('%LOCALAPPDATA%\\IconCache.db'),
        f'{explorer_path}\\iconcache*.db',
        f'{explorer_path}\\thumbcache*.db',
        os.path.expandvars('%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\Explorer\\*.db'),
        'C:\\Users\\All Users\\Microsoft\\Windows\\Explorer\\*.db'
    ]
    
    # Убиваем explorer
    try:
        subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], 
                     capture_output=True, text=True)
        log("  Explorer остановлен", Colors.BLUE)
        time.sleep(1.5)
    except:
        pass
    
    # Удаляем файлы кэша
    deleted = 0
    errors = 0
    
    for pattern in icon_paths:
        if '*' in pattern:
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                    deleted += 1
                    log(f"    Удален: {os.path.basename(file)}", Colors.BLUE)
                except:
                    errors += 1
        else:
            if os.path.exists(pattern):
                try:
                    os.remove(pattern)
                    deleted += 1
                    log(f"    Удален: {os.path.basename(pattern)}", Colors.BLUE)
                except:
                    errors += 1
    
    # Чистим кэш в реестре
    try:
        subprocess.run(['reg', 'delete', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\ThumbnailCache', '/f'],
                      capture_output=True, text=True)
        log("  Кэш реестра очищен", Colors.BLUE)
    except:
        pass
    
    log(f"  ✓ Удалено файлов: {deleted}, ошибок: {errors}", Colors.GREEN)
    
    # Запускаем explorer
    try:
        subprocess.Popen(['explorer.exe'])
        log("  Explorer запущен", Colors.BLUE)
    except:
        pass
    
    return True

def clear_prefetch():
    """Очистка Prefetch"""
    log("[4/6] Очистка Prefetch...", Colors.CYAN)
    
    if not is_admin():
        log("  ⚠ Требуются права администратора", Colors.YELLOW)
        return False
    
    prefetch_path = 'C:\\Windows\\Prefetch'
    if not os.path.exists(prefetch_path):
        log("  ✗ Папка Prefetch не найдена", Colors.RED)
        return False
    
    try:
        files = os.listdir(prefetch_path)
        if not files:
            log("  Папка уже пуста", Colors.BLUE)
            return True
            
        deleted = 0
        for file in files:
            if file.endswith('.pf') or file.endswith('.db'):
                try:
                    os.remove(os.path.join(prefetch_path, file))
                    deleted += 1
                except:
                    pass
        
        log(f"  ✓ Удалено файлов: {deleted}", Colors.GREEN)
        return True
    except Exception as e:
        log(f"  ✗ Ошибка: {e}", Colors.RED)
        return False

def clear_recycle_bin():
    """Очистка корзины"""
    log("[5/6] Очистка корзины...", Colors.CYAN)
    
    try:
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0001 | 0x0002)
        if result == 0:
            log("  ✓ Корзина очищена", Colors.GREEN)
            return True
        else:
            log("  ✗ Ошибка при очистке корзины", Colors.RED)
            return False
    except Exception as e:
        log(f"  ✗ Ошибка: {e}", Colors.RED)
        return False

def clear_recent_files():
    """Очистка недавних файлов"""
    log("[6/6] Очистка недавних файлов...", Colors.CYAN)
    
    recent_path = os.path.expandvars('%APPDATA%\\Microsoft\\Windows\\Recent')
    recent_path2 = os.path.expandvars('%APPDATA%\\Microsoft\\Windows\\Recent\\AutomaticDestinations')
    
    deleted = 0
    
    # Чистим Recent
    if os.path.exists(recent_path):
        try:
            for file in os.listdir(recent_path):
                try:
                    file_path = os.path.join(recent_path, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted += 1
                except:
                    pass
        except:
            pass
    
    # Чистим AutomaticDestinations
    if os.path.exists(recent_path2):
        try:
            for file in os.listdir(recent_path2):
                try:
                    file_path = os.path.join(recent_path2, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted += 1
                except:
                    pass
        except:
            pass
    
    log(f"  ✓ Удалено элементов: {deleted}", Colors.GREEN)
    return True

def show_menu():
    """Показывает меню и возвращает выбор"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔══════════════════════════════════════════╗")
    print("║       PYTHON SYSTEM CLEANER v2.1        ║")
    print("║         (без DNS кэша)                   ║")
    print("╚══════════════════════════════════════════╝")
    print(Colors.RESET)
    
    # Проверка прав
    if is_admin():
        log("✓ Запущено от администратора", Colors.GREEN)
    else:
        log("⚠ Запущено без прав администратора", Colors.YELLOW)
        log("  Prefetch не будет работать\n")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Что хотите почистить?{Colors.RESET}")
    print("1. RAM (оперативная память)")
    print("2. Temp папки (временные файлы)")
    print("3. Кэш иконок и thumbnails")
    print("4. Prefetch (требует админа)")
    print("5. Корзина")
    print("6. Недавние файлы")
    print("7. ВСЁ ПОДРЯД")
    print("0. Выход")
    
    try:
        choice = input(f"\n{Colors.YELLOW}Ваш выбор (0-7): {Colors.RESET}").strip()
        return choice
    except:
        return '0'

def main():
    """Главная функция"""
    # Очищаем лог файл при запуске
    with open('cleaner_log.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== SYSTEM CLEANER LOG [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ===\n")
        f.write("="*50 + "\n\n")
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            log("\nВыход...", Colors.MAGENTA)
            break
        
        print()  # Отступ
        
        if choice == '7':
            log("=== ЗАПУСК ПОЛНОЙ ОЧИСТКИ ===", Colors.BOLD + Colors.MAGENTA)
            clear_ram()
            print()
            clear_temp_folders()
            print()
            clear_icon_cache()
            print()
            clear_prefetch()
            print()
            clear_recycle_bin()
            print()
            clear_recent_files()
        elif choice == '1':
            clear_ram()
        elif choice == '2':
            clear_temp_folders()
        elif choice == '3':
            clear_icon_cache()
        elif choice == '4':
            clear_prefetch()
        elif choice == '5':
            clear_recycle_bin()
        elif choice == '6':
            clear_recent_files()
        else:
            log("Неверный выбор, сорян", Colors.RED)
        
        # Показываем итог
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ Операция завершена!{Colors.RESET}")
        print(f"{Colors.BLUE}📄 Лог сохранен в cleaner_log.txt{Colors.RESET}")
        
        # Показываем свободное место
        try:
            import psutil
            disk = psutil.disk_usage('C:')
            free_gb = disk.free / (1024**3)
            log(f"💾 Свободно на диске C: {free_gb:.2f} GB", Colors.CYAN)
        except:
            pass
        
        # Ждем нажатия клавиши для возврата в меню
        input(f"\n{Colors.CYAN}Нажми Enter, чтобы вернуться в меню...{Colors.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Программа прервана пользователем{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Ошибка: {e}{Colors.RESET}")
        input("Нажми Enter для выхода...")
