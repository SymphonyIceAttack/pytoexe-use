
import io
from dataclasses import dataclass
from typing import List, Tuple, Dict
import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

st.set_page_config(page_title="Раскладка изделий (гуилотинная)", layout="centered")

@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    label: str
    orient: str  # 'A' or 'B'

@dataclass
class Plan:
    name: str
    description: str
    main_orient: str
    n_main_cols: int
    n_main_rows: int
    extras_right: Tuple[int, int]
    extras_bottom: Tuple[int, int]
    rects: List[Rect]
    total: int
    main_block_size: Tuple[float, float]  # (W_main, H_main)
    trims: Dict[str, Tuple[float, float]]  # right, bottom, corner
    used_area: float

def pitch_fit(total: float, size: float, gap: float) -> int:
    if size <= 0 or total <= 0:
        return 0
    if gap < 0: gap = 0.0
    # n * size + (n-1) * gap <= total
    return max(0, int(math.floor((total + gap) / (size + gap))))

def build_main(sheet_w, sheet_h, iw, ih, gap, orient_label) -> Tuple[int, int, List[Rect], Tuple[float, float]]:
    n_cols = pitch_fit(sheet_w, iw, gap)
    n_rows = pitch_fit(sheet_h, ih, gap)
    rects = []
    for r in range(n_rows):
        for c in range(n_cols):
            x = c * (iw + gap)
            y = r * (ih + gap)
            rects.append(Rect(x, y, iw, ih, f"r{r+1} c{c+1}", orient_label))
    w_main = n_cols * iw + max(0, n_cols - 1) * gap
    h_main = n_rows * ih + max(0, n_rows - 1) * gap
    return n_cols, n_rows, rects, (w_main, h_main)

def build_mixed(sheet_w, sheet_h, iw, ih, gap, main_is_A: bool) -> Plan:
    # Main orientation
    if main_is_A:
        mw, mh = iw, ih
        rw, rh = ih, iw  # rotated for extras
        main_label = "А"
    else:
        mw, mh = ih, iw
        rw, rh = iw, ih
        main_label = "Б"

    n_cols, n_rows, rects, (w_main, h_main) = build_main(sheet_w, sheet_h, mw, mh, gap, main_label)

    # Extras in right stripe (height limited to main block)
    right_w = max(0.0, sheet_w - w_main)
    right_h = h_main
    n_cols_right = pitch_fit(right_w, rw, gap)
    n_rows_right = pitch_fit(right_h, rh, gap)
    x0_right = w_main
    for r in range(n_rows_right):
        for c in range(n_cols_right):
            x = x0_right + c * (rw + gap)
            y = r * (rh + gap)
            rects.append(Rect(x, y, rw, rh, f"R r{r+1} c{c+1}", "Б" if main_is_A else "А"))

    # Extras in bottom stripe (width is full sheet, below main block)
    bottom_h = max(0.0, sheet_h - h_main)
    bottom_w = sheet_w
    n_cols_bottom = pitch_fit(bottom_w, rw, gap)
    n_rows_bottom = pitch_fit(bottom_h, rh, gap)
    y0_bottom = h_main
    for r in range(n_rows_bottom):
        for c in range(n_cols_bottom):
            x = c * (rw + gap)
            y = y0_bottom + r * (rh + gap)
            rects.append(Rect(x, y, rw, rh, f"B r{r+1} c{c+1}", "Б" if main_is_A else "А"))

    total = len(rects)
    used_area = sum(r.w * r.h for r in rects)

    # Trims relative to main block
    trim_right = (max(0.0, sheet_w - w_main), max(0.0, h_main))
    trim_bottom = (sheet_w, max(0.0, sheet_h - h_main))
    corner = (trim_right[0], max(0.0, trim_bottom[1]))  # bottom-right rectangle size

    desc = f"Смешанная: основной блок ориентации {main_label}, повёрнутые изделия в правой и нижней полосах."

    return Plan(
        name="Смешанная",
        description=desc,
        main_orient=main_label,
        n_main_cols=n_cols,
        n_main_rows=n_rows,
        extras_right=(n_cols_right, n_rows_right),
        extras_bottom=(n_cols_bottom, n_rows_bottom),
        rects=rects,
        total=total,
        main_block_size=(w_main, h_main),
        trims={"right": trim_right, "bottom": trim_bottom, "corner": corner},
        used_area=used_area,
    )

def build_pure(sheet_w, sheet_h, iw, ih, gap, is_A: bool) -> Plan:
    if is_A:
        mw, mh = iw, ih
        label = "А"
        name = "Ориентация А"
    else:
        mw, mh = ih, iw
        label = "Б"
        name = "Ориентация Б"

    n_cols, n_rows, rects, (w_main, h_main) = build_main(sheet_w, sheet_h, mw, mh, gap, label)
    total = len(rects)
    used_area = total * iw * ih  # изделия одинаковые по площади

    trim_right = (max(0.0, sheet_w - w_main), max(0.0, h_main))
    trim_bottom = (sheet_w, max(0.0, sheet_h - h_main))
    corner = (trim_right[0], max(0.0, trim_bottom[1]))

    desc = f"Полная сетка в ориентации {label}: {n_cols}×{n_rows} без доп. полос."

    return Plan(
        name=name,
        description=desc,
        main_orient=label,
        n_main_cols=n_cols,
        n_main_rows=n_rows,
        extras_right=(0, 0),
        extras_bottom=(0, 0),
        rects=rects,
        total=total,
        main_block_size=(w_main, h_main),
        trims={"right": trim_right, "bottom": trim_bottom, "corner": corner},
        used_area=used_area,
    )

def choose_best(plans: List[Plan]) -> Plan:
    return max(plans, key=lambda p: (p.total, p.used_area))

def draw_plan(plan: Plan, sheet_w: float, sheet_h: float, gap: float) -> Tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(min(10, sheet_w/5+2), min(8, sheet_h/5+2)))
    # Sheet
    ax.add_patch(Rectangle((0, 0), sheet_w, sheet_h, facecolor="#E0E0E0", edgecolor="black", lw=1.5, zorder=0))
    # Hatch trims (relative to main block geometry)
    w_main, h_main = plan.main_block_size
    # Right trim
    tr_w, tr_h = plan.trims["right"]
    if tr_w > 0 and tr_h > 0:
        ax.add_patch(Rectangle((w_main, 0), tr_w, tr_h, facecolor="none", edgecolor="black", hatch="///", lw=0.5, zorder=1))
    # Bottom trim
    bt_w, bt_h = plan.trims["bottom"]
    if bt_h > 0:
        ax.add_patch(Rectangle((0, h_main), bt_w, bt_h, facecolor="none", edgecolor="black", hatch="///", lw=0.5, zorder=1))
    # Corner shown implicitly via overlaps of the two hatched rectangles

    # Items
    for r in plan.rects:
        color = "#90CAF9"  # light blue
        ax.add_patch(Rectangle((r.x, r.y), r.w, r.h, facecolor=color, edgecolor="#1976D2", lw=1.0, zorder=5))
        # label
        cx = r.x + r.w/2
        cy = r.y + r.h/2
        ax.text(cx, cy, r.label, ha="center", va="center", fontsize=7, color="#0D47A1", zorder=6)

    ax.set_xlim(0, sheet_w)
    ax.set_ylim(0, sheet_h)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("см")
    ax.set_ylabel("см")
    ax.set_title("Схема раскладки (лист серый, изделия голубые, штриховка — отходы)")
    ax.grid(False)
    return fig, ax

def fmt_cm2(x: float) -> str:
    return f"{x:.2f} см²"

def main():
    st.title("Оптимальная раскладка прямоугольных изделий (гуилотинная)")
    st.markdown("Укажите размеры в сантиметрах, зазор — в миллиметрах.")

    col1, col2 = st.columns(2)
    with col1:
        sheet_w = st.number_input("Ширина листа, см", min_value=1.0, value=70.0, step=0.5)
        item_w = st.number_input("Ширина изделия, см", min_value=0.1, value=15.0, step=0.1)
    with col2:
        sheet_h = st.number_input("Высота листа, см", min_value=1.0, value=100.0, step=0.5)
        item_h = st.number_input("Высота изделия, см", min_value=0.1, value=20.0, step=0.1)

    gap_mm = st.number_input("Зазор между изделиями, мм", min_value=0.0, value=0.0, step=0.5)
    gap = gap_mm / 10.0  # convert to cm

    if st.button("Рассчитать раскладку"):
        # Build candidate plans
        plans = [
            build_pure(sheet_w, sheet_h, item_w, item_h, gap, is_A=True),
            build_pure(sheet_w, sheet_h, item_w, item_h, gap, is_A=False),
            build_mixed(sheet_w, sheet_h, item_w, item_h, gap, main_is_A=True),
            build_mixed(sheet_w, sheet_h, item_w, item_h, gap, main_is_A=False),
        ]
        best = choose_best(plans)

        fig, ax = draw_plan(best, sheet_w, sheet_h, gap)
        st.pyplot(fig, use_container_width=True)

        # Prepare PNG for download
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
        buf.seek(0)
        st.download_button("Скачать рисунок PNG", data=buf, file_name="layout.png", mime="image/png")

        # Metrics
        sheet_area = sheet_w * sheet_h
        items_area = best.used_area
        waste_area = max(0.0, sheet_area - items_area)
        waste_pct = 0.0 if sheet_area <= 0 else 100.0 * waste_area / sheet_area

        st.subheader("Результаты")
        st.markdown(f"- Выбранная схема: **{best.name}** — {best.description}")
        st.markdown(f"- Основной блок: {best.n_main_cols} по горизонтали × {best.n_main_rows} по вертикали")
        if best.name == "Смешанная":
            st.markdown(f"- Дополнительно: правая полоса {best.extras_right[0]}×{best.extras_right[1]}, нижняя полоса {best.extras_bottom[0]}×{best.extras_bottom[1]} (повёрнутые)")
        st.markdown(f"- Итого изделий на листе: **{best.total}**")
        st.markdown(f"- Площадь листа: {fmt_cm2(sheet_area)}")
        st.markdown(f"- Площадь изделий: {fmt_cm2(items_area)}")
        st.markdown(f"- Площадь отходов: {fmt_cm2(waste_area)} ({waste_pct:.1f}%)")

        tr = best.trims
        st.markdown(
            f"- Обрезки относительно основного блока:\n"
            f"  - Правый: {tr['right'][0]:.2f} × {tr['right'][1]:.2f} см\n"
            f"  - Нижний: {tr['bottom'][0]:.2f} × {tr['bottom'][1]:.2f} см\n"
            f"  - Угловой остаток: {tr['corner'][0]:.2f} × {tr['bottom'][1]:.2f} см"
        )

        st.caption("Примечание: ограничение гильотинной резки соблюдается — полосы справа/снизу формируются последовательностью сквозных резов.")
    else:
        st.info("Введите параметры и нажмите «Рассчитать раскладку».")

if __name__ == '__main__':
    main()
