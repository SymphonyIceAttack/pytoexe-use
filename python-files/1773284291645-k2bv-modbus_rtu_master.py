#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modbus RTU 上位机软件
支持20个自定义查询地址，可读写Modbus RTU从站寄存器
"""

import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QGroupBox, QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from pymodbus.client import ModbusSerialClient


class ModbusWorker(QThread):
    """Modbus通信工作线程"""
    data_received = pyqtSignal(int, int, object)  # index, address, value
    error_occurred = pyqtSignal(int, int, str)  # index, address, error_msg
    log_data = pyqtSignal(str, str)  # direction, hex_data (TX/RX, hex string)
    
    def __init__(self, client, index, address, slave_id, function_code, write_value=None):
        super().__init__()
        self.client = client
        self.index = index
        self.address = address
        self.slave_id = slave_id
        self.function_code = function_code
        self.write_value = write_value
        
    def build_request_frame(self, device_id, func_code, address, value=None):
        """构建请求帧的十六进制字符串"""
        if value is not None:
            # 写操作
            if func_code == 0x06:  # 写单个寄存器
                frame = bytes([device_id, func_code, (address >> 8) & 0xFF, address & 0xFF, 
                              (value >> 8) & 0xFF, value & 0xFF])
            elif func_code == 0x05:  # 写单个线圈
                coil_value = 0xFF00 if value else 0x0000
                frame = bytes([device_id, func_code, (address >> 8) & 0xFF, address & 0xFF,
                              (coil_value >> 8) & 0xFF, coil_value & 0xFF])
            else:
                frame = bytes([device_id, func_code, (address >> 8) & 0xFF, address & 0xFF, 0x00, 0x01])
        else:
            # 读操作
            frame = bytes([device_id, func_code, (address >> 8) & 0xFF, address & 0xFF, 0x00, 0x01])
        
        # 计算CRC16
        crc = self.calculate_crc16(frame)
        return frame + crc
        
    def calculate_crc16(self, data):
        """计算Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return bytes([crc & 0xFF, (crc >> 8) & 0xFF])
        
    def run(self):
        try:
            # pymodbus 3.x 版本使用 device_id 参数
            device_id = self.slave_id
            
            # 根据功能码获取对应的Modbus功能码数值
            func_code_map = {
                "01-读线圈": 0x01,
                "02-读离散输入": 0x02,
                "03-读保持寄存器": 0x03,
                "04-读输入寄存器": 0x04,
                "05-写单个线圈": 0x05,
                "06-写单个寄存器": 0x06
            }
            
            func_code = func_code_map.get(self.function_code, 0x03)
            
            # 构建并发送请求帧
            if "写" in self.function_code and self.write_value is not None:
                request_frame = self.build_request_frame(device_id, func_code, self.address, self.write_value)
            else:
                request_frame = self.build_request_frame(device_id, func_code, self.address)
            
            # 发送请求帧日志
            self.log_data.emit("TX", request_frame.hex().upper())
            
            if self.function_code == "03-读保持寄存器":
                result = self.client.read_holding_registers(address=self.address, count=1, device_id=device_id)
                if not result.isError():
                    # 构建响应帧模拟
                    value = result.registers[0]
                    response_frame = bytes([device_id, 0x03, 0x02, (value >> 8) & 0xFF, value & 0xFF])
                    crc = self.calculate_crc16(response_frame)
                    response_frame = response_frame + crc
                    self.log_data.emit("RX", response_frame.hex().upper())
                    self.data_received.emit(self.index, self.address, value)
                else:
                    self.error_occurred.emit(self.index, self.address, str(result))
                    
            elif self.function_code == "04-读输入寄存器":
                result = self.client.read_input_registers(address=self.address, count=1, device_id=device_id)
                if not result.isError():
                    value = result.registers[0]
                    response_frame = bytes([device_id, 0x04, 0x02, (value >> 8) & 0xFF, value & 0xFF])
                    crc = self.calculate_crc16(response_frame)
                    response_frame = response_frame + crc
                    self.log_data.emit("RX", response_frame.hex().upper())
                    self.data_received.emit(self.index, self.address, value)
                else:
                    self.error_occurred.emit(self.index, self.address, str(result))
                    
            elif self.function_code == "01-读线圈":
                result = self.client.read_coils(address=self.address, count=1, device_id=device_id)
                if not result.isError():
                    value = result.bits[0]
                    response_frame = bytes([device_id, 0x01, 0x01, 0x01 if value else 0x00])
                    crc = self.calculate_crc16(response_frame)
                    response_frame = response_frame + crc
                    self.log_data.emit("RX", response_frame.hex().upper())
                    self.data_received.emit(self.index, self.address, 1 if value else 0)
                else:
                    self.error_occurred.emit(self.index, self.address, str(result))
                    
            elif self.function_code == "02-读离散输入":
                result = self.client.read_discrete_inputs(address=self.address, count=1, device_id=device_id)
                if not result.isError():
                    value = result.bits[0]
                    response_frame = bytes([device_id, 0x02, 0x01, 0x01 if value else 0x00])
                    crc = self.calculate_crc16(response_frame)
                    response_frame = response_frame + crc
                    self.log_data.emit("RX", response_frame.hex().upper())
                    self.data_received.emit(self.index, self.address, 1 if value else 0)
                else:
                    self.error_occurred.emit(self.index, self.address, str(result))
                    
            elif self.function_code == "06-写单个寄存器":
                if self.write_value is not None:
                    result = self.client.write_register(address=self.address, value=self.write_value, device_id=device_id)
                    if not result.isError():
                        # 写成功响应帧（原样返回请求）
                        response_frame = request_frame
                        self.log_data.emit("RX", response_frame.hex().upper())
                        self.data_received.emit(self.index, self.address, self.write_value)
                    else:
                        self.error_occurred.emit(self.index, self.address, str(result))
                        
            elif self.function_code == "05-写单个线圈":
                if self.write_value is not None:
                    result = self.client.write_coil(address=self.address, value=bool(self.write_value), device_id=device_id)
                    if not result.isError():
                        response_frame = request_frame
                        self.log_data.emit("RX", response_frame.hex().upper())
                        self.data_received.emit(self.index, self.address, self.write_value)
                    else:
                        self.error_occurred.emit(self.index, self.address, str(result))
                        
        except Exception as e:
            self.error_occurred.emit(self.index, self.address, str(e))


class RegisterWidget(QWidget):
    """单个寄存器控制组件"""
    write_requested = pyqtSignal(int, int, int)  # index, address, value
    
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # 根据奇偶行设置不同背景色 - 莫兰迪淡色
        if self.index % 2 == 0:
            bg_color = "#f5f3f0"
        else:
            bg_color = "#faf9f7"
        self.setStyleSheet(f"background-color: {bg_color}; border-radius: 6px;")
        
        # 序号 - 莫兰迪灰蓝色圆形
        self.lbl_index = QLabel(f"{self.index + 1}")
        self.lbl_index.setFixedSize(28, 28)
        self.lbl_index.setAlignment(Qt.AlignCenter)
        self.lbl_index.setStyleSheet("""
            QLabel {
                background-color: #8fa4b3;
                color: #ffffff;
                border-radius: 14px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.lbl_index)
        
        # 备注文本框（用户自定义）
        self.txt_remark = QLineEdit()
        self.txt_remark.setPlaceholderText("备注说明...")
        self.txt_remark.setFixedWidth(150)
        self.txt_remark.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d4c8c0;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                color: #5a5a5a;
            }
            QLineEdit:focus {
                border: 1px solid #a3b5c0;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border: 1px solid #b5a99d;
            }
        """)
        layout.addWidget(self.txt_remark)
        
        # 使能复选框 - 莫兰迪风格
        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(False)
        self.chk_enabled.setFixedSize(20, 20)
        self.chk_enabled.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #c0b8af;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #9aadab;
                border-color: #9aadab;
            }
            QCheckBox::indicator:hover {
                border-color: #a3b5c0;
            }
        """)
        layout.addWidget(self.chk_enabled)
        
        # 寄存器地址
        self.spn_address = QSpinBox()
        self.spn_address.setRange(0, 65535)
        self.spn_address.setValue(0)
        self.spn_address.setFixedWidth(80)
        self.spn_address.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #d4c8c0;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #5a5a5a;
            }
            QSpinBox:focus {
                border: 1px solid #a3b5c0;
            }
            QSpinBox:hover {
                border: 1px solid #b5a99d;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #a3b5c0;
                border-radius: 2px;
                width: 16px;
                margin: 1px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #8fa4b3;
            }
        """)
        layout.addWidget(self.spn_address)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 值显示/输入框 - 莫兰迪淡色边框
        self.txt_value = QLineEdit()
        self.txt_value.setPlaceholderText("数值")
        self.txt_value.setFixedWidth(150)
        self.txt_value.setAlignment(Qt.AlignCenter)
        self.txt_value.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #c8bbb0;
                border-radius: 6px;
                padding: 5px;
                font-size: 15px;
                font-weight: bold;
                color: #5a5a5a;
            }
            QLineEdit:focus {
                border: 2px solid #a3b5c0;
                background-color: #fefefe;
            }
            QLineEdit:hover {
                border: 2px solid #b5a99d;
            }
        """)
        layout.addWidget(self.txt_value)
        
        # 读按钮 - 莫兰迪绿色
        self.btn_read = QPushButton("读")
        self.btn_read.setFixedSize(50, 30)
        self.btn_read.setStyleSheet("""
            QPushButton {
                background-color: #8fae8b;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7d9d79;
            }
            QPushButton:pressed {
                background-color: #6b8c67;
            }
        """)
        layout.addWidget(self.btn_read)
        
        # 写按钮 - 莫兰迪珊瑚色
        self.btn_write = QPushButton("写")
        self.btn_write.setFixedSize(50, 30)
        self.btn_write.setStyleSheet("""
            QPushButton {
                background-color: #c4a48a;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b3937a;
            }
            QPushButton:pressed {
                background-color: #a2826a;
            }
        """)
        layout.addWidget(self.btn_write)
        
        # 状态显示
        self.lbl_status = QLabel("●")
        self.lbl_status.setFixedSize(20, 20)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("""
            QLabel {
                color: #c0b8af;
                font-size: 18px;
            }
        """)
        layout.addWidget(self.lbl_status)
        
    def get_config(self):
        """获取配置"""
        return {
            'enabled': self.chk_enabled.isChecked(),
            'remark': self.txt_remark.text(),
            'address': self.spn_address.value()
        }
    
    def set_config(self, config):
        """设置配置"""
        if 'enabled' in config:
            self.chk_enabled.setChecked(config['enabled'])
        if 'remark' in config:
            self.txt_remark.setText(config['remark'])
        if 'address' in config:
            self.spn_address.setValue(config['address'])


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.modbus_client = None
        self.workers = []
        self.settings = QSettings("ModbusRTU", "Master")
        self.init_ui()
        self.load_settings()
        
        # 轮询定时器
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_enabled_registers)
        self.current_poll_index = 0
        
    def init_ui(self):
        self.setWindowTitle("Modbus RTU 上位机 - 20通道读写")
        self.setMinimumSize(1300, 800)
        
        # 莫兰迪风格整体窗口背景
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0ebe5;
            }
            QGroupBox {
                background-color: #faf9f7;
                border: 1px solid #d4c8c0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #7d8a94;
            }
            QLabel {
                color: #5a5a5a;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #d4c8c0;
                border-radius: 4px;
                padding: 5px 10px;
                color: #5a5a5a;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #b5a99d;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #d4c8c0;
                border-radius: 4px;
                padding: 4px 8px;
                color: #5a5a5a;
            }
            QSpinBox:hover {
                border: 1px solid #b5a99d;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #a3b5c0;
                border-radius: 2px;
                width: 14px;
            }
            QPushButton {
                background-color: #a3b5c0;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8fa4b3;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #c0b8af;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #9aadab;
                border-color: #9aadab;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # ========== 左侧配置区 ==========
        left_panel = QWidget()
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #e8e4df;
                border-radius: 10px;
            }
            QGroupBox {
                background-color: #faf9f7;
                border: none;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 6px;
            }
            QGroupBox::title {
                color: #7d8a94;
                font-size: 12px;
            }
            QLabel {
                color: #5a5a5a;
                font-size: 11px;
            }
            QComboBox, QSpinBox {
                background-color: #ffffff;
                border: 1px solid #d4c8c0;
            }
            QComboBox:hover, QSpinBox:hover {
                border: 1px solid #b5a99d;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)
        
        # 串口配置区
        serial_group = QGroupBox("串口配置")
        serial_layout = QGridLayout(serial_group)
        serial_layout.setSpacing(5)
        serial_layout.setContentsMargins(10, 12, 10, 8)
        
        # 串口选择
        serial_layout.addWidget(QLabel("串口:"), 0, 0)
        self.cmb_port = QComboBox()
        self.refresh_ports()
        serial_layout.addWidget(self.cmb_port, 0, 1)
        
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setFixedSize(50, 26)
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #a3b5c0;
                font-size: 11px;
            }
        """)
        serial_layout.addWidget(self.btn_refresh, 1, 0, 1, 2)
        
        # 波特率
        serial_layout.addWidget(QLabel("波特率:"), 2, 0)
        self.cmb_baudrate = QComboBox()
        self.cmb_baudrate.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.cmb_baudrate.setCurrentText("9600")
        serial_layout.addWidget(self.cmb_baudrate, 2, 1)
        
        # 数据位
        serial_layout.addWidget(QLabel("数据位:"), 3, 0)
        self.cmb_databits = QComboBox()
        self.cmb_databits.addItems(["5", "6", "7", "8"])
        self.cmb_databits.setCurrentText("8")
        serial_layout.addWidget(self.cmb_databits, 3, 1)
        
        # 停止位
        serial_layout.addWidget(QLabel("停止位:"), 4, 0)
        self.cmb_stopbits = QComboBox()
        self.cmb_stopbits.addItems(["1", "1.5", "2"])
        serial_layout.addWidget(self.cmb_stopbits, 4, 1)
        
        # 校验
        serial_layout.addWidget(QLabel("校验:"), 5, 0)
        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(["无", "奇", "偶"])
        serial_layout.addWidget(self.cmb_parity, 5, 1)
        
        # 从站地址
        serial_layout.addWidget(QLabel("从站地址:"), 6, 0)
        self.spn_slave_id = QSpinBox()
        self.spn_slave_id.setRange(1, 247)
        self.spn_slave_id.setValue(1)
        serial_layout.addWidget(self.spn_slave_id, 6, 1)
        
        # 超时
        serial_layout.addWidget(QLabel("超时(ms):"), 7, 0)
        self.spn_timeout = QSpinBox()
        self.spn_timeout.setRange(100, 10000)
        self.spn_timeout.setValue(1000)
        serial_layout.addWidget(self.spn_timeout, 7, 1)
        
        # 轮询间隔
        serial_layout.addWidget(QLabel("轮询(ms):"), 8, 0)
        self.spn_poll_interval = QSpinBox()
        self.spn_poll_interval.setRange(100, 10000)
        self.spn_poll_interval.setValue(500)
        serial_layout.addWidget(self.spn_poll_interval, 8, 1)
        
        # 重试次数
        serial_layout.addWidget(QLabel("重试次数:"), 9, 0)
        self.spn_retries = QSpinBox()
        self.spn_retries.setRange(0, 10)
        self.spn_retries.setValue(3)
        serial_layout.addWidget(self.spn_retries, 9, 1)
        
        # 连接按钮 - 莫兰迪蓝色
        self.btn_connect = QPushButton("连接")
        self.btn_connect.setFixedHeight(36)
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #7d9eb8;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #6d8ea8;
            }
            QPushButton:pressed {
                background-color: #5d7e98;
            }
        """)
        serial_layout.addWidget(self.btn_connect, 10, 0, 1, 2)
        
        # 保存配置按钮
        self.btn_save = QPushButton("保存配置")
        self.btn_save.setFixedHeight(28)
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #b5a99d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #a5998d;
            }
        """)
        serial_layout.addWidget(self.btn_save, 11, 0, 1, 2)
        
        left_layout.addWidget(serial_group)
        
        # 控制区
        control_group = QGroupBox("快捷操作")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(10, 12, 10, 8)
        
        self.btn_poll_all = QPushButton("全部读取")
        self.btn_poll_all.setFixedHeight(30)
        self.btn_poll_all.clicked.connect(self.poll_all_once)
        self.btn_poll_all.setStyleSheet("""
            QPushButton {
                background-color: #8fae8b;
                color: #ffffff;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f9e7b;
            }
        """)
        control_layout.addWidget(self.btn_poll_all)
        
        self.btn_start_poll = QPushButton("开始轮询")
        self.btn_start_poll.setFixedHeight(30)
        self.btn_start_poll.clicked.connect(self.toggle_poll)
        self.btn_start_poll.setStyleSheet("""
            QPushButton {
                background-color: #9aadab;
                color: #ffffff;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8a9d9b;
            }
        """)
        control_layout.addWidget(self.btn_start_poll)
        
        # 使能控制按钮
        enable_layout = QHBoxLayout()
        self.btn_enable_all = QPushButton("全部启用")
        self.btn_enable_all.clicked.connect(lambda: self.set_all_enabled(True))
        self.btn_enable_all.setStyleSheet("""
            QPushButton {
                background-color: #8fae8b;
                color: #ffffff;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7f9e7b;
            }
        """)
        enable_layout.addWidget(self.btn_enable_all)
        
        self.btn_disable_all = QPushButton("全部禁用")
        self.btn_disable_all.clicked.connect(lambda: self.set_all_enabled(False))
        self.btn_disable_all.setStyleSheet("""
            QPushButton {
                background-color: #a89f94;
                color: #ffffff;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #988f84;
            }
        """)
        enable_layout.addWidget(self.btn_disable_all)
        control_layout.addLayout(enable_layout)
        
        self.btn_clear_status = QPushButton("清除状态")
        self.btn_clear_status.setFixedHeight(28)
        self.btn_clear_status.clicked.connect(self.clear_all_status)
        self.btn_clear_status.setStyleSheet("""
            QPushButton {
                background-color: #c4a48a;
                color: #ffffff;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4947a;
            }
        """)
        control_layout.addWidget(self.btn_clear_status)
        
        left_layout.addWidget(control_group)
        
        # 连接状态显示
        self.lbl_conn_status = QLabel("未连接")
        self.lbl_conn_status.setAlignment(Qt.AlignCenter)
        self.lbl_conn_status.setFixedHeight(36)
        self.lbl_conn_status.setStyleSheet("""
            QLabel {
                background-color: #faf9f7;
                color: #c47a7a;
                font-weight: bold;
                font-size: 12px;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        left_layout.addWidget(self.lbl_conn_status)
        
        left_layout.addStretch()
        
        main_layout.addWidget(left_panel)
        
        # ========== 右侧数据显示区 ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # 寄存器列表区
        register_group = QGroupBox("数据监控 (20通道)")
        register_group.setStyleSheet("""
            QGroupBox {
                background-color: #faf9f7;
                border: 1px solid #d4c8c0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #7d8a94;
            }
        """)
        register_layout = QVBoxLayout(register_group)
        register_layout.setSpacing(2)
        register_layout.setContentsMargins(8, 12, 8, 8)
        
        # 表头
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)
        header_labels = [("序号", 28), ("备注", 150), ("使能", 20), ("地址", 80), ("", 0), ("值", 150), ("", 50), ("", 50), ("状态", 20)]
        for label, width in header_labels:
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignCenter)
            if width > 0:
                lbl.setFixedWidth(width)
            else:
                lbl.setFixedWidth(0)
            lbl.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 11px;
                    color: #7d8a94;
                    background-color: #ebe8e4;
                    border-radius: 3px;
                    padding: 3px;
                }
            """)
            header_layout.addWidget(lbl)
        register_layout.addLayout(header_layout)
        
        # 滚动区域包裹寄存器列表
        from PyQt5.QtWidgets import QScrollArea, QFrame
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #ebe8e4;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #a3b5c0;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8fa4b3;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(2)
        
        # 创建20个寄存器控件
        self.register_widgets = []
        for i in range(20):
            widget = RegisterWidget(i)
            widget.btn_read.clicked.connect(lambda checked, idx=i: self.read_single_register(idx))
            widget.btn_write.clicked.connect(lambda checked, idx=i: self.write_single_register(idx))
            self.register_widgets.append(widget)
            scroll_layout.addWidget(widget)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        register_layout.addWidget(scroll_area)
        
        right_layout.addWidget(register_group, 3)
        
        # 日志区
        log_group = QGroupBox("通信日志")
        log_group.setStyleSheet("""
            QGroupBox {
                background-color: #faf9f7;
                border: 1px solid #d4c8c0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #7d8a94;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(8, 12, 8, 8)
        log_layout.setSpacing(6)
        
        # 添加清空按钮
        log_btn_layout = QHBoxLayout()
        self.btn_clear_log = QPushButton("清空")
        self.btn_clear_log.setFixedWidth(50)
        self.btn_clear_log.clicked.connect(self.clear_log)
        self.btn_clear_log.setStyleSheet("""
            QPushButton {
                background-color: #a89f94;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #988f84;
            }
        """)
        log_btn_layout.addWidget(self.btn_clear_log)
        
        self.chk_show_hex = QCheckBox("显示数据流")
        self.chk_show_hex.setChecked(True)
        self.chk_show_hex.setStyleSheet("color: #7d8a94; font-size: 11px;")
        log_btn_layout.addWidget(self.chk_show_hex)
        
        log_btn_layout.addStretch()
        
        # 日志记录数显示
        self.lbl_log_count = QLabel("0条")
        self.lbl_log_count.setStyleSheet("color: #9aadab; font-size: 11px;")
        log_btn_layout.addWidget(self.lbl_log_count)
        
        log_layout.addLayout(log_btn_layout)
        
        # 日志文本框
        from PyQt5.QtWidgets import QTextEdit
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("""
            QTextEdit {
                background-color: #3a3a3a; 
                color: #b8c4b8; 
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px;
            }
            QScrollBar:vertical {
                background-color: #4a4a4a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #7a8a7a;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #8a9a8a;
            }
        """)
        log_layout.addWidget(self.txt_log)
        
        right_layout.addWidget(log_group, 1)
        
        main_layout.addWidget(right_panel, 1)
        
        # 状态栏
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #a3b5c0;
                color: #ffffff;
                font-weight: bold;
                padding: 4px;
                font-size: 11px;
            }
        """)
        self.statusBar().showMessage("就绪 - 点击任意[读]按钮即可自动连接并读取数据")
        
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.cmb_port.clear()
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            self.cmb_port.addItem(port.portName())
        if self.cmb_port.count() == 0:
            self.cmb_port.addItem("无可用串口")
            
    def toggle_connection(self):
        """切换连接状态"""
        if self.modbus_client and self.modbus_client.connected:
            self.modbus_client.close()
            self.modbus_client = None
            self.btn_connect.setText("连接")
            self.btn_connect.setStyleSheet("""
                QPushButton {
                    background-color: #7d9eb8;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #6d8ea8;
                }
            """)
            self.lbl_conn_status.setText("未连接")
            self.lbl_conn_status.setStyleSheet("""
                QLabel {
                    background-color: #faf9f7;
                    color: #c47a7a;
                    font-weight: bold;
                    font-size: 12px;
                    border-radius: 6px;
                    padding: 6px;
                }
            """)
            self.poll_timer.stop()
            self.btn_start_poll.setText("开始轮询")
            self.btn_start_poll.setStyleSheet("""
                QPushButton {
                    background-color: #9aadab;
                    color: #ffffff;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #8a9d9b;
                }
            """)
            self.log_message("已断开连接")
        else:
            port = self.cmb_port.currentText()
            baudrate = int(self.cmb_baudrate.currentText())
            databits = int(self.cmb_databits.currentText())
            stopbits = float(self.cmb_stopbits.currentText())
            parity_map = {"无": "N", "奇": "O", "偶": "E"}
            parity = parity_map[self.cmb_parity.currentText()]
            timeout = self.spn_timeout.value() / 1000.0
            retries = self.spn_retries.value()
            
            try:
                self.modbus_client = ModbusSerialClient(
                    port=port,
                    baudrate=baudrate,
                    bytesize=databits,
                    stopbits=stopbits,
                    parity=parity,
                    timeout=timeout,
                    retries=retries
                )
                
                if self.modbus_client.connect():
                    self.btn_connect.setText("断开")
                    self.btn_connect.setStyleSheet("""
                        QPushButton {
                            background-color: #c47a7a;
                            color: #ffffff;
                            border: none;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 13px;
                        }
                        QPushButton:hover {
                            background-color: #b46a6a;
                        }
                    """)
                    self.lbl_conn_status.setText(f"已连接: {port}")
                    self.lbl_conn_status.setStyleSheet("""
                        QLabel {
                            background-color: #faf9f7;
                            color: #8fae8b;
                            font-weight: bold;
                            font-size: 12px;
                            border-radius: 6px;
                            padding: 6px;
                        }
                    """)
                    self.log_message(f"已连接到 {port} - 波特率:{baudrate}, 数据位:{databits}, 停止位:{stopbits}, 校验:{parity}")
                else:
                    self.modbus_client = None
                    QMessageBox.warning(self, "连接失败", "无法打开串口，请检查串口是否被占用。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
                
    def auto_connect(self):
        """自动连接串口（如果未连接）"""
        if not self.modbus_client or not self.modbus_client.connected:
            # 自动执行连接
            port = self.cmb_port.currentText()
            if port == "无可用串口":
                QMessageBox.warning(self, "警告", "未检测到可用串口！")
                return False
            
            baudrate = int(self.cmb_baudrate.currentText())
            databits = int(self.cmb_databits.currentText())
            stopbits = float(self.cmb_stopbits.currentText())
            parity_map = {"无": "N", "奇": "O", "偶": "E"}
            parity = parity_map[self.cmb_parity.currentText()]
            timeout = self.spn_timeout.value() / 1000.0
            retries = self.spn_retries.value()
            
            try:
                self.modbus_client = ModbusSerialClient(
                    port=port,
                    baudrate=baudrate,
                    bytesize=databits,
                    stopbits=stopbits,
                    parity=parity,
                    timeout=timeout,
                    retries=retries
                )
                
                if self.modbus_client.connect():
                    self.btn_connect.setText("断开")
                    self.btn_connect.setStyleSheet("""
                        QPushButton {
                            background-color: #c47a7a;
                            color: #ffffff;
                            border: none;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 13px;
                        }
                        QPushButton:hover {
                            background-color: #b46a6a;
                        }
                    """)
                    self.lbl_conn_status.setText(f"已连接: {port}")
                    self.lbl_conn_status.setStyleSheet("""
                        QLabel {
                            background-color: #faf9f7;
                            color: #8fae8b;
                            font-weight: bold;
                            font-size: 12px;
                            border-radius: 6px;
                            padding: 6px;
                        }
                    """)
                    self.log_message(f"自动连接到 {port} - 波特率:{baudrate}")
                    return True
                else:
                    self.modbus_client = None
                    QMessageBox.warning(self, "连接失败", "无法打开串口，请检查串口是否被占用。")
                    return False
            except Exception as e:
                QMessageBox.critical(self, "错误", f"连接失败: {str(e)}")
                return False
        return True
    
    def read_single_register(self, index):
        """读取单个寄存器"""
        # 自动连接检查
        if not self.auto_connect():
            return
            
        widget = self.register_widgets[index]
        address = widget.spn_address.value()
        slave_id = self.spn_slave_id.value()
        
        # 默认使用读保持寄存器（功能码03）
        function = "03-读保持寄存器"
        
        worker = ModbusWorker(self.modbus_client, index, address, slave_id, function)
        worker.data_received.connect(self.on_data_received)
        worker.error_occurred.connect(self.on_error_occurred)
        worker.log_data.connect(self.on_log_data)
        worker.start()
        self.workers.append(worker)
        
    def write_single_register(self, index):
        """写入单个寄存器"""
        # 自动连接检查
        if not self.auto_connect():
            return
            
        widget = self.register_widgets[index]
        address = widget.spn_address.value()
        slave_id = self.spn_slave_id.value()
        
        # 默认使用写单个寄存器（功能码06）
        function = "06-写单个寄存器"
        
        # 从输入框获取写入值
        value_text = widget.txt_value.text().strip()
        if not value_text:
            QMessageBox.warning(self, "警告", "请在值框中输入要写入的值！")
            return
            
        try:
            write_value = int(value_text)
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的整数！")
            return
            
        worker = ModbusWorker(self.modbus_client, index, address, slave_id, function, write_value)
        worker.data_received.connect(self.on_data_received)
        worker.error_occurred.connect(self.on_error_occurred)
        worker.log_data.connect(self.on_log_data)
        worker.start()
        self.workers.append(worker)
        
    def poll_all_once(self):
        """轮询所有启用的寄存器"""
        for i, widget in enumerate(self.register_widgets):
            if widget.chk_enabled.isChecked():
                self.read_single_register(i)
                
    def poll_enabled_registers(self):
        """轮询启用的寄存器（定时调用）"""
        if not self.modbus_client or not self.modbus_client.connected:
            self.poll_timer.stop()
            return
            
        # 找到下一个启用的寄存器
        for _ in range(20):
            widget = self.register_widgets[self.current_poll_index]
            if widget.chk_enabled.isChecked():
                self.read_single_register(self.current_poll_index)
                self.current_poll_index = (self.current_poll_index + 1) % 20
                return
            self.current_poll_index = (self.current_poll_index + 1) % 20
            
    def toggle_poll(self):
        """切换轮询状态"""
        if self.poll_timer.isActive():
            self.poll_timer.stop()
            self.btn_start_poll.setText("🔄 开始轮询")
            self.btn_start_poll.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5568d3, stop:1 #6b4190);
                }
            """)
            self.log_message("⏹️ 轮询已停止")
        else:
            interval = self.spn_poll_interval.value()
            self.poll_timer.start(interval)
            self.btn_start_poll.setText("⏸️ 停止轮询")
            self.btn_start_poll.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff6b6b, stop:1 #ffa36b);
                    color: white;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff5252, stop:1 #ff8a50);
                }
            """)
            self.log_message(f"▶️ 轮询已开始，间隔:{interval}ms")
            
    def set_all_enabled(self, enabled):
        """设置所有寄存器的使能状态"""
        for widget in self.register_widgets:
            widget.chk_enabled.setChecked(enabled)
            
    def clear_all_status(self):
        """清除所有状态显示"""
        for widget in self.register_widgets:
            widget.txt_value.clear()
            widget.txt_value.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            widget.lbl_status.setStyleSheet("color: gray; font-size: 16px;")
            
    def test_communication(self):
        """测试通信 - 扫描从站地址"""
        if not self.modbus_client or not self.modbus_client.connected:
            QMessageBox.warning(self, "警告", "请先连接串口！")
            return
            
        self.log_message("[测试] 开始扫描从站地址 1-10...")
        self.statusBar().showMessage("正在扫描从站地址...")
        
        found_slaves = []
        
        # 扫描从站地址 1-10
        for slave_id in range(1, 11):
            try:
                # 尝试读取地址0的保持寄存器
                result = self.modbus_client.read_holding_registers(address=0, count=1, device_id=slave_id)
                if not result.isError():
                    found_slaves.append(slave_id)
                    self.log_message(f"[测试] 发现从站 {slave_id} 响应正常")
                else:
                    self.log_message(f"[测试] 从站 {slave_id} 无响应")
            except Exception as e:
                self.log_message(f"[测试] 从站 {slave_id} 通信异常: {str(e)[:30]}")
                
        self.statusBar().showMessage("扫描完成")
        
        if found_slaves:
            QMessageBox.information(self, "扫描结果", 
                f"发现以下从站地址响应正常:\n{found_slaves}\n\n请将'从站地址'设置为响应的地址。")
        else:
            QMessageBox.warning(self, "扫描结果", 
                "未发现响应的从站设备!\n\n请检查:\n"
                "1. 下位机是否已上电\n"
                "2. 串口线是否正确连接(A+/B-)\n"
                "3. 波特率/校验位是否与下位机一致\n"
                "4. 下位机Modbus RTU是否已启用")
            
    def on_data_received(self, index, address, value):
        """数据接收成功回调"""
        widget = self.register_widgets[index]
        widget.txt_value.setText(str(value))
        widget.txt_value.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d4edda, stop:1 #c3e6cb);
                border: 3px solid #28a745;
                border-radius: 8px;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
                color: #155724;
            }
        """)
        widget.lbl_status.setText("🟢")
        widget.lbl_status.setStyleSheet("""
            QLabel {
                color: #28a745;
                font-size: 16px;
            }
        """)
        
    def on_error_occurred(self, index, address, error_msg):
        """错误回调"""
        widget = self.register_widgets[index]
        widget.txt_value.setText("❌")
        widget.txt_value.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8d7da, stop:1 #f5c6cb);
                border: 3px solid #dc3545;
                border-radius: 8px;
                padding: 5px;
                font-size: 16px;
                font-weight: bold;
                color: #721c24;
            }
        """)
        widget.lbl_status.setText("🔴")
        widget.lbl_status.setStyleSheet("""
            QLabel {
                color: #dc3545;
                font-size: 16px;
            }
        """)
        
    def on_log_data(self, direction, hex_data):
        """记录数据流"""
        if self.chk_show_hex.isChecked():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if direction == "TX":
                # 发送 - 蓝色
                color = "#00BFFF"
                arrow = "→"
            else:
                # 接收 - 绿色
                color = "#00FF00"
                arrow = "←"
            
            # 格式化十六进制数据，每两个字符加空格
            formatted_hex = ' '.join([hex_data[i:i+2] for i in range(0, len(hex_data), 2)])
            
            log_entry = f'<span style="color: #888888">[{timestamp}]</span> <span style="color: {color}"><b>[{direction}]</b> {arrow}</span> <span style="color: #FFFFFF">{formatted_hex}</span>'
            self.txt_log.append(log_entry)
            
            # 自动滚动到底部
            scrollbar = self.txt_log.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            # 更新日志计数
            self.update_log_count()
        
    def log_message(self, msg):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.txt_log.append(f'<span style="color: #888888">[{timestamp}]</span> <span style="color: #FFFF00">{msg}</span>')
        
        # 自动滚动到底部
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 更新日志计数
        self.update_log_count()
        
    def clear_log(self):
        """清空日志"""
        self.txt_log.clear()
        self.update_log_count()
        
    def update_log_count(self):
        """更新日志计数"""
        line_count = self.txt_log.document().lineCount()
        self.lbl_log_count.setText(f"日志数: {line_count}")
        
    def save_settings(self):
        """保存配置"""
        # 保存串口配置
        self.settings.setValue("port", self.cmb_port.currentText())
        self.settings.setValue("baudrate", self.cmb_baudrate.currentText())
        self.settings.setValue("databits", self.cmb_databits.currentText())
        self.settings.setValue("stopbits", self.cmb_stopbits.currentText())
        self.settings.setValue("parity", self.cmb_parity.currentText())
        self.settings.setValue("slave_id", self.spn_slave_id.value())
        self.settings.setValue("timeout", self.spn_timeout.value())
        self.settings.setValue("poll_interval", self.spn_poll_interval.value())
        self.settings.setValue("retries", self.spn_retries.value())
        
        # 保存寄存器配置
        register_configs = []
        for widget in self.register_widgets:
            register_configs.append(widget.get_config())
        self.settings.setValue("register_configs", json.dumps(register_configs))
        
        QMessageBox.information(self, "成功", "配置已保存！")
        
    def load_settings(self):
        """加载配置"""
        # 加载串口配置
        port = self.settings.value("port")
        if port:
            index = self.cmb_port.findText(port)
            if index >= 0:
                self.cmb_port.setCurrentIndex(index)
                
        baudrate = self.settings.value("baudrate")
        if baudrate:
            index = self.cmb_baudrate.findText(baudrate)
            if index >= 0:
                self.cmb_baudrate.setCurrentIndex(index)
                
        databits = self.settings.value("databits")
        if databits:
            index = self.cmb_databits.findText(databits)
            if index >= 0:
                self.cmb_databits.setCurrentIndex(index)
                
        stopbits = self.settings.value("stopbits")
        if stopbits:
            index = self.cmb_stopbits.findText(stopbits)
            if index >= 0:
                self.cmb_stopbits.setCurrentIndex(index)
                
        parity = self.settings.value("parity")
        if parity:
            index = self.cmb_parity.findText(parity)
            if index >= 0:
                self.cmb_parity.setCurrentIndex(index)
                
        slave_id = self.settings.value("slave_id")
        if slave_id:
            self.spn_slave_id.setValue(int(slave_id))
            
        timeout = self.settings.value("timeout")
        if timeout:
            self.spn_timeout.setValue(int(timeout))
            
        poll_interval = self.settings.value("poll_interval")
        if poll_interval:
            self.spn_poll_interval.setValue(int(poll_interval))
            
        retries = self.settings.value("retries")
        if retries:
            self.spn_retries.setValue(int(retries))
            
        # 加载寄存器配置
        register_configs = self.settings.value("register_configs")
        if register_configs:
            try:
                configs = json.loads(register_configs)
                for i, config in enumerate(configs):
                    if i < len(self.register_widgets):
                        self.register_widgets[i].set_config(config)
            except:
                pass
                
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.modbus_client and self.modbus_client.connected:
            self.modbus_client.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
