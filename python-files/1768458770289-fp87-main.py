# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime, timedelta
import threading

# Конфигурация
BOT_TOKEN = "8203695173:AAF96cGjJ_LcfchvmsLAbxk2-WjkWZRNRzw"
CHAT_ID = None # Будет установлен при запуске бота
DATA_FILE = "shifts.json"
CONFIG_FILE = "config.json"

class ShiftApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Выход на смену")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Загружаем данные
        self.load_data()
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Проверяем, нужно ли сбросить ежедневный статус
        self.check_daily_reset()
    
    def load_data(self):
        """Загружает данные из файла"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "shifts": [],
                "last_shift_date": None,
                "shift_today": False
            }
        
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                global CHAT_ID
                CHAT_ID = config.get("chat_id")
    
    def save_data(self):
        """Сохраняет данные в файл"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def check_daily_reset(self):
        """Сбрасывает статус смены в 8:00 по МСК"""
        now = datetime.now()
        msk_time = now + timedelta(hours=3) # UTC+3 для МСК
        
        if self.data["last_shift_date"]:
            last_date = datetime.fromisoformat(self.data["last_shift_date"])
            if msk_time.hour >= 8 and now.date() > last_date.date():
                self.data["shift_today"] = False
        
        # Проверяем каждую минуту
        self.root.after(60000, self.check_daily_reset)
    
    def create_widgets(self):
        """Создает элементы интерфейса"""
        # Заголовок
        title_label = tk.Label(
            self.root,
            text="Выход на смену",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # Выбор имени
        name_frame = tk.Frame(self.root)
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="Ваше имя:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(
            name_frame,
            textvariable=self.name_var,
            values=["Костя", "Настя", "Маша", "Рауль", "Никита", "Аня"],
            state="readonly",
            width=15
        )
        self.name_combo.pack(side=tk.LEFT)
        
        # Выбор адреса
        address_frame = tk.Frame(self.root)
        address_frame.pack(pady=10)
        
        tk.Label(address_frame, text="Адрес смены:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.address_var = tk.StringVar()
        self.address_combo = ttk.Combobox(
            address_frame,
            textvariable=self.address_var,
            values=["ул. Нежнова WB", "ул. Пестова WB", "ул. Нежнова OZON"],
            state="readonly",
            width=20
        )
        self.address_combo.pack(side=tk.LEFT)
        
        # Кнопка начала смены
        self.start_button = tk.Button(
            self.root,
            text="Начать смену",
            command=self.start_shift,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        self.start_button.pack(pady=30)
        
        # Статус
        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack()
    
    def start_shift(self):
        """Обрабатывает нажатие кнопки начала смены"""
        name = self.name_var.get()
        address = self.address_var.get()
        
        if not name or not address:
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите имя и адрес!")
            return
        
        # Проверяем, была ли уже смена сегодня
        if self.data["shift_today"]:
            messagebox.showinfo("Информация", "Вы уже вышли на смену сегодня!")
            return
        
        # Записываем смену
        now = datetime.now()
        shift_data = {
            "name": name,
            "address": address,
            "date": now.isoformat(),
            "date_str": now.strftime("%d.%m.%y")
        }
        
        self.data["shifts"].append(shift_data)
        self.data["shift_today"] = True
        self.data["last_shift_date"] = now.isoformat()
        self.save_data()
        
        # Отправляем в бота
        self.send_to_bot(name, address, now.strftime("%d.%m.%y"))
        
        # Показываем сообщение
        messagebox.showinfo("Успешно", "Вы вышли на смену, можете закрыть программу")
        self.status_label.config(text=f"Смена: {name} - {address}", fg="green")
    
    def send_to_bot(self, name, address, date):
        """Отправляет данные в телеграм-бота"""
        if not CHAT_ID:
            return
        
        message = f"{name}, вышел(ла) на смену по адресу: {address}, {date}"
        
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": CHAT_ID,
                "text": message
            }
            response = requests.post(url, json=data, timeout=5)
            
            if response.status_code != 200:
                print(f"Ошибка отправки: {response.text}")
        except Exception as e:
            print(f"Ошибка: {e}")

def main():
    root = tk.Tk()
    app = ShiftApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()