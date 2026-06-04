import os
import sys
import win32com.client

def create_shortcut(target_path, shortcut_path):
    """创建快捷方式"""
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path  # 目标程序路径
    shortcut.WorkingDirectory = os.path.dirname(target_path)  # 工作目录
    shortcut.Save()

if __name__ == "__main__":
    # 获取拖入的文件路径（从命令行参数获取）
    if len(sys.argv) < 2:
        print("请将exe程序拖到本程序上")
        input("按回车键退出...")
        sys.exit(1)
    
    exe_path = sys.argv[1]
    if not (os.path.isfile(exe_path) and exe_path.endswith(".exe")):
        print("请拖入有效的exe文件")
        input("按回车键退出...")
        sys.exit(1)
    
    # 获取当前用户的启动文件夹路径
    startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    
    # 快捷方式名称（用exe文件名）
    exe_name = os.path.splitext(os.path.basename(exe_path))[0]
    shortcut_name = f"{exe_name}.lnk"
    shortcut_path = os.path.join(startup_folder, shortcut_name)
    
    # 创建快捷方式
    try:
        create_shortcut(exe_path, shortcut...