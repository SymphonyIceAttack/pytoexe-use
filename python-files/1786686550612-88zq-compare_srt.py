import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox

class SrtComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнение SRT-файлов")
        self.root.geometry("650x300")
        
        self.file1_path = tk.StringVar() # Файл с потенциальными новыми фразами
        self.file2_path = tk.StringVar() # Файл для сравнения
        
        # Поле 1
        tk.Label(root, text="Выберите файл *.srt, в котором могут быть новые фразы:").place(x=20, y=20)
        self.file1_entry = tk.Entry(root, textvariable=self.file1_path, width=55)
        self.file1_entry.place(x=20, y=50)
        tk.Button(root, text="Обзор", command=self.select_file1).place(x=500, y=45)
        
        # Поле 2
        tk.Label(root, text="Выберите файл *.srt, с которым будем сравнивать:").place(x=20, y=90)
        self.file2_entry = tk.Entry(root, textvariable=self.file2_path, width=55)
        self.file2_entry.place(x=20, y=120)
        tk.Button(root, text="Обзор", command=self.select_file2).place(x=500, y=115)

        # Кнопка сравнения
        tk.Button(root, text="Сравнить", 
                  command=self.run_comparison,
                  bg="#4CAF50", fg="white", font=('Arial', 12, 'bold')).place(x=250, y=180, width=120)

    def select_file1(self):
        path = filedialog.askopenfilename(
            title="Выберите первый SRT-файл",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if path:
            self.file1_path.set(path)

    def select_file2(self):
        path = filedialog.askopenfilename(
            title="Выберите второй SRT-файл для сравнения",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if path:
            self.file2_path.set(path)

    def extract_replicas_with_time(self, part):
        """Извлекает реплики с таймингом и нормализованным текстом для поиска."""
        blocks = re.split(r'\r?\n\r?\n', part)
        replicas = []
        for block in blocks:
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', block)
            if not time_match:
                continue
                
            lines = block.splitlines()
            # Находим строку с таймингом
            for i, line in enumerate(lines):
                if time_match and time_match.group(0) in line:
                    text_start = i + 1
                    break
            else:
                continue

            # Собираем текст реплики (может быть многострочным)
            text_lines = lines[text_start:]
            text_replica = '\n'.join(text_lines).strip()
            if not text_replica:
                continue

            # Нормализация: убираем знаки препинания и лишние пробелы для сравнения
            norm = re.sub(r'[^a-zA-Z0-9 ]', '', text_replica).lower()
            norm = re.sub(r' +', ' ', norm).strip()
            
            replicas.append({'start': time_match.group(1), 'end': time_match.group(2), 'orig': text_replica, 'norm': norm})
            
        return replicas

    def run_comparison(self):
        file1 = self.file1_path.get() # Источник (где ищем новые фразы)
        file2 = self.file2_path.get() # С чем сравниваем
        
        if not file1 or not file2:
            messagebox.showwarning("Ошибка", "Пожалуйста, выберите оба файла.")
            return

        try:
            with open(file1, 'r', encoding='utf-8-sig') as f:
                file1_text = f.read()
                
            with open(file2, 'r', encoding='utf-8-sig') as f:
                file2_text = f.read()
                
            replicas_file1 = self.extract_replicas_with_time(file1_text)
            replicas_file2 = self.extract_replicas_with_time(file2_text)
            
            # Множество нормализованных реплик второго файла для быстрого поиска
            set_file2_norms = set(r['norm'] for r in replicas_file2)
            
            # Ищем реплики из первого файла (file1), которых нет во втором (file2)
            missing_in_file2 = [r for r in replicas_file1 if r['norm'] not in set_file2_norms]

            if not missing_in_file2:
                messagebox.showinfo("Результат", "Все реплики из первого файла найдены во втором.")
                return

            # Сохранение результата в формате SRT
            folder = os.path.dirname(file1)
            base_name = os.path.splitext(os.path.basename(file1))[0]
            
            # Суффикс зависит от того, что мы нашли (отсутствующие относительно второго файла)
            output_file = os.path.join(folder, f"{base_name}_missing_from_second.srt")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, r in enumerate(missing_in_file2, start=1):
                    f.write(f"{i}\n")
                    f.write(f"{r['start']} --> {r['end']}\n")
                    f.write(f"{r['orig']}\n")
                    f.write("\n") # Пустая строка между блоками SRT

            messagebox.showinfo("Готово!", f"Реплики сохранены в:\n{output_file}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SrtComparatorApp(root)
    root.mainloop()