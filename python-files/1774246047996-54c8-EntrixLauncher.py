import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
import math

# ===== ENTRIX LAUNCHER - CYBER NEON + DARK GAMING =====

class EntrixLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ENTRIX LAUNCHER")
        self.root.geometry("1200x750")
        self.root.configure(bg="#05070a")
        
        # Кастомная рамка
        self.root.overrideredirect(True)
        
        # Центрируем
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 750) // 2
        self.root.geometry(f"1200x750+{x}+{y}")
        
        # Загрузка данных
        self.load_data()
        
        # Переменные для анимации
        self.hover_buttons = {}
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Анимация свечения
        self.animate_glow()
        
    def load_data(self):
        """Загрузка данных"""
        if os.path.exists("entrix_data.json"):
            with open("entrix_data.json", "r") as f:
                self.user_data = json.load(f)
        else:
            self.user_data = {
                "username": "GHOST",
                "balance": 500,
                "level": 1,
                "cheats": [],
                "premium": False
            }
            self.save_data()
    
    def save_data(self):
        """Сохранение"""
        with open("entrix_data.json", "w") as f:
            json.dump(self.user_data, f)
    
    def setup_ui(self):
        """Создание интерфейса"""
        
        # Градиентный фон (кастомный)
        self.gradient_bg()
        
        # Верхняя панель (кастомная)
        top_bar = tk.Frame(self.root, bg="#0a0e14", height=55)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        
        # Логотип с неоном
        logo = tk.Label(top_bar, text="ENTRIX", bg="#0a0e14", fg="#00f2ff",
                        font=("Orbitron", 20, "bold"))
        logo.pack(side="left", padx=25, pady=12)
        
        # Неоновая подсветка логотипа
        logo_shadow = tk.Label(top_bar, text="ENTRIX", bg="#0a0e14", fg="#00f2ff",
                               font=("Orbitron", 20, "bold"))
        logo_shadow.place(x=27, y=13)
        
        # Кнопки управления
        control_frame = tk.Frame(top_bar, bg="#0a0e14")
        control_frame.pack(side="right", padx=15)
        
        # Минимизация
        self.create_neon_button(control_frame, "─", 35, 30, self.minimize_window, "#00f2ff")
        
        # Закрытие
        self.create_neon_button(control_frame, "✕", 35, 30, self.root.destroy, "#ff3366")
        
        # Перетаскивание окна
        top_bar.bind("<Button-1>", self.start_drag)
        top_bar.bind("<B1-Motion>", self.on_drag)
        logo.bind("<Button-1>", self.start_drag)
        
        # Основной контейнер
        main_container = tk.Frame(self.root, bg="#05070a")
        main_container.pack(fill="both", expand=True, padx=25, pady=20)
        
        # ===== ЛЕВОЕ МЕНЮ (ИКОНКИ) =====
        sidebar = tk.Frame(main_container, bg="#0a0e14", width=100)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Аватар
        avatar_frame = tk.Frame(sidebar, bg="#0a0e14")
        avatar_frame.pack(pady=30)
        
        avatar_circle = tk.Canvas(avatar_frame, width=70, height=70, bg="#0a0e14", highlightthickness=0)
        avatar_circle.pack()
        avatar_circle.create_oval(5, 5, 65, 65, fill="#1a1f2a", outline="#00f2ff", width=2)
        avatar_circle.create_text(35, 35, text="👤", font=("Segoe UI", 28), fill="#00f2ff")
        
        # Уровень
        level_label = tk.Label(sidebar, text=f"LVL {self.user_data['level']}", bg="#0a0e14",
                               fg="#00f2ff", font=("Orbitron", 10, "bold"))
        level_label.pack(pady=5)
        
        # Баланс с неоном
        balance_frame = tk.Frame(sidebar, bg="#0a0e14")
        balance_frame.pack(pady=15)
        
        tk.Label(balance_frame, text="⭐", bg="#0a0e14", fg="#ffd966", font=("Arial", 18)).pack()
        self.balance_label = tk.Label(balance_frame, text=str(self.user_data['balance']), 
                                      bg="#0a0e14", fg="#ffd966", font=("Orbitron", 16, "bold"))
        self.balance_label.pack()
        
        # Меню иконки
        menu_items = [
            ("🏠", "ГЛАВНАЯ", self.show_home),
            ("🛒", "МАГАЗИН", self.show_shop),
            ("⚡", "ЧИТЫ", self.show_cheats),
            ("⚙️", "НАСТРОЙКИ", self.show_settings),
            ("📊", "СТАТИСТИКА", self.show_stats)
        ]
        
        for icon, text, command in menu_items:
            btn_frame = tk.Frame(sidebar, bg="#0a0e14")
            btn_frame.pack(pady=8)
            
            btn = tk.Button(btn_frame, text=icon, bg="#0a0e14", fg="#ffffff",
                           font=("Segoe UI", 18), bd=0, padx=15, pady=8,
                           command=command, cursor="hand2")
            btn.pack()
            
            # Подпись
            tk.Label(btn_frame, text=text, bg="#0a0e14", fg="#5a6e8a",
                    font=("Orbitron", 8)).pack()
            
            # Ховер эффект
            btn.bind("<Enter>", lambda e, b=btn, t=text: self.on_hover(b, t, True))
            btn.bind("<Leave>", lambda e, b=btn, t=text: self.on_hover(b, t, False))
        
        # ===== ЦЕНТРАЛЬНЫЙ КОНТЕНТ =====
        self.content_frame = tk.Frame(main_container, bg="#05070a")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=(20, 0))
        
        # Показываем главную
        self.show_home()
    
    def gradient_bg(self):
        """Градиентный фон"""
        canvas = tk.Canvas(self.root, width=1200, height=750, bg="#05070a", highlightthickness=0)
        canvas.place(x=0, y=0)
        
        for i in range(750):
            r = 5 + int(30 * (1 - i/750))
            g = 7 + int(25 * (1 - i/750))
            b = 10 + int(40 * (1 - i/750))
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(0, i, 1200, i, fill=color, width=1)
        
        # Неоновые линии
        canvas.create_line(0, 55, 1200, 55, fill="#00f2ff", width=2, dash=(5, 5))
        canvas.create_line(0, 695, 1200, 695, fill="#ff3366", width=2, dash=(5, 5))
        
        self.bg_canvas = canvas
    
    def create_neon_button(self, parent, text, width, height, command, color):
        """Неоновая кнопка"""
        btn = tk.Button(parent, text=text, bg="#0a0e14", fg=color,
                       font=("Arial", 12, "bold"), bd=0, padx=width, pady=height//2,
                       command=command, cursor="hand2", activebackground="#0a0e14",
                       activeforeground=color)
        btn.pack(side="left", padx=5)
        return btn
    
    def on_hover(self, button, text, enter):
        """Эффект при наведении"""
        if enter:
            button.config(fg="#00f2ff")
        else:
            button.config(fg="#ffffff")
    
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        x = self.root.winfo_x() + event.x - self.drag_x
        y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def minimize_window(self):
        self.root.iconify()
    
    def animate_glow(self):
        """Анимация свечения"""
        self.glow_value = 0
        self.glow_direction = 1
        
        def update_glow():
            self.glow_value += 0.05 * self.glow_direction
            if self.glow_value >= 1:
                self.glow_direction = -1
            elif self.glow_value <= 0:
                self.glow_direction = 1
            
            intensity = int(100 + 155 * abs(self.glow_value))
            self.root.after(50, update_glow)
        
        update_glow()
    
    def show_home(self):
        """ГЛАВНАЯ СТРАНИЦА"""
        self.clear_content()
        
        # Центральная кнопка ИГРАТЬ
        play_frame = tk.Frame(self.content_frame, bg="#05070a")
        play_frame.pack(expand=True, fill="both")
        
        # Приветствие
        welcome = tk.Label(play_frame, 
                          text=f"ПРИВЕТСТВУЮ, {self.user_data['username']}",
                          bg="#05070a", fg="#ffffff", font=("Orbitron", 22, "bold"))
        welcome.pack(pady=40)
        
        # Неоновая подпись
        neon_text = tk.Label(play_frame, text="⚡ ГОТОВ К БИТВЕ ⚡",
                             bg="#05070a", fg="#00f2ff", font=("Orbitron", 12))
        neon_text.pack()
        
        # ОГРОМНАЯ КНОПКА ИГРАТЬ
        play_btn = tk.Button(play_frame, text="▶  ИГРАТЬ  ◀",
                             bg="#00f2ff", fg="#05070a", font=("Orbitron", 28, "bold"),
                             bd=0, padx=60, pady=20, cursor="hand2",
                             activebackground="#ff3366", activeforeground="white",
                             command=self.launch_game)
        play_btn.pack(pady=60)
        
        # Эффект свечения
        def glow_effect():
            for _ in range(3):
                play_btn.config(bg="#ff3366")
                play_frame.after(100)
                play_btn.config(bg="#00f2ff")
                play_frame.after(100)
        
        # Новости
        news_frame = tk.Frame(play_frame, bg="#0a0e14", relief="flat", bd=1)
        news_frame.pack(pady=20)
        
        tk.Label(news_frame, text="📢 ПОСЛЕДНИЕ НОВОСТИ", bg="#0a0e14", fg="#00f2ff",
                font=("Orbitron", 10, "bold")).pack(pady=10, padx=20)
        
        news = [
            "🔥 Обновление 2.0 - Новые читы!",
            "💎 Скидка 50% на все премиум читы!",
            "🏆 Турнир Entrix Cup - регистрация открыта!"
        ]
        
        for n in news:
            tk.Label(news_frame, text=n, bg="#0a0e14", fg="#8a9ac0",
                    font=("Segoe UI", 10)).pack(pady=3, padx=20)
    
    def show_shop(self):
        """МАГАЗИН"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="🛒 ПРЕМИУМ МАГАЗИН", 
                bg="#05070a", fg="#00f2ff", font=("Orbitron", 20, "bold")).pack(pady=20)
        
        # Создаём сетку карточек
        cards_frame = tk.Frame(self.content_frame, bg="#05070a")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        packs = [
            {"name": "СТАРТОВЫЙ", "price": 100, "stars": 100, "color": "#2a6f8f"},
            {"name": "ПРО", "price": 500, "stars": 550, "color": "#8f6f2a", "popular": True},
            {"name": "VIP", "price": 1000, "stars": 1200, "color": "#8f2a6f"},
            {"name": "LEGEND", "price": 2500, "stars": 3000, "color": "#ff3366"}
        ]
        
        for i, pack in enumerate(packs):
            card = tk.Frame(cards_frame, bg="#0a0e14", relief="flat", bd=2)
            card.grid(row=i//2, column=i%2, padx=15, pady=15, sticky="nsew")
            
            # Популярный бейдж
            if pack.get("popular"):
                pop_badge = tk.Label(card, text="🔥 ПОПУЛЯРНО", bg="#ff3366", fg="white",
                                    font=("Orbitron", 8, "bold"))
                pop_badge.pack(pady=(10, 0))
            
            tk.Label(card, text=pack["name"], bg="#0a0e14", fg="#00f2ff",
                    font=("Orbitron", 14, "bold")).pack(pady=15)
            
            tk.Label(card, text=f"{pack['stars']} ⭐️", bg="#0a0e14", fg="#ffd966",
                    font=("Orbitron", 18, "bold")).pack()
            
            tk.Label(card, text=f"{pack['price']} ₽", bg="#0a0e14", fg="#8a9ac0",
                    font=("Orbitron", 12)).pack(pady=5)
            
            buy_btn = tk.Button(card, text="КУПИТЬ", bg="#ff3366", fg="white",
                               font=("Orbitron", 10, "bold"), bd=0, padx=20, pady=8,
                               cursor="hand2", command=lambda p=pack: self.buy_pack(p))
            buy_btn.pack(pady=15)
            
            buy_btn.bind("<Enter>", lambda e, b=buy_btn: b.config(bg="#ff6666"))
            buy_btn.bind("<Leave>", lambda e, b=buy_btn: b.config(bg="#ff3366"))
        
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
    
    def show_cheats(self):
        """ЧИТЫ"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="⚡ АКТИВНЫЕ ЧИТЫ ⚡", 
                bg="#05070a", fg="#00f2ff", font=("Orbitron", 20, "bold")).pack(pady=20)
        
        cheats_frame = tk.Frame(self.content_frame, bg="#05070a")
        cheats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cheats = [
            {"name": "X-RAY", "desc": "Видеть сквозь стены", "price": 150, "icon": "👁️"},
            {"name": "KILL AURA", "desc": "Автоматические удары", "price": 350, "icon": "⚔️"},
            {"name": "FLY", "desc": "Режим полёта", "price": 200, "icon": "🪽"},
            {"name": "AIMBOT", "desc": "Автонаведение", "price": 300, "icon": "🎯"},
            {"name": "SPEED", "desc": "Увеличение скорости", "price": 180, "icon": "💨"},
            {"name": "ESP", "desc": "Подсветка игроков", "price": 250, "icon": "🔴"}
        ]
        
        for cheat in cheats:
            card = tk.Frame(cheats_frame, bg="#0a0e14", relief="flat", bd=1)
            card.pack(fill="x", pady=5)
            
            owned = cheat["name"] in self.user_data["cheats"]
            
            # Иконка
            tk.Label(card, text=cheat["icon"], bg="#0a0e14", fg="#00f2ff",
                    font=("Segoe UI", 24)).pack(side="left", padx=15, pady=10)
            
            # Инфо
            info_frame = tk.Frame(card, bg="#0a0e14")
            info_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            tk.Label(info_frame, text=cheat["name"], bg="#0a0e14", fg="#ffffff",
                    font=("Orbitron", 12, "bold")).pack(anchor="w")
            
            tk.Label(info_frame, text=cheat["desc"], bg="#0a0e14", fg="#8a9ac0",
                    font=("Segoe UI", 10)).pack(anchor="w")
            
            # Цена/Статус
            status_frame = tk.Frame(card, bg="#0a0e14")
            status_frame.pack(side="right", padx=15)
            
            if owned:
                tk.Label(status_frame, text="✅ АКТИВИРОВАН", bg="#0a0e14", fg="#00ff88",
                        font=("Orbitron", 10, "bold")).pack()
            else:
                tk.Label(status_frame, text=f"{cheat['price']} ⭐️", bg="#0a0e14", fg="#ffd966",
                        font=("Orbitron", 12, "bold")).pack()
                
                buy_btn = tk.Button(status_frame, text="АКТИВИРОВАТЬ", bg="#ff3366", fg="white",
                                   font=("Orbitron", 9, "bold"), bd=0, padx=10, pady=3,
                                   command=lambda c=cheat: self.buy_cheat(c))
                buy_btn.pack(pady=5)
    
    def show_settings(self):
        """НАСТРОЙКИ"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="⚙️ НАСТРОЙКИ ⚙️", 
                bg="#05070a", fg="#00f2ff", font=("Orbitron", 20, "bold")).pack(pady=20)
        
        settings_frame = tk.Frame(self.content_frame, bg="#0a0e14")
        settings_frame.pack(pady=20, padx=40, fill="both")
        
        # Имя игрока
        tk.Label(settings_frame, text="ИГРОК:", bg="#0a0e14", fg="#ffffff",
                font=("Orbitron", 12)).pack(pady=(20, 5))
        
        name_entry = tk.Entry(settings_frame, bg="#1a1f2a", fg="#00f2ff",
                             insertbackground="#00f2ff", font=("Orbitron", 12), width=30)
        name_entry.insert(0, self.user_data["username"])
        name_entry.pack(pady=5)
        
        def save_name():
            self.user_data["username"] = name_entry.get()
            self.save_data()
            messagebox.showinfo("Успех", "Имя сохранено!")
        
        tk.Button(settings_frame, text="СОХРАНИТЬ", bg="#00f2ff", fg="#05070a",
                 font=("Orbitron", 10, "bold"), command=save_name).pack(pady=10)
        
        # RAM
        tk.Label(settings_frame, text="ОПЕРАТИВНАЯ ПАМЯТЬ:", bg="#0a0e14", fg="#ffffff",
                font=("Orbitron", 12)).pack(pady=(20, 5))
        
        ram_var = tk.StringVar(value="4096")
        ram_menu = ttk.Combobox(settings_frame, textvariable=ram_var, 
                                values=["2048", "4096", "6144", "8192"],
                                font=("Orbitron", 12), state="readonly")
        ram_menu.pack(pady=5)
        
        # Версия
        tk.Label(settings_frame, text="ВЕРСИЯ MINECRAFT:", bg="#0a0e14", fg="#ffffff",
                font=("Orbitron", 12)).pack(pady=(20, 5))
        
        version_var = tk.StringVar(value="1.8.9")
        version_menu = ttk.Combobox(settings_frame, textvariable=version_var,
                                   values=["1.8.9", "1.12.2", "1.16.5", "1.20.4"],
                                   font=("Orbitron", 12), state="readonly")
        version_menu.pack(pady=5)
        
        def save_settings():
            messagebox.showinfo("Успех", "Настройки сохранены!")
        
        tk.Button(settings_frame, text="СОХРАНИТЬ ВСЕ", bg="#ff3366", fg="white",
                 font=("Orbitron", 12, "bold"), padx=30, pady=10, command=save_settings).pack(pady=30)
    
    def show_stats(self):
        """СТАТИСТИКА"""
        self.clear_content()
        
        tk.Label(self.content_frame, text="📊 СТАТИСТИКА ИГРОКА 📊", 
                bg="#05070a", fg="#00f2ff", font=("Orbitron", 20, "bold")).pack(pady=20)
        
        stats_frame = tk.Frame(self.content_frame, bg="#0a0e14")
        stats_frame.pack(pady=20, padx=40, fill="both")
        
        stats = [
            ("👤 ИМЯ:", self.user_data["username"]),
            ("⭐️ БАЛАНС:", f"{self.user_data['balance']} ⭐️"),
            ("⚡ АКТИВНО ЧИТОВ:", str(len(self.user_data["cheats"]))),
            ("💎 СТАТУС:", "PREMIUM" if self.user_data["premium"] else "FREE"),
            ("🏆 УРОВЕНЬ:", str(self.user_data["level"]))
        ]
        
        for label, value in stats:
            frame = tk.Frame(stats_frame, bg="#0a0e14")
            frame.pack(fill="x", pady=10, padx=20)
            
            tk.Label(frame, text=label, bg="#0a0e14", fg="#8a9ac0",
                    font=("Orbitron", 14)).pack(side="left")
            
            tk.Label(frame, text=value, bg="#0a0e14", fg="#00f2ff",
                    font=("Orbitron", 14, "bold")).pack(side="right")
        
        # Прогресс-бар уровня
        tk.Label(stats_frame, text="ПРОГРЕСС ДО СЛЕДУЮЩЕГО УРОВНЯ:", 
                bg="#0a0e14", fg="#ffffff", font=("Orbitron", 10)).pack(pady=(20, 5))
        
        progress = tk.Canvas(stats_frame, width=400, height=20, bg="#1a1f2a", highlightthickness=0)
        progress.pack(pady=5)
        progress.create_rectangle(0, 0, 200, 20, fill="#00f2ff", width=0)
        
        tk.Label(stats_frame, text="50% до 2 уровня", bg="#0a0e14", fg="#8a9ac0",
                font=("Orbitron", 9)).pack(pady=5)
    
    def buy_pack(self, pack):
        """Покупка пакета звёзд"""
        self.user_data["balance"] += pack["stars"]
        self.save_data()
        self.balance_label.config(text=str(self.user_data["balance"]))
        messagebox.showinfo("Успех", f"Куплен {pack['name']}!\n+{pack['stars']} ⭐️!")
    
    def buy_cheat(self, cheat):
        """Покупка чита"""
        if cheat["name"] in self.user_data["cheats"]:
            messagebox.showinfo("Информация", f"Чит {cheat['name']} уже активирован!")
            return
        
        if self.user_data["balance"] >= cheat["price"]:
            self.user_data["balance"] -= cheat["price"]
            self.user_data["cheats"].append(cheat["name"])
            self.save_data()
            self.balance_label.config(text=str(self.user_data["balance"]))
            messagebox.showinfo("Успех", f"Чит {cheat['name']} активирован!")
            self.show_cheats()
        else:
            messagebox.showerror("Ошибка", f"Недостаточно ⭐️! Нужно {cheat['price']}⭐️")
    
    def launch_game(self):
        """Запуск игры"""
        messagebox.showinfo("ENTRIX", f"Запуск Minecraft 1.8.9\nАктивировано читов: {len(self.user_data['cheats'])}\n\nПриятной игры! 🎮")
    
    def clear_content(self):
        """Очистка контента"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def run(self):
        self.root.mainloop()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    app = EntrixLauncher()
    app.run()