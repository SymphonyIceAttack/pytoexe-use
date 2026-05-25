import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings
import sys
warnings.filterwarnings("ignore")

# ===================== 仅使用 Windows 自带中文字体，无任何警告 =====================
plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
# ==================================================================================

# ===================== 悬浮提示（Tooltip）类 =====================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("微软雅黑", 9)
        )
        label.pack()

    def leave(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()
# ===================================================================

class Matrixes():
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.matrix = None
        if filepath:
            self.load_matrix(filepath)

    def load_matrix(self, filepath):
        matrix = np.genfromtxt(filepath, delimiter=None, skip_header=1).astype(int)
        self.matrix = matrix[:, 1:].astype(int)

    def winlose_count(self):
        max_count = [0] * 5
        min_count = [0] * 5
        for row in self.matrix:
            maximum = max(row)
            minimum = min(row)
            for j, val in enumerate(row):
                if val == maximum:
                    max_count[j] += 1
                if val == minimum:
                    min_count[j] += 1
        return f"冠军次数：{max_count}\n垫底次数：{min_count}"

    def total_sum(self, opt1, opt2, opt3):
        data_matrix = self.matrix / 6000
        for col_idx in range(data_matrix.shape[1]):
            col = data_matrix[:, col_idx]
            maximum = max(col)
            minimum = min(col)
            q10, q25, qmid, q75, q90 = np.percentile(col, [10, 25, 50, 75, 90])
            cgdata = (q25)/5 + qmid/2 + 3*(q75)/10
            ckdata = (q25)/4 + qmid/2 + q75/4
            dogedata = q10/10 + q25/4 + 2*(qmid)/5 + q75/5 + q90/20
            pop_var = np.var(col, ddof=0)
            
            text = f'中位数时长 (常规水平):{round(qmid,4)}分钟\n下十分位 (10%):{round(q10,4)}分钟\n下四分位 (25%):{round(q25,4)}分钟\n上四分位 (75%):{round(q75,4)}分钟\n上十分位 (90%):{round(q90,4)}分钟\n最佳表现:{round(maximum,4)}分钟\n最差表现:{round(minimum,4)}分钟\nσ² 方差:{round(pop_var,2)}'
            text1 = f'加权均值 (2:5:3)（残光方法）：{round(cgdata,4)}分钟' if opt1 else ''
            text2 = f'加权均值 (1:2:1)（参考用）:{round(ckdata,4)}分钟' if opt2 else ''
            text3 = f'加权均值 (1:2.5:4:2:0.5)（doge方法）:{round(dogedata,4)}分钟' if opt3 else ''
            parts = [text1, text2, text3, text]
            yield '\n'.join(p for p in parts if p)

    def get_single_group_data(self, idx):
        data_matrix = self.matrix / 6000
        return data_matrix[:, idx]
    
    def get_comparison_data(self, indices):
        data_matrix = self.matrix / 6000
        comparison_data = []
        for idx in indices:
            col = data_matrix[:, idx]
            maximum = max(col)
            minimum = min(col)
            q25, q75 = np.percentile(col, [25, 75])
            comparison_data.append({
                'min': minimum,
                'max': maximum,
                'q25': q25,
                'q75': q75
            })
        return comparison_data

class DataUI:
    def __init__(self, root):
        self.root = root
        self.root.title("比赛数据统计工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.doc = Matrixes()
        self.team_names = []
        self.child_windows = []

        self.option1_var = tk.IntVar()
        self.option2_var = tk.IntVar()
        self.option3_var = tk.IntVar()
        self.option1_var.set(1)
        self.option2_var.set(0)
        self.option3_var.set(0)

        # ---------- 复选框 + Tooltip ----------
        cb1 = tk.Checkbutton(root, variable=self.option1_var, text='加权均值 (2:5:3)（残光方法）')
        cb1.grid(row=0, column=0, sticky="w", padx=20, pady=5)
        ToolTip(cb1, "残光方法：25%分位×0.2 + 中位数×0.5 + 75%分位×0.3")

        cb2 = tk.Checkbutton(root, variable=self.option2_var, text='加权均值 (1:2:1)（参考用）')
        cb2.grid(row=0, column=1, sticky="w", padx=20, pady=5)
        ToolTip(cb2, "参考加权：25%×0.25 + 中位数×0.5 + 75%×0.25")

        cb3 = tk.Checkbutton(root, variable=self.option3_var, text='加权均值 (1:2.5:4:2:0.5)（doge方法）')
        cb3.grid(row=0, column=2, sticky="w", padx=20, pady=5)
        ToolTip(cb3, "doge方法：10%、25%、中位数、75%、90%分位加权")

        # ---------- 按钮栏 + Tooltip ----------
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=5)

        btn_file = ttk.Button(btn_frame, text="选择文件", command=self.load_file)
        btn_file.grid(row=0, column=0, padx=5)
        ToolTip(btn_file, "请选择txt数据文件，第一行忽略，从第二行开始读取")

        btn_reset = ttk.Button(btn_frame, text="重置清空", command=self.reset_all)
        btn_reset.grid(row=0, column=1, padx=5)
        ToolTip(btn_reset, "清空所有数据、队伍名、结果，恢复初始状态")

        btn_save = ttk.Button(btn_frame, text="保存结果", command=self.save_result)
        btn_save.grid(row=0, column=2, padx=5)
        ToolTip(btn_save, "将基础信息和详细统计结果保存为.log文件")

        btn_single_plot = ttk.Button(btn_frame, text="每组统计图", command=self.open_team_selector)
        btn_single_plot.grid(row=0, column=3, padx=5)
        ToolTip(btn_single_plot, "选择单个队伍，查看其时长分布直方图")

        btn_comp_plot = ttk.Button(btn_frame, text="多队对比图", command=self.open_comparison_selector)
        btn_comp_plot.grid(row=0, column=4, padx=5)
        ToolTip(btn_comp_plot, "最多选5队，生成最大/最小折线图+四分位条形对比图")

        self.file_label = ttk.Label(root, text="未选择文件")
        self.file_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=10)

        self.basic_info = scrolledtext.ScrolledText(root, width=80, height=4)
        self.basic_info.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        ttk.Label(root, text="输入队伍编号（空格分隔）").grid(row=4, column=0, columnspan=3, sticky="w", padx=10)
        self.team_entry = ttk.Entry(root, width=50)
        self.team_entry.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        btn_calc = ttk.Button(root, text="开始统计", command=self.calc_data)
        btn_calc.grid(row=6, column=1, padx=20, pady=5)
        ToolTip(btn_calc, "按输入的队伍顺序，输出各队分位、均值、方差等详细数据")

        btn_note = ttk.Button(root,text='注意事项',command=self.show_text)
        btn_note.grid(row=6,column=2,padx=20,pady=5)
        ToolTip(btn_note, "查看使用说明与注意事项")

        ttk.Label(root, text="详细统计结果").grid(row=7, column=0, columnspan=3, sticky="w", padx=10)
        self.result_text = scrolledtext.ScrolledText(root, width=80, height=20)
        self.result_text.grid(row=8, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        btn_exit = ttk.Button(root, text="退出程序", command=self.quit_app)
        btn_exit.place(relx=0.92, rely=0.95, anchor=tk.SE)
        ToolTip(btn_exit, "关闭所有窗口并退出程序")

        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)
        root.rowconfigure(8, weight=1)

    def on_close(self):
        plt.close('all')
        for win in self.child_windows:
            try: win.destroy()
            except: pass
        self.root.destroy()
        sys.exit()

    def quit_app(self):
        self.on_close()
        
    def show_text(self):
        textshow = '1.窗口上方的三个选项可以同时勾选也可以同时不选，默认选残光中位。注意要先勾选才能在下方输出中显示对应的中位！\n2.输出的统计结果是能改动的，所以最好不要在这里有旺盛的好奇心（）\n3.“重置清空”会将所有数据清空并默认回调至残光中位，在保存前谨慎点击！\n4.多队对比图最多支持同时选择5个队伍进行对比分析'
        messagebox.showinfo("注意事项", textshow)

    def open_team_selector(self):
        if self.doc.matrix is None:
            self.result_text.insert(tk.END, "\n请先加载数据！\n")
            return
        if not self.team_names:
            self.result_text.insert(tk.END, "\n请先输入队伍编号并统计！\n")
            return
        sel_win = tk.Toplevel(self.root)
        self.child_windows.append(sel_win)
        sel_win.title("选择要查看的队伍")
        sel_win.geometry("300x400")
        ttk.Label(sel_win, text="点击队伍查看统计图", font=('微软雅黑',11,'bold')).pack(pady=10)
        for idx, name in enumerate(self.team_names):
            ttk.Button(
                sel_win,
                text=f"队伍：{name}",
                command=lambda i=idx, n=name: self.show_single_plot(i, n)
            ).pack(fill='x', padx=20, pady=3)

    def show_single_plot(self, idx, team_name):
        data = self.doc.get_single_group_data(idx)
        plot_win = tk.Toplevel(self.root)
        self.child_windows.append(plot_win)
        plot_win.title(f"{team_name} 时长分布（组距1分钟）")
        plot_win.geometry("800x500")
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        bins = np.arange(int(np.floor(data.min())), int(np.ceil(data.max())) + 1, 1)
        ax.hist(data, bins=bins, color='#42b983', edgecolor='black', alpha=0.75)
        ax.set_title(f"队伍【{team_name}】时长分布", fontsize=13, fontweight='bold')
        ax.set_xlabel("时长（分钟）")
        ax.set_ylabel("出现次数")
        ax.grid(alpha=0.3)
        canvas = FigureCanvasTkAgg(fig, master=plot_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def open_comparison_selector(self):
        if self.doc.matrix is None:
            self.result_text.insert(tk.END, "\n请先加载数据！\n")
            return
        if not self.team_names:
            self.result_text.insert(tk.END, "\n请先输入队伍编号并统计！\n")
            return
        comp_sel_win = tk.Toplevel(self.root)
        self.child_windows.append(comp_sel_win)
        comp_sel_win.title("选择要对比的队伍（最多5个）")
        comp_sel_win.geometry("350x450")
        ttk.Label(comp_sel_win, text="勾选要对比的队伍（最多5个）", font=('微软雅黑',11,'bold')).pack(pady=10)
        self.comp_check_vars = []
        for name in self.team_names:
            var = tk.IntVar()
            self.comp_check_vars.append(var)
            ttk.Checkbutton(comp_sel_win, text=f"队伍：{name}", variable=var).pack(anchor='w', padx=30, pady=3)
        ttk.Button(comp_sel_win, text="生成对比图", command=lambda: self.generate_comparison_plots(comp_sel_win)).pack(pady=20)

    def generate_comparison_plots(self, sel_win):
        selected_indices = [i for i, var in enumerate(self.comp_check_vars) if var.get() == 1]
        if len(selected_indices) == 0:
            messagebox.showwarning("警告", "请至少选择一个队伍！")
            return
        if len(selected_indices) > 5:
            messagebox.showwarning("警告", "最多只能选择5个队伍进行对比！")
            return
        comp_data = self.doc.get_comparison_data(selected_indices)
        selected_names = [self.team_names[i] for i in selected_indices]
        sel_win.destroy()
        comp_win = tk.Toplevel(self.root)
        self.child_windows.append(comp_win)
        comp_win.title("多队数据对比")
        comp_win.geometry("1000x800")
        main_frame = ttk.Frame(comp_win)
        main_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        fig1, ax1 = plt.subplots(figsize=(10, 4), dpi=100)
        min_values = [data['min'] for data in comp_data]
        ax1.plot(selected_names, min_values, marker='o', linewidth=2, markersize=8, color='#2E86AB')
        ax1.set_title("各队最佳表现对比（数值越小越好）", fontsize=13, fontweight='bold')
        ax1.set_xlabel("队伍")
        ax1.set_ylabel("时长（分钟）")
        ax1.grid(alpha=0.3)
        ax1.set_ylim(bottom=0)
        for i, v in enumerate(min_values):
            ax1.text(i, v + 0.1, f"{v:.2f}", ha='center', fontweight='bold')
        canvas1 = FigureCanvasTkAgg(fig1, master=scrollable_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill='x', padx=20, pady=10)

        fig2, ax2 = plt.subplots(figsize=(10, 4), dpi=100)
        max_values = [data['max'] for data in comp_data]
        ax2.plot(selected_names, max_values, marker='s', linewidth=2, markersize=8, color='#A23B72')
        ax2.set_title("各队最差表现对比（数值越小越好）", fontsize=13, fontweight='bold')
        ax2.set_xlabel("队伍")
        ax2.set_ylabel("时长（分钟）")
        ax2.grid(alpha=0.3)
        for i, v in enumerate(max_values):
            ax2.text(i, v + 0.1, f"{v:.2f}", ha='center', fontweight='bold')
        canvas2 = FigureCanvasTkAgg(fig2, master=scrollable_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='x', padx=20, pady=10)

        fig3, ax3 = plt.subplots(figsize=(10, 5), dpi=100)
        x_pos = np.arange(len(selected_names))
        bar_width = 0.6
        q25_values = [data['q25'] for data in comp_data]
        q75_values = [data['q75'] for data in comp_data]
        min_values_bar = [data['min'] for data in comp_data]
        max_values_bar = [data['max'] for data in comp_data]
        ax3.bar(x_pos, [q25 - min_val for q25, min_val in zip(q25_values, min_values_bar)],
                bottom=min_values_bar, width=bar_width, color='#87CEEB', edgecolor='black', label='最小值-下四分位')
        ax3.bar(x_pos, [q75 - q25 for q75, q25 in zip(q75_values, q25_values)],
                bottom=q25_values, width=bar_width, color='#1E90FF', edgecolor='black', label='下四分位-上四分位(核心区间)')
        ax3.bar(x_pos, [max_val - q75 for max_val, q75 in zip(max_values_bar, q75_values)],
                bottom=q75_values, width=bar_width, color='#87CEEB', edgecolor='black', label='上四分位-最大值')
        ax3.set_title("各队时长分布区间对比", fontsize=13, fontweight='bold')
        ax3.set_xlabel("队伍")
        ax3.set_ylabel("时长（分钟）")
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(selected_names)
        ax3.legend()
        ax3.grid(alpha=0.3, axis='y')
        canvas3 = FigureCanvasTkAgg(fig3, master=scrollable_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill='x', padx=20, pady=10)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path: return
        try:
            self.doc.load_matrix(path)
            self.file_label.config(text=f"已加载：{path}")
            info = f"有效局数：{self.doc.matrix.shape[0]}\n{self.doc.winlose_count()}"
            self.basic_info.delete(1.0, tk.END)
            self.basic_info.insert(tk.END, info)
        except Exception as e:
            self.basic_info.delete(1.0, tk.END)
            self.basic_info.insert(tk.END, f"加载失败：{str(e)}")

    def reset_all(self):
        self.doc = Matrixes()
        self.file_label.config(text="未选择文件")
        self.basic_info.delete(1.0, tk.END)
        self.team_entry.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.option1_var.set(1)
        self.option2_var.set(0)
        self.option3_var.set(0)
        self.team_names = []

    def save_result(self):
        basic = self.basic_info.get(1.0, tk.END).strip()
        detail = self.result_text.get(1.0, tk.END).strip()
        if not basic and not detail:
            self.result_text.insert(tk.END, "\n无内容可保存！\n")
            return
        content = "===== 基础信息 =====\n" + basic + "\n\n===== 详细数据 =====\n" + detail
        save_path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log文件", "*.log")])
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.result_text.insert(tk.END, f"\n✅ 已保存：{save_path}\n")

    def calc_data(self):
        if self.doc.matrix is None:
            self.result_text.insert(tk.END, "请先选择文件！\n")
            return
        self.team_names = self.team_entry.get().strip().split()
        if not self.team_names:
            self.result_text.insert(tk.END, "请输入队伍编号！\n")
            return
        o1 = self.option1_var.get()
        o2 = self.option2_var.get()
        o3 = self.option3_var.get()
        self.result_text.delete(1.0, tk.END)
        try:
            for idx, data in enumerate(self.doc.total_sum(o1, o2, o3)):
                name = f"队伍 {self.team_names[idx]}" if idx < len(self.team_names) else f"队伍{idx+1}"
                self.result_text.insert(tk.END, "="*50 + "\n")
                self.result_text.insert(tk.END, name + "\n\n")
                self.result_text.insert(tk.END, data + "\n\n")
        except Exception as e:
            self.result_text.insert(tk.END, f"出错：{str(e)}")

if __name__ == '__main__':
    main_root = tk.Tk()
    app = DataUI(main_root)
    main_root.mainloop()