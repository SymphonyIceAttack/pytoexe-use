import tkinter as tk
from tkinter import filedialog, messagebox
import os

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Новый документ")
        self.root.geometry("900x600")

        self.dark_theme = {
            "bg": "#2E3440",
            "toolbar_bg": "#3B4252",
            "button_bg": "#434C5E",
            "button_fg": "white",
            "text_bg": "#4C566A",
            "text_fg": "#D8DEE9",
            "insert_bg": "white",
            "select_bg": "#5E81AC"
        }

        self.light_theme = {
            "bg": "#FFFFFF",
            "toolbar_bg": "#F0F0F0",
            "button_bg": "#E0E0E0",
            "button_fg": "black",
            "text_bg": "#FFFFFF",
            "text_fg": "black",
            "insert_bg": "black",
            "select_bg": "#B0E2FF"
        }

        self.current_theme = self.dark_theme  # Начальная тема - темная
        self.root.configure(bg=self.current_theme["bg"])

        self.toolbar = tk.Frame(self.root, bg=self.current_theme["toolbar_bg"], width=150)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)

        buttons = [
            ("Новый", self.new_file), ("Открыть", self.open_file),
            ("Сохранить", self.save_file), ("Копировать", self.copy_text),
            ("Вставить", self.paste_text), ("Инверт. регистр", self.invert_case),
            ("Буфер", self.show_clipboard), ("Выделить все", self.select_all),
            ("Eng/Рус", self.translate_text), ("Сменить тему", self.toggle_theme)  # Добавлена кнопка смены темы
        ]
        for text, command in buttons:
            button = tk.Button(self.toolbar, text=text, command=command, bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"], bd=0, padx=10, pady=5, relief=tk.FLAT, highlightthickness=0)
            button.pack(pady=5, fill=tk.X)
            # Сохраняем ссылку на button, чтобы можно было её перекрашивать при смене темы.
            setattr(self, f"{text.replace('/', '_').replace(' ', '_').lower()}_button", button)

        self.text_area = tk.Text(self.root, wrap=tk.WORD, font=("Consolas", 12), bg=self.current_theme["text_bg"], fg=self.current_theme["text_fg"], insertbackground=self.current_theme["insert_bg"], selectbackground=self.current_theme["select_bg"], bd=0)
        self.text_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10), pady=10)

        self.current_file = None

    def apply_theme(self):
        self.root.configure(bg=self.current_theme["bg"])
        self.toolbar.configure(bg=self.current_theme["toolbar_bg"])
        self.text_area.configure(bg=self.current_theme["text_bg"], fg=self.current_theme["text_fg"], insertbackground=self.current_theme["insert_bg"], selectbackground=self.current_theme["select_bg"])

        for text, command in [
            ("Новый", self.new_file), ("Открыть", self.open_file),
            ("Сохранить", self.save_file), ("Копировать", self.copy_text),
            ("Вставить", self.paste_text), ("Инверт. регистр", self.invert_case),
            ("Буфер", self.show_clipboard), ("Выделить все", self.select_all),
            ("Eng/Рус", self.translate_text), ("Сменить тему", self.toggle_theme)
        ]:
            button_name = f"{text.replace('/', '_').replace(' ', '_').lower()}_button"
            button = getattr(self, button_name)
            button.configure(bg=self.current_theme["button_bg"], fg=self.current_theme["button_fg"])




    def toggle_theme(self):
        if self.current_theme == self.dark_theme:
            self.current_theme = self.light_theme
        else:
            self.current_theme = self.dark_theme
        self.apply_theme()

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

    def translate_text(self):
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
            selected_text = self.text_area.get(start, end)
            translated_text = self.translate(selected_text)
            self.text_area.delete(start, end)
            self.text_area.insert(start, translated_text)
        except tk.TclError:
            messagebox.showinfo("Перевод", "Выделите текст для перевода.")

    def translate(self, text):
        eng_to_rus = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
            'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
            'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '?': ',',
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
            'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э',
            'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь', '<': 'Б', '>': 'Ю', '@': '"', '#': '№', '$': ';', '^': ':', '&': '?'
        }
        rus_to_eng = {v: k for k, v in eng_to_rus.items()}  #Reverse dict

        translated = ""
        for char in text:
            if char in eng_to_rus:
                translated += eng_to_rus[char]
            elif char in rus_to_eng:
                translated += rus_to_eng[char]
            else:
                translated += char
        return translated

if __name__ == "__main__":
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()
