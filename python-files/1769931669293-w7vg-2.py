import tkinter as tk
from tkinter import filedialog, messagebox
import os

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Новый документ")
        self.root.geometry("900x600")
        self.root.configure(bg="#2E3440")

        self.toolbar = tk.Frame(self.root, bg="#3B4252", width=150)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)

        buttons = [
            ("Новый", self.new_file), ("Открыть", self.open_file),
            ("Сохранить", self.save_file), ("Копировать", self.copy_text),
            ("Вставить", self.paste_text), ("Инверт. регистр", self.invert_case),
            ("Буфер", self.show_clipboard), ("Выделить все", self.select_all)
        ]
        for text, command in buttons:
            button = tk.Button(self.toolbar, text=text, command=command, bg="#434C5E", fg="white", bd=0, padx=10, pady=5, relief=tk.FLAT, highlightthickness=0)
            button.pack(pady=5, fill=tk.X)

        self.text_area = tk.Text(self.root, wrap=tk.WORD, font=("Consolas", 12), bg="#4C566A", fg="#D8DEE9", insertbackground="white", selectbackground="#5E81AC", bd=0)
        self.text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10), pady=10)

        self.current_file = None

    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("Новый документ")

    def open_file(self): #Открытие файла
        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - Текстовый редактор")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def save_file(self):#Сохранение файла
        if self.current_file:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(self.current_file, "w", encoding="utf-8") as file:
                    file.write(content)
                messagebox.showinfo("Успех", "Файл сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self): #Сохранение как...
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if file_path:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                self.current_file = file_path
                self.root.title(f"{os.path.basename(file_path)} - Текстовый редактор")
                messagebox.showinfo("Успех", "Файл сохранён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def copy_text(self):#Копировать текст
        try:
            self.root.clipboard_clear()
            text = self.text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_append(text)
        except tk.TclError:
            pass

    def paste_text(self):#Вставить текст
        try:
            text = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def show_clipboard(self):#Показать буфер обмена
        try:
            text = self.root.clipboard_get()
            messagebox.showinfo("Буфер обмена", text)
        except tk.TclError:
            messagebox.showinfo("Буфер обмена", "Буфер обмена пуст")

    def invert_case(self):#Инвертировать регистр выделенного текста
                try:
                    start = self.text_area.index(tk.SEL_FIRST)
                    end = self.text_area.index(tk.SEL_LAST)
                    selected_text = self.text_area.get(start, end)
                    inverted_text = "".join([c.lower() if c.isupper() else c.upper() for c in selected_text])
                    self.text_area.delete(start, end)
                    self.text_area.insert(start, inverted_text)
                except tk.TclError:
                        messagebox.showinfo("Регистр", "Выделите текст для инвертирования.")
    def select_all(self):#Выделить все
        self.text_area.tag_add(tk.SEL, "1.0", tk.END)
        self.text_area.mark_set(tk.INSERT, "1.0")
        self.text_area.see(tk.INSERT)

if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
