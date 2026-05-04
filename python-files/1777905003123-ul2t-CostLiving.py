import tkinter as tk
from tkinter import ttk, messagebox


class WaterElectricityCalcSimple:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("校园宿舍水电费计算小程序")
        self.root.geometry("420x280")
        self.root.resizable(False, False)

        # 常量定义
        self.ELECTRIC_BASE = 0.55
        self.ELECTRIC_OVER = 0.85
        self.WATER_PRICE = 3.20
        self.ELECTRIC_LADDER = 100

        self.init_ui()

        # 居中显示
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def init_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        # 宿舍楼栋选择（使用单选按钮）
        ttk.Label(input_frame, text="选择宿舍楼栋：").grid(row=0, column=0, sticky=tk.W, pady=5)

        # 创建单选按钮框架
        radio_frame = ttk.Frame(input_frame)
        radio_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        self.building_var = tk.StringVar(value="1号宿舍楼")
        buildings = ["1号宿舍楼", "2号宿舍楼", "3号宿舍楼", "研究生公寓"]

        for i, building in enumerate(buildings):
            rb = ttk.Radiobutton(radio_frame, text=building, variable=self.building_var, value=building)
            rb.grid(row=i, column=0, sticky=tk.W, padx=5)
        # 用电量输入
        ttk.Label(input_frame, text="本月用电量(度)：").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.txt_electric = ttk.Entry(input_frame, width=22)
        self.txt_electric.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 用水量输入
        ttk.Label(input_frame, text="本月用水量(吨)：").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.txt_water = ttk.Entry(input_frame, width=22)
        self.txt_water.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, pady=(10, 0))

        btn_calc = ttk.Button(btn_frame, text="计算费用", command=self.calc_fee)
        btn_calc.grid(row=0, column=0, padx=10)

        btn_reset = ttk.Button(btn_frame, text="重置清空", command=self.reset_form)
        btn_reset.grid(row=0, column=1, padx=10)

    def calc_fee(self):
        try:
            e_str = self.txt_electric.get().strip()
            w_str = self.txt_water.get().strip()

            if not e_str or not w_str:
                messagebox.showwarning("提示", "用电量、用水量不能为空！")
                return

            electric = float(e_str)
            water = float(w_str)

            if electric < 0 or water < 0:
                messagebox.showwarning("提示", "用电量和用水量不能为负数！")
                return

            if electric > 9999 or water > 999:
                messagebox.showwarning("提示", "输入数值超出合理范围！")
                return

            # 阶梯电费计算
            if electric <= self.ELECTRIC_LADDER:
                electric_fee = electric * self.ELECTRIC_BASE
            else:
                electric_fee = (self.ELECTRIC_LADDER * self.ELECTRIC_BASE +
                                (electric - self.ELECTRIC_LADDER) * self.ELECTRIC_OVER)

            water_fee = water * self.WATER_PRICE
            total = electric_fee + water_fee

            # 显示结果
            result = f"水费：{water_fee:.2f}元，电费：{electric_fee:.2f}元，合计：{total:.2f}元"
            messagebox.showinfo("计算结果", result)

        except ValueError:
            messagebox.showerror("错误", "请输入合法数字，不能输入汉字、字母、符号！")

    def reset_form(self):
        self.building_var.set("1号宿舍楼")
        self.txt_electric.delete(0, tk.END)
        self.txt_water.delete(0, tk.END)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WaterElectricityCalcSimple()
    app.run()
