import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ТВОЙ ТОКЕН
TOKEN = "8427474808:AAGMJe4EcTp1JYETpMD-n8CbsjzpSCrGW-w"
bot = telebot.TeleBot(TOKEN)

# МЕНЮ С КНОПКАМИ
def menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📸 Скриншот", callback_data="screen"),
        InlineKeyboardButton("ℹ️ Инфо", callback_data="info"),
        InlineKeyboardButton("🖱️ Мышка", callback_data="mouse"),
        InlineKeyboardButton("🔠 Caps Lock", callback_data="caps"),
    ]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔥 **Главное меню**", reply_markup=menu())

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "info":
        bot.send_message(call.message.chat.id, "🖥 Компьютер: Windows\n👤 Пользователь: Test")
    elif call.data == "screen":
        bot.send_message(call.message.chat.id, "📸 Скрин (скоро будет)")
    elif call.data == "mouse":
        bot.send_message(call.message.chat.id, "🖱️ Мышка (скоро будет)")
    elif call.data == "caps":
        bot.send_message(call.message.chat.id, "🔠 Caps (скоро будет)")

print("✅ Бот с кнопками запущен!")
bot.polling()