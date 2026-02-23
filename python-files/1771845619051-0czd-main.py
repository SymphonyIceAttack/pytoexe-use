import tkinter as tk
import sys
import os
import shutil
import random
import time
import threading
from pathlib import Path

class FullscreenGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        
        # На весь экран
        self.root.attributes('-fullscreen', True)
        
        # Правильное число - 77
        self.secret_number = 77
        self.attempt_made = False
        
        # Инициализируем переменную для папки
        self.test_folder = None
        
        # Переменные для эффектов глюков
        self.glitch_active = True
        self.noise_labels = []
        self.scanline_y = 0
        
        # Создаем тестовую папку
        self.create_test_folder()
        
        # Настройки внешнего вида
        self.root.configure(bg='black')
        
        # Устанавливаем курсор в виде черепа (если поддерживается системой)
        try:
            self.root.config(cursor="pirate")
        except:
            pass
        
        # Блокируем все способы закрытия
        self.block_all_closing()
        
        # Создаем интерфейс с устрашающим видом
        self.create_scary_widgets()
        
        # Окно всегда сверху
        self.root.attributes('-topmost', True)
        
        # Запускаем анимацию мигания
        self.blink_warning()
        
        # Запускаем все эффекты глюков
        self.start_glitch_effects()
        
        self.root.mainloop()
    
    def start_glitch_effects(self):
        """Запускает все эффекты глюков"""
        self.glitch_loop()
        self.scanline_animation()
        self.noise_animation()
        self.text_glitch()
    
    def glitch_loop(self):
        """Основной цикл глюков - случайные искажения"""
        if self.glitch_active:
            # Случайно искажаем цвета некоторых элементов
            if random.random() < 0.3:  # 30% шанс
                self.glitch_colors()
            
            # Случайно двигаем элементы
            if random.random() < 0.2:  # 20% шанс
                self.shift_elements()
            
            # Случайно показываем/скрываем символы
            if random.random() < 0.4:  # 40% шанс
                self.glitch_symbols()
            
            self.root.after(random.randint(50, 200), self.glitch_loop)
    
    def glitch_colors(self):
        """Искажение цветов"""
        try:
            # Случайно меняем цвета элементов
            elements = [self.title, self.demonic_text, self.instruction, 
                       self.warning_label, self.blood_text]
            
            for element in elements:
                if random.random() < 0.3:
                    # Сохраняем оригинальный цвет
                    if not hasattr(element, 'original_fg'):
                        element.original_fg = element.cget('fg')
                    
                    # Меняем на случайный цвет
                    glitch_colors = ['#ff0000', '#00ff00', '#0000ff', '#ff00ff', '#ffff00']
                    element.config(fg=random.choice(glitch_colors))
                    
                    # Возвращаем обратно через короткое время
                    self.root.after(random.randint(50, 150), 
                                  lambda e=element: e.config(fg=e.original_fg))
        except:
            pass
    
    def shift_elements(self):
        """Сдвиг элементов"""
        try:
            # Случайно сдвигаем некоторые элементы
            elements = [self.title, self.demonic_text, self.instruction, 
                       self.button, self.entry]
            
            for element in elements:
                if random.random() < 0.2:
                    # Сохраняем оригинальную позицию
                    if not hasattr(element, 'original_place_info'):
                        element.original_place_info = element.place_info()
                    
                    # Случайный сдвиг
                    dx = random.randint(-20, 20)
                    dy = random.randint(-10, 10)
                    
                    try:
                        element.place(relx=0.5 + dx/1000, rely=0.5 + dy/1000, anchor='center')
                    except:
                        pass
                    
                    # Возвращаем обратно
                    self.root.after(random.randint(50, 100), 
                                  lambda e=element: e.place(relx=0.5, rely=0.5, anchor='center'))
        except:
            pass
    
    def glitch_symbols(self):
        """Глючные символы по экрану"""
        try:
            for _ in range(random.randint(3, 8)):
                x = random.random()
                y = random.random()
                
                glitch_chars = ['$', '%', '&', '#', '@', '!', '?', '*', '➕', '➖', '=', '╳', '▀', '▄', '█']
                
                label = tk.Label(
                    self.root,
                    text=random.choice(glitch_chars),
                    font=("Courier", random.randint(12, 32)),
                    fg=random.choice(['red', 'green', 'blue', 'yellow', 'magenta']),
                    bg='black'
                )
                label.place(relx=x, rely=y)
                
                # Удаляем через короткое время
                self.root.after(random.randint(100, 300), label.destroy)
        except:
            pass
    
    def scanline_animation(self):
        """Анимация линии сканирования"""
        if self.glitch_active:
            try:
                # Удаляем старую линию
                if hasattr(self, 'scanline'):
                    self.scanline.destroy()
                
                # Создаем новую линию
                self.scanline = tk.Frame(
                    self.root,
                    bg='red',
                    height=2,
                    width=self.root.winfo_screenwidth()
                )
                self.scanline.place(relx=0, rely=self.scanline_y)
                
                # Двигаем линию вниз
                self.scanline_y += 0.02
                if self.scanline_y > 1:
                    self.scanline_y = 0
                
            except:
                pass
            
            self.root.after(50, self.scanline_animation)
    
    def noise_animation(self):
        """Анимация шума (случайные пиксели)"""
        if self.glitch_active:
            try:
                # Создаем случайный шум
                for _ in range(random.randint(5, 15)):
                    x = random.random()
                    y = random.random()
                    
                    noise = tk.Frame(
                        self.root,
                        bg=random.choice(['red', 'darkred', '#330000']),
                        width=random.randint(1, 4),
                        height=random.randint(1, 4)
                    )
                    noise.place(relx=x, rely=y)
                    
                    # Удаляем через короткое время
                    self.root.after(random.randint(50, 150), noise.destroy)
            except:
                pass
            
            self.root.after(random.randint(30, 80), self.noise_animation)
    
    def text_glitch(self):
        """Глюки текста - случайные символы в надписях"""
        if self.glitch_active:
            try:
                # Сохраняем оригинальные тексты
                if not hasattr(self, 'original_title'):
                    self.original_title = self.title.cget('text')
                    self.original_demonic = self.demonic_text.cget('text')
                    self.original_warning = self.warning_label.cget('text')
                
                if random.random() < 0.2:  # 20% шанс
                    # Глючим заголовок
                    glitched = ''.join([
                        random.choice([c, random.choice(['░', '▒', '▓', '█', '⎕', '⧈'])]) 
                        if random.random() < 0.3 else c 
                        for c in self.original_title
                    ])
                    self.title.config(text=glitched)
                    
                    # Возвращаем обратно
                    self.root.after(random.randint(100, 200), 
                                  lambda: self.title.config(text=self.original_title))
                
                if random.random() < 0.2:
                    # Глючим предупреждение
                    glitched = ''.join([
                        random.choice([c, random.choice(['⚠', '⚡', '💢', '❌', '‼'])]) 
                        if random.random() < 0.2 else c 
                        for c in self.original_warning
                    ])
                    self.warning_label.config(text=glitched)
                    
                    self.root.after(random.randint(100, 200), 
                                  lambda: self.warning_label.config(text=self.original_warning))
                
            except:
                pass
            
            self.root.after(random.randint(200, 400), self.text_glitch)
    
    def create_test_folder(self):
        """Создаем тестовую папку"""
        try:
            # Путь к папке в той же директории, где запущен скрипт
            self.test_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_FOLDER")
            
            # Удаляем если уже существует
            if os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
            
            # Создаем новую папку
            os.makedirs(self.test_folder)
            
            # Создаем несколько тестовых файлов
            for i in range(1, 4):
                file_path = os.path.join(self.test_folder, f"file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Test file {i}")
            
            print(f"[СОЗДАНО] Папка: {self.test_folder}")
            
        except Exception as e:
            print(f"[ОШИБКА] Не удалось создать папку: {e}")
            self.test_folder = None
    
    def delete_test_folder(self):
        """Удаляем тестовую папку"""
        try:
            if self.test_folder is not None and os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
                print(f"[УДАЛЕНО] Папка: {self.test_folder}")
                return True
        except Exception as e:
            print(f"[ОШИБКА] Не удалось удалить папку: {e}")
        return False
    
    def block_all_closing(self):
        """Блокируем все способы закрытия"""
        self.root.protocol("WM_DELETE_WINDOW", self.block_close)
        
        # Блокируем горячие клавиши
        keys = ["<Alt-F4>", "<Control-w>", "<Control-q>", "<Escape>", 
                "<F11>", "<Alt-Tab>", "<Super_L>", "<Super_R>", "<F4>",
                "<Control-Alt-Delete>", "<Control-Shift-Escape>"]
        
        for key in keys:
            try:
                self.root.bind(key, self.block_close)
            except:
                pass
        
        # Блокируем мышь
        self.root.bind("<Button-3>", self.block_close)
        self.root.bind("<Button-2>", self.block_close)
        
        # Блокируем функциональные клавиши
        for i in range(1, 13):
            self.root.bind(f"<F{i}>", self.block_close)
    
    def block_close(self, event=None):
        # Добавляем глючный эффект при попытке закрыть
        self.glitch_colors()
        self.glitch_symbols()
        return "break"
    
    def blink_warning(self):
        """Анимация мигающего текста"""
        try:
            current_color = self.warning_label.cget("fg")
            if current_color == "red":
                new_color = "darkred"
            else:
                new_color = "red"
            self.warning_label.config(fg=new_color)
        except:
            pass
        self.root.after(500, self.blink_warning)
    
    def create_scary_widgets(self):
        """Создаем устрашающий интерфейс"""
        
        # Кровавый фон с эффектом
        bloody_bg = tk.Frame(self.root, bg='black')
        bloody_bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # "Кровавые" полосы по краям
        for i in range(0, 10):
            tk.Frame(
                bloody_bg, 
                bg='darkred', 
                height=2, 
                width=self.root.winfo_screenwidth()
            ).place(relx=0, rely=i*0.1)
        
        # Череп в углу (символический)
        skull = tk.Label(
            bloody_bg,
            text="💀",
            font=("Arial", 48),
            fg="red",
            bg="black"
        )
        skull.place(relx=0.02, rely=0.02)
        
        # Второй череп
        skull2 = tk.Label(
            bloody_bg,
            text="💀",
            font=("Arial", 48),
            fg="red",
            bg="black"
        )
        skull2.place(relx=0.92, rely=0.02)
        
        # Основной контейнер с эффектом тени
        main_frame = tk.Frame(bloody_bg, bg='black', relief='solid', bd=5)
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Кровавый заголовок
        title_frame = tk.Frame(main_frame, bg='darkred', height=5)
        title_frame.pack(fill='x', pady=(0, 20))
        
        self.title = tk.Label(
            main_frame,
            text="☠ ТЫ В ЛОВУШКЕ ☠",
            font=("Arial", 50, "bold"),
            fg="red",
            bg="black",
            relief='ridge',
            bd=5
        )
        self.title.pack(pady=20, padx=40)
        
        # Демонический текст
        self.demonic_text = tk.Label(
            main_frame,
            text="👹 ВЫБОР БУДЕТ РОКОВЫМ 👹",
            font=("Arial", 20, "bold"),
            fg="darkred",
            bg="black"
        )
        self.demonic_text.pack(pady=10)
        
        # Инструкция с эффектом
        self.instruction = tk.Label(
            main_frame,
            text="ВВЕДИ ЧИСЛО ОТ 1 ДО 100:",
            font=("Courier", 24, "bold"),
            fg="red",
            bg="black",
            relief='sunken',
            bd=3
        )
        self.instruction.pack(pady=30, padx=50)
        
        # Поле ввода с красным свечением
        entry_frame = tk.Frame(main_frame, bg='darkred', padx=3, pady=3)
        entry_frame.pack(pady=20)
        
        self.entry = tk.Entry(
            entry_frame,
            font=("Courier", 36, "bold"),
            width=6,
            justify="center",
            bg="black",
            fg="red",
            insertbackground="red",
            relief='sunken',
            bd=5
        )
        self.entry.pack()
        self.entry.focus()
        
        # Кнопка с устрашающим видом
        button_frame = tk.Frame(main_frame, bg='darkred', padx=5, pady=5)
        button_frame.pack(pady=30)
        
        self.button = tk.Button(
            button_frame,
            text="⚔ ПРИЗВАТЬ СУДЬБУ ⚔",
            font=("Arial", 24, "bold"),
            bg="black",
            fg="red",
            activebackground="darkred",
            activeforeground="white",
            padx=60,
            pady=20,
            command=self.confirm_choice,
            relief='raised',
            bd=5,
            cursor="target"
        )
        self.button.pack()
        
        # Enter тоже работает
        self.root.bind("<Return>", lambda event: self.confirm_choice())
        
        # Мигающее предупреждение
        self.warning_label = tk.Label(
            self.root,
            text="⚠⚠⚠ ТОЛЬКО ОДНА ПОПЫТКА ⚠⚠⚠",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="black"
        )
        self.warning_label.place(relx=0.5, rely=0.85, anchor='center')
        
        # Кровавый текст внизу
        self.blood_text = tk.Label(
            self.root,
            text="ПРИ ОШИБКЕ ПАПКА БУДЕТ УНИЧТОЖЕНА",
            font=("Courier", 16, "bold"),
            fg="darkred",
            bg="black"
        )
        self.blood_text.place(relx=0.5, rely=0.92, anchor='center')
        
        # Случайные "кровавые" символы по краям
        for i in range(20):
            x = random.random()
            y = random.random()
            blood_symbol = tk.Label(
                bloody_bg,
                text=random.choice(["🩸", "🔪", "💀", "⚰️", "🕯️"]),
                font=("Arial", random.randint(16, 32)),
                fg="darkred",
                bg="black"
            )
            blood_symbol.place(relx=x, rely=y)
    
    def confirm_choice(self):
        """Подтверждение выбора"""
        
        if self.attempt_made:
            # Глючный эффект при повторной попытке
            self.glitch_colors()
            self.glitch_symbols()
            return
        
        number_text = self.entry.get().strip()
        if not number_text:
            return
        
        try:
            number = int(number_text)
            
            if number < 1 or number > 100:
                self.show_scary_error("ЧИСЛО ДОЛЖНО БЫТЬ ОТ 1 ДО 100!")
                return
            
            self.show_scary_confirmation(number)
            
        except ValueError:
            self.show_scary_error("ЭТО НЕ ЧИСЛО, СМЕРТНЫЙ!")
    
    def show_scary_error(self, message):
        """Устрашающая ошибка ввода"""
        error = tk.Toplevel(self.root)
        error.title("")
        error.configure(bg='black')
        error.attributes('-topmost', True)
        
        # Центрируем
        w, h = 500, 250
        x = (error.winfo_screenwidth() - w) // 2
        y = (error.winfo_screenheight() - h) // 2
        error.geometry(f"{w}x{h}+{x}+{y}")
        
        error.resizable(False, False)
        
        tk.Label(
            error,
            text="⚠️ ОШИБКА ⚠️",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=30)
        
        tk.Label(
            error,
            text=message,
            font=("Arial", 16),
            fg="red",
            bg="black",
            wraplength=450
        ).pack(pady=20)
        
        tk.Label(
            error,
            text="Попробуй снова...",
            font=("Arial", 14),
            fg="darkred",
            bg="black"
        ).pack()
        
        error.after(1500, error.destroy)
    
    def show_scary_confirmation(self, number):
        """Устрашающий диалог подтверждения"""
        
        confirm = tk.Toplevel(self.root)
        confirm.title("")
        confirm.configure(bg='black')
        confirm.attributes('-topmost', True)
        
        # Нельзя закрыть
        confirm.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Размер и положение
        w, h = 600, 350
        x = (confirm.winfo_screenwidth() - w) // 2
        y = (confirm.winfo_screenheight() - h) // 2
        confirm.geometry(f"{w}x{h}+{x}+{y}")
        
        confirm.resizable(False, False)
        
        tk.Label(
            confirm,
            text="☠ ТЫ УВЕРЕН? ☠",
            font=("Arial", 28, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=30)
        
        tk.Label(
            confirm,
            text=f"Ты выбрал число {number}",
            font=("Arial", 20),
            fg="darkred",
            bg="black"
        ).pack(pady=10)
        
        tk.Label(
            confirm,
            text="⚔ ЭТО ТВОЯ ЕДИНСТВЕННАЯ ПОПЫТКА ⚔",
            font=("Arial", 16, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=20)
        
        tk.Label(
            confirm,
            text="При ошибке папка будет уничтожена навсегда!",
            font=("Arial", 14),
            fg="darkred",
            bg="black"
        ).pack(pady=10)
        
        # Кнопка ДА с устрашающим видом
        yes_frame = tk.Frame(confirm, bg='darkred', padx=3, pady=3)
        yes_frame.pack(pady=30)
        
        yes_button = tk.Button(
            yes_frame,
            text="⚔ ДА, Я ГОТОВ К СУДЬБЕ ⚔",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="red",
            activebackground="darkred",
            activeforeground="white",
            padx=50,
            pady=15,
            command=lambda: self.check_number(number, confirm),
            relief='raised',
            bd=5,
            cursor="target"
        )
        yes_button.pack()
        
        # Enter на кнопку ДА
        confirm.bind("<Return>", lambda event: self.check_number(number, confirm))
        
        confirm.grab_set()
        confirm.focus()
    
    def check_number(self, number, confirm_window):
        """Проверка числа"""
        
        self.attempt_made = True
        confirm_window.destroy()
        
        if number == self.secret_number:  # 77
            self.show_scary_victory()
        else:
            self.show_scary_defeat_with_fake_hint(number)
    
    def show_scary_victory(self):
        """Устрашающая победа"""
        victory = tk.Toplevel(self.root)
        victory.title("")
        victory.configure(bg='black')
        victory.attributes('-topmost', True)
        
        victory.protocol("WM_DELETE_WINDOW", lambda: None)
        
        w, h = 550, 350
        x = (victory.winfo_screenwidth() - w) // 2
        y = (victory.winfo_screenheight() - h) // 2
        victory.geometry(f"{w}x{h}+{x}+{y}")
        
        victory.resizable(False, False)
        
        tk.Label(
            victory,
            text="🏆 ТЫ ПОБЕДИЛ СУДЬБУ 🏆",
            font=("Arial", 30, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=40)
        
        tk.Label(
            victory,
            text="Число 77 было правильным!",
            font=("Arial", 20),
            fg="red",
            bg="black"
        ).pack(pady=20)
        
        tk.Label(
            victory,
            text="Папка осталась нетронутой...",
            font=("Arial", 16),
            fg="darkred",
            bg="black"
        ).pack(pady=10)
        
        tk.Label(
            victory,
            text="Выход через 3 секунды",
            font=("Arial", 14),
            fg="gray",
            bg="black"
        ).pack(pady=20)
        
        victory.after(3000, self.exit_game)
        victory.grab_set()
    
    def show_scary_defeat_with_fake_hint(self, wrong_number):
        """Устрашающее поражение с обманной подсказкой на основе введённого числа"""
        
        # Генерируем обманное число (на 1 больше или меньше того, что ввёл пользователь)
        fake_correct = wrong_number + random.choice([-1, 1])
        
        # Убеждаемся, что обманное число в диапазоне 1-100
        if fake_correct < 1:
            fake_correct = 2
        elif fake_correct > 100:
            fake_correct = 99
        
        # Удаляем папку
        deleted = self.delete_test_folder()
        
        defeat = tk.Toplevel(self.root)
        defeat.title("")
        defeat.configure(bg='black')
        defeat.attributes('-topmost', True)
        
        defeat.protocol("WM_DELETE_WINDOW", lambda: None)
        
        w, h = 650, 450
        x = (defeat.winfo_screenwidth() - w) // 2
        y = (defeat.winfo_screenheight() - h) // 2
        defeat.geometry(f"{w}x{h}+{x}+{y}")
        
        defeat.resizable(False, False)
        
        tk.Label(
            defeat,
            text="💀 ТЫ ПРОИГРАЛ 💀",
            font=("Arial", 36, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=30)
        
        tk.Label(
            defeat,
            text=f"Ты выбрал {wrong_number}, но это неверно!",
            font=("Arial", 18),
            fg="red",
            bg="black"
        ).pack(pady=10)
        
        # Обманная подсказка (на основе введённого числа)
        tk.Label(
            defeat,
            text=f"⚠️ ПОДСКАЗКА: Нужно было ввести {fake_correct} ⚠️",
            font=("Arial", 22, "bold"),
            fg="darkred",
            bg="black"
        ).pack(pady=20)
        
        # Мелким шрифтом настоящая правда (почти незаметно)
        tk.Label(
            defeat,
            text=f"(на самом деле правильное число 77, но ты этого не узнаешь...)",
            font=("Arial", 8),
            fg="#330000",  # Очень тёмно-красный, почти невидимый
            bg="black"
        ).pack()
        
        if deleted:
            tk.Label(
                defeat,
                text="💢 ПАПКА System32 УНИЧТОЖЕНА 💢",
                font=("Arial", 18, "bold"),
                fg="red",
                bg="black"
            ).pack(pady=20)
        else:
            tk.Label(
                defeat,
                text="Не удалось уничтожить папку",
                font=("Arial", 16),
                fg="darkred",
                bg="black"
            ).pack(pady=20)
        
        tk.Label(
            defeat,
            text="Выход через 5 секунд...",
            font=("Arial", 14),
            fg="gray",
            bg="black"
        ).pack(pady=10)
        
        defeat.after(5000, self.exit_game)
        defeat.grab_set()
    
    def exit_game(self):
        """Выход"""
        self.glitch_active = False
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    print("=" * 60)
    print("☠ ЗАПУСК ПРОГРАММЫ ☠")
    print("=" * 60)
    print("📁 Создается тестовая папка")
    print("🎯 Попробуй угадать число 77")
    print("⚠️  При ошибке папка будет уничтожена")
    print("=" * 60)
    
    app = FullscreenGame()