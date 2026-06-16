import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pygame

# инициализация миксера
pygame.mixer.init()


def play_music():
    """Воспроизводит выбранный трек или возобновляет после паузы"""
    global current_track_index
    selection = playlist.curselection()
    if not selection:
        messagebox.showwarning("Нет трека", "Выбери песню из списка!")
        return

    current_track_index = selection[0]
    track = playlist.get(current_track_index)
    track_path = track_list[track]

    # Если музыка уже играет, просто снимаем паузу
    pygame.mixer.music.unpause()
    # если не играет — загружаем и запускаем
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.play()
    update_now_playing_label(track)



def pause_music():
    pygame.mixer.music.pause()

# для кнопки следующий трек
def next_track():
    if playlist.size() == 0:
        return
    next_index = (current_track_index + 1) % playlist.size()
    playlist.selection_clear(0, tk.END)
    playlist.selection_set(next_index)
    pygame.mixer.music.stop()   # Остановить текущий трек
    play_music()                # Теперь загрузит выбранный


def update_now_playing_label(track_name):
    now_playing_label.config(text=track_name)


# регулировка громкости (val от 0 до 100)
def set_volume(val):
    volume = int(val) / 100
    pygame.mixer.music.set_volume(volume)

# добавляет MP3-файлы в плейлист
def add_tracks():
    files = filedialog.askopenfilenames(filetypes=[("MP3 файлы", "*.mp3")])
    for file in files:
        filename = os.path.basename(file)
        if filename not in track_list:
            track_list[filename] = file
            playlist.insert(tk.END, filename)

# удаляет выбранный трек из плейлиста
def remove_track():
    selection = playlist.curselection()
    if not selection:
        return
    track = playlist.get(selection[0])
    playlist.delete(selection[0])
    del track_list[track]

# очищает весь плейлист
def clear_playlist():
    playlist.delete(0, tk.END)
    track_list.clear()
    pygame.mixer.music.stop()


root = tk.Tk()
root.title("Музыкальный плеер 2.0")
root.geometry("750x250")
root.resizable(False, False)

# хранение данных
track_list = {}  # словарь: имя файла -> полный путь
current_track_index = 0

# левая панель: плейлист
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(left_frame, text="Ваш плейлист", font=("Arial", 12, "bold")).pack(anchor="w")

# список треков + скроллбар
scrollbar = tk.Scrollbar(left_frame)
playlist = tk.Listbox(left_frame, yscrollcommand=scrollbar.set, bg="lightyellow", selectmode=tk.SINGLE)
scrollbar.config(command=playlist.yview)
playlist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)



# кнопки управления плейлистом
btn_frame = tk.Frame(left_frame)
btn_frame.pack(fill=tk.X, pady=5)

tk.Button(btn_frame, text="➕ Добавить", command=add_tracks, bg="lightgreen", width=12).pack(pady=2)
tk.Button(btn_frame, text="❌ Удалить", command=remove_track, bg="lightcoral", width=12).pack(pady=2)
tk.Button(btn_frame, text="Очистить всё", command=clear_playlist, bg="orange", width=12).pack(pady=2)

# правая панель - управление воспроизведением
right_frame = tk.Frame(root, bg="lightgray")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

now_playing_label = tk.Label(right_frame, font=("Arial", 10), bg="lightgray")
now_playing_label.pack(pady=10)

# кнопки управления
control_frame = tk.Frame(right_frame, bg="lightgray")
control_frame.pack(pady=10)

tk.Button(control_frame, text="▶ Играть", command=play_music, width=10).pack(side=tk.LEFT, padx=2)
tk.Button(control_frame, text="⏸ Пауза", command=pause_music, width=10).pack(side=tk.LEFT, padx=2)
tk.Button(control_frame, text="⏩ Следующий", command=next_track, width=12).pack(side=tk.LEFT, padx=2)

# ползунок громкости
volume_frame = tk.Frame(right_frame, bg="lightgray")
volume_frame.pack(pady=15)

# скейл громкость
tk.Label(volume_frame, text="🔊 Громкость:", bg="lightgray").pack(side=tk.LEFT, padx=5)
volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=set_volume, length=150)
volume_slider.set(70)
volume_slider.pack(side=tk.LEFT)

# Запуск окна
root.mainloop()