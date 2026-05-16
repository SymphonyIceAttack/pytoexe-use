import tkinter as tk
import random
import time

class StablePrank:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.title("⚠️ ВНИМАНИЕ ⚠️")
        
        # Отключаем крестик
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        self.progress = 0
        self.shaking = False
        
        # Большой заголовок
        self.title_label = tk.Label(
            self.root,
            text="⚠️ ВАШ КОМПЬЮТЕР ЗАБЛОКИРОВАН ⚠️",
            font=("Arial", 28, "bold"),
            fg="red",
            bg="black"
        )
        self.title_label.pack(pady=50)
        
        # Угрожающий текст
        self.threat_text = tk.Label(
            self.root,
            text="ОБНАРУЖЕНА УГРОЗА: TROJAN.WINLOCKER.TUNTUN\n\n"
                 "НЕ ВЫКЛЮЧАЙТЕ КОМПЬЮТЕР!\n"
                 "ВАШИ ДАННЫЕ ШИФРУЮТСЯ...\n\n"
                 "ТРЕБУЕТСЯ ВЕРИФИКАЦИЯ",
            font=("Arial", 16),
            fg="white",
            bg="black"
        )
        self.threat_text.pack(pady=30)
        
        # Прогресс-бар
        self.progress_frame = tk.Frame(self.root, bg="black")
        self.progress_frame.pack(pady=20)
        
        self.progress_bar = tk.Label(
            self.progress_frame,
            text="█░░░░░░░░░ 0%",
            font=("Courier", 20, "bold"),
            fg="red",
            bg="black"
        )
        self.progress_bar.pack()
        
        # Текст с предупреждением (будет мигать)
        self.warning_label = tk.Label(
            self.root,
            text="НЕ ПЫТАЙТЕСЬ ЗАКРЫТЬ ПРОГРАММУ!",
            font=("Arial", 12),
            fg="yellow",
            bg="black"
        )
        self.warning_label.pack(pady=20)
        
        # Запускаем атаку
        self.start_attack()
        
        self.root.mainloop()
    
    def update_progress(self):
        if self.progress < 100:
            self.progress += random.randint(1, 5)
            if self.progress > 100:
                self.progress = 100
            
            # Рисуем прогресс-бар символами
            filled = int(self.progress / 10)
            empty = 10 - filled
            bar = "█" * filled + "░" * empty
            self.progress_bar.config(text=f"{bar} {self.progress}%")
            
            # Меняем цвет в зависимости от прогресса
            if self.progress < 30:
                color = "red"
            elif self.progress < 70:
                color = "orange"
            else:
                color = "darkred"
            self.progress_bar.config(fg=color)
            
            # Страшные сообщения по ходу
            if self.progress == 50 and not hasattr(self, "msg1"):
                self.threat_text.config(
                    text="⚠️ ШИФРОВАНИЕ В ПРОЦЕССЕ!\n\n"
                         "ОБНАРУЖЕН ТРОЯН: TUNTUN.SAHUR\n\n"
                         "НЕ ВЫКЛЮЧАЙТЕ ПК!"
                )
                self.msg1 = True
            
            if self.progress == 80 and not hasattr(self, "msg2"):
                self.threat_text.config(
                    text="💀 ПОСЛЕДНИЙ ЭТАП ШИФРОВАНИЯ!\n\n"
                         "ТРОЯН АКТИВИРУЕТСЯ ЧЕРЕЗ 5 СЕКУНД...\n\n"
                         "ПОДГОТОВЬТЕСЬ К ВСТРЕЧЕ С ТУН-ТУН САХУРОМ! 💀"
                )
                self.msg2 = True
            
            self.root.after(150, self.update_progress)
        else:
            self.spawn_monster()
    
    def start_attack(self):
        # Запускаем мигание предупреждения
        self.blink_warning()
        # Запускаем прогресс
        self.root.after(500, self.update_progress)
        # Запускаем тряску через 2 секунды
        self.root.after(2000, self.start_shaking)
    
    def blink_warning(self):
        """Мигание текста"""
        if self.progress < 100:
            current_color = self.warning_label.cget("fg")
            new_color = "red" if current_color == "yellow" else "yellow"
            self.warning_label.config(fg=new_color)
            self.root.after(300, self.blink_warning)
    
    def start_shaking(self):
        self.shaking = True
        self.shake_screen()
    
    def shake_screen(self):
        if self.shaking and self.progress < 100:
            x = random.randint(-8, 8)
            y = random.randint(-5, 5)
            self.root.geometry(f"+{x}+{y}")
            self.root.after(40, self.shake_screen)
        else:
            self.root.geometry("+0+0")
    
    def spawn_monster(self):
        self.shaking = False
        self.root.geometry("+0+0")
        
        # Очищаем экран
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg="darkred")
        
        # ОГРОМНЫЙ монстр на весь экран
        monster_text = """
        ╔════════════════════════════════════════╗
        ║                                        ║
        ║     👹 ТУН-ТУН САХУР 👹               ║
        ║                                        ║
        ║        🕺 ТВЕРК-ТВЕРК 🕺               ║
        ║                                        ║
        ║    ОН ТЕПЕРЬ В ТВОЁМ КОМПЬЮТЕРЕ!       ║
        ║                                        ║
        ║    ПОЙМАЙ МЕНЯ, ЕСЛИ СМОЖЕШЬ...       ║
        ║                                        ║
        ╚════════════════════════════════════════╝
        """
        
        monster_label = tk.Label(
            self.root,
            text=monster_text,
            font=("Courier", 18, "bold"),
            fg="yellow",
            bg="darkred",
            justify="center"
        )
        monster_label.pack(expand=True)
        
        # Маленький мигающий текст внизу
        dance_label = tk.Label(
            self.root,
            text="💃🕺💃🕺💃🕺💃🕺💃🕺",
            font=("Arial", 20),
            fg="white",
            bg="darkred"
        )
        dance_label.pack(pady=20)
        
        # Анимируем танцующие символы
        def animate_dance():
            symbols = ["💃", "🕺", "💃", "🕺", "👹", "🕺", "💃", "👹"]
            i = 0
            while True:
                try:
                    new_text = " ".join([symbols[(i + j) % len(symbols)] for j in range(10)])
                    dance_label.config(text=new_text)
                    i += 1
                    self.root.update()
                    time.sleep(0.2)
                except:
                    break
        
        # Запускаем анимацию в отдельном потоке (но safe way)
        def animate():
            try:
                symbols = ["💃", "🕺", "💃", "🕺", "👹"]
                i = 0
                for _ in range(50):  # 10 секунд анимации
                    new_text = " ".join([symbols[(i + j) % len(symbols)] for j in range(8)])
                    dance_label.config(text=new_text)
                    self.root.update()
                    time.sleep(0.15)
                    i += 1
            except:
                pass
        
        self.root.after(0, lambda: self.safe_animate(dance_label))
        
        # Кнопка выхода появится через 5 секунд
        self.root.after(5000, self.show_exit_button)
    
    def safe_animate(self, dance_label):
        """Безопасная анимация"""
        try:
            symbols = ["💃", "🕺", "💃", "🕺", "👹"]
            for _ in range(30):
                if not self.root.winfo_exists():
                    break
                text = " ".join(random.choices(symbols, k=10))
                dance_label.config(text=text)
                self.root.update()
                time.sleep(0.15)
        except:
            pass
    
    def show_exit_button(self):
        """Показываем кнопку выхода"""
        exit_btn = tk.Button(
            self.root,
            text="😅 ЭТО БЫЛА ШУТКА! НАЖМИ СЮДА 😅",
            font=("Arial", 18, "bold"),
            bg="green",
            fg="white",
            command=self.finish
        )
        exit_btn.pack(pady=30)
    
    def finish(self):
        """Завершаем программу с юмором"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg="green")
        
        end_text = """
        
        😂 ХА-ХА, ЭТО БЫЛА ШУТКА! 😂
        
        НИКАКОГО ВИРУСА НЕ БЫЛО
        
        ТВОЙ КОМПЬЮТЕР В БЕЗОПАСНОСТИ
        
        ТУН-ТУН САХУР ГОВОРИТ: "ДО НОВЫХ ВСТРЕЧ!"
        
        ОКНО ЗАКРОЕТСЯ ЧЕРЕЗ 5 СЕКУНД
        
        """
        
        label = tk.Label(
            self.root,
            text=end_text,
            font=("Courier", 16, "bold"),
            fg="white",
            bg="green",
            justify="center"
        )
        label.pack(expand=True)
        
        self.root.after(5000, self.root.destroy)

if __name__ == "__main__":
    StablePrank()