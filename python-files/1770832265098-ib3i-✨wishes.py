import tkinter as tk
from tkinter import messagebox
import random
import math
import json
import os
from datetime import datetime

class StarryWishes:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Звездное небо желаний ✨")
        self.root.geometry("1200x700")
        self.root.configure(bg='#0a0a1a')
        self.root.minsize(1100, 650)
        
        self.wishes = []
        self.stars = []
        self.wish_items = []
        self.program_dir = ""
        self.wishes_folder = ""
        
        # Создаем папку для желаний
        self.create_wishes_folder()
        
        # Загружаем сохраненные желания
        self.load_wishes()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Отображаем сохраненные желания
        self.refresh_wishes_list()
        
        # Запускаем анимации
        self.animate_shooting_stars()
        self.twinkle_stars()
    
    def create_wishes_folder(self):
        """Создает папку Wishes в директории с программой"""
        try:
            self.program_dir = os.path.dirname(os.path.abspath(__file__))
            self.wishes_folder = os.path.join(self.program_dir, "Wishes")
            
            if not os.path.exists(self.wishes_folder):
                os.makedirs(self.wishes_folder)
        except Exception as e:
            print(f"Ошибка при создании папки: {e}")
            self.wishes_folder = "Wishes"
            if not os.path.exists(self.wishes_folder):
                os.makedirs(self.wishes_folder)
    
    def setup_ui(self):
        """Создает весь интерфейс"""
        # Основной контейнер
        self.main_frame = tk.Frame(self.root, bg='#0a0a1a')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Левая панель - звездное небо
        self.sky_frame = tk.Frame(self.main_frame, bg='#0a0a1a', width=780, height=650)
        self.sky_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.sky_frame.pack_propagate(False)
        
        # Правая панель - список желаний
        self.wishes_frame = tk.Frame(self.main_frame, bg='#1a1a2e', width=350, height=650)
        self.wishes_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))
        self.wishes_frame.pack_propagate(False)
        
        # Добавляем рамку для правой панели
        self.add_frame_border(self.wishes_frame, '#4a4a8a')
        
        # Создаем контент
        self.create_sky_panel()
        self.create_wishes_panel()
    
    def add_frame_border(self, frame, color):
        """Добавляет красивую рамку с эффектом свечения"""
        # Внешняя рамка
        outer_border = tk.Frame(frame, bg=color, bd=1)
        outer_border.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Внутренняя рамка
        inner_border = tk.Frame(frame, bg='#1a1a2e', bd=2, relief=tk.GROOVE)
        inner_border.place(x=2, y=2, relwidth=1, relheight=1, width=-4, height=-4)
    
    def create_sky_panel(self):
        """Создает панель со звездным небом"""
        # Холст для звездного неба
        self.canvas = tk.Canvas(self.sky_frame, 
                              bg='#0a0a1a', 
                              highlightthickness=2,
                              highlightbackground='#4a4a8a',
                              highlightcolor='#6a6aaa',
                              width=780,
                              height=650)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Заливаем фон
        self.canvas.create_rectangle(0, 0, 780, 650, fill='#0a0a1a', outline='')
        
        # Декоративные уголки
        self.add_corner_decorations()
        
        # Звезды
        self.create_stars(300)
        
        # Луна
        self.create_moon()
        
        # Область ввода желания
        self.create_wishing_area()
        
        # Счетчик желаний
        self.create_wish_counter()
    
    def add_corner_decorations(self):
        """Добавляет декоративные уголки на холст"""
        # Левый верхний угол
        self.canvas.create_line(10, 5, 30, 5, fill='#6a6aaa', width=2)
        self.canvas.create_line(5, 10, 5, 30, fill='#6a6aaa', width=2)
        
        # Правый верхний угол
        self.canvas.create_line(750, 5, 770, 5, fill='#6a6aaa', width=2)
        self.canvas.create_line(775, 10, 775, 30, fill='#6a6aaa', width=2)
        
        # Левый нижний угол
        self.canvas.create_line(10, 645, 30, 645, fill='#6a6aaa', width=2)
        self.canvas.create_line(5, 620, 5, 640, fill='#6a6aaa', width=2)
        
        # Правый нижний угол
        self.canvas.create_line(750, 645, 770, 645, fill='#6a6aaa', width=2)
        self.canvas.create_line(775, 620, 775, 640, fill='#6a6aaa', width=2)
    
    def create_wishes_panel(self):
        """Создает панель со списком желаний"""
        # Внутренний отступ
        inner_frame = tk.Frame(self.wishes_frame, bg='#1a1a2e')
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок с рамкой
        title_frame = tk.Frame(inner_frame, bg='#25253a', bd=1, relief=tk.RAISED)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title = tk.Label(title_frame, 
                        text="✨ Мои желания ✨", 
                        font=('Arial', 16, 'bold'),
                        bg='#25253a',
                        fg='#ffd700',
                        pady=8)
        title.pack()
        
        # Декоративная линия
        self.create_decorative_line(inner_frame, '#4a4a8a')
        
        subtitle = tk.Label(inner_frame,
                          text="✧ Каждая звезда - это мечта ✧",
                          font=('Arial', 10, 'italic'),
                          bg='#1a1a2e',
                          fg='#b0c4de')
        subtitle.pack(pady=(5, 15))
        
        # Контейнер для списка желаний
        list_container = tk.Frame(inner_frame, bg='#1a1a2e', bd=1, relief=tk.SUNKEN)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas для прокрутки
        self.wishes_canvas = tk.Canvas(list_container,
                                      bg='#1a1a2e',
                                      highlightthickness=1,
                                      highlightbackground='#4a4a8a',
                                      width=300,
                                      height=400)
        self.wishes_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Стильный скроллбар
        scrollbar = tk.Scrollbar(list_container,
                                orient=tk.VERTICAL,
                                command=self.wishes_canvas.yview,
                                bg='#2a2a4a',
                                troughcolor='#0a0a1a',
                                width=12,
                                relief=tk.FLAT,
                                bd=0)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 1), pady=1)
        
        self.wishes_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Фрейм для содержимого
        self.wishes_content = tk.Frame(self.wishes_canvas, bg='#1a1a2e')
        self.wishes_canvas.create_window((0, 0), window=self.wishes_content,
                                        anchor='nw', width=280)
        
        self.wishes_content.bind('<Configure>', 
                               lambda e: self.wishes_canvas.configure(
                                   scrollregion=self.wishes_canvas.bbox('all')))
        
        # Привязываем колесико мыши
        def on_mousewheel(event):
            self.wishes_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.wishes_canvas.bind('<MouseWheel>', on_mousewheel)
        
        # Кнопка экспорта с дизайном
        export_frame = tk.Frame(inner_frame, bg='#1a1a2e')
        export_frame.pack(fill=tk.X, pady=15)
        
        export_btn = tk.Button(export_frame,
                             text="📤 Экспорт желаний",
                             font=('Arial', 11, 'bold'),
                             bg='#6a4a8a',
                             fg='white',
                             activebackground='#8a6aaa',
                             activeforeground='white',
                             bd=2,
                             relief=tk.RAISED,
                             padx=20,
                             pady=8,
                             cursor='hand2',
                             command=self.export_wishes)
        export_btn.pack(fill=tk.X)
        
        self.add_button_effects(export_btn)
    
    def create_decorative_line(self, parent, color):
        """Создает декоративную линию"""
        line_frame = tk.Frame(parent, bg=color, height=2)
        line_frame.pack(fill=tk.X, padx=20, pady=5)
    
    def add_button_effects(self, button):
        """Добавляет красивые эффекты для кнопки"""
        def on_enter(e):
            button.config(bg='#8a6aaa', relief=tk.GROOVE)
        
        def on_leave(e):
            button.config(bg='#6a4a8a', relief=tk.RAISED)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
    
    def create_stars(self, count):
        """Создает звезды"""
        star_colors = ['#ffffff', '#ffe4e1', '#e0ffff', '#fff0f5', '#f0e68c', '#ffd700']
        
        for _ in range(count):
            x = random.randint(20, 760)
            y = random.randint(20, 500)
            size = random.randint(1, 3)
            color = random.choice(star_colors)
            
            star = self.canvas.create_oval(x, y, x+size, y+size,
                                         fill=color, outline='',
                                         tags='star')
            
            self.stars.append({
                'id': star,
                'x': x,
                'y': y,
                'size': size,
                'color': color
            })
    
    def create_moon(self):
        """Создает луну с украшениями"""
        # Свечение луны
        for i in range(3):
            self.canvas.create_oval(
                708 - i*2, 28 - i*2, 772 + i*2, 92 + i*2,
                fill='', 
                outline=f'#{int(255-i*30):02x}{int(250-i*30):02x}{int(210-i*30):02x}',
                width=1,
                tags='moon_glow'
            )
        
        # Луна
        self.canvas.create_oval(710, 30, 770, 90,
                              fill='#fffacd', 
                              outline='#ffd700', 
                              width=2,
                              tags='moon')
        
        # Кратеры
        self.canvas.create_oval(725, 45, 745, 65,
                              fill='#f0e68c', 
                              outline='#e6d681', 
                              width=1,
                              tags='moon')
        self.canvas.create_oval(740, 55, 755, 70,
                              fill='#f0e68c', 
                              outline='#e6d681', 
                              width=1,
                              tags='moon')
        self.canvas.create_oval(715, 65, 730, 80,
                              fill='#f0e68c', 
                              outline='#e6d681', 
                              width=1,
                              tags='moon')
        
        # Звездочка рядом с луной
        self.canvas.create_text(690, 45, text='⭐', fill='#ffd700', font=('Arial', 12), tags='moon_star')
        self.canvas.create_text(780, 60, text='✨', fill='#ffffff', font=('Arial', 10), tags='moon_star')
    
    def create_wishing_area(self):
        """Создает красивую область для ввода желаний"""
        # Основная рамка
        frame_x1, frame_y1 = 40, 540
        frame_x2, frame_y2 = 740, 620
        
        # Внешняя рамка с эффектом свечения
        for i in range(3):
            offset = i * 2
            self.canvas.create_rectangle(
                frame_x1 - offset, frame_y1 - offset,
                frame_x2 + offset, frame_y2 + offset,
                outline=f'#{40+i*20:02x}{40+i*20:02x}{80+i*20:02x}',
                width=1,
                tags='wish_frame_glow'
            )
        
        # Основной фон
        self.canvas.create_rectangle(frame_x1, frame_y1, frame_x2, frame_y2,
                                   fill='#1a1a3a',
                                   outline='#6a6aaa',
                                   width=3,
                                   tags='wish_area')
        
        # Внутренняя рамка
        self.canvas.create_rectangle(frame_x1+3, frame_y1+3, frame_x2-3, frame_y2-3,
                                   outline='#4a4a8a',
                                   width=1,
                                   tags='wish_area')
        
        # Украшения по углам
        self.add_frame_corners(frame_x1, frame_y1, frame_x2, frame_y2)
        
        # Заголовок - теперь просто текст без рамки!
        self.canvas.create_text(390, 560,
                              text="✨ Загадай желание ✨",
                              font=('Arial', 12, 'bold'),
                              fill='#ffd700',
                              tags='wish_area')
        
        # Поле ввода с красивой рамкой
        entry_frame = tk.Frame(self.canvas,
                             bg='#ffd700',
                             bd=2,
                             relief=tk.RIDGE)
        
        self.wish_entry = tk.Entry(entry_frame,
                                 font=('Arial', 11),
                                 width=45,
                                 bg='#2a2a4a',
                                 fg='white',
                                 insertbackground='white',
                                 bd=0,
                                 relief=tk.FLAT)
        self.wish_entry.pack(padx=2, pady=2)
        
        self.canvas.create_window(390, 590, window=entry_frame, tags='wish_area')
        
        # Привязываем Enter
        self.wish_entry.bind('<Return>', self.add_wish)
        
        # Кнопка отправки
        self.create_send_button()
        
        # Подсказка
        self.canvas.create_text(390, 610,
                              text="✏️ Напиши желание и нажми кнопку или Enter",
                              font=('Arial', 9, 'italic'),
                              fill='#b0c4de',
                              tags='wish_area')
    
    def add_frame_corners(self, x1, y1, x2, y2):
        """Добавляет декоративные уголки к рамке"""
        # Левый верхний угол
        self.canvas.create_line(x1-2, y1-2, x1+10, y1-2, fill='#ffd700', width=2, tags='wish_corner')
        self.canvas.create_line(x1-2, y1-2, x1-2, y1+10, fill='#ffd700', width=2, tags='wish_corner')
        
        # Правый верхний угол
        self.canvas.create_line(x2+2, y1-2, x2-10, y1-2, fill='#ffd700', width=2, tags='wish_corner')
        self.canvas.create_line(x2+2, y1-2, x2+2, y1+10, fill='#ffd700', width=2, tags='wish_corner')
        
        # Левый нижний угол
        self.canvas.create_line(x1-2, y2+2, x1+10, y2+2, fill='#ffd700', width=2, tags='wish_corner')
        self.canvas.create_line(x1-2, y2+2, x1-2, y2-10, fill='#ffd700', width=2, tags='wish_corner')
        
        # Правый нижний угол
        self.canvas.create_line(x2+2, y2+2, x2-10, y2+2, fill='#ffd700', width=2, tags='wish_corner')
        self.canvas.create_line(x2+2, y2+2, x2+2, y2-10, fill='#ffd700', width=2, tags='wish_corner')
    
    def create_send_button(self):
        """Создает стильную кнопку отправки с правильной анимацией"""
        x, y = 670, 590
        
        # Сохраняем ID кнопки и текста для анимации
        self.send_button_id = self.canvas.create_rectangle(640, 575, 700, 605,
                                                         fill='#6a4a8a',
                                                         outline='#ffd700',
                                                         width=2,
                                                         tags='send_button')
        
        self.send_text_id = self.canvas.create_text(670, 590,
                                                  text="✨ Отправить",
                                                  font=('Arial', 10, 'bold'),
                                                  fill='white',
                                                  tags='send_button')
        
        # Привязываем события отдельно для каждого элемента
        for tag in ['send_button']:
            self.canvas.tag_bind(tag, '<Button-1>', self.add_wish)
            self.canvas.tag_bind(tag, '<Enter>', self.on_send_enter)
            self.canvas.tag_bind(tag, '<Leave>', self.on_send_leave)
    
    def on_send_enter(self, event):
        """Эффект при наведении на кнопку отправки"""
        self.canvas.itemconfig(self.send_button_id, fill='#8a6aaa', width=3)
        self.canvas.itemconfig(self.send_text_id, fill='#ffd700')
    
    def on_send_leave(self, event):
        """Эффект при уходе с кнопки отправки"""
        self.canvas.itemconfig(self.send_button_id, fill='#6a4a8a', width=2)
        self.canvas.itemconfig(self.send_text_id, fill='white')
    
    def create_wish_counter(self):
        """Создает красивый счетчик желаний"""
        # Фон счетчика с рамкой
        self.canvas.create_oval(670, 20, 730, 60,
                              fill='#1a1a3a',
                              outline='#ffd700',
                              width=3,
                              tags='counter_bg')
        
        self.counter_text = self.canvas.create_text(700, 40,
                                                  text="0",
                                                  font=('Arial', 18, 'bold'),
                                                  fill='#ffd700',
                                                  tags='counter')
        
        self.canvas.create_text(700, 75,
                              text="желаний",
                              font=('Arial', 9),
                              fill='#b0c4de',
                              tags='counter')
        
        # Маленькие звездочки вокруг счетчика
        self.canvas.create_text(660, 30, text='⭐', fill='#ffd700', font=('Arial', 10), tags='counter_star')
        self.canvas.create_text(740, 50, text='✨', fill='#ffd700', font=('Arial', 10), tags='counter_star')
    
    def add_wish_to_list(self, wish_text, wish_index):
        """Добавляет желание в список с красивым дизайном"""
        # Фрейм для одного желания
        wish_item = tk.Frame(self.wishes_content,
                           bg='#25253a',
                           bd=1,
                           relief=tk.RAISED)
        wish_item.pack(fill=tk.X, padx=8, pady=4)
        
        # Добавляем эффект наведения
        self.add_item_hover_effect(wish_item)
        
        # Контейнер для контента
        content_frame = tk.Frame(wish_item, bg='#25253a')
        content_frame.pack(fill=tk.X, padx=10, pady=8)
        
        # Звезда и номер
        number_label = tk.Label(content_frame,
                              text=f"⭐ {wish_index}.",
                              font=('Arial', 10, 'bold'),
                              bg='#25253a',
                              fg='#ffd700',
                              width=5,
                              anchor='w')
        number_label.pack(side=tk.LEFT)
        
        # Текст желания
        display_text = wish_text[:25] + '...' if len(wish_text) > 25 else wish_text
        wish_label = tk.Label(content_frame,
                            text=display_text,
                            font=('Arial', 10),
                            bg='#25253a',
                            fg='#e6e6fa',
                            anchor='w',
                            justify=tk.LEFT,
                            wraplength=170)
        wish_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Дата
        date_text = datetime.now().strftime('%d.%m')
        date_label = tk.Label(content_frame,
                            text=date_text,
                            font=('Arial', 8),
                            bg='#25253a',
                            fg='#8888aa')
        date_label.pack(side=tk.RIGHT)
        
        self.wish_items.append(wish_item)
        
        # Прокручиваем к новому желанию
        self.root.after(100, lambda: self.wishes_canvas.yview_moveto(1.0))
    
    def add_item_hover_effect(self, widget):
        """Добавляет эффект при наведении на элемент"""
        def on_enter(e):
            widget.config(bg='#2f2f4a', relief=tk.GROOVE)
            for child in widget.winfo_children():
                child.config(bg='#2f2f4a')
        
        def on_leave(e):
            widget.config(bg='#25253a', relief=tk.RAISED)
            for child in widget.winfo_children():
                child.config(bg='#25253a')
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def add_wish(self, event=None):
        """Добавляет новое желание"""
        wish_text = self.wish_entry.get().strip()
        if wish_text:
            wish_data = {
                'text': wish_text,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'id': len(self.wishes)
            }
            self.wishes.append(wish_data)
            
            # Очищаем поле
            self.wish_entry.delete(0, tk.END)
            
            # Анимация успешной отправки
            self.animate_success()
            
            # Добавляем в список
            self.add_wish_to_list(wish_text, len(self.wishes))
            
            # Обновляем счетчик
            self.update_wish_counter()
            
            # Сохраняем
            self.save_wishes()
    
    def animate_success(self):
        """Анимация успешной отправки"""
        # Вспышка на кнопке
        self.canvas.itemconfig(self.send_button_id, fill='#ffd700')
        self.canvas.itemconfig(self.send_text_id, fill='#6a4a8a')
        
        # Возвращаем исходный цвет
        self.root.after(100, lambda: self.canvas.itemconfig(self.send_button_id, fill='#6a4a8a'))
        self.root.after(100, lambda: self.canvas.itemconfig(self.send_text_id, fill='white'))
        
        # Падающая звезда
        x = random.randint(200, 600)
        y = 540
        
        star = self.canvas.create_text(x, y,
                                     text='✨',
                                     font=('Arial', 24),
                                     fill='#ffd700',
                                     tags='success_star')
        
        def move_star(step=0):
            if step < 30:
                self.canvas.move(star, 5, -3)
                self.root.after(20, lambda: move_star(step+1))
            else:
                self.canvas.delete(star)
        
        move_star()
    
    def update_wish_counter(self):
        """Обновляет счетчик желаний"""
        self.canvas.itemconfig(self.counter_text, text=str(len(self.wishes)))
    
    def clear_wishes_list(self):
        """Очищает список желаний"""
        for item in self.wish_items:
            item.destroy()
        self.wish_items = []
    
    def refresh_wishes_list(self):
        """Обновляет список желаний"""
        self.clear_wishes_list()
        for i, wish in enumerate(self.wishes, 1):
            if isinstance(wish, dict):
                text = wish.get('text', '')
            else:
                text = wish
            self.add_wish_to_list(text, i)
        self.update_wish_counter()
    
    def save_wishes(self):
        """Сохраняет желания в папку Wishes"""
        try:
            file_path = os.path.join(self.wishes_folder, "wishes_data.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.wishes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Не удалось сохранить желания: {e}")
    
    def load_wishes(self):
        """Загружает желания из папки Wishes"""
        try:
            file_path = os.path.join(self.wishes_folder, "wishes_data.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.wishes = json.load(f)
            else:
                self.wishes = []
        except Exception as e:
            print(f"Не удалось загрузить желания: {e}")
            self.wishes = []
    
    def export_wishes(self):
        """Экспортирует желания в текстовый файл"""
        if not self.wishes:
            messagebox.showinfo("Экспорт", "✨ У вас пока нет желаний для экспорта!")
            return
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"wishes_export_{timestamp}.txt"
            file_path = os.path.join(self.wishes_folder, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("✨✨✨ МОИ ЗАГАДАННЫЕ ЖЕЛАНИЯ ✨✨✨\n")
                f.write("═" * 60 + "\n\n")
                
                for i, wish in enumerate(self.wishes, 1):
                    if isinstance(wish, dict):
                        text = wish.get('text', '')
                        date = wish.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))
                    else:
                        text = wish
                        date = datetime.now().strftime('%Y-%m-%d %H:%M')
                    
                    f.write(f"{i:2d}. ⭐ {text}\n")
                    f.write(f"     📅 {date}\n\n")
                
                f.write("═" * 60 + "\n")
                f.write(f"✨ Всего желаний: {len(self.wishes)} ✨")
            
            messagebox.showinfo("Экспорт", 
                              f"✅ Желания сохранены в папку Wishes!\n📁 Файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Не удалось экспортировать желания: {e}")
    
    def twinkle_stars(self):
        """Мерцание звезд"""
        if self.stars:
            for star in random.sample(self.stars, min(15, len(self.stars))):
                if random.random() > 0.5:
                    self.canvas.itemconfig(star['id'], fill=star['color'])
                else:
                    self.canvas.itemconfig(star['id'], fill='#ffffff')
        
        self.root.after(800, self.twinkle_stars)
    
    def animate_shooting_stars(self):
        """Падающие звезды"""
        if random.random() < 0.2:
            x_start = random.randint(100, 600)
            y_start = random.randint(50, 300)
            
            star = self.canvas.create_text(x_start, y_start,
                                         text='✨',
                                         font=('Arial', random.choice([16, 18, 20])),
                                         fill=random.choice(['#ffffff', '#ffe4e1', '#fffacd']),
                                         tags='shooting_star')
            
            def fall(step=0):
                if step < 40:
                    self.canvas.move(star, 12, 8)
                    self.root.after(25, lambda: fall(step+1))
                else:
                    self.canvas.delete(star)
            
            fall()
        
        self.root.after(2000, self.animate_shooting_stars)

if __name__ == "__main__":
    root = tk.Tk()
    app = StarryWishes(root)
    root.mainloop()