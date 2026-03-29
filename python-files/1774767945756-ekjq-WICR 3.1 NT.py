import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import subprocess

class WindowsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("wicr 3.1 NT")
        self.root.geometry("800x600")
        self.root.configure(bg="#a51a89")
        root.iconbitmap("windows-10.ico")

        # Переменные настроек
        self.theme_color = "#861d68"
        self.font_size = 10
        self.wallpaper = "default"

        self.create_desktop()

    def create_desktop(self):
        # Панель задач
        taskbar = tk.Frame(self.root, bg="#680b44", height=40)
        taskbar.pack(side="bottom", fill="x")

        start_btn = tk.Button(taskbar, text="Start", bg="#810876", fg="white",
                           command=self.show_start_menu)
        start_btn.pack(side="left", padx=5, pady=5)

        # Иконки приложений на рабочем столе
        self.create_icon("проводник", 50, 50, self.open_notepad)
        self.create_icon("Калькулятор", 200, 50, self.open_calculator)
        self.create_icon("медиа плеер", 350, 50, self.open_settings)
        self.create_icon("Браузер", 500, 50, self.open_browser)
        self.create_icon("Калькулятор 2", 50, 200, self.open_calendar)
        self.create_icon("О программе", 200, 200, self.about_app)

    def create_icon(self, text, x, y, command):
        icon = tk.Button(self.root, text=text, width=10, height=3,
                       command=command, bg="lightblue")
        icon.place(x=x, y=y)

    def show_start_menu(self):
        start_menu = tk.Toplevel(self.root)
        start_menu.title("Start Menu")
        start_menu.geometry("300x400+0+360")
        start_menu.configure(bg="#2a2a2a")
        start_menu.overrideredirect(True)

        apps = [
            ("проводник", self.open_notepad),
            ("Калькулятор", self.open_calculator),
            ("медиа плеер", self.open_settings),
            ("Браузер", self.open_browser),
            ("калькулятор 2", self.open_calendar),
            ("О программе", self.about_app)
        ]

        for text, cmd in apps:
            btn = tk.Button(start_menu, text=text, bg="#861595", fg="white",
                      command=cmd, anchor="w")
            btn.pack(fill="x", padx=10, pady=2)

        close_btn = tk.Button(start_menu, text="Закрыть", bg="#888", fg="white",
                         command=start_menu.destroy)
        close_btn.pack(pady=10)

    # Приложения
    def open_notepad(self):
        subprocess.Popen("exp.exe")

    def open_calculator(self):
        subprocess.Popen("calc.exe")

    def open_browser(self):
        subprocess.Popen('Internet Explorer\iexplore.exe')

    def open_calendar(self):
        subprocess.Popen("calc_win11.exe")

    def about_app(self):
         root = tk.Tk()
         root.title("об системе")
         root.iconbitmap('win.ico')
         label = tk.Label(root, text="виртуальная ОС WICR версия 3.1 NT", font="Arial, 14", fg="blue")
         label.pack(padx=20, pady=20)
        
    def apply_theme(self, theme_var):
        self.theme_color = theme_var.get()
        messagebox.showinfo("Тема", f"Цвет темы изменён на {self.theme_color}")

    def open_settings(self):
        subprocess.Popen('Windows Media Player\wmplayer.exe')

# Основная функция запуска приложения
def main():
    root = tk.Tk()
    app = WindowsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
