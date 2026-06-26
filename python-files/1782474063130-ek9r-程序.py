
import random
import math
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.lines import Line2D

# 预设参数
DEFAULT_D = 1.0       # 平行线间距
DEFAULT_L = 0.8       # 针长 (需满足 L <= d)
DEFAULT_N = 500       # 投针总数

class BuffonExperiment:
    def __init__(self):
        # 创建图形和子图
        self.fig = plt.figure(figsize=(12, 6))
        self.ax1 = self.fig.add_axes([0.05, 0.15, 0.55, 0.80])  # 针分布图
        self.ax2 = self.fig.add_axes([0.65, 0.55, 0.30, 0.35])  # π 收敛曲线
        self.ax1.set_aspect('equal')
        self.ax1.set_xlim(0, 10)
        self.ax1.set_ylim(0, 10)
        self.ax1.set_title("Buffon's Needle Experiment")
        self.ax2.set_title("Estimation of π")
        self.ax2.axhline(y=np.pi, color='gray', linestyle='--', linewidth=1)

        # 画平行线 (初始间距为1)
        self.line_spacing = DEFAULT_D
        self._draw_parallel_lines()

        # 针长和投针次数 (通过滑块控制)
        self.needle_length = DEFAULT_L
        self.total_needles = DEFAULT_N

        # 存储所有针的端点与颜色
        self.needles = []  # 每个元素为 (x1, y1, x2, y2, color)

        # 当前针数和累积相交数
        self.count = 0
        self.cross_count = 0

        # 收敛数据
        self.pi_estimates = []

        # 添加控件
        self._add_widgets()

        # 统计信息文本框
        self.stats_text = self.fig.text(0.65, 0.40, "", fontsize=12, family="monospace")
        self.update_stats()

    def _draw_parallel_lines(self):
        """根据当前间距重画平行线"""
        self.ax1.clear()
        d = self.line_spacing
        xmin, xmax = 0, 10
        ymin, ymax = 0, 10
        y = 0
        while y <= ymax:
            self.ax1.axhline(y, color='black', linewidth=0.5)
            y += d
        self.ax1.set_xlim(xmin, xmax)
        self.ax1.set_ylim(ymin, ymax)
        self.ax1.set_aspect('equal')

    def _add_widgets(self):
        # 间距滑块
        ax_d = self.fig.add_axes([0.25, 0.02, 0.15, 0.03])
        self.slider_d = Slider(ax_d, 'Spacing d', 0.5, 3.0, valinit=DEFAULT_D, valstep=0.1)
        self.slider_d.on_changed(self._update_d)

        # 针长滑块
        ax_l = self.fig.add_axes([0.50, 0.02, 0.15, 0.03])
        self.slider_l = Slider(ax_l, 'Needle L', 0.1, self.slider_d.val, valinit=DEFAULT_L, valstep=0.05)
        self.slider_l.on_changed(self._update_l)
        # 限制 L <= d
        self.slider_d.on_changed(self._limit_l)

        # 总针数滑块
        ax_n = self.fig.add_axes([0.75, 0.02, 0.15, 0.03])
        self.slider_n = Slider(ax_n, 'Total N', 100, 5000, valinit=DEFAULT_N, valfmt='%d', valstep=100)
        self.slider_n.on_changed(self._update_n)

        # 启动按钮
        ax_button = self.fig.add_axes([0.65, 0.08, 0.1, 0.04])
        self.button = Button(ax_button, 'Run')
        self.button.on_clicked(self.run_simulation)

        # 重置按钮
        ax_reset = self.fig.add_axes([0.78, 0.08, 0.1, 0.04])
        self.reset_btn = Button(ax_reset, 'Reset')
        self.reset_btn.on_clicked(self.reset)

    def _limit_l(self, val):
        """当间距变化时，限制针长滑块的最大值"""
        self.slider_l.valmax = val
        if self.slider_l.val > val:
            self.slider_l.set_val(val)

    def _update_d(self, val):
        self.line_spacing = val
        self._draw_parallel_lines()
        self.redraw_needles()
        # 限制针长
        self._limit_l(val)

    def _update_l(self, val):
        self.needle_length = val

    def _update_n(self, val):
        self.total_needles = int(val)

    def run_simulation(self, event=None):
        """执行模拟：生成所有针，绘制它们，并显示收敛过程"""
        # 清除之前的针和收敛数据
        self.count = 0
        self.cross_count = 0
        self.needles.clear()
        self.pi_estimates.clear()
        d = self.line_spacing
        L = self.needle_length
        N = self.total_needles
        # 在绘图区域内随机生成中心点
        x_center = np.random.uniform(1, 9, N)
        y_center = np.random.uniform(0, 10, N)
        angles = np.random.uniform(0, np.pi, N)
        for i in range(N):
            xc, yc, theta = x_center[i], y_center[i], angles[i]
            dx = 0.5 * L * np.cos(theta)
            dy = 0.5 * L * np.sin(theta)
            x1, y1 = xc - dx, yc - dy
            x2, y2 = xc + dx, yc + dy
            # 判断相交：针中心到最近平行线的距离 <= (L/2)*sinθ
            nearest_line = round(yc / d) * d
            dist = abs(yc - nearest_line)
            cross = dist <= (0.5 * L * np.sin(theta))
            if cross:
                self.cross_count += 1
                color = 'red'
            else:
                color = 'blue'
            self.needles.append((x1, y1, x2, y2, color))
            self.count += 1
            # 计算 π 估计值
            if self.cross_count > 0:
                est_pi = (2 * L * self.count) / (d * self.cross_count)
            else:
                est_pi = np.nan
            self.pi_estimates.append(est_pi)
        # 画所有针
        self.redraw_needles()
        # 画收敛曲线
        self.plot_convergence()
        self.update_stats()

    def redraw_needles(self):
        """在 ax1 上画出所有已生成的针"""
        # 清除旧的针（保留平行线，可重新画）
        self._draw_parallel_lines()
        for (x1, y1, x2, y2, col) in self.needles:
            self.ax1.plot([x1, x2], [y1, y2], color=col, linewidth=0.8)

    def plot_convergence(self):
        """更新收敛曲线"""
        self.ax2.clear()
        self.ax2.set_title("Estimation of π")
        self.ax2.axhline(y=np.pi, color='gray', linestyle='--', linewidth=1)
        if self.pi_estimates:
            self.ax2.plot(range(1, len(self.pi_estimates)+1), self.pi_estimates, color='green', linewidth=1)
            self.ax2.set_xlabel("Number of needles")
            self.ax2.set_ylabel("Estimated π")
        self.fig.canvas.draw_idle()

    def update_stats(self):
        """更新统计信息文本"""
        d = self.line_spacing
        L = self.needle_length
        if self.count > 0 and self.cross_count > 0:
            freq = self.cross_count / self.count
            est_pi = (2 * L * self.count) / (d * self.cross_count)
        else:
            freq = 0
            est_pi = 0
        text = f"Total needles: {self.count}\nCross count: {self.cross_count}\nFrequency: {freq:.4f}\nEstimated π: {est_pi:.6f}\nTrue π: {np.pi:.6f}"
        self.stats_text.set_text(text)
        self.fig.canvas.draw_idle()

    def reset(self, event=None):
        """重置实验，清除数据"""
        self.count = 0
        self.cross_count = 0
        self.needles.clear()
        self.pi_estimates.clear()
        self.ax1.clear()
        self._draw_parallel_lines()
        self.ax2.clear()
        self.ax2.set_title("Estimation of π")
        self.ax2.axhline(y=np.pi, color='gray', linestyle='--', linewidth=1)
        self.fig.canvas.draw_idle()
        self.update_stats()

if __name__ == "__main__":
    exp = BuffonExperiment()
    plt.show()