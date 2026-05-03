import tkinter as tk
from tkinter import messagebox, filedialog
import json
import random

class WordGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("生成器")
        self.categories = {}
        self.current_category = None
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.setup_category_management(left_frame)
        self.setup_pattern_management(left_frame)
        self.setup_generation_controls(right_frame)
        self.setup_save_load_controls(right_frame)
        
    def setup_category_management(self, parent):
        category_frame = tk.LabelFrame(parent, text="类型管理")
        category_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(category_frame, text="类型名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.category_entry = tk.Entry(category_frame)
        self.category_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        category_frame.columnconfigure(1, weight=1)
        
        btn_frame = tk.Frame(category_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        tk.Button(btn_frame, text="添加类型", command=self.add_category).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="删除类型", command=self.delete_category).pack(side=tk.LEFT, padx=2)
        
        tk.Label(category_frame, text="现有类型:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(10, 5))
        
        self.category_listbox = tk.Listbox(category_frame, height=6)
        self.category_listbox.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=(0, 5))
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
    def setup_pattern_management(self, parent):
        pattern_frame = tk.LabelFrame(parent, text="组合管理")
        pattern_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        tk.Label(pattern_frame, text="组合:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.pattern_entry = tk.Entry(pattern_frame)
        self.pattern_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        tk.Label(pattern_frame, text="权重:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.weight_entry = tk.Entry(pattern_frame)
        self.weight_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        pattern_frame.columnconfigure(1, weight=1)
        
        btn_frame = tk.Frame(pattern_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        tk.Button(btn_frame, text="添加组合", command=self.add_pattern).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="删除组合", command=self.delete_pattern).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="特殊组合说明", command=self.show_special_instructions).pack(side=tk.LEFT, padx=2)
        
        tk.Label(pattern_frame, text="当前类型已有的组合:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=(10, 5))
        
        self.pattern_listbox = tk.Listbox(pattern_frame)
        self.pattern_listbox.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=(0, 5))
        pattern_frame.rowconfigure(4, weight=1)
        
    def setup_generation_controls(self, parent):
        gen_frame = tk.LabelFrame(parent, text="生成管理")
        gen_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(gen_frame, text="类型顺序:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.sequence_entry = tk.Entry(gen_frame)
        self.sequence_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        tk.Label(gen_frame, text="生成数量:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.count_entry = tk.Entry(gen_frame)
        self.count_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        gen_frame.columnconfigure(1, weight=1)
        
        tk.Button(gen_frame, text="生成", command=self.generate_words).grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Label(gen_frame, text="生成结果:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=(10, 5))
        
        self.result_text = tk.Text(gen_frame, height=10, width=30)
        self.result_text.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=(0, 5))
        gen_frame.rowconfigure(4, weight=1)
        
    def setup_save_load_controls(self, parent):
        save_frame = tk.LabelFrame(parent, text="存档管理")
        save_frame.pack(fill=tk.X, pady=(5, 0))
        
        btn_frame = tk.Frame(save_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="存档", command=self.save_data).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="读档", command=self.load_data).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="清除", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="复制", command=self.copy_results).pack(side=tk.LEFT, padx=5)
        
    def show_special_instructions(self):
        instructions = """
特殊说明 - void 使用规则:

如果字母组合设定为"void"(不区分大小写)，则在生成时:
- 如果抽到void，则该类型位置不输出任何内容
- 例如: 类型C包含 void(权重3) 和 b(权重2)
- 生成CC时可能的结果有:
  * b (第一个C是void，第二个C是b)
  * bb (两个C都是b)
  * 空字符串 (两个C都是void)
  * b (第一个C是b，第二个C是void)
        """
        messagebox.showinfo("特殊组合说明", instructions)
        
    def copy_results(self):
        results = self.result_text.get(1.0, tk.END).strip()
        if results:
            self.root.clipboard_clear()
            self.root.clipboard_append(results)
            messagebox.showinfo("成功", "结果已复制到剪贴板")
        else:
            messagebox.showinfo("提示", "没有内容可复制")
        
    def add_category(self):
        name = self.category_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入类型名称")
            return
        
        if name in self.categories:
            messagebox.showerror("错误", "类型已存在")
            return
        
        self.categories[name] = {}
        self.update_category_listbox()
        self.category_entry.delete(0, tk.END)
        
    def delete_category(self):
        selection = self.category_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请选择要删除的类型")
            return
        
        category_name = self.category_listbox.get(selection[0])
        if messagebox.askyesno("确认", f"确定要删除类型 '{category_name}' 吗？"):
            del self.categories[category_name]
            if self.current_category == category_name:
                self.current_category = None
            self.update_category_listbox()
            self.pattern_listbox.delete(0, tk.END)
        
    def on_category_select(self, event):
        selection = self.category_listbox.curselection()
        if selection:
            category_name = self.category_listbox.get(selection[0])
            self.current_category = category_name
            self.update_pattern_listbox(category_name)
        
    def add_pattern(self):
        if not self.current_category:
            messagebox.showerror("错误", "请先选择一个类型")
            return
        
        category_name = self.current_category
        pattern = self.pattern_entry.get().strip()
        weight_str = self.weight_entry.get().strip()
        
        if not pattern or not weight_str:
            messagebox.showerror("错误", "请输入组合和权重")
            return
        
        try:
            weight = int(weight_str)
            if weight <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "权重必须是正整数")
            return
        
        self.categories[category_name][pattern] = weight
        self.update_pattern_listbox(category_name)
        self.pattern_entry.delete(0, tk.END)
        self.weight_entry.delete(0, tk.END)
        
    def delete_pattern(self):
        selection = self.pattern_listbox.curselection()
        if not selection:
            messagebox.showerror("错误", "请选择要删除的组合")
            return
            
        if not self.current_category:
            messagebox.showerror("错误", "请先选择一个类型")
            return
        
        category_name = self.current_category
        pattern_text = self.pattern_listbox.get(selection[0])
        
        if " - " in pattern_text:
            pattern = pattern_text.split(" - ")[0]
        else:
            pattern = pattern_text
        
        if messagebox.askyesno("确认", f"确定要删除组合 '{pattern}' 吗？"):
            if pattern in self.categories[category_name]:
                del self.categories[category_name][pattern]
                self.update_pattern_listbox(category_name)
            else:
                messagebox.showerror("错误", f"组合 '{pattern}' 不存在")
        
    def generate_words(self):
        sequence = self.sequence_entry.get().strip().upper()
        count_str = self.count_entry.get().strip()
        
        if not sequence or not count_str:
            messagebox.showerror("错误", "请输入类型顺序和生成数量")
            return
        
        try:
            count = int(count_str)
            if count < 1 or count > 9999:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "生成数量必须是1-9999之间的整数")
            return
        
        for char in sequence:
            if char not in self.categories or not self.categories[char]:
                messagebox.showerror("错误", f"类型 '{char}' 不存在或没有定义字母组合")
                return
        
        results = []
        for _ in range(count):
            word = ""
            for char in sequence:
                patterns = list(self.categories[char].keys())
                weights = list(self.categories[char].values())
                chosen_pattern = random.choices(patterns, weights=weights)[0]
                
                if chosen_pattern.lower() != "void":
                    word += chosen_pattern
            
            results.append(word)
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, "\n".join(results))
        
    def save_data(self):
        if not self.categories:
            messagebox.showerror("错误", "没有数据可保存")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.categories, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "数据保存成功")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
        
    def load_data(self):
        if self.categories and not messagebox.askyesno("确认", "读档将覆盖当前所有数据，确定继续吗？"):
            return
        
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
                self.current_category = None
                self.update_category_listbox()
                self.pattern_listbox.delete(0, tk.END)
                messagebox.showinfo("成功", "数据加载成功")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")
        
    def clear_all(self):
        if not self.categories:
            messagebox.showinfo("提示", "已经是空数据")
            return
        
        if messagebox.askyesno("确认", "确定要清除所有数据吗？"):
            self.categories.clear()
            self.current_category = None
            self.update_category_listbox()
            self.pattern_listbox.delete(0, tk.END)
            self.result_text.delete(1.0, tk.END)
            self.category_entry.delete(0, tk.END)
            self.pattern_entry.delete(0, tk.END)
            self.weight_entry.delete(0, tk.END)
            self.sequence_entry.delete(0, tk.END)
            self.count_entry.delete(0, tk.END)
        
    def update_category_listbox(self):
        self.category_listbox.delete(0, tk.END)
        for category in sorted(self.categories.keys()):
            self.category_listbox.insert(tk.END, category)
        
    def update_pattern_listbox(self, category_name):
        self.pattern_listbox.delete(0, tk.END)
        for pattern, weight in self.categories[category_name].items():
            self.pattern_listbox.insert(tk.END, f"{pattern} - {weight}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordGenerator(root)
    root.mainloop()
