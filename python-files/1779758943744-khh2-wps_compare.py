"""
WPS 表格对比工具 v2 — 左右并排视图
功能：
  1. 加载两个 Excel/WPS 文件（.xlsx .xls .et .csv）
  2. 自动读取第一行作为表头，支持选择 Sheet
  3. 可自由勾选"关键字段"用于行匹配，不勾选则按行号对比
  4. 对比结果左右两栏并排：左侧=文件A，右侧=文件B，差异行高亮
  5. 左右两栏垂直同步滚动，各自可独立水平滚动
  6. 虚拟滚动（Canvas）保证超大数据不卡顿
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import os

# ──────────────────────────────────────────────
# 颜色常量
# ──────────────────────────────────────────────
BG          = "#F5F7FA"
PANEL_BG    = "#FFFFFF"
ACCENT      = "#4A6CF7"
ADDED_BG    = "#C8F7C5"   # 右侧新增行（B有A无）
DELETED_BG  = "#FAD4D4"   # 左侧删除行（A有B无）
CHANGED_BG  = "#FFF8CC"   # 修改行
SAME_BG     = "#FFFFFF"   # 相同行
EMPTY_BG    = "#F0F0F0"   # 对端无数据的占位行
DIFF_CELL   = "#FFD580"   # 修改行中具体差异单元格
HEADER_BG   = "#4A6CF7"
HEADER_FG   = "#FFFFFF"
DIVIDER_CLR = "#4A6CF7"   # 中间分隔线
CELL_H      = 28
CELL_PAD    = 8

# ──────────────────────────────────────────────
# 单侧虚拟滚动表格（Canvas 实现）
# ──────────────────────────────────────────────
class SideTable(tk.Frame):
    """
    单侧表格，支持外部同步 y 偏移（左右联动）。
    data     : list of dict  每行原始数据
    row_tags : list of str   'added'/'deleted'/'changed'/'same'/'empty'
    diff_cells: list of set  每行中有差异的列名集合（仅 changed 行用到）
    on_scroll_cb : 当本侧滚动时回调，用于同步对端
    show_vscroll : 是否显示自己的垂直滚动条（右侧显示，左侧隐藏共用）
    """
    def __init__(self, master, columns, data, row_tags, diff_cells,
                 on_scroll_cb=None, show_vscroll=True, **kw):
        super().__init__(master, bg=BG, **kw)
        self.columns      = columns
        self.data         = data
        self.row_tags     = row_tags
        self.diff_cells   = diff_cells   # list[set]
        self._on_scroll_cb = on_scroll_cb
        self._show_vscroll = show_vscroll
        self._col_widths  = []
        self._total_w     = 0
        self._y_offset    = 0
        self._x_offset    = 0
        self._font        = ("Microsoft YaHei UI", 9)
        self._hdr_font    = ("Microsoft YaHei UI", 9, "bold")
        self._sync_locked = False   # 防止循环触发同步

        self._build_ui()
        self.after(30, self._calc_col_widths)

    def _build_ui(self):
        # 固定表头
        self.hdr_canvas = tk.Canvas(self, height=CELL_H + 2,
                                    bg=HEADER_BG, highlightthickness=0)
        self.hdr_canvas.pack(fill="x", side="top")

        # 底部水平滚动条
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal")
        self.h_scroll.pack(side="bottom", fill="x")

        # 内容行
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        if self._show_vscroll:
            self.v_scroll = ttk.Scrollbar(body, orient="vertical")
            self.v_scroll.pack(side="right", fill="y")
        else:
            self.v_scroll = None

        self.canvas = tk.Canvas(body, bg=BG, highlightthickness=0,
                                xscrollcommand=self.h_scroll.set)
        if self.v_scroll:
            self.canvas.config(yscrollcommand=self.v_scroll.set)
            self.v_scroll.config(command=self._on_vscroll)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.h_scroll.config(command=self._on_hscroll)

        self.canvas.bind("<Configure>",  lambda e: self._render())
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>",   lambda e: self._mouse_scroll(-3))
        self.canvas.bind("<Button-5>",   lambda e: self._mouse_scroll(3))

    # ── 列宽计算 ────────────────────────────────
    def _calc_col_widths(self):
        import tkinter.font as tkfont
        mf = tkfont.Font(font=self._font)
        hf = tkfont.Font(font=self._hdr_font)
        widths = []
        for col in self.columns:
            w = hf.measure(str(col)) + CELL_PAD * 2
            for row in self.data[:200]:
                cw = mf.measure(str(row.get(col, ""))) + CELL_PAD * 2
                if cw > w:
                    w = cw
            widths.append(max(w, 60))
        self._col_widths = widths
        self._total_w = sum(widths)
        total_h = len(self.data) * CELL_H
        self.canvas.config(scrollregion=(0, 0, self._total_w, total_h))
        self.hdr_canvas.config(scrollregion=(0, 0, self._total_w, CELL_H))
        self.after(20, self._draw_header)
        self.after(40, self._render)

    # ── 表头绘制 ────────────────────────────────
    def _draw_header(self):
        self.hdr_canvas.delete("all")
        x = -self._x_offset
        for i, col in enumerate(self.columns):
            w = self._col_widths[i] if i < len(self._col_widths) else 80
            self.hdr_canvas.create_rectangle(
                x, 0, x + w, CELL_H, fill=HEADER_BG, outline="#3A5CF0")
            self.hdr_canvas.create_text(
                x + w // 2, CELL_H // 2, text=str(col),
                fill=HEADER_FG, font=self._hdr_font, anchor="center")
            x += w

    # ── 内容渲染（虚拟滚动核心）────────────────
    def _render(self, *_):
        self.canvas.delete("all")
        ch = self.canvas.winfo_height()
        if ch < 2 or not self._col_widths:
            return

        import tkinter.font as tkfont
        mf = tkfont.Font(font=self._font)

        first = self._y_offset // CELL_H
        visible = ch // CELL_H + 2
        last = min(first + visible, len(self.data))

        tag_bg = {
            "added":   ADDED_BG,
            "deleted": DELETED_BG,
            "changed": CHANGED_BG,
            "same":    SAME_BG,
            "empty":   EMPTY_BG,
        }

        for ri in range(first, last):
            row   = self.data[ri]
            tag   = self.row_tags[ri] if ri < len(self.row_tags) else "same"
            diffs = self.diff_cells[ri] if ri < len(self.diff_cells) else set()
            row_bg = tag_bg.get(tag, SAME_BG)
            y0 = ri * CELL_H - self._y_offset
            y1 = y0 + CELL_H
            x  = -self._x_offset

            for ci, col in enumerate(self.columns):
                cw  = self._col_widths[ci]
                val = str(row.get(col, ""))
                # 单元格背景：差异单元格加深
                cell_bg = DIFF_CELL if (tag == "changed" and col in diffs) else row_bg
                self.canvas.create_rectangle(
                    x, y0, x + cw, y1, fill=cell_bg, outline="#E0E0E0")
                # 文字截断
                disp = val
                if mf.measure(disp) > cw - CELL_PAD * 2:
                    while disp and mf.measure(disp + "…") > cw - CELL_PAD * 2:
                        disp = disp[:-1]
                    disp += "…"
                self.canvas.create_text(
                    x + CELL_PAD, y0 + CELL_H // 2,
                    text=disp, fill="#222222",
                    font=self._font, anchor="w")
                x += cw

        # 更新纵向滚动条
        total_h = len(self.data) * CELL_H
        cv_h = self.canvas.winfo_height()
        if total_h > 0 and self.v_scroll:
            top = self._y_offset / total_h
            bot = min((self._y_offset + cv_h) / total_h, 1.0)
            self.v_scroll.set(top, bot)

    # ── 纵向滚动 ────────────────────────────────
    def _on_vscroll(self, action, *args):
        self._set_y(action, args)
        self._notify_sync()

    def _set_y(self, action, args):
        total_h = len(self.data) * CELL_H
        cv_h = self.canvas.winfo_height()
        max_off = max(0, total_h - cv_h)
        if action == "moveto":
            self._y_offset = int(float(args[0]) * total_h)
        elif action == "scroll":
            amt  = int(args[0])
            unit = args[1]
            self._y_offset += amt * (CELL_H if unit == "units" else cv_h)
        self._y_offset = max(0, min(self._y_offset, max_off))
        self._render()

    def _notify_sync(self):
        if not self._sync_locked and self._on_scroll_cb:
            self._on_scroll_cb(self._y_offset)

    def sync_y(self, y_offset):
        """由外部（对端）调用，同步纵向位置"""
        if self._sync_locked:
            return
        self._sync_locked = True
        total_h = len(self.data) * CELL_H
        cv_h = self.canvas.winfo_height()
        max_off = max(0, total_h - cv_h)
        self._y_offset = max(0, min(y_offset, max_off))
        self._render()
        self._sync_locked = False

    # ── 横向滚动 ────────────────────────────────
    def _on_hscroll(self, action, *args):
        cv_w = self.canvas.winfo_width()
        max_off = max(0, self._total_w - cv_w)
        if action == "moveto":
            self._x_offset = int(float(args[0]) * self._total_w)
        elif action == "scroll":
            amt  = int(args[0])
            unit = args[1]
            self._x_offset += amt * (40 if unit == "units" else cv_w)
        self._x_offset = max(0, min(self._x_offset, max_off))
        self._draw_header()
        self._render()

    def _on_mousewheel(self, event):
        self._mouse_scroll(-event.delta // 30)

    def _mouse_scroll(self, n):
        self._set_y("scroll", (n, "units"))
        self._notify_sync()

    def scroll_to_top(self):
        self._y_offset = 0
        self._render()

    # ── 数据替换（过滤后重绘） ──────────────────
    def update_data(self, data, row_tags, diff_cells):
        self.data       = data
        self.row_tags   = row_tags
        self.diff_cells = diff_cells
        self._y_offset  = 0
        self._x_offset  = 0
        self._calc_col_widths()


# ──────────────────────────────────────────────
# 左右并排对比容器
# ──────────────────────────────────────────────
class SideBySideView(tk.Frame):
    """
    左侧=文件A，右侧=文件B，中间分隔线 + 行号列联动。
    paired_rows : list of (row_a, row_b, tag, diff_set)
      row_a/row_b : dict | None
      tag         : 'same'/'changed'/'added'/'deleted'
      diff_set    : set of 列名（changed 行中不同的字段）
    """
    def __init__(self, master, cols_a, cols_b, paired_rows, **kw):
        super().__init__(master, bg=BG, **kw)
        self._cols_a = cols_a
        self._cols_b = cols_b
        self._paired = paired_rows
        self._build(paired_rows)

    def _split_data(self, paired):
        """将 paired_rows 拆分成左右各自的数据列表"""
        data_a, data_b = [], []
        tags_a, tags_b = [], []
        diff_a, diff_b = [], []

        for row_a, row_b, tag, diff_set in paired:
            if tag == "added":
                # B 有 A 无
                data_a.append({})
                tags_a.append("empty")
                diff_a.append(set())
                data_b.append(row_b if row_b else {})
                tags_b.append("added")
                diff_b.append(set())
            elif tag == "deleted":
                # A 有 B 无
                data_a.append(row_a if row_a else {})
                tags_a.append("deleted")
                diff_a.append(set())
                data_b.append({})
                tags_b.append("empty")
                diff_b.append(set())
            else:
                data_a.append(row_a if row_a else {})
                tags_a.append(tag)
                diff_a.append(diff_set)
                data_b.append(row_b if row_b else {})
                tags_b.append(tag)
                diff_b.append(diff_set)

        return data_a, tags_a, diff_a, data_b, tags_b, diff_b

    def _build(self, paired):
        data_a, tags_a, diff_a, data_b, tags_b, diff_b = self._split_data(paired)

        # 行号列（独立 Canvas，与两侧同步）
        lno_frame = tk.Frame(self, bg=BG, width=46)
        lno_frame.pack(side="left", fill="y")
        lno_frame.pack_propagate(False)

        # 行号表头
        lno_hdr = tk.Canvas(lno_frame, height=CELL_H + 2,
                            bg=HEADER_BG, highlightthickness=0, width=46)
        lno_hdr.pack(fill="x")
        lno_hdr.create_text(23, CELL_H // 2, text="#",
                            fill=HEADER_FG, font=("Microsoft YaHei UI", 9, "bold"))

        self._lno_canvas = tk.Canvas(lno_frame, bg="#EAEEF8",
                                     highlightthickness=0, width=46)
        self._lno_canvas.pack(fill="both", expand=True)
        self._lno_total = len(paired)

        # 左侧
        self._left = SideTable(
            self, self._cols_a, data_a, tags_a, diff_a,
            on_scroll_cb=self._left_scrolled,
            show_vscroll=False)
        self._left.pack(side="left", fill="both", expand=True)

        # 分隔线
        div = tk.Frame(self, bg=DIVIDER_CLR, width=3)
        div.pack(side="left", fill="y")
        div.pack_propagate(False)

        # 右侧（带纵向滚动条）
        self._right = SideTable(
            self, self._cols_b, data_b, tags_b, diff_b,
            on_scroll_cb=self._right_scrolled,
            show_vscroll=True)
        self._right.pack(side="left", fill="both", expand=True)

        # 延迟渲染行号
        self.after(60, self._render_lno)
        self._left.canvas.bind("<Configure>", lambda e: self._render_lno())

    def _render_lno(self, offset=None):
        c = self._lno_canvas
        c.delete("all")
        ch = c.winfo_height()
        if ch < 2:
            return
        y_off = offset if offset is not None else self._left._y_offset
        first = y_off // CELL_H
        visible = ch // CELL_H + 2
        last = min(first + visible, self._lno_total)
        for ri in range(first, last):
            y0 = ri * CELL_H - y_off
            y1 = y0 + CELL_H
            c.create_rectangle(0, y0, 46, y1, fill="#EAEEF8", outline="#D8DCE8")
            c.create_text(23, y0 + CELL_H // 2, text=str(ri + 1),
                          fill="#888", font=("Microsoft YaHei UI", 8))

    def _left_scrolled(self, y_off):
        self._right.sync_y(y_off)
        self._render_lno(y_off)

    def _right_scrolled(self, y_off):
        self._left.sync_y(y_off)
        self._render_lno(y_off)

    def update_data(self, paired, cols_a=None, cols_b=None):
        if cols_a:
            self._cols_a = cols_a
        if cols_b:
            self._cols_b = cols_b
        self._paired = paired
        self._lno_total = len(paired)
        data_a, tags_a, diff_a, data_b, tags_b, diff_b = self._split_data(paired)
        self._left.update_data(data_a, tags_a, diff_a)
        self._right.update_data(data_b, tags_b, diff_b)
        self._render_lno(0)


# ──────────────────────────────────────────────
# 主应用
# ──────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WPS 表格对比工具 — 左右并排视图")
        self.geometry("1400x820")
        self.minsize(1000, 600)
        self.configure(bg=BG)

        self._df1 = None
        self._df2 = None
        self._path1 = tk.StringVar(value="未选择")
        self._path2 = tk.StringVar(value="未选择")
        self._sheet1_var = tk.StringVar()
        self._sheet2_var = tk.StringVar()
        self._key_vars   = {}
        # 保存完整对比结果用于过滤
        self._all_paired = []
        self._cols_a     = []
        self._cols_b     = []
        self._sbsview    = None

        self._build_ui()

    # ── 界面搭建 ────────────────────────────────
    def _build_ui(self):
        # 顶栏
        toolbar = tk.Frame(self, bg=ACCENT, padx=10, pady=6)
        toolbar.pack(fill="x", side="top")
        tk.Label(toolbar, text="📊  WPS 表格对比工具  —  左右并排",
                 bg=ACCENT, fg="white",
                 font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")

        # 文件选择
        file_frame = tk.Frame(self, bg=PANEL_BG, padx=12, pady=8)
        file_frame.pack(fill="x", padx=10, pady=(8, 0))
        self._make_file_row(file_frame, "文件 A（左）：", self._path1,
                            self._sheet1_var, 0, self._load_file1)
        self._make_file_row(file_frame, "文件 B（右）：", self._path2,
                            self._sheet2_var, 1, self._load_file2)

        # 关键字段
        key_outer = tk.Frame(self, bg=PANEL_BG, padx=12, pady=6)
        key_outer.pack(fill="x", padx=10, pady=(4, 0))
        tk.Label(key_outer,
                 text="比对关键字段（勾选用于行匹配；不勾选则按行号顺序对比）：",
                 bg=PANEL_BG, fg="#555",
                 font=("Microsoft YaHei UI", 9)).pack(anchor="w")
        self._key_frame = tk.Frame(key_outer, bg=PANEL_BG)
        self._key_frame.pack(fill="x")

        # 操作栏
        btn_bar = tk.Frame(self, bg=BG, pady=5)
        btn_bar.pack(fill="x", padx=10)

        self._compare_btn = tk.Button(
            btn_bar, text="▶  开始对比", bg=ACCENT, fg="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=16, pady=5, cursor="hand2",
            command=self._start_compare)
        self._compare_btn.pack(side="left", padx=(0, 8))

        tk.Button(btn_bar, text="↺  重置", bg="#888", fg="white",
                  font=("Microsoft YaHei UI", 10), relief="flat",
                  padx=12, pady=5, cursor="hand2",
                  command=self._reset).pack(side="left")

        # 图例
        legend = tk.Frame(btn_bar, bg=BG)
        legend.pack(side="right")
        for bg_c, label in [
            (CHANGED_BG, "修改行"),
            (DIFF_CELL,  "修改单元格"),
            (ADDED_BG,   "新增(B有A无)"),
            (DELETED_BG, "删除(A有B无)"),
            (EMPTY_BG,   "对端空行"),
            (SAME_BG,    "相同"),
        ]:
            tk.Label(legend, text="  ", bg=bg_c,
                     relief="solid", bd=1).pack(side="left")
            tk.Label(legend, text=label, bg=BG,
                     font=("Microsoft YaHei UI", 8), fg="#555").pack(
                side="left", padx=(2, 8))

        # 状态栏
        self._status = tk.StringVar(value="就绪 — 请先加载两个文件")
        tk.Label(self, textvariable=self._status,
                 bg="#E8ECF4", fg="#444",
                 font=("Microsoft YaHei UI", 9),
                 anchor="w", padx=10).pack(fill="x", side="bottom")

        # 结果区
        self._result_area = tk.Frame(self, bg=BG)
        self._result_area.pack(fill="both", expand=True, padx=10, pady=(4, 0))
        tk.Label(self._result_area, text="对比结果将在此处左右并排显示",
                 bg=BG, fg="#AAAAAA",
                 font=("Microsoft YaHei UI", 11)).pack(expand=True)

    def _make_file_row(self, parent, label, path_var, sheet_var, row, cmd):
        tk.Label(parent, text=label, bg=PANEL_BG, width=12,
                 font=("Microsoft YaHei UI", 9, "bold"),
                 fg="#333", anchor="w").grid(row=row, column=0, sticky="w", pady=3)
        tk.Label(parent, textvariable=path_var, bg=PANEL_BG, fg="#555",
                 font=("Microsoft YaHei UI", 9),
                 anchor="w", width=55).grid(row=row, column=1, sticky="w")
        tk.Button(parent, text="浏览…", command=cmd,
                  bg=ACCENT, fg="white", relief="flat",
                  font=("Microsoft YaHei UI", 9),
                  padx=8, cursor="hand2").grid(row=row, column=2, padx=8)
        tk.Label(parent, text="Sheet：", bg=PANEL_BG,
                 font=("Microsoft YaHei UI", 9),
                 fg="#555").grid(row=row, column=3)
        cb = ttk.Combobox(parent, textvariable=sheet_var,
                          width=15, state="readonly")
        cb.grid(row=row, column=4, padx=4)
        if row == 0:
            self._sheet1_cb = cb
        else:
            self._sheet2_cb = cb

    # ── 文件加载 ────────────────────────────────
    def _browse(self):
        return filedialog.askopenfilename(
            title="选择 WPS/Excel 文件",
            filetypes=[("表格文件", "*.xlsx *.xls *.et *.csv"),
                       ("所有文件", "*.*")])

    def _load_file1(self):
        p = self._browse()
        if p:
            self._path1.set(os.path.basename(p))
            self._load_df(p, 1)

    def _load_file2(self):
        p = self._browse()
        if p:
            self._path2.set(os.path.basename(p))
            self._load_df(p, 2)

    def _load_df(self, path, idx):
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path, dtype=str)
                sheets = ["Sheet1"]
            else:
                xl = pd.ExcelFile(path)
                sheets = xl.sheet_names
                df = xl.parse(sheets[0], dtype=str)
            df = df.fillna("")

            if idx == 1:
                self._df1 = df
                self._path1_full = path
                self._sheet1_cb["values"] = sheets
                self._sheet1_var.set(sheets[0])
                self._sheet1_cb.bind("<<ComboboxSelected>>",
                                     lambda e: self._reload_sheet(1))
            else:
                self._df2 = df
                self._path2_full = path
                self._sheet2_cb["values"] = sheets
                self._sheet2_var.set(sheets[0])
                self._sheet2_cb.bind("<<ComboboxSelected>>",
                                     lambda e: self._reload_sheet(2))

            self._update_key_fields()
            self._status.set(
                f"文件 {'A' if idx == 1 else 'B'} 已加载：{os.path.basename(path)}  "
                f"共 {len(df)} 行")
        except Exception as ex:
            messagebox.showerror("读取失败", str(ex))

    def _reload_sheet(self, idx):
        try:
            path  = self._path1_full if idx == 1 else self._path2_full
            sheet = self._sheet1_var.get() if idx == 1 else self._sheet2_var.get()
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path, dtype=str)
            else:
                df = pd.read_excel(path, sheet_name=sheet, dtype=str)
            df = df.fillna("")
            if idx == 1:
                self._df1 = df
            else:
                self._df2 = df
            self._update_key_fields()
            self._status.set(f"已切换 Sheet: {sheet}")
        except Exception as ex:
            messagebox.showerror("切换 Sheet 失败", str(ex))

    # ── 关键字段复选框 ───────────────────────────
    def _update_key_fields(self):
        for w in self._key_frame.winfo_children():
            w.destroy()
        self._key_vars.clear()
        cols1 = list(self._df1.columns) if self._df1 is not None else []
        cols2 = list(self._df2.columns) if self._df2 is not None else []
        common = [c for c in cols1 if c in cols2]
        if not common:
            tk.Label(self._key_frame,
                     text="（请先加载两个文件，将显示公共列）",
                     bg=PANEL_BG, fg="#AAA",
                     font=("Microsoft YaHei UI", 9)).pack(side="left")
            return
        per_row = 8
        row_f = None
        for i, col in enumerate(common):
            if i % per_row == 0:
                row_f = tk.Frame(self._key_frame, bg=PANEL_BG)
                row_f.pack(anchor="w")
            var = tk.BooleanVar(value=False)
            self._key_vars[col] = var
            tk.Checkbutton(row_f, text=col, variable=var,
                           bg=PANEL_BG, fg="#333",
                           font=("Microsoft YaHei UI", 9),
                           activebackground=PANEL_BG).pack(side="left", padx=4)

    # ── 对比逻辑 ────────────────────────────────
    def _start_compare(self):
        if self._df1 is None or self._df2 is None:
            messagebox.showwarning("提示", "请先加载两个文件！")
            return
        self._compare_btn.config(state="disabled", text="对比中…")
        self._status.set("正在对比，请稍候…")
        threading.Thread(target=self._do_compare, daemon=True).start()

    def _do_compare(self):
        try:
            df1  = self._df1.copy()
            df2  = self._df2.copy()
            keys = [c for c, v in self._key_vars.items() if v.get()]
            cols_a = list(df1.columns)
            cols_b = list(df2.columns)

            paired = []   # (row_a, row_b, tag, diff_set)

            if keys:
                # ── 按关键字段匹配 ──
                idx1 = {}
                for _, r in df1.iterrows():
                    k = tuple(str(r.get(c, "")) for c in keys)
                    idx1.setdefault(k, []).append(dict(r))

                idx2 = {}
                for _, r in df2.iterrows():
                    k = tuple(str(r.get(c, "")) for c in keys)
                    idx2.setdefault(k, []).append(dict(r))

                all_keys = list(dict.fromkeys(
                    list(idx1.keys()) + list(idx2.keys())))

                for k in all_keys:
                    rows1 = idx1.get(k, [])
                    rows2 = idx2.get(k, [])
                    mx = max(len(rows1), len(rows2), 1)
                    for i in range(mx):
                        r1 = rows1[i] if i < len(rows1) else None
                        r2 = rows2[i] if i < len(rows2) else None
                        if r1 is not None and r2 is None:
                            paired.append((r1, None, "deleted", set()))
                        elif r1 is None and r2 is not None:
                            paired.append((None, r2, "added", set()))
                        else:
                            common_c = [c for c in cols_a if c in cols_b]
                            diffs = {c for c in common_c
                                     if str(r1.get(c,"")) != str(r2.get(c,""))}
                            tag = "changed" if diffs else "same"
                            paired.append((r1, r2, tag, diffs))
            else:
                # ── 按行号对比 ──
                max_r = max(len(df1), len(df2))
                for i in range(max_r):
                    r1 = dict(df1.iloc[i]) if i < len(df1) else None
                    r2 = dict(df2.iloc[i]) if i < len(df2) else None
                    if r1 is not None and r2 is None:
                        paired.append((r1, None, "deleted", set()))
                    elif r1 is None and r2 is not None:
                        paired.append((None, r2, "added", set()))
                    else:
                        common_c = [c for c in cols_a if c in cols_b]
                        diffs = {c for c in common_c
                                 if str(r1.get(c,"")) != str(r2.get(c,""))}
                        tag = "changed" if diffs else "same"
                        paired.append((r1, r2, tag, diffs))

            cnt = {"added":0,"deleted":0,"changed":0,"same":0}
            for _, _, t, _ in paired:
                cnt[t] = cnt.get(t, 0) + 1

            self.after(0, lambda: self._show_result(
                cols_a, cols_b, paired, cnt))
        except Exception as ex:
            self.after(0, lambda: (
                messagebox.showerror("对比失败", str(ex)),
                self._compare_btn.config(state="normal", text="▶  开始对比")
            ))

    # ── 显示结果 ────────────────────────────────
    def _show_result(self, cols_a, cols_b, paired, cnt):
        self._all_paired = paired
        self._cols_a = cols_a
        self._cols_b = cols_b

        for w in self._result_area.winfo_children():
            w.destroy()

        # ── 过滤 / 搜索栏 ──
        filter_bar = tk.Frame(self._result_area, bg=BG, pady=4)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="显示：", bg=BG,
                 font=("Microsoft YaHei UI", 9)).pack(side="left")

        self._filter_vars = {}
        for tag, label, color in [
            ("all",     f"全部({len(paired)})", ACCENT),
            ("changed", f"修改({cnt['changed']})", "#E6A000"),
            ("added",   f"新增({cnt['added']})",   "#28A745"),
            ("deleted", f"删除({cnt['deleted']})", "#DC3545"),
            ("same",    f"相同({cnt['same']})",    "#888"),
        ]:
            var = tk.BooleanVar(value=True)
            self._filter_vars[tag] = var
            tk.Checkbutton(filter_bar, text=label, variable=var,
                           bg=BG, fg=color,
                           font=("Microsoft YaHei UI", 9, "bold"),
                           activebackground=BG,
                           command=self._apply_filter
                           ).pack(side="left", padx=5)

        tk.Label(filter_bar, text="   搜索：", bg=BG,
                 font=("Microsoft YaHei UI", 9)).pack(side="left")
        self._search_var = tk.StringVar()
        se = ttk.Entry(filter_bar, textvariable=self._search_var, width=20)
        se.pack(side="left")
        tk.Button(filter_bar, text="🔍", bg=ACCENT, fg="white",
                  relief="flat", font=("Microsoft YaHei UI", 9),
                  padx=6, cursor="hand2",
                  command=self._apply_filter).pack(side="left", padx=4)
        se.bind("<Return>", lambda e: self._apply_filter())

        # ── 表头标题行（文件名） ──
        title_bar = tk.Frame(self._result_area, bg=BG)
        title_bar.pack(fill="x")
        tk.Frame(title_bar, bg=BG, width=46).pack(side="left")  # 行号列占位
        tk.Label(title_bar,
                 text=f"  📄 文件 A（左）：{self._path1.get()}",
                 bg="#E8F0FE", fg="#2A4DB5",
                 font=("Microsoft YaHei UI", 9, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Frame(title_bar, bg=DIVIDER_CLR, width=3).pack(side="left", fill="y")
        tk.Label(title_bar,
                 text=f"  📄 文件 B（右）：{self._path2.get()}",
                 bg="#E8F5E9", fg="#1A6B2A",
                 font=("Microsoft YaHei UI", 9, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True, padx=(2, 0))

        # ── 左右并排视图 ──
        self._sbsview = SideBySideView(
            self._result_area, cols_a, cols_b, paired)
        self._sbsview.pack(fill="both", expand=True)

        self._compare_btn.config(state="normal", text="▶  开始对比")
        self._status.set(
            f"对比完成 — 共 {len(paired)} 行  |  "
            f"修改: {cnt['changed']}  新增: {cnt['added']}  "
            f"删除: {cnt['deleted']}  相同: {cnt['same']}")

    # ── 过滤逻辑 ────────────────────────────────
    def _apply_filter(self):
        if self._sbsview is None:
            return
        show_tags = set()
        if self._filter_vars.get("all") and self._filter_vars["all"].get():
            show_tags = {"added", "deleted", "changed", "same"}
        else:
            for t in ("added", "deleted", "changed", "same"):
                if self._filter_vars.get(t) and self._filter_vars[t].get():
                    show_tags.add(t)

        q = self._search_var.get().lower()
        filtered = []
        for row_a, row_b, tag, diff_set in self._all_paired:
            if tag not in show_tags:
                continue
            if q:
                text_a = " ".join(str(v) for v in (row_a or {}).values())
                text_b = " ".join(str(v) for v in (row_b or {}).values())
                if q not in text_a.lower() and q not in text_b.lower():
                    continue
            filtered.append((row_a, row_b, tag, diff_set))

        self._sbsview.update_data(filtered)

    # ── 重置 ────────────────────────────────────
    def _reset(self):
        self._df1 = self._df2 = None
        self._sbsview = None
        self._all_paired = []
        self._path1.set("未选择")
        self._path2.set("未选择")
        self._sheet1_var.set("")
        self._sheet2_var.set("")
        self._sheet1_cb["values"] = []
        self._sheet2_cb["values"] = []
        for w in self._key_frame.winfo_children():
            w.destroy()
        self._key_vars.clear()
        for w in self._result_area.winfo_children():
            w.destroy()
        tk.Label(self._result_area, text="对比结果将在此处左右并排显示",
                 bg=BG, fg="#AAAAAA",
                 font=("Microsoft YaHei UI", 11)).pack(expand=True)
        self._status.set("已重置")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
