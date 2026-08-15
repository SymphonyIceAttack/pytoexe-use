import tkinter as tk
from tkinter import messagebox, ttk
import pyperclip

class PIDtoHEXCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("PIDHEX by zhangluyu")  # ← 修改这里
        self.root.geometry("450x380")
        self.root.resizable(False, False)
        
        # 设置样式和颜色
        self.root.configure(bg='#f0f0f0')
        
        # 主框架
        main_frame = tk.Frame(root, bg='#f0f0f0', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题（带作者信息）
        title_label = tk.Label(
            main_frame, 
            text="🖥️ PID → HEX 转换工具", 
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=(0, 5))
        
        # 作者小标签
        author_label = tk.Label(
            main_frame,
            text="by zhangluyu",
            font=("Arial", 9, "italic"),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        author_label.pack(pady=(0, 15))
        
        # 输入区域
        input_frame = tk.Frame(main_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            input_frame, 
            text="输入PID（十进制）：", 
            font=("Arial", 11),
            bg='#f0f0f0'
        ).pack(anchor=tk.W)
        
        self.entry = tk.Entry(
            input_frame,
            font=("Arial", 14),
            bg='white',
            fg='#2c3e50',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor='#3498db',
            highlightbackground='#bdc3c7'
        )
        self.entry.pack(fill=tk.X, pady=(5, 10), ipady=5)
        self.entry.bind('<Return>', lambda e: self.calculate())
        self.entry.focus()
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=10)
        
        calc_btn = tk.Button(
            button_frame,
            text="🔄 转换",
            command=self.calculate,
            font=("Arial", 11, "bold"),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        calc_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(
            button_frame,
            text="🗑️ 清空",
            command=self.clear_all,
            font=("Arial", 11),
            bg='#95a5a6',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        clear_btn.pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = tk.Frame(main_frame, bg='white', relief=tk.GROOVE, bd=2)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 10))
        
        tk.Label(
            result_frame,
            text="📊 转换结果",
            font=("Arial", 12, "bold"),
            bg='white',
            fg='#2c3e50'
        ).pack(anchor=tk.W, padx=15, pady=(10, 5))
        
        # 结果显示框
        self.result_var = tk.StringVar()
        self.result_var.set("等待输入...")
        
        self.result_label = tk.Label(
            result_frame,
            textvariable=self.result_var,
            font=("Consolas", 18, "bold"),
            bg='white',
            fg='#2c3e50',
            wraplength=380,
            justify=tk.CENTER
        )
        self.result_label.pack(expand=True, fill=tk.BOTH, padx=15, pady=10)
        
        # 历史记录区域
        history_frame = tk.Frame(main_frame, bg='#f0f0f0')
        history_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(
            history_frame,
            text="📝 历史记录",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0',
            fg='#7f8c8d'
        ).pack(anchor=tk.W)
        
        self.history_listbox = tk.Listbox(
            history_frame,
            height=3,
            font=("Consolas", 10),
            bg='white',
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor='#3498db',
            highlightbackground='#bdc3c7'
        )
        self.history_listbox.pack(fill=tk.X, pady=(2, 0))
        
        # 底部信息
        info_label = tk.Label(
            main_frame,
            text="💡 提示：双击结果可直接复制 | 支持十进制PID输入",
            font=("Arial", 9),
            bg='#f0f0f0',
            fg='#7f8c8d'
        )
        info_label.pack(pady=(10, 0))
        
        # 绑定双击复制功能
        self.result_label.bind('<Double-Button-1>', self.copy_result)
        
        # 存储历史记录
        self.history = []
    
    def calculate(self):
        """执行PID到HEX的转换"""
        try:
            pid_str = self.entry.get().strip()
            
            if not pid_str:
                messagebox.showwarning("警告", "请输入PID！")
                return
            
            # 转换为整数
            pid = int(pid_str)
            
            if pid < 0 or pid > 65535:
                messagebox.showwarning("警告", "PID范围应在 0-65535 之间！")
                return
            
            # 转换为十六进制（大写，去掉0x前缀）
            hex_value = format(pid, 'X')
            
            # 显示结果
            result_text = f"十进制: {pid}\n十六进制: 0x{hex_value}\n纯HEX: {hex_value}"
            self.result_var.set(result_text)
            
            # 添加到历史记录
            history_entry = f"{pid} → 0x{hex_value} ({hex_value})"
            self.history.append(history_entry)
            self.history_listbox.insert(0, history_entry)
            
            # 限制历史记录数量
            if self.history_listbox.size() > 10:
                self.history_listbox.delete(10)
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的十进制数字！")
        except Exception as e:
            messagebox.showerror("错误", f"转换失败：{str(e)}")
    
    def clear_all(self):
        """清空输入和结果"""
        self.entry.delete(0, tk.END)
        self.result_var.set("等待输入...")
        self.entry.focus()
    
    def copy_result(self, event=None):
        """双击复制结果到剪贴板"""
        result = self.result_var.get()
        if result and result != "等待输入...":
            # 提取HEX值
            lines = result.split('\n')
            for line in lines:
                if '纯HEX' in line:
                    hex_value = line.split(': ')[1]
                    pyperclip.copy(hex_value)
                    messagebox.showinfo("复制成功", f"已复制 HEX 值: {hex_value}")
                    break
        else:
            messagebox.showinfo("提示", "没有可复制的内容")

def main():
    root = tk.Tk()
    app = PIDtoHEXCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()