# build_exe.py - 打包配置文件
import PyInstaller.__main__
import os
import sys

# 打包参数配置
args = [
    'anti_control_tool.py',   # 主程序文件
    '--name=杨羡之极域反控工具箱',  # 生成的 EXE 名称
    '--onefile',              # 打包为单个文件
    '--windowed',             # 不显示控制台窗口
    '--clean',                # 清理临时文件
    '--noconfirm',            # 覆盖时不确认
    '--icon=icon.ico',       # 程序图标（可选）
    
    # 添加数据文件（图片、配置文件等）
    '--add-data=background.jpg;.',  # Windows 用分号
    # '--add-data=background.jpg:.',  # Linux/macOS 用冒号
    
    # 添加额外模块
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=PIL._imagingtk',
    '--hidden-import=PIL._imaging',
    
    # UPX 压缩（可选，减小体积）
    '--upx-dir=upx',
    
    # 版本信息
    '--version-file=version.txt',  # 需要先创建
]

PyInstaller.__main__.run(args)
