import platform
import subprocess
import os

def file_write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def run_wmic(cmd):
    try:
        result = subprocess.run(f'wmic {cmd}', capture_output=True, text=True, shell=True, encoding='cp866')
        return result.stdout.strip()
    except:
        return ""

def get_reg_value(path, name):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        return str(value).strip()
    except:
        return "0"

def sys_info(path):
    s = "SysInfo\r\n"
    s += f"\r\nCPU Architecture : {platform.machine()}"
    s += f"\r\nProduct Type : {platform.platform()}"
    s += f"\r\nKernel Type : {platform.system().lower()}"
    s += f"\r\nKernel Version : {platform.version()}"
    s += f"\r\nMachine ID : {platform.node()}"
    s += "\r\n-----------------------------------------------------------------\r\n"
    
    if platform.system() == 'Windows':
        cpu = run_wmic("cpu get name")
        s += f"\r\nCPU:\r\n{cpu}\r\n"
        
        gpu = run_wmic("PATH Win32_videocontroller get VideoProcessor")
        s += f"\r\nGPU:\r\n{gpu}\r\n"
        
        ram = run_wmic("PATH Win32_VideoController get AdapterRAM")
        s += f"\r\nGPU RAM:\r\n{ram}\r\n"
    
    file_write(path, s)

def drive_info(path):
    s = "Mounted Volumes\r\n"
    
    if platform.system() == 'Windows':
        disks = run_wmic("logicaldisk get deviceid,volumename,filesystem,size,freespace")
        lines = disks.split('\n')
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if parts:
                    device = parts[0]
                    fs = parts[3] if len(parts) > 3 else ""
                    name = " ".join(parts[4:]) if len(parts) > 4 else ""
                    s += "\r\n"
                    s += f"\r\nDevice: {device}"
                    s += f"\r\nDisplayName: {name}"
                    s += f"\r\nName: {name}"
                    s += f"\r\nRoot: {device}/"
                    s += f"\r\nFileSys: {fs}"
                    if len(parts) > 2:
                        s += f"\r\nDisk Spaces Available: {parts[1]}"
                        s += f"\r\nDisk Spaces Total: {parts[2]}"
    
    file_write(path, s)

def seting_info(path):
    s = "System BIOS informations\r\n"
    
    if platform.system() == 'Windows':
        bios_key = r"HARDWARE\DESCRIPTION\System\BIOS"
        s += f"Base Manufacturer: {get_reg_value(bios_key, 'BaseBoardManufacturer')}\r\n"
        s += f"Base Product: {get_reg_value(bios_key, 'BaseBoardProduct')}\r\n"
        s += f"BIOS Vendor: {get_reg_value(bios_key, 'BIOSVendor')}\r\n"
        s += f"BIOS Release Date: {get_reg_value(bios_key, 'BIOSReleaseDate')}\r\n"
        s += f"System Manufacturer: {get_reg_value(bios_key, 'SystemManufacturer')}\r\n"
        s += f"Product Name: {get_reg_value(bios_key, 'SystemProductName')}\r\n"
        s += f"System SKU: {get_reg_value(bios_key, 'SystemSKU')}\r\n"
    
    file_write(path, s)

def main():
    sys_info("info.txt")
    drive_info("drive.txt")
    seting_info("seting.txt")
    print("ok")

if __name__ == "__main__":
    main()