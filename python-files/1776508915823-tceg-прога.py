import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, BooleanVar, Checkbutton

# Расширения, считающиеся фотографиями
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}

def natural_sort_key(filename):
    """Естественная сортировка: 1, 2, 10, а не 1, 10, 2."""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', filename)]

class RenameApp:
    def __init__(self, master):
        self.master = master
        master.title("Массовое переименование фото")
        master.geometry("600x500")
        master.resizable(True, True)

        # Выбор папки
        tk.Label(master, text="Основная папка:").pack(pady=(10,0))
        self.folder_path = tk.StringVar()
        frame_folder = tk.Frame(master)
        frame_folder.pack(pady=5)
        tk.Entry(frame_folder, textvariable=self.folder_path, width=55).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_folder, text="Обзор", command=self.browse_folder).pack(side=tk.LEFT)

        # Чекбокс для обработки вложенных папок
        self.process_subfolders = BooleanVar(value=False)
        Checkbutton(master, text="Обработать все вложенные папки (подкаталоги)",
                    variable=self.process_subfolders).pack(pady=5)

        # Год
        tk.Label(master, text="Год для имени файла:").pack()
        self.year = tk.StringVar(value="2026")
        tk.Entry(master, textvariable=self.year, width=20, justify='center').pack(pady=5)

        # Кнопка запуска
        tk.Button(master, text="Запустить переименование", command=self.rename_files,
                  bg="#4CAF50", fg="white", padx=10, pady=5).pack(pady=10)

        # Область вывода сообщений
        tk.Label(master, text="Результаты:").pack()
        self.output_text = scrolledtext.ScrolledText(master, width=80, height=18, state='disabled')
        self.output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def log(self, message):
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
        self.master.update()

    def rename_in_folder(self, folder_path, year):
        """Переименовывает все изображения в одной конкретной папке."""
        folder_name = os.path.basename(folder_path)
        all_files = os.listdir(folder_path)
        image_files = []
        for f in all_files:
            full = os.path.join(folder_path, f)
            if os.path.isfile(full):
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    image_files.append(f)

        if not image_files:
            return 0, []

        image_files.sort(key=natural_sort_key)
        renamed = 0
        errors = []

        for idx, old_name in enumerate(image_files, start=1):
            old_path = os.path.join(folder_path, old_name)
            ext = os.path.splitext(old_name)[1]
            new_name = f"№{folder_name}-{year}-{idx}{ext}"
            new_path = os.path.join(folder_path, new_name)

            if old_name == new_name:
                continue
            if os.path.exists(new_path):
                errors.append(f"[!] {new_name} уже существует, пропущен ({old_name})")
                continue

            try:
                os.rename(old_path, new_path)
                renamed += 1
            except Exception as e:
                errors.append(f"[X] Ошибка переименования {old_name}: {e}")

        return renamed, errors

    def rename_files(self):
        root_folder = self.folder_path.get().strip()
        year = self.year.get().strip()
        process_subs = self.process_subfolders.get()

        # Проверки
        if not root_folder:
            messagebox.showerror("Ошибка", "Выберите папку!")
            return
        if not os.path.isdir(root_folder):
            messagebox.showerror("Ошибка", "Указанная папка не существует!")
            return
        if not year.isdigit() or len(year) != 4:
            messagebox.showerror("Ошибка", "Год должен быть числом из 4 цифр (например, 2026)!")
            return

        self.log("=" * 60)
        self.log(f"[*] Главная папка: {root_folder}")
        self.log(f"[*] Год: {year}")
        self.log(f"[*] Обработка вложенных папок: {'ДА' if process_subs else 'НЕТ'}")
        self.log("=" * 60)

        if not process_subs:
            # Обрабатываем только выбранную папку
            renamed, errors = self.rename_in_folder(root_folder, year)
            self.log(f"[>] Папка: {os.path.basename(root_folder)}")
            self.log(f"[+] Переименовано файлов: {renamed}")
            for err in errors:
                self.log(err)
        else:
            # Обрабатываем все подпапки первого уровня
            total_renamed = 0
            subdirs = [d for d in os.listdir(root_folder)
                       if os.path.isdir(os.path.join(root_folder, d))]
            if not subdirs:
                self.log("[!] В выбранной папке нет вложенных подкаталогов.")
            else:
                self.log(f"[i] Найдено подкаталогов: {len(subdirs)}")
                self.log("-" * 40)
                for sub in subdirs:
                    sub_path = os.path.join(root_folder, sub)
                    self.log(f"[>] Обработка: {sub}")
                    renamed, errors = self.rename_in_folder(sub_path, year)
                    total_renamed += renamed
                    if renamed:
                        self.log(f"    [+] Переименовано: {renamed} файл(ов)")
                    if errors:
                        for err in errors:
                            self.log(f"    {err}")
                    if renamed == 0 and not errors:
                        self.log("    [i] Нет изображений для переименования.")
                self.log("-" * 40)
                self.log(f"[++] ИТОГО переименовано файлов во всех папках: {total_renamed}")

        self.log("=" * 60)
        messagebox.showinfo("Готово", "Операция завершена.\nПодробности в окне вывода.")

def main():
    root = tk.Tk()
    app = RenameApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()