import vlc
import tkinter as tk
from tkinter import filedialog, ttk
import os

class MediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Медиаплеер Wicr 1.1")
        self.root.geometry("800x600")
        self.root.configure(bg="#2d2d30")

        # Инициализация VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Флаг для отслеживания состояния обновления
        self.updating = False

        # Основной фрейм
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Область для видео
        self.video_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.play_btn = ttk.Button(control_frame, text="▶ Воспроизвести", command=self.play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = ttk.Button(control_frame, text="⏸️ Пауза", command=self.pause)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="■ Стоп", command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.open_btn = ttk.Button(control_frame, text="📁 Открыть файл", command=self.open_file)
        self.open_btn.pack(side=tk.LEFT, padx=5)

        # Ползунок прогресса
        self.progress = ttk.Scale(main_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.progress.pack(fill=tk.X, pady=5)

        # Метка текущего времени
        self.time_label = ttk.Label(main_frame, text="00:00 / 00:00")
        self.time_label.pack()

        # Запускаем обновление прогресса (раз в 1 секунду)
        self.update_progress()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Все поддерживаемые", "*.mp4 *.avi *.mkv *.mov *.wmv *.mp3 *.wav *.flac"),
                ("Видео", "*.mp4 *.avi *.mkv *.mov *.wmv"),
                ("Аудио", "*.mp3 *.wav *.flac")
            ]
        )
        if file_path:
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            # Сбрасываем прогресс при загрузке нового файла
            self.progress.set(0)
            self.time_label.config(text="00:00 / 00:00")

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def seek(self, value):
        if self.player.is_playing():
            total_length = self.player.get_length()
            if total_length > 0:
                target_time = int((float(value) / 100) * total_length)
                self.player.set_time(target_time)

    def update_progress(self):
        """Обновляет прогресс раз в секунду, только если идёт воспроизведение"""
        if self.player.is_playing():
            total_length = self.player.get_length()
            current_time = self.player.get_time()

            if total_length > 0 and current_time > 0:
                # Обновляем ползунок только если прошло достаточно времени
                progress = (current_time / total_length) * 100
                self.progress.set(progress)

                # Форматирование времени
                def format_time(ms):
                    seconds = ms // 1000
                    minutes = seconds // 60
                    hours = minutes // 60
                    return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"

                self.time_label.config(
                    text=f"{format_time(current_time)} / {format_time(total_length)}"
                )
        # Обновляем раз в 1000 мс (1 секунда) вместо 500 мс
        self.root.after(1000, self.update_progress)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaPlayer(root)
    root.mainloop()
