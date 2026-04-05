#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消防设备监控系远程统 - PC客户端
功能: 实时数据监控、智能缓存、可配置报警系统
作者: 13037990547
日期: 2026-03-31
版本: 由 update_manager.CURRENT_VERSION 统一管理
"""

import sys
import os
import json
import socket
import threading
import time
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import winsound

# ===================== 在线升级模块 =====================
from update_manager import (
    VersionCheckThread,
    UpdateDownloadThread,
    install_update,
    CURRENT_VERSION,
    format_size
)

# ===================== 单实例运行检查 =====================
def check_single_instance():
    """确保只有一个实例运行"""
    import ctypes
    mutex_name = "Global\\ZF_S1215_Monitor_Single_Instance"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        # 使用Windows原生消息框，不依赖QApplication
        ctypes.windll.user32.MessageBoxW(0, "远程消防设备监控系统已经在运行中！", "程序已运行", 0x30)
        sys.exit(1)
    return mutex

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QComboBox, QDateEdit, QMessageBox, QDialog,
    QCheckBox, QSlider, QGroupBox, QSplitter, QTextEdit,
    QSystemTrayIcon, QMenu, QStatusBar, QHeaderView, QFileDialog,
    QSpinBox, QGridLayout, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QToolButton, QStyle, QAction, QInputDialog,
    QAbstractItemView
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QDate, QSettings, QSize,
    QPropertyAnimation, QEasingCurve
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QPalette, QCloseEvent,
    QKeySequence, QPixmap, QPainter, QPen
)
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPolygon
from PyQt5.QtWidgets import QShortcut

# ===================== 全局配置 =====================
APP_NAME = "远程消防设备监控系统"
APP_VERSION = f"V{CURRENT_VERSION}"  # 统一引用 update_manager 中的版本号
SERVER_IP = "162.14.120.49"
DEVICE_PORT = 18567      # 设备数据接收端口（服务器内部使用）
PC_LONG_PORT = 18678     # PC长连接端口（实时数据）
PC_SHORT_PORT = 18568    # PC短连接端口（管理操作）

# 目录配置 - 使用程序当前目录（兼容打包后的EXE）
def get_base_dir():
    """获取程序基础目录，兼容开发环境和打包后的EXE"""
    if getattr(sys, 'frozen', False):
        # 打包后的EXE运行
        return Path(sys.executable).parent.resolve()
    else:
        # 开发环境运行
        return Path(__file__).parent.resolve()

BASE_DIR = get_base_dir()
APP_DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"

# 多数据库架构
DB_MAIN = APP_DATA_DIR / "client_main.db"      # 主数据库（配置、用户、设备名）
DB_HISTORY = APP_DATA_DIR / "history_data.db"   # 历史数据（设备数据、报警记录）
DB_LOGS = APP_DATA_DIR / "system_logs.db"       # 系统日志（接收日志、错误日志）

# 兼容旧代码
DB_PATH = DB_MAIN

print(f"[系统] 程序目录: {BASE_DIR}")
print(f"[系统] 数据目录: {APP_DATA_DIR}")
print(f"[系统] 主数据库: {DB_MAIN}")
print(f"[系统] 历史数据库: {DB_HISTORY}")
print(f"[系统] 日志数据库: {DB_LOGS}")

# 确保目录存在
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ===================== SQLite多数据库初始化 =====================
def init_main_database():
    """初始化主数据库（配置、用户、设备名）"""
    conn = sqlite3.connect(DB_MAIN)
    cursor = conn.cursor()
    
    # 配置表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value_json TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 设备名称表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hid TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[数据库] 主数据库初始化完成")

def init_history_database():
    """初始化历史数据库（设备数据、报警记录）"""
    conn = sqlite3.connect(DB_HISTORY)
    cursor = conn.cursor()
    
    # 缓存数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            hid TEXT NOT NULL,
            date TEXT NOT NULL,
            fetch_time TEXT,
            data_count INTEGER,
            data_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, hid, date)
        )
    ''')
    
    # 设备历史数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hid TEXT NOT NULL,
            receive_time TIMESTAMP NOT NULL,
            server_type TEXT,
            raw_data TEXT,
            parsed_data TEXT,
            is_admin_received INTEGER DEFAULT 0,
            data_size INTEGER
        )
    ''')
    
    # 设备历史索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_hid_time 
        ON device_history(hid, receive_time)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_time 
        ON device_history(receive_time)
    ''')
    
    # 报警历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alarm_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hid TEXT,
            alarm_type TEXT,
            description TEXT,
            timestamp TEXT,
            raw_data TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 报警历史索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alarm_type 
        ON alarm_history(alarm_type)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alarm_timestamp 
        ON alarm_history(timestamp)
    ''')
    
    conn.commit()
    conn.close()
    print("[数据库] 历史数据库初始化完成")

def init_logs_database():
    """初始化系统日志数据库"""
    conn = sqlite3.connect(DB_LOGS)
    cursor = conn.cursor()
    
    # 接收数据日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS received_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            log_type TEXT DEFAULT 'INFO',
            source TEXT,
            content TEXT,
            data_size INTEGER
        )
    ''')
    
    # 接收日志索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_received_log_time 
        ON received_logs(log_time)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_received_source 
        ON received_logs(source)
    ''')
    
    # 错误日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            context TEXT
        )
    ''')
    
    # 错误日志索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_error_log_time 
        ON error_logs(error_time)
    ''')
    
    # 实时数据表（专门用于存储接收到的实时数据，登录后快速恢复显示）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS realtime_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receive_time DATETIME NOT NULL,
            hid TEXT,
            raw_data TEXT NOT NULL,
            server_type TEXT DEFAULT '',
            is_heartbeat INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 实时数据索引（按时间倒序查询优化）
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_realtime_time 
        ON realtime_data(receive_time DESC)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_realtime_hid 
        ON realtime_data(hid)
    ''')
    
    conn.commit()
    conn.close()
    print("[数据库] 日志数据库初始化完成")

def init_all_databases():
    """初始化所有数据库"""
    init_main_database()
    init_history_database()
    init_logs_database()
    print("[数据库] 所有数据库初始化完成")

# 初始化所有数据库
init_all_databases()

# ===================== 数据库管理器 =====================
class DatabaseManager:
    """多数据库统一管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 主数据库连接（配置、用户、设备名）
        self.db_main = sqlite3.connect(DB_MAIN, check_same_thread=False)
        self.db_main.row_factory = sqlite3.Row
        
        # 历史数据库连接（设备数据、报警记录）
        self.db_history = sqlite3.connect(DB_HISTORY, check_same_thread=False)
        self.db_history.row_factory = sqlite3.Row
        
        # 日志数据库连接（接收日志、错误日志）
        self.db_logs = sqlite3.connect(DB_LOGS, check_same_thread=False)
        self.db_logs.row_factory = sqlite3.Row
        
        self._initialized = True
        print("[数据库管理器] 初始化完成")
    
    def get_main_connection(self):
        """获取主数据库连接"""
        return self.db_main
    
    def get_history_connection(self):
        """获取历史数据库连接"""
        return self.db_history
    
    def get_logs_connection(self):
        """获取日志数据库连接"""
        return self.db_logs
    
    def save_device_history(self, hid, raw_data, server_type, is_admin=False):
        """保存设备数据到历史数据库"""
        try:
            cursor = self.db_history.cursor()
            cursor.execute('''
                INSERT INTO device_history 
                (hid, receive_time, server_type, raw_data, data_size, is_admin_received)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                hid,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                server_type,
                raw_data[:1000],  # 限制原始数据长度，避免过大
                len(raw_data),
                1 if is_admin else 0
            ))
            self.db_history.commit()
        except Exception as e:
            print(f"[数据库管理器] 保存设备历史失败: {e}")
    
    def log_received_data(self, data, source=None):
        """记录接收到的数据到日志数据库"""
        try:
            cursor = self.db_logs.cursor()
            cursor.execute('''
                INSERT INTO received_logs 
                (log_time, log_type, source, content, data_size)
                VALUES (?, 'INFO', ?, ?, ?)
            ''', (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                source or "unknown",
                data[:500],  # 限制内容长度
                len(data)
            ))
            self.db_logs.commit()
        except Exception as e:
            print(f"[数据库管理器] 记录接收日志失败: {e}")
    
    def log_error(self, error_type, error_message, stack_trace=None, context=None):
        """记录错误日志"""
        try:
            cursor = self.db_logs.cursor()
            cursor.execute('''
                INSERT INTO error_logs 
                (error_time, error_type, error_message, stack_trace, context)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                error_type,
                error_message[:500],
                (stack_trace or "")[:2000],
                context
            ))
            self.db_logs.commit()
        except Exception as e:
            print(f"[数据库管理器] 记录错误日志失败: {e}")
    
    def cleanup_old_logs(self, received_days=30, error_days=90):
        """清理旧日志"""
        try:
            from datetime import timedelta
            
            # 清理接收日志
            received_cutoff = datetime.now() - timedelta(days=received_days)
            cursor = self.db_logs.cursor()
            cursor.execute('DELETE FROM received_logs WHERE log_time < ?', 
                         (received_cutoff.strftime("%Y-%m-%d %H:%M:%S"),))
            deleted_received = cursor.rowcount
            
            # 清理错误日志（保留更久）
            error_cutoff = datetime.now() - timedelta(days=error_days)
            cursor.execute('DELETE FROM error_logs WHERE error_time < ?', 
                         (error_cutoff.strftime("%Y-%m-%d %H:%M:%S"),))
            deleted_errors = cursor.rowcount
            
            self.db_logs.commit()
            
            # 压缩日志数据库
            self.db_logs.execute('VACUUM')
            
            print(f"[维护] 已清理 {deleted_received} 条接收日志, {deleted_errors} 条错误日志")
            
        except Exception as e:
            print(f"[维护] 清理日志失败: {e}")
    
    def cleanup_old_history(self, days=180):
        """清理旧的历史数据"""
        try:
            from datetime import timedelta
            
            cutoff = datetime.now() - timedelta(days=days)
            
            # 清理旧的设备历史
            cursor = self.db_history.cursor()
            cursor.execute('DELETE FROM device_history WHERE receive_time < ?', 
                         (cutoff.strftime("%Y-%m-%d %H:%M:%S"),))
            deleted_device = cursor.rowcount
            
            # 清理旧的报警历史
            cursor.execute('DELETE FROM alarm_history WHERE timestamp < ?', 
                         (cutoff.strftime("%Y-%m-%d %H:%M:%S"),))
            deleted_alarm = cursor.rowcount
            
            self.db_history.commit()
            
            # 压缩历史数据库
            self.db_history.execute('VACUUM')
            
            print(f"[维护] 已清理 {deleted_device} 条设备历史, {deleted_alarm} 条报警记录")
            
        except Exception as e:
            print(f"[维护] 清理历史数据失败: {e}")
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        stats = {}
        
        try:
            import os
            
            # 主数据库大小
            if os.path.exists(DB_MAIN):
                stats['main_db'] = {
                    'size_mb': round(os.path.getsize(DB_MAIN) / (1024*1024), 2),
                    'path': str(DB_MAIN)
                }
            
            # 历史数据库大小
            if os.path.exists(DB_HISTORY):
                stats['history_db'] = {
                    'size_mb': round(os.path.getsize(DB_HISTORY) / (1024*1024), 2),
                    'path': str(DB_HISTORY)
                }
            
            # 日志数据库大小
            if os.path.exists(DB_LOGS):
                stats['logs_db'] = {
                    'size_mb': round(os.path.getsize(DB_LOGS) / (1024*1024), 2),
                    'path': str(DB_LOGS)
                }
            
            # 记录数量统计
            cursor = self.db_logs.cursor()
            cursor.execute('SELECT COUNT(*) FROM received_logs')
            stats['received_log_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM error_logs')
            stats['error_log_count'] = cursor.fetchone()[0]
            
            cursor = self.db_history.cursor()
            cursor.execute('SELECT COUNT(*) FROM device_history')
            stats['device_history_count'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM alarm_history')
            stats['alarm_history_count'] = cursor.fetchone()[0]
            
        except Exception as e:
            print(f"[数据库管理器] 获取统计信息失败: {e}")
        
        return stats
    
    def close_all(self):
        """关闭所有数据库连接"""
        try:
            if self.db_main:
                self.db_main.close()
                print("[数据库管理器] 主数据库已关闭")
            
            if self.db_history:
                self.db_history.close()
                print("[数据库管理器] 历史数据库已关闭")
            
            if self.db_logs:
                self.db_logs.close()
                print("[数据库管理器] 日志数据库已关闭")
                
        except Exception as e:
            print(f"[数据库管理器] 关闭数据库失败: {e}")

# 全局数据库管理器实例
db_manager = DatabaseManager()

# ===================== 配置文件管理 =====================
class ConfigManager:
    """配置文件管理器 - 使用SQLite"""
    
    DEFAULT_CONFIG = {
        "version": "2.2",
        "user": {
            "last_username": "",
            "last_password": "",
            "remember_password": False
        },
        "alarm": {
            "enabled": True,
            "types": {
                "fault": {"enabled": True, "sound": True, "popup": True, "name": "故障"},
                "alarm": {"enabled": True, "sound": True, "popup": True, "name": "报警"},
                "feedback": {"enabled": False, "sound": False, "popup": False, "name": "反馈"},
                "reset": {"enabled": False, "sound": False, "popup": False, "name": "复位"}
            },
            "sound": {
                "enabled": True,
                "volume": 70,
                "sound_type": "default"
            },
            "popup": {
                "enabled": True,
                "stay_on_top": True,
                "auto_close_seconds": 0
            },
            "flash_taskbar": True
        },
        "ui": {
            "theme": "default",
            "font_size": 10,
            "language": "zh_CN"
        },
        "connection": {
            "server_ip": SERVER_IP,
            "server_port": PC_LONG_PORT,
            "short_port": PC_SHORT_PORT,
            "auto_reconnect": True,
            "reconnect_interval": 5,
            "reconnect_max": 10
        },
        "cache": {
            "max_size_mb": 100,
            "auto_clean": True,
            "export_path": "Desktop"
        },
        "users": {}
    }
    
    def __init__(self):
        self.config = self.load()
    
    def load(self) -> dict:
        """从SQLite加载配置"""
        cursor = db_manager.get_main_connection().cursor()
        try:
            cursor.execute("SELECT value_json FROM config WHERE key = 'main_config'")
            row = cursor.fetchone()
            if row:
                loaded = json.loads(row[0])
                return self._merge_config(self.DEFAULT_CONFIG.copy(), loaded)
        except Exception as e:
            print(f"加载配置失败: {e}")
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """保存配置到SQLite"""
        cursor = db_manager.get_main_connection().cursor()
        try:
            value_json = json.dumps(self.config, ensure_ascii=False)
            cursor.execute('''
                INSERT OR REPLACE INTO config (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', ('main_config', value_json))
            db_manager.get_main_connection().commit()
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def _merge_config(self, default: dict, loaded: dict) -> dict:
        """递归合并配置"""
        for key, value in default.items():
            if key not in loaded:
                loaded[key] = value
            elif isinstance(value, dict) and isinstance(loaded[key], dict):
                loaded[key] = self._merge_config(value, loaded[key])
        return loaded
    
    def get(self, key_path: str, default=None):
        """获取配置项"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value):
        """设置配置项"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save()

# 全局配置实例
config = ConfigManager()

# ===================== 数据缓存管理 =====================
class CacheManager:
    """本地数据缓存管理器 - 使用历史数据库"""
    
    MAX_CACHE_SIZE = 100  # 内存缓存最大条数
    
    def __init__(self, username: str):
        self.username = username
        self._memory_cache: Dict[str, dict] = {}
        self._cache_order = []  # LRU顺序列表
        print(f"[缓存管理器] 用户 {username} 的缓存已初始化（最大{self.MAX_CACHE_SIZE}条）")
    
    def _add_to_memory_cache(self, cache_key: str, cache_data: dict):
        """添加到内存缓存，实现LRU淘汰"""
        if cache_key in self._memory_cache:
            # 已存在，移到末尾
            self._cache_order.remove(cache_key)
            self._cache_order.append(cache_key)
        else:
            # 新增
            if len(self._memory_cache) >= self.MAX_CACHE_SIZE:
                # 淘汰最旧的
                oldest_key = self._cache_order.pop(0)
                del self._memory_cache[oldest_key]
            
            self._cache_order.append(cache_key)
        
        self._memory_cache[cache_key] = cache_data
    
    def has_cache(self, hid: str, date: str) -> bool:
        """检查是否有缓存"""
        cache_key = f"{hid}_{date}"
        if cache_key in self._memory_cache:
            return True
        
        try:
            cursor = db_manager.get_history_connection().cursor()
            cursor.execute('''
                SELECT id FROM cache_data 
                WHERE username = ? AND hid = ? AND date = ?
            ''', (self.username, hid, date))
            return cursor.fetchone() is not None
        except Exception as e:
            print(f"[缓存管理器] 检查缓存失败: {e}")
            return False
    
    def get_cache(self, hid: str, date: str) -> Optional[dict]:
        """获取缓存数据"""
        cache_key = f"{hid}_{date}"
        
        if cache_key in self._memory_cache:
            # 更新访问顺序（LRU）
            self._cache_order.remove(cache_key)
            self._cache_order.append(cache_key)
            return self._memory_cache[cache_key]
        
        try:
            cursor = db_manager.get_history_connection().cursor()
            cursor.execute('''
                SELECT fetch_time, data_count, data_json 
                FROM cache_data 
                WHERE username = ? AND hid = ? AND date = ?
            ''', (self.username, hid, date))
            row = cursor.fetchone()
            if row:
                cache_data = {
                    "hid": hid,
                    "date": date,
                    "fetch_time": row[0],
                    "count": row[1],
                    "data": json.loads(row[2])
                }
                self._add_to_memory_cache(cache_key, cache_data)
                return cache_data
        except Exception as e:
            print(f"[缓存管理器] 读取缓存失败: {e}")
        return None
    
    def save_cache(self, hid: str, date: str, data: list):
        """保存缓存数据"""
        cache_key = f"{hid}_{date}"
        cache_data = {
            "hid": hid,
            "date": date,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(data),
            "data": data
        }
        
        self._add_to_memory_cache(cache_key, cache_data)
        
        try:
            cursor = db_manager.get_history_connection().cursor()
            data_json = json.dumps(data, ensure_ascii=False)
            cursor.execute('''
                INSERT OR REPLACE INTO cache_data 
                (username, hid, date, fetch_time, data_count, data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.username, hid, date, cache_data["fetch_time"], len(data), data_json))
            db_manager.get_history_connection().commit()
        except Exception as e:
            print(f"[缓存管理器] 保存缓存失败: {e}")
    
    def clear_cache(self):
        """清空所有缓存"""
        self._memory_cache.clear()
        self._cache_order.clear()
        try:
            cursor = db_manager.get_history_connection().cursor()
            cursor.execute('DELETE FROM cache_data WHERE username = ?', (self.username,))
            db_manager.get_history_connection().commit()
        except Exception as e:
            print(f"[缓存管理器] 清空缓存失败: {e}")
    
    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        try:
            cursor = db_manager.get_history_connection().cursor()
            cursor.execute('SELECT COUNT(*), SUM(LENGTH(data_json)) FROM cache_data WHERE username = ?', (self.username,))
            row = cursor.fetchone()
            count = row[0] or 0
            total_size = row[1] or 0
            return {
                "file_count": count,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "memory_count": len(self._memory_cache),
                "max_memory": self.MAX_CACHE_SIZE
            }
        except Exception as e:
            print(f"[缓存管理器] 获取缓存信息失败: {e}")
            return {"file_count": 0, "total_size_mb": 0, "memory_count": 0, "max_memory": self.MAX_CACHE_SIZE}

# ===================== 网络通信线程 =====================
class NetworkThread(QThread):
    """网络通信线程"""
    
    connected = pyqtSignal()
    connecting = pyqtSignal()  # ✅ TCP连接建立，正在登录中
    disconnected = pyqtSignal()
    login_success = pyqtSignal(bool, dict)
    login_failed = pyqtSignal(str)
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    kicked_out = pyqtSignal(str)  # 异地登录被踢出信号
    
    def __init__(self, server_ip: str, server_port: int, username: str = None, password: str = None, main_window=None):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket: Optional[socket.socket] = None
        self.running = False
        self.user: Optional[str] = username
        self.password: Optional[str] = password
        self.main_window = main_window  # ✅ 保存主窗口引用（用于自动重登）
        self._lock = threading.Lock()
        self._pending_request = None
    
    def run(self):
        """主循环 - 简化的长连接模式"""
        self.running = True
        reconnect_count = 0
        max_reconnect = config.get('connection.reconnect_max', 10)
        buffer = ""
        buffer_start_time = 0  # 缓冲区数据开始时间
        login_completed = False  # 登录是否完成
        last_ping_time = 0  # 上次发送ping的时间
        ping_interval = 30  # 每30秒发送一次ping
        
        while self.running:
            try:
                # 如果没有连接，建立连接
                if not self.socket:
                    print("[网络连接] 建立新连接...")
                    self._connect()
                    buffer = ""
                    buffer_start_time = 0
                    login_completed = False
                    # ✅ 不在这里重置 reconnect_count，只在登录成功后才重置
                
                # 连接建立后，发送加密登录请求
                if not login_completed:
                    import hashlib, time
                    
                    # ✅ 生成时间戳（用于防重放攻击）
                    timestamp = str(int(time.time()))
                    
                    # ✅ 加盐哈希：密码 + 用户名 + 时间戳
                    salt = f"{self.user}{timestamp}"
                    password_hash = hashlib.sha256((self.password + salt).encode('utf-8')).hexdigest()
                    
                    # 发送加密后的登录数据（不再发送明文密码）
                    login_data = json.dumps({
                        "user": self.user,
                        "pwd_hash": password_hash,
                        "ts": timestamp
                    })
                    self.socket.send(login_data.encode('utf-8'))
                    print(f"[网络连接] 发送加密登录请求: {self.user} (已使用SHA256+时间戳加密)")
                    
                    # 等待登录响应（5秒超时）
                    self.socket.settimeout(5)
                    response = self.socket.recv(1024)
                    self.socket.settimeout(None)
                    
                    if not response:
                        raise ConnectionError("登录响应为空")
                    
                    # 解析登录响应
                    try:
                        resp_data = json.loads(response.decode('utf-8'))
                        if resp_data.get('code') == 0:
                            print(f"[网络连接] 登录成功: {resp_data}")
                            login_completed = True
                            reconnect_count = 0  # ✅ 登录成功后重置重连计数器
                            # ✅ 登录成功后才发出 connected 信号
                            self.connected.emit()
                            # 发送登录成功信号
                            is_admin = bool(resp_data.get('is_admin', 0))
                            self.login_success.emit(is_admin, resp_data)
                        else:
                            error_msg = resp_data.get('msg', '登录失败')
                            print(f"[网络连接] 登录失败: {error_msg}")
                            self.login_failed.emit(error_msg)
                            raise ConnectionError(f"登录失败: {error_msg}")
                    except json.JSONDecodeError as e:
                        print(f"[网络连接] 登录响应解析失败: {e}, 数据: {response}")
                        raise ConnectionError("登录响应格式错误")
                    
                    # 登录成功后发送第一个ping
                    self.socket.send(b'ping')
                    last_ping_time = time.time()
                    print("[网络连接] 发送初始ping")
                    continue
                
                # 登录完成后，正常接收数据
                # 检查是否需要发送ping保活
                current_time = time.time()
                if current_time - last_ping_time >= ping_interval:
                    try:
                        self.socket.send(b'ping')
                        last_ping_time = current_time
                    except Exception as e:
                        print(f"[网络连接] 发送ping失败: {e}")
                        raise ConnectionError("发送ping失败")
                
                # 设置较短的超时时间用于检查ping间隔
                self.socket.settimeout(5)  # 5秒超时，用于定期检查ping间隔
                
                # ✅ 检查socket是否有效
                if not self.socket:
                    raise ConnectionError("Socket已关闭")
                
                try:
                    data = self.socket.recv(4096)
                except OSError as e:
                    if e.winerror == 10038:
                        raise ConnectionError("Socket连接已断开")
                    raise
                self.socket.settimeout(None)  # 取消超时
                
                if not data:
                    raise ConnectionError("连接已断开")
                
                # ✅ 关键调试：立即打印收到的原始数据
                print(f"[网络接收] 收到 {len(data)} 字节，原始数据: {data[:200]}")
                
                # 将数据添加到缓冲区
                decoded_data = data.decode('utf-8', errors='ignore')
                
                # 如果是新数据的开始，记录时间戳
                if not buffer:
                    buffer_start_time = time.time()
                
                buffer += decoded_data
                
                # ✅ 调试：显示缓冲区内容
                print(f"[网络接收] 缓冲区: {len(buffer)} 字节，内容: {buffer[:150]}...")
                
                # 安全保护：限制缓冲区最大大小（防止内存泄漏）
                MAX_BUFFER_SIZE = 1024 * 1024  # 1MB 限制
                if len(buffer) > MAX_BUFFER_SIZE:
                    print(f"[网络接收] ⚠️ 缓冲区过大 ({len(buffer)} 字节)，强制清空")
                    buffer = ""
                    continue
                
                # 超时保护：如果缓冲区数据超过30秒未完成，清理它
                BUFFER_TIMEOUT = 30  # 30秒超时
                if buffer and (time.time() - buffer_start_time) > BUFFER_TIMEOUT:
                    print(f"[网络接收] ⚠️ 缓冲区超时 ({int(time.time() - buffer_start_time)}秒)，丢弃不完整数据: {buffer[:100]}...")
                    buffer = ""
                    continue
                
                # 超时保护：如果缓冲区数据超过30秒未完成，清理它
                BUFFER_TIMEOUT = 30  # 30秒超时
                if buffer and (time.time() - buffer_start_time) > BUFFER_TIMEOUT:
                    print(f"[数据接收] ⚠️ 缓冲区超时，丢弃不完整数据")
                    buffer = ""
                    continue
                
                # 处理缓冲区中的设备数据
                has_device_data = '[报警]' in buffer or '[故障]' in buffer or '[反馈]' in buffer or '[心跳]' in buffer or '[正常]' in buffer or '[复位]' in buffer
                if has_device_data:
                    print(f"[网络接收] ✅ 检测到设备数据，开始处理...")
                    import re
                    pattern = r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[[^\]]+\] [^|]+\| \{[^}]+\})'
                    matches = re.findall(pattern, buffer)
                    print(f"[网络接收] 正则匹配结果: {len(matches)} 条")
                    
                    if matches:
                        for match in matches:
                            print(f"[网络接收] 处理正则匹配: {match[:80]}...")
                            self._handle_data(match)
                    
                    # ✅ 无论正则是否匹配成功，都按行分割处理
                    lines = buffer.split('\n')
                    print(f"[网络接收] 按行分割: {len(lines)} 行")
                    processed_lines = []
                    for i, line in enumerate(lines):
                        if '[报警]' in line or '[故障]' in line or '[反馈]' in line or '[心跳]' in line or '[正常]' in line or '[复位]' in line:
                            print(f"[网络接收] 处理第{i}行: {line[:80]}...")
                            self._handle_data(line)
                            processed_lines.append(line)
                    
                    # 如果有处理过的行，清空已处理的数据
                    if processed_lines or matches:
                        buffer = ""
                    else:
                        # 保留未处理的数据
                        buffer = lines[-1] if lines else ""
                    continue
                
                # 尝试解析JSON数据
                while buffer:
                    try:
                        # 尝试解析完整的JSON对象
                        json_data = json.loads(buffer)
                        # 解析成功，处理数据并清空缓冲区
                        self._handle_data(buffer)
                        buffer = ""
                        break
                    except json.JSONDecodeError as e:
                        # 如果错误是期望更多数据，则等待更多数据
                        if "Expecting" in str(e) or "Unterminated" in str(e):
                            # 数据不完整，等待更多数据
                            break
                        # 如果错误是多余的字符，尝试找到完整的JSON
                        if "Extra data" in str(e):
                            # 找到第一个完整的JSON对象
                            try:
                                # 尝试逐字符解析找到完整的JSON
                                for i in range(1, len(buffer)):
                                    try:
                                        json.loads(buffer[:i])
                                        # 找到完整的JSON，处理它
                                        self._handle_data(buffer[:i])
                                        buffer = buffer[i:]
                                        break
                                    except:
                                        continue
                            except:
                                pass
                            break
                        # 其他错误，可能是设备数据格式
                        if 'HID=' in buffer or '[报警]' in buffer:
                            self._handle_data(buffer)
                            buffer = ""
                        else:
                            print(f"[接收错误] JSON解析失败: {e}")
                            buffer = ""
                        break
                
            except socket.timeout:
                # 接收超时，这是正常的，继续循环检查是否需要发送ping
                self.socket.settimeout(None)  # 取消超时
                continue
            except Exception as e:
                import traceback
                # ✅ 关闭程序时的Socket错误是正常的，不打印详细堆栈
                if "WinError 10038" in str(e) or "非套接字" in str(e):
                    print(f"[网络连接] 程序正在退出，停止接收数据")
                    # 程序退出时直接结束线程，不触发重连
                    if not self.running:
                        break
                else:
                    print(f"网络错误: {e}")
                    print(f"错误详情: {traceback.format_exc()}")
                self.disconnected.emit()
                self._close_socket()
                
                # 重置状态标志
                self._login_sent = False
                self._keepalive_sent = False
                
                if not self.running:
                    break
                
                reconnect_count += 1
                # 无限重连，但显示警告
                if reconnect_count > max_reconnect:
                    print(f"[网络连接] 重连次数超过{max_reconnect}次，继续尝试...")
                    # 每10次重连显示一次警告
                    if reconnect_count % 10 == 0:
                        self.error_occurred.emit(f"网络不稳定，已重连{reconnect_count}次，正在继续尝试...")
                else:
                    print(f"尝试第 {reconnect_count} 次重连...")
                time.sleep(config.get('connection.reconnect_interval', 5))
    
    def _connect(self):
        """建立连接"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(10)
        self.socket.connect((self.server_ip, self.server_port))
        self.socket.settimeout(None)
        # ✅ TCP连接已建立，发出 connecting 信号（正在登录中）
        self.connecting.emit()
    
    def _is_connected(self):
        """检测连接是否有效"""
        if not self.socket:
            return False
        
        # 使用getsockopt检测连接状态，而不是发送数据
        try:
            import socket
            # 获取socket错误状态
            error = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            return error == 0
        except:
            return False
    
    def _close_socket(self):
        """关闭连接"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def _handle_data(self, data: str):
        """处理接收到的数据"""
        print(f"[数据处理] 收到数据: {data[:100]}...")  # ✅ 调试日志
        
        # 检查是否有待处理的请求
        if hasattr(self, '_pending_request') and self._pending_request:
            try:
                json_data = json.loads(data)
                # 如果是用户管理响应或历史查询响应，放入队列
                if 'msg' in json_data or 'users' in json_data or 'data' in json_data:
                    self._pending_request.put(json_data)
                    return
            except Exception as e:
                # 不是JSON，可能是设备数据，继续处理
                pass
        
        try:
            json_data = json.loads(data)
            # 检查是否是异地登录被踢出通知
            if json_data.get('type') == 'kick':
                kick_msg = json_data.get('msg', '您的账号已在其他地方登录')
                print(f"[异地登录] 收到踢出通知: {kick_msg}")
                self.kicked_out.emit(kick_msg)
                return
            # 检查是否是登录响应（包含 code 字段）
            if 'code' in json_data:
                if json_data.get('code') == 0:
                    # 登录成功，检查是否有 is_admin 字段
                    if 'is_admin' in json_data:
                        # 服务器返回的是数字 1/0，转换为布尔值
                        is_admin_val = json_data.get('is_admin', False)
                        is_admin_bool = bool(is_admin_val) if isinstance(is_admin_val, int) else is_admin_val
                        print(f"[登录响应] is_admin={is_admin_val} ({type(is_admin_val)}), 转换后={is_admin_bool}")
                        self.login_success.emit(
                            is_admin_bool,
                            json_data
                        )
                    else:
                        # 成功响应但没有 is_admin，可能是其他成功响应
                        self.login_success.emit(False, json_data)
                    return
                else:
                    # 登录失败（code != 0）
                    error_msg = json_data.get('msg', '账号或密码错误')
                    print(f"[登录失败] {error_msg}")
                    self.login_failed.emit(error_msg)
                    return
            # 其他带 code 的响应（如设备列表、历史查询）放入队列
            elif 'code' in json_data and hasattr(self, '_pending_request') and self._pending_request:
                self._pending_request.put(json_data)
                return
        except json.JSONDecodeError:
            pass
        
        # 检查是否是设备数据（包含HID=）
        if 'HID=' in data:
            # 同时保存到日志文件
            try:
                import os
                log_dir = os.path.join(os.path.dirname(__file__), 'logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'received_data.txt')
                with open(log_file, 'a', encoding='utf-8') as f:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {data}\n")
            except Exception as e:
                print(f"[日志保存失败] {e}")
            self.data_received.emit(data)
        else:
            print(f"[数据处理] 未知数据格式，不处理: {data[:80]}...")
    
    def login(self, username: str, password: str):
        """发送登录请求"""
        self.user = username
        login_data = json.dumps({"user": username, "pwd": password})
        self._send(login_data)
    
    def _send(self, data: str):
        """发送数据"""
        with self._lock:
            if self.socket:
                try:
                    self.socket.send(data.encode('utf-8'))
                except Exception as e:
                    print(f"发送失败: {e}")
    
    def send_request(self, data: str, timeout: int = 5) -> dict:
        """发送短连接请求并等待响应（使用PC_SHORT_PORT）"""
        import socket
        import json
        
        print(f"[短连接请求] {data[:100]}...")
        
        try:
            # 创建独立短连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # 连接到短连接端口
            sock.connect((self.server_ip, PC_SHORT_PORT))
            print(f"[短连接请求] 已连接到 {self.server_ip}:{PC_SHORT_PORT}")
            
            # 解析原始请求数据
            try:
                request_data = json.loads(data)
            except:
                request_data = {}
            
            # ✅ 强制Token认证（不再支持明文密码）
            auth_token = getattr(self.main_window, 'auth_token', '') if hasattr(self, 'main_window') and self.main_window else ''
            
            # ✅ 如果Token为空，尝试等待一小段时间后重新获取（避免竞态条件）
            if not auth_token and hasattr(self, 'main_window') and self.main_window:
                import time
                time.sleep(0.3)  # 等待300ms
                auth_token = getattr(self.main_window, 'auth_token', '')
            
            if not auth_token:
                print(f"[短连接请求] ❌ 缺少认证Token")
                return {"code": -1, "msg": "缺少认证Token，请重新登录"}
            
            request_data["token"] = auth_token
            
            # 重新编码为JSON
            request_with_auth = json.dumps(request_data)
            
            # 发送请求
            sock.send(request_with_auth.encode('utf-8'))
            print(f"[短连接请求] 已发送数据: {request_with_auth}")
            
            # 接收响应
            response_data = b""
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                except socket.timeout:
                    break
            
            # 关闭连接
            sock.close()
            print(f"[短连接请求] 连接已关闭")
            
            # 解析响应
            if response_data:
                try:
                    response = json.loads(response_data.decode('utf-8'))
                    print(f"[短连接请求] 收到响应: {response}")
                    
                    # ✅ 检查是否Token过期，自动重登
                    if response.get('code') == -1 and 'Token' in str(response.get('msg', '')):
                        print(f"[短连接请求] ⚠️ Token已过期，尝试自动重新登录...")
                        if self._auto_relogin():
                            print(f"[短连接请求] ✅ 自动重登成功，重试请求...")
                            # 重试一次（使用新Token）
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(timeout)
                            sock.connect((self.server_ip, PC_SHORT_PORT))
                            
                            request_data["token"] = self.main_window.auth_token  # ✅ 使用新Token
                            sock.send(json.dumps(request_data).encode('utf-8'))
                            
                            response_data = b""
                            while True:
                                try:
                                    chunk = sock.recv(4096)
                                    if not chunk:
                                        break
                                    response_data += chunk
                                except socket.timeout:
                                    break
                            
                            sock.close()
                            if response_data:
                                response = json.loads(response_data.decode('utf-8'))
                                print(f"[短连接请求] ✅ 重试成功: {response}")
                    
                    return response
                except json.JSONDecodeError as e:
                    print(f"[短连接请求] 响应解析失败: {e}")
                    return {"code": 1, "msg": "响应格式错误"}
            else:
                print(f"[短连接请求] 响应为空")
                return {"code": 1, "msg": "响应为空"}
                
        except socket.timeout:
            print(f"[短连接请求] 超时")
            return {"code": 1, "msg": "请求超时"}
        except Exception as e:
            print(f"[短连接请求] 错误: {e}")
            return {"code": 1, "msg": str(e)}
    
    def _auto_relogin(self) -> bool:
        """Token过期时自动重新登录（使用保存的凭证）"""
        try:
            if not self.main_window.current_user or not self.main_window.current_password:
                print("[自动重登] ❌ 缺少保存的登录凭证")
                return False
            
            print(f"[自动重登] 正在为用户 {self.main_window.current_user} 自动重新登录...")
            
            # 创建新的网络连接进行登录
            import socket
            import hashlib
            import time as time_module
            import json
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.server_ip, PC_LONG_PORT))
            
            # 使用加密方式登录
            timestamp = str(int(time_module.time()))
            salt = f"{self.main_window.current_user}{timestamp}"
            password_hash = hashlib.sha256((self.main_window.current_password + salt).encode('utf-8')).hexdigest()
            
            login_data = json.dumps({
                "user": self.main_window.current_user,
                "pwd_hash": password_hash,
                "ts": timestamp
            })
            sock.send(login_data.encode('utf-8'))
            
            # 等待响应
            response = sock.recv(1024)
            sock.close()
            
            if response:
                resp_data = json.loads(response.decode('utf-8'))
                if resp_data.get('code') == 0:
                    # ✅ 登录成功，更新Token
                    if 'token' in resp_data:
                        self.main_window.auth_token = resp_data['token']
                        print(f"[自动重登] ✅ 成功！新Token: {resp_data['token'][:16]}...")
                        return True
                
            print(f"[自动重登] ❌ 失败: {resp_data.get('msg', '未知错误')}")
            return False
            
        except Exception as e:
            print(f"[自动重登] ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop(self):
        """停止线程"""
        self.running = False
        self._close_socket()
        self.wait(1000)

# ===================== 历史查询线程 =====================
class HistoryQueryThread(QThread):
    """历史数据查询线程"""
    
    query_finished = pyqtSignal(str, list)  # hid, data
    query_error = pyqtSignal(str)
    query_progress = pyqtSignal(int, int)   # current, total
    
    def __init__(self, network_thread, hid: str, start_date: str, end_date: str, username: str = "", password: str = "", token: str = ""):
        super().__init__()
        self.network_thread = network_thread
        self.hid = hid
        self.start_date = start_date
        self.end_date = end_date
        self.username = username
        self.password = password
        self.token = token  # ✅ 新增Token参数
    
    def run(self):
        """执行查询 - 支持分批接收"""
        import socket
        import time
        
        all_data = []
        buffer = ""
        
        try:
            # 获取服务器配置（短连接使用PC_SHORT_PORT）
            server_ip = config.get('server.ip', SERVER_IP)
            server_port = config.get('connection.short_port', PC_SHORT_PORT)
            
            # 创建新连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(60)
            sock.connect((server_ip, server_port))
            
            # ✅ 强制Token认证（不再支持明文密码）
            if not self.token:
                print(f"[历史查询] ❌ 缺少认证Token")
                self.query_error.emit("缺少认证Token，请重新登录")
                return
            
            request_data = {
                "token": self.token,
                "action": "query_history",
                "hid": self.hid,
                "start_date": self.start_date,
                "end_date": self.end_date
            }
            print(f"[历史查询] 发送请求 (Token认证)")
            
            sock.send(json.dumps(request_data).encode('utf-8'))
            
            # 分批接收数据
            total_count = 0
            received_count = 0
            is_started = False
            
            while True:
                try:
                    data = sock.recv(8192)
                    print(f"[历史查询] 收到 {len(data)} 字节数据")
                    if not data:
                        print("[历史查询] 连接已关闭")
                        break
                    
                    decoded = data.decode('utf-8', errors='ignore')
                    print(f"[历史查询] 原始数据: {decoded[:300]}...")
                    buffer += decoded
                    print(f"[历史查询] 缓冲区: {len(buffer)} 字节")
                    
                    # 处理缓冲区中的完整JSON消息
                    # 服务器可能连续发送多个JSON，需要逐个解析
                    while buffer.strip():
                        buffer = buffer.strip()
                        print(f"[历史查询] 处理缓冲区: {buffer[:100]}...")
                        
                        try:
                            # 尝试解析完整的JSON
                            json_data = json.loads(buffer)
                            print(f"[历史查询] 解析到JSON: {json_data}")
                            
                            # 首先检查是否有错误码
                            if json_data.get('code') == 1:
                                error_msg = json_data.get('msg', '未知错误')
                                print(f"[历史查询] 服务器返回错误: {error_msg}")
                                sock.close()
                                self.query_error.emit(error_msg)
                                return
                            
                            # 处理消息
                            msg_type = json_data.get('type', '')
                            
                            if msg_type == 'start':
                                total_count = json_data.get('total', 0)
                                is_started = True
                                print(f"[历史查询] 开始接收，共 {total_count} 条")
                                self.query_progress.emit(0, total_count)
                                buffer = ""  # 清空缓冲区
                            
                            elif msg_type == 'data':
                                batch_data = json_data.get('data', [])
                                all_data.extend(batch_data)
                                received_count += len(batch_data)
                                print(f"[历史查询] 收到数据批，共 {len(batch_data)} 条，累计 {received_count}/{total_count}")
                                self.query_progress.emit(received_count, total_count)
                                buffer = ""  # 清空缓冲区
                            
                            elif msg_type == 'end':
                                # 传输完成
                                print(f"[历史查询] 接收完成，共 {received_count} 条")
                                sock.close()
                                self.query_finished.emit(self.hid, all_data)
                                return
                            
                            else:
                                # 未知类型，清空缓冲区避免死循环
                                print(f"[历史查询] 未知消息类型: {msg_type}, 数据: {json_data}")
                                buffer = ""
                            
                            break  # 处理完一个JSON后跳出内层循环，继续接收
                            
                        except json.JSONDecodeError as e:
                            error_msg = str(e)
                            if "Expecting" in error_msg or "Unterminated" in error_msg or "EOF" in error_msg:
                                # 数据不完整，等待更多
                                print(f"[历史查询] 数据不完整，等待更多: {error_msg[:50]}")
                                break
                            elif "Extra data" in error_msg:
                                # 有多个JSON对象，从后向前找到最完整的JSON边界
                                print(f"[历史查询] 发现多个JSON对象，缓冲区: {len(buffer)} 字节")
                                found = False
                                # 从后向前搜索，找到最长的有效JSON
                                for i in range(len(buffer), 0, -1):
                                    try:
                                        json_data = json.loads(buffer[:i])
                                        print(f"[历史查询] 解析到JSON({i}字节): type={json_data.get('type', '')}")
                                        
                                        # 首先检查是否有错误码
                                        if json_data.get('code') == 1:
                                            error_msg = json_data.get('msg', '未知错误')
                                            print(f"[历史查询] 服务器返回错误: {error_msg}")
                                            sock.close()
                                            self.query_error.emit(error_msg)
                                            return
                                        
                                        msg_type = json_data.get('type', '')
                                        
                                        if msg_type == 'start':
                                            total_count = json_data.get('total', 0)
                                            is_started = True
                                            print(f"[历史查询] 开始接收，共 {total_count} 条")
                                            self.query_progress.emit(0, total_count)
                                        
                                        elif msg_type == 'data':
                                            batch_data = json_data.get('data', [])
                                            all_data.extend(batch_data)
                                            received_count += len(batch_data)
                                            print(f"[历史查询] 收到数据批，共 {len(batch_data)} 条，累计 {received_count}")
                                            self.query_progress.emit(received_count, total_count)
                                        
                                        elif msg_type == 'end':
                                            print(f"[历史查询] 接收完成，共 {received_count} 条")
                                            sock.close()
                                            self.query_finished.emit(self.hid, all_data)
                                            return
                                        
                                        # 移除已处理的数据，继续处理剩余数据
                                        buffer = buffer[i:].strip()
                                        print(f"[历史查询] 剩余缓冲区: {len(buffer)} 字节，继续处理...")
                                        found = True
                                        break
                                    except json.JSONDecodeError:
                                        continue
                                
                                if not found:
                                    print("[历史查询] 未找到完整JSON，等待更多数据")
                                    break
                            else:
                                # 其他错误，清空缓冲区
                                print(f"[历史查询] JSON解析错误: {error_msg[:50]}")
                                buffer = ""
                                break
                    
                except socket.timeout:
                    if is_started and received_count >= total_count:
                        # 超时但数据已接收完
                        sock.close()
                        self.query_finished.emit(self.hid, all_data)
                        return
                    else:
                        raise Exception("接收数据超时")
            
            sock.close()
            self.query_finished.emit(self.hid, all_data)
            
        except Exception as e:
            self.query_error.emit(str(e))

# ===================== 设备列表查询线程 =====================
class DeviceListQueryThread(QThread):
    """设备列表查询线程 - 使用独立连接，但不登录（避免踢掉主连接）"""
    
    query_finished = pyqtSignal(list)  # devices
    query_error = pyqtSignal(str)
    
    def __init__(self, server_ip: str, server_port: int, main_window=None):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.main_window = main_window
    
    def run(self):
        """执行查询 - 使用独立连接，发送Token认证"""
        import socket
        
        try:
            # 创建独立连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.server_ip, self.server_port))
            
            # 获取Token（支持多种方式）
            auth_token = ""
            if hasattr(self, 'main_window') and self.main_window:
                auth_token = getattr(self.main_window, 'auth_token', '')
            
            # 如果Token为空，尝试等待一小段时间后重新获取（避免竞态条件）
            if not auth_token and hasattr(self, 'main_window') and self.main_window:
                import time
                time.sleep(0.5)  # 等待500ms
                auth_token = getattr(self.main_window, 'auth_token', '')
            
            if not auth_token:
                self.query_error.emit("缺少认证Token")
                return
            
            # 发送查询请求（使用Token认证）
            request_data = {
                "action": "list_devices",
                "token": auth_token
            }
            sock.send(json.dumps(request_data).encode('utf-8'))
            
            # 接收响应
            response_data = sock.recv(8192).decode('utf-8')
            sock.close()
            
            response = json.loads(response_data)
            if response.get('code') == 0:
                devices = response.get('devices', [])
                self.query_finished.emit(devices)
            else:
                self.query_error.emit(response.get('msg', '未知错误'))
        except Exception as e:
            self.query_error.emit(str(e))

# ===================== 报警管理器 =====================
class AlarmManager:
    """报警管理器"""
    
    ALARM_TYPES = {
        'fault': {'key': 'FLT', 'name': '故障', 'default': True},
        'alarm': {'key': 'ALM', 'name': '报警', 'default': True},
        'feedback': {'key': 'FBK', 'name': '反馈', 'default': False},
        'reset': {'key': 'RST', 'name': '复位', 'default': False}
    }
    
    MAX_HISTORY_SIZE = 1000  # 内存中最多保留的报警记录数
    
    def __init__(self, parent=None):
        self.parent = parent
        self.alarm_history: List[dict] = []
        self._last_alarm_time: Dict[str, datetime] = {}
        self._load_alarm_history()
    
    def _load_alarm_history(self):
        """从历史数据库加载报警历史"""
        cursor = db_manager.get_history_connection().cursor()
        try:
            cursor.execute('''
                SELECT hid, alarm_type, description, timestamp, raw_data
                FROM alarm_history
                ORDER BY id DESC
                LIMIT 1000
            ''')
            rows = cursor.fetchall()
            self.alarm_history = []
            for row in reversed(rows):
                self.alarm_history.append({
                    'hid': row[0],
                    'type': row[1],
                    'type_name': self._get_type_name(row[1]),
                    'time': row[3],
                    'raw_data': row[4]
                })
            print(f"[报警管理器] 从历史数据库加载了 {len(self.alarm_history)} 条记录")
        except Exception as e:
            print(f"加载报警历史失败: {e}")
            self.alarm_history = []
    
    def _get_type_name(self, alarm_type: str) -> str:
        """获取类型名称"""
        type_names = {
            'fault': '故障',
            'alarm': '报警',
            'feedback': '反馈',
            'reset': '复位'
        }
        return type_names.get(alarm_type, alarm_type)
    
    def save_alarm_history(self):
        """保存报警历史到历史数据库"""
        if not self.alarm_history:
            return

        cursor = db_manager.get_history_connection().cursor()
        try:
            latest = self.alarm_history[-1]
            cursor.execute('''
                INSERT INTO alarm_history
                (hid, alarm_type, description, timestamp, raw_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                latest.get('hid', ''),
                latest.get('type', ''),
                latest.get('type_name', ''),
                latest.get('time', ''),
                latest.get('raw_data', '')
            ))
            db_manager.get_history_connection().commit()
        except Exception as e:
            print(f"保存报警历史失败: {e}")

    def check_alarm(self, raw_data: str, server_type: str = "") -> List[dict]:
        """检查数据中是否包含报警
        
        Args:
            raw_data: 原始数据
            server_type: 服务器传来的类型（优先使用）
        """
        alarms = []
        
        if not config.get('alarm.enabled', True):
            return alarms
        
        # 解析设备数据
        data_dict = self._parse_data(raw_data)
        hid = data_dict.get('HID', 'Unknown')
        fds_s = data_dict.get('FDS_S', '')
        
        # 优先使用服务器传来的类型
        alarm_type = None
        if server_type:
            server_type_map = {
                '报警': 'alarm',
                '火警': 'alarm',
                '故障': 'fault',
                '反馈': 'feedback',
                '复位': 'reset'
            }
            alarm_type = server_type_map.get(server_type)
            if not alarm_type and server_type == '状态':
                # 对于传输装置状态，检查是否包含故障信息
                if '故障' in raw_data or 'FSS=' in raw_data:
                    alarm_type = 'fault'
        
        # 如果服务器类型未识别，使用FDS_S字段
        if not alarm_type:
            # FDS_S 状态映射: 0=正常, 1=火警, 2=故障, 3=屏蔽, 4=反馈
            alarm_type_map = {
                '1': 'alarm',      # 火警/报警
                '2': 'fault',      # 故障
                '4': 'feedback'    # 反馈
            }
            if fds_s in alarm_type_map:
                alarm_type = alarm_type_map[fds_s]
        
        if alarm_type:
            info = self.ALARM_TYPES.get(alarm_type)
            
            if info:
                type_config = config.get(f'alarm.types.{alarm_type}', {})
                
                if not type_config.get('enabled', info['default']):
                    return alarms
                
                # 去重机制已禁用 - 每次报警都触发
                now = datetime.now()
                
                alarm_info = {
                    'type': alarm_type,
                    'type_name': info['name'],
                    'hid': hid,
                    'time': now.strftime("%Y-%m-%d %H:%M:%S"),
                    'raw_data': raw_data,
                    'sound': type_config.get('sound', True),
                    'popup': type_config.get('popup', True)
                }
                alarms.append(alarm_info)
                
                self.alarm_history.append(alarm_info)
                
                if len(self.alarm_history) > self.MAX_HISTORY_SIZE:
                    removed = self.alarm_history.pop(0)
                
                self.save_alarm_history()
        
        return alarms

    def _parse_data(self, raw_data: str) -> dict:
        """解析设备数据"""
        result = {}
        try:
            data = raw_data.strip()
            if data.startswith('{'):
                data = data[1:]
            if data.endswith('}'):
                data = data[:-1]
            
            for pair in data.split(','):
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    result[key.strip()] = value.strip()
        except Exception as e:
            print(f"[数据解析错误] {e}")
        return result

    def get_alarm_count(self):
        """获取今日报警数量"""
        try:
            # 计算今日的报警数量
            today = datetime.now().strftime("%Y-%m-%d")
            count = 0
            for alarm in self.alarm_history:
                if alarm.get('time', '').startswith(today):
                    count += 1
            print(f"[报警统计] 今日报警数量: {count}")
            return count
        except Exception as e:
            print(f"[报警统计] 获取报警数量失败: {e}")
            return 0
    
    def play_alarm_sound(self, alarm_type):
        if not config.get('alarm.sound.enabled', True):
            return None
        try:
            sound_files = {
                'alarm': 'D:\\1215\\bj.mp3',
                'feedback': 'D:\\1215\\fk.mp3',
                'fault': 'D:\\1215\\gz.mp3',
                'reset': 'D:\\1215\\fw.mp3'
            }
            sound_file = sound_files.get(alarm_type)
            if sound_file and os.path.exists(sound_file):
                import ctypes
                import threading
                
                class MultiSoundPlayer:
                    def __init__(self, sound_file, alarm_type):
                        self.sound_files = [(sound_file.replace('/', '\\'), alarm_type)]
                        self.running = True
                        self.current_index = 0
                        self.alias = "alarm_sound"
                        self.lock = threading.Lock()
                        self.thread = threading.Thread(target=self._play_loop, daemon=True)
                        self.thread.start()
                    
                    def add_sound(self, sound_file, alarm_type):
                        with self.lock:
                            if (sound_file.replace('/', '\\'), alarm_type) not in self.sound_files:
                                self.sound_files.append((sound_file.replace('/', '\\'), alarm_type))
                    
                    def _play_loop(self):
                        while self.running:
                            try:
                                with self.lock:
                                    if not self.sound_files or not self.running:
                                        break
                                    current_file, current_type = self.sound_files[self.current_index % len(self.sound_files)]
                                
                                ctypes.windll.winmm.mciSendStringW(
                                    f'open "{current_file}" alias {self.alias}',
                                    None, 0, None
                                )
                                ctypes.windll.winmm.mciSendStringW(
                                    f'play {self.alias} wait',
                                    None, 0, None
                                )
                                ctypes.windll.winmm.mciSendStringW(
                                    f'close {self.alias}',
                                    None, 0, None
                                )
                                
                                with self.lock:
                                    self.current_index += 1
                                    
                            except Exception as e:
                                break
                    
                    def stop(self):
                        self.running = False
                        try:
                            ctypes.windll.winmm.mciSendStringW(
                                f'stop {self.alias}',
                                None, 0, None
                            )
                            ctypes.windll.winmm.mciSendStringW(
                                f'close {self.alias}',
                                None, 0, None
                            )
                        except:
                            pass
                
                player = MultiSoundPlayer(sound_file, alarm_type)
                return player
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return None
        except Exception as e:
            print(f"播放报警声音失败: {e}")
            return None
    
    def stop_alarm_sound(self, sound_player):
        if sound_player:
            try:
                sound_player.stop()
            except Exception as e:
                print(f"停止报警声音失败: {e}")


# ===================== 设备名称管理器 =====================
class DeviceNameManager:
    """设备名称管理器 - 使用SQLite"""
    
    def __init__(self):
        self.device_names: Dict[str, str] = {}
        self._load_device_names()
    
    def _load_device_names(self):
        """从SQLite加载设备名称配置"""
        cursor = db_manager.get_main_connection().cursor()
        try:
            cursor.execute('SELECT hid, name FROM device_names')
            rows = cursor.fetchall()
            self.device_names = {}
            for row in rows:
                self.device_names[row[0]] = row[1]
        except Exception as e:
            print(f"[设备名称] 加载失败: {e}")
            self.device_names = {}
    
    def save_device_names(self):
        """保存设备名称配置到SQLite"""
        cursor = db_manager.get_main_connection().cursor()
        try:
            cursor.execute('DELETE FROM device_names')
            for hid, name in self.device_names.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO device_names (hid, name)
                    VALUES (?, ?)
                ''', (hid, name))
            db_manager.get_main_connection().commit()
        except Exception as e:
            print(f"[设备名称] 保存失败: {e}")
    
    def get_device_name(self, hid: str) -> str:
        """获取设备名称，如果没有设置则返回空字符串"""
        return self.device_names.get(hid, "")
    
    def set_device_name(self, hid: str, name: str):
        """设置设备名称"""
        if name and name.strip():
            self.device_names[hid] = name.strip()
        else:
            # 如果名称为空，删除该设备的自定义名称
            self.device_names.pop(hid, None)
        self.save_device_names()
    
    def get_display_name(self, hid: str) -> str:
        """获取显示名称：如果有自定义名称则返回 自定义名称(设备编号)，否则返回设备编号"""
        custom_name = self.get_device_name(hid)
        if custom_name:
            return f"{custom_name}({hid})"
        return hid
    
    def sync_to_server(self, main_window):
        """上传设备名称到服务器"""
        try:
            # ✅ 兼容两种属性名：.user (NetworkThread) 和 .current_user (MainWindow)
            user = getattr(main_window, 'current_user', None) or getattr(main_window, 'user', None)
            if not user:
                print("[设备名称] 未登录，无法同步")
                return False
            
            request_data = json.dumps({
                "action": "sync_device_names",
                "device_names": self.device_names
            })
            
            # ✅ 使用 network_thread 发送请求（send_request 是 NetworkThread 的方法）
            response = main_window.network_thread.send_request(request_data)
            if response and response.get('code') == 0:
                print(f"[设备名称] ✓ 同步成功: {response.get('msg')}")
                return True
            else:
                print(f"[设备名称] ✗ 同步失败: {response.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"[设备名称] 同步异常: {e}")
            return False
    
    def load_from_server(self, main_window):
        """从服务器下载设备名称"""
        try:
            # ✅ 兼容两种属性名：.user (NetworkThread) 和 .current_user (MainWindow)
            user = getattr(main_window, 'current_user', None) or getattr(main_window, 'user', None)
            if not user:
                print("[设备名称] 未登录，无法加载")
                return False
            
            request_data = json.dumps({
                "action": "get_device_names"
            })
            
            # ✅ 使用 network_thread 发送请求（send_request 是 NetworkThread 的方法）
            response = main_window.network_thread.send_request(request_data)
            if response and response.get('code') == 0:
                server_device_names = response.get('device_names', {})
                count = len(server_device_names)
                
                if count > 0:
                    # 合并服务器数据到本地（服务器优先）
                    for hid, name in server_device_names.items():
                        if name and name.strip():
                            self.device_names[hid] = name.strip()
                    
                    # 保存到本地数据库
                    self.save_device_names()
                    print(f"[设备名称] ✓ 从服务器加载了 {count} 个设备名称")
                else:
                    print(f"[设备名称] 服务器无设备名称数据")
                
                return True
            else:
                print(f"[设备名称] ✗ 加载失败: {response.get('msg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"[设备名称] 加载异常: {e}")
            return False
    
    def _parse_data(self, raw_data: str) -> dict:
        """解析设备数据"""
        result = {}
        try:
            data = raw_data.strip()
            if data.startswith('{'):
                data = data[1:]
            if data.endswith('}'):
                data = data[:-1]
            
            for pair in data.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    result[key.strip()] = value.strip()
        except Exception as e:
            print(f"解析数据失败: {e}")
        
        return result

# ===================== 登录对话框 =====================
class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"登录 - {APP_NAME}")
        self.setFixedSize(450, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        self._setup_ui()
        self._load_saved_credentials()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a5f; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # 表单
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        form_layout.addWidget(QLabel("账号:"), 0, 0)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入账号")
        self.username_input.setMinimumHeight(30)
        self.username_input.setStyleSheet("padding: 5px; font-size: 12px;")
        form_layout.addWidget(self.username_input, 0, 1)
        
        form_layout.addWidget(QLabel("密码:"), 1, 0)
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(30)
        self.password_input.setStyleSheet("padding: 5px; font-size: 12px;")
        
        # 添加显示/隐藏密码按钮
        self.toggle_password_btn = QPushButton("显示")
        self.toggle_password_btn.setFixedSize(50, 30)
        self.toggle_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self._toggle_password_visibility)
        
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_btn)
        form_layout.addLayout(password_layout, 1, 1)
        
        layout.addLayout(form_layout)
        
        self.remember_checkbox = QCheckBox("记住账号密码")
        layout.addWidget(self.remember_checkbox)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #ff6b35;")
        layout.addWidget(self.status_label)
        
        self.login_btn = QPushButton("登录")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e3a5f;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2a4a73;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)
        
        # 忘记密码按钮
        self.forgot_password_btn = QPushButton("忘记密码？")
        self.forgot_password_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1e3a5f;
                padding: 5px;
                font-size: 12px;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #2a4a73;
            }
        """)
        self.forgot_password_btn.clicked.connect(self._on_forgot_password)
        
        # 关于按钮
        about_btn = QPushButton("ℹ️ 关于")
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                padding: 5px 10px;
                font-size: 12px;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #1e3a5f;
            }
        """)
        about_btn.clicked.connect(self._show_about)
        
        # 将两个按钮放在同一行，避免重叠
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.forgot_password_btn)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(about_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.password_input.returnPressed.connect(self._on_login)
    
    def _toggle_password_visibility(self, checked):
        """切换密码显示/隐藏"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("隐藏")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("显示")
    
    def _load_saved_credentials(self):
        """加载保存的账号密码"""
        last_user = config.get('user.last_username', '')
        remember = config.get('user.remember_password', False)
        
        if last_user and remember:
            self.username_input.setText(last_user)
            self.remember_checkbox.setChecked(True)
            
            # ✅ 加载并解密密码
            encoded_pwd = config.get('user.last_password', '')
            if encoded_pwd:
                try:
                    import base64
                    decoded_pwd = base64.b64decode(encoded_pwd.encode('utf-8')).decode('utf-8')
                    self.password_input.setText(decoded_pwd)
                except Exception as e:
                    print(f"[登录] 解码保存的密码失败: {e}")
            
            self.password_input.setFocus()
    
    def _on_login(self):
        """登录按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            self.status_label.setText("请输入账号和密码")
            return
        
        config.set('user.remember_password', self.remember_checkbox.isChecked())
        if self.remember_checkbox.isChecked():
            config.set('user.last_username', username)
            # ✅ 保存加密后的密码
            import base64
            encoded_pwd = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            config.set('user.last_password', encoded_pwd)
        else:
            # ✅ 取消勾选时，清除保存的凭证
            config.set('user.last_username', '')
            config.set('user.last_password', '')
        
        self.login_btn.setEnabled(False)
        self.status_label.setText("正在连接服务器...")
        self.status_label.setStyleSheet("color: #1e3a5f;")
        
        self.accepted_credentials = (username, password)
        self.accept()
    
    def get_credentials(self) -> Tuple[str, str]:
        """获取登录凭据"""
        return getattr(self, 'accepted_credentials', ('', ''))

    def _on_forgot_password(self):
        """忘记密码按钮点击"""
        QMessageBox.information(
            self,
            "忘记密码",
            "如需重置密码，请联系售后：\n\n"
            "电话：13037990547"
        )
    
    def _show_about(self):
        """显示关于信息"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("关于")
        about_dialog.setFixedSize(350, 220)
        
        layout = QVBoxLayout(about_dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e3a5f;")
        layout.addWidget(title)
        
        info_text = f"""
        <div style='text-align: center; color: #666;'>
            <p style='font-size: 14px; color: #333; font-weight: bold;'>版本: {APP_VERSION}</p>
            <p style='margin-top: 10px;'>技术支持: mevenly@outlook.com</p>
            <p style='margin-top: 5px;'>📞 电话: 13037990547</p>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setOpenExternalLinks(True)
        layout.addWidget(info_label)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        close_btn.clicked.connect(about_dialog.close)
        layout.addWidget(close_btn)
        
        about_dialog.exec()

# ===================== 报警设置对话框 =====================
class AlarmSettingsDialog(QDialog):
    """报警设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("报警设置")
        self.setFixedSize(500, 500)
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 总开关
        self.master_switch = QCheckBox("启用报警提示")
        self.master_switch.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(self.master_switch)
        
        # 报警类型设置
        group = QGroupBox("报警类型设置（选中的类型会进行报警提示）")
        group_layout = QVBoxLayout(group)
        
        self.alarm_type_checks = {}
        
        # 报警类型 - 改为可选，默认勾选（报警）
        alarm_group = QGroupBox("报警（火警）")
        alarm_layout = QHBoxLayout(alarm_group)
        alarm_layout.setSpacing(10)
        
        # 启用复选框（勾选后自动播放声音+弹窗）
        alarm_enable = QCheckBox("启用")
        alarm_enable.setChecked(True)  # 默认勾选
        alarm_enable.setToolTip("ALM=1表示设备报警，勾选后将播放声音并显示弹窗")
        alarm_layout.addWidget(alarm_enable)
        alarm_layout.addStretch()
        
        group_layout.addWidget(alarm_group)
        self.alarm_type_checks['alarm'] = {
            'enable': alarm_enable
        }
        
        # 其他可选报警类型
        optional_types = [
            ('fault', '故障', 'FLT=1表示设备故障'),
            ('feedback', '反馈', 'FBK=1表示设备反馈'),
            ('reset', '复位', 'RST=1表示设备复位')
        ]
        
        for type_key, name, desc in optional_types:
            type_group = QGroupBox(name)
            type_layout = QHBoxLayout(type_group)
            type_layout.setSpacing(10)
            
            # 启用复选框（勾选后自动播放声音+弹窗）
            enable_check = QCheckBox("启用")
            enable_check.setToolTip(f"{desc}，勾选后将播放声音并显示弹窗")
            type_layout.addWidget(enable_check)
            type_layout.addStretch()
            
            group_layout.addWidget(type_group)
            
            self.alarm_type_checks[type_key] = {
                'enable': enable_check
            }
        
        layout.addWidget(group)
        
        # 声音设置（隐藏，默认启用最大音量）
        self.sound_enable = QCheckBox("启用声音提示")
        self.sound_enable.setChecked(True)
        self.sound_enable.hide()  # 隐藏但保持功能
        
        # 音量固定为100%，隐藏控件
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(100, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.hide()
        
        # 弹窗设置（简化，默认启用置顶）
        self.popup_enable = QCheckBox("启用弹窗提示")
        self.popup_enable.setChecked(True)
        self.popup_enable.hide()  # 隐藏但保持功能
        
        self.popup_topmost = QCheckBox("弹窗置顶显示（确保能看到）")
        self.popup_topmost.hide()  # 隐藏但保持功能
        
        layout.addStretch()
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        
        version_label = QLabel(f"📱 {APP_NAME} <b>{APP_VERSION}</b>")
        version_label.setStyleSheet("font-size: 14px; color: #333;")
        about_layout.addWidget(version_label)
        
        support_label = QLabel("技术支持: mevenly@outlook.com")
        support_label.setStyleSheet("font-size: 12px; color: #666;")
        about_layout.addWidget(support_label)
        
        phone_label = QLabel("📞 电话: 13037990547")
        phone_label.setStyleSheet("font-size: 12px; color: #17a2b8; font-weight: bold;")
        about_layout.addWidget(phone_label)
        
        copyright_label = QLabel("© 2026 All Rights Reserved")
        copyright_label.setStyleSheet("font-size: 11px; color: #999;")
        about_layout.addWidget(copyright_label)
        
        layout.addWidget(about_group)
        
        # 在线升级按钮
        check_update_btn = QPushButton("🔄 检查更新")
        check_update_btn.setToolTip("检查是否有新版本可用")
        check_update_btn.setCursor(Qt.PointingHandCursor)
        check_update_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        check_update_btn.clicked.connect(self._manual_check_update)
        layout.addWidget(check_update_btn)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 20px;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.default_btn = QPushButton("🔄 恢复默认")
        self.default_btn.clicked.connect(self._load_default)
        btn_layout.addWidget(self.default_btn)
        
        btn_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """加载设置"""
        self.master_switch.setChecked(config.get('alarm.enabled', True))
        
        for type_key, checks in self.alarm_type_checks.items():
            type_config = config.get(f'alarm.types.{type_key}', {})
            checks['enable'].setChecked(
                type_config.get('enabled', type_key in ['fault', 'alarm'])
            )
    
    def _save_settings(self):
        """保存设置"""
        config.set('alarm.enabled', self.master_switch.isChecked())
        
        for type_key, checks in self.alarm_type_checks.items():
            enabled = checks['enable'].isChecked()
            config.set(f'alarm.types.{type_key}.enabled', enabled)
            # 勾选启用时，自动启用声音和弹窗
            config.set(f'alarm.types.{type_key}.sound', enabled)
            config.set(f'alarm.types.{type_key}.popup', enabled)
        config.set('alarm.popup.stay_on_top', True)
        
        # 使用非模态提示，避免阻塞报警弹窗
        self._show_non_blocking_message("保存成功", "报警设置已保存！")
        self.accept()
    
    def _manual_check_update(self):
        """手动检查更新（从设置页面触发）"""
        try:
            # 获取主窗口引用
            main_window = self.parent()
            if not main_window:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "⚠️ 提示",
                    "无法检查更新：未找到主窗口",
                    QMessageBox.Ok
                )
                return
            
            # 调用主窗口的版本检查方法
            main_window._check_for_updates()
            
            # 显示正在检查的提示
            self._show_non_blocking_message("🔄 检查中", "正在检查更新，请稍候...")
            
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "❌ 错误",
                f"检查更新失败：\n\n{str(e)}",
                QMessageBox.Ok
            )
    
    def _show_non_blocking_message(self, title: str, message: str):
        """显示非模态提示消息"""
        # 创建一个简单的非模态提示窗口
        msg_label = QLabel(message, self)
        msg_label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
            }
        """)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_label.setFixedSize(200, 50)
        
        # 定位在窗口中央
        msg_label.move(
            (self.width() - msg_label.width()) // 2,
            (self.height() - msg_label.height()) // 2
        )
        msg_label.show()
        
        # 2秒后自动关闭
        QTimer.singleShot(2000, msg_label.deleteLater)
    
    def _load_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.master_switch.setChecked(True)
            
            # 报警（火警）固定启用
            self.alarm_type_checks['alarm']['enable'].setChecked(True)
            
            # 故障默认开启
            self.alarm_type_checks['fault']['enable'].setChecked(True)
            
            # 反馈和复位默认关闭
            self.alarm_type_checks['feedback']['enable'].setChecked(False)
            self.alarm_type_checks['reset']['enable'].setChecked(False)
            
            # 声音和弹窗固定启用
            self.sound_enable.setChecked(True)
            self.popup_enable.setChecked(True)
            self.popup_topmost.setChecked(True)

# ===================== 报警弹窗 =====================
class AlarmPopup(QDialog):
    """报警弹窗 - 单例模式，支持内容更新"""
    
    _instance = None
    
    @classmethod
    def show_alarm(cls, alarm_info: dict, stats: dict = None, parent=None, on_close_callback=None, device_name_manager=None):
        """工厂方法：显示报警弹窗或更新现有弹窗
        
        Args:
            alarm_info: 当前报警信息
            stats: 报警统计数据，格式为 {'alarm': 5, 'fault': 2, 'feedback': 1, 'reset': 0}
            parent: 父窗口
            on_close_callback: 弹窗关闭时的回调函数
            device_name_manager: 设备名称管理器，用于显示设备名称
        """
        # 如果实例已存在且可见，更新内容
        if cls._instance is not None:
            try:
                if cls._instance.isVisible():
                    cls._instance.update_alarm_info(alarm_info, stats, device_name_manager)
                    cls._instance.raise_()
                    cls._instance.activateWindow()
                    return cls._instance
            except RuntimeError:
                # 实例已被删除
                cls._instance = None
        
        # 创建新实例 - 使用None作为父窗口，避免被模态对话框阻塞
        cls._instance = cls(alarm_info, parent)
        cls._instance._on_close_callback = on_close_callback
        cls._instance._device_name_manager = device_name_manager
        # 设置弹窗出现时间（静态，只在创建时设置）
        from datetime import datetime
        popup_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        cls._instance.popup_time_label.setText(f"首次报警时间: {popup_time}")
        # 如果有统计数据，更新显示
        if stats:
            cls._instance._update_stats_display(stats)
        
        # 播放报警声音
        if alarm_info and alarm_info.get('sound'):
            alarm_type = alarm_info.get('type', '')
            if parent and hasattr(parent, 'alarm_manager'):
                cls._instance.sound_player = parent.alarm_manager.play_alarm_sound(alarm_type)
        
        cls._instance.show()
        cls._instance.raise_()
        cls._instance.activateWindow()
        return cls._instance
    
    def __init__(self, alarm_info: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔴 设备报警提醒")
        self.setFixedSize(520, 400)
        
        # 保存父窗口引用
        self.parent = parent
        
        # 声音播放器
        self.sound_player = None
        
        if config.get('alarm.popup.stay_on_top', True):
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Window |
                Qt.WindowType.WindowCloseButtonHint
            )
        
        self._setup_ui()
        if alarm_info:
            self.update_alarm_info(alarm_info)
    
    def _setup_ui(self):
        """初始化UI结构"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 报警图标和标题
        self.header = QLabel("⚠️ 检测到报警信号")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #dc3545;
            padding: 5px;
        """)
        layout.addWidget(self.header)
        
        # 弹窗出现时间（放在顶部）
        self.popup_time_label = QLabel()
        self.popup_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.popup_time_label.setStyleSheet("""
            font-size: 13px;
            color: #666;
            padding: 2px;
            border: none;
            background: transparent;
        """)
        layout.addWidget(self.popup_time_label)
        
        # 报警信息框
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 8px;
            }
        """)
        self.info_layout = QGridLayout(self.info_frame)
        self.info_layout.setSpacing(5)
        self.info_layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.info_frame)
        
        # 创建信息标签（用于后续更新）
        label_style = "font-size: 14px; font-weight: bold; color: #555; border: none; background: transparent;"
        value_style = "font-size: 14px; color: #000; border: none; background: transparent;"
        
        # 设备编号
        device_label = QLabel("设备编号:")
        device_label.setStyleSheet(label_style)
        self.info_layout.addWidget(device_label, 0, 0)
        self.device_value = QLabel()
        self.device_value.setStyleSheet(value_style)
        self.info_layout.addWidget(self.device_value, 0, 1)
        
        # 报警时间
        time_label = QLabel("报警时间:")
        time_label.setStyleSheet(label_style)
        self.info_layout.addWidget(time_label, 1, 0)
        self.time_value = QLabel()
        self.time_value.setStyleSheet(value_style)
        self.info_layout.addWidget(self.time_value, 1, 1)
        
        # 详细信息框
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border: 2px solid #4dabf7;
                border-radius: 8px;
            }
        """)
        self.detail_layout = QGridLayout(self.detail_frame)
        self.detail_layout.setSpacing(3)
        self.detail_layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.detail_frame)
        
        # 详细信息标签
        detail_label_style = "font-size: 13px; font-weight: bold; color: #1971c2; border: none; background: transparent;"
        detail_value_style = "font-size: 13px; color: #000; border: none; background: transparent;"
        
        # 设备类型
        self.type_label = QLabel("设备类型:")
        self.type_label.setStyleSheet(detail_label_style)
        self.type_label.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.type_label, 0, 0)
        self.type_detail_value = QLabel()
        self.type_detail_value.setStyleSheet(detail_value_style)
        self.type_detail_value.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.type_detail_value, 0, 1)
        
        # 设备位置
        self.pos_label = QLabel("设备位置:")
        self.pos_label.setStyleSheet(detail_label_style)
        self.pos_label.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.pos_label, 1, 0)
        self.pos_value = QLabel()
        self.pos_value.setStyleSheet(detail_value_style)
        self.pos_value.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.pos_value, 1, 1)
        
        # 设备编号（FDS_C）
        self.code_label = QLabel("设备编号:")
        self.code_label.setStyleSheet(detail_label_style)
        self.code_label.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.code_label, 2, 0)
        self.code_value = QLabel()
        self.code_value.setStyleSheet(detail_value_style)
        self.code_value.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.code_value, 2, 1)
        
        # 当前状态
        self.status_label = QLabel("当前状态:")
        self.status_label.setStyleSheet(detail_label_style)
        self.status_label.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.status_label, 3, 0)
        self.status_value = QLabel()
        self.status_value.setStyleSheet("font-size: 13px; font-weight: bold; color: #dc3545; border: none; background: transparent;")
        self.status_value.setVisible(False)  # 初始隐藏
        self.detail_layout.addWidget(self.status_value, 3, 1)
        
        # 统计信息框
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        self.stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_layout.setSpacing(10)
        self.stats_layout.setContentsMargins(10, 8, 10, 8)
        layout.addWidget(self.stats_frame)
        
        # 统计标签
        self.stats_label = QLabel("📊 报警统计: 等待数据...")
        self.stats_label.setStyleSheet("font-size: 12px; color: #495057; border: none; background: transparent;")
        self.stats_layout.addWidget(self.stats_label)
        self.stats_layout.addStretch()
        
        # 按钮 - 居中显示
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        confirm_btn = QPushButton("✓ 确认收到")
        confirm_btn.setFixedSize(150, 45)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 30px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def update_alarm_info(self, info: dict, stats: dict = None, device_name_manager=None):
        """更新报警信息
        
        Args:
            info: 当前报警信息
            stats: 报警统计数据，格式为 {'alarm': 5, 'fault': 2, 'feedback': 1, 'reset': 0}
            device_name_manager: 设备名称管理器
        """
        # 添加新报警类型的声音到播放列表
        if self.sound_player and hasattr(self.sound_player, 'add_sound') and info.get('sound'):
            alarm_type = info.get('type', '')
            sound_files = {
                'alarm': 'D:\\1215\\bj.mp3',
                'feedback': 'D:\\1215\\fk.mp3',
                'fault': 'D:\\1215\\gz.mp3',
                'reset': 'D:\\1215\\fw.mp3'
            }
            sound_file = sound_files.get(alarm_type)
            if sound_file:
                self.sound_player.add_sound(sound_file, alarm_type)
        
        # 更新基本信息 - 使用设备名称
        hid = info['hid']
        if device_name_manager:
            display_name = device_name_manager.get_display_name(hid)
        elif hasattr(self, '_device_name_manager') and self._device_name_manager:
            display_name = self._device_name_manager.get_display_name(hid)
        else:
            display_name = hid
        self.device_value.setText(f"<b>{display_name}</b>")
        self.time_value.setText(info['time'])
        # 注意：弹窗时间只在创建时设置，这里不更新
        
        # 解析并更新详细信息
        device_info = self._parse_alarm_data(info['raw_data'])
        
        # 更新详细信息
        if device_info.get('type'):
            self.type_label.setVisible(True)
            self.type_detail_value.setVisible(True)
            self.type_detail_value.setText(device_info['type'])
        else:
            self.type_label.setVisible(False)
            self.type_detail_value.setVisible(False)
        
        if device_info.get('position'):
            self.pos_label.setVisible(True)
            self.pos_value.setVisible(True)
            self.pos_value.setText(device_info['position'])
        else:
            self.pos_label.setVisible(False)
            self.pos_value.setVisible(False)
        
        if device_info.get('code'):
            self.code_label.setVisible(True)
            self.code_value.setVisible(True)
            self.code_value.setText(device_info['code'])
        else:
            self.code_label.setVisible(False)
            self.code_value.setVisible(False)
        
        if device_info.get('status'):
            self.status_label.setVisible(True)
            self.status_value.setVisible(True)
            self.status_value.setText(device_info['status'])
        else:
            self.status_label.setVisible(False)
            self.status_value.setVisible(False)
        
        # 更新统计信息
        if stats:
            self._update_stats_display(stats)
        
        # 更新窗口标题，显示最新的报警次数
        self.setWindowTitle(f"🔴 设备报警提醒 - {info['time']}")
        
        # 强制刷新显示
        self.update()
        self.raise_()
        self.activateWindow()
    
    def _update_stats_display(self, stats: dict):
        """更新统计信息显示 - 只显示用户在设置中启用了弹窗的报警类型"""
        # 获取用户在设置中启用了弹窗的报警类型
        enabled_types = []
        type_names = {
            'alarm': '🔥火警',
            'fault': '⚠️故障',
            'feedback': '📢反馈',
            'reset': '🔄复位'
        }
        
        for type_key, name in type_names.items():
            # 检查该类型是否启用了弹窗
            type_config = config.get(f'alarm.types.{type_key}', {})
            if type_config.get('popup', False) and stats.get(type_key, 0) > 0:
                enabled_types.append(f"{name}: {stats[type_key]}条")
        
        if enabled_types:
            self.stats_label.setText("📊 本次报警统计: " + " | ".join(enabled_types))
        else:
            self.stats_label.setText("📊 暂无报警统计")
    
    def _on_confirm(self):
        """确认收到按钮 - 隐藏弹窗而不是关闭"""
        # 停止报警声音
        if self.sound_player:
            try:
                if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'alarm_manager'):
                    self.parent.alarm_manager.stop_alarm_sound(self.sound_player)
                else:
                    # 如果没有 parent 引用，直接调用 stop
                    self.sound_player.stop()
            except Exception as e:
                print(f"[报警弹窗] 停止声音失败: {e}")
        
        self.hide()
        # 调用关闭回调
        if hasattr(self, '_on_close_callback') and self._on_close_callback:
            self._on_close_callback()
        # 重置实例，允许下次创建新弹窗
        AlarmPopup._instance = None
    
    def closeEvent(self, event):
        """关闭事件 - 隐藏而不是关闭"""
        # 停止报警声音
        if self.sound_player:
            try:
                if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'alarm_manager'):
                    self.parent.alarm_manager.stop_alarm_sound(self.sound_player)
                else:
                    self.sound_player.stop()
            except Exception as e:
                print(f"[报警弹窗] 停止声音失败: {e}")
        
        event.ignore()
        self.hide()
        # 调用关闭回调
        if hasattr(self, '_on_close_callback') and self._on_close_callback:
            self._on_close_callback()
        # 重置实例，允许下次创建新弹窗
        AlarmPopup._instance = None
        event.ignore()  # 忽略关闭事件，防止应用程序退出
    
    def _parse_alarm_data(self, raw_data: str) -> dict:
        """解析报警原始数据，提取详细信息"""
        result = {}
        try:
            # 提取 FDS_T (设备类型)
            if "FDS_T=" in raw_data:
                start = raw_data.index("FDS_T=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    result['type'] = raw_data[start:end].strip()
            
            # 提取 FDS_P (设备位置)
            if "FDS_P=" in raw_data:
                start = raw_data.index("FDS_P=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    result['position'] = raw_data[start:end].strip()
            
            # 提取 FDS_C (设备编号/回路号)
            if "FDS_C=" in raw_data:
                start = raw_data.index("FDS_C=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    result['code'] = raw_data[start:end].strip()
            
            # 提取传输装置状态 (TDP_M, TDP_B, TDL_A) - 优先处理
            status_parts = []
            if "TDP_M=" in raw_data:
                start = raw_data.index("TDP_M=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    tdp_m = raw_data[start:end].strip()
                    print(f"[解析报警数据] TDP_M={tdp_m}")
                    if tdp_m and tdp_m != '正常':
                        status_parts.append(f"主电:{tdp_m}")
            
            if "TDP_B=" in raw_data:
                start = raw_data.index("TDP_B=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    tdp_b = raw_data[start:end].strip()
                    print(f"[解析报警数据] TDP_B={tdp_b}")
                    if tdp_b and tdp_b != '正常':
                        status_parts.append(f"备电:{tdp_b}")
            
            if "TDL_A=" in raw_data:
                start = raw_data.index("TDL_A=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    tdl_a = raw_data[start:end].strip()
                    print(f"[解析报警数据] TDL_A={tdl_a}")
                    if tdl_a and tdl_a != '正常':
                        status_parts.append(f"连接:{tdl_a}")
            
            if status_parts:
                # 将 "备电:故障" 转换为 "备电故障" 格式
                formatted_status = ", ".join(status_parts)
                # 移除冒号，使显示更简洁："备电:故障" -> "备电故障"
                formatted_status = formatted_status.replace(':', '')
                result['status'] = formatted_status
                print(f"[解析报警数据] 传输装置状态: {result['status']}")
            # 如果没有传输装置状态，再检查 FDS_S
            elif "FDS_S=" in raw_data:
                start = raw_data.index("FDS_S=") + 6
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    status_code = raw_data[start:end].strip()
                    status_map = {
                        '0': '正常',
                        '1': '火警',
                        '2': '故障',
                        '3': '屏蔽',
                        '4': '反馈'
                    }
                    result['status'] = status_map.get(status_code, f'未知状态({status_code})')
                    print(f"[解析报警数据] FDS_S状态: {result['status']}")
            
            # 检查 FSS 系统状态（用于复位等系统级状态）
            if "FSS=" in raw_data:
                start = raw_data.index("FSS=") + 4
                end = raw_data.find(",", start)
                if end == -1:
                    end = raw_data.find("}", start)
                if end != -1:
                    fss_value = raw_data[start:end].strip()
                    print(f"[解析报警数据] FSS={fss_value}")
                    if fss_value:
                        # FSS 状态直接显示
                        result['status'] = fss_value
                        print(f"[解析报警数据] FSS状态: {result['status']}")
        except Exception as e:
            print(f"[解析报警数据失败] {e}")
        
        return result

# ===================== 主窗口 =====================
class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - {APP_VERSION}")
        self.resize(1200, 800)
        
        # 创建消防相关的图标
        self._create_fire_icon()
        
        self.current_user: Optional[str] = None
        self.current_password: str = ""
        self.is_admin: bool = False
        self.auth_token: str = ""  # ✅ 认证Token（登录后获得）
        self.cache_manager: Optional[CacheManager] = None
        self.alarm_manager = AlarmManager(self)
        self.network_thread: Optional[NetworkThread] = None
        self.devices: set = set()
        self.device_online_status: Dict[str, datetime] = {}  # 设备最后通信时间
        self.assigned_devices: set = set()
        self._settings_dialog = None  # 设置对话框引用
        self.device_name_manager = DeviceNameManager()  # 设备名称管理器
        self._device_error_shown = False  # 防止重复弹窗标志
        self._is_logging_out = False  # ✅ 是否正在退出登录（防止显示断网提示）
        
        self._setup_ui()
        self._setup_tray()
        
        # 连接设备分配表格更新信号
        self.update_assignment_table_signal.connect(self._do_update_assignment_table)
    
    def _create_fire_icon(self):
        """创建消防相关的图标"""
        try:
            # 创建一个红色的火焰图标
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制红色火焰
            painter.setBrush(QColor(255, 0, 0))  # 红色
            painter.setPen(QPen(QColor(200, 0, 0), 2))  # 深红色边框
            
            # 绘制火焰形状
            points = [
                QPoint(32, 10),  # 顶部
                QPoint(45, 25),  # 右上
                QPoint(40, 45),  # 右下
                QPoint(32, 55),  # 底部
                QPoint(24, 45),  # 左下
                QPoint(19, 25)   # 左上
            ]
            painter.drawPolygon(QPolygon(points))
            
            # 绘制火焰内部的高光
            painter.setBrush(QColor(255, 100, 0))  # 橙红色
            inner_points = [
                QPoint(32, 15),
                QPoint(40, 28),
                QPoint(37, 40),
                QPoint(32, 48),
                QPoint(27, 40),
                QPoint(24, 28)
            ]
            painter.drawPolygon(QPolygon(inner_points))
            
            painter.end()
            
            self.fire_icon = QIcon(pixmap)
            self.setWindowIcon(self.fire_icon)
            print("[图标] 消防图标创建成功")
        except Exception as e:
            print(f"[图标错误] 创建消防图标失败: {e}")
            # 使用默认图标作为备选方案
            self.fire_icon = QIcon()
            self.setWindowIcon(self.fire_icon)
    
    def _setup_ui(self):
        """设置UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.sidebar = self._create_sidebar()
        splitter.addWidget(self.sidebar)
        
        self.content_stack = QTabWidget()
        self.content_stack.setTabPosition(QTabWidget.TabPosition.West)
        self.content_stack.tabBar().hide()
        
        self._create_pages()
        splitter.addWidget(self.content_stack)
        splitter.setSizes([200, 1000])
        
        layout.addWidget(splitter, 1)
        
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)
        self.statusbar.addPermanentWidget(QLabel(f"版本: {APP_VERSION}"))
        self.cache_label = QLabel("缓存: 0文件")
        self.statusbar.addPermanentWidget(self.cache_label)
        self.server_label = QLabel("服务器: 未连接")
        self.statusbar.addPermanentWidget(self.server_label)
    
    def _create_toolbar(self) -> QFrame:
        """创建顶部工具栏"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #1e3a5f;
                color: white;
                padding: 5px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #ff6b35;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e55a2b;
            }
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()
        
        self.user_label = QLabel("未登录")
        layout.addWidget(self.user_label)
        
        self.role_label = QLabel("")
        layout.addWidget(self.role_label)
        
        self.alarm_btn = QPushButton("🔔 今日报警数: 0")
        self.alarm_btn.setVisible(False)
        self.alarm_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
            }
        """)
        layout.addWidget(self.alarm_btn)
        
        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 15px;
                font-size: 13px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)
        
        service_btn = QPushButton("📞 客服")
        service_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 15px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        service_btn.clicked.connect(self._show_service_contact)
        layout.addWidget(service_btn)
        
        logout_btn = QPushButton("退出")
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)
        
        return toolbar
    
    def _create_sidebar(self) -> QFrame:
        """创建侧边栏"""
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                border: none;
                background-color: transparent;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:checked {
                background-color: #1e3a5f;
                color: white;
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 10, 0, 10)
        
        self.menu_buttons = []
        
        menus = [
            ("📊 实时数据", 0),
            ("📱 设备列表", 1),
            ("📜 历史查询", 2),
            ("📋 数据导出", 3),
        ]
        
        for text, index in menus:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            layout.addWidget(btn)
            self.menu_buttons.append(btn)
        
        self.admin_menus = []
        admin_menus = [
            ("👤 用户管理", 4),
            ("🔧 设备分配", 5),
        ]
        
        for text, index in admin_menus:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            btn.setVisible(False)
            layout.addWidget(btn)
            self.menu_buttons.append(btn)
            self.admin_menus.append(btn)
        
        layout.addStretch()
        self.menu_buttons[0].setChecked(True)
        
        return sidebar
    
    def _create_pages(self):
        """创建各个页面"""
        self.realtime_page = self._create_realtime_page()
        self.content_stack.addTab(self.realtime_page, "实时数据")
        
        self.device_list_page = self._create_device_list_page()
        self.content_stack.addTab(self.device_list_page, "设备列表")
        
        self.history_page = self._create_history_page()
        self.content_stack.addTab(self.history_page, "历史查询")
        
        self.export_page = self._create_export_page()
        self.content_stack.addTab(self.export_page, "数据导出")
        
        self.user_page = self._create_user_page()
        self.content_stack.addTab(self.user_page, "用户管理")
        
        self.device_page = self._create_device_page()
        self.content_stack.addTab(self.device_page, "设备分配")
    
    def _create_realtime_page(self) -> QWidget:
        """创建实时数据页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        toolbar = QHBoxLayout()
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self._toggle_pause)
        toolbar.addWidget(self.pause_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self._clear_realtime)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        # 保持唤醒功能（防止系统黑屏/息屏/睡眠）
        self.keep_awake = QCheckBox("☕ 保持唤醒")
        self.keep_awake.setChecked(True)  # 默认启用保持唤醒
        self.keep_awake.setStyleSheet("color: #e83e8c; font-weight: bold;")
        self.keep_awake.setToolTip("启用后防止系统自动黑屏、息屏、睡眠或关机")
        self.keep_awake.stateChanged.connect(self._toggle_keep_awake)
        toolbar.addWidget(self.keep_awake)
        
        # 显示心跳功能（默认不勾选，不显示心跳数据）
        self.show_heartbeat = QCheckBox("💓 显示心跳")
        settings = QSettings("FireMonitor", "FireMonitorClient")
        self.show_heartbeat.setChecked(settings.value("show_heartbeat", False, type=bool))
        self.show_heartbeat.setStyleSheet("color: #17a2b8; font-weight: bold;")
        self.show_heartbeat.setToolTip("勾选后在实时数据表格中显示心跳包数据\n不勾选则过滤掉心跳数据，只显示有效业务数据")
        self.show_heartbeat.stateChanged.connect(self._toggle_show_heartbeat)
        toolbar.addWidget(self.show_heartbeat)
        
        # 默认启用保持唤醒
        self._keep_awake_enabled = True
        self._enable_keep_awake()
        
        layout.addLayout(toolbar)
        
        self.realtime_table = QTableWidget()
        self.realtime_table.setColumnCount(4)
        self.realtime_table.setHorizontalHeaderLabels(["时间", "设备", "数据内容", "状态"])
        self.realtime_table.horizontalHeader().setStretchLastSection(True)
        self.realtime_table.setAlternatingRowColors(True)
        
        # ✅ 设置表格字体大小（增大到12pt）
        table_font = QFont()
        table_font.setPointSize(12)
        self.realtime_table.setFont(table_font)
        
        # ✅ 设置表头字体（与内容一致）
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        self.realtime_table.horizontalHeader().setFont(header_font)
        
        # 禁止编辑
        self.realtime_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置列宽
        self.realtime_table.setColumnWidth(0, 180)  # 时间（包含年月日，不换行）
        self.realtime_table.setColumnWidth(1, 100)  # 设备名称（自动调整）
        self.realtime_table.setColumnWidth(2, 300)  # 数据内容（自动换行，可多行显示）
        self.realtime_table.setColumnWidth(3, 60)   # 状态
        
        # ✅ 设置默认行高（适应12pt字体）
        self.realtime_table.verticalHeader().setDefaultSectionSize(28)
        
        layout.addWidget(self.realtime_table)
        
        self.stats_label = QLabel("接收: 0条 | 心跳: 0条 | 🔥火警: 0条 | ⚠️故障: 0条 | 📢反馈: 0条 | 🔄复位: 0条")
        layout.addWidget(self.stats_label)
        
        self.realtime_stats = {'total': 0, 'heartbeat': 0, 'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
        
        # 弹窗报警统计 - 累计本次弹窗显示期间收到的各类报警数量
        self._popup_alarm_stats = {'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
        
        return page
    
    def _create_device_list_page(self) -> QWidget:
        """创建设备列表页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.refresh_devices_btn = QPushButton("🔄 刷新设备列表")
        self.refresh_devices_btn.clicked.connect(self._refresh_device_list)
        toolbar.addWidget(self.refresh_devices_btn)
        
        toolbar.addStretch()
        
        self.device_count_label = QLabel("设备数量: 0")
        toolbar.addWidget(self.device_count_label)
        
        layout.addLayout(toolbar)
        
        # 设备列表表格
        self.device_list_table = QTableWidget()
        self.device_list_table.setColumnCount(5)
        self.device_list_table.setHorizontalHeaderLabels(["设备编号", "设备名称", "在线状态", "最新数据时间", "操作"])
        self.device_list_table.horizontalHeader().setStretchLastSection(True)
        # 禁止编辑（设备名称通过修改按钮编辑）
        self.device_list_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置列宽
        self.device_list_table.setColumnWidth(0, 120)  # 设备编号
        self.device_list_table.setColumnWidth(1, 150)  # 设备名称
        self.device_list_table.setColumnWidth(2, 100)  # 在线状态
        self.device_list_table.setColumnWidth(3, 150)  # 最新数据时间
        self.device_list_table.setColumnWidth(4, 250)  # 操作（增加宽度）
        
        layout.addWidget(self.device_list_table)
        
        # 说明标签
        info_label = QLabel("💡 提示：点击设备行的'查看历史'按钮可查看该设备的历史数据")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)
        
        return page
    
    def _create_history_page(self) -> QWidget:
        """创建历史查询页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 第一行工具栏 - 缓存查询
        toolbar1 = QHBoxLayout()
        
        toolbar1.addWidget(QLabel("设备:"))
        self.history_device = QComboBox()
        self.history_device.setMinimumWidth(150)
        toolbar1.addWidget(self.history_device)
        
        toolbar1.addWidget(QLabel("开始日期:"))
        self.history_start_date = QDateEdit()
        self.history_start_date.setCalendarPopup(True)
        self.history_start_date.setDisplayFormat("yyyy-MM-dd")
        self.history_start_date.setDate(QDate.currentDate().addDays(-6))  # 默认7天前
        toolbar1.addWidget(self.history_start_date)
        
        toolbar1.addWidget(QLabel("结束日期:"))
        self.history_end_date = QDateEdit()
        self.history_end_date.setCalendarPopup(True)
        self.history_end_date.setDisplayFormat("yyyy-MM-dd")
        self.history_end_date.setDate(QDate.currentDate())  # 默认今天
        toolbar1.addWidget(self.history_end_date)
        
        self.query_btn = QPushButton("🔍 查询数据")
        self.query_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.query_btn.clicked.connect(self._query_history)
        toolbar1.addWidget(self.query_btn)
        
        self.clear_cache_btn = QPushButton("🗑️ 清空数据")
        self.clear_cache_btn.clicked.connect(self._clear_user_cache)
        toolbar1.addWidget(self.clear_cache_btn)
        
        toolbar1.addStretch()
        
        self.cache_info_label = QLabel("缓存: 0文件")
        toolbar1.addWidget(self.cache_info_label)
        
        layout.addLayout(toolbar1)
        
        # 第二行工具栏 - 事件类型筛选
        toolbar_filter = QHBoxLayout()
        
        toolbar_filter.addWidget(QLabel("事件类型筛选:"))
        
        # 创建复选框用于筛选事件类型
        self.filter_alarm = QCheckBox("🔥 火警")
        self.filter_alarm.setChecked(True)
        self.filter_alarm.setStyleSheet("color: #dc3545; font-weight: bold;")
        toolbar_filter.addWidget(self.filter_alarm)
        
        self.filter_fault = QCheckBox("⚠️ 故障")
        self.filter_fault.setChecked(True)
        self.filter_fault.setStyleSheet("color: #fd7e14;")
        toolbar_filter.addWidget(self.filter_fault)
        
        self.filter_feedback = QCheckBox("📢 反馈")
        self.filter_feedback.setChecked(True)
        self.filter_feedback.setStyleSheet("color: #0d6efd;")
        toolbar_filter.addWidget(self.filter_feedback)
        
        self.filter_reset = QCheckBox("🔄 复位")
        self.filter_reset.setChecked(True)
        self.filter_reset.setStyleSheet("color: #6c757d;")
        toolbar_filter.addWidget(self.filter_reset)
        
        self.filter_heartbeat = QCheckBox("💓 心跳")
        self.filter_heartbeat.setChecked(False)  # 默认不显示心跳
        self.filter_heartbeat.setStyleSheet("color: #28a745;")
        toolbar_filter.addWidget(self.filter_heartbeat)
        
        # 全选/取消全选按钮
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.select_all_btn.clicked.connect(self._select_all_filters)
        toolbar_filter.addWidget(self.select_all_btn)
        
        self.clear_all_btn = QPushButton("清空")
        self.clear_all_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.clear_all_btn.clicked.connect(self._clear_all_filters)
        toolbar_filter.addWidget(self.clear_all_btn)
        
        toolbar_filter.addStretch()
        
        # 应用筛选按钮
        self.apply_filter_btn = QPushButton("🔍 应用筛选")
        self.apply_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.apply_filter_btn.clicked.connect(self._apply_history_filter)
        toolbar_filter.addWidget(self.apply_filter_btn)
        
        layout.addLayout(toolbar_filter)
        
        # 第三行工具栏 - 服务器查询
        toolbar2 = QHBoxLayout()
        
        toolbar2.addWidget(QLabel("从服务器查询:"))
        
        toolbar2.addWidget(QLabel("开始日期:"))
        self.server_query_start = QDateEdit()
        self.server_query_start.setCalendarPopup(True)
        self.server_query_start.setDisplayFormat("yyyy-MM-dd")
        self.server_query_start.setDate(QDate.currentDate().addDays(-6))  # 默认6天前，这样加7天正好是今天
        self.server_query_start.dateChanged.connect(self._on_start_date_changed)
        toolbar2.addWidget(self.server_query_start)
        
        toolbar2.addWidget(QLabel("结束日期:"))
        self.server_query_end = QDateEdit()
        self.server_query_end.setCalendarPopup(True)
        self.server_query_end.setDisplayFormat("yyyy-MM-dd")
        self.server_query_end.setDate(QDate.currentDate())
        self.server_query_end.dateChanged.connect(self._on_end_date_changed)
        toolbar2.addWidget(self.server_query_end)
        
        self.server_query_btn = QPushButton("🌐 从服务器查询")
        self.server_query_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 5px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.server_query_btn.clicked.connect(self._query_from_server)
        toolbar2.addWidget(self.server_query_btn)
        
        toolbar2.addStretch()
        
        layout.addLayout(toolbar2)
        
        # 说明标签
        info_label = QLabel(
            "📌 <b>从服务器查询说明：</b><br>"
            "• 单次查询最多选择 <b>7天</b> 范围（为保护服务器性能）<br>"
            "• 查询的数据会自动保存到本地缓存，<br>"
            "  之后可通过「本地查询」快速查看，无需再次联网<br>"
            "• 如需查询更早的历史记录，可<b>分多次查询</b>，每次选7天"
        )
        info_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 13px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border-left: 4px solid #17a2b8;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "设备", "数据内容", "状态"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        # 禁止编辑
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置列宽
        self.history_table.setColumnWidth(0, 200)  # 时间 - 更宽（20字符宽度）
        self.history_table.setColumnWidth(1, 80)   # 设备
        self.history_table.setColumnWidth(2, 400)  # 数据内容 - 更宽
        self.history_table.setColumnWidth(3, 60)   # 状态
        
        layout.addWidget(self.history_table)
        
        return page
    
    def _create_export_page(self) -> QWidget:
        """创建数据导出页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        settings_group = QGroupBox("导出设置（从本地缓存导出，不请求服务器）")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("选择设备:"), 0, 0)
        self.export_device = QComboBox()
        settings_layout.addWidget(self.export_device, 0, 1)
        
        settings_layout.addWidget(QLabel("开始日期:"), 1, 0)
        self.export_start_date = QDateEdit()
        self.export_start_date.setCalendarPopup(True)
        self.export_start_date.setDisplayFormat("yyyy-MM-dd")
        self.export_start_date.setDate(QDate.currentDate().addDays(-7))
        settings_layout.addWidget(self.export_start_date, 1, 1)
        
        settings_layout.addWidget(QLabel("结束日期:"), 2, 0)
        self.export_end_date = QDateEdit()
        self.export_end_date.setCalendarPopup(True)
        self.export_end_date.setDisplayFormat("yyyy-MM-dd")
        self.export_end_date.setDate(QDate.currentDate())
        settings_layout.addWidget(self.export_end_date, 2, 1)
        
        settings_layout.addWidget(QLabel("导出位置:"), 3, 0)
        export_path_layout = QHBoxLayout()
        self.export_path = QLineEdit()
        self.export_path.setText(str(Path.home() / "Desktop"))
        export_path_layout.addWidget(self.export_path)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_export_path)
        export_path_layout.addWidget(self.browse_btn)
        settings_layout.addLayout(export_path_layout, 3, 1)
        
        layout.addWidget(settings_group)
        
        info = QLabel("""
        <p style='color: #666; margin: 10px;'>
        💡 <b>导出说明：</b><br>
        • 数据从<b>本地缓存</b>中导出（需要先从服务器查询数据并保存到缓存）<br>
        • 选择时间范围后点击导出，会导出该时间段内的历史数据<br>
        • 导出格式：Excel (.xlsx)<br>
        • 导出字段：序号、设备编号、记录时间、原始数据
        </p>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()
        
        self.export_btn = QPushButton("📥 开始导出")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 15px;
                font-size: 14px;
            }
        """)
        self.export_btn.clicked.connect(self._export_data)
        layout.addWidget(self.export_btn)
        
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        layout.addWidget(self.export_progress)
        
        return page
    
    def _create_user_page(self) -> QWidget:
        """创建用户管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题区域
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_icon = QLabel("👤")
        title_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(title_icon)
        
        title_label = QLabel("用户管理")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1e3a5f;
        """)
        title_layout.addWidget(title_label)
        
        subtitle = QLabel("仅超级管理员可见")
        subtitle.setStyleSheet("font-size: 12px; color: #999; margin-left: 10px;")
        title_layout.addWidget(subtitle)
        
        title_layout.addStretch()
        layout.addWidget(title_widget)
        
        # 用户表格
        self.user_list = QTableWidget()
        self.user_list.setColumnCount(4)
        self.user_list.setHorizontalHeaderLabels(["用户名", "密码", "权限", "操作"])
        
        # 表格样式
        self.user_list.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                background-color: white;
                gridline-color: #f0f0f0;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e6f2ff;
                color: #1e3a5f;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #475569;
                font-size: 13px;
            }
            QTableWidget {
                alternate-background-color: #fafbfc;
            }
        """)
        
        # 设置列宽
        header = self.user_list.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.user_list.setColumnWidth(0, 120)
        self.user_list.setColumnWidth(2, 150)
        self.user_list.setColumnWidth(3, 200)
        
        # 设置行高
        self.user_list.verticalHeader().setVisible(False)
        self.user_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.user_list.verticalHeader().setDefaultSectionSize(48)
        
        # 启用交替行颜色
        self.user_list.setAlternatingRowColors(True)
        self.user_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.user_list)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e2e8f0;")
        line.setMaximumHeight(1)
        layout.addWidget(line)
        
        # 添加用户区域
        add_widget = QWidget()
        add_layout = QHBoxLayout(add_widget)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.setSpacing(10)
        
        add_label = QLabel("➕ 新增用户：")
        add_label.setStyleSheet("font-size: 14px; color: #475569; font-weight: bold;")
        add_layout.addWidget(add_label)
        
        self.new_user_input = QLineEdit()
        self.new_user_input.setPlaceholderText("输入用户名")
        self.new_user_input.setMinimumWidth(150)
        self.new_user_input.setMaximumHeight(36)
        self.new_user_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        add_layout.addWidget(self.new_user_input)
        
        pwd_label_text = QLabel("密码：")
        pwd_label_text.setStyleSheet("font-size: 14px; color: #475569;")
        add_layout.addWidget(pwd_label_text)
        
        self.new_pwd_input = QLineEdit()
        self.new_pwd_input.setPlaceholderText("输入密码")
        self.new_pwd_input.setMinimumWidth(150)
        self.new_pwd_input.setMaximumHeight(36)
        self.new_pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pwd_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        add_layout.addWidget(self.new_pwd_input)
        
        self.add_user_btn = QPushButton("添加用户")
        self.add_user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_user_btn.setMinimumSize(100, 36)
        self.add_user_btn.clicked.connect(self._add_user)
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        add_layout.addWidget(self.add_user_btn)
        
        add_layout.addStretch()
        layout.addWidget(add_widget)
        return page
    
    def _create_device_page(self) -> QWidget:
        """创建设备分配页面 - 超级管理员查看所有设备的分配情况"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        label = QLabel("🔧 设备分配管理（仅超级管理员可见）")
        label.setStyleSheet("font-size: 16px; color: #666;")
        layout.addWidget(label)
        
        # 说明标签
        info_label = QLabel("💡 提示：表格显示所有设备及其分配情况，勾选设备后选择用户进行分配")
        info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_label)
        
        # 用户选择区域
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("选择要分配的用户:"))
        self.assign_user = QComboBox()
        self.assign_user.setMinimumWidth(150)
        self.assign_user.currentTextChanged.connect(self._on_assign_user_changed)
        user_layout.addWidget(self.assign_user)
        
        self.refresh_assign_btn = QPushButton("🔄 刷新")
        self.refresh_assign_btn.clicked.connect(self._refresh_assignment_page)
        user_layout.addWidget(self.refresh_assign_btn)
        
        user_layout.addStretch()
        
        # 统计标签
        self.assign_stats_label = QLabel("设备总数: 0 | 已分配: 0 | 未分配: 0")
        user_layout.addWidget(self.assign_stats_label)
        
        layout.addLayout(user_layout)
        
        # 设备表格（替代原来的列表）
        self.device_assign_table = QTableWidget()
        self.device_assign_table.setColumnCount(4)
        self.device_assign_table.setHorizontalHeaderLabels(["选择", "设备编号", "设备名称", "已分配用户"])
        
        # 设置表格属性
        self.device_assign_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.device_assign_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.device_assign_table.setAlternatingRowColors(True)  # 交替行颜色
        
        # 设置列宽策略 - 使用更灵活的列宽设置
        header = self.device_assign_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 选择列固定宽度
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # 设备编号固定宽度
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 设备名称自动拉伸
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 已分配用户自动拉伸
        
        # 设置固定列宽
        self.device_assign_table.setColumnWidth(0, 60)   # 选择
        self.device_assign_table.setColumnWidth(1, 120)  # 设备编号
        
        # 设置表格最小高度，确保内容可见
        self.device_assign_table.setMinimumHeight(300)
        
        layout.addWidget(self.device_assign_table)
        print(f"[设备分配页面] 表格初始化完成，列数: {self.device_assign_table.columnCount()}")
        
        # 保存按钮
        self.save_assign_btn = QPushButton("💾 保存分配")
        self.save_assign_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.save_assign_btn.clicked.connect(self._save_device_assignment)
        layout.addWidget(self.save_assign_btn)
        
        # 存储所有设备的分配信息 {hid: [user1, user2, ...]}
        self._device_assignment_map = {}
        
        return page
    
    def _setup_tray(self):
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.fire_icon)
        
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
    
    def _switch_page(self, index: int):
        """切换页面"""
        self.content_stack.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        
        # 如果是设备分配页面且是超级管理员，自动刷新数据
        if index == 5 and self.is_admin:  # 设备分配页面索引为5
            QTimer.singleShot(500, self._refresh_assignment_page)
    
    def login(self, username: str, password: str):
        """执行登录"""
        self.current_user = username
        self.current_password = password
        self._is_logging_out = False  # ✅ 重置退出登录标志位
        self.cache_manager = CacheManager(username)
        
        self.user_label.setText(f"用户: {username}")
        
        # 创建网络线程时传递用户名和密码（使用长连接端口）
        self.network_thread = NetworkThread(SERVER_IP, PC_LONG_PORT, username, password, self)  # ✅ 传入main_window引用
        self.network_thread.connecting.connect(self._on_connecting)
        self.network_thread.connected.connect(self._on_connected)
        self.network_thread.disconnected.connect(self._on_disconnected)
        self.network_thread.login_success.connect(self._on_login_success)
        self.network_thread.login_failed.connect(self._on_login_failed)
        self.network_thread.data_received.connect(self._on_data_received)
        self.network_thread.error_occurred.connect(self._on_network_error)
        self.network_thread.kicked_out.connect(self._on_kicked_out)  # 异地登录被踢出
        self.network_thread.start()
        
        # 启动网络健康检查定时器（每30秒检查一次）
        self._health_check_timer = QTimer(self)
        self._health_check_timer.timeout.connect(self._check_network_health)
        self._health_check_timer.start(30000)  # 30秒
        
        # 启动设备列表自动刷新定时器（每60秒刷新一次）
        self._device_refresh_timer = QTimer(self)
        self._device_refresh_timer.timeout.connect(self._refresh_device_list)
        self._device_refresh_timer.start(60000)  # 60秒
        
        # 启动设备在线状态检查定时器（每30秒检查一次）
        self._online_status_timer = QTimer(self)
        self._online_status_timer.timeout.connect(self._check_device_online_status)
        self._online_status_timer.start(30000)  # 30秒
    
    def _check_network_health(self):
        """检查网络线程健康状态"""
        if self.network_thread:
            # 检查线程是否还在运行
            if not self.network_thread.isRunning():
                print("[网络健康] ⚠️ 网络线程异常，正在重启...")
                self.status_label.setText("网络线程异常，正在重启...")
                # 重新创建并启动网络线程
                self.network_thread = NetworkThread(SERVER_IP, PC_LONG_PORT, self.current_user, self.current_password, self)  # ✅ 传入main_window引用
                self.network_thread.connecting.connect(self._on_connecting)
                self.network_thread.connected.connect(self._on_connected)
                self.network_thread.disconnected.connect(self._on_disconnected)
                self.network_thread.login_success.connect(self._on_login_success)
                self.network_thread.login_failed.connect(self._on_login_failed)
                self.network_thread.data_received.connect(self._on_data_received)
                self.network_thread.error_occurred.connect(self._on_network_error)
                self.network_thread.kicked_out.connect(self._on_kicked_out)
                self.network_thread.start()
    

    def _on_connecting(self):
        """TCP连接已建立，正在登录中"""
        self.server_label.setText("服务器: 连接中...")
        self.server_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        
        # ✅ 不在这里隐藏断网提示，等登录成功后再关闭
    
    def _on_connected(self):
        """连接成功（登录完成）"""
        self.server_label.setText("服务器: 已连接")
        self.server_label.setStyleSheet("color: #28a745;")
        
        # ✅ 连接成功，确保断网提示已关闭
        self._hide_disconnect_overlay()
        
        # ✅ 连接成功，自动关闭错误弹窗（如果存在）
        if hasattr(self, '_error_dialog') and self._error_dialog:
            try:
                self._error_dialog.close()
                self._error_dialog = None
                print("[网络连接] ✓ 已自动关闭连接异常弹窗")
            except:
                pass
    
    def _on_disconnected(self):
        """连接断开"""
        self.server_label.setText("服务器: 已断开")
        self.server_label.setStyleSheet("color: #dc3545;")
        
        # ✅ 如果是主动退出登录，不显示断网提示
        if self._is_logging_out:
            print("[网络连接] 主动退出登录，跳过断网提示显示")
            return
        
        # ✅ 显示断网提示弹窗
        self._show_disconnect_overlay()
    
    def _show_disconnect_overlay(self):
        """显示断网提示弹窗（窗口内居中，与报警弹窗同大小）"""
        # 如果已经显示了，不重复创建
        if hasattr(self, '_disconnect_dialog') and self._disconnect_dialog:
            return
        
        print("[断网提示] 显示断网提示弹窗")
        
        # 创建对话框（和报警弹窗一样大小：520x400）
        self._disconnect_dialog = QDialog(self)
        self._disconnect_dialog.setWindowTitle("⚠️ 网络连接中断")
        self._disconnect_dialog.setFixedSize(520, 420)
        
        if config.get('alarm.popup.stay_on_top', True):
            self._disconnect_dialog.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Window |
                Qt.WindowType.WindowCloseButtonHint
            )
        
        self._disconnect_dialog.setStyleSheet("""
            QDialog {
                background-color: #fff5f5;
                border: 3px solid #dc3545;
                border-radius: 10px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self._disconnect_dialog)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)
        
        # 🔌 断网图标（大号）
        icon_label = QLabel("🔌")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 64px;
            background: transparent;
            padding: 10px;
        """)
        layout.addWidget(icon_label)
        
        # ⚠️ 警告标题
        title_label = QLabel("网络连接中断")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #dc3545;
            background: transparent;
            padding: 8px;
        """)
        layout.addWidget(title_label)
        
        # 📝 描述信息
        desc_label = QLabel("与服务器连接已断开")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("""
            font-size: 16px;
            color: #495057;
            background: transparent;
            padding: 5px;
        """)
        layout.addWidget(desc_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #dc3545; max-height: 2px;")
        layout.addWidget(line)
        
        # 💡 动态提示信息
        self._reconnect_hint_label = QLabel("正在尝试重新连接...")
        self._reconnect_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._reconnect_hint_label.setStyleSheet("""
            font-size: 14px;
            color: #856404;
            background-color: #fff3cd;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #ffc107;
        """)
        layout.addWidget(self._reconnect_hint_label)
        
        # 启动定时器动态更新状态
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.timeout.connect(self._update_reconnect_status)
        self._reconnect_timer.start(1000)  # 每秒更新一次
        
        # ✅ 允许用户手动关闭弹窗
        self._disconnect_dialog.finished.connect(self._on_disconnect_dialog_closed)
        
        # 居中显示
        self._disconnect_dialog.show()
        center_point = self.geometry().center()
        self._disconnect_dialog.move(
            center_point.x() - self._disconnect_dialog.width() // 2,
            center_point.y() - self._disconnect_dialog.height() // 2
        )
    
    def _on_disconnect_dialog_closed(self):
        """断网对话框被用户手动关闭"""
        print("[断网提示] 用户手动关闭了断网提示")
        
        # 停止定时器
        if hasattr(self, '_reconnect_timer') and self._reconnect_timer:
            self._reconnect_timer.stop()
            self._reconnect_timer = None
        
        # 清空引用，允许下次断网时再次显示
        self._disconnect_dialog = None
    
    def _hide_disconnect_overlay(self):
        """隐藏断网提示弹窗"""
        if not hasattr(self, '_disconnect_dialog') or not self._disconnect_dialog:
            return
        
        print("[断网提示] 隐藏断网提示")
        
        # 停止定时器
        if hasattr(self, '_reconnect_timer') and self._reconnect_timer:
            self._reconnect_timer.stop()
            self._reconnect_timer = None
        
        # 关闭并销毁对话框
        try:
            self._disconnect_dialog.close()
            self._disconnect_dialog = None
        except:
            pass
    
    def _update_reconnect_status(self):
        """更新重连状态提示"""
        if not hasattr(self, '_reconnect_hint_label') or not self._reconnect_hint_label:
            return
        
        import time
        current_time = time.strftime("%H:%M:%S")
        
        hints = [
            f"🔄 正在尝试重新连接... ({current_time})",
            f"⏳ 请检查网络连接... ({current_time})",
            f"🔍 等待服务器响应... ({current_time})",
            f"♻️ 自动重连中... ({current_time})"
        ]
        
        import random
        hint = random.choice(hints)
        self._reconnect_hint_label.setText(hint)
    
    def _on_kicked_out(self, msg: str):
        """异地登录被踢出"""
        print(f"[异地登录] 被踢出: {msg}")
        
        # 停止网络线程
        if self.network_thread:
            self.network_thread.stop()
            self.network_thread = None
        
        # 停止健康检查定时器
        if hasattr(self, '_health_check_timer') and self._health_check_timer:
            self._health_check_timer.stop()
        
        # 显示警告对话框
        QMessageBox.warning(self, "异地登录", f"{msg}\n\n您已被迫下线，请重新登录。")
        
        # 返回登录界面
        self._logout()
    
    def _on_login_success(self, is_admin: bool, user_info: dict):
        """登录成功"""
        print(f"[登录成功] is_admin={is_admin}, user_info={user_info}")
        self.is_admin = is_admin
        
        # ✅ 保存Token（用于后续所有API请求）
        if 'token' in user_info:
            self.auth_token = user_info['token']
            token_expiry = user_info.get('token_expiry', 0)
            from datetime import datetime
            expiry_time = datetime.fromtimestamp(token_expiry) if token_expiry else "未知"
            print(f"[登录成功] 已保存Token: {self.auth_token[:16]}... (过期时间: {expiry_time})")
        else:
            print(f"[登录警告] 服务器未返回Token，将使用兼容模式")
        
        # ✅ 保存服务器时间（用于限制日期选择器，避免本地时间不准）
        if 'server_time' in user_info:
            self.server_time_str = user_info['server_time']
            try:
                from datetime import datetime
                self.server_date = datetime.strptime(self.server_time_str, "%Y-%m-%d %H:%M:%S").date()
                print(f"[登录成功] 服务器时间: {self.server_time_str}, 日期: {self.server_date}")
                
                # ✅ 容错处理：如果服务器时间比本地时间晚超过1天，使用本地时间
                local_date = QDate.currentDate()
                server_qdate = QDate(self.server_date.year, self.server_date.month, self.server_date.day)
                days_diff = local_date.daysTo(server_qdate)
                
                if days_diff < -1:  # 服务器时间比本地时间晚超过1天
                    print(f"[登录警告] 服务器时间({self.server_date})比本地时间({local_date.toString('yyyy-MM-dd')})晚 {-days_diff} 天")
                    print(f"[登录警告] 可能是Docker容器时间未同步，将使用本地时间作为最大日期限制")
                    self.server_date = local_date.toPythonDate() if hasattr(local_date, 'toPythonDate') else datetime.now().date()
                    print(f"[登录成功] 使用本地日期: {self.server_date}")
                
                # 限制所有日期选择器的最大值为服务器日期
                self._limit_all_dates_to_server()
            except Exception as e:
                print(f"[登录警告] 解析服务器时间失败: {e}，使用本地时间")
                self.server_date = QDate.currentDate()
        else:
            print("[登录警告] 服务器未返回时间，使用本地时间")
            self.server_date = QDate.currentDate()
        
        if is_admin:
            self.role_label.setText("[超级管理员]")
            for btn in self.admin_menus:
                btn.setVisible(True)
            # admin用户可以访问所有设备
            self.assigned_devices = set()
            
            # admin用户：直接刷新设备列表
            QTimer.singleShot(2000, self._refresh_device_list)
        else:
            self.role_label.setText("[普通用户]")
            # 普通用户：加载设备分配信息，然后刷新设备列表
            def load_and_refresh():
                # 加载设备分配信息
                self._load_user_devices()
                # 延迟刷新设备列表（确保设备分配信息已加载）
                QTimer.singleShot(2000, self._refresh_device_list)
            
            QTimer.singleShot(100, load_and_refresh)
        
        self.status_label.setText(f"登录成功，欢迎 {self.current_user}")
        self._update_cache_info()
        
        # ✅ 登录成功后，从服务器同步设备名称（多端同步）
        QTimer.singleShot(1500, lambda: self._sync_device_names_from_server())
        
        # ✅ 登录成功后，从数据库加载最近1000条实时数据显示到表格
        QTimer.singleShot(500, self._load_recent_realtime_data)
        
        # 如果是超级管理员，延迟刷新用户列表和设备分配用户下拉框
        if is_admin:
            QTimer.singleShot(3000, self._refresh_user_list)
            QTimer.singleShot(4000, self._refresh_assign_user_combo)
        
        # ✅ 登录成功后，延迟3秒自动检查版本更新
        QTimer.singleShot(3000, self._check_for_updates)
    
    def _check_for_updates(self):
        """检查版本更新"""
        try:
            print(f"[版本检测] 开始检查更新，当前版本: {CURRENT_VERSION}")
            
            self.version_check_thread = VersionCheckThread(
                SERVER_IP, PC_SHORT_PORT, 
                parent=self
            )
            self.version_check_thread.check_finished.connect(
                self._on_version_check_result
            )
            self.version_check_thread.error_occurred.connect(
                lambda err: print(f"[版本检测] {err}")
            )
            self.version_check_thread.start()
            
        except Exception as e:
            print(f"[版本检测] 启动失败: {e}")
    
    def _on_version_check_result(self, result):
        """处理版本检测结果 - 弹窗提示用户"""
        try:
            if not result or result.get('code') != 0:
                return
            
            has_update = result.get('has_update', False)
            
            if not has_update:
                print(f"[版本检测] ✓ 已是最新版本: {CURRENT_VERSION}")
                self.status_label.setText(f"✓ 已是最新版本 v{CURRENT_VERSION}")
                return
            
            latest_version = result.get('latest_version', '')
            force_update = result.get('force_update', False)
            changelog = result.get('changelog', [])
            file_size = result.get('file_size', 0)
            
            print(f"[版本检测] 🆕 发现新版本: {CURRENT_VERSION} → {latest_version}")
            
            # 构建更新日志文本
            changelog_text = "\n".join([f"  • {line}" for line in changelog]) if changelog else "  • 性能优化和Bug修复"
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("🆕 发现新版本")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setText(
                f"<h3 style='margin-bottom:10px;'>🆕 发现新版本 <b>v{latest_version}</b></h3>"
                f"<p style='color:#666;margin:5px 0;'>当前版本: <b>{CURRENT_VERSION}</b></p>"
                f"<p style='font-weight:bold;color:#333;margin:10px 0 5px 0;'>✨ 更新内容:</p>"
                f"<pre style='background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px;line-height:1.6;"
                f"border-left:4px solid #28a745;margin:10px 0;'>{changelog_text}</pre>"
                f"<p style='color:#666;margin:10px 0 5px 0;'>📦 更新包大小: <b>{format_size(file_size)}</b></p>"
            )
            msg_box.setStyleSheet("""
                QMessageBox {
                    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                    font-size: 14px;
                }
                QMessageBox QLabel {
                    min-width: 400px;
                    max-width: 500px;
                }
            """)
            
            if force_update:
                # 强制更新：只有"立即更新"按钮
                update_btn = msg_box.addButton("🔄 立即更新", QMessageBox.AcceptRole)
                update_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
            else:
                # 可选更新：提供两个按钮
                update_btn = msg_box.addButton("🔄 立即更新", QMessageBox.AcceptRole)
                update_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
                
                later_btn = msg_box.addButton("⏰ 稍后提醒", QMessageBox.RejectRole)
                later_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #6c757d;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 120px;
                    }
                    QPushButton:hover {
                        background-color: #5a6268;
                    }
                """)
            
            ret = msg_box.exec_()
            
            if ret == QMessageBox.AcceptRole:
                # 用户点击了"立即更新"
                self._start_download_update(latest_version, file_size, result.get('md5', ''))
            elif force_update:
                # 如果是强制更新但用户关闭窗口，退出程序
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().quit()
                
        except Exception as e:
            print(f"[版本检测错误] 处理结果时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_download_update(self, version, expected_size, expected_md5=''):
        """开始下载更新包"""
        try:
            from PyQt5.QtWidgets import QProgressDialog
            
            # 创建进度对话框
            self.progress_dialog = QProgressDialog(
                f"🔄 正在下载更新包 <b>v{version}</b>...\n\n"
                f"⏳ 请耐心等待，下载过程中请勿关闭程序。\n\n"
                f"📦 文件大小: <b>{format_size(expected_size)}</b>",
                "❌ 取消下载",
                0, 100,
                self
            )
            self.progress_dialog.setWindowTitle("🚀 在线升级")
            self.progress_dialog.setMinimumWidth(450)
            self.progress_dialog.setMinimumHeight(150)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.setModal(True)
            self.progress_dialog.setStyleSheet("""
                QProgressDialog {
                    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                    font-size: 14px;
                }
                QProgressBar {
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    text-align: center;
                    background-color: #f0f0f0;
                    height: 25px;
                    font-size: 13px;
                    font-weight: bold;
                    color: white;
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #28a745, stop:1 #20c997);
                    border-radius: 6px;
                }
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 6px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.progress_dialog.show()
            
            # 保存路径（保存在程序目录下）
            save_path = os.path.join(
                os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd(),
                f'update_v{version}.zip'
            )
            
            print(f"[在线升级] 准备下载到: {save_path}")
            
            # 启动下载线程
            self.download_thread = UpdateDownloadThread(
                url=f"http://{SERVER_IP}:{PC_SHORT_PORT}/download",
                save_path=save_path,
                expected_md5=expected_md5,
                parent=self
            )
            
            self.download_thread.progress_updated.connect(
                lambda p: self.progress_dialog.setValue(p)
            )
            self.download_thread.download_finished.connect(
                lambda path: self._on_download_complete(path, version)
            )
            self.download_thread.download_error.connect(
                lambda err: self._on_download_error(err)
            )
            self.download_thread.start()
            
        except Exception as e:
            print(f"[在线升级错误] 启动下载失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "下载失败",
                f"无法启动下载：\n\n{str(e)}\n\n请检查网络连接后重试。",
                QMessageBox.Ok
            )
    
    def _on_download_complete(self, file_path, version):
        """下载完成回调"""
        try:
            self.progress_dialog.close()
            
            from PyQt5.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self,
                "✅ 下载完成",
                f"<h3 style='color:#28a745;margin-bottom:15px;'>🎉 更新包下载成功！</h3>"
                f"<p><b>版本:</b> v{version}</p>"
                f"<p><b>位置:</b> {file_path}</p>"
                f"<p style='color:#666;margin-top:15px;'>安装过程中程序会自动关闭并重启，</p>"
                f"<p style='color:#666;'>是否立即安装？</p>",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            reply.setStyleSheet("""
                QMessageBox {
                    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                    font-size: 14px;
                }
                QPushButton {
                    padding: 8px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 13px;
                    min-width: 100px;
                }
            """)
            
            if reply == QMessageBox.Yes:
                install_update(file_path, main_window=self)
            else:
                QMessageBox.information(
                    self,
                    "💡 提示",
                    f"<p>更新包已保存至：</p>"
                    f"<p style='background:#f5f5f5;padding:10px;border-radius:5px;"
                    f"font-family:Consolas,monospace;'>{file_path}</p>"
                    f"<p style='margin-top:10px;color:#666;'>您可以稍后手动运行此文件进行更新。</p>",
                    QMessageBox.Ok
                )
                
        except Exception as e:
            print(f"[在线升级错误] 下载完成处理失败: {e}")
    
    def _on_download_error(self, error_msg):
        """下载错误回调"""
        try:
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "❌ 下载失败",
                f"<h3 style='color:#dc3545;margin-bottom:15px;'>❌ 更新包下载失败</h3>"
                f"<p style='background:#fff3cd;padding:12px;border-radius:6px;"
                f"border-left:4px solid #ffc107;margin:15px 0;'>{error_msg}</p>"
                f"<p style='color:#666;'>可能的原因：</p>"
                f"<ul style='color:#666;margin-left:20px;'>"
                f"<li>网络连接不稳定</li>"
                f"<li>服务器暂时不可用</li>"
                f"<li>防火墙阻止了下载</li>"
                f"</ul>"
                f"<p style='margin-top:15px;'>请检查网络连接后重试。</p>",
                QMessageBox.Ok
            )
            
        except Exception as e:
            print(f"[在线升级错误] 显示错误信息失败: {e}")

    def _limit_all_dates_to_server(self):
        """限制所有日期选择器的最大值为服务器日期"""
        if not hasattr(self, 'server_date'):
            return
        
        server_qdate = QDate(self.server_date.year, self.server_date.month, self.server_date.day)
        print(f"[日期限制] 服务器日期: {server_qdate.toString('yyyy-MM-dd')}，开始限制所有日期选择器")
        
        # 1️⃣ 本地查询 - 开始/结束日期
        if hasattr(self, 'history_start_date') and self.history_start_date:
            self.history_start_date.setMaximumDate(server_qdate)
            if self.history_start_date.date() > server_qdate or self.history_start_date.date() > QDate.currentDate():
                self.history_start_date.setDate(min(server_qdate, QDate.currentDate()))
        
        if hasattr(self, 'history_end_date') and self.history_end_date:
            self.history_end_date.setMaximumDate(server_qdate)
            # ✅ 确保结束日期默认为服务器日期（可以查今天）
            self.history_end_date.setDate(server_qdate)
            print(f"[日期限制] 本地查询结束日期设置为: {server_qdate.toString('yyyy-MM-dd')}")
        
        # 2️⃣ 服务器查询 - 开始/结束日期
        if hasattr(self, 'server_query_start') and self.server_query_start:
            self.server_query_start.setMaximumDate(server_qdate)
            if self.server_query_start.date() > server_qdate or self.server_query_start.date() > QDate.currentDate():
                self.server_query_start.setDate(min(server_qdate, QDate.currentDate()))
                # 触发联动更新结束日期
                self._on_start_date_changed(self.server_query_start.date())
        
        if hasattr(self, 'server_query_end') and self.server_query_end:
            self.server_query_end.setMaximumDate(server_qdate)
            # ✅ 确保结束日期默认为服务器日期（可以查今天）
            self.server_query_end.setDate(server_qdate)
            print(f"[日期限制] 服务器查询结束日期设置为: {server_qdate.toString('yyyy-MM-dd')}")
        
        # 3️⃣ 数据导出 - 开始/结束日期
        if hasattr(self, 'export_start_date') and self.export_start_date:
            self.export_start_date.setMaximumDate(server_qdate)
            if self.export_start_date.date() > server_qdate:
                self.export_start_date.setDate(server_qdate)
        
        if hasattr(self, 'export_end_date') and self.export_end_date:
            self.export_end_date.setMaximumDate(server_qdate)
            # ✅ 确保导出结束日期默认为服务器日期
            self.export_end_date.setDate(server_qdate)
        
        print(f"[日期限制] ✓ 所有日期选择器已限制最大值为: {server_qdate.toString('yyyy-MM-dd')}（包含今天）")
    
    def _sync_device_names_from_server(self):
        """从服务器同步设备名称（登录后自动调用）"""
        print("[设备名称] 开始从服务器同步设备名称...")
        
        try:
            success = self.device_name_manager.load_from_server(self)
            
            if success:
                # 刷新设备列表中的设备名称显示
                self._update_device_list_with_names()
                # 刷新实时数据表格中的设备名称显示
                self._update_realtime_table_with_device_names()
                
                count = len(self.device_name_manager.device_names)
                if count > 0:
                    self.status_label.setText(f"✓ 已同步 {count} 个设备名称")
                    print(f"[设备名称] ✓ 同步完成，共 {count} 个设备名称")
                else:
                    print("[设备名称] 服务器无设备名称数据（首次使用正常）")
            else:
                print("[设备名称] 同步失败，使用本地数据")
                
        except Exception as e:
            print(f"[设备名称] 同步异常: {e}，使用本地数据")
    
    def _update_device_list_with_names(self):
        """刷新设备列表中的设备名称显示"""
        try:
            for row in range(self.device_list_table.rowCount()):
                # 获取该行的hid
                hid_item = self.device_list_table.item(row, 0)
                if not hid_item:
                    continue
                
                hid = hid_item.text()
                
                # 更新名称列（第2列，索引1）
                name_item = self.device_list_table.item(row, 1)
                if name_item:
                    custom_name = self.device_name_manager.get_device_name(hid)
                    name_item.setText(custom_name)
                    
                    if custom_name:
                        name_item.setBackground(QColor(255, 255, 200))
                    else:
                        name_item.setBackground(QColor(255, 255, 255))
            
            # ✅ 自动调整名称列宽度以适应新名称
            self.device_list_table.resizeColumnToContents(1)
                        
            print("[设备名称] ✓ 设备列表名称已更新")
        except Exception as e:
            print(f"[设备名称] 更新设备列表失败: {e}")
    
    def _load_recent_realtime_data(self):
        """从实时数据数据库加载最近1000条数据显示到表格"""
        try:
            if not db_manager or not hasattr(db_manager, 'db_logs'):
                print("[实时数据] 数据库管理器未初始化，跳过加载")
                return
            
            cursor = db_manager.db_logs.cursor()
            
            # ✅ 从专门的 realtime_data 表查询最近1000条记录（按时间倒序）
            cursor.execute('''
                SELECT receive_time, hid, raw_data, server_type, is_heartbeat 
                FROM realtime_data 
                ORDER BY id DESC 
                LIMIT 1000
            ''')
            rows = cursor.fetchall()
            
            if not rows:
                print("[实时数据] 实时数据表中无历史记录")
                return
            
            print(f"[实时数据] 从实时数据表加载了 {len(rows)} 条历史记录")
            
            # 倒序排列，让最新的数据在最上面（与实时接收顺序一致）
            rows_reversed = list(reversed(rows))
            
            # 清空当前表格（避免重复）
            current_row_count = self.realtime_table.rowCount()
            if current_row_count > 0:
                self.realtime_table.setRowCount(0)
                self.realtime_stats = {'total': 0, 'heartbeat': 0, 'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
            
            # 批量添加数据到表格
            for row_idx, (receive_time, hid, raw_data, server_type, is_heartbeat) in enumerate(rows_reversed):
                # 判断是否为心跳包
                is_heartbeat_bool = bool(is_heartbeat)
                
                # 如果是普通用户且设备未分配，跳过
                if not self.is_admin and hid and hid not in self.assigned_devices:
                    continue
                
                # ✅ 检查是否显示心跳数据（与实时接收保持一致）
                if is_heartbeat_bool and not self.show_heartbeat.isChecked():
                    continue
                
                # 调用添加行的方法（复用现有逻辑，传入完整时间）
                self._add_realtime_row_to_table(raw_data, hid, is_heartbeat_bool, server_type or "", row_idx, receive_time)
            
            # 更新统计显示
            self._update_stats()
            
            # 滚动到顶部显示最新数据
            self.realtime_table.scrollToTop()
            
            print(f"[实时数据] 成功恢复 {self.realtime_table.rowCount()} 条数据到表格")
            
        except Exception as e:
            print(f"[实时数据] 加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_user_devices(self):
        """加载用户分配的设备列表（使用独立短连接）"""
        if not self.current_user:
            return
            
        print(f"[设备分配] 加载用户 {self.current_user} 的设备列表")
        
        # 使用独立短连接获取设备分配信息，避免阻塞主线程
        import socket
        import json
        
        def load_devices_async():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                
                # 连接到服务器（短连接使用PC_SHORT_PORT）
                sock.connect((SERVER_IP, PC_SHORT_PORT))
                
                # 发送设备分配信息请求
                request_data = {
                    "action": "get_user_devices", 
                    "username": self.current_user,
                    "user": self.current_user,
                    "pwd": self.current_password
                }
                request = json.dumps(request_data)
                sock.send(request.encode('utf-8'))
                
                # 接收响应
                response_data = b""
                while True:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    response_data += chunk
                    # 检查是否收到完整JSON响应
                    if b"}" in response_data:
                        break
                
                sock.close()
                
                # 解析响应
                response = json.loads(response_data.decode('utf-8'))
                if response.get("code") == 0:
                    user_devices = response.get("devices", [])
                    self.assigned_devices = set(user_devices)
                    print(f"[设备分配] 用户 {self.current_user} 分配的设备: {user_devices}")
                else:
                    print(f"[设备分配] 获取设备列表失败: {response.get('msg', '未知错误')}")
                    self.assigned_devices = set()
                    
            except Exception as e:
                print(f"[设备分配错误] {e}")
                self.assigned_devices = set()
        
        # 在后台线程中执行网络请求
        import threading
        thread = threading.Thread(target=load_devices_async)
        thread.daemon = True
        thread.start()
    
    def _on_login_failed(self, reason: str):
        """登录失败"""
        QMessageBox.critical(self, "登录失败", reason)
        self._logout()
    
    def _on_network_error(self, error: str):
        """网络错误"""
        self.status_label.setText(f"网络错误: {error}")
        QMessageBox.critical(self, "网络错误", error)
    
    def _on_data_received(self, data: str):
        """接收到数据"""
        print(f"[数据接收] 原始数据: {data[:100]}...")  # ✅ 调试日志
        try:
            if self.pause_btn.isChecked():
                print("[数据接收] ⏸️ 暂停状态，跳过处理")
                return
            
            # 从服务器数据中提取类型信息 [时间] [类型] 描述 | {原始数据}
            server_type = "未知"
            if " [" in data and "] " in data:
                try:
                    # 提取 [类型] 部分
                    type_start = data.index(" [") + 2
                    type_end = data.index("] ", type_start)
                    server_type = data[type_start:type_end]
                except:
                    pass
            
            # 处理服务器发送的日志格式数据 [时间] [类型] 描述 | {原始数据}
            raw_data = data
            if " | {" in data:
                parts = data.split(" | ", 1)
                if len(parts) == 2:
                    raw_data = parts[1]
            
            is_heartbeat = "DT=0" in raw_data and "FDS_S" not in raw_data and "FSS" not in raw_data
            
            # 心跳包不再过滤，只记录统计
            if is_heartbeat:
                self.realtime_stats['heartbeat'] += 1
                self._update_stats()
            
            hid = self._extract_hid(raw_data)
            
            # 如果是普通用户，检查设备是否被分配
            if not self.is_admin and hid:
                # 使用本地缓存的设备分配信息
                if hid not in self.assigned_devices:
                    print(f"[数据过滤] 非管理员且设备未分配，跳过")
                    return
            
            if hid:
                self.devices.add(hid)
                self.device_online_status[hid] = datetime.now()  # 更新最后通信时间
                self._update_device_lists()
                self._update_device_online_status(hid, online=True)  # 立即更新在线状态显示
            
            self._add_realtime_row(raw_data, hid, is_heartbeat, server_type)
            self._check_and_handle_alarm(raw_data, server_type)
            
            # ✅ 接收总数不包含心跳
            if not is_heartbeat:
                self.realtime_stats['total'] += 1
            self._update_stats()
            
            # 如果不在实时数据页面，显示提示卡片
            if self.content_stack.currentIndex() != 0 and not is_heartbeat:
                self._show_new_data_notification(server_type, hid)
            
        except Exception as e:
            print(f"[数据接收错误] {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_hid(self, data: str) -> Optional[str]:
        """提取设备编号"""
        try:
            if "HID=" in data:
                start = data.index("HID=") + 4
                end = data.find(",", start)
                if end == -1:
                    end = data.find("}", start)
                if end == -1:
                    end = len(data)
                return data[start:end].strip()
        except:
            pass
        return None
    
    def _parse_data_content(self, data: str) -> tuple:
        """解析数据内容，返回(类型, 关键信息, 状态)"""
        try:
            # 提取FDS_S状态
            if "FDS_S=" in data:
                fds_s = ""
                start = data.index("FDS_S=") + 6
                end = data.find(",", start)
                if end == -1:
                    end = data.find("}", start)
                if end != -1:
                    fds_s = data[start:end].strip()
                
                status_map = {
                    '0': ('正常', '正常'),
                    '1': ('火警', '报警'),
                    '2': ('故障', '故障'),
                    '3': ('屏蔽', '屏蔽'),
                    '4': ('反馈', '反馈')
                }
                
                # 提取关键信息
                info_parts = []
                
                # 设备类型
                if "FDS_T=" in data:
                    start = data.index("FDS_T=") + 6
                    end = data.find(",", start)
                    if end == -1:
                        end = data.find("}", start)
                    if end != -1:
                        info_parts.append(data[start:end].strip())
                
                # 位置
                if "FDS_P=" in data:
                    start = data.index("FDS_P=") + 6
                    end = data.find(",", start)
                    if end == -1:
                        end = data.find("}", start)
                    if end != -1:
                        info_parts.append(data[start:end].strip())
                
                type_name, status = status_map.get(fds_s, ('未知', '未知'))
                return type_name, " | ".join(info_parts) if info_parts else "", status
            
            # 系统状态 FSS
            elif "FSS=" in data:
                start = data.index("FSS=") + 4
                end = data.find(",", start)
                if end == -1:
                    end = data.find("}", start)
                if end != -1:
                    fss = data[start:end].strip()
                    if '复位' in fss:
                        return '系统', fss, '复位'
                    elif '故障' in fss:
                        return '系统', fss, '故障'
                    else:
                        return '系统', fss, '正常'
            
            # 传输装置状态
            elif "TDP_M=" in data or "TDP_B=" in data:
                parts = []
                if "TDP_M=" in data:
                    start = data.index("TDP_M=") + 6
                    end = data.find(",", start)
                    if end == -1:
                        end = data.find("}", start)
                    if end != -1:
                        parts.append(f"主电:{data[start:end].strip()}")
                if "TDP_B=" in data:
                    start = data.index("TDP_B=") + 6
                    end = data.find(",", start)
                    if end == -1:
                        end = data.find("}", start)
                    if end != -1:
                        parts.append(f"备电:{data[start:end].strip()}")
                return '状态', " | ".join(parts), '正常'
            
        except:
            pass
        
        return '数据', data[:50], '正常'
    
    def _add_realtime_row(self, data: str, hid: Optional[str], is_heartbeat: bool, server_type: str = ""):
        """添加实时数据行，同时保存到缓存"""
        # 解析数据内容，优先使用服务器传来的类型
        type_name, info, status = self._parse_data_content(data)
        
        # 如果服务器传了类型，使用服务器的类型（更可靠）
        if server_type:
            # 映射服务器类型到显示类型
            type_map = {
                '报警': '火警',
                '故障': '故障',
                '反馈': '反馈',
                '正常': '正常',
                '复位': '复位',
                '心跳': '心跳'
            }
            type_name = type_map.get(server_type, type_name)
            status = server_type  # 状态也使用服务器类型
            print(f"[_add_realtime_row] 使用服务器类型: {server_type} -> 显示: {type_name}, 状态: {status}")
        
        # 获取当前时间
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")
        full_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # ✅ 保存到实时数据数据库（用于登录后恢复显示）
        if db_manager and hasattr(db_manager, 'db_logs'):
            try:
                cursor = db_manager.db_logs.cursor()
                cursor.execute('INSERT INTO realtime_data (receive_time, hid, raw_data, server_type, is_heartbeat) VALUES (?, ?, ?, ?, ?)', 
                    (full_time, hid, data[:2000], server_type, 1 if is_heartbeat else 0))
                db_manager.db_logs.commit()
                # 保持最近1000条记录，删除更旧的（避免数据库无限增长）
                cursor.execute('DELETE FROM realtime_data WHERE id NOT IN (SELECT id FROM realtime_data ORDER BY id DESC LIMIT 1000)')
                db_manager.db_logs.commit()
            except Exception as e:
                print(f"[实时数据] 保存到数据库失败: {e}")
        
        # 保存到缓存（非心跳数据）
        if hid and not is_heartbeat and hasattr(self, 'cache_manager') and self.cache_manager:
            try:
                # 检查是否已存在相同数据（避免重复）
                cache_data = self.cache_manager.get_cache(hid, current_date)
                if cache_data:
                    existing_data = cache_data.get('data', [])
                    # 检查是否已存在相同时间和数据
                    exists = any(
                        d.get('time') == full_time and d.get('raw') == data
                        for d in existing_data
                    )
                    if not exists:
                        # 添加到缓存
                        new_item = {
                            'time': full_time,
                            'date': current_date,
                            'raw': data
                        }
                        existing_data.append(new_item)
                        self.cache_manager.save_cache(hid, current_date, existing_data)
                        print(f"[实时数据] 已保存到缓存: {hid} {full_time}")
                else:
                    # 创建新缓存
                    new_item = {
                        'time': full_time,
                        'date': current_date,
                        'raw': data
                    }
                    self.cache_manager.save_cache(hid, current_date, [new_item])
                    print(f"[实时数据] 已创建新缓存: {hid} {full_time}")
            except Exception as e:
                print(f"[实时数据] 保存缓存失败: {e}")
        
        # ✅ 检查是否显示心跳数据
        if is_heartbeat and not self.show_heartbeat.isChecked():
            # 心跳包但用户选择不显示，跳过UI显示（已保存到数据库）
            return
        
        # 添加到实时表格 - 插入到顶部（第0行）
        self.realtime_table.insertRow(0)
        
        # 时间（包含年月日）- 不换行
        time_item = QTableWidgetItem(full_time)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中显示
        self.realtime_table.setItem(0, 0, time_item)
        
        # 设备（显示设备名称，如果有的话）
        display_name = self.device_name_manager.get_display_name(hid) if hid else "Unknown"
        self.realtime_table.setItem(0, 1, QTableWidgetItem(display_name))
        
        # ✅ 自动调整设备列宽度以适应新名称
        self.realtime_table.resizeColumnToContents(1)
        
        # 显示关键信息
        display_text = f"[{type_name}] {info}" if info else f"[{type_name}]"
        data_item = QTableWidgetItem(display_text)
        data_item.setToolTip(data)  # 完整数据作为提示
        self.realtime_table.setItem(0, 2, data_item)
        
        # ✅ 数据内容列自动换行，支持多行显示
        self.realtime_table.setWordWrap(True)
        
        # 状态
        self.realtime_table.setItem(0, 3, QTableWidgetItem(status))
        
        # ✅ 自动调整行高以适应多行内容
        self.realtime_table.resizeRowToContents(0)
        
        # 根据状态设置颜色并统计
        if status in ['火警', '报警']:
            for col in range(4):
                item = self.realtime_table.item(0, col)
                if item:
                    item.setBackground(QColor(255, 200, 200))
            self.realtime_stats['alarm'] = self.realtime_stats.get('alarm', 0) + 1
        elif status == '故障':
            for col in range(4):
                item = self.realtime_table.item(0, col)
                if item:
                    item.setBackground(QColor(255, 230, 200))
            self.realtime_stats['fault'] = self.realtime_stats.get('fault', 0) + 1
        elif status == '反馈':
            for col in range(4):
                item = self.realtime_table.item(0, col)
                if item:
                    item.setBackground(QColor(200, 220, 255))
            self.realtime_stats['feedback'] = self.realtime_stats.get('feedback', 0) + 1
        elif status == '复位':
            self.realtime_stats['reset'] = self.realtime_stats.get('reset', 0) + 1
        
        # 限制最多1000条，删除最旧的（底部）
        while self.realtime_table.rowCount() > 1000:
            self.realtime_table.removeRow(self.realtime_table.rowCount() - 1)
        
        # 收到新数据自动滚动到顶部，显示最新数据
        self.realtime_table.scrollToTop()
    
    def _add_realtime_row_to_table(self, data: str, hid: Optional[str], is_heartbeat: bool, server_type: str = "", row_index: int = 0, receive_time: str = ""):
        """添加实时数据行到表格（仅用于从数据库恢复数据，不保存缓存）"""
        # 解析数据内容，优先使用服务器传来的类型
        type_name, info, status = self._parse_data_content(data)
        
        # 如果服务器传了类型，使用服务器的类型（更可靠）
        if server_type:
            type_map = {
                '报警': '火警',
                '故障': '故障',
                '反馈': '反馈',
                '正常': '正常',
                '复位': '复位',
                '心跳': '心跳'
            }
            type_name = type_map.get(server_type, type_name)
            status = server_type
        
        # 使用传入的时间（从数据库读取的完整时间）
        display_time = receive_time if receive_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 添加到表格 - 使用指定的行索引
        self.realtime_table.insertRow(row_index)
        
        # 时间（包含年月日）- 不换行，居中显示
        time_item = QTableWidgetItem(display_time)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中显示
        self.realtime_table.setItem(row_index, 0, time_item)
        
        # 设备（显示设备名称）
        display_name = self.device_name_manager.get_display_name(hid) if hid else "Unknown"
        self.realtime_table.setItem(row_index, 1, QTableWidgetItem(display_name))
        
        # ✅ 自动调整设备列宽度
        self.realtime_table.resizeColumnToContents(1)
        
        # 显示关键信息
        display_text = f"[{type_name}] {info}" if info else f"[{type_name}]"
        data_item = QTableWidgetItem(display_text)
        data_item.setToolTip(data)
        self.realtime_table.setItem(row_index, 2, data_item)
        
        # ✅ 数据内容列自动换行，支持多行显示
        self.realtime_table.setWordWrap(True)
        
        # 状态
        self.realtime_table.setItem(row_index, 3, QTableWidgetItem(status))
        
        # ✅ 自动调整行高以适应多行内容
        self.realtime_table.resizeRowToContents(row_index)
        
        # 根据状态设置颜色并统计
        if status in ['火警', '报警']:
            for col in range(4):
                item = self.realtime_table.item(row_index, col)
                if item:
                    item.setBackground(QColor(255, 200, 200))
            self.realtime_stats['alarm'] = self.realtime_stats.get('alarm', 0) + 1
        elif status == '故障':
            for col in range(4):
                item = self.realtime_table.item(row_index, col)
                if item:
                    item.setBackground(QColor(255, 230, 200))
            self.realtime_stats['fault'] = self.realtime_stats.get('fault', 0) + 1
        elif status == '反馈':
            for col in range(4):
                item = self.realtime_table.item(row_index, col)
                if item:
                    item.setBackground(QColor(200, 220, 255))
            self.realtime_stats['feedback'] = self.realtime_stats.get('feedback', 0) + 1
        elif status == '复位':
            self.realtime_stats['reset'] = self.realtime_stats.get('reset', 0) + 1
        
        # 更新总统计和心跳统计（接收总数不包含心跳）
        if not is_heartbeat:
            self.realtime_stats['total'] = self.realtime_stats.get('total', 0) + 1
        if is_heartbeat:
            self.realtime_stats['heartbeat'] = self.realtime_stats.get('heartbeat', 0) + 1
    
    def _show_new_data_notification(self, data_type: str, hid: str):
        """显示新数据提示卡片（左下角）- 单卡片显示多条数据，最多10条"""
        # 初始化通知数据列表（如果不存在）
        if not hasattr(self, '_notification_data'):
            self._notification_data = []
        
        # 添加新数据到列表
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self._notification_data.insert(0, {
            'time': current_time,
            'type': data_type,
            'hid': hid
        })
        
        # 最多保留4条
        if len(self._notification_data) > 4:
            self._notification_data = self._notification_data[:4]
        
        # 如果已有通知卡片，更新内容
        if hasattr(self, '_notification_card') and self._notification_card:
            self._update_notification_card()
            return
        
        # 创建新的通知卡片
        self._notification_card = QFrame(self)
        self._notification_card.setFixedSize(320, 120)
        self._notification_card.setStyleSheet("""
            QFrame {
                background-color: #343a40;
                border-radius: 8px;
                border: 2px solid #495057;
            }
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self._notification_card)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(5)
        
        # 标题栏布局
        header_layout = QHBoxLayout()
        
        # 标题
        self._notification_title = QLabel("📡 收到新数据")
        self._notification_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffc107;")
        header_layout.addWidget(self._notification_title)
        
        header_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("关闭")
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # 数据列表标签
        self._notification_list = QLabel()
        self._notification_list.setStyleSheet("font-size: 11px;")
        self._notification_list.setWordWrap(True)
        main_layout.addWidget(self._notification_list)
        
        # 定位到左下角（紧贴左边）
        self._notification_card.move(0, self.height() - 140)
        self._notification_card.show()
        self._notification_card.raise_()
        
        # 更新内容
        self._update_notification_card()
        
        # 关闭按钮事件
        def close_notification():
            self._notification_card.deleteLater()
            self._notification_card = None
            self._notification_data = []
            print("[通知] 用户关闭卡片")
        
        close_btn.clicked.connect(close_notification)
        
        # 点击卡片跳转到实时数据页面
        def on_card_clicked(event):
            # 防止重复触发
            if not hasattr(self, '_notification_card') or not self._notification_card:
                return
            # 先关闭通知
            close_notification()
            # 再切换页面（使用正确的方法名）
            self._switch_page(0)
        
        self._notification_card.mousePressEvent = on_card_clicked
        
        print(f"[通知] 显示新数据提示: {data_type} - {hid}, 当前共 {len(self._notification_data)} 条")
    
    def _update_notification_card(self):
        """更新通知卡片内容"""
        if not hasattr(self, '_notification_card') or not self._notification_card:
            return
        
        # 更新标题显示为"最近10条数据"
        count = len(self._notification_data)
        self._notification_title.setText(f"📡 最近{count}条数据")
        
        # 构建数据列表文本 - 显示所有数据（最多10条）
        lines = []
        for item in self._notification_data:  # 显示所有保留的数据
            type_emoji = {
                '火警': '🔥',
                '报警': '🔥',
                '故障': '⚠️',
                '反馈': '📢',
                '复位': '🔄',
                '正常': '✅'
            }.get(item['type'], '📡')
            lines.append(f"{item['time']} {type_emoji} [{item['type']}] {item['hid']}")
        
        self._notification_list.setText('\n'.join(lines))
        
        # 调整高度 - 根据实际数据条数调整
        new_height = min(80 + count * 20, 300)
        self._notification_card.setFixedHeight(new_height)
    
    def _check_and_handle_alarm(self, data: str, server_type: str = ""):
        """检查并处理报警
        
        Args:
            data: 原始数据
            server_type: 服务器传来的类型（更可靠）
        """
        # 检查报警总开关
        if not config.get('alarm.enabled', True):
            return
            
        alarms = self.alarm_manager.check_alarm(data, server_type)
        
        # 检查弹窗是否已显示
        popup_visible = AlarmPopup._instance is not None
        if popup_visible:
            try:
                popup_visible = AlarmPopup._instance.isVisible()
            except RuntimeError:
                popup_visible = False
        
        # 如果弹窗未显示，重置统计（开始新的累计周期）
        if not popup_visible:
            self._popup_alarm_stats = {'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
        
        # 跟踪是否有新报警需要显示弹窗
        has_new_alarm = False
        last_alarm = None
        
        for alarm in alarms:
            alarm_type = alarm.get('type', '')
            
            # 累计到弹窗统计中
            if alarm_type in self._popup_alarm_stats:
                self._popup_alarm_stats[alarm_type] += 1
            
            # 只有当用户勾选了启用时，才播放声音和显示弹窗
            type_config = config.get(f'alarm.types.{alarm_type}', {})
            
            if type_config.get('enabled', True):
                if alarm['popup']:
                    has_new_alarm = True
                    last_alarm = alarm
            
            self._update_alarm_button()
        
        # 使用单例模式显示报警弹窗
        # 如果弹窗已存在，会更新内容；如果不存在，会创建新弹窗
        if has_new_alarm and last_alarm:
            # 定义弹窗关闭回调 - 重置统计
            def on_popup_close():
                self._popup_alarm_stats = {'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
            
            try:
                AlarmPopup.show_alarm(last_alarm, self._popup_alarm_stats, self, on_popup_close, self.device_name_manager)
            except Exception as e:
                print(f"[报警弹窗] 显示失败: {e}")
    
    def _update_alarm_button(self):
        """更新报警按钮"""
        count = self.alarm_manager.get_alarm_count()
        self.alarm_btn.setText(f"🔔 今日报警数: {count}")
        self.alarm_btn.setVisible(count > 0)
    
    def _update_stats(self):
        """更新统计信息"""
        self.stats_label.setText(
            f"接收: {self.realtime_stats['total']}条 | "
            f"心跳: {self.realtime_stats['heartbeat']}条 | "
            f"🔥火警: {self.realtime_stats.get('alarm', 0)}条 | "
            f"⚠️故障: {self.realtime_stats.get('fault', 0)}条 | "
            f"📢反馈: {self.realtime_stats.get('feedback', 0)}条 | "
            f"🔄复位: {self.realtime_stats.get('reset', 0)}条"
        )
    
    def _update_device_lists(self):
        """更新设备列表 - 实时将新设备添加到设备列表表格和下拉框"""
        try:
            devices = sorted(self.devices)
            
            # 获取当前表格中的所有设备ID
            existing_hids = set()
            for row in range(self.device_list_table.rowCount()):
                item = self.device_list_table.item(row, 0)
                if item:
                    existing_hids.add(item.text())
            
            # 找出需要添加的新设备
            new_devices = [d for d in devices if d not in existing_hids]
            
            if new_devices:
                print(f"[_update_device_list] 发现 {len(new_devices)} 个新设备，立即添加: {new_devices}")
                
                # 1️⃣ 在设备列表表格末尾添加新行
                current_row = self.device_list_table.rowCount()
                self.device_list_table.setRowCount(current_row + len(new_devices))
                
                for i, hid in enumerate(new_devices):
                    row = current_row + i
                    
                    # 设备编号列（第0列）
                    self.device_list_table.setItem(row, 0, QTableWidgetItem(hid))
                    
                    # 设备名称列（第1列）- 暂时为空，等服务器刷新时填充
                    self.device_list_table.setItem(row, 1, QTableWidgetItem(""))
                    
                    # 在线状态列（第2列）- 默认在线
                    status_item = QTableWidgetItem("🟢 在线")
                    status_item.setBackground(QColor(200, 255, 200))
                    self.device_list_table.setItem(row, 2, status_item)
                    
                    # 最新数据时间列（第3列）
                    time_item = QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    self.device_list_table.setItem(row, 3, time_item)
                    
                    print(f"[_update_device_list] 已添加设备 {hid} 到表格第 {row} 行")
                
                # 滚动到底部显示新设备
                self.device_list_table.scrollToBottom()
                
                # 2️⃣ 更新历史查询页面的设备下拉框
                for hid in new_devices:
                    if self.history_device.findText(hid) == -1:
                        self.history_device.addItem(hid)
                        print(f"[_update_device_list] 已添加设备 {hid} 到历史查询下拉框")
                
                # 3️⃣ 更新数据导出页面的设备下拉框
                for hid in new_devices:
                    if self.export_device.findText(hid) == -1:
                        self.export_device.addItem(hid)
                        print(f"[_update_device_list] 已添加设备 {hid} 到数据导出下拉框")
            else:
                print(f"[_update_device_list] 无新设备需要添加")
        except Exception as e:
            print(f"[_update_device_list] 更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_cache_info(self):
        """更新缓存信息"""
        if self.cache_manager:
            info = self.cache_manager.get_cache_info()
            self.cache_label.setText(f"缓存: {info['file_count']}文件 {info['total_size_mb']}MB")
            self.cache_info_label.setText(f"缓存: {info['file_count']}文件")
    
    def _toggle_pause(self):
        """暂停/继续"""
        if self.pause_btn.isChecked():
            self.pause_btn.setText("▶️ 继续")
        else:
            self.pause_btn.setText("⏸️ 暂停")
    
    def _toggle_keep_awake(self, state):
        """切换保持唤醒状态"""
        if state == Qt.Checked:
            print("[保持唤醒] 启用 - 防止系统黑屏/息屏/睡眠")
            self._enable_keep_awake()
        else:
            print("[保持唤醒] 禁用 - 恢复系统正常电源管理")
            self._disable_keep_awake()
    
    def _toggle_show_heartbeat(self, state):
        """切换显示心跳状态并保存设置"""
        show = (state == Qt.Checked)
        
        # 保存设置到 QSettings（持久化）
        settings = QSettings("FireMonitor", "FireMonitorClient")
        settings.setValue("show_heartbeat", show)
        
        if show:
            print("[显示心跳] 已启用 - 实时数据表格将显示心跳包数据")
        else:
            print("[显示心跳] 已禁用 - 心跳数据将被过滤，只显示业务数据")
    
    def _enable_keep_awake(self):
        """启用保持唤醒 - 防止系统黑屏、息屏、睡眠"""
        try:
            # Windows: 使用SetThreadExecutionState防止系统睡眠
            import ctypes
            from ctypes import wintypes
            
            # ES_CONTINUOUS = 0x80000000
            # ES_SYSTEM_REQUIRED = 0x00000001
            # ES_DISPLAY_REQUIRED = 0x00000002
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            
            kernel32 = ctypes.windll.kernel32
            result = kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            if result:
                print("[保持唤醒] Windows电源管理已设置 - 防止黑屏/睡眠")
                self._keep_awake_enabled = True
            else:
                print("[保持唤醒] 设置失败")
        except Exception as e:
            print(f"[保持唤醒] 启用失败: {e}")
    
    def _disable_keep_awake(self):
        """禁用保持唤醒 - 恢复系统正常电源管理"""
        try:
            import ctypes
            ES_CONTINUOUS = 0x80000000
            
            kernel32 = ctypes.windll.kernel32
            result = kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            if result:
                print("[保持唤醒] Windows电源管理已恢复")
                self._keep_awake_enabled = False
        except Exception as e:
            print(f"[保持唤醒] 禁用失败: {e}")
    
    def _clear_realtime(self):
        """清空实时数据"""
        self.realtime_table.setRowCount(0)
        self.realtime_stats = {'total': 0, 'heartbeat': 0, 'alarm': 0, 'fault': 0, 'feedback': 0, 'reset': 0}
        self._update_stats()
    
    def _query_history(self):
        """查询历史数据（本地缓存查询，支持任意日期范围）"""
        hid = self.history_device.currentText()
        
        if not hid:
            QMessageBox.warning(self, "提示", "请选择设备")
            return
        
        # 获取日期范围
        start_date = self.history_start_date.date()
        end_date = self.history_end_date.date()
        start_str = start_date.toString("yyyy-MM-dd")
        end_str = end_date.toString("yyyy-MM-dd")
        
        print(f"[历史查询] 查询设备 {hid} 的数据: {start_str} ~ {end_str} (共 {(start_date.daysTo(end_date) + 1)} 天)")
        
        # 收集所有日期的数据
        all_data = []
        dates_with_cache = []
        dates_without_cache = []
        
        # 遍历日期范围
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.toString("yyyy-MM-dd")
            
            if self.cache_manager.has_cache(hid, date_str):
                cache_data = self.cache_manager.get_cache(hid, date_str)
                if cache_data:
                    all_data.extend(cache_data['data'])
                    dates_with_cache.append(date_str)
                    print(f"[历史查询] {date_str}: 从缓存加载 {len(cache_data['data'])} 条")
            else:
                dates_without_cache.append(date_str)
                print(f"[历史查询] {date_str}: 无本地缓存")
            
            current_date = current_date.addDays(1)
        
        # 如果有缓存数据显示
        if all_data:
            self._display_history_data(all_data)
            self.status_label.setText(
                f"✓ 已从缓存加载 {len(all_data)} 条数据 ({len(dates_with_cache)}/{start_date.daysTo(end_date) + 1} 天有缓存)"
            )
            
            # 如果部分日期没有缓存，提示用户是否从服务器补充
            if dates_without_cache and len(dates_without_cache) > 0:
                reply = QMessageBox.question(
                    self, "提示",
                    f"已加载 {len(dates_with_cache)} 天的缓存数据。\n"
                    f"还有 {len(dates_without_cache)} 天 ({', '.join(dates_without_cache)}) 无本地缓存。\n"
                    f"是否从服务器补充这些日期的数据？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.server_query_start.setDate(start_date)
                    self.server_query_end.setDate(end_date)
                    self._query_from_server()
            return
        
        # 完全没有缓存数据，询问是否从服务器查询
        if dates_without_cache:
            reply = QMessageBox.question(
                self, "提示",
                f"日期范围 {start_str} ~ {end_str} 暂无本地缓存数据。\n是否从服务器查询？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.server_query_start.setDate(start_date)
                self.server_query_end.setDate(end_date)
                self._query_from_server()
    
    def _display_history_data(self, data: list):
        """显示历史数据（带筛选）"""
        # 保存原始数据用于筛选
        self._current_history_data = data
        
        # 应用筛选
        filtered_data = self._filter_history_data(data)
        
        self.history_table.setRowCount(len(filtered_data))
        
        for row, item in enumerate(filtered_data):
            # 时间
            self.history_table.setItem(row, 0, QTableWidgetItem(item.get('time', '')))
            
            # 设备编号
            raw_data = item.get('raw', '')
            hid = self._extract_hid(raw_data)
            self.history_table.setItem(row, 1, QTableWidgetItem(hid or "Unknown"))
            
            # 解析数据内容
            type_name, info, status = self._parse_data_content(raw_data)
            display_text = f"[{type_name}] {info}" if info else f"[{type_name}]"
            data_item = QTableWidgetItem(display_text)
            data_item.setToolTip(raw_data)
            self.history_table.setItem(row, 2, data_item)
            
            # 状态
            self.history_table.setItem(row, 3, QTableWidgetItem(status))
            
            # 根据状态设置颜色
            if status in ['火警', '报警']:
                for col in range(4):
                    self.history_table.item(row, col).setBackground(QColor(255, 200, 200))
            elif status == '故障':
                for col in range(4):
                    self.history_table.item(row, col).setBackground(QColor(255, 230, 200))
            elif status == '反馈':
                for col in range(4):
                    self.history_table.item(row, col).setBackground(QColor(200, 220, 255))
    
    def _filter_history_data(self, data: list) -> list:
        """根据筛选条件过滤历史数据"""
        if not data:
            return []
        
        # 获取筛选条件
        show_alarm = self.filter_alarm.isChecked()
        show_fault = self.filter_fault.isChecked()
        show_feedback = self.filter_feedback.isChecked()
        show_reset = self.filter_reset.isChecked()
        show_heartbeat = self.filter_heartbeat.isChecked()
        
        filtered = []
        for item in data:
            raw_data = item.get('raw', '')
            type_name, info, status = self._parse_data_content(raw_data)
            
            # 根据类型决定是否显示
            should_show = False
            if status in ['火警', '报警'] and show_alarm:
                should_show = True
            elif status == '故障' and show_fault:
                should_show = True
            elif status == '反馈' and show_feedback:
                should_show = True
            elif status == '复位' and show_reset:
                should_show = True
            elif status == '心跳' and show_heartbeat:
                should_show = True
            
            if should_show:
                filtered.append(item)
        
        return filtered
    
    def _apply_history_filter(self):
        """应用历史数据筛选"""
        if hasattr(self, '_current_history_data') and self._current_history_data:
            self._display_history_data(self._current_history_data)
            filtered_count = len(self._filter_history_data(self._current_history_data))
            total_count = len(self._current_history_data)
            self.status_label.setText(f"✓ 筛选完成：显示 {filtered_count}/{total_count} 条数据")
        else:
            QMessageBox.information(self, "提示", "请先查询数据")
    
    def _select_all_filters(self):
        """全选所有筛选条件"""
        self.filter_alarm.setChecked(True)
        self.filter_fault.setChecked(True)
        self.filter_feedback.setChecked(True)
        self.filter_reset.setChecked(True)
        self.filter_heartbeat.setChecked(True)
    
    def _clear_all_filters(self):
        """清空所有筛选条件"""
        self.filter_alarm.setChecked(False)
        self.filter_fault.setChecked(False)
        self.filter_feedback.setChecked(False)
        self.filter_reset.setChecked(False)
        self.filter_heartbeat.setChecked(False)
    
    def _refresh_device_list(self):
        """刷新设备列表"""
        self.refresh_devices_btn.setEnabled(False)
        self.refresh_devices_btn.setText("🔄 刷新中...")
        self.status_label.setText("正在获取设备列表...")
        
        # 创建后台线程获取设备列表 - 使用独立短连接，传入main_window以获取Token
        server_ip = config.get('server.ip', SERVER_IP)
        server_port = config.get('connection.short_port', PC_SHORT_PORT)
        self.device_list_thread = DeviceListQueryThread(
            server_ip, server_port, 
            main_window=self  # ✅ 传入main_window引用以获取Token
        )
        self.device_list_thread.query_finished.connect(self._on_device_list_finished)
        self.device_list_thread.query_error.connect(self._on_device_list_error)
        self.device_list_thread.start()
    
    def _on_device_list_finished(self, devices: list):
        """设备列表获取完成"""
        print(f"[设备列表] 获取完成，共 {len(devices)} 个设备")
        
        # ✅ 成功获取数据，重置错误标志（允许下次失败时再次弹窗）
        self._device_error_shown = False
        
        # ✅ 成功后重置重试计数
        if hasattr(self, '_device_list_retry_count'):
            del self._device_list_retry_count
        
        # ✅ 自动关闭之前的错误弹窗（如果存在）
        if hasattr(self, '_error_dialog') and self._error_dialog:
            try:
                self._error_dialog.close()
                self._error_dialog = None
                print("[设备列表] ✓ 已自动关闭连接异常弹窗")
            except:
                pass
        
        try:
            # 如果是普通用户，过滤设备列表，只显示分配的设备
            filtered_devices = devices
            if not self.is_admin:
                # 使用本地缓存的设备分配信息，避免网络请求阻塞
                user_devices = list(self.assigned_devices)
                print(f"[设备列表] 用户 {self.current_user} 分配的设备: {user_devices}")
                
                # 过滤设备列表
                filtered_devices = [d for d in devices if d.get('hid', '') in user_devices]
                print(f"[设备列表] 过滤后设备数量: {len(filtered_devices)}")
            
            self.device_list_table.setRowCount(len(filtered_devices))
            print(f"[设备列表] 设置表格行数: {len(filtered_devices)}")
            
            for row, device in enumerate(filtered_devices):
                print(f"[设备列表] 处理第 {row} 行: {device.get('hid', '')}")
                hid = device.get('hid', '')
                
                # 设备编号
                self.device_list_table.setItem(row, 0, QTableWidgetItem(hid))
                
                # 设备名称（显示名称，不可编辑）
                device_name = self.device_name_manager.get_device_name(hid)
                name_item = QTableWidgetItem(device_name)
                if device_name:
                    name_item.setBackground(QColor(255, 255, 200))  # 有名称的用淡黄色标记
                self.device_list_table.setItem(row, 1, name_item)
                
                # 在线状态
                is_online = device.get('is_online', False)
                status_item = QTableWidgetItem("🟢 在线" if is_online else "⚫ 离线")
                if is_online:
                    status_item.setBackground(QColor(200, 255, 200))
                else:
                    status_item.setBackground(QColor(230, 230, 230))
                self.device_list_table.setItem(row, 2, status_item)
                
                # 最新数据时间
                self.device_list_table.setItem(row, 3, QTableWidgetItem(device.get('latest_time', '无数据')))
                
                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(5, 2, 5, 2)
                
                # 修改名称按钮
                edit_btn = QPushButton("✏️ 修改名称")
                edit_btn.setProperty("hid", hid)
                edit_btn.setProperty("row", row)
                edit_btn.clicked.connect(self._edit_device_name)
                btn_layout.addWidget(edit_btn)
                
                view_btn = QPushButton("📈 查看历史")
                view_btn.setProperty("hid", hid)
                view_btn.clicked.connect(self._view_device_history)
                btn_layout.addWidget(view_btn)
                
                # ✅ 管理员专属：删除设备按钮
                if self.is_admin:
                    delete_device_btn = QPushButton("🗑️ 删除设备")
                    delete_device_btn.setProperty("hid", hid)
                    delete_device_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #dc3545;
                            color: white;
                            padding: 5px 10px;
                            font-size: 12px;
                            border-radius: 4px;
                            border: 1px solid #bd2130;
                        }
                        QPushButton:hover {
                            background-color: #c82333;
                        }
                    """)
                    delete_device_btn.clicked.connect(self._delete_device_with_password)
                    btn_layout.addWidget(delete_device_btn)
                    
                    # ✅ 管理员专属：删除数据按钮
                    delete_data_btn = QPushButton("📋 删除数据")
                    delete_data_btn.setProperty("hid", hid)
                    delete_data_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #fd7e14;
                            color: white;
                            padding: 5px 10px;
                            font-size: 12px;
                            border-radius: 4px;
                            border: 1px solid #d96400;
                        }
                        QPushButton:hover {
                            background-color: #e8690c;
                        }
                    """)
                    delete_data_btn.clicked.connect(self._delete_device_data_with_password)
                    btn_layout.addWidget(delete_data_btn)
                
                self.device_list_table.setCellWidget(row, 4, btn_widget)
            
            print(f"[设备列表] 更新UI标签")
            self.device_count_label.setText(f"设备数量: {len(devices)}")
            self.status_label.setText(f"✓ 已获取 {len(devices)} 个设备")
            
            # 恢复按钮
            self.refresh_devices_btn.setEnabled(True)
            self.refresh_devices_btn.setText("🔄 刷新设备列表")
            
            # 同时更新历史查询页面的设备下拉框
            print(f"[设备列表] 更新历史查询下拉框")
            self._update_history_device_combo(devices)
            print(f"[设备列表] 处理完成")
        except Exception as e:
            print(f"[设备列表错误] {e}")
            import traceback
            traceback.print_exc()
    
    def _update_device_online_status(self, hid: str, online: bool = True):
        """实时更新设备在线状态（收到数据时立即调用）"""
        try:
            table = self.device_list_table
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item and item.text() == hid:
                    status_item = QTableWidgetItem("🟢 在线" if online else "⚫ 离线")
                    if online:
                        status_item.setBackground(QColor(200, 255, 200))
                    else:
                        status_item.setBackground(QColor(230, 230, 230))
                    table.setItem(row, 2, status_item)
                    
                    time_item = QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    table.setItem(row, 3, time_item)
                    
                    print(f"[设备状态] 实时更新 {hid}: {'在线' if online else '离线'}")
                    return
        except Exception as e:
            print(f"[设备状态] 更新失败: {e}")
    
    def _check_device_online_status(self):
        """定期检查设备在线状态（超时自动标记为离线）"""
        try:
            timeout_seconds = 120  # 120秒无数据则标记为离线
            now = datetime.now()
            
            for hid, last_time in list(self.device_online_status.items()):
                time_diff = (now - last_time).total_seconds()
                if time_diff > timeout_seconds:
                    self._update_device_online_status(hid, online=False)
                    del self.device_online_status[hid]
        except Exception as e:
            print(f"[设备在线] 检查失败: {e}")
    
    def _update_history_device_combo(self, devices: list):
        """更新历史查询页面和数据导出页面的设备下拉框"""
        print(f"[设备列表] _update_history_device_combo 开始")
        try:
            # 如果是普通用户，过滤设备列表，只显示分配的设备
            filtered_devices = devices
            if not self.is_admin:
                # 使用本地缓存的设备分配信息，避免网络请求阻塞
                user_devices = list(self.assigned_devices)
                print(f"[设备列表] 用户 {self.current_user} 分配的设备: {user_devices}")
                
                # 过滤设备列表
                filtered_devices = [d for d in devices if d.get('hid', '') in user_devices]
                print(f"[设备列表] 过滤后设备数量: {len(filtered_devices)}")
            
            # 更新历史查询页面下拉框
            current_text_history = self.history_device.currentText()
            print(f"[设备列表] 历史查询当前选择: {current_text_history}")
            self.history_device.clear()
            print(f"[设备列表] 清空历史查询下拉框")
            # 超级管理员显示所有设备，普通用户显示分配的设备
            display_devices = devices if self.is_admin else filtered_devices
            print(f"[设备列表] 显示设备数量: {len(display_devices)} (超级管理员: {self.is_admin})")
            for device in display_devices:
                hid = device.get('hid', '')
                self.history_device.addItem(hid)
                print(f"[设备列表] 添加设备到历史查询: {hid}")
            # 恢复之前的选择
            if current_text_history:
                index = self.history_device.findText(current_text_history)
                if index >= 0:
                    self.history_device.setCurrentIndex(index)
                    print(f"[设备列表] 恢复历史查询选择: {current_text_history}")
            
            # 更新数据导出页面下拉框
            current_text_export = self.export_device.currentText()
            print(f"[设备列表] 数据导出当前选择: {current_text_export}")
            self.export_device.clear()
            print(f"[设备列表] 清空数据导出下拉框")
            # 超级管理员显示所有设备，普通用户显示分配的设备
            for device in display_devices:
                hid = device.get('hid', '')
                self.export_device.addItem(hid)
                print(f"[设备列表] 添加设备到数据导出: {hid}")
            # 恢复之前的选择
            if current_text_export:
                index = self.export_device.findText(current_text_export)
                if index >= 0:
                    self.export_device.setCurrentIndex(index)
                    print(f"[设备列表] 恢复数据导出选择: {current_text_export}")
            
            print(f"[设备列表] _update_history_device_combo 完成")
        except Exception as e:
            print(f"[设备列表] _update_history_device_combo 错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_device_list_error(self, error_msg: str):
        """设备列表获取失败"""
        # ✅ 先转换错误信息（确保变量始终可用）
        friendly_msg = self._translate_error_message(error_msg)
        
        # ✅ Token相关错误 - 不显示弹窗，自动延迟重试（限制最多3次）
        if "token" in error_msg.lower() or "认证" in error_msg.lower():
            if not hasattr(self, '_device_list_retry_count'):
                self._device_list_retry_count = 0
            
            self._device_list_retry_count += 1
            
            if self._device_list_retry_count <= 3:
                print(f"[设备列表] ⚠️ Token未就绪 (第{self._device_list_retry_count}次)，2秒后自动重试...")
                self.status_label.setText(f"⏳ 正在准备认证信息... ({self._device_list_retry_count}/3)")
                QTimer.singleShot(2000, self._refresh_device_list)
            else:
                print(f"[设备列表] ❌ 重试{self._device_list_retry_count}次仍失败，停止重试")
                self.status_label.setText("⚠️ 设备列表加载失败")
                self.refresh_devices_btn.setEnabled(True)
                self.refresh_devices_btn.setText("🔄 刷新设备列表")
            return
        
        # ✅ 成功后重置重试计数
        if hasattr(self, '_device_list_retry_count'):
            del self._device_list_retry_count
        
        # ✅ 防止重复弹窗：只在首次失败时显示弹窗
        if not self._device_error_shown:
            self._device_error_shown = True
            
            # ✅ 创建并保存弹窗引用（用于后续自动关闭）
            self._error_dialog = QMessageBox(self)
            self._error_dialog.setWindowTitle("⚠️ 网络连接异常")
            self._error_dialog.setIcon(QMessageBox.Icon.Warning)
            self._error_dialog.setText(f"<h3>无法连接到服务器</h3>")
            self._error_dialog.setInformativeText(f"<p style='font-size:13px;'>{friendly_msg}</p><p style='color:#666;font-size:12px;margin-top:10px;'>💡 正在尝试重新连接，连接成功后此窗口将自动关闭...</p>")
            self._error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            self._error_dialog.show()  # 使用 show() 而非 exec()，不阻塞
        
        self.status_label.setText(f"⚠️ 连接异常: {friendly_msg}")
        
        # 恢复按钮
        self.refresh_devices_btn.setEnabled(True)
        self.refresh_devices_btn.setText("🔄 刷新设备列表")
    
    def _translate_error_message(self, error_msg: str) -> str:
        """将技术性错误信息转换为用户友好的中文"""
        error_lower = error_msg.lower()
        
        # ✅ Token相关错误 - 给出友好提示
        if "token" in error_lower or "认证" in error_lower:
            return "认证信息正在准备中，请稍候..."
        
        # 常见网络错误的中文翻译
        if "expecting value" in error_lower or "json" in error_lower:
            return "服务器响应格式异常，可能是网络不稳定或服务器繁忙"
        elif "connection refused" in error_lower:
            return "服务器拒绝连接，请检查服务器是否启动"
        elif "timeout" in error_lower:
            return "连接超时，请检查网络是否正常"
        elif "connection reset" in error_lower or "reset by peer" in error_lower:
            return "连接被重置，可能服务器正在重启"
        elif "no route to host" in error_lower or "unreachable" in error_lower:
            return "无法访问服务器，请检查网络连接"
        elif "timed out" in error_lower:
            return "请求超时，服务器响应较慢"
        elif "format error" in error_lower:
            return "数据格式错误，通信协议不匹配"
        else:
            # 通用友好提示
            return f"网络通信出现问题（{error_msg[:50]}）"
    
    def _edit_device_name(self):
        """修改设备名称"""
        btn = self.sender()
        if btn:
            hid = btn.property("hid")
            row = btn.property("row")
            
            # 获取当前名称
            name_item = self.device_list_table.item(row, 1)
            if not name_item:
                return
            
            current_name = name_item.text()
            
            # 弹出输入对话框
            new_name, ok = QInputDialog.getText(
                self, 
                "修改设备名称", 
                f"请输入设备 {hid} 的新名称:",
                text=current_name
            )
            
            if ok and new_name is not None:
                new_name = new_name.strip()
                # 保存设备名称（本地）
                self.device_name_manager.set_device_name(hid, new_name)
                
                # ✅ 同步到服务器（多端同步）
                QTimer.singleShot(500, lambda: self._sync_device_name_to_server())
                
                # 更新显示
                if new_name:
                    name_item.setText(new_name)
                    name_item.setBackground(QColor(255, 255, 200))
                    self.status_label.setText(f"✓ 设备 {hid} 名称已设置为: {new_name}")
                else:
                    name_item.setText("")
                    name_item.setBackground(QColor(255, 255, 255))
                    self.status_label.setText(f"✓ 设备 {hid} 名称已清除")
                
                # 刷新实时数据表格，显示新的设备名称
                self._update_realtime_table_with_device_names()
    
    def _sync_device_name_to_server(self):
        """上传设备名称到服务器（修改名称后调用）"""
        try:
            print("[设备名称] 开始同步到服务器...")
            success = self.device_name_manager.sync_to_server(self)
            
            if success:
                print("[设备名称] ✓ 已同步到服务器")
            else:
                print("[设备名称] ⚠ 同步失败，下次登录时会自动重试")
                
        except Exception as e:
            print(f"[设备名称] ⚠ 同步异常: {e}")
    
    def _delete_device_with_password(self):
        """删除设备（管理员功能，需要密码确认）"""
        btn = self.sender()
        if not btn:
            return
        
        hid = btn.property("hid")
        if not hid:
            return
        
        # 确认对话框
        reply = QMessageBox.warning(
            self,
            "⚠️ 确认删除设备",
            f"<h3>您确定要删除设备 <b>{hid}</b> 吗？</h3>"
            f"<p style='color: #dc3545; font-size: 14px;'>此操作将：</p>"
            f"<ul>"
            f"<li>从服务器永久删除该设备的所有数据</li>"
            f"<li>删除设备状态记录</li>"
            f"<li>删除设备名称</li>"
            f"<li>删除历史数据和实时数据</li>"
            f"</ul>"
            f"<p style='color: #dc3545;'><b>此操作不可恢复！</b></p>",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            print(f"[删除设备] 用户取消删除: {hid}")
            return
        
        # 密码确认对话框
        password, ok = QInputDialog.getText(
            self,
            "🔐 密码确认",
            f"请输入您的登录密码以确认删除设备 {hid}：",
            QLineEdit.Password
        )
        
        if not ok or not password:
            print(f"[删除设备] 用户取消密码输入: {hid}")
            return
        
        # 执行删除
        self._execute_delete_device(hid, password)
    
    def _delete_device_data_with_password(self):
        """删除设备数据（管理员功能，需要密码确认）"""
        btn = self.sender()
        if not btn:
            return
        
        hid = btn.property("hid")
        if not hid:
            return
        
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📋 删除设备数据 - {hid}")
        dialog.setFixedSize(500, 350)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("<h2>⚠️ 删除设备数据</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel(
            f"将要删除设备 <b>{hid}</b> 的数据。"
            f"\n\n可以选择删除全部数据或指定日期范围的数据。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #495057; font-size: 13px;")
        layout.addWidget(info_label)
        
        # 选项组
        options_group = QGroupBox("删除范围")
        options_layout = QVBoxLayout(options_group)
        
        delete_all_radio = QRadioButton("删除全部数据（从创建至今的所有记录）")
        delete_all_radio.setChecked(True)  # 默认选中
        options_layout.addWidget(delete_all_radio)
        
        date_range_radio = QRadioButton("按日期范围删除：")
        options_layout.addWidget(date_range_radio)
        
        # 日期选择
        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(20, 0, 0, 0)
        
        start_date_edit = QDateEdit()
        start_date_edit.setCalendarPopup(True)
        start_date_edit.setDisplayFormat("yyyy-MM-dd")
        start_date_edit.setDate(QDate.currentDate().addDays(-30))  # 默认30天前
        start_date_edit.setEnabled(False)
        date_layout.addWidget(QLabel("开始日期:"))
        date_layout.addWidget(start_date_edit)
        
        end_date_edit = QDateEdit()
        end_date_edit.setCalendarPopup(True)
        end_date_edit.setDisplayFormat("yyyy-MM-dd")
        end_date_edit.setDate(QDate.currentDate())
        end_date_edit.setEnabled(False)
        date_layout.addWidget(QLabel("结束日期:"))
        date_layout.addWidget(end_date_edit)
        
        options_layout.addWidget(date_widget)
        layout.addWidget(options_group)
        
        # 连接信号：启用/禁用日期选择
        date_range_radio.toggled.connect(lambda checked: start_date_edit.setEnabled(checked))
        date_range_radio.toggled.connect(lambda checked: end_date_edit.setEnabled(checked))
        
        # 密码输入
        pwd_group = QGroupBox("🔐 安全验证")
        pwd_layout = QVBoxLayout(pwd_group)
        pwd_input = QLineEdit()
        pwd_input.setPlaceholderText("请输入您的登录密码")
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(pwd_input)
        layout.addWidget(pwd_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("✓ 确认删除")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 20px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        confirm_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)
        
        # 显示对话框
        result = dialog.exec()
        
        if result != QDialog.DialogCode.Accepted:
            print(f"[删除数据] 用户取消删除: {hid}")
            return
        
        password = pwd_input.text().strip()
        if not password:
            QMessageBox.warning(self, "错误", "请输入密码！")
            return
        
        # 获取删除参数
        if delete_all_radio.isChecked():
            start_date = None
            end_date = None
        else:
            start_date = start_date_edit.date().toString("yyyy-MM-dd") + " 00:00:00"
            end_date = end_date_edit.date().toString("yyyy-MM-dd") + " 23:59:59"
        
        # 执行删除
        self._execute_delete_device_data(hid, password, start_date, end_date)
    
    def _execute_delete_device(self, hid: str, password: str):
        """执行删除设备操作"""
        try:
            self.status_label.setText(f"正在删除设备 {hid}...")
            
            request_data = json.dumps({
                "action": "delete_device",
                "hid": hid,
                "confirm_password": password
            })
            
            response = self.send_request(request_data)
            
            if response and response.get('code') == 0:
                QMessageBox.information(
                    self,
                    "✓ 删除成功",
                    f"<h3>设备删除成功</h3>"
                    f"<p>{response.get('msg', '')}</p>",
                    QMessageBox.StandardButton.Ok
                )
                self.status_label.setText(f"✓ 设备 {hid} 已删除")
                
                # 刷新设备列表
                QTimer.singleShot(1000, self._refresh_device_list)
            else:
                error_msg = response.get('msg', '未知错误')
                QMessageBox.critical(self, "✗ 删除失败", error_msg)
                self.status_label.setText(f"✗ 删除设备失败: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除设备时发生错误：{str(e)}")
            self.status_label.setText(f"✗ 删除设备异常: {e}")
    
    def _execute_delete_device_data(self, hid: str, password: str, start_date=None, end_date=None):
        """执行删除设备数据操作"""
        try:
            self.status_label.setText(f"正在删除设备 {hid} 的数据...")
            
            request_data = {
                "action": "delete_device_data",
                "hid": hid,
                "confirm_password": password
            }
            
            if start_date and end_date:
                request_data["start_date"] = start_date
                request_data["end_date"] = end_date
            
            response = self.send_request(json.dumps(request_data))
            
            if response and response.get('code') == 0:
                QMessageBox.information(
                    self,
                    "✓ 删除成功",
                    f"<h3>数据删除成功</h3>"
                    f"<p>{response.get('msg', '')}</p>",
                    QMessageBox.StandardButton.Ok
                )
                self.status_label.setText(f"✓ 设备 {hid} 数据已删除")
            else:
                error_msg = response.get('msg', '未知错误')
                QMessageBox.critical(self, "✗ 删除失败", error_msg)
                self.status_label.setText(f"✗ 删除数据失败: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除数据时发生错误：{str(e)}")
            self.status_label.setText(f"✗ 删除数据异常: {e}")
    
    def _update_realtime_table_with_device_names(self):
        """刷新实时数据表格中的设备名称显示"""
        for row in range(self.realtime_table.rowCount()):
            item = self.realtime_table.item(row, 1)
            if item:
                # 从显示文本中提取设备编号（格式：名称(编号) 或 编号）
                text = item.text()
                if '(' in text and text.endswith(')'):
                    hid = text[text.rfind('(')+1:-1]
                else:
                    hid = text
                # 更新显示名称
                new_display = self.device_name_manager.get_display_name(hid)
                item.setText(new_display)
        
        # ✅ 自动调整设备列宽度以适应新名称
        self.realtime_table.resizeColumnToContents(1)
    
    def _view_device_history(self):
        """查看设备历史"""
        btn = self.sender()
        if btn:
            hid = btn.property("hid")
            # 切换到历史查询页面
            self._switch_page(2)  # 历史查询页面索引
            # 设置设备
            index = self.history_device.findText(hid)
            if index >= 0:
                self.history_device.setCurrentIndex(index)
            # 自动查询
            self._query_history()
    
    def _on_start_date_changed(self, new_date):
        """开始日期改变时，限制结束日期范围"""
        # 计算最大结束日期（开始后7天）
        max_end_date = new_date.addDays(6)  # 包含起始日共7天
        
        # ✅ 不能超过服务器日期
        if hasattr(self, 'server_date'):
            server_qdate = QDate(self.server_date.year, self.server_date.month, self.server_date.day)
            if max_end_date > server_qdate:
                max_end_date = server_qdate
        
        # 获取当前结束日期
        current_end = self.server_query_end.date()
        
        # 如果当前结束日期超过最大允许日期，则自动调整
        if current_end > max_end_date:
            self.server_query_end.setDate(max_end_date)
        
        # 设置结束日期的最小和最大值
        self.server_query_end.setMinimumDate(new_date)
        self.server_query_end.setMaximumDate(max_end_date)
        
        print(f"[日期选择] 开始日期: {new_date.toString('yyyy-MM-dd')}, 最大结束日期: {max_end_date.toString('yyyy-MM-dd')}")
    
    def _on_end_date_changed(self, new_date):
        """结束日期改变时，确保不超出范围"""
        start_date = self.server_query_start.date()
        max_end_date = start_date.addDays(6)
        
        # ✅ 不能超过服务器日期
        if hasattr(self, 'server_date'):
            server_qdate = QDate(self.server_date.year, self.server_date.month, self.server_date.day)
            if max_end_date > server_qdate:
                max_end_date = server_qdate
            if new_date > server_qdate:
                new_date = server_qdate
        
        # 如果选择的结束日期超过7天范围，自动调整为最大允许值
        if new_date > max_end_date:
            self.server_query_end.setDate(max_end_date)
            QMessageBox.information(
                self, 
                "提示", 
                "<h3>⏱️ 查询范围说明</h3>"
                "<p>为保护服务器性能，<b>单次查询最多选择7天</b>范围。</p>"
                "<p>但这并不意味着服务器只保存7天的数据！</p>"
                "<p><b>如需查询更早的历史记录：</b></p>"
                "<p>• 可分多次查询，每次选7天</p>"
                "<p>• 查询过的数据会保存在本地缓存中</p>"
                "<p>• 之后可通过「本地查询」快速查看所有已缓存数据</p>"
                f"<p style='color: #666; font-size: 12px;'>已自动将结束日期调整为：{max_end_date.toString('yyyy-MM-dd')}</p>"
            )
        elif new_date < start_date:
            self.server_query_end.setDate(start_date)
    
    def _query_from_server(self):
        """从服务器查询历史数据"""
        hid = self.history_device.currentText()
        start_date = self.server_query_start.date()
        end_date = self.server_query_end.date()
        
        if not hid:
            QMessageBox.warning(self, "提示", "请选择设备")
            return
        
        if start_date > end_date:
            QMessageBox.warning(self, "提示", "开始日期不能晚于结束日期")
            return
        
        # 禁用按钮防止重复点击
        self.server_query_btn.setEnabled(False)
        self.server_query_btn.setText("🌐 查询中...")
        self.status_label.setText("正在从服务器查询数据...")
        
        # 创建后台查询线程
        self.query_thread = HistoryQueryThread(
            self.network_thread,
            hid,
            start_date.toString("yyyy-MM-dd"),
            end_date.toString("yyyy-MM-dd"),
            self.current_user,
            self.current_password,
            self.auth_token  # ✅ 传入Token
        )
        self.query_thread.query_finished.connect(self._on_query_finished)
        self.query_thread.query_error.connect(self._on_query_error)
        self.query_thread.query_progress.connect(self._on_query_progress)
        self.query_thread.start()
    
    def _on_query_progress(self, current: int, total: int):
        """查询进度回调"""
        if total > 0:
            percent = int(current * 100 / total)
            self.status_label.setText(f"正在从服务器查询数据... {percent}% ({current}/{total})")
        else:
            self.status_label.setText(f"正在从服务器查询数据... 已接收 {current} 条")
    
    def _on_query_finished(self, hid: str, data: list):
        """查询完成回调"""
        # 保存到缓存 - 使用字典去重，避免重复数据
        date_data_map = {}
        
        # 按日期分组数据
        for item in data:
            date_str = item.get('date', '')
            if date_str:
                if date_str not in date_data_map:
                    date_data_map[date_str] = []
                date_data_map[date_str].append(item)
        
        # 保存到缓存，合并时去重
        for date_str, new_data in date_data_map.items():
            cache_data = self.cache_manager.get_cache(hid, date_str)
            if cache_data:
                existing_data = cache_data.get('data', [])
                # 使用时间和原始数据作为唯一标识去重
                existing_keys = {(d.get('time', ''), d.get('raw', '')) for d in existing_data}
                for item in new_data:
                    key = (item.get('time', ''), item.get('raw', ''))
                    if key not in existing_keys:
                        existing_data.append(item)
                        existing_keys.add(key)
                self.cache_manager.save_cache(hid, date_str, existing_data)
            else:
                self.cache_manager.save_cache(hid, date_str, new_data)
        
        self._display_history_data(data)
        self.status_label.setText(f"✓ 从服务器获取 {len(data)} 条数据，已保存到缓存")
        self._update_cache_info()
        
        # 恢复按钮
        self.server_query_btn.setEnabled(True)
        self.server_query_btn.setText("🌐 从服务器查询")
    
    def _on_query_error(self, error_msg: str):
        """查询错误回调"""
        QMessageBox.warning(self, "查询失败", error_msg)
        self.status_label.setText(f"查询失败: {error_msg}")
        
        # 恢复按钮
        self.server_query_btn.setEnabled(True)
        self.server_query_btn.setText("🌐 从服务器查询")
    
    def _clear_user_cache(self):
        """清空用户缓存"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有本地缓存吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.cache_manager:
                self.cache_manager.clear_cache()
                self._update_cache_info()
                # 清空页面数据
                self.history_table.setRowCount(0)
                self.realtime_table.setRowCount(0)
                self.realtime_stats = {'total': 0, 'heartbeat': 0, 'alarm': 0}
                self._update_stats()
                QMessageBox.information(self, "完成", "缓存已清空")
    
    def _browse_export_path(self):
        """浏览导出路径"""
        path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if path:
            self.export_path.setText(path)
    
    def _export_data(self):
        """导出数据 - 格式化为易读的表格形式（给领导查看）"""
        hid = self.export_device.currentText()
        if not hid:
            QMessageBox.warning(self, "提示", "请选择设备")
            return
        
        start_date = self.export_start_date.date()
        end_date = self.export_end_date.date()
        export_path = self.export_path.text()
        
        all_data = []
        current = start_date
        
        while current <= end_date:
            date_str = current.toString("yyyy-MM-dd")
            if self.cache_manager.has_cache(hid, date_str):
                cache = self.cache_manager.get_cache(hid, date_str)
                if cache:
                    all_data.extend(cache['data'])
            current = current.addDays(1)
        
        if not all_data:
            QMessageBox.warning(self, "提示", "所选日期范围内没有缓存数据")
            return
        
        # 导出为Excel格式（使用CSV，可以用Excel直接打开）
        filename = f"{hid}_{start_date.toString('yyyyMMdd')}_{end_date.toString('yyyyMMdd')}.csv"
        filepath = Path(export_path) / filename
        
        try:
            import csv
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入文件头部注释（推荐使用Excel/WPS打开）
                writer.writerow(['💡 推荐使用 Microsoft Excel 或 WPS 表格 打开此文件以获得最佳显示效果'])
                writer.writerow([''])
                # 写入标题（更清晰的列名）
                writer.writerow(['序号', '记录时间', '设备编号', '事件类型', '部件编号', '部件类型', '安装位置', '事件状态'])
                
                # 写入数据
                for i, item in enumerate(all_data, 1):
                    raw_data = item.get('raw', '')
                    time_str = item.get('time', '')
                    
                    # 解析数据内容
                    parsed = self._parse_export_data(raw_data)
                    
                    # 优化数据显示，确保每条数据清晰易读
                    writer.writerow([
                        i,
                        time_str.replace('[', '').replace(']', ''),  # 去掉时间中的方括号
                        parsed.get('hid', hid),
                        parsed.get('type_name', ''),
                        parsed.get('fds_c', ''),
                        parsed.get('fds_t', ''),
                        parsed.get('fds_p', ''),
                        parsed.get('status', '')
                    ])
            
            QMessageBox.information(self, "导出成功", 
                f"✅ 数据已成功导出！\n\n"
                f"📁 文件位置：\n{filepath}\n\n"
                f"💡 打开方式：\n"
                f"   推荐使用 Microsoft Excel 或 WPS 表格 打开此文件\n"
                f"   以获得最佳的表格显示效果\n\n"
                f"📊 包含字段：\n"
                f"   序号、记录时间、设备编号、事件类型、部件编号、\n"
                f"   部件类型、安装位置、事件状态")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
    
    def _parse_export_data(self, data: str) -> dict:
        """解析导出数据，返回易读的字段（优化给领导查看）"""
        result = {
            'hid': '',
            'type_name': '',
            'fds_c': '',
            'fds_t': '',
            'fds_p': '',
            'status': ''
        }
        
        try:
            # 首先检查是否是复位数据
            if '复位' in data:
                result['type_name'] = '复位'
                result['status'] = '复位完成'
            
            # 提取HID
            if 'HID=' in data:
                start = data.index('HID=') + 4
                end = data.find(',', start)
                if end == -1:
                    end = data.find('}', start)
                if end != -1:
                    result['hid'] = data[start:end].strip()
            
            # 判断数据类型
            if 'FDS_S=' in data:
                # 部件状态
                start = data.index('FDS_S=') + 6
                end = data.find(',', start)
                if end == -1:
                    end = data.find('}', start)
                if end != -1:
                    fds_s = data[start:end].strip()
                    status_map = {
                        '0': ('正常', '正常'),
                        '1': ('火警', '报警'),
                        '2': ('故障', '故障'),
                        '3': ('屏蔽', '屏蔽'),
                        '4': ('反馈', '反馈'),
                    }
                    type_name, status = status_map.get(fds_s, ('未知', f'状态{fds_s}'))
                    result['type_name'] = type_name
                    result['status'] = status
                
                # 提取部件编号
                if 'FDS_C=' in data:
                    start = data.index('FDS_C=') + 6
                    end = data.find(',', start)
                    if end == -1:
                        end = data.find('}', start)
                    if end != -1:
                        result['fds_c'] = data[start:end].strip()
                
                # 提取部件类型
                if 'FDS_T=' in data:
                    start = data.index('FDS_T=') + 6
                    end = data.find(',', start)
                    if end == -1:
                        end = data.find('}', start)
                    if end != -1:
                        result['fds_t'] = data[start:end].strip()
                
                # 提取位置
                if 'FDS_P=' in data:
                    start = data.index('FDS_P=') + 6
                    end = data.find(',', start)
                    if end == -1:
                        end = data.find('}', start)
                    if end != -1:
                        result['fds_p'] = data[start:end].strip()
            
            elif 'FSS=' in data:
                # 系统状态
                start = data.index('FSS=') + 4
                end = data.find(',', start)
                if end == -1:
                    end = data.find('}', start)
                if end != -1:
                    fss = data[start:end].strip()
                    result['type_name'] = '系统'
                    result['fds_t'] = fss
                    if '复位' in fss:
                        result['status'] = '复位'
                    elif '故障' in fss:
                        result['status'] = '故障'
                    else:
                        result['status'] = '正常'
            
            elif 'TDP_M=' in data or 'TDP_B=' in data:
                # 传输装置状态
                result['type_name'] = '状态'
                parts = []
                if 'TDP_M=' in data:
                    start = data.index('TDP_M=') + 6
                    end = data.find(',', start)
                    if end == -1:
                        end = data.find('}', start)
                    if end != -1:
                        parts.append(f"主电:{data[start:end].strip()}")
                if 'TDP_B=' in data:
                    start = data.index('TDP_B=') + 6
                    end = data.find(',', start)
                    if end == -1:
                        end = data.find('}', start)
                    if end != -1:
                        parts.append(f"备电:{data[start:end].strip()}")
                result['fds_t'] = ' | '.join(parts)
                result['status'] = '正常'
        
        except Exception as e:
            print(f"[导出解析错误] {e}")
        
        return result
    
    def _add_user(self):
        """添加用户"""
        username = self.new_user_input.text().strip()
        password = self.new_pwd_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        
        # 发送到服务器创建用户
        if self.network_thread and self.network_thread.socket:
            request = json.dumps({
                "action": "create_user",
                "username": username,
                "password": password,
                "is_admin": False
            })
            response = self.network_thread.send_request(request)
            if response.get("code") == 0:
                QMessageBox.information(self, "成功", f"用户 {username} 已添加")
                self.new_user_input.clear()
                self.new_pwd_input.clear()
                self._refresh_user_list()
            else:
                QMessageBox.warning(self, "失败", response.get("msg", "创建失败"))
        else:
            QMessageBox.warning(self, "错误", "未连接到服务器")
    
    def _refresh_user_list(self):
        """刷新用户列表"""
        # 从服务器获取用户列表
        if self.network_thread and self.network_thread.socket:
            request = json.dumps({"action": "list_users"})
            response = self.network_thread.send_request(request)
            if response.get("code") == 0:
                users = response.get("users", [])
                self.user_list.setRowCount(len(users))
                
                for row, user_info in enumerate(users):
                    username = user_info.get("username", "")
                    password = user_info.get("password", "")
                    is_admin = user_info.get("is_admin", False)
                    
                    # 用户名列（第0列）
                    name_item = QTableWidgetItem(username)
                    name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if username == "admin":
                        name_item.setForeground(QColor(59, 130, 246))  # 蓝色高亮admin
                        name_item.setFont(QFont("", -1, QFont.Weight.Bold))
                    self.user_list.setItem(row, 0, name_item)
                    
                    # 密码列（第1列）：美化显示
                    pwd_container = QWidget()
                    pwd_layout = QHBoxLayout(pwd_container)
                    pwd_layout.setContentsMargins(10, 0, 10, 0)
                    pwd_layout.setSpacing(8)
                    
                    # 密码文本
                    pwd_label = QLabel("••••••")
                    pwd_label.setStyleSheet("""
                        color: #64748b;
                        font-family: 'Segoe UI', 'Microsoft YaHei';
                        font-size: 14px;
                        letter-spacing: 2px;
                        font-weight: bold;
                        padding: 4px 0;
                    """)
                    pwd_layout.addWidget(pwd_label)
                    
                    # 显示/隐藏按钮（使用图标样式）
                    show_btn = QPushButton()
                    show_btn.setText("👁")
                    show_btn.setToolTip("点击显示/隐藏密码")
                    show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    show_btn.setFixedSize(32, 28)
                    show_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f1f5f9;
                            border: 1px solid #e2e8f0;
                            border-radius: 14px;
                            font-size: 14px;
                            padding: 2px;
                            margin: 0;
                        }
                        QPushButton:hover {
                            background-color: #e2e8f0;
                            border-color: #cbd5e1;
                        }
                        QPushButton:pressed {
                            background-color: #cbd5e1;
                        }
                    """)
                    show_btn.clicked.connect(lambda checked, lbl=pwd_label, pw=password: self._toggle_password_visibility(lbl, pw))
                    pwd_layout.addWidget(show_btn)
                    
                    pwd_layout.addStretch()
                    self.user_list.setCellWidget(row, 1, pwd_container)
                    
                    # 权限列（第2列）：使用标签样式
                    perm_widget = QWidget()
                    perm_layout = QHBoxLayout(perm_widget)
                    perm_layout.setContentsMargins(5, 0, 5, 0)
                    
                    if is_admin:
                        badge = QLabel("⭐ 超级管理员")
                        badge.setStyleSheet("""
                            color: #dc2626;
                            background-color: #fef2f2;
                            padding: 6px 12px;
                            border-radius: 12px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 1px solid #fecaca;
                        """)
                    else:
                        badge = QLabel("👤 普通用户")
                        badge.setStyleSheet("""
                            color: #2563eb;
                            background-color: #eff6ff;
                            padding: 6px 12px;
                            border-radius: 12px;
                            font-size: 12px;
                            font-weight: bold;
                            border: 1px solid #bfdbfe;
                        """)
                    
                    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    perm_layout.addWidget(badge)
                    perm_layout.addStretch()
                    self.user_list.setCellWidget(row, 2, perm_widget)
                    
                    # 操作列（第3列）：美化按钮组
                    op_container = QWidget()
                    op_layout = QHBoxLayout(op_container)
                    op_layout.setContentsMargins(5, 0, 5, 0)
                    op_layout.setSpacing(8)
                    
                    # 重置密码按钮
                    reset_btn = QPushButton("🔑 重置密码")
                    reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    reset_btn.setMinimumSize(90, 30)
                    reset_btn.setToolTip(f"重置用户 {username} 的密码")
                    reset_btn.clicked.connect(lambda checked, u=username: self._show_reset_password_dialog(u))
                    reset_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #fef3c7;
                            color: #d97706;
                            border: 1px solid #fde68a;
                            border-radius: 15px;
                            font-size: 11px;
                            font-weight: bold;
                            padding: 4px 12px;
                        }
                        QPushButton:hover {
                            background-color: #fde68a;
                            border-color: #fcd34d;
                        }
                        QPushButton:pressed {
                            background-color: #fcd34d;
                        }
                    """)
                    op_layout.addWidget(reset_btn)
                    
                    # 删除按钮（非admin用户才显示）
                    if username != "admin":
                        delete_btn = QPushButton("🗑 删除")
                        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        delete_btn.setMinimumSize(70, 30)
                        delete_btn.setToolTip(f"删除用户 {username}")
                        delete_btn.clicked.connect(lambda checked, u=username: self._delete_user(u))
                        delete_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #fee2e2;
                                color: #dc2626;
                                border: 1px solid #fecaca;
                                border-radius: 15px;
                                font-size: 11px;
                                font-weight: bold;
                                padding: 4px 12px;
                            }
                            QPushButton:hover {
                                background-color: #fecaca;
                                border-color: #fca5a5;
                            }
                            QPushButton:pressed {
                                background-color: #fca5a5;
                            }
                        """)
                        op_layout.addWidget(delete_btn)
                    
                    op_layout.addStretch()
                    self.user_list.setCellWidget(row, 3, op_container)
                
                # 同时更新设备分配页面的用户下拉框
                self._refresh_assign_user_combo(users)
            else:
                QMessageBox.warning(self, "错误", response.get("msg", "获取用户列表失败"))
    
    def _refresh_assign_user_combo(self, users=None):
        """刷新设备分配页面的用户下拉框"""
        if users is None:
            # 如果没有提供用户列表，从服务器获取
            if self.network_thread and self.network_thread.socket:
                request = json.dumps({"action": "list_users"})
                response = self.network_thread.send_request(request)
                if response.get("code") == 0:
                    users = response.get("users", [])
                else:
                    print("[设备分配] 获取用户列表失败")
                    return
            else:
                print("[设备分配] 网络连接不可用")
                return
        
        # 保存当前选择
        current_text = self.assign_user.currentText()
        
        # 暂时断开用户选择变化事件，避免触发网络请求
        self.assign_user.currentTextChanged.disconnect(self._on_assign_user_changed)
        
        # 清空并重新填充下拉框
        self.assign_user.clear()
        
        user_count = 0
        for user_info in users:
            username = user_info.get("username", "")
            is_admin = user_info.get("is_admin", False)
            if username != "admin":  # 不显示admin用户
                self.assign_user.addItem(username)
                user_count += 1
        
        print(f"[设备分配] 用户列表已更新 ({user_count} 个用户)")
        
        # 恢复之前的选择或选择第一个
        if not self.assign_user.currentText() and self.assign_user.count() > 0:
            self.assign_user.setCurrentIndex(0)
        
        # 重新连接用户选择变化事件
        self.assign_user.currentTextChanged.connect(self._on_assign_user_changed)
        
        # 如果当前有选择用户，手动触发一次设备加载
        current_text = self.assign_user.currentText()
        if current_text:
            self._on_assign_user_changed(current_text)
    
    def _on_assign_user_changed(self, username: str):
        """设备分配页面用户选择变化 - 重新加载数据"""
        if not username:
            return
        
        # 重新加载设备分配数据
        self._refresh_assignment_page()
    
    def _check_user_assigned_devices(self, username: str):
        """根据当前表格数据，勾选指定用户已分配的设备"""
        
        checked_count = 0
        for row in range(self.device_assign_table.rowCount()):
            # 获取已分配用户列的内容
            assigned_item = self.device_assign_table.item(row, 3)
            checkbox_widget = self.device_assign_table.cellWidget(row, 0)
            
            if assigned_item and checkbox_widget:
                assigned_text = assigned_item.text()
                checkbox = checkbox_widget.findChild(QCheckBox)
                
                if checkbox:
                    # 检查该设备是否分配给了当前用户
                    if username in assigned_text:
                        checkbox.setChecked(True)
                        checked_count += 1
                    else:
                        checkbox.setChecked(False)
        
        print(f"[设备分配] 已勾选 {checked_count} 个设备")
        self.status_label.setText(f"已为用户 {username} 勾选 {checked_count} 个已分配设备")
    
    def _delete_user(self, username: str):
        """删除用户"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除用户 {username} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.network_thread and self.network_thread.socket:
                request = json.dumps({
                    "action": "delete_user",
                    "username": username
                })
                response = self.network_thread.send_request(request)
                if response.get("code") == 0:
                    QMessageBox.information(self, "成功", f"用户 {username} 已删除")
                    self._refresh_user_list()
                else:
                    QMessageBox.warning(self, "失败", response.get("msg", "删除失败"))
    
    def _toggle_password_visibility(self, label: QLabel, password: str):
        """切换密码显示/隐藏状态"""
        current_text = label.text()
        if current_text == "••••••":
            # 显示密码
            label.setText(password)
            label.setStyleSheet("""
                color: #1e3a5f;
                font-family: 'Consolas', 'Courier New';
                font-size: 13px;
                letter-spacing: 1px;
                font-weight: bold;
                padding: 4px 0;
                background-color: #f0f9ff;
                border-radius: 4px;
                padding: 6px 10px;
            """)
        else:
            # 隐藏密码
            label.setText("••••••")
            label.setStyleSheet("""
                color: #64748b;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 14px;
                letter-spacing: 2px;
                font-weight: bold;
                padding: 4px 0;
            """)
    
    def _show_reset_password_dialog(self, username: str):
        """显示重置密码对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"🔑 重置密码 - {username}")
        dialog.setFixedSize(420, 280)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #334155;
                font-size: 13px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel(f"为用户 <b style='color: #3b82f6; font-size: 16px;'>{username}</b> 设置新密码")
        title.setStyleSheet("font-size: 14px; padding-bottom: 10px;")
        layout.addWidget(title)
        
        # 新密码输入框
        new_pwd_label = QLabel("新密码：")
        new_pwd_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(new_pwd_label)
        
        pwd_input = QLineEdit()
        pwd_input.setPlaceholderText("请输入新密码（至少4位）")
        pwd_input.setMinimumHeight(40)
        pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f8fafc;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: white;
            }
        """)
        layout.addWidget(pwd_input)
        
        # 确认密码输入框
        confirm_label = QLabel("确认密码：")
        confirm_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(confirm_label)
        
        confirm_input = QLineEdit()
        confirm_input.setPlaceholderText("再次输入新密码")
        confirm_input.setMinimumHeight(40)
        confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f8fafc;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: white;
            }
        """)
        layout.addWidget(confirm_input)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setMinimumSize(100, 38)
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                border-color: #94a3b8;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
        """)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✓ 确认重置")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setMinimumSize(140, 38)
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_pwd = pwd_input.text().strip()
            confirm_pwd = confirm_input.text().strip()
            
            if not new_pwd or not confirm_pwd:
                QMessageBox.warning(self, "⚠️ 提示", "密码不能为空！")
                return
            
            if new_pwd != confirm_pwd:
                QMessageBox.warning(self, "⚠️ 提示", "两次输入的密码不一致！")
                return
            
            if len(new_pwd) < 4:
                QMessageBox.warning(self, "⚠️ 提示", "密码长度至少4位！")
                return
            
            if self.network_thread and self.network_thread.socket:
                request = json.dumps({
                    "action": "reset_password",
                    "username": username,
                    "password": new_pwd
                })
                response = self.network_thread.send_request(request)
                if response.get("code") == 0:
                    QMessageBox.information(
                        self, 
                        "✅ 成功", 
                        f"用户 <b>{username}</b> 的密码已成功重置！",
                        QMessageBox.StandardButton.Ok
                    )
                else:
                    QMessageBox.warning(self, "❌ 失败", response.get("msg", "重置失败"))
    
    def _refresh_assignment_page(self):
        """刷新设备分配页面 - 加载所有设备和分配信息"""
        if not self.is_admin:
            QMessageBox.warning(self, "提示", "只有超级管理员可以查看设备分配")
            return
        
        self.refresh_assign_btn.setEnabled(False)
        self.refresh_assign_btn.setText("🔄 加载中...")
        
        # 使用独立线程加载数据，避免阻塞UI
        threading.Thread(target=self._load_assignment_data, daemon=True).start()
    
    def _load_assignment_data(self):
        """在后台线程加载设备分配数据"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            # 尝试连接服务器
            try:
                sock.connect((SERVER_IP, PC_SHORT_PORT))
            except socket.timeout:
                self._show_assignment_error("连接服务器超时，请检查网络连接")
                return
            except ConnectionRefusedError:
                self._show_assignment_error("服务器拒绝连接，请确认服务器是否运行")
                return
            
            # 发送获取所有设备和分配信息的请求（使用Token认证）
            target_user = self.assign_user.currentText() if self.assign_user.currentText() else ""
            request_data = {
                "action": "get_assigned_devices_info",
                "token": self.auth_token,
                "target_user": target_user
            }
            request_json = json.dumps(request_data)
            print(f"[设备分配] 获取用户 {target_user or '全部'} 的分配信息")
            sock.send(request_json.encode('utf-8'))
            
            response_data = sock.recv(8192).decode('utf-8')
            sock.close()
            
            response = json.loads(response_data)
            
            if response.get("code") == 0:
                # 获取所有设备
                all_devices = response.get("devices", [])
                # 获取分配信息 {hid: [user1, user2, ...]}
                user_devices = response.get("user_devices", [])
                # 转换格式：从 user_devices 列表转换为 {hid: [user1, user2]}
                self._device_assignment_map = {}
                current_target_user = self.assign_user.currentText() if self.assign_user.currentText() else None
                if current_target_user:
                    for hid in user_devices:
                        if hid not in self._device_assignment_map:
                            self._device_assignment_map[hid] = []
                        self._device_assignment_map[hid].append(current_target_user)
                
                print(f"[设备分配] 获取到 {len(all_devices)} 个设备")
                
                # 在主线程更新UI
                self._update_assignment_table(all_devices)
            else:
                error_msg = response.get("msg", "获取数据失败")
                print(f"[设备分配] 服务器返回错误: {error_msg}")
                self._show_assignment_error(error_msg)
        except Exception as e:
            self._show_assignment_error(str(e))
    
    # 定义信号用于在主线程更新表格
    update_assignment_table_signal = pyqtSignal(list)
    
    def _update_assignment_table(self, devices):
        """更新设备分配表格（在主线程执行）- 使用信号槽机制"""
        # 使用信号槽机制确保在主线程执行
        self.update_assignment_table_signal.emit(devices)
    
    def _do_update_assignment_table(self, devices):
        """实际更新表格的实现"""
        print(f"[设备分配表格] 开始更新表格，设备数量: {len(devices)}")
        self.device_assign_table.setRowCount(len(devices))
        
        assigned_count = 0
        for row, device in enumerate(devices):
            hid = device.get("hid", "") if isinstance(device, dict) else device
            print(f"[设备分配表格] 处理第 {row} 行，设备: {hid}")
            
            # 复选框
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.device_assign_table.setCellWidget(row, 0, checkbox_widget)
            
            # 设备编号
            self.device_assign_table.setItem(row, 1, QTableWidgetItem(hid))
            
            # 设备名称
            device_name = self.device_name_manager.get_device_name(hid)
            self.device_assign_table.setItem(row, 2, QTableWidgetItem(device_name))
            
            # 已分配用户
            assigned_users = self._device_assignment_map.get(hid, [])
            if assigned_users:
                users_text = ", ".join(assigned_users)
                assigned_count += 1
            else:
                users_text = "未分配"
            item = QTableWidgetItem(users_text)
            if assigned_users:
                item.setBackground(QColor(200, 255, 200))  # 已分配用绿色
            else:
                item.setBackground(QColor(255, 230, 230))  # 未分配用淡红色
            self.device_assign_table.setItem(row, 3, item)
        
        # 更新统计
        total = len(devices)
        unassigned = total - assigned_count
        self.assign_stats_label.setText(f"设备总数: {total} | 已分配: {assigned_count} | 未分配: {unassigned}")
        
        # 恢复按钮
        self.refresh_assign_btn.setEnabled(True)
        self.refresh_assign_btn.setText("🔄 刷新")
        print(f"[设备分配表格] 表格更新完成，共 {total} 个设备，已分配: {assigned_count}")
        
        # 刷新后自动勾选当前用户已分配的设备
        current_user = self.assign_user.currentText()
        if current_user:
            print(f"[设备分配表格] 刷新后自动勾选用户 {current_user} 的设备")
            self._check_user_assigned_devices(current_user)
    
    def _show_assignment_error(self, error_msg):
        """显示错误信息"""
        # 使用 QTimer.singleShot 确保在主线程执行
        QTimer.singleShot(0, lambda: self._do_show_assignment_error(error_msg))
    
    def _do_show_assignment_error(self, error_msg):
        """执行错误显示"""
        QMessageBox.warning(self, "错误", f"加载设备分配数据失败: {error_msg}")
        self.refresh_assign_btn.setEnabled(True)
        self.refresh_assign_btn.setText("🔄 刷新")
    
    def _update_assignment_after_save(self, username: str, selected_devices: list):
        """保存成功后更新分配信息，保持当前用户的勾选状态"""
        print(f"[设备分配] 保存成功，更新分配信息，用户: {username}, 设备: {selected_devices}")
        
        # 更新分配映射
        for hid in selected_devices:
            if hid not in self._device_assignment_map:
                self._device_assignment_map[hid] = []
            if username not in self._device_assignment_map[hid]:
                self._device_assignment_map[hid].append(username)
        
        # 移除该用户之前分配但本次未选择的设备
        for hid, users in list(self._device_assignment_map.items()):
            if username in users and hid not in selected_devices:
                users.remove(username)
                if not users:
                    self._device_assignment_map[hid] = []
        
        # 更新表格中的分配显示（已分配用户列），保持勾选状态
        for row in range(self.device_assign_table.rowCount()):
            hid_item = self.device_assign_table.item(row, 1)
            if hid_item:
                hid = hid_item.text()
                assigned_users = self._device_assignment_map.get(hid, [])
                
                # 更新已分配用户列
                if assigned_users:
                    users_text = ", ".join(assigned_users)
                    item = QTableWidgetItem(users_text)
                    item.setBackground(QColor(200, 255, 200))  # 已分配用绿色
                else:
                    item = QTableWidgetItem("未分配")
                    item.setBackground(QColor(255, 230, 230))  # 未分配用淡红色
                
                self.device_assign_table.setItem(row, 3, item)
        
        # 更新统计
        assigned_count = sum(1 for users in self._device_assignment_map.values() if users)
        total = self.device_assign_table.rowCount()
        unassigned = total - assigned_count
        self.assign_stats_label.setText(f"设备总数: {total} | 已分配: {assigned_count} | 未分配: {unassigned}")
        
        print(f"[设备分配] 分配信息更新完成")
    
    def _save_device_assignment(self):
        """保存设备分配 - 新版使用表格"""
        username = self.assign_user.currentText()
        if not username:
            QMessageBox.warning(self, "提示", "请选择要分配的用户")
            return
        
        # 获取选中的设备
        selected_devices = []
        for row in range(self.device_assign_table.rowCount()):
            checkbox_widget = self.device_assign_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    hid_item = self.device_assign_table.item(row, 1)
                    if hid_item:
                        selected_devices.append(hid_item.text())
        
        if not selected_devices:
            reply = QMessageBox.question(self, "确认", 
                f"确定要清空用户 {username} 的所有设备分配吗？",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        # 发送到服务器保存设备分配
        if self.network_thread and self.network_thread.socket:
            request = json.dumps({
                "action": "assign_devices",
                "username": username,
                "devices": selected_devices
            })
            response = self.network_thread.send_request(request)
            if response.get("code") == 0:
                QMessageBox.information(self, "成功", 
                    f"已为 {username} 分配 {len(selected_devices)} 个设备")
                # 保存成功后更新分配信息，保持当前勾选状态
                self._update_assignment_after_save(username, selected_devices)
            else:
                QMessageBox.warning(self, "失败", response.get("msg", "设备分配失败"))
        else:
            QMessageBox.warning(self, "错误", "网络连接不可用")
    
    def _show_settings(self):
        """显示设置对话框"""
        # 使用非模态对话框，避免阻塞报警弹窗
        if not hasattr(self, '_settings_dialog') or self._settings_dialog is None:
            self._settings_dialog = AlarmSettingsDialog(self)
            # 对话框关闭时重置引用
            self._settings_dialog.finished.connect(self._on_settings_dialog_closed)
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()
    
    def _on_settings_dialog_closed(self):
        """设置对话框关闭回调"""
        self._settings_dialog = None
    
    def _show_service_contact(self):
        """显示客服联系方式"""
        QMessageBox.information(
            self,
            "📞 客服联系",
            "<h2 style='color: #17a2b8; margin-bottom: 15px;'>客服联系方式</h2>"
            "<p style='font-size: 14px; margin: 10px 0;'>如有任何问题，请联系客服：</p>"
            "<p style='font-size: 18px; font-weight: bold; color: #28a745; margin: 15px 0;'>"
            "📱 电话：13037990547</p>"
            "<p style='font-size: 12px; color: #666; margin-top: 20px;'>"
            "工作时间：周一至周日 9:00-18:00</p>",
            QMessageBox.StandardButton.Ok
        )
    
    def _logout(self):
        """退出登录"""
        # ✅ 设置标志位：正在退出登录，不显示断网提示
        self._is_logging_out = True
        
        # ✅ 先隐藏断网提示（退出登录是主动操作，不应该显示断网提示）
        self._hide_disconnect_overlay()
        
        # 停止健康检查定时器
        if hasattr(self, '_health_check_timer') and self._health_check_timer:
            self._health_check_timer.stop()
        
        if self.network_thread:
            self.network_thread.stop()
            self.network_thread = None
        
        # ✅ 清除Token（退出登录后失效）
        self.auth_token = ""
        print("[退出登录] 已清除认证Token")
        
        # ⚠️ 不再清空缓存和实时数据，保留给下次登录使用
        # 用户可能只是想切换账号查看相同的数据
        
        # 只重置用户相关状态，不清空实际数据
        self.current_user = None
        self.is_admin = False
        # 注意：不执行 self.devices.clear() 和 self.assigned_devices.clear()
        # 这样重新登录后，之前的设备和实时数据仍然可见
        
        self.user_label.setText("未登录")
        self.role_label.setText("")
        
        for btn in self.admin_menus:
            btn.setVisible(False)
        
        self.status_label.setText("已退出登录")
        self._show_login()
    
    def _show_login(self):
        """显示登录对话框"""
        dialog = LoginDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            username, password = dialog.get_credentials()
            if username and password:
                self.login(username, password)
            else:
                # 没有输入用户名密码，重新显示登录框
                QTimer.singleShot(100, self._show_login)
        else:
            # 用户取消登录，退出程序
            self._quit()
    
    def _tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _quit(self):
        """退出程序"""
        self.tray_icon.hide()
        
        if hasattr(self, '_device_refresh_timer') and self._device_refresh_timer:
            self._device_refresh_timer.stop()
            print("[设备列表] 停止自动刷新定时器")
        
        if hasattr(self, '_online_status_timer') and self._online_status_timer:
            self._online_status_timer.stop()
            print("[设备在线] 停止在线状态检查定时器")
        
        if hasattr(self, '_health_check_timer') and self._health_check_timer:
            self._health_check_timer.stop()
            print("[网络健康] 停止健康检查定时器")
        
        if self.network_thread:
            self.network_thread.stop()
        
        db_manager.close_all()
        QApplication.quit()
    
    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        self.hide()
        self.tray_icon.show()
        self.tray_icon.showMessage(
            APP_NAME,
            "程序已最小化到系统托盘",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        event.ignore()


# ===================== 程序入口 =====================
def main():
    """主函数"""
    # 检查是否已有实例运行
    check_single_instance()
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle('Fusion')
    
    window = MainWindow()
    QTimer.singleShot(100, window._show_login)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
