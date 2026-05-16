import tkinter as tk
from tkinter import ttk, messagebox

# ================== 枪械数据 ==================
# 属性顺序：垂直后座控制, 水平后座控制, 人机工效, 精准度,
#           腰射稳定, 有效射程, 射速, 弹药威力, 枪口初速, 激发威力, 连发能力, 价钱评分
WEAPONS = [
    # 步枪
    {"name": "AKM", "type": "步枪", "attrs": [50, 45, 45, 55, 40, 70, 60, 75, 65, 75, 100, 80]},
    {"name": "M4A1", "type": "步枪", "attrs": [70, 65, 65, 70, 55, 65, 75, 65, 70, 65, 100, 50]},
    {"name": "FAL", "type": "步枪", "attrs": [30, 30, 40, 70, 35, 80, 55, 90, 80, 90, 100, 30]},
    {"name": "H416", "type": "步枪", "attrs": [80, 75, 70, 75, 65, 70, 80, 65, 75, 70, 100, 20]},
    {"name": "MDR", "type": "步枪", "attrs": [65, 60, 60, 75, 55, 75, 70, 80, 75, 80, 100, 40]},
    {"name": "AK74N", "type": "步枪", "attrs": [65, 60, 55, 60, 45, 65, 65, 60, 65, 60, 100, 70]},
    {"name": "AUG", "type": "步枪", "attrs": [75, 70, 70, 70, 60, 70, 70, 65, 70, 65, 100, 45]},
    {"name": "AR57", "type": "步枪", "attrs": [70, 65, 68, 70, 58, 60, 78, 45, 65, 50, 100, 55]},
    {"name": "ACE31", "type": "步枪", "attrs": [55, 50, 55, 65, 50, 70, 62, 80, 75, 80, 100, 35]},
    {"name": "AEK", "type": "步枪", "attrs": [65, 60, 60, 68, 55, 65, 72, 60, 68, 60, 100, 60]},
    {"name": "AN94", "type": "步枪", "attrs": [60, 55, 65, 75, 50, 75, 65, 60, 70, 65, 100, 65]},
    {"name": "MCX", "type": "步枪", "attrs": [72, 68, 68, 70, 60, 60, 80, 55, 65, 55, 100, 40]},
    {"name": "QBZ191", "type": "步枪", "attrs": [70, 65, 65, 70, 58, 65, 75, 65, 70, 65, 100, 55]},
    {"name": "QBZ192", "type": "步枪", "attrs": [68, 60, 62, 68, 55, 60, 70, 60, 65, 60, 100, 60]},
    {"name": "A545", "type": "步枪", "attrs": [75, 70, 68, 72, 60, 65, 78, 60, 68, 60, 100, 50]},
    # 冲锋枪
    {"name": "MP5", "type": "冲锋枪", "attrs": [80, 75, 60, 60, 65, 40, 80, 40, 50, 40, 100, 85]},
    {"name": "MPX", "type": "冲锋枪", "attrs": [78, 72, 65, 65, 70, 45, 85, 40, 52, 42, 100, 70]},
    {"name": "P90", "type": "冲锋枪", "attrs": [75, 70, 55, 50, 60, 40, 95, 42, 48, 40, 100, 65]},
    {"name": "VECTOR(.45)", "type": "冲锋枪", "attrs": [70, 65, 50, 45, 55, 35, 100, 50, 40, 50, 100, 60]},
    {"name": "VECTOR(9×19)", "type": "冲锋枪", "attrs": [72, 68, 50, 45, 55, 35, 100, 40, 42, 40, 100, 65]},
    # 射手步枪
    {"name": "SVDS", "type": "射手步枪", "attrs": [40, 35, 45, 80, 35, 90, 40, 85, 85, 85, 50, 40]},
    {"name": "VSS", "type": "射手步枪", "attrs": [65, 60, 55, 75, 50, 50, 55, 70, 40, 70, 70, 50]},
    {"name": "MK14", "type": "射手步枪", "attrs": [35, 30, 45, 85, 35, 85, 60, 90, 80, 90, 100, 20]},
    {"name": "M110", "type": "射手步枪", "attrs": [45, 40, 50, 90, 40, 90, 45, 90, 85, 90, 50, 30]},
    {"name": "QBU191", "type": "射手步枪", "attrs": [50, 45, 55, 85, 40, 88, 50, 65, 75, 70, 100, 55]},
    # 栓动步枪
    {"name": "莫辛纳甘", "type": "栓动步枪", "attrs": [20, 15, 30, 95, 15, 100, 10, 85, 85, 90, 10, 75]},
    {"name": "AX50", "type": "栓动步枪", "attrs": [15, 10, 25, 100, 10, 100, 5, 100, 100, 100, 10, 15]},
    {"name": "SJ16", "type": "栓动步枪", "attrs": [18, 12, 28, 98, 12, 100, 8, 100, 95, 100, 10, 20]},
    {"name": "M24", "type": "栓动步枪", "attrs": [25, 20, 32, 92, 18, 95, 12, 75, 80, 80, 10, 65]},
    # 机枪
    {"name": "RPK16", "type": "机枪", "attrs": [55, 45, 48, 55, 40, 70, 65, 60, 65, 60, 100, 70]},
    {"name": "M249", "type": "机枪", "attrs": [40, 35, 40, 45, 30, 65, 80, 65, 70, 65, 100, 45]},
    # 霰弹枪
    {"name": "USAS12", "type": "霰弹枪", "attrs": [30, 25, 35, 20, 20, 30, 60, 70, 30, 80, 100, 85]},
    {"name": "DP12", "type": "霰弹枪", "attrs": [35, 30, 40, 25, 25, 35, 40, 70, 35, 80, 30, 80]},
    # 手枪
    {"name": "G18C", "type": "手枪", "attrs": [60, 55, 45, 40, 50, 25, 90, 30, 35, 30, 100, 95]},
]

ATTR_NAMES = [
    "垂直后座控制", "水平后座控制", "人机工效", "精准度",
    "腰射稳定", "有效射程", "射速", "弹药威力", "枪口初速", "激发威力",
    "连发能力", "价钱评分"
]

# 补充说明文本
HELP_TEXT = """属性解读（满改正向评分 0~100）：
• 垂直后座控制：70以上压枪较简单
• 精准度：20以上满足基本战斗需求
• 腰射稳定：93以上25米内优势明显
• 人机工效：65是手感分水岭，75以上举镜丝滑
• 连发能力：全自动100，半自动50，栓动10
  （QBU191/MK14可全自动，设为100）
• 价钱评分：越高越便宜/性价比越好
  例：G18C(95)、MP5(85)、莫辛纳甘(75)、H416(20)
"""

# ================== 主程序类 ==================
class GunAdvisor:
    def __init__(self, root):
        self.root = root
        self.root.title("暗区突围 改枪评分推荐系统")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        self.weights = [1.0] * len(ATTR_NAMES)
        self.create_widgets()
        self.update_table("全部")

    def create_widgets(self):
        left_frame = ttk.Frame(self.root, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(left_frame, text="选择类别", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(0,5))
        categories = ["全部", "步枪", "冲锋枪", "射手步枪", "栓动步枪", "机枪", "霰弹枪", "手枪"]
        self.category_listbox = tk.Listbox(left_frame, listvariable=tk.StringVar(value=categories),
                                           height=8, exportselection=False)
        self.category_listbox.pack(fill=tk.X, pady=5)
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_change)

        # 帮助按钮
        ttk.Button(left_frame, text="查看数值说明", command=self.show_help).pack(fill=tk.X, pady=5)

        ttk.Label(left_frame, text="权重设置 (0~10)", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=(20,5))

        weight_canvas = tk.Canvas(left_frame, borderwidth=0, height=400)
        weight_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=weight_canvas.yview)
        self.weight_frame = ttk.Frame(weight_canvas)
        self.weight_frame.bind("<Configure>",
                               lambda e: weight_canvas.configure(scrollregion=weight_canvas.bbox("all")))
        weight_canvas.create_window((0, 0), window=self.weight_frame, anchor="nw")
        weight_canvas.configure(yscrollcommand=weight_scrollbar.set)
        weight_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        weight_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.weight_scales = []
        for i, name in enumerate(ATTR_NAMES):
            frame = ttk.Frame(self.weight_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=name, width=12, anchor=tk.W).pack(side=tk.LEFT)
            scale_var = tk.DoubleVar(value=1.0)
            scale = ttk.Scale(frame, from_=0, to=10, variable=scale_var, orient=tk.HORIZONTAL)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            value_label = ttk.Label(frame, text="1.0", width=4)
            value_label.pack(side=tk.RIGHT)
            scale_var.trace_add("write", lambda *args, v=scale_var, l=value_label: l.configure(text=f"{v.get():.1f}"))
            self.weight_scales.append(scale_var)

        ttk.Button(left_frame, text="应用权重并重新计算", command=self.apply_weights).pack(fill=tk.X, pady=15)

        right_frame = ttk.Frame(self.root, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        table_frame = ttk.Frame(right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ["name", "type"] + [f"attr{i}" for i in range(len(ATTR_NAMES))] + ["score"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        self.tree.heading("name", text="枪械名称")
        self.tree.column("name", width=100, anchor=tk.CENTER)
        self.tree.heading("type", text="类别")
        self.tree.column("type", width=80, anchor=tk.CENTER)
        for i, name in enumerate(ATTR_NAMES):
            col = f"attr{i}"
            self.tree.heading(col, text=name)
            self.tree.column(col, width=70, anchor=tk.CENTER)
        self.tree.heading("score", text="综合评分")
        self.tree.column("score", width=90, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def show_help(self):
        """弹出属性说明窗口"""
        messagebox.showinfo("数值说明", HELP_TEXT)

    def on_category_change(self, event):
        selection = self.category_listbox.curselection()
        if selection:
            category = self.category_listbox.get(selection[0])
            self.update_table(category)

    def apply_weights(self):
        for i, var in enumerate(self.weight_scales):
            self.weights[i] = var.get()
        selection = self.category_listbox.curselection()
        category = "全部"
        if selection:
            category = self.category_listbox.get(selection[0])
        self.update_table(category)

    def update_table(self, category):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if category == "全部":
            filtered = WEAPONS
        else:
            filtered = [w for w in WEAPONS if w["type"] == category]
        scored = []
        for gun in filtered:
            total = sum(a * w for a, w in zip(gun["attrs"], self.weights))
            scored.append((total, gun))
        scored.sort(key=lambda x: x[0], reverse=True)
        for total, gun in scored:
            values = [gun["name"], gun["type"]] + gun["attrs"] + [f"{total:.1f}"]
            self.tree.insert("", tk.END, values=values)


if __name__ == "__main__":
    root = tk.Tk()
    app = GunAdvisor(root)
    root.mainloop()
