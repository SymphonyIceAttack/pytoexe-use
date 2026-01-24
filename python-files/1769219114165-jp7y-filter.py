import pandas as pd
import os
import re
import tkinter as tk
from tkinter import Tk, Toplevel, Listbox, StringVar, END, MULTIPLE, messagebox, ttk, Canvas
from tkinter.filedialog import askopenfilenames, askdirectory
from datetime import datetime


# ========================== 悬停提示工具类（支持 Listbox 每项独立提示） ==========================
class ToolTip:
    """tkinter悬停提示工具类，支持普通控件和 Listbox 每项独立提示"""
    def __init__(self, widget, item_texts=None):
        self.widget = widget
        self.item_texts = item_texts or {}  # 对于 Listbox：{index: text}
        self.tipwindow = None

    def showtip(self, text):
        if self.tipwindow or not text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("微软雅黑", 9), wraplength=600
        )
        label.pack(ipadx=2, ipady=2)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def bind_widget(self):
        """通用绑定"""
        self.widget.bind('<Enter>', lambda e: self.enter(e))
        self.widget.bind('<Leave>', lambda e: self.hidetip())
        self.widget.bind('<Motion>', lambda e: self.motion(e))

    def enter(self, event):
        self.motion(event)

    def motion(self, event):
        if isinstance(self.widget, Listbox):
            index = self.widget.nearest(event.y)
            text = self.item_texts.get(index)
            self.showtip(text or "")
        else:
            # 普通控件直接显示固定文本（通过 item_texts[0] 存储）
            text = self.item_texts.get(0)
            self.showtip(text or "")


def create_listbox_tooltip(listbox, item_texts):
    """为 Listbox 创建每项独立悬停提示"""
    tooltip = ToolTip(listbox, item_texts)
    tooltip.bind_widget()
    return tooltip


# ========================== 主应用类 ==========================
class ExcelFilterTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Excel 筛选工具")
        self.withdraw()

        self.destroyed = False
        self.protocol("WM_DELETE_WINDOW", self.safe_destroy)

        # ========================== 常量 ==========================
        self.MAX_SHEET_NAME_LEN = 31
        self.DEFAULT_SAVE_DIR = r"D:\Downloads" if os.path.isdir(r"D:\Downloads") else os.path.expanduser("~/Downloads")

        self.PRIMARY_COLOR = "#0078D7"
        self.ACCENT_COLOR = "#106EBE"
        self.BG_COLOR = "#F5F7FA"
        self.FG_COLOR = "#2D2D2D"

        # ========================== 样式 ==========================
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', background=self.BG_COLOR, foreground=self.FG_COLOR, font=('微软雅黑', 10))
        style.configure('TButton', padding=8, font=('微软雅黑', 10, 'bold'))
        style.map('TButton',
                  background=[('active', self.ACCENT_COLOR), ('pressed', '#005A9E')],
                  foreground=[('active', 'white')])
        style.configure('TLabel', font=('微软雅黑', 11))
        style.configure('Heading.TLabel', font=('微软雅黑', 14, 'bold'), foreground=self.PRIMARY_COLOR)
        style.configure('Info.TLabel', font=('微软雅黑', 10), foreground='#555555')
        style.configure('Tip.TLabel', font=('微软雅黑', 9), foreground='#666666', wraplength=750)

        # ========================== 优先级 ==========================
        self.PRIORITY = [
            ('学号', ['学号', '学员号', '学生编号', '学工号', '工号', 'ID', '编号', 'student id', '准考证号', '身份证']),
            ('联系方式', ['手机', '电话', '手机号', '联系方式', '微信', 'phone', 'tel', 'mobile']),
            ('姓名', ['姓名', '学生姓名', '姓名全称', '学员姓名', 'name', '学生', '考生姓名'])
        ]

        self.main_program()

    def safe_destroy(self):
        if not self.destroyed:
            self.destroyed = True
            try:
                self.quit()
                self.destroy()
            except:
                pass

    def safe_operation(self, func, default_return=None):
        if self.destroyed:
            return default_return
        try:
            return func()
        except (RuntimeError, tk.TclError):
            self.destroyed = True
            return default_return

    # ========================== 美化 Listbox（带水平滚动条） ==========================
    def styled_listbox(self, parent, selectmode="single", height=6, width=40):
        frame = ttk.Frame(parent)
        h_scrollbar = ttk.Scrollbar(frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        v_scrollbar = ttk.Scrollbar(frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        listbox = Listbox(
            frame,
            font=("微软雅黑", 10),
            bg="white", fg=self.FG_COLOR,
            selectbackground=self.PRIMARY_COLOR, selectforeground="white",
            activestyle='none', highlightthickness=0, bd=0,
            selectmode=selectmode,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            exportselection=0,
            height=height,
            width=width
        )
        v_scrollbar.config(command=listbox.yview)
        h_scrollbar.config(command=listbox.xview)
        listbox.pack(side="left", fill="both", expand=True)
        frame.pack(fill="both", expand=True, pady=5)
        return listbox

    # ========================== 数据清洗 ==========================
    def normalize_value(self, x, is_id=False):
        if pd.isna(x):
            return None
        x_str = str(x).strip()
        full2half = str.maketrans(
            '０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～',
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        )
        x_str = x_str.translate(full2half)
        x_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', x_str)
        x_str = re.sub(r'\s+', ' ', x_str)
        if is_id:
            x_str = re.sub(r'\s+', '', x_str).upper()
        else:
            x_str = x_str.upper()
            x_str = re.sub(r'[\(（【].*?[)）】]$', '', x_str)
            x_str = re.sub(r'[\*＊]', '', x_str)
            x_str = x_str.strip()
        return x_str if x_str else None

    # ========================== 手动匹配列选择（保留原样） ==========================
    def select_all_columns_in_one_page(self, a_pairs, b_pairs):
        if self.destroyed:
            return None

        top = Toplevel(self)
        top.title("统一选择匹配列（多B表自定义）")
        top.geometry("900x600")
        top.configure(bg=self.BG_COLOR)
        top.grab_set()

        def on_top_close():
            result["value"] = None
            self.safe_operation(lambda: top.destroy())
        top.protocol("WM_DELETE_WINDOW", on_top_close)

        ttk.Label(top, text="🔑 手动匹配列选择（为每个A/B工作表单独选择匹配列）", style='Heading.TLabel').pack(pady=(10, 8))
        ttk.Label(top, text="为每个A工作表和B工作表分别选择匹配列（同语义列匹配更准确）", style='Info.TLabel', wraplength=850).pack(pady=(0, 10))

        # 加载列名（略，同前）
        a_sheet_cols = {}
        for file_a, sheet_a in a_pairs:
            key = (file_a, sheet_a)
            try:
                cols = pd.read_excel(file_a, sheet_name=sheet_a, nrows=0).columns.tolist()
                a_sheet_cols[key] = cols
            except Exception as e:
                messagebox.showwarning("读取失败", f"无法加载 {os.path.basename(file_a)} - {sheet_a} 列名：{str(e)[:100]}")
                a_sheet_cols[key] = []

        b_sheet_cols = {}
        for file_b, sheet_b in b_pairs:
            key = (file_b, sheet_b)
            try:
                cols = pd.read_excel(file_b, sheet_name=sheet_b, nrows=0).columns.tolist()
                b_sheet_cols[key] = cols
            except Exception as e:
                messagebox.showwarning("读取失败", f"无法加载 {os.path.basename(file_b)} - {sheet_b} 列名：{str(e)[:100]}")
                b_sheet_cols[key] = []

        if not a_sheet_cols or not b_sheet_cols:
            messagebox.showerror("错误", "A/B表列名加载失败")
            self.safe_operation(lambda: top.destroy())
            return None

        main = ttk.Frame(top)
        main.pack(fill='both', expand=True, padx=15, pady=8)

        # 左侧 A
        left = ttk.Frame(main)
        left.pack(side='left', fill='both', expand=True, padx=(0, 15))
        ttk.Label(left, text="参考表 A 各工作表匹配列", font=('微软雅黑', 11, 'bold'), foreground=self.PRIMARY_COLOR).pack(anchor='w', pady=(0, 8))

        canvas_a = Canvas(left, bg=self.BG_COLOR)
        scrollbar_a = ttk.Scrollbar(left, orient="vertical", command=canvas_a.yview)
        scrollable_frame_a = ttk.Frame(canvas_a)
        scrollable_frame_a.bind("<Configure>", lambda e: self.safe_operation(lambda: canvas_a.configure(scrollregion=canvas_a.bbox("all"))))
        canvas_a.create_window((0, 0), window=scrollable_frame_a, anchor="nw")
        canvas_a.configure(yscrollcommand=scrollbar_a.set)
        canvas_a.pack(side="left", fill="both", expand=True)
        scrollbar_a.pack(side="right", fill="y")

        # 右侧 B
        right = ttk.Frame(main)
        right.pack(side='right', fill='both', expand=True, padx=(10, 0))
        ttk.Label(right, text="名单表 B 各工作表匹配列", font=('微软雅黑', 11, 'bold'), foreground=self.PRIMARY_COLOR).pack(anchor='w', pady=(0, 8))

        canvas_b = Canvas(right, bg=self.BG_COLOR)
        scrollbar_b = ttk.Scrollbar(right, orient="vertical", command=canvas_b.yview)
        scrollable_frame_b = ttk.Frame(canvas_b)
        scrollable_frame_b.bind("<Configure>", lambda e: self.safe_operation(lambda: canvas_b.configure(scrollregion=canvas_b.bbox("all"))))
        canvas_b.create_window((0, 0), window=scrollable_frame_b, anchor="nw")
        canvas_b.configure(yscrollcommand=scrollbar_b.set)
        canvas_b.pack(side="left", fill="both", expand=True)
        scrollbar_b.pack(side="right", fill="y")

        # A 列选择（带文件名 ToolTip）
        a_vars = {}
        default_col_per_file = {}
        for (file_a, sheet_a), cols_a in a_sheet_cols.items():
            row = ttk.Frame(scrollable_frame_a)
            row.pack(fill='x', pady=4, padx=6)
            display_text = f"{os.path.basename(file_a)} - {sheet_a}"
            full_text = f"文件路径：{file_a}\n工作表名：{sheet_a}"
            file_label = ttk.Label(row, text=display_text, width=30, font=('微软雅黑', 9))
            file_label.pack(side='left')
            ToolTip(file_label, {0: full_text}).bind_widget()

            var = StringVar()
            combo = ttk.Combobox(row, textvariable=var, values=cols_a, state="readonly", width=25, font=('微软雅黑', 9))
            combo.pack(side='left', padx=10)
            if cols_a:
                combo.current(0)
                var.set(cols_a[0])

            def make_trace(f=file_a, v=var):
                def on_change(*args):
                    if self.destroyed:
                        return
                    selected = v.get()
                    if selected and f not in default_col_per_file:
                        default_col_per_file[f] = selected
                        for (fa, sa), va in a_vars.items():
                            if fa == f:
                                va.set(selected)
                return on_change
            var.trace("w", make_trace())
            a_vars[(file_a, sheet_a)] = var

        # B 列选择（同上）
        b_vars = {}
        default_col_per_b_file = {}
        for (file_b, sheet_b), cols_b in b_sheet_cols.items():
            row = ttk.Frame(scrollable_frame_b)
            row.pack(fill='x', pady=4, padx=6)
            display_text = f"{os.path.basename(file_b)} - {sheet_b}"
            full_text = f"文件路径：{file_b}\n工作表名：{sheet_b}"
            file_label = ttk.Label(row, text=display_text, width=30, font=('微软雅黑', 9))
            file_label.pack(side='left')
            ToolTip(file_label, {0: full_text}).bind_widget()

            var = StringVar()
            combo = ttk.Combobox(row, textvariable=var, values=cols_b, state="readonly", width=25, font=('微软雅黑', 9))
            combo.pack(side='left', padx=10)
            if cols_b:
                combo.current(0)
                var.set(cols_b[0])

            def make_b_trace(f=file_b, v=var):
                def on_change(*args):
                    if self.destroyed:
                        return
                    selected = v.get()
                    if selected and f not in default_col_per_b_file:
                        default_col_per_b_file[f] = selected
                        for (fb, sb), vb in b_vars.items():
                            if fb == f:
                                vb.set(selected)
                return on_change
            var.trace("w", make_b_trace())
            b_vars[(file_b, sheet_b)] = var

        btn_frame = ttk.Frame(top)
        btn_frame.pack(pady=12, anchor='center')
        result = {"value": None}

        def confirm():
            if self.destroyed:
                return
            a_selected = {}
            for key, var in a_vars.items():
                col = var.get()
                if not col:
                    messagebox.showwarning("未选择", f"请为 {os.path.basename(key[0])} - {key[1]} 选择匹配列")
                    return
                a_selected[key] = col
            b_selected = {}
            for key, var in b_vars.items():
                col = var.get()
                if not col:
                    messagebox.showwarning("未选择", f"请为 {os.path.basename(key[0])} - {key[1]} 选择匹配列")
                    return
                b_selected[key] = col
            result["value"] = (a_selected, b_selected)
            self.safe_operation(lambda: top.destroy())

        def cancel():
            result["value"] = None
            self.safe_operation(lambda: top.destroy())

        ttk.Button(btn_frame, text="✅ 确认所有选择并继续筛选", command=confirm).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ 取消（返回文件选择）", command=cancel).pack(side='left', padx=10)

        self.safe_operation(lambda: top.update_idletasks())
        self.safe_operation(lambda: top.geometry(f"+{top.winfo_screenwidth()//2 - 450}+{top.winfo_screenheight()//2 - 300}"))
        top.wait_window()
        return result["value"]

    # ========================== 模式设置 ==========================
    def show_settings(self):
        if self.destroyed:
            return None, None

        top = Toplevel(self)
        top.title("Excel 筛选工具 - (made by xyf)")
        top.geometry("550x480")
        top.configure(bg=self.BG_COLOR)
        top.grab_set()
        top.protocol("WM_DELETE_WINDOW", self.safe_destroy)

        ttk.Label(top, text="🔍 Excel 智能筛选工具", style='Heading.TLabel').pack(pady=(30, 15))
        ttk.Label(top, text="请先选择筛选模式和列匹配方式", style='Info.TLabel').pack(pady=(0, 20))

        mode_var = StringVar(value="1")
        ttk.Label(top, text="筛选模式：", font=('微软雅黑', 11, 'bold')).pack(anchor='w', padx=60, pady=(8,4))
        ttk.Radiobutton(top, text="正向筛选：名单表（B）中存在，参考表（A）中也存在的记录", variable=mode_var, value="1").pack(anchor='w', padx=70, pady=4)
        ttk.Radiobutton(top, text="反向筛选：名单表（B）中存在，参考表（A）中不存在的记录", variable=mode_var, value="2").pack(anchor='w', padx=70, pady=4)

        col_mode_var = StringVar(value="1")
        ttk.Label(top, text="匹配列选择：", font=('微软雅黑', 11, 'bold')).pack(anchor='w', padx=60, pady=(20,4))
        ttk.Radiobutton(top, text="⚡ 自动模式（学号>联系方式>姓名）", variable=col_mode_var, value="1").pack(anchor='w', padx=80, pady=4)
        ttk.Radiobutton(top, text="✋ 手动模式", variable=col_mode_var, value="2").pack(anchor='w', padx=80, pady=4)

        result = {"mode": None, "col_mode": None}

        def confirm():
            if self.destroyed:
                return
            result['mode'] = mode_var.get()
            result['col_mode'] = col_mode_var.get()
            self.safe_operation(lambda: top.destroy())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(pady=30, anchor='center')
        ttk.Button(btn_frame, text="🚀 开始筛选（选择文件）", command=confirm).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="❌ 退出程序", command=self.safe_destroy).pack(side='left', padx=10)

        self.safe_operation(lambda: top.update_idletasks())
        self.safe_operation(lambda: top.geometry(f"+{top.winfo_screenwidth()//2 - 275}+{top.winfo_screenheight()//2 - 240}"))
        top.wait_window()
        return result['mode'], result['col_mode']

    # ========================== 文件与工作表选择（重点恢复并正确实现 ToolTip） ==========================
    def select_files_and_sheets(self, col_mode):
        if self.destroyed:
            return "exit"

        top = Toplevel(self)
        top.title("选择文件与工作表")
        top.geometry("800x550")
        top.configure(bg=self.BG_COLOR)
        top.grab_set()
        top.protocol("WM_DELETE_WINDOW", self.safe_destroy)

        is_auto_mode = (col_mode == "1")

        title_frame = ttk.Frame(top)
        title_frame.pack(fill='x', padx=15, pady=(15, 10))
        if is_auto_mode:
            main_title = "📂 请添加参考表 A 和名单表 B 文件（自动模式为每对A-B表单独匹配最优列）"
            ttk.Label(title_frame, text=main_title, style='Heading.TLabel').pack(anchor='w')
            tip_text = """💡 自动模式说明：
1. 无需手动选择工作表，程序将自动读取文件中所有工作表
2. 为每对A工作表-B工作表单独匹配最优列（优先级：学号>联系方式>姓名）
3. 支持多文件批量处理，添加后可通过「移除选中」清理错误文件"""
            ttk.Label(title_frame, text=tip_text, style='Tip.TLabel').pack(anchor='w', pady=(5, 0))
        else:
            main_title = "📂 请添加参考表 A 和名单表 B 文件（添加/移除后自动刷新下方工作表列表）"
            ttk.Label(title_frame, text=main_title, style='Heading.TLabel').pack(anchor='w')

        file_frame = ttk.Frame(top)
        file_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        # 左侧 A 文件
        left_files = ttk.Frame(file_frame)
        left_files.pack(side='left', fill='both', expand=True, padx=(0, 15))
        ttk.Label(left_files, text="参考表 A（完整大表，可多选文件）", font=('微软雅黑', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        a_list_height = 12 if is_auto_mode else 5
        listbox_a_files = self.styled_listbox(left_files, selectmode=MULTIPLE, height=a_list_height, width=40)
        a_files = []
        a_file_tooltips = {}  # index -> full_path

        btn_a_frame = ttk.Frame(left_files)
        btn_a_frame.pack(fill='x', pady=(5, 0), anchor='center')
        def add_a():
            if self.destroyed:
                return
            new_files = askopenfilenames(title="添加参考表 A（支持多选）", filetypes=[("Excel 文件", "*.xlsx *.xls")])
            for f in new_files:
                if f and f not in a_files:
                    a_files.append(f)
                    idx = listbox_a_files.size()
                    listbox_a_files.insert(END, os.path.basename(f))
                    a_file_tooltips[idx] = f"完整路径：{f}"
            create_listbox_tooltip(listbox_a_files, a_file_tooltips)
            update_sheets()
        def remove_a():
            if self.destroyed:
                return
            sel = listbox_a_files.curselection()
            if sel:
                for i in reversed(sel):
                    del a_files[i]
                    del a_file_tooltips[i]
                    listbox_a_files.delete(i)
                    # 重新编号
                    new_tooltips = {}
                    for old_idx, text in a_file_tooltips.items():
                        if old_idx > i:
                            new_tooltips[old_idx - 1] = text
                        elif old_idx < i:
                            new_tooltips[old_idx] = text
                    a_file_tooltips.clear()
                    a_file_tooltips.update(new_tooltips)
                create_listbox_tooltip(listbox_a_files, a_file_tooltips)
            update_sheets()
        ttk.Button(btn_a_frame, text="➕ 添加文件", command=add_a).pack(side='left', padx=5)
        ttk.Button(btn_a_frame, text="➖ 移除选中", command=remove_a).pack(side='left', padx=5)

        # 右侧 B 文件
        right_files = ttk.Frame(file_frame)
        right_files.pack(side='right', fill='both', expand=True)
        ttk.Label(right_files, text="名单表 B（待筛选名单，可多选文件）", font=('微软雅黑', 11, 'bold')).pack(anchor='w', pady=(0, 5))
        b_list_height = 12 if is_auto_mode else 5
        listbox_b_files = self.styled_listbox(right_files, selectmode=MULTIPLE, height=b_list_height, width=40)
        b_files = []
        b_file_tooltips = {}

        btn_b_frame = ttk.Frame(right_files)
        btn_b_frame.pack(fill='x', pady=(5, 0), anchor='center')
        def add_b():
            if self.destroyed:
                return
            new_files = askopenfilenames(title="添加名单表 B（支持多选）", filetypes=[("Excel 文件", "*.xlsx *.xls")])
            for f in new_files:
                if f and f not in b_files:
                    b_files.append(f)
                    idx = listbox_b_files.size()
                    listbox_b_files.insert(END, os.path.basename(f))
                    b_file_tooltips[idx] = f"完整路径：{f}"
            create_listbox_tooltip(listbox_b_files, b_file_tooltips)
            update_sheets()
        def remove_b():
            if self.destroyed:
                return
            sel = listbox_b_files.curselection()
            if sel:
                for i in reversed(sel):
                    del b_files[i]
                    del b_file_tooltips[i]
                    listbox_b_files.delete(i)
                    new_tooltips = {}
                    for old_idx, text in b_file_tooltips.items():
                        if old_idx > i:
                            new_tooltips[old_idx - 1] = text
                        elif old_idx < i:
                            new_tooltips[old_idx] = text
                    b_file_tooltips.clear()
                    b_file_tooltips.update(new_tooltips)
                create_listbox_tooltip(listbox_b_files, b_file_tooltips)
            update_sheets()
        ttk.Button(btn_b_frame, text="➕ 添加文件", command=add_b).pack(side='left', padx=5)
        ttk.Button(btn_b_frame, text="➖ 移除选中", command=remove_b).pack(side='left', padx=5)

        # 工作表区（仅手动模式）
        sheets_frame = ttk.Frame(top)
        listbox_a_sheets = listbox_b_sheets = None
        a_sheet_tooltips = {}
        b_sheet_tooltips = {}
        if not is_auto_mode:
            sheets_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
            ttk.Label(sheets_frame, text="📋 工作表列表（默认全选，支持多选/取消）", style='Heading.TLabel').pack(anchor='w', pady=(0, 5))
            sheets_main = ttk.Frame(sheets_frame)
            sheets_main.pack(fill='both', expand=True)
            left_sheets = ttk.Frame(sheets_main)
            left_sheets.pack(side='left', fill='both', expand=True, padx=(0, 15))
            ttk.Label(left_sheets, text="参考表 A 工作表", font=('微软雅黑', 11, 'bold'), foreground=self.PRIMARY_COLOR).pack(anchor='w')
            listbox_a_sheets = self.styled_listbox(left_sheets, selectmode=MULTIPLE, height=5, width=40)
            right_sheets = ttk.Frame(sheets_main)
            right_sheets.pack(side='right', fill='both', expand=True)
            ttk.Label(right_sheets, text="名单表 B 工作表", font=('微软雅黑', 11, 'bold'), foreground=self.PRIMARY_COLOR).pack(anchor='w')
            listbox_b_sheets = self.styled_listbox(right_sheets, selectmode=MULTIPLE, height=5, width=40)

        a_pairs_all = []
        b_pairs_all = []
        def update_sheets():
            if self.destroyed:
                return
            if not is_auto_mode:
                listbox_a_sheets.delete(0, END)
                listbox_b_sheets.delete(0, END)
                a_pairs_all.clear()
                b_pairs_all.clear()
                a_sheet_tooltips.clear()
                b_sheet_tooltips.clear()

            failed_files = []
            for file in a_files:
                try:
                    excel = pd.ExcelFile(file)
                    sheet_names = excel.sheet_names
                    excel.close()
                    if not is_auto_mode:
                        for sheet in sheet_names:
                            idx = listbox_a_sheets.size()
                            a_pairs_all.append((file, sheet))
                            display = f"{os.path.basename(file)} - {sheet}"
                            listbox_a_sheets.insert(END, display)
                            a_sheet_tooltips[idx] = f"文件路径：{file}\n工作表：{sheet}"
                        create_listbox_tooltip(listbox_a_sheets, a_sheet_tooltips)
                except Exception as e:
                    failed_files.append(f"{os.path.basename(file)} ({str(e)[:50]})")

            for file in b_files:
                try:
                    excel = pd.ExcelFile(file)
                    sheet_names = excel.sheet_names
                    excel.close()
                    if not is_auto_mode:
                        for sheet in sheet_names:
                            idx = listbox_b_sheets.size()
                            b_pairs_all.append((file, sheet))
                            display = f"{os.path.basename(file)} - {sheet}"
                            listbox_b_sheets.insert(END, display)
                            b_sheet_tooltips[idx] = f"文件路径：{file}\n工作表：{sheet}"
                        create_listbox_tooltip(listbox_b_sheets, b_sheet_tooltips)
                except Exception as e:
                    failed_files.append(f"{os.path.basename(file)} ({str(e)[:50]})")

            if not is_auto_mode:
                listbox_a_sheets.select_set(0, END)
                listbox_b_sheets.select_set(0, END)

            if failed_files:
                messagebox.showwarning("部分文件读取失败", f"以下文件无法读取，将被跳过：\n" + "\n".join(failed_files))

        update_sheets()

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill='x', padx=15, pady=(0, 20), anchor='center')
        result = {"value": None}

        def confirm():
            if self.destroyed:
                return
            if not a_files or not b_files:
                messagebox.showwarning("缺少文件", "请至少各添加一个 A 和 B 文件")
                return

            selected_a = []
            selected_b = []
            if is_auto_mode:
                for file in a_files:
                    try:
                        excel = pd.ExcelFile(file)
                        sheet_names = excel.sheet_names
                        excel.close()
                        for sheet in sheet_names:
                            selected_a.append((file, sheet))
                    except Exception as e:
                        messagebox.showwarning("读取失败", f"{os.path.basename(file)} 读取失败: {str(e)[:50]}")
                for file in b_files:
                    try:
                        excel = pd.ExcelFile(file)
                        sheet_names = excel.sheet_names
                        excel.close()
                        for sheet in sheet_names:
                            selected_b.append((file, sheet))
                    except Exception as e:
                        messagebox.showwarning("读取失败", f"{os.path.basename(file)} 读取失败: {str(e)[:50]}")
            else:
                sel_a = listbox_a_sheets.curselection()
                sel_b = listbox_b_sheets.curselection()
                if len(sel_a) == 0 or len(sel_b) == 0:
                    messagebox.showwarning("缺少选择", "请至少各选择一个工作表")
                    return
                selected_a = [a_pairs_all[i] for i in sel_a]
                selected_b = [b_pairs_all[i] for i in sel_b]

            result["value"] = (a_files[:], b_files[:], selected_a, selected_b)
            self.safe_operation(lambda: top.destroy())

        def back_to_settings():
            result["value"] = "back_to_settings"
            self.safe_operation(lambda: top.destroy())

        btn_container = ttk.Frame(btn_frame)
        btn_container.pack(anchor='center')
        ttk.Button(btn_container, text="✅ 确认并继续", command=confirm).pack(side='left', padx=10)
        ttk.Button(btn_container, text="⬅ 返回模式设置", command=back_to_settings).pack(side='left', padx=10)
        ttk.Button(btn_container, text="❌ 退出程序", command=self.safe_destroy).pack(side='left', padx=10)

        self.safe_operation(lambda: top.update_idletasks())
        self.safe_operation(lambda: top.geometry(f"+{top.winfo_screenwidth()//2 - 400}+{top.winfo_screenheight()//2 - 275}"))
        top.wait_window()
        return result["value"]

    # ========================== 列匹配工具 ==========================
    def find_best_column(self, columns):
        for col_type, keywords in self.PRIORITY:
            for col in columns:
                if any(kw.lower() in str(col).lower() for kw in keywords):
                    return col, col_type
        return None, None

    # ========================== 主程序 ==========================
    def main_program(self):
        while not self.destroyed:
            mode, col_mode = self.show_settings()
            if mode is None or self.destroyed:
                break

            while not self.destroyed:
                result = self.select_files_and_sheets(col_mode)
                if result == "exit" or self.destroyed:
                    return
                elif result == "back_to_settings":
                    break
                elif result is not None:
                    A_files, B_files, a_pairs, b_pairs = result

                    a_selected_cols = b_selected_cols = None
                    if col_mode == "2" and not self.destroyed:
                        column_result = self.select_all_columns_in_one_page(a_pairs, b_pairs)
                        if column_result is None or self.destroyed:
                            continue
                        a_selected_cols, b_selected_cols = column_result

                    matched_pairs = []
                    results_dict = {}

                    for file_a, sheet_a in a_pairs:
                        if self.destroyed:
                            break
                        try:
                            df_a = pd.read_excel(file_a, sheet_name=sheet_a)
                        except Exception as e:
                            messagebox.showwarning("读取失败", f"{os.path.basename(file_a)} - {sheet_a} 读取失败: {str(e)[:100]}")
                            continue

                        for file_b, sheet_b in b_pairs:
                            if self.destroyed:
                                break
                            try:
                                df_b = pd.read_excel(file_b, sheet_name=sheet_b)
                            except Exception as e:
                                messagebox.showwarning("读取失败", f"{os.path.basename(file_b)} - {sheet_b} 读取失败: {str(e)[:100]}")
                                continue

                            if col_mode == "1":
                                col_a, col_a_type = self.find_best_column(df_a.columns)
                                col_b, col_b_type = self.find_best_column(df_b.columns)
                            else:
                                col_a = a_selected_cols.get((file_a, sheet_a))
                                col_b = b_selected_cols.get((file_b, sheet_b))
                                _, col_a_type = self.find_best_column([col_a]) if col_a else (None, "自定义")
                                _, col_b_type = self.find_best_column([col_b]) if col_b else (None, "自定义")

                            if not col_a or not col_b or col_a not in df_a.columns or col_b not in df_b.columns:
                                continue

                            matched_pairs.append({
                                "a_file": os.path.basename(file_a),
                                "a_sheet": sheet_a,
                                "a_col": col_a,
                                "a_col_type": col_a_type,
                                "b_file": os.path.basename(file_b),
                                "b_sheet": sheet_b,
                                "b_col": col_b,
                                "b_col_type": col_b_type
                            })

                            is_id_like = col_a_type in ["学号", "联系方式"] or col_b_type in ["学号", "联系方式"]

                            df_a_clean = df_a.rename(columns={col_a: 'KEY'})
                            df_a_clean['KEY'] = df_a_clean['KEY'].apply(lambda x: self.normalize_value(x, is_id_like))
                            df_a_clean = df_a_clean.drop_duplicates(subset=['KEY'])
                            df_a_clean = df_a_clean.dropna(subset=['KEY']).copy()

                            df_b_clean = df_b.rename(columns={col_b: 'KEY'})
                            df_b_clean['KEY'] = df_b_clean['KEY'].apply(lambda x: self.normalize_value(x, is_id_like))
                            df_b_clean = df_b_clean.drop_duplicates(subset=['KEY'])
                            df_b_clean = df_b_clean.dropna(subset=['KEY']).copy()

                            if mode == "1":
                                unique_b_cols = [c for c in df_b_clean.columns if c != 'KEY' and c not in df_a_clean.columns]
                                merged = pd.merge(df_a_clean, df_b_clean[['KEY'] + unique_b_cols], on='KEY', how='inner')
                            else:
                                merged = df_b_clean[~df_b_clean['KEY'].isin(df_a_clean['KEY'])]

                            if merged.empty:
                                continue

                            final_key_name = col_a_type if col_a_type != "自定义" else col_a
                            if 'KEY' in merged.columns:
                                merged.rename(columns={'KEY': final_key_name}, inplace=True)
                            if final_key_name in merged.columns:
                                cols = [final_key_name] + [c for c in merged.columns if c != final_key_name]
                                merged = merged[cols]

                            a_short = os.path.basename(file_a).rsplit('.', 1)[0][:10]
                            b_short = os.path.basename(file_b).rsplit('.', 1)[0][:10]
                            sheet_name = f"{a_short}_{sheet_a[:8]}_{b_short}_{sheet_b[:8]}"
                            sheet_name = sheet_name[:self.MAX_SHEET_NAME_LEN]
                            idx_a = a_pairs.index((file_a, sheet_a))
                            idx_b = b_pairs.index((file_b, sheet_b))
                            if sheet_name in results_dict:
                                sheet_name = f"{sheet_name}_{idx_a}_{idx_b}"[:self.MAX_SHEET_NAME_LEN]

                            results_dict[sheet_name] = merged

                    if not matched_pairs and not self.destroyed:
                        messagebox.showerror("匹配失败", "未找到任何可匹配的A-B工作表对！\n请检查列名或重新选择文件。")
                        continue

                    mode_desc = "正向筛选（B在A中存在）" if mode == "1" else "反向筛选（B在A中不存在）"
                    total_records = sum(len(df) for df in results_dict.values())

                    if not self.destroyed:
                        match_info = []
                        for i, pair in enumerate(matched_pairs[:50]):
                            match_info.append(
                                f"{i+1}. A[{pair['a_file']}-{pair['a_sheet']}:{pair['a_col']}({pair['a_col_type']})] "
                                f"↔ B[{pair['b_file']}-{pair['b_sheet']}:{pair['b_col']}({pair['b_col_type']})]"
                            )
                        if len(matched_pairs) > 50:
                            match_info.append(f"...（共 {len(matched_pairs)} 对，省略其余）")
                        match_info = "\n".join(match_info)

                        messagebox.showinfo(
                            "匹配成功",
                            f"成功匹配 {len(matched_pairs)} 对A-B工作表！\n"
                            f"筛选模式：{mode_desc}\n"
                            f"生成结果工作表：{len(results_dict)} 个\n"
                            f"总计匹配记录：{total_records} 条\n\n"
                            f"匹配详情：\n{match_info}"
                        )

                    if total_records == 0 and not self.destroyed:
                        messagebox.showinfo("无匹配记录", f"{mode_desc}下未找到任何记录")
                        continue

                    if not self.destroyed:
                        save_dir = askdirectory(title="选择结果保存目录", initialdir=self.DEFAULT_SAVE_DIR)
                        if not save_dir:
                            messagebox.showwarning("保存取消", "未选择保存目录，结果未保存！")
                            continue

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"筛选结果_{timestamp}.xlsx"
                        save_path = os.path.join(save_dir, file_name)

                        try:
                            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                                for sheet_name, df in results_dict.items():
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                            messagebox.showinfo(
                                "保存成功",
                                f"结果已成功保存！\n\n"
                                f"保存路径：{save_path}\n"
                                f"包含工作表：{len(results_dict)} 个\n"
                                f"总计记录：{total_records} 条"
                            )
                        except Exception as e:
                            messagebox.showerror(
                                "保存失败",
                                f"文件保存失败：{str(e)}\n\n建议检查：\n"
                                "1. 保存目录是否有权限\n"
                                "2. 文件是否被占用\n"
                                "3. 是否安装openpyxl库（执行：pip install openpyxl）"
                            )
                            continue

                    self.safe_destroy()
                    return

if __name__ == "__main__":
    try:
        import openpyxl
    except ImportError:
        messagebox.showwarning("缺少依赖", "未检测到openpyxl库，将无法保存Excel文件！\n请执行命令安装：pip install openpyxl")
    try:
        app = ExcelFilterTool()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("程序异常", f"程序运行出错：{str(e)}")