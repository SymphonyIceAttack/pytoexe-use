import tkinter as tk
from tkinter import Canvas
import math

# 创建主窗口
root = tk.Tk()
root.title("❤ 送给霜霜 ❤")
root.geometry("500x600")
root.configure(bg='#ffe6f0')

# 创建画布
canvas = Canvas(root, width=500, height=500, bg='#ffe6f0', highlightthickness=0)
canvas.pack()

# 绘制粉色爱心函数
def draw_heart(canvas, x, y, size, color, outline_color=None, width=2):
    """使用参数方程绘制爱心"""
    points = []
    # 生成爱心轮廓点
    for i in range(100):
        t = (i / 100.0) * 2 * math.pi
        # 爱心参数方程
        hx = 16 * math.sin(t) ** 3
        hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
        
        px = x + hx * size
        py = y + hy * size
        points.extend([px, py])
    
    canvas.create_polygon(points, fill=color, outline=outline_color if outline_color else color, width=width, smooth=True)

draw_heart(canvas, 252, 252, 8, '#ff69b4', '#ff1493', 3)
draw_heart(canvas, 250, 250, 8, '#ff69b4', '#ff1493', 3)
draw_heart(canvas, 250, 255, 6.5, '#ffb6c1', '#ff69b4', 2)
draw_heart(canvas, 250, 260, 5, '#ffc0cb', '#ffb6c1', 1)

sparkles = [
    (180, 180, 5), (320, 180, 4), (150, 250, 3), 
    (350, 250, 3), (200, 320, 4), (300, 320, 5),
    (250, 150, 4), (180, 280, 3), (320, 280, 3)
]

for sx, sy, ss in sparkles:
    canvas.create_oval(sx-ss, sy-ss, sx+ss, sy+ss, fill='white', outline='#ff69b4', width=1)

# 添加文字标签
label = tk.Label(
    root, 
    text="我爱霜霜", 
    font=("微软雅黑", 36, "bold"),
    fg='#ff1493',
    bg='#ffe6f0'
)
label.pack(pady=20)

sub_label = tk.Label(
    root,
    text="❤ 永远爱你 ❤",
    font=("微软雅黑", 14),
    fg='#ff69b4',
    bg='#ffe6f0'
)
sub_label.pack()

root.mainloop()
