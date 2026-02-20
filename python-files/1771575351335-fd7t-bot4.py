import time, threading, re, os, json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import deque

# محاولة استيراد المكتبات الثقيلة مع معالجة الخطأ
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.firefox.options import Options
    from telethon import TelegramClient, events
    import numpy as np
    HAS_LIBRARIES = True
except ImportError:
    HAS_LIBRARIES = False

# ================= CONFIG =================
API_ID = 23266065
API_HASH = '69a3ab80862efbf72f96b7366bf7ba90'
TARGET_CHANNELS = ['Mk07mm', 'FutureSignalsPocket', 'JokerTrading']
KNOWLEDGE_FILE = "ai_persistent_brain.json"

class StableAI_V27:
    def __init__(self, root):
        self.root = root
        self.root.title("AI HYBRID SNIPER V27 - STABLE MODE")
        self.root.geometry("500x850")
        self.root.configure(bg="#0a0a0a")
        
        # التأكد من ثبات النافذة (مثل برنامجك البسيط)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        # البيانات
        self.prices = deque(maxlen=4000)
        self.candles_history = []
        self.brain_data = self.load_brain()
        self.wins, self.losses = 0, 0
        self.driver = None

        self.setup_ui()
        
        # فحص المكتبات قبل البدء
        if not HAS_LIBRARIES:
            self.add_log("❌ خطأ: المكتبات البرمجية ناقصة (selenium, numpy, telethon).")
            messagebox.showerror("خطأ", "برجاء تثبيت المكتبات المطلوبة عبر CMD")
        else:
            # تشغيل المحركات في خيوط منفصلة لضمان عدم تجمد الواجهة
            threading.Thread(target=self.safe_init_browser, daemon=True).start()
            threading.Thread(target=self.start_telegram_safe, daemon=True).start()
            threading.Thread(target=self.early_warning_worker, daemon=True).start()
            threading.Thread(target=self.price_engine_safe, daemon=True).start()

    def setup_ui(self):
        # العنوان (تصميم عصري)
        header = tk.Frame(self.root, bg="#111")
        header.pack(fill="x")
        tk.Label(header, text="CORE AI HYBRID V27", fg="#00FFCC", bg="#111", font=("Arial", 12, "bold")).pack(pady=10)

        # عرض السعر الكبير
        self.price_lbl = tk.Label(self.root, text="0.00000", fg="#FFFF00", bg="#0a0a0a", font=("Consolas", 50, "bold"))
        self.price_lbl.pack(pady=20)

        # منطقة الإشارات
        self.signal_lbl = tk.Label(self.root, text="INITIALIZING...", fg="#FFA500", bg="#000", font=("Arial", 14, "bold"), height=3)
        self.signal_lbl.pack(fill="x", padx=30, pady=5)

        # لوحة اللوج (Log) مثل البرنامج المستقر
        self.log_box = tk.Text(self.root, bg="#000", fg="#00FF66", font=("Consolas", 9), height=15, bd=0)
        self.log_box.pack(fill="both", expand=True, padx=15, pady=10)

        # الإحصائيات
        self.stats_lbl = tk.Label(self.root, text="W:0 | L:0 | BRAIN: 0", fg="#aaa", bg="#0a0a0a")
        self.stats_lbl.pack(fill="x", pady=10)

    def add_log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{now}] {msg}\n")
        self.log_box.see(tk.END)

    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r') as f: return json.load(f)
            except: pass
        return {"patterns": {}, "total_trades": 0}

    # --- المحركات الآمنة (Safe Engines) لعدم الإغلاق المفاجئ ---
    
    def safe_init_browser(self):
        self.add_log("🌐 محاولة فتح المتصفح...")
        try:
            opts = Options()
            # يمكنك تفعيل الـ headless لو مش عايز المتصفح يظهر
            # opts.add_argument("--headless") 
            self.driver = webdriver.Firefox(options=opts)
            self.driver.get("https://pocketoption.com/en/trade")
            self.add_log("✅ المتصفح جاهز.")
            self.signal_lbl.config(text="SCANNING MARKET...", fg="#00FFCC")
        except Exception as e:
            self.add_log(f"❌ فشل فتح المتصفح: {str(e)[:50]}...")
            self.add_log("💡 تأكد من وجود Firefox و Geckodriver.")

    def start_telegram_safe(self):
        self.add_log("📱 محاولة ربط تليجرام...")
        try:
            client = TelegramClient("stable_v27", API_ID, API_HASH)
            self.add_log("✅ تليجرام متصل.")
            # هنا يوضع الـ handler الخاص بك
            client.start()
        except Exception as e:
            self.add_log(f"❌ فشل ربط تليجرام: {str(e)[:50]}")

    def price_engine_safe(self):
        while True:
            if self.driver:
                try:
                    p_text = self.driver.find_element(By.CSS_SELECTOR, ".current-price").text
                    price = float(p_text.replace(",", ""))
                    self.prices.append(price)
                    self.price_lbl.config(text=f"{price:.5f}")
                    
                    # منطق الشموع هنا (نفس الكود السابق)
                    now = datetime.now()
                    if not hasattr(self, 'cur_c') or now.second == 0:
                        if hasattr(self, 'cur_c'):
                            self.candles_history.append(self.cur_c['c'] - self.cur_c['o'])
                        self.cur_c = {'o': price, 'c': price}
                    else:
                        self.cur_c['c'] = price
                except:
                    pass
            time.sleep(0.5)

    def early_warning_worker(self):
        while True:
            now = datetime.now()
            # نظام الـ 90 ثانية (تنبيه في الدقيقة 2 و 30 ثانية)
            if now.second == 30 and (now.minute % 6 == 2):
                if len(self.candles_history) >= 2:
                    self.add_log("🔔 تنبيه مبكر: نمط محتمل يتشكل...")
                    self.signal_lbl.config(text="⚠️ PREPARE TRADE (90s)", fg="#FFA500")
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = StableAI_V27(root)
    root.mainloop()