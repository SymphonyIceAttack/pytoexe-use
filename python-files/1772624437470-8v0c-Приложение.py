import tkinter as tk
import json
import os
import uuid
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import os
FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

THEMES = {
    "light": {
        "name": "📜 Бумажная",
        "bg": "#f5efe6",  # Цвет старой бумаги
        "fg": "#5d4a36",  # Тёмно-коричневый текст
        "header": "#b08968",  # Коричневый заголовок
        "header_fg": "white",
        "card_bg": "#faf3e8",  # Светлая бумага для карточек
        "card_border": "#d9c8b2",  # Бежевая граница
        "input_bg": "#fff9f0",  # Очень светлая бумага для полей
        "input_fg": "#5d4a36",  # Коричневый текст
        "input_border": "#d9c8b2",  # Бежевая граница
        "button_primary": "#3498db",
        "button_success": "#27ae60",
        "button_warning": "#f39c12",
        "button_danger": "#e74c3c",
        "button_purple": "#9b59b6",
        "tree_bg": "#faf3e8",  # Бумажный фон для таблицы
        "tree_fg": "#5d4a36",  # Коричневый текст в таблице
        "tree_heading_bg": "#b08968",
        "tree_heading_fg": "white",
        "tree_selected": "#c9b39b",
        "status_bg": "#b08968",
        "status_fg": "white",
        "done": "#27ae60",
        "overdue": "#e74c3c",
        "active": "#3498db",
        "warning": "#f39c12"
    }
}

current_theme = "light"
PRIORITY_ORDER = {"Высокий": 0, "Средний": 1, "Низкий": 2}
PRIORITY_ICONS = {"Высокий": "⭐⭐⭐", "Средний": "⭐⭐", "Низкий": "⭐"}
tasks = []
stats_frame = None
reminder_shown = False

# Глобальные виджеты
title_entry = None
deadline_entry = None
description_input = None
priority_var = None
priority_box = None
tree_all = None
description_view = None
right_column = None
right_panel = None
btn_frame = None
style = None
header_frame = None
title_label = None
top_frame = None
tree_frame = None


def load_tasks():
    global tasks
    if not os.path.exists(FILENAME):
        return []
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            return tasks
    except:
        return []


def save_tasks():
    try:
        with open(FILENAME, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")


def get_status(task):
    today = datetime.now().date()
    if task.get("done", False):
        return "✅ Выполнено"
    try:
        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
        if deadline < today:
            return "⚠️ Просрочено"
    except:
        pass
    return "🔄 В процессе"


def check_initial_reminder():
    """Проверяет задачи при запуске и показывает напоминание один раз"""
    global reminder_shown
    if not reminder_shown:
        check_reminders()
        reminder_shown = True


def check_reminders():
    """Проверяет задачи и показывает напоминание о сегодняшних и завтрашних задачах"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    today_tasks = []
    tomorrow_tasks = []

    for task in tasks:
        if task.get("done", False):
            continue

        try:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d").date()

            if deadline == today:
                today_tasks.append(task)
            elif deadline == tomorrow:
                tomorrow_tasks.append(task)
        except:
            pass

    # Показываем напоминание только если есть задачи на сегодня или завтра
    if today_tasks or tomorrow_tasks:
        show_reminder(today_tasks, tomorrow_tasks)


def show_reminder(today_tasks, tomorrow_tasks):
    """Показывает окно с напоминаниями"""
    theme = THEMES["light"]

    # Создаем окно напоминания
    reminder = tk.Toplevel(root)
    reminder.title("Напоминание")
    reminder.geometry("450x350")
    reminder.configure(bg=theme["card_bg"])
    reminder.transient(root)
    reminder.grab_set()

    # Центрируем окно
    reminder.update_idletasks()
    x = (reminder.winfo_screenwidth() // 2) - (450 // 2)
    y = (reminder.winfo_screenheight() // 2) - (350 // 2)
    reminder.geometry(f'450x350+{x}+{y}')

    # Заголовок
    tk.Label(reminder, text="⌛ Ближайшие дедлайны",
             bg=theme["header"], fg=theme["header_fg"],
             font=("Segoe UI", 14, "bold"), pady=10).pack(fill="x")

    # Фрейм для контента с прокруткой
    canvas = tk.Canvas(reminder, bg=theme["card_bg"], highlightthickness=0)
    scrollbar = tk.Scrollbar(reminder, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=theme["card_bg"])

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
    scrollbar.pack(side="right", fill="y", pady=10)

    # Сегодняшние задачи
    if today_tasks:
        tk.Label(scrollable_frame, text="🔥 Сегодня:",
                 bg=theme["card_bg"], fg=theme["warning"],
                 font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 5))

        for task in today_tasks:
            tk.Label(scrollable_frame, text=f"• {task['title']}",
                     bg=theme["card_bg"], fg=theme["fg"],
                     font=("Segoe UI", 11), anchor="w", justify="left").pack(fill="x", padx=20)

        tk.Label(scrollable_frame, text="", bg=theme["card_bg"]).pack(pady=5)

    # Завтрашние задачи
    if tomorrow_tasks:
        tk.Label(scrollable_frame, text="⏰ Завтра:",
                 bg=theme["card_bg"], fg=theme["warning"],
                 font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 5))

        for task in tomorrow_tasks:
            tk.Label(scrollable_frame, text=f"• {task['title']}",
                     bg=theme["card_bg"], fg=theme["fg"],
                     font=("Segoe UI", 11), anchor="w", justify="left").pack(fill="x", padx=20)

    # Кнопка закрытия
    btn_frame = tk.Frame(reminder, bg=theme["card_bg"], padx=20, pady=10)
    btn_frame.pack(fill="x")

    tk.Button(btn_frame, text="OK", bg=theme["button_primary"], fg="white",
              command=reminder.destroy,
              font=("Segoe UI", 11, "bold"), width=10, cursor="hand2", relief="flat").pack()


def add_task():
    title = title_entry.get().strip()
    deadline = deadline_entry.get().strip()
    description = description_input.get("1.0", tk.END).strip()
    priority = priority_var.get()

    if not title or not deadline:
        messagebox.showwarning("Ошибка", "Заполните название и срок")
        return

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except:
        messagebox.showerror("Ошибка", "Дата в формате: ГГГГ-ММ-ДД")
        return

    tasks.append({
        "id": str(uuid.uuid4()),
        "title": title,
        "deadline": deadline,
        "description": description,
        "priority": priority,
        "done": False
    })
    save_tasks()
    update_all()
    clear_inputs()
    messagebox.showinfo("Успех", "Задача добавлена!")


def clear_inputs():
    title_entry.delete(0, tk.END)
    deadline_entry.delete(0, tk.END)
    description_input.delete("1.0", tk.END)
    priority_var.set("Средний")


def get_selected_ids():
    if not tree_all:
        return []
    selected = tree_all.selection()
    ids = []
    for item in selected:
        values = tree_all.item(item)["values"]
        if len(values) > 4:
            ids.append(values[4])
    return ids


def mark_done(value):
    ids = get_selected_ids()
    if not ids:
        messagebox.showinfo("Информация", "Выберите задачу")
        return
    for task in tasks:
        if task["id"] in ids:
            task["done"] = value
    save_tasks()
    update_all()
    messagebox.showinfo("Успех", "Выполнено!" if value else "Снято!")


def delete_tasks():
    global tasks
    ids = get_selected_ids()
    if not ids:
        messagebox.showinfo("Информация", "Выберите задачу")
        return

    count = len(ids)
    word = "задачу" if count == 1 else "задачи"
    if messagebox.askyesno("Подтверждение", f"Удалить {count} {word}?"):
        tasks = [t for t in tasks if t["id"] not in ids]
        save_tasks()
        update_all()
        if description_view:
            description_view.delete("1.0", tk.END)
        messagebox.showinfo("Успех", f"Удалено")


def on_select(event):
    if not tree_all or not tree_all.selection():
        return
    selected = tree_all.selection()[0]
    values = tree_all.item(selected)["values"]
    if len(values) <= 4:
        return
    task_id = values[4]
    for task in tasks:
        if task["id"] == task_id:
            description_view.delete("1.0", tk.END)
            description_view.insert(tk.END, task.get("description", ""))
            title_entry.delete(0, tk.END)
            title_entry.insert(0, task["title"])
            deadline_entry.delete(0, tk.END)
            deadline_entry.insert(0, task["deadline"])
            priority_var.set(task["priority"])
            break


def save_description():
    if not tree_all or not tree_all.selection():
        messagebox.showinfo("Информация", "Выберите задачу")
        return
    selected = tree_all.selection()[0]
    values = tree_all.item(selected)["values"]
    if len(values) <= 4:
        return
    task_id = values[4]
    new_desc = description_view.get("1.0", tk.END).strip()
    for task in tasks:
        if task["id"] == task_id:
            task["description"] = new_desc
            break
    save_tasks()
    messagebox.showinfo("Сохранено", "Описание обновлено!")


def edit_task():
    if not tree_all or not tree_all.selection():
        messagebox.showinfo("Информация", "Выберите задачу")
        return
    selected = tree_all.selection()[0]
    values = tree_all.item(selected)["values"]
    if len(values) <= 4:
        return
    task_id = values[4]
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = title_entry.get().strip() or task["title"]
            task["deadline"] = deadline_entry.get().strip() or task["deadline"]
            task["description"] = description_input.get("1.0", tk.END).strip() or task["description"]
            task["priority"] = priority_var.get()
            break
    save_tasks()
    update_all()
    clear_inputs()
    messagebox.showinfo("Успех", "Задача обновлена!")


def insert_task(task):
    status = get_status(task)
    priority = task.get("priority", "Средний")
    priority_display = f"{PRIORITY_ICONS.get(priority, '⭐')} {priority}"
    item = tree_all.insert("", "end", values=(task["title"], task["deadline"], priority_display, status, task["id"]))

    if "Выполнено" in status:
        tree_all.item(item, tags=("done",))
    elif "Просрочено" in status:
        tree_all.item(item, tags=("overdue",))
    else:
        tree_all.item(item, tags=("active",))


def fill_tree():
    tree_all.delete(*tree_all.get_children())
    sorted_tasks = sorted(tasks, key=lambda x: (
        PRIORITY_ORDER.get(x.get("priority", "Средний"), 1),
        x.get("title", "").lower()
    ))
    for task in sorted_tasks:
        insert_task(task)


def update_stats():
    global stats_frame
    theme = THEMES["light"]

    # Очищаем старую статистику если она есть
    if stats_frame and stats_frame.winfo_exists():
        for widget in stats_frame.winfo_children():
            widget.destroy()

    # Заголовок статистики
    tk.Label(stats_frame, text="📊 Статистика задач", bg=theme["card_bg"], fg=theme["fg"],
             font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 5))

    # Расчет статистики
    total = len(tasks)
    done = len([t for t in tasks if t.get("done", False)])
    active = total - done
    overdue = len([t for t in tasks if "Просрочено" in get_status(t)])

    percent = (done / total * 100) if total else 0

    # Строки статистики 
    stats_items = [
        ("Всего задач:", str(total), theme["fg"]),
        ("✅ Выполнено:", str(done), theme["done"]),
        ("🔄 В процессе:", str(active), theme["active"]),
        ("⚠️ Просрочено:", str(overdue), theme["overdue"]),
        ("📈 Прогресс:", f"{percent:.1f}%", theme["fg"])
    ]

    # Отображаем статистику
    for label, value, color in stats_items:
        item_frame = tk.Frame(stats_frame, bg=theme["card_bg"])
        item_frame.pack(fill="x", padx=10, pady=1)

        tk.Label(item_frame, text=label, bg=theme["card_bg"], fg=theme["fg"],
                 font=("Segoe UI", 11), anchor="w").pack(side="left")
        tk.Label(item_frame, text=value, bg=theme["card_bg"], fg=color,
                 font=("Segoe UI", 11, "bold"), anchor="e").pack(side="right")


def update_all():
    fill_tree()
    update_stats()


# === GUI ===
root = tk.Tk()
root.title("📜 Task Manager Pro")
root.geometry("1400x800")
try:
    root.iconbitmap("icon.ico")
except:
    pass

style = ttk.Style()
style.theme_use("clam")
load_tasks()

# Header
header_frame = tk.Frame(root, bg=THEMES["light"]["header"], height=70)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

title_label = tk.Label(header_frame, text="📜 Task Manager Pro", bg=THEMES["light"]["header"],
                       fg=THEMES["light"]["header_fg"], font=("Segoe UI", 24, "bold"))
title_label.place(relx=0.5, rely=0.5, anchor="center")

# Main
main_container = tk.Frame(root, bg=THEMES["light"]["bg"])
main_container.pack(expand=True, fill="both", padx=20, pady=10)

left_column = tk.Frame(main_container, bg=THEMES["light"]["bg"])
left_column.pack(side="left", expand=True, fill="both", padx=(0, 10))

# Форма
top_frame = tk.Frame(left_column, bg=THEMES["light"]["card_bg"], relief="solid", bd=1,
                     highlightbackground=THEMES["light"]["card_border"], highlightthickness=1)
top_frame.pack(pady=(0, 10), fill="x")

tk.Label(top_frame, text="➕ Добавить задачу", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=10)

form_frame = tk.Frame(top_frame, bg=THEMES["light"]["card_bg"])
form_frame.pack(padx=10, pady=10, fill="x")

row1 = tk.Frame(form_frame, bg=THEMES["light"]["card_bg"])
row1.pack(fill="x", pady=5)

tk.Label(row1, text="Название:", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 11)).pack(side="left")
title_entry = tk.Entry(row1, width=40, bg=THEMES["light"]["input_bg"], fg=THEMES["light"]["input_fg"],
                       font=("Segoe UI", 11), relief="solid", bd=1,
                       highlightbackground=THEMES["light"]["input_border"], highlightthickness=1)
title_entry.pack(side="left", padx=(10, 15))

tk.Label(row1, text="Срок (ГГГГ-ММ-ДД):", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 11)).pack(side="left")
deadline_entry = tk.Entry(row1, width=15, bg=THEMES["light"]["input_bg"], fg=THEMES["light"]["input_fg"],
                          font=("Segoe UI", 11), relief="solid", bd=1,
                          highlightbackground=THEMES["light"]["input_border"], highlightthickness=1)
deadline_entry.pack(side="left", padx=(5, 15))

tk.Label(row1, text="Приоритет:", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 11)).pack(side="left")
priority_var = tk.StringVar(value="Средний")
priority_box = ttk.Combobox(row1, textvariable=priority_var, values=["Высокий", "Средний", "Низкий"],
                            state="readonly", width=12)
priority_box.pack(side="left", padx=5)

row2 = tk.Frame(form_frame, bg=THEMES["light"]["card_bg"])
row2.pack(fill="x", pady=10)

tk.Label(row2, text="Описание:", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 11)).pack(side="left")
description_input = tk.Text(row2, width=70, height=3, bg=THEMES["light"]["input_bg"],
                            fg=THEMES["light"]["input_fg"], font=("Segoe UI", 11),
                            relief="solid", bd=1, highlightbackground=THEMES["light"]["input_border"],
                            highlightthickness=1)
description_input.pack(side="left", padx=(10, 0))

btn_frame = tk.Frame(top_frame, bg=THEMES["light"]["card_bg"])
btn_frame.pack(pady=15)

tk.Button(btn_frame, text="➕ Добавить", bg=THEMES["light"]["button_success"], fg="white",
          command=add_task, font=("Segoe UI", 11, "bold"), width=15,
          cursor="hand2", relief="flat").pack(side="left", padx=5)
tk.Button(btn_frame, text="✏️ Редактировать", bg=THEMES["light"]["button_warning"], fg="white",
          command=edit_task, font=("Segoe UI", 11, "bold"), width=15,
          cursor="hand2", relief="flat").pack(side="left", padx=5)
tk.Button(btn_frame, text="🗑️ Удалить", bg=THEMES["light"]["button_danger"], fg="white",
          command=delete_tasks, font=("Segoe UI", 11, "bold"), width=15,
          cursor="hand2", relief="flat").pack(side="left", padx=5)

# Treeview
tree_frame = tk.Frame(left_column, bg=THEMES["light"]["card_bg"], relief="solid", bd=1,
                      highlightbackground=THEMES["light"]["card_border"], highlightthickness=1)
tree_frame.pack(expand=True, fill="both")

# Настройка стиля для Treeview с увеличенным текстом
style.configure("Treeview",
                background=THEMES["light"]["tree_bg"],
                foreground=THEMES["light"]["tree_fg"],
                fieldbackground=THEMES["light"]["tree_bg"],
                rowheight=40,
                font=("Segoe UI", 12))

style.map("Treeview",
          background=[("selected", THEMES["light"]["tree_selected"])],
          foreground=[("selected", THEMES["light"]["tree_fg"])])

style.configure("Treeview.Heading",
                background=THEMES["light"]["tree_heading_bg"],
                foreground=THEMES["light"]["tree_heading_fg"],
                font=("Segoe UI", 12, "bold"))

tree_all = ttk.Treeview(tree_frame, columns=("Название", "Срок", "Приоритет", "Статус", "ID"),
                        show="headings", selectmode="extended")

tree_all.heading("Название", text="Название")
tree_all.heading("Срок", text="Срок")
tree_all.heading("Приоритет", text="Приоритет")
tree_all.heading("Статус", text="Статус")
tree_all.heading("ID", text="ID")

tree_all.column("Название", width=350)
tree_all.column("Срок", width=130)
tree_all.column("Приоритет", width=160)
tree_all.column("Статус", width=150)
tree_all.column("ID", width=0, stretch=False)

tree_all.pack(side="left", expand=True, fill="both", padx=1, pady=1)
tree_all.bind("<<TreeviewSelect>>", on_select)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_all.yview)
scrollbar.pack(side="right", fill="y")
tree_all.configure(yscrollcommand=scrollbar.set)

# Инициализация цветов при запуске
tree_all.tag_configure("done", foreground=THEMES["light"]["done"], font=("Segoe UI", 12))
tree_all.tag_configure("overdue", foreground=THEMES["light"]["overdue"], font=("Segoe UI", 12))
tree_all.tag_configure("active", foreground=THEMES["light"]["active"], font=("Segoe UI", 12))

# Правая колонка
right_column = tk.Frame(main_container, bg=THEMES["light"]["bg"], width=350)
right_column.pack(side="right", fill="both", padx=(10, 0))
right_column.pack_propagate(False)

# Статистика - создаем фрейм
stats_frame = tk.Frame(right_column, bg=THEMES["light"]["card_bg"], relief="solid", bd=1,
                       highlightbackground=THEMES["light"]["card_border"], highlightthickness=1)
stats_frame.pack(fill="x", pady=(0, 10))

# Вызываем функцию обновления статистики
update_stats()

# Правая панель
right_panel = tk.Frame(right_column, bg=THEMES["light"]["card_bg"], relief="solid", bd=1,
                       highlightbackground=THEMES["light"]["card_border"], highlightthickness=1)
right_panel.pack(fill="both", expand=True)

tk.Label(right_panel, text="📄 Детали задачи", bg=THEMES["light"]["header"], fg=THEMES["light"]["header_fg"],
         font=("Segoe UI", 12, "bold"), pady=8).pack(fill="x")

desc_frame = tk.Frame(right_panel, bg=THEMES["light"]["card_bg"], padx=10, pady=8)
desc_frame.pack(fill="both", expand=True)

tk.Label(desc_frame, text="Описание:", bg=THEMES["light"]["card_bg"], fg=THEMES["light"]["fg"],
         font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")

description_view = tk.Text(desc_frame, height=12, bg=THEMES["light"]["input_bg"],
                           fg=THEMES["light"]["input_fg"], font=("Segoe UI", 12),
                           relief="solid", bd=1, wrap="word",
                           highlightbackground=THEMES["light"]["input_border"], highlightthickness=1)
description_view.pack(fill="both", expand=True, pady=5)

btn_frame_right = tk.Frame(right_panel, bg=THEMES["light"]["card_bg"], padx=10, pady=8)
btn_frame_right.pack(fill="x")

tk.Button(btn_frame_right, text="💾 Сохранить описание", bg=THEMES["light"]["button_primary"], fg="white",
          command=save_description, font=("Segoe UI", 11, "bold"),
          width=22, cursor="hand2", relief="flat").pack(pady=2)

tk.Button(btn_frame_right, text="✅ Отметить выполненной", bg=THEMES["light"]["button_success"], fg="white",
          command=lambda: mark_done(True), font=("Segoe UI", 11, "bold"),
          width=22, cursor="hand2", relief="flat").pack(pady=2)

tk.Button(btn_frame_right, text="❌ Снять выполнение", bg=THEMES["light"]["button_warning"], fg="white",
          command=lambda: mark_done(False), font=("Segoe UI", 11, "bold"),
          width=22, cursor="hand2", relief="flat").pack(pady=2)

# Запуск приложения
update_all()
# Проверяем напоминания один раз при запуске
root.after(500, check_initial_reminder)
root.mainloop()