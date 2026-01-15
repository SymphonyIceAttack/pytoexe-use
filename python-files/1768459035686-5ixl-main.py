# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime, timedelta
import threading

# Конфигурация
BOT_TOKEN = "8203695173:AAF96cGjJ_LcfchvmsLAbxk2-WjkWZRNRzw"
CHAT_ID = None # Будет установлен при запуске бота# bot.py
import telebot
from telebot import types
import json
from datetime import datetime
import threading
import os

# Конфигурация
TOKEN = "8203695173:AAF96cGjJ_LcfchvmsLAbxk2-WjkWZRNRzw"
PASSWORD = "89097538585"
DATA_FILE = "shifts.json"
CONFIG_FILE = "config.json"

bot = telebot.TeleBot(TOKEN)

# Загружаем данные
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        shifts_data = json.load(f)
else:
    shifts_data = {"shifts": []}

# Словарь для авторизованных пользователей
authorized_users = set()

def save_config(chat_id):
    """Сохраняет конфигурацию"""
    config = {"chat_id": chat_id}
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Посчитать смены"))
    
    if message.from_user.id in authorized_users:
        bot.send_message(
            message.chat.id,
            "Здравствуйте! Вы уже авторизованы.",
            reply_markup=markup
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            "Введите пароль для доступа к боту:"
        )
        bot.register_next_step_handler(msg, check_password)

def check_password(message):
    """Проверяет пароль"""
    if message.text == PASSWORD:
        authorized_users.add(message.from_user.id)
        save_config(message.chat.id)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Посчитать смены"))
        
        bot.send_message(
            message.chat.id,
            "Здравствуйте! Вы успешно авторизовались.",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "Неверный пароль. Попробуйте снова с команды /start"
        )

@bot.message_handler(func=lambda message: message.text == "Посчитать смены")
def count_shifts(message):
    """Подсчитывает смены"""
    if message.from_user.id not in authorized_users:
        bot.send_message(message.chat.id, "Сначала авторизуйтесь с помощью /start")
        return
    
    # Загружаем свежие данные
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            shifts_data = json.load(f)
    
    # Определяем период
    today = datetime.now()
    if 1 <= today.day <= 15:
        period = "first_half"
        period_name = "1-15 число"
    else:
        period = "second_half"
        period_name = "16-31 число"
    
    # Подсчитываем смены по именам
    name_counts = {}
    address_details = {}
    
    for shift in shifts_data.get("shifts", []):
        shift_date = datetime.fromisoformat(shift["date"])
        
        # Проверяем период
        if period == "first_half" and 1 <= shift_date.day <= 15:
            pass
        elif period == "second_half" and shift_date.day >= 16:
            pass
        else:
            continue
        
        name = shift["name"]
        address = shift["address"]
        
        # Считаем общее количество
        name_counts[name] = name_counts.get(name, 0) + 1
        
        # Запоминаем детали по адресам
        if name not in address_details:
            address_details[name] = {}
        address_details[name][address] = address_details[name].get(address, 0) + 1
    
    # Формируем ответ
    if not name_counts:
        bot.send_message(message.chat.id, f"За {period_name} смен не было")
        return
    
    # Детальная информация по адресам
    details_text = "📊 Детальная статистика по адресам:\n\n"
    for name, addresses in address_details.items():
        details_text += f"👤 {name}:\n"
        for address, count in addresses.items():
            details_text += f" 📍 {address}: {count} смен(ы)\n"
        details_text += "\n"
    
    # Общий список
    list_text = f"📅 Смены за {period_name}:\n\n"
    sorted_names = sorted(name_counts.items(), key=lambda x: x[1], reverse=True)
    
    for i, (name, count) in enumerate(sorted_names, 1):
        list_text += f"{i}. {name} - {count} смен(ы)\n"
    
    # Отправляем сообщение
    bot.send_message(message.chat.id, details_text)
    bot.send_message(message.chat.id, list_text)

def run_bot():
    """Запускает бота"""
    print("Бот запущен...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Основной поток ждет завершения
    bot_thread.join()
