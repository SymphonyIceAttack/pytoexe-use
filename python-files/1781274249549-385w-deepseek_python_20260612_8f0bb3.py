import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import cv2
import moviepy.editor as mp
from moviepy.video.fx import time_mirror
import threading
from datetime import timedelta

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Видео процессор")
        self.root.geometry("800x600")
        
        self.video_files = []
        self.processing = False  # Флаг для предотвращения множественной обработки
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_video_btn = tk.Button(button_frame, text="Добавить видео", command=self.add_video)
        add_video_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        add_folder_btn = tk.Button(button_frame, text="Добавить папку", command=self.add_folder)
        add_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        remove_btn = tk.Button(button_frame, text="Удалить выбранное", command=self.remove_selected)
        remove_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_btn = tk.Button(button_frame, text="Сохранить", command=self.save_video)
        save_btn.pack(side=tk.LEFT)
        
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(main_frame, text="Готов", anchor=tk.W)
        self.status_label.pack(fill=tk.X)
    
    def add_video(self):
        if self.processing:
            messagebox.showwarning("Предупреждение", "Сначала дождитесь завершения обработки")
            return
            
        file_paths = filedialog.askopenfilenames(
            title="Выберите видео файлы",
            filetypes=[("MP4 файлы", "*.mp4"), ("AVI файлы", "*.avi"), ("MOV файлы", "*.mov"), ("Все файлы", "*.*")]
        )
        
        added = False
        for file_path in file_paths:
            if file_path not in self.video_files:
                self.video_files.append(file_path)
                added = True
        
        if added:
            self.update_video_list()
    
    def add_folder(self):
        if self.processing:
            messagebox.showwarning("Предупреждение", "Сначала дождитесь завершения обработки")
            return
            
        folder_path = filedialog.askdirectory(title="Выберите папку с видео")
        
        if folder_path:
            added = False
            for file in os.listdir(folder_path):
                if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    file_path = os.path.join(folder_path, file)
                    if file_path not in self.video_files:
                        self.video_files.append(file_path)
                        added = True
            
            if added:
                self.update_video_list()
            else:
                messagebox.showinfo("Информация", "В папке не найдено видео файлов")
    
    def remove_selected(self):
        if self.processing:
            messagebox.showwarning("Предупреждение", "Сначала дождитесь завершения обработки")
            return
            
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.video_files):
                del self.video_files[index]
                self.update_video_list()
    
    def update_video_list(self):
        self.listbox.delete(0, tk.END)
        
        for file_path in self.video_files:
            try:
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    raise Exception("Не удалось открыть видео")
                    
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                if fps > 0:
                    duration = frame_count / fps
                    duration_str = str(timedelta(seconds=int(duration)))
                else:
                    duration_str = "Неизвестно"
                
                cap.release()
                
                file_name = os.path.basename(file_path)
                resolution = f"{width}x{height}"
                
                list_item = f"{file_name} | {resolution} | {duration_str}"
                self.listbox.insert(tk.END, list_item)
                
            except Exception as e:
                file_name = os.path.basename(file_path)
                list_item = f"{file_name} | Ошибка: {str(e)[:30]} | Ошибка"
                self.listbox.insert(tk.END, list_item)
    
    def process_video(self, input_path, output_path, progress_callback):
        video = None
        reversed_video = None
        final_video = None
        
        try:
            # Проверяем существование файла
            if not os.path.exists(input_path):
                raise Exception(f"Файл не найден: {input_path}")
            
            progress_callback(10)
            
            # Загружаем видео
            video = mp.VideoFileClip(input_path)
            
            if video is None or video.duration is None:
                raise Exception("Не удалось загрузить видео")
            
            progress_callback(30)
            
            # Создаем обратное видео
            reversed_video = video.fx(time_mirror.time_mirror)
            
            progress_callback(60)
            
            # Объединяем видео
            final_video = mp.concatenate_videoclips([video, reversed_video])
            
            progress_callback(80)
            
            # Сохраняем результат
            final_video.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac', 
                verbose=False, 
                logger=None,
                threads=4  # Используем несколько потоков для ускорения
            )
            
            progress_callback(100)
            return True
            
        except Exception as e:
            print(f"Ошибка при обработке {input_path}: {e}")
            return False
            
        finally:
            # Закрываем все клипы
            if video:
                video.close()
            if reversed_video:
                reversed_video.close()
            if final_video:
                final_video.close()
    
    def process_all_videos(self, output_folder):
        try:
            total_videos = len(self.video_files)
            successful = 0
            
            for idx, video_path in enumerate(self.video_files, 1):
                if not self.processing:
                    break
                    
                def update_status(text):
                    self.root.after(0, lambda: self.status_label.config(text=text))
                
                update_status(f"Обработка видео {idx} из {total_videos}: {os.path.basename(video_path)}")
                
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_filename = f"{base_name}_reversed_merged.mp4"
                output_path = os.path.join(output_folder, output_filename)
                
                # Создаем callback для обновления прогресса
                def make_progress_callback(idx, total_videos):
                    def update_progress(value):
                        if self.processing:
                            overall_progress = ((idx - 1) * 100 + value) / total_videos
                            self.root.after(0, lambda: self.progress_var.set(overall_progress))
                    return update_progress
                
                success = self.process_video(video_path, output_path, make_progress_callback(idx, total_videos))
                
                if success:
                    successful += 1
            
            self.processing = False
            
            self.root.after(0, lambda: self.status_label.config(text="Готов"))
            self.root.after(0, lambda: self.progress_var.set(0))
            
            if successful == total_videos:
                self.root.after(0, lambda: messagebox.showinfo("Готово", f"Успешно обработано {successful} из {total_videos} видео"))
            else:
                self.root.after(0, lambda: messagebox.showwarning("Завершено с ошибками", f"Обработано {successful} из {total_videos} видео"))
                
        except Exception as e:
            self.processing = False
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Ошибка"))
            self.root.after(0, lambda: self.progress_var.set(0))
    
    def save_video(self):
        if self.processing:
            messagebox.showwarning("Предупреждение", "Обработка уже выполняется")
            return
            
        if not self.video_files:
            messagebox.showwarning("Предупреждение", "Нет добавленных видео файлов")
            return
        
        output_folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        
        if output_folder:
            self.processing = True
            self.status_label.config(text="Начало обработки...")
            self.progress_var.set(0)
            
            thread = threading.Thread(target=self.process_all_videos, args=(output_folder,))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()