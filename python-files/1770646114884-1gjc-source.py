
global pipe_threads
global log_callback
global monitor_thread
global valorant_running
global shutdown_event
global monitored_pids
global stopped_once
global current_job
global pipe_handles
global monitoring_active
import sys
import os
import time
import threading
import psutil
import win32pipe
import win32file
import pywintypes
import win32con
import win32job
import win32api
import shutil
import base64
import random
import datetime
import subprocess
from PySide6.QtCore import Qt, QRectF, QSize, QRect, QPoint, QPointF, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget, QPlainTextEdit, QGridLayout, QMessageBox, QGraphicsOpacityEffect, QSizePolicy, QProgressBar
from PySide6.QtWidgets import QButtonGroup
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath, QLinearGradient, QRadialGradient
pipe_name = '\\\\.\\pipe\\933823D3-C77B-4BAE-89D7-A92B567236BC'
valorant_running = False
stopped_once = False
current_job = None
log_callback = None
pipe_threads = []
pipe_handles = []
monitor_thread = None
monitored_pids = set()
monitored_lock = threading.Lock()
monitoring_active = False
def make_shutdown_event():
    return threading.Event()
shutdown_event = make_shutdown_event()
def log_message(msg):
    if log_callback:
        log_callback(msg)
def stop_and_restart_vgc():
    os.system('sc stop vgc')
    time.sleep(0.5)
    os.system('sc start vgc')
    time.sleep(0.5)
def override_vgc_pipe():
    try:
        pipe = win32file.CreateFile(pipe_name, win32con.GENERIC_READ | win32con.GENERIC_WRITE, 0, None, win32con.OPEN_EXISTING, 0, None)
        win32file.CloseHandle(pipe)
    except Exception:
        return None
def handle_client(pipe):
    # irreducible cflow, using cdg fallback
    global stopped_once
    if not shutdown_event.is_set():
        pass
    data = win32file.ReadFile(pipe, 4096)
    if data:
        pass
    if not stopped_once:
        os.system('sc stop vgc')
        try:
            import winsound
            winsound.Beep(1000, 500)
        except:
            pass
        stopped_once = True
    win32file.WriteFile(pipe, data[1])
    try:
        win32file.CloseHandle(pipe)
    except Exception:
        return
    except pywintypes.error as e:
        pass
    if getattr(e, 'winerror', None) == 109:
        pass
    time.sleep(0.1)
def create_named_pipe():
    if not shutdown_event.is_set():
        try:
            pipe = win32pipe.CreateNamedPipe(pipe_name, win32con.PIPE_ACCESS_DUPLEX, win32con.PIPE_TYPE_MESSAGE | win32con.PIPE_WAIT, win32con.PIPE_UNLIMITED_INSTANCES, 1048576, 1048576, 500, None)
            pipe_handles.append(pipe)
            win32pipe.ConnectNamedPipe(pipe, None)
            t = threading.Thread(target=handle_client, args=(pipe,), daemon=True)
            t.start()
            pipe_threads.append(t)
        except Exception:
            time.sleep(1)
def create_job_object():
    job = win32job.CreateJobObject(None, '')
    extended_info = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    extended_info['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, extended_info)
    return job
def assign_valorant_to_job():
    # irreducible cflow, using cdg fallback
    global current_job
    if current_job:
        try:
            win32job.TerminateJobObject(current_job, 0)
            current_job.Close()
        except Exception:
            pass
        current_job = None
        time.sleep(2)
    current_job = create_job_object()
    found = False
    if not found:
        if not shutdown_event.is_set():
            for proc in psutil.process_iter(['pid', 'name']):
                pass
    if proc.info['name'] and 'VALORANT-Win64-Shipping.exe' in proc.info['name']:
        pass
    h_process = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.info['pid'])
    win32job.AssignProcessToJobObject(current_job, h_process)
    found = True
    if not found:
        time.sleep(1)
def find_riot_client_path():
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == 'riotclientservices.exe' and proc.info['exe'] and os.path.exists(proc.info['exe']):
                            return proc.info['exe']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    common_dirs = ['C:\\Riot Games', 'C:\\Program Files\\Riot Games', 'C:\\Program Files (x86)\\Riot Games', 'D:\\Riot Games', 'D:\\Program Files\\Riot Games', 'D:\\Program Files (x86)\\Riot Games']
    for base in common_dirs:
        candidate = os.path.join(base, 'Riot Client', 'RiotClientServices.exe')
        if os.path.exists(candidate):
            return candidate
    exe_in_path = shutil.which('RiotClientServices.exe')
    if exe_in_path:
        return exe_in_path
    else:
        search_roots = ['C:\\Program Files', 'C:\\Program Files (x86)', 'C:\\Riot Games', 'D:\\Program Files', 'D:\\Program Files (x86)', 'D:\\Riot Games']
        for root in search_roots:
            for dirpath, _, filenames in os.walk(root):
                if 'RiotClientServices.exe' in filenames:
                    return os.path.join(dirpath, 'RiotClientServices.exe')
        return None
def launch_valorant():
    path = find_riot_client_path()
    if path:
        subprocess.Popen([path, '--launch-product=valorant', '--launch-patchline=live'])
        assign_valorant_to_job()
def start_valorant():
    global current_job
    global valorant_running
    if not valorant_running:
        threading.Thread(target=launch_valorant, daemon=True).start()
        valorant_running = True
        return None
    else:
        if current_job:
            try:
                win32job.TerminateJobObject(current_job, 0)
                current_job.Close()
            except Exception:
                pass
            current_job = None
        os.system('taskkill /f /im VALORANT-Win64-Shipping.exe')
        valorant_running = False
def monitor_new_exes():
    # irreducible cflow, using cdg fallback
    prev_pids = set((p.info['pid'] for p in psutil.process_iter(['pid'])))
    if monitoring_active and (not shutdown_event.is_set()):
            current_pids = set((p.info['pid'] for p in psutil.process_iter(['pid'])))
            new_pids = current_pids - prev_pids
            with monitored_lock:
                pass
    for pid in new_pids:
        pass
    proc = psutil.Process(pid)
    exe = proc.exe()
    if exe:
        pass
    monitored_pids.add(pid)
    prev_pids = current_pids
    time.sleep(0.5)
def start_monitoring_exes():
    global monitor_thread
    global monitoring_active
    with monitored_lock:
        monitored_pids.clear()
    monitoring_active = True
    monitor_thread = threading.Thread(target=monitor_new_exes, daemon=True)
    monitor_thread.start()
def stop_monitoring_exes():
    global monitor_thread
    global monitoring_active
    monitoring_active = False
    if monitor_thread:
        monitor_thread.join(timeout=2)
        monitor_thread = None
def kill_monitored_exes():
    # irreducible cflow, using cdg fallback
    killed = []
    with monitored_lock:
        pass
    for pid in list(monitored_pids):
                proc = psutil.Process(pid)
                exe = proc.exe()
                if exe and proc.is_running():
                        proc.kill()
                        killed.append(exe)
                monitored_pids.clear()
                return killed
def reset_shutdown_event():
    global shutdown_event
    shutdown_event = make_shutdown_event()
def close_all_pipes():
    for h in pipe_handles:
        try:
            win32file.CloseHandle(h)
        except Exception:
            pass
    pipe_handles.clear()
def start_with_emulate():
    global current_job
    global stopped_once
    global valorant_running
    stopped_once = False
    reset_shutdown_event()
    close_all_pipes()
    pipe_threads.clear()
    if current_job:
        try:
            win32job.TerminateJobObject(current_job, 0)
            current_job.Close()
        except Exception:
            pass
        current_job = None
    stop_and_restart_vgc()
    override_vgc_pipe()
    threading.Thread(target=create_named_pipe, daemon=True).start()
    start_monitoring_exes()
    threading.Thread(target=launch_valorant, daemon=True).start()
    valorant_running = True
def safe_exit():
    global current_job
    global stopped_once
    global valorant_running
    shutdown_event.set()
    stopped_once = False
    try:
        for t in pipe_threads:
            t.join(timeout=1)
    except:
        pass
    pipe_threads.clear()
    close_all_pipes()
    if current_job:
        try:
            win32job.TerminateJobObject(current_job, 0)
            current_job.Close()
        except Exception:
            pass
        current_job = None
    os.system('taskkill /f /im VALORANT-Win64-Shipping.exe')
    os.system('sc stop vgc')
    valorant_running = False
    stop_monitoring_exes()
    kill_monitored_exes()
class SystemMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fan_angle = 0
        self.setMinimumSize(360, 400)
        self.temperature = 34.0
        self.rpm = 0
        self.sensor_data = {'CPU': 27, 'System 1': 26, 'System 2': 26, 'Chipset': 29, 'VRM MOS': 34, 'PCIE X16': 27, 'PCIE X8': 26}
        self.fan_curve = {30: 25, 40: 40, 50: 50, 60: 65, 70: 85, 80: 97, 90: 100}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)
    def update_data(self):
        self.temperature += random.uniform((-0.3), 0.3)
        self.temperature = max(30, min(95, self.temperature))
        self.rpm = int((self.temperature - 30) * 100)
        for key in self.sensor_data:
            if isinstance(self.sensor_data[key], int):
                self.sensor_data[key] += random.randint((-1), 1)
        self.fan_angle += self.rpm / 60
        self.fan_angle %= 360
        self.update()
    def draw_fan_curve_graph(self, painter, x, y, width=300, height=180):
        margin = 40
        graph_rect = QRect(x, y, width, height)
        painter.setPen(QPen(QColor('#444444')))
        painter.setBrush(QColor('#121212'))
        painter.drawRoundedRect(graph_rect, 8, 8)
        painter.setPen(QPen(QColor('#888888')))
        painter.drawLine(x + margin, y + height - margin, x + width - margin, y + height - margin)
        painter.drawLine(x + margin, y + height - margin, x + margin, y + margin)
        temps = sorted(self.fan_curve.keys())
        points = []
        for temp in temps:
            pwm = self.fan_curve[temp]
            px = x + margin + (temp - 30) / 60 * (width - 2 * margin)
            py = y + height - margin - pwm / 100 * (height - 2 * margin)
            points.append(QPointF(px, py))
        painter.setPen(QPen(QColor('#ff7043'), 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
        for pt in points:
            painter.setBrush(QColor('#ff8a65'))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pt, 4, 4)
        painter.setPen(QColor('#aaaaaa'))
        painter.setFont(QFont('Segoe UI', 9))
        for i in range(0, 101, 20):
            py = y + height - margin - i / 100 * (height - 2 * margin)
            painter.drawText(x + 10, int(py + 5), f'{i}%')
        for temp in range(30, 91, 10):
            px = x + margin + (temp - 30) / 60 * (width - 2 * margin)
            painter.drawText(int(px - 10), y + height - 20, f'{temp}')
        painter.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        painter.setPen(QColor('#ffffff'))
        painter.drawText(x + margin, y + 20, 'Fan Curve')
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#1c1c1c'))
        self.draw_fan_curve_graph(painter, 20, 30)
        painter.setPen(QPen(QColor('#555555')))
        painter.setBrush(QColor('#2a2a2a'))
        painter.drawRoundedRect(self.width() - 240, 30, 220, 180, 10, 10)
        painter.setPen(QColor('#ffffff'))
        painter.setFont(QFont('Segoe UI', 11))
        y = 60
        for key, value in self.sensor_data.items():
            val_text = f'{value}' if isinstance(value, int) else '--'
            painter.drawText(self.width() - 230, y, f'{key}: {val_text}')
            y += 22
class Particle:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.vx = random.uniform((-0.4), 0.4)
        self.vy = random.uniform((-0.4), 0.4)
        self.size = random.uniform(1.2, 2.5)
    def move(self, width, height):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > width:
            self.vx *= (-1)
        if self.y < 0 or self.y > height:
            self.vy *= (-1)
class ParticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.particles = [Particle(420, 700) for _ in range(35)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(20)
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, p in enumerate(self.particles):
            p.move(self.width(), self.height())
            for p2 in self.particles[i + 1:]:
                dist = (p.x - p2.x) ** 2 + (p.y - p2.y) ** 2
                if dist < 4500:
                    opacity = int(50 * (1 - dist / 4500))
                    painter.setPen(QColor(120, 200, 255, opacity))
                    painter.drawLine(QPointF(p.x, p.y), QPointF(p2.x, p2.y))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(120, 200, 255, 120))
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
class CustomGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FUCKED BY GENERIC SERVER ')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.loading_timer_count = 0
        self.loading_button = None
        self.loading_target_function = None
        self.progress_timer = None
        self.setStyleSheet('\n            QWidget#MainFrame {\n                background-color: rgba(5, 5, 15, 245);\n                border: 1px solid #1a1a2a;\n                border-radius: 20px;\n            }\n            QLabel { \n                color: #ffffff; \n                font-family: \'Segoe UI\', sans-serif; \n                background: transparent; \n            }\n            QPushButton#NavBtn { \n                color: #555; \n                font-size: 11px; \n                font-weight: bold; \n                border: none; \n                padding: 10px; \n                background: transparent; \n            }\n            QPushButton#NavBtn:checked { \n                color: #3399ff; \n                border-bottom: 2px solid #3399ff; \n            }\n            QPushButton#ActionBtn { \n                background-color: rgba(8, 8, 20, 150); \n                border: 1px solid #10334a; \n                border-radius: 8px; \n                color: #ffffff; \n                font-size: 12px; \n                padding: 10px; \n                font-weight: bold; \n            }\n            QPushButton#ActionBtn:hover { \n                background-color: rgba(5, 10, 26, 200); \n                border: 1px solid #3399ff; \n            }\n            QFrame#StatusBox { \n                background-color: #0d0d1a; \n                border-radius: 8px; \n            }\n            QFrame#CompactStep { \n                background-color: #0a0a15; \n                border: 1px solid #151525; \n                border-radius: 6px; \n                padding: 8px; \n            }\n            QPlainTextEdit#LogArea {\n                background-color: rgba(0, 0, 10, 100);\n                border: 1px solid #1a1a2a;\n                border-radius: 10px; \n                color: #a0c0ff;\n                font-family: \'Consolas\', monospace;\n                font-size: 10px;\n                padding: 5px;\n            }\n        ')
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QFrame()
        self.container.setObjectName('MainFrame')
        self.main_layout.addWidget(self.container)
        self.particle_layer = ParticleWidget(self.container)
        self.particle_layer.setGeometry(self.container.rect())
        self.particle_layer.lower()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(25, 20, 25, 25)
        header_layout = QHBoxLayout()
        left_spacer = QWidget()
        left_spacer.setFixedWidth(30)
        header_layout.addWidget(left_spacer)
        header_layout.addStretch()
        right_spacer = QWidget()
        right_spacer.setFixedWidth(75)
        header_layout.addWidget(right_spacer)
        ver = QLabel('Nigbesitng crack by frosty')
        ver.setStyleSheet('\n            color: #3399ff; \n            font-weight: bold; \n            font-size: 10px; \n            border: 1px solid #10334a; \n            padding: 5px 20px; \n            border-radius: 8px; \n            background: rgba(0,0,10,100);\n        ')
        header_layout.addWidget(ver)
        header_layout.addStretch(1)
        minimize_btn = QPushButton('-')
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet('\n            QPushButton {\n                font-size: 18px; \n                font-weight: bold;\n                background: transparent;\n            }\n            QPushButton {\n                color: #3399ff;\n                background: rgba(51, 153, 255, 0.1);\n                border-radius: 4px;\n            }\n        ')
        minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minimize_btn.clicked.connect(self.showMinimized)
        header_layout.addWidget(minimize_btn)
        close_btn = QPushButton('x')
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet('\n            QPushButton { \n                font-size: 20px; \n                font-weight: bold;\n                background: transparent;\n            }\n            QPushButton {\n                color: #ff3333;\n                background: rgba(255, 51, 51, 0.1);\n                border-radius: 4px;\n            }\n        ')
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        self.container_layout.addLayout(header_layout)
        nav_layout = QHBoxLayout()
        self.tab_stack = QStackedWidget()
        for name in ['UPDATES', 'EMULATOR', 'SPOOFER - CHEAT']:
            btn = QPushButton(name)
            btn.setObjectName('NavBtn')
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda ch, n=name: self.switch_tab(n))
            if name == 'EMULATOR':
                btn.setChecked(True)
            nav_layout.addWidget(btn)
        self.container_layout.addLayout(nav_layout)
        self.setup_updates_page()
        self.setup_emulator_page()
        self.setup_spoofer_page()
        self.container_layout.addWidget(self.tab_stack)
        self.tab_stack.setCurrentIndex(1)
        self.setMinimumSize(420, 620)
        self.setMaximumSize(420, 700)
        self._drag_pos = None
    def add_log(self, message):
        now = datetime.datetime.now().strftime('%H:%M:%S')
        log_entry = f'[{now}] {message}'
        self.log_area.appendPlainText(log_entry)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
    def switch_tab(self, name):
        indices = {'UPDATES': 0, 'EMULATOR': 1, 'SPOOFER - CHEAT': 2}
        self.tab_stack.setCurrentIndex(indices[name])
    def setup_updates_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 10, 5, 10)
        title = QLabel('LATEST CHANGES')
        title.setStyleSheet('color: #3399ff; font-weight: bold; font-size: 12px; margin-bottom: 5px;')
        layout.addWidget(title)
        changes = ['> Vanguard Emulator core engine updated.', '> Bypass stability improved for Version 2.0.', '> GUI performance optimizations and fixes.']
        for change in changes:
            lbl = QLabel(change)
            lbl.setStyleSheet('color: #a0c0ff; font-size: 11px; padding: 4px; border-bottom: 1px solid #111125;')
            layout.addWidget(lbl)
        layout.addStretch()
        self.tab_stack.addWidget(page)
    def setup_misc_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        coming_soon = QLabel('MORE FEATURES\nCOMING SOON')
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_soon.setStyleSheet('\n            color: #334466; \n            font-size: 14px; \n            font-weight: bold; \n            letter-spacing: 3px;\n            border: 1px dashed #222244;\n            border-radius: 10px;\n            padding: 50px;\n        ')
        layout.addStretch()
        layout.addWidget(coming_soon)
        layout.addStretch()
        self.tab_stack.addWidget(page)
    def setup_spoofer_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        btns_container = QVBoxLayout()
        btns_container.setSpacing(10)
        drive_oneclick = QPushButton('DRIVER SPOOFER')
        drive_oneclick.setObjectName('ActionBtn')
        drive_oneclick.setFixedHeight(35)
        drive_oneclick.clicked.connect(lambda: self.button_with_loading(drive_oneclick, 'DRIVER SPOOFER', self.driver_spoof_clicked))
        btn_oneclick = QPushButton('ONECLICK SPOOFER')
        btn_oneclick.setObjectName('ActionBtn')
        btn_oneclick.setFixedHeight(35)
        btn_oneclick.clicked.connect(lambda: self.button_with_loading(btn_oneclick, 'ONECLICK SPOOFER', self.oneclick_spoofer_clicked))
        btn_checker = QPushButton('CHECKER')
        btn_checker.setObjectName('ActionBtn')
        btn_checker.setFixedHeight(35)
        btn_checker.clicked.connect(lambda: self.button_with_loading(btn_checker, 'CHECKER', self.checker_clicked))
        btn_internal = QPushButton('LOAD INTERNAL')
        btn_internal.setObjectName('ActionBtn')
        btn_internal.setFixedHeight(35)
        btn_internal.clicked.connect(lambda: self.button_with_loading(btn_internal, 'INTERNAL', self.internal_clicked))
        btns_container.addWidget(drive_oneclick)
        btns_container.addWidget(btn_oneclick)
        btns_container.addWidget(btn_checker)
        btns_container.addWidget(btn_internal)
        main_layout.addLayout(btns_container)
        main_layout.addSpacing(10)
        self.guide_type_frame = QFrame()
        guide_type_layout = QHBoxLayout(self.guide_type_frame)
        guide_type_layout.setContentsMargins(0, 0, 0, 0)
        guide_type_layout.setSpacing(5)
        guide_type_layout.addStretch(1)
        self.btn_driver_guide = QPushButton('DRIVER GUIDE')
        self.btn_driver_guide.setObjectName('NavBtn')
        self.btn_driver_guide.setCheckable(True)
        self.btn_driver_guide.setAutoExclusive(True)
        self.btn_oneclick_guide = QPushButton('ONE CLICK GUIDE')
        self.btn_oneclick_guide.setObjectName('NavBtn')
        self.btn_oneclick_guide.setCheckable(True)
        self.btn_oneclick_guide.setAutoExclusive(True)
        self.btn_oneclick_guide.setChecked(True)
        guide_type_layout.addWidget(self.btn_driver_guide)
        guide_type_layout.addWidget(self.btn_oneclick_guide)
        guide_type_layout.addStretch(1)
        main_layout.addWidget(self.guide_type_frame)
        self.spoofer_steps_container = QFrame()
        self.spoofer_steps_layout = QVBoxLayout(self.spoofer_steps_container)
        self.spoofer_steps_layout.setContentsMargins(0, 5, 0, 5)
        self.spoofer_steps_layout.setSpacing(10)
        main_layout.addWidget(self.spoofer_steps_container)
        def clear_steps():
            if self.spoofer_steps_layout.count():
                item = self.spoofer_steps_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
        def add_step(number, text):
            step = self.create_step(number, text)
            self.spoofer_steps_layout.addWidget(step)
        def show_oneclick_guide():
            clear_steps()
            add_step('1', 'Disable graphics card from Device Manager')
            add_step('2', 'Turn off TPM, Secure Boot, and HVCI')
            add_step('3', 'Run One-Click and restart')
            add_step('4', 'Spoof successful when message appears on boot')
        def show_driver_guide():
            clear_steps()
            add_step('1', 'Turn Off Secure Boot and TPM, Turn On HVCI ')
            add_step('2', 'Run Driver Spoofer and restart')
        self.btn_oneclick_guide.clicked.connect(show_oneclick_guide)
        self.btn_driver_guide.clicked.connect(show_driver_guide)
        show_oneclick_guide()
        main_layout.addStretch()
        self.tab_stack.addWidget(page)
    def clear_steps(self):
        if self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
    def spoofer_button_clicked(self, log_text, status_text):
        self.status_val.setText(status_text)
    def spoof_all_clicked(self):
        self.status_val.setText('FULL SPOOFING')
    def create_steps_overlay(self, parent):
        self.steps_overlay = QFrame(parent)
        self.steps_overlay.setObjectName('StepsOverlay')
        self.steps_overlay.setStyleSheet('\n            QFrame#StepsOverlay {\n                background-color: rgba(20, 20, 30, 240);\n                border-radius: 10px;\n            }\n        ')
        self.steps_overlay.hide()
        self.steps_overlay.setGeometry(20, parent.height(), parent.width() - 40, parent.height() - 40)
        lay = QVBoxLayout(self.steps_overlay)
        lay.setContentsMargins(15, 15, 15, 15)
        close_btn = QPushButton('Close')
        close_btn.setObjectName('NavBtn')
        close_btn.clicked.connect(self.hide_steps_overlay)
        lay.addWidget(close_btn)
        self.steps_container = QFrame()
        self.steps_layout = QGridLayout(self.steps_container)
        self.steps_layout.setSpacing(8)
        lay.addWidget(self.steps_container)
    def show_steps_overlay(self):
        self.steps_overlay.show()
        start_rect = QRect(20, self.height(), self.width() - 40, self.height() - 40)
        end_rect = QRect(20, 20, self.width() - 40, self.height() - 40)
        self.steps_anim = QPropertyAnimation(self.steps_overlay, b'geometry')
        self.steps_anim.setDuration(300)
        self.steps_anim.setStartValue(start_rect)
        self.steps_anim.setEndValue(end_rect)
        self.steps_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.steps_anim.start()
    def create_silent_title(self, text):
        title = QLabel(text)
        title.setStyleSheet('\n            QLabel {\n                border-bottom: 2px solid #00ffaa;\n                padding: 6px 4px;\n                font-size: 14px;\n                font-weight: bold;\n            }\n        ')
        return title
    def setup_emulator_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        status_fr = QFrame()
        status_fr.setObjectName('StatusBox')
        status_fr.setFixedHeight(45)
        status_lay = QHBoxLayout(status_fr)
        status_lay.addWidget(QLabel('STATUS', styleSheet='color: #444466; font-size: 9px; font-weight: bold;'))
        self.status_val = QLabel('IDLE')
        self.status_val.setStyleSheet('color: #3399ff; font-weight: bold; font-size: 11px; letter-spacing: 1px;')
        self.opacity_effect = QGraphicsOpacityEffect(self.status_val)
        self.status_val.setGraphicsEffect(self.opacity_effect)
        self.start_anim()
        status_lay.addWidget(self.status_val)
        status_lay.addStretch()
        layout.addWidget(status_fr)
        guide_selector_frame = QFrame()
        guide_selector_layout = QHBoxLayout(guide_selector_frame)
        guide_selector_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_bypass_guide = QPushButton('Bypass Guide')
        self.btn_bypass_guide.setObjectName('NavBtn')
        self.btn_bypass_guide.setCheckable(True)
        self.btn_bypass_guide.setAutoExclusive(True)
        self.btn_emulator_guide = QPushButton('Emulator Guide')
        self.btn_emulator_guide.setObjectName('NavBtn')
        self.btn_emulator_guide.setCheckable(True)
        self.btn_emulator_guide.setAutoExclusive(True)
        self.btn_emulator_guide.setChecked(True)
        guide_selector_layout.addWidget(self.btn_bypass_guide)
        guide_selector_layout.addWidget(self.btn_emulator_guide)
        guide_selector_layout.addStretch()
        layout.addWidget(guide_selector_frame)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet('\n            QProgressBar { background-color: #2d2d3a; border: none; border-radius: 1px; }\n            QProgressBar::chunk { background-color: #3399ff; border-radius: 1px; }\n        ')
        vanguard_frame = QFrame()
        vanguard_layout = QHBoxLayout(vanguard_frame)
        vanguard_layout.setContentsMargins(0, 0, 0, 0)
        vanguard_layout.setSpacing(5)
        self.btn_vanguard = QPushButton('Vanguard Emulator')
        self.btn_vanguard.setObjectName('ActionBtn')
        self.btn_vanguard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_vanguard.clicked.connect(lambda: self.button_with_loading(self.btn_vanguard, 'Vanguard Emulator', self.start_with_emulate_ui))
        vanguard_layout.addWidget(self.btn_vanguard)
        self.btn_bypass = QPushButton('Vanguard Bypass')
        self.btn_bypass.setObjectName('ActionBtn')
        self.btn_bypass.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_bypass.clicked.connect(lambda: self.button_with_loading(self.btn_bypass, 'Vanguard Bypass', self.start_bypass_logic))
        vanguard_layout.addWidget(self.btn_bypass)
        layout.addWidget(vanguard_frame)
        self.btn_popup = QPushButton('Popup Bypass')
        self.btn_popup.setObjectName('ActionBtn')
        self.btn_popup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_popup.clicked.connect(lambda: self.button_with_loading(self.btn_popup, 'Popup Bypass', self.popup_bypass_pipe))
        layout.addWidget(self.btn_popup)
        fix_frame = QFrame()
        fix_layout = QHBoxLayout(fix_frame)
        fix_layout.setContentsMargins(0, 0, 0, 0)
        fix_layout.setSpacing(5)
        self.btn_fix1 = QPushButton('Van 68 Fix #1')
        self.btn_fix1.setObjectName('ActionBtn')
        self.btn_fix1.clicked.connect(lambda: self.button_with_loading(self.btn_fix1, 'Van 68 Fix #1', self.fix_van_68_1))
        fix_layout.addWidget(self.btn_fix1)
        self.btn_fix2 = QPushButton('Van 68 Fix #2')
        self.btn_fix2.setObjectName('ActionBtn')
        self.btn_fix2.clicked.connect(lambda: self.button_with_loading(self.btn_fix2, 'Van 68 Fix #2', self.fix_van_68_2))
        fix_layout.addWidget(self.btn_fix2)
        layout.addWidget(fix_frame)
        action_frame = QFrame()
        sub = QHBoxLayout(action_frame)
        sub.setContentsMargins(0, 0, 0, 0)
        sub.setSpacing(5)
        self.btn_start = QPushButton('Exit Bypass')
        self.btn_start.setObjectName('ActionBtn')
        self.btn_start.clicked.connect(lambda: self.button_with_loading(self.btn_start, 'Exit Bypass', self.first_safe_exit_ui))
        sub.addWidget(self.btn_start)
        self.btn_exit = QPushButton('Exit Emulator')
        self.btn_exit.setObjectName('ActionBtn')
        self.btn_exit.clicked.connect(lambda: self.button_with_loading(self.btn_exit, 'Exit Emulator', self.safe_exit_ui))
        sub.addWidget(self.btn_exit)
        layout.addWidget(action_frame)
        layout.addSpacing(10)
        self.guide_type_frame = QFrame()
        guide_type_layout = QHBoxLayout(self.guide_type_frame)
        guide_type_layout.setContentsMargins(0, 0, 0, 0)
        guide_type_layout.setSpacing(5)
        guide_type_layout.addStretch(1)
        self.btn_standard_guide = QPushButton('Standard')
        self.btn_standard_guide.setObjectName('NavBtn')
        self.btn_standard_guide.setCheckable(True)
        self.btn_standard_guide.setAutoExclusive(True)
        self.btn_standard_guide.setChecked(True)
        self.btn_silent_guide = QPushButton('Silent')
        self.btn_silent_guide.setObjectName('NavBtn')
        self.btn_silent_guide.setCheckable(True)
        self.btn_silent_guide.setAutoExclusive(True)
        self.btn_popup_guide = QPushButton('Popup')
        self.btn_popup_guide.setObjectName('NavBtn')
        self.btn_popup_guide.setCheckable(True)
        self.btn_popup_guide.setAutoExclusive(True)
        guide_type_layout.addWidget(self.btn_standard_guide)
        guide_type_layout.addStretch(1)
        layout.addWidget(self.guide_type_frame)
        self.steps_container = QFrame()
        self.steps_layout = QGridLayout(self.steps_container)
        self.steps_layout.setContentsMargins(0, 5, 0, 5)
        self.steps_layout.setSpacing(5)
        self.steps_layout.setColumnStretch(0, 1)
        self.steps_layout.setColumnStretch(1, 1)
        layout.addWidget(self.steps_container)
        def clear_steps():
            if self.steps_layout.count():
                item = self.steps_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
        def show_standard_bypass():
            clear_steps()
            s1 = self.create_step('1', 'Van Bypass & Launch Game')
            s2 = self.create_step('2', 'Start match from lobby')
            s3 = self.create_step('3', '\'Match Found\' > press F6')
            s4 = self.create_step('4', 'Agent Screen > press F6')
            s5 = self.create_step('5', 'Bypass active > inject cheat')
            s6 = self.create_step('6', 'Match end > Exit Byps > repeat')
            self.steps_layout.addWidget(s1, 0, 0)
            self.steps_layout.addWidget(s2, 0, 1)
            self.steps_layout.addWidget(s3, 1, 0)
            self.steps_layout.addWidget(s4, 1, 1)
            self.steps_layout.addWidget(s5, 2, 0)
            self.steps_layout.addWidget(s6, 2, 1)
        def show_silent_bypass():
            clear_steps()
            s1 = self.create_step('1', 'Start Van Bypass')
            s2 = self.create_step('2', 'Launch Game & Enter lobby')
            s3 = self.create_step('3', 'Start match & select Agent')
            s4 = self.create_step('4', 'Bypass Activated!')
            s5 = self.create_step('5', 'Inject your cheat')
            s6 = self.create_step('6', 'End match > Exit Byps > repeat')
            self.steps_layout.addWidget(s1, 0, 0)
            self.steps_layout.addWidget(s2, 0, 1)
            self.steps_layout.addWidget(s3, 1, 0)
            self.steps_layout.addWidget(s4, 1, 1)
            self.steps_layout.addWidget(s5, 2, 0)
            self.steps_layout.addWidget(s6, 2, 1)
        def show_popup_bypass():
            clear_steps()
            s13 = self.create_step('1', 'Loading 75% > press F5')
            s14 = self.create_step('2', 'Error mid-game > F6 & close')
            s15 = self.create_step('3', 'Relaunch > 75% > F5')
            self.steps_layout.addWidget(s13, 0, 0)
            self.steps_layout.addWidget(s14, 0, 1)
            self.steps_layout.addWidget(s15, 1, 0, 1, 2)
        def show_emulator():
            clear_steps()
            s1 = self.create_step('1', 'Launch the Game')
            s2 = self.create_step('2', 'Close the Game at Round 1')
            s3 = self.create_step('3', 'Click Vanguard Emulator')
            s4 = self.create_step('4', 'Wait for Game to Relaunch')
            self.steps_layout.addWidget(s1, 0, 0)
            self.steps_layout.addWidget(s2, 0, 1)
            self.steps_layout.addWidget(s3, 1, 0)
            self.steps_layout.addWidget(s4, 1, 1)
            self.guide_type_frame.setVisible(False)
        def show_bypass():
            show_standard_bypass()
            try:
                if self.btn_standard_guide.receivers(self.btn_standard_guide.clicked) > 0:
                    self.btn_standard_guide.clicked.disconnect()
            except:
                pass
            try:
                if self.btn_silent_guide.receivers(self.btn_silent_guide.clicked) > 0:
                    self.btn_silent_guide.clicked.disconnect()
            except:
                pass
            try:
                if self.btn_popup_guide.receivers(self.btn_popup_guide.clicked) > 0:
                    self.btn_popup_guide.clicked.disconnect()
            except:
                pass
            self.btn_standard_guide.clicked.connect(show_standard_bypass)
            self.btn_silent_guide.clicked.connect(show_silent_bypass)
            self.btn_popup_guide.clicked.connect(show_popup_bypass)
            self.guide_type_frame.setVisible(True)
        def on_guide_type_changed(guide_type):
            if guide_type == 'bypass':
                show_bypass()
            else:
                self.guide_type_frame.setVisible(False)
                show_emulator()
        on_guide_type_changed('bypass')
        self.btn_bypass_guide.clicked.connect(lambda: on_guide_type_changed('bypass'))
        self.btn_emulator_guide.clicked.connect(lambda: on_guide_type_changed('emulator'))
        layout.addStretch()
        self.tab_stack.addWidget(page)
        self.setup_spoofer_page_buttons()
    def setup_spoofer_page_buttons(self):
        return None
    def button_with_loading(self, button, original_text, target_function):
        button.setEnabled(False)
        original_style = button.styleSheet()
        button.setStyleSheet('\n            QPushButton#ActionBtn {\n                background-color: #3399ff;\n                color: white;\n                border: 1px solid #3399ff;\n                border-radius: 8px;\n                padding: 10px;\n                font-size: 12px;\n                font-weight: bold;\n            }\n        ')
        button.original_text = original_text
        button.original_style = original_style
        button.setText('Loading...')
        self.loading_timer_count = 0
        self.loading_button = button
        self.loading_target_function = target_function
        QTimer.singleShot(2500, self.execute_with_loading)
    def update_progress_bar(self):
        self.loading_timer_count += 1
        progress = min(100, self.loading_timer_count * 30 // 25)
        self.progress_bar.setValue(progress)
        if progress >= 100 and self.progress_timer:
                self.progress_timer.stop()
    def execute_with_loading(self):
        try:
            if self.loading_target_function:
                self.loading_target_function()
        except Exception as e:
            print('')
        self.reset_button_state()
    def reset_button_state(self):
        if hasattr(self, 'loading_button') and self.loading_button:
                self.loading_button.setText(getattr(self.loading_button, 'original_text', ''))
                self.loading_button.setEnabled(True)
                if hasattr(self.loading_button, 'original_style'):
                    self.loading_button.setStyleSheet(self.loading_button.original_style)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)
        if hasattr(self, 'progress_timer') and self.progress_timer:
                self.progress_timer.stop()
    def clear_steps_layout(self):
        if self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
    def create_step(self, number, text):
        step_fr = QFrame()
        step_fr.setObjectName('CompactStep')
        step_fr.setMinimumHeight(60)
        step_fr.setMaximumHeight(70)
        step_lay = QVBoxLayout(step_fr)
        step_lay.setContentsMargins(10, 8, 10, 8)
        step_lay.setSpacing(4)
        number_lbl = QLabel(f'STEP {number}')
        number_lbl.setAlignment(Qt.AlignCenter)
        number_lbl.setStyleSheet('\n            QLabel {\n                color: #3399ff;\n                font-weight: bold;\n                font-size: 10px;\n                margin: 0px;\n            }\n        ')
        text_lbl = QLabel(text)
        text_lbl.setWordWrap(True)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setStyleSheet('\n            QLabel {\n                color: #a0c0ff;\n                font-size: 10px;\n                margin: 0px;\n                padding: 2px;\n            }\n        ')
        text_lbl.setMinimumHeight(40)
        step_lay.addWidget(number_lbl)
        step_lay.addWidget(text_lbl)
        return step_fr
    def toggle_start_stop(self):
        if not valorant_running:
            self.status_val.setText('STARTING VALORANT...')
            threading.Thread(target=self.start_valorant_logic, daemon=True).start()
        else:
            self.status_val.setText('STOPPING VALORANT...')
            self.safe_exit_ui()
    def start_valorant_logic(self):
        global valorant_running
        start_valorant()
        valorant_running = True
        self.status_val.setText('VALORANT RUNNING')
    def start_with_emulate_ui(self):
        if not self.show_confirmation('Emulator', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('STARTING EMULATOR...')
            threading.Thread(target=self.do_emulate_and_update, daemon=True).start()
    def do_emulate_and_update(self):
        start_with_emulate()
        self.status_val.setText('EMULATOR ACTIVE')
    def safe_exit_ui(self):
        if not self.show_confirmation('System', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('CLEAN CLOSING...')
            threading.Thread(target=self.do_safe_exit_and_update, daemon=True).start()
    def do_safe_exit_and_update(self):
        global valorant_running
        safe_exit()
        valorant_running = False
        self.status_val.setText('STOPPED')
    def create_step(self, num, text):
        f = QFrame()
        f.setObjectName('CompactStep')
        f.setFixedHeight(50)
        l = QVBoxLayout(f)
        l.setContentsMargins(8, 2, 8, 2)
        l.setSpacing(0)
        n = QLabel(f'STEP {num}')
        n.setStyleSheet('color: #3399ff; font-weight: bold; font-size: 9px; margin: 0px;')
        t = QLabel(text)
        t.setStyleSheet('color: #a0c0ff; font-size: 10px; margin: 0px;')
        t.setWordWrap(True)
        l.addWidget(n)
        l.addWidget(t)
        l.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        return f
    def show_confirmation(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setFixedSize(QSize(320, 160))
        msg_box.setStyleSheet('\n            QMessageBox {\n                background-color: #121212;\n            }\n            QLabel {\n                color: #58a6ff;\n                font-size: 12px;\n                font-weight: bold;\n                padding-left: 10px;\n                margin-top: 10px;\n            }\n            QPushButton {\n                background-color: #212121;\n                color: #cccccc;\n                border: 1px solid #333333;\n                padding: 4px 20px;\n                min-width: 60px;\n                margin-right: 10px;\n                margin-bottom: 5px;\n            }\n            QPushButton:hover {\n                background-color: #323232;\n                border: 1px solid #444444;\n                color: white;\n            }\n        ')
        reply = msg_box.exec()
        return reply == QMessageBox.StandardButton.Yes
    def start_bypass_logic(self):
        if not self.show_confirmation('Bypass', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('BYPASS')
            name = '\\\\.\\pipe\\session_0000000000004e2a'
            threading.Thread(target=self.create_bypass_pipe, args=(name,), daemon=True).start()
    def fix_van_68_1(self):
        if not self.show_confirmation('Fix #1 Control', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('FIX #1')
            name = '\\\\.\\pipe\\session_0000000000004e3a'
            threading.Thread(target=self.create_bypass_pipe, args=(name,), daemon=True).start()
    def fix_van_68_2(self):
        if not self.show_confirmation('Fix #2 Control', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('FIX #2')
            name = '\\\\.\\pipe\\session_0000000000004e4a'
            threading.Thread(target=self.create_bypass_pipe, args=(name,), daemon=True).start()
    def oneclick_spoofer_clicked(self):
        if not self.show_confirmation('Spoofer', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('ONECLICK ACTIVE')
            pipe_name = '\\\\.\\pipe\\session_0000000000004e5a'
            threading.Thread(target=self.create_bypass_pipe, args=(pipe_name,), daemon=True).start()
    def checker_clicked(self):
        if not self.show_confirmation('Checker', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('CHECKER ACTIVE')
            pipe_name = '\\\\.\\pipe\\session_0000000000004e6a'
            threading.Thread(target=self.create_bypass_pipe, args=(pipe_name,), daemon=True).start()
    def first_safe_exit_ui(self):
        if not self.show_confirmation('System', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('CLEAN CLOSING...')
            name = '\\\\.\\pipe\\session_0000000000004e7a'
            threading.Thread(target=self.create_bypass_pipe, args=(name,), daemon=True).start()
    def internal_clicked(self):
        if not self.show_confirmation('Internal', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('INTERNAL')
            pipe_name = '\\\\.\\pipe\\session_0000000000004e8a'
            threading.Thread(target=self.create_bypass_pipe, args=(pipe_name,), daemon=True).start()
    def driver_spoof_clicked(self):
        if not self.show_confirmation('Spoofer', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('DRIVER SPOOF')
            pipe_name = '\\\\.\\pipe\\session_0000000000004e9a'
            threading.Thread(target=self.create_bypass_pipe, args=(pipe_name,), daemon=True).start()
    def popup_bypass_pipe(self):
        if not self.show_confirmation('Bypass', 'Do you want to proceed?'):
            return None
        else:
            self.status_val.setText('POPUP BYPASS')
            name = '\\\\.\\pipe\\session_0000000000004e0a'
            threading.Thread(target=self.create_bypass_pipe, args=(name,), daemon=True).start()
    def create_bypass_pipe(self, pipe_name):
        import win32pipe
        import win32file
        try:
            pipe = win32pipe.CreateNamedPipe(pipe_name, win32pipe.PIPE_ACCESS_OUTBOUND, win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT, 1, 65536, 65536, 0, None)
            win32pipe.ConnectNamedPipe(pipe, None)
            win32pipe.DisconnectNamedPipe(pipe)
            win32file.CloseHandle(pipe)
        except Exception:
            return None
    def start_anim(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b'opacity')
        self.anim.setDuration(1000)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.2)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.setLoopCount((-1))
        self.anim.start()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CustomGUI()
    window.show()
    sys.exit(app.exec())