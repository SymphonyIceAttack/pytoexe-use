# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import schedule
import time
import threading

class WaterAutoPublishTool:
    def __init__(self, root):
        self.root = root
        self.root.title("水利行业·多网站抓取→AI推文→定时发公众号 V2.0")
        self.root.geometry("1000x900")
        self.root.resizable(False, False)

        # 1. 抓取网站
        ttk.Label(root, text="【1】抓取网站（一行一个网址）").place(x=20, y=10)
        self.url_text = scrolledtext.ScrolledText(root, width=120, height=4)
        self.url_text.place(x=20, y=35)

        # 2. 关键词 + 时间
        ttk.Label(root, text="关键词（空格分隔）").place(x=20, y=110)
        self.key_entry = ttk.Entry(root, width=40)
        self.key_entry.place(x=140, y=110)

        ttk.Label(root, text="开始日期：").place(x=450, y=110)
        self.start_entry = ttk.Entry(root, width=15)
        self.start_entry.place(x=510, y=110)

        ttk.Label(root, text="结束日期：").place(x=630, y=110)
        self.end_entry = ttk.Entry(root, width=15)
        self.end_entry.place(x=690, y=110)

        # 3. 范文要求
        ttk.Label(root, text="【2】公众号范文风格/写作要求").place(x=20, y=145)
        self.fanwen_text = scrolledtext.ScrolledText(root, width=120, height=8)
        self.fanwen_text.place(x=20, y=170)

        # 4. 公众号配置
        ttk.Label(root, text="【3】公众号配置").place(x=20, y=310)
        ttk.Label(root, text="AppID：").place(x=20, y=335)
        self.wx_appid = ttk.Entry(root, width=45)
        self.wx_appid.place(x=70, y=335)

        ttk.Label(root, text="AppSecret：").place(x=400, y=335)
        self.wx_secret = ttk.Entry(root, width=45)
        self.wx_secret.place(x=470, y=335)

        # 5. 发布时间
        ttk.Label(root, text="【4】定时发布时间（例：2026-03-29 08:30）").place(x=20, y=370)
        self.publish_time = ttk.Entry(root, width=50)
        self.publish_time.place(x=20, y=395)

        # 6. 豆包API
        ttk.Label(root, text="豆包API Key：").place(x=650, y=335)
        self.doubao_key = ttk.Entry(root, width=40)
        self.doubao_key.place(x=730, y=335)

        # 日志
        ttk.Label(root, text="【运行日志】").place(x=20, y=430)
        self.log_text = scrolledtext.ScrolledText(root, width=120, height=18)
        self.log_text.place(x=20, y=455)

        # 按钮
        ttk.Button(root, text="🚀 开始抓取数据", command=self.start_crawl_thread).place(x=80, y=770, width=140)
        ttk.Button(root, text="📝 生成公众号文章", command=self.gen_article_thread).place(x=240, y=770, width=140)
        ttk.Button(root, text="⏰ 启动定时发布", command=self.set_schedule).place(x=400, y=770, width=140)
        ttk.Button(root, text="📢 立即发布测试", command=self.publish_now_thread).place(x=560, y=770, width=120)
        ttk.Button(root, text="🧹 清空日志", command=lambda: self.log_text.delete(1.0, tk.END)).place(x=700, y=770, width=100)

        self.crawl_content = ""
        self.article_content = ""

    def log(self, msg):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{now}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def crawl_data(self):
        urls = [u.strip() for u in self.url_text.get(1.0, tk.END).splitlines() if u.strip()]
        keys = self.key_entry.get().strip().split()
        start_dt = self.start_entry.get().strip()
        end_dt = self.end_entry.get().strip()
        res = []

        for url in urls:
            try:
                self.log(f"正在抓取：{url}")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36"}
                r = requests.get(url, headers=headers, timeout=20)
                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.find_all(["a", "li", "div"], limit=40)

                for tag in items:
                    txt = tag.get_text(strip=True)
                    if not any(k in txt for k in keys):
                        continue
                    link = tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = url.rstrip("/") + "/" + link.lstrip("/")
                    res.append(f"{txt}\n链接：{link}\n")
            except Exception as e:
                self.log(f"抓取异常：{str(e)}")

        self.crawl_content = "\n".join(res) if res else "未抓取到符合条件的信息"
        self.log(f"抓取完成，共 {len(res)} 条有效信息")

    def start_crawl_thread(self):
        threading.Thread(target=self.crawl_data, daemon=True).start()

    def gen_article(self):
        if not self.doubao_key.get().strip():
            messagebox.showwarning("提示", "请填写豆包API Key")
            return
        if not self.crawl_content:
            messagebox.showwarning("提示", "请先抓取数据")
            return

        self.log("正在调用豆包生成文章...")
        prompt = f"""
你是水利行业公众号编辑，请根据下面信息写一篇公众号推文。

【写作要求/范文风格】
{self.fanwen_text.get(1.0, tk.END)}

【今日抓取信息】
{self.crawl_content}

要求：
1. 标题包含今日日期
2. 排版简洁专业
3. 直接输出正文，不要多余表情
4. 结尾标注信息来源
"""
        api = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.doubao_key.get().strip()}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "doubao-lite",
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            resp = requests.post(api, json=data, timeout=30)
            self.article_content = resp.json()["choices"][0]["message"]["content"]
            self.log("✅ 文章生成完成")
        except Exception as e:
            self.log(f"生成失败：{str(e)}")

    def gen_article_thread(self):
        threading.Thread(target=self.gen_article, daemon=True).start()

    def publish_to_wechat(self):
        if not self.article_content:
            self.log("无文章内容，取消发布")
            return
        try:
            self.log("正在发布至公众号...")
            appid = self.wx_appid.get().strip()
            secret = self.wx_secret.get().strip()

            # 获取token
            token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
            token = requests.get(token_url).json()["access_token"]

            # 上传图文
            news = {
                "articles": [
                    {
                        "title": f"水利行业招标汇总 {datetime.now().strftime('%m月%d日')}",
                        "content": self.article_content.replace("\n", "<br>"),
                        "show_cover_pic": 0
                    }
                ]
            }
            up_url = f"https://api.weixin.qq.com/cgi-bin/material/add_news?access_token={token}"
            media = requests.post(up_url, json=news).json()
            media_id = media["media_id"]

            # 群发
            send_url = f"https://api.weixin.qq.com/cgi-bin/message/mass/sendall?access_token={token}"
            send_data = {
                "filter": {"is_to_all": True},
                "mpnews": {"media_id": media_id},
                "msgtype": "mpnews"
            }
            res = requests.post(send_url, json=send_data).json()
            if res.get("errcode") == 0:
                self.log("✅ 公众号发布成功！")
            else:
                self.log(f"❌ 发布失败：{res}")
        except Exception as e:
            self.log(f"发布异常：{str(e)}")

    def publish_now_thread(self):
        threading.Thread(target=self.publish_to_wechat, daemon=True).start()

    def schedule_job(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def set_schedule(self):
        t = self.publish_time.get().strip()
        try:
            schedule.every().day.at(t.split(" ")[1]).do(self.publish_to_wechat)
            self.log(f"定时已设置：每天 {t.split(' ')[1]} 自动发布")
            threading.Thread(target=self.schedule_job, daemon=True).start()
        except:
            self.log("时间格式错误，例：2026-03-29 08:30")

if __name__ == "__main__":
    root = tk.Tk()
    app = WaterAutoPublishTool(root)
    root.mainloop()