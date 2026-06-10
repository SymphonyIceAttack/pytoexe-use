import json
import os
from datetime import datetime, date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ------------------- ФАЙЛ ДАННЫХ -------------------
DATA_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

# ------------------- УДАЛЕНИЕ ВЫПОЛНЕННЫХ ЗА ВЧЕРА -------------------
def remove_completed_old(tasks):
    today_str = date.today().isoformat()
    new_tasks = []
    for t in tasks:
        if t.get("completed") and t.get("completed_date", "") < today_str:
            continue  # удаляем
        new_tasks.append(t)
    return new_tasks

# ------------------- ОСНОВНОЕ ПРИЛОЖЕНИЕ -------------------
class TaskWidget:
    def __init__(self, root):
        self.root = root
        self.root.title("Задачи")
        self.root.geometry("500x600")
        self.root.configure(bg="#1e1f2c")
        # разрешаем изменение размера
        self.root.minsize(300, 400)

        # загружаем и чистим старые выполненные
        self.tasks = load_tasks()
        self.tasks = remove_completed_old(self.tasks)
        save_tasks(self.tasks)

        # фрейм для списка с прокруткой
        self.canvas = tk.Canvas(root, bg="#1e1f2c", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1e1f2c")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_width())
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # кнопка + (плавающая)
        self.add_btn = tk.Button(root, text="+", font=("Segoe UI", 24, "bold"),
                                 bg="#5f7fbf", fg="white", relief="flat",
                                 command=self.open_add_dialog)
        self.add_btn.place(relx=0.92, rely=0.92, anchor="se", width=50, height=50)

        # обновляем отображение
        self.refresh_list()

        # периодическая проверка (каждые 60 секунд) на удаление выполненных
        self.check_loop()

    def check_loop(self):
        """Проверяем каждую минуту, не нужно ли удалить выполненные задачи"""
        old_len = len(self.tasks)
        self.tasks = remove_completed_old(self.tasks)
        if len(self.tasks) != old_len:
            save_tasks(self.tasks)
            self.refresh_list()
        self.root.after(60000, self.check_loop)

    def refresh_list(self):
        # очищаем фрейм
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        today_str = date.today().isoformat()

        # добавляем мета-информацию для сортировки
        tasks_with_meta = []
        for t in self.tasks:
            is_overdue = False
            if not t.get("completed") and t.get("due_date") and t["due_date"] < today_str:
                is_overdue = True
            tasks_with_meta.append({
                "task": t,
                "is_overdue": is_overdue,
                "completed": t.get("completed", False),
                "due_date": t.get("due_date", "9999-12-31")
            })

        # сортировка: просроченные (невыполненные) вверх, потом обычные активные по дате, потом выполненные
        tasks_with_meta.sort(key=lambda x: (
            0 if (x["is_overdue"] and not x["completed"]) else 1,  # сначала просроченные
            x["completed"],  # False раньше True
            x["due_date"] if not x["completed"] else "9999-12-31"
        ))

        for item in tasks_with_meta:
            task = item["task"]
            self.create_task_widget(task, item["is_overdue"])

    def create_task_widget(self, task, is_overdue):
        frame = tk.Frame(self.scrollable_frame, bg="#242531", bd=0, relief="flat")
        frame.pack(fill="x", padx=10, pady=5, ipadx=8, ipady=8)

        # цвет фона для просроченных
        if is_overdue and not task.get("completed"):
            frame.configure(bg="#552c2c")
        elif task.get("completed"):
            frame.configure(bg="#1f2930")

        # строка: текст + дата + кнопки
        inner = tk.Frame(frame, bg=frame["bg"])
        inner.pack(fill="x", padx=5, pady=2)

        # текст задачи
        text = task["text"]
        lbl = tk.Label(inner, text=text, font=("Segoe UI", 10),
                       bg=inner["bg"], fg="#eceef7", anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        if task.get("completed"):
            lbl.configure(fg="#7aa57c", font=("Segoe UI", 10, "overstrike"))

        # дата
        due = task.get("due_date", "без даты")
        due_lbl = tk.Label(inner, text=due, font=("Segoe UI", 8),
                           bg=inner["bg"], fg="#bdc2da")
        due_lbl.pack(side="left", padx=10)

        # кнопка галочки (выполнить)
        def complete():
            if not task.get("completed"):
                task["completed"] = True
                task["completed_date"] = date.today().isoformat()
                save_tasks(self.tasks)
                self.refresh_list()

        chk_btn = tk.Button(inner, text="✅" if task.get("completed") else "⬜",
                            font=("Segoe UI", 10), relief="flat", bg=inner["bg"],
                            command=complete, cursor="hand2")
        chk_btn.pack(side="left", padx=2)
        if task.get("completed"):
            chk_btn.configure(state="disabled")

        # кнопка редактировать
        def edit():
            self.edit_task_dialog(task)

        edit_btn = tk.Button(inner, text="✏️", font=("Segoe UI", 10),
                             relief="flat", bg=inner["bg"], command=edit, cursor="hand2")
        edit_btn.pack(side="left", padx=2)

        # примечание
        note = task.get("note", "")
        if note:
            note_lbl = tk.Label(frame, text=f"📌 {note}", font=("Segoe UI", 8, "italic"),
                                bg=frame["bg"], fg="#9ca1bc", anchor="w", wraplength=400,
                                justify="left")
            note_lbl.pack(fill="x", padx=12, pady=(0, 4))

    def open_add_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая задача")
        dialog.geometry("350x320")
        dialog.configure(bg="#2d2e3a")
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Задача:", bg="#2d2e3a", fg="white").pack(pady=(10,0), anchor="w", padx=20)
        entry_text = tk.Entry(dialog, width=40, bg="#1b1c26", fg="white", insertbackground="white")
        entry_text.pack(padx=20, pady=5, fill="x")

        tk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):", bg="#2d2e3a", fg="white").pack(anchor="w", padx=20)
        entry_date = tk.Entry(dialog, width=40, bg="#1b1c26", fg="white")
        entry_date.pack(padx=20, pady=5, fill="x")

        tk.Label(dialog, text="Примечание / этап:", bg="#2d2e3a", fg="white").pack(anchor="w", padx=20)
        text_note = tk.Text(dialog, height=4, width=40, bg="#1b1c26", fg="white")
        text_note.pack(padx=20, pady=5, fill="x")

        def save():
            text = entry_text.get().strip()
            if not text:
                messagebox.showwarning("Ошибка", "Введите текст задачи")
                return
            due = entry_date.get().strip()
            if due and not self.valid_date(due):
                messagebox.showwarning("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
                return
            note = text_note.get("1.0", tk.END).strip()
            new_id = int(datetime.now().timestamp() * 1000)
            new_task = {
                "id": new_id,
                "text": text,
                "due_date": due if due else None,
                "completed": False,
                "completed_date": None,
                "note": note
            }
            self.tasks.append(new_task)
            save_tasks(self.tasks)
            self.refresh_list()
            dialog.destroy()

        btn_save = tk.Button(dialog, text="Добавить", bg="#5f7fbf", fg="white",
                             command=save, relief="flat", font=("Segoe UI", 10))
        btn_save.pack(pady=15)

    def edit_task_dialog(self, task):
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать задачу")
        dialog.geometry("350x320")
        dialog.configure(bg="#2d2e3a")
        dialog.grab_set()

        tk.Label(dialog, text="Задача:", bg="#2d2e3a", fg="white").pack(pady=(10,0), anchor="w", padx=20)
        entry_text = tk.Entry(dialog, width=40, bg="#1b1c26", fg="white")
        entry_text.insert(0, task["text"])
        entry_text.pack(padx=20, pady=5, fill="x")

        tk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):", bg="#2d2e3a", fg="white").pack(anchor="w", padx=20)
        entry_date = tk.Entry(dialog, width=40, bg="#1b1c26", fg="white")
        entry_date.insert(0, task.get("due_date", ""))
        entry_date.pack(padx=20, pady=5, fill="x")

        tk.Label(dialog, text="Примечание / этап:", bg="#2d2e3a", fg="white").pack(anchor="w", padx=20)
        text_note = tk.Text(dialog, height=4, width=40, bg="#1b1c26", fg="white")
        text_note.insert("1.0", task.get("note", ""))
        text_note.pack(padx=20, pady=5, fill="x")

        def update():
            new_text = entry_text.get().strip()
            if not new_text:
                messagebox.showwarning("Ошибка", "Текст не может быть пустым")
                return
            new_date = entry_date.get().strip()
            if new_date and not self.valid_date(new_date):
                messagebox.showwarning("Ошибка", "Неверный формат даты")
                return
            new_note = text_note.get("1.0", tk.END).strip()
            task["text"] = new_text
            task["due_date"] = new_date if new_date else None
            task["note"] = new_note
            save_tasks(self.tasks)
            self.refresh_list()
            dialog.destroy()

        btn_update = tk.Button(dialog, text="Сохранить", bg="#5f7fbf", fg="white",
                               command=update, relief="flat")
        btn_update.pack(pady=15)

    @staticmethod
    def valid_date(d):
        try:
            datetime.strptime(d, "%Y-%m-%d")
            return True
        except:
            return False

# ------------------- ЗАПУСК -------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskWidget(root)
    root.mainloop()