import os
import string
import subprocess
import ctypes
import time

def run_wait_and_delete():
    # 列表用于存放元组：(进程对象, exe文件的完整路径)
    launched_processes = [] 

    # 1. 遍历 A-Z 所有可能的盘符
    for drive_letter in string.ascii_uppercase:
        drive_path = f"{drive_letter}:\\"
        
        if os.path.exists(drive_path):
            # 调用 Windows API 获取驱动器类型，3 代表本地固定磁盘
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
            
            # 只处理本地固定分区，自动排除U盘、光驱等
            if drive_type == 3:
                for_folder = os.path.join(drive_path, "FOR")
                # 检查当前分区根目录下是否存在 FOR 文件夹
                if os.path.exists(for_folder) and os.path.isdir(for_folder):
                    # 遍历 FOR 文件夹内的所有文件
                    for file_name in os.listdir(for_folder):
                        if file_name.lower().endswith('.exe'):
                            exe_path = os.path.join(for_folder, file_name)
                            try:
                                # 启动 exe 文件
                                process = subprocess.Popen([exe_path])
                                # 将进程对象和对应的文件路径一起存入列表
                                launched_processes.append((process, exe_path))
                            except Exception as e:
                                print(f"启动程序 {exe_path} 失败: {e}")

    # 2. 等待所有启动的 EXE 进程关闭，并在关闭后删除文件
    while launched_processes:
        time.sleep(1) # 每隔 1 秒检查一次
        for proc, path in launched_processes[:]:
            # poll() 返回不为 None 表示进程已经结束
            if proc.poll() is not None: 
                try:
                    # 进程结束后，执行删除操作
                    os.remove(path)
                    print(f"程序已退出，文件已删除: {path}")
                except Exception as e:
                    print(f"删除文件 {path} 失败: {e}")
                
                # 无论删除是否成功，都将该任务从监控列表中移除
                launched_processes.remove((proc, path))

if __name__ == "__main__":
    run_wait_and_delete()