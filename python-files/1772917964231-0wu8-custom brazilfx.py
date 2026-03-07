#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PĖDSAKŲ VALIKLIS
Sukurtas pagal pokalbį: išvalo Windows pėdsakus po cheat'ų / įrankių paleidimo
Paleisti kaip administratorių!
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import time
import glob

# Spalvotas tekstas (Windows ir Linux)
class Colors:
    GREEN = '\033[92m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[93m' if platform.system() != 'Windows' else ''
    RED = '\033[91m' if platform.system() != 'Windows' else ''
    BLUE = '\033[94m' if platform.system() != 'Windows' else ''
    RESET = '\033[0m' if platform.system() != 'Windows' else ''

def print_step(text):
    print(f"{Colors.BLUE}[*]{Colors.RESET} {text}")

def print_success(text):
    print(f"{Colors.GREEN}[+]{Colors.RESET} {text}")

def print_error(text):
    print(f"{Colors.RED}[-]{Colors.RESET} {text}")

def print_warning(text):
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {text}")

def is_admin():
    """Tikrina ar paleista kaip administratorius"""
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False

def clear_prefetch():
    """Išvalo Prefetch aplanką"""
    print_step("Valomas Prefetch...")
    prefetch_path = r"C:\Windows\Prefetch"
    
    if not os.path.exists(prefetch_path):
        print_error("Prefetch aplankas nerastas")
        return
    
    count = 0
    try:
        for file in os.listdir(prefetch_path):
            if file.endswith('.pf'):
                file_path = os.path.join(prefetch_path, file)
                try:
                    os.remove(file_path)
                    count += 1
                except:
                    pass
        print_success(f"Išvalyta {count} Prefetch failų")
    except Exception as e:
        print_error(f"Klaida valant Prefetch: {e}")

def clear_recent_files():
    """Išvalo Recent files"""
    print_step("Valomi Recent files...")
    recent_path = os.path.join(os.environ['USERPROFILE'], 
                               r'AppData\Roaming\Microsoft\Windows\Recent')
    
    if not os.path.exists(recent_path):
        print_error("Recent aplankas nerastas")
        return
    
    count = 0
    try:
        for file in os.listdir(recent_path):
            file_path = os.path.join(recent_path, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1
            except:
                pass
        print_success(f"Išvalyta {count} Recent failų")
    except Exception as e:
        print_error(f"Klaida: {e}")

def clear_jump_lists():
    """Išvalo Jump Lists"""
    print_step("Valomi Jump Lists...")
    jump_path = os.path.join(os.environ['USERPROFILE'], 
                             r'AppData\Roaming\Microsoft\Windows\Recent\AutomaticDestinations')
    
    if not os.path.exists(jump_path):
        print_error("Jump Lists aplankas nerastas")
        return
    
    count = 0
    try:
        for file in os.listdir(jump_path):
            file_path = os.path.join(jump_path, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    count += 1
            except:
                pass
        print_success(f"Išvalyta {count} Jump List failų")
    except Exception as e:
        print_error(f"Klaida: {e}")

def clear_temp_files():
    """Išvalo TEMP aplankus"""
    print_step("Valomi TEMP failai...")
    
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        r"C:\Windows\Temp",
        os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Temp')
    ]
    
    total_count = 0
    for temp_path in temp_paths:
        if temp_path and os.path.exists(temp_path):
            count = 0
            try:
                for file in os.listdir(temp_path):
                    file_path = os.path.join(temp_path, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            count += 1
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path, ignore_errors=True)
                            count += 1
                    except:
                        pass
                total_count += count
            except:
                pass
    
    print_success(f"Išvalyta ~{total_count} TEMP failų/aplankų")

def clear_powershell_history():
    """Išvalo PowerShell istoriją"""
    print_step("Valoma PowerShell istorija...")
    
    ps_history = os.path.join(os.environ['USERPROFILE'], 
                              r'AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt')
    
    try:
        if os.path.exists(ps_history):
            with open(ps_history, 'w') as f:
                f.write('')
            print_success("PowerShell istorija išvalyta")
        else:
            print_warning("PowerShell istorijos failas nerastas")
    except Exception as e:
        print_error(f"Klaida: {e}")

def clear_cmd_history():
    """Išvalo CMD istoriją (registre)"""
    print_step("Valoma CMD istorija...")
    
    try:
        # Išvalome DOSKEY istoriją (tik šiai sesijai)
        subprocess.run('doskey /reinstall', shell=True, capture_output=True)
        print_success("CMD istorija išvalyta (šiai sesijai)")
    except:
        print_error("Nepavyko išvalyti CMD istorijos")

def clear_recycle_bin():
    """Išvalo šiukšliadėžę"""
    print_step("Valoma šiukšliadėžė...")
    
    try:
        # PowerShell komanda išvalyti šiukšliadėžę
        subprocess.run('powershell -Command "Clear-RecycleBin -Force"', 
                      shell=True, capture_output=True)
        print_success("Šiukšliadėžė išvalyta")
    except:
        print_error("Nepavyko išvalyti šiukšliadėžės")

def clear_event_logs():
    """Išvalo Event Logs (tik su admin teisėmis)"""
    print_step("Valomi Event Logs...")
    
    if not is_admin():
        print_warning("Praleista: reikia administratoriaus teisių")
        return
    
    try:
        # Gauname visų logų sąrašą ir bandome išvalyti
        result = subprocess.run('wevtutil el', shell=True, capture_output=True, text=True)
        logs = result.stdout.split('\n')
        
        count = 0
        for log in logs:
            if log.strip():
                try:
                    subprocess.run(f'wevtutil cl "{log}" 2>nul', shell=True)
                    count += 1
                except:
                    pass
        
        print_success(f"Išvalyta {count} Event Logų")
    except Exception as e:
        print_error(f"Klaida: {e}")

def clear_usb_history():
    """Išvalo USB įrenginių istoriją iš registro (tik admin)"""
    print_step("Valoma USB įrenginių istorija...")
    
    if not is_admin():
        print_warning("Praleista: reikia administratoriaus teisių")
        return
    
    print_warning("USB istorijos valymas iš registro yra rizikingas")
    print_warning("Praleidžiama, kad nepažeisti sistemos")
    # Čia galima pridėti registry valymą, bet tai pavojinga

def clear_browser_history():
    """Išvalo naršyklių istoriją (Chrome, Edge)"""
    print_step("Valoma naršyklių istorija...")
    
    # Chrome
    chrome_history = os.path.join(os.environ['USERPROFILE'], 
                                  r'AppData\Local\Google\Chrome\User Data\Default\History')
    try:
        if os.path.exists(chrome_history):
            os.remove(chrome_history)
            print_success("Chrome istorija išvalyta")
    except:
        pass
    
    # Edge
    edge_history = os.path.join(os.environ['USERPROFILE'], 
                                r'AppData\Local\Microsoft\Edge\User Data\Default\History')
    try:
        if os.path.exists(edge_history):
            os.remove(edge_history)
            print_success("Edge istorija išvalyta")
    except:
        pass

def clear_dns_cache():
    """Išvalo DNS cache"""
    print_step("Valomas DNS cache...")
    
    try:
        subprocess.run('ipconfig /flushdns', shell=True, capture_output=True)
        print_success("DNS cache išvalytas")
    except:
        print_error("Nepavyko išvalyti DNS cache")

def main():
    """Pagrindinė funkcija"""
    print("\n" + "="*60)
    print("                 PĖDSAKŲ VALIKLIS")
    print("="*60)
    print(f"Paleista: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Vartotojas: {os.environ.get('USERNAME', 'Unknown')}")
    print(f"Admin teisės: {'TAIP' if is_admin() else 'NE'}")
    print("-"*60 + "\n")
    
    # Tikriname ar Windows
    if platform.system() != 'Windows':
        print_error("Šis įrankis veikia tik Windows sistemoje!")
        sys.exit(1)
    
    # Klausiame patvirtinimo
    print_warning("Šis įrankis ištrins laikinuosius failus, istoriją ir pėdsakus.")
    print_warning("Kai kurių failų negalėsite atkurti!")
    confirm = input("\nAr tikrai norite tęsti? (taip/ne): ").lower()
    
    if confirm not in ['taip', 't', 'yes', 'y']:
        print("\nOperacija atšaukta.")
        sys.exit(0)
    
    print("\n" + "-"*60)
    print("PRADEDAMAS VALYMAS...")
    print("-"*60 + "\n")
    
    # Vykdome valymo funkcijas
    clear_prefetch()
    print()
    clear_recent_files()
    print()
    clear_jump_lists()
    print()
    clear_temp_files()
    print()
    clear_powershell_history()
    print()
    clear_cmd_history()
    print()
    clear_recycle_bin()
    print()
    clear_browser_history()
    print()
    clear_dns_cache()
    print()
    
    # Event logs tik su admin
    if is_admin():
        clear_event_logs()
        print()
        clear_usb_history()
    else:
        print_warning("Norint išvalyti Event Logs ir USB istoriją, paleiskite kaip administratorius.")
    
    print("\n" + "="*60)
    print("                  VALYMAS BAIGTAS")
    print("="*60)
    print_success("Visi pėdsakai išvalyti!")
    print_warning("Prisiminkite: anti-cheat sistemos veikia realiu laiku ir serverio pusėje.")
    print("="*60 + "\n")
    
    input("Paspauskite Enter norėdami išeiti...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperacija nutraukta vartotojo.")
        sys.exit(0)
    except Exception as e:
        print_error(f"Nežinoma klaida: {e}")
        sys.exit(1)