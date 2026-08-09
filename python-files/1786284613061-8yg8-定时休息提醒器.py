import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
from datetime import datetime

class BreakReminder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("休息提醒器")
        self.root.geometry("480x500")
        self.root.resizable(False, False)
        
        # 设置窗口置顶
        self.root.attributes('-topmost', True)
        
        # 休息状态
        self.is_on_break = False
        self.is_running = False
        self.remaining_time = 0
        
        # 默认时间设置
        self.work_minutes = tk.IntVar(value=45)
        self.break_minutes = tk.IntVar(value=5)
        
        # 创建主界面
        self.create_widgets()
        
        # 计时器线程
        self.timer_thread = None
        
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(
            self.root, 
            text="💪 健康工作提醒器", 
            font=("Arial", 18, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=15)
        
        # === 设置框架 ===
        setting_frame = tk.LabelFrame(self.root, text="⏱️ 时间设置", font=("Arial", 12, "bold"))
        setting_frame.pack(pady=10, padx=20, fill="x")
        
        # 工作时间设置
        work_frame = tk.Frame(setting_frame)
        work_frame.pack(pady=8, padx=10)
        
        tk.Label(work_frame, text="🕐 工作时间：", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.work_spinbox = tk.Spinbox(
            work_frame,
            from_=1,
            to=180,
            textvariable=self.work_minutes,
            width=12,
            font=("Arial", 11)
        )
        self.work_spinbox.pack(side=tk.LEFT, padx=5)
        tk.Label(work_frame, text="分钟", font=("Arial", 11)).pack(side=tk.LEFT)
        
        # 休息时间设置
        break_frame = tk.Frame(setting_frame)
        break_frame.pack(pady=8, padx=10)
        
        tk.Label(break_frame, text="☕ 休息时间：", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.break_spinbox = tk.Spinbox(
            break_frame,
            from_=1,
            to=60,
            textvariable=self.break_minutes,
            width=12,
            font=("Arial", 11)
        )
        self.break_spinbox.pack(side=tk.LEFT, padx=5)
        tk.Label(break_frame, text="分钟", font=("Arial", 11)).pack(side=tk.LEFT)
        
        # === 状态和计时显示 ===
        display_frame = tk.Frame(self.root, bg="#f8f9fa", relief="ridge", bd=2)
        display_frame.pack(pady=15, padx=20, fill="x")
        
        # 状态标签
        self.status_label = tk.Label(
            display_frame,
            text="⏸️ 等待开始",
            font=("Arial", 13),
            fg="#7f8c8d",
            bg="#f8f9fa"
        )
        self.status_label.pack(pady=5)
        
        # 计时显示
        self.time_label = tk.Label(
            display_frame,
            text="--:--",
            font=("Arial", 56, "bold"),
            fg="#2980b9",
            bg="#f8f9fa"
        )
        self.time_label.pack(pady=5)
        
        # 进度条
        progress_frame = tk.Frame(display_frame, bg="#f8f9fa")
        progress_frame.pack(pady=10, padx=10)
        
        self.progress = tk.Canvas(progress_frame, width=380, height=28, bg="#ecf0f1", highlightthickness=0)
        self.progress.pack()
        self.progress_bar = self.progress.create_rectangle(0, 0, 0, 28, fill="#3498db")
        self.progress_text = self.progress.create_text(190, 14, text="0%", fill="white", font=("Arial", 11, "bold"))
        
        # === 按钮区域 ===
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=15)
        
        # 第一行按钮
        self.start_button = tk.Button(
            button_frame,
            text="▶ 开始计时",
            font=("Arial", 12, "bold"),
            command=self.start_timer,
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=10,
            cursor="hand2",
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=6)
        
        self.pause_button = tk.Button(
            button_frame,
            text="⏸️ 暂停",
            font=("Arial", 12),
            command=self.pause_timer,
            bg="#f39c12",
            fg="white",
            padx=25,
            pady=10,
            cursor="hand2",
            width=10,
            state="disabled"
        )
        self.pause_button.pack(side=tk.LEFT, padx=6)
        
        self.break_button = tk.Button(
            button_frame,
            text="☕ 提前休息",
            font=("Arial", 12),
            command=self.manual_break,
            bg="#e67e22",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            width=10,
            state="disabled"
        )
        self.break_button.pack(side=tk.LEFT, padx=6)
        
        # 第二行按钮
        button_frame2 = tk.Frame(self.root)
        button_frame2.pack(pady=8)
        
        self.reset_button = tk.Button(
            button_frame2,
            text="🔄 重置",
            font=("Arial", 11),
            command=self.reset_timer,
            bg="#95a5a6",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            width=12,
            state="disabled"
        )
        self.reset_button.pack(side=tk.LEFT, padx=6)
        
        self.quit_button = tk.Button(
            button_frame2,
            text="🚪 退出",
            font=("Arial", 11),
            command=self.quit_app,
            bg="#e74c3c",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            width=12
        )
        self.quit_button.pack(side=tk.LEFT, padx=6)
        
        # 底部提示
        info_frame = tk.Frame(self.root, bg="#f0f0f0")
        info_frame.pack(pady=15, fill="x")
        
        info_label = tk.Label(
            info_frame,
            text="💡 设置好时间后点击「开始计时」即可\n⏰ 休息时会自动锁定屏幕，解锁后可继续工作",
            font=("Arial", 10),
            fg="#555555",
            bg="#f0f0f0",
            justify="center"
        )
        info_label.pack(pady=8)
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
    def start_timer(self):
        """开始计时"""
        if self.is_running:
            return
            
        # 获取设置的时间
        work_time = self.work_minutes.get()
        break_time = self.break_minutes.get()
        
        if work_time <= 0 or break_time <= 0:
            messagebox.showwarning("警告", "时间必须大于0分钟！")
            return
            
        # 转换为秒
        self.work_duration = work_time * 60
        self.break_duration = break_time * 60
        self.remaining_time = self.work_duration
        
        self.is_running = True
        self.is_on_break = False
        
        # 更新按钮状态
        self.start_button.config(state="disabled", bg="#95a5a6", text="⏳ 运行中")
        self.pause_button.config(state="normal")
        self.break_button.config(state="normal")
        self.reset_button.config(state="normal")
        self.work_spinbox.config(state="disabled")
        self.break_spinbox.config(state="disabled")
        
        # 更新状态
        self.status_label.config(text="⏰ 工作状态", fg="#27ae60")
        self.time_label.config(fg="#2980b9")
        
        # 启动计时线程
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()
        
    def timer_loop(self):
        """计时器主循环"""
        while self.is_running and self.remaining_time > 0:
            self.update_display(self.remaining_time, self.work_duration if not self.is_on_break else self.break_duration)
            time.sleep(1)
            self.remaining_time -= 1
            
        # 时间到
        if self.is_running:
            if not self.is_on_break:
                # 工作时间结束，开始休息
                self.root.after(0, self.start_break)
            else:
                # 休息时间结束
                self.root.after(0, self.end_break)
                
    def update_display(self, remaining, total):
        """更新界面显示"""
        # 更新文字
        minutes = remaining // 60
        seconds = remaining % 60
        time_text = f"{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_text)
        
        # 更新进度条
        if total > 0:
            progress_percent = (remaining / total) * 100
            progress_width = (remaining / total) * 380
            self.progress.coords(self.progress_bar, 0, 0, progress_width, 28)
            self.progress.itemconfig(self.progress_text, text=f"{int(progress_percent)}%")
        
        # 更新界面
        self.root.update_idletasks()
        
    def start_break(self):
        """开始休息"""
        self.is_on_break = True
        self.remaining_time = self.break_duration
        
        # 锁定屏幕
        self.lock_screen()
        
        # 更新状态
        self.status_label.config(text="☕ 休息时间", fg="#e67e22")
        self.time_label.config(fg="#e67e22")
        self.break_button.config(text="⏹️ 结束休息")
        self.start_button.config(text="⏳ 休息中")
        
        # 显示通知
        self.show_notification(
            "休息时间到！",
            f"请站起来活动一下，休息{self.break_minutes.get()}分钟",
            "info"
        )
        
        # 继续计时（休息倒计时）
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()
        
    def end_break(self):
        """结束休息"""
        self.is_on_break = False
        self.is_running = False
        self.remaining_time = 0
        
        # 解锁屏幕（通知用户）
        self.unlock_screen()
        
        # 更新界面
        self.time_label.config(text="休息结束！", fg="#27ae60")
        self.status_label.config(text="✅ 休息结束", fg="#27ae60")
        self.break_button.config(text="☕ 提前休息", state="disabled")
        self.start_button.config(text="▶ 开始计时", state="normal", bg="#27ae60")
        
        # 恢复按钮状态
        self.pause_button.config(state="disabled")
        self.reset_button.config(state="disabled")
        self.work_spinbox.config(state="normal")
        self.break_spinbox.config(state="normal")
        
        # 显示通知
        self.show_notification(
            "休息结束！",
            "继续努力工作吧！💪",
            "info"
        )
        
        # 重置进度条
        self.progress.coords(self.progress_bar, 0, 0, 0, 28)
        self.progress.itemconfig(self.progress_text, text="0%")
        
    def pause_timer(self):
        """暂停/继续计时"""
        if self.is_running:
            # 暂停
            self.is_running = False
            self.pause_button.config(text="▶ 继续", bg="#27ae60")
            self.status_label.config(text="⏸️ 已暂停", fg="#f39c12")
        else:
            # 继续
            self.is_running = True
            self.pause_button.config(text="⏸️ 暂停", bg="#f39c12")
            self.status_label.config(text="⏰ 工作状态" if not self.is_on_break else "☕ 休息时间", 
                                    fg="#27ae60" if not self.is_on_break else "#e67e22")
            # 重新启动线程
            self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
            self.timer_thread.start()
        
    def manual_break(self):
        """手动开始/结束休息"""
        if not self.is_on_break:
            # 开始手动休息
            if messagebox.askyesno("确认", f"确定要现在开始休息{self.break_minutes.get()}分钟吗？"):
                # 停止当前计时
                self.is_running = False
                # 开始休息
                self.start_break()
        else:
            # 结束休息
            if messagebox.askyesno("确认", "确定要结束休息吗？"):
                self.is_running = False
                self.end_break()
                
    def reset_timer(self):
        """重置计时器"""
        if self.is_running:
            self.is_running = False
            
        self.is_on_break = False
        self.remaining_time = 0
        
        # 重置显示
        self.time_label.config(text="--:--", fg="#2980b9")
        self.status_label.config(text="⏸️ 已重置", fg="#7f8c8d")
        self.progress.coords(self.progress_bar, 0, 0, 0, 28)
        self.progress.itemconfig(self.progress_text, text="0%")
        
        # 重置按钮
        self.start_button.config(text="▶ 开始计时", state="normal", bg="#27ae60")
        self.pause_button.config(text="⏸️ 暂停", state="disabled", bg="#f39c12")
        self.break_button.config(text="☕ 提前休息", state="disabled")
        self.reset_button.config(state="disabled")
        self.work_spinbox.config(state="normal")
        self.break_spinbox.config(state="normal")
        
    def lock_screen(self):
        """锁定电脑屏幕"""
        system = sys.platform
        
        try:
            if system == 'win32':
                # Windows
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], 
                             check=True, shell=True)
            elif system == 'darwin':
                # macOS
                subprocess.run(['pmset', 'displaysleepnow'], check=True)
            else:
                # Linux
                try:
                    subprocess.run(['gnome-screensaver-command', '-l'], check=True)
                except:
                    subprocess.run(['xdg-screensaver', 'lock'], check=True)
        except Exception as e:
            print(f"锁定屏幕时出错: {e}")
            
    def unlock_screen(self):
        """解锁屏幕（仅通知）"""
        # 实际解锁需要用户手动操作
        pass
        
    def show_notification(self, title, message, type="info"):
        """显示通知"""
        self.root.attributes('-topmost', True)
        
        if type == "info":
            messagebox.showinfo(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        elif type == "error":
            messagebox.showerror(title, message)
            
        self.root.attributes('-topmost', False)
        
    def quit_app(self):
        """退出应用"""
        if messagebox.askyesno("确认退出", "确定要退出休息提醒器吗？"):
            self.is_running = False
            self.root.quit()
            self.root.destroy()
            
    def run(self):
        """运行应用"""
        self.root.mainloop()

def main():
    """主函数"""
    app = BreakReminder()
    app.run()

if __name__ == "__main__":
    main()
