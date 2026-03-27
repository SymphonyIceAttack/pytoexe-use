import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox
import math

def L_eq(l2D, h, d, n, a):
    t1 = math.log(2 * (h + 0.1) / a)
    t2 = (2 * (h + 0.1)) / (1.15 * (n ** 0.57) * d)
    t3 = ((n - 1) / 2) * math.log(1 + t2 ** 2)
    return (l2D / (5 * n)) * (t1 + t3)

def M_eq(l2D, h, d, n, a):
    t = (2 * (h + 0.1)) / (1.15 * (n ** 0.57) * d)
    return (l2D / 10) * math.log(1 + t ** 2)

def C_c(l3D, d, n, a, er):
    t1 = 1.6 * n - 0.54
    t2 = math.log(4 * n * n) / math.log(4 * n * n * n)
    t3 = (8.854 * math.pi * er) / (1000 * math.log(d / a))
    return t1 * t2 * t3 * l3D

root = tk.Tk()
root.title("射频计算器")
root.geometry("600x400")

tab = ttk.Notebook(root)
t1 = ttk.Frame(tab)
t2 = ttk.Frame(tab)
t3 = ttk.Frame(tab)
tab.add(t1, text="L_eq")
tab.add(t2, text="M_eq")
tab.add(t3, text="C_c")
tab.pack(expand=1, fill="both", padx=10, pady=10)

def calc1():
    try:
        v = L_eq(float(i1[0].get()),float(i1[1].get()),float(i1[2].get()),float(i1[3].get()),float(i1[4].get()))
        o1.config(text=f"结果：{v:.6e} H")
    except: tkinter.messagebox.showerror("错误","输入有效数字")
def calc2():
    try:
        v = M_eq(float(i2[0].get()),float(i2[1].get()),float(i2[2].get()),float(i2[3].get()),float(i2[4].get()))
        o2.config(text=f"结果：{v:.6e} H")
    except: tkinter.messagebox.showerror("错误","输入有效数字")
def calc3():
    try:
        v = C_c(float(i3[0].get()),float(i3[1].get()),float(i3[2].get()),float(i3[3].get()),float(i3[4].get()))
        o3.config(text=f"结果：{v:.4f} pF")
    except: tkinter.messagebox.showerror("错误","输入有效数字")

for f,func,names,out in [(t1,calc1,["l2D","h","d","n","a"],None),(t2,calc2,["l2D","h","d","n","a"],None),(t3,calc3,["l3D","d","n","a","er"],None)]:
    fr = tk.Frame(f)
    fr.pack(pady=10)
    ens = []
    for i,n in enumerate(names):
        tk.Label(fr,text=n).grid(row=i//2,column=(i%2)*2,padx=4,pady=3)
        e = tk.Entry(fr,width=10)
        e.grid(row=i//2,column=(i%2)*2+1,padx=4,pady=3)
        ens.append(e)
    ol = tk.Label(f,text="结果：")
    ol.pack(pady=5)
    tk.Button(f,text="计算",command=func).pack()
    if f==t1:i1,o1=ens,ol
    elif f==t2:i2,o2=ens,ol
    else:i3,o3=ens,ol

root.mainloop()