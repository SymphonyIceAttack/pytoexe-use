import tkinter as tk
from tkinter import ttk
import math

class GameCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏计算器")
        self.root.geometry("380x520")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')

        # 窗口置顶状态
        self.topmost = False

        # 变量
        self.position_var = tk.StringVar(value="")
        self.red_var = tk.StringVar()
        self.bottom_red_var = tk.StringVar()
        self.open_red_var = tk.StringVar()
        self.result_var = tk.StringVar(value="0 万")

        self.build_ui()

    def build_ui(self):
        # 标题
        title = tk.Label(self.root, text="⚔️ 游戏计算器", font=("Microsoft YaHei", 18, "bold"),
                         bg='#1a1a2e', fg='#e0e0e0')
        title.pack(pady=15)

        # 置顶按钮
        self.pin_btn = tk.Button(self.root, text="📌 置顶(关)", font=("Microsoft YaHei", 9),
                                 bg='#334155', fg='#cbd5e1', relief='flat',
                                 activebackground='#475569', activeforeground='white',
                                 command=self.toggle_topmost)
        self.pin_btn.place(x=300, y=15, width=70, height=28)

        # 仓位选择
        frame_pos = tk.LabelFrame(self.root, text="📦 仓位选择", font=("Microsoft YaHei", 11, "bold"),
                                  bg='#1a1a2e', fg='#94a3b8', padx=10, pady=10)
        frame_pos.pack(pady=10, padx=20, fill='x')

        positions = [("半仓 10万", "100000"), ("满仓 20万", "200000"), ("超大仓 30万", "300000")]
        for text, value in positions:
            rb = tk.Radiobutton(frame_pos, text=text, variable=self.position_var, value=value,
                                font=("Microsoft YaHei", 11), bg='#1a1a2e', fg='#cbd5e1',
                                selectcolor='#1a1a2e', activebackground='#1a1a2e',
                                activeforeground='#f59e0b',
                                indicatoron=0, padx=10, pady=5,
                                command=self.update_result)
            rb.pack(side='left', expand=True, fill='x', padx=2)

        # 输入框区域
        frame_input = tk.LabelFrame(self.root, text="📝 参数输入", font=("Microsoft YaHei", 11, "bold"),
                                    bg='#1a1a2e', fg='#94a3b8', padx=15, pady=15)
        frame_input.pack(pady=10, padx=20, fill='x')

        fields = [
            ("🔴 红（数量）", self.red_var),
            ("🔻 底红（数量）", self.bottom_red_var),
            ("💰 明红价值", self.open_red_var)
        ]
        for label_text, var in fields:
            lbl = tk.Label(frame_input, text=label_text, font=("Microsoft YaHei", 10),
                           bg='#1a1a2e', fg='#cbd5e1')
            lbl.pack(anchor='w')
            entry = tk.Entry(frame_input, textvariable=var, font=("Microsoft YaHei", 12),
                             bg='#1e293b', fg='white', insertbackground='white',
                             relief='flat', bd=5)
            entry.pack(fill='x', pady=(2, 8))
            var.trace_add('write', lambda *args: self.update_result())

        # 重置按钮
        reset_btn = tk.Button(frame_input, text="🔄 重置输入框", font=("Microsoft YaHei", 10),
                              bg='#334155', fg='#cbd5e1', relief='flat',
                              activebackground='#475569', activeforeground='white',
                              command=self.reset_inputs)
        reset_btn.pack(fill='x', pady=5)

        # 结果展示
        result_frame = tk.Frame(self.root, bg='#1a1a2e')
        result_frame.pack(pady=15)

        result_label = tk.Label(result_frame, text="计算结果", font=("Microsoft YaHei", 10),
                                bg='#1a1a2e', fg='#fbbf24')
        result_label.pack()

        result_display = tk.Label(result_frame, textvariable=self.result_var,
                                  font=("Microsoft YaHei", 28, "bold"),
                                  bg='#1a1a2e', fg='#fbbf24')
        result_display.pack()

    def toggle_topmost(self):
        self.topmost = not self.topmost
        self.root.attributes('-topmost', self.topmost)
        self.pin_btn.config(text="📌 置顶(开)" if self.topmost else "📌 置顶(关)")

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

    def update_result(self):
        total = self.calculate()
        text = self.format_wan(total)
        self.result_var.set(text)

    def reset_inputs(self):
        self.red_var.set('')
        self.bottom_red_var.set('')
        self.open_red_var.set('')
        # 仓位不重置，保持原样
        self.update_result()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameCalculator(root)
    root.mainloop()