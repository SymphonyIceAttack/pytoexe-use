import os
import time
import pandas as pd
import ctypes  # 用于弹窗提示，替代print，更适配EXE

def scan_c_h_files(folder_path):
    # 扫描当前目录及所有子文件夹，提取.c/.h文件信息
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.c', '.h')):
                file_path = os.path.join(root, file)
                file_name, file_ext = os.path.splitext(file)
                file_size = os.path.getsize(file_path)
                # 格式化时间
                modify_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path)))
                # 只保留核心字段，适配Excel统计
                file_list.append({
                    "文件名": file_name,
                    "后缀": file_ext[1:],
                    "完整文件名": file,
                    "文件路径": file_path,
                    "文件大小(字节)": file_size,
                    "修改时间": modify_time
                })
    return file_list

def save_to_excel(file_list):
    # 保存到Excel，固定文件名，同目录生成
    df = pd.DataFrame(file_list)
    df.to_excel("C_H文件统计.xlsx", index=False, engine="openpyxl")

if __name__ == "__main__":
    # 当前目录（EXE所在目录）作为扫描根目录
    target_folder = os.getcwd()
    file_list = scan_c_h_files(target_folder)
    
    if file_list:
        save_to_excel(file_list)
        # 弹窗提示成功，适配EXE可视化
        ctypes.windll.user32.MessageBoxW(0, "✅ 统计完成！Excel文件已生成在当前目录", "操作成功", 0)
    else:
        # 弹窗提示无相关文件
        ctypes.windll.user32.MessageBoxW(0, "⚠️ 未找到任何.c/.h文件", "提示", 0)