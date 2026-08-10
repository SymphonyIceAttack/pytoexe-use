import time
import ctypes
import subprocess

def lock_screen():
    try:
        ctypes.windll.user32.LockWorkStation()
        print("屏幕已锁定")
    except:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            print("屏幕已锁定")
        except:
            print("锁屏失败")

def main():
    print("=" * 30)
    print("计时锁屏程序")
    print("=" * 30)
    
    inp = input("请输入时间（例如: 1.30 或 0.45）: ")
    
    if "." in inp:
        parts = inp.split(".")
        minutes = int(parts[0])
        seconds = int(parts[1])
    else:
        minutes = int(inp)
        seconds = 0
    
    total = minutes * 60 + seconds + 5
    
    if minutes > 0:
        print(f"开始计时 {minutes}分{seconds:02d}秒 + 5秒...")
    else:
        print(f"开始计时 {seconds}秒 + 5秒...")
    
    for i in range(total, 0, -1):
        m = i // 60
        s = i % 60
        print(f"\r剩余时间: {m:02d}:{s:02d}", end="")
        time.sleep(1)
    
    print("\n时间到！正在锁屏...")
    lock_screen()

if __name__ == "__main__":
    main()