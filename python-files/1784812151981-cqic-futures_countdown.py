# -*- coding: utf-8 -*-
"""
股指期货交割日倒计时桌面小工具
功能：实时显示 IF/IH/IC/IM/A50 距离下一个交割日的剩余天数
"""

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import date, datetime


# ========== 交割日计算 ==========
def get_third_friday(year: int, month: int) -> date:
    """获取指定年月的第三个周五"""
    cal = calendar.monthcalendar(year, month)
    # 第一周如果包含周五，则是第一个周五；否则第二周是第一个
    if cal[0][calendar.FRIDAY] != 0:
        return date(year, month, cal[2][calendar.FRIDAY])
    else:
        return date(year, month, cal[3][calendar.FRIDAY])


def get_next_delivery_date(today: date = None) -> date:
    """获取下一个交割日（每月第三个周五）"""
    if today is None:
        today = date.today()
    current_delivery = get_third_friday(today.year, today.month)
    if today <= current_delivery:
        return current_delivery
    # 本月已过交割日，取下月
    if today.month == 12:
        return get_third_friday(today.year + 1, 1)
    else:
        return get_third_friday(today.year, today.month + 1)


def days_until(delivery_date: date, today: date = None) -> int:
    """计算距离交割日的天数"""
    if today is None:
        today = date.today()
    return (delivery_date - today).days


# ========== 主程序 ==========
class FuturesCountdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股指期货交割日倒计时")

        # 窗口设置：无边框、置顶、透明
        self.root.overrideredirect(True)  # 无边框
        self.root.attributes("-topmost", True)  # 始终置顶
        self.root.attributes("-alpha", 0.9)  # 透明度
        self.root.configure(bg="#1a1a2e")

        # 品种配置
        self.futures = {
            "IF": {"name": "沪深300", "color": "#ff6b6b", "enabled": True},
            "IH": {"name": "上证50", "color": "#4ecdc4", "enabled": True},
            "IC": {"name": "中证500", "color": "#ffe66d", "enabled": True},
            "IM": {"name": "中证1000", "color": "#a8e6cf", "enabled": True},
            "A50": {"name": "富时A50", "color": "#c9b1ff", "enabled": True},
        }

        # 置顶状态
        self.topmost = True

        # 拖动相关
        self.drag_data = {"x": 0, "y": 0}

        # 构建UI
        self._build_ui()
        self._build_menu()
        self._bind_events()

        # 初始位置（屏幕右上角）
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_w - 220}+80")

        # 启动定时刷新
        self._refresh_countdown()
        self._schedule_refresh()

    def _build_ui(self):
        """构建界面"""
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#16213e", height=28)
        title_frame.pack(fill="x", side="top")
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="📅 交割日倒计时",
            bg="#16213e",
            fg="#e0e0e0",
            font=("微软雅黑", 10, "bold"),
        )
        title_label.pack(side="left", padx=10, pady=4)

        # 内容区
        self.content_frame = tk.Frame(self.root, bg="#1a1a2e")
        self.content_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # 各品种行（动态创建）
        self.row_widgets = {}
        for code in ["IF", "IH", "IC", "IM", "A50"]:
            info = self.futures[code]
            row = tk.Frame(self.content_frame, bg="#1a1a2e")
            row.pack(fill="x", pady=3)

            # 左侧代码 + 名称
            left_frame = tk.Frame(row, bg="#1a1a2e")
            left_frame.pack(side="left")

            code_label = tk.Label(
                left_frame,
                text=code,
                bg="#1a1a2e",
                fg=info["color"],
                font=("Consolas", 12, "bold"),
                width=4,
                anchor="w",
            )
            code_label.pack(side="left")

            name_label = tk.Label(
                left_frame,
                text=info["name"],
                bg="#1a1a2e",
                fg="#aaaaaa",
                font=("微软雅黑", 9),
            )
            name_label.pack(side="left", padx=(4, 0))

            # 右侧天数
            days_label = tk.Label(
                row,
                text="-- 天",
                bg="#1a1a2e",
                fg=info["color"],
                font=("Consolas", 12, "bold"),
                anchor="e",
            )
            days_label.pack(side="right")

            self.row_widgets[code] = {"row": row, "days_label": days_label}

        # 底部日期提示
        self.date_label = tk.Label(
            self.content_frame,
            text="",
            bg="#1a1a2e",
            fg="#666666",
            font=("微软雅黑", 8),
        )
        self.date_label.pack(fill="x", pady=(6, 2))

    def _build_menu(self):
        """构建右键菜单"""
        self.menu = tk.Menu(self.root, tearoff=0)

        # 品种子菜单
        self.futures_menu = tk.Menu(self.menu, tearoff=0)
        self.futures_var = {}
        for code in ["IF", "IH", "IC", "IM", "A50"]:
            var = tk.BooleanVar(value=self.futures[code]["enabled"])
            self.futures_var[code] = var
            self.futures_menu.add_checkbutton(
                label=f"{code} {self.futures[code]['name']}",
                variable=var,
                command=lambda c=code: self._toggle_future(c),
            )
        self.menu.add_cascade(label="显示品种", menu=self.futures_menu)

        self.menu.add_separator()

        # 置顶开关
        self.topmost_var = tk.BooleanVar(value=True)
        self.menu.add_checkbutton(
            label="始终置顶",
            variable=self.topmost_var,
            command=self._toggle_topmost,
        )

        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.quit)

    def _bind_events(self):
        """绑定事件"""
        # 拖动窗口
        for widget in [self.root] + [w for w in self.root.winfo_children()]:
            widget.bind("<Button-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            # 递归绑定子控件
            self._bind_drag_recursive(widget)

        # 右键菜单
        self.root.bind("<Button-3>", self._show_menu)
        for widget in self.root.winfo_children():
            widget.bind("<Button-3>", self._show_menu)
            self._bind_rightclick_recursive(widget)

    def _bind_drag_recursive(self, parent):
        """递归绑定拖动事件"""
        for child in parent.winfo_children():
            child.bind("<Button-1>", self._start_drag)
            child.bind("<B1-Motion>", self._on_drag)
            self._bind_drag_recursive(child)

    def _bind_rightclick_recursive(self, parent):
        """递归绑定右键事件"""
        for child in parent.winfo_children():
            child.bind("<Button-3>", self._show_menu)
            self._bind_rightclick_recursive(child)

    def _start_drag(self, event):
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _toggle_future(self, code):
        """切换品种显示"""
        self.futures[code]["enabled"] = self.futures_var[code].get()
        if self.futures[code]["enabled"]:
            self.row_widgets[code]["row"].pack(fill="x", pady=3)
        else:
            self.row_widgets[code]["row"].pack_forget()

    def _toggle_topmost(self):
        """切换置顶状态"""
        self.topmost = self.topmost_var.get()
        self.root.attributes("-topmost", self.topmost)

    def _refresh_countdown(self):
        """刷新倒计时数据"""
        today = date.today()
        next_delivery = get_next_delivery_date(today)
        days = days_until(next_delivery, today)

        # 更新各品种显示（国内四大股指 + A50 都是每月第三个周五）
        for code in ["IF", "IH", "IC", "IM", "A50"]:
            label = self.row_widgets[code]["days_label"]
            if days == 0:
                label.config(text="今天交割", fg="#ff4757")
            elif days == 1:
                label.config(text="明天交割", fg="#ffa502")
            else:
                label.config(text=f"{days} 天")

        # 更新底部日期
        weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        wd = weekday_cn[next_delivery.weekday()]
        self.date_label.config(
            text=f"下一交割日：{next_delivery.strftime('%Y-%m-%d')} {wd}"
        )

    def _schedule_refresh(self):
        """定时刷新（每小时检查一次，跨天自动更新）"""
        self._refresh_countdown()
        self.root.after(3600000, self._schedule_refresh)  # 1小时


def main():
    root = tk.Tk()
    app = FuturesCountdownApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
