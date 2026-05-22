import random
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

class RollCallSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("班级随机点名系统")
        self.root.geometry("600x450")
        
        self.students = []
        # 界面组件
        tk.Label(root, text="班级随机点名", font=("黑体", 20)).pack(pady=10)
        
        # 名单显示框
        self.list_text = tk.Text(root, width=70, height=10)
        self.list_text.pack(pady=5)
        
        # 操作按钮区
        frame1 = tk.Frame(root)
        frame1.pack(pady=8)
        tk.Button(frame1, text="导入Excel名单", command=self.load_excel, width=12).grid(row=0,column=0,padx=5)
        tk.Button(frame1, text="添加学生", command=self.add_stu, width=10).grid(row=0,column=1,padx=5)
        tk.Button(frame1, text="清空名单", command=self.clear_list, width=10).grid(row=0,column=2,padx=5)
        
        # 点名人数输入
        frame2 = tk.Frame(root)
        frame2.pack(pady=8)
        tk.Label(frame2, text="点名人数：").grid(row=0,column=0)
        self.num_entry = tk.Entry(frame2, width=8)
        self.num_entry.grid(row=0,column=1,padx=5)
        tk.Button(frame2, text="开始点名", command=self.roll_call, bg="#4299e1", fg="white").grid(row=0,column=2,padx=8)
        
        # 结果展示
        tk.Label(root, text="点名结果", font=("黑体",14)).pack(pady=5)
        self.result_label = tk.Label(root, text="暂无结果", font=("黑体",16), fg="#e53e3e")
        self.result_label.pack()

    # 导入Excel
    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel文件","*.xlsx;*.xls")])
        if not path:
            return
        try:
            df = pd.read_excel(path)
            self.students = df.iloc[:,0].dropna().tolist()
            self.refresh_list()
            messagebox.showinfo("成功", f"导入{len(self.students)}名学生")
        except:
            messagebox.showerror("错误", "文件读取失败")

    # 刷新名单显示
    def refresh_list(self):
        self.list_text.delete(1.0, tk.END)
        self.list_text.insert(tk.END, "、".join(self.students))

    # 添加学生
    def add_stu(self):
        name = tk.simpledialog.askstring("添加学生", "输入学生姓名")
        if name and name.strip():
            self.students.append(name.strip())
            self.refresh_list()

    # 清空名单
    def clear_list(self):
        self.students.clear()
        self.refresh_list()
        self.result_label.config(text="暂无结果")

    # 随机点名
    def roll_call(self):
        if not self.students:
            messagebox.showwarning("提示", "请先导入或添加学生")
            return
        try:
            count = int(self.num_entry.get())
            total = len(self.students)
            if count <1 or count>total:
                messagebox.showwarning("提示", f"人数范围1-{total}")
                return
            res = random.sample(self.students, count)
            self.result_label.config(text="、".join(res))
        except:
            messagebox.showerror("错误", "请输入合法数字")

if __name__ == "__main__":
    root = tk.Tk()
    import tkinter.simpledialog
    app = RollCallSystem(root)
    root.mainloop()