import sys
import sys
import os
import json
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QMenu, QColorDialog, QFontDialog, QSpacerItem, QSizePolicy,
                             QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QSystemTrayIcon, QAction)
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize, QRect, QTranslator, QLibraryInfo
from PyQt5.QtGui import QFont, QFontMetrics, QColor, QPainter, QMouseEvent, QPaintEvent, QResizeEvent, QIcon, QPixmap, QPen

# ==============================================================================
# 强制唤醒最高级别的高分屏支持与抗锯齿
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# 全局常量配置
UI_FONT = 'Microsoft YaHei' # UI 界面默认使用微软雅黑，兼容性最好
DEFAULT_CONFIG: Dict[str, Any] = {
    "geometry": "400x180+500+300", 
    "pinned": True,
    "text_color": "#FFFFFF",       
    "font_family": "Arial",        
    "show_hours": True,
    "show_date": True,             
    "show_shadow": True,           # 【新增】默认开启文字阴影
    "minimal_mode": False
}
# ==============================================================================

def get_config_path() -> Path:
    """获取配置文件路径并确保目录存在"""
    if sys.platform == "win32":
        config_dir = Path(os.getenv('APPDATA', '~')) / 'TransparentClock'
    else:
        config_dir = Path.home() / '.transparent_clock'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'clock_config.json'

CONFIG_FILE: Path = get_config_path()

# ================= 终极翻译器 (解决环境翻译包丢失问题) =================
class UIRepairTranslator(QTranslator):
    """
    底层文字拦截翻译器：
    专门解决通过 pip 安装的 PyQt5 缺失官方 qtbase_zh_CN.qm 翻译包的问题。
    将原生 QColorDialog 和 QFontDialog 中的硬编码英文强制映射为中文。
    """
    def translate(self, context: str, sourceText: str, disambiguation: Optional[str] = None, n: int = -1) -> str:
        if not sourceText:
            return super().translate(context, sourceText, disambiguation, n)

        mapping = {
            "Basic colors": "基本颜色",
            "Custom colors": "自定义颜色",
            "Add to Custom Colors": "添加到自定义颜色",
            "Pick Screen Color": "拾取屏幕颜色",
            "OK": "确定",
            "Cancel": "取消",
            "Font": "字体",
            "Font style": "字体样式",
            "Size": "大小",
            "Effects": "效果",
            "Strikeout": "删除线",
            "Underline": "下划线",
            "Sample": "示例",
            "Writing System": "书写系统",
            "Any": "任意",
            "Regular": "常规",
            "Bold": "粗体",
            "Italic": "斜体",
            "Bold Italic": "粗斜体",
            "Light": "细体",
            "Hue": "色调",
            "Sat": "饱和度",
            "Val": "亮度",
            "Red": "红",
            "Green": "绿",
            "Blue": "蓝",
            "HTML": "HTML代码"
        }

        # 去除 Qt 快捷键符号 '&'
        clean_text = sourceText.replace('&', '')

        if clean_text in mapping:
            return mapping[clean_text]

        # 智能处理带冒号的标签 (如 "Hue:")
        if clean_text.endswith(':') and clean_text[:-1] in mapping:
            return mapping[clean_text[:-1]] + ":"

        return super().translate(context, sourceText, disambiguation, n)


# ================= 自定义 UI 组件 =================

def create_text_shadow(blur_radius: int = 8, offset_x: int = 2, offset_y: int = 2) -> QGraphicsDropShadowEffect:
    """生成文字阴影，防止在浅色壁纸下文字看不清"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setColor(QColor(0, 0, 0, 180)) 
    shadow.setOffset(offset_x, offset_y)
    return shadow

class ResizeHandle(QLabel):
    """右下角的无边界缩放手柄"""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__('⤡', parent)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.resizing: bool = False
        self.start_pos: QPoint = QPoint()
        self.start_size: QSize = QSize()
        self._update_style("#AAAAAA")

    def _update_style(self, color: str) -> None:
        self.setStyleSheet(f"color: {color}; font-family: '{UI_FONT}'; font-size: 14pt;")

    def enterEvent(self, event: Any) -> None:
        super().enterEvent(event)
        self._update_style("#FFFFFF")

    def leaveEvent(self, event: Any) -> None:
        super().leaveEvent(event)
        self._update_style("#AAAAAA")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.resizing = True
            self.start_pos = event.globalPos()
            if self.window():
                self.start_size = self.window().size()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.resizing and event.buttons() & Qt.LeftButton and self.window():
            delta = event.globalPos() - self.start_pos
            new_w = max(self.window().minimumWidth(), self.start_size.width() + delta.x())
            new_h = max(self.window().minimumHeight(), self.start_size.height() + delta.y())
            self.window().resize(new_w, new_h)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.resizing = False

class PinButton(QLabel):
    """图钉按钮"""
    def __init__(self, is_pinned: bool, parent: Optional[QWidget] = None) -> None:
        super().__init__('📌', parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"font-family: 'Segoe UI Emoji'; font-size: 14pt;") 

        self.op_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.op_effect)
        self.is_pinned: bool = is_pinned
        self.set_pinned(is_pinned)

    def set_pinned(self, is_pinned: bool) -> None:
        self.is_pinned = is_pinned
        self.op_effect.setOpacity(1.0 if is_pinned else 0.3)
        self.setToolTip("当前状态：已置顶\n点击解除置顶" if is_pinned else "当前状态：未置顶\n点击置顶在最前")

    def enterEvent(self, event: Any) -> None:
        super().enterEvent(event)
        self.op_effect.setOpacity(0.8 if self.is_pinned else 0.6)

    def leaveEvent(self, event: Any) -> None:
        super().leaveEvent(event)
        self.op_effect.setOpacity(1.0 if self.is_pinned else 0.3)

class ControlButton(QLabel):
    """通用状态控制按钮"""
    def __init__(self, text: str, normal_color: str, hover_color: str, font_size: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.font_size = font_size
        self._update_style(self.normal_color)

    def _update_style(self, color: str) -> None:
        self.setStyleSheet(f"color: {color}; font-family: '{UI_FONT}'; font-size: {self.font_size}pt; font-weight: bold;")

    def enterEvent(self, event: Any) -> None:
        super().enterEvent(event)
        self._update_style(self.hover_color)

    def leaveEvent(self, event: Any) -> None:
        super().leaveEvent(event)
        self._update_style(self.normal_color)


# ================= 主窗口 =================

class TransparentClock(QWidget):
    def __init__(self) -> None:
        super().__init__()

        # --- 1. 状态初始化 ---
        self.config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load_config()
        self.moving: bool = False
        self.ghost_mode_active: bool = False 
        self.drag_pos: QPoint = QPoint()
        self.current_time_str: str = ""
        self.current_date_str: str = ""
        self.last_label_size: QSize = QSize()
        self.last_toggle_time: float = 0.0

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._do_save_config)

        # 字体引擎初始化
        self._work_time_font = QFont(self.config["font_family"], 10, QFont.Bold)
        self._work_date_font = QFont(self.config["font_family"], 10, QFont.Medium)

        # --- 2. 窗口基础设置 ---
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- 3. UI 布局与托盘 ---
        self.init_ui()
        self.init_system_tray()

        self.update_window_flags()
        self.apply_minimal_mode(init=True)

        self.apply_saved_geometry()
        self.ensure_on_screen()

        # --- 4. 启动定时器 ---
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_time_loop)
        self.clock_timer.start(100) 

        self.show()

    def update_window_flags(self) -> None:
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.ghost_mode_active:
            flags |= Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput
        else:
            if self.config["pinned"]:
                flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def init_system_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(40, 44, 52))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        painter.setPen(QPen(Qt.white, 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(32, 32, 32, 14)
        painter.drawLine(32, 32, 48, 32)
        painter.end()

        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("透明桌面时钟")

        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"QMenu {{ font-family: '{UI_FONT}'; font-size: 10pt; }}")

        self.action_toggle_ghost_tray = tray_menu.addAction("👻 关闭幽灵穿透模式")
        self.action_toggle_ghost_tray.triggered.connect(self.toggle_ghost_mode)
        self.action_toggle_ghost_tray.setVisible(False) 

        tray_menu.addSeparator()
        action_quit = tray_menu.addAction("❌ 退出时钟")
        action_quit.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def load_config(self) -> None:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                print(f"配置加载异常: {e}")

    def save_config_deferred(self) -> None:
        self.save_timer.start(500)

    def save_config_immediate(self) -> None:
        self.save_timer.stop()
        self._do_save_config()

    def _do_save_config(self) -> None:
        self.config["geometry"] = f"{self.width()}x{self.height()}+{self.x()}+{self.y()}"
        try:
            tmp_file = CONFIG_FILE.with_suffix('.tmp')
            with open(tmp_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno()) 
            tmp_file.replace(CONFIG_FILE)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def apply_saved_geometry(self) -> None:
        geo_str = str(self.config.get("geometry", "400x180+500+300"))
        m = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geo_str)
        if m:
            w, h, x, y = map(int, m.groups())
            self.setGeometry(x, y, w, h)

    def ensure_on_screen(self) -> None:
        desktop = QApplication.desktop()
        if desktop.screenNumber(self.geometry().center()) == -1:
            primary_geo = desktop.availableGeometry(desktop.primaryScreen())
            new_x = primary_geo.center().x() - self.width() // 2
            new_y = primary_geo.center().y() - self.height() // 2
            self.move(new_x, new_y)

    def closeEvent(self, event: Any) -> None:
        self.save_config_immediate()
        event.accept()

    def init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ============= 顶部控制栏 =============
        self.top_widget = QWidget(self)
        self.top_widget.setFixedHeight(28) 
        self.top_layout = QHBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(0, 2, 12, 0)
        self.top_layout.setSpacing(10)
        self.top_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.pin_btn = PinButton(bool(self.config["pinned"]), self)
        self.pin_btn.mousePressEvent = self.toggle_pin # type: ignore
        self.top_layout.addWidget(self.pin_btn)

        self.close_btn = ControlButton('✕', '#FF5555', 'red', 14, self)
        self.close_btn.setToolTip("退出时钟")
        self.close_btn.mousePressEvent = self.quit_app # type: ignore
        self.top_layout.addWidget(self.close_btn)
        self.main_layout.addWidget(self.top_widget)

        # ============= 核心：时钟与日期显示区 =============
        self.center_widget = QWidget(self)
        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)

        self.time_label = QLabel("00:00", self)
        self.time_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.time_label.setStyleSheet(f"color: {self.config['text_color']};")
        self.center_layout.addWidget(self.time_label)

        self.date_label = QLabel("2024年1月1日 星期一", self)
        self.date_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop) 
        self.date_label.setStyleSheet(f"color: {self.config['text_color']};")
        self.date_label.setVisible(self.config["show_date"])
        self.center_layout.addWidget(self.date_label)

        self.main_layout.addWidget(self.center_widget)

        # ============= 底部缩放栏 =============
        self.bottom_widget = QWidget(self)
        self.bottom_widget.setFixedHeight(22) 
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.bottom_layout.setContentsMargins(0, 0, 5, 2)
        self.bottom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.resize_handle = ResizeHandle(self)
        self.bottom_layout.addWidget(self.resize_handle)
        self.main_layout.addWidget(self.bottom_widget)

        # 【新增】应用阴影配置
        self.apply_shadow_settings()

    def apply_shadow_settings(self) -> None:
        """根据配置为文字和控件动态附加或移除阴影效果"""
        if self.config.get("show_shadow", True):
            self.time_label.setGraphicsEffect(create_text_shadow(10, 2, 2))
            self.date_label.setGraphicsEffect(create_text_shadow(6, 1, 1))
            self.resize_handle.setGraphicsEffect(create_text_shadow(4, 1, 1))
        else:
            self.time_label.setGraphicsEffect(None)
            self.date_label.setGraphicsEffect(None)
            self.resize_handle.setGraphicsEffect(None)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255, 1)) 

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.moving = True
            self.drag_pos = event.globalPos() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.moving and (event.buttons() & Qt.LeftButton):
            new_pos = event.globalPos() - self.drag_pos

            desktop_geo = QApplication.desktop().availableGeometry(self)
            snap_dist = 20

            if abs(new_pos.x() - desktop_geo.left()) < snap_dist:
                new_pos.setX(desktop_geo.left())
            elif abs(new_pos.x() + self.width() - desktop_geo.right()) < snap_dist:
                new_pos.setX(desktop_geo.right() - self.width())

            if abs(new_pos.y() - desktop_geo.top()) < snap_dist:
                new_pos.setY(desktop_geo.top())
            elif abs(new_pos.y() + self.height() - desktop_geo.bottom()) < snap_dist:
                new_pos.setY(desktop_geo.bottom() - self.height())

            self.move(new_pos)
            self.save_config_deferred()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.moving = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle_minimal_mode()
            event.accept()

    def wheelEvent(self, event: Any) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = 1.1 if delta > 0 else 0.9
        new_w = int(self.width() * factor)
        new_h = int(self.height() * factor)

        new_w = max(self.minimumWidth(), min(new_w, 2000))
        new_h = max(self.minimumHeight(), min(new_h, 1000))

        self.resize(new_w, new_h)
        self.save_config_deferred()
        event.accept()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.adjust_font_size()
        self.save_config_deferred()

    # --- 右键菜单与业务逻辑 ---
    def contextMenuEvent(self, event: Any) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ font-family: '{UI_FONT}'; font-size: 10pt; }}")

        action_color = menu.addAction("🎨 更改文字颜色...")
        action_font = menu.addAction("🅰️ 更改文字字体...")

        # 【新增】文字阴影切换菜单项
        action_shadow = menu.addAction("🌘 关闭文字阴影" if self.config.get("show_shadow", True) else "🌒 开启文字阴影")
        menu.addSeparator()

        action_hours = menu.addAction("⏱️ 隐藏时数" if self.config.get("show_hours", True) else "⏱️ 显示时数")
        action_date = menu.addAction("📅 隐藏日期" if self.config.get("show_date", True) else "📅 显示日期")
        action_minimal = menu.addAction("🖥️ 极简模式 (双击也可切换/滚轮可缩放)")
        menu.addSeparator()

        action_ghost = menu.addAction("👻 开启幽灵穿透 (鼠标完全穿过时钟)")
        menu.addSeparator()

        action_quit = menu.addAction("❌ 退出时钟")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == action_color: self.change_color()
        elif action == action_font: self.change_font()
        elif action == action_shadow: self.toggle_shadow()
        elif action == action_hours: self.toggle_hours()
        elif action == action_date: self.toggle_date()
        elif action == action_minimal: self.toggle_minimal_mode()
        elif action == action_ghost: self.toggle_ghost_mode()
        elif action == action_quit: self.quit_app()

    def change_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.config["text_color"]), self, "选择时钟颜色")
        if color.isValid():
            self.config["text_color"] = color.name()
            self.time_label.setStyleSheet(f"color: {self.config['text_color']};")
            self.date_label.setStyleSheet(f"color: {self.config['text_color']};")
            self.save_config_immediate()

    def change_font(self) -> None:
        current_font = QFont(self.config["font_family"])
        font, ok = QFontDialog.getFont(current_font, self, "选择时钟字体")
        if ok:
            self.config["font_family"] = font.family()
            self._work_time_font.setFamily(font.family())
            self._work_date_font.setFamily(font.family())
            self.last_label_size = QSize() 
            self.adjust_font_size()
            self.save_config_immediate()

    def toggle_shadow(self) -> None:
        """【新增】切换阴影状态"""
        self.config["show_shadow"] = not bool(self.config.get("show_shadow", True))
        self.apply_shadow_settings()
        self.save_config_immediate()

    def toggle_hours(self) -> None:
        self.config["show_hours"] = not bool(self.config.get("show_hours", True))
        self.current_time_str = "" 
        self.last_label_size = QSize() 
        self.adjust_font_size()
        self.save_config_immediate()

    def toggle_date(self) -> None:
        self.config["show_date"] = not bool(self.config.get("show_date", True))
        self.date_label.setVisible(self.config["show_date"])
        self.last_label_size = QSize() 
        self.adjust_font_size()
        self.save_config_immediate()

    def toggle_ghost_mode(self) -> None:
        self.ghost_mode_active = not self.ghost_mode_active
        geo = self.geometry()
        self.update_window_flags()
        self.setGeometry(geo) 

        self.action_toggle_ghost_tray.setVisible(self.ghost_mode_active)
        if self.ghost_mode_active:
            self.tray_icon.showMessage(
                "👻 幽灵模式已开启", 
                "时钟现已置顶且鼠标将直接穿透它。\n如需恢复正常拖拽，请右键点击电脑右下角的时钟托盘图标。", 
                QSystemTrayIcon.Information, 
                5000
            )

    def toggle_minimal_mode(self) -> None:
        self.config["minimal_mode"] = not bool(self.config["minimal_mode"])
        self.apply_minimal_mode()
        self.save_config_immediate()

    def apply_minimal_mode(self, init: bool = False) -> None:
        if self.config["minimal_mode"]:
            self.top_widget.hide()
            self.bottom_widget.hide()
            self.setMinimumSize(10, 10)
            if not init:
                self.resize(max(10, self.width()), max(10, self.height() - 50))
        else:
            self.top_widget.show()
            self.bottom_widget.show()
            self.setMinimumSize(60, 40)
            if not init:
                self.resize(max(60, self.width()), self.height() + 50)

    # --- 核心排版引擎 ---
    def adjust_font_size(self) -> None:
        if not hasattr(self, 'center_widget'):
            return

        current_size = self.center_widget.size()
        if current_size == self.last_label_size or current_size.width() <= 1 or current_size.height() <= 1:
            return
        self.last_label_size = current_size

        w, h = current_size.width(), current_size.height()
        show_date = self.config["show_date"]

        time_max_h = h * 0.70 if show_date else h * 0.95
        time_max_w = w * 0.95

        sample_time = '00:00:00' if self.config.get("show_hours", True) else '00:00'

        low, high, best_time_size = 1, 400, 1
        while low <= high:
            mid = (low + high) // 2
            self._work_time_font.setPointSize(mid)
            fm = QFontMetrics(self._work_time_font)
            rect = fm.boundingRect(sample_time)

            if rect.width() <= time_max_w and rect.height() <= time_max_h:
                best_time_size = mid
                low = mid + 1
            else:
                high = mid - 1

        self._work_time_font.setPointSize(best_time_size)
        self.time_label.setFont(self._work_time_font)

        if show_date:
            date_size = max(1, int(best_time_size * 0.35))
            self._work_date_font.setPointSize(date_size)
            self.date_label.setFont(self._work_date_font)

    # --- 循环更新引擎 ---
    def update_time_loop(self) -> None:
        curr_time = time.localtime()

        format_str = '%H:%M:%S' if self.config.get("show_hours", True) else '%M:%S'
        new_time_str = time.strftime(format_str, curr_time)
        if self.current_time_str != new_time_str:
            self.current_time_str = new_time_str
            self.time_label.setText(self.current_time_str)

        if self.config["show_date"]:
            week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday_str = week_map[curr_time.tm_wday]
            new_date_str = time.strftime(f"%Y年%m月%d日 {weekday_str}", curr_time)

            if self.current_date_str != new_date_str:
                self.current_date_str = new_date_str
                self.date_label.setText(self.current_date_str)

    def toggle_pin(self, event: Any = None) -> None:
        now = time.time()
        if now - self.last_toggle_time < 0.5:
            return
        self.last_toggle_time = now

        self.config["pinned"] = not bool(self.config["pinned"])
        self.pin_btn.set_pinned(self.config["pinned"])

        geo = self.geometry()
        self.update_window_flags()
        self.setGeometry(geo) 
        self.save_config_immediate()

    def quit_app(self, event: Any = None) -> None:
        self.save_config_immediate()
        QApplication.quit() 

if __name__ == "__main__":
    app = QApplication(sys.argv)

    translator = QTranslator()
    qt_translator_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if translator.load("qtbase_zh_CN.qm", qt_translator_path):
        app.installTranslator(translator)

    fallback_translator = UIRepairTranslator()
    app.installTranslator(fallback_translator)

    QApplication.setQuitOnLastWindowClosed(False)

    clock = TransparentClock()
    sys.exit(app.exec_())


