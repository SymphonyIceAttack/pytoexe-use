# -*- coding: utf-8 -*-
"""
紧固件生成器 v18 — 单文件版
Fastener Assembly TXT Generator v18 (single-file)

生成 Bocad 格式紧固件装配输入文件。
v18 改动：所有模块合并为单文件 + 建模层级下拉位置调整（移到螺栓长度余量下方）。
v17 特性：3 种建模层级（Equipment / SubEquipment / Volume model）+ M22 螺栓尺寸修正。
v12 基础：16 规格螺栓数据、BOX + NXTRUSION 六角建模、自动长度计算。

使用方法：直接运行本文件，或用 PyInstaller 打包为 exe。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
import datetime
from typing import Dict, List, Optional, Tuple


# ==================================================================
# 1. 数据定义 — 16 规格紧固件尺寸表
# ==================================================================

# ---------------------------------------------------------------
# 螺栓尺寸：{规格: {'s': 对边距 mm, 'h': 头厚 mm}}
# ---------------------------------------------------------------
BOLT_DATA: Dict[str, Dict[str, float]] = {
    'M6':  {'s': 10,  'h': 4},
    'M8':  {'s': 13,  'h': 5.3},
    'M10': {'s': 16,  'h': 6.4},
    'M12': {'s': 18,  'h': 7.5},
    'M14': {'s': 21,  'h': 8.8},
    'M16': {'s': 24,  'h': 10},
    'M18': {'s': 27,  'h': 11.5},
    'M20': {'s': 30,  'h': 12.5},
    'M22': {'s': 34,  'h': 14},
    'M24': {'s': 36,  'h': 15},
    'M30': {'s': 46,  'h': 18.7},
    'M36': {'s': 55,  'h': 22.5},
    'M42': {'s': 65,  'h': 26},
    'M48': {'s': 75,  'h': 30},
    'M56': {'s': 85,  'h': 35},
    'M64': {'s': 95,  'h': 40},
}

# ---------------------------------------------------------------
# 螺母尺寸：{规格: {'s': 对边距 mm, 'h': 厚度 mm}}
# ---------------------------------------------------------------
NUT_DATA: Dict[str, Dict[str, float]] = {
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

# ---------------------------------------------------------------
# 平垫片尺寸：{规格: {'d': 外径 mm, 'h': 厚度 mm}}
# ---------------------------------------------------------------
FLAT_WASHER_DATA: Dict[str, Dict[str, float]] = {
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

# ---------------------------------------------------------------
# 弹簧垫片尺寸：{规格: {'d': 外径 mm, 'h': 厚度 mm}}
# 数据仅到 M48
# ---------------------------------------------------------------
SPRING_WASHER_DATA: Dict[str, Dict[str, float]] = {
    'M6':  {'d': 11,   'h': 1.6},
    'M8':  {'d': 14.5, 'h': 2.1},
    'M10': {'d': 17.5, 'h': 2.6},
    'M12': {'d': 21,   'h': 3.1},
    'M14': {'d': 24,   'h': 3.6},
    'M16': {'d': 27,   'h': 4.1},
    'M18': {'d': 30,   'h': 4.5},
    'M20': {'d': 30,   'h': 5.0},
    'M22': {'d': 36,   'h': 5.5},
    'M24': {'d': 39,   'h': 6.0},
    'M30': {'d': 48,   'h': 7.5},
    'M36': {'d': 56,   'h': 8.5},
    'M42': {'d': 63,   'h': 9.5},
    'M48': {'d': 72,   'h': 11},
}

# ---------------------------------------------------------------
# 螺距 P (mm)
# ---------------------------------------------------------------
PITCH_DATA: Dict[str, float] = {
    'M6':  1,
    'M8':  1.25,
    'M10': 1.5,
    'M12': 1.75,
    'M14': 2,
    'M16': 2,
    'M18': 2.5,
    'M20': 2.5,
    'M22': 2.5,
    'M24': 3,
    'M30': 3.5,
    'M36': 4,
    'M42': 4.5,
    'M48': 5,
    'M56': 5.5,
    'M64': 6,
}

# ---------------------------------------------------------------
# GB/T 5783 公称长度标准系列 (mm)
# ---------------------------------------------------------------
BOLT_LENGTH_SERIES: List[int] = [
    20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70,
    80, 90, 100, 110, 120, 130, 140, 150, 160,
    180, 200, 220, 240, 260, 280, 300, 320, 340,
    360, 380, 400, 420, 440, 460, 480, 500, 520,
    540, 560, 580, 600, 620, 640,
]

# ---------------------------------------------------------------
# 各规格可用长度范围 (min, max) mm
# ---------------------------------------------------------------
BOLT_LENGTH_RANGE: Dict[str, Tuple[int, int]] = {
    'M6':  (12, 60),
    'M8':  (16, 80),
    'M10': (20, 100),
    'M12': (25, 120),
    'M14': (30, 140),
    'M16': (30, 160),
    'M18': (35, 180),
    'M20': (40, 200),
    'M22': (45, 220),
    'M24': (45, 240),
    'M30': (60, 300),
    'M36': (70, 360),
    'M42': (80, 420),
    'M48': (100, 480),
    'M56': (110, 560),
    'M64': (120, 640),
}

# ---------------------------------------------------------------
# 螺栓长度余量选项 + 默认值
# ---------------------------------------------------------------
LENGTH_MARGIN_OPTIONS: List[str] = ['1P', '2P', '3P', '4P', '5P']
DEFAULT_MARGIN: str = '2P'

# ---------------------------------------------------------------
# 螺栓规格列表（有序）
# ---------------------------------------------------------------
BOLT_SIZES: List[str] = [
    'M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M18', 'M20',
    'M22', 'M24', 'M30', 'M36', 'M42', 'M48', 'M56', 'M64',
]

# ---------------------------------------------------------------
# 六角 NXTRUSION 切角的四个角
# 每个：(角标识, x方向符号, y方向符号)
# ---------------------------------------------------------------
HEX_CORNERS: List[Tuple[str, int, int]] = [
    ('X+Y-', +1, -1),
    ('X-Y-', -1, -1),
    ('X+Y+', +1, +1),
    ('X-Y+', -1, +1),
]


# ==================================================================
# 2. 常量与工具函数 — 几何计算、格式化、Z 坐标
# ==================================================================

# ---------------------------------------------------------------
# 参考位置（项目坐标偏移）
# ---------------------------------------------------------------
REF_X: float = -256.0
REF_Y: float = 632.22

# 螺栓尖端 Z 位置（固定参考，螺栓 +Z 端）
REF_BOLT_TIP_Z: float = 25.0

# ---------------------------------------------------------------
# 六角几何常量
# ---------------------------------------------------------------
# e = s / cos(30°) = s * 2/√3 = s * 1.1547
HEX_E_FACTOR: float = 1.1547

# tan(30°) = 1/√3 = 0.5774
TAN_30: float = 0.5774

# ---------------------------------------------------------------
# 数值格式化工具
# ---------------------------------------------------------------

def fmt_val(val: float) -> str:
    """格式化数值，带 mm 后缀，去除末尾零。"""
    if val == int(val):
        return f"{int(val)}mm"
    else:
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return f"{s}mm"


def fmt_thickness(val: float) -> str:
    """格式化厚度值（用于文件名）。"""
    if val == int(val):
        return f"{int(val)}"
    else:
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return s


# ---------------------------------------------------------------
# 六角几何计算
# ---------------------------------------------------------------

def calc_hex_e(s: float) -> float:
    """
    六角外接圆直径（对角距）。
    e = s * 1.1547  （s / cos(30°)）
    """
    return s * HEX_E_FACTOR


def calc_cut_x(s: float) -> float:
    """
    角部三角形 NXTRUSION 的水平切距。
    cut_x = (s/2) * tan(30°) = s/2 * 0.5774
    """
    return (s / 2.0) * TAN_30


# ---------------------------------------------------------------
# NREVOLUTION 杆部轮廓顶点生成
# ---------------------------------------------------------------

def calc_shaft_vertices(d_bolt: float, s_bolt: float, L: float
                        ) -> List[Optional[Tuple[float, float, float]]]:
    """
    计算杆部 NREVOLUTION 顶点（5 顶点闭合回路）。
    外半径 = s_bolt（BOX 全 Y 尺寸，确保切穿）
    内半径 = d_bolt / 2（公称杆半径）

    v1: 尖端内半径（X=0）
    v2: 尖端外半径（X=0）
    v3: 头端外半径（X=-L）
    v4: 头端内半径（X=-L）
    v5: 同 v1（闭合）
    """
    r_inner = d_bolt / 2.0
    r_outer = s_bolt

    return [
        (0, r_inner, 0),
        (0, r_outer, 0),
        (-L, r_outer, 0),
        (-L, r_inner, 0),
        (0, r_inner, 0),
    ]


# ---------------------------------------------------------------
# 角部 NXTRUSION 顶点生成（六角切角）
# ---------------------------------------------------------------

def calc_corner_nxtrusion_vertices(corner_id: str, s: float, cut_x: float
                                   ) -> List[Optional[Tuple[float, float, float]]]:
    """
    生成单个角部 NXTRUSION 的 3 顶点三角形。
    第一个顶点为空（无 POS，角点原点）。

    corner_id: 'X+Y-', 'X-Y-', 'X+Y+', 'X-Y+' 之一
    s: 对边距（BOX 的 YLEN）
    cut_x: 水平切距 = (s/2) * tan(30)

    三角形顶点（局部 NXTRUSION 坐标，原点在 BOX 角点）：
      v1: 空（角点 = 原点）
      v2: 沿 Y 向中心 → 该侧六角顶点
      v3: 沿 X 向中心 → 相邻平边端点

    X-Y- 角有微小 Y 偏移（0.01mm）以匹配参考模板。
    """
    half_s = s / 2.0

    # corner_id → (v2_y符号, v3_x符号)
    corner_map = {
        'X+Y-': (+1, -1),
        'X-Y-': (+1, +1),
        'X+Y+': (-1, -1),
        'X-Y+': (-1, +1),
    }

    y_sign, x_sign = corner_map[corner_id]

    # X-Y- 角有微小 Y 偏移以匹配参考模板
    y_offset = 0.01 if corner_id == 'X-Y-' else 0.0

    v2 = (0, y_sign * half_s + y_offset, 0)
    v3 = (x_sign * cut_x, 0, 0)

    return [None, v2, v3]


# ---------------------------------------------------------------
# 每个角的 NXTRUSION 位置
# ---------------------------------------------------------------

def corner_pos(corner_id: str, e_val: float, s_val: float, local_z: float
               ) -> Tuple[float, float, float]:
    """
    计算角部 NXTRUSION 的 POS (x, y, z)。
    位置在 BOX 截面的角点处。

    corner_id: 'X+Y-', 'X-Y-', 'X+Y+', 'X-Y+' 之一
    e_val: 六角外接圆直径（BOX 的 XLEN）
    s_val: 对边距（BOX 的 YLEN）
    local_z: BOX 内的局部 Z 偏移
    """
    half_e = e_val / 2.0
    half_s = s_val / 2.0

    pos_map = {
        'X+Y-': (half_e, -half_s, local_z),
        'X-Y-': (-half_e, -half_s, local_z),
        'X+Y+': (half_e, half_s, local_z),
        'X-Y+': (-half_e, half_s, local_z),
    }

    return pos_map[corner_id]


# ---------------------------------------------------------------
# 螺栓长度计算（自动长度逻辑）
# ---------------------------------------------------------------

def calc_required_length(bolt_size: str, t_conn: float, margin_n: int) -> float:
    """
    计算所需螺栓长度 L_required。

    公式：L_required = 2*t_w + t_spring + t_nut + T_conn + n*P

    参数：
        bolt_size: 如 'M20'
        t_conn: 连接件厚度 mm
        margin_n: 整数 1~5，余量倍数

    返回：
        L_required mm
    """
    t_w = FLAT_WASHER_DATA[bolt_size]['h']
    t_spring = SPRING_WASHER_DATA[bolt_size]['h']
    t_nut = NUT_DATA[bolt_size]['h']
    P = PITCH_DATA[bolt_size]

    return 2 * t_w + t_spring + t_nut + t_conn + margin_n * P


def select_bolt_length(bolt_size: str, L_required: float) -> Tuple[Optional[int], str]:
    """
    从 GB/T 5783 系列中选择 >= L_required 的最小标准公称长度，
    并限制在该规格可用范围内。

    参数：
        bolt_size: 如 'M20'
        L_required: 最小所需长度 mm

    返回：
        (bolt_length, status)，status 为 'ok' 或 'too_thick'
        bolt_length 为选中的标准长度（int），
        若超出最大可用长度则返回 None。
    """
    L_min, L_max = BOLT_LENGTH_RANGE[bolt_size]

    if L_required > L_max:
        return None, 'too_thick'

    # 过滤出该规格可用范围内的标准系列
    available = [L for L in BOLT_LENGTH_SERIES if L_min <= L <= L_max]

    # 找第一个 >= L_required 的长度
    for L in available:
        if L >= L_required:
            return L, 'ok'

    return None, 'too_thick'


def margin_text_to_n(margin_text: str) -> int:
    """将余量显示文本（如 '2P'）转换为整数 n（如 2）。"""
    return int(margin_text.replace('P', ''))


# ---------------------------------------------------------------
# Z 坐标计算
# ---------------------------------------------------------------

def calc_z_positions(bolt_size: str, bolt_length: int, t_input: float
                     ) -> dict:
    """
    计算紧固件装配的所有 Z 坐标。
    螺栓尖端（+Z 端）在 Z = REF_BOLT_TIP_Z (25mm)。

    从 -Z 到 +Z 堆叠顺序：
      螺栓头 → 平垫片1 → [连接件 T_conn] → 平垫片2
      → 弹簧垫片 → 螺母
    """
    bolt = BOLT_DATA[bolt_size]
    h_bolt = bolt['h']
    L = float(bolt_length)

    fw_h = FLAT_WASHER_DATA[bolt_size]['h']
    sw_h = SPRING_WASHER_DATA.get(bolt_size, {}).get('h', 0)
    h_nut = NUT_DATA[bolt_size]['h']

    # 螺栓毛坯总高度 = 杆长 + 头厚
    bolt_total_h = L + h_bolt

    # 螺栓中心 Z（BOX 中心）
    bolt_center_z = REF_BOLT_TIP_Z - bolt_total_h / 2.0

    # 螺栓头 NXTRUSION 局部 Z（相对 BOX 中心）
    bolt_head_local_z = -bolt_total_h / 2.0

    # 杆部 NREVOLUTION 局部 Z（相对 BOX 中心）
    shaft_local_z = bolt_total_h / 2.0

    # 头-杆分界面全局 Z
    interface_z = REF_BOLT_TIP_Z - L

    # 平垫片1：靠头侧（头侧）
    fw1_center_z = interface_z + fw_h / 2.0

    # 平垫片2：螺母侧
    fw2_center_z = fw1_center_z + t_input + fw_h

    # 弹簧垫片：在 FW2 的 +Z 侧
    sw_center_z = fw2_center_z + fw_h / 2.0 + sw_h / 2.0

    # 螺母：在弹簧垫片 +Z 侧
    nut_center_z = sw_center_z + sw_h / 2.0 + h_nut / 2.0

    # 螺母 NXTRUSION 局部 Z（相对螺母 BOX 中心）
    nut_nxtrusion_local_z = -h_nut / 2.0

    return {
        'bolt_center_z': bolt_center_z,
        'bolt_total_h': bolt_total_h,
        'bolt_head_local_z': bolt_head_local_z,
        'shaft_local_z': shaft_local_z,
        'fw1_center_z': fw1_center_z,
        'fw2_center_z': fw2_center_z,
        'sw_center_z': sw_center_z,
        'nut_center_z': nut_center_z,
        'nut_nxtrusion_local_z': nut_nxtrusion_local_z,
        'center_distance': t_input + fw_h,
    }


# ==================================================================
# 3. 核心生成 — Bocad TXT 文件生成（3 种建模层级）
# ==================================================================

# ---------------------------------------------------------------
# 建模层级常量
# ---------------------------------------------------------------

MODEL_LEVELS: List[str] = [
    'Equipment',
    'SubEquipment',
    'Volume model',
]

DEFAULT_MODEL_LEVEL: str = 'Equipment'

# Volume model 父路径（硬编码，v10 约定）
VOLUME_PARENT_PATH: str = '/84XN001_FASTENER'


# ---------------------------------------------------------------
# 底层构建块
# ---------------------------------------------------------------

def _gen_vertex_block(vertices: List) -> List[str]:
    """
    生成 NEW LOOP 块及顶点。
    若 vertices[0] 为 None，第一个顶点为空（无 POS 行）。
    返回行列表。
    """
    lines: List[str] = []
    lines.append("NEW LOOP")
    lines.append("")

    for v in vertices:
        lines.append("NEW VERTEX")
        if v is not None:
            x, y, z = v
            lines.append(f"POS X {fmt_val(x)} Y {fmt_val(y)} Z 0mm")
        lines.append("")
        lines.append("END")

    lines.append("END")
    return lines


def _gen_nxtrusion(pos: Tuple[float, float, float], height: float,
                   vertices: List) -> List[str]:
    """
    生成单个 NXTRUSION 体。
    pos: (x, y, z) 位置
    height: 拉伸高度（HEIG）
    vertices: 回路顶点（角三角形为 3 个）
    """
    lines: List[str] = []
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X {fmt_val(pos[0])} Y {fmt_val(pos[1])} Z {fmt_val(pos[2])}")
    lines.append(f"HEIG {fmt_val(height)}")
    lines.append("")
    lines.extend(_gen_vertex_block(vertices))
    lines.append("END")
    return lines


def _gen_hex_nxtrusions(e_val: float, s_val: float, local_z: float,
                        height: float) -> List[str]:
    """
    为六角头/螺母生成 4 个角部 NXTRUSION（数据驱动循环）。
    e_val: 六角外接圆直径（BOX 的 XLEN）
    s_val: 对边距（BOX 的 YLEN）
    local_z: 父 BOX 内的局部 Z
    height: 拉伸高度（HEIG）
    """
    cut_x = calc_cut_x(s_val)
    lines: List[str] = []

    for corner_id, _x_sign, _y_sign in HEX_CORNERS:
        pos = corner_pos(corner_id, e_val, s_val, local_z)
        vertices = calc_corner_nxtrusion_vertices(corner_id, s_val, cut_x)
        lines.extend(_gen_nxtrusion(pos, height, vertices))

    return lines


def _gen_cylinder(pos_z: float, diam: float, heig: float) -> List[str]:
    """
    在 (REF_X, REF_Y, pos_z) 处生成单个 CYLINDER 体。
    """
    lines: List[str] = []
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(pos_z)}")
    lines.append(f"DIAM {fmt_val(diam)}")
    lines.append(f"HEIG {fmt_val(heig)}")
    lines.append("")
    lines.append("END")
    return lines


# ---------------------------------------------------------------
# 部件生成器（每个主要组件一个）
# ---------------------------------------------------------------

def _generate_bolt_body(s_bolt: float, h_bolt: float, d_bolt: float,
                        L: float, z: dict) -> List[str]:
    """
    生成螺栓体：BOX 毛坯 + NREVOLUTION 杆部 + 4× NXTRUSION 头部。
    """
    e_bolt = calc_hex_e(s_bolt)
    shaft_v = calc_shaft_vertices(d_bolt, s_bolt, L)

    lines: List[str] = []

    # BOX 毛坯
    lines.append("NEW BOX")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['bolt_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"XLEN {fmt_val(e_bolt)}")
    lines.append(f"YLEN {fmt_val(s_bolt)}")
    lines.append(f"ZLEN {fmt_val(z['bolt_total_h'])}")
    lines.append("")

    # 杆部 NREVOLUTION
    lines.append("NEW NREVOLUTION")
    lines.append(f"POS X 0mm Y 0mm Z {fmt_val(z['shaft_local_z'])}")
    lines.append("ORI Y is -X and Z is -Y")
    lines.append("")
    lines.extend(_gen_vertex_block(shaft_v))
    lines.append("END")

    # 螺栓头 4× NXTRUSION（角切，仅头高）
    lines.extend(_gen_hex_nxtrusions(
        e_bolt, s_bolt, z['bolt_head_local_z'], h_bolt))

    lines.append("END")
    return lines


def _generate_nut_body(s_nut: float, h_nut: float, z: dict) -> List[str]:
    """
    生成螺母体：BOX 毛坯 + 4× NXTRUSION（全高角切）。
    """
    e_nut = calc_hex_e(s_nut)

    lines: List[str] = []

    # BOX 毛坯
    lines.append("NEW BOX")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['nut_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"XLEN {fmt_val(e_nut)}")
    lines.append(f"YLEN {fmt_val(s_nut)}")
    lines.append(f"ZLEN {fmt_val(h_nut)}")
    lines.append("")

    # 螺母 4× NXTRUSION（角切，全螺母高度）
    lines.extend(_gen_hex_nxtrusions(
        e_nut, s_nut, z['nut_nxtrusion_local_z'], h_nut))

    lines.append("END")
    return lines


def _generate_washer_bodies(bolt_size: str, z: dict) -> List[str]:
    """
    生成 3 个垫片 CYLINDER 体：
    - 平垫片 1（头侧）
    - 平垫片 2（螺母侧）
    - 弹簧垫片
    """
    fw = FLAT_WASHER_DATA[bolt_size]
    sw = SPRING_WASHER_DATA[bolt_size]

    lines: List[str] = []

    # 平垫片 1（头侧）
    lines.extend(_gen_cylinder(z['fw1_center_z'], fw['d'], fw['h']))

    # 平垫片 2（螺母侧）
    lines.extend(_gen_cylinder(z['fw2_center_z'], fw['d'], fw['h']))

    # 弹簧垫片
    lines.extend(_gen_cylinder(z['sw_center_z'], sw['d'], sw['h']))

    return lines


def _generate_geometry(bolt_size: str, bolt_length: int, t_input: float) -> List[str]:
    """
    生成所有几何体（所有建模层级完全相同）。
    返回几何行列表。
    """
    bolt = BOLT_DATA[bolt_size]
    nut = NUT_DATA[bolt_size]

    s_bolt = bolt['s']
    h_bolt = bolt['h']
    L = float(bolt_length)

    s_nut = nut['s']
    h_nut = nut['h']

    d_bolt = float(bolt_size.replace('M', ''))

    z = calc_z_positions(bolt_size, bolt_length, t_input)

    lines: List[str] = []
    lines.extend(_generate_bolt_body(s_bolt, h_bolt, d_bolt, L, z))
    lines.extend(_generate_nut_body(s_nut, h_nut, z))
    lines.extend(_generate_washer_bodies(bolt_size, z))
    return lines


# ---------------------------------------------------------------
# 文件前导 / 后导（所有层级共用）
# ---------------------------------------------------------------

def _gen_preamble(datetime_str: str) -> List[str]:
    """
    生成文件前导：$S-、日期注释、ONERROR、INPUT BEGIN。
    3 种建模层级共用。
    """
    lines: List[str] = []
    lines.append("$S-  -- Synonym translation OFF")
    lines.append("-- ----------------------------------------------------------------")
    lines.append(f"-- Data Listing    Date : {datetime_str}")
    lines.append("")
    lines.append("ONERROR GOLABEL /ERROR3")
    lines.append("")
    lines.append("INPUT BEGIN")
    return lines


def _gen_postamble(datetime_str: str) -> List[str]:
    """
    生成文件后导：INPUT FINISH、错误处理、$S+、结束日期。
    3 种建模层级共用。
    """
    lines: List[str] = []
    lines.append("INPUT FINISH")
    lines.append("-- Switch synonyms back on if an error occurs.")
    lines.append("LABEL /ERROR3")
    lines.append("handle ANY")
    lines.append("$S+")
    lines.append("RETURN ERROR")
    lines.append("endhandle")
    lines.append("")
    lines.append(f"-- End Data Listing    Date : {datetime_str}")
    lines.append("$S+  -- Synonym translation ON")
    lines.append("-- ----------------------------------------------------------------")
    lines.append("")
    lines.append("")
    return lines


# ---------------------------------------------------------------
# 各层级专属头/尾对
# ---------------------------------------------------------------

def _gen_equipment_header(equip_name: str) -> List[str]:
    """
    Equipment 模式头部（INPUT BEGIN 之后）：
    NEW EQUIPMENT /name + BUIL/DSCO/PTSP/INSC 标志
    """
    lines: List[str] = []
    lines.append(f"NEW EQUIPMENT {equip_name}")
    lines.append("BUIL false")
    lines.append("DSCO unset")
    lines.append("PTSP unset")
    lines.append("INSC unset")
    lines.append("")
    return lines


def _gen_equipment_footer(equip_name: str) -> List[str]:
    """
    Equipment 模式尾部（INPUT FINISH 之前）：
    END（关闭 EQUIPMENT）+ INPUT END EQUIPMENT /name
    """
    lines: List[str] = []
    lines.append("END")
    lines.append(f"INPUT END  EQUIPMENT {equip_name}")
    return lines


def _gen_subequipment_header() -> List[str]:
    """
    SubEquipment 模式头部（INPUT BEGIN 之后）：
    NEW SUBEQUIPMENT（匿名，无路径）+ BUIL/DSCO/PTSP/INSC 标志
    """
    lines: List[str] = []
    lines.append("NEW SUBEQUIPMENT")
    lines.append("BUIL false")
    lines.append("DSCO unset")
    lines.append("PTSP unset")
    lines.append("INSC unset")
    lines.append("")
    return lines


def _gen_subequipment_footer(equip_name: str) -> List[str]:
    """
    SubEquipment 模式尾部（INPUT FINISH 之前）：
    END（关闭 SUBEQUIPMENT）+ INPUT END SUBEQUIPMENT 1 of EQUIPMENT /name
    """
    lines: List[str] = []
    lines.append("END")
    lines.append(f"INPUT END  SUBEQUIPMENT 1 of EQUIPMENT {equip_name}")
    return lines


def _gen_volume_header() -> List[str]:
    """
    Volume model 头部（INPUT BEGIN 之后）：
    无内容 — 无 NEW EQUIPMENT/SUBEQUIPMENT，无标志。
    几何直接跟在 INPUT BEGIN 之后。
    """
    return []


def _gen_volume_footer() -> List[str]:
    """
    Volume model 尾部（INPUT FINISH 之前）：
    END + INPUT END 列出所有顶级图元
    （BOX 1, BOX 2, CYLINDER 1/2/3）在 /84XN001_FASTENER 下
    """
    parent = VOLUME_PARENT_PATH
    lines: List[str] = []
    lines.append("END")
    lines.append(
        f"INPUT END  "
        f"BOX 1 of SUBEQUIPMENT {parent} "
        f"BOX 2 of SUBEQUIPMENT {parent} "
        f"CYLINDER 1 of SUBEQUIPMENT {parent} "
        f"CYLINDER 2 of SUBEQUIPMENT {parent} "
        f"CYLINDER 3 of SUBEQUIPMENT {parent}"
    )
    return lines


# ---------------------------------------------------------------
# 主入口函数
# ---------------------------------------------------------------

def generate_fastener_txt(bolt_size: str, bolt_length: int, t_input: float,
                          model_level: str = DEFAULT_MODEL_LEVEL) -> str:
    """
    生成 Bocad 格式紧固件装配 TXT 文件。

    5 个体（几何在所有层级完全相同）：
      BOX 1: 螺栓（BOX 毛坯 + NREVOLUTION + 4× NXTRUSION）
      BOX 2: 螺母（BOX 毛坯 + 4× NXTRUSION）
      CYLINDER 1: 平垫片 1（头侧）
      CYLINDER 2: 平垫片 2（螺母侧）
      CYLINDER 3: 弹簧垫片

    参数：
        bolt_size: 如 'M14'
        bolt_length: 公称长度 mm（如 80）
        t_input: 连接件厚度 mm（如 43.0）
        model_level: 'Equipment' | 'SubEquipment' | 'Volume model'

    返回：
        完整 Bocad TXT 内容字符串。
    """
    if model_level not in MODEL_LEVELS:
        raise ValueError(
            f"Invalid model_level '{model_level}'. "
            f"Must be one of: {', '.join(MODEL_LEVELS)}"
        )

    # 验证弹簧垫片数据
    if bolt_size not in SPRING_WASHER_DATA:
        raise ValueError(f"No spring washer data for {bolt_size}")

    # --- 设备名（Equipment 和 SubEquipment 模式使用）---
    t_formatted = fmt_thickness(t_input)
    equip_name = f"/{bolt_size}x{bolt_length}-{t_formatted}"

    # --- 日期字符串（匹配参考格式）---
    now = datetime.datetime.now()
    datetime_str = f"{now.day}  {now.strftime('%b')} {now.year} {now.hour:02d}:{now.minute:02d}"

    # --- 几何（所有层级完全相同）---
    geometry = _generate_geometry(bolt_size, bolt_length, t_input)

    # --- 层级专属头/尾 ---
    if model_level == 'Equipment':
        level_header = _gen_equipment_header(equip_name)
        level_footer = _gen_equipment_footer(equip_name)
    elif model_level == 'SubEquipment':
        level_header = _gen_subequipment_header()
        level_footer = _gen_subequipment_footer(equip_name)
    else:  # Volume model
        level_header = _gen_volume_header()
        level_footer = _gen_volume_footer()

    # --- 组装所有行 ---
    lines: List[str] = []
    lines.extend(_gen_preamble(datetime_str))
    lines.extend(level_header)
    lines.extend(geometry)
    lines.extend(level_footer)
    lines.extend(_gen_postamble(datetime_str))

    return '\n'.join(lines)


# ==================================================================
# 4. UI 界面 — Tkinter GUI 应用
# ==================================================================

class BoltGeneratorApp:
    """主应用窗口 — 中文 UI，v18 布局。

    v18 布局顺序：螺栓尺寸 → 连接件厚度 → 螺栓长度余量 → 建模层级
    （建模层级从 v17 的第 3 位移到第 4 位，放在螺栓长度余量下方）
    """

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("紧固件生成器for MEHV")
        self.root.geometry("440x480")
        self.root.resizable(False, False)

        self.center_window()
        self.create_widgets()

    def center_window(self) -> None:
        """窗口居中。"""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def create_widgets(self) -> None:
        """创建所有 UI 控件。

        v18 布局调整：建模层级从第 3 行移到第 4 行（螺栓长度余量下方）。
        行号映射：
          row 1: 螺栓尺寸
          row 2: 连接件厚度
          row 3: 螺栓长度余量  ← 上移
          row 4: 建模层级       ← 下移到最下
        """
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="紧固件装配参数",
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 螺栓尺寸（下拉）
        ttk.Label(main_frame, text="螺栓尺寸：").grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=8)
        self.bolt_size_var = tk.StringVar(value='')
        self.bolt_size_combo = ttk.Combobox(
            main_frame, textvariable=self.bolt_size_var,
            values=BOLT_SIZES, state='readonly', width=20)
        self.bolt_size_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        self.bolt_size_combo.bind('<<ComboboxSelected>>', self.on_param_change)

        # 连接件厚度（T_input = 实际连接件厚度）
        ttk.Label(main_frame, text="连接件厚度：").grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=8)
        self.t_thickness_var = tk.StringVar(value='')
        vcmd = (self.root.register(self.validate_positive), '%P')
        self.t_thickness_entry = ttk.Entry(
            main_frame, textvariable=self.t_thickness_var,
            validate='key', validatecommand=vcmd, width=22)
        self.t_thickness_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=8)
        self.t_thickness_entry.bind('<KeyRelease>', self.on_param_change)

        ttk.Label(main_frame, text="mm", foreground="#888").grid(
            row=2, column=2, sticky=tk.W, pady=8)

        # 螺栓长度余量下拉（v11 起替代手动螺栓长度）
        ttk.Label(main_frame, text="螺栓长度余量：").grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=8)
        self.margin_var = tk.StringVar(value=DEFAULT_MARGIN)
        self.margin_combo = ttk.Combobox(
            main_frame, textvariable=self.margin_var,
            values=LENGTH_MARGIN_OPTIONS, state='readonly', width=20)
        self.margin_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=8)
        self.margin_combo.bind('<<ComboboxSelected>>', self.on_param_change)

        # 建模层级（下拉）— v18 调整到螺栓长度余量下方
        ttk.Label(main_frame, text="建模层级：").grid(
            row=4, column=0, sticky=tk.E, padx=5, pady=8)
        self.model_level_var = tk.StringVar(value=DEFAULT_MODEL_LEVEL)
        self.model_level_combo = ttk.Combobox(
            main_frame, textvariable=self.model_level_var,
            values=MODEL_LEVELS, state='readonly', width=20)
        self.model_level_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=8)
        self.model_level_combo.bind('<<ComboboxSelected>>', self.on_param_change)

        # 信息框
        self.info_frame = ttk.LabelFrame(main_frame, text="自动匹配尺寸", padding="10")
        self.info_frame.grid(row=5, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)

        self.info_text = tk.StringVar()
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_text,
                                     justify=tk.LEFT, foreground="#333")
        self.info_label.pack(anchor=tk.W)

        # 按钮区
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(15, 0))

        self.clear_btn = ttk.Button(btn_frame, text="清除全部输入",
                                     command=self.clear_all, width=15)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        self.generate_btn = ttk.Button(btn_frame, text="生成紧固件",
                                        command=self.generate_fastener, width=15)
        self.generate_btn.pack(side=tk.LEFT, padx=10)

        # 初始信息
        self.update_info()

    def validate_positive(self, value: str) -> bool:
        """验证输入为正数（整数或小数）。"""
        if value == '':
            return True
        try:
            num = float(value)
            return num >= 0
        except ValueError:
            return False

    def on_param_change(self, event=None) -> None:
        """参数变化时更新信息。"""
        self.update_info()

    def update_info(self) -> None:
        """更新匹配尺寸信息（中文）。"""
        bolt_size = self.bolt_size_var.get()
        if bolt_size not in BOLT_DATA:
            self.info_text.set("请选择螺栓尺寸以查看匹配参数")
            return

        bolt = BOLT_DATA[bolt_size]
        nut = NUT_DATA[bolt_size]
        fw = FLAT_WASHER_DATA[bolt_size]
        sw = SPRING_WASHER_DATA.get(bolt_size)

        info = f"螺栓：对边 {bolt['s']}mm，头厚 {bolt['h']}mm\n"
        info += f"螺母：对边 {nut['s']}mm，厚度 {nut['h']}mm\n"
        info += f"平垫片：Ø{fw['d']}×{fw['h']}mm\n"
        if sw:
            info += f"弹簧垫片：Ø{sw['d']}×{sw['h']}mm"
        else:
            info += f"弹簧垫片：{bolt_size} 无数据"

        # 若输入了连接件厚度，自动计算并显示螺栓长度
        t_str = self.t_thickness_var.get().strip()
        margin_text = self.margin_var.get()

        if t_str and sw and margin_text:
            try:
                t_conn = float(t_str)
                if t_conn > 0:
                    margin_n = margin_text_to_n(margin_text)
                    L_req = calc_required_length(bolt_size, t_conn, margin_n)
                    L_sel, status = select_bolt_length(bolt_size, L_req)
                    if status == 'ok':
                        info += f"\n螺栓长度（不含六角头）：{L_sel} mm"
                    else:
                        info += f"\n螺栓长度：超出最大规格，请减小厚度或选更大规格"
            except ValueError:
                pass

        self.info_text.set(info)

    def clear_all(self) -> None:
        """清除所有输入。"""
        self.bolt_size_var.set('')
        self.t_thickness_var.set('')
        self.margin_var.set(DEFAULT_MARGIN)
        self.model_level_var.set(DEFAULT_MODEL_LEVEL)
        self.update_info()

    def generate_fastener(self) -> None:
        """生成紧固件 TXT 文件。
        螺栓长度自动计算，无需手动输入。
        """
        # 验证输入
        bolt_size = self.bolt_size_var.get()
        if not bolt_size:
            messagebox.showwarning("警告", "请选择螺栓尺寸")
            return

        t_str = self.t_thickness_var.get().strip()
        if not t_str:
            messagebox.showwarning("警告", "请输入连接件厚度")
            return

        try:
            t_input = float(t_str)
            if t_input <= 0:
                messagebox.showwarning("警告", "连接件厚度必须为正数")
                return
        except ValueError:
            messagebox.showwarning("警告", "连接件厚度必须为有效数字")
            return

        # 检查弹簧垫片数据
        if bolt_size not in SPRING_WASHER_DATA:
            messagebox.showerror("错误",
                f"{bolt_size} 无弹簧垫片数据。\n"
                f"支持规格：M6 ~ M48")
            return

        # 自动计算螺栓长度
        margin_text = self.margin_var.get()
        margin_n = margin_text_to_n(margin_text)
        L_required = calc_required_length(bolt_size, t_input, margin_n)
        bolt_length, status = select_bolt_length(bolt_size, L_required)

        if status == 'too_thick':
            L_max = BOLT_LENGTH_RANGE[bolt_size][1]
            messagebox.showerror("错误",
                f"当前连接件过厚，所需螺栓长度（{L_required:.1f}mm）\n"
                f"超过 {bolt_size} 的最大公称长度（{L_max}mm）。\n\n"
                f"请选更大规格或减小余量。")
            return

        fw_h = FLAT_WASHER_DATA[bolt_size]['h']
        center_dist = t_input + fw_h

        # 获取建模层级
        model_level = self.model_level_var.get()

        # 默认文件名（M{规格}x{长度}-{厚度}.txt）
        t_formatted = fmt_thickness(t_input)
        default_name = f"{bolt_size}x{bolt_length}-{t_formatted}.txt"

        # 保存对话框
        file_path = filedialog.asksaveasfilename(
            title="导出 TXT 文件",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return  # 用户取消

        try:
            content = generate_fastener_txt(bolt_size, bolt_length, t_input,
                                            model_level=model_level)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("成功",
                f"紧固件 TXT 文件生成成功！\n\n"
                f"文件：{file_path}\n"
                f"螺栓规格：{bolt_size}\n"
                f"螺栓长度：{bolt_length} mm\n"
                f"螺栓长度余量：{margin_text}\n"
                f"建模层级：{model_level}\n"
                f"连接件厚度：{t_input} mm\n"
                f"平垫片中心距：{center_dist} mm")

        except Exception as e:
            messagebox.showerror("错误", f"生成文件时出错：\n{str(e)}")


# ==================================================================
# 5. 程序入口
# ==================================================================

def main() -> None:
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use('clam')
    except Exception:
        pass

    app = BoltGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
