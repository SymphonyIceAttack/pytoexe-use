import tkinter as tk
from tkinter import messagebox


class UnClosableWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("无法关闭窗口")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tips = '我是小丑'

        # 设置窗口大小和位置
        self.root.geometry("400x200+500+300")

        # 添加标签
        label = tk.Label(self.root, text="输入下面的内容，否则别想关掉我", font=("Arial", 14))
        label.pack(pady=20)

        # 添加输入框
        self.entry = tk.Entry(self.root, font=("Arial", 12), width=30)
        self.entry.pack(pady=10)

        # 添加提示标签
        hint_label = tk.Label(self.root, text=f"请输入'{self.tips}'来关闭窗口", font=("Arial", 10))
        hint_label.pack(pady=5)

        # 添加按钮
        button = tk.Button(self.root, text="尝试关闭", command=self.on_close)
        button.pack(pady=10)

        # 禁止使用Alt+F4等系统快捷键
        self.root.bind("<Alt-F4>", lambda e: "break")

    def on_close(self):
        # 检查输入内容
        if self.entry.get().strip() == self.tips:
            self.root.destroy()
        else:
            messagebox.showwarning("错误", "请输入正确的关闭密码！")
            self.root.focus_force()  # 强制窗口获取焦点
            self.entry.focus_set()  # 将焦点设置到输入框

    def run(self):
        self.root.mainloop()


# 创建并运行窗口
if __name__ == "__main__":
    window = UnClosableWindow()
    window.run()