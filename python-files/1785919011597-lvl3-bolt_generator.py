# -*- coding: utf-8 -*-
"""
Fastener Assembly TXT Generator v7
Generates Bocad-format fastener assembly input files based on
bolt size, connection thickness, and bolt length.

v7 changes (geometry overhaul for Bocad rendering fidelity):
  - Bolt head: standard 6-vertex hex prism via 2x NXTRUSION (L+R halves)
  - Nut: standard 6-vertex hex prism via 2x NXTRUSION (L+R halves)
  - Bolt shaft: CYLINDER instead of NREVOLUTION (simpler, no ambiguity)
  - Bolt split into 2 CYLINDERs (head + shaft), total 6 CYLINDERs
  - Fixes: hex prism distortion, incomplete cutting, shaft ovality

v6 algorithm preserved:
  - T_input = actual connector thickness T_conn
  - Center-to-center distance between flat washers = T_input + t_w
  - GUI label: "连接件厚度"
  - Filename: M{size}x{length}-{thickness}.txt
  - Window title: "紧固件生成器for青岛MEHV"
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import datetime
import math

# ============================================================
# Data Definitions - Dimensions per user-provided tables
# ============================================================

# Bolt dimensions: {size: {'s': hex flat-to-flat (mm), 'h': head height (mm)}}
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

# Nut dimensions: {size: {'s': hex flat-to-flat (mm), 'h': height (mm)}}
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

# Flat washer dimensions: {size: {'d': outer diameter (mm), 'h': thickness (mm)}}
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

# Spring washer dimensions: {size: {'d': outer diameter (mm), 'h': thickness (mm)}}
# Data available up to M48 only
SPRING_WASHER_DATA = {
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

# Available bolt lengths (mm)
BOLT_LENGTHS = [3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50,
                55, 60, 65, 70, 80, 90, 100, 110, 120, 130, 140, 150,
                160, 180, 200]

# Bolt size list (ordered)
BOLT_SIZES = ['M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M18', 'M20',
              'M22', 'M24', 'M30', 'M36', 'M42', 'M48', 'M56', 'M64']

# Reference: M20 base values
REF_SIZE = 'M20'
REF_S = 30.0          # hex flat-to-flat for M20
REF_E = 34.7          # hex circumscribed diameter for M20
REF_H_BOLT = 12.5     # bolt head height for M20
REF_H_NUT = 18.0      # nut height for M20
REF_LENGTH = 130.0    # bolt length for reference
REF_D = 20.0          # nominal diameter for M20
REF_BOLT_TIP_Z = 25.0 # bolt +Z end position (fixed reference)

# Reference X/Y position for assembly
REF_X = -256.0
REF_Y = 632.22

# ============================================================
# Standard Hex Prism Vertex Generation (v7)
# 6 vertices on circumscribed circle + center closure
# Split into L/R halves, each cut by one NXTRUSION
# ============================================================

def gen_hex_half_verts(R, side='right'):
    """
    Generate vertices for one half of a standard hex prism.
    R: circumscribed radius (e/2)
    side: 'right' for x>=0 half, 'left' for x<=0 half

    Returns list of 5 vertex positions [None, v2, v3, v4, v5]
    where v2..v4 are the 3 hex vertices on that side, v5 is center.
    Vertex order: top -> outer -> bottom -> center (clockwise for right half)
    """
    sqrt3 = math.sqrt(3)

    if side == 'right':
        # 3 vertices on the right half (x >= 0): 60deg, 0deg, -60deg
        v_top    = ( R * 0.5,       R * sqrt3 / 2,  0)   # 60 deg
        v_outer  = ( R,             0,              0)   # 0 deg
        v_bottom = ( R * 0.5,      -R * sqrt3 / 2,  0)   # -60 deg
    else:  # left
        # 3 vertices on the left half (x <= 0): 120deg, 180deg, 240deg
        v_top    = (-R * 0.5,       R * sqrt3 / 2,  0)   # 120 deg
        v_outer  = (-R,             0,              0)   # 180 deg
        v_bottom = (-R * 0.5,      -R * sqrt3 / 2,  0)   # 240 deg

    v_center = (0, 0, 0)

    # Round to 2 decimal places (matches Bocad convention)
    def rnd(v):
        return (round(v[0], 2), round(v[1], 2), v[2])

    return [None, rnd(v_top), rnd(v_outer), rnd(v_bottom), rnd(v_center)]


# ============================================================
# Helper Functions
# ============================================================

def fmt_val(val):
    """Format a numeric value with 'mm' suffix, no trailing zeros."""
    if val == int(val):
        return f"{int(val)}mm"
    else:
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return f"{s}mm"


def fmt_thickness(val):
    """Format thickness value for filename."""
    if val == int(val):
        return f"{int(val)}"
    else:
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return s


def calc_hex_e(s):
    """Hex circumscribed diameter, scaled from reference M20."""
    return s * REF_E / REF_S


def scale_vertices(vertices, scale_xy, scale_x=None, scale_y=None):
    """
    Scale a list of vertex tuples.
    Returns list of scaled (x, y, z) tuples, None stays None.
    """
    sx = scale_x if scale_x is not None else scale_xy
    sy = scale_y if scale_y is not None else scale_xy

    result = []
    for v in vertices:
        if v is None:
            result.append(None)
        else:
            x, y, z = v
            result.append((round(x * sx, 2), round(y * sy, 2), z))
    return result


# ============================================================
# Z Position Calculations (v7 - bolt split into head + shaft)
# ============================================================

def calc_z_positions(bolt_size, bolt_length, t_input):
    """
    Calculate all Z positions for v7.
    Bolt tip (+Z end) at Z = REF_BOLT_TIP_Z (25mm).

    v7: bolt split into 2 separate CYLINDERs:
      CYL 1: Bolt head (hex, height h_bolt)
      CYL 2: Bolt shaft (cylinder, diameter d, length L)

    Stacking from -Z to +Z:
      bolt head -> shaft interface -> flat washer 1 -> [T_conn]
      -> flat washer 2 -> spring washer -> nut

    Head-shaft interface at Z = REF_BOLT_TIP_Z - L
    Bolt head spans: interface - h_bolt  to  interface  (-Z direction from interface)
    Bolt shaft spans: interface  to  interface + L  (= REF_BOLT_TIP_Z)

    v6 algorithm preserved for washers/nut:
      FW1 center = interface_z + fw_h/2  (against head, shaft side)
      FW2 center = FW1 center + t_input + fw_h
      SW center = FW2 center + fw_h/2 + sw_h/2
      Nut center = SW center + sw_h/2 + h_nut/2
    """
    bolt = BOLT_DATA[bolt_size]
    h_bolt = bolt['h']
    L = float(bolt_length)

    fw_h = FLAT_WASHER_DATA[bolt_size]['h']
    sw_h = SPRING_WASHER_DATA.get(bolt_size, {}).get('h', 0)
    h_nut = NUT_DATA[bolt_size]['h']

    # Head-shaft interface global Z
    interface_z = REF_BOLT_TIP_Z - L

    # Bolt head center Z (CYL 1)
    bolt_head_center_z = interface_z - h_bolt / 2.0

    # Bolt shaft center Z (CYL 2)
    shaft_center_z = interface_z + L / 2.0

    # Bolt head NXTRUSION local Z (relative to head center)
    # POS at -Z end of head: local_z = -h_bolt / 2
    bolt_head_nxtrusion_local_z = -h_bolt / 2.0

    # Flat washer 1: against head (head side of connection)
    # FW1 sits on shaft side, right against head
    fw1_center_z = interface_z + fw_h / 2.0

    # Flat washer 2: nut side
    fw2_center_z = fw1_center_z + t_input + fw_h

    # Spring washer: on +Z side of FW2
    sw_center_z = fw2_center_z + fw_h / 2.0 + sw_h / 2.0

    # Nut: on +Z side of spring washer
    nut_center_z = sw_center_z + sw_h / 2.0 + h_nut / 2.0

    # Nut NXTRUSION local Z (relative to nut blank center)
    # POS at -Z end of nut: local_z = -h_nut / 2
    nut_nxtrusion_local_z = -h_nut / 2.0

    return {
        'bolt_head_center_z': bolt_head_center_z,
        'shaft_center_z': shaft_center_z,
        'interface_z': interface_z,
        'bolt_head_nxtrusion_local_z': bolt_head_nxtrusion_local_z,
        'fw1_center_z': fw1_center_z,
        'fw2_center_z': fw2_center_z,
        'sw_center_z': sw_center_z,
        'nut_center_z': nut_center_z,
        'nut_nxtrusion_local_z': nut_nxtrusion_local_z,
        'fw_h': fw_h,
        'center_distance': t_input + fw_h,
    }


# ============================================================
# Vertex Block Generation
# ============================================================

def generate_vertex_block(vertices, first_empty=False):
    """
    Generate NEW LOOP block with vertices.
    first_empty: if True, the first vertex has no POS line (empty vertex).
    Returns list of lines.
    """
    lines = []
    lines.append("NEW LOOP")
    lines.append("")

    for i, v in enumerate(vertices):
        lines.append("NEW VERTEX")
        if v is not None:
            x, y, z = v
            lines.append(f"POS X {fmt_val(x)} Y {fmt_val(y)} Z 0mm")
        lines.append("")
        lines.append("END")

    lines.append("END")
    return lines


# ============================================================
# TXT File Generation - Bocad format (v7)
# ============================================================

def generate_fastener_txt(bolt_size, bolt_length, t_input):
    """
    Generate fastener assembly TXT file in Bocad format (v7).

    v7 geometry:
      CYL 1: Bolt head (hex prism via 2x NXTRUSION on cylindrical blank)
      CYL 2: Bolt shaft (plain CYLINDER, no NREVOLUTION)
      CYL 3: Flat washer 1 (head side)
      CYL 4: Flat washer 2 (nut side)
      CYL 5: Spring washer
      CYL 6: Nut (hex prism via 2x NXTRUSION + NCYLINDER hole)
    """
    bolt = BOLT_DATA[bolt_size]
    nut = NUT_DATA[bolt_size]
    fw = FLAT_WASHER_DATA[bolt_size]
    sw = SPRING_WASHER_DATA.get(bolt_size)

    if sw is None:
        raise ValueError(f"No spring washer data for {bolt_size}")

    s_bolt = bolt['s']
    h_bolt = bolt['h']
    L = float(bolt_length)

    s_nut = nut['s']
    h_nut = nut['h']

    fw_d = fw['d']
    fw_h = fw['h']

    sw_d = sw['d']
    sw_h = sw['h']

    # Nominal diameter (shaft diameter)
    d_bolt = float(bolt_size.replace('M', ''))

    # Hex circumscribed diameters
    e_bolt = calc_hex_e(s_bolt)
    e_nut = calc_hex_e(s_nut)

    # Hex circumscribed radii
    R_bolt = e_bolt / 2.0
    R_nut = e_nut / 2.0

    # Scaling factor (relative to M20 reference)
    hex_scale_bolt = s_bolt / REF_S
    hex_scale_nut = s_nut / REF_S

    # Z positions
    z = calc_z_positions(bolt_size, bolt_length, t_input)

    # ---- Generate standard hex half-vertices for bolt head ----
    bolt_head_right_v = gen_hex_half_verts(R_bolt, 'right')
    bolt_head_left_v  = gen_hex_half_verts(R_bolt, 'left')

    # ---- Generate standard hex half-vertices for nut ----
    nut_right_v = gen_hex_half_verts(R_nut, 'right')
    nut_left_v  = gen_hex_half_verts(R_nut, 'left')

    # NXTRUSION X offset for bolt head (cut from -X side)
    bolt_head_nxtrusion_x = -R_bolt

    # NXTRUSION X offset for nut (cut from +X side for right, -X side for left)
    nut_nxtrusion_x_right = R_nut
    nut_nxtrusion_x_left = -R_nut

    # Left NXTRUSION tiny Y offset (avoids perfect overlap artifacts)
    left_y_offset = -0.01 * hex_scale_bolt
    nut_left_y_offset = -0.01 * hex_scale_nut

    # Date string
    now = datetime.datetime.now()
    date_str = f"{now.day}  {now.strftime('%b')} {now.year}"
    datetime_str = f"{now.day}  {now.strftime('%b')} {now.year} {now.hour:02d}:{now.minute:02d}"

    lines = []

    # ========================================
    # File header
    # ========================================
    lines.append("$S-  -- Synonym translation OFF")
    lines.append("-- ----------------------------------------------------------------")
    lines.append(f"-- Data Listing    Date : {datetime_str}")
    lines.append("")
    lines.append("ONERROR GOLABEL /ERROR3")
    lines.append("")
    lines.append("INPUT BEGIN")

    # ========================================
    # CYLINDER 1: BOLT HEAD (hex prism)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['bolt_head_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"DIAM {fmt_val(e_bolt)}")
    lines.append(f"HEIG {fmt_val(h_bolt)}")
    lines.append("")

    # Bolt head right NXTRUSION (standard hex right half)
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X {fmt_val(bolt_head_nxtrusion_x)} Y 0mm Z {fmt_val(z['bolt_head_nxtrusion_local_z'])}")
    lines.append("ORI Y is -X and Z is -Z")
    lines.append(f"HEIG {fmt_val(h_bolt)}")
    lines.append("")
    for vline in generate_vertex_block(bolt_head_right_v):
        lines.append(vline)
    lines.append("END")

    # Bolt head left NXTRUSION (standard hex left half)
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X {fmt_val(bolt_head_nxtrusion_x)} Y {fmt_val(left_y_offset)} Z {fmt_val(z['bolt_head_nxtrusion_local_z'])}")
    lines.append("ORI Y is -X and Z is -Z")
    lines.append(f"HEIG {fmt_val(h_bolt)}")
    lines.append("")
    for vline in generate_vertex_block(bolt_head_left_v):
        lines.append(vline)
    lines.append("END")

    lines.append("END")

    # ========================================
    # CYLINDER 2: BOLT SHAFT (plain cylinder)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['shaft_center_z'])}")
    lines.append(f"DIAM {fmt_val(d_bolt)}")
    lines.append(f"HEIG {fmt_val(L)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 3: FLAT WASHER 1 (head side)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['fw1_center_z'])}")
    lines.append(f"DIAM {fmt_val(fw_d)}")
    lines.append(f"HEIG {fmt_val(fw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 4: FLAT WASHER 2 (nut side)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['fw2_center_z'])}")
    lines.append(f"DIAM {fmt_val(fw_d)}")
    lines.append(f"HEIG {fmt_val(fw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 5: SPRING WASHER
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['sw_center_z'])}")
    lines.append(f"DIAM {fmt_val(sw_d)}")
    lines.append(f"HEIG {fmt_val(sw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 6: NUT (hex prism + inner hole)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['nut_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"DIAM {fmt_val(e_nut)}")
    lines.append(f"HEIG {fmt_val(h_nut)}")
    lines.append("")

    # Nut right NXTRUSION (standard hex right half)
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X {fmt_val(nut_nxtrusion_x_right)} Y 0mm Z {fmt_val(z['nut_nxtrusion_local_z'])}")
    lines.append(f"HEIG {fmt_val(h_nut)}")
    lines.append("")
    for vline in generate_vertex_block(nut_right_v):
        lines.append(vline)
    lines.append("END")

    # Nut left NXTRUSION (standard hex left half)
    lines.append("NEW NXTRUSION")
    lines.append(f"POS X {fmt_val(nut_nxtrusion_x_left)} Y {fmt_val(nut_left_y_offset)} Z {fmt_val(z['nut_nxtrusion_local_z'])}")
    lines.append(f"HEIG {fmt_val(h_nut)}")
    lines.append("")
    for vline in generate_vertex_block(nut_left_v):
        lines.append(vline)
    lines.append("END")

    # Nut inner hole (NCYLINDER)
    lines.append("NEW NCYLINDER")
    lines.append("POS X 0mm Y 0mm Z 0mm")
    lines.append(f"DIAM {fmt_val(d_bolt)}")
    lines.append(f"HEIG {fmt_val(h_nut)}")
    lines.append("")
    lines.append("END")

    lines.append("END")

    # ========================================
    # INPUT END line (6 CYLINDERs)
    # ========================================
    subequip = "/84XN001_FASTENER"
    end_line = (f"INPUT END  CYLINDER 1 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 2 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 3 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 4 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 5 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 6 of SUBEQUIPMENT {subequip}")
    lines.append(end_line)
    lines.append("INPUT FINISH")

    # ========================================
    # File footer
    # ========================================
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

    return '\n'.join(lines)


# ============================================================
# GUI Application (Chinese UI)
# ============================================================

class BoltGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("紧固件生成器for青岛MEHV")
        self.root.geometry("440x450")
        self.root.resizable(False, False)

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
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="紧固件装配参数",
                                font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Bolt size (dropdown)
        ttk.Label(main_frame, text="螺栓尺寸：").grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=8)
        self.bolt_size_var = tk.StringVar(value='')
        self.bolt_size_combo = ttk.Combobox(
            main_frame, textvariable=self.bolt_size_var,
            values=BOLT_SIZES, state='readonly', width=20)
        self.bolt_size_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        self.bolt_size_combo.bind('<<ComboboxSelected>>', self.on_bolt_size_change)

        # Connection thickness (T_input = actual connector thickness)
        ttk.Label(main_frame, text="连接件厚度：").grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=8)
        self.t_thickness_var = tk.StringVar(value='')
        vcmd = (self.root.register(self.validate_positive), '%P')
        self.t_thickness_entry = ttk.Entry(
            main_frame, textvariable=self.t_thickness_var,
            validate='key', validatecommand=vcmd, width=22)
        self.t_thickness_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=8)

        ttk.Label(main_frame, text="mm", foreground="#888").grid(
            row=2, column=2, sticky=tk.W, pady=8)

        # Bolt length (dropdown)
        ttk.Label(main_frame, text="螺栓长度：").grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=8)
        self.bolt_length_var = tk.StringVar(value='')
        self.bolt_length_combo = ttk.Combobox(
            main_frame, textvariable=self.bolt_length_var,
            values=[str(x) for x in BOLT_LENGTHS], state='readonly', width=20)
        self.bolt_length_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=8)

        ttk.Label(main_frame, text="mm", foreground="#888").grid(
            row=3, column=2, sticky=tk.W, pady=8)

        # Info frame
        self.info_frame = ttk.LabelFrame(main_frame, text="自动匹配尺寸", padding="10")
        self.info_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)

        self.info_text = tk.StringVar()
        self.info_label = ttk.Label(self.info_frame, textvariable=self.info_text,
                                     justify=tk.LEFT, foreground="#333")
        self.info_label.pack(anchor=tk.W)

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(15, 0))

        self.clear_btn = ttk.Button(btn_frame, text="清除全部输入",
                                     command=self.clear_all, width=15)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        self.generate_btn = ttk.Button(btn_frame, text="生成紧固件",
                                        command=self.generate_fastener, width=15)
        self.generate_btn.pack(side=tk.LEFT, padx=10)

        # Initial info
        self.update_info()

    def validate_positive(self, value):
        """Validate input is a positive number (int or float)"""
        if value == '':
            return True
        try:
            num = float(value)
            return num >= 0
        except ValueError:
            return False

    def on_bolt_size_change(self, event=None):
        """Update info when bolt size changes"""
        self.update_info()

    def update_info(self):
        """Update matched dimension info (Chinese)"""
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

        self.info_text.set(info)

    def clear_all(self):
        """Clear all inputs"""
        self.bolt_size_var.set('')
        self.t_thickness_var.set('')
        self.bolt_length_var.set('')
        self.update_info()

    def generate_fastener(self):
        """Generate fastener TXT file"""
        # Validate inputs
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

        bolt_length_str = self.bolt_length_var.get()
        if not bolt_length_str:
            messagebox.showwarning("警告", "请选择螺栓长度")
            return

        bolt_length = int(bolt_length_str)

        # Check spring washer data
        if bolt_size not in SPRING_WASHER_DATA:
            messagebox.showerror("错误",
                f"{bolt_size} 无弹簧垫片数据。\n"
                f"支持规格：M6 ~ M48")
            return

        fw_h = FLAT_WASHER_DATA[bolt_size]['h']
        center_dist = t_input + fw_h

        # Default filename
        t_formatted = fmt_thickness(t_input)
        default_name = f"{bolt_size}x{bolt_length}-{t_formatted}.txt"

        # Save dialog
        file_path = filedialog.asksaveasfilename(
            title="导出 TXT 文件",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if not file_path:
            return  # User cancelled

        try:
            content = generate_fastener_txt(bolt_size, bolt_length, t_input)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            messagebox.showinfo("成功",
                f"紧固件 TXT 文件生成成功！\n\n"
                f"文件：{file_path}\n"
                f"螺栓规格：{bolt_size}\n"
                f"螺栓长度：{bolt_length} mm\n"
                f"连接件厚度：{t_input} mm\n"
                f"平垫片中心距：{center_dist} mm")

        except Exception as e:
            messagebox.showerror("错误", f"生成文件时出错：\n{str(e)}")


# ============================================================
# Main Entry
# ============================================================

def main():
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use('clam')
    except:
        pass

    app = BoltGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
