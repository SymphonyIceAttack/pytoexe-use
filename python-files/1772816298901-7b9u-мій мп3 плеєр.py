import tkinter as tk
from tkinter import filedialog
from ctypes import windll, create_string_buffer

class SimplePlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Python MP3 Player")
        self.root.geometry("300x150")

        # Кнопки керування
        self.btn_open = tk.Button(root, text="Відкрити файл", command=self.open_file)
        self.btn_open.pack(pady=10)

        self.btn_play = tk.Button(root, text="Грати", command=self.play_music, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=20)

        self.btn_stop = tk.Button(root, text="Стоп", command=self.stop_music, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, padx=20)

        self.file_path = None

    def mci_send(self, command):
        # Функція для відправки команд системному медіаплеєру Windows
        windll.winmm.mciSendStringW(command, None, 0, 0)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if self.file_path:
            self.btn_play.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            print(f"Завантажено: {self.file_path}")

    def play_music(self):
        if self.file_path:
            # Закриваємо попередній потік, якщо він був, і відкриваємо новий
            self.mci_send("close mp3_file")
            self.mci_send(f'open "{self.file_path}" type mpegvideo alias mp3_file')
            self.mci_send("play mp3_file")

    def stop_music(self):
        self.mci_send("stop mp3_file")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimplePlayer(root)
    root.mainloop()