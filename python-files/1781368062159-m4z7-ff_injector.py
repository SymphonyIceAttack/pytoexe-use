import json
import os
import subprocess
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Entry, Button, Text, Scrollbar, Listbox,
    messagebox, END, BOTH, RIGHT, LEFT, Y, filedialog
)
import tkinter as tk

# --- Конфигурация ---
APP_NAME = "FastFlag Injector"
VERSION = "1.0"

DEFAULT_FLAGS = {
    "FFlagDebugGraphicsPreferD3D11": "True",
    "DFIntTaskSchedulerTargetFps": "240"
}

# Функция для правильного поиска файлов при сборке в exe
def get_resource_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(os.path.dirname(os.path.abspath(__file__)))

BLOXSTRAP_FLAGS_PATH = Path(os.getenv('LOCALAPPDATA', '')) / 'Bloxstrap' / 'Modifications' / 'FastFlags.json'


class FastFlagInjectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.configure(bg='#2b2b2b')

        self.flags = DEFAULT_FLAGS.copy()
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_flags_list)

        self.setup_ui()
        self.refresh_flags_display()
        self.load_existing_flags()

    def setup_ui(self):
        main_frame = Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # --- Верхняя панель ---
        top_frame = Frame(main_frame, bg='#2b2b2b')
        top_frame.pack(fill='x', pady=(0, 10))

        Label(top_frame, text="Поиск флага:", bg='#2b2b2b', fg='white').pack(side=LEFT, padx=(0, 5))
        Entry(top_frame, textvariable=self.search_var, width=30, bg='#3c3c3c', fg='white', insertbackground='white').pack(side=LEFT, padx=(0, 10))

        Button(top_frame, text="+ Добавить флаг", command=self.add_flag_dialog, bg='#4CAF50', fg='white').pack(side=RIGHT, padx=(5, 0))
        Button(top_frame, text="Импорт JSON", command=self.import_json, bg='#2196F3', fg='white').pack(side=RIGHT)

        # --- Центральная область ---
        center_frame = Frame(main_frame, bg='#2b2b2b')
        center_frame.pack(fill=BOTH, expand=True)

        # Левая панель
        left_panel = Frame(center_frame, width=300, bg='#2b2b2b')
        left_panel.pack(side=LEFT, fill=BOTH, expand=False)
        left_panel.pack_propagate(False)

        Label(left_panel, text="Список флагов:", font=('Arial', 10, 'bold'), bg='#2b2b2b', fg='white').pack(anchor='w')

        listbox_frame = Frame(left_panel, bg='#2b2b2b')
        listbox_frame.pack(fill=BOTH, expand=True, pady=(5, 0))

        self.flags_listbox = Listbox(listbox_frame, selectmode='single', exportselection=False, bg='#3c3c3c', fg='white', selectbackground='#4CAF50')
        self.flags_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.flags_listbox.bind('<<ListboxSelect>>', self.on_flag_select)

        scrollbar = Scrollbar(listbox_frame, orient='vertical', command=self.flags_listbox.yview, bg='#2b2b2b')
        scrollbar.pack(side=RIGHT, fill=Y)
        self.flags_listbox.config(yscrollcommand=scrollbar.set)

        # Правая панель
        right_panel = Frame(center_frame, bg='#2b2b2b')
        right_panel.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        Label(right_panel, text="Редактор флага:", font=('Arial', 10, 'bold'), bg='#2b2b2b', fg='white').pack(anchor='w')

        flag_name_frame = Frame(right_panel, bg='#2b2b2b')
        flag_name_frame.pack(fill='x', pady=5)
        Label(flag_name_frame, text="Название:", width=10, anchor='w', bg='#2b2b2b', fg='white').pack(side=LEFT)
        self.flag_name_entry = Entry(flag_name_frame, bg='#3c3c3c', fg='white', insertbackground='white')
        self.flag_name_entry.pack(side=LEFT, fill='x', expand=True)

        flag_value_frame = Frame(right_panel, bg='#2b2b2b')
        flag_value_frame.pack(fill='x', pady=5)
        Label(flag_value_frame, text="Значение:", width=10, anchor='w', bg='#2b2b2b', fg='white').pack(side=LEFT)
        self.flag_value_entry = Entry(flag_value_frame, bg='#3c3c3c', fg='white', insertbackground='white')
        self.flag_value_entry.pack(side=LEFT, fill='x', expand=True)

        btn_frame = Frame(right_panel, bg='#2b2b2b')
        btn_frame.pack(fill='x', pady=10)
        Button(btn_frame, text="Сохранить изменения", command=self.save_current_flag, bg='#FF9800', fg='white').pack(side=LEFT, padx=5)
        Button(btn_frame, text="Удалить флаг", command=self.delete_current_flag, bg='#f44336', fg='white').pack(side=LEFT, padx=5)

        # --- Нижняя панель ---
        bottom_frame = Frame(main_frame, bg='#2b2b2b')
        bottom_frame.pack(fill=BOTH, expand=True, pady=(10, 0))

        Label(bottom_frame, text="JSON для вставки в Bloxstrap:", font=('Arial', 9, 'bold'), bg='#2b2b2b', fg='white').pack(anchor='w')

        text_frame = Frame(bottom_frame, bg='#2b2b2b')
        text_frame.pack(fill=BOTH, expand=True)

        self.json_text = Text(text_frame, wrap='word', height=10, bg='#1e1e1e', fg='#d4d4d4', insertbackground='white')
        self.json_text.pack(side=LEFT, fill=BOTH, expand=True)

        json_scrollbar = Scrollbar(text_frame, orient='vertical', command=self.json_text.yview, bg='#2b2b2b')
        json_scrollbar.pack(side=RIGHT, fill=Y)
        self.json_text.config(yscrollcommand=json_scrollbar.set)

        # Кнопки действий
        action_frame = Frame(main_frame, bg='#2b2b2b')
        action_frame.pack(fill='x', pady=(10, 0))

        Button(action_frame, text="Копировать JSON", command=self.copy_json, bg='#9C27B0', fg='white').pack(side=LEFT, padx=5)
        Button(action_frame, text="Экспорт JSON", command=self.export_json, bg='#9C27B0', fg='white').pack(side=LEFT, padx=5)
        Button(action_frame, text="Применить (Bloxstrap)", command=self.apply_flags, bg="#4CAF50", fg="white").pack(side=RIGHT, padx=5)
        Button(action_frame, text="Сбросить", command=self.reset_flags, bg="#f44336", fg="white").pack(side=RIGHT, padx=5)

    def refresh_flags_display(self):
        self.flags_listbox.delete(0, END)
        for flag_name in sorted(self.flags.keys()):
            self.flags_listbox.insert(END, flag_name)
        self.update_json_display()

    def filter_flags_list(self, *args):
        search_term = self.search_var.get().lower()
        self.flags_listbox.delete(0, END)
        for flag_name in sorted(self.flags.keys()):
            if search_term in flag_name.lower():
                self.flags_listbox.insert(END, flag_name)

    def update_json_display(self):
        try:
            json_data = json.dumps(self.flags, indent=2, ensure_ascii=False)
            self.json_text.delete(1.0, END)
            self.json_text.insert(END, json_data)
        except Exception as e:
            self.json_text.delete(1.0, END)
            self.json_text.insert(END, f"# Ошибка генерации JSON: {e}")

    def on_flag_select(self, event):
        selection = self.flags_listbox.curselection()
        if selection:
            flag_name = self.flags_listbox.get(selection[0])
            self.flag_name_entry.delete(0, END)
            self.flag_name_entry.insert(0, flag_name)
            self.flag_value_entry.delete(0, END)
            self.flag_value_entry.insert(0, str(self.flags.get(flag_name, "")))

    def add_flag_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить флаг")
        dialog.geometry("400x200")
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.configure(bg='#2b2b2b')

        Label(dialog, text="Название флага:", font=('Arial', 10), bg='#2b2b2b', fg='white').pack(pady=(20, 5))
        name_entry = Entry(dialog, width=40, bg='#3c3c3c', fg='white', insertbackground='white')
        name_entry.pack(pady=5)

        Label(dialog, text="Значение флага:", font=('Arial', 10), bg='#2b2b2b', fg='white').pack(pady=5)
        value_entry = Entry(dialog, width=40, bg='#3c3c3c', fg='white', insertbackground='white')
        value_entry.pack(pady=5)

        def add():
            name = name_entry.get().strip()
            value = value_entry.get().strip()
            if name and value:
                self.flags[name] = value
                self.refresh_flags_display()
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Заполните оба поля.", parent=dialog)

        Button(dialog, text="Добавить", command=add, bg="#4CAF50", fg="white").pack(pady=20)

    def save_current_flag(self):
        flag_name = self.flag_name_entry.get().strip()
        flag_value = self.flag_value_entry.get().strip()

        if not flag_name:
            messagebox.showerror("Ошибка", "Название флага не может быть пустым.")
            return

        selection = self.flags_listbox.curselection()
        if selection:
            old_name = self.flags_listbox.get(selection[0])
            if old_name and old_name != flag_name:
                del self.flags[old_name]

        self.flags[flag_name] = flag_value
        self.refresh_flags_display()

        for i, name in enumerate(self.flags_listbox.get(0, END)):
            if name == flag_name:
                self.flags_listbox.selection_set(i)
                break

    def delete_current_flag(self):
        selection = self.flags_listbox.curselection()
        if selection:
            flag_name = self.flags_listbox.get(selection[0])
            if messagebox.askyesno("Подтверждение", f"Удалить флаг '{flag_name}'?"):
                del self.flags[flag_name]
                self.refresh_flags_display()
                self.flag_name_entry.delete(0, END)
                self.flag_value_entry.delete(0, END)

    def import_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_flags = json.load(f)
                if isinstance(imported_flags, dict):
                    self.flags.update(imported_flags)
                    self.refresh_flags_display()
                    messagebox.showinfo("Успех", f"Импортировано {len(imported_flags)} флагов.")
                else:
                    messagebox.showerror("Ошибка", "Неверный формат JSON. Ожидается словарь.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать файл:\n{e}")

    def export_json(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.flags, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Успех", f"Флаги сохранены в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

    def copy_json(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.json_text.get(1.0, END).strip())
        messagebox.showinfo("Успех", "JSON скопирован в буфер обмена.")

    def apply_flags(self):
        try:
            BLOXSTRAP_FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)

            with open(BLOXSTRAP_FLAGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.flags, f, indent=2, ensure_ascii=False)

            local_appdata = os.getenv('LOCALAPPDATA', '')
            program_files = os.getenv('PROGRAMFILES', 'C:\\Program Files')
            program_files_x86 = os.getenv('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')

            possible_paths = [
                Path(local_appdata) / 'Bloxstrap' / 'Bloxstrap.exe',
                Path(program_files) / 'Bloxstrap' / 'Bloxstrap.exe',
                Path(program_files_x86) / 'Bloxstrap' / 'Bloxstrap.exe'
            ]

            bloxstrap_path = None
            for path in possible_paths:
                if path.exists():
                    bloxstrap_path = str(path)
                    break

            if bloxstrap_path:
                subprocess.Popen([bloxstrap_path, "launch"], shell=False)
                messagebox.showinfo(
                    "Успех",
                    "Флаги сохранены и Roblox запущен через Bloxstrap.\n\n"
                    "Важно: Не все флаги могут работать из-за белого списка Roblox."
                )
            else:
                messagebox.showwarning(
                    "Bloxstrap не найден",
                    f"Флаги сохранены в:\n{BLOXSTRAP_FLAGS_PATH}\n\n"
                    "Установите Bloxstrap с https://bloxstrap.xyz\n\n"
                    "Или вставьте JSON вручную в настройках Bloxstrap."
                )

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить флаги:\n{e}")

    def reset_flags(self):
        if messagebox.askyesno("Подтверждение", "Сбросить все флаги к значениям по умолчанию?"):
            self.flags = DEFAULT_FLAGS.copy()
            self.refresh_flags_display()
            self.flag_name_entry.delete(0, END)
            self.flag_value_entry.delete(0, END)

    def load_existing_flags(self):
        if BLOXSTRAP_FLAGS_PATH.exists():
            try:
                with open(BLOXSTRAP_FLAGS_PATH, 'r', encoding='utf-8') as f:
                    existing_flags = json.load(f)
                if isinstance(existing_flags, dict):
                    self.flags = existing_flags
                    self.refresh_flags_display()
            except (json.JSONDecodeError, IOError):
                pass


def main():
    root = Tk()
    app = FastFlagInjectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    import sys
    main()