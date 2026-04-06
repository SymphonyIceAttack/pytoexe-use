import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class FileNameReplaceTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件名批量替换工具")
        self.root.geometry("800x600")
        
        # 核心变量
        self.target_folder = tk.StringVar()
        self.file_list = []
        
        # 界面布局
        # 1. 文件夹选择区域
        frame_folder = ttk.Frame(root, padding="10")
        frame_folder.pack(fill=tk.X)
        
        ttk.Label(frame_folder, text="目标文件夹：").pack(side=tk.LEFT)
        ttk.Entry(frame_folder, textvariable=self.target_folder, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_folder, text="选择文件夹", command=self.select_folder).pack(side=tk.LEFT)
        
        # 2. 替换规则区域
        frame_rule = ttk.LabelFrame(root, text="替换规则（原内容 → 新内容）", padding="10")
        frame_rule.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 规则表格
        self.rule_tree = ttk.Treeview(frame_rule, columns=("old", "new"), show="headings", height=5)
        self.rule_tree.heading("old", text="原内容")
        self.rule_tree.heading("new", text="新内容")
        self.rule_tree.column("old", width=350, anchor=tk.CENTER)
        self.rule_tree.column("new", width=350, anchor=tk.CENTER)
        self.rule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 规则操作按钮
        frame_rule_btn = ttk.Frame(frame_rule, padding="5")
        frame_rule_btn.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(frame_rule_btn, text="添加规则", command=self.add_rule).pack(fill=tk.X, pady=2)
        ttk.Button(frame_rule_btn, text="删除选中", command=self.del_rule).pack(fill=tk.X, pady=2)
        ttk.Button(frame_rule_btn, text="清空规则", command=self.clear_rule).pack(fill=tk.X, pady=2)
        
        # 3. 预览区域
        frame_preview = ttk.LabelFrame(root, text="文件名预览", padding="10")
        frame_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 预览表格
        self.preview_tree = ttk.Treeview(frame_preview, columns=("old_name", "new_name"), show="headings", height=10)
        self.preview_tree.heading("old_name", text="原文件名")
        self.preview_tree.heading("new_name", text="替换后文件名")
        self.preview_tree.column("old_name", width=380, anchor=tk.W)
        self.preview_tree.column("new_name", width=380, anchor=tk.W)
        self.preview_tree.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.preview_tree, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 4. 操作按钮区域
        frame_btn = ttk.Frame(root, padding="10")
        frame_btn.pack(fill=tk.X)
        
        ttk.Button(frame_btn, text="刷新预览", command=self.preview_replace).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame_btn, text="执行批量替换", command=self.do_replace).pack(side=tk.RIGHT, padx=10)
    
    # 选择目标文件夹
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder.set(folder)
            self.preview_replace()
    
    # 添加替换规则
    def add_rule(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加替换规则")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="原内容：").pack(padx=10, pady=5, anchor=tk.W)
        old_entry = ttk.Entry(dialog, width=40)
        old_entry.pack(padx=10, fill=tk.X)
        
        ttk.Label(dialog, text="新内容：").pack(padx=10, pady=5, anchor=tk.W)
        new_entry = ttk.Entry(dialog, width=40)
        new_entry.pack(padx=10, fill=tk.X)
        
        def confirm():
            old = old_entry.get().strip()
            new = new_entry.get().strip()
            if old:
                self.rule_tree.insert("", tk.END, values=(old, new))
                dialog.destroy()
            else:
                messagebox.showwarning("提示", "原内容不能为空！")
        
        ttk.Button(dialog, text="确认添加", command=confirm).pack(pady=15)
    
    # 删除选中规则
    def del_rule(self):
        selected = self.rule_tree.selection()
        if selected:
            for item in selected:
                self.rule_tree.delete(item)
        else:
            messagebox.showwarning("提示", "请先选中要删除的规则！")
    
    # 清空所有规则
    def clear_rule(self):
        for item in self.rule_tree.get_children():
            self.rule_tree.delete(item)
    
    # 预览替换结果
    def preview_replace(self):
        # 清空预览表
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        folder = self.target_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            return
        
        # 读取所有替换规则
        rules = []
        for item in self.rule_tree.get_children():
            old, new = self.rule_tree.item(item, "values")
            rules.append((old, new))
        
        # 遍历文件夹内的文件
        self.file_list = []
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                self.file_list.append(filename)
                # 分离文件名和后缀，避免修改文件格式
                name_part, ext_part = os.path.splitext(filename)
                new_name = name_part
                # 按规则批量替换
                for old_str, new_str in rules:
                    new_name = new_name.replace(old_str, new_str)
                new_full_name = new_name + ext_part
                # 插入预览表
                self.preview_tree.insert("", tk.END, values=(filename, new_full_name))
    
    # 执行批量重命名
    def do_replace(self):
        folder = self.target_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请先选择有效的目标文件夹！")
            return
        
        rules = []
        for item in self.rule_tree.get_children():
            old, new = self.rule_tree.item(item, "values")
            rules.append((old, new))
        if not rules:
            messagebox.showerror("错误", "请至少添加一条替换规则！")
            return
        
        # 二次确认，防止误操作
        if not messagebox.askyesno("确认", "替换操作不可撤销，建议先备份文件！\n是否确认执行批量替换？"):
            return
        
        # 执行重命名
        success_count = 0
        fail_count = 0
        for filename in self.file_list:
            try:
                old_path = os.path.join(folder, filename)
                name_part, ext_part = os.path.splitext(filename)
                new_name = name_part
                for old_str, new_str in rules:
                    new_name = new_name.replace(old_str, new_str)
                new_full_name = new_name + ext_part
                new_path = os.path.join(folder, new_full_name)
                
                if old_path != new_path:
                    os.rename(old_path, new_path)
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"替换失败：{filename}，错误：{str(e)}")
        
        # 刷新预览并提示结果
        self.preview_replace()
        messagebox.showinfo("完成", f"批量替换执行完毕！\n成功：{success_count} 个\n失败：{fail_count} 个")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileNameReplaceTool(root)
    root.mainloop()
