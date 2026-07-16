import tkinter as tk
from tkinter import ttk, messagebox

class UnitConverter:
    def __init__(self, root):
        self.root = root
        root.title("mm ⇄ mil 单位转换器")
        root.geometry("400x300")
        root.resizable(False, False)
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 标题
        title = tk.Label(root, text="毫米 (mm) ⇄ 密耳 (mil) 转换", 
                        font=("Arial", 16, "bold"), fg="#2c3e50")
        title.pack(pady=15)
        
        # 转换公式提示
        info = tk.Label(root, text="1 mm = 39.3701 mil\n1 mil = 0.0254 mm", 
                       font=("Arial", 10), fg="#7f8c8d", justify="center")
        info.pack(pady=5)
        
        # === mm 转 mil 区域 ===
        frame1 = tk.LabelFrame(root, text="毫米 → 密耳", font=("Arial", 11), padx=15, pady=10)
        frame1.pack(fill="x", padx=20, pady=8)
        
        tk.Label(frame1, text="输入 mm:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.mm_entry = tk.Entry(frame1, font=("Arial", 12), width=15)
        self.mm_entry.grid(row=0, column=1, padx=5, pady=5)
        self.mm_entry.bind('<Return>', lambda e: self.mm_to_mil())
        
        self.mm_to_mil_btn = tk.Button(frame1, text="→ 转换为 mil", font=("Arial", 10), 
                                      bg="#3498db", fg="white", command=self.mm_to_mil)
        self.mm_to_mil_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.mm_result = tk.Label(frame1, text="结果: ", font=("Arial", 11, "bold"), fg="#2c3e50")
        self.mm_result.grid(row=1, column=0, columnspan=3, pady=5)
        
        # === mil 转 mm 区域 ===
        frame2 = tk.LabelFrame(root, text="密耳 → 毫米", font=("Arial", 11), padx=15, pady=10)
        frame2.pack(fill="x", padx=20, pady=8)
        
        tk.Label(frame2, text="输入 mil:", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.mil_entry = tk.Entry(frame2, font=("Arial", 12), width=15)
        self.mil_entry.grid(row=0, column=1, padx=5, pady=5)
        self.mil_entry.bind('<Return>', lambda e: self.mil_to_mm())
        
        self.mil_to_mm_btn = tk.Button(frame2, text="→ 转换为 mm", font=("Arial", 10),
                                      bg="#e67e22", fg="white", command=self.mil_to_mm)
        self.mil_to_mm_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.mil_result = tk.Label(frame2, text="结果: ", font=("Arial", 11, "bold"), fg="#2c3e50")
        self.mil_result.grid(row=1, column=0, columnspan=3, pady=5)
        
        # 清除按钮
        clear_btn = tk.Button(root, text="清空所有", font=("Arial", 10), 
                             bg="#95a5a6", fg="white", command=self.clear_all)
        clear_btn.pack(pady=10)
    
    def mm_to_mil(self):
        """毫米转密耳"""
        try:
            mm = float(self.mm_entry.get().strip())
            mil = mm * 39.3701
            self.mm_result.config(text=f"结果: {mm} mm = {mil:.4f} mil")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
    
    def mil_to_mm(self):
        """密耳转毫米"""
        try:
            mil = float(self.mil_entry.get().strip())
            mm = mil * 0.0254
            self.mil_result.config(text=f"结果: {mil} mil = {mm:.4f} mm")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
    
    def clear_all(self):
        """清空所有输入和结果"""
        self.mm_entry.delete(0, tk.END)
        self.mil_entry.delete(0, tk.END)
        self.mm_result.config(text="结果: ")
        self.mil_result.config(text="结果: ")

if __name__ == "__main__":
    root = tk.Tk()
    app = UnitConverter(root)
    root.mainloop()