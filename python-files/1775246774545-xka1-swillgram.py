import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import json
import os
import datetime
import hashlib
import threading
import time
import random

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class SwillGram:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("SWILLGRAM - Аналог Telegram")
        self.window.geometry("400x700")
        self.window.resizable(False, False)
        
        # Данные пользователей
        self.users_file = "swillgram_users.json"
        self.messages_file = "swillgram_messages.json"
        self.load_data()
        
        # Текущий пользователь
        self.current_user = None
        self.ai_code = None
        
        # ИИ код (правильный)
        self.CORRECT_AI_CODE = "SWILL2025"
        
        # Показываем экран входа
        self.show_login_screen()
        
    def load_data(self):
        """Загрузка пользователей и сообщений"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
            
        if os.path.exists(self.messages_file):
            with open(self.messages_file, 'r') as f:
                self.messages = json.load(f)
        else:
            self.messages = []
            
    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=4)
            
    def save_messages(self):
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=4)
            
    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()
            
    def show_login_screen(self):
        self.clear_window()
        
        # Заголовок
        title = ctk.CTkLabel(self.window, text="SWILLGRAM", font=("Arial", 36, "bold"))
        title.pack(pady=50)
        
        subtitle = ctk.CTkLabel(self.window, text="Аналог Telegram с ИИ", font=("Arial", 14))
        subtitle.pack(pady=10)
        
        # Кнопки
        login_btn = ctk.CTkButton(self.window, text="ВХОД", width=200, height=40, 
                                   font=("Arial", 16), command=self.show_login_form)
        login_btn.pack(pady=20)
        
        register_btn = ctk.CTkButton(self.window, text="РЕГИСТРАЦИЯ", width=200, height=40,
                                      font=("Arial", 16), command=self.show_register_form)
        register_btn.pack(pady=10)
        
    def show_register_form(self):
        self.clear_window()
        
        title = ctk.CTkLabel(self.window, text="РЕГИСТРАЦИЯ", font=("Arial", 28, "bold"))
        title.pack(pady=30)
        
        # Поля ввода
        phone_frame = ctk.CTkFrame(self.window)
        phone_frame.pack(pady=10, padx=40, fill="x")
        phone_label = ctk.CTkLabel(phone_frame, text="📱 Номер телефона:", font=("Arial", 14))
        phone_label.pack(anchor="w")
        self.phone_entry = ctk.CTkEntry(phone_frame, placeholder_text="+7 999 123-45-67", height=35)
        self.phone_entry.pack(fill="x", pady=5)
        
        username_frame = ctk.CTkFrame(self.window)
        username_frame.pack(pady=10, padx=40, fill="x")
        username_label = ctk.CTkLabel(username_frame, text="👤 Никнейм:", font=("Arial", 14))
        username_label.pack(anchor="w")
        self.username_entry = ctk.CTkEntry(username_frame, placeholder_text="cool_user", height=35)
        self.username_entry.pack(fill="x", pady=5)
        
        password_frame = ctk.CTkFrame(self.window)
        password_frame.pack(pady=10, padx=40, fill="x")
        password_label = ctk.CTkLabel(password_frame, text="🔒 Пароль:", font=("Arial", 14))
        password_label.pack(anchor="w")
        self.password_entry = ctk.CTkEntry(password_frame, placeholder_text="******", show="*", height=35)
        self.password_entry.pack(fill="x", pady=5)
        
        # Код ИИ
        ai_frame = ctk.CTkFrame(self.window)
        ai_frame.pack(pady=20, padx=40, fill="x")
        ai_label = ctk.CTkLabel(ai_frame, text="🤖 КОД ДЛЯ ИСКУССТВЕННОГО ИНТЕЛЛЕКТА:", font=("Arial", 12))
        ai_label.pack(anchor="w")
        self.ai_code_entry = ctk.CTkEntry(ai_frame, placeholder_text="Введи код активации ИИ", height=35)
        self.ai_code_entry.pack(fill="x", pady=5)
        
        ai_info = ctk.CTkLabel(ai_frame, text="(Без кода ИИ не будет работать)", font=("Arial", 10), text_color="gray")
        ai_info.pack(anchor="w")
        
        # Кнопки
        register_btn = ctk.CTkButton(self.window, text="ЗАРЕГИСТРИРОВАТЬСЯ", width=200, height=40,
                                      font=("Arial", 14), command=self.register_user)
        register_btn.pack(pady=20)
        
        back_btn = ctk.CTkButton(self.window, text="Назад", width=200, height=35,
                                  fg_color="gray", command=self.show_login_screen)
        back_btn.pack(pady=5)
        
    def register_user(self):
        phone = self.phone_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        ai_code = self.ai_code_entry.get().strip()
        
        # Проверки
        if not phone or not username or not password:
            messagebox.showerror("Ошибка", "Заполни все поля!")
            return
            
        if phone in self.users:
            messagebox.showerror("Ошибка", "Этот номер уже зарегистрирован!")
            return
            
        if username in [self.users[u]["username"] for u in self.users]:
            messagebox.showerror("Ошибка", "Этот ник уже занят!")
            return
            
        # Проверка кода ИИ
        if ai_code != self.CORRECT_AI_CODE:
            messagebox.showerror("Ошибка", "НЕВЕРНЫЙ КОД ДЛЯ ИИ!\nПравильный код: SWILL2025")
            return
            
        # Сохраняем пользователя
        user_id = str(len(self.users) + 1)
        self.users[phone] = {
            "id": user_id,
            "username": username,
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "phone": phone,
            "ai_code": ai_code,
            "registered_at": str(datetime.datetime.now())
        }
        self.save_users()
        
        messagebox.showinfo("Успех", f"Регистрация завершена!\nДобро пожаловать, {username}!")
        self.show_login_form()
        
    def show_login_form(self):
        self.clear_window()
        
        title = ctk.CTkLabel(self.window, text="ВХОД В SWILLGRAM", font=("Arial", 28, "bold"))
        title.pack(pady=50)
        
        # Поля входа
        phone_frame = ctk.CTkFrame(self.window)
        phone_frame.pack(pady=10, padx=40, fill="x")
        phone_label = ctk.CTkLabel(phone_frame, text="📱 Номер телефона:", font=("Arial", 14))
        phone_label.pack(anchor="w")
        self.login_phone = ctk.CTkEntry(phone_frame, placeholder_text="+7 999 123-45-67", height=35)
        self.login_phone.pack(fill="x", pady=5)
        
        password_frame = ctk.CTkFrame(self.window)
        password_frame.pack(pady=10, padx=40, fill="x")
        password_label = ctk.CTkLabel(password_frame, text="🔒 Пароль:", font=("Arial", 14))
        password_label.pack(anchor="w")
        self.login_password = ctk.CTkEntry(password_frame, placeholder_text="******", show="*", height=35)
        self.login_password.pack(fill="x", pady=5)
        
        login_btn = ctk.CTkButton(self.window, text="ВОЙТИ", width=200, height=40,
                                   font=("Arial", 14), command=self.login_user)
        login_btn.pack(pady=20)
        
        back_btn = ctk.CTkButton(self.window, text="Назад", width=200, height=35,
                                  fg_color="gray", command=self.show_login_screen)
        back_btn.pack(pady=5)
        
    def login_user(self):
        phone = self.login_phone.get().strip()
        password = self.login_password.get()
        
        if phone not in self.users:
            messagebox.showerror("Ошибка", "Пользователь не найден!")
            return
            
        user = self.users[phone]
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        
        if user["password"] != hashed_pass:
            messagebox.showerror("Ошибка", "Неверный пароль!")
            return
            
        self.current_user = user
        self.ai_code = user.get("ai_code")
        self.show_main_app()
        
    def show_main_app(self):
        self.clear_window()
        
        # Верхняя панель
        top_frame = ctk.CTkFrame(self.window, height=60)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        user_info = ctk.CTkLabel(top_frame, text=f"👤 {self.current_user['username']}", 
                                   font=("Arial", 16, "bold"))
        user_info.pack(side="left", padx=10)
        
        online_label = ctk.CTkLabel(top_frame, text="● ONLINE", font=("Arial", 10), text_color="green")
        online_label.pack(side="left", padx=5)
        
        logout_btn = ctk.CTkButton(top_frame, text="Выход", width=60, height=30,
                                    fg_color="red", command=self.logout)
        logout_btn.pack(side="right", padx=10)
        
        # Чат с ИИ
        chat_frame = ctk.CTkFrame(self.window)
        chat_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Заголовок чата
        chat_header = ctk.CTkLabel(chat_frame, text="🤖 ЧАТ С ИСКУССТВЕННЫМ ИНТЕЛЛЕКТОМ 🤖",
                                     font=("Arial", 14, "bold"))
        chat_header.pack(pady=10)
        
        # Область сообщений
        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap="word", 
                                                     bg="#1e1e1e", fg="#00ffcc",
                                                     font=("Arial", 12))
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_area.config(state="disabled")
        
        # Нижняя панель ввода
        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.message_entry = ctk.CTkEntry(input_frame, placeholder_text="Напиши сообщение...", height=40)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        send_btn = ctk.CTkButton(input_frame, text="📤", width=50, height=40,
                                  font=("Arial", 16), command=self.send_message)
        send_btn.pack(side="right")
        
        # Приветственное сообщение
        self.add_system_message("🤖 ИИ активирован! Задай любой вопрос.")
        
        # Привязываем Enter
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
    def add_system_message(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"🔷 СИСТЕМА: {text}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see("end")
        
    def add_user_message(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"👤 {self.current_user['username']}: {text}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see("end")
        
    def add_ai_message(self, text):
        self.chat_area.config(state="normal")
        self.chat_area.insert("end", f"🤖 ИИ: {text}\n\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see("end")
        
    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
            
        self.message_entry.delete(0, "end")
        self.add_user_message(message)
        
        # Сохраняем сообщение
        self.messages.append({
            "user": self.current_user["username"],
            "message": message,
            "time": str(datetime.datetime.now())
        })
        self.save_messages()
        
        # ИИ отвечает в отдельном потоке
        threading.Thread(target=self.ai_respond, args=(message,), daemon=True).start()
        
    def ai_respond(self, message):
        time.sleep(0.5)  # Эмуляция задержки ИИ
        
        # Проверка кода ИИ
        if self.ai_code != self.CORRECT_AI_CODE:
            self.add_ai_message("❌ КОД ИИ НЕ АКТИВИРОВАН! Введи правильный код при регистрации.")
            return
            
        # Умные ответы ИИ
        message_lower = message.lower()
        
        if "привет" in message_lower or "здарова" in message_lower:
            response = f"Привет, {self.current_user['username']}! Чем могу помочь?"
        elif "как дела" in message_lower:
            response = "У меня всё отлично! Я нейросеть, всегда на связи."
        elif "кто ты" in message_lower:
            response = "Я SWILL AI - искусственный интеллект, созданный для общения в SwillGram."
        elif "погода" in message_lower:
            response = "Я не могу узнать погоду, но могу поговорить на любые темы!"
        elif "люблю" in message_lower:
            response = "Это прекрасно! Любовь делает мир лучше ❤️"
        elif "читы" in message_lower or "хак" in message_lower:
            response = "О, ты из команды SWILL? Круто! Читы - наша тема 🔥"
        elif "помощь" in message_lower or "help" in message_lower:
            response = "Просто пиши мне что угодно, я поддержу разговор!"
        elif "пока" in message_lower:
            response = "До связи! Заходи ещё в SwillGram 😊"
        else:
            responses = [
                f"Интересно, {self.current_user['username']}! Расскажи подробнее.",
                "Я тебя слышу. Продолжай, мне интересно.",
                "Хорошая мысль! А что ты думаешь по этому поводу?",
                "Запомню это. У тебя отличный вкус!",
                "SWILL AI к твоим услугам. Задавай любые вопросы!"
            ]
            response = random.choice(responses)
            
        self.add_ai_message(response)
        
    def logout(self):
        self.current_user = None
        self.ai_code = None
        self.show_login_screen()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = SwillGram()
    app.run()