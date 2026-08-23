import tkinter as tk
from tkinter import filedialog, scrolledtext, Listbox, SINGLE
from PIL import Image, ImageTk
import os

class SongKeeperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Хранилище стихов и песен")
        self.root.geometry("900x700")
        self.root.configure(bg='#2b2b2b')

        # Переменные для хранения данных
        self.images = []  # Список путей к загруженным изображениям
        self.image_refs = []  # Ссылки на фото для предотвращения сборки мусора
        self.current_image = None

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Основной контейнер (разделение на левую панель и основную область)
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель (список загруженных фото)
        left_panel = tk.Frame(main_frame, bg='#3c3f41', width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="Загруженные файлы", fg='white', bg='#3c3f41', font=('Arial', 12, 'bold')).pack(pady=5)

        self.listbox = Listbox(left_panel, bg='#4a4d4f', fg='white', selectmode=SINGLE, font=('Arial', 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_image)

        btn_load = tk.Button(left_panel, text="Загрузить фото", command=self.load_images, bg='#5a8c5a', fg='white', font=('Arial', 10, 'bold'))
        btn_load.pack(pady=5, padx=5, fill=tk.X)

        btn_clear = tk.Button(left_panel, text="Очистить список", command=self.clear_all, bg='#8c5a5a', fg='white', font=('Arial', 10, 'bold'))
        btn_clear.pack(pady=5, padx=5, fill=tk.X)

        # Правая область (отображение фото, аккордов и текста)
        right_panel = tk.Frame(main_frame, bg='#2b2b2b')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Область для фото
        self.image_label = tk.Label(right_panel, bg='#2b2b2b', relief=tk.SUNKEN, bd=2)
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.image_label.bind('<Double-Button-1>', self.open_fullscreen_image)

        # Строка для аккордов (полупрозрачная) - над текстом
        chords_frame = tk.Frame(right_panel, bg='#2b2b2b')
        chords_frame.pack(fill=tk.X, pady=(0, 5))

        tk.Label(chords_frame, text="Аккорды:", fg='#aaaaaa', bg='#2b2b2b', font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        # Эффект "полупрозрачности" за счет светлого фона и альфа-канала (имитация)
        self.chords_entry = tk.Entry(chords_frame, font=('Arial', 12, 'bold'), 
                                     bg='#4a4d4f', fg='#ffcc66', 
                                     relief=tk.GROOVE, bd=2)
        self.chords_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Область для текста (под аккордами)
        self.text_area = scrolledtext.ScrolledText(right_panel, wrap=tk.WORD, 
                                                   font=('Arial', 12), 
                                                   bg='#3c3f41', fg='#e0e0e0',
                                                   insertbackground='white',
                                                   height=10)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Статус бар
        self.status_label = tk.Label(self.root, text="Готов к работе", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='#3c3f41', fg='#cccccc')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_images(self):
        files = filedialog.askopenfilenames(
            title="Выберите фотографии",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if not files:
            return

        for file_path in files:
            if file_path not in self.images:
                self.images.append(file_path)
                # Добавляем только имя файла в список
                self.listbox.insert(tk.END, os.path.basename(file_path))
        
        self.status_label.config(text=f"Загружено {len(self.images)} файлов")
        
        # Если ничего не выбрано, выбираем первый
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
            self.on_select_image(None)

    def on_select_image(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        file_path = self.images[index]
        
        try:
            # Открываем и изменяем размер изображения для отображения в Label
            img = Image.open(file_path)
            # Получаем размеры Label
            label_width = self.image_label.winfo_width() if self.image_label.winfo_width() > 10 else 400
            label_height = self.image_label.winfo_height() if self.image_label.winfo_height() > 10 else 300
            
            # Сохраняем пропорции
            img.thumbnail((label_width, label_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Сохраняем ссылку
            self.current_image = file_path
            self.status_label.config(text=f"Открыт: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_label.config(text=f"Ошибка загрузки: {str(e)}")

    def open_fullscreen_image(self, event):
        """Открывает текущее фото в отдельном увеличенном окне"""
        if not self.current_image:
            return
        
        # Создаем новое окно
        top = tk.Toplevel(self.root)
        top.title(f"Просмотр: {os.path.basename(self.current_image)}")
        top.geometry("800x600")
        top.configure(bg='black')
        
        # Загружаем изображение без ограничений
        img = Image.open(self.current_image)
        
        # Получаем размеры экрана для адаптации
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        
        # Изменяем размер, чтобы влезло в окно с учетом полей
        max_width = screen_width - 100
        max_height = screen_height - 100
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(top, image=photo, bg='black')
        label.pack(fill=tk.BOTH, expand=True)
        label.image = photo  # Сохраняем ссылку
        
        # Кнопка закрыть
        btn_close = tk.Button(top, text="Закрыть", command=top.destroy, bg='red', fg='white', font=('Arial', 10, 'bold'))
        btn_close.pack(pady=10)

    def clear_all(self):
        """Очищает все: список, фото, текст и аккорды"""
        self.listbox.delete(0, tk.END)
        self.images.clear()
        self.image_refs.clear()
        self.image_label.config(image='')
        self.image_label.image = None
        self.text_area.delete('1.0', tk.END)
        self.chords_entry.delete(0, tk.END)
        self.current_image = None
        self.status_label.config(text="Список очищен")

if __name__ == "__main__":
    root = tk.Tk()
    app = SongKeeperApp(root)
    root.mainloop()