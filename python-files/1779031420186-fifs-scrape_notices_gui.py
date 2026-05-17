import requests
import json
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import os

class NoticeScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("东方财富公告爬虫")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        
        # 爬虫状态
        self.is_running = False
        self.is_paused = False
        self.all_notices = []
        self.current_page = 0
        self.total_pages = 500
        self.page_size = 100
        
        # 重试配置
        self.max_retries = 5  # 最大重试次数
        self.retry_delay = 2  # 重试间隔(秒)
        
        # 配置样式
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        """配置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主色调
        style.configure("Title.TLabel", font=("Microsoft YaHei", 18, "bold"), foreground="#1a73e8")
        style.configure("Header.TLabel", font=("Microsoft YaHei", 11), foreground="#333")
        style.configure("Info.TLabel", font=("Microsoft YaHei", 10), foreground="#666")
        style.configure("Count.TLabel", font=("Microsoft YaHei", 12, "bold"), foreground="#34a853")
        
        # 按钮样式
        style.configure("Start.TButton", font=("Microsoft YaHei", 11), background="#34a853", foreground="white")
        style.configure("Pause.TButton", font=("Microsoft YaHei", 11), background="#fbbc04", foreground="#333")
        style.configure("Stop.TButton", font=("Microsoft YaHei", 11), background="#ea4335", foreground="white")
        style.configure("Save.TButton", font=("Microsoft YaHei", 10))
        
    def setup_ui(self):
        """设置界面"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="东方财富公告爬虫", style="Title.TLabel").pack(side=tk.LEFT)
        
        # 状态栏
        status_frame = ttk.LabelFrame(main_frame, text=" 爬取状态 ", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 进度信息
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(info_frame, text="等待开始...", style="Info.TLabel")
        self.status_label.pack(side=tk.LEFT)
        
        self.count_label = ttk.Label(info_frame, text="已获取: 0 条", style="Count.TLabel")
        self.count_label.pack(side=tk.RIGHT)
        
        # 进度条
        self.progress = ttk.Progressbar(status_frame, mode='determinate', length=300)
        self.progress.pack(fill=tk.X, pady=(10, 0))
        
        # 配置面板
        config_frame = ttk.LabelFrame(main_frame, text=" 爬取配置 ")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        config_inner = ttk.Frame(config_frame)
        config_inner.pack(fill=tk.X, padx=10, pady=8)
        
        # 总页数
        ttk.Label(config_inner, text="总页数:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.total_pages_var = tk.IntVar(value=500)
        total_pages_spin = ttk.Spinbox(config_inner, from_=1, to=10000, textvariable=self.total_pages_var, width=8)
        total_pages_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        # 每页条数
        ttk.Label(config_inner, text="每页条数:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        self.page_size_var = tk.IntVar(value=100)
        page_size_spin = ttk.Spinbox(config_inner, from_=10, to=100, textvariable=self.page_size_var, width=8)
        page_size_spin.grid(row=0, column=3, sticky=tk.W, padx=5, pady=3)
        
        # 最大重试次数
        ttk.Label(config_inner, text="最大重试:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=3)
        self.max_retries_var = tk.IntVar(value=5)
        max_retries_spin = ttk.Spinbox(config_inner, from_=0, to=20, textvariable=self.max_retries_var, width=8)
        max_retries_spin.grid(row=0, column=5, sticky=tk.W, padx=5, pady=3)
        
        # 重试间隔
        ttk.Label(config_inner, text="重试间隔(秒):").grid(row=0, column=6, sticky=tk.W, padx=5, pady=3)
        self.retry_delay_var = tk.IntVar(value=2)
        retry_delay_spin = ttk.Spinbox(config_inner, from_=1, to=30, textvariable=self.retry_delay_var, width=8)
        retry_delay_spin.grid(row=0, column=7, sticky=tk.W, padx=5, pady=3)
        
        # 控制按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_btn = ttk.Button(btn_frame, text="▶ 开始", command=self.start_scraping, style="Start.TButton", width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(btn_frame, text="⏸ 暂停", command=self.toggle_pause, state=tk.DISABLED, width=12)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", command=self.stop_scraping, state=tk.DISABLED, style="Stop.TButton", width=12)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(btn_frame, text="💾 保存Excel", command=self.save_to_excel, width=12)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        # 日志显示
        log_frame = ttk.LabelFrame(main_frame, text=" 运行日志 ")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 日志文本框
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_text_frame, height=8, font=("Consolas", 9), wrap=tk.WORD,
                                bg="#f8f9fa", fg="#333", relief=tk.FLAT, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_text_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 数据表格
        table_frame = ttk.LabelFrame(main_frame, text=" 公告数据预览 ")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表格
        columns = ("代码", "名称", "公告名称", "公告类型", "公告日期", "公告地址")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        # 设置列
        self.tree.heading("代码", text="股票代码")
        self.tree.heading("名称", text="股票简称")
        self.tree.heading("公告名称", text="公告名称")
        self.tree.heading("公告类型", text="公告类型")
        self.tree.heading("公告日期", text="公告日期")
        self.tree.heading("公告地址", text="公告地址")
        
        self.tree.column("代码", width=80, anchor=tk.CENTER)
        self.tree.column("名称", width=80, anchor=tk.CENTER)
        self.tree.column("公告名称", width=250, anchor=tk.W)
        self.tree.column("公告类型", width=120, anchor=tk.CENTER)
        self.tree.column("公告日期", width=120, anchor=tk.CENTER)
        self.tree.column("公告地址", width=200, anchor=tk.W)
        
        # 表格样式
        style = ttk.Style()
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=25)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        
        # 滚动条
        yscroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        
        # 绑定双击打开链接
        self.tree.bind("<Double-1>", self.open_link)
        
    def log(self, message):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_status(self, text):
        """更新状态"""
        self.status_label.config(text=text)
        self.root.update_idletasks()
        
    def update_count(self, count):
        """更新计数"""
        self.count_label.config(text=f"已获取: {count} 条")
        self.count_label.pack(side=tk.RIGHT)
        self.root.update_idletasks()
        
    def update_progress(self, value):
        """更新进度"""
        self.progress['value'] = value
        self.root.update_idletasks()
        
    def toggle_pause(self):
        """暂停/继续"""
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="⏸ 暂停")
            self.log("继续爬取...")
        else:
            self.is_paused = True
            self.pause_btn.config(text="▶ 继续")
            self.log("已暂停")
            
    def start_scraping(self):
        """开始爬取"""
        if self.is_running:
            return
            
        # 读取配置
        self.total_pages = self.total_pages_var.get()
        self.page_size = self.page_size_var.get()
        self.max_retries = self.max_retries_var.get()
        self.retry_delay = self.retry_delay_var.get()
        
        self.is_running = True
        self.is_paused = False
        self.current_page = 0
        self.all_notices = []
        
        # 更新按钮状态
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="⏸ 暂停")
        self.stop_btn.config(state=tk.NORMAL)
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.log("开始爬取公告数据...")
        self.update_status("正在爬取...")
        
        # 启动爬取线程
        self.thread = threading.Thread(target=self.scraping_worker, daemon=True)
        self.thread.start()
        
    def stop_scraping(self):
        """停止爬取"""
        self.is_running = False
        self.is_paused = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.log("已停止爬取")
        self.update_status("已停止")
        self.update_progress(0)
        
    def scraping_worker(self):
        """爬取工作线程"""
        for page in range(1, self.total_pages + 1):
            if not self.is_running:
                break
                
            # 检查暂停
            while self.is_paused and self.is_running:
                import time
                time.sleep(0.5)
                
            if not self.is_running:
                break
                
            self.current_page = page
            
            # 在主线程更新UI
            self.root.after(0, lambda p=page: self.update_status(f"正在爬取第 {p}/{self.total_pages} 页..."))
            self.root.after(0, lambda p=page: self.update_progress(p / self.total_pages * 100))
            
            try:
                notices = self.fetch_page_with_retry(page)
                
                if notices:
                    self.all_notices.extend(notices)
                    
                    # 更新UI
                    self.root.after(0, lambda n=len(self.all_notices): self.update_count(n))
                    self.root.after(0, lambda: self.log(f"第 {page} 页: 获取 {len(notices)} 条"))
                    
                    # 更新表格（显示前100条）
                    if len(self.all_notices) <= 100:
                        self.root.after(0, lambda notices=notices: self.update_table(notices))
                else:
                    self.root.after(0, lambda: self.log(f"第 {page} 页无数据，停止爬取"))
                    break
                    
            except Exception as e:
                self.root.after(0, lambda err=str(e): self.log(f"第 {page} 页出错: {err}"))
                continue
                
        # 完成
        self.is_running = False
        self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.pause_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        self.root.after(0, lambda: self.update_status("爬取完成"))
        self.root.after(0, lambda: self.log(f"爬取完成! 共获取 {len(self.all_notices)} 条数据"))
        
    def fetch_page_with_retry(self, page_index):
        """带重试机制获取单页数据"""
        for attempt in range(1, self.max_retries + 1):
            try:
                notices = self.fetch_page(page_index)
                if notices:
                    return notices
                    
                # 如果没有数据但请求成功，不重试
                return []
                
            except Exception as e:
                if attempt < self.max_retries:
                    self.root.after(0, lambda a=attempt, err=str(e): 
                        self.log(f"第 {page_index} 页第 {a} 次请求失败: {err}，{self.retry_delay}秒后重试..."))
                    import time
                    time.sleep(self.retry_delay)
                else:
                    self.root.after(0, lambda: self.log(f"第 {page_index} 页重试 {self.max_retries} 次后放弃"))
                    raise e
        return []
        
    def fetch_page(self, page_index):
        """获取单页数据"""
        url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
        
        params = {
            "sr": "-1",
            "page_size": self.page_size,
            "page_index": page_index,
            "ann_type": "SHA,CYB,SZA,BJA,INV",
            "client_source": "web",
            "f_node": "0",
            "s_node": "0"
        }
        
        headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Referer": "https://data.eastmoney.com/notices/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "list" in data["data"]:
                    return data["data"]["list"]
        except Exception as e:
            pass
            
        return []
        
    def parse_notice(self, item):
        """解析公告数据"""
        codes = item.get("codes", [])
        columns = item.get("columns", [])
        
        # 股票代码和名称
        code = "; ".join([c.get("stock_code", "") for c in codes])
        name = "; ".join([c.get("short_name", "") for c in codes])
        
        # 公告类型
        column_names = "; ".join([col.get("column_name", "") for col in columns])
        
        # 公告地址
        stock_code = codes[0].get("stock_code", "") if codes else ""
        art_code = item.get("art_code", "")
        url = f"https://data.eastmoney.com/notices/detail/{stock_code}/{art_code}.html"
        
        return {
            "代码": code,
            "名称": name,
            "公告名称": item.get("title", ""),
            "公告类型": column_names,
            "公告日期": item.get("notice_date", "")[:10] if item.get("notice_date") else "",
            "公告地址": url
        }
        
    def update_table(self, notices):
        """更新表格"""
        for notice in notices:
            parsed = self.parse_notice(notice)
            self.tree.insert("", tk.END, values=(
                parsed["代码"],
                parsed["名称"],
                parsed["公告名称"],
                parsed["公告类型"],
                parsed["公告日期"],
                parsed["公告地址"]
            ))
            
    def open_link(self, event):
        """双击打开链接"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            item = self.tree.selection()[0]
            url = self.tree.item(item, "values")[5]
            if url:
                import webbrowser
                webbrowser.open(url)
                
    def save_to_excel(self):
        """保存到Excel"""
        if not self.all_notices:
            messagebox.showwarning("提示", "没有可保存的数据")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")],
            initialfile=f"东方财富公告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
        if filename:
            try:
                data = []
                for notice in self.all_notices:
                    parsed = self.parse_notice(notice)
                    data.append(parsed)
                    
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False, engine='openpyxl')
                
                messagebox.showinfo("成功", f"已保存到:\n{filename}")
                self.log(f"数据已保存到: {filename}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存失败:\n{str(e)}")
                self.log(f"保存失败: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    
    # 设置窗口图标（如果存在）
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
        
    app = NoticeScraperApp(root)
    root.mainloop()
