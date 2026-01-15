import platform
import socket
import os
import sys
import time
import datetime
import subprocess
import ctypes
import math
import random
import winreg
import struct

class Tectra:
    def __init__(self):
        self.sistema = platform.system()
        self.colores = self._verificar_colores()
        self.puntuacion = 0
        self.test_resultados = {}
        
    def _verificar_colores(self):
        if self.sistema == "Windows":
            return True
        else:
            return sys.stdout.isatty()
    
    def _color(self, codigo):
        if self.colores:
            return f"\033[{codigo}m"
        return ""
    
    RESET = property(lambda self: self._color(0))
    ROJO = property(lambda self: self._color(91))
    VERDE = property(lambda self: self._color(92))
    AMARILLO = property(lambda self: self._color(93))
    AZUL = property(lambda self: self._color(94))
    MAGENTA = property(lambda self: self._color(95))
    CIAN = property(lambda self: self._color(96))
    BLANCO = property(lambda self: self._color(97))
    NEGRITA = property(lambda self: self._color(1))
    
    def limpiar(self):
        os.system('cls' if self.sistema == 'Windows' else 'clear')
    
    def banner(self):
        banner = f"""
{self.CIAN}{self.NEGRITA}
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  ████████╗███████╗ ██████╗████████╗██████╗  █████╗     ║
║  ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗    ║
║     ██║   █████╗  ██║        ██║   ██████╔╝███████║    ║
║     ██║   ██╔══╝  ██║        ██║   ██╔══██╗██╔══██║    ║
║     ██║   ███████╗╚██████╗   ██║   ██║  ██║██║  ██║    ║
║     ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ║
║                                                        ║
╠════════════════════════════════════════════════════════╣
║               Technical Computer Tracker               ║
║                    Version 0.7 :)                      ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
{self.RESET}
"""
        print(banner)
    
    def separador(self, texto="", char="═", largo=60):
        if texto:
            espacios = (largo - len(texto) - 4) // 2
            print(f"{self.AZUL}{char * espacios} {self.CIAN}{texto} {self.AZUL}{char * espacios}")
        else:
            print(f"{self.AZUL}{char * largo}{self.RESET}")
    
    def barra(self, pct, largo=30, texto=""):
        bloques = int((pct / 100) * largo)
        bar = f"{self.VERDE}{'█' * bloques}{self.ROJO}{'░' * (largo - bloques)}"
        if texto:
            print(f"{texto}: {bar} {self.AMARILLO}{pct:.1f}%{self.RESET}")
        else:
            print(f"{bar} {self.AMARILLO}{pct:.1f}%{self.RESET}")
    
    def get_cpu(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                    info['nombre'] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                    info['marca'] = winreg.QueryValueEx(key, "VendorIdentifier")[0]
                    try:
                        info['mhz'] = winreg.QueryValueEx(key, "~MHz")[0]
                    except:
                        info['mhz'] = "?"
                    try:
                        info['identificador'] = winreg.QueryValueEx(key, "Identifier")[0]
                    except:
                        info['identificador'] = "?"
                    winreg.CloseKey(key)
                except:
                    info['nombre'] = platform.processor()
                    info['marca'] = "?"
                    info['mhz'] = "?"
                    info['identificador'] = "?"
            elif self.sistema == "Linux":
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        lines = f.read().split('\n')
                        for line in lines:
                            if 'model name' in line:
                                info['nombre'] = line.split(':')[1].strip()
                            elif 'vendor_id' in line and 'marca' not in info:
                                info['marca'] = line.split(':')[1].strip()
                            elif 'cpu MHz' in line:
                                info['mhz'] = float(line.split(':')[1].strip())
                except:
                    info['nombre'] = platform.processor()
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().strip()
                    info['nombre'] = output
                    output = subprocess.check_output(['sysctl', '-n', 'hw.cpufrequency']).decode().strip()
                    info['mhz'] = int(output) / 1000000
                except:
                    info['nombre'] = platform.processor()
            cores = os.cpu_count()
            if cores:
                info['fisicos'] = cores // 2 if cores % 2 == 0 else cores
                info['logicos'] = cores
                info['total'] = cores
            else:
                info['fisicos'] = "?"
                info['logicos'] = "?"
                info['total'] = "?"
            info['arch'] = platform.architecture()[0]
            info['maquina'] = platform.machine()
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_ram(self):
        info = {}
        try:
            if self.sistema == "Windows":
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
                    ]
                mem = MEMORYSTATUSEX()
                mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                    info['total_gb'] = mem.ullTotalPhys / (1024**3)
                    info['libre_gb'] = mem.ullAvailPhys / (1024**3)
                    info['uso_gb'] = info['total_gb'] - info['libre_gb']
                    info['pct'] = mem.dwMemoryLoad
                    info['total_mb'] = mem.ullTotalPhys / (1024**2)
                else:
                    info['total_gb'] = "No disponible"
            elif self.sistema == "Linux":
                try:
                    with open('/proc/meminfo', 'r') as f:
                        meminfo = {}
                        for line in f:
                            if ':' in line:
                                key, value = line.split(':', 1)
                                meminfo[key.strip()] = value.strip()
                        if 'MemTotal' in meminfo:
                            total_kb = int(meminfo['MemTotal'].split()[0])
                            info['total_gb'] = total_kb / (1024**2)
                        if 'MemAvailable' in meminfo:
                            disp_kb = int(meminfo['MemAvailable'].split()[0])
                            info['libre_gb'] = disp_kb / (1024**2)
                            info['uso_gb'] = info['total_gb'] - info['libre_gb']
                            info['pct'] = (info['uso_gb'] / info['total_gb']) * 100
                except:
                    info['total_gb'] = "No disponible"
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['sysctl', '-n', 'hw.memsize']).decode().strip()
                    total_bytes = int(output)
                    info['total_gb'] = total_bytes / (1024**3)
                    output = subprocess.check_output(['vm_stat']).decode()
                    lines = output.split('\n')
                    page_size = 4096
                    free_pages = 0
                    for line in lines:
                        if 'Pages free:' in line:
                            free_pages = int(line.split(':')[1].strip(' .'))
                            break
                    info['libre_gb'] = (free_pages * page_size) / (1024**3)
                    info['uso_gb'] = info['total_gb'] - info['libre_gb']
                    info['pct'] = (info['uso_gb'] / info['total_gb']) * 100
                except:
                    info['total_gb'] = "No disponible"
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_disco(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    free_bytes = ctypes.c_ulonglong()
                    total_bytes = ctypes.c_ulonglong()
                    free_bytes_ptr = ctypes.c_ulonglong()
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p("C:\\"),
                        ctypes.byref(free_bytes_ptr),
                        ctypes.byref(total_bytes),
                        ctypes.byref(free_bytes)
                    )
                    info['total_gb'] = total_bytes.value / (1024**3)
                    info['libre_gb'] = free_bytes.value / (1024**3)
                    info['uso_gb'] = info['total_gb'] - info['libre_gb']
                    if info['total_gb'] > 0:
                        info['pct'] = (info['uso_gb'] / info['total_gb']) * 100
                    else:
                        info['pct'] = 0
                except:
                    info['total_gb'] = "No disponible"
                drives = []
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in range(65, 91):
                    if bitmask & 1:
                        drives.append(chr(letter) + ":\\")
                    bitmask >>= 1
                info['unidades'] = drives
            else:
                try:
                    stat = os.statvfs('/')
                    info['total_gb'] = (stat.f_blocks * stat.f_frsize) / (1024**3)
                    info['libre_gb'] = (stat.f_bfree * stat.f_frsize) / (1024**3)
                    info['uso_gb'] = info['total_gb'] - info['libre_gb']
                    if info['total_gb'] > 0:
                        info['pct'] = (info['uso_gb'] / info['total_gb']) * 100
                    else:
                        info['pct'] = 0
                except:
                    info['total_gb'] = "No disponible"
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_pantalla(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    user32 = ctypes.windll.user32
                    info['ancho'] = user32.GetSystemMetrics(0)
                    info['alto'] = user32.GetSystemMetrics(1)
                    info['resolucion'] = f"{info['ancho']}x{info['alto']}"
                    
                    try:
                        info['bits_color'] = user32.GetSystemMetrics(12)
                        info['profundidad'] = f"{info['bits_color']} bits"
                    except:
                        info['profundidad'] = "?"
                    
                    try:
                        info['monitores'] = user32.GetSystemMetrics(80)
                        info['multi_monitor'] = "Sí" if info['monitores'] > 1 else "No"
                    except:
                        info['multi_monitor'] = "?"
                        
                except:
                    info['resolucion'] = "No disponible"
                    
            elif self.sistema == "Linux":
                try:
                    output = subprocess.check_output(['xrandr']).decode()
                    lines = output.split('\n')
                    for line in lines:
                        if '*' in line and 'connected' in line:
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and part.count('x') == 1:
                                    info['resolucion'] = part
                                    break
                            break
                    if 'resolucion' not in info:
                        info['resolucion'] = "No detectada"
                except:
                    info['resolucion'] = "No disponible"
                    
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode()
                    lines = output.split('\n')
                    for line in lines:
                        if 'Resolution' in line:
                            info['resolucion'] = line.split(':')[1].strip()
                            break
                    if 'resolucion' not in info:
                        info['resolucion'] = "No detectada"
                except:
                    info['resolucion'] = "No disponible"
                    
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_audio(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    import comtypes
                    import comtypes.client
                    
                    try:
                        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                        devices = AudioUtilities.GetSpeakers()
                        interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
                        volume = comtypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))
                        info['volumen'] = f"{int(volume.GetMasterVolumeLevelScalar() * 100)}%"
                        info['silenciado'] = "Sí" if volume.GetMute() else "No"
                        info['audio_detectado'] = "Sí"
                    except:
                        info['audio_detectado'] = "Posiblemente"
                        info['volumen'] = "No disponible"
                        
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Render")
                        count = winreg.QueryInfoKey(key)[0]
                        info['dispositivos_audio'] = count
                        winreg.CloseKey(key)
                    except:
                        info['dispositivos_audio'] = "?"
                        
                except:
                    info['audio_detectado'] = "Sistema de audio detectado"
                    
            elif self.sistema == "Linux":
                try:
                    output = subprocess.check_output(['aplay', '-l']).decode()
                    if 'card' in output.lower():
                        info['audio_detectado'] = "Sí"
                        lines = output.split('\n')
                        cards = [line for line in lines if 'card' in line]
                        info['tarjetas_audio'] = len(cards)
                    else:
                        info['audio_detectado'] = "No detectado"
                except:
                    info['audio_detectado'] = "Compruebe paquetes ALSA"
                    
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['system_profiler', 'SPAudioDataType']).decode()
                    if 'Audio' in output:
                        info['audio_detectado'] = "Sí"
                        lines = output.count('\n')
                        info['lineas_config'] = lines
                    else:
                        info['audio_detectado'] = "Sistema de audio presente"
                except:
                    info['audio_detectado'] = "Audio macOS detectado"
                    
        except Exception as e:
            info['error'] = str(e)
            info['audio_detectado'] = "Error en detección"
        return info
    
    def get_wifi(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces']).decode('latin-1')
                    lines = output.split('\n')
                    
                    for line in lines:
                        if 'Nombre' in line and ':' in line:
                            info['nombre_wifi'] = line.split(':')[1].strip()
                        elif 'SSID' in line and ':' in line:
                            info['ssid'] = line.split(':')[1].strip()
                        elif 'Tipo de radio' in line and ':' in line:
                            info['tipo_wifi'] = line.split(':')[1].strip()
                        elif 'Autenticación' in line and ':' in line:
                            info['autenticacion'] = line.split(':')[1].strip()
                        elif 'Cifrado' in line and ':' in line:
                            info['cifrado'] = line.split(':')[1].strip()
                        elif 'Estado' in line and ':' in line:
                            info['estado'] = line.split(':')[1].strip()
                        elif 'Señal' in line and ':' in line:
                            info['senal'] = line.split(':')[1].strip()
                        elif 'Velocidad de recepción (Mbps)' in line and ':' in line:
                            info['velocidad_rx'] = line.split(':')[1].strip()
                        elif 'Velocidad de transmisión (Mbps)' in line and ':' in line:
                            info['velocidad_tx'] = line.split(':')[1].strip()
                    
                    if 'tipo_wifi' in info:
                        tipo = info['tipo_wifi'].upper()
                        if '802.11A' in tipo:
                            info['generacion'] = "WiFi 2 (802.11a)"
                        elif '802.11B' in tipo:
                            info['generacion'] = "WiFi 1 (802.11b)"
                        elif '802.11G' in tipo:
                            info['generacion'] = "WiFi 3 (802.11g)"
                        elif '802.11N' in tipo:
                            info['generacion'] = "WiFi 4 (802.11n)"
                        elif '802.11AC' in tipo:
                            info['generacion'] = "WiFi 5 (802.11ac)"
                        elif '802.11AX' in tipo:
                            info['generacion'] = "WiFi 6 (802.11ax)"
                        elif '802.11BE' in tipo or 'WIFI 7' in tipo:
                            info['generacion'] = "WiFi 7"
                        else:
                            info['generacion'] = f"WiFi ({info['tipo_wifi']})"
                            
                except:
                    info['wifi_detectado'] = "Adaptador WiFi no detectado"
                    
            elif self.sistema == "Linux":
                try:
                    output = subprocess.check_output(['iwconfig']).decode()
                    if 'IEEE' in output:
                        lines = output.split('\n')
                        for line in lines:
                            if 'IEEE' in line:
                                if '802.11' in line:
                                    info['estandar'] = line.split('IEEE')[1].split()[0]
                                    if '802.11a' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 2"
                                    elif '802.11b' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 1"
                                    elif '802.11g' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 3"
                                    elif '802.11n' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 4"
                                    elif '802.11ac' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 5"
                                    elif '802.11ax' in info['estandar'].lower():
                                        info['generacion'] = "WiFi 6"
                                    else:
                                        info['generacion'] = f"WiFi ({info['estandar']})"
                                break
                        info['wifi_detectado'] = "Sí"
                    else:
                        info['wifi_detectado'] = "No detectado"
                except:
                    info['wifi_detectado'] = "Compruebe permisos/paquetes"
                    
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['networksetup', '-listallhardwareports']).decode()
                    if 'Wi-Fi' in output or 'AirPort' in output:
                        info['wifi_detectado'] = "Sí"
                        try:
                            output = subprocess.check_output(['system_profiler', 'SPAirPortDataType']).decode()
                            if 'PHY Mode' in output:
                                for line in output.split('\n'):
                                    if 'PHY Mode' in line:
                                        modo = line.split(':')[1].strip()
                                        if '802.11a' in modo:
                                            info['generacion'] = "WiFi 2"
                                        elif '802.11b' in modo:
                                            info['generacion'] = "WiFi 1"
                                        elif '802.11g' in modo:
                                            info['generacion'] = "WiFi 3"
                                        elif '802.11n' in modo:
                                            info['generacion'] = "WiFi 4"
                                        elif '802.11ac' in modo:
                                            info['generacion'] = "WiFi 5"
                                        elif '802.11ax' in modo:
                                            info['generacion'] = "WiFi 6"
                                        else:
                                            info['generacion'] = f"WiFi ({modo})"
                                        break
                        except:
                            info['generacion'] = "WiFi detectado"
                    else:
                        info['wifi_detectado'] = "No detectado"
                except:
                    info['wifi_detectado'] = "Adaptador WiFi macOS"
                    
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_bateria(self):
        info = {}
        try:
            if self.sistema == "Windows":
                try:
                    class SYSTEM_POWER_STATUS(ctypes.Structure):
                        _fields_ = [
                            ('ACLineStatus', ctypes.c_byte),
                            ('BatteryFlag', ctypes.c_byte),
                            ('BatteryLifePercent', ctypes.c_byte),
                            ('Reserved1', ctypes.c_byte),
                            ('BatteryLifeTime', ctypes.c_ulong),
                            ('BatteryFullLifeTime', ctypes.c_ulong)
                        ]
                    
                    power_status = SYSTEM_POWER_STATUS()
                    if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(power_status)):
                        info['conectado'] = "Sí" if power_status.ACLineStatus == 1 else "No"
                        info['porcentaje'] = f"{power_status.BatteryLifePercent}%"
                        
                        if power_status.BatteryLifeTime != 0xFFFFFFFF:
                            minutos = power_status.BatteryLifeTime // 60
                            horas = minutos // 60
                            minutos = minutos % 60
                            info['tiempo_restante'] = f"{horas}h {minutos}m"
                        else:
                            info['tiempo_restante'] = "Calculando..."
                            
                        flag = power_status.BatteryFlag
                        if flag & 1:
                            info['estado'] = "Alta"
                        elif flag & 2:
                            info['estado'] = "Baja"
                        elif flag & 4:
                            info['estado'] = "Crítica"
                        elif flag & 8:
                            info['estado'] = "Cargando"
                        elif flag & 128:
                            info['estado'] = "Sin batería"
                        else:
                            info['estado'] = "Desconocido"
                            
                        try:
                            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                                r"SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes")
                            subkey = winreg.OpenKey(key, r"381b4222-f694-41f0-9685-ff5bb260df2e")
                            value, _ = winreg.QueryValueEx(subkey, "FriendlyName")
                            info['esquema_energia'] = value.split('(')[0].strip()
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                        except:
                            info['esquema_energia'] = "Equilibrado"
                            
                    else:
                        info['sin_bateria'] = "PC de escritorio o error"
                        
                except:
                    info['bateria'] = "No disponible (PC escritorio?)"
                    
            elif self.sistema == "Linux":
                try:
                    if os.path.exists('/sys/class/power_supply/BAT0'):
                        with open('/sys/class/power_supply/BAT0/capacity', 'r') as f:
                            info['porcentaje'] = f"{f.read().strip()}%"
                        with open('/sys/class/power_supply/BAT0/status', 'r') as f:
                            estado = f.read().strip()
                            info['estado'] = estado
                        info['conectado'] = "Sí" if estado == "Charging" else "No"
                        info['bateria_detectada'] = "Sí"
                    else:
                        info['sin_bateria'] = "PC de escritorio o sin batería"
                except:
                    info['bateria'] = "No disponible"
                    
            elif self.sistema == "Darwin":
                try:
                    output = subprocess.check_output(['pmset', '-g', 'batt']).decode()
                    lines = output.split('\n')
                    if len(lines) > 1 and 'Battery' in lines[1]:
                        parts = lines[1].split('\t')
                        if len(parts) >= 2:
                            estado_info = parts[1].split(';')
                            if len(estado_info) >= 2:
                                info['porcentaje'] = estado_info[0].strip()
                                info['estado'] = estado_info[1].strip()
                                info['conectado'] = "Sí" if 'charged' in estado_info[1] or 'charging' in estado_info[1] else "No"
                                info['bateria_detectada'] = "Sí"
                    else:
                        info['sin_bateria'] = "iMac o Mac Pro (sin batería)"
                except:
                    info['bateria'] = "No disponible"
                    
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def get_sistema(self):
        info = {}
        try:
            info['so'] = platform.system()
            info['version'] = platform.version()
            info['release'] = platform.release()
            info['arch'] = platform.architecture()[0]
            info['maquina'] = platform.machine()
            info['hostname'] = socket.gethostname()
            info['procesador'] = platform.processor()
            
            try:
                info['usuario'] = os.getlogin()
            except:
                info['usuario'] = os.environ.get('USERNAME', os.environ.get('USER', '?'))
                
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                info['ip'] = s.getsockname()[0]
                s.close()
            except:
                info['ip'] = "No disponible"
                
            info['dir'] = os.getcwd()
            info['python_ver'] = platform.python_version()
            info['python_comp'] = platform.python_compiler()
            info['fecha_hora'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if self.sistema == "Windows":
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                    info['product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
                    info['build'] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
                    info['edition'] = winreg.QueryValueEx(key, "EditionID")[0] if 'EditionID' in [winreg.EnumValue(key, i)[0] for i in range(winreg.QueryInfoKey(key)[1])] else "?"
                    winreg.CloseKey(key)
                except:
                    info['product_name'] = f"Windows {info['release']}"
                    
        except Exception as e:
            info['error'] = str(e)
        return info
    
    def check_internet(self):
        try:
            param = '-n' if self.sistema == 'Windows' else '-c'
            result = subprocess.call(
                ['ping', param, '1', '8.8.8.8'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return "Conectado" if result == 0 else "Sin conexión"
        except:
            return "No verificado"
    
    def mostrar_completo(self):
        self.limpiar()
        self.banner()
        print(f"{self.CIAN}{self.NEGRITA}📊 INFORMACIÓN COMPLETA v0.7{self.RESET}")
        self.separador("TODOS LOS COMPONENTES DETALLADOS")
        
        print(f"\n{self.VERDE}🚀 PROCESADOR:{self.RESET}")
        cpu = self.get_cpu()
        print(f"   • {self.AMARILLO}Nombre:{self.RESET} {cpu.get('nombre', '?')}")
        print(f"   • {self.AMARILLO}Marca:{self.RESET} {cpu.get('marca', '?')}")
        if 'mhz' in cpu and cpu['mhz'] != "?":
            ghz = cpu['mhz'] / 1000 if isinstance(cpu['mhz'], (int, float)) else cpu['mhz']
            if isinstance(ghz, (int, float)):
                print(f"   • {self.AMARILLO}Frecuencia:{self.RESET} {ghz:.2f} GHz")
        print(f"   • {self.AMARILLO}Núcleos:{self.RESET} {cpu.get('fisicos', '?')} físicos, {cpu.get('logicos', '?')} lógicos")
        if 'identificador' in cpu and cpu['identificador'] != "?":
            print(f"   • {self.AMARILLO}ID:{self.RESET} {cpu['identificador']}")
        
        print(f"\n{self.VERDE}💾 MEMORIA RAM:{self.RESET}")
        ram = self.get_ram()
        if 'total_gb' in ram and ram['total_gb'] != "No disponible":
            total = ram['total_gb']
            if isinstance(total, (int, float)):
                print(f"   • {self.AMARILLO}Total:{self.RESET} {total:.2f} GB")
                if 'uso_gb' in ram and 'pct' in ram:
                    print(f"   • {self.AMARILLO}En uso:{self.RESET} {ram['uso_gb']:.2f} GB ({ram['pct']:.1f}%)")
                    print(f"   • {self.AMARILLO}Uso:{self.RESET} ", end="")
                    self.barra(ram['pct'], 25)
        else:
            print(f"   • {self.ROJO}No disponible{self.RESET}")
        
        print(f"\n{self.VERDE}💿 ALMACENAMIENTO:{self.RESET}")
        disco = self.get_disco()
        if 'total_gb' in disco and disco['total_gb'] != "No disponible":
            total = disco['total_gb']
            if isinstance(total, (int, float)):
                print(f"   • {self.AMARILLO}Total:{self.RESET} {total:.2f} GB")
                print(f"   • {self.AMARILLO}Libre:{self.RESET} {disco['libre_gb']:.2f} GB")
                print(f"   • {self.AMARILLO}Usado:{self.RESET} {disco['uso_gb']:.2f} GB")
                print(f"   • {self.AMARILLO}Uso:{self.RESET} ", end="")
                self.barra(disco['pct'], 25)
        else:
            print(f"   • {self.ROJO}No disponible{self.RESET}")
        
        print(f"\n{self.VERDE}🖥️  PANTALLA:{self.RESET}")
        pantalla = self.get_pantalla()
        if 'resolucion' in pantalla:
            print(f"   • {self.AMARILLO}Resolución:{self.RESET} {pantalla['resolucion']}")
            if 'profundidad' in pantalla:
                print(f"   • {self.AMARILLO}Profundidad color:{self.RESET} {pantalla['profundidad']}")
            if 'multi_monitor' in pantalla:
                print(f"   • {self.AMARILLO}Múltiples monitores:{self.RESET} {pantalla['multi_monitor']}")
        else:
            print(f"   • {self.ROJO}No disponible{self.RESET}")
        
        print(f"\n{self.VERDE}🔊 AUDIO:{self.RESET}")
        audio = self.get_audio()
        if 'audio_detectado' in audio:
            print(f"   • {self.AMARILLO}Sistema de audio:{self.RESET} {audio['audio_detectado']}")
            if 'volumen' in audio:
                print(f"   • {self.AMARILLO}Volumen:{self.RESET} {audio['volumen']}")
            if 'silenciado' in audio:
                print(f"   • {self.AMARILLO}Silenciado:{self.RESET} {audio['silenciado']}")
            if 'dispositivos_audio' in audio:
                print(f"   • {self.AMARILLO}Dispositivos:{self.RESET} {audio['dispositivos_audio']}")
        
        print(f"\n{self.VERDE}📡 WIFI:{self.RESET}")
        wifi = self.get_wifi()
        if 'wifi_detectado' in wifi:
            print(f"   • {self.AMARILLO}Adaptador WiFi:{self.RESET} {wifi['wifi_detectado']}")
            if 'generacion' in wifi:
                print(f"   • {self.AMARILLO}Generación WiFi:{self.RESET} {wifi['generacion']}")
            if 'tipo_wifi' in wifi:
                print(f"   • {self.AMARILLO}Tipo:{self.RESET} {wifi['tipo_wifi']}")
            if 'senal' in wifi:
                print(f"   • {self.AMARILLO}Señal:{self.RESET} {wifi['senal']}")
            if 'velocidad_rx' in wifi:
                print(f"   • {self.AMARILLO}Velocidad RX:{self.RESET} {wifi['velocidad_rx']}")
            if 'velocidad_tx' in wifi:
                print(f"   • {self.AMARILLO}Velocidad TX:{self.RESET} {wifi['velocidad_tx']}")
        
        print(f"\n{self.VERDE}🔋 BATERÍA:{self.RESET}")
        bateria = self.get_bateria()
        if 'porcentaje' in bateria:
            print(f"   • {self.AMARILLO}Porcentaje:{self.RESET} {bateria['porcentaje']}")
            print(f"   • {self.AMARILLO}Cargando:{self.RESET} {bateria.get('conectado', '?')}")
            print(f"   • {self.AMARILLO}Estado:{self.RESET} {bateria.get('estado', '?')}")
            if 'tiempo_restante' in bateria:
                print(f"   • {self.AMARILLO}Tiempo restante:{self.RESET} {bateria['tiempo_restante']}")
            if 'esquema_energia' in bateria:
                print(f"   • {self.AMARILLO}Esquema energía:{self.RESET} {bateria['esquema_energia']}")
        elif 'sin_bateria' in bateria:
            print(f"   • {self.AMARILLO}Tipo:{self.RESET} {self.ROJO}PC de escritorio{self.RESET}")
        
        print(f"\n{self.VERDE}🌐 SISTEMA Y RED:{self.RESET}")
        sistema = self.get_sistema()
        print(f"   • {self.AMARILLO}Sistema:{self.RESET} {sistema.get('so', '?')} {sistema.get('release', '?')}")
        if 'product_name' in sistema:
            print(f"   • {self.AMARILLO}Edición:{self.RESET} {sistema['product_name']}")
        print(f"   • {self.AMARILLO}Arquitectura:{self.RESET} {sistema.get('arch', '?')}")
        print(f"   • {self.AMARILLO}Hostname:{self.RESET} {sistema.get('hostname', '?')}")
        if 'ip' in sistema:
            print(f"   • {self.AMARILLO}IP:{self.RESET} {sistema['ip']}")
        internet = self.check_internet()
        color = self.VERDE if internet == "Conectado" else self.ROJO
        print(f"   • {self.AMARILLO}Internet:{self.RESET} {color}{internet}{self.RESET}")
        
        print(f"\n{self.VERDE}👤 USUARIO:{self.RESET}")
        print(f"   • {self.AMARILLO}Usuario:{self.RESET} {sistema.get('usuario', '?')}")
        print(f"   • {self.AMARILLO}Directorio:{self.RESET} {sistema.get('dir', '?')}")
        
        print(f"\n{self.VERDE}🐍 PYTHON:{self.RESET}")
        print(f"   • {self.AMARILLO}Versión:{self.RESET} {sistema.get('python_ver', '?')}")
        
        if self.puntuacion > 0:
            print(f"\n{self.VERDE}🏆 RENDIMIENTO:{self.RESET}")
            print(f"   • {self.AMARILLO}Puntuación:{self.RESET} {self.CIAN}{self.puntuacion:,}{self.RESET}")
            if self.puntuacion > 1000:
                calif = f"{self.VERDE}Excelente{self.RESET}"
            elif self.puntuacion > 800:
                calif = f"{self.CIAN}Muy Bueno{self.RESET}"
            elif self.puntuacion > 600:
                calif = f"{self.VERDE}Bueno{self.RESET}"
            elif self.puntuacion > 400:
                calif = f"{self.AMARILLO}Aceptable{self.RESET}"
            else:
                calif = f"{self.ROJO}Básico{self.RESET}"
            print(f"   • {self.AMARILLO}Calificación:{self.RESET} {calif}")
        
        print(f"\n{self.VERDE}📅 TIEMPO:{self.RESET}")
        print(f"   • {self.AMARILLO}Fecha/Hora:{self.RESET} {sistema.get('fecha_hora', '?')}")
        
        self.separador()
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
    
    def ejecutar_test(self):
        resultados = {}
        tiempos = {}
        
        print(f"{self.VERDE}[1/4] CPU...{self.RESET}")
        inicio = time.time()
        total = 0.0
        for i in range(1, 100000):
            total += math.sqrt(i) * math.sin(i * 0.01)
        tiempos['cpu'] = time.time() - inicio
        if tiempos['cpu'] < 0.15:
            resultados['cpu'] = 800
        elif tiempos['cpu'] < 0.25:
            resultados['cpu'] = 650
        elif tiempos['cpu'] < 0.4:
            resultados['cpu'] = 500
        elif tiempos['cpu'] < 0.6:
            resultados['cpu'] = 400
        else:
            resultados['cpu'] = 300
        print(f"   ⏱️  {tiempos['cpu']:.3f}s | ⭐ {resultados['cpu']}")
        
        print(f"\n{self.VERDE}[2/4] RAM...{self.RESET}")
        inicio = time.time()
        lista = []
        for i in range(100000):
            lista.append(i)
            if i % 3 == 0 and lista:
                lista.pop()
        tiempos['ram'] = time.time() - inicio
        if tiempos['ram'] < 0.1:
            resultados['ram'] = 700
        elif tiempos['ram'] < 0.2:
            resultados['ram'] = 550
        elif tiempos['ram'] < 0.35:
            resultados['ram'] = 400
        else:
            resultados['ram'] = 300
        print(f"   ⏱️  {tiempos['ram']:.3f}s | ⭐ {resultados['ram']}")
        
        print(f"\n{self.VERDE}[3/4] DISCO...{self.RESET}")
        try:
            inicio = time.time()
            test_file = 'test.tmp'
            with open(test_file, 'w') as f:
                f.write('X' * 10000)
            with open(test_file, 'r') as f:
                contenido = f.read()
            os.remove(test_file)
            tiempos['disco'] = time.time() - inicio
        except:
            tiempos['disco'] = 0.5
        if tiempos['disco'] < 0.05:
            resultados['disco'] = 750
        elif tiempos['disco'] < 0.1:
            resultados['disco'] = 600
        elif tiempos['disco'] < 0.2:
            resultados['disco'] = 450
        else:
            resultados['disco'] = 350
        print(f"   ⏱️  {tiempos['disco']:.3f}s | ⭐ {resultados['disco']}")
        
        print(f"\n{self.VERDE}[4/4] SISTEMA...{self.RESET}")
        inicio = time.time()
        for _ in range(1000):
            _ = time.time()
        tiempos['sistema'] = time.time() - inicio
        if tiempos['sistema'] < 0.05:
            resultados['sistema'] = 600
        elif tiempos['sistema'] < 0.1:
            resultados['sistema'] = 450
        elif tiempos['sistema'] < 0.2:
            resultados['sistema'] = 300
        else:
            resultados['sistema'] = 200
        print(f"   ⏱️  {tiempos['sistema']:.3f}s | ⭐ {resultados['sistema']}")
        
        puntuacion_total = (
            resultados['cpu'] * 0.35 +
            resultados['ram'] * 0.25 +
            resultados['disco'] * 0.20 +
            resultados['sistema'] * 0.20
        )
        puntuacion_total = min(1200, max(300, puntuacion_total))
        
        resultados['total'] = round(puntuacion_total, 0)
        resultados['tiempos'] = tiempos
        
        if puntuacion_total > 1000:
            resultados['calif'] = 'EXCELENTE'
            resultados['color'] = self.VERDE
        elif puntuacion_total > 800:
            resultados['calif'] = 'MUY BUENO'
            resultados['color'] = self.CIAN
        elif puntuacion_total > 600:
            resultados['calif'] = 'BUENO'
            resultados['color'] = self.VERDE
        elif puntuacion_total > 400:
            resultados['calif'] = 'ACEPTABLE'
            resultados['color'] = self.AMARILLO
        else:
            resultados['calif'] = 'BÁSICO'
            resultados['color'] = self.ROJO
        
        self.puntuacion = puntuacion_total
        self.test_resultados = resultados
        
        return resultados
    
    def mostrar_test(self):
        self.limpiar()
        self.banner()
        print(f"{self.CIAN}{self.NEGRITA}⚡ TEST DE RENDIMIENTO{self.RESET}")
        self.separador("EVALUACIÓN")
        
        cpu = self.get_cpu()
        print(f"\n{self.VERDE}💻 Sistema:{self.RESET}")
        print(f"   {self.AMARILLO}{cpu.get('nombre', '?')[:60]}{self.RESET}")
        
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
        
        resultados = self.ejecutar_test()
        
        self.limpiar()
        print(f"\n{self.CIAN}{self.NEGRITA}📊 RESULTADOS{self.RESET}")
        self.separador("PUNTUACIONES")
        
        print(f"\n{self.AZUL}┌{'─' * 20}┬{'─' * 10}┬{'─' * 10}┬{'─' * 10}┐{self.RESET}")
        print(f"{self.AZUL}│{self.RESET} {self.NEGRITA}{'Componente':<18}{self.RESET} {self.AZUL}│{self.RESET} {self.NEGRITA}{'Tiempo':<8}{self.RESET} {self.AZUL}│{self.RESET} {self.NEGRITA}{'Puntos':<8}{self.RESET} {self.AZUL}│{self.RESET} {self.NEGRITA}{'Nivel':<8}{self.RESET} {self.AZUL}│{self.RESET}")
        print(f"{self.AZUL}├{'─' * 20}┼{'─' * 10}┼{'─' * 10}┼{'─' * 10}┤{self.RESET}")
        
        componentes = [
            ("CPU", resultados['cpu'], resultados['tiempos']['cpu']),
            ("RAM", resultados['ram'], resultados['tiempos']['ram']),
            ("Disco", resultados['disco'], resultados['tiempos']['disco']),
            ("Sistema", resultados['sistema'], resultados['tiempos']['sistema'])
        ]
        
        for nombre, puntos, tiempo in componentes:
            if puntos > 700:
                nivel = f"{self.VERDE}Alto{self.RESET}"
            elif puntos > 500:
                nivel = f"{self.CIAN}Medio{self.RESET}"
            elif puntos > 350:
                nivel = f"{self.AMARILLO}Bajo{self.RESET}"
            else:
                nivel = f"{self.ROJO}M.Bajo{self.RESET}"
            tiempo_str = f"{tiempo:.3f}s"
            puntos_str = f"{puntos}"
            print(f"{self.AZUL}│{self.RESET} {nombre:<18} {self.AZUL}│{self.RESET} {tiempo_str:>8} {self.AZUL}│{self.RESET} {puntos_str:>8} {self.AZUL}│{self.RESET} {nivel:^8} {self.AZUL}│{self.RESET}")
        
        print(f"{self.AZUL}└{'─' * 20}┴{'─' * 10}┴{'─' * 10}┴{'─' * 10}┘{self.RESET}")
        
        total = resultados['total']
        calif = resultados['calif']
        color = resultados['color']
        
        print(f"\n{self.VERDE}🎯 TOTAL:{self.RESET}")
        print(f"   {self.CIAN}{self.NEGRITA}{total:,}{self.RESET} / 1,200")
        
        print(f"\n{self.VERDE}🏅 CALIFICACIÓN:{self.RESET}")
        print(f"   {color}{self.NEGRITA}{calif}{self.RESET}")
        
        print(f"\n{self.AMARILLO}📊 Rendimiento:{self.RESET}")
        porcentaje = (total / 1200) * 100
        print("  ", end="")
        self.barra(porcentaje, 40, f"{total:,}/1,200")
        
        print(f"\n{self.VERDE}💡 RECOMENDACIONES:{self.RESET}")
        if total > 800:
            print(f"   {self.VERDE}✅ Sistema óptimo{self.RESET}")
            print(f"   • Mantén actualizaciones")
        elif total > 600:
            print(f"   {self.CIAN}👍 Buen rendimiento{self.RESET}")
            print(f"   • Optimiza programas")
        elif total > 400:
            print(f"   {self.AMARILLO}⚠️  Rendimiento aceptable{self.RESET}")
            print(f"   • Evita multitarea pesada")
        else:
            print(f"   {self.ROJO}🔧 Sistema limitado{self.RESET}")
            print(f"   • Considera optimizar")
        
        self.separador()
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
    
    def mostrar_resumen(self):
        self.limpiar()
        self.banner()
        print(f"{self.CIAN}{self.NEGRITA}📋 RESUMEN RÁPIDO v2.0{self.RESET}")
        self.separador("INFORMACIÓN ESENCIAL")
        
        cpu = self.get_cpu()
        ram = self.get_ram()
        sistema = self.get_sistema()
        pantalla = self.get_pantalla()
        wifi = self.get_wifi()
        bateria = self.get_bateria()
        
        print(f"\n{self.VERDE}💻 Hardware:{self.RESET}")
        nombre = cpu.get('nombre', '?')
        if len(nombre) > 50:
            nombre = nombre[:50] + "..."
        print(f"   • CPU: {nombre}")
        print(f"   • Núcleos: {cpu.get('logicos', '?')}")
        if 'total_gb' in ram and isinstance(ram['total_gb'], (int, float)):
            print(f"   • RAM: {ram['total_gb']:.1f} GB")
        if 'resolucion' in pantalla:
            print(f"   • Pantalla: {pantalla['resolucion']}")
        
        print(f"\n{self.VERDE}🔌 Conectividad:{self.RESET}")
        if 'generacion' in wifi:
            print(f"   • WiFi: {wifi['generacion']}")
        if 'porcentaje' in bateria:
            print(f"   • Batería: {bateria['porcentaje']} ({bateria.get('estado', '?')})")
        elif 'sin_bateria' in bateria:
            print(f"   • Tipo: PC de escritorio")
        
        print(f"\n{self.VERDE}🖥️  Sistema:{self.RESET}")
        print(f"   • SO: {sistema.get('so', '?')} {sistema.get('release', '?')}")
        print(f"   • Usuario: {sistema.get('usuario', '?')}")
        
        if self.puntuacion > 0:
            print(f"\n{self.VERDE}⚡ Rendimiento:{self.RESET}")
            print(f"   • Puntuación: {self.puntuacion:,}")
            if self.puntuacion > 1000:
                calif = f"{self.VERDE}Excelente{self.RESET}"
            elif self.puntuacion > 800:
                calif = f"{self.CIAN}Muy Bueno{self.RESET}"
            elif self.puntuacion > 600:
                calif = f"{self.VERDE}Bueno{self.RESET}"
            elif self.puntuacion > 400:
                calif = f"{self.AMARILLO}Aceptable{self.RESET}"
            else:
                calif = f"{self.ROJO}Básico{self.RESET}"
            print(f"   • Calificación: {calif}")
        
        print(f"\n{self.VERDE}📅 Estado:{self.RESET}")
        print(f"   • Fecha: {datetime.datetime.now().strftime('%d/%m/%Y')}")
        print(f"   • Hora: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        self.separador()
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
    
    def mostrar_menu(self):
        while True:
            self.limpiar()
            self.banner()
            
            print(f"{self.CIAN}{self.NEGRITA}📋 MENÚ PRINCIPAL v2.0{self.RESET}")
            self.separador("OPCIONES")
            
            print(f"\n{self.VERDE}1.{self.RESET} {self.NEGRITA}📊 Información COMPLETA{self.RESET}")
            print(f"{self.VERDE}2.{self.RESET} {self.NEGRITA}⚡ Test de Rendimiento{self.RESET}")
            print(f"{self.VERDE}3.{self.RESET} {self.NEGRITA}📋 Resumen Rápido{self.RESET}")
            print(f"{self.VERDE}4.{self.VERDE}🆕 {self.NEGRITA}Especificaciones Avanzadas{self.RESET}")
            print(f"{self.VERDE}5.{self.RESET} {self.NEGRITA}ℹ️  Acerca de Tectra{self.RESET}")
            print(f"{self.VERDE}0.{self.RESET} {self.NEGRITA}🚪 Salir{self.RESET}")
            
            self.separador()
            
            opcion = input(f"\n{self.AMARILLO}Opción (0-5): {self.RESET}").strip()
            
            if opcion == "1":
                self.mostrar_completo()
            elif opcion == "2":
                self.mostrar_test()
            elif opcion == "3":
                self.mostrar_resumen()
            elif opcion == "4":
                self.mostrar_especificaciones()
            elif opcion == "5":
                self.mostrar_acerca()
            elif opcion == "0":
                self.mostrar_salida()
                break
            else:
                print(f"\n{self.ROJO}❌ Opción inválida{self.RESET}")
                time.sleep(1)
    
    def mostrar_especificaciones(self):
        self.limpiar()
        self.banner()
        print(f"{self.CIAN}{self.NEGRITA}🔧 ESPECIFICACIONES AVANZADAS{self.RESET}")
        self.separador("DETALLES TÉCNICOS COMPLETOS")
        
        print(f"\n{self.VERDE}🖥️  PANTALLA DETALLADA:{self.RESET}")
        pantalla = self.get_pantalla()
        for key, value in pantalla.items():
            if key not in ['error']:
                print(f"   • {self.AMARILLO}{key}:{self.RESET} {value}")
        
        print(f"\n{self.VERDE}🔊 SISTEMA DE AUDIO:{self.RESET}")
        audio = self.get_audio()
        for key, value in audio.items():
            if key not in ['error']:
                print(f"   • {self.AMARILLO}{key}:{self.RESET} {value}")
        
        print(f"\n{self.VERDE}📡 WIFI COMPLETO:{self.RESET}")
        wifi = self.get_wifi()
        for key, value in wifi.items():
            if key not in ['error']:
                print(f"   • {self.AMARILLO}{key}:{self.RESET} {value}")
        
        print(f"\n{self.VERDE}🔋 BATERÍA DETALLADA:{self.RESET}")
        bateria = self.get_bateria()
        for key, value in bateria.items():
            if key not in ['error']:
                print(f"   • {self.AMARILLO}{key}:{self.RESET} {value}")
        
        print(f"\n{self.VERDE}💻 SISTEMA COMPLETO:{self.RESET}")
        sistema = self.get_sistema()
        for key in ['so', 'version', 'release', 'arch', 'maquina', 'hostname', 
                   'usuario', 'ip', 'python_ver', 'python_comp']:
            if key in sistema:
                print(f"   • {self.AMARILLO}{key}:{self.RESET} {sistema[key]}")
        
        self.separador()
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
    
    def mostrar_acerca(self):
        self.limpiar()
        self.banner()
        print(f"{self.CIAN}{self.NEGRITA}ℹ️  ACERCA DE TECTRA v0.7{self.RESET}")
        self.separador("VERSION 0.7 - ESPECIFICACIONES COMPLETAS")
        
        texto = f"""
{self.VERDE}🚀 TECTRA - Technical Computer Tracker v0.7{self.RESET}

{self.AMARILLO}📊 NUEVAS FUNCIONALIDADES:{self.RESET}
• Resolución de pantalla completa
• Información del sistema de audio
• Tipo y generación de WiFi
• Estado detallado de batería
• Esquema de energía
• Velocidades de red WiFi

{self.AMARILLO}🎯 DETALLES INCLUIDOS:{self.RESET}
• Procesador completo con ID
• Memoria RAM con uso en tiempo real
• Almacenamiento y unidades
• Pantalla (resolución, profundidad)
• Audio (volumen, dispositivos)
• WiFi (tipo, generación, señal)
• Batería (%, estado, tiempo)
• Sistema operativo completo

{self.AMARILLO}🔧 TECNOLOGÍAS:{self.RESET}
• Módulos estándar de Python
• WinReg para Windows
• APIs del sistema (Windows/Linux/macOS)
• Comandos del sistema
• Cálculos matemáticos
• Formato ANSI colores

{self.AMARILLO}🎨 INTERFAZ MEJORADA:{self.RESET}
• Banner ASCII mejorado
• Separadores organizados
• Barras de progreso visuales
• Códigos de color intuitivos
• Navegación mejorada
• Menú expandido
"""
        print(texto)
        
        self.separador()
        input(f"\n{self.MAGENTA}Presiona Enter...{self.RESET}")
    
    def mostrar_salida(self):
        self.limpiar()
        
        salida = f"""
{self.CIAN}{self.NEGRITA}
╔════════════════════════════════════════════════════════╗
║                                                        ║
║  ████████╗███████╗ ██████╗████████╗██████╗  █████╗     ║
║  ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗    ║
║     ██║   █████╗  ██║        ██║   ██████╔╝███████║    ║
║     ██║   ██╔══╝  ██║        ██║   ██╔══██╗██╔══██║    ║
║     ██║   ███████╗╚██████╗   ██║   ██║  ██║██║  ██║    ║
║     ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ║
║                                                        ║
║          Gracias por usar TECTRA v0.7!                 ║
║                                                        ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
{self.RESET}

{self.VERDE}💻 Especificaciones completas de tu sistema!{self.RESET}
{self.AMARILLO}¡Hasta pronto! 👋{self.RESET}
"""
        print(salida)
        time.sleep(2)

def main():
    try:
        app = Tectra()
        app.mostrar_menu()
    except KeyboardInterrupt:
        print(f"\n\n{app.ROJO}Interrumpido por usuario.{app.RESET}")
    except Exception as e:
        print(f"\n{app.ROJO}Error: {e}{app.RESET}")
        input("Presiona Enter para salir...")

if __name__ == "__main__":
    main()
