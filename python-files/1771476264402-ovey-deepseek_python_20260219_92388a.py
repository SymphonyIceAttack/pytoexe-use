import os
import sys
import re
from datetime import datetime

# Color codes for blue background, black text
BLUE_BG = '\033[44m'
BLACK = '\033[30m'
RESET = '\033[0m'
BOLD = '\033[1m'

__author__ = "Eng. Ahmed Hegazi"
__version__ = "2.0"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text):
    print(f"{BLUE_BG}{BLACK}{BOLD}{text}{RESET}")

def get_exe_folder():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_unique_filename(folder, filename):
    """Auto-rename if file already exists"""
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    
    while os.path.exists(os.path.join(folder, new_filename)):
        new_filename = f"{name} ({counter}){ext}"
        counter += 1
    
    return new_filename

def show_menu():
    clear_screen()
    print_colored("="*60)
    print_colored(f"   FILE RENAMER v{__version__} - by {__author__}")
    print_colored("="*60)
    print_colored("   BLUE BACKGROUND MODE ACTIVE")
    print_colored("="*60)
    print_colored("1. Add prefix to all files")
    print_colored("2. Add suffix to all files")
    print_colored("3. Replace text in filenames")
    print_colored("4. Convert to lowercase")
    print_colored("5. Convert to uppercase")
    print_colored("6. Add numbering to files")
    print_colored("7. Remove all numbers")
    print_colored("8. Remove all spaces")
    print_colored("9. Remove special characters")
    print_colored("10. Change file extension")
    print_colored("11. Shorten filename")
    print_colored("12. Auto-rename duplicates only")
    print_colored("13. Exit")
    print_colored("="*60)
    return input(f"{BLUE_BG}{BLACK}Choose (1-13): {RESET}")

def get_files():
    folder = get_exe_folder()
    exe_name = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else os.path.basename(__file__)
    files = []
    for f in os.listdir(folder):
        full = os.path.join(folder, f)
        if os.path.isfile(full) and f != exe_name and not f.endswith('.exe'):
            files.append((full, f))
    return folder, files

def rename_files_with_auto(files, new_names):
    """Rename with auto-handling of existing filenames"""
    folder, files_list = files
    renamed_count = 0
    skipped_count = 0
    
    print_colored("\nRenaming files...")
    
    for (full, old), new in zip(files_list, new_names):
        if old != new:
            # Auto-rename if target already exists
            final_new = get_unique_filename(os.path.dirname(full), new)
            new_full = os.path.join(os.path.dirname(full), final_new)
            
            try:
                os.rename(full, new_full)
                print_colored(f"  ✓ {old} -> {final_new}")
                renamed_count += 1
            except Exception as e:
                print_colored(f"  ✗ Error with {old}: {str(e)[:50]}")
                skipped_count += 1
    
    print_colored(f"\nDone! {renamed_count} renamed, {skipped_count} skipped")
    return renamed_count

def add_prefix():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    prefix = input(f"{BLUE_BG}{BLACK}Enter prefix: {RESET}")
    new = [prefix + f for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def add_suffix():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    suffix = input(f"{BLUE_BG}{BLACK}Enter suffix: {RESET}")
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        new.append(f"{name}{suffix}{ext}")
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def replace_text():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    old = input(f"{BLUE_BG}{BLACK}Replace: {RESET}")
    new_t = input(f"{BLUE_BG}{BLACK}With: {RESET}")
    new = [f.replace(old, new_t) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def to_lower():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.lower() for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def to_upper():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.upper() for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def add_numbering():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    try:
        start = input(f"{BLUE_BG}{BLACK}Start number (default 1): {RESET}")
        start = int(start) if start.strip() else 1
    except:
        start = 1
    
    pos = input(f"{BLUE_BG}{BLACK}Number at (b)eginning or (e)nd? {RESET}")
    zeros = input(f"{BLUE_BG}{BLACK}Use leading zeros? (y/n): {RESET}").lower() == 'y'
    
    new = []
    for i, (_, f) in enumerate(files, start):
        name, ext = os.path.splitext(f)
        num = str(i).zfill(3) if zeros else str(i)
        
        if pos.lower() == 'b':
            new.append(f"{num}_{f}")
        else:
            new.append(f"{name}_{num}{ext}")
    
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def remove_numbers():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [re.sub(r'[0-9]', '', f) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def remove_spaces():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.replace(' ', '') for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def remove_special():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [re.sub(r'[^a-zA-Z0-9._-]', '', f) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def change_ext():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new_ext = input(f"{BLUE_BG}{BLACK}New extension (e.g., .txt): {RESET}")
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    
    new = []
    for _, f in files:
        name, _ = os.path.splitext(f)
        new.append(name + new_ext)
    
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def shorten():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    try:
        length = int(input(f"{BLUE_BG}{BLACK}Max length (without extension): {RESET}"))
    except:
        length = 20
    
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        if len(name) > length:
            name = name[:length]
        new.append(name + ext)
    
    rename_files_with_auto((folder, files), new)
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def auto_rename_duplicates():
    """Specifically handle duplicate filenames"""
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    
    print_colored("\nChecking for duplicate names...")
    name_count = {}
    
    # Count occurrences of each name (without extension)
    for _, f in files:
        name, ext = os.path.splitext(f)
        if name not in name_count:
            name_count[name] = []
        name_count[name].append((_, f))
    
    # Rename duplicates
    renamed = 0
    for name, file_list in name_count.items():
        if len(file_list) > 1:
            print_colored(f"\nFound {len(file_list)} files with name: {name}")
            for i, (full, f) in enumerate(file_list):
                if i == 0:
                    print_colored(f"  Keeping: {f}")
                else:
                    name_part, ext = os.path.splitext(f)
                    new_name = f"{name_part} ({i}){ext}"
                    new_full = os.path.join(os.path.dirname(full), new_name)
                    try:
                        os.rename(full, new_full)
                        print_colored(f"  Renamed: {f} -> {new_name}")
                        renamed += 1
                    except Exception as e:
                        print_colored(f"  Error: {f} - {str(e)[:30]}")
    
    print_colored(f"\nRenamed {renamed} duplicate files")
    input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

def main():
    while True:
        try:
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
            elif choice == '12': auto_rename_duplicates()
            elif choice == '13': 
                clear_screen()
                print_colored(f"Goodbye! Thank you for using {__author__}'s File Renamer!")
                print_colored("Blue background mode deactivated.")
                print(f"{RESET}")
                sys.exit()
            else:
                print_colored("Invalid option!")
                input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")
                
        except KeyboardInterrupt:
            print(f"\n\n{BLUE_BG}{BLACK}Goodbye!{RESET}")
            sys.exit(0)
        except Exception as e:
            print_colored(f"Error: {e}")
            input(f"{BLUE_BG}{BLACK}Press Enter...{RESET}")

if __name__ == "__main__":
    # Apply blue background at start
    print(f"{BLUE_BG}{BLACK}", end='')
    main()