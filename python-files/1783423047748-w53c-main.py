Python 3.13.14 (tags/v3.13.14:fd17997, Jun 10 2026, 13:03:48) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> import tkinter as tk
... from tkinter import filedialog, messagebox, ttk
... from PIL import Image, ImageTk
... import os
... import time
... 
... class ImageOrganizer:
...     def __init__(self, root):
...         self.root = root
...         self.root.title("Органайзер изображений BMP/JPG")
... 
...         # Инициализация данных
...         self.images = []  # список кортежей: (путь, имя файла, дата, размер)
...         self.filtered_images = []  # отфильтрованный список изображений
...         self.current_image_index = None  # индекс текущего отображаемого изображения
... 
...         # --- Верхняя панель с часами ---
...         self.clock_label = tk.Label(self.root, font=('Arial', 14))
...         self.clock_label.pack(side=tk.TOP, pady=5)
...         self.update_clock()
... 
...         # --- Панель поиска ---
...         search_frame = tk.Frame(self.root)
...         search_frame.pack(pady=5, fill=tk.X, padx=10)
...         tk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
...         self.search_entry = tk.Entry(search_frame)
...         self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
...         self.search_entry.bind("<KeyRelease>", self.apply_filter)
... 
...         # --- Панель сортировки ---
...         sort_frame = tk.Frame(self.root)
...         sort_frame.pack(pady=5, fill=tk.X, padx=10)
...         tk.Label(sort_frame, text="Сортировать по:").pack(side=tk.LEFT)
...         self.sort_var = tk.StringVar(value="name")
...         sort_options = [("Имя", "name"), ("Дата", "date"), ("Размер", "size")]
...         for text, value in sort_options:
            tk.Radiobutton(sort_frame, text=text, variable=self.sort_var, value=value, command=self.sort_images).pack(side=tk.LEFT)

        # --- Панель кнопок ---
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        self.load_btn = tk.Button(btn_frame, text="Загрузить папку", command=self.load_folder)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = tk.Button(btn_frame, text="Следующее изображение", command=self.show_next_image)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # --- Область предпросмотра ---
        self.preview_label = tk.Label(self.root, bd=2, relief=tk.SUNKEN)
        self.preview_label.pack(pady=10)

        # --- Дерево папок (Treeview) ---
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        self.tree = ttk.Treeview(tree_frame)
        self.tree.heading('#0', text='Папки и файлы', anchor='w')
        self.tree.pack(side=tk.LEFT, fill=tk.Y)

        # Скроллер для дерева
        tree_scroll = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Связываем выбор в дереве с функцией
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        # --- Обновление часов ---
        self.update_clock()

    def update_clock(self):
        """Обновление отображения времени каждую секунду"""
        now = time.strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def load_folder(self):
        """Загрузка папки и сбор изображений в ней"""
        folder = filedialog.askdirectory(title="Выберите папку с изображениями")
        if not folder:
            return

        # Очистка текущих данных
        self.images.clear()
        self.filtered_images.clear()
        self.current_image_index = None
        self.tree.delete(*self.tree.get_children())

        # Проход по папкам и файлам
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.bmp', '.jpg', '.jpeg')):
                    full_path = os.path.join(root_dir, file)
                    try:
                        stat = os.stat(full_path)
                        size = stat.st_size
                        mtime = stat.st_mtime
                        self.images.append((full_path, file, mtime, size))
                    except Exception as e:
                        print(f"Ошибка при чтении файла {full_path}: {e}")

        # Построение структуры папок
        self.build_tree(folder)

        # Отображение всех изображений по умолчанию
        self.apply_filter()

    def build_tree(self, root_folder):
        """Создание дерева папок и файлов"""
        self.tree.delete(*self.tree.get_children())  # очищаем дерево
        root_node = self.tree.insert('', 'end', text=os.path.basename(root_folder), open=True, values=[root_folder])
        self._add_subfolders(root_node, root_folder)

    def _add_subfolders(self, parent_node, folder):
        """Рекурсивное добавление папок и файлов"""
        try:
            for entry in os.scandir(folder):
                if entry.is_dir():
                    node = self.tree.insert(parent_node, 'end', text=entry.name, open=False, values=[entry.path])
                    self._add_subfolders(node, entry.path)
                else:
                    if entry.name.lower().endswith(('.bmp', '.jpg', '.jpeg')):
                        self.tree.insert(parent_node, 'end', text=entry.name, values=[entry.path])
        except PermissionError:
            # Обработка ошибок доступа
            pass

    def on_tree_select(self, event):
        """Обработка выбора элемента в дереве"""
        selected_items = self.tree.selection()
        if selected_items:
            path = self.tree.item(selected_items[0], 'values')[0]
            if os.path.isfile(path):
                self.show_image(path)

    def show_image(self, path):
        """Отображение выбранного изображения"""
        try:
            img = Image.open(path)
            max_size = (400, 300)
            img.thumbnail(max_size)
            self.tk_img = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.tk_img)
            # Обновляем текущий индекс для навигации
            for idx, img_tuple in enumerate(self.images):
                if img_tuple[0] == path:
                    self.current_image_index = idx
                    break
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение:\n{e}")

    def show_next_image(self):
        """Показать следующее изображение из фильтрованного списка"""
        if not self.filtered_images:
            messagebox.showinfo("Информация", "Нет изображений для отображения")
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.filtered_images)
        self.show_image(self.filtered_images[self.current_image_index][0])

    def apply_filter(self, event=None):
        """Фильтрация изображений по поисковому запросу"""
        query = self.search_entry.get().lower()
        self.filtered_images = [
            img for img in self.images
            if query in img[1].lower() or query in os.path.basename(img[0]).lower()
        ]
        self.sort_images()  # сортируем по выбранному критерию
        if self.filtered_images:
            self.current_image_index = 0
            self.show_image(self.filtered_images[0][0])
        else:
            self.preview_label.config(image='')

    def sort_images(self):
        """Сортировка фильтрованных изображений"""
        key = self.sort_var.get()
        if key == "name":
            self.filtered_images.sort(key=lambda x: x[1].lower())
        elif key == "date":
            self.filtered_images.sort(key=lambda x: x[2])
        elif key == "size":
            self.filtered_images.sort(key=lambda x: x[3])
        # Обновляем отображение
        if self.filtered_images:
            self.current_image_index = 0
            self.show_image(self.filtered_images[0][0])

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageOrganizer(root)
