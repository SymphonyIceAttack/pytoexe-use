import math
import tkinter as tk
from tkinter import ttk, Notebook, filedialog, messagebox
import json

# ===================== 材料数据库 =====================
material_data = {
    "6061/6063铝合金": {"HRC0-20": {"carbide":1200, "hss":500}},
    "7075铝合金": {"HRC0-20": {"carbide":800, "hss":350}},
    "紫铜/红铜": {"HRC0-20": {"carbide":350, "hss":150}},
    "黄铜": {"HRC0-20": {"carbide":500, "hss":220}},
    "石墨": {"HRC0-20": {"carbide":1500, "hss":600}},
    "亚克力PMMA": {"HRC0-20": {"carbide":600, "hss":300}},
    "POM赛钢": {"HRC0-20": {"carbide":500, "hss":260}},
    "尼龙PA66": {"HRC0-20": {"carbide":400, "hss":200}},
    "45#钢调质": {
        "HRC20-30": {"carbide":150, "hss":35},
        "HRC30-40": {"carbide":120, "hss":28}
    },
    "Cr12MoV模具钢": {
        "HRC40-50": {"carbide":100, "hss":22},
        "HRC50-60": {"carbide":70, "hss":15}
    },
    "SKD11": {
        "HRC40-50": {"carbide":90, "hss":20},
        "HRC50-60": {"carbide":65, "hss":14}
    },
    "S136": {
        "HRC28-38": {"carbide":110, "hss":26},
        "HRC40-48": {"carbide":85, "hss":19}
    },
    "NAK80": {"HRC38-45": {"carbide":120, "hss":28}},
    "H13热作钢": {
        "HRC42-50": {"carbide":85, "hss":18},
        "HRC50-58": {"carbide":60, "hss":13}
    },
    "304不锈钢": {"HRC18-28": {"carbide":80, "hss":20}},
    "316不锈钢": {"HRC20-30": {"carbide":65, "hss":16}},
    "TC4钛合金": {"HRC30-40": {"carbide":45, "hss":12}},
    "HT200灰铸铁": {"HRC18-28": {"carbide":120, "hss":30}},
    "QT450球墨铸铁": {"HRC25-35": {"carbide":90, "hss":24}},
    "淬火钢HRC50~60": {"HRC50-60": {"carbide":40, "hss":10}},
    "自定义": {"HRC自定义": {"carbide":0, "hss":0}}
}

cooling_data = {"干切":0.7, "乳化液":1.0, "油冷":1.15}
milling_dir_data = {"顺铣":1.1, "逆铣":0.85}

hardness_list = ["HRC0-20","HRC20-30","HRC30-40","HRC40-50","HRC50-60","HRC自定义"]
tool_list = ["平底刀","球刀","圆鼻刀"]
tool_material_list = ["硬质合金刀具","高速钢刀具"]
unit_list = ["mm 公制","inch 英制"]
cooling_list = ["干切","乳化液","油冷"]
milling_dir_list = ["顺铣","逆铣"]

save_data = {}
is_calculating = False

# ===================== 主窗口 =====================
root = tk.Tk()
root.title("CNC全能终极工具箱 V1.0｜专业操机专用")
root.geometry("660x780")
root.resizable(True, True)

nb = Notebook(root)
tab1 = ttk.Frame(nb)
tab2 = ttk.Frame(nb)
tab3 = ttk.Frame(nb)
tab4 = ttk.Frame(nb)
tab5 = ttk.Frame(nb)
tab6 = ttk.Frame(nb)
tab7 = ttk.Frame(nb)
nb.add(tab1, text="切削参数计算")
nb.add(tab2, text="型腔开粗&球刀换算")
nb.add(tab3, text="刀具磨损&刀尖R补偿")
nb.add(tab4, text="圆弧&坐标&分中")
nb.add(tab5, text="攻丝&螺纹&沉头孔")
nb.add(tab6, text="Z向对刀&锥度倒角")
nb.add(tab7, text="方案保存&公英制&G代码")
nb.pack(expand=True, fill="both")

# ===================== Tab1 切削参数 =====================
def update_hardness_list(event):
    mat = mat_var.get()
    keys = list(material_data[mat].keys())
    cb_hard["values"] = keys
    hardness_var.set(keys[0])

def material_select(event):
    mat = mat_var.get()
    update_hardness_list(None)
    refresh_vc(None)

def refresh_vc(event=None):
    mat = mat_var.get()
    hard = hardness_var.get()
    tool_mat = tool_material_var.get()
    cool = cooling_var.get()
    mill_dir = milling_dir_var.get()
    key = "carbide" if tool_mat == "硬质合金刀具" else "hss"
    base_vc = material_data[mat][hard][key]
    vc_val = base_vc * cooling_data[cool] * milling_dir_data[mill_dir]
    entry_Vc.delete(0, tk.END)
    entry_Vc.insert(0, round(vc_val,1))

def mode_switch(event=None):
    mode = mode_var.get()
    if mode == "普通铣削" or mode == "侧铣加工":
        lbl_ap.config(text="切削深度 ap")
        lbl_ae.config(text="切削宽度 ae")
    elif mode == "螺旋下刀":
        lbl_ap.config(text="下刀深度 H")
        lbl_ae.config(text="螺旋角度(°)")
    elif mode == "钻孔计算":
        lbl_ap.config(text="钻孔深度 H")
        lbl_ae.config(text="钻头顶角 2θ(°)")

def unit_switch(event=None):
    unit = unit_var.get()
    if unit.startswith("inch"):
        lbl_D.config(text="刀具直径 D(inch)")
        lbl_ap.config(text="切削深度 ap(inch)")
        lbl_ae.config(text="切削宽度 ae(inch)")
        lbl_L.config(text="切削总长度 L(inch)")
    else:
        lbl_D.config(text="刀具直径 D(mm)")
        lbl_ap.config(text="切削深度 ap(mm)")
        lbl_ae.config(text="切削宽度 ae(mm)")
        lbl_L.config(text="切削总长度 L(mm)")

def calc_load(S, D, F, ap, ae):
    try:
        torque = (0.001 * ap * ae * 250) / (S * D / 1000)
        power = (2 * math.pi * S * torque) / 60000
        load_rate = round(power / 3.75 * 100, 1)
        return power, load_rate
    except:
        return 0, 0

def copy_gcode():
    root.clipboard_clear()
    root.clipboard_append(var_G.get())
    messagebox.showinfo("提示", "G代码已复制到剪贴板")

def calculate():
    global is_calculating
    if is_calculating:
        return
    is_calculating = True
    try:
        D = float(entry_D.get())
        Vc = float(entry_Vc.get())
        z = int(entry_z.get())
        fz = float(entry_fz.get())
        L = float(entry_L.get())
        mode = mode_var.get()
        tool_type = tool_var.get()
        unit = unit_var.get()

        if D <= 0 or z <= 0 or fz <= 0 or L <= 0:
            var_S.set("⚠️ 数值必须大于0")
            return

        if unit.startswith("inch"):
            D *= 25.4
            L *= 25.4

        S = round(1000 * Vc / (math.pi * D), 2)
        F = round(z * fz * S, 2)
        f_per_rev = round(fz * z, 4)
        T_sec = round(L / F * 60, 2)
        T_hour = T_sec / 3600
        pcs_8h = round(8 / T_hour, 0) if T_hour > 0 else 0

        load_color = "black"
        if mode == "普通铣削":
            ap = float(entry_ap.get())
            ae = float(entry_ae.get())
            if unit.startswith("inch"):
                ap *= 25.4
                ae *= 25.4
            Q = round(ap * ae * F / 60, 3)
            Q_min = round(Q*60,2)
            power, load_rate = calc_load(S, D, F, ap, ae)
            if load_rate > 80:
                load_color = "red"
                load_text = f"主轴功率≈{power:.2f}kW，负载≈{load_rate}% ⚠️偏高"
            else:
                load_text = f"主轴功率≈{power:.2f}kW，负载≈{load_rate}%"
            var_Q.set(f"面铣去除率 Q：{Q} cm³/s | {Q_min} cm³/min | {load_text}")
            gcode = f"(材料:{mat_var.get()} S{S} F{F})\nG97 S{S} M03\nG01 F{F}"

        elif mode == "侧铣加工":
            ap = float(entry_ap.get())
            ae = float(entry_ae.get())
            if unit.startswith("inch"):
                ap *= 25.4
                ae *= 25.4
            Q = round(ap * ae * F / 60, 3)
            Q_min = round(Q*60,2)
            power, load_rate = calc_load(S, D, F, ap, ae)
            if load_rate > 80:
                load_color = "red"
                load_text = f"主轴功率≈{power:.2f}kW，负载≈{load_rate}% ⚠️偏高"
            else:
                load_text = f"主轴功率≈{power:.2f}kW，负载≈{load_rate}%"
            var_Q.set(f"侧铣去除率 Q：{Q} cm³/s | {Q_min} cm³/min | {load_text}")
            gcode = f"(材料:{mat_var.get()} S{S} F{F})\nG97 S{S} M03\nG01 F{F}"

        elif mode == "螺旋下刀":
            H = float(entry_ap.get())
            angle = float(entry_ae.get())
            if angle <= 0 or angle >= 90:
                var_S.set("⚠️ 螺旋角度范围 1~89°")
                return
            var_Q.set(f"螺旋下刀深度：{H}，倾角：{angle}°")
            gcode = f"(螺旋下刀，倾角{angle}°)\nG97 S{S} M03\nG01 F{F}"

        elif mode == "钻孔计算":
            H = float(entry_ap.get())
            theta = float(entry_ae.get())
            tip_len = D / (2 * math.tan(math.radians(theta/2)))
            total_dep = H + tip_len
            var_Q.set(f"钻头尖点补偿长度：{round(tip_len,2)} mm")
            gcode = f"(钻孔 S{S} F{F})\nG97 S{S} M03\nG81 R2.0 Z-{total_dep:.2f} F{F}"

        tool_life = "建议加工时长：硬质合金30~120min，高速钢5~20min"
        var_S.set(f"主轴转速 S：{S} r/min")
        var_F.set(f"进给速度 F：{F} mm/min | 每转进给 f：{f_per_rev} mm/转")
        var_T.set(f"单件切削时间：{T_sec} 秒 | 8小时产能≈{pcs_8h} 件 | {tool_life}")
        var_G.set(gcode)
        label_Q.config(foreground=load_color)
    except ValueError:
        var_S.set("⚠️ 请输入正确有效数字！")
        var_F.set("")
        var_Q.set("")
        var_T.set("")
        var_G.set("")
    finally:
        is_calculating = False

def quick_fill_al():
    entry_D.delete(0,tk.END);entry_D.insert(0,"10")
    entry_z.delete(0,tk.END);entry_z.insert(0,"4")
    entry_fz.delete(0,tk.END);entry_fz.insert(0,"0.15")
    entry_ap.delete(0,tk.END);entry_ap.insert(0,"5")
    entry_ae.delete(0,tk.END);entry_ae.insert(0,"5")
    entry_L.delete(0,tk.END);entry_L.insert(0,"100")
    mat_var.set("6061/6063铝合金")
    material_select(None)

def quick_fill_steel():
    entry_D.delete(0,tk.END);entry_D.insert(0,"10")
    entry_z.delete(0,tk.END);entry_z.insert(0,"4")
    entry_fz.delete(0,tk.END);entry_fz.insert(0,"0.08")
    entry_ap.delete(0,tk.END);entry_ap.insert(0,"3")
    entry_ae.delete(0,tk.END);entry_ae.insert(0,"3")
    entry_L.delete(0,tk.END);entry_L.insert(0,"100")
    mat_var.set("45#钢调质")
    material_select(None)

def reset_all():
    for w in [entry_D,entry_Vc,entry_z,entry_fz,entry_ap,entry_ae,entry_L]:
        w.delete(0,tk.END)
    var_S.set("")
    var_F.set("")
    var_Q.set("")
    var_T.set("")
    var_G.set("")

# Tab1布局
unit_var = tk.StringVar(value="mm 公制")
ttk.Label(tab1, text="单位选择：").pack()
cb_unit = ttk.Combobox(tab1, textvariable=unit_var, values=unit_list, state="readonly")
cb_unit.pack()
cb_unit.bind("<<ComboboxSelected>>", unit_switch)

cooling_var = tk.StringVar(value="乳化液")
ttk.Label(tab1, text="冷却方式：").pack()
cb_cool = ttk.Combobox(tab1, textvariable=cooling_var, values=cooling_list, state="readonly")
cb_cool.pack()
cb_cool.bind("<<ComboboxSelected>>", refresh_vc)

milling_dir_var = tk.StringVar(value="顺铣")
ttk.Label(tab1, text="铣削方向：").pack()
cb_mill = ttk.Combobox(tab1, textvariable=milling_dir_var, values=milling_dir_list, state="readonly")
cb_mill.pack()
cb_mill.bind("<<ComboboxSelected>>", refresh_vc)

tool_material_var = tk.StringVar(value="硬质合金刀具")
ttk.Label(tab1, text="刀具材质：").pack()
cb_tool_mat = ttk.Combobox(tab1, textvariable=tool_material_var, values=tool_material_list, state="readonly")
cb_tool_mat.pack()
cb_tool_mat.bind("<<ComboboxSelected>>", refresh_vc)

tool_var = tk.StringVar(value="平底刀")
ttk.Label(tab1, text="刀具类型：").pack()
cb_tool = ttk.Combobox(tab1, textvariable=tool_var, values=tool_list, state="readonly")
cb_tool.pack()

mode_var = tk.StringVar(value="普通铣削")
ttk.Label(tab1, text="加工模式：").pack()
cb_mode = ttk.Combobox(tab1, textvariable=mode_var, values=["普通铣削","侧铣加工","螺旋下刀","钻孔计算"], state="readonly")
cb_mode.pack()
cb_mode.bind("<<ComboboxSelected>>", mode_switch)

mat_var = tk.StringVar(value="6061/6063铝合金")
ttk.Label(tab1, text="加工材料：").pack()
cb_mat = ttk.Combobox(tab1, textvariable=mat_var, values=list(material_data.keys()), width=32, state="readonly")
cb_mat.pack()
cb_mat.bind("<<ComboboxSelected>>", material_select)

hardness_var = tk.StringVar()
ttk.Label(tab1, text="材料硬度 HRC：").pack()
cb_hard = ttk.Combobox(tab1, textvariable=hardness_var, state="readonly")
cb_hard.pack()
cb_hard.bind("<<ComboboxSelected>>", refresh_vc)

frame_quick = ttk.Frame(tab1)
frame_quick.pack(pady=5)
ttk.Button(frame_quick, text="铝件快速填充", command=quick_fill_al).grid(row=0,column=0,padx=5)
ttk.Button(frame_quick, text="钢件快速填充", command=quick_fill_steel).grid(row=0,column=1,padx=5)
ttk.Button(frame_quick, text="重置", command=reset_all).grid(row=0,column=2,padx=5)

frame_in = ttk.LabelFrame(tab1, text="切削参数输入")
frame_in.pack(padx=12, pady=8, fill="x")
row=0
lbl_D = ttk.Label(frame_in, text="刀具直径 D(mm)：")
lbl_D.grid(row=row, column=0, sticky="w")
entry_D = ttk.Entry(frame_in, width=18)
entry_D.grid(row=row, column=1, padx=6, pady=3)
row+=1
ttk.Label(frame_in, text="切削线速度 Vc(m/min)：").grid(row=row, column=0, sticky="w")
entry_Vc = ttk.Entry(frame_in, width=18)
entry_Vc.grid(row=row, column=1, padx=6, pady=3)
row+=1
ttk.Label(frame_in, text="刀具齿数 z：").grid(row=row, column=0, sticky="w")
entry_z = ttk.Entry(frame_in, width=18)
entry_z.grid(row=row, column=1, padx=6, pady=3)
row+=1
ttk.Label(frame_in, text="每齿进给 fz(mm/z)：").grid(row=row, column=0, sticky="w")
entry_fz = ttk.Entry(frame_in, width=18)
entry_fz.grid(row=row, column=1, padx=6, pady=3)
row+=1
lbl_ap = ttk.Label(frame_in, text="切削深度 ap(mm)：")
lbl_ap.grid(row=row, column=0, sticky="w")
entry_ap = ttk.Entry(frame_in, width=18)
entry_ap.grid(row=row, column=1, padx=6, pady=3)
row+=1
lbl_ae = ttk.Label(frame_in, text="切削宽度 ae(mm)：")
lbl_ae.grid(row=row, column=0, sticky="w")
entry_ae = ttk.Entry(frame_in, width=18)
entry_ae.grid(row=row, column=1, padx=6, pady=3)
row+=1
lbl_L = ttk.Label(frame_in, text="切削总长度 L(mm)：")
lbl_L.grid(row=row, column=0, sticky="w")
entry_L = ttk.Entry(frame_in, width=18)
entry_L.grid(row=row, column=1, padx=6, pady=3)

ttk.Button(tab1, text="一键计算切削参数", command=calculate).pack(pady=10)
frame_out = ttk.LabelFrame(tab1, text="计算结果 & G代码 & 主轴负载")
frame_out.pack(padx=12, pady=5, fill="both", expand=True)
var_S = tk.StringVar()
var_F = tk.StringVar()
var_Q = tk.StringVar()
var_T = tk.StringVar()
var_G = tk.StringVar()
label_S = ttk.Label(frame_out, textvariable=var_S, font=("微软雅黑",10))
label_S.pack(anchor="w", padx=5, pady=2)
label_F = ttk.Label(frame_out, textvariable=var_F, font=("微软雅黑",10))
label_F.pack(anchor="w", padx=5, pady=2)
label_Q = ttk.Label(frame_out, textvariable=var_Q, font=("微软雅黑",10))
label_Q.pack(anchor="w", padx=5, pady=2)
label_T = ttk.Label(frame_out, textvariable=var_T, font=("微软雅黑",10))
label_T.pack(anchor="w", padx=5, pady=2)
ttk.Label(frame_out, text="———— G代码 ————", font=("微软雅黑",10)).pack(pady=4)
label_G = ttk.Label(frame_out, textvariable=var_G, font=("Consolas",10))
label_G.pack(anchor="w", padx=5)
ttk.Button(frame_out, text="复制G代码", command=copy_gcode).pack(pady=3)

# ===================== Tab2 型腔开粗&球刀换算 =====================
def cavity_calc():
    try:
        D = float(e_cd.get())
        ap = float(e_cap.get())
        step = float(e_step.get())
        F = float(e_cf.get())
        res_h = D - math.sqrt(D**2 - step**2)
        Q_cav = round(ap * step * F / 60, 3)
        Q_min = round(Q_cav*60,2)
        res_cav.set(f"残余高度≈{res_h:.4f} mm\n型腔去除率：{Q_cav} cm³/s | {Q_min} cm³/min")
    except:
        res_cav.set("输入错误")

def ball_eff_dia():
    try:
        D = float(e_bd.get())
        ap = float(e_bap.get())
        if ap > D/2:
            res_ball.set("⚠️ 切深不能大于球刀半径")
            return
        eff_dia = 2 * math.sqrt(D*ap - ap**2)
        res_ball.set(f"球刀有效切削直径≈{eff_dia:.3f} mm")
    except:
        res_ball.set("输入错误")

ttk.Label(tab2, text="型腔开粗｜行距&残余高度&去除率").pack()
ttk.Label(tab2, text="刀具直径 D：").pack()
e_cd = ttk.Entry(tab2)
e_cd.pack()
ttk.Label(tab2, text="每层切深 ap：").pack()
e_cap = ttk.Entry(tab2)
e_cap.pack()
ttk.Label(tab2, text="切削行距 step：").pack()
e_step = ttk.Entry(tab2)
e_step.pack()
ttk.Label(tab2, text="进给速度 F：").pack()
e_cf = ttk.Entry(tab2)
e_cf.pack()
ttk.Button(tab2, text="型腔开粗计算", command=cavity_calc).pack(pady=8)
res_cav = tk.StringVar()
ttk.Label(tab2, textvariable=res_cav, font=("Consolas",10)).pack()

ttk.Separator(tab2,orient="horizontal").pack(fill="x",pady=10)
ttk.Label(tab2, text="球刀有效切削直径换算").pack()
ttk.Label(tab2, text="球刀直径 D：").pack()
e_bd = ttk.Entry(tab2)
e_bd.pack()
ttk.Label(tab2, text="实际切深 ap：").pack()
e_bap = ttk.Entry(tab2)
e_bap.pack()
ttk.Button(tab2, text="计算有效直径", command=ball_eff_dia).pack(pady=8)
res_ball = tk.StringVar()
ttk.Label(tab2, textvariable=res_ball, font=("Consolas",10)).pack()

# ===================== Tab3 刀具磨损&刀尖R补偿 =====================
def wear_calc():
    try:
        D = float(e_wd.get())
        wear = float(e_wear.get())
        life_h = float(e_life.get())
        comp_val = wear * 2
        wear_rate = wear / life_h
        res_wear.set(f"直径补偿值≈{comp_val:.4f} mm\n每小时单边磨损≈{wear_rate:.4f} mm/h")
    except:
        res_wear.set("输入错误")

def corner_r_comp():
    try:
        D = float(e_rd.get())
        r = float(e_rr.get())
        ap = float(e_rap.get())
        eff_ap = ap - (r - math.sqrt(r**2 - (D/2 - r)**2))
        res_r.set(f"刀尖R实际等效切深≈{eff_ap:.3f} mm")
    except:
        res_r.set("输入错误")

ttk.Label(tab3, text="刀具径向磨损补偿计算").pack()
ttk.Label(tab3, text="刀具原始直径 D：").pack()
e_wd = ttk.Entry(tab3)
e_wd.pack()
ttk.Label(tab3, text="单边磨损量：").pack()
e_wear = ttk.Entry(tab3)
e_wear.pack()
ttk.Label(tab3, text="预估寿命(h)：").pack()
e_life = ttk.Entry(tab3)
e_life.pack()
ttk.Button(tab3, text="计算补偿值", command=wear_calc).pack(pady=8)
res_wear = tk.StringVar()
ttk.Label(tab3, textvariable=res_wear, font=("Consolas",10)).pack()

ttk.Separator(tab3,orient="horizontal").pack(fill="x",pady=10)
ttk.Label(tab3, text="圆鼻刀/球刀 刀尖R等效切深换算").pack()
ttk.Label(tab3, text="刀具直径 D：").pack()
e_rd = ttk.Entry(tab3)
e_rd.pack()
ttk.Label(tab3, text="刀尖圆角 R：").pack()
e_rr = ttk.Entry(tab3)
e_rr.pack()
ttk.Label(tab3, text="名义切深 ap：").pack()
e_rap = ttk.Entry(tab3)
e_rap.pack()
ttk.Button(tab3, text="计算等效切深", command=corner_r_comp).pack(pady=8)
res_r = tk.StringVar()
ttk.Label(tab3, textvariable=res_r, font=("Consolas",10)).pack()

# ===================== Tab4 圆弧&坐标&分中 =====================
def arc_calc():
    try:
        x0 = float(e_x0.get())
        y0 = float(e_y0.get())
        x1 = float(e_x1.get())
        y1 = float(e_y1.get())
        r = float(e_r.get())
        dx = x1 - x0
        dy = y1 - y0
        I = r * dx / math.hypot(dx, dy)
        J = r * dy / math.hypot(dx, dy)
        res_ijk.set(f"I={I:.4f}  J={J:.4f}")
    except:
        res_ijk.set("输入错误")

def polar2xy():
    try:
        r = float(e_pr.get())
        ang = math.radians(float(e_pa.get()))
        x = r * math.cos(ang)
        y = r * math.sin(ang)
        res_xy.set(f"X={x:.4f}  Y={y:.4f}")
    except:
        res_xy.set("输入错误")

def single_edge():
    try:
        pos = float(e_se_pos.get())
        tool_d = float(e_se_d.get())
        work = pos + tool_d/2
        res_se.set(f"工件中心坐标≈{work:.3f}")
    except:
        res_se.set("输入错误")

ttk.Label(tab4, text="圆弧起点 X0 Y0：").pack()
e_x0 = ttk.Entry(tab4, width=10)
e_x0.pack()
e_y0 = ttk.Entry(tab4, width=10)
e_y0.pack()
ttk.Label(tab4, text="圆弧终点 X1 Y1：").pack()
e_x1 = ttk.Entry(tab4, width=10)
e_x1.pack()
e_y1 = ttk.Entry(tab4, width=10)
e_y1.pack()
ttk.Label(tab4, text="圆弧半径 R：").pack()
e_r = ttk.Entry(tab4, width=10)
e_r.pack()
ttk.Button(tab4, text="R → IJK 换算", command=arc_calc).pack(pady=8)
res_ijk = tk.StringVar()
ttk.Label(tab4, textvariable=res_ijk, font=("Consolas",11)).pack()

ttk.Separator(tab4,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab4, text="极坐标 → 直角坐标").pack()
ttk.Label(tab4, text="半径 R：").pack()
e_pr = ttk.Entry(tab4)
e_pr.pack()
ttk.Label(tab4, text="角度(°)：").pack()
e_pa = ttk.Entry(tab4)
e_pa.pack()
ttk.Button(tab4, text="计算XY", command=polar2xy).pack(pady=4)
res_xy = tk.StringVar()
ttk.Label(tab4, textvariable=res_xy, font=("Consolas",11)).pack()

ttk.Separator(tab4,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab4, text="单边分中计算").pack()
ttk.Label(tab4, text="寻边器坐标：").pack()
e_se_pos = ttk.Entry(tab4)
e_se_pos.pack()
ttk.Label(tab4, text="寻边器直径：").pack()
e_se_d = ttk.Entry(tab4)
e_se_d.pack()
ttk.Button(tab4, text="算中心坐标", command=single_edge).pack(pady=4)
res_se = tk.StringVar()
ttk.Label(tab4, textvariable=res_se, font=("Consolas",11)).pack()

# ===================== Tab5 攻丝&螺纹&沉头孔 =====================
def tap_calc():
    try:
        S = float(e_tap_S.get())
        P = float(e_tap_P.get())
        F = S * P
        res_tap.set(f"G84进给 F≈{F:.2f} mm/min")
    except:
        res_tap.set("输入错误")

def thread_calc():
    try:
        d = float(e_td.get())
        p = float(e_tp.get())
        d1 = d - 1.0825*p
        res_thread.set(f"螺纹小径≈{d1:.3f} mm｜推荐底孔≈{round(d1,1)} mm")
    except:
        res_thread.set("输入错误")

def countersink_calc():
    try:
        D = float(e_cs_D.get())
        d = float(e_cs_d.get())
        depth = (D - d) / (2 * math.tan(math.radians(45)))
        res_cs.set(f"90°沉头深度≈{depth:.3f} mm")
    except:
        res_cs.set("输入错误")

ttk.Label(tab5, text="刚性攻丝 G84 计算").pack()
ttk.Label(tab5, text="主轴转速 S：").pack()
e_tap_S = ttk.Entry(tab5)
e_tap_S.pack()
ttk.Label(tab5, text="螺距 P：").pack()
e_tap_P = ttk.Entry(tab5)
e_tap_P.pack()
ttk.Button(tab5, text="计算攻丝进给F", command=tap_calc).pack(pady=4)
res_tap = tk.StringVar()
ttk.Label(tab5, textvariable=res_tap, font=("Consolas",10)).pack()

ttk.Separator(tab5,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab5, text="公制螺纹铣｜大径/螺距").pack()
e_td = ttk.Entry(tab5, width=10)
e_td.pack()
e_tp = ttk.Entry(tab5, width=10)
e_tp.pack()
ttk.Button(tab5, text="算小径&底孔", command=thread_calc).pack(pady=4)
res_thread = tk.StringVar()
ttk.Label(tab5, textvariable=res_thread).pack()

ttk.Separator(tab5,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab5, text="90°沉头孔深度计算").pack()
ttk.Label(tab5, text="沉头大径 D：").pack()
e_cs_D = ttk.Entry(tab5)
e_cs_D.pack()
ttk.Label(tab5, text="底孔直径 d：").pack()
e_cs_d = ttk.Entry(tab5)
e_cs_d.pack()
ttk.Button(tab5, text="计算沉头深度", command=countersink_calc).pack(pady=4)
res_cs = tk.StringVar()
ttk.Label(tab5, textvariable=res_cs, font=("Consolas",10)).pack()

# ===================== Tab6 Z向对刀&锥度倒角 =====================
def z_tool_set():
    try:
        gauge_h = float(e_z_gauge.get())
        read_z = float(e_z_read.get())
        work_z = read_z + gauge_h
        res_z.set(f"工件顶面Z≈{work_z:.3f}")
    except:
        res_z.set("输入错误")

def taper_calc():
    try:
        h = float(e_th.get())
        d1 = float(e_td1.get())
        d2 = float(e_td2.get())
        ang = math.degrees(math.atan((d2-d1)/(2*h)))
        res_taper.set(f"单边斜角≈{ang:.3f}°")
    except:
        res_taper.set("输入错误")

def chamfer_calc():
    try:
        c = float(e_cc.get())
        w = c*1.4142
        res_cham.set(f"45°C角斜面宽度≈{w:.3f} mm")
    except:
        res_cham.set("输入错误")

ttk.Label(tab6, text="Z向对刀高度补偿（对刀块）").pack()
ttk.Label(tab6, text="对刀块高度：").pack()
e_z_gauge = ttk.Entry(tab6)
e_z_gauge.pack()
ttk.Label(tab6, text="机床读取Z值：").pack()
e_z_read = ttk.Entry(tab6)
e_z_read.pack()
ttk.Button(tab6, text="计算工件顶面Z", command=z_tool_set).pack(pady=8)
res_z = tk.StringVar()
ttk.Label(tab6, textvariable=res_z, font=("Consolas",11)).pack()

ttk.Separator(tab6,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab6, text="锥度｜高度/大小端直径").pack()
e_th = ttk.Entry(tab6, width=10)
e_th.pack()
e_td1 = ttk.Entry(tab6, width=10)
e_td1.pack()
e_td2 = ttk.Entry(tab6, width=10)
e_td2.pack()
ttk.Button(tab6, text="算单边角度", command=taper_calc).pack(pady=4)
res_taper = tk.StringVar()
ttk.Label(tab6, textvariable=res_taper, font=("Consolas",10)).pack()

ttk.Separator(tab6,orient="horizontal").pack(fill="x",pady=8)
ttk.Label(tab6, text="45°C角倒角计算").pack()
e_cc = ttk.Entry(tab6)
e_cc.pack()
ttk.Button(tab6, text="算斜面宽度", command=chamfer_calc).pack(pady=4)
res_cham = tk.StringVar()
ttk.Label(tab6, textvariable=res_cham, font=("Consolas",10)).pack()

# ===================== Tab7 方案保存&公英制&G代码 =====================
def save_plan():
    name = e_plan_name.get().strip()
    if not name:
        messagebox.showwarning("提示","请输入方案名称")
        return
    data = {
        "D":entry_D.get(),"Vc":entry_Vc.get(),"z":entry_z.get(),"fz":entry_fz.get(),
        "ap":entry_ap.get(),"ae":entry_ae.get(),"L":entry_L.get(),
        "material":mat_var.get(),"hardness":hardness_var.get(),
        "tool_mat":tool_material_var.get(),"tool_type":tool_var.get(),"mode":mode_var.get(),
        "cooling":cooling_var.get(),"milling_dir":milling_dir_var.get()
    }
    save_data[name] = data
    cb_plan["values"] = list(save_data.keys())
    messagebox.showinfo("成功",f"方案【{name}】已保存")

def load_plan():
    name = plan_var.get()
    if name not in save_data:
        return
    d = save_data[name]
    entry_D.delete(0,tk.END);entry_D.insert(0,d["D"])
    entry_Vc.delete(0,tk.END);entry_Vc.insert(0,d["Vc"])
    entry_z.delete(0,tk.END);entry_z.insert(0,d["z"])
    entry_fz.delete(0,tk.END);entry_fz.insert(0,d["fz"])
    entry_ap.delete(0,tk.END);entry_ap.insert(0,d["ap"])
    entry_ae.delete(0,tk.END);entry_ae.insert(0,d["ae"])
    entry_L.delete(0,tk.END);entry_L.insert(0,d["L"])
    mat_var.set(d["material"])
    material_select(None)
    hardness_var.set(d["hardness"])
    tool_material_var.set(d["tool_mat"])
    tool_var.set(d["tool_type"])
    mode_var.set(d["mode"])
    cooling_var.set(d["cooling"])
    milling_dir_var.set(d["milling_dir"])
    mode_switch(None)

def export_plan():
    try:
        with open("CNC方案备份.json","w",encoding="utf-8") as f:
            json.dump(save_data,f,ensure_ascii=False,indent=2)
        messagebox.showinfo("成功","方案已导出为 CNC方案备份.json")
    except:
        messagebox.showerror("错误","导出失败")

def mm2inch():
    try:
        mm = float(e_mm.get())
        inch = mm/25.4
        res_mi.set(f"{inch:.6f} inch")
    except:
        res_mi.set("错误")

def inch2mm():
    try:
        inch = float(e_inch.get())
        mm = inch*25.4
        res_im.set(f"{mm:.4f} mm")
    except:
        res_im.set("错误")

# 方案
ttk.Label(tab7, text="自定义加工方案保存/调用/导出").pack()
e_plan_name = ttk.Entry(tab7, width=20)
e_plan_name.pack()
frame_plan = ttk.Frame(tab7)
frame_plan.pack(pady=3)
ttk.Button(frame_plan, text="保存当前方案", command=save_plan).grid(row=0,column=0,padx=3)
ttk.Button(frame_plan, text="导出全部方案", command=export_plan).grid(row=0,column=1,padx=3)
plan_var = tk.StringVar()
cb_plan = ttk.Combobox(tab7, textvariable=plan_var, width=20, state="readonly")
cb_plan.pack()
ttk.Button(tab7, text="加载选中方案", command=load_plan).pack(pady=3)

# 公英制
ttk.Label(tab7, text="公英制换算").pack()
e_mm = ttk.Entry(tab7, width=12)
e_mm.pack()
ttk.Button(tab7, text="mm → inch", command=mm2inch).pack()
res_mi = tk.StringVar()
ttk.Label(tab7, textvariable=res_mi).pack()

e_inch = ttk.Entry(tab7, width=12)
e_inch.pack()
ttk.Button(tab7, text="inch → mm", command=inch2mm).pack()
res_im = tk.StringVar()
ttk.Label(tab7, textvariable=res_im).pack()

# G代码
g_text = """
通用标准加工模板：
G54 G90 G17 G40 G80
G00 X0. Y0.
G43 Z50.0 H01
S____ M03
G01 Z-___ F___
G81 R2.0 Z-___ F___
G00 Z50.
M05
M30
"""
ttk.Label(tab7, text="常用G代码模板").pack()
tk.Text(tab7, height=10, width=48, font=("Consolas",9)).insert("end", g_text).pack()

# 初始化
material_select(None)
root.mainloop()