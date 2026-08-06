# -*- coding: utf-8 -*-
"""
Fastener Assembly TXT Generator v11
Generates Bocad-format fastener assembly input files based on
bolt size, connection thickness, and bolt length margin.

v11: UI simplified — bolt length L is auto-calculated, no manual selection.
     Added "bolt length margin" dropdown (1P~5P, default 2P).
     L_required = 2*t_w + t_spring + t_nut + T_conn + n*P
     L = smallest standard length >= L_required (from GB/T 5783 series).

v10 (carried over, unchanged):
     Blank geometry changed from CYLINDER to BOX (rectangular prism).
     Hex head/nut cut by 4 corner NXTRUSIONs (3-vertex triangles)
     instead of 2 side NXTRUSIONs (10-vertex profiles).
     Nut inner hole (NCYLINDER) removed.
     NREVOLUTION outer radius = s_bolt (full Y dimension of BOX).

  - Bolt: single BOX blank + NREVOLUTION shaft + 4x NXTRUSION hex head
  - Nut: BOX blank + 4x NXTRUSION (full-height corner cuts, no inner hole)
  - Flat washers & spring washer: simple CYLINDER
  - Total: 2 BOX + 3 CYLINDER = 5 bodies

  - Algorithm: T_input = actual connector thickness T_conn
               Center distance = T_input + t_w
  - UI: Chinese labels, title "紧固件生成器for MEHV"
  - Filename: M{size}x{length}-{thickness}.txt
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

# v11: Thread pitch P for each bolt size (mm)
PITCH_DATA = {
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

# v11: GB/T 5783 nominal length standard series (mm)
BOLT_LENGTH_SERIES = [
    20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70,
    80, 90, 100, 110, 120, 130, 140, 150, 160,
    180, 200, 220, 240, 260, 280, 300, 320, 340,
    360, 380, 400, 420, 440, 460, 480, 500, 520,
    540, 560, 580, 600, 620, 640
]

# v11: Available length range per size (min, max) in mm
BOLT_LENGTH_RANGE = {
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

# v11: Bolt length margin options (display text)
LENGTH_MARGIN_OPTIONS = ['1P', '2P', '3P', '4P', '5P']
DEFAULT_MARGIN = '2P'

# Bolt size list (ordered)
BOLT_SIZES = ['M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M18', 'M20',
              'M22', 'M24', 'M30', 'M36', 'M42', 'M48', 'M56', 'M64']

# Hex geometry constant: e = s / cos(30 deg) = s * 2/sqrt(3) = s * 1.1547
HEX_E_FACTOR = 1.1547

# tan(30 deg) = 1/sqrt(3) = 0.5774
TAN_30 = 0.5774

# Bolt tip Z position (fixed reference, +Z end of bolt)
REF_BOLT_TIP_Z = 25.0

# Reference X/Y position for assembly
REF_X = -256.0
REF_Y = 632.22


# ============================================================
# Helper Functions
# ============================================================

def fmt_val(val):
    """Format a numeric value with 'mm' suffix, no trailing zeros."""
    if val == int(val):
        return f"{int(val)}mm"
    else:
        # Remove trailing zeros
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return f"{s}mm"


def fmt_thickness(val):
    """Format thickness value for filename (v7/v8 convention)."""
    if val == int(val):
        return f"{int(val)}"
    else:
        s = f"{val:.2f}".rstrip('0').rstrip('.')
        return s


def calc_hex_e(s):
    """
    Hex circumscribed diameter (corner-to-corner).
    e = s * 1.1547  (standard hex geometry: s / cos(30 deg))
    """
    return s * HEX_E_FACTOR


def calc_cut_x(s):
    """
    Horizontal cut distance for corner triangle NXTRUSION.
    cut_x = (s/2) * tan(30 deg) = s/2 * 0.5774
    This equals e/4 since e = s * 2/sqrt(3) and e/4 = s/(2*sqrt(3)).
    """
    return (s / 2.0) * TAN_30


def calc_shaft_vertices(d_bolt, s_bolt, L):
    """
    v10: Calculate shaft NREVOLUTION vertices directly.
    5 vertices forming the shaft profile (revolved around X axis).
    Outer radius = s_bolt (full Y dimension of BOX, ensures cut-through).
    Inner radius = d_bolt / 2 (nominal shaft radius).

    v1: inner radius at bolt tip (X=0)
    v2: outer radius at bolt tip (X=0)
    v3: outer radius at head end (X=-L)
    v4: inner radius at head end (X=-L)
    v5: same as v1 (close loop)
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


def calc_corner_nxtrusion_vertices(corner, s, cut_x):
    """
    v10: Generate 3-vertex triangle for a single corner NXTRUSION.
    First vertex is empty (no POS, corner origin).

    corner: one of 'X+Y-', 'X-Y-', 'X+Y+', 'X-Y+'
    s: flat-to-flat distance (YLEN of BOX)
    cut_x: horizontal cut distance = (s/2) * tan(30)

    Triangle vertices (local NXTRUSION coords, origin at box corner):
      v1: empty (corner point = origin)
      v2: along Y toward center -> hex vertex on that side
      v3: along X toward center -> end of the adjacent flat

    X-Y- corner has tiny Y offset (0.01mm) to match reference template.
    """
    half_s = s / 2.0

    if corner == 'X+Y-':
        # Top-right corner (X+, Y-): v2 goes +Y, v3 goes -X
        v2 = (0, half_s, 0)
        v3 = (-cut_x, 0, 0)
    elif corner == 'X-Y-':
        # Top-left corner (X-, Y-): v2 goes +Y, v3 goes +X
        # Tiny Y offset to match reference template
        v2 = (0, half_s + 0.01, 0)
        v3 = (cut_x, 0, 0)
    elif corner == 'X+Y+':
        # Bottom-right corner (X+, Y+): v2 goes -Y, v3 goes -X
        v2 = (0, -half_s, 0)
        v3 = (-cut_x, 0, 0)
    elif corner == 'X-Y+':
        # Bottom-left corner (X-, Y+): v2 goes -Y, v3 goes +X
        v2 = (0, -half_s, 0)
        v3 = (cut_x, 0, 0)
    else:
        raise ValueError(f"Unknown corner: {corner}")

    return [None, v2, v3]


# ============================================================
# v11: Bolt Length Auto-Calculation
# ============================================================

def calc_required_length(bolt_size, t_conn, margin_n):
    """
    v11: Calculate required bolt length L_required.

    Formula: L_required = 2*t_w + t_spring + t_nut + T_conn + n*P

    Args:
        bolt_size: e.g. 'M20'
        t_conn: connector thickness in mm
        margin_n: integer 1~5, number of P for margin

    Returns:
        L_required in mm (float)
    """
    t_w = FLAT_WASHER_DATA[bolt_size]['h']       # flat washer thickness
    t_spring = SPRING_WASHER_DATA[bolt_size]['h']  # spring washer thickness
    t_nut = NUT_DATA[bolt_size]['h']              # nut height
    P = PITCH_DATA[bolt_size]                     # thread pitch

    L_required = 2 * t_w + t_spring + t_nut + t_conn + margin_n * P
    return L_required


def select_bolt_length(bolt_size, L_required):
    """
    v11: Select the smallest standard nominal length >= L_required
    from GB/T 5783 series, clamped to the size's available range.

    Args:
        bolt_size: e.g. 'M20'
        L_required: minimum required length in mm

    Returns:
        (bolt_length, status) where status is 'ok' or 'too_thick'
        bolt_length is the selected standard length (int),
        or None if L_required exceeds max available length.
    """
    L_min, L_max = BOLT_LENGTH_RANGE[bolt_size]

    if L_required > L_max:
        return None, 'too_thick'

    # Filter standard series to available range for this size
    available = [L for L in BOLT_LENGTH_SERIES if L_min <= L <= L_max]

    # Find smallest L >= L_required
    for L in available:
        if L >= L_required:
            return L, 'ok'

    # Should not reach here if L_required <= L_max
    return None, 'too_thick'


def margin_text_to_n(margin_text):
    """
    v11: Convert margin display text (e.g. '2P') to integer n (e.g. 2).
    """
    return int(margin_text.replace('P', ''))


# ============================================================
# Z Position Calculations (v7/v8/v9 algorithm, unchanged)
# ============================================================

def calc_z_positions(bolt_size, bolt_length, t_input):
    """
    Calculate all Z positions.
    Bolt tip (+Z end) at Z = REF_BOLT_TIP_Z (25mm).

    v7/v8/v9 algorithm (unchanged in v10/v11):
      - T_input = actual connector thickness T_conn
      - FW center-to-center distance = T_input + t_w
      - FW1 center = interface_z + t_w/2
      - FW2 center = FW1 center + (T_input + t_w)

    Bolt structure (v10 BOX blank):
      BOX blank: total height = L + h_bolt
      NREVOLUTION: cuts shaft profile (length L, from tip to head interface)
      4x NXTRUSION: cuts hex head profile (height h, at head end)

    Stacking from -Z to +Z:
      bolt head -> flat washer 1 -> [T_conn] -> flat washer 2
      -> spring washer -> nut
    """
    bolt = BOLT_DATA[bolt_size]
    h_bolt = bolt['h']
    L = float(bolt_length)

    fw_h = FLAT_WASHER_DATA[bolt_size]['h']
    sw_h = SPRING_WASHER_DATA.get(bolt_size, {}).get('h', 0)
    h_nut = NUT_DATA[bolt_size]['h']

    # Bolt blank total height = shaft length + head height
    bolt_total_h = L + h_bolt

    # Bolt center Z (BOX center)
    bolt_center_z = REF_BOLT_TIP_Z - bolt_total_h / 2.0

    # Bolt head NXTRUSION local Z (relative to BOX center)
    # POS Z = -(L+h)/2  (at -Z end of BOX, head side)
    bolt_head_local_z = -bolt_total_h / 2.0

    # Shaft NREVOLUTION local Z (relative to BOX center)
    # POS Z = (L + h) / 2  (at +Z end of BOX, bolt tip side)
    shaft_local_z = bolt_total_h / 2.0

    # Head-shaft interface global Z
    interface_z = REF_BOLT_TIP_Z - L

    # Flat washer 1: against head (head side)
    # FW1 -Z face = head +Z face = interface_z
    fw1_center_z = interface_z + fw_h / 2.0

    # Flat washer 2: nut side
    # v7 algorithm: center distance = T_input + t_w
    fw2_center_z = fw1_center_z + t_input + fw_h

    # Spring washer: on +Z side of FW2
    sw_center_z = fw2_center_z + fw_h / 2.0 + sw_h / 2.0

    # Nut: on +Z side of spring washer
    nut_center_z = sw_center_z + sw_h / 2.0 + h_nut / 2.0

    # Nut NXTRUSION local Z (relative to nut BOX center)
    # POS Z = -h_nut / 2  (at nut -Z end)
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


# ============================================================
# Vertex Block Generation
# ============================================================

def generate_vertex_block(vertices):
    """
    Generate NEW LOOP block with vertices.
    First vertex is empty (no POS line) if vertices[0] is None.
    Returns list of lines.
    """
    lines = []
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


# ============================================================
# TXT File Generation - Bocad format (v10 BOX geometry)
# ============================================================

def generate_fastener_txt(bolt_size, bolt_length, t_input):
    """
    Generate fastener assembly TXT file in Bocad format.
    v10: BOX blanks + 4 corner NXTRUSIONs for hex head/nut.
         NREVOLUTION for shaft (outer radius = s_bolt).
         No nut inner hole (NCYLINDER removed).

    5 bodies:
      BOX 1: Bolt (BOX blank + NREVOLUTION + 4x NXTRUSION)
      BOX 2: Nut (BOX blank + 4x NXTRUSION)
      CYLINDER 1: Flat washer 1 (head side)
      CYLINDER 2: Flat washer 2 (nut side)
      CYLINDER 3: Spring washer
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

    # Nominal diameter
    d_bolt = float(bolt_size.replace('M', ''))

    # v10: Hex circumscribed diameters (e = s * 1.1547)
    e_bolt = calc_hex_e(s_bolt)
    e_nut = calc_hex_e(s_nut)

    # v10: Corner cut distances
    cut_x_bolt = calc_cut_x(s_bolt)
    cut_x_nut = calc_cut_x(s_nut)

    # Z positions (v7/v8/v9 algorithm, unchanged)
    z = calc_z_positions(bolt_size, bolt_length, t_input)

    # v10: Shaft NREVOLUTION vertices (outer radius = s_bolt)
    shaft_v = calc_shaft_vertices(d_bolt, s_bolt, L)

    # v10: 4 corner NXTRUSION vertices for bolt head
    bolt_corners = ['X+Y-', 'X-Y-', 'X+Y+', 'X-Y+']
    bolt_head_nx_v = {}
    for corner in bolt_corners:
        bolt_head_nx_v[corner] = calc_corner_nxtrusion_vertices(
            corner, s_bolt, cut_x_bolt)

    # v10: 4 corner NXTRUSION vertices for nut
    nut_nx_v = {}
    for corner in bolt_corners:
        nut_nx_v[corner] = calc_corner_nxtrusion_vertices(
            corner, s_nut, cut_x_nut)

    # NXTRUSION position offsets (4 corners of BOX cross-section)
    def corner_pos(corner, e_val, s_val, local_z):
        half_e = e_val / 2.0
        half_s = s_val / 2.0
        if corner == 'X+Y-':
            return (half_e, -half_s, local_z)
        elif corner == 'X-Y-':
            return (-half_e, -half_s, local_z)
        elif corner == 'X+Y+':
            return (half_e, half_s, local_z)
        elif corner == 'X-Y+':
            return (-half_e, half_s, local_z)

    # Date string (matches reference format)
    now = datetime.datetime.now()
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
    # BOX 1: BOLT (BOX blank + NREVOLUTION + 4x NXTRUSION)
    # ========================================
    lines.append("NEW BOX")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['bolt_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"XLEN {fmt_val(e_bolt)}")
    lines.append(f"YLEN {fmt_val(s_bolt)}")
    lines.append(f"ZLEN {fmt_val(z['bolt_total_h'])}")
    lines.append("")

    # Shaft NREVOLUTION
    lines.append("NEW NREVOLUTION")
    lines.append(f"POS X 0mm Y 0mm Z {fmt_val(z['shaft_local_z'])}")
    lines.append("ORI Y is -X and Z is -Y")
    lines.append("ANGL 0degree")
    lines.append("")
    for vline in generate_vertex_block(shaft_v):
        lines.append(vline)
    lines.append("END")

    # Bolt head 4x NXTRUSION (corner cuts, head height only)
    for corner in bolt_corners:
        nx, ny, nz = corner_pos(corner, e_bolt, s_bolt, z['bolt_head_local_z'])
        lines.append("NEW NXTRUSION")
        lines.append(f"POS X {fmt_val(nx)} Y {fmt_val(ny)} Z {fmt_val(nz)}")
        lines.append(f"HEIG {fmt_val(h_bolt)}")
        lines.append("")
        for vline in generate_vertex_block(bolt_head_nx_v[corner]):
            lines.append(vline)
        lines.append("END")

    lines.append("END")

    # ========================================
    # BOX 2: NUT (BOX blank + 4x NXTRUSION, no inner hole)
    # ========================================
    lines.append("NEW BOX")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['nut_center_z'])}")
    lines.append("ORI Y is -Y and Z is Z")
    lines.append(f"XLEN {fmt_val(e_nut)}")
    lines.append(f"YLEN {fmt_val(s_nut)}")
    lines.append(f"ZLEN {fmt_val(h_nut)}")
    lines.append("")

    # Nut 4x NXTRUSION (corner cuts, full nut height)
    for corner in bolt_corners:
        nx, ny, nz = corner_pos(corner, e_nut, s_nut, z['nut_nxtrusion_local_z'])
        lines.append("NEW NXTRUSION")
        lines.append(f"POS X {fmt_val(nx)} Y {fmt_val(ny)} Z {fmt_val(nz)}")
        lines.append(f"HEIG {fmt_val(h_nut)}")
        lines.append("")
        for vline in generate_vertex_block(nut_nx_v[corner]):
            lines.append(vline)
        lines.append("END")

    lines.append("END")

    # ========================================
    # CYLINDER 1: FLAT WASHER 1 (head side)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['fw1_center_z'])}")
    lines.append(f"DIAM {fmt_val(fw_d)}")
    lines.append(f"HEIG {fmt_val(fw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 2: FLAT WASHER 2 (nut side)
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['fw2_center_z'])}")
    lines.append(f"DIAM {fmt_val(fw_d)}")
    lines.append(f"HEIG {fmt_val(fw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # CYLINDER 3: SPRING WASHER
    # ========================================
    lines.append("NEW CYLINDER")
    lines.append(f"POS X {fmt_val(REF_X)} Y {fmt_val(REF_Y)} Z {fmt_val(z['sw_center_z'])}")
    lines.append(f"DIAM {fmt_val(sw_d)}")
    lines.append(f"HEIG {fmt_val(sw_h)}")
    lines.append("")
    lines.append("END")

    # ========================================
    # INPUT END line (2 BOX + 3 CYLINDER, v10 format)
    # ========================================
    subequip = "/84XN001_FASTENER"
    end_line = (f"INPUT END  BOX 1 of SUBEQUIPMENT {subequip} "
                f"BOX 2 of SUBEQUIPMENT {subequip} "
                f"CYLINDER 1 of $")
    lines.append(end_line)
    lines.append(f"SUBEQUIPMENT {subequip} CYLINDER 2 of SUBEQUIPMENT {subequip} CYLINDER 3 of SUBEQUIPMENT {subequip}")
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
# GUI Application (Chinese UI - v11 with auto length)
# ============================================================

class BoltGeneratorApp:
    def __init__(self, root):
        self.root = root
        # v11: title changed from "紧固件生成器for青岛MEHV" to "紧固件生成器for MEHV"
        self.root.title("紧固件生成器for MEHV")
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
        self.bolt_size_combo.bind('<<ComboboxSelected>>', self.on_param_change)

        # Connection thickness (T_input = actual connector thickness)
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

        # v11: Bolt length margin dropdown (replaces manual bolt length)
        ttk.Label(main_frame, text="螺栓长度余量：").grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=8)
        self.margin_var = tk.StringVar(value=DEFAULT_MARGIN)
        self.margin_combo = ttk.Combobox(
            main_frame, textvariable=self.margin_var,
            values=LENGTH_MARGIN_OPTIONS, state='readonly', width=20)
        self.margin_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=8)
        self.margin_combo.bind('<<ComboboxSelected>>', self.on_param_change)

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

    def on_param_change(self, event=None):
        """Update info when any parameter changes"""
        self.update_info()

    def update_info(self):
        """Update matched dimension info (Chinese)
        v11: Added bolt length line at the end.
        """
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

        # v11: Auto-calculate and display bolt length if T_conn is provided
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

    def clear_all(self):
        """Clear all inputs"""
        self.bolt_size_var.set('')
        self.t_thickness_var.set('')
        self.margin_var.set(DEFAULT_MARGIN)
        self.update_info()

    def generate_fastener(self):
        """Generate fastener TXT file
        v11: Bolt length is auto-calculated, no manual input.
        """
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

        # Check spring washer data
        if bolt_size not in SPRING_WASHER_DATA:
            messagebox.showerror("错误",
                f"{bolt_size} 无弹簧垫片数据。\n"
                f"支持规格：M6 ~ M48")
            return

        # v11: Auto-calculate bolt length
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

        # Default filename (v7/v8 convention: M{size}x{length}-{thickness}.txt)
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
                f"紧固件 DB 文件生成成功！\n\n"
                f"文件：{file_path}\n"
                f"螺栓规格：{bolt_size}\n"
                f"螺栓长度：{bolt_length} mm\n"
                f"螺栓长度余量：{margin_text}\n"
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
