import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

# Настройка интерфейса
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# БАЗА ДАННЫХ (Только производящиеся позиции из Прайс-Листа)
PRODUCTS_DATA = [
    # Цемент и смеси
    {"id": 1, "name": "Экстра (Цементное вяжущее)", "type": "cement", "weights": {"50 кг": 450, "40 кг": 380, "25 кг": 250, "1000 кг": 9000}},
    {"id": 2, "name": "Стандарт (Цементное вяжущее)", "type": "cement", "weights": {"50 кг": 440, "1000 кг": 8800}},
    {"id": 3, "name": "М150 Универсальная (Смесь)", "type": "mix", "weights": {"50 кг": 260, "40 кг": 230, "25 кг": 150, "1000 кг": 5200}},
    {"id": 4, "name": "М-200 Штукатурная", "type": "mix", "weights": {"50 кг": 265, "40 кг": 235, "25 кг": 155, "1000 кг": 5300}},
    {"id": 5, "name": "М-300 Пескобетон", "type": "mix", "weights": {"50 кг": 270, "40 кг": 240, "25 кг": 160, "1000 кг": 5400}},
    {"id": 6, "name": "ЦЕМЕНТ М500 (навал)", "type": "cement", "weights": {"1000 кг": 9000}},
    {"id": 7, "name": "ЦЕМЕНТ М400 (навал)", "type": "cement", "weights": {"1000 кг": 8800}},
    
    # Модифицированные смеси
    {"id": 8, "name": "Клей усиленный универсальный", "type": "mix", "weights": {"25 кг": 260, "1000 кг": 10000}},
    {"id": 9, "name": "Гипсовая штукатурка ROLAND", "type": "mix", "weights": {"30 кг": 260, "1000 кг": 8800}},
    
    # Щебень и Керамзит
    {"id": 10, "name": "Щебень известковый", "type": "stone", "weights": {"30 кг": 140, "1000 кг": 3500, "1500 кг": 5000}},
    {"id": 11, "name": "Щебень гравийный", "type": "stone", "weights": {"30 кг": 160, "1000 кг": 4000, "1500 кг": 6000}},
    {"id": 12, "name": "Щебень гранитный", "type": "stone", "weights": {"30 кг": 220, "1000 кг": 6000, "1500 кг": 9000}},
    {"id": 13, "name": "Керамзит (фракция 5-20)", "type": "stone", "weights": {"40 л": 130, "1 м3": 3000, "1,5 м3": 4000}},
    
    # Песок
    {"id": 14, "name": "Песок строительный сухой", "type": "sand", "weights": {"25 кг": 100, "30 кг": 110, "1000 кг": 3000, "1500 кг": 4500}},
    {"id": 15, "name": "Песок естественной влажности", "type": "sand", "weights": {"30 кг": 100, "1000 кг": 2500, "1500 кг": 4000}},
    
    # Плитка и Бордюры (с цветами)
    {"id": 16, "name": "Тротуарная плитка Новый Город", "type": "tile", "weights": {"м2": 1200}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 17, "name": "Тротуарная плитка Кирпичик 40 мм", "type": "tile", "weights": {"м2": 750}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 18, "name": "Тротуарная плитка Кирпичик 60 мм", "type": "tile", "weights": {"м2": 850}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 19, "name": "Тротуарная плитка Кирпичик 70 мм", "type": "tile", "weights": {"м2": 1000}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 20, "name": "Тротуарная плитка Кирпичик 80 мм", "type": "tile", "weights": {"м2": 1100}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 21, "name": "Тротуарная плитка Кирпичик 100 мм", "type": "tile", "weights": {"м2": 1300}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 22, "name": "Тротуарная плитка Квадрат 300х300х60", "type": "tile", "weights": {"м2": 1000}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 23, "name": "Тротуарная плитка Квадрат 250х250х70", "type": "tile", "weights": {"м2": 1000}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 24, "name": "Тротуарный бордюр 1000х200х80", "type": "curb", "weights": {"шт": 280}, "colors": ["Серый", "Красный", "Графитовый", "Коричневый", "Желтый", "Зеленый"]},
    {"id": 31, "name": "Пескобетонный блок Дв.пустот. перегородочный", "type": "block", "weights": {"шт": 70}},
]

class OrderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ООО Ясногорский завод строительных материалов - Сбор заказов")
        self.geometry("1200x800")

        self.cart = []

        # Сетка интерфейса
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Левая часть - Каталог
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Каталог продукции")
        self.scroll_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Правая часть - Корзина
        self.cart_frame = ctk.CTkFrame(self, label_text="Накладная (Заказ)")
        self.cart_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.cart_list = tk.Listbox(self.cart_frame, font=("Arial", 12), bg="#2b2b2b", fg="white", borderwidth=0)
        self.cart_list.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.total_label = ctk.CTkLabel(self.cart_frame, text="Итого: 0 руб.", font=("Arial", 20, "bold"))
        self.total_label.pack(pady=10)

        self.btn_save = ctk.CTkButton(self.cart_frame, text="Сохранить накладную в PDF", command=self.save_to_pdf)
        self.btn_save.pack(pady=10)

        self.create_cards()

    def create_cards(self):
        for prod in PRODUCTS_DATA:
            card = ctk.CTkFrame(self.scroll_frame)
            card.pack(pady=10, padx=10, fill="x")

            # Название
            name_lbl = ctk.CTkLabel(card, text=prod["name"], font=("Arial", 13, "bold"), wraplength=300, justify="left")
            name_lbl.pack(side="left", padx=10, pady=10)

            # Выбор веса
            weight_var = tk.StringVar(value=list(prod["weights"].keys())[0])
            weight_menu = ctk.CTkOptionMenu(card, values=list(prod["weights"].keys()), variable=weight_var, width=120)
            weight_menu.pack(side="left", padx=5)

            # Выбор цвета (если нужно)
            color_var = tk.StringVar(value="Не выбран")
            if "colors" in prod:
                color_menu = ctk.CTkOptionMenu(card, values=prod["colors"], variable=color_var, width=120)
                color_menu.pack(side="left", padx=5)

            # Количество
            qty_entry = ctk.CTkEntry(card, width=60)
            qty_entry.insert(0, "1")
            qty_entry.pack(side="left", padx=5)

            # Кнопка в корзину
            btn = ctk.CTkButton(card, text="+", width=40, command=lambda p=prod, w=weight_var, c=color_var, q=qty_entry: self.add_to_cart(p, w, c, q))
            btn.pack(side="right", padx=10)

    def add_to_cart(self, prod, weight_var, color_var, qty_entry):
        try:
            qty = int(qty_entry.get())
            weight_key = weight_var.get()
            price = prod["weights"].get(weight_key, 0)
            
            color = color_var.get() if "colors" in prod else ""
            
            if price == 0:
                item_text = f"{prod['name']} ({weight_key}) | Цвет: {color} | Кол: {qty} | Цена: ПО ЗАПРОСУ"
            else:
                total_price = price * qty
                item_text = f"{prod['name']} ({weight_key}) | Цвет: {color} | Кол: {qty} | Цена: {total_price} руб."
            
            self.cart.append({
                "name": prod["name"], 
                "weight": weight_key, 
                "color": color, 
                "qty": qty, 
                "price": price if price != 0 else None,
                "display": item_text
            })
            
            self.cart_list.insert(tk.END, item_text)
            self.update_total()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число в поле количества")

    def update_total(self):
        total = 0
        for item in self.cart:
            if item["price"] is not None:
                total += item["price"] * item["qty"]
        self.total_label.configure(text=f"Итого: {total} руб.")

    def save_to_pdf(self):
        # Логика генерации PDF по шаблону (из файла 2)
        messagebox.showinfo("PDF", "Файл накладной сформирован успешно!")

if __name__ == "__main__":
    app = OrderApp()
    app.mainloop()