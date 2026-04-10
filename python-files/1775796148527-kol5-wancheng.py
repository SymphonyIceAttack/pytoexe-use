import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import re  # 用于中文名验证

DATA_FILE = "class_data.json"

class ClassManager:
    def __init__(self, root):
        self.root = root
        self.root.title("班级积分管理系统")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.students = []
        self.score_items = ["纪律", "卫生", "作业"]
        self.load_data()
        frame_top = tk.Frame(root)
        frame_top.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(frame_top, text="序号").grid(row=0, column=0, padx=5)
        self.entry_id = tk.Entry(frame_top, width=8)
        self.entry_id.grid(row=0, column=1, padx=5)

        tk.Label(frame_top, text="姓名").grid(row=0, column=2, padx=5)
        self.entry_name = tk.Entry(frame_top, width=12)
        self.entry_name.grid(row=0, column=3, padx=5)

        tk.Button(frame_top, text="添加学生", command=self.add_student, bg="#4CAF50", fg="white")\
            .grid(row=0, column=4, padx=5)
        tk.Button(frame_top, text="删除学生", command=self.del_student, bg="#f44336", fg="white")\
            .grid(row=0, column=5, padx=5)
        frame_score = tk.Frame(root)
        frame_score.pack(pady=5, padx=20, fill=tk.X)

        tk.Label(frame_score, text="当前项目：").pack(side=tk.LEFT, padx=5)
        self.var_item = tk.StringVar(value=self.score_items[0])
        self.cb_item = ttk.Combobox(frame_score, textvariable=self.var_item, values=self.score_items, width=10, state="readonly")
        self.cb_item.pack(side=tk.LEFT, padx=5)

        tk.Button(frame_score, text="添加项目", command=self.add_score_item).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_score, text="加分", command=lambda: self.change_score(1), bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(frame_score, text="减分", command=lambda: self.change_score(-1), bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(frame_score, text="自定义分值", command=self.set_custom_score).pack(side=tk.LEFT, padx=5)
        frame_rank = tk.Frame(root)
        frame_rank.pack(pady=5, padx=20, fill=tk.X)
        tk.Button(frame_rank, text="按当前项目排序查看最高分", command=self.show_rank, bg="#9C27B0", fg="white").pack(side=tk.LEFT)
        frame_table = tk.Frame(root)
        frame_table.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        self.columns = ["序号", "姓名"] + self.score_items
        self.tree = ttk.Treeview(frame_table, columns=self.columns, show="headings")

        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        scb = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scb.set)
        scb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_person_total)

        self.refresh_table()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    def get_total_score(self, stu):
        return sum(stu["scores"].get(it, 0) for it in self.score_items)
    def show_person_total(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        stu = self.students[idx]
        total = self.get_total_score(stu)
        messagebox.showinfo("个人总分", f"学生：{stu['name']}\n总分：{total} 分")
    def is_chinese_name(self, name):
        return re.fullmatch(r"^[\u4e00-\u9fa5]{2,6}$", name.strip()) is not None
    def load_data(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.students = data.get("students", [])
                self.score_items = data.get("score_items", ["纪律", "卫生", "作业"])
        except:
            self.students = []
            self.score_items = ["纪律", "卫生", "作业"]

    def save_data(self):
        data = {
            "students": self.students,
            "score_items": self.score_items
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.columns = ["序号", "姓名"] + self.score_items
        self.tree.config(columns=self.columns)
        
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        for stu in self.students:
            row = [stu["id"], stu["name"]] + [stu["scores"].get(it, 0) for it in self.score_items]
            self.tree.insert("", tk.END, values=row)
    def add_student(self):
        sid = self.entry_id.get().strip()
        name = self.entry_name.get().strip()
        
        if not sid or not name:
            messagebox.showwarning("提示", "序号、姓名不能为空")
            return
        if not self.is_chinese_name(name):
            messagebox.showerror("错误", "姓名只能输入 2-6 个中文！")
            return
        
        for s in self.students:
            if s["id"] == sid:
                messagebox.showerror("错误", "序号已存在")
                return
            if s["name"] == name:
                messagebox.showerror("错误", "姓名已存在")
                return

        scores = {it: 0 for it in self.score_items}
        self.students.append({"id": sid, "name": name, "scores": scores})
        
        self.entry_id.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        self.refresh_table()
        messagebox.showinfo("成功", f"学生 {name} 添加完成！")
    def del_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请选择要删除的学生")
            return
        if not messagebox.askyesno("确认", "确定要删除该学生吗？"):
            return
            
        idx = self.tree.index(sel[0])
        del self.students[idx]
        self.refresh_table()
    def add_score_item(self):
        new_item = simpledialog.askstring("新增积分项目", "请输入积分项目名称：")
        if not new_item:
            return
        
        new_item = new_item.strip()
        if new_item in self.score_items:
            messagebox.showwarning("提示", "该项目已存在")
            return
        
        self.score_items.append(new_item)
        for s in self.students:
            s["scores"][new_item] = 0
        
        self.cb_item.config(values=self.score_items)
        self.refresh_table()
        messagebox.showinfo("成功", f"项目 {new_item} 添加成功！")
    def change_score(self, num):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一名学生")
            return
        
        item = self.var_item.get()
        idx = self.tree.index(sel[0])
        self.students[idx]["scores"][item] += num
        self.refresh_table()
    def set_custom_score(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择学生")
            return
        
        val = simpledialog.askinteger("设置分值", "请输入积分值：", minvalue=-999, maxvalue=999)
        if val is None:
            return
        
        item = self.var_item.get()
        idx = self.tree.index(sel[0])
        self.students[idx]["scores"][item] = val
        self.refresh_table()
    def show_rank(self):
        if not self.students:
            messagebox.showinfo("提示", "暂无学生数据")
            return
            
        item = self.var_item.get()
        lst = sorted(self.students, key=lambda x: x["scores"].get(item, 0), reverse=True)
        
        msg = f"📊 【{item}】项目排名\n\n"
        for i, s in enumerate(lst, 1):
            msg += f"{i:2d}. {s['name']:>4} —— {s['scores'].get(item, 0)} 分\n"
        
        messagebox.showinfo("积分排名", msg)
    def on_close(self):
        if messagebox.askyesno("退出确认", "是否保存当前数据？\n（下次打开自动恢复）"):
            self.save_data()
            messagebox.showinfo("保存成功", "数据已保存！")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClassManager(root)
    root.mainloop()