import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import math
import os

# ---------- 尺寸数据 ----------
# 螺栓规格 -> (内切圆直径, 头部厚度)
BOLT_HEADS = {
    "M6": (10, 4), "M8": (13, 5.3), "M10": (16, 6.4), "M12": (18, 7.5),
    "M14": (21, 8.8), "M16": (24, 10), "M18": (27, 11.5), "M20": (30, 12.5),
    "M22": (22, 14), "M24": (36, 15), "M30": (46, 18.7), "M36": (55, 22.5),
    "M42": (65, 26), "M48": (75, 30), "M56": (85, 35), "M64": (95, 40)
}
# 螺母规格 -> (内切圆直径, 厚度)
NUTS = {
    "M6": (10, 5.2), "M8": (13, 6.8), "M10": (16, 8.4), "M12": (18, 10.8),
    "M14": (21, 12.8), "M16": (24, 14.8), "M18": (27, 15.8), "M20": (30, 18),
    "M22": (34, 19.4), "M24": (36, 21.5), "M30": (46, 25.6), "M36": (55, 31),
    "M42": (65, 34), "M48": (75, 38), "M56": (85, 45), "M64": (95, 51)
}
# 平垫片规格 -> (直径, 厚度)
WASHERS = {
    "M6": (12, 1.6), "M8": (16, 1.6), "M10": (20, 2), "M12": (24, 2.5),
    "M14": (28, 2.5), "M16": (30, 3), "M18": (34, 3), "M20": (37, 3),
    "M22": (39, 3), "M24": (44, 4), "M30": (56, 4), "M36": (66, 5),
    "M42": (78, 8), "M48": (92, 8), "M56": (105, 10), "M64": (115, 10)
}
# 弹簧垫片规格 -> (直径, 厚度)
SPRINGS = {
    "M6": (11, 1.6), "M8": (14.5, 2.1), "M10": (17.5, 2.6), "M12": (21, 3.1),
    "M14": (24, 3.6), "M16": (27, 4.1), "M18": (30, 4.5), "M20": (33, 5.0),
    "M22": (36, 5.5), "M24": (39, 6.0), "M30": (48, 7.5), "M36": (56, 8.5),
    "M42": (63, 9.5), "M48": (72, 11), "M56": (85, 12), "M64": (95, 15)  # M56/M64 未提供，按比例估算
}
# 螺栓公称直径（用于杆径）
BOLT_DIAM = {
    "M6": 6, "M8": 8, "M10": 10, "M12": 12, "M14": 14, "M16": 16,
    "M18": 18, "M20": 20, "M22": 22, "M24": 24, "M30": 30, "M36": 36,
    "M42": 42, "M48": 48, "M56": 56, "M64": 64
}

# ---------- 辅助函数 ----------
def calc_circ_diam(hex_diam):
    """由内切圆直径计算外接圆直径（保留1位小数）"""
    return round(hex_diam / math.cos(math.radians(30)), 1)

def generate_script(bolt_spec, t, L):
    """生成完整的脚本字符串"""
    # 提取尺寸
    d_hex, h_head = BOLT_HEADS[bolt_spec]
    d_nut_hex, h_nut = NUTS[bolt_spec]
    d_washer, h_washer = WASHERS[bolt_spec]
    d_spring, h_spring = SPRINGS[bolt_spec]
    d_shank = BOLT_DIAM[bolt_spec]          # 杆径（公称直径）
    
    # 外接圆直径
    D_head = calc_circ_diam(d_hex)
    D_nut = calc_circ_diam(d_nut_hex)
    R_head = D_head / 2
    R_nut = D_nut / 2
    r_head = d_hex / 2                      # 内切圆半径
    r_nut = d_nut_hex / 2
    
    # 计算各部件Z坐标（头部底面在Z=0，向下为负）
    # 上平垫片
    z_washer1_center = -h_washer / 2
    # 下平垫片
    z_washer2_center = -h_washer - t - h_washer / 2
    # 弹簧垫片
    z_spring_center = -h_washer - t - h_washer - h_spring / 2
    # 螺母
    z_nut_center = -h_washer - t - h_washer - h_spring - h_nut / 2
    # 螺母底面（用于拉伸起始）
    z_nut_bottom = -h_washer - t - h_washer - h_spring - h_nut
    # 螺栓杆中心
    z_shank_center = -L / 2
    
    # 日期时间
    now = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    
    # 构建脚本
    lines = []
    lines.append("$S-  -- Synonym translation OFF")
    lines.append("-- ----------------------------------------------------------------")
    lines.append(f"-- Data Listing    Date : {now}")
    lines.append("")
    lines.append("ONERROR GOLABEL /ERROR3")
    lines.append("")
    lines.append("INPUT BEGIN")
    lines.append("")
    
    # 1. 螺栓杆圆柱
    lines.append("NEW CYLINDER")
    lines.append(f"POS X 0mm Y 0mm Z {z_shank_center:.2f}mm")
    lines.append(f"DIAM {d_shank}mm")
    lines.append(f"HEIG {L}mm")
    lines.append("")
    
    # 2. 头部六角切割（两个半六边形拉伸）
    # 右半部分
    lines.append("NEW NXTRUSION")
    lines.append("POS X 0mm Y 0mm Z 0mm")
    lines.append("ORI Y is -X and Z is Z")
    lines.append(f"HEIG {h_head}mm")
    lines.append("")
    lines.append("NEW LOOP")
    # 顶点： (0, -r), (R/2, -r), (R, 0), (R/2, r), (0, r)
    points_right = [
        (0, -r_head),
        (R_head/2, -r_head),
        (R_head, 0),
        (R_head/2, r_head),
        (0, r_head)
    ]
    for x, y in points_right:
        lines.append("NEW VERTEX")
        lines.append("")
        lines.append("END")
        lines.append(f"POS X {x:.2f}mm Y {y:.2f}mm Z 0mm")
        lines.append("")
        lines.append("END")
    lines.append("END")
    lines.append("END")
    lines.append("")
    
    # 左半部分
    lines.append("NEW NXTRUSION")
    lines.append("POS X 0mm Y 0mm Z 0mm")
    lines.append("ORI Y is -X and Z is Z")
    lines.append(f"HEIG {h_head}mm")
    lines.append("")
    lines.append("NEW LOOP")
    points_left = [
        (0, -r_head),
        (0, r_head),
        (-R_head/2, r_head),
        (-R_head, 0),
        (-R_head/2, -r_head)
    ]
    for x, y in points_left:
        lines.append("NEW VERTEX")
        lines.append("")
        lines.append("END")
        lines.append(f"POS X {x:.2f}mm Y {y:.2f}mm Z 0mm")
        lines.append("")
        lines.append("END")
    lines.append("END")
    lines.append("END")
    lines.append("")
    
    # 3. 上平垫片
    lines.append("NEW CYLINDER")
    lines.append(f"POS X 0mm Y 0mm Z {z_washer1_center:.2f}mm")
    lines.append(f"DIAM {d_washer}mm")
    lines.append(f"HEIG {h_washer}mm")
    lines.append("")
    
    # 4. 下平垫片
    lines.append("NEW CYLINDER")
    lines.append(f"POS X 0mm Y 0mm Z {z_washer2_center:.2f}mm")
    lines.append(f"DIAM {d_washer}mm")
    lines.append(f"HEIG {h_washer}mm")
    lines.append("")
    
    # 5. 弹簧垫片
    lines.append("NEW CYLINDER")
    lines.append(f"POS X 0mm Y 0mm Z {z_spring_center:.2f}mm")
    lines.append(f"DIAM {d_spring}mm")
    lines.append(f"HEIG {h_spring}mm")
    lines.append("")
    
    # 6. 螺母圆柱（外接圆）
    lines.append("NEW CYLINDER")
    lines.append(f"POS X 0mm Y 0mm Z {z_nut_center:.2f}mm")
    lines.append(f"DIAM {D_nut}mm")
    lines.append(f"HEIG {h_nut}mm")
    lines.append("")
    
    # 7. 螺母六角切割（两个半六边形拉伸）
    # 右半部分
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X 0mm Y 0mm Z {z_nut_bottom:.2f}mm")
    lines.append("ORI Y is -X and Z is Z")
    lines.append(f"HEIG {h_nut}mm")
    lines.append("")
    lines.append("NEW LOOP")
    points_right_nut = [
        (0, -r_nut),
        (R_nut/2, -r_nut),
        (R_nut, 0),
        (R_nut/2, r_nut),
        (0, r_nut)
    ]
    for x, y in points_right_nut:
        lines.append("NEW VERTEX")
        lines.append("")
        lines.append("END")
        lines.append(f"POS X {x:.2f}mm Y {y:.2f}mm Z 0mm")
        lines.append("")
        lines.append("END")
    lines.append("END")
    lines.append("END")
    lines.append("")
    
    # 左半部分
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X 0mm Y 0mm Z {z_nut_bottom:.2f}mm")
    lines.append("ORI Y is -X and Z is Z")
    lines.append(f"HEIG {h_nut}mm")
    lines.append("")
    lines.append("NEW LOOP")
    points_left_nut = [
        (0, -r_nut),
        (0, r_nut),
        (-R_nut/2, r_nut),
        (-R_nut, 0),
        (-R_nut/2, -r_nut)
    ]
    for x, y in points_left_nut:
        lines.append("NEW VERTEX")
        lines.append("")
        lines.append("END")
        lines.append(f"POS X {x:.2f}mm Y {y:.2f}mm Z 0mm")
        lines.append("")
        lines.append("END")
    lines.append("END")
    lines.append("END")
    lines.append("")
    
    # 结束
    lines.append("INPUT END  CYLINDER 1 of SUBEQUIPMENT /84XN001_FASTENER CYLINDER 2 of SUBEQUIPMENT /84XN001_FASTENER CYLINDER 3 of $")
    lines.append("SUBEQUIPMENT /84XN001_FASTENER CYLINDER 4 of SUBEQUIPMENT /84XN001_FASTENER CYLINDER 5 of SUBEQUIPMENT /84XN001_FASTENER")
    lines.append("INPUT FINISH")
    lines.append("-- Switch synonyms back on if an error occurs.")
    lines.append("LABEL /ERROR3")
    lines.append("handle ANY")
    lines.append("$S+")
    lines.append("RETURN ERROR")
    lines.append("endhandle")
    lines.append("")
    lines.append(f"-- End Data Listing    Date : {now}")
    lines.append("$S+  -- Synonym translation ON")
    lines.append("-- ----------------------------------------------------------------")
    
    return "\n".join(lines)

# ---------- GUI 界面 ----------
class App:
    def __init__(self, root):
        self.root = root
        root.title("紧固件生成器")
        root.geometry("400x300")
        root.resizable(False, False)
        
        # 变量
        self.bolt_var = tk.StringVar()
        self.thickness_var = tk.StringVar()
        self.length_var = tk.StringVar()
        
        # 螺栓尺寸
        tk.Label(root, text="螺栓尺寸：").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        bolt_combo = ttk.Combobox(root, textvariable=self.bolt_var, values=list(BOLT_HEADS.keys()), state="readonly")
        bolt_combo.grid(row=0, column=1, padx=5, pady=5)
        bolt_combo.current(0)
        
        # 连接件厚度
        tk.Label(root, text="连接件厚度 (mm)：").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        thickness_entry = tk.Entry(root, textvariable=self.thickness_var)
        thickness_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 螺栓长度
        tk.Label(root, text="螺栓长度 (mm)：").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        length_values = [3,4,5,6,8,10,12,16,20,25,30,35,40,45,50,55,60,65,70,80,90,100,110,120,130,140,150,160,180,200]
        length_combo = ttk.Combobox(root, textvariable=self.length_var, values=length_values, state="readonly")
        length_combo.grid(row=2, column=1, padx=5, pady=5)
        length_combo.current(0)
        
        # 按钮
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        clear_btn = tk.Button(btn_frame, text="清除全部输入", command=self.clear_all)
        clear_btn.pack(side="left", padx=10)
        
        generate_btn = tk.Button(btn_frame, text="生成紧固件", command=self.generate)
        generate_btn.pack(side="left", padx=10)
        
        # 状态标签
        self.status_label = tk.Label(root, text="", fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)
        
    def clear_all(self):
        self.bolt_var.set("M6")
        self.thickness_var.set("")
        self.length_var.set("")
        self.status_label.config(text="已清除")
        
    def generate(self):
        bolt = self.bolt_var.get()
        thickness_str = self.thickness_var.get().strip()
        length_str = self.length_var.get().strip()
        
        # 验证
        if not bolt or not thickness_str or not length_str:
            messagebox.showerror("错误", "请完整填写所有选项")
            return
        try:
            t = float(thickness_str)
            if t <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "连接件厚度必须是正数")
            return
        try:
            L = int(length_str)
            if L <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "螺栓长度必须是正整数")
            return
        
        # 检查长度是否足够
        h_washer = WASHERS[bolt][1]
        h_spring = SPRINGS[bolt][1]
        h_nut = NUTS[bolt][1]
        total_thick = h_washer + t + h_washer + h_spring + h_nut
        if L < total_thick:
            if not messagebox.askyesno("警告", f"螺栓长度 {L}mm 小于所需总厚度 {total_thick:.1f}mm，可能无法装配。是否继续？"):
                return
        
        # 生成脚本
        script = generate_script(bolt, t, L)
        
        # 保存文件
        default_name = f"{L}_{t:.1f}.txt".replace(".", "_")  # 避免小数点
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=default_name
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(script)
            self.status_label.config(text=f"已生成：{os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()