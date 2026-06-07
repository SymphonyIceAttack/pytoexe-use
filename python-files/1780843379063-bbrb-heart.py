import tkinter as tk
import tkinter.messagebox
import random
from math import sin, cos, pi, log
from tkinter.constants import *

# 设置窗口的宽度和高度
width = 888
height = 500
# 设置爱心的中心点坐标
heartx = width / 2
hearty = height / 2
# 设置爱心图案的缩放比例
side = 11
# 设置爱心的颜色
heartcolor = "red"
# 设置想要显示的文字
word = "I Love You!"

class Heart:
    def __init__(self, generate_frame=20):
        self._points = set()  # 原始爱心坐标集合
        self._edge_diffusion_points = set()  # 边缘扩散效果点坐标集合
        self._center_diffusion_points = set()  # 中心扩散效果点坐标集合
        self.all_points = {
   }  # 每帧动态点坐标
        self.build(2000)  # 生成爱心图案的基础点
        self.random_halo = 1000  # 随机光环效果参数
        self.generate_frame = generate_frame  # 生成的帧数
        for frame in range(generate_frame):
            self.calc(frame)  # 计算每一帧的动态点坐标

    def build(self, number):
        # 生成爱心的基础点
        for _ in range(number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t)
            self._points.add((x, y))
            # 为每个基础点生成边缘扩散效果点
        for _x, _y in list(self._points):
            for _ in range(3):
                x, y = scatter_inside(_x, _y, 0.05)
                self._edge_diffusion_points.add((x, y))
                # 为爱心生成中心扩散效果点
        point_list = list(self._points)
        for _ in range(4000):
            x, y = random.choice(point_list)
            x, y = scatter_inside(x, y, 0.17)
            self._center_diffusion_points.add((x, y))

    @staticmethod
    def calc_position(x, y, ratio):
        # 计算点的动态位置
        force = 1 / (((x - heartx) ** 2 + (y - hearty) ** 2) ** 0.520)
        dx = ratio * force * (x - heartx) + random.randint(-1, 1)
        dy = ratio * force * (y - hearty) + random.randint(-1, 1)
        return x - dx, y - dy

    def calc(self, generate_frame):
        # 计算每一帧的动态点
        ratio = 10 * curve(generate_frame / 10 * pi)
        halo_radius = int(4 + 6 * (1 + curve(generate_frame / 10 * pi)))
        halo_number = int(3000 + 4000 * abs(curve(generate_frame / 10 * pi) ** 2))
        all_points = []
        heart_halo_point = set()
        # 生成光环效果点
        for _ in range(halo_number):
            t = random.uniform(0, 2 * pi)
            x, y = heart_function(t, shrink_ratio=11.6)
            x, y = shrink(x, y, halo_radius)
            if (x, y) not in heart_halo_point:
                heart_halo_point.add((x, y))
                x += random.randint(-14, 14)
                y += random.randint(-14, 14)
                size = random.choice((1, 2, 2))
                all_points.append((x, y, size))
                # 处理原始点、边缘扩散点、中心扩散点的动态位置
        for x, y in self._points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 3)
            all_points.append((x, y, size))
        for x, y in self._edge_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))
        for x, y in self._center_diffusion_points:
            x, y = self.calc_position(x, y, ratio)
            size = random.randint(1, 2)
            all_points.append((x, y, size))
        self.all_points[generate_frame] = all_points

    def render(self, render_canvas, render_frame):
        # 渲染每一帧的动态点到画布上
        for x, y, size in self.all_points[render_frame % self.generate_frame]:
            render_canvas.create_rectangle(x, y, x + size, y + size, width=0, fill=heartcolor)

        # 爱心图案的数学函数

def heart_function(t, shrink_ratio: float = side):
    x = 16 * (sin(t) ** 3)
    y = -(13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t))
    x *= shrink_ratio
    y *= shrink_ratio
    x += heartx
    y += hearty
    return int(x), int(y)

# 生成边缘扩散效果点的函数
def scatter_inside(x, y, beta=0.15):
    ratio_x = - beta * log(random.random())
    ratio_y = - beta * log(random.random())
    dx = ratio_x * (x - heartx)
    dy = ratio_y * (y - hearty)
    return x - dx, y - dy

# 生成中心扩散效果点的函数
def shrink(x, y, ratio):
    force = -1 / (((x - heartx) ** 2 + (y - hearty) ** 2) ** 0.6)
    dx = ratio * force * (x - heartx)
    dy = ratio * force * (y - hearty)
    return x - dx, y - dy

# 生成光环效果点的辅助函数
def curve(p):
    return 2 * (2 * sin(4 * p)) / (2 * pi)

# 动态渲染函数
def draw(main: tk.Tk, render_canvas: tk.Canvas, render_heart: Heart, render_frame=0):
    render_canvas.delete('all')
    render_heart.render(render_canvas, render_frame)
    main.after(160, draw, main, render_canvas, render_heart, render_frame + 1)

# 显示爱心图案的函数
def love():
    root = tk.Tk()
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    x = (screenwidth - width) // 2
    y = (screenheight - height) // 2 - 66
    root.geometry("%dx%d+%d+%d" % (width, height, x, y))
    root.title("❤")
    canvas = tk.Canvas(root, bg="black", width=width, height=height)
    canvas.pack()
    heart = Heart()
    draw(root, canvas, heart)
    tk.Label(root, text=word, bg="black", fg="cyan", font="Helvetic 25 bold").place(relx=.5, rely=.5, anchor=CENTER)
    root.mainloop()

# 主函数
if __name__ == '__main__':
    root = tk.Tk()
    root.title('❤')
    root.resizable(0, 0)
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    widths = 300
    heights = 100
    x = (screenwidth - widths) / 2
    y = (screenheight - heights) / 2 - 66
    root.geometry('%dx%d+%d+%d' % (widths, heights, x, y))
    tk.Label(root, text='亲爱的，做我女朋友好吗？', width=37, font=('宋体', 12)).place(x=0, y=10)

    def OK():  # 定义一个名为OK的函数，用于处理用户点击“好哦”按钮的事件
        root.destroy()  # 关闭当前的窗口
        love()  # 调用love函数，假设这个函数用于显示跳动的爱心

    def NO():  # 定义一个名为NO的函数，用于处理用户点击“不要”按钮的事件
        tk.messagebox.showwarning('❤', '再给你一次机会！')  # 显示一个警告消息框

    def closeWindow():  # 定义一个名为closeWindow的函数，用于处理用户尝试关闭窗口的事件
        tk.messagebox.showwarning('❤', '逃避是没有用的哦')  # 显示一个警告消息框

    # 创建一个按钮
    tk.Button(root, text='好哦', width=5, height=1, command=OK).place(x=80,y=50)
    # 创建另一个按钮
    tk.Button(root, text='不要', width=5, height=1, command=NO).place(x=160,y=50)
    root.protocol('WM_DELETE_WINDOW', closeWindow)  # 绑定关闭窗口的事件到closeWindow函数
    root.mainloop()  # 进入Tkinter的主事件循环，等待用户事件。