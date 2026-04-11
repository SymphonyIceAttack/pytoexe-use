import smtplib
import tkinter as tk
from tkinter import messagebox
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
import threading

# 邮件配置信息
my_sender = '3869603852@qq.com'  # 填写发信人的邮箱账号
my_pass = 'wxaqhdsgzxspcbga'  # 发件人邮箱授权码

class MailApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("MCkali 白名单管理")
        self.window.geometry("350x300")
        self.window.attributes('-topmost', True)  # 窗口置顶
        self.window.resizable(False, False)
        
        # 设置窗口图标（可选）
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_widgets()
        
    def create_widgets(self):
        # QQ号输入框
        tk.Label(self.window, text="QQ号:", font=("微软雅黑", 10)).pack(pady=(10, 0))
        self.qq_entry = tk.Entry(self.window, width=30, font=("微软雅黑", 10))
        self.qq_entry.pack(pady=(5, 10))
        
        # 名字输入框
        tk.Label(self.window, text="玩家名字:", font=("微软雅黑", 10)).pack()
        self.name_entry = tk.Entry(self.window, width=30, font=("微软雅黑", 10))
        self.name_entry.pack(pady=(5, 15))
        
        # 按钮框架
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        # 通过按钮
        self.pass_btn = tk.Button(button_frame, text="通过", 
                                  bg="#4CAF50", fg="white", 
                                  font=("微软雅黑", 11, "bold"),
                                  width=10, height=1,
                                  command=self.send_pass_email)
        self.pass_btn.pack(side=tk.LEFT, padx=5)
        
        # 拒绝按钮
        self.reject_btn = tk.Button(button_frame, text="拒绝", 
                                    bg="#FF9800", fg="white", 
                                    font=("微软雅黑", 11, "bold"),
                                    width=10, height=1,
                                    command=self.send_reject_email)
        self.reject_btn.pack(side=tk.LEFT, padx=5)
        
        # 封禁按钮
        self.ban_btn = tk.Button(button_frame, text="封禁", 
                                 bg="#f44336", fg="white", 
                                 font=("微软雅黑", 11, "bold"),
                                 width=10, height=1,
                                 command=self.send_ban_email)
        self.ban_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(self.window, text="就绪", 
                                     font=("微软雅黑", 9), fg="gray")
        self.status_label.pack(pady=15)
        
        # 添加最小化提示
        tk.Label(self.window, text="提示: 窗口始终置顶，方便操作", 
                font=("微软雅黑", 8), fg="gray").pack(side=tk.BOTTOM, pady=5)
    
    def get_current_date(self):
        """获取当前日期"""
        return datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    def send_email(self, subject, content):
        """发送邮件的通用函数"""
        qq = self.qq_entry.get().strip()
        name = self.name_entry.get().strip()
        
        # 验证输入
        if not qq:
            messagebox.showwarning("警告", "请输入QQ号！")
            return False
        if not name:
            messagebox.showwarning("警告", "请输入玩家名字！")
            return False
        
        # 处理QQ号，去掉可能存在的@qq.com
        qq = qq.replace('@qq.com', '').strip()
        recipient = f"{qq}@qq.com"
        
        # 格式化邮件内容
        formatted_content = content.replace("【上方输入的名字】", name)
        formatted_content += f"\n\n\n{' '*50}{self.get_current_date()}"
        
        # 在新线程中发送邮件，避免界面卡顿
        def send_in_thread():
            self.status_label.config(text="正在发送邮件...", fg="blue")
            self.disable_buttons(True)
            
            ret = True
            try:
                msg = MIMEText(formatted_content, 'plain', 'utf-8')
                msg['From'] = formataddr(["Miao团队机器人", my_sender])
                msg['To'] = formataddr([name, recipient])
                msg['Subject'] = subject
                
                server = smtplib.SMTP_SSL("smtp.qq.com", 465)
                server.login(my_sender, my_pass)
                server.sendmail(my_sender, [recipient], msg.as_string())
                server.quit()
                
                self.window.after(0, lambda: self.status_label.config(
                    text=f"✓ 邮件发送成功！ ({self.get_current_date()})", fg="green"))
                self.window.after(0, lambda: messagebox.showinfo("成功", f"邮件已发送给 {name}({recipient})"))
                
            except Exception as e:
                ret = False
                error_msg = str(e)
                self.window.after(0, lambda: self.status_label.config(
                    text=f"✗ 邮件发送失败: {error_msg[:30]}...", fg="red"))
                self.window.after(0, lambda: messagebox.showerror("错误", f"邮件发送失败:\n{error_msg}"))
            
            self.window.after(0, lambda: self.disable_buttons(False))
            return ret
        
        thread = threading.Thread(target=send_in_thread)
        thread.daemon = True
        thread.start()
        
        return True
    
    def send_pass_email(self):
        """发送通过邮件"""
        subject = "MCkali白名单申请 - 已通过"
        content = """尊贵的【上方输入的名字】:
        你的游戏白名单申请已通过，感谢你对MCkali的支持！"""
        self.send_email(subject, content)
    
    def send_reject_email(self):
        """发送拒绝邮件"""
        subject = "MCkali白名单申请 - 未通过"
        content = """尊贵的【上方输入的名字】:
        你的游戏白名单申请无法通过，原因可能是：服务器已关闭，服务器故障，你的用户名是假的等"""
        self.send_email(subject, content)
    
    def send_ban_email(self):
        """发送封禁邮件"""
        subject = "MCkali白名单 - 已被注销"
        content = """尊贵的【上方输入的名字】:
        因为你被其他玩家举报，举报原因：违规行为，所以你的白名单已被注销！"""
        self.send_email(subject, content)
    
    def disable_buttons(self, disabled):
        """禁用/启用按钮"""
        state = tk.DISABLED if disabled else tk.NORMAL
        self.pass_btn.config(state=state)
        self.reject_btn.config(state=state)
        self.ban_btn.config(state=state)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            self.window.destroy()
    
    def run(self):
        """运行程序"""
        self.window.mainloop()

# 主程序入口
if __name__ == "__main__":
    # 检查邮箱配置
    if my_sender == 'xxxx@qq.com' or my_pass == 'xxxx':
        print("警告：请先在代码中配置发件人邮箱和授权码！")
        print("my_sender: 你的QQ邮箱")
        print("my_pass: QQ邮箱的授权码（不是QQ密码）")
        
    app = MailApp()
    app.run()