import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image
import math
import webbrowser

# ===== 全局配置 =====
APP_VERSION = "1.1.0"
LOGO_PATH = "logo.png"  # 替换为你的logo路径
MM2_TO_IN2 = 0.0015500031  # 单位转换系数
BASE_UNIT = 1.0e-4  # 基础面积单位


class EngineeringSuite:
    def __init__(self, root):
        self.root = root
        self.root.title("器件工艺常用工具")
        self.root.geometry("1000x800")
        self.setup_ui()

    def setup_ui(self):
        # 加载logo
        self.load_logo()

        # 创建主容器
        self.notebook = ttk.Notebook(self.root)

        # 创建各功能页面
        self.create_signal_page()
        self.create_shear_page()
        self.create_about_page()

        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        self.setup_styles()

    def load_logo(self):
        try:
            img = Image.open(LOGO_PATH)
            img = img.resize((80, 80), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            logo_frame = ttk.Frame(self.root)
            logo_frame.place(x=10, y=10)
            ttk.Label(logo_frame, image=self.logo).pack()
        except Exception as e:
            print(f"Logo加载失败: {str(e)}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        # 自定义样式
        style.configure("Title.TLabel", font=("微软雅黑", 18, "bold"), foreground="#2c3e50")
        style.configure("SubTitle.TLabel", font=("宋体", 12), foreground="#34495e")
        style.configure("Copyright.TLabel", font=("楷体", 10), foreground="#7f8c8d")
        style.configure("Result.TEntry", foreground="#2c3e50", background="#f5f6fa")

    # ===== 信号转换页面 =====
    def create_signal_page(self):
        frame = ttk.Frame(self.notebook)

        # dB转换模块
        db_frame = ttk.LabelFrame(frame, text="dB ↔ 百分比转换", padding=15)
        db_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(db_frame, text="输入dB值：").grid(row=0, column=0, padx=5)
        self.db_entry = ttk.Entry(db_frame, width=18)
        self.db_entry.grid(row=0, column=1, padx=5)

        ttk.Button(db_frame, text="转换", command=self.calculate_db).grid(row=0, column=2, padx=10)

        ttk.Label(db_frame, text="透射百分比：").grid(row=1, column=0, pady=5)
        self.trans_result = ttk.Entry(db_frame, width=18, state="readonly", style="Result.TEntry")
        self.trans_result.grid(row=1, column=1)

        ttk.Label(db_frame, text="反射百分比：").grid(row=2, column=0, pady=5)
        self.reflect_result = ttk.Entry(db_frame, width=18, state="readonly", style="Result.TEntry")
        self.reflect_result.grid(row=2, column=1)

        # dBm转换模块
        dbm_frame = ttk.LabelFrame(frame, text="dBm ↔ mW转换", padding=15)
        dbm_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(dbm_frame, text="dBm：").grid(row=0, column=0)
        self.dbm_entry = ttk.Entry(dbm_frame, width=15)
        self.dbm_entry.grid(row=0, column=1)

        ttk.Button(dbm_frame, text="↔ 转换 ↔", command=self.convert_dbm_mw).grid(row=0, column=2, padx=10)

        ttk.Label(dbm_frame, text="mW：").grid(row=0, column=3)
        self.mw_entry = ttk.Entry(dbm_frame, width=15)
        self.mw_entry.grid(row=0, column=4)

        # 清空按钮
        ttk.Button(frame, text="清空所有数据", command=self.clear_all).pack(pady=15)

        self.notebook.add(frame, text="信号转换")

    # ===== 剪切力计算页面 =====
    def create_shear_page(self):
        frame = ttk.Frame(self.notebook)

        # 输入区域
        input_frame = ttk.LabelFrame(frame, text="参数输入", padding=15)
        input_frame.pack(padx=10, pady=10, fill="x")

        # 形状选择
        self.shape_var = tk.StringVar(value="矩形")
        shape_frame = ttk.Frame(input_frame)
        shape_frame.pack(pady=5)
        ttk.Radiobutton(shape_frame, text="矩形", variable=self.shape_var,
                        value="矩形", command=self.toggle_shape).pack(side="left", padx=10)
        ttk.Radiobutton(shape_frame, text="圆形", variable=self.shape_var,
                        value="圆形", command=self.toggle_shape).pack(side="left", padx=10)

        # 尺寸输入
        param_frame = ttk.Frame(input_frame)
        param_frame.pack(pady=10)

        ttk.Label(param_frame, text="芯片名称：").grid(row=0, column=0, padx=5)
        self.chip_name_entry = ttk.Entry(param_frame)
        self.chip_name_entry.grid(row=0, column=1, pady=5)

        ttk.Label(param_frame, text="长 (mm)：").grid(row=1, column=0)
        self.length_entry = ttk.Entry(param_frame)
        self.length_entry.grid(row=1, column=1)

        ttk.Label(param_frame, text="宽 (mm)：").grid(row=2, column=0)
        self.width_entry = ttk.Entry(param_frame)
        self.width_entry.grid(row=2, column=1)

        ttk.Label(param_frame, text="半径 (mm)：").grid(row=3, column=0)
        self.radius_entry = ttk.Entry(param_frame, state="disabled")
        self.radius_entry.grid(row=3, column=1)

        # 按钮区域
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="计算", command=self.calculate_shear).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="清空", command=self.clear_shear).pack(side="left", padx=10)

        # 结果表格
        result_frame = ttk.LabelFrame(frame, text="计算结果", padding=15)
        result_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ("芯片名称", "面积(mm²)", "面积(in²)", "1.0X", "1.25X", "2.0X")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=8)

        # 配置表格列
        col_width = [120, 100, 120, 80, 100, 80]
        for col, width in zip(columns, col_width):
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=width, anchor="center")

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.result_tree.pack(fill="both", expand=True)

        self.notebook.add(frame, text="剪切力计算")

    # ===== 关于页面 =====
    def create_about_page(self):
        frame = ttk.Frame(self.notebook)

        # 主信息区
        info_frame = ttk.Frame(frame)
        info_frame.pack(pady=50, expand=True)

        ttk.Label(info_frame, text="器件工艺组常用工具", style="Title.TLabel").pack(pady=15)
        ttk.Label(info_frame, text=f"版本: {APP_VERSION}", style="SubTitle.TLabel").pack(pady=5)

        # 功能列表
        ttk.Label(info_frame, text="包含功能：", style="SubTitle.TLabel").pack(pady=10)
        feature_frame = ttk.Frame(info_frame)
        feature_frame.pack()
        features = [
            "• 信号参数转换（dB/dBm/mW）",
            "• 芯片剪切力专业计算",
            "• 数据表格输出"
        ]
        for feat in features:
            ttk.Label(feature_frame, text=feat).pack(anchor="w")

        # 版权信息
        copyright_frame = ttk.Frame(frame)
        copyright_frame.pack(side="bottom", fill="x", pady=15)
        ttk.Label(copyright_frame, text="© 2025.02 Leo",
                  style="Copyright.TLabel").pack(side="right", padx=20)

        self.notebook.add(frame, text="关于")

    # ===== 核心功能函数 =====
    def calculate_db(self):
        try:
            db = float(self.db_entry.get())
            trans = 10 ** (db / 10) * 100
            refl = 100 - trans

            self.update_entry(self.trans_result, f"{trans:.4f}%")
            self.update_entry(self.reflect_result, f"{refl:.4f}%")
        except ValueError:
            self.show_error("请输入有效的dB值")

    def convert_dbm_mw(self):
        try:
            if self.dbm_entry.get():
                dbm = float(self.dbm_entry.get())
                mw = 10 ** (dbm / 10)
                self.update_entry(self.mw_entry, f"{mw:.4f}", readonly=True)
                self.dbm_entry.delete(0, tk.END)
            elif self.mw_entry.get():
                mw = float(self.mw_entry.get())
                if mw <= 0:
                    raise ValueError("功率值必须大于0")
                dbm = 10 * math.log10(mw)
                self.update_entry(self.dbm_entry, f"{dbm:.4f}", readonly=True)
                self.mw_entry.delete(0, tk.END)
        except Exception as e:
            self.show_error(str(e))
            self.dbm_entry.config(state="normal")
            self.mw_entry.config(state="normal")

    def calculate_shear(self):
        try:
            # 获取输入参数
            length = self.length_entry.get()
            width = self.width_entry.get()
            radius = self.radius_entry.get()

            # 计算面积
            if self.shape_var.get() == "矩形":
                l, w = float(length), float(width)
                area_mm = l * w
            else:
                r = float(radius)
                area_mm = math.pi * r ** 2

            # 单位转换和计算
            area_in = area_mm * MM2_TO_IN2
            base = area_in / BASE_UNIT

            # 计算剪切力
            if base < 5:
                forces = [base * 0.04, base * 0.05, base * 0.08]
            elif base <= 64:
                forces = [base * 0.04, base * 0.05, base * 0.08]
            else:
                forces = [2.5, 3.125, 5.0]

            # 添加结果到表格
            self.result_tree.insert("", "end", values=(
                self.chip_name_entry.get() or "-",
                f"{area_mm:.4f}",
                f"{area_in:.6f}",
                f"{forces[0]:.3f} Kg",
                f"{forces[1]:.3f} Kg",
                f"{forces[2]:.3f} Kg"
            ))
        except Exception as e:
            self.show_error(str(e))

    # ===== 工具函数 =====
    def update_entry(self, entry, value, readonly=True):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if readonly:
            entry.config(state="readonly")

    def show_error(self, message):
        messagebox.showerror("输入错误", message)

    def toggle_shape(self):
        if self.shape_var.get() == "矩形":
            self.length_entry.config(state="normal")
            self.width_entry.config(state="normal")
            self.radius_entry.config(state="disabled")
        else:
            self.length_entry.config(state="disabled")
            self.width_entry.config(state="disabled")
            self.radius_entry.config(state="normal")

    def clear_all(self):
        # 清空信号转换数据
        self.db_entry.delete(0, tk.END)
        self.update_entry(self.trans_result, "")
        self.update_entry(self.reflect_result, "")
        self.dbm_entry.config(state="normal")
        self.dbm_entry.delete(0, tk.END)
        self.mw_entry.config(state="normal")
        self.mw_entry.delete(0, tk.END)

    def clear_shear(self):
        # 清空剪切力计算数据
        self.length_entry.delete(0, tk.END)
        self.width_entry.delete(0, tk.END)
        self.radius_entry.delete(0, tk.END)
        self.chip_name_entry.delete(0, tk.END)
        self.result_tree.delete(*self.result_tree.get_children())


if __name__ == "__main__":
    root = tk.Tk()
    app = EngineeringSuite(root)
    root.mainloop()