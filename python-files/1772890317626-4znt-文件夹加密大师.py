import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import sys

class FolderEncryptor:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹加密大师")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Windows中文显示适配
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = tk.Frame(self.root, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_label = tk.Label(main_frame, text="文件夹加密大师", font=("微软雅黑", 22, "bold"), fg="#3366cc")
        title_label.pack(pady=10)
        author_label = tk.Label(main_frame, text="lmt制作", font=("微软雅黑", 10, "italic"), fg="#666")
        author_label.pack(pady=5)
        
        # 选择文件夹行
        file_frame = tk.Frame(main_frame, pady=8)
        file_frame.pack(fill=tk.X)
        
        tk.Label(file_frame, text="选择文件夹:", font=("微软雅黑", 12), width=12, anchor="w").pack(side=tk.LEFT)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(
            file_frame,
            textvariable=self.file_path_var,
            width=35,
            font=("微软雅黑", 10)
        )
        self.file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.file_entry.config(state="readonly")
        
        # 浏览按钮
        browse_btn = tk.Button(
            file_frame,
            text="浏览",
            command=self.browse_folder,
            font=("微软雅黑", 10),
            bg="#3366cc",
            fg="white",
            bd=1,
            relief="raised",
            padx=8
        )
        browse_btn.pack(side=tk.LEFT, padx=3)
        
        # 密码设置行
        pwd_frame = tk.Frame(main_frame, pady=8)
        pwd_frame.pack(fill=tk.X)
        tk.Label(pwd_frame, text="设置密码:", font=("微软雅黑", 12), width=12, anchor="w").pack(side=tk.LEFT)
        
        self.password_var = tk.StringVar()
        tk.Entry(
            pwd_frame,
            textvariable=self.password_var,
            show="*",
            width=35,
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # 确认密码行
        confirm_frame = tk.Frame(main_frame, pady=8)
        confirm_frame.pack(fill=tk.X)
        tk.Label(confirm_frame, text="确认密码:", font=("微软雅黑", 12), width=12, anchor="w").pack(side=tk.LEFT)
        
        self.confirm_var = tk.StringVar()
        tk.Entry(
            confirm_frame,
            textvariable=self.confirm_var,
            show="*",
            width=35,
            font=("微软雅黑", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # 加密按钮
        btn_frame = tk.Frame(main_frame, pady=15)
        btn_frame.pack()
        
        tk.Button(
            btn_frame,
            text="加密",
            command=self.encrypt_folder,
            font=("微软雅黑", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=28,
            height=2,
            bd=0,
            relief="flat"
        ).pack()
        
        # 状态提示
        self.status_var = tk.StringVar(value="请点击【浏览】选择文件夹")
        tk.Label(main_frame, textvariable=self.status_var, font=("微软雅黑", 10), fg="#3366cc").pack(pady=10)

    def browse_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择要加密的文件夹")
        if folder_path:
            self.file_entry.config(state="normal")
            self.file_path_var.set(folder_path)
            self.file_entry.config(state="readonly")
            self.status_var.set("已选择文件夹，可加密")
        else:
            self.status_var.set("未选择文件夹")

    def encrypt_folder(self):
        """加密核心逻辑（修复f-string反斜杠错误）"""
        folder_path = self.file_path_var.get().strip()
        pwd = self.password_var.get().strip()
        confirm_pwd = self.confirm_var.get().strip()

        # 基础校验
        if not folder_path:
            messagebox.showerror("错误", "请先选择文件夹！")
            return
        if not pwd:
            messagebox.showerror("错误", "请设置密码！")
            return
        if pwd != confirm_pwd:
            messagebox.showerror("错误", "两次密码不一致！")
            return
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "文件夹不存在！")
            self.status_var.set("加密失败")
            return

        try:
            folder_name = os.path.basename(folder_path)
            target_dir = r"C:\jiami"
            target_path = os.path.join(target_dir, folder_name)
            original_full_path = folder_path  # 保存完整原路径

            # 修复f-string反斜杠问题：提前处理路径转义
            original_path_escaped = original_full_path.replace("\\", "\\\\")

            # 权限校验
            if not os.access("C:\\", os.W_OK):
                messagebox.askyesno("权限提示", "需管理员权限操作C盘，是否继续？")
                self.status_var.set("加密失败：权限不足")
                return

            # 创建加密目录
            os.makedirs(target_dir, exist_ok=True)

            # 覆盖处理
            if os.path.exists(target_path):
                if not messagebox.askyesno("提示", "文件夹已存在，是否覆盖？"):
                    self.status_var.set("加密取消")
                    return
                shutil.rmtree(target_path, ignore_errors=True)

            # 移动文件夹
            self.status_var.set("加密中...")
            self.root.update()
            shutil.move(folder_path, target_path)

            # 生成BAT解密脚本（核心修复：解决乱码+语法错误）
            self.generate_decrypt_bat(original_full_path, original_path_escaped, folder_name, pwd)

            # 成功提示
            messagebox.showinfo("成功", "文件夹加密完成！\n原位置已生成BAT解密文件，双击即可使用")
            self.status_var.set("加密成功")
            
            # 清空密码
            self.password_var.set("")
            self.confirm_var.set("")

        except PermissionError:
            messagebox.showerror("错误", "请以管理员身份运行程序！")
            self.status_var.set("加密失败")
        except Exception as e:
            messagebox.showerror("加密失败", f"操作失败：{str(e)}")
            self.status_var.set("加密失败")

    def generate_decrypt_bat(self, original_full_path, original_path_escaped, folder_name, pwd):
        """生成无乱码、无语法错误的BAT解密脚本"""
        # 提前拼接固定路径，避免f-string内用反斜杠
        encrypted_folder = "C:\\jiami\\" + folder_name
        
        # BAT脚本内容（解决乱码+语法错误）
        bat_content = f'''@echo off
:: 强制设置命令行编码为GBK，解决中文乱码
chcp 936 >nul
title 文件夹解密器 - {folder_name}
color 0B
mode con cols=60 lines=20

echo.
echo          ==============================
echo          文件夹解密器
echo          ==============================
echo.
set "input_pwd="
set /p "input_pwd=  请输入解密密码："

:: 密码校验
if not "%input_pwd%"=="{pwd}" (
    echo.
    echo          密码错误！操作失败
    pause >nul
    exit /b 1
)

:: 定义路径（提前转义，避免f-string反斜杠错误）
set "encrypted_folder={encrypted_folder}"
set "original_folder={original_path_escaped}"

:: 检查加密文件夹是否存在
if not exist "%encrypted_folder%" (
    echo.
    echo          错误：加密文件夹不存在！
    pause >nul
    exit /b 1
)

:: 操作选择
echo.
echo          ==============================
echo          请选择操作：
echo          1 - 仅打开加密文件夹（不移回）
echo          2 - 解密文件夹（移回原位置）
echo          ==============================
echo.
set "operate_choice="
set /p "operate_choice=  请输入选择(1/2)："

:: 执行选择的操作
if "%operate_choice%"=="1" (
    echo.
    echo          正在打开加密文件夹...
    start "" "%encrypted_folder%"
    echo.
    echo          操作完成！文件夹仍保存在C:\jiami
    pause >nul
    exit /b 0
) else if "%operate_choice%"=="2" (
    echo.
    echo          即将解密到原位置：{original_full_path}
    :: 处理原位置同名文件夹
    if exist "%original_folder%" (
        echo          警告：原位置已有同名文件夹！
        choice /c YN /m "          是否覆盖(Y/N)："
        if errorlevel 2 (
            echo.
            echo          操作取消
            pause >nul
            exit /b 1
        )
        rd /s /q "%original_folder%"
    )
    :: 移动文件夹回原位置
    move "%encrypted_folder%" "%original_folder%" >nul
    if exist "%original_folder%" (
        echo.
        echo          解密成功！正在打开文件夹...
        start "" "%original_folder%"
        echo.
        echo          提示：文件夹已移回原位置
        pause >nul
        exit /b 0
    ) else (
        echo.
        echo          解密失败！移动文件夹出错
        pause >nul
        exit /b 1
    )
) else (
    echo.
    echo          无效选择！请输入1或2
    pause >nul
    exit /b 1
)
'''
        # 用GBK编码写入BAT文件（Windows批处理唯一正确编码）
        bat_save_dir = os.path.dirname(original_full_path)
        bat_save_path = os.path.join(bat_save_dir, f"{folder_name}_解密器.bat")
        with open(bat_save_path, "w", encoding="gbk") as f:
            f.write(bat_content)

# 程序入口
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = FolderEncryptor(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("启动失败", f"加密程序启动异常：{str(e)}")
