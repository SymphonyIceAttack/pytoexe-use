import os
import sys
import subprocess
import zipfile
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path

# 文件头魔数
MAGIC = {
    b'PK\x03\x04': 'zip',
    b'Rar!\x1a\x07': 'rar',
    b'7z\xbc\xaf\x27\x1c': '7z',
}

def find_7z():
    """查找 7z.exe（优先使用用户指定路径）"""
    custom_path = r"D:\学习办公\7-Zip\7z.exe"
    if Path(custom_path).exists():
        return custom_path

    # 备选路径
    common_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    for path in common_paths:
        if Path(path).exists():
            return path

    # 环境变量 PATH
    for dir in os.environ["PATH"].split(os.pathsep):
        exe = Path(dir) / "7z.exe"
        if exe.exists():
            return str(exe)
    return None

def detect_format(file_path):
    """读取文件前8字节，返回识别出的格式名（zip/rar/7z）或 None"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
        for magic, fmt in MAGIC.items():
            if header.startswith(magic):
                return fmt
    except:
        pass
    return None

def rename_to_correct_ext(file_path, correct_fmt):
    """将文件重命名为正确的扩展名，返回新路径"""
    orig = Path(file_path)
    new_path = orig.with_suffix(f'.{correct_fmt}')
    if new_path == orig:
        return orig
    if new_path.exists():
        counter = 1
        while True:
            alt = orig.with_name(f"{orig.stem}_{counter}.{correct_fmt}")
            if not alt.exists():
                new_path = alt
                break
            counter += 1
    orig.rename(new_path)
    print(f"🔁 重命名: {orig.name} -> {new_path.name}")
    return new_path

def extract_with_7z(sevenz_path, file_path, password, delete=True):
    """使用 7-Zip 解压文件"""
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False

    cmd = [sevenz_path, 'x', str(file_path), f'-o{file_path.parent}', '-y']
    if password:
        cmd.append(f'-p{password}')
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            print(f"✅ 解压成功: {file_path}")
            if delete:
                file_path.unlink()
                print(f"🗑️ 已删除原文件: {file_path}")
            return True
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            if "Wrong password" in error_msg or "Can not open encrypted archive" in error_msg:
                print(f"❌ 密码错误: {file_path}")
            else:
                print(f"❌ 解压失败 {file_path}:\n{error_msg[:200]}")
            return False
    except Exception as e:
        print(f"❌ 调用 7z 失败: {e}")
        return False

def extract_fallback(file_path, password, delete=True):
    """降级方案：使用 Python 内置 zipfile 解压（仅支持 zip）"""
    file_path = Path(file_path)
    if file_path.suffix.lower() != '.zip':
        print(f"⚠️ 无法解压 {file_path}：请安装 7-Zip 以支持更多格式")
        return False
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(path=file_path.parent, pwd=password.encode('utf-8'))
        print(f"✅ 解压成功 (内置zip): {file_path}")
        if delete:
            file_path.unlink()
            print(f"🗑️ 已删除原文件: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 解压失败 {file_path}: {e}")
        return False

def main():
    root = tk.Tk()
    root.withdraw()
    password = simpledialog.askstring("解压密码", "请输入解压密码（留空表示无密码）:", show='*')
    root.destroy()
    if password is None:
        print("已取消操作")
        return

    sevenz_path = find_7z()
    if sevenz_path:
        print(f"🔍 找到 7-Zip: {sevenz_path}")
        use_7z = True
    else:
        print("⚠️ 未找到 7-Zip，将使用内置解压（仅支持 ZIP 格式）")
        use_7z = False

    if len(sys.argv) < 2:
        print("请将要解压的文件或文件夹拖放到本程序上。")
        return

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"无效路径: {arg}")
            continue

        if path.is_dir():
            for item in path.rglob('*'):
                if item.is_file():
                    fmt = detect_format(item)
                    if fmt:
                        if use_7z:
                            extract_with_7z(sevenz_path, item, password, delete=True)
                        else:
                            extract_fallback(item, password, delete=True)
        else:
            fmt = detect_format(path)
            if fmt:
                if use_7z:
                    extract_with_7z(sevenz_path, path, password, delete=True)
                else:
                    extract_fallback(path, password, delete=True)
            else:
                print(f"跳过非压缩文件: {path}")

if __name__ == "__main__":
    main()