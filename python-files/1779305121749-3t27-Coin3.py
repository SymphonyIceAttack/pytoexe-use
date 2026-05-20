import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import os
import json
from datetime import datetime, timedelta

# Скрываем консольное окно (для Windows)
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class CoinTossGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Виртуальный генератор монеты")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        
        # Переменные состояния
        self.is_running = False
        self.is_paused = False
        self.mode = "minute"  # "minute" или "unlimited"
        self.start_time = 0
        self.pause_start_time = 0
        self.total_paused_time = 0
        self.heads_count = 0
        self.tails_count = 0
        
        # Файл для сохранения последнего результата
        self.save_file = "coin_toss_last_result.json"
        
        # Настройка интерфейса
        self.setup_ui()
        
        # АВТОМАТИЧЕСКИ загружаем сохраненный прогресс без вопросов
        self.load_progress()
        
    def setup_ui(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Режим работы (переключатель)
        mode_frame = ttk.LabelFrame(main_frame, text="Режим работы", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="minute")
        
        self.minute_radio = ttk.Radiobutton(
            mode_frame, 
            text="Замер за минуту (60 секунд)", 
            variable=self.mode_var, 
            value="minute",
            command=self.change_mode
        )
        self.minute_radio.pack(anchor=tk.W, pady=2)
        
        self.unlimited_radio = ttk.Radiobutton(
            mode_frame, 
            text="До завершения (бесконечная генерация)", 
            variable=self.mode_var, 
            value="unlimited",
            command=self.change_mode
        )
        self.unlimited_radio.pack(anchor=tk.W, pady=2)
        
        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(
            control_frame, 
            text="СТАРТ", 
            command=self.start_or_stop_toss,
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=2)
        
        self.pause_button = ttk.Button(
            control_frame, 
            text="ПАУЗА", 
            command=self.pause_toss,
            state="disabled",
            width=12
        )
        self.pause_button.pack(side=tk.LEFT, padx=2)
        
        self.reset_button = ttk.Button(
            control_frame, 
            text="СБРОС РЕЗУЛЬТАТОВ", 
            command=self.reset_toss,
            width=18
        )
        self.reset_button.pack(side=tk.LEFT, padx=2)
        
        # Рамка для отображения результатов
        self.display_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.display_frame.pack(fill=tk.BOTH, expand=True, pady=8)
        
        # Канва для рисования
        self.canvas = tk.Canvas(
            self.display_frame, 
            bg='white', 
            height=250,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Индикатор времени
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=3)
        
        self.time_label = ttk.Label(time_frame, text="Время: 00:00:00", font=('Arial', 9))
        self.time_label.pack(side=tk.LEFT)
        
        self.date_label = ttk.Label(time_frame, text="Дата: --", font=('Arial', 9))
        self.date_label.pack(side=tk.RIGHT)
        
        # Статистика
        self.stats_frame = ttk.LabelFrame(main_frame, text="Статистика", padding="8")
        self.stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_label = ttk.Label(
            self.stats_frame, 
            text="Нажмите 'СТАРТ' для начала", 
            font=('Arial', 10, 'bold')
        )
        self.stats_label.pack()
        
        self.compare_label = ttk.Label(
            self.stats_frame, 
            text="", 
            font=('Arial', 9),
            foreground='blue'
        )
        self.compare_label.pack(pady=3)
        
        # Обновляем состояние кнопок в зависимости от режима
        self.update_buttons_for_mode()
    
    def update_buttons_for_mode(self):
        """Обновляет состояние кнопок в зависимости от режима"""
        if self.mode == "minute":
            # В режиме минуты: пауза не нужна
            self.pause_button.config(state="disabled")
        else:
            # В бесконечном режиме
            if not self.is_running:
                self.pause_button.config(state="disabled")
                self.reset_button.config(state="normal")
    
    def change_mode(self):
        """Изменение режима работы"""
        if self.is_running:
            # Если идет процесс, останавливаем его
            self.stop_toss()
        
        self.mode = self.mode_var.get()
        
        # Сбрасываем результаты при смене режима
        self.heads_count = 0
        self.tails_count = 0
        self.total_paused_time = 0
        self.update_stats()
        
        # Обновляем отображение времени
        if self.mode == "minute":
            self.time_label.config(text="Время: 00:00:00")
            self.date_label.config(text="Дата: --")
            self.canvas.delete("all")
        else:
            # АВТОМАТИЧЕСКИ загружаем сохраненный прогресс при смене на бесконечный режим
            self.load_progress()
        
        # Обновляем состояние кнопок
        self.update_buttons_for_mode()
        
        # Убеждаемся что кнопка старт имеет правильный текст
        self.start_button.config(text="СТАРТ")
    
    def draw_coin(self, result):
        """Рисует орел или решку на канве"""
        self.canvas.delete("all")
        
        center_x = self.canvas.winfo_width() // 2
        center_y = self.canvas.winfo_height() // 2
        
        if center_x == 0 or center_y == 0:
            center_x = 235
            center_y = 125
        
        radius = 70
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill='gold', outline='orange', width=2
        )
        
        if result == "head":
            self.canvas.create_text(
                center_x, center_y,
                text="🦅\nОРЁЛ",
                font=('Arial', 20, 'bold'),
                fill='darkgreen'
            )
        else:
            self.canvas.create_text(
                center_x, center_y,
                text="🪙\nРЕШКА",
                font=('Arial', 20, 'bold'),
                fill='darkred'
            )
    
    def update_time_display(self):
        """Обновляет отображение времени"""
        if self.is_running and not self.is_paused:
            elapsed = time.time() - self.start_time - self.total_paused_time
            
            if self.mode == "minute":
                remaining = max(0, 60 - elapsed)
                if remaining <= 0:
                    return
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                self.time_label.config(text=f"Осталось: {minutes:02d}:{seconds:02d}")
                self.date_label.config(text="Дата: --")
            else:
                # Для бесконечного режима показываем прошедшее время
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                self.time_label.config(text=f"Прошло: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Показываем текущую дату
                current_date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                self.date_label.config(text=f"Дата: {current_date}")
        
        if self.is_running:
            self.root.after(1000, self.update_time_display)
    
    def save_last_result(self):
        """Сохраняет ТОЛЬКО последний результат в файл (без лога)"""
        if self.mode == "unlimited":
            try:
                data = {
                    'heads': self.heads_count,
                    'tails': self.tails_count,
                    'total': self.heads_count + self.tails_count,
                    'last_save': datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                }
                with open(self.save_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except:
                pass
    
    def animate_toss(self):
        """Анимация подбрасывания"""
        if not self.is_running or self.is_paused:
            return
        
        if self.mode == "minute":
            # Режим за минуту
            elapsed = time.time() - self.start_time - self.total_paused_time
            if elapsed >= 60:
                self.stop_toss()
                return
        
        # Генерируем результат
        is_head = random.choice([True, False])
        
        if is_head:
            self.heads_count += 1
            self.draw_coin("head")
        else:
            self.tails_count += 1
            self.draw_coin("tail")
        
        # Обновляем статистику
        self.update_stats()
        
        # Сохраняем последний результат КАЖДЫЕ 10 подбрасываний
        if self.mode == "unlimited" and (self.heads_count + self.tails_count) % 10 == 0:
            self.save_last_result()
        
        # Скорость генерации
        next_delay = random.uniform(0.05, 0.15)
        self.root.after(int(next_delay * 1000), self.animate_toss)
    
    def update_stats(self):
        """Обновляет отображение статистики"""
        total = self.heads_count + self.tails_count
        if total > 0:
            stats_text = f"ОРЛОВ: {self.heads_count} | РЕШЕК: {self.tails_count} | ВСЕГО: {total}"
            
            if self.heads_count > self.tails_count:
                compare_text = f"✓ ОРЛОВ БОЛЬШЕ на {self.heads_count - self.tails_count} ✓"
                compare_color = 'darkgreen'
            elif self.tails_count > self.heads_count:
                compare_text = f"✓ РЕШЕК БОЛЬШЕ на {self.tails_count - self.heads_count} ✓"
                compare_color = 'darkred'
            else:
                compare_text = "✓ ОРЛОВ И РЕШЕК ПОРОВНУ! ✓"
                compare_color = 'blue'
            
            self.compare_label.config(text=compare_text, foreground=compare_color)
        else:
            stats_text = "Ожидание результатов..."
            self.compare_label.config(text="")
        
        self.stats_label.config(text=stats_text)
    
    def start_or_stop_toss(self):
        """Универсальная кнопка: старт или завершение или возобновление"""
        if self.is_paused:
            # Если на паузе - возобновляем
            self.resume_toss()
        elif self.is_running:
            # Если процесс идет - завершаем
            self.stop_toss()
        else:
            # Если процесс не идет - запускаем
            self.start_toss()
    
    def start_toss(self):
        """Запускает генерацию"""
        if self.is_running:
            return
        
        # Новый запуск
        if self.mode == "minute":
            # В режиме минуты сбрасываем результаты при новом запуске
            self.heads_count = 0
            self.tails_count = 0
            self.total_paused_time = 0
            self.update_stats()
        
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_time = 0
        
        self.canvas.delete("all")
        
        # Меняем текст кнопки на ЗАВЕРШИТЬ
        self.start_button.config(text="ЗАВЕРШИТЬ")
        
        if self.mode == "minute":
            # В режиме минуты: пауза неактивна
            self.pause_button.config(state="disabled")
        else:
            # В бесконечном режиме активируем паузу
            self.pause_button.config(text="ПАУЗА", state="normal")
        
        self.minute_radio.config(state="disabled")
        self.unlimited_radio.config(state="disabled")
        
        # Сохраняем начальный результат
        if self.mode == "unlimited":
            self.save_last_result()
        
        self.update_stats()
        self.animate_toss()
        self.update_time_display()
    
    def pause_toss(self):
        """Ставит генерацию на паузу (только для бесконечного режима)"""
        if not self.is_running or self.is_paused or self.mode == "minute":
            return
        
        self.is_paused = True
        self.pause_start_time = time.time()
        
        # СОХРАНЯЕМ ПРИ ПАУЗЕ
        self.save_last_result()
        
        # Меняем текст кнопки на ПРОДОЛЖИТЬ
        self.start_button.config(text="ПРОДОЛЖИТЬ")
        self.pause_button.config(text="ПАУЗА", state="disabled")
        
        # Показываем сообщение о паузе
        self.canvas.delete("all")
        center_x = self.canvas.winfo_width() // 2
        center_y = self.canvas.winfo_height() // 2
        if center_x == 0 or center_y == 0:
            center_x = 235
            center_y = 125
        
        self.canvas.create_text(
            center_x, center_y,
            text="⏸ ПАУЗА ⏸\n\nПрогресс сохранен",
            font=('Arial', 16, 'bold'),
            fill='orange',
            justify='center'
        )
    
    def resume_toss(self):
        """Возобновляет генерацию после паузы"""
        if not self.is_paused:
            return
        
        # Обновляем время паузы
        if self.pause_start_time > 0:
            self.total_paused_time += time.time() - self.pause_start_time
            self.pause_start_time = 0
        
        self.is_paused = False
        
        # Меняем текст кнопки обратно на ЗАВЕРШИТЬ
        self.start_button.config(text="ЗАВЕРШИТЬ")
        self.pause_button.config(text="ПАУЗА", state="normal")
        
        # Сохраняем при возобновлении
        self.save_last_result()
        
        # Очищаем канву и продолжаем
        self.draw_coin("head" if random.choice([True, False]) else "tail")
        self.animate_toss()
        self.update_time_display()
    
    def stop_toss(self):
        """Останавливает генерацию и показывает результат"""
        if not self.is_running:
            return
        
        if self.is_paused:
            # Если на паузе, обновляем время перед остановкой
            if self.pause_start_time > 0:
                self.total_paused_time += time.time() - self.pause_start_time
            self.is_paused = False
        
        self.is_running = False
        
        # СОХРАНЯЕМ ПРИ ЗАВЕРШЕНИИ
        if self.mode == "unlimited":
            self.save_last_result()
        
        # Возвращаем кнопке текст СТАРТ
        self.start_button.config(text="СТАРТ")
        self.pause_button.config(text="ПАУЗА", state="disabled")
        
        self.minute_radio.config(state="normal")
        self.unlimited_radio.config(state="normal")
        
        # Показываем финальную статистику
        self.finalize_stats()
    
    def reset_toss(self):
        """Сбрасывает текущие результаты (только для бесконечного режима)"""
        if self.mode == "minute":
            return
        
        if self.is_running:
            self.stop_toss()
        
        self.heads_count = 0
        self.tails_count = 0
        self.total_paused_time = 0
        
        # Удаляем сохраненный файл
        if os.path.exists(self.save_file):
            os.remove(self.save_file)
        
        self.update_stats()
        
        self.canvas.delete("all")
        center_x = self.canvas.winfo_width() // 2
        center_y = self.canvas.winfo_height() // 2
        if center_x == 0 or center_y == 0:
            center_x = 235
            center_y = 125
        
        self.canvas.create_text(
            center_x, center_y,
            text="Результаты сброшены!",
            font=('Arial', 14, 'bold'),
            fill='red',
            justify='center'
        )
        
        self.time_label.config(text="Время: 00:00:00")
        self.date_label.config(text="Дата: --")
        
        # Убеждаемся что кнопка старт имеет правильный текст
        self.start_button.config(text="СТАРТ")
    
    def finalize_stats(self):
        """Показывает финальную статистику"""
        total = self.heads_count + self.tails_count
        
        if total > 0:
            if self.heads_count > self.tails_count:
                result_text = f"ОРЛОВ {self.heads_count} > РЕШЕК {self.tails_count}"
            elif self.tails_count > self.heads_count:
                result_text = f"ОРЛОВ {self.heads_count} < РЕШЕК {self.tails_count}"
            else:
                result_text = f"ОРЛОВ = РЕШЕК ({self.heads_count} = {self.tails_count})"
            
            # Получаем время для бесконечного режима
            time_info = ""
            if self.mode == "unlimited" and self.start_time > 0:
                elapsed = time.time() - self.start_time - self.total_paused_time
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                time_info = f"\n\nВремя генерации: {hours:02d}:{minutes:02d}:{seconds:02d}"
            
            extra_text = f"\n\nВсего подбрасываний: {total}{time_info}"
            
            self.canvas.delete("all")
            center_x = self.canvas.winfo_width() // 2
            center_y = self.canvas.winfo_height() // 2
            
            if center_x == 0 or center_y == 0:
                center_x = 235
                center_y = 125
            
            self.canvas.create_text(
                center_x, center_y,
                text=f"ГОТОВО!\n\n{result_text}\n{extra_text}",
                font=('Arial', 10, 'bold'),
                fill='darkblue',
                justify='center'
            )
    
    def load_progress(self):
        """АВТОМАТИЧЕСКИ загружает сохраненный прогресс без вопросов"""
        if self.mode == "unlimited" and os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Автоматически загружаем без вопросов
                self.heads_count = data['heads']
                self.tails_count = data['tails']
                self.update_stats()
                
                self.canvas.delete("all")
                center_x = self.canvas.winfo_width() // 2
                center_y = self.canvas.winfo_height() // 2
                if center_x == 0 or center_y == 0:
                    center_x = 235
                    center_y = 125
                
                self.canvas.create_text(
                    center_x, center_y,
                    text=f"Загружен последний результат:\nОрлов: {self.heads_count}\nРешек: {self.tails_count}\nВсего: {self.heads_count + self.tails_count}",
                    font=('Arial', 11, 'bold'),
                    fill='green',
                    justify='center'
                )
            except:
                pass

def main():
    root = tk.Tk()
    app = CoinTossGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
