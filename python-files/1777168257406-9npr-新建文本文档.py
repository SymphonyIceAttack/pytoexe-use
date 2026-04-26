import tkinter as tk
from tkinter import messagebox

# 计算器类
class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("药剂兑水计算器")
        self.root.geometry("400x400")

        # 创建初始面板
        self.create_initial_panel()

    def create_initial_panel(self):
        # 清空窗口
        for widget in self.root.winfo_children():
            widget.destroy()

        # 显示输入框和标签
        self.dose_label = tk.Label(self.root, text="药剂量(g/kg/ml/l):")
        self.dose_label.grid(row=0, column=0)
        self.dose_entry = tk.Entry(self.root)
        self.dose_entry.grid(row=0, column=1)

        self.water_label = tk.Label(self.root, text="兑水量或兑水倍数:")
        self.water_label.grid(row=1, column=0)
        self.water_entry = tk.Entry(self.root)
        self.water_entry.grid(row=1, column=1)

        # 操作按钮
        self.calculate_button = tk.Button(self.root, text="计算", command=self.calculate)
        self.calculate_button.grid(row=2, column=0, columnspan=2)

    def calculate(self):
        # 获取用户输入的药剂量与兑水信息
        dose = self.dose_entry.get()
        water = self.water_entry.get()

        try:
            dose = float(dose)
            water = float(water)

            # 判断用户输入的是兑水量还是兑水倍数
            if water <= 1:  # 假设兑水倍数是大于1
                # 如果是兑水量，则计算每斤水需要多少药剂
                amount_per_kg = dose / water
                messagebox.showinfo("结果", f"每斤水需要药剂：{amount_per_kg:.2f} 单位")
            else:
                # 如果是兑水倍数，则计算药剂可兑水总量
                total_water = dose * water
                messagebox.showinfo("结果", f"药剂可兑水总量：{total_water:.2f} 单位")
                self.create_calculation_panel(dose, water)

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")

    def create_calculation_panel(self, dose, water):
        # 创建新的面板进行计算
        for widget in self.root.winfo_children():
            widget.destroy()

        # 创建计算面板
        self.new_calculation_label = tk.Label(self.root, text="请输入需要计算的数据")
        self.new_calculation_label.grid(row=0, column=0, columnspan=2)

        self.water_amount_label = tk.Label(self.root, text="需要的水量(斤):")
        self.water_amount_label.grid(row=1, column=0)
        self.water_amount_entry = tk.Entry(self.root)
        self.water_amount_entry.grid(row=1, column=1)

        self.dose_amount_label = tk.Label(self.root, text="药剂量(单位):")
        self.dose_amount_label.grid(row=2, column=0)
        self.dose_amount_entry = tk.Entry(self.root)
        self.dose_amount_entry.grid(row=2, column=1)

        # 计算按钮
        self.calculate_final_button = tk.Button(self.root, text="计算", command=lambda: self.final_calculate(dose, water))
        self.calculate_final_button.grid(row=3, column=0, columnspan=2)

    def final_calculate(self, dose, water):
        try:
            water_amount = float(self.water_amount_entry.get())
            dose_amount = float(self.dose_amount_entry.get())

            # 进行计算
            if water_amount:
                result = dose * water_amount / dose_amount
                messagebox.showinfo("结果", f"所需药剂量：{result:.2f} 单位")
            else:
                result = dose * dose_amount / water_amount
                messagebox.showinfo("结果", f"所需兑水量：{result:.2f} 单位")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")


# 主函数
if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()