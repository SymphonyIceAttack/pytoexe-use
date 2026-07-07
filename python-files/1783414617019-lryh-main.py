import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import json
from tkinter import ttk
from tkinter.simpledialog import askstring

try:
    from docx import Document
except ImportError:
    messagebox.showerror("Ошибка", "Библиотека 'python-docx' не установлена.\nУстановите её командой: pip install python-docx")
    exit()

# Путь к файлу для хранения данных
DATA_FILE = 'organizer_data.json'

# Загружаем существующие данные или создаем новые
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    data = {}

# Функции для работы с данными
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_category():
    cat = category_entry.get().strip()
    if cat and cat not in data:
        data[cat] = []
        update_category_list()
        save_data()
        category_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Внимание", "Введите уникальное название категории.")

def delete_category():
    selected = category_listbox.curselection()
    if selected:
        cat = category_listbox.get(selected)
        if messagebox.askyesno("Удаление", f"Удалить категорию '{cat}'?"):
            del data[cat]
            update_category_list()
            update_file_list()
            save_data()

def update_category_list():
    category_listbox.delete(0, tk.END)
    for cat in sorted(data):
        category_listbox.insert(tk.END, cat)

def select_files():
    selected = category_listbox.curselection()
    if not selected:
        messagebox.showwarning("Внимание", "Выберите категорию.")
        return
    cat = category_listbox.get(selected)
    files = filedialog.askopenfilenames(title="Выберите файлы", filetypes=[("Текстовые файлы", "*.txt"), ("Word файлы", "*.docx")])
    for file_path in files:
        if file_path not in data[cat]:
            data[cat].append(file_path)
    update_file_list()
    save_data()

def update_file_list():
    file_listbox.delete(0, tk.END)
    selected = category_listbox.curselection()
    if not selected:
        return
    cat = category_listbox.get(selected)
    for file_path in data[cat]:
        filename = os.path.basename(file_path)
        file_listbox.insert(tk.END, filename)

def open_file():
    selected_cat_idx = category_listbox.curselection()
    selected_file_idx = file_listbox.curselection()
    if not selected_cat_idx or not selected_file_idx:
        messagebox.showwarning("Внимание", "Выберите файл для открытия.")
        return
    cat = category_listbox.get(selected_cat_idx)
    filename = data[cat][selected_file_idx[0]]
    try:
        if os.name == 'nt':  # Windows
            os.startfile(filename)
        elif os.name == 'posix':  # Linux/macOS
            import subprocess
            subprocess.call(('xdg-open', filename))
        else:
            messagebox.showinfo("Информация", "Открытие файла не поддерживается для этой ОС.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def delete_file():
    selected_cat_idx = category_listbox.curselection()
    selected_file_idx = file_listbox.curselection()
    if not selected_cat_idx or not selected_file_idx:
        messagebox.showwarning("Внимание", "Выберите файл для удаления.")
        return
    cat = category_listbox.get(selected_cat_idx)
    filename = data[cat][selected_file_idx[0]]
    if messagebox.askyesno("Удаление", f"Удалить файл '{os.path.basename(filename)}'?"):
        data[cat].pop(selected_file_idx[0])
        update_file_list()

def preview_file():
    selected_cat_idx = category_listbox.curselection()
    selected_file_idx = file_listbox.curselection()
    if not selected_cat_idx or not selected_file_idx:
        messagebox.showwarning("Внимание", "Выберите файл для предпросмотра.")
        return
    cat = category_listbox.get(selected_cat_idx)
    filename = data[cat][selected_file_idx[0]]
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext == '.txt':
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            show_text_window(content, os.path.basename(filename))
        elif ext == '.docx':
            doc = Document(filename)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            show_text_window(full_text, os.path.basename(filename))
        else:
            messagebox.showinfo("Информация", "Просмотр поддерживается только для .txt и .docx файлов.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def show_text_window(content, title):
    preview_win = tk.Toplevel(root)
    preview_win.title(f"Просмотр: {title}")
    preview_win.geometry("600x400")
    txt = scrolledtext.ScrolledText(preview_win, wrap=tk.WORD)
    txt.pack(fill=tk.BOTH, expand=True)
    txt.insert(tk.END, content)
    txt.config(state=tk.DISABLED)

def on_category_select(event):
    update_file_list()

# Создаем основное окно
root = tk.Tk()
root.title("Файловый органайзер txt/docx")
root.geometry("800x600")
root.resizable(False, False)

# Стиль
style = ttk.Style()
style.theme_use('clam')

# Левая панель
frame_left = tk.Frame(root, width=250, padx=5, pady=5)
frame_left.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(frame_left, text="Категории", font=("Arial", 12, "bold")).pack(pady=5)

category_listbox = tk.Listbox(frame_left, height=15)
category_listbox.pack(fill=tk.BOTH, expand=True)
category_listbox.bind('<<ListboxSelect>>', on_category_select)

category_entry = tk.Entry(frame_left)
category_entry.pack(pady=5, fill=tk.X)

btn_add_cat = tk.Button(frame_left, text="Добавить категорию", command=add_category)
btn_add_cat.pack(fill=tk.X, pady=2)

btn_del_cat = tk.Button(frame_left, text="Удалить категорию", command=delete_category)
btn_del_cat.pack(fill=tk.X, pady=2)

btn_load_files = tk.Button(frame_left, text="Загрузить файлы", command=select_files)
btn_load_files.pack(fill=tk.X, pady=2)

# Правая панель
frame_right = tk.Frame(root, padx=5, pady=5)
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Label(frame_right, text="Файлы", font=("Arial", 12, "bold")).pack(pady=5)

file_listbox = tk.Listbox(frame_right, height=15)
file_listbox.pack(fill=tk.BOTH, expand=True)

# Кнопки для работы с файлами
buttons_frame = tk.Frame(frame_right)
buttons_frame.pack(fill=tk.X, pady=5)

btn_open = tk.Button(buttons_frame, text="Открыть файл", command=open_file)
btn_open.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

btn_delete = tk.Button(buttons_frame, text="Удалить файл", command=delete_file)
btn_delete.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

btn_preview = tk.Button(buttons_frame, text="Просмотр", command=preview_file)
btn_preview.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

# Инициализация списка категорий
update_category_list()

# Запуск
try:
    root.mainloop()
finally:
    save_data()