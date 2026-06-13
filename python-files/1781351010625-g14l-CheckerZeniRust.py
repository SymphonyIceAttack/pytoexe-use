#!/usr/bin/env python3

import os
import sys
import ctypes
import argparse
import subprocess
import winreg
import codecs
import uuid
import socket
import platform
from pathlib import Path
from typing import Set, List, Dict, Tuple, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.isatty():
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GRAY    = "\033[90m"
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    RESET   = "\033[0m"
else:
    GREEN = RED = YELLOW = GRAY = WHITE = CYAN = MAGENTA = RESET = ""

LOG_LINES: List[str] = []

def log(text: str):
    clean = text
    for esc in [GREEN, RED, YELLOW, GRAY, WHITE, CYAN, MAGENTA, RESET]:
        if esc:
            clean = clean.replace(esc, "")
    LOG_LINES.append(clean)

def color_text(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"

def print_border():
    line = "+" + "-" * 51 + "+"
    print(color_text(line, CYAN))
    log(line)

def print_row(text: str, color: str = WHITE):
    padded = text.ljust(50)[:50]
    line = f"| {padded} |"
    sys.stdout.write(color_text("| ", CYAN))
    sys.stdout.write(color_text(padded, color))
    print(color_text(" |", CYAN))
    log(line)

def print_found(msg: str, critical: bool = False):
    if critical:
        line = f"      [!!!] {msg}"
        print(f"      {color_text('[!!!]', RED)} {color_text(msg, RED)}")
    else:
        line = f"      [+] {msg}"
        print(f"      {color_text('[+]', GREEN)} {msg}")
    log(line)

def print_not_found(msg: str):
    line = f"      [-] {msg}"
    print(f"      {color_text('[-]', GRAY)} {msg}")
    log(line)

def print_warn(msg: str):
    line = f"      [!] {msg}"
    print(f"      {color_text('[!]', YELLOW)} {msg}")
    log(line)

def print_cleaner_evidence(msg: str):
    line = f"      [CLEANER] {msg}"
    print(f"      {color_text('[CLEANER]', MAGENTA)} {msg}")
    log(line)

def print_explain(msg: str):
    line = f"         >> {msg}"
    print(f"         {color_text('>>', YELLOW)} {color_text(msg, GRAY)}")
    log(line)

def print_step(step: str, title: str):
    line = f"\n  [{step}] {title}"
    print()
    sys.stdout.write(f"  {color_text(f'[{step}]', CYAN)} ")
    print(color_text(title, WHITE))
    log(line)

def print_divider():
    line = "+" + "-" * 51 + "+"
    print(color_text(line, CYAN))
    log(line)

def print_plain(text: str):
    print(text)
    log(text)

def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    ascii_art = r"""
███████╗███████╗███╗   ██╗██╗██████╗ ██╗   ██╗███████╗████████╗
╚══███╔╝██╔════╝████╗  ██║██║██╔══██╗██║   ██║██╔════╝╚══██╔══╝
  ███╔╝ █████╗  ██╔██╗ ██║██║██████╔╝██║   ██║███████╗   ██║
 ███╔╝  ██╔══╝  ██║╚██╗██║██║██╔══██╗██║   ██║╚════██║   ██║
███████╗███████╗██║ ╚████║██║██║  ██║╚██████╔╝███████║   ██║
╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝
"""
    for line in ascii_art.splitlines():
        if line.strip():
            print(color_text(line, YELLOW))
    print_border()
    print_row("  FindIT! - Superiority Traces Finder v2.3", CYAN)
    print_row("  + cLeanIT! evidence detection", MAGENTA)
    print_row("  for moderation/research only", GRAY)
    print_row("  by ZENIRUST  ", GRAY)
    print_divider()
    print_row("")
    print_row("  Searches for:", WHITE)
    for line in [
        "    * Superiority cheat traces",
        "    * cLeanIT! cleaner evidence",
    ]:
        print_row(line, GRAY)
    print_row("")
    print_row("  [NO DELETIONS -- info only]", RED)
    print_border()
    print()

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_hwid() -> str:
    try:
        result = subprocess.run(
            ["wmic", "csproduct", "get", "UUID"],
            capture_output=True, text=True, timeout=8
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and l.strip() != "UUID"]
        if lines:
            return lines[0]
    except:
        pass
    try:
        return str(uuid.getnode())
    except:
        return "N/A"

def get_system_info() -> Dict[str, str]:
    info: Dict[str, str] = {}

    info["PC Name"]       = os.environ.get("COMPUTERNAME", socket.gethostname())
    info["Username"]      = os.environ.get("USERNAME", "N/A")
    info["OS"]            = platform.version()
    info["HWID"]          = get_hwid()
    info["Scan Time"]     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-WinSystemLocale | Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=8
        )
        info["System Locale"] = result.stdout.strip() or "N/A"
    except:
        info["System Locale"] = "N/A"

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-TimeZone).Id"],
            capture_output=True, text=True, timeout=8
        )
        info["Timezone"] = result.stdout.strip() or "N/A"
    except:
        info["Timezone"] = "N/A"

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[System.Globalization.RegionInfo]::CurrentRegion.EnglishName"],
            capture_output=True, text=True, timeout=8
        )
        info["Region"] = result.stdout.strip() or "N/A"
    except:
        info["Region"] = "N/A"

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[System.Globalization.RegionInfo]::CurrentRegion.TwoLetterISORegionName"],
            capture_output=True, text=True, timeout=8
        )
        info["Country Code"] = result.stdout.strip() or "N/A"
    except:
        info["Country Code"] = "N/A"

    return info

def print_system_info(info: Dict[str, str]):
    print_border()
    print_row("  SYSTEM INFO", CYAN)
    print_divider()
    for k, v in info.items():
        line = f"  {k}: {v}"
        print_row(line, WHITE)
    print_border()
    print()

def scan_and_find(path: str, pattern: str = "superiority") -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {"files": [], "folders": []}
    p = Path(path)
    if not p.exists():
        return found
    try:
        for root, dirs, files in os.walk(p, topdown=False):
            root_path = Path(root)
            for f in files:
                if pattern.lower() in f.lower():
                    found["files"].append(str(root_path / f))
            for d in dirs:
                if pattern.lower() in d.lower():
                    found["folders"].append(str(root_path / d))
    except Exception as e:
        print_warn(f"Access error in {path}: {e}")
    return found

def scan_all_paths(scan_paths: Set[str]) -> Tuple[List[str], List[str]]:
    all_files: List[str] = []
    all_folders: List[str] = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(scan_and_find, path): path for path in scan_paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                res = future.result()
                for f in res["files"]:
                    print_found(f"File: {f}")
                    all_files.append(f)
                for d in res["folders"]:
                    print_found(f"Folder: {d}")
                    all_folders.append(d)
            except Exception as e:
                print_warn(f"Scan error for {path}: {e}")
    return all_files, all_folders

def find_registry_key(key_path: str) -> bool:
    try:
        parts = key_path.split('\\', 1)
        hive_str = parts[0]
        subkey = parts[1] if len(parts) > 1 else ""
        hive_map = {
            "HKCU": winreg.HKEY_CURRENT_USER,
            "HKLM": winreg.HKEY_LOCAL_MACHINE,
        }
        if hive_str not in hive_map:
            return False
        winreg.OpenKeyEx(hive_map[hive_str], subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        return True
    except:
        return False

def check_autorun_entry() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        winreg.QueryValueEx(key, "Superiority")
        winreg.CloseKey(key)
        return True
    except:
        return False

def check_registry_run_leftover() -> List[str]:
    found: List[str] = []
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        i = 0
        while True:
            try:
                name, data, _ = winreg.EnumValue(key, i)
                if "superior" in name.lower() or "superior" in str(data).lower():
                    found.append(f"{name} -> {data}")
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except:
        pass
    return found

def check_userassist() -> List[str]:
    found: List[str] = []
    target_rot13 = codecs.encode("superiority", "rot_13")
    try:
        base_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        guid_count = 0
        while True:
            try:
                guid = winreg.EnumKey(base_key, guid_count)
                guid_count += 1
                try:
                    count_key = winreg.OpenKey(base_key, guid + "\\Count", 0, winreg.KEY_READ)
                    val_index = 0
                    while True:
                        try:
                            name, _, _ = winreg.EnumValue(count_key, val_index)
                            val_index += 1
                            if target_rot13 in name.lower():
                                decoded = codecs.decode(name, "rot_13")
                                found.append(decoded)
                        except OSError:
                            break
                    winreg.CloseKey(count_key)
                except:
                    pass
            except OSError:
                break
        winreg.CloseKey(base_key)
    except:
        pass
    return found

def check_recent_docs_registry() -> List[str]:
    found: List[str] = []
    try:
        base_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
            0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        i = 0
        while True:
            try:
                name, data, _ = winreg.EnumValue(base_key, i)
                i += 1
                raw = bytes(data) if isinstance(data, (bytes, bytearray)) else b""
                decoded = raw.decode("utf-16-le", errors="ignore")
                if "superior" in decoded.lower():
                    found.append(f"RecentDocs: {name} -> {decoded[:80]}")
            except OSError:
                break
        winreg.CloseKey(base_key)
    except:
        pass
    return found

def check_appcompat_flags() -> List[str]:
    found: List[str] = []
    paths = [
        r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store",
        r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
    ]
    for subkey_path in paths:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, subkey_path,
                0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    i += 1
                    if "superior" in name.lower():
                        found.append(f"AppCompat: {name}")
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    return found

def check_prefetch() -> List[str]:
    found: List[str] = []
    prefetch_dir = Path("C:\\Windows\\Prefetch")
    if not prefetch_dir.exists():
        return found
    try:
        for pf in prefetch_dir.glob("*.pf"):
            if "superior" in pf.name.lower():
                mtime = datetime.fromtimestamp(pf.stat().st_mtime)
                found.append(f"{pf.name} (last run: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    except:
        pass
    return found

def check_recent_lnk() -> List[str]:
    found: List[str] = []
    recent_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Recent"
    if not recent_dir.exists():
        return found
    try:
        for lnk in recent_dir.rglob("*.lnk"):
            if "superior" in lnk.stem.lower():
                found.append(str(lnk))
    except:
        pass
    return found

def check_defender_logs() -> List[str]:
    found: List[str] = []
    defender_dir = Path("C:\\ProgramData\\Microsoft\\Windows Defender\\Support")
    if not defender_dir.exists():
        return found
    try:
        for log_file in defender_dir.glob("*.log"):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        if "superior" in line.lower():
                            found.append(f"{log_file.name}:{i+1} -> {line.strip()[:80]}")
                            if len(found) >= 5:
                                return found
            except:
                pass
    except:
        pass
    return found

def check_usn_journal(drive: str) -> Tuple[bool, bool]:
    if not Path(drive).exists():
        return (False, False)
    try:
        result = subprocess.run(
            ["fsutil", "usn", "queryjournal", drive],
            capture_output=True, text=True, timeout=8
        )
        out = result.stdout + result.stderr
        if result.returncode == 0 and out.strip():
            disabled = "not active" in out.lower() or "no journal" in out.lower()
            return (True, not disabled)
        return (False, False)
    except Exception as e:
        print_warn(f"USN check error on {drive}: {e}")
        return (False, False)

def check_event_log(log_name: str) -> Tuple[bool, bool]:
    exists = False
    was_cleared = False
    try:
        result = subprocess.run(
            ["wevtutil", "get-log", log_name],
            capture_output=True, text=True, timeout=8
        )
        out = result.stdout + result.stderr
        if result.returncode == 0 and ("enabled" in out.lower() or log_name.lower() in out.lower()):
            exists = True
        if exists:
            if log_name == "Security":
                qr = subprocess.run(
                    ["wevtutil", "qe", "Security",
                     "/q:*[System[(EventID=1102)]]",
                     "/c:1", "/rd:true", "/f:text"],
                    capture_output=True, text=True, timeout=10
                )
                out2 = qr.stdout + qr.stderr
                if "1102" in out2 or "audit log was cleared" in out2.lower():
                    was_cleared = True
            elif log_name == "System":
                qr = subprocess.run(
                    ["wevtutil", "qe", "System",
                     "/q:*[System[(EventID=104)]]",
                     "/c:1", "/rd:true", "/f:text"],
                    capture_output=True, text=True, timeout=10
                )
                if "log was cleared" in (qr.stdout + qr.stderr).lower():
                    was_cleared = True
        return (exists, was_cleared)
    except Exception as e:
        print_warn(f"Event log check error ({log_name}): {e}")
        return (False, False)

def check_cleaner_script_files() -> List[str]:
    found: List[str] = []
    possible_names = [
        "cLeanIT!.py", "cLeanIT!.exe",
        "cleanit.py", "CleanIT.py",
        "cleanit.exe", "CleanIT.exe",
    ]
    user_profile = os.environ.get("USERPROFILE", "")
    search_dirs = [
        user_profile + "\\Desktop",
        user_profile + "\\Downloads",
        user_profile + "\\Documents",
        os.environ.get("TEMP", ""),
        os.environ.get("APPDATA", ""),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for search_dir in search_dirs:
        if not search_dir or not Path(search_dir).exists():
            continue
        for name in possible_names:
            target = Path(search_dir) / name
            if target.exists() and str(target) not in found:
                found.append(str(target))
            try:
                for found_file in Path(search_dir).rglob(name):
                    if str(found_file) not in found:
                        found.append(str(found_file))
            except:
                pass
    return found

def check_cleaner_logs() -> List[Tuple[str, List[str]]]:
    results: List[Tuple[str, List[str]]] = []
    user_profile = os.environ.get("USERPROFILE", "")
    temp_dir = os.environ.get("TEMP", "")
    possible_logs = [
        "cleanit_log.txt", "cLeanIT_log.txt",
        "superiority_clean.log", "cleanit.log",
    ]
    search_roots = [
        user_profile + "\\Desktop",
        user_profile + "\\Downloads",
        temp_dir,
    ]
    for logname in possible_logs:
        for search_root in search_roots:
            if not search_root or not Path(search_root).exists():
                continue
            log_path = Path(search_root) / logname
            if log_path.exists():
                lines: List[str] = []
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [l.strip() for l in f.readlines()[:3] if l.strip()]
                except:
                    pass
                results.append((str(log_path), lines))
    return results

def check_mft_timestamp_anomalies() -> bool:
    suspicious = 0
    for drive_letter in "CDEFG":
        drive = f"{drive_letter}:"
        if Path(drive).exists():
            exists, enabled = check_usn_journal(drive)
            if exists and not enabled:
                suspicious += 1
    return suspicious > 0

def check_scheduled_tasks() -> List[str]:
    found: List[str] = []
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "LIST"],
            capture_output=True, text=True, timeout=15
        )
        task_name = ""
        for line in result.stdout.splitlines():
            if line.startswith("TaskName:"):
                task_name = line.split(":", 1)[1].strip()
            if "superior" in task_name.lower():
                found.append(task_name)
    except:
        pass
    return found

def save_log(path: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            for line in LOG_LINES:
                f.write(line + "\n")
    except Exception as e:
        print_warn(f"Failed to save log: {e}")

def main():
    parser = argparse.ArgumentParser(description="FindIT! - Superiority Traces Finder")
    parser.add_argument("--quiet", action="store_true", help="Skip banner and prompts")
    parser.add_argument("--log", metavar="FILE", help="Save full report to .txt file")
    args = parser.parse_args()

    admin_mode = is_admin()

    if not args.quiet:
        if not admin_mode:
            print(color_text("  [!] Admin rights recommended for full search (USN/logs).", YELLOW))
            print(color_text("  Press ENTER to continue anyway, Ctrl+C to exit.", GRAY))
            try:
                input()
            except KeyboardInterrupt:
                sys.exit(0)
        print_banner()
        try:
            input(color_text("  Press ENTER to start search...", GRAY))
        except KeyboardInterrupt:
            sys.exit(0)
        print()

    sysinfo = get_system_info()
    print_system_info(sysinfo)

    cheat_found:    List[str] = []
    cleaner_evidence_count = 0
    critical_evidence: List[str] = []

    print_step("1/7", "Searching Superiority files (parallel)...")
    scan_paths: Set[str] = set()
    for env in ["APPDATA", "LOCALAPPDATA", "TEMP", "ProgramFiles", "ProgramFiles(x86)", "ProgramData"]:
        p = os.environ.get(env)
        if p and Path(p).exists():
            scan_paths.add(p)
    user = os.environ.get("USERPROFILE", "")
    for sub in ["Documents", "Downloads", "Desktop"]:
        p = Path(user) / sub
        if p.exists():
            scan_paths.add(str(p))
    for path in sorted(scan_paths):
        print_plain(f"    -> {path}")
    all_files, all_folders = scan_all_paths(scan_paths)
    for f in all_files:
        cheat_found.append(f"File: {f}")
    for d in all_folders:
        cheat_found.append(f"Folder: {d}")

    print_step("2/7", "Searching registry (Superiority)...")
    registry_keys = [
        "HKCU\\Software\\Superiority",
        "HKLM\\Software\\Superiority",
        "HKCU\\Software\\Classes\\superiority",
    ]
    for key in registry_keys:
        if find_registry_key(key):
            print_found(f"Registry key: {key}")
            print_explain("Cheat installed registry entries -- direct evidence of installation.")
            cheat_found.append(f"Registry key: {key}")
        else:
            print_not_found(f"Registry key: {key}")

    if check_autorun_entry():
        print_found("Autorun entry: HKCU\\...\\Run\\Superiority")
        print_explain("Cheat was set to auto-start with Windows.")
        cheat_found.append("Autorun entry: Superiority")
    else:
        print_not_found("Autorun entry: Superiority")

    for rv in check_registry_run_leftover():
        print_found(f"Run value: {rv}")
        print_explain("Leftover run entry referencing Superiority path.")
        cheat_found.append(f"Run value: {rv}")

    print_step("3/7", "Searching execution traces...")

    prefetch_hits = check_prefetch()
    if prefetch_hits:
        for ph in prefetch_hits:
            print_found(f"Prefetch: {ph}", critical=True)
            print_explain("Windows creates Prefetch files every time a program runs.")
            print_explain("This proves the cheat executable was launched on this PC.")
            print_explain("Prefetch survives file deletion -- cannot be faked.")
            cheat_found.append(f"Prefetch: {ph}")
    else:
        print_not_found("No Superiority prefetch files found")

    userassist_hits = check_userassist()
    if userassist_hits:
        for ua in userassist_hits:
            print_found(f"UserAssist: {ua}", critical=True)
            print_explain("UserAssist tracks every program the user opened via Explorer.")
            print_explain("Stored in registry, encoded ROT13. Survives file deletion.")
            cheat_found.append(f"UserAssist: {ua}")
    else:
        print_not_found("No UserAssist entries found")

    appcompat_hits = check_appcompat_flags()
    if appcompat_hits:
        for ac in appcompat_hits:
            print_found(ac, critical=True)
            print_explain("AppCompatFlags: Windows logs every .exe that was ever run,")
            print_explain("including those later deleted. Strong execution proof.")
            cheat_found.append(ac)
    else:
        print_not_found("No AppCompat flags found")

    recent_lnk = check_recent_lnk()
    if recent_lnk:
        for lnk in recent_lnk:
            print_found(f"Recent shortcut: {lnk}")
            print_explain("Windows auto-creates .lnk shortcuts for recently opened files.")
            print_explain("Shortcut remains even if the original file was deleted.")
            cheat_found.append(f"Recent shortcut: {lnk}")
    else:
        print_not_found("No Recent .lnk shortcuts found")

    recent_docs = check_recent_docs_registry()
    if recent_docs:
        for rd in recent_docs:
            print_found(rd)
            print_explain("RecentDocs registry stores names of recently accessed files.")
            cheat_found.append(rd)
    else:
        print_not_found("No RecentDocs registry entries found")

    print_step("4/7", "Checking scheduled tasks...")
    tasks = check_scheduled_tasks()
    if tasks:
        for t in tasks:
            print_found(f"Scheduled task: {t}")
            print_explain("A scheduled task referencing Superiority was registered.")
            print_explain("Used for persistence -- cheat auto-launches on schedule.")
            cheat_found.append(f"Scheduled task: {t}")
    else:
        print_not_found("No suspicious scheduled tasks found")

    print_step("5/7", "Checking USN Journal status...")
    print_explain("USN Journal = Windows file system change log. Always active by default.")
    print_explain("cLeanIT! disables it to erase file operation history.")
    for drive_letter in "CDEFG":
        drive = f"{drive_letter}:"
        exists, enabled = check_usn_journal(drive)
        if exists:
            if enabled:
                print_found(f"USN Journal active on {drive} (normal)")
            else:
                print_cleaner_evidence(f"USN Journal DISABLED on {drive}!")
                print_explain(f"USN Journal on {drive} was deliberately disabled.")
                print_explain("This is not normal -- only cLeanIT! or manual tampering does this.")
                cleaner_evidence_count += 2
                critical_evidence.append(f"USN Journal disabled on {drive}")
        else:
            print_not_found(f"USN Journal on {drive} (drive not present)")

    print_step("6/7", "Checking event logs...")
    print_explain("Windows Event Logs record system activity. cLeanIT! clears them")
    print_explain("to hide cheat installation/execution events.")
    logs = [
        "Microsoft-Windows-NTFS/Operational",
        "System",
        "Security",
        "Application",
    ]
    for log_name in logs:
        exists, was_cleared = check_event_log(log_name)
        if exists:
            print_found(f"Log exists: {log_name} (normal)")
            if was_cleared:
                print_cleaner_evidence(f"{log_name} log was CLEARED!")
                print_explain(f"Event log '{log_name}' was manually wiped.")
                print_explain("Normal users never clear event logs.")
                print_explain("EventID 1102 (Security) / 104 (System) confirm the clear.")
                cleaner_evidence_count += 2
                critical_evidence.append(f"Event log {log_name} was cleared")
        else:
            if log_name == "Security":
                print_cleaner_evidence("Security log MISSING -- abnormal!")
                print_explain("Security event log is present on every Windows install.")
                print_explain("Its absence means it was disabled or deleted externally.")
                print_explain("Strong indicator of anti-forensic activity.")
                cleaner_evidence_count += 2
                critical_evidence.append("Security event log is missing")
            else:
                print_not_found(f"Log {log_name}: not found")

    print_step("7/7", "Searching for cLeanIT! cleaner evidence...")

    cleaner_files = check_cleaner_script_files()
    if cleaner_files:
        for cf in cleaner_files:
            print_cleaner_evidence(f"cLeanIT! script found: {cf}")
            print_explain(f"Path: {cf}")
            print_explain("The cleaner tool itself is present on this machine.")
            cleaner_evidence_count += 3
            critical_evidence.append(f"Cleaner file present: {cf}")
    else:
        print_not_found("No cLeanIT! script files found")

    if check_mft_timestamp_anomalies():
        print_cleaner_evidence("USN Journal missing/disabled on one or more drives!")
        print_explain("Consistent with cLeanIT! wiping file system journal.")
        cleaner_evidence_count += 3

    temp_dir_path = os.environ.get("TEMP", "")
    if temp_dir_path and Path(temp_dir_path).exists():
        try:
            count = len(list(Path(temp_dir_path).glob("*")))
            if count < 5:
                print_cleaner_evidence(f"Temp directory nearly empty ({count} files)")
                print_explain("Normal Windows temp folder contains dozens of files.")
                print_explain("Near-empty temp suggests it was manually wiped.")
                cleaner_evidence_count += 1
        except:
            pass

    cleaner_logs = check_cleaner_logs()
    for log_path, lines in cleaner_logs:
        print_cleaner_evidence(f"Cleaner log file found: {log_path}")
        print_explain(f"Path: {log_path}")
        print_explain("cLeanIT! leaves a log of what it deleted. Found on this machine.")
        cleaner_evidence_count += 2
        critical_evidence.append(f"Cleaner log exists: {log_path}")
        for line in lines:
            print_plain(f"           -> {line[:60]}")

    defender_hits = check_defender_logs()
    if defender_hits:
        for dh in defender_hits:
            print_cleaner_evidence(f"Defender log: {dh}")
            print_explain("Windows Defender logged Superiority as a threat.")
            print_explain("This entry persists in Defender support logs independently.")
            cleaner_evidence_count += 2
            critical_evidence.append(f"Defender log hit: {dh[:60]}")
    else:
        print_not_found("No Defender log entries for Superiority")

    print()
    print_border()
    print_row("  SCAN RESULTS", CYAN)
    print_divider()

    total_cheat = len(cheat_found)

    if total_cheat > 0:
        print_row(f"  Superiority traces found: {total_cheat}", GREEN)
        for item in cheat_found:
            print_row(f"    + {item[:46]}", YELLOW)
    else:
        print_row("  No direct Superiority traces found.", GRAY)

    if cleaner_evidence_count > 0:
        print_row(f"  cLeanIT! evidence: {cleaner_evidence_count} points", MAGENTA)
        if cleaner_evidence_count >= 3:
            print_row("  [WARNING] Cleaner was likely used!", RED)
        for evidence in critical_evidence:
            print_row(f"    * {evidence[:46]}", YELLOW)
    else:
        print_row("  No cLeanIT! evidence found.", GRAY)

    print_divider()
    if cleaner_evidence_count >= 3 and total_cheat > 0:
        print_row("  VERDICT: Cheat + cleaner usage confirmed!", RED)
        print_row("  Direct traces AND cleaner evidence found.", RED)
    elif cleaner_evidence_count >= 3:
        print_row("  VERDICT: Cleaner usage confirmed!", RED)
        print_row("  Evidence of cheat removal attempt.", RED)
    elif total_cheat == 0 and cleaner_evidence_count > 0:
        print_row("  VERDICT: Suspicious -- cleaner detected.", YELLOW)
    elif total_cheat > 0:
        print_row("  VERDICT: Cheat detected directly.", RED)
    else:
        print_row("  VERDICT: No evidence found.", GREEN)

    print_row("  No files were deleted -- report only.", CYAN)
    print_border()
    print()

    if cleaner_evidence_count >= 3 or total_cheat > 0:
        print(color_text("  ACTION REQUIRED:", RED))
        if cleaner_evidence_count >= 3:
            print(color_text("    User likely used cLeanIT! to hide Superiority.", WHITE))
        if total_cheat > 0:
            print(color_text("    Direct cheat traces found.", WHITE))
        print(color_text("    Share this report with moderators for ban decision.", WHITE))
    else:
        print(color_text("  System appears clean.", GREEN))

    print()

    if args.log:
        save_log(args.log)
        print(color_text(f"  Report saved to: {args.log}", CYAN))
        print()
    else:
        user_profile = os.environ.get("USERPROFILE", "")
        default_log = str(Path(user_profile) / "Desktop" / f"findit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            save_log_prompt = input(color_text(f"  Save report to Desktop? [Y/n]: ", GRAY)).strip().lower()
        except KeyboardInterrupt:
            save_log_prompt = "n"
        if save_log_prompt in ("", "y", "yes"):
            save_log(default_log)
            print(color_text(f"  Report saved to: {default_log}", CYAN))
            print()

    if not args.quiet:
        try:
            input(color_text("  Press ENTER to exit...", GRAY))
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(color_text("\n  Interrupted by user.", YELLOW))
        sys.exit(0)

