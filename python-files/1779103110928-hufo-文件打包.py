import os
import shutil
import pandas as pd
from datetime import datetime
import sys

def resource_path(relative_path):
    """ 获取资源的绝对路径，用于 PyInstaller 打包后的临时目录 """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def classify_files_with_log():
    # 自动获取 exe 所在的目录作为工作目录
    source_folder = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(source_folder, "list.xlsx")

    if not os.path.exists(excel_path):
        print(f"❌ 错误：未在同目录下找到 list.xlsx 文件！")
        input("按 Enter 键退出...")
        return

    try:
        df = pd.read_excel(excel_path, usecols=[0, 1]) 
        df.columns = ['base_name', 'target_folder']
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        input("按 Enter 键退出...")
        return

    df['base_name'] = df['base_name'].astype(str).str.strip()
    df['target_folder'] = df['target_folder'].astype(str).str.strip()
    df = df.dropna(subset=['base_name', 'target_folder'])

    log_file_path = os.path.join(source_folder, f"分类日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    log_data = []

    print(f"📄 读取到 {len(df)} 条指令，开始处理...")

    all_files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]

    for index, row in df.iterrows():
        base_name = row['base_name']
        target_folder_name = row['target_folder']
        
        matched_files = [f for f in all_files if os.path.splitext(f)[0] == base_name]

        if not matched_files:
            log_data.append([datetime.now(), base_name, "未找到", target_folder_name, "失败：未找到文件"])
            print(f"⚠️  未找到: [{base_name}]")
            continue

        for real_file in matched_files:
            source_file_path = os.path.join(source_folder, real_file)
            target_folder_path = os.path.join(source_folder, target_folder_name)
            
            try:
                if not os.path.exists(target_folder_path):
                    os.makedirs(target_folder_path)
                shutil.move(source_file_path, os.path.join(target_folder_path, real_file))
                status = "成功"
                print(f"✅ 成功: {real_file} -> {target_folder_name}")
            except Exception as e:
                status = f"失败：{str(e)}"
                print(f"❌ 失败: {real_file}")

            log_data.append([datetime.now(), base_name, real_file, target_folder_name, status])

    if log_data:
        import csv
        with open(log_file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["时间", "Excel文件名", "实际文件", "目标文件夹", "状态"])
            writer.writerows(log_data)
        print(f"\n📊 日志已保存至: {log_file_path}")
    
    print("\n🎉 任务完成！")
    input("按 Enter 键退出...")

if __name__ == "__main__":
    classify_files_with_log()