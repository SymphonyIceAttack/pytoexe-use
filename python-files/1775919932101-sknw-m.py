import os
import shutil
import tempfile
import ctypes

def delete_files_in_folder(folder):
    if not os.path.exists(folder):
        return

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Skipped: {file_path}")

def clean_temp():
    print("Cleaning TEMP folder...")
    delete_files_in_folder(tempfile.gettempdir())

def clean_windows_temp():
    print("Cleaning Windows TEMP folder...")
    windows_temp = r"C:\Windows\Temp"
    delete_files_in_folder(windows_temp)

def empty_recycle_bin():
    print("Emptying Recycle Bin...")
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
    except:
        print("Failed to empty recycle bin")

def main():
    print("=== Windows Optimizer Tool ===")
    clean_temp()
    clean_windows_temp()
    empty_recycle_bin()
    print("Done! System cleaned 🚀")

if __name__ == "__main__":
    main()