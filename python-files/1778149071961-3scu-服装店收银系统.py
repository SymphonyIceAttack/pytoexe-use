import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import shutil
import tkinter.simpledialog as simpledialog

# ===================== 基础配置 =====================
DB_FILE = "clothes_store.db"
BACKUP_DIR = "db_backup"
LOW_STOCK_WARN = 5  # 库存预警值

# 预设下拉选项
COLOR_LIST = ["黑色", "白色", "灰色", "蓝色", "红色", "米色", "咖色"]
all_sizes = ["28", "29", "30", "31", "32", "33", "S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"]

# 记忆变量
last_stock_num = "1"
price_memory = dict()

# ===================== 数据库初始化 =====================
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE products
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      code TEXT,name TEXT,category TEXT,size TEXT,color TEXT,
                      cost REAL,stock INTEGER)''')
        c.execute('''CREATE TABLE sales
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      stime TEXT,sdate TEXT,smonth TEXT,
                      code TEXT,name TEXT,size TEXT,color TEXT,
                      cost REAL,price REAL,qty INTEGER,
                      total REAL,profit REAL)''')
        conn.commit()
        conn.close()
    auto_backup_db()

# 自动备份数据库
def auto_backup_db():
    if not os.path.exists(BACKUP_DIR):
        os.mkdir(BACKUP_DIR)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_name = f"{BACKUP_DIR}/store_bak_{now}.db"
    try:
        shutil.copy(DB_FILE, bak_name)
    except:
        pass

# 手动清理零库存
def clear_zero_stock():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE stock <= 0")
    conn.commit()
    conn.close()
    messagebox.showinfo("完成", "已一键清理零库存商品")
    load_products()

# ===================== 主窗口 =====================
root = tk.Tk()
root.title("服装店进销存 完整版（颜色可选填）")
root.geometry("1600x900")
root.resizable(True, True)

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

tab = ttk.Notebook(main_frame)
tab.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

tab1 = ttk.Frame(tab)
tab2 = ttk.Frame(tab)
tab3 = ttk.Frame(tab)
tab4 = ttk.Frame(tab)
tab5 = ttk.Frame(tab)
tab6 = ttk.Frame(tab)
tab7 = ttk.Frame(tab)

tab.add(tab1, text="库存查询")
tab.add(tab2, text="添加商品")
tab.add(tab3, text="销售开单")
tab.add(tab4, text="销售记录")
tab.add(tab5, text="每日汇总")
tab.add(tab6, text="月度报表")
tab.add(tab7, text="销量排行&批量改进价")

today_date = datetime.now().strftime("%Y-%m-%d")
today_month = datetime.now().strftime("%Y-%m")

# ===================== 1.库存查询页面（增加删除按钮） =====================
def load_products(keyword=""):
    for item in tree.get_children():
        tree.delete(item)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if keyword:
        c.execute("SELECT * FROM products WHERE code LIKE ? OR name LIKE ?", (f"%{keyword}%", f"%{keyword}%"))
    else:
        c.execute("SELECT * FROM products")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        stock = row[7]
        tag = "low" if stock <= LOW_STOCK_WARN else "normal"
        tree.insert("", "end", values=row, tags=(tag,))
    tree.tag_configure("low", foreground="red")
    tree.tag_configure("normal", foreground="black")

def search_pro():
    load_products(search_entry.get())

# 删除选中商品（新增）
def delete_selected_product():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("提示", "请先选择要删除的商品")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for item in selected:
        pid = tree.item(item)["values"][0]
        cur.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    load_products()
    messagebox.showinfo("成功", "已删除选中商品")

search_frame = tk.Frame(tab1)
search_frame.pack(pady=5)
tk.Label(search_frame, text="搜索款号/名称：").pack(side=tk.LEFT)
search_entry = tk.Entry(search_frame, width=20)
search_entry.pack(side=tk.LEFT, padx=5)
tk.Button(search_frame, text="搜索", command=search_pro).pack(side=tk.LEFT)
tk.Button(search_frame, text="刷新", command=lambda: load_products()).pack(side=tk.LEFT)
tk.Button(search_frame, text="删除选中", bg="red", fg="white", command=delete_selected_product).pack(side=tk.LEFT, padx=5)
tk.Button(search_frame, text="一键清理零库存", bg="#ff5722", fg="white", command=clear_zero_stock).pack(side=tk.LEFT, padx=10)

tree = ttk.Treeview(tab1, columns=("id", "code", "name", "cate", "size", "color", "cost", "stock"), show="headings")
tree.heading("id", text="ID")
tree.heading("code", text="款号")
tree.heading("name", text="名称")
tree.heading("cate", text="类别")
tree.heading("size", text="尺码")
tree.heading("color", text="颜色")
tree.heading("cost", text="进价")
tree.heading("stock", text="库存")
tree.column("id", width=40)
tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ===================== 2.添加商品页面（类别手动输入） =====================
tk.Label(tab2, text="款号").place(x=30, y=20)
code_entry = tk.Entry(tab2)
code_entry.place(x=100, y=20, width=180)

tk.Label(tab2, text="商品名称").place(x=320, y=20)
name_entry = tk.Entry(tab2)
name_entry.place(x=400, y=20, width=220)

tk.Label(tab2, text="类别").place(x=660, y=20)
cate_entry = tk.Entry(tab2)
cate_entry.place(x=720, y=20, width=150)

tk.Label(tab2, text="颜色").place(x=30, y=60)
color_combo = ttk.Combobox(tab2, values=COLOR_LIST, state="readonly")
color_combo.place(x=100, y=60, width=180)

tk.Label(tab2, text="进价(成本)").place(x=320, y=60)
cost_entry = tk.Entry(tab2)
cost_entry.place(x=400, y=60, width=150)

tk.Label(tab2, text="选择尺码").place(x=30, y=110)
size_combo = ttk.Combobox(tab2, values=all_sizes, state="readonly")
size_combo.place(x=100, y=110, width=120)
size_combo.current(0)

tk.Label(tab2, text="批量区间：").place(x=30, y=145)
batch_start_combo = ttk.Combobox(tab2, values=all_sizes, state="readonly", width=10)
batch_start_combo.place(x=100, y=145)
batch_start_combo.current(0)
tk.Label(tab2, text="→").place(x=210, y=145)
batch_end_combo = ttk.Combobox(tab2, values=all_sizes, state="readonly", width=10)
batch_end_combo.place(x=240, y=145)
batch_end_combo.current(len(all_sizes)-1)

tk.Label(tab2, text="库存数量").place(x=260, y=110)
stock_entry = tk.Entry(tab2)
stock_entry.place(x=340, y=110, width=150)
stock_entry.insert(0, last_stock_num)

def clear_all_input():
    code_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    cate_entry.delete(0, tk.END)
    color_combo.set("")
    cost_entry.delete(0, tk.END)
    stock_entry.delete(0, tk.END)
    stock_entry.insert(0, "1")

tk.Button(tab2, text="一键清空录入", command=clear_all_input, bg="#999").place(x=720, y=60, width=120)

tk.Button(tab2, text="添加该尺码", command=lambda: add_size()).place(x=520, y=105, width=120)
tk.Button(tab2, text="批量添加区间", bg="#42A5F5", fg="white", command=lambda: add_batch_sizes()).place(x=520, y=140, width=120)
tk.Button(tab2, text="清空尺码列表", command=lambda: clear_size_table()).place(x=660, y=110, width=100)

current_product_table = ttk.Treeview(tab2, columns=("code", "name", "color", "cost", "size", "stock"), show="headings")
current_product_table.heading("code", text="款号")
current_product_table.heading("name", text="商品名称")
current_product_table.heading("color", text="颜色")
current_product_table.heading("cost", text="成本")
current_product_table.heading("size", text="尺码")
current_product_table.heading("stock", text="库存")
current_product_table.column("code", width=100, anchor=tk.CENTER)
current_product_table.column("name", width=120, anchor=tk.CENTER)
current_product_table.column("color", width=80, anchor=tk.CENTER)
current_product_table.column("cost", width=80, anchor=tk.CENTER)
current_product_table.column("size", width=80, anchor=tk.CENTER)
current_product_table.column("stock", width=80, anchor=tk.CENTER)
current_product_table.place(x=40, y=170, width=480, height=350)

product_list = ttk.Treeview(tab2, columns=("code", "name", "color", "cost", "size", "stock"), show="headings")
product_list.heading("code", text="款号")
product_list.heading("name", text="商品名称")
product_list.heading("color", text="颜色")
product_list.heading("cost", text="成本")
product_list.heading("size", text="尺码")
product_list.heading("stock", text="库存")
product_list.column("code", width=100, anchor=tk.CENTER)
product_list.column("name", width=120, anchor=tk.CENTER)
product_list.column("color", width=80, anchor=tk.CENTER)
product_list.column("cost", width=80, anchor=tk.CENTER)
product_list.column("size", width=80, anchor=tk.CENTER)
product_list.column("stock", width=80, anchor=tk.CENTER)
product_list.place(x=560, y=170, width=950, height=350)

def delete_selected_left():
    sel = current_product_table.selection()
    for i in sel:
        current_product_table.delete(i)

def delete_selected_right():
    sel = product_list.selection()
    for i in sel:
        product_list.delete(i)

tk.Button(tab2, text="删除选中(左)", command=delete_selected_left).place(x=40, y=530)
tk.Button(tab2, text="删除选中(右)", command=delete_selected_right).place(x=560, y=530)

def is_exist_in_current(code, color, size):
    for item in current_product_table.get_children():
        vals = current_product_table.item(item)["values"]
        if vals[0] == code and vals[2] == color and vals[4] == size:
            return True
    return False

def add_size():
    s = size_combo.get()
    q = stock_entry.get().strip()
    if not q.isdigit():
        messagebox.showwarning("提示", "库存必须为数字")
        return
    code = code_entry.get().strip()
    name = name_entry.get().strip()
    color = color_combo.get().strip()
    cost = cost_entry.get().strip()
    if not (code and cost):
        messagebox.showwarning("提示", "请填款号、成本")
        return
    if is_exist_in_current(code, color, s):
        messagebox.showwarning("提示", "该款号+颜色+尺码已存在，无需重复添加")
        return
    current_product_table.insert("", "end", values=(code, name, color, cost, s, q))
    last_stock_num = q

def add_batch_sizes():
    q = stock_entry.get().strip()
    if not q.isdigit():
        messagebox.showwarning("提示", "库存必须为数字")
        return
    code = code_entry.get().strip()
    name = name_entry.get().strip()
    color = color_combo.get().strip()
    cost = cost_entry.get().strip()
    if not (code and cost):
        messagebox.showwarning("提示", "请填款号、成本")
        return

    start_sz = batch_start_combo.get()
    end_sz = batch_end_combo.get()
    try:
        start_idx = all_sizes.index(start_sz)
        end_idx = all_sizes.index(end_sz)
    except:
        messagebox.showerror("错误", "尺码异常")
        return

    if start_idx <= end_idx:
        target_sizes = all_sizes[start_idx:end_idx+1]
    else:
        target_sizes = all_sizes[end_idx:start_idx+1][::-1]

    cnt = 0
    for sz in target_sizes:
        if is_exist_in_current(code, color, sz):
            continue
        current_product_table.insert("", "end", values=(code, name, color, cost, sz, q))
        cnt += 1
    messagebox.showinfo("完成", f"共添加 {cnt} 个新尺码，跳过重复")
    last_stock_num = q

def clear_size_table():
    for i in current_product_table.get_children():
        current_product_table.delete(i)

def add_product_to_list():
    items = current_product_table.get_children()
    if not items:
        messagebox.showwarning("提示", "请先添加尺码库存")
        return
    for i in items:
        val = current_product_table.item(i)["values"]
        product_list.insert("", "end", values=val)
    clear_size_table()
    messagebox.showinfo("成功", "已加入待保存")

def clear_all_product_list():
    product_list.delete(*product_list.get_children())
    clear_size_table()

def save_all_products():
    items = product_list.get_children()
    if not items:
        messagebox.showwarning("提示", "无商品保存")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cate = cate_entry.get().strip()
    for i in items:
        code, name, color, cost, size, stock = product_list.item(i)["values"]
        cur.execute("SELECT id FROM products WHERE code=? AND color=? AND size=?", (code, color, size))
        if cur.fetchone():
            continue
        cur.execute('''INSERT INTO products
        (code,name,category,size,color,cost,stock)
        VALUES (?,?,?,?,?,?,?)''',
                    (code, name, cate, size, color, float(cost), int(stock)))
    conn.commit()
    conn.close()
    messagebox.showinfo("完成", f"入库完成")
    clear_all_product_list()
    load_products()

tk.Button(tab2, text="加入待保存", bg="#FF9800", fg="white", command=add_product_to_list).place(x=40, y=580)
tk.Button(tab2, text="清空全部", command=clear_all_product_list).place(x=180, y=580)
tk.Button(tab2, text="一键保存入库", bg="#2196F3", fg="white", command=save_all_products).place(x=320, y=580)

# ===================== 3.销售开单页面（颜色可选填） =====================
# 输入区域
tk.Label(tab3, text="款号").place(x=20, y=22)
sale_code = tk.Entry(tab3, width=12)
sale_code.place(x=70, y=22)

tk.Label(tab3, text="颜色").place(x=160, y=22)
sale_color_combo = ttk.Combobox(tab3, values=[], state="readonly", width=10)
sale_color_combo.place(x=210, y=22)

tk.Label(tab3, text="尺码").place(x=320, y=22)
sale_size_combo = ttk.Combobox(tab3, values=[], state="readonly", width=10)
sale_size_combo.place(x=370, y=22)

tk.Label(tab3, text="数量").place(x=480, y=22)
sale_qty = tk.Entry(tab3, width=8)
sale_qty.place(x=530, y=22)

# 最后统一填总价
tk.Label(tab3, text="本次销售总价").place(x=610, y=22)
total_price_entry = tk.Entry(tab3, width=12)
total_price_entry.place(x=700, y=22)

# 购物车
cart = ttk.Treeview(tab3, columns=("code", "name", "color", "size", "cost", "price", "qty", "total", "profit"), show="headings")
cart.heading("code", text="款号")
cart.heading("name", text="名称")
cart.heading("color", text="颜色")
cart.heading("size", text="尺码")
cart.heading("cost", text="进价")
cart.heading("price", text="售价")
cart.heading("qty", text="数量")
cart.heading("total", text="小计")
cart.heading("profit", text="利润")
cart.place(x=20, y=65, width=1520, height=340)

lab_sale = tk.Label(tab3, text="合计金额：0.00 元", font=("黑体", 11))
lab_sale.place(x=20, y=420)
lab_profit = tk.Label(tab3, text="合计利润：0.00 元", font=("黑体", 11), fg="red")
lab_profit.place(x=160, y=420)

_search_job = None

def get_color_by_code():
    global _search_job
    if _search_job is not None:
        root.after_cancel(_search_job)
    code = sale_code.get().strip()
    if len(code) < 3:
        sale_color_combo.set("")
        sale_color_combo["values"] = []
        sale_size_combo.set("")
        sale_size_combo["values"] = []
        return
    _search_job = root.after(500, lambda: _do_query_color(code))

def _do_query_color(code):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT color FROM products WHERE code=?", (code,))
    res = [r[0] for r in cur.fetchall()]
    conn.close()
    sale_color_combo["values"] = res
    if res:
        sale_color_combo.current(0)
    else:
        sale_color_combo.set("")
    get_size_by_color()

def get_size_by_color():
    code = sale_code.get().strip()
    color = sale_color_combo.get().strip()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if color == "":
        cur.execute("SELECT DISTINCT size FROM products WHERE code=?", (code,))
    else:
        cur.execute("SELECT DISTINCT size FROM products WHERE code=? AND color=?", (code, color))
    res = [r[0] for r in cur.fetchall()]
    conn.close()
    sale_size_combo["values"] = res
    if res:
        sale_size_combo.current(0)

# 加入购物车（颜色可选填）
def add_to_cart_no_price():
    code = sale_code.get().strip()
    color = sale_color_combo.get().strip()
    size = sale_size_combo.get().strip()
    qty_txt = sale_qty.get().strip()

    # 只校验款号、尺码、数量，颜色不再必填
    if not (code and size and qty_txt):
        messagebox.showwarning("提示", "请填写款号、尺码、数量")
        return
    if not qty_txt.isdigit():
        messagebox.showwarning("提示", "数量必须是数字")
        return
    qty = int(qty_txt)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if color == "":
        cur.execute("SELECT name,cost,stock FROM products WHERE code=? AND size=?", (code, size))
    else:
        cur.execute("SELECT name,cost,stock FROM products WHERE code=? AND color=? AND size=?", (code, color, size))
    res = cur.fetchone()
    conn.close()
    if not res:
        messagebox.showwarning("提示", "未找到商品，请检查款号、颜色、尺码是否正确")
        return
    name, cost, stock = res
    if qty > stock:
        messagebox.showerror("错误", "库存不足")
        return

    cart.insert("", "end", values=(code, name, color, size, cost, 0, qty, 0, 0))
    count_total()

# 自动计算总价并拆分单价
def apply_total_price():
    items = cart.get_children()
    if not items:
        messagebox.showwarning("提示", "购物车为空")
        return

    total_input = total_price_entry.get().strip()
    if not total_input:
        messagebox.showwarning("提示", "请输入本次销售总价")
        return
    try:
        total_all = float(total_input)
    except:
        messagebox.showerror("错误", "总价必须是数字")
        return

    total_qty = 0
    for item in items:
        qty = int(cart.item(item)["values"][6])
        total_qty += qty
    if total_qty == 0:
        return

    unit_price = total_all / total_qty
    for item in items:
        val = list(cart.item(item)["values"])
        qty = int(val[6])
        cost = float(val[4])
        val[5] = round(unit_price, 2)
        val[7] = round(unit_price * qty, 2)
        val[8] = round((unit_price - cost) * qty, 2)
        cart.item(item, values=val)
    count_total()
    messagebox.showinfo("完成", "已自动分配单价")

def count_total():
    sum_t = 0.0
    sum_p = 0.0
    for i in cart.get_children():
        v = cart.item(i)["values"]
        sum_t += float(v[7])
        sum_p += float(v[8])
    lab_sale.config(text=f"合计金额：{sum_t:.2f} 元")
    lab_profit.config(text=f"合计利润：{sum_p:.2f} 元")

def clear_cart():
    cart.delete(*cart.get_children())
    total_price_entry.delete(0, tk.END)
    count_total()

def check_out():
    items = cart.get_children()
    if not items:
        messagebox.showwarning("提示", "购物车为空")
        return
    now = datetime.now()
    stime = now.strftime("%Y-%m-%d %H:%M:%S")
    sdate = now.strftime("%Y-%m-%d")
    smonth = now.strftime("%Y-%m")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for i in items:
        v = cart.item(i)["values"]
        code, name, color, size, cost, price, qty, total, profit = v
        qty = int(qty)
        if color == "":
            cur.execute("UPDATE products SET stock=stock-? WHERE code=? AND size=?", (qty, code, size))
        else:
            cur.execute("UPDATE products SET stock=stock-? WHERE code=? AND color=? AND size=?", (qty, code, color, size))
        cur.execute('INSERT INTO sales (stime,sdate,smonth,code,name,size,color,cost,price,qty,total,profit) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    (stime, sdate, smonth, code, name, size, color, cost, price, qty, total, profit))
    conn.commit()
    conn.close()
    messagebox.showinfo("成功", "结账完成")
    clear_cart()
    load_products()

# 按钮
tk.Button(tab3, text="加入购物车", bg="#4CAF50", fg="white", command=add_to_cart_no_price).place(x=820, y=20)
tk.Button(tab3, text="填入总价", bg="#FF9800", fg="white", command=apply_total_price).place(x=920, y=20)
tk.Button(tab3, text="清空购物车", command=clear_cart).place(x=1010, y=20)
tk.Button(tab3, text="确认结账", bg="#f44336", fg="white", command=check_out).place(x=1100, y=20)

sale_code.bind("<KeyRelease>", lambda e: get_color_by_code())
sale_color_combo.bind("<<ComboboxSelected>>", lambda e: get_size_by_color())

# ===================== 4.销售记录 =====================
def query_day():
    d = day_entry.get().strip()
    sale_tree.delete(*sale_tree.get_children())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM sales WHERE sdate=?", (d,))
    rows = cur.fetchall()
    cur.execute("SELECT SUM(total),SUM(profit) FROM sales WHERE sdate=?", (d,))
    s, p = cur.fetchone()
    conn.close()
    for r in rows:
        sale_tree.insert("", "end", values=r)
    tip.config(text=f"当日总额：{s if s else 0:.2f} 元，利润：{p if p else 0:.2f} 元")

def del_sale():
    sel = sale_tree.selection()
    if not sel:
        messagebox.showwarning("提示", "选择记录")
        return
    for i in sel:
        vals = sale_tree.item(i)["values"]
        sid = vals[0]
        code = vals[4]
        color = vals[8]
        size = vals[7]
        qty = int(vals[10])
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("DELETE FROM sales WHERE id=?", (sid,))
        if color == "":
            cur.execute("UPDATE products SET stock=stock+? WHERE code=? AND size=?", (qty, code, size))
        else:
            cur.execute("UPDATE products SET stock=stock+? WHERE code=? AND color=? AND size=?", (qty, code, color, size))
        conn.commit()
        conn.close()
    query_day()
    load_products()

query_top = tk.Frame(tab4)
query_top.pack(fill=tk.X, padx=5, pady=3)
tk.Label(query_top, text="日期：").pack(side=tk.LEFT)
day_entry = tk.Entry(query_top, width=12)
day_entry.insert(0, today_date)
day_entry.pack(side=tk.LEFT)
tk.Button(query_top, text="查询", command=query_day).pack(side=tk.LEFT, padx=5)

sale_tree = ttk.Treeview(tab4, columns=("id", "stime", "sdate", "smonth", "code", "name", "size", "color", "cost", "price", "qty", "total", "profit"), show="headings")
sale_tree.heading("id", text="ID")
sale_tree.heading("stime", text="销售时间")
sale_tree.heading("sdate", text="日期")
sale_tree.heading("smonth", text="月份")
sale_tree.heading("code", text="款号")
sale_tree.heading("name", text="名称")
sale_tree.heading("size", text="尺码")
sale_tree.heading("color", text="颜色")
sale_tree.heading("cost", text="进价")
sale_tree.heading("price", text="售价")
sale_tree.heading("qty", text="数量")
sale_tree.heading("total", text="小计")
sale_tree.heading("profit", text="利润")

sale_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
tk.Button(tab4, text="删除选中记录(自动退库存)", command=del_sale, bg="#f44336", fg="white").pack()
tip = tk.Label(tab4, text="", fg="red")
tip.pack()

# ===================== 5.每日汇总 =====================
daily_total_label = tk.Label(tab5, text="全部合计：总销售额 0.00 元 | 总利润 0.00 元",
                            font=("黑体", 11), fg="red")

def load_daily_summary():
    daily_tree.delete(*daily_tree.get_children())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT sdate,SUM(total),SUM(profit) FROM sales GROUP BY sdate ORDER BY sdate DESC")
    rows = cur.fetchall()
    cur.execute("SELECT SUM(total),SUM(profit) FROM sales")
    all_sale, all_profit = cur.fetchone()
    conn.close()

    all_sale = all_sale if all_sale else 0.00
    all_profit = all_profit if all_profit else 0.00

    for row in rows:
        daily_tree.insert("", "end", values=row)

    daily_total_label.config(text=f"全部合计：总销售额 {all_sale:.2f} 元 | 总利润 {all_profit:.2f} 元")

def export_daily_excel():
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV表格", "*.csv")])
    if not file:
        return
    with open(file, "w", encoding="utf-8-sig") as f:
        f.write("日期,销售额,利润\n")
        for i in daily_tree.get_children():
            v = daily_tree.item(i)["values"]
            f.write(f"{v[0]},{v[1]},{v[2]}\n")
    messagebox.showinfo("导出成功")

daily_tree = ttk.Treeview(tab5, columns=("date", "sale", "profit"), show="headings")
daily_tree.heading("date", text="日期")
daily_tree.heading("sale", text="当日销售额")
daily_tree.heading("profit", text="当日利润")
daily_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
tk.Button(tab5, text="刷新", command=load_daily_summary).pack()
tk.Button(tab5, text="导出Excel", command=export_daily_excel).pack()
daily_total_label.pack(pady=5)

# ===================== 6.月度报表 =====================
month_total_label = tk.Label(tab6, text="当月合计：销售额 0.00 元 | 利润 0.00 元",
                            font=("黑体", 11), fg="red")

def query_month():
    m = mon_entry.get().strip()
    mon_tree.delete(*mon_tree.get_children())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT sdate,SUM(total),SUM(profit) FROM sales WHERE smonth=? GROUP BY sdate", (m,))
    rows = cur.fetchall()
    cur.execute("SELECT SUM(total),SUM(profit) FROM sales WHERE smonth=?", (m,))
    sum_sale, sum_profit = cur.fetchone()
    conn.close()

    sum_sale = sum_sale if sum_sale else 0.00
    sum_profit = sum_profit if sum_profit else 0.00

    for row in rows:
        mon_tree.insert("", "end", values=row)

    month_total_label.config(text=f"当月合计：销售额 {sum_sale:.2f} 元 | 利润 {sum_profit:.2f} 元")

def export_month_excel():
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV表格", "*.csv")])
    if not file:
        return
    with open(file, "w", encoding="utf-8-sig") as f:
        f.write("日期,销售额,利润\n")
        for i in mon_tree.get_children():
            v = mon_tree.item(i)["values"]
            f.write(f"{v[0]},{v[1]},{v[2]}\n")
    messagebox.showinfo("导出成功")

tk.Label(tab6, text="输入月份 格式：2026-04").pack()
mon_entry = tk.Entry(tab6)
mon_entry.pack()
tk.Button(tab6, text="查询月度", command=query_month).pack(pady=3)
tk.Button(tab6, text="导出Excel", command=export_month_excel).pack()
month_total_label.pack(pady=5)

mon_tree = ttk.Treeview(tab6, columns=("date", "sale", "profit"), show="headings")
mon_tree.heading("date", text="日期")
mon_tree.heading("sale", text="当日销售额")
mon_tree.heading("profit", text="当日利润")
mon_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ===================== 7.销量排行 & 批量改进价 =====================
def load_sale_rank():
    rank_tree.delete(*rank_tree.get_children())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT code,name,SUM(qty) as sell_num,SUM(profit) as all_profit FROM sales GROUP BY code,name ORDER BY sell_num DESC")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        rank_tree.insert("", "end", values=row)

def batch_modify_cost():
    code = simpledialog.askstring("输入", "请输入要批量改进价的款号：")
    if not code:
        return
    new_cost = simpledialog.askfloat("输入", "请输入新进价：")
    if new_cost is None:
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE products SET cost=? WHERE code=?", (new_cost, code))
    conn.commit()
    conn.close()
    messagebox.showinfo("完成", "该款号所有尺码进价已批量修改")
    load_products()

tk.Button(tab7, text="刷新销量排行", command=load_sale_rank).pack()
tk.Button(tab7, text="按款号批量修改进价", command=batch_modify_cost, bg="#ff9800").pack()
rank_tree = ttk.Treeview(tab7, columns=("code", "name", "sell_num", "profit"), show="headings")
rank_tree.heading("code", text="款号")
rank_tree.heading("name", text="名称")
rank_tree.heading("sell_num", text="销量")
rank_tree.heading("profit", text="总利润")
rank_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ===================== 启动 =====================
init_db()
load_products()
load_daily_summary()

root.mainloop()