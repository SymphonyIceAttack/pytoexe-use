# =========================================================
#          FAKE FPS - PERFECTED ULTIMATE EDITION
# =========================================================
import sys, os, ctypes, random, frida, webbrowser, threading, winsound, json, traceback
import qtawesome as qta
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

TARGET_PROCESS = "HD-Player.exe"
DISCORD_URL    = "https://dsc.gg/romulus"
YOUTUBE_URL    = "https://youtube.com/@Romulus_FF"
CONFIG_FILE    = "config.json"

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except AttributeError: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =========================================================
#                 AUDIO FEEDBACK PALETTE
# =========================================================
def async_sound(freq, duration):
    def play():
        try: winsound.Beep(freq, duration)
        except: pass
    threading.Thread(target=play, daemon=True).start()

def sound_hover():   async_sound(850, 10)
def sound_click():   async_sound(1100, 20)
def sound_success(): async_sound(1350, 50)
def sound_stop():    async_sound(450, 80)

# =========================================================
#            HIGH-PERFORMANCE STABLE PRESET PILL
# =========================================================
class AnimatedPresetButton(QPushButton):
    clicked_with_bounds = pyqtSignal(int, int, int)

    def __init__(self, text, min_v, max_v, index, parent=None):
        super().__init__(text, parent)
        self.min_v = min_v
        self.max_v = max_v
        self.idx = index
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        sound_hover()
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            sound_click()
            self.clicked_with_bounds.emit(self.min_v, self.max_v, self.idx)
        super().mousePressEvent(event)

    def set_active(self, state):
        self.blockSignals(True)
        self.setChecked(state)
        self.blockSignals(False)
        self.setProperty("activeState", "true" if state else "false")
        self.style().unpolish(self)
        self.style().polish(self)

# =========================================================
#            REAL-TIME SYSTEM PERFORMANCE GRAPH
# =========================================================
class RealTimeGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = [200] * 40
        self.min_val = 100
        self.max_val = 99999
        self.setFixedHeight(140)

    def update_values(self, next_val, min_v, max_v):
        self.min_val = max(1, min_v)
        self.max_val = max(min_v + 1, max_v)
        self.points.append(next_val)
        if len(self.points) > 40:
            self.points.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w < 10 or h < 10: return
        painter.setPen(QPen(QColor(255, 255, 255, 8), 1, Qt.DashLine))
        for i in range(1, 4):
            y_grid = int(h * (i / 4))
            painter.drawLine(0, y_grid, w, y_grid)
        coords = []
        dx = w / max(1, len(self.points) - 1)
        v_range = float(self.max_val - self.min_val)
        if v_range == 0: v_range = 1.0
        for idx, val in enumerate(self.points):
            cx = int(idx * dx)
            ratio = (val - self.min_val) / v_range
            cy = int(h - 15 - (ratio * (h - 30)))
            cy = max(5, min(h - 5, cy))
            coords.append(QPoint(cx, cy))
        if len(coords) < 2: return
        path = QPainterPath()
        path.moveTo(coords[0].x(), h)
        for pt in coords:
            path.lineTo(pt.x(), pt.y())
        path.lineTo(coords[-1].x(), h)
        path.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(124, 92, 255, 45))
        grad.setColorAt(1, QColor(124, 92, 255, 0))
        painter.fillPath(path, grad)
        painter.setPen(QPen(QColor(124, 92, 255), 2.5, Qt.SolidLine))
        for i in range(len(coords) - 1):
            painter.drawLine(coords[i], coords[i+1])

# =========================================================
#            FAKE INJECTION ENGINE – COMPLETELY INERT
# =========================================================
class FridaWorker(QThread):
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, min_fps, max_fps, use_jitter):
        super().__init__()
        self.min_fps = min_fps
        self.max_fps = max_fps
        self.use_jitter = "true" if use_jitter else "false"
        self.session = None
        self.script = None

    def run(self):
        self.status_changed.emit("Searching for process...")
        QThread.sleep(1)
        self.status_changed.emit("Active")
        self.exec_()

    def stop(self):
        self.quit()
        self.wait(1000)

# =========================================================
#            STABILIZED IMMUTABLE PLATFORM BUTTONS
# =========================================================
class PremiumButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def enterEvent(self, event):
        sound_hover()
        super().enterEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            sound_click()
        super().mousePressEvent(event)

class AnimatedStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_animations = []

    def setCurrentIndex(self, index):
        if index == self.currentIndex(): return
        next_w = self.widget(index)
        eff = QGraphicsOpacityEffect(next_w)
        next_w.setGraphicsEffect(eff)
        super().setCurrentIndex(index)
        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        self.active_animations.append(anim)
        anim.finished.connect(lambda: self.clean_anim_track(anim))
        anim.start()

    def clean_anim_track(self, anim):
        if anim in self.active_animations:
            self.active_animations.remove(anim)

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(60)
        self.drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            delta = event.globalPos() - self.drag_pos
            self.parent.move(self.parent.pos() + delta)
            self.drag_pos = event.globalPos()

# =========================================================
#                      UI CORE FRAME
# =========================================================
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.frida_worker = None
        self.is_initializing = True

        self.setting_minimize_to_tray = False
        self.setting_always_on_top = False
        self.setting_jitter = True
        self.saved_min_fps = 240
        self.saved_max_fps = 350
        self.saved_preset_idx = 1

        self.graph_current = 240
        self._tick_counter = 0
        self.preset_buttons = []

        self.setFixedSize(960, 640)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.frida_debounce_timer = QTimer(self)
        self.frida_debounce_timer.setSingleShot(True)
        self.frida_debounce_timer.timeout.connect(lambda: None)

        self.load_settings_from_json()
        self.build_ui()
        self.setup_tray()
        self.apply_loaded_window_states()

        self.is_initializing = False
        self.show()

    def load_settings_from_json(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.setting_minimize_to_tray = data.get("minimize_to_tray", False)
                    self.setting_always_on_top = data.get("always_on_top", False)
                    self.setting_jitter = data.get("enable_jitter", True)
                    self.saved_min_fps = data.get("min_fps", 240)
                    self.saved_max_fps = data.get("max_fps", 350)
                    self.saved_preset_idx = data.get("preset_index", 1)
            except: pass

    def save_settings_to_json(self):
        if self.is_initializing:
            return
        active_idx = 0
        for btn in self.preset_buttons:
            if btn.isChecked():
                active_idx = btn.idx
                break
        try:
            data = {
                "minimize_to_tray": self.setting_minimize_to_tray,
                "always_on_top": self.setting_always_on_top,
                "enable_jitter": self.setting_jitter,
                "min_fps": self.min_slider.value(),
                "max_fps": self.max_slider.value(),
                "preset_index": active_idx
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except: pass

    def apply_loaded_window_states(self):
        if self.setting_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(14,14,14,14)

        self.main = QFrame()
        self.main.setObjectName("main")
        outer.addWidget(self.main)
        layout = QHBoxLayout(self.main)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(92)
        layout.addWidget(sidebar)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0,24,0,24)
        side.setSpacing(16)

        logo = QFrame()
        logo.setObjectName("logo")
        logo.setFixedSize(52,52)
        l2 = QVBoxLayout(logo); l2.setContentsMargins(0,0,0,0)
        ic = QLabel()
        ic.setPixmap(qta.icon("fa5s.bolt", color="white").pixmap(22,22))
        ic.setAlignment(Qt.AlignCenter)
        l2.addWidget(ic)
        side.addWidget(logo, alignment=Qt.AlignCenter)
        side.addStretch()

        for url, icon_name in [(DISCORD_URL, "fa5b.discord"), (YOUTUBE_URL, "fa5b.youtube")]:
            btn = PremiumButton()
            btn.setObjectName("sideBtn")
            btn.setIcon(qta.icon(icon_name, color="white"))
            btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
            side.addWidget(btn, alignment=Qt.AlignCenter)

        content = QWidget()
        layout.addWidget(content)
        cont = QVBoxLayout(content)
        cont.setContentsMargins(0,0,0,0)
        cont.setSpacing(0)

        self.title_bar = TitleBar(self)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(40, 0, 40, 0)

        window_title = QLabel("FAKE FPS")
        window_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #ffffff; letter-spacing: 1px;")
        title_layout.addWidget(window_title, 0, Qt.AlignVCenter)
        title_layout.addStretch()

        self.min_btn = PremiumButton()
        self.min_btn.setObjectName("minBtn")
        self.min_btn.setIcon(qta.icon("fa5s.window-minimize", color="white", scale_factor=0.8))
        self.min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.min_btn, 0, Qt.AlignVCenter)

        self.close_btn = PremiumButton()
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setIcon(qta.icon("fa5s.times", color="white", scale_factor=0.8))
        self.close_btn.clicked.connect(self.handle_close_action)
        title_layout.addWidget(self.close_btn, 0, Qt.AlignVCenter)

        cont.addWidget(self.title_bar)

        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(40, 0, 40, 40)
        body_layout.setSpacing(24)

        self.tabs = AnimatedStackedWidget()
        body_layout.addWidget(self.tabs, 3)

        # PANEL 1: MAIN BOARD
        page_control = QWidget()
        p1_layout = QVBoxLayout(page_control)
        p1_layout.setContentsMargins(0,0,0,0)
        p1_layout.setSpacing(20)

        left = QFrame()
        left.setObjectName("card")
        p1_layout.addWidget(left)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(36,28,36,28)
        left_layout.setSpacing(16)

        glow = QFrame()
        glow.setObjectName("glow")
        glow.setFixedHeight(4)
        left_layout.addWidget(glow)

        lbl_preset = QLabel("PRESETS")
        lbl_preset.setObjectName("label")
        left_layout.addWidget(lbl_preset)

        preset_grid_widget = QWidget()
        preset_grid = QGridLayout(preset_grid_widget)
        preset_grid.setContentsMargins(0,0,0,0)
        preset_grid.setSpacing(10)

        presets_data = [
            ("240 - 350", 240, 350, 1),
            ("240 - 999", 240, 999, 2),
            ("500 - 999", 500, 999, 3),
            ("1500 - 2000", 1500, 2000, 4)
        ]

        for i, (label, mn, mx, idx) in enumerate(presets_data):
            btn = AnimatedPresetButton(label, mn, mx, idx)
            btn.clicked_with_bounds.connect(self._apply_preset_profile_direct)
            preset_grid.addWidget(btn, i // 2, i % 2)
            self.preset_buttons.append(btn)

        left_layout.addWidget(preset_grid_widget)

        lbl = QLabel("CONFIGURED LIMITS")
        lbl.setObjectName("label")
        left_layout.addWidget(lbl)

        min_row = QHBoxLayout(); min_row.setSpacing(12)
        min_lbl = QLabel("Min"); min_lbl.setFixedWidth(30)
        min_row.addWidget(min_lbl)
        self.min_slider = QSlider(Qt.Horizontal)
        self.min_slider.setRange(100, 99999)
        self.min_slider.setValue(self.saved_min_fps)
        self.min_slider.valueChanged.connect(self._min_slider_changed)
        self.min_slider.sliderReleased.connect(self.save_settings_to_json)
        min_row.addWidget(self.min_slider, 1)
        self.min_input = QLineEdit(str(self.saved_min_fps))
        self.min_input.setObjectName("fpsInput")
        self.min_input.setFixedWidth(85)
        self.min_input.setValidator(QIntValidator(100, 99999))
        self.min_input.textChanged.connect(self._min_input_changed)
        min_row.addWidget(self.min_input)
        left_layout.addLayout(min_row)

        max_row = QHBoxLayout(); max_row.setSpacing(12)
        max_lbl = QLabel("Max"); max_lbl.setFixedWidth(30)
        max_row.addWidget(max_lbl)
        self.max_slider = QSlider(Qt.Horizontal)
        self.max_slider.setRange(100, 99999)
        self.max_slider.setValue(self.saved_max_fps)
        self.max_slider.valueChanged.connect(self._max_slider_changed)
        self.max_slider.sliderReleased.connect(self.save_settings_to_json)
        max_row.addWidget(self.max_slider, 1)
        self.max_input = QLineEdit(str(self.saved_max_fps))
        self.max_input.setObjectName("fpsInput")
        self.max_input.setFixedWidth(85)
        self.max_input.setValidator(QIntValidator(100, 99999))
        self.max_input.textChanged.connect(self._max_input_changed)
        max_row.addWidget(self.max_input)
        left_layout.addLayout(max_row)

        self.start_btn = PremiumButton("START INJECTION")
        self.start_btn.setObjectName("patchBtn")
        self.start_btn.clicked.connect(self.start_hook)
        left_layout.addWidget(self.start_btn)

        self.stop_btn = PremiumButton("STOP & CLEAN MEMORY")
        self.stop_btn.setObjectName("restoreBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_hook)
        left_layout.addWidget(self.stop_btn)

        self.go_settings_btn = QPushButton("Open Settings Panel →")
        self.go_settings_btn.setStyleSheet("color: #7c5cff; font-weight:700; text-align:left; border:none; background:transparent; font-size:12px; padding: 4px;")
        self.go_settings_btn.setCursor(Qt.PointingHandCursor)
        self.go_settings_btn.clicked.connect(self._goto_settings_tab)
        left_layout.addWidget(self.go_settings_btn)
        self.tabs.addWidget(page_control)

        # PANEL 2: SETTINGS
        page_settings = QWidget()
        p2_layout = QVBoxLayout(page_settings)
        p2_layout.setContentsMargins(0,0,0,0)

        sett_card = QFrame()
        sett_card.setObjectName("card")
        p2_layout.addWidget(sett_card)
        sc_lay = QVBoxLayout(sett_card)
        sc_lay.setContentsMargins(36,32,36,32)
        sc_lay.setSpacing(24)

        slbl = QLabel("SETTINGS & PREFERENCES")
        slbl.setObjectName("label")
        sc_lay.addWidget(slbl)

        self.chk_tray = QCheckBox("Minimize to system tray on close command")
        self.chk_tray.setChecked(self.setting_minimize_to_tray)
        self.chk_tray.stateChanged.connect(self._toggle_tray_setting)
        sc_lay.addWidget(self.chk_tray)

        self.chk_top = QCheckBox("Keep tool window always on top")
        self.chk_top.setChecked(self.setting_always_on_top)
        self.chk_top.stateChanged.connect(self._toggle_always_on_top)
        sc_lay.addWidget(self.chk_top)

        self.chk_jitter = QCheckBox("Enable continuous frame variance fluctuations")
        self.chk_jitter.setChecked(self.setting_jitter)
        self.chk_jitter.stateChanged.connect(self._toggle_jitter_setting)
        sc_lay.addWidget(self.chk_jitter)

        sc_lay.addSpacing(20)
        self.back_btn = PremiumButton("SAVE & RETURN")
        self.back_btn.setObjectName("restoreBtn")
        self.back_btn.clicked.connect(self._goto_main_tab)
        sc_lay.addWidget(self.back_btn)
        sc_lay.addStretch()
        self.tabs.addWidget(page_settings)

        for btn in self.preset_buttons:
            if btn.idx == self.saved_preset_idx:
                btn.set_active(True)

        right = QFrame()
        right.setObjectName("statusCard")
        body_layout.addWidget(right, 2)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24,24,24,24)

        sicon = QLabel()
        sicon.setPixmap(qta.icon("fa5s.tachometer-alt", color="#7c5cff").pixmap(36,36))
        sicon.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(sicon)

        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status)
        right_layout.addSpacing(10)

        lbl_g = QLabel("DYNAMIC OUTPUT ENGINE VISUALIZER")
        lbl_g.setObjectName("label")
        lbl_g.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(lbl_g)

        self.graph = RealTimeGraph()
        right_layout.addWidget(self.graph)
        right_layout.addStretch()

        self.status_glow = QGraphicsDropShadowEffect(blurRadius=12, color=QColor(124,92,255,140), offset=QPointF(0,0))
        self.status.setGraphicsEffect(self.status_glow)
        self._hue = 260

        self.engine_timer = QTimer(self)
        self.engine_timer.timeout.connect(self._sync_local_graph_ticks)
        self.engine_timer.start(16)

        cont.addWidget(body_widget)

    def _apply_preset_profile_direct(self, mn, mx, idx):
        for btn in self.preset_buttons:
            btn.set_active(btn.idx == idx)
        self.min_slider.blockSignals(True)
        self.max_slider.blockSignals(True)
        self.min_slider.setValue(mn)
        self.max_slider.setValue(mx)
        self.min_slider.blockSignals(False)
        self.max_slider.blockSignals(False)
        self.min_input.blockSignals(True); self.min_input.setText(str(mn)); self.min_input.blockSignals(False)
        self.max_input.blockSignals(True); self.max_input.setText(str(mx)); self.max_input.blockSignals(False)
        self.save_settings_to_json()

    def _sync_local_graph_ticks(self):
        self._hue = (self._hue + 0.5) % 360
        c = QColor(); c.setHsl(int(self._hue), 190, 130)
        self.status_glow.setColor(c.lighter(110))
        mn = self.min_slider.value()
        mx = self.max_slider.value()
        self._tick_counter += 1
        if self.setting_jitter:
            if self._tick_counter >= 37:
                self._tick_counter = 0
                self.graph_current = random.randint(mn, mx)
        else:
            self.graph_current = mx
        if self.graph_current < mn: self.graph_current = mn
        if self.graph_current > mx: self.graph_current = mx
        self.graph.update_values(self.graph_current, mn, mx)

    def _goto_settings_tab(self):
        sound_click()
        self.tabs.setCurrentIndex(1)

    def _goto_main_tab(self):
        sound_click()
        self.tabs.setCurrentIndex(0)

    def _clear_preset_highlights(self):
        for btn in self.preset_buttons:
            if btn.isChecked():
                btn.set_active(False)

    def _min_slider_changed(self, value):
        if value > self.max_slider.value():
            self.max_slider.blockSignals(True)
            self.max_slider.setValue(value)
            self.max_input.blockSignals(True); self.max_input.setText(str(value)); self.max_input.blockSignals(False)
            self.max_slider.blockSignals(False)
        self.min_input.blockSignals(True); self.min_input.setText(str(value)); self.min_input.blockSignals(False)
        self._clear_preset_highlights()

    def _min_input_changed(self, text):
        if text and text.isdigit():
            val = int(text)
            if 100 <= val <= 99999:
                self.min_slider.blockSignals(True)
                self.min_slider.setValue(val)
                self.min_slider.blockSignals(False)
                if val > self.max_slider.value():
                    self.max_slider.blockSignals(True)
                    self.max_slider.setValue(val)
                    self.max_input.blockSignals(True); self.max_input.setText(str(val)); self.max_input.blockSignals(False)
                    self.max_slider.blockSignals(False)
                self._clear_preset_highlights()
                self.save_settings_to_json()

    def _max_slider_changed(self, value):
        if value < self.min_slider.value():
            self.min_slider.blockSignals(True)
            self.min_slider.setValue(value)
            self.min_input.blockSignals(True); self.min_input.setText(str(value)); self.min_input.blockSignals(False)
            self.min_slider.blockSignals(False)
        self.max_input.blockSignals(True); self.max_input.setText(str(value)); self.max_input.blockSignals(False)
        self._clear_preset_highlights()

    def _max_input_changed(self, text):
        if text and text.isdigit():
            val = int(text)
            if 100 <= val <= 99999:
                self.max_slider.blockSignals(True)
                self.max_slider.setValue(val)
                self.max_slider.blockSignals(False)
                if val < self.min_slider.value():
                    self.min_slider.blockSignals(True)
                    self.min_slider.setValue(val)
                    self.min_input.blockSignals(True); self.min_input.setText(str(val)); self.min_input.blockSignals(False)
                    self.min_slider.blockSignals(False)
                self._clear_preset_highlights()
                self.save_settings_to_json()

    def _toggle_tray_setting(self, state):
        sound_click()
        self.setting_minimize_to_tray = (state == Qt.Checked)
        self.save_settings_to_json()

    def _toggle_always_on_top(self, state):
        sound_click()
        self.setting_always_on_top = (state == Qt.Checked)
        self.save_settings_to_json()
        flags = self.windowFlags()
        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint if self.setting_always_on_top else flags & ~Qt.WindowStaysOnTopHint)
        self.show()

    def _toggle_jitter_setting(self, state):
        sound_click()
        self.setting_jitter = (state == Qt.Checked)
        self.save_settings_to_json()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(qta.icon("fa5s.tachometer-alt", color="#7c5cff"))
        m = QMenu()
        m.addAction("Show Interface", self.show_window)
        m.addAction("Exit Complete Tool", self.force_quit)
        self.tray.setContextMenu(m)
        self.tray.activated.connect(lambda r: self.show_window() if r == QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def show_window(self):
        self.showNormal(); self.activateWindow(); self.raise_()

    def handle_close_action(self):
        if self.setting_minimize_to_tray: self.hide()
        else: self.force_quit()

    def force_quit(self):
        self.stop_hook(); self.tray.hide(); QApplication.instance().quit()

    def closeEvent(self, event):
        if self.setting_minimize_to_tray: event.ignore(); self.hide()
        else: self.stop_hook(); event.accept()

    def start_hook(self):
        if not is_admin():
            sound_stop(); QMessageBox.critical(self, "Error", "Administrator configuration access required.")
            return
        sound_success()
        self.status.setText("Scanning data...")
        self.start_btn.setEnabled(False); self.stop_btn.setEnabled(True)
        self.frida_worker = FridaWorker(self.min_slider.value(), self.max_slider.value(), self.setting_jitter)
        self.frida_worker.status_changed.connect(lambda t: self.status.setText(t))
        self.frida_worker.start()

    def stop_hook(self):
        if self.frida_worker:
            sound_stop(); self.status.setText("Restoring memory...")
            self.frida_worker.stop(); self.frida_worker = None
        self.start_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        self.status.setText("Disengaged")

# =========================================================
#            THE CLEANEST HIGH-END STYLING SYSTEM
# =========================================================
STYLE = """
QMainWindow { background: transparent; }
#main {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #070911, stop:1 #0d101d);
    border-radius: 24px; border: 1px solid rgba(255,255,255,0.04);
}
#sidebar {
    background: rgba(255,255,255,0.01); border-top-left-radius: 24px;
    border-bottom-left-radius: 24px; border-right: 1px solid rgba(255,255,255,0.02);
}
#logo { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c5cff, stop:1 #5266ff); border-radius: 14px; }
#card, #statusCard { background: rgba(255,255,255,0.02); border-radius: 20px; border: 1px solid rgba(255,255,255,0.03); }
#glow { background: #7c5cff; border-radius: 2px; }
#label { color: rgba(255,255,255,0.35); font-size: 10px; font-weight: 800; letter-spacing: 1.5px; }
#status { color: white; font-size: 15px; font-weight: 700; }
QLabel { background: transparent; border: none; color: white; font-family: 'Segoe UI', Arial; }

AnimatedPresetButton {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; color: rgba(255,255,255,0.70); font-weight: 600; font-size: 12px;
}
AnimatedPresetButton:hover {
    background: rgba(124,92,255,0.10); border: 1px solid rgba(124,92,255,0.3);
    color: white;
}
AnimatedPresetButton[activeState="true"] {
    background: #7c5cff; border: 1px solid #9275ff; color: white; font-weight: 700;
}

QSlider:horizontal { min-height: 28px; max-height: 28px; }
QSlider::groove:horizontal { background: rgba(255,255,255,0.05); border-radius: 4px; height: 6px; }
QSlider::handle:horizontal { background: #7c5cff; width: 16px; margin: -5px 0; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: #9275ff; }
QSlider::sub-page:horizontal { background: #7c5cff; border-radius: 4px; }

#fpsInput {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 5px 10px; color: white; font-size: 13px; font-weight: 600;
}
#fpsInput:focus { border: 1px solid #7c5cff; background: rgba(255,255,255,0.06); }

QCheckBox { color: rgba(255,255,255,0.75); font-size: 13px; spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.02); }
QCheckBox::indicator:hover { border: 1px solid #7c5cff; background: rgba(124,92,255,0.05); }
QCheckBox::indicator:checked { background: #7c5cff; border: 1px solid #7c5cff; }

#patchBtn {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #4f62ff);
    border: none; border-radius: 16px; color: white; font-size: 14px; font-weight: 700; min-height: 50px;
}
#patchBtn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #9275ff, stop:1 #6073ff); }
#patchBtn:disabled { background: rgba(255,255,255,0.02); color: rgba(255,255,255,0.15); }

#restoreBtn { background: rgba(255,255,255,0.04); border: none; border-radius: 16px; color: white; font-size: 14px; font-weight: 700; min-height: 50px; }
#restoreBtn:hover { background: rgba(255,255,255,0.08); }
#restoreBtn:disabled { background: rgba(255,255,255,0.01); color: rgba(255,255,255,0.15); }

#sideBtn { background: rgba(255,255,255,0.02); border: none; border-radius: 12px; min-width: 46px; min-height: 46px; }
#sideBtn:hover { background: rgba(124,92,255,0.2); }

#closeBtn, #minBtn {
    background: rgba(255,255,255,0.03); border: none; border-radius: 10px;
    min-width: 42px; max-width: 42px; min-height: 42px; max-height: 42px; margin-left: 8px;
}
#closeBtn:hover { background: #ff4d6d; }
#minBtn:hover { background: rgba(255,255,255,0.08); }

QMessageBox { background: #070911; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; }
QMessageBox QLabel { color: white; }
QMessageBox QPushButton { background: #7c5cff; border-radius: 8px; padding: 6px 14px; color: white; font-weight: 700; }
"""

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setStyleSheet(STYLE)

        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path): app.setWindowIcon(QIcon(icon_path))
        else: app.setWindowIcon(qta.icon("fa5s.bolt", color="#7c5cff"))

        window = App()
        sys.exit(app.exec_())
    except Exception as e:
        with open("crash_log.txt", "w") as crash_file:
            traceback.print_exc(file=crash_file)