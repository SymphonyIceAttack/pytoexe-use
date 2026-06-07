import tkinter as tk
from tkinter import ttk, messagebox

# -------------------------- 核心计算函数（CAAC考试专用）--------------------------
# 1. 基础运算
def calc_base():
    try:
        result = eval(entry_base.get())
        entry_base_res.delete(0, tk.END)
        entry_base_res.insert(0, str(result))
    except:
        messagebox.showerror("错误", "输入格式无效")

# 2. 时钟计算：时分相加
def time_add():
    try:
        h1 = int(entry_h1.get())
        m1 = int(entry_m1.get())
        h2 = int(entry_h2.get())
        m2 = int(entry_m2.get())
        total_m = h1*60 + m1 + h2*60 + m2
        h = total_m // 60
        m = total_m % 60
        entry_time_res.delete(0, tk.END)
        entry_time_res.insert(0, f"{h}时{m}分")
    except:
        messagebox.showerror("错误", "请输入整数")

# 时钟计算：时间差（大时间-小时间）
def time_sub():
    try:
        h1 = int(entry_h1.get())
        m1 = int(entry_m1.get())
        h2 = int(entry_h2.get())
        m2 = int(entry_m2.get())
        t1 = h1*60 + m1
        t2 = h2*60 + m2
        diff = abs(t1 - t2)
        h = diff // 60
        m = diff % 60
        entry_time_res.delete(0, tk.END)
        entry_time_res.insert(0, f"{h}时{m}分")
    except:
        messagebox.showerror("错误", "请输入整数")

# 时钟：时分转总分钟
def hm2min():
    try:
        h = int(entry_h1.get())
        m = int(entry_m1.get())
        res = h*60 + m
        entry_time_res.delete(0, tk.END)
        entry_time_res.insert(0, f"{res}分钟")
    except:
        messagebox.showerror("错误", "请输入整数")

# 3. 角度归一化（0-360°，航空必考）
def angle_360(angle):
    return angle % 360

# 风向/航向：磁航向→真航向（真航向=磁航向+磁偏角）
def mag2true():
    try:
        mag = float(entry_mag.get())
        dev = float(entry_dev.get())
        true = angle_360(mag + dev)
        entry_true.delete(0, tk.END)
        entry_true.insert(0, f"{true:.1f}°")
    except:
        messagebox.showerror("错误", "输入数字")

# 4. 度分秒 ↔ 十进制度（内外角/导航角度必考）
def dms2deg():
    try:
        d = int(entry_d.get())
        m = int(entry_m.get())
        s = int(entry_s.get())
        deg = d + m/60 + s/3600
        entry_deg_res.delete(0, tk.END)
        entry_deg_res.insert(0, f"{deg:.6f}°")
    except:
        messagebox.showerror("错误", "输入整数")

def deg2dms():
    try:
        deg = float(entry_deg.get())
        d = int(deg)
        m = int((deg - d)*60)
        s = (deg - d - m/60)*3600
        entry_dms_res.delete(0, tk.END)
        entry_dms_res.insert(0, f"{d}°{m}′{s:.2f}″")
    except:
        messagebox.showerror("错误", "输入数字")

# 三角形内外角计算（内角和180°，外角=180-内角）
def triangle_angle():
    try:
        a1 = float(entry_tri1.get())
        a2 = float(entry_tri2.get())
        in3 = 180 - a1 - a2
        out3 = 180 - in3
        entry_tri_in.delete(0, tk.END)
        entry_tri_out.delete(0, tk.END)
        entry_tri_in.insert(0, f"{in3:.1f}°")
        entry_tri_out.insert(0, f"{out3:.1f}°")
    except:
        messagebox.showerror("错误", "输入数字")

# -------------------------- GUI界面设计 --------------------------
root = tk.Tk()
root.title("CAAC民航考试专用计算器")
root.geometry("650x500")

# 标签样式
style = ttk.Style()
style.configure("Title.TLabel", font=("微软雅黑", 12, "bold"), foreground="blue")

# ====================== 1. 基础运算区 ======================
tk.Label(root, text="【基础四则运算】", style="Title.TLabel").grid(row=0, column=0, columnspan=2, pady=5)
entry_base = ttk.Entry(root, width=20)
entry_base.grid(row=1, column=0, padx=5)
ttk.Button(root, text="计算", command=calc_base).grid(row=1, column=1, padx=5)
entry_base_res = ttk.Entry(root, width=20)
entry_base_res.grid(row=1, column=2, padx=5)

# ====================== 2. 时钟计算区（飞行时间） ======================
tk.Label(root, text="【时钟计算】", style="Title.TLabel").grid(row=2, column=0, columnspan=2, pady=5)
tk.Label(root, text="时1:").grid(row=3, column=0)
entry_h1 = ttk.Entry(root, width=5)
entry_h1.grid(row=3, column=1)
tk.Label(root, text="分1:").grid(row=3, column=2)
entry_m1 = ttk.Entry(root, width=5)
entry_m1.grid(row=3, column=3)

tk.Label(root, text="时2:").grid(row=4, column=0)
entry_h2 = ttk.Entry(root, width=5)
entry_h2.grid(row=4, column=1)
tk.Label(root, text="分2:").grid(row=4, column=2)
entry_m2 = ttk.Entry(root, width=5)
entry_m2.grid(row=4, column=3)

ttk.Button(root, text="时间相加", command=time_add).grid(row=5, column=0, pady=2)
ttk.Button(root, text="时间差", command=time_sub).grid(row=5, column=1, pady=2)
ttk.Button(root, text="时分转分钟", command=hm2min).grid(row=5, column=2, pady=2)
entry_time_res = ttk.Entry(root, width=15)
entry_time_res.grid(row=5, column=3)

# ====================== 3. 风向/航向计算区 ======================
tk.Label(root, text="【风向/航向修正】", style="Title.TLabel").grid(row=6, column=0, columnspan=2, pady=5)
tk.Label(root, text="磁航向(°):").grid(row=7, column=0)
entry_mag = ttk.Entry(root, width=8)
entry_mag.grid(row=7, column=1)
tk.Label(root, text="磁偏角(°):").grid(row=7, column=2)
entry_dev = ttk.Entry(root, width=8)
entry_dev.grid(row=7, column=3)
ttk.Button(root, text="计算真航向", command=mag2true).grid(row=8, column=0, columnspan=2)
entry_true = ttk.Entry(root, width=12)
entry_true.grid(row=8, column=2, columnspan=2)

# ====================== 4. 内外角/角度转换区 ======================
tk.Label(root, text="【角度/内外角计算】", style="Title.TLabel").grid(row=9, column=0, columnspan=2, pady=5)
# 度分秒转十进制度
tk.Label(root, text="度:").grid(row=10, column=0)
entry_d = ttk.Entry(root, width=4)
entry_d.grid(row=10, column=1)
tk.Label(root, text="分:").grid(row=10, column=2)
entry_m = ttk.Entry(root, width=4)
entry_m.grid(row=10, column=3)
tk.Label(root, text="秒:").grid(row=10, column=4)
entry_s = ttk.Entry(root, width=4)
entry_s.grid(row=10, column=5)
ttk.Button(root, text="度分秒→度", command=dms2deg).grid(row=11, column=0, columnspan=2)
entry_deg_res = ttk.Entry(root, width=15)
entry_deg_res.grid(row=11, column=2, columnspan=3)

# 十进制度转度分秒
tk.Label(root, text="十进制度:").grid(row=12, column=0)
entry_deg = ttk.Entry(root, width=8)
entry_deg.grid(row=12, column=1)
ttk.Button(root, text="度→度分秒", command=deg2dms).grid(row=12, column=2)
entry_dms_res = ttk.Entry(root, width=15)
entry_dms_res.grid(row=12, column=3, columnspan=2)

# 三角形内外角
tk.Label(root, text="内角1:").grid(row=13, column=0)
entry_tri1 = ttk.Entry(root, width=5)
entry_tri1.grid(row=13, column=1)
tk.Label(root, text="内角2:").grid(row=13, column=2)
entry_tri2 = ttk.Entry(root, width=5)
entry_tri2.grid(row=13, column=3)
ttk.Button(root, text="计算第三内角/外角", command=triangle_angle).grid(row=14, column=0, columnspan=2)
entry_tri_in = ttk.Entry(root, width=8)
entry_tri_in.grid(row=14, column=2)
entry_tri_out = ttk.Entry(root, width=8)
entry_tri_out.grid(row=14, column=3)

# 启动界面
root.mainloop()