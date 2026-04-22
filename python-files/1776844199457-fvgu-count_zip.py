import zipfile
import os

current_dir = os.getcwd()
total = 0
zip_num = 0

print("="*60)
print("【当前目录 ZIP 内部文件统计工具】")
print("只统计文件，不统计文件夹 | 安全只读不解压")
print("="*60)

for name in os.listdir(current_dir):
    if name.lower().endswith('.zip'):
        zip_num += 1
        try:
            with zipfile.ZipFile(name,'r') as z:
                items = z.namelist()
                files = [f for f in items if not f.endswith('/')]
                cnt = len(files)
                total += cnt
                print(f"{name:<25} 内部文件数量：{cnt}")
        except Exception as e:
            print(f"{name:<25} 读取失败：{e}")

print("="*60)
print(f"扫描完成！")
print(f"总共找到 ZIP 压缩包：{zip_num} 个")
print(f"所有压缩包内部合计文件总数：{total} 个")
print("="*60)
input("\n按回车键退出...")