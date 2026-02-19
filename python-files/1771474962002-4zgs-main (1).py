import os
import sys
import re
import shutil
from datetime import datetime
import time

# AUTHOR INFORMATION
__author__ = "Eng. Ahmed Hegazi"
__version__ = "3.0"

def get_exe_folder():
    """Get the folder where the executable is actually located"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def log_error(error_message):
    """Log errors to a file instead of closing"""
    folder = get_exe_folder()
    log_file = os.path.join(folder, "renamer_error_log.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] ERROR: {error_message}\n")

def safe_execute(func, *args, **kwargs):
    """Safely execute any function and prevent program from closing on error"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"Error in {func.__name__}: {str(e)}"
        print(f"\n❌ {error_msg}")
        log_error(error_msg)
        print("\nPress Enter to return to main menu...")
        input()
        return None

def show_menu():
    print("\n" + "="*60)
    print(f"   SIMPLE FILE RENAMER v{__version__} - by {__author__}")
    print("="*60)
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
    print("12. Add date/time stamps to filenames")
    print("13. Add folder name to filenames")
    print("14. Convert spaces to underscores or hyphens")
    print("15. Capitalize first letter of each word")
    print("16. Limit/shorten filename to desired length")
    print("17. Filter by file type (only specific extensions)")
    print("18. Include or exclude subfolders")
    print("19. Filter by date (created/modified)")
    print("20. Create numbered backups before renaming")
    print("21. Undo last rename operation")
    print("22. Save rename log to text file")
    print("23. Sort files differently before numbering")
    print("24. Test mode (show changes without applying)")
    print("25. Exit")
    print("="*60)
    return input("Choose option (1-25): ")

def get_files_in_folder(include_subfolders=False, file_filter=None, date_filter=None):
    """Get files with optional filtering"""
    folder_path = get_exe_folder()
    exe_name = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else os.path.basename(__file__)
    
    files = []
    
    if include_subfolders:
        for root, dirs, filenames in os.walk(folder_path):
            for f in filenames:
                full_path = os.path.join(root, f)
                if f != exe_name and not f.endswith('.exe'):
                    rel_path = os.path.relpath(full_path, folder_path)
                    files.append((full_path, rel_path))
    else:
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path) and f != exe_name and not f.endswith('.exe'):
                files.append((full_path, f))
    
    # Apply file type filter
    if file_filter and file_filter != '*':
        filtered_files = []
        for full_path, rel_path in files:
            ext = os.path.splitext(rel_path)[1].lower()
            if ext in [f'.{ft.lower()}' for ft in file_filter.split(',')]:
                filtered_files.append((full_path, rel_path))
        files = filtered_files
    
    # Apply date filter
    if date_filter:
        filtered_files = []
        filter_type, days = date_filter
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for full_path, rel_path in files:
            if filter_type == 'created':
                file_time = os.path.getctime(full_path)
            else:  # modified
                file_time = os.path.getmtime(full_path)
            
            if file_time >= cutoff_time:
                filtered_files.append((full_path, rel_path))
        files = filtered_files
    
    return folder_path, files

def preview_changes(files, new_names, test_mode=False):
    """Preview changes with optional test mode"""
    print("\n" + "="*50)
    print("PREVIEW OF CHANGES:")
    print("="*50)
    
    changes_count = 0
    for (full_path, old), new in zip(files, new_names):
        if old != new:
            if len(files[0]) == 2:  # With full path
                print(f"{old} -> {new}")
            else:  # Without full path
                print(f"{old} -> {new}")
            changes_count += 1
    
    if changes_count == 0:
        print("No changes will be made.")
        return False
    
    print("="*50)
    print(f"Total files to rename: {changes_count}")
    
    if test_mode:
        print("🔍 TEST MODE: No actual changes will be made.")
        input("Press Enter to continue...")
        return False
    
    confirm = input(f"\nApply {changes_count} changes? (y/n): ")
    return confirm.lower() == 'y'

def add_prefix(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    prefix = input("Enter prefix to add: ")
    new_names = [prefix + rel_path for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def add_suffix(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    suffix = input("Enter suffix to add (before extension): ")
    new_names = []
    for _, rel_path in files:
        name, ext = os.path.splitext(rel_path)
        new_names.append(f"{name}{suffix}{ext}")
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def replace_text(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    old_text = input("Enter text to replace: ")
    new_text = input("Enter new text: ")
    new_names = [rel_path.replace(old_text, new_text) for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def to_lowercase(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [rel_path.lower() for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def to_uppercase(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [rel_path.upper() for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def add_numbering(test_mode=False):
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
    leading_zeros = input("Use leading zeros? (y/n): ").lower() == 'y'
    
    new_names = []
    for i, (_, rel_path) in enumerate(files, start):
        name, ext = os.path.splitext(rel_path)
        if leading_zeros:
            num = str(i).zfill(3)
        else:
            num = str(i)
        
        if position == 'b':
            new_names.append(f"{num}_{rel_path}")
        else:
            new_names.append(f"{name}_{num}{ext}")
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_numbers(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [re.sub(r'[0-9]', '', rel_path) for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_spaces(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [rel_path.replace(' ', '') for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_special_characters(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    # Keep letters, numbers, dots, underscores, hyphens
    new_names = [re.sub(r'[^a-zA-Z0-9._-]', '', rel_path) for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Files renamed successfully!")
    input("Press Enter to continue...")

def remove_extensions(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = [os.path.splitext(rel_path)[0] for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Extensions removed successfully!")
    input("Press Enter to continue...")

def change_extension(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_ext = input("Enter new extension (with dot, e.g., .txt): ")
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    
    new_names = []
    for _, rel_path in files:
        name, _ = os.path.splitext(rel_path)
        new_names.append(name + new_ext)
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Extensions changed successfully!")
    input("Press Enter to continue...")

def add_date_stamp(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    date_format = input("Enter date format (e.g., YYYY-MM-DD, YYYYMMDD, DD-MM-YY): ")
    position = input("Add date at (b)eginning or (e)nd? (b/e): ").lower()
    
    current_date = datetime.now().strftime(date_format)
    
    new_names = []
    for _, rel_path in files:
        name, ext = os.path.splitext(rel_path)
        if position == 'b':
            new_names.append(f"{current_date}_{rel_path}")
        else:
            new_names.append(f"{name}_{current_date}{ext}")
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Date stamps added successfully!")
    input("Press Enter to continue...")

def add_folder_name(test_mode=False):
    folder, files = get_files_in_folder(include_subfolders=True)
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = []
    for full_path, rel_path in files:
        folder_name = os.path.basename(os.path.dirname(rel_path))
        if folder_name == '.':
            folder_name = 'root'
        name, ext = os.path.splitext(os.path.basename(rel_path))
        new_names.append(f"{folder_name}_{name}{ext}")
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Folder names added successfully!")
    input("Press Enter to continue...")

def convert_spaces(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    replacement = input("Replace spaces with ( _ or - ): ")
    
    new_names = [rel_path.replace(' ', replacement) for _, rel_path in files]
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Spaces converted successfully!")
    input("Press Enter to continue...")

def capitalize_words(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    new_names = []
    for _, rel_path in files:
        name, ext = os.path.splitext(rel_path)
        capitalized_name = ' '.join(word.capitalize() for word in name.split())
        new_names.append(capitalized_name + ext)
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Words capitalized successfully!")
    input("Press Enter to continue...")

def limit_filename_length(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    try:
        max_length = int(input("Enter maximum filename length (excluding extension): "))
    except:
        print("Invalid number, using 20")
        max_length = 20
    
    new_names = []
    for _, rel_path in files:
        name, ext = os.path.splitext(rel_path)
        if len(name) > max_length:
            name = name[:max_length]
        new_names.append(name + ext)
    
    if preview_changes(files, new_names, test_mode):
        for (full_path, old), new in zip(files, new_names):
            if old != new:
                new_full_path = os.path.join(os.path.dirname(full_path), new)
                os.rename(full_path, new_full_path)
        print("Filenames shortened successfully!")
    input("Press Enter to continue...")

def filter_by_type(test_mode=False):
    file_types = input("Enter file extensions to include (comma-separated, e.g., txt,jpg,png): ")
    folder, files = get_files_in_folder(file_filter=file_types)
    
    if not files:
        print("No matching files found!")
        input("Press Enter to continue...")
        return
    
    print(f"\nFound {len(files)} matching files:")
    for _, rel_path in files:
        print(f"  - {rel_path}")
    input("\nPress Enter to continue...")

def toggle_subfolders(test_mode=False):
    include = input("Include subfolders? (y/n): ").lower() == 'y'
    folder, files = get_files_in_folder(include_subfolders=include)
    
    print(f"\nFound {len(files)} files:")
    for _, rel_path in files[:10]:  # Show first 10
        print(f"  - {rel_path}")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")
    input("\nPress Enter to continue...")

def filter_by_date(test_mode=False):
    print("Filter by:")
    print("1. Creation date")
    print("2. Modification date")
    choice = input("Choose (1 or 2): ")
    
    days = int(input("Files newer than how many days? (enter number): "))
    
    date_type = 'created' if choice == '1' else 'modified'
    folder, files = get_files_in_folder(date_filter=(date_type, days))
    
    print(f"\nFound {len(files)} files modified in the last {days} days:")
    for _, rel_path in files[:10]:  # Show first 10
        print(f"  - {rel_path}")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")
    input("\nPress Enter to continue...")

def create_backups(test_mode=False):
    folder, files = get_files_in_folder()
    if not files:
        input("No files found in folder! Press Enter to continue...")
        return
    
    backup_folder = os.path.join(folder, "Rename_Backups")
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_subfolder = os.path.join(backup_folder, f"backup_{timestamp}")
    os.makedirs(backup_subfolder)
    
    for full_path, rel_path in files:
        backup_path = os.path.join(backup_subfolder, rel_path)
        shutil.copy2(full_path, backup_path)
    
    print(f"Backups created in: {backup_subfolder}")
    input("Press Enter to continue...")

def undo_last_operation():
    print("Undo feature requires saving operation history.")
    print("This will be implemented in a future version.")
    input("Press Enter to continue...")

def save_rename_log():
    print("Log saving feature will be implemented soon.")
    input("Press Enter to continue...")

def sort_files_before_numbering(test_mode=False):
    print("Sort by:")
    print("1. Name (alphabetical)")
    print("2. Size (smallest first)")
    print("3. Size (largest first)")
    print("4. Date created (oldest first)")
    print("5. Date created (newest first)")
    print("6. Date modified (oldest first)")
    print("7. Date modified (newest first)")
    
    choice = input("Choose sort option (1-7): ")
    
    folder, files = get_files_in_folder()
    
    if choice == '1':
        files.sort(key=lambda x: x[1].lower())
    elif choice == '2':
        files.sort(key=lambda x: os.path.getsize(x[0]))
    elif choice == '3':
        files.sort(key=lambda x: os.path.getsize(x[0]), reverse=True)
    elif choice == '4':
        files.sort(key=lambda x: os.path.getctime(x[0]))
    elif choice == '5':
        files.sort(key=lambda x: os.path.getctime(x[0]), reverse=True)
    elif choice == '6':
        files.sort(key=lambda x: os.path.getmtime(x[0]))
    elif choice == '7':
        files.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
    
    print("\nFiles sorted successfully!")
    input("Press Enter to continue...")
    return files

def test_mode_menu():
    print("\n🔍 TEST MODE - No actual changes will be made")
    print("This allows you to see what would happen without renaming files.")
    
    # Re-show main options but in test mode
    choice = show_menu()
    # Map choices to functions with test_mode=True
    test_functions = {
        '1': add_prefix, '2': add_suffix, '3': replace_text,
        '4': to_lowercase, '5': to_uppercase, '6': add_numbering,
        '7': remove_numbers, '8': remove_spaces, '9': remove_special_characters,
        '10': remove_extensions, '11': change_extension, '12': add_date_stamp,
        '13': add_folder_name, '14': convert_spaces, '15': capitalize_words,
        '16': limit_filename_length
    }
    
    if choice in test_functions:
        safe_execute(test_functions[choice], test_mode=True)
    elif choice == '25':
        return
    else:
        print("Test mode not available for this option yet.")
        input("Press Enter to continue...")

def main():
    print("="*60)
    print(f"   SIMPLE FILE RENAMER v{__version__}")
    print(f"   Created by {__author__}")
    print("="*60)
    print(f"Working folder: {get_exe_folder()}")
    print("="*60)
    
    while True:
        try:
            choice = show_menu()
            
            # Map menu choices to functions
            functions = {
                '1': add_prefix, '2': add_suffix, '3': replace_text,
                '4': to_lowercase, '5': to_uppercase, '6': add_numbering,
                '7': remove_numbers, '8': remove_spaces, '9': remove_special_characters,
                '10': remove_extensions, '11': change_extension, '12': add_date_stamp,
                '13': add_folder_name, '14': convert_spaces, '15': capitalize_words,
                '16': limit_filename_length, '17': filter_by_type,
                '18': toggle_subfolders, '19': filter_by_date, '20': create_backups,
                '21': undo_last_operation, '22': save_rename_log,
                '23': sort_files_before_numbering, '24': test_mode_menu
            }
            
            if choice == '25':
                print(f"\nGoodbye! Thank you for using {__author__}'s File Renamer!")
                sys.exit()
            elif choice in functions:
                safe_execute(functions[choice])
            else:
                print("Invalid option!")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user.")
            print(f"Goodbye! - {__author__}")
            sys.exit(0)
        except Exception as e:
            error_msg = f"Unexpected error in main: {str(e)}"
            print(f"\n❌ {error_msg}")
            log_error(error_msg)
            print("\nPress Enter to continue...")
            input()

if __name__ == "__main__":
    main()