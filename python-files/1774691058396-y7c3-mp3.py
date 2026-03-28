import tkinter as tk
from tkinter import filedialog, messagebox
import vlc
import os
from pathlib import Path

class MP3Player:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Player - wicr")
        self.root.geometry("500x300")
        self.root.configure(bg="#2d2d30")

        # Инициализация VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_file = None

        self.create_widgets()

    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(
            self.root,
            text="MP3 Player",
            font=("Segoe UI", 16, "bold"),
            bg="#2d2d30",
            fg="white"
        )
        title_label.pack(pady=10)

        # Отображение текущего файла
        self.file_label = tk.Label(
            self.root,
            text="Нет файла",
            font=("Segoe UI", 10),
            bg="#2d2d30",
            fg="#cccccc",
            wraplength=400
        )
        self.file_label.pack(pady=5)

        # Кнопки управления
        button_frame = tk.Frame(self.root, bg="#2d2d30")
        button_frame.pack(pady=20)

        style_config = {
            "font": ("Segoe UI", 10),
            "bg": "#007acc",
            "fg": "white",
            "relief": "flat",
            "padx": 15,
            "pady": 8
        }

        self.btn_open = tk.Button(
            button_frame,
            text="Открыть MP3",
            command=self.open_file,
            **style_config
        )
        self.btn_open.grid(row=0, column=0, padx=5)

        self.btn_play = tk.Button(
            button_frame,
            text="Воспроизвести",
            command=self.play,
            state="disabled",
            **style_config
        )
        self.btn_play.grid(row=0, column=1, padx=5)

        self.btn_pause = tk.Button(
            button_frame,
            text="Пауза",
            command=self.pause,
            state="disabled",
            **style_config
        )
        self.btn_pause.grid(row=0, column=2, padx=5)

        self.btn_stop = tk.Button(
            button_frame,
            text="Стоп",
            command=self.stop,
            state="disabled",
            **style_config
        )
        self.btn_stop.grid(row=0, column=3, padx=5)

        # Статус воспроизведения
        self.status_label = tk.Label(
            self.root,
            text="Готов к работе",
            font=("Segoe UI", 9),
            bg="#2d2d30",
            fg="#888888"
        )
        self.status_label.pack(side="bottom", pady=10)

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите MP3 файл",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )

        if file_path:
            self.current_file = file_path
            self.file_label.config(text=Path(file_path).name)
            self.btn_play.config(state="normal")
            self.status_label.config(text="Файл загружен")

    def play(self):
        if self.current_file:
            media = self.instance.media_new(self.current_file)
            self.player.set_media(media)
            self.player.play()
            self.btn_pause.config(state="normal")
            self.btn_stop.config(state="normal")
            self.status_label.config(text="Воспроизведение...")

    def pause(self):
        self.player.pause()
        if self.player.is_playing():
            self.status_label.config(text="Воспроизведение...")
        else:
            self.status_label.config(text="Пауза")

    def stop(self):
        self.player.stop()
        self.btn_pause.config(state="disabled")
        self.btn_stop.config(state="disabled")
        self.status_label.config(text="Остановлено")

def main():
    root = tk.Tk()
    app = MP3Player(root)
    root.mainloop()

if __name__ == "__main__":
    main()
