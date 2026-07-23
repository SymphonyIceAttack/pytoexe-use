import tkinter as tk
from tkinter import Menu, BooleanVar
import datetime

# 品种列表（显示顺序）
VARIETIES = ['IF', 'IH', 'IC', 'IM', 'A50']
BG_COLOR = '#f0f0f0'          # 透明色（该颜色将完全透明）
FONT = ('Microsoft YaHei', 12, 'bold')

class TransparentWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("股指期货交割日倒计时")
        self.root.overrideredirect(True)                     # 无边框
        self.root.attributes('-topmost', True)              # 始终置顶
        self.root.configure(bg=BG_COLOR)
        self.root.attributes('-transparentcolor', BG_COLOR) # 背景透明

        # 存储每个品种的显示状态（勾选）
        self.show_vars = {v: BooleanVar(value=True) for v in VARIETIES}

        # 创建标签（每个品种一行）
        self.labels = {}
        for v in VARIETIES:
            lbl = tk.Label(
                root, text=f"{v}: -- 天", font=FONT,
                bg=BG_COLOR, fg='#000000'   # 文字黑色，背景透明
            )
            lbl.pack(anchor='w', padx=10, pady=2)
            self.labels[v] = lbl

        # 右键菜单
        self.menu = Menu(root, tearoff=0)
        for v in VARIETIES:
            self.menu.add_checkbutton(
                label=v, variable=self.show_vars[v],
                command=self.update_visibility
            )
        self.menu.add_separator()
        self.menu.add_command(label="置顶（切换）", command=self.toggle_topmost)
        self.menu.add_command(label="退出", command=self.quit)

        # 绑定鼠标事件
        self.root.bind('<Button-3>', self.show_menu)          # 右键显示菜单
        self.root.bind('<Button-1>', self.start_move)         # 左键按下开始拖动
        self.root.bind('<B1-Motion>', self.on_move)           # 拖动移动
        self.root.bind('<ButtonRelease-1>', self.stop_move)

        # 拖动数据
        self.drag_data = {'x': 0, 'y': 0}

        # 首次更新倒计时，并启动定时更新（每分钟刷新）
        self.update_counts()

    # ---------- 日期计算 ----------
    @staticmethod
    def get_third_friday(year, month):
        """返回指定年月的第三个周五的日期"""
        first_day = datetime.date(year, month, 1)
        # 周五的 weekday = 4（周一=0）
        offset = (4 - first_day.weekday()) % 7
        first_friday = first_day + datetime.timedelta(days=offset)
        third_friday = first_friday + datetime.timedelta(days=14)
        return third_friday

    def get_next_futures_date(self, today):
        """从今天开始查找最近的第三个周五（交割日）"""
        year, month = today.year, today.month
        while True:
            third_fri = self.get_third_friday(year, month)
            if third_fri >= today:
                return third_fri
            month += 1
            if month > 12:
                month = 1
                year += 1

    # ---------- 更新显示 ----------
    def update_counts(self):
        today = datetime.date.today()
        next_date = self.get_next_futures_date(today)
        days = (next_date - today).days

        for v in VARIETIES:
            if self.show_vars[v].get():
                self.labels[v].config(text=f"{v}: {days} 天")
            else:
                self.labels[v].config(text="")   # 不显示

        # 每分钟更新一次（60,000 毫秒）
        self.root.after(60000, self.update_counts)

    def update_visibility(self):
        """菜单勾选变化时，立即刷新显示（调用 update_counts 会统一更新）"""
        self.update_counts()

    # ---------- 鼠标拖动 ----------
    def start_move(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y

    def on_move(self, event):
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        self.drag_data['x'] = 0
        self.drag_data['y'] = 0

    # ---------- 右键菜单 ----------
    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def toggle_topmost(self):
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)

    def quit(self):
        self.root.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TransparentWindow(root)
    root.mainloop()