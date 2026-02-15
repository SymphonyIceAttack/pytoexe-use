import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
from datetime import datetime

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Мой To-Do List")
        self.root.geometry("500x600")
        
        # Установка иконки для программы
        self.set_icon()
        
        # Определение пути для сохранения файла
        self.tasks_file = self.get_tasks_file_path()
        self.tasks = self.load_tasks()
        
        # Остальной код как в предыдущей версии...
        self.setup_styles()
        self.create_widgets()
        self.update_task_list()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def set_icon(self):
        """Установка иконки программы"""
        try:
            # Можно добавить свою иконку
            # self.root.iconbitmap(default='icon.ico')
            pass
        except:
            pass
    
    def get_tasks_file_path(self):
        """Получение пути для сохранения файла с задачами"""
        if getattr(sys, 'frozen', False):
            # Если программа запущена как EXE
            application_path = os.path.dirname(sys.executable)
        else:
            # Если запущена как скрипт Python
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(application_path, "tasks.json")
    
    def setup_styles(self):
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4CAF50"
        self.root.configure(bg=self.bg_color)
    
    def create_widgets(self):
        # Верхняя панель с заголовком
        header_frame = tk.Frame(self.root, bg=self.accent_color, height=50)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(header_frame, text="Мой To-Do List", 
                               font=("Arial", 16, "bold"), 
                               bg=self.accent_color, fg="white")
        title_label.pack(pady=10)
        
        # Панель ввода задач
        input_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        input_frame.pack(fill=tk.X, padx=10)
        
        self.task_entry = tk.Entry(input_frame, font=("Arial", 12), width=40)
        self.task_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        
        add_button = tk.Button(input_frame, text="Добавить задачу", 
                               command=self.add_task,
                               bg=self.accent_color, fg="white",
                               font=("Arial", 10, "bold"))
        add_button.pack(side=tk.LEFT)
        
        # Фильтры
        filter_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        filter_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(filter_frame, text="Показать:", bg=self.bg_color).pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="all")
        filters = [("Все", "all"), ("Активные", "active"), ("Выполненные", "completed")]
        
        for text, value in filters:
            tk.Radiobutton(filter_frame, text=text, variable=self.filter_var, 
                          value=value, bg=self.bg_color,
                          command=self.update_task_list).pack(side=tk.LEFT, padx=5)
        
        # Список задач с прокруткой
        list_frame = tk.Frame(self.root, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas для прокрутки
        self.canvas = tk.Canvas(list_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Нижняя панель со статистикой
        self.stats_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        self.stats_frame.pack(fill=tk.X)
        
        self.stats_label = tk.Label(self.stats_frame, text="", bg=self.bg_color)
        self.stats_label.pack()
        
        # Кнопки управления
        button_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        button_frame.pack(fill=tk.X)
        
        tk.Button(button_frame, text="Удалить выполненные", 
                 command=self.delete_completed,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Сохранить", 
                 command=self.save_tasks,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="О программе", 
                 command=self.show_about,
                 bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)
    
    def show_about(self):
        """Информация о программе"""
        about_text = """Мой To-Do List
Версия 1.0
Простая программа для управления задачами

Возможности:
• Добавление задач
• Отметка о выполнении
• Фильтрация задач
• Автоматическое сохранение
• Статистика"""
        
        messagebox.showinfo("О программе", about_text)
    
    def on_closing(self):
        """Действия при закрытии программы"""
        self.save_tasks()
        self.root.destroy()
    
    def add_task(self):
        task_text = self.task_entry.get().strip()
        if task_text:
            task = {
                "text": task_text,
                "completed": False,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "completed_date": None
            }
            self.tasks.append(task)
            self.task_entry.delete(0, tk.END)
            self.save_tasks()
            self.update_task_list()
        else:
            messagebox.showwarning("Предупреждение", "Введите текст задачи!")
    
    def toggle_task(self, index):
        self.tasks[index]["completed"] = not self.tasks[index]["completed"]
        if self.tasks[index]["completed"]:
            self.tasks[index]["completed_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            self.tasks[index]["completed_date"] = None
        self.save_tasks()
        self.update_task_list()
    
    def delete_task(self, index):
        if messagebox.askyesno("Подтверждение", "Удалить задачу?"):
            del self.tasks[index]
            self.save_tasks()
            self.update_task_list()
    
    def delete_completed(self):
        if messagebox.askyesno("Подтверждение", "Удалить все выполненные задачи?"):
            self.tasks = [task for task in self.tasks if not task["completed"]]
            self.save_tasks()
            self.update_task_list()
    
    def update_task_list(self):
        # Очистка текущего списка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Фильтрация задач
        filter_type = self.filter_var.get()
        filtered_tasks = []
        for i, task in enumerate(self.tasks):
            if filter_type == "all":
                filtered_tasks.append((i, task))
            elif filter_type == "active" and not task["completed"]:
                filtered_tasks.append((i, task))
            elif filter_type == "completed" and task["completed"]:
                filtered_tasks.append((i, task))
        
        # Отображение задач
        for idx, (orig_index, task) in enumerate(filtered_tasks):
            task_frame = tk.Frame(self.scrollable_frame, bg="white", relief=tk.RAISED, bd=1)
            task_frame.pack(fill=tk.X, pady=2)
            
            # Чекбокс для выполнения
            var = tk.BooleanVar(value=task["completed"])
            cb = tk.Checkbutton(task_frame, variable=var, 
                               command=lambda i=orig_index: self.toggle_task(i),
                               bg="white")
            cb.pack(side=tk.LEFT, padx=5)
            
            # Текст задачи
            text_frame = tk.Frame(task_frame, bg="white")
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
            
            task_text = task["text"]
            if task["completed"]:
                task_text = f"✓ {task_text}"
                text_color = "gray"
            else:
                text_color = "black"
            
            task_label = tk.Label(text_frame, text=task_text, 
                                 font=("Arial", 11),
                                 fg=text_color, bg="white",
                                 wraplength=300, justify=tk.LEFT)
            task_label.pack(anchor=tk.W)
            
            # Дата создания
            date_label = tk.Label(text_frame, text=f"Создано: {task['created']}",
                                 font=("Arial", 8), fg="gray", bg="white")
            date_label.pack(anchor=tk.W)
            
            if task["completed"] and task["completed_date"]:
                complete_label = tk.Label(text_frame, 
                                        text=f"Выполнено: {task['completed_date']}",
                                        font=("Arial", 8), fg="green", bg="white")
                complete_label.pack(anchor=tk.W)
            
            # Кнопка удаления
            delete_btn = tk.Button(task_frame, text="✕", 
                                  command=lambda i=orig_index: self.delete_task(i),
                                  bg="#f44336", fg="white", bd=0,
                                  font=("Arial", 8, "bold"))
            delete_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Обновление статистики
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task["completed"])
        active = total - completed
        
        stats_text = f"Всего: {total} | Активных: {active} | Выполненных: {completed}"
        self.stats_label.config(text=stats_text)
    
    def load_tasks(self):
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_tasks(self):
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()