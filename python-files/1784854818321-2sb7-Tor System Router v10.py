#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii
import ctypes
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog


APP_NAME = "TorLeakGuard"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TorLeakGuard"

DOWNLOAD_DIR = APP_DIR / "downloads"
TOR_DIR = APP_DIR / "tor"
SINGBOX_DIR = APP_DIR / "sing-box"
TOR_DATA = APP_DIR / "tor-data"
PT_DIR = APP_DIR / "pt"

TORRC = APP_DIR / "torrc"
SINGBOX_CONFIG = APP_DIR / "sing-box.json"
STATE_FILE = APP_DIR / "state.json"
VERSIONS_FILE = APP_DIR / "versions.json"
SETTINGS_FILE = APP_DIR / "settings.json"

TOR_LOG = APP_DIR / "tor.log"
SINGBOX_LOG = APP_DIR / "sing-box.log"
SINGBOX_CONSOLE_LOG = APP_DIR / "sing-box-console.log"

# Portable temp location: per-user %TEMP% (writable without admin, no root-of-C:
# permission issues). Used ONLY by the fallback silent Tor Browser install path.
TOR_BROWSER_TEMP_DIR = Path(
    os.environ.get("TEMP") or os.environ.get("TMP") or str(Path.home())
) / "TorLeakGuard_TB_Temp"

WINTUN_VERSION = "0.14.1"

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

HTTP_HEADERS = {
    "User-Agent": "TorLeakGuard/1.0 (Windows11; local privacy tool)"
}

KILL_PS = r'''
Get-CimInstance Win32_Process | Where-Object {
  $_.ExecutablePath -like '*\TorLeakGuard\*' -and
  (
    $_.Name -eq 'tor.exe' -or
    $_.Name -eq 'sing-box.exe' -or
    $_.Name -eq 'obfs4proxy.exe' -or
    $_.Name -eq 'lyrebird.exe' -or
    $_.Name -eq 'snowflake-client.exe'
  )
} | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
'''

CIRCUM_HINT = (
    "How circumvention works here:\n"
    "- Tor already HIDES the sites you visit (SNI / IP) inside the tunnel, so "
    "site-level DPI blocks do not apply.\n"
    "- If your ISP blocks or throttles TOR ITSELF, use Bridges mode: obfs4 looks "
    "like random noise, webtunnel like plain HTTPS, snowflake like WebRTC.\n"
    "- 'Check bridge status' proves a bridge is really carrying traffic: [ACTIVE] "
    "means the obfs4 plugin has an open connection to that bridge IP.\n"
    "- RESET is an emergency eject: it never waits, aborts any running task and "
    "force-kills hung processes, then keeps the window open.\n"
    "- Limits: Tor speed is capped by the Tor network; a raw whole-link bandwidth "
    "cap from the ISP cannot be bypassed by any software."
)

_ABORT = {"flag": False}


class Aborted(Exception):
    pass


def abort_now():
    _ABORT["flag"] = True


def abort_clear():
    _ABORT["flag"] = False


def check_abort():
    if _ABORT["flag"]:
        raise Aborted()


def ensure_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TOR_DIR.mkdir(parents=True, exist_ok=True)
    SINGBOX_DIR.mkdir(parents=True, exist_ok=True)
    TOR_DATA.mkdir(parents=True, exist_ok=True)
    PT_DIR.mkdir(parents=True, exist_ok=True)


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin(action=None):
    script = Path(sys.argv[0]).resolve()
    params = f'"{script}"'

    if action == "start":
        params += " --autostart"
    elif action == "install":
        params += " --autoinstall"
    elif action == "update":
        params += " --autoupdate"
    elif action == "stop":
        params += " --autostop"

    ret = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )

    if ret <= 32:
        raise RuntimeError("Failed to request administrator rights.")

    sys.exit(0)


def safe_unlink(path):
    try:
        path = Path(path)
        if path.exists():
            path.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        pass


def ps_quote(s):
    return "'" + str(s).replace("'", "''") + "'"


def load_versions():
    if VERSIONS_FILE.exists():
        try:
            return json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_versions(data):
    ensure_dirs()
    VERSIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_settings():
    defaults = {
        "mode": "normal",
        "bridges": "",
        "pt_path": "",
        "prevent_circuit_change": True,
        "padding": True,
    }

    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if "pt_path" not in data and data.get("obfs4proxy"):
                data["pt_path"] = data.get("obfs4proxy")
            defaults.update(data)
        except Exception:
            pass

    return defaults


def save_settings(settings):
    ensure_dirs()
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def http_get_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_text(url, timeout=60):
    return http_get_bytes(url, timeout=timeout).decode("utf-8", errors="ignore")


def url_exists(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers=HTTP_HEADERS)
        with urllib.request.urlopen(req, timeout=30):
            return True
    except Exception:
        return False


def download_file(url, dest, log):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    log(f"Downloading: {url}")

    req = urllib.request.Request(url, headers=HTTP_HEADERS)

    with urllib.request.urlopen(req, timeout=180) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    log(f"Saved: {dest}")


def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest().lower()


def verify_sha256_from_text(sum_text, filename, filepath, log):
    actual = sha256_file(filepath)

    for line in sum_text.splitlines():
        if filename in line:
            parts = line.split()
            if not parts:
                continue

            expected = parts[0].strip().lower().lstrip("*")

            if expected == actual:
                log(f"SHA256 OK: {filename}")
                return True

            raise ValueError(
                f"SHA256 mismatch for {filename}\n"
                f"expected: {expected}\n"
                f"actual:   {actual}"
            )

    log(f"SHA256 for {filename} not found, check skipped.")
    return False


def extract_zip(zip_path, dest_dir, log):
    zip_path = Path(zip_path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    log(f"Extracting ZIP {zip_path.name} -> {dest_dir}")

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)


def extract_archive(path, dest_dir, log):
    path = Path(path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    log(f"Extracting {path.name} -> {dest_dir}")

    low = path.name.lower()

    if low.endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            zf.extractall(dest_dir)

    elif low.endswith((".tar.gz", ".tgz", ".tar.xz", ".txz", ".tar")):
        with tarfile.open(path, "r:*") as tf:
            try:
                tf.extractall(dest_dir, filter="data")
            except TypeError:
                tf.extractall(dest_dir)

    else:
        raise RuntimeError(f"Unsupported archive format: {path.name}")


_SEVENZIP_CACHE = None


def read_7z_from_registry():
    found = []

    try:
        import winreg
    except Exception:
        return found

    hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    key_paths = [r"SOFTWARE\7-Zip", r"SOFTWARE\WOW6432Node\7-Zip"]

    for hive in hives:
        for kp in key_paths:
            try:
                key = winreg.OpenKey(hive, kp)
            except OSError:
                continue

            try:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                    except OSError:
                        break

                    if isinstance(value, str) and value.strip():
                        p = Path(value.strip())
                        if p.exists():
                            found.append(p)

                    i += 1
            finally:
                try:
                    winreg.CloseKey(key)
                except Exception:
                    pass

    return found


def find_7z():
    global _SEVENZIP_CACHE

    if _SEVENZIP_CACHE and _SEVENZIP_CACHE.exists():
        return _SEVENZIP_CACHE

    names = ("7z.exe", "7zz.exe", "7za.exe")

    for n in names:
        w = shutil.which(n)
        if w:
            _SEVENZIP_CACHE = Path(w)
            return _SEVENZIP_CACHE

    dirs = [
        Path("C:/Program Files/7-Zip"),
        Path("C:/Program Files (x86)/7-Zip"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "7-Zip",
        Path(os.environ.get("ProgramFiles", "")) / "7-Zip",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "7-Zip",
        Path("C:/7-Zip"),
        Path("D:/7-Zip"),
        Path("E:/7-Zip"),
    ]

    for rp in read_7z_from_registry():
        dirs.append(rp)

    for d in dirs:
        try:
            if not d or not d.exists():
                continue
        except Exception:
            continue

        for n in names:
            c = d / n
            if c.exists():
                _SEVENZIP_CACHE = c
                return c

    return None


def add_7z_to_path():
    exe = find_7z()

    extra = []

    if exe:
        extra.append(exe.parent)

    extra += [
        Path("C:/Program Files/7-Zip"),
        Path("C:/Program Files (x86)/7-Zip"),
    ]

    cur = os.environ.get("PATH", "")
    add = []

    for d in extra:
        try:
            s = str(d)
            if d.exists() and s not in cur:
                add.append(s)
        except Exception:
            pass

    if add:
        os.environ["PATH"] = os.pathsep.join(add) + os.pathsep + cur


def extract_with_7z(archive, dest_dir, log):
    exe = find_7z()

    if not exe:
        log("7-Zip not found - cannot extract exe archive.")
        return False

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    log(f"Extracting via 7-Zip ({exe})...")

    try:
        p = subprocess.run(
            [str(exe), "x", str(archive), f"-o{dest_dir}", "-y"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )

        log(f"7-Zip returncode={p.returncode} (0 and 1 = success)")

        if p.stdout and p.stdout.strip():
            log("7-Zip stdout (tail): " + p.stdout.strip().replace("\r", "")[-500:])

        if p.stderr and p.stderr.strip():
            log("7-Zip stderr (tail): " + p.stderr.strip().replace("\r", "")[-500:])

        return p.returncode in (0, 1)

    except Exception as e:
        log(f"7-Zip extraction error: {e}")
        return False


def find_file(root, name):
    root = Path(root)

    if not root.exists():
        return None

    try:
        for p in root.rglob(name):
            if p.is_file():
                return p
    except Exception:
        pass

    return None


def find_wintun_dll_in_tree(root):
    root = Path(root)

    if not root.exists():
        return None

    candidates = []

    try:
        for p in root.rglob("wintun.dll"):
            if p.is_file():
                candidates.append(p)
    except Exception:
        pass

    if not candidates:
        return None

    def score(p):
        low = str(p).lower().replace("\\", "/")
        if "/amd64/" in low or "/x64/" in low:
            return 0
        if "/arm64/" in low:
            return 2
        if "/x86/" in low or "/386/" in low:
            return 3
        return 1

    candidates.sort(key=score)
    return candidates[0]


def get_tor_exe():
    return find_file(TOR_DIR, "tor.exe")


def get_singbox_exe():
    return find_file(SINGBOX_DIR, "sing-box.exe")


def get_wintun_dll():
    candidates = [
        SINGBOX_DIR / "wintun.dll",
        APP_DIR / "wintun.dll",
    ]

    for c in candidates:
        if c.exists():
            return c

    found = find_file(SINGBOX_DIR, "wintun.dll")
    if found:
        return found

    system_root = Path(os.environ.get("SystemRoot", "C:\\Windows"))
    sys32 = system_root / "System32" / "wintun.dll"

    if sys32.exists():
        return sys32

    return None


def components_status(log):
    tor = get_tor_exe()
    sing = get_singbox_exe()
    wintun = get_wintun_dll()

    log(f"tor.exe:      {tor if tor else 'not found'}")
    log(f"sing-box.exe: {sing if sing else 'not found'}")
    log(f"wintun.dll:   {wintun if wintun else 'not found'}")

    return bool(tor and sing and wintun)


def get_latest_tor_version(log):
    url = "https://dist.torproject.org/torbrowser/"
    log("Fetching Tor version list...")

    html = http_get_text(url)

    versions = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/"', html)
    versions = sorted(set(versions), key=lambda v: tuple(int(x) for x in v.split(".")))

    if not versions:
        raise RuntimeError("Could not get Tor version list from dist.torproject.org")

    latest = versions[-1]
    log(f"Latest Tor version: {latest}")
    return latest


def get_tor_expert_bundle_url(version, log):
    base = f"https://dist.torproject.org/torbrowser/{version}/"

    try:
        html = http_get_text(base)
        links = re.findall(r'href="([^"]+)"', html)

        candidates = []

        for link in links:
            name = link.split("/")[-1]
            if not name:
                continue

            low = name.lower()

            if (
                "expert-bundle" in low
                and "windows" in low
                and "x86_64" in low
                and (
                    low.endswith(".zip")
                    or low.endswith(".tar.gz")
                    or low.endswith(".tar.xz")
                )
            ):
                url = link if link.startswith("http") else base + name

                if low.endswith(".zip"):
                    priority = 0
                elif low.endswith(".tar.gz"):
                    priority = 1
                else:
                    priority = 2

                candidates.append((priority, url, name))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1], candidates[0][2]

    except Exception as e:
        log(f"Could not get Tor Expert Bundle file list: {e}")

    fallbacks = [
        f"tor-expert-bundle-windows-x86_64-{version}.zip",
        f"tor-expert-bundle-windows-x86_64-{version}.tar.gz",
        f"tor-expert-bundle-windows-x86_64-{version}.tar.xz",
    ]

    for name in fallbacks:
        url = base + name
        if url_exists(url):
            return url, name

    raise RuntimeError("Tor Expert Bundle file for Windows x86_64 not found.")


def install_tor(log, force=False):
    ensure_dirs()
    check_abort()

    exe = get_tor_exe()
    versions = load_versions()
    latest = get_latest_tor_version(log)

    if exe and versions.get("tor") == latest and not force:
        log(f"Tor already installed and up to date: {latest}")
        return latest

    if exe and force and versions.get("tor") == latest:
        log(f"Tor is up to date: {latest}. Reinstall not needed.")
        return latest

    url, file_name = get_tor_expert_bundle_url(latest, log)
    archive_path = DOWNLOAD_DIR / file_name

    download_file(url, archive_path, log)
    check_abort()

    try:
        sums_url = f"https://dist.torproject.org/torbrowser/{latest}/sha256sums-signed-build.txt"
        sums_text = http_get_text(sums_url)
        verify_sha256_from_text(sums_text, file_name, archive_path, log)
    except urllib.error.HTTPError:
        log("Tor SHA256 file not found, check skipped.")
    except ValueError:
        safe_unlink(archive_path)
        raise
    except Exception as e:
        log(f"Tor SHA256 check skipped due to error: {e}")

    if TOR_DIR.exists():
        log("Removing old Tor folder...")
        shutil.rmtree(TOR_DIR, ignore_errors=True)

    extract_archive(archive_path, TOR_DIR, log)
    safe_unlink(archive_path)

    versions = load_versions()
    versions["tor"] = latest
    save_versions(versions)

    tor_exe = get_tor_exe()
    if not tor_exe:
        raise RuntimeError("Tor extracted but tor.exe not found.")

    log(f"Tor installed: {tor_exe}")
    return latest


def get_latest_singbox_release(log):
    api_url = "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
    log("Fetching latest sing-box version...")

    data = json.loads(http_get_text(api_url))
    version = data.get("tag_name", "").lstrip("v")

    if not version:
        raise RuntimeError("Could not get sing-box version from GitHub API")

    asset_name = f"sing-box-{version}-windows-amd64.zip"
    asset_url = None

    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name == asset_name:
            asset_url = asset.get("browser_download_url")
            break

    if not asset_url:
        asset_url = f"https://github.com/SagerNet/sing-box/releases/download/v{version}/{asset_name}"

    log(f"Latest sing-box version: {version}")
    return version, asset_url, asset_name


def install_singbox(log, force=False):
    ensure_dirs()
    check_abort()

    exe = get_singbox_exe()
    versions = load_versions()
    latest, url, asset_name = get_latest_singbox_release(log)

    if exe and versions.get("sing-box") == latest and not force:
        log(f"sing-box already installed and up to date: {latest}")
        return latest

    if exe and force and versions.get("sing-box") == latest:
        log(f"sing-box is up to date: {latest}. Reinstall not needed.")
        return latest

    zip_path = DOWNLOAD_DIR / asset_name
    download_file(url, zip_path, log)
    check_abort()

    try:
        sha_url = url + ".sha256sum"
        sha_text = http_get_text(sha_url)
        verify_sha256_from_text(sha_text, asset_name, zip_path, log)
    except urllib.error.HTTPError:
        log("sing-box SHA256 file not found, check skipped.")
    except ValueError:
        safe_unlink(zip_path)
        raise
    except Exception as e:
        log(f"sing-box SHA256 check skipped due to error: {e}")

    if SINGBOX_DIR.exists():
        log("Removing old sing-box folder...")
        shutil.rmtree(SINGBOX_DIR, ignore_errors=True)

    extract_zip(zip_path, SINGBOX_DIR, log)
    safe_unlink(zip_path)

    versions = load_versions()
    versions["sing-box"] = latest
    save_versions(versions)

    sing_exe = get_singbox_exe()
    if not sing_exe:
        raise RuntimeError("sing-box extracted but sing-box.exe not found.")

    log(f"sing-box installed: {sing_exe}")
    return latest


def install_wintun(log, force=False):
    ensure_dirs()
    check_abort()

    dll = get_wintun_dll()
    versions = load_versions()

    if dll and versions.get("wintun") == WINTUN_VERSION and not force:
        log(f"Wintun already installed: {dll}")
        return WINTUN_VERSION

    if dll and force and versions.get("wintun") == WINTUN_VERSION:
        log(f"Wintun is up to date: {WINTUN_VERSION}")
        return WINTUN_VERSION

    zip_name = f"wintun-{WINTUN_VERSION}.zip"
    url = f"https://www.wintun.net/builds/{zip_name}"
    zip_path = DOWNLOAD_DIR / zip_name
    temp_dir = DOWNLOAD_DIR / "wintun-extract"

    download_file(url, zip_path, log)
    check_abort()

    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)

    extract_zip(zip_path, temp_dir, log)

    src = find_wintun_dll_in_tree(temp_dir)
    if not src:
        raise RuntimeError("wintun.dll not found in Wintun archive")

    log(f"Found wintun.dll in archive: {src}")

    SINGBOX_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, SINGBOX_DIR / "wintun.dll")
    shutil.copy2(src, APP_DIR / "wintun.dll")

    sing_exe = get_singbox_exe()
    if sing_exe:
        shutil.copy2(src, Path(sing_exe).parent / "wintun.dll")

    shutil.rmtree(temp_dir, ignore_errors=True)
    safe_unlink(zip_path)

    versions = load_versions()
    versions["wintun"] = WINTUN_VERSION
    save_versions(versions)

    log("Wintun installed.")
    return WINTUN_VERSION


def remove_ipv6_block(log):
    ps = (
        "Get-NetFirewallRule -DisplayName 'TorLeakGuard*' "
        "-ErrorAction SilentlyContinue | "
        "Remove-NetFirewallRule -ErrorAction SilentlyContinue"
    )

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
        log("TorLeakGuard IPv6 rules removed, if any existed.")
    except Exception as e:
        log(f"Could not remove IPv6 rules: {e}")


def add_ipv6_block(log, tor_exe=None, pt_exes=None):
    if pt_exes is None:
        pt_exes = []

    cmds = [
        "Get-NetFirewallRule -DisplayName 'TorLeakGuard*' "
        "-ErrorAction SilentlyContinue | "
        "Remove-NetFirewallRule -ErrorAction SilentlyContinue"
    ]

    if tor_exe and Path(tor_exe).exists():
        path = str(Path(tor_exe).resolve())
        cmds.append(
            f"New-NetFirewallRule -Name {ps_quote('TorLeakGuard Allow IPv6 Tor')} "
            f"-DisplayName {ps_quote('TorLeakGuard Allow IPv6 Tor')} "
            f"-Direction Outbound -Action Allow -AddressFamily IPv6 "
            f"-Program {ps_quote(path)}"
        )

    for i, pt in enumerate(pt_exes, start=1):
        if pt and Path(pt).exists():
            path = str(Path(pt).resolve())
            cmds.append(
                f"New-NetFirewallRule -Name {ps_quote(f'TorLeakGuard Allow IPv6 PT {i}')} "
                f"-DisplayName {ps_quote(f'TorLeakGuard Allow IPv6 PT {i}')} "
                f"-Direction Outbound -Action Allow -AddressFamily IPv6 "
                f"-Program {ps_quote(path)}"
            )

    cmds.append(
        f"New-NetFirewallRule -Name {ps_quote('TorLeakGuard Block IPv6 Out')} "
        f"-DisplayName {ps_quote('TorLeakGuard Block IPv6 Out')} "
        f"-Direction Outbound -Action Block -AddressFamily IPv6"
    )

    ps = "; ".join(cmds)

    try:
        p = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )

        if p.returncode != 0:
            log(f"Could not configure IPv6 rules: {p.stderr.strip()}")
        else:
            log("IPv6 firewall configured: Tor/PT allowed, other IPv6 outbound blocked.")
    except Exception as e:
        log(f"IPv6 firewall setup error: {e}")


def reset_processes(log):
    log("Stopping TorLeakGuard processes...")

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", KILL_PS],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        log(f"Process stop error: {e}")

    try:
        subprocess.run(
            [
                "netsh",
                "interface",
                "set",
                "interface",
                "name=TorLeakGuard",
                "admin=disabled",
            ],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception:
        pass

    remove_ipv6_block(log)
    time.sleep(1)


def reset_files(log, full=False):
    log("Cleaning working files...")

    for f in [
        TORRC,
        SINGBOX_CONFIG,
        STATE_FILE,
        TOR_LOG,
        SINGBOX_LOG,
        SINGBOX_CONSOLE_LOG,
    ]:
        safe_unlink(f)

    if full:
        log("Full clean of tor-data...")
        if TOR_DATA.exists():
            shutil.rmtree(TOR_DATA, ignore_errors=True)

    log("Files cleaned.")


def warn_if_tun2socks(log):
    try:
        p = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )

        for line in p.stdout.splitlines():
            if "tun2socks" in line.lower():
                log("WARNING: tun2socks process detected.")
                log("It may conflict with sing-box TUN.")
                log("If you don't need tun2socks - close it before starting.")
                break
    except Exception as e:
        log(f"Could not check tun2socks: {e}")


# ----------------------------
# Text widget clipboard + context menu (fix copy/paste in bridge field)
# ----------------------------

def _txt_select_all(w):
    w.tag_add("sel", "1.0", "end")
    return "break"


def _txt_copy(w):
    try:
        text = w.get("sel.first", "sel.last")
    except tk.TclError:
        return "break"
    try:
        w.clipboard_clear()
        w.clipboard_append(text)
    except tk.TclError:
        pass
    return "break"


def _txt_cut(w):
    _txt_copy(w)
    try:
        w.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    return "break"


def _txt_paste(w):
    try:
        text = w.clipboard_get()
    except tk.TclError:
        return "break"
    try:
        w.delete("sel.first", "sel.last")
    except tk.TclError:
        pass
    try:
        w.insert("insert", text)
    except tk.TclError:
        pass
    return "break"


def bind_text_clipboard(w):
    w.bind("<Control-a>", lambda e: _txt_select_all(e.widget))
    w.bind("<Control-A>", lambda e: _txt_select_all(e.widget))
    w.bind("<Control-c>", lambda e: _txt_copy(e.widget))
    w.bind("<Control-C>", lambda e: _txt_copy(e.widget))
    w.bind("<Control-Insert>", lambda e: _txt_copy(e.widget))
    w.bind("<Control-x>", lambda e: _txt_cut(e.widget))
    w.bind("<Control-X>", lambda e: _txt_cut(e.widget))
    w.bind("<Shift-Delete>", lambda e: _txt_cut(e.widget))
    w.bind("<Control-v>", lambda e: _txt_paste(e.widget))
    w.bind("<Control-V>", lambda e: _txt_paste(e.widget))
    w.bind("<Shift-Insert>", lambda e: _txt_paste(e.widget))

    menu = tk.Menu(w, tearoff=0)
    menu.add_command(label="Cut", command=lambda: _txt_cut(w))
    menu.add_command(label="Copy", command=lambda: _txt_copy(w))
    menu.add_command(label="Paste", command=lambda: _txt_paste(w))
    menu.add_separator()
    menu.add_command(label="Select all", command=lambda: _txt_select_all(w))

    def _popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    w.bind("<Button-3>", _popup)


# ----------------------------
# Bridge runtime status (is the obfs4 plugin REALLY connected to a bridge IP?)
# ----------------------------

def parse_bridge_rows(text):
    rows = []

    for raw in text.splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        tokens = line.split()

        if not tokens:
            continue

        if tokens[0].lower() == "bridge":
            tokens = tokens[1:]

        if len(tokens) < 2:
            continue

        rows.append((tokens[0], tokens[1]))

    return rows


def get_pt_runtime():
    pids = set()

    try:
        p = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process -Name lyrebird,obfs4proxy,'snowflake-client','snowflake_client',snowflake "
                "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id",
            ],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )

        for line in p.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.add(int(line))

    except Exception:
        pass

    remote = set()

    if pids:
        try:
            p = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )

            for line in p.stdout.splitlines():
                parts = line.split()

                if len(parts) < 5:
                    continue

                if parts[3] != "ESTABLISHED":
                    continue

                pid = parts[4]
                if pid.isdigit() and int(pid) in pids:
                    remote.add(parts[2].strip())

        except Exception:
            pass

    return pids, remote


def read_tor_log_tail(max_bytes=300000):
    try:
        if not TOR_LOG.exists():
            return ""

        size = TOR_LOG.stat().st_size

        with open(TOR_LOG, "rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
            data = f.read()

        return data.decode(errors="ignore")

    except Exception:
        return ""


def tor_quote_path(p):
    s = Path(p).as_posix()
    if " " in s:
        return f'"{s}"'
    return s


def normalize_bridge_lines(text):
    out = []

    for raw in text.splitlines():
        line = raw.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if re.match(r'(?i)^(UseBridges|ClientTransportPlugin)\b', line):
            continue

        m = re.match(r'(?i)^bridge\s+(.*)$', line)
        if m:
            line = m.group(1).strip()

        if not line:
            continue

        out.append(f"Bridge {line}")

    return out


KNOWN_PT = {
    "obfs2",
    "obfs3",
    "obfs4",
    "meek_lite",
    "webtunnel",
    "snowflake",
}


def bridge_transports(bridge_lines):
    transports = set()

    for line in bridge_lines:
        parts = line.split()

        if len(parts) >= 2 and parts[0].lower() == "bridge":
            token = parts[1].lower()
            if token in KNOWN_PT:
                transports.add(token)

    return transports


def tor_browser_pt_dirs():
    dirs = []

    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if not base:
            continue

        dirs.append(
            Path(base)
            / "Tor Browser"
            / "Browser"
            / "TorBrowser"
            / "Tor"
            / "PluggableTransports"
        )

    home = Path.home()

    dirs.append(
        home
        / "Desktop"
        / "Tor Browser"
        / "Browser"
        / "TorBrowser"
        / "Tor"
        / "PluggableTransports"
    )

    dirs.append(
        home
        / "Downloads"
        / "Tor Browser"
        / "Browser"
        / "TorBrowser"
        / "Tor"
        / "PluggableTransports"
    )

    return dirs


def get_tor_browser_url(version, log):
    base = f"https://dist.torproject.org/torbrowser/{version}/"

    try:
        html = http_get_text(base)
        links = re.findall(r'href="([^"]+)"', html)

        zip_urls = []
        portable_urls = []
        exe_urls = []

        for link in links:
            name = link.split("/")[-1]
            if not name:
                continue

            low = name.lower()

            if (
                "windows" in low
                and "x86_64" in low
                and (low.endswith(".zip") or low.endswith(".exe"))
            ):
                url = link if link.startswith("http") else base + name

                if low.endswith(".zip"):
                    zip_urls.append(url)
                elif "portable" in low:
                    portable_urls.append(url)
                else:
                    exe_urls.append(url)

        if zip_urls:
            return zip_urls[0]

        if portable_urls:
            return portable_urls[0]

        if exe_urls:
            return exe_urls[0]

    except Exception as e:
        log(f"Could not get Tor Browser file list: {e}")

    fallbacks = [
        f"{base}tor-browser-windows-x86_64-{version}.zip",
        f"{base}tor-browser-windows-x86_64-portable-{version}.exe",
        f"{base}tor-browser-windows-x86_64-{version}.exe",
        f"{base}torbrowser-install-win64-{version}_en-US.exe",
    ]

    for url in fallbacks:
        if url_exists(url):
            return url

    return None


def get_tor_browser_installer_url(version, log):
    base = f"https://dist.torproject.org/torbrowser/{version}/"

    try:
        html = http_get_text(base)
        links = re.findall(r'href="([^"]+)"', html)

        for link in links:
            name = link.split("/")[-1]
            low = name.lower()

            if low.startswith("torbrowser-install-win64") and low.endswith(".exe"):
                return link if link.startswith("http") else base + name

    except Exception as e:
        log(f"Could not get Tor Browser installer URL: {e}")

    return f"{base}torbrowser-install-win64-{version}_en-US.exe"


PT_GROUPS = [
    ["lyrebird.exe", "obfs4proxy.exe"],
    ["snowflake-client.exe", "snowflake_client.exe", "snowflake.exe"],
]

ALL_PT_NAMES = [n for g in PT_GROUPS for n in g]


def pt_group_satisfied_in(dirpath):
    dirpath = Path(dirpath)
    for group in PT_GROUPS:
        if not any((dirpath / n).exists() for n in group):
            return False
    return True


def pt_ready():
    return pt_group_satisfied_in(PT_DIR)


def pt_search_roots():
    # PT_DIR is our canonical copy target.
    # TOR_DIR: Tor Expert Bundle 15.x ships pluggable_transports (lyrebird /
    # obfs4proxy / snowflake-client / snowflake_client / snowflake) INSIDE the
    # extracted tor\ folder, so Install/Update/Status must look there too -
    # otherwise they report 'not found' while Start (which scans TOR_DIR) works.
    # find_file_in_roots rglobs every name of every group, so ALL name variants
    # (including snowflake_client.exe) are searched recursively in TOR_DIR.
    roots = [PT_DIR, TOR_DIR]

    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if not base:
            continue

        roots.append(
            Path(base)
            / "Tor Browser"
            / "Browser"
            / "TorBrowser"
            / "Tor"
            / "PluggableTransports"
        )
        roots.append(
            Path(base)
            / "Tor Browser"
            / "Browser"
            / "TorBrowser"
            / "Tor"
        )

    roots.append(TOR_BROWSER_TEMP_DIR)
    roots.append(DOWNLOAD_DIR / "tor-browser-extract")
    roots.append(APP_DIR / "tor-browser")

    return roots


def find_file_in_roots(names, roots):
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue

        for name in names:
            try:
                for p in root.rglob(name):
                    if p.is_file():
                        return p
            except Exception:
                pass

    return None


def list_pt_like_files(root):
    root = Path(root)
    found = []

    if not root.exists():
        return found

    try:
        for p in root.rglob("*"):
            if p.is_file():
                low = p.name.lower()
                if any(k in low for k in ("snowflake", "lyrebird", "obfs", "meek")):
                    found.append(str(p))
    except Exception:
        pass

    return found


def list_top_entries(root, log, limit=40):
    root = Path(root)

    if not root.exists():
        log(f"   folder does not exist: {root}")
        return

    try:
        entries = sorted(os.listdir(root))
    except Exception as e:
        log(f"   could not read {root}: {e}")
        return

    if not entries:
        log(f"   folder is EMPTY: {root}")
        return

    log(f"   top level of {root}:")
    for e in entries[:limit]:
        log("     " + e)

    if len(entries) > limit:
        log(f"     ...and {len(entries) - limit} more")


def copy_groups_from_roots(roots, log, overwrite=False):
    copied = []

    exclude = {Path(r).resolve() for r in roots if Path(r).resolve() == PT_DIR.resolve()}

    for group in PT_GROUPS:
        if not overwrite and any((PT_DIR / n).exists() for n in group):
            continue

        src = find_file_in_roots(group, [r for r in roots if Path(r).resolve() not in exclude])

        if src:
            try:
                shutil.copy2(src, PT_DIR / src.name)
                copied.append(src.name)
                log(f"Copied PT file: {src} -> {PT_DIR / src.name}")
            except Exception as e:
                log(f"Could not copy {src}: {e}")

    return copied


def missing_group_names():
    miss = []

    for group in PT_GROUPS:
        if not any((PT_DIR / n).exists() for n in group):
            miss.append(group)

    return miss


def get_7zip_installer_url(log):
    try:
        html = http_get_text("https://www.7-zip.org/download.html")
        links = re.findall(r'href="a/(7z\d+-x64\.exe)"', html)

        if links:
            def ver(s):
                m = re.match(r'7z(\d+)-x64\.exe', s)
                return int(m.group(1)) if m else 0

            links = sorted(set(links), key=ver)
            chosen = links[-1]
            log(f"Found 7-Zip installer on site: {chosen}")
            return "https://www.7-zip.org/a/" + chosen

    except Exception as e:
        log(f"Could not get 7-Zip download page: {e}")

    for v in ("2409", "2408", "2407", "2406", "2301", "2201"):
        url = f"https://www.7-zip.org/a/7z{v}-x64.exe"
        if url_exists(url):
            log(f"Using fallback 7-Zip installer: {url}")
            return url

    return "https://www.7-zip.org/a/7z2409-x64.exe"


def winget_available():
    return bool(shutil.which("winget"))


def ensure_7zip(log):
    add_7z_to_path()

    existing = find_7z()
    if existing:
        log(f"7-Zip found automatically: {existing}")
        return True

    if not is_admin():
        log("WARNING: no admin rights - 7-Zip install may fail.")

    if winget_available():
        log("winget: installing 7-Zip...")

        try:
            p = subprocess.run(
                [
                    "winget",
                    "install",
                    "--id",
                    "7zip.7zip",
                    "-e",
                    "--silent",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )

            if p.stdout and p.stdout.strip():
                log("winget stdout: " + p.stdout.strip()[-600:])

            if p.returncode != 0 and p.stderr and p.stderr.strip():
                log("winget stderr: " + p.stderr.strip()[-600:])

        except Exception as e:
            log(f"winget 7zip error: {e}")

        add_7z_to_path()

        if find_7z():
            log("7-Zip installed via winget.")
            return True

    url = get_7zip_installer_url(log)
    log(f"Downloading 7-Zip installer: {url}")

    try:
        dest = DOWNLOAD_DIR / Path(url).name
        download_file(url, dest, log)

        subprocess.run(
            [str(dest), "/S"],
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )

        deadline = time.time() + 120

        while time.time() < deadline:
            add_7z_to_path()
            if find_7z():
                safe_unlink(dest)
                log("7-Zip installed from installer.")
                return True
            time.sleep(2)

        safe_unlink(dest)
        add_7z_to_path()
        log("7-Zip installer finished but 7z.exe not found in usual paths.")

    except Exception as e:
        log(f"7-Zip install error: {e}")

    final = find_7z()
    log(f"7-Zip after all attempts: {final if final else 'NOT found'}")
    return bool(final)


def extract_tor_browser_archive(archive, extract_dir, log):
    extract_dir = Path(extract_dir)

    if extract_dir.exists():
        shutil.rmtree(extract_dir, ignore_errors=True)

    low = archive.name.lower()

    if low.endswith(".exe"):
        if not ensure_7zip(log):
            log("7-Zip unavailable - cannot extract Tor Browser exe.")
            return False

        return extract_with_7z(archive, extract_dir, log)

    try:
        extract_archive(archive, extract_dir, log)
        return True
    except Exception as e:
        log(f"Tor Browser archive extraction error: {e}")
        return False


def quiet_install_tor_browser(installer, install_dir, log):
    install_dir = Path(install_dir)

    if install_dir.exists():
        shutil.rmtree(install_dir, ignore_errors=True)

    log(f"Silent install of Tor Browser into {install_dir}")

    try:
        subprocess.run(
            [str(installer), "/S", f"/D={install_dir}"],
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )
    except Exception as e:
        log(f"Could not run Tor Browser installer: {e}")
        return False

    deadline = time.time() + 300

    while time.time() < deadline:
        if find_file_in_roots(ALL_PT_NAMES, [install_dir]):
            time.sleep(3)
            return True
        time.sleep(2)

    log("Silent Tor Browser install produced no PT files in time.")
    return False


# ----------------------------
# PT install (install & update use the SAME fetch path; TOR_DIR now searched)
# ----------------------------

def install_pt_components(log, force=False):
    ensure_dirs()
    check_abort()

    versions = load_versions()
    latest = None

    try:
        latest = get_latest_tor_version(log)
    except Exception as e:
        log(f"Could not get latest Tor Browser version: {e}")

    # Step 1: complete PT from anything already on disk (our tor\ bundle ships
    # pluggable_transports in 15.x, plus any installed Tor Browser / extracts).
    # overwrite=True so a group that already holds ONE file still gets the
    # missing sibling copied in.
    roots = pt_search_roots()
    log("Collecting PT from local sources (tor bundle / installed Tor Browser / extracts)...")
    copy_groups_from_roots(roots, log, overwrite=True)

    if pt_ready():
        log("PT components ready from local sources.")
        versions["pt_attempted"] = True
        save_versions(versions)
        return True

    # Step 2: fetch a fresh Tor Browser and extract PT. Identical path for
    # 'Install / repair' and 'Check for updates'.
    log("Local PT incomplete - fetching fresh Tor Browser to extract PT...")

    if not latest:
        log("Tor Browser version unknown - cannot fetch.")
    else:
        has7 = ensure_7zip(log)
        if not has7:
            log("WARNING: 7-Zip unavailable - portable Tor Browser exe cannot be unpacked; PT extraction will likely fail.")
        check_abort()

        url = get_tor_browser_url(latest, log)

        if url:
            dest = DOWNLOAD_DIR / Path(url).name

            try:
                download_file(url, dest, log)
                check_abort()

                extract_dir = DOWNLOAD_DIR / "tor-browser-extract"

                ok = extract_tor_browser_archive(dest, extract_dir, log)

                if ok:
                    log("Contents of extracted Tor Browser:")
                    list_top_entries(extract_dir, log)

                    like = list_pt_like_files(extract_dir)
                    if like:
                        log("PT-like files in extracted Tor Browser:")
                        for f in like:
                            log("   " + f)
                    else:
                        log("No PT files found in extracted Tor Browser.")

                    copy_groups_from_roots([extract_dir], log, overwrite=True)
                else:
                    log("Tor Browser extraction returned False (see 7-Zip lines above).")

                shutil.rmtree(extract_dir, ignore_errors=True)
                safe_unlink(dest)

            except Exception as e:
                log(f"Tor Browser download/extraction error: {e}")

            check_abort()

        if not pt_ready():
            iurl = get_tor_browser_installer_url(latest, log)

            try:
                idest = DOWNLOAD_DIR / Path(iurl).name
                download_file(iurl, idest, log)
                check_abort()

                if quiet_install_tor_browser(idest, TOR_BROWSER_TEMP_DIR, log):
                    like = list_pt_like_files(TOR_BROWSER_TEMP_DIR)
                    if like:
                        log("PT-like files after silent Tor Browser install:")
                        for f in like:
                            log("   " + f)

                    copy_groups_from_roots([TOR_BROWSER_TEMP_DIR], log, overwrite=True)

                shutil.rmtree(TOR_BROWSER_TEMP_DIR, ignore_errors=True)
                safe_unlink(idest)

            except Exception as e:
                log(f"Silent Tor Browser install error: {e}")

    # Step 3: final sweep over ALL roots (catches a fresh extract anywhere)
    copy_groups_from_roots(pt_search_roots(), log, overwrite=True)

    versions = load_versions()
    versions["pt_attempted"] = True
    save_versions(versions)

    if pt_ready():
        if latest:
            versions["pt_tor_browser"] = latest
            save_versions(versions)

        log("PT components ready.")
        return True

    miss = missing_group_names()
    log("Could not fetch PT files for groups:")

    for g in miss:
        log("  - " + " / ".join(g))

    log("7-Zip present: " + ("yes" if find_7z() else "NO -> install 7-Zip, then press 'Check for updates'"))
    log("Copy the needed files manually into " + str(PT_DIR))
    return False


def pt_status(log, mode="normal"):
    log("Checking PT components:")

    roots = pt_search_roots()

    for group in PT_GROUPS:
        found = None

        for n in group:
            p = PT_DIR / n
            if p.exists():
                found = p
                break

        if not found:
            found = find_file_in_roots(group, roots)

        label = " / ".join(group)

        if found:
            log(f"{label}: {found}")
        else:
            if mode == "normal":
                log(f"{label}: not required in plain mode (needed only for bridges)")
            else:
                log(f"{label}: not found")

    return pt_ready()


def find_pt_executable(kind, settings_path=None):
    if kind in ("obfs", "obfs4"):
        names = ["lyrebird.exe", "obfs4proxy.exe"]
    elif kind == "lyrebird":
        names = ["lyrebird.exe"]
    elif kind == "snowflake":
        names = ["snowflake-client.exe", "snowflake_client.exe", "snowflake.exe"]
    else:
        names = []

    candidates = []
    names_lower = [n.lower() for n in names]

    for n in names:
        candidates.append(PT_DIR / n)

    if settings_path:
        p = Path(settings_path)

        if p.exists():
            if p.is_file() and p.name.lower() in names_lower:
                candidates.append(p)

            base = p if p.is_dir() else p.parent

            for n in names:
                candidates.append(base / n)

    for n in names:
        w = shutil.which(n)
        if w:
            candidates.append(Path(w))

        for root in (APP_DIR, SINGBOX_DIR, TOR_DIR, PT_DIR):
            found = find_file(root, n)
            if found:
                candidates.append(found)

    for d in tor_browser_pt_dirs():
        for n in names:
            candidates.append(d / n)

    for c in candidates:
        try:
            if c and Path(c).exists():
                return Path(c)
        except Exception:
            pass

    return None


def resolve_pt_map(transports, settings_pt_path, log):
    pt_map = {}
    pt_exes = []

    for t in sorted(transports):
        exe = None

        if t in ("obfs2", "obfs3", "obfs4", "meek_lite"):
            exe = find_pt_executable("obfs", settings_pt_path)

            if not exe:
                raise RuntimeError(
                    "lyrebird.exe or obfs4proxy.exe not found.\n"
                    "The program will try to install PT automatically."
                )

        elif t == "webtunnel":
            exe = find_pt_executable("lyrebird", settings_pt_path)

            if not exe:
                raise RuntimeError(
                    "webtunnel requires lyrebird.exe.\n"
                    "The program will try to install PT automatically."
                )

        elif t == "snowflake":
            exe = find_pt_executable("snowflake", settings_pt_path)

            if not exe:
                raise RuntimeError(
                    "snowflake-client.exe not found.\n"
                    "The program will try to install PT automatically."
                )

        else:
            raise RuntimeError(f"Unknown bridge transport: {t}")

        pt_map[t] = exe

        if exe not in pt_exes:
            pt_exes.append(exe)

        log(f"PT for {t}: {exe}")

    return pt_map, pt_exes


def client_transport_plugin_lines(pt_map):
    lines = []

    for t, exe in sorted(pt_map.items()):
        lines.append(f"ClientTransportPlugin {t} exec {tor_quote_path(exe)}")

    return lines


def install_components(log, force=False):
    reset_processes(log)

    install_tor(log, force=force)
    check_abort()
    install_singbox(log, force=force)
    check_abort()
    install_wintun(log, force=force)
    check_abort()
    install_pt_components(log, force=force)

    if components_status(log):
        log("Core components ready.")
    else:
        raise RuntimeError("After install not all core components were found.")

    pt_status(log, mode="bridge")


def kill_tun2socks(log):
    log("Stopping tun2socks...")

    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process | Where-Object { $_.ProcessName -like 'tun2socks*' } | "
                "Stop-Process -Force -ErrorAction SilentlyContinue",
            ],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        log(f"tun2socks stop error: {e}")

    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Service | Where-Object { $_.Name -like 'tun2socks*' -or "
                "$_.DisplayName -like 'tun2socks*' } | "
                "Stop-Service -Force -ErrorAction SilentlyContinue",
            ],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception as e:
        log(f"tun2socks service stop error: {e}")

    for name in (
        "tun2socks.exe",
        "tun2socks64.exe",
        "tun2socks-windows-amd64.exe",
        "tun2socks-windows-386.exe",
    ):
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", name],
                capture_output=True,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            pass


def kill_all_conflicting(log):
    log("Stopping all conflicting processes...")
    log("Warning: this may close Tor Browser and other Tor/sing-box/tun2socks processes.")

    names = [
        "tor.exe",
        "sing-box.exe",
        "obfs4proxy.exe",
        "lyrebird.exe",
        "snowflake-client.exe",
        "snowflake_client.exe",
        "snowflake.exe",
        "tun2socks.exe",
        "tun2socks64.exe",
        "tun2socks-windows-amd64.exe",
        "tun2socks-windows-386.exe",
    ]

    for name in names:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", name],
                capture_output=True,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            pass

    kill_tun2socks(log)


def get_pids_for_port(port):
    pids = set()

    try:
        p = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )

        for line in p.stdout.splitlines():
            parts = line.split()

            if len(parts) < 5:
                continue

            local = parts[1]
            pid = parts[-1]

            if local.endswith(f":{port}") and pid.isdigit():
                pids.add(int(pid))

    except Exception:
        pass

    return pids


def kill_processes_on_ports(log):
    log("Freeing occupied ports...")
    log("Warning: processes listening on Tor/socks/tun2socks ports may be closed.")

    ports = {
        9050,
        9150,
        9250,
        9041,
        5354,
        1080,
        10808,
    }

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

            for key in ("socks_port", "dns_port", "control_port"):
                if state.get(key):
                    ports.add(int(state[key]))

        except Exception:
            pass

    current_pid = os.getpid()

    for port in sorted(ports):
        pids = get_pids_for_port(port)

        for pid in pids:
            if pid <= 4 or pid == current_pid:
                continue

            log(f"Killing PID {pid}, port {port}")

            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW,
                )
            except Exception:
                pass


def clean_temp_files(log):
    log("Cleaning temporary files...")

    if DOWNLOAD_DIR.exists():
        for p in DOWNLOAD_DIR.iterdir():
            try:
                if p.is_file():
                    safe_unlink(p)
                elif p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
            except Exception:
                pass

    for d in (
        DOWNLOAD_DIR / "tor-browser-extract",
        DOWNLOAD_DIR / "wintun-extract",
        TOR_BROWSER_TEMP_DIR,
    ):
        try:
            if d.exists():
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass

    log("Temporary files cleaned.")


def get_free_port(proto="tcp"):
    sock_type = socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM

    with socket.socket(socket.AF_INET, sock_type) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_tcp_port(port, timeout=60):
    end = time.time() + timeout

    while time.time() < end:
        check_abort()
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)

    return False


def singbox_env():
    env = os.environ.copy()
    env["ENABLE_DEPRECATED_LEGACY_DNS_SERVERS"] = "true"
    return env


class ControlUnavailable(Exception):
    pass


def _ctrl_recv_response(sock, buf, deadline):
    lines = []

    while True:
        while b"\r\n" in buf:
            line, buf = buf.split(b"\r\n", 1)
            t = line.decode(errors="ignore")
            lines.append(t)

            if len(t) >= 4 and t[3] == " ":
                return lines, buf

        left = deadline - time.time()
        if left <= 0:
            raise socket.timeout("timed out")

        sock.settimeout(left)
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("control connection closed")

        buf += chunk


def _ctrl_open(control_port, deadline):
    left = max(0.5, min(4.0, deadline - time.time()))

    try:
        sock = socket.create_connection(("127.0.0.1", control_port), timeout=left)
    except (socket.timeout, OSError) as e:
        raise ControlUnavailable(f"connect: {e}")

    try:
        sock.settimeout(max(0.5, deadline - time.time()))
        buf = b""

        banner, buf = _ctrl_recv_response(sock, buf, deadline)
        if not banner or not banner[-1].startswith("250"):
            raise ControlUnavailable(f"banner: {banner}")

        cookie_path = TOR_DATA / "control_auth_cookie"
        if not cookie_path.exists():
            raise ControlUnavailable("control_auth_cookie not found")

        hexc = binascii.hexlify(cookie_path.read_bytes()).decode()
        sock.sendall(f"AUTHENTICATE {hexc}\r\n".encode())

        resp, buf = _ctrl_recv_response(sock, buf, deadline)
        if not resp or not resp[-1].startswith("250"):
            raise ControlUnavailable(f"auth: {resp}")

        return sock, buf

    except ControlUnavailable:
        try:
            sock.close()
        except Exception:
            pass
        raise
    except Exception as e:
        try:
            sock.close()
        except Exception:
            pass
        raise ControlUnavailable(f"open: {e}")


def _ctrl_command(control_port, command, timeout=6):
    deadline = time.time() + timeout
    sock, buf = _ctrl_open(control_port, deadline)

    try:
        sock.sendall((command + "\r\n").encode())
        resp, buf = _ctrl_recv_response(sock, buf, deadline)
        return resp
    except ControlUnavailable:
        raise
    except Exception as e:
        raise ControlUnavailable(f"cmd: {e}")
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _get_bootstrap(control_port):
    resp = _ctrl_command(control_port, "GETINFO status/bootstrap-phase", timeout=4)
    text = "\n".join(resp)
    done = ("TAG=done" in text) or ("PROGRESS=100" in text)
    m = re.search(r"PROGRESS=(\d+)", text)
    prog = int(m.group(1)) if m else -1
    return prog, done


def tor_wait_bootstrap(control_port, timeout, log):
    deadline = time.time() + timeout
    consec_fail = 0
    seen = False
    last_prog = -1

    while time.time() < deadline:
        check_abort()

        try:
            prog, done = _get_bootstrap(control_port)
            consec_fail = 0
            seen = True

            if prog != last_prog:
                log(f"Tor bootstrap: {prog}%")
                last_prog = prog

            if done or prog >= 100:
                log("Tor bootstrap: ready (100%).")
                return True

        except ControlUnavailable:
            consec_fail += 1
            if not seen and consec_fail >= 4:
                log("ControlPort not responding - skipping bootstrap wait (decisive test = internet probe via Tor).")
                return False

        except Exception as e:
            consec_fail += 1
            log(f"bootstrap poll: {e}")
            if consec_fail >= 4:
                log("ControlPort unstable - skipping bootstrap wait (decisive test = internet probe).")
                return False

        time.sleep(2)

    if seen:
        log("Tor did not reach 100% in time (continuing - decisive test is the internet probe).")
    else:
        log("ControlPort did not answer during bootstrap wait (continuing).")

    return False


def socks5_probe(socks_port, timeout_each=12):
    targets = [
        ("1.1.1.1", 443),
        ("8.8.8.8", 443),
        ("9.9.9.9", 53),
    ]

    for host, port in targets:
        try:
            with socket.create_connection(("127.0.0.1", socks_port), timeout=timeout_each) as s:
                s.sendall(b"\x05\x01\x00")
                hdr = s.recv(2)
                if len(hdr) < 2 or hdr[0] != 0x05 or hdr[1] != 0x00:
                    continue

                req = b"\x05\x01\x00\x01" + socket.inet_aton(host) + port.to_bytes(2, "big")
                s.sendall(req)

                resp = s.recv(10)
                if len(resp) >= 2 and resp[0] == 0x05 and resp[1] == 0x00:
                    return True, f"{host}:{port}"

        except Exception:
            continue

    return False, ""


def write_torrc(socks_port, dns_port, control_port, settings, pt_map, log):
    ensure_dirs()

    lines = [
        "# Managed by TorLeakGuard",
        f"DataDirectory {TOR_DATA.as_posix()}",
        f"SocksPort 127.0.0.1:{socks_port}",
        f"DNSPort 127.0.0.1:{dns_port}",
        "ClientUseIPv4 1",
        "ClientUseIPv6 0",
        "ClientPreferIPv6ORPort 0",
        "ClientPreferIPv6DirPort 0",
        "IPv6Exit 0",
        "AutomapHostsOnResolve 1",
        "VirtualAddrNetworkIPv4 10.192.0.0/10",
        f"ControlPort 127.0.0.1:{control_port}",
        "CookieAuthentication 1",
    ]

    if settings.get("prevent_circuit_change", True):
        lines.append("MaxCircuitDirtiness 31536000")
    else:
        lines.append("MaxCircuitDirtiness 600")

    if settings.get("padding", True):
        lines.append("# Anti traffic-analysis / anti pattern-throttling padding")
        lines.append("ConnectionPadding 1")
        lines.append("ReducedConnectionPadding 0")
        lines.append("CircuitPadding 1")
        lines.append("ReducedCircuitPadding 0")

    mode = settings.get("mode", "normal")

    if mode == "bridge":
        bridge_lines = normalize_bridge_lines(settings.get("bridges", ""))

        if not bridge_lines:
            raise RuntimeError(
                "Bridges mode is on but bridge lines are empty.\n"
                "Paste bridges from Tor Browser into the text field."
            )

        lines.append("UseBridges 1")

        transports = bridge_transports(bridge_lines)

        if transports:
            if not pt_map:
                pt_map, _ = resolve_pt_map(
                    transports,
                    settings.get("pt_path", ""),
                    log
                )

            lines.extend(client_transport_plugin_lines(pt_map))

        lines.extend(bridge_lines)

    else:
        lines.append("UseBridges 0")

    TORRC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"torrc written: {TORRC}")


def build_singbox_config(
    socks_port,
    dns_port,
    tor_exe,
    sing_exe,
    strict_route,
    stack,
    pt_exes=None,
    sniff_action=True,
):
    if pt_exes is None:
        pt_exes = []

    process_names = [
        "tor.exe",
        "tor",
        "sing-box.exe",
        "sing-box",
    ]

    process_paths = [
        str(tor_exe),
        str(sing_exe),
    ]

    for pt in pt_exes:
        pt = Path(pt)
        process_names.append(pt.name)
        process_names.append(pt.stem)
        process_paths.append(str(pt))

    inbound = {
        "type": "tun",
        "tag": "tun-in",
        "interface_name": "TorLeakGuard",
        "address": ["172.19.0.1/30"],
        "mtu": 1500,
        "auto_route": True,
        "strict_route": strict_route,
        "stack": stack,
    }

    route_rules = []

    if sniff_action:
        route_rules.append({"action": "sniff"})

    route_rules.append({"port": [53], "action": "hijack-dns"})

    route_rules += [
        {
            "process_name": process_names,
            "outbound": "direct",
        },
        {
            "process_path": process_paths,
            "outbound": "direct",
        },
        {
            "ip_cidr": [
                "127.0.0.0/8",
            ],
            "outbound": "direct",
        },
        {
            "network": "udp",
            "port": [67, 68],
            "outbound": "direct",
        },
        {
            "ip_version": 6,
            "outbound": "block",
        },
        {
            "network": "udp",
            "outbound": "block",
        },
        {
            "ip_cidr": [
                "10.0.0.0/8",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "169.254.0.0/16",
                "224.0.0.0/4",
                "255.255.255.255/32",
            ],
            "outbound": "block",
        },
    ]

    return {
        "log": {
            "level": "info",
            "output": SINGBOX_LOG.as_posix(),
        },
        "dns": {
            "servers": [
                {
                    "type": "udp",
                    "tag": "tor-dns",
                    "server": "127.0.0.1",
                    "server_port": dns_port,
                }
            ],
            "rules": [
                {
                    "query_type": [
                        "A",
                        "AAAA",
                        "CNAME",
                        "TXT",
                        "MX",
                        "NS",
                        "SOA",
                        "SRV",
                        "PTR",
                    ],
                    "server": "tor-dns",
                }
            ],
            "final": "tor-dns",
        },
        "inbounds": [inbound],
        "outbounds": [
            {
                "type": "socks",
                "tag": "tor",
                "server": "127.0.0.1",
                "server_port": socks_port,
                "version": "5",
            },
            {
                "type": "direct",
                "tag": "direct",
            },
            {
                "type": "block",
                "tag": "block",
            },
        ],
        "route": {
            "rules": route_rules,
            "final": "tor",
        },
    }


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TorLeakGuard: Tor + sing-box + bridges + circumvention")
        self.root.geometry("1040x1040")

        self.busy = False
        self.handles = []
        self.spawned = []
        self.last_newnym = 0.0

        self.settings = load_settings()

        self.mode_var = tk.StringVar(value=self.settings.get("mode", "normal"))
        self.prevent_var = tk.BooleanVar(value=self.settings.get("prevent_circuit_change", True))
        self.padding_var = tk.BooleanVar(value=self.settings.get("padding", True))
        self.pt_path_var = tk.StringVar(value=self.settings.get("pt_path", ""))
        self.pt_label_var = tk.StringVar(value="obfs4/lyrebird: ? | snowflake: ?  (press 'Check bridge status')")

        self.reset_tun2socks_var = tk.BooleanVar(value=True)
        self.reset_ports_var = tk.BooleanVar(value=False)
        self.reset_temp_var = tk.BooleanVar(value=True)
        self.reset_tordata_var = tk.BooleanVar(value=False)
        self.reset_all_proc_var = tk.BooleanVar(value=False)

        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, **pad)

        ttk.Button(
            top,
            text="Check components",
            command=self.on_check,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            top,
            text="Install / repair components",
            command=self.on_install,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            top,
            text="Check for updates",
            command=self.on_update,
        ).pack(side=tk.LEFT, padx=2)

        mid = ttk.Frame(self.root)
        mid.pack(fill=tk.X, **pad)

        ttk.Button(
            mid,
            text="Start Tor + protection",
            command=self.on_start,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            mid,
            text="Stop (restore internet)",
            command=self.on_stop,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            mid,
            text="RESET (emergency eject)",
            command=self.on_reset,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            mid,
            text="New circuit (NEWNYM)",
            command=self.on_newnym,
        ).pack(side=tk.LEFT, padx=2)

        reset_frame = ttk.LabelFrame(self.root, text="RESET / emergency eject options")
        reset_frame.pack(fill=tk.X, **pad)

        ttk.Label(
            reset_frame,
            text="RESET never waits for a running task: it aborts it, force-kills hung "
                 "processes by saved PID, drops TUN + IPv6 rules, cleans files, and keeps the window open.",
            justify=tk.LEFT,
            wraplength=980,
        ).pack(anchor=tk.W, padx=6, pady=2)

        ttk.Checkbutton(
            reset_frame,
            text="Stop tun2socks",
            variable=self.reset_tun2socks_var,
        ).pack(anchor=tk.W, padx=6, pady=1)

        ttk.Checkbutton(
            reset_frame,
            text="Force-free occupied ports",
            variable=self.reset_ports_var,
        ).pack(anchor=tk.W, padx=6, pady=1)

        ttk.Checkbutton(
            reset_frame,
            text="Clean temporary files",
            variable=self.reset_temp_var,
        ).pack(anchor=tk.W, padx=6, pady=1)

        ttk.Checkbutton(
            reset_frame,
            text="Full clean of tor-data",
            variable=self.reset_tordata_var,
        ).pack(anchor=tk.W, padx=6, pady=1)

        ttk.Checkbutton(
            reset_frame,
            text="Stop ALL conflicting processes by name (dangerous: also closes Tor Browser / any tor.exe / sing-box.exe)",
            variable=self.reset_all_proc_var,
        ).pack(anchor=tk.W, padx=6, pady=1)

        mode_frame = ttk.LabelFrame(self.root, text="Connection mode")
        mode_frame.pack(fill=tk.X, **pad)

        ttk.Radiobutton(
            mode_frame,
            text="Plain Tor (protected)",
            variable=self.mode_var,
            value="normal",
        ).pack(anchor=tk.W, padx=6, pady=2)

        ttk.Radiobutton(
            mode_frame,
            text="Connect via bridges",
            variable=self.mode_var,
            value="bridge",
        ).pack(anchor=tk.W, padx=6, pady=2)

        ttk.Checkbutton(
            mode_frame,
            text="Don't rotate circuit automatically (MaxCircuitDirtiness = 1 year)",
            variable=self.prevent_var,
        ).pack(anchor=tk.W, padx=6, pady=2)

        circum_frame = ttk.LabelFrame(self.root, text="Circumvention & anti-analysis (DPI / throttling)")
        circum_frame.pack(fill=tk.X, **pad)

        ttk.Checkbutton(
            circum_frame,
            text="Enable connection & circuit padding (defeats traffic-pattern throttling / analysis)",
            variable=self.padding_var,
        ).pack(anchor=tk.W, padx=6, pady=2)

        circum_btn = ttk.Frame(circum_frame)
        circum_btn.pack(fill=tk.X, padx=6, pady=2)

        ttk.Button(
            circum_btn,
            text="Apply recommended anti-DPI preset",
            command=self.on_apply_preset,
        ).pack(side=tk.LEFT)

        ttk.Label(
            circum_btn,
            text="(switches to Bridges + padding; then paste obfs4/webtunnel/snowflake bridges below)",
        ).pack(side=tk.LEFT, padx=8)

        hint = ttk.Label(
            circum_frame,
            text=CIRCUM_HINT,
            justify=tk.LEFT,
            wraplength=980,
        )
        hint.pack(anchor=tk.W, padx=8, pady=4)

        bridge_frame = ttk.LabelFrame(
            self.root,
            text="Bridges from Tor Browser: obfs4 / meek_lite / webtunnel / snowflake",
        )
        bridge_frame.pack(fill=tk.BOTH, expand=True, **pad)

        pt_frame = ttk.Frame(bridge_frame)
        pt_frame.pack(fill=tk.X, padx=4, pady=4)

        ttk.Label(
            pt_frame,
            text="PT file:",
        ).pack(side=tk.LEFT)

        ttk.Entry(
            pt_frame,
            textvariable=self.pt_path_var,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        ttk.Button(
            pt_frame,
            text="Choose PT file",
            command=self.on_choose_pt,
        ).pack(side=tk.LEFT)

        bridges_wrap = ttk.Frame(bridge_frame)
        bridges_wrap.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.bridges_text = tk.Text(bridges_wrap, height=5, wrap=tk.NONE)

        bv = ttk.Scrollbar(bridges_wrap, orient=tk.VERTICAL, command=self.bridges_text.yview)
        bh = ttk.Scrollbar(bridges_wrap, orient=tk.HORIZONTAL, command=self.bridges_text.xview)
        self.bridges_text.config(yscrollcommand=bv.set, xscrollcommand=bh.set)

        self.bridges_text.grid(row=0, column=0, sticky="nsew")
        bv.grid(row=0, column=1, sticky="ns")
        bh.grid(row=1, column=0, sticky="ew")
        bridges_wrap.rowconfigure(0, weight=1)
        bridges_wrap.columnconfigure(0, weight=1)

        self.bridges_text.insert(tk.END, self.settings.get("bridges", ""))
        bind_text_clipboard(self.bridges_text)

        status_btn = ttk.Frame(bridge_frame)
        status_btn.pack(fill=tk.X, padx=4, pady=2)

        ttk.Button(
            status_btn,
            text="Check bridge status",
            command=self.on_check_bridges,
        ).pack(side=tk.LEFT)

        ttk.Label(
            status_btn,
            text="  [ACTIVE] = obfs4 plugin really connected to that bridge IP  |  "
                 "[no connection] = plugin up but not on this bridge  |  "
                 "[NO PT PROCESS] = plugin missing, bridges cannot work",
            wraplength=760,
            justify=tk.LEFT,
        ).pack(side=tk.LEFT, padx=6)

        ttk.Label(
            bridge_frame,
            textvariable=self.pt_label_var,
        ).pack(anchor=tk.W, padx=6, pady=2)

        self.bridge_status_lb = tk.Listbox(bridge_frame, height=4, activestyle="none")
        self.bridge_status_lb.pack(fill=tk.X, padx=4, pady=4)

        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, **pad)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        bind_text_clipboard(self.log_text)

        self.log("Ready.")
        self.log(f"Working folder: {APP_DIR}")
        self.log("Install/update/start/stop request administrator rights (UAC). RESET does NOT - it always works.")
        self.log("RESET = emergency eject: aborts any task, force-kills hung processes, drops TUN/IPv6, keeps window open.")
        self.log("Bridge field: Ctrl+V to paste, right-click for menu, horizontal scrollbar for long lines.")
        self.log("After Start in bridge mode, bridge status auto-refreshes; or press 'Check bridge status' anytime.")

    def log(self, msg):
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        self.root.after(0, _append)

    def run_thread(self, func):
        if self.busy:
            self.log("Another operation is running. Wait for it, or press RESET to eject now.")
            return

        self.busy = True

        def wrapper():
            try:
                func()
            except Aborted:
                self.log("Background task aborted by RESET (emergency eject).")
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                self.root.after(0, lambda: setattr(self, "busy", False))

        threading.Thread(target=wrapper, daemon=True).start()

    def collect_settings(self):
        return {
            "mode": self.mode_var.get(),
            "bridges": self.bridges_text.get("1.0", tk.END).strip(),
            "pt_path": self.pt_path_var.get().strip(),
            "prevent_circuit_change": bool(self.prevent_var.get()),
            "padding": bool(self.padding_var.get()),
        }

    def collect_reset_options(self):
        return {
            "tun2socks": bool(self.reset_tun2socks_var.get()),
            "ports": bool(self.reset_ports_var.get()),
            "temp": bool(self.reset_temp_var.get()),
            "tor_data": bool(self.reset_tordata_var.get()),
            "all_processes": bool(self.reset_all_proc_var.get()),
        }

    def save_current_settings(self):
        save_settings(self.collect_settings())

    def on_close(self):
        try:
            self.save_current_settings()
        except Exception:
            pass

        self.root.destroy()

    def on_check(self):
        self.run_thread(self.task_check)

    def on_install(self):
        if not is_admin():
            self.log("Installing components needs admin rights (for 7-Zip/winget).")
            self.log("Requesting UAC...")
            try:
                restart_as_admin("install")
            except Exception as e:
                self.log(str(e))
            return

        self.run_thread(self.task_install)

    def on_update(self):
        if not is_admin():
            self.log("Updating components needs admin rights.")
            self.log("Requesting UAC...")
            try:
                restart_as_admin("update")
            except Exception as e:
                self.log(str(e))
            return

        self.run_thread(self.task_update)

    def on_start(self):
        if not is_admin():
            self.log("Starting TUN and firewall needs admin rights.")
            self.log("Requesting UAC...")
            try:
                restart_as_admin("start")
            except Exception as e:
                self.log(str(e))
            return

        settings = self.collect_settings()
        self.run_thread(lambda: self.task_start(settings))

    def on_stop(self):
        if not is_admin():
            self.log("Stopping needs admin rights (firewall/TUN).")
            self.log("Requesting UAC...")
            try:
                restart_as_admin("stop")
            except Exception as e:
                self.log(str(e))
            return

        self.run_thread(self.task_stop)

    def on_reset(self):
        self.log("=== EMERGENCY RESET (eject) === forcing immediate stop, NOT waiting for any task...")
        abort_now()
        self.busy = False
        options = self.collect_reset_options()
        threading.Thread(target=lambda: self._emergency_reset_work(options), daemon=True).start()

    def on_newnym(self):
        self.run_thread(self.task_newnym)

    def on_apply_preset(self):
        self.mode_var.set("bridge")
        self.padding_var.set(True)
        self.log("Anti-DPI preset applied: mode = Bridges, padding = ON.")
        self.log("Now paste obfs4 / webtunnel / snowflake bridges into the field below.")
        self.log("Best against DPI on Tor itself: webtunnel (looks like HTTPS) or snowflake (looks like WebRTC).")
        self.log("Get bridges: Tor Browser -> Settings -> Connection -> 'Use a bridge' -> 'Provide a bridge' / request from torproject.org.")

    def on_check_bridges(self):
        txt = self.bridges_text.get("1.0", tk.END)
        self.run_thread(lambda: self.refresh_bridge_status(txt, log_too=True))

    def on_choose_pt(self):
        filename = filedialog.askopenfilename(
            title="Choose PT file: obfs4proxy.exe / lyrebird.exe / snowflake-client.exe",
            filetypes=[
                ("Executable files", "*.exe"),
                ("All files", "*.*"),
            ],
        )

        if filename:
            self.pt_path_var.set(filename)
            self.log(f"Chosen PT file: {filename}")

    # ----------------------------
    # Bridge status (proof the bridge carries traffic)
    # ----------------------------

    def _bridge_status_compute(self, bridges_text):
        obfs = find_pt_executable("obfs", None)
        sf = find_pt_executable("snowflake", None)
        pt_text = (
            f"obfs4/lyrebird: {'FOUND' if obfs else 'MISSING'} | "
            f"snowflake: {'FOUND' if sf else 'MISSING'}"
        )

        rows = parse_bridge_rows(bridges_text)
        pids, remote = get_pt_runtime()

        lines = []
        any_active = False

        if not rows:
            lines.append("(no bridge lines parsed from the field)")
        else:
            for transport, ipport in rows:
                ip = ipport.split(":")[0] if ":" in ipport else ipport

                active = (ipport in remote) or any(
                    r == ipport or r.startswith(ip + ":") for r in remote
                )

                if active:
                    st = "[ACTIVE]"
                    any_active = True
                elif not pids:
                    st = "[NO PT PROCESS]"
                else:
                    st = "[no connection]"

                lines.append(f"{transport:10} {ipport:26} {st}")

        tail = read_tor_log_tail()
        low = tail.lower()
        has_bridge_log = (
            "conn_bridge" in low
            or "connected to a bridge" in low
            or "managed proxy" in low
            or ("bootstrapped" in low and "bridge" in low)
        )
        relay_only = ("connecting to a relay" in low) and not has_bridge_log

        if not rows:
            verdict = "No bridges in the field."
        elif not pids:
            verdict = "PT plugin NOT running -> bridges CANNOT work. Run Install/repair or check the PT label."
        elif any_active:
            verdict = "BRIDGES IN USE: yes (obfs4 plugin has an open connection to a bridge IP)."
        else:
            verdict = "PT plugin running but no bridge connection yet (Tor still bootstrapping, or bridges are dead)."

        if relay_only:
            verdict += "  WARNING: tor.log shows 'connecting to a relay' (Tor may be ignoring bridges)."
        elif has_bridge_log and rows:
            verdict += "  tor.log confirms bridge bootstrap."

        return pt_text, lines, verdict, tail

    def _apply_bridge_status_ui(self, pt_text, lines):
        self.pt_label_var.set(pt_text)
        self.bridge_status_lb.delete(0, tk.END)
        for ln in lines:
            self.bridge_status_lb.insert(tk.END, ln)

    def refresh_bridge_status(self, bridges_text, log_too=False):
        pt_text, lines, verdict, tail = self._bridge_status_compute(bridges_text)

        self.root.after(0, lambda: self._apply_bridge_status_ui(pt_text, lines))

        if log_too:
            self.log("---- Bridge status ----")
            self.log(pt_text)
            for ln in lines:
                self.log("  " + ln)
            self.log("VERDICT: " + verdict)

            low = tail.lower()
            shown = 0
            for raw in tail.splitlines():
                s = raw.strip()
                ls = s.lower()
                if not s:
                    continue
                if any(k in ls for k in ("bridge", "obfs4", "managed proxy", "pluggable", "[warn]", "[err]")):
                    self.log("  [tor] " + s)
                    shown += 1
                    if shown >= 8:
                        break

    def task_check(self):
        ensure_dirs()
        self.log("Checking components...")

        if components_status(self.log):
            self.log("Core components found.")
        else:
            self.log("Not all core components found. Press 'Install / repair components'.")

        pt_status(self.log, mode=self.mode_var.get())

    def task_install(self):
        ensure_dirs()
        abort_clear()
        self.log("Installing / repairing components...")
        install_components(self.log, force=False)

    def task_update(self):
        ensure_dirs()
        abort_clear()
        self.log("Checking for updates...")
        install_components(self.log, force=True)

    def task_stop(self):
        ensure_dirs()
        self.log("Stop: stopping protection and restoring normal internet...")

        reset_processes(self.log)

        for h in self.handles:
            try:
                h.close()
            except Exception:
                pass

        self.handles = []
        self.spawned = []

        safe_unlink(STATE_FILE)
        self.log("Stop done. Normal internet should work.")

    # ----------------------------
    # Emergency eject work (runs in its own thread, never blocked by busy)
    # ----------------------------

    def _kill_saved_pids(self):
        if not STATE_FILE.exists():
            return

        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return

        for key in ("tor_pid", "sing_box_pid"):
            pid = state.get(key)
            if not pid:
                continue
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW,
                )
                self.log(f"Emergency kill PID {pid} ({key}).")
            except Exception:
                pass

    def _kill_spawned(self):
        for proc in list(self.spawned):
            try:
                if proc.poll() is None:
                    proc.kill()
                    self.log(f"Emergency kill spawned PID {proc.pid}.")
            except Exception:
                pass

        self.spawned = []

    def _emergency_reset_work(self, options):
        try:
            self._kill_spawned()
            self._kill_saved_pids()

            if options.get("all_processes"):
                kill_all_conflicting(self.log)
            elif options.get("tun2socks"):
                kill_tun2socks(self.log)

            reset_processes(self.log)

            if options.get("ports"):
                kill_processes_on_ports(self.log)

            for h in list(self.handles):
                try:
                    h.close()
                except Exception:
                    pass

            self.handles = []

            reset_files(self.log, full=options.get("tor_data", False))

            if options.get("temp"):
                clean_temp_files(self.log)

            self.log("=== EMERGENCY RESET done === protection stopped, window stays open.")

        except Exception as e:
            self.log(f"Emergency reset error: {e}")

        finally:
            abort_clear()

    def task_reset(self, options):
        self._emergency_reset_work(options)

    def task_newnym(self):
        if not STATE_FILE.exists():
            self.log("Start Tor + protection first.")
            return

        now = time.time()
        if now - self.last_newnym < 10:
            self.log("Circuit change too frequent. Wait 10 seconds.")
            return

        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            self.log(f"Could not read state.json: {e}")
            return

        control_port = state.get("control_port")
        if not control_port:
            self.log("state.json has no control_port. Restart protection.")
            return

        try:
            resp = _ctrl_command(int(control_port), "SIGNAL NEWNYM", timeout=6)

            if not resp or not resp[-1].startswith("250"):
                raise RuntimeError(str(resp))

            self.last_newnym = now
            self.log("NEWNYM sent.")
            self.log("Tor will build new circuits for new connections.")
            self.log("For a fully new IP - restart your browser.")

        except ControlUnavailable:
            self.log("ControlPort unavailable - NEWNYM via it is impossible.")
            self.log("To change the circuit: press 'Stop (restore internet)', then 'Start Tor + protection' - Tor will rebuild circuits.")

        except Exception as e:
            self.log(f"NEWNYM error: {e}")

    def rollback(self, tor_proc, sing_proc, log):
        log("ROLLBACK: stopping Tor/sing-box and restoring normal internet...")

        for proc in (sing_proc, tor_proc):
            if proc is None:
                continue
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        for h in self.handles:
            try:
                h.close()
            except Exception:
                pass

        self.handles = []
        self.spawned = []

        try:
            subprocess.run(
                [
                    "netsh",
                    "interface",
                    "set",
                    "interface",
                    "name=TorLeakGuard",
                    "admin=disabled",
                ],
                capture_output=True,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception:
            pass

        remove_ipv6_block(log)
        safe_unlink(STATE_FILE)
        log("Rollback done. Normal internet should work.")

    def task_start(self, settings):
        ensure_dirs()
        abort_clear()
        save_settings(settings)

        self.log("Preparing to start...")
        self.spawned = []

        warn_if_tun2socks(self.log)

        reset_processes(self.log)

        for h in self.handles:
            try:
                h.close()
            except Exception:
                pass

        self.handles = []

        reset_files(self.log, full=False)

        if not components_status(self.log):
            self.log("Components missing. Installing...")
            install_components(self.log, force=False)

        check_abort()

        tor_exe = get_tor_exe()
        sing_exe = get_singbox_exe()

        if not tor_exe or not sing_exe:
            self.log("tor.exe or sing-box.exe not found. Start impossible.")
            return

        wintun = get_wintun_dll()
        if wintun and sing_exe:
            target = Path(sing_exe).parent / "wintun.dll"
            try:
                if not target.exists():
                    shutil.copy2(wintun, target)
            except Exception as e:
                self.log(f"Could not copy wintun.dll next to sing-box.exe: {e}")

        versions = load_versions()

        if not pt_ready() and not versions.get("pt_attempted"):
            self.log("Fetching PT components (needed for bridges; one-time)...")
            try:
                install_pt_components(self.log, force=False)
            except Aborted:
                raise
            except Exception as e:
                self.log(f"PT auto-fetch failed: {e}")

        pt_map = {}
        pt_exes = []

        if settings.get("mode") == "bridge":
            bridge_lines = normalize_bridge_lines(settings.get("bridges", ""))
            transports = bridge_transports(bridge_lines)

            if transports:
                try:
                    pt_map, pt_exes = resolve_pt_map(
                        transports,
                        settings.get("pt_path", ""),
                        self.log
                    )
                except Exception as e:
                    self.log(str(e))
                    self.log("Trying to install PT components automatically...")
                    install_pt_components(self.log, force=False)

                    pt_map, pt_exes = resolve_pt_map(
                        transports,
                        settings.get("pt_path", ""),
                        self.log
                    )

        socks_port = get_free_port("tcp")
        dns_port = get_free_port("udp")
        control_port = get_free_port("tcp")

        self.log(f"Chosen ports: SOCKS={socks_port}, DNS={dns_port}, Control={control_port}")

        write_torrc(
            socks_port=socks_port,
            dns_port=dns_port,
            control_port=control_port,
            settings=settings,
            pt_map=pt_map,
            log=self.log,
        )

        if settings.get("padding", True):
            self.log("Connection/circuit padding enabled (anti traffic-analysis / anti pattern-throttling).")

        self.log("Starting Tor...")

        tor_log_f = open(TOR_LOG, "wb")
        self.handles.append(tor_log_f)

        tor_proc = subprocess.Popen(
            [str(tor_exe), "-f", str(TORRC)],
            stdout=tor_log_f,
            stderr=tor_log_f,
            creationflags=CREATE_NO_WINDOW,
            cwd=str(TOR_DIR),
        )
        self.spawned.append(tor_proc)

        if not wait_tcp_port(socks_port, timeout=60):
            self.log("Tor did not raise SOCKS port in time. See tor.log.")
            self.rollback(tor_proc, None, self.log)
            return

        self.log("Tor SOCKS port is listening.")

        cookie_path = TOR_DATA / "control_auth_cookie"
        deadline = time.time() + 30

        while time.time() < deadline and not cookie_path.exists():
            check_abort()
            time.sleep(0.3)

        if not cookie_path.exists():
            self.log("control_auth_cookie not found. Circuit-change button may not work.")

        tor_wait_bootstrap(control_port, timeout=20, log=self.log)

        started = False
        sing_proc = None
        chosen = None

        variants = []
        for sr in (True, False):
            for st in ("system", "gvisor"):
                for sn in (True, False):
                    variants.append({
                        "strict_route": sr,
                        "stack": st,
                        "sniff_action": sn,
                    })

        env = singbox_env()

        for v in variants:
            check_abort()

            self.log(
                f"Trying sing-box: strict_route={v['strict_route']}, "
                f"stack={v['stack']}, sniff_action={v['sniff_action']}"
            )

            cfg = build_singbox_config(
                socks_port=socks_port,
                dns_port=dns_port,
                tor_exe=tor_exe,
                sing_exe=sing_exe,
                strict_route=v["strict_route"],
                stack=v["stack"],
                pt_exes=pt_exes,
                sniff_action=v["sniff_action"],
            )

            SINGBOX_CONFIG.write_text(
                json.dumps(cfg, indent=2),
                encoding="utf-8",
            )

            check = subprocess.run(
                [str(sing_exe), "check", "-c", str(SINGBOX_CONFIG)],
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                cwd=str(APP_DIR),
                env=env,
            )

            if check.returncode != 0:
                self.log("sing-box check failed:")
                self.log(check.stderr.strip() or check.stdout.strip())
                continue

            sing_console_f = open(SINGBOX_CONSOLE_LOG, "wb")
            self.handles.append(sing_console_f)

            sing_proc = subprocess.Popen(
                [str(sing_exe), "run", "-c", str(SINGBOX_CONFIG)],
                stdout=sing_console_f,
                stderr=sing_console_f,
                creationflags=CREATE_NO_WINDOW,
                cwd=str(APP_DIR),
                env=env,
            )
            self.spawned.append(sing_proc)

            time.sleep(4)

            if sing_proc.poll() is not None:
                self.log("sing-box exited immediately. See sing-box.log and sing-box-console.log.")
                sing_proc = None
                continue

            ok, target = socks5_probe(socks_port, timeout_each=12)

            if ok:
                started = True
                chosen = v
                self.log(f"Internet probe via Tor PASSED ({target}). Protection is working.")
                break

            self.log("Internet probe via Tor failed after TUN up - trying another config variant...")

            try:
                if sing_proc.poll() is None:
                    sing_proc.kill()
            except Exception:
                pass

            sing_proc = None

            try:
                subprocess.run(
                    [
                        "netsh",
                        "interface",
                        "set",
                        "interface",
                        "name=TorLeakGuard",
                        "admin=disabled",
                    ],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW,
                )
            except Exception:
                pass

            time.sleep(1)

        if not started:
            self.log("No sing-box variant gave working internet via Tor.")
            self.log("Possible routing loop or Tor cannot reach the network.")
            self.rollback(tor_proc, sing_proc, self.log)
            return

        add_ipv6_block(self.log, tor_exe=tor_exe, pt_exes=pt_exes)

        state = {
            "tor_pid": tor_proc.pid,
            "sing_box_pid": sing_proc.pid,
            "socks_port": socks_port,
            "dns_port": dns_port,
            "control_port": control_port,
            "mode": settings.get("mode", "normal"),
            "pt_exes": [str(x) for x in pt_exes],
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

        self.log("Started.")
        self.log(f"SOCKS5 Tor: 127.0.0.1:{socks_port}")
        self.log(f"DNS Tor:    127.0.0.1:{dns_port}")
        self.log(f"Control:    127.0.0.1:{control_port}")
        self.log(
            f"sing-box config: strict_route={chosen['strict_route']}, "
            f"stack={chosen['stack']}, sniff_action={chosen['sniff_action']}"
        )

        if settings.get("mode") == "bridge":
            self.log("Mode: bridges.")
        else:
            self.log("Mode: plain Tor.")

        if settings.get("prevent_circuit_change", True):
            self.log("Automatic circuit rotation every 10 minutes is disabled.")
        else:
            self.log("Using Tor's default circuit rotation behavior.")

        self.log("To stop press 'Stop (restore internet)'. Emergency = 'RESET (emergency eject)'. Manual circuit = 'New circuit (NEWNYM)'.")

        if settings.get("mode") == "bridge":
            self.refresh_bridge_status(settings.get("bridges", ""), log_too=True)


def main():
    ensure_dirs()

    root = tk.Tk()
    app = App(root)

    if "--autostart" in sys.argv:
        root.after(500, app.on_start)

    if "--autoinstall" in sys.argv:
        root.after(500, app.on_install)

    if "--autoupdate" in sys.argv:
        root.after(500, app.on_update)

    if "--autostop" in sys.argv:
        root.after(500, app.on_stop)

    root.mainloop()


if __name__ == "__main__":
    main()