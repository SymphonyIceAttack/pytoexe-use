import tkinter as tk
import subprocess
import os

# =========================
# CONFIG
# =========================

EXCEL_PATH = r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"

APP_DEVICE_SYSTEM = r"C:\Users\HASCHKO\OneDrive - Hong Kong Airport Services Ltd\HAS Device Management\HAS-DeviceInformationSystem(Push-to-Talk).xlsm"

# If you have more apps, add here:
APP_1 = APP_DEVICE_SYSTEM


# =========================
# CORE FUNCTION
# =========================

def open_excel(file_path):
    if not os.path.exists(file_path):
        print("File not found:")
        print(file_path)
        return

    try:
        subprocess.Popen([EXCEL_PATH, file_path])
    except Exception as e:
        print("Error opening Excel:", e)


# =========================
# BUTTON ACTIONS
# =========================

def launch_app1():
    open_excel(APP_1)

def launch_app2():
    # placeholder for future app
    print("App 2 not configured yet")

def launch_app3():
    # placeholder for future app
    print("App 3 not configured yet")


# =========================
# UI
# =========================

root = tk.Tk()
root.title("HAS Mini App Launcher")
root.geometry("320x260")
root.resizable(False, False)

label = tk.Label(root, text="Select Mini Application", font=("Arial", 14))
label.pack(pady=20)

btn1 = tk.Button(root, text="Device Management System", width=28, command=launch_app1)
btn1.pack(pady=8)

btn2 = tk.Button(root, text="App 2 (Not Set)", width=28, command=launch_app2)
btn2.pack(pady=8)

btn3 = tk.Button(root, text="App 3 (Not Set)", width=28, command=launch_app3)
btn3.pack(pady=8)

exit_btn = tk.Button(root, text="Exit", width=28, command=root.quit)
exit_btn.pack(pady=15)

root.mainloop()