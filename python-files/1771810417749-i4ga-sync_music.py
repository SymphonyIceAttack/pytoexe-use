import os
import shutil
import math
from collections import OrderedDict

# ===== НАСТРОЙКИ =====
SOURCE = r"C:\Users\artem\Downloads\Мне нравится"
BASE_FOLDER = "Music"
MAX_FILES = 1000
# ====================

# Определяем папку с программой (флешка)
USB = os.path.dirname(os.path.abspath(__file__))

def get_artist(filename):
    """Извлекает исполнителя из названия файла"""
    # Убираем расширение .mp3
    name = filename[:-4] if filename.lower().endswith('.mp3') else filename
    
    # Ищем паттерн "Исполнитель - Название"
    separators = [" - ", " – ", " — ", " -", "-"]
    
    for sep in separators:
        if sep in name:
            artist = name.split(sep)[0].strip()
            return artist
    
    # Если нет разделителя, возвращаем первый символ как "Unknown"
    if name:
        return f"Unknown_{name[0]}"
    return "Unknown"

def get_first_char(text):
    """Получает первый символ для группировки"""
    if not text:
        return '#'
    return text[0]

def get_letter_for_display(char):
    """Преобразует символ для отображения (только буквы)"""
    if char.isalpha():
        if 'a' <= char.lower() <= 'z' or 'а' <= char.lower() <= 'я':
            return char.upper()
    return None

def get_sort_key(artist):
    """Ключ для сортировки: спецсимволы, цифры, буквы"""
    first = artist[0]
    if not first.isalnum():
        return (0, artist.lower())  # Спецсимволы первые
    elif first.isdigit():
        return (1, artist.lower())  # Потом цифры
    else:
        return (2, artist.lower())  # Потом буквы

def case_insensitive_sort(files):
    """Сортировка файлов"""
    return sorted(files, key=lambda s: s.lower())

def main():
    print("=" * 70)
    print("           MUSIC SYNC FOR CAR")
    print("=" * 70)
    print(f"\nUSB drive: {USB}")
    print(f"Music folder: {SOURCE}")
    print(f"Max files per folder: {MAX_FILES}")
    print(f"Mode: Artists grouped by first letter (strict grouping)\n")

    # Проверяем существует ли папка с музыкой
    if not os.path.exists(SOURCE):
        print("[ERROR] Music folder not found!")
        input("\nPress Enter to exit...")
        return

    # Удаляем старые папки
    print("[1/4] Cleaning old folders...")
    for item in os.listdir(USB):
        item_path = os.path.join(USB, item)
        if os.path.isdir(item_path) and item.startswith(BASE_FOLDER):
            shutil.rmtree(item_path)
            print(f"  - Deleted {item}")

    # Удаляем старые mp3 из корня
    for file in os.listdir(USB):
        if file.lower().endswith('.mp3'):
            os.remove(os.path.join(USB, file))

    # Получаем список всех MP3 файлов
    print("\n[2/4] Scanning for MP3 files...")
    all_files = []
    skipped_files = []
    
    for file in os.listdir(SOURCE):
        if file.lower().endswith('.mp3'):
            if "(1)" in file:
                skipped_files.append(file)
                print(f"  [SKIPPING DUPLICATE] {file}")
            else:
                all_files.append(file)
    
    # Сортируем все файлы
    all_files = case_insensitive_sort(all_files)
    total = len(all_files)
    skipped = len(skipped_files)
    
    print(f"\nFound {total} tracks (skipped {skipped} duplicates)")

    # Группируем по артистам
    print("\n[3/4] Grouping by artist...")
    
    artist_groups = OrderedDict()
    artist_lower_map = {}
    
    for file in all_files:
        artist = get_artist(file)
        artist_lower = artist.lower()
        
        if artist_lower not in artist_lower_map:
            artist_lower_map[artist_lower] = artist
        
        original_artist = artist_lower_map[artist_lower]
        
        if original_artist not in artist_groups:
            artist_groups[original_artist] = []
        artist_groups[original_artist].append(file)
    
    # Получаем список артистов
    all_artists = list(artist_groups.keys())
    
    # Группируем по первой букве
    letter_groups = {}
    artist_to_letter = {}
    
    for artist in all_artists:
        first_char = get_first_char(artist)
        if first_char not in letter_groups:
            letter_groups[first_char] = []
        letter_groups[first_char].append(artist)
        artist_to_letter[artist] = first_char
    
    # Сортируем буквы для вывода
    sorted_letters = sorted(letter_groups.keys(), 
                           key=lambda x: (0 if not x.isalnum() else 1 if x.isdigit() else 2, x))
    
    print(f"\nFound {len(artist_groups)} unique artists")
    print(f"Grouped by {len(letter_groups)} unique first characters:")
    
    for letter in sorted_letters:
        artists = letter_groups[letter]
        track_count = sum(len(artist_groups[a]) for a in artists)
        if letter.isalpha():
            display_char = letter.upper()
            print(f"  {display_char}: {len(artists)} artists, {track_count} tracks")
        else:
            print(f"  [SYMBOLS/DIGITS]: {len(artists)} artists, {track_count} tracks")

    # Подтверждение
    print("\nWARNING: All old folders will be DELETED from USB!")
    answer = input("\nStart copying? (Y/N): ").upper()
    if answer != 'Y':
        print("Cancelled.")
        input("\nPress Enter to exit...")
        return

    # Сортируем артистов для копирования
    sorted_artists = sorted(all_artists, key=lambda a: get_sort_key(a))
    
    # Группируем по папкам, сохраняя все артисты с одинаковой первой буквой вместе
    print("\n[4/4] Copying files...")
    
    folders_info = []
    current_folder = 1
    current_artists = []
    current_letters = set()
    current_count = 0
    
    i = 0
    while i < len(sorted_artists):
        artist = sorted_artists[i]
        first_char = artist_to_letter[artist]
        artist_size = len(artist_groups[artist])
        
        # Проверяем, можно ли добавить этого артиста в текущую папку
        can_add = True
        
        # Если это первая буква в папке - можно добавлять
        if not current_letters:
            can_add = True
        # Если буква уже есть в папке - можно добавлять
        elif first_char in current_letters:
            can_add = True
        # Если буквы нет в папке, проверяем поместится ли весь remaining этой буквы
        else:
            # Считаем все треки для этой буквы
            remaining_artists = []
            j = i
            while j < len(sorted_artists) and artist_to_letter[sorted_artists[j]] == first_char:
                remaining_artists.append(sorted_artists[j])
                j += 1
            
            total_for_letter = sum(len(artist_groups[a]) for a in remaining_artists)
            
            # Если вся буква помещается - можно добавить
            if current_count + total_for_letter <= MAX_FILES:
                can_add = True
            else:
                can_add = False
        
        if can_add:
            # Добавляем артиста в текущую папку
            current_artists.append(artist)
            current_letters.add(first_char)
            
            # Копируем треки
            folder_path = os.path.join(USB, f"{BASE_FOLDER} {current_folder}")
            os.makedirs(folder_path, exist_ok=True)
            
            for track in artist_groups[artist]:
                src = os.path.join(SOURCE, track)
                dst = os.path.join(folder_path, track)
                shutil.copy2(src, dst)
                current_count += 1
            
            print(f"  Added {artist} ({artist_size} tracks) to folder {current_folder}")
            i += 1
        else:
            # Сохраняем текущую папку и переходим к следующей
            if current_artists:
                # Получаем первую и последнюю букву для отображения (только буквы)
                letter_items = [c for c in current_letters if c.isalpha()]
                
                if letter_items:
                    first_display = min(letter_items, key=lambda x: x.upper()).upper()
                    last_display = max(letter_items, key=lambda x: x.upper()).upper()
                else:
                    first_display = "SYM"
                    last_display = "SYM"
                
                folders_info.append({
                    'number': current_folder,
                    'first': first_display,
                    'last': last_display,
                    'count': current_count
                })
            
            current_folder += 1
            current_artists = []
            current_letters = set()
            current_count = 0
    
    # Сохраняем последнюю папку
    if current_artists:
        letter_items = [c for c in current_letters if c.isalpha()]
        
        if letter_items:
            first_display = min(letter_items, key=lambda x: x.upper()).upper()
            last_display = max(letter_items, key=lambda x: x.upper()).upper()
        else:
            first_display = "SYM"
            last_display = "SYM"
        
        folders_info.append({
            'number': current_folder,
            'first': first_display,
            'last': last_display,
            'count': current_count
        })

    # Переименовываем все папки в конце
    print("\n[5/4] Renaming folders...")
    
    for info in folders_info:
        old_path = os.path.join(USB, f"{BASE_FOLDER} {info['number']}")
        new_name = f"{BASE_FOLDER} {info['number']} - {info['first']}-{info['last']}"
        new_path = os.path.join(USB, new_name)
        
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
                print(f"  Renamed: {BASE_FOLDER} {info['number']} -> {new_name}")
            except PermissionError:
                # Альтернативный метод
                os.makedirs(new_path, exist_ok=True)
                for file in os.listdir(old_path):
                    shutil.move(os.path.join(old_path, file), os.path.join(new_path, file))
                os.rmdir(old_path)
                print(f"  Moved files to: {new_name}")

    # Результат
    print("\n" + "=" * 70)
    print("                 DONE!")
    print("=" * 70)
    print(f"\nTotal tracks copied: {total}")
    print(f"Duplicates skipped: {skipped}")
    print(f"Total folders used: {current_folder}\n")

    # Подсчет файлов в каждой папке
    total_in_folders = 0
    
    for info in folders_info:
        folder_name = f"{BASE_FOLDER} {info['number']} - {info['first']}-{info['last']}"
        folder_path = os.path.join(USB, folder_name)
        
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]
            count = len(files)
            print(f"  {folder_name}: {count} tracks")
            total_in_folders += count

    print(f"\nTotal in folders: {total_in_folders}")
    
    # Показываем распределение по буквам
    print("\nLetter distribution:")
    for letter in sorted_letters:
        if letter.isalpha():
            display_char = letter.upper()
            
            # Находим в какой папке эта буква
            folder_num = None
            for info in folders_info:
                if info['first'] <= display_char <= info['last']:
                    folder_num = info['number']
                    break
            
            if folder_num:
                artists = letter_groups[letter]
                track_count = sum(len(artist_groups[a]) for a in artists)
                print(f"  {display_char}: folder {folder_num} ({len(artists)} artists, {track_count} tracks)")

    print("\n" + "=" * 70)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()