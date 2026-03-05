import tkinter as tk
from tkinter import scrolledtext
import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class CurveEditorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("📈 曲线手动调整工具")
        self.master.geometry("900x600")

        # 存储数据的列表
        self.x_data = []
        self.y_data = []
        self.dragging_point = None  # 当前正在拖拽的点的索引

        # --- 左侧控制面板 (输入与输出) ---
        self.frame_left = tk.Frame(master, width=250)
        self.frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(self.frame_left, text="1. 粘贴原始数据 (一列数字):", font=("SimHei", 10, "bold")).pack(anchor=tk.W)
        self.input_text = scrolledtext.ScrolledText(self.frame_left, width=25, height=12)
        self.input_text.pack(pady=5)

        self.btn_plot = tk.Button(self.frame_left, text="👉 生成 / 重置曲线", bg="#4CAF50", fg="white",
                                  command=self.plot_data)
        self.btn_plot.pack(fill=tk.X, pady=10)

        tk.Label(self.frame_left, text="3. 拖拽后的新数据 (实时更新):", font=("SimHei", 10, "bold")).pack(anchor=tk.W)
        self.output_text = scrolledtext.ScrolledText(self.frame_left, width=25, height=12)
        self.output_text.pack(pady=5)

        # --- 右侧绘图面板 (Matplotlib 画布) ---
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 绑定鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)

    def plot_data(self):
        """读取输入框数据并画图"""
        raw_text = self.input_text.get("1.0", tk.END).strip()
        if not raw_text:
            return

        try:
            # 清洗并读取数据
            self.y_data = [float(val) for val in raw_text.split()]
            self.x_data = list(range(len(self.y_data)))
        except ValueError:
            tk.messagebox.showerror("错误", "数据格式不对，请确保全是数字！")
            return

        self.update_plot()
        self.update_output()

    def update_plot(self):
        """刷新曲线显示"""
        self.ax.clear()
        # 画出蓝色连线和红色拖拽点
        self.ax.plot(self.x_data, self.y_data, 'b-', marker='o', markersize=8, markerfacecolor='red',
                     markeredgecolor='white')
        self.ax.set_title("2. 用鼠标按住红点上下拖动，调整数据！", fontsize=12, fontname='SimHei', fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()

    def update_output(self):
        """把最新的数据写回左下角的输出框"""
        self.output_text.delete("1.0", tk.END)
        # 默认保留 3 位小数，你可以根据需要修改
        out_str = "\n".join([f"{y:.3f}" for y in self.y_data])
        self.output_text.insert(tk.END, out_str)

    # --- 核心拖拽逻辑 ---
    def on_press(self, event):
        """鼠标按下时，寻找离鼠标最近的红点"""
        if event.inaxes != self.ax: return

        # 因为我们的 X 轴是 0, 1, 2... 的整数，直接对鼠标 X 坐标四舍五入就能找到对应的点
        idx = int(round(event.xdata))
        if 0 <= idx < len(self.y_data):
            # 检查一下鼠标 Y 轴也没有偏离太远（容错率）
            if abs(event.ydata - self.y_data[idx]) < (max(self.y_data) - min(self.y_data)) * 0.1 + 0.01:
                self.dragging_point = idx

    def on_motion(self, event):
        """鼠标移动时，实时更新该点的 Y 坐标并重绘"""
        if self.dragging_point is None or event.inaxes != self.ax: return

        # 更新数据
        self.y_data[self.dragging_point] = event.ydata
        self.update_plot()
        self.update_output()

    def on_release(self, event):
        """松开鼠标，结束拖拽"""
        self.dragging_point = None


if __name__ == "__main__":
    root = tk.Tk()
    app = CurveEditorApp(root)
    root.mainloop()