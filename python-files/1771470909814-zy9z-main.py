import os
import sys

def show_menu():
    print("\n=== SIMPLE FILE RENAMER ===")
    print("1. Add prefix to all files")
    print("2. Add suffix to all files")
    print("3. Replace text in filenames")
    print("4. Convert to lowercase")
    print("5. Convert to uppercase")
    print("6. Add numbering to files")
    print("7. Exit")
    return input("Choose option (1-7): ")

def get_files_in_folder():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f)) 
             and f != os.path.basename(__file__)
             and not f.endswith('.exe')]
    return folder_path, files

def preview_changes(files, new_names):
    print("\nPreview of changes:")
    for old, new in zip(files, new_names):
        print(f"{old} -> {new}")
    
    confirm = input("\nApply these changes? (y/n): ")
    return confirm.lower() == 'y'

def add_prefix():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
        return
    
    prefix = input("Enter prefix to add: ")
    new_names = [prefix + f for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")

def add_suffix():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
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

def replace_text():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
        return
    
    old_text = input("Enter text to replace: ")
    new_text = input("Enter new text: ")
    new_names = [f.replace(old_text, new_text) for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")

def to_lowercase():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
        return
    
    new_names = [f.lower() for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")

def to_uppercase():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
        return
    
    new_names = [f.upper() for f in files]
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")

def add_numbering():
    folder, files = get_files_in_folder()
    if not files:
        print("No files found in folder!")
        return
    
    start = input("Enter starting number (default 1): ")
    if not start:
        start = 1
    else:
        start = int(start)
    
    new_names = []
    for i, f in enumerate(files, start):
        name, ext = os.path.splitext(f)
        new_names.append(f"{i}_{f}")
    
    if preview_changes(files, new_names):
        for old, new in zip(files, new_names):
            os.rename(os.path.join(folder, old), os.path.join(folder, new))
        print("Files renamed successfully!")

def main():
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
            print("Goodbye!")
            sys.exit()
        else:
            print("Invalid option!")

if __name__ == "__main__":
    main()