import tkinter as tk
from tkinter import messagebox, filedialog

class LadderCompiler:
    def __init__(self, root):
        self.root = root
        self.root.title("简易梯形图编译器")
        self.root.geometry("600x400")
        
        # 创建界面组件
        self.create_widgets()
        
        # 存储梯形图元素
        self.elements = []
    
    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="梯形图编译器", font=("Arial", 16))
        title_label.pack(pady=10)
        
        # 输入区域
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(input_frame, text="输入梯形图指令 (每行一个元素):").pack(anchor=tk.W)
        
        self.input_text = tk.Text(input_frame, height=8)
        self.input_text.pack(fill=tk.X, pady=5)
        self.input_text.insert(tk.END, "常开 X0\n常闭 X1\n线圈 Y0")
        
        # 按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="编译", command=self.compile_ladder).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="清空", command=self.clear_input).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="保存", command=self.save_file).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="加载", command=self.load_file).pack(side=tk.LEFT, padx=5)
        
        # 输出区域
        output_frame = tk.Frame(self.root)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(output_frame, text="编译结果:").pack(anchor=tk.W)
        
        self.output_text = tk.Text(output_frame, height=8)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def compile_ladder(self):
        # 获取输入内容
        input_data = self.input_text.get("1.0", tk.END).splitlines()
        self.elements = [line.strip() for line in input_data if line.strip()]
        
        # 编译逻辑
        output_lines = []
        for element in self.elements:
            if "常开" in element:
                output_lines.append(f"LD {element.split()[1]}")
            elif "常闭" in element:
                output_lines.append(f"LDN {element.split()[1]}")
            elif "线圈" in element:
                output_lines.append(f"OUT {element.split()[1]}")
            else:
                output_lines.append(f"; 未知元素: {element}")
        
        # 显示结果
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "\n".join(output_lines))
        messagebox.showinfo("编译完成", f"成功编译 {len(self.elements)} 个元件")
    
    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.elements = []
    
    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".lad",
            filetypes=[("梯形图文件", "*.lad"), ("所有文件", "*.*")]
        )
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.input_text.get("1.0", tk.END))
            messagebox.showinfo("保存成功", f"文件已保存到:\n{file_path}")
    
   
