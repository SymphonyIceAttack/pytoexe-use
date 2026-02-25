# -*- coding: utf-8 -*-
import os
import shutil
import sys

def organize_files():
    """Организует файлы .sxf и .xml по папкам на основе их имени"""
    
    # Определяем папку для обработки
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
    else:
        target_folder = os.getcwd()
    
    # Очищаем экран (для Windows)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 60)
    print("           ОРГАНИЗАЦИЯ ФАЙЛОВ SXF И XML")
    print("=" * 60)
    print("📁 Папка: " + target_folder)
    print("")
    
    # Проверяем существование папки
    if not os.path.exists(target_folder):
        print("❌ ОШИБКА: Папка не существует!")
        print("   " + target_folder)
        raw_input("\nНажмите Enter для выхода...")
        return
    
    # Получаем список файлов
    try:
        files = os.listdir(target_folder)
    except Exception as e:
        print("❌ ОШИБКА: Не удается прочитать папку - " + str(e))
        raw_input("\nНажмите Enter для выхода...")
        return
    
    # Счетчики
    total_files = 0
    moved_files = 0
    created_folders = 0
    skipped_files = 0
    errors = 0
    
    # Список обработанных папок
    created_folders_list = []
    
    print("📊 Найдено файлов: " + str(len(files)))
    print("-" * 60)
    
    # Обрабатываем каждый файл
    for filename in sorted(files):
        file_path = os.path.join(target_folder, filename)
        
        # Пропускаем папки
        if os.path.isdir(file_path):
            continue
        
        # Проверяем расширение
        if not (filename.lower().endswith('.sxf') or filename.lower().endswith('.xml')):
            continue
        
        total_files += 1
        
        # Получаем имя без расширения
        name_without_ext = os.path.splitext(filename)[0]
        
        # Убираем подчёркивание в конце, если оно есть
        if name_without_ext.endswith('_'):
            folder_name = name_without_ext[:-1]
            had_underscore = True
        else:
            folder_name = name_without_ext
            had_underscore = False
        
        # Проверяем, что имя папки не пустое
        if not folder_name:
            print("  ⚠️  Пропущен: " + filename + " (пустое имя папки)")
            skipped_files += 1
            continue
        
        # Создаём папку, если её нет
        folder_path = os.path.join(target_folder, folder_name)
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                created_folders += 1
                created_folders_list.append(folder_name)
                print("  📁 Создана папка: " + folder_name)
            except Exception as e:
                print("  ❌ Ошибка создания папки " + folder_name + ": " + str(e))
                errors += 1
                continue
        
        # Перемещаем файл
        new_path = os.path.join(folder_path, filename)
        try:
            # Проверяем, не существует ли уже файл
            if os.path.exists(new_path):
                # Добавляем суффикс к имени
                base, ext = os.path.splitext(filename)
                new_filename = base + "_copy" + ext
                new_path = os.path.join(folder_path, new_filename)
                print("  ⚠️  Файл уже существует, сохраняю как: " + new_filename)
            
            shutil.move(file_path, new_path)
            moved_files += 1
            
            # Красивое отображение результата
            if had_underscore:
                print("  ✅ " + filename + " -> " + folder_name + "/ (подчёркивание убрано)")
            else:
                print("  ✅ " + filename + " -> " + folder_name + "/")
                
        except Exception as e:
            errors += 1
            print("  ❌ Ошибка при перемещении " + filename + ": " + str(e))
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("                     ГОТОВО!")
    print("=" * 60)
    
    if total_files == 0:
        print("❌ Нет файлов .sxf или .xml для обработки!")
    else:
        print("📊 Статистика:")
        print("   📁 Всего обработано файлов: " + str(total_files))
        print("   📦 Перемещено файлов: " + str(moved_files))
        print("   📂 Создано новых папок: " + str(created_folders))
        print("   ⏭️  Пропущено файлов: " + str(skipped_files))
        print("   ❌ Ошибок: " + str(errors))
    
    print("\n" + "=" * 60)
    
    # Список созданных папок
    if created_folders_list:
        print("\n📂 Созданные папки:")
        for folder in created_folders_list[:10]:
            print("   • " + folder)
        if len(created_folders_list) > 10:
            print("   • ... и ещё " + str(len(created_folders_list) - 10) + " папок")
    
    print("\n✅ Работа завершена!")
    
    # Для Python 2 используем raw_input, для Python 3 - input
    try:
        input("Нажмите Enter для выхода...")
    except:
        raw_input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    # Проверка аргументов командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Использование:")
        print("  python organize_files.py            - обработать текущую папку")
        print("  python organize_files.py C:\\папка   - обработать указанную папку")
        print("  python organize_files.py --help     - показать справку")
    else:
        organize_files()# -*- coding: utf-8 -*-
import os
import shutil
import sys

def organize_files():
    """Организует файлы .sxf и .xml по папкам на основе их имени"""
    
    # Определяем папку для обработки
    if len(sys.argv) > 1:
        target_folder = sys.argv[1]
    else:
        target_folder = os.getcwd()
    
    # Очищаем экран (для Windows)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 60)
    print("           ОРГАНИЗАЦИЯ ФАЙЛОВ SXF И XML")
    print("=" * 60)
    print("📁 Папка: " + target_folder)
    print("")
    
    # Проверяем существование папки
    if not os.path.exists(target_folder):
        print("❌ ОШИБКА: Папка не существует!")
        print("   " + target_folder)
        raw_input("\nНажмите Enter для выхода...")
        return
    
    # Получаем список файлов
    try:
        files = os.listdir(target_folder)
    except Exception as e:
        print("❌ ОШИБКА: Не удается прочитать папку - " + str(e))
        raw_input("\nНажмите Enter для выхода...")
        return
    
    # Счетчики
    total_files = 0
    moved_files = 0
    created_folders = 0
    skipped_files = 0
    errors = 0
    
    # Список обработанных папок
    created_folders_list = []
    
    print("📊 Найдено файлов: " + str(len(files)))
    print("-" * 60)
    
    # Обрабатываем каждый файл
    for filename in sorted(files):
        file_path = os.path.join(target_folder, filename)
        
        # Пропускаем папки
        if os.path.isdir(file_path):
            continue
        
        # Проверяем расширение
        if not (filename.lower().endswith('.sxf') or filename.lower().endswith('.xml')):
            continue
        
        total_files += 1
        
        # Получаем имя без расширения
        name_without_ext = os.path.splitext(filename)[0]
        
        # Убираем подчёркивание в конце, если оно есть
        if name_without_ext.endswith('_'):
            folder_name = name_without_ext[:-1]
            had_underscore = True
        else:
            folder_name = name_without_ext
            had_underscore = False
        
        # Проверяем, что имя папки не пустое
        if not folder_name:
            print("  ⚠️  Пропущен: " + filename + " (пустое имя папки)")
            skipped_files += 1
            continue
        
        # Создаём папку, если её нет
        folder_path = os.path.join(target_folder, folder_name)
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                created_folders += 1
                created_folders_list.append(folder_name)
                print("  📁 Создана папка: " + folder_name)
            except Exception as e:
                print("  ❌ Ошибка создания папки " + folder_name + ": " + str(e))
                errors += 1
                continue
        
        # Перемещаем файл
        new_path = os.path.join(folder_path, filename)
        try:
            # Проверяем, не существует ли уже файл
            if os.path.exists(new_path):
                # Добавляем суффикс к имени
                base, ext = os.path.splitext(filename)
                new_filename = base + "_copy" + ext
                new_path = os.path.join(folder_path, new_filename)
                print("  ⚠️  Файл уже существует, сохраняю как: " + new_filename)
            
            shutil.move(file_path, new_path)
            moved_files += 1
            
            # Красивое отображение результата
            if had_underscore:
                print("  ✅ " + filename + " -> " + folder_name + "/ (подчёркивание убрано)")
            else:
                print("  ✅ " + filename + " -> " + folder_name + "/")
                
        except Exception as e:
            errors += 1
            print("  ❌ Ошибка при перемещении " + filename + ": " + str(e))
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("                     ГОТОВО!")
    print("=" * 60)
    
    if total_files == 0:
        print("❌ Нет файлов .sxf или .xml для обработки!")
    else:
        print("📊 Статистика:")
        print("   📁 Всего обработано файлов: " + str(total_files))
        print("   📦 Перемещено файлов: " + str(moved_files))
        print("   📂 Создано новых папок: " + str(created_folders))
        print("   ⏭️  Пропущено файлов: " + str(skipped_files))
        print("   ❌ Ошибок: " + str(errors))
    
    print("\n" + "=" * 60)
    
    # Список созданных папок
    if created_folders_list:
        print("\n📂 Созданные папки:")
        for folder in created_folders_list[:10]:
            print("   • " + folder)
        if len(created_folders_list) > 10:
            print("   • ... и ещё " + str(len(created_folders_list) - 10) + " папок")
    
    print("\n✅ Работа завершена!")
    
    # Для Python 2 используем raw_input, для Python 3 - input
    try:
        input("Нажмите Enter для выхода...")
    except:
        raw_input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    # Проверка аргументов командной строки
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Использование:")
        print("  python organize_files.py            - обработать текущую папку")
        print("  python organize_files.py C:\\папка   - обработать указанную папку")
        print("  python organize_fpip install pyinstalleriles.py --help     - показать справку")
    else:
        organize_files()