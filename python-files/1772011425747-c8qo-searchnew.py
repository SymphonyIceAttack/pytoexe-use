import mmap
import os
import time
import re
from datetime import datetime

def search_in_file(filename, query, max_results=None):
    """Ищет строки в одном файле, корректно обрабатывая спецсимволы"""
    try:
        results = []
        
        with open(filename, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                pattern = re.compile(re.escape(query.encode('utf-8')), re.IGNORECASE)
                
                pos = 0
                while True:
                    match = pattern.search(mm, pos)
                    if not match:
                        break
                    
                    line_start = mm.rfind(b'\n', 0, match.start()) + 1
                    line_end = mm.find(b'\n', match.end())
                    if line_end == -1:
                        line_end = mm.size()
                    
                    line = mm[line_start:line_end].decode('utf-8', errors='ignore')
                    results.append(line)
                    pos = line_end + 1
                    
                    if max_results is not None and len(results) >= max_results:
                        break
                    
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {str(e)}")
        return []
    
    return results

def save_results_to_file(results, query, folder_path, processed_files, max_results, selected_files=None):
    """Сохраняет все найденные результаты в файл с выбором имени и пути"""
    if not results:
        print("Нет результатов для сохранения.")
        return False
    
    try:
        default_name = f"search_results_{query[:20]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filename = input(f"Введите имя файла для сохранения [по умолчанию: {default_name}]: ").strip()
        if not filename:
            filename = default_name
        
        default_path = os.getcwd()
        path = input(f"Введите путь для сохранения [по умолчанию: {default_path}]: ").strip()
        if not path:
            path = default_path
        
        full_path = os.path.join(path, filename)
        os.makedirs(path, exist_ok=True)
        
        # Информация о выбранных файлах для сохранения
        files_info = f"Обработано файлов: {processed_files}"
        if selected_files:
            if selected_files == "all":
                files_info += " (все файлы)"
            else:
                files_info += f" (файлы #{', '.join(map(str, selected_files))})"
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"Результаты поиска '{query}' в папке '{folder_path}'\n")
            f.write(f"{files_info}\n")
            f.write(f"Ограничение на количество результатов: {max_results if max_results else 'нет'}\n")
            f.write(f"Всего найдено: {len(results)} совпадений\n")
            f.write(f"Дата поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            for i, line in enumerate(results, 1):
                f.write(f"{i}. {line.strip()}\n")
        
        print(f"\nВсе результаты сохранены в файл: {full_path}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении результатов: {str(e)}")
        return False

def get_all_files_from_folder(folder_path):
    """Получает список всех файлов в папке и подпапках с сортировкой"""
    all_files = []
    
    for root, dirs, files in os.walk(folder_path):
        for file in sorted(files):  # Сортируем файлы по алфавиту
            file_path = os.path.join(root, file)
            all_files.append(file_path)
    
    return sorted(all_files)  # Сортируем общий список

def display_files_list(files, page=1, items_per_page=20):
    """Отображает список файлов с нумерацией по страницам"""
    total_files = len(files)
    total_pages = (total_files + items_per_page - 1) // items_per_page
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_files)
    
    print(f"\n{'='*80}")
    print(f"СПИСОК ФАЙЛОВ (страница {page}/{total_pages})")
    print(f"{'='*80}")
    
    for i in range(start_idx, end_idx):
        file_path = files[i]
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        size_str = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/(1024*1024):.2f} MB"
        print(f"{i+1:4d}. {os.path.basename(file_path):50} [{size_str:>10}]")
    
    print(f"{'='*80}")
    print(f"Всего файлов: {total_files} | Страница {page}/{total_pages}")
    print("Команды: n - следующая страница, p - предыдущая, q - выход из просмотра")
    return total_pages

def select_files_from_list(files):
    """Позволяет пользователю выбрать файлы для поиска"""
    current_page = 1
    items_per_page = 20
    selected_files = []
    
    while True:
        total_pages = display_files_list(files, current_page, items_per_page)
        
        print("\nВыберите действие:")
        print("1. Ввести номера файлов (например: 1,3,5-10)")
        print("2. Выбрать все файлы")
        print("3. Продолжить с текущим выбором")
        print("4. Отмена")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '1':
            range_input = input("Введите номера файлов (например: 1,3,5-10): ").strip()
            try:
                selected = parse_file_range(range_input, len(files))
                if selected:
                    selected_files.extend(selected)
                    selected_files = sorted(list(set(selected_files)))  # Убираем дубликаты
                    print(f"Выбрано файлов: {len(selected_files)}")
                else:
                    print("Не удалось распознать диапазон")
            except Exception as e:
                print(f"Ошибка при разборе диапазона: {e}")
        
        elif choice == '2':
            selected_files = list(range(1, len(files) + 1))
            print(f"Выбраны все файлы ({len(selected_files)} шт.)")
        
        elif choice == '3':
            if selected_files:
                return selected_files
            else:
                print("Сначала выберите файлы!")
        
        elif choice == '4':
            return None
        
        elif choice.lower() == 'n':
            if current_page < total_pages:
                current_page += 1
        
        elif choice.lower() == 'p':
            if current_page > 1:
                current_page -= 1
        
        elif choice.lower() == 'q':
            return selected_files if selected_files else None

def parse_file_range(range_str, max_num):
    """Разбирает строку с диапазонами номеров файлов"""
    selected = []
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            start = max(1, min(start, max_num))
            end = max(start, min(end, max_num))
            selected.extend(range(start, end + 1))
        else:
            try:
                num = int(part)
                if 1 <= num <= max_num:
                    selected.append(num)
            except ValueError:
                continue
    
    return sorted(list(set(selected)))

def get_folder_path():
    """Запрашивает путь к папке у пользователя"""
    while True:
        folder_path = input("Введите путь к папке для поиска: ").strip()
        if not folder_path:
            print("Путь не может быть пустым. Попробуйте ещё раз.")
            continue
        
        if not os.path.isdir(folder_path):
            print(f"Папка '{folder_path}' не найдена или недоступна. Попробуйте ещё раз.")
            continue
        
        return folder_path

def get_max_results():
    """Запрашивает максимальное количество результатов у пользователя"""
    while True:
        try:
            max_input = input("Введите максимальное количество результатов для поиска (или 0 для без ограничений): ").strip()
            
            if not max_input:
                print("Пожалуйста, введите число.")
                continue
                
            max_results = int(max_input)
            
            if max_results < 0:
                print("Количество не может быть отрицательным.")
                continue
                
            if max_results == 0:
                print("Ограничение на количество результатов отключено.")
                return None
            else:
                print(f"Поиск будет остановлен после нахождения {max_results} результатов.")
                return max_results
                
        except ValueError:
            print("Пожалуйста, введите корректное число.")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Ошибка: {str(e)}")

def main():
    print("=== Улучшенный поиск строк в файлах папки ===")
    print("С возможностью выбора файлов по номерам и ограничения результатов\n")
    
    folder_path = get_folder_path()
    
    try:
        # Получаем все файлы в папке и подпапках
        all_files = get_all_files_from_folder(folder_path)
        
        if not all_files:
            print(f"\nВ папке '{folder_path}' не найдено файлов.")
            return
            
        print(f"\nНайдено {len(all_files)} файлов в папке '{folder_path}'")
        
        # Выбор файлов для поиска
        print("\nХотите выбрать конкретные файлы для поиска?")
        print("1. Просмотреть список файлов и выбрать")
        print("2. Искать во всех файлах")
        print("3. Выйти")
        
        file_choice = input("\nВаш выбор: ").strip()
        
        selected_indices = None
        
        if file_choice == '1':
            selected_indices = select_files_from_list(all_files)
            if selected_indices is None:
                print("Поиск отменен.")
                return
            
            # Преобразуем номера в индексы (номера с 1, индексы с 0)
            files_to_search = [all_files[i-1] for i in selected_indices]
            print(f"\nВыбрано {len(files_to_search)} файлов для поиска")
            
            # Показываем первые несколько выбранных файлов
            print("Выбранные файлы (первые 10):")
            for i, idx in enumerate(selected_indices[:10]):
                print(f"  {i+1}. {os.path.basename(all_files[idx-1])}")
            if len(selected_indices) > 10:
                print(f"  ... и ещё {len(selected_indices)-10}")
        
        elif file_choice == '2':
            files_to_search = all_files
            selected_indices = "all"
            print(f"\nБудут обработаны все {len(files_to_search)} файлов")
        
        else:
            print("Поиск отменен.")
            return
        
        # Запрашиваем максимальное количество результатов
        max_results = get_max_results()
        
        print("\nВведите часть строки для поиска (или 'exit' для выхода):")
        
        while True:
            query = input("\nПоиск: ").strip()
            
            if not query:
                print("Введите поисковый запрос.")
                continue
                
            if query.lower() in ('exit', 'quit', 'q'):
                break
                
            start_time = time.time()
            all_results = []
            processed_files = 0
            search_completed = False
            
            print(f"\nНачинаю поиск в {len(files_to_search)} файлах...")
            if max_results:
                print(f"Цель: найти до {max_results} результатов")
            
            # Обрабатываем выбранные файлы поочередно
            total_files = len(files_to_search)
            for idx, file_path in enumerate(files_to_search, 1):
                if search_completed:
                    print(f"Поиск завершен досрочно - достигнуто максимальное количество результатов ({max_results})")
                    break
                    
                processed_files += 1
                file_start_time = time.time()
                
                try:
                    file_size = os.path.getsize(file_path)
                    file_number = selected_indices[idx-1] if selected_indices != "all" else idx
                    print(f"[{idx}/{total_files}] Обработка файла #{file_number}: {os.path.basename(file_path)} ({file_size/1024:.1f} KB)")
                    
                    remaining_results = None
                    if max_results:
                        remaining_results = max_results - len(all_results)
                        if remaining_results <= 0:
                            search_completed = True
                            break
                    
                    file_results = search_in_file(file_path, query, remaining_results)
                    
                    if file_results:
                        print(f"   Найдено совпадений в этом файле: {len(file_results)}")
                        for result in file_results:
                            all_results.append(f"[Файл #{file_number}: {os.path.basename(file_path)}] {result}")
                        
                        if max_results and len(all_results) >= max_results:
                            search_completed = True
                    
                    file_processing_time = time.time() - file_start_time
                    print(f"   Время обработки файла: {file_processing_time:.2f} сек")
                    
                    del file_results
                    
                except Exception as e:
                    print(f"   Ошибка при обработке файла {file_path}: {str(e)}")
                    continue
            
            total_search_time = time.time() - start_time
            
            if not all_results:
                print(f"\nСовпадений не найдено (поиск занял {total_search_time:.2f} сек)")
            else:
                print(f"\nНайдено {len(all_results)} совпадений в {processed_files} файлах (поиск занял {total_search_time:.2f} сек):")
                
                if max_results and len(all_results) >= max_results:
                    print(f"Достигнуто максимальное количество результатов ({max_results})")
                
                print('-' * 80)
                
                max_display = min(100, len(all_results))
                for i, line in enumerate(all_results[:max_display], 1):
                    print(f"{i}. {line.strip()}")
                
                if len(all_results) > max_display:
                    print(f"\n... и ещё {len(all_results)-max_display} совпадений (показаны первые {max_display})")
                print('-' * 80)
                
                save = input("\nСохранить ВСЕ результаты в файл? (y/n): ").strip().lower()
                if save == 'y':
                    save_results_to_file(all_results, query, folder_path, processed_files, max_results, selected_indices)
                
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

if __name__ == "__main__":
    main()