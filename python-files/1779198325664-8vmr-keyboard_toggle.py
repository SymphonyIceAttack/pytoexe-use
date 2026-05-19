
import os
import ctypes
from tkinter import Tk, messagebox

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 自动请求管理员权限
if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        "python",
        __file__,
        None,
        1
    )
    raise SystemExit

print("=" * 40)
print(" 键盘服务切换工具 ")
print("=" * 40)
print("Y -> 禁用键盘")
print("N -> 恢复键盘")
print("=" * 40)

choice = input("请输入选项(Y/N)：").strip().upper()

if choice == "Y":
    os.system("sc config i8042prt start= disabled")
    print("已设置为禁用")

elif choice == "N":
    os.system("sc config i8042prt start= auto")
    print("已恢复自动启动")

else:
    print("输入错误")
    input("按回车退出...")
    raise SystemExit

root = Tk()
root.withdraw()

restart = messagebox.askyesno(
    "重启提示",
    "设置已完成，是否立即重启电脑？"
)

if restart:
    os.system("shutdown /r /t 0")
