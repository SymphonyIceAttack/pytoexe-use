#!/usr/bin/env python3
"""
Reaper's Tweaks v3.2 — Windows Performance Optimizer
A desktop GUI application that applies real Windows tweaks via CMD/PowerShell/Registry.
Run as Administrator for full functionality.

Requirements:
    pip install customtkinter psutil

To build EXE:
    See BUILD_EXE.bat in the same folder.
"""

import customtkinter as ctk
import subprocess
import threading
import os
import sys
import ctypes
import datetime
import re
import time

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ════════════════════════════════════════════════════════════
#  ADMIN CHECK & ELEVATION
# ════════════════════════════════════════════════════════════

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

# ════════════════════════════════════════════════════════════
#  COMMAND RUNNER
# ════════════════════════════════════════════════════════════

def run_cmd(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        output = result.stdout.strip() or result.stderr.strip() or "Done"
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def run_ps(script):
    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{script}"'
    return run_cmd(cmd)

# ════════════════════════════════════════════════════════════
#  THEME COLORS
# ════════════════════════════════════════════════════════════

COLORS = {
    "bg": "#0a0a0a", "sidebar": "#0d0d0d", "card": "#111111",
    "card_border": "#1e1e1e", "header": "#111111",
    "text": "#e8e8e8", "text_dim": "#555555", "text_mid": "#999999",
    "accent": "#ffffff", "hover": "#1a1a1a",
    "success": "#4ade80", "warning": "#fbbf24", "error": "#f87171",
    "ascension": "#a78bfa",
    "bar_cpu": "#60a5fa",   # blue
    "bar_ram": "#34d399",   # green
    "bar_gpu": "#f472b6",   # pink
    "bar_temp": "#fb923c",  # orange
}

# ════════════════════════════════════════════════════════════
#  TWEAK DEFINITIONS
# ════════════════════════════════════════════════════════════

POWER_TWEAKS = [
    ("USB Selective Suspend", "USB devices never sleep",
     "powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 && powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0",
     "powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1"),
    ("PCI-E Link State Power Mgmt", "GPU stays at full PCIe bandwidth",
     "powercfg /setacvalueindex SCHEME_CURRENT 501a4d13-42af-4429-9fd1-a8218c268e20 ee12f906-d277-404b-b6da-e5fa1a576df5 0 && powercfg /setdcvalueindex SCHEME_CURRENT 501a4d13-42af-4429-9fd1-a8218c268e20 ee12f906-d277-404b-b6da-e5fa1a576df5 0",
     "powercfg /setacvalueindex SCHEME_CURRENT 501a4d13-42af-4429-9fd1-a8218c268e20 ee12f906-d277-404b-b6da-e5fa1a576df5 1"),
    ("CPU Idle States (C-States)", "No wake-up latency spikes",
     "powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c 100 && powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 bc5038f7-23e0-4960-96da-33abaf5935ec 100",
     "powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c 5"),
    ("Core Parking", "All cores stay online always",
     'powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 100 && reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerSettings\\54533251-82be-4824-96c1-47b60b740d00\\0cc5b647-c1df-4637-891a-dec35c318583" /v ValueMax /t REG_DWORD /d 0 /f',
     "powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 50"),
    ("Hard Disk Sleep", "No spindown delays",
     "powercfg /setacvalueindex SCHEME_CURRENT 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e 0",
     "powercfg /setacvalueindex SCHEME_CURRENT 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e 1200"),
    ("Display Sleep", "Set to never",
     "powercfg /change monitor-timeout-ac 0",
     "powercfg /change monitor-timeout-ac 10"),
    ("System Sleep / Hibernate", "Disabled for zero interruption",
     "powercfg /change standby-timeout-ac 0 && powercfg /change hibernate-timeout-ac 0 && powercfg /hibernate off",
     "powercfg /change standby-timeout-ac 30 && powercfg /hibernate on"),
]

CPU_UNIVERSAL = [
    ("HPET Disable", "Use RDTSC for lower latency",
     "bcdedit /set useplatformclock false && bcdedit /set disabledynamictick yes",
     "bcdedit /set useplatformclock true && bcdedit /set disabledynamictick no"),
    ("Timer Resolution 0.5ms", "Smoother frame pacing",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v GlobalTimerResolutionRequests /t REG_DWORD /d 1 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v GlobalTimerResolutionRequests /f'),
    ("Win32 Priority Separation", "Max foreground boost (0x26)",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f',
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 2 /f'),
    ("DPC Latency Fix", "Eliminate deferred procedure spikes",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v DpcWatchdogProfileOffset /t REG_DWORD /d 0 /f && reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v DpcTimeout /t REG_DWORD /d 0 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v DpcWatchdogProfileOffset /f'),
    ("Game Priority (High)", "GPU Priority 8, CPU Priority 6",
     'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
     'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 20 /f'),
]

CPU_AMD = [
    ("CPPC Preferred Cores", "OS routes threads to fastest cores",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AmdPPM\\Parameters" /v CppcPreferredCores /t REG_DWORD /d 1 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AmdPPM\\Parameters" /v CppcPreferredCores /f'),
    ("Cool'n'Quiet Disable", "Disable clock throttling at idle",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AmdPPM\\Parameters" /v EistEnable /t REG_DWORD /d 0 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\AmdPPM\\Parameters" /v EistEnable /f'),
]

CPU_INTEL = [
    ("SpeedStep Disable", "Disable dynamic frequency scaling",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\intelppm\\Parameters" /v EistEnable /t REG_DWORD /d 0 /f',
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\intelppm\\Parameters" /v EistEnable /t REG_DWORD /d 1 /f'),
    ("Turbo Boost Enable", "Allow sustained boost clocks",
     "powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 0",
     "powercfg /setacvalueindex SCHEME_CURRENT 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 1"),
    ("Speed Shift (HWP)", "Hardware-managed P-state transitions",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\intelppm\\Parameters" /v HWPEnable /t REG_DWORD /d 1 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\intelppm\\Parameters" /v HWPEnable /f'),
]

GPU_UNIVERSAL = [
    ("HAGS (HW GPU Scheduling)", "Reduces CPU dispatch overhead",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f',
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 1 /f'),
    ("Fullscreen Optimizations Off", "True exclusive fullscreen",
     'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f && reg add "HKCU\\System\\GameConfigStore" /v GameDVR_HonorUserFSEBehaviorMode /t REG_DWORD /d 1 /f && reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehavior /t REG_DWORD /d 2 /f',
     'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 0 /f'),
    ("Game DVR / Game Bar Off", "Remove recording overhead",
     'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f && reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR" /v AllowGameDVR /t REG_DWORD /d 0 /f',
     'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 1 /f'),
    ("TDR Delay Increase", "Prevent GPU timeout crashes",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 10 /f',
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v TdrDelay /t REG_DWORD /d 2 /f'),
]

MEMORY_TWEAKS = [
    ("SysMain / Superfetch Off", "No benefit on SSD, wastes RAM",
     "sc stop SysMain && sc config SysMain start= disabled",
     "sc config SysMain start= auto && sc start SysMain"),
    ("Last-Access Timestamps Off", "Stop updating file access times",
     "fsutil behavior set DisableLastAccess 1",
     "fsutil behavior set DisableLastAccess 0"),
    ("Large Page Support", "2 MB pages for heavy workloads",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v LargePageMinimum /t REG_DWORD /d 1 /f',
     'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v LargePageMinimum /f'),
    ("Clear Pagefile on Shutdown", "Fresh state each boot",
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v ClearPageFileAtShutdown /t REG_DWORD /d 1 /f',
     'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v ClearPageFileAtShutdown /t REG_DWORD /d 0 /f'),
]

NETWORK_TWEAKS = [
    ("TCP Auto-Tuning", "Scale receive window dynamically",
     "netsh int tcp set global autotuninglevel=normal",
     "netsh int tcp set global autotuninglevel=disabled"),
    ("QoS Bandwidth Reserve Off", "Reclaim 20%% reserved bandwidth",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched" /v NonBestEffortLimit /t REG_DWORD /d 0 /f',
     'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched" /v NonBestEffortLimit /f'),
    ("RSS (Receive Side Scaling)", "Spread NIC load across cores",
     "netsh int tcp set global rss=enabled",
     "netsh int tcp set global rss=disabled"),
    ("ECN Disable", "Disable explicit congestion notify",
     "netsh int tcp set global ecncapability=disabled",
     "netsh int tcp set global ecncapability=default"),
    ("Network Throttling Off", "Remove bandwidth limiting",
     'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
     'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f'),
]

STORAGE_TWEAKS = [
    ("8.3 Filename Generation Off", "Remove legacy short-name overhead",
     "fsutil behavior set disable8dot3 1", "fsutil behavior set disable8dot3 0"),
    ("Last-Access Timestamps Off", "Reduces disk writes",
     "fsutil behavior set DisableLastAccess 1", "fsutil behavior set DisableLastAccess 0"),
    ("NTFS Memory Usage High", "Better file system performance",
     "fsutil behavior set memoryusage 2", "fsutil behavior set memoryusage 1"),
    ("SSD TRIM Enabled", "Maintain SSD write performance",
     "fsutil behavior set DisableDeleteNotify 0", "fsutil behavior set DisableDeleteNotify 1"),
]

SERVICES_LIST = [
    ("Windows Search", "WSearch", "Heavy CPU/disk usage"),
    ("SysMain (Superfetch)", "SysMain", "No benefit on SSD"),
    ("DiagTrack", "DiagTrack", "Telemetry relay service"),
    ("Print Spooler", "Spooler", "Disable if no printer"),
    ("Remote Registry", "RemoteRegistry", "Security + performance"),
    ("Xbox Live Auth", "XblAuthManager", "Xbox feature"),
    ("Xbox Live Game Save", "XblGameSave", "Xbox feature"),
    ("Xbox Networking", "XboxNetApiSvc", "Xbox feature"),
    ("Fax", "Fax", "Safe to disable"),
    ("Error Reporting", "WerSvc", "Sends crash data"),
    ("Windows Update", "wuauserv", "Prevent background throttle"),
]

PRIVACY_TWEAKS = [
    ("Diagnostic Data Off", "Block all uploads to Microsoft",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 3 /f'),
    ("Advertising ID Off", "Disable per-app ad targeting",
     'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
     'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 1 /f'),
    ("Activity History Off", "No timeline collection",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f && reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v PublishUserActivities /t REG_DWORD /d 0 /f',
     'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableActivityFeed /f'),
    ("Location Services Off", "System-wide location disabled",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 1 /f',
     'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" /v DisableLocation /f'),
    ("Cortana Off", "Voice + search logging removed",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f',
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 1 /f'),
    ("Edge Telemetry Off", "Block browser data collection",
     'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge" /v MetricsReportingEnabled /t REG_DWORD /d 0 /f && reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge" /v SendSiteInfoToImproveServices /t REG_DWORD /d 0 /f',
     'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge" /v MetricsReportingEnabled /f'),
]

BLOATWARE = [
    ("Microsoft Teams", "*MicrosoftTeams*"), ("Cortana", "*Microsoft.549981C3F5F10*"),
    ("Xbox App", "*XboxApp*"), ("Xbox Game Bar", "*XboxGamingOverlay*"),
    ("Xbox Identity", "*XboxIdentityProvider*"), ("Xbox Speech", "*XboxSpeechToTextOverlay*"),
    ("Groove Music", "*ZuneMusic*"), ("Movies & TV", "*ZuneVideo*"),
    ("Mail & Calendar", "*windowscommunicationsapps*"), ("Microsoft News", "*BingNews*"),
    ("Solitaire", "*MicrosoftSolitaireCollection*"), ("Mixed Reality", "*MixedReality.Portal*"),
    ("OneDrive", "*OneDriveSync*"), ("Paint 3D", "*MSPaint*"),
    ("People", "*People*"), ("Phone Link", "*YourPhone*"),
    ("Skype", "*SkypeApp*"), ("Feedback Hub", "*WindowsFeedbackHub*"),
    ("Maps", "*WindowsMaps*"), ("Weather", "*BingWeather*"),
    ("Camera", "*WindowsCamera*"), ("Get Help", "*GetHelp*"),
    ("Tips", "*Getstarted*"),
]

ASCENSION_KILL = [
    "SearchUI.exe", "SearchApp.exe", "Cortana.exe", "OneDrive.exe",
    "PhoneExperienceHost.exe", "YourPhone.exe", "GameBar.exe",
    "GameBarPresenceWriter.exe", "MicrosoftEdgeUpdate.exe",
    "BackgroundTransferHost.exe", "backgroundTaskHost.exe",
    "SettingSyncHost.exe", "SpeechRuntime.exe", "TextInputHost.exe",
    "MsSpellCheckingHost.exe", "Widgets.exe", "WidgetService.exe",
    "SecurityHealthSystray.exe", "TabTip.exe", "msedgewebview2.exe",
]

ASCENSION_SVCS = [
    "WSearch", "SysMain", "DiagTrack", "dmwappushservice", "Spooler",
    "RemoteRegistry", "WerSvc", "XblAuthManager", "XblGameSave",
    "XboxNetApiSvc", "Fax", "MapsBroker", "lfsvc", "WbioSrvc",
    "WMPNetworkSvc", "wisvc", "TabletInputService", "wuauserv", "UsoSvc",
]


# ════════════════════════════════════════════════════════════
#  HARDWARE MONITOR  (psutil-based, robust fallback)
# ════════════════════════════════════════════════════════════

class HardwareMonitor:
    """Collects CPU, RAM, GPU, temperature, network and process data."""

    def __init__(self):
        self._last_net_io = None
        self._last_net_time = None
        # Prime psutil cpu_percent (first call always returns 0.0)
        if HAS_PSUTIL:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(percpu=True, interval=None)

    # ── CPU ─────────────────────────────────────────────────
    def cpu_overall(self) -> float:
        if HAS_PSUTIL:
            return psutil.cpu_percent(interval=0.3)
        return self._wmic_cpu()

    def cpu_per_core(self) -> list:
        """Returns list of per-core usage floats (logical cores)."""
        if HAS_PSUTIL:
            return psutil.cpu_percent(percpu=True, interval=0.3)
        return []

    def cpu_freq_mhz(self) -> int:
        """Current CPU frequency in MHz."""
        if HAS_PSUTIL:
            try:
                freq = psutil.cpu_freq()
                if freq:
                    return int(freq.current)
            except:
                pass
        return 0

    def cpu_count(self):
        """(physical_cores, logical_cores)"""
        if HAS_PSUTIL:
            try:
                phys = psutil.cpu_count(logical=False) or 0
                logi = psutil.cpu_count(logical=True) or 0
                return phys, logi
            except:
                pass
        return 0, 0

    def _wmic_cpu(self) -> float:
        _, out = run_cmd("wmic cpu get LoadPercentage /format:value")
        for l in out.split("\n"):
            if "LoadPercentage=" in l:
                try:
                    return float(l.split("=", 1)[1].strip())
                except:
                    pass
        return 0.0

    # ── RAM ─────────────────────────────────────────────────
    def ram_stats(self):
        """Returns (pct, used_gb, total_gb)."""
        if HAS_PSUTIL:
            m = psutil.virtual_memory()
            return m.percent, m.used / (1024**3), m.total / (1024**3)
        return self._wmic_ram()

    def _wmic_ram(self):
        _, out = run_cmd("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /format:value")
        total_kb = free_kb = 0
        for l in out.split("\n"):
            if "TotalVisibleMemorySize=" in l:
                try: total_kb = int(l.split("=", 1)[1].strip())
                except: pass
            if "FreePhysicalMemory=" in l:
                try: free_kb = int(l.split("=", 1)[1].strip())
                except: pass
        if total_kb:
            pct = (1 - free_kb / total_kb) * 100
            used = (total_kb - free_kb) / (1024 * 1024)
            total = total_kb / (1024 * 1024)
            return pct, used, total
        return 0.0, 0.0, 0.0

    # ── GPU ─────────────────────────────────────────────────
    def gpu_stats(self):
        """Returns (name, load_pct, vram_used_mb, vram_total_mb, temp_c).
        Tries nvidia-smi first, then WMI, then returns placeholders."""
        # --- NVIDIA via nvidia-smi ---
        try:
            r = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=4
            )
            if r.returncode == 0 and r.stdout.strip():
                parts = [p.strip() for p in r.stdout.strip().split(",")]
                if len(parts) >= 5:
                    return (
                        parts[0],
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3]),
                        float(parts[4]),
                    )
        except FileNotFoundError:
            pass
        except Exception:
            pass

        # --- AMD via PowerShell + WMI ---
        try:
            ps_cmd = (
                "Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine "
                "| Select-Object -ExpandProperty UtilizationPercentage "
                "| Measure-Object -Average | Select-Object -ExpandProperty Average"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0 and r.stdout.strip():
                load = float(r.stdout.strip())
                return ("GPU", load, 0.0, 0.0, 0.0)
        except Exception:
            pass

        return ("GPU", 0.0, 0.0, 0.0, 0.0)

    # ── Temperature ─────────────────────────────────────────
    def cpu_temp(self) -> float:
        """Returns CPU package temp in °C, or 0 if unavailable."""
        if HAS_PSUTIL:
            try:
                temps = psutil.sensors_temperatures()
                if not temps:
                    return 0.0
                priority = ["coretemp", "k10temp", "cpu_thermal", "acpitz"]
                for key in priority:
                    if key in temps and temps[key]:
                        return float(temps[key][0].current)
                # Fall back to first available
                for entries in temps.values():
                    if entries:
                        return float(entries[0].current)
            except Exception:
                pass
        # PowerShell WMI fallback
        try:
            ps = (
                "(Get-CimInstance -Namespace 'root/WMI' -ClassName MSAcpi_ThermalZoneTemperature "
                "| Select-Object -First 1).CurrentTemperature"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, timeout=4
            )
            if r.returncode == 0 and r.stdout.strip().isdigit():
                return (int(r.stdout.strip()) - 2732) / 10.0
        except Exception:
            pass
        return 0.0

    # ── Network speed ────────────────────────────────────────
    def net_speed(self):
        """Returns (send_mb_s, recv_mb_s) since last call."""
        if not HAS_PSUTIL:
            return 0.0, 0.0
        try:
            now = time.time()
            counters = psutil.net_io_counters()
            if self._last_net_io and self._last_net_time:
                dt = now - self._last_net_time
                if dt > 0:
                    sent = (counters.bytes_sent - self._last_net_io.bytes_sent) / dt / (1024 * 1024)
                    recv = (counters.bytes_recv - self._last_net_io.bytes_recv) / dt / (1024 * 1024)
                    self._last_net_io = counters
                    self._last_net_time = now
                    return round(sent, 2), round(recv, 2)
            self._last_net_io = counters
            self._last_net_time = now
        except Exception:
            pass
        return 0.0, 0.0

    # ── Disk usage ───────────────────────────────────────────
    def disk_usage(self):
        """Returns (used_pct, read_mb_s, write_mb_s) for the C: drive."""
        pct = 0.0
        if HAS_PSUTIL:
            try:
                du = psutil.disk_usage("C:\\")
                pct = du.percent
            except Exception:
                pass
        return pct

    # ── Top processes ────────────────────────────────────────
    def top_processes(self, n=5):
        """Returns list of (name, cpu_pct) sorted descending."""
        if HAS_PSUTIL:
            try:
                procs = []
                for p in psutil.process_iter(["name", "cpu_percent"]):
                    try:
                        c = p.info.get("cpu_percent") or 0.0
                        if c > 0:
                            procs.append((p.info["name"], c))
                    except Exception:
                        pass
                procs.sort(key=lambda x: x[1], reverse=True)
                return procs[:n]
            except Exception:
                pass
        # PowerShell fallback
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 "
                 "| ForEach-Object { $_.ProcessName + '|' + [math]::Round($_.CPU,1) }"],
                capture_output=True, text=True, timeout=8
            )
            procs = []
            for line in result.stdout.strip().split("\n"):
                parts = line.strip().split("|")
                if len(parts) == 2:
                    try:
                        procs.append((parts[0].strip() + ".exe", float(parts[1].strip())))
                    except Exception:
                        pass
            return procs[:n]
        except Exception:
            pass
        return []


# ════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ════════════════════════════════════════════════════════════

class ReapersTweaks(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reaper's Tweaks v3.2")
        self.geometry("1100x740")
        self.minsize(950, 620)
        self.configure(fg_color=COLORS["bg"])
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.log_file = os.path.join(os.path.expanduser("~"), "Desktop", "ReapersTweaks_Log.txt")
        self.ascension_active = False
        self.prev_power_guid = None
        self.tweak_vars = {}
        self._hw = HardwareMonitor()
        self.total_ram_gb = 16
        self._boot_time = None
        self._gpu_name_cache = None
        self._build_header()
        self._build_body()
        self._show_page("overview")
        self._load_system_info()
        self._start_live_stats()

    # ── Header ──────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, height=48, fg_color=COLORS["header"], corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="●", text_color=COLORS["accent"], font=("Arial", 10)).pack(side="left", padx=(16, 6))
        ctk.CTkLabel(header, text="REAPER'S TWEAKS", font=("Consolas", 16, "bold"), text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(header, text="v3.2", font=("Consolas", 10), text_color=COLORS["text_dim"]).pack(side="left", padx=(6, 0))
        self.status_label = ctk.CTkLabel(header, text="READY", font=("Consolas", 10), text_color=COLORS["success"])
        self.status_label.pack(side="right", padx=16)
        admin_text = "ADMIN" if is_admin() else "NO ADMIN"
        admin_color = COLORS["success"] if is_admin() else COLORS["error"]
        ctk.CTkLabel(header, text=admin_text, font=("Consolas", 10), text_color=admin_color).pack(side="right", padx=8)
        self.hdr_clock = ctk.CTkLabel(header, text="00:00:00", font=("Consolas", 11), text_color=COLORS["text_dim"])
        self.hdr_clock.pack(side="right", padx=12)
        self.hdr_net = ctk.CTkLabel(header, text="↑0 ↓0 MB/s", font=("Consolas", 11), text_color=COLORS["text_dim"])
        self.hdr_net.pack(side="right", padx=4)
        self.hdr_ram = ctk.CTkLabel(header, text="ram --%", font=("Consolas", 11), text_color=COLORS["text_dim"])
        self.hdr_ram.pack(side="right", padx=4)
        self.hdr_cpu = ctk.CTkLabel(header, text="cpu --%", font=("Consolas", 11), text_color=COLORS["text_dim"])
        self.hdr_cpu.pack(side="right", padx=4)

    # ── Body / sidebar ──────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=COLORS["bg"], corner_radius=0)
        body.pack(fill="both", expand=True)
        self.sidebar = ctk.CTkFrame(body, width=180, fg_color=COLORS["sidebar"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.nav_buttons = {}
        nav = [
            ("MONITOR", None), ("Overview", "overview"),
            ("HARDWARE", None), ("CPU Tweaks", "cpu"), ("GPU Tweaks", "gpu"), ("Memory", "memory"),
            ("Network", "network"), ("Storage", "storage"),
            ("SYSTEM", None), ("Debloater", "debloat"),
            ("Services", "services"), ("Privacy", "privacy"), ("Cleanup", "cleanup"),
            ("GAMING", None), ("FPS Tweaks", "fps"),
            ("", None), ("ASCENSION", "ascension"),
        ]
        for label, pid in nav:
            if pid is None:
                ctk.CTkLabel(self.sidebar, text=label, font=("Consolas", 9),
                              text_color=COLORS["text_dim"], anchor="w").pack(fill="x", padx=16, pady=(12, 2))
            else:
                btn = ctk.CTkButton(
                    self.sidebar, text=label, anchor="w", font=("Segoe UI", 13),
                    fg_color="transparent", text_color=COLORS["text_dim"], hover_color=COLORS["hover"],
                    height=32, corner_radius=4, command=lambda p=pid: self._show_page(p)
                )
                btn.pack(fill="x", padx=8, pady=1)
                self.nav_buttons[pid] = btn
        self.content = ctk.CTkFrame(body, fg_color=COLORS["bg"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages = {}
        self._build_overview_page()
        self._build_cpu_page()
        self._build_gpu_page()
        self._build_memory_page()
        self._build_network_page()
        self._build_storage_page()
        self._build_debloat_page()
        self._build_services_page()
        self._build_privacy_page()
        self._build_cleanup_page()
        self._build_fps_page()
        self._build_ascension_page()

    def _show_page(self, page_id):
        for f in self.pages.values():
            f.pack_forget()
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True, padx=20, pady=16)
        for nid, btn in self.nav_buttons.items():
            btn.configure(
                text_color=COLORS["accent"] if nid == page_id else COLORS["text_dim"],
                fg_color=COLORS["hover"] if nid == page_id else "transparent",
            )

    def _make_page(self, pid, title):
        frame = ctk.CTkScrollableFrame(self.content, fg_color=COLORS["bg"],
                                        scrollbar_button_color=COLORS["card_border"])
        self.pages[pid] = frame
        ctk.CTkLabel(frame, text=title.upper(), font=("Consolas", 13, "bold"),
                      text_color=COLORS["accent"], anchor="w").pack(fill="x", pady=(0, 14))
        return frame

    def _make_card(self, parent, title=None):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=6,
                             border_width=1, border_color=COLORS["card_border"])
        card.pack(fill="x", pady=(0, 10))
        if title:
            ctk.CTkLabel(card, text=title.upper(), font=("Consolas", 10, "bold"),
                          text_color="#777777", anchor="w").pack(fill="x", padx=14, pady=(10, 4))
        return card

    def _make_tweak_row(self, parent, name, desc, on_cmd, off_cmd, default_on=False):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=44)
        row.pack(fill="x", padx=14, pady=2)
        row.pack_propagate(False)
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left, text=name, font=("Segoe UI", 13, "bold"),
                      text_color=COLORS["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(left, text=desc, font=("Segoe UI", 10),
                      text_color=COLORS["text_dim"], anchor="w").pack(fill="x")
        var = ctk.BooleanVar(value=default_on)
        key = name + "_" + str(id(parent))
        self.tweak_vars[key] = (var, on_cmd, off_cmd)
        ctk.CTkSwitch(
            row, text="", variable=var, width=44,
            button_color=COLORS["accent"], button_hover_color="#ccc",
            progress_color=COLORS["text_dim"], fg_color=COLORS["card_border"],
            command=lambda k=key: self._toggle_tweak(k)
        ).pack(side="right")
        return var

    def _toggle_tweak(self, key):
        var, on_cmd, off_cmd = self.tweak_vars[key]
        cmd = on_cmd if var.get() else off_cmd
        self._run_threaded(cmd, key.split("_")[0])

    def _make_log(self, parent):
        log = ctk.CTkTextbox(
            parent, height=80, fg_color="#080808", font=("Consolas", 10),
            text_color=COLORS["text_dim"], border_width=1,
            border_color=COLORS["card_border"], corner_radius=4, state="disabled"
        )
        log.pack(fill="x", padx=0, pady=(8, 12))
        return log

    def _log(self, log_widget, msg, level="info"):
        if log_widget is None:
            return
        log_widget.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        log_widget.insert("end", f"[{ts}] {msg}\n")
        log_widget.see("end")
        log_widget.configure(state="disabled")
        try:
            with open(self.log_file, "a") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    def _run_threaded(self, cmd, label="cmd", log_widget=None, callback=None):
        def worker():
            self.status_label.configure(text="APPLYING...", text_color=COLORS["warning"])
            ok, out = run_cmd(cmd)
            if log_widget:
                self._log(log_widget, f"{label}: {'OK' if ok else 'FAIL'}", "ok" if ok else "error")
            self.status_label.configure(
                text="READY" if ok else "ERROR",
                text_color=COLORS["success"] if ok else COLORS["error"]
            )
            if callback:
                callback(ok, out)
        threading.Thread(target=worker, daemon=True).start()

    # ────────────────────────────────────────────────────────
    #  OVERVIEW PAGE
    # ────────────────────────────────────────────────────────
    def _build_overview_page(self):
        page = self._make_page("overview", "Overview")

        # ── Top 4 stat cards ──────────────────────────────
        stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))
        stats_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")

        self.stat_cards = {}
        stat_defs = [
            ("CPU",  "--%%", "-- cores",    COLORS["bar_cpu"]),
            ("RAM",  "--%%", "-- / -- GB",  COLORS["bar_ram"]),
            ("GPU",  "--%%", "-- VRAM",     COLORS["bar_gpu"]),
            ("TEMP", "--°",  "CPU package", COLORS["bar_temp"]),
        ]
        for i, (label, val, sub, bar_color) in enumerate(stat_defs):
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["card"], corner_radius=6,
                                 border_width=1, border_color=COLORS["card_border"])
            card.grid(row=0, column=i, padx=(0 if i == 0 else 4, 0), sticky="nsew")
            ctk.CTkLabel(card, text=label, font=("Consolas", 9),
                          text_color=COLORS["text_dim"], anchor="w").pack(fill="x", padx=12, pady=(10, 0))
            val_lbl = ctk.CTkLabel(card, text=val, font=("Consolas", 28, "bold"),
                                    text_color=bar_color, anchor="w")
            val_lbl.pack(fill="x", padx=12, pady=(2, 0))
            bar_bg = ctk.CTkFrame(card, fg_color="#1a1a1a", height=4, corner_radius=2)
            bar_bg.pack(fill="x", padx=12, pady=(6, 0))
            bar_bg.pack_propagate(False)
            bar_fill = ctk.CTkFrame(bar_bg, fg_color=bar_color, height=4, corner_radius=2, width=0)
            bar_fill.place(x=0, y=0, relheight=1.0, relwidth=0.0)
            sub_lbl = ctk.CTkLabel(card, text=sub, font=("Consolas", 10),
                                    text_color=COLORS["text_dim"], anchor="w")
            sub_lbl.pack(fill="x", padx=12, pady=(4, 10))
            self.stat_cards[label.lower()] = {"val": val_lbl, "bar": bar_fill, "sub": sub_lbl}

        # ── CPU per-core bars ─────────────────────────────
        core_card = self._make_card(page, "CPU Core Usage")
        self._core_bar_frame = ctk.CTkFrame(core_card, fg_color="transparent")
        self._core_bar_frame.pack(fill="x", padx=14, pady=(4, 10))
        self._core_bars = []   # list of (pct_label, bar_fill)
        self._core_bars_built = False

        # ── Middle row: Score + Processes + Net ───────────
        mid_frame = ctk.CTkFrame(page, fg_color="transparent")
        mid_frame.pack(fill="x", pady=(0, 10))
        mid_frame.columnconfigure(0, weight=1, uniform="mid")
        mid_frame.columnconfigure(1, weight=2, uniform="mid")
        mid_frame.columnconfigure(2, weight=1, uniform="mid")

        # Reaper Score
        score_card = ctk.CTkFrame(mid_frame, fg_color=COLORS["card"], corner_radius=6,
                                   border_width=1, border_color=COLORS["card_border"])
        score_card.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        ctk.CTkLabel(score_card, text="REAPER SCORE", font=("Consolas", 9),
                      text_color=COLORS["text_dim"]).pack(pady=(14, 0))
        self.score_val = ctk.CTkLabel(score_card, text="--", font=("Consolas", 52, "bold"),
                                       text_color=COLORS["accent"])
        self.score_val.pack(pady=(4, 0))
        ctk.CTkLabel(score_card, text="PERFORMANCE / 100", font=("Consolas", 9),
                      text_color=COLORS["text_dim"]).pack(pady=(2, 4))
        self.uptime_lbl = ctk.CTkLabel(score_card, text="uptime: --", font=("Consolas", 9),
                                        text_color=COLORS["text_dim"])
        self.uptime_lbl.pack(pady=(0, 14))

        # Top Processes
        proc_card = ctk.CTkFrame(mid_frame, fg_color=COLORS["card"], corner_radius=6,
                                  border_width=1, border_color=COLORS["card_border"])
        proc_card.grid(row=0, column=1, padx=4, sticky="nsew")
        ctk.CTkLabel(proc_card, text="TOP PROCESSES (CPU %)", font=("Consolas", 9),
                      text_color=COLORS["text_dim"], anchor="w").pack(fill="x", padx=14, pady=(10, 6))
        self.proc_rows = []
        for _ in range(6):
            row = ctk.CTkFrame(proc_card, fg_color="transparent", height=22)
            row.pack(fill="x", padx=14, pady=1)
            row.pack_propagate(False)
            name_lbl = ctk.CTkLabel(row, text="--", font=("Consolas", 11),
                                     text_color=COLORS["text_mid"], anchor="w")
            name_lbl.pack(side="left", fill="x", expand=True)
            pct_lbl = ctk.CTkLabel(row, text="--%", font=("Consolas", 11),
                                    text_color=COLORS["text_dim"])
            pct_lbl.pack(side="right")
            self.proc_rows.append((name_lbl, pct_lbl))
        ctk.CTkLabel(proc_card, text="", font=("Consolas", 2)).pack()

        # Network speed
        net_card = ctk.CTkFrame(mid_frame, fg_color=COLORS["card"], corner_radius=6,
                                 border_width=1, border_color=COLORS["card_border"])
        net_card.grid(row=0, column=2, padx=(4, 0), sticky="nsew")
        ctk.CTkLabel(net_card, text="NETWORK", font=("Consolas", 9),
                      text_color=COLORS["text_dim"]).pack(pady=(14, 4))
        self.net_up_lbl = ctk.CTkLabel(net_card, text="↑ 0.00", font=("Consolas", 22, "bold"),
                                        text_color=COLORS["success"])
        self.net_up_lbl.pack(pady=(4, 0))
        ctk.CTkLabel(net_card, text="MB/s  SEND", font=("Consolas", 9),
                      text_color=COLORS["text_dim"]).pack()
        self.net_dn_lbl = ctk.CTkLabel(net_card, text="↓ 0.00", font=("Consolas", 22, "bold"),
                                        text_color=COLORS["bar_cpu"])
        self.net_dn_lbl.pack(pady=(10, 0))
        ctk.CTkLabel(net_card, text="MB/s  RECV", font=("Consolas", 9),
                      text_color=COLORS["text_dim"]).pack()
        self.disk_pct_lbl = ctk.CTkLabel(net_card, text="disk: --%", font=("Consolas", 9),
                                           text_color=COLORS["text_dim"])
        self.disk_pct_lbl.pack(pady=(10, 14))

        # ── System Info card ──────────────────────────────
        sys_card = self._make_card(page, "System")
        sys_inner = ctk.CTkFrame(sys_card, fg_color="transparent")
        sys_inner.pack(fill="x", padx=14, pady=(0, 10))
        sys_inner.columnconfigure(0, weight=1, uniform="sys")
        sys_inner.columnconfigure(1, weight=1, uniform="sys")

        self.sys_labels = {}
        left_items = [("OS", "Loading..."), ("CPU", "Loading..."), ("Cores", "Loading..."),
                       ("RAM", "Loading..."), ("Freq", "Loading...")]
        right_items = [("GPU", "Loading..."), ("VRAM", "--"), ("Disk C:", "Loading..."),
                        ("Power", "Loading..."), ("Uptime", "--")]

        for i, (key, val) in enumerate(left_items):
            row = ctk.CTkFrame(sys_inner, fg_color="transparent", height=22)
            row.grid(row=i, column=0, sticky="ew", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=key, font=("Consolas", 11),
                          text_color=COLORS["text_dim"], anchor="w").pack(side="left")
            v = ctk.CTkLabel(row, text=val, font=("Consolas", 11),
                              text_color=COLORS["text_mid"], anchor="e")
            v.pack(side="right", padx=(0, 10))
            self.sys_labels[key.lower()] = v

        for i, (key, val) in enumerate(right_items):
            row = ctk.CTkFrame(sys_inner, fg_color="transparent", height=22)
            row.grid(row=i, column=1, sticky="ew", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=key, font=("Consolas", 11),
                          text_color=COLORS["text_dim"], anchor="w").pack(side="left")
            v = ctk.CTkLabel(row, text=val, font=("Consolas", 11),
                              text_color=COLORS["text_mid"], anchor="e")
            v.pack(side="right")
            self.sys_labels[key.lower()] = v

        # ── Safety card ───────────────────────────────────
        rp_card = self._make_card(page, "Safety")
        bf = ctk.CTkFrame(rp_card, fg_color="transparent")
        bf.pack(fill="x", padx=14, pady=12)
        ctk.CTkButton(
            bf, text="CREATE RESTORE POINT", font=("Consolas", 11),
            fg_color="transparent", border_width=1, border_color=COLORS["warning"],
            text_color=COLORS["warning"], hover_color=COLORS["hover"],
            command=self._create_restore_point
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            bf, text="FLUSH RAM", font=("Consolas", 11),
            fg_color="transparent", border_width=1, border_color=COLORS["bar_cpu"],
            text_color=COLORS["bar_cpu"], hover_color=COLORS["hover"],
            command=self._flush_ram
        ).pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            bf, text="FLUSH DNS", font=("Consolas", 11),
            fg_color="transparent", border_width=1, border_color=COLORS["text_dim"],
            text_color=COLORS["text_dim"], hover_color=COLORS["hover"],
            command=lambda: self._run_threaded("ipconfig /flushdns", "DNS Flush")
        ).pack(side="left")

    # ── Build per-core bars dynamically ────────────────────
    def _build_core_bars(self, n_cores):
        for w in self._core_bar_frame.winfo_children():
            w.destroy()
        self._core_bars.clear()
        cols = min(n_cores, 8)  # max 8 per row
        rows_needed = (n_cores + cols - 1) // cols
        for r in range(rows_needed):
            for c in range(cols):
                idx = r * cols + c
                if idx >= n_cores:
                    break
                cell = ctk.CTkFrame(self._core_bar_frame, fg_color="transparent")
                cell.grid(row=r * 2, column=c, padx=3, pady=(4, 0), sticky="ew")
                self._core_bar_frame.columnconfigure(c, weight=1)
                lbl = ctk.CTkLabel(cell, text=f"C{idx}", font=("Consolas", 8),
                                    text_color=COLORS["text_dim"])
                lbl.pack()
                pct_lbl = ctk.CTkLabel(cell, text="0%", font=("Consolas", 9),
                                        text_color=COLORS["bar_cpu"])
                pct_lbl.pack()
                bg = ctk.CTkFrame(cell, fg_color="#1a1a1a", width=10, height=60, corner_radius=3)
                bg.pack(pady=(2, 0))
                bg.pack_propagate(False)
                fill = ctk.CTkFrame(bg, fg_color=COLORS["bar_cpu"], width=10, corner_radius=3)
                fill.place(relx=0, rely=1.0, relwidth=1.0, relheight=0.0, anchor="sw")
                self._core_bars.append((pct_lbl, fill))
        self._core_bars_built = True

    def _update_core_bars(self, per_core):
        if not per_core:
            return
        if not self._core_bars_built or len(self._core_bars) != len(per_core):
            self.after(0, lambda: self._build_core_bars(len(per_core)))
            return
        for i, (pct_lbl, fill) in enumerate(self._core_bars):
            if i < len(per_core):
                v = per_core[i]
                pct_lbl.configure(text=f"{v:.0f}%")
                fill.place(relx=0, rely=1.0, relwidth=1.0, relheight=v / 100, anchor="sw")

    # ── System info (static, loaded once) ──────────────────
    def _load_system_info(self):
        def worker():
            def _set(key, val):
                self.after(0, lambda: self.sys_labels[key].configure(text=val)
                            if key in self.sys_labels else None)

            # CPU cores
            phys, logi = self._hw.cpu_count()
            if phys or logi:
                _set("cores", f"{phys}P / {logi}L")
                if "cpu" in self.stat_cards:
                    self.after(0, lambda: self.stat_cards["cpu"]["sub"].configure(
                        text=f"{logi} threads"))

            # Boot time / uptime
            if HAS_PSUTIL:
                try:
                    bt = datetime.datetime.fromtimestamp(psutil.boot_time())
                    self._boot_time = bt
                    _set("uptime", bt.strftime("%b %d %H:%M"))
                except Exception:
                    pass

            # GPU name from nvidia-smi or registry
            try:
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=4
                )
                if r.returncode == 0 and r.stdout.strip():
                    self._gpu_name_cache = r.stdout.strip().split("\n")[0].strip()
            except FileNotFoundError:
                pass
            except Exception:
                pass

            if not self._gpu_name_cache:
                try:
                    gpu_cmd = 'reg query "HKLM\\SYSTEM\\ControlSet001\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0000" /v DriverDesc'
                    r = subprocess.run(gpu_cmd, capture_output=True, text=True, shell=True, timeout=10)
                    for line in r.stdout.split("\n"):
                        if "DriverDesc" in line and "REG_SZ" in line:
                            self._gpu_name_cache = line.split("REG_SZ")[-1].strip()
                            break
                except Exception:
                    pass

            if self._gpu_name_cache:
                _set("gpu", self._gpu_name_cache[:26])

            # Disk C: usage
            try:
                pct = self._hw.disk_usage()
                if pct:
                    _set("disk c:", f"{pct:.1f}% used")
            except Exception:
                pass

            # Power plan
            try:
                r = subprocess.run("powercfg /getactivescheme", capture_output=True, text=True,
                                    shell=True, timeout=5)
                out = r.stdout.strip()
                if "(" in out and ")" in out:
                    _set("power", out.split("(")[1].split(")")[0][:20])
            except Exception:
                pass

            # OS + CPU name + RAM via systeminfo
            try:
                r = subprocess.run("systeminfo", capture_output=True, text=True, shell=True, timeout=45)
                out = r.stdout
                got_cpu = False
                for line in out.split("\n"):
                    line = line.strip()
                    if line.startswith("OS Name:"):
                        ov = line.split(":", 1)[-1].strip().replace("Microsoft ", "")
                        _set("os", ov[:28])
                    elif "Total Physical Memory:" in line:
                        ram = line.split(":", 1)[-1].strip()
                        _set("ram", ram[:18])
                        try:
                            num = "".join(c for c in ram if c.isdigit() or c == ".")
                            val = float(num)
                            self.total_ram_gb = val / 1024 if val > 100 else val
                        except Exception:
                            pass
                    elif not got_cpu and (
                        "GHz" in line or "CPU" in line.upper()
                        or "AMD" in line.upper() or "Intel" in line.upper()
                    ):
                        if ":" not in line or line.startswith("["):
                            cpu_val = line.strip().lstrip("[").rstrip("]").strip()
                            if "]:" in cpu_val:
                                cpu_val = cpu_val.split("]:")[-1].strip()
                            if cpu_val:
                                _set("cpu", cpu_val[:28])
                                got_cpu = True
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    # ── Live stats loop ────────────────────────────────────
    def _start_live_stats(self):
        self._update_live_stats()

    def _update_live_stats(self):
        def worker():
            # CPU
            cpu_pct = self._hw.cpu_overall()
            per_core = self._hw.cpu_per_core()
            freq = self._hw.cpu_freq_mhz()

            # RAM
            ram_pct, ram_used, ram_total = self._hw.ram_stats()
            self.total_ram_gb = ram_total if ram_total > 0 else self.total_ram_gb

            # GPU
            gpu_name, gpu_pct, vram_used, vram_total, gpu_temp = self._hw.gpu_stats()
            if self._gpu_name_cache:
                gpu_name = self._gpu_name_cache

            # CPU temp
            cpu_temp = self._hw.cpu_temp()

            # Temp: prefer GPU temp if CPU unavailable and GPU is NVIDIA
            disp_temp = cpu_temp if cpu_temp > 0 else gpu_temp

            # Network
            net_up, net_dn = self._hw.net_speed()

            # Disk
            disk_pct = self._hw.disk_usage()

            # Processes
            procs = self._hw.top_processes(6)

            # Uptime
            uptime_str = "--"
            if HAS_PSUTIL:
                try:
                    secs = int(time.time() - psutil.boot_time())
                    h, rem = divmod(secs, 3600)
                    m, s = divmod(rem, 60)
                    uptime_str = f"{h}h {m}m"
                except Exception:
                    pass

            self.after(0, lambda: self._apply_stats(
                cpu_pct, per_core, freq,
                ram_pct, ram_used, ram_total,
                gpu_name, gpu_pct, vram_used, vram_total,
                disp_temp, net_up, net_dn, disk_pct, procs, uptime_str
            ))

        threading.Thread(target=worker, daemon=True).start()
        self.after(2000, self._update_live_stats)

    def _apply_stats(self, cpu_pct, per_core, freq,
                     ram_pct, ram_used, ram_total,
                     gpu_name, gpu_pct, vram_used, vram_total,
                     disp_temp, net_up, net_dn, disk_pct, procs, uptime_str):

        # ── Header ──
        self.hdr_cpu.configure(text=f"cpu {cpu_pct:.0f}%")
        self.hdr_ram.configure(text=f"ram {ram_pct:.0f}%")
        self.hdr_net.configure(text=f"↑{net_up:.1f} ↓{net_dn:.1f}MB/s")
        self.hdr_clock.configure(text=datetime.datetime.now().strftime("%H:%M:%S"))

        # ── Stat cards ──
        cards = self.stat_cards

        # CPU
        cards["cpu"]["val"].configure(text=f"{cpu_pct:.0f}%")
        cards["cpu"]["bar"].place(x=0, y=0, relheight=1.0, relwidth=cpu_pct / 100)
        if freq:
            cards["cpu"]["sub"].configure(text=f"{freq / 1000:.2f} GHz")

        # RAM
        cards["ram"]["val"].configure(text=f"{ram_pct:.0f}%")
        cards["ram"]["bar"].place(x=0, y=0, relheight=1.0, relwidth=ram_pct / 100)
        cards["ram"]["sub"].configure(text=f"{ram_used:.1f} / {ram_total:.0f} GB")

        # GPU
        cards["gpu"]["val"].configure(text=f"{gpu_pct:.0f}%")
        cards["gpu"]["bar"].place(x=0, y=0, relheight=1.0, relwidth=min(gpu_pct, 100) / 100)
        if vram_total > 0:
            cards["gpu"]["sub"].configure(text=f"{vram_used:.0f}/{vram_total:.0f} MB VRAM")
        elif gpu_name and gpu_name != "GPU":
            short = gpu_name.split()[-1] if gpu_name else "GPU"
            cards["gpu"]["sub"].configure(text=short[:18])

        # Temp
        if disp_temp > 0:
            temp_color = (COLORS["error"] if disp_temp > 85
                          else COLORS["warning"] if disp_temp > 70
                          else COLORS["bar_temp"])
            cards["temp"]["val"].configure(text=f"{disp_temp:.0f}°", text_color=temp_color)
            cards["temp"]["bar"].configure(fg_color=temp_color)
            cards["temp"]["bar"].place(x=0, y=0, relheight=1.0, relwidth=min(disp_temp, 110) / 110)
        else:
            cards["temp"]["val"].configure(text="N/A")
            cards["temp"]["sub"].configure(text="sensor unavailable")

        # ── Core bars ──
        if per_core:
            self._update_core_bars(per_core)

        # ── Net / disk panel ──
        self.net_up_lbl.configure(text=f"↑ {net_up:.2f}")
        self.net_dn_lbl.configure(text=f"↓ {net_dn:.2f}")
        if disk_pct:
            self.disk_pct_lbl.configure(text=f"disk C: {disk_pct:.1f}%")

        # ── Uptime ──
        self.uptime_lbl.configure(text=f"uptime: {uptime_str}")

        # ── Reaper Score (deterministic, not random) ──
        tweaks_on = sum(1 for v, _, _ in self.tweak_vars.values() if v.get())
        max_tweaks = max(len(self.tweak_vars), 1)
        tweak_bonus = int(tweaks_on / max_tweaks * 20)
        perf_component = max(0, int((100 - cpu_pct) * 0.4 + (100 - ram_pct) * 0.2))
        score = max(40, min(99, 40 + perf_component + tweak_bonus))
        score_color = (COLORS["success"] if score >= 80
                       else COLORS["warning"] if score >= 60
                       else COLORS["error"])
        self.score_val.configure(text=str(score), text_color=score_color)

        # ── Top processes ──
        for i, (name_lbl, pct_lbl) in enumerate(self.proc_rows):
            if i < len(procs):
                name_lbl.configure(text=procs[i][0][:22])
                pct_lbl.configure(text=f"{procs[i][1]:.1f}%")
            else:
                name_lbl.configure(text="--")
                pct_lbl.configure(text="--")

        # ── Sys labels dynamic ──
        if "freq" in self.sys_labels and freq:
            self.sys_labels["freq"].configure(text=f"{freq / 1000:.2f} GHz")
        if "vram" in self.sys_labels and vram_total > 0:
            self.sys_labels["vram"].configure(text=f"{vram_used:.0f}/{vram_total:.0f} MB")
        if "uptime" in self.sys_labels:
            self.sys_labels["uptime"].configure(text=uptime_str)
        if "power" in self.sys_labels:
            # Refresh power plan every update (cheap regex)
            try:
                _, out = run_cmd("powercfg /getactivescheme")
                if "(" in out and ")" in out:
                    self.sys_labels["power"].configure(text=out.split("(")[1].split(")")[0][:20])
            except Exception:
                pass

    # ── Quick actions ──────────────────────────────────────
    def _create_restore_point(self):
        self.status_label.configure(text="CREATING RESTORE POINT...", text_color=COLORS["warning"])
        def worker():
            ok, _ = run_ps("Checkpoint-Computer -Description 'Reapers Tweaks' -RestorePointType MODIFY_SETTINGS")
            self.status_label.configure(
                text="RESTORE POINT CREATED" if ok else "FAILED",
                text_color=COLORS["success"] if ok else COLORS["error"]
            )
        threading.Thread(target=worker, daemon=True).start()

    def _flush_ram(self):
        self.status_label.configure(text="FLUSHING RAM...", text_color=COLORS["warning"])
        def worker():
            run_cmd("rundll32.exe advapi32.dll,ProcessIdleTasks")
            self.status_label.configure(text="RAM FLUSHED", text_color=COLORS["success"])
        threading.Thread(target=worker, daemon=True).start()

    # ────────────────────────────────────────────────────────
    #  OTHER PAGES (unchanged logic, same as v3.1)
    # ────────────────────────────────────────────────────────

    def _build_cpu_page(self):
        page = self._make_page("cpu", "CPU Tweaks")
        c1 = self._make_card(page, "Universal CPU Tweaks")
        for t in CPU_UNIVERSAL: self._make_tweak_row(c1, *t)
        c2 = self._make_card(page, "AMD Ryzen Specific")
        for t in CPU_AMD: self._make_tweak_row(c2, *t)
        c3 = self._make_card(page, "Intel Core Specific")
        for t in CPU_INTEL: self._make_tweak_row(c3, *t)
        self.cpu_log = self._make_log(page)
        self._log(self.cpu_log, "CPU module ready.")

    def _build_gpu_page(self):
        page = self._make_page("gpu", "GPU Tweaks")
        ctk.CTkLabel(
            page,
            text="NVIDIA/AMD specific tweaks need their control panels. Universal tweaks below work for all GPUs.",
            font=("Segoe UI", 11), text_color=COLORS["text_dim"], wraplength=700, anchor="w"
        ).pack(fill="x", pady=(0, 12))
        c1 = self._make_card(page, "Universal GPU Tweaks")
        for t in GPU_UNIVERSAL: self._make_tweak_row(c1, *t)
        self.gpu_log = self._make_log(page)
        self._log(self.gpu_log, "GPU module ready.")

    def _build_memory_page(self):
        page = self._make_page("memory", "Memory")
        c1 = self._make_card(page, "Memory Performance")
        for t in MEMORY_TWEAKS: self._make_tweak_row(c1, *t)
        self.mem_log = self._make_log(page)
        self._log(self.mem_log, "Memory module ready.")

    def _build_network_page(self):
        page = self._make_page("network", "Network")
        c1 = self._make_card(page, "TCP / UDP Optimization")
        for t in NETWORK_TWEAKS: self._make_tweak_row(c1, *t)
        nagle_card = self._make_card(page, "Nagle Algorithm")
        ctk.CTkButton(
            nagle_card, text="DISABLE NAGLE ON ALL ADAPTERS", font=("Consolas", 10),
            fg_color="transparent", border_width=1, border_color=COLORS["accent"],
            text_color=COLORS["accent"], hover_color=COLORS["hover"],
            command=self._disable_nagle
        ).pack(padx=14, pady=10, anchor="w")
        dns_card = self._make_card(page, "DNS Provider")
        df = ctk.CTkFrame(dns_card, fg_color="transparent")
        df.pack(fill="x", padx=14, pady=10)
        for n, p, s in [("Cloudflare", "1.1.1.1", "1.0.0.1"),
                         ("Google", "8.8.8.8", "8.8.4.4"),
                         ("Quad9", "9.9.9.9", "149.112.112.112")]:
            ctk.CTkButton(
                df, text=n.upper(), font=("Consolas", 10), fg_color="transparent",
                border_width=1, border_color=COLORS["card_border"], text_color=COLORS["text"],
                hover_color=COLORS["hover"], width=120,
                command=lambda pp=p, ss=s, nn=n: self._set_dns(pp, ss, nn)
            ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            df, text="FLUSH DNS", font=("Consolas", 10), fg_color="transparent",
            border_width=1, border_color=COLORS["warning"], text_color=COLORS["warning"],
            hover_color=COLORS["hover"], width=100,
            command=lambda: self._run_threaded("ipconfig /flushdns", "DNS Flush", self.net_log)
        ).pack(side="left")
        self.net_log = self._make_log(page)
        self._log(self.net_log, "Network module ready.")

    def _disable_nagle(self):
        ps = (
            "Get-NetAdapter | Where-Object Status -eq Up | ForEach-Object { "
            "$p = 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces\\' + $_.InterfaceGuid; "
            "Set-ItemProperty -Path $p -Name TcpAckFrequency -Value 1 -EA SilentlyContinue; "
            "Set-ItemProperty -Path $p -Name TCPNoDelay -Value 1 -EA SilentlyContinue; "
            "Set-ItemProperty -Path $p -Name TcpDelAckTicks -Value 0 -EA SilentlyContinue; "
            "Write-Host ('Nagle off: ' + $_.Name) }"
        )
        cmd = 'powershell -NoProfile -Command "' + ps + '"'
        self._run_threaded(cmd, "Nagle", self.net_log)

    def _set_dns(self, primary, secondary, name):
        ps = (
            f"$a = (Get-NetAdapter | Where-Object Status -eq Up | Select-Object -First 1).Name; "
            f"netsh interface ip set dns $a static {primary} primary; "
            f"netsh interface ip add dns $a {secondary} index=2"
        )
        cmd = 'powershell -NoProfile -Command "' + ps + '"'
        self._run_threaded(cmd, f"DNS ({name})", self.net_log)

    def _build_storage_page(self):
        page = self._make_page("storage", "Storage")
        c1 = self._make_card(page, "Disk Performance")
        for t in STORAGE_TWEAKS: self._make_tweak_row(c1, *t)
        self.str_log = self._make_log(page)
        self._log(self.str_log, "Storage module ready.")

    def _build_debloat_page(self):
        page = self._make_page("debloat", "Debloater")
        ctk.CTkLabel(
            page,
            text="Removing built-in apps is permanent. Create a restore point first!",
            font=("Segoe UI", 11), text_color=COLORS["warning"], wraplength=700, anchor="w"
        ).pack(fill="x", pady=(0, 12))
        card = self._make_card(page, "Select Apps to Remove")
        self.bloat_vars = {}
        for name, pkg in BLOATWARE:
            row = ctk.CTkFrame(card, fg_color="transparent", height=30)
            row.pack(fill="x", padx=14, pady=1)
            row.pack_propagate(False)
            var = ctk.BooleanVar(value=True)
            self.bloat_vars[pkg] = (var, name)
            ctk.CTkCheckBox(
                row, text=name, variable=var, font=("Segoe UI", 12), text_color=COLORS["text"],
                fg_color=COLORS["card_border"], hover_color=COLORS["hover"],
                checkmark_color=COLORS["accent"], border_color=COLORS["card_border"]
            ).pack(side="left")
        bf = ctk.CTkFrame(page, fg_color="transparent")
        bf.pack(fill="x", pady=8)
        ctk.CTkButton(bf, text="SELECT ALL", font=("Consolas", 10), fg_color="transparent",
                       border_width=1, border_color=COLORS["card_border"], text_color=COLORS["text"],
                       hover_color=COLORS["hover"], width=100,
                       command=lambda: [v.set(True) for v, _ in self.bloat_vars.values()]).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bf, text="NONE", font=("Consolas", 10), fg_color="transparent",
                       border_width=1, border_color=COLORS["card_border"], text_color=COLORS["text"],
                       hover_color=COLORS["hover"], width=80,
                       command=lambda: [v.set(False) for v, _ in self.bloat_vars.values()]).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bf, text="REMOVE SELECTED", font=("Consolas", 11, "bold"), fg_color="transparent",
                       border_width=1, border_color=COLORS["error"], text_color=COLORS["error"],
                       hover_color=COLORS["hover"], width=160,
                       command=self._run_debloat).pack(side="left")
        self.debloat_log = self._make_log(page)
        self._log(self.debloat_log, "Debloater ready.")

    def _run_debloat(self):
        selected = [(p, n) for p, (v, n) in self.bloat_vars.items() if v.get()]
        if not selected:
            self._log(self.debloat_log, "Nothing selected.")
            return
        def worker():
            self.status_label.configure(text="REMOVING...", text_color=COLORS["warning"])
            for pkg, name in selected:
                ok, _ = run_ps(f"Get-AppxPackage {pkg} | Remove-AppxPackage -EA SilentlyContinue")
                self._log(self.debloat_log, f"{'Removed' if ok else 'Skipped'}: {name}", "ok")
            self.status_label.configure(text=f"{len(selected)} APPS PROCESSED", text_color=COLORS["success"])
        threading.Thread(target=worker, daemon=True).start()

    def _build_services_page(self):
        page = self._make_page("services", "Services")
        card = self._make_card(page, "Disable for Performance")
        self.svc_vars = {}
        for display, svc, desc in SERVICES_LIST:
            row = ctk.CTkFrame(card, fg_color="transparent", height=44)
            row.pack(fill="x", padx=14, pady=2)
            row.pack_propagate(False)
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(left, text=display, font=("Segoe UI", 13), text_color=COLORS["text"], anchor="w").pack(fill="x")
            ctk.CTkLabel(left, text=desc, font=("Segoe UI", 10), text_color=COLORS["text_dim"], anchor="w").pack(fill="x")
            var = ctk.BooleanVar(value=False)
            self.svc_vars[svc] = (var, display)
            ctk.CTkSwitch(
                row, text="", variable=var, width=44, button_color=COLORS["accent"],
                button_hover_color="#ccc", progress_color=COLORS["text_dim"],
                fg_color=COLORS["card_border"],
                command=lambda s=svc: self._toggle_svc(s)
            ).pack(side="right")
        self.svc_log = self._make_log(page)
        self._log(self.svc_log, "Services module ready.")

    def _toggle_svc(self, svc):
        var, display = self.svc_vars[svc]
        if var.get():
            cmd = f"sc stop {svc} & sc config {svc} start= disabled"
        else:
            cmd = f"sc config {svc} start= auto & sc start {svc}"
        self._run_threaded(cmd, display, self.svc_log)

    def _build_privacy_page(self):
        page = self._make_page("privacy", "Privacy")
        card = self._make_card(page, "Telemetry & Tracking")
        for t in PRIVACY_TWEAKS: self._make_tweak_row(card, *t)
        self.priv_log = self._make_log(page)
        self._log(self.priv_log, "Privacy module ready.")

    def _build_cleanup_page(self):
        page = self._make_page("cleanup", "Cleanup")
        card = self._make_card(page, "Disk Cleanup")
        actions = [
            ("Clean Temp Files", "del /q /f /s %TEMP%\\* 2>nul & del /q /f /s C:\\Windows\\Temp\\* 2>nul"),
            ("Run Windows Disk Cleanup", "cleanmgr /sagerun:1"),
            ("Clear DNS Cache", "ipconfig /flushdns"),
            ("Clear Thumbnail Cache", "del /f /s /q %LocalAppData%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db 2>nul"),
            ("Run SFC Scan", "sfc /scannow"),
            ("Run DISM Cleanup", "dism /Online /Cleanup-Image /RestoreHealth"),
            ("Empty Recycle Bin", 'powershell -Command "Clear-RecycleBin -Force -EA SilentlyContinue"'),
            ("Defrag C: (HDD only)", "defrag C: /U /V"),
        ]
        self.clean_log = self._make_log(page)
        for name, cmd in actions:
            ctk.CTkButton(
                card, text=name, font=("Consolas", 11), fg_color="transparent",
                border_width=1, border_color=COLORS["card_border"], text_color=COLORS["text"],
                hover_color=COLORS["hover"], anchor="w",
                command=lambda c=cmd, n=name: self._run_threaded(c, n, self.clean_log)
            ).pack(fill="x", padx=14, pady=3)
        self._log(self.clean_log, "Cleanup module ready.")

    def _build_fps_page(self):
        page = self._make_page("fps", "FPS Tweaks")
        fn_card = self._make_card(page, "Fullscreen & Game Mode")
        fn_tweaks = [
            ("Game Mode On", "Prioritise game threads & GPU",
             'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f && reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f',
             'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 0 /f'),
            ("Disable Xbox Game Bar", "Kill overlay CPU overhead",
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 1 /f'),
            ("GPU Priority for Games", "GPU Priority 8, Scheduling High",
             'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f && reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
             'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 2 /f'),
            ("System Responsiveness 0%%", "All CPU resources available to games",
             'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f',
             'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 20 /f'),
        ]
        for t in fn_tweaks: self._make_tweak_row(fn_card, *t)
        vis_card = self._make_card(page, "Windows Visual — Reduce Overhead")
        vis_tweaks = [
            ("Disable Transparency", "Remove Aero glass CPU usage",
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f',
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 1 /f'),
            ("Disable Animations", "Instant window transitions",
             'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d "0" /f',
             'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d "1" /f'),
            ("Best Performance Visual", "Disable all visual effects",
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f',
             'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 0 /f'),
        ]
        for t in vis_tweaks: self._make_tweak_row(vis_card, *t)
        self.fps_log = self._make_log(page)
        self._log(self.fps_log, "FPS module ready. Toggle switches to apply instantly.")

    def _build_ascension_page(self):
        page = self._make_page("ascension", "Ascension Mode")
        banner = ctk.CTkFrame(page, fg_color="#0f0a1a", corner_radius=8,
                               border_width=1, border_color="#2a1a4a")
        banner.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(banner, text="ASCENSION MODE", font=("Consolas", 18, "bold"),
                      text_color=COLORS["ascension"]).pack(pady=(14, 2))
        ctk.CTkLabel(
            banner,
            text="One-click gaming optimizer. Kills background processes,\nstops services, maxes power, flushes RAM.",
            font=("Segoe UI", 11), text_color="#6a5aaa", justify="center"
        ).pack(pady=(0, 14))
        self.asc_status = ctk.CTkLabel(page, text="STATUS: INACTIVE",
                                        font=("Consolas", 12), text_color=COLORS["text_dim"])
        self.asc_status.pack(pady=8)
        bf = ctk.CTkFrame(page, fg_color="transparent")
        bf.pack(fill="x", pady=8)
        self.asc_on_btn = ctk.CTkButton(
            bf, text="ACTIVATE ASCENSION", font=("Consolas", 13, "bold"),
            fg_color=COLORS["ascension"], text_color="#000", hover_color="#8b6fe6",
            height=44, width=260, command=self._ascension_on
        )
        self.asc_on_btn.pack(side="left", padx=(0, 12))
        self.asc_off_btn = ctk.CTkButton(
            bf, text="DEACTIVATE", font=("Consolas", 13),
            fg_color="transparent", border_width=1, border_color=COLORS["card_border"],
            text_color=COLORS["text_dim"], hover_color=COLORS["hover"],
            height=44, width=160, command=self._ascension_off, state="disabled"
        )
        self.asc_off_btn.pack(side="left")
        info_card = self._make_card(page, "What Ascension Does")
        for item in [
            "Kills 20+ background processes", "Stops 19 non-essential services",
            "Sets Ultimate Performance power plan", "Disables notifications",
            "Flushes standby RAM", "Maximizes game process priority", "Disables network throttling"
        ]:
            ctk.CTkLabel(info_card, text=f"  ->  {item}", font=("Segoe UI", 11),
                          text_color=COLORS["text_mid"], anchor="w").pack(fill="x", padx=14, pady=1)
        ctk.CTkLabel(info_card, text="", font=("Segoe UI", 4)).pack()
        self.asc_log = self._make_log(page)
        self._log(self.asc_log, "Ascension module ready.")

    def _ascension_on(self):
        def worker():
            self.asc_status.configure(text="STATUS: ACTIVATING...", text_color=COLORS["warning"])
            self.status_label.configure(text="ASCENSION...", text_color=COLORS["warning"])
            ok, out = run_cmd("powercfg /getactivescheme")
            if ok:
                for p in out.split():
                    if len(p) == 36 and "-" in p:
                        self.prev_power_guid = p
                        break
            self._log(self.asc_log, "Killing background processes...")
            for proc in ASCENSION_KILL:
                run_cmd(f'taskkill /f /im "{proc}"')
            self._log(self.asc_log, f"Killed {len(ASCENSION_KILL)} process types.", "ok")
            self._log(self.asc_log, "Stopping services...")
            for svc in ASCENSION_SVCS:
                run_cmd(f"sc stop {svc}")
            self._log(self.asc_log, f"Stopped {len(ASCENSION_SVCS)} services.", "ok")
            self._log(self.asc_log, "Power plan: Not changed (use your .pow file)", "ok")
            run_cmd('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f')
            run_cmd('reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer" /v DisableNotificationCenter /t REG_DWORD /d 1 /f')
            self._log(self.asc_log, "Notifications disabled.", "ok")
            run_cmd("rundll32.exe advapi32.dll,ProcessIdleTasks")
            self._log(self.asc_log, "RAM flushed.", "ok")
            run_cmd('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f')
            run_cmd('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f')
            self._log(self.asc_log, "Game priority max, network throttle off.", "ok")
            self._log(self.asc_log, "======= ASCENSION MODE ACTIVE =======", "ok")
            self.ascension_active = True
            self.asc_status.configure(text="STATUS: ACTIVE", text_color=COLORS["ascension"])
            self.status_label.configure(text="ASCENSION: ACTIVE", text_color=COLORS["ascension"])
            self.asc_on_btn.configure(state="disabled")
            self.asc_off_btn.configure(state="normal", text_color=COLORS["accent"],
                                        border_color=COLORS["accent"])
        threading.Thread(target=worker, daemon=True).start()

    def _ascension_off(self):
        def worker():
            self.asc_status.configure(text="STATUS: DEACTIVATING...", text_color=COLORS["warning"])
            for svc in ["WSearch", "SysMain", "Spooler", "wuauserv", "UsoSvc"]:
                run_cmd(f"sc config {svc} start= auto")
                run_cmd(f"sc start {svc}")
            self._log(self.asc_log, "Services restored.", "ok")
            run_cmd('reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d 1 /f')
            run_cmd('reg delete "HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer" /v DisableNotificationCenter /f')
            self._log(self.asc_log, "Notifications restored.", "ok")
            self._log(self.asc_log, "======= ASCENSION DEACTIVATED =======", "ok")
            self.ascension_active = False
            self.asc_status.configure(text="STATUS: INACTIVE", text_color=COLORS["text_dim"])
            self.status_label.configure(text="READY", text_color=COLORS["success"])
            self.asc_on_btn.configure(state="normal")
            self.asc_off_btn.configure(state="disabled", text_color=COLORS["text_dim"],
                                        border_color=COLORS["card_border"])
        threading.Thread(target=worker, daemon=True).start()


# ════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if os.name == "nt":
        run_as_admin()
    app = ReapersTweaks()
    app.mainloop()
