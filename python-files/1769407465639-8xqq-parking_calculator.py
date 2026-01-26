#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import math

class ParkingCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Помощник застройщика по парковкам")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Создание виджетов
        ttk.Label(root, text="Количество квартир:", font=("Arial", 10)).pack(pady=(20, 5))
        self.apartments_entry = ttk.Entry(root, font=("Arial", 10))
        self.apartments_entry.pack(pady=5)

        ttk.Label(root, text="Тип жилья:", font=("Arial", 10)).pack(pady=(15, 5))
        self.housing_type = ttk.Combobox(root, values=["Комфорт", "Бизнес", "Стандарт", "Эконом"],
                                         state="readonly", font=("Arial", 10))
        self.housing_type.set("Стандарт")
        self.housing_type.pack(pady=5)

        self.calculate_btn = ttk.Button(root, text="Рассчитать", command=self.calculate)
        self.calculate_btn.pack(pady=20)

        self.result_frame = ttk.Frame(root)
        self.result_frame.pack(pady=10, fill="both", expand=True)

        self.result_text = tk.Text(self.result_frame, wrap="word", font=("Arial", 10),
                                   bg="#f0f0f0", relief="flat", height=8)
        self.result_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.result_text.config(state="disabled")

    def calculate(self):
        try:
            apartments = int(self.apartments_entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число квартир")
            return

        if apartments < 1 or apartments > 1000:
            messagebox.showerror("Ошибка", "Количество квартир должно быть от 1 до 1000")
            return

        housing_type = self.housing_type.get()
        coefficients = {
            "Комфорт": 2.0,
            "Бизнес": 1.5,
            "Стандарт": 1.0,
            "Эконом": 0.7
        }

        coef = coefficients[housing_type]
        resident_parking = math.ceil(apartments * coef)
        disabled_parking = math.ceil(resident_parking * 0.1)
        guest_parking = math.ceil(resident_parking * 0.2)

        parking_types = {
            "Комфорт": "Подземная роторная парковка",
            "Бизнес": "Подземная парковка",
            "Стандарт": "Подземно-наземная парковка",
            "Эконом": "Наземная парковка"
        }

        parking_type = parking_types[housing_type]

        result = (
            f"Тип парковки: {parking_type}\n"
            f"Парковок для жильцов: {resident_parking}\n"
            f"Парковок для инвалидов: {disabled_parking}\n"
            f"Гостевые парковки: {guest_parking}\n"
            f"Итого: {resident_parking + disabled_parking + guest_parking}"
        )

        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)
        self.result_text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingCalculatorApp(root)
    root.mainloop()
