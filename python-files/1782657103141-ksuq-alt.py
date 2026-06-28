import subprocess
import sys
import os
import time

# ── Auto-install ──────────────────────────────────────────────────────────────
def _install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _pkg in ("colorama", "requests"):
    try:
        __import__(_pkg)
    except ImportError:
        _install(_pkg)

import re
import glob
from datetime import datetime
import requests
from colorama import init, Fore, Style

init(autoreset=True)

# ── Constants ─────────────────────────────────────────────────────────────────
C   = Fore.LIGHTCYAN_EX          # main light-blue colour
W   = Fore.WHITE
R   = Fore.RED
DIM = Style.DIM
B   = Style.BRIGHT
RST = Style.RESET_ALL
DIV = C + "─" * 60

LOG_PATH = os.path.expandvars(r"%LOCALAPPDATA%\Roblox\logs")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Content-Type": "application/json",
}

# ── Console setup ─────────────────────────────────────────────────────────────
os.system("title  TAXIDEV ALT SCANNER")
os.system("mode con cols=62 lines=40")
os.system("cls")

# ── Banner ────────────────────────────────────────────────────────────────────
def banner():
    os.system("cls")
    print(C + B + r"""
  ╔════════════════════════════════════════════════════════╗
  ║           T A X I D E V   A L T   S C A N N E R      ║
  ╚════════════════════════════════════════════════════════╝
""")

# ── Scan logs (silent) ────────────────────────────────────────────────────────
PATTERNS = [
    r'userId["\s:=]+(\d{7,})',
    r'UserId["\s:=]+(\d{7,})',
    r'"userId"\s*:\s*(\d{7,})',
    r'rbx-user-id["\s:=]+(\d{7,})',
    r'user_id["\s:=]+(\d{7,})',
    r'AccountId["\s:=]+(\d{7,})',
]

def scan_logs():
    found = {}
    if not os.path.exists(LOG_PATH):
        return found

    for log_file in glob.glob(os.path.join(LOG_PATH, "*.log")):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            ids = set()
            for pat in PATTERNS:
                ids.update(re.findall(pat, content, re.IGNORECASE))
            for uid in ids:
                mtime     = os.path.getmtime(log_file)
                last_seen = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                if uid not in found or found[uid]["last_seen"] < last_seen:
                    found[uid] = {"last_seen": last_seen}
        except Exception:
            pass
    return found

# ── Roblox API (batch + fallback) ─────────────────────────────────────────────
def batch_lookup(uid_list):
    """POST /v1/users  — returns {uid_str: {username, display, profile}}"""
    results = {}
    try:
        r = requests.post(
            "https://users.roblox.com/v1/users",
            json={"userIds": [int(u) for u in uid_list], "excludeBannedUsers": False},
            headers=HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            for entry in r.json().get("data", []):
                uid = str(entry["id"])
                results[uid] = {
                    "username":     entry.get("name", "Unknown"),
                    "display_name": entry.get("displayName", ""),
                    "profile":      f"https://www.roblox.com/users/{uid}/profile",
                }
    except Exception:
        pass
    return results

def single_lookup(uid):
    """Fallback: GET /v1/users/{id}"""
    for attempt in range(3):
        try:
            r = requests.get(
                f"https://users.roblox.com/v1/users/{uid}",
                headers=HEADERS, timeout=6,
            )
            if r.status_code == 200:
                d = r.json()
                return {
                    "username":     d.get("name", "Unknown"),
                    "display_name": d.get("displayName", ""),
                    "profile":      f"https://www.roblox.com/users/{uid}/profile",
                }
        except Exception:
            time.sleep(0.5)
    return None

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    banner()

    # Silent scan
    print(C + "  Checking...\n")
    found = scan_logs()

    if not found:
        print(R + B + "  No accounts found on this PC.")
        print()
        print(DIV)
        input(C + "\n  Press Enter to exit...")
        return

    uid_list = list(found.keys())

    # Batch lookup first
    info_map = batch_lookup(uid_list)

    # Single fallback for any that batch missed
    for uid in uid_list:
        if uid not in info_map:
            result = single_lookup(uid)
            if result:
                info_map[uid] = result

    os.system("cls")
    banner()
    print(DIV)
    print(C + B + f"  {len(found)} ACCOUNT(S) FOUND ON THIS PC")
    print(DIV + "\n")

    for i, uid in enumerate(uid_list, 1):
        meta = found[uid]
        info = info_map.get(uid)

        print(C + B + f"  [{i}]  USER ID    ›  {uid}")
        print(W     +  f"       LAST SEEN  ›  {meta['last_seen']}")

        if info:
            uname = info["username"]
            dname = info["display_name"]
            print(C + B + f"       ROBLOX USER ›  {uname}" +
                  (f"  ({dname})" if dname and dname != uname else ""))
            print(C +  f"       PROFILE    ›  {info['profile']}")
        else:
            print(R  + "       ROBLOX USER ›  Could not resolve (banned / deleted?)")
        print()

    print(DIV)
    input(C + "\n  Press Enter to exit...")

if __name__ == "__main__":
    main()