import os
import shutil
import csv
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

class FileDistributorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Распределитель файлов v1.0")
        self.root.geometry("800x500")

        # Установка иконки (опционально)
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

        self.csv_path = tk.StringVar()
        self.source_folder = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # CSV файл
        ttk.Label(main_frame, text="CSV файл:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.csv_path, width=70).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Обзор", command=self.select_csv).grid(row=0, column=2, padx=5)

        # Папка с файлами
        ttk.Label(main_frame, text="Папка с файлами:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.source_folder, width=70).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(main_frame, text="Обзор", command=self.select_source_folder).grid(row=1, column=2, padx=5)

        # Кнопка распределения
        self.distribute_btn = ttk.Button(main_frame, text="РАСПРЕДЕЛИТЬ", command=self.distribute_files)
        self.distribute_btn.grid(row=2, column=0, columnspan=3, pady=20)

        # Прогресс-бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Лог операций
        ttk.Label(main_frame, text="Лог операций:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5)

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.log_text = tk.Text(log_frame, wrap="word", height=15, font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Статус
        self.status_label = ttk.Label(main_frame, text="Готов", relief=tk.SUNKEN)
        self.status_label.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def select_csv(self):
        file_path = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.csv_path.set(file_path)
            self.log(f"✓ Выбран CSV: {os.path.basename(file_path)}")

    def select_source_folder(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с файлами")
        if folder_path:
            self.source_folder.set(folder_path)
            self.log(f"✓ Выбрана папка: {folder_path}")

    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def find_file(self, source_dir, filename):
        """Поиск файла в папке и подпапках"""
        # Прямой поиск
        direct_path = os.path.join(source_dir, filename)
        if os.path.isfile(direct_path):
            return direct_path

        # Рекурсивный поиск
        for root, dirs, files in os.walk(source_dir):
            if filename in files:
                return os.path.join(root, filename)

            # Поиск по имени без учета расширения
            name_without_ext = os.path.splitext(filename)[0]
            for file in files:
                if os.path.splitext(file)[0] == name_without_ext:
                    return os.path.join(root, file)

        return None

    def distribute_files(self):
        csv_file = self.csv_path.get().strip()
        source_dir = self.source_folder.get().strip()

        if not csv_file or not os.path.exists(csv_file):
            messagebox.showerror("Ошибка", "Укажите корректный путь к CSV файлу")
            return

        if not source_dir or not os.path.exists(source_dir):
            messagebox.showerror("Ошибка", "Укажите корректную папку с файлами")
            return

        # Запуск процесса
        self.distribute_btn.config(state='disabled')
        self.progress.start(10)
        self.status_label.config(text="Распределение...")
        self.log("\n" + "="*60)
        self.log("НАЧАЛО РАСПРЕДЕЛЕНИЯ")
        self.log("="*60)

        try:
            # Чтение CSV
            records = []
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        records.append((row[0], row[1], row[2]))

            if not records:
                messagebox.showwarning("Предупреждение", "CSV файл не содержит данных")
                return

            self.log(f"Загружено записей: {len(records)}")

            success_count = 0
            error_count = 0
            missing_files = []

            for idx, (col1, col2, filename) in enumerate(records, 1):
                col1 = col1.strip()
                col2 = col2.strip()
                filename = filename.strip()

                if not all([col1, col2, filename]):
                    self.log(f"⚠ Строка {idx}: пропущена (пустые поля)")
                    continue

                # Создание папки
                target_dir = os.path.join(source_dir, col1, col2)
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except Exception as e:
                    self.log(f"✗ Строка {idx}: ошибка создания папки - {str(e)}")
                    error_count += 1
                    continue

                # Поиск и копирование файла
                source_file = self.find_file(source_dir, filename)

                if source_file:
                    dest_file = os.path.join(target_dir, os.path.basename(source_file))

                    # Обработка дубликатов
                    counter = 1
                    while os.path.exists(dest_file):
                        name, ext = os.path.splitext(os.path.basename(source_file))
                        dest_file = os.path.join(target_dir, f"{name}_{counter}{ext}")
                        counter += 1

                    try:
                        shutil.copy2(source_file, dest_file)
                        self.log(f"✓ Строка {idx}: {filename} -> {col1}/{col2}")
                        success_count += 1
                    except Exception as e:
                        self.log(f"✗ Строка {idx}: ошибка копирования - {str(e)}")
                        error_count += 1
                else:
                    self.log(f"⚠ Строка {idx}: файл '{filename}' не найден")
                    missing_files.append(filename)
                    error_count += 1

            # Итоги
            self.log("\n" + "="*60)
            self.log(f"ГОТОВО!")
            self.log(f"✓ Успешно скопировано: {success_count}")
            self.log(f"✗ Ошибок: {error_count}")
            if missing_files:
                self.log(f"⚠ Не найдено файлов: {len(missing_files)}")

            messagebox.showinfo("Завершено",
                               f"Распределение завершено!\n\n"
                               f"✓ Скопировано: {success_count}\n"
                               f"✗ Ошибок: {error_count}")

        except Exception as e:
            self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
        finally:
            self.progress.stop()
            self.distribute_btn.config(state='normal')
            self.status_label.config(text="Готов")

def main():
    root = tk.Tk()
    app = FileDistributorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
