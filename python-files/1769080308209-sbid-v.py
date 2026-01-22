Python 3.14.0 (tags/v3.14.0:ebf955d, Oct  7 2025, 10:15:03) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import tkinter as tk
from math import pi

# دالة حساب الوزن
def calculate_weight():
    shape = shape_var.get()
    density = float(density_entry.get())  # الكثافة
    diameter = float(diameter_entry.get()) / 1000  # mm -> m
    length = float(length_entry.get()) / 1000      # mm -> m

    if shape == "قضيب":
        weight = pi * (diameter/2)**2 * length * density
    else:  # ماسورة
        inner_diameter = float(inner_diameter_entry.get()) / 1000
        weight = pi * ((diameter**2 - inner_diameter**2)/4) * length * density
    
    weight_label.config(text=f"الوزن: {weight:.3f} كجم")
    return weight

# دالة حساب التكلفة
def calculate_cost():
    weight = calculate_weight()
    price_per_kg = float(price_entry.get())
    time_minutes = float(time_entry.get())
    cost_per_hour = float(cost_hour_entry.get())
    tool_cost = float(tool_entry.get())
    waste_percent = float(waste_entry.get()) / 100

    cost_material = weight * price_per_kg
    cost_waste = cost_material * waste_percent
    cost_time = time_minutes * (cost_per_hour/60)
    total_cost = cost_material + cost_waste + cost_time + tool_cost

    cost_label.config(text=f"إجمالي تكلفة القطعة: {total_cost:.2f} جنيه")

# واجهة المستخدم
root = tk.Tk()
root.title("برنامج حساب تكلفة القطعة - مصنع تشكيل معادن")

# المتغيرات
shape_var = tk.StringVar(value="قضيب")

# المدخلات
tk.Label(root, text="شكل الخامة:").grid(row=0, column=0)
tk.OptionMenu(root, shape_var, "قضيب", "ماسورة").grid(row=0, column=1)

tk.Label(root, text="الكثافة (kg/m3):").grid(row=1, column=0)
... density_entry = tk.Entry(root); density_entry.grid(row=1, column=1); density_entry.insert(0,"7850")
... 
... tk.Label(root, text="القطر الخارجي (مم):").grid(row=2, column=0)
... diameter_entry = tk.Entry(root); diameter_entry.grid(row=2, column=1)
... 
... tk.Label(root, text="القطر الداخلي (مم) - للماسورة:").grid(row=3, column=0)
... inner_diameter_entry = tk.Entry(root); inner_diameter_entry.grid(row=3, column=1)
... 
... tk.Label(root, text="الطول (مم):").grid(row=4, column=0)
... length_entry = tk.Entry(root); length_entry.grid(row=4, column=1)
... 
... tk.Label(root, text="سعر الكيلو (جنيه):").grid(row=5, column=0)
... price_entry = tk.Entry(root); price_entry.grid(row=5, column=1)
... 
... tk.Label(root, text="زمن التشغيل (دقيقة):").grid(row=6, column=0)
... time_entry = tk.Entry(root); time_entry.grid(row=6, column=1)
... 
... tk.Label(root, text="تكلفة الساعة (جنيه):").grid(row=7, column=0)
... cost_hour_entry = tk.Entry(root); cost_hour_entry.grid(row=7, column=1)
... 
... tk.Label(root, text="تكلفة العدة (جنيه):").grid(row=8, column=0)
... tool_entry = tk.Entry(root); tool_entry.grid(row=8, column=1)
... 
... tk.Label(root, text="نسبة الهالك (%):").grid(row=9, column=0)
... waste_entry = tk.Entry(root); waste_entry.grid(row=9, column=1)
... 
... # أزرار ونتيجة
... tk.Button(root, text="حساب", command=calculate_cost).grid(row=10, column=0, columnspan=2)
... 
... weight_label = tk.Label(root, text="الوزن: ")
... weight_label.grid(row=11, column=0, columnspan=2)
... 
... cost_label = tk.Label(root, text="إجمالي تكلفة القطعة: ")
... cost_label.grid(row=12, column=0, columnspan=2)
... 
... root.mainloop()
