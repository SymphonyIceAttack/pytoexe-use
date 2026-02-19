import os
import sys
import re
from datetime import datetime

# More readable colors - White background, Black text
BG_WHITE = '\033[47m'
TEXT_BLACK = '\033[30m'
BOLD = '\033[1m'
RESET = '\033[0m'

__author__ = "Eng. Ahmed Hegazi"
__version__ = "2.2"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text):
    print(f"{BG_WHITE}{TEXT_BLACK}{BOLD}{text}{RESET}")

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
    print_colored("   WHITE BACKGROUND MODE - Easy to Read")
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
    print_colored("10. Remove ALL dots (complete) - no dots left")  # UPDATED
    print_colored("11. Remove extension only (keep name)")          # NEW
    print_colored("12. Change file extension")
    print_colored("13. Shorten filename")
    print_colored("14. Auto-rename duplicates only")
    print_colored("15. Exit")
    print_colored("="*60)
    return input(f"{BG_WHITE}{TEXT_BLACK}Choose (1-15): {RESET}")

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
    prefix = input(f"{BG_WHITE}{TEXT_BLACK}Enter prefix: {RESET}")
    new = [prefix + f for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def add_suffix():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    suffix = input(f"{BG_WHITE}{TEXT_BLACK}Enter suffix: {RESET}")
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        new.append(f"{name}{suffix}{ext}")
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def replace_text():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    old = input(f"{BG_WHITE}{TEXT_BLACK}Replace: {RESET}")
    new_t = input(f"{BG_WHITE}{TEXT_BLACK}With: {RESET}")
    new = [f.replace(old, new_t) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def to_lower():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.lower() for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def to_upper():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.upper() for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def add_numbering():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    try:
        start = input(f"{BG_WHITE}{TEXT_BLACK}Start number (default 1): {RESET}")
        start = int(start) if start.strip() else 1
    except:
        start = 1
    
    pos = input(f"{BG_WHITE}{TEXT_BLACK}Number at (b)eginning or (e)nd? {RESET}")
    zeros = input(f"{BG_WHITE}{TEXT_BLACK}Use leading zeros? (y/n): {RESET}").lower() == 'y'
    
    new = []
    for i, (_, f) in enumerate(files, start):
        name, ext = os.path.splitext(f)
        num = str(i).zfill(3) if zeros else str(i)
        
        if pos.lower() == 'b':
            new.append(f"{num}_{f}")
        else:
            new.append(f"{name}_{num}{ext}")
    
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def remove_numbers():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [re.sub(r'[0-9]', '', f) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def remove_spaces():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [f.replace(' ', '') for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def remove_special():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new = [re.sub(r'[^a-zA-Z0-9._-]', '', f) for _, f in files]
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def remove_all_dots_completely():
    """Remove EVERY dot from filename - no dots remaining at all"""
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    
    print_colored("\nRemoving ALL dots from filenames...")
    new = []
    for _, f in files:
        # Remove EVERY single dot from the filename
        new_name = f.replace('.', '')
        new.append(new_name)
    
    rename_files_with_auto((folder, files), new)
    print_colored("\n✅ All dots removed! Files now have NO extensions.")
    print_colored("   Use option 12 to add new extension.")
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def remove_extension_only():
    """Remove only the extension (keeps name, removes dot and extension)"""
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    
    print_colored("\nRemoving extensions only...")
    new = []
    for _, f in files:
        # Keep name part only, remove extension and its dot
        name, _ = os.path.splitext(f)
        new.append(name)
    
    rename_files_with_auto((folder, files), new)
    print_colored("\n✅ Extensions removed! Files now have no extensions.")
    print_colored("   Use option 12 to add new extension.")
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def change_ext():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    new_ext = input(f"{BG_WHITE}{TEXT_BLACK}New extension (e.g., .txt): {RESET}")
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    
    new = []
    for _, f in files:
        name, _ = os.path.splitext(f)
        new.append(name + new_ext)
    
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

def shorten():
    folder, files = get_files()
    if not files: 
        input("No files found! Press Enter...")
        return
    try:
        length = int(input(f"{BG_WHITE}{TEXT_BLACK}Max length (without extension): {RESET}"))
    except:
        length = 20
    
    new = []
    for _, f in files:
        name, ext = os.path.splitext(f)
        if len(name) > length:
            name = name[:length]
        new.append(name + ext)
    
    rename_files_with_auto((folder, files), new)
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

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
    input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

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
            elif choice == '10': remove_all_dots_completely()
            elif choice == '11': remove_extension_only()
            elif choice == '12': change_ext()
            elif choice == '13': shorten()
            elif choice == '14': auto_rename_duplicates()
            elif choice == '15': 
                clear_screen()
                print_colored(f"Goodbye! Thank you for using {__author__}'s File Renamer!")
                print_colored("White background mode deactivated.")
                print(f"{RESET}")
                sys.exit()
            else:
                print_colored("Invalid option!")
                input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")
                
        except KeyboardInterrupt:
            print(f"\n\n{BG_WHITE}{TEXT_BLACK}Goodbye!{RESET}")
            sys.exit(0)
        except Exception as e:
            print_colored(f"Error: {e}")
            input(f"{BG_WHITE}{TEXT_BLACK}Press Enter...{RESET}")

if __name__ == "__main__":
    # Apply white background at start
    print(f"{BG_WHITE}{TEXT_BLACK}", end='')
    main()