import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import subprocess
import os
import threading
import re
import sys
import platform

# Скрываем консольное окно (для Windows)
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class ProgressBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=100)
        self.progress.pack(fill='x', padx=20)
        
        self.label = tk.Label(self, text="0%", font=('Arial', 8))
        self.label.pack()
        
    def update(self, value):
        self.progress['value'] = value
        self.label.config(text=f"{int(value)}%")

# Глобальные переменные
current_process = None
current_download_path = ""
current_filename = ""

def clear_url():
    """Очищает поле ввода ссылки"""
    entry.delete(0, tk.END)

def open_download_folder():
    """Открывает папку с загруженными файлами и выделяет скачанный файл"""
    if current_download_path and os.path.exists(current_download_path):
        try:
            if platform.system() == "Windows":
                # На Windows открываем папку и выделяем файл
                if current_filename and os.path.exists(os.path.join(current_download_path, current_filename)):
                    file_path = os.path.join(current_download_path, current_filename)
                    # Команда для открытия папки с выделенным файлом
                    os.system(f'explorer /select,"{os.path.normpath(file_path)}"')
                else:
                    # Если файл не найден, просто открываем папку
                    os.startfile(os.path.normpath(current_download_path))
            elif platform.system() == "Darwin":  # macOS
                if current_filename and os.path.exists(os.path.join(current_download_path, current_filename)):
                    # На Mac открываем папку с выделенным файлом
                    os.system(f'open -R "{os.path.join(current_download_path, current_filename)}"')
                else:
                    os.system(f'open "{current_download_path}"')
            else:  # Linux
                if current_filename and os.path.exists(os.path.join(current_download_path, current_filename)):
                    # На Linux открываем папку содержащую файл
                    os.system(f'xdg-open "{os.path.dirname(os.path.join(current_download_path, current_filename))}"')
                else:
                    os.system(f'xdg-open "{current_download_path}"')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
    else:
        messagebox.showwarning("Внимание", "Папка загрузки не найдена или не выбрана")

def get_quality_code():
    """Возвращает код формата для выбранного качества"""
    quality = quality_var.get()
    quality_map = {
        "Максимальное": "best[ext=mp4]/best",
        "1080p": "best[height<=1080][ext=mp4]/best[height<=1080]",
        "720p": "best[height<=720][ext=mp4]/best[height<=720]",
        "480p": "best[height<=480][ext=mp4]/best[height<=480]",
        "360p": "best[height<=360][ext=mp4]/best[height<=360]"
    }
    return quality_map.get(quality, "best[ext=mp4]/best")

def download_video():
    global current_process, current_download_path, current_filename
    
    url = entry.get().strip()
    if not url:
        messagebox.showerror("Ошибка", "Введите ссылку")
        return
    
    # Выбор папки для сохранения
    download_path = filedialog.askdirectory(title="Выберите папку для сохранения")
    if not download_path:
        return
    
    current_download_path = download_path
    
    # Обновляем отображаемый путь
    path_label.config(text=f"Сохраняется в: {download_path}")
    filename_label.config(text="Файл: подготавливаю файл, ожидание (обычно около минуты)...")
    
    download_btn.config(state="disabled")
    cancel_btn.config(state="normal")
    open_btn.config(state="disabled")
    quality_combo.config(state="disabled")
    status_label.config(text="Начинаем загрузку...")
    progress_bar.update(0)  # Сбрасываем прогресс
    
    def download_thread():
        global current_process, current_filename
        
        try:
            quality_format = get_quality_code()
            
            cmd = [
                'yt-dlp',
                '-f', quality_format,
                '--no-warnings',
                '--no-check-formats',
                '--ignore-errors',
                '--newline',
                '-o', f'{download_path}/%(title)s.%(ext)s',
                url
            ]
            
            # Перенаправляем stderr в null чтобы скрыть все ошибки
            if os.name == 'nt':  # Windows
                current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    universal_newlines=True,
                    bufsize=1,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:  # Linux/Mac
                current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    universal_newlines=True,
                    bufsize=1
                )
            
            # Регулярные выражения для извлечения данных
            progress_pattern = re.compile(r'(\d+\.\d+)%')
            filename_pattern = re.compile(r'Destination:\s+(.+)')
            
            for line in current_process.stdout:
                line = line.strip()
                
                # Извлекаем имя файла
                if 'Destination:' in line:
                    match = filename_pattern.search(line)
                    if match:
                        current_filename = os.path.basename(match.group(1))
                        # Обрезаем длинное имя файла до 50 знаков
                        display_name = current_filename
                        if len(display_name) > 50:
                            display_name = display_name[:47] + "..."
                        root.after(0, lambda f=display_name: filename_label.config(text=f"Файл: {f}"))
                
                # Извлекаем прогресс загрузки
                elif '[download]' in line and '%' in line:
                    match = progress_pattern.search(line)
                    if match:
                        percent = float(match.group(1))
                        root.after(0, lambda p=percent: progress_bar.update(p))
                        root.after(0, lambda l=line: status_label.config(text=l))
                
                # Общая информация
                elif any(x in line for x in ['[info]', 'Writing video']):
                    root.after(0, lambda l=line: status_label.config(text=l))
            
            current_process.wait()
            
            if current_process.returncode == 0:
                root.after(0, lambda: progress_bar.update(100))
                root.after(0, lambda: open_btn.config(state="normal"))
                root.after(0, lambda: clear_url())  # Очищаем ссылку после загрузки
                root.after(0, lambda: messagebox.showinfo("Успех", f"Видео загружено в:\n{download_path}"))
            else:
                root.after(0, lambda: messagebox.showerror("Ошибка", "Ошибка загрузки"))
            
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка: {str(e)}"))
        finally:
            root.after(0, lambda: download_btn.config(state="normal"))
            root.after(0, lambda: cancel_btn.config(state="disabled"))
            root.after(0, lambda: quality_combo.config(state="readonly"))
            root.after(0, lambda: status_label.config(text="Готово"))
            current_process = None
    
    threading.Thread(target=download_thread, daemon=True).start()

def cancel_download():
    global current_process
    if current_process:
        current_process.terminate()
        status_label.config(text="Загрузка отменена")
        download_btn.config(state="normal")
        cancel_btn.config(state="disabled")
        open_btn.config(state="disabled")
        quality_combo.config(state="readonly")
        current_process = None

def paste_from_clipboard(event=None):
    try:
        clipboard_text = root.clipboard_get()
        if 'http' in clipboard_text:
            entry.delete(0, tk.END)
            entry.insert(0, clipboard_text)
    except:
        pass

# Создаем GUI
root = tk.Tk()
root.title("PHV Downloader")
root.geometry("650x245")  # Вернул высоту
root.resizable(False, False)

# Главный фрейм для ввода ссылки и кнопок
main_frame = tk.Frame(root)
main_frame.pack(pady=20, padx=20, fill='x')  # Верхний отступ УВЕЛИЧЕН до 15px

# Фрейм для ссылки и кнопок
input_frame = tk.Frame(main_frame)
input_frame.pack(fill='x')

tk.Label(input_frame, text="Ссылка:").pack(side='left')

# Фрейм для поля ввода и кнопки очистки
entry_frame = tk.Frame(input_frame)
entry_frame.pack(side='left', padx=10, fill='x', expand=True)

entry = tk.Entry(entry_frame, width=35)
entry.pack(side='left', fill='x', expand=True)

# Кнопка очистки (крестик)
clear_btn = tk.Button(entry_frame, text="✕", command=clear_url, 
                     width=2, font=('Arial', 8), bg='#f0f0f0')
clear_btn.pack(side='right', padx=(5, 0))

# Фрейм для кнопок управления
button_frame = tk.Frame(input_frame)
button_frame.pack(side='right')

download_btn = tk.Button(button_frame, text="Download", command=download_video, width=10)
download_btn.pack(side='left', padx=2)

cancel_btn = tk.Button(button_frame, text="Cancel", command=cancel_download, width=10, state="disabled")
cancel_btn.pack(side='left', padx=2)

# Биндим правую кнопку мыши для вставки
entry.bind("<Button-3>", paste_from_clipboard)
entry.bind("<Control-v>", paste_from_clipboard)

# Фрейм для информации о файле и качества
info_frame = tk.Frame(root)
info_frame.pack(fill='x', padx=20, pady=8)

# Метка для отображения имени файла (слева) с фиксированной шириной
filename_label = tk.Label(info_frame, text="Файл: не выбран", 
                         relief='flat', anchor='w', font=('Arial', 9), width=55)
filename_label.pack(side='left')

# Фрейм для выбора качества (справа) с фиксированной позицией
quality_frame = tk.Frame(info_frame)
quality_frame.pack(side='right')

tk.Label(quality_frame, text="Качество:", font=('Arial', 9)).pack(side='left')
quality_var = tk.StringVar(value="720p")
quality_combo = ttk.Combobox(quality_frame, 
                            textvariable=quality_var,
                            values=["Максимальное", "1080p", "720p", "480p", "360p"],
                            state="readonly",
                            width=12)
quality_combo.pack(side='left', padx=(5, 0))

# Кастомный прогресс-бар с процентами
progress_bar = ProgressBar(root)
progress_bar.pack(fill='x', pady=8)

# Статус
status_label = tk.Label(root, text="Введите ссылку и нажмите Download", 
                       relief='sunken', anchor='w')
status_label.pack(fill='x', padx=20, pady=5)

# Нижний фрейм для пути и кнопки открытия
bottom_frame = tk.Frame(root)
bottom_frame.pack(fill='x', padx=20, pady=5)  # Нижний отступ УМЕНЬШЕН до 5px

# Инфо о сохранении
path_label = tk.Label(bottom_frame, text="Сохраняется в: не выбрана", 
                     relief='flat', anchor='w', font=('Arial', 9))
path_label.pack(side='left', fill='x', expand=True)

# Кнопка "Открыть" в правом нижнем углу
open_btn = tk.Button(bottom_frame, text="Открыть", command=open_download_folder, 
                    width=8, state="disabled")
open_btn.pack(side='right')

# Запускаем приложение
if __name__ == "__main__":
    root.mainloop()
