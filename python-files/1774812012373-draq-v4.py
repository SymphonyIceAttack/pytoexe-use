import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import subprocess
import sys
import json

if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Матвей пидарас")
        self.root.iconbitmap("GL.ico")
        self.root.geometry("800x600")
        self.root.configure(bg="white")
        self.data_file = "launcher_data.json"
        self.language = "ru"
        self.games_data = []
        self.apps_data = []
        self.load_data()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.games_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.games_frame, text="Игры")
        self.create_games_tab()
        self.apps_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.apps_frame, text="Приложения")
        self.create_apps_tab()
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Настройки")
        self.create_settings_tab()

        # Вкладка "Выйти"
        self.exit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.exit_frame, text="Выйти")
        self.create_exit_tab()

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_data(self):
        """Загружает сохранённые данные из файла."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            self.games_data = data.get("games", [])
            self.apps_data = data.get("apps", [])
        except Exception as e:
            messagebox.showwarning("Предупреждение", f"Не удалось загрузить данные: {e}\nБудет создан новый файл.")
            self.games_data = []
            self.apps_data = []

    def save_data(self):
        """Сохраняет данные в файл."""
        try:
            data = {
                "games": self.games_data,
                "apps": self.apps_data
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")

    def on_closing(self):
        """Вызывается при закрытии окна."""
        self.save_data()
        self.root.quit()
        self.root.destroy()

    def create_games_tab(self):
        """Создаёт интерфейс вкладки «Игры» с кнопками для каждой игры."""
        ttk.Label(self.games_frame, text="Мои игры", font=("Arial", 12, "bold")).pack(pady=10)
        self.games_buttons_frame = ttk.Frame(self.games_frame)
        self.games_buttons_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.refresh_games_list()

    def create_apps_tab(self):
        """Создаёт интерфейс вкладки «Приложения»."""
        ttk.Label(self.apps_frame, text="Мои приложения", font=("Arial", 12, "bold")).pack(pady=10)
        self.apps_buttons_frame = ttk.Frame(self.apps_frame)
        self.apps_buttons_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.refresh_apps_list()

    def create_exit_tab(self):
        """Создаёт вкладку «Выйти»."""
        self.exit_btn = ttk.Button(
            self.exit_frame,
            text="Выйти из программы",
            command=self.exit_program,
            width=20
        )
        self.exit_btn.pack(pady=20)

    def create_settings_tab(self):
        """Создаёт вкладку «Настройки» с управлением элементами."""
        # Язык интерфейса
        ttk.Label(self.settings_frame, text="Язык интерфейса:", font=("Arial", 10)).pack(pady=5)
        self.lang_var = tk.StringVar(value=self.language)
        ttk.Radiobutton(
            self.settings_frame,
            text="Русский",
            variable=self.lang_var,
            value="ru",
            command=self.change_language
        ).pack(anchor='w', padx=20)
        ttk.Radiobutton(
            self.settings_frame,
            text="English",
            variable=self.lang_var,
            value="en",
            command=self.change_language
        ).pack(anchor='w', padx=20)

        # Разделитель
        ttk.Separator(self.settings_frame, orient='horizontal').pack(fill='x', pady=15)

        # Управление играми
        ttk.Label(self.settings_frame, text="Управление играми", font=("Arial", 11, "bold")).pack(pady=(10, 5))
        ttk.Button(
            self.settings_frame,
            text="Добавить игру",
            command=self.add_game
        ).pack(pady=2, fill='x', padx=20)
        # Список для удаления игр
        ttk.Label(self.settings_frame, text="Удалить игру:").pack(anchor='w', padx=20, pady=(10, 0))
        self.games_listbox = tk.Listbox(self.settings_frame, height=4)
        self.games_listbox.pack(fill='x', padx=20, pady=2)
        ttk.Button(
            self.settings_frame,
            text="Удалить выбранную игру",
            command=self.remove_selected_game
        ).pack(pady=2, fill='x', padx=20)

        # Разделитель
        ttk.Separator(self.settings_frame, orient='horizontal').pack(fill='x', pady=15)

        # Управление приложениями
        ttk.Label(self.settings_frame, text="Управление приложениями", font=("Arial", 11, "bold")).pack(pady=(10, 5))
        ttk.Button(
            self.settings_frame,
            text="Добавить приложение",
            command=self.add_app
        ).pack(pady=2, fill='x', padx=20)
        # Список для удаления приложений
        ttk.Label(self.settings_frame, text="Удалить приложение:").pack(anchor='w', padx=20, pady=(10, 0))
        self.apps_listbox = tk.Listbox(self.settings_frame, height=4)
        self.apps_listbox.pack(fill='x', padx=20, pady=2)
        ttk.Button(
            self.settings_frame,
            text="Удалить выбранное приложение",
            command=self.remove_selected_app
        ).pack(pady=2, fill='x', padx=20)

        # Обновляем списки при открытии вкладки
        self.refresh_games_listbox()
        self.refresh_apps_listbox()

    def refresh_games_listbox(self):
        """Обновляет список игр в Listbox для удаления."""
        self.games_listbox.delete(0, tk.END)
        for game in self.games_data:
            self.games_listbox.insert(tk.END, game["name"])

    def refresh_apps_listbox(self):
        """Обновляет список приложений в Listbox для удаления."""
        self.apps_listbox.delete(0, tk.END)
        for app in self.apps_data:
            self.apps_listbox.insert(tk.END, app["name"])

    def remove_selected_game(self):
        """Удаляет выбранную игру из списка."""
        selection = self.games_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для удаления!")
            return

        index = selection[0]
        name_to_remove = self.games_listbox.get(index)
        self.games_data = [game for game in self.games_data if game["name"] != name_to_remove]
        self.refresh_games_list()
        self.refresh_games_listbox()
        messagebox.showinfo("Успех", f"Игра '{name_to_remove}' удалена!")

    def remove_selected_app(self):
        """Удаляет выбранное приложение из списка."""
        selection = self.apps_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите приложение для удаления!")
            return

        index = selection[0]
        name_to_remove = self.apps_listbox.get(index)
        self.apps_data = [app for app in self.apps_data if app["name"] != name_to_remove]
        self.refresh_apps_list()
        self.refresh_apps_listbox()
        messagebox.showinfo("Успех", f"Приложение '{name_to_remove}' удалено!")

    def add_game(self):
        """Добавляет новую игру с иконкой."""
        name = simpledialog.askstring("Добавление игры", "Название игры:")
        if not name:
            return

        path = simpledialog.askstring("Добавление игры", "Полный путь к исполняемому файлу:")
        if not path or not os.path.exists(path):
            messagebox.showerror("Ошибка", "Неверный путь к игре!")
            return

        # Выбор иконки
        icon_path = filedialog.askopenfilename(
            title="Выберите иконку для игры",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.ico"), ("All files", "*.*")]
        )

        game_entry = {"name": name, "path": path}
        if icon_path:
            game_entry["icon"] = icon_path

        self.games_data.append(game_entry)
        self.refresh_games_list()
        self.refresh_games_listbox()
        messagebox.showinfo("Успех", f"Игра '{name}' добавлена!")

    def add_app(self):
        """Добавляет новое приложение с иконкой."""
        name = simpledialog.askstring("Добавление приложения", "Название приложения:")
        if not name:
            return

        is_web = messagebox.askyesno("Тип приложения", "Это веб‑приложение (открывается в браузере)?")

        app_entry = {"name": name}

        if is_web:
            url = simpledialog.askstring("Добавление приложения", "URL‑адрес:")
            if not url:
                return
            app_entry["url"] = url
        else:
            path = simpledialog.askstring("Добавление приложения", "Полный путь к исполняемому файлу:")
            if not path or not os.path.exists(path):
                messagebox.showerror("Ошибка", "Неверный путь!")
                return
            app_entry["path"] = path

        # Выбор иконки
        icon_path = filedialog.askopenfilename(
            title="Выберите иконку для приложения",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.ico"), ("All files", "*.*")]
        )

        if icon_path:
            app_entry["icon"] = icon_path

        self.apps_data.append(app_entry)
        self.refresh_apps_list()
        self.refresh_apps_listbox()
        messagebox.showinfo("Успех", f"Приложение '{name}' добавлено!")

    def refresh_games_list(self):
        """Обновляет список кнопок игр с иконками."""
        # Очищаем старый список
        for widget in self.games_buttons_frame.winfo_children():
            widget.destroy()

        if not self.games_data:
            ttk.Label(self.games_buttons_frame, text="Нет добавленных игр").pack(pady=10)
            return

        # Создаём кнопки для каждой игры
        for game in self.games_data:
            # Загружаем иконку, если есть
            icon = None
            if "icon" in game and os.path.exists(game["icon"]):
                try:
                    icon_image = tk.PhotoImage(file=game["icon"])
                    # Масштабируем иконку до 20×20 пикселей
                    icon = icon_image.subsample(
                        max(icon_image.width() // 20, 1),
                        max(icon_image.height() // 20, 1)
                    )
                except Exception:
                    pass  # Если не получилось загрузить — используем стандартную кнопку

            btn = ttk.Button(
                self.games_buttons_frame,
                text=game["name"],
                image=icon,
                compound="left",  # Иконка слева от текста
                command=lambda g=game: self.launch_game(g)
            )
            # Сохраняем ссылку на иконку, чтобы она не удалилась сборщиком мусора
            if icon:
                btn.icon = icon
            btn.pack(fill='x', pady=2)

    def refresh_apps_list(self):
        """Обновляет список кнопок приложений с иконками."""
        # Очищаем старый список
        for widget in self.apps_buttons_frame.winfo_children():
            widget.destroy()

        if not self.apps_data:
            ttk.Label(self.apps_buttons_frame, text="Нет добавленных приложений").pack(pady=10)
            return

        # Создаём кнопки для каждого приложения
        for app in self.apps_data:
            # Загружаем иконку, если есть
            icon = None
            if "icon" in app and os.path.exists(app["icon"]):
                    try:
                        icon_image = tk.PhotoImage(file=app["icon"])
                        icon = icon_image.subsample(
                            max(icon_image.width() // 20, 1),
                            max(icon_image.height() // 20, 1)
                        )
                    except Exception:
                        pass  # Игнорируем ошибку — используем стандартную кнопку, если иконка не загрузилась

                    # Масштабируем иконку до 20×20 пикселей
            icon = icon_image.subsample(
                max(icon_image.width() // 20, 1),
                max(icon_image.height() // 20, 1)
            )
            
        btn = ttk.Button(
            self.apps_buttons_frame,
            text=app["name"],
            image=icon,
            compound="left",
            command=lambda a=app: self.launch_app(a)
        )
        # Сохраняем ссылку на иконку
        if icon:
            btn.icon = icon
        btn.pack(fill='x', pady=2)

    def launch_game(self, game):
        """Запускает выбранную игру."""
        if not os.path.exists(game["path"]):
            messagebox.showerror("Ошибка", f"Игра не найдена: {game['name']}\nПроверьте путь.")
            return
        try:
            subprocess.Popen(game["path"])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить {game['name']}: {e}")

    def launch_app(self, app):
        """Запускает выбранное приложение."""
        if "url" in app:  # Если это веб‑приложение
            try:
                import webbrowser
                webbrowser.open(app["url"])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть {app['name']}: {e}")
        else:  # Локальное приложение
            if not os.path.exists(app["path"]):
                messagebox.showerror("Ошибка", f"Приложение не найдено: {app['name']}\nПроверьте путь.")
                return
            try:
                subprocess.Popen(app["path"])
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось запустить {app['name']}: {e}")

    def change_language(self):
        """Меняет язык интерфейса."""
        self.language = self.lang_var.get()
        self.update_ui_text()

    def update_ui_text(self):
        """Обновляет текст элементов интерфейса в соответствии с выбранным языком."""
        if self.language == "ru":
            self.root.title("Матвей пидарас")
            self.notebook.tab(0, text="Игры")
            self.notebook.tab(1, text="Приложения")
            self.notebook.tab(2, text="Настройки")
            self.notebook.tab(3, text="Выйти")

            # Обновляем тексты на вкладке настроек
            for widget in self.settings_frame.winfo_children():
                if isinstance(widget, ttk.Label):
                    current_text = widget.cget("text")
                    if current_text == "Язык интерфейса:":
                        widget.config(text="Язык интерфейса:")
                    elif current_text == "Управление играми":
                        widget.config(text="Управление играми")
                    elif current_text == "Удалить игру:":
                        widget.config(text="Удалить игру:")
                    elif current_text == "Управление приложениями":
                        widget.config(text="Управление приложениями")
                    elif current_text == "Удалить приложение:":
                        widget.config(text="Удалить приложение:")

                    elif isinstance(widget, ttk.Button):
                        current_text = widget.cget("text")
                    if current_text == "Добавить игру":
                        widget.config(text="Добавить игру")
                    elif current_text == "Удалить выбранную игру":
                        widget.config(text="Удалить выбранную игру")
                    elif current_text == "Добавить приложение":
                        widget.config(text="Добавить приложение")
                    elif current_text == "Удалить выбранное приложение":
                        widget.config(text="Удалить выбранное приложение")

        else:  # en
            self.root.title("MatveyPidoruga")
            self.notebook.tab(0, text="Games")
            self.notebook.tab(1, text="Applications")
            self.notebook.tab(2, text="Settings")
            self.notebook.tab(3, text="Exit")

            # Обновляем тексты на вкладке настроек (английский)
            for widget in self.settings_frame.winfo_children():
                if isinstance(widget, ttk.Label):
                    current_text = widget.cget("text")
            if current_text == "Язык интерфейса:":
                widget.config(text="Language:")
            elif current_text == "Управление играми":
                widget.config(text="Manage Games")
            elif current_text == "Удалить игру:":
                widget.config(text="Remove game:")
            elif current_text == "Управление приложениями":
                widget.config(text="Manage Applications")
            elif current_text == "Удалить приложение:":
                widget.config(text="Remove application:")

            elif isinstance(widget, ttk.Button):
                current_text = widget.cget("text")
                if current_text == "Добавить игру":
                    widget.config(text="Add Game")
                elif current_text == "Удалить выбранную игру":
                    widget.config(text="Remove Selected Game")
                elif current_text == "Добавить приложение":
                    widget.config(text="Add Application")
                elif current_text == "Удалить выбранное приложение":
                    widget.config(text="Remove Selected Application")

    def exit_program(self):
        """Закрывает программу."""
        self.save_data()
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
