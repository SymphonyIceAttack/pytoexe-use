import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
import math
import time

# ===== NEW LAUNCHER - ТОЧНАЯ КОПИЯ =====

class NewLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("New Launcher")
        self.root.geometry("1280x720")
        self.root.configure(bg="#0b0e14")
        
        # Кастомная рамка как в оригинале
        self.root.overrideredirect(True)
        
        # Центрируем
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1280) // 2
        y = (screen_height - 720) // 2
        self.root.geometry(f"1280x720+{x}+{y}")
        
        # Данные
        self.load_data()
        
        # Переменные для анимаций
        self.animation_id = None
        self.current_page = "home"
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Запускаем анимации
        self.start_animations()
        
    def load_data(self):
        """Загрузка данных"""
        if os.path.exists("newlauncher_data.json"):
            with open("newlauncher_data.json", "r") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "username": "Player",
                "balance": 0,
                "premium": False,
                "games": []
            }
            self.save_data()
    
    def save_data(self):
        with open("newlauncher_data.json", "w") as f:
            json.dump(self.data, f)
    
    def setup_ui(self):
        """Интерфейс точь-в-точь как New Launcher"""
        
        # Верхняя панель (как в оригинале)
        self.top_bar = tk.Frame(self.root, bg="#14181f", height=48)
        self.top_bar.pack(fill="x")
        self.top_bar.pack_propagate(False)
        
        # Кнопки управления
        control_frame = tk.Frame(self.top_bar, bg="#14181f")
        control_frame.pack(side="right", padx=10, pady=12)
        
        self.min_btn = tk.Label(control_frame, text="─", bg="#14181f", fg="#8a9bb5",
                                font=("Segoe UI", 14), cursor="hand2")
        self.min_btn.pack(side="left", padx=12)
        self.min_btn.bind("<Button-1>", lambda e: self.root.iconify())
        self.min_btn.bind("<Enter>", lambda e: self.min_btn.config(fg="white"))
        self.min_btn.bind("<Leave>", lambda e: self.min_btn.config(fg="#8a9bb5"))
        
        self.close_btn = tk.Label(control_frame, text="✕", bg="#14181f", fg="#8a9bb5",
                                  font=("Segoe UI", 14), cursor="hand2")
        self.close_btn.pack(side="left", padx=12)
        self.close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg="#ff5e5e"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg="#8a9bb5"))
        
        # Перетаскивание
        self.top_bar.bind("<Button-1>", self.start_drag)
        self.top_bar.bind("<B1-Motion>", self.on_drag)
        
        # ===== ОСНОВНОЙ КОНТЕЙНЕР =====
        main_container = tk.Frame(self.root, bg="#0b0e14")
        main_container.pack(fill="both", expand=True)
        
        # ===== ЛЕВОЕ МЕНЮ (КАК В NEW LAUNCHER) =====
        self.sidebar = tk.Frame(main_container, bg="#0f1219", width=280)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(self.sidebar, bg="#0f1219", height=70)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        
        self.logo = tk.Label(logo_frame, text="NEW LAUNCHER", bg="#0f1219", fg="#ffffff",
                             font=("Montserrat", 18, "bold"))
        self.logo.pack(pady=20)
        
        # Аватар
        avatar_frame = tk.Frame(self.sidebar, bg="#0f1219")
        avatar_frame.pack(pady=20)
        
        self.avatar_canvas = tk.Canvas(avatar_frame, width=80, height=80, bg="#0f1219", highlightthickness=0)
        self.avatar_canvas.pack()
        self.avatar_canvas.create_oval(5, 5, 75, 75, fill="#1e2530", outline="#2a3548", width=2)
        self.avatar_canvas.create_text(40, 40, text="👤", font=("Segoe UI", 32), fill="#8a9bb5")
        
        # Имя
        self.name_label = tk.Label(self.sidebar, text=self.data["username"], bg="#0f1219", 
                                   fg="white", font=("Montserrat", 12, "bold"))
        self.name_label.pack()
        
        # Баланс
        balance_frame = tk.Frame(self.sidebar, bg="#0f1219")
        balance_frame.pack(pady=10)
        
        self.balance_label = tk.Label(balance_frame, text=f"{self.data['balance']} ⭐", bg="#0f1219",
                                      fg="#ffb347", font=("Montserrat", 14, "bold"))
        self.balance_label.pack()
        
        # Меню (как в оригинале)
        menu_items = [
            ("🏠", "Главная", self.show_home),
            ("🛒", "Магазин", self.show_shop),
            ("🎮", "Игры", self.show_games),
            ("⚙️", "Настройки", self.show_settings),
            ("👤", "Профиль", self.show_profile)
        ]
        
        self.menu_buttons = []
        for icon, text, cmd in menu_items:
            btn_frame = tk.Frame(self.sidebar, bg="#0f1219", height=45)
            btn_frame.pack(fill="x", pady=2)
            btn_frame.pack_propagate(False)
            
            btn = tk.Label(btn_frame, text=f"{icon}  {text}", bg="#0f1219", fg="#8a9bb5",
                          font=("Montserrat", 11), cursor="hand2", anchor="w")
            btn.pack(fill="both", expand=True, padx=20, pady=12)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, b=btn: self.menu_hover(b, True))
            btn.bind("<Leave>", lambda e, b=btn: self.menu_hover(b, False))
            self.menu_buttons.append(btn)
        
        # ===== ПРАВЫЙ КОНТЕНТ =====
        self.content_frame = tk.Frame(main_container, bg="#0b0e14")
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Показываем главную
        self.show_home()
    
    def menu_hover(self, btn, enter):
        if enter:
            btn.config(fg="white", bg="#1a1f2a")
        else:
            btn.config(fg="#8a9bb5", bg="#0f1219")
    
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def start_animations(self):
        """Анимации как в New Launcher"""
        self.pulse_value = 0
        self.pulse_dir = 1
        
        def animate():
            self.pulse_value += 0.02 * self.pulse_dir
            if self.pulse_value >= 1:
                self.pulse_dir = -1
            elif self.pulse_value <= 0:
                self.pulse_dir = 1
            
            # Анимация для главной кнопки
            if hasattr(self, 'play_btn'):
                alpha = int(100 + 155 * abs(self.pulse_value))
                self.play_btn.config(bg=f"#{alpha:02x}3566")
            
            self.root.after(50, animate)
        
        animate()
    
    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
    
    def show_home(self):
        """Главная страница как в New Launcher"""
        self.clear_content()
        self.current_page = "home"
        
        # Приветствие
        welcome = tk.Label(self.content_frame, 
                          text=f"Добро пожаловать, {self.data['username']}!",
                          bg="#0b0e14", fg="white", font=("Montserrat", 28, "bold"))
        welcome.pack(pady=(40, 10))
        
        # Подпись
        subtitle = tk.Label(self.content_frame, text="Ваш персональный игровой лаунчер",
                           bg="#0b0e14", fg="#8a9bb5", font=("Montserrat", 12))
        subtitle.pack()
        
        # Центральная кнопка PLAY
        play_frame = tk.Frame(self.content_frame, bg="#0b0e14")
        play_frame.pack(expand=True)
        
        self.play_btn = tk.Button(play_frame, text="▶  PLAY  ◀",
                                  bg="#ff3566", fg="white", font=("Montserrat", 24, "bold"),
                                  bd=0, padx=50, pady=20, cursor="hand2",
                                  activebackground="#ff5e8e", activeforeground="white")
        self.play_btn.pack()
        
        # Эффект при наведении
        self.play_btn.bind("<Enter>", lambda e: self.play_btn.config(bg="#ff5e8e"))
        self.play_btn.bind("<Leave>", lambda e: self.play_btn.config(bg="#ff3566"))
        self.play_btn.bind("<Button-1>", lambda e: self.launch_game())
        
        # Новости
        news_frame = tk.Frame(self.content_frame, bg="#0f1219")
        news_frame.pack(pady=30, padx=40, fill="x")
        
        tk.Label(news_frame, text="НОВОСТИ", bg="#0f1219", fg="white",
                font=("Montserrat", 14, "bold")).pack(pady=10)
        
        news = [
            "• Обновление New Launcher 2.0",
            "• Новые игры в магазине",
            "• Скидки до 50% на премиум"
        ]
        
        for n in news:
            tk.Label(news_frame, text=n, bg="#0f1219", fg="#8a9bb5",
                    font=("Montserrat", 11)).pack(pady=3, anchor="w", padx=20)
    
    def show_shop(self):
        """Магазин как в New Launcher"""
        self.clear_content()
        self.current_page = "shop"
        
        tk.Label(self.content_frame, text="МАГАЗИН", 
                bg="#0b0e14", fg="white", font=("Montserrat", 24, "bold")).pack(pady=20)
        
        # Сетка товаров
        items_frame = tk.Frame(self.content_frame, bg="#0b0e14")
        items_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        products = [
            {"name": "СТАРТОВЫЙ", "price": 99, "stars": 100, "color": "#2a6f8f"},
            {"name": "ПРО", "price": 499, "stars": 550, "color": "#8f6f2a"},
            {"name": "VIP", "price": 999, "stars": 1200, "color": "#8f2a6f"},
            {"name": "ПРЕМИУМ", "price": 1999, "stars": 2500, "color": "#ff3566"}
        ]
        
        for i, p in enumerate(products):
            card = tk.Frame(items_frame, bg="#0f1219", relief="flat", bd=1)
            card.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="nsew", ipadx=20, ipady=20)
            
            tk.Label(card, text=p["name"], bg="#0f1219", fg="white",
                    font=("Montserrat", 16, "bold")).pack(pady=10)
            
            tk.Label(card, text=f"{p['stars']} ⭐", bg="#0f1219", fg="#ffb347",
                    font=("Montserrat", 24, "bold")).pack()
            
            tk.Label(card, text=f"{p['price']} ₽", bg="#0f1219", fg="#8a9bb5",
                    font=("Montserrat", 12)).pack(pady=5)
            
            btn = tk.Button(card, text="КУПИТЬ", bg="#ff3566", fg="white",
                           font=("Montserrat", 10, "bold"), bd=0, padx=25, pady=8,
                           command=lambda pp=p: self.buy_product(pp))
            btn.pack(pady=10)
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ff5e8e"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff3566"))
        
        items_frame.grid_columnconfigure(0, weight=1)
        items_frame.grid_columnconfigure(1, weight=1)
    
    def show_games(self):
        """Игры как в New Launcher"""
        self.clear_content()
        self.current_page = "games"
        
        tk.Label(self.content_frame, text="ИГРЫ", 
                bg="#0b0e14", fg="white", font=("Montserrat", 24, "bold")).pack(pady=20)
        
        games_frame = tk.Frame(self.content_frame, bg="#0b0e14")
        games_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        games = [
            {"name": "MINECRAFT", "icon": "⛏️", "version": "1.8.9", "players": "1.2M"},
            {"name": "CS:GO", "icon": "🔫", "version": "Latest", "players": "890K"},
            {"name": "DOTA 2", "icon": "🎮", "version": "7.35", "players": "450K"},
            {"name": "VALORANT", "icon": "🎯", "version": "8.0", "players": "1.1M"}
        ]
        
        for i, game in enumerate(games):
            card = tk.Frame(games_frame, bg="#0f1219", relief="flat", bd=1)
            card.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="nsew", ipadx=20, ipady=20)
            
            tk.Label(card, text=game["icon"], bg="#0f1219", fg="white",
                    font=("Segoe UI", 40)).pack(pady=10)
            
            tk.Label(card, text=game["name"], bg="#0f1219", fg="white",
                    font=("Montserrat", 16, "bold")).pack()
            
            tk.Label(card, text=f"Версия: {game['version']}", bg="#0f1219", fg="#8a9bb5",
                    font=("Montserrat", 10)).pack()
            
            tk.Label(card, text=f"👥 {game['players']} игроков", bg="#0f1219", fg="#ffb347",
                    font=("Montserrat", 10)).pack(pady=5)
            
            btn = tk.Button(card, text="ИГРАТЬ", bg="#ff3566", fg="white",
                           font=("Montserrat", 10, "bold"), bd=0, padx=25, pady=8)
            btn.pack(pady=10)
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ff5e8e"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff3566"))
        
        games_frame.grid_columnconfigure(0, weight=1)
        games_frame.grid_columnconfigure(1, weight=1)
    
    def show_settings(self):
        """Настройки как в New Launcher"""
        self.clear_content()
        self.current_page = "settings"
        
        tk.Label(self.content_frame, text="НАСТРОЙКИ", 
                bg="#0b0e14", fg="white", font=("Montserrat", 24, "bold")).pack(pady=20)
        
        settings_frame = tk.Frame(self.content_frame, bg="#0f1219")
        settings_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Имя
        tk.Label(settings_frame, text="Имя пользователя:", bg="#0f1219", fg="white",
                font=("Montserrat", 12)).pack(pady=(20, 5))
        
        name_entry = tk.Entry(settings_frame, bg="#1e2530", fg="white",
                             insertbackground="white", font=("Montserrat", 12), width=30)
        name_entry.insert(0, self.data["username"])
        name_entry.pack(pady=5)
        
        def save_name():
            self.data["username"] = name_entry.get()
            self.name_label.config(text=self.data["username"])
            self.save_data()
            messagebox.showinfo("Успех", "Имя сохранено!")
        
        tk.Button(settings_frame, text="СОХРАНИТЬ", bg="#ff3566", fg="white",
                 font=("Montserrat", 10, "bold"), command=save_name).pack(pady=10)
        
        # RAM
        tk.Label(settings_frame, text="Оперативная память (MB):", bg="#0f1219", fg="white",
                font=("Montserrat", 12)).pack(pady=(20, 5))
        
        ram_var = tk.StringVar(value="4096")
        ram_menu = ttk.Combobox(settings_frame, textvariable=ram_var, 
                                values=["2048", "4096", "6144", "8192"],
                                font=("Montserrat", 12), state="readonly")
        ram_menu.pack(pady=5)
        
        # Версия
        tk.Label(settings_frame, text="Версия Minecraft:", bg="#0f1219", fg="white",
                font=("Montserrat", 12)).pack(pady=(20, 5))
        
        version_var = tk.StringVar(value="1.8.9")
        version_menu = ttk.Combobox(settings_frame, textvariable=version_var,
                                   values=["1.8.9", "1.12.2", "1.16.5", "1.20.4"],
                                   font=("Montserrat", 12), state="readonly")
        version_menu.pack(pady=5)
        
        def save_settings():
            messagebox.showinfo("Успех", "Настройки сохранены!")
        
        tk.Button(settings_frame, text="СОХРАНИТЬ НАСТРОЙКИ", bg="#ff3566", fg="white",
                 font=("Montserrat", 12, "bold"), padx=30, pady=10, command=save_settings).pack(pady=30)
    
    def show_profile(self):
        """Профиль как в New Launcher"""
        self.clear_content()
        self.current_page = "profile"
        
        tk.Label(self.content_frame, text="ПРОФИЛЬ", 
                bg="#0b0e14", fg="white", font=("Montserrat", 24, "bold")).pack(pady=20)
        
        profile_frame = tk.Frame(self.content_frame, bg="#0f1219")
        profile_frame.pack(pady=20, padx=40, fill="both", expand=True)
        
        # Аватар
        avatar_frame = tk.Frame(profile_frame, bg="#0f1219")
        avatar_frame.pack(pady=20)
        
        avatar_canvas = tk.Canvas(avatar_frame, width=100, height=100, bg="#0f1219", highlightthickness=0)
        avatar_canvas.pack()
        avatar_canvas.create_oval(5, 5, 95, 95, fill="#1e2530", outline="#ff3566", width=3)
        avatar_canvas.create_text(50, 50, text="👤", font=("Segoe UI", 40), fill="white")
        
        # Информация
        info = [
            ("Имя:", self.data["username"]),
            ("ID:", str(random.randint(100000, 999999))),
            ("Статус:", "PREMIUM" if self.data["premium"] else "FREE"),
            ("Баланс:", f"{self.data['balance']} ⭐"),
            ("Игр в библиотеке:", str(len(self.data["games"])) if self.data["games"] else "0")
        ]
        
        for label, value in info:
            row = tk.Frame(profile_frame, bg="#0f1219")
            row.pack(fill="x", pady=10, padx=40)
            
            tk.Label(row, text=label, bg="#0f1219", fg="#8a9bb5",
                    font=("Montserrat", 12)).pack(side="left")
            
            tk.Label(row, text=value, bg="#0f1219", fg="white",
                    font=("Montserrat", 12, "bold")).pack(side="right")
    
    def buy_product(self, product):
        self.data["balance"] += product["stars"]
        self.balance_label.config(text=f"{self.data['balance']} ⭐")
        self.save_data()
        messagebox.showinfo("Успех", f"Куплен {product['name']}!\n+{product['stars']} ⭐")
    
    def launch_game(self):
        messagebox.showinfo("New Launcher", "Запуск Minecraft...\n\nПриятной игры!")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NewLauncher()
    app.run()