import tkinter as tk
from tkinter import messagebox
import os

class PSPLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PSP XMB Launcher")
        
        # 1. Настройка полноэкранного режима
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#050505") # Очень тёмный фон

        # 2. Переменные для навигации
        self.shortcuts = []
        self.shortcut_widgets = []
        self.current_index = 0
        
        # Размеры для "эффекта XMB"
        self.normal_width = 16
        self.normal_height = 8
        self.selected_width = 24  # Выбранный элемент больше
        self.selected_height = 10
        self.normal_font = ("Segoe UI", 12)
        self.selected_font = ("Segoe UI", 16, "bold")

        # 3. Элементы интерфейса
        # Заголовок (верхний левый угол, как часы/дата на PSP)
        self.header = tk.Label(
            root, text="System Menu", font=("Segoe UI", 18),
            bg="#050505", fg="#aaaaaa", anchor="nw"
        )
        self.header.pack(anchor="nw", padx=30, pady=20)

        # Контейнер для горизонтального меню
        self.menu_frame = tk.Frame(root, bg="#050505")
        self.menu_frame.pack(expand=True) # Центрируем по вертикали

        # 4. Загрузка данных
        self.load_shortcuts()
        
        if not self.shortcuts:
            # Если рабочий стол пуст
            tk.Label(self.menu_frame, text="Нет ярлыков", fg="white", bg="#050505", font=("Segoe UI", 18)).pack()
            self.root.bind("<Escape>", lambda e: self.root.destroy())
            return

        # 5. Отрисовка меню
        self.draw_menu()

        # 6. Привязка клавиш (Управление в стиле PSP)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Return>", self.launch_current) # Enter = 'Cross' (X)
        self.root.bind("<space>", self.launch_current)
        
        # Кнопки выхода
        self.root.bind("<Escape>", lambda e: self.root.destroy()) # 'Select'
        self.root.bind("t", lambda e: self.root.destroy())       # 'Triangle' (T)

    def load_shortcuts(self):
        """Сканирует рабочий стол для получения списка ярлыков."""
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        public_desktop = os.path.join(os.environ['PUBLIC'], 'Desktop')
        paths = [desktop, public_desktop]
        
        for path in paths:
            if not os.path.exists(path): continue
            for item in os.listdir(path):
                if item.lower() == 'desktop.ini': continue
                
                full_path = os.path.join(path, item)
                name = os.path.splitext(item)[0]
                
                # Упрощенная категория (все игры/приложения)
                icon_char = "🎮" 
                
                self.shortcuts.append({'name': name, 'path': full_path, 'icon': icon_char})

    def draw_menu(self):
        """Создает виджеты для каждого ярлыка в горизонтальную линию."""
        # Очищаем фрейм перед отрисовкой
        for widget in self.menu_frame.winfo_children():
            widget.destroy()
        self.shortcut_widgets = []

        for i, sc in enumerate(self.shortcuts):
            # Текст плитки: Иконка + Имя
            display_text = f"{sc['icon']}\n{sc['name']}"
            if i == self.current_index:
                 # Отображаем только имя выбранного файла, как в XMB
                 pass
            
            # Создаем контейнер для каждого элемента (для эффекта масштабирования)
            item_frame = tk.Frame(self.menu_frame, bg="#050505", padx=20)
            item_frame.pack(side="left")

            btn = tk.Button(
                item_frame, 
                text=display_text,
                font=self.normal_font,
                fg="#ffffff", 
                bg="#1a1a1a",  # Тёмно-серый
                activebackground="#ffffff",
                activeforeground="#000000",
                width=self.normal_width, 
                height=self.normal_height,
                relief="flat",
                command=lambda p=sc['path']: self.launch(p)
            )
            # Наведение мыши (для поддержки мыши)
            btn.bind("<Enter>", lambda e, index=i: self.select_index(index))
            
            btn.pack()
            self.shortcut_widgets.append(btn)

        # Выделяем первый элемент
        self.update_selection()

    def update_selection(self):
        """Визуально выделяет текущий выбранный элемент (увеличивает его)."""
        for i, btn in enumerate(self.shortcut_widgets):
            if i == self.current_index:
                # Выбранный элемент
                btn.configure(
                    bg="#ffffff",       # Белый фон
                    fg="#000000",       # Чёрный текст
                    font=self.selected_font,
                    width=self.selected_width,
                    height=self.selected_height,
                    activebackground="#ffffff"
                )
            else:
                # Обычный элемент
                btn.configure(
                    bg="#1a1a1a",       # Тёмно-серый фон
                    fg="#ffffff",       # Белый текст
                    font=self.normal_font,
                    width=self.normal_width,
                    height=self.normal_height,
                    activebackground="#ffffff"
                )

    def select_index(self, index):
        """Устанавливает индекс выбора при наведении мыши."""
        self.current_index = index
        self.update_selection()

    def move_right(self, event):
        """Циклическая навигация вправо."""
        if self.shortcuts:
            self.current_index = (self.current_index + 1) % len(self.shortcuts)
            self.update_selection()

    def move_left(self, event):
        """Циклическая навигация влево."""
        if self.shortcuts:
            self.current_index = (self.current_index - 1) % len(self.shortcuts)
            self.update_selection()

    def launch_current(self, event=None):
        """Запускает текущий выбранный файл."""
        if self.shortcuts:
            self.launch(self.shortcuts[self.current_index]['path'])

    def launch(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить:\n{path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PSPLauncher(root)
    root.mainloop()