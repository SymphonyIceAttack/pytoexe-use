import sys
import json
import os
import serial

def app_dir():
    """返回 exe 所在目录（打包后）或脚本所在目录（开发时）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(filename):
    """返回打包内资源路径（临时解压目录），开发时返回脚本目录"""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class FilterRule:
    def __init__(self):
        self.delete_start = 0
        self.delete_end = 0
        self.global_find = ""
        self.global_replace = ""
        self.pos_replace = ""
        self.pos_index = 0
        self.add_start = ""
        self.add_end = ""
    
    def update_from_ui(self, delete_start_spin, delete_end_spin, global_find_edit, global_replace_edit,
                      pos_replace_edit, pos_index_spin, add_start_edit, add_end_edit):
        self.delete_start = delete_start_spin.value()
        self.delete_end = delete_end_spin.value()
        self.global_find = global_find_edit.text()
        self.global_replace = global_replace_edit.text()
        self.pos_replace = pos_replace_edit.text()
        self.pos_index = pos_index_spin.value()
        self.add_start = add_start_edit.text()
        self.add_end = add_end_edit.text()

class SerialThread(QThread):
    data_received = pyqtSignal(str)
    raw_data_received = pyqtSignal(bytes)
    
    def __init__(self, port, baud_rate, data_bits=8, parity='N', stop_bits=1, flow_control='N', parent=None):
        super().__init__(parent)
        self.port = port
        self.baud_rate = baud_rate
        self.data_bits = data_bits
        self.parity = parity
        self.stop_bits = stop_bits
        self.flow_control = flow_control
        self.ser = None
        self.running = False
    
    error_occurred = pyqtSignal(str)
    
    def run(self):
        self.running = True
        try:
            parity_map = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD, 'M': serial.PARITY_MARK, 'S': serial.PARITY_SPACE}
            stop_bits_map = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
            
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=self.data_bits,
                parity=parity_map.get(self.parity, serial.PARITY_NONE),
                stopbits=stop_bits_map.get(self.stop_bits, serial.STOPBITS_ONE),
                xonxoff=(self.flow_control == 'XON'),
                rtscts=(self.flow_control == 'RTS'),
                dsrdtr=False,
                timeout=0.1
            )
            self.data_received.emit(f"串口 {self.port} 已打开，波特率 {self.baud_rate}")
            while self.running:
                try:
                    if self.ser.in_waiting > 0:
                        raw_data = self.ser.read(self.ser.in_waiting)
                        self.raw_data_received.emit(raw_data)
                except Exception as e:
                    self.error_occurred.emit(f"读取错误: {str(e)}")
        except Exception as e:
            error_msg = f"串口错误: {str(e)}"
            self.error_occurred.emit(error_msg)
        finally:
            if self.ser:
                try:
                    self.ser.close()
                except:
                    pass
    
    def stop(self):
        self.running = False
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
    
    def write_data(self, data):
        if self.ser and self.ser.is_open:
            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                self.ser.write(data)
                self.ser.flush()
            except Exception as e:
                pass

class OutputPortWidget(QWidget):
    log_signal = pyqtSignal(str)
    config_changed = pyqtSignal()

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.filter_rule = FilterRule()
        self.serial_thread = None
        self.init_ui()
        self.update_rule()
    
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        font = QFont()
        font.setPointSize(10)
        
        left_layout = QFormLayout()
        left_layout.setVerticalSpacing(6)
        left_layout.setHorizontalSpacing(8)
        
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(120)
        self.port_combo.setFont(font)
        self.update_ports(self.port_combo)
        left_layout.addRow("串口:", self.port_combo)
        
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("9600")
        self.baud_combo.setMinimumWidth(100)
        self.baud_combo.setFont(font)
        left_layout.addRow("波特率:", self.baud_combo)
        
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        self.data_bits_combo.setMinimumWidth(60)
        self.data_bits_combo.setFont(font)
        left_layout.addRow("数据位:", self.data_bits_combo)
        
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["无(N)", "偶校验(E)", "奇校验(O)", "标记(M)", "空格(S)"])
        self.parity_combo.setCurrentIndex(0)
        self.parity_combo.setMinimumWidth(80)
        self.parity_combo.setFont(font)
        left_layout.addRow("校验位:", self.parity_combo)
        
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")
        self.stop_bits_combo.setMinimumWidth(60)
        self.stop_bits_combo.setFont(font)
        left_layout.addRow("停止位:", self.stop_bits_combo)
        
        self.flow_control_combo = QComboBox()
        self.flow_control_combo.addItems(["无(N)", "RTS/CTS", "XON/XOFF"])
        self.flow_control_combo.setCurrentIndex(0)
        self.flow_control_combo.setMinimumWidth(80)
        self.flow_control_combo.setFont(font)
        left_layout.addRow("流控制:", self.flow_control_combo)
        
        self.start_button = QPushButton("开始")
        self.start_button.setFont(font)
        self.start_button.setMinimumWidth(60)
        self.start_button.clicked.connect(self.toggle_serial)
        left_layout.addRow("", self.start_button)

        self.enable_checkbox = QCheckBox("启用（自动启动）")
        self.enable_checkbox.setFont(font)
        self.enable_checkbox.stateChanged.connect(self.config_changed)
        left_layout.addRow("", self.enable_checkbox)
        
        layout.addLayout(left_layout)
        
        mid_line = QFrame()
        mid_line.setFrameShape(QFrame.VLine)
        mid_line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(mid_line)
        
        right_layout = QFormLayout()
        right_layout.setVerticalSpacing(6)
        right_layout.setHorizontalSpacing(8)

        self.delete_start_spin = QSpinBox()
        self.delete_start_spin.setRange(0, 100)
        self.delete_start_spin.setValue(0)
        self.delete_start_spin.setFont(font)
        self.delete_start_spin.setFixedWidth(120)
        right_layout.addRow("删除起始:", self.delete_start_spin)

        self.delete_end_spin = QSpinBox()
        self.delete_end_spin.setRange(0, 100)
        self.delete_end_spin.setValue(0)
        self.delete_end_spin.setFont(font)
        self.delete_end_spin.setFixedWidth(120)
        right_layout.addRow("删除末尾:", self.delete_end_spin)

        self.global_find_edit = QLineEdit()
        self.global_find_edit.setFont(font)
        self.global_find_edit.setFixedWidth(100)
        self.global_replace_edit = QLineEdit()
        self.global_replace_edit.setFont(font)
        self.global_replace_edit.setFixedWidth(100)
        find_widget = QWidget()
        find_layout = QHBoxLayout(find_widget)
        find_layout.setContentsMargins(0, 0, 0, 0)
        find_layout.addWidget(self.global_find_edit)
        find_layout.addWidget(QLabel("替换为:"))
        find_layout.addWidget(self.global_replace_edit)
        right_layout.addRow("查找:", find_widget)

        self.pos_replace_edit = QLineEdit()
        self.pos_replace_edit.setFont(font)
        self.pos_replace_edit.setFixedWidth(100)
        self.pos_replace_index_spin = QSpinBox()
        self.pos_replace_index_spin.setRange(0, 1000)
        self.pos_replace_index_spin.setValue(0)
        self.pos_replace_index_spin.setFont(font)
        self.pos_replace_index_spin.setFixedWidth(100)
        pos_widget = QWidget()
        pos_layout = QHBoxLayout(pos_widget)
        pos_layout.setContentsMargins(0, 0, 0, 0)
        pos_layout.addWidget(self.pos_replace_edit)
        pos_layout.addWidget(QLabel("位置:"))
        pos_layout.addWidget(self.pos_replace_index_spin)
        right_layout.addRow("替换:", pos_widget)

        self.add_start_edit = QLineEdit()
        self.add_start_edit.setFont(font)
        self.add_start_edit.setFixedWidth(120)
        right_layout.addRow("添加起始:", self.add_start_edit)

        self.add_end_edit = QLineEdit()
        self.add_end_edit.setFont(font)
        self.add_end_edit.setFixedWidth(120)
        right_layout.addRow("添加末尾:", self.add_end_edit)
        
        layout.addLayout(right_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
        self.delete_start_spin.valueChanged.connect(self.update_rule)
        self.delete_end_spin.valueChanged.connect(self.update_rule)
        self.global_find_edit.textChanged.connect(self.update_rule)
        self.global_replace_edit.textChanged.connect(self.update_rule)
        self.pos_replace_edit.textChanged.connect(self.update_rule)
        self.pos_replace_index_spin.valueChanged.connect(self.update_rule)
        self.add_start_edit.textChanged.connect(self.update_rule)
        self.add_end_edit.textChanged.connect(self.update_rule)

        for w in [self.port_combo, self.baud_combo, self.data_bits_combo,
                  self.parity_combo, self.stop_bits_combo, self.flow_control_combo]:
            w.currentIndexChanged.connect(self.config_changed)
        for w in [self.delete_start_spin, self.delete_end_spin, self.pos_replace_index_spin]:
            w.valueChanged.connect(self.config_changed)
        for w in [self.global_find_edit, self.global_replace_edit,
                  self.pos_replace_edit, self.add_start_edit, self.add_end_edit]:
            w.textChanged.connect(self.config_changed)
        
        self.update_rule()
    
    def update_rule(self):
        self.filter_rule.update_from_ui(
            self.delete_start_spin, self.delete_end_spin,
            self.global_find_edit, self.global_replace_edit,
            self.pos_replace_edit, self.pos_replace_index_spin,
            self.add_start_edit, self.add_end_edit
        )
    
    def update_ports(self, combo_box):
        port_list = []
        port_set = set()
        
        try:
            import winreg
            
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    if value and value not in port_set:
                        port_set.add(value)
                        port_list.append(value)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
        
        if not port_set:
            try:
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    try:
                        device = port.device
                        if device and device not in port_set:
                            port_set.add(device)
                            desc = ""
                            if hasattr(port, 'description') and port.description:
                                desc = str(port.description)
                            elif hasattr(port, 'hwid') and port.hwid:
                                desc = str(port.hwid)
                            
                            desc = desc.replace('\n', ' ').replace('\r', ' ').strip()
                            desc = ''.join(filter(lambda x: x.isprintable(), desc)).strip()
                            
                            if len(desc) > 50:
                                desc = desc[:50] + "..."
                            
                            if desc and desc != device:
                                port_list.append(f"{device} - {desc}")
                            else:
                                port_list.append(device)
                    except:
                        pass
            except Exception:
                pass
        
        current = combo_box.currentText()
        combo_box.clear()
        
        if port_list:
            combo_box.addItems(port_list)
            if current and any(current in p for p in port_list):
                combo_box.setCurrentText(current)
        else:
            combo_box.addItem("未找到串口设备")
    
    def send_data(self, data):
        if self.start_button.text() != "停止":
            return
        
        delete_start = self.delete_start_spin.value()
        delete_end = self.delete_end_spin.value()
        global_find = self.global_find_edit.text()
        global_replace = self.global_replace_edit.text()
        pos_replace = self.pos_replace_edit.text()
        pos_index = self.pos_replace_index_spin.value()
        add_start = self.add_start_edit.text()
        add_end = self.add_end_edit.text()
        
        if isinstance(data, str):
            data = data.encode('latin-1')
        
        # 分离控制符和可打印字节，记录控制符原始位置
        controls_before = bytearray()  # 数据前的控制符
        controls_after = bytearray()   # 数据后的控制符
        visible = bytearray()
        reached_visible = False
        tail_controls = bytearray()
        
        for b in data:
            if 0x20 <= b <= 0x7E:
                if tail_controls:
                    # 之前积累的控制符夹在可打印字节中间，暂归入visible处理后区域
                    visible.extend(tail_controls)
                    tail_controls = bytearray()
                visible.append(b)
                reached_visible = True
            else:
                if not reached_visible:
                    controls_before.append(b)
                else:
                    tail_controls.append(b)
        controls_after = tail_controls

        # 删除起始/末尾可打印字节
        if delete_start > 0:
            del visible[:delete_start]
        if delete_end > 0 and delete_end <= len(visible):
            del visible[-delete_end:]

        # 全局查找替换（global_replace 为空表示删除）
        if global_find:
            find_bytes = global_find.encode('latin-1')
            rep_bytes = global_replace.encode('latin-1') if global_replace else b''
            visible = bytearray(bytes(visible).replace(find_bytes, rep_bytes))

        # 位置替换（1-based，作用于可打印区）
        if pos_replace and 0 < pos_index <= len(visible):
            idx = pos_index - 1
            rep = pos_replace.encode('latin-1')
            visible[idx:idx + len(rep)] = rep

        # 添加起始/末尾
        if add_start:
            visible[:0] = add_start.encode('latin-1')
        if add_end:
            visible.extend(add_end.encode('latin-1'))

        # 控制符归位：前控制符 + 可打印数据 + 后控制符
        result = bytes(controls_before) + bytes(visible) + bytes(controls_after)
        
        ASCII_CTRL = {
            0x00:'NUL',0x01:'SOH',0x02:'STX',0x03:'ETX',0x04:'EOT',0x05:'ENQ',
            0x06:'ACK',0x07:'BEL',0x08:'BS', 0x09:'HT', 0x0A:'LF', 0x0B:'VT',
            0x0C:'FF', 0x0D:'CR', 0x0E:'SO', 0x0F:'SI', 0x10:'DLE',0x11:'DC1',
            0x12:'DC2',0x13:'DC3',0x14:'DC4',0x15:'NAK',0x16:'SYN',0x17:'ETB',
            0x18:'CAN',0x19:'EM', 0x1A:'SUB',0x1B:'ESC',0x1C:'FS', 0x1D:'GS',
            0x1E:'RS', 0x1F:'US', 0x7F:'DEL'
        }
        hex_str = ' '.join(f'{b:02X}' for b in result)
        ascii_str = ''.join(chr(b) if 0x20 <= b <= 0x7E else f'[{ASCII_CTRL.get(b, f"{b:02X}")}]' for b in result)
        port_text = self.port_combo.currentText().split(' - ')[0]
        self.log_signal.emit(f"输出[{port_text}] HEX: {hex_str}")
        self.log_signal.emit(f"输出[{port_text}] TXT: {ascii_str}")

        if self.serial_thread and self.serial_thread.isRunning():
            try:
                self.serial_thread.write_data(result)
            except Exception as e:
                pass
    
    def toggle_serial(self):
        if self.start_button.text() == "开始":
            self.start_serial()
        else:
            self.stop_serial()
    
    def start_serial(self):
        port_text = self.port_combo.currentText()
        port = port_text.split(' - ')[0] if ' - ' in port_text else port_text
        baud = int(self.baud_combo.currentText())
        data_bits = int(self.data_bits_combo.currentText())
            
        parity_text = self.parity_combo.currentText()
        if "偶校验" in parity_text:
            parity = 'E'
        elif "奇校验" in parity_text:
            parity = 'O'
        elif "标记" in parity_text:
            parity = 'M'
        elif "空格" in parity_text:
            parity = 'S'
        else:
            parity = 'N'
            
        stop_bits = float(self.stop_bits_combo.currentText())
            
        flow_text = self.flow_control_combo.currentText()
        if "RTS" in flow_text:
            flow_control = 'RTS'
        elif "XON" in flow_text:
            flow_control = 'XON'
        else:
            flow_control = 'N'
            
        self.serial_thread = SerialThread(port, baud, data_bits, parity, stop_bits, flow_control)
        self.serial_thread.error_occurred.connect(lambda msg: self.start_button.setText("开始"))
        self.serial_thread.start()
        self.start_button.setText("停止")
    
    def stop_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait()
            self.serial_thread = None
        self.start_button.setText("开始")

class MainWindow(QMainWindow):
    CONFIG_FILE = os.path.join(app_dir(), 'config.json')

    def __init__(self):
        super().__init__()
        self.setWindowTitle("串口一拖N、字符过滤__WPython__20260429")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(900, 600)
        
        self.input_serial = None
        
        self.init_ui()
        self._init_tray()
        self.load_config()
        # 延迟自动启动，确保窗口完全显示后再连接串口
        QTimer.singleShot(500, self.auto_start)

    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        ico_path = resource_path('app.ico')
        if os.path.exists(ico_path):
            icon = QIcon(ico_path)
        else:
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)
        self.tray_icon.setToolTip(self.windowTitle())

        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self._show_from_tray)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_from_tray()

    def _quit_app(self):
        self.save_config()
        self.stop_serial()
        QApplication.quit()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.gui_output_widgets = []
        self.brm_output_widgets = []
        self.other_output_widgets = []
        
        main_tabs = QTabWidget()
        
        input_tab = QWidget()
        input_layout = QHBoxLayout(input_tab)
        
        font = QFont()
        font.setPointSize(10)
        
        left_layout = QFormLayout()
        left_layout.setVerticalSpacing(6)
        left_layout.setHorizontalSpacing(8)
        
        self.input_port_combo = QComboBox()
        self.input_port_combo.setEditable(True)
        self.input_port_combo.setMinimumWidth(150)
        self.input_port_combo.setFont(font)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.input_port_combo)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setFont(font)
        self.refresh_button.setMinimumWidth(60)
        self.refresh_button.clicked.connect(self.update_ports)
        port_layout.addWidget(self.refresh_button)
        left_layout.addRow("串口:", port_layout)
        
        self.input_baud_combo = QComboBox()
        self.input_baud_combo.addItems(["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.input_baud_combo.setCurrentText("9600")
        self.input_baud_combo.setMinimumWidth(120)
        self.input_baud_combo.setFont(font)
        left_layout.addRow("波特率:", self.input_baud_combo)
        
        self.input_data_bits_combo = QComboBox()
        self.input_data_bits_combo.addItems(["5", "6", "7", "8"])
        self.input_data_bits_combo.setCurrentText("8")
        self.input_data_bits_combo.setMinimumWidth(80)
        self.input_data_bits_combo.setFont(font)
        left_layout.addRow("数据位:", self.input_data_bits_combo)
        
        self.input_parity_combo = QComboBox()
        self.input_parity_combo.addItems(["无(N)", "偶校验(E)", "奇校验(O)", "标记(M)", "空格(S)"])
        self.input_parity_combo.setCurrentIndex(0)
        self.input_parity_combo.setMinimumWidth(100)
        self.input_parity_combo.setFont(font)
        left_layout.addRow("校验位:", self.input_parity_combo)
        
        self.input_stop_bits_combo = QComboBox()
        self.input_stop_bits_combo.addItems(["1", "1.5", "2"])
        self.input_stop_bits_combo.setCurrentText("1")
        self.input_stop_bits_combo.setMinimumWidth(80)
        self.input_stop_bits_combo.setFont(font)
        left_layout.addRow("停止位:", self.input_stop_bits_combo)
        
        self.input_flow_control_combo = QComboBox()
        self.input_flow_control_combo.addItems(["无(N)", "RTS/CTS", "XON/XOFF"])
        self.input_flow_control_combo.setCurrentIndex(0)
        self.input_flow_control_combo.setMinimumWidth(100)
        self.input_flow_control_combo.setFont(font)
        left_layout.addRow("流控制:", self.input_flow_control_combo)
        
        self.start_button = QPushButton("开始")
        self.start_button.setFont(font)
        self.start_button.setMinimumWidth(80)
        self.start_button.clicked.connect(self.toggle_serial)
        left_layout.addRow("", self.start_button)

        self.input_enable_checkbox = QCheckBox("启用（自动启动）")
        self.input_enable_checkbox.setFont(font)
        self.input_enable_checkbox.stateChanged.connect(self.save_config)
        left_layout.addRow("", self.input_enable_checkbox)

        self.autorun_checkbox = QCheckBox("开机自启动")
        self.autorun_checkbox.setFont(font)
        self.autorun_checkbox.setChecked(self.is_autorun())
        self.autorun_checkbox.stateChanged.connect(lambda state: self.set_autorun(state == Qt.Checked))
        left_layout.addRow("", self.autorun_checkbox)
        
        input_layout.addLayout(left_layout)
        
        mid_line = QFrame()
        mid_line.setFrameShape(QFrame.VLine)
        mid_line.setFrameShadow(QFrame.Sunken)
        input_layout.addWidget(mid_line)
        
        right_placeholder = QVBoxLayout()
        right_placeholder.addStretch()
        input_layout.addLayout(right_placeholder)
        
        input_layout.addStretch()
        
        main_tabs.addTab(input_tab, "输入页")
        
        output_tab = QWidget()
        output_tab_layout = QVBoxLayout(output_tab)
        
        output_tabs = QTabWidget()
        
        gui_tab = QWidget()
        gui_layout = QVBoxLayout(gui_tab)
        
        self.gui_output_scroll = QScrollArea()
        self.gui_output_scroll.setWidgetResizable(True)
        self.gui_output_container = QWidget()
        self.gui_output_layout = QVBoxLayout(self.gui_output_container)
        self.gui_output_scroll.setWidget(self.gui_output_container)
        gui_layout.addWidget(self.gui_output_scroll)
        
        output_tabs.addTab(gui_tab, "GUI")
        
        brm_tab = QWidget()
        brm_layout = QVBoxLayout(brm_tab)
        
        self.brm_output_scroll = QScrollArea()
        self.brm_output_scroll.setWidgetResizable(True)
        self.brm_output_container = QWidget()
        self.brm_output_layout = QVBoxLayout(self.brm_output_container)
        self.brm_output_scroll.setWidget(self.brm_output_container)
        brm_layout.addWidget(self.brm_output_scroll)
        
        output_tabs.addTab(brm_tab, "BRM")
        
        other_tab = QWidget()
        other_layout = QVBoxLayout(other_tab)
        
        other_count_layout = QHBoxLayout()
        other_count_label = QLabel("输出端口数量:")
        other_count_label.setFont(font)
        other_count_layout.addWidget(other_count_label)
        self.other_output_count_spin = QSpinBox()
        self.other_output_count_spin.setFont(font)
        self.other_output_count_spin.setRange(0, 20)
        self.other_output_count_spin.setValue(0)
        self.other_output_count_spin.setMaximumWidth(60)
        self.other_output_count_spin.valueChanged.connect(lambda: self.update_output_count('other'))
        other_count_layout.addWidget(self.other_output_count_spin)
        other_count_layout.addStretch()
        other_layout.addLayout(other_count_layout)
        
        self.other_output_scroll = QScrollArea()
        self.other_output_scroll.setWidgetResizable(True)
        self.other_output_container = QWidget()
        self.other_output_layout = QVBoxLayout(self.other_output_container)
        self.other_output_scroll.setWidget(self.other_output_container)
        other_layout.addWidget(self.other_output_scroll)
        
        output_tabs.addTab(other_tab, "Other")
        
        output_tab_layout.addWidget(output_tabs)
        
        main_tabs.addTab(output_tab, "输出页")
        
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        
        main_tabs.addTab(log_tab, "日志")
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(main_tabs)
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        self.update_ports()
        
        self.update_output_count('gui')
        self.update_output_count('brm')
        self.update_output_count('other')

        # 输入页控件变化时立即保存 config
        for w in [self.input_port_combo, self.input_baud_combo,
                  self.input_data_bits_combo, self.input_parity_combo,
                  self.input_stop_bits_combo, self.input_flow_control_combo]:
            w.currentIndexChanged.connect(self.save_config)
            if hasattr(w, 'editTextChanged'):
                w.editTextChanged.connect(self.save_config)
        self.other_output_count_spin.valueChanged.connect(self.save_config)
    
    def update_ports(self):
        port_list = []
        port_set = set()
        
        try:
            import winreg
            
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    if value and value not in port_set:
                        port_set.add(value)
                        port_list.append(value)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
        
        if not port_set:
            try:
                ports = serial.tools.list_ports.comports()
                for port in ports:
                    try:
                        device = port.device
                        if device and device not in port_set:
                            port_set.add(device)
                            port_list.append(device)
                    except:
                        pass
            except Exception:
                pass
        
        current = self.input_port_combo.currentText()
        self.input_port_combo.clear()
        
        if port_list:
            self.input_port_combo.addItems(port_list)
            if current and any(current in p for p in port_list):
                self.input_port_combo.setCurrentText(current)
        else:
            self.input_port_combo.addItem("未找到串口设备")
        
        for widget in self.gui_output_widgets + self.brm_output_widgets + self.other_output_widgets:
            current_out = widget.port_combo.currentText()
            widget.port_combo.clear()
            if port_list:
                widget.port_combo.addItems(port_list)
                if current_out and any(current_out in p for p in port_list):
                    widget.port_combo.setCurrentText(current_out)
            else:
                widget.port_combo.addItem("未找到串口设备")
        
        if hasattr(self, 'log_text'):
            self.add_log(f"已扫描到 {len(port_set)} 个串口设备")
    
    def update_output_count(self, tab):
        if tab == 'gui':
            count = 1  # GUI固定1个端口
            widgets = self.gui_output_widgets
            layout = self.gui_output_layout
            max_index = 1000
        elif tab == 'brm':
            count = 1  # BRM固定1个端口
            widgets = self.brm_output_widgets
            layout = self.brm_output_layout
            max_index = 2000
        else:
            count = self.other_output_count_spin.value()
            widgets = self.other_output_widgets
            layout = self.other_output_layout
            max_index = 3000
        
        current_count = len(widgets)
        
        if count > current_count:
            for i in range(current_count, count):
                widget = OutputPortWidget(max_index + i)
                widget.log_signal.connect(self.add_log)
                widget.config_changed.connect(self.save_config)
                widgets.append(widget)
                layout.addWidget(widget)
        elif count < current_count:
            for i in range(current_count - 1, count - 1, -1):
                widget = widgets.pop()
                widget.setParent(None)
    
    def toggle_serial(self):
        if self.start_button.text() == "开始":
            self.start_serial()
        else:
            self.stop_serial()
    
    def start_serial(self):
        input_port_text = self.input_port_combo.currentText()
        input_port = input_port_text.split(' - ')[0] if ' - ' in input_port_text else input_port_text
        input_baud = int(self.input_baud_combo.currentText())
        input_data_bits = int(self.input_data_bits_combo.currentText())
        
        parity_text = self.input_parity_combo.currentText()
        if "偶校验" in parity_text:
            input_parity = 'E'
        elif "奇校验" in parity_text:
            input_parity = 'O'
        elif "标记" in parity_text:
            input_parity = 'M'
        elif "空格" in parity_text:
            input_parity = 'S'
        else:
            input_parity = 'N'
        
        input_stop_bits = float(self.input_stop_bits_combo.currentText())
        
        flow_text = self.input_flow_control_combo.currentText()
        if "RTS" in flow_text:
            input_flow_control = 'RTS'
        elif "XON" in flow_text:
            input_flow_control = 'XON'
        else:
            input_flow_control = 'N'
        
        self.input_serial = SerialThread(input_port, input_baud, input_data_bits, input_parity, input_stop_bits, input_flow_control)
        self.input_serial.data_received.connect(self.handle_input_data)
        self.input_serial.raw_data_received.connect(self.handle_raw_data)
        self.input_serial.error_occurred.connect(self.add_log)
        self.input_serial.start()
        
        self.start_button.setText("停止")
        self.status_bar.showMessage("运行中")
        self.add_log("串口通信已启动")
    
    def stop_serial(self):
        if self.input_serial:
            self.input_serial.stop()
            self.input_serial.wait()
            self.input_serial = None
        
        for widget in self.gui_output_widgets + self.brm_output_widgets + self.other_output_widgets:
            widget.stop_serial()
        
        self.start_button.setText("开始")
        self.status_bar.showMessage("已停止")
        self.add_log("串口通信已停止")
    
    def handle_input_data(self, data):
        pass  # 数据已在 handle_raw_data 中记录
    
    def handle_raw_data(self, raw_data):
        ASCII_CTRL = {
            0x00:'NUL',0x01:'SOH',0x02:'STX',0x03:'ETX',0x04:'EOT',0x05:'ENQ',
            0x06:'ACK',0x07:'BEL',0x08:'BS', 0x09:'HT', 0x0A:'LF', 0x0B:'VT',
            0x0C:'FF', 0x0D:'CR', 0x0E:'SO', 0x0F:'SI', 0x10:'DLE',0x11:'DC1',
            0x12:'DC2',0x13:'DC3',0x14:'DC4',0x15:'NAK',0x16:'SYN',0x17:'ETB',
            0x18:'CAN',0x19:'EM', 0x1A:'SUB',0x1B:'ESC',0x1C:'FS', 0x1D:'GS',
            0x1E:'RS', 0x1F:'US', 0x7F:'DEL'
        }
        hex_str = ' '.join(f'{b:02X}' for b in raw_data)
        ascii_str = ''.join(chr(b) if 0x20 <= b <= 0x7E else f'[{ASCII_CTRL.get(b, f"{b:02X}")}]' for b in raw_data)
        self.add_log(f"输入 HEX: {hex_str}")
        self.add_log(f"输入 TXT: {ascii_str}")
        
        for widget in self.gui_output_widgets + self.brm_output_widgets + self.other_output_widgets:
            if widget.start_button.text() == "停止":
                widget.send_data(raw_data)
    
    def write_log_file(self, message):
        now = QDateTime.currentDateTime()
        base = app_dir()
        folder = os.path.join(base, 'Log',
                              now.toString('yyyy-MM-dd'))
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, now.toString('yyyy-MM-dd-HH') + '.txt')
        timestamp = now.toString('yyyy-MM-dd HH:mm:ss.zzz')
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(timestamp + ' ' + message + '\n')
        except Exception:
            pass

    def add_log(self, message):
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.log_text.moveCursor(self.log_text.textCursor().End)
        self.log_text.insertPlainText(timestamp + " " + message + "\n")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        self.write_log_file(message)
    
    def save_config(self):
        def widget_cfg(w):
            return {
                'port': w.port_combo.currentText(),
                'baud': w.baud_combo.currentText(),
                'data_bits': w.data_bits_combo.currentText(),
                'parity': w.parity_combo.currentText(),
                'stop_bits': w.stop_bits_combo.currentText(),
                'flow_control': w.flow_control_combo.currentText(),
                'delete_start': w.delete_start_spin.value(),
                'delete_end': w.delete_end_spin.value(),
                'global_find': w.global_find_edit.text(),
                'global_replace': w.global_replace_edit.text(),
                'pos_replace': w.pos_replace_edit.text(),
                'pos_index': w.pos_replace_index_spin.value(),
                'add_start': w.add_start_edit.text(),
                'add_end': w.add_end_edit.text(),
                'enabled': w.enable_checkbox.isChecked(),
            }
        cfg = {
            'input': {
                'port': self.input_port_combo.currentText(),
                'baud': self.input_baud_combo.currentText(),
                'data_bits': self.input_data_bits_combo.currentText(),
                'parity': self.input_parity_combo.currentText(),
                'stop_bits': self.input_stop_bits_combo.currentText(),
                'flow_control': self.input_flow_control_combo.currentText(),
                'enabled': self.input_enable_checkbox.isChecked(),
            },
            'other_count': self.other_output_count_spin.value(),
            'gui': [widget_cfg(w) for w in self.gui_output_widgets],
            'brm': [widget_cfg(w) for w in self.brm_output_widgets],
            'other': [widget_cfg(w) for w in self.other_output_widgets],
        }
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.add_log(f"保存配置失败: {e}")

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE):
            return
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception as e:
            self.add_log(f"加载配置失败: {e}")
            return

        def restore_combo(combo, value):
            idx = combo.findText(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.setCurrentText(value)

        inp = cfg.get('input', {})
        restore_combo(self.input_port_combo, inp.get('port', ''))
        restore_combo(self.input_baud_combo, inp.get('baud', '9600'))
        restore_combo(self.input_data_bits_combo, inp.get('data_bits', '8'))
        restore_combo(self.input_parity_combo, inp.get('parity', '无(N)'))
        restore_combo(self.input_stop_bits_combo, inp.get('stop_bits', '1'))
        restore_combo(self.input_flow_control_combo, inp.get('flow_control', '无(N)'))

        other_count = cfg.get('other_count', 1)
        self.other_output_count_spin.setValue(other_count)

        def restore_widget(w, c):
            restore_combo(w.port_combo, c.get('port', ''))
            restore_combo(w.baud_combo, c.get('baud', '9600'))
            restore_combo(w.data_bits_combo, c.get('data_bits', '8'))
            restore_combo(w.parity_combo, c.get('parity', '无(N)'))
            restore_combo(w.stop_bits_combo, c.get('stop_bits', '1'))
            restore_combo(w.flow_control_combo, c.get('flow_control', '无(N)'))
            w.delete_start_spin.setValue(c.get('delete_start', 0))
            w.delete_end_spin.setValue(c.get('delete_end', 0))
            w.global_find_edit.setText(c.get('global_find', ''))
            w.global_replace_edit.setText(c.get('global_replace', ''))
            w.pos_replace_edit.setText(c.get('pos_replace', ''))
            w.pos_replace_index_spin.setValue(c.get('pos_index', 0))
            w.add_start_edit.setText(c.get('add_start', ''))
            w.add_end_edit.setText(c.get('add_end', ''))
            w.enable_checkbox.setChecked(c.get('enabled', False))

        for w, c in zip(self.gui_output_widgets, cfg.get('gui', [])):
            restore_widget(w, c)
        for w, c in zip(self.brm_output_widgets, cfg.get('brm', [])):
            restore_widget(w, c)
        for w, c in zip(self.other_output_widgets, cfg.get('other', [])):
            restore_widget(w, c)

        # 记录需要自动启动的状态，由 auto_start 执行
        self._auto_start_input = inp.get('enabled', False)
        self._auto_start_outputs = {
            'gui': [c.get('enabled', False) for c in cfg.get('gui', [])],
            'brm': [c.get('enabled', False) for c in cfg.get('brm', [])],
            'other': [c.get('enabled', False) for c in cfg.get('other', [])],
        }
        self.input_enable_checkbox.setChecked(self._auto_start_input)

    def auto_start(self):
        if not hasattr(self, '_auto_start_input'):
            return
        for w, run in zip(self.gui_output_widgets, self._auto_start_outputs.get('gui', [])):
            if run:
                w.start_serial()
        for w, run in zip(self.brm_output_widgets, self._auto_start_outputs.get('brm', [])):
            if run:
                w.start_serial()
        for w, run in zip(self.other_output_widgets, self._auto_start_outputs.get('other', [])):
            if run:
                w.start_serial()
        if self._auto_start_input:
            self.start_serial()

    def set_autorun(self, enable):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            if enable:
                winreg.SetValueEx(key, "SerialFilter", 0, winreg.REG_SZ, f'"{app_path}"')
                self.add_log("已设置开机自启动")
            else:
                try:
                    winreg.DeleteValue(key, "SerialFilter")
                    self.add_log("已取消开机自启动")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.add_log(f"设置自启动失败: {e}")

    def is_autorun(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "SerialFilter")
            winreg.CloseKey(key)
            return True
        except:
            return False

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            self.windowTitle(), "程序已最小化到托盘，双击图标恢复",
            QSystemTrayIcon.Information, 2000
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())