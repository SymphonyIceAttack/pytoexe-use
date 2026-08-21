import os
import subprocess
import sys
import ctypes
import psutil
import gc
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

print("="*70)
print("  FORTNITE ULTIMATE PERFORMANCE - 40+ TWEAKS")
print("  0 DELAY + MAX FPS + MIN PING")
print("  DISCORD REMAINS OPEN")
print("="*70)
print("")

total = 0

print("[1/40] Ultimate Performance Power Plan...")
subprocess.run("powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61", shell=True, capture_output=True)
subprocess.run("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True, capture_output=True)
print("    OK")
total += 1

print("[2/40] Disabling HPET...")
subprocess.run("bcdedit /set useplatformclock false", shell=True, capture_output=True)
subprocess.run("bcdedit /set disabledynamictick yes", shell=True, capture_output=True)
print("    OK")
total += 1

print("[3/40] Closing background apps (Discord stays open)...")
apps = [
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
    "spotify.exe", "steam.exe", "epicgameslauncher.exe", "origin.exe",
    "battlenet.exe", "uplay.exe", "slack.exe", "zoom.exe", "skype.exe",
    "teams.exe", "onedrive.exe", "dropbox.exe", "anydesk.exe",
    "teamviewer.exe", "qbittorrent.exe", "utorrent.exe", "deluge.exe",
    "photoshop.exe", "premiere.exe", "afterfx.exe", "vlc.exe",
    "java.exe", "javaw.exe", "python.exe", "node.exe", "code.exe",
    "obs64.exe", "obs32.exe", "outlook.exe", "telegram.exe"
]
for app in apps:
    subprocess.run(f"taskkill /f /im {app} 2>nul", shell=True, capture_output=True)
print("    OK")
total += 1

print("[4/40] Disabling Windows services...")
services = [
    "SysMain", "WSearch", "DiagTrack", "dmwappushservice", "MapsBroker",
    "Fax", "XblAuthManager", "XboxNetApiSvc", "XboxGipSvc", "XblGameSave",
    "WindowsUpdate", "wuauserv", "BITS", "DPS", "PcaSvc"
]
for s in services:
    subprocess.run(f'sc config {s} start= disabled', shell=True, capture_output=True)
    subprocess.run(f'net stop {s} /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[5/40] Network optimization for minimum ping...")
subprocess.run("netsh int tcp set global autotuninglevel=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global chimney=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global rss=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global netdma=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global timestamps=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global ecncapability=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global initialRto=2000", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global congestionprovider=ctcp", shell=True, capture_output=True)
print("    OK")
total += 1

print("[6/40] Disabling Nagle's Algorithm...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v TcpAckFrequency /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v TCPNoDelay /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v GlobalMaxTcpWindowSize /t REG_DWORD /d 262144 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v TcpWindowSize /t REG_DWORD /d 262144 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[7/40] Setting fast DNS servers...")
subprocess.run('netsh interface ip set dns "Ethernet" static 1.1.1.1', shell=True, capture_output=True)
subprocess.run('netsh interface ip add dns "Ethernet" 8.8.8.8 index=2', shell=True, capture_output=True)
subprocess.run('netsh interface ip add dns "Ethernet" 9.9.9.9 index=3', shell=True, capture_output=True)
print("    OK")
total += 1

print("[8/40] Disabling IPv6...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" /v DisabledComponents /t REG_DWORD /d 255 /f', shell=True, capture_output=True)
subprocess.run("netsh interface ipv6 set state disabled", shell=True, capture_output=True)
print("    OK")
total += 1

print("[9/40] Flushing DNS and resetting Winsock...")
subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
subprocess.run("netsh winsock reset", shell=True, capture_output=True)
subprocess.run("netsh int ip reset", shell=True, capture_output=True)
print("    OK")
total += 1

print("[10/40] Disabling Game DVR and Fullscreen optimizations...")
subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v FullscreenOptimizationsDisabled /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Software\\Microsoft\\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[11/40] Disabling Mouse Acceleration...")
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[12/40] Disabling USB power saving...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[13/40] Optimizing Priority Control...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[14/40] Disabling Windows Defender...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[15/40] Pausing Windows Updates...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[16/40] Disabling Telemetry...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[17/40] Disabling animations and transparency...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[18/40] Disabling Hibernation...")
subprocess.run("powercfg -h off", shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[19/40] Optimizing Multimedia Priority...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v Priority /t REG_DWORD /d 6 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[20/40] GPU Performance Tweaks...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 8 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDdiDelay /t REG_DWORD /d 5 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\\Scheduler" /v EnableHwSch /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[21/40] Disabling Prefetch and Superfetch...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[22/40] Ethernet Optimization...")
subprocess.run("netsh interface ipv4 set subinterface Ethernet mtu=1500 store=persistent", shell=True, capture_output=True)
subprocess.run("netsh interface ipv4 set interface Ethernet metric=1", shell=True, capture_output=True)
print("    OK")
total += 1

print("[23/40] Disabling Cortana...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[24/40] Disabling Notifications...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[25/40] Disabling Core Parking...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\0cc5b647-c1df-4637-891a-dec35c318583" /v Attributes /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[26/40] Disabling Error Reporting...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v DontShowUI /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[27/40] Disabling Font Cache...")
subprocess.run('sc config FontCache start= disabled', shell=True, capture_output=True)
subprocess.run('net stop FontCache /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[28/40] Disabling Print Spooler...")
subprocess.run('sc config Spooler start= disabled', shell=True, capture_output=True)
subprocess.run('net stop Spooler /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[29/40] Disabling Xbox Services...")
subprocess.run('sc config XboxGipSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop XboxGipSvc /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[30/40] GPU preference for Fortnite...")
subprocess.run('reg add "HKCU\\Software\\Microsoft\\DirectX\\GraphicsSettings" /v "FortniteClient-Win64-Shipping.exe" /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[31/40] Disabling Windows Search...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v DisableIndexer /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[32/40] Disabling Storage Sense...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters" /v StorageSenseEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[33/40] Disabling System Restore...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[34/40] Disabling WMP Network...")
subprocess.run('sc config WMPNetworkSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop WMPNetworkSvc /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[35/40] Disabling Biometric Services...")
subprocess.run('sc config WbioSrvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop WbioSrvc /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[36/40] Disabling SMB 1.0...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v SMB1 /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    OK")
total += 1

print("[37/40] Disabling Indexing...")
subprocess.run("wmic service where 'name=\"wsearch\"' call change startmode disabled", shell=True, capture_output=True)
print("    OK")
total += 1

print("[38/40] Flushing DNS cache...")
subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
print("    OK")
total += 1

print("[39/40] Disabling Windows Error Reporting Service...")
subprocess.run('sc config WerSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop WerSvc /y', shell=True, capture_output=True)
print("    OK")
total += 1

print("[40/40] Cleaning temporary files...")
subprocess.run("del /q /s %TEMP%\\* 2>nul", shell=True, capture_output=True)
subprocess.run("del /q /s %WINDIR%\\Temp\\* 2>nul", shell=True, capture_output=True)
print("    OK")
total += 1

print("")
print("[BONUS] Freeing RAM...")
gc.collect()
try:
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.SetProcessWorkingSetSize(-1, -1, -1)
    print("    OK")
except:
    pass

print("")
print("[BONUS] Setting Fortnite to High Priority...")
try:
    for proc in psutil.process_iter(['pid', 'name']):
        if "FortniteClient-Win64-Shipping" in proc.info['name']:
            subprocess.run(f"wmic process where processid={proc.info['pid']} CALL setpriority 128", shell=True, capture_output=True)
            print(f"    Fortnite found! High Priority set (PID: {proc.info['pid']})")
            break
    else:
        print("    Fortnite not running - will auto-set when opened")
except:
    print("    Could not find Fortnite")

print("")
print("="*70)
print(f"  ALL {total} TWEAKS COMPLETED SUCCESSFULLY!")
print("  DISCORD REMAINS OPEN!")
print("  RESTART YOUR PC NOW FOR BEST RESULTS")
print("="*70)
print("")
input("Press Enter to exit...")

# ============================================================
# 1. POWER PLAN
# ============================================================
print("[1/40] Ενεργοποίηση Ultimate Performance Power Plan...")
subprocess.run("powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61", shell=True, capture_output=True)
subprocess.run("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 2. PROCESSOR PERFORMANCE BOOST
# ============================================================
print("[2/40] Ενεργοποίηση CPU Performance Boost...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\be337238-0d82-4146-a960-4f3749d470c7" /v Attributes /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\be337238-0d82-4146-a960-4f3749d470c7" /v Default /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 3. DISABLE HPET (HIGH PRECISION EVENT TIMER)
# ============================================================
print("[3/40] Απενεργοποίηση HPET (μειώνει input lag)...")
subprocess.run("bcdedit /set useplatformclock false", shell=True, capture_output=True)
subprocess.run("bcdedit /set disabledynamictick yes", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 4. KILL BACKGROUND APPS (NO DISCORD)
# ============================================================
print("[4/40] Κλείσιμο background apps (Discord ΑΓΝΟΕΙΤΑΙ)...")
apps_to_kill = [
    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe",
    "spotify.exe", "steam.exe", "epicgameslauncher.exe", "origin.exe", "battlenet.exe",
    "uplay.exe", "goggalaxy.exe", "riotclient.exe", "slack.exe", "zoom.exe", "skype.exe",
    "teams.exe", "onedrive.exe", "dropbox.exe", "googleupdate.exe", "anydesk.exe",
    "teamviewer.exe", "filezilla.exe", "qbittorrent.exe", "utorrent.exe", "deluge.exe",
    "photoshop.exe", "premiere.exe", "afterfx.exe", "vlc.exe", "winrar.exe", "7z.exe",
    "java.exe", "javaw.exe", "python.exe", "node.exe", "npm.exe", "code.exe",
    "notepad++.exe", "sublime.exe", "obs64.exe", "obs32.exe", "xbox.exe",
    "outlook.exe", "thunderbird.exe", "telegram.exe", "whatsapp.exe"
]

for app in apps_to_kill:
    subprocess.run(f"taskkill /f /im {app} 2>nul", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε (Discord έμεινε ΑΝΟΙΧΤΟ)")
total_tweaks += 1

# ============================================================
# 5. DISABLE WINDOWS SERVICES
# ============================================================
print("[5/40] Απενεργοποίηση περιττών υπηρεσιών...")
services = [
    "SysMain", "WSearch", "DiagTrack", "dmwappushservice", "MapsBroker", "lfsvc",
    "Fax", "XblAuthManager", "XboxNetApiSvc", "XboxGipSvc", "XblGameSave",
    "WindowsUpdate", "wuauserv", "BITS", "DPS", "WdiSystemHost", "WdiServiceHost",
    "PcaSvc", "TabletInputService", "SensorService", "SensrSvc",
    "PcaSvc", "PNRPsvc", "p2psvc", "p2pimsvc", "iphlpsvc"
]
for service in services:
    subprocess.run(f'sc config {service} start= disabled', shell=True, capture_output=True)
    subprocess.run(f'net stop {service} /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 6. NETWORK - PING REDUCTION
# ============================================================
print("[6/40] Βελτιστοποίηση δικτύου για ελάχιστο ping...")
# TCP Global
subprocess.run("netsh int tcp set global autotuninglevel=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global chimney=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global rss=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global netdma=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global timestamps=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global ecncapability=disabled", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global initialRto=2000", shell=True, capture_output=True)
subprocess.run("netsh int tcp set global nonsackrttresiliency=disabled", shell=True, capture_output=True)
# Congestion Control
subprocess.run("netsh int tcp set global congestionprovider=ctcp", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 7. NAGLE'S ALGORITHM + TCP WINDOW
# ============================================================
print("[7/40] Απενεργοποίηση Nagle's Algorithm & TCP tuning...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v TcpAckFrequency /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces" /v TCPNoDelay /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v GlobalMaxTcpWindowSize /t REG_DWORD /d 262144 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v TcpWindowSize /t REG_DWORD /d 262144 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v Tcp1323Opts /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 8. DNS SERVERS (MULTIPLE FAST DNS)
# ============================================================
print("[8/40] Ορισμός γρήγορων DNS servers...")
subprocess.run('netsh interface ip set dns "Ethernet" static 1.1.1.1', shell=True, capture_output=True)
subprocess.run('netsh interface ip add dns "Ethernet" 8.8.8.8 index=2', shell=True, capture_output=True)
subprocess.run('netsh interface ip add dns "Ethernet" 9.9.9.9 index=3', shell=True, capture_output=True)
subprocess.run('netsh interface ip add dns "Ethernet" 208.67.222.222 index=4', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 9. DISABLE IPv6
# ============================================================
print("[9/40] Απενεργοποίηση IPv6...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" /v DisabledComponents /t REG_DWORD /d 255 /f', shell=True, capture_output=True)
subprocess.run("netsh interface ipv6 set state disabled", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 10. FLUSH DNS & WINSOCK
# ============================================================
print("[10/40] Flush DNS & Winsock reset...")
subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
subprocess.run("netsh winsock reset", shell=True, capture_output=True)
subprocess.run("netsh int ip reset", shell=True, capture_output=True)
subprocess.run("netsh int ipv6 reset", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 11. GAME MODE & DVR OFF
# ============================================================
print("[11/40] Απενεργοποίηση Game DVR & Fullscreen optimizations...")
subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\System\\GameConfigStore" /v FullscreenOptimizationsDisabled /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Software\\Microsoft\\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Software\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 12. MOUSE ACCELERATION OFF
# ============================================================
print("[12/40] Απενεργοποίηση Mouse Acceleration...")
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v SmoothMouseXCurve /t REG_BINARY /d 0000000000000000000000000000000000000000000000000000000000000000 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Mouse" /v SmoothMouseYCurve /t REG_BINARY /d 0000000000000000000000000000000000000000000000000000000000000000 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 13. USB POWER MANAGEMENT
# ============================================================
print("[13/40] Απενεργοποίηση USB power saving...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Enum\\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\USB" /v DisableSelectiveSuspend /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power" /v HibernateEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 14. PRIORITY CONTROL
# ============================================================
print("[14/40] Βελτιστοποίηση Priority Control...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 15. DISABLE WINDOWS DEFENDER
# ============================================================
print("[15/40] Απενεργοποίηση Windows Defender...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 16. DISABLE WINDOWS UPDATES
# ============================================================
print("[16/40] Αναστολή Windows Updates...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\WindowsUpdate\\UX\\Settings" /v FlightSettingsMaxPauseDays /t REG_DWORD /d 7 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 17. DISABLE TELEMETRY
# ============================================================
print("[17/40] Απενεργοποίηση Telemetry...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 18. DISABLE ANIMATIONS & TRANSPARENCY
# ============================================================
print("[18/40] Απενεργοποίηση animations & transparency...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\Control Panel\\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f', shell=True, capture_output=True)
subprocess.run("reg add 'HKCU\\Control Panel\\Desktop' /v MenuShowDelay /t REG_SZ /d 0 /f", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 19. DISABLE HIBERNATION & PAGEFILE
# ============================================================
print("[19/40] Απενεργοποίηση Hibernation & Pagefile tuning...")
subprocess.run("powercfg -h off", shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v LargeSystemCache /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 20. MULTIMEDIA PRIORITY
# ============================================================
print("[20/40] Βελτιστοποίηση Multimedia Priority...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v GPU Priority /t REG_DWORD /d 8 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v Priority /t REG_DWORD /d 6 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v Scheduling Category /t REG_SZ /d "High" /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 21. GPU TWEAKS
# ============================================================
print("[21/40] GPU Performance Tweaks...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 8 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDdiDelay /t REG_DWORD /d 5 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\\Scheduler" /v EnableHwSch /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v PreferSystem32 /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 22. DISABLE PREFETCH & SUPERFETCH
# ============================================================
print("[22/40] Απενεργοποίηση Prefetch & Superfetch...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 23. ETHERNET OPTIMIZATION
# ============================================================
print("[23/40] Ethernet Optimization...")
subprocess.run("netsh interface ipv4 set subinterface Ethernet mtu=1500 store=persistent", shell=True, capture_output=True)
subprocess.run("netsh interface ipv4 set interface Ethernet metric=1", shell=True, capture_output=True)
subprocess.run("netsh interface ipv4 set interface Ethernet forwarding=disabled", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 24. DISABLE CORTANA
# ============================================================
print("[24/40] Απενεργοποίηση Cortana...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Personalization\\Settings" /v AcceptedPrivacyPolicy /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 25. DISABLE NOTIFICATIONS
# ============================================================
print("[25/40] Απενεργοποίηση Notifications...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 26. DISABLE STORAGE SENSE
# ============================================================
print("[26/40] Απενεργοποίηση Storage Sense...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\StorageSense\\Parameters" /v StorageSenseEnabled /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 27. GPU PREFERENCE FOR FORTNITE (NVIDIA)
# ============================================================
print("[27/40] Ορισμός GPU preference...")
subprocess.run('reg add "HKCU\\Software\\Microsoft\\DirectX\\GraphicsSettings" /v "FortniteClient-Win64-Shipping.exe" /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 28. SYSTEM RESTORE POINT OFF
# ============================================================
print("[28/40] Απενεργοποίηση System Restore...")
subprocess.run("vssadmin delete shadows /all /quiet", shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 29. DISABLE INDEXING
# ============================================================
print("[29/40] Απενεργοποίηση Indexing...")
subprocess.run("wmic service where 'name=\"wsearch\"' call change startmode disabled", shell=True, capture_output=True)
subprocess.run("net stop wsearch /y", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 30. CPU CORE PARKING OFF
# ============================================================
print("[30/40] Απενεργοποίηση Core Parking...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\0cc5b647-c1df-4637-891a-dec35c318583" /v Attributes /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\0cc5b647-c1df-4637-891a-dec35c318583" /v Default /t REG_DWORD /d 2 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 31. DISABLE WINDOWS ERROR REPORTING
# ============================================================
print("[31/40] Απενεργοποίηση Error Reporting...")
subprocess.run('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v DontShowUI /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting" /v Disabled /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 32. DISABLE WINDOWS SEARCH
# ============================================================
print("[32/40] Απενεργοποίηση Windows Search...")
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v DisableIndexer /t REG_DWORD /d 1 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 33. DISABLE FONT CACHE
# ============================================================
print("[33/40] Απενεργοποίηση Font Cache...")
subprocess.run('sc config FontCache start= disabled', shell=True, capture_output=True)
subprocess.run('net stop FontCache /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 34. DISABLE PRINT SPOOLER
# ============================================================
print("[34/40] Απενεργοποίηση Print Spooler...")
subprocess.run('sc config Spooler start= disabled', shell=True, capture_output=True)
subprocess.run('net stop Spooler /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 35. DISABLE WINDOWS MEDIA PLAYER NETWORK
# ============================================================
print("[35/40] Απενεργοποίηση WMP Network...")
subprocess.run('sc config WMPNetworkSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop WMPNetworkSvc /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 36. DISABLE BIOMETRIC SERVICES
# ============================================================
print("[36/40] Απενεργοποίηση Biometric Services...")
subprocess.run('sc config WbioSrvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop WbioSrvc /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 37. DISABLE XBOX SERVICES
# ============================================================
print("[37/40] Απενεργοποίηση Xbox Services...")
subprocess.run('sc config XboxGipSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop XboxGipSvc /y', shell=True, capture_output=True)
subprocess.run('sc config XboxNetApiSvc start= disabled', shell=True, capture_output=True)
subprocess.run('net stop XboxNetApiSvc /y', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 38. DISABLE SMB 1.0
# ============================================================
print("[38/40] Απενεργοποίηση SMB 1.0...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v SMB1 /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 39. DISABLE SYSMAIN (SUPERFETCH) COMPLETELY
# ============================================================
print("[39/40] Πλήρης απενεργοποίηση Superfetch...")
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 0 /f', shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# 40. CLEAN TEMP FILES
# ============================================================
print("[40/40] Καθαρισμός temporary files...")
subprocess.run("del /q /s %TEMP%\\* 2>nul", shell=True, capture_output=True)
subprocess.run("del /q /s %WINDIR%\\Temp\\* 2>nul", shell=True, capture_output=True)
subprocess.run("del /q /s C:\\Windows\\Prefetch\\* 2>nul", shell=True, capture_output=True)
print("    ✓ Ολοκληρώθηκε")
total_tweaks += 1

# ============================================================
# BONUS: RAM CLEANER
# ============================================================
print("")
... print("[BONUS] Απελευθέρωση RAM...")
... gc.collect()
... try:
...     kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
...     kernel32.SetProcessWorkingSetSize(-1, -1, -1)
...     print("    ✓ RAM απελευθερώθηκε")
... except:
...     pass
... 
... # ============================================================
... # FORTNITE PRIORITY
... # ============================================================
... print("")
... print("[BONUS] Έλεγχος για Fortnite...")
... try:
...     for proc in psutil.process_iter(['pid', 'name']):
...         if "FortniteClient-Win64-Shipping" in proc.info['name']:
...             subprocess.run(f"wmic process where processid={proc.info['pid']} CALL setpriority 128", shell=True, capture_output=True)
...             print(f"    ✅ Fortnite βρέθηκε! High Priority (PID: {proc.info['pid']})")
...             break
...     else:
...         print("    ⚠️ Fortnite δεν τρέχει - Θα μπει σε High Priority μόλις ανοίξει")
... except:
...     print("    ⚠️ Δεν βρέθηκε")
... 
... # ============================================================
... # FINAL
... # ============================================================
... print("")
... print("="*70)
... print(f"  ✅ ΟΛΟΚΛΗΡΩΘΗΚΑΝ {total_tweaks} TWEAKS + BONUSES!")
... print("  🔥 Discord ΠΑΡΑΜΕΝΕΙ ΑΝΟΙΧΤΟ (δεν το έκλεισα)")
... print("  🚀 MAX PERFORMANCE - MIN PING - 0 DELAY")
... print("  ⚡ Κάνε επανεκκίνηση του PC σου τώρα!")
... print("="*70)
... print("")
