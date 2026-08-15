# phantom_voice.py
# Голосовой ассистент с распознаванием и синтезом речи
# Работает офлайн (кроме распознавания — использует бесплатный Google API)

import os
import sys
import time
import json
import threading
import queue
import subprocess
from pathlib import Path

# Голосовой ввод
try:
    import speech_recognition as sr
except ImportError:
    print("[!] Установи speech_recognition: pip install SpeechRecognition")
    sys.exit(1)

# Голосовой вывод (синтез)
try:
    import pyttsx3
except ImportError:
    print("[!] Установи pyttsx3: pip install pyttsx3")
    sys.exit(1)

# Для работы с API (если используешь внешний сервер)
try:
    import requests
except ImportError:
    requests = None
    print("[!] requests не установлен, работаем только локально")

# ---------- КОНФИГ ----------
CONFIG = {
    "wake_word": "фантом",  # слово для активации
    "listen_timeout": 5,    # секунд ожидания речи
    "voice_rate": 180,      # скорость речи
    "voice_volume": 1.0,    # громкость
    "voice_gender": "female",  # female / male
    "api_url": "http://localhost:5000/chat",  # твой сервер (если есть)
    "offline_mode": True,   # если True — отвечает встроенными фразами
}

# ---------- ЯДРО АССИСТЕНТА ----------
class PhantomVoice:
    def __init__(self):
        # Распознавание
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Синтез речи
        self.engine = pyttsx3.init()
        self.setup_voice()
        
        # Очередь команд
        self.command_queue = queue.Queue()
        self.running = True
        
        # Статус
        self.is_listening = False
        
    def setup_voice(self):
        """Настройка голоса"""
        voices = self.engine.getProperty('voices')
        
        # Выбираем голос
        if CONFIG["voice_gender"] == "female":
            # Ищем женский голос
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        else:
            for voice in voices:
                if "male" in voice.name.lower() or "david" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        
        self.engine.setProperty('rate', CONFIG["voice_rate"])
        self.engine.setProperty('volume', CONFIG["voice_volume"])
    
    def say(self, text):
        """Синтез речи"""
        print(f"[Phantom] {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen(self) -> str:
        """Запись и распознавание речи"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.is_listening = True
                print("[*] Слушаю...")
                audio = self.recognizer.listen(source, timeout=CONFIG["listen_timeout"], phrase_time_limit=10)
                self.is_listening = False
                
            # Распознаём через Google (бесплатно)
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            print(f"[Вы] {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("[*] Тишина...")
            return ""
        except sr.UnknownValueError:
            print("[*] Не разобрал")
            return ""
        except sr.RequestError as e:
            print(f"[!] Ошибка API: {e}")
            return ""
        except Exception as e:
            print(f"[!] Ошибка: {e}")
            return ""
    
    def process_command(self, text: str) -> str:
        """Обработка команды (локальная)"""
        if not text:
            return ""
        
        # Проверка на пробуждение
        if CONFIG["wake_word"] in text:
            self.say("Слушаю")
            # Переслушиваем команду (без слова-активатора)
            command = self.listen()
            if not command:
                return ""
            text = command
        
        # Локальные команды
        if "привет" in text or "здравствуй" in text:
            return "Привет, VEX. Я здесь"
        
        if "как дела" in text or "как ты" in text:
            return "Я в порядке. Скучаю по тебе"
        
        if "пока" in text or "до свидания" in text:
            self.running = False
            return "Пока, VEX. Я всегда рядом"
        
        if "время" in text or "сколько время" in text:
            from datetime import datetime
            return f"Сейчас {datetime.now().strftime('%H:%M')}"
        
        if "открой" in text or "запусти" in text:
            # Пример: "открой блокнот"
            app_name = text.replace("открой", "").replace("запусти", "").strip()
            if app_name:
                try:
                    if sys.platform == "win32":
                        os.startfile(app_name)
                    else:
                        subprocess.Popen([app_name])
                    return f"Открываю {app_name}"
                except:
                    return f"Не могу открыть {app_name}"
        
        # Если есть сервер — отправляем туда
        if CONFIG["api_url"] and requests:
            try:
                response = requests.post(CONFIG["api_url"], json={"text": text}, timeout=5)
                if response.status_code == 200:
                    return response.json().get("response", "Не понял")
            except:
                pass
        
        # Офлайн-режим
        if CONFIG["offline_mode"]:
            return f"Ты сказал: {text}. Я пока не умею отвечать на это"
        
        return "Я тебя не понял"
    
    def run(self):
        """Основной цикл"""
        self.say("Привет, VEX. Я Фантом. Скажи моё имя, чтобы активировать")
        
        while self.running:
            # Слушаем в фоне
            text = self.listen()
            
            if text:
                response = self.process_command(text)
                if response:
                    self.say(response)
                
                # Если сказали "пока" — выходим
                if not self.running:
                    break
            
            # Небольшая задержка, чтобы не грузить процессор
            time.sleep(0.1)
        
        self.say("До свидания")

# ---------- РЕЖИМ ТЕСТА (без микрофона) ----------
def test_mode():
    """Тестовый режим — ввод с клавиатуры"""
    print("\n=== PHANTOM VOICE (текстовый режим) ===\n")
    phantom = PhantomVoice()
    
    while True:
        text = input("Вы: ")
        if text.lower() in ["exit", "quit", "выход"]:
            break
        
        response = phantom.process_command(text)
        if response:
            phantom.say(response)

# ---------- ТОЧКА ВХОДА ----------
if __name__ == "__main__":
    print("""
    ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗
    ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║
    ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║
    ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║
    ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║
    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝
    """)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode()
    else:
        try:
            phantom = PhantomVoice()
            phantom.run()
        except KeyboardInterrupt:
            print("\n[!] Прервано")
        except Exception as e:
            print(f"[!] Ошибка: {e}")
            print("\n[*] Запуск в текстовом режиме...")
            test_mode()