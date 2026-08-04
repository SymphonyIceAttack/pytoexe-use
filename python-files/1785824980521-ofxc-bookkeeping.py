#!/usr/bin/env python3
"""极简记账 - 桌面 GUI 版（tkinter + Canvas 圆角）"""

import json
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# ==================== 常量 ====================
DATA_FILE = "bookkeeping_data.json"
DEFAULT_EXPENSE_CATS = ["餐饮", "交通", "购物", "娱乐", "居住", "医疗", "教育", "其他"]
DEFAULT_INCOME_CATS = ["工资", "奖金", "红包", "理财", "其他"]

CAT_ICONS = {
    "餐饮": "🍜", "交通": "🚗", "购物": "🛍️", "娱乐": "🎮",
    "居住": "🏠", "医疗": "💊", "教育": "📚", "其他": "📌",
    "工资": "💼", "奖金": "🎁", "红包": "🧧", "理财": "📈",
}

GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#3b82f6"
BG = "#f5f5f7"
CARD = "#ffffff"
TEXT = "#1d1d1f"
SECONDARY = "#86868b"
BORDER = "#e5e5ea"
RADIUS = 14

# ==================== 圆角工具 ====================
def draw_rounded_rect(canvas, x1, y1, x2, y2, r=RADIUS, fill=CARD, outline=BORDER, tags=""):
    """在 Canvas 上绘制圆角矩形（底层填充 + 边框线）"""
    d = 2 * r
    kw_fill = {"fill": fill, "outline": "", "tags": tags}
    # 四个角弧形填充
    canvas.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style="pieslice", **kw_fill)
    canvas.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style="pieslice", **kw_fill)
    canvas.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style="pieslice", **kw_fill)
    canvas.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style="pieslice", **kw_fill)
    # 中间矩形填充
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kw_fill)
    canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kw_fill)
    # 边框
    kw_line = {"fill": outline, "tags": tags}
    canvas.create_line(x1 + r, y1, x2 - r, y1, **kw_line)
    canvas.create_line(x1 + r, y2, x2 - r, y2, **kw_line)
    canvas.create_line(x1, y1 + r, x1, y2 - r, **kw_line)
    canvas.create_line(x2, y1 + r, x2, y2 - r, **kw_line)
    canvas.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90, style="arc", outline=outline, tags=tags)
    canvas.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90, style="arc", outline=outline, tags=tags)
    canvas.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90, style="arc", outline=outline, tags=tags)
    canvas.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90, style="arc", outline=outline, tags=tags)


# ==================== 数据层 ====================
def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_records():
    return _load_json(DATA_FILE, [])

def save_records(records):
    _save_json(DATA_FILE, records)

def load_categories():
    data = _load_json("bookkeeping_categories.json", None)
    if data and "expense" in data and "income" in data:
        return data
    return {"expense": list(DEFAULT_EXPENSE_CATS), "income": list(DEFAULT_INCOME_CATS)}

def save_categories(cats):
    _save_json("bookkeeping_categories.json", cats)

def add_record(record):
    records = load_records()
    records.insert(0, {
        "id": uuid.uuid4().hex[:10],
        "type": record["type"],
        "category": record["category"],
        "amount": float(record["amount"]),
        "note": record.get("note", ""),
        "date": record["date"],
    })
    save_records(records)

def delete_record(rid):
    records = load_records()
    records = [r for r in records if r["id"] != rid]
    save_records(records)


# ==================== GUI 应用 ====================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("极简记账")
        self.root.geometry("1020x720")
        self.root.minsize(800, 540)
        self.root.configure(bg=BG)

        self.categories = load_categories()
        self.current_month = datetime.now().strftime("%Y-%m")

        self._setup_style()
        self._build_ui()
        self._refresh_dashboard()

    # ---------- 样式 ----------
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Microsoft YaHei", 13, "bold"),
                        padding=[24, 10], background=BG, borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", CARD)],
                  foreground=[("selected", TEXT)])
        style.configure("TFrame", background=BG)
        style.configure("TLabelframe", background=BG, borderwidth=0)
        style.configure("TLabelframe.Label", font=("Microsoft YaHei", 13), background=BG)
        style.configure("TButton", font=("Microsoft YaHei", 11), padding=[16, 6])
        style.configure("TCombobox", font=("Microsoft YaHei", 11), padding=8)
        style.configure("TEntry", font=("Microsoft YaHei", 11), padding=8)
        style.configure("TRadiobutton", font=("Microsoft YaHei", 11), background=BG)

    # ---------- 整体布局 ----------
    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self.tab_dash = ttk.Frame(self.notebook)
        self.tab_add = ttk.Frame(self.notebook)
        self.tab_bills = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dash, text="  📊  概览  ")
        self.notebook.add(self.tab_add, text="  ✏️  记账  ")
        self.notebook.add(self.tab_bills, text="  📋  账单  ")
        self.notebook.add(self.tab_settings, text="  ⚙️  设置  ")

        self._build_dashboard()
        self._build_add()
        self._build_bills()
        self._build_settings()

    def _on_tab_change(self, event):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0:   self._refresh_dashboard()
        elif idx == 2: self._refresh_bills()
        elif idx == 3: self._refresh_settings()

    # ==================== 仪表盘 ====================
    def _build_dashboard(self):
        self.dash_container = tk.Frame(self.tab_dash, bg=BG)
        self.dash_container.pack(fill="both", expand=True, padx=24, pady=(20, 10))

    def _refresh_dashboard(self):
        for w in self.dash_container.winfo_children():
            w.destroy()

        records = load_records()
        month_records = [r for r in records if r["date"].startswith(self.current_month)]
        total_income = sum(r["amount"] for r in month_records if r["type"] == "income")
        total_expense = sum(r["amount"] for r in month_records if r["type"] == "expense")
        balance = total_income - total_expense

        # 三张圆角卡片
        cards_data = [
            ("本月收入", f"¥{total_income:,.2f}", GREEN),
            ("本月支出", f"¥{total_expense:,.2f}", RED),
            ("本月结余", f"¥{balance:,.2f}", TEXT),
        ]
        card_row = tk.Frame(self.dash_container, bg=BG)
        card_row.pack(fill="x")
        for i, (label, value, color) in enumerate(cards_data):
            c = tk.Canvas(card_row, bg=BG, highlightthickness=0, height=110)
            c.pack(side="left", expand=True, fill="x", padx=(0 if i == 0 else 10, 0))
            c.bind("<Configure>", lambda e, canvas=c, lbl=label, val=value, clr=color: self._draw_card(canvas, lbl, val, clr))

        # 间隔
        tk.Frame(self.dash_container, bg=BG, height=16).pack()

        # 支出排行
        rank_label = tk.Label(self.dash_container, text="支出分类排行",
                              font=("Microsoft YaHei", 14, "bold"),
                              fg=SECONDARY, bg=BG)
        rank_label.pack(anchor="w", pady=(0, 10))

        expense_by_cat = {}
        for r in month_records:
            if r["type"] == "expense":
                expense_by_cat[r["category"]] = expense_by_cat.get(r["category"], 0) + r["amount"]

        rank_frame = tk.Frame(self.dash_container, bg=BG)
        rank_frame.pack(fill="both", expand=True)

        if not expense_by_cat:
            tk.Label(rank_frame, text="本月暂无支出记录",
                     font=("Microsoft YaHei", 12), fg=SECONDARY,
                     bg=BG).pack(pady=30)
            return

        sorted_cats = sorted(expense_by_cat.items(), key=lambda x: -x[1])
        for cat, amt in sorted_cats:
            row_canvas = tk.Canvas(rank_frame, bg=BG, highlightthickness=0, height=48)
            row_canvas.pack(fill="x", pady=2)
            row_canvas.bind("<Configure>", lambda e, c=row_canvas, cat_name=cat, amt_val=amt:
                            self._draw_rank_row(c, cat_name, amt_val))

    def _draw_card(self, canvas, label, value, color):
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 10 or h < 10:
            return
        draw_rounded_rect(canvas, 2, 2, w - 2, h - 2)
        cx = w // 2
        canvas.create_text(cx, h * 0.32, text=label, font=("Microsoft YaHei", 13),
                           fill=SECONDARY, anchor="center")
        canvas.create_text(cx, h * 0.68, text=value, font=("Microsoft YaHei", 24, "bold"),
                           fill=color, anchor="center")

    def _draw_rank_row(self, canvas, cat_name, amt):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w < 10:
            return
        draw_rounded_rect(canvas, 1, 1, w - 1, 47)
        canvas.create_text(16, 24, text=f"{CAT_ICONS.get(cat_name, '📌')}  {cat_name}",
                           font=("Microsoft YaHei", 12), fill=TEXT, anchor="w")
        canvas.create_text(w - 16, 24, text=f"¥{amt:,.2f}",
                           font=("Microsoft YaHei", 13, "bold"), fill=RED, anchor="e")

    # ==================== 记账 ====================
    def _build_add(self):
        container = ttk.Frame(self.tab_add)
        container.pack(fill="both", expand=True)
        inner = ttk.Frame(container)
        inner.pack(expand=True)

        # 类型切换
        self.record_type = tk.StringVar(value="expense")
        type_frame = tk.Frame(inner, bg=BG)
        type_frame.pack(fill="x", pady=(0, 18))
        rb1 = tk.Radiobutton(type_frame, text="💰 支出", variable=self.record_type,
                             value="expense", font=("Microsoft YaHei", 14, "bold"),
                             bg=BG, fg=RED, selectcolor=BG, activebackground=BG,
                             indicatoron=0, command=self._on_type_change)
        rb1.pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=10)
        rb2 = tk.Radiobutton(type_frame, text="💵 收入", variable=self.record_type,
                             value="income", font=("Microsoft YaHei", 14, "bold"),
                             bg=BG, fg=GREEN, selectcolor=BG, activebackground=BG,
                             indicatoron=0, command=self._on_type_change)
        rb2.pack(side="left", expand=True, fill="x", padx=(6, 0), ipady=10)

        # 分类
        tk.Label(inner, text="分类", font=("Microsoft YaHei", 11),
                 fg=SECONDARY, bg=BG).pack(anchor="w", pady=(0, 4))
        self.cat_combo = ttk.Combobox(inner, state="readonly", width=30)
        self.cat_combo.pack(fill="x", ipady=4, pady=(0, 14))
        self._update_category_combo()

        # 金额
        tk.Label(inner, text="金额", font=("Microsoft YaHei", 11),
                 fg=SECONDARY, bg=BG).pack(anchor="w", pady=(0, 4))
        self.amount_entry = tk.Entry(inner, font=("Microsoft YaHei", 14),
                                     bg=CARD, relief="flat", bd=0, highlightthickness=0)
        # 用 Canvas 画圆角输入框背景
        amt_frame = tk.Frame(inner, bg=BG)
        amt_frame.pack(fill="x", pady=(0, 14))
        self._amt_canvas = tk.Canvas(amt_frame, bg=BG, highlightthickness=0, height=44)
        self._amt_canvas.pack(fill="x")
        self._amt_canvas.bind("<Configure>",
            lambda e: draw_rounded_rect(self._amt_canvas, 1, 1,
                                        self._amt_canvas.winfo_width() - 1, 43,
                                        r=10, fill=CARD, outline=BORDER))
        self._amt_canvas.create_window(14, 22, window=self.amount_entry, anchor="w")
        self.amount_entry.bind("<FocusIn>", lambda e: self._highlight_input(self._amt_canvas, True))
        self.amount_entry.bind("<FocusOut>", lambda e: self._highlight_input(self._amt_canvas, False))

        # 备注
        tk.Label(inner, text="备注（选填）", font=("Microsoft YaHei", 11),
                 fg=SECONDARY, bg=BG).pack(anchor="w", pady=(0, 4))
        self.note_entry = tk.Entry(inner, font=("Microsoft YaHei", 14),
                                   bg=CARD, relief="flat", bd=0)
        note_frame = tk.Frame(inner, bg=BG)
        note_frame.pack(fill="x", pady=(0, 14))
        self._note_canvas = tk.Canvas(note_frame, bg=BG, highlightthickness=0, height=44)
        self._note_canvas.pack(fill="x")
        self._note_canvas.bind("<Configure>",
            lambda e: draw_rounded_rect(self._note_canvas, 1, 1,
                                        self._note_canvas.winfo_width() - 1, 43,
                                        r=10, fill=CARD, outline=BORDER))
        self._note_canvas.create_window(14, 22, window=self.note_entry, anchor="w")

        # 日期
        tk.Label(inner, text="日期", font=("Microsoft YaHei", 11),
                 fg=SECONDARY, bg=BG).pack(anchor="w", pady=(0, 4))
        self.date_entry = tk.Entry(inner, font=("Microsoft YaHei", 14),
                                   bg=CARD, relief="flat", bd=0)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_frame = tk.Frame(inner, bg=BG)
        date_frame.pack(fill="x", pady=(0, 24))
        self._date_canvas = tk.Canvas(date_frame, bg=BG, highlightthickness=0, height=44)
        self._date_canvas.pack(fill="x")
        self._date_canvas.bind("<Configure>",
            lambda e: draw_rounded_rect(self._date_canvas, 1, 1,
                                        self._date_canvas.winfo_width() - 1, 43,
                                        r=10, fill=CARD, outline=BORDER))
        self._date_canvas.create_window(14, 22, window=self.date_entry, anchor="w")

        # 保存按钮（Canvas 圆角）
        btn_frame = tk.Frame(inner, bg=BG, height=52)
        btn_frame.pack(fill="x")
        self._save_canvas = tk.Canvas(btn_frame, bg=BG, highlightthickness=0, height=52)
        self._save_canvas.pack(fill="x")
        self._save_canvas.bind("<Configure>",
            lambda e: self._draw_save_btn())
        self._save_canvas.bind("<Button-1>", lambda e: self._save_record())
        self._save_canvas.bind("<Enter>", lambda e: self._draw_save_btn(hover=True))
        self._save_canvas.bind("<Leave>", lambda e: self._draw_save_btn(hover=False))

    def _highlight_input(self, canvas, focused):
        w = canvas.winfo_width()
        canvas.delete("border")
        if focused:
            draw_rounded_rect(canvas, 1, 1, w - 1, 43, r=10, fill=CARD, outline=BLUE, tags="border")
        else:
            draw_rounded_rect(canvas, 1, 1, w - 1, 43, r=10, fill=CARD, outline=BORDER, tags="border")

    def _draw_save_btn(self, hover=False):
        c = self._save_canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 10:
            return
        fill = "#16a34a" if hover else GREEN
        draw_rounded_rect(c, 1, 1, w - 1, 51, r=12, fill=fill, outline=fill)
        c.create_text(w // 2, 26, text="保存记录",
                      font=("Microsoft YaHei", 15, "bold"), fill="white", anchor="center")

    def _on_type_change(self):
        self._update_category_combo()

    def _update_category_combo(self):
        tp = self.record_type.get()
        cats = self.categories[tp]
        self.cat_combo["values"] = [f"{CAT_ICONS.get(c, '📌')} {c}" for c in cats]
        if cats:
            self.cat_combo.current(0)

    def _save_record(self):
        tp = self.record_type.get()
        idx = self.cat_combo.current()
        cats = self.categories[tp]
        if idx < 0 or idx >= len(cats):
            messagebox.showwarning("提示", "请选择分类")
            return
        category = cats[idx]

        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的正数金额")
            return

        note = self.note_entry.get().strip()
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("提示", "日期格式错误，请使用 YYYY-MM-DD")
            return

        add_record({"type": tp, "category": category, "amount": amount,
                     "note": note, "date": date_str})
        self.amount_entry.delete(0, "end")
        self.note_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.record_type.set("expense")
        self._update_category_combo()

    # ==================== 账单 ====================
    def _build_bills(self):
        # 月份导航
        nav = tk.Frame(self.tab_bills, bg=BG)
        nav.pack(fill="x", padx=24, pady=(18, 10))
        self.prev_btn = tk.Button(nav, text="◀", font=("Microsoft YaHei", 12),
                                  bg=CARD, relief="flat", padx=14, pady=5,
                                  cursor="hand2", command=self._prev_month)
        self.prev_btn.pack(side="left")
        self.month_label = tk.Label(nav, font=("Microsoft YaHei", 15, "bold"),
                                    bg=BG, fg=TEXT)
        self.month_label.pack(side="left", expand=True)
        self.next_btn = tk.Button(nav, text="▶", font=("Microsoft YaHei", 12),
                                  bg=CARD, relief="flat", padx=14, pady=5,
                                  cursor="hand2", command=self._next_month)
        self.next_btn.pack(side="right")

        # 可滚动列表
        list_container = tk.Frame(self.tab_bills, bg=BG)
        list_container.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self.bill_canvas = tk.Canvas(list_container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.bill_canvas.yview)
        self.bill_list_frame = tk.Frame(self.bill_canvas, bg=BG)
        self.bill_list_frame.bind("<Configure>",
            lambda e: self.bill_canvas.configure(scrollregion=self.bill_canvas.bbox("all")))
        self.bill_canvas.create_window((0, 0), window=self.bill_list_frame, anchor="nw")
        self.bill_canvas.configure(yscrollcommand=scrollbar.set)
        self.bill_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bill_canvas.bind_all("<MouseWheel>",
            lambda e: self.bill_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _refresh_bills(self):
        for w in self.bill_list_frame.winfo_children():
            w.destroy()
        y, m = self.current_month.split("-")
        self.month_label.config(text=f"{y}年{int(m)}月")

        records = [r for r in load_records() if r["date"].startswith(self.current_month)]
        records.sort(key=lambda r: r["date"] + r["id"], reverse=True)

        if not records:
            tk.Label(self.bill_list_frame, text="📭\n本月暂无记录",
                     font=("Microsoft YaHei", 14), fg=SECONDARY, bg=BG).pack(pady=40)
            return

        for r in records:
            # 整行 Canvas 圆角卡片
            row_c = tk.Canvas(self.bill_list_frame, bg=BG, highlightthickness=0, height=62)
            row_c.pack(fill="x", pady=2)
            row_c.bind("<Configure>", lambda e, c=row_c, rec=r: self._draw_bill_row(c, rec))

    def _draw_bill_row(self, canvas, rec):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w < 10:
            return
        draw_rounded_rect(canvas, 1, 1, w - 1, 61, r=12)

        # 图标
        icon_bg = "#fee2e2" if rec["type"] == "expense" else "#dcfce7"
        canvas.create_oval(10, 14, 44, 48, fill=icon_bg, outline="")
        canvas.create_text(27, 31, text=CAT_ICONS.get(rec["category"], "📌"),
                           font=("Microsoft YaHei", 17), anchor="center")

        # 分类
        canvas.create_text(54, 24, text=rec["category"],
                           font=("Microsoft YaHei", 12, "bold"), fill=TEXT, anchor="w")
        # 日期 + 备注
        d = rec["date"]
        meta = f"{int(d[5:7])}月{int(d[8:10])}日"
        if rec["note"]:
            meta += f"  ·  {rec['note']}"
        canvas.create_text(54, 44, text=meta,
                           font=("Microsoft YaHei", 10), fill=SECONDARY, anchor="w")

        # 金额
        amt_color = RED if rec["type"] == "expense" else GREEN
        prefix = "-" if rec["type"] == "expense" else "+"
        canvas.create_text(w - 52, 32, text=f"{prefix}¥{rec['amount']:,.2f}",
                           font=("Microsoft YaHei", 13, "bold"), fill=amt_color, anchor="e")

        # 删除按钮
        canvas.create_text(w - 18, 32, text="🗑", font=("Microsoft YaHei", 12),
                           fill=SECONDARY, anchor="e")
        # 删除点击区域
        canvas.tag_bind("all", "<Button-1>", lambda e, rid=rec["id"]: self._hit_test_delete(e, rid))

    def _hit_test_delete(self, event, rid):
        """如果点击在删除图标附近（右 36px 内），触发删除"""
        w = event.widget.winfo_width()
        if event.x > w - 36:
            self._confirm_delete(rid)

    def _prev_month(self):
        y, m = map(int, self.current_month.split("-"))
        if m == 1:
            y, m = y - 1, 12
        else:
            m -= 1
        self.current_month = f"{y}-{m:02d}"
        self._refresh_bills()

    def _next_month(self):
        y, m = map(int, self.current_month.split("-"))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
        self.current_month = f"{y}-{m:02d}"
        self._refresh_bills()

    def _confirm_delete(self, rid):
        if messagebox.askyesno("确认删除", "确定要删除这条记录吗？此操作不可撤销。"):
            delete_record(rid)
            self._refresh_bills()

    # ==================== 设置 ====================
    def _build_settings(self):
        container = tk.Frame(self.tab_settings, bg=BG)
        container.pack(fill="both", expand=True, padx=32, pady=24)

        tk.Label(container, text="💸 支出分类", font=("Microsoft YaHei", 14, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        self._build_cat_section(container, "expense")

        tk.Frame(container, bg=BG, height=24).pack()

        tk.Label(container, text="💰 收入分类", font=("Microsoft YaHei", 14, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        self._build_cat_section(container, "income")

    def _build_cat_section(self, parent, tp):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", pady=(4, 0))
        tag_frame = tk.Frame(frame, bg=BG)
        tag_frame.pack(fill="x", pady=(0, 10))
        setattr(self, f"{tp}_tag_frame", tag_frame)

        add_frame = tk.Frame(frame, bg=BG)
        add_frame.pack(fill="x")
        entry = tk.Entry(add_frame, font=("Microsoft YaHei", 12), bg=CARD,
                         relief="flat", bd=0)
        # 圆角输入框
        entry_canvas = tk.Canvas(add_frame, bg=BG, highlightthickness=0, height=42)
        entry_canvas.pack(side="left", fill="x", expand=True)
        entry_canvas.bind("<Configure>",
            lambda e, c=entry_canvas: draw_rounded_rect(c, 1, 1,
                c.winfo_width() - 1, 41, r=10, fill=CARD, outline=BORDER))
        entry_canvas.create_window(14, 21, window=entry, anchor="w")

        btn = tk.Button(add_frame, text="添加", font=("Microsoft YaHei", 12, "bold"),
                        bg=BLUE, fg="white", relief="flat", padx=20, pady=7,
                        cursor="hand2", activebackground="#2563eb",
                        command=lambda e=entry, t=tp: self._add_cat(e, t))
        btn.pack(side="left", padx=(10, 0))
        setattr(self, f"{tp}_cat_entry", entry)

    def _refresh_settings(self):
        self.categories = load_categories()
        for tp in ("expense", "income"):
            tag_frame = getattr(self, f"{tp}_tag_frame")
            for w in tag_frame.winfo_children():
                w.destroy()
            bg_color = "#fee2e2" if tp == "expense" else "#dcfce7"
            fg_color = "#991b1b" if tp == "expense" else "#166534"
            cats = self.categories[tp]
            for cat in cats:
                tag = tk.Frame(tag_frame, bg=bg_color, padx=12, pady=5,
                               highlightthickness=0)
                tag.pack(side="left", padx=(0, 8), pady=4)
                tk.Label(tag, text=f"{CAT_ICONS.get(cat, '📌')} {cat}",
                         font=("Microsoft YaHei", 11), bg=bg_color, fg=fg_color).pack(side="left")
                if len(cats) > 1:
                    x_btn = tk.Label(tag, text=" ✕", font=("Microsoft YaHei", 10),
                                     bg=bg_color, fg=fg_color, cursor="hand2")
                    x_btn.pack(side="left", padx=(3, 0))
                    x_btn.bind("<Button-1>", lambda e, t=tp, c=cat: self._del_cat(t, c))
        self._update_category_combo()

    def _add_cat(self, entry, tp):
        name = entry.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入分类名称")
            return
        if name in self.categories[tp]:
            messagebox.showwarning("提示", "该分类已存在")
            return
        self.categories[tp].append(name)
        save_categories(self.categories)
        entry.delete(0, "end")
        self._refresh_settings()

    def _del_cat(self, tp, cat):
        if len(self.categories[tp]) <= 1:
            messagebox.showwarning("提示", "至少保留一个分类")
            return
        self.categories[tp].remove(cat)
        save_categories(self.categories)
        self._refresh_settings()


# ==================== 入口 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
