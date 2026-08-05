# -*- coding: utf-8 -*-
"""
紧固件装配 TXT 生成工具
根据螺栓规格、连接件厚度、螺栓长度生成紧固件装配输入文件
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import datetime

# ============================================================
# 数据定义 - 严格按用户提供的尺寸表
# ============================================================

# 螺栓尺寸：{规格: {'s': 六角头内切圆直径, 'h': 六角头厚度}}
BOLT_DATA = {
    'M6':  {'s': 10,  'h': 4},
    'M8':  {'s': 13,  'h': 5.3},
    'M10': {'s': 16,  'h': 6.4},
    'M12': {'s': 18,  'h': 7.5},
    'M14': {'s': 21,  'h': 8.8},
    'M16': {'s': 24,  'h': 10},
    'M18': {'s': 27,  'h': 11.5},
    'M20': {'s': 30,  'h': 12.5},
    'M22': {'s': 22,  'h': 14},
    'M24': {'s': 36,  'h': 15},
    'M30': {'s': 46,  'h': 18.7},
    'M36': {'s': 55,  'h': 22.5},
    'M42': {'s': 65,  'h': 26},
    'M48': {'s': 75,  'h': 30},
    'M56': {'s': 85,  'h': 35},
    'M64': {'s': 95,  'h': 40},
}

# 螺母尺寸：{规格: {'s': 六角头内切圆直径, 'h': 厚度}}
NUT_DATA = {
    'M6':  {'s': 10,  'h': 5.2},
    'M8':  {'s': 13,  'h': 6.8},
    'M10': {'s': 16,  'h': 8.4},
    'M12': {'s': 18,  'h': 10.8},
    'M14': {'s': 21,  'h': 12.8},
    'M16': {'s': 24,  'h': 14.8},
    'M18': {'s': 27,  'h': 15.8},
    'M20': {'s': 30,  'h': 18},
    'M22': {'s': 34,  'h': 19.4},
    'M24': {'s': 36,  'h': 21.5},
    'M30': {'s': 46,  'h': 25.6},
    'M36': {'s': 55,  'h': 31},
    'M42': {'s': 65,  'h': 34},
    'M48': {'s': 75,  'h': 38},
    'M56': {'s': 85,  'h': 45},
    'M64': {'s': 95,  'h': 51},
}

# 平垫片尺寸：{规格: {'d': 圆柱直径, 'h': 厚度}}
FLAT_WASHER_DATA = {
    'M6':  {'d': 12,  'h': 1.6},
    'M8':  {'d': 16,  'h': 1.6},
    'M10': {'d': 20,  'h': 2},
    'M12': {'d': 24,  'h': 2.5},
    'M14': {'d': 28,  'h': 2.5},
    'M16': {'d': 30,  'h': 3},
    'M18': {'d': 34,  'h': 3},
    'M20': {'d': 37,  'h': 3},
    'M22': {'d': 39,  'h': 3},
    'M24': {'d': 44,  'h': 4},
    'M30': {'d': 56,  'h': 4},
    'M36': {'d': 66,  'h': 5},
    'M42': {'d': 78,  'h': 8},
    'M48': {'d': 92,  'h': 8},
    'M56': {'d': 105, 'h': 10},
    'M64': {'d': 115, 'h': 10},
}

# 弹簧垫片尺寸：{规格: {'d': 圆柱直径, 'h': 厚度}}
# 注意：用户仅提供到 M48，M56/M64 无数据
SPRING_WASHER_DATA = {
    'M6':  {'d': 11,   'h': 1.6},
    'M8':  {'d': 14.5, 'h': 2.1},
    'M10': {'d': 17.5, 'h': 2.6},
    'M12': {'d': 21,   'h': 3.1},
    'M14': {'d': 24,   'h': 3.6},
    'M16': {'d': 27,   'h': 4.1},
    'M18': {'d': 30,   'h': 4.5},
    'M20': {'d': 33,   'h': 5.0},
    'M22': {'d': 36,   'h': 5.5},
    'M24': {'d': 39,   'h': 6.0},
    'M30': {'d': 48,   'h': 7.5},
    'M36': {'d': 56,   'h': 8.5},
    'M42': {'d': 63,   'h': 9.5},
    'M48': {'d': 72,   'h': 11},
}

# 螺栓长度可选值
BOLT_LENGTHS = [3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50,
                55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150,
                160, 180, 200]

# 螺栓规格列表（按顺序）
BOLT_SIZES = ['M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M18', 'M20',
              'M22', 'M24', 'M30', 'M36', 'M42', 'M48', 'M56', 'M64']

# 基准规格（M20×130）用于缩放
REF_SIZE = 'M20'
REF_LENGTH = 130.0
REF_S = BOLT_DATA[REF_SIZE]['s']  # 30
REF_H_BOLT = BOLT_DATA[REF_SIZE]['h']  # 12.5


# ============================================================
# 几何计算
# ============================================================

def calc_hex_e(s):
    """六角头外接圆直径 e = s × 1.1547"""
    return s * 1.1547


def calc_z_positions(bolt_size, bolt_length, t_thickness):
    """
    计算各零件的 Z 坐标位置
    堆叠顺序（从 -Z 到 +Z）：
      螺栓头部 → 螺栓杆部 → 平垫片1 → [T间距] → 平垫片2 → 弹簧垫片 → 螺母

    螺栓整体 POS Z = -(L+h)/2 （头部在 -Z 端，杆端在 +Z 端）
    头-杆分界面在螺栓局部坐标的 Z = +(L-h)/2 处（即杆部起点）
    平垫片1紧贴头-杆分界面

    返回各零件的全局 Z 位置（零件中心/基准面 Z 坐标）
    """
    bolt = BOLT_DATA[bolt_size]
    h_bolt = bolt['h']   # 头部厚度
    L = float(bolt_length)  # 杆部长度

    # 螺栓整体位置
    bolt_pos_z = -(L + h_bolt) / 2.0

    # 头-杆分界面的全局 Z 坐标
    # 头部在螺栓局部的位置：POS Z 局部 = (h-L)/2
    # 杆部在螺栓局部的位置：POS Z 局部 = +(L+h)/2  ... 等等，让我重新理解
    #
    # 螺栓总长 = h（头部） + L（杆部）
    # 螺栓整体中心 POS Z = -(L+h)/2
    #
    # 头部 NXTRUSION 局部 POS Z = (h-L)/2
    # 杆部 NREVOLUTION 局部 POS Z = +(L+h)/2
    #
    # 头-杆分界面（杆部起点）的全局 Z = bolt_pos_z + (h-L)/2 + h
    # = -(L+h)/2 + (h-L)/2 + h
    # = (-L -h + h - L)/2 + h
    # = (-2L)/2 + h
    # = -L + h
    #
    # 等等，这不对。让我重新理解：
    # NXTRUSION 头部的局部 POS Z = (h-L)/2
    # NREVOLUTION 杆部的局部 POS Z = +(L+h)/2
    #
    # 头部是拉伸体，厚度为 h，中心在 (h-L)/2
    # 所以头部范围：(h-L)/2 - h/2 到 (h-L)/2 + h/2
    # = (h-L-h)/2 到 (h-L+h)/2
    # = -L/2 到 (2h-L)/2
    #
    # 杆部是旋转体，长度为 L，中心在 (L+h)/2
    # 所以杆部范围：(L+h)/2 - L/2 到 (L+h)/2 + L/2
    # = h/2 到 L + h/2
    #
    # 头-杆之间有间隙？不对，应该是连接的。
    #
    # 让我重新理解 POS Z 的含义。
    # 如果 POS Z 是零件的基准面位置（而不是中心），那就不同了。
    #
    # 实际上，从用户描述"POS Z = -(L+h)/2"来看，这是螺栓整体的位置。
    # 头部和杆部是螺栓的两个部分，有各自的局部坐标偏移。
    #
    # 让我用 M20×130 来验证：
    # L = 130, h = 12.5
    # bolt_pos_z = -(130 + 12.5)/2 = -71.25
    #
    # 头部局部 POS Z = (h-L)/2 = (12.5-130)/2 = -58.75
    # 杆部局部 POS Z = (L+h)/2 = (130+12.5)/2 = 71.25
    #
    # 头部全局 Z 中心 = -71.25 + (-58.75) = -130
    # 头部厚度 12.5，所以头部范围：-136.25 到 -123.75
    #
    # 杆部全局 Z 中心 = -71.25 + 71.25 = 0
    # 杆部长度 130，所以杆部范围：-65 到 +65
    #
    # 这样头-杆之间有间隙（-123.75 到 -65），不对。
    #
    # 我觉得 POS Z 可能不是中心，而是某个基准面。
    # 或者局部坐标的含义不同。
    #
    # 让我重新理解：
    # "NXTRUSION 头部 POS Z 局部 = (h-L)/2"
    # "NREVOLUTION 杆部 POS Z 局部 = +(L+h)/2"
    #
    # 如果 POS Z 是零件的"起点"（-Z 端面），那么：
    # 头部起点在 (h-L)/2，厚度 h，所以头部范围：(h-L)/2 到 (h-L)/2 + h = (3h-L)/2
    # 杆部起点在 (L+h)/2，长度 L，所以杆部范围：(L+h)/2 到 (L+h)/2 + L = (3L+h)/2
    #
    # 这显然也不对，间隙更大了。
    #
    # 也许 POS Z 是 +Z 端面？
    # 头部 +Z 端面在 (h-L)/2，厚度 h，所以头部范围：(h-L)/2 - h 到 (h-L)/2 = (-h-L)/2 到 (h-L)/2
    # 杆部 +Z 端面在 (L+h)/2，长度 L，所以杆部范围：(L+h)/2 - L 到 (L+h)/2 = (h-L)/2 到 (L+h)/2
    #
    # 哦！这样就对了！头部的 +Z 端面在 (h-L)/2，杆部的 -Z 端面也在 (h-L)/2
    # 两者在 (h-L)/2 处连接！
    #
    # 头部范围（局部）：(-h-L)/2 到 (h-L)/2
    # 杆部范围（局部）：(h-L)/2 到 (L+h)/2
    #
    # 螺栓整体长度 = (L+h)/2 - (-h-L)/2 = (L+h+h+L)/2 = (2L+2h)/2 = L+h ✓
    # 头-杆分界面在局部 Z = (h-L)/2 处
    #
    # 螺栓整体 POS Z = -(L+h)/2
    # 所以全局坐标：
    # 螺栓 -Z 端（头部端面）= -(L+h)/2 + (-h-L)/2 = -(L+h)
    # 螺栓 +Z 端（杆部端面）= -(L+h)/2 + (L+h)/2 = 0
    # 头-杆分界面全局 Z = -(L+h)/2 + (h-L)/2 = (-L-h+h-L)/2 = -L
    #
    # 验证 M20×130：
    # 螺栓 -Z 端 = -(130+12.5) = -142.5
    # 螺栓 +Z 端 = 0
    # 头-杆分界面 = -130
    # 头部厚度 = -130 - (-142.5) = 12.5 ✓
    # 杆部长度 = 0 - (-130) = 130 ✓
    #
    # 完美！所以 POS Z 是零件的 +Z 端面位置。

    # 头-杆分界面全局 Z 坐标（杆部起点，-Z 侧）
    interface_z = -L  # 螺栓 +Z 端在 0，头-杆分界面在 -L

    # 堆叠顺序（从 -Z 到 +Z）：
    #   螺栓头部 → [头-杆分界面] → 平垫片1 → 连接件(T) → 平垫片2 → 弹簧垫片 → 螺母
    # 每个零件的 POS Z = 其 +Z 端面的全局 Z 坐标

    fw1_h = FLAT_WASHER_DATA[bolt_size]['h']
    fw2_h = FLAT_WASHER_DATA[bolt_size]['h']
    sw_h = SPRING_WASHER_DATA.get(bolt_size, {}).get('h', 0)
    nut_h = NUT_DATA[bolt_size]['h']

    # 平垫片1：紧贴头-杆分界面，向 +Z 方向生长
    # 范围: interface_z 到 interface_z + fw1_h
    fw1_pos_z = interface_z + fw1_h  # +Z 端面

    # 连接件（T 厚度，不建模）
    # 范围: fw1_pos_z 到 fw1_pos_z + t_thickness
    t_end_z = fw1_pos_z + t_thickness  # 连接件 +Z 侧

    # 平垫片2：在连接件 +Z 侧
    # 范围: t_end_z 到 t_end_z + fw2_h
    fw2_pos_z = t_end_z + fw2_h  # +Z 端面

    # 弹簧垫片：在平垫片2 的 +Z 侧
    # 范围: fw2_pos_z 到 fw2_pos_z + sw_h
    sw_pos_z = fw2_pos_z + sw_h  # +Z 端面

    # 螺母：在弹簧垫片的 +Z 侧
    # 范围: sw_pos_z 到 sw_pos_z + nut_h
    nut_pos_z = sw_pos_z + nut_h  # +Z 端面

    return {
        'bolt_pos_z': bolt_pos_z,
        'interface_z': interface_z,
        'fw1_pos_z': fw1_pos_z,
        'fw2_pos_z': fw2_pos_z,
        'sw_pos_z': sw_pos_z,
        'nut_pos_z': nut_pos_z,
        'bolt_end_z': 0.0,  # 螺栓 +Z 端
        'nut_end_z': nut_pos_z,  # 螺母 +Z 端
    }


# ============================================================
# TXT 文件生成
# ============================================================

def generate_fastener_txt(bolt_size, bolt_length, t_thickness):
    """
    生成紧固件装配 TXT 文件内容
    包含 5 个 INPUT BEGIN 块：螺栓、平垫片1、平垫片2、弹簧垫片、螺母
    """
    bolt = BOLT_DATA[bolt_size]
    nut = NUT_DATA[bolt_size]
    fw = FLAT_WASHER_DATA[bolt_size]
    sw = SPRING_WASHER_DATA.get(bolt_size)

    if sw is None:
        raise ValueError(f"{bolt_size} 无弹簧垫片数据，无法生成")

    s_bolt = bolt['s']
    h_bolt = bolt['h']
    L = float(bolt_length)

    s_nut = nut['s']
    h_nut = nut['h']

    fw_d = fw['d']
    fw_h = fw['h']

    sw_d = sw['d']
    sw_h = sw['h']

    # 缩放因子
    s_scale = s_bolt / REF_S  # 径向缩放
    l_scale = L / REF_LENGTH  # 轴向缩放

    # 外接圆直径
    e_bolt = calc_hex_e(s_bolt)
    e_nut = calc_hex_e(s_nut)

    # 螺栓杆径（公称直径）
    d_bolt = float(bolt_size.replace('M', ''))

    # Z 坐标
    z = calc_z_positions(bolt_size, bolt_length, t_thickness)

    lines = []

    # ========================================
    # 文件头
    # ========================================
    lines.append(f"* 紧固件装配输入文件")
    lines.append(f"* 规格: {bolt_size} x {bolt_length}")
    lines.append(f"* 连接件厚度: {t_thickness}")
    lines.append(f"* 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"*")

    # ========================================
    # INPUT BLOCK 1: 螺栓 (BOLT)
    # ========================================
    lines.append(f"INPUT BEGIN BOLT_{bolt_size}_{bolt_length}")
    lines.append(f"  TYPE BOLT")
    lines.append(f"  SIZE {bolt_size}")
    lines.append(f"  LENGTH {L}")
    lines.append(f"  POS Z {z['bolt_pos_z']:.6f}")
    lines.append(f"  * 头部 - 六角拉伸体")
    lines.append(f"  NXTRUSION HEX_HEAD")
    lines.append(f"    S {s_bolt}")
    lines.append(f"    E {e_bolt:.4f}")
    lines.append(f"    H {h_bolt}")
    lines.append(f"    POS Z {(h_bolt - L) / 2.0:.6f}")
    lines.append(f"    DIAM {e_bolt:.4f}")
    lines.append(f"  END NXTRUSION")
    lines.append(f"  * 杆部 - 旋转体")
    lines.append(f"  NREVOLUTION SHAFT")
    lines.append(f"    D {d_bolt}")
    lines.append(f"    L {L}")
    lines.append(f"    POS Z {(L + h_bolt) / 2.0:.6f}")
    lines.append(f"  END NREVOLUTION")
    lines.append(f"END INPUT")
    lines.append(f"")

    # ========================================
    # INPUT BLOCK 2: 平垫片1 (FLAT WASHER 1)
    # ========================================
    lines.append(f"INPUT BEGIN FLAT_WASHER_1_{bolt_size}")
    lines.append(f"  TYPE FLAT_WASHER")
    lines.append(f"  SIZE {bolt_size}")
    lines.append(f"  LOCATION HEAD_SIDE")
    lines.append(f"  D {fw_d}")
    lines.append(f"  H {fw_h}")
    lines.append(f"  POS Z {z['fw1_pos_z']:.6f}")
    lines.append(f"  NREVOLUTION WASHER")
    lines.append(f"    D_OUT {fw_d}")
    lines.append(f"    D_IN {d_bolt}")
    lines.append(f"    H {fw_h}")
    lines.append(f"  END NREVOLUTION")
    lines.append(f"END INPUT")
    lines.append(f"")

    # ========================================
    # INPUT BLOCK 3: 平垫片2 (FLAT WASHER 2)
    # ========================================
    lines.append(f"INPUT BEGIN FLAT_WASHER_2_{bolt_size}")
    lines.append(f"  TYPE FLAT_WASHER")
    lines.append(f"  SIZE {bolt_size}")
    lines.append(f"  LOCATION NUT_SIDE")
    lines.append(f"  D {fw_d}")
    lines.append(f"  H {fw_h}")
    lines.append(f"  POS Z {z['fw2_pos_z']:.6f}")
    lines.append(f"  NREVOLUTION WASHER")
    lines.append(f"    D_OUT {fw_d}")
    lines.append(f"    D_IN {d_bolt}")
    lines.append(f"    H {fw_h}")
    lines.append(f"  END NREVOLUTION")
    lines.append(f"END INPUT")
    lines.append(f"")

    # ========================================
    # INPUT BLOCK 4: 弹簧垫片 (SPRING WASHER)
    # ========================================
    lines.append(f"INPUT BEGIN SPRING_WASHER_{bolt_size}")
    lines.append(f"  TYPE SPRING_WASHER")
    lines.append(f"  SIZE {bolt_size}")
    lines.append(f"  D {sw_d}")
    lines.append(f"  H {sw_h}")
    lines.append(f"  POS Z {z['sw_pos_z']:.6f}")
    lines.append(f"  NREVOLUTION WASHER")
    lines.append(f"    D_OUT {sw_d}")
    lines.append(f"    D_IN {d_bolt}")
    lines.append(f"    H {sw_h}")
    lines.append(f"  END NREVOLUTION")
    lines.append(f"END INPUT")
    lines.append(f"")

    # ========================================
    # INPUT BLOCK 5: 螺母 (NUT)
    # ========================================
    lines.append(f"INPUT BEGIN NUT_{bolt_size}")
    lines.append(f"  TYPE NUT")
    lines.append(f"  SIZE {bolt_size}")
    lines.append(f"  H {h_nut}")
    lines.append(f"  POS Z {z['nut_pos_z']:.6f}")
    lines.append(f"  NXTRUSION HEX_NUT")
    lines.append(f"    S {s_nut}")
    lines.append(f"    E {e_nut:.4f}")
    lines.append(f"    H {h_nut}")
    lines.append(f"    DIAM {e_nut:.4f}")
    lines.append(f"  END NXTRUSION")
    lines.append(f"END INPUT")
    lines.append(f"")

    # ========================================
    # 装配汇总信息
    # ========================================
    lines.append(f"* ========================================")
    lines.append(f"* 装配几何汇总")
    lines.append(f"* ========================================")
    lines.append(f"* 螺栓规格: {bolt_size}")
    lines.append(f"* 螺栓长度: {L} mm")
    lines.append(f"* 连接件厚度: {t_thickness} mm")
    lines.append(f"* 六角头对边距: {s_bolt} mm")
    lines.append(f"* 六角头外接圆: {e_bolt:.4f} mm")
    lines.append(f"* 头部厚度: {h_bolt} mm")
    lines.append(f"* 螺母对边距: {s_nut} mm")
    lines.append(f"* 螺母厚度: {h_nut} mm")
    lines.append(f"* 平垫片直径: {fw_d} mm, 厚度: {fw_h} mm")
    lines.append(f"* 弹簧垫片直径: {sw_d} mm, 厚度: {sw_h} mm")
    lines.append(f"* 螺栓 -Z 端: {z['bolt_pos_z'] - (L + h_bolt)/2.0:.6f} mm")
    lines.append(f"* 螺栓 +Z 端: {z['bolt_end_z']:.6f} mm")
    lines.append(f"* 螺母 +Z 端: {z['nut_end_z']:.6f} mm")
    lines.append(f"* 总装配高度: {z['nut_end_z'] - (z['bolt_pos_z'] - (L + h_bolt)/2.0):.6f} mm")
    lines.append(f"* 杆部伸出螺母长度: {z['bolt_end_z'] - z['nut_pos_z'] + h_nut:.6f} mm")
    lines.append(f"* ========================================")

    return '\n'.join(lines)


# ============================================================
# GUI 界面
# ============================================================

class BoltGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("紧固件装配 TXT 生成工具")
        self.root.geometry("420x430")
        self.root.resizable(False, False)

        # 居中显示
        self.center_window()

        self.create_widgets()

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="紧固件装配参数输入",
                                font=("Microsoft YaHei", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 螺栓尺寸（下拉选择）
        ttk.Label(main_frame, text="螺栓尺寸：").grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=8)
        self.bolt_size_var = tk.StringVar(value='M20')
        self.bolt_size_combo = ttk.Combobox(
            main_frame, textvariable=self.bolt_size_var,
            values=BOLT_SIZES, state='readonly', width=20)
        self.bolt_size_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        self.bolt_size_combo.bind('<<ComboboxSelected>>', self.on_bolt_size_change)

        # 连接件厚度（仅正数）
        ttk.Label(main_frame, text="连接件厚度：").grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=8)
        self.t_thickness_var = tk.StringVar(value='20')
        vcmd = (self.root.register(self.validate_positive), '%P')
        self.t_thickness_entry = ttk.Entry(
            main_frame, textvariable=self.t_thickness_var,
            validate='key', validatecommand=vcmd, width=22)
        self.t_thickness_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=8)

        ttk.Label(main_frame, text="mm", foreground="#888").grid(
            row=2, column=2, sticky=tk.W, pady=8)

        # 螺栓长度（下拉选择）
        ttk.Label(main_frame, text="螺栓长度：").grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=8)
        self.bolt_length_var = tk.StringVar(value='130')
        self.bolt_length_combo = ttk.Combobox(
            main_frame, textvariable=self.bolt_length_var,
            values=[str(x) for x in BOLT_LENGTHS], state='readonly', width=20)
        self.bolt_length_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=8)

        ttk.Label(main_frame, text="mm", foreground="#888").grid(
            row=3, column=2, sticky=tk.W, pady=8)

        # 匹配信息显示
        self.info_frame = ttk.LabelFrame(main_frame, text="自动匹配尺寸", padding="10")
        self.info_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)

        self.info_text = tk.StringVar()
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_text,
                                     justify=tk.LEFT, foreground="#333")
        self.info_label.pack(anchor=tk.W)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(15, 0))

        self.clear_btn = ttk.Button(btn_frame, text="清除全部输入",
                                     command=self.clear_all, width=15)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        self.generate_btn = ttk.Button(btn_frame, text="生成紧固件",
                                        command=self.generate_fastener, width=15)
        self.generate_btn.pack(side=tk.LEFT, padx=10)

        # 初始化显示匹配信息
        self.update_info()

    def validate_positive(self, value):
        """验证输入为正数（整数或小数）"""
        if value == '':
            return True
        try:
            num = float(value)
            return num >= 0
        except ValueError:
            return False

    def on_bolt_size_change(self, event=None):
        """螺栓规格改变时更新信息"""
        self.update_info()

    def update_info(self):
        """更新匹配尺寸信息"""
        bolt_size = self.bolt_size_var.get()
        if bolt_size not in BOLT_DATA:
            self.info_text.set("请选择螺栓规格")
            return

        bolt = BOLT_DATA[bolt_size]
        nut = NUT_DATA[bolt_size]
        fw = FLAT_WASHER_DATA[bolt_size]
        sw = SPRING_WASHER_DATA.get(bolt_size)

        info = f"螺栓：六角对边 {bolt['s']}mm，头厚 {bolt['h']}mm\n"
        info += f"螺母：六角对边 {nut['s']}mm，厚 {nut['h']}mm\n"
        info += f"平垫片：直径 {fw['d']}mm，厚 {fw['h']}mm\n"
        if sw:
            info += f"弹簧垫片：直径 {sw['d']}mm，厚 {sw['h']}mm"
        else:
            info += f"弹簧垫片：无数据（{bolt_size} 暂不支持）"

        self.info_text.set(info)

    def clear_all(self):
        """清除全部输入，恢复默认值"""
        self.bolt_size_var.set('M20')
        self.t_thickness_var.set('')
        self.bolt_length_var.set('130')
        self.update_info()

    def generate_fastener(self):
        """生成紧固件 TXT 文件"""
        # 验证输入
        bolt_size = self.bolt_size_var.get()
        if not bolt_size:
            messagebox.showwarning("提示", "请选择螺栓尺寸")
            return

        t_str = self.t_thickness_var.get().strip()
        if not t_str:
            messagebox.showwarning("提示", "请输入连接件厚度")
            return

        try:
            t_thickness = float(t_str)
            if t_thickness <= 0:
                messagebox.showwarning("提示", "连接件厚度必须为正数")
                return
        except ValueError:
            messagebox.showwarning("提示", "连接件厚度必须为有效数字")
            return

        bolt_length_str = self.bolt_length_var.get()
        if not bolt_length_str:
            messagebox.showwarning("提示", "请选择螺栓长度")
            return

        bolt_length = int(bolt_length_str)

        # 检查弹簧垫片数据
        if bolt_size not in SPRING_WASHER_DATA:
            messagebox.showerror("错误",
                f"{bolt_size} 暂无弹簧垫片数据，暂不支持生成。\n"
                f"支持弹簧垫片的规格：M6 ~ M48")
            return

        # 生成文件名：螺栓规格+连接件厚度
        # 格式：M{规格}_{厚度}.txt
        default_name = f"{bolt_size}_{t_thickness}.txt"

        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            title="导出 TXT 文件",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return  # 用户取消

        try:
            # 生成内容
            content = generate_fastener_txt(bolt_size, bolt_length, t_thickness)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("成功",
                f"紧固件 TXT 文件已生成！\n\n"
                f"文件路径：{file_path}\n"
                f"螺栓规格：{bolt_size}\n"
                f"螺栓长度：{bolt_length} mm\n"
                f"连接件厚度：{t_thickness} mm")

        except Exception as e:
            messagebox.showerror("错误", f"生成文件时出错：\n{str(e)}")


# ============================================================
# 主入口
# ============================================================

def main():
    root = tk.Tk()

    # 设置主题
    try:
        style = ttk.Style()
        style.theme_use('clam')
    except:
        pass

    app = BoltGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
