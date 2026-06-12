import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import cv2
import moviepy.editor as mp
from moviepy.editor import VideoFileClip, vfx
import threading
from datetime import timedelta

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Видео процессор")
        self.root.geometry("800x600")
        
        self.video_files = []
        
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
        file_paths = filedialog.askopenfilenames(
            title="Выберите видео файлы",
            filetypes=[("MP4 файлы", "*.mp4"), ("Все файлы", "*.*")]
        )
        
        for file_path in file_paths:
            if file_path not in self.video_files:
                self.video_files.append(file_path)
                self.update_video_list()
    
    def add_folder(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с видео")
        
        if folder_path:
            for file in os.listdir(folder_path):
                if file.lower().endswith('.mp4'):
                    file_path = os.path.join(folder_path, file)
                    if file_path not in self.video_files:
                        self.video_files.append(file_path)
            
            self.update_video_list()
    
    def update_video_list(self):
        self.listbox.delete(0, tk.END)
        
        for file_path in self.video_files:
            try:
                cap = cv2.VideoCapture(file_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = frame_count / fps
                
                cap.release()
                
                file_name = os.path.basename(file_path)
                resolution = f"{width}x{height}"
                duration_str = str(timedelta(seconds=int(duration)))
                
                list_item = f"{file_name} | {resolution} | {duration_str}"
                self.listbox.insert(tk.END, list_item)
                
            except Exception as e:
                file_name = os.path.basename(file_path)
                list_item = f"{file_name} | Ошибка | Ошибка"
                self.listbox.insert(tk.END, list_item)
    
    def process_video(self, input_path, output_path, progress_callback):
        try:
            progress_callback(10)
            
            video = VideoFileClip(input_path)
            
            progress_callback(30)
            
            reversed_video = video.fx(vfx.time_mirror)
            
            progress_callback(60)
            
            final_video = mp.concatenate_videoclips([video, reversed_video])
            
            progress_callback(80)
            
            final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
            
            progress_callback(100)
            
            video.close()
            reversed_video.close()
            final_video.close()
            
            return True
        except Exception as e:
            print(f"Ошибка при обработке: {e}")
            return False
    
    def process_all_videos(self, output_folder):
        total_videos = len(self.video_files)
        
        for idx, video_path in enumerate(self.video_files, 1):
            self.root.after(0, self.status_label.config, {'text': f"Обработка видео {idx} из {total_videos}: {os.path.basename(video_path)}"})
            
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_filename = f"{base_name}_reversed_merged.mp4"
            output_path = os.path.join(output_folder, output_filename)
            
            def update_progress(value):
                overall_progress = ((idx - 1) * 100 + value) / total_videos
                self.root.after(0, self.progress_var.set, overall_progress)
            
            success = self.process_video(video_path, output_path, update_progress)
            
            if not success:
                self.root.after(0, messagebox.showerror, "Ошибка", f"Не удалось обработать видео: {os.path.basename(video_path)}")
        
        self.root.after(0, self.status_label.config, {'text': "Готов"})
        self.root.after(0, messagebox.showinfo, "Готово", "Обработка видео завершена")
        self.root.after(0, self.progress_var.set, 0)
    
    def save_video(self):
        if not self.video_files:
            messagebox.showwarning("Предупреждение", "Нет добавленных видео файлов")
            return
        
        output_folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        
        if output_folder:
            self.status_label.config(text="Начало обработки...")
            self.progress_var.set(0)
            
            thread = threading.Thread(target=self.process_all_videos, args=(output_folder,))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()