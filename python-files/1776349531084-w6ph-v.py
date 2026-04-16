import os
import time
import tempfile
import sys

def main():
    if len(sys.argv) < 2:
        print("用法: keep_hdd_alive.exe E:")
        input("按回车退出")
        return

    drive = sys.argv[1].strip()
    if not drive.endswith(':'):
        drive += ':'

    print(f"开始保持硬盘 {drive} 活跃...")
    print("按 Ctrl+C 停止")

    try:
        while True:
            try:
                with tempfile.NamedTemporaryFile(dir=drive, delete=True) as f:
                    f.write(b'1')
                print(time.strftime("%H:%M:%S"), "已激活硬盘")
            except Exception as e:
                print("错误:", e)
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n已停止")

if __name__ == "__main__":
    main()
