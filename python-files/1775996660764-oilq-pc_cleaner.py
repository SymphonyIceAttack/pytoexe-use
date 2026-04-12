import os
import shutil
import tempfile
import ctypes

# -----------------------------
# TEMP CLEANER FUNCTION
# -----------------------------
def clean_temp():
    temp_paths = [
        tempfile.gettempdir(),              # User temp
        os.environ.get("TEMP"),             # System temp
        os.environ.get("TMP")               # Another temp path
    ]

    for path in temp_paths:
        if path and os.path.exists(path):
            print(f"[+] Cleaning: {path}")

            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        os.remove(file_path)
                    except:
                        pass

                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        shutil.rmtree(dir_path, ignore_errors=True)
                    except:
                        pass

    print("[✔] Temp files cleaned successfully!")


# -----------------------------
# RECYCLE BIN CLEANER (WITH CONFIRMATION)
# -----------------------------
def empty_recycle_bin():
    print("\n⚠️ Warning: This will permanently empty Recycle Bin")
    confirm = input("Type YES to continue: ")

    if confirm == "YES":
        try:
            # Windows API call
            ctypes.windll.shell32.SHEmptyRecycleBinW(
                None, None, 0x00000001
            )
            print("[✔] Recycle Bin emptied successfully!")
        except Exception as e:
            print("[-] Failed to empty Recycle Bin:", e)
    else:
        print("[!] Cancelled by user.")


# -----------------------------
# MAIN MENU
# -----------------------------
def main():
    print("\n===== PC CLEANER TOOL =====")
    print("1. Clean Temp Files")
    print("2. Empty Recycle Bin")
    print("3. Do Both")
    print("4. Exit")

    choice = input("Choose option: ")

    if choice == "1":
        clean_temp()
    elif choice == "2":
        empty_recycle_bin()
    elif choice == "3":
        clean_temp()
        empty_recycle_bin()
    elif choice == "4":
        print("Bye 👋")
    else:
        print("Invalid option")


if __name__ == "__main__":
    main()