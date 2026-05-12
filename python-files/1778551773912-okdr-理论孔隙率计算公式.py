import tkinter as tk
from tkinter import ttk, messagebox

# ---------- 切换显示 ----------
def update_inputs():
    if mode_var.get() == "deposition":
        lbl_resin_density.grid_remove()
        entry_resin_density.grid_remove()
        lbl_impreg_density.grid_remove()
        entry_impreg_density.grid_remove()
    else:
        lbl_resin_density.grid()
        entry_resin_density.grid()
        lbl_impreg_density.grid()
        entry_impreg_density.grid()

# ---------- 计算核心 ----------
def calculate():
    try:
        fiber_d = float(entry_fiber_density.get())
        preform_d = float(entry_preform_density.get())
        dep_carbon_d = float(entry_dep_carbon_density.get())
        post_dep_d = float(entry_post_dep_density.get())
    except ValueError:
        messagebox.showerror("输入错误", "请确保前四个参数都是有效数字")
        return

    if mode_var.get() == "deposition":
        # 沉积后孔隙率公式： ( 1/preform - 1/fiber - (post_dep/preform - 1)/dep_carbon ) * preform
        numerator = 1 / preform_d - 1 / fiber_d - (post_dep_d / preform_d - 1) / dep_carbon_d
        porosity = numerator * preform_d
        result = f"沉积后孔隙率 = {porosity:.6f}"
    else:
        try:
            resin_d = float(entry_resin_density.get())
            impreg_d = float(entry_impreg_density.get())
        except ValueError:
            messagebox.showerror("输入错误", "请输入浸渍碳密度和浸渍后材料密度")
            return
        # 浸渍后孔隙率公式：
        # [ (1/preform - 1/fiber - (post_dep/preform - 1)/dep_carbon) - (impreg/preform - post_dep/preform)/resin ] * preform
        term1 = (1 / preform_d - 1 / fiber_d - (post_dep_d / preform_d - 1) / dep_carbon_d)
        term2 = (impreg_d / preform_d - post_dep_d / preform_d) / resin_d
        porosity = (term1 - term2) * preform_d
        result = f"浸渍后孔隙率 = {porosity:.6f}"

    lbl_result.config(text=result)

# ---------- 主窗口 ----------
root = tk.Tk()
root.title("孔隙率计算器")
root.geometry("450x350")
root.resizable(False, False)

mode_var = tk.StringVar(value="deposition")
ttk.Label(root, text="选择计算类型：").grid(row=0, column=0, padx=10, pady=10, sticky="w")
ttk.Radiobutton(root, text="沉积后孔隙率", variable=mode_var,
                value="deposition", command=update_inputs).grid(row=0, column=1, padx=5, pady=10)
ttk.Radiobutton(root, text="浸渍后孔隙率", variable=mode_var,
                value="impregnation", command=update_inputs).grid(row=0, column=2, padx=5, pady=10)

ttk.Label(root, text="碳纤维密度：").grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_fiber_density = ttk.Entry(root)
entry_fiber_density.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="w")

ttk.Label(root, text="预制体密度：").grid(row=2, column=0, padx=10, pady=5, sticky="e")
entry_preform_density = ttk.Entry(root)
entry_preform_density.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")

ttk.Label(root, text="沉积碳密度：").grid(row=3, column=0, padx=10, pady=5, sticky="e")
entry_dep_carbon_density = ttk.Entry(root)
entry_dep_carbon_density.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="w")

ttk.Label(root, text="沉积后材料密度：").grid(row=4, column=0, padx=10, pady=5, sticky="e")
entry_post_dep_density = ttk.Entry(root)
entry_post_dep_density.grid(row=4, column=1, columnspan=2, padx=10, pady=5, sticky="w")

lbl_resin_density = ttk.Label(root, text="浸渍碳密度（树脂/沥青等）：")
entry_resin_density = ttk.Entry(root)
lbl_impreg_density = ttk.Label(root, text="浸渍后材料密度：")
entry_impreg_density = ttk.Entry(root)

lbl_resin_density.grid(row=5, column=0, padx=10, pady=5, sticky="e")
entry_resin_density.grid(row=5, column=1, columnspan=2, padx=10, pady=5, sticky="w")
lbl_impreg_density.grid(row=6, column=0, padx=10, pady=5, sticky="e")
entry_impreg_density.grid(row=6, column=1, columnspan=2, padx=10, pady=5, sticky="w")
lbl_resin_density.grid_remove()
entry_resin_density.grid_remove()
lbl_impreg_density.grid_remove()
entry_impreg_density.grid_remove()

update_inputs()

btn_calc = ttk.Button(root, text="开始计算", command=calculate)
btn_calc.grid(row=7, column=0, columnspan=3, pady=15)

lbl_result = ttk.Label(root, text="", font=("微软雅黑", 10, "bold"), foreground="blue")
lbl_result.grid(row=8, column=0, columnspan=3, pady=5)

root.mainloop()