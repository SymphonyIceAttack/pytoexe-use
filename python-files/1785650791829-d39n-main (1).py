
import ctypes
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk

from pathlib import Path
from tkinter import ttk, messagebox


APP_NAME = "UDO"
APP_VERSION = "mark 1.0"

BASE_DIR = Path(__file__).resolve().parent
PROGRAMS_DIR = BASE_DIR / "programs"
DRIVERS_DIR = BASE_DIR / "drivers"
TWEAKS_DIR = BASE_DIR / "tweaks"


# ============================================================
# СПИСОК ЭЛЕМЕНТОВ
# Для добавления новых программ изменяйте только этот список.
# ============================================================

ITEMS = {
    "programs": [
        {
            "name": "7-Zip",
            "file": PROGRAMS_DIR / "7zip.exe",
            "type": "exe",
            "icon": "▣",
            "arguments": [],
        },
        {
            "name": "VLC Media Player",
            "file": PROGRAMS_DIR / "vlc.exe",
            "type": "exe",
            "icon": "▶",
            "arguments": [],
        },
        {
            "name": "Пример MSI-пакета",
            "file": PROGRAMS_DIR / "example.msi",
            "type": "msi",
            "icon": "▤",
            "arguments": [],
        },
    ],

    "drivers": [
        {
            "name": "Пример драйвера",
            "file": DRIVERS_DIR / "example-driver.inf",
            "type": "inf",
            "icon": "⚙",
            "arguments": [],
        },
    ],

    "optimizations": [
        {
            "name": "Отключить телеметрию Windows",
            "file": TWEAKS_DIR / "disable-telemetry.reg",
            "type": "reg",
            "icon": "⚡",
            "arguments": [],
        },
        {
            "name": "Запустить оптимизацию системы",
            "file": TWEAKS_DIR / "optimize.bat",
            "type": "bat",
            "icon": "⚡",
            "arguments": [],
        },
        {
            "name": "PowerShell-твик",
            "file": TWEAKS_DIR / "optimize.ps1",
            "type": "ps1",
            "icon": "⚡",
            "arguments": [],
        },
    ],
}


def is_windows_admin():
    """Проверяет наличие прав администратора."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_as_admin():
    """
    Перезапускает программу с правами администратора.
    Используется перед установкой программ, драйверов и твиков.
    """
    if not sys.platform.startswith("win"):
        return False

    if is_windows_admin():
        return True

    try:
        script = str(Path(sys.argv[0]).resolve())
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1,
        )

        if result <= 32:
            return False

        sys.exit(0)

    except Exception as error:
        messagebox.showerror(
            "Ошибка",
            f"Не удалось получить права администратора:\n{error}",
        )
        return False


def execute_item(item):
    """
    Выполняет установку или запуск одного элемента.
    Возвращает пару: успешность и текст результата.
    """
    file_path = Path(item["file"])
    file_type = item["type"].lower()
    arguments = item.get("arguments", [])

    if not file_path.exists():
        return False, f"Файл не найден: {file_path}"

    try:
        if file_type == "exe":
            command = [str(file_path), *arguments]
            subprocess.run(command, check=True)

        elif file_type == "msi":
            command = [
                "msiexec.exe",
                "/i",
                str(file_path),
                *arguments,
            ]
            subprocess.run(command, check=True)

        elif file_type in ("bat", "cmd"):
            command = [
                "cmd.exe",
                "/c",
                str(file_path),
                *arguments,
            ]
            subprocess.run(command, check=True)

        elif file_type == "ps1":
            command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(file_path),
                *arguments,
            ]
            subprocess.run(command, check=True)

        elif file_type == "reg":
            command = [
                "reg.exe",
                "import",
                str(file_path),
            ]
            subprocess.run(command, check=True)

        elif file_type == "inf":
            # Установка драйвера средствами Windows.
            command = [
                "pnputil.exe",
                "/add-driver",
                str(file_path),
                "/install",
            ]
            subprocess.run(command, check=True)

        else:
            return False, (
                f"Неподдерживаемый тип файла: {file_type}\n"
                f"Файл: {file_path.name}"
            )

        return True, f"Успешно обработано: {item['name']}"

    except subprocess.CalledProcessError as error:
        return False, (
            f"Ошибка выполнения: {item['name']}\n"
            f"Код завершения: {error.returncode}"
        )

    except Exception as error:
        return False, f"Ошибка: {item['name']}\n{error}"


class UDOApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("UDO — Windows Utility Pack")
        self.geometry("850x600")
        self.minsize(700, 480)
        self.configure(bg="#eeeeee")

        self.variables = {
            "programs": [],
            "drivers": [],
            "optimizations": [],
        }

        self.checkbuttons = {
            "programs": [],
            "drivers": [],
            "optimizations": [],
        }

        self.log_queue = queue.Queue()

        self.create_styles()
        self.create_interface()

        self.after(100, self.process_log_queue)

    def create_styles(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TNotebook",
            background="#eeeeee",
            borderwidth=0,
        )

        style.configure(
            "TNotebook.Tab",
            padding=(18, 8),
            font=("Segoe UI", 10, "bold"),
        )

        style.configure(
            "Action.TButton",
            padding=(12, 6),
            font=("Segoe UI", 9, "bold"),
        )

        style.configure(
            "Apply.TButton",
            padding=(24, 10),
            font=("Segoe UI", 11, "bold"),
        )

    def create_interface(self):
        self.create_header()

        main_frame = tk.Frame(self, bg="#eeeeee")
        main_frame.pack(fill="both", expand=True, padx=14, pady=(12, 8))

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        self.create_tab(
            notebook,
            "programs",
            "Программы",
        )

        self.create_tab(
            notebook,
            "drivers",
            "Драйверы",
        )

        self.create_tab(
            notebook,
            "optimizations",
            "Оптимизации",
        )

        bottom_frame = tk.Frame(self, bg="#eeeeee")
        bottom_frame.pack(fill="x", padx=14, pady=(0, 12))

        self.status_label = tk.Label(
            bottom_frame,
            text="Готово к работе",
            bg="#eeeeee",
            fg="#555555",
            anchor="w",
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side="left")

        self.apply_button = ttk.Button(
            bottom_frame,
            text="Применить",
            style="Apply.TButton",
            command=self.apply_selected,
        )
        self.apply_button.pack(side="right")

    def create_header(self):
        header = tk.Frame(
            self,
            bg="#111111",
            height=30,
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        logo = tk.Label(
            header,
            text="UDO",
            bg="#111111",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        )
        logo.pack(side="left", padx=(15, 10))

        version = tk.Label(
            header,
            text=APP_VERSION,
            bg="#111111",
            fg="#cccccc",
            font=("Segoe UI", 8),
        )
        version.pack(side="left", pady=(5, 0))

    def create_tab(self, notebook, key, title):
        tab = tk.Frame(notebook, bg="#eeeeee")
        notebook.add(tab, text=title)

        toolbar = tk.Frame(tab, bg="#eeeeee")
        toolbar.pack(fill="x", padx=10, pady=10)

        reset_button = ttk.Button(
            toolbar,
            text="Сбросить",
            width=12,
            style="Action.TButton",
            command=lambda: self.uncheck_all(key),
        )
        reset_button.pack(side="left")

        select_button = ttk.Button(
            toolbar,
            text="Пометить все",
            width=12,
            style="Action.TButton",
            command=lambda: self.check_all(key),
        )
        select_button.pack(side="left", padx=(8, 0))

        count_label = tk.Label(
            toolbar,
            text=f"Всего: {len(ITEMS[key])}",
            bg="#eeeeee",
            fg="#666666",
            font=("Segoe UI", 9),
        )
        count_label.pack(side="right")

        list_container = tk.Frame(tab, bg="#ffffff", bd=1, relief="solid")
        list_container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10),
        )

        canvas = tk.Canvas(
            list_container,
            bg="#ffffff",
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=canvas.yview,
        )

        rows_frame = tk.Frame(canvas, bg="#ffffff")

        canvas_window = canvas.create_window(
            (0, 0),
            window=rows_frame,
            anchor="nw",
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_rows(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        rows_frame.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_rows)

        for index, item in enumerate(ITEMS[key]):
            self.create_item_row(
                rows_frame,
                key,
                item,
                index,
            )

    def create_item_row(self, parent, key, item, index):
        variable = tk.BooleanVar(value=False)
        self.variables[key].append(variable)

        row_bg = "#ffffff" if index % 2 == 0 else "#f7f7f7"

        row = tk.Frame(
            parent,
            bg=row_bg,
            height=55,
        )
        row.pack(fill="x")
        row.pack_propagate(False)

        icon = tk.Label(
            row,
            text=item.get("icon", "•"),
            width=4,
            bg=row_bg,
            fg="#222222",
            font=("Segoe UI Symbol", 18),
        )
        icon.pack(side="left", padx=(12, 4))

        name = tk.Label(
            row,
            text=item["name"],
            bg=row_bg,
            fg="#222222",
            anchor="w",
            font=("Segoe UI", 10),
        )
        name.pack(side="left", fill="x", expand=True)

        file_label = tk.Label(
            row,
            text=f"{item['file'].name}  [{item['type'].upper()}]",
            bg=row_bg,
            fg="#888888",
            anchor="e",
            font=("Segoe UI", 8),
        )
        file_label.pack(side="right", padx=(5, 15))

        checkbutton = tk.Checkbutton(
            row,
            variable=variable,
            bg=row_bg,
            activebackground=row_bg,
            selectcolor="white",
            cursor="hand2",
        )
        checkbutton.pack(side="right", padx=10)

        self.checkbuttons[key].append(checkbutton)

        # Возможность выбрать строку кликом по названию или иконке.
        name.bind(
            "<Button-1>",
            lambda event, var=variable: var.set(not var.get()),
        )
        icon.bind(
            "<Button-1>",
            lambda event, var=variable: var.set(not var.get()),
        )

    def check_all(self, key):
        for variable in self.variables[key]:
            variable.set(True)

    def uncheck_all(self, key):
        for variable in self.variables[key]:
            variable.set(False)

    def get_selected_items(self):
        selected = []

        for key, items in ITEMS.items():
            for index, item in enumerate(items):
                if self.variables[key][index].get():
                    selected.append(item)

        return selected

    def apply_selected(self):
        selected = self.get_selected_items()

        if not selected:
            messagebox.showinfo(
                "UDO",
                "Не выбрано ни одной программы, драйвера или оптимизации.",
            )
            return

        if not sys.platform.startswith("win"):
            messagebox.showerror(
                "Ошибка",
                "Эта программа предназначена только для Windows.",
            )
            return

        confirmation = messagebox.askyesno(
            "Подтверждение",
            f"Выбрано элементов: {len(selected)}.\n\n"
            "Некоторые операции требуют прав администратора.\n"
            "Продолжить?",
        )

        if not confirmation:
            return

        if not is_windows_admin():
            messagebox.showwarning(
                "Требуются права администратора",
                "Перезапустите программу от имени администратора "
                "и повторите операцию.",
            )
            return

        self.apply_button.configure(state="disabled")
        self.status_label.configure(text="Выполнение операций...")

        thread = threading.Thread(
            target=self.install_thread,
            args=(selected,),
            daemon=True,
        )
        thread.start()

    def install_thread(self, selected):
        success_count = 0
        error_count = 0

        for number, item in enumerate(selected, start=1):
            self.log_queue.put(
                (
                    "status",
                    f"Обработка {number}/{len(selected)}: {item['name']}",
                )
            )

            success, result = execute_item(item)

            if success:
                success_count += 1
                self.log_queue.put(("success", result))
            else:
                error_count += 1
                self.log_queue.put(("error", result))

        self.log_queue.put(
            (
                "finished",
                (success_count, error_count),
            )
        )

    def process_log_queue(self):
        try:
            while True:
                message_type, data = self.log_queue.get_nowait()

                if message_type == "status":
                    self.status_label.configure(text=data)

                elif message_type == "success":
                    self.status_label.configure(text=data)

                elif message_type == "error":
                    self.status_label.configure(text="Обнаружена ошибка")
                    messagebox.showerror("Ошибка", data)

                elif message_type == "finished":
                    success_count, error_count = data

                    self.apply_button.configure(state="normal")
                    self.status_label.configure(
                        text=(
                            f"Готово. Успешно: {success_count}; "
                            f"с ошибками: {error_count}"
                        )
                    )

                    messagebox.showinfo(
                        "UDO",
                        f"Операции завершены.\n\n"
                        f"Успешно: {success_count}\n"
                        f"С ошибками: {error_count}",
                    )

        except queue.Empty:
            pass

        self.after(100, self.process_log_queue)


if __name__ == "__main__":
    app = UDOApp()
    app.mainloop()