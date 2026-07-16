import sys
import struct
import math
import time
import threading
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import List, Dict, Optional

import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit,
    QGroupBox, QGridLayout, QMessageBox, QFileDialog,
    QCheckBox, QSpinBox, QTabWidget, QScrollArea, QFrame
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThreadPool, QRunnable, pyqtSlot
from PyQt5.QtGui import QFont, QColor

# ==================== 配置参数 ====================
BAUDRATE = 460800
DATA_BITS = 8
STOP_BITS = 1
PARITY = 'N'

SENSOR_NUM = 6
PER_SENSOR_LEN = 12
FRAME_HEADER = 0xAA
FRAME_LENGTH = 1 + SENSOR_NUM * PER_SENSOR_LEN
FLUSH_INTERVAL = 50

OUTPUT_DIR = './sensor_data'
MAX_SERIAL_PORTS = 16  # 最大串口数量限制


def decode_24bit_signed(raw_value: int) -> int:
    """将32位无符号整数中的低24位，解析为有符号24位整数"""
    val = raw_value & 0xFFFFFF
    if val & 0x800000:
        val -= 0x1000000
    return val


# ==================== 帧解析器 ====================
class FrameParser:
    """6通道帧解析器"""
    def __init__(self):
        self.buffer = bytearray()

    def parse(self, raw_data: bytes) -> list:
        frames = []
        self.buffer.extend(raw_data)

        while len(self.buffer) >= FRAME_LENGTH:
            if self.buffer[0] != FRAME_HEADER:
                self.buffer.pop(0)
                continue

            frame_bytes = self.buffer[:FRAME_LENGTH]
            self.buffer = self.buffer[FRAME_LENGTH:]

            try:
                sensor_data = []
                offset = 1
                for _ in range(SENSOR_NUM):
                    d1, d2 = struct.unpack('>2I', frame_bytes[offset:offset+8])
                    (d3_raw,) = struct.unpack('>I', frame_bytes[offset+8:offset+12])
                    d3 = decode_24bit_signed(d3_raw)
                    sensor_data.append((d1, d2, d3))
                    offset += PER_SENSOR_LEN

                ts = time.time_ns()
                frames.append((ts, sensor_data))
            except struct.error:
                continue

        return frames


# ==================== SQLite数据库写入器 ====================
class SQLiteWriter:
    """每个串口独立的SQLite数据库写入器"""
    
    def __init__(self, output_dir=OUTPUT_DIR, port_name="", sensor_configs=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 传感器配置：[(id, enabled), ...]
        if sensor_configs is None or len(sensor_configs) != SENSOR_NUM:
            self.sensor_configs = [(f'S{i+1}', True) for i in range(SENSOR_NUM)]
        else:
            self.sensor_configs = sensor_configs
        
        # 生成数据库文件名（包含串口信息）
        safe_port = port_name.replace('/', '_').replace(':', '')
        filename = datetime.now().strftime(f'%Y-%m-%d_%H-%M-%S') + f'_{safe_port}_sensor.db'
        self.db_path = self.output_dir / filename
        self.conn = None
        self.cursor = None
        self.frame_count = 0
        self.batch_data = []
        self.batch_size = 100
        
        self._init_database()
    
    def _init_database(self):
        try:
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # 创建元数据表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT
                )
            ''')
            
            # 保存传感器配置
            for i, (sensor_id, enabled) in enumerate(self.sensor_configs):
                self.cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', (f'sensor_{i+1}_id', sensor_id if enabled else 'DISABLED'))
                self.cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', (f'sensor_{i+1}_enabled', str(enabled)))
            
            # 创建数据表
            columns = []
            for i, (sensor_id, enabled) in enumerate(self.sensor_configs):
                if enabled:
                    columns.extend([
                        f'"{sensor_id}_D1" REAL',
                        f'"{sensor_id}_D2" REAL',
                        f'"{sensor_id}_D3" REAL'
                    ])
            
            if not columns:
                columns = ['dummy INTEGER DEFAULT 0']
            
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_ns INTEGER NOT NULL,
                    timestamp_iso TEXT NOT NULL,
                    {', '.join(columns)}
                )
            '''
            self.cursor.execute(create_table_sql)
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON sensor_data(timestamp_ns)
            ''')
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value) 
                VALUES (?, ?)
            ''', ('start_time', datetime.now().isoformat()))
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO metadata (key, value) 
                VALUES (?, ?)
            ''', ('sensor_count', str(SENSOR_NUM)))
            
            self.conn.commit()
            
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise
    
    def write(self, frames: list):
        for ts, sensor_raw_list in frames:
            display_values = []
            for i, (d1_raw, d2_raw, d3_raw) in enumerate(sensor_raw_list):
                if self.sensor_configs[i][1]:
                    d1 = round(1000 * math.sqrt(d1_raw) / 512, 6)
                    d2 = round(1000 * math.sqrt(d2_raw) / 512, 6)
                    d3 = round(d3_raw * 0.00010464 - 51.455, 6)
                    display_values.extend([d1, d2, d3])
            
            self.batch_data.append((
                ts,
                datetime.fromtimestamp(ts / 1e9).isoformat(),
                *display_values
            ))
            self.frame_count += 1
            
            if len(self.batch_data) >= self.batch_size:
                self._flush_batch()
    
    def _flush_batch(self):
        if not self.batch_data:
            return
        
        try:
            columns = []
            for sensor_id, enabled in self.sensor_configs:
                if enabled:
                    columns.extend([f'"{sensor_id}_D1"', f'"{sensor_id}_D2"', f'"{sensor_id}_D3"'])
            
            placeholders = ','.join(['?'] * (2 + len(columns)))
            insert_sql = f'''
                INSERT INTO sensor_data 
                (timestamp_ns, timestamp_iso, {', '.join(columns)})
                VALUES ({placeholders})
            '''
            
            self.cursor.executemany(insert_sql, self.batch_data)
            self.conn.commit()
            self.batch_data.clear()
            
        except Exception as e:
            print(f"批量写入失败: {e}")
    
    def close(self):
        if self.batch_data:
            self._flush_batch()
        
        if self.conn:
            try:
                self.cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', ('end_time', datetime.now().isoformat()))
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO metadata (key, value) 
                    VALUES (?, ?)
                ''', ('total_frames', str(self.frame_count)))
                self.conn.commit()
            except:
                pass
            
            self.conn.close()
            self.conn = None
    
    def get_db_path(self) -> str:
        return str(self.db_path)


# ==================== 单个串口的采集工作线程 ====================
class SerialWorker(QObject):
    """单个串口的采集工作者"""
    
    log_signal = pyqtSignal(str, str)  # (port, message)
    data_signal = pyqtSignal(str, list)  # (port, display_list)
    status_signal = pyqtSignal(str, str)  # (port, status)
    progress_signal = pyqtSignal(str, int)  # (port, frame_count)
    error_signal = pyqtSignal(str, str)  # (port, error)
    finished_signal = pyqtSignal(str)  # (port)
    
    def __init__(self, port_name: str, sensor_configs: list, output_dir: str):
        super().__init__()
        self.port_name = port_name
        self.sensor_configs = sensor_configs
        self.output_dir = output_dir
        self.ser = None
        self.running = False
        self.paused = False
        self.stop_flag = False
        self.db_writer = None
        self.parser = FrameParser()
    
    def start(self):
        """启动采集"""
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=BAUDRATE,
                bytesize=DATA_BITS,
                stopbits=STOP_BITS,
                parity=PARITY,
                timeout=1.0
            )
            self.log_signal.emit(self.port_name, f'串口 {self.port_name} 已连接')
            
            # 初始化数据库
            self.db_writer = SQLiteWriter(self.output_dir, self.port_name, self.sensor_configs)
            self.log_signal.emit(self.port_name, f'数据文件: {self.db_writer.get_db_path()}')
            
            self.running = True
            self.stop_flag = False
            self.paused = False
            
            self.status_signal.emit(self.port_name, '采集中')
            
            while not self.stop_flag:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                try:
                    raw = self.ser.read(FRAME_LENGTH * 2)
                except serial.SerialException as e:
                    self.error_signal.emit(self.port_name, f'串口读取错误: {e}')
                    break
                
                if raw:
                    frames = self.parser.parse(raw)
                    if frames:
                        _, sensor_raw_list = frames[-1]
                        display_list = []
                        for i, (d1_raw, d2_raw, d3_raw) in enumerate(sensor_raw_list):
                            if self.sensor_configs[i][1]:
                                d1_display = round(1000 * math.sqrt(d1_raw) / 512, 2)
                                d2_display = round(1000 * math.sqrt(d2_raw) / 512, 2)
                                d3_display = round(d3_raw * 0.00010464 - 51.455, 2)
                                display_list.append((d1_display, d2_display, d3_display))
                            else:
                                display_list.append(('--', '--', '--'))
                        
                        self.data_signal.emit(self.port_name, display_list)
                        
                        if self.db_writer:
                            self.db_writer.write(frames)
                        
                        self.progress_signal.emit(self.port_name, self.db_writer.frame_count if self.db_writer else 0)
            
            self.running = False
            self._close_writer()
            self.status_signal.emit(self.port_name, '已停止')
            self.log_signal.emit(self.port_name, f'采集已停止')
            self.finished_signal.emit(self.port_name)
            
        except Exception as e:
            self.error_signal.emit(self.port_name, f'启动失败: {e}')
            self.finished_signal.emit(self.port_name)
    
    def stop(self):
        self.stop_flag = True
    
    def pause(self):
        self.paused = True
        self.status_signal.emit(self.port_name, '已暂停')
    
    def resume(self):
        self.paused = False
        self.status_signal.emit(self.port_name, '采集中')
    
    def _close_writer(self):
        if self.db_writer:
            self.db_writer.close()
            self.log_signal.emit(self.port_name, f'数据已保存至: {self.db_writer.get_db_path()}')
            self.db_writer = None


# ==================== 串口管理器和控制器 ====================
class MultiSerialController(QObject):
    """管理多个串口采集工作者"""
    
    log_signal = pyqtSignal(str, str)
    data_signal = pyqtSignal(str, list)
    status_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(str, int)
    error_signal = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.workers: Dict[str, SerialWorker] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.output_dir = OUTPUT_DIR
        self.sensor_configs = [(f'S{i+1}', True) for i in range(SENSOR_NUM)]
    
    def add_serial_port(self, port_name: str, sensor_configs: list = None):
        """添加一个串口"""
        if port_name in self.workers:
            return False, f"串口 {port_name} 已存在"
        
        if sensor_configs is None:
            sensor_configs = self.sensor_configs
        
        worker = SerialWorker(port_name, sensor_configs, self.output_dir)
        
        # 连接信号
        worker.log_signal.connect(self.log_signal)
        worker.data_signal.connect(self.data_signal)
        worker.status_signal.connect(self.status_signal)
        worker.progress_signal.connect(self.progress_signal)
        worker.error_signal.connect(self.error_signal)
        worker.finished_signal.connect(self.on_worker_finished)
        
        self.workers[port_name] = worker
        return True, f"串口 {port_name} 已添加"
    
    def remove_serial_port(self, port_name: str):
        """移除一个串口"""
        if port_name not in self.workers:
            return False, f"串口 {port_name} 不存在"
        
        # 如果正在运行，先停止
        if port_name in self.threads and self.threads[port_name].is_alive():
            self.stop_port(port_name)
        
        del self.workers[port_name]
        return True, f"串口 {port_name} 已移除"
    
    def start_all(self):
        """启动所有串口采集"""
        for port_name in self.workers:
            self.start_port(port_name)
    
    def start_port(self, port_name: str):
        """启动指定串口"""
        if port_name not in self.workers:
            return False, f"串口 {port_name} 不存在"
        
        if port_name in self.threads and self.threads[port_name].is_alive():
            return False, f"串口 {port_name} 已在运行"
        
        worker = self.workers[port_name]
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        self.threads[port_name] = thread
        
        return True, f"串口 {port_name} 已启动"
    
    def stop_all(self):
        """停止所有串口采集"""
        for port_name in self.workers:
            self.stop_port(port_name)
    
    def stop_port(self, port_name: str):
        """停止指定串口"""
        if port_name not in self.workers:
            return
        
        worker = self.workers[port_name]
        worker.stop()
    
    def pause_all(self):
        """暂停所有串口"""
        for port_name in self.workers:
            self.pause_port(port_name)
    
    def pause_port(self, port_name: str):
        """暂停指定串口"""
        if port_name in self.workers:
            self.workers[port_name].pause()
    
    def resume_all(self):
        """恢复所有串口"""
        for port_name in self.workers:
            self.resume_port(port_name)
    
    def resume_port(self, port_name: str):
        """恢复指定串口"""
        if port_name in self.workers:
            self.workers[port_name].resume()
    
    def on_worker_finished(self, port_name: str):
        """工作者完成回调"""
        if port_name in self.threads:
            del self.threads[port_name]
    
    def set_output_dir(self, output_dir: str):
        """设置输出目录"""
        self.output_dir = output_dir
    
    def set_sensor_configs(self, sensor_configs: list):
        """设置传感器配置"""
        self.sensor_configs = sensor_configs
    
    def get_ports(self) -> List[str]:
        """获取所有串口列表"""
        return list(self.workers.keys())
    
    def get_active_ports(self) -> List[str]:
        """获取正在运行的串口列表"""
        active = []
        for port_name, thread in self.threads.items():
            if thread.is_alive():
                active.append(port_name)
        return active


# ==================== 主窗口 GUI ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = MultiSerialController()
        self.port_widgets = {}  # 存储每个串口的UI组件
        self.setup_ui()
        self.connect_signals()
        self.refresh_serial_ports()
    
    def setup_ui(self):
        self.setWindowTitle('多串口传感器数据采集系统 v4.0')
        self.setMinimumSize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # ===== 顶部控制区 =====
        top_control = QHBoxLayout()
        
        # 串口管理组
        port_group = QGroupBox('串口管理')
        port_layout = QHBoxLayout()
        
        port_layout.addWidget(QLabel('可选串口:'))
        self.combo_available_ports = QComboBox()
        self.combo_available_ports.setMinimumWidth(150)
        port_layout.addWidget(self.combo_available_ports)
        
        self.btn_refresh = QPushButton('刷新')
        self.btn_refresh.clicked.connect(self.refresh_serial_ports)
        port_layout.addWidget(self.btn_refresh)
        
        self.btn_add_port = QPushButton('+ 添加串口')
        self.btn_add_port.clicked.connect(self.add_serial_port)
        port_layout.addWidget(self.btn_add_port)
        
        self.btn_remove_port = QPushButton('- 移除串口')
        self.btn_remove_port.clicked.connect(self.remove_serial_port)
        port_layout.addWidget(self.btn_remove_port)
        
        port_group.setLayout(port_layout)
        top_control.addWidget(port_group)
        
        # 采集控制组
        control_group = QGroupBox('采集控制')
        control_layout = QHBoxLayout()
        
        self.btn_start_all = QPushButton('▶ 全部启动')
        self.btn_start_all.setStyleSheet('background-color: #4CAF50; color: white;')
        self.btn_start_all.clicked.connect(self.start_all)
        control_layout.addWidget(self.btn_start_all)
        
        self.btn_pause_all = QPushButton('⏸ 全部暂停')
        self.btn_pause_all.setEnabled(False)
        self.btn_pause_all.clicked.connect(self.pause_all)
        control_layout.addWidget(self.btn_pause_all)
        
        self.btn_resume_all = QPushButton('▶ 全部继续')
        self.btn_resume_all.setEnabled(False)
        self.btn_resume_all.clicked.connect(self.resume_all)
        control_layout.addWidget(self.btn_resume_all)
        
        self.btn_stop_all = QPushButton('⏹ 全部停止')
        self.btn_stop_all.setEnabled(False)
        self.btn_stop_all.setStyleSheet('background-color: #f44336; color: white;')
        self.btn_stop_all.clicked.connect(self.stop_all)
        control_layout.addWidget(self.btn_stop_all)
        
        control_group.setLayout(control_layout)
        top_control.addWidget(control_group)
        
        main_layout.addLayout(top_control)
        
        # ===== 输出设置 =====
        output_group = QGroupBox('数据输出设置')
        output_layout = QHBoxLayout()
        
        output_layout.addWidget(QLabel('输出目录:'))
        self.edit_output_dir = QLineEdit(OUTPUT_DIR)
        self.edit_output_dir.setMinimumWidth(200)
        output_layout.addWidget(self.edit_output_dir)
        
        self.btn_browse_dir = QPushButton('浏览...')
        self.btn_browse_dir.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.btn_browse_dir)
        
        output_layout.addStretch()
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # ===== 多串口数据显示 (TabWidget) =====
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget, stretch=2)
        
        # ===== 日志区域 =====
        log_group = QGroupBox('运行日志')
        log_layout = QVBoxLayout()
        
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setFont(QFont('Consolas', 9))
        log_layout.addWidget(self.text_log)
        
        self.btn_clear_log = QPushButton('清空日志')
        self.btn_clear_log.clicked.connect(lambda: self.text_log.clear())
        log_layout.addWidget(self.btn_clear_log)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)
        
        # ===== 状态栏 =====
        self.statusBar().showMessage('就绪')
    
    def connect_signals(self):
        self.controller.log_signal.connect(self.append_log)
        self.controller.data_signal.connect(self.update_data_display)
        self.controller.status_signal.connect(self.update_port_status)
        self.controller.progress_signal.connect(self.update_frame_count)
        self.controller.error_signal.connect(self.on_error)
    
    def refresh_serial_ports(self):
        """刷新可用串口列表"""
        self.combo_available_ports.clear()
        ports = serial.tools.list_ports.comports()
        for port in sorted(ports):
            self.combo_available_ports.addItem(f'{port.device} - {port.description}', port.device)
        if self.combo_available_ports.count() == 0:
            self.combo_available_ports.addItem('未检测到串口')
    
    def add_serial_port(self):
        """添加串口"""
        if self.combo_available_ports.currentData() is None:
            return
        
        port = self.combo_available_ports.currentData()
        
        # 检查是否已添加
        if port in self.controller.get_ports():
            QMessageBox.warning(self, '重复添加', f'串口 {port} 已经添加')
            return
        
        # 创建传感器配置（使用默认配置）
        sensor_configs = [(f'S{i+1}', True) for i in range(SENSOR_NUM)]
        
        # 添加到控制器
        success, msg = self.controller.add_serial_port(port, sensor_configs)
        if not success:
            QMessageBox.critical(self, '错误', msg)
            return
        
        # 创建UI标签页
        self.create_port_tab(port)
        self.append_log(port, f'串口 {port} 已添加')
        
        # 更新可用串口列表（移除已添加的）
        self.update_available_ports()
    
    def remove_serial_port(self):
        """移除串口"""
        current_tab = self.tab_widget.currentIndex()
        if current_tab < 0:
            return
        
        port_name = self.tab_widget.tabText(current_tab)
        
        reply = QMessageBox.question(self, '确认移除', 
            f'确定要移除串口 {port_name} 吗？\n如果正在采集，将停止采集。',
            QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从控制器移除
            success, msg = self.controller.remove_serial_port(port_name)
            if success:
                # 移除UI标签页
                self.tab_widget.removeTab(current_tab)
                del self.port_widgets[port_name]
                self.append_log(port_name, f'串口 {port_name} 已移除')
                self.update_available_ports()
    
    def create_port_tab(self, port_name: str):
        """为串口创建UI标签页"""
        # 创建主容器
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # 传感器配置区域
        config_group = QGroupBox(f'{port_name} - 传感器配置')
        config_layout = QGridLayout()
        
        # 表头
        config_layout.addWidget(QLabel('通道'), 0, 0)
        config_layout.addWidget(QLabel('启用'), 0, 1)
        config_layout.addWidget(QLabel('传感器ID'), 0, 2)
        config_layout.addWidget(QLabel('状态'), 0, 3)
        
        # 存储控件
        id_inputs = []
        enable_checkboxes = []
        status_labels = []
        
        for i in range(SENSOR_NUM):
            # 通道号
            ch_label = QLabel(f'通道 {i+1}')
            ch_label.setStyleSheet('font-weight:bold;')
            config_layout.addWidget(ch_label, i+1, 0)
            
            # 启用复选框
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            config_layout.addWidget(checkbox, i+1, 1)
            
            # ID输入框
            id_input = QLineEdit(f'S{i+1}')
            id_input.setPlaceholderText(f'输入传感器{i+1}的ID')
            id_input.setMaximumWidth(120)
            config_layout.addWidget(id_input, i+1, 2)
            
            # 状态标签
            status_label = QLabel('● 启用')
            status_label.setStyleSheet('color: green; font-weight: bold;')
            config_layout.addWidget(status_label, i+1, 3)
            
            id_inputs.append(id_input)
            enable_checkboxes.append(checkbox)
            status_labels.append(status_label)
        
        config_group.setLayout(config_layout)
        tab_layout.addWidget(config_group)
        
        # 数据显示区域
        data_group = QGroupBox(f'{port_name} - 实时数据')
        data_layout = QGridLayout()
        data_layout.setSpacing(5)
        
        # 表头
        headers = ['传感器', 'D1', 'D2', 'D3', '状态']
        for col, txt in enumerate(headers):
            lbl = QLabel(txt)
            lbl.setStyleSheet('font-weight:bold; background:#eeeeee; padding:3px;')
            data_layout.addWidget(lbl, 0, col)
        
        # 存储数据显示标签
        data_labels = []
        color_list = ['#0066cc', '#009933', '#cc6600', '#9933cc', '#00aaaa', '#cc2222']
        
        for i in range(SENSOR_NUM):
            # 传感器ID
            id_label = QLabel(f'S{i+1}')
            id_label.setStyleSheet(f'font-weight:bold; color:{color_list[i]};')
            data_layout.addWidget(id_label, i+1, 0)
            
            # D1, D2, D3
            d_labels = []
            for j in range(3):
                d_label = QLabel('--')
                d_label.setStyleSheet(f'font-size:14px; font-weight:bold; color:{color_list[i]};')
                data_layout.addWidget(d_label, i+1, j+1)
                d_labels.append(d_label)
            
            # 状态
            status_label = QLabel('● 启用')
            status_label.setStyleSheet('color: green; font-weight: bold;')
            data_layout.addWidget(status_label, i+1, 4)
            d_labels.append(status_label)
            
            data_labels.append(d_labels)
        
        # 帧数显示
        data_layout.addWidget(QLabel('累计帧数：'), SENSOR_NUM+1, 0)
        frame_label = QLabel('0')
        frame_label.setStyleSheet('font-size:14px; font-weight:bold;')
        data_layout.addWidget(frame_label, SENSOR_NUM+1, 1, 1, 4)
        
        data_group.setLayout(data_layout)
        tab_layout.addWidget(data_group)
        
        # 单个串口的控制按钮
        control_group = QGroupBox(f'{port_name} - 控制')
        control_layout = QHBoxLayout()
        
        btn_start = QPushButton('▶ 启动')
        btn_start.setStyleSheet('background-color: #4CAF50; color: white;')
        btn_start.clicked.connect(lambda: self.start_port(port_name))
        control_layout.addWidget(btn_start)
        
        btn_pause = QPushButton('⏸ 暂停')
        btn_pause.setEnabled(False)
        btn_pause.clicked.connect(lambda: self.pause_port(port_name))
        control_layout.addWidget(btn_pause)
        
        btn_resume = QPushButton('▶ 继续')
        btn_resume.setEnabled(False)
        btn_resume.clicked.connect(lambda: self.resume_port(port_name))
        control_layout.addWidget(btn_resume)
        
        btn_stop = QPushButton('⏹ 停止')
        btn_stop.setEnabled(False)
        btn_stop.setStyleSheet('background-color: #f44336; color: white;')
        btn_stop.clicked.connect(lambda: self.stop_port(port_name))
        control_layout.addWidget(btn_stop)
        
        control_group.setLayout(control_layout)
        tab_layout.addWidget(control_group)
        
        # 保存UI组件引用
        self.port_widgets[port_name] = {
            'tab': tab_widget,
            'id_inputs': id_inputs,
            'enable_checkboxes': enable_checkboxes,
            'status_labels': status_labels,
            'data_labels': data_labels,
            'frame_label': frame_label,
            'btn_start': btn_start,
            'btn_pause': btn_pause,
            'btn_resume': btn_resume,
            'btn_stop': btn_stop
        }
        
        # 添加标签页
        self.tab_widget.addTab(tab_widget, port_name)
    
    def update_available_ports(self):
        """更新可用串口下拉列表（移除已添加的）"""
        current_selection = self.combo_available_ports.currentData()
        self.combo_available_ports.clear()
        
        all_ports = serial.tools.list_ports.comports()
        added_ports = self.controller.get_ports()
        
        for port in sorted(all_ports):
            if port.device not in added_ports:
                self.combo_available_ports.addItem(f'{port.device} - {port.description}', port.device)
        
        if self.combo_available_ports.count() == 0:
            self.combo_available_ports.addItem('无可添加的串口')
    
    def start_all(self):
        """启动所有串口采集"""
        if not self.controller.get_ports():
            QMessageBox.warning(self, '无串口', '请先添加串口')
            return
        
        self.controller.set_output_dir(self.edit_output_dir.text().strip() or OUTPUT_DIR)
        self.controller.start_all()
        
        self.btn_start_all.setEnabled(False)
        self.btn_pause_all.setEnabled(True)
        self.btn_stop_all.setEnabled(True)
        
        self.append_log('系统', '========== 全部启动采集 ==========')
    
    def stop_all(self):
        """停止所有串口采集"""
        reply = QMessageBox.question(self, '确认停止', '确定要停止所有采集吗？',
                                       QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.controller.stop_all()
            self.append_log('系统', '全部停止采集')
    
    def pause_all(self):
        """暂停所有串口"""
        self.controller.pause_all()
        self.btn_pause_all.setEnabled(False)
        self.btn_resume_all.setEnabled(True)
        self.append_log('系统', '全部暂停')
    
    def resume_all(self):
        """恢复所有串口"""
        self.controller.resume_all()
        self.btn_pause_all.setEnabled(True)
        self.btn_resume_all.setEnabled(False)
        self.append_log('系统', '全部恢复')
    
    def start_port(self, port_name: str):
        """启动单个串口"""
        self.controller.set_output_dir(self.edit_output_dir.text().strip() or OUTPUT_DIR)
        success, msg = self.controller.start_port(port_name)
        if success:
            widgets = self.port_widgets.get(port_name)
            if widgets:
                widgets['btn_start'].setEnabled(False)
                widgets['btn_pause'].setEnabled(True)
                widgets['btn_stop'].setEnabled(True)
                widgets['btn_resume'].setEnabled(False)
        else:
            QMessageBox.warning(self, '启动失败', msg)
    
    def stop_port(self, port_name: str):
        """停止单个串口"""
        self.controller.stop_port(port_name)
        widgets = self.port_widgets.get(port_name)
        if widgets:
            widgets['btn_start'].setEnabled(True)
            widgets['btn_pause'].setEnabled(False)
            widgets['btn_stop'].setEnabled(False)
            widgets['btn_resume'].setEnabled(False)
    
    def pause_port(self, port_name: str):
        """暂停单个串口"""
        self.controller.pause_port(port_name)
        widgets = self.port_widgets.get(port_name)
        if widgets:
            widgets['btn_pause'].setEnabled(False)
            widgets['btn_resume'].setEnabled(True)
    
    def resume_port(self, port_name: str):
        """恢复单个串口"""
        self.controller.resume_port(port_name)
        widgets = self.port_widgets.get(port_name)
        if widgets:
            widgets['btn_pause'].setEnabled(True)
            widgets['btn_resume'].setEnabled(False)
    
    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, '选择数据输出目录', self.edit_output_dir.text())
        if directory:
            self.edit_output_dir.setText(directory)
    
    def update_port_status(self, port_name: str, status: str):
        """更新串口状态"""
        if port_name in self.port_widgets:
            self.statusBar().showMessage(f'{port_name}: {status}')
    
    def update_frame_count(self, port_name: str, count: int):
        """更新帧数显示"""
        widgets = self.port_widgets.get(port_name)
        if widgets:
            widgets['frame_label'].setText(str(count))
    
    def update_data_display(self, port_name: str, display_list: list):
        """更新数据显示"""
        widgets = self.port_widgets.get(port_name)
        if not widgets:
            return
        
        data_labels = widgets['data_labels']
        for i, (d1, d2, d3) in enumerate(display_list):
            if i < len(data_labels):
                if d1 != '--':
                    data_labels[i][0].setText(f'{d1:.2f}')
                    data_labels[i][1].setText(f'{d2:.2f}')
                    data_labels[i][2].setText(f'{d3:.2f}')
                else:
                    data_labels[i][0].setText('--')
                    data_labels[i][1].setText('--')
                    data_labels[i][2].setText('--')
    
    def append_log(self, source: str, msg: str):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.text_log.append(f'[{timestamp}] [{source}] {msg}')
        if self.text_log.document().blockCount() > 500:
            cursor = self.text_log.textCursor()
            cursor.moveStart(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.deleteChar()
            self.text_log.setTextCursor(cursor)
    
    def on_error(self, port_name: str, msg: str):
        """错误处理"""
        QMessageBox.critical(self, f'{port_name} 错误', msg)
        self.append_log(port_name, f'错误: {msg}')
    
    def closeEvent(self, event):
        """关闭窗口"""
        self.controller.stop_all()
        time.sleep(0.5)
        event.accept()


# ==================== 入口 ====================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
