import os
import sys
from pathlib import Path

def is_image_file(filename):
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
    return Path(filename).suffix.lower() in image_extensions

def should_skip_folder(folder_name):
    skip_folders = {'_internal', '__pycache__', '.git', '.vscode', 'venv', 'dist', 'build'}
    return folder_name in skip_folders or folder_name.startswith('.')

def should_skip_file(filename):
    skip_files = {
        'base_library.zip', 'python311.dll', 'libcrypto-3.dll', 'VCRUNTIME140.dll',
        'select.pyd', 'unicodedata.pyd', '_bz2.pyd', '_decimal.pyd', '_hashlib.pyd',
        '_lzma.pyd', '_socket.pyd', '游戏列表生成工具.exe', '游戏列表.txt'
    }
    return filename in skip_files or filename.endswith(('.pyd', '.dll', '.exe', '.bat'))

def process_folders(root_dir):
    try:
        folders = [f for f in os.listdir(root_dir) 
                  if os.path.isdir(os.path.join(root_dir, f)) and not should_skip_folder(f)]
        
        if not folders:
            print("未找到任何游戏文件夹！")
            return
        
        print(f"找到 {len(folders)} 个游戏文件夹")
        output_file = os.path.join(root_dir, "游戏列表.txt")
        all_entries = []
        total_count = 0
        
        for folder_name in folders:
            folder_path = os.path.join(root_dir, folder_name)
            print(f"正在扫描: {folder_name}")
            non_image_files = []
            
            try:
                for file_path in Path(folder_path).rglob('*'):
                    if (file_path.is_file() and 
                        not is_image_file(file_path.name) and 
                        not should_skip_file(file_path.name)):
                        non_image_files.append(file_path.name)
            except Exception as e:
                continue
            
            for filename in non_image_files:
                total_count += 1
                sort_by = f"{total_count:03d}"
                entry = f"game: {folder_name}\nfile: {filename}\nsort-by: {sort_by}\ndeveloper: {folder_name}\ndescription: 暂无信息\n"
                all_entries.append(entry)
                print(f"  ✓ 添加: {filename}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(all_entries):
                f.write(entry)
                if i < len(all_entries) - 1:
                    f.write("\n")
        
        print(f"\n✓ 处理完成！共 {len(all_entries)} 个游戏")
        print(f"✓ 输出文件: 游戏列表.txt")
        
    except Exception as e:
        print(f"错误: {e}")

def main():
    print("=" * 50)
    print("       游戏列表生成工具 v2.0")
    print("=" * 50)
    print("功能: 自动扫描所有文件夹并生成游戏列表")
    print("支持: .sfc .smc .nds .gba .chd 等格式")
    print("=" * 50)
    input("按回车键开始扫描...")
    process_folders(os.getcwd())
    print("=" * 50)
    input("按回车键退出...")

if __name__ == "__main__":
    main()