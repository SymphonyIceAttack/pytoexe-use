from tkinter import *
import tkinter.messagebox as messagebox
power_dict = {"LED灯": 0.005, "白炽灯": 0.05,"荧光灯": 0.014}
def calculate_saving():
    try:
        light_type = entry1.get().strip()
        hours = entry2.get().strip()  
        if not light_type:
            messagebox.showwarning("输入错误", "请输入灯具类型！")
            return
        if not hours.isdigit() or int(hours) < 24:  # 最少1天（24小时）
            messagebox.showwarning("输入错误", "关灯时长请输入≥24的数字（小时）！")
            return
        if light_type not in power_dict:
            messagebox.showwarning("类型错误", f"暂不支持{light_type}，仅支持：{list(power_dict.keys())}")
            return
        power = power_dict[light_type]
        saving = power * int(hours)
        result_label.config(text=f"节电度数：{saving:.4f} 度\n（{light_type} 关闭 {hours} 小时）")
    except Exception as e:
        messagebox.showerror("计算错误", f"出错了：{str(e)}")
root = Tk()
root.title("节能助手")
root.geometry("300x500")
root.resizable(False, False)
try:
    root.iconbitmap("C:\icon (3).ico")
except Exception as e:
    messagebox.showinfo("提示", f"图标加载失败：{str(e)}\n程序将继续运行")
Label(root, text="用电计算", font=("微软雅黑", 14, "bold")).pack(pady=10)
Label(root, text="输入家里灯具类型（如LED灯，白炽灯等）").pack(pady=5)
entry1 = Entry(root, width=20)
entry1.pack(pady=5)
Label(root, text="关灯时长（最少24小时，输入数字）").pack(pady=5)
entry2 = Entry(root, width=20)
entry2.pack(pady=5)
Button(root, text="计算节电度数", command=calculate_saving, bg="#4A90E2", fg="white").pack(pady=15)
result_label = Label(root, text="", font=("微软雅黑", 12))
result_label.pack(pady=20)
root.mainloop()