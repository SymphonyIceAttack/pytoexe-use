#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Screenshot Tool - Professional Video Player with Screenshot Capability
A standalone video player that allows frame-by-frame navigation and lossless screenshots.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import os
import threading
from datetime import datetime


class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Screenshot Tool v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Video state
        self.video_path = None
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25
        self.playback_speed = 1.0
        
        # Screenshot folder
        self.screenshot_folder = None
        
        # Setup UI
        self.setup_ui()
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Open video button
        self.btn_open = ttk.Button(toolbar, text="📂 Открыть видео", command=self.open_video)
        self.btn_open.pack(side=tk.LEFT, padx=2)
        
        # Screenshot folder button
        self.btn_folder = ttk.Button(toolbar, text="📁 Папка для скриншотов", command=self.select_screenshot_folder)
        self.btn_folder.pack(side=tk.LEFT, padx=2)
        
        # Screenshot button
        self.btn_screenshot = ttk.Button(toolbar, text="📸 Скриншот (S)", command=self.take_screenshot, state=tk.DISABLED)
        self.btn_screenshot.pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_var = tk.StringVar(value="Откройте видеофайл для начала работы")
        status_label = ttk.Label(toolbar, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=10)
        
        # Video display area
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for video display
        self.canvas = tk.Canvas(video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas resize
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        # Playback controls
        btn_frame = ttk.Frame(controls_frame)
        btn_frame.pack(fill=tk.X)
        
        # Frame backward button
        self.btn_frame_back = ttk.Button(btn_frame, text="⏮ Кадр ←", command=self.frame_backward, state=tk.DISABLED)
        self.btn_frame_back.pack(side=tk.LEFT, padx=2)
        
        # Play/Pause button
        self.btn_play = ttk.Button(btn_frame, text="▶ Воспроизвести", command=self.toggle_play, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=2)
        
        # Frame forward button
        self.btn_frame_forward = ttk.Button(btn_frame, text="Кадр → ⏭", command=self.frame_forward, state=tk.DISABLED)
        self.btn_frame_forward.pack(side=tk.LEFT, padx=2)
        
        # Stop button
        self.btn_stop = ttk.Button(btn_frame, text="⏹ Стоп", command=self.stop_video, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        
        # Speed control
        speed_frame = ttk.Frame(btn_frame)
        speed_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(speed_frame, text="Скорость:").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="1.0x")
        speed_combo = ttk.Combobox(speed_frame, textvariable=self.speed_var, 
                                    values=["0.25x", "0.5x", "0.75x", "1.0x", "1.5x", "2.0x"],
                                    width=6, state="readonly")
        speed_combo.pack(side=tk.LEFT, padx=5)
        speed_combo.bind("<<ComboboxSelected>>", self.on_speed_change)
        
        # Progress slider frame
        slider_frame = ttk.Frame(controls_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        # Time labels
        self.time_var = tk.StringVar(value="00:00:00 / 00:00:00")
        time_label = ttk.Label(slider_frame, textvariable=self.time_var)
        time_label.pack(side=tk.LEFT, padx=5)
        
        # Progress slider
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_slider = ttk.Scale(slider_frame, from_=0, to=100, 
                                          variable=self.progress_var, 
                                          command=self.on_slider_move)
        self.progress_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Frame info
        self.frame_info_var = tk.StringVar(value="Кадр: 0 / 0")
        frame_label = ttk.Label(slider_frame, textvariable=self.frame_info_var)
        frame_label.pack(side=tk.LEFT, padx=5)
        
        # Jump to frame
        jump_frame = ttk.Frame(controls_frame)
        jump_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(jump_frame, text="Перейти к кадру:").pack(side=tk.LEFT, padx=5)
        self.jump_entry = ttk.Entry(jump_frame, width=10)
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        self.jump_entry.bind("<Return>", self.jump_to_frame)
        
        jump_btn = ttk.Button(jump_frame, text="Перейти", command=self.jump_to_frame)
        jump_btn.pack(side=tk.LEFT, padx=5)
        
        # Help text
        help_text = "Горячие клавиши: Пробел - пауза/воспроизведение | ← → - кадр вперёд/назад | S - скриншот | Home/End - начало/конец"
        help_label = ttk.Label(controls_frame, text=help_text, foreground="gray")
        help_label.pack(fill=tk.X, pady=5)
        
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<Left>", lambda e: self.frame_backward())
        self.root.bind("<Right>", lambda e: self.frame_forward())
        self.root.bind("s", lambda e: self.take_screenshot())
        self.root.bind("S", lambda e: self.take_screenshot())
        self.root.bind("<Home>", lambda e: self.go_to_start())
        self.root.bind("<End>", lambda e: self.go_to_end())
        self.root.bind("<Up>", lambda e: self.skip_frames(25))
        self.root.bind("<Down>", lambda e: self.skip_frames(-25))
        
    def open_video(self):
        """Open a video file"""
        file_path = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpeg *.mpg *.3gp *.ts"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
            
        # Release previous video if any
        if self.cap is not None:
            self.cap.release()
            
        # Open new video
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", f"Не удалось открыть видеофайл:\n{file_path}")
            return
            
        self.video_path = file_path
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        self.current_frame = 0
        self.is_playing = False
        
        # Enable controls
        self.btn_play.config(state=tk.NORMAL, text="▶ Воспроизвести")
        self.btn_frame_back.config(state=tk.NORMAL)
        self.btn_frame_forward.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_screenshot.config(state=tk.NORMAL)
        
        # Update status
        self.status_var.set(f"Загружено: {os.path.basename(file_path)}")
        
        # Display first frame
        self.display_frame(0)
        self.update_progress()
        
    def select_screenshot_folder(self):
        """Select folder for saving screenshots"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения скриншотов")
        if folder:
            self.screenshot_folder = folder
            self.status_var.set(f"Скриншоты будут сохранены в: {folder}")
            
    def toggle_play(self):
        """Toggle play/pause"""
        if self.cap is None:
            return
            
        self.is_playing = not self.is_playing
        
        if self.is_playing:
            self.btn_play.config(text="⏸ Пауза")
            self.play_thread()
        else:
            self.btn_play.config(text="▶ Воспроизвести")
            
    def play_thread(self):
        """Play video in a thread"""
        if not self.is_playing:
            return
            
        if self.current_frame >= self.total_frames - 1:
            self.current_frame = 0
            
        ret, frame = self.cap.read()
        if ret:
            self.current_frame += 1
            self.display_current_frame()
            self.update_progress()
            
            # Schedule next frame
            delay = int(1000 / (self.fps * self.playback_speed))
            self.root.after(delay, self.play_thread)
        else:
            self.is_playing = False
            self.btn_play.config(text="▶ Воспроизвести")
            
    def stop_video(self):
        """Stop video and return to beginning"""
        self.is_playing = False
        self.btn_play.config(text="▶ Воспроизвести")
        self.current_frame = 0
        self.display_frame(0)
        self.update_progress()
        
    def frame_forward(self):
        """Go one frame forward"""
        if self.cap is None:
            return
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.display_frame(self.current_frame)
            self.update_progress()
            
    def frame_backward(self):
        """Go one frame backward"""
        if self.cap is None:
            return
        if self.current_frame > 0:
            self.current_frame -= 1
            self.display_frame(self.current_frame)
            self.update_progress()
            
    def skip_frames(self, count):
        """Skip multiple frames"""
        if self.cap is None:
            return
        new_frame = max(0, min(self.total_frames - 1, self.current_frame + count))
        self.display_frame(new_frame)
        self.update_progress()
        
    def go_to_start(self):
        """Go to video start"""
        if self.cap is None:
            return
        self.is_playing = False
        self.btn_play.config(text="▶ Воспроизвести")
        self.display_frame(0)
        self.update_progress()
        
    def go_to_end(self):
        """Go to video end"""
        if self.cap is None:
            return
        self.is_playing = False
        self.btn_play.config(text="▶ Воспроизвести")
        self.display_frame(self.total_frames - 1)
        self.update_progress()
        
    def display_frame(self, frame_number):
        """Display a specific frame"""
        if self.cap is None:
            return
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        if ret:
            self.current_frame = frame_number
            self.display_image(frame)
            
    def display_current_frame(self):
        """Display current frame from video"""
        if self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            self.display_image(frame)
            
    def display_image(self, frame):
        """Display a frame on the canvas"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
            
        # Calculate aspect ratio
        img_height, img_width = frame_rgb.shape[:2]
        aspect_ratio = img_width / img_height
        
        # Calculate new dimensions
        if canvas_width / canvas_height > aspect_ratio:
            new_height = canvas_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)
            
        # Resize frame
        frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
        
        # Convert to PhotoImage
        img = Image.fromarray(frame_resized)
        self.photo = ImageTk.PhotoImage(image=img)
        
        # Display on canvas
        self.canvas.delete("all")
        x = canvas_width // 2
        y = canvas_height // 2
        self.canvas.create_image(x, y, image=self.photo, anchor=tk.CENTER)
        
        # Store original frame for screenshot
        self.current_frame_original = frame.copy()
        self.current_frame_original_rgb = frame_rgb.copy()
        
    def on_canvas_resize(self, event):
        """Handle canvas resize"""
        if self.cap is not None:
            self.display_frame(self.current_frame)
            
    def update_progress(self):
        """Update progress display"""
        # Update slider
        if self.total_frames > 0:
            progress = (self.current_frame / self.total_frames) * 100
            self.progress_var.set(progress)
            
        # Update time display
        current_time = self.current_frame / self.fps
        total_time = self.total_frames / self.fps
        
        current_str = self.format_time(current_time)
        total_str = self.format_time(total_time)
        self.time_var.set(f"{current_str} / {total_str}")
        
        # Update frame info
        self.frame_info_var.set(f"Кадр: {self.current_frame} / {self.total_frames}")
        
    def format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
    def on_slider_move(self, value):
        """Handle slider movement"""
        if self.cap is None or self.is_playing:
            return
            
        frame_number = int((float(value) / 100) * self.total_frames)
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        if frame_number != self.current_frame:
            self.display_frame(frame_number)
            self.update_progress()
            
    def on_speed_change(self, event):
        """Handle speed change"""
        speed_str = self.speed_var.get()
        self.playback_speed = float(speed_str.replace("x", ""))
        
    def jump_to_frame(self, event=None):
        """Jump to specific frame number"""
        if self.cap is None:
            return
            
        try:
            frame_number = int(self.jump_entry.get())
            frame_number = max(0, min(frame_number, self.total_frames - 1))
            self.is_playing = False
            self.btn_play.config(text="▶ Воспроизвести")
            self.display_frame(frame_number)
            self.update_progress()
        except ValueError:
            messagebox.showwarning("Предупреждение", "Введите корректный номер кадра")
            
    def take_screenshot(self):
        """Take a screenshot of the current frame"""
        if self.cap is None:
            messagebox.showwarning("Предупреждение", "Сначала откройте видеофайл")
            return
            
        if not hasattr(self, 'current_frame_original_rgb'):
            return
            
        # Determine save folder
        save_folder = self.screenshot_folder
        if save_folder is None:
            save_folder = filedialog.askdirectory(title="Выберите папку для сохранения скриншота")
            if not save_folder:
                return
                
        # Generate filename
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_name}_frame{self.current_frame:06d}_{timestamp}.png"
        filepath = os.path.join(save_folder, filename)
        
        # Get original frame dimensions
        original_height, original_width = self.current_frame_original_rgb.shape[:2]
        
        # Save screenshot in original quality (PNG, lossless)
        img = Image.fromarray(self.current_frame_original_rgb)
        img.save(filepath, "PNG", optimize=True)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        file_size_str = self.format_file_size(file_size)
        
        # Show success message
        self.status_var.set(f"Скриншот сохранён: {filename} ({original_width}x{original_height}, {file_size_str})")
        messagebox.showinfo("Скриншот сохранён", 
                          f"Файл: {filename}\n"
                          f"Разрешение: {original_width}x{original_height}\n"
                          f"Размер файла: {file_size_str}\n"
                          f"Путь: {filepath}")
                          
    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            
    def on_closing(self):
        """Handle window closing"""
        self.is_playing = False
        if self.cap is not None:
            self.cap.release()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VideoPlayer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
