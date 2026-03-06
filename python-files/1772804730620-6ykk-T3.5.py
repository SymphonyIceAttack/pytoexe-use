import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# ================= 参数设置 =================
l = 2           # 初始边长
v = 0.5           # 速率
t_max = 3      # 最大模拟时间
dt = 0.001        # 微分步长（用于模拟）

# 初始位置：正三角形，A在(0,0)，B在(l,0)，C在中间上方
A0 = np.array([0.0, 0.0])
B0 = np.array([l, 0.0])
C0 = np.array([l/2, l * np.sqrt(3)/2])

# 存储轨迹（可选）
A_traj = [A0.copy()]
B_traj = [B0.copy()]
C_traj = [C0.copy()]

# ================= 数值模拟运动 =================
# 使用欧拉法模拟微分方程
t_sim = 0
A, B, C = A0.copy(), B0.copy(), C0.copy()

while t_sim < t_max:
    # 计算方向向量（单位向量）
    dir_A = (B - A) / np.linalg.norm(B - A)
    dir_B = (C - B) / np.linalg.norm(C - B)
    dir_C = (A - C) / np.linalg.norm(A - C)

    # 更新位置
    A += v * dir_A * dt
    B += v * dir_B * dt
    C += v * dir_C * dt

    # 存储
    A_traj.append(A.copy())
    B_traj.append(B.copy())
    C_traj.append(C.copy())

    t_sim += dt

# 转为数组
A_traj = np.array(A_traj)
B_traj = np.array(B_traj)
C_traj = np.array(C_traj)
times = np.arange(0, t_max + dt, dt)

# ================= 可视化设置 =================
fig, ax = plt.subplots(figsize=(8, 8))
plt.subplots_adjust(bottom=0.25)

# 初始三角形
initial_triangle = plt.Polygon([A0, B0, C0], fill=None, linestyle='--', color='gray', label='Initial Triangle')

# 初始连线
line, = ax.plot([], [], 'o-', lw=2, markersize=8)
# 轨迹（可选，可注释掉）
ax.plot(A_traj[:,0], A_traj[:,1], '--', alpha=0.5, color='blue')
ax.plot(B_traj[:,0], B_traj[:,1], '--', alpha=0.5, color='red')
ax.plot(C_traj[:,0], C_traj[:,1], '--', alpha=0.5, color='green')

ax.add_patch(initial_triangle)

# 文本显示距离
dist_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, color='red')

ax.set_xlim(-0.2, l + 0.2)
ax.set_ylim(-0.2, l + 0)
ax.set_aspect('equal')
ax.grid(True)
ax.set_title("L=2,v=0.5")
ax.legend()

# ================= 滑块 =================
ax_time = plt.axes([0.2, 0.1, 0.65, 0.03], facecolor='lightgoldenrodyellow')
slider_t = Slider(ax_time, 'Time', 0, t_max, valinit=0, valstep=dt)

# ================= 更新函数 =================
def update(val):
    t = slider_t.val
    idx = min(int(t / dt), len(times) - 1)

    A_pos = A_traj[idx]
    B_pos = B_traj[idx]
    C_pos = C_traj[idx]

    # 更新连线
    x_data = [A_pos[0], B_pos[0], C_pos[0], A_pos[0]]
    y_data = [A_pos[1], B_pos[1], C_pos[1], A_pos[1]]
    line.set_data(x_data, y_data)

    # 更新距离显示（A到B）
    dist = np.linalg.norm(B_pos - A_pos)
    dist_text.set_text(f'Distance A-B: {dist:.4f}')

    fig.canvas.draw_idle()

slider_t.on_changed(update)

# 初始化
update(0)

plt.show()
