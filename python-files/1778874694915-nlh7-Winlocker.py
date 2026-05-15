import tkinter as tk
import time
import hashlib
import random

class SimpleWinLocker:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🔒")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg='#0a0a2a')
        
        # Пароль (по умолчанию: 1234)
        self.password_hash = hashlib.sha256("1234".encode()).hexdigest()
        self.attempts = 0
        
        self.create_widgets()
        self.update_time()
        self.animate_background()
        
        # Защита от закрытия
        self.window.protocol("WM_DELETE_WINDOW", self.block_close)
    
    def block_close(self):
        pass
    
    def create_widgets(self):
        # Центральный фрейм
        center = tk.Frame(self.window, bg='#0a0a2a')
        center.place(relx=0.5, rely=0.4, anchor='center')
        
        # Красивый замок с анимацией
        self.lock_emoji = tk.Label(center, text="🔒", font=("Segoe UI", 70), 
                                    bg='#0a0a2a', fg='#ff6b6b')
        self.lock_emoji.pack(pady=10)
        
        # Заголовок
        tk.Label(center, text="ДОСТУП ЗАБЛОКИРОВАН", 
                font=("Segoe UI", 28, "bold"), 
                bg='#0a0a2a', fg='#ffffff').pack(pady=5)
        
        # Подзаголовок
        tk.Label(center, text="Введите пароль для разблокировки", 
                font=("Segoe UI", 14), 
                bg='#0a0a2a', fg='#888888').pack(pady=5)
        
        # Поле ввода
        self.password_entry = tk.Entry(center, show="•", 
                                        font=("Segoe UI", 18), 
                                        bg='#1e1e3e', fg='#ffffff',
                                        insertbackground='white',
                                        width=20, justify='center',
                                        relief='flat')
        self.password_entry.pack(pady=20)
        self.password_entry.bind('<Return>', self.check_password)
        self.password_entry.focus()
        
        # Кнопка
        self.unlock_btn = tk.Button(center, text="РАЗБЛОКИРОВАТЬ", 
                                     command=self.check_password,
                                     font=("Segoe UI", 12, "bold"),
                                     bg='#ff6b6b', fg='#ffffff',
                                     activebackground='#ff5252',
                                     relief='flat', padx=30, pady=10,
                                     cursor='hand2')
        self.unlock_btn.pack(pady=10)
        
        # Счётчик попыток
        self.attempts_label = tk.Label(center, text="", 
                                        font=("Segoe UI", 10), 
                                        bg='#0a0a2a', fg='#ff6b6b')
        self.attempts_label.pack(pady=5)
        
        # Время внизу
        self.time_label = tk.Label(self.window, text="", 
                                    font=("Segoe UI", 12), 
                                    bg='#0a0a2a', fg='#666666')
        self.time_label.place(relx=0.02, rely=0.95)
        
        # Подсказка
        tk.Label(self.window, text="💡 Подсказка: пароль из 4 цифр", 
                font=("Segoe UI", 10), 
                bg='#0a0a2a', fg='#444444').place(relx=0.5, rely=0.9, anchor='center')
        
        # Декоративные точки по углам
        corners = [(10, 10), (self.window.winfo_screenwidth()-20, 10), 
                   (10, self.window.winfo_screenheight()-20), 
                   (self.window.winfo_screenwidth()-20, self.window.winfo_screenheight()-20)]
        for x, y in corners:
            tk.Label(self.window, text="✦", font=("Segoe UI", 20), 
                    bg='#0a0a2a', fg='#ff6b6b').place(x=x, y=y)
    
    def update_time(self):
        current_time = time.strftime("%H:%M:%S | %d.%m.%Y")
        self.time_label.config(text=current_time)
        self.window.after(1000, self.update_time)
    
    def animate_background(self):
        """Плавная смена цвета фона"""
        colors = ['#0a0a2a', '#0f0f35', '#141440', '#0f0f35']
        current = colors[int(time.time() * 0.5) % len(colors)]
        self.window.configure(bg=current)
        self.window.after(2000, self.animate_background)
    
    def shake(self):
        """Дрожание окна"""
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        for _ in range(4):
            self.window.geometry(f"+{x+8}+{y}")
            self.window.update()
            time.sleep(0.02)
            self.window.geometry(f"+{x-8}+{y}")
            self.window.update()
            time.sleep(0.02)
        self.window.geometry(f"+{x}+{y}")
    
    def flash_red(self):
        """Красная вспышка при ошибке"""
        self.window.configure(bg='#440000')
        self.window.after(200, lambda: self.animate_background())
    
    def check_password(self, event=None):
        password = self.password_entry.get()
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if input_hash == self.password_hash:
            self.unlock()
        else:
            self.attempts += 1
            remaining = 5 - self.attempts
            
            self.shake()
            self.flash_red()
            self.password_entry.delete(0, tk.END)
            
            # Меняем замок на крестик
            self.lock_emoji.config(text="❌", fg='#ff4444')
            self.window.after(300, lambda: self.lock_emoji.config(text="🔒", fg='#ff6b6b'))
            
            if remaining > 0:
                self.attempts_label.config(text=f"❌ Неверно! Осталось {remaining} попыток")
                self.window.after(2000, lambda: self.attempts_label.config(text=""))
            else:
                self.timeout()
    
    def timeout(self):
        self.password_entry.config(state='disabled')
        self.unlock_btn.config(state='disabled')
        self.attempts_label.config(text="⏰ Слишком много попыток. Подождите 30 секунд", fg='#ffaa00')
        
        # Обратный отсчёт
        for i in range(30, 0, -1):
            self.attempts_label.config(text=f"⏰ Подождите {i} секунд...")
            self.window.update()
            time.sleep(1)
        
        self.attempts = 0
        self.password_entry.config(state='normal')
        self.unlock_btn.config(state='normal')
        self.password_entry.focus()
        self.attempts_label.config(text="✅ Можно пробовать снова", fg='#00ff88')
        self.window.after(2000, lambda: self.attempts_label.config(text=""))
    
    def unlock(self):
        """Красивая анимация разблокировки"""
        # Меняем замок на открытый
        self.lock_emoji.config(text="🔓", fg='#00ff88')
        self.unlock_btn.config(text="ДОБРО ПОЖАЛОВАТЬ!", bg='#00ff88')
        
        # Радужный эффект
        for i in range(10):
            r = random.randint(100, 255)
            g = random.randint(100, 255)
            b = random.randint(100, 255)
            self.window.configure(bg=f'#{r:02x}{g:02x}{b:02x}')
            self.window.update()
            time.sleep(0.05)
        
        time.sleep(0.5)
        
        # Закрываем
        self.window.attributes('-fullscreen', False)
        self.window.destroy()
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    locker = SimpleWinLocker()
    locker.run()