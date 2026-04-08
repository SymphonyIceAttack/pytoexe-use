import os
import threading
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image
from io import BytesIO

# ---------------------- Основные функции обработки ----------------------
def resize_if_large(image, max_dim):
    """Уменьшает изображение, если большая сторона превышает max_dim."""
    width, height = image.size
    if width <= max_dim and height <= max_dim:
        return image
    scale = max_dim / max(width, height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    return image.resize((new_width, new_height), Image.LANCZOS)

def compress_image_to_target(filepath, target_kb, max_dim, log_callback):
    """
    Обрабатывает одно изображение:
    - уменьшает размер при необходимости,
    - сжимает качеством до целевого размера.
    Возвращает True при успехе, иначе False.
    """
    original_size_kb = os.path.getsize(filepath) / 1024
    try:
        img = Image.open(filepath)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
    except Exception as e:
        log_callback(f"✗ Ошибка открытия {os.path.basename(filepath)}: {e}")
        return False

    # Изменяем размер
    old_size = img.size
    img = resize_if_large(img, max_dim)
    new_size = img.size
    if old_size != new_size:
        log_callback(f"  Изменён размер {os.path.basename(filepath)}: {old_size[0]}x{old_size[1]} → {new_size[0]}x{new_size[1]}")

    # Определяем формат сохранения
    ext = os.path.splitext(filepath)[1].lower()
    save_format = 'WEBP' if ext == '.webp' else 'JPEG'

    # Пробуем сразу сохранить с качеством 90, чтобы оценить размер
    try:
        buffer = BytesIO()
        if save_format == 'JPEG':
            img.save(buffer, format='JPEG', quality=90, optimize=True)
        else:
            img.save(buffer, format='WEBP', quality=90, method=6)
        if buffer.tell() / 1024 <= target_kb:
            # Уже подходит, сохраняем
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            new_size_kb = os.path.getsize(filepath) / 1024
            log_callback(f"✓ {os.path.basename(filepath)}: {original_size_kb:.1f} КБ → {new_size_kb:.1f} КБ (качество 90)")
            return True
    except:
        pass

    # Бинарный поиск по качеству
    low, high = 20, 95
    best_quality = None
    best_size = None

    while low <= high:
        quality = (low + high) // 2
        try:
            buffer = BytesIO()
            if save_format == 'JPEG':
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                img.save(buffer, format='WEBP', quality=quality, method=6)
            size_kb = buffer.tell() / 1024
            if size_kb <= target_kb:
                best_quality = quality
                best_size = size_kb
                high = quality - 1
            else:
                low = quality + 1
        except Exception as e:
            log_callback(f"✗ Ошибка сжатия {os.path.basename(filepath)}: {e}")
            return False

    if best_quality is not None:
        try:
            buffer = BytesIO()
            if save_format == 'JPEG':
                img.save(buffer, format='JPEG', quality=best_quality, optimize=True)
            else:
                img.save(buffer, format='WEBP', quality=best_quality, method=6)
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            new_size_kb = os.path.getsize(filepath) / 1024
            log_callback(f"✓ {os.path.basename(filepath)}: {original_size_kb:.1f} КБ → {new_size_kb:.1f} КБ (качество {best_quality})")
            return True
        except Exception as e:
            log_callback(f"✗ Ошибка сохранения {os.path.basename(filepath)}: {e}")
            return False
    else:
        log_callback(f"✗ {os.path.basename(filepath)}: не удалось сжать до {target_kb} КБ")
        return False

def process_folder(folder_path, target_kb, max_dim, log_callback, done_callback):
    """Обрабатывает все изображения в папке рекурсивно."""
    supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    files = []
    for root, _, filenames in os.walk(folder_path):
        for f in filenames:
            if os.path.splitext(f)[1].lower() in supported_formats:
                files.append(os.path.join(root, f))

    if not files:
        log_callback("Не найдено изображений для обработки.")
        done_callback()
        return

    log_callback(f"Найдено {len(files)} изображений. Начинаем обработку...")
    success = 0
    for i, filepath in enumerate(files, 1):
        log_callback(f"[{i}/{len(files)}] Обработка {os.path.basename(filepath)}...")
        if compress_image_to_target(filepath, target_kb, max_dim, log_callback):
            success += 1
    log_callback(f"Готово! Обработано {success} из {len(files)} изображений.")
    done_callback()

# ---------------------- GUI на tkinter ----------------------
class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сжатие изображений")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Выбор папки
        frame_folder = LabelFrame(root, text="Папка с изображениями", padx=5, pady=5)
        frame_folder.pack(fill="x", padx=10, pady=5)

        self.folder_path = StringVar()
        entry_folder = Entry(frame_folder, textvariable=self.folder_path, width=60)
        entry_folder.pack(side=LEFT, padx=(0,5), fill="x", expand=True)

        btn_browse = Button(frame_folder, text="Выбрать папку", command=self.browse_folder)
        btn_browse.pack(side=RIGHT)

        # Параметры
        frame_params = LabelFrame(root, text="Параметры", padx=5, pady=5)
        frame_params.pack(fill="x", padx=10, pady=5)

        Label(frame_params, text="Целевой размер (КБ):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.target_kb = IntVar(value=100)
        Entry(frame_params, textvariable=self.target_kb, width=10).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        Label(frame_params, text="Макс. сторона (пиксели):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.max_dim = IntVar(value=1000)
        Entry(frame_params, textvariable=self.max_dim, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Кнопка запуска
        btn_start = Button(root, text="Начать обработку", command=self.start_processing, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        btn_start.pack(pady=10)

        # Лог-область
        frame_log = LabelFrame(root, text="Лог", padx=5, pady=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(frame_log, wrap=WORD, height=20)
        self.log_area.pack(fill="both", expand=True)

        # Статус
        self.status_label = Label(root, text="Готов", bd=1, relief=SUNKEN, anchor=W)
        self.status_label.pack(side=BOTTOM, fill="x")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def log(self, message):
        """Безопасный вывод в лог из любого потока."""
        def _append():
            self.log_area.insert(END, message + "\n")
            self.log_area.see(END)
            self.root.update_idletasks()
        self.root.after(0, _append)

    def set_status(self, text):
        def _set():
            self.status_label.config(text=text)
        self.root.after(0, _set)

    def start_processing(self):
        folder = self.folder_path.get().strip()
        if not folder:
            messagebox.showerror("Ошибка", "Выберите папку!")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Ошибка", "Указанная папка не существует!")
            return

        target = self.target_kb.get()
        if target <= 0:
            messagebox.showerror("Ошибка", "Целевой размер должен быть положительным числом!")
            return
        max_dim = self.max_dim.get()
        if max_dim <= 0:
            messagebox.showerror("Ошибка", "Максимальная сторона должна быть положительным числом!")
            return

        # Очищаем лог и блокируем кнопку
        self.log_area.delete(1.0, END)
        self.log("Запуск обработки...")
        self.set_status("Обработка...")
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._process, args=(folder, target, max_dim), daemon=True)
        thread.start()

    def _process(self, folder, target, max_dim):
        def log_cb(msg):
            self.log(msg)
        def done_cb():
            self.set_status("Готово")
        try:
            process_folder(folder, target, max_dim, log_cb, done_cb)
        except Exception as e:
            self.log(f"Критическая ошибка: {e}")
            self.set_status("Ошибка")
            done_cb()

if __name__ == "__main__":
    root = Tk()
    app = ImageCompressorApp(root)
    root.mainloop()