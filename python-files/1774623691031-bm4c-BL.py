import sys
import time

# 可以在这里添加一个全局延时，让程序启动后停顿一下（可选）
time.sleep(1)
def printf(s):
    import time
    for i in s:    #显示动画
        print(i,end="")
        time.sleep(0.02)
    print("",end="\n")
def dism_progress(prefix, total_bytes=40960, duration_sec=2.0):  # 修改此处：从 0.077 改为 2.0
    """模拟 Dism 风格的进度条，在指定时间内从 0% 更新到 100%"""
    bar_length = 50
    start = time.time()
    percent = 0
    while percent < 100:
        elapsed = time.time() - start
        percent = min(100, int((elapsed / duration_sec) * 100))
        filled_length = int(bar_length * percent / 100)
        bar = '=' * filled_length + ' ' * (bar_length - filled_length)
        sys.stdout.write(f"\r{prefix} [{bar}] {percent}%")
        sys.stdout.flush()
        time.sleep(0.01)  # 刷新频率不变，但总时间变长，进度更新会更慢
    sys.stdout.write(f"\r{prefix} 100% 完成\n")
    sys.stdout.write(f"linuxloader_unlock.efi: 1 file pushed, 0 skipped. 0.5 MB/s (40960 bytes in {duration_sec:.3f}s)\n")

def main():
    print("设备已连接")
    time.sleep(0.2)            # 适当增加延时
    print("检查解锁状态…")
    time.sleep(0.1)
    print("临时宽容SELinux…")
    print("等待设备连接…")
    time.sleep(0.2)
    print("设备已连接")
    print("检查SELinux状态…")
    time.sleep(0.1)
    print("写入解锁程序…")
    
    # 模拟动态进度推送（使用新的持续时间）
    dism_progress("正在推送 linuxloader_unlock.efi", total_bytes=40960, duration_sec=2.0)
    
    print("重启到fastboot…")
    time.sleep(0.5)
    print("等待设备连接…")
    printf("1145cffd fastboot")
    print("设备已连接")
    print("检查解锁状态…")
    print("恭喜！解锁成功")
    print("清空efisp分区…")
    print("Sending ‘efisp’ (40 KB) OKAY [ 0.002s]")
    time.sleep(0.01)
    print("Writing ‘efisp’ OKAY [ 0.049s]")
    time.sleep(0.01)
    print("Finished. Total time: 0.088s")
    time.sleep(0.01)
    print("重启并自动恢复出厂…")
    time.sleep(0.01)
    print("Sending ‘misc’ (8 KB) OKAY [ 0.001s]")
    time.sleep(0.01)
    print("Writing ‘misc’ OKAY [ 0.049s]")
    time.sleep(0.01)
    print("Finished. Total time: 0.093s")
    time.sleep(0.01)
    print("Rebooting OKAY [ 0.001s]")
    time.sleep(0.01)
    print("Finished. Total time: 0.004s")
    print("全部完成。按任意键退出…")

if __name__ == "__main__":
    main()
    input()  # 等待用户按键
