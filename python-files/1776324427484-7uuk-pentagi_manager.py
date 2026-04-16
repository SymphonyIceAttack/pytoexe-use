import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
import threading
import json
from datetime import datetime
import ssl
from requests.adapters import HTTPAdapter
import random

# 禁用SSL警告
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SSLAdapter(HTTPAdapter):
    """忽略SSL证书验证的适配器"""

    def init_poolmanager(self, *args, **kwargs):
        kwargs['cert_reqs'] = ssl.CERT_NONE
        kwargs['assert_hostname'] = False
        super().init_poolmanager(*args, **kwargs)


class CyberStyle:
    """赛博风格样式定义"""

    # 颜色方案
    BG_DARK = "#0a0a0f"
    BG_MEDIUM = "#0f0f1a"
    BG_LIGHT = "#1a1a2e"

    CYAN = "#00ffcc"
    CYAN_DARK = "#00b3aa"
    MAGENTA = "#ff00cc"
    MAGENTA_DARK = "#cc00aa"
    PURPLE = "#7b2eda"
    PURPLE_LIGHT = "#9b4dff"
    GREEN = "#00ff66"
    RED = "#ff3366"
    YELLOW = "#ffcc00"
    ORANGE = "#ff6600"

    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#a0a0b0"
    TEXT_DIM = "#606070"

    # 字体配置
    TITLE_FONT = ("Courier New", 16, "bold")
    HEADING_FONT = ("Courier New", 12, "bold")
    BODY_FONT = ("Consolas", 10)
    SMALL_FONT = ("Consolas", 9)
    BUTTON_FONT = ("Courier New", 10, "bold")
    MONO_FONT = ("Consolas", 10)

    @classmethod
    def apply_style(cls):
        """应用全局样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置各种组件样式
        style.configure('Cyber.TFrame', background=cls.BG_DARK)
        style.configure('CyberDark.TFrame', background=cls.BG_MEDIUM)
        style.configure('Cyber.TLabel', background=cls.BG_DARK, foreground=cls.CYAN, font=cls.BODY_FONT)
        style.configure('CyberHeading.TLabel', background=cls.BG_DARK, foreground=cls.MAGENTA, font=cls.HEADING_FONT)
        style.configure('CyberTitle.TLabel', background=cls.BG_DARK, foreground=cls.CYAN, font=cls.TITLE_FONT)

        # Button样式
        style.configure('Cyber.TButton',
                        background=cls.BG_LIGHT,
                        foreground=cls.CYAN,
                        borderwidth=1,
                        focusthickness=0,
                        font=cls.BUTTON_FONT)
        style.map('Cyber.TButton',
                  background=[('active', cls.PURPLE), ('pressed', cls.PURPLE_LIGHT)],
                  foreground=[('active', cls.TEXT_PRIMARY)])

        # Entry样式
        style.configure('Cyber.TEntry',
                        fieldbackground=cls.BG_MEDIUM,
                        foreground=cls.CYAN,
                        borderwidth=1,
                        font=cls.BODY_FONT)

        # Treeview样式
        style.configure('Cyber.Treeview',
                        background=cls.BG_MEDIUM,
                        foreground=cls.TEXT_PRIMARY,
                        fieldbackground=cls.BG_MEDIUM,
                        borderwidth=0,
                        font=cls.SMALL_FONT)
        style.map('Cyber.Treeview',
                  background=[('selected', cls.PURPLE)],
                  foreground=[('selected', cls.TEXT_PRIMARY)])

        # Notebook样式
        style.configure('Cyber.TNotebook', background=cls.BG_DARK, borderwidth=0)
        style.configure('Cyber.TNotebook.Tab',
                        background=cls.BG_LIGHT,
                        foreground=cls.TEXT_SECONDARY,
                        padding=[10, 5],
                        font=cls.BODY_FONT)
        style.map('Cyber.TNotebook.Tab',
                  background=[('selected', cls.PURPLE)],
                  foreground=[('selected', cls.CYAN)])

        # LabelFrame样式
        style.configure('Cyber.TLabelframe',
                        background=cls.BG_MEDIUM,
                        foreground=cls.CYAN,
                        borderwidth=2,
                        relief=tk.GROOVE)
        style.configure('Cyber.TLabelframe.Label',
                        background=cls.BG_MEDIUM,
                        foreground=cls.MAGENTA,
                        font=cls.HEADING_FONT)


class PentAGIClient:
    def __init__(self, root):
        self.root = root
        self.root.title("PentAGI - 渗透测试智能体客户端")
        self.root.geometry("1400x900")
        self.root.configure(bg=CyberStyle.BG_DARK)

        # 设置窗口图标（如果可用）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass

        # API配置 - 默认值
        self.api_base = "https://192.168.150.128:8443/api/v1"
        self.restart_api_base = "http://192.168.150.128:8444"  # 重启服务端口
        self.verify_ssl = False
        self.token = None
        self.refresh_job = None
        self.auto_refresh = True
        self.refresh_interval = 10
        self.current_flow_id = None

        self.restart_fixed_token = "pentagi-restart-2024-secret-key"

        # 动画相关
        self.glitch_animation = True
        self.glitch_jobs = []

        # 运行标志位（用于防止重启后控件已销毁时继续更新UI）
        self.is_running = True
        self.pending_after_jobs = []

        # 创建带SSL忽略的Session
        self.session = requests.Session()
        adapter = SSLAdapter()
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # 状态栏变量
        self.status_bar = None
        self.grid_canvas = None

        # 应用样式
        CyberStyle.apply_style()

        # 登录界面
        self.show_login()

    def safe_after(self, delay, func, *args):
        """安全的after调用，记录任务ID"""
        try:
            job_id = self.root.after(delay, func, *args)
            self.pending_after_jobs.append(job_id)
            return job_id
        except:
            return None

    def cancel_all_after_jobs(self):
        """取消所有待执行的after任务"""
        for job_id in self.pending_after_jobs:
            try:
                self.root.after_cancel(job_id)
            except:
                pass
        self.pending_after_jobs.clear()

    def create_glitch_label(self, parent, text, size=20):
        """创建故障风格标签"""
        label = tk.Label(parent, text=text,
                         font=("Courier New", size, "bold"),
                         bg=CyberStyle.BG_DARK,
                         fg=CyberStyle.CYAN)

        # 添加故障动画效果
        def glitch_effect():
            if hasattr(self, 'glitch_animation') and self.glitch_animation and self.is_running:
                colors = [CyberStyle.CYAN, CyberStyle.MAGENTA, CyberStyle.GREEN, CyberStyle.YELLOW]
                if random.random() < 0.1:  # 10%概率产生故障效果
                    try:
                        original_text = label.cget('text')
                        label.config(fg=random.choice(colors))
                        if random.random() < 0.05:
                            glitched = ''.join([c if random.random() > 0.05 else '█' for c in original_text])
                            label.config(text=glitched)
                            self.root.after(150, lambda: label.config(text=original_text, fg=CyberStyle.CYAN))
                    except:
                        pass
                job_id = self.root.after(5000, glitch_effect)  # 每5秒检查一次
                self.glitch_jobs.append(job_id)

        self.root.after(1000, glitch_effect)
        return label

    def show_login(self):
        """显示登录界面 - 赛博风格"""
        # 重置运行标志
        self.is_running = True
        self.cancel_all_after_jobs()

        self.clear_window()

        # 背景框架
        main_frame = tk.Frame(self.root, bg=CyberStyle.BG_DARK)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # 装饰性网格线（模拟矩阵效果）
        self.create_grid_overlay(main_frame)

        # 登录卡片 - 使用Frame而不是LabelFrame以获得更好控制
        login_card = tk.Frame(main_frame, bg=CyberStyle.BG_MEDIUM,
                              highlightbackground=CyberStyle.CYAN,
                              highlightcolor=CyberStyle.CYAN,
                              highlightthickness=1)
        login_card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=500, height=450)

        # 标题区域
        title_frame = tk.Frame(login_card, bg=CyberStyle.BG_MEDIUM)
        title_frame.pack(fill=tk.X, pady=30)

        # 故障风格标题
        title_label = self.create_glitch_label(title_frame, ">_ PENTAGI", 28)
        title_label.pack()

        subtitle = tk.Label(title_frame, text="渗透测试智能体管理系统",
                            font=("Consolas", 10),
                            bg=CyberStyle.BG_MEDIUM,
                            fg=CyberStyle.TEXT_DIM)
        subtitle.pack(pady=5)

        # 分隔线
        separator = tk.Frame(login_card, height=2, bg=CyberStyle.CYAN)
        separator.pack(fill=tk.X, padx=40, pady=10)

        # 表单区域
        form_frame = tk.Frame(login_card, bg=CyberStyle.BG_MEDIUM)
        form_frame.pack(pady=30)

        # API地址
        tk.Label(form_frame, text="[ API 终端 ]",
                 font=("Consolas", 10),
                 bg=CyberStyle.BG_MEDIUM,
                 fg=CyberStyle.MAGENTA).grid(row=0, column=0, sticky=tk.W, pady=10)

        self.api_entry = tk.Entry(form_frame, width=40, font=("Consolas", 10),
                                  bg=CyberStyle.BG_DARK, fg=CyberStyle.CYAN,
                                  insertbackground=CyberStyle.CYAN,
                                  relief=tk.FLAT, highlightthickness=1,
                                  highlightcolor=CyberStyle.CYAN,
                                  highlightbackground=CyberStyle.CYAN)
        self.api_entry.grid(row=0, column=1, padx=15, pady=10)
        self.api_entry.insert(0, self.api_base)

        # 邮箱
        tk.Label(form_frame, text="[ 用户标识 ]",
                 font=("Consolas", 10),
                 bg=CyberStyle.BG_MEDIUM,
                 fg=CyberStyle.MAGENTA).grid(row=1, column=0, sticky=tk.W, pady=10)

        self.email_entry = tk.Entry(form_frame, width=40, font=("Consolas", 10),
                                    bg=CyberStyle.BG_DARK, fg=CyberStyle.CYAN,
                                    insertbackground=CyberStyle.CYAN,
                                    relief=tk.FLAT, highlightthickness=1,
                                    highlightcolor=CyberStyle.CYAN,
                                    highlightbackground=CyberStyle.CYAN)
        self.email_entry.grid(row=1, column=1, padx=15, pady=10)

        # 密码
        tk.Label(form_frame, text="[ 安全凭证 ]",
                 font=("Consolas", 10),
                 bg=CyberStyle.BG_MEDIUM,
                 fg=CyberStyle.MAGENTA).grid(row=2, column=0, sticky=tk.W, pady=10)

        self.password_entry = tk.Entry(form_frame, width=40, show="•", font=("Consolas", 10),
                                       bg=CyberStyle.BG_DARK, fg=CyberStyle.CYAN,
                                       insertbackground=CyberStyle.CYAN,
                                       relief=tk.FLAT, highlightthickness=1,
                                       highlightcolor=CyberStyle.CYAN,
                                       highlightbackground=CyberStyle.CYAN)
        self.password_entry.grid(row=2, column=1, padx=15, pady=10)

        # 登录按钮
        login_btn = tk.Button(login_card, text="[ 身份验证 ]",
                              command=self.login,
                              font=("Courier New", 12, "bold"),
                              bg=CyberStyle.PURPLE, fg=CyberStyle.TEXT_PRIMARY,
                              activebackground=CyberStyle.PURPLE_LIGHT,
                              activeforeground=CyberStyle.CYAN,
                              relief=tk.FLAT, cursor="hand2",
                              padx=30, pady=10, bd=0)
        login_btn.pack(pady=30)

        # 按Enter键登录
        self.password_entry.bind("<Return>", lambda e: self.login())

        # 底部提示
        footer = tk.Label(login_card, text="© 2026 PentAGI | 安全渗透测试框架",
                          font=("Consolas", 8),
                          bg=CyberStyle.BG_MEDIUM,
                          fg=CyberStyle.TEXT_DIM)
        footer.pack(side=tk.BOTTOM, pady=10)

        # 状态栏
        self.status_bar = tk.Label(self.root, text="系统就绪 >_",
                                   relief=tk.FLAT, anchor=tk.W,
                                   bg=CyberStyle.BG_MEDIUM,
                                   fg=CyberStyle.CYAN,
                                   font=("Consolas", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_grid_overlay(self, parent):
        """创建网格叠加层（装饰效果）"""
        self.grid_canvas = tk.Canvas(parent, bg=CyberStyle.BG_DARK, highlightthickness=0)
        self.grid_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # 获取窗口大小
        def draw_grid(event=None):
            if not self.is_running:
                return
            try:
                self.grid_canvas.delete("all")
                width = self.grid_canvas.winfo_width()
                height = self.grid_canvas.winfo_height()

                if width <= 1 or height <= 1:
                    return

                # 绘制网格线
                for i in range(0, width, 50):
                    self.grid_canvas.create_line(i, 0, i, height, fill="#0a1a1a", width=1)
                for i in range(0, height, 50):
                    self.grid_canvas.create_line(0, i, width, i, fill="#0a1a1a", width=1)

                # 添加一些随机的"代码"点（使用更深的颜色，不带透明度）
                for _ in range(100):
                    x = random.randint(0, max(1, width - 10))
                    y = random.randint(0, max(1, height - 10))
                    self.grid_canvas.create_text(x, y, text=random.choice(["0", "1"]),
                                                 fill="#003333", font=("Consolas", 8))
            except:
                pass

        # 绑定配置事件
        self.grid_canvas.bind("<Configure>", draw_grid)
        self.root.after(100, draw_grid)

    def login(self):
        """执行登录"""
        # 从API地址中提取IP和端口，用于重启服务
        import re
        match = re.search(r'https?://([^:]+):?(\d+)?', self.api_entry.get().strip())
        if match:
            ip = match.group(1)
            self.restart_api_base = f"http://{ip}:8444"

        self.api_base = self.api_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("错误", "请输入用户标识和安全凭证")
            return

        if not self.api_base:
            messagebox.showerror("错误", "请输入API终端地址")
            return

        self.update_status("正在建立安全连接...")

        def do_login():
            try:
                response = self.session.post(
                    f"{self.api_base}/auth/login",
                    json={"mail": email, "password": password},
                    timeout=15,
                    verify=self.verify_ssl
                )

                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get('data', {}).get('token', None)
                    if not self.token:
                        self.token = self.session.cookies.get('token', 'logged_in')

                    self.root.after(0, self.show_main_interface)
                else:
                    error_msg = response.json().get('msg', '认证失败')
                    self.root.after(0, lambda: messagebox.showerror("错误", f"认证失败: {error_msg}"))
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"连接失败: {str(e)}\n请检查API地址是否正确"))
            finally:
                self.root.after(0, lambda: self.update_status("系统就绪 >_"))

        threading.Thread(target=do_login, daemon=True).start()

    def restart_backend_service(self):
        """重启后端服务"""
        # 确认对话框
        if not messagebox.askyesno("确认重启",
                                   "⚠️ 警告：重启服务将中断当前所有运行中的任务！\n\n"
                                   "确定要重启 PentAGI 后端服务吗？",
                                   icon='warning'):
            return

        self.update_status("正在发送重启命令...")
        self.add_log("=" * 60)
        self.add_log("正在请求重启后端服务...")

        def do_restart():
            try:
                FIXED_TOKEN = "pentagi-restart-2024-secret-key"

                url = f"{self.restart_api_base}/restart"
                headers = {
                    "Authorization": f"Bearer {FIXED_TOKEN}",
                    "Content-Type": "application/json"
                }

                self.add_log(f"请求地址: {url}")

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=10,
                    verify=False
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        self.add_log("重启命令发送成功")
                        self.add_log(f"响应: {result.get('message', '')}")

                        # 显示成功消息
                        self.safe_after(0, lambda: messagebox.showinfo("成功",
                                                                       f"重启命令已发送！\n\n"
                                                                       f"服务正在重启，请稍后...\n"
                                                                       f"消息: {result.get('message', '')}"))

                        # 等待服务重启完成（给服务端一些时间）
                        self.safe_after(8000, self.reconnect_after_restart)
                    else:
                        error_msg = result.get('message', '未知错误')
                        self.safe_after(0, lambda: messagebox.showerror("重启失败", f"服务返回错误: {error_msg}"))
                        self.add_log(f"重启失败: {error_msg}")
                        self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
                elif response.status_code == 401:
                    self.safe_after(0, lambda: messagebox.showerror("认证失败",
                                                                    "密钥验证失败，请检查客户端和服务端密钥配置"))
                    self.add_log("重启失败: 密钥验证失败")
                    self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
                elif response.status_code == 403:
                    self.safe_after(0, lambda: messagebox.showerror("权限不足",
                                                                    "IP地址未授权或权限不足"))
                    self.add_log("重启失败: 权限不足")
                    self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
                elif response.status_code == 429:
                    self.safe_after(0, lambda: messagebox.showerror("请求过于频繁",
                                                                    "请求过于频繁，请稍后再试"))
                    self.add_log("重启失败: 请求过于频繁")
                    self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
                else:
                    self.safe_after(0, lambda: messagebox.showerror("重启失败",
                                                                    f"请求失败，状态码: {response.status_code}\n"
                                                                    f"请检查监听服务是否正常运行"))
                    self.add_log(f"重启失败: HTTP {response.status_code}")
                    self.safe_after(0, lambda: self.update_status("系统就绪 >_"))

            except requests.exceptions.ConnectionError:
                self.safe_after(0, lambda: messagebox.showerror("连接失败",
                                                                "无法连接到重启服务端点！\n\n"))
                self.add_log("重启失败: 无法连接到重启服务端点")
                self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
            except requests.exceptions.Timeout:
                self.safe_after(0, lambda: messagebox.showerror("超时", "请求超时，请检查网络连接"))
                self.add_log("重启失败: 请求超时")
                self.safe_after(0, lambda: self.update_status("系统就绪 >_"))
            except Exception as e:
                self.safe_after(0, lambda: messagebox.showerror("错误", f"发生异常: {str(e)}"))
                self.add_log(f"重启失败: {str(e)}")
                self.safe_after(0, lambda: self.update_status("系统就绪 >_"))

        threading.Thread(target=do_restart, daemon=True).start()

    def reconnect_after_restart(self):
        """重启后重新连接并刷新数据"""
        self.add_log("=" * 60)
        self.add_log("等待服务重启完成...")
        self.update_status("等待服务重启完成...")

        def attempt_reconnect():
            try:
                self.add_log("尝试重新连接服务...")

                # 尝试调用一个简单的API来检查服务是否就绪
                url = f"{self.api_base}/flows/?page=1&pageSize=1"
                headers = {"Authorization": f"Bearer {self.token}"} if self.token and self.token != 'logged_in' else {}

                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=10,
                    verify=self.verify_ssl
                )

                if response.status_code == 200:
                    self.add_log("服务已就绪，正在刷新数据...")
                    self.safe_after(0, lambda: self.update_status("服务已就绪"))

                    # 刷新Flow列表
                    self.safe_after(0, self.refresh_flows)

                    # 显示成功消息
                    self.safe_after(0, lambda: messagebox.showinfo("成功",
                                                                   "服务重启完成！\n\n"
                                                                   "数据已自动刷新，您可以继续使用。"))
                    self.add_log("数据刷新完成")
                elif response.status_code == 401:
                    self.add_log("Token已过期，需要重新登录")
                    self.safe_after(0, lambda: messagebox.showwarning("需要重新登录",
                                                                      "服务重启后会话已过期，请重新登录。"))
                    self.safe_after(0, self.show_login)
                else:
                    self.add_log(f"服务未就绪，状态码: {response.status_code}，3秒后重试...")
                    self.safe_after(3000, attempt_reconnect)

            except requests.exceptions.RequestException as e:
                self.add_log(f"连接失败: {str(e)}，3秒后重试...")
                self.safe_after(3000, attempt_reconnect)
            except Exception as e:
                self.add_log(f"未知错误: {str(e)}，3秒后重试...")
                self.safe_after(3000, attempt_reconnect)

        # 延迟10秒后开始尝试重连（给服务端足够的启动时间）
        self.safe_after(10000, attempt_reconnect)

    def show_main_interface(self):
        """显示主界面 - 赛博风格"""
        self.is_running = True
        self.clear_window()
        self.root.configure(bg=CyberStyle.BG_DARK)

        # 主容器
        main_container = tk.Frame(self.root, bg=CyberStyle.BG_DARK)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 创建菜单栏
        menubar = tk.Menu(self.root, bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN,
                          activebackground=CyberStyle.PURPLE,
                          activeforeground=CyberStyle.TEXT_PRIMARY)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0, bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN)
        menubar.add_cascade(label="[文件]", menu=file_menu)
        file_menu.add_command(label="刷新数据", command=self.refresh_flows)
        file_menu.add_separator()
        file_menu.add_command(label="退出系统", command=self.on_exit)

        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0, bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN)
        menubar.add_cascade(label="[设置]", menu=settings_menu)
        settings_menu.add_command(label="自动刷新配置", command=self.show_auto_refresh_settings)
        settings_menu.add_command(label="API终端配置", command=self.show_api_settings)

        # 系统菜单
        system_menu = tk.Menu(menubar, tearoff=0, bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN)
        menubar.add_cascade(label="[系统]", menu=system_menu)
        system_menu.add_command(label="🔄 重启后端服务", command=self.restart_backend_service,
                                foreground=CyberStyle.RED)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0, bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN)
        menubar.add_cascade(label="[帮助]", menu=help_menu)
        help_menu.add_command(label="系统信息", command=self.show_about)

        # 顶部状态栏（霓虹效果）
        top_bar = tk.Frame(main_container, bg=CyberStyle.BG_MEDIUM, height=40)
        top_bar.pack(fill=tk.X, padx=10, pady=5)
        top_bar.pack_propagate(False)

        # 系统状态指示灯
        status_led = tk.Canvas(top_bar, width=20, height=20, bg=CyberStyle.BG_MEDIUM, highlightthickness=0)
        status_led.pack(side=tk.LEFT, padx=10)
        led = status_led.create_oval(5, 5, 15, 15, fill=CyberStyle.GREEN, outline="")

        # 闪烁效果
        def blink_led():
            if hasattr(self, 'glitch_animation') and self.glitch_animation and self.is_running:
                try:
                    current_fill = status_led.itemcget(led, "fill")
                    new_fill = CyberStyle.CYAN if current_fill == CyberStyle.GREEN else CyberStyle.GREEN
                    status_led.itemconfig(led, fill=new_fill)
                    self.root.after(1000, blink_led)
                except:
                    pass

        blink_led()

        # 标题
        title_label = tk.Label(top_bar, text="PENTAGI | 渗透测试智能体",
                               font=("Courier New", 12, "bold"),
                               bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN)
        title_label.pack(side=tk.LEFT, padx=10)

        # 工具栏
        toolbar = tk.Frame(main_container, bg=CyberStyle.BG_MEDIUM, height=45)
        toolbar.pack(fill=tk.X, padx=10, pady=5)
        toolbar.pack_propagate(False)

        # 工具栏按钮样式
        btn_style = {"font": ("Courier New", 10, "bold"), "bg": CyberStyle.PURPLE,
                     "fg": CyberStyle.TEXT_PRIMARY, "activebackground": CyberStyle.PURPLE_LIGHT,
                     "activeforeground": CyberStyle.CYAN, "relief": tk.FLAT,
                     "cursor": "hand2", "padx": 15, "pady": 5}

        tk.Button(toolbar, text="⟳ 刷新", command=self.refresh_flows, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⊕ 创建Flow", command=self.show_create_flow_dialog, **btn_style).pack(side=tk.LEFT,
                                                                                                      padx=2)
        tk.Button(toolbar, text="✓ 完成Flow", command=self.finish_flow, **btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="⊗ 删除Flow", command=self.delete_flow, **btn_style).pack(side=tk.LEFT, padx=2)

        # 分隔线
        tk.Frame(toolbar, width=2, bg=CyberStyle.TEXT_DIM).pack(side=tk.LEFT, padx=10, fill=tk.Y, pady=5)

        # 重启服务按钮（红色警告风格）
        restart_btn_style = {"font": ("Courier New", 10, "bold"), "bg": CyberStyle.RED,
                             "fg": CyberStyle.TEXT_PRIMARY, "activebackground": "#ff5555",
                             "activeforeground": CyberStyle.CYAN, "relief": tk.FLAT,
                             "cursor": "hand2", "padx": 15, "pady": 5}
        tk.Button(toolbar, text="⚡ 重启服务", command=self.restart_backend_service, **restart_btn_style).pack(
            side=tk.LEFT, padx=2)

        # 自动刷新指示器
        self.refresh_indicator = tk.Label(toolbar, text=f"⏱ 自动刷新: {self.refresh_interval}s",
                                          bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.GREEN,
                                          font=("Consolas", 9))
        self.refresh_indicator.pack(side=tk.RIGHT, padx=10)

        # 主内容区域 - PanedWindow
        main_paned = tk.PanedWindow(main_container, bg=CyberStyle.BG_DARK,
                                    sashwidth=3, sashrelief=tk.FLAT)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧面板 - Flow列表
        left_frame = tk.Frame(main_paned, bg=CyberStyle.BG_MEDIUM)
        main_paned.add(left_frame, width=500)

        # 列表标题
        list_header = tk.Frame(left_frame, bg=CyberStyle.PURPLE, height=35)
        list_header.pack(fill=tk.X)
        list_header.pack_propagate(False)

        tk.Label(list_header, text=">_ 活跃任务列表",
                 font=("Courier New", 11, "bold"),
                 bg=CyberStyle.PURPLE, fg=CyberStyle.TEXT_PRIMARY).pack(pady=8)

        # Treeview框架
        tree_frame = tk.Frame(left_frame, bg=CyberStyle.BG_MEDIUM)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建Treeview
        columns = ("ID", "标题", "状态", "模型", "创建时间")
        self.flow_tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                      style="Cyber.Treeview", height=20)

        for col in columns:
            self.flow_tree.heading(col, text=col)

        self.flow_tree.column("ID", width=60, anchor=tk.CENTER)
        self.flow_tree.column("标题", width=200)
        self.flow_tree.column("状态", width=100)
        self.flow_tree.column("模型", width=120)
        self.flow_tree.column("创建时间", width=140)

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.flow_tree.yview)
        self.flow_tree.configure(yscrollcommand=scrollbar.set)

        self.flow_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.flow_tree.bind("<<TreeviewSelect>>", self.on_flow_select)
        self.flow_tree.bind("<Double-1>", self.on_flow_double_click)

        # 右侧面板 - 详细信息
        right_frame = tk.Frame(main_paned, bg=CyberStyle.BG_MEDIUM)
        main_paned.add(right_frame, width=800)

        # Notebook样式标签页
        self.detail_notebook = ttk.Notebook(right_frame, style="Cyber.TNotebook")
        self.detail_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 基本信息标签页
        info_frame = tk.Frame(self.detail_notebook, bg=CyberStyle.BG_MEDIUM)
        self.detail_notebook.add(info_frame, text="[ 详细信息 ]")

        self.flow_info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD,
                                                        bg=CyberStyle.BG_DARK,
                                                        fg=CyberStyle.TEXT_PRIMARY,
                                                        insertbackground=CyberStyle.CYAN,
                                                        font=("Consolas", 9),
                                                        relief=tk.FLAT,
                                                        highlightthickness=0)
        self.flow_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 任务列表标签页
        tasks_frame = tk.Frame(self.detail_notebook, bg=CyberStyle.BG_MEDIUM)
        self.detail_notebook.add(tasks_frame, text="[ 任务清单 ]")

        tasks_cols = ("ID", "标题", "状态", "输入")
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=tasks_cols, show="headings",
                                       style="Cyber.Treeview", height=12)
        for col in tasks_cols:
            self.tasks_tree.heading(col, text=col)
        self.tasks_tree.column("ID", width=60, anchor=tk.CENTER)
        self.tasks_tree.column("标题", width=180)
        self.tasks_tree.column("状态", width=100)
        self.tasks_tree.column("输入", width=450)
        self.tasks_tree.pack(fill=tk.BOTH, expand=True)

        self.tasks_tree.bind("<Double-1>", self.on_task_double_click)

        # 日志标签页
        logs_frame = tk.Frame(self.detail_notebook, bg=CyberStyle.BG_MEDIUM)
        self.detail_notebook.add(logs_frame, text="[ 运行日志 ]")

        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD,
                                                   bg=CyberStyle.BG_DARK,
                                                   fg=CyberStyle.TEXT_SECONDARY,
                                                   insertbackground=CyberStyle.CYAN,
                                                   font=("Consolas", 9),
                                                   relief=tk.FLAT,
                                                   highlightthickness=0)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 清除日志按钮
        clear_btn = tk.Button(logs_frame, text="[ 清除日志 ]",
                              command=lambda: self.logs_text.delete(1.0, tk.END),
                              font=("Consolas", 9),
                              bg=CyberStyle.BG_LIGHT, fg=CyberStyle.CYAN,
                              activebackground=CyberStyle.PURPLE,
                              relief=tk.FLAT, cursor="hand2")
        clear_btn.pack(side=tk.BOTTOM, pady=5)

        # 底部状态栏
        self.status_bar = tk.Label(self.root, text="系统就绪 >_",
                                   relief=tk.FLAT, anchor=tk.W,
                                   bg=CyberStyle.BG_MEDIUM,
                                   fg=CyberStyle.CYAN,
                                   font=("Consolas", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 初始加载
        self.refresh_flows()

        # 启动自动刷新
        if self.auto_refresh:
            self.start_auto_refresh()

        # 添加欢迎日志
        self.add_log("=" * 60)
        self.add_log("PentAGI 系统已启动")
        self.add_log(f"连接终端: {self.api_base}")
        self.add_log(f"重启服务端点: {self.restart_api_base}")
        self.add_log("=" * 60)

    def make_request(self, method, endpoint, data=None):
        """发送API请求"""
        headers = {"Content-Type": "application/json"}
        if self.token and self.token != 'logged_in':
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.api_base}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=15, verify=self.verify_ssl)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=30, verify=self.verify_ssl)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=30, verify=self.verify_ssl)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=15, verify=self.verify_ssl)
            else:
                return None

            if response.status_code in (200, 201):
                return response.json()
            elif response.status_code == 401:
                self.safe_after(0, lambda: messagebox.showerror("错误", "会话已过期，请重新登录"))
                self.safe_after(0, self.show_login)
                return None
            else:
                error_msg = response.json().get('msg', f'请求失败: {response.status_code}')
                if response.status_code != 404:
                    self.safe_after(0, lambda: messagebox.showerror("错误", error_msg))
                return None
        except requests.exceptions.RequestException as e:
            self.safe_after(0, lambda: self.add_log(f"请求错误: {str(e)}"))
            return None

    def refresh_flows(self):
        """刷新Flow列表"""
        if not self.is_running:
            return

        self.update_status("正在加载任务数据...")

        def do_refresh():
            if not self.is_running:
                return

            result = self.make_request("GET", "/flows/?page=1&pageSize=100&type=init")

            if not self.is_running:
                return

            if result and result.get('status') == 'success':
                data = result.get('data', {})
                flows = data.get('flows', [])

                self.safe_after(0, lambda: self.update_flow_list(flows) if self.is_running else None)
                self.update_status(f"已加载 {len(flows)} 个任务")
                self.add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 刷新任务列表，共 {len(flows)} 个")
            else:
                self.update_status("加载失败")

        threading.Thread(target=do_refresh, daemon=True).start()

    def update_flow_list(self, flows):
        """更新Flow列表显示"""
        if not self.is_running or not hasattr(self, 'flow_tree'):
            return

        try:
            selected = None
            selection = self.flow_tree.selection()
            if selection:
                values = self.flow_tree.item(selection[0], 'values')
                if values:
                    selected = values[0]

            for item in self.flow_tree.get_children():
                self.flow_tree.delete(item)

            for flow in flows:
                status = flow.get('status', 'unknown')
                status_display = self.get_status_display(status)

                # 根据状态设置tag
                tag = 'normal'
                if status in ['running', 'executing']:
                    tag = 'running'
                elif status in ['finished', 'completed']:
                    tag = 'completed'
                elif status in ['error', 'failed']:
                    tag = 'error'

                item_id = self.flow_tree.insert("", tk.END, values=(
                    flow.get('id', ''),
                    flow.get('title', '未命名'),
                    status_display,
                    flow.get('model', 'custom'),
                    flow.get('created_at', '')[:19] if flow.get('created_at') else ''
                ), tags=(tag,))

                if selected and str(flow.get('id')) == str(selected):
                    self.flow_tree.selection_set(item_id)
                    self.current_flow_id = selected
                    self.load_flow_details(selected)

            # 配置标签颜色
            self.flow_tree.tag_configure('running', background='#1a3a2a')
            self.flow_tree.tag_configure('completed', background='#1a2a3a')
            self.flow_tree.tag_configure('error', background='#3a1a2a')
        except:
            pass

    def get_status_display(self, status):
        """获取显示用的状态文本"""
        status_lower = status.lower()
        status_map = {
            'running': '🟢 运行中',
            'executing': '🟢 执行中',
            'waiting': '🟡 等待中',
            'pending': '⏳ 等待中',
            'finished': '✅ 已完成',
            'completed': '✅ 已完成',
            'error': '❌ 错误',
            'failed': '❌ 失败',
            'stopped': '⏹️ 已停止'
        }
        return status_map.get(status_lower, f'⚪ {status}')

    def get_status_icon(self, status):
        """获取状态图标"""
        status_lower = status.lower()
        icons = {
            'running': '🔄',
            'executing': '🔄',
            'finished': '✅',
            'completed': '✅',
            'waiting': '⏳',
            'pending': '⏳',
            'created': '🆕',
            'error': '❌',
            'failed': '❌',
            'stopped': '⏹️'
        }
        return icons.get(status_lower, '⚪')

    def on_flow_select(self, event):
        """Flow选择事件"""
        if not self.is_running:
            return
        selection = self.flow_tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.flow_tree.item(item, 'values')
        if values:
            flow_id = values[0]
            self.current_flow_id = flow_id
            self.load_flow_details(flow_id)

    def on_flow_double_click(self, event):
        """双击Flow显示更多详情"""
        if not self.is_running:
            return
        selection = self.flow_tree.selection()
        if selection:
            values = self.flow_tree.item(selection[0], 'values')
            if values:
                self.show_flow_graph(values[0])

    def on_task_double_click(self, event):
        """双击任务查看详情"""
        if not self.is_running:
            return
        selection = self.tasks_tree.selection()
        if not selection:
            return

        values = self.tasks_tree.item(selection[0], 'values')
        if values and self.current_flow_id:
            task_id = values[0]
            self.load_task_details(self.current_flow_id, task_id)

    def load_task_details(self, flow_id, task_id):
        """加载任务详细信息"""
        if not self.is_running:
            return
        self.update_status(f"正在加载任务 #{task_id} 详情...")

        def do_load():
            if not self.is_running:
                return
            task_result = self.make_request("GET", f"/flows/{flow_id}/tasks/{task_id}")
            self.safe_after(0, lambda: self.show_task_details_dialog(flow_id, task_id,
                                                                     task_result) if self.is_running else None)

        threading.Thread(target=do_load, daemon=True).start()

    def show_task_details_dialog(self, flow_id, task_id, task_result):
        """显示任务详情对话框 - 赛博风格"""
        if not self.is_running:
            return
        if not task_result or task_result.get('status') != 'success':
            messagebox.showerror("错误", "无法加载任务详情")
            return

        task = task_result.get('data', {})

        dialog = tk.Toplevel(self.root)
        dialog.title(f"[ 任务详情 ] Task #{task_id}")
        dialog.geometry("900x700")
        dialog.configure(bg=CyberStyle.BG_DARK)
        dialog.transient(self.root)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        notebook = ttk.Notebook(dialog, style="Cyber.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 输入页面
        input_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(input_frame, text="[ 输入数据 ]")
        input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD,
                                               bg=CyberStyle.BG_DARK,
                                               fg=CyberStyle.TEXT_PRIMARY,
                                               font=("Consolas", 10),
                                               relief=tk.FLAT)
        input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        input_text.insert(1.0, task.get('input', '无'))
        input_text.config(state=tk.DISABLED)

        # 输出页面
        output_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(output_frame, text="[ 输出结果 ]")
        output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD,
                                                bg=CyberStyle.BG_DARK,
                                                fg=CyberStyle.CYAN,
                                                font=("Consolas", 10),
                                                relief=tk.FLAT)
        output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        output_text.insert(1.0, task.get('result', '暂无结果'))
        output_text.config(state=tk.DISABLED)

        # 子任务页面
        subtasks_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(subtasks_frame, text="[ 子任务列表 ]")

        def load_subtasks():
            if not self.is_running:
                return
            result = self.make_request("GET",
                                       f"/flows/{flow_id}/tasks/{task_id}/subtasks/?page=1&pageSize=50&type=init")
            if result and result.get('status') == 'success':
                data = result.get('data', {})
                subtasks = data.get('subtasks', [])
                self.safe_after(0, lambda: display_subtasks(subtasks) if self.is_running else None)

        def display_subtasks(subtasks):
            for widget in subtasks_frame.winfo_children():
                widget.destroy()

            tree = ttk.Treeview(subtasks_frame, columns=("ID", "标题", "状态", "结果预览"),
                                show="headings", style="Cyber.Treeview", height=15)
            tree.heading("ID", text="ID")
            tree.heading("标题", text="标题")
            tree.heading("状态", text="状态")
            tree.heading("结果预览", text="结果预览")
            tree.column("ID", width=60, anchor=tk.CENTER)
            tree.column("标题", width=200)
            tree.column("状态", width=100)
            tree.column("结果预览", width=500)
            tree.pack(fill=tk.BOTH, expand=True)

            for subtask in subtasks:
                result_preview = subtask.get('result', '')[:100] if subtask.get('result') else '等待中'
                if len(subtask.get('result', '')) > 100:
                    result_preview += '...'
                tree.insert("", tk.END, values=(
                    subtask.get('id'),
                    subtask.get('title'),
                    subtask.get('status'),
                    result_preview
                ))

            def on_subtask_double_click(event):
                if not self.is_running:
                    return
                selection = tree.selection()
                if selection:
                    values = tree.item(selection[0], 'values')
                    if values:
                        self.show_subtask_details(flow_id, task_id, values[0])

            tree.bind("<Double-1>", on_subtask_double_click)

        threading.Thread(target=load_subtasks, daemon=True).start()

    def show_subtask_details(self, flow_id, task_id, subtask_id):
        """显示子任务详情"""
        if not self.is_running:
            return

        def do_load():
            if not self.is_running:
                return
            result = self.make_request("GET", f"/flows/{flow_id}/tasks/{task_id}/subtasks/{subtask_id}")
            self.safe_after(0, lambda: self.display_subtask_details(subtask_id, result) if self.is_running else None)

        threading.Thread(target=do_load, daemon=True).start()

    def display_subtask_details(self, subtask_id, result):
        """显示子任务详情对话框 - 赛博风格"""
        if not self.is_running:
            return
        if not result or result.get('status') != 'success':
            messagebox.showerror("错误", "无法加载子任务详情")
            return

        subtask = result.get('data', {})

        dialog = tk.Toplevel(self.root)
        dialog.title(f"[ 子任务详情 ] Subtask #{subtask_id}")
        dialog.geometry("1000x800")
        dialog.configure(bg=CyberStyle.BG_DARK)

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        notebook = ttk.Notebook(dialog, style="Cyber.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 基本信息
        info_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(info_frame, text="[ 基本信息 ]")
        info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD,
                                              bg=CyberStyle.BG_DARK,
                                              fg=CyberStyle.TEXT_PRIMARY,
                                              font=("Consolas", 10),
                                              relief=tk.FLAT)
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        info_content = f"""
╔══════════════════════════════════════════════════════════════╗
║                     子任务详细信息                           ║
╠══════════════════════════════════════════════════════════════╣
║ ID:          {subtask.get('id')}
║ 标题:        {subtask.get('title')}
║ 状态:        {subtask.get('status')}
║ 描述:        {subtask.get('description', '无')}
║ 创建时间:    {subtask.get('created_at')}
║ 更新时间:    {subtask.get('updated_at')}
╚══════════════════════════════════════════════════════════════╝
"""
        info_text.insert(1.0, info_content)
        info_text.config(state=tk.DISABLED)

        # 结果页面
        result_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(result_frame, text="[ 执行结果 ]")
        result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD,
                                                bg=CyberStyle.BG_DARK,
                                                fg=CyberStyle.CYAN,
                                                font=("Consolas", 10),
                                                relief=tk.FLAT)
        result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        result_text.insert(1.0, subtask.get('result', '暂无结果'))
        result_text.config(state=tk.DISABLED)

        # 上下文
        context_frame = tk.Frame(notebook, bg=CyberStyle.BG_MEDIUM)
        notebook.add(context_frame, text="[ 上下文数据 ]")
        context_text = scrolledtext.ScrolledText(context_frame, wrap=tk.WORD,
                                                 bg=CyberStyle.BG_DARK,
                                                 fg=CyberStyle.TEXT_SECONDARY,
                                                 font=("Consolas", 10),
                                                 relief=tk.FLAT)
        context_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        context_text.insert(1.0, subtask.get('context', '无'))
        context_text.config(state=tk.DISABLED)

    def load_flow_details(self, flow_id):
        """加载Flow详细信息"""
        if not self.is_running:
            return
        self.update_status(f"正在加载任务 #{flow_id} 详情...")

        def do_load():
            if not self.is_running:
                return
            flow_result = self.make_request("GET", f"/flows/{flow_id}")
            tasks_result = self.make_request("GET", f"/flows/{flow_id}/tasks/?page=1&pageSize=50&type=init")

            self.safe_after(0, lambda: self.update_flow_details(flow_id, flow_result,
                                                                tasks_result) if self.is_running else None)

        threading.Thread(target=do_load, daemon=True).start()

    def update_flow_details(self, flow_id, flow_result, tasks_result):
        """更新Flow详情显示"""
        if not self.is_running:
            return
        # 更新基本信息
        if flow_result and flow_result.get('status') == 'success':
            flow = flow_result.get('data', {})
            info_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    Flow 详细信息                              ║
╠══════════════════════════════════════════════════════════════╣
║ ID:          {flow.get('id')}
║ 标题:        {flow.get('title')}
║ 状态:        {flow.get('status')}
║ 模型:        {flow.get('model', 'custom')}
║ 提供商:      {flow.get('model_provider_name', 'custom')}
║ 语言:        {flow.get('language', 'zh')}
║ 追踪ID:      {flow.get('trace_id')}
║ 创建时间:    {flow.get('created_at')}
║ 更新时间:    {flow.get('updated_at')}
╚══════════════════════════════════════════════════════════════╝

📦 Functions 配置:
{json.dumps(flow.get('functions', {}), indent=2, ensure_ascii=False) if flow.get('functions') else '  无'}
"""
            try:
                self.flow_info_text.delete(1.0, tk.END)
                self.flow_info_text.insert(1.0, info_text)
            except:
                pass

        # 更新任务列表
        if tasks_result and tasks_result.get('status') == 'success':
            data = tasks_result.get('data', {})
            tasks = data.get('tasks', [])

            try:
                for item in self.tasks_tree.get_children():
                    self.tasks_tree.delete(item)

                for task in tasks:
                    input_text = task.get('input', '')
                    if len(input_text) > 80:
                        input_text = input_text[:80] + '...'
                    self.tasks_tree.insert("", tk.END, values=(
                        task.get('id', ''),
                        task.get('title', ''),
                        task.get('status', ''),
                        input_text
                    ))
            except:
                pass

        self.update_status(f"任务 #{flow_id} 详情加载完成")

    def show_flow_graph(self, flow_id):
        """显示Flow图形结构"""
        if not self.is_running:
            return
        self.update_status(f"正在加载任务 #{flow_id} 结构图...")

        def do_load():
            if not self.is_running:
                return
            result = self.make_request("GET", f"/flows/{flow_id}/graph")
            self.safe_after(0, lambda: self.display_flow_graph(flow_id, result) if self.is_running else None)

        threading.Thread(target=do_load, daemon=True).start()

    def display_flow_graph(self, flow_id, result):
        """显示Flow图形 - 赛博风格"""
        if not self.is_running:
            return
        if not result or result.get('status') != 'success':
            messagebox.showerror("错误", "无法加载任务结构图")
            return

        data = result.get('data', {})

        graph_window = tk.Toplevel(self.root)
        graph_window.title(f"[ 任务结构图 ] Flow #{flow_id}")
        graph_window.geometry("1200x850")
        graph_window.configure(bg=CyberStyle.BG_DARK)

        main_frame = tk.Frame(graph_window, bg=CyberStyle.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        toolbar = tk.Frame(main_frame, bg=CyberStyle.BG_MEDIUM, height=40)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        toolbar.pack_propagate(False)

        show_detail_var = tk.BooleanVar(value=False)

        def toggle_detail():
            show_detail_var.set(not show_detail_var.get())
            refresh_display()

        btn_style = {"font": ("Courier New", 9, "bold"), "bg": CyberStyle.PURPLE,
                     "fg": CyberStyle.TEXT_PRIMARY, "activebackground": CyberStyle.PURPLE_LIGHT,
                     "relief": tk.FLAT, "cursor": "hand2", "padx": 10, "pady": 3}

        tk.Button(toolbar, text="[ 切换详细结果 ]", command=toggle_detail, **btn_style).pack(side=tk.LEFT, padx=5)

        def export_structure():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"flow_{flow_id}_structure.txt"
            )
            if file_path:
                self.export_flow_structure(file_path, flow_id, data)

        tk.Button(toolbar, text="[ 导出结构 ]", command=export_structure, **btn_style).pack(side=tk.LEFT, padx=5)

        # 文本框
        text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD,
                                              bg=CyberStyle.BG_DARK,
                                              fg=CyberStyle.TEXT_PRIMARY,
                                              font=("Consolas", 10),
                                              relief=tk.FLAT,
                                              insertbackground=CyberStyle.CYAN)
        text_area.pack(fill=tk.BOTH, expand=True)

        # 配置文本标签样式
        text_area.tag_configure("title", font=("Courier New", 13, "bold"), foreground=CyberStyle.CYAN)
        text_area.tag_configure("task", font=("Courier New", 11, "bold"), foreground=CyberStyle.MAGENTA)
        text_area.tag_configure("subtask", font=("Consolas", 10), foreground=CyberStyle.GREEN)
        text_area.tag_configure("result_title", font=("Courier New", 9, "bold"), foreground=CyberStyle.YELLOW)

        def refresh_display():
            text_area.delete(1.0, tk.END)

            # 头部
            text_area.insert(tk.END, "╔" + "═" * 88 + "╗\n", "title")
            text_area.insert(tk.END, "║" + " " * 30 + "FLOW 任务结构图" + " " * 39 + "║\n", "title")
            text_area.insert(tk.END, "╠" + "═" * 88 + "╣\n", "title")
            text_area.insert(tk.END, f"║ Flow ID: {flow_id:<78}║\n")
            text_area.insert(tk.END, f"║ 标题: {data.get('title', 'N/A'):<78}║\n")
            text_area.insert(tk.END, f"║ 状态: {data.get('status', 'N/A'):<78}║\n")
            text_area.insert(tk.END, "╚" + "═" * 88 + "╝\n\n")

            tasks = data.get('tasks', [])
            if not tasks:
                text_area.insert(tk.END, "  📭 暂无任务数据\n")
                return

            # 统计
            total_tasks = len(tasks)
            total_subtasks = sum(len(t.get('subtasks', [])) for t in tasks)
            finished_subtasks = sum(1 for t in tasks for st in t.get('subtasks', []) if st.get('status') == 'finished')

            text_area.insert(tk.END, f"📊 统计分析: {total_tasks} 个主任务, {total_subtasks} 个子任务", "task")
            if finished_subtasks > 0:
                text_area.insert(tk.END, f" (已完成: {finished_subtasks}/{total_subtasks})\n\n")
            else:
                text_area.insert(tk.END, "\n\n")

            # 显示任务树
            for idx, task in enumerate(tasks):
                task_id = task.get('id')
                task_title = task.get('title', '无标题')
                task_status = task.get('status', 'unknown')
                task_input = task.get('input', '')

                status_icon = self.get_status_icon(task_status)
                text_area.insert(tk.END, f"┌─", "task")
                text_area.insert(tk.END, f"─" * 85 + "┐\n")
                text_area.insert(tk.END, f"│ 📌 ", "task")
                text_area.insert(tk.END, f"任务 #{task_id}: ", "task")
                text_area.insert(tk.END, f"{task_title}\n", "task")
                text_area.insert(tk.END, f"│   状态: {status_icon} {task_status}\n")

                if task_input:
                    input_display = task_input[:100] + "..." if len(task_input) > 100 else task_input
                    input_display = input_display.replace("\n", " ")
                    text_area.insert(tk.END, f"│   输入: {input_display}\n")

                text_area.insert(tk.END, f"│\n")

                subtasks = task.get('subtasks', [])
                if subtasks:
                    text_area.insert(tk.END, f"│   📋 子任务清单:\n")
                    for st_idx, subtask in enumerate(subtasks):
                        st_id = subtask.get('id')
                        st_title = subtask.get('title', '无标题')
                        st_status = subtask.get('status', 'unknown')
                        st_result = subtask.get('result', '')

                        if st_idx == len(subtasks) - 1:
                            prefix = "│   └──"
                        else:
                            prefix = "│   ├──"

                        status_icon = self.get_status_icon(st_status)
                        text_area.insert(tk.END, f"{prefix} 🔹 ", "subtask")
                        text_area.insert(tk.END, f"子任务 #{st_id}: {st_title} [{status_icon} {st_status}]\n",
                                         "subtask")

                        if show_detail_var.get() and st_result:
                            text_area.insert(tk.END, f"│       📄 执行结果:\n", "result_title")
                            for line in st_result.split('\n'):
                                text_area.insert(tk.END, f"│         {line}\n")
                        elif st_result and not show_detail_var.get():
                            preview = st_result[:200].replace('\n', ' ')
                            if len(st_result) > 200:
                                preview += "..."
                            text_area.insert(tk.END, f"│       📄 结果预览: {preview}\n")

                    text_area.insert(tk.END, f"│\n")
                else:
                    text_area.insert(tk.END, f"│   └── (无子任务)\n│\n")

                text_area.insert(tk.END, f"└─" + "─" * 85 + "┘\n\n")

            text_area.see("1.0")

        refresh_display()

    def export_flow_structure(self, file_path, flow_id, data):
        """导出Flow结构到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"PentAGI - Flow #{flow_id} 任务结构图\n")
                f.write(f"标题: {data.get('title', 'N/A')}\n")
                f.write(f"状态: {data.get('status', 'N/A')}\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                tasks = data.get('tasks', [])
                for task in tasks:
                    f.write(f"\n[任务 #{task.get('id')}] {task.get('title')} [{task.get('status')}]\n")
                    f.write(f"  输入: {task.get('input', '')}\n")
                    if task.get('result'):
                        f.write(f"  输出: {task.get('result')}\n")
                    f.write(f"  {'-' * 60}\n")

                    subtasks = task.get('subtasks', [])
                    for subtask in subtasks:
                        f.write(f"\n  [子任务 #{subtask.get('id')}] {subtask.get('title')} [{subtask.get('status')}]\n")
                        if subtask.get('description'):
                            f.write(f"    描述: {subtask.get('description')}\n")
                        if subtask.get('result'):
                            f.write(f"    结果: {subtask.get('result')}\n")
                        if subtask.get('context'):
                            f.write(f"    上下文: {subtask.get('context')}\n")
                        f.write(f"    {'-' * 50}\n")

            messagebox.showinfo("成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

    def show_create_flow_dialog(self):
        """显示创建Flow对话框 - 赛博风格"""
        dialog = tk.Toplevel(self.root)
        dialog.title("[ 创建新任务 ]")
        dialog.geometry("600x400")
        dialog.configure(bg=CyberStyle.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(dialog, bg=CyberStyle.BG_MEDIUM)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(main_frame, text=">_ 目标任务描述",
                 font=("Courier New", 12, "bold"),
                 bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.MAGENTA).pack(anchor=tk.W, pady=(0, 10))

        input_text = scrolledtext.ScrolledText(main_frame, height=12, width=70,
                                               bg=CyberStyle.BG_DARK,
                                               fg=CyberStyle.CYAN,
                                               insertbackground=CyberStyle.CYAN,
                                               font=("Consolas", 10),
                                               relief=tk.FLAT)
        input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        def do_create():
            user_input = input_text.get(1.0, tk.END).strip()
            if not user_input:
                messagebox.showerror("错误", "请输入目标任务描述")
                return

            data = {
                "input": user_input,
                "provider": "custom"
            }

            dialog.destroy()
            self.create_flow(data)

        btn_frame = tk.Frame(main_frame, bg=CyberStyle.BG_MEDIUM)
        btn_frame.pack(fill=tk.X)

        btn_style = {"font": ("Courier New", 10, "bold"), "bg": CyberStyle.PURPLE,
                     "fg": CyberStyle.TEXT_PRIMARY, "activebackground": CyberStyle.PURPLE_LIGHT,
                     "relief": tk.FLAT, "cursor": "hand2", "padx": 20, "pady": 8}

        tk.Button(btn_frame, text="[ 提交任务 ]", command=do_create, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="[ 取消操作 ]", command=dialog.destroy, **btn_style).pack(side=tk.LEFT, padx=5)

        input_text.focus_set()

    def create_flow(self, data):
        """创建新Flow"""
        if not self.is_running:
            return
        self.update_status("正在创建任务...")
        self.add_log(f"创建新任务: {data.get('input', '')[:50]}...")

        def do_create():
            if not self.is_running:
                return
            result = self.make_request("POST", "/flows/", data)

            if result and result.get('status') == 'success':
                flow = result.get('data', {})
                self.safe_after(0, lambda: messagebox.showinfo("成功",
                                                               f"任务创建成功!\nID: {flow.get('id')}\n标题: {flow.get('title')}"))
                self.safe_after(0, self.refresh_flows)
                self.add_log(f"任务创建成功: ID={flow.get('id')}")
            elif result:
                self.add_log(f"任务创建失败: {result.get('msg', '未知错误')}")
            else:
                self.add_log("任务创建失败: 请求错误")

            self.update_status("系统就绪 >_")

        threading.Thread(target=do_create, daemon=True).start()

    def finish_flow(self):
        """完成Flow"""
        if not self.is_running:
            return
        selection = self.flow_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        values = self.flow_tree.item(selection[0], 'values')
        flow_id = values[0]
        flow_title = values[1]

        if not messagebox.askyesno("确认", f"确定要完成任务 \"{flow_title}\" 吗？"):
            return

        self.update_status(f"正在完成任务 {flow_id}...")
        self.add_log(f"正在完成任务: {flow_title}")

        def do_finish():
            if not self.is_running:
                return
            result = self.make_request("PUT", f"/flows/{flow_id}", {"action": "finish"})

            if result and result.get('status') == 'success':
                self.safe_after(0, lambda: messagebox.showinfo("成功", f"任务 \"{flow_title}\" 已完成"))
                self.safe_after(0, self.refresh_flows)
                self.add_log(f"任务完成成功: {flow_title}")
            else:
                self.add_log(f"任务完成失败: {flow_title}")

            self.update_status("系统就绪 >_")

        threading.Thread(target=do_finish, daemon=True).start()

    def delete_flow(self):
        """删除Flow"""
        if not self.is_running:
            return
        selection = self.flow_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个任务")
            return

        values = self.flow_tree.item(selection[0], 'values')
        flow_id = values[0]
        flow_title = values[1]

        if not messagebox.askyesno("确认", f"确定要删除任务 \"{flow_title}\" 吗？\n此操作不可恢复！"):
            return

        self.update_status(f"正在删除任务 {flow_id}...")
        self.add_log(f"正在删除任务: {flow_title}")

        def do_delete():
            if not self.is_running:
                return
            result = self.make_request("DELETE", f"/flows/{flow_id}")

            if result and result.get('status') == 'success':
                self.safe_after(0, lambda: messagebox.showinfo("成功", f"任务 \"{flow_title}\" 已删除"))
                self.safe_after(0, self.refresh_flows)
                self.add_log(f"任务删除成功: {flow_title}")
            else:
                self.add_log(f"任务删除失败: {flow_title}")

            self.update_status("系统就绪 >_")

        threading.Thread(target=do_delete, daemon=True).start()

    def show_auto_refresh_settings(self):
        """显示自动刷新设置对话框 - 赛博风格"""
        dialog = tk.Toplevel(self.root)
        dialog.title("[ 自动刷新配置 ]")
        dialog.geometry("400x250")
        dialog.configure(bg=CyberStyle.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=CyberStyle.BG_MEDIUM)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(frame, text="自动刷新:",
                 font=("Courier New", 11),
                 bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        enabled_var = tk.BooleanVar(value=self.auto_refresh)
        enabled_check = tk.Checkbutton(frame, variable=enabled_var,
                                       bg=CyberStyle.BG_MEDIUM,
                                       activebackground=CyberStyle.BG_MEDIUM,
                                       selectcolor=CyberStyle.BG_MEDIUM,
                                       fg=CyberStyle.CYAN)
        enabled_check.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        tk.Label(frame, text="刷新间隔(秒):",
                 font=("Courier New", 11),
                 bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        interval_spin = tk.Spinbox(frame, from_=5, to=120, width=10,
                                   bg=CyberStyle.BG_DARK, fg=CyberStyle.CYAN,
                                   font=("Consolas", 10),
                                   relief=tk.FLAT)
        interval_spin.delete(0, tk.END)
        interval_spin.insert(0, str(self.refresh_interval))
        interval_spin.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        def save_settings():
            self.auto_refresh = enabled_var.get()
            new_interval = int(interval_spin.get())
            if new_interval >= 5:
                self.refresh_interval = new_interval

            if self.auto_refresh:
                self.restart_auto_refresh()
            else:
                self.stop_auto_refresh()

            if hasattr(self, 'refresh_indicator'):
                self.refresh_indicator.config(
                    text=f"⏱ 自动刷新: {self.refresh_interval}s" if self.auto_refresh else "⏱ 自动刷新: 关闭")
            dialog.destroy()

        btn_style = {"font": ("Courier New", 10, "bold"), "bg": CyberStyle.PURPLE,
                     "fg": CyberStyle.TEXT_PRIMARY, "activebackground": CyberStyle.PURPLE_LIGHT,
                     "relief": tk.FLAT, "cursor": "hand2", "padx": 15, "pady": 5}

        tk.Button(frame, text="[ 保存配置 ]", command=save_settings, **btn_style).grid(row=2, column=0, columnspan=2,
                                                                                       pady=20)

    def show_api_settings(self):
        """显示API设置对话框 - 赛博风格"""
        dialog = tk.Toplevel(self.root)
        dialog.title("[ API终端配置 ]")
        dialog.geometry("500x250")
        dialog.configure(bg=CyberStyle.BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=CyberStyle.BG_MEDIUM)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(frame, text="API终端地址:",
                 font=("Courier New", 11),
                 bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        api_entry = tk.Entry(frame, width=40,
                             bg=CyberStyle.BG_DARK, fg=CyberStyle.CYAN,
                             insertbackground=CyberStyle.CYAN,
                             font=("Consolas", 10),
                             relief=tk.FLAT)
        api_entry.insert(0, self.api_base)
        api_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="忽略SSL证书:",
                 font=("Courier New", 11),
                 bg=CyberStyle.BG_MEDIUM, fg=CyberStyle.CYAN).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        verify_var = tk.BooleanVar(value=not self.verify_ssl)
        verify_check = tk.Checkbutton(frame, text="启用忽略模式", variable=verify_var,
                                      bg=CyberStyle.BG_MEDIUM,
                                      activebackground=CyberStyle.BG_MEDIUM,
                                      selectcolor=CyberStyle.BG_MEDIUM,
                                      fg=CyberStyle.CYAN)
        verify_check.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        def save_api_settings():
            self.api_base = api_entry.get().strip()
            self.verify_ssl = not verify_var.get()
            messagebox.showinfo("成功", "API配置已更新，请重新登录")
            dialog.destroy()
            self.safe_after(500, self.show_login)

        btn_style = {"font": ("Courier New", 10, "bold"), "bg": CyberStyle.PURPLE,
                     "fg": CyberStyle.TEXT_PRIMARY, "activebackground": CyberStyle.PURPLE_LIGHT,
                     "relief": tk.FLAT, "cursor": "hand2", "padx": 15, "pady": 5}

        tk.Button(frame, text="[ 保存并重启 ]", command=save_api_settings, **btn_style).grid(row=2, column=0,
                                                                                             columnspan=2, pady=20)

    def start_auto_refresh(self):
        """启动自动刷新"""
        self.stop_auto_refresh()
        self.refresh_job = self.safe_after(self.refresh_interval * 1000, self.auto_refresh_callback)

    def stop_auto_refresh(self):
        """停止自动刷新"""
        if self.refresh_job:
            try:
                self.root.after_cancel(self.refresh_job)
            except:
                pass
            self.refresh_job = None

    def restart_auto_refresh(self):
        """重启自动刷新"""
        self.stop_auto_refresh()
        self.start_auto_refresh()

    def auto_refresh_callback(self):
        """自动刷新回调"""
        if self.auto_refresh and hasattr(self, 'flow_tree') and self.is_running:
            self.refresh_flows()
            self.refresh_job = self.safe_after(self.refresh_interval * 1000, self.auto_refresh_callback)

    def add_log(self, message):
        """添加日志"""
        if not self.is_running:
            return

        def _add_log_impl():
            if not self.is_running:
                return
            if hasattr(self, 'logs_text'):
                try:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
                    self.logs_text.see(tk.END)
                    if int(self.logs_text.index('end-1c').split('.')[0]) > 500:
                        self.logs_text.delete(1.0, 2.0)
                except:
                    pass

        self.safe_after(0, _add_log_impl)

    def update_status(self, message):
        """更新状态栏"""
        if not self.is_running:
            return

        def _update_status_impl():
            if not self.is_running:
                return
            if hasattr(self, 'status_bar') and self.status_bar and self.status_bar.winfo_exists():
                try:
                    self.status_bar.config(text=f">_ {message}")
                except:
                    pass

        self.safe_after(0, _update_status_impl)

    def clear_window(self):
        """清空窗口内容"""
        # 停止所有后台任务
        self.is_running = False
        self.stop_auto_refresh()
        self.cancel_all_after_jobs()

        # 停止所有动画
        for job in self.glitch_jobs:
            try:
                self.root.after_cancel(job)
            except:
                pass
        self.glitch_jobs.clear()

        # 销毁所有子控件
        for widget in self.root.winfo_children():
            widget.destroy()

        # 重置标志位
        self.is_running = True

    def show_about(self):
        """显示关于对话框 - 赛博风格"""
        about_text = """
╔══════════════════════════════════════════════════════════════╗
║                    PentAGI 渗透测试智能体                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  功能特性:                                                    ║
║  • 实时监控任务运行状态                                        ║
║  • 智能创建和管理渗透测试任务                                  ║
║  • 自动刷新任务状态数据                                        ║
║  • 详细任务执行结果查看                                        ║
║  • 支持任务结构图导出                                         ║
║  • 远程重启后端服务                                           ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  技术支持: S&R Team                                          ║
╚══════════════════════════════════════════════════════════════╝
"""
        messagebox.showinfo("系统信息", about_text)

    def on_exit(self):
        """退出程序"""
        self.is_running = False
        self.glitch_animation = False
        self.stop_auto_refresh()
        self.cancel_all_after_jobs()

        # 停止所有动画
        for job in self.glitch_jobs:
            try:
                self.root.after_cancel(job)
            except:
                pass
        self.root.quit()


def main():
    root = tk.Tk()
    app = PentAGIClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()


if __name__ == "__main__":
    main()