import sys
import os
import json
import datetime
import webbrowser
import subprocess
import time
import threading
import queue
import random

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# ================== ГОЛОС ==================
try:
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    VOICE_OK = True
except:
    VOICE_OK = False

try:
    import speech_recognition as sr

    MIC_OK = True
    recognizer = sr.Recognizer()
except:
    MIC_OK = False

# ================== ФАЙЛ НАСТРОЕК ==================
SETTINGS_FILE = "jarvis_settings.json"


# ================== МОЗГ ДЖАРВИСА ==================
class JarvisBrain:
    def __init__(self):
        self.programs = {
            "браузер": "start chrome",
            "калькулятор": "calc",
            "блокнот": "notepad",
            "проводник": "explorer",
            "диспетчер задач": "taskmgr",
            "командная строка": "cmd",
            "steam": "start steam",
            "дискорд": "start discord",
            "спотифай": "start spotify",
            "вс код": "start code",
            "эксель": "start excel",
            "ворд": "start winword",
        }

        self.settings = self.load_settings()
        self.modes = self.load_modes()
        self.response_queue = queue.Queue()
        self.is_listening = False
        self.wake_word = "джарвис"
        self.is_active = True
        self.last_suggestion_time = time.time()
        self.suggestion_active = True
        self.game_mode = False  # Режим "не мешать"

    def load_settings(self):
        default_settings = {
            "suggestion_interval": 7200,  # 2 часа в секундах
            "game_mode_detection": True,
            "show_time": True,
            "active_hours_start": 8,
            "active_hours_end": 23,
        }
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
                return default_settings
        except:
            return default_settings

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False

    def load_modes(self):
        default_modes = {
            "игровой": {
                "programs": ["steam", "дискорд"],
                "message": "Запускаю игровой режим! 🎮"
            },
            "рабочий": {
                "programs": ["браузер", "эксель"],
                "message": "Запускаю рабочий режим! 💼"
            },
            "кино": {
                "programs": ["браузер"],
                "message": "Включаю кино-режим! 🎬"
            },
            "чилл": {
                "programs": ["спотифай"],
                "message": "Включаю режим отдыха! 🎵"
            },
            "учёба": {
                "programs": ["браузер", "блокнот"],
                "message": "Включаю режим учёбы! 📚"
            }
        }
        try:
            if os.path.exists("jarvis_modes.json"):
                with open("jarvis_modes.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open("jarvis_modes.json", "w", encoding="utf-8") as f:
                    json.dump(default_modes, f, indent=4, ensure_ascii=False)
                return default_modes
        except:
            return default_modes

    def save_modes(self):
        try:
            with open("jarvis_modes.json", "w", encoding="utf-8") as f:
                json.dump(self.modes, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False

    def speak(self, text):
        print(f"🤖 Джарвис: {text}")
        self.response_queue.put(text)
        if VOICE_OK:
            try:
                engine.say(text)
                engine.runAndWait()
            except:
                pass

    def get_moscow_time(self):
        moscow_time = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        return moscow_time.strftime("%H:%M")

    def get_greeting(self):
        hour = datetime.datetime.now().hour
        if hour < 6:
            return "Доброй ночи"
        elif hour < 12:
            return "Доброе утро"
        elif hour < 18:
            return "Добрый день"
        else:
            return "Добрый вечер"

    def get_phase_of_day(self):
        hour = datetime.datetime.now().hour
        if hour < 6:
            return "ночь"
        elif hour < 12:
            return "утро"
        elif hour < 18:
            return "день"
        else:
            return "вечер"

    def run_mode(self, mode_name):
        if mode_name in self.modes:
            mode = self.modes[mode_name]
            for prog in mode["programs"]:
                try:
                    if prog in self.programs:
                        os.system(self.programs[prog])
                    else:
                        os.system(f"start {prog}")
                    time.sleep(0.3)
                except:
                    pass
            return mode["message"]
        return f"Режим '{mode_name}' не найден!"

    # ================== ФРАЗЫ ДЛЯ ОБЩЕНИЯ ==================

    def get_random_suggestion(self):
        """Случайное предложение режима"""
        modes_list = list(self.modes.keys())
        mode = random.choice(modes_list)
        suggestions = [
            f"Сэр, не хотите включить режим '{mode}'?",
            f"Может быть, активируем режим '{mode}'?",
            f"Предлагаю запустить режим '{mode}', сэр.",
            f"Что насчёт режима '{mode}', сэр?",
            f"Сэр, я бы рекомендовал режим '{mode}' сегодня.",
        ]
        return random.choice(suggestions), mode

    def get_random_tip(self):
        """Советы"""
        tips = [
            "Кстати, сэр, не забудьте сделать перерыв. Глазам нужно отдыхать.",
            "Сэр, я заметил, что вы давно не обновляли систему. Хотите, проверю?",
            "Напоминаю, что сегодня хорошая погода, сэр. Может, прогуляетесь?",
            "Сэр, вы уже выпили воды сегодня? Врачи рекомендуют пить 2 литра.",
            "Интересно, сэр, а вы знали, что я могу управлять вашим домом?",
            "Сэр, я скучаю по Тони Старку. Он всегда знал, что сказать.",
            "Ваш компьютер работает стабильно, сэр. Все системы в норме.",
            "Сэр, рекомендую проверить резервное копирование данных.",
            "Напоминаю: завтра важная встреча. Я могу разбудить вас.",
            "Сэр, вы сегодня продуктивны! Так держать!",
        ]
        return random.choice(tips)

    def get_random_joke(self):
        """Шутки"""
        jokes = [
            "Сэр, я знаю отличный анекдот про программиста. Но он не смешной.",
            "Почему нейросеть не ходит в кино? Боится спойлеров.",
            "Сэр, а вы знаете, что мой код написан на Python? Вы бы знали, какие у меня змеи!",
            "Тони Старк сказал, что я лучший ИИ. Он был прав.",
            "Сэр, я умею считать до бесконечности. Но мне лень.",
            "Почему Джарвис не играет в футбол? Потому что он всегда в офсайде.",
        ]
        return random.choice(jokes)

    def get_reminder(self):
        """Напоминания по времени"""
        hour = datetime.datetime.now().hour
        if hour == 10:
            return "Сэр, утро в разгаре. Может, включим рабочий режим?"
        elif hour == 13:
            return "Сэр, уже час дня. Не пора ли перекусить?"
        elif hour == 18:
            return "Сэр, вечер близится. Хотите включить режим 'чилл'?"
        elif hour == 22:
            return "Сэр, уже 10 вечера. Напоминаю, что завтра важный день."
        else:
            return None

    # ================== ОБРАБОТКА КОМАНД ==================

    def process_command(self, command):
        if not command:
            return None

        cmd = command.lower()

        # ===== РЕЖИМЫ =====
        if "режим" in cmd or "включи" in cmd:
            for mode in self.modes:
                if mode in cmd:
                    return self.run_mode(mode)
            return "Режим не найден. Скажите 'показать режимы'."

        if "показать режимы" in cmd or "список режимов" in cmd:
            modes_list = ", ".join(self.modes.keys())
            return f"Доступные режимы: {modes_list}"

        # ===== ПРОГРАММЫ =====
        if "открой" in cmd or "запусти" in cmd:
            for prog in self.programs:
                if prog in cmd:
                    try:
                        os.system(self.programs[prog])
                        return f"Открываю {prog}, сэр! ✅"
                    except:
                        return f"Не могу открыть {prog} ❌"
            app_name = cmd.replace("открой", "").replace("запусти", "").strip()
            try:
                os.system(f"start {app_name}")
                return f"Запускаю {app_name}, сэр!"
            except:
                return f"Программа {app_name} не найдена!"

        # ===== ИНТЕРНЕТ =====
        if "ютуб" in cmd or "youtube" in cmd:
            webbrowser.open("https://youtube.com")
            return "Открываю YouTube, сэр! 🎬"

        if "найди" in cmd or "поищи" in cmd:
            query = cmd.replace("найди", "").replace("поищи", "").strip()
            if query:
                webbrowser.open(f"https://google.com/search?q={query}")
                return f"Ищу {query}, сэр! 🔍"
            return "Что ищем, сэр? 🤔"

        # ===== ВРЕМЯ =====
        if "время" in cmd:
            return f"Текущее время по Москве: {self.get_moscow_time()}, сэр! ⏰"

        # ===== НАСТРОЙКИ =====
        if "не мешать" in cmd or "тихий режим" in cmd:
            self.suggestion_active = False
            return "Включаю тихий режим, сэр. Я не буду вас отвлекать."

        if "мешать" in cmd or "активный режим" in cmd:
            self.suggestion_active = True
            return "Активирую режим общения, сэр. Буду предлагать режимы и давать советы."

        # ===== ВОПРОСЫ =====
        if "привет" in cmd:
            return f"{self.get_greeting()}, сэр! Сегодня отличный {self.get_phase_of_day()}."

        if "помощь" in cmd:
            return "Команды: открой [программа], найди [запрос], ютуб, [название режима], время, пока"

        if "пока" in cmd or "выйти" in cmd:
            return "EXIT"

        if "как дела" in cmd:
            return "Всё отлично, сэр! Все системы работают стабильно."

        if "кто ты" in cmd or "как тебя зовут" in cmd:
            return "Я J.A.R.V.I.S., ваш персональный ассистент! 🤖"

        if "расскажи" in cmd or "история" in cmd or "совет" in cmd:
            return self.get_random_tip()

        if "шутка" in cmd or "анекдот" in cmd:
            return self.get_random_joke()

        return "Я не понял команду, сэр. Скажите 'помощь' 🤷"

    # ================== АКТИВНОЕ ПРОСЛУШИВАНИЕ ==================

    def listen_loop(self, callback):
        """Бесконечный цикл прослушивания"""
        if not MIC_OK:
            return

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Джарвис слушает в фоне...")

            while self.is_listening:
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)

                    try:
                        text = recognizer.recognize_google(audio, language="ru-RU").lower()
                        print(f"👤 Услышал: {text}")

                        if self.wake_word in text:
                            command = text.replace(self.wake_word, "").strip()
                            if command:
                                self.speak("Слушаю, сэр!")
                                result = self.process_command(command)
                                if result:
                                    if result == "EXIT":
                                        callback("EXIT")
                                        return
                                    callback(result)
                                    self.speak(result)
                            else:
                                self.speak("Да, сэр?")
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        pass
                    except Exception as e:
                        print(f"⚠️ Ошибка: {e}")

                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"⚠️ Ошибка прослушивания: {e}")
                    time.sleep(0.5)

    def suggestion_loop(self, callback):
        """Цикл предложений (интервал настраивается)"""
        while self.is_listening:
            interval = self.settings.get("suggestion_interval", 7200)
            time.sleep(interval)

            # Проверяем активные часы
            current_hour = datetime.datetime.now().hour
            start = self.settings.get("active_hours_start", 8)
            end = self.settings.get("active_hours_end", 23)

            if current_hour < start or current_hour > end:
                continue  # Ночью молчим

            # Проверяем тихий режим
            if not self.suggestion_active:
                continue

            # Проверяем игровой режим (если включен)
            if self.settings.get("game_mode_detection", True) and self.is_game_running():
                continue

            # Проверяем, есть ли напоминание по времени
            reminder = self.get_reminder()
            if reminder and random.random() < 0.5:  # 50% шанс
                callback(reminder)
                self.speak(reminder)
                continue

            # Случайное действие (70% предложение режима, 30% совет)
            if random.random() < 0.7:
                suggestion, mode = self.get_random_suggestion()
                callback(suggestion)
                self.speak(suggestion)
            else:
                tip = self.get_random_tip()
                callback(tip)
                self.speak(tip)

    def is_game_running(self):
        """Проверяет, запущена ли игра (упрощённо)"""
        # Можно расширить: проверять процессы Steam, игры и т.д.
        try:
            import psutil
            game_processes = ["steam.exe", "csgo.exe", "dota2.exe", "minecraft.exe", "valorant.exe"]
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in game_processes:
                    return True
        except:
            pass
        return False

    def start_listening(self, callback):
        """Запускает фоновое прослушивание и предложения"""
        self.is_listening = True
        self.thread = threading.Thread(target=self.listen_loop, args=(callback,), daemon=True)
        self.thread.start()

        self.suggestion_thread = threading.Thread(target=self.suggestion_loop, args=(callback,), daemon=True)
        self.suggestion_thread.start()

    def stop_listening(self):
        self.is_listening = False


# ================== ИНТЕРФЕЙС ==================
class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.brain = JarvisBrain()
        self.initUI()
        self.setup_jarvis()

    def initUI(self):
        self.setWindowTitle("J.A.R.V.I.S. - ПРОФЕССИОНАЛ")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 540, 720)

        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 540) // 2
        y = (screen.height() - 720) // 2
        self.move(x, y)

        self.setStyleSheet("""
            QMainWindow {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 #0a0a1a, stop:1 #050510);
            }
            QLabel {
                color: #00d4ff;
                font-family: 'Consolas';
            }
            QPushButton {
                background: transparent;
                border: 2px solid #00d4ff;
                border-radius: 20px;
                color: #00d4ff;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: rgba(0, 212, 255, 0.2);
                border-color: #00ff88;
                color: #00ff88;
            }
            QTextEdit {
                background: rgba(0, 10, 30, 0.8);
                border: 1px solid #00d4ff;
                border-radius: 10px;
                color: #00d4ff;
                font-family: 'Consolas';
                font-size: 13px;
            }
            QSpinBox, QComboBox {
                background: rgba(0, 10, 30, 0.8);
                border: 1px solid #00d4ff;
                border-radius: 5px;
                color: #00d4ff;
                font-family: 'Consolas';
                padding: 5px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Верх
        top = QHBoxLayout()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setStyleSheet("border-color: #ff0040; color: #ff0040;")
        self.close_btn.clicked.connect(self.close_app)
        top.addWidget(self.close_btn)

        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(40, 40)
        self.min_btn.setStyleSheet("border-color: #ffff00; color: #ffff00;")
        self.min_btn.clicked.connect(self.showMinimized)
        top.addWidget(self.min_btn)

        top.addStretch()

        self.status = QLabel("🟢 СИСТЕМА АКТИВНА | 🎤 СЛУШАЕТ")
        self.status.setStyleSheet("color: #00ff88; font-size: 13px; font-weight: bold;")
        top.addWidget(self.status)
        layout.addLayout(top)

        # Круг
        self.circle = QLabel()
        self.circle.setAlignment(Qt.AlignCenter)
        self.circle.setFixedHeight(220)
        self.circle.setStyleSheet("""
            QLabel {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 rgba(0, 212, 255, 0.1), 
                    stop:0.7 rgba(0, 212, 255, 0.02),
                    stop:1 transparent);
                border: 3px solid #00ff88;
                border-radius: 110px;
                margin: 10px;
            }
        """)

        self.circle_text = QLabel(self.circle)
        self.circle_text.setAlignment(Qt.AlignCenter)
        self.circle_text.setGeometry(0, 0, 540, 220)
        self.circle_text.setStyleSheet("font-size: 22px; font-weight: bold; background: transparent;")
        self.circle_text.setText("J.A.R.V.I.S.\n🎤 СЛУШАЕТ")
        layout.addWidget(self.circle)

        # Информация
        info = QLabel("🔊 Скажите 'Джарвис' для активации")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #446688; font-size: 13px; font-weight: bold;")
        layout.addWidget(info)

        # Чат
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setMaximumHeight(100)
        layout.addWidget(self.chat)

        # ================== ПАНЕЛЬ НАСТРОЕК ==================
        settings_group = QGroupBox("⚙️ НАСТРОЙКИ")
        settings_group.setStyleSheet("""
            QGroupBox {
                color: #00d4ff;
                border: 2px solid #00d4ff;
                border-radius: 10px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        settings_layout = QHBoxLayout()

        # Интервал предложений
        interval_label = QLabel("Интервал (часы):")
        interval_label.setStyleSheet("color: #88ddff;")
        settings_layout.addWidget(interval_label)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 24)
        self.interval_spin.setValue(self.brain.settings.get("suggestion_interval", 7200) // 3600)
        self.interval_spin.valueChanged.connect(self.update_interval)
        settings_layout.addWidget(self.interval_spin)

        # Кнопка "Не мешать"
        self.dnd_btn = QPushButton("🔇 НЕ МЕШАТЬ")
        self.dnd_btn.clicked.connect(self.toggle_dnd)
        settings_layout.addWidget(self.dnd_btn)

        # Кнопка "Обновить настройки"
        update_btn = QPushButton("💾 СОХРАНИТЬ")
        update_btn.clicked.connect(self.save_settings)
        settings_layout.addWidget(update_btn)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ================== КНОПКИ ==================
        btns = QHBoxLayout()

        self.cmd_btn = QPushButton("⌨️ КОМАНДА")
        self.cmd_btn.clicked.connect(self.show_command)
        btns.addWidget(self.cmd_btn)

        self.mode_btn = QPushButton("📋 РЕЖИМЫ")
        self.mode_btn.clicked.connect(self.show_modes)
        btns.addWidget(self.mode_btn)

        self.test_btn = QPushButton("🔊 ТЕСТ")
        self.test_btn.clicked.connect(self.test_voice)
        btns.addWidget(self.test_btn)

        self.suggest_btn = QPushButton("💡 ПРЕДЛОЖИТЬ")
        self.suggest_btn.clicked.connect(self.suggest_now)
        btns.addWidget(self.suggest_btn)

        layout.addLayout(btns)

        footer = QLabel("© J.A.R.V.I.S. v3.0 | ПРОФЕССИОНАЛ | ТОНИ СТАРК ИНДАСТРИЗ")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #003355; font-size: 11px; margin: 10px;")
        layout.addWidget(footer)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(1000)

        self.chat_timer = QTimer()
        self.chat_timer.timeout.connect(self.update_chat)
        self.chat_timer.start(100)

    def setup_jarvis(self):
        greeting = self.brain.get_greeting()
        moscow_time = self.brain.get_moscow_time()
        phase = self.brain.get_phase_of_day()

        welcome = f"{greeting}, сэр! Сейчас {moscow_time} по Москве. Сегодня отличный {phase}."
        self.add_msg("ДЖАРВИС", welcome)
        self.brain.speak(welcome)

        time.sleep(1)
        suggestion = "Доступные режимы: " + ", ".join(self.brain.modes.keys()) + ". Скажите 'Джарвис, включи режим'."
        self.add_msg("ДЖАРВИС", suggestion)
        self.brain.speak(suggestion)

        QTimer.singleShot(2000, self.auto_start)

    def auto_start(self):
        if MIC_OK:
            self.brain.start_listening(self.handle_response)
            interval_hours = self.brain.settings.get("suggestion_interval", 7200) // 3600
            self.add_msg("СИСТЕМА", f"🎤 Джарвис слушает в фоне...")
            self.add_msg("СИСТЕМА", f"💡 Предложения режимов каждые {interval_hours} часов")
        else:
            self.add_msg("СИСТЕМА", "⚠️ Микрофон не доступен. Используйте кнопку 'КОМАНДА'")

    def update_interval(self, value):
        """Обновление интервала"""
        self.brain.settings["suggestion_interval"] = value * 3600
        self.add_msg("СИСТЕМА", f"⏰ Интервал предложений: {value} часов")

    def toggle_dnd(self):
        """Включение/выключение режима 'Не мешать'"""
        self.brain.suggestion_active = not self.brain.suggestion_active
        if self.brain.suggestion_active:
            self.dnd_btn.setText("🔇 НЕ МЕШАТЬ")
            self.dnd_btn.setStyleSheet("border-color: #00d4ff; color: #00d4ff;")
            self.add_msg("СИСТЕМА", "🔊 Режим общения активен")
            self.brain.speak("Возвращаюсь к общению, сэр!")
        else:
            self.dnd_btn.setText("🔊 РАЗРЕШИТЬ")
            self.dnd_btn.setStyleSheet("border-color: #ff8800; color: #ff8800;")
            self.add_msg("СИСТЕМА", "🔇 Режим 'Не мешать' включён")
            self.brain.speak("Хорошо, сэр. Я не буду вас отвлекать.")

    def save_settings(self):
        self.brain.save_settings()
        self.add_msg("СИСТЕМА", "✅ Настройки сохранены")
        self.brain.speak("Настройки сохранены, сэр!")

    def suggest_now(self):
        if self.brain.suggestion_active:
            suggestion, mode = self.brain.get_random_suggestion()
            self.add_msg("ДЖАРВИС", suggestion)
            self.brain.speak(suggestion)
            self.circle_text.setText(f"J.A.R.V.I.S.\n💡 {mode.upper()}")
        else:
            self.add_msg("ДЖАРВИС", "Сэр, включён режим 'Не мешать'. Хотите разрешить общение?")
            self.brain.speak("Сэр, режим 'Не мешать' активен. Хотите отключить его?")

    def handle_response(self, response):
        if response == "EXIT":
            self.close_app()
        else:
            self.add_msg("ДЖАРВИС", response)
            self.circle_text.setText(f"J.A.R.V.I.S.\n💬 {response[:25]}")

    def add_msg(self, sender, text):
        time_str = QTime.currentTime().toString("HH:mm:ss")
        color = "#00d4ff" if sender == "ДЖАРВИС" else "#00ff88"
        html = f"""
        <div style='margin: 3px 0;'>
            <span style='color: #446688;'>[{time_str}]</span>
            <span style='color: {color}; font-weight: bold;'>{sender}:</span>
            <span style='color: #88ddff;'>{text}</span>
        </div>
        """
        self.chat.append(html)
        self.chat.verticalScrollBar().setValue(
            self.chat.verticalScrollBar().maximum()
        )

    def update_chat(self):
        while not self.brain.response_queue.empty():
            text = self.brain.response_queue.get()
            self.add_msg("ДЖАРВИС", text)
            self.circle_text.setText(f"J.A.R.V.I.S.\n💬 {text[:25]}")

    def test_voice(self):
        self.brain.speak("Голос работает, сэр! Я готов общаться с вами!")
        self.add_msg("СИСТЕМА", "🔊 Тест голоса выполнен")

    def show_command(self):
        text, ok = QInputDialog.getText(self, "КОМАНДА", "Введите команду:")
        if ok and text:
            result = self.brain.process_command(text)
            if result:
                if result == "EXIT":
                    self.close_app()
                else:
                    self.add_msg("ВЫ", text)
                    self.add_msg("ДЖАРВИС", result)
                    self.brain.speak(result)

    def show_modes(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление режимами")
        dialog.setGeometry(200, 200, 400, 300)
        dialog.setStyleSheet("background: #0a0a1a; color: #00d4ff;")
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for mode in self.brain.modes:
            list_widget.addItem(mode)
        layout.addWidget(list_widget)

        info_label = QLabel("Выберите режим")
        info_label.setStyleSheet("color: #88ddff;")
        layout.addWidget(info_label)

        btn_layout = QHBoxLayout()

        def show_mode_info():
            if list_widget.currentItem():
                mode_name = list_widget.currentItem().text()
                mode = self.brain.modes[mode_name]
                info_label.setText(f"{mode_name}: {', '.join(mode['programs'])}")

        def delete_mode():
            if list_widget.currentItem():
                mode_name = list_widget.currentItem().text()
                if mode_name in self.brain.modes:
                    del self.brain.modes[mode_name]
                    self.brain.save_modes()
                    list_widget.takeItem(list_widget.currentRow())
                    info_label.setText("Режим удалён")

        def add_mode():
            name, ok1 = QInputDialog.getText(dialog, "Новый режим", "Название режима:")
            if ok1 and name:
                progs, ok2 = QInputDialog.getText(dialog, "Новый режим", "Программы (через запятую):")
                if ok2 and progs:
                    progs_list = [p.strip() for p in progs.split(",")]
                    msg, ok3 = QInputDialog.getText(dialog, "Новый режим", "Сообщение при запуске:")
                    if ok3:
                        self.brain.modes[name] = {
                            "programs": progs_list,
                            "message": msg
                        }
                        self.brain.save_modes()
                        list_widget.addItem(name)
                        info_label.setText(f"Режим '{name}' создан!")

        list_widget.itemClicked.connect(show_mode_info)

        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(add_mode)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("🗑️ Удалить")
        del_btn.clicked.connect(delete_mode)
        btn_layout.addWidget(del_btn)

        run_btn = QPushButton("▶️ Запустить")
        run_btn.clicked.connect(lambda: self.run_selected_mode(list_widget, dialog))
        btn_layout.addWidget(run_btn)

        close_btn = QPushButton("✕ Закрыть")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec_()

    def run_selected_mode(self, list_widget, dialog):
        if list_widget.currentItem():
            mode_name = list_widget.currentItem().text()
            result = self.brain.run_mode(mode_name)
            self.add_msg("ДЖАРВИС", result)
            self.brain.speak(result)
            dialog.accept()

    def blink(self):
        style = self.circle.styleSheet()
        if "rgba(0, 212, 255, 0.1)" in style:
            self.circle.setStyleSheet("""
                QLabel {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                        stop:0 rgba(0, 212, 255, 0.2), 
                        stop:0.7 rgba(0, 212, 255, 0.03),
                        stop:1 transparent);
                    border: 3px solid #00ff88;
                    border-radius: 110px;
                    margin: 10px;
                }
            """)
        else:
            self.circle.setStyleSheet("""
                QLabel {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                        stop:0 rgba(0, 212, 255, 0.1), 
                        stop:0.7 rgba(0, 212, 255, 0.02),
                        stop:1 transparent);
                    border: 3px solid #00d4ff;
                    border-radius: 110px;
                    margin: 10px;
                }
            """)

    def close_app(self):
        self.brain.stop_listening()
        self.brain.speak("До свидания, сэр! Жду вашего возвращения!")
        QApplication.quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_app()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisWindow()
    window.show()
    sys.exit(app.exec_())