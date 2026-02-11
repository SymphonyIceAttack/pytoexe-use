import tkinter as tk
from tkinter import messagebox, ttk, colorchooser
from datetime import datetime
import pygame
import os
import random
import json
import math

class GrishaAndPolyaLoveStory:
    def __init__(self, root):
        self.root = root
        self.root.title("💕 Гриша + Поля")
        self.root.attributes('-fullscreen', True)
        
        # Инициализация музыки
        pygame.mixer.init()
        
        # ============ СКРЫТАЯ ПАПКА ДЛЯ СОХРАНЕНИЯ ============
        self.data_folder = os.path.join(os.path.dirname(__file__), ".lovestory")
        self.messages_file = os.path.join(self.data_folder, "message_count.json")
        self.events_file = os.path.join(self.data_folder, "events.json")
        
        # 📱 ЗАГРУЗКА ДАННЫХ ИЗ СКРЫТОЙ ПАПКИ
        self.message_count = self.load_message_count()
        self.custom_events = self.load_custom_events()
        
        # 🔥 ИСТОРИЯ ЛЮБВИ ГРИШИ И ПОЛИ 🔥
        self.relationship_data = {
            "names": {
                "boy": "Гриша",
                "girl": "Поля"
            },
            "start_date": datetime(2024, 9, 7, 20, 0),
            "important_moments": [
                {"date": "2024-09-07", "title": "💑 Начало истории", 
                 "description": "День, когда мы стали парой", "icon": "💕", "short": "Начало", "custom": False},
                {"date": "2024-09-22", "title": "💋 Первый поцелуй", 
                 "description": "22 сентября 2024 - самый нежный и долгожданный", "icon": "💋", "short": "Первый поцелуй", "custom": False},
                {"date": "2024-10-21", "title": "🎀 День рождения Поли", 
                 "description": "21 октября 2024 - самой красивой девочке исполнилось 15 лет! 🎂", 
                 "icon": "🎀", "short": "ДР Поли 2024", "custom": False},
                {"date": "2024-12-06", "title": "✨ Стали намного ближе", 
                 "description": "6 декабря 2024 - наши сердца бьются в унисон", "icon": "💫", "short": "Стали ближе", "custom": False},
                {"date": "2024-12-16", "title": "🎉 100 дней вместе", 
                 "description": "16 декабря 2024 - 100 дней счастья", "icon": "🎂", "short": "100 дней", "custom": False},
                {"date": "2025-01-01", "title": "🎄 Первый Новый год вместе", 
                 "description": "1 января 2025 - начали год в объятиях друг друга", "icon": "🎆", "short": "Новый год 2025", "custom": False},
                {"date": "2025-01-20", "title": "💞 Стали лучше понимать", 
                 "description": "20 января 2025 - научились слышать сердца", "icon": "💝", "short": "Понимание", "custom": False},
                {"date": "2025-02-20", "title": "💬 300к сообщений", 
                 "description": "20 февраля 2025 - 300 000 сообщений в чате", "icon": "💬", "short": "300к сообщений", "custom": False},
                {"date": "2025-03-01", "title": "🦋 Побороли черную полосу", 
                 "description": "1 марта 2025 - вместе мы можем всё!", "icon": "🦋", "short": "Победа над кризисом", "custom": False},
                {"date": "2025-03-07", "title": "🌺 Полгода отношений", 
                 "description": "7 марта 2025 - 6 месяцев любви", "icon": "🌺", "short": "6 месяцев", "custom": False},
                {"date": "2025-03-09", "title": "🔓 Поля освободилась от Family Link", 
                 "description": "9 марта 2025 - свобода!", "icon": "🔓", "short": "Freedom", "custom": False},
                {"date": "2025-03-10", "title": "🎂 День рождения Гриши", 
                 "description": "10 марта 2025 - 20 лет", "icon": "🎂", "short": "ДР Гриши", "custom": False},
                {"date": "2025-04-06", "title": "🌸 Поля начала любить себя", 
                 "description": "6 апреля 2025 - самая красивая учится быть счастливой", "icon": "🌸", "short": "Любовь к себе", "custom": False},
                {"date": "2025-04-29", "title": "📱 400к сообщений", 
                 "description": "29 апреля 2025 - еще 100 000 сообщений", "icon": "📱", "short": "400к сообщений", "custom": False},
                {"date": "2025-05-09", "title": "🎖️ Первое 9 мая вместе", 
                 "description": "9 мая 2025 - помним, чтим, любим", "icon": "🏆", "short": "9 мая вместе", "custom": False},
                {"date": "2025-06-27", "title": "⚔️ Победа над черной полосой", 
                 "description": "27 июня 2025 - очередная победа нашей любви", "icon": "⚔️", "short": "Снова победа", "custom": False},
                {"date": "2025-08-01", "title": "🌟 Стали чуточку ближе", 
                 "description": "1 августа 2025 - сердца сливаются сильнее", "icon": "🌟", "short": "Еще ближе", "custom": False},
                {"date": "2025-08-02", "title": "💭 500к сообщений", 
                 "description": "2 августа 2025 - полмиллиона сообщений", "icon": "💭", "short": "500к сообщений", "custom": False},
                {"date": "2025-09-07", "title": "🎊 Год отношений!", 
                 "description": "7 сентября 2025 - 365 дней любви", "icon": "🎊", "short": "1 год вместе", "custom": False},
                {"date": "2025-10-21", "title": "🎀 День рождения Поли", 
                 "description": "21 октября 2025 - самой красивой девочке в мире", "icon": "🎀", "short": "ДР Поли 2025", "custom": False},
                {"date": "2026-01-01", "title": "🎇 Второй Новый год вместе", 
                 "description": "1 января 2026 - снова встречаем чудо вдвоем", "icon": "🎇", "short": "Новый год 2026", "custom": False}
            ]
        }
        
        # ДОБАВЛЯЕМ СОХРАНЕННЫЕ ПОЛЬЗОВАТЕЛЬСКИЕ СОБЫТИЯ
        for event in self.custom_events:
            self.relationship_data["important_moments"].append(event)
        
        self.relationship_data["important_moments"].sort(key=lambda x: x["date"])
        
        self.setup_ui()
        self.start_animations()
        self.play_music()
    
    # ============ МЕТОДЫ ДЛЯ СОХРАНЕНИЯ В СКРЫТУЮ ПАПКУ ============
    
    def load_message_count(self):
        """Загружает количество сообщений из скрытой папки"""
        default_count = 670312
        
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            
            if os.path.exists(self.messages_file):
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    count = data.get('message_count', default_count)
                    print(f"📨 Загружено сообщений: {count:,}")
                    return count
            else:
                self.save_message_count(default_count)
                return default_count
        except Exception as e:
            print(f"❌ Ошибка загрузки сообщений: {e}")
            return default_count
    
    def save_message_count(self, count=None):
        """Сохраняет количество сообщений в скрытую папку"""
        if count is None:
            count = self.message_count
        
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            
            data = {
                'message_count': count,
                'last_updated': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                'updated_by': 'Гриша + Поля'
            }
            
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщений: {e}")
            return False
    
    def load_custom_events(self):
        """Загружает пользовательские события из скрытой папки"""
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)
                    print(f"📅 Загружено событий: {len(events)}")
                    return events
            else:
                return []
        except Exception as e:
            print(f"❌ Ошибка загрузки событий: {e}")
            return []
    
    def save_custom_events(self):
        """Сохраняет пользовательские события в скрытую папку"""
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_events, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Сохранено событий: {len(self.custom_events)}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения событий: {e}")
            return False
        
    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.root.winfo_screenwidth(), 
                               height=self.root.winfo_screenheight(), highlightthickness=0)
        self.canvas.pack()
        
        self.create_gradient()
        self.create_decorative_frame()
        self.create_floating_decorations()
        self.create_corner_decorations()
        self.create_scattered_decorations()
        self.create_title()
        self.create_timer()
        self.create_counters()
        self.create_timeline_line()
        self.create_music_player()
        self.create_future_goals()
        self.create_control_buttons()  # ИСПРАВЛЕННАЯ КНОПКА
        
    def create_gradient(self):
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        
        for i in range(0, height, 3):
            color = f'#{255-int(i/height*50):02x}{200-int(i/height*50):02x}{210-int(i/height*70):02x}'
            self.canvas.create_line(0, i, width, i, fill=color, width=3)
    
    def create_decorative_frame(self):
        """Создает декоративные рамки по краям экрана"""
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        # Основная рамка из сердечек
        for x in range(20, w-20, 40):
            self.canvas.create_text(x, 15, text='💕', font=('Arial', 12), fill='#ffb6c1')
            self.canvas.create_text(x, h-25, text='💕', font=('Arial', 12), fill='#ffb6c1')
        
        for y in range(20, h-20, 40):
            self.canvas.create_text(15, y, text='💕', font=('Arial', 12), fill='#ffb6c1')
            self.canvas.create_text(w-25, y, text='💕', font=('Arial', 12), fill='#ffb6c1')
        
        # Внутренняя рамка из цветочков
        for x in range(40, w-40, 80):
            self.canvas.create_text(x, 35, text='🌸', font=('Arial', 10), fill='#ff99cc')
            self.canvas.create_text(x, h-45, text='🌸', font=('Arial', 10), fill='#ff99cc')
        
        for y in range(40, h-40, 80):
            self.canvas.create_text(35, y, text='🌸', font=('Arial', 10), fill='#ff99cc')
            self.canvas.create_text(w-45, y, text='🌸', font=('Arial', 10), fill='#ff99cc')
    
    def create_floating_decorations(self):
        """Создает плавающие декорации по всему экрану"""
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        # Облака из сердечек
        decorations = [
            (w//6, h//5, '🌸'), (w//4, h//3, '✨'), (w//3, h//2, '💫'),
            (w*2//3, h//4, '🌟'), (w*3//4, h//3, '🌺'), (w*5//6, h//2, '🦋'),
            (w//5, h*2//3, '💕'), (w//2, h//6, '❤️'), (w*2//5, h*3//4, '💖'),
            (w*4//5, h*2//3, '💗'), (w//3, h*4//5, '💘'), (w*3//4, h*5//6, '💝'),
        ]
        
        for x, y, dec in decorations:
            self.canvas.create_text(x, y, text=dec, font=('Arial', 24), fill='#ffb6c1')
    
    def create_corner_decorations(self):
        """Создает красивые угловые декорации"""
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        # Верхний левый угол
        self.canvas.create_text(60, 60, text='❤️', font=('Arial', 32), fill='#ff69b4')
        self.canvas.create_text(100, 40, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(40, 100, text='✨', font=('Arial', 28), fill='#ffd700')
        
        # Верхний правый угол
        self.canvas.create_text(w-60, 60, text='❤️', font=('Arial', 32), fill='#ff69b4')
        self.canvas.create_text(w-100, 40, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(w-40, 100, text='✨', font=('Arial', 28), fill='#ffd700')
        
        # Нижний левый угол
        self.canvas.create_text(60, h-60, text='❤️', font=('Arial', 32), fill='#ff69b4')
        self.canvas.create_text(100, h-40, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(40, h-100, text='✨', font=('Arial', 28), fill='#ffd700')
        
        # Нижний правый угол
        self.canvas.create_text(w-60, h-60, text='❤️', font=('Arial', 32), fill='#ff69b4')
        self.canvas.create_text(w-100, h-40, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(w-40, h-100, text='✨', font=('Arial', 28), fill='#ffd700')
        
        # Декоративные линии по углам
        for i in range(3):
            self.canvas.create_line(20, 20 + i*5, 60, 60 + i*5, fill='#ffb6c1', width=1)
            self.canvas.create_line(w-20, 20 + i*5, w-60, 60 + i*5, fill='#ffb6c1', width=1)
            self.canvas.create_line(20, h-20 - i*5, 60, h-60 - i*5, fill='#ffb6c1', width=1)
            self.canvas.create_line(w-20, h-20 - i*5, w-60, h-60 - i*5, fill='#ffb6c1', width=1)
    
    def create_scattered_decorations(self):
        """Создает рассыпанные декорации по всему экрану"""
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        
        decorations = ['❤️', '💕', '💖', '💗', '🌸', '🌺', '✨', '🌟', '⭐', '🦋', '💫', '🎀']
        colors = ['#ffb6c1', '#ff99cc', '#ffc0cb', '#ffe4e1', '#ffdab9', '#e6e6fa']
        
        # Рассыпаем декорации случайным образом
        for _ in range(50):
            x = random.randint(50, w-50)
            y = random.randint(50, h-50)
            dec = random.choice(decorations)
            color = random.choice(colors)
            size = random.randint(12, 18)
            
            self.canvas.create_text(x, y, text=dec, font=('Arial', size), fill=color)
        
        # Добавляем маленькие звездочки
        for _ in range(100):
            x = random.randint(0, w)
            y = random.randint(0, h)
            self.canvas.create_text(x, y, text='✦', font=('Arial', 8), fill='#ffd700')
    
    def create_title(self):
        x = self.root.winfo_screenwidth() // 2
        
        # Декоративные элементы вокруг заголовка
        self.canvas.create_text(x-200, 55, text='✨', font=('Arial', 24), fill='#ffd700')
        self.canvas.create_text(x+200, 55, text='✨', font=('Arial', 24), fill='#ffd700')
        self.canvas.create_text(x-250, 55, text='🌸', font=('Arial', 20), fill='#ff99cc')
        self.canvas.create_text(x+250, 55, text='🌸', font=('Arial', 20), fill='#ff99cc')
        
        title_text = f"💖 {self.relationship_data['names']['boy']} + {self.relationship_data['names']['girl']} 💖"
        self.title = self.canvas.create_text(
            x, 55,
            text=title_text,
            font=('Arial', 48, 'bold'),
            fill='#ff1493',
            anchor='center'
        )
    
    def create_timer(self):
        x = self.root.winfo_screenwidth() // 2
        
        # Декоративные элементы вокруг таймера
        self.canvas.create_text(x-300, 132, text='⏰', font=('Arial', 20), fill='#ffd700')
        self.canvas.create_text(x+300, 132, text='⏰', font=('Arial', 20), fill='#ffd700')
        
        self.canvas.create_rectangle(x-350, 110, x+350, 155,
                                   fill='#4a4a4a', stipple='gray50', outline='#ff69b4', width=2)
        self.canvas.create_rectangle(x-348, 112, x+348, 153,
                                   fill='#2c3e50', outline='#ff1493', width=2)
        
        self.timer_display = self.canvas.create_text(
            x, 132,
            text="",
            font=('Arial', 28, 'bold'),
            fill='#ffffff',
            anchor='center'
        )
    
    def create_counters(self):
        now = datetime.now()
        delta = now - self.relationship_data["start_date"]
        
        # ============ ДНИ ВМЕСТЕ ============
        # Декоративные элементы
        self.canvas.create_text(30, 202, text='📅', font=('Arial', 24), fill='#ffd700')
        self.canvas.create_text(380, 202, text='💝', font=('Arial', 20), fill='#ff99cc')
        
        self.canvas.create_rectangle(40, 170, 370, 235,
                                   fill='#4a4a4a', stipple='gray50', outline='#ffd700', width=2)
        self.canvas.create_rectangle(45, 175, 365, 230,
                                   fill='#2c3e50', outline='#ff1493', width=2)
        
        days_text = f"💕 Дней вместе: {delta.days}"
        self.days_counter = self.canvas.create_text(
            60, 202,
            text=days_text,
            font=('Arial', 20, 'bold'),
            fill='white',
            anchor='w'
        )
        
        # ============ СООБЩЕНИЯ ============
        # Декоративные элементы
        self.canvas.create_text(self.root.winfo_screenwidth() - 550, 202, 
                               text='📨', font=('Arial', 24), fill='#ffd700')
        self.canvas.create_text(self.root.winfo_screenwidth() - 100, 202, 
                               text='💬', font=('Arial', 20), fill='#ff99cc')
        
        self.canvas.create_rectangle(
            self.root.winfo_screenwidth() - 530, 170,
            self.root.winfo_screenwidth() - 110, 235,
            fill='#4a4a4a', stipple='gray50', outline='#ffd700', width=2
        )
        self.canvas.create_rectangle(
            self.root.winfo_screenwidth() - 525, 175,
            self.root.winfo_screenwidth() - 115, 230,
            fill='#2c3e50', outline='#ff1493', width=2
        )
        
        msg_text = f"📨 Сообщений: {self.message_count:,}".replace(",", " ")
        self.msg_counter = self.canvas.create_text(
            self.root.winfo_screenwidth() - 515, 202,
            text=msg_text,
            font=('Arial', 20, 'bold'),
            fill='white',
            anchor='w'
        )
        
        # Кнопка под счетчиком сообщений
        msg_btn_frame = tk.Frame(self.root, bg='#ff69b4', bd=2, relief='raised')
        msg_btn_frame.place(
            x=self.root.winfo_screenwidth() - 360,
            y=240,
            width=180, 
            height=35
        )
        
        msg_btn = tk.Button(msg_btn_frame, text="✏️ Изменить количество", 
                          command=self.edit_message_count,
                          bg='#ff1493', fg='white',
                          font=('Arial', 10, 'bold'),
                          bd=0, padx=5, pady=2,
                          activebackground='#c71585', activeforeground='white')
        msg_btn.pack(expand=True, fill='both')
    
    def edit_message_count(self):
        """Окно для изменения количества сообщений"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📨 Обновить счетчик")
        dialog.geometry("450x400")
        dialog.configure(bg='#fff0f5')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Декоративная рамка
        main_frame = tk.Frame(dialog, bg='#fff0f5', bd=5, relief='ridge')
        main_frame.pack(padx=15, pady=15, fill='both', expand=True)
        
        # Декоративные элементы
        tk.Label(main_frame, text="✨", font=('Arial', 30), 
                bg='#fff0f5', fg='#ffd700').pack(pady=5)
        
        tk.Label(main_frame, text="💬 Текущее количество сообщений", 
                font=('Arial', 14, 'bold'), bg='#fff0f5', fg='#d63384').pack(pady=10)
        
        tk.Label(main_frame, text=f"{self.message_count:,} сообщений".replace(",", " "), 
                font=('Arial', 24, 'bold'), bg='#fff0f5', fg='#4b0082').pack(pady=5)
        
        # Информация о последнем сохранении
        try:
            if os.path.exists(self.messages_file):
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_updated = data.get('last_updated', 'неизвестно')
                    tk.Label(main_frame, text=f"🕐 Последнее обновление: {last_updated}", 
                            font=('Arial', 10), bg='#fff0f5', fg='#808080').pack(pady=5)
        except:
            pass
        
        tk.Label(main_frame, text="Введите новое значение:", 
                bg='#fff0f5', font=('Arial', 12)).pack(pady=10)
        
        entry = tk.Entry(main_frame, width=25, font=('Arial', 16), justify='center',
                        bd=3, relief='sunken')
        entry.insert(0, str(self.message_count))
        entry.pack(pady=5, ipady=5)
        entry.focus()
        entry.select_range(0, tk.END)
        
        # Кнопка сохранения
        save_btn = tk.Button(main_frame, text="💾 СОХРАНИТЬ", 
                           command=lambda: self.save_message_count_callback(dialog, entry),
                           bg='#98fb98', fg='#2e8b57',
                           font=('Arial', 14, 'bold'), 
                           padx=30, pady=10, bd=3, relief='raised',
                           activebackground='#90ee90', activeforeground='#006400')
        save_btn.pack(pady=15)
        
        # Кнопка отмены
        cancel_btn = tk.Button(main_frame, text="✕ Отмена", command=dialog.destroy,
                             bg='#ffb6c1', fg='#8b4513',
                             font=('Arial', 11), 
                             padx=20, pady=5, bd=2, relief='raised')
        cancel_btn.pack(pady=5)
    
    def save_message_count_callback(self, dialog, entry):
        """Сохранение количества сообщений"""
        try:
            new_count = int(entry.get().replace(" ", ""))
            if new_count > 0:
                self.message_count = new_count
                self.canvas.itemconfig(
                    self.msg_counter,
                    text=f"📨 Сообщений: {self.message_count:,}".replace(",", " ")
                )
                self.save_message_count(new_count)
                dialog.destroy()
                
                confirm = self.canvas.create_text(
                    self.root.winfo_screenwidth() - 515, 270,
                    text="✅ Сохранено!",
                    font=('Arial', 14, 'bold'),
                    fill='#32cd32',
                    anchor='w'
                )
                self.root.after(2000, lambda: self.canvas.delete(confirm))
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите число")
    
    def add_event_dialog(self):
        """Окно для добавления нового события"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💝 Новое воспоминание")
        dialog.geometry("600x700")
        dialog.configure(bg='#fff0f5')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Canvas с прокруткой
        canvas_frame = tk.Frame(dialog, bg='#fff0f5')
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg='#fff0f5', highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Фрейм для содержимого
        main_frame = tk.Frame(canvas, bg='#fff0f5', bd=3, relief='ridge')
        canvas.create_window((0, 0), window=main_frame, anchor='nw')
        
        # Декоративные элементы
        tk.Label(main_frame, text="✨💝✨", font=('Arial', 24), 
                bg='#fff0f5', fg='#ff69b4').pack(pady=10)
        
        tk.Label(main_frame, text="✨ Сохраним момент навсегда ✨", 
                font=('Arial', 18, 'bold'), bg='#fff0f5', fg='#d63384').pack(pady=10)
        
        tk.Label(main_frame, text="Добавьте новое памятное событие в вашу историю", 
                font=('Arial', 11, 'italic'), bg='#fff0f5', fg='#4b0082').pack(pady=5)
        
        # Дата
        tk.Label(main_frame, text="📅 Дата (ГГГГ-ММ-ДД):", 
                font=('Arial', 12, 'bold'), bg='#fff0f5', fg='#8b4513').pack(pady=5)
        date_entry = tk.Entry(main_frame, width=30, font=('Arial', 12), 
                             justify='center', bd=3, relief='sunken')
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack(pady=5, ipady=3)
        
        # Название
        tk.Label(main_frame, text="📌 Название события:", 
                font=('Arial', 12, 'bold'), bg='#fff0f5', fg='#8b4513').pack(pady=5)
        title_entry = tk.Entry(main_frame, width=30, font=('Arial', 12), 
                              bd=3, relief='sunken')
        title_entry.pack(pady=5, ipady=3)
        
        # Короткое название
        tk.Label(main_frame, text="✂️ Короткое название (для хронологии):", 
                font=('Arial', 12, 'bold'), bg='#fff0f5', fg='#8b4513').pack(pady=5)
        short_entry = tk.Entry(main_frame, width=30, font=('Arial', 12), 
                              bd=3, relief='sunken')
        short_entry.pack(pady=5, ipady=3)
        
        # Описание
        tk.Label(main_frame, text="📝 Описание:", 
                font=('Arial', 12, 'bold'), bg='#fff0f5', fg='#8b4513').pack(pady=5)
        desc_entry = tk.Text(main_frame, width=40, height=4, font=('Arial', 11),
                            bd=3, relief='sunken')
        desc_entry.pack(pady=5)
        
        # Иконка
        tk.Label(main_frame, text="🎨 Иконка (выберите):", 
                font=('Arial', 12, 'bold'), bg='#fff0f5', fg='#8b4513').pack(pady=5)
        
        icons_frame = tk.Frame(main_frame, bg='#fff0f5')
        icons_frame.pack(pady=5)
        
        icon_var = tk.StringVar(value="💝")
        icons = ["💝", "❤️", "💕", "💖", "💗", "✨", "🌟", "⭐", "🎉", "🎊", "🌸", "🌺", "🦋", "💫", "🎂", "🎀"]
        
        row, col = 0, 0
        for icon in icons:
            rb = tk.Radiobutton(icons_frame, text=icon, value=icon,
                               variable=icon_var, bg='#fff0f5', 
                               font=('Arial', 14), indicatoron=0,
                               width=3, height=1, bd=2, relief='raised')
            rb.grid(row=row, column=col, padx=3, pady=3)
            col += 1
            if col > 5:
                col = 0
                row += 1
        
        def save_event():
            date = date_entry.get()
            title = title_entry.get()
            short = short_entry.get()
            desc = desc_entry.get("1.0", tk.END).strip()
            icon = icon_var.get()
            
            if not title or not short or not desc:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля!")
                return
            
            new_event = {
                "date": date,
                "title": title,
                "description": desc,
                "icon": icon,
                "short": short[:18],
                "custom": True
            }
            
            self.custom_events.append(new_event)
            self.relationship_data["important_moments"].append(new_event)
            self.relationship_data["important_moments"].sort(key=lambda x: x["date"])
            
            self.save_custom_events()
            
            messagebox.showinfo("💕 Спасибо!", 
                              "✨ Новое воспоминание сохранено! ✨\n"
                              "Оно появится в хронологии после перезапуска.")
            dialog.destroy()
        
        tk.Button(main_frame, text="💖 Сохранить событие 💖", command=save_event,
                 bg='#ff99cc', font=('Arial', 14, 'bold'), 
                 padx=30, pady=10, bd=3, relief='raised',
                 activebackground='#ff69b4', activeforeground='white').pack(pady=20)
        
        tk.Button(main_frame, text="✕ Отмена", command=dialog.destroy,
                 bg='#ffb6c1', font=('Arial', 11), 
                 padx=20, pady=5, bd=2, relief='raised').pack(pady=10)
        
        tk.Label(main_frame, text="✨💕✨", font=('Arial', 20), 
                bg='#fff0f5', fg='#ffb6c1').pack(pady=10)
        
        # Обновление области прокрутки
        main_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind('<MouseWheel>', on_mousewheel)
        main_frame.bind('<MouseWheel>', on_mousewheel)
    
    def create_timeline_line(self):
        """ПРОКРУЧИВАЕМАЯ ХРОНОЛОГИЯ"""
        canvas_width = self.root.winfo_screenwidth()
        
        # ЗАГОЛОВОК С ДЕКОРАЦИЯМИ
        x = canvas_width // 2
        
        # Декоративные элементы вокруг заголовка
        self.canvas.create_text(x-300, 242, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(x+300, 242, text='🌸', font=('Arial', 24), fill='#ff99cc')
        self.canvas.create_text(x-350, 242, text='✨', font=('Arial', 28), fill='#ffd700')
        self.canvas.create_text(x+350, 242, text='✨', font=('Arial', 28), fill='#ffd700')
        
        self.canvas.create_text(
            x, 242,
            text="📜 ХРОНОЛОГИЯ НАШЕЙ ЛЮБВИ 📜",
            font=('Arial', 28, 'bold'),
            fill='#ff1493',
            anchor='center'
        )
        
        # ФРЕЙМ ДЛЯ ПРОКРУТКИ ХРОНОЛОГИИ
        timeline_container = tk.Frame(self.root, bg='#ffe4e1', bd=3, relief='ridge')
        timeline_container.place(x=50, y=290, width=canvas_width-100, height=220)
        
        # Декоративные элементы на рамке
        deco_frame = tk.Frame(timeline_container, bg='#ffe4e1')
        deco_frame.place(x=0, y=0, width=canvas_width-100, height=30)
        
        for i in range(0, canvas_width-100, 40):
            tk.Label(deco_frame, text='💕', bg='#ffe4e1', fg='#ffb6c1',
                    font=('Arial', 10)).place(x=i, y=0)
        
        # Canvas для прокрутки
        self.timeline_canvas = tk.Canvas(timeline_container, bg='#ffe4e1', height=180, 
                                        highlightthickness=0, bd=2, relief='sunken')
        
        # ГОРИЗОНТАЛЬНЫЙ СКРОЛЛБАР
        h_scrollbar = tk.Scrollbar(timeline_container, orient="horizontal", 
                                  command=self.timeline_canvas.xview)
        self.timeline_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # Размещаем canvas и скроллбар
        self.timeline_canvas.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        h_scrollbar.pack(side='bottom', fill='x', padx=5, pady=5)
        
        # Фрейм для линии времени
        self.timeline_frame = tk.Frame(self.timeline_canvas, bg='#ffe4e1')
        self.timeline_canvas.create_window((0, 0), window=self.timeline_frame, anchor='nw')
        
        # Рисуем линию времени
        self.draw_timeline_on_frame()
        
        # Привязываем обновление скролла к изменению размера
        self.timeline_frame.bind('<Configure>', self.on_timeline_frame_configure)
        
        # Добавляем колесико мыши для горизонтальной прокрутки
        self.timeline_canvas.bind('<MouseWheel>', self.on_timeline_mousewheel)
        self.timeline_frame.bind('<MouseWheel>', self.on_timeline_mousewheel)
    
    def on_timeline_frame_configure(self, event):
        self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox("all"))
    
    def on_timeline_mousewheel(self, event):
        self.timeline_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
    
    def draw_timeline_on_frame(self):
        moments = self.relationship_data["important_moments"]
        
        x_position = 50
        spacing = 220
        
        line_canvas_width = x_position + (len(moments) * spacing) + 200
        line = tk.Canvas(self.timeline_frame, width=line_canvas_width, height=160,
                        bg='#ffe4e1', highlightthickness=0)
        line.pack()
        
        y_line = 50
        y_dates = y_line + 45
        
        # Декоративная подложка для линии
        line.create_line(
            x_position-5, y_line, line_canvas_width-50, y_line,
            fill='#ffb6c1', width=12, dash=(15, 5)
        )
        
        # Основная линия
        line.create_line(
            x_position, y_line, line_canvas_width-50, y_line,
            fill='white', width=8, dash=(15, 5)
        )
        
        # Линия дат
        line.create_line(
            x_position, y_dates, line_canvas_width-50, y_dates,
            fill='#c0c0c0', width=2, dash=(5, 5)
        )
        
        for i, moment in enumerate(moments):
            x = x_position + (i * spacing)
            
            # Декоративные элементы вокруг маркеров
            line.create_text(x, y_line-30, text='✨', font=('Arial', 12), fill='#ffd700')
            line.create_text(x, y_line+30, text='✨', font=('Arial', 12), fill='#ffd700')
            
            # Декоративное свечение для особых событий
            if moment.get('custom', False):
                line.create_oval(
                    x-20, y_line-20, x+20, y_line+20,
                    fill='', outline='#ffd700', width=2, dash=(3, 3)
                )
            
            # Маркер
            line.create_oval(
                x-15, y_line-15, x+15, y_line+15,
                fill='', outline='#ffb6c1', width=2
            )
            
            # Основной маркер
            marker_color = '#ffd700' if moment.get('custom', False) else '#ff1493'
            line.create_oval(
                x-12, y_line-12, x+12, y_line+12,
                fill=marker_color, outline='white', width=2
            )
            
            # Иконка
            line.create_text(
                x, y_line,
                text=moment["icon"],
                font=('Arial', 14),
                anchor='center'
            )
            
            # Дата
            date_obj = datetime.strptime(moment["date"], "%Y-%m-%d")
            date_text = date_obj.strftime("%d.%m.%y")
            
            date_color = '#ff8c00' if moment.get('custom', False) else '#4b0082'
            line.create_text(
                x, y_dates + 12,
                text=date_text,
                font=('Arial', 11, 'bold'),
                fill=date_color,
                anchor='center'
            )
            
            # Название
            short_title = moment.get("short", moment["title"].split(' ', 1)[1] if ' ' in moment["title"] else moment["title"])
            if len(short_title) > 18:
                short_title = short_title[:18] + "."
            
            if moment.get('custom', False):
                short_title = "✨ " + short_title
            
            line.create_text(
                x, y_dates + 32,
                text=short_title,
                font=('Arial', 9, 'bold'),
                fill='#8b4513',
                anchor='center',
                width=150
            )
    
    def create_music_player(self):
        """МУЗЫКАЛЬНЫЙ ПЛЕЕР"""
        player_frame = tk.Frame(self.root, bg='#2c3e50', bd=3, relief='ridge')
        player_frame.place(x=70, y=530, width=400, height=170)
        
        # Градиентный фон
        player_canvas = tk.Canvas(player_frame, width=400, height=170, 
                                 bg='#2c3e50', highlightthickness=0)
        player_canvas.pack()
        
        # Декоративные элементы
        player_canvas.create_text(50, 20, text='♪', font=('Arial', 24), fill='#f1c40f')
        player_canvas.create_text(350, 20, text='♫', font=('Arial', 24), fill='#f1c40f')
        
        # Закругленный прямоугольник
        player_canvas.create_oval(0, 0, 20, 20, fill='#8e44ad', outline='#f1c40f', width=1)
        player_canvas.create_oval(380, 150, 400, 170, fill='#8e44ad', outline='#f1c40f', width=1)
        player_canvas.create_rectangle(10, 0, 390, 170, fill='#8e44ad', outline='')
        player_canvas.create_rectangle(0, 10, 400, 160, fill='#9b59b6', outline='#f1c40f', width=1)
        
        # Заголовок
        player_canvas.create_text(200, 40, text="🎵 МУЗЫКАЛЬНЫЙ ПЛЕЕР", 
                                 font=('Arial', 16, 'bold'), fill='#f1c40f',
                                 anchor='center')
        
        # Статус
        self.music_status_text = "🎵 our_song.mp3"
        player_canvas.create_text(200, 75, text=self.music_status_text,
                                      font=('Arial', 12, 'italic'), fill='#ecf0f1',
                                      anchor='center')
        
        # Кнопки управления
        controls_frame = tk.Frame(player_frame, bg='#34495e', bd=2, relief='sunken')
        controls_frame.place(x=100, y=100, width=200, height=45)
        
        # Кнопка Play/Pause
        self.play_btn = tk.Button(controls_frame, text="▶", font=('Arial', 14, 'bold'),
                                 bg='#2ecc71', fg='white', width=3, height=1,
                                 command=self.toggle_music,
                                 bd=1, relief='raised', activebackground='#27ae60')
        self.play_btn.pack(side='left', padx=10, pady=5)
        
        # Вращающийся индикатор
        self.spinner_label = tk.Label(controls_frame, text="⬤", font=('Arial', 16),
                                     bg='#34495e', fg='#f39c12')
        self.spinner_label.pack(side='left', padx=10)
        
        # Индикатор громкости
        volume_label = tk.Label(controls_frame, text="🔊", font=('Arial', 12),
                               bg='#34495e', fg='#ecf0f1')
        volume_label.pack(side='left', padx=5)
        
        # Прогресс-бар
        self.progress_frame = tk.Frame(player_frame, bg='#34495e', bd=1, relief='sunken')
        self.progress_frame.place(x=50, y=155, width=300, height=8)
        
        self.progress_canvas = tk.Canvas(self.progress_frame, width=300, height=8, 
                                        bg='#7f8c8d', highlightthickness=0)
        self.progress_canvas.pack()
        
        # Декоративные ноты
        player_canvas.create_text(50, 130, text='♪', font=('Arial', 20), 
                                fill='#f1c40f', anchor='center')
        player_canvas.create_text(350, 130, text='♫', font=('Arial', 24), 
                                fill='#f1c40f', anchor='center')
        
        self.animate_player()
    
    def animate_player(self):
        if pygame.mixer.music.get_busy():
            spinners = ['⬤', '◯', '⦿', '◎']
            current = getattr(self, 'spinner_index', 0)
            self.spinner_label.config(text=spinners[current % len(spinners)])
            self.spinner_index = current + 1
            
            width = self.progress_canvas.winfo_width()
            if width > 10:
                progress = (pygame.mixer.music.get_pos() / 1000) % 30 / 30
                self.progress_canvas.delete('progress')
                progress_width = width * progress
                self.progress_canvas.create_rectangle(
                    0, 0, progress_width, 8,
                    fill='#f1c40f', outline='', tags='progress'
                )
                self.progress_canvas.create_rectangle(
                    0, 0, progress_width, 4,
                    fill='#f39c12', outline='', tags='progress'
                )
        else:
            self.spinner_label.config(text="⬤")
            self.progress_canvas.delete('progress')
            self.progress_canvas.create_rectangle(
                0, 0, 0, 8, fill='#f1c40f', outline='', tags='progress'
            )
        
        self.root.after(200, self.animate_player)
    
    def create_future_goals(self):
        """Мечты"""
        frame = tk.Frame(self.root, bg='#e6e6fa', bd=3, relief='ridge')
        frame.place(x=self.root.winfo_screenwidth() - 470, y=530, width=400, height=180)
        
        # Декоративные элементы
        deco_frame = tk.Frame(frame, bg='#e6e6fa')
        deco_frame.place(x=0, y=0, width=400, height=30)
        
        for i in range(0, 400, 50):
            tk.Label(deco_frame, text='✨', bg='#e6e6fa', fg='#ffd700',
                    font=('Arial', 12)).place(x=i, y=0)
        
        inner_frame = tk.Frame(frame, bg='#e6e6fa', bd=0)
        inner_frame.pack(padx=10, pady=15, fill='both', expand=True)
        
        tk.Label(inner_frame, text="✨ НАШИ МЕЧТЫ ✨", 
                font=('Arial', 16, 'bold'), bg='#e6e6fa', fg='#8a2be2').pack(pady=5)
        
        goals_frame = tk.Frame(inner_frame, bg='#e6e6fa')
        goals_frame.pack(pady=5, padx=20, fill='both', expand=True)
        
        goals = [
            "1. дожить до 18 🌸",
            "2. съехаться 🏠", 
            "3. завести котенка 🐱",
            "4. сыграть свадьбу 💒",
            "5. переехать в другую страну ✈️",
            "6. завести ребенка 👶"
        ]
        
        for i, goal in enumerate(goals):
            cb = tk.Checkbutton(goals_frame, text=goal, font=('Arial', 12), 
                              bg='#e6e6fa', fg='#4b0082', selectcolor='#e6e6fa',
                              activebackground='#e6e6fa')
            cb.pack(pady=2, anchor='w')
    
    def create_control_buttons(self):
        """ИСПРАВЛЕННЫЕ КНОПКИ УПРАВЛЕНИЯ"""
        
        # Кнопка выхода с декором
        exit_frame = tk.Frame(self.root, bg='#ff6b6b', bd=2, relief='raised')
        exit_frame.place(x=20, y=20, width=110, height=45)
        
        tk.Label(exit_frame, text='💔', bg='#ff6b6b', fg='white',
                font=('Arial', 14)).place(x=5, y=10)
        
        exit_btn = tk.Button(exit_frame, text="Выйти", 
                           command=self.confirm_exit,
                           bg='#ff6b6b', fg='white',
                           font=('Arial', 12, 'bold'),
                           bd=0, padx=0, pady=0,
                           activebackground='#c0392b', activeforeground='white')
        exit_btn.place(x=35, y=10, width=60, height=25)
        
        # Кнопка добавления события с декором - ИСПРАВЛЕНА!
        add_frame = tk.Frame(self.root, bg='#3498db', bd=2, relief='raised')
        add_frame.place(x=140, y=20, width=190, height=45)
        
        tk.Label(add_frame, text='✨', bg='#3498db', fg='white',
                font=('Arial', 16)).place(x=10, y=10)
        
        add_btn = tk.Button(add_frame, text="Добавить событие", 
                          command=self.add_event_dialog,
                          bg='#3498db', fg='white',
                          font=('Arial', 12, 'bold'),
                          bd=0, padx=0, pady=0,
                          activebackground='#2980b9', activeforeground='white')
        add_btn.place(x=40, y=10, width=140, height=25)
    
    def update_counter(self):
        now = datetime.now()
        delta = now - self.relationship_data["start_date"]
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds // 60) % 60
        seconds = delta.seconds % 60
        
        self.canvas.itemconfig(
            self.days_counter,
            text=f"💕 Дней вместе: {days}"
        )
        
        time_string = f"❤️ {days}д {hours}ч {minutes}м {seconds}с"
        
        next_anniversary = datetime(2025, 9, 7)
        days_to = (next_anniversary - now).days
        if days_to > 0:
            time_string += f"  ✨ До года: {days_to}д"
        elif days_to == 0:
            time_string += f"  🎉 ГОД СЕГОДНЯ! 🎉"
        
        self.canvas.itemconfig(self.timer_display, text=time_string)
        self.root.after(1000, self.update_counter)
    
    def start_animations(self):
        self.update_counter()
        self.float_hearts()
    
    def float_hearts(self):
        x = random.randint(100, self.root.winfo_screenwidth() - 100)
        hearts = ['❤️', '💕', '💖', '💗', '💘', '💝']
        decorations = ['🌸', '✨', '🦋', '🌟', '💫']
        
        if random.random() > 0.5:
            symbol = random.choice(hearts)
        else:
            symbol = random.choice(decorations)
        
        heart = self.canvas.create_text(
            x, self.root.winfo_screenheight(),
            text=symbol,
            font=('Arial', random.randint(20, 25)),
            fill=random.choice(['#ff69b4', '#ff1493', '#ff6eb4', '#ff99cc', '#ffd700'])
        )
        
        def move():
            if self.canvas.coords(heart)[1] > -50:
                self.canvas.move(heart, random.randint(-2, 2), -random.randint(2, 4))
                self.root.after(50, move)
            else:
                self.canvas.delete(heart)
        
        move()
        self.root.after(random.randint(800, 1500), self.float_hearts)
    
    def toggle_music(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.play_btn.config(text="▶", bg='#2ecc71')
        else:
            pygame.mixer.music.unpause()
            self.play_btn.config(text="⏸", bg='#e74c3c')
    
    def play_music(self):
        try:
            music_path = os.path.join(os.path.dirname(__file__), "music", "our_song.mp3")
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.3)
                self.play_btn.config(text="⏸", bg='#e74c3c')
            else:
                print(f"❌ Музыка не найдена. Создайте папку 'music' и добавьте файл 'our_song.mp3'")
        except Exception as e:
            print(f"❌ Ошибка загрузки музыки: {e}")
    
    def confirm_exit(self):
        if messagebox.askyesno("💕 Выход", "Уходишь? 😢"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GrishaAndPolyaLoveStory(root)
    root.mainloop()