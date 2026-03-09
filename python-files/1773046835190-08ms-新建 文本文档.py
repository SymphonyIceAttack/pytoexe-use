import tkinter as tk

# 创建主窗口
root = tk.Tk()
root.title("CAD铝建材快捷键悬浮窗")
root.geometry("220x350")  # 窗口尺寸
root.attributes('-topmost', True)  # 永久置顶
root.attributes('-alpha', 0.75)  # 75%透明度
root.configure(bg='#1e1e2e')  # 深色护眼背景
root.resizable(False, False)  # 禁止缩放

# 快捷键列表（铝建材核心）
shortcuts = [
    ("L", "直线（型材边框）"),
    ("PL", "多段线（型材截面）"),
    ("REC", "矩形（方管）"),
    ("C", "圆（螺丝孔）"),
    ("O", "偏移（壁厚）| M=多重偏移"),
    ("TR", "修剪 | 空格2下=全图修剪"),
    ("CO", "复制 | M=多重复制"),
    ("MI", "镜像（对称型材）"),
    ("F", "圆角 | F+R=改半径"),
    ("AR", "阵列（批量排孔/格栅）"),
    ("MA", "格式刷（统一属性）"),
    ("LA", "图层管理器"),
    ("Ctrl+1", "批量改属性"),
    ("QSELECT", "按条件批量选择"),
    ("F3/F8", "捕捉 / 正交")
]

# 添加标题
title = tk.Label(
    root, text="🎯 铝建材CAD快捷键",
    bg='#1e1e2e', fg='#89d1ff', font=("微软雅黑", 11, "bold")
)
title.pack(pady=8)

# 循环添加快捷键条目
for key, desc in shortcuts:
    # 快捷键按键（高亮）
    key_label = tk.Label(
        root, text=key,
        bg='#1e1e2e', fg='#ffb86c', font=("微软雅黑", 10, "bold"),
        width=8, anchor='w'
    )
    # 快捷键说明
    desc_label = tk.Label(
        root, text=desc,
        bg='#1e1e2e', fg='#ffffff', font=("微软雅黑", 9),
        anchor='w'
    )
    key_label.pack(padx=10, pady=1, anchor='w')
    desc_label.pack(padx=10, pady=0, anchor='w')

# 启动窗口
root.mainloop()