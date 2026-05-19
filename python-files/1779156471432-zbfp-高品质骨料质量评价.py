import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import matplotlib.pyplot as plt

# ==================== 数据定义 ====================
mechanism_sand = [
    ("级配 (累计筛余超出值总和, %)", [2, 3, 4, 5], 5, 5, 0.0909, 'lower', (0, 10)),
    ("细度模数 (波动性)", [0.08, 0.1, 0.13, 0.15], 0.1, 0.15, 0.0844, 'lower', (0.05, 0.20)),
    ("松散堆积空隙率 (%)", [40, 41, 42, 43], 41, 43, 0.0909, 'lower', (38, 45)),
    ("亚甲蓝 (MB) 值 (g/kg)", [0.5, 0.8, 1.0, 1.2], 0.8, 1.2, 0.0909, 'lower', (0, 2)),
    ("石粉含量 (波动性, %)", [0.8, 1.0, 1.2, 1.5], 1.0, 1.5, 0.0779, 'lower', (0, 3)),
    ("片状颗粒含量 (%)", [4, 5, 7, 8], 5, 8, 0.0844, 'lower', (0, 10)),
    ("硫化物及硫酸盐含量 (%)", [0, 0.2, 0.25, 0.5], 0.5, 0.5, 0.0714, 'lower', (0, 1)),
    ("云母含量 (%)", [0.5, 1.0, 1.5, 2.0], 1.0, 2.0, 0.0714, 'lower', (0, 3)),
    ("泥块含量 (%)", [0, 0.1, 0.15, 0.2], 0, 0.2, 0.0649, 'lower', (0, 0.5)),
    ("坚固性 (%)", [3, 5, 7, 8], 5, 8, 0.0779, 'lower', (0, 10)),
    ("单级压碎指标 (%)", [15, 16, 18, 20], 20, 20, 0.0649, 'lower', (10, 25)),
    ("吸水率 (%)", [0.5, 1.0, 2.0, 2.5], 2.0, 2.5, 0.0584, 'lower', (0, 3)),
    ("含水率 (波动性, %)", [0.7, 0.8, 0.9, 1.0], 1.0, 1.0, 0.0714, 'lower', (0, 2))
]

coarse_aggregate = [
    ("针片状含量 (%)", [2, 3, 4, 5], 5, 5, 0.1261, 'lower', (0, 10)),
    ("连续松散堆积空隙率 (%)", [41, 42, 43, 44], 43, 44, 0.1261, 'lower', (38, 48)),
    ("不规则颗粒含量 (%)", [3, 5, 8, 10], 5, 10, 0.1261, 'lower', (0, 15)),
    ("吸水率 (%)", [0.5, 1.0, 1.5, 2.0], 1.0, 2.0, 0.0811, 'lower', (0, 3)),
    ("压碎指标 (%)", [8, 10, 15, 20], 10, 20, 0.0811, 'lower', (0, 30)),
    ("坚固性 (%)", [2, 3, 4, 5], 5, 5, 0.1081, 'lower', (0, 8)),
    ("表观密度 (kg/m³)", [2700, 2650, 2600, 2550], 2600, 2550, 0.0541, 'higher', (2500, 2800)),
    ("泥粉含量 (%)", [0.1, 0.5, 1.0, 1.5], 0.5, 1.5, 0.1081, 'lower', (0, 2)),
    ("硫化物及硫酸盐含量 (%)", [0, 0.2, 0.35, 0.5], 0.5, 0.5, 0.0991, 'lower', (0, 1)),
    ("泥块含量 (%)", [0, 0.03, 0.06, 0.1], 0, 0.1, 0.0901, 'lower', (0, 0.2))
]

# ==================== 评分核心函数 ====================
def get_score(value, thresholds, direction):
    if value is None:
        return 0
    if direction == 'lower':
        if value <= thresholds[0]:
            return 1.0
        elif value <= thresholds[1]:
            return 0.9
        elif value <= thresholds[2]:
            return 0.8
        elif value <= thresholds[3]:
            return 0.7
        else:
            return 0.0
    else:
        if value >= thresholds[0]:
            return 1.0
        elif value >= thresholds[1]:
            return 0.9
        elif value >= thresholds[2]:
            return 0.8
        elif value >= thresholds[3]:
            return 0.7
        else:
            return 0.0

def check_grade(value, limit, direction):
    if value is None:
        return False
    if direction == 'lower':
        return value <= limit
    else:
        return value >= limit

def evaluate(material_data, input_values):
    total_score = 0.0
    a_fail = 0
    b_fail = 0
    for i, (name, thresh, a_limit, b_limit, weight, direction, _) in enumerate(material_data):
        val = input_values[i]
        if val is None:
            score = 0
            a_ok = False
            b_ok = False
        else:
            score = get_score(val, thresh, direction)
            a_ok = check_grade(val, a_limit, direction)
            b_ok = check_grade(val, b_limit, direction)
            if not a_ok:
                a_fail += 1
            if not b_ok:
                b_fail += 1
        total_score += score * weight
    if a_fail == 0:
        grade = "A级"
    elif b_fail == 0:
        grade = "B级"
    else:
        grade = "不合格"
    return total_score, grade

# ==================== GUI 主程序 ====================
class AggregateApp:
    def __init__(self, root):
        self.root = root
        root.title("高品质骨料质量评价系统")
        root.geometry("1350x900")
        self.current_font_size = 12
        self.setup_styles()
        self.create_menu()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # 机制砂单页
        self.sand_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sand_frame, text="机制砂 (单次评价)")
        self.create_eval_page(self.sand_frame, mechanism_sand, "sand")

        # 粗骨料单页
        self.coarse_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.coarse_frame, text="粗骨料 (单次评价)")
        self.create_eval_page(self.coarse_frame, coarse_aggregate, "coarse")

        # 批量评价页
        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="批量评价 (多工程)")
        self.create_batch_page()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("Treeview", font=('微软雅黑', self.current_font_size), rowheight=28, borderwidth=1, relief='solid')
        self.style.configure("Treeview.Heading", font=('微软雅黑', self.current_font_size, 'bold'))
        self.style.configure("TLabel", font=('微软雅黑', self.current_font_size))
        self.style.configure("TButton", font=('微软雅黑', self.current_font_size))
        self.style.configure("TEntry", font=('微软雅黑', self.current_font_size))
        self.style.configure("TNotebook.Tab", font=('微软雅黑', self.current_font_size))
        self.style.configure("TLabelframe.Label", font=('微软雅黑', self.current_font_size, 'bold'))

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        for size in [10,12,14,16]:
            view_menu.add_command(label=f"字体大小 {size}", command=lambda s=size: self.set_font_size(s))

    def set_font_size(self, size):
        self.current_font_size = size
        self.style.configure("Treeview", font=('微软雅黑', size), rowheight=size+16)
        self.style.configure("Treeview.Heading", font=('微软雅黑', size, 'bold'))
        self.style.configure("TLabel", font=('微软雅黑', size))
        self.style.configure("TButton", font=('微软雅黑', size))
        self.style.configure("TEntry", font=('微软雅黑', size))
        self.style.configure("TNotebook.Tab", font=('微软雅黑', size))
        self.style.configure("TLabelframe.Label", font=('微软雅黑', size, 'bold'))
        self.update_widget_fonts()

    def update_widget_fonts(self):
        font = ('微软雅黑', self.current_font_size)
        # 单次评价页面更新（略）
        if hasattr(self, 'batch_tree'):
            pass  # 字体样式由 style 控制

    # ------------------ 单次评价页面 ------------------
    def create_eval_page(self, parent, material_data, tag):
        left_frame = ttk.LabelFrame(parent, text="实测值输入", width=450)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        entries = []
        for i, item in enumerate(material_data):
            name = item[0]
            lbl = tk.Label(left_frame, text=name, font=('微软雅黑', self.current_font_size))
            lbl.grid(row=i, column=0, sticky='w', padx=5, pady=2)
            var = tk.StringVar()
            entry = tk.Entry(left_frame, textvariable=var, width=15, font=('微软雅黑', self.current_font_size))
            entry.grid(row=i, column=1, padx=5, pady=2)
            entries.append((var, entry))

        right_frame = ttk.LabelFrame(parent, text="评价结果")
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        hint_label = tk.Label(right_frame, text="", fg="blue", wraplength=350, justify='left',
                              font=('微软雅黑', self.current_font_size))
        hint_label.pack(side='top', fill='x', padx=5, pady=2)

        tree_frame = ttk.Frame(right_frame)
        tree_frame.pack(fill='both', expand=True)
        columns = ("指标名称", "实测值", "单项得分", "A级符合", "B级符合")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15, style="Treeview")
        for col in columns:
            tree.heading(col, text=col)
            if col == "指标名称":
                tree.column(col, width=300, anchor='w')
            else:
                tree.column(col, width=100, anchor='center')
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(side='left', fill='both', expand=True)

        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill='x', pady=10)
        score_label = tk.Label(bottom_frame, text="", font=('微软雅黑', self.current_font_size+2, 'bold'), fg='#2c3e50')
        score_label.pack(side='top', pady=2)
        grade_label = tk.Label(bottom_frame, text="", font=('微软雅黑', self.current_font_size+2, 'bold'), fg='#2c3e50')
        grade_label.pack(side='top', pady=2)

        btn_row = ttk.Frame(bottom_frame)
        btn_row.pack(side='bottom', pady=5)
        export_btn = ttk.Button(btn_row, text="导出结果 (Excel)", command=lambda: self.export_single(tree, score_label, grade_label))
        export_btn.pack(side='left', padx=5)
        radar_btn = ttk.Button(btn_row, text="绘制雷达图", command=lambda: self.plot_radar(tree, score_label))
        radar_btn.pack(side='left', padx=5)

        def on_focus_in(event, name, minv, maxv):
            hint_label.config(text=f"当前指标：{name}\n建议范围：{minv} ~ {maxv}")

        def on_focus_out(event, var, entry, minv, maxv):
            hint_label.config(text="")
            raw = var.get().strip()
            if raw == "":
                entry.config(bg="white")
                return
            try:
                val = float(raw)
                if (minv is not None and val < minv) or (maxv is not None and val > maxv):
                    entry.config(bg="#ffcccc")
                else:
                    entry.config(bg="white")
            except ValueError:
                entry.config(bg="#ffcccc")

        for i, (var, entry) in enumerate(entries):
            name, _, _, _, _, _, (minv, maxv) = material_data[i]
            entry.bind("<FocusIn>", lambda e, n=name, mn=minv, mx=maxv: on_focus_in(e, n, mn, mx))
            entry.bind("<FocusOut>", lambda e, v=var, en=entry, mn=minv, mx=maxv: on_focus_out(e, v, en, mn, mx))

        def compute():
            for row in tree.get_children():
                tree.delete(row)
            values = []
            for var, entry in entries:
                raw = var.get().strip()
                if raw == "":
                    values.append(None)
                else:
                    try:
                        v = float(raw)
                        values.append(v)
                    except ValueError:
                        messagebox.showerror("输入错误", f"请输入有效的数字，当前值：{raw}")
                        return
            total_score, grade = evaluate(material_data, values)
            total_score_percent = total_score * 100
            for i, (name, thresh, a_limit, b_limit, weight, direction, _) in enumerate(material_data):
                val = values[i]
                score = get_score(val, thresh, direction)
                a_ok = check_grade(val, a_limit, direction) if val is not None else False
                b_ok = check_grade(val, b_limit, direction) if val is not None else False
                val_str = f"{val:.3f}" if val is not None else "未输入"
                a_str = "✓" if a_ok else "✗"
                b_str = "✓" if b_ok else "✗"
                tree.insert("", tk.END, values=(name, val_str, f"{score:.2f}", a_str, b_str))
            score_label.config(text=f"★ 加权综合得分：{total_score_percent:.2f} 分")
            grade_label.config(text=f"★ 最终定级：{grade}")

        btn = ttk.Button(left_frame, text="计算得分与定级", command=compute)
        btn.grid(row=len(material_data), column=0, columnspan=2, pady=20)

        if tag == "sand":
            self.sand_entries = entries
            self.sand_hint_label = hint_label
            self.sand_score_label = score_label
            self.sand_grade_label = grade_label
        else:
            self.coarse_entries = entries
            self.coarse_hint_label = hint_label
            self.coarse_score_label = score_label
            self.coarse_grade_label = grade_label

    def export_single(self, tree, score_label, grade_label):
        if not tree.get_children():
            messagebox.showwarning("无数据", "请先计算评价结果")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        data = []
        for child in tree.get_children():
            values = tree.item(child)['values']
            data.append({
                "指标名称": values[0],
                "实测值": values[1],
                "单项得分": values[2],
                "A级符合": values[3],
                "B级符合": values[4]
            })
        df = pd.DataFrame(data)
        score_text = score_label.cget("text")
        grade_text = grade_label.cget("text")
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="评价详情", index=False)
            summary = pd.DataFrame({"项目": ["综合得分", "最终定级"], "结果": [score_text, grade_text]})
            summary.to_excel(writer, sheet_name="汇总", index=False)
        messagebox.showinfo("导出成功", f"结果已保存至 {file_path}")

    def plot_radar(self, tree, score_label):
        if not tree.get_children():
            messagebox.showwarning("无数据", "请先计算评价结果")
            return
        indicators = []
        scores = []
        for child in tree.get_children():
            values = tree.item(child)['values']
            indicators.append(values[0])
            try:
                s = float(values[2]) * 100
            except:
                s = 0
            scores.append(s)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        N = len(indicators)
        angles = [n / float(N) * 2 * 3.1415926 for n in range(N)]
        angles += angles[:1]
        scores += scores[:1]
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.plot(angles, scores, 'o-', linewidth=2, color='#1f77b4')
        ax.fill(angles, scores, alpha=0.25, color='#1f77b4')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(indicators, fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'])
        ax.set_title('骨料质量指标得分雷达图 (百分制)', fontsize=14)
        total_score_text = score_label.cget("text")
        ax.text(0.5, -0.15, total_score_text, transform=ax.transAxes, ha='center', fontsize=12, color='red')
        plt.tight_layout()
        plt.show()

    # ------------------ 批量评价页面（内联编辑，单击直接输入） ------------------
    def create_batch_page(self):
        # 数据存储
        self.batch_data_storage = {
            "机制砂": {"columns": ["工程1", "工程2", "工程3"], "data": None, "results": []},
            "粗骨料": {"columns": ["工程1", "工程2", "工程3"], "data": None, "results": []}
        }
        self.init_batch_storage()
        self.current_batch_type = "机制砂"

        # 顶部控件
        top_frame = ttk.Frame(self.batch_frame)
        top_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(top_frame, text="骨料类型:").pack(side='left', padx=5)
        self.batch_type_var = tk.StringVar(value="机制砂")
        type_combo = ttk.Combobox(top_frame, textvariable=self.batch_type_var, values=["机制砂", "粗骨料"], state="readonly", width=12)
        type_combo.pack(side='left', padx=5)
        type_combo.bind("<<ComboboxSelected>>", self.on_batch_type_change)
        ttk.Label(top_frame, text="  操作: 单击单元格直接输入 | 右键菜单 | Ctrl+C/V 复制粘贴当前单元格").pack(side='left', padx=10)

        # 表格区域
        table_frame = ttk.LabelFrame(self.batch_frame, text="工程数据表")
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.batch_tree = ttk.Treeview(table_frame, show="headings", style="Treeview")
        self.batch_tree.pack(side='left', fill='both', expand=True)
        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.batch_tree.yview)
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(table_frame, orient='horizontal', command=self.batch_tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.batch_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 绑定事件
        self.batch_tree.bind("<Button-1>", self.batch_cell_click)
        self.batch_tree.bind("<Button-3>", self.batch_show_context_menu)
        self.batch_tree.bind("<Control-c>", self.batch_copy_current)
        self.batch_tree.bind("<Control-v>", self.batch_paste_current)

        # 用于内联编辑的控件引用
        self.current_edit_entry = None
        self.current_cell = None  # (row, col)

        # 结果区域
        result_frame = ttk.LabelFrame(self.batch_frame, text="批量评价结果")
        result_frame.pack(fill='x', padx=5, pady=5)
        self.batch_result_tree = ttk.Treeview(result_frame, columns=("工程", "综合得分(百分制)", "等级"), show="headings", height=8)
        self.batch_result_tree.heading("工程", text="工程")
        self.batch_result_tree.heading("综合得分(百分制)", text="综合得分(百分制)")
        self.batch_result_tree.heading("等级", text="等级")
        self.batch_result_tree.column("工程", width=150)
        self.batch_result_tree.column("综合得分(百分制)", width=150)
        self.batch_result_tree.column("等级", width=100)
        self.batch_result_tree.pack(side='left', fill='both', expand=True)
        vsb_res = ttk.Scrollbar(result_frame, orient='vertical', command=self.batch_result_tree.yview)
        vsb_res.pack(side='right', fill='y')
        self.batch_result_tree.configure(yscrollcommand=vsb_res.set)

        # 按钮栏
        btn_frame = ttk.Frame(self.batch_frame)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="添加工程列", command=self.batch_add_column).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="删除最后一列", command=self.batch_del_last_column).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="计算所有工程", command=self.batch_compute).pack(side='left', padx=20)
        ttk.Button(btn_frame, text="导出批量结果", command=self.batch_export).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="绘制雷达图", command=self.batch_plot_radar).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清空所有数据", command=self.batch_clear_all).pack(side='left', padx=5)

        # 加载默认数据
        self.load_batch_data("机制砂")

    def init_batch_storage(self):
        for typ in ["机制砂", "粗骨料"]:
            mat = mechanism_sand if typ == "机制砂" else coarse_aggregate
            n_rows = len(mat)
            n_cols = len(self.batch_data_storage[typ]["columns"])
            self.batch_data_storage[typ]["data"] = [[None for _ in range(n_cols)] for __ in range(n_rows)]

    def load_batch_data(self, typ):
        self.current_batch_type = typ
        storage = self.batch_data_storage[typ]
        self.batch_columns = storage["columns"].copy()
        self.batch_data = storage["data"]
        self.batch_results = storage["results"]
        mat = mechanism_sand if typ == "机制砂" else coarse_aggregate
        n_rows = len(mat)
        n_cols = len(self.batch_columns)
        if len(self.batch_data) != n_rows:
            self.batch_data = [[None]*n_cols for _ in range(n_rows)]
        else:
            for row in self.batch_data:
                if len(row) < n_cols:
                    row.extend([None]*(n_cols - len(row)))
                elif len(row) > n_cols:
                    row[:] = row[:n_cols]
        self.update_batch_table_columns()
        self.update_batch_table_data()
        self.update_batch_result_tree()

    def update_batch_table_columns(self):
        all_cols = ["评价指标"] + self.batch_columns
        self.batch_tree["columns"] = all_cols
        for col in all_cols:
            self.batch_tree.heading(col, text=col)
            if col == "评价指标":
                self.batch_tree.column(col, width=350, anchor='w')
            else:
                self.batch_tree.column(col, width=100, anchor='center')

    def update_batch_table_data(self):
        mat = mechanism_sand if self.current_batch_type == "机制砂" else coarse_aggregate
        indicators = [item[0] for item in mat]
        for row in self.batch_tree.get_children():
            self.batch_tree.delete(row)
        for r, ind in enumerate(indicators):
            row_vals = [ind]
            if r < len(self.batch_data):
                for c in range(len(self.batch_columns)):
                    v = self.batch_data[r][c] if c < len(self.batch_data[r]) else None
                    row_vals.append(str(v) if v is not None else "")
            else:
                row_vals.extend([""]*len(self.batch_columns))
            iid = str(r)
            self.batch_tree.insert("", "end", iid=iid, values=row_vals)
            tag = 'odd' if r % 2 == 0 else 'even'
            self.batch_tree.item(iid, tags=(tag,))
        self.batch_tree.tag_configure('odd', background='#f9f9f9')
        self.batch_tree.tag_configure('even', background='#ffffff')

    def batch_cell_click(self, event):
        """单击单元格：内联编辑"""
        if self.current_edit_entry:
            self.save_edit()
            return
        region = self.batch_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.batch_tree.identify_column(event.x)
        if not col:
            return
        col_idx = int(col[1:]) - 1
        if col_idx == 0:   # 第一列不可编辑
            return
        item = self.batch_tree.identify_row(event.y)
        if not item:
            return
        row = int(item)
        eng_col = col_idx - 1
        self.current_cell = (row, eng_col)

        # 获取单元格位置
        bbox = self.batch_tree.bbox(item, column=col)
        if not bbox:
            return
        x, y, w, h = bbox

        # 当前值
        current_val = self.batch_data[row][eng_col] if row < len(self.batch_data) and eng_col < len(self.batch_data[row]) else None
        entry_var = tk.StringVar(value=str(current_val) if current_val is not None else "")
        self.current_edit_entry = tk.Entry(self.batch_tree, textvariable=entry_var, font=('微软雅黑', self.current_font_size))
        self.current_edit_entry.place(x=x, y=y, width=w, height=h)
        self.current_edit_entry.focus_set()
        self.current_edit_entry.select_range(0, tk.END)

        # 绑定事件
        def on_confirm(event=None):
            self.save_edit()
        def on_cancel(event=None):
            self.cancel_edit()
        self.current_edit_entry.bind("<Return>", on_confirm)
        self.current_edit_entry.bind("<FocusOut>", on_confirm)
        self.current_edit_entry.bind("<Escape>", on_cancel)

    def save_edit(self):
        if not self.current_edit_entry:
            return
        new_val_str = self.current_edit_entry.get().strip()
        row, col = self.current_cell
        if new_val_str == "":
            new_val = None
        else:
            try:
                new_val = float(new_val_str)
            except ValueError:
                new_val = None   # 非数字清空
        if row < len(self.batch_data) and col < len(self.batch_data[row]):
            self.batch_data[row][col] = new_val
        self.update_batch_table_data()
        self.save_current_batch_data()
        self.current_edit_entry.destroy()
        self.current_edit_entry = None

    def cancel_edit(self):
        if self.current_edit_entry:
            self.current_edit_entry.destroy()
            self.current_edit_entry = None

    def batch_show_context_menu(self, event):
        if self.current_edit_entry:
            self.save_edit()
        region = self.batch_tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.batch_tree.identify_column(event.x)
            if col:
                col_idx = int(col[1:]) - 1
                if col_idx > 0:
                    eng_col = col_idx - 1
                    self.show_column_menu(event, eng_col)
            return
        col = self.batch_tree.identify_column(event.x)
        if not col:
            return
        col_idx = int(col[1:]) - 1
        if col_idx == 0:
            return
        item = self.batch_tree.identify_row(event.y)
        if not item:
            return
        row = int(item)
        eng_col = col_idx - 1
        self.current_cell = (row, eng_col)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="复制单元格", command=self.batch_copy_current_cell)
        menu.add_command(label="粘贴到单元格", command=self.batch_paste_to_current_cell)
        menu.add_command(label="清除单元格", command=self.batch_clear_current_cell)
        menu.add_separator()
        menu.add_command(label="清除当前工程列", command=self.batch_clear_current_column)
        menu.add_command(label="清除所有数据", command=self.batch_clear_all)
        menu.post(event.x_root, event.y_root)

    def show_column_menu(self, event, eng_col):
        current_name = self.batch_columns[eng_col]
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=f"修改列名 '{current_name}'", command=lambda: self.batch_modify_column_name(eng_col))
        menu.add_command(label="在前面添加列", command=lambda: self.batch_insert_column_before(eng_col))
        menu.add_command(label="在后面添加列", command=lambda: self.batch_insert_column_after(eng_col))
        if len(self.batch_columns) > 1:
            menu.add_command(label="删除此列", command=lambda: self.batch_delete_column(eng_col))
        menu.post(event.x_root, event.y_root)

    def batch_copy_current_cell(self):
        if not self.current_cell:
            return
        row, col = self.current_cell
        val = self.batch_data[row][col] if row < len(self.batch_data) and col < len(self.batch_data[row]) else None
        self.root.clipboard_clear()
        self.root.clipboard_append(str(val) if val is not None else "")
        messagebox.showinfo("复制", "已复制单元格内容")

    def batch_paste_to_current_cell(self):
        if not self.current_cell:
            return
        try:
            clipboard = self.root.clipboard_get()
        except:
            return
        val_str = clipboard.strip()
        if val_str == "":
            new_val = None
        else:
            try:
                new_val = float(val_str)
            except ValueError:
                messagebox.showerror("粘贴错误", "剪贴板内容不是数字")
                return
        row, col = self.current_cell
        self.batch_data[row][col] = new_val
        self.update_batch_table_data()
        self.save_current_batch_data()

    def batch_clear_current_cell(self):
        if not self.current_cell:
            return
        row, col = self.current_cell
        self.batch_data[row][col] = None
        self.update_batch_table_data()
        self.save_current_batch_data()

    def batch_clear_current_column(self):
        if not self.current_cell:
            messagebox.showwarning("操作", "请先单击一个单元格以确定工程列")
            return
        _, col = self.current_cell
        for r in range(len(self.batch_data)):
            if col < len(self.batch_data[r]):
                self.batch_data[r][col] = None
        self.update_batch_table_data()
        self.save_current_batch_data()

    def batch_copy_current(self, event):
        self.batch_copy_current_cell()
        return "break"

    def batch_paste_current(self, event):
        self.batch_paste_to_current_cell()
        return "break"

    # 列操作、计算、导出、雷达图等方法（与之前相同，此处略，但实际必须包含）
    def batch_add_column(self):
        new_name = f"工程{len(self.batch_columns)+1}"
        self.batch_columns.append(new_name)
        for row in self.batch_data:
            row.append(None)
        self.update_batch_table_columns()
        self.save_current_batch_data()

    def batch_del_last_column(self):
        if len(self.batch_columns) <= 1:
            messagebox.showwarning("警告", "至少保留一个工程列")
            return
        self.batch_columns.pop()
        for row in self.batch_data:
            if row:
                row.pop()
        self.update_batch_table_columns()
        self.save_current_batch_data()

    def batch_modify_column_name(self, col_idx):
        new_name = simpledialog.askstring("修改工程名", "请输入新的工程名称:", initialvalue=self.batch_columns[col_idx])
        if new_name and new_name.strip():
            self.batch_columns[col_idx] = new_name.strip()
            self.update_batch_table_columns()
            self.save_current_batch_data()

    def batch_insert_column_before(self, col_idx):
        default_name = f"工程{len(self.batch_columns)+1}"
        self.batch_columns.insert(col_idx, default_name)
        for row in self.batch_data:
            row.insert(col_idx, None)
        self.update_batch_table_columns()
        self.save_current_batch_data()

    def batch_insert_column_after(self, col_idx):
        default_name = f"工程{len(self.batch_columns)+1}"
        self.batch_columns.insert(col_idx+1, default_name)
        for row in self.batch_data:
            row.insert(col_idx+1, None)
        self.update_batch_table_columns()
        self.save_current_batch_data()

    def batch_delete_column(self, col_idx):
        if len(self.batch_columns) <= 1:
            messagebox.showwarning("警告", "至少保留一个工程列")
            return
        self.batch_columns.pop(col_idx)
        for row in self.batch_data:
            if col_idx < len(row):
                row.pop(col_idx)
        self.update_batch_table_columns()
        self.save_current_batch_data()

    def batch_clear_all(self):
        if messagebox.askyesno("确认", "清空所有工程数据？此操作不可撤销。"):
            for r in range(len(self.batch_data)):
                for c in range(len(self.batch_columns)):
                    self.batch_data[r][c] = None
            self.update_batch_table_data()
            self.save_current_batch_data()
            self.batch_results = []
            self.update_batch_result_tree()

    def batch_compute(self):
        mat = mechanism_sand if self.current_batch_type == "机制砂" else coarse_aggregate
        results = []
        for col_idx, col_name in enumerate(self.batch_columns):
            col_values = [self.batch_data[r][col_idx] if r < len(self.batch_data) and col_idx < len(self.batch_data[r]) else None for r in range(len(mat))]
            total_score, grade = evaluate(mat, col_values)
            results.append((col_name, total_score*100, grade))
        self.batch_results = results
        self.update_batch_result_tree()
        self.save_current_batch_data()
        messagebox.showinfo("计算完成", f"共计算 {len(results)} 个工程")

    def update_batch_result_tree(self):
        for item in self.batch_result_tree.get_children():
            self.batch_result_tree.delete(item)
        for name, score, grade in self.batch_results:
            self.batch_result_tree.insert("", "end", values=(name, f"{score:.2f}", grade))

    def batch_export(self):
        if not self.batch_results:
            messagebox.showwarning("无数据", "请先计算批量结果")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not file_path:
            return
        result_data = [{"工程": n, "综合得分(百分制)": f"{s:.2f}", "等级": g} for n, s, g in self.batch_results]
        df_res = pd.DataFrame(result_data)
        mat = mechanism_sand if self.current_batch_type == "机制砂" else coarse_aggregate
        indicators = [item[0] for item in mat]
        data_dict = {"指标": indicators}
        for c_idx, c_name in enumerate(self.batch_columns):
            col_vals = [self.batch_data[r][c_idx] if r < len(self.batch_data) and c_idx < len(self.batch_data[r]) else None for r in range(len(indicators))]
            data_dict[c_name] = col_vals
        df_data = pd.DataFrame(data_dict)
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_res.to_excel(writer, sheet_name="综合评价", index=False)
            df_data.to_excel(writer, sheet_name="原始数据", index=False)
        messagebox.showinfo("导出成功", f"批量结果已保存至 {file_path}")

    def batch_plot_radar(self):
        if not self.batch_results:
            messagebox.showwarning("无数据", "请先计算批量结果")
            return
        mat = mechanism_sand if self.current_batch_type == "机制砂" else coarse_aggregate
        indicators = [item[0] for item in mat]
        eng_scores = []
        for col_idx, col_name in enumerate(self.batch_columns):
            col_vals = [self.batch_data[r][col_idx] if r < len(self.batch_data) and col_idx < len(self.batch_data[r]) else None for r in range(len(mat))]
            scores = []
            for i, v in enumerate(col_vals):
                _, thresh, _, _, _, direction, _ = mat[i]
                s = get_score(v, thresh, direction) * 100
                scores.append(s)
            eng_scores.append((col_name, scores))
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        N = len(indicators)
        angles = [n / float(N) * 2 * 3.1415926 for n in range(N)]
        angles += angles[:1]
        fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
        for i, (name, scores) in enumerate(eng_scores):
            scores_plot = scores + scores[:1]
            ax.plot(angles, scores_plot, 'o-', linewidth=2, label=name, color=colors[i % len(colors)])
            ax.fill(angles, scores_plot, alpha=0.1, color=colors[i % len(colors)])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(indicators, fontsize=8)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'])
        ax.set_title('各工程骨料质量指标得分对比雷达图 (百分制)', fontsize=14)
        ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
        plt.tight_layout()
        plt.show()

    def save_current_batch_data(self):
        self.batch_data_storage[self.current_batch_type]["columns"] = self.batch_columns.copy()
        self.batch_data_storage[self.current_batch_type]["data"] = self.batch_data
        self.batch_data_storage[self.current_batch_type]["results"] = self.batch_results

    def on_batch_type_change(self, event=None):
        if self.current_edit_entry:
            self.save_edit()
        self.save_current_batch_data()
        new_type = self.batch_type_var.get()
        self.load_batch_data(new_type)

if __name__ == "__main__":
    root = tk.Tk()
    app = AggregateApp(root)
    root.mainloop()