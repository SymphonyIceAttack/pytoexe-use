import tkinter as tk
import random
import threading
import time


def dow():
    window = tk.Tk()
    window.title('你是憨憨')
    window.geometry("200x50" + "+" + str(random.randrange(0, window.winfo_screenwidth())) + "+" + str(random.randrange(0, window.winfo_screenheight())))
    tk.Label(window,
             text='你是个SB！',  # 标签的文字
             bg='Red',  # 背景颜色
             font=('楷体', 17),  # 字体和字体大小
             width=20, height=2  # 标签长宽
             ).pack()  # 固定窗口位置
    window.mainloop()


threads = []
# while True:  #这句为死循环，无限弹窗
for i in range(500):  # 需要的弹框数量
    t = threading.Thread(target=dow)
    threads.append(t)
    time.sleep(0.1)
    threads[i].start()
