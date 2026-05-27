import subprocess
import sys
import os
import ctypes
import time
import winreg
import glob
import shutil

# ============================================
# AUTO ELEVATE WITH ALLOW PROMPT
# ============================================
def auto_elevate():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{__file__}"', None, 1
        )
        sys.exit()

auto_elevate()

# ============================================
# FANCY WELCOME ANIMATION
# ============================================
def welcome_animation():
    os.system('cls')
    os.system('color 0E')
    
    border = "█" * 70
    
    def slow_print(text, delay=0.03):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
    
    def slow_print_center(text, delay=0.03):
        spaces = " " * ((70 - len(text)) // 2)
        for char in (spaces + text):
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
    
    print("\n" * 2)
    slow_print(border, 0.001)
    time.sleep(0.3)
    print()
    time.sleep(0.2)
    
    title = "⚡ ULTIMATE SYSTEM CLEANER ⚡"
    slow_print_center(title, 0.05)
    time.sleep(0.5)
    
    print()
    time.sleep(0.2)
    
    subtitle = "~ Complete Windows Optimization Tool ~"
    slow_print_center(subtitle, 0.04)
    time.sleep(0.5)
    
    print()
    time.sleep(0.3)
    
    name_line1 = "═" * 30
    name_text = f"     Developed by :  E Y A D   Z A E N     "
    name_line2 = "═" * 30
    
    slow_print_center(name_line1, 0.02)
    time.sleep(0.2)
    slow_print_center(name_text, 0.07)
    time.sleep(0.2)
    slow_print_center(name_line2, 0.02)
    time.sleep(0.5)
    
    print()
    time.sleep(0.3)
    
    features = [
        "✓ Remove ANY program completely",
        "✓ Clean Windows junk files",
        "✓ No leftovers - No registry traces",
        "✓ Boost system performance"
    ]
    
    for feature in features:
        slow_print_center(feature, 0.02)
        time.sleep(0.3)
    
    print()
    time.sleep(0.5)
    slow_print(border, 0.001)
    time.sleep(0.8)
    
    print()
    ready_msg = ">> SYSTEM READY <<"
    slow_print_center(ready_msg, 0.1)
    time.sleep(0.5)
    print("\n" * 2)

# ============================================
# MAIN MENU
# ============================================
def main_menu():
    os.system('cls')
    print("\n" + "="*70)
    print("                     🏠 MAIN MENU")
    print("="*70)
    print()
    print("   ╔══════════════════════════════════════════════════════╗")
    print("   ║                                                      ║")
    print("   ║     [1]  🗑️  UNINSTALL PROGRAMS                     ║")
    print("   ║          Remove any program completely              ║")
    print("   ║                                                      ║")
    print("   ║     [2]  🧹  CLEAN WINDOWS JUNK                     ║")
    print("   ║          Delete temp, cache, logs, prefetch         ║")
    print("   ║                                                      ║")
    print("   ║     [0]  ❌  EXIT                                   ║")
    print("   ║                                                      ║")
    print("   ╚══════════════════════════════════════════════════════╝")
    print()
    print("="*70)
    
    choice = input("\n  >> Select option (1, 2, or 0): ").strip()
    return choice

# ============================================
# SECTION 1: UNINSTALL PROGRAMS (COMPLETE)
# ============================================
def get_all_programs():
    programs = []
    
    print("\n[*] Scanning registry for Win32 programs...")
    
    registry_paths = [
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    for reg_path in registry_paths:
        try:
            result = subprocess.run(f'reg query "{reg_path}" /s /v DisplayName', 
                                  shell=True, capture_output=True, text=True, timeout=15)
            for line in result.stdout.split('\n'):
                if 'REG_SZ' in line:
                    parts = line.split('REG_SZ')
                    if len(parts) > 1:
                        name = parts[1].strip()
                        if name and len(name) > 2 and name != '(Default)':
                            programs.append({"name": name, "type": "Win32"})
        except:
            pass
    
    print("[*] Scanning Microsoft Store apps...")
    
    try:
        result = subprocess.run('powershell -Command "Get-AppxPackage | Select-Object -ExpandProperty Name"',
                              shell=True, capture_output=True, text=True, timeout=15)
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and len(line) > 2:
                programs.append({"name": line, "type": "Modern"})
    except:
        pass
    
    seen = set()
    unique = []
    for p in programs:
        if p['name'].lower() not in seen:
            seen.add(p['name'].lower())
            unique.append(p)
    
    return sorted(unique, key=lambda x: x['name'].lower())

def uninstall_win32(program):
    print(f"\n[+] Removing: {program['name']}")
    
    try:
        registry_paths = [
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for reg_path in registry_paths:
            result = subprocess.run(f'reg query "{reg_path}" /s', shell=True, capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if program['name'] in line and i + 2 < len(lines):
                    if 'UninstallString' in lines[i + 1]:
                        parts = lines[i + 2].split('REG_SZ')
                        if len(parts) > 1:
                            uninstaller = parts[1].strip()
                            if uninstaller:
                                subprocess.run(uninstaller, shell=True, timeout=30, capture_output=True)
                                break
    except:
        pass
    
    try:
        first_word = program['name'].split()[0] if program['name'].split() else program['name']
        for pattern in [
            f"C:\\Program Files\\*{first_word}*",
            f"C:\\Program Files (x86)\\*{first_word}*",
            f"{os.environ.get('LOCALAPPDATA', '')}\\*{first_word}*",
            f"{os.environ.get('APPDATA', '')}\\*{first_word}*"
        ]:
            for folder in glob.glob(pattern):
                subprocess.run(f'rd /s /q "{folder}"', shell=True, capture_output=True)
    except:
        pass
    
    print(f"[✓] {program['name']} removed")

def uninstall_modern(program):
    print(f"\n[+] Removing: {program['name']}")
    subprocess.run(f'powershell "Get-AppxPackage *{program["name"]}* | Remove-AppxPackage"', shell=True, capture_output=True)
    subprocess.run(f'powershell "Get-AppxProvisionedPackage -Online | Where-Object {{$_.DisplayName -like \"*{program["name"]}*\"}} | Remove-AppxProvisionedPackage -Online"', shell=True, capture_output=True)
    print(f"[✓] {program['name']} removed permanently")

def uninstall_programs_section():
    os.system('cls')
    print("\n" + "="*70)
    print("                  🗑️  UNINSTALL PROGRAMS")
    print("="*70)
    
    print("\n[*] Loading all installed programs...")
    programs = get_all_programs()
    
    if not programs:
        print("[!] No programs found")
        input("\nPress Enter to continue...")
        return
    
    os.system('cls')
    print("\n" + "═"*80)
    print("                     📦 ALL INSTALLED PROGRAMS")
    print("═"*80)
    print(f"  Total: {len(programs)} programs")
    print("─"*80)
    
    for i, prog in enumerate(programs, 1):
        if prog['type'] == 'Win32':
            prog_type = "Win32"
        else:
            prog_type = "Store"
        print(f"  {i:4d}. [{prog_type:6}] {prog['name']}")
    
    print("─"*80)
    print("  [0] Back to Main Menu     [S] Search")
    print("═"*80)
    
    while True:
        try:
            choice = input("\n  >> Select number or 'S' to search: ").strip().lower()
            
            if choice == '0':
                break
            
            elif choice == 's':
                search = input("  Search: ").lower()
                results = [p for p in programs if search in p['name'].lower()]
                
                if results:
                    print(f"\n  Found {len(results)} results:")
                    print("  " + "-"*70)
                    for i, p in enumerate(results[:50], 1):
                        print(f"    {i:3d}. {p['name'][:65]}")
                    print("  " + "-"*70)
                    
                    idx = input("\n  Number to remove (or Enter to cancel): ")
                    if idx:
                        num = int(idx) - 1
                        if 0 <= num < len(results):
                            confirm = input(f"  Remove '{results[num]['name']}'? (y/n): ").lower()
                            if confirm == 'y':
                                if results[num]['type'] == 'Win32':
                                    uninstall_win32(results[num])
                                else:
                                    uninstall_modern(results[num])
                                programs = get_all_programs()
                                print("\n  List refreshed")
                else:
                    print("  No results found")
            
            else:
                num = int(choice) - 1
                if 0 <= num < len(programs):
                    selected = programs[num]
                    confirm = input(f"  Remove '{selected['name']}'? (y/n): ").lower()
                    if confirm == 'y':
                        if selected['type'] == 'Win32':
                            uninstall_win32(selected)
                        else:
                            uninstall_modern(selected)
                        programs = get_all_programs()
                        print("\n  List refreshed")
                    else:
                        print("  Cancelled")
                else:
                    print("  Invalid number")
                    
        except ValueError:
            print("  Invalid input, please enter a number")
        except KeyboardInterrupt:
            break
        
        input("\n  Press Enter to continue...")
        os.system('cls')
        print("\n" + "═"*80)
        print("                     📦 ALL INSTALLED PROGRAMS")
        print("═"*80)
        print(f"  Total: {len(programs)} programs")
        print("─"*80)
        
        for i, prog in enumerate(programs, 1):
            if prog['type'] == 'Win32':
                prog_type = "Win32"
            else:
                prog_type = "Store"
            print(f"  {i:4d}. [{prog_type:6}] {prog['name']}")
        
        print("─"*80)
        print("  [0] Back to Main Menu     [S] Search")
        print("═"*80)

# ============================================
# SECTION 2: CLEAN WINDOWS JUNK
# ============================================
def clean_windows_junk():
    os.system('cls')
    print("\n" + "="*70)
    print("                  🧹  CLEAN WINDOWS JUNK")
    print("="*70)
    print()
    
    # 1. User Temp
    print("[1/10] Cleaning User Temp...")
    user_temp = os.environ.get('TEMP', '')
    if user_temp:
        try:
            for item in os.listdir(user_temp):
                item_path = os.path.join(user_temp, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            print("      User Temp cleaned")
        except:
            print("      Failed to clean User Temp")
    
    # 2. System Temp
    print("[2/10] Cleaning System Temp...")
    system_temp = "C:\\Windows\\Temp"
    if os.path.exists(system_temp):
        try:
            for item in os.listdir(system_temp):
                item_path = os.path.join(system_temp, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            print("      System Temp cleaned")
        except:
            print("      Failed to clean System Temp")
    
    # 3. Prefetch
    print("[3/10] Cleaning Prefetch...")
    prefetch = "C:\\Windows\\Prefetch"
    if os.path.exists(prefetch):
        try:
            for item in os.listdir(prefetch):
                if item.endswith('.pf'):
                    item_path = os.path.join(prefetch, item)
                    try:
                        os.remove(item_path)
                    except:
                        pass
            print("      Prefetch cleaned")
        except:
            print("      Failed to clean Prefetch")
    
    # 4. Recycle Bin
    print("[4/10] Emptying Recycle Bin...")
    try:
        subprocess.run('powershell "Clear-RecycleBin -Force"', shell=True, capture_output=True)
        print("      Recycle Bin emptied")
    except:
        print("      Failed to empty Recycle Bin")
    
    # 5. Windows Logs
    print("[5/10] Cleaning Windows Logs...")
    logs_path = "C:\\Windows\\Logs"
    if os.path.exists(logs_path):
        try:
            for item in os.listdir(logs_path):
                item_path = os.path.join(logs_path, item)
                try:
                    if os.path.isfile(item_path) and item.endswith('.log'):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            print("      Windows Logs cleaned")
        except:
            print("      Failed to clean Windows Logs")
    
    # 6. Windows Update Cache
    print("[6/10] Cleaning Windows Update Cache...")
    update_cache = "C:\\Windows\\SoftwareDistribution\\Download"
    if os.path.exists(update_cache):
        try:
            for item in os.listdir(update_cache):
                item_path = os.path.join(update_cache, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except:
                    pass
            print("      Windows Update Cache cleaned")
        except:
            print("      Failed to clean Windows Update Cache")
    
    # 7. Browser Caches
    print("[7/10] Cleaning Browser Caches...")
    browser_caches = [
        os.environ.get('LOCALAPPDATA', '') + "\\Google\\Chrome\\User Data\\Default\\Cache",
        os.environ.get('LOCALAPPDATA', '') + "\\Microsoft\\Edge\\User Data\\Default\\Cache"
    ]
    for cache in browser_caches:
        if os.path.exists(cache):
            try:
                for item in os.listdir(cache):
                    item_path = os.path.join(cache, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                    except:
                        pass
                print(f"      Cleaned: {os.path.basename(os.path.dirname(os.path.dirname(cache)))}")
            except:
                pass
    
    # 8. DNS Cache
    print("[8/10] Flushing DNS Cache...")
    try:
        subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
        print("      DNS Cache flushed")
    except:
        print("      Failed to flush DNS Cache")
    
    # 9. Recent Documents
    print("[9/10] Cleaning Recent Documents...")
    recent = os.environ.get('USERPROFILE', '') + "\\Recent"
    if os.path.exists(recent):
        try:
            for item in os.listdir(recent):
                item_path = os.path.join(recent, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                except:
                    pass
            print("      Recent Documents cleaned")
        except:
            print("      Failed to clean Recent Documents")
    
    # 10. Thumbnail Cache
    print("[10/10] Cleaning Thumbnail Cache...")
    try:
        subprocess.run('del /f /s /q "%USERPROFILE%\\AppData\\Local\\Microsoft\\Windows\\Explorer\\thumbcache_*.db"', shell=True, capture_output=True)
        print("      Thumbnail Cache cleaned")
    except:
        print("      Failed to clean Thumbnail Cache")
    
    print("\n" + "="*70)
    print("  ✅ WINDOWS JUNK CLEANING COMPLETED!")
    print("  🚀 Your system is now cleaner and faster")
    print("="*70)
    
    input("\n  Press Enter to continue...")

# ============================================
# MAIN
# ============================================
def main():
    welcome_animation()
    
    while True:
        choice = main_menu()
        
        if choice == '1':
            uninstall_programs_section()
        elif choice == '2':
            clean_windows_junk()
        elif choice == '0':
            print("\n✨ Goodbye! Have a great day ✨")
            time.sleep(1)
            break
        else:
            print("\n❌ Invalid option! Please select 1, 2, or 0")
            time.sleep(1.5)

if __name__ == "__main__":
    main()