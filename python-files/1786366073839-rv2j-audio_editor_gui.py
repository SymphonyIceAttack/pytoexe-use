# Сохраните как audio_editor_gui.py
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pydub import AudioSegment
import threading

class AudioEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Аудио Редактор")
        self.root.geometry("800x600")
        
        # Переменные
        self.current_file = tk.StringVar()
        self.output_file = tk.StringVar()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Создаем вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка "Основное"
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Основные операции")
        self.setup_main_tab(main_frame)
        
        # Вкладка "Эффекты"
        effects_frame = ttk.Frame(notebook)
        notebook.add(effects_frame, text="Эффекты")
        self.setup_effects_tab(effects_frame)
        
        # Вкладка "Склеивание"
        merge_frame = ttk.Frame(notebook)
        notebook.add(merge_frame, text="Склеивание")
        self.setup_merge_tab(merge_frame)
        
        # Вкладка "Информация"
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Информация")
        self.setup_info_tab(info_frame)
        
        # Статус бар
        self.status_bar = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_main_tab(self, parent):
        # Выбор файла
        file_frame = ttk.LabelFrame(parent, text="Выбор файла", padding=10)
        file_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Entry(file_frame, textvariable=self.current_file, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Обзор", command=self.browse_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Воспроизвести", command=self.play_audio).pack(side=tk.LEFT, padx=5)
        
        # Обрезка
        cut_frame = ttk.LabelFrame(parent, text="Обрезка аудио", padding=10)
        cut_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(cut_frame, text="Начало (мм:сс):").grid(row=0, column=0, padx=5, pady=5)
        self.start_time = ttk.Entry(cut_frame, width=10)
        self.start_time.grid(row=0, column=1, padx=5, pady=5)
        self.start_time.insert(0, "0:00")
        
        ttk.Label(cut_frame, text="Конец (мм:сс):").grid(row=0, column=2, padx=5, pady=5)
        self.end_time = ttk.Entry(cut_frame, width=10)
        self.end_time.grid(row=0, column=3, padx=5, pady=5)
        self.end_time.insert(0, "1:00")
        
        ttk.Button(cut_frame, text="Обрезать и сохранить", command=self.cut_audio).grid(row=0, column=4, padx=20, pady=5)
        
        # Извлечение фрагмента
        extract_frame = ttk.LabelFrame(parent, text="Извлечь фрагмент", padding=10)
        extract_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(extract_frame, text="Начало (мм:сс):").grid(row=0, column=0, padx=5, pady=5)
        self.extract_start = ttk.Entry(extract_frame, width=10)
        self.extract_start.grid(row=0, column=1, padx=5, pady=5)
        self.extract_start.insert(0, "0:00")
        
        ttk.Label(extract_frame, text="Длительность (сек):").grid(row=0, column=2, padx=5, pady=5)
        self.extract_duration = ttk.Entry(extract_frame, width=10)
        self.extract_duration.grid(row=0, column=3, padx=5, pady=5)
        self.extract_duration.insert(0, "30")
        
        ttk.Button(extract_frame, text="Извлечь и сохранить", command=self.extract_segment).grid(row=0, column=4, padx=20, pady=5)
        
        # Громкость
        volume_frame = ttk.LabelFrame(parent, text="Изменить громкость", padding=10)
        volume_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(volume_frame, text="Изменение (дБ):").grid(row=0, column=0, padx=5, pady=5)
        self.volume_change = ttk.Entry(volume_frame, width=10)
        self.volume_change.grid(row=0, column=1, padx=5, pady=5)
        self.volume_change.insert(0, "5")
        
        ttk.Button(volume_frame, text="Применить и сохранить", command=self.change_volume).grid(row=0, column=2, padx=20, pady=5)
    
    def setup_effects_tab(self, parent):
        # Скорость
        speed_frame = ttk.LabelFrame(parent, text="Изменение скорости", padding=10)
        speed_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(speed_frame, text="Скорость (1.0 = норм):").grid(row=0, column=0, padx=5, pady=5)
        self.speed_factor = ttk.Entry(speed_frame, width=10)
        self.speed_factor.grid(row=0, column=1, padx=5, pady=5)
        self.speed_factor.insert(0, "1.5")
        
        ttk.Button(speed_frame, text="Изменить скорость", command=self.change_speed).grid(row=0, column=2, padx=20, pady=5)
        
        # Реверс
        reverse_frame = ttk.LabelFrame(parent, text="Реверс аудио", padding=10)
        reverse_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(reverse_frame, text="Перевернуть аудио", command=self.reverse_audio).pack(padx=20, pady=5)
        
        # Затухание
        fade_frame = ttk.LabelFrame(parent, text="Затухание", padding=10)
        fade_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(fade_frame, text="Затухание в начале (мс):").grid(row=0, column=0, padx=5, pady=5)
        self.fade_in = ttk.Entry(fade_frame, width=10)
        self.fade_in.grid(row=0, column=1, padx=5, pady=5)
        self.fade_in.insert(0, "2000")
        
        ttk.Label(fade_frame, text="Затухание в конце (мс):").grid(row=0, column=2, padx=5, pady=5)
        self.fade_out = ttk.Entry(fade_frame, width=10)
        self.fade_out.grid(row=0, column=3, padx=5, pady=5)
        self.fade_out.insert(0, "2000")
        
        ttk.Button(fade_frame, text="Применить затухание", command=self.fade_audio).grid(row=0, column=4, padx=20, pady=5)
    
    def setup_merge_tab(self, parent):
        # Список файлов для склеивания
        ttk.Label(parent, text="Файлы для склеивания:").pack(padx=10, pady=5)
        
        self.merge_listbox = tk.Listbox(parent, height=10)
        self.merge_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Добавить файлы", command=self.add_merge_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить выбранный", command=self.remove_merge_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить список", command=self.clear_merge_list).pack(side=tk.LEFT, padx=5)
        
        # Опции склеивания
        options_frame = ttk.Frame(parent)
        options_frame.pack(padx=10, pady=5)
        
        ttk.Label(options_frame, text="Перекрестное затухание (мс):").pack(side=tk.LEFT, padx=5)
        self.crossfade = ttk.Entry(options_frame, width=10)
        self.crossfade.pack(side=tk.LEFT, padx=5)
        self.crossfade.insert(0, "0")
        
        ttk.Button(parent, text="Склеить и сохранить", command=self.merge_audio).pack(padx=10, pady=10)
    
    def setup_info_tab(self, parent):
        self.info_text = scrolledtext.ScrolledText(parent, height=20)
        self.info_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(parent, text="Показать информацию о файле", command=self.show_file_info).pack(padx=10, pady=5)
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=[
                ("Аудио файлы", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("Все файлы", "*.*")
            ]
        )
        if filename:
            self.current_file.set(filename)
    
    def browse_output(self, title="Сохранить как", default_ext=".mp3"):
        filename = filedialog.asksaveasfilename(
            title=title,
            defaultextension=default_ext,
            filetypes=[
                ("MP3 файлы", "*.mp3"),
                ("WAV файлы", "*.wav"),
                ("OGG файлы", "*.ogg"),
                ("FLAC файлы", "*.flac")
            ]
        )
        return filename
    
    def play_audio(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        def play_thread():
            try:
                audio = AudioSegment.from_file(self.current_file.get())
                from pydub.playback import play
                self.status_bar.config(text="Воспроизведение...")
                play(audio)
                self.status_bar.config(text="Готов к работе")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось воспроизвести: {str(e)}")
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def cut_audio(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить обрезанный файл")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            start_ms = self.time_to_ms(self.start_time.get())
            end_ms = self.time_to_ms(self.end_time.get())
            
            cut = audio[start_ms:end_ms]
            cut.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def extract_segment(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить фрагмент")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            start_ms = self.time_to_ms(self.extract_start.get())
            duration_ms = int(float(self.extract_duration.get()) * 1000)
            
            segment = audio[start_ms:start_ms + duration_ms]
            segment.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def change_volume(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить с измененной громкостью")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            db_change = float(self.volume_change.get())
            modified = audio + db_change
            modified.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def change_speed(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить с измененной скоростью")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            speed = float(self.speed_factor.get())
            
            modified = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed)
            })
            modified.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def reverse_audio(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить перевернутое аудио")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            reversed_audio = audio.reverse()
            reversed_audio.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def fade_audio(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        output = self.browse_output("Сохранить с затуханием")
        if not output:
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            fade_in_ms = int(self.fade_in.get())
            fade_out_ms = int(self.fade_out.get())
            
            modified = audio
            if fade_in_ms > 0:
                modified = modified.fade_in(fade_in_ms)
            if fade_out_ms > 0:
                modified = modified.fade_out(fade_out_ms)
            
            modified.export(output, format=output.split('.')[-1])
            
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def add_merge_files(self):
        files = filedialog.askopenfilenames(
            title="Выберите файлы для склеивания",
            filetypes=[
                ("Аудио файлы", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("Все файлы", "*.*")
            ]
        )
        for file in files:
            self.merge_listbox.insert(tk.END, file)
    
    def remove_merge_file(self):
        selection = self.merge_listbox.curselection()
        if selection:
            self.merge_listbox.delete(selection[0])
    
    def clear_merge_list(self):
        self.merge_listbox.delete(0, tk.END)
    
    def merge_audio(self):
        files = list(self.merge_listbox.get(0, tk.END))
        if len(files) < 2:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы 2 файла для склеивания!")
            return
        
        output = self.browse_output("Сохранить склеенный файл")
        if not output:
            return
        
        try:
            combined = AudioSegment.empty()
            crossfade_ms = int(self.crossfade.get())
            
            for i, file in enumerate(files):
                self.status_bar.config(text=f"Обработка: {os.path.basename(file)}")
                audio = AudioSegment.from_file(file)
                
                if i == 0:
                    combined = audio
                else:
                    if crossfade_ms > 0:
                        combined = combined.append(audio, crossfade=crossfade_ms)
                    else:
                        combined = combined + audio
            
            combined.export(output, format=output.split('.')[-1])
            
            self.status_bar.config(text="Готов к работе")
            messagebox.showinfo("Успех", f"Файл сохранен: {output}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def show_file_info(self):
        if not self.current_file.get():
            messagebox.showwarning("Предупреждение", "Выберите файл!")
            return
        
        try:
            audio = AudioSegment.from_file(self.current_file.get())
            file_path = self.current_file.get()
            
            info = f"""Информация о файле:
Путь: {file_path}
Размер: {os.path.getsize(file_path) / (1024*1024):.2f} МБ
Длительность: {len(audio) / 1000:.2f} сек
Каналы: {audio.channels}
Частота дискретизации: {audio.frame_rate} Гц
Битрейт: {audio.sample_width * 8} бит
Формат: {file_path.split('.')[-1].upper()}
"""
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def time_to_ms(self, time_str):
        """Конвертация времени в миллисекунды"""
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = map(float, parts)
                return int((minutes * 60 + seconds) * 1000)
            elif len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                return int((hours * 3600 + minutes * 60 + seconds) * 1000)
        else:
            return int(float(time_str) * 1000)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioEditorApp(root)
    root.mainloop()