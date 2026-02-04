import json, time, threading, subprocess, os, sys
from pathlib import Path as P
import socket
import datetime

# Проверяем наличие telebot
try:
    import telebot
    from telebot import types
    print("✅ telebot импортирован успешно")
except ImportError:
    print("❌ telebot не найден, пытаемся установить...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyTelegramBotAPI"])
        import telebot
        from telebot import types
        print("✅ telebot установлен и импортирован")
    except:
        print("❌ Не удалось установить telebot")
        print("Пожалуйста, установите вручную:")
        print("pip install pyTelegramBotAPI")
        sys.exit(1)

# Импорт остальных библиотек
try:
    import pyautogui as p
    import cv2
    import numpy as n
    import winsound as w
    from plyer import notification as N
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Установите: pip install pyautogui opencv-python numpy plyer")
    sys.exit(1)

# ========== НАСТРОЙКИ ==========
d = P(__file__).parent
t = d / "temp"
t.mkdir(exist_ok=True)

# Загрузка конфига
try:
    with open(d / "config.json", "r", encoding="utf-8") as c:
        j = json.load(c)
    T = j["token"]
    C = str(j["chat_id"])
except:
    print("❌ Ошибка загрузки config.json")
    sys.exit(1)

# Создаем бота
b = telebot.TeleBot(T)

# Глобальные переменные
W = 0  # Флаг наблюдения
start_time = time.time()

# Проверка доступа
A = lambda m: str(m.chat.id) == C

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    """Основная клавиатура (Reply)"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    
    # Первый ряд
    markup.add(
        types.KeyboardButton("📸 Скриншот"),
        types.KeyboardButton("📷 Вебкамера"),
        types.KeyboardButton("📊 Статус")
    )
    
    # Второй ряд
    markup.add(
        types.KeyboardButton("👀 Наблюдение ВКЛ"),
        types.KeyboardButton("⛔ Наблюдение ВЫКЛ"),
        types.KeyboardButton("📢 Уведомление")
    )
    
    # Третий ряд
    markup.add(
        types.KeyboardButton("🛑 Выключить"),
        types.KeyboardButton("🔄 Перезагрузка"),
        types.KeyboardButton("ℹ️ Инфо")
    )
    
    # Четвертый ряд
    markup.add(
        types.KeyboardButton("🎮 Расширенное меню"),
        types.KeyboardButton("❓ Помощь"),
        types.KeyboardButton("🗑️ Очистить")
    )
    
    return markup

def inline_menu():
    """Inline меню"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Первый ряд
    markup.add(
        types.InlineKeyboardButton("📸 Скриншот", callback_data="screenshot"),
        types.InlineKeyboardButton("📷 Вебкамера", callback_data="webcam")
    )
    
    # Второй ряд
    markup.add(
        types.InlineKeyboardButton("👀 Наблюдение ВКЛ", callback_data="watch_on"),
        types.InlineKeyboardButton("⛔ Наблюдение ВЫКЛ", callback_data="watch_off")
    )
    
    # Третий ряд
    markup.add(
        types.InlineKeyboardButton("📊 Статус системы", callback_data="status"),
        types.InlineKeyboardButton("ℹ️ Информация", callback_data="info")
    )
    
    # Четвертый ряд
    markup.add(
        types.InlineKeyboardButton("🛑 Выключить ПК", callback_data="shutdown"),
        types.InlineKeyboardButton("🔄 Перезагрузить", callback_data="reboot"),
        types.InlineKeyboardButton("📢 Уведомление", callback_data="notify")
    )
    
    # Пятый ряд
    markup.add(
        types.InlineKeyboardButton("🎮 Основное меню", callback_data="main_menu"),
        types.InlineKeyboardButton("❓ Помощь", callback_data="help")
    )
    
    return markup

def shutdown_keyboard():
    """Клавиатура подтверждения выключения"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Да, выключить", callback_data="confirm_shutdown"),
        types.InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_shutdown")
    )
    return markup

def reboot_keyboard():
    """Клавиатура подтверждения перезагрузки"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Да, перезагрузить", callback_data="confirm_reboot"),
        types.InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_reboot")
    )
    return markup

# ========== ФУНКЦИИ ==========
def notify_startup():
    """Уведомление о запуске"""
    try:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Не определен"
        
        message = (
            f"🚀 <b>Удаленный доступ запущен</b>\n\n"
            f"🖥️ <b>Компьютер:</b> {hostname}\n"
            f"📍 <b>IP:</b> <code>{local_ip}</code>\n"
            f"⏰ <b>Время:</b> {datetime.datetime.now().strftime('%H:%M:%S')}\n\n"
            f"🎮 <i>Используйте кнопки для управления</i>"
        )
        
        b.send_message(C, message, parse_mode='HTML', reply_markup=main_keyboard())
        
    except Exception as e:
        print(f"❌ Ошибка уведомления: {e}")

def take_screenshot():
    """Сделать скриншот"""
    try:
        screenshot_path = t / f"screenshot_{int(time.time())}.png"
        p.screenshot().save(screenshot_path)
        
        with open(screenshot_path, "rb") as f:
            b.send_photo(C, f, caption="📸 Скриншот экрана")
        
        return True
    except Exception as e:
        b.send_message(C, f"❌ Ошибка: {e}")
        return False

def take_webcam_photo():
    """Фото с вебкамеры"""
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            webcam_path = t / f"webcam_{int(time.time())}.jpg"
            cv2.imwrite(str(webcam_path), frame)
            
            with open(webcam_path, "rb") as f:
                b.send_photo(C, f, caption="📷 Вебкамера")
            
            return True
        return False
    except:
        return False

def start_watching():
    """Запустить наблюдение"""
    global W
    
    def watch_thread():
        global W
        prev_mean = None
        
        while W:
            try:
                screenshot = p.screenshot()
                img = screenshot.resize((64, 64)).convert("L")
                current_mean = n.mean(n.array(img))
                
                if prev_mean and abs(current_mean - prev_mean) > 5:
                    screenshot_path = t / f"motion_{int(time.time())}.png"
                    screenshot.save(screenshot_path)
                    
                    with open(screenshot_path, "rb") as f:
                        b.send_photo(C, f, caption="👀 Обнаружено движение!")
                    
                    # Уведомление на ПК
                    try:
                        N.notify(
                            title="Обнаружено движение",
                            message="Скриншот отправлен в Telegram",
                            timeout=3
                        )
                    except:
                        pass
                
                prev_mean = current_mean
                time.sleep(2)
            except:
                time.sleep(5)
    
    if not W:
        W = 1
        threading.Thread(target=watch_thread, daemon=True).start()
        return True
    return False

def stop_watching():
    """Остановить наблюдение"""
    global W
    W = 0
    return True

def get_system_status():
    """Получить статус системы"""
    uptime = int(time.time() - start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    
    # Подсчет файлов в temp
    file_count = len(list(t.glob("*"))) if t.exists() else 0
    
    return (
        f"📊 <b>Статус системы</b>\n\n"
        f"🕐 <b>Время работы:</b> {hours:02d}:{minutes:02d}:{seconds:02d}\n"
        f"👀 <b>Наблюдение:</b> {'✅ ВКЛ' if W else '❌ ВЫКЛ'}\n"
        f"📁 <b>Файлов в temp:</b> {file_count}\n"
        f"⏰ <b>Текущее время:</b> {datetime.datetime.now().strftime('%H:%M:%S')}\n"
        f"💾 <b>Папка скрипта:</b>\n<code>{d}</code>"
    )

def get_system_info():
    """Получить информацию о системе"""
    try:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "Не определен"
        
        return (
            f"🖥️ <b>Информация о системе</b>\n\n"
            f"<b>Имя ПК:</b> {hostname}\n"
            f"<b>IP адрес:</b> <code>{local_ip}</code>\n"
            f"<b>ОС:</b> {os.name}\n"
            f"<b>Архитектура:</b> {platform.architecture()[0]}\n"
            f"<b>Python:</b> {sys.version.split()[0]}\n"
            f"<b>Время запуска:</b> {datetime.datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}"
        )
    except:
        return "❌ Не удалось получить информацию"

def send_notification(text):
    """Отправить уведомление на ПК"""
    try:
        N.notify(
            title="Telegram Bot",
            message=text,
            timeout=5
        )
        return True
    except:
        return False

def clear_temp():
    """Очистить временные файлы"""
    try:
        files = list(t.glob("*"))
        count = 0
        for file in files:
            try:
                file.unlink()
                count += 1
            except:
                pass
        return count
    except:
        return 0

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@b.message_handler(commands=["start", "menu"])
def start_command(m):
    if not A(m):
        return
    
    welcome_text = (
        "🤖 <b>Удаленное управление ПК</b>\n\n"
        "🎮 <i>Используйте кнопки ниже для управления</i>\n\n"
        "📱 <b>Основные возможности:</b>\n"
        "• Скриншоты экрана\n"
        "• Вебкамера\n"
        "• Наблюдение за движением\n"
        "• Управление питанием\n"
        "• Системные уведомления\n"
        "• Воспроизведение голосовых\n\n"
        "📌 <i>Для расширенного меню нажмите</i> <b>🎮 Расширенное меню</b>"
    )
    
    b.send_message(C, welcome_text, parse_mode='HTML', reply_markup=main_keyboard())

@b.message_handler(func=lambda m: m.text == "🎮 Расширенное меню")
def extended_menu(m):
    if not A(m):
        return
    
    b.send_message(C, 
                   "🎮 <b>Расширенное меню управления</b>\nВыберите действие:",
                   parse_mode='HTML',
                   reply_markup=inline_menu())

# Обработчик текстовых сообщений (кнопок Reply)
@b.message_handler(content_types=["text"])
def handle_text(m):
    if not A(m):
        return
    
    text = m.text
    
    if text == "📸 Скриншот":
        b.send_message(C, "📸 Делаю скриншот...")
        take_screenshot()
        
    elif text == "📷 Вебкамера":
        b.send_message(C, "📷 Проверяю вебкамеру...")
        if take_webcam_photo():
            b.send_message(C, "✅ Фото сделано")
        else:
            b.send_message(C, "❌ Вебкамера недоступна")
            
    elif text == "📊 Статус":
        b.send_message(C, get_system_status(), parse_mode='HTML')
        
    elif text == "👀 Наблюдение ВКЛ":
        if start_watching():
            b.send_message(C, "✅ Наблюдение запущено")
        else:
            b.send_message(C, "⚠️ Наблюдение уже запущено")
            
    elif text == "⛔ Наблюдение ВЫКЛ":
        if stop_watching():
            b.send_message(C, "✅ Наблюдение остановлено")
        else:
            b.send_message(C, "⚠️ Наблюдение уже остановлено")
            
    elif text == "📢 Уведомление":
        msg = b.send_message(C, "📝 Введите текст уведомления:")
        b.register_next_step_handler(msg, process_notification)
        
    elif text == "🛑 Выключить":
        b.send_message(C, 
                      "⚠️ <b>Подтверждение выключения</b>\nВы уверены что хотите выключить ПК?",
                      parse_mode='HTML',
                      reply_markup=shutdown_keyboard())
        
    elif text == "🔄 Перезагрузка":
        b.send_message(C,
                      "⚠️ <b>Подтверждение перезагрузки</b>\nВы уверены что хотите перезагрузить ПК?",
                      parse_mode='HTML',
                      reply_markup=reboot_keyboard())
        
    elif text == "ℹ️ Инфо":
        b.send_message(C, get_system_info(), parse_mode='HTML')
        
    elif text == "❓ Помощь":
        help_text = (
            "📚 <b>Справка по управлению</b>\n\n"
            "<b>Основные кнопки:</b>\n"
            "• 📸 Скриншот - снимок экрана\n"
            "• 📷 Вебкамера - фото с камеры\n"
            "• 👀 Наблюдение - мониторинг движения\n"
            "• 📊 Статус - информация о системе\n"
            "• 🛑 Выключение - отключить ПК\n"
            "• 🔄 Перезагрузка - перезапустить ПК\n\n"
            "<b>Дополнительно:</b>\n"
            "• Отправьте голосовое сообщение для воспроизведения\n"
            "• Используйте /menu для inline-меню\n"
            "• /clear для очистки временных файлов"
        )
        b.send_message(C, help_text, parse_mode='HTML')
        
    elif text == "🗑️ Очистить":
        count = clear_temp()
        b.send_message(C, f"✅ Удалено {count} временных файлов")

# Обработчик inline-кнопок
@b.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if not A(call.message):
        return
    
    if call.data == "screenshot":
        b.answer_callback_query(call.id, "Делаю скриншот...")
        take_screenshot()
        
    elif call.data == "webcam":
        b.answer_callback_query(call.id, "Проверяю вебкамеру...")
        if take_webcam_photo():
            b.send_message(C, "✅ Фото сделано")
        else:
            b.send_message(C, "❌ Вебкамера недоступна")
            
    elif call.data == "watch_on":
        if start_watching():
            b.answer_callback_query(call.id, "Наблюдение запущено")
            b.send_message(C, "✅ Наблюдение запущено")
        else:
            b.answer_callback_query(call.id, "Наблюдение уже запущено")
            
    elif call.data == "watch_off":
        if stop_watching():
            b.answer_callback_query(call.id, "Наблюдение остановлено")
            b.send_message(C, "✅ Наблюдение остановлено")
        else:
            b.answer_callback_query(call.id, "Наблюдение уже остановлено")
            
    elif call.data == "status":
        b.answer_callback_query(call.id, "Получаю статус...")
        b.send_message(C, get_system_status(), parse_mode='HTML')
        
    elif call.data == "info":
        b.answer_callback_query(call.id, "Получаю информацию...")
        b.send_message(C, get_system_info(), parse_mode='HTML')
        
    elif call.data == "shutdown":
        b.answer_callback_query(call.id, "Подтверждение...")
        b.send_message(C,
                      "⚠️ <b>Подтверждение выключения</b>\nВы уверены что хотите выключить ПК?",
                      parse_mode='HTML',
                      reply_markup=shutdown_keyboard())
        
    elif call.data == "reboot":
        b.answer_callback_query(call.id, "Подтверждение...")
        b.send_message(C,
                      "⚠️ <b>Подтверждение перезагрузки</b>\nВы уверены что хотите перезагрузить ПК?",
                      parse_mode='HTML',
                      reply_markup=reboot_keyboard())
        
    elif call.data == "confirm_shutdown":
        b.answer_callback_query(call.id, "Выключаю ПК...")
        b.send_message(C, "🛑 Выключение через 5 секунд...")
        os.system("shutdown /s /t 5" if os.name == 'nt' else "echo 'Выключение не поддерживается'")
        
    elif call.data == "cancel_shutdown":
        b.answer_callback_query(call.id, "Выключение отменено")
        b.send_message(C, "✅ Выключение отменено")
        os.system("shutdown /a" if os.name == 'nt' else "")
        
    elif call.data == "confirm_reboot":
        b.answer_callback_query(call.id, "Перезагружаю ПК...")
        b.send_message(C, "🔄 Перезагрузка через 5 секунд...")
        os.system("shutdown /r /t 5" if os.name == 'nt' else "echo 'Перезагрузка не поддерживается'")
        
    elif call.data == "cancel_reboot":
        b.answer_callback_query(call.id, "Перезагрузка отменена")
        b.send_message(C, "✅ Перезагрузка отменена")
        os.system("shutdown /a" if os.name == 'nt' else "")
        
    elif call.data == "notify":
        b.answer_callback_query(call.id, "Введите текст...")
        msg = b.send_message(C, "📝 Введите текст уведомления:")
        b.register_next_step_handler(msg, process_notification)
        
    elif call.data == "main_menu":
        b.answer_callback_query(call.id, "Открываю меню...")
        start_command(call.message)
        
    elif call.data == "help":
        b.answer_callback_query(call.id, "Показываю справку...")
        help_text = (
            "📚 <b>Справка по inline-меню</b>\n\n"
            "Все кнопки выполняют действия сразу.\n"
            "Для возврата в основное меню используйте /start"
        )
        b.send_message(C, help_text, parse_mode='HTML')

def process_notification(m):
    """Обработка текста уведомления"""
    if send_notification(m.text):
        b.send_message(C, f"✅ Уведомление отправлено:\n{m.text}")
    else:
        b.send_message(C, "❌ Ошибка отправки уведомления")

# Обработчик голосовых сообщений
@b.message_handler(content_types=["voice"])
def voice_handler(m):
    if not A(m):
        return
    
    try:
        b.send_message(C, "🔊 Обрабатываю голосовое...")
        
        file_info = b.get_file(m.voice.file_id)
        downloaded_file = b.download_file(file_info.file_path)
        
        ogg_path = t / "voice.ogg"
        wav_path = t / "voice.wav"
        
        with open(ogg_path, "wb") as f:
            f.write(downloaded_file)
        
        # Конвертируем
        subprocess.call(
            f'ffmpeg -y -i "{ogg_path}" "{wav_path}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Воспроизводим
        if wav_path.exists():
            w.PlaySound(str(wav_path), w.SND_FILENAME)
            b.send_message(C, "✅ Голосовое воспроизведено")
        else:
            b.send_message(C, "❌ Ошибка конвертации")
            
    except Exception as e:
        b.send_message(C, f"❌ Ошибка: {e}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Telegram Remote Control Bot")
    print("🎮 Версия с кнопками управления")
    print("=" * 50)
    
    # Импорт platform для информации
    try:
        import platform
    except:
        platform = None
    
    # Отправляем уведомление о запуске
    notify_startup()
    
    print("✅ Бот запущен")
    print("📱 Используйте Telegram для управления")
    print("=" * 50)
    
    # Запускаем бота
    try:
        b.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
        b.send_message(C, "🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        try:
            b.send_message(C, f"❌ Бот упал:\n<code>{e}</code>", parse_mode='HTML')
        except:
            pass