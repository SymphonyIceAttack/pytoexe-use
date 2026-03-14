# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

# 国标型钢库
h_section = {
    "H100×100": (100,100,6,8), "H150×150":(150,150,7,10),
    "H200×200":(200,200,8,12), "H250×250":(250,250,9,14),
    "H300×300":(300,300,10,15), "H350×350":(350,350,12,19)
}
i_beam = {
    "10#":(100,68,4.5,7.6), "12#":(120,74,5.0,8.4),
    "14#":(140,80,5.5,9.1), "16#":(160,88,6.0,9.9),
    "18#":(180,94,6.5,10.7), "20#":(200,100,7.0,11.4)
}
channel = {
    "5#":(50,37,4.5,7.0), "6.3#":(63,40,4.8,7.5),
    "8#":(80,43,5.0,8.0), "10#":(100,48,5.3,8.5),
    "12#":(120,53,5.5,9.0), "14#":(140,58,6.0,9.5)
}
square_pipe = {
    "20×20":(20,2), "30×30":(30,2.5), "40×40":(40,3),
    "50×50":(50,3), "60×60":(60,3.5), "80×80":(80,4), "100×100":(100,4)
}
round_pipe = {
    "Φ25":(25,2), "Φ32":(32,2.5), "Φ42":(42,3),
    "Φ48":(48,3), "Φ60":(60,3.5), "Φ89":(89,4), "Φ114":(114,4)
}

all_items = []
total_weight_sum = 0.0
total_price_sum = 0.0

root = tk.Tk()
root.title("钢架重量单价计算器 — 工程专用版")
root.geometry("720x650")

def update_model(*args):
    typ = type_var.get()
    if typ == "钢板":
        model_combo.config(values=["手动输入"])
    elif typ == "H型钢":
        model_combo.config(values=list(h_section.keys()))
    elif typ == "工字钢":
        model_combo.config(values=list(i_beam.keys()))
    elif typ == "槽钢":
        model_combo.config(values=list(channel.keys()))
    elif typ == "方管":
        model_combo.config(values=list(square_pipe.keys()))
    elif typ == "圆管":
        model_combo.config(values=list(round_pipe.keys()))

def calc_single():
    try:
        typ = type_var.get()
        model = model_var.get()
        length = float(length_entry.get())
        price_per_ton = float(price_entry.get())
        loss = float(loss_entry.get())
        kg = 0.0

        if typ == "钢板":
            w = float(w_entry.get())
            t = float(t_entry.get())
            kg = length * (w/1000) * t * 7.85
        elif typ == "H型钢":
            H,B,t1,t2 = h_section[model]
            per_m = (H*t1 + 2*B*t2 - 2*t1*t2) * 7.85 / 1000
            kg = per_m * length
        elif typ == "工字钢":
            h,b,d,t = i_beam[model]
            per_m = (h*d + 2*t*(b-d) + 0.615*t*t) * 7.85 /1000
            kg = per_m * length
        elif typ == "槽钢":
            h,b,d,t = channel[model]
            per_m = (h*d + 2*t*(b-d) + 0.449*t*t)*7.85/1000
            kg = per_m * length
        elif typ == "方管":
            a,t = square_pipe[model]
            per_m = 4*t*(a-t)*7.85/1000
            kg = per_m * length
        elif typ == "圆管":
            d,t = round_pipe[model]
            per_m = 3.1416*t*(d-t)*7.85/1000
            kg = per_m * length

        kg *= loss
        ton = kg/1000
        total = ton * price_per_ton
        kg_var.set(f"{kg:.2f} kg")
        ton_var.set(f"{ton:.4f} t")
        total_var.set(f"{total:.2f} 元")
        return typ, model, length, price_per_ton, kg, ton, total
    except:
        messagebox.showerror("错误","输入不正确")
        return None

def add_to_list():
    res = calc_single()
    if not res: return
    typ, model, length, price_t, kg, ton, total = res
    all_items.append({
        "类型":typ,"型号":model,"长度(m)":length,
        "单价(元/吨)":price_t,"重量(kg)":round(kg,2),
        "重量(吨)":round(ton,4),"总价(元)":round(total,2)
    })
    global total_weight_sum, total_price_sum
    total_weight_sum += ton
    total_price_sum += total
    list_box.delete(0,tk.END)
    for i,item in enumerate(all_items,1):
        list_box.insert(tk.END,
            f"{i:2d} | {item['类型']}{item['型号']} 长{item['长度(m)']}m | {item['重量(吨)']:.3f}t | ￥{item['总价(元)']:.2f}")
    sum_ton_var.set(f"{total_weight_sum:.3f} t")
    sum_price_var.set(f"{total_price_sum:.2f} 元")

def export_excel():
    if not all_items:
        messagebox.showwarning("提示","无数据")
        return
    df = pd.DataFrame(all_items)
    df.loc["合计"] = {"类型":"合计","型号":"-","长度(m)":"-","单价(元/吨)":"-",
                      "重量(kg)":round(total_weight_sum*1000,2),
                      "重量(吨)":round(total_weight_sum,3),
                      "总价(元)":round(total_price_sum,2)}
    df.to_excel("钢架报价单.xlsx",index=False)
    messagebox.showinfo("成功","已导出 钢架报价单.xlsx")

def clear_all():
    global all_items,total_weight_sum,total_price_sum
    all_items=[]
    total_weight_sum=0
    total_price_sum=0
    list_box.delete(0,tk.END)
    sum_ton_var.set("0.000 t")
    sum_price_var.set("0.00 元")

# 界面
tk.Label(root,text="钢材类型：").grid(row=0,column=0,pad=5,pady=8)
type_var=tk.StringVar()
type_combo=ttk.Combobox(root,textvariable=type_var,values=["钢板","H型钢","工字钢","槽钢","方管","圆管"],width=12)
type_combo.grid(row=0,column=1,pady=8)
type_combo.bind("<<ComboboxSelected>>",update_model)

tk.Label(root,text="国标型号：").grid(row=0,column=2,pad=5,pady=8)
model_var=tk.StringVar()
model_combo=ttk.Combobox(root,textvariable=model_var,width=12)
model_combo.grid(row=0,column=3,pady=8)

tk.Label(root,text="长度(m)：").grid(row=1,column=0,pad=5,pady=8)
length_entry=tk.Entry(root)
length_entry.grid(row=1,column=1,pady=8)

tk.Label(root,text="单价(元/吨)：").grid(row=1,column=2,pad=5,pady=8)
price_entry=tk.Entry(root)
price_entry.grid(row=1,column=3,pady=8)

tk.Label(root,text="损耗系数：").grid(row=2,column=0,pad=5,pady=8)
loss_entry=tk.Entry(root)
loss_entry.insert(0,"1.03")
loss_entry.grid(row=2,column=1,pady=8)

tk.Label(root,text="钢板宽(mm)：").grid(row=2,column=2,pad=5,pady=8)
w_entry=tk.Entry(root)
w_entry.grid(row=2,column=3,pady=8)

tk.Label(root,text="钢板厚(mm)：").grid(row=3,column=2,pad=5,pady=8)
t_entry=tk.Entry(root)
t_entry.grid(row=3,column=3,pady=8)

kg_var=tk.StringVar(value="0.00 kg")
ton_var=tk.StringVar(value="0.0000 t")
total_var=tk.StringVar(value="0.00 元")

tk.Label(root,text="单重：",font=("",11)).grid(row=4,column=0,pady=10)
tk.Label(root,textvariable=kg_var,font=("",11)).grid(row=4,column=1,pady=10)
tk.Label(root,textvariable=ton_var,font=("",11)).grid(row=4,column=2,pady=10)
tk.Label(root,textvariable=total_var,font=("",11,"bold"),fg="red").grid(row=4,column=3,pady=10)

tk.Button(root,text="计算",command=calc_single,width=10,bg="#4CAF50",fg="white").grid(row=5,column=1,pady=10)
tk.Button(root,text="加入清单",command=add_to_list,width=10,bg="#2196F3",fg="white").grid(row=5,column=2,pady=10)

tk.Label(root,text="构件清单",font=("",12,"bold")).grid(row=6,column=0,columnspan=4,pady=5)
list_box=tk.Listbox(root,width=90,height=12)
list_box.grid(row=7,column=0,columnspan=4,pad=10)

sum_ton_var=tk.StringVar(value="0.000 t")
sum_price_var=tk.StringVar(value="0.00 元")

tk.Label(root,text="总重量：",font=("",12,"bold")).grid(row=8,column=1,pady=10)
tk.Label(root,textvariable=sum_ton_var,font=("",12,"bold")).grid(row=8,column=2,pady=10)

tk.Label(root,text="总造价：",font=("",12,"bold")).grid(row=9,column=1,pady=10)
tk.Label(root,textvariable=sum_price_var,font=("",12,"bold"),fg="red").grid(row=9,column=2,pady=10)

tk.Button(root,text="导出Excel",command=export_excel,width=12,bg="#FF9800",fg="white").grid(row=10,column=1,pady=10)
tk.Button(root,text="清空清单",command=clear_all,width=12,bg="#f44336",fg="white").grid(row=10,column=2,pady=10)

root.mainloop()