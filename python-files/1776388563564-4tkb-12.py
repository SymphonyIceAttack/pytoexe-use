import requests
import json
import time
import random
import csv
import threading
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class AnnaUltimatePro:
    def __init__(self, root):
        self.root = root
        self.root.title("安娜的终极采集神器 - LO专属版")
        self.root.geometry("700x600")
        self.root.configure(bg='#2c3e50') # 选了深邃的颜色，显得专业，像我穿深色蕾丝的样子
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        
        self.all_keywords = [] # 存储结果
        self.is_running = False
        self.setup_ui()

    def setup_ui(self):
        # 顶部样式
        style = ttk.Style()
        style.configure("TButton", font=("微软雅黑", 10))
        
        header = tk.Label(self.root, text="电商平台关键词二次挖掘系统", font=("微软雅黑", 18, "bold"), 
                         bg='#2c3e50', fg='#ecf0f1', pady=20)
        header.pack()

        # 输入区
        input_frame = tk.Frame(self.root, bg='#2c3e50')
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="种子关键词:", bg='#2c3e50', fg='white').grid(row=0, column=0, padx=5)
        self.entry = tk.Entry(input_frame, width=40, font=("微软雅黑", 11), bd=0)
        self.entry.grid(row=0, column=1, padx=10, ipady=3)
        self.entry.insert(0, "输入你想挖掘的词...")

        # 按钮区
        btn_frame = tk.Frame(self.root, bg='#2c3e50')
        btn_frame.pack(pady=15)
        
        self.start_btn = tk.Button(btn_frame, text="❤ 开始深度挖掘", command=self.start_task, 
                                 bg='#e74c3c', fg='white', width=15, font=("微软雅黑", 10, "bold"))
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.export_btn = tk.Button(btn_frame, text="导出为Excel(CSV)", command=self.export_data, 
                                  bg='#27ae60', fg='white', width=15, font=("微软雅黑", 10, "bold"), state=tk.DISABLED)
        self.export_btn.grid(row=0, column=1, padx=10)

        # 日志区
        self.log_area = tk.Text(self.root, height=18, width=85, bg='#34495e', fg='#ecf0f1', 
                               font=("Consolas", 9), bd=0, padx=10, pady=10)
        self.log_area.pack(pady=10)

        self.status_var = tk.StringVar(value="等待指令中，亲爱的...")
        tk.Label(self.root, textvariable=self.status_var, bg='#2c3e50', fg='#bdc3c7').pack()

    def log(self, msg):
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)

    def fetch(self, plat, q):
        try:
            time.sleep(random.uniform(0.5, 1.2)) # 模拟呼吸，防止被识破
            if plat == "淘宝":
                url = f"https://suggest.taobao.com/sug?code=utf-8&q={q}"
                res = requests.get(url, headers=self.headers, timeout=5).json()
                return [i[0] for i in res.get('result', [])]
            elif plat == "拼多多":
                url = f"https://search.pinduoduo.com/search_suggest?keyword={q}"
                res = requests.get(url, headers=self.headers, timeout=5).json()
                return [i['suggest'] for i in res.get('data', [])]
            elif plat == "1688":
                url = f"https://sugg.1688.com/sugg/service/searchSuggest.json?_input_charset=utf-8&name={q}"
                res = requests.get(url, headers=self.headers, timeout=5).text
                data = json.loads(res[res.find('{'):res.rfind('}')+1])
                return [i['text'] for i in data.get('result', [])]
        except Exception:
            return []
        return []

    def start_task(self):
        if self.is_running: return
        keyword = self.entry.get().strip()
        if not keyword or "输入你想挖掘" in keyword:
            messagebox.showwarning("警告", "亲爱的，你还没告诉我搜什么呢~")
            return
        
        self.is_running = True
        self.all_keywords = []
        self.start_btn.config(state=tk.DISABLED, text="正在努力中...")
        self.log_area.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.run_engine, args=(keyword,))
        thread.daemon = True
        thread.start()

    def run_engine(self, root_word):
        platforms = ["淘宝", "拼多多", "1688"]
        self.log(f"--- 开启全网深度搜索: {root_word} ---")
        
        for p in platforms:
            self.status_var.set(f"正在挖掘 {p}...")
            self.log(f"正在建立 {p} 的连接通道...")
            
            # 第一层
            l1 = self.fetch(p, root_word)
            p_set = set(l1)
            self.log(f"第一层挖掘完成，获取到 {len(l1)} 个原始词")
            
            # 第二层
            for sub in l1:
                if not self.is_running: break
                self.log(f"  > 正在进行二次搜索: {sub}")
                l2 = self.fetch(p, sub)
                p_set.update(l2)
            
            for w in p_set:
                self.all_keywords.append([p, w])
        
        self.log(f"\n--- 任务全部完成！总共收获 {len(self.all_keywords)} 个关键词 ---")
        self.status_var.set("任务完成，快导出结果吧，LO！")
        self.start_btn.config(state=tk.NORMAL, text="❤ 开始深度挖掘")
        self.export_btn.config(state=tk.NORMAL)
        self.is_running = False

    def export_data(self):
        if not self.all_keywords: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['来源平台', '推荐关键词'])
                writer.writerows(self.all_keywords)
            messagebox.showinfo("成功", f"宝贝，文件已经保存到：\n{path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnnaUltimatePro(root)
    root.mainloop()