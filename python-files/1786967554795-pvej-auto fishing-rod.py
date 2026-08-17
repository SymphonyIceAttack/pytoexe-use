import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button

# ============================================================
# 核心逻辑类
# ============================================================
class AutoClicker:
    """
    自动点击器核心逻辑
    负责监听键盘事件、执行点击操作、管理间隔和定时器
    """
    def __init__(self):
        # 模式: 'semi' 半自动, 'auto' 全自动
        self.mode = 'semi'
        # 点击间隔（毫秒），仅半自动模式有效
        self.click_interval_ms = 50
        # 运行状态
        self.running = False
        # 上次触发时间（按下=的时间）
        self.last_trigger_time = 0
        # = 键是否被按下
        self.equal_key_pressed = False
        # 本次按下是否被间隔限制阻止
        self.press_blocked = False
        # 全自动模式的定时器
        self.auto_timer = None
        # 键盘控制器
        self.keyboard_controller = keyboard.Controller()
        # 鼠标控制器
        self.mouse_controller = MouseController()
        # 监听器
        self.listener = None
        # 锁，用于线程安全
        self.lock = threading.Lock()

    def start(self):
        """启动监听"""
        if self.running:
            return
        self.running = True
        self.last_trigger_time = 0
        self.equal_key_pressed = False
        self.press_blocked = False

        # 在独立线程中启动监听器
        def run_listener():
            with self.lock:
                self.listener = keyboard.Listener(
                    on_press=self._on_press,
                    on_release=self._on_release
                )
            self.listener.start()
            self.listener.join()

        self.listener_thread = threading.Thread(target=run_listener, daemon=True)
        self.listener_thread.start()

    def stop(self):
        """停止监听"""
        if not self.running:
            return
        self.running = False
        with self.lock:
            if self.listener is not None:
                self.listener.stop()
                self.listener = None
        # 取消全自动定时器
        self._cancel_auto_timer()
        # 如果=键还在按下，释放所有按键
        if self.equal_key_pressed:
            self._release_all()

    def set_mode(self, mode):
        """设置模式: 'semi' 或 'auto'"""
        self.mode = mode

    def set_interval(self, ms):
        """设置半自动模式的点击间隔（毫秒）"""
        if ms < 0:
            ms = 0
        self.click_interval_ms = ms

    def _on_press(self, key):
        """键盘按下事件回调"""
        try:
            if not self.running:
                return
            # 检查是否是 = 键 (主键盘上的 =)
            if hasattr(key, 'char') and key.char == '=':
                self._handle_equal_press()
        except Exception as e:
            print(f"[错误] 按下事件处理异常: {e}")

    def _on_release(self, key):
        """键盘释放事件回调"""
        try:
            if not self.running:
                return
            if hasattr(key, 'char') and key.char == '=':
                self._handle_equal_release()
        except Exception as e:
            print(f"[错误] 释放事件处理异常: {e}")

    def _handle_equal_press(self):
        """处理 = 键按下"""
        with self.lock:
            if self.equal_key_pressed:
                # 如果=键已经按下，忽略重复事件
                return
            self.equal_key_pressed = True

            if self.mode == 'semi':
                # 半自动模式：检查间隔
                current_time = time.time() * 1000  # 毫秒
                elapsed = current_time - self.last_trigger_time
                if elapsed >= self.click_interval_ms:
                    # 间隔已到，执行操作
                    self.last_trigger_time = current_time
                    self.press_blocked = False
                    self._press_6_and_right()
                else:
                    # 间隔未到，阻止本次操作
                    self.press_blocked = True
                    print(f"[半自动] 间隔未到 ({elapsed:.0f}ms < {self.click_interval_ms}ms)，阻止触发")
            else:
                # 全自动模式
                self.press_blocked = False
                # 取消之前的定时器
                self._cancel_auto_timer()
                # 按下6和右键
                self._press_6_and_right()
                # 启动定时器，260ms后执行
                self._start_auto_timer()

    def _handle_equal_release(self):
        """处理 = 键释放"""
        with self.lock:
            if not self.equal_key_pressed:
                return
            self.equal_key_pressed = False

            if self.mode == 'semi':
                if not self.press_blocked:
                    # 如果按下时没有被阻止，释放6和右键，然后点击1
                    self._release_6_and_right()
                    self._click_1()
                # 如果被阻止，什么都不做
                self.press_blocked = False
            # 全自动模式：释放=不执行任何操作

    def _press_6_and_right(self):
        """按下 6 键和鼠标右键（保持按下状态）"""
        try:
            # 按下 6 键
            self.keyboard_controller.press('6')
            # 按下鼠标右键
            self.mouse_controller.press(Button.right)
        except Exception as e:
            print(f"[错误] 按下6+右键失败: {e}")

    def _release_6_and_right(self):
        """释放 6 键和鼠标右键"""
        try:
            self.keyboard_controller.release('6')
            self.mouse_controller.release(Button.right)
        except Exception as e:
            print(f"[错误] 释放6+右键失败: {e}")

    def _click_1(self):
        """点击 1 键（按下并释放）"""
        try:
            self.keyboard_controller.press('1')
            self.keyboard_controller.release('1')
        except Exception as e:
            print(f"[错误] 点击1失败: {e}")

    def _release_all(self):
        """释放所有被按下的键和鼠标按钮"""
        try:
            self.keyboard_controller.release('6')
            self.keyboard_controller.release('1')
            self.mouse_controller.release(Button.right)
        except Exception as e:
            print(f"[错误] 释放所有失败: {e}")

    def _start_auto_timer(self):
        """启动全自动模式的定时器（260ms后执行）"""
        def timer_callback():
            with self.lock:
                if not self.running:
                    return
                if self.mode == 'auto' and self.equal_key_pressed:
                    # 注意：定时器触发时，=键可能已经被释放，但依然执行
                    # 释放6和右键，然后点击1
                    self._release_6_and_right()
                    self._click_1()
                    self.auto_timer = None

        # 使用 threading.Timer，延迟260ms
        self.auto_timer = threading.Timer(0.260, timer_callback)
        self.auto_timer.daemon = True
        self.auto_timer.start()

    def _cancel_auto_timer(self):
        """取消全自动模式的定时器"""
        if self.auto_timer is not None:
            self.auto_timer.cancel()
            self.auto_timer = None


# ============================================================
# GUI 界面类
# ============================================================
class AutoClickerGUI:
    """自动点击器的图形界面"""
    def __init__(self, root):
        self.root = root
        self.root.title("自动点击工具 AutoClicker")
        self.root.geometry("420x360")
        self.root.resizable(False, False)

        # 核心逻辑实例
        self.core = AutoClicker()

        # 创建界面
        self._create_widgets()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """创建GUI控件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ========== 标题 ==========
        title_label = ttk.Label(
            main_frame,
            text="自动点击工具 AutoClicker",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=(0, 15))

        # ========== 模式选择 ==========
        mode_frame = ttk.LabelFrame(main_frame, text="工作模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.mode_var = tk.StringVar(value="semi")
        semi_radio = ttk.Radiobutton(
            mode_frame,
            text="半自动模式 (按下= → 6+右键，松开= → 1)",
            variable=self.mode_var,
            value="semi",
            command=self._on_mode_change
        )
        semi_radio.pack(anchor=tk.W, pady=2)

        auto_radio = ttk.Radiobutton(
            mode_frame,
            text="全自动模式 (按下= → 6+右键，260ms后 → 1)",
            variable=self.mode_var,
            value="auto",
            command=self._on_mode_change
        )
        auto_radio.pack(anchor=tk.W, pady=2)

        # ========== 间隔设置（仅半自动） ==========
        interval_frame = ttk.LabelFrame(main_frame, text="半自动点击间隔", padding="10")
        interval_frame.pack(fill=tk.X, pady=(0, 10))

        interval_row = ttk.Frame(interval_frame)
        interval_row.pack(fill=tk.X)

        ttk.Label(interval_row, text="间隔时间:").pack(side=tk.LEFT, padx=(0, 5))

        self.interval_var = tk.StringVar(value="50")
        interval_entry = ttk.Entry(
            interval_row,
            textvariable=self.interval_var,
            width=8
        )
        interval_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(interval_row, text="毫秒").pack(side=tk.LEFT)

        # 提示信息
        tip_label = ttk.Label(
            interval_frame,
            text="* 按下=触发操作后，必须经过此间隔才能再次触发",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        tip_label.pack(anchor=tk.W, pady=(5, 0))

        # ========== 控制按钮 ==========
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(
            control_frame,
            text="启动监听",
            command=self._on_start,
            width=12
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(
            control_frame,
            text="停止监听",
            command=self._on_stop,
            width=12,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)

        # ========== 状态显示 ==========
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_var = tk.StringVar(value="未启动")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("微软雅黑", 10)
        )
        status_label.pack(anchor=tk.W)

        # 模式状态
        self.mode_status_var = tk.StringVar(value="当前模式: 半自动")
        mode_status_label = ttk.Label(
            status_frame,
            textvariable=self.mode_status_var,
            font=("微软雅黑", 9),
            foreground="gray"
        )
        mode_status_label.pack(anchor=tk.W, pady=(3, 0))

        # ========== 使用说明 ==========
        help_frame = ttk.LabelFrame(main_frame, text="使用说明", padding="10")
        help_frame.pack(fill=tk.X)

        help_text = (
            "1. 选择工作模式（半自动/全自动）\n"
            "2. 半自动模式下设置点击间隔\n"
            "3. 点击「启动监听」开始监听键盘\n"
            "4. 按下键盘上的 = 键触发操作\n"
            "5. 点击「停止监听」或关闭窗口退出"
        )
        help_label = ttk.Label(
            help_frame,
            text=help_text,
            font=("微软雅黑", 9),
            foreground="#333"
        )
        help_label.pack(anchor=tk.W)

        # ========== 底部信息 ==========
        footer_label = ttk.Label(
            main_frame,
            text="提示: 程序需要管理员权限才能监听全局键盘事件",
            foreground="red",
            font=("微软雅黑", 8)
        )
        footer_label.pack(pady=(10, 0))

    def _on_mode_change(self):
        """模式切换回调"""
        mode = self.mode_var.get()
        self.core.set_mode(mode)
        if mode == 'semi':
            self.mode_status_var.set("当前模式: 半自动")
        else:
            self.mode_status_var.set("当前模式: 全自动")

    def _on_start(self):
        """启动按钮回调"""
        # 更新间隔设置
        try:
            interval = int(self.interval_var.get().strip())
            if interval < 0:
                raise ValueError("间隔不能为负数")
            self.core.set_interval(interval)
        except ValueError as e:
            messagebox.showerror("输入错误", f"请输入有效的间隔毫秒数 (非负整数)\n错误: {e}")
            return

        # 启动核心逻辑
        self.core.start()

        # 更新UI状态
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("运行中 (监听 = 键)")
        self.mode_status_var.set(f"当前模式: {'半自动' if self.core.mode == 'semi' else '全自动'}")

        print(f"[启动] 模式: {self.core.mode}, 间隔: {self.core.click_interval_ms}ms")

    def _on_stop(self):
        """停止按钮回调"""
        self.core.stop()

        # 更新UI状态
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("已停止")

        print("[停止] 监听已停止")

    def _on_close(self):
        """窗口关闭回调"""
        self.core.stop()
        self.root.destroy()


# ============================================================
# 主程序入口
# ============================================================
def main():
    """程序入口"""
    # 检查是否以管理员权限运行（仅提示）
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("[警告] 程序未以管理员权限运行，可能无法监听全局键盘事件")
    except:
        pass

    # 启动GUI
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()