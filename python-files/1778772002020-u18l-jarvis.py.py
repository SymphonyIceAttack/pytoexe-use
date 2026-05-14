import speech_recognition as sr
import pyttsx3
import subprocess
import os
import webbrowser
import datetime
import time
import sys
import random
import psutil
import ctypes
import socket
import threading
import queue
import re
import json
import shutil
import getpass
import platform
import requests
import pyautogui
import keyboard
import winreg
import string
import glob
import hashlib
import tempfile
import zipfile
import math
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import pickle

# ==================== LOGO HANDLER ====================
class LogoHandler:
    @staticmethod
    def set_console_icon(icon_path):
        """Set console window icon"""
        try:
            import ctypes
            # Convert to absolute path
            abs_path = os.path.abspath(icon_path)
            if os.path.exists(abs_path):
                # Set window icon using Windows API
                ctypes.windll.user32.SetWindowTextW(ctypes.windll.kernel32.GetConsoleWindow(), "JARVIS AI - Ultimate Assistant")
                print(f"✓ Logo loaded: {abs_path}")
            else:
                print("⚠️ Logo file not found, using default")
        except:
            pass

# ==================== ULTIMATE SYSTEM SCANNER ====================
class UltimateSystemScanner:
    def __init__(self):
        self.all_applications = {}
        self.system_info = {}
        self.drive_info = {}
        self.network_info = {}
        self.user_data = {}
        
    def comprehensive_system_scan(self):
        """Perform the most comprehensive system scan possible"""
        
        # Get all drives
        self.scan_drives()
        
        # Scan for applications
        self.scan_all_applications()
        
        # Scan system information
        self.scan_system_info()
        
        # Scan network
        self.scan_network_info()
        
        # Scan user data
        self.scan_user_data()
        
        return {
            'applications': self.all_applications,
            'system': self.system_info,
            'drives': self.drive_info,
            'network': self.network_info,
            'user': self.user_data
        }
    
    def scan_drives(self):
        """Scan all drives with detailed info"""
        for drive_letter in string.ascii_uppercase:
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                try:
                    usage = shutil.disk_usage(drive_path)
                    self.drive_info[drive_path] = {
                        'total_gb': usage.total / (1024**3),
                        'used_gb': usage.used / (1024**3),
                        'free_gb': usage.free / (1024**3),
                        'percent_used': (usage.used / usage.total) * 100,
                        'drive_type': self.get_drive_type(drive_path),
                        'volume_name': self.get_volume_name(drive_path)
                    }
                except:
                    pass
    
    def get_drive_type(self, drive_path):
        """Get drive type (HDD, SSD, Removable, etc.)"""
        try:
            import win32file
            drive_type = win32file.GetDriveType(drive_path)
            types = {2: "Removable", 3: "Fixed (HDD/SSD)", 4: "Network", 5: "CD-ROM"}
            return types.get(drive_type, "Unknown")
        except:
            return "Unknown"
    
    def get_volume_name(self, drive_path):
        """Get volume name of drive"""
        try:
            import win32api
            return win32api.GetVolumeInformation(drive_path)[0]
        except:
            return "Local Drive"
    
    def scan_all_applications(self):
        """Enhanced application scanning"""
        search_locations = [
            # Standard Program Files
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            os.path.expanduser("~\\AppData\\Local\\Programs"),
            os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"),
            os.path.expanduser("~\\Desktop"),
            # Portable Apps
            "C:\\PortableApps",
            os.path.expanduser("~\\PortableApps"),
            # Game Launchers
            "C:\\Program Files\\Steam",
            "C:\\Program Files (x86)\\Steam",
            "C:\\Program Files\\Epic Games",
            "C:\\Program Files\\Origin",
            "C:\\Program Files\\Ubisoft",
            # Development Tools
            "C:\\Program Files\\Microsoft VS Code",
            "C:\\Program Files\\JetBrains",
            "C:\\Users\\{}\\AppData\\Local\\Programs".format(getpass.getuser()),
        ]
        
        # Scan all drives for additional locations
        for drive in self.drive_info.keys():
            for location in ["Program Files", "Program Files (x86)", "Programs", "Applications"]:
                path = os.path.join(drive, location)
                if os.path.exists(path):
                    search_locations.append(path)
        
        # Perform scanning
        for location in search_locations:
            if os.path.exists(location):
                try:
                    self.scan_directory_for_apps(location)
                except:
                    pass
        
        # Registry scanning
        self.scan_registry_apps()
    
    def scan_directory_for_apps(self, directory, max_depth=4):
        """Recursively scan directory for applications"""
        try:
            for root, dirs, files in os.walk(directory):
                depth = root.replace(directory, '').count(os.sep)
                if depth > max_depth:
                    continue
                
                for file in files:
                    if file.lower().endswith(('.exe', '.lnk', '.bat', '.cmd')):
                        full_path = os.path.join(root, file)
                        app_name = os.path.splitext(file)[0]
                        
                        # Get additional file info
                        try:
                            file_size = os.path.getsize(full_path) / (1024**2)
                            modified_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                            creation_time = datetime.fromtimestamp(os.path.getctime(full_path))
                        except:
                            file_size = 0
                            modified_time = datetime.now()
                            creation_time = datetime.now()
                        
                        self.all_applications[app_name.lower()] = {
                            'path': full_path,
                            'size_mb': file_size,
                            'modified': modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'created': creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                            'type': 'Portable' if 'portable' in root.lower() else 'Installed'
                        }
        except:
            pass
    
    def scan_registry_apps(self):
        """Scan registry for installed applications"""
        try:
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if self.reg_value_exists(subkey, "DisplayVersion") else "Unknown"
                                publisher = winreg.QueryValueEx(subkey, "Publisher")[0] if self.reg_value_exists(subkey, "Publisher") else "Unknown"
                                
                                if display_name and display_name.lower() not in self.all_applications:
                                    self.all_applications[display_name.lower()] = {
                                        'path': "Registry Installed",
                                        'version': display_version,
                                        'publisher': publisher,
                                        'type': 'Installed'
                                    }
                            except:
                                pass
                        except:
                            pass
                except:
                    pass
        except:
            pass
    
    def reg_value_exists(self, key, value_name):
        """Check if registry value exists"""
        try:
            winreg.QueryValueEx(key, value_name)
            return True
        except:
            return False
    
    def scan_system_info(self):
        """Get comprehensive system information"""
        try:
            self.system_info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'os_release': platform.release(),
                'architecture': platform.machine(),
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'username': getpass.getuser(),
                'python_version': sys.version,
                'cpu_cores_physical': psutil.cpu_count(logical=False),
                'cpu_cores_logical': psutil.cpu_count(logical=True),
                'cpu_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else "N/A",
                'total_ram_gb': psutil.virtual_memory().total / (1024**3),
                'available_ram_gb': psutil.virtual_memory().available / (1024**3),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Battery info
            battery = psutil.sensors_battery()
            if battery:
                self.system_info['battery_percent'] = battery.percent
                self.system_info['battery_plugged'] = battery.power_plugged
        except:
            pass
    
    def scan_network_info(self):
        """Get network information"""
        try:
            interfaces = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append({
                            'name': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        })
            
            self.network_info = {
                'interfaces': interfaces,
                'hostname': socket.gethostname(),
                'default_gateway': self.get_default_gateway()
            }
        except:
            pass
    
    def get_default_gateway(self):
        """Get default gateway"""
        try:
            result = subprocess.run('ipconfig', capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'Default Gateway' in line and ':' in line:
                    return line.split(':')[-1].strip()
            return "Unknown"
        except:
            return "Unknown"
    
    def scan_user_data(self):
        """Scan user data and preferences"""
        try:
            self.user_data = {
                'user_directories': {
                    'desktop': os.path.expanduser("~\\Desktop"),
                    'documents': os.path.expanduser("~\\Documents"),
                    'downloads': os.path.expanduser("~\\Downloads"),
                    'pictures': os.path.expanduser("~\\Pictures"),
                    'music': os.path.expanduser("~\\Music"),
                    'videos': os.path.expanduser("~\\Videos")
                },
                'recent_files': self.get_recent_files(),
                'large_files': self.get_large_files()
            }
        except:
            pass
    
    def get_recent_files(self, limit=10):
        """Get recently accessed files"""
        recent_files = []
        try:
            recent_path = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Recent")
            if os.path.exists(recent_path):
                files = glob.glob(os.path.join(recent_path, "*.lnk"))
                for file in files[:limit]:
                    recent_files.append(os.path.basename(file).replace('.lnk', ''))
        except:
            pass
        return recent_files
    
    def get_large_files(self, size_mb=100, limit=5):
        """Get large files on system"""
        large_files = []
        try:
            for drive in self.drive_info.keys():
                try:
                    for root, dirs, files in os.walk(drive):
                        for file in files[:10]:
                            try:
                                file_path = os.path.join(root, file)
                                size = os.path.getsize(file_path) / (1024**2)
                                if size > size_mb:
                                    large_files.append({
                                        'name': file,
                                        'path': file_path,
                                        'size_mb': size
                                    })
                                    if len(large_files) >= limit:
                                        break
                            except:
                                pass
                except:
                    pass
        except:
            pass
        return large_files[:limit]

# ==================== ULTIMATE JARVIS ====================
class UltimateJarvis:
    def __init__(self):
        print("🚀 Initializing Ultimate Jarvis Assistant...")
        
        # Initialize scanner
        self.scanner = UltimateSystemScanner()
        
        # Voice setup with better configuration
        self.engine = pyttsx3.init()
        self.setup_voice()
        
        # Enhanced voice recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.command_queue = queue.Queue()
        self.listening = True
        self.wake_word = "jarvis"
        
        # Performance optimization
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Command history and analytics
        self.command_history = []
        self.start_time = datetime.now()
        self.session_commands = 0
        self.successful_commands = 0
        
        # Configuration
        self.settings = self.load_settings()
        
        # Perform comprehensive scan
        print("🔍 Performing comprehensive system scan...")
        self.system_data = self.scanner.comprehensive_system_scan()
        print(f"✅ Scan complete! Found {len(self.system_data['applications'])} applications")
        
        # Start listening
        self.start_background_listening()
        
        # Show startup message
        self.greeting()
    
    def setup_voice(self):
        """Enhanced voice configuration"""
        try:
            voices = self.engine.getProperty('voices')
            
            # Try to set a premium voice if available
            for voice in voices:
                if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                elif len(voices) > 1:
                    self.engine.setProperty('voice', voices[1].id)
            
            self.engine.setProperty('rate', 175)  # Slightly slower for clarity
            self.engine.setProperty('volume', 1.0)  # Max volume
        except:
            pass
    
    def load_settings(self):
        """Load user settings"""
        default_settings = {
            'wake_word': 'jarvis',
            'voice_speed': 175,
            'voice_volume': 1.0,
            'auto_complete': True,
            'sound_effects': True,
            'dark_mode': True,
            'confirmation_before_action': True
        }
        
        try:
            if os.path.exists('jarvis_settings.json'):
                with open('jarvis_settings.json', 'r') as f:
                    settings = json.load(f)
                    return settings
        except:
            pass
        
        return default_settings
    
    def save_settings(self):
        """Save user settings"""
        try:
            with open('jarvis_settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except:
            pass
    
    def greeting(self):
        """Enhanced greeting message"""
        greeting = f"Welcome back! I've completed scanning your system. Found {len(self.system_data['applications'])} applications across {len(self.system_data['drives'])} drives. System is running with {self.system_data['system'].get('cpu_cores_physical', 'N/A')} CPU cores and {self.system_data['system'].get('total_ram_gb', 0):.1f} GB of RAM. How may I assist you today?"
        self.speak(greeting)
    
    def start_background_listening(self):
        """Enhanced background listening"""
        self.listening = True
        self.listen_thread = threading.Thread(target=self._continuous_listen, daemon=True)
        self.listen_thread.start()
    
    def _continuous_listen(self):
        """Enhanced continuous listening"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            while self.listening:
                try:
                    audio = self.recognizer.listen(source, timeout=0.3, phrase_time_limit=3)
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        if self.wake_word in text:
                            self.print_colored("🎤 Wake word detected!", 'green')
                            self.speak("Yes?")
                            
                            audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=8)
                            command = self.recognizer.recognize_google(audio).lower()
                            self.command_queue.put(command)
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError:
                        pass
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    pass
    
    def get_command(self):
        """Get command from queue"""
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None
    
    def speak(self, text):
        """Enhanced speak function with display"""
        self.print_colored(f"\n🤖 JARVIS: {text}", 'cyan')
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass
    
    def print_colored(self, text, color='white'):
        """Print colored text to console"""
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m'
        }
        reset = '\033[0m'
        print(f"{colors.get(color, colors['white'])}{text}{reset}")
    
    def print_header(self):
        """Print enhanced header"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Try to load logo
        logo_path = r"C:\Users\bradz\Pictures\Screenshots\Vortex util.ico.png"
        if os.path.exists(logo_path):
            print(f"\033[95m")
            print("=" * 80)
            print(f"     {os.path.basename(logo_path).replace('.ico.png', '').upper()} UTILITY SYSTEM")
            print("=" * 80)
            print("\033[0m")
        
        print("\033[96m" + "=" * 80 + "\033[0m")
        print("\033[95m" + " " * 25 + "ULTIMATE JARVIS AI ASSISTANT" + "\033[0m")
        print("\033[96m" + "=" * 80 + "\033[0m")
        print(f"\033[93m📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
        print(f"\033[92m🎤 Wake Word: '{self.wake_word}'\033[0m")
        print(f"\033[94m📱 Applications: {len(self.system_data['applications'])}\033[0m")
        print(f"\033[92m💾 Drives: {len(self.system_data['drives'])}\033[0m")
        print(f"\033[96m🧠 Memory: {self.system_data['system'].get('available_ram_gb', 0):.1f}/{self.system_data['system'].get('total_ram_gb', 0):.1f} GB\033[0m")
        
        # Battery status
        if 'battery_percent' in self.system_data['system']:
            battery_icon = "🔋" if not self.system_data['system'].get('battery_plugged', False) else "⚡"
            print(f"{battery_icon} Battery: {self.system_data['system']['battery_percent']}%")
        
        print("\033[96m" + "=" * 80 + "\033[0m")
        print("\033[93m💡 Say 'Jarvis' followed by your command!" + "\033[0m")
        print("\033[90m📖 Say 'Help' for complete command list\033[0m\n")
    
    def get_voice_input(self, prompt="I'm listening"):
        """Enhanced voice input with confirmation"""
        self.speak(prompt)
        self.print_colored("🎤 Listening for your response...", 'yellow')
        
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio).lower()
                self.print_colored(f"📝 You said: {text}", 'green')
                
                # Confirmation
                self.speak(f"Did you say {text}?")
                confirm = self.listen_for_confirmation()
                if confirm:
                    return text
                else:
                    return self.get_voice_input("Please repeat your command")
            except:
                self.print_colored("❌ No input detected", 'red')
                return ""
    
    def listen_for_confirmation(self):
        """Listen for yes/no confirmation"""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=3)
                text = self.recognizer.recognize_google(audio).lower()
                return 'yes' in text or 'yeah' in text or 'correct' in text or 'right' in text
        except:
            return True  # Default to True if unclear
    
    def show_dashboard(self):
        """Show comprehensive system dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("\033[96m" + "╔" + "═" * 78 + "╗" + "\033[0m")
        print("\033[96m║" + "\033[93m" + " SYSTEM DASHBOARD ".center(78) + "\033[96m║" + "\033[0m")
        print("\033[96m╠" + "═" * 78 + "╣" + "\033[0m")
        
        # System Info
        print("\033[96m║\033[92m SYSTEM INFORMATION".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   OS: {self.system_data['system'].get('os', 'N/A')} {self.system_data['system'].get('os_release', 'N/A')}".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   CPU: {self.system_data['system'].get('processor', 'N/A')[:50]}".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   Cores: {self.system_data['system'].get('cpu_cores_physical', 'N/A')} Physical, {self.system_data['system'].get('cpu_cores_logical', 'N/A')} Logical".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   RAM: {self.system_data['system'].get('available_ram_gb', 0):.1f} GB Available / {self.system_data['system'].get('total_ram_gb', 0):.1f} GB Total".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   Boot Time: {self.system_data['system'].get('boot_time', 'N/A')}".ljust(79) + "\033[96m║\033[0m")
        
        print("\033[96m╠" + "═" * 78 + "╣" + "\033[0m")
        
        # Drive Info
        print("\033[96m║\033[92m DRIVE INFORMATION".ljust(79) + "\033[96m║\033[0m")
        for drive, info in self.system_data['drives'].items():
            bar_length = 20
            used_percent = info['percent_used'] / 100
            filled = int(bar_length * used_percent)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            color = '92' if info['percent_used'] < 70 else ('93' if info['percent_used'] < 90 else '91')
            print(f"\033[96m║   {drive} \033[{color}m[{bar}] {info['used_gb']:.1f}/{info['total_gb']:.1f} GB ({info['percent_used']:.0f}%)\033[0m".ljust(79) + "\033[96m║\033[0m")
        
        print("\033[96m╠" + "═" * 78 + "╣" + "\033[0m")
        
        # Performance Stats
        print("\033[96m║\033[92m PERFORMANCE STATISTICS".ljust(79) + "\033[96m║\033[0m")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_color = '92' if cpu_percent < 50 else ('93' if cpu_percent < 80 else '91')
        print(f"\033[96m║   CPU Usage: \033[{cpu_color}m{cpu_percent}%\033[0m".ljust(79) + "\033[96m║\033[0m")
        
        # RAM usage
        ram_percent = psutil.virtual_memory().percent
        ram_color = '92' if ram_percent < 50 else ('93' if ram_percent < 80 else '91')
        print(f"\033[96m║   RAM Usage: \033[{ram_color}m{ram_percent}%\033[0m".ljust(79) + "\033[96m║\033[0m")
        
        # Session stats
        session_duration = datetime.now() - self.start_time
        print(f"\033[96m║   Session Duration: {str(session_duration).split('.')[0]}".ljust(79) + "\033[96m║\033[0m")
        print(f"\033[96m║   Commands Processed: {self.session_commands}".ljust(79) + "\033[96m║\033[0m")
        
        print("\033[96m╚" + "═" * 78 + "╝" + "\033[0m")
        
        self.speak("Dashboard displayed")
    
    def show_applications(self, category='all'):
        """Show applications in categorized view"""
        apps = list(self.system_data['applications'].keys())[:25]
        
        print("\033[96m" + "╔" + "═" * 78 + "╗" + "\033[0m")
        print("\033[96m║" + "\033[93m" + f" APPLICATIONS ({len(self.system_data['applications'])} total) ".center(78) + "\033[96m║" + "\033[0m")
        print("\033[96m╠" + "═" * 78 + "╣" + "\033[0m")
        
        # Display in columns
        col_width = 25
        for i in range(0, len(apps), 3):
            row = apps[i:i+3]
            line = ""
            for app in row:
                line += app[:col_width-2].ljust(col_width)
            print("\033[96m║ " + "\033[97m" + line.ljust(76) + "\033[96m║\033[0m")
        
        print("\033[96m╚" + "═" * 78 + "╝" + "\033[0m")
        self.speak(f"Showing {len(apps)} of {len(self.system_data['applications'])} applications")
    
    def search_applications(self, search_term):
        """Enhanced application search"""
        results = []
        search_lower = search_term.lower()
        
        for app_name, app_info in self.system_data['applications'].items():
            if search_lower in app_name:
                results.append(app_name)
        
        if results:
            print("\033[96m" + "╔" + "═" * 78 + "╗" + "\033[0m")
            print("\033[96m║" + "\033[93m" + f" SEARCH RESULTS: '{search_term}' ({len(results)} found)".center(78) + "\033[96m║" + "\033[0m")
            print("\033[96m╠" + "═" * 78 + "╣" + "\033[0m")
            
            for result in results[:20]:
                print("\033[96m║ " + "\033[92m• " + "\033[97m" + result.ljust(74) + "\033[96m║\033[0m")
            
            print("\033[96m╚" + "═" * 78 + "╝" + "\033[0m")
            self.speak(f"Found {len(results)} applications matching {search_term}")
        else:
            self.speak(f"No applications found matching {search_term}")
    
    def launch_application(self, app_name):
        """Enhanced application launcher"""
        app_name_lower = app_name.lower()
        
        # Direct match
        if app_name_lower in self.system_data['applications']:
            app_path = self.system_data['applications'][app_name_lower].get('path', '')
            if app_path and os.path.exists(app_path):
                try:
                    self.print_colored(f"🚀 Launching {app_name}...", 'green')
                    subprocess.Popen([app_path])
                    self.speak(f"Launched {app_name}")
                    return True
                except:
                    pass
        
        # Try to find similar
        for installed_app, info in self.system_data['applications'].items():
            if app_name_lower in installed_app or installed_app in app_name_lower:
                app_path = info.get('path', '')
                if app_path and os.path.exists(app_path):
                    try:
                        self.print_colored(f"🚀 Launching {installed_app}...", 'green')
                        subprocess.Popen([app_path])
                        self.speak(f"Launched {installed_app}")
                        return True
                    except:
                        pass
        
        # Try system command
        try:
            subprocess.Popen(app_name)
            self.speak(f"Launched {app_name}")
            return True
        except:
            self.speak(f"Could not find {app_name}")
            return False
    
    def take_screenshot_with_options(self):
        """Enhanced screenshot with options"""
        self.speak("Would you like full screen or selected area?")
        choice = self.get_voice_input()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        if 'area' in choice or 'selection' in choice:
            self.print_colored("📸 Select area to capture (you have 5 seconds)", 'yellow')
            time.sleep(5)
            screenshot = pyautogui.screenshot(region=pyautogui.locateOnScreen)
        else:
            screenshot = pyautogui.screenshot()
        
        screenshot.save(filename)
        self.speak(f"Screenshot saved as {filename}")
        
        # Option to open
        self.speak("Would you like to open the screenshot?")
        if self.listen_for_confirmation():
            os.startfile(filename)
    
    def system_optimization(self):
        """Perform system optimization"""
        self.print_colored("🔧 Starting system optimization...", 'yellow')
        self.speak("Performing system optimization. This may take a moment.")
        
        optimizations = []
        
        # Clear temp files
        temp_paths = [tempfile.gettempdir(), os.path.expanduser("~\\AppData\\Local\\Temp")]
        cleared = 0
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                try:
                    for file in os.listdir(temp_path):
                        try:
                            file_path = os.path.join(temp_path, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                cleared += 1
                        except:
                            pass
                except:
                    pass
        optimizations.append(f"Cleared {cleared} temporary files")
        
        # Empty recycle bin
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            optimizations.append("Emptied recycle bin")
        except:
            pass
        
        # Clear clipboard
        try:
            import pyperclip
            pyperclip.copy('')
            optimizations.append("Cleared clipboard")
        except:
            pass
        
        # Memory optimization
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetProcessWorkingSetSize(-1, -1, -1)
            optimizations.append("Optimized memory usage")
        except:
            pass
        
        # Display results
        print("\033[92m" + "=" * 60 + "\033[0m")
        print("\033[93mOPTIMIZATION RESULTS:\033[0m")
        for opt in optimizations:
            print(f"  ✓ {opt}")
        print("\033[92m" + "=" * 60 + "\033[0m")
        
        self.speak(f"Optimization complete. {len(optimizations)} tasks performed.")
    
    def process_command(self, command):
        """Enhanced command processor"""
        if not command:
            return True
        
        self.session_commands += 1
        self.command_history.append(command)
        
        # ========== SYSTEM COMMANDS ==========
        if "dashboard" in command or "system dashboard" in command:
            self.show_dashboard()
        
        elif "system info" in command or "system information" in command:
            info = f"System: {self.system_data['system'].get('os', 'Unknown')}. "
            info += f"CPU: {self.system_data['system'].get('cpu_cores_physical', 'Unknown')} cores at {self.system_data['system'].get('cpu_frequency', 'Unknown')} MHz. "
            info += f"RAM: {self.system_data['system'].get('available_ram_gb', 0):.1f} GB available out of {self.system_data['system'].get('total_ram_gb', 0):.1f} GB. "
            self.speak(info)
        
        elif "drive info" in command or "disk info" in command:
            for drive, info in self.system_data['drives'].items():
                self.speak(f"Drive {drive}: {info['free_gb']:.1f} GB free of {info['total_gb']:.1f} GB")
        
        elif "optimize" in command or "cleanup" in command:
            self.system_optimization()
        
        # ========== APPLICATION COMMANDS ==========
        elif "list apps" in command or "show applications" in command:
            self.show_applications()
        
        elif "search app" in command or "find app" in command:
            self.speak("What application would you like to search for?")
            search_term = self.get_voice_input()
            if search_term:
                self.search_applications(search_term)
        
        elif "open" in command and len(command.split()) > 1:
            app_name = command.replace("open", "").strip()
            self.launch_application(app_name)
        
        # ========== MEDIA COMMANDS ==========
        elif "spotify" in command:
            self.launch_application("spotify")
        
        elif "pause" in command:
            keyboard.press_and_release('play/pause media')
            self.speak("Music paused")
        
        elif "next" in command:
            keyboard.press_and_release('next track')
            self.speak("Next track")
        
        elif "volume" in command:
            if "up" in command or "increase" in command:
                keyboard.press_and_release('volume up')
                self.speak("Volume increased")
            elif "down" in command or "decrease" in command:
                keyboard.press_and_release('volume down')
                self.speak("Volume decreased")
            elif "mute" in command:
                keyboard.press_and_release('volume mute')
                self.speak("Volume muted")
        
        # ========== UTILITY COMMANDS ==========
        elif "screenshot" in command:
            self.take_screenshot_with_options()
        
        elif "lock" in command:
            self.speak("Locking workstation")
            ctypes.windll.user32.LockWorkStation()
        
        elif "shutdown" in command:
            self.speak("Shutting down in 10 seconds. Say 'cancel' to stop.")
            for i in range(10, 0, -1):
                cmd = self.get_command()
                if cmd and ("cancel" in cmd or "stop" in cmd):
                    self.speak("Shutdown cancelled")
                    return True
                if i <= 3:
                    self.speak(str(i))
                time.sleep(1)
            os.system("shutdown /s /t 1")
            return False
        
        elif "restart" in command:
            self.speak("Restarting in 10 seconds. Say 'cancel' to stop.")
            for i in range(10, 0, -1):
                cmd = self.get_command()
                if cmd and ("cancel" in cmd or "stop" in cmd):
                    self.speak("Restart cancelled")
                    return True
                if i <= 3:
                    self.speak(str(i))
                time.sleep(1)
            os.system("shutdown /r /t 1")
            return False
        
        # ========== INFORMATION COMMANDS ==========
        elif "time" in command:
            current_time = datetime.now().strftime("%I:%M %p")
            self.speak(f"The time is {current_time}")
        
        elif "date" in command:
            current_date = datetime.now().strftime("%B %d, %Y")
            self.speak(f"Today is {current_date}")
        
        elif "weather" in command:
            self.speak("Which city?")
            city = self.get_voice_input()
            if city:
                try:
                    url = f"https://wttr.in/{city}?format=%C+%t+%w"
                    response = requests.get(url, timeout=5)
                    self.speak(f"Weather in {city}: {response.text.strip()}")
                except:
                    self.speak("Weather service unavailable")
        
        elif "joke" in command:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "What do you call a fake noodle? An impasta!",
                "Why did the math book look so sad? Because it had too many problems!",
                "What do you call a bear with no teeth? A gummy bear!"
            ]
            self.speak(random.choice(jokes))
        
        elif "quote" in command:
            quotes = [
                "The only limit to our realization of tomorrow is our doubts of today.",
                "Do what you can, with what you have, where you are.",
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "The future belongs to those who believe in the beauty of their dreams."
            ]
            self.speak(random.choice(quotes))
        
        # ========== SETTINGS ==========
        elif "wake word" in command:
            self.speak("What would you like the new wake word to be?")
            new_wake = self.get_voice_input()
            if new_wake:
                self.wake_word = new_wake
                self.settings['wake_word'] = new_wake
                self.save_settings()
                self.speak(f"Wake word changed to {new_wake}")
        
        # ========== HELP ==========
        elif "help" in command:
            self.show_help()
        
        # ========== EXIT ==========
        elif "exit" in command or "goodbye" in command or "quit" in command:
            self.speak(f"Goodbye! You processed {self.session_commands} commands this session. Have a great day!")
            return False
        
        # ========== FALLBACK ==========
        else:
            self.speak("I didn't understand that command. Say 'Help' for available commands")
        
        return True
    
    def show_help(self):
        """Show comprehensive help menu"""
        help_text = """
\033[96m╔═══════════════════════════════════════════════════════════════════════╗
║                         ULTIMATE JARVIS HELP MENU                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║ \033[93mSYSTEM CONTROL:\033[0m                                                       ║
║   • "Dashboard" - Show system dashboard                                  ║
║   • "System Info" - Display system information                           ║
║   • "Drive Info" - Show disk usage                                       ║
║   • "Optimize" - Perform system optimization                             ║
║   • "Lock" - Lock workstation                                            ║
║   • "Screenshot" - Take screenshot                                       ║
║                                                                          ║
║ \033[93mAPPLICATION MANAGEMENT:\033[0m                                                ║
║   • "Open [app]" - Launch any application                                ║
║   • "List Apps" - Show installed applications                            ║
║   • "Search App" - Find specific applications                            ║
║                                                                          ║
║ \033[93mMEDIA CONTROL:\033[0m                                                         ║
║   • "Open Spotify" - Launch Spotify                                      ║
║   • "Pause" - Pause music                                                ║
║   • "Next" - Next track                                                  ║
║   • "Volume Up/Down/Mute" - Volume control                               ║
║                                                                          ║
║ \033[93mINFORMATION:\033[0m                                                          ║
║   • "Time" - Current time                                                ║
║   • "Date" - Current date                                                ║
║   • "Weather" - Weather forecast                                         ║
║   • "Joke" - Tell a joke                                                 ║
║   • "Quote" - Inspirational quote                                        ║
║                                                                          ║
║ \033[93mSETTINGS:\033[0m                                                             ║
║   • "Change Wake Word" - Set new activation word                         ║
║                                                                          ║
║ \033[93mSYSTEM:\033[0m                                                               ║
║   • "Shutdown" - Shutdown computer                                       ║
║   • "Restart" - Restart computer                                         ║
║   • "Exit" - Close Jarvis                                                ║
║   • "Help" - Show this menu                                              ║
╚═══════════════════════════════════════════════════════════════════════╝\033[0m
        """
        print(help_text)
        self.speak("Help menu displayed")
    
    def run(self):
        """Main execution loop"""
        self.print_header()
        self.speak("Ultimate Jarvis assistant ready for command")
        
        while True:
            try:
                command = self.get_command()
                if command:
                    self.successful_commands += 1
                    should_continue = self.process_command(command)
                    if not should_continue:
                        break
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.print_colored("\n\n⚠️ Interrupt received", 'yellow')
                break
            except Exception as e:
                self.print_colored(f"Error: {e}", 'red')
                continue
        
        # Shutdown
        self.print_colored("\n" + "=" * 60, 'cyan')
        self.print_colored("SHUTTING DOWN ULTIMATE JARVIS".center(60), 'magenta')
        self.print_colored("=" * 60, 'cyan')
        self.print_colored(f"Session Statistics:".center(60), 'yellow')
        self.print_colored(f"Commands Processed: {self.session_commands}".center(60), 'green')
        self.print_colored(f"Session Duration: {str(datetime.now() - self.start_time).split('.')[0]}".center(60), 'green')
        self.print_colored("Thank you for using Ultimate Jarvis!".center(60), 'magenta')
        print()

# ==================== MAIN ====================
if __name__ == "__main__":
    # Ensure required packages
    required_packages = [
        'speechrecognition', 'pyttsx3', 'psutil', 'pyautogui',
        'keyboard', 'requests', 'pyperclip', 'wmi', 'pypiwin32'
    ]
    
    print("🔧 Checking and installing dependencies...")
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\n✅ All dependencies ready!\n")
    
    try:
        jarvis = UltimateJarvis()
        jarvis.run()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        input("\nPress Enter to exit...")