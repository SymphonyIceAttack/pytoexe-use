import tkinter as tk
from tkinter import messagebox
import winreg
import windnd
import os
import sys

class AutoStartTool:
    def __init__(self, root):
        self.root = root
        self.root.title("拖拽设置开机自启工具")
        self.root.geometry("400x200")
        
        # 创建提示标签
        self.label = tk.Label(root, text="请将需要开机自启的程序(.exe)\n拖拽到此窗口内", 
                              justify=tk.CENTER, font=("微软雅黑", 12))
        self.label.pack(pady=40)
        
        # 绑定拖拽事件
        # windnd.hook_dropfiles 会将拖拽的文件路径列表传递给 handle_drop
        windnd.hook_dropfiles(root, func=self.handle_drop)

    def handle_drop(self, files):
        """处理拖拽事件"""
        if not files:
            return
        
        # windnd 返回的是字节串，需要解码
        # 通常Windows路径编码为 gbk 或 utf-8，尝试解码
        try:
            file_path = files.decode('gbk')
        except UnicodeDecodeError:
            try:
                file_path = files.decode('utf-8')
            except:
                messagebox.showerror("错误", "无法识别文件路径编码")
                return

        # 验证文件是否存在
        if not os.path.exists(file_path):
            messagebox.showerror("错误", "文件不存在或路径无效")
            return
            
        # 确认是否为可执行文件(可选，这里放宽限制允许任何文件)
        if not file_path.lower().endswith('.exe'):
            if not messagebox.askyesno("提示", "拖入的不是.exe文件，确定要添加吗？"):
                return

        # 添加到注册表启动项
        if self.add_to_startup(file_path):
            messagebox.showinfo("成功", f"已设置开机自启:\n{os.path.basename(file_path)}")
            self.label.config(text=f"已添加:\n{os.path.basename(file_path)}")
        else:
            messagebox.showerror("失败", "设置开机自启失败，请以管理员身份运行或检查权限")

    def add_to_startup(self, file_path):
        """将程序路径写入注册表 Run 键"""
        try:
            # 打开当前用户的 Run 键
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            # 生成一个唯一的键名，这里使用文件名作为键名
            key_name = os.path.basename(file_path).split('.')
            
            # 设置注册表值
            # 注意：如果路径包含空格，建议加上引号，但现代Windows通常能处理不带引号的路径
            # 为了稳妥，可以加上引号: f'"{file_path}"'
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, file_path)
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"注册表写入错误: {e}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoStartTool(root)
    root.mainloop()