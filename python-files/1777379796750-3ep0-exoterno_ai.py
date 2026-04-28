import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, colorchooser
import json
import os
import webbrowser
import difflib
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
import sys
import importlib.util
import shutil
import datetime

# Попытка импорта голосовых библиотек
VOICE_AVAILABLE = True
try:
    import speech_recognition as sr
    import pyttsx3
except ImportError:
    VOICE_AVAILABLE = False

# Определяем, где лежит программа (актуально и для .py, и для .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_FILE = BASE_DIR / "config.json"
KNOWLEDGE_FILE = BASE_DIR / "knowledge.json"
PLUGIN_FILE = BASE_DIR / "plugin.py"
BACKUP_DIR = BASE_DIR / "plugin_backups"

# Базовые настройки
DEFAULT_CONFIG = {
    "bg_image": "",
    "bg_color": "#1e1e1e",
    "window_color": "#2d2d2d",
    "voice_enabled": True,
    "speech_rate": 180,
    "match_threshold": 0.55,
    "user_name": ""
}

# Встроенная база команд (если плагин не переопределит)
DEFAULT_KNOWLEDGE = {
    "привет": {"type": "answer", "value": "Привет! Как дела?"},
    "как дела": {"type": "answer", "value": "У меня всё отлично, спасибо!"},
    "что ты умеешь": {"type": "answer", "value": "Я умею открывать сайты, программы, искать в интернете, поддерживать разговор. Попробуйте сказать: открой сайт ВКонтакте, открой калькулятор, или просто спросите что-нибудь."},
    "открой калькулятор": {"type": "open", "value": "calc"},
    "открой блокнот": {"type": "open", "value": "notepad"},
    "пока": {"type": "exit", "value": "До свидания!"}
}

def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default.items():
                if k not in data:
                    data[k] = v
            return data
    return default.copy()

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class ExoternoAI:
    def __init__(self, root):
        self.root = root
        self.root.title("exoterno AI")
        self.root.geometry("800x600")
        self.root.minsize(400, 300)

        # Загружаем конфиг и знания
        self.config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.knowledge = load_json(KNOWLEDGE_FILE, DEFAULT_KNOWLEDGE)

        # Имя пользователя (если нет — спросим позже)
        self.user_name = self.config.get("user_name", "")
        if not self.user_name:
            self.ask_name()

        # Голосовой движок
        self.engine = None
        if VOICE_AVAILABLE and self.config.get("voice_enabled", True):
            self.init_voice()

        # Плагин
        self.plugin = None
        self.plugin_version = "1.0"
        self.load_plugin()   # загружаем, если plugin.py уже лежит рядом

        # Визуальные переменные
        self.bg_photo = None
        self.bg_label = None

        # Строим интерфейс
        self.setup_ui()
        self.apply_appearance()

        # Приветствие
        self.add_message("exoterno AI", f"Привет, {self.user_name or 'друг'}! Я готов помочь.", "ai")
        self.update_idletasks()

    # ----------------------------------------------------------------------
    # ИНИЦИАЛИЗАЦИЯ
    # ----------------------------------------------------------------------
    def ask_name(self):
        self.config["user_name"] = "пользователь"
        save_json(CONFIG_FILE, self.config)

    def init_voice(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.config.get("speech_rate", 180))
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
        except:
            self.engine = None

    def load_plugin(self):
        """Загружает plugin.py, если он есть, и обновляет базу знаний."""
        if not PLUGIN_FILE.exists():
            return
        try:
            spec = importlib.util.spec_from_file_location("plugin", PLUGIN_FILE)
            self.plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.plugin)
            if hasattr(self.plugin, '__version__'):
                self.plugin_version = self.plugin.__version__
            if hasattr(self.plugin, 'CUSTOM_KNOWLEDGE'):
                # Плагин может дополнить/переопределить команды
                self.knowledge.update(self.plugin.CUSTOM_KNOWLEDGE)
                save_json(KNOWLEDGE_FILE, self.knowledge)
            self.add_message("Система", f"Плагин загружен. Версия {self.plugin_version}", "system")
        except Exception as e:
            self.add_message("Система", f"Ошибка загрузки плагина: {e}", "system")

    # ----------------------------------------------------------------------
    # ИНТЕРФЕЙС
    # ----------------------------------------------------------------------
    def setup_ui(self):
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=self.config["window_color"])
        top_frame.pack(side=tk.TOP, fill=tk.X)

        btn_settings = tk.Button(top_frame, text="⚙️ Настройки", command=self.open_settings)
        btn_settings.pack(side=tk.LEFT, padx=5, pady=5)

        self.voice_btn = tk.Button(top_frame, text="🎤 Голос", command=self.start_voice_input)
        self.voice_btn.pack(side=tk.LEFT, padx=5, pady=5)
        if not VOICE_AVAILABLE:
            self.voice_btn.config(state=tk.DISABLED, text="🎤 (нет библиотек)")

        btn_learn = tk.Button(top_frame, text="🧠 Научить", command=self.teach_dialog)
        btn_learn.pack(side=tk.LEFT, padx=5, pady=5)

        # Кнопка управления плагином
        btn_plugin = tk.Button(top_frame, text="📦 Плагин", command=self.load_plugin_from_file)
        btn_plugin.pack(side=tk.LEFT, padx=5, pady=5)

        # Чат область
        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            bg=self.config["bg_color"],
            fg="white",
            insertbackground="white",
            font=("Arial", 11),
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Настройка стилей сообщений
        self.chat_area.tag_config("user", foreground="#4FC3F7", font=("Arial", 11, "bold"))
        self.chat_area.tag_config("ai", foreground="#FFFFFF", font=("Arial", 11))
        self.chat_area.tag_config("thinking", foreground="#AAAAAA", font=("Arial", 10, "italic"))
        self.chat_area.tag_config("system", foreground="#FFD54F", font=("Arial", 10, "italic"))

        # Нижняя панель ввода
        bottom_frame = tk.Frame(self.root, bg=self.config["window_color"])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_field = tk.Entry(bottom_frame, bg="#3c3c3c", fg="white", insertbackground="white",
                                    font=("Arial", 12), relief=tk.FLAT)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 2), pady=5)
        self.input_field.bind("<Return>", lambda event: self.send_message())
        self.input_field.focus_set()

        send_btn = tk.Button(bottom_frame, text="➤", command=self.send_message,
                             bg="#0a84ff", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT)
        send_btn.pack(side=tk.RIGHT, padx=(2, 5), pady=5)

        # Метка версии плагина
        self.version_label = tk.Label(bottom_frame, text=f"Плагин: {self.plugin_version}",
                                      bg=self.config["window_color"], fg="gray")
        self.version_label.pack(side=tk.RIGHT, padx=5, pady=2)

        self.root.bind("<Configure>", self.on_resize)

    def apply_appearance(self):
        self.root.configure(bg=self.config["window_color"])
        self.chat_area.configure(bg=self.config["bg_color"])
        self.set_background_image(self.config.get("bg_image", ""))

    def set_background_image(self, path):
        # Упрощённо – картинка на весь фон root, чат поверх.
        if self.bg_label:
            self.bg_label.destroy()
            self.bg_label = None
        if path and os.path.exists(path):
            try:
                img = tk.PhotoImage(file=path)
                self.bg_photo = img
                self.bg_label = tk.Label(self.root, image=img)
                self.bg_label.place(relwidth=1, relheight=1)
                # Чтобы чат не перекрывался полностью, можно сделать прозрачность,
                # но в базовом Tkinter это сложно. Оставим как есть.
            except tk.TclError:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение")

    # ----------------------------------------------------------------------
    # СООБЩЕНИЯ В ЧАТ
    # ----------------------------------------------------------------------
    def add_message(self, sender, text, tag):
        self.chat_area.config(state=tk.NORMAL)
        if sender:
            self.chat_area.insert(tk.END, f"{sender}: ", "user" if sender != "exoterno AI" else "ai")
        self.chat_area.insert(tk.END, f"{text}\n\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    # ----------------------------------------------------------------------
    # ОСНОВНАЯ ЛОГИКА ОБРАБОТКИ КОМАНД
    # ----------------------------------------------------------------------
    def send_message(self):
        text = self.input_field.get().strip().lower()
        if not text:
            return
        self.input_field.delete(0, tk.END)
        self.add_message("Вы", text, "user")
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()

    def process_command(self, text):
        # Размышления
        self.add_message("exoterno AI (размышление)", "🧠 Анализ запроса...", "thinking")
        time.sleep(0.3)

        if text in ["пока", "выход", "стоп"]:
            self.add_message("exoterno AI", "До свидания!", "ai")
            self.speak("До свидания!")
            self.root.after(1000, self.root.destroy)
            return

        # Поиск в базе знаний
        cmd_key, score = self.find_command(text)
        if cmd_key:
            self.add_message("exoterno AI (размышление)",
                             f"✅ Найдена команда: \"{cmd_key}\" (совпадение {score:.2f})", "thinking")
            time.sleep(0.2)
            self.execute_action(cmd_key)
            return

        # Умный анализ: сайты
        if "открой сайт" in text or "открой в" in text:
            for prefix in ["открой сайт", "открой в"]:
                if prefix in text:
                    site_name = text.split(prefix, 1)[1].strip()
                    break
            self.smart_open_site(site_name)
            return

        # Умный анализ: программы
        if any(word in text for word in ["открой программу", "запусти", "открой"]):
            for prefix in ["открой программу", "запусти", "открой"]:
                if prefix in text:
                    prog = text.split(prefix, 1)[1].strip()
                    break
            self.smart_open_program(prog)
            return

        # Ничего не подошло — поиск в Google
        self.add_message("exoterno AI (размышление)", "🌐 Запускаю поиск в интернете...", "thinking")
        time.sleep(0.3)
        webbrowser.open(f"https://www.google.com/search?q={text.replace(' ', '+')}")
        self.add_message("exoterno AI", f"Я открыл поиск Google по запросу: {text}", "ai")
        self.speak(f"Я поискал в интернете по запросу {text}")

    def find_command(self, text):
        best_key = None
        best_score = 0
        for key in self.knowledge.keys():
            score = difflib.SequenceMatcher(None, text, key).ratio()
            if score > best_score:
                best_score = score
                best_key = key
        threshold = self.config.get("match_threshold", 0.55)
        if best_score >= threshold:
            return best_key, best_score
        return None, best_score

    def execute_action(self, key):
        cmd = self.knowledge[key]
        action = cmd["type"]
        value = cmd["value"]
        if action == "answer":
            self.add_message("exoterno AI", value, "ai")
            self.speak(value)
        elif action == "open":
            self.add_message("exoterno AI", f"Открываю {value}...", "ai")
            os.system(value)
        elif action == "open_url":
            self.add_message("exoterno AI", f"Открываю {value}...", "ai")
            webbrowser.open(value)
            self.speak(f"Открываю {value}")
        elif action == "exit":
            self.add_message("exoterno AI", value, "ai")
            self.speak(value)
            self.root.after(1000, self.root.destroy)

    def smart_open_site(self, site_name):
        if site_name.startswith("http"):
            webbrowser.open(site_name)
            self.add_message("exoterno AI", f"Открываю {site_name}", "ai")
            return
        domain = site_name.replace(" ", "").lower()
        for w in ["сайт", "страницу", "в", "на"]:
            domain = domain.replace(w, "")
        urls_to_try = [
            f"https://www.{domain}.com",
            f"https://{domain}.com",
            f"https://www.{domain}.ru",
            f"https://{domain}.ru",
            f"https://www.{domain}.org",
        ]
        self.add_message("exoterno AI (размышление)", f"🔗 Пробую открыть сайт: {domain}...", "thinking")
        time.sleep(0.2)
        for url in urls_to_try:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=2):
                    self.add_message("exoterno AI", f"✅ Сайт найден, открываю: {url}", "ai")
                    webbrowser.open(url)
                    self.speak(f"Открываю {domain}")
                    return
            except:
                continue
        # Не открылся ни один — поиск
        webbrowser.open(f"https://www.google.com/search?q={site_name}")
        self.add_message("exoterno AI", f"Не удалось открыть сайт {site_name}, вот результаты поиска.", "ai")
        self.speak(f"Сайт {site_name} не открылся, смотрите поиск")

    def smart_open_program(self, program):
        self.add_message("exoterno AI (размышление)", f"⚙️ Пытаюсь запустить программу: {program}...", "thinking")
        time.sleep(0.2)
        safe_prog = program.lower().strip()
        # Простые синонимы
        if safe_prog in ["калькулятор", "кальк"]:
            safe_prog = "calc"
        elif safe_prog in ["блокнот", "notepad"]:
            safe_prog = "notepad"
        elif safe_prog in ["паинт", "рисование"]:
            safe_prog = "mspaint"
        try:
            os.system(f"start {safe_prog}")
            self.add_message("exoterno AI", f"Запускаю {safe_prog}", "ai")
            self.speak(f"Запускаю {safe_prog}")
        except:
            webbrowser.open(f"https://www.google.com/search?q=скачать+{program}")
            self.add_message("exoterno AI", f"Возможно, {program} придётся скачать, я открыл поиск.", "ai")

    # ----------------------------------------------------------------------
    # ГОЛОС
    # ----------------------------------------------------------------------
    def speak(self, text):
        if self.engine and self.config.get("voice_enabled", True):
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except:
                pass

    def start_voice_input(self):
        if not VOICE_AVAILABLE:
            messagebox.showinfo("Голос", "Голосовые библиотеки не установлены.")
            return
        self.voice_btn.config(state=tk.DISABLED, text="🎤 Слушаю...")
        threading.Thread(target=self.voice_listen, daemon=True).start()

    def voice_listen(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                self.add_message("Система", "🎤 Говорите...", "system")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = recognizer.recognize_google(audio, language="ru-RU")
                self.root.after(0, self.handle_voice_result, text)
            except Exception as e:
                self.root.after(0, self.handle_voice_error, str(e))
        finally:
            self.root.after(0, lambda: self.voice_btn.config(state=tk.NORMAL, text="🎤 Голос"))

    def handle_voice_result(self, text):
        self.add_message("Вы (голос)", text, "user")
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()

    def handle_voice_error(self, error):
        self.add_message("Система", f"Ошибка распознавания: {error}", "system")

    # ----------------------------------------------------------------------
    # РУЧНОЕ ОБУЧЕНИЕ
    # ----------------------------------------------------------------------
    def teach_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Обучение exoterno AI")
        win.geometry("400x220")
        win.configure(bg="#2d2d2d")
        tk.Label(win, text="Фраза (что скажет пользователь):", bg="#2d2d2d", fg="white").pack(pady=5)
        phrase_entry = tk.Entry(win, width=40)
        phrase_entry.pack()
        tk.Label(win, text="Тип (ответ/сайт/программа):", bg="#2d2d2d", fg="white").pack(pady=5)
        type_entry = tk.Entry(win, width=40)
        type_entry.pack()
        tk.Label(win, text="Значение (текст, URL или команда):", bg="#2d2d2d", fg="white").pack(pady=5)
        value_entry = tk.Entry(win, width=40)
        value_entry.pack()

        def save():
            phrase = phrase_entry.get().strip().lower()
            atype = type_entry.get().strip().lower()
            value = value_entry.get().strip()
            if not phrase or not atype or not value:
                messagebox.showwarning("Заполните все поля")
                return
            if atype not in ["ответ", "сайт", "программа"]:
                messagebox.showwarning("Тип должен быть: ответ, сайт или программа")
                return
            action_map = {"ответ": "answer", "сайт": "open_url", "программа": "open"}
            self.knowledge[phrase] = {"type": action_map[atype], "value": value}
            save_json(KNOWLEDGE_FILE, self.knowledge)
            self.add_message("Система", f"Новая команда '{phrase}' обучена.", "system")
            win.destroy()

        tk.Button(win, text="Обучить", command=save).pack(pady=10)

    # ----------------------------------------------------------------------
    # НАСТРОЙКИ
    # ----------------------------------------------------------------------
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Настройки")
        win.geometry("400x300")
        win.configure(bg="#2d2d2d")

        tk.Label(win, text="Цвет фона чата:", bg="#2d2d2d", fg="white").pack(pady=5)
        btn_bg = tk.Button(win, text="Выбрать", command=lambda: self.choose_color("bg_color"))
        btn_bg.pack()

        tk.Label(win, text="Цвет окна:", bg="#2d2d2d", fg="white").pack(pady=5)
        btn_win = tk.Button(win, text="Выбрать", command=lambda: self.choose_color("window_color"))
        btn_win.pack()

        tk.Label(win, text="Фоновая картинка (путь):", bg="#2d2d2d", fg="white").pack(pady=5)
        img_frame = tk.Frame(win, bg="#2d2d2d")
        img_frame.pack()
        img_entry = tk.Entry(img_frame, width=30)
        img_entry.pack(side=tk.LEFT, padx=5)
        img_entry.insert(0, self.config.get("bg_image", ""))
        def browse_img():
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.gif")])
            if path:
                img_entry.delete(0, tk.END)
                img_entry.insert(0, path)
        tk.Button(img_frame, text="Обзор", command=browse_img).pack(side=tk.LEFT)

        def save():
            self.config["bg_image"] = img_entry.get()
            save_json(CONFIG_FILE, self.config)
            self.apply_appearance()
            win.destroy()
            self.add_message("Система", "Настройки сохранены.", "system")

        tk.Button(win, text="Сохранить", command=save).pack(pady=10)

    def choose_color(self, key):
        color = colorchooser.askcolor(title="Выберите цвет")[1]
        if color:
            self.config[key] = color
            save_json(CONFIG_FILE, self.config)
            self.apply_appearance()

    # ----------------------------------------------------------------------
    # ПЛАГИНЫ (ОБНОВЛЕНИЕ)
    # ----------------------------------------------------------------------
    def load_plugin_from_file(self):
        """Выбрать новый plugin.py, заменить старый с бэкапом и загрузить."""
        path = filedialog.askopenfilename(
            title="Выберите файл плагина (.py)",
            filetypes=[("Python плагин", "*.py")]
        )
        if not path:
            return
        src = Path(path)
        if not src.exists():
            return

        BACKUP_DIR.mkdir(exist_ok=True)

        # Бэкап старого плагина
        if PLUGIN_FILE.exists():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"plugin_{timestamp}.py.bak"
            shutil.copy(PLUGIN_FILE, BACKUP_DIR / backup_name)

        # Копируем новый плагин
        shutil.copy(src, PLUGIN_FILE)

        # Сбрасываем знания до дефолтных и перезагружаем плагин
        self.knowledge = load_json(KNOWLEDGE_FILE, DEFAULT_KNOWLEDGE)
        self.load_plugin()
        self.version_label.config(text=f"Плагин: {self.plugin_version}")
        save_json(CONFIG_FILE, self.config)
        self.add_message("Система",
                         f"Плагин обновлён до версии {self.plugin_version}. "
                         f"Старый сохранён в {BACKUP_DIR.name}", "system")

    def on_resize(self, event=None):
        pass

# ----------------------------------------------------------------------
# ЗАПУСК
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ExoternoAI(root)
    root.mainloop()