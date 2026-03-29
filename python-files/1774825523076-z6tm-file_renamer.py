import os

def get_file_list(folder):
    """Возвращает список всех файлов в указанной папке."""
    try:
        files = os.listdir(folder)
        return [f for f in files if os.path.isfile(os.path.join(folder, f))]
    except Exception as e:
        print(f"Ошибка при получении списка файлов: {e}")
        return []

def get_folder_list(folder):
    """Возвращает список всех папок в указанной папке."""
    try:
        folders = os.listdir(folder)
        return [f for f in folders if os.path.isdir(os.path.join(folder, f))]
    except Exception as e:
        print(f"Ошибка при получении списка папок: {e}")
        return []

def load_new_names(file_path):
    """Загружает новые имена файлов из текстового файла."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except Exception as e:
        print(f"Ошибка при чтении файла имен: {e}")
        return []

def rename_files(folder, new_names):
    """Переименовывает файлы в указанной папке, сохраняя расширения."""
    files = get_file_list(folder)
    file_count = len(files)
    name_count = len(new_names)

    print(f"Найдено файлов: {file_count}")
    print(f"Названий в текстовом файле: {name_count}")

    for i in range(min(file_count, name_count)):
        old_file = files[i]
        old_file_name, old_extension = os.path.splitext(old_file)  # Получаем имя и расширение
        new_file = new_names[i] + old_extension  # Добавляем расширение к новому имени
        old_file_path = os.path.join(folder, old_file)
        new_file_path = os.path.join(folder, new_file)

        try:
            os.rename(old_file_path, new_file_path)
            print(f"Переименован: {old_file} -> {new_file}")
        except Exception as e:
            print(f"Ошибка при переименовании {old_file}: {e}")

def rename_folders(folder, new_names):
    """Переименовывает папки в указанной папке."""
    folders = get_folder_list(folder)
    folder_count = len(folders)
    name_count = len(new_names)

    print(f"Найдено папок: {folder_count}")
    print(f"Названий в текстовом файле: {name_count}")

    for i in range(min(folder_count, name_count)):
        old_folder = folders[i]
        new_folder = new_names[i]  # Новое имя без расширения
        old_folder_path = os.path.join(folder, old_folder)
        new_folder_path = os.path.join(folder, new_folder)

        try:
            os.rename(old_folder_path, new_folder_path)
            print(f"Переименована папка: {old_folder} -> {new_folder}")
        except Exception as e:
            print(f"Ошибка при переименовании папки {old_folder}: {e}")

def main():
    # Определяем текущую рабочую директорию и пути
    current_folder = os.getcwd()
    names_file = os.path.join(current_folder, 'names.txt')
    folders_to_rename = os.path.join(current_folder, 'folders_to_rename')

    # Загружаем новые имена
    new_names = load_new_names(names_file)
    
    # Получаем список папок
    folder_list = get_folder_list(folders_to_rename)

    if not folder_list:
        print("В указанной папке нет папок для переименования.")
        return

    print("Найдены папки для переименования:")
    for idx, val in enumerate(folder_list):
        print(f"{idx + 1}: {val}")

    # Если найдено больше одной папки, запрашиваем, какую из них использовать
    if len(folder_list) > 1:
        folder_choice = input("Введите номер папки для переименования (или 'все' для всех): ").strip()
        
        if folder_choice.lower() == 'все':
            for folder in folder_list:
                rename_files(os.path.join(folders_to_rename, folder), new_names)
                rename_folders(os.path.join(folders_to_rename, folder), new_names)
        else:
            try:
                index = int(folder_choice) - 1
                if 0 <= index < len(folder_list):
                    folder_name = folder_list[index]
                    rename_files(os.path.join(folders_to_rename, folder_name), new_names)
                    rename_folders(os.path.join(folders_to_rename, folder_name), new_names)
                else:
                    print("Недопустимый номер папки.")
            except ValueError:
                print("Введите корректный номер.")
    else:
        # Если только одна папка, переименовываем в ней
        rename_files(os.path.join(folders_to_rename, folder_list[0]), new_names)
        rename_folders(os.path.join(folders_to_rename, folder_list[0]), new_names)

if __name__ == "__main__":
    main()

input()