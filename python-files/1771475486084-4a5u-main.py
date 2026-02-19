import os
import sys
import re
import shutil
from datetime import datetime
import time

__author__ = "Eng. Ahmed Hegazi"
__version__ = "3.0"

def get_exe_folder():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def show_menu():
    print("\n" + "="*50)
    print(f"FILE RENAMER v{__version__} - {__author__}")
    print("="*50)
    print("1. Add prefix")
    print("2. Add suffix")
    print("3. Replace text")
    print("4. To lowercase")
    print("5. To uppercase")
    print("6. Add numbering")
    print("7. Remove numbers")
    print("8. Remove spaces")
    print("9. Remove special characters")
    print("10. Change extension")
    print("11. Shorten filename")
    print("12. Exit")
    return input("Choose (1-12): ")

def get_files():
    folder = get_exe_folder()
    exe_name = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else os.path.basename(__file__)
    files = []
    for f in os.listdir(folder):
        full = os.path.join(folder, f)
        if os.path.isfile(full) and f != exe_name and not f.endswith('.exe'):
            files.append((full, f))
    return folder, files

def rename_files(files, new_names):
    folder, files_list = files
    for (full, old), new in zip(files_list, new_names):
        if old != new:
            new_full = os.path.join(os.path.dirname(full), new)
            os.rename(full, new_full)
    print("Done!")

# Option functions
def add_prefix():
    folder, files = get_files()
    if not files: return
    prefix = input("Prefix: ")
    new = [prefix + f for _, f in files]
    rename_files((folder, files), new)

def add_suffix():
    folder, files = get_files()
    if not files: return
    suffix = input("Suffix: ")
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        new.append(f"{name}{suffix}{ext}")
    rename_files((folder, files), new)

def replace_text():
    folder, files = get_files()
    if not files: return
    old = input("Replace: ")
    new_t = input("With: ")
    new = [f.replace(old, new_t) for _, f in files]
    rename_files((folder, files), new)

def to_lower():
    folder, files = get_files()
    if not files: return
    new = [f.lower() for _, f in files]
    rename_files((folder, files), new)

def to_upper():
    folder, files = get_files()
    if not files: return
    new = [f.upper() for _, f in files]
    rename_files((folder, files), new)

def add_numbering():
    folder, files = get_files()
    if not files: return
    start = input("Start number (default 1): ")
    start = int(start) if start.strip() else 1
    pos = input("Number at (b)eginning or (e)nd? ")
    new = []
    for i, (_, f) in enumerate(files, start):
        name, ext = os.path.splitext(f)
        if pos.lower() == 'b':
            new.append(f"{i}_{f}")
        else:
            new.append(f"{name}_{i}{ext}")
    rename_files((folder, files), new)

def remove_numbers():
    folder, files = get_files()
    if not files: return
    new = [re.sub(r'[0-9]', '', f) for _, f in files]
    rename_files((folder, files), new)

def remove_spaces():
    folder, files = get_files()
    if not files: return
    new = [f.replace(' ', '') for _, f in files]
    rename_files((folder, files), new)

def remove_special():
    folder, files = get_files()
    if not files: return
    new = [re.sub(r'[^a-zA-Z0-9._-]', '', f) for _, f in files]
    rename_files((folder, files), new)

def change_ext():
    folder, files = get_files()
    if not files: return
    new_ext = input("New extension (e.g., .txt): ")
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    new = []
    for _, f in files:
        name, _ = os.path.splitext(f)
        new.append(name + new_ext)
    rename_files((folder, files), new)

def shorten():
    folder, files = get_files()
    if not files: return
    try:
        length = int(input("Max length (without extension): "))
    except:
        length = 20
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        if len(name) > length:
            name = name[:length]
        new.append(name + ext)
    rename_files((folder, files), new)

def main():
    print(f"Folder: {get_exe_folder()}")
    while True:
        choice = show_menu()
        if choice == '1': add_prefix()
        elif choice == '2': add_suffix()
        elif choice == '3': replace_text()
        elif choice == '4': to_lower()
        elif choice == '5': to_upper()
        elif choice == '6': add_numbering()
        elif choice == '7': remove_numbers()
        elif choice == '8': remove_spaces()
        elif choice == '9': remove_special()
        elif choice == '10': change_ext()
        elif choice == '11': shorten()
        elif choice == '12': 
            print(f"Goodbye! - {__author__}")
            sys.exit()
        else:
            print("Invalid")
        input("\nPress Enter...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit")