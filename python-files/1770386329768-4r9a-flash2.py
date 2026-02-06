import time
import ctypes
import requests
import random
import string
from ctypes import wintypes

random_title = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
ctypes.windll.kernel32.SetConsoleTitleW(random_title)

PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

kernel32 = ctypes.windll.kernel32
RPM = kernel32.ReadProcessMemory
WPM = kernel32.WriteProcessMemory

def get_offsets():
    off = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
    cl = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
    return off, cl

offsets, client_data = get_offsets()
dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
m_flFlashDuration = client_data['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_flFlashDuration']

import pymem
try:
    pm = pymem.Pymem("cs2.exe")
    client_base = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
    pid = pm.process_id
    
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION, False, pid)
    print(f"[{random_title}] Active. Delay: 0.1s")
except:
    print("Игра не найдена.")
    exit()

def read_ptr(addr):
    buffer = ctypes.c_longlong()
    RPM(handle, ctypes.c_void_p(addr), ctypes.byref(buffer), ctypes.sizeof(buffer), None)
    return buffer.value

def read_float(addr):
    buffer = ctypes.c_float()
    RPM(handle, ctypes.c_void_p(addr), ctypes.byref(buffer), ctypes.sizeof(buffer), None)
    return buffer.value

def write_float(addr, value):
    buffer = ctypes.c_float(value)
    WPM(handle, ctypes.c_void_p(addr), ctypes.byref(buffer), ctypes.sizeof(buffer), None)

while True:
    try:
        local_player = read_ptr(client_base + dwLocalPlayerPawn)
        
        if local_player:
            flash_addr = local_player + m_flFlashDuration
            flash_dur = read_float(flash_addr)

            if flash_dur > 0.0:
                write_float(flash_addr, 0.0)

    except Exception:
        pass

    time.sleep(0.1)