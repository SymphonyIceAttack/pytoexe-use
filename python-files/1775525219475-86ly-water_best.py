import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import json
import os
from datetime import datetime

DATA_FILE = "water_records.json"
STOCK_FILE = "water_stock.json"

class WaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("送水登记系统")
        self.root.geometry("900x700")

        self.records = self.load_json(DATA_FILE)
        self.stock = self.load_json(STOCK_FILE) or {"大桶":50, "小桶":50, "会员":{}}

        # 录入区域
        input_frame = ttk.LabelFrame(root, text="送水登记")
        input_frame.pack(fill="x", padx=20, pady=10)

        # 基础信息
        ttk.Label(input_frame, text="日期：").grid(row=0,column=0,padx=5)
        self.date = ttk.Entry(input_frame, width=12)
        self.date.grid(row=0,column=1)
        self.date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(input_frame, text="会员号：").grid(row=0,column=2,padx=5)
        self.vip = ttk.Entry(input_frame, width=10)
        self.vip.grid(row=0,column=3)

        ttk.Label(input_frame, text="手机号：").grid(row=0,column=4,padx=5)
        self.phone = ttk.Entry(input_frame, width=15)
        self.phone.grid(row=0,column=5)

        ttk.Label(input_frame, text="地址：").grid(row=0,column=6,padx=5)
        self.addr = ttk.Entry(input_frame, width=20)
        self.addr.grid(row=0,column=7)

        # 送水信息
        ttk.Label(input_frame, text="规格：").grid(row=1,column=0,padx=5)
        self.type_var = tk.StringVar(value="大桶")
        ttk.Combobox(input_frame, textvariable=self.type_var, values=["大桶","小桶"], width=8).grid(row=1,column=1)

        ttk.Label(input_frame, text="数量：").grid(row=1,column=2,padx=5)
        self.num = ttk.Entry(input_frame, width=10)
        self.num.grid(row=1,column=3)

        ttk.Label(input_frame, text="送水人：").grid(row=1,column=4,padx=5)
        self.sender = ttk.Entry(input_frame, width=10)
        self.sender.grid(row=1,column=5)

        # 金额/欠款
        ttk.Label(input_frame, text="单价：").grid(row=2,column=0,padx=5)
        self.price = ttk.Entry(input_frame, width=10)
        self.price.grid(row=2,column=1)
        self.price.insert(0, "20")

        ttk.Label(input_frame, text="已付：").grid(row=2,column=2,padx=5)
        self.paid = ttk.Entry(input_frame, width=10)
        self.paid.grid(row=2,column=3)
        self.paid.insert(0, "0")

        # 按钮
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="提交", command=self.submit).grid(row=0,column=0,padx=5)
        ttk.Button(btn_frame, text="显示全部", command=self.show_all).grid(row=0,column=1,padx=5)
        ttk.Button(btn_frame, text="今日统计", command=self.stat_day).grid(row=0,column=2,padx=5)

        # 记录显示
        self.list_box = scrolledtext.ScrolledText(root, width=100, height=25)
        self.list_box.pack(padx=20, pady=10)

        self.show_all()

    def load_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_json(self, data, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def submit(self):
        # 核心提交逻辑
        vip = self.vip.get().strip()
        phone = self.phone.get().strip()
        date = self.date.get()
        addr = self.addr.get().strip()
        wtype = self.type_var.get()
        num = self.num.get().strip()
        sender = self.sender.get().strip()
        price = int(self.price.get() or 20)
        paid = int(self.paid.get() or 0)

        if not addr or not num:
            messagebox.showwarning("提示", "地址和数量不能为空！")
            return

        num = int(num)
        total = num * price
        debt = total - paid

        # 库存计算
        if self.stock[wtype] < num:
            messagebox.showerror("错误", "库存不足！")
            return
        self.stock[wtype] -= num

        # 会员欠款
        user_debt = 0
        if vip:
            self.stock["会员"][vip] = self.stock["会员"].get(vip, 0) + debt
            user_debt = self.stock["会员"][vip]

        # 保存记录
        self.records.append({
            "日期":date, "会员号":vip, "手机号":phone, "地址":addr,
            "规格":wtype, "数量":num, "送水人":sender,
            "总价":total, "已付":paid, "欠款":user_debt
        })
        self.save_json(self.records, DATA_FILE)
        self.save_json(self.stock, STOCK_FILE)

        messagebox.showinfo("成功", "登记完成！")
        self.show_all()

    def show_all(self):
        self.list_box.delete(1.0, tk.END)
        for i, r in enumerate(self.records, 1):
            self.list_box.insert(tk.END, f"[{i}] {r['日期']} | 会员:{r['会员号']} | 电话:{r['手机号']} | 地址:{r['地址']} | {r['规格']}{r['数量']}桶 | 送水人:{r['送水人']} | 欠款:{r['欠款']}\n{'-'*100}\n")

    def stat_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        day_rec = [r for r in self.records if r["日期"] == today]
        cnt = sum(r["数量"] for r in day_rec)
        money = sum(r["总价"] for r in day_rec)
        messagebox.showinfo("今日统计", f"今日送水：{cnt}桶\n今日总额：{money}元")

if __name__ == "__main__":
    root = tk.Tk()
    app = WaterApp(root)
    root.mainloop()