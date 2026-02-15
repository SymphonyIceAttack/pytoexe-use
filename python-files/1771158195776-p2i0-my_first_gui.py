import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
from datetime import datetime

PRODUCTS_FILE = "products.csv"
SUPPLIES_FILE = "supplies.csv"

def init_files():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['商品名称', '库存数量', '进货单价', '销售单价', '总进货金额',
                           '总销售收入', '总利润', '损耗数量', '损耗金额', '最后更新时间'])

    if not os.path.exists(SUPPLIES_FILE):
        with open(SUPPLIES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['耗材名称', '剩余数量', '单位', '最后更新时间'])
            writer.writerow(['包装', 100, '个', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['贴纸', 500, '张', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['胶带', 50, '卷', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['快递盒', 100, '个', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

def read_products():
    products = []
    with open(PRODUCTS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                products.append({
                    'name': row[0],
                    'stock': int(row[1]),
                    'purchase_price': float(row[2]),
                    'sale_price': float(row[3]),
                    'total_purchase': float(row[4]),
                    'total_sale': float(row[5]),
                    'profit': float(row[6]),
                    'loss_quantity': int(row[7]),
                    'loss_amount': float(row[8]),
                    'update_time': row[9]
                })
    return products

def read_supplies():
    supplies = []
    with open(SUPPLIES_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                supplies.append({
                    'name': row[0],
                    'quantity': int(row[1]),
                    'unit': row[2],
                    'update_time': row[3]
                })
    return supplies

def add_product(name, purchase_price, sale_price, initial_stock=0):
    total_purchase = purchase_price * initial_stock
    total_sale = 0.0
    profit = total_sale - total_purchase
    loss_quantity = 0
    loss_amount = 0.0
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(PRODUCTS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([name, initial_stock, purchase_price, sale_price, total_purchase,
                       total_sale, profit, loss_quantity, loss_amount, update_time])

def update_product(name, stock_change=0, sale_quantity=0, loss_quantity=0):
    products = read_products()
    with open(PRODUCTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['商品名称', '库存数量', '进货单价', '销售单价', '总进货金额',
                       '总销售收入', '总利润', '损耗数量', '损耗金额', '最后更新时间'])
        for product in products:
            if product['name'] == name:
                new_stock = product['stock'] + stock_change - sale_quantity - loss_quantity
                new_total_purchase = product['total_purchase']
                if stock_change > 0:
                    new_total_purchase += product['purchase_price'] * stock_change
                new_total_sale = product['total_sale'] + (product['sale_price'] * sale_quantity)
                new_loss_quantity = product['loss_quantity'] + loss_quantity
                new_loss_amount = new_loss_quantity * product['purchase_price']
                new_profit = new_total_sale - new_total_purchase - new_loss_amount
                update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([
                    name, new_stock, product['purchase_price'], product['sale_price'],
                    new_total_purchase, new_total_sale, new_profit,
                    new_loss_quantity, new_loss_amount, update_time
                ])
            else:
                writer.writerow([
                    product['name'], product['stock'], product['purchase_price'], product['sale_price'],
                    product['total_purchase'], product['total_sale'], product['profit'],
                    product['loss_quantity'], product['loss_amount'], product['update_time']
                ])

def update_supply(name, quantity_change):
    supplies = read_supplies()
    with open(SUPPLIES_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['耗材名称', '剩余数量', '单位', '最后更新时间'])
        for supply in supplies:
            if supply['name'] == name:
                new_quantity = max(0, supply['quantity'] + quantity_change)
                update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([name, new_quantity, supply['unit'], update_time])
            else:
                writer.writerow([supply['name'], supply['quantity'], supply['unit'], supply['update_time']])

class InventorySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("电商进销存管理系统（含快递盒）")
        self.root.geometry("1200x800")
        init_files()

        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tab_control = ttk.Notebook(main_frame)
        self.product_tab = ttk.Frame(tab_control)
        tab_control.add(self.product_tab, text='商品管理')
        self.supply_tab = ttk.Frame(tab_control)
        tab_control.add(self.supply_tab, text='耗材管理')
        self.profit_tab = ttk.Frame(tab_control)
        tab_control.add(self.profit_tab, text='利润分析')
        tab_control.pack(expand=1, fill="both")

        self.init_product_tab()
        self.init_supply_tab()
        self.init_profit_tab()

        self.refresh_product_table()
        self.refresh_supply_table()
        self.refresh_profit_table()

    def init_product_tab(self):
        button_frame = ttk.Frame(self.product_tab)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="添加商品", command=self.add_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="进货", command=self.purchase_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="销售", command=self.sell_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="记录损耗", command=self.record_loss_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新", command=self.refresh_product_table).pack(side=tk.LEFT, padx=5)

        columns = ('name', 'stock', 'purchase_price', 'sale_price', 'total_purchase',
                  'total_sale', 'profit', 'loss_quantity', 'update_time')
        self.product_tree = ttk.Treeview(self.product_tab, columns=columns, show='headings')
        self.product_tree.heading('name', text='商品名称')
        self.product_tree.heading('stock', text='库存数量')
        self.product_tree.heading('purchase_price', text='进货单价')
        self.product_tree.heading('sale_price', text='销售单价')
        self.product_tree.heading('total_purchase', text='总进货金额')
        self.product_tree.heading('total_sale', text='总销售收入')
        self.product_tree.heading('profit', text='总利润')
        self.product_tree.heading('loss_quantity', text='损耗数量')
        self.product_tree.heading('update_time', text='最后更新时间')
        scrollbar = ttk.Scrollbar(self.product_tab, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def init_supply_tab(self):
        button_frame = ttk.Frame(self.supply_tab)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="添加耗材", command=self.add_supply_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="领用耗材", command=self.use_supply_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="补充耗材", command=self.add_supply_quantity_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新", command=self.refresh_supply_table).pack(side=tk.LEFT, padx=5)

        columns = ('name', 'quantity', 'unit', 'update_time')
        self.supply_tree = ttk.Treeview(self.supply_tab, columns=columns, show='headings')
        self.supply_tree.heading('name', text='耗材名称')
        self.supply_tree.heading('quantity', text='剩余数量')
        self.supply_tree.heading('unit', text='单位')
        self.supply_tree.heading('update_time', text='最后更新时间')
        scrollbar = ttk.Scrollbar(self.supply_tab, orient=tk.VERTICAL, command=self.supply_tree.yview)
        self.supply_tree.configure(yscrollcommand=scrollbar.set)
        self.supply_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def init_profit_tab(self):
        columns = ('name', 'total_purchase', 'total_sale', 'profit', 'loss_amount', 'net_profit')
        self.profit_tree = ttk.Treeview(self.profit_tab, columns=columns, show='headings')
        self.profit_tree.heading('name', text='商品名称')
        self.profit_tree.heading('total_purchase', text='总进货金额')
        self.profit_tree.heading('total_sale', text='总销售收入')
        self.profit_tree.heading('profit', text='毛利')
        self.profit_tree.heading('loss_amount', text='损耗金额')
        self.profit_tree.heading('net_profit', text='净利润')
        scrollbar = ttk.Scrollbar(self.profit_tab, orient=tk.VERTICAL, command=self.profit_tree.yview)
        self.profit_tree.configure(yscrollcommand=scrollbar.set)
        self.profit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        total_frame = ttk.Frame(self.profit_tab)
        total_frame.pack(fill=tk.X, pady=10)
        self.total_label = ttk.Label(total_frame, text="")
        self.total_label.pack()

    def refresh_product_table(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        products = read_products()
        for p in products:
            self.product_tree.insert('', tk.END, values=(
                p['name'], p['stock'], f"{p['purchase_price']:.2f}", f"{p['sale_price']:.2f}",
                f"{p['total_purchase']:.2f}", f"{p['total_sale']:.2f}", f"{p['profit']:.2f}",
                p['loss_quantity'], p['update_time']
            ))

    def refresh_supply_table(self):
        for item in self.supply_tree.get_children():
            self.supply_tree.delete(item)
        supplies = read_supplies()
        for s in supplies:
            self.supply_tree.insert('', tk.END, values=(s['name'], s['quantity'], s['unit'], s['update_time']))

    def refresh_profit_table(self):
        for item in self.profit_tree.get_children():
            self.profit_tree.delete(item)
        products = read_products()
        tp = ts = tf = tl = tn = 0.0
        for p in products:
            net = p['profit'] - p['loss_amount']
            self.profit_tree.insert('', tk.END, values=(
                p['name'], f"{p['total_purchase']:.2f}", f"{p['total_sale']:.2f}",
                f"{p['profit']:.2f}", f"{p['loss_amount']:.2f}", f"{net:.2f}"
            ))
            tp += p['total_purchase']
            ts += p['total_sale']
            tf += p['profit']
            tl += p['loss_amount']
            tn += net
        self.total_label.config(text=(
            f"总计：进货{tp:.2f}元 | 销售{ts:.2f}元 | 毛利{tf:.2f}元 | 损耗{tl:.2f}元 | 净利{tn:.2f}元"
        ))

    def add_product_dialog(self):
        name = simpledialog.askstring("添加商品", "商品名称：")
        if not name: return
        for p in read_products():
            if p['name'] == name:
                messagebox.showwarning("提示", "已存在")
                return
        try:
            pp = float(simpledialog.askstring("进货单价", "进货单价："))
            sp = float(simpledialog.askstring("销售单价", "销售单价："))
            st = int(simpledialog.askstring("初始库存", "初始库存：", initialvalue="0"))
            add_product(name, pp, sp, st)
            self.refresh_product_table()
            self.refresh_profit_table()
        except:
            messagebox.showerror("错误", "输入格式有误")

    def purchase_product_dialog(self):
        name = simpledialog.askstring("进货", "商品名称：")
        if not name: return
        if not any(p['name'] == name for p in read_products()):
            messagebox.showwarning("错误", "不存在")
            return
        try:
            q = int(simpledialog.askstring("数量", "进货数量："))
            update_product(name, stock_change=q)
            self.refresh_product_table()
            self.refresh_profit_table()
        except:
            messagebox.showerror("错误", "输入错误")

    def sell_product_dialog(self):
        name = simpledialog.askstring("销售", "商品名称：")
        if not name: return
        pinfo = None
        for p in read_products():
            if p['name'] == name:
                pinfo = p
                break
        if not pinfo:
            messagebox.showwarning("错误", "不存在")
            return
        try:
            q = int(simpledialog.askstring("销售数量", f"库存：{pinfo['stock']}，销售数量："))
            update_product(name, sale_quantity=q)
            update_supply("包装", -q)
            update_supply("贴纸", -q)
            update_supply("胶带", -q//10)
            update_supply("快递盒", -q)
            self.refresh_product_table()
            self.refresh_supply_table()
            self.refresh_profit_table()
        except:
            messagebox.showerror("错误", "输入错误")

    def record_loss_dialog(self):
        name = simpledialog.askstring("损耗", "商品名称：")
        if not name: return
        pinfo = None
        for p in read_products():
            if p['name'] == name:
                pinfo = p
                break
        if not pinfo:
            messagebox.showwarning("错误", "不存在")
            return
        try:
            q = int(simpledialog.askstring("损耗数量", f"库存：{pinfo['stock']}，损耗数量："))
            update_product(name, loss_quantity=q)
            self.refresh_product_table()
            self.refresh_profit_table()
        except:
            messagebox.showerror("错误", "输入错误")

    def add_supply_dialog(self):
        name = simpledialog.askstring("耗材名", "耗材名称：")
        if not name: return
        for s in read_supplies():
            if s['name'] == name:
                messagebox.showwarning("提示", "已存在")
                return
        try:
            q = int(simpledialog.askstring("数量", "初始数量："))
            u = simpledialog.askstring("单位", "单位：", initialvalue="个")
            with open(SUPPLIES_FILE, 'a', encoding='utf-8', newline='') as f:
                csv.writer(f).writerow([name, q, u, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            self.refresh_supply_table()
        except:
            messagebox.showerror("错误", "输入错误")

    def use_supply_dialog(self):
        name = simpledialog.askstring("领用", "耗材名称：")
        if not name: return
        sinfo = None
        for s in read_supplies():
            if s['name'] == name:
                sinfo = s
                break
        if not sinfo:
            messagebox.showwarning("错误", "不存在")
            return
        try:
            q = int(simpledialog.askstring("领用数量", f"剩余：{sinfo['quantity']}，领用："))
            update_supply(name, -q)
            self.refresh_supply_table()
        except:
            messagebox.showerror("错误", "输入错误")

    def add_supply_quantity_dialog(self):
        name = simpledialog.askstring("补充", "耗材名称：")
        if not name: return
        if not any(s['name'] == name for s in read_supplies()):
            messagebox.showwarning("错误", "不存在")
            return
        try:
            q = int(simpledialog.askstring("补充数量", "补充数量："))
            update_supply(name, q)
            self.refresh_supply_table()
        except:
            messagebox.showerror("错误", "输入错误")

if __name__ == "__main__":
    root = tk.Tk()
    app = InventorySystem(root)
    root.mainloop()