import tkinter as tk
from tkinter import ttk, messagebox
import re

# 主窗口
root = tk.Tk()
root.title("纯币计算器")
root.geometry("460x290")
root.resizable(False, False)

# 样式美化
style = ttk.Style()
style.configure(".", font=("微软雅黑", 11))
style.configure("TButton", padding=6)

# 复制功能
def copy_text(entry_widget):
    content = entry_widget.get().strip()
    if content:
        root.clipboard_clear()
        root.clipboard_append(content)
        messagebox.showinfo("复制成功", f"已复制：{content}")
    else:
        messagebox.showwarning("提示", "框内无内容")

# 核心计算（已修正：100m = 100×1000 = 100000）
def calculate():
    try:
        # === 1. 处理纯币框：支持 80m / 100M / 50 ===
        coin_text = entry_coin.get().strip().upper()
        match = re.match(r'(\d+(?:\.\d+)?)M?', coin_text)
        if not match:
            messagebox.showerror("错误", "纯币格式错误，示例：80m、100M、50")
            return
        
        # 关键：提取数字 ×1000
        coin_num = float(match.group(1))
        total_coin = coin_num * 1000  # 100m = 100000

        # === 2. 比例框 ===
        rate = float(entry_rate.get().strip())
        if rate <= 0:
            messagebox.showerror("错误", "比例必须大于0")
            return

        # === 3. 计算结果（取整）===
        amount = int(total_coin / rate)

        # 输出到金额框
        entry_result.delete(0, tk.END)
        entry_result.insert(0, str(amount))

    except ValueError:
        messagebox.showerror("错误", "请输入有效数字")

# ------------------- 界面布局 -------------------
# 纯币框
frame1 = ttk.Frame(root)
frame1.pack(pady=14, fill=tk.X, padx=32)
btn1 = ttk.Button(frame1, text="复制", width=6, command=lambda: copy_text(entry_coin))
btn1.pack(side=tk.LEFT, padx=6)
ttk.Label(frame1, text="纯币：").pack(side=tk.LEFT)
entry_coin = ttk.Entry(frame1, font=("微软雅黑", 12))
entry_coin.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

# 比例框
frame2 = ttk.Frame(root)
frame2.pack(pady=14, fill=tk.X, padx=32)
btn2 = ttk.Button(frame2, text="复制", width=6, command=lambda: copy_text(entry_rate))
btn2.pack(side=tk.LEFT, padx=6)
ttk.Label(frame2, text="比例：").pack(side=tk.LEFT)
entry_rate = ttk.Entry(frame2, font=("微软雅黑", 12))
entry_rate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

# 金额框
frame3 = ttk.Frame(root)
frame3.pack(pady=14, fill=tk.X, padx=32)
btn3 = ttk.Button(frame3, text="复制", width=6, command=lambda: copy_text(entry_result))
btn3.pack(side=tk.LEFT, padx=6)
ttk.Label(frame3, text="金额：").pack(side=tk.LEFT)
entry_result = ttk.Entry(frame3, font=("微软雅黑", 12))
entry_result.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

# 计算按钮
btn_calc = ttk.Button(root, text="计算", command=calculate)
btn_calc.pack(pady=18, ipadx=35)

root.mainloop()