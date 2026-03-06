import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
import pandas as pd
import numpy as np
import threading
import time
import logging
from datetime import datetime
from PIL import Image, ImageTk
import os

# -------------------------- 全局配置 --------------------------
# 日志保存路径
LOG_FILE = "chat_bot_log.csv"
# 工作状态标识（True=运行中，False=暂停/未运行）
WORK_STATUS = False
# API连接状态
API_CONNECTED = False
# B站Cookie缓存
BILIBILI_COOKIE = ""
# DeepSeek API配置
DEEPSEEK_CONFIG = {
    "api_key": "",
    "model": "",
    "base_url": "https://api.deepseek.com/v1/chat/completions"
}

# -------------------------- 日志配置 --------------------------
# 初始化日志文件（pandas）
def init_log_file():
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame(columns=["时间", "类型", "内容"])
        df.to_csv(LOG_FILE, index=False, encoding="utf-8")

# 日志写入函数（同时更新UI和文件）
def log_message(log_text_widget, log_type, content):
    # 格式化时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 日志内容
    log_content = f"[{now}] [{log_type}] {content}"
    # 更新UI文本框
    log_text_widget.insert(END, log_content + "\n")
    log_text_widget.see(END)  # 自动滚动到最后
    # 写入CSV文件
    new_log = pd.DataFrame([[now, log_type, content]], columns=["时间", "类型", "内容"])
    new_log.to_csv(LOG_FILE, mode="a", header=False, index=False, encoding="utf-8")

# -------------------------- 核心功能 --------------------------
# 验证DeepSeek API连接
def check_api_connection(api_key, model, log_widget):
    global API_CONNECTED
    if not api_key or not model:
        log_message(log_widget, "错误", "API密钥或模型不能为空！")
        return False
    # 测试请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "测试连接"}]
    }
    try:
        response = requests.post(DEEPSEEK_CONFIG["base_url"], headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            API_CONNECTED = True
            log_message(log_widget, "成功", f"API连接成功！模型：{model}")
            return True
        else:
            log_message(log_widget, "错误", f"API连接失败：{response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(log_widget, "错误", f"API连接异常：{str(e)}")
        return False

# 生成AI回复
def generate_reply(comment_content, api_key, model):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个B站评论回复助手，回复要友好、简洁，符合B站用户交流风格。"},
            {"role": "user", "content": f"请回复这条B站评论：{comment_content}"}
        ]
    }
    try:
        response = requests.post(DEEPSEEK_CONFIG["base_url"], headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"回复生成失败：{response.status_code}"
    except Exception as e:
        return f"回复生成异常：{str(e)}"

# 模拟B站评论监控（实际需替换为真实B站API）
def monitor_bilibili_comments(log_widget, root):
    global WORK_STATUS, BILIBILI_COOKIE
    # 频率控制：随机间隔（10-30秒），用numpy生成
    interval = np.random.uniform(10, 30)
    log_message(log_widget, "信息", f"开始监控B站评论，检查间隔：{interval:.1f}秒")
    
    while WORK_STATUS:
        if not BILIBILI_COOKIE:
            log_message(log_widget, "警告", "B站Cookie未填写，跳过本次监控")
            time.sleep(interval)
            continue
        if not API_CONNECTED:
            log_message(log_widget, "警告", "API未连接，跳过本次监控")
            time.sleep(interval)
            continue
        
        # 模拟获取评论（实际需调用B站评论API）
        try:
            # 此处替换为真实B站评论接口
            test_comments = [
                {"id": f"test_{int(time.time())}", "content": "这个视频太赞了！"},
                {"id": f"test_{int(time.time())+1}", "content": "求教程，UP主辛苦了！"}
            ]
            for comment in test_comments:
                if not WORK_STATUS:
                    break
                log_message(log_widget, "信息", f"发现新评论：{comment['content']}")
                # 生成回复
                reply = generate_reply(comment["content"], DEEPSEEK_CONFIG["api_key"], DEEPSEEK_CONFIG["model"])
                log_message(log_widget, "回复", f"生成回复：{reply}")
                # 模拟发送回复（实际需调用B站回复API）
                log_message(log_widget, "成功", f"回复评论 {comment['id']} 完成")
        except Exception as e:
            log_message(log_widget, "错误", f"监控评论异常：{str(e)}")
        
        # 频率控制：等待下一次检查
        time.sleep(interval)
    
    log_message(log_widget, "信息", "B站评论监控已暂停/停止")

# -------------------------- 界面开发 --------------------------
# 启动界面
class StartWindow:
    def __init__(self):
        self.root = ttk.Window(themename="superhero")
        self.root.title("B站评论回复机器人 - 启动")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        self.root.center_window()  # 居中
        
        # 加载背景图片（可选，需提前准备图片）
        try:
            self.bg_image = Image.open("start_bg.png")  # 替换为你的图片路径
            self.bg_image = self.bg_image.resize((400, 300), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(self.bg_image)
            self.bg_label = ttk.Label(self.root, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except:
            # 无图片时设置背景色
            self.root.configure(bg="#2c3e50")
        
        # 标题
        title_label = ttk.Label(
            self.root, 
            text="B站评论自动回复机器人", 
            font=("微软雅黑", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=50)
        
        # 按钮框架
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        # 启动按钮
        start_btn = ttk.Button(
            btn_frame,
            text="启动程序",
            command=self.open_main_window,
            bootstyle="success",
            width=15
        )
        start_btn.grid(row=0, column=0, padx=10)
        
        # 退出按钮
        exit_btn = ttk.Button(
            btn_frame,
            text="退出程序",
            command=self.root.quit,
            bootstyle="danger",
            width=15
        )
        exit_btn.grid(row=0, column=1, padx=10)
        
        self.root.mainloop()
    
    def open_main_window(self):
        self.root.destroy()  # 关闭启动界面
        MainWindow()  # 打开主界面

# 主界面
class MainWindow:
    def __init__(self):
        self.root = ttk.Window(themename="superhero")
        self.root.title("chat - B站评论回复机器人")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.center_window()
        
        # 初始化日志文件
        init_log_file()
        
        # -------------------------- 标题栏 --------------------------
        title_label = ttk.Label(
            self.root,
            text="chat",
            font=("微软雅黑", 20, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=10)
        
        # -------------------------- API配置区 --------------------------
        api_frame = ttk.LabelFrame(self.root, text="API配置", bootstyle="info")
        api_frame.pack(fill=X, padx=20, pady=5)
        
        # API密钥输入
        ttk.Label(api_frame, text="DeepSeek API密钥：").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.api_entry = ttk.Entry(api_frame, width=50)
        self.api_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 模型选择
        ttk.Label(api_frame, text="模型选择：").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.model_var = tk.StringVar(value="deepseek-chat")
        self.model_combobox = ttk.Combobox(
            api_frame,
            textvariable=self.model_var,
            values=["deepseek-chat", "deepseek-coder", "deepseek-llm-7b-chat"],
            width=15
        )
        self.model_combobox.grid(row=0, column=3, padx=5, pady=5)
        
        # 连接按钮
        self.connect_btn = ttk.Button(
            api_frame,
            text="连接API",
            command=self.connect_api,
            bootstyle="primary"
        )
        self.connect_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # -------------------------- B站Cookie配置区 --------------------------
        cookie_frame = ttk.LabelFrame(self.root, text="B站Cookie配置", bootstyle="info")
        cookie_frame.pack(fill=X, padx=20, pady=5)
        
        ttk.Label(cookie_frame, text="B站Cookie（多行）：").grid(row=0, column=0, padx=5, pady=5, sticky=NW)
        self.cookie_text = ttk.Text(cookie_frame, width=70, height=3)
        self.cookie_text.grid(row=0, column=1, padx=5, pady=5)
        
        # -------------------------- 日志区 --------------------------
        log_frame = ttk.LabelFrame(self.root, text="日志记录", bootstyle="info")
        log_frame.pack(fill=BOTH, expand=True, padx=20, pady=5)
        
        # 日志文本框
        self.log_text = ttk.Text(log_frame, width=80, height=15)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)
        
        # 滚动条
        log_scroll = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_text.yview)
        log_scroll.pack(side=RIGHT, fill=Y, padx=5, pady=5)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        # -------------------------- 功能按钮区 --------------------------
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=X, padx=20, pady=10)
        
        # 开始工作按钮
        self.start_btn = ttk.Button(
            btn_frame,
            text="开始工作",
            command=self.start_working,
            bootstyle="success",
            width=15
        )
        self.start_btn.grid(row=0, column=0, padx=10)
        
        # 暂停工作按钮
        self.pause_btn = ttk.Button(
            btn_frame,
            text="暂停工作",
            command=self.pause_working,
            bootstyle="warning",
            width=15,
            state=DISABLED
        )
        self.pause_btn.grid(row=0, column=1, padx=10)
        
        # 初始化日志
        log_message(self.log_text, "信息", "程序启动完成，等待配置API和Cookie")
        
        self.root.mainloop()
    
    # 连接API按钮事件
    def connect_api(self):
        api_key = self.api_entry.get().strip()
        model = self.model_var.get().strip()
        DEEPSEEK_CONFIG["api_key"] = api_key
        DEEPSEEK_CONFIG["model"] = model
        check_api_connection(api_key, model, self.log_text)
    
    # 开始工作按钮事件
    def start_working(self):
        global WORK_STATUS, BILIBILI_COOKIE
        if not API_CONNECTED:
            log_message(self.log_text, "错误", "请先成功连接API！")
            return
        # 获取Cookie
        BILIBILI_COOKIE = self.cookie_text.get("1.0", END).strip()
        if not BILIBILI_COOKIE:
            log_message(self.log_text, "警告", "B站Cookie未填写，仍可启动但无法监控评论")
        
        # 更新工作状态
        WORK_STATUS = True
        self.start_btn.config(state=DISABLED)
        self.pause_btn.config(state=NORMAL)
        
        # 启动监控线程（避免阻塞UI）
        monitor_thread = threading.Thread(target=monitor_bilibili_comments, args=(self.log_text, self.root))
        monitor_thread.daemon = True  # 主线程退出时子线程也退出
        monitor_thread.start()
    
    # 暂停工作按钮事件
    def pause_working(self):
        global WORK_STATUS
        WORK_STATUS = False
        self.start_btn.config(state=NORMAL)
        self.pause_btn.config(state=DISABLED)
        log_message(self.log_text, "信息", "已暂停工作，点击「开始工作」恢复")

# -------------------------- 程序入口 --------------------------
if __name__ == "__main__":
    # 初始化全局状态
    WORK_STATUS = False
    API_CONNECTED = False
    # 启动程序
    StartWindow()