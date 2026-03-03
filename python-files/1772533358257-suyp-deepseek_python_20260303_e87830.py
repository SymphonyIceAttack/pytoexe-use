import sys
import zipfile
from pathlib import Path

def extract_zip(zip_path, password, delete=False):
    zip_path = Path(zip_path)
    if not zip_path.exists() or zip_path.suffix.lower() != '.zip':
        print(f"跳过非ZIP文件或文件不存在: {zip_path}")
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(path=zip_path.parent, pwd=password.encode('utf-8'))
        print(f"✅ 解压成功: {zip_path}")
        if delete:
            zip_path.unlink()
            print(f"🗑️ 已删除原文件: {zip_path}")
    except RuntimeError as e:
        if 'password required' in str(e) or 'Bad password' in str(e):
            print(f"❌ 密码错误或需要密码: {zip_path}")
        else:
            print(f"❌ 解压失败 {zip_path}: {e}")
    except Exception as e:
        print(f"❌ 解压失败 {zip_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("请将要解压的ZIP文件或文件夹拖放到本程序上。")
        print("示例：直接拖放文件，或命令行执行：unzip_drop.exe file1.zip file2.zip")
        return

    password = "av783661"
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_dir():
            for zip_file in path.glob("*.zip"):
                extract_zip(zip_file, password, delete=True)
        elif path.is_file():
            extract_zip(path, password, delete=True)
        else:
            print(f"无效路径: {arg}")

if __name__ == "__main__":
    main()