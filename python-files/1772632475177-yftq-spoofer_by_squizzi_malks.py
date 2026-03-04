import ctypes
import sys
import webbrowser
import subprocess
import uuid
import struct
import random
import socket
import tkinter as tk
import os
import time
import shutil
import winreg
from tkinter import messagebox

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


menu = tk.Tk()
menu.title("Spoofer by SQUIZZI squad")
menu.geometry("500x500")
menu.configure(bg="#2C3E50")

maintext = tk.Label(menu, text="Enter password: ", fg="white", bg="#2C3E50", font=("Arial", 32))
maintext.pack(pady=20)

entry = tk.Entry(menu, font=("Arial", 32), bg="#ECF0F1", fg="#2C3E50")
entry.pack(pady=10)

button = tk.Button(menu, font=("Arial", 32), text="enter", bg="#E74C3C", fg="white", command=lambda: checkpassword())
button.pack(pady=20)

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
ip = tk.Label(menu, text=f"Your IP: {local_ip}", font=("Arial", 18), bg="#2C3E50", fg="#ECF0F1")
host = tk.Label(menu, text=f"Your hostname: {hostname}", font=("Arial", 18), bg="#2C3E50", fg="#ECF0F1")
ip.pack()
host.pack()


def checkpassword():
    if entry.get() == "DeIiveLegendarySPOOFER!!*(eFJ)":
        entry.delete(0, "end")
        messagebox.showwarning("Spoofer", "Right!")
        menu.destroy()
        spoofing()
    else:
        button.destroy()
        notrightpass = tk.Label(menu, text="Password is not correct.", fg="red", bg="#2C3E50", font=("Arial", 32))
        notrightpass.pack()


def spoofing():
    new_window = tk.Tk()
    new_window.geometry("800x800")
    new_window.title("Spoofer")
    new_window.configure(bg="#2C3E50")
    
    welcome_label = tk.Label(new_window, text="Welcome to Spoofer!", font=("Arial", 32), bg="#2C3E50", fg="white")
    welcome_label.pack(pady=50)
    
    var1 = tk.IntVar()
    var2 = tk.IntVar()
    var3 = tk.IntVar()
    var4 = tk.IntVar()
    var5 = tk.IntVar()
    var6 = tk.IntVar()
    var7 = tk.IntVar()


    def select_all():
        if var1.get() == 1:
            var2.set(1)
            var3.set(1)
            var4.set(1)
            var5.set(1)
            var6.set(1)
            var7.set(1)
        else:
            var2.set(0)
            var3.set(0)
            var4.set(0)
            var5.set(0)
            var6.set(0)
            var7.set(0)
    
    def start_spoof():
        if var2.get() == 1:
            spoof_bios()
        if var3.get() == 1:
            spoof_cpu()
        if var4.get() == 1:
            spoof_disk_serial()
        if var5.get() == 1:
            spoof_mac_powershell()
        if var6.get() == 1:
            registery()
        if var7.get() == 1:
            computer_name()

    def cache():
        if clean_logs.get() == 1:
            clean_logs()
    
    check1 = tk.Checkbutton(new_window, text="Full spoof(select all)", variable=var1, 
                           font=("Arial", 16), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white", command=select_all)
    check1.pack(pady=5)
    
    check2 = tk.Checkbutton(new_window, text="Spoof BIOS / Motherboard", variable=var2, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check2.pack(pady=2)
    
    check3 = tk.Checkbutton(new_window, text="Spoof CPU Info", variable=var3, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check3.pack(pady=5)
    
    check4 = tk.Checkbutton(new_window, text="Spoof Disk / Volume IDs", variable=var4, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check4.pack(pady=5)
    
    check5 = tk.Checkbutton(new_window, text="Spoof Network Adapters (MAC)", variable=var5, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check5.pack(pady=5)
    
    check6 = tk.Checkbutton(new_window, text="Spoof windows registry / TPM traces", variable=var6, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check6.pack(pady=5)
    
    check7 = tk.Checkbutton(new_window, text="Spoof computer name", variable=var7, 
                           font=("Arial", 12), bg="#2C3E50", fg="white", selectcolor="#34495E",
                           activebackground="#2C3E50", activeforeground="white")
    check7.pack(pady=5)
    
    button_spoof = tk.Button(new_window, font=("Arial", 32), text="SPOOF", bg="#27AE60", fg="white", command=start_spoof)
    button_spoof.pack(pady=20)

    button_clean = tk.Button(new_window, text="Clean FORTNITE logs (after spoof)", font=("Arial", 32), bg="#27AE60", command=clean_logs)
    button_clean.pack()

    button_society = tk.Button(new_window, font=("Arial", 24), text="CREATOR", bg="#27AE60", command=dm_creator)
    button_society.pack()
    new_window.mainloop()


def spoof_bios():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS", 0, winreg.KEY_SET_VALUE)

        bios_vendors = [
            "American Megatrends Inc.",
            "Phoenix Technologies Ltd.",
            "Insyde Corp.",
            "Dell Inc.",
            "HP",
            "LENOVO",
            "ASUS",
            "Micro-Star International Co., Ltd.",
            "Gigabyte Technology Co., Ltd.",
            "Intel Corp."
        ]

        system_manufacturers = [
            "Dell Inc.",
            "HP Inc.",
            "Lenovo",
            "ASUS",
            "Acer",
            "Microsoft Corporation",
            "Apple Inc.",
            "Samsung Electronics",
            "Toshiba",
            "Sony"
        ]

        bios_versions = [
            "1.2.3",
            "F.25",
            "P1.40",
            "2.1.0",
            "5.12",
            "3.0.1",
            "1.7.0",
            "4.6.1",
            "2.3.0",
            "6.0.2"
        ]

        winreg.SetValueEx(key, "BIOSVendor", 0, winreg.REG_SZ, random.choice(bios_vendors))
        winreg.SetValueEx(key, "BIOSVersion", 0, winreg.REG_SZ, random.choice(bios_versions))
        winreg.SetValueEx(key, "SystemManufacturer", 0, winreg.REG_SZ, random.choice(system_manufacturers))
        winreg.SetValueEx(key, "BaseBoardManufacturer", 0, winreg.REG_SZ, random.choice(system_manufacturers))

        winreg.CloseKey(key)
        messagebox.showwarning("spoofer", "BIOS Successfully spoofed!")
    except Exception as e:
        messagebox.showerror("spoofer", "Unknown Error")
    

def spoof_cpu():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0", 0, winreg.KEY_SET_VALUE)

        cpu_names = [
            "Intel(R) Core(TM) i9-13900K CPU @ 3.00GHz",
            "Intel(R) Core(TM) i7-13700K CPU @ 3.40GHz",
            "Intel(R) Core(TM) i5-13600K CPU @ 3.50GHz",
            "AMD Ryzen 9 7950X 16-Core Processor",
            "AMD Ryzen 7 7800X3D 8-Core Processor",
            "AMD Ryzen 5 7600X 6-Core Processor",
            "Intel(R) Xeon(R) Gold 6258R CPU @ 2.70GHz",
            "AMD EPYC 7763 64-Core Processor" ]
        
        vendors = [
            "GenuineIntel",
            "AuthenticAMD"
        ]
        
        winreg.SetValueEx(key, "ProcessorNameString", 0, winreg.REG_SZ , random.choice(cpu_names))
        winreg.SetValueEx(key, "VendorIdentifier", 0, winreg.REG_SZ, random.choice(vendors))

        winreg.CloseKey(key)
        messagebox.showwarning("spoofer", "CPU spoofed successfully!")
    except Exception as e:
        messagebox.showerror("spoofer", "Unknown ERROR")
    
def spoof_disk_serial(drive='C:'):
    try:
        handle = os.open(f"\\\\.\\{drive}", os.O_RDWR | os.O_BINARY)
        os.lseek(handle, 0, 0)
        sector = os.read(handle, 512)
        
        if sector[3:7] == b'NTFS':
            offset = 0x48
        elif sector[82:86] == b'FAT32':
            offset = 0x43
        else:
            offset = 0x27
            
        new_serial = random.randint(0x10000000, 0xFFFFFFFF)
        sector = bytearray(sector)
        sector[offset] = new_serial & 0xFF
        sector[offset + 1] = (new_serial >> 8) & 0xFF
        sector[offset + 2] = (new_serial >> 16) & 0xFF
        sector[offset + 3] = (new_serial >> 24) & 0xFF
        
        os.lseek(handle, 0, 0)
        os.write(handle, bytes(sector))
        os.close(handle)
        
        serial_str = f"{new_serial:08X}"
        messagebox.showwarning("spoofer", "Your disk successfully spoofed!")
        
    except Exception as e:
        messagebox.showerror("spoofer", "Unknown ERROR")

def spoof_mac_powershell():
    try:
        
        new_mac = "02" + ''.join(random.choices("0123456789ABCDEF", k=10))
        
        
        ps_script = f"""
        $adapter = Get-NetAdapter | Where-Object {{$_.Status -eq "Up"}} | Select-Object -First 1
        if ($adapter) {{
            Disable-NetAdapter -Name $adapter.Name -Confirm:$false
            Set-NetAdapterAdvancedProperty -Name $adapter.Name -RegistryKeyword "NetworkAddress" -RegistryValue "{new_mac}"
            Enable-NetAdapter -Name $adapter.Name -Confirm:$false
        }}
        """
        
        subprocess.run(["powershell", "-Command", ps_script], check=True)
        messagebox.showinfo("Success", f"MAC changed to {new_mac}")
    except:
        messagebox.showerror("Error", "Failed to change MAC")

def  registery():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_SET_VALUE)

        guid_list = []
        for i in range(100):
            guid_list.append(str(uuid.uuid4()).upper())

        winreg.SetValueEx(key, "MachineGuid", 0, winreg.REG_SZ, random.choice(guid_list))
        winreg.CloseKey(key)
        messagebox.showwarning("Spoofer", "GUID spoofed successfully!")

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\IDConfigDB\Hardware Profiles\0001", 0, winreg.KEY_SET_VALUE)

        hwprofileguid = []
        for i in range(100):
            hwprofileguid.append(str(uuid.uuid4()).upper())

        winreg.SetValueEx(key, "HwProfileGuid", 0, winreg.REG_SZ, random.choice(hwprofileguid))
        winreg.CloseKey(key)
        
        productIDs = [
            "56360-25898-77180-91168-12345",
            "87654-32109-87654-32109-56789",
            "45678-90123-45678-90123-23456",
            "78901-23456-78901-23456-89012",
            "34567-89012-34567-89012-67890",
            "23456-78901-23456-78901-12345",
            "98765-43210-98765-43210-54321",
            "65432-10987-65432-10987-98765",
            "32109-87654-32109-87654-43210",
            "13579-24680-13579-24680-97531"
        ]

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", 0, winreg.KEY_SET_VALUE)

        winreg.SetValueEx(key, "ProductId", 0, winreg.REG_SZ, random.choice(productIDs))
        winreg.CloseKey(key)

        messagebox.showwarning("Spoofer", "Registry spoofed successfully!")
    except Exception as e:
        messagebox.showerror("Spoofer", "Unknown ERROR!")

def computer_name():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName", 0, winreg.KEY_SET_VALUE)

        computer_names = [
            "DESKTOP-A38J83F",
            "DESKTOP-R38FB92",
            "DESKTOP-ACC921I",
            "DESKTOP-IO280FD",
            "DESKTOP-D73UI92",
            "DESKTOP-OT92U88",
            "DESKTOP-BDH729D",
            "DESKTOP-UWI923T",
            "DESKTOP-KT923PA",
            "DESKTOP-9329KFA",
            "DESKTOP-JF29DKK",
            "DESKTOP-95UGJS9",
            "DESKTOP-IEOF03J",
            "DESKTOP-FER0381",
            "DESKTOP-FK92HEW",
            "DESKTOP-IREW931",
            "DESKTOP-9D7K4T3",
            "DESKTOP-FJ7SJG9"
        ]

        winreg.SetValueEx(key, "ComputerName", 0, winreg.REG_SZ, random.choice(computer_names))
        winreg.CloseKey(key)
        messagebox.showwarning("Spoofer", "Computer name successfully spoofed! Restart your pc!")
    except Exception as e:
        messagebox.showerror("Spoofer", "Unknown ERROR!") 

def clean_logs():
    try:
        ways = [
            os.path.expandvars(r"%LOCALAPPDATA%\EpicGamesLauncher\Saved"),
            os.path.expandvars(r"%LOCALAPPDATA%\UnrealEngine"),
            os.path.expandvars(r"%APPDATA%\Epic"),
            os.path.expandvars(r"%PROGRAMDATA%\Epic"),
            os.path.expandvars(r"%USERPROFILE%\Documents\Fortnite"),
            os.path.expandvars(r"%USERPROFILE%\Documents\Unreal Engine")
        ]
        
        launcher_saved = os.path.expandvars(r"%LOCALAPPDATA%\EpicGamesLauncher\Saved")
        if os.path.exists(launcher_saved):
            for file in os.listdir(launcher_saved):
                if file.startswith("webcache"):
                    try:
                        file_path = os.path.join(launcher_saved, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except:
                        pass
        
        temp = os.path.expandvars(r"%TEMP%")
        for root, dirs, files in os.walk(temp):
            for file in files:
                if "epic" in file.lower() or "fortnite" in file.lower() or "unreal" in file.lower():
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
        
        messagebox.showwarning("Spoofer", "Logs successfully cleaned!")
    except Exception as e:
        messagebox.showerror("Spoofer", "Unknown ERROR!")

def dm_creator():
    webbrowser.open(url="https://t.me/DeIive")



    

    

menu.mainloop()