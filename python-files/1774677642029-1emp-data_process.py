import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def plot_from_txt(txt_path):
    """
    输入txt文件路径，自动读取数据并绘制【1个窗口、4个子图】的交互式双Y轴图
    鼠标悬停时会自动显示该点精确的 x（时间）和 y（左右两个轴的数值）
    """
    try:
        data = np.loadtxt(txt_path)
    except Exception as e:
        messagebox.showerror("读取错误", f"无法读取文件：{str(e)}")
        return

    # 提取各列数据（保持你原来的逻辑完全不变）
    pendulum_angle = data[:, 1]      
    slider_position = data[:, 2]     
    position_deviation = data[:, 3]  
    motor_current = data[:, 4]       
    target_angle = data[:, 5]        
    target_position = data[:, 6]     
    reserved = data[:, 7]            
    target_current = data[:, 8]      
    
    # 生成时间轴
    n = len(data)
    time = np.arange(n) * 0.005
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '摆杆角度 与 目标角度',
            '滑块位置 与 目标位置',
            '位置偏差 与 保留',
            '电机电流 与 目标电流'
        ),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 四个子图（和你原来一模一样）
    fig.add_trace(go.Scatter(x=time, y=pendulum_angle, name='摆杆角度', line=dict(color='blue', width=2)), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=time, y=target_angle, name='目标角度', line=dict(color='red', width=2)), row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text='摆杆角度', row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text='目标角度', row=1, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(x=time, y=slider_position, name='滑块位置', line=dict(color='blue', width=2)), row=1, col=2, secondary_y=False)
    fig.add_trace(go.Scatter(x=time, y=target_position, name='目标位置', line=dict(color='red', width=2)), row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text='滑块位置', row=1, col=2, secondary_y=False)
    fig.update_yaxes(title_text='目标位置', row=1, col=2, secondary_y=True)

    fig.add_trace(go.Scatter(x=time, y=position_deviation, name='位置偏差', line=dict(color='blue', width=2)), row=2, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=time, y=reserved, name='保留', line=dict(color='red', width=2)), row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text='位置偏差', row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text='保留', row=2, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(x=time, y=motor_current, name='电机电流', line=dict(color='blue', width=2)), row=2, col=2, secondary_y=False)
    fig.add_trace(go.Scatter(x=time, y=target_current, name='目标电流', line=dict(color='red', width=2)), row=2, col=2, secondary_y=True)
    fig.update_yaxes(title_text='电机电流', row=2, col=2, secondary_y=False)
    fig.update_yaxes(title_text='目标电流', row=2, col=2, secondary_y=True)

    # 全局设置（和你原来完全一样）
    fig.update_xaxes(title_text='时间 (s)', row=1, col=1)
    fig.update_xaxes(title_text='时间 (s)', row=1, col=2)
    fig.update_xaxes(title_text='时间 (s)', row=2, col=1)
    fig.update_xaxes(title_text='时间 (s)', row=2, col=2)
    
    fig.update_layout(
        height=900,
        width=1600,
        title_text="四组双Y轴数据对比图（鼠标悬停显示精确数值）",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white"
    )
    
    fig.show()   # ← 直接弹出浏览器图表（和你原来一样）


# ====================== 简单图形化界面 ======================
def select_file():
    file_path = filedialog.askopenfilename(
        title="选择数据文件",
        filetypes=[("TXT文件", "*.txt"), ("所有文件", "*.*")]
    )
    if file_path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, file_path)

def run_plot():
    path = entry_path.get().strip()
    if not path:
        messagebox.showwarning("提示", "请先选择一个TXT文件！")
        return
    if not os.path.exists(path):
        messagebox.showerror("错误", "文件不存在！")
        return
    plot_from_txt(path)


# ====================== 主程序 ======================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("倒立摆数据可视化工具")
    root.geometry("680x180")
    root.resizable(False, False)

    tk.Label(root, text="倒立摆数据绘图", font=("微软雅黑", 16, "bold")).pack(pady=10)

    frame = tk.Frame(root)
    frame.pack(pady=5, padx=20, fill="x")
    
    tk.Label(frame, text="数据文件：", font=("微软雅黑", 10)).pack(side=tk.LEFT)
    entry_path = tk.Entry(frame, width=70, font=("Consolas", 9))
    entry_path.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
    
    # 默认路径（你可以改掉）
    entry_path.insert(0, r"数据处理\data\p0.15.txt")

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text="浏览文件...", width=12, height=2,
              command=select_file, font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=15)
    
    tk.Button(btn_frame, text="生成图表", width=15, height=2, bg="#1f77b4", fg="white",
              command=run_plot, font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT, padx=15)

    tk.Label(root, text="提示：选择文件后点击“生成图表”，会直接弹出原来的交互式图表", 
             fg="gray", font=("微软雅黑", 9)).pack()

    root.mainloop()