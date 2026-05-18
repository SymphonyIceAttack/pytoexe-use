# -*- coding: utf-8 -*-
"""
NCS32100 快速设计工具 v3

依赖：
    pip install numpy matplotlib
运行：
    python NCS32100_tool_v3.py

说明：
    本程序用于快速解析/半解析设计筛选，不替代 FEM、Gerber 寄生提取、样机实测和 NCS32100 实机校准。
"""

import csv
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
import numpy as np

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import Rectangle


# ======================================================================
# 视觉主题常量
# ======================================================================
class Theme:
    """集中管理配色与字体，便于统一风格（浅色明亮主题）。"""
    BG = "#F4F6FB"            # 主背景（浅灰蓝）
    BG_PANEL = "#FFFFFF"      # 卡片背景（白）
    BG_PANEL_ALT = "#EDF1F8"  # 卡片备用背景 / 斑马纹
    BG_INPUT = "#FFFFFF"      # 输入框背景
    FG = "#1F2A44"            # 主文字（深蓝灰）
    FG_MUTED = "#65718C"      # 次要文字
    ACCENT = "#2F6BFF"        # 主强调色（蓝）
    ACCENT_DARK = "#1F50CC"
    SUCCESS = "#22A861"       # 成功（绿）
    WARNING = "#E08A00"       # 警告（橙）
    DANGER = "#E0443E"        # 错误（红）
    BORDER = "#D6DEEC"
    GRID = "#E3E9F4"

    FONT_FAMILY = "Microsoft YaHei"
    FONT_MONO = "Consolas"

    # matplotlib 配色（浅色）
    PLOT_BG = "#FFFFFF"
    PLOT_AXES_BG = "#FBFCFE"
    PLOT_FG = "#1F2A44"
    PLOT_GRID = "#E3E9F4"
    PLOT_CYCLE = ["#2F6BFF", "#22A861", "#E08A00", "#E0443E",
                  "#7C5CFF", "#0FB5C9", "#D6478C", "#C9A227"]


def setup_cn_font():
    """尽量启用中文字体；如果系统没有对应字体，matplotlib 会自动回退。"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC",
        "Arial Unicode MS", "DejaVu Sans"
    ]
    plt.rcParams["axes.unicode_minus"] = False
    # 全局 matplotlib 浅色风格
    plt.rcParams["figure.facecolor"] = Theme.PLOT_BG
    plt.rcParams["axes.facecolor"] = Theme.PLOT_AXES_BG
    plt.rcParams["axes.edgecolor"] = Theme.BORDER
    plt.rcParams["axes.labelcolor"] = Theme.PLOT_FG
    plt.rcParams["text.color"] = Theme.PLOT_FG
    plt.rcParams["xtick.color"] = Theme.FG_MUTED
    plt.rcParams["ytick.color"] = Theme.FG_MUTED
    plt.rcParams["grid.color"] = Theme.PLOT_GRID
    plt.rcParams["axes.titlecolor"] = Theme.PLOT_FG
    plt.rcParams["savefig.facecolor"] = Theme.PLOT_BG


setup_cn_font()


MATERIALS = {
    "铜 / Copper": {"rho": 1.724e-8, "mur": 1.0, "note": "PCB 铜箔"},
    "铝 6061 / Aluminum 6061": {"rho": 4.0e-8, "mur": 1.0, "note": "常见铝合金目标件"},
    "黄铜 / Brass": {"rho": 6.3e-8, "mur": 1.0, "note": "电导率低于铜"},
    "不锈钢 304 / Stainless 304": {"rho": 7.2e-7, "mur": 1.02, "note": "弱导电，涡流响应较弱"},
}

COIL_MODES = [
    "Fine+Coarse 三相绝对角模式",
    "Fine 三相相对角模式",
    "Fine 两相 sin/cos 简化模式",
]

RX_MODELS = [
    "理想正弦三相接收",
    "Twisted loop 抑制偶次谐波",
    "Dogbone/面积权重近似",
    "谐波应力测试",
]

DRIVE_MODELS = [
    "固定 Tx 电流",
    "串联 LC 电压驱动",
    "方波基波等效",
    "AGC 归一化电流",
]


def mm_to_m(x_mm: float) -> float:
    return x_mm * 1e-3


def circular_error_deg(pred_deg: np.ndarray, true_deg: np.ndarray) -> np.ndarray:
    """返回 [-180, 180) 范围内的角度误差，单位 deg。"""
    return (pred_deg - true_deg + 180.0) % 360.0 - 180.0


def wrap_2pi(x):
    return np.mod(x, 2.0 * np.pi)


def clarke_3phase(a, b, c):
    """三相 120° 信号到 alpha/beta。"""
    alpha = (2.0 / 3.0) * (a - 0.5 * b - 0.5 * c)
    beta = (2.0 / 3.0) * ((np.sqrt(3.0) / 2.0) * (b - c))
    return alpha, beta


def circular_phase_error(phi1, phi2):
    return np.angle(np.exp(1j * (phi1 - phi2)))


def mohan_planar_spiral_L(n_turns, r_inner_mm, r_outer_mm):
    """
    Mohan 近似圆形平面螺旋自感，单位 H。
    这里用于快速趋势估算，不用于替代电磁场仿真。
    """
    mu0 = 4.0 * np.pi * 1e-7
    r_in = mm_to_m(r_inner_mm)
    r_out = mm_to_m(r_outer_mm)
    d_in = 2.0 * r_in
    d_out = 2.0 * r_out
    d_avg = 0.5 * (d_in + d_out)
    fill = (d_out - d_in) / max(d_out + d_in, 1e-12)
    fill = np.clip(fill, 1e-6, 0.95)
    # circular spiral empirical form
    return mu0 * n_turns**2 * d_avg / 2.0 * (np.log(2.46 / fill) + 0.20 * fill**2)


def skin_depth_m(freq_hz, rho, mur=1.0):
    mu0 = 4.0 * np.pi * 1e-7
    omega = 2.0 * np.pi * freq_hz
    return math.sqrt(2.0 * rho / max(omega * mu0 * mur, 1e-30))


def estimate_ac_resistance(freq_hz, rho, mur, trace_width_mm, copper_thickness_um, length_mm):
    """单根走线高频 AC 电阻趋势估算。"""
    delta = skin_depth_m(freq_hz, rho, mur)
    t = copper_thickness_um * 1e-6
    w = mm_to_m(trace_width_mm)
    length = mm_to_m(length_mm)
    effective_t = min(t, max(delta, 1e-9))
    area = max(w * effective_t, 1e-15)
    return rho * length / area, delta


# ======================================================================
# 样式工厂：集中创建 ttk 样式
# ======================================================================
def build_styles(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    T = Theme

    # 全局
    style.configure(".",
                    background=T.BG,
                    foreground=T.FG,
                    fieldbackground=T.BG_INPUT,
                    bordercolor=T.BORDER,
                    font=(T.FONT_FAMILY, 10))

    style.configure("TFrame", background=T.BG)
    style.configure("Panel.TFrame", background=T.BG_PANEL)
    style.configure("Card.TFrame", background=T.BG_PANEL)

    style.configure("TLabel", background=T.BG, foreground=T.FG)
    style.configure("Panel.TLabel", background=T.BG_PANEL, foreground=T.FG)
    style.configure("Muted.TLabel", background=T.BG, foreground=T.FG_MUTED)
    style.configure("PanelMuted.TLabel", background=T.BG_PANEL, foreground=T.FG_MUTED)
    style.configure("Header.TLabel", background=T.BG, foreground=T.FG,
                    font=(T.FONT_FAMILY, 17, "bold"))
    style.configure("SubHeader.TLabel", background=T.BG, foreground=T.FG_MUTED,
                    font=(T.FONT_FAMILY, 10))
    style.configure("CardTitle.TLabel", background=T.BG_PANEL, foreground=T.ACCENT,
                    font=(T.FONT_FAMILY, 11, "bold"))
    style.configure("GridHead.TLabel", background=T.BG_PANEL_ALT, foreground=T.FG,
                    font=(T.FONT_FAMILY, 10, "bold"))

    # LabelFrame -> 卡片
    style.configure("Card.TLabelframe",
                    background=T.BG_PANEL,
                    bordercolor=T.BORDER,
                    relief="flat",
                    borderwidth=1)
    style.configure("Card.TLabelframe.Label",
                    background=T.BG_PANEL,
                    foreground=T.ACCENT,
                    font=(T.FONT_FAMILY, 11, "bold"))

    # 输入框
    style.configure("TEntry",
                    fieldbackground=T.BG_INPUT,
                    foreground=T.FG,
                    bordercolor=T.BORDER,
                    insertcolor=T.FG,
                    padding=4)
    style.map("TEntry",
              bordercolor=[("focus", T.ACCENT)],
              fieldbackground=[("focus", T.BG_INPUT)])

    # Combobox
    style.configure("TCombobox",
                    fieldbackground=T.BG_INPUT,
                    background=T.BG_INPUT,
                    foreground=T.FG,
                    arrowcolor=T.ACCENT,
                    bordercolor=T.BORDER,
                    padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", T.BG_INPUT)],
              foreground=[("readonly", T.FG)],
              bordercolor=[("focus", T.ACCENT)])

    # 主按钮
    style.configure("Accent.TButton",
                    background=T.ACCENT,
                    foreground="#FFFFFF",
                    font=(T.FONT_FAMILY, 10, "bold"),
                    borderwidth=0,
                    focusthickness=0,
                    padding=(16, 9))
    style.map("Accent.TButton",
              background=[("active", T.ACCENT_DARK), ("pressed", T.ACCENT_DARK)])

    # 次按钮
    style.configure("Ghost.TButton",
                    background=T.BG_PANEL_ALT,
                    foreground=T.FG,
                    font=(T.FONT_FAMILY, 10),
                    borderwidth=0,
                    focusthickness=0,
                    padding=(14, 8))
    style.map("Ghost.TButton",
              background=[("active", T.BORDER), ("pressed", T.BORDER)])

    # 成功按钮
    style.configure("Success.TButton",
                    background=T.SUCCESS,
                    foreground="#FFFFFF",
                    font=(T.FONT_FAMILY, 10, "bold"),
                    borderwidth=0,
                    focusthickness=0,
                    padding=(16, 9))
    style.map("Success.TButton",
              background=[("active", "#1B8C50"), ("pressed", "#1B8C50")])

    # Checkbutton
    style.configure("TCheckbutton",
                    background=T.BG_PANEL,
                    foreground=T.FG,
                    focuscolor=T.BG_PANEL)
    style.map("TCheckbutton",
              background=[("active", T.BG_PANEL)],
              indicatorcolor=[("selected", T.ACCENT), ("!selected", T.BG_INPUT)])

    # Radiobutton
    style.configure("TRadiobutton",
                    background=T.BG_PANEL,
                    foreground=T.FG,
                    focuscolor=T.BG_PANEL,
                    font=(T.FONT_FAMILY, 10))
    style.map("TRadiobutton",
              background=[("active", T.BG_PANEL)],
              foreground=[("active", T.ACCENT)],
              indicatorcolor=[("selected", T.ACCENT), ("!selected", T.BG_INPUT)])

    # Notebook 选项卡
    style.configure("TNotebook",
                    background=T.BG,
                    borderwidth=0,
                    tabmargins=(2, 6, 2, 0))
    style.configure("TNotebook.Tab",
                    background=T.BG_PANEL,
                    foreground=T.FG_MUTED,
                    padding=(20, 11),
                    font=(T.FONT_FAMILY, 10, "bold"),
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", T.ACCENT), ("active", T.BG_PANEL_ALT)],
              foreground=[("selected", "#FFFFFF"), ("active", T.FG)])

    # 滚动条
    style.configure("Vertical.TScrollbar",
                    background=T.BG_PANEL_ALT,
                    troughcolor=T.BG,
                    bordercolor=T.BG,
                    arrowcolor=T.FG_MUTED,
                    width=12)
    style.map("Vertical.TScrollbar",
              background=[("active", T.ACCENT)])

    return style


def style_axis(ax):
    """统一单个 axes 的暗色外观。"""
    ax.set_facecolor(Theme.PLOT_AXES_BG)
    for spine in ax.spines.values():
        spine.set_color(Theme.BORDER)
    ax.tick_params(colors=Theme.FG_MUTED, labelsize=8)
    ax.grid(True, alpha=0.22, color=Theme.PLOT_GRID, linewidth=0.7)


def style_legend(ax):
    leg = ax.legend(fontsize=8, facecolor=Theme.BG_PANEL,
                    edgecolor=Theme.BORDER, labelcolor=Theme.FG)
    if leg:
        leg.get_frame().set_alpha(0.92)
    return leg


# ======================================================================
# 可滚动容器（暗色）
# ======================================================================
class ScrollableFrame(ttk.Frame):
    def __init__(self, master, style_name="TFrame"):
        super().__init__(master, style=style_name)
        self.canvas = tk.Canvas(self, highlightthickness=0,
                                bg=Theme.BG, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview,
                                       style="Vertical.TScrollbar")
        self.body = ttk.Frame(self.canvas, style=style_name)
        self.body.bind("<Configure>",
                       lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass


class NCS32100Tool:
    def __init__(self, root):
        self.root = root
        self.root.title("NCS32100 中文高精度快速设计工具 v3")
        self.root.geometry("1360x880")
        self.root.minsize(1140, 740)
        self.root.configure(bg=Theme.BG)

        self.style = build_styles(self.root)

        self.structure_confirmed = False
        self.latest_results = None
        self.latest_lines = []

        self.structure_vars = {}
        self.operation_vars = {}
        self.error_vars = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        # ---- 顶部标题栏 ----
        header = tk.Frame(self.root, bg=Theme.BG_PANEL, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        # 左侧强调竖条 + 标题
        accent_bar = tk.Frame(header, bg=Theme.ACCENT, width=5)
        accent_bar.pack(side="left", fill="y", padx=(0, 0))

        title_box = tk.Frame(header, bg=Theme.BG_PANEL)
        title_box.pack(side="left", fill="y", padx=20, pady=12)

        tk.Label(title_box, text="NCS32100 电感编码器设计工具",
                 bg=Theme.BG_PANEL, fg=Theme.FG,
                 font=(Theme.FONT_FAMILY, 17, "bold")).pack(anchor="w")
        tk.Label(title_box,
                 text="结构确认  →  解析 / 半解析计算  →  可选曲线结果显示",
                 bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 10)).pack(anchor="w", pady=(3, 0))

        # 右侧版本徽章
        badge = tk.Label(header, text="  v3  ",
                         bg=Theme.ACCENT, fg="#FFFFFF",
                         font=(Theme.FONT_FAMILY, 11, "bold"))
        badge.pack(side="right", padx=24)

        # 分隔线
        tk.Frame(self.root, bg=Theme.BORDER, height=1).pack(fill="x")

        # ---- Notebook ----
        nb_wrap = ttk.Frame(self.root, style="TFrame", padding=(12, 12, 12, 12))
        nb_wrap.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(nb_wrap)
        self.notebook.pack(fill="both", expand=True)

        self.tab_structure = ScrollableFrame(self.notebook)
        self.tab_diagram = ttk.Frame(self.notebook, style="TFrame")
        self.tab_operation = ScrollableFrame(self.notebook)
        self.tab_error = ScrollableFrame(self.notebook)
        self.tab_result = ttk.Frame(self.notebook, style="TFrame")
        self.tab_log = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.tab_structure, text="  ①  结构参数  ")
        self.notebook.add(self.tab_diagram, text="  ◎  结构示意图  ")
        self.notebook.add(self.tab_operation, text="  ②  工况 / 线圈 / 材料  ")
        self.notebook.add(self.tab_error, text="  ③  误差 / 校正 / 计算  ")
        self.notebook.add(self.tab_result, text="  ▤  计算结果  ")
        self.notebook.add(self.tab_log, text="  ☰  日志  ")

        self._build_structure_tab(self.tab_structure.body)
        self._build_diagram_tab(self.tab_diagram)
        self._build_operation_tab(self.tab_operation.body)
        self._build_error_tab(self.tab_error.body)
        self._build_result_tab(self.tab_result)
        self._build_log_tab(self.tab_log)

    def _info_banner(self, parent, text):
        """信息提示条：左侧强调色条 + 说明文字。"""
        wrap = tk.Frame(parent, bg=Theme.BG_PANEL)
        wrap.pack(fill="x", padx=14, pady=(14, 6))
        tk.Frame(wrap, bg=Theme.ACCENT, width=4).pack(side="left", fill="y")
        tk.Label(wrap, text=text, bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 10), justify="left",
                 wraplength=1140, anchor="w").pack(side="left", fill="x",
                                                   expand=True, padx=14, pady=12)

    def _add_param_grid(self, parent, title, defs, var_store):
        frame = ttk.LabelFrame(parent, text="  " + title + "  ",
                               style="Card.TLabelframe", padding=14)
        frame.pack(fill="x", padx=14, pady=10)

        header = ["参数", "数值", "单位", "说明"]
        for c, h in enumerate(header):
            cell = tk.Label(frame, text=h, bg=Theme.BG_PANEL_ALT, fg=Theme.FG,
                            font=(Theme.FONT_FAMILY, 10, "bold"),
                            anchor="w", padx=10, pady=7)
            cell.grid(row=0, column=c, sticky="ew", padx=(0, 1), pady=(0, 6))

        for r, item in enumerate(defs, start=1):
            key, label, default, unit, desc = item
            row_bg = Theme.BG_PANEL if r % 2 else Theme.BG_PANEL_ALT

            l1 = tk.Label(frame, text=label, bg=row_bg, fg=Theme.FG,
                          font=(Theme.FONT_FAMILY, 10), anchor="w",
                          padx=10, pady=6)
            l1.grid(row=r, column=0, sticky="ew", padx=(0, 1))

            cell2 = tk.Frame(frame, bg=row_bg)
            cell2.grid(row=r, column=1, sticky="ew", padx=(0, 1))
            v = tk.StringVar(value=str(default))
            entry = tk.Entry(cell2, textvariable=v, width=14,
                             bg=Theme.BG_INPUT, fg=Theme.FG,
                             insertbackground=Theme.FG,
                             relief="flat", highlightthickness=1,
                             highlightbackground=Theme.BORDER,
                             highlightcolor=Theme.ACCENT,
                             font=(Theme.FONT_FAMILY, 10))
            entry.pack(padx=10, pady=6, anchor="w", ipady=2)

            l3 = tk.Label(frame, text=unit, bg=row_bg, fg=Theme.FG_MUTED,
                          font=(Theme.FONT_FAMILY, 10), anchor="w",
                          padx=10, pady=6)
            l3.grid(row=r, column=2, sticky="ew", padx=(0, 1))

            l4 = tk.Label(frame, text=desc, bg=row_bg, fg=Theme.FG_MUTED,
                          font=(Theme.FONT_FAMILY, 9), anchor="w",
                          wraplength=720, justify="left", padx=10, pady=6)
            l4.grid(row=r, column=3, sticky="ew")

            var_store[key] = v

        frame.columnconfigure(0, weight=0, minsize=170)
        frame.columnconfigure(1, weight=0)
        frame.columnconfigure(2, weight=0, minsize=70)
        frame.columnconfigure(3, weight=1)
        return frame

    def _button_bar(self, parent):
        bar = tk.Frame(parent, bg=Theme.BG)
        bar.pack(fill="x", padx=14, pady=(6, 10))
        return bar

    def _build_structure_tab(self, parent):
        note = (
            "本页用于确认机械 / PCB 结构。增强示意图会显示：定子 PCB、转子 PCB、轴孔、"
            "fine / coarse / excitation 线圈的径向分布，以及 rotor-stator 气隙、PCB 厚度、"
            "电子器件高度、壳体纵向长度。"
        )
        self._info_banner(parent, note)

        structure_defs = [
            ("sensor_od_mm", "传感器有效外径", 38.0, "mm", "参考设计约 37.5–38 mm"),
            ("rotor_od_mm", "转子 PCB 外径", 38.0, "mm", "转子被动导体图形所在 PCB 外径"),
            ("stator_od_mm", "定子 PCB 外径", 40.0, "mm", "定子 PCB 可略大于传感器有效区域"),
            ("shaft_hole_d_mm", "中心轴孔直径", 8.0, "mm", "评估夹具常见 8 mm 轴孔"),
            ("rotor_pcb_thk_mm", "转子 PCB 厚度", 0.80, "mm", "轴向叠层长度的一部分"),
            ("stator_pcb_thk_mm", "定子 PCB 厚度", 1.20, "mm", "轴向叠层长度的一部分"),
            ("airgap_mm", "转子-定子气隙", 0.30, "mm", "建议检查 0.2–0.5 mm 工作范围"),
            ("electronics_height_mm", "定子背面器件高度", 2.20, "mm", "NCS32100、接口、电容等元件高度包络"),
            ("bottom_clearance_mm", "底部装配余量", 0.60, "mm", "电子器件到壳体底部安全间隙"),
            ("top_clearance_mm", "顶部装配余量", 0.60, "mm", "转子 PCB 到壳体顶部安全间隙"),
            ("housing_inner_height_mm", "壳体内部纵向长度", 6.00, "mm", "应大于 PCB+气隙+器件+装配余量总长"),
            ("coarse_inner_r_mm", "Coarse 内半径", 5.0, "mm", "内圈 coarse 区域起始半径"),
            ("coarse_outer_r_mm", "Coarse 外半径", 10.0, "mm", "内圈 coarse 区域结束半径"),
            ("exc_inner_r_mm", "Excitation 内半径", 11.0, "mm", "激励线圈位于 coarse 与 fine 之间"),
            ("exc_outer_r_mm", "Excitation 外半径", 14.0, "mm", "激励线圈外半径"),
            ("fine_inner_r_mm", "Fine 内半径", 15.0, "mm", "外圈 fine 区域起始半径"),
            ("fine_outer_r_mm", "Fine 外半径", 18.2, "mm", "外圈 fine 区域结束半径，应留边距"),
            ("min_radial_gap_mm", "最小径向间距", 0.35, "mm", "不同功能线圈带之间的最小安全间隔"),
            ("edge_clearance_mm", "PCB 边缘安全距", 0.50, "mm", "最外线圈到 PCB 边缘的距离"),
            ("conductive_keepout_mm", "导电材料避让", 5.0, "mm", "传感区周边导电件 keepout"),
            ("conductive_shell_inner_d_mm", "导电壳体内径", 48.0, "mm", "小于 传感器外径 + 2×keepout 时报警"),
            ("eccentricity_mm", "装配偏心", 0.05, "mm", "推荐目标不超过 ±0.25 mm"),
            ("tilt_mrad", "转子倾斜", 0.50, "mrad", "倾斜和偏心组合会带来低频角度误差"),
        ]
        self._add_param_grid(parent, "结构与纵向长度参数", structure_defs, self.structure_vars)

        buttons = self._button_bar(parent)
        ttk.Button(buttons, text="规范检查", style="Ghost.TButton",
                   command=self.check_structure).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="生成结构示意图", style="Accent.TButton",
                   command=self.show_structure_diagram).pack(side="left", padx=8)
        ttk.Button(buttons, text="确认结构参数", style="Success.TButton",
                   command=self.confirm_structure).pack(side="left", padx=8)
        ttk.Button(buttons, text="恢复结构默认值", style="Ghost.TButton",
                   command=self.reset_structure_defaults).pack(side="left", padx=8)

        # 状态徽章
        status_wrap = tk.Frame(parent, bg=Theme.BG)
        status_wrap.pack(fill="x", padx=18, pady=(2, 16))
        self.status_dot = tk.Label(status_wrap, text="●", bg=Theme.BG,
                                   fg=Theme.WARNING,
                                   font=(Theme.FONT_FAMILY, 11))
        self.status_dot.pack(side="left")
        self.structure_status = tk.StringVar(value="结构尚未确认。")
        tk.Label(status_wrap, textvariable=self.structure_status,
                 bg=Theme.BG, fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 10)).pack(side="left", padx=8)

    def _build_operation_tab(self, parent):
        note = (
            "本页设置激励、材料、线圈周期和信号模型。若用户不输入，程序使用默认值进行快速预测。"
        )
        self._info_banner(parent, note)

        option_frame = ttk.LabelFrame(parent, text="  模型选项  ",
                                      style="Card.TLabelframe", padding=14)
        option_frame.pack(fill="x", padx=14, pady=10)

        self.operation_vars["coil_mode"] = tk.StringVar(value=COIL_MODES[0])
        self.operation_vars["rx_model"] = tk.StringVar(value=RX_MODELS[0])
        self.operation_vars["drive_model"] = tk.StringVar(value=DRIVE_MODELS[0])
        self.operation_vars["material"] = tk.StringVar(value="铜 / Copper")

        options = [
            ("线圈种类", "coil_mode", COIL_MODES),
            ("接收线圈模型", "rx_model", RX_MODELS),
            ("激励输入模型", "drive_model", DRIVE_MODELS),
            ("目标 / 转子材料", "material", list(MATERIALS.keys())),
        ]
        for r, (label, key, values) in enumerate(options):
            tk.Label(option_frame, text=label, bg=Theme.BG_PANEL, fg=Theme.FG,
                     font=(Theme.FONT_FAMILY, 10),
                     anchor="w").grid(row=r, column=0, sticky="w", padx=6, pady=7)
            cb = ttk.Combobox(option_frame, textvariable=self.operation_vars[key],
                              values=values, state="readonly", width=34,
                              style="TCombobox")
            cb.grid(row=r, column=1, sticky="w", padx=10, pady=7)
        option_frame.columnconfigure(2, weight=1)

        op_defs = [
            ("fine_cycles", "Fine 周期数", 64, "-", "可尝试 8/16/32/64/128/256；默认参考设计 64"),
            ("coarse_cycles", "Coarse 周期数", 5, "-", "默认参考设计 5；也可设为 3 做对比"),
            ("samples", "角度采样点数", 2048, "点", "用于一圈 0–360° 波形和误差计算"),
            ("excitation_freq_mhz", "激励频率", 4.0, "MHz", "NCS32100 方案常用 MHz 级激励"),
            ("tx_current_ma", "Tx 电流幅值", 20.0, "mA", "固定 Tx 电流模型下直接使用"),
            ("tx_voltage_v", "Tx 驱动电压", 3.3, "V", "LC 电压驱动/方波模型使用"),
            ("rx_nominal_mv", "接收基波标称幅值", 120.0, "mV", "解调前后等效包络，用于快速预测"),
            ("copper_thickness_um", "PCB 铜厚", 35.0, "µm", "用于 AC 电阻和趋肤深度估算"),
            ("trace_width_mm", "等效走线宽度", 0.15, "mm", "用于粗略 AC 电阻估算"),
            ("tx_turns", "Tx 等效匝数", 5, "turn", "激励线圈等效匝数"),
            ("rx_turns", "Rx 等效匝数", 1, "turn", "接收线圈等效匝数，仅作为幅值趋势因子"),
            ("target_thickness_um", "转子导体厚度", 35.0, "µm", "用于有限厚度/趋肤深度趋势估计"),
            ("coupling_k", "等效耦合系数", 0.020, "-", "快速模型中的互感/耦合趋势参数"),
        ]
        self._add_param_grid(parent, "工况与电磁参数", op_defs, self.operation_vars)

    def _build_error_tab(self, parent):
        note = (
            "本页用于误差注入、校正开关和计算输出。新增评价项：角度预测平均误差 MAE。"
        )
        self._info_banner(parent, note)

        err_defs = [
            ("gain_imbalance_pct", "三相增益不平衡", 0.30, "%", "A/B/C 相幅值不一致"),
            ("phase_error_deg", "三相相位误差", 0.08, "deg", "B/C 相相位偏差"),
            ("offset_mv", "残余偏置", 0.50, "mV", "Clarke 后仍可能形成角度偏置"),
            ("direct_coupling_mv", "Tx-Rx 直接耦合", 1.00, "mV", "近场直接耦合/寄生耦合项"),
            ("noise_rms_uv", "接收噪声 RMS", 80.0, "µV", "各相独立高斯噪声"),
            ("harmonic2_pct", "二次空间谐波", 0.15, "%", "结构非对称/偶次残留"),
            ("harmonic3_pct", "三次空间谐波", 0.10, "%", "三相差分通常可抑制一部分"),
            ("harmonic5_pct", "五次空间谐波", 0.25, "%", "转子图形误差常关注项"),
            ("harmonic7_pct", "七次空间谐波", 0.08, "%", "高阶残余项"),
            ("ecc_sensitivity_pct", "偏心幅值调制灵敏度", 0.70, "%/0.25mm", "偏心导致的 1/rev 幅值调制"),
            ("tilt_sensitivity_pct", "倾斜幅值调制灵敏度", 0.35, "%/mrad", "倾斜导致的低阶调制"),
            ("lut_harmonics", "傅里叶校正阶数", 12, "阶", "用于仿真中的参考校正，样机需外部基准"),
        ]
        self._add_param_grid(parent, "误差注入与校正参数", err_defs, self.error_vars)

        sw_frame = ttk.LabelFrame(parent, text="  计算开关  ",
                                  style="Card.TLabelframe", padding=14)
        sw_frame.pack(fill="x", padx=14, pady=10)
        self.error_vars["enable_lut"] = tk.BooleanVar(value=True)
        self.error_vars["random_seed"] = tk.StringVar(value="1")
        ttk.Checkbutton(sw_frame, text="启用傅里叶误差 LUT 校正预测",
                        variable=self.error_vars["enable_lut"],
                        style="TCheckbutton").grid(row=0, column=0, sticky="w",
                                                   padx=6, pady=6)
        tk.Label(sw_frame, text="随机噪声种子", bg=Theme.BG_PANEL, fg=Theme.FG,
                 font=(Theme.FONT_FAMILY, 10)).grid(row=0, column=1, sticky="w",
                                                    padx=18, pady=6)
        seed_entry = tk.Entry(sw_frame, textvariable=self.error_vars["random_seed"],
                              width=10, bg=Theme.BG_INPUT, fg=Theme.FG,
                              insertbackground=Theme.FG, relief="flat",
                              highlightthickness=1, highlightbackground=Theme.BORDER,
                              highlightcolor=Theme.ACCENT,
                              font=(Theme.FONT_FAMILY, 10))
        seed_entry.grid(row=0, column=2, sticky="w", padx=6, pady=6, ipady=2)

        btns = self._button_bar(parent)
        ttk.Button(btns, text="确认结构后开始计算", style="Accent.TButton",
                   command=self.run_calculation).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="导出最近结果 CSV", style="Ghost.TButton",
                   command=self.export_csv).pack(side="left", padx=8)

    def _build_log_tab(self, parent):
        wrap = tk.Frame(parent, bg=Theme.BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(wrap, text="运行日志", bg=Theme.BG, fg=Theme.ACCENT,
                 font=(Theme.FONT_FAMILY, 11, "bold")).pack(anchor="w", pady=(0, 8))

        text_frame = tk.Frame(wrap, bg=Theme.BORDER, bd=0)
        text_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(text_frame, wrap="word",
                                font=(Theme.FONT_MONO, 10),
                                bg=Theme.BG_PANEL, fg=Theme.FG,
                                insertbackground=Theme.FG,
                                relief="flat", padx=14, pady=12,
                                selectbackground=Theme.ACCENT)
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)
        self.log("程序已启动。请先检查结构参数，生成增强示意图，并确认结构后再计算。")

    # ------------------------------------------------------------------
    # 参数读取/日志/默认
    # ------------------------------------------------------------------
    def log(self, msg):
        if not hasattr(self, "log_text"):
            return
        self.log_text.insert("end", "›  " + msg + "\n")
        self.log_text.see("end")

    def _set_status(self, text, level="muted"):
        """level: ok / warn / err / muted"""
        color_map = {
            "ok": Theme.SUCCESS,
            "warn": Theme.WARNING,
            "err": Theme.DANGER,
            "muted": Theme.FG_MUTED,
        }
        dot_color = color_map.get(level, Theme.FG_MUTED)
        self.structure_status.set(text)
        if hasattr(self, "status_dot"):
            self.status_dot.config(fg=dot_color)

    def _get_float(self, var_dict, key):
        try:
            return float(var_dict[key].get())
        except Exception as e:
            raise ValueError(f"参数 {key} 不是合法数字：{var_dict[key].get()}") from e

    def _get_int(self, var_dict, key):
        try:
            return int(float(var_dict[key].get()))
        except Exception as e:
            raise ValueError(f"参数 {key} 不是合法整数：{var_dict[key].get()}") from e

    def get_structure_params(self):
        return {k: self._get_float(self.structure_vars, k) for k in self.structure_vars.keys()}

    def get_operation_params(self):
        p = {}
        for k, v in self.operation_vars.items():
            if k in ("coil_mode", "rx_model", "drive_model", "material"):
                p[k] = v.get()
            else:
                if k in ("fine_cycles", "coarse_cycles", "samples", "tx_turns", "rx_turns"):
                    p[k] = self._get_int(self.operation_vars, k)
                else:
                    p[k] = self._get_float(self.operation_vars, k)
        return p

    def get_error_params(self):
        p = {}
        for k, v in self.error_vars.items():
            if k == "enable_lut":
                p[k] = bool(v.get())
            elif k == "random_seed":
                p[k] = self._get_int(self.error_vars, k)
            elif k == "lut_harmonics":
                p[k] = self._get_int(self.error_vars, k)
            else:
                p[k] = self._get_float(self.error_vars, k)
        return p

    def reset_structure_defaults(self):
        defaults = {
            "sensor_od_mm": 38.0, "rotor_od_mm": 38.0, "stator_od_mm": 40.0, "shaft_hole_d_mm": 8.0,
            "rotor_pcb_thk_mm": 0.80, "stator_pcb_thk_mm": 1.20, "airgap_mm": 0.30,
            "electronics_height_mm": 2.20, "bottom_clearance_mm": 0.60, "top_clearance_mm": 0.60,
            "housing_inner_height_mm": 6.00, "coarse_inner_r_mm": 5.0, "coarse_outer_r_mm": 10.0,
            "exc_inner_r_mm": 11.0, "exc_outer_r_mm": 14.0, "fine_inner_r_mm": 15.0, "fine_outer_r_mm": 18.2,
            "min_radial_gap_mm": 0.35, "edge_clearance_mm": 0.50, "conductive_keepout_mm": 5.0,
            "conductive_shell_inner_d_mm": 48.0, "eccentricity_mm": 0.05, "tilt_mrad": 0.50,
        }
        for k, v in defaults.items():
            if k in self.structure_vars:
                self.structure_vars[k].set(str(v))
        self.structure_confirmed = False
        self._set_status("已恢复默认值，结构尚未确认。", "warn")
        self.log("结构参数已恢复默认值。")

    # ------------------------------------------------------------------
    # 结构规范检查
    # ------------------------------------------------------------------
    def validate_structure(self, p):
        errors = []
        warnings = []
        derived = {}

        sensor_r = p["sensor_od_mm"] / 2.0
        rotor_r = p["rotor_od_mm"] / 2.0
        stator_r = p["stator_od_mm"] / 2.0
        hole_r = p["shaft_hole_d_mm"] / 2.0
        min_r = min(sensor_r, rotor_r, stator_r)
        gap = p["min_radial_gap_mm"]
        edge = p["edge_clearance_mm"]

        order = [
            ("轴孔半径", hole_r),
            ("Coarse 内半径", p["coarse_inner_r_mm"]),
            ("Coarse 外半径", p["coarse_outer_r_mm"]),
            ("Excitation 内半径", p["exc_inner_r_mm"]),
            ("Excitation 外半径", p["exc_outer_r_mm"]),
            ("Fine 内半径", p["fine_inner_r_mm"]),
            ("Fine 外半径", p["fine_outer_r_mm"]),
            ("有效边界半径", min_r - edge),
        ]

        for i in range(1, len(order)):
            prev_name, prev_val = order[i - 1]
            name, val = order[i]
            if i == 1:
                required = prev_val + gap
            elif name == "有效边界半径":
                required = prev_val + edge * 0.0
            else:
                required = prev_val + gap
            if val <= required:
                errors.append(f"{name}={val:.3f} mm 与 {prev_name}={prev_val:.3f} mm 距离不足，建议至少保留 {gap:.3f} mm。")

        if p["sensor_od_mm"] <= p["shaft_hole_d_mm"] + 2.0:
            errors.append("传感器有效外径过小，无法容纳中心轴孔和线圈区域。")
        if p["rotor_od_mm"] < p["sensor_od_mm"]:
            warnings.append("转子 PCB 外径小于传感器有效外径，可能裁切转子 fine/coarse 图形。")
        if p["stator_od_mm"] < p["sensor_od_mm"]:
            warnings.append("定子 PCB 外径小于传感器有效外径，可能裁切接收/激励线圈。")

        if not (0.2 <= p["airgap_mm"] <= 0.5):
            warnings.append(f"气隙 {p['airgap_mm']:.3f} mm 超出 0.2–0.5 mm 参考工作/容差范围，需要重新评估耦合和校准。")
        if abs(p["eccentricity_mm"]) > 0.25:
            warnings.append(f"偏心 {p['eccentricity_mm']:.3f} mm 超过 ±0.25 mm 参考目标，角度误差可能明显上升。")
        if abs(p["tilt_mrad"]) > 2.0:
            warnings.append("转子倾斜较大。倾斜与偏心同时存在时，容易形成 1/rev 或低阶角度误差。")

        keepout_required_d = p["sensor_od_mm"] + 2.0 * p["conductive_keepout_mm"]
        if p["conductive_shell_inner_d_mm"] < keepout_required_d:
            errors.append(
                f"导电壳体内径 {p['conductive_shell_inner_d_mm']:.2f} mm 小于 keepout 要求 "
                f"{keepout_required_d:.2f} mm，存在导电材料侵入传感区风险。"
            )

        total_stack = (
            p["bottom_clearance_mm"] + p["electronics_height_mm"] + p["stator_pcb_thk_mm"]
            + p["airgap_mm"] + p["rotor_pcb_thk_mm"] + p["top_clearance_mm"]
        )
        derived["total_stack_mm"] = total_stack
        if total_stack > p["housing_inner_height_mm"]:
            errors.append(
                f"轴向叠层总长 {total_stack:.2f} mm 超过壳体内部纵向长度 "
                f"{p['housing_inner_height_mm']:.2f} mm，存在轴向结构冲突。"
            )
        else:
            margin = p["housing_inner_height_mm"] - total_stack
            if margin < 0.3:
                warnings.append(f"壳体轴向余量仅 {margin:.2f} mm，装配和公差空间偏小。")

        derived["sensor_r_mm"] = sensor_r
        derived["rotor_r_mm"] = rotor_r
        derived["stator_r_mm"] = stator_r
        derived["hole_r_mm"] = hole_r
        derived["keepout_required_d_mm"] = keepout_required_d

        return errors, warnings, derived

    def check_structure(self):
        try:
            p = self.get_structure_params()
            errors, warnings, derived = self.validate_structure(p)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        msg_lines = []
        if errors:
            msg_lines.append("【严重冲突】")
            msg_lines.extend(f"- {x}" for x in errors)
        if warnings:
            msg_lines.append("\n【警告】")
            msg_lines.extend(f"- {x}" for x in warnings)
        if not errors and not warnings:
            msg_lines.append("结构检查通过，未发现严重冲突或警告。")
        msg_lines.append(f"\n轴向叠层总长：{derived['total_stack_mm']:.3f} mm")
        msg_lines.append(f"导电材料 keepout 要求内径：≥ {derived['keepout_required_d_mm']:.3f} mm")

        text = "\n".join(msg_lines)
        if errors:
            messagebox.showerror("结构检查结果", text)
            self._set_status("结构检查存在严重冲突，不能确认。", "err")
        elif warnings:
            messagebox.showwarning("结构检查结果", text)
            self._set_status("结构检查存在警告，可人工确认后继续。", "warn")
        else:
            messagebox.showinfo("结构检查结果", text)
            self._set_status("结构检查通过，可确认。", "ok")
        self.log(text)

    def confirm_structure(self):
        try:
            p = self.get_structure_params()
            errors, warnings, derived = self.validate_structure(p)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        if errors:
            messagebox.showerror("无法确认结构", "仍存在严重结构冲突：\n\n" + "\n".join(errors))
            self.structure_confirmed = False
            self._set_status("结构存在严重冲突，确认失败。", "err")
            return

        text = f"轴向叠层总长 {derived['total_stack_mm']:.3f} mm。\n"
        if warnings:
            text += "存在以下警告，确认继续吗？\n\n" + "\n".join("- " + w for w in warnings)
        else:
            text += "未发现冲突，是否确认结构参数？"
        if messagebox.askyesno("确认结构参数", text):
            self.structure_confirmed = True
            self._set_status("结构参数已确认，可以进入计算流程。", "ok")
            self.log("结构参数已由用户确认。")
        else:
            self.structure_confirmed = False
            self._set_status("结构尚未确认。", "warn")

    # ------------------------------------------------------------------
    # 结构示意图（内嵌选项卡，带三视图视角选项）
    # ------------------------------------------------------------------
    def _build_diagram_tab(self, parent):
        """构建结构示意图选项卡的静态 UI：左侧视角选项 + 右侧画布占位。"""
        self.diagram_view = tk.StringVar(value="iso")

        # 顶部信息条
        banner = tk.Frame(parent, bg=Theme.BG_PANEL)
        banner.pack(fill="x", padx=14, pady=(14, 6))
        tk.Frame(banner, bg=Theme.ACCENT, width=4).pack(side="left", fill="y")
        tk.Label(banner,
                 text="结构示意图展示定子 / 转子 PCB、轴孔、fine / coarse / excitation "
                      "线圈径向分布与纵向叠层长度。在左侧切换三视图视角后会自动重绘。",
                 bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 10), justify="left",
                 wraplength=1120, anchor="w").pack(side="left", fill="x",
                                                   expand=True, padx=14, pady=12)

        body = tk.Frame(parent, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        # ---- 左侧视角控制面板 ----
        side = tk.Frame(body, bg=Theme.BG, width=210)
        side.pack(side="left", fill="y", padx=(0, 12))
        side.pack_propagate(False)

        view_card = tk.Frame(side, bg=Theme.BG_PANEL)
        view_card.pack(fill="x")
        tk.Frame(view_card, bg=Theme.ACCENT, height=3).pack(fill="x")
        vc_inner = tk.Frame(view_card, bg=Theme.BG_PANEL)
        vc_inner.pack(fill="x", padx=14, pady=14)

        tk.Label(vc_inner, text="视角选项", bg=Theme.BG_PANEL, fg=Theme.ACCENT,
                 font=(Theme.FONT_FAMILY, 12, "bold")).pack(anchor="w",
                                                            pady=(0, 10))

        view_options = [
            ("iso",   "立体视图  (等轴测)"),
            ("front", "前视图  (X-Z)"),
            ("side",  "侧视图  (Y-Z)"),
            ("top",   "俯视图  (X-Y)"),
        ]
        for val, label in view_options:
            rb = ttk.Radiobutton(vc_inner, text=label, value=val,
                                 variable=self.diagram_view,
                                 command=self._on_view_change,
                                 style="TRadiobutton")
            rb.pack(anchor="w", pady=4)

        tk.Frame(vc_inner, bg=Theme.BORDER, height=1).pack(fill="x", pady=12)

        ttk.Button(vc_inner, text="刷新示意图", style="Accent.TButton",
                   command=self.show_structure_diagram).pack(fill="x")

        tip_card = tk.Frame(side, bg=Theme.BG_PANEL)
        tip_card.pack(fill="x", pady=(12, 0))
        tk.Label(tip_card,
                 text="提示：修改结构参数后，\n点击「刷新示意图」或\n①结构参数页的\n「生成结构示意图」\n按钮即可更新。",
                 bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 9), justify="left",
                 anchor="w").pack(anchor="w", padx=14, pady=12)

        # ---- 右侧画布区 ----
        self.diagram_canvas_host = tk.Frame(body, bg=Theme.BORDER)
        self.diagram_canvas_host.pack(side="right", fill="both", expand=True)

        self._diagram_canvas = None
        self._diagram_toolbar = None
        self._diagram_rendered = False

        # 初始占位提示
        self._diagram_placeholder = tk.Label(
            self.diagram_canvas_host,
            text="尚未生成结构示意图。\n\n请在「①结构参数」页点击「生成结构示意图」，\n或点击左侧「刷新示意图」。",
            bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
            font=(Theme.FONT_FAMILY, 12), justify="center")
        self._diagram_placeholder.pack(fill="both", expand=True, padx=1, pady=1)

    def _on_view_change(self):
        """切换视角时，若已渲染过则按当前参数自动重绘。"""
        if getattr(self, "_diagram_rendered", False):
            self._render_diagram(jump=False)

    def show_structure_diagram(self):
        """响应按钮：校验参数 → 跳转到示意图选项卡 → 渲染。"""
        try:
            p = self.get_structure_params()
            errors, warnings, derived = self.validate_structure(p)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        if errors:
            if not messagebox.askyesno(
                "存在结构冲突",
                "当前结构存在严重冲突，仍要生成示意图用于排查吗？\n\n" + "\n".join(errors)
            ):
                return

        self._render_diagram(jump=True)

    def _render_diagram(self, jump=True):
        """实际绘制：清空画布宿主，按当前视角重建 figure。"""
        try:
            p = self.get_structure_params()
            errors, warnings, derived = self.validate_structure(p)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        host = self.diagram_canvas_host

        # 清空旧内容（占位标签 / 旧画布 / 旧工具栏）
        if self._diagram_placeholder is not None:
            self._diagram_placeholder.destroy()
            self._diagram_placeholder = None
        if self._diagram_toolbar is not None:
            self._diagram_toolbar.destroy()
            self._diagram_toolbar = None
        if self._diagram_canvas is not None:
            self._diagram_canvas.get_tk_widget().destroy()
            self._diagram_canvas = None

        view = self.diagram_view.get()

        fig = Figure(figsize=(12.5, 7.2), dpi=100, facecolor=Theme.PLOT_BG)
        gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 0.85])
        ax3d = fig.add_subplot(gs[0, 0], projection="3d")
        ax2d = fig.add_subplot(gs[0, 1])

        self._draw_3d_structure(ax3d, p, view=view)
        self._draw_side_structure(ax2d, p, derived)

        fig.suptitle("NCS32100 参数化结构示意：线圈径向分布 + 纵向叠层长度",
                     fontsize=14, color=Theme.PLOT_FG, fontweight="bold")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=host)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=1, pady=1)
        toolbar = NavigationToolbar2Tk(canvas, host)
        toolbar.config(bg=Theme.BG_PANEL)
        toolbar.update()

        self._diagram_canvas = canvas
        self._diagram_toolbar = toolbar
        self._diagram_rendered = True

        if jump:
            self.notebook.select(self.tab_diagram)
        self.log(f"已生成结构示意图（视角：{view}）。")

    def _draw_ring_wave_3d(self, ax, r_center, width, cycles, z, phase, label, color, lw=1.2, linestyle="-", max_points=2400):
        theta = np.linspace(0, 2.0 * np.pi, max_points)
        amp = width * 0.35
        r = r_center + amp * np.sin(cycles * theta + phase)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        ax.plot(x, y, np.full_like(x, z), color=color, linewidth=lw, linestyle=linestyle, label=label)

    def _draw_circle_3d(self, ax, radius, z, color, lw=1.0, linestyle="-", label=None):
        theta = np.linspace(0, 2.0 * np.pi, 500)
        ax.plot(radius * np.cos(theta), radius * np.sin(theta), np.full_like(theta, z),
                color=color, linewidth=lw, linestyle=linestyle, label=label)

    def _draw_3d_structure(self, ax, p, view="iso"):
        ax.set_facecolor(Theme.PLOT_AXES_BG)
        try:
            ax.xaxis.set_pane_color((0.97, 0.98, 0.99, 0.85))
            ax.yaxis.set_pane_color((0.97, 0.98, 0.99, 0.85))
            ax.zaxis.set_pane_color((0.97, 0.98, 0.99, 0.85))
            ax.xaxis.line.set_color(Theme.BORDER)
            ax.yaxis.line.set_color(Theme.BORDER)
            ax.zaxis.line.set_color(Theme.BORDER)
        except Exception:
            pass

        stator_top = 0.0
        stator_bottom = -p["stator_pcb_thk_mm"]
        rotor_bottom = p["airgap_mm"]
        rotor_top = p["airgap_mm"] + p["rotor_pcb_thk_mm"]
        electronics_bottom = stator_bottom - p["electronics_height_mm"]

        max_r = max(p["stator_od_mm"], p["rotor_od_mm"], p["conductive_shell_inner_d_mm"]) / 2.0

        theta = np.linspace(0, 2.0 * np.pi, 96)
        rr = np.linspace(p["shaft_hole_d_mm"] / 2.0, p["stator_od_mm"] / 2.0, 24)
        T, R = np.meshgrid(theta, rr)
        X = R * np.cos(T)
        Y = R * np.sin(T)
        ax.plot_surface(X, Y, np.full_like(X, stator_top), alpha=0.32, color="#2F6BFF", linewidth=0)
        ax.plot_surface(X, Y, np.full_like(X, stator_bottom), alpha=0.20, color="#2F6BFF", linewidth=0)

        rr2 = np.linspace(p["shaft_hole_d_mm"] / 2.0, p["rotor_od_mm"] / 2.0, 24)
        T2, R2 = np.meshgrid(theta, rr2)
        X2 = R2 * np.cos(T2)
        Y2 = R2 * np.sin(T2)
        ax.plot_surface(X2, Y2, np.full_like(X2, rotor_bottom), alpha=0.32, color="#E08A00", linewidth=0)
        ax.plot_surface(X2, Y2, np.full_like(X2, rotor_top), alpha=0.20, color="#E08A00", linewidth=0)

        shaft_r = p["shaft_hole_d_mm"] / 2.0 * 0.86
        z_vals = np.linspace(electronics_bottom - p["bottom_clearance_mm"], rotor_top + p["top_clearance_mm"], 30)
        Tshaft, Zshaft = np.meshgrid(theta, z_vals)
        Xshaft = shaft_r * np.cos(Tshaft)
        Yshaft = shaft_r * np.sin(Tshaft)
        ax.plot_surface(Xshaft, Yshaft, Zshaft, alpha=0.40, color="#8A93A8", linewidth=0)

        coarse_c = 0.5 * (p["coarse_inner_r_mm"] + p["coarse_outer_r_mm"])
        coarse_w = p["coarse_outer_r_mm"] - p["coarse_inner_r_mm"]
        fine_c = 0.5 * (p["fine_inner_r_mm"] + p["fine_outer_r_mm"])
        fine_w = p["fine_outer_r_mm"] - p["fine_inner_r_mm"]

        colors = ["#2ECC71", "#F5A623", "#A78BFA"]
        phases = [0.0, -2.0 * np.pi / 3.0, 2.0 * np.pi / 3.0]

        for i, ph in enumerate(phases):
            self._draw_ring_wave_3d(ax, coarse_c, coarse_w, 5, stator_top + 0.04 + 0.015*i, ph,
                                    f"定子 Coarse Rx 相{i+1}", colors[i], lw=1.1)
        for i, ph in enumerate(phases):
            self._draw_ring_wave_3d(ax, fine_c, fine_w, 64, stator_top + 0.12 + 0.015*i, ph,
                                    f"定子 Fine Rx 相{i+1}", colors[i], lw=0.85)

        exc_radii = np.linspace(p["exc_inner_r_mm"], p["exc_outer_r_mm"], 6)
        for j, r in enumerate(exc_radii):
            self._draw_circle_3d(ax, r, stator_top + 0.24 + 0.01*j, color="#FF5C5C", lw=1.2,
                                 label="Excitation Tx" if j == 0 else None)

        self._draw_ring_wave_3d(ax, coarse_c, coarse_w * 0.85, 5, rotor_bottom - 0.02, 0.35,
                                "转子 Coarse 被动图形", "#4A5878", lw=1.2, linestyle="--")
        self._draw_ring_wave_3d(ax, fine_c, fine_w * 0.85, 64, rotor_bottom - 0.04, 0.50,
                                "转子 Fine 被动图形", "#4A5878", lw=0.9, linestyle="--")

        keepout_r = p["sensor_od_mm"] / 2.0 + p["conductive_keepout_mm"]
        self._draw_circle_3d(ax, keepout_r, stator_top + 0.35, "#FF5C5C", lw=1.5, linestyle=":", label="导电材料 keepout")
        self._draw_circle_3d(ax, p["conductive_shell_inner_d_mm"] / 2.0, stator_top + 0.45, "#65718C", lw=1.2, linestyle="-.", label="导电壳体内径")

        ax.text(0, -max_r * 0.92, rotor_top, f"Rotor PCB\n厚 {p['rotor_pcb_thk_mm']:.2f} mm",
                fontsize=9, color=Theme.PLOT_FG)
        ax.text(0, -max_r * 0.92, stator_top, f"Airgap {p['airgap_mm']:.2f} mm",
                fontsize=9, color=Theme.PLOT_FG)
        ax.text(0, -max_r * 0.92, stator_bottom, f"Stator PCB\n厚 {p['stator_pcb_thk_mm']:.2f} mm",
                fontsize=9, color=Theme.PLOT_FG)

        view_map = {
            "iso":   (28, -58, "立体视图（等轴测）"),
            "front": (0,  -90, "前视图（X-Z 面）"),
            "side":  (0,    0, "侧视图（Y-Z 面）"),
            "top":   (89, -90, "俯视图（X-Y 面）"),
        }
        elev, azim, view_title = view_map.get(view, view_map["iso"])

        ax.set_xlabel("X / mm", color=Theme.FG_MUTED)
        ax.set_ylabel("Y / mm", color=Theme.FG_MUTED)
        ax.set_zlabel("Z / mm", color=Theme.FG_MUTED)
        ax.set_title(view_title, color=Theme.PLOT_FG, fontweight="bold")
        ax.tick_params(colors=Theme.FG_MUTED, labelsize=7)
        ax.set_xlim(-max_r, max_r)
        ax.set_ylim(-max_r, max_r)
        zmin = electronics_bottom - p["bottom_clearance_mm"] - 0.2
        zmax = rotor_top + p["top_clearance_mm"] + 0.3
        ax.set_zlim(zmin, zmax)
        try:
            if view == "top":
                ax.set_box_aspect((1, 1, 0.55))
            else:
                ax.set_box_aspect((1, 1, 0.28))
        except Exception:
            pass
        ax.view_init(elev=elev, azim=azim)
        leg = ax.legend(loc="upper left", fontsize=8, facecolor=Theme.BG_PANEL,
                        edgecolor=Theme.BORDER, labelcolor=Theme.FG)
        if leg:
            leg.get_frame().set_alpha(0.9)

    def _draw_side_structure(self, ax, p, derived):
        style_axis(ax)
        ax.set_title("纵向剖面长度与径向线圈带", color=Theme.PLOT_FG, fontweight="bold")
        rmax = max(p["conductive_shell_inner_d_mm"] / 2.0, p["stator_od_mm"] / 2.0) + 2.0

        z_elec_bottom = p["bottom_clearance_mm"]
        z_stator_bottom = z_elec_bottom + p["electronics_height_mm"]
        z_stator_top = z_stator_bottom + p["stator_pcb_thk_mm"]
        z_rotor_bottom = z_stator_top + p["airgap_mm"]
        z_rotor_top = z_rotor_bottom + p["rotor_pcb_thk_mm"]
        z_housing_top = p["housing_inner_height_mm"]

        # 为右侧引线注释预留绘图空间：x 轴正方向扩展
        label_x = rmax + 0.5            # 引线文字所在列
        anchor_x = rmax * 0.62          # 引线在结构上的起点（右半结构内侧）
        x_right_limit = rmax + 9.5      # 画布右边界

        ax.add_patch(Rectangle((-p["conductive_shell_inner_d_mm"]/2, 0),
                               p["conductive_shell_inner_d_mm"], z_housing_top,
                               fill=False, linestyle="--", linewidth=1.3, edgecolor="#65718C"))

        ax.add_patch(Rectangle((-p["stator_od_mm"]/2, z_elec_bottom),
                               p["stator_od_mm"], p["electronics_height_mm"],
                               color="#8A93A8", alpha=0.55, label="背面电子器件高度"))
        ax.add_patch(Rectangle((-p["stator_od_mm"]/2, z_stator_bottom),
                               p["stator_od_mm"], p["stator_pcb_thk_mm"],
                               color="#2F6BFF", alpha=0.45, label="Stator PCB"))
        ax.add_patch(Rectangle((-p["rotor_od_mm"]/2, z_rotor_bottom),
                               p["rotor_od_mm"], p["rotor_pcb_thk_mm"],
                               color="#E08A00", alpha=0.50, label="Rotor PCB"))
        ax.add_patch(Rectangle((-p["shaft_hole_d_mm"]/2*0.86, 0),
                               p["shaft_hole_d_mm"]*0.86, z_housing_top,
                               color="#8A93A8", alpha=0.35, label="中心轴"))

        ax.add_patch(Rectangle((-p["sensor_od_mm"]/2, z_stator_top),
                               p["sensor_od_mm"], p["airgap_mm"],
                               color="#0FB5C9", alpha=0.30, hatch="///",
                               edgecolor="#0FB5C9", label="Airgap"))

        # 线圈带：仅画色条，名称不在带子旁标注（统一走右侧引线，避免重叠）
        coil_bands = [
            ("Coarse Rx / 转子 Coarse", p["coarse_inner_r_mm"], p["coarse_outer_r_mm"], "#22A861"),
            ("Excitation Tx", p["exc_inner_r_mm"], p["exc_outer_r_mm"], "#E0443E"),
            ("Fine Rx / 转子 Fine", p["fine_inner_r_mm"], p["fine_outer_r_mm"], "#7C5CFF"),
        ]
        for name, r1, r2, color in coil_bands:
            for sign in [-1, 1]:
                ax.plot([sign*r1, sign*r2], [z_stator_top + 0.05, z_stator_top + 0.05],
                        color=color, linewidth=5, solid_capstyle="butt")
            for sign in [-1, 1]:
                ax.plot([sign*r1, sign*r2], [z_rotor_bottom - 0.05, z_rotor_bottom - 0.05],
                        color=color, linewidth=2.5, linestyle="--", solid_capstyle="butt")

        keepout_r = p["sensor_od_mm"]/2 + p["conductive_keepout_mm"]
        ax.axvline(keepout_r, color="#E0443E", linestyle=":", linewidth=1.2)
        ax.axvline(-keepout_r, color="#E0443E", linestyle=":", linewidth=1.2)

        # ---- 统一的右侧引线注释 ----
        # 每条注释 = (锚点坐标(x,y), 文字, 颜色)；文字按 y 排序后均匀分布到右侧列，
        # 用细引线连回锚点，彻底避免文字相互重叠。
        annotations = []

        def add_note(ax_pt, text, color):
            annotations.append({"anchor": ax_pt, "text": text, "color": color})

        # 各薄层 / 关键尺寸的锚点取该层中心
        add_note((0.0, z_elec_bottom + p["electronics_height_mm"]/2),
                 f"背面器件高度 {p['electronics_height_mm']:.2f} mm", "#5B6376")
        add_note((anchor_x*0.5, z_stator_bottom + p["stator_pcb_thk_mm"]/2),
                 f"定子 PCB {p['stator_pcb_thk_mm']:.2f} mm", "#2F6BFF")
        add_note((anchor_x*0.5, z_stator_top + p["airgap_mm"]/2),
                 f"气隙 {p['airgap_mm']:.2f} mm", "#0E9DAE")
        add_note((anchor_x*0.5, z_rotor_bottom + p["rotor_pcb_thk_mm"]/2),
                 f"转子 PCB {p['rotor_pcb_thk_mm']:.2f} mm", "#E08A00")
        add_note((0.0, z_housing_top),
                 f"壳体内部纵向长度 {p['housing_inner_height_mm']:.2f} mm", "#5B6376")
        add_note((-keepout_r, z_housing_top*0.5),
                 f"导电材料 keepout  ±{keepout_r:.2f} mm", "#E0443E")
        add_note((0.0, derived["total_stack_mm"]),
                 f"轴向叠层总长 {derived['total_stack_mm']:.2f} mm", "#1F2A44")

        # 线圈带锚点（取定子顶面的带中点）
        for name, r1, r2, color in coil_bands:
            add_note(((r1 + r2) / 2.0, z_stator_top + 0.05), name, color)

        # 按锚点 y 排序，从上到下均匀铺到右侧文字列
        annotations.sort(key=lambda a: a["anchor"][1], reverse=True)
        n_notes = len(annotations)
        y_top = max(z_housing_top, derived["total_stack_mm"]) + 0.3
        y_bot = 0.1
        if n_notes > 1:
            ys = np.linspace(y_top, y_bot, n_notes)
        else:
            ys = [0.5 * (y_top + y_bot)]

        for note, ly in zip(annotations, ys):
            ax0, ay = note["anchor"]
            color = note["color"]
            # 引线：锚点 -> 中转点 -> 文字行起点（折线，浅色细线）
            ax.annotate(
                "", xy=(ax0, ay), xytext=(label_x, ly),
                arrowprops=dict(arrowstyle="-", color=color, alpha=0.55,
                                linewidth=0.9,
                                connectionstyle="arc3,rad=0.0",
                                shrinkA=0, shrinkB=2),
            )
            ax.plot([ax0], [ay], marker="o", markersize=3.0,
                    color=color, alpha=0.8)
            ax.text(label_x + 0.25, ly, note["text"], va="center", ha="left",
                    fontsize=8.5, color=color,
                    fontweight="bold" if "总长" in note["text"] else "normal")

        ax.set_xlabel("径向位置 r / mm", color=Theme.FG_MUTED)
        ax.set_ylabel("轴向长度 z / mm", color=Theme.FG_MUTED)
        ax.set_xlim(-rmax, x_right_limit)
        ax.set_ylim(-0.4, max(z_housing_top, derived["total_stack_mm"]) + 0.9)
        leg = ax.legend(loc="lower left", fontsize=8, facecolor=Theme.BG_PANEL,
                        edgecolor=Theme.BORDER, labelcolor=Theme.FG,
                        framealpha=0.92, ncol=2)
        if leg:
            leg.get_frame().set_alpha(0.92)

    # ------------------------------------------------------------------
    # 计算
    # ------------------------------------------------------------------
    def run_calculation(self):
        if not self.structure_confirmed:
            if not messagebox.askyesno(
                "结构尚未确认",
                "结构参数尚未确认。是否先执行规范检查，并在无严重冲突时继续人工确认？",
            ):
                return
            try:
                p = self.get_structure_params()
                errors, warnings, derived = self.validate_structure(p)
            except ValueError as e:
                messagebox.showerror("参数错误", str(e))
                return
            if errors:
                messagebox.showerror("无法计算", "存在严重结构冲突，不能开始计算：\n\n" + "\n".join(errors))
                return
            text = "结构没有严重冲突。"
            if warnings:
                text += "\n存在警告：\n" + "\n".join("- " + w for w in warnings)
            text += "\n\n是否确认当前结构并开始计算？"
            if not messagebox.askyesno("确认后开始计算", text):
                return
            self.structure_confirmed = True
            self._set_status("结构参数已确认，可以进入计算流程。", "ok")

        try:
            sp = self.get_structure_params()
            op = self.get_operation_params()
            ep = self.get_error_params()
            errors, warnings, derived = self.validate_structure(sp)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        if errors:
            messagebox.showerror("结构冲突", "结构出现严重冲突，计算中止：\n\n" + "\n".join(errors))
            return

        if not messagebox.askyesno("开始计算", "结构参数已确认。是否使用当前工况与误差参数开始解析/半解析计算？"):
            return

        try:
            results = self.simulate(sp, op, ep)
        except Exception as e:
            messagebox.showerror("计算失败", f"计算过程中出现错误：\n{e}")
            raise

        self.latest_results = results
        self._render_results(results, jump=True)
        self.log("计算完成。新增评价项：角度预测平均误差 MAE = "
                 f"{results['metrics']['mae_arcsec']:.3f} arcsec。")

    def simulate(self, sp, op, ep):
        rng = np.random.default_rng(ep["random_seed"])
        n = max(256, int(op["samples"]))
        theta = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        true_deg = np.degrees(theta)

        fine_N = int(op["fine_cycles"])
        coarse_M = int(op["coarse_cycles"])
        if fine_N <= 0 or coarse_M <= 0:
            raise ValueError("Fine/Coarse 周期数必须为正。")
        if op["coil_mode"] == "Fine 三相相对角模式":
            coarse_M = 1
        if op["coil_mode"] == "Fine 两相 sin/cos 简化模式":
            pass

        freq = op["excitation_freq_mhz"] * 1e6
        material = MATERIALS[op["material"]]
        rho = material["rho"]
        mur = material["mur"]

        exc_mid_r = 0.5 * (sp["exc_inner_r_mm"] + sp["exc_outer_r_mm"])
        approx_tx_length_mm = 2.0 * np.pi * exc_mid_r * max(op["tx_turns"], 1)
        tx_R_ac, delta = estimate_ac_resistance(
            freq, rho, mur, op["trace_width_mm"], op["copper_thickness_um"], approx_tx_length_mm
        )
        tx_L = mohan_planar_spiral_L(op["tx_turns"], sp["exc_inner_r_mm"], sp["exc_outer_r_mm"])
        omega = 2.0 * np.pi * freq
        cap_resonant = 1.0 / max(omega**2 * tx_L, 1e-30)

        drive = op["drive_model"]
        if drive == "固定 Tx 电流":
            tx_current_a = op["tx_current_ma"] * 1e-3
        elif drive == "串联 LC 电压驱动":
            tx_current_a = min(op["tx_voltage_v"] / max(tx_R_ac, 1e-3), 2.0)
        elif drive == "方波基波等效":
            tx_current_a = op["tx_current_ma"] * 1e-3 * 4.0 / np.pi
        else:
            tx_current_a = op["tx_current_ma"] * 1e-3

        airgap = max(sp["airgap_mm"], 0.05)
        gap_factor = np.exp(-(airgap - 0.30) / 0.55)
        coupling_factor = op["coupling_k"] * gap_factor * (tx_current_a / max(op["tx_current_ma"] * 1e-3, 1e-9))
        base_mv = op["rx_nominal_mv"] * coupling_factor / max(op["coupling_k"], 1e-9)

        target_t = op["target_thickness_um"] * 1e-6
        sheet_eff = 1.0 - np.exp(-target_t / max(delta, 1e-12))
        base_mv *= np.clip(0.35 + 0.65 * sheet_eff, 0.05, 2.0)

        h2 = ep["harmonic2_pct"] / 100.0
        h3 = ep["harmonic3_pct"] / 100.0
        h5 = ep["harmonic5_pct"] / 100.0
        h7 = ep["harmonic7_pct"] / 100.0
        rx_model = op["rx_model"]
        if rx_model == "Twisted loop 抑制偶次谐波":
            h2 *= 0.30
        elif rx_model == "Dogbone/面积权重近似":
            h5 *= 0.70
            h7 *= 0.85
        elif rx_model == "谐波应力测试":
            h2 *= 2.0
            h3 *= 2.0
            h5 *= 2.0
            h7 *= 2.0

        ecc = sp["eccentricity_mm"]
        tilt = sp["tilt_mrad"]
        ecc_mod = (ep["ecc_sensitivity_pct"] / 100.0) * (ecc / 0.25)
        tilt_mod = (ep["tilt_sensitivity_pct"] / 100.0) * tilt
        amplitude_mod = 1.0 + ecc_mod * np.cos(theta) + tilt_mod * np.cos(theta - np.pi / 5.0)

        gain = ep["gain_imbalance_pct"] / 100.0
        gains = np.array([1.0 - 0.5*gain, 1.0 + gain, 1.0 - 0.5*gain])
        phase_err = np.radians(ep["phase_error_deg"])
        phase_offsets = np.array([0.0, -2.0*np.pi/3.0 + phase_err, 2.0*np.pi/3.0 - phase_err])
        offset = ep["offset_mv"]
        offsets = np.array([offset, -0.55*offset, -0.45*offset])
        direct = ep["direct_coupling_mv"]
        direct_vec = np.array([0.50*direct, -0.25*direct, -0.25*direct])
        noise_rms_mv = ep["noise_rms_uv"] * 1e-3

        def make_3phase(cycles, amplitude_scale=1.0):
            phi = cycles * theta
            sigs = []
            for i in range(3):
                core = np.cos(phi + phase_offsets[i])
                harmonic = (
                    h2 * np.cos(2*phi + phase_offsets[i] + 0.20)
                    + h3 * np.cos(3*phi + phase_offsets[i] - 0.10)
                    + h5 * np.cos(5*phi + phase_offsets[i] + 0.45)
                    + h7 * np.cos(7*phi + phase_offsets[i] - 0.35)
                )
                s = base_mv * amplitude_scale * amplitude_mod * gains[i] * (core + harmonic)
                s += offsets[i] + direct_vec[i]
                s += rng.normal(0.0, noise_rms_mv, size=n)
                sigs.append(s)
            return np.array(sigs)

        fine_sigs = make_3phase(fine_N, amplitude_scale=1.0)
        coarse_sigs = make_3phase(coarse_M, amplitude_scale=0.78)

        if op["coil_mode"] == "Fine 两相 sin/cos 简化模式":
            sin_sig = base_mv * np.sin(fine_N * theta) + rng.normal(0, noise_rms_mv, size=n)
            cos_sig = base_mv * np.cos(fine_N * theta) + rng.normal(0, noise_rms_mv, size=n)
            fine_phi = wrap_2pi(np.arctan2(sin_sig, cos_sig))
            fine_alpha, fine_beta = cos_sig, sin_sig
        else:
            fine_alpha, fine_beta = clarke_3phase(fine_sigs[0], fine_sigs[1], fine_sigs[2])
            fine_phi = wrap_2pi(np.arctan2(fine_beta, fine_alpha))

        coarse_alpha, coarse_beta = clarke_3phase(coarse_sigs[0], coarse_sigs[1], coarse_sigs[2])
        coarse_phi = wrap_2pi(np.arctan2(coarse_beta, coarse_alpha))

        if op["coil_mode"] == "Fine 三相相对角模式" or coarse_M <= 1:
            pred_rad = fine_phi / fine_N
        else:
            ks = np.arange(fine_N)[:, None]
            candidates = (fine_phi[None, :] + 2.0*np.pi*ks) / fine_N
            diff = circular_phase_error(coarse_M * candidates, coarse_phi[None, :])
            best_k = np.argmin(np.abs(diff), axis=0)
            pred_rad = (fine_phi + 2.0*np.pi*best_k) / fine_N
            pred_rad = wrap_2pi(pred_rad)

        pred_deg = np.degrees(pred_rad)
        raw_error_deg = circular_error_deg(pred_deg, true_deg)
        raw_error_arcsec = raw_error_deg * 3600.0

        zero_bias_deg = np.mean(raw_error_deg)
        pred_zero_deg = pred_deg - zero_bias_deg
        zero_error_deg = circular_error_deg(pred_zero_deg, true_deg)

        corrected_error_deg = zero_error_deg.copy()
        lut_pred_deg = pred_zero_deg.copy()
        if ep["enable_lut"]:
            corrected_error_deg, lut_pred_deg = self._fourier_lut_correct(theta, pred_zero_deg, true_deg, int(ep["lut_harmonics"]))

        corrected_error_arcsec = corrected_error_deg * 3600.0

        metrics = self._compute_metrics(raw_error_deg, zero_error_deg, corrected_error_deg)
        spectrum = self._error_spectrum(theta, corrected_error_arcsec, max_harm=24)

        results = {
            "theta_rad": theta,
            "true_deg": true_deg,
            "pred_deg": pred_deg,
            "pred_zero_deg": pred_zero_deg,
            "pred_lut_deg": lut_pred_deg,
            "raw_error_deg": raw_error_deg,
            "zero_error_deg": zero_error_deg,
            "corrected_error_deg": corrected_error_deg,
            "raw_error_arcsec": raw_error_arcsec,
            "zero_error_arcsec": zero_error_deg * 3600.0,
            "corrected_error_arcsec": corrected_error_arcsec,
            "fine_sigs": fine_sigs,
            "coarse_sigs": coarse_sigs,
            "fine_alpha": fine_alpha,
            "fine_beta": fine_beta,
            "coarse_alpha": coarse_alpha,
            "coarse_beta": coarse_beta,
            "fine_phi_deg": np.degrees(fine_phi),
            "coarse_phi_deg": np.degrees(coarse_phi),
            "metrics": metrics,
            "spectrum": spectrum,
            "derived": {
                "tx_L_uH": tx_L * 1e6,
                "tx_R_ac_ohm": tx_R_ac,
                "skin_depth_um": delta * 1e6,
                "cap_resonant_nF": cap_resonant * 1e9,
                "base_rx_mv": base_mv,
                "tx_current_ma_eff": tx_current_a * 1e3,
                "sheet_eff": sheet_eff,
                "zero_bias_deg": zero_bias_deg,
                "fine_cycles": fine_N,
                "coarse_cycles": coarse_M,
            },
            "params": {"structure": sp, "operation": op, "error": ep},
        }
        return results

    def _fourier_lut_correct(self, theta, pred_zero_deg, true_deg, harm_order):
        err_deg = circular_error_deg(pred_zero_deg, true_deg)
        order = max(0, int(harm_order))
        if order <= 0:
            return err_deg, pred_zero_deg

        X_cols = [np.ones_like(theta)]
        for k in range(1, order + 1):
            X_cols.append(np.cos(k * theta))
            X_cols.append(np.sin(k * theta))
        X = np.column_stack(X_cols)
        coef, *_ = np.linalg.lstsq(X, err_deg, rcond=None)
        fitted = X @ coef
        pred_corr = pred_zero_deg - fitted
        corr_err = circular_error_deg(pred_corr, true_deg)
        return corr_err, pred_corr

    def _compute_metrics(self, raw_err_deg, zero_err_deg, corr_err_deg):
        def metrics_for(e):
            return {
                "mean_deg": float(np.mean(e)),
                "mae_deg": float(np.mean(np.abs(e))),
                "rms_deg": float(np.sqrt(np.mean(e**2))),
                "max_abs_deg": float(np.max(np.abs(e))),
                "ptp_deg": float(np.ptp(e)),
                "mean_arcsec": float(np.mean(e) * 3600.0),
                "mae_arcsec": float(np.mean(np.abs(e)) * 3600.0),
                "rms_arcsec": float(np.sqrt(np.mean(e**2)) * 3600.0),
                "max_abs_arcsec": float(np.max(np.abs(e)) * 3600.0),
                "ptp_arcsec": float(np.ptp(e) * 3600.0),
            }
        raw = metrics_for(raw_err_deg)
        zero = metrics_for(zero_err_deg)
        corr = metrics_for(corr_err_deg)
        return {
            "raw": raw,
            "zero": zero,
            "corrected": corr,
            "mean_deg": corr["mean_deg"],
            "mae_deg": corr["mae_deg"],
            "rms_deg": corr["rms_deg"],
            "max_abs_deg": corr["max_abs_deg"],
            "ptp_deg": corr["ptp_deg"],
            "mean_arcsec": corr["mean_arcsec"],
            "mae_arcsec": corr["mae_arcsec"],
            "rms_arcsec": corr["rms_arcsec"],
            "max_abs_arcsec": corr["max_abs_arcsec"],
            "ptp_arcsec": corr["ptp_arcsec"],
        }

    def _error_spectrum(self, theta, err_arcsec, max_harm=24):
        err = err_arcsec - np.mean(err_arcsec)
        fft = np.fft.rfft(err) / len(err)
        harmonics = np.arange(1, min(max_harm, len(fft)-1) + 1)
        amp = 2.0 * np.abs(fft[harmonics])
        return {"harmonics": harmonics, "amp_arcsec": amp}

    # ------------------------------------------------------------------
    # 计算结果（内嵌选项卡，每条曲线可选择显示）
    # ------------------------------------------------------------------
    def _build_result_tab(self, parent):
        """构建结果选项卡静态骨架：左侧可滚动信息/控制区 + 右侧画布宿主。"""
        body = tk.Frame(parent, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=14, pady=14)

        # ---- 左侧：整体可滚动，避免内容被截断 ----
        left_wrap = tk.Frame(body, bg=Theme.BG, width=360)
        left_wrap.pack(side="left", fill="y", padx=(0, 12))
        left_wrap.pack_propagate(False)

        self.result_left_scroll = ScrollableFrame(left_wrap, style_name="TFrame")
        self.result_left_scroll.pack(fill="both", expand=True)
        self.result_left = self.result_left_scroll.body

        # 占位提示
        self.result_placeholder = tk.Label(
            self.result_left,
            text="尚无计算结果。\n\n请在「③误差 / 校正 / 计算」页\n点击「确认结构后开始计算」。",
            bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
            font=(Theme.FONT_FAMILY, 11), justify="center")
        self.result_placeholder.pack(fill="x", padx=4, pady=4, ipady=40)

        # ---- 右侧：画布宿主 ----
        self.result_canvas_host = tk.Frame(body, bg=Theme.BORDER)
        self.result_canvas_host.pack(side="right", fill="both", expand=True)

        self.result_canvas = None
        self._result_toolbar = None
        self._result_rendered = False

        self.result_canvas_placeholder = tk.Label(
            self.result_canvas_host,
            text="计算完成后，曲线与谐波谱将在此显示。",
            bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
            font=(Theme.FONT_FAMILY, 12), justify="center")
        self.result_canvas_placeholder.pack(fill="both", expand=True, padx=1, pady=1)

    def _render_results(self, results, jump=True):
        """把计算结果渲染进结果选项卡（替换原弹窗）。"""
        # 清空左侧旧内容
        for w in self.result_left.winfo_children():
            w.destroy()
        self.result_placeholder = None

        # 清空右侧旧画布
        if self.result_canvas_placeholder is not None:
            self.result_canvas_placeholder.destroy()
            self.result_canvas_placeholder = None
        if self._result_toolbar is not None:
            self._result_toolbar.destroy()
            self._result_toolbar = None
        if self.result_canvas is not None:
            self.result_canvas.get_tk_widget().destroy()
            self.result_canvas = None

        left = self.result_left
        host = self.result_canvas_host

        m = results["metrics"]
        d = results["derived"]

        # ---- 评价结果卡片 ----
        metrics_card = tk.Frame(left, bg=Theme.BG_PANEL)
        metrics_card.pack(fill="x", pady=(0, 10))
        tk.Frame(metrics_card, bg=Theme.ACCENT, height=3).pack(fill="x")
        inner = tk.Frame(metrics_card, bg=Theme.BG_PANEL)
        inner.pack(fill="x", padx=16, pady=14)

        tk.Label(inner, text="评价结果", bg=Theme.BG_PANEL, fg=Theme.ACCENT,
                 font=(Theme.FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))

        # 大号 MAE 高亮
        mae_box = tk.Frame(inner, bg=Theme.BG_PANEL_ALT)
        mae_box.pack(fill="x", pady=(0, 12))
        tk.Label(mae_box, text="角度预测平均误差 (MAE)", bg=Theme.BG_PANEL_ALT,
                 fg=Theme.FG_MUTED,
                 font=(Theme.FONT_FAMILY, 9)).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(mae_box, text=f"{m['mae_arcsec']:.3f} arcsec",
                 bg=Theme.BG_PANEL_ALT, fg=Theme.SUCCESS,
                 font=(Theme.FONT_FAMILY, 19, "bold")).pack(anchor="w", padx=14)
        tk.Label(mae_box, text=f"{m['mae_deg']:.9f} deg", bg=Theme.BG_PANEL_ALT,
                 fg=Theme.FG_MUTED,
                 font=(Theme.FONT_MONO, 9)).pack(anchor="w", padx=14, pady=(0, 12))

        def metric_row(parent, label, value, accent=False):
            row = tk.Frame(parent, bg=Theme.BG_PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=Theme.BG_PANEL, fg=Theme.FG_MUTED,
                     font=(Theme.FONT_FAMILY, 9), anchor="w").pack(side="left")
            tk.Label(row, text=value, bg=Theme.BG_PANEL,
                     fg=Theme.ACCENT if accent else Theme.FG,
                     font=(Theme.FONT_MONO, 9, "bold"),
                     anchor="e").pack(side="right")

        metric_row(inner, "平均有符号误差", f"{m['mean_arcsec']:.3f}\u2033")
        metric_row(inner, "RMS 误差", f"{m['rms_arcsec']:.3f}\u2033")
        metric_row(inner, "最大绝对误差", f"{m['max_abs_arcsec']:.3f}\u2033")
        metric_row(inner, "峰峰值误差", f"{m['ptp_arcsec']:.3f}\u2033")

        tk.Frame(inner, bg=Theme.BORDER, height=1).pack(fill="x", pady=10)

        metric_row(inner, "Tx 等效电感", f"{d['tx_L_uH']:.3f} \u00b5H")
        metric_row(inner, "Tx AC 电阻", f"{d['tx_R_ac_ohm']:.3f} \u03a9")
        metric_row(inner, "推荐谐振电容", f"{d['cap_resonant_nF']:.3f} nF", accent=True)
        metric_row(inner, "趋肤深度", f"{d['skin_depth_um']:.3f} \u00b5m")
        metric_row(inner, "等效 Rx 基波", f"{d['base_rx_mv']:.3f} mV")
        metric_row(inner, "零位偏置", f"{d['zero_bias_deg']:.6f}\u00b0")

        # ---- 曲线显示控制卡片 ----
        control_card = tk.Frame(left, bg=Theme.BG_PANEL)
        control_card.pack(fill="x", pady=(0, 10))
        tk.Frame(control_card, bg=Theme.ACCENT, height=3).pack(fill="x")
        ctrl_inner = tk.Frame(control_card, bg=Theme.BG_PANEL)
        ctrl_inner.pack(fill="x", padx=16, pady=14)

        tk.Label(ctrl_inner, text="曲线显示控制", bg=Theme.BG_PANEL,
                 fg=Theme.ACCENT,
                 font=(Theme.FONT_FAMILY, 12, "bold")).pack(anchor="w", pady=(0, 10))

        # 三个按钮改用 grid 等宽布局，整行铺满，彻底避免「只看误差」被遮挡
        btn_row = tk.Frame(ctrl_inner, bg=Theme.BG_PANEL)
        btn_row.pack(fill="x", pady=(0, 10))
        btn_row.columnconfigure(0, weight=1, uniform="rbtn")
        btn_row.columnconfigure(1, weight=1, uniform="rbtn")
        btn_row.columnconfigure(2, weight=1, uniform="rbtn")
        ttk.Button(btn_row, text="全选", style="Ghost.TButton",
                   command=lambda: self._set_all_lines(True)).grid(
                       row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(btn_row, text="全不选", style="Ghost.TButton",
                   command=lambda: self._set_all_lines(False)).grid(
                       row=0, column=1, sticky="ew", padx=4)
        ttk.Button(btn_row, text="只看误差", style="Accent.TButton",
                   command=self._show_only_errors).grid(
                       row=0, column=2, sticky="ew", padx=(4, 0))

        self.line_checkbox_container = tk.Frame(ctrl_inner, bg=Theme.BG_PANEL)
        self.line_checkbox_container.pack(fill="x")

        # ---- 图表 ----
        fig = Figure(figsize=(10.6, 8.0), dpi=100, facecolor=Theme.PLOT_BG)
        gs = fig.add_gridspec(2, 2, hspace=0.34, wspace=0.26)
        ax_wave = fig.add_subplot(gs[0, 0])
        ax_angle = fig.add_subplot(gs[0, 1])
        ax_error = fig.add_subplot(gs[1, 0])
        ax_spec = fig.add_subplot(gs[1, 1])
        for ax in (ax_wave, ax_angle, ax_error, ax_spec):
            style_axis(ax)

        cyc = Theme.PLOT_CYCLE
        self.line_vars = []
        self.latest_lines = []
        x = results["true_deg"]

        names = ["Fine A", "Fine B", "Fine C", "Coarse A", "Coarse B", "Coarse C"]
        arrays = [
            results["fine_sigs"][0], results["fine_sigs"][1], results["fine_sigs"][2],
            results["coarse_sigs"][0], results["coarse_sigs"][1], results["coarse_sigs"][2],
        ]
        for idx, (name, arr) in enumerate(zip(names, arrays)):
            line, = ax_wave.plot(x, arr, linewidth=0.9, label=name,
                                 color=cyc[idx % len(cyc)])
            self._register_line(name, line, ax_wave)
        ax_wave.set_title("接收波形", color=Theme.PLOT_FG, fontweight="bold")
        ax_wave.set_xlabel("Mechanical angle / deg")
        ax_wave.set_ylabel("Equivalent RX / mV")
        style_legend(ax_wave)

        angle_items = [
            ("True angle", results["true_deg"]),
            ("Raw predicted angle", results["pred_deg"]),
            ("Zero-offset predicted angle", results["pred_zero_deg"]),
            ("LUT corrected predicted angle", results["pred_lut_deg"]),
        ]
        for idx, (name, arr) in enumerate(angle_items):
            line, = ax_angle.plot(x, arr, linewidth=1.0, label=name,
                                  color=cyc[idx % len(cyc)])
            self._register_line(name, line, ax_angle)
        ax_angle.set_title("机械角预测", color=Theme.PLOT_FG, fontweight="bold")
        ax_angle.set_xlabel("True mechanical angle / deg")
        ax_angle.set_ylabel("Predicted angle / deg")
        style_legend(ax_angle)

        err_items = [
            ("Raw error", results["raw_error_arcsec"]),
            ("Zero-offset error", results["zero_error_arcsec"]),
            ("Final corrected error", results["corrected_error_arcsec"]),
        ]
        err_colors = [Theme.FG_MUTED, Theme.WARNING, Theme.SUCCESS]
        for idx, (name, arr) in enumerate(err_items):
            line, = ax_error.plot(x, arr, linewidth=1.1, label=name,
                                  color=err_colors[idx])
            self._register_line(name, line, ax_error)
        ax_error.set_title("角度预测误差", color=Theme.PLOT_FG, fontweight="bold")
        ax_error.set_xlabel("True mechanical angle / deg")
        ax_error.set_ylabel("Error / arcsec")
        ax_error.axhline(0, color=Theme.BORDER, linewidth=0.8, linestyle="--")
        style_legend(ax_error)

        spec = results["spectrum"]
        bars = ax_spec.bar(spec["harmonics"], spec["amp_arcsec"],
                           label="Error harmonic amplitude",
                           color=Theme.ACCENT, edgecolor=Theme.ACCENT_DARK)
        ax_spec.set_title("校正后误差谐波谱", color=Theme.PLOT_FG, fontweight="bold")
        ax_spec.set_xlabel("Mechanical harmonic order")
        ax_spec.set_ylabel("Amplitude / arcsec")
        style_legend(ax_spec)
        self._register_bar_group("Error harmonic bars", bars, ax_spec)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=host)
        self.result_canvas = canvas
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=1, pady=1)
        toolbar = NavigationToolbar2Tk(canvas, host)
        toolbar.config(bg=Theme.BG_PANEL)
        toolbar.update()
        self._result_toolbar = toolbar
        self._result_rendered = True

        self._build_line_checkboxes()
        self._refresh_axes()

        if jump:
            self.notebook.select(self.tab_result)

    def _register_line(self, name, line, ax):
        self.latest_lines.append({"name": name, "artist": line, "axis": ax, "type": "line", "var": tk.BooleanVar(value=True)})

    def _register_bar_group(self, name, bars, ax):
        self.latest_lines.append({"name": name, "artist": list(bars), "axis": ax, "type": "bar", "var": tk.BooleanVar(value=True)})

    def _build_line_checkboxes(self):
        body = self.line_checkbox_container
        for w in body.winfo_children():
            w.destroy()

        groups = [
            ("波形", ["Fine A", "Fine B", "Fine C", "Coarse A", "Coarse B", "Coarse C"]),
            ("角度", ["True angle", "Raw predicted angle", "Zero-offset predicted angle", "LUT corrected predicted angle"]),
            ("误差", ["Raw error", "Zero-offset error", "Final corrected error"]),
            ("频谱", ["Error harmonic bars"]),
        ]

        for group_name, names in groups:
            lf = ttk.LabelFrame(body, text="  " + group_name + "  ",
                                style="Card.TLabelframe", padding=8)
            lf.pack(fill="x", padx=0, pady=5)
            for item in self.latest_lines:
                if item["name"] in names:
                    cb = ttk.Checkbutton(
                        lf,
                        text=item["name"],
                        variable=item["var"],
                        command=self._refresh_axes,
                        style="TCheckbutton"
                    )
                    cb.pack(anchor="w", pady=2, fill="x")

    def _set_all_lines(self, visible):
        for item in self.latest_lines:
            item["var"].set(visible)
        self._refresh_axes()

    def _show_only_errors(self):
        for item in self.latest_lines:
            item["var"].set(item["name"] in ["Raw error", "Zero-offset error", "Final corrected error"])
        self._refresh_axes()

    def _refresh_axes(self):
        axes = set()
        for item in self.latest_lines:
            visible = bool(item["var"].get())
            artist = item["artist"]
            if item["type"] == "line":
                artist.set_visible(visible)
            else:
                for b in artist:
                    b.set_visible(visible)
            axes.add(item["axis"])

        for ax in axes:
            try:
                ax.relim()
                ax.autoscale_view()
                style_legend(ax)
            except Exception:
                pass
        if hasattr(self, "result_canvas"):
            self.result_canvas.draw_idle()

    # ------------------------------------------------------------------
    # 导出
    # ------------------------------------------------------------------
    def export_csv(self):
        if self.latest_results is None:
            messagebox.showwarning("无结果", "尚无计算结果可导出。")
            return

        path = filedialog.asksaveasfilename(
            title="导出计算结果 CSV",
            defaultextension=".csv",
            initialfile="ncs32100_result_v3.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return

        r = self.latest_results
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["NCS32100 calculation result v3"])
            writer.writerow(["MAE arcsec", r["metrics"]["mae_arcsec"]])
            writer.writerow(["MAE deg", r["metrics"]["mae_deg"]])
            writer.writerow(["Mean signed error arcsec", r["metrics"]["mean_arcsec"]])
            writer.writerow(["RMS arcsec", r["metrics"]["rms_arcsec"]])
            writer.writerow(["Max abs arcsec", r["metrics"]["max_abs_arcsec"]])
            writer.writerow(["Peak-to-peak arcsec", r["metrics"]["ptp_arcsec"]])
            writer.writerow([])
            writer.writerow([
                "true_deg", "pred_raw_deg", "pred_zero_deg", "pred_lut_deg",
                "raw_error_arcsec", "zero_error_arcsec", "corrected_error_arcsec",
                "fine_A_mv", "fine_B_mv", "fine_C_mv",
                "coarse_A_mv", "coarse_B_mv", "coarse_C_mv"
            ])
            for i in range(len(r["true_deg"])):
                writer.writerow([
                    r["true_deg"][i], r["pred_deg"][i], r["pred_zero_deg"][i], r["pred_lut_deg"][i],
                    r["raw_error_arcsec"][i], r["zero_error_arcsec"][i], r["corrected_error_arcsec"][i],
                    r["fine_sigs"][0, i], r["fine_sigs"][1, i], r["fine_sigs"][2, i],
                    r["coarse_sigs"][0, i], r["coarse_sigs"][1, i], r["coarse_sigs"][2, i],
                ])

        messagebox.showinfo("导出完成", f"结果已导出：\n{path}")
        self.log(f"结果已导出：{path}")


def main():
    root = tk.Tk()
    app = NCS32100Tool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
