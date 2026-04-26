import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os

class Notepad:
    def __init__(self, root):
        self.root = root
        self.root.title("Простой блокнот")
        self.root.geometry("800x600")

        # Текстовое поле
        self.text_area = tk.Text(self.root, wrap="word", undo=True)
        self.text_area.pack(expand=True, fill="both", padx=5, pady=5)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(self.text_area, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)

        self.current_file = None
        self.create_menu()

    def create_menu(self):
        """Создание меню"""
        menu_bar = tk.Menu(self.root)

        # Меню «Файл»
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Новый", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.exit_app)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        # Меню «Правка»
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Отменить", command=self.text_area.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.text_area.edit_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Вырезать", command=lambda: self.root.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="Копировать", command=lambda: self.root.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить", command=lambda: self.root.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Найти", command=self.find_text, accelerator="Ctrl+F")
        menu_bar.add_cascade(label="Правка", menu=edit_menu)

        self.root.config(menu=menu_bar)

        # Горячие клавиши
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-f>', lambda e: self.find_text())

    def new_file(self):
        """Создать новый файл"""
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Новый файл - Простой блокнот")

    def open_file(self):
        """Открыть существующий файл"""
        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - Простой блокнот")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def save_file(self):
        """Сохранить текущий файл"""
        if self.current_file:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                messagebox.showinfo("Успех", "Файл сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
        else:
            self.save_as()

    def save_as(self):
        """Сохранить файл с новым именем"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if file_path:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - Простой блокнот")
                messagebox.showinfo("Успех", "Файл сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def find_text(self):
        """Поиск текста в документе"""
        def find():
            text_to_find = find_entry.get()
            if text_to_find:
                start_pos = "1.0"
                while True:
                    start_pos = self.text_area.search(text_to_find, start_pos, stopindex=tk.END)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(text_to_find)}c"
                    self.text_area.tag_add("found", start_pos, end_pos)
                    start_pos = end_pos
                self.text_area.tag_config("found", background="yellow")

        find_window = tk.Toplevel(self.root)
        find_window.title("Найти")
        find_window.geometry("300x100")

        tk.Label(find_window, text="Найти:").pack(pady=5)
        find_entry = tk.Entry(find_window, width=30)
        find_entry.pack(pady=5)
        tk.Button(find_window, text="Найти", command=find).pack(pady=5)

    def exit_app(self):
        """Выход из приложения"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()
