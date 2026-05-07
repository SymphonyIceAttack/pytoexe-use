import tkinter as tk
from tkinter import messagebox

def main():
    # 创建主窗口
    root = tk.Tk()
    root.title("工程天数计算器")
    root.geometry("450x350")  # 窗口大小和C版本一致
    root.resizable(False, False)  # 禁止拉伸、最大化，和原程序一致

    # ===================== 标题标签 =====================
    title_label = tk.Label(
        root,
        text="工程天数计算器",
        font=("微软雅黑", 14, "bold")
    )
    title_label.place(x=100, y=20, width=220, height=40)

    # ===================== 甲单独天数 =====================
    label_jia = tk.Label(root, text="甲单独完成天数：", font=("微软雅黑", 10))
    label_jia.place(x=50, y=80, width=150, height=25)

    entry_jia = tk.Entry(root, font=("微软雅黑", 10))
    entry_jia.place(x=220, y=80, width=180, height=25)

    # ===================== 乙单独天数 =====================
    label_yi = tk.Label(root, text="乙单独完成天数：", font=("微软雅黑", 10))
    label_yi.place(x=50, y=130, width=150, height=25)

    entry_yi = tk.Entry(root, font=("微软雅黑", 10))
    entry_yi.place(x=220, y=130, width=180, height=25)

    # ===================== 计算功能 =====================
    def calc_days():
        try:
            jia = float(entry_jia.get().strip())
            yi = float(entry_yi.get().strip())

            # 输入合法性检查
            if jia <= 0 or yi <= 0:
                messagebox.showerror("输入错误", "请输入有效的正数天数！")
                return

            # 核心计算公式：和C语言完全一致
            days = (jia * yi) / (jia + yi)
            messagebox.showinfo("计算结果", f"两人合作需要：{days:.2f} 天完成")

        except ValueError:
            messagebox.showerror("输入错误", "请输入数字！")

    # ===================== 清除功能 =====================
    def clear_text():
        entry_jia.delete(0, tk.END)
        entry_yi.delete(0, tk.END)

    # ===================== 按钮 =====================
    btn_calc = tk.Button(
        root,
        text="计算合作天数",
        font=("微软雅黑", 10, "bold"),
        command=calc_days
    )
    btn_calc.place(x=80, y=200, width=130, height=40)

    btn_clear = tk.Button(
        root,
        text="清除",
        font=("微软雅黑", 10),
        command=clear_text
    )
    btn_clear.place(x=240, y=200, width=130, height=40)

    # 主消息循环（对应C语言的GetMessage循环）
    root.mainloop()

if __name__ == "__main__":
    main()