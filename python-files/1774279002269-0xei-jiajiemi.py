import tkinter as tk
from tkinter import messagebox, ttk
import random
import string

# 加密解密核心算法


def caesar_cipher(text: str, key: int, mode: str = 'encrypt') -> str:
    """
    凯撒密码加解密核心函数
    :param text: 输入文本
    :param key: 移位密钥 (1-25)
    :param mode: 'encrypt' 加密 或 'decrypt' 解密
    :return: 处理后的文本
    """
    result = []
    shift = key if mode == 'encrypt' else -key
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            # 计算移位后的字符
            shifted = (ord(ch) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            result.append(ch)  # 非字母保持不变
    return ''.join(result)


class CaesarCipherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("凯撒密码加解密系统")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # 设置样式
        self.root.configure(bg='#f0f0f0')
        self.setup_styles()

        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 操作选择区域
        self.create_operation_section(main_frame)

        # 密钥设置区域
        self.create_key_section(main_frame)

        # 输入输出区域
        self.create_io_section(main_frame)

        # 按钮区域
        self.create_button_section(main_frame)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 默认操作模式
        self.current_mode = "encrypt"

    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('微软雅黑', 10))
        style.configure('TButton', font=('微软雅黑', 10))
        style.configure('TLabelframe', background='#f0f0f0',
                        font=('微软雅黑', 10, 'bold'))
        style.configure('TLabelframe.Label',
                        background='#f0f0f0', font=('微软雅黑', 10, 'bold'))

    def create_operation_section(self, parent):
        """创建操作选择区域"""
        op_frame = ttk.LabelFrame(parent, text="操作选择", padding="10")
        op_frame.pack(fill=tk.X, pady=(0, 10))

        self.op_var = tk.StringVar(value="encrypt")

        ttk.Radiobutton(op_frame, text="加密", variable=self.op_var,
                        value="encrypt", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(op_frame, text="解密", variable=self.op_var,
                        value="decrypt", command=self.on_mode_change).pack(side=tk.LEFT, padx=10)

    def on_mode_change(self):
        """模式切换时的回调"""
        self.current_mode = self.op_var.get()
        self.status_var.set(
            f"已切换到{'加密' if self.current_mode == 'encrypt' else '解密'}模式")
        # 清空输入输出区域提示
        if self.current_mode == 'encrypt':
            self.input_label.config(text="请输入要加密的英文句子:")
            self.process_btn.config(text="加密")
        else:
            self.input_label.config(text="请输入密文:")
            self.process_btn.config(text="解密")
        # 清空输入输出
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)

    def create_key_section(self, parent):
        """创建密钥设置区域"""
        key_frame = ttk.LabelFrame(parent, text="密钥设置", padding="10")
        key_frame.pack(fill=tk.X, pady=(0, 10))

        # 密钥类型选择
        self.key_type_var = tk.StringVar(value="custom")
        ttk.Radiobutton(key_frame, text="自定义密钥", variable=self.key_type_var,
                        value="custom", command=self.on_key_type_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(key_frame, text="随机密钥", variable=self.key_type_var,
                        value="random", command=self.on_key_type_change).pack(side=tk.LEFT, padx=10)

        # 密钥输入框
        key_input_frame = ttk.Frame(key_frame)
        key_input_frame.pack(side=tk.LEFT, padx=20)

        ttk.Label(key_input_frame, text="密钥值 (1-25):").pack(side=tk.LEFT)
        self.key_entry = ttk.Entry(
            key_input_frame, width=10, font=('Consolas', 10))
        self.key_entry.pack(side=tk.LEFT, padx=5)
        self.key_entry.insert(0, "3")

        # 随机密钥显示
        self.random_key_label = ttk.Label(
            key_frame, text="", foreground="blue")
        self.random_key_label.pack(side=tk.LEFT, padx=10)

        # 生成随机密钥按钮
        self.gen_random_btn = ttk.Button(
            key_frame, text="生成随机密钥", command=self.generate_random_key)
        self.gen_random_btn.pack(side=tk.LEFT, padx=5)
        self.gen_random_btn.config(state=tk.DISABLED)  # 初始禁用，因为默认是自定义模式

    def on_key_type_change(self):
        """密钥类型切换时的回调"""
        if self.key_type_var.get() == "random":
            self.key_entry.config(state=tk.DISABLED)
            self.gen_random_btn.config(state=tk.NORMAL)
            self.generate_random_key()  # 自动生成一个随机密钥
        else:
            self.key_entry.config(state=tk.NORMAL)
            self.gen_random_btn.config(state=tk.DISABLED)
            # 确保密钥值有效
            self.validate_key()

    def generate_random_key(self):
        """生成1-25之间的随机密钥"""
        key = random.randint(1, 25)
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, str(key))
        self.random_key_label.config(text=f"已生成随机密钥: {key}")
        self.status_var.set(f"随机密钥已生成: {key}")

    def validate_key(self) -> int:
        """验证密钥输入，返回有效的密钥值"""
        try:
            key = int(self.key_entry.get().strip())
            if 1 <= key <= 25:
                return key
            else:
                raise ValueError
        except ValueError:
            # 无效输入时，默认使用3
            messagebox.showwarning("密钥错误", "密钥必须是1-25之间的整数，已自动设为3")
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, "3")
            return 3

    def create_io_section(self, parent):
        """创建输入输出区域"""
        io_frame = ttk.Frame(parent)
        io_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 输入区域
        input_frame = ttk.LabelFrame(io_frame, text="输入", padding="5")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.input_label = ttk.Label(input_frame, text="请输入要加密的英文句子:")
        self.input_label.pack(anchor=tk.W)

        self.input_text = tk.Text(
            input_frame, height=8, width=30, font=('Consolas', 10), wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # 滚动条
        input_scroll = ttk.Scrollbar(
            input_frame, command=self.input_text.yview)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text.config(yscrollcommand=input_scroll.set)

        # 输出区域
        output_frame = ttk.LabelFrame(io_frame, text="输出", padding="5")
        output_frame.pack(side=tk.RIGHT, fill=tk.BOTH,
                          expand=True, padx=(5, 0))

        ttk.Label(output_frame, text="处理结果:").pack(anchor=tk.W)

        self.output_text = tk.Text(
            output_frame, height=8, width=30, font=('Consolas', 10), wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)

        output_scroll = ttk.Scrollbar(
            output_frame, command=self.output_text.yview)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=output_scroll.set)

        # 快捷操作按钮
        quick_frame = ttk.Frame(io_frame)
        quick_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        ttk.Button(quick_frame, text="清空输入", command=self.clear_input).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="清空输出", command=self.clear_output).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(quick_frame, text="交换内容", command=self.swap_content).pack(
            side=tk.LEFT, padx=5)

    def create_button_section(self, parent):
        """创建按钮区域"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.process_btn = ttk.Button(
            btn_frame, text="加密", command=self.process, style='Accent.TButton')
        self.process_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 尝试创建带样式的按钮
        try:
            style = ttk.Style()
            style.configure('Accent.TButton', font=(
                '微软雅黑', 10, 'bold'), background='#4caf50')
        except:
            pass

        ttk.Button(btn_frame, text="退出", command=self.root.quit).pack(
            side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def clear_input(self):
        """清空输入框"""
        self.input_text.delete(1.0, tk.END)
        self.status_var.set("输入已清空")

    def clear_output(self):
        """清空输出框"""
        self.output_text.delete(1.0, tk.END)
        self.status_var.set("输出已清空")

    def swap_content(self):
        """交换输入输出内容"""
        input_content = self.input_text.get(1.0, tk.END).strip()
        output_content = self.output_text.get(1.0, tk.END).strip()
        if output_content:
            self.input_text.delete(1.0, tk.END)
            self.input_text.insert(1.0, output_content)
        if input_content:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(1.0, input_content)
        self.status_var.set("已交换输入输出内容")

    def process(self):
        """执行加解密操作"""
        input_text = self.input_text.get(1.0, tk.END).strip()
        if not input_text:
            messagebox.showwarning("输入为空", "请输入要处理的文本")
            return

        # 获取密钥
        key = self.validate_key()

        try:
            # 根据当前模式执行操作
            if self.current_mode == "encrypt":
                result = caesar_cipher(input_text, key, "encrypt")
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(1.0, result)
                self.status_var.set(f"加密完成，密钥: {key}")
            else:
                result = caesar_cipher(input_text, key, "decrypt")
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(1.0, result)
                self.status_var.set(f"解密完成，密钥: {key}")
        except Exception as e:
            messagebox.showerror("处理错误", f"处理过程中出现错误:\n{str(e)}")
            self.status_var.set("处理失败")


def main():
    root = tk.Tk()
    app = CaesarCipherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
