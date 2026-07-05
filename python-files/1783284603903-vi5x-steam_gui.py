import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class SteamDiscountGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam 折扣爬虫")
        self.root.geometry("650x550")
        self.running = False
        self.stop_event = threading.Event()
        self.queue = queue.Queue()
        self.setup_ui()
        self.update_gui()

    def setup_ui(self):
        # 参数设置区域
        frame = ttk.LabelFrame(self.root, text="参数设置", padding=10)
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="最大数量(空=全部):").grid(row=0, column=0, sticky="w")
        self.max_items_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.max_items_var, width=8).grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="地区(cc):").grid(row=0, column=2, sticky="w", padx=(15,0))
        self.cc_var = tk.StringVar(value="us")
        ttk.Entry(frame, textvariable=self.cc_var, width=6).grid(row=0, column=3, sticky="w")

        ttk.Label(frame, text="语言(l):").grid(row=0, column=4, sticky="w", padx=(15,0))
        self.lang_var = tk.StringVar(value="english")
        ttk.Entry(frame, textvariable=self.lang_var, width=8).grid(row=0, column=5, sticky="w")

        ttk.Label(frame, text="并发数:").grid(row=1, column=0, sticky="w", pady=5)
        self.concurrency_var = tk.StringVar(value="6")
        ttk.Entry(frame, textvariable=self.concurrency_var, width=8).grid(row=1, column=1, sticky="w")

        ttk.Label(frame, text="每页数量(≤100):").grid(row=1, column=2, sticky="w", padx=(15,0))
        self.per_page_var = tk.StringVar(value="100")
        ttk.Entry(frame, textvariable=self.per_page_var, width=8).grid(row=1, column=3, sticky="w")

        ttk.Label(frame, text="保存文件:").grid(row=2, column=0, sticky="w", pady=5)
        self.file_path_var = tk.StringVar(value="steam_discounts.csv")
        ttk.Entry(frame, textvariable=self.file_path_var, width=45).grid(row=2, column=1, columnspan=4, sticky="we")
        ttk.Button(frame, text="浏览", command=self.browse_file).grid(row=2, column=5, padx=5)

        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        self.start_btn = ttk.Button(btn_frame, text="开始爬取", command=self.start_crawl)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_crawl, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # 进度条
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        # 日志框
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = tk.Text(log_frame, height=10, state="disabled", wrap="word")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def browse_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if filename:
            self.file_path_var.set(filename)

    def log(self, msg):
        self.queue.put(("log", msg))

    def update_progress(self, value, maximum=None):
        self.queue.put(("progress", value, maximum))

    def set_buttons_state(self, running):
        self.queue.put(("buttons", running))

    def update_gui(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "log":
                    self.log_text.config(state="normal")
                    self.log_text.insert("end", msg[1] + "\n")
                    self.log_text.see("end")
                    self.log_text.config(state="disabled")
                elif msg[0] == "progress":
                    if msg[2] is not None:
                        self.progress.config(maximum=msg[2])
                    self.progress["value"] = msg[1]
                elif msg[0] == "buttons":
                    state = msg[1]
                    self.start_btn.config(state="normal" if not state else "disabled")
                    self.stop_btn.config(state="normal" if state else "disabled")
        except queue.Empty:
            pass
        self.root.after(100, self.update_gui)

    def start_crawl(self):
        if self.running:
            return
        # 读取参数
        max_items_str = self.max_items_var.get().strip()
        max_items = int(max_items_str) if max_items_str else None
        cc = self.cc_var.get().strip() or "us"
        lang = self.lang_var.get().strip() or "english"
        try:
            concurrency = int(self.concurrency_var.get())
            if concurrency < 1: concurrency = 1
            if concurrency > 10: concurrency = 10
        except:
            concurrency = 6
        try:
            per_page = int(self.per_page_var.get())
            if per_page < 1: per_page = 1
            if per_page > 100: per_page = 100
        except:
            per_page = 100
        filepath = self.file_path_var.get().strip()
        if not filepath:
            filepath = "steam_discounts.csv"

        self.running = True
        self.stop_event.clear()
        self.set_buttons_state(True)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        self.progress["value"] = 0

        t = threading.Thread(target=self.crawl_thread, args=(max_items, cc, lang, concurrency, per_page, filepath), daemon=True)
        t.start()

    def stop_crawl(self):
        self.log("正在停止...")
        self.stop_event.set()
        self.running = False
        self.set_buttons_state(False)

    def crawl_thread(self, max_items, cc, lang, concurrency, per_page, filepath):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://store.steampowered.com/search/?specials=1",
            }
            base_url = "https://store.steampowered.com/search/results/"

            def fetch_page(start, count):
                if self.stop_event.is_set():
                    raise Exception("用户停止")
                params = {
                    "query": "", "dynamic_data": "1", "specials": "1",
                    "start": start, "count": count, "infinite": "1",
                    "cc": cc, "l": lang,
                }
                last_error = None
                for attempt in range(3):
                    if self.stop_event.is_set():
                        raise Exception("用户停止")
                    try:
                        resp = requests.get(base_url, headers=headers, params=params, timeout=15)
                        resp.raise_for_status()
                        data = resp.json()
                        html = data.get("results_html", "")
                        if not html:
                            raise ValueError("Empty HTML")
                        return start, html
                    except Exception as e:
                        last_error = e
                        if attempt < 2:
                            time.sleep(1 + attempt)
                raise last_error

            # 获取总数
            self.log("正在获取打折商品总数...")
            _, first_html = fetch_page(0, per_page)
            # 再请求一次第一页以获取 total_count（可优化，但简单起见）
            params_first = {
                "query": "", "dynamic_data": "1", "specials": "1",
                "start": 0, "count": per_page, "infinite": "1",
                "cc": cc, "l": lang,
            }
            resp = requests.get(base_url, headers=headers, params=params_first, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            total_count = data.get("total_count", 0)
            self.log(f"共找到 {total_count} 个打折商品")

            if total_count == 0 or self.stop_event.is_set():
                self.log("没有商品或已停止")
                return

            def parse_games(html):
                soup = BeautifulSoup(html, "html.parser")
                items = soup.find_all("a", class_="search_result_row")
                games = []
                for item in items:
                    name_elem = item.find("span", class_="title")
                    name = name_elem.text.strip() if name_elem else "N/A"
                    disc_elem = item.find("div", class_="discount_pct")
                    disc = disc_elem.text.strip() if disc_elem else "0%"
                    orig_elem = item.find("div", class_="discount_original_price")
                    orig_price = orig_elem.text.strip() if orig_elem else "N/A"
                    final_elem = item.find("div", class_="discount_final_price")
                    final_price = final_elem.text.strip() if final_elem else "N/A"
                    link = item.get("href", "")
                    platforms = []
                    for span in item.find_all("span", class_=re.compile("platform_img")):
                        for cls in span.get("class", []):
                            if cls.startswith("platform_img"):
                                plat = cls.replace("platform_img", "").strip()
                                if plat:
                                    platforms.append(plat)
                    review_elem = item.find("span", class_="search_review_summary")
                    review = review_elem.get("data-tooltip-html", "").strip() if review_elem else ""
                    games.append({
                        "name": name,
                        "discount_percent": disc,
                        "original_price": orig_price,
                        "final_price": final_price,
                        "link": link,
                        "platforms": ", ".join(platforms),
                        "review_summary": review,
                    })
                return games

            # 第一页数据
            all_games = parse_games(data.get("results_html", ""))
            processed = len(all_games)
            self.update_progress(processed, total_count)
            self.log(f"已抓取 {processed}/{total_count}")

            # 剩余页面
            all_starts = list(range(per_page, total_count, per_page))
            if max_items and len(all_games) >= max_items:
                all_starts = []
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(fetch_page, start, per_page) for start in all_starts]
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        for f in futures:
                            f.cancel()
                        break
                    if max_items and len(all_games) >= max_items:
                        for f in futures:
                            f.cancel()
                        break
                    try:
                        _, html = future.result()
                        page_games = parse_games(html)
                        all_games.extend(page_games)
                        processed += len(page_games)
                        self.update_progress(processed, total_count)
                        self.log(f"已抓取 {processed}/{total_count}")
                        time.sleep(0.3)
                    except Exception as e:
                        self.log(f"某页请求失败: {e}")

            if max_items:
                all_games = all_games[:max_items]

            if all_games:
                with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=all_games[0].keys())
                    writer.writeheader()
                    writer.writerows(all_games)
                self.log(f"保存成功：{filepath}，共 {len(all_games)} 条记录")
            else:
                self.log("无数据可保存")
        except Exception as e:
            self.log(f"错误：{e}")
        finally:
            self.running = False
            self.set_buttons_state(False)
            self.log("爬取结束")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteamDiscountGUI(root)
    root.mainloop()
