import sys
import random
import math
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPoint
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QHeaderView, QGraphicsDropShadowEffect,
                             QAbstractItemView, QMessageBox, QFrame, QKeySequenceEdit)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath, QKeySequence

# 苹果莫兰迪色系精选（高级、低饱和度）
MORANDI_COLORS = [
    "#E2C0B6", "#B3C5D7", "#C2D3CD", "#DCE1DE", 
    "#E0CBD5", "#EADBC8", "#D3E4CD", "#ADC2A9",
    "#E8D3C9", "#CFD2CF", "#D0C993", "#A2B5CD"
]

class LuckyWheelWidget(QWidget):
    """超级大转盘绘制与核心动画组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.options = []          
        self.current_angle = 0.0      
        self.start_base_angle = 0.0   
        self.total_target_angle = 0.0 
        self.is_spinning = False    
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_physics_animation)
        self.elapsed_timer = QElapsedTimer()
        self.callback_on_finished = None
        
        self.center_point = QPoint(0, 0)
        self.center_axis_radius = 18
        
        # 内部记录鼠标拖动状态
        self.drag_position = QPoint()

    def set_options(self, data_list):
        total_weight = sum(item['weight'] for item in data_list)
        if total_weight <= 0:
            self.options = []
            self.update()
            return
        
        current_start = 0.0
        self.options = []
        for i, item in enumerate(data_list):
            weight_angle = 360.0 * (item['weight'] / total_weight)
            self.options.append({
                'name': item['name'],
                'weight_angle': weight_angle,
                'start_angle': current_start,
                'end_angle': current_start + weight_angle,
                'color': MORANDI_COLORS[i % len(MORANDI_COLORS)]
            })
            current_start += weight_angle
        self.update()

    def start_spin(self, winner_index, callback):
        if self.is_spinning or not self.options or winner_index >= len(self.options):
            return
        
        self.is_spinning = True
        self.callback_on_finished = callback
        self.start_base_angle = self.current_angle
        
        target_sector = self.options[winner_index]
        s_angle = target_sector['start_angle']
        e_angle = target_sector['end_angle']
        
        safe_margin = (e_angle - s_angle) * 0.15
        random_offset = random.uniform(s_angle + safe_margin, e_angle - safe_margin)
        absolute_dest_angle = 360.0 - random_offset
        
        turns = random.randint(22, 28)
        current_mod = self.start_base_angle % 360.0
        if absolute_dest_angle >= current_mod:
            angle_delta = absolute_dest_angle - current_mod
        else:
            angle_delta = 360.0 - current_mod + absolute_dest_angle
            
        self.total_target_angle = turns * 360.0 + angle_delta
        
        self.elapsed_timer.start()
        self.anim_timer.start(10)

    def update_physics_animation(self):
        elapsed_seconds = self.elapsed_timer.elapsed() / 1000.0
        T = 7.0  
        Theta = self.total_target_angle
        
        if elapsed_seconds >= T:
            self.current_angle = self.start_base_angle + Theta
            self.anim_timer.stop()
            self.is_spinning = False
            if self.callback_on_finished:
                self.callback_on_finished()
            self.update()
            return

        t = elapsed_seconds
        
        if t < 3.5:
            p = t / 3.5
            factor = (p ** 2) * 0.5
            self.current_angle = self.start_base_angle + Theta * (factor * (7.0 / 5.25))
        else:
            dt = t - 3.5
            p = dt / 3.5  
            
            angle_at_35s = Theta * (0.5 * (7.0 / 5.25))
            remaining_angle = Theta - angle_at_35s
            
            if p < (1.0 / 3.5):
                factor = 1.0 - math.pow(1.0 - p, 3.5)
            else:
                factor = 1.0 - math.pow(1.0 - p, 4.8)
            
            self.current_angle = self.start_base_angle + angle_at_35s + remaining_angle * factor
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        width = self.width()
        height = self.height()
        size = min(width, height) - 60
        rect = QRectF((width - size) / 2, (height - size) / 2 + 15, size, size)
        self.center_point = rect.center().toPoint()
        radius = size / 2

        if not self.options:
            painter.setPen(QPen(QColor("#E8E8ED"), 2))
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(rect)
            return

        # 1. 动态绘制各个概率扇形与文本
        for opt in self.options:
            qt_start = 90.0 - (opt['start_angle'] + self.current_angle)
            qt_span = -opt['weight_angle']
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(opt['color'])))
            painter.drawPie(rect, int(qt_start * 16), int(qt_span * 16))
            
            painter.save()
            mid_angle = opt['start_angle'] + opt['weight_angle'] / 2 + self.current_angle
            painter.translate(rect.center())
            painter.rotate(mid_angle - 90.0)
            
            painter.setPen(QPen(QColor("#1D1D1F")))
            font = QFont("PingFang SC", 12)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = QRectF(radius * 0.25, -15, radius * 0.6, 30)
            metrics = painter.fontMetrics()
            elided_text = metrics.elidedText(opt['name'], Qt.TextElideMode.ElideRight, int(text_rect.width()))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_text)
            painter.restore()

        # 2. 外部高光环
        painter.setPen(QPen(QColor("#FFFFFF"), 6))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        
        painter.setPen(QPen(QColor("#E8E8ED"), 1))
        painter.drawEllipse(rect)

        # 3. 中心黑轴（隐藏配置中心入口）
        painter.setPen(QPen(QColor("#FFFFFF"), 4))
        painter.setBrush(QBrush(QColor("#1D1D1F")))
        painter.drawEllipse(rect.center(), self.center_axis_radius, self.center_axis_radius)

        # 4. 顶部固定红色指针
        pointer_path = QPainterPath()
        pointer_top = rect.top()
        pointer_path.moveTo(width / 2 - 14, pointer_top - 18)
        pointer_path.lineTo(width / 2 + 14, pointer_top - 18)
        pointer_path.lineTo(width / 2, pointer_top + 16)
        pointer_path.closeSubpath()
        
        painter.setPen(QPen(QColor("#FFFFFF"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
        painter.setBrush(QBrush(QColor("#FF3B30")))
        painter.drawPath(pointer_path)

    def mousePressEvent(self, event):
        """核心交互重构：在实体的转盘画布上拦截并识别鼠标事件"""
        main_win = self.window()
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 1. 计算点击位置到黑色中心轴的物理距离
            distance = math.hypot(event.position().x() - self.center_point.x(), 
                                  event.position().y() - self.center_point.y())
            
            if distance <= self.center_axis_radius + 6: # 增加到6像素的微调宽容度
                # 点击黑轴：触发设置菜单
                if hasattr(main_win, 'toggle_settings_panel'):
                    main_win.toggle_settings_panel()
                event.accept()
                return
            else:
                # 点击转盘其他彩色区域：视为按住并准备拖动窗口
                self.drag_position = event.globalPosition().toPoint() - main_win.frameGeometry().topLeft()
                event.accept()
                
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键点击转盘：优雅关闭程序
            main_win.close()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理无边框窗口拖拽"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            main_win = self.window()
            # 只有当没有弹出设置面板时，才允许拖动主窗口
            if hasattr(main_win, 'settings_panel') and not main_win.settings_panel.isVisible():
                main_win.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("超级大转盘")
        self.resize(650, 680)  
        
        # 窗口完全无边框且全透明置顶
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint) 
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        self.trigger_shortcut = QKeySequence(Qt.Key.Key_Space) 
        self.init_ui()

    def init_ui(self):
        self.main_container = QWidget(self)
        self.main_container.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.main_container)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(40, 40, 40, 40)

        self.wheel_widget = LuckyWheelWidget()
        main_layout.addWidget(self.wheel_widget, stretch=1)

        # ==================== 隐藏式配置抽屉面板 ====================
        self.settings_panel = QFrame(self)
        self.settings_panel.setVisible(False)  
        self.settings_panel.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E8E8ED;
                border-radius: 16px;
            }
        """)
        
        panel_shadow = QGraphicsDropShadowEffect()
        panel_shadow.setBlurRadius(25)
        panel_shadow.setColor(QColor(0, 0, 0, 35))
        panel_shadow.setOffset(0, 8)
        self.settings_panel.setGraphicsEffect(panel_shadow)

        side_layout = QVBoxLayout(self.settings_panel)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        panel_title = QLabel("⚙️ 奖项配置中心")
        panel_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1D1D1F; background: transparent;")
        self.btn_close_panel = QPushButton("✕")
        self.btn_close_panel.setFixedSize(24, 24)
        self.btn_close_panel.setStyleSheet("border: none; font-size: 14px; color: #8E8E93; font-weight: bold; background: transparent;")
        self.btn_close_panel.clicked.connect(self.toggle_settings_panel)
        header_layout.addWidget(panel_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close_panel)
        side_layout.addLayout(header_layout)

        # 快捷键绑定组件
        shortcut_layout = QHBoxLayout()
        shortcut_label = QLabel("抽奖快捷键:")
        shortcut_label.setStyleSheet("font-size: 12px; color: #515154; font-weight: bold; background: transparent;")
        self.shortcut_editor = QKeySequenceEdit(self.trigger_shortcut)
        self.shortcut_editor.setStyleSheet("""
            QKeySequenceEdit {
                background-color: #F5F5F7;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 3px;
                font-size: 12px;
                color: #1D1D1F;
            }
        """)
        self.shortcut_editor.keySequenceChanged.connect(self.update_shortcut)
        shortcut_layout.addWidget(shortcut_label)
        shortcut_layout.addWidget(self.shortcut_editor)
        side_layout.addLayout(shortcut_layout)

        # 权重表格
        self.table = QTableWidget(6, 2)
        self.table.setHorizontalHeaderLabels(["选项名称", "权重(概率)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E8E8ED;
                border-radius: 8px;
                gridline-color: #F5F5F7;
                background-color: #FFFFFF;
                alternate-background-color: #FAFAFC;
            }
            QTableWidget::item { padding: 4px; color: #1D1D1F; font-size: 12px; }
            QHeaderView::section {
                background-color: #F5F5F7;
                border: none;
                font-weight: bold;
                color: #8E8E93;
                padding: 4px;
                font-size: 12px;
            }
        """)
        
        default_data = [
            ("iPhone 16 Pro", "10"),
            ("iPad Air", "20"),
            ("MacBook Air", "15"),
            ("AirPods 4", "30"),
            ("Apple Watch", "25"),
            ("谢谢参与", "50")
        ]
        for row, (name, val) in enumerate(default_data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(val))
        side_layout.addWidget(self.table)
        self.table.itemChanged.connect(self.sync_table_to_wheel)

        action_layout = QHBoxLayout()
        self.btn_add = QPushButton("+ 添加奖项")
        self.btn_del = QPushButton("- 删除选中")
        sub_btn_qss = """
            QPushButton {
                background-color: #F5F5F7; color: #1D1D1F;
                border: 1px solid #D2D2D7; border-radius: 6px;
                padding: 6px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E8E8ED; }
        """
        self.btn_add.setStyleSheet(sub_btn_qss)
        self.btn_del.setStyleSheet(sub_btn_qss)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.delete_row)
        action_layout.addWidget(self.btn_add)
        action_layout.addWidget(self.btn_del)
        side_layout.addLayout(action_layout)

        self.sync_table_to_wheel()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 弹窗保持在主转盘内的黄金悬浮位置
        self.settings_panel.setGeometry(40, 50, 310, 400)

    def toggle_settings_panel(self):
        if self.wheel_widget.is_spinning:
            return 
        self.settings_panel.setVisible(not self.settings_panel.isVisible())
        if self.settings_panel.isVisible():
            self.settings_panel.raise_()  

    def update_shortcut(self, key_sequence):
        self.trigger_shortcut = key_sequence

    def keyPressEvent(self, event):
        """键盘全局监控快捷键抽奖"""
        if not self.wheel_widget.is_spinning and not self.settings_panel.isVisible():
            current_key_seq = QKeySequence(event.key() if event.modifiers() == Qt.KeyboardModifier.NoModifier else event.modifiers() | event.key())
            if event.key() == Qt.Key.Key_Space and self.trigger_shortcut.toString() == "Space":
                self.execute_lucky_draw()
                return
            elif current_key_seq.toString() == self.trigger_shortcut.toString():
                self.execute_lucky_draw()
                return
        super().keyPressEvent(event)

    def sync_table_to_wheel(self):
        data_list = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            weight_item = self.table.item(row, 1)
            name = name_item.text().strip() if name_item else ""
            if not name: continue
            try:
                weight = float(weight_item.text().strip()) if weight_item else 0.0
                if weight <= 0: continue
            except ValueError: continue
            data_list.append({'name': name, 'weight': weight})
        self.wheel_widget.set_options(data_list)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(f"新奖项 {row+1}"))
        self.table.setItem(row, 1, QTableWidgetItem("10"))

    def delete_row(self):
        curr_row = self.table.currentRow()
        if curr_row >= 0:
            self.table.removeRow(curr_row)
            self.sync_table_to_wheel()

    def execute_lucky_draw(self):
        options = self.wheel_widget.options
        if not options: return
        self.settings_panel.setVisible(False) 
        weights = [opt['weight_angle'] for opt in options]
        winner_index = random.choices(range(len(options)), weights=weights, k=1)[0]
        self.wheel_widget.start_spin(winner_index, self.on_draw_animation_complete)

    def on_draw_animation_complete(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())