import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

class PrankApp:
    def __init__(self, root):
        self.root = root
        self.root.title("系统安全扫描")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        self.root.configure(bg='black')

        # 让窗口始终置顶，增加"严肃感"
        self.root.attributes('-topmost', True)

        # 标题标签
        self.title_label = tk.Label(
            root, text="🔍 正在执行深度安全扫描...", 
            fg="#00ff00", bg='black', font=("Courier", 16, "bold")
        )
        self.title_label.pack(pady=15)

        # 进度条
        self.progress = ttk.Progressbar(
            root, orient="horizontal", length=400, mode="determinate", maximum=100
        )
        self.progress.pack(pady=10)

        # 状态信息（动态变化）
        self.status_var = tk.StringVar()
        self.status_var.set("初始化扫描引擎...")
        self.status_label = tk.Label(
            root, textvariable=self.status_var, fg="#00ff00", 
            bg='black', font=("Courier", 10)
        )
        self.status_label.pack(pady=10)

        # 虚假的"威胁列表"（滚动显示）
        self.threat_list = tk.Listbox(
            root, height=6, bg='black', fg='#ff4444', 
            font=("Courier", 9), selectmode=tk.NONE, highlightthickness=0
        )
        self.threat_list.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

        # 威胁数据库（搞笑/虚构）
        self.fake_threats = [
            "发现可疑进程：抖音脑波入侵.exe",
            "检测到未授权访问：你的WiFi密码被邻居记住",
            "高危漏洞：键盘上Ctrl和C离得太近",
            "警告：检测到用户试图关闭窗口 (已被拦截)",
            "发现木马：昨天说的'明天开始减肥'计划",
            "系统发现：你的浏览器历史记录异常丰富",
            "警告：CPU温度过高，可能因为你开了太多网页",
            "发现恶意软件：'再玩5分钟' 自动点击器",
            "检测到外星信号：来自冰箱的嗡嗡声",
        ]

        # 开始进度
        self.current_progress = 0
        self.threat_index = 0
        self.update_progress()

        # 绑定关闭事件，增加趣味
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_progress(self):
        """更新进度条和状态信息"""
        if self.current_progress < 100:
            # 进度增加（偶尔跳动）
            increment = random.randint(1, 5)
            self.current_progress = min(self.current_progress + increment, 100)
            self.progress['value'] = self.current_progress

            # 随机更新状态信息
            statuses = [
                "正在扫描系统文件...",
                "检查注册表项...",
                "分析网络流量...",
                "扫描硬盘分区...",
                "验证系统完整性...",
                "检测潜在威胁...",
                "正在加密你的文件（开玩笑的）...",
                "读取内存页面...",
                "与NSA数据库比对...",
                "扫描你的表情包...",
            ]
            self.status_var.set(random.choice(statuses))

            # 随机添加一条"威胁"到列表（但限制数量，防止溢出）
            if random.random() < 0.2:  # 20%概率添加
                threat = random.choice(self.fake_threats)
                self.threat_list.insert(tk.END, f"⚠ {threat}")
                # 保持列表最多显示10条
                if self.threat_list.size() > 10:
                    self.threat_list.delete(0)
                # 自动滚动到底部
                self.threat_list.yview_moveto(1)

            # 继续更新
            self.root.after(random.randint(100, 300), self.update_progress)
        else:
            # 进度完成，触发"高潮"
            self.finish_scan()

    def finish_scan(self):
        """扫描完成，展示恶搞结果"""
        self.status_var.set("扫描完成！正在生成报告...")
        self.title_label.config(text="🎉 扫描完成！")

        # 弹出多个搞笑消息框（用after延迟逐个弹出）
        self.root.after(500, self.popup_1)
        self.root.after(1500, self.popup_2)
        self.root.after(2500, self.popup_3)
        self.root.after(3500, self.final_popup)

    def popup_1(self):
        messagebox.showinfo("扫描结果", "你的电脑很干净！\n但是...你被耍了！😂")

    def popup_2(self):
        messagebox.showwarning("紧急通知", "其实你的电脑正在被外星人远程控制！\n（才怪）")

    def popup_3(self):
        messagebox.showerror("致命错误", "系统检测到你的智商过高，无法匹配当前程序！")

    def final_popup(self):
        """最后的大结局"""
        answer = messagebox.askyesno("🤖 终极问题", "你觉得这个程序有趣吗？\n（点『是』继续，『否』重来）")
        if answer:
            messagebox.showinfo("感谢", "谢谢你！祝你开心每一天！😄")
            self.root.destroy()
        else:
            # 重新开始扫描（循环）
            self.restart_scan()

    def restart_scan(self):
        """重置所有，重新扫描"""
        self.current_progress = 0
        self.progress['value'] = 0
        self.threat_list.delete(0, tk.END)
        self.title_label.config(text="🔍 正在执行深度安全扫描...")
        self.status_var.set("重新启动扫描引擎...")
        self.update_progress()

    def on_close(self):
        """尝试关闭窗口时的反应"""
        # 弹出恐吓对话框
        reply = messagebox.askyesno("⚠ 安全警告", 
            "关闭此窗口将导致系统崩溃！\n你确定要继续吗？")
        if reply:
            # 假装崩溃，实际是另一个搞笑对话框
            messagebox.showerror("💥 系统崩溃", 
                "开玩笑的！你的系统很安全。\n不过你差点就上了我的当！哈哈哈")
            self.root.destroy()
        else:
            messagebox.showinfo("明智的选择", "我就知道你没这个胆量！😎")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrankApp(root)
    root.mainloop()