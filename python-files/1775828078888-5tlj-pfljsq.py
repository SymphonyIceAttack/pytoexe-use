from tkinter import *
import tkinter.messagebox as messagebox
power_dict = {"油车": 197.5, "电车": 99.7,"油电混动车": 139.4}
def calculate_saving():
    try:
        light_type = entry1.get().strip()  #汽车类型
        hours = entry2.get().strip()  # 行驶路程（千米）
        if not light_type:
            messagebox.showwarning("输入错误", "请输入汽车类型！")
            return
        if not hours.isdigit() or int(hours) < 1:  # 最少1km（1km）
            messagebox.showwarning("输入错误", "行驶距离请输入≥1的数字（千米）！")
            return
        # 获取对应二氧化碳排放量，无匹配则提示
        if light_type not in power_dict:
            messagebox.showwarning("类型错误", f"暂不支持{light_type}，仅支持：{list(power_dict.keys())}")
            return
        power = power_dict[light_type]
        saving = power * int(hours)
        result_label.config(text=f"二氧化碳排放量：{saving:.4f} g\n（{light_type} 行驶 {hours} 千米）")
    except Exception as e:
        messagebox.showerror("计算错误", f"出错了：{str(e)}")
root = Tk()
root.title("汽车二氧化碳排放量计算器")
root.geometry("400x500")
root.resizable(False, False)
try:
    root.iconbitmap("C:\pq.ico")
except Exception as e:
    messagebox.showinfo("提示", f"图标加载失败：{str(e)}\n程序将继续运行")
Label(root, text="排放量计算", font=("微软雅黑", 14, "bold")).pack(pady=10)
Label(root, text="输入家里车辆类型（如油车，电车等）").pack(pady=5)
entry1 = Entry(root, width=20)
entry1.pack(pady=5)
Label(root, text="行驶距离（最少1千米，输入数字）").pack(pady=5)
entry2 = Entry(root, width=20)
entry2.pack(pady=5)
Button(root, text="计算排放量", command=calculate_saving, bg="#4A90E2", fg="white").pack(pady=15)
result_label = Label(root, text="", font=("微软雅黑", 12))
result_label.pack(pady=20)
root.mainloop()