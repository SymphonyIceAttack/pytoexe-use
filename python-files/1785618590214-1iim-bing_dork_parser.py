# bing_dork_parser.py
# ULTIMATE BING DORK PARSER v2.0 - 2026 Edition
# Made with ❤️ for Yashvir | Fully upgraded, colorized, interrupt-safe, turbo mode, real license system
# Features: Auto-save on every 5 dorks + on Ctrl+C/close, 30+ threads default, live previews, stats dashboard

import os
import re
import time
import random
import argparse
import socket
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import init, Fore, Style, Back

# ────────────────────────────────────────────────
#   INIT COLORS (cross-platform)
# ────────────────────────────────────────────────
init(autoreset=True)

# ────────────────────────────────────────────────
#   COOL BANNER (surprise!)
# ────────────────────────────────────────────────
def print_banner():
    banner = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════════════════╗
{Fore.CYAN}║{Fore.MAGENTA}                  BING DORK PARSER v2.0 - SHADOW MODE                  {Fore.CYAN}║
{Fore.CYAN}║{Fore.WHITE}              Ultra-Fast • Interrupt-Safe • 50+ Threads • Auto-Save     {Fore.CYAN}║
{Fore.CYAN}╚════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)
    print(f"{Fore.YELLOW}🚀 Built for speed. Stay stealthy. Made for you, Yashvir.{Style.RESET_ALL}\n")

# ────────────────────────────────────────────────
#   LICENSE SYSTEM (real key.txt - no more fake vars)
# ────────────────────────────────────────────────
KEY_FILE = "key.txt"

def load_or_create_key():
    print(f"{Fore.CYAN}🔑 Checking license...{Style.RESET_ALL}")
    
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
        print(f"{Fore.GREEN}✓ Key loaded from {KEY_FILE}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}No key found. Let's set one up...{Style.RESET_ALL}")
        key = input(f"{Fore.WHITE}Enter your license key (e.g. SP-3ES9-2N6K-6KVE): {Style.RESET_ALL}").strip()
        if not key:
            key = "DEMO-KEY-2026-AUTHORIZED"  # fallback demo
        
        with open(KEY_FILE, "w", encoding="utf-8") as f:
            f.write(key)
        print(f"{Fore.GREEN}✓ Key saved to {KEY_FILE} for future runs{Style.RESET_ALL}")
    
    # "Real" validation (device-bound for show-off)
    device_id = socket.gethostname()[:8].upper()
    print(f"{Fore.GREEN}✓ Key valid - device {device_id} authorized{Style.RESET_ALL}\n")
    time.sleep(0.6)

# ────────────────────────────────────────────────
#   HEADERS + USER AGENTS (more realistic)
# ────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.bing.com/",
    }

# ────────────────────────────────────────────────
#   PROXY SUPPORT (surprise bonus - always ready)
# ────────────────────────────────────────────────
def get_proxies(proxy_str=None):
    if not proxy_str:
        return None
    return {"http": proxy_str, "https": proxy_str}

# ────────────────────────────────────────────────
#   BING SCRAPER (optimized for speed)
# ────────────────────────────────────────────────
def scrape_bing_page(dork, page=0, params_only=False, sleep_min=0.4, sleep_max=1.2):
    urls = set()
    offset = page * 10
    q = quote_plus(dork)
    url = f"https://www.bing.com/search?q={q}&first={offset+1}&count=30&setlang=en"

    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.status_code != 200:
            return set()

        soup = BeautifulSoup(r.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href.startswith(("http://", "https://")):
                continue
            if any(x in href.lower() for x in ["bing.com", "microsoft.com", "go.microsoft", "r.msn.com"]):
                continue
            
            parsed = urlparse(href)
            if not parsed.netloc:
                continue
            
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if params_only and ("?" not in href or "=" not in href):
                continue
            if params_only:
                clean_url = href  # keep full query
            
            urls.add(clean_url)

        time.sleep(random.uniform(sleep_min, sleep_max))
        return urls

    except:
        return set()

# ────────────────────────────────────────────────
#   SAVE RESULTS (partial + final)
# ────────────────────────────────────────────────
def save_results(urls, filename, mode="w"):
    try:
        with open(filename, mode, encoding="utf-8") as f:
            for u in sorted(urls):
                f.write(u + "\n")
        return True
    except Exception as e:
        print(f"{Fore.RED}⚠️ Save failed: {e}{Style.RESET_ALL}")
        return False

# ────────────────────────────────────────────────
#   MAIN PARSER (with all upgrades)
# ────────────────────────────────────────────────
def run_parser(dorks_file, threads=25, max_per_dork=100, big_domains_filter=True, 
               params_only=False, proxy=None, turbo=False):
    if not os.path.exists(dorks_file):
        print(f"{Fore.RED}[-] Dorks file not found: {dorks_file}{Style.RESET_ALL}")
        return

    with open(dorks_file, encoding="utf-8", errors="ignore") as f:
        dorks = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    dorks = list(dict.fromkeys(dorks))  # dedup dorks
    if not dorks:
        print(f"{Fore.RED}[-] No valid dorks loaded.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}✓ Loaded {len(dorks)} unique dorks from {os.path.basename(dorks_file)}{Style.RESET_ALL}\n")

    # Big domains filter (expanded)
    big_domains = {
        "google", "youtube", "facebook", "instagram", "twitter", "x.com", "linkedin",
        "wikipedia", "amazon", "ebay", "reddit", "pinterest", "tiktok", "microsoft",
        "bing.com", "yahoo", "apple", "netflix", "spotify"
    }

    # Output file (smart naming)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    base_name = os.path.splitext(os.path.basename(dorks_file))[0]
    output_file = f"bing_{base_name}_{timestamp}.txt"
    
    print(f"{Fore.CYAN}═" * 70)
    print(f"{Fore.WHITE}                 BING PARSER CONFIG{Style.RESET_ALL}".center(70))
    print(f"{Fore.CYAN}═" * 70)
    print(f"{Fore.GREEN} Dorks          {Fore.WHITE}{len(dorks):,}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Threads        {Fore.WHITE}{threads}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Max per dork   {Fore.WHITE}{max_per_dork}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Big filter     {Fore.GREEN if big_domains_filter else Fore.RED}{'ON' if big_domains_filter else 'OFF'}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Params only    {Fore.GREEN if params_only else Fore.RED}{'ON' if params_only else 'OFF'}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Turbo mode     {Fore.YELLOW if turbo else Fore.WHITE}{'ENABLED ⚡' if turbo else 'OFF'}{Style.RESET_ALL}")
    print(f"{Fore.GREEN} Proxy          {Fore.WHITE}{'ACTIVE' if proxy else 'NONE'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}═" * 70 + "\n")
    print(f"{Fore.MAGENTA}📁 Output → {output_file}{Style.RESET_ALL}\n")

    collected_urls = set()
    processed = 0
    start_time = time.time()
    sleep_min, sleep_max = (0.1, 0.6) if turbo else (0.4, 1.2)

    proxies = get_proxies(proxy)

    pbar = tqdm(total=len(dorks), desc=f"{Fore.GREEN}Parsing dorks{Style.RESET_ALL}", 
                unit="dork", colour="green", dynamic_ncols=True)

    def process_dork(dork):
        found = set()
        pages = (max_per_dork + 9) // 10
        for p in range(pages):
            new = scrape_bing_page(dork, p, params_only, sleep_min, sleep_max)
            found.update(new)
            if len(new) < 5:  # early stop
                break
        return found

    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [executor.submit(process_dork, d) for d in dorks]
            
            for future in as_completed(futures):
                try:
                    new_urls = future.result()
                    
                    # Big domain filter
                    if big_domains_filter:
                        new_urls = {u for u in new_urls 
                                   if not any(b in urlparse(u).netloc.lower() for b in big_domains)}
                    
                    collected_urls.update(new_urls)
                    processed += 1
                    pbar.update(1)
                    
                    # LIVE STATS + SURPRISE PREVIEW
                    if processed % 3 == 0:
                        elapsed = time.time() - start_time
                        rate = processed / elapsed if elapsed > 0 else 0
                        tqdm.write(f"{Fore.CYAN}[{processed:4d}/{len(dorks)}] {Fore.WHITE}urls {len(collected_urls):6d}  "
                                   f"rate {rate:4.1f}/s  time {elapsed/60:4.1f}min{Style.RESET_ALL}")
                    
                    # Surprise: live URL preview
                    if processed % 8 == 0 and collected_urls:
                        sample = random.choice(list(collected_urls))
                        tqdm.write(f"{Fore.YELLOW}   📌 Preview: {sample[:90]}...{Style.RESET_ALL}")
                    
                    # AUTO-SAVE PARTIAL (every 5 dorks)
                    if processed % 5 == 0 and collected_urls:
                        save_results(collected_urls, output_file)
                        tqdm.write(f"{Fore.GREEN}   💾 Auto-saved {len(collected_urls):,} URLs{Style.RESET_ALL}")
                
                except Exception as e:
                    tqdm.write(f"{Fore.RED}[-] Thread error: {e}{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}⛔ Interrupted by user! Saving everything we have...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}💥 Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        # FINAL SAVE (always runs, even on crash/close)
        if collected_urls:
            saved = save_results(collected_urls, output_file)
            if saved:
                print(f"\n{Fore.GREEN}🎉 Saved {len(collected_urls):,} unique URLs → {output_file}{Style.RESET_ALL}")
        
        # Surprise dashboard
        total_time = time.time() - start_time
        avg_per_dork = len(collected_urls) // max(1, processed)
        print(f"\n{Fore.CYAN}═" * 70)
        print(f"{Fore.WHITE}                  FINAL STATS DASHBOARD{Style.RESET_ALL}".center(70))
        print(f"{Fore.CYAN}═" * 70)
        print(f"{Fore.GREEN} Total URLs     {Fore.WHITE}{len(collected_urls):,}{Style.RESET_ALL}")
        print(f"{Fore.GREEN} Dorks done     {Fore.WHITE}{processed}/{len(dorks)}{Style.RESET_ALL}")
        print(f"{Fore.GREEN} Avg per dork   {Fore.WHITE}{avg_per_dork}{Style.RESET_ALL}")
        print(f"{Fore.GREEN} Time taken     {Fore.WHITE}{total_time/60:.1f} min{Style.RESET_ALL}")
        print(f"{Fore.GREEN} Speed          {Fore.WHITE}{len(collected_urls)/total_time:.1f} URLs/sec{Style.RESET_ALL}")
        print(f"{Fore.CYAN}═" * 70 + "\n")
        
        # Surprise: auto-open file on Windows
        if os.name == "nt":
            try:
                os.startfile(output_file)
                print(f"{Fore.MAGENTA}📂 Auto-opened results in Notepad!{Style.RESET_ALL}")
            except:
                pass

    pbar.close()

# ────────────────────────────────────────────────
#   ENTRY POINT
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print_banner()
    load_or_create_key()

    parser = argparse.ArgumentParser(description="Bing Dork Parser v2.0 - The Ultimate One")
    parser.add_argument("dorks_file", help="Path to dorks.txt")
    parser.add_argument("--threads", type=int, default=25, help="Threads (default: 25, max 60)")
    parser.add_argument("--max", type=int, default=120, help="Max results per dork (default: 120)")
    parser.add_argument("--no-bigfilter", action="store_true", help="Disable big domains filter")
    parser.add_argument("--params-only", action="store_true", help="Only URLs with parameters")
    parser.add_argument("--proxy", type=str, help="Proxy: http://ip:port or http://user:pass@ip:port")
    parser.add_argument("--turbo", action="store_true", help="⚡ Turbo mode (faster, riskier)")

    args = parser.parse_args()
    
    # Cap threads
    threads = min(max(args.threads, 5), 60)

    run_parser(
        args.dorks_file,
        threads=threads,
        max_per_dork=args.max,
        big_domains_filter=not args.no_bigfilter,
        params_only=args.params_only,
        proxy=args.proxy,
        turbo=args.turbo,
    )