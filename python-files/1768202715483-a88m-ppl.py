import tkinter as tk
import threading
import time

def 烦死你():
    while True:
        窗口 = tk.Tk()
        窗口.title("惊喜")
        tk.Label(窗口, text="烦死你！！！", font=("微软雅黑", 20)).pack()
        # 他妈的不让关
        窗口.protocol("WM_DELETE_WINDOW", lambda: None)
        窗口.after(1000, 窗口.destroy)
        窗口.mainloop()
        time.sleep(0.5)  # 歇半秒继续干

# 开个线程免得卡住主程序
threading.Thread(target=烦死你, daemon=True).start()

print("🎉 开始烦人模式！按Ctrl+C都停不下来，哈哈哈！")
