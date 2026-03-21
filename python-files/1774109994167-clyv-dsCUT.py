import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import numpy as np
from io import BytesIO

# Настройка страницы
st.set_page_config(
    page_title="Оптимальная раскладка для типографии",
    page_icon="📐",
    layout="wide"
)

st.title("📐 Оптимальная раскладка изделий на листе")
st.markdown("---")

# Боковая панель с вводом данных
with st.sidebar:
    st.header("📏 Параметры листа")
    sheet_width = st.number_input("Ширина листа (см)", min_value=1.0, value=70.0, step=1.0, format="%.1f")
    sheet_height = st.number_input("Высота листа (см)", min_value=1.0, value=100.0, step=1.0, format="%.1f")
    
    st.header("📦 Параметры изделия")
    item_width = st.number_input("Ширина изделия (см)", min_value=0.1, value=15.0, step=1.0, format="%.1f")
    item_height = st.number_input("Высота изделия (см)", min_value=0.1, value=20.0, step=1.0, format="%.1f")
    
    st.header("⚙️ Дополнительно")
    gap_mm = st.number_input("Зазор между изделиями (мм)", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    gap_cm = gap_mm / 10  # перевод в сантиметры
    
    st.markdown("---")
    st.caption("Алгоритм учитывает гильотинную резку (только ряды и колонки)")

# Функция для расчёта раскладки в одной ориентации
def calculate_layout_simple(sheet_w, sheet_h, item_w, item_h, gap):
    """Простая раскладка без поворота"""
    item_w_total = item_w + gap
    item_h_total = item_h + gap
    
    cols = int(sheet_w // item_w_total)
    rows = int(sheet_h // item_h_total)
    
    # Корректировка, если зазор добавляется после последнего изделия
    if cols > 0 and gap > 0:
        total_width = cols * item_w + (cols - 1) * gap
        if total_width > sheet_w:
            cols -= 1
    
    if rows > 0 and gap > 0:
        total_height = rows * item_h + (rows - 1) * gap
        if total_height > sheet_h:
            rows -= 1
    
    total_items = cols * rows
    
    return {
        'cols': cols,
        'rows': rows,
        'total': total_items,
        'item_w': item_w,
        'item_h': item_h,
        'orientation': 'А'
    }

# Функция для расчёта раскладки с поворотом на 90°
def calculate_layout_rotated(sheet_w, sheet_h, item_w, item_h, gap):
    """Раскладка с поворотом изделия на 90°"""
    return calculate_layout_simple(sheet_w, sheet_h, item_h, item_w, gap)

# Функция для смешанной раскладки
def calculate_layout_mixed(sheet_w, sheet_h, item_w, item_h, gap):
    """Смешанная раскладка: основной блок + дополнительные в оставшемся пространстве"""
    
    item_w_total = item_w + gap
    item_h_total = item_h + gap
    
    # Основной блок в ориентации А
    cols_main = int(sheet_w // item_w_total)
    rows_main = int(sheet_h // item_h_total)
    
    if cols_main == 0 or rows_main == 0:
        return {'total': 0, 'items': []}
    
    # Корректировка с учётом зазора
    if gap > 0:
        total_width_main = cols_main * item_w + (cols_main - 1) * gap
        if total_width_main > sheet_w:
            cols_main -= 1
        total_height_main = rows_main * item_h + (rows_main - 1) * gap
        if total_height_main > sheet_h:
            rows_main -= 1
    
    total_main = cols_main * rows_main
    
    # Оставшееся пространство справа
    right_space_w = sheet_w - (cols_main * item_w + max(0, cols_main - 1) * gap)
    right_space_h = sheet_h
    
    # Оставшееся пространство снизу
    bottom_space_w = sheet_w
    bottom_space_h = sheet_h - (rows_main * item_h + max(0, rows_main - 1) * gap)
    
    # Пытаемся разместить дополнительные изделия в правой полосе (повёрнутые)
    right_items = []
    if right_space_w >= min(item_w, item_h) and right_space_h >= min(item_w, item_h):
        # Пробуем разместить в правой полосе повёрнутые изделия
        if right_space_w >= item_h + gap and right_space_h >= item_w + gap:
            cols_right = int(right_space_w // (item_h + gap))
            rows_right = int(right_space_h // (item_w + gap))
            
            if gap > 0:
                total_width_right = cols_right * item_h + (cols_right - 1) * gap
                if total_width_right > right_space_w:
                    cols_right -= 1
                total_height_right = rows_right * item_w + (rows_right - 1) * gap
                if total_height_right > right_space_h:
                    rows_right -= 1
            
            if cols_right > 0 and rows_right > 0:
                right_items = [{'col': c, 'row': r, 'rotated': True} 
                              for r in range(rows_right) for c in range(cols_right)]
    
    # Пытаемся разместить дополнительные изделия в нижней полосе (повёрнутые)
    bottom_items = []
    if bottom_space_w >= min(item_w, item_h) and bottom_space_h >= min(item_w, item_h):
        if bottom_space_w >= item_h + gap and bottom_space_h >= item_w + gap:
            cols_bottom = int(bottom_space_w // (item_h + gap))
            rows_bottom = int(bottom_space_h // (item_w + gap))
            
            if gap > 0:
                total_width_bottom = cols_bottom * item_h + (cols_bottom - 1) * gap
                if total_width_bottom > bottom_space_w:
                    cols_bottom -= 1
                total_height_bottom = rows_bottom * item_w + (rows_bottom - 1) * gap
                if total_height_bottom > bottom_space_h:
                    rows_bottom -= 1
            
            if cols_bottom > 0 and rows_bottom > 0:
                bottom_items = [{'col': c, 'row': r, 'rotated': True, 'position': 'bottom'} 
                               for r in range(rows_bottom) for c in range(cols_bottom)]
    
    # Создаём список всех изделий
    items = []
    
    # Основные изделия (ориентация А)
    for row in range(rows_main):
        for col in range(cols_main):
            x = col * (item_w + gap)
            y = row * (item_h + gap)
            items.append({
                'x': x, 'y': y, 'w': item_w, 'h': item_h,
                'rotated': False, 'type': 'main'
            })
    
    # Добавляем изделия из правой полосы
    for i, item in enumerate(right_items):
        col_idx = item['col']
        row_idx = item['row']
        x = cols_main * (item_w + gap) + col_idx * (item_h + gap)
        y = row_idx * (item_w + gap)
        items.append({
            'x': x, 'y': y, 'w': item_h, 'h': item_w,
            'rotated': True, 'type': 'right'
        })
    
    # Добавляем изделия из нижней полосы
    for i, item in enumerate(bottom_items):
        col_idx = item['col']
        row_idx = item['row']
        x = col_idx * (item_h + gap)
        y = rows_main * (item_h + gap) + row_idx * (item_w + gap)
        items.append({
            'x': x, 'y': y, 'w': item_h, 'h': item_w,
            'rotated': True, 'type': 'bottom'
        })
    
    return {
        'total': len(items),
        'items': items,
        'cols_main': cols_main,
        'rows_main': rows_main,
        'gap': gap
    }

# Функция для визуализации
def visualize_layout(sheet_w, sheet_h, layout_data, item_w, item_h, gap):
    """Визуализация раскладки"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Рисуем лист
    sheet_rect = Rectangle((0, 0), sheet_w, sheet_h, 
                           facecolor='lightgray', edgecolor='black', 
                           linewidth=2, alpha=0.3)
    ax.add_patch(sheet_rect)
    
    # Рисуем изделия
    if 'items' in layout_data:  # Смешанная раскладка
        for item in layout_data['items']:
            rect = Rectangle((item['x'], item['y']), item['w'], item['h'],
                           facecolor='lightblue', edgecolor='blue', 
                           linewidth=1.5, alpha=0.7)
            ax.add_patch(rect)
            
            # Подпись
            if item['rotated']:
                label = f"{item['h']}x{item['w']}"
            else:
                label = f"{item['w']}x{item['h']}"
            ax.text(item['x'] + item['w']/2, item['y'] + item['h']/2, label,
                   ha='center', va='center', fontsize=8)
    else:  # Простая раскладка
        cols = layout_data['cols']
        rows = layout_data['rows']
        item_w_actual = layout_data['item_w']
        item_h_actual = layout_data['item_h']
        
        for row in range(rows):
            for col in range(cols):
                x = col * (item_w_actual + gap)
                y = row * (item_h_actual + gap)
                rect = Rectangle((x, y), item_w_actual, item_h_actual,
                               facecolor='lightblue', edgecolor='blue', 
                               linewidth=1.5, alpha=0.7)
                ax.add_patch(rect)
                ax.text(x + item_w_actual/2, y + item_h_actual/2, 
                       f"{item_w_actual}x{item_h_actual}",
                       ha='center', va='center', fontsize=8)
    
    # Отмечаем отходы штриховкой
    if 'items' in layout_data and layout_data['items']:
        # Находим максимальную занятую область
        max_x = max([item['x'] + item['w'] for item in layout_data['items']])
        max_y = max([item['y'] + item['h'] for item in layout_data['items']])
        
        if max_x < sheet_w:
            waste_rect = Rectangle((max_x, 0), sheet_w - max_x, sheet_h,
                                 facecolor='red', edgecolor='red', 
                                 alpha=0.2, hatch='//')
            ax.add_patch(waste_rect)
        
        if max_y < sheet_h:
            waste_rect = Rectangle((0, max_y), sheet_w, sheet_h - max_y,
                                 facecolor='red', edgecolor='red', 
                                 alpha=0.2, hatch='//')
            ax.add_patch(waste_rect)
    else:
        # Для простой раскладки
        cols = layout_data['cols']
        rows = layout_data['rows']
        used_width = cols * layout_data['item_w'] + max(0, cols - 1) * gap
        used_height = rows * layout_data['item_h'] + max(0, rows - 1) * gap
        
        if used_width < sheet_w:
            waste_rect = Rectangle((used_width, 0), sheet_w - used_width, sheet_h,
                                 facecolor='red', edgecolor='red', 
                                 alpha=0.2, hatch='//')
            ax.add_patch(waste_rect)
        
        if used_height < sheet_h:
            waste_rect = Rectangle((0, used_height), sheet_w, sheet_h - used_height,
                                 facecolor='red', edgecolor='red', 
                                 alpha=0.2, hatch='//')
            ax.add_patch(waste_rect)
    
    ax.set_xlim(0, sheet_w)
    ax.set_ylim(0, sheet_h)
    ax.set_aspect('equal')
    ax.set_xlabel('Ширина (см)', fontsize=10)
    ax.set_ylabel('Высота (см)', fontsize=10)
    ax.set_title('Схема раскладки изделий на листе', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    return fig

# Основная логика
if st.sidebar.button("🚀 Рассчитать оптимальную раскладку", type="primary"):
    # Расчёт всех вариантов
    layout_a = calculate_layout_simple(sheet_width, sheet_height, item_width, item_height, gap_cm)
    layout_b = calculate_layout_rotated(sheet_width, sheet_height, item_width, item_height, gap_cm)
    layout_mixed = calculate_layout_mixed(sheet_width, sheet_height, item_width, item_height, gap_cm)
    
    # Выбор лучшего варианта
    best_layout = None
    best_type = ""
    max_items = 0
    
    if layout_a['total'] > max_items:
        max_items = layout_a['total']
        best_layout = layout_a
        best_type = "А (стандартная)"
    
    if layout_b['total'] > max_items:
        max_items = layout_b['total']
        best_layout = layout_b
        best_type = "Б (повёрнутая на 90°)"
    
    if layout_mixed['total'] > max_items:
        max_items = layout_mixed['total']
        best_layout = layout_mixed
        best_type = "Смешанная"
    
    # Отображение результатов
    if best_layout:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Схема раскладки")
            fig = visualize_layout(sheet_width, sheet_height, best_layout, 
                                  item_width, item_height, gap_cm)
            st.pyplot(fig)
            
            # Кнопка скачивания
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            st.download_button(
                label="📥 Скачать рисунок PNG",
                data=buf,
                file_name="layout.png",
                mime="image/png"
            )
        
        with col2:
            st.subheader("📈 Результаты раскладки")
            
            st.markdown(f"**Выбранная схема:** {best_type}")
            
            if best_type == "Смешанная":
                st.markdown(f"**Основной блок:** {best_layout['cols_main']} × {best_layout['rows_main']}")
                st.markdown(f"**Дополнительные изделия:** {best_layout['total'] - best_layout['cols_main'] * best_layout['rows_main']} шт.")
            else:
                st.markdown(f"**Количество по горизонтали:** {best_layout['cols']}")
                st.markdown(f"**Количество по вертикали:** {best_layout['rows']}")
            
            st.markdown(f"**Всего изделий на листе:** **{best_layout['total']}** шт.")
            
            # Расчёт площадей
            sheet_area = sheet_width * sheet_height
            items_area = best_layout['total'] * item_width * item_height
            waste_area = sheet_area - items_area
            waste_percent = (waste_area / sheet_area) * 100
            
            st.markdown("---")
            st.markdown("**Площади:**")
            st.markdown(f"• Площадь листа: **{sheet_area:.1f} см²**")
            st.markdown(f"• Площадь изделий: **{items_area:.1f} см²**")
            st.markdown(f"• Площадь отходов: **{waste_area:.1f} см²** ({waste_percent:.1f}%)")
            
            # Расчёт обрезков
            if best_type == "Смешанная" and best_layout['items']:
                max_x = max([item['x'] + item['w'] for item in best_layout['items']])
                max_y = max([item['y'] + item['h'] for item in best_layout['items']])
                right_waste = sheet_width - max_x
                bottom_waste = sheet_height - max_y
                corner_waste = right_waste * bottom_waste
                
                st.markdown("---")
                st.markdown("**Размеры обрезков:**")
                st.markdown(f"• Правый обрезок: {right_waste:.1f} × {sheet_height:.1f} см")
                st.markdown(f"• Нижний обрезок: {sheet_width:.1f} × {bottom_waste:.1f} см")
                st.markdown(f"• Угловой остаток: {right_waste:.1f} × {bottom_waste:.1f} см ({corner_waste:.1f} см²)")
            else:
                used_width = best_layout['cols'] * best_layout['item_w'] + max(0, best_layout['cols'] - 1) * gap_cm
                used_height = best_layout['rows'] * best_layout['item_h'] + max(0, best_layout['rows'] - 1) * gap_cm
                right_waste = sheet_width - used_width
                bottom_waste = sheet_height - used_height
                corner_waste = right_waste * bottom_waste
                
                st.markdown("---")
                st.markdown("**Размеры обрезков:**")
                st.markdown(f"• Правый обрезок: {right_waste:.1f} × {sheet_height:.1f} см")
                st.markdown(f"• Нижний обрезок: {sheet_width:.1f} × {bottom_waste:.1f} см")
                st.markdown(f"• Угловой остаток: {right_waste:.1f} × {bottom_waste:.1f} см ({corner_waste:.1f} см²)")
    else:
        st.error("Не удалось разместить ни одного изделия. Проверьте размеры!")

else:
    st.info("👈 Введите параметры в боковой панели и нажмите кнопку «Рассчитать оптимальную раскладку»")
    
    # Пример
    with st.expander("ℹ️ Пример использования"):
        st.markdown("""
        **Пример:**  
        - Лист: 70 × 100 см  
        - Изделие: 15 × 20 см  
        - Зазор: 0 мм
        
        Алгоритм проверит:
        1. Стандартную ориентацию
        2. Повёрнутую ориентацию
        3. Смешанную раскладку (основной блок + дополнительные в оставшемся пространстве)
        
        Выберет вариант с максимальным количеством изделий.
        """)