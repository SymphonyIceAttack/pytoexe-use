import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import datetime
import time
import threading

class ShutdownTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("定时关机助手")
        self.root.geometry("480x380")
        self.root.resizable(False, False)
        
        # 定时任务相关变量
        self.target_time = None          # 目标关机时间 (datetime对象)
        self.after_id = None             # after事件ID
        self.is_active = False           # 是否有活动的定时任务
        
        # 创建界面
        self.create_widgets()
        
        # 启动时钟更新
        self.update_current_time()
        
        # 窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="定时关机程序", font=('微软雅黑', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 当前时间显示区域
        time_frame = ttk.LabelFrame(main_frame, text="当前系统时间", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_time_var = tk.StringVar()
        current_time_label = ttk.Label(time_frame, textvariable=self.current_time_var, 
                                       font=('Consolas', 14))
        current_time_label.pack()
        
        # 模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="关机模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_var = tk.IntVar(value=1)
        ttk.Radiobutton(mode_frame, text="倒计时模式", variable=self.mode_var, 
                        value=1, command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="指定时间模式", variable=self.mode_var, 
                        value=2, command=self.on_mode_change).pack(anchor=tk.W)
        
        # 参数输入区域
        self.input_frame = ttk.Frame(main_frame)
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 倒计时模式控件
        self.countdown_frame = ttk.Frame(self.input_frame)
        ttk.Label(self.countdown_frame, text="倒计时时间:").pack(side=tk.LEFT, padx=(0, 5))
        self.minutes_var = tk.StringVar(value="30")
        minutes_spinbox = ttk.Spinbox(self.countdown_frame, from_=1, to=1440, 
                                      width=10, textvariable=self.minutes_var)
        minutes_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(self.countdown_frame, text="分钟").pack(side=tk.LEFT)
        
        # 指定时间模式控件
        self.specific_frame = ttk.Frame(self.input_frame)
        ttk.Label(self.specific_frame, text="关机时间 (HH:MM):").pack(side=tk.LEFT, padx=(0, 5))
        self.time_var = tk.StringVar(value="23:00")
        time_entry = ttk.Entry(self.specific_frame, width=10, textvariable=self.time_var)
        time_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(self.specific_frame, text="例如: 22:30").pack(side=tk.LEFT)
        
        # 默认显示倒计时模式
        self.countdown_frame.pack(fill=tk.X)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 5))
        
        self.start_btn = ttk.Button(button_frame, text="开始定时", command=self.start_timer)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.cancel_btn = ttk.Button(button_frame, text="取消定时", command=self.cancel_timer)
        self.cancel_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.shutdown_btn = ttk.Button(button_frame, text="立即关机", command=self.shutdown_now)
        self.shutdown_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(main_frame, text="任务状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="当前无定时任务")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                 font=('微软雅黑', 10), wraplength=400)
        status_label.pack(fill=tk.X, pady=(0, 5))
        
        self.remaining_var = tk.StringVar(value="剩余时间: --小时 --分钟 --秒")
        remaining_label = ttk.Label(status_frame, textvariable=self.remaining_var, 
                                    font=('Consolas', 11))
        remaining_label.pack(fill=tk.X)
        
        # 提示信息
        info_label = ttk.Label(main_frame, text="提示: 关机任务由系统执行，程序退出不影响已设定的关机计划。",
                               foreground="gray", font=('微软雅黑', 8))
        info_label.pack(pady=(5, 0))
    
    def on_mode_change(self):
        """模式切换时切换输入控件"""
        # 清空当前显示的框架
        for widget in self.input_frame.winfo_children():
            widget.pack_forget()
        
        if self.mode_var.get() == 1:
            self.countdown_frame.pack(fill=tk.X)
        else:
            self.specific_frame.pack(fill=tk.X)
    
    def update_current_time(self):
        """更新当前时间显示"""
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        self.current_time_var.set(current_time)
        # 每秒更新一次
        self.root.after(1000, self.update_current_time)
    
    def start_timer(self):
        """启动定时关机"""
        try:
            # 获取关机时间（秒数）
            seconds, target_time = self.get_shutdown_seconds()
            if seconds <= 0:
                messagebox.showwarning("无效时间", "关机时间必须晚于当前时间！")
                return
            
            # 取消已有定时任务（如果有）
            self.cancel_timer(keep_status=False)
            
            # 调用系统关机命令
            result = subprocess.run(["shutdown", "/s", "/t", str(seconds)], 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                # 如果出错，显示错误信息
                error_msg = result.stderr.strip() if result.stderr else "未知错误"
                messagebox.showerror("设置失败", f"无法设置系统关机任务:\n{error_msg}")
                return
            
            # 记录目标时间
            self.target_time = target_time
            self.is_active = True
            
            # 更新状态显示
            if self.mode_var.get() == 1:
                minutes = int(self.minutes_var.get())
                self.status_var.set(f"定时任务已设置: {minutes}分钟后关机 ({target_time.strftime('%H:%M:%S')})")
            else:
                self.status_var.set(f"定时任务已设置: {target_time.strftime('%H:%M:%S')} 关机")
            
            # 开始倒计时显示
            self.update_remaining_time()
            
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"发生意外错误:\n{str(e)}")
    
    def get_shutdown_seconds(self):
        """
        根据用户输入获取关机倒计时秒数和目标时间
        返回: (seconds, target_datetime)
        """
        current_time = datetime.datetime.now()
        
        if self.mode_var.get() == 1:  # 倒计时模式
            try:
                minutes = int(self.minutes_var.get())
                if minutes <= 0:
                    raise ValueError("倒计时分钟数必须大于0")
            except ValueError:
                raise ValueError("请输入有效的分钟数（正整数）")
            
            seconds = minutes * 60
            target_time = current_time + datetime.timedelta(seconds=seconds)
            return seconds, target_time
        
        else:  # 指定时间模式
            time_str = self.time_var.get().strip()
            try:
                # 解析时间
                time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
                target_time = datetime.datetime.combine(current_time.date(), time_obj)
                
                # 如果指定时间已过，则设为明天
                if target_time <= current_time:
                    target_time += datetime.timedelta(days=1)
                
                seconds = int((target_time - current_time).total_seconds())
                if seconds <= 0:
                    raise ValueError("关机时间必须晚于当前时间")
                return seconds, target_time
                
            except ValueError:
                raise ValueError("请输入有效的时间格式 (HH:MM)，例如 23:30")
    
    def cancel_timer(self, keep_status=False):
        """
        取消定时关机任务
        keep_status: 是否保留状态显示（用于内部调用时避免重复清空状态）
        """
        # 调用系统取消关机命令
        try:
            subprocess.run(["shutdown", "/a"], capture_output=True, check=False)
        except:
            pass  # 忽略可能的错误
        
        # 取消待执行的after回调
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        
        # 重置状态
        self.is_active = False
        self.target_time = None
        
        if not keep_status:
            self.status_var.set("定时任务已取消")
            self.remaining_var.set("剩余时间: --小时 --分钟 --秒")
    
    def shutdown_now(self):
        """立即关机"""
        if messagebox.askyesno("确认关机", "确定要立即关闭计算机吗？\n所有未保存的工作将会丢失！"):
            try:
                subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("关机失败", f"无法执行关机命令:\n{e.stderr}")
            except Exception as e:
                messagebox.showerror("错误", f"发生错误:\n{str(e)}")
    
    def update_remaining_time(self):
        """更新剩余时间显示"""
        if not self.is_active or self.target_time is None:
            return
        
        current_time = datetime.datetime.now()
        remaining_seconds = int((self.target_time - current_time).total_seconds())
        
        if remaining_seconds <= 0:
            # 时间已到，系统应该已经关机或正在关机
            self.remaining_var.set("剩余时间: 正在关机...")
            self.status_var.set("关机任务已执行，系统正在关机...")
            # 停止更新
            self.is_active = False
            self.target_time = None
            return
        
        # 格式化显示剩余时间
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        
        self.remaining_var.set(f"剩余时间: {hours:02d}小时 {minutes:02d}分钟 {seconds:02d}秒")
        
        # 每秒更新一次
        self.after_id = self.root.after(1000, self.update_remaining_time)
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.is_active:
            if messagebox.askyesno("确认退出", "当前有未执行的关机任务。\n是否取消关机任务并退出？"):
                self.cancel_timer()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ShutdownTimer(root)
    root.mainloop()

if __name__ == "__main__":
    main()