import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys

# 第一个游戏路径
GAME_EXE_1 = os.path.join("BattleZone-3", "Battlezone-3.exe")
# 第二个游戏路径（根据需要修改）
GAME_EXE_2 = os.path.join("Computer", "Computer.exe")

def launch_game1():
    try:
        if not os.path.exists(GAME_EXE_1):
            messagebox.showerror("错误", f"找不到游戏文件：{GAME_EXE_1}")
            return
        subprocess.Popen([GAME_EXE_1], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        messagebox.showerror("启动失败", str(e))

def launch_game2():
    try:
        if not os.path.exists(GAME_EXE_2):
            messagebox.showerror("错误", f"找不到游戏文件：{GAME_EXE_2}")
            return
        subprocess.Popen([GAME_EXE_2], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        messagebox.showerror("启动失败", str(e))

# 创建窗口
root = tk.Tk()
root.title("游戏启动器")
root.geometry("500x300")
root.resizable(False, False)

# 两个按钮垂直排列
btn1 = tk.Button(root, text="启动主游戏", font=("Arial", 14), command=launch_game1)
btn1.pack(pady=10)

btn2 = tk.Button(root, text="启动电脑", font=("Arial", 14), command=launch_game2)
btn2.pack(pady=10)

root.mainloop()