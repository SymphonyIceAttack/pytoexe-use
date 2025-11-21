import os
import shutil

# 获取当前脚本所在目录
folder = os.path.dirname(os.path.abspath(__file__))
backup_folder = os.path.join(folder, "backup_pdb")

# 创建备份文件夹
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)
    print(f"已创建备份文件夹：{backup_folder}")
else:
    print(f"备份文件夹已存在：{backup_folder}")

# 批量处理PDB文件
count = 0
for filename in os.listdir(folder):
    if filename.lower().endswith(".pdb"):
        file_path = os.path.join(folder, filename)
        backup_path = os.path.join(backup_folder, filename)

        # 备份原始文件
        shutil.copy2(file_path, backup_path)

        # 读取并删除ENDMDL行
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [line for line in lines if "ENDMDL" not in line]
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        count += 1
        print(f"已处理文件：{filename}")

if count == 0:
    print("未找到任何 .pdb 文件。")
else:
    print(f"\n处理完成，共修改 {count} 个文件。")
    print(f"所有原始文件已备份至：{backup_folder}")

input("\n按回车键退出...")
