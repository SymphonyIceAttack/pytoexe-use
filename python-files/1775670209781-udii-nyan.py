import tkinter as tk
from tkinter import scrolledtext
import threading
import speech_recognition as sr
import pyttsx3
import subprocess
import datetime
import webbrowser
import pyautogui
import os

# --- Настройки голоса ---
engine = pyttsx3.init()
engine.setProperty('rate', 180)  # Скорость речи
engine.setProperty('volume', 0.9)

def speak(text):
    """Озвучить текст"""
    engine.say(text)
    engine.runAndWait()

# --- Функции-команды ---
def execute_command(cmd):
    cmd = cmd.lower()
    if "привет" in cmd:
        return "Приветик! Чем могу помочь, сенпай?"
    elif "время" in cmd:
        return f"Сейчас {datetime.datetime.now().strftime('%H:%M')}"
    elif "открой браузер" in cmd:
        webbrowser.open("https://www.google.com")
        return "Открываю браузер~"
    elif "открой блокнот" in cmd:
        subprocess.Popen("notepad.exe")
        return "Блокнот готов!"
    elif "калькулятор" in cmd:
        subprocess.Popen("calc.exe")
        return "Калькулятор на месте!"
    elif "что на рабочем столе" in cmd:
        pyautogui.press('win', 'd')
        return "Свернула все окошки. Красота!"
    elif "заблокируй" in cmd:
        pyautogui.hotkey('win', 'l')
        return "Компьютер заблокирован. Пока!"
    elif "выключи" in cmd and "комп" in cmd:
        speak("Выключаю через 10 секунд. Сохраните всё!")
        os.system("shutdown /s /t 10")
        return "Пока-пока!"
    elif "стоп" in cmd or "выйти" in cmd:
        return "Завершаю работу. До встречи!"
        root.quit()
    else:
        return "Я не знаю такой команды... Попробуй 'время', 'открой браузер' или 'калькулятор'"

# --- Распознавание голоса ---
def listen_mic():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="🎧 Слушаю...")
        root.update()
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="ru-RU")
            status_label.config(text=f"Ты сказал: {text}")
            return text
        except sr.UnknownValueError:
            status_label.config(text="Не поняла, повтори")
            return ""
        except sr.RequestError:
            status_label.config(text="Ошибка сети")
            return ""

def process_voice():
    """Запустить прослушку в отдельном потоке"""
    def task():
        command = listen_mic()
        if command:
            response = execute_command(command)
            chat_area.insert(tk.END, f"Ты: {command}\n", "user")
            chat_area.insert(tk.END, f"✨ Хаяо: {response}\n\n", "bot")
            chat_area.see(tk.END)
            speak(response)
        status_label.config(text="Готова к работе")
    threading.Thread(target=task, daemon=True).start()

def send_text():
    """Отправить текст из поля ввода"""
    command = text_entry.get()
    if command:
        chat_area.insert(tk.END, f"Ты: {command}\n", "user")
        response = execute_command(command)
        chat_area.insert(tk.END, f"✨ Хаяо: {response}\n\n", "bot")
        chat_area.see(tk.END)
        text_entry.delete(0, tk.END)
        speak(response)
        if "выйти" in command.lower():
            root.after(1000, root.quit)

# --- Создание окошка с аниме-девушкой ---
root = tk.Tk()
root.title("Хаяо — твоя компьютерная тяночка")
root.geometry("500x600")
root.configure(bg="#ffe6f0")

# Рамка с аватаркой (текстовая, но можешь вставить картинку)
avatar_frame = tk.Frame(root, bg="#ffb3c6", height=100)
avatar_frame.pack(fill=tk.X, pady=10)
avatar_label = tk.Label(avatar_frame, text="(◕‿◕)✧  ХАЯО  ✧(◕‿◕)", font=("Arial", 16, "bold"), bg="#ffb3c6", fg="#b30047")
avatar_label.pack(pady=15)

# Область чата
chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15, font=("Arial", 10))
chat_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
chat_area.tag_config("user", foreground="#2c3e50", font=("Arial", 10, "bold"))
chat_area.tag_config("bot", foreground="#c0392b", font=("Arial", 10))

# Поле ввода текста
text_entry = tk.Entry(root, width=40, font=("Arial", 12))
text_entry.pack(pady=5, side=tk.LEFT, padx=10)
text_entry.bind("<Return>", lambda event: send_text())

# Кнопки
btn_send = tk.Button(root, text="Отправить (текст)", command=send_text, bg="#ff99bb", fg="white", font=("Arial", 10))
btn_send.pack(pady=5, side=tk.LEFT)

btn_mic = tk.Button(root, text="🎤 Сказать голосом", command=process_voice, bg="#66ccff", fg="white", font=("Arial", 10))
btn_mic.pack(pady=5, side=tk.LEFT, padx=5)

status_label = tk.Label(root, text="Нажми 🎤 или напиши команду", bg="#ffe6f0", fg="#666")
status_label.pack(pady=10)

# Приветствие при старте
chat_area.insert(tk.END, "✨ Хаяо: Привет! Я твоя компьютерная помощница. Говори или пиши!\n\n", "bot")

root.mainloop()