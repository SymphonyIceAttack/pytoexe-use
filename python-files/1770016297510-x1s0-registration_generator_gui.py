import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pyperclip
import sys

def encode_last_byte(b):
    """编码最后一个字节"""
    high = (b >> 4) - 5
    low = (b & 0x0F) + 5
    
    # 高4位映射到 A-Z
    if 0 <= high <= 25:
        char1 = chr(ord('A') + high)
    else:
        char1 = '?'
    
    # 低4位映射
    if 0 <= low <= 9:
        char2 = str(low)
    elif 10 <= low <= 14:
        char2 = chr(ord('A') + (low - 10))
    else:
        char2 = '?'
    
    return char1 + char2

def generate_registration_code(machine_code_hex):
    """生成注册码"""
    machine_code_hex = machine_code_hex.replace(' ', '').replace('-', '').upper()
    
    if len(machine_code_hex) != 16:
        return None, "错误：机器码必须是16位十六进制数"
    
    try:
        bytes_data = bytes.fromhex(machine_code_hex)
        fixed_part = "GKJGKGKK555G5;"
        last_byte = bytes_data[7]
        last_part = encode_last_byte(last_byte)
        return fixed_part + last_part, None
    except ValueError:
        return None, "错误：无效的十六进制数"
    except Exception as e:
        return None, f"错误：{e}"

class RegistrationGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("机器码注册码生成器 v1.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义颜色
        self.bg_color = "#f0f0f0"
        self.button_color = "#4CAF50"
        self.root.configure(bg=self.bg_color)
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 标题
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=20)
        
        title_label = tk.Label(
            title_frame, 
            text="机器码注册码生成器", 
            font=("微软雅黑", 20, "bold"),
            bg=self.bg_color,
            fg="#333"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="输入16位十六进制机器码，自动生成对应注册码",
            font=("微软雅黑", 10),
            bg=self.bg_color,
            fg="#666"
        )
        subtitle_label.pack()
        
        # 输入区域
        input_frame = tk.LabelFrame(
            self.root, 
            text="输入机器码", 
            font=("微软雅黑", 11),
            bg=self.bg_color,
            padx=20,
            pady=15
        )
        input_frame.pack(padx=30, pady=10, fill="x")
        
        # 输入框和标签
        tk.Label(
            input_frame, 
            text="机器码（16位十六进制）:", 
            font=("微软雅黑", 10),
            bg=self.bg_color
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        self.machine_code_var = tk.StringVar()
        self.machine_code_entry = ttk.Entry(
            input_frame, 
            textvariable=self.machine_code_var,
            font=("Consolas", 12),
            width=30
        )
        self.machine_code_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # 示例标签
        tk.Label(
            input_frame,
            text="示例: BFEBFBFF000B06F2",
            font=("微软雅黑", 9),
            bg=self.bg_color,
            fg="#888"
        ).grid(row=1, column=1, sticky="w", padx=10)
        
        # 按钮区域
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=15)
        
        # 生成按钮
        generate_btn = tk.Button(
            button_frame,
            text="生成注册码",
            command=self.generate_code,
            font=("微软雅黑", 11, "bold"),
            bg=self.button_color,
            fg="white",
            padx=25,
            pady=8,
            cursor="hand2"
        )
        generate_btn.pack(side="left", padx=5)
        
        # 复制按钮
        copy_btn = tk.Button(
            button_frame,
            text="复制注册码",
            command=self.copy_to_clipboard,
            font=("微软雅黑", 11),
            bg="#2196F3",
            fg="white",
            padx=25,
            pady=8,
            cursor="hand2"
        )
        copy_btn.pack(side="left", padx=5)
        
        # 清空按钮
        clear_btn = tk.Button(
            button_frame,
            text="清空",
            command=self.clear_all,
            font=("微软雅黑", 11),
            bg="#FF9800",
            fg="white",
            padx=25,
            pady=8,
            cursor="hand2"
        )
        clear_btn.pack(side="left", padx=5)
        
        # 输出区域
        output_frame = tk.LabelFrame(
            self.root, 
            text="生成的注册码", 
            font=("微软雅黑", 11),
            bg=self.bg_color,
            padx=20,
            pady=15
        )
        output_frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        # 注册码显示（大字体，只读）
        self.registration_code_var = tk.StringVar()
        registration_code_entry = tk.Entry(
            output_frame,
            textvariable=self.registration_code_var,
            font=("Consolas", 16, "bold"),
            bg="white",
            fg="#D32F2F",
            justify="center",
            state="readonly",
            readonlybackground="white",
            relief="flat"
        )
        registration_code_entry.pack(fill="x", pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            output_frame,
            text="等待输入...",
            font=("微软雅黑", 9),
            bg=self.bg_color,
            fg="#666"
        )
        self.status_label.pack()
        
        # 历史记录区域
        history_frame = tk.LabelFrame(
            self.root,
            text="生成历史",
            font=("微软雅黑", 11),
            bg=self.bg_color,
            padx=20,
            pady=15
        )
        history_frame.pack(padx=30, pady=10, fill="both", expand=True)
        
        # 历史记录文本框
        self.history_text = scrolledtext.ScrolledText(
            history_frame,
            height=6,
            font=("Consolas", 9),
            wrap=tk.NONE
        )
        self.history_text.pack(fill="both", expand=True)
        
        # 默认聚焦到输入框
        self.machine_code_entry.focus()
        
        # 绑定回车键
        self.root.bind('<Return>', lambda event: self.generate_code())
        
        # 添加测试数据菜单
        self.create_menu()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="测试示例1", 
                              command=lambda: self.set_machine_code("BFEBFBFF000B06F2"))
        tools_menu.add_command(label="测试示例2", 
                              command=lambda: self.set_machine_code("BFEBFBFF000B06A2"))
        tools_menu.add_separator()
        tools_menu.add_command(label="清空历史", command=self.clear_history)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def set_machine_code(self, code):
        """设置机器码到输入框"""
        self.machine_code_var.set(code)
        self.generate_code()
    
    def generate_code(self):
        """生成注册码"""
        machine_code = self.machine_code_var.get().strip()
        
        if not machine_code:
            messagebox.showwarning("警告", "请输入机器码！")
            return
        
        registration_code, error = generate_registration_code(machine_code)
        
        if error:
            self.registration_code_var.set("")
            self.status_label.config(text=error, fg="red")
            messagebox.showerror("错误", error)
        else:
            self.registration_code_var.set(registration_code)
            self.status_label.config(text="✓ 注册码生成成功！", fg="green")
            
            # 添加到历史记录
            self.add_to_history(machine_code, registration_code)
    
    def add_to_history(self, machine_code, registration_code):
        """添加到历史记录"""
        history_entry = f"机器码: {machine_code}  ->  注册码: {registration_code}\n"
        self.history_text.insert(tk.END, history_entry)
        self.history_text.see(tk.END)  # 滚动到底部
    
    def copy_to_clipboard(self):
        """复制注册码到剪贴板"""
        registration_code = self.registration_code_var.get()
        if registration_code:
            try:
                pyperclip.copy(registration_code)
                self.status_label.config(text="✓ 注册码已复制到剪贴板", fg="blue")
            except:
                messagebox.showerror("错误", "无法复制到剪贴板，请手动复制")
        else:
            messagebox.showwarning("警告", "没有可复制的注册码")
    
    def clear_all(self):
        """清空所有输入和输出"""
        self.machine_code_var.set("")
        self.registration_code_var.set("")
        self.status_label.config(text="等待输入...", fg="#666")
        self.machine_code_entry.focus()
    
    def clear_history(self):
        """清空历史记录"""
        self.history_text.delete(1.0, tk.END)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """机器码注册码生成器 v1.0

功能：
1. 输入16位十六进制机器码
2. 自动生成对应的注册码
3. 支持复制到剪贴板
4. 保存生成历史

规则说明：
- 前7字节固定编码为"GKJGKGKK555G5;"
- 最后一个字节按特定规则编码

示例：
BFEBFBFF000B06F2 → GKJGKGKK555G5;K7
BFEBFBFF000B06A2 → GKJGKGKK555G5;F7"""
        
        messagebox.showinfo("关于", about_text)

def main():
    root = tk.Tk()
    app = RegistrationGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()