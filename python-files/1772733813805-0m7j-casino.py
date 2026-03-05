import tkinter as tk
from tkinter import ttk, messagebox
import winsound
import threading
import time

class CasinoHack:
    def __init__(self, root):
        self.root = root
        self.root.title("Взлом казино")
        self.root.geometry("400x230")
        self.root.resizable(False, False)
        
        # Данные
        self.progress = 14
        self.stolen = 12050
        self.total = 70055020
        self.is_hacking = False
        
        # Центрируем окно
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (230 // 2)
        self.root.geometry(f'400x230+{x}+{y}')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        tk.Label(self.root, text="Взлом казино", font=("Segoe UI", 14, "bold")).pack(pady=5)
        
        # Процент
        self.percent_label = tk.Label(self.root, text="Казино взломано на 14%", font=("Segoe UI", 9))
        self.percent_label.pack()
        
        # Баланс
        self.balance_label = tk.Label(self.root, text=f"Выкачано {self.stolen:,} руб. из {self.total:,} руб.", font=("Segoe UI", 9))
        self.balance_label.pack()
        
        # Прогрессбар (красный)
        self.progress_bar = ttk.Progressbar(self.root, length=360, value=14, maximum=100)
        self.progress_bar.pack(pady=5)
        
        # Делаем прогрессбар красным через стиль
        style = ttk.Style()
        style.theme_use('default')
        style.configure("red.Horizontal.TProgressbar", foreground='red', background='red', thickness=12)
        self.progress_bar.configure(style="red.Horizontal.TProgressbar")
        
        # Вопрос
        self.question_label = tk.Label(self.root, text="Продолжить?", font=("Segoe UI", 9))
        self.question_label.pack(pady=5)
        
        # Кнопки
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.yes_btn = tk.Button(btn_frame, text="Да", width=10, command=self.start_hack)
        self.yes_btn.pack(side=tk.LEFT, padx=5)
        
        self.no_btn = tk.Button(btn_frame, text="Нет", width=10, command=self.cancel_hack)
        self.no_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = tk.Button(btn_frame, text="Отменить взлом", width=15, command=self.cancel_hack, state='disabled')
    
    def start_hack(self):
        self.is_hacking = True
        self.yes_btn.pack_forget()
        self.no_btn.pack_forget()
        self.question_label.pack_forget()
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        threading.Thread(target=self.hack_process, daemon=True).start()
    
    def hack_process(self):
        while self.progress < 100 and self.is_hacking:
            time.sleep(1)  # 1 секунда = 1%
            self.progress += 1
            self.stolen = int(self.total * self.progress / 100)
            
            # Обновляем интерфейс
            self.root.after(0, self.update_ui)
        
        if self.progress >= 100:
            self.root.after(0, self.show_victory)
    
    def update_ui(self):
        self.percent_label.config(text=f"Казино взломано на {self.progress}%")
        self.balance_label.config(text=f"Выкачано {self.stolen:,} руб. из {self.total:,} руб.")
        self.progress_bar['value'] = self.progress
    
    def cancel_hack(self):
        if self.is_hacking:
            self.is_hacking = False
        winsound.Beep(440, 500)  # Звук ошибки
        result = messagebox.showwarning("Отмена", "Вы отменили выкачку")
        if result == 'ok':
            self.root.quit()
    
    def show_victory(self):
        messagebox.showinfo("Победа", "Вы взломали все деньги!")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CasinoHack(root)
    root.mainloop()