import asyncio
import ctypes
import gzip
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from mitmproxy import certs
from mitmproxy.options import Options
from mitmproxy.tools.dump import DumpMaster

from colorama import Fore, Style, init
init()

# =======================
# PREMIUM THEME COLORS
# =======================

BLUE  = Fore.CYAN
LIGHT = Fore.LIGHTCYAN_EX
WHITE = Fore.WHITE
DIM   = Fore.LIGHTBLACK_EX
RESET = Style.RESET_ALL

# =======================
# CONSTANTS
# =======================

ROBLOX_PROCESS = "RobloxPlayerBeta.exe"
PROXY_TARGET_HOST = "assetdelivery.roblox.com"
STRIPPABLE_ASSET_TYPES = {"Image", "TexturePack"}

# =======================
# PREMIUM UI FUNCTIONS
# =======================

def banner():
    print(LIGHT + """
╔══════════════════════════════════════════════════════╗
║            LIFENZ NO-TEXTURE PROXY UTILITY           ║
║        Premium Light-Blue Performance Edition        ║
╚══════════════════════════════════════════════════════╝
""" + RESET)

def section(title):
    print(LIGHT + f"\n─── {title} ─────────────────────────────\n" + RESET)

def log(category, message):
    print(BLUE + f"[{category}]" + WHITE + f" {message}" + RESET)

# =======================
# TEXTURE STRIPPER
# =======================

class TextureStripper:
    """Mitmproxy addon that strips texture priority data"""

    @staticmethod
    def _decode(content: bytes, encoding: str):
        if encoding == "gzip":
            content = gzip.decompress(content)
        return json.loads(content)

    @staticmethod
    def _encode(data, encoding: str):
        raw = json.dumps(data, separators=(",", ":")).encode()
        return gzip.compress(raw) if encoding == "gzip" else raw

    def request(self, flow):
        parsed = urlparse(flow.request.pretty_url)
        if parsed.hostname != PROXY_TARGET_HOST or not flow.request.raw_content:
            return

        encoding = flow.request.headers.get("Content-Encoding", "").lower()

        try:
            data = self._decode(flow.request.raw_content, encoding)
        except:
            return

        if not isinstance(data, list):
            return

        modified = False

        for entry in data:
            if not isinstance(entry, dict):
                continue
            if entry.get("assetType") not in STRIPPABLE_ASSET_TYPES:
                continue
            if entry.pop("contentRepresentationPriorityList", None) is not None:
                modified = True
                log("Stripper", f"Optimized {entry['assetType']}")

        if modified:
            flow.request.raw_content = self._encode(data, encoding)
            flow.request.headers["Content-Length"] = str(len(flow.request.raw_content))

# =======================
# ROBLOX PROCESS MANAGER
# =======================

class RobloxManager:
    STORAGE_DB = Path.home() / "AppData/Local/Roblox/rbx-storage.db"
    LOCAL_APPDATA = Path.home() / "AppData/Local"

    @classmethod
    def is_running(cls):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {ROBLOX_PROCESS}"],
                capture_output=True, text=True
            )
            return ROBLOX_PROCESS in result.stdout
        except:
            return False

    @classmethod
    def terminate(cls):
        if not cls.is_running():
            log("Roblox", "Process not running")
            return False

        subprocess.run(
            ["taskkill", "/F", "/IM", ROBLOX_PROCESS],
            capture_output=True, text=True
        )
        log("Roblox", "Termination signal sent")
        return True

    @classmethod
    def wait_for_exit(cls, timeout=10):
        log("Roblox", "Waiting for process exit...")
        end = time.time() + timeout
        while time.time() < end:
            if not cls.is_running():
                log("Roblox", "Process exited")
                return True
            time.sleep(0.5)
        log("Roblox", "Exit timeout")
        return False

    @classmethod
    def delete_storage(cls):
        if not cls.STORAGE_DB.exists():
            log("Storage", "Database not found — skipping")
            return False
        try:
            cls.STORAGE_DB.unlink()
            log("Storage", "Storage database deleted")
            return True
        except:
            log("Storage", "Deletion failed")
            return False

    @classmethod
    def find_install_dirs(cls):
        for path in cls.LOCAL_APPDATA.glob("Roblox/version-*"):
            if path.is_dir() and (path / ROBLOX_PROCESS).exists():
                yield path

# =======================
# CERTIFICATE MANAGER
# =======================

class CertificateManager:
    MITMPROXY_DIR = Path.home() / ".mitmproxy"
    CA_CERT_FILE = MITMPROXY_DIR / "mitmproxy-ca-cert.pem"

    @classmethod
    def get_ca_content(cls):
        cls.MITMPROXY_DIR.mkdir(exist_ok=True)
        certs.CertStore.from_store(str(cls.MITMPROXY_DIR), "mitmproxy", 2048)
        if cls.CA_CERT_FILE.exists():
            return cls.CA_CERT_FILE.read_text(encoding="utf-8")
        return None

    @classmethod
    def install_to_roblox(cls):
        ca_content = cls.get_ca_content()
        if not ca_content:
            return False

        for install_dir in RobloxManager.find_install_dirs():
            ssl_dir = install_dir / "ssl"
            ssl_dir.mkdir(exist_ok=True)
            ca_file = ssl_dir / "cacert.pem"

            existing = ca_file.read_text(encoding="utf-8") if ca_file.exists() else ""
            if ca_content not in existing:
                ca_file.write_text(existing + "\n" + ca_content, encoding="utf-8")

        return True

    @classmethod
    async def wait_for_install(cls, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if cls.install_to_roblox():
                return True
            await asyncio.sleep(0.2)
        return False

# =======================
# MAIN PROXY FUNCTION
# =======================

async def run_proxy():
    banner()
    section("SYSTEM CLEANUP")

    RobloxManager.terminate()
    if RobloxManager.wait_for_exit():
        RobloxManager.delete_storage()

    section("STARTING PROXY ENGINE")

    options = Options(mode=[f"local:{ROBLOX_PROCESS}"])
    master = DumpMaster(options, with_termlog=False, with_dumper=False)
    master.addons.add(TextureStripper())

    proxy_task = asyncio.create_task(master.run())

    if not await CertificateManager.wait_for_install():
        log("Certificate", "Installation failed")
        return

    section("PROXY STATUS")

    print(LIGHT + " No-Texture Proxy is ACTIVE" + RESET)
    print(WHITE + f" Intercepting → {ROBLOX_PROCESS}" + RESET)
    print(DIM + "\n Launch Roblox to begin...\n" + RESET)

    print(LIGHT + " Powered by LIFENZ Premium Utility" + RESET)
    print(DIM + " discord.gg/resurrect\n" + RESET)

    await proxy_task

# =======================
# ENTRY POINT
# =======================

def main():
    try:
        asyncio.run(run_proxy())
    except KeyboardInterrupt:
        log("Proxy", "Shutting down...")
    except Exception as e:
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Proxy startup failed:\n{e}\n\nApplication will exit.",
            "LIFENZ Proxy Error",
            0x10,
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
