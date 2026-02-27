import json
import os
from datetime import datetime
from tkinter import *
from tkinter import messagebox

# 数据文件
DATA_FILE = "records.json"

# ---------- 数据操作 ----------
def load_records():
    """从JSON文件加载记录，若文件不存在或损坏则返回空列表"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_records(records):
    """保存记录到JSON文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def compute_balance(records):
    """计算当前余额"""
    return sum(item["amount"] for item in records)

# ---------- GUI 应用程序 ----------
class AccountingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个人记账本")
        self.root.geometry("520x480")
        self.root.resizable(False, False)

        # 加载数据
        self.records = load_records()
        self.balance = compute_balance(self.records)

        # 创建界面组件
        self.create_widgets()
        self.refresh_listbox()

    def create_widgets(self):
        # 余额显示
        self.balance_var = StringVar()
        self.balance_var.set(f"当前余额：{self.balance:.2f} 元")
        Label(self.root, textvariable=self.balance_var, font=("微软雅黑", 14, "bold"),
              fg="green").pack(pady=10)

        # 记录列表 + 滚动条
        frame_list = Frame(self.root)
        frame_list.pack(pady=5, padx=10, fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame_list)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox = Listbox(frame_list, yscrollcommand=scrollbar.set,
                               font=("Consolas", 11), height=12)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # 输入区域
        frame_input = Frame(self.root)
        frame_input.pack(pady=10)

        Label(frame_input, text="描述：", font=("微软雅黑", 10)).grid(row=0, column=0, padx=5)
        self.desc_entry = Entry(frame_input, width=20, font=("微软雅黑", 10))
        self.desc_entry.grid(row=0, column=1, padx=5)

        Label(frame_input, text="金额：", font=("微软雅黑", 10)).grid(row=0, column=2, padx=5)
        self.amount_entry = Entry(frame_input, width=12, font=("微软雅黑", 10))
        self.amount_entry.grid(row=0, column=3, padx=5)
        Label(frame_input, text="(收入用正数，支出用负数)", fg="gray", font=("微软雅黑", 8)).grid(row=1, column=0, columnspan=4, pady=2)

        # 按钮区域
        frame_btn = Frame(self.root)
        frame_btn.pack(pady=10)

        Button(frame_btn, text="添加记录", command=self.add_record,
               bg="#4CAF50", fg="white", font=("微软雅黑", 10), width=10).pack(side=LEFT, padx=10)
        Button(frame_btn, text="删除选中", command=self.delete_selected,
               bg="#f44336", fg="white", font=("微软雅黑", 10), width=10).pack(side=LEFT, padx=10)
        Button(frame_btn, text="退出", command=self.root.quit,
               bg="#808080", fg="white", font=("微软雅黑", 10), width=8).pack(side=LEFT, padx=10)

    def refresh_listbox(self):
        """刷新列表显示和余额"""
        self.listbox.delete(0, END)
        for idx, rec in enumerate(self.records):
            line = f"{rec['date']}  {rec['description']}  {rec['amount']:+.2f} 元"
            self.listbox.insert(END, line)
        self.balance = compute_balance(self.records)
        self.balance_var.set(f"当前余额：{self.balance:.2f} 元")

    def add_record(self):
        """添加一条记录"""
        desc = self.desc_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        if not desc:
            messagebox.showwarning("输入错误", "请输入描述")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            messagebox.showwarning("输入错误", "金额必须是数字")
            return

        # 生成记录
        record = {
            "description": desc,
            "amount": amount,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.records.append(record)
        save_records(self.records)

        # 清空输入框
        self.desc_entry.delete(0, END)
        self.amount_entry.delete(0, END)

        # 刷新界面
        self.refresh_listbox()

    def delete_selected(self):
        """删除选中的记录"""
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showinfo("提示", "请先选中要删除的记录")
            return
        index = selected[0]
        rec = self.records[index]
        confirm = messagebox.askyesno("确认删除", f"确定要删除这条记录吗？\n{rec['date']} {rec['description']} {rec['amount']:+.2f}元")
        if confirm:
            del self.records[index]
            save_records(self.records)
            self.refresh_listbox()

if __name__ == "__main__":
    root = Tk()
    app = AccountingApp(root)
    root.mainloop()