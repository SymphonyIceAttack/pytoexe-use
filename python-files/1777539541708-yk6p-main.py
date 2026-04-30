import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Складской Аналитик v1.0")
        self.root.geometry("500x400")
        
        # Переменные для хранения путей к файлам
        self.stock_path = tk.StringVar()
        self.orders_path = tk.StringVar()
        
        self.create_widgets()

    def create_widgets(self):
        # Стилизация
        style = ttk.Style()
        style.configure("TButton", padding=6, font=('Helvetica', 10))
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Блок файла остатков (Лист 1)
        ttk.Label(main_frame, text="Файл остатков (Код, Артикул, Количество):", font=('Helvetica', 9, 'bold')).pack(anchor=tk.W)
        stock_entry = ttk.Entry(main_frame, textvariable=self.stock_path, width=50)
        stock_entry.pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="Выбрать файл остатков", command=self.load_stock).pack(anchor=tk.E, pady=(0, 15))

        # Блок файла заказов (Лист 2)
        ttk.Label(main_frame, text="Файл заказов (Артикул, Кол-во, Номер листа):", font=('Helvetica', 9, 'bold')).pack(anchor=tk.W)
        orders_entry = ttk.Entry(main_frame, textvariable=self.orders_path, width=50)
        orders_entry.pack(fill=tk.X, pady=5)
        ttk.Button(main_frame, text="Выбрать файл заказов", command=self.load_orders).pack(anchor=tk.E, pady=(0, 20))

        # Кнопка запуска
        self.run_btn = ttk.Button(main_frame, text="ОБРАБОТАТЬ И СОХРАНИТЬ", command=self.process_data)
        self.run_btn.pack(fill=tk.X, ipady=10)

        # Поле логов
        self.log_text = tk.Text(main_frame, height=8, state='disabled', font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def load_stock(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path: self.stock_path.set(path)

    def load_orders(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path: self.orders_path.set(path)

    def process_data(self):
        if not self.stock_path.get() or not self.orders_path.get():
            messagebox.showwarning("Ошибка", "Выберите оба файла!")
            return

        try:
            self.log("--- Начало обработки ---")
            
            # 1. Загрузка данных
            # Предполагаем колонки: Лист1 (0:Код, 1:Артикул, 2:Кол-во)
            # Лист2 (0:Номенклатура, 1:Артикул, 2:Нужное_кол-во, 3:Номер_листа)
            df_stock = pd.read_excel(self.stock_path.get())
            df_orders = pd.read_excel(self.orders_path.get())

            # Переименуем для удобства (индексы как в макросе)
            df_stock.columns = ['Код', 'Артикул', 'Остаток'] + list(df_stock.columns[3:])
            df_orders.columns = ['Номенклатура', 'Артикул', 'Заказано', 'Сервисный_Лист'] + list(df_orders.columns[4:])

            self.log(f"Загружено остатков: {len(df_stock)} поз.")
            self.log(f"Загружено заказов: {len(df_orders)} поз.")

            # 2. Сливаем таблицы по Артикулу
            merged = pd.merge(df_orders, df_stock[['Артикул', 'Остаток', 'Код']], on='Артикул', how='left')

            # 3. Проверка наличия
            merged['Найдено'] = merged['Остаток'].notna() & (merged['Остаток'] >= merged['Заказано'])

            # 4. ЛОГИКА МАКРОСА: Если в сервисном листе хоть одна позиция False -> бракуем весь лист
            # Группируем по 'Сервисный_Лист' и проверяем, что ВСЕ значения 'Найдено' == True
            merged['Лист_Валиден'] = merged.groupby('Сервисный_Лист')['Найдено'].transform('all')

            # 5. Разделяем результат
            final_report = merged[merged['Лист_Валиден'] == True].copy()
            rejected_sheets = merged[merged['Лист_Валиден'] == False]['Сервисный_Лист'].unique()

            if len(rejected_sheets) > 0:
                self.log(f"Аннулировано листов (некомплект): {len(rejected_sheets)}")
            
            # 6. Сохранение
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            if save_path:
                # Оставляем только нужные колонки для Листа 3
                output = final_report[['Код', 'Артикул', 'Номенклатура', 'Заказано', 'Сервисный_Лист']]
                output.to_excel(save_path, index=False)
                self.log(f"Успешно сохранено: {len(output)} строк")
                messagebox.showinfo("Готово", f"Файл сохранен!\nОбработано строк: {len(output)}")
            
        except Exception as e:
            self.log(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошел сбой: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()