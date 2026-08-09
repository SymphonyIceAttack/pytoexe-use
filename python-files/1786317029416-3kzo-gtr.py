import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys
import threading
import json
from pathlib import Path

class PyToExeConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Py to EXE Converter")
        self.root.geometry("650x550")
        self.root.resizable(False, False)
        self.root.configure(bg='#2C3E50')
        
        # Настройки по умолчанию
        self.settings = {
            'output_name': '',
            'onefile': True,
            'windowed': True,
            'icon_path': '',
            'add_data': '',
            'clean_build': True,
            'debug_mode': False
        }
        
        self.py_file_path = tk.StringVar()
        self.output_name = tk.StringVar()
        self.icon_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Готов к работе...")
        
        self.create_widgets()
        self.check_pyinstaller()
    
    def check_pyinstaller(self):
        """Проверка наличия PyInstaller"""
        try:
            subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                         capture_output=True, check=True)
            return True
        except:
            response = messagebox.askyesno(
                "PyInstaller не найден",
                "PyInstaller не установлен. Хотите установить его сейчас?"
            )
            if response:
                self.install_pyinstaller()
            return False
    
    def install_pyinstaller(self):
        """Установка PyInstaller"""
        self.status_text.set("Установка PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                         check=True)
            messagebox.showinfo("Успех", "PyInstaller успешно установлен!")
        except:
            messagebox.showerror("Ошибка", "Не удалось установить PyInstaller")
    
    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg='#2C3E50')
        title_frame.pack(pady=10)
        
        tk.Label(
            title_frame, 
            text="🐍 Py to EXE Converter",
            font=('Segoe UI', 20, 'bold'),
            bg='#2C3E50',
            fg='#ECF0F1'
        ).pack()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#34495E', bd=0)
        main_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        # Выбор файла
        self.create_file_selector(
            main_frame, 
            "Python файл:", 
            self.py_file_path, 
            "Выбрать .py файл",
            [("Python files", "*.py")]
        )
        
        # Имя выходного файла
        tk.Label(
            main_frame,
            text="Имя EXE файла (необязательно):",
            font=('Segoe UI', 10),
            bg='#34495E',
            fg='#ECF0F1'
        ).pack(pady=(10,0))
        
        self.output_name = tk.StringVar()
        tk.Entry(
            main_frame,
            textvariable=self.output_name,
            font=('Segoe UI', 10),
            bg='#2C3E50',
            fg='#ECF0F1',
            insertbackground='white',
            bd=0
        ).pack(padx=20, pady=5, fill='x')
        
        # Выбор иконки
        self.create_file_selector(
            main_frame,
            "Иконка (необязательно):",
            self.icon_path,
            "Выбрать иконку",
            [("Icon files", "*.ico")]
        )
        
        # Настройки
        settings_frame = tk.Frame(main_frame, bg='#34495E')
        settings_frame.pack(pady=15, padx=20, fill='x')
        
        # Чекбоксы
        self.onefile_var = tk.BooleanVar(value=True)
        self.create_checkbox(settings_frame, "Один файл (--onefile)", self.onefile_var)
        
        self.windowed_var = tk.BooleanVar(value=True)
        self.create_checkbox(settings_frame, "Без консоли (--windowed)", self.windowed_var)
        
        self.clean_var = tk.BooleanVar(value=True)
        self.create_checkbox(settings_frame, "Очистить временные файлы", self.clean_var)
        
        self.debug_var = tk.BooleanVar(value=False)
        self.create_checkbox(settings_frame, "Режим отладки", self.debug_var)
        
        # Кнопки
        buttons_frame = tk.Frame(self.root, bg='#2C3E50')
        buttons_frame.pack(pady=10)
        
        # Кнопка конвертации
        self.convert_btn = tk.Button(
            buttons_frame,
            text="🔄 Конвертировать в EXE",
            command=self.start_conversion,
            font=('Segoe UI', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            activebackground='#219A52',
            activeforeground='white',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.convert_btn.pack(side='left', padx=5)
        
        # Кнопка очистки
        tk.Button(
            buttons_frame,
            text="🗑️ Очистить",
            command=self.clear_all,
            font=('Segoe UI', 10),
            bg='#E74C3C',
            fg='white',
            activebackground='#C0392B',
            activeforeground='white',
            bd=0,
            padx=15,
            pady=10,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Статус
        status_frame = tk.Frame(self.root, bg='#2C3E50')
        status_frame.pack(pady=10, fill='x', padx=20)
        
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_text,
            font=('Segoe UI', 9),
            bg='#2C3E50',
            fg='#95A5A6',
            wraplength=600
        )
        self.status_label.pack()
        
        # Прогресс бар
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=5)
    
    def create_file_selector(self, parent, label_text, variable, button_text, filetypes):
        tk.Label(
            parent,
            text=label_text,
            font=('Segoe UI', 10),
            bg='#34495E',
            fg='#ECF0F1'
        ).pack(pady=(10,0))
        
        frame = tk.Frame(parent, bg='#34495E')
        frame.pack(padx=20, pady=5, fill='x')
        
        tk.Entry(
            frame,
            textvariable=variable,
            font=('Segoe UI', 9),
            bg='#2C3E50',
            fg='#ECF0F1',
            insertbackground='white',
            bd=0
        ).pack(side='left', fill='x', expand=True)
        
        tk.Button(
            frame,
            text=button_text,
            command=lambda: self.browse_file(variable, filetypes),
            font=('Segoe UI', 9),
            bg='#3498DB',
            fg='white',
            activebackground='#2980B9',
            activeforeground='white',
            bd=0,
            padx=10,
            cursor='hand2'
        ).pack(side='left', padx=(5,0))
    
    def create_checkbox(self, parent, text, variable):
        tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            font=('Segoe UI', 10),
            bg='#34495E',
            fg='#ECF0F1',
            selectcolor='#2C3E50',
            activebackground='#34495E',
            activeforeground='#ECF0F1',
            cursor='hand2'
        ).pack(anchor='w', pady=2)
    
    def browse_file(self, variable, filetypes):
        if "*.ico" in filetypes[0][1]:
            filename = filedialog.askopenfilename(
                title="Выберите иконку",
                filetypes=filetypes
            )
        else:
            filename = filedialog.askopenfilename(
                title="Выберите Python файл",
                filetypes=filetypes
            )
        if filename:
            variable.set(filename)
    
    def clear_all(self):
        self.py_file_path.set("")
        self.output_name.set("")
        self.icon_path.set("")
        self.status_text.set("Готов к работе...")
        self.progress.stop()
    
    def start_conversion(self):
        if not self.py_file_path.get():
            messagebox.showerror("Ошибка", "Выберите Python файл!")
            return
        
        if not os.path.exists(self.py_file_path.get()):
            messagebox.showerror("Ошибка", "Файл не найден!")
            return
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.convert_to_exe, daemon=True)
        thread.start()
    
    def convert_to_exe(self):
        self.convert_btn.config(state='disabled')
        self.progress.start(10)
        self.status_text.set("Конвертация началась...")
        
        try:
            # Формирование команды
            cmd = [sys.executable, "-m", "PyInstaller"]
            
            # Добавление параметров
            if self.onefile_var.get():
                cmd.append("--onefile")
            
            if self.windowed_var.get():
                cmd.append("--windowed")
            
            if self.clean_var.get():
                cmd.append("--clean")
            
            if self.debug_var.get():
                cmd.append("--debug")
            
            # Имя выходного файла
            if self.output_name.get():
                cmd.extend(["--name", self.output_name.get()])
            else:
                # Использовать имя исходного файла
                name = os.path.splitext(os.path.basename(self.py_file_path.get()))[0]
                cmd.extend(["--name", name])
            
            # Иконка
            if self.icon_path.get():
                cmd.extend(["--icon", self.icon_path.get()])
            
            # Добавление самого файла
            cmd.append(self.py_file_path.get())
            
            self.status_text.set("Запуск PyInstaller...")
            
            # Запуск конвертации
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Чтение вывода в реальном времени
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.status_text.set(f"PyInstaller: {output.strip()}")
                    self.root.update()
            
            # Проверка результата
            if process.returncode == 0:
                self.status_text.set("✅ Конвертация успешно завершена!")
                self.open_output_folder()
            else:
                error_output = process.stderr.read()
                self.status_text.set(f"❌ Ошибка конвертации")
                messagebox.showerror("Ошибка", f"Ошибка при конвертации:\n{error_output}")
        
        except Exception as e:
            self.status_text.set(f"❌ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
        
        finally:
            self.convert_btn.config(state='normal')
            self.progress.stop()
    
    def open_output_folder(self):
        # Получаем путь к выходной папке
        current_dir = os.path.dirname(os.path.abspath(self.py_file_path.get()))
        dist_path = os.path.join(current_dir, "dist")
        
        if os.path.exists(dist_path):
            if messagebox.askyesno("Успешно", f"EXE файл создан в папке:\n{dist_path}\n\nОткрыть папку?"):
                os.startfile(dist_path)
        else:
            # Ищем dist в текущей директории
            if os.path.exists("dist"):
                if messagebox.askyesno("Успешно", "EXE файл создан в папке dist\n\nОткрыть папку?"):
                    os.startfile("dist")

def main():
    root = tk.Tk()
    app = PyToExeConverter(root)
    
    # Обработка перетаскивания файлов
    def on_drop(event):
        if event.data.endswith('.py'):
            app.py_file_path.set(event.data)
    
    try:
        root.drop_target_register('*')
        root.dnd_bind('<<Drop>>', on_drop)
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()
