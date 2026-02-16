Python 3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import re
import threading
import queue


class TocUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обновление Interface версии в .toc файлах")
        self.root.resizable(True, True)

        # Переменные для хранения введённых данных
        self.folder_path = tk.StringVar(value=os.getcwd())
        self.interface_version = tk.StringVar(value="120000")
        self.add_if_missing = tk.BooleanVar(value=True)

        # Очередь для обмена сообщениями между потоком и GUI
        self.msg_queue = queue.Queue()
        self.worker_thread = None
        self.is_running = False

        self.create_widgets()
        self.process_queue()  # начинаем следить за очередью

    def create_widgets(self):
        # Строка выбора папки
        tk.Label(self.root, text="Папка с аддонами:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Обзор", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=5)

        # Поле для версии интерфейса
        tk.Label(self.root, text="Версия интерфейса:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.interface_version, width=20).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # Опция добавлять отсутствующую директиву
        tk.Checkbutton(self.root, text="Добавлять директиву, если отсутствует",
                       variable=self.add_if_missing).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Кнопка запуска
        self.run_button = tk.Button(self.root, text="Обновить все .toc файлы",
                                    command=self.start_update, bg="#4CAF50", fg="white")
        self.run_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Область лога с прокруткой
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20, state='normal')
        self.log_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        # Кнопка очистки лога
        tk.Button(self.root, text="Очистить лог", command=self.clear_log).grid(row=5, column=0, pady=5)

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)

    def clear_log(self):
        self.log_text.delete('1.0', tk.END)

    def log_message(self, message):
        """Добавляет сообщение в лог и прокручивает к последней строке."""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)

    def process_queue(self):
        """Периодически проверяет очередь и выводит сообщения из рабочего потока."""
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                self.log_message(msg)
        except queue.Empty:
            pass

        # Если поток завершился – разблокируем кнопку и показываем уведомление
        if self.worker_thread is not None and not self.worker_thread.is_alive():
            self.worker_thread = None
            self.is_running = False
            self.run_button.config(state='normal')
            messagebox.showinfo("Завершено", "Обновление файлов завершено!")

        # Проверяем очередь каждые 100 мс
        self.root.after(100, self.process_queue)

    def start_update(self):
        if self.is_running:
            return

        folder = self.folder_path.get()
        if not os.path.isdir(folder):
            messagebox.showerror("Ошибка", "Указанная папка не существует или не является папкой.")
            return

        version = self.interface_version.get().strip()
        if not version.isdigit():
            messagebox.showerror("Ошибка", "Версия интерфейса должна быть числом (например, 120000).")
            return

        self.is_running = True
        self.run_button.config(state='disabled')
        self.clear_log()
        self.log_message("Поиск .toc файлов...")

        # Запускаем обработку в отдельном потоке
        self.worker_thread = threading.Thread(
            target=self.update_toc_files,
            args=(folder, version, self.add_if_missing.get(), self.msg_queue)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()

    @staticmethod
    def update_toc_files(root_dir, version, add_if_missing, queue):
        """Выполняет обновление файлов и кладёт сообщения в очередь."""
        # Собираем все .toc файлы рекурсивно
        toc_files = []
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.toc'):
                    toc_files.append(os.path.join(dirpath, filename))

        queue.put(f"Найдено .toc файлов: {len(toc_files)}")
        if not toc_files:
            queue.put("Нет файлов для обработки.")
            return

        # Регулярное выражение для поиска директивы Interface
        interface_pattern = re.compile(r'^(##\s*Interface:)\s*(.*)', re.IGNORECASE)

        for filepath in toc_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                queue.put(f"Ошибка чтения {os.path.basename(filepath)}: {e}")
                continue

            modified = False
            found = False

            for i, line in enumerate(lines):
                match = interface_pattern.match(line)
                if match:
                    found = True
                    values_part = match.group(2).strip()
                    # Разбиваем существующие значения по запятой
                    current_values = [v.strip() for v in values_part.split(',') if v.strip()]

...                     if version not in current_values:
...                         # Добавляем новую версию в начало списка
...                         new_values = [version] + current_values
...                         new_line = f"## Interface: {', '.join(new_values)}\n"
...                         lines[i] = new_line
...                         modified = True
...                         queue.put(f"Обновлено: {os.path.basename(filepath)} (добавлен {version})")
...                     else:
...                         queue.put(f"Пропущено: {os.path.basename(filepath)} (уже содержит {version})")
...                     break  # обрабатываем только первую директиву
... 
...             if not found and add_if_missing:
...                 lines.append(f"## Interface: {version}\n")
...                 modified = True
...                 queue.put(f"Добавлена строка: {os.path.basename(filepath)}")
...             elif not found and not add_if_missing:
...                 queue.put(f"Пропущено: {os.path.basename(filepath)} (нет директивы Interface)")
... 
...             if modified:
...                 try:
...                     with open(filepath, 'w', encoding='utf-8') as f:
...                         f.writelines(lines)
...                 except Exception as e:
...                     queue.put(f"Ошибка записи {os.path.basename(filepath)}: {e}")
... 
...         queue.put("Обработка завершена.")
... 
... 
... def main():
...     root = tk.Tk()
...     app = TocUpdaterApp(root)
...     root.mainloop()
... 
... 
... if __name__ == "__main__":
