import tkinter as tk
from tkinter import ttk
import threading
import time
import math

class AlwaysOnTopTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Таймер для курсантов")
        self.root.geometry("300x250")
        
        # Делаем окно всегда поверх всех окон
        self.root.attributes('-topmost', True)
        
        # Убираем стандартные элементы управления окном
        self.root.overrideredirect(True)
        
        # Делаем окно прозрачным для фона
        self.root.wm_attributes('-transparentcolor', 'gray')
        
        # Переменные для таймера
        self.running = False
        self.seconds = 0
        self.minutes = 0
        self.hours = 0
        
        # Для перетаскивания окна
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.setup_ui()
        self.setup_dragging()
        
    def setup_ui(self):
        # Основной фрейм с круглым фоном
        main_frame = tk.Frame(self.root, bg='gray', width=250, height=250)
        main_frame.pack_propagate(False)
        main_frame.pack()
        
        # Создаем холст для рисования круга
        canvas = tk.Canvas(main_frame, width=250, height=250, bg='gray', 
                          highlightthickness=0)
        canvas.pack()
        
        # Рисуем синий круг
        canvas.create_oval(15, 15, 235, 235, 
                          fill='#3498db',  # Синий цвет
                          outline='#2980b9',  # Темно-синяя окантовка
                          width=3)
        
        # Заголовок внутри круга
        canvas.create_text(125, 60, 
                          text="ТАЙМЕР ДЛЯ\nКУРСАНТОВ",
                          font=('Arial', 14, 'bold'),
                          fill='white',
                          justify='center')
        
        # Время - большие цифры
        self.time_text = canvas.create_text(125, 130, 
                                           text="00:00:00",
                                           font=('Arial', 24, 'bold'),
                                           fill='white')
        
        # Кнопка закрытия (маленький крестик в углу)
        close_button = tk.Button(main_frame, text='✕', 
                                bg='#e74c3c', fg='white',
                                font=('Arial', 10, 'bold'),
                                bd=0, command=self.root.quit,
                                width=2, height=1)
        close_button.place(x=220, y=5)
        
        # Кнопки управления под кругом
        button_frame = tk.Frame(self.root, bg='gray')
        button_frame.pack(pady=5)
        
        self.start_button = tk.Button(button_frame, text="▶ Старт", 
                                      command=self.start_timer,
                                      width=8, bg='#2ecc71', fg='white',
                                      font=('Arial', 9, 'bold'),
                                      relief='flat')
        self.start_button.pack(side='left', padx=2)
        
        self.pause_button = tk.Button(button_frame, text="⏸ Пауза", 
                                      command=self.pause_timer,
                                      width=8, bg='#f39c12', fg='white',
                                      font=('Arial', 9, 'bold'),
                                      relief='flat',
                                      state='disabled')
        self.pause_button.pack(side='left', padx=2)
        
        self.reset_button = tk.Button(button_frame, text="↺ Сброс", 
                                      command=self.reset_timer,
                                      width=8, bg='#e74c3c', fg='white',
                                      font=('Arial', 9, 'bold'),
                                      relief='flat')
        self.reset_button.pack(side='left', padx=2)
        
        # Сохраняем ссылки на canvas элементы
        self.canvas = canvas
        
    def setup_dragging(self):
        # Привязываем события для перетаскивания окна
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.drag)
        
    def start_drag(self, event):
        # Разрешаем перетаскивание за любую часть окна
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
    def drag(self, event):
        if self.drag_start_x and self.drag_start_y:
            x = self.root.winfo_x() + event.x - self.drag_start_x
            y = self.root.winfo_y() + event.y - self.drag_start_y
            self.root.geometry(f'+{x}+{y}')
    
    def update_timer(self):
        while self.running:
            time.sleep(1)
            self.seconds += 1
            
            if self.seconds >= 60:
                self.seconds = 0
                self.minutes += 1
            
            if self.minutes >= 60:
                self.minutes = 0
                self.hours += 1
            
            # Обновляем текст времени на холсте
            time_str = f"{self.hours:02d}:{self.minutes:02d}:{self.seconds:02d}"
            self.root.after(0, lambda: self.canvas.itemconfig(self.time_text, 
                                                             text=time_str))
    
    def start_timer(self):
        if not self.running:
            self.running = True
            self.start_button.config(state='disabled', bg='#27ae60')
            self.pause_button.config(state='normal', bg='#f39c12')
            
            # Запускаем таймер в отдельном потоке
            timer_thread = threading.Thread(target=self.update_timer, daemon=True)
            timer_thread.start()
    
    def pause_timer(self):
        self.running = False
        self.start_button.config(state='normal', bg='#2ecc71')
        self.pause_button.config(state='disabled', bg='#f39c12')
    
    def reset_timer(self):
        self.running = False
        self.seconds = 0
        self.minutes = 0
        self.hours = 0
        self.canvas.itemconfig(self.time_text, text="00:00:00")
        self.start_button.config(state='normal', bg='#2ecc71')
        self.pause_button.config(state='disabled', bg='#f39c12')
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    timer = AlwaysOnTopTimer()
    timer.run()