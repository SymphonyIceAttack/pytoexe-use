import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime


class ProductApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учёт продуктов")
        self.root.geometry("800x600")

        # Файл для сохранения данных
        self.data_file = "products.json"
        self.products = []

        self.load_data()

        self.setup_ui()

    def setup_ui(self):
        # Верхняя панель (поиск и кнопки)
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(top_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self.filter_products)

        tk.Button(top_frame, text="Добавить", command=self.show_add_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Удалить", command=self.delete_product).pack(side=tk.LEFT, padx=5)

        # Таблица продуктов
        columns = ("Название", "Количество", "Срок годности")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200, anchor=tk.CENTER)

        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.refresh_table()

    def load_data(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.products = json.load(f)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные: {e}")

    def refresh_table(self):
        """Обновление таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_term = self.search_var.get().lower()
        filtered_products = [
            p for p in self.products
            if search_term in p["name"].lower()
        ]

        for product in filtered_products:
            self.tree.insert("", tk.END, values=(
                product["name"],
                product["quantity"],
                product["expiry"]
            ))

    def filter_products(self, event=None):
        """Фильтрация при вводе в поиск"""
        self.refresh_table()

    def show_add_dialog(self):
        """Диалоговое окно для добавления продукта"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить продукт")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Название:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        tk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        tk.Label(dialog, text="Количество:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        quantity_var = tk.IntVar(value=1)
        tk.Spinbox(dialog, from_=1, to=999, textvariable=quantity_var, width=28).grid(row=1, column=1, padx=10, pady=10)

        tk.Label(dialog, text="Срок годности (ГГГГ-ММ-ДД):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        expiry_var = tk.StringVar()
        tk.Entry(dialog, textvariable=expiry_var, width=30).grid(row=2, column=1, padx=10, pady=10)

        def add_product():
            name = name_var.get().strip()
            quantity = quantity_var.get()
            expiry = expiry_var.get().strip()

            if not name:
                messagebox.showwarning("Ошибка", "Введите название продукта!")
                return

            try:
                datetime.strptime(expiry, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Ошибка", "Неверный формат даты (должен быть ГГГГ-ММ-ДД)!")
                return

            self.products.append({
                "name": name,
                "quantity": quantity,
                "expiry": expiry
            })

            self.save_data()
            self.refresh_table()
            dialog.destroy()

        tk.Button(dialog, text="Добавить", command=add_product).grid(row=3, column=0, columnspan=2, pady=20)

    def delete_product(self):
        """Удаление выбранного продукта"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите продукт для удаления!")
            return

        item = self.tree.item(selected[0])
        product_name = item["values"][0]

        # Находим продукт в списке по названию
        for i, product in enumerate(self.products):
            if product["name"] == product_name:
                del self.products[i]
                break

        self.save_data()
        self.refresh_table()


def main():
    root = tk.Tk()
    app = ProductApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
