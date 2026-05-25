import tkinter as tk
from tkinter import ttk

class GameCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏计算器")
        self.root.geometry("430x620")  # 窗口加大
        self.root.resizable(False, False)
        self.root.configure(bg='#0f172a')  # 更深邃的底色

        # 置顶状态
        self.topmost = False

        # 变量
        self.position_var = tk.StringVar(value="")
        self.red_var = tk.StringVar()
        self.bottom_red_var = tk.StringVar()
        self.open_red_var = tk.StringVar()
        self.result_var = tk.StringVar(value="0 万")

        # 存储仓位按钮对象，用于手动高亮
        self.pos_buttons = []

        self.build_ui()
        # 初始化一下高亮
        self.update_position_highlight()

    def build_ui(self):
        # ---------- 顶部标题栏 ----------
        title_bar = tk.Frame(self.root, bg='#0f172a')
        title_bar.pack(fill='x', padx=20, pady=(20, 5))

        title = tk.Label(title_bar, text="⚔️ 游戏计算器",
                         font=("Microsoft YaHei", 20, "bold"),
                         bg='#0f172a', fg='#e2e8f0')
        title.pack(side='left')

        # 置顶按钮
        self.pin_btn = tk.Button(title_bar, text="📌 置顶(关)",
                                 font=("Microsoft YaHei", 9),
                                 bg='#334155', fg='#cbd5e1',
                                 relief='flat', bd=0,
                                 activebackground='#475569',
                                 activeforeground='white',
                                 command=self.toggle_topmost)
        self.pin_btn.pack(side='right', padx=5)

        # ---------- 仓位选择（高亮卡片式） ----------
        pos_frame = tk.LabelFrame(self.root, text="📦 仓位选择",
                                  font=("Microsoft YaHei", 11, "bold"),
                                  bg='#0f172a', fg='#94a3b8',
                                  padx=15, pady=15, bd=0,
                                  highlightbackground='#1e293b',
                                  highlightthickness=1)
        pos_frame.pack(pady=(15, 10), padx=20, fill='x')

        # 三个仓位按钮
        positions = [
            ("半仓", "10万", "100000"),
            ("满仓", "20万", "200000"),
            ("超大仓", "30万", "300000")
        ]
        for name, display, value in positions:
            # 使用 indicatoron=0 的 Radiobutton 做成卡片
            btn = tk.Radiobutton(
                pos_frame,
                text=f"{name}\n{display}",
                variable=self.position_var,
                value=value,
                font=("Microsoft YaHei", 11, "bold"),
                bg='#1e293b',          # 默认背景
                fg='#cbd5e1',          # 默认文字
                selectcolor='#0f172a', # 选中时的小圆点颜色（不显示圆点）
                indicatoron=0,         # 去掉圆点，整体可点击
                relief='flat',
                bd=2,
                padx=10, pady=8,
                activebackground='#334155',
                activeforeground='white',
                command=lambda: self.on_position_change(),
                justify='center'
            )
            btn.pack(side='left', expand=True, fill='x', padx=3, pady=3)
            self.pos_buttons.append(btn)

        # ---------- 参数输入 ----------
        input_frame = tk.LabelFrame(self.root, text="📝 参数输入",
                                    font=("Microsoft YaHei", 11, "bold"),
                                    bg='#0f172a', fg='#94a3b8',
                                    padx=15, pady=15, bd=0,
                                    highlightbackground='#1e293b',
                                    highlightthickness=1)
        input_frame.pack(pady=10, padx=20, fill='x')

        # 三个输入项
        fields = [
            ("🔴 红（数量）", self.red_var),
            ("🔻 底红（数量）", self.bottom_red_var),
            ("💰 明红价值", self.open_red_var)
        ]
        for label_text, var in fields:
            lbl = tk.Label(input_frame, text=label_text,
                           font=("Microsoft YaHei", 10),
                           bg='#0f172a', fg='#cbd5e1')
            lbl.pack(anchor='w', pady=(8, 2))
            entry = tk.Entry(input_frame, textvariable=var,
                             font=("Microsoft YaHei", 13),
                             bg='#1e293b', fg='white',
                             insertbackground='white',
                             relief='flat', bd=6,
                             highlightthickness=0)
            entry.pack(fill='x', ipady=4)
            # 绑定输入变化
            var.trace_add('write', lambda *args: self.update_result())

        # 重置按钮
        reset_btn = tk.Button(input_frame, text="🔄 重置输入框",
                              font=("Microsoft YaHei", 10, "bold"),
                              bg='#334155', fg='#e2e8f0',
                              relief='flat', bd=0,
                              activebackground='#475569',
                              activeforeground='white',
                              padx=10, pady=8,
                              command=self.reset_inputs)
        reset_btn.pack(fill='x', pady=(12, 5))

        # ---------- 结果展示 ----------
        result_frame = tk.Frame(self.root, bg='#0f172a',
                                highlightbackground='#f59e0b',
                                highlightthickness=2,
                                bd=0)
        result_frame.pack(pady=20, padx=30, fill='x', ipady=15)

        result_label = tk.Label(result_frame, text="计算结果",
                                font=("Microsoft YaHei", 11),
                                bg='#0f172a', fg='#fbbf24')
        result_label.pack(pady=(15, 5))

        result_display = tk.Label(result_frame, textvariable=self.result_var,
                                  font=("Microsoft YaHei", 32, "bold"),
                                  bg='#0f172a', fg='#fbbf24')
        result_display.pack(pady=(0, 15))

    def toggle_topmost(self):
        self.topmost = not self.topmost
        self.root.attributes('-topmost', self.topmost)
        self.pin_btn.config(text="📌 置顶(开)" if self.topmost else "📌 置顶(关)")

    def on_position_change(self):
        """仓位切换时更新高亮和结果"""
        self.update_position_highlight()
        self.update_result()

    def update_position_highlight(self):
        """根据选中的仓位，手动设置按钮背景/前景色"""
        selected_val = self.position_var.get()
        for btn in self.pos_buttons:
            if btn['value'] == selected_val:
                btn.configure(bg='#f59e0b', fg='#0f172a',
                              activebackground='#fbbf24', activeforeground='#0f172a')
            else:
                btn.configure(bg='#1e293b', fg='#cbd5e1',
                              activebackground='#334155', activeforeground='white')

    def get_position_value(self):
        val = self.position_var.get()
        return int(val) if val else 0

    def get_entry_value(self, var):
        s = var.get().strip()
        if s == '':
            return 0
        try:
            return float(s)
        except ValueError:
            return 0

    def calculate(self):
        pos = self.get_position_value()
        red = self.get_entry_value(self.red_var)
        bot = self.get_entry_value(self.bottom_red_var)
        open_red = self.get_entry_value(self.open_red_var)
        total_yuan = round(pos + red * 200000 + bot * 300000 + open_red)
        return total_yuan

    def format_wan(self, total_yuan):
        yuan_str = str(total_yuan)
        if len(yuan_str) > 4:
            int_part = yuan_str[:-4]
            frac_part = yuan_str[-4:]
        else:
            int_part = '0'
            frac_part = yuan_str.zfill(4)

        wan_str = int_part + '.' + frac_part
        wan_str = wan_str.rstrip('0').rstrip('.')
        digits = wan_str.replace('.', '')

        if len(digits) <= 5:
            return wan_str + " 万"

        top5 = digits[:5]
        dot_pos = wan_str.find('.')
        if dot_pos == -1:
            return top5 + " 万"
        if dot_pos >= 5:
            return top5 + " 万"

        int_top = top5[:dot_pos]
        frac_top = top5[dot_pos:]
        return int_top + '.' + frac_top + " 万"

    def update_result(self, *args):
        total = self.calculate()
        text = self.format_wan(total)
        self.result_var.set(text)

    def reset_inputs(self):
        self.red_var.set('')
        self.bottom_red_var.set('')
        self.open_red_var.set('')
        self.update_result()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameCalculator(root)
    root.mainloop()