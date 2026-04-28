#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多旋翼无人机悬停续航计算器 v2.6.1
Ivan (LXX LTD)
支持: 共轴双桨 / 不共轴单桨 两种模式
内置电机:
  好盈: H13MD / H15Plus / H15MD Plus (28S)
  T-Motor: X-A14(共轴,24S) / A14-14S(14S) / U15L/U15XL/U15XXL/U15(通用,24S)
电机与电池S数自动绑定对应
"""

import tkinter as tk
from tkinter import ttk, messagebox


class HoverCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("多旋翼悬停续航计算器 v2.6.1")
        self.root.geometry("900x980")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.configure("TLabel", font=("微软雅黑", 10))
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("Header.TLabel", font=("微软雅黑", 13, "bold"))
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title = ttk.Label(main_frame, text="多旋翼悬停续航计算器", style="Header.TLabel")
        title.pack(pady=(0, 5))
        subtitle = ttk.Label(main_frame, text="支持共轴双桨 / 不共轴单桨 | 电机与电池S数自动绑定",
                            font=("微软雅黑", 9), foreground="#666")
        subtitle.pack(pady=(0, 5))

        sep1 = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        sep1.pack(fill=tk.X, pady=3)

        # ========== 布局选择区 ==========
        layout_frame = ttk.LabelFrame(main_frame, text=" 布局模式 ", padding="8")
        layout_frame.pack(fill=tk.X, pady=4)

        self.layout_var = tk.StringVar(value="coaxial")
        layout_inner = ttk.Frame(layout_frame)
        layout_inner.pack(fill=tk.X)

        rb1 = ttk.Radiobutton(layout_inner, text="共轴双桨 (每组上下2个电机)", 
                             variable=self.layout_var, value="coaxial",
                             command=self._on_layout_change)
        rb1.pack(side=tk.LEFT, padx=15)
        rb2 = ttk.Radiobutton(layout_inner, text="不共轴单桨 (每轴1个电机)", 
                             variable=self.layout_var, value="single",
                             command=self._on_layout_change)
        rb2.pack(side=tk.LEFT, padx=15)

        # ========== 第一步：基础参数 ==========
        step1_frame = ttk.LabelFrame(main_frame, text=" 第一步：基础参数 ", padding="8")
        step1_frame.pack(fill=tk.X, pady=4)

        input_grid = ttk.Frame(step1_frame)
        input_grid.pack(fill=tk.X)

        # 行0: 起飞重量 + 电机型号
        ttk.Label(input_grid, text="起飞重量 (kg):").grid(row=0, column=0, sticky=tk.W, pady=4, padx=4)
        self.weight_var = tk.StringVar(value="320")
        ttk.Entry(input_grid, textvariable=self.weight_var, width=12).grid(row=0, column=1, pady=4, padx=4)

        ttk.Label(input_grid, text="电机型号:").grid(row=0, column=2, sticky=tk.W, pady=4, padx=4)
        self.motor_var = tk.StringVar(value="好盈 H15Plus")
        self.motor_combo = ttk.Combobox(input_grid, textvariable=self.motor_var, 
                                   values=["好盈 H13MD", "好盈 H15Plus", "好盈 H15MD Plus", 
                                           "T-Motor X-A14", "T-Motor A14-14S", "T-Motor U15L", 
                                           "T-Motor U15XL", "T-Motor U15XXL", "T-Motor U15(通用)", "其他"],
                                   width=22, state="readonly")
        self.motor_combo.grid(row=0, column=3, pady=4, padx=4)
        self.motor_combo.bind("<<ComboboxSelected>>", self._on_motor_change)

        # 行1: 共轴组数/轴数
        self.axes_label = ttk.Label(input_grid, text="共轴组数:")
        self.axes_label.grid(row=1, column=0, sticky=tk.W, pady=4, padx=4)
        self.axes_var = tk.StringVar(value="4")
        self.axes_entry = ttk.Entry(input_grid, textvariable=self.axes_var, width=12)
        self.axes_entry.grid(row=1, column=1, pady=4, padx=4)
        self.axes_hint = ttk.Label(input_grid, text="(如4组共轴双桨 = 8个电机)")
        self.axes_hint.grid(row=1, column=2, columnspan=2, sticky=tk.W, pady=4)

        # 行2: 电池串联数(S) + 提示（独占一行，避免重叠）
        ttk.Label(input_grid, text="电池串联数 (S):").grid(row=2, column=0, sticky=tk.W, pady=4, padx=4)
        self.s_var = tk.StringVar(value="28")
        self.s_entry = ttk.Entry(input_grid, textvariable=self.s_var, width=12)
        self.s_entry.grid(row=2, column=1, pady=4, padx=4)
        self.s_hint = ttk.Label(input_grid, text="(已根据电机型号自动绑定)")
        self.s_hint.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=4)

        # 行3: 单块容量 + 并联块数
        ttk.Label(input_grid, text="单块容量 (Ah):").grid(row=3, column=0, sticky=tk.W, pady=4, padx=4)
        self.ah_var = tk.StringVar(value="47")
        ttk.Entry(input_grid, textvariable=self.ah_var, width=12).grid(row=3, column=1, pady=4, padx=4)

        ttk.Label(input_grid, text="并联块数:").grid(row=3, column=2, sticky=tk.W, pady=4, padx=4)
        self.parallel_var = tk.StringVar(value="2")
        ttk.Entry(input_grid, textvariable=self.parallel_var, width=12).grid(row=3, column=3, pady=4, padx=4)

        # 行4: 放电倍率 + 单片满电电压
        ttk.Label(input_grid, text="放电倍率 (C):").grid(row=4, column=0, sticky=tk.W, pady=4, padx=4)
        self.c_var = tk.StringVar(value="10")
        ttk.Entry(input_grid, textvariable=self.c_var, width=12).grid(row=4, column=1, pady=4, padx=4)

        ttk.Label(input_grid, text="单片满电电压 (V):").grid(row=4, column=2, sticky=tk.W, pady=4, padx=4)
        self.vcell_var = tk.StringVar(value="4.2")
        ttk.Entry(input_grid, textvariable=self.vcell_var, width=12).grid(row=4, column=3, pady=4, padx=4)

        # 行5: 放电深度
        ttk.Label(input_grid, text="放电深度 DOD:").grid(row=5, column=0, sticky=tk.W, pady=4, padx=4)
        self.dod_var = tk.StringVar(value="0.8")
        ttk.Entry(input_grid, textvariable=self.dod_var, width=12).grid(row=5, column=1, pady=4, padx=4)

        # 按钮
        btn_frame1 = ttk.Frame(step1_frame)
        btn_frame1.pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame1, text="计算单轴/单组悬停拉力", command=self.calc_thrust).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame1, text="重置", command=self.reset).pack(side=tk.LEFT, padx=4)

        # 拉力结果显示
        self.thrust_result = ttk.Label(step1_frame, text="请点击上方按钮计算拉力", 
                                      font=("微软雅黑", 11), foreground="#666")
        self.thrust_result.pack(pady=4)

        # ========== 第二步：力效输入 ==========
        sep2 = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        sep2.pack(fill=tk.X, pady=3)

        step2_frame = ttk.LabelFrame(main_frame, text=" 第二步：输入力效 ", padding="8")
        step2_frame.pack(fill=tk.X, pady=4)

        ttk.Label(step2_frame, text="根据上方计算出的拉力，查阅电机力效表后输入力效值 (g/W):").pack(anchor=tk.W, pady=2)

        eff_frame = ttk.Frame(step2_frame)
        eff_frame.pack(fill=tk.X, pady=4)

        ttk.Label(eff_frame, text="力效 (g/W):").pack(side=tk.LEFT, padx=5)
        self.eff_var = tk.StringVar()
        self.eff_entry = ttk.Entry(eff_frame, textvariable=self.eff_var, width=12)
        self.eff_entry.pack(side=tk.LEFT, padx=5)

        # 参考数据 - 可滚动的 Text 控件
        ref_frame = ttk.Frame(step2_frame)
        ref_frame.pack(fill=tk.X, pady=4)

        self.ref_text = tk.Text(ref_frame, height=8, width=88, 
                                font=("Consolas", 9), wrap=tk.NONE,
                                bg="#f5f5f5", fg="#666", padx=8, pady=5)
        self.ref_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 垂直滚动条
        v_scroll = ttk.Scrollbar(ref_frame, orient=tk.VERTICAL, command=self.ref_text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.ref_text.config(yscrollcommand=v_scroll.set)

        # 水平滚动条
        h_scroll_frame = ttk.Frame(step2_frame)
        h_scroll_frame.pack(fill=tk.X)
        h_scroll = ttk.Scrollbar(h_scroll_frame, orient=tk.HORIZONTAL, command=self.ref_text.xview)
        h_scroll.pack(fill=tk.X)
        self.ref_text.config(xscrollcommand=h_scroll.set)

        # 设置 ref_text 为只读
        self.ref_text.config(state=tk.DISABLED)

        self._update_ref_text()

        ttk.Button(step2_frame, text="计算续航时间", command=self.calc_endurance).pack(pady=4)

        # ========== 结果显示区 ==========
        sep3 = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        sep3.pack(fill=tk.X, pady=3)

        result_frame = ttk.LabelFrame(main_frame, text=" 计算结果 ", padding="8")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.result_text = tk.Text(result_frame, height=24, width=88, 
                                   font=("Consolas", 10), wrap=tk.WORD,
                                   bg="#fafafa", fg="#333", padx=8, pady=8)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "等待计算...")
        self.result_text.config(state=tk.DISABLED)

        # 底部版权
        footer = ttk.Label(main_frame, text="龙巡星智能制造科技有限公司 | 仅供工程估算参考", 
                          font=("微软雅黑", 8), foreground="#999")
        footer.pack(pady=(3, 0))

    def _on_layout_change(self):
        mode = self.layout_var.get()
        if mode == "coaxial":
            self.axes_label.config(text="共轴组数:")
            self.axes_hint.config(text="(如4组共轴双桨 = 8个电机)")
        else:
            self.axes_label.config(text="轴数 / 电机数:")
            self.axes_hint.config(text="(每轴1个电机，如4轴 = 4个电机)")
        self._update_ref_text()

    def _on_motor_change(self, event=None):
        """电机型号改变时，自动绑定对应的电池S数"""
        motor = self.motor_var.get()

        # 电机与推荐S数映射表
        motor_s_map = {
            "好盈 H13MD": 28,
            "好盈 H15Plus": 28,
            "好盈 H15MD Plus": 28,
            "T-Motor X-A14": 24,
            "T-Motor A14-14S": 14,
            "T-Motor U15L": 24,
            "T-Motor U15XL": 24,
            "T-Motor U15XXL": 24,
            "T-Motor U15(通用)": 24,
        }

        if motor in motor_s_map:
            s = motor_s_map[motor]
            self.s_var.set(str(s))
            self.s_hint.config(text="(已根据 %s 自动绑定为 %dS)" % (motor, s), foreground="#5cb85c")
        else:
            self.s_hint.config(text="(已根据电机型号自动绑定)", foreground="#666")

        # 同时更新力效参考文本
        self._update_ref_text()

    def _update_ref_text(self):
        mode = self.layout_var.get()
        motor = self.motor_var.get()

        if mode == "coaxial":
            text = (
                "【共轴双桨】官方共轴总力效参考 (g/W):\n"
                "好盈 H13MD 54x20\" @108V/28S:      30kg->10.5 | 40kg->9.4 | 50kg->8.5 | 60kg->7.8 | 70kg->7.2 | 80kg->6.8\n"
                "好盈 H15Plus 72x25\" @108V/28S:    40kg->9.7 | 60kg->8.3 | 80kg->7.1 | 100kg->6.2 | 120kg->5.3\n"
                "好盈 H15MD Plus 73x21\" @108V/28S:  40kg->9.9 | 60kg->8.6 | 80kg->7.4 | 100kg->6.6 | 120kg->5.9\n"
                "T-Motor X-A14 KV37 EZ57 @100V/24S:  37kg->8.5 | 46kg->7.4 | 55kg->7.1 | 63kg->6.4 | 73kg->6.0 | 82kg->5.5 | 92kg->5.1 | 116kg->4.0 (官方实测)\n"
                "T-Motor A14-14S MF56P @52V/14S:    30kg->9.8 | 40kg->8.9 | 50kg->8.1 | 60kg->7.4 (估算)\n"
                "【注意】T-Motor U15L/U15XL/U15XXL 为单轴电机设计，无官方共轴数据，请切换至不共轴模式"
            )
        else:
            text = (
                "【不共轴单桨】官方单轴力效参考 (g/W):\n"
                "好盈 H13MD 54x20\" 上轴 @108V/28S:   20kg->11.4 | 30kg->10.7 | 40kg->10.3 | 50kg->9.2 | 60kg->8.6 | 70kg->8.1\n"
                "好盈 H15Plus 72x25\" 上轴 @108V/28S:  20kg->11.4 | 40kg->10.5 | 60kg->9.9 | 80kg->9.3 | 100kg->8.6\n"
                "好盈 H15MD Plus 73x21\" 上轴 @108V/28S: 20kg->12.7 | 40kg->11.3 | 60kg->10.1 | 80kg->9.2 | 100kg->8.5\n"
                "T-Motor A14-14S MF56P @52V/14S:     20kg->10.2 | 25kg->9.2 | 30kg->8.6 | 35kg->8.1 | 40kg->7.6 | 50kg->6.8\n"
                "T-Motor U15L NS47x18 @24S:          15kg->11.2 | 25kg->9.8 | 35kg->8.6 | 45kg->7.5 | 55kg->6.6 (官方参数估算)\n"
                "T-Motor U15XL NS52x20 @24S:         20kg->11.5 | 30kg->10.2| 45kg->8.9 | 60kg->7.7 | 75kg->6.8 (官方参数估算)\n"
                "T-Motor U15XXL NS57x22 @24S:        25kg->12.0 | 40kg->10.8| 55kg->9.5 | 70kg->8.2 | 85kg->7.1 (官方参数估算)\n"
                "【注意】T-Motor X-A14 为共轴动力系统设计，无官方单轴数据，请切换至共轴模式"
            )
        self.ref_text.config(state=tk.NORMAL)
        self.ref_text.delete(1.0, tk.END)
        self.ref_text.insert(tk.END, text)
        self.ref_text.config(state=tk.DISABLED)

    def calc_thrust(self):
        try:
            weight = float(self.weight_var.get())
            axes = float(self.axes_var.get())
            mode = self.layout_var.get()
            motor = self.motor_var.get()

            if weight <= 0 or axes <= 0:
                messagebox.showerror("输入错误", "起飞重量和轴数/组数必须大于0")
                return

            # U15系列为单轴电机，共轴模式下提示
            if mode == "coaxial" and "U15" in motor:
                messagebox.showwarning("模式不匹配", 
                    "T-Motor U15L/U15XL/U15XXL 为单轴电机设计，无官方共轴数据。\n"
                    "请切换至【不共轴单桨】模式后重新计算。")
                return

            # X-A14为共轴电机，不共轴模式下提示
            if mode == "single" and "X-A14" in motor:
                messagebox.showwarning("模式不匹配", 
                    "T-Motor X-A14 为共轴动力系统设计，无官方单轴数据。\n"
                    "请切换至【共轴双桨】模式后重新计算。")
                return

            thrust_g = (weight * 1000.0) / axes
            thrust_kg = thrust_g / 1000.0

            if mode == "coaxial":
                label_text = "单组共轴悬停拉力: %.0f g = %.1f kg/组 (每组2个电机)" % (thrust_g, thrust_kg)
            else:
                label_text = "单轴悬停拉力: %.0f g = %.1f kg/轴 (每轴1个电机)" % (thrust_g, thrust_kg)

            self.thrust_result.config(
                text=label_text,
                foreground="#d9534f", font=("微软雅黑", 11, "bold")
            )

            ref_eta = self._estimate_eta(motor, thrust_kg, mode)

            if ref_eta > 0:
                self.eff_var.set("%.3f" % ref_eta)
                if mode == "coaxial":
                    hint = "已根据 %s 官方【共轴总力效】表自动推荐" % motor
                else:
                    hint = "已根据 %s 官方【单轴力效】表自动推荐" % motor
                self._show_result(
                    "【拉力计算完成】\n" + label_text + "\n" + hint + ": %.3f g/W\n" % ref_eta +
                    "您可修改力效值后点击【计算续航时间】"
                )
            else:
                self._show_result(
                    "【拉力计算完成】\n" + label_text + "\n" +
                    "请查阅您的电机力效表，输入对应力效值后计算续航。"
                )

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")

    def _estimate_eta(self, motor, thrust_kg, mode):
        """根据电机型号、拉力、布局模式估算力效"""

        # U15系列为单轴电机，共轴模式下无官方数据
        if mode == "coaxial" and "U15" in motor:
            return 0

        # X-A14为共轴电机，不共轴模式下无官方数据
        if mode == "single" and "X-A14" in motor:
            return 0

        # ===== 共轴双桨力效表 =====
        # H13MD 54x20" 108V/28S 共轴总力效 (官方)
        h13md_coaxial = {
            20: 11.0, 30: 10.5, 40: 9.4, 50: 8.5, 60: 7.8,
            70: 7.2, 80: 6.8, 90: 6.3, 100: 5.9, 110: 5.5
        }
        # H15Plus 72x25" 108V/28S 共轴总力效 (官方)
        h15_coaxial = {
            20: 11.4, 30: 10.5, 40: 9.7, 50: 8.9, 60: 8.3,
            70: 7.8, 80: 7.1, 90: 6.8, 100: 6.2, 120: 5.3, 150: 4.5
        }
        # H15MD Plus 73x21" 108V/28S 共轴总力效 (官方)
        h15md_coaxial = {
            30: 11.1, 40: 9.9, 50: 9.0, 60: 8.6, 70: 8.3,
            80: 7.4, 90: 7.1, 100: 6.6, 110: 6.3, 120: 5.9, 150: 5.1
        }
        # T-Motor X-A14 KV37 EZ57 100V/24S 共轴总力效 (官方实测数据)
        # 数据来源: X-A14-24S共轴产品规格书 2026-01-30
        # 测试条件: 100V(24S满电) + 57寸折叠桨 + 30C环境
        xa14_coaxial = {
            10: 17.5,   # 30%油门 10332gf
            16: 13.5,   # 35%油门 16094gf
            22: 11.4,   # 40%油门 22257gf
            29: 9.6,    # 45%油门 29282gf
            37: 8.5,    # 50%油门 37349gf
            46: 7.4,    # 55%油门 45742gf (额定区 45-50kg)
            55: 7.1,    # 60%油门 54509gf
            63: 6.4,    # 65%油门 63140gf
            73: 6.0,    # 70%油门 72857gf
            82: 5.5,    # 75%油门 82017gf
            92: 5.1,    # 80%油门 91578gf
            101: 4.8,   # 85%油门 101372gf
            111: 4.4,   # 90%油门 110932gf
            116: 4.0    # 95-100%油门 116116-116474gf (最大113kg)
        }
        # T-Motor A14-14S MF56P 52V/14S 共轴总力效 (基于单轴估算)
        a14_coaxial = {
            20: 10.2, 30: 9.8, 40: 8.9, 50: 8.1, 60: 7.4,
            70: 6.8, 80: 6.3, 90: 5.9, 100: 5.5
        }

        # ===== 不共轴单桨力效表 =====
        # H13MD 54x20" 108V/28S 上轴单轴力效 (官方)
        h13md_single = {
            10: 12.0, 15: 10.0, 20: 11.4, 25: 10.8, 30: 10.7,
            35: 10.3, 40: 10.3, 45: 9.7, 50: 9.2, 55: 8.8,
            60: 8.6, 65: 8.2, 70: 8.1, 75: 7.7, 80: 7.4
        }
        # H15Plus 72x25" 108V/28S 上轴单轴力效 (官方)
        h15_single = {
            10: 13.2, 20: 11.4, 30: 10.5, 40: 10.0, 50: 9.5,
            60: 9.3, 70: 8.9, 80: 8.6, 90: 8.2, 100: 7.9, 120: 7.3
        }
        # H15MD Plus 73x21" 108V/28S 上轴单轴力效 (官方)
        h15md_single = {
            10: 14.0, 20: 12.7, 30: 11.5, 40: 10.8, 50: 10.2,
            60: 9.8, 70: 9.4, 80: 9.0, 90: 8.6, 100: 8.2, 120: 7.5
        }
        # T-Motor A14-14S MF56P 52V/14S 单轴力效 (官方)
        a14_single = {
            10: 11.5, 15: 10.8, 20: 10.2, 25: 9.2, 30: 8.6,
            35: 8.1, 40: 7.6, 45: 7.2, 50: 6.8, 55: 6.4
        }
        # T-Motor U15L NS47x18 24S 单轴力效 (基于官方参数估算)
        u15l_single = {
            10: 12.0, 15: 11.2, 20: 10.5, 25: 9.8, 30: 9.1,
            35: 8.6, 40: 8.0, 45: 7.5, 50: 7.1, 55: 6.6, 60: 6.2
        }
        # T-Motor U15XL NS52x20 24S 单轴力效 (基于官方参数估算)
        u15xl_single = {
            15: 12.5, 20: 11.5, 25: 10.8, 30: 10.2, 35: 9.6,
            40: 9.0, 45: 8.5, 50: 8.0, 55: 7.5, 60: 7.1, 65: 6.7, 70: 6.3, 75: 6.0
        }
        # T-Motor U15XXL NS57x22 24S 单轴力效 (基于官方参数估算)
        u15xxl_single = {
            20: 13.0, 25: 12.0, 30: 11.3, 35: 10.7, 40: 10.2,
            45: 9.7, 50: 9.2, 55: 8.7, 60: 8.3, 65: 7.9, 70: 7.5, 75: 7.1, 80: 6.8, 85: 6.4
        }
        # T-Motor U15 通用参考
        u15_single = {
            10: 12.5, 20: 11.5, 30: 10.5, 40: 9.5, 50: 8.6,
            60: 7.8, 70: 7.1, 80: 6.5, 90: 6.0, 100: 5.6
        }

        # 选择对应数据表
        data = None
        if mode == "coaxial":
            if "X-A14" in motor:
                data = xa14_coaxial
            elif "H13MD" in motor:
                data = h13md_coaxial
            elif "H15MD" in motor:
                data = h15md_coaxial
            elif "H15" in motor:
                data = h15_coaxial
            elif "A14" in motor:
                data = a14_coaxial
        else:  # single
            if "H13MD" in motor:
                data = h13md_single
            elif "H15MD" in motor:
                data = h15md_single
            elif "H15" in motor:
                data = h15_single
            elif "A14" in motor:
                data = a14_single
            elif "U15XXL" in motor:
                data = u15xxl_single
            elif "U15XL" in motor:
                data = u15xl_single
            elif "U15L" in motor:
                data = u15l_single
            elif "U15" in motor:
                data = u15_single

        if data is None:
            return 0

        # 线性插值
        keys = sorted(data.keys())
        if thrust_kg <= keys[0]:
            return data[keys[0]]
        if thrust_kg >= keys[-1]:
            return data[keys[-1]]

        for i in range(len(keys) - 1):
            if keys[i] <= thrust_kg <= keys[i+1]:
                t = (thrust_kg - keys[i]) / (keys[i+1] - keys[i])
                return data[keys[i]] + t * (data[keys[i+1]] - data[keys[i]])
        return data[keys[-1]]

    def calc_endurance(self):
        try:
            weight = float(self.weight_var.get())
            axes = float(self.axes_var.get())
            s_count = float(self.s_var.get())
            ah = float(self.ah_var.get())
            parallel = float(self.parallel_var.get())
            c_rate = float(self.c_var.get())
            v_cell = float(self.vcell_var.get())
            dod = float(self.dod_var.get())
            eta = float(self.eff_var.get())
            mode = self.layout_var.get()
            motor = self.motor_var.get()

            if any(v <= 0 for v in [weight, axes, s_count, ah, parallel, c_rate, v_cell, dod, eta]):
                messagebox.showerror("输入错误", "所有参数必须大于0")
                return

            # U15系列为单轴电机，共轴模式下提示
            if mode == "coaxial" and "U15" in motor:
                messagebox.showwarning("模式不匹配", 
                    "T-Motor U15L/U15XL/U15XXL 为单轴电机设计，无官方共轴数据。\n"
                    "请切换至【不共轴单桨】模式后重新计算。")
                return

            # X-A14为共轴电机，不共轴模式下提示
            if mode == "single" and "X-A14" in motor:
                messagebox.showwarning("模式不匹配", 
                    "T-Motor X-A14 为共轴动力系统设计，无官方单轴数据。\n"
                    "请切换至【共轴双桨】模式后重新计算。")
                return

            v_bat = s_count * v_cell
            total_ah = ah * parallel
            e_usable = v_bat * total_ah * dod
            total_power = (weight * 1000.0) / eta
            time_min = (e_usable / total_power) * 60.0

            i_hover = total_power / v_bat
            i_max = total_ah * c_rate
            safety_margin = i_max / i_hover

            thrust_per_axis = (weight * 1000.0) / axes
            power_per_axis = total_power / axes

            if safety_margin >= 2.0:
                safety_text = "安全 (余量 %.2f 倍，建议 >2.0)" % safety_margin
            elif safety_margin >= 1.3:
                safety_text = "警告 (余量 %.2f 倍，建议 >2.0)" % safety_margin
            else:
                safety_text = "危险 (余量 %.2f 倍，远低于安全线)" % safety_margin

            time_ideal = time_min * 0.90
            time_normal = time_min * 0.85
            time_conservative = time_min * 0.80

            if mode == "coaxial":
                layout_name = "共轴双桨"
                axis_label = "共轴组数"
                thrust_label = "单组共轴拉力"
                motor_label = "每组电机数: 2 (上下各1)"
            else:
                layout_name = "不共轴单桨"
                axis_label = "轴数"
                thrust_label = "单轴拉力"
                motor_label = "每轴电机数: 1"

            result = (
                "=============================================================\n"
                "                   悬停续航计算结果\n"
                "=============================================================\n"
                "\n"
                "【布局模式】  %s\n"
                "【基础参数】\n"
                "  起飞重量:     %.0f kg\n"
                "  %s:         %.0f\n"
                "  %s\n"
                "  电机型号:     %s\n"
                "  电池配置:     %.0fS %.0fAh x %.0f 并联 = %.0fAh\n"
                "  满电电压:     %.1f V (%.1fV/芯 x %.0fS)\n"
                "  放电深度:     %.0f%%\n"
                "\n"
                "【拉力与功率】\n"
                "  %s:   %.0f g (%.1f kg)\n"
                "  输入力效:     %.3f g/W\n"
                "  总悬停功率:   %.0f W\n"
                "  单轴/单组功率: %.0f W\n"
                "\n"
                "【电池能量】\n"
                "  可用能量:     %.0f Wh\n"
                "\n"
                "【电流安全校验】\n"
                "  悬停电流:     %.1f A\n"
                "  最大放电:     %.0f A (%.0fC)\n"
                "  放电余量:     %.2f 倍\n"
                "  安全状态:     %s\n"
                "\n"
                "=============================================================\n"
                "  ★★★ 理论悬停续航: %.1f 分钟 ★★★\n"
                "=============================================================\n"
                "\n"
                "【实际飞行修正】\n"
                "  理想工况 (机动裕量10%%):  %.1f 分钟\n"
                "  常规工况 (机动+线损15%%): %.1f 分钟\n"
                "  保守工况 (综合损耗20%%):  %.1f 分钟\n"
                "\n"
                "=============================================================\n"
            ) % (
                layout_name,
                weight, axis_label, axes, motor_label, self.motor_var.get(),
                s_count, ah, parallel, total_ah,
                v_bat, v_cell, s_count, dod*100,
                thrust_label, thrust_per_axis, thrust_per_axis/1000, eta,
                total_power, power_per_axis,
                e_usable,
                i_hover, i_max, c_rate, safety_margin, safety_text,
                time_min,
                time_ideal, time_normal, time_conservative
            )

            self._show_result(result)

        except ValueError:
            messagebox.showerror("输入错误", "请确保所有输入均为有效数字")

    def _show_result(self, text):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)

    def reset(self):
        self.weight_var.set("320")
        self.axes_var.set("4")
        self.s_var.set("28")
        self.s_hint.config(text="(已根据电机型号自动绑定)", foreground="#666")
        self.ah_var.set("47")
        self.parallel_var.set("2")
        self.c_var.set("10")
        self.vcell_var.set("4.2")
        self.dod_var.set("0.8")
        self.eff_var.set("")
        self.layout_var.set("coaxial")
        self._on_layout_change()
        self.thrust_result.config(text="请点击上方按钮计算拉力", foreground="#666")
        self._show_result("等待计算...")


if __name__ == "__main__":
    root = tk.Tk()
    app = HoverCalculator(root)
    root.mainloop()