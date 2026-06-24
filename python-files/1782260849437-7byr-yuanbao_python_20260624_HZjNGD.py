import tkinter as tk

def close_window():
    root.destroy()

# 创建主窗口
root = tk.Tk()
root.title("示例窗口")
root.geometry("300x150")

# 创建一个按钮
btn = tk.Button(
    root,
    text="关闭窗口",
    command=close_window,
    width=15,
    height=2
)
btn.pack(expand=True)

# 运行主循环
root.mainloop()