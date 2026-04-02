import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import re
import webbrowser
import threading
import time

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股票人气榜查询助手")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="东方财富股票人气榜查询", 
                               font=("微软雅黑", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 说明文字
        info_text = (
            "使用说明：\n"
            "1. 在东方财富网站或其他地方复制股票代码\n"
            "2. 粘贴到下方输入框或直接粘贴到任意位置\n"
            "3. 程序会自动检测剪贴板变化并显示查询选项\n"
            "4. 支持的股票代码格式：00xxxx(深市), 60xxxx/68xxxx(沪市)"
        )
        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
        info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # 股票代码输入区域
        ttk.Label(main_frame, text="股票代码:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.stock_var = tk.StringVar()
        self.stock_entry = ttk.Entry(main_frame, textvariable=self.stock_var, font=("Arial", 12), width=20)
        self.stock_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.search_btn = ttk.Button(button_frame, text="查询人气榜", command=self.search_stock)
        self.search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.paste_btn = ttk.Button(button_frame, text="粘贴代码", command=self.paste_from_clipboard)
        self.paste_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空", command=self.clear_fields)
        self.clear_btn.pack(side=tk.LEFT)
        
        # 自动检测开关
        self.auto_detect_var = tk.BooleanVar(value=True)
        self.auto_detect_check = ttk.Checkbutton(
            main_frame, 
            text="开启自动检测剪贴板", 
            variable=self.auto_detect_var,
            command=self.toggle_auto_detect
        )
        self.auto_detect_check.grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        # 结果显示区域
        ttk.Label(main_frame, text="查询结果:", font=("微软雅黑", 10, "bold")).grid(
            row=5, column=0, sticky=tk.W, pady=(20, 5)
        )
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        main_frame.rowconfigure(6, weight=1)
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        
        self.result_text = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 开启自动检测后将监控剪贴板变化")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 初始化剪贴板监控
        self.last_clipboard_content = ""
        self.monitoring = False
        self.monitor_thread = None
        
        # 绑定回车键
        self.stock_entry.bind('<Return>', lambda event: self.search_stock())
        
        # 启动剪贴板监控
        self.start_clipboard_monitoring()
    
    def validate_stock_code(self, code):
        """验证股票代码格式"""
        if not code:
            return False
        # 匹配股票代码格式：6位数字，开头为00,30,60,68
        pattern = r'^(00|30|60|68)\d{4}$'
        return bool(re.match(pattern, code.strip()))
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴内容到输入框"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content.strip():
                # 尝试提取股票代码
                code = self.extract_stock_code(clipboard_content)
                if code:
                    self.stock_var.set(code)
                    self.status_var.set(f"已从剪贴板提取股票代码: {code}")
                else:
                    self.stock_var.set(clipboard_content.strip())
                    self.status_var.set("已粘贴剪贴板内容，请确认是否为股票代码")
            else:
                self.status_var.set("剪贴板为空")
        except Exception as e:
            self.status_var.set(f"粘贴失败: {str(e)}")
    
    def extract_stock_code(self, text):
        """从文本中提取股票代码"""
        # 尝试匹配6位数字的股票代码
        pattern = r'\b(00|30|60|68)\d{4}\b'
        matches = re.findall(pattern, text)
        if matches:
            # 返回第一个匹配的完整股票代码
            start_pos = text.find(matches[0])
            return text[start_pos:start_pos+6]
        return None
    
    def search_stock(self):
        """查询股票人气榜"""
        stock_code = self.stock_var.get().strip()
        
        if not stock_code:
            messagebox.showwarning("警告", "请输入股票代码！")
            return
        
        if not self.validate_stock_code(stock_code):
            messagebox.showerror("错误", f"'{stock_code}' 不是有效的股票代码格式！\n支持格式：00xxxx, 30xxxx, 60xxxx, 68xxxx")
            return
        
        # 在新线程中执行查询，避免界面冻结
        threading.Thread(target=self._perform_search, args=(stock_code,), daemon=True).start()
    
    def _perform_search(self, stock_code):
        """执行实际的搜索操作"""
        self.update_result_text("正在查询中...")
        
        # 模拟查询过程
        time.sleep(1)
        
        # 根据股票代码前缀判断市场
        market = "上海" if stock_code.startswith(('60', '68')) else "深圳"
        
        result = f"""股票代码: {stock_code}
所属市场: {market}证券交易所
查询状态: 成功获取查询链接

点击以下链接查看东方财富人气榜:
- https://so.eastmoney.com/web/s?keyword={stock_code}

人气榜相关信息:
- 今日人气排名: -- (需访问网站查看)
- 关注人数: -- (需访问网站查看)
- 讨论热度: -- (需访问网站查看)

注意: 由于网站策略限制，程序仅提供查询链接，
     实时数据请访问东方财富官方网站查看。
        """
        
        self.update_result_text(result)
        self.status_var.set(f"查询完成: {stock_code}")
    
    def update_result_text(self, text):
        """更新结果显示文本"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)
    
    def clear_fields(self):
        """清空所有字段"""
        self.stock_var.set("")
        self.update_result_text("")
        self.status_var.set("已清空")
    
    def toggle_auto_detect(self):
        """切换自动检测状态"""
        if self.auto_detect_var.get():
            self.start_clipboard_monitoring()
            self.status_var.set("已开启自动检测剪贴板")
        else:
            self.stop_clipboard_monitoring()
            self.status_var.set("已关闭自动检测剪贴板")
    
    def start_clipboard_monitoring(self):
        """开始剪贴板监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
            self.monitor_thread.start()
    
    def stop_clipboard_monitoring(self):
        """停止剪贴板监控"""
        self.monitoring = False
    
    def _monitor_clipboard(self):
        """监控剪贴板变化的后台线程"""
        while self.monitoring:
            try:
                current_content = pyperclip.paste()
                
                # 如果内容发生变化且开启了自动检测
                if (current_content != self.last_clipboard_content and 
                    self.auto_detect_var.get() and 
                    current_content.strip()):
                    
                    # 检查是否是股票代码
                    code = self.extract_stock_code(current_content)
                    if code and self.validate_stock_code(code):
                        self.root.after(0, lambda c=code: self._auto_fill_stock(c))
                
                self.last_clipboard_content = current_content
                time.sleep(0.5)  # 每0.5秒检查一次
                
            except Exception as e:
                print(f"剪贴板监控出错: {e}")
                time.sleep(1)
    
    def _auto_fill_stock(self, code):
        """自动填充股票代码"""
        self.stock_var.set(code)
        self.status_var.set(f"自动检测到股票代码: {code}")

def main():
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()