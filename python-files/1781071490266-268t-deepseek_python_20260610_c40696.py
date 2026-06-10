import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import json
import datetime
import random
import os
import math

SAVE_FILE = "rpg_save.json"

class RPGTaskDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Task Dashboard")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1a1a2e")
        
        # Инициализация состояния
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        self.strength = 5
        self.intelligence = 5
        self.stamina = 5
        self.completed_tasks = 0
        self.character_name = "Искатель приключений"
        self.avatar_color = "#8a6de9"   # цвет фона аватара
        self.avatar_initials = "ИП"
        self.tasks = []                  # список задач
        self.current_filter = "all"      # all, active, completed, overdue
        self.current_sort = "date"       # date, xp, name, priority
        self.achievements = self.init_achievements()
        
        self.load_state()
        
        # Построение интерфейса
        self.create_widgets()
        self.update_ui()
        
    # ---------- Модель данных ----------
    def init_achievements(self):
        return [
            {"id": 1, "name": "Новичок", "desc": "Выполните первую задачу", "evolved_desc": "Выполните 10 задач",
             "icon": "🎯", "type": "tasks", "target": 1, "level": 1, "max_level": 5, "unlocked": False, "evolved": False},
            {"id": 2, "name": "Трудолюбивый", "desc": "Выполните 5 задач", "evolved_desc": "Выполните 25 задач",
             "icon": "💪", "type": "tasks", "target": 5, "level": 1, "max_level": 3, "unlocked": False, "evolved": False},
            {"id": 3, "name": "Мастер продуктивности", "desc": "Выполните 15 задач", "evolved_desc": "Выполните 50 задач",
             "icon": "🏆", "type": "tasks", "target": 15, "level": 1, "max_level": 2, "unlocked": False, "evolved": False},
            {"id": 4, "name": "Силач", "desc": "Достигните 10 силы", "evolved_desc": "Достигните 20 силы",
             "icon": "🔥", "type": "strength", "target": 10, "level": 1, "max_level": 3, "unlocked": False, "evolved": False},
            {"id": 5, "name": "Мудрец", "desc": "Достигните 10 интеллекта", "evolved_desc": "Достигните 20 интеллекта",
             "icon": "📚", "type": "intelligence", "target": 10, "level": 1, "max_level": 3, "unlocked": False, "evolved": False},
            {"id": 6, "name": "Неутомимый", "desc": "Достигните 10 выносливости", "evolved_desc": "Достигните 20 выносливости",
             "icon": "⚡", "type": "stamina", "target": 10, "level": 1, "max_level": 3, "unlocked": False, "evolved": False}
        ]
    
    def save_state(self):
        data = {
            "level": self.level, "exp": self.exp, "exp_to_next": self.exp_to_next,
            "strength": self.strength, "intelligence": self.intelligence, "stamina": self.stamina,
            "completed_tasks": self.completed_tasks, "character_name": self.character_name,
            "avatar_color": self.avatar_color, "avatar_initials": self.avatar_initials,
            "tasks": self.tasks, "achievements": self.achievements
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_state(self):
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.level = data.get("level", 1)
            self.exp = data.get("exp", 0)
            self.exp_to_next = data.get("exp_to_next", 100)
            self.strength = data.get("strength", 5)
            self.intelligence = data.get("intelligence", 5)
            self.stamina = data.get("stamina", 5)
            self.completed_tasks = data.get("completed_tasks", 0)
            self.character_name = data.get("character_name", "Искатель приключений")
            self.avatar_color = data.get("avatar_color", "#8a6de9")
            self.avatar_initials = data.get("avatar_initials", "ИП")
            self.tasks = data.get("tasks", [])
            # восстановление дат из строк
            for task in self.tasks:
                if task.get("due_date"):
                    task["due_date"] = datetime.datetime.fromisoformat(task["due_date"]).date()
                if "subtasks" not in task:
                    task["subtasks"] = []
            self.achievements = data.get("achievements", self.init_achievements())
        except:
            pass
    
    # ---------- Вспомогательные функции ----------
    def format_date(self, date_obj):
        if not date_obj:
            return ""
        return date_obj.strftime("%d.%m.%Y")
    
    def is_today(self, date_obj):
        return date_obj == datetime.date.today()
    
    def is_tomorrow(self, date_obj):
        return date_obj == datetime.date.today() + datetime.timedelta(days=1)
    
    def is_overdue(self, date_obj):
        return date_obj and date_obj < datetime.date.today()
    
    def get_date_status(self, date_obj):
        if not date_obj: return "no-date"
        if self.is_today(date_obj): return "today"
        if self.is_tomorrow(date_obj): return "tomorrow"
        if self.is_overdue(date_obj): return "overdue"
        return "future"
    
    def sort_tasks(self, tasks):
        tasks_copy = tasks[:]
        if self.current_sort == "date":
            tasks_copy.sort(key=lambda t: (t.get("due_date") is None, t.get("due_date")))
        elif self.current_sort == "xp":
            tasks_copy.sort(key=lambda t: t.get("xp", 0), reverse=True)
        elif self.current_sort == "name":
            tasks_copy.sort(key=lambda t: t.get("text", ""))
        elif self.current_sort == "priority":
            def priority_key(t):
                status = self.get_date_status(t.get("due_date"))
                order = {"overdue":0, "today":1, "tomorrow":2, "future":3, "no-date":4}
                return order[status]
            tasks_copy.sort(key=priority_key)
        return tasks_copy
    
    def filter_tasks(self):
        filtered = []
        for task in self.tasks:
            if self.current_filter == "all":
                filtered.append(task)
            elif self.current_filter == "active":
                if not task.get("completed", False):
                    filtered.append(task)
            elif self.current_filter == "completed":
                if task.get("completed", False):
                    filtered.append(task)
            elif self.current_filter == "overdue":
                if not task.get("completed", False) and self.is_overdue(task.get("due_date")):
                    filtered.append(task)
        return self.sort_tasks(filtered)
    
    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.5)
            self.show_notification(f"Поздравляем! Вы достигли {self.level} уровня!", "level_up")
    
    def complete_task(self, task_idx, subtask_idx=None):
        task = self.tasks[task_idx]
        if subtask_idx is not None:
            subtask = task["subtasks"][subtask_idx]
            if subtask.get("completed"):
                return
            subtask["completed"] = True
            self.add_exp(subtask["xp"])
            self.show_notification(f"Побочная задача выполнена! +{subtask['xp']} XP")
            # небольшое повышение статов
            inc = random.choice(["strength","intelligence","stamina"])
            setattr(self, inc, getattr(self, inc) + 0.5)
        else:
            if task.get("completed"):
                return
            task["completed"] = True
            self.add_exp(task["xp"])
            self.completed_tasks += 1
            self.show_notification(f"Задача выполнена! +{task['xp']} XP")
            inc = random.choice(["strength","intelligence","stamina"])
            setattr(self, inc, getattr(self, inc) + 1)
        
        # округление статов до 1 знака
        self.strength = round(self.strength, 1)
        self.intelligence = round(self.intelligence, 1)
        self.stamina = round(self.stamina, 1)
        
        self.check_achievements()
        self.update_ui()
    
    def add_task(self, text, due_date_str):
        if not text.strip():
            return
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except:
                pass
        xp = random.randint(10, 30)
        self.tasks.append({
            "text": text,
            "completed": False,
            "xp": xp,
            "due_date": due_date,
            "subtasks": []
        })
        self.update_ui()
    
    def delete_task(self, task_idx):
        del self.tasks[task_idx]
        self.update_ui()
    
    def reschedule_task(self, task_idx, new_date_str):
        if not new_date_str:
            return
        try:
            new_date = datetime.datetime.strptime(new_date_str, "%Y-%m-%d").date()
            self.tasks[task_idx]["due_date"] = new_date
            self.tasks[task_idx]["completed"] = False
            self.show_notification(f"Задача перенесена на {self.format_date(new_date)}")
            self.update_ui()
        except:
            pass
    
    def add_subtask(self, task_idx, text):
        if not text.strip():
            return
        xp = random.randint(5, 15)
        self.tasks[task_idx]["subtasks"].append({
            "text": text,
            "completed": False,
            "xp": xp
        })
        self.update_ui()
    
    def check_achievements(self):
        for ach in self.achievements:
            progress = 0
            if ach["type"] == "tasks":
                progress = self.completed_tasks
            elif ach["type"] == "strength":
                progress = self.strength
            elif ach["type"] == "intelligence":
                progress = self.intelligence
            elif ach["type"] == "stamina":
                progress = self.stamina
            
            if not ach["unlocked"] and progress >= ach["target"]:
                ach["unlocked"] = True
                self.show_notification(f"Достижение разблокировано: {ach['name']}!", "achievement")
            
            if ach["unlocked"] and not ach.get("evolved") and ach["level"] < ach["max_level"]:
                if progress >= ach["target"]:
                    ach["level"] += 1
                    ach["target"] = int(ach["target"] * 2.5)
                    ach["evolved"] = True
                    self.show_notification(f"Достижение эволюционировало: {ach['name']} Ур.{ach['level']}!", "achievement")
            elif ach.get("evolved") and progress >= ach["target"] and ach["level"] < ach["max_level"]:
                ach["level"] += 1
                ach["target"] = int(ach["target"] * 2.5)
                self.show_notification(f"Достижение эволюционировало: {ach['name']} Ур.{ach['level']}!", "achievement")
            
            if ach["level"] >= ach["max_level"]:
                ach["evolved"] = False
        
        # Сброс флага evolved, если эволюция завершена (чисто визуально)
        for ach in self.achievements:
            if ach["level"] >= ach["max_level"]:
                ach["evolved"] = False
    
    def reset_progress(self):
        if messagebox.askyesno("Сброс", "Вы уверены? Весь прогресс будет удалён безвозвратно."):
            self.level = 1
            self.exp = 0
            self.exp_to_next = 100
            self.strength = 5
            self.intelligence = 5
            self.stamina = 5
            self.completed_tasks = 0
            self.tasks = []
            self.achievements = self.init_achievements()
            self.update_ui()
            self.show_notification("Прогресс сброшен")
    
    # ---------- GUI ----------
    def create_widgets(self):
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg="#1a1a2e")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Левая колонка
        left_frame = tk.Frame(main_frame, bg="#1e1e2e", relief=tk.RAISED, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10), pady=5)
        
        # Правая колонка
        right_frame = tk.Frame(main_frame, bg="#1e1e2e", relief=tk.RAISED, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=5)
        
        # --- Левая панель: персонаж ---
        self.char_panel = tk.LabelFrame(left_frame, text="Персонаж", bg="#1e1e2e", fg="#ffcc00", font=("Segoe UI",12,"bold"), bd=0)
        self.char_panel.pack(fill=tk.X, padx=10, pady=10)
        
        # Аватар (canvas)
        self.avatar_canvas = tk.Canvas(self.char_panel, width=120, height=120, bg="#2a2a4a", highlightthickness=0)
        self.avatar_canvas.pack(pady=10)
        self.avatar_canvas.bind("<Button-1>", self.change_avatar)
        self.draw_avatar()
        
        # Имя персонажа (редактируемое)
        self.name_label = tk.Label(self.char_panel, text=self.character_name, fg="#ffcc00", bg="#1e1e2e", font=("Segoe UI",16,"bold"), cursor="hand2")
        self.name_label.pack(pady=5)
        self.name_label.bind("<Button-1>", self.edit_name)
        
        # Уровень и опыт
        level_frame = tk.Frame(self.char_panel, bg="#1e1e2e")
        level_frame.pack(fill=tk.X, pady=5)
        self.level_lbl = tk.Label(level_frame, text=f"Ур. {self.level}", fg="white", bg="#4a2c92", font=("Segoe UI",12), padx=10, pady=2)
        self.level_lbl.pack(side=tk.LEFT)
        self.exp_bar = ttk.Progressbar(level_frame, length=150, mode='determinate')
        self.exp_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Статы
        stats_frame = tk.Frame(self.char_panel, bg="#1e1e2e")
        stats_frame.pack(fill=tk.X, pady=10)
        self.strength_var = tk.StringVar(value=f"Сила: {self.strength}")
        self.intelligence_var = tk.StringVar(value=f"Интеллект: {self.intelligence}")
        self.stamina_var = tk.StringVar(value=f"Выносливость: {self.stamina}")
        self.completed_var = tk.StringVar(value=f"Выполнено: {self.completed_tasks}")
        
        tk.Label(stats_frame, textvariable=self.strength_var, bg="#1e1e2e", fg="white").grid(row=0, column=0, sticky="w", padx=5)
        tk.Label(stats_frame, textvariable=self.intelligence_var, bg="#1e1e2e", fg="white").grid(row=1, column=0, sticky="w", padx=5)
        tk.Label(stats_frame, textvariable=self.stamina_var, bg="#1e1e2e", fg="white").grid(row=0, column=1, sticky="w", padx=5)
        tk.Label(stats_frame, textvariable=self.completed_var, bg="#1e1e2e", fg="white").grid(row=1, column=1, sticky="w", padx=5)
        
        btn_reset = tk.Button(self.char_panel, text="Сбросить прогресс", bg="#e74c3c", fg="white", command=self.reset_progress)
        btn_reset.pack(pady=10, fill=tk.X)
        
        # --- Достижения ---
        self.ach_frame = tk.LabelFrame(left_frame, text="Достижения", bg="#1e1e2e", fg="#ffcc00", font=("Segoe UI",12,"bold"))
        self.ach_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.ach_canvas = tk.Canvas(self.ach_frame, bg="#1e1e2e", highlightthickness=0)
        self.ach_scroll = tk.Scrollbar(self.ach_frame, orient="vertical", command=self.ach_canvas.yview)
        self.ach_scrollable = tk.Frame(self.ach_canvas, bg="#1e1e2e")
        self.ach_scrollable.bind("<Configure>", lambda e: self.ach_canvas.configure(scrollregion=self.ach_canvas.bbox("all")))
        self.ach_canvas.create_window((0,0), window=self.ach_scrollable, anchor="nw")
        self.ach_canvas.configure(yscrollcommand=self.ach_scroll.set)
        self.ach_canvas.pack(side="left", fill="both", expand=True)
        self.ach_scroll.pack(side="right", fill="y")
        
        # --- Правая панель: задачи ---
        # Форма добавления
        add_frame = tk.Frame(right_frame, bg="#1e1e2e")
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        self.task_entry = tk.Entry(add_frame, bg="#2a2a4a", fg="white", insertbackground="white")
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.date_entry = tk.Entry(add_frame, width=12, bg="#2a2a4a", fg="white")
        self.date_entry.pack(side=tk.LEFT, padx=(0,5))
        self.date_entry.insert(0, "ГГГГ-ММ-ДД")
        self.date_entry.bind("<FocusIn>", lambda e: self.date_entry.delete(0, tk.END) if self.date_entry.get()=="ГГГГ-ММ-ДД" else None)
        btn_add = tk.Button(add_frame, text="+", bg="#8a6de9", fg="white", command=self.on_add_task)
        btn_add.pack(side=tk.LEFT)
        
        # Фильтры и сортировка
        filter_frame = tk.Frame(right_frame, bg="#1e1e2e")
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        filter_btns = [("Все","all"), ("Активные","active"), ("Просроченные","overdue"), ("Выполненные","completed")]
        for text, filt in filter_btns:
            btn = tk.Button(filter_frame, text=text, bg="#2a2a4a", fg="white", command=lambda f=filt: self.set_filter(f))
            btn.pack(side=tk.LEFT, padx=2)
        
        sort_frame = tk.Frame(right_frame, bg="#1e1e2e")
        sort_frame.pack(fill=tk.X, padx=10, pady=5)
        sort_btns = [("По дате","date"), ("По опыту","xp"), ("По имени","name"), ("Приоритет","priority")]
        for text, srt in sort_btns:
            btn = tk.Button(sort_frame, text=text, bg="#2a2a4a", fg="white", command=lambda s=srt: self.set_sort(s))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Список задач (скроллируемый)
        self.task_canvas = tk.Canvas(right_frame, bg="#1e1e2e", highlightthickness=0)
        self.task_scroll = tk.Scrollbar(right_frame, orient="vertical", command=self.task_canvas.yview)
        self.task_container = tk.Frame(self.task_canvas, bg="#1e1e2e")
        self.task_container.bind("<Configure>", lambda e: self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all")))
        self.task_canvas.create_window((0,0), window=self.task_container, anchor="nw")
        self.task_canvas.configure(yscrollcommand=self.task_scroll.set)
        self.task_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.task_scroll.pack(side="right", fill="y")
        
        # Уведомление
        self.notif_label = tk.Label(self.root, text="", bg="#8a6de9", fg="white", font=("Segoe UI",10))
        self.notif_label.place(relx=1.0, y=10, anchor="ne")
        self.root.after(3000, self.hide_notification)
    
    def draw_avatar(self):
        self.avatar_canvas.delete("all")
        w, h = 120, 120
        self.avatar_canvas.create_oval(5,5,w-5,h-5, fill=self.avatar_color, outline="#ffcc00", width=2)
        self.avatar_canvas.create_text(w//2, h//2, text=self.avatar_initials, fill="white", font=("Segoe UI",24,"bold"))
    
    def change_avatar(self, event):
        # Выбор цвета
        color = colorchooser.askcolor(title="Выберите цвет аватара", initialcolor=self.avatar_color)[1]
        if color:
            self.avatar_color = color
            # запрос инициалов
            initials = tk.simpledialog.askstring("Инициалы", "Введите инициалы (2-3 буквы):", initialvalue=self.avatar_initials)
            if initials:
                self.avatar_initials = initials.upper()[:3]
            self.draw_avatar()
            self.save_state()
    
    def edit_name(self, event):
        new_name = tk.simpledialog.askstring("Имя персонажа", "Введите новое имя:", initialvalue=self.character_name)
        if new_name:
            self.character_name = new_name
            self.name_label.config(text=self.character_name)
            self.save_state()
    
    def set_filter(self, filt):
        self.current_filter = filt
        self.update_ui()
    
    def set_sort(self, sort):
        self.current_sort = sort
        self.update_ui()
    
    def on_add_task(self):
        text = self.task_entry.get()
        due = self.date_entry.get()
        self.add_task(text, due)
        self.task_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, "ГГГГ-ММ-ДД")
    
    def show_notification(self, msg, msg_type=""):
        self.notif_label.config(text=msg)
        self.notif_label.lift()
        self.root.after(3000, self.hide_notification)
        self.save_state()
    
    def hide_notification(self):
        self.notif_label.config(text="")
    
    def update_ui(self):
        # Обновление статов
        self.name_label.config(text=self.character_name)
        self.level_lbl.config(text=f"Ур. {self.level}")
        self.exp_bar["value"] = (self.exp / self.exp_to_next) * 100
        self.strength_var.set(f"Сила: {self.strength}")
        self.intelligence_var.set(f"Интеллект: {self.intelligence}")
        self.stamina_var.set(f"Выносливость: {self.stamina}")
        self.completed_var.set(f"Выполнено: {self.completed_tasks}")
        self.draw_avatar()
        
        # Обновление достижений
        for widget in self.ach_scrollable.winfo_children():
            widget.destroy()
        row = 0
        for ach in self.achievements:
            desc = ach["evolved_desc"] if ach.get("evolved") and ach["level"]>1 else ach["desc"]
            if ach["unlocked"]:
                bg = "#2a2a4a"
                fg = "#ffcc00"
            else:
                bg = "#1a1a2a"
                fg = "gray"
            frame = tk.Frame(self.ach_scrollable, bg=bg, relief=tk.RAISED, bd=1)
            frame.grid(row=row, column=0, sticky="ew", pady=2, padx=2)
            frame.columnconfigure(0, weight=1)
            progress = 0
            if ach["type"] == "tasks": progress = self.completed_tasks
            elif ach["type"] == "strength": progress = self.strength
            elif ach["type"] == "intelligence": progress = self.intelligence
            elif ach["type"] == "stamina": progress = self.stamina
            text = f"{ach['icon']} {ach['name']} Ур.{ach['level']}\n{desc}\n{min(progress, ach['target'])}/{ach['target']}"
            tk.Label(frame, text=text, bg=bg, fg=fg, justify=tk.LEFT, font=("Segoe UI",9)).pack(anchor="w", padx=5, pady=5)
            row += 1
        
        # Обновление списка задач
        for widget in self.task_container.winfo_children():
            widget.destroy()
        
        tasks_to_show = self.filter_tasks()
        for idx, task in enumerate(tasks_to_show):
            # находим оригинальный индекс
            orig_idx = self.tasks.index(task)
            status = self.get_date_status(task.get("due_date"))
            frame = tk.Frame(self.task_container, bg="#2a2a4a", bd=1, relief=tk.RAISED)
            frame.pack(fill=tk.X, pady=3, padx=3)
            # чекбокс
            var = tk.BooleanVar(value=task.get("completed", False))
            cb = tk.Checkbutton(frame, variable=var, bg="#2a2a4a", fg="white", command=lambda t_idx=orig_idx: self.complete_task(t_idx))
            cb.pack(side=tk.LEFT, padx=5)
            # текст задачи и дата
            text_frame = tk.Frame(frame, bg="#2a2a4a")
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            task_text = task["text"]
            if task.get("completed"):
                task_text = f"✓ {task_text}"
            tk.Label(text_frame, text=task_text, bg="#2a2a4a", fg="white", font=("Segoe UI",10)).pack(anchor="w")
            date_str = self.format_date(task.get("due_date"))
            if date_str:
                color = "#e74c3c" if status=="overdue" else "#ff9900" if status=="today" else "#3498db" if status=="tomorrow" else "#aaa"
                tk.Label(text_frame, text=date_str, bg="#2a2a4a", fg=color, font=("Segoe UI",8)).pack(anchor="w")
            # XP
            tk.Label(frame, text=f"+{task['xp']} XP", bg="#2a2a4a", fg="#ffcc00").pack(side=tk.RIGHT, padx=5)
            # кнопки действий
            btn_frame = tk.Frame(frame, bg="#2a2a4a")
            btn_frame.pack(side=tk.RIGHT)
            # перенос
            def reschedule_callback(t_idx=orig_idx):
                new_date = tk.simpledialog.askstring("Перенос", "Новая дата (ГГГГ-ММ-ДД):")
                if new_date:
                    self.reschedule_task(t_idx, new_date)
            tk.Button(btn_frame, text="↻", width=2, command=reschedule_callback, bg="#1e1e2e", fg="white").pack(side=tk.LEFT, padx=2)
            # удаление
            tk.Button(btn_frame, text="✕", width=2, command=lambda t_idx=orig_idx: self.delete_task(t_idx), bg="#1e1e2e", fg="white").pack(side=tk.LEFT)
            
            # подзадачи
            subtask_frame = tk.Frame(frame, bg="#2a2a4a")
            subtask_frame.pack(fill=tk.X, padx=25, pady=5)
            if "subtasks" in task and task["subtasks"]:
                for st_idx, st in enumerate(task["subtasks"]):
                    sub_var = tk.BooleanVar(value=st.get("completed", False))
                    sub_cb = tk.Checkbutton(subtask_frame, text=st["text"], variable=sub_var, bg="#2a2a4a", fg="white",
                                            command=lambda t_idx=orig_idx, s_idx=st_idx: self.complete_task(t_idx, s_idx))
                    sub_cb.pack(anchor="w")
                    xp_lbl = tk.Label(subtask_frame, text=f"+{st['xp']} XP", bg="#2a2a4a", fg="#aaa", font=("Segoe UI",8))
                    xp_lbl.pack(anchor="w", padx=20)
            # кнопка добавить подзадачу
            def add_sub_callback(t_idx=orig_idx):
                text = tk.simpledialog.askstring("Новая подзадача", "Текст:")
                if text:
                    self.add_subtask(t_idx, text)
            tk.Button(subtask_frame, text="+ Добавить подзадачу", command=add_sub_callback, bg="#1e1e2e", fg="white").pack(anchor="w", pady=2)
        
        self.save_state()

if __name__ == "__main__":
    root = tk.Tk()
    app = RPGTaskDashboard(root)
    root.mainloop()