import os
import sys
import re

def get_exe_folder():
    """Get the folder where the executable is actually located"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def show_menu():
    print("\n=== SIMPLE FILE RENAMER v2 ===")
    print("1. Add prefix to all files")
    print("2. Add suffix to all files")
    print("3. Replace text in filenames")
    print("4. Convert to lowercase")
    print("5. Convert to uppercase")
    print("6. Add numbering to files")
    print("7. Remove all numbers from filenames")
    print("8. Remove all spaces from filenames")
    print("9. Remove special characters (keep letters, numbers, dots)")
    print("10. Remove file extensions (name only)")
    print("11. Change/rename file extensions")
    print("12. Exit")
    return input("Choose option (1-12): ")

def get_files_in_folder():
    folder_path = get_exe_folder()
    exe_name = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else os.path.basename(__file__)
    
    files = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f)) 
             and f != exe_name]
    return folder_path, files

def preview_changes(files, new_names):
    print("\nPreview of changes:")
    changes_count = 0
    for old, new in zip(files, new_names):
        if old != new:
            print(f"{old} -> {new}")
            changes_count += 1
    
    if changes_count == 0:
        print("No changes will be made.")
        return False
    
    confirm = input(f"\nApply {changes_count} changes? (y/n): ")
    return confirm.lower() == 'y'

def add_prefix():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    prefix = input("Enter prefix to add: ")
    new_names = [prefix + f for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def add_suffix():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    suffix = input("Enter suffix to add (before extension): ")
    new_names = []
    for f in files:
        name, ext = os.path.splitext(f)
        new_names.append(f"{name}{suffix}{ext}")
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def replace_text():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    old_text = input("Enter text to replace: ")
    new_text = input("Enter new text: ")
    new_names = [f.replace(old_text, new_text) for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def to_lowercase():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [f.lower() for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def to_uppercase():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [f.upper() for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def add_numbering():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    try:
        start = input("Enter starting number (default 1): ")
        if not start.strip():
            start = 1
        else:
            start = int(start)
    except:
        print("Invalid number, using 1")
        start = 1
    
    position = input("Add number at (b)eginning or (e)nd? (b/e): ").lower()
    
    new_names = []
    for i, f in enumerate(files, start):
        name, ext = os.path.splitext(f)
        if position == 'b':
            new_names.append(f"{i}_{f}")
        else:
            new_names.append(f"{name}_{i}{ext}")
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_numbers():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [re.sub(r'[0-9]', '', f) for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            if old != new:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_spaces():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [f.replace(' ', '') for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            if old != new:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_special_characters():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    # Keep letters, numbers, dots, underscores, hyphens
    new_names = [re.sub(r'[^a-zA-Z0-9._-]', '', f) for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            if old != new:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_extensions():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [os.path.splitext(f)[0] for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            if old != new:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Extensions removed successfully!")
    input("Press Enter to continue...")

def change_extension():
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_ext = input("Enter new extension (with dot, e.g., .txt): ")
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    
    new_names = []
    for f in files:
        name, _ = os.path.splitext(f)
        new_names.append(name + new_ext)
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            if old != new:
                os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Extensions changed successfully!")
    input("Press Enter to continue...")

def main():
    print("Simple File Renamer v2")
    print(f"Working folder: {get_exe_folder()}")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            add_prefix()
        elif choice == '2':
            add_suffix()
        elif choice == '3':
            replace_text()
        elif choice == '4':
            to_lowercase()
        elif choice == '5':
            to_uppercase()
        elif choice == '6':
            add_numbering()
        elif choice == '7':
            remove_numbers()
        elif choice == '8':
            remove_spaces()
        elif choice == '9':
            remove_special_characters()
        elif choice == '10':
            remove_extensions()
        elif choice == '11':
            change_extension()
        elif choice == '12':
            print("Goodbye!")
            sys.exit()
        else:
            print("Invalid option!")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()