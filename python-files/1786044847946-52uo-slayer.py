#!/usr/bin/env python3
"""
VulnLeecher v1.0 - أداة لجمع الروابط والبريد الإلكتروني والملفات الحساسة (مشابهة لـ SlayerLeecher ولكن محدثة)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import urllib.parse
import re
import random
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠️ يرجى تثبيت المكتبات: pip install requests beautifulsoup4 urllib3")
    exit(1)

# إعدادات الواجهة
BG = "#0d1117"
FG = "#c9d1d9"
ACCENT = "#58a6ff"
SUCCESS = "#3fb950"
DANGER = "#f85149"
TURBO = "#ff6b35"
SECONDARY = "#161b22"

class VulnLeecher:
    def __init__(self, root):
        self.root = root
        self.root.title("VulnLeecher v1.0 - مستخرج الروابط والبريد")
        self.root.geometry("1000x800")
        self.root.configure(bg=BG)

        # متغيرات التحكم
        self.dorks_path = tk.StringVar()
        self.workers = tk.IntVar(value=100)
        self.pages = tk.IntVar(value=10)
        self.timeout = tk.IntVar(value=15)

        # خيارات التصفية (ميزات الـ Leecher)
        self.ext_filter = tk.StringVar(value="php,asp,aspx,jsp,do,action")  # امتدادات مستهدفة
        self.extract_emails = tk.BooleanVar(value=True)   # استخراج الإيميلات
        self.extract_sensitive = tk.BooleanVar(value=True) # استخراج ملفات حساسة (.env, .sql, .log)

        self.running = False
        self.results = set()
        self.emails_found = set()
        self.dorks = []
        self.output_dir = "leecher_outputs"

        # إنشاء مجلد المخرجات
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # جلسة Requests
        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(pool_connections=200, pool_maxsize=200, max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })

        self.build_ui()
        self.log("⚡ VulnLeecher جاهز - استخراج الروابط والإيميلات والملفات الحساسة", "turbo")

    def clean_url(self, url: str) -> str:
        if not url: return ""
        url = re.sub(r'[\s\n\r\t]+', '', url)
        url = re.sub(r'\.{3,}$', '', url)
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def build_ui(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # العنوان
        tk.Label(main, text="⚡ VulnLeecher v1.0", font=("Segoe UI", 22, "bold"), bg=BG, fg=TURBO).pack(anchor="w")
        tk.Label(main, text="مستخرج الروابط والإيميلات والملفات الحساسة (SQL, ENV, LOG)", font=("Segoe UI", 10), bg=BG, fg=FG).pack(anchor="w", pady=(0,10))

        # ملف الدوركس
        df = tk.Frame(main, bg=BG)
        df.pack(fill=tk.X, pady=5)
        tk.Entry(df, textvariable=self.dorks_path, bg=SECONDARY, fg=FG, relief=tk.FLAT, bd=6).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        tk.Button(df, text="📂 Browse Dorks", command=self.browse_dorks, bg=ACCENT, fg="white", relief=tk.FLAT, padx=10, cursor="hand2").pack(side=tk.RIGHT)

        # الإعدادات الأساسية
        sf = tk.Frame(main, bg=BG)
        sf.pack(fill=tk.X, pady=5)
        for label, var, from_v, to_v in [("Workers:", self.workers, 1, 500), ("Pages:", self.pages, 1, 50), ("Timeout:", self.timeout, 5, 60)]:
            f = tk.Frame(sf, bg=BG)
            f.pack(side=tk.LEFT, padx=10)
            tk.Label(f, text=label, bg=BG, fg=FG).pack(side=tk.LEFT)
            tk.Spinbox(f, from_=from_v, to=to_v, textvariable=var, width=6, bg=SECONDARY, fg=FG, buttonbackground=SECONDARY).pack(side=tk.LEFT, padx=3)

        # خيارات الـ Leecher (التصفية)
        lf = tk.LabelFrame(main, text="🔎 خيارات التصفية (Filtering)", bg=BG, fg=ACCENT, font=("Segoe UI", 10, "bold"), padx=10, pady=5)
        lf.pack(fill=tk.X, pady=10)

        tk.Label(lf, text="الامتدادات المستهدفة (مثال: php,asp,aspx,jsp):", bg=BG, fg=FG).pack(anchor="w")
        tk.Entry(lf, textvariable=self.ext_filter, bg=SECONDARY, fg=FG, relief=tk.FLAT, bd=6).pack(fill=tk.X, pady=2)

        cf = tk.Frame(lf, bg=BG)
        cf.pack(anchor="w", pady=5)
        tk.Checkbutton(cf, text="📧 استخراج الإيميلات", variable=self.extract_emails, bg=BG, fg=FG, selectcolor=SECONDARY).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(cf, text="📁 استخراج ملفات حساسة (.env, .sql, .log)", variable=self.extract_sensitive, bg=BG, fg=FG, selectcolor=SECONDARY).pack(side=tk.LEFT, padx=10)

        # زر TURBO
        tef = tk.Frame(main, bg=BG)
        tef.pack(fill=tk.X, pady=5)
        tk.Button(tef, text="🔥 TURBO (500 Worker / 30 Page)", command=self.activate_turbo, bg=TURBO, fg="white", relief=tk.FLAT, padx=15, cursor="hand2").pack(side=tk.LEFT)

        # أزرار التحكم
        bf = tk.Frame(main, bg=BG)
        bf.pack(fill=tk.X, pady=10)
        self.run_btn = tk.Button(bf, text="▶ START LEECH", command=self.start_scan, bg=SUCCESS, fg="white", font=("Segoe UI", 12, "bold"), relief=tk.FLAT, padx=20, cursor="hand2")
        self.run_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(bf, text="⏹ STOP", command=self.stop_scan, bg=DANGER, fg="white", font=("Segoe UI", 12, "bold"), relief=tk.FLAT, padx=20, cursor="hand2", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="🗑️ Clear", command=self.clear_log, bg="#6e7681", fg="white", relief=tk.FLAT, padx=10, cursor="hand2").pack(side=tk.RIGHT)

        # شريط التقدم والإحصائيات
        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill=tk.X, pady=5)
        self.stats_var = tk.StringVar(value="Ready | URLs: 0 | Emails: 0 | Files: 0")
        tk.Label(main, textvariable=self.stats_var, bg=SECONDARY, fg=FG, anchor="w", padx=5).pack(fill=tk.X, pady=5)

        # مربع السجلات
        self.log_text = scrolledtext.ScrolledText(main, wrap=tk.WORD, font=("Consolas", 9), bg=SECONDARY, fg=FG, relief=tk.FLAT, bd=6, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def browse_dorks(self):
        path = filedialog.askopenfilename(title="Select Dorks File", filetypes=[("Text files", "*.txt")])
        if path: self.dorks_path.set(path)

    def activate_turbo(self):
        self.workers.set(500)
        self.pages.set(30)
        self.timeout.set(8)
        self.log("🔥 TURBO ACTIVATED! (Workers=500, Pages=30)", "turbo")

    def log(self, msg, tag="info"):
        self.log_text.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.tag_config("info", foreground=FG)
        self.log_text.tag_config("success", foreground=SUCCESS)
        self.log_text.tag_config("error", foreground=DANGER)
        self.log_text.tag_config("turbo", foreground=TURBO)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_stats(self):
        self.stats_var.set(f"Ready | URLs: {len(self.results)} | Emails: {len(self.emails_found)} | Files: 0")

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.results.clear()
        self.emails_found.clear()
        self.update_stats()

    def start_scan(self):
        if not self.dorks_path.get() or not os.path.exists(self.dorks_path.get()):
            messagebox.showerror("Error", "حدد ملف الدوركس أولاً!"); return

        with open(self.dorks_path.get(), "r", encoding="utf-8", errors="ignore") as f:
            self.dorks = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        if not self.dorks: messagebox.showerror("Error", "لا توجد دوركس!"); return

        self.running = True
        self.results.clear()
        self.emails_found.clear()
        self.run_btn.config(state=tk.DISABLED, text="⏳ SCANNING...")
        self.stop_btn.config(state=tk.NORMAL)

        pages = self.pages.get()
        total = len(self.dorks) * pages
        self.progress["maximum"] = total
        self.progress["value"] = 0

        # أسماء الملفات
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.url_file = os.path.join(self.output_dir, f"urls_{timestamp}.txt")
        self.email_file = os.path.join(self.output_dir, f"emails_{timestamp}.txt")
        self.sensitive_file = os.path.join(self.output_dir, f"sensitive_{timestamp}.txt")

        with open(self.url_file, "w") as f: f.write("")
        with open(self.email_file, "w") as f: f.write("")
        with open(self.sensitive_file, "w") as f: f.write("")

        self.log(f"🚀 بدء المسح... حفظ في: {self.output_dir}", "success")
        thread = threading.Thread(target=self.scan_thread, args=(pages, total), daemon=True)
        thread.start()

    def stop_scan(self):
        self.running = False
        self.log("⏹ تم الإيقاف بواسطتك", "error")

    def scan_thread(self, pages, total):
        completed = 0
        tasks = []
        for d in self.dorks:
            for p in range(1, pages + 1):
                tasks.append((d, p))

        workers_count = min(self.workers.get(), len(tasks))
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            future_to_task = {executor.submit(self.worker_task, t): t for t in tasks}
            for future in as_completed(future_to_task):
                if not self.running: break
                try:
                    data = future.result()
                    if data:
                        urls, emails, sensitive = data
                        for u in urls:
                            if u not in self.results:
                                self.results.add(u)
                                with open(self.url_file, "a") as f: f.write(u + "\n")
                        for e in emails:
                            if e not in self.emails_found:
                                self.emails_found.add(e)
                                with open(self.email_file, "a") as f: f.write(e + "\n")
                        for s in sensitive:
                            with open(self.sensitive_file, "a") as f: f.write(s + "\n")
                except Exception as e:
                    pass

                completed += 1
                if completed % 10 == 0:
                    self.root.after(0, lambda c=completed: self.progress.config(value=c))
                    self.root.after(0, self.update_stats)

        self.root.after(0, self.scan_finished)

    def worker_task(self, task):
        dork, page = task
        if not self.running: return ([], [], [])
        return self.search_engines(dork, page)

    def search_engines(self, dork, page):
        """البحث في جوجل فقط (للسرعة) واستخراج كل شيء"""
        urls = []
        emails = []
        sensitive = []

        try:
            start = (page - 1) * 10
            url = f"https://www.google.com/search?q={urllib.parse.quote(dork)}&start={start}"
            resp = self.session.get(url, timeout=self.timeout.get())
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 1. استخراج الروابط
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/url?q='):
                    href = href.split('/url?q=')[1].split('&')[0]
                    href = urllib.parse.unquote(href)
                    clean = self.clean_url(href)
                    if clean and 'google.com' not in clean and 'youtube.com' not in clean:
                        urls.append(clean)

                        # 2. تصفية الامتدادات
                        ext_list = [x.strip() for x in self.ext_filter.get().split(',')]
                        for ext in ext_list:
                            if clean.endswith('.' + ext):
                                sensitive.append(f"[EXT:{ext}] {clean}")

                        # 3. استخراج الملفات الحساسة (حسب الاسم)
                        if self.extract_sensitive.get():
                            for pattern in ['.env', '.sql', '.log', '.bak', '.conf', '.json', '.xml']:
                                if pattern in clean:
                                    sensitive.append(f"[SENS:{pattern}] {clean}")

            # 4. استخراج الإيميلات من النص الكامل
            if self.extract_emails.get():
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found_emails = re.findall(email_pattern, resp.text)
                for em in found_emails:
                    if em not in emails and 'example.com' not in em:
                        emails.append(em)

        except Exception:
            pass

        return (list(dict.fromkeys(urls)), list(dict.fromkeys(emails)), list(dict.fromkeys(sensitive)))

    def scan_finished(self):
        self.running = False
        self.run_btn.config(state=tk.NORMAL, text="▶ START LEECH")
        self.stop_btn.config(state=tk.DISABLED)
        self.progress["value"] = self.progress["maximum"]

        self.log(f"✅ اكتمل المسح!", "success")
        self.log(f"📌 الروابط: {len(self.results)} → {self.url_file}", "info")
        self.log(f"📧 الإيميلات: {len(self.emails_found)} → {self.email_file}", "info")
        self.log(f"📁 الملفات الحساسة: محفوظة في {self.sensitive_file}", "info")

        messagebox.showinfo("اكتمل", f"تم الحفظ في:\n{self.output_dir}\nروابط: {len(self.results)}\nإيميلات: {len(self.emails_found)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VulnLeecher(root)
    root.mainloop()