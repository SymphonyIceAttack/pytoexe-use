import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import os
import threading
import speech_recognition as sr
import subprocess
import difflib
import keyboard
import pyttsx3
import time

# Инициализация TTS
tts_engine = pyttsx3.init()

def say(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Главное окно и переменные
commands = {}
CONFIG_FILE = 'commands_config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        commands = json.load(f)

def save_commands():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(commands, f, ensure_ascii=False, indent=4)

# Обработчики для кнопок
def add_command():
    command = entry_command.get().lower().strip()
    path_or_url = entry_path.get().strip()
    if command and path_or_url:
        commands[command] = path_or_url
        save_commands()
        listbox_commands.insert(tk.END, command)
        entry_command.delete(0, tk.END)
        entry_path.delete(0, tk.END)
    else:
        messagebox.showwarning("Внимание", "Введите команду и путь или сайт!")

def delete_command():
    """Удаляет выбранную команду из списка и конфигурации"""
    try:
        selected = listbox_commands.curselection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите команду для удаления!")
            return
        command = listbox_commands.get(selected[0])
        if messagebox.askyesno("Подтверждение", f"Удалить команду '{command}'?"):
            listbox_commands.delete(selected[0])
            del commands[command]
            save_commands()
            say(f"Команда {command} удалена")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

def browse_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

def find_closest_word(word, options, cutoff=0.4):
    matches = difflib.get_close_matches(word, options, n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    return None

def open_application_or_site(path_or_url):
    try:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            import webbrowser
            webbrowser.open(path_or_url)
        else:
            if os.name == 'nt':
                os.startfile(path_or_url)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', path_or_url])
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть: {e}")

# Обработка голосовых команд
def recognize_and_launch():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        label_status.config(text="Говорите сейчас...")
        root.update()
        try:
            # Слушаем дольше для записи
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            spoken_text = r.recognize_google(audio, language='ru-RU').lower()
            label_status.config(text=f"Распознано: {spoken_text}")
            print(f"Распознано: {spoken_text}")

            # Обработка специальных фраз
            if "завершить работу" in spoken_text or "выход" in spoken_text:
                say("Выход из программы")
                root.quit()
                return

            if "заблокировать компьютер" in spoken_text or "блокировка" in spoken_text:
                say("Блокировка компьютера")
                if os.name == 'nt':
                    subprocess.call('rundll32.exe user32.dll,LockWorkStation')
                elif os.name == 'posix':
                    subprocess.call('gnome-screensaver-command -l', shell=True)
                return

            if "запиши пожалуйста" in spoken_text or "запиши" in spoken_text:
                listen_and_save()
                return

            # Проверка на время
            if ("сколько времени" in spoken_text or
                "какое сейчас время" in spoken_text or
                "время" == spoken_text):
                now = time.strftime("%H:%M")
                say(f"Сейчас {now}")
                return

            # Проверка на дату
            if ("какое сегодня число" in spoken_text or
                "какая сегодня дата" in spoken_text or
                "какая дата" in spoken_text):
                today_date = time.strftime("%d.%m.%Y")
                say(f"Сегодня {today_date}")
                return

            # Обработка команд из списка
            words = spoken_text.split()
            for spoken_word in words:
                match = find_closest_word(spoken_word, list(commands.keys()), cutoff=0.4)
                if match:
                    say(f"Выполняю команду: {match}")
                    open_application_or_site(commands[match])
                    break

        except sr.UnknownValueError:
            label_status.config(text="Не удалось распознать речь.")
        except sr.RequestError as e:
            label_status.config(text=f"Ошибка сервиса: {e}")

# Для записи длинной фразы или разговора
def listen_and_save():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        say("Говорите, я буду слушать долго.")
        label_status.config(text="Длительное слушание...")
        root.update()
        try:
            audio = r.listen(source, timeout=2, phrase_time_limit=15)
            text = r.recognize_google(audio, language='ru-RU')
            # Предлагаем сохранить
            save = messagebox.askyesno("Сохранить", f"Сохранить запись?\n\n{text}")
            if save:
                filename = simpledialog.askstring("Имя файла", "Введите имя файла")
                if filename:
                    with open(f"{filename}.txt", "w", encoding='utf-8') as f:
                        f.write(text)
                    say("Запись сохранена.")
        except sr.UnknownValueError:
            say("Не удалось распознать речь.")
        except sr.RequestError as e:
            say(f"Ошибка сервиса: {e}")

# Основной цикл прослушки
def background_listening():
    while True:
        if keyboard.is_pressed('z') and keyboard.is_pressed('q'):
            recognize_and_launch()
            while keyboard.is_pressed('z') or keyboard.is_pressed('q'):
                time.sleep(0.1)
        else:
            time.sleep(0.1)

def start_listening():
    threading.Thread(target=background_listening, daemon=True).start()

# Создаем GUI
root = tk.Tk()
root.title("Голосовой помощник")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="Команда:").grid(row=0, column=0, sticky='w')
entry_command = tk.Entry(frame, width=30)
entry_command.grid(row=0, column=1, pady=5)

tk.Label(frame, text="Путь/сайт:").grid(row=1, column=0, sticky='w')
entry_path = tk.Entry(frame, width=30)
entry_path.grid(row=1, column=1, pady=5)

btn_browse = tk.Button(frame, text="Обзор...", command=browse_file)
btn_browse.grid(row=1, column=2, padx=5)

btn_add = tk.Button(frame, text="Добавить команду", command=add_command)
btn_add.grid(row=2, column=1, pady=10)

tk.Label(root, text="Текущие команды:").pack()
listbox_commands = tk.Listbox(root, height=8, width=50)
listbox_commands.pack()

# Кнопка удаления команды
btn_delete = tk.Button(root, text="Удалить выбранную команду", command=delete_command)
btn_delete.pack(pady=5)

for cmd in commands:
    listbox_commands.insert(tk.END, cmd)

label_status = tk.Label(root, text="Статус: ожидает")
label_status.pack(pady=5)

btn_start = tk.Button(root, text="Запустить распознавание", command=start_listening)
btn_start.pack(pady=10)

# Инструкция
instr_label = tk.Label(root, text="Активировать голосовой режим: нажмите 'Z' + 'Q'")
instr_label.pack(pady=5)

root.mainloop()
