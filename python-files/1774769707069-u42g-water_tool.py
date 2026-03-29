# -*- coding: utf-8 -*-
# 适配在线PY转EXE工具，tkinter轻量化，无复杂线程/依赖，打包后不闪退
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import webbrowser
import re

# 全局配置（无需修改，适配在线打包）
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36"}
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}|(\d{2})月(\d{2})日(\d{4})")

class WaterToolOnline:
    def __init__(self, root):
        self.root = root
        self.root.title("水利招标抓取+AI推文生成")
        self.root.geometry("950x850")
        self.root.resizable(False, False)
        self._init_ui()
        # 初始化默认值（用户可修改）
        self.start_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.key_entry.insert(0, "水利 中标 招标 水电 河道")

    def _init_ui(self):
        # 1. 多抓取网站
        ttk.Label(self.root, text="【1】抓取网站（一行一个）").place(x=20, y=10)
        self.url_text = scrolledtext.ScrolledText(self.root, width=115, height=4)
        self.url_text.place(x=20, y=35)

        # 2. 关键词+日期筛选
        ttk.Label(self.root, text="关键词（空格分隔）").place(x=20, y=110)
        self.key_entry = ttk.Entry(self.root, width=35)
        self.key_entry.place(x=130, y=110)

        ttk.Label(self.root, text="开始日期").place(x=400, y=110)
        self.start_entry = ttk.Entry(self.root, width=15)
        self.start_entry.place(x=470, y=110)

        ttk.Label(self.root, text="结束日期").place(x=600, y=110)
        self.end_entry = ttk.Entry(self.root, width=15)
        self.end_entry.place(x=670, y=110)

        # 3. 范文/写作要求
        ttk.Label(self.root, text="【2】公众号范文/写作要求").place(x=20, y=145)
        self.fanwen_text = scrolledtext.ScrolledText(self.root, width=115, height=8)
        self.fanwen_text.place(x=20, y=170)

        # 4. 抓取结果
        ttk.Label(self.root, text="【3】抓取到的信息").place(x=20, y=310)
        self.result_text = scrolledtext.ScrolledText(self.root, width=115, height=12)
        self.result_text.place(x=20, y=335)

        # 5. 豆包推文提示词（直接复制用）
        ttk.Label(self.root, text="【4】豆包生成提示词（复制到豆包网页版）").place(x=20, y=530)
        self.prompt_text = scrolledtext.ScrolledText(self.root, width=115, height=14)
        self.prompt_text.place(x=20, y=555)

        # 功能按钮
        ttk.Button(self.root, text="🚀 开始抓取", command=self.crawl_data).place(x=80, y=800, width=120)
        ttk.Button(self.root, text="📝 生成豆包提示词", command=self.make_prompt).place(x=220, y=800, width=150)
        ttk.Button(self.root, text="🌐 打开豆包", command=lambda: webbrowser.open("https://www.doubao.com")).place(x=390, y=800, width=120)
        ttk.Button(self.root, text="📋 复制提示词", command=self.copy_prompt).place(x=530, y=800, width=120)
        ttk.Button(self.root, text="🧹 清空所有", command=self.clear_all).place(x=670, y=800, width=120)

    # 日期校验与转换（适配常见格式）
    def _parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None

    # 核心抓取逻辑（轻量化，无复杂线程，适配在线打包）
    def crawl_data(self):
        self.result_text.delete(1.0, tk.END)
        urls = [u.strip() for u in self.url_text.get(1.0, tk.END).splitlines() if u.strip()]
        keys = self.key_entry.get().strip().split()
        start_dt = self._parse_date(self.start_entry.get().strip())
        end_dt = self._parse_date(self.end_entry.get().strip())

        # 基础校验
        if not urls:
            messagebox.showwarning("提示", "请至少输入一个抓取网站！")
            return
        if not start_dt or not end_dt:
            messagebox.showwarning("提示", "日期格式请填写：YYYY-MM-DD！")
            return
        if start_dt > end_dt:
            messagebox.showwarning("提示", "开始日期不能晚于结束日期！")
            return

        self.result_text.insert(tk.END, "正在抓取数据，请稍候...\n")
        self.root.update()  # 刷新界面，避免假死
        res = []
        for url in urls:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.find_all(["a", "li", "div"], limit=30)
                for item in items:
                    txt = item.get_text(strip=True)
                    if not txt:
                        continue
                    # 关键词筛选
                    if keys and not any(k in txt for k in keys):
                        continue
                    # 日期筛选
                    date_match = DATE_PATTERN.search(txt)
                    if date_match:
                        item_date = self._parse_date(date_match.group())
                        if item_date and not (start_dt <= item_date <= end_dt):
                            continue
                    # 拼接链接
                    link = item.get("href", "")
                    if link and not link.startswith(("http://", "https://")):
                        link = requests.compat.urljoin(url, link)
                    res.append(f"【信息】{txt}\n【链接】{link}\n\n")
            except Exception as e:
                res.append(f"【抓取失败】{url} - 原因：{str(e)}\n\n")

        final_data = "".join(res) if res else "未抓取到符合条件的信息！"
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, final_data)
        messagebox.showinfo("完成", "数据抓取结束！")

    # 生成豆包提示词（直接复制可用）
    def make_prompt(self):
        crawl_data = self.result_text.get(1.0, tk.END).strip()
        fanwen = self.fanwen_text.get(1.0, tk.END).strip()
        today = datetime.now().strftime("%Y年%m月%d日")

        if not crawl_data or crawl_data == "未抓取到符合条件的信息！":
            messagebox.showwarning("提示", "请先抓取有效数据！")
            return
        if not fanwen:
            fanwen = "专业简洁，符合水利行业公众号风格，标题包含当日日期，结构清晰，结尾标注信息来源。"

        prompt = f"""
你是资深水利行业公众号编辑，根据以下信息生成一篇公众号推文，严格遵循要求：
【写作风格/范文要求】
{fanwen}
【今日水利招标/中标信息（已按关键词+日期筛选）】
{crawl_data}
【推文硬性要求】
1. 标题必须包含：{today} 水利行业招标中标信息汇总
2. 排版适配微信公众号，用<br>实现换行，无需复杂格式
3. 语言正式专业，符合水利工程行业阅读习惯
4. 结尾明确标注：信息来源为公开招标平台，仅供参考
5. 直接输出推文正文，无多余表情、符号和开场白
"""
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, prompt)

    # 复制提示词到剪贴板
    def copy_prompt(self):
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showwarning("提示", "暂无提示词可复制！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(prompt)
        messagebox.showinfo("成功", "提示词已复制到剪贴板！")

    # 清空所有内容
    def clear_all(self):
        for widget in [self.url_text, self.result_text, self.prompt_text, self.fanwen_text]:
            widget.delete(1.0, tk.END)
        self.key_entry.delete(0, tk.END)
        self.start_entry.delete(0, tk.END)
        self.end_entry.delete(0, tk.END)

if __name__ == "__main__":
    # 轻量化tkinter启动，适配在线打包
    root = tk.Tk()
    app = WaterToolOnline(root)
    root.mainloop()