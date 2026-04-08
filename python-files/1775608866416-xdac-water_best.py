import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import json
import os
import pandas as pd
from datetime import datetime

# ========== 配置文件 ==========
DATA_FILE = "water_records.json"
STOCK_FILE = "water_stock.json"
USER_FILE = "water_users.json"

# ========== 主程序 ==========
class WaterBestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("送水登记管理系统【最终完美版】")
        self.root.geometry("1050x850")
        self.current_user = ""

        # 加载数据
        self.records = self.load_json(DATA_FILE)
        self.stock = self.load_json(STOCK_FILE)
        self.users = self.load_json(USER_FILE)

        # 初始化数据
        if not self.stock:
            self.stock = {"大桶": 50, "小桶": 50, "会员": {}}
        if not self.users:
            self.users = {"admin": "123456", "user": "123"}

        # 登录窗口
        self.login_window()

    # ===================== 登录系统 =====================
    def login_window(self):
        login = tk.Toplevel(self.root)
        login.title("用户登录")
        login.geometry("350x200")
        login.resizable(False, False)
        tk.Label(login, text="账号登录", font=("微软雅黑", 16)).pack(pady=10)
        tk.Label(login, text="账号：").pack()
        user_entry = ttk.Entry(login)
        user_entry.pack()
        tk.Label(login, text="密码：").pack()
        pwd_entry = ttk.Entry(login, show="*")
        pwd_entry.pack()

        def check():
            u = user_entry.get().strip()
            p = pwd_entry.get().strip()
            if u in self.users and self.users[u] == p:
                self.current_user = u
                login.destroy()
                self.main_ui()
            else:
                messagebox.showerror("错误", "账号或密码错误")
        ttk.Button(login, text="登录", command=check).pack(pady=10)
        login.transient(self.root)
        login.grab_set()
        self.root.wait_window(login)

    # ===================== 主界面 =====================
    def main_ui(self):
        # 标题
        tk.Label(self.root, text="🏠 送水登记管理系统【最终完美版】", font=("微软雅黑", 22, "bold")).pack(pady=10)

        # 录入区域
        input_frame = ttk.LabelFrame(self.root, text="送水/还桶登记")
        input_frame.pack(fill="x", padx=30, pady=5)

        # 第1行
        ttk.Label(input_frame, text="日期：").grid(row=0, column=0, pad=5, pady=6)
        self.date = ttk.Entry(input_frame, width=12)
        self.date.grid(row=0, column=1)
        self.date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(input_frame, text="会员号：").grid(row=0, column=2, pad=5)
        self.vip = ttk.Entry(input_frame, width=10)
        self.vip.grid(row=0, column=3)

        ttk.Label(input_frame, text="手机号：").grid(row=0, column=4, pad=5)
        self.phone = ttk.Entry(input_frame, width=15)
        self.phone.grid(row=0, column=5)

        ttk.Label(input_frame, text="地址：").grid(row=0, column=6, pad=5)
        self.addr = ttk.Entry(input_frame, width=28)
        self.addr.grid(row=0, column=7)

        # 第2行
        ttk.Label(input_frame, text="规格：").grid(row=1, column=0, pad=5, pady=6)
        self.type_var = tk.StringVar(value="大桶")
        ttk.Combobox(input_frame, textvariable=self.type_var, values=["大桶", "小桶"], width=8).grid(row=1, column=1)

        ttk.Label(input_frame, text="数量：").grid(row=1, column=2, pad=5)
        self.num = ttk.Entry(input_frame, width=10)
        self.num.grid(row=1, column=3)

        ttk.Label(input_frame, text="类型：").grid(row=1, column=4, pad=5)
        self.act_var = tk.StringVar(value="送水")
        ttk.Combobox(input_frame, textvariable=self.act_var, values=["送水", "还桶"], width=8).grid(row=1, column=5)

        ttk.Label(input_frame, text="单价：").grid(row=1, column=6, pad=5)
        self.price = ttk.Entry(input_frame, width=10)
        self.price.grid(row=1, column=7)
        self.price.insert(0, "20")

        # 第3行
        ttk.Label(input_frame, text="已付：").grid(row=2, column=0, pad=5, pady=6)
        self.paid = ttk.Entry(input_frame, width=10)
        self.paid.grid(row=2, column=1)
        self.paid.insert(0, "0")

        ttk.Label(input_frame, text="还款：").grid(row=2, column=2, pad=5)
        self.pay_back = ttk.Entry(input_frame, width=10)
        self.pay_back.grid(row=2, column=3)
        self.pay_back.insert(0, "0")

        # ========== 【新增】送水人 ==========
        ttk.Label(input_frame, text="送水人：").grid(row=2, column=4, pad=5)
        self.sender_var = tk.StringVar(value="")
        sender_cb = ttk.Combobox(input_frame, textvariable=self.sender_var,
                                 values=["送水员1", "送水员2", "送水员3", "其他"], width=10)
        sender_cb.grid(row=2, column=5)

        # ========== 【自动】登记人（当前登录用户） ==========
        ttk.Label(input_frame, text="登记人：").grid(row=2, column=6, pad=5)
        self.regist_var = tk.StringVar(value=self.current_user)
        ttk.Label(input_frame, textvariable=self.regist_var, font=("微软雅黑", 9, "bold")).grid(row=2, column=7)

        # 第4行
        ttk.Label(input_frame, text="备注：").grid(row=3, column=0, pad=5, pady=6)
        self.note = ttk.Entry(input_frame, width=40)
        self.note.grid(row=3, column=1, columnspan=7)

        # 按钮区
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="✅提交", command=self.submit).pack(side="left", pad=5)
        ttk.Button(btn_frame, text="🧹清空", command=self.clear).pack(side="left", pad=5)
        ttk.Button(btn_frame, text="🧾打印小票", command=self.print_ticket).pack(side="left", pad=5)
        ttk.Button(btn_frame, text="📊今日统计", command=self.stat_day).pack(side="left", pad=5)
        ttk.Button(btn_frame, text="📅本月统计", command=self.stat_month).pack(side="left", pad=5)
        ttk.Button(btn_frame, text="📋导出Excel", command=self.export).pack(side="left", pad=5)

        # 搜索
        search_frame = ttk.LabelFrame(self.root, text="查询/操作")
        search_frame.pack(fill="x", padx=30, pady=3)
        ttk.Label(search_frame, text="搜索(会员/电话/地址)：").pack(side="left", pad=5)
        self.search_key = ttk.Entry(search_frame, width=30)
        self.search_key.pack(side="left", pad=5)
        ttk.Button(search_frame, text="搜索", command=self.do_search).pack(side="left", pad=5)
        ttk.Button(search_frame, text="全部", command=self.show_all).pack(side="left", pad=5)
        ttk.Button(search_frame, text="修改", command=self.edit).pack(side="left", pad=5)
        ttk.Button(search_frame, text="删除", command=self.delete).pack(side="left", pad=5)

        # 库存
        self.stock_label = tk.Label(self.root, text=f"📦库存：大桶 {self.stock['大桶']} | 小桶 {self.stock['小桶']}", font=("微软雅黑", 11, "bold"))
        self.stock_label.pack(pady=2)

        # 记录列表
        tk.Label(self.root, text="送水记录列表", font=("微软雅黑", 12)).pack()
        self.list_box = scrolledtext.ScrolledText(self.root, width=130, height=32)
        self.list_box.pack(padx=30, pady=5, fill="both", expand=True)

        self.show_all()

    # ===================== 核心提交 =====================
    def submit(self):
        vip = self.vip.get().strip()
        phone = self.phone.get().strip()
        date = self.date.get()
        addr = self.addr.get()
        wtype = self.type_var.get()
        num = self.num.get().strip()
        act = self.act_var.get()
        price = self.price.get().strip()
        paid = int(self.paid.get().strip() or 0)
        pay_back = int(self.pay_back.get().strip() or 0)
        sender = self.sender_var.get().strip()
        regist = self.regist_var.get()
        note = self.note.get()

        if not num or not price:
            messagebox.showwarning("提示", "数量/单价不能为空")
            return
        if act == "送水" and not sender:
            messagebox.showwarning("提示", "请选择送水人")
            return

        num = int(num)
        price = int(price)
        total = num * price
        debt = total - paid

        # 库存
        if act == "送水":
            if self.stock[wtype] < num:
                messagebox.showerror("错误", "库存不足！")
                return
            self.stock[wtype] -= num
        else:
            self.stock[wtype] += num

        # 会员欠款
        user_debt = 0
        if vip:
            if vip not in self.stock["会员"]:
                self.stock["会员"][vip] = 0
            self.stock["会员"][vip] += debt
            self.stock["会员"][vip] -= pay_back
            user_debt = self.stock["会员"][vip]

        # 记录
        item = {
            "日期": date, "会员号": vip, "手机号": phone, "地址": addr,
            "规格": wtype, "数量": num, "类型": act,
            "单价": price, "总价": total, "已付": paid, "本次欠款": debt, "还款": pay_back,
            "客户总欠款": user_debt,
            "送水人": sender, "登记人": regist,
            "备注": note
        }
        self.records.append(item)
        self.save_json(self.records, DATA_FILE)
        self.save_json(self.stock, STOCK_FILE)

        messagebox.showinfo("成功", f"操作成功！\n送水人：{sender}\n登记人：{regist}\n客户欠款：{user_debt}")
        self.clear()
        self.refresh_stock()
        self.show_all()

    # ===================== 打印小票（含送水人+登记人）=====================
    def print_ticket(self):
        try:
            ticket = f"""
            ====== 送水服务单 ======
            日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}
            会员号：{self.vip.get() or '无'}
            电话：{self.phone.get() or '无'}
            地址：{self.addr.get() or '无'}
            ------------------------
            规格：{self.type_var.get()}
            数量：{self.num.get() or 0}桶
            单价：{self.price.get() or 0}元
            总价：{int(self.num.get() or 0)*int(self.price.get() or 0)}元
            已付：{self.paid.get() or 0}元
            ------------------------
            送水人：{self.sender_var.get() or '无'}
            登记人：{self.current_user}
            ========================
            感谢惠顾！
            """
            messagebox.showinfo("小票打印", "已发送至打印机！\n\n" + ticket)
        except:
            messagebox.showerror("错误", "打印失败")

    # ===================== 基础功能 =====================
    def load_json(self, p):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    def save_json(self, d, p):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    def refresh_stock(self):
        self.stock_label.config(text=f"📦库存：大桶 {self.stock['大桶']} | 小桶 {self.stock['小桶']}")
    def clear(self):
        for w in [self.num, self.paid, self.pay_back, self.note, self.phone, self.addr, self.vip]:
            w.delete(0, tk.END)
        self.paid.insert(0, "0")
        self.pay_back.insert(0, "0")
        self.sender_var.set("")
    def show_all(self):
        self.list_box.delete(1.0, tk.END)
        for i, it in enumerate(self.records, 1):
            line = (f"[{i}] {it['日期']} | 会员:{it['会员号']} | 电话:{it['手机号']} | {it['地址']} | "
                    f"{it['规格']}{it['数量']}桶 | {it['类型']} | 送水人:{it['送水人']} | 登记人:{it['登记人']} | 欠款:{it['客户总欠款']}\n")
            self.list_box.insert(tk.END, line + "-"*200 + "\n")
    def do_search(self):
        k = self.search_key.get().strip()
        if not k: return
        res = [r for r in self.records if k in r['会员号'] or k in r['手机号'] or k in r['地址']]
        self.list_box.delete(1.0, tk.END)
        for r in res:
            self.list_box.insert(tk.END, f"{r}\n---------------------------------------\n")
    def edit(self):
        messagebox.showinfo("提示", "修改：请提交新记录后删除旧记录")
    def delete(self):
        idx = simpledialog.askinteger("删除", "输入序号")
        if idx and 1 <= idx <= len(self.records):
            del self.records[idx-1]
            self.save_json(self.records, DATA_FILE)
            self.show_all()
    def stat_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        d = [r for r in self.records if r['日期'] == today and r['类型'] == '送水']
        c = sum(r['数量'] for r in d)
        m = sum(r['总价'] for r in d)
        messagebox.showinfo("今日统计", f"日期：{today}\n送水：{c}桶\n总额：{m}元")
    def stat_month(self):
        m = datetime.now().strftime("%Y-%m")
        d = [r for r in self.records if r['日期'].startswith(m) and r['类型'] == '送水']
        c = sum(r['数量'] for r in d)
        m = sum(r['总价'] for r in d)
        messagebox.showinfo("本月统计", f"送水：{c}桶\n总额：{m}元")
    def export(self):
        pd.DataFrame(self.records).to_excel("送水记录.xlsx", index=False)
        messagebox.showinfo("成功", "已导出Excel")

if __name__ == "__main__":
    root = tk.Tk()
    app = WaterBestApp(root)
    root.mainloop()