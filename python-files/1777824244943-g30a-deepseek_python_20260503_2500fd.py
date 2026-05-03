import os
import tkinter as tk
from tkinter import font, messagebox
import subprocess

# ------------------ Класс лаунчера ------------------
class ConsoleLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Game Launcher")
        self.root.attributes('-fullscreen', True)          # полноэкранный режим
        self.root.configure(bg='#0a0f1f')                  # тёмный фон как у консолей
        
        # Привязка клавиш
        self.root.bind('<Escape>', self.exit_fullscreen)    # Esc - выход из полноэкранного режима
        self.root.bind('<F11>', self.toggle_fullscreen)     # F11 - переключить полноэкранный режим
        
        # Получаем путь к рабочему столу
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Сканируем ярлыки
        self.shortcuts = self.get_desktop_shortcuts()
        
        if not self.shortcuts:
            messagebox.showwarning("Нет ярлыков", "На рабочем столе не найдено ярлыков (.lnk)")
            self.root.quit()
            return
        
        # Создаём основной фрейм с прокруткой
        self.create_scrollable_grid()
        
        # Заполняем сетку плитками
        self.populate_grid()
        
        self.root.mainloop()
    
    def get_desktop_shortcuts(self):
        """Возвращает список кортежей (путь_к_ярлыку, отображаемое_имя) для всех .lnk на рабочем столе"""
        shortcuts = []
        try:
            for item in os.listdir(self.desktop_path):
                if item.lower().endswith('.lnk'):
                    full_path = os.path.join(self.desktop_path, item)
                    # Отображаемое имя = имя файла без расширения .lnk
                    display_name = os.path.splitext(item)[0]
                    shortcuts.append((full_path, display_name))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать рабочий стол:\n{e}")
        # Сортируем по имени для удобства
        shortcuts.sort(key=lambda x: x[1].lower())
        return shortcuts
    
    def create_scrollable_grid(self):
        """Создаёт область с полосой прокрутки для размещения плиток"""
        # Контейнер для прокрутки
        self.canvas = tk.Canvas(self.root, bg='#0a0f1f', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#0a0f1f')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Упаковка
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Прокрутка колёсиком мыши
        self.bind_mousewheel()
    
    def bind_mousewheel(self):
        """Привязывает прокрутку колёсиком мыши (работает и для Windows, и для других ОС)"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def populate_grid(self):
        """Размещает кнопки-плитки в сетке (по 4 колонки, адаптивно)"""
        # Определяем количество колонок в зависимости от ширины экрана
        screen_width = self.root.winfo_screenwidth()
        columns = max(4, screen_width // 280)   # минимум 4, но можно больше, если экран широкий
        columns = min(columns, 8)               # ограничиваем 8 колонками
        
        # Стили для кнопок
        button_font = font.Font(family="Segoe UI", size=12, weight="bold")
        tile_width = 220
        tile_height = 100
        
        row = 0
        col = 0
        for idx, (shortcut_path, display_name) in enumerate(self.shortcuts):
            # Создаём рамку для плитки (эффект карточки)
            tile_frame = tk.Frame(
                self.scrollable_frame,
                bg='#1e2a3a',
                relief='raised',
                bd=2,
                highlightbackground='#3a506c',
                highlightthickness=1
            )
            tile_frame.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            tile_frame.grid_propagate(False)
            tile_frame.config(width=tile_width, height=tile_height)
            
            # Внутри плитки: иконка (эмодзи/текст) и название
            icon_label = tk.Label(
                tile_frame, text="🎮",
                font=("Segoe UI", 32), bg='#1e2a3a', fg='#f0a500'
            )
            icon_label.pack(pady=(10, 0))
            
            name_label = tk.Label(
                tile_frame, text=display_name,
                font=button_font, bg='#1e2a3a', fg='white',
                wraplength=tile_width-20
            )
            name_label.pack(pady=(5, 10))
            
            # Клик по плитке запускает ярлык
            def launch(event, path=shortcut_path):
                self.launch_shortcut(path)
            
            tile_frame.bind("<Button-1>", launch)
            icon_label.bind("<Button-1>", launch)
            name_label.bind("<Button-1>", launch)
            
            # Эффект наведения
            def on_enter(e, f=tile_frame):
                f.config(bg='#2a3e55', highlightbackground='#f0a500')
                f.winfo_children()[0].config(bg='#2a3e55')   # icon_label
                f.winfo_children()[1].config(bg='#2a3e55')   # name_label
            def on_leave(e, f=tile_frame):
                f.config(bg='#1e2a3a', highlightbackground='#3a506c')
                f.winfo_children()[0].config(bg='#1e2a3a')
                f.winfo_children()[1].config(bg='#1e2a3a')
            
            tile_frame.bind("<Enter>", on_enter)
            tile_frame.bind("<Leave>", on_leave)
            
            # Обновляем позицию
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Настройка веса колонок для адаптивности
        for c in range(columns):
            self.scrollable_frame.columnconfigure(c, weight=1)
    
    def launch_shortcut(self, shortcut_path):
        """Запускает ярлык как при двойном щелчке мыши"""
        try:
            os.startfile(shortcut_path)
        except Exception as e:
            messagebox.showerror("Ошибка запуска", f"Не удалось запустить:\n{shortcut_path}\n\n{e}")
    
    def exit_fullscreen(self, event=None):
        """Выход из полноэкранного режима (но не закрытие окна)"""
        self.root.attributes('-fullscreen', False)
    
    def toggle_fullscreen(self, event=None):
        """Переключение полноэкранного режима"""
        is_full = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_full)


# ------------------ Точка входа ------------------
if __name__ == "__main__":
    app = ConsoleLauncher()