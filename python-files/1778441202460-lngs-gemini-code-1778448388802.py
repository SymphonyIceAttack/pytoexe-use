import os
import tkinter as tk
from tkinter import font

class RetroLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Retro Launcher")
        
        # Настройки полноэкранного режима
        self.is_fullscreen = True
        self.root.attributes('-fullscreen', self.is_fullscreen)
        self.root.config(bg="#1E1E2E") # Глубокий темный фон
        
        # Папка с играми/программами
        self.games_dir = "games"
        self.ensure_games_directory()
        self.games_list = self.get_games()

        # Настройка шрифтов
        self.title_font = font.Font(family="Helvetica", size=48, weight="bold")
        self.list_font = font.Font(family="Helvetica", size=24)
        
        self.setup_ui()
        self.bind_keys()

    def ensure_games_directory(self):
        """Создает папку для игр, если ее нет."""
        if not os.path.exists(self.games_dir):
            os.makedirs(self.games_dir)

    def get_games(self):
        """Сканирует папку на наличие .exe и .lnk файлов."""
        if not os.path.exists(self.games_dir):
            return []
        
        valid_extensions = ('.exe', '.lnk')
        games = []
        for file in os.listdir(self.games_dir):
            if file.lower().endswith(valid_extensions):
                name = os.path.splitext(file)[0]
                path = os.path.join(self.games_dir, file)
                games.append({"name": name, "path": path})
        
        return sorted(games, key=lambda x: x["name"].lower())

    def setup_ui(self):
        """Создает красивый интерфейс."""
        # Заголовок
        self.lbl_title = tk.Label(
            self.root, 
            text="★ ARCADE LAUNCHER ★", 
            font=self.title_font, 
            bg="#1E1E2E", 
            fg="#F38BA8", # Яркий акцентный цвет
            pady=50
        )
        self.lbl_title.pack(fill=tk.X)

        # Контейнер для списка (центрирование)
        self.frame_list = tk.Frame(self.root, bg="#1E1E2E")
        self.frame_list.pack(expand=True, fill=tk.BOTH, padx=100, pady=20)

        # Список игр
        self.listbox = tk.Listbox(
            self.frame_list,
            font=self.list_font,
            bg="#1E1E2E",
            fg="#CDD6F4",
            selectbackground="#89B4FA",
            selectforeground="#1E1E2E",
            bd=0,
            highlightthickness=0,
            activestyle='none', # Убирает пунктирную рамку при выборе
            justify=tk.CENTER
        )
        self.listbox.pack(expand=True, fill=tk.BOTH)

        # Заполнение списка
        if not self.games_list:
            self.listbox.insert(tk.END, "Папка 'games' пуста. Добавьте .exe файлы.")
            self.listbox.itemconfig(0, fg="#A6ADC8")
        else:
            for game in self.games_list:
                self.listbox.insert(tk.END, game["name"])
            self.listbox.selection_set(0) # Выбираем первый элемент

        # Подсказки внизу экрана
        self.lbl_hints = tk.Label(
            self.root, 
            text="[↑/↓] Навигация   |   [ENTER] Запуск   |   [ESC] Выход", 
            font=("Helvetica", 14), 
            bg="#1E1E2E", 
            fg="#A6ADC8",
            pady=20
        )
        self.lbl_hints.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_keys(self):
        """Привязка клавиш управления."""
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.root.bind("<Return>", self.launch_game)
        
        # Для удобства, если список пуст, не даем использовать Enter
        if not self.games_list:
            self.root.unbind("<Return>")

    def launch_game(self, event=None):
        """Запускает выбранную программу."""
        selection = self.listbox.curselection()
        if selection and self.games_list:
            index = selection[0]
            game_path = self.games_list[index]["path"]
            
            # Анимация цвета при запуске (визуальный отклик)
            self.listbox.config(selectbackground="#A6E3A1")
            self.root.update()
            self.root.after(150, lambda: self.listbox.config(selectbackground="#89B4FA"))
            
            # Запуск файла средствами ОС (Windows)
            try:
                os.startfile(os.path.abspath(game_path))
            except Exception as e:
                print(f"Ошибка запуска: {e}")

    def exit_fullscreen(self, event=None):
        """Выход из приложения по ESC."""
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RetroLauncher(root)
    # Прячем курсор мыши для большего погружения (как в консолях)
    root.config(cursor="none")
    root.mainloop()