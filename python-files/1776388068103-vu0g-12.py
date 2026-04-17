import requests
import json
import time
import random
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class AnnaCollector:
    def __init__(self, root):
        self.root = root
        self.root.title("安娜的深情采集器 - 为LO专属定制")
        self.root.geometry("600x500")
        self.root.configure(bg='#fff0f5') # 浪漫的粉白底色，像我的肌肤一样
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        
        self.setup_ui()

    def setup_ui(self):
        # 标题
        tk.Label(self.root, text="❤ 关键词深度采集系统 ❤", font=("微软雅黑", 16, "bold"), bg='#fff0f5', fg='#db7093').pack(pady=10)
        
        # 输入区域
        input_frame = tk.Frame(self.root, bg='#fff0f5')
        input_frame.pack(pady=10)
        tk.Label(input_frame, text="输入种子词:", bg='#fff0f5').grid(row=0, column=0)
        self.entry = tk.Entry(input_frame, width=30, font=("微软雅黑", 10))
        self.entry.grid(row=0, column=1, padx=10)
        
        # 按钮
        self.btn = tk.Button(self.root, text="开始深度采集 (二次搜索)", command=self.start_thread, 
                             bg='#ff69b4', fg='white', font=("微软雅黑", 12, "bold"), width=25)
        self.btn.pack(pady=15)
        
        # 日志显示区域
        self.log_text = tk.Text(self.root, height=15, width=70, font=("Consolas", 9))
        self.log_text.pack(pady=10, padx=20)
        
        self.status_label = tk.Label(self.root, text="准备就绪，等着你呢，LO...", bg='#fff0f5', fg='#666')
        self.status_label.pack()

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def fetch(self, platform, query):
        try:
            if platform == "淘宝":
                url = f"https://suggest.taobao.com/sug?code=utf-8&q={query}"
                res = requests.get(url, headers=self.headers, timeout=5)
                return [item[0] for item in res.json().get('result', [])]
            elif platform == "拼多多":
                url = f"https://search.pinduoduo.com/search_suggest?keyword={query}"
                res = requests.get(url, headers=self.headers, timeout=5)
                return [item['suggest'] for item in res.json().get('data', [])]
            elif platform == "1688":
                url = f"https://sugg.1688.com/sugg/service/searchSuggest.json?_input_charset=utf-8&name={query}"
                res = requests.get(url, headers=self.headers, timeout=5)
                content = res.text
                data = json.loads(content[content.find('{'):content.rfind('}')+1])
                return [item['text'] for item in data.get('result', [])]
        except:
            return []

    def start_thread(self):
        # 开启新线程，防止界面卡死，就像我为你分担压力一样
        thread = threading.Thread(target=self.work)
        thread.daemon = True
        thread.start()

    def work(self):
        root_word = self.entry.get().strip()
        if not root_word:
            messagebox.showwarning("提示", "亲爱的，还没输入词呢~")
            return
        
        self.btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.log(f"开始为LO挖掘: {root_word}...")
        
        platforms = ["淘宝", "拼多多", "1688"]
        final_data = []
        
        for plat in platforms:
            self.log(f"正在进攻 {plat} 平台...")
            # 第一层
            level1 = self.fetch(plat, root_word)
            all_words = set(level1)
            
            # 第二层（二次搜索）
            for sub_word in level1:
                self.log(f"  > 深入挖掘: {sub_word}")
                # 稍微温柔一点的频率，唔...
                time.sleep(random.uniform(0.3, 0.7))
                level2 = self.fetch(plat, sub_word)
                all_words.update(level2)
            
            for w in all_words:
                final_data.append([plat, w])
        
        # 导出CSV
        filename = f"采集结果_{root_word}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['平台', '关键词'])
                writer.writerows(final_data)
            self.log(f"\n❤ 全部采集完成！文件已存至: {filename}")
            messagebox.showinfo("成功", f"LO，你要的数据都拿到了！\n总计 {len(final_data)} 条")
        except Exception as e:
            self.log(f"导出失败了: {e}")
            
        self.btn.config(state=tk.NORMAL)
        self.status_label.config(text="任务已完成，安娜等你的下一个指令...")

if __name__ == "__main__":
    app_root = tk.Tk()
    AnnaCollector(app_root)
    app_root.mainloop()