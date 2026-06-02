import tkinter as tk
from tkinter import ttk, messagebox
import math
from PIL import Image, ImageTk
import requests
from io import BytesIO

root = tk.Tk()
root.title("一莫跨境｜TikTok东南亚选品利润测算器")
root.geometry("820x720")
root.resizable(False, False)
root.configure(bg="#ffffff")

# ====== 1、加载一莫跨境LOGO ======
try:
    # 你的logo在线图源
    logo_url = "https://p3-flow-image-sign.douyinpic.com/ocean-cloud-tos/9a24f130903c493899d39d9909191311~tplv-a9rns2rl98-image.image"
    resp = requests.get(logo_url)
    img = Image.open(BytesIO(resp.content)).resize((120,120))
    photo = ImageTk.PhotoImage(img)
    lab_logo = tk.Label(root, image=photo, bg="#fff")
    lab_logo.image = photo
    lab_logo.pack(pady=(8,0))
except:
    pass

# 品牌标题
tk.Label(root,text="山东一莫跨境｜TikTok新加坡选品核算",font=("黑体",16,"bold"),bg="#fff",fg="#002080").pack(pady=5)

# ========== 变量区（默认和你原图参数一致）==========
# 输入
var_cost_cny = tk.DoubleVar(value=10.0)    #采购价CNY
var_weight_g = tk.DoubleVar(value=20.0)     #重量g
var_show_sgd = tk.DoubleVar(value=12.18)   #前台原价SGD
var_discount = tk.DoubleVar(value=5)        #折扣 5折

#费率配置（和你截图模板一致）
var_ex = tk.DoubleVar(value=0.19)        #汇率1CNY=SGD
var_rate_plat = tk.DoubleVar(value=6.54) #佣金%
var_rate_deal = tk.DoubleVar(value=3.27) #交易手续费%
var_rate_tax = tk.DoubleVar(value=9.0)   #消费税%
var_rate_with = tk.DoubleVar(value=1.0)  #提现%
var_other_cny = tk.DoubleVar(value=6.0)  #其他杂费CNY

#新加坡尾程运费：首重40g=0.98SGD，续重每10g+0.15SGD
first_g = 40
first_sgd = 0.98
add_10g_sgd = 0.15

#结果变量
var_off_sgd = tk.StringVar()    #折后售价
var_ship_cny = tk.StringVar()   #尾程运费CNY
var_fee_total_cny = tk.StringVar() #平台总费用CNY
var_income_cny = tk.StringVar() #回款CNY
var_profit_cny = tk.StringVar() #利润
var_status = tk.StringVar("待计算")

# ========== 计算函数 ==========
def calc():
    try:
        cost = var_cost_cny.get()
        w = var_weight_g.get()
        show = var_show_sgd.get()
        disc = var_discount.get()
        ex = var_ex.get()

        #1 折后售价
        off_price = show * disc /10
        var_off_sgd.set(f"{off_price:.2f} SGD")

        #2 尾程运费SGD→CNY
        if w <= first_g:
            ship_sgd = first_sgd
        else:
            over = w - first_g
            cnt = math.ceil(over/10)
            ship_sgd = first_sgd + cnt*add_10g_sgd
        ship_cny = ship_sgd / ex
        var_ship_cny.set(f"{ship_cny:.2f} CNY")

        #3平台各项费用（以折后售价为基数）
        fee1 = off_price * var_rate_plat.get()/100
        fee2 = off_price * var_rate_deal.get()/100
        fee3 = off_price * var_rate_tax.get()/100
        fee4 = off_price * var_rate_with.get()/100
        all_fee_sgd = fee1+fee2+fee3+fee4
        all_fee_cny = all_fee_sgd/ex
        var_fee_total_cny.set(f"{all_fee_cny:.2f} CNY")

        #4总收入CNY
        in_cny = off_price/ex
        var_income_cny.set(f"{in_cny:.2f} CNY")

        #5总成本
        total_cost = cost + ship_cny + all_fee_cny + var_other_cny.get()
        profit = in_cny - total_cost
        var_profit_cny.set(f"{profit:.2f} CNY")

        #盈亏变色
        if profit>0:
            var_status.set("✅盈利")
            lab_p.config(fg="#009900")
            lab_st.config(fg="#009900")
        elif profit<0:
            var_status.set("❌亏损")
            lab_p.config(fg="#dd0000")
            lab_st.config(fg="#dd0000")
        else:
            var_status.set("⚪保本")
            lab_p.config(fg="#333333")
            lab_st.config(fg="#333333")
    except:
        messagebox.showerror("错误","请输入纯数字！")

#重置
def reset():
    var_cost_cny.set(10.0)
    var_weight_g.set(20)
    var_show_sgd.set(12.18)
    var_discount.set(5)
    var_off_sgd.set("")
    var_ship_cny.set("")
    var_fee_total_cny.set("")
    var_income_cny.set("")
    var_profit_cny.set("")
    var_status.set("待计算")
    lab_p.config(fg="#333")
    lab_st.config(fg="#333")

# ========== UI布局 ==========
#输入区
frm_in = ttk.LabelFrame(root,text="【选品录入区】仅填4项数据",padding=12)
frm_in.pack(fill="x",padx=20,pady=6)

row1=ttk.Frame(frm_in)
row1.pack(fill="x",pady=4)
ttk.Label(row1,text="采购成本(CNY):",width=14).pack(side="left")
ttk.Entry(row1,textvariable=var_cost_cny,width=12).pack(side="left",padx=3)
ttk.Label(row1,text="包裹重量(g):",width=14).pack(side="left",padx=12)
ttk.Entry(row1,textvariable=var_weight_g,width=12).pack(side="left")

row2=ttk.Frame(frm_in)
row2.pack(fill="x",pady=4)
ttk.Label(row2,text="前台标价(SGD):",width=14).pack(side="left")
ttk.Entry(row2,textvariable=var_show_sgd,width=12).pack(side="left",padx=3)
ttk.Label(row2,text="折扣(几折，例5=5折):",width=16).pack(side="left",padx=12)
ttk.Entry(row2,textvariable=var_discount,width=12).pack(side="left")

#按钮
frm_btn=ttk.Frame(root)
frm_btn.pack(pady=8)
ttk.Button(frm_btn,text="一键核算利润",command=calc,width=16).pack(side="left",padx=12)
ttk.Button(frm_btn,text="重置清空",command=reset,width=16).pack(side="left")

#结果区
frm_res=ttk.LabelFrame(root,text="【核算结果明细】",padding=12)
frm_res.pack(fill="x",padx=20,pady=6)

r1=ttk.Frame(frm_res)
r1.pack(fill="x",pady=3)
ttk.Label(r1,text="折后售价:",width=16).pack(side="left")
ttk.Label(r1,textvariable=var_off_sgd,font=("",10,"bold")).pack(side="left")
ttk.Label(r1,text="尾程运费(CNY):",width=16,padx=15).pack(side="left")
ttk.Label(r1,textvariable=var_ship_cny,font=("",10,"bold")).pack(side="left")

r2=ttk.Frame(frm_res)
r2.pack(fill="x",pady=3)
ttk.Label(r2,text="平台总费用(CNY):",width=16).pack(side="left")
ttk.Label(r2,textvariable=var_fee_total_cny,font=("",10,"bold")).pack(side="left")
ttk.Label(r2,text="折后回款(CNY):",width=16,padx=15).pack(side="left")
ttk.Label(r2,textvariable=var_income_cny,font=("",10,"bold")).pack(side="left")

r3=ttk.Frame(frm_res)
r3.pack(fill="x",pady=6)
ttk.Label(r3,text="单件纯利润:",width=16).pack(side="left")
lab_p=ttk.Label(r3,textvariable=var_profit_cny,font=("",12,"bold"))
lab_p.pack(side="left")
ttk.Label(r3,text="盈亏状态:",width=16,padx=15).pack(side="left")
lab_st=ttk.Label(r3,textvariable=var_status,font=("",12,"bold"))
lab_st.pack(side="left")

#费率配置区
frm_set=ttk.LabelFrame(root,text="【费率参数设置（可按需修改）】",padding=10)
frm_set.pack(fill="x",padx=20,pady=6)
s1=ttk.Frame(frm_set)
s1.pack(fill="x",pady=3)
ttk.Label(s1,text="汇率1CNY=SGD:",width=13).pack(side="left")
ttk.Entry(s1,textvariable=var_ex,width=8).pack(side="left")
ttk.Label(s1,text="佣金%:",width=8,padx=6).pack(side="left")
ttk.Entry(s1,textvariable=var_rate_plat,width=7).pack(side="left")
ttk.Label(s1,text="手续费%:",width=9,padx=6).pack(side="left")
ttk.Entry(s1,textvariable=var_rate_deal,width=7).pack(side="left")
ttk.Label(s1,text="消费税%:",width=9,padx=6).pack(side="left")
ttk.Entry(s1,textvariable=var_rate_tax,width=7).pack(side="left")
ttk.Label(s1,text="提现%:",width=7,padx=6).pack(side="left")
ttk.Entry(s1,textvariable=var_rate_with,width=7).pack(side="left")

s2=ttk.Frame(frm_set)
s2.pack(fill="x",pady=3)
ttk.Label(s2,text="其他杂费CNY:",width=13).pack(side="left")
ttk.Entry(s2,textvariable=var_other_cny,width=8).pack(side="left")

#底部备注
tk.Label(root,text="山东一莫跨境 | TikTok选品专用测算工具",bg="#fff",fg="#224499",font=("",9)).pack(pady=12)

root.mainloop()