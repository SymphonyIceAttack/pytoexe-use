import pandas as pd
import sys
import os
from tkinter import filedialog, messagebox, Tk
from tkinter import ttk
import tkinter as tk
import threading

class ExcelFilterApp:
    """
    Приложение с графическим интерфейсом для фильтрации Excel файлов.
    Оставляет только нужные типы документов в указанном столбце.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Фильтр Excel по типам документов")
        self.root.geometry("620x480")
        self.root.resizable(False, False)

        # --- НАСТРОЙКИ (измените здесь, если нужно) ---
        self.DEFAULT_COLUMN_NAME = "тип документа"
        self.ALLOWED_TYPES = [
            "Приход от поставщика",
            "Реализация по банковской карте",
            "Розничная реализация"
        ]
        # -----------------------------------------------

        # Переменные для хранения путей к файлам
        self.input_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()

        # Построение интерфейса
        self._create_widgets()

    def _create_widgets(self):
        """Создаёт все элементы интерфейса."""
        # --- Рамка выбора входного файла ---
        frame_input = tk.LabelFrame(self.root, text="1. Выберите Excel файл", padx=10, pady=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        btn_browse_input = tk.Button(frame_input, text="Обзор...", command=self._select_input_file, width=12)
        btn_browse_input.grid(row=0, column=0, padx=5, pady=5)

        lbl_input_path = tk.Label(frame_input, textvariable=self.input_file_path, fg="blue", wraplength=450, anchor="w")
        lbl_input_path.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- Рамка для настроек ---
        frame_settings = tk.LabelFrame(self.root, text="2. Настройки фильтра", padx=10, pady=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        # Название столбца
        lbl_column = tk.Label(frame_settings, text="Название столбца с типом документа:")
        lbl_column.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.column_name_entry = tk.Entry(frame_settings, width=40)
        self.column_name_entry.insert(0, self.DEFAULT_COLUMN_NAME)
        self.column_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Разрешённые типы
        lbl_allowed = tk.Label(frame_settings, text="Разрешённые типы (каждый с новой строки):")
        lbl_allowed.grid(row=1, column=0, sticky="nw", padx=5, pady=5)

        self.allowed_types_text = tk.Text(frame_settings, height=6, width=40)
        self.allowed_types_text.insert("1.0", "\n".join(self.ALLOWED_TYPES))
        self.allowed_types_text.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # --- Рамка для выходного файла ---
        frame_output = tk.LabelFrame(self.root, text="3. Куда сохранить результат", padx=10, pady=10)
        frame_output.pack(fill="x", padx=10, pady=5)

        btn_browse_output = tk.Button(frame_output, text="Сохранить как...", command=self._select_output_file, width=12)
        btn_browse_output.grid(row=0, column=0, padx=5, pady=5)

        lbl_output_path = tk.Label(frame_output, textvariable=self.output_file_path, fg="green", wraplength=450, anchor="w")
        lbl_output_path.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # --- Статус и прогресс ---
        self.status_label = tk.Label(self.root, text="Готов к работе", fg="gray")
        self.status_label.pack(anchor="w", padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        # --- Кнопка запуска ---
        btn_run = tk.Button(self.root, text="ЗАПУСТИТЬ ФИЛЬТРАЦИЮ", command=self._start_filtering,
                            bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_run.pack(fill="x", padx=10, pady=10)

    def _select_input_file(self):
        """Открывает диалог выбора входного Excel файла."""
        file_path = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)
            # Автоматически предложить имя для выходного файла
            base, ext = os.path.splitext(file_path)
            default_output = f"{base}_filtered{ext}"
            self.output_file_path.set(default_output)

    def _select_output_file(self):
        """Открывает диалог для выбора пути сохранения результата."""
        if not self.input_file_path.get():
            messagebox.showerror("Ошибка", "Сначала выберите входной файл.")
            return
        file_path = filedialog.asksaveasfilename(
            title="Сохранить результат как",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if file_path:
            self.output_file_path.set(file_path)

    def _start_filtering(self):
        """Запускает процесс фильтрации в отдельном потоке, чтобы интерфейс не завис."""
        if not self.input_file_path.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите входной Excel файл.")
            return
        if not self.output_file_path.get():
            messagebox.showerror("Ошибка", "Пожалуйста, укажите, куда сохранить результат.")
            return

        # Получаем настройки из интерфейса
        column_name = self.column_name_entry.get().strip()
        if not column_name:
            messagebox.showerror("Ошибка", "Пожалуйста, укажите название столбца.")
            return

        allowed_raw = self.allowed_types_text.get("1.0", tk.END).strip()
        allowed_list = [line.strip() for line in allowed_raw.splitlines() if line.strip()]
        if not allowed_list:
            messagebox.showerror("Ошибка", "Пожалуйста, укажите хотя бы один разрешённый тип документа.")
            return

        # Запускаем фильтрацию в фоновом потоке
        threading.Thread(target=self._filter_excel, args=(column_name, allowed_list), daemon=True).start()

    def _filter_excel(self, column_name, allowed_list):
        """Выполняет фильтрацию Excel файла. Запускается в отдельном потоке."""
        input_path = self.input_file_path.get()
        output_path = self.output_file_path.get()

        # Блокируем интерфейс и показываем прогресс
        self.root.config(cursor="watch")
        self.progress_bar.start()
        self.status_label.config(text="Выполняется фильтрация... Пожалуйста, подождите.", fg="orange")
        self.root.update_idletasks()

        try:
            # Читаем Excel файл
            df = pd.read_excel(input_path, dtype_backend='numpy_nullable')
            original_row_count = len(df)

            # Проверяем наличие столбца
            if column_name not in df.columns:
                error_msg = f"Столбец '{column_name}' не найден.\nДоступные столбцы: {', '.join(list(df.columns))}"
                raise ValueError(error_msg)

            # Приводим всё к нижнему регистру для сравнения (без учёта регистра и лишних пробелов)
            allowed_norm = [str(t).strip().lower() for t in allowed_list]
            mask = df[column_name].astype(str).str.strip().str.lower().isin(allowed_norm)

            # Применяем маску
            filtered_df = df[mask].copy()
            filtered_row_count = len(filtered_df)

            if filtered_row_count == 0:
                raise ValueError("После фильтрации не осталось ни одной строки. Проверьте разрешённые типы.")

            # Сохраняем результат
            filtered_df.to_excel(output_path, index=False, engine='openpyxl')

            # Показываем сообщение об успехе
            self.progress_bar.stop()
            self.status_label.config(
                text=f"Готово! Исходных строк: {original_row_count}, осталось: {filtered_row_count}",
                fg="green"
            )
            result_msg = (
                f"Фильтрация выполнена успешно!\n\n"
                f"Исходных строк: {original_row_count}\n"
                f"Оставлено строк: {filtered_row_count}\n\n"
                f"Результат сохранён в:\n{output_path}"
            )
            messagebox.showinfo("Завершено", result_msg)

        except Exception as e:
            self.progress_bar.stop()
            self.status_label.config(text="Ошибка", fg="red")
            messagebox.showerror("Ошибка", f"Не удалось выполнить фильтрацию:\n{e}")
        finally:
            self.root.config(cursor="")

# --- Точка входа в программу ---
if __name__ == "__main__":
    try:
        # Создаём главное окно приложения
        root = Tk()
        app = ExcelFilterApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить приложение:\n{e}")