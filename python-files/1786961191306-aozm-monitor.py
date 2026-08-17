# optimized_monitor.py
import tkinter as tk
from tkinter import ttk
import psutil
import GPUtil
import threading
import time
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sys
import os

# Функция для определения пути к ресурсам
def resource_path(relative_path):
    """Получение абсолютного пути к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Системный мониторинг v1.0")
        self.root.geometry("900x600")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # Установка иконки (если есть)
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        
        # Настройка стиля
        self.setup_styles()
        
        # Исторические данные
        self.history_length = 60
        self.cpu_temp_history = deque(maxlen=self.history_length)
        self.cpu_load_history = deque(maxlen=self.history_length)
        self.gpu_temp_history = deque(maxlen=self.history_length)
        self.gpu_load_history = deque(maxlen=self.history_length)
        self.fps_history = deque(maxlen=self.history_length)
        self.time_history = deque(maxlen=self.history_length)
        
        # Инициализация данных
        for i in range(self.history_length):
            self.cpu_temp_history.append(0)
            self.cpu_load_history.append(0)
            self.gpu_temp_history.append(0)
            self.gpu_load_history.append(0)
            self.fps_history.append(0)
            self.time_history.append(i)
        
        # Создание GUI
        self.create_widgets()
        
        # Запуск обновления
        self.running = True
        self.update_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_thread.start()
        
        # FPS счетчик
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        
        # Обработка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Настройка стилей интерфейса"""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg_color = '#1e1e1e'
        self.fg_color = '#ffffff'
        self.accent_color = '#007acc'
        
        style.configure('Title.TLabel', 
                       background=self.bg_color, 
                       foreground=self.fg_color, 
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Value.TLabel', 
                       background=self.bg_color, 
                       foreground=self.fg_color, 
                       font=('Segoe UI', 14))
        
        style.configure('Unit.TLabel', 
                       background=self.bg_color, 
                       foreground='#888888', 
                       font=('Segoe UI', 10))
        
        style.configure('Card.TFrame', 
                       background='#2d2d2d',
                       relief='flat')
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Заголовок
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, pady=10)
        
        title_label = ttk.Label(title_frame, text="Системный мониторинг", 
                                style='Title.TLabel')
        title_label.pack()
        
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Верхняя панель
        top_panel = ttk.Frame(main_frame)
        top_panel.pack(fill=tk.X, pady=(0, 10))
        
        # Настройка grid
        for i in range(4):
            top_panel.grid_columnconfigure(i, weight=1)
        
        # Метрики
        self.create_metric_card(top_panel, 0, "Температура CPU", "cpu_temp", "°C")
        self.create_metric_card(top_panel, 1, "Нагрузка CPU", "cpu_load", "%")
        self.create_metric_card(top_panel, 2, "Температура GPU", "gpu_temp", "°C")
        self.create_metric_card(top_panel, 3, "Нагрузка GPU", "gpu_load", "%")
        
        # FPS отдельно
        fps_frame = ttk.Frame(main_frame)
        fps_frame.pack(fill=tk.X, pady=5)
        
        self.create_metric_card(fps_frame, 0, "FPS", "fps", "FPS")
        
        # Графики
        self.create_charts(main_frame)
    
    def create_metric_card(self, parent, column, title, metric_key, unit):
        """Создание карточки с метрикой"""
        card = ttk.Frame(parent, style='Card.TFrame', padding=15)
        card.grid(row=0, column=column, padx=5, pady=5, sticky='nsew')
        
        title_label = ttk.Label(card, text=title, style='Value.TLabel', 
                               font=('Segoe UI', 10))
        title_label.pack()
        
        value_label = ttk.Label(card, text="--", style='Value.TLabel', 
                               font=('Segoe UI', 20, 'bold'))
        value_label.pack()
        
        unit_label = ttk.Label(card, text=unit, style='Unit.TLabel')
        unit_label.pack()
        
        if not hasattr(self, 'metric_labels'):
            self.metric_labels = {}
        self.metric_labels[metric_key] = value_label
    
    def create_charts(self, parent):
        """Создание графиков"""
        fig = Figure(figsize=(8, 4), facecolor=self.bg_color)
        fig.subplots_adjust(hspace=0.4, bottom=0.1, left=0.08, right=0.95, top=0.95)
        
        # График температур
        self.ax_temp = fig.add_subplot(311)
        self.ax_temp.set_facecolor('#2d2d2d')
        self.ax_temp.set_title('Температуры', color=self.fg_color, fontsize=10)
        self.ax_temp.tick_params(colors=self.fg_color, labelsize=8)
        self.ax_temp.set_ylabel('°C', color=self.fg_color, fontsize=9)
        self.ax_temp.grid(True, alpha=0.3)
        
        # График нагрузок
        self.ax_load = fig.add_subplot(312)
        self.ax_load.set_facecolor('#2d2d2d')
        self.ax_load.set_title('Нагрузки', color=self.fg_color, fontsize=10)
        self.ax_load.tick_params(colors=self.fg_color, labelsize=8)
        self.ax_load.set_ylabel('%', color=self.fg_color, fontsize=9)
        self.ax_load.grid(True, alpha=0.3)
        
        # График FPS
        self.ax_fps = fig.add_subplot(313)
        self.ax_fps.set_facecolor('#2d2d2d')
        self.ax_fps.set_title('FPS', color=self.fg_color, fontsize=10)
        self.ax_fps.tick_params(colors=self.fg_color, labelsize=8)
        self.ax_fps.set_ylabel('FPS', color=self.fg_color, fontsize=9)
        self.ax_fps.set_xlabel('Время (сек)', color=self.fg_color, fontsize=9)
        self.ax_fps.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.fig = fig
        self.canvas = canvas
    
    def get_cpu_temperature(self):
        """Получение температуры CPU"""
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            elif 'cpu-thermal' in temps:
                return temps['cpu-thermal'][0].current
            elif 'k10temp' in temps:
                return temps['k10temp'][0].current
            else:
                return 0
        except:
            return 0
    
    def update_data(self):
        """Обновление данных"""
        while self.running:
            try:
                # CPU
                cpu_temp = self.get_cpu_temperature()
                cpu_load = psutil.cpu_percent(interval=0.1)
                
                # GPU
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_temp = gpu.temperature
                    gpu_load = gpu.load * 100
                else:
                    gpu_temp = 0
                    gpu_load = 0
                
                # FPS
                self.fps_counter += 1
                current_time = time.time()
                if current_time - self.fps_start_time >= 1.0:
                    self.current_fps = self.fps_counter
                    self.fps_counter = 0
                    self.fps_start_time = current_time
                
                # Обновление истории
                self.cpu_temp_history.append(cpu_temp)
                self.cpu_load_history.append(cpu_load)
                self.gpu_temp_history.append(gpu_temp)
                self.gpu_load_history.append(gpu_load)
                self.fps_history.append(self.current_fps)
                self.time_history.append(len(self.time_history))
                
                # Обновление GUI
                self.root.after(0, self.update_gui, cpu_temp, cpu_load, 
                              gpu_temp, gpu_load, self.current_fps)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)
    
    def update_gui(self, cpu_temp, cpu_load, gpu_temp, gpu_load, fps):
        """Обновление GUI"""
        try:
            self.metric_labels['cpu_temp'].config(text=f"{cpu_temp:.1f}")
            self.metric_labels['cpu_load'].config(text=f"{cpu_load:.1f}")
            self.metric_labels['gpu_temp'].config(text=f"{gpu_temp:.1f}")
            self.metric_labels['gpu_load'].config(text=f"{gpu_load:.1f}")
            self.metric_labels['fps'].config(text=f"{fps}")
            
            self.update_charts()
        except:
            pass
    
    def update_charts(self):
        """Обновление графиков"""
        try:
            # Очистка
            self.ax_temp.clear()
            self.ax_load.clear()
            self.ax_fps.clear()
            
            # Настройка
            self.ax_temp.set_facecolor('#2d2d2d')
            self.ax_load.set_facecolor('#2d2d2d')
            self.ax_fps.set_facecolor('#2d2d2d')
            
            # Температуры
            self.ax_temp.plot(list(self.time_history), list(self.cpu_temp_history), 
                            color='#ff6b6b', label='CPU', linewidth=2)
            self.ax_temp.plot(list(self.time_history), list(self.gpu_temp_history), 
                            color='#4dabf7', label='GPU', linewidth=2)
            self.ax_temp.set_ylim(0, 100)
            self.ax_temp.legend(loc='upper right', facecolor='#2d2d2d', 
                              labelcolor=self.fg_color, fontsize=8)
            self.ax_temp.set_ylabel('°C', color=self.fg_color)
            self.ax_temp.tick_params(colors=self.fg_color)
            self.ax_temp.grid(True, alpha=0.3)
            
            # Нагрузки
            self.ax_load.plot(list(self.time_history), list(self.cpu_load_history), 
                            color='#ff6b6b', label='CPU', linewidth=2)
            self.ax_load.plot(list(self.time_history), list(self.gpu_load_history), 
                            color='#4dabf7', label='GPU', linewidth=2)
            self.ax_load.set_ylim(0, 100)
            self.ax_load.legend(loc='upper right', facecolor='#2d2d2d', 
                              labelcolor=self.fg_color, fontsize=8)
            self.ax_load.set_ylabel('%', color=self.fg_color)
            self.ax_load.tick_params(colors=self.fg_color)
            self.ax_load.grid(True, alpha=0.3)
            
            # FPS
            self.ax_fps.plot(list(self.time_history), list(self.fps_history), 
                           color='#51cf66', linewidth=2)
            self.ax_fps.set_ylim(0, max(120, max(self.fps_history) * 1.2))
            self.ax_fps.set_ylabel('FPS', color=self.fg_color)
            self.ax_fps.set_xlabel('Время (сек)', color=self.fg_color)
            self.ax_fps.tick_params(colors=self.fg_color)
            self.ax_fps.grid(True, alpha=0.3)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Ошибка графиков: {e}")
    
    def on_closing(self):
        """Закрытие приложения"""
        self.running = False
        self.root.destroy()
        sys.exit(0)

def main():
    try:
        root = tk.Tk()
        app = SystemMonitor(root)
        root.mainloop()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()