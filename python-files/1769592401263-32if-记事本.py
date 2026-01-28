import tkinter as tk
from tkinter import filedialog, messagebox
import os

class Notepad:
    def __init__(self, root):
        # 初始化主窗口
        self.root = root
        self.root.title("简易记事本 - 未命名")
        self.root.geometry("800x600")  # 默认窗口大小

        # 初始化文件路径变量（None 表示未保存的新文件）
        self.file_path = None

        # 创建菜单栏
        self.create_menu()

        # 创建文本编辑区域
        self.text_area = tk.Text(self.root, wrap=tk.WORD, font=("Consolas", 12))
        self.text_area.pack(expand=True, fill=tk.BOTH)  # 填满窗口并支持缩放

        # 绑定快捷键
        self.bind_shortcuts()

    def create_menu(self):
        """创建菜单栏"""
        menu_bar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="新建", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app, accelerator="Alt+F4")
        menu_bar.add_cascade(label="文件", menu=file_menu)

        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menu_bar)

    def bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-s>", lambda e: self.save_as_file())

    def new_file(self):
        """新建文件"""
        # 如果当前内容未保存，弹出提示
        if self.check_unsaved_changes():
            return
        
        # 清空文本区域，重置文件路径
        self.text_area.delete(1.0, tk.END)
        self.file_path = None
        self.root.title("简易记事本 - 未命名")

    def open_file(self):
        """打开文件"""
        # 如果当前内容未保存，弹出提示
        if self.check_unsaved_changes():
            return
        
        # 弹出文件选择对话框，只显示文本文件
        file_path = filedialog.askopenfilename(
            title="打开文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 清空文本区域并写入新内容
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(1.0, content)
                self.file_path = file_path
                self.root.title(f"简易记事本 - {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"打开文件失败：{str(e)}")

    def save_file(self):
        """保存文件（已有路径则直接保存，无则调用另存为）"""
        if self.file_path:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(self.file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("成功", "文件保存成功！")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败：{str(e)}")
        else:
            self.save_as_file()

    def save_as_file(self):
        """另存为文件"""
        file_path = filedialog.asksaveasfilename(
            title="另存为",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.file_path = file_path
                self.root.title(f"简易记事本 - {os.path.basename(file_path)}")
                messagebox.showinfo("成功", "文件保存成功！")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败：{str(e)}")

    def check_unsaved_changes(self):
        """检查是否有未保存的更改，返回 True 表示需要中断操作"""
        # 获取文本区域内容（排除最后一个换行符）
        content = self.text_area.get(1.0, tk.END).rstrip("\n")
        
        # 如果是新文件且有内容，或已有文件但内容已修改
        if (self.file_path is None and content) or (self.file_path and content != self.get_file_content()):
            result = messagebox.askyesnocancel("提示", "当前文件有未保存的更改，是否保存？")
            if result is True:
                self.save_file()  # 保存后继续操作
                return False
            elif result is None:
                return True  # 取消操作
        return False

    def get_file_content(self):
        """获取当前文件的原始内容（用于对比是否修改）"""
        if not self.file_path:
            return ""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read().rstrip("\n")
        except:
            return ""

    def show_about(self):
        """显示关于信息"""
        messagebox.showinfo("关于", "简易Python记事本\n版本：1.0\n使用tkinter开发")

    def quit_app(self):
        """退出程序"""
        if self.check_unsaved_changes():
            return
        self.root.quit()

if __name__ == "__main__":
    # 创建主窗口并运行
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()
