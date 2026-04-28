import json
import os
import webbrowser
import difflib
import sys
import time
from pathlib import Path

# Попытка импорта голосовых библиотек
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("Библиотеки speech_recognition и pyttsx3 не установлены. Голосовой режим отключён.")
    print("Установите: pip install SpeechRecognition pyttsx3 pyaudio")

# Пути к файлам
BASE_DIR = Path(__file__).parent if "__file__" in dir() else Path.cwd()
CONFIG_FILE = BASE_DIR / "config.json"
KNOWLEDGE_FILE = BASE_DIR / "knowledge.json"

# ------------------ ЗАГРУЗКА КОНФИГА ------------------
DEFAULT_CONFIG = {
    "user_name": "",
    "speech_rate": 180,     # скорость речи (слов в минуту)
    "voice_index": 0,       # 0 - женский (обычно), 1 - мужской
    "match_threshold": 0.55, # порог нечёткого совпадения (чем ниже, тем больше допускает ошибок)
    "admin_password": "12345", # простой пароль для команды администрирования
    "voice_enabled": True,   # использовать ли голос
    "first_run": True
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # дополняем отсутствующие ключи
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            return config
    else:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

config = load_config()
user_name = config["user_name"]

# ------------------ ЗАГРУЗКА БАЗЫ ЗНАНИЙ ------------------
DEFAULT_KNOWLEDGE = {
    "привет": {"type": "answer", "value": "Привет, {name}! Как дела?"},
    "как дела": {"type": "answer", "value": "У меня всё отлично, {name}!"},
    "что ты умеешь": {"type": "answer", "value": "Я могу открывать сайты, программы, обучаться новому и менять настройки. Скажи 'помощь'."},
    "открой калькулятор": {"type": "open", "value": "calc"},
    "открой блокнот": {"type": "open", "value": "notepad"},
    "открой ютуб": {"type": "open_url", "value": "https://youtube.com"},
    "открой гугл": {"type": "open_url", "value": "https://google.com"},
    "пока": {"type": "exit", "value": "До свидания, {name}!"},
    "помощь": {"type": "answer", "value": "Вы можете просить меня открыть сайт или программу. Например: открой сайт википедия. Я учусь на лету, просто скажите команду и научите меня."}
}

def load_knowledge():
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return DEFAULT_KNOWLEDGE.copy()

def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

knowledge = load_knowledge()

# ------------------ ГОЛОСОВЫЕ ФУНКЦИИ ------------------
engine = None
if VOICE_AVAILABLE:
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', config["speech_rate"])
        voices = engine.getProperty('voices')
        if len(voices) > config["voice_index"]:
            engine.setProperty('voice', voices[config["voice_index"]].id)
    except Exception as e:
        print(f"Ошибка инициализации движка речи: {e}")
        engine = None

def speak(text):
    """Произнести текст голосом, если доступен движок"""
    global engine
    if engine and config.get("voice_enabled", True):
        try:
            print(f"AI (голос): {text}")
            engine.say(text)
            engine.runAndWait()
        except:
            print(f"AI (текст): {text}")
    else:
        print(f"AI: {text}")

def listen():
    """Прослушать микрофон и вернуть распознанный текст"""
    if not VOICE_AVAILABLE or not config.get("voice_enabled", True):
        return input("Ты (текст): ").strip().lower()

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Слушаю...")
        try:
            # регулировка шума
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("Распознаю...")
            # используем Google Web Speech (нужен интернет)
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(f"Вы сказали: {text}")
            return text.lower().strip()
        except sr.WaitTimeoutError:
            speak("Я вас не услышал. Повторите.")
            return ""
        except sr.UnknownValueError:
            speak("Не понял, повторите.")
            return ""
        except sr.RequestError:
            speak("Проблемы с интернетом. Перехожу в текстовый режим.")
            config["voice_enabled"] = False
            save_config(config)
            return input("Ты (текст): ").strip().lower()
        except OSError:
            speak("Микрофон не найден. Перехожу в текстовый режим.")
            config["voice_enabled"] = False
            save_config(config)
            return input("Ты (текст): ").strip().lower()

# ------------------ ОСНОВНАЯ ЛОГИКА ------------------
def find_command(user_text):
    """Нечёткий поиск похожей команды в базе знаний"""
    best_key = None
    best_score = 0
    for key in knowledge.keys():
        score = difflib.SequenceMatcher(None, user_text, key).ratio()
        if score > best_score:
            best_score = score
            best_key = key
    threshold = config.get("match_threshold", 0.55)
    if best_score >= threshold:
        return best_key, best_score
    return None, best_score

def execute_command(cmd_key):
    """Выполнить действие по ключу команды"""
    global user_name, config, knowledge
    cmd = knowledge[cmd_key]
    action_type = cmd["type"]
    value = cmd["value"]

    # Подстановка имени
    if isinstance(value, str):
        value = value.replace("{name}", user_name or "друг")

    if action_type == "answer":
        speak(value)
    elif action_type == "open":
        speak(f"Открываю {value}")
        os.system(value)
    elif action_type == "open_url":
        speak(f"Открываю {value}")
        webbrowser.open(value)
    elif action_type == "exit":
        speak(value)
        return True  # сигнал завершения
    elif action_type == "change_setting":
        # Административная команда: value содержит имя настройки
        speak(f"Настройка {value} изменена.")
        # Реализовано отдельно
        # Но мы можем сделать универсальную логику, пока оставим заглушку
        pass
    return False

def teach_new_command(user_text):
    """Обучить ассистента новой фразе"""
    global knowledge
    speak("Я пока не знаю такую команду. Научите меня: что мне делать?")
    print("Возможные варианты: 'ответ: ...', 'сайт: ...', 'программа: ...'")
    print("Пример: ответ: Привет, я твой помощник")
    # Используем текстовый ввод для обучения, чтобы избежать ошибок распознавания
    teach = input("Введите действие: ").strip().lower()
    if not teach:
        return

    if teach.startswith("ответ:"):
        text = teach[len("ответ:"):].strip()
        knowledge[user_text] = {"type": "answer", "value": text}
    elif teach.startswith("сайт:") or teach.startswith("открой сайт:"):
        # Поддержка "сайт: адрес"
        if "сайт:" in teach:
            url = teach.split("сайт:", 1)[1].strip()
        else:
            url = teach.split("открой сайт:", 1)[1].strip()
        if not url.startswith("http"):
            url = "https://" + url
        knowledge[user_text] = {"type": "open_url", "value": url}
    elif teach.startswith("программа:") or teach.startswith("открой программу:"):
        if "программа:" in teach:
            prog = teach.split("программа:", 1)[1].strip()
        else:
            prog = teach.split("открой программу:", 1)[1].strip()
        knowledge[user_text] = {"type": "open", "value": prog}
    else:
        # Если не указан префикс, считаем ответом
        knowledge[user_text] = {"type": "answer", "value": teach}

    save_knowledge(knowledge)
    speak("Спасибо, я запомнил эту команду!")

def process_admin_command(user_text):
    """Обработка административных команд (например, сменить имя, порог)"""
    global config, user_name, engine
    if "сменить имя" in user_text:
        parts = user_text.split("сменить имя", 1)
        if len(parts) > 1 and parts[1].strip():
            new_name = parts[1].strip()
            user_name = new_name
            config["user_name"] = new_name
            save_config(config)
            speak(f"Теперь я буду называть вас {new_name}")
            return True
        else:
            speak("Скажите новое имя после фразы 'сменить имя'.")
            return True

    if "изменить голос" in user_text or "поменять голос" in user_text:
        if engine:
            voices = engine.getProperty('voices')
            current = config.get("voice_index", 0)
            new_index = (current + 1) % len(voices)
            engine.setProperty('voice', voices[new_index].id)
            config["voice_index"] = new_index
            save_config(config)
            speak("Голос изменён.")
        return True

    if "скорость речи" in user_text:
        # Установка скорости: скажи "скорость речи 150"
        try:
            words = user_text.split()
            for w in words:
                if w.isdigit():
                    rate = int(w)
                    if 50 <= rate <= 300:
                        config["speech_rate"] = rate
                        if engine:
                            engine.setProperty('rate', rate)
                        save_config(config)
                        speak(f"Скорость речи установлена на {rate}")
                        return True
            speak("Не удалось понять число. Скажите, например, 'скорость речи 200'.")
        except:
            pass
        return True

    if "порог совпадения" in user_text or "чувствительность" in user_text:
        try:
            for w in user_text.split():
                # ищем число с плавающей точкой
                if '.' in w or w.isdigit():
                    val = float(w)
                    if 0.3 <= val <= 0.95:
                        config["match_threshold"] = val
                        save_config(config)
                        speak(f"Порог совпадения установлен на {val}")
                        return True
            speak("Скажите число от 0.3 до 0.95, например 'порог совпадения 0.7'.")
        except:
            pass
        return True

    return False

# ------------------ ПЕРВЫЙ ЗАПУСК ------------------
if not user_name:
    print("Привет! Я твой новый ассистент. Как тебя зовут?")
    if config.get("voice_enabled") and VOICE_AVAILABLE:
        speak("Привет! Я твой новый ассистент. Как тебя зовут?")
        name = listen()
        if not name:
            name = input("Имя (текст): ").strip()
    else:
        name = input("Имя: ").strip()
    if name:
        user_name = name
        config["user_name"] = name
        config["first_run"] = False
        save_config(config)
        speak(f"Приятно познакомиться, {user_name}!")
    else:
        user_name = "друг"
        config["user_name"] = user_name
        save_config(config)

# ------------------ ГЛАВНЫЙ ЦИКЛ ------------------
print("\n==== Голосовой ассистент готов ====")
speak(f"Я слушаю вас, {user_name}")

while True:
    user_input = listen()
    if not user_input:
        continue

    # Проверка команды выхода
    if user_input in ["пока", "выход", "стоп"]:
        cmd_key, _ = find_command("пока")
        if cmd_key:
            if execute_command(cmd_key):
                break
        else:
            speak("До свидания!")
            break

    # Проверка административных команд (всегда доступны, без пароля для простоты)
    if process_admin_command(user_input):
        continue

    # Поиск в знаниях
    cmd_key, score = find_command(user_input)
    if cmd_key:
        if execute_command(cmd_key):
            break
    else:
        speak(f"Команда не распознана (похоже на известные на {score:.2f}). Обучите меня.")
        teach_new_command(user_input)

print("Программа завершена.")