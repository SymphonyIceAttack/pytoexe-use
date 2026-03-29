# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import schedule
import time
import threading
import queue  # 用于线程间通信，避免GUI线程安全问题

class WaterAutoPublishTool:
    def __init__(self, root):
        self.root = root
        self.root.title("水利行业·多网站抓取→AI推文→定时发公众号 V2.0")
        self.root.geometry("1000x900")
        self.root.resizable(False, False)

        # 线程通信队列（用于子线程向主线程传递日志信息）
        self.log_queue = queue.Queue()
        self.root.after(100, self.process_log_queue)  # 定时处理日志队列

        # 1. 抓取网站
        ttk.Label(root, text="【1】抓取网站（一行一个网址）").place(x=20, y=10)
        self.url_text = scrolledtext.ScrolledText(root, width=120, height=4)
        self.url_text.place(x=20, y=35)

        # 2. 关键词 + 时间
        ttk.Label(root, text="关键词（空格分隔）").place(x=20, y=110)
        self.key_entry = ttk.Entry(root, width=40)
        self.key_entry.place(x=140, y=110)

        ttk.Label(root, text="开始日期：（YYYY-MM-DD）").place(x=450, y=110)
        self.start_entry = ttk.Entry(root, width=15)
        self.start_entry.place(x=510, y=110)
        self.start_entry.insert(0, (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))  # 默认昨天

        ttk.Label(root, text="结束日期：（YYYY-MM-DD）").place(x=630, y=110)
        self.end_entry = ttk.Entry(root, width=15)
        self.end_entry.place(x=690, y=110)
        self.end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))  # 默认今天

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
        self.schedule_thread = None  # 避免重复创建定时线程

    # 处理日志队列（主线程执行）
    def process_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            now = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{now}] {msg}\n")
            self.log_text.see(tk.END)
        self.root.after(100, self.process_log_queue)

    # 日志封装（子线程调用，仅向队列放数据）
    def log(self, msg):
        self.log_queue.put(msg)

    # 日期格式校验
    def validate_date(self, date_str, format="%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, format)
        except ValueError:
            return None

    # 时间格式校验（含日期+时间）
    def validate_datetime(self, dt_str, format="%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, format)
        except ValueError:
            return None

    def crawl_data(self):
        # 1. 输入校验
        urls = [u.strip() for u in self.url_text.get(1.0, tk.END).splitlines() if u.strip()]
        if not urls:
            self.log("错误：未填写抓取网址！")
            return
        
        keys = self.key_entry.get().strip().split()
        if not keys:
            self.log("警告：未填写关键词，将抓取全部内容！")
        
        # 2. 日期校验
        start_dt_str = self.start_entry.get().strip()
        end_dt_str = self.end_entry.get().strip()
        start_dt = self.validate_date(start_dt_str)
        end_dt = self.validate_date(end_dt_str)
        if not start_dt or not end_dt:
            self.log(f"错误：日期格式无效！请填写 YYYY-MM-DD 格式（当前：开始={start_dt_str}，结束={end_dt_str}）")
            return

        res = []
        self.log(f"开始抓取 {len(urls)} 个网站，关键词：{keys}，日期范围：{start_dt_str} ~ {end_dt_str}")

        for url in urls:
            try:
                self.log(f"正在抓取：{url}")
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                r = requests.get(url, headers=headers, timeout=20)
                r.raise_for_status()  # 非200状态码抛异常
                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.find_all(["a", "li", "div"], limit=40)

                for tag in items:
                    txt = tag.get_text(strip=True)
                    if keys and not any(k in txt for k in keys):
                        continue
                    
                    # 简易日期过滤（需根据实际网站的日期格式调整，此处仅示例）
                    item_dt = None
                    # 从文本中提取日期（示例：匹配 YYYY-MM-DD 格式）
                    import re
                    date_match = re.search(r"\d{4}-\d{2}-\d{2}", txt)
                    if date_match:
                        item_dt = self.validate_date(date_match.group())
                    
                    # 若提取到日期，则校验是否在范围内；未提取到则跳过（或根据需求调整）
                    if item_dt:
                        if not (start_dt <= item_dt <= end_dt):
                            continue
                    else:
                        continue  # 无日期的内容跳过（可根据需求改为保留）

                    link = tag.get("href", "")
                    if link and not link.startswith(("http://", "https://")):
                        link = requests.compat.urljoin(url, link)  # 正确拼接URL
                    res.append(f"{txt}\n链接：{link}\n")
            except Exception as e:
                self.log(f"抓取 {url} 异常：{str(e)}")

        self.crawl_content = "\n".join(res) if res else "未抓取到符合条件的信息"
        self.log(f"抓取完成，共 {len(res)} 条有效信息")

    def start_crawl_thread(self):
        threading.Thread(target=self.crawl_data, daemon=True).start()

    def gen_article(self):
        # 输入校验
        doubao_key = self.doubao_key.get().strip()
        if not doubao_key:
            self.log("错误：未填写豆包API Key！")
            messagebox.showwarning("提示", "请填写豆包API Key")
            return
        if not self.crawl_content:
            self.log("错误：未抓取到数据，无法生成文章！")
            messagebox.showwarning("提示", "请先抓取数据")
            return
        
        fanwen_content = self.fanwen_text.get(1.0, tk.END).strip()
        if not fanwen_content:
            fanwen_content = "简洁专业，符合水利行业公众号风格，标题包含当日日期，结尾标注信息来源"

        self.log("正在调用豆包生成文章...")
        prompt = f"""
你是水利行业公众号编辑，请根据下面信息写一篇公众号推文。

【写作要求/范文风格】
{fanwen_content}

【今日抓取信息】
{self.crawl_content}

要求：
1. 标题包含今日日期（{datetime.now().strftime('%Y年%m月%d日')}）
2. 排版简洁专业，使用微信公众号兼容的排版（如<br>换行）
3. 直接输出正文，不要多余表情
4. 结尾标注信息来源
"""
        # 豆包API 正确地址（火山方舟版，需确认自己的模型端点）
        api = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Authorization": f"Bearer {doubao_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "doubao-lite",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            resp = requests.post(api, json=data, timeout=30)
            resp.raise_for_status()
            resp_json = resp.json()
            if "choices" not in resp_json or len(resp_json["choices"]) == 0:
                self.log("生成失败：API返回无有效内容")
                return
            self.article_content = resp_json["choices"][0]["message"]["content"]
            self.log("✅ 文章生成完成")
        except requests.exceptions.RequestException as e:
            self.log(f"生成失败：网络/API错误 - {str(e)}")
        except KeyError as e:
            self.log(f"生成失败：返回格式异常 - 缺失字段 {e}")
        except Exception as e:
            self.log(f"生成失败：未知错误 - {str(e)}")

    def gen_article_thread(self):
        threading.Thread(target=self.gen_article, daemon=True).start()

    def get_wechat_token(self, appid, secret):
        """获取微信Access Token（带异常处理）"""
        try:
            token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
            resp = requests.get(token_url, timeout=10)
            resp.raise_for_status()
            resp_json = resp.json()
            if "errcode" in resp_json and resp_json["errcode"] != 0:
                self.log(f"获取Token失败：{resp_json['errmsg']}")
                return None
            return resp_json.get("access_token")
        except Exception as e:
            self.log(f"获取Token异常：{str(e)}")
            return None

    def publish_to_wechat(self):
        # 输入校验
        if not self.article_content:
            self.log("错误：无文章内容，取消发布")
            messagebox.showwarning("提示", "无文章内容，请先生成文章")
            return
        
        appid = self.wx_appid.get().strip()
        secret = self.wx_secret.get().strip()
        if not appid or not secret:
            self.log("错误：未填写微信AppID/Secret！")
            messagebox.showwarning("提示", "请填写微信AppID和AppSecret")
            return

        try:
            self.log("正在发布至公众号...")
            # 1. 获取Token
            token = self.get_wechat_token(appid, secret)
            if not token:
                return

            # 2. 上传临时图文素材（永久素材需权限，临时素材更适合测试）
            news = {
                "articles": [
                    {
                        "title": f"水利行业招标汇总 {datetime.now().strftime('%m月%d日')}",
                        "content": self.article_content.replace("\n", "<br>"),
                        "show_cover_pic": 0,
                        "author": "水利助手",
                        "digest": "水利行业最新资讯汇总"
                    }
                ]
            }
            # 临时素材接口（media/upload/news）
            up_url = f"https://api.weixin.qq.com/cgi-bin/media/upload/news?access_token={token}"
            up_resp = requests.post(up_url, json=news, timeout=20)
            up_resp.raise_for_status()
            up_json = up_resp.json()
            if "errcode" in up_json and up_json["errcode"] != 0:
                self.log(f"上传素材失败：{up_json['errmsg']}")
                return
            media_id = up_json.get("media_id")
            if not media_id:
                self.log("上传素材失败：未返回media_id")
                return

            # 3. 群发（仅测试，注意：普通订阅号无群发权限，需改用预览接口）
            send_url = f"https://api.weixin.qq.com/cgi-bin/message/mass/sendall?access_token={token}"
            send_data = {
                "filter": {"is_to_all": False, "tag_id": 1},  # 改为指定标签，避免群发全部
                "mpnews": {"media_id": media_id},
                "msgtype": "mpnews",
                "send_ignore_reprint": 0
            }
            send_resp = requests.post(send_url, json=send_data, timeout=20)
            send_resp.raise_for_status()
            send_json = send_resp.json()
            if send_json.get("errcode") == 0:
                self.log("✅ 公众号发布成功！")
            else:
                self.log(f"❌ 发布失败：{send_json['errmsg']}")
                # 提示权限问题
                if "api unauthorized" in send_json['errmsg']:
                    self.log("提示：普通订阅号无群发权限，请改用预览接口或升级账号权限")
        except requests.exceptions.RequestException as e:
            self.log(f"发布异常：网络错误 - {str(e)}")
        except KeyError as e:
            self.log(f"发布异常：返回格式错误 - 缺失字段 {e}")
        except Exception as e:
            self.log(f"发布异常：未知错误 - {str(e)}")

    def publish_now_thread(self):
        threading.Thread(target=self.publish_to_wechat, daemon=True).start()

    def schedule_job_wrapper(self):
        """定时任务包装器（仅执行一次指定日期的任务）"""
        self.publish_to_wechat()
        # 执行后清除定时任务
        schedule.clear()

    def set_schedule(self):
        # 输入校验
        t_str = self.publish_time.get().strip()
        publish_dt = self.validate_datetime(t_str)
        if not publish_dt:
            self.log("错误：时间格式无效！请填写 YYYY-MM-DD HH:MM 格式（例：2026-03-29 08:30）")
            messagebox.showwarning("提示", "时间格式错误！请填写 YYYY-MM-DD HH:MM")
            return
        
        # 检查是否已过时间
        now = datetime.now()
        if publish_dt < now:
            self.log("错误：指定时间已过期！")
            messagebox.showwarning("提示", "指定时间已过期，请选择未来的时间")
            return

        # 清除原有定时任务，避免重复
        schedule.clear()
        # 设置一次性定时任务（按指定日期执行）
        delay_seconds = (publish_dt - now).total_seconds()
        schedule.every(delay_seconds).seconds.do(self.schedule_job_wrapper)

        # 启动定时线程（仅启动一次）
        if not self.schedule_thread or not self.schedule_thread.is_alive():
            self.schedule_thread = threading.Thread(target=self.schedule_runner, daemon=True)
            self.schedule_thread.start()

        self.log(f"✅ 定时任务已设置：{t_str} 执行发布（延迟 {int(delay_seconds)} 秒）")

    def schedule_runner(self):
        """定时任务执行器（单线程）"""
        while True:
            schedule.run_pending()
            time.sleep(1)
            # 无任务时退出
            if not schedule.jobs:
                self.log("定时任务队列已空，停止定时线程")
                break

if __name__ == "__main__":
    # 检查依赖
    try:
        import requests
        from bs4 import BeautifulSoup
        import schedule
    except ImportError as e:
        print(f"缺少依赖库：{e}，请执行安装命令：")
        print("pip install requests beautifulsoup4 schedule")
        exit(1)

    root = tk.Tk()
    app = WaterAutoPublishTool(root)
    root.mainloop()