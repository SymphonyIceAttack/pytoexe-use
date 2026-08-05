"""螺栓 Bocad 脚本生成器

依 m20x130.txt 语法，按用户输入的 4 个参数生成 .txt 文件。
- 输入：圆柱毛坯直径、毛坯长度、六棱柱高度、切削后圆柱直径
- 输出：Bocad 数据列表文件
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox


# === 原始 m20x130.txt 关键常量 ===
ORIG_D = 34.7  # 原毛坯直径
ORIG_L = 142.5  # 原毛坯长度

# 切角（NREVOLUTION）原始顶点（5 点：v5=v1 闭合，首点带 POS）
ORIG_CHAMFER = [
    (0, -10.01),       # 内径
    (0, -18),          # 外径
    (-130, -18),       # 沿杆长
    (-130, -10.01),
    (0, -10.01),       # 闭合（与 v1 同坐标）
]

# 头部（NXTRUSION）右半顶点（10 点：v10=v1 闭合）
ORIG_HEAD_RIGHT = [
    (0, 0),
    (8.68, -2.32),
    (15.03, -8.67),
    (17.35, -17.35),
    (15.03, -26.02),
    (8.68, -32.38),
    (0, -34.7),
    (15, -26),
    (15, -8.7),
    (0, 0),
]

ORIG_HEAD_LEFT = [
    (0, 0),
    (-8.68, -2.32),
    (-15.03, -8.67),
    (-17.36, -17.35),
    (-15.03, -26.02),
    (-8.68, -32.38),
    (0, -34.7),
    (-15.01, -26),
    (-15.01, -8.7),
    (-0.01, 0),
]

ORIG_Y_OFFSET = -0.01   # 第二段 NXTRUSION Y 微偏移
ORIG_CYL_POS = "POS X -256mm Y 632.22mm Z -46.25mm"  # 项目坐标系，沿用原值
ORIG_SUBEQUIP = "/84XN001_FASTENER"


def fmt(v):
    """格式化浮点数：整数显示无小数；其余保留 2 位小数并去尾零。"""
    v = round(v, 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def format_loop(vertices, skip_first_pos=False):
    """把 (x, y) 列表转成 Bocad 的 NEW VERTEX 串。

    skip_first_pos: 若为 True，首点不输出 POS（用于头部环，首点隐含为原点）。
    """
    parts = []
    for i, (x, y) in enumerate(vertices):
        parts.append("NEW VERTEX")
        if not (skip_first_pos and i == 0):
            parts.append(f"POS X {fmt(x)}mm Y {fmt(y)}mm Z 0mm")
        parts.append("")  # 空行
        parts.append("END")
    return "\n".join(parts)


def generate_bolt_txt(D_stock, L_stock, h_head, D_shank):
    """根据 4 个参数生成 Bocad .txt 内容。

    Args:
        D_stock:  圆柱毛坯直径 (mm)，正数
        L_stock:  毛坯长度 (mm)，正数
        h_head:   六棱柱高度 (mm)，正数且 < L_stock
        D_shank:  切削后圆柱直径 (mm)，正数且 < D_stock
    """
    # 校验
    if D_stock <= 0 or L_stock <= 0 or h_head <= 0 or D_shank <= 0:
        raise ValueError("所有尺寸必须为正数")
    if h_head >= L_stock:
        raise ValueError(f"六棱柱高度 ({h_head}mm) 必须小于毛坯长度 ({L_stock}mm)，"
                         f"以保证切削后有杆部。")
    if D_shank >= D_stock:
        raise ValueError(f"切削后直径 ({D_shank}mm) 必须小于毛坯直径 ({D_stock}mm)。")

    shank_L = L_stock - h_head
    scale = D_stock / ORIG_D

    # 切角顶点
    # - 内径 = D_shank/2 + 0.01（杆半径 + 微小间隙，避开退化几何）
    # - 外径 = D_stock/2 + 0.65*scale（头部外接圆 + 倒角余量，按 D 等比缩放）
    chamfer_inner = D_shank / 2 + 0.01
    chamfer_outer = D_stock / 2 + 0.65 * scale
    chamfer = [
        (0.0, -chamfer_inner),
        (0.0, -chamfer_outer),
        (-shank_L, -chamfer_outer),
        (-shank_L, -chamfer_inner),
        (0.0, -chamfer_inner),
    ]

    # 头部顶点（按 D 缩放）
    head_right = [(x * scale, y * scale) for (x, y) in ORIG_HEAD_RIGHT]
    head_left  = [(x * scale, y * scale) for (x, y) in ORIG_HEAD_LEFT]
    y_offset = ORIG_Y_OFFSET * scale

    # 位置参数
    nrev_pos_z = L_stock / 2
    head_pos_z = -(L_stock / 2 - h_head)
    cyl_x = -D_stock / 2

    # 时间戳（沿用原格式：日  月  年  时:分）
    now = datetime.now()
    day = now.day
    month_abbr = now.strftime("%b")
    year = now.year
    hour = now.hour
    minute = now.minute
    date_str = f"{day}  {month_abbr} {year} {hour}:{minute:02d}"

    nrev_loop      = format_loop(chamfer, skip_first_pos=False)
    head_right_str = format_loop(head_right, skip_first_pos=True)
    head_left_str  = format_loop(head_left,  skip_first_pos=True)

    content = f"""$S-  -- Synonym translation OFF
-- ----------------------------------------------------------------
-- Data Listing    Date : {date_str}

ONERROR GOLABEL /ERROR3

INPUT BEGIN
NEW CYLINDER
{ORIG_CYL_POS}
ORI Y is -Y and Z is Z
DIAM {fmt(D_stock)}mm
HEIG {fmt(L_stock)}mm

NEW NREVOLUTION
POS X 0mm Y 0mm Z {fmt(nrev_pos_z)}mm
ORI Y is -X and Z is -Y
ANGL 0degree

NEW LOOP

{nrev_loop}
END
END
NEW NXTRUSION
POS X {fmt(cyl_x)}mm Y 0mm Z {fmt(head_pos_z)}mm
ORI Y is -X and Z is -Z
HEIG {fmt(h_head)}mm

NEW LOOP

{head_right_str}
END
END
NEW NXTRUSION
POS X {fmt(cyl_x)}mm Y {fmt(y_offset)}mm Z {fmt(head_pos_z)}mm
ORI Y is -X and Z is -Z
HEIG {fmt(h_head)}mm

NEW LOOP

{head_left_str}
END
END
END
INPUT END  CYLINDER 1 of SUBEQUIPMENT {ORIG_SUBEQUIP}
INPUT FINISH
-- Switch synonyms back on if an error occurs.
LABEL /ERROR3
handle ANY
$S+
RETURN ERROR
endhandle

-- End Data Listing    Date : {date_str}
$S+  -- Synonym translation ON
-- ----------------------------------------------------------------
"""
    return content


# === GUI ===

class BoltGeneratorApp:
    def __init__(self, root):
        self.root = root
        root.title("螺栓 Bocad 脚本生成器")
        root.geometry("440x270")
        root.resizable(False, False)

        # 数值校验：只允许正数（含空与中间态，如 "1."）
        vcmd = (root.register(self._validate_positive), "%P")

        labels = [
            ("圆柱毛坯直径 (mm)", "d_stock"),
            ("毛坯长度 (mm)",     "l_stock"),
            ("六棱柱高度 (mm)",   "h_head"),
            ("切削后圆柱直径 (mm)", "d_shank"),
        ]

        self.entries = {}
        frame = tk.Frame(root, padx=20, pady=16)
        frame.pack(fill="both", expand=True)

        for i, (label, key) in enumerate(labels):
            lbl = tk.Label(frame, text=label, anchor="w")
            lbl.grid(row=i, column=0, sticky="w", pady=4, padx=(0, 12))
            entry = tk.Entry(frame, validate="key", validatecommand=vcmd, width=22)
            entry.grid(row=i, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        frame.grid_columnconfigure(1, weight=1)

        # 按钮
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=(18, 0))

        self.gen_btn = tk.Button(btn_frame, text="生成螺栓",
                                 width=14, command=self.on_generate)
        self.gen_btn.pack(side="left", padx=6)
        self.clear_btn = tk.Button(btn_frame, text="清除全部输入",
                                   width=14, command=self.on_clear)
        self.clear_btn.pack(side="left", padx=6)

    def _validate_positive(self, text):
        """仅允许非负数串：空、纯数字、含一个小数点。"""
        if text == "":
            return True
        if not re.match(r"^\d*\.?\d*$", text):
            return False
        try:
            return float(text) >= 0
        except ValueError:
            return False

    def _get_float(self, key, label):
        raw = self.entries[key].get().strip()
        if not raw:
            raise ValueError(f"「{label}」不能为空")
        try:
            val = float(raw)
        except ValueError:
            raise ValueError(f"「{label}」必须是数字")
        if val <= 0:
            raise ValueError(f"「{label}」必须为正数")
        return val

    def on_generate(self):
        try:
            D_stock  = self._get_float("d_stock",  "圆柱毛坯直径")
            L_stock  = self._get_float("l_stock",  "毛坯长度")
            h_head   = self._get_float("h_head",   "六棱柱高度")
            D_shank  = self._get_float("d_shank",  "切削后圆柱直径")
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return

        shank_L = L_stock - h_head
        if shank_L <= 0:
            messagebox.showerror("参数错误",
                                 f"六棱柱高度 ({h_head}mm) 必须小于毛坯长度 ({L_stock}mm)")
            return

        try:
            content = generate_bolt_txt(D_stock, L_stock, h_head, D_shank)
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        path = filedialog.asksaveasfilename(
            title="保存螺栓 Bocad 脚本",
            defaultextension=".txt",
            initialfile="bolt.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            Path(path).write_text(content, encoding="utf-8")
        except OSError as e:
            messagebox.showerror("保存失败", str(e))
            return

        messagebox.showinfo(
            "完成",
            f"已生成：\n{path}\n\n"
            f"毛坯: Ø{D_stock} × L{L_stock} mm\n"
            f"头高: {h_head} mm（外接圆 Ø{D_stock}）\n"
            f"杆部: Ø{D_shank} × L{shank_L} mm",
        )

    def on_clear(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)


def main():
    root = tk.Tk()
    BoltGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
