import os
import sys
import time
import random
import subprocess
import urllib.request
import zipfile
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from datetime import datetime
import requests
import ssl
import certifi

class DependencyManager:
    """مدیریت و دانلود خودکار پیش‌نیازها"""
    
    def __init__(self):
        self.base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.driver_path = os.path.join(self.base_path, "chromedriver.exe")
        self.chrome_paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe")
        ]
        
    def check_chrome_installed(self):
        """بررسی نصب بودن کروم"""
        print("🔍 بررسی نصب Chrome...")
        for path in self.chrome_paths:
            if os.path.exists(path):
                print("✅ Chrome نصب است")
                return True
        return False
    
    def download_chrome(self):
        """دانلود کروم اگه نصب نباشه"""
        print("📥 Chrome یافت نشد! در حال دانلود...")
        try:
            chrome_url = "https://dl.google.com/chrome/install/latest/chrome_installer.exe"
            installer_path = os.path.join(self.base_path, "chrome_installer.exe")
            
            # دانلود با نمایش پیشرفت
            urllib.request.urlretrieve(chrome_url, installer_path, self.download_progress)
            
            print("\n💿 در حال نصب Chrome...")
            subprocess.run([installer_path, "/silent", "/install"], check=True)
            
            # پاک کردن فایل نصب
            os.remove(installer_path)
            print("✅ Chrome با موفقیت نصب شد")
            return True
        except Exception as e:
            print(f"❌ خطا در نصب Chrome: {e}")
            return False
    
    def download_progress(self, block_num, block_size, total_size):
        """نمایش پیشرفت دانلود"""
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(int(downloaded * 100 / total_size), 100)
            bar = '█' * (percent // 2) + '░' * (50 - (percent // 2))
            print(f"\r   پیشرفت: |{bar}| {percent}%", end='')
    
    def get_chrome_version(self):
        """دریافت نسخه کروم نصب شده"""
        try:
            # اجرای chrome --version
            result = subprocess.run(
                ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'version' in line.lower():
                        version = line.strip().split()[-1]
                        return version.split('.')[0]  # فقط عدد اصلی
        except:
            pass
        return "120"  # نسخه پیش‌فرض
    
    def download_chromedriver(self):
        """دانلود خودکار کروم درایور متناسب با نسخه کروم"""
        print("\n🔍 بررسی ChromeDriver...")
        
        if os.path.exists(self.driver_path):
            print("✅ ChromeDriver قبلاً دانلود شده")
            return True
        
        try:
            # دریافت نسخه کروم
            chrome_version = self.get_chrome_version()
            print(f"📌 نسخه Chrome: {chrome_version}")
            
            # دریافت لینک آخرین نسخه
            driver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}.0.0.0/win32/chromedriver-win32.zip"
            
            # دانلود کروم درایور
            print("📥 در حال دانلود ChromeDriver...")
            zip_path = os.path.join(self.base_path, "chromedriver.zip")
            urllib.request.urlretrieve(driver_url, zip_path, self.download_progress)
            
            # استخراج فایل
            print("\n📦 در حال استخراج...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.base_path)
            
            # پیدا کردن فایل chromedriver.exe
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file == "chromedriver.exe":
                        shutil.move(os.path.join(root, file), self.driver_path)
                        break
            
            # پاک کردن فایل‌های موقت
            os.remove(zip_path)
            shutil.rmtree(os.path.join(self.base_path, "chromedriver-win32"), ignore_errors=True)
            
            print("\n✅ ChromeDriver با موفقیت نصب شد")
            return True
            
        except Exception as e:
            print(f"\n❌ خطا در دانلود ChromeDriver: {e}")
            return False
    
    def check_and_install_all(self):
        """بررسی و نصب همه پیش‌نیازها"""
        print("="*60)
        print("🛠️  بررسی پیش‌نیازهای سیستم")
        print("="*60)
        
        # بررسی Chrome
        if not self.check_chrome_installed():
            if not self.download_chrome():
                print("❌ نصب Chrome ناموفق بود")
                return False
        
        # بررسی ChromeDriver
        if not os.path.exists(self.driver_path):
            if not self.download_chromedriver():
                print("❌ نصب ChromeDriver ناموفق بود")
                return False
        
        # نصب کتابخانه‌های پایتون (اگه تو محیط exe باشه نیازی نیست)
        if not getattr(sys, 'frozen', False):
            self.install_python_packages()
        
        print("="*60)
        print("✅ همه پیش‌نیازها آماده هستند")
        print("="*60)
        return True
    
    def install_python_packages(self):
        """نصب پکیج‌های پایتون"""
        packages = ['selenium', 'requests', 'certifi']
        for package in packages:
            try:
                __import__(package)
            except ImportError:
                print(f"📦 نصب {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])

class AparatLiveViewBot:
    def __init__(self):
        """مقداردهی اولیه بات"""
        self.dep_manager = DependencyManager()
        self.proxy_list = [
            "45.87.137.55:5432",
            "185.217.137.117:5432",
            "195.154.233.102:5555",
            "94.23.52.254:4545",
            "163.172.107.216:5555",
            "51.158.108.171:8811",
            "78.47.15.184:3128",
            "138.201.21.231:5566",
        ]
        
        self.working_proxies = []
        self.current_proxy_index = 0
        self.live_url = ""
        self.target_views = 0
        self.active_views = 0
        self.drivers = []
        self.is_running = True
        self.views_created = 0
        
    def get_resource_path(self, relative_path):
        """دریافت مسیر فایل در حالت exe"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def get_user_input(self):
        """گرفتن ورودی از کاربر"""
        print("\n" + "="*60)
        print("🚀 بات افزایش ویو لایو آپارات")
        print("="*60)
        
        # گرفتن لینک لایو
        while True:
            self.live_url = input("📺 لینک پخش زنده آپارات: ").strip()
            if "aparat.com" in self.live_url:
                break
            else:
                print("❌ لینک نامعتبر!")
        
        # گرفتن تعداد ویو
        while True:
            try:
                self.target_views = int(input("🎯 تعداد ویو مورد نظر: ").strip())
                if self.target_views > 0:
                    break
            except:
                print("❌ لطفاً یک عدد وارد کنید")
    
    def create_driver(self, view_id):
        """ایجاد درایور با بررسی مسیرها"""
        chrome_options = Options()
        
        # تنظیمات پایه
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--window-size=800x600")
        chrome_options.add_argument("--disable-gpu")
        
        # تنظیمات VPS
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # User Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # مسیر کروم درایور
        chromedriver_path = self.dep_manager.driver_path
        
        try:
            if os.path.exists(chromedriver_path):
                driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver, None
            
        except Exception as e:
            print(f"❌ خطا در ایجاد درایور: {e}")
            return None, None
    
    def quick_join_live(self, driver, view_id):
        """اتصال سریع به لایو"""
        try:
            driver.get(self.live_url)
            time.sleep(2)
            
            driver.execute_script("""
                var video = document.querySelector('video');
                if(video) {
                    video.muted = true;
                    video.play();
                }
            """)
            
            time.sleep(1)
            print(f"✅ ویو {view_id}: متصل شد")
            return True
            
        except Exception as e:
            print(f"❌ ویو {view_id}: خطا - {str(e)[:30]}")
            return False
    
    def keep_view_alive(self, driver, view_id):
        """نگه داشتن ویو در لایو"""
        fail_count = 0
        
        while self.is_running:
            try:
                time.sleep(15)
                
                try:
                    is_playing = driver.execute_script("""
                        var video = document.querySelector('video');
                        return video ? !video.paused : false;
                    """)
                    
                    if not is_playing:
                        driver.execute_script("document.querySelector('video')?.play()")
                        fail_count = 0
                    
                except:
                    fail_count += 1
                    if fail_count > 5:
                        break
                        
            except:
                break
        
        self.active_views -= 1
        try:
            driver.quit()
        except:
            pass
    
    def create_view(self, view_id):
        """ایجاد ویو جدید"""
        if view_id > self.target_views or not self.is_running:
            return
        
        driver, _ = self.create_driver(view_id)
        if driver and self.quick_join_live(driver, view_id):
            self.active_views += 1
            self.views_created += 1
            self.keep_view_alive(driver, view_id)
    
    def start_bot(self):
        """شروع بات"""
        # اول پیش‌نیازها رو چک کن
        if not self.dep_manager.check_and_install_all():
            print("❌ مشکل در نصب پیش‌نیازها")
            input("برای خروج Enter بزنید...")
            return
        
        # گرفتن ورودی
        self.get_user_input()
        
        print(f"\n🚀 شروع ایجاد {self.target_views} ویو...")
        
        # ایجاد ویوها
        threads = []
        for i in range(self.target_views):
            if not self.is_running:
                break
            
            thread = threading.Thread(target=self.create_view, args=(i+1,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            print(f"   ویو {i+1} در حال ایجاد...", end="\r")
            time.sleep(0.5)
        
        print(f"\n✅ همه ویوها ایجاد شدند!")
        print(f"👥 ویوهای فعال: {self.active_views}")
        print("\n" + "="*60)
        print("🟢 بات فعال است - Ctrl+C برای توقف")
        print("="*60)
        
        try:
            while self.active_views > 0:
                time.sleep(2)
                print(f"📊 ویوهای فعال: {self.active_views}", end="\r")
        except KeyboardInterrupt:
            self.stop_bot()
    
    def stop_bot(self):
        """توقف بات"""
        print("\n\n🛑 توقف بات...")
        self.is_running = False
        for driver in self.drivers[:]:
            try:
                driver.quit()
            except:
                pass
        print("✅ بات متوقف شد")

# ================== بسته‌بندی برای EXE ==================
def create_spec_file():
    """ساخت فایل spec برای pyinstaller"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['bot.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AparatLiveBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
"""
    with open("bot.spec", "w", encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ فایل bot.spec ساخته شد")

# ================== اجرای اصلی ==================
if __name__ == "__main__":
    # پاک کردن صفحه
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # بنر خوش‌آمدگویی
    print(r"""
    ╔═══════════════════════════════════════════════╗
    ║     🚀 بات افزایش ویو لایو آپارات             ║
    ║     مجهز به دانلود خودکار پیش‌نیازها          ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    # اجرای بات
    bot = AparatLiveViewBot()
    try:
        bot.start_bot()
    except KeyboardInterrupt:
        bot.stop_bot()
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        input("برای خروج Enter بزنید...")