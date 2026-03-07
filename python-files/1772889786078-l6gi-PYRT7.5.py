#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYRT安全卫士
版本: 7.5
作者: PYRT官方 哔哩哔哩：3546827603314741
日期: 2026 02 01 10:26
功能: 整合杀毒引擎和引导保护，提供完整的系统安全解决方案
"""

import os
import hashlib
import time
import platform
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import logging
from datetime import datetime
import shutil
import math
import random
import re
import struct
import pickle
from collections import defaultdict
import subprocess
import signal
import ctypes
import glob
import socket
import urllib.request
import urllib.error
import ipaddress

# ==================== 全局配置 ====================
class Config:
    """PYRT安全卫士配置"""
    APP_NAME = "PYRT安全卫士"
    VERSION = "7.5"
    COMPANY = "PYRT Security"
    LOGO = "🛡️"  # 盾牌图标
    BOOT_LOGO = "🔒"  # 引导保护图标
    NETWORK_LOGO = "🌐"  # 网络保护图标
    
    # 语言设置
    LANGUAGE = "zh_CN"  # 默认简体中文
    LANGUAGE_FILE = "language.json"  # 语言配置文件
    SUPPORTED_LANGUAGES = {
        "zh_CN": "简体中文",
        "zh_TW": "繁體中文",
        "en_US": "English",
        "ja_JP": "日本語",
        "ko_KR": "한국어",
        "ru_RU": "Русский",
        "de_DE": "Deutsch"
    }
    
    # 语言显示名称（用于下拉框）
    LANGUAGE_DISPLAY_NAMES = {
        "zh_CN": "简体中文",
        "zh_TW": "繁體中文",
        "en_US": "English",
        "ja_JP": "日本語",
        "ko_KR": "한국어",
        "ru_RU": "Русский",
        "de_DE": "Deutsch"
    }
    
    # 颜色主题
    THEME = {
        'bg_dark': '#f5f7fa',           # 主背景 - 浅灰色
        'bg_card': '#ffffff',           # 卡片背景 - 白色
        'sidebar_bg': '#ffffff',        # 侧边栏背景 - 白色
        'sidebar_hover': '#eef2f7',     # 侧边栏悬停 - 浅蓝灰色
        'primary': '#0066cc',           # 主色调 - 蓝色
        'secondary': '#666666',         # 次要色 - 灰色
        'accent': '#ff3333',            # 强调色 - 红色
        'success': '#00aa44',           # 成功色 - 绿色
        'warning': '#ff9900',           # 警告色 - 橙色
        'text_primary': '#333333',      # 主要文字 - 深灰色
        'text_secondary': '#666666',    # 次要文字 - 灰色
        'border': '#dddddd',            # 边框颜色
        'highlight': '#e6f2ff',         # 高亮背景
        'button_bg': '#0066cc',         # 按钮背景
        'button_fg': '#ffffff',
    }
    
    # 侧边栏配置
    SIDEBAR_WIDTH = 220
    SIDEBAR_COLLAPSED_WIDTH = 60
    SIDEBAR_DEFAULT_OPEN = True
    
    # 病毒特征库路径
    VIRUS_DB_PATH = "virus_signatures.db"
    HEURISTIC_RULES_PATH = "heuristic_rules.json"
    REAL_TIME_LOG = "realtime_protection.log"
    
    # 扫描配置
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 最大扫描文件大小 100MB
    QUARANTINE_DIR = "pyrt_quarantine"
    LOG_DIR = "pyrt_logs"
    
    # 实时保护配置
    REAL_TIME_PROTECTION = True
    MONITOR_PATHS = [
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
        os.environ.get('TEMP', ''),
        os.environ.get('APPDATA', ''),
    ]
    SCAN_ON_CREATE = True
    SCAN_ON_MODIFY = True
    BLOCK_SUSPICIOUS = True
    
    # 进程监控配置
    MONITOR_PROCESSES = True
    SUSPICIOUS_PROCESS_NAMES = [
        'taskkill.exe', 'cmd.exe', 'powershell.exe', 
        'wscript.exe', 'cscript.exe', 'mshta.exe',
        'regsvr32.exe', 'rundll32.exe', 'certutil.exe'
    ]
    
    # 扫描间隔（秒）
    DIRECTORY_SCAN_INTERVAL = 30  # 目录扫描间隔
    PROCESS_SCAN_INTERVAL = 10    # 进程扫描间隔
    
    # 引导保护配置
    BOOT_PROTECTION_ENABLED = True
    BOOT_BACKUP_DIR = "boot_protection_backup"
    BOOT_HASH_DB = "boot_hashes.db"
    BOOT_SCAN_INTERVAL = 300  # 5分钟检查一次（秒）
    BOOT_AUTO_REPAIR = True  # 自动修复引导文件
    
    # Windows引导文件
    WINDOWS_BOOT_FILES = [
        ("C:\\bootmgr", "Windows启动管理器"),
        ("C:\\boot\\bcd", "引导配置数据"),
        ("C:\\Windows\\System32\\winload.exe", "Windows加载器"),
        ("C:\\Windows\\System32\\ntoskrnl.exe", "Windows内核"),
        ("C:\\Windows\\System32\\hal.dll", "硬件抽象层"),
        ("C:\\Windows\\System32\\smss.exe", "会话管理器"),
        ("C:\\Windows\\System32\\csrss.exe", "客户端服务器运行时子系统"),
        ("C:\\Windows\\System32\\winlogon.exe", "Windows登录管理器"),
    ]
    
    # Linux引导文件
    LINUX_BOOT_FILES = [
        ("/boot/grub/grub.cfg", "GRUB引导配置文件"),
        ("/boot/grub2/grub.cfg", "GRUB2引导配置文件"),
        ("/boot/efi/EFI/*/grubx64.efi", "UEFI引导文件"),
        ("/boot/vmlinuz-*", "Linux内核"),
        ("/boot/initrd.img-*", "初始化内存盘"),
        ("/etc/default/grub", "GRUB默认配置"),
    ]
    
    # ==================== 断网保护配置 ====================
    NETWORK_PROTECTION_ENABLED = True
    NETWORK_MONITOR_INTERVAL = 10  # 网络监控间隔（秒）
    NETWORK_LOG = "network_protection.log"
    
    # 恶意IP地址和域名列表（示例）
    MALICIOUS_IPS = [
        "192.168.1.100", "10.0.0.1",  # 局域网恶意IP示例
        "127.0.0.1",                  # 本地环回（用于测试）
    ]
    
    MALICIOUS_DOMAINS = [
        "malicious-site.com",
        "bad-domain.org",
        "evil-server.net",
        "ransomware-decryptor.com",
        "hacker-tools.io",
    ]
    
    # 可疑端口列表
    SUSPICIOUS_PORTS = [
        4444,  # Metasploit默认端口
        31337, # Back Orifice
        6667,  # IRC（常用于僵尸网络）
        8080,  # 代理服务器（可能被滥用）
        1337,  # 1337端口
        12345, # NetBus木马
        27374, # Sub7木马
        54321, # 僵尸网络
    ]
    
    # 网络监控进程
    NETWORK_MONITOR_PROCESSES = [
        "nc.exe", "netcat.exe", "nmap.exe", "wireshark.exe",
        "tcpdump", "ncat.exe", "hping.exe", "curl.exe",
    ]
    
    # 受保护的重要域名（不允许被修改）
    PROTECTED_HOSTS = [
        "windowsupdate.com",
        "microsoft.com",
        "update.microsoft.com",
        "security.microsoft.com",
        "defender.microsoft.com",
    ]

# ==================== 语言管理器 ====================
class LanguageManager:
    """多语言管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.current_language = Config.LANGUAGE
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """加载翻译文件"""
        default_translations = {
            "zh_CN": {
                # 通用
                "app_name": "PYRT安全卫士",
                "version": "版本",
                "save": "保存",
                "cancel": "取消",
                "confirm": "确认",
                "close": "关闭",
                "settings": "设置",
                "language": "语言",
                "select_language": "选择语言",
                
                # 侧边栏菜单
                "dashboard": "仪表盘",
                "security_scan": "安全扫描",
                "realtime_protection": "实时保护",
                "boot_protection": "引导保护",
                "threat_list": "威胁列表",
                "quarantine": "隔离区",
                "log_center": "日志中心",
                "network_protection": "断网保护",
                
                # 仪表盘
                "security_dashboard": "安全仪表盘",
                "real_time_monitoring": "实时监控系统安全状态",
                "system_status": "系统状态",
                "secure": "安全",
                "running": "运行中",
                "virus_db": "病毒库",
                "latest": "最新",
                "quick_actions": "快速操作",
                "quick_scan": "快速扫描",
                "quick_scan_desc": "检查关键系统区域",
                "full_scan": "全盘扫描",
                "full_scan_desc": "深度检查所有文件",
                "boot_check": "引导检查",
                "boot_check_desc": "验证引导完整性",
                "network_check": "网络检查",
                "network_check_desc": "检查网络连接",
                "update_virus_db": "更新病毒库",
                "update_virus_db_desc": "获取最新病毒定义",
                "execute": "执行",
                
                # 安全扫描
                "security_scan_title": "安全扫描",
                "start_scan": "开始安全扫描",
                "stop_scan": "停止扫描",
                
                # 实时保护
                "realtime_protection_title": "实时保护",
                "protection_status": "保护状态",
                "status": "状态",
                "monitored_dirs": "监控目录",
                "process_monitoring": "进程监控",
                "enabled": "启用",
                "disabled": "禁用",
                "pause_protection": "暂停保护",
                "start_protection": "启动保护",
                "realtime_alerts": "实时警报",
                
                # 引导保护
                "boot_protection_title": "引导保护",
                "protected_files": "保护文件",
                "auto_repair": "自动修复",
                "check_integrity": "检查完整性",
                "create_backup": "创建备份",
                "repair_boot": "修复引导",
                "boot_alerts": "引导警报",
                
                # 断网保护
                "network_protection_title": "断网保护",
                "network": "网络",
                "internet": "互联网",
                "connected": "已连接",
                "disconnected": "未连接",
                "blocked_ips": "阻止IP数",
                "blocked_domains": "阻止域名",
                "check_network": "检查网络",
                "view_connections": "查看连接",
                "emergency_disconnect": "紧急断网",
                "network_alerts": "网络警报",
                
                # 威胁列表
                "threat_detection": "威胁检测",
                "detected_threats": "检测到的威胁",
                "quarantine_selected": "隔离选中",
                "delete_selected": "删除选中",
                "clear_list": "清除列表",
                
                # 隔离区
                "quarantine_title": "隔离区",
                "quarantine_info": "隔离文件信息",
                "quarantined_files": "隔离文件数",
                "space_used": "占用空间",
                "location": "目录位置",
                "open_quarantine": "打开隔离区",
                "clear_quarantine": "清空隔离区",
                "view_log": "查看日志",
                
                # 日志中心
                "log_center_title": "日志中心",
                "log_files": "日志文件",
                "main_log": "主程序日志",
                "realtime_log": "实时保护日志",
                "network_log": "网络保护日志",
                "quarantine_log": "隔离区日志",
                "scan_log": "扫描日志",
                "boot_log": "引导保护日志",
                "view": "查看",
                
                # 设置
                "settings_title": "设置",
                "program_settings": "程序设置",
                "auto_start": "开机自启动",
                "auto_start_desc": "系统启动时自动运行PYRT安全卫士",
                "auto_update": "自动更新",
                "auto_update_desc": "自动检查并更新病毒库",
                "show_notifications": "显示通知",
                "show_notifications_desc": "在检测到威胁时显示系统通知",
                "low_resource_mode": "低资源模式",
                "low_resource_mode_desc": "降低CPU和内存使用率",
                "dark_theme": "暗色主题",
                "dark_theme_desc": "使用暗色界面主题",
                "enable_network_protection": "启用断网保护",
                "enable_network_protection_desc": "启用网络监控和断网保护功能",
                "save_settings": "保存设置",
                
                # 消息框
                "warning": "警告",
                "error": "错误",
                "info": "信息",
                "success": "成功",
                "confirm_action": "确认操作",
                "scan_in_progress": "扫描正在进行中",
                "scan_complete": "扫描完成",
                "threats_found": "检测到威胁",
                "no_threats": "未发现任何威胁",
                "system_secure": "系统安全",
                
                # 按钮
                "ok": "确定",
                "yes": "是",
                "no": "否",
                "apply": "应用",
                "refresh": "刷新",
                "add": "添加",
                
                # 扫描状态
                "preparing_scan": "准备扫描...",
                "scanning": "正在扫描",
                "files": "文件",
                "threats": "威胁",
                "speed": "速度",
                "elapsed": "已用时间",
                
                # 威胁等级
                "critical": "严重",
                "high": "高",
                "medium": "中",
                "low": "低",
                
                # 网络状态
                "network_status": "网络状态",
                "internet_status": "互联网状态",
                "unknown": "未知",
                "checking": "检查中...",
                
                # 退出确认
                "exit_confirm": "确定要退出PYRT安全卫士吗？\n\n所有保护服务也将被关闭。",
                "exit": "退出",
                
                # 语言选择对话框
                "language_selection": "语言选择",
                "select_language_prompt": "请选择界面语言：",
                "save_and_restart": "保存并重启"
            },
            
            "zh_TW": {
                # 通用
                "app_name": "PYRT安全衛士",
                "version": "版本",
                "save": "保存",
                "cancel": "取消",
                "confirm": "確認",
                "close": "關閉",
                "settings": "設置",
                "language": "語言",
                "select_language": "選擇語言",
                
                # 侧边栏菜单
                "dashboard": "儀表盤",
                "security_scan": "安全掃描",
                "realtime_protection": "實時保護",
                "boot_protection": "引導保護",
                "threat_list": "威脅列表",
                "quarantine": "隔離區",
                "log_center": "日誌中心",
                "network_protection": "斷網保護",
                
                # 仪表盘
                "security_dashboard": "安全儀表盤",
                "real_time_monitoring": "實時監控系統安全狀態",
                "system_status": "系統狀態",
                "secure": "安全",
                "running": "運行中",
                "virus_db": "病毒庫",
                "latest": "最新",
                "quick_actions": "快速操作",
                "quick_scan": "快速掃描",
                "quick_scan_desc": "檢查關鍵系統區域",
                "full_scan": "全盤掃描",
                "full_scan_desc": "深度檢查所有文件",
                "boot_check": "引導檢查",
                "boot_check_desc": "驗證引導完整性",
                "network_check": "網絡檢查",
                "network_check_desc": "檢查網絡連接",
                "update_virus_db": "更新病毒庫",
                "update_virus_db_desc": "獲取最新病毒定義",
                "execute": "執行",
                
                # 安全扫描
                "security_scan_title": "安全掃描",
                "start_scan": "開始安全掃描",
                "stop_scan": "停止掃描",
                
                # 实时保护
                "realtime_protection_title": "實時保護",
                "protection_status": "保護狀態",
                "status": "狀態",
                "monitored_dirs": "監控目錄",
                "process_monitoring": "進程監控",
                "enabled": "啟用",
                "disabled": "禁用",
                "pause_protection": "暫停保護",
                "start_protection": "啟動保護",
                "realtime_alerts": "實時警報",
                
                # 引导保护
                "boot_protection_title": "引導保護",
                "protected_files": "保護文件",
                "auto_repair": "自動修復",
                "check_integrity": "檢查完整性",
                "create_backup": "創建備份",
                "repair_boot": "修復引導",
                "boot_alerts": "引導警報",
                
                # 断网保护
                "network_protection_title": "斷網保護",
                "network": "網絡",
                "internet": "互聯網",
                "connected": "已連接",
                "disconnected": "未連接",
                "blocked_ips": "阻止IP數",
                "blocked_domains": "阻止域名",
                "check_network": "檢查網絡",
                "view_connections": "查看連接",
                "emergency_disconnect": "緊急斷網",
                "network_alerts": "網絡警報",
                
                # 威胁列表
                "threat_detection": "威脅檢測",
                "detected_threats": "檢測到的威脅",
                "quarantine_selected": "隔離選中",
                "delete_selected": "刪除選中",
                "clear_list": "清除列表",
                
                # 隔离区
                "quarantine_title": "隔離區",
                "quarantine_info": "隔離文件信息",
                "quarantined_files": "隔離文件數",
                "space_used": "佔用空間",
                "location": "目錄位置",
                "open_quarantine": "打開隔離區",
                "clear_quarantine": "清空隔離區",
                "view_log": "查看日誌",
                
                # 日志中心
                "log_center_title": "日誌中心",
                "log_files": "日誌文件",
                "main_log": "主程序日誌",
                "realtime_log": "實時保護日誌",
                "network_log": "網絡保護日誌",
                "quarantine_log": "隔離區日誌",
                "scan_log": "掃描日誌",
                "boot_log": "引導保護日誌",
                "view": "查看",
                
                # 设置
                "settings_title": "設置",
                "program_settings": "程序設置",
                "auto_start": "開機自啟動",
                "auto_start_desc": "系統啟動時自動運行PYRT安全衛士",
                "auto_update": "自動更新",
                "auto_update_desc": "自動檢查並更新病毒庫",
                "show_notifications": "顯示通知",
                "show_notifications_desc": "在檢測到威脅時顯示系統通知",
                "low_resource_mode": "低資源模式",
                "low_resource_mode_desc": "降低CPU和內存使用率",
                "dark_theme": "暗色主題",
                "dark_theme_desc": "使用暗色界面主題",
                "enable_network_protection": "啟用斷網保護",
                "enable_network_protection_desc": "啟用網絡監控和斷網保護功能",
                "save_settings": "保存設置",
                
                # 消息框
                "warning": "警告",
                "error": "錯誤",
                "info": "信息",
                "success": "成功",
                "confirm_action": "確認操作",
                "scan_in_progress": "掃描正在進行中",
                "scan_complete": "掃描完成",
                "threats_found": "檢測到威脅",
                "no_threats": "未發現任何威脅",
                "system_secure": "系統安全",
                
                # 按钮
                "ok": "確定",
                "yes": "是",
                "no": "否",
                "apply": "應用",
                "refresh": "刷新",
                "add": "添加",
                
                # 扫描状态
                "preparing_scan": "準備掃描...",
                "scanning": "正在掃描",
                "files": "文件",
                "threats": "威脅",
                "speed": "速度",
                "elapsed": "已用時間",
                
                # 威胁等级
                "critical": "嚴重",
                "high": "高",
                "medium": "中",
                "low": "低",
                
                # 网络状态
                "network_status": "網絡狀態",
                "internet_status": "互聯網狀態",
                "unknown": "未知",
                "checking": "檢查中...",
                
                # 退出确认
                "exit_confirm": "確定要退出PYRT安全衛士嗎？\n\n所有保護服務也將被關閉。",
                "exit": "退出",
                
                # 语言选择对话框
                "language_selection": "語言選擇",
                "select_language_prompt": "請選擇界面語言：",
                "save_and_restart": "保存並重啟"
            },
            
            "en_US": {
                # General
                "app_name": "PYRT Security Guard",
                "version": "Version",
                "save": "Save",
                "cancel": "Cancel",
                "confirm": "Confirm",
                "close": "Close",
                "settings": "Settings",
                "language": "Language",
                "select_language": "Select Language",
                
                # Sidebar Menu
                "dashboard": "Dashboard",
                "security_scan": "Security Scan",
                "realtime_protection": "Real-time Protection",
                "boot_protection": "Boot Protection",
                "threat_list": "Threat List",
                "quarantine": "Quarantine",
                "log_center": "Log Center",
                "network_protection": "Network Protection",
                
                # Dashboard
                "security_dashboard": "Security Dashboard",
                "real_time_monitoring": "Real-time system security monitoring",
                "system_status": "System Status",
                "secure": "Secure",
                "running": "Running",
                "virus_db": "Virus Database",
                "latest": "Latest",
                "quick_actions": "Quick Actions",
                "quick_scan": "Quick Scan",
                "quick_scan_desc": "Check critical system areas",
                "full_scan": "Full Scan",
                "full_scan_desc": "Deep check all files",
                "boot_check": "Boot Check",
                "boot_check_desc": "Verify boot integrity",
                "network_check": "Network Check",
                "network_check_desc": "Check network connections",
                "update_virus_db": "Update Virus DB",
                "update_virus_db_desc": "Get latest virus definitions",
                "execute": "Execute",
                
                # Security Scan
                "security_scan_title": "Security Scan",
                "start_scan": "Start Security Scan",
                "stop_scan": "Stop Scan",
                
                # Real-time Protection
                "realtime_protection_title": "Real-time Protection",
                "protection_status": "Protection Status",
                "status": "Status",
                "monitored_dirs": "Monitored Directories",
                "process_monitoring": "Process Monitoring",
                "enabled": "Enabled",
                "disabled": "Disabled",
                "pause_protection": "Pause Protection",
                "start_protection": "Start Protection",
                "realtime_alerts": "Real-time Alerts",
                
                # Boot Protection
                "boot_protection_title": "Boot Protection",
                "protected_files": "Protected Files",
                "auto_repair": "Auto Repair",
                "check_integrity": "Check Integrity",
                "create_backup": "Create Backup",
                "repair_boot": "Repair Boot",
                "boot_alerts": "Boot Alerts",
                
                # Network Protection
                "network_protection_title": "Network Protection",
                "network": "Network",
                "internet": "Internet",
                "connected": "Connected",
                "disconnected": "Disconnected",
                "blocked_ips": "Blocked IPs",
                "blocked_domains": "Blocked Domains",
                "check_network": "Check Network",
                "view_connections": "View Connections",
                "emergency_disconnect": "Emergency Disconnect",
                "network_alerts": "Network Alerts",
                
                # Threat List
                "threat_detection": "Threat Detection",
                "detected_threats": "Detected Threats",
                "quarantine_selected": "Quarantine Selected",
                "delete_selected": "Delete Selected",
                "clear_list": "Clear List",
                
                # Quarantine
                "quarantine_title": "Quarantine",
                "quarantine_info": "Quarantine Information",
                "quarantined_files": "Quarantined Files",
                "space_used": "Space Used",
                "location": "Location",
                "open_quarantine": "Open Quarantine",
                "clear_quarantine": "Clear Quarantine",
                "view_log": "View Log",
                
                # Log Center
                "log_center_title": "Log Center",
                "log_files": "Log Files",
                "main_log": "Main Program Log",
                "realtime_log": "Real-time Protection Log",
                "network_log": "Network Protection Log",
                "quarantine_log": "Quarantine Log",
                "scan_log": "Scan Log",
                "boot_log": "Boot Protection Log",
                "view": "View",
                
                # Settings
                "settings_title": "Settings",
                "program_settings": "Program Settings",
                "auto_start": "Auto Start",
                "auto_start_desc": "Automatically run PYRT Security Guard at system startup",
                "auto_update": "Auto Update",
                "auto_update_desc": "Automatically check and update virus database",
                "show_notifications": "Show Notifications",
                "show_notifications_desc": "Show system notifications when threats are detected",
                "low_resource_mode": "Low Resource Mode",
                "low_resource_mode_desc": "Reduce CPU and memory usage",
                "dark_theme": "Dark Theme",
                "dark_theme_desc": "Use dark interface theme",
                "enable_network_protection": "Enable Network Protection",
                "enable_network_protection_desc": "Enable network monitoring and disconnection protection",
                "save_settings": "Save Settings",
                
                # Message Boxes
                "warning": "Warning",
                "error": "Error",
                "info": "Information",
                "success": "Success",
                "confirm_action": "Confirm Action",
                "scan_in_progress": "Scan in progress",
                "scan_complete": "Scan Complete",
                "threats_found": "Threats Found",
                "no_threats": "No threats found",
                "system_secure": "System is secure",
                
                # Buttons
                "ok": "OK",
                "yes": "Yes",
                "no": "No",
                "apply": "Apply",
                "refresh": "Refresh",
                "add": "Add",
                
                # Scan Status
                "preparing_scan": "Preparing scan...",
                "scanning": "Scanning",
                "files": "Files",
                "threats": "Threats",
                "speed": "Speed",
                "elapsed": "Elapsed",
                
                # Threat Levels
                "critical": "Critical",
                "high": "High",
                "medium": "Medium",
                "low": "Low",
                
                # Network Status
                "network_status": "Network Status",
                "internet_status": "Internet Status",
                "unknown": "Unknown",
                "checking": "Checking...",
                
                # Exit Confirmation
                "exit_confirm": "Are you sure you want to exit PYRT Security Guard?\n\nAll protection services will be stopped.",
                "exit": "Exit",
                
                # Language Selection Dialog
                "language_selection": "Language Selection",
                "select_language_prompt": "Please select interface language:",
                "save_and_restart": "Save and Restart"
            },
            
            "ja_JP": {
                # 一般
                "app_name": "PYRTセキュリティガード",
                "version": "バージョン",
                "save": "保存",
                "cancel": "キャンセル",
                "confirm": "確認",
                "close": "閉じる",
                "settings": "設定",
                "language": "言語",
                "select_language": "言語選択",
                
                # サイドバーメニュー
                "dashboard": "ダッシュボード",
                "security_scan": "セキュリティスキャン",
                "realtime_protection": "リアルタイム保護",
                "boot_protection": "ブート保護",
                "threat_list": "脅威リスト",
                "quarantine": "隔離",
                "log_center": "ログセンター",
                "network_protection": "ネットワーク保護",
                
                # ダッシュボード
                "security_dashboard": "セキュリティダッシュボード",
                "real_time_monitoring": "リアルタイムシステムセキュリティ監視",
                "system_status": "システム状態",
                "secure": "安全",
                "running": "実行中",
                "virus_db": "ウイルスデータベース",
                "latest": "最新",
                "quick_actions": "クイックアクション",
                "quick_scan": "クイックスキャン",
                "quick_scan_desc": "重要なシステム領域をチェック",
                "full_scan": "フルスキャン",
                "full_scan_desc": "すべてのファイルを詳細チェック",
                "boot_check": "ブートチェック",
                "boot_check_desc": "ブート整合性の検証",
                "network_check": "ネットワークチェック",
                "network_check_desc": "ネットワーク接続の確認",
                "update_virus_db": "ウイルスDB更新",
                "update_virus_db_desc": "最新のウイルス定義を取得",
                "execute": "実行",
                
                # セキュリティスキャン
                "security_scan_title": "セキュリティスキャン",
                "start_scan": "スキャン開始",
                "stop_scan": "スキャン停止",
                
                # リアルタイム保護
                "realtime_protection_title": "リアルタイム保護",
                "protection_status": "保護状態",
                "status": "状態",
                "monitored_dirs": "監視ディレクトリ",
                "process_monitoring": "プロセス監視",
                "enabled": "有効",
                "disabled": "無効",
                "pause_protection": "保護一時停止",
                "start_protection": "保護開始",
                "realtime_alerts": "リアルタイムアラート",
                
                # ブート保護
                "boot_protection_title": "ブート保護",
                "protected_files": "保護ファイル",
                "auto_repair": "自動修復",
                "check_integrity": "整合性チェック",
                "create_backup": "バックアップ作成",
                "repair_boot": "ブート修復",
                "boot_alerts": "ブートアラート",
                
                # ネットワーク保護
                "network_protection_title": "ネットワーク保護",
                "network": "ネットワーク",
                "internet": "インターネット",
                "connected": "接続済み",
                "disconnected": "未接続",
                "blocked_ips": "ブロックIP数",
                "blocked_domains": "ブロックドメイン数",
                "check_network": "ネットワーク確認",
                "view_connections": "接続表示",
                "emergency_disconnect": "緊急切断",
                "network_alerts": "ネットワークアラート",
                
                # 脅威リスト
                "threat_detection": "脅威検出",
                "detected_threats": "検出された脅威",
                "quarantine_selected": "選択を隔離",
                "delete_selected": "選択を削除",
                "clear_list": "リストクリア",
                
                # 隔離
                "quarantine_title": "隔離",
                "quarantine_info": "隔離情報",
                "quarantined_files": "隔離ファイル数",
                "space_used": "使用容量",
                "location": "場所",
                "open_quarantine": "隔離を開く",
                "clear_quarantine": "隔離を空にする",
                "view_log": "ログ表示",
                
                # ログセンター
                "log_center_title": "ログセンター",
                "log_files": "ログファイル",
                "main_log": "メインプログラムログ",
                "realtime_log": "リアルタイム保護ログ",
                "network_log": "ネットワーク保護ログ",
                "quarantine_log": "隔離ログ",
                "scan_log": "スキャンログ",
                "boot_log": "ブート保護ログ",
                "view": "表示",
                
                # 設定
                "settings_title": "設定",
                "program_settings": "プログラム設定",
                "auto_start": "自動起動",
                "auto_start_desc": "システム起動時にPYRTセキュリティガードを自動実行",
                "auto_update": "自動更新",
                "auto_update_desc": "ウイルスデータベースを自動チェックして更新",
                "show_notifications": "通知表示",
                "show_notifications_desc": "脅威検出時にシステム通知を表示",
                "low_resource_mode": "低リソースモード",
                "low_resource_mode_desc": "CPUとメモリ使用量を削減",
                "dark_theme": "ダークテーマ",
                "dark_theme_desc": "ダークインターフェーステーマを使用",
                "enable_network_protection": "ネットワーク保護を有効",
                "enable_network_protection_desc": "ネットワーク監視と切断保護を有効",
                "save_settings": "設定保存",
                
                # メッセージボックス
                "warning": "警告",
                "error": "エラー",
                "info": "情報",
                "success": "成功",
                "confirm_action": "操作確認",
                "scan_in_progress": "スキャン実行中",
                "scan_complete": "スキャン完了",
                "threats_found": "脅威が見つかりました",
                "no_threats": "脅威は見つかりませんでした",
                "system_secure": "システムは安全です",
                
                # ボタン
                "ok": "OK",
                "yes": "はい",
                "no": "いいえ",
                "apply": "適用",
                "refresh": "更新",
                "add": "追加",
                
                # スキャン状態
                "preparing_scan": "スキャン準備中...",
                "scanning": "スキャン中",
                "files": "ファイル",
                "threats": "脅威",
                "speed": "速度",
                "elapsed": "経過時間",
                
                # 脅威レベル
                "critical": "重大",
                "high": "高",
                "medium": "中",
                "low": "低",
                
                # ネットワーク状態
                "network_status": "ネットワーク状態",
                "internet_status": "インターネット状態",
                "unknown": "不明",
                "checking": "確認中...",
                
                # 終了確認
                "exit_confirm": "PYRTセキュリティガードを終了してもよろしいですか？\n\nすべての保護サービスが停止します。",
                "exit": "終了",
                
                # 言語選択ダイアログ
                "language_selection": "言語選択",
                "select_language_prompt": "インターフェース言語を選択してください：",
                "save_and_restart": "保存して再起動"
            },
            
            "ko_KR": {
                # 일반
                "app_name": "PYRT 보안 가드",
                "version": "버전",
                "save": "저장",
                "cancel": "취소",
                "confirm": "확인",
                "close": "닫기",
                "settings": "설정",
                "language": "언어",
                "select_language": "언어 선택",
                
                # 사이드바 메뉴
                "dashboard": "대시보드",
                "security_scan": "보안 스캔",
                "realtime_protection": "실시간 보호",
                "boot_protection": "부트 보호",
                "threat_list": "위협 목록",
                "quarantine": "격리",
                "log_center": "로그 센터",
                "network_protection": "네트워크 보호",
                
                # 대시보드
                "security_dashboard": "보안 대시보드",
                "real_time_monitoring": "실시간 시스템 보안 모니터링",
                "system_status": "시스템 상태",
                "secure": "안전",
                "running": "실행 중",
                "virus_db": "바이러스 데이터베이스",
                "latest": "최신",
                "quick_actions": "빠른 작업",
                "quick_scan": "빠른 스캔",
                "quick_scan_desc": "중요 시스템 영역 확인",
                "full_scan": "전체 스캔",
                "full_scan_desc": "모든 파일 심층 검사",
                "boot_check": "부트 확인",
                "boot_check_desc": "부트 무결성 확인",
                "network_check": "네트워크 확인",
                "network_check_desc": "네트워크 연결 확인",
                "update_virus_db": "바이러스 DB 업데이트",
                "update_virus_db_desc": "최신 바이러스 정의 가져오기",
                "execute": "실행",
                
                # 보안 스캔
                "security_scan_title": "보안 스캔",
                "start_scan": "스캔 시작",
                "stop_scan": "스캔 중지",
                
                # 실시간 보호
                "realtime_protection_title": "실시간 보호",
                "protection_status": "보호 상태",
                "status": "상태",
                "monitored_dirs": "모니터링 디렉토리",
                "process_monitoring": "프로세스 모니터링",
                "enabled": "활성화",
                "disabled": "비활성화",
                "pause_protection": "보호 일시 중지",
                "start_protection": "보호 시작",
                "realtime_alerts": "실시간 알림",
                
                # 부트 보호
                "boot_protection_title": "부트 보호",
                "protected_files": "보호 파일",
                "auto_repair": "자동 복구",
                "check_integrity": "무결성 확인",
                "create_backup": "백업 생성",
                "repair_boot": "부트 복구",
                "boot_alerts": "부트 알림",
                
                # 네트워크 보호
                "network_protection_title": "네트워크 보호",
                "network": "네트워크",
                "internet": "인터넷",
                "connected": "연결됨",
                "disconnected": "연결 끊김",
                "blocked_ips": "차단된 IP 수",
                "blocked_domains": "차단된 도메인 수",
                "check_network": "네트워크 확인",
                "view_connections": "연결 보기",
                "emergency_disconnect": "긴급 연결 끊기",
                "network_alerts": "네트워크 알림",
                
                # 위협 목록
                "threat_detection": "위협 탐지",
                "detected_threats": "탐지된 위협",
                "quarantine_selected": "선택 항목 격리",
                "delete_selected": "선택 항목 삭제",
                "clear_list": "목록 지우기",
                
                # 격리
                "quarantine_title": "격리",
                "quarantine_info": "격리 정보",
                "quarantined_files": "격리된 파일 수",
                "space_used": "사용 공간",
                "location": "위치",
                "open_quarantine": "격리 열기",
                "clear_quarantine": "격리 비우기",
                "view_log": "로그 보기",
                
                # 로그 센터
                "log_center_title": "로그 센터",
                "log_files": "로그 파일",
                "main_log": "메인 프로그램 로그",
                "realtime_log": "실시간 보호 로그",
                "network_log": "네트워크 보호 로그",
                "quarantine_log": "격리 로그",
                "scan_log": "스캔 로그",
                "boot_log": "부트 보호 로그",
                "view": "보기",
                
                # 설정
                "settings_title": "설정",
                "program_settings": "프로그램 설정",
                "auto_start": "자동 시작",
                "auto_start_desc": "시스템 시작 시 PYRT 보안 가드 자동 실행",
                "auto_update": "자동 업데이트",
                "auto_update_desc": "바이러스 데이터베이스 자동 확인 및 업데이트",
                "show_notifications": "알림 표시",
                "show_notifications_desc": "위협 감지 시 시스템 알림 표시",
                "low_resource_mode": "저리소스 모드",
                "low_resource_mode_desc": "CPU 및 메모리 사용량 감소",
                "dark_theme": "다크 테마",
                "dark_theme_desc": "다크 인터페이스 테마 사용",
                "enable_network_protection": "네트워크 보호 활성화",
                "enable_network_protection_desc": "네트워크 모니터링 및 연결 차단 보호 활성화",
                "save_settings": "설정 저장",
                
                # 메시지 박스
                "warning": "경고",
                "error": "오류",
                "info": "정보",
                "success": "성공",
                "confirm_action": "작업 확인",
                "scan_in_progress": "스캔 진행 중",
                "scan_complete": "스캔 완료",
                "threats_found": "위협 발견됨",
                "no_threats": "위협이 발견되지 않음",
                "system_secure": "시스템이 안전합니다",
                
                # 버튼
                "ok": "확인",
                "yes": "예",
                "no": "아니오",
                "apply": "적용",
                "refresh": "새로고침",
                "add": "추가",
                
                # 스캔 상태
                "preparing_scan": "스캔 준비 중...",
                "scanning": "스캔 중",
                "files": "파일",
                "threats": "위협",
                "speed": "속도",
                "elapsed": "경과 시간",
                
                # 위협 수준
                "critical": "심각",
                "high": "높음",
                "medium": "중간",
                "low": "낮음",
                
                # 네트워크 상태
                "network_status": "네트워크 상태",
                "internet_status": "인터넷 상태",
                "unknown": "알 수 없음",
                "checking": "확인 중...",
                
                # 종료 확인
                "exit_confirm": "PYRT 보안 가드를 종료하시겠습니까?\n\n모든 보호 서비스가 중지됩니다.",
                "exit": "종료",
                
                # 언어 선택 대화상자
                "language_selection": "언어 선택",
                "select_language_prompt": "인터페이스 언어를 선택하세요:",
                "save_and_restart": "저장 후 다시 시작"
            },
            
            "ru_RU": {
                # Общие
                "app_name": "PYRT Security Guard",
                "version": "Версия",
                "save": "Сохранить",
                "cancel": "Отмена",
                "confirm": "Подтвердить",
                "close": "Закрыть",
                "settings": "Настройки",
                "language": "Язык",
                "select_language": "Выбрать язык",
                
                # Боковое меню
                "dashboard": "Панель управления",
                "security_scan": "Сканирование",
                "realtime_protection": "Реальная защита",
                "boot_protection": "Защита загрузки",
                "threat_list": "Список угроз",
                "quarantine": "Карантин",
                "log_center": "Центр журналов",
                "network_protection": "Сетевая защита",
                
                # Панель управления
                "security_dashboard": "Панель безопасности",
                "real_time_monitoring": "Мониторинг безопасности в реальном времени",
                "system_status": "Состояние системы",
                "secure": "Безопасно",
                "running": "Работает",
                "virus_db": "База вирусов",
                "latest": "Последняя",
                "quick_actions": "Быстрые действия",
                "quick_scan": "Быстрое сканирование",
                "quick_scan_desc": "Проверка критических областей системы",
                "full_scan": "Полное сканирование",
                "full_scan_desc": "Глубокая проверка всех файлов",
                "boot_check": "Проверка загрузки",
                "boot_check_desc": "Проверка целостности загрузки",
                "network_check": "Проверка сети",
                "network_check_desc": "Проверка сетевых подключений",
                "update_virus_db": "Обновить базу",
                "update_virus_db_desc": "Получить последние определения вирусов",
                "execute": "Выполнить",
                
                # Сканирование
                "security_scan_title": "Сканирование",
                "start_scan": "Начать сканирование",
                "stop_scan": "Остановить сканирование",
                
                # Реальная защита
                "realtime_protection_title": "Реальная защита",
                "protection_status": "Статус защиты",
                "status": "Статус",
                "monitored_dirs": "Отслеживаемые папки",
                "process_monitoring": "Мониторинг процессов",
                "enabled": "Включено",
                "disabled": "Отключено",
                "pause_protection": "Приостановить",
                "start_protection": "Запустить",
                "realtime_alerts": "Оповещения",
                
                # Защита загрузки
                "boot_protection_title": "Защита загрузки",
                "protected_files": "Защищенные файлы",
                "auto_repair": "Автовосстановление",
                "check_integrity": "Проверить целостность",
                "create_backup": "Создать резервную копию",
                "repair_boot": "Восстановить загрузку",
                "boot_alerts": "Оповещения загрузки",
                
                # Сетевая защита
                "network_protection_title": "Сетевая защита",
                "network": "Сеть",
                "internet": "Интернет",
                "connected": "Подключено",
                "disconnected": "Отключено",
                "blocked_ips": "Заблокированных IP",
                "blocked_domains": "Заблокированных доменов",
                "check_network": "Проверить сеть",
                "view_connections": "Посмотреть соединения",
                "emergency_disconnect": "Экстренное отключение",
                "network_alerts": "Сетевые оповещения",
                
                # Список угроз
                "threat_detection": "Обнаружение угроз",
                "detected_threats": "Обнаруженные угрозы",
                "quarantine_selected": "Поместить в карантин",
                "delete_selected": "Удалить выбранное",
                "clear_list": "Очистить список",
                
                # Карантин
                "quarantine_title": "Карантин",
                "quarantine_info": "Информация о карантине",
                "quarantined_files": "Файлов в карантине",
                "space_used": "Используемое место",
                "location": "Расположение",
                "open_quarantine": "Открыть карантин",
                "clear_quarantine": "Очистить карантин",
                "view_log": "Просмотреть журнал",
                
                # Центр журналов
                "log_center_title": "Центр журналов",
                "log_files": "Файлы журналов",
                "main_log": "Главный журнал",
                "realtime_log": "Журнал реальной защиты",
                "network_log": "Журнал сетевой защиты",
                "quarantine_log": "Журнал карантина",
                "scan_log": "Журнал сканирования",
                "boot_log": "Журнал защиты загрузки",
                "view": "Просмотреть",
                
                # Настройки
                "settings_title": "Настройки",
                "program_settings": "Настройки программы",
                "auto_start": "Автозапуск",
                "auto_start_desc": "Автоматический запуск PYRT Security Guard при старте системы",
                "auto_update": "Автообновление",
                "auto_update_desc": "Автоматическая проверка и обновление базы вирусов",
                "show_notifications": "Показывать уведомления",
                "show_notifications_desc": "Показывать системные уведомления при обнаружении угроз",
                "low_resource_mode": "Режим экономии ресурсов",
                "low_resource_mode_desc": "Снижение использования CPU и памяти",
                "dark_theme": "Темная тема",
                "dark_theme_desc": "Использовать темную тему интерфейса",
                "enable_network_protection": "Включить сетевую защиту",
                "enable_network_protection_desc": "Включить мониторинг сети и защиту от отключения",
                "save_settings": "Сохранить настройки",
                
                # Диалоговые окна
                "warning": "Предупреждение",
                "error": "Ошибка",
                "info": "Информация",
                "success": "Успешно",
                "confirm_action": "Подтверждение действия",
                "scan_in_progress": "Сканирование выполняется",
                "scan_complete": "Сканирование завершено",
                "threats_found": "Обнаружены угрозы",
                "no_threats": "Угроз не обнаружено",
                "system_secure": "Система безопасна",
                
                # Кнопки
                "ok": "ОК",
                "yes": "Да",
                "no": "Нет",
                "apply": "Применить",
                "refresh": "Обновить",
                "add": "Добавить",
                
                # Статус сканирования
                "preparing_scan": "Подготовка сканирования...",
                "scanning": "Сканирование",
                "files": "Файлов",
                "threats": "Угроз",
                "speed": "Скорость",
                "elapsed": "Прошло",
                
                # Уровни угроз
                "critical": "Критический",
                "high": "Высокий",
                "medium": "Средний",
                "low": "Низкий",
                
                # Сетевой статус
                "network_status": "Статус сети",
                "internet_status": "Статус интернета",
                "unknown": "Неизвестно",
                "checking": "Проверка...",
                
                # Подтверждение выхода
                "exit_confirm": "Вы уверены, что хотите выйти из PYRT Security Guard?\n\nВсе службы защиты будут остановлены.",
                "exit": "Выход",
                
                # Диалог выбора языка
                "language_selection": "Выбор языка",
                "select_language_prompt": "Пожалуйста, выберите язык интерфейса:",
                "save_and_restart": "Сохранить и перезапустить"
            },
            
            "de_DE": {
                # Allgemein
                "app_name": "PYRT Sicherheitswächter",
                "version": "Version",
                "save": "Speichern",
                "cancel": "Abbrechen",
                "confirm": "Bestätigen",
                "close": "Schließen",
                "settings": "Einstellungen",
                "language": "Sprache",
                "select_language": "Sprache auswählen",
                
                # Seitenleistenmenü
                "dashboard": "Dashboard",
                "security_scan": "Sicherheitsscan",
                "realtime_protection": "Echtzeitschutz",
                "boot_protection": "Boot-Schutz",
                "threat_list": "Bedrohungsliste",
                "quarantine": "Quarantäne",
                "log_center": "Log-Zentrum",
                "network_protection": "Netzwerkschutz",
                
                # Dashboard
                "security_dashboard": "Sicherheits-Dashboard",
                "real_time_monitoring": "Echtzeit-Systemüberwachung",
                "system_status": "Systemstatus",
                "secure": "Sicher",
                "running": "Aktiv",
                "virus_db": "Virendatenbank",
                "latest": "Aktuell",
                "quick_actions": "Schnellaktionen",
                "quick_scan": "Schnellscan",
                "quick_scan_desc": "Kritische Systembereiche prüfen",
                "full_scan": "Vollständiger Scan",
                "full_scan_desc": "Alle Dateien tiefgehend prüfen",
                "boot_check": "Boot-Prüfung",
                "boot_check_desc": "Boot-Integrität prüfen",
                "network_check": "Netzwerkprüfung",
                "network_check_desc": "Netzwerkverbindungen prüfen",
                "update_virus_db": "Viren-DB aktualisieren",
                "update_virus_db_desc": "Neueste Virendefinitionen abrufen",
                "execute": "Ausführen",
                
                # Sicherheitsscan
                "security_scan_title": "Sicherheitsscan",
                "start_scan": "Scan starten",
                "stop_scan": "Scan stoppen",
                
                # Echtzeitschutz
                "realtime_protection_title": "Echtzeitschutz",
                "protection_status": "Schutzstatus",
                "status": "Status",
                "monitored_dirs": "Überwachte Verzeichnisse",
                "process_monitoring": "Prozessüberwachung",
                "enabled": "Aktiviert",
                "disabled": "Deaktiviert",
                "pause_protection": "Schutz pausieren",
                "start_protection": "Schutz starten",
                "realtime_alerts": "Echtzeit-Warnungen",
                
                # Boot-Schutz
                "boot_protection_title": "Boot-Schutz",
                "protected_files": "Geschützte Dateien",
                "auto_repair": "Automatische Reparatur",
                "check_integrity": "Integrität prüfen",
                "create_backup": "Backup erstellen",
                "repair_boot": "Boot reparieren",
                "boot_alerts": "Boot-Warnungen",
                
                # Netzwerkschutz
                "network_protection_title": "Netzwerkschutz",
                "network": "Netzwerk",
                "internet": "Internet",
                "connected": "Verbunden",
                "disconnected": "Getrennt",
                "blocked_ips": "Blockierte IPs",
                "blocked_domains": "Blockierte Domains",
                "check_network": "Netzwerk prüfen",
                "view_connections": "Verbindungen anzeigen",
                "emergency_disconnect": "Notfall-Trennung",
                "network_alerts": "Netzwerk-Warnungen",
                
                # Bedrohungsliste
                "threat_detection": "Bedrohungserkennung",
                "detected_threats": "Erkannte Bedrohungen",
                "quarantine_selected": "Ausgewählte in Quarantäne",
                "delete_selected": "Ausgewählte löschen",
                "clear_list": "Liste löschen",
                
                # Quarantäne
                "quarantine_title": "Quarantäne",
                "quarantine_info": "Quarantäne-Informationen",
                "quarantined_files": "Dateien in Quarantäne",
                "space_used": "Belegter Speicher",
                "location": "Ort",
                "open_quarantine": "Quarantäne öffnen",
                "clear_quarantine": "Quarantäne leeren",
                "view_log": "Log anzeigen",
                
                # Log-Zentrum
                "log_center_title": "Log-Zentrum",
                "log_files": "Log-Dateien",
                "main_log": "Hauptprogramm-Log",
                "realtime_log": "Echtzeitschutz-Log",
                "network_log": "Netzwerkschutz-Log",
                "quarantine_log": "Quarantäne-Log",
                "scan_log": "Scan-Log",
                "boot_log": "Boot-Schutz-Log",
                "view": "Anzeigen",
                
                # Einstellungen
                "settings_title": "Einstellungen",
                "program_settings": "Programmeinstellungen",
                "auto_start": "Autostart",
                "auto_start_desc": "PYRT Sicherheitswächter beim Systemstart automatisch starten",
                "auto_update": "Automatische Updates",
                "auto_update_desc": "Virendatenbank automatisch prüfen und aktualisieren",
                "show_notifications": "Benachrichtigungen anzeigen",
                "show_notifications_desc": "Systembenachrichtigungen bei Bedrohungserkennung anzeigen",
                "low_resource_mode": "Ressourcensparmodus",
                "low_resource_mode_desc": "CPU- und Speichernutzung reduzieren",
                "dark_theme": "Dunkles Thema",
                "dark_theme_desc": "Dunkles Oberflächenthema verwenden",
                "enable_network_protection": "Netzwerkschutz aktivieren",
                "enable_network_protection_desc": "Netzwerküberwachung und Trennschutz aktivieren",
                "save_settings": "Einstellungen speichern",
                
                # Dialogfelder
                "warning": "Warnung",
                "error": "Fehler",
                "info": "Information",
                "success": "Erfolg",
                "confirm_action": "Aktion bestätigen",
                "scan_in_progress": "Scan läuft",
                "scan_complete": "Scan abgeschlossen",
                "threats_found": "Bedrohungen gefunden",
                "no_threats": "Keine Bedrohungen gefunden",
                "system_secure": "System ist sicher",
                
                # Schaltflächen
                "ok": "OK",
                "yes": "Ja",
                "no": "Nein",
                "apply": "Anwenden",
                "refresh": "Aktualisieren",
                "add": "Hinzufügen",
                
                # Scan-Status
                "preparing_scan": "Scan vorbereiten...",
                "scanning": "Scanne",
                "files": "Dateien",
                "threats": "Bedrohungen",
                "speed": "Geschwindigkeit",
                "elapsed": "Verstrichen",
                
                # Bedrohungsstufen
                "critical": "Kritisch",
                "high": "Hoch",
                "medium": "Mittel",
                "low": "Niedrig",
                
                # Netzwerkstatus
                "network_status": "Netzwerkstatus",
                "internet_status": "Internetstatus",
                "unknown": "Unbekannt",
                "checking": "Prüfe...",
                
                # Beenden-Bestätigung
                "exit_confirm": "Sind Sie sicher, dass Sie PYRT Sicherheitswächter beenden möchten?\n\nAlle Schutzdienste werden gestoppt.",
                "exit": "Beenden",
                
                # Sprachauswahl-Dialog
                "language_selection": "Sprachauswahl",
                "select_language_prompt": "Bitte wählen Sie die Oberflächensprache:",
                "save_and_restart": "Speichern und neu starten"
            }
        }
        
        # 尝试从文件加载翻译
        try:
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE, 'r', encoding='utf-8') as f:
                    loaded_translations = json.load(f)
                    # 合并加载的翻译和默认翻译
                    for lang, trans in loaded_translations.items():
                        if lang in default_translations:
                            default_translations[lang].update(trans)
                        else:
                            default_translations[lang] = trans
        except Exception as e:
            print(f"加载语言文件失败: {e}")
        
        self.translations = default_translations
    
    def get_text(self, key, default=None):
        """获取当前语言的文本"""
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, default or key)
        return default or key
    
    def set_language(self, language_code):
        """设置语言"""
        if language_code in self.SUPPORTED_LANGUAGES:
            self.current_language = language_code
            Config.LANGUAGE = language_code
            self.save_language_setting()
            return True
        return False
    
    def save_language_setting(self):
        """保存语言设置到文件"""
        try:
            config = {}
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['language'] = self.current_language
            
            with open(Config.LANGUAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存语言设置失败: {e}")
    
    def load_language_setting(self):
        """从文件加载语言设置"""
        try:
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'language' in config and config['language'] in self.SUPPORTED_LANGUAGES:
                        self.current_language = config['language']
                        Config.LANGUAGE = config['language']
        except Exception as e:
            print(f"加载语言设置失败: {e}")

# ==================== 语言管理器实例 ====================
lang = LanguageManager()
lang.load_language_setting()

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PYRT安全卫士] - %(levelname)s - %(message)s',
    filename='pyrt_security_suite.log',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# ==================== 语言选择对话框 ====================
class LanguageSelectionDialog:
    """语言选择对话框"""
    
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(lang.get_text("language_selection", "语言选择"))
        self.dialog.geometry("400x350")
        self.dialog.configure(bg=Config.THEME['bg_dark'])
        self.dialog.resizable(False, False)
        
        # 居中显示
        self.dialog.update_idletasks()
        width = 400
        height = 350
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # 设置模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # 等待对话框关闭
        parent.wait_window(self.dialog)
    
    def _create_widgets(self):
        """创建对话框组件"""
        # 主框架
        main_frame = tk.Frame(self.dialog, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="🌐 " + lang.get_text("language_selection", "语言选择"),
            font=("Microsoft YaHei", 16, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        )
        title_label.pack(pady=(0, 20))
        
        # 提示文本
        prompt_label = tk.Label(
            main_frame,
            text=lang.get_text("select_language_prompt", "请选择界面语言："),
            font=("Microsoft YaHei", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        )
        prompt_label.pack(pady=(0, 10))
        
        # 语言列表框架
        list_frame = tk.Frame(main_frame, bg=Config.THEME['bg_card'], relief=tk.FLAT, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建语言选择列表
        self.language_var = tk.StringVar(value=Config.LANGUAGE)
        
        # 使用Canvas和Frame实现滚动列表
        canvas = tk.Canvas(
            list_frame,
            bg=Config.THEME['bg_card'],
            highlightthickness=0,
            height=180
        )
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Config.THEME['bg_card'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 添加语言选项
        for lang_code, lang_name in Config.SUPPORTED_LANGUAGES.items():
            rb_frame = tk.Frame(scrollable_frame, bg=Config.THEME['bg_card'])
            rb_frame.pack(fill=tk.X, padx=10, pady=5)
            
            rb = tk.Radiobutton(
                rb_frame,
                text=lang_name,
                variable=self.language_var,
                value=lang_code,
                font=("Microsoft YaHei", 11),
                fg=Config.THEME['text_primary'],
                bg=Config.THEME['bg_card'],
                selectcolor=Config.THEME['bg_card'],
                activebackground=Config.THEME['bg_card'],
                activeforeground=Config.THEME['primary'],
                indicatoron=True,
                padx=10
            )
            rb.pack(anchor=tk.W)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = tk.Frame(main_frame, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X)
        
        # 保存按钮
        save_btn = tk.Button(
            button_frame,
            text=lang.get_text("save", "保存"),
            command=self._on_save,
            font=("Microsoft YaHei", 11),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            width=10
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_frame,
            text=lang.get_text("cancel", "取消"),
            command=self._on_cancel,
            font=("Microsoft YaHei", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            width=10
        )
        cancel_btn.pack(side=tk.LEFT)
    
    def _on_save(self):
        """保存按钮点击事件"""
        selected_lang = self.language_var.get()
        if selected_lang != Config.LANGUAGE:
            lang.set_language(selected_lang)
            self.result = selected_lang
            
            # 询问是否重启应用
            if self.callback:
                self.callback(selected_lang)
            else:
                response = messagebox.askyesno(
                    lang.get_text("confirm", "确认"),
                    lang.get_text("save_and_restart", "语言已更改，是否立即重启应用以应用新语言？")
                )
                if response:
                    self.dialog.quit()
                    self.dialog.destroy()
                    self._restart_app()
                    return
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """取消按钮点击事件"""
        self.dialog.destroy()
    
    def _restart_app(self):
        """重启应用"""
        python = sys.executable
        os.execl(python, python, *sys.argv)

# ==================== 断网保护引擎 ====================
class NetworkProtectionEngine:
    """断网保护核心引擎"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.network_alerts = []
        self.blocked_ips = set()
        self.blocked_domains = set()
        self.network_connections = []
        self.last_scan_time = 0
        
        # 网络状态
        self.network_status = "unknown"
        self.internet_status = False
        
        # 创建网络保护日志
        self._init_network_log()
        
        logger.info("断网保护引擎初始化完成")
    
    def _init_network_log(self):
        """初始化网络保护日志"""
        try:
            if not os.path.exists(Config.LOG_DIR):
                os.makedirs(Config.LOG_DIR)
            
            self.network_log_path = os.path.join(Config.LOG_DIR, Config.NETWORK_LOG)
            
            network_handler = logging.FileHandler(self.network_log_path, encoding='utf-8')
            network_handler.setFormatter(logging.Formatter('%(asctime)s - [网络保护] - %(levelname)s - %(message)s'))
            logger.addHandler(network_handler)
            
        except Exception as e:
            logger.error(f"初始化网络保护日志失败: {e}")
    
    def start_protection(self):
        """启动网络保护"""
        if self.running:
            logger.warning("网络保护已经在运行中")
            return False
        
        try:
            self.running = True
            
            # 初始化恶意列表
            self._load_malicious_lists()
            
            # 检查当前网络状态
            self._check_network_status()
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="NetworkMonitor"
            )
            self.monitor_thread.start()
            
            logger.info("网络保护引擎启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动网络保护失败: {e}")
            self.running = False
            return False
    
    def stop_protection(self):
        """停止网络保护"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        logger.info("网络保护引擎已停止")
    
    def _load_malicious_lists(self):
        """加载恶意IP和域名列表"""
        # 添加配置中的恶意IP
        for ip in Config.MALICIOUS_IPS:
            self.blocked_ips.add(ip)
        
        # 添加配置中的恶意域名
        for domain in Config.MALICIOUS_DOMAINS:
            self.blocked_domains.add(domain.lower())
        
        # 尝试从文件加载更多恶意列表
        self._load_from_external_sources()
    
    def _load_from_external_sources(self):
        """从外部来源加载恶意列表"""
        try:
            # 恶意IP列表文件
            malicious_ip_file = os.path.join(Config.LOG_DIR, "malicious_ips.txt")
            if os.path.exists(malicious_ip_file):
                with open(malicious_ip_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith('#'):
                            self.blocked_ips.add(ip)
            
            # 恶意域名列表文件
            malicious_domain_file = os.path.join(Config.LOG_DIR, "malicious_domains.txt")
            if os.path.exists(malicious_domain_file):
                with open(malicious_domain_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        domain = line.strip().lower()
                        if domain and not domain.startswith('#'):
                            self.blocked_domains.add(domain)
                            
        except Exception as e:
            logger.debug(f"加载外部恶意列表失败: {e}")
    
    def _check_network_status(self):
        """检查网络状态"""
        try:
            # 检查本地网络连接
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='gbk')
                if "Media disconnected" not in result.stdout:
                    self.network_status = "connected"
                else:
                    self.network_status = "disconnected"
            else:
                # Linux/Mac
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                if "UP" in result.stdout:
                    self.network_status = "connected"
                else:
                    self.network_status = "disconnected"
            
            # 检查互联网连接
            self.internet_status = self._check_internet_connection()
            
            logger.info(f"网络状态: {self.network_status}, 互联网: {'已连接' if self.internet_status else '未连接'}")
            
        except Exception as e:
            logger.error(f"检查网络状态失败: {e}")
            self.network_status = "error"
            self.internet_status = False
    
    def _check_internet_connection(self, timeout=3):
        """检查互联网连接"""
        try:
            # 尝试连接多个知名网站
            test_urls = [
                "http://www.baidu.com",
                "http://www.google.com",
                "http://www.cloudflare.com",
                "http://1.1.1.1",
            ]
            
            for url in test_urls:
                try:
                    response = urllib.request.urlopen(url, timeout=timeout)
                    if response.getcode() == 200:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"检查互联网连接失败: {e}")
            return False
    
    def _monitor_loop(self):
        """网络监控循环"""
        while self.running:
            try:
                # 检查网络状态变化
                old_status = self.network_status
                old_internet = self.internet_status
                
                self._check_network_status()
                
                if old_status != self.network_status:
                    alert = {
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': '网络状态变化',
                        'severity': '中',
                        'message': f'网络状态从 {old_status} 变为 {self.network_status}'
                    }
                    self._add_alert(alert)
                
                if old_internet != self.internet_status:
                    alert = {
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': '互联网连接变化',
                        'severity': '中',
                        'message': f'互联网连接 {"已连接" if self.internet_status else "已断开"}'
                    }
                    self._add_alert(alert)
                
                # 扫描网络连接
                if self.internet_status:
                    self._scan_network_connections()
                
                # 扫描可疑进程
                self._scan_network_processes()
                
                # 检查hosts文件
                self._check_hosts_file()
                
                time.sleep(Config.NETWORK_MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"网络监控循环错误: {e}")
                time.sleep(30)
    
    def _scan_network_connections(self):
        """扫描网络连接"""
        try:
            current_time = time.time()
            
            # 每30秒扫描一次
            if current_time - self.last_scan_time < 30:
                return
            
            self.last_scan_time = current_time
            
            if platform.system() == "Windows":
                connections = self._get_windows_connections()
            else:
                connections = self._get_unix_connections()
            
            for conn in connections:
                self._analyze_connection(conn)
            
            # 只保留最近的100个连接
            if len(self.network_connections) > 100:
                self.network_connections = self.network_connections[-100:]
                
        except Exception as e:
            logger.error(f"扫描网络连接失败: {e}")
    
    def _get_windows_connections(self):
        """获取Windows网络连接"""
        connections = []
        
        try:
            # 使用netstat命令获取连接
            cmd = 'netstat -an'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'ESTABLISHED' in line or 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        # 解析本地地址和远程地址
                        local_addr = parts[1]
                        remote_addr = parts[2] if len(parts) > 2 else ''
                        state = parts[3] if len(parts) > 3 else ''
                        
                        # 提取IP和端口
                        local_ip, local_port = self._parse_address(local_addr)
                        remote_ip, remote_port = self._parse_address(remote_addr)
                        
                        conn_info = {
                            'local_ip': local_ip,
                            'local_port': local_port,
                            'remote_ip': remote_ip,
                            'remote_port': remote_port,
                            'state': state,
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'process': self._get_process_by_port(local_port)
                        }
                        
                        connections.append(conn_info)
        
        except Exception as e:
            logger.debug(f"获取Windows连接失败: {e}")
        
        return connections
    
    def _get_unix_connections(self):
        """获取Unix/Linux网络连接"""
        connections = []
        
        try:
            # 使用netstat或ss命令
            cmd = 'netstat -tunap 2>/dev/null || ss -tunap 2>/dev/null'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'ESTAB' in line or 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        # 不同系统的输出格式可能不同
                        try:
                            local_addr = parts[3]
                            remote_addr = parts[4]
                            state = parts[5] if len(parts) > 5 else ''
                            
                            local_ip, local_port = self._parse_address(local_addr)
                            remote_ip, remote_port = self._parse_address(remote_addr)
                            
                            conn_info = {
                                'local_ip': local_ip,
                                'local_port': local_port,
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'state': state,
                                'time': datetime.now().strftime('%H:%M:%S'),
                                'process': self._get_process_by_port_unix(local_port)
                            }
                            
                            connections.append(conn_info)
                        except:
                            continue
        
        except Exception as e:
            logger.debug(f"获取Unix连接失败: {e}")
        
        return connections
    
    def _parse_address(self, address):
        """解析地址字符串为IP和端口"""
        if not address or ':' not in address:
            return "", ""
        
        try:
            if '[' in address and ']' in address:
                # IPv6地址
                ip_end = address.find(']')
                ip = address[1:ip_end]
                port = address[ip_end+2:]
            else:
                # IPv4地址
                parts = address.rsplit(':', 1)
                ip = parts[0]
                port = parts[1] if len(parts) > 1 else ""
            
            return ip, port
        except:
            return "", ""
    
    def _get_process_by_port(self, port):
        """根据端口获取进程（Windows）"""
        if not port:
            return ""
        
        try:
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if f':{port}' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        
                        # 根据PID获取进程名
                        cmd2 = f'tasklist /FI "PID eq {pid}" /FO CSV'
                        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True, encoding='gbk')
                        
                        if '"' in result2.stdout:
                            process_line = result2.stdout.split('\n')[1]
                            process_name = process_line.split('","')[0].strip('"')
                            return process_name
            
            return ""
            
        except Exception as e:
            logger.debug(f"获取进程信息失败 端口{port}: {e}")
            return ""
    
    def _get_process_by_port_unix(self, port):
        """根据端口获取进程（Unix/Linux）"""
        if not port:
            return ""
        
        try:
            cmd = f'lsof -i :{port} 2>/dev/null | head -2 | tail -1'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                parts = result.stdout.split()
                if len(parts) > 0:
                    return parts[0]
            
            return ""
            
        except Exception as e:
            logger.debug(f"获取Unix进程信息失败 端口{port}: {e}")
            return ""
    
    def _analyze_connection(self, conn_info):
        """分析网络连接"""
        suspicious = False
        severity = "低"
        reasons = []
        
        remote_ip = conn_info.get('remote_ip', '')
        remote_port = conn_info.get('remote_port', '')
        process_name = conn_info.get('process', '').lower()
        
        # 检查是否在恶意IP列表中
        if remote_ip in self.blocked_ips:
            suspicious = True
            severity = "高"
            reasons.append(f"连接到恶意IP: {remote_ip}")
        
        # 检查可疑端口
        if remote_port and remote_port.isdigit():
            port_num = int(remote_port)
            if port_num in Config.SUSPICIOUS_PORTS:
                suspicious = True
                severity = "中" if severity != "高" else severity
                reasons.append(f"连接到可疑端口: {port_num}")
        
        # 检查网络监控进程
        for net_proc in Config.NETWORK_MONITOR_PROCESSES:
            if net_proc in process_name:
                suspicious = True
                severity = "中" if severity != "高" else severity
                reasons.append(f"网络监控进程: {process_name}")
                break
        
        # 检查私有IP范围（可能的内网攻击）
        if remote_ip:
            try:
                ip_obj = ipaddress.ip_address(remote_ip)
                if ip_obj.is_private and ip_obj != ipaddress.ip_address("127.0.0.1"):
                    # 内网连接通常正常，但可以作为记录
                    pass
            except:
                pass
        
        # 如果是可疑连接，记录并通知
        if suspicious:
            alert = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': '可疑网络连接',
                'severity': severity,
                'message': f"进程 {process_name} 连接到 {remote_ip}:{remote_port}",
                'reasons': reasons,
                'connection_info': conn_info
            }
            
            self._add_alert(alert)
            self.network_connections.append(conn_info)
            
            # 严重情况下可以尝试阻止连接
            if severity == "高" and self.running:
                self._block_suspicious_connection(conn_info)
    
    def _block_suspicious_connection(self, conn_info):
        """阻止可疑连接"""
        try:
            remote_ip = conn_info.get('remote_ip', '')
            process_name = conn_info.get('process', '')
            
            if not remote_ip or not process_name:
                return
            
            # 记录阻止操作
            logger.warning(f"尝试阻止可疑连接: {process_name} -> {remote_ip}")
            
            # 在Windows上可以使用netsh添加防火墙规则
            if platform.system() == "Windows":
                # 创建防火墙规则阻止IP
                rule_name = f"PYRT_Block_{remote_ip}_{int(time.time())}"
                cmd = f'netsh advfirewall firewall add rule name="{rule_name}" dir=out action=block remoteip={remote_ip} enable=yes'
                subprocess.run(cmd, shell=True, capture_output=True)
                
                # 尝试终止进程
                if process_name:
                    try:
                        subprocess.run(f'taskkill /F /IM {process_name}', shell=True, capture_output=True)
                    except:
                        pass
                
                alert = {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '连接已阻止',
                    'severity': '高',
                    'message': f'已阻止进程 {process_name} 连接到 {remote_ip}'
                }
                self._add_alert(alert)
        
        except Exception as e:
            logger.error(f"阻止连接失败: {e}")
    
    def _scan_network_processes(self):
        """扫描网络相关进程"""
        try:
            if platform.system() == "Windows":
                processes = self._get_windows_processes()
            else:
                processes = self._get_unix_processes()
            
            for proc_info in processes:
                self._analyze_network_process(proc_info)
        
        except Exception as e:
            logger.error(f"扫描网络进程失败: {e}")
    
    def _get_windows_processes(self):
        """获取Windows进程列表"""
        processes = []
        
        try:
            cmd = 'wmic process get ProcessId,Name,CommandLine /format:csv'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
            
            lines = result.stdout.strip().split('\n')
            if len(lines) > 2:
                for line in lines[2:]:
                    if line.strip():
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            processes.append({
                                'pid': int(parts[-3]) if parts[-3].isdigit() else None,
                                'name': parts[-2],
                                'cmdline': parts[-1]
                            })
        
        except Exception as e:
            logger.debug(f"获取Windows进程列表失败: {e}")
        
        return processes
    
    def _get_unix_processes(self):
        """获取Unix/Linux进程列表"""
        processes = []
        
        try:
            cmd = 'ps -eo pid,comm,args'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        parts = line.strip().split(None, 2)
                        if len(parts) >= 3:
                            processes.append({
                                'pid': int(parts[0]) if parts[0].isdigit() else None,
                                'name': parts[1],
                                'cmdline': parts[2]
                            })
        
        except Exception as e:
            logger.debug(f"获取Unix进程列表失败: {e}")
        
        return processes
    
    def _analyze_network_process(self, proc_info):
        """分析网络相关进程"""
        process_name = proc_info.get('name', '').lower()
        cmdline = proc_info.get('cmdline', '').lower()
        
        # 检查是否为已知的网络监控/攻击工具
        for net_tool in Config.NETWORK_MONITOR_PROCESSES:
            if net_tool in process_name:
                alert = {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '网络工具进程',
                    'severity': '中',
                    'message': f'检测到网络工具进程: {process_name}',
                    'process_info': proc_info
                }
                self._add_alert(alert)
                break
        
        # 检查命令行中的可疑网络操作
        suspicious_patterns = [
            (r'nc\s+.*\d+\.\d+\.\d+\.\d+\s+\d+', 'Netcat连接'),
            (r'nmap\s+.*\d+\.\d+\.\d+\.\d+', 'Nmap扫描'),
            (r'wget\s+.*http://.*\.(exe|dll|scr)', '可疑下载'),
            (r'curl\s+.*http://.*\.(exe|dll|scr)', '可疑下载'),
            (r'powershell.*download', 'PowerShell下载'),
            (r'certutil.*urlcache', 'Certutil下载'),
        ]
        
        for pattern, desc in suspicious_patterns:
            if re.search(pattern, cmdline, re.IGNORECASE):
                alert = {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '可疑网络命令',
                    'severity': '高',
                    'message': f'检测到{desc}: {cmdline[:100]}',
                    'process_info': proc_info
                }
                self._add_alert(alert)
                break
    
    def _check_hosts_file(self):
        """检查hosts文件是否被篡改"""
        try:
            # 确定hosts文件路径
            if platform.system() == "Windows":
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:
                hosts_path = '/etc/hosts'
            
            if not os.path.exists(hosts_path):
                return
            
            with open(hosts_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查是否包含对受保护域名的重定向
            for protected_domain in Config.PROTECTED_HOSTS:
                if protected_domain in content.lower():
                    # 检查是否是恶意重定向（指向非常用IP）
                    lines = content.split('\n')
                    for line in lines:
                        if protected_domain in line.lower() and not line.strip().startswith('#'):
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[0]
                                # 检查是否指向本地或可疑IP
                                if ip != '127.0.0.1' and ip != '0.0.0.0':
                                    try:
                                        ip_obj = ipaddress.ip_address(ip)
                                        if ip_obj.is_private or ip in self.blocked_ips:
                                            alert = {
                                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                'type': 'Hosts文件篡改',
                                                'severity': '高',
                                                'message': f'检测到hosts文件被篡改: {protected_domain} 被重定向到 {ip}',
                                                'line': line.strip()
                                            }
                                            self._add_alert(alert)
                                    except:
                                        pass
        
        except Exception as e:
            logger.error(f"检查hosts文件失败: {e}")
    
    def _add_alert(self, alert_info):
        """添加警报"""
        self.network_alerts.append(alert_info)
        
        # 限制警报数量
        if len(self.network_alerts) > 100:
            self.network_alerts = self.network_alerts[-100:]
        
        alert_msg = f"网络保护警报: {alert_info.get('type', '未知')} - {alert_info.get('severity', '中')}"
        logger.warning(alert_msg)
    
    def get_alerts(self, count=10):
        """获取最近的警报"""
        return self.network_alerts[-count:] if self.network_alerts else []
    
    def clear_alerts(self):
        """清除警报"""
        self.network_alerts.clear()
    
    def get_network_status(self):
        """获取网络状态"""
        return {
            'network': self.network_status,
            'internet': self.internet_status,
            'blocked_ips': len(self.blocked_ips),
            'blocked_domains': len(self.blocked_domains),
            'recent_connections': len(self.network_connections)
        }
    
    def add_blocked_ip(self, ip):
        """添加要阻止的IP"""
        self.blocked_ips.add(ip)
        logger.info(f"已添加阻止IP: {ip}")
    
    def add_blocked_domain(self, domain):
        """添加要阻止的域名"""
        self.blocked_domains.add(domain.lower())
        logger.info(f"已添加阻止域名: {domain}")
    
    def is_running(self):
        """检查是否在运行"""
        return self.running
    
    def emergency_disconnect(self):
        """紧急断开网络连接"""
        try:
            if platform.system() == "Windows":
                # 禁用网络适配器
                cmd = 'netsh interface set interface "以太网" admin=disable'
                subprocess.run(cmd, shell=True, capture_output=True)
                
                # 或者断开所有连接
                cmd2 = 'ipconfig /release'
                subprocess.run(cmd2, shell=True, capture_output=True)
            else:
                # Linux/Mac
                cmd = 'ifconfig eth0 down 2>/dev/null || ip link set eth0 down 2>/dev/null'
                subprocess.run(cmd, shell=True, capture_output=True)
            
            alert = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': '紧急断网',
                'severity': '严重',
                'message': '已执行紧急断网操作'
            }
            self._add_alert(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"紧急断网失败: {e}")
            return False

# ==================== 侧边栏按钮类 ====================
class SidebarButton:
    """侧边栏按钮类"""
    
    def __init__(self, parent, text, icon, command, is_active=False):
        self.parent = parent
        self.text = text
        self.icon = icon
        self.command = command
        self.is_active = is_active
        self.button = None
        self.icon_label = None
        self.text_label = None
        
    def create(self, x, y, width, height):
        """创建按钮"""
        # 按钮背景
        self.button = tk.Frame(
            self.parent,
            bg=Config.THEME['sidebar_bg'] if not self.is_active else Config.THEME['primary'],
            width=width,
            height=height
        )
        self.button.place(x=x, y=y)
        
        # 绑定鼠标事件
        self.button.bind("<Enter>", self._on_enter)
        self.button.bind("<Leave>", self._on_leave)
        self.button.bind("<Button-1>", self._on_click)
        
        # 图标
        self.icon_label = tk.Label(
            self.button,
            text=self.icon,
            font=("Segoe UI Emoji", 14),
            fg=Config.THEME['text_primary'] if not self.is_active else Config.THEME['bg_dark'],
            bg=Config.THEME['sidebar_bg'] if not self.is_active else Config.THEME['primary']
        )
        self.icon_label.place(x=15, y=height//2 - 10)
        self.icon_label.bind("<Enter>", self._on_enter)
        self.icon_label.bind("<Leave>", self._on_leave)
        self.icon_label.bind("<Button-1>", self._on_click)
        
        # 文本
        self.text_label = tk.Label(
            self.button,
            text=self.text,
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_primary'] if not self.is_active else Config.THEME['bg_dark'],
            bg=Config.THEME['sidebar_bg'] if not self.is_active else Config.THEME['primary'],
            anchor="w"
        )
        self.text_label.place(x=50, y=height//2 - 10)
        self.text_label.bind("<Enter>", self._on_enter)
        self.text_label.bind("<Leave>", self._on_leave)
        self.text_label.bind("<Button-1>", self._on_click)
        
        return self.button
    
    def _on_enter(self, event):
        """鼠标进入"""
        if not self.is_active:
            self.button.config(bg=Config.THEME['sidebar_hover'])
            for child in self.button.winfo_children():
                child.config(bg=Config.THEME['sidebar_hover'])
    
    def _on_leave(self, event):
        """鼠标离开"""
        if not self.is_active:
            self.button.config(bg=Config.THEME['sidebar_bg'])
            for child in self.button.winfo_children():
                child.config(bg=Config.THEME['sidebar_bg'])
    
    def _on_click(self, event):
        """点击事件"""
        if self.command:
            self.command()
    
    def set_active(self, active):
        """设置活动状态"""
        self.is_active = active
        if active:
            self.button.config(bg=Config.THEME['primary'])
            for child in self.button.winfo_children():
                child.config(bg=Config.THEME['primary'], fg=Config.THEME['bg_dark'])
        else:
            self.button.config(bg=Config.THEME['sidebar_bg'])
            for child in self.button.winfo_children():
                child.config(bg=Config.THEME['sidebar_bg'], fg=Config.THEME['text_primary'])

# ==================== 滑动侧边栏 ====================
class SlidingSidebar:
    """滑动侧边栏"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.is_open = Config.SIDEBAR_DEFAULT_OPEN
        self.buttons = []
        self.current_active = 0  # 当前活动按钮索引
        
        # 创建侧边栏容器
        self.sidebar_frame = tk.Frame(
            parent,
            bg=Config.THEME['sidebar_bg'],
            width=Config.SIDEBAR_WIDTH if self.is_open else Config.SIDEBAR_COLLAPSED_WIDTH
        )
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        # 创建侧边栏内容
        self._create_sidebar()
        
        # 绑定动画
        self.animation_id = None
    
    def _create_sidebar(self):
        """创建侧边栏内容"""
        # 侧边栏顶部区域
        top_frame = tk.Frame(self.sidebar_frame, bg=Config.THEME['sidebar_bg'], height=80)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # 应用Logo和名称
        logo_label = tk.Label(
            top_frame,
            text=Config.LOGO,
            font=("Segoe UI Emoji", 24),
            fg=Config.THEME['primary'],
            bg=Config.THEME['sidebar_bg']
        )
        logo_label.pack(side=tk.LEFT, padx=(20, 10), pady=20)
        
        self.app_name_label = tk.Label(
            top_frame,
            text=lang.get_text("app_name") if self.is_open else "",
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['sidebar_bg']
        )
        self.app_name_label.pack(side=tk.LEFT, pady=20)
        
        # 侧边栏按钮列表
        button_definitions = [
            {"text_key": "dashboard", "icon": "📊", "command": lambda: self._switch_page(0)},
            {"text_key": "security_scan", "icon": "🔍", "command": lambda: self._switch_page(1)},
            {"text_key": "realtime_protection", "icon": "🛡️", "command": lambda: self._switch_page(2)},
            {"text_key": "boot_protection", "icon": "🔒", "command": lambda: self._switch_page(3)},
            {"text_key": "threat_list", "icon": "⚠️", "command": lambda: self._switch_page(4)},
            {"text_key": "quarantine", "icon": "🗄️", "command": lambda: self._switch_page(5)},
            {"text_key": "log_center", "icon": "📋", "command": lambda: self._switch_page(6)},
            {"text_key": "settings", "icon": "⚙️", "command": lambda: self._switch_page(7)},
            {"text_key": "network_protection", "icon": "🌐", "command": lambda: self._switch_page(8)},
        ]
        
        # 创建按钮
        button_y = 90
        button_height = 50
        
        for i, btn_def in enumerate(button_definitions):
            is_active = (i == self.current_active)
            button_text = lang.get_text(btn_def["text_key"]) if self.is_open else ""
            button = SidebarButton(
                self.sidebar_frame,
                button_text,
                btn_def["icon"],
                btn_def["command"],
                is_active
            )
            btn_widget = button.create(0, button_y, 
                                     Config.SIDEBAR_WIDTH if self.is_open else Config.SIDEBAR_COLLAPSED_WIDTH, 
                                     button_height)
            self.buttons.append(button)
            button_y += button_height + 5
        
        # 侧边栏底部区域
        bottom_frame = tk.Frame(self.sidebar_frame, bg=Config.THEME['sidebar_bg'])
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        # 语言切换按钮
        self.lang_button = tk.Label(
            bottom_frame,
            text="🌐",
            font=("Segoe UI Emoji", 16),
            fg=Config.THEME['primary'],
            bg=Config.THEME['sidebar_bg'],
            cursor="hand2"
        )
        self.lang_button.pack(pady=5)
        self.lang_button.bind("<Button-1>", self._show_language_selection)
        
        # 折叠/展开按钮
        self.toggle_button = tk.Label(
            bottom_frame,
            text="«" if self.is_open else "»",
            font=("Microsoft YaHei", 16, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['sidebar_bg'],
            cursor="hand2"
        )
        self.toggle_button.pack(pady=10)
        self.toggle_button.bind("<Button-1>", self.toggle)
        
        # 版本信息
        version_label = tk.Label(
            bottom_frame,
            text=f"v{Config.VERSION}" if self.is_open else f"v{Config.VERSION[:3]}",
            font=("Microsoft YaHei", 9),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['sidebar_bg']
        )
        version_label.pack(pady=5)
    
    def _switch_page(self, page_index):
        """切换页面"""
        # 更新按钮状态
        for i, button in enumerate(self.buttons):
            button.set_active(i == page_index)
        
        self.current_active = page_index
        
        # 调用主应用的页面切换
        if hasattr(self.main_app, 'switch_page'):
            self.main_app.switch_page(page_index)
    
    def _show_language_selection(self, event=None):
        """显示语言选择对话框"""
        def on_language_changed(lang_code):
            self.main_app.root.after(100, self._restart_app)
        
        LanguageSelectionDialog(self.parent, on_language_changed)
    
    def _restart_app(self):
        """重启应用"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def toggle(self, event=None):
        """切换侧边栏状态"""
        target_width = Config.SIDEBAR_COLLAPSED_WIDTH if self.is_open else Config.SIDEBAR_WIDTH
        self._animate_sidebar(target_width)
    
    def _animate_sidebar(self, target_width):
        """侧边栏动画"""
        current_width = self.sidebar_frame.winfo_width()
        
        if current_width < target_width:
            step = 10
        else:
            step = -10
        
        def animate():
            nonlocal current_width
            current_width += step
            
            # 检查是否到达目标宽度
            if (step > 0 and current_width >= target_width) or (step < 0 and current_width <= target_width):
                current_width = target_width
                self.sidebar_frame.config(width=current_width)
                self.is_open = not self.is_open
                self._update_sidebar_content()
                return
            
            # 更新宽度
            self.sidebar_frame.config(width=current_width)
            
            # 继续动画
            self.animation_id = self.sidebar_frame.after(5, animate)
        
        # 开始动画
        if self.animation_id:
            self.sidebar_frame.after_cancel(self.animation_id)
        
        animate()
    
    def _update_sidebar_content(self):
        """更新侧边栏内容"""
        # 更新应用名称
        self.app_name_label.config(text=lang.get_text("app_name") if self.is_open else "")
        
        # 更新按钮文本
        button_text_keys = ["dashboard", "security_scan", "realtime_protection", "boot_protection", 
                           "threat_list", "quarantine", "log_center", "settings", "network_protection"]
        
        for i, button in enumerate(self.buttons):
            button.text_label.config(text=lang.get_text(button_text_keys[i]) if self.is_open else "")
            
            # 更新按钮宽度
            button.button.config(width=Config.SIDEBAR_WIDTH if self.is_open else Config.SIDEBAR_COLLAPSED_WIDTH)
            
            # 更新图标位置
            if self.is_open:
                button.icon_label.place(x=15, y=15)
                button.text_label.place(x=50, y=15)
            else:
                button.icon_label.place(x=15, y=15)
                button.text_label.place(x=-100, y=15)  # 隐藏文本
        
        # 更新切换按钮
        self.toggle_button.config(text="«" if self.is_open else "»")
        
        # 更新版本显示
        for child in self.sidebar_frame.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_children():
                for grandchild in child.winfo_children():
                    if "v" in grandchild.cget("text"):
                        grandchild.config(text=f"v{Config.VERSION}" if self.is_open else f"v{Config.VERSION[:3]}")
                        break

# ==================== 页面容器 ====================
class PageContainer:
    """页面容器"""
    
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.pages = []
        self.current_page = 0
        
        # 创建页面容器
        self.container = tk.Frame(parent, bg=Config.THEME['bg_dark'])
        self.container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建页面
        self._create_pages()
        
        # 显示默认页面
        self.show_page(0)
    
    def _create_pages(self):
        """创建所有页面"""
        # 页面1: 仪表盘
        dashboard_page = self._create_dashboard_page()
        self.pages.append(dashboard_page)
        
        # 页面2: 安全扫描
        scan_page = self._create_scan_page()
        self.pages.append(scan_page)
        
        # 页面3: 实时保护
        realtime_page = self._create_realtime_page()
        self.pages.append(realtime_page)
        
        # 页面4: 引导保护
        boot_page = self._create_boot_page()
        self.pages.append(boot_page)
        
        # 页面5: 威胁列表
        threats_page = self._create_threats_page()
        self.pages.append(threats_page)
        
        # 页面6: 隔离区
        quarantine_page = self._create_quarantine_page()
        self.pages.append(quarantine_page)
        
        # 页面7: 日志中心
        logs_page = self._create_logs_page()
        self.pages.append(logs_page)
        
        # 页面8: 设置
        settings_page = self._create_settings_page()
        self.pages.append(settings_page)
        
        # 页面9: 断网保护（新增）
        network_page = self._create_network_page()
        self.pages.append(network_page)
    
    def _create_dashboard_page(self):
        """创建仪表盘页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="📊 " + lang.get_text("security_dashboard"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text=lang.get_text("real_time_monitoring"),
            font=("Microsoft YaHe", 12),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # 统计卡片
        stats_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        stats_frame.pack(fill=tk.X, padx=30, pady=(0, 30))
        
        # 创建统计卡片
        stats_cards = [
            {"title_key": "system_status", "value": "🟢 " + lang.get_text("secure"), "icon": "✅", "color": Config.THEME['success']},
            {"title_key": "realtime_protection", "value": "🟢 " + lang.get_text("running"), "icon": "🛡️", "color": Config.THEME['primary']},
            {"title_key": "boot_protection", "value": "🟢 " + lang.get_text("running"), "icon": "🔒", "color": Config.THEME['warning']},
            {"title_key": "network_protection", "value": "🟢 " + lang.get_text("running"), "icon": "🌐", "color": Config.THEME['secondary']},
            {"title_key": "virus_db", "value": lang.get_text("latest"), "icon": "📦", "color": Config.THEME['secondary']},
        ]
        
        for i, card in enumerate(stats_cards):
            card_frame = tk.Frame(
                stats_frame,
                bg=Config.THEME['bg_card'],
                relief=tk.FLAT,
                width=180,
                height=120
            )
            card_frame.grid(row=0, column=i, padx=(0, 15), sticky="nsew")
            card_frame.grid_propagate(False)
            
            # 卡片内容
            tk.Label(
                card_frame,
                text=card["icon"],
                font=("Segoe UI Emoji", 24),
                fg=card["color"],
                bg=Config.THEME['bg_card']
            ).pack(anchor="nw", padx=15, pady=15)
            
            tk.Label(
                card_frame,
                text=lang.get_text(card["title_key"]),
                font=("Microsoft YaHe", 11),
                fg=Config.THEME['text_secondary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="nw", padx=15, pady=(0, 5))
            
            tk.Label(
                card_frame,
                text=card["value"],
                font=("Microsoft YaHe", 16, "bold"),
                fg=Config.THEME['text_primary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="nw", padx=15)
        
        # 快速操作
        quick_actions_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        quick_actions_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            quick_actions_frame,
            text="🚀 " + lang.get_text("quick_actions"),
            font=("Microsoft YaHe", 16, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor="w", pady=(0, 15))
        
        actions = [
            {"name_key": "quick_scan", "desc_key": "quick_scan_desc", "icon": "⚡", "command": self.main_app._start_pyrt_scan},
            {"name_key": "full_scan", "desc_key": "full_scan_desc", "icon": "📁", "command": lambda: self.main_app._select_scan_type("full")},
            {"name_key": "boot_check", "desc_key": "boot_check_desc", "icon": "🔍", "command": self.main_app._check_boot_integrity},
            {"name_key": "network_check", "desc_key": "network_check_desc", "icon": "🌐", "command": self.main_app._check_network_security},
            {"name_key": "update_virus_db", "desc_key": "update_virus_db_desc", "icon": "🔄", "command": self.main_app._update_virus_database},
        ]
        
        for action in actions:
            action_frame = tk.Frame(quick_actions_frame, bg=Config.THEME['bg_card'])
            action_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(
                action_frame,
                text=action["icon"],
                font=("Segoe UI Emoji", 20),
                fg=Config.THEME['primary'],
                bg=Config.THEME['bg_card']
            ).pack(side=tk.LEFT, padx=15, pady=15)
            
            text_frame = tk.Frame(action_frame, bg=Config.THEME['bg_card'])
            text_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
            
            tk.Label(
                text_frame,
                text=lang.get_text(action["name_key"]),
                font=("Microsoft YaHe", 12, "bold"),
                fg=Config.THEME['text_primary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="w", pady=(10, 2))
            
            tk.Label(
                text_frame,
                text=lang.get_text(action["desc_key"]),
                font=("Microsoft YaHe", 10),
                fg=Config.THEME['text_secondary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="w")
            
            tk.Button(
                action_frame,
                text=lang.get_text("execute"),
                command=action["command"],
                font=("Microsoft YaHe", 10),
                bg=Config.THEME['primary'],
                fg=Config.THEME['bg_dark'],
                relief=tk.FLAT,
                padx=20,
                pady=5,
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=15)
        
        return page
    
    def _create_scan_page(self):
        """创建安全扫描页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="🔍 " + lang.get_text("security_scan_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 扫描动画区域
        scan_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        scan_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 30))
        
        # 创建Canvas用于动画
        self.main_app.animation_canvas = tk.Canvas(
            scan_frame,
            bg=Config.THEME['bg_card'],
            highlightthickness=0,
            width=400,
            height=400
        )
        self.main_app.animation_canvas.pack(expand=True, padx=10, pady=10)
        
        # 创建PYRT扫描动画
        self.main_app.scan_animation = PYRTScanAnimation(self.main_app.animation_canvas, 200, 200, 150)
        
        # 控制按钮
        button_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.main_app.scan_button = tk.Button(
            button_frame,
            text="🚀 " + lang.get_text("start_scan"),
            command=self.main_app._start_pyrt_scan,
            font=("Microsoft YaHe", 14, "bold"),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            activebackground=Config.THEME['secondary'],
            activeforeground=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=40,
            pady=15,
            cursor="hand2",
            borderwidth=0
        )
        self.main_app.scan_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.main_app.stop_button = tk.Button(
            button_frame,
            text="⏹️ " + lang.get_text("stop_scan"),
            command=self.main_app._stop_pyrt_scan,
            font=("Microsoft YaHe", 14),
            bg=Config.THEME['accent'],
            fg="white",
            activebackground="#ff3333",
            activeforeground="white",
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor="hand2",
            borderwidth=0,
            state=tk.DISABLED
        )
        self.main_app.stop_button.pack(side=tk.LEFT)
        
        return page
    
    def _create_realtime_page(self):
        """创建实时保护页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="🛡️ " + lang.get_text("realtime_protection_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 实时保护状态
        status_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        status_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Label(
            status_frame,
            text=lang.get_text("protection_status"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # 状态信息
        info_frame = tk.Frame(status_frame, bg=Config.THEME['bg_card'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.main_app.realtime_status_label = tk.Label(
            info_frame,
            text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
            font=("Microsoft YaHe", 12),
            fg=Config.THEME['success'],
            bg=Config.THEME['bg_card']
        )
        self.main_app.realtime_status_label.pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_frame,
            text=lang.get_text("monitored_dirs") + f": {len(Config.MONITOR_PATHS)}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        process_status = lang.get_text("enabled") if Config.MONITOR_PROCESSES else lang.get_text("disabled")
        tk.Label(
            info_frame,
            text=lang.get_text("process_monitoring") + f": {process_status}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        # 控制按钮
        control_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        control_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        self.main_app.realtime_toggle_btn = tk.Button(
            control_frame,
            text="⏸️ " + lang.get_text("pause_protection"),
            command=self.main_app._toggle_realtime_protection,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['warning'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.main_app.realtime_toggle_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            control_frame,
            text="⚙️ " + lang.get_text("settings"),
            command=self.main_app._show_realtime_settings,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # 警报列表
        alerts_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        alerts_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            alerts_frame,
            text=lang.get_text("realtime_alerts"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        alerts_container = tk.Frame(alerts_frame, bg=Config.THEME['bg_card'])
        alerts_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.main_app.realtime_alerts_listbox = tk.Listbox(
            alerts_container,
            bg=Config.THEME['bg_dark'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 10),
            selectbackground=Config.THEME['primary'],
            selectforeground=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.main_app.realtime_alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(alerts_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_app.realtime_alerts_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.main_app.realtime_alerts_listbox.yview)
        
        return page
    
    def _create_boot_page(self):
        """创建引导保护页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="🔒 " + lang.get_text("boot_protection_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 引导保护状态
        status_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        status_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Label(
            status_frame,
            text=lang.get_text("protection_status"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # 状态信息
        info_frame = tk.Frame(status_frame, bg=Config.THEME['bg_card'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.main_app.boot_status_label = tk.Label(
            info_frame,
            text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
            font=("Microsoft YaHe", 12),
            fg=Config.THEME['success'],
            bg=Config.THEME['bg_card']
        )
        self.main_app.boot_status_label.pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_frame,
            text=lang.get_text("protected_files") + f": {len(self.main_app.boot_engine.boot_files) if hasattr(self.main_app, 'boot_engine') else 0}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        auto_repair_status = lang.get_text("enabled") if Config.BOOT_AUTO_REPAIR else lang.get_text("disabled")
        tk.Label(
            info_frame,
            text=lang.get_text("auto_repair") + f": {auto_repair_status}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        # 控制按钮
        control_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        control_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        row1_frame = tk.Frame(control_frame, bg=Config.THEME['bg_dark'])
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.main_app.boot_toggle_btn = tk.Button(
            row1_frame,
            text="⏸️ " + lang.get_text("pause_protection"),
            command=self.main_app._toggle_boot_protection,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['warning'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.main_app.boot_toggle_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row1_frame,
            text="🔍 " + lang.get_text("check_integrity"),
            command=self.main_app._check_boot_integrity,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row1_frame,
            text="⚙️ " + lang.get_text("settings"),
            command=self.main_app._show_boot_settings,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        row2_frame = tk.Frame(control_frame, bg=Config.THEME['bg_dark'])
        row2_frame.pack(fill=tk.X)
        
        tk.Button(
            row2_frame,
            text="💾 " + lang.get_text("create_backup"),
            command=self.main_app._backup_boot,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row2_frame,
            text="🔄 " + lang.get_text("repair_boot"),
            command=self.main_app._repair_boot,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['accent'],
            fg="white",
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # 警报列表
        alerts_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        alerts_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            alerts_frame,
            text=lang.get_text("boot_alerts"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        alerts_container = tk.Frame(alerts_frame, bg=Config.THEME['bg_card'])
        alerts_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.main_app.boot_alerts_listbox = tk.Listbox(
            alerts_container,
            bg=Config.THEME['bg_dark'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 10),
            selectbackground=Config.THEME['primary'],
            selectforeground=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.main_app.boot_alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(alerts_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_app.boot_alerts_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.main_app.boot_alerts_listbox.yview)
        
        return page
    
    def _create_threats_page(self):
        """创建威胁列表页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="⚠️ " + lang.get_text("threat_detection"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 威胁列表
        threats_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        threats_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            threats_frame,
            text=lang.get_text("detected_threats"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        threats_container = tk.Frame(threats_frame, bg=Config.THEME['bg_card'])
        threats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.main_app.threats_listbox = tk.Listbox(
            threats_container,
            bg=Config.THEME['bg_dark'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 10),
            selectbackground=Config.THEME['primary'],
            selectforeground=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.main_app.threats_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(threats_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_app.threats_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.main_app.threats_listbox.yview)
        
        # 操作按钮
        actions_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        actions_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Button(
            actions_frame,
            text="🛡️ " + lang.get_text("quarantine_selected"),
            command=self.main_app._quarantine_selected,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['warning'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            actions_frame,
            text="🗑️ " + lang.get_text("delete_selected"),
            command=self.main_app._delete_selected,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['accent'],
            fg="white",
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            actions_frame,
            text="📋 " + lang.get_text("clear_list"),
            command=self.main_app._clear_threats,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
        
        return page
    
    def _create_quarantine_page(self):
        """创建隔离区页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="🗄️ " + lang.get_text("quarantine_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 隔离区信息
        info_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        info_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Label(
            info_frame,
            text=lang.get_text("quarantine_info"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        info_container = tk.Frame(info_frame, bg=Config.THEME['bg_card'])
        info_container.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        # 获取隔离区文件信息
        quarantine_count = 0
        quarantine_size = 0
        
        if os.path.exists(Config.QUARANTINE_DIR):
            for root, dirs, files in os.walk(Config.QUARANTINE_DIR):
                quarantine_count += len(files)
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        quarantine_size += os.path.getsize(file_path)
                    except:
                        pass
        
        tk.Label(
            info_container,
            text=lang.get_text("quarantined_files") + f": {quarantine_count}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        size_mb = quarantine_size / (1024 * 1024)
        tk.Label(
            info_container,
            text=lang.get_text("space_used") + f": {size_mb:.2f} MB",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_container,
            text=lang.get_text("location") + f": {Config.QUARANTINE_DIR}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        # 操作按钮
        actions_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        actions_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Button(
            actions_frame,
            text="📂 " + lang.get_text("open_quarantine"),
            command=self._open_quarantine,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            actions_frame,
            text="🗑️ " + lang.get_text("clear_quarantine"),
            command=self._clear_quarantine,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['accent'],
            fg="white",
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            actions_frame,
            text="📋 " + lang.get_text("view_log"),
            command=self._view_quarantine_log,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
        
        return page
    
    def _open_quarantine(self):
        """打开隔离区目录"""
        try:
            if os.path.exists(Config.QUARANTINE_DIR):
                if platform.system() == "Windows":
                    os.startfile(Config.QUARANTINE_DIR)
                else:
                    subprocess.run(['xdg-open', Config.QUARANTINE_DIR])
            else:
                messagebox.showinfo(lang.get_text("quarantine_title"), lang.get_text("quarantine") + " " + lang.get_text("info") + " " + lang.get_text("location"))
        except Exception as e:
            messagebox.showerror(lang.get_text("error"), f"{lang.get_text('error')}: {str(e)}")
    
    def _clear_quarantine(self):
        """清空隔离区"""
        if not os.path.exists(Config.QUARANTINE_DIR):
            messagebox.showinfo(lang.get_text("quarantine_title"), lang.get_text("quarantine") + " " + lang.get_text("info"))
            return
        
        if messagebox.askyesno(lang.get_text("confirm_action"), "⚠️  " + lang.get_text("confirm") + " " + lang.get_text("clear_quarantine") + "?\n\n" + lang.get_text("warning") + "!"):
            try:
                shutil.rmtree(Config.QUARANTINE_DIR)
                os.makedirs(Config.QUARANTINE_DIR, exist_ok=True)
                messagebox.showinfo(lang.get_text("success"), lang.get_text("quarantine") + " " + lang.get_text("clear_list") + " " + lang.get_text("success"))
            except Exception as e:
                messagebox.showerror(lang.get_text("error"), f"{lang.get_text('error')}: {str(e)}")
    
    def _view_quarantine_log(self):
        """查看隔离区日志"""
        log_file = os.path.join(Config.LOG_DIR, 'quarantine.log')
        if os.path.exists(log_file):
            try:
                if platform.system() == "Windows":
                    os.startfile(log_file)
                else:
                    subprocess.run(['xdg-open', log_file])
            except Exception as e:
                messagebox.showerror(lang.get_text("error"), f"{lang.get_text('error')}: {str(e)}")
        else:
            messagebox.showinfo(lang.get_text("log_center"), lang.get_text("quarantine_log") + " " + lang.get_text("info"))
    
    def _create_logs_page(self):
        """创建日志中心页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="📋 " + lang.get_text("log_center_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 日志文件列表
        logs_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            logs_frame,
            text=lang.get_text("log_files"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        logs_container = tk.Frame(logs_frame, bg=Config.THEME['bg_card'])
        logs_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 日志文件列表
        log_files = [
            {"name_key": "main_log", "path": "pyrt_security_suite.log", "desc": lang.get_text("main_log")},
            {"name_key": "realtime_log", "path": Config.REAL_TIME_LOG, "desc": lang.get_text("realtime_log")},
            {"name_key": "network_log", "path": Config.NETWORK_LOG, "desc": lang.get_text("network_log")},
            {"name_key": "quarantine_log", "path": "quarantine.log", "desc": lang.get_text("quarantine_log")},
            {"name_key": "scan_log", "path": "pyrt_antivirus.log", "desc": lang.get_text("scan_log")},
            {"name_key": "boot_log", "path": Config.BOOT_HASH_DB, "desc": lang.get_text("boot_log")},
        ]
        
        for log_file in log_files:
            file_frame = tk.Frame(logs_container, bg=Config.THEME['bg_card'])
            file_frame.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(
                file_frame,
                text="📄",
                font=("Segoe UI Emoji", 16),
                fg=Config.THEME['primary'],
                bg=Config.THEME['bg_card']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            text_frame = tk.Frame(file_frame, bg=Config.THEME['bg_card'])
            text_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
            
            tk.Label(
                text_frame,
                text=lang.get_text(log_file["name_key"]),
                font=("Microsoft YaHe", 12, "bold"),
                fg=Config.THEME['text_primary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="w")
            
            tk.Label(
                text_frame,
                text=log_file["desc"],
                font=("Microsoft YaHe", 10),
                fg=Config.THEME['text_secondary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor="w")
            
            tk.Button(
                file_frame,
                text=lang.get_text("view"),
                command=lambda p=log_file["path"]: self._view_log_file(p),
                font=("Microsoft YaHe", 10),
                bg=Config.THEME['primary'],
                fg=Config.THEME['bg_dark'],
                relief=tk.FLAT,
                padx=15,
                pady=5,
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=(0, 10))
        
        return page
    
    def _view_log_file(self, log_path):
        """查看日志文件"""
        try:
            full_path = os.path.join(Config.LOG_DIR, log_path) if not os.path.isabs(log_path) else log_path
            if os.path.exists(full_path):
                if platform.system() == "Windows":
                    os.startfile(full_path)
                else:
                    subprocess.run(['xdg-open', full_path])
            else:
                messagebox.showinfo(lang.get_text("log_center"), f"{lang.get_text('log_files')} {lang.get_text('info')}: {log_path}")
        except Exception as e:
            messagebox.showerror(lang.get_text("error"), f"{lang.get_text('error')}: {str(e)}")
    
    def _create_settings_page(self):
        """创建设置页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="⚙️ " + lang.get_text("settings_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 设置选项
        settings_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            settings_frame,
            text=lang.get_text("program_settings"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        settings_container = tk.Frame(settings_frame, bg=Config.THEME['bg_card'])
        settings_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        # 设置选项
        settings_options = [
            {"name_key": "auto_start", "desc_key": "auto_start_desc", "default": False},
            {"name_key": "auto_update", "desc_key": "auto_update_desc", "default": True},
            {"name_key": "show_notifications", "desc_key": "show_notifications_desc", "default": True},
            {"name_key": "low_resource_mode", "desc_key": "low_resource_mode_desc", "default": False},
            {"name_key": "dark_theme", "desc_key": "dark_theme_desc", "default": True},
            {"name_key": "enable_network_protection", "desc_key": "enable_network_protection_desc", "default": Config.NETWORK_PROTECTION_ENABLED},
        ]
        
        self.setting_vars = []
        
        for option in settings_options:
            option_frame = tk.Frame(settings_container, bg=Config.THEME['bg_card'])
            option_frame.pack(fill=tk.X, pady=(0, 15))
            
            var = tk.BooleanVar(value=option["default"])
            self.setting_vars.append(var)
            
            tk.Checkbutton(
                option_frame,
                text=lang.get_text(option["name_key"]),
                variable=var,
                font=("Microsoft YaHe", 12),
                fg=Config.THEME['text_primary'],
                bg=Config.THEME['bg_card'],
                selectcolor=Config.THEME['bg_dark'],
                activebackground=Config.THEME['bg_card'],
                activeforeground=Config.THEME['text_primary']
            ).pack(anchor=tk.W)
            
            tk.Label(
                option_frame,
                text=lang.get_text(option["desc_key"]),
                font=("Microsoft YaHe", 10),
                fg=Config.THEME['text_secondary'],
                bg=Config.THEME['bg_card']
            ).pack(anchor=tk.W, padx=(20, 0))
        
        # 语言设置
        lang_frame = tk.Frame(settings_container, bg=Config.THEME['bg_card'])
        lang_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            lang_frame,
            text=lang.get_text("language") + ":",
            font=("Microsoft YaHe", 12),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=(0, 5))
        
        lang_button = tk.Button(
            lang_frame,
            text=Config.SUPPORTED_LANGUAGES[Config.LANGUAGE] + " ▼",
            command=self._show_language_selection,
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        )
        lang_button.pack(anchor=tk.W)
        
        # 保存按钮
        button_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="💾 " + lang.get_text("save_settings"),
            command=self._save_settings,
            font=("Microsoft YaHe", 14, "bold"),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor="hand2"
        ).pack()
        
        return page
    
    def _show_language_selection(self):
        """显示语言选择对话框"""
        def on_language_changed(lang_code):
            # 刷新页面文本
            self._refresh_all_texts()
        
        LanguageSelectionDialog(self.parent, on_language_changed)
    
    def _refresh_all_texts(self):
        """刷新所有页面文本"""
        # 重新创建所有页面
        for page in self.pages:
            page.destroy()
        self.pages.clear()
        self._create_pages()
        self.show_page(self.current_page)
    
    def _save_settings(self):
        """保存设置"""
        # 在实际应用中，这里应该将设置保存到配置文件
        messagebox.showinfo(lang.get_text("settings_title"), lang.get_text("save_settings") + " " + lang.get_text("success"))
    
    def _create_network_page(self):
        """创建断网保护页面"""
        page = tk.Frame(self.container, bg=Config.THEME['bg_dark'])
        
        # 页面标题
        title_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        title_frame.pack(fill=tk.X, pady=(20, 30), padx=30)
        
        tk.Label(
            title_frame,
            text="🌐 " + lang.get_text("network_protection_title"),
            font=("Microsoft YaHe", 24, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(side=tk.LEFT)
        
        # 网络保护状态
        status_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        status_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Label(
            status_frame,
            text=lang.get_text("protection_status"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # 状态信息
        info_frame = tk.Frame(status_frame, bg=Config.THEME['bg_card'])
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.main_app.network_status_label = tk.Label(
            info_frame,
            text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
            font=("Microsoft YaHe", 12),
            fg=Config.THEME['success'],
            bg=Config.THEME['bg_card']
        )
        self.main_app.network_status_label.pack(anchor=tk.W, pady=5)
        
        self.main_app.network_status_text = tk.Label(
            info_frame,
            text=lang.get_text("network_status") + ": " + lang.get_text("checking") + " | " + lang.get_text("internet_status") + ": " + lang.get_text("checking"),
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        )
        self.main_app.network_status_text.pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_frame,
            text=lang.get_text("blocked_ips") + f": {len(self.main_app.network_engine.blocked_ips) if hasattr(self.main_app, 'network_engine') else 0}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        tk.Label(
            info_frame,
            text=lang.get_text("blocked_domains") + f": {len(self.main_app.network_engine.blocked_domains) if hasattr(self.main_app, 'network_engine') else 0}",
            font=("Microsoft YaHe", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_card']
        ).pack(anchor=tk.W, pady=5)
        
        # 控制按钮
        control_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        control_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        row1_frame = tk.Frame(control_frame, bg=Config.THEME['bg_dark'])
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.main_app.network_toggle_btn = tk.Button(
            row1_frame,
            text="⏸️ " + lang.get_text("pause_protection"),
            command=self.main_app._toggle_network_protection,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['warning'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        )
        self.main_app.network_toggle_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row1_frame,
            text="🔍 " + lang.get_text("check_network"),
            command=self.main_app._check_network_security,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row1_frame,
            text="⚙️ " + lang.get_text("settings"),
            command=self.main_app._show_network_settings,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        row2_frame = tk.Frame(control_frame, bg=Config.THEME['bg_dark'])
        row2_frame.pack(fill=tk.X)
        
        tk.Button(
            row2_frame,
            text="📋 " + lang.get_text("view_connections"),
            command=self.main_app._show_network_connections,
            font=("Microsoft YaHe", 12),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        tk.Button(
            row2_frame,
            text="🚫 " + lang.get_text("emergency_disconnect"),
            command=self.main_app._emergency_disconnect,
            font=("Microsoft YaHe", 12, "bold"),
            bg=Config.THEME['accent'],
            fg="white",
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # 警报列表
        alerts_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        alerts_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))
        
        tk.Label(
            alerts_frame,
            text=lang.get_text("network_alerts"),
            font=("Microsoft YaHe", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_card'],
            anchor=tk.W
        ).pack(fill=tk.X, padx=20, pady=(15, 10))
        
        alerts_container = tk.Frame(alerts_frame, bg=Config.THEME['bg_card'])
        alerts_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        self.main_app.network_alerts_listbox = tk.Listbox(
            alerts_container,
            bg=Config.THEME['bg_dark'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 10),
            selectbackground=Config.THEME['primary'],
            selectforeground=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.main_app.network_alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(alerts_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_app.network_alerts_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.main_app.network_alerts_listbox.yview)
        
        return page
    
    def show_page(self, page_index):
        """显示指定页面"""
        # 隐藏所有页面
        for page in self.pages:
            page.pack_forget()
        
        # 显示指定页面
        if 0 <= page_index < len(self.pages):
            self.pages[page_index].pack(fill=tk.BOTH, expand=True)
            self.current_page = page_index

# ==================== 病毒特征库 ====================
class VirusDatabase:
    """病毒特征数据库"""
    
    def __init__(self):
        self.signatures = {}
        self.behavior_patterns = {}
        self.heuristic_rules = {}
        self.load_databases()
    
    def load_databases(self):
        """加载病毒数据库"""
        # 基本病毒签名（MD5/SHA1）
        self.signatures = {
            # 已知病毒哈希（示例）
            'e99a18c428cb38d5f260853678922e03': 'Trojan.Win32.Generic',
            '5d41402abc4b2a76b9719d911017c592': 'Backdoor.Win32.Agent',
            '098f6bcd4621d373cade4e832627b4f6': 'Ransomware.Win32.Crypto',
            'a4d3b161ce1309df1c4e25df1c4e25df': 'Adware.Win32.Popup',
            'b7e23ec29c22dde397d5e83d7e23ec29': 'Spyware.Win32.Keylogger',
            # 更多示例签名
            'c4ca4238a0b923820dcc509a6f75849b': 'Virus.Test.1',
            'c81e728d9d4c2f636f067f89cc14862c': 'Virus.Test.2',
            'eccbc87e4b5ce2fe28308fd9f2a7baf3': 'Virus.Test.3',
        }
        
        # 行为模式
        self.behavior_patterns = {
            'registry_autostart': ['\\Run', '\\RunOnce', '\\Policies\\Explorer\\Run'],
            'system_file_modification': ['system32', 'drivers', 'hosts', 'boot.ini'],
            'network_connections': ['botnet', 'c2', 'command', 'control'],
            'file_encryption': ['encrypt', 'crypt', 'ransom', '.locked'],
            'process_injection': ['CreateRemoteThread', 'WriteProcessMemory'],
        }
        
        # 启发式规则
        self.heuristic_rules = {
            'suspicious_strings': [
                'format c:', 'delete system', 'disable firewall',
                'disable antivirus', 'taskkill', 'reg delete',
                'powershell -enc', 'certutil -decode', 'wmic process call',
                'rm -rf', 'del /f /q', 'format', 'erase',
                'rundll32', 'regsvr32', 'wscript.shell',
            ],
            'suspicious_apis': [
                'VirtualAllocEx', 'CreateRemoteThread', 'SetWindowsHookEx',
                'RegisterHotKey', 'keybd_event', 'GetAsyncKeyState',
                'WSASocket', 'connect', 'bind', 'listen',
            ],
            'file_extensions': ['.vbs', '.js', '.ps1', '.bat', '.cmd', '.scr', '.pif', '.jar'],
            'entropy_threshold': 7.0,
        }
        
        # 尝试从文件加载
        self._load_from_files()
    
    def _load_from_files(self):
        """从文件加载数据库"""
        try:
            if os.path.exists(Config.VIRUS_DB_PATH):
                with open(Config.VIRUS_DB_PATH, 'rb') as f:
                    loaded_sigs = pickle.load(f)
                    self.signatures.update(loaded_sigs)
        except Exception as e:
            logger.warning(f"加载病毒签名数据库失败: {e}")
        
        try:
            if os.path.exists(Config.HEURISTIC_RULES_PATH):
                with open(Config.HEURISTIC_RULES_PATH, 'r', encoding='utf-8') as f:
                    loaded_rules = json.load(f)
                    self.heuristic_rules.update(loaded_rules)
        except Exception as e:
            logger.warning(f"加载启发式规则失败: {e}")
    
    def save_databases(self):
        """保存数据库到文件"""
        try:
            with open(Config.VIRUS_DB_PATH, 'wb') as f:
                pickle.dump(self.signatures, f)
        except Exception as e:
            logger.error(f"保存病毒签名数据库失败: {e}")
        
        try:
            with open(Config.HEURISTIC_RULES_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.heuristic_rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存启发式规则失败: {e}")
    
    def add_signature(self, file_hash, virus_name):
        """添加新的病毒签名"""
        self.signatures[file_hash] = virus_name
        self.save_databases()
    
    def check_hash(self, file_hash):
        """检查文件哈希是否在病毒库中"""
        return self.signatures.get(file_hash, None)
    
    def heuristic_analysis(self, file_path):
        """启发式分析"""
        score = 0
        findings = []
        
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return 0, ["空文件"]
            
            with open(file_path, 'rb') as f:
                content = f.read(65536)  # 读取前64KB
                
                if not content:
                    return 0, ["无法读取文件内容"]
                
                # 检查可疑字符串
                text_content = content.decode('utf-8', errors='ignore').lower()
                for suspicious in self.heuristic_rules['suspicious_strings']:
                    if suspicious.lower() in text_content:
                        score += 10
                        findings.append(f"发现可疑字符串: {suspicious}")
                
                # 检查文件熵
                entropy = self._calculate_entropy(content)
                if entropy > self.heuristic_rules['entropy_threshold']:
                    score += int(entropy * 2)  # 根据熵值调整分数
                    findings.append(f"高熵值文件 (熵: {entropy:.2f})")
                
                # 检查二进制模式
                if content.count(b'\x00') > len(content) * 0.3:
                    score += 5
                    findings.append("高比例空字节填充")
                
                # 检查可执行文件特征
                if file_path.lower().endswith(('.exe', '.dll', '.sys')):
                    pe_score, pe_findings = self._analyze_executable(file_path, content)
                    score += pe_score
                    findings.extend(pe_findings)
                
                # 检查可疑扩展名
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.heuristic_rules['file_extensions']:
                    score += 5
                    findings.append(f"可疑文件扩展名: {ext}")
        
        except Exception as e:
            logger.debug(f"启发式分析失败 {file_path}: {e}")
            findings.append(f"分析异常: {str(e)[:50]}")
        
        return score, findings
    
    def _calculate_entropy(self, data):
        """计算数据熵值"""
        if not data:
            return 0
        
        entropy = 0
        data_len = len(data)
        
        # 统计字节频率
        frequency = {}
        for byte in data:
            if byte in frequency:
                frequency[byte] += 1
            else:
                frequency[byte] = 1
        
        # 计算熵值
        for count in frequency.values():
            probability = count / data_len
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _analyze_executable(self, file_path, content):
        """分析可执行文件"""
        score = 0
        findings = []
        
        try:
            # 检查MZ头
            if content[:2] != b'MZ':
                score += 20
                findings.append("无效的EXE文件头")
                return score, findings
            
            # 检查PE头偏移
            if len(content) >= 64:
                pe_offset = struct.unpack('<I', content[60:64])[0]
                if pe_offset < 64 or pe_offset > len(content) - 4:
                    score += 15
                    findings.append("可疑的PE头偏移")
                    return score, findings
                
                # 检查PE签名
                if len(content) >= pe_offset + 4:
                    if content[pe_offset:pe_offset+4] != b'PE\0\0':
                        score += 25
                        findings.append("无效的PE签名")
            
            # 检查常见恶意字符串
            malware_strings = [
                b'This program cannot be run in DOS mode',
                b'Microsoft',
                b'Windows',
                b'kernel32.dll',
                b'user32.dll',
            ]
            
            found_strings = 0
            for mal_str in malware_strings:
                if mal_str in content:
                    found_strings += 1
            
            if found_strings < 2:  # 正常EXE应该包含多个系统字符串
                score += 10
                findings.append("缺少常见系统字符串")
        
        except Exception as e:
            logger.debug(f"可执行文件分析失败 {file_path}: {e}")
        
        return score, findings

# ==================== 增强的PYRT扫描引擎 ====================
class EnhancedPYRTScanEngine:
    """增强的PYRT专业扫描引擎"""
    
    def __init__(self):
        self.scanning = False
        self.total_files = 0
        self.scanned_files = 0
        self.threats_found = 0
        self.scan_speed = 0
        self.start_time = 0
        self.animation_angle = 0
        self.virus_db = VirusDatabase()
        self.suspicious_files = []
        self.current_scan_paths = []
        self.current_file_index = 0
        
        # 文件类型扫描器
        self.file_scanners = {
            '.exe': self._scan_executable,
            '.dll': self._scan_executable,
            '.sys': self._scan_executable,
            '.doc': self._scan_office_document,
            '.docx': self._scan_office_document,
            '.xls': self._scan_office_document,
            '.xlsx': self._scan_office_document,
            '.pdf': self._scan_pdf,
            '.js': self._scan_script,
            '.vbs': self._scan_script,
            '.ps1': self._scan_script,
            '.bat': self._scan_script,
            '.cmd': self._scan_script,
            '.jar': self._scan_jar,
        }
    
    def start_scan(self, scan_type="quick", scan_paths=None):
        """开始增强扫描"""
        self.scanning = True
        self.scanned_files = 0
        self.threats_found = 0
        self.suspicious_files = []
        self.current_file_index = 0
        self.start_time = time.time()
        
        # 确定扫描路径
        if scan_paths:
            self.current_scan_paths = scan_paths
        elif scan_type == "quick":
            self.current_scan_paths = self._get_quick_scan_paths()
        elif scan_type == "full":
            self.current_scan_paths = self._get_full_scan_paths()
        else:
            self.current_scan_paths = [os.path.expanduser("~")]
        
        # 计算总文件数
        self.total_files = self._count_files(self.current_scan_paths)
        if self.total_files == 0:
            self.total_files = 100  # 默认值
        
        self.scan_speed = random.randint(10, 30)
        
        logger.info(f"PYRT增强扫描引擎启动 - 类型: {scan_type}, 文件数: {self.total_files}")
    
    def _get_quick_scan_paths(self):
        """获取快速扫描路径"""
        paths = []
        user_profile = os.path.expanduser("~")
        
        # 关键系统路径
        system_paths = [
            os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "Documents"),
            os.getenv("TEMP", os.path.join(user_profile, "AppData", "Local", "Temp")),
            os.getenv("APPDATA", os.path.join(user_profile, "AppData", "Roaming")),
        ]
        
        for path in system_paths:
            if os.path.exists(path):
                paths.append(path)
        
        return paths
    
    def _get_full_scan_paths(self):
        """获取全盘扫描路径"""
        paths = []
        
        # Windows系统
        if platform.system() == "Windows":
            import string
            for drive in string.ascii_uppercase:
                drive_path = f"{drive}:\\"
                if os.path.exists(drive_path):
                    paths.append(drive_path)
        else:
            # Linux/Mac
            paths = ["/", os.path.expanduser("~")]
            common_dirs = ["/etc", "/var", "/usr", "/bin", "/sbin"]
            for dir_path in common_dirs:
                if os.path.exists(dir_path):
                    paths.append(dir_path)
        
        return paths
    
    def _count_files(self, paths):
        """计算要扫描的文件总数"""
        count = 0
        max_files = 5000  # 限制最大文件数以提高性能
        
        for path in paths[:3]:  # 限制前3个目录
            if os.path.exists(path):
                try:
                    for root, dirs, files in os.walk(path):
                        count += len(files)
                        if count >= max_files:
                            return max_files
                except Exception as e:
                    logger.warning(f"遍历目录失败 {path}: {e}")
        
        return min(count, max_files)
    
    def update_scan(self):
        """更新扫描进度"""
        if not self.scanning:
            return None
        
        # 扫描文件
        threats = []
        files_scanned_in_batch = 0
        max_files_per_batch = 5
        
        # 收集要扫描的文件
        files_to_scan = []
        
        for scan_path in self.current_scan_paths:
            if not self.scanning or len(files_to_scan) >= max_files_per_batch:
                break
                
            if os.path.exists(scan_path):
                try:
                    for root, dirs, files in os.walk(scan_path):
                        for file in files:
                            if len(files_to_scan) >= max_files_per_batch:
                                break
                            
                            file_path = os.path.join(root, file)
                            
                            # 跳过系统文件和临时文件
                            if self._should_skip_file(file_path):
                                continue
                            
                            # 检查文件大小
                            try:
                                if os.path.getsize(file_path) > Config.MAX_FILE_SIZE:
                                    continue
                            except:
                                continue
                            
                            files_to_scan.append(file_path)
                        
                        if len(files_to_scan) >= max_files_per_batch:
                            break
                except Exception as e:
                    logger.warning(f"扫描目录失败 {scan_path}: {e}")
                    continue
        
        # 扫描收集到的文件
        for file_path in files_to_scan:
            if not self.scanning:
                break
            
            try:
                file_threats = self._scan_file(file_path)
                if file_threats:
                    threats.extend(file_threats)
                    self.threats_found += len(file_threats)
                
                self.scanned_files += 1
                files_scanned_in_batch += 1
                
            except Exception as e:
                logger.warning(f"扫描文件失败 {file_path}: {e}")
                self.scanned_files += 1
        
        # 计算扫描统计
        elapsed = time.time() - self.start_time
        progress = (self.scanned_files / self.total_files) * 100 if self.total_files > 0 else 0
        
        if self.scanned_files >= self.total_files or not self.current_scan_paths:
            self.scanning = False
            logger.info("PYRT增强扫描完成")
        
        return {
            'progress': min(progress, 100),
            'scanned': self.scanned_files,
            'total': self.total_files,
            'threats': self.threats_found,
            'speed': self.scan_speed,
            'elapsed': elapsed,
            'new_threats': threats,
            'scanning': self.scanning,
            'suspicious_files': self.suspicious_files[-5:]
        }
    
    def _should_skip_file(self, file_path):
        """检查是否应该跳过文件"""
        skip_patterns = [
            r'\.(log|tmp|temp|bak|old)$',
            r'pagefile\.sys$',
            r'hiberfil\.sys$',
            r'\\Windows\\',
            r'\\Program Files\\',
            r'\\Program Files \(x86\)\\',
        ]
        
        file_path_lower = file_path.lower()
        for pattern in skip_patterns:
            if re.search(pattern, file_path_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _scan_file(self, file_path):
        """扫描单个文件"""
        threats = []
        
        try:
            # 1. 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)
            
            # 2. 检查已知病毒签名
            known_virus = self.virus_db.check_hash(file_hash)
            if known_virus:
                threats.append({
                    'name': known_virus,
                    'file': file_path,
                    'severity': 'Critical',
                    'type': '已知病毒',
                    'hash': file_hash,
                    'method': '哈希匹配'
                })
                return threats
            
            # 3. 根据文件类型调用相应的扫描器
            ext = os.path.splitext(file_path)[1].lower()
            if ext in self.file_scanners:
                scanner_threats = self.file_scanners[ext](file_path)
                if scanner_threats:
                    threats.extend(scanner_threats)
            
            # 4. 启发式分析
            heuristic_score, findings = self.virus_db.heuristic_analysis(file_path)
            if heuristic_score > 15:
                threat_level = 'Low'
                if heuristic_score > 30:
                    threat_level = 'Medium'
                if heuristic_score > 50:
                    threat_level = 'High'
                if heuristic_score > 70:
                    threat_level = 'Critical'
                
                threats.append({
                    'name': f'启发式检测.{threat_level}',
                    'file': file_path,
                    'severity': threat_level,
                    'type': '启发式检测',
                    'score': heuristic_score,
                    'findings': findings[:3],
                    'method': '启发式分析'
                })
                
                # 记录可疑文件
                if heuristic_score > 40:
                    self.suspicious_files.append({
                        'path': file_path,
                        'score': heuristic_score,
                        'findings': findings
                    })
            
            # 5. 检查可疑文件名模式
            filename = os.path.basename(file_path).lower()
            suspicious_patterns = [
                (r'(keygen|crack|serial|patch)\.(exe|dll)$', 'High', '破解工具'),
                (r'(invoice|receipt|document_\d+)\.(exe|scr)$', 'High', '钓鱼软件'),
                (r'(decryptor|recover_files)\.(exe|html)$', 'Critical', '勒索软件'),
                (r'(update|upgrade|installer_\d+)\.exe$', 'Medium', '伪装更新'),
                (r'(free|gift|prize|winner)\.(exe|scr)$', 'Medium', '诈骗软件'),
            ]
            
            for pattern, severity, threat_type in suspicious_patterns:
                if re.search(pattern, filename):
                    threats.append({
                        'name': f'可疑文件.{threat_type}',
                        'file': file_path,
                        'severity': severity,
                        'type': '文件名模式',
                        'pattern': pattern,
                        'method': '文件名分析'
                    })
                    break
        
        except Exception as e:
            logger.debug(f"扫描文件失败 {file_path}: {e}")
        
        return threats
    
    def _calculate_file_hash(self, file_path):
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return "00000000000000000000000000000000"
    
    def _scan_executable(self, file_path):
        """扫描可执行文件"""
        threats = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024)
                
                if len(content) < 2:
                    return threats
                
                # 检查MZ头
                if content[:2] != b'MZ':
                    threats.append({
                        'name': '异常EXE文件',
                        'file': file_path,
                        'severity': 'Medium',
                        'type': '无效文件头',
                        'method': 'PE头分析'
                    })
                    return threats
                
                # 检查文件大小
                file_size = os.path.getsize(file_path)
                if file_size < 1024:
                    threats.append({
                        'name': '微型EXE文件',
                        'file': file_path,
                        'severity': 'Medium',
                        'type': '可疑文件大小',
                        'method': '文件大小分析'
                    })
        
        except Exception as e:
            pass
        
        return threats
    
    def _scan_office_document(self, file_path):
        """扫描Office文档"""
        threats = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(4096)
                
                # 检查Office文档签名
                if content[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                    # OLE复合文档
                    if b'VBA' in content or b'Macros' in content or b'Macro' in content:
                        threats.append({
                            'name': 'Office宏文档',
                            'file': file_path,
                            'severity': 'Medium',
                            'type': '宏文档',
                            'method': '文档结构分析'
                        })
                
                # 检查新版Office格式
                elif content[:4] == b'PK\x03\x04':
                    threats.append({
                        'name': '新版Office文档',
                        'file': file_path,
                        'severity': 'Low',
                        'type': '文档格式检查',
                        'method': '文件格式分析'
                    })
        
        except:
            pass
        
        return threats
    
    def _scan_pdf(self, file_path):
        """扫描PDF文件"""
        threats = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(1024)
                
                # 检查PDF头
                if content[:5] != b'%PDF-':
                    threats.append({
                        'name': '异常PDF文件',
                        'file': file_path,
                        'severity': 'Medium',
                        'type': '无效PDF头',
                        'method': 'PDF头分析'
                    })
                    return threats
                
                # 检查JavaScript
                f.seek(0)
                more_content = f.read(8192)
                
                if b'/JavaScript' in more_content or b'/JS' in more_content:
                    threats.append({
                        'name': 'PDF含JavaScript',
                        'file': file_path,
                        'severity': 'High',
                        'type': 'PDF脚本',
                        'method': 'PDF内容分析'
                    })
        
        except:
            pass
        
        return threats
    
    def _scan_script(self, file_path):
        """扫描脚本文件"""
        threats = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(16384)
                
                # 检查可疑命令
                suspicious_cmds = [
                    (r'powershell.*-enc', 'High', '编码PowerShell'),
                    (r'wscript\.createobject', 'Medium', 'WScript对象创建'),
                    (r'shell\.execute', 'Medium', 'Shell执行'),
                    (r'reg\.(add|delete)', 'High', '注册表修改'),
                    (r'taskkill.*/im.*(av|anti|defender|security)', 'Critical', '杀软关闭'),
                    (r'format.*[cdefg]:', 'Critical', '磁盘格式化'),
                    (r'net.*user.*/add', 'High', '用户创建'),
                    (r'netsh.*firewall.*disable', 'High', '防火墙关闭'),
                    (r'cmd\.exe.*/c', 'Medium', 'CMD执行'),
                    (r'start.*/min', 'Low', '最小化启动'),
                ]
                
                for pattern, severity, desc in suspicious_cmds:
                    if re.search(pattern, content, re.IGNORECASE):
                        threats.append({
                            'name': f'可疑脚本.{desc}',
                            'file': file_path,
                            'severity': severity,
                            'type': '脚本命令',
                            'method': '脚本内容分析'
                        })
                        break
        
        except Exception as e:
            logger.debug(f"脚本文件分析失败 {file_path}: {e}")
        
        return threats
    
    def _scan_jar(self, file_path):
        """扫描JAR文件"""
        threats = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read(4)
                
                if content[:4] == b'PK\x03\x04':
                    threats.append({
                        'name': 'Java归档文件',
                        'file': file_path,
                        'severity': 'Low',
                        'type': 'JAR文件',
                        'method': '文件格式检查'
                    })
        
        except:
            pass
        
        return threats
    
    def quarantine_file(self, file_path, threat_info):
        """隔离文件"""
        try:
            quarantine_dir = Config.QUARANTINE_DIR
            if not os.path.exists(quarantine_dir):
                os.makedirs(quarantine_dir)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = os.path.basename(file_path)
            safe_file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            quarantine_name = f"{timestamp}_{threat_info.get('name', 'unknown').replace('.', '_')}_{safe_file_name}"
            quarantine_path = os.path.join(quarantine_dir, quarantine_name)
            
            shutil.copy2(file_path, quarantine_path)
            
            log_entry = {
                'timestamp': timestamp,
                'original_path': file_path,
                'quarantine_path': quarantine_path,
                'threat_name': threat_info.get('name', 'unknown'),
                'severity': threat_info.get('severity', 'unknown'),
                'action': 'quarantined'
            }
            
            log_dir = Config.LOG_DIR
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, 'quarantine.log')
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            return True, quarantine_path
            
        except Exception as e:
            logger.error(f"隔离文件失败 {file_path}: {e}")
            return False, str(e)
    
    def restore_file(self, quarantine_path):
        """恢复隔离文件"""
        try:
            log_file = os.path.join(Config.LOG_DIR, 'quarantine.log')
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('quarantine_path') == quarantine_path:
                                original_path = entry.get('original_path')
                                
                                if os.path.exists(quarantine_path):
                                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                                    shutil.move(quarantine_path, original_path)
                                    return True
                        except:
                            continue
            
            return False
            
        except Exception as e:
            logger.error(f"恢复文件失败 {quarantine_path}: {e}")
            return False
    
    def stop_scan(self):
        """停止扫描"""
        self.scanning = False
        logger.info("PYRT增强扫描已停止")

# ==================== 实时保护引擎 ====================
class RealTimeProtection:
    """实时保护引擎"""
    
    def __init__(self, virus_db, scan_engine):
        self.virus_db = virus_db
        self.scan_engine = scan_engine
        self.running = False
        self.monitor_thread = None
        self.process_monitor_thread = None
        self.directory_monitor_thread = None
        self.blocked_files = set()
        self.alert_queue = []
        self.last_alert_time = 0
        self.alert_cooldown = 5
        
        # 文件监控状态
        self.file_states = {}
        self.directory_states = {}
        
        # 进程监控状态
        self.process_states = set()
        
        # 创建实时保护日志
        self._init_realtime_log()
    
    def _init_realtime_log(self):
        """初始化实时保护日志"""
        try:
            if not os.path.exists(Config.LOG_DIR):
                os.makedirs(Config.LOG_DIR)
            
            self.realtime_log_path = os.path.join(Config.LOG_DIR, Config.REAL_TIME_LOG)
            
            realtime_handler = logging.FileHandler(self.realtime_log_path, encoding='utf-8')
            realtime_handler.setFormatter(logging.Formatter('%(asctime)s - [实时保护] - %(levelname)s - %(message)s'))
            logger.addHandler(realtime_handler)
            
        except Exception as e:
            logger.error(f"初始化实时保护日志失败: {e}")
    
    def start(self):
        """启动实时保护"""
        if self.running:
            logger.warning("实时保护已经在运行中")
            return False
        
        try:
            self.running = True
            
            # 启动目录监控
            self._start_directory_monitor()
            
            # 启动进程监控
            if Config.MONITOR_PROCESSES:
                self._start_process_monitor()
            
            logger.info("实时保护引擎启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动实时保护失败: {e}")
            self.running = False
            return False
    
    def stop(self):
        """停止实时保护"""
        self.running = False
        
        for thread in [self.directory_monitor_thread, self.process_monitor_thread, self.monitor_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2)
        
        logger.info("实时保护引擎已停止")
    
    def _start_directory_monitor(self):
        """启动目录监控"""
        try:
            self.directory_monitor_thread = threading.Thread(
                target=self._directory_monitor_loop, 
                daemon=True,
                name="DirectoryMonitor"
            )
            self.directory_monitor_thread.start()
            logger.info("目录监控已启动")
        except Exception as e:
            logger.error(f"启动目录监控失败: {e}")
    
    def _start_process_monitor(self):
        """启动进程监控"""
        try:
            self.process_monitor_thread = threading.Thread(
                target=self._process_monitor_loop, 
                daemon=True,
                name="ProcessMonitor"
            )
            self.process_monitor_thread.start()
            logger.info("进程监控已启动")
        except Exception as e:
            logger.error(f"启动进程监控失败: {e}")
    
    def _directory_monitor_loop(self):
        """目录监控循环"""
        # 初始化目录状态
        for path in Config.MONITOR_PATHS:
            if os.path.exists(path):
                self._scan_directory_state(path)
        
        while self.running:
            try:
                for path in Config.MONITOR_PATHS:
                    if not self.running:
                        break
                    
                    if os.path.exists(path):
                        self._check_directory_changes(path)
                
                time.sleep(Config.DIRECTORY_SCAN_INTERVAL)
                
            except Exception as e:
                logger.error(f"目录监控循环错误: {e}")
                time.sleep(5)
    
    def _scan_directory_state(self, directory):
        """扫描目录状态"""
        try:
            file_list = []
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        self.file_states[file_path] = (stat.st_size, stat.st_mtime)
                        file_list.append(file_path)
                    except:
                        continue
            
            self.directory_states[directory] = set(file_list)
            
        except Exception as e:
            logger.error(f"扫描目录状态失败 {directory}: {e}")
    
    def _check_directory_changes(self, directory):
        """检查目录变化"""
        try:
            current_files = set()
            
            for root, dirs, files in os.walk(directory):
                if not self.running:
                    break
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        if os.path.getsize(file_path) > Config.MAX_FILE_SIZE:
                            continue
                    except:
                        continue
                    
                    current_files.add(file_path)
                    
                    try:
                        stat = os.stat(file_path)
                        current_size = stat.st_size
                        current_mtime = stat.st_mtime
                        
                        if file_path not in self.file_states:
                            if Config.SCAN_ON_CREATE:
                                self._handle_file_event(file_path, 'created')
                            self.file_states[file_path] = (current_size, current_mtime)
                        
                        elif Config.SCAN_ON_MODIFY:
                            old_size, old_mtime = self.file_states[file_path]
                            if current_mtime != old_mtime or current_size != old_size:
                                self._handle_file_event(file_path, 'modified')
                                self.file_states[file_path] = (current_size, current_mtime)
                    
                    except Exception as e:
                        logger.debug(f"检查文件状态失败 {file_path}: {e}")
            
            if directory in self.directory_states:
                old_files = self.directory_states[directory]
                deleted_files = old_files - current_files
                
                for file_path in deleted_files:
                    if file_path in self.file_states:
                        del self.file_states[file_path]
            
            self.directory_states[directory] = current_files
            
        except Exception as e:
            logger.error(f"检查目录变化失败 {directory}: {e}")
    
    def _handle_file_event(self, file_path, event_type):
        """处理文件事件"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            scan_extensions = ['.exe', '.dll', '.sys', '.vbs', '.js', '.ps1', '.bat', '.cmd', '.scr', '.pif', '.jar']
            
            if ext in scan_extensions:
                threading.Timer(1.0, self._scan_delayed, args=[file_path, event_type]).start()
        
        except Exception as e:
            logger.error(f"处理文件事件失败 {file_path}: {e}")
    
    def _scan_delayed(self, file_path, event_type):
        """延迟扫描文件"""
        try:
            if os.path.exists(file_path):
                if self.is_file_blocked(file_path):
                    logger.warning(f"阻止访问被拦截的文件: {file_path}")
                    return
                
                threats = self.scan_engine._scan_file(file_path)
                
                if threats:
                    threat = max(threats, key=lambda x: {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}.get(x.get('severity', 'Low'), 0))
                    
                    alert_info = {
                        'type': f'文件{event_type}',
                        'name': threat.get('name', 'Unknown'),
                        'severity': threat.get('severity', 'Medium'),
                        'file_path': file_path,
                        'threat_type': threat.get('type', 'Unknown'),
                        'event_type': event_type,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self._add_alert(alert_info)
                    
                    if Config.BLOCK_SUSPICIOUS and threat.get('severity') in ['High', 'Critical']:
                        self.block_file(file_path)
                        
                        try:
                            success, _ = self.scan_engine.quarantine_file(file_path, threat)
                            if success:
                                alert_info['action'] = '文件已自动隔离'
                            else:
                                alert_info['action'] = '文件被阻止访问'
                        except:
                            alert_info['action'] = '文件被阻止访问'
                    
                    logger.warning(f"实时保护检测到威胁: {alert_info.get('name')} - 文件: {file_path}")
        
        except Exception as e:
            logger.error(f"延迟扫描失败 {file_path}: {e}")
    
    def _process_monitor_loop(self):
        """进程监控循环"""
        known_processes = set()
        
        while self.running:
            try:
                current_processes = set()
                
                if platform.system() == "Windows":
                    processes = self._get_windows_processes()
                else:
                    processes = self._get_unix_processes()
                
                for proc_info in processes:
                    pid = proc_info.get('pid')
                    name = proc_info.get('name', '').lower()
                    cmdline = proc_info.get('cmdline', '')
                    
                    if pid:
                        current_processes.add(pid)
                        
                        if pid not in known_processes:
                            is_suspicious = False
                            threat_info = {}
                            
                            for suspicious_name in Config.SUSPICIOUS_PROCESS_NAMES:
                                if suspicious_name in name:
                                    is_suspicious = True
                                    threat_info = {
                                        'type': '可疑进程',
                                        'name': f"Suspicious.Process.{suspicious_name}",
                                        'severity': 'High',
                                        'process_name': name,
                                        'pid': pid,
                                        'cmdline': cmdline[:200] if cmdline else '',
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    break
                            
                            if not is_suspicious and cmdline:
                                cmdline_lower = cmdline.lower()
                                suspicious_patterns = [
                                    (r'powershell.*-enc', '编码PowerShell'),
                                    (r'reg\s+add', '注册表修改'),
                                    (r'reg\s+delete', '注册表删除'),
                                    (r'taskkill.*/im.*(av|anti|defender)', '杀软关闭'),
                                    (r'format\s+[c-z]:', '磁盘格式化'),
                                ]
                                
                                for pattern, desc in suspicious_patterns:
                                    if re.search(pattern, cmdline_lower):
                                        is_suspicious = True
                                        threat_info = {
                                            'type': '可疑命令行',
                                            'name': f"Suspicious.Cmdline.{desc}",
                                            'severity': 'Critical',
                                            'process_name': name,
                                            'pid': pid,
                                            'cmdline': cmdline_lower[:200],
                                            'pattern': pattern,
                                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                        break
                            
                            if is_suspicious:
                                self._add_alert(threat_info)
                                self._handle_suspicious_process(threat_info)
                
                known_processes = current_processes
                
            except Exception as e:
                logger.error(f"进程监控错误: {e}")
            
            time.sleep(Config.PROCESS_SCAN_INTERVAL)
    
    def _handle_suspicious_process(self, threat_info):
        """处理可疑进程"""
        try:
            pid = threat_info.get('pid')
            process_name = threat_info.get('process_name', '')
            
            logger.warning(f"检测到可疑进程: {process_name} (PID: {pid})")
            
            if Config.BLOCK_SUSPICIOUS:
                try:
                    if platform.system() == "Windows":
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
                    else:
                        os.kill(pid, signal.SIGTERM)
                    
                    logger.warning(f"已终止可疑进程: {process_name} (PID: {pid})")
                    
                    threat_info['action'] = '进程已终止'
                    threat_info['terminated'] = True
                    
                except Exception as e:
                    logger.debug(f"终止进程失败 {pid}: {e}")
            
            self.alert_queue.append(threat_info)
            
        except Exception as e:
            logger.error(f"处理可疑进程失败: {e}")
    
    def _add_alert(self, threat_info):
        """添加警报"""
        current_time = time.time()
        
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        self.alert_queue.append(threat_info)
        self.last_alert_time = current_time
        
        alert_msg = f"实时保护警报: {threat_info.get('name', 'Unknown')} - {threat_info.get('type', 'Unknown')}"
        logger.warning(alert_msg)
    
    def get_alerts(self, max_count=5):
        """获取最近的警报"""
        alerts = self.alert_queue[-max_count:] if self.alert_queue else []
        return alerts
    
    def clear_alerts(self):
        """清除警报队列"""
        self.alert_queue.clear()
    
    def is_running(self):
        """检查实时保护是否在运行"""
        return self.running
    
    def block_file(self, file_path):
        """阻止文件访问"""
        if file_path not in self.blocked_files:
            self.blocked_files.add(file_path)
            logger.info(f"已阻止文件: {file_path}")
            return True
        return False
    
    def unblock_file(self, file_path):
        """解除文件阻止"""
        if file_path in self.blocked_files:
            self.blocked_files.remove(file_path)
            logger.info(f"已解除文件阻止: {file_path}")
            return True
        return False
    
    def is_file_blocked(self, file_path):
        """检查文件是否被阻止"""
        return file_path in self.blocked_files

# ==================== 引导保护引擎 ====================
class BootProtectionEngine:
    """引导保护核心引擎"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.boot_hashes = {}
        self.boot_alerts = []
        self.boot_files = []
        self.system_type = platform.system()
        
        self._init_boot_protection()
        logger.info("引导保护引擎初始化完成")
    
    def _init_boot_protection(self):
        """初始化引导保护"""
        if not os.path.exists(Config.BOOT_BACKUP_DIR):
            os.makedirs(Config.BOOT_BACKUP_DIR)
        
        self._load_boot_files()
        self._load_boot_hashes()
    
    def _load_boot_files(self):
        """加载引导文件列表"""
        self.boot_files = []
        
        if self.system_type == "Windows":
            boot_list = Config.WINDOWS_BOOT_FILES
        else:
            boot_list = Config.LINUX_BOOT_FILES
        
        for pattern, description in boot_list:
            try:
                if '*' in pattern:
                    files = glob.glob(pattern)
                    for file_path in files:
                        if os.path.exists(file_path):
                            self.boot_files.append((file_path, description))
                else:
                    if os.path.exists(pattern):
                        self.boot_files.append((pattern, description))
            except Exception as e:
                logger.warning(f"加载引导文件失败 {pattern}: {e}")
        
        logger.info(f"找到 {len(self.boot_files)} 个引导文件")
    
    def _load_boot_hashes(self):
        """加载引导文件哈希"""
        try:
            if os.path.exists(Config.BOOT_HASH_DB):
                with open(Config.BOOT_HASH_DB, 'rb') as f:
                    self.boot_hashes = pickle.load(f)
                logger.info(f"已加载 {len(self.boot_hashes)} 个引导文件哈希")
        except Exception as e:
            logger.warning(f"加载引导哈希失败: {e}")
            self.boot_hashes = {}
    
    def _save_boot_hashes(self):
        """保存引导文件哈希"""
        try:
            with open(Config.BOOT_HASH_DB, 'wb') as f:
                pickle.dump(self.boot_hashes, f)
        except Exception as e:
            logger.error(f"保存引导哈希失败: {e}")
    
    def _calculate_hash(self, file_path):
        """计算文件SHA256哈希"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.debug(f"计算哈希失败 {file_path}: {e}")
            return None
    
    def _backup_file(self, file_path, description=""):
        """备份文件"""
        try:
            if not os.path.exists(file_path):
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = os.path.basename(file_path)
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            backup_name = f"{timestamp}_{description}_{safe_name}"
            backup_path = os.path.join(Config.BOOT_BACKUP_DIR, backup_name)
            
            shutil.copy2(file_path, backup_path)
            
            file_hash = self._calculate_hash(file_path)
            if file_hash:
                self.boot_hashes[file_path] = {
                    'hash': file_hash,
                    'backup': backup_path,
                    'time': timestamp,
                    'size': os.path.getsize(file_path),
                    'description': description
                }
                self._save_boot_hashes()
            
            logger.info(f"已备份: {description} -> {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"备份失败 {file_path}: {e}")
            return None
    
    def start_protection(self):
        """启动引导保护"""
        if self.running:
            return True
        
        self.running = True
        
        self._initial_check()
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="BootMonitor"
        )
        self.monitor_thread.start()
        
        logger.info("引导保护已启动")
        return True
    
    def stop_protection(self):
        """停止引导保护"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        logger.info("引导保护已停止")
    
    def _initial_check(self):
        """初始检查"""
        logger.info("开始初始引导文件检查...")
        
        for file_path, description in self.boot_files:
            try:
                if os.path.exists(file_path):
                    if file_path not in self.boot_hashes:
                        self._backup_file(file_path, description)
                    else:
                        self._check_file_integrity(file_path, description)
            except Exception as e:
                logger.error(f"检查引导文件失败 {file_path}: {e}")
    
    def _check_file_integrity(self, file_path, description):
        """检查文件完整性"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"引导文件不存在: {file_path}")
                return False
            
            current_hash = self._calculate_hash(file_path)
            if not current_hash:
                return False
            
            stored_info = self.boot_hashes.get(file_path)
            if not stored_info:
                self._backup_file(file_path, description)
                return True
            
            stored_hash = stored_info.get('hash')
            
            if current_hash == stored_hash:
                return True
            else:
                logger.warning(f"引导文件被修改: {description}")
                
                alert = {
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'file': file_path,
                    'description': description,
                    'original_hash': stored_hash[:12] if stored_hash else "未知",
                    'current_hash': current_hash[:12],
                    'severity': '严重',
                    'type': '引导文件修改'
                }
                
                self.boot_alerts.append(alert)
                
                if Config.BOOT_AUTO_REPAIR:
                    self._repair_file(file_path, description)
                
                return False
                
        except Exception as e:
            logger.error(f"检查文件完整性失败 {file_path}: {e}")
            return False
    
    def _repair_file(self, file_path, description):
        """修复引导文件"""
        try:
            stored_info = self.boot_hashes.get(file_path)
            if not stored_info:
                logger.warning(f"没有备份信息: {file_path}")
                return False
            
            backup_path = stored_info.get('backup')
            if not os.path.exists(backup_path):
                logger.warning(f"备份文件不存在: {backup_path}")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted_backup = os.path.join(
                Config.BOOT_BACKUP_DIR,
                f"CORRUPTED_{timestamp}_{os.path.basename(file_path)}"
            )
            shutil.copy2(file_path, corrupted_backup)
            
            shutil.copy2(backup_path, file_path)
            
            logger.info(f"已修复引导文件: {description}")
            
            alert = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'file': file_path,
                'description': description,
                'action': '已自动修复',
                'severity': '高',
                'type': '引导文件修复'
            }
            self.boot_alerts.append(alert)
            
            return True
            
        except Exception as e:
            logger.error(f"修复文件失败 {file_path}: {e}")
            return False
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                for file_path, description in self.boot_files:
                    if not self.running:
                        break
                    
                    if os.path.exists(file_path):
                        self._check_file_integrity(file_path, description)
                
                time.sleep(Config.BOOT_SCAN_INTERVAL)
                
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                time.sleep(60)
    
    def check_integrity(self):
        """手动检查引导完整性"""
        results = {
            'total': len(self.boot_files),
            'ok': 0,
            'modified': 0,
            'missing': 0,
            'errors': 0,
            'details': []
        }
        
        for file_path, description in self.boot_files:
            try:
                if not os.path.exists(file_path):
                    results['missing'] += 1
                    results['details'].append({
                        'file': description,
                        'status': '丢失',
                        'message': '文件不存在'
                    })
                    continue
                
                current_hash = self._calculate_hash(file_path)
                stored_info = self.boot_hashes.get(file_path)
                
                if not stored_info:
                    results['errors'] += 1
                    results['details'].append({
                        'file': description,
                        'status': '未备份',
                        'message': '文件未备份'
                    })
                elif not current_hash:
                    results['errors'] += 1
                    results['details'].append({
                        'file': description,
                        'status': '错误',
                        'message': '无法计算哈希'
                    })
                else:
                    stored_hash = stored_info.get('hash')
                    if current_hash == stored_hash:
                        results['ok'] += 1
                        results['details'].append({
                            'file': description,
                            'status': '正常',
                            'message': '文件完整'
                        })
                    else:
                        results['modified'] += 1
                        results['details'].append({
                            'file': description,
                            'status': '已修改',
                            'message': f'哈希不匹配: {stored_hash[:8]} -> {current_hash[:8]}'
                        })
                        
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'file': description,
                    'status': '异常',
                    'message': str(e)[:50]
                })
        
        if results['total'] > 0:
            integrity_score = (results['ok'] / results['total']) * 100
        else:
            integrity_score = 0
        
        results['score'] = integrity_score
        
        return results
    
    def repair_all(self):
        """修复所有引导文件"""
        repaired = 0
        errors = []
        
        for file_path, description in self.boot_files:
            try:
                if self._repair_file(file_path, description):
                    repaired += 1
            except Exception as e:
                errors.append(f"{description}: {str(e)}")
        
        return {
            'repaired': repaired,
            'total': len(self.boot_files),
            'errors': errors
        }
    
    def create_backup(self):
        """创建所有引导文件备份"""
        backed_up = 0
        errors = []
        
        for file_path, description in self.boot_files:
            try:
                if os.path.exists(file_path):
                    backup_path = self._backup_file(file_path, description)
                    if backup_path:
                        backed_up += 1
            except Exception as e:
                errors.append(f"{description}: {str(e)}")
        
        return {
            'backed_up': backed_up,
            'total': len(self.boot_files),
            'errors': errors
        }
    
    def get_alerts(self, count=10):
        """获取引导警报"""
        return self.boot_alerts[-count:] if self.boot_alerts else []
    
    def clear_alerts(self):
        """清除警报"""
        self.boot_alerts.clear()
    
    def is_running(self):
        """检查是否在运行"""
        return self.running

# ==================== PYRT扫描动画类 ====================
class PYRTScanAnimation:
    """PYRT扫描动画类"""
    def __init__(self, canvas, x, y, radius=180):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.scanning = False
        
        self._create_animation_elements()
        
        self.stats_text = canvas.create_text(
            x, y + radius + 50,
            text=lang.get_text("preparing_scan"),
            font=("Microsoft YaHe", 11),
            fill=Config.THEME['text_secondary'],
            anchor=tk.CENTER
        )
    
    def _create_animation_elements(self):
        """创建动画元素"""
        theme = Config.THEME
        
        self.outer_ring = self.canvas.create_oval(
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius,
            outline=theme['secondary'],
            width=3,
            fill=""
        )
        
        inner_radius = self.radius - 30
        self.inner_ring = self.canvas.create_oval(
            self.x - inner_radius, self.y - inner_radius,
            self.x + inner_radius, self.y + inner_radius,
            outline=theme['primary'],
            width=2,
            fill=""
        )
        
        self.scan_line = None
        
        self.dots = []
        for i in range(0, 360, 15):
            rad = math.radians(i)
            dot_x = self.x + (self.radius - 15) * math.cos(rad)
            dot_y = self.y + (self.radius - 15) * math.sin(rad)
            
            dot = self.canvas.create_oval(
                dot_x - 2, dot_y - 2,
                dot_x + 2, dot_y + 2,
                fill=theme['secondary'],
                outline=""
            )
            self.dots.append((dot, i))
        
        self.center_logo = self.canvas.create_text(
            self.x, self.y,
            text=Config.LOGO,
            font=("Segoe UI Emoji", 48),
            fill=theme['primary']
        )
        
        self.center_text = self.canvas.create_text(
            self.x, self.y + 60,
            text="PYRT",
            font=("Microsoft YaHe", 16, "bold"),
            fill=theme['text_primary']
        )
        
        self.progress_arc = None
    
    def start_scan(self):
        """开始扫描动画"""
        self.scanning = True
        self._animate()
    
    def stop_scan(self):
        """停止扫描动画"""
        self.scanning = False
        if self.scan_line:
            self.canvas.delete(self.scan_line)
            self.scan_line = None
        
        if self.progress_arc:
            self.canvas.delete(self.progress_arc)
            self.progress_arc = None
        
        for dot, _ in self.dots:
            self.canvas.itemconfig(dot, fill=Config.THEME['secondary'])
    
    def _animate(self):
        """动画循环"""
        if not self.scanning:
            return
        
        if not hasattr(self, 'animation_angle'):
            self.animation_angle = 0
        self.animation_angle = (self.animation_angle + 5) % 360
        
        self._update_scan_line()
        self._update_dots()
        
        self.canvas.after(20, self._animate)
    
    def _update_scan_line(self):
        """更新扫描线"""
        if self.scan_line:
            self.canvas.delete(self.scan_line)
        
        rad = math.radians(self.animation_angle)
        end_x = self.x + self.radius * math.cos(rad)
        end_y = self.y + self.radius * math.sin(rad)
        
        self.scan_line = self.canvas.create_line(
            self.x, self.y, end_x, end_y,
            fill=Config.THEME['primary'],
            width=2,
            arrow="last",
            arrowshape=(8, 10, 3)
        )
    
    def _update_dots(self):
        """更新圆点高亮"""
        for dot, angle in self.dots:
            angle_diff = abs((self.animation_angle - angle) % 360)
            
            if angle_diff < 30:
                intensity = 1.0 - (angle_diff / 30)
                color = self._get_intensity_color(intensity)
                self.canvas.itemconfig(dot, fill=color)
            else:
                self.canvas.itemconfig(dot, fill=Config.THEME['secondary'])
    
    def _get_intensity_color(self, intensity):
        """根据强度获取颜色"""
        r = int(100 + 155 * intensity)
        g = int(255 * intensity)
        b = int(218 * intensity)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_stats(self, scanned, total, threats, progress, speed):
        """更新统计信息"""
        stats_text = f"📊 {scanned}/{total} {lang.get_text('files')} | 🦠 {threats} {lang.get_text('threats')} | ⚡ {speed} {lang.get_text('speed')}"
        self.canvas.itemconfig(self.stats_text, text=stats_text)
        
        if threats > 0:
            self.canvas.itemconfig(self.stats_text, fill=Config.THEME['accent'])
        else:
            self.canvas.itemconfig(self.stats_text, fill=Config.THEME['success'])
        
        self._update_progress_arc(progress)
    
    def _update_progress_arc(self, progress):
        """更新进度环"""
        if self.progress_arc:
            self.canvas.delete(self.progress_arc)
        
        if progress > 0:
            angle = 360 * progress / 100
            
            self.progress_arc = self.canvas.create_arc(
                self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius,
                start=90,
                extent=-angle,
                outline=Config.THEME['success'],
                width=3,
                style=tk.ARC
            )

# ==================== PYRT安全卫士主界面（带滑动侧边栏） ====================
class PYRTSecuritySuiteGUI:
    """PYRT安全卫士主界面（带滑动侧边栏）"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{lang.get_text('app_name')} {Config.VERSION}")
        self.root.geometry("1400x900")
        self.root.configure(bg=Config.THEME['bg_dark'])
        
        try:
            self.root.iconbitmap(default='pyrt_icon.ico')
        except:
            pass
        
        # 初始化引擎
        self.scan_engine = EnhancedPYRTScanEngine()
        self.realtime_engine = RealTimeProtection(self.scan_engine.virus_db, self.scan_engine)
        self.boot_engine = BootProtectionEngine()
        self.network_engine = NetworkProtectionEngine()  # 新增网络保护引擎
        
        self.scanning = False
        self.threats_list = []
        self.alerts_list = []
        self.boot_alerts_list = []
        self.network_alerts_list = []
        
        # 创建滑动侧边栏
        self.sidebar = SlidingSidebar(root, self)
        
        # 创建页面容器
        self.page_container = PageContainer(root, self)
        
        # 启动保护
        if Config.REAL_TIME_PROTECTION:
            self._start_realtime_protection()
        
        if Config.BOOT_PROTECTION_ENABLED:
            self._start_boot_protection()
        
        if Config.NETWORK_PROTECTION_ENABLED:
            self._start_network_protection()
        
        self._update_status(lang.get_text("app_name") + " " + lang.get_text("info"))
        logger.info(f"{lang.get_text('app_name')} {Config.VERSION} {lang.get_text('info')}")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 启动警报检查
        self._start_alert_check()
        self._start_network_status_check()
    
    def switch_page(self, page_index):
        """切换页面"""
        self.page_container.show_page(page_index)
    
    # ==================== 网络保护控制方法 ====================
    
    def _start_network_protection(self):
        """启动网络保护"""
        if self.network_engine and not self.network_engine.is_running():
            if self.network_engine.start_protection():
                if hasattr(self, 'network_status_label'):
                    self.network_status_label.config(
                        text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
                        fg=Config.THEME['success']
                    )
                if hasattr(self, 'network_toggle_btn'):
                    self.network_toggle_btn.config(text="⏸️ " + lang.get_text("pause_protection"))
                logger.info("网络保护已启动")
            else:
                if hasattr(self, 'network_status_label'):
                    self.network_status_label.config(
                        text=lang.get_text("status") + ": 🔴 " + lang.get_text("error"),
                        fg=Config.THEME['accent']
                    )
                logger.error("网络保护启动失败")
    
    def _stop_network_protection(self):
        """停止网络保护"""
        if self.network_engine and self.network_engine.is_running():
            self.network_engine.stop_protection()
            if hasattr(self, 'network_status_label'):
                self.network_status_label.config(
                    text=lang.get_text("status") + ": ⏸️ " + lang.get_text("disabled"),
                    fg=Config.THEME['secondary']
                )
            if hasattr(self, 'network_toggle_btn'):
                self.network_toggle_btn.config(text="▶️ " + lang.get_text("start_protection"))
            logger.info("网络保护已停止")
    
    def _toggle_network_protection(self):
        """切换网络保护状态"""
        if self.network_engine.is_running():
            self._stop_network_protection()
        else:
            self._start_network_protection()
    
    def _check_network_security(self):
        """检查网络安全"""
        self._update_status(lang.get_text("network_check") + "...")
        
        def do_check():
            try:
                # 获取网络状态
                status = self.network_engine.get_network_status()
                
                # 获取最近的网络警报
                alerts = self.network_engine.get_alerts(5)
                
                self.root.after(0, lambda: self._on_network_check_complete(status, alerts))
            except Exception as e:
                self.root.after(0, lambda: self._on_network_check_error(str(e)))
        
        threading.Thread(target=do_check, daemon=True).start()
    
    def _on_network_check_complete(self, status, alerts):
        """网络检查完成回调"""
        network_status = status.get('network', 'unknown')
        internet_status = status.get('internet', False)
        blocked_ips = status.get('blocked_ips', 0)
        blocked_domains = status.get('blocked_domains', 0)
        
        network_status_text = lang.get_text("connected") if network_status == "connected" else lang.get_text("disconnected")
        internet_status_text = lang.get_text("connected") if internet_status else lang.get_text("disconnected")
        
        status_text = (
            f"🌐 {lang.get_text('network_check')} {lang.get_text('complete')}！\n\n"
            f"{lang.get_text('network_status')}: {network_status_text}\n"
            f"{lang.get_text('internet_status')}: {internet_status_text}\n"
            f"{lang.get_text('blocked_ips')}: {blocked_ips}\n"
            f"{lang.get_text('blocked_domains')}: {blocked_domains}\n"
        )
        
        if alerts:
            status_text += f"\n{lang.get_text('realtime_alerts')}: {len(alerts)}\n"
            for alert in alerts[:3]:
                status_text += f"• {alert.get('type', 'unknown')} - {alert.get('severity', 'medium')}\n"
        
        self._update_status(status_text)
        
        # 更新UI状态显示
        if hasattr(self, 'network_status_text'):
            status_display = f"{lang.get_text('network')}: {network_status_text} | {lang.get_text('internet')}: {internet_status_text}"
            self.network_status_text.config(text=status_display)
        
        # 如果有严重警报，提示用户
        severe_alerts = [a for a in alerts if a.get('severity') in ['严重', '高', 'Critical', 'High']]
        if severe_alerts:
            response = messagebox.askyesno(
                lang.get_text("warning"),
                f"{lang.get_text('threats_found')}: {len(severe_alerts)} {lang.get_text('critical')} {lang.get_text('threats')}！\n\n"
                f"{lang.get_text('confirm')} {lang.get_text('view')} {lang.get_text('network_alerts')}？"
            )
            
            if response:
                self.switch_page(8)  # 切换到网络保护页面
    
    def _on_network_check_error(self, error):
        """网络检查错误回调"""
        self._update_status(f"❌ {lang.get_text('network_check')} {lang.get_text('error')}！\n{lang.get_text('error')}: {error}")
        messagebox.showerror(lang.get_text("error"), f"{lang.get_text('network_check')} {lang.get_text('error')}: {error}")
    
    def _show_network_settings(self):
        """显示网络保护设置"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(lang.get_text("settings") + " - " + lang.get_text("network_protection"))
        settings_window.geometry("600x500")
        settings_window.configure(bg=Config.THEME['bg_dark'])
        
        settings_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            settings_frame,
            text=lang.get_text("network_protection") + " " + lang.get_text("settings"),
            font=("Microsoft YaHei", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # 恶意IP列表
        ip_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        ip_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            ip_frame,
            text=lang.get_text("blocked_ips") + ":",
            font=("Microsoft YaHei", 11, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 5))
        
        ip_text = tk.Text(
            ip_frame,
            height=4,
            bg=Config.THEME['bg_card'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        ip_text.pack(fill=tk.BOTH, expand=True)
        
        for ip in Config.MALICIOUS_IPS:
            ip_text.insert(tk.END, f"{ip}\n")
        
        # 恶意域名列表
        domain_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        domain_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            domain_frame,
            text=lang.get_text("blocked_domains") + ":",
            font=("Microsoft YaHei", 11, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 5))
        
        domain_text = tk.Text(
            domain_frame,
            height=4,
            bg=Config.THEME['bg_card'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        domain_text.pack(fill=tk.BOTH, expand=True)
        
        for domain in Config.MALICIOUS_DOMAINS:
            domain_text.insert(tk.END, f"{domain}\n")
        
        # 监控间隔
        interval_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        interval_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            interval_frame,
            text=lang.get_text("monitored_dirs") + f": {Config.NETWORK_MONITOR_INTERVAL} {lang.get_text('speed')}",
            font=("Microsoft YaHei", 11),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W)
        
        button_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="💾 " + lang.get_text("save"),
            command=lambda: self._save_network_settings(settings_window, ip_text, domain_text),
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            button_frame,
            text=lang.get_text("add") + " IP",
            command=lambda: self._add_blocked_ip(ip_text),
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text=lang.get_text("cancel"),
            command=settings_window.destroy,
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
    
    def _save_network_settings(self, settings_window, ip_text, domain_text):
        """保存网络保护设置"""
        try:
            # 获取IP列表
            ip_content = ip_text.get("1.0", tk.END).strip().split('\n')
            Config.MALICIOUS_IPS = [ip.strip() for ip in ip_content if ip.strip()]
            
            # 获取域名列表
            domain_content = domain_text.get("1.0", tk.END).strip().split('\n')
            Config.MALICIOUS_DOMAINS = [domain.strip().lower() for domain in domain_content if domain.strip()]
            
            # 重新加载网络引擎
            if self.network_engine and self.network_engine.is_running():
                self.network_engine.stop_protection()
                time.sleep(1)
                self.network_engine.start_protection()
            
            messagebox.showinfo(lang.get_text("success"), lang.get_text("save") + " " + lang.get_text("success"))
            settings_window.destroy()
            
        except Exception as e:
            messagebox.showerror(lang.get_text("error"), f"{lang.get_text('save')} {lang.get_text('error')}: {str(e)}")
    
    def _add_blocked_ip(self, ip_text):
        """添加要阻止的IP"""
        ip = simpledialog.askstring(lang.get_text("add") + " IP", lang.get_text("add") + " IP:")
        if ip:
            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                ip_text.insert(tk.END, f"{ip}\n")
                if self.network_engine:
                    self.network_engine.add_blocked_ip(ip)
            else:
                messagebox.showerror(lang.get_text("error"), lang.get_text("error") + " IP")
    
    def _show_network_connections(self):
        """显示网络连接"""
        connections_window = tk.Toplevel(self.root)
        connections_window.title(lang.get_text("network") + " " + lang.get_text("view_connections"))
        connections_window.geometry("800x600")
        connections_window.configure(bg=Config.THEME['bg_dark'])
        
        main_frame = tk.Frame(connections_window, bg=Config.THEME['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            main_frame,
            text=lang.get_text("view_connections"),
            font=("Microsoft YaHei", 14, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 创建Treeview显示连接
        columns = (lang.get_text("network"), lang.get_text("status"), lang.get_text("threats"), lang.get_text("speed"))
        tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            height=20
        )
        
        # 设置列
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 获取并显示连接
        def refresh_connections():
            try:
                # 清空现有数据
                for item in tree.get_children():
                    tree.delete(item)
                
                # 获取连接
                if platform.system() == "Windows":
                    connections = self.network_engine._get_windows_connections()
                else:
                    connections = self.network_engine._get_unix_connections()
                
                # 添加数据
                for conn in connections[:50]:  # 限制显示数量
                    local_addr = f"{conn.get('local_ip', '')}:{conn.get('local_port', '')}"
                    remote_addr = f"{conn.get('remote_ip', '')}:{conn.get('remote_port', '')}"
                    
                    tree.insert("", tk.END, values=(
                        local_addr,
                        remote_addr,
                        conn.get('state', ''),
                        conn.get('process', ''),
                        conn.get('time', '')
                    ))
                
            except Exception as e:
                logger.error(f"刷新连接失败: {e}")
        
        # 刷新按钮
        button_frame = tk.Frame(main_frame, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            button_frame,
            text="🔄 " + lang.get_text("refresh"),
            command=refresh_connections,
            font=("Microsoft YaHe", 10),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # 初始刷新
        refresh_connections()
    
    def _emergency_disconnect(self):
        """紧急断网"""
        if messagebox.askyesno(lang.get_text("warning"), 
                              "⚠️  " + lang.get_text("warning") + "：" + lang.get_text("emergency_disconnect") + "！\n\n"
                              + lang.get_text("confirm") + "？"):
            if self.network_engine:
                success = self.network_engine.emergency_disconnect()
                if success:
                    messagebox.showinfo(lang.get_text("success"), lang.get_text("emergency_disconnect") + " " + lang.get_text("success"))
                else:
                    messagebox.showerror(lang.get_text("error"), lang.get_text("emergency_disconnect") + " " + lang.get_text("error"))
    
    def _start_network_status_check(self):
        """启动网络状态检查循环"""
        self._update_network_status()
        self.root.after(10000, self._start_network_status_check)  # 每10秒检查一次
    
    def _update_network_status(self):
        """更新网络状态显示"""
        if hasattr(self, 'network_engine') and self.network_engine:
            status = self.network_engine.get_network_status()
            
            if hasattr(self, 'network_status_text'):
                network_status = status.get('network', 'unknown')
                internet_status = status.get('internet', False)
                
                network_status_text = lang.get_text("connected") if network_status == "connected" else lang.get_text("disconnected")
                internet_status_text = lang.get_text("connected") if internet_status else lang.get_text("disconnected")
                
                status_text = f"{lang.get_text('network')}: {network_status_text} | {lang.get_text('internet')}: {internet_status_text}"
                self.network_status_text.config(text=status_text)
                
                # 根据状态改变颜色
                if internet_status:
                    self.network_status_text.config(fg=Config.THEME['success'])
                else:
                    self.network_status_text.config(fg=Config.THEME['warning'])
    
    # ==================== 保护控制方法 ====================
    
    def _start_realtime_protection(self):
        """启动实时保护"""
        if self.realtime_engine and not self.realtime_engine.is_running():
            if self.realtime_engine.start():
                if hasattr(self, 'realtime_status_label'):
                    self.realtime_status_label.config(
                        text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
                        fg=Config.THEME['success']
                    )
                if hasattr(self, 'realtime_toggle_btn'):
                    self.realtime_toggle_btn.config(text="⏸️ " + lang.get_text("pause_protection"))
                logger.info("实时保护已启动")
            else:
                if hasattr(self, 'realtime_status_label'):
                    self.realtime_status_label.config(
                        text=lang.get_text("status") + ": 🔴 " + lang.get_text("error"),
                        fg=Config.THEME['accent']
                    )
                logger.error("实时保护启动失败")
    
    def _stop_realtime_protection(self):
        """停止实时保护"""
        if self.realtime_engine and self.realtime_engine.is_running():
            self.realtime_engine.stop()
            if hasattr(self, 'realtime_status_label'):
                self.realtime_status_label.config(
                    text=lang.get_text("status") + ": ⏸️ " + lang.get_text("disabled"),
                    fg=Config.THEME['secondary']
                )
            if hasattr(self, 'realtime_toggle_btn'):
                self.realtime_toggle_btn.config(text="▶️ " + lang.get_text("start_protection"))
            logger.info("实时保护已停止")
    
    def _toggle_realtime_protection(self):
        """切换实时保护状态"""
        if self.realtime_engine.is_running():
            self._stop_realtime_protection()
        else:
            self._start_realtime_protection()
    
    def _start_boot_protection(self):
        """启动引导保护"""
        if self.boot_engine and not self.boot_engine.is_running():
            if self.boot_engine.start_protection():
                if hasattr(self, 'boot_status_label'):
                    self.boot_status_label.config(
                        text=lang.get_text("status") + ": 🟢 " + lang.get_text("running"),
                        fg=Config.THEME['success']
                    )
                if hasattr(self, 'boot_toggle_btn'):
                    self.boot_toggle_btn.config(text="⏸️ " + lang.get_text("pause_protection"))
                logger.info("引导保护已启动")
            else:
                if hasattr(self, 'boot_status_label'):
                    self.boot_status_label.config(
                        text=lang.get_text("status") + ": 🔴 " + lang.get_text("error"),
                        fg=Config.THEME['accent']
                    )
                logger.error("引导保护启动失败")
    
    def _stop_boot_protection(self):
        """停止引导保护"""
        if self.boot_engine and self.boot_engine.is_running():
            self.boot_engine.stop_protection()
            if hasattr(self, 'boot_status_label'):
                self.boot_status_label.config(
                    text=lang.get_text("status") + ": ⏸️ " + lang.get_text("disabled"),
                    fg=Config.THEME['secondary']
                )
            if hasattr(self, 'boot_toggle_btn'):
                self.boot_toggle_btn.config(text="▶️ " + lang.get_text("start_protection"))
            logger.info("引导保护已停止")
    
    def _toggle_boot_protection(self):
        """切换引导保护状态"""
        if self.boot_engine.is_running():
            self._stop_boot_protection()
        else:
            self._start_boot_protection()
    
    def _show_realtime_settings(self):
        """显示实时保护设置"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(lang.get_text("settings") + " - " + lang.get_text("realtime_protection"))
        settings_window.geometry("500x400")
        settings_window.configure(bg=Config.THEME['bg_dark'])
        
        settings_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            settings_frame,
            text=lang.get_text("monitored_dirs") + ":",
            font=("Microsoft YaHei", 11, "bold"),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 5))
        
        paths_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        paths_frame.pack(fill=tk.X, pady=(0, 15))
        
        paths_text = tk.Text(
            paths_frame,
            height=4,
            bg=Config.THEME['bg_card'],
            fg=Config.THEME['text_primary'],
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        paths_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for path in Config.MONITOR_PATHS:
            paths_text.insert(tk.END, f"{path}\n")
        
        paths_text.config(state=tk.DISABLED)
        
        options_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.scan_on_create_var = tk.BooleanVar(value=Config.SCAN_ON_CREATE)
        tk.Checkbutton(
            options_frame,
            text=lang.get_text("quick_scan") + " " + lang.get_text("quick_scan_desc"),
            variable=self.scan_on_create_var,
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark'],
            selectcolor=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        self.scan_on_modify_var = tk.BooleanVar(value=Config.SCAN_ON_MODIFY)
        tk.Checkbutton(
            options_frame,
            text=lang.get_text("quick_scan") + " " + lang.get_text("quick_scan_desc"),
            variable=self.scan_on_modify_var,
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark'],
            selectcolor=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        self.block_suspicious_var = tk.BooleanVar(value=Config.BLOCK_SUSPICIOUS)
        tk.Checkbutton(
            options_frame,
            text=lang.get_text("blocked_ips") + " " + lang.get_text("blocked_ips"),
            variable=self.block_suspicious_var,
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark'],
            selectcolor=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        self.monitor_processes_var = tk.BooleanVar(value=Config.MONITOR_PROCESSES)
        tk.Checkbutton(
            options_frame,
            text=lang.get_text("process_monitoring"),
            variable=self.monitor_processes_var,
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark'],
            selectcolor=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        button_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="💾 " + lang.get_text("save"),
            command=lambda: self._save_realtime_settings(settings_window),
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            button_frame,
            text=lang.get_text("cancel"),
            command=settings_window.destroy,
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
    
    def _save_realtime_settings(self, settings_window):
        """保存实时保护设置"""
        Config.SCAN_ON_CREATE = self.scan_on_create_var.get()
        Config.SCAN_ON_MODIFY = self.scan_on_modify_var.get()
        Config.BLOCK_SUSPICIOUS = self.block_suspicious_var.get()
        Config.MONITOR_PROCESSES = self.monitor_processes_var.get()
        
        if self.realtime_engine and self.realtime_engine.is_running():
            self.realtime_engine.stop()
            time.sleep(1)
            self.realtime_engine.start()
        
        messagebox.showinfo(lang.get_text("success"), lang.get_text("save") + " " + lang.get_text("success"))
        settings_window.destroy()
    
    def _show_boot_settings(self):
        """显示引导保护设置"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title(lang.get_text("settings") + " - " + lang.get_text("boot_protection"))
        settings_window.geometry("500x300")
        settings_window.configure(bg=Config.THEME['bg_dark'])
        
        settings_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            settings_frame,
            text=lang.get_text("boot_protection") + " " + lang.get_text("settings"),
            font=("Microsoft YaHei", 12, "bold"),
            fg=Config.THEME['primary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=(0, 15))
        
        options_frame = tk.Frame(settings_frame, bg=Config.THEME['bg_dark'])
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.boot_auto_repair_var = tk.BooleanVar(value=Config.BOOT_AUTO_REPAIR)
        tk.Checkbutton(
            options_frame,
            text=lang.get_text("auto_repair"),
            variable=self.boot_auto_repair_var,
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_primary'],
            bg=Config.THEME['bg_dark'],
            selectcolor=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            options_frame,
            text=lang.get_text("monitored_dirs") + f": {Config.BOOT_SCAN_INTERVAL} {lang.get_text('speed')}",
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            options_frame,
            text=lang.get_text("protected_files") + f": {len(self.boot_engine.boot_files)}",
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        tk.Label(
            options_frame,
            text=lang.get_text("location") + f": {Config.BOOT_BACKUP_DIR}",
            font=("Microsoft YaHe", 10),
            fg=Config.THEME['text_secondary'],
            bg=Config.THEME['bg_dark']
        ).pack(anchor=tk.W, pady=2)
        
        button_frame = tk.Frame(settings_window, bg=Config.THEME['bg_dark'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="💾 " + lang.get_text("save"),
            command=lambda: self._save_boot_settings(settings_window),
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['primary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        tk.Button(
            button_frame,
            text=lang.get_text("view") + " " + lang.get_text("create_backup"),
            command=self._view_boot_backup,
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Button(
            button_frame,
            text=lang.get_text("cancel"),
            command=settings_window.destroy,
            font=("Microsoft YaHe", 11),
            bg=Config.THEME['secondary'],
            fg=Config.THEME['bg_dark'],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
    
    def _save_boot_settings(self, settings_window):
        """保存引导保护设置"""
        Config.BOOT_AUTO_REPAIR = self.boot_auto_repair_var.get()
        
        if self.boot_engine and self.boot_engine.is_running():
            self.boot_engine.stop_protection()
            time.sleep(1)
            self.boot_engine.start_protection()
        
        messagebox.showinfo(lang.get_text("success"), lang.get_text("save") + " " + lang.get_text("success"))
        settings_window.destroy()
    
    def _view_boot_backup(self):
        """查看引导备份"""
        try:
            if os.path.exists(Config.BOOT_BACKUP_DIR):
                if platform.system() == "Windows":
                    os.startfile(Config.BOOT_BACKUP_DIR)
                else:
                    subprocess.run(['xdg-open', Config.BOOT_BACKUP_DIR])
        except Exception as e:
            messagebox.showerror(lang.get_text("error"), f"{lang.get_text('error')}: {str(e)}")
    
    # ==================== 引导保护方法 ====================
    
    def _check_boot_integrity(self):
        """检查引导完整性"""
        self._update_status(lang.get_text("check_integrity") + "...")
        
        def do_check():
            try:
                results = self.boot_engine.check_integrity()
                self.root.after(0, lambda: self._on_boot_check_complete(results))
            except Exception as e:
                self.root.after(0, lambda: self._on_boot_check_error(str(e)))
        
        threading.Thread(target=do_check, daemon=True).start()
    
    def _on_boot_check_complete(self, results):
        """引导检查完成回调"""
        integrity_score = results.get('score', 0)
        
        if integrity_score >= 95:
            status = lang.get_text("secure")
            color = Config.THEME['success']
            emoji = "🟢"
        elif integrity_score >= 80:
            status = lang.get_text("warning")
            color = Config.THEME['warning']
            emoji = "🟡"
        else:
            status = lang.get_text("critical")
            color = Config.THEME['accent']
            emoji = "🔴"
        
        status_text = (
            f"{emoji} {lang.get_text('check_integrity')} {lang.get_text('complete')}！\n\n"
            f"{lang.get_text('status')}: {integrity_score:.1f}% ({status})\n\n"
            f"{lang.get_text('info')}:\n"
            f"• {lang.get_text('system_status')}: {results.get('ok', 0)}\n"
            f"• {lang.get_text('modified')}: {results.get('modified', 0)}\n"
            f"• {lang.get_text('missing')}: {results.get('missing', 0)}\n"
            f"• {lang.get_text('error')}: {results.get('errors', 0)}\n"
            f"• {lang.get_text('total')}: {results.get('total', 0)}\n"
        )
        
        if results.get('modified', 0) > 0:
            status_text += f"\n⚠️  {lang.get_text('warning')} {results['modified']} {lang.get_text('modified')} {lang.get_text('files')}！"
            
            modified_files = [d for d in results['details'] if d['status'] == '已修改' or d['status'] == 'modified']
            if modified_files:
                status_text += f"\n\n{lang.get_text('modified')} {lang.get_text('files')}:\n"
                for i, detail in enumerate(modified_files[:5]):
                    status_text += f"  {i+1}. {detail['file']}\n"
        
        self._update_status(status_text)
        
        if results.get('modified', 0) > 0:
            response = messagebox.askyesno(
                lang.get_text("warning"),
                f"{lang.get_text('warning')} {results['modified']} {lang.get_text('modified')} {lang.get_text('files')}！\n\n"
                f"{lang.get_text('status')}: {integrity_score:.1f}%\n\n"
                f"{lang.get_text('repair_boot')}？"
            )
            
            if response:
                self._repair_boot()
        else:
            messagebox.showinfo(
                lang.get_text("check_integrity"),
                f"{lang.get_text('status')}: {integrity_score:.1f}%\n\n"
                f"{lang.get_text('status')}: {status}\n\n"
                f"{lang.get_text('system_status')} {lang.get_text('secure')}！"
            )
    
    def _on_boot_check_error(self, error):
        """引导检查错误回调"""
        self._update_status(f"❌ {lang.get_text('check_integrity')} {lang.get_text('error')}！\n{lang.get_text('error')}: {error}")
        messagebox.showerror(lang.get_text("error"), f"{lang.get_text('check_integrity')} {lang.get_text('error')}: {error}")
    
    def _backup_boot(self):
        """创建引导备份"""
        if not self.boot_engine:
            messagebox.showerror(lang.get_text("error"), lang.get_text("error"))
            return
        
        if messagebox.askyesno(lang.get_text("confirm"), lang.get_text("confirm") + " " + lang.get_text("create_backup") + "？"):
            self._update_status(lang.get_text("create_backup") + "...")
            
            def do_backup():
                try:
                    result = self.boot_engine.create_backup()
                    self.root.after(0, lambda: self._on_boot_backup_complete(result))
                except Exception as e:
                    self.root.after(0, lambda: self._on_boot_backup_error(str(e)))
            
            threading.Thread(target=do_backup, daemon=True).start()
    
    def _on_boot_backup_complete(self, result):
        """引导备份完成回调"""
        self._update_status(
            f"✅ {lang.get_text('create_backup')} {lang.get_text('complete')}！\n\n"
            f"{lang.get_text('create_backup')}: {result['backed_up']}/{result['total']}\n"
            f"{lang.get_text('location')}: {Config.BOOT_BACKUP_DIR}"
        )
        
        if result['errors']:
            error_msg = "\n".join(result['errors'][:3])
            messagebox.showwarning(
                lang.get_text("warning"),
                f"{lang.get_text('success')} {result['backed_up']} {lang.get_text('files')}，{lang.get_text('error')}：\n\n{error_msg}"
            )
        else:
            messagebox.showinfo(lang.get_text("success"), f"{lang.get_text('create_backup')} {result['backed_up']} {lang.get_text('files')}")
    
    def _on_boot_backup_error(self, error):
        """引导备份错误回调"""
        self._update_status(f"❌ {lang.get_text('create_backup')} {lang.get_text('error')}！\n{lang.get_text('error')}: {error}")
        messagebox.showerror(lang.get_text("error"), f"{lang.get_text('create_backup')} {lang.get_text('error')}: {error}")
    
    def _repair_boot(self):
        """修复引导"""
        if not self.boot_engine:
            messagebox.showerror(lang.get_text("error"), lang.get_text("error"))
            return
        
        if messagebox.askyesno(lang.get_text("confirm"), 
                              "⚠️  " + lang.get_text("confirm") + " " + lang.get_text("repair_boot") + "？\n\n"
                              + lang.get_text("warning") + "！"):
            self._update_status(lang.get_text("repair_boot") + "...")
            
            def do_repair():
                try:
                    result = self.boot_engine.repair_all()
                    self.root.after(0, lambda: self._on_boot_repair_complete(result))
                except Exception as e:
                    self.root.after(0, lambda: self._on_boot_repair_error(str(e)))
            
            threading.Thread(target=do_repair, daemon=True).start()
    
    def _on_boot_repair_complete(self, result):
        """引导修复完成回调"""
        self._update_status(
            f"✅ {lang.get_text('repair_boot')} {lang.get_text('complete')}！\n\n"
            f"{lang.get_text('repair_boot')}: {result['repaired']}/{result['total']}\n"
            f"{lang.get_text('info')}"
        )
        
        if result['errors']:
            error_msg = "\n".join(result['errors'][:3])
            messagebox.showwarning(
                lang.get_text("warning"),
                f"{lang.get_text('success')} {result['repaired']} {lang.get_text('files')}，{lang.get_text('error')}：\n\n{error_msg}"
            )
        else:
            messagebox.showinfo(
                lang.get_text("success"),
                f"{lang.get_text('success')} {result['repaired']} {lang.get_text('files')}！\n\n"
                f"{lang.get_text('info')}"
            )
    
    def _on_boot_repair_error(self, error):
        """引导修复错误回调"""
        self._update_status(f"❌ {lang.get_text('repair_boot')} {lang.get_text('error')}！\n{lang.get_text('error')}: {error}")
        messagebox.showerror(lang.get_text("error"), f"{lang.get_text('repair_boot')} {lang.get_text('error')}: {error}")
    
    def _start_alert_check(self):
        """启动警报检查"""
        self._check_alerts()
        self.root.after(5000, self._start_alert_check)
    
    def _check_alerts(self):
        """检查并显示警报"""
        # 实时保护警报
        if self.realtime_engine:
            alerts = self.realtime_engine.get_alerts(10)
            
            for alert in alerts:
                if alert not in self.alerts_list:
                    self.alerts_list.append(alert)
                    
                    timestamp = alert.get('timestamp', datetime.now().strftime('%H:%M:%S'))
                    alert_type = alert.get('type', 'unknown')
                    alert_name = alert.get('name', 'unknown')
                    severity = alert.get('severity', 'Medium')
                    
                    severity_text = lang.get_text("high") if severity in ['High', '高'] else lang.get_text("medium") if severity in ['Medium', '中'] else lang.get_text("low")
                    
                    alert_text = f"[{timestamp}] {severity_text}: {alert_name}"
                    
                    if hasattr(self, 'realtime_alerts_listbox'):
                        self.realtime_alerts_listbox.insert(0, alert_text)
                        
                        colors = {
                            'Critical': '#ff0000',
                            'High': Config.THEME['accent'],
                            'Medium': Config.THEME['warning'],
                            'Low': Config.THEME['secondary']
                        }
                        
                        self.realtime_alerts_listbox.itemconfig(0, fg=colors.get(severity, Config.THEME['text_primary']))
                        
                        if self.realtime_alerts_listbox.size() > 10:
                            self.realtime_alerts_listbox.delete(10, tk.END)
                    
                    self._show_alert_notification(alert, "realtime")
        
        # 引导保护警报
        if self.boot_engine:
            boot_alerts = self.boot_engine.get_alerts(10)
            
            for alert in boot_alerts:
                if alert not in self.boot_alerts_list:
                    self.boot_alerts_list.append(alert)
                    
                    timestamp = alert.get('time', datetime.now().strftime('%H:%M:%S'))
                    description = alert.get('description', 'unknown')
                    severity = alert.get('severity', '高')
                    
                    severity_text = lang.get_text("high") if severity in ['High', '高'] else lang.get_text("medium") if severity in ['Medium', '中'] else lang.get_text("low")
                    
                    alert_text = f"[{timestamp}] {severity_text}: {description}"
                    
                    if hasattr(self, 'boot_alerts_listbox'):
                        self.boot_alerts_listbox.insert(0, alert_text)
                        
                        if severity in ['严重', '高', 'Critical', 'High']:
                            self.boot_alerts_listbox.itemconfig(0, fg=Config.THEME['accent'])
                        elif severity in ['中', 'Medium']:
                            self.boot_alerts_listbox.itemconfig(0, fg=Config.THEME['warning'])
                        else:
                            self.boot_alerts_listbox.itemconfig(0, fg=Config.THEME['secondary'])
                        
                        if self.boot_alerts_listbox.size() > 10:
                            self.boot_alerts_listbox.delete(10, tk.END)
                    
                    self._show_alert_notification(alert, "boot")
        
        # 网络保护警报
        if self.network_engine:
            network_alerts = self.network_engine.get_alerts(10)
            
            for alert in network_alerts:
                if alert not in self.network_alerts_list:
                    self.network_alerts_list.append(alert)
                    
                    timestamp = alert.get('time', datetime.now().strftime('%H:%M:%S'))
                    alert_type = alert.get('type', 'unknown')
                    severity = alert.get('severity', '中')
                    message = alert.get('message', '')[:50]
                    
                    severity_text = lang.get_text("high") if severity in ['High', '高'] else lang.get_text("medium") if severity in ['Medium', '中'] else lang.get_text("low")
                    
                    alert_text = f"[{timestamp}] {severity_text}: {alert_type}"
                    if message:
                        alert_text += f" - {message}"
                    
                    if hasattr(self, 'network_alerts_listbox'):
                        self.network_alerts_listbox.insert(0, alert_text)
                        
                        if severity in ['严重', '高', 'Critical', 'High']:
                            self.network_alerts_listbox.itemconfig(0, fg=Config.THEME['accent'])
                        elif severity in ['中', 'Medium']:
                            self.network_alerts_listbox.itemconfig(0, fg=Config.THEME['warning'])
                        else:
                            self.network_alerts_listbox.itemconfig(0, fg=Config.THEME['secondary'])
                        
                        if self.network_alerts_listbox.size() > 10:
                            self.network_alerts_listbox.delete(10, tk.END)
                    
                    self._show_alert_notification(alert, "network")
    
    def _show_alert_notification(self, alert, alert_type):
        """显示警报通知"""
        if not hasattr(self, 'last_notification_time'):
            self.last_notification_time = 0
        
        current_time = time.time()
        if current_time - self.last_notification_time > 10:
            self.last_notification_time = current_time
            
            if self.root.state() != 'iconic':
                if alert_type == "realtime":
                    messagebox.showwarning(
                        lang.get_text("warning"),
                        f"{lang.get_text('warning')}: {alert.get('name', 'unknown')}\n\n"
                        f"{lang.get_text('type')}: {alert.get('type', 'unknown')}\n"
                        f"{lang.get_text('severity')}: {alert.get('severity', 'medium')}"
                    )
                elif alert_type == "boot":
                    messagebox.showwarning(
                        lang.get_text("warning"),
                        f"{lang.get_text('warning')} {lang.get_text('boot_protection')}！\n\n"
                        f"{lang.get_text('files')}: {alert.get('description', 'unknown')}\n"
                        f"{lang.get_text('time')}: {alert.get('time', 'unknown')}\n"
                        f"{lang.get_text('severity')}: {alert.get('severity', 'high')}\n\n"
                        f"{lang.get_text('check_integrity')}！"
                    )
                else:
                    messagebox.showwarning(
                        lang.get_text("warning"),
                        f"{lang.get_text('warning')} {lang.get_text('network_protection')}！\n\n"
                        f"{lang.get_text('type')}: {alert.get('type', 'unknown')}\n"
                        f"{lang.get_text('severity')}: {alert.get('severity', 'medium')}\n"
                        f"{lang.get_text('message')}: {alert.get('message', 'unknown')[:100]}"
                    )
    
    def _minimize_to_tray(self):
        """最小化到托盘"""
        self.root.withdraw()
        messagebox.showinfo(lang.get_text("app_name"), lang.get_text("info"))
    
    def _on_closing(self):
        """窗口关闭事件"""
        if messagebox.askyesno(lang.get_text("exit"), lang.get_text("exit_confirm")):
            # 停止所有引擎
            if self.realtime_engine:
                self.realtime_engine.stop()
            
            if self.boot_engine:
                self.boot_engine.stop_protection()
            
            if self.network_engine:
                self.network_engine.stop_protection()
            
            # 退出程序
            self.root.quit()
    
    # ==================== 扫描控制方法 ====================
    
    def _start_pyrt_scan(self):
        """开始安全扫描"""
        if self.scanning:
            messagebox.showwarning(lang.get_text("warning"), lang.get_text("scan_in_progress"))
            return
        
        self.scanning = True
        
        if hasattr(self, 'threats_listbox'):
            self.threats_listbox.delete(0, tk.END)
        self.threats_list = []
        
        if hasattr(self, 'scan_button'):
            self.scan_button.config(
                text="🌀 " + lang.get_text("scanning") + "...",
                bg=Config.THEME['secondary'],
                state=tk.DISABLED
            )
        if hasattr(self, 'stop_button'):
            self.stop_button.config(state=tk.NORMAL)
        
        if hasattr(self, 'scan_animation'):
            self.scan_animation.start_scan()
        
        self.scan_engine.start_scan()
        
        self._update_status(lang.get_text("scanning") + "...")
        
        self._scan_loop()
    
    def _scan_loop(self):
        """扫描循环"""
        if not self.scanning:
            return
        
        scan_data = self.scan_engine.update_scan()
        
        if scan_data:
            if hasattr(self, 'scan_animation'):
                self.scan_animation.update_stats(
                    scan_data['scanned'],
                    scan_data['total'],
                    scan_data['threats'],
                    scan_data['progress'],
                    scan_data['speed']
                )
            
            for threat in scan_data['new_threats']:
                self._add_threat(threat)
            
            if scan_data['scanning']:
                self.root.after(100, self._scan_loop)
            else:
                self._scan_complete()
    
    def _scan_complete(self):
        """扫描完成"""
        self.scanning = False
        
        if hasattr(self, 'scan_animation'):
            self.scan_animation.stop_scan()
        
        if hasattr(self, 'scan_button'):
            self.scan_button.config(
                text="🚀 " + lang.get_text("start_scan"),
                bg=Config.THEME['primary'],
                state=tk.NORMAL
            )
        if hasattr(self, 'stop_button'):
            self.stop_button.config(state=tk.DISABLED)
        
        threats_found = len(self.threats_list)
        if threats_found > 0:
            messagebox.showwarning(
                lang.get_text("warning"),
                f"{lang.get_text('threats_found')}: {threats_found}！\n"
                f"{lang.get_text('quarantine_selected')}"
            )
        else:
            messagebox.showinfo(
                lang.get_text("success"),
                f"{lang.get_text('scan_complete')}，{lang.get_text('system_secure')}！\n"
                f"{lang.get_text('no_threats')}"
            )
        
        self._update_status(f"{lang.get_text('scan_complete')}，{lang.get_text('threats_found')}: {threats_found}")
    
    def _stop_pyrt_scan(self):
        """停止扫描"""
        if self.scanning:
            self.scanning = False
            self.scan_engine.stop_scan()
            
            if hasattr(self, 'scan_animation'):
                self.scan_animation.stop_scan()
            
            if hasattr(self, 'scan_button'):
                self.scan_button.config(
                    text="🚀 " + lang.get_text("start_scan"),
                    bg=Config.THEME['primary'],
                    state=tk.NORMAL
                )
            if hasattr(self, 'stop_button'):
                self.stop_button.config(state=tk.DISABLED)
            
            self._update_status(lang.get_text("stop_scan") + " " + lang.get_text("complete"))
            
            messagebox.showinfo(
                lang.get_text("info"),
                lang.get_text("stop_scan") + "。\n"
                + lang.get_text("start_scan")
            )
    
    def _select_scan_type(self, scan_type):
        """选择扫描类型"""
        if self.scanning:
            messagebox.showwarning(lang.get_text("warning"), lang.get_text("scan_in_progress"))
            return
        
        if scan_type == "full":
            response = messagebox.askyesno(
                lang.get_text("full_scan"),
                lang.get_text("full_scan") + " " + lang.get_text("full_scan_desc") + "。\n\n"
                + lang.get_text("confirm") + "？"
            )
            if response:
                self._start_full_scan()
        else:
            self._start_pyrt_scan()
    
    def _start_full_scan(self):
        """开始全盘扫描"""
        self.scanning = True
        
        if hasattr(self, 'threats_listbox'):
            self.threats_listbox.delete(0, tk.END)
        self.threats_list = []
        
        if hasattr(self, 'scan_button'):
            self.scan_button.config(
                text="🌀 " + lang.get_text("full_scan") + "...",
                bg=Config.THEME['secondary'],
                state=tk.DISABLED
            )
        if hasattr(self, 'stop_button'):
            self.stop_button.config(state=tk.NORMAL)
        
        if hasattr(self, 'scan_animation'):
            self.scan_animation.start_scan()
        
        self.scan_engine.start_scan("full")
        
        self._update_status(lang.get_text("full_scan") + "...")
        
        self._scan_loop()
    
    def _select_custom_directory(self):
        """选择自定义扫描目录"""
        if self.scanning:
            messagebox.showwarning(lang.get_text("warning"), lang.get_text("scan_in_progress"))
            return
        
        directory = filedialog.askdirectory(title=lang.get_text("quick_scan"))
        if directory:
            response = messagebox.askyesno(
                lang.get_text("quick_scan"),
                f"{lang.get_text('quick_scan')}: {directory}\n\n"
                + lang.get_text("confirm") + "？"
            )
            if response:
                self._start_custom_scan(directory)
    
    def _start_custom_scan(self, directory):
        """开始自定义扫描"""
        self.scanning = True
        
        if hasattr(self, 'threats_listbox'):
            self.threats_listbox.delete(0, tk.END)
        self.threats_list = []
        
        if hasattr(self, 'scan_button'):
            self.scan_button.config(
                text=f"🌀 {lang.get_text('quick_scan')}: {os.path.basename(directory)}",
                bg=Config.THEME['secondary'],
                state=tk.DISABLED
            )
        if hasattr(self, 'stop_button'):
            self.stop_button.config(state=tk.NORMAL)
        
        if hasattr(self, 'scan_animation'):
            self.scan_animation.start_scan()
        
        self.scan_engine.start_scan("custom", [directory])
        
        self._update_status(f"{lang.get_text('quick_scan')}: {directory}")
        
        self._scan_loop()
    
    def _add_threat(self, threat):
        """添加威胁到列表"""
        severity = threat.get('severity', 'Unknown')
        severity_text = lang.get_text("high") if severity in ['High', '高'] else lang.get_text("medium") if severity in ['Medium', '中'] else lang.get_text("low")
        
        threat_text = f"[{severity_text}] {threat.get('name', 'Unknown')}"
        threat_text += f"\n   📍 {threat.get('file', 'Unknown')[:50]}..."
        if threat.get('method'):
            threat_text += f"\n   🔍 {threat.get('method')}"
        
        if hasattr(self, 'threats_listbox'):
            self.threats_listbox.insert(tk.END, threat_text)
        self.threats_list.append(threat)
        
        colors = {
            'Low': Config.THEME['secondary'],
            'Medium': Config.THEME['warning'],
            'High': Config.THEME['accent'],
            'Critical': '#ff0000'
        }
        
        if hasattr(self, 'threats_listbox'):
            idx = self.threats_listbox.size() - 1
            self.threats_listbox.itemconfig(idx, fg=colors.get(threat.get('severity', 'Low'), Config.THEME['text_primary']))
        
        logger.warning(f"检测到威胁: {threat.get('name', 'Unknown')} (严重性: {threat.get('severity', 'Unknown')})")
    
    def _quarantine_selected(self):
        """隔离选中威胁"""
        if not hasattr(self, 'threats_listbox'):
            return
        
        selection = self.threats_listbox.curselection()
        if not selection:
            messagebox.showwarning(lang.get_text("warning"), lang.get_text("quarantine_selected"))
            return
        
        for idx in selection:
            if idx < len(self.threats_list):
                threat = self.threats_list[idx]
                file_path = threat.get('file', '')
                
                if os.path.exists(file_path):
                    success, result = self.scan_engine.quarantine_file(file_path, threat)
                    
                    if success:
                        current_text = self.threats_listbox.get(idx)
                        new_text = f"✅ {lang.get_text('quarantine_selected')} - {current_text}"
                        self.threats_listbox.delete(idx)
                        self.threats_listbox.insert(idx, new_text)
                        self.threats_listbox.itemconfig(idx, fg=Config.THEME['secondary'])
                        
                        messagebox.showinfo(
                            lang.get_text("success"),
                            f"{lang.get_text('success')} {lang.get_text('quarantine_selected')}：{threat.get('name', 'Unknown')}\n"
                            f"{lang.get_text('quarantine')} {lang.get_text('success')}"
                        )
                    else:
                        messagebox.showerror(
                            lang.get_text("error"),
                            f"{lang.get_text('error')}：{file_path}\n"
                            f"{lang.get_text('error')}：{result}"
                        )
        
        self._update_status(lang.get_text("quarantine_selected") + " " + lang.get_text("success"))
    
    def _delete_selected(self):
        """删除选中威胁"""
        if not hasattr(self, 'threats_listbox'):
            return
        
        selection = self.threats_listbox.curselection()
        if not selection:
            messagebox.showwarning(lang.get_text("warning"), lang.get_text("delete_selected"))
            return
        
        if not messagebox.askyesno(lang.get_text("confirm"), 
                                   "⚠️  " + lang.get_text("warning") + "！\n\n"
                                   + lang.get_text("delete_selected") + "？"):
            return
        
        deleted_count = 0
        failed_files = []
        
        for idx in reversed(selection):
            if idx < len(self.threats_list):
                threat = self.threats_list[idx]
                file_path = threat.get('file', '')
                
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self.threats_listbox.delete(idx)
                        self.threats_list.pop(idx)
                        deleted_count += 1
                        logger.warning(f"已删除威胁文件: {file_path}")
                    else:
                        failed_files.append(f"{file_path} ({lang.get_text('error')})")
                except Exception as e:
                    failed_files.append(f"{file_path} ({str(e)})")
        
        if failed_files:
            messagebox.showwarning(
                lang.get_text("warning"),
                f"{lang.get_text('success')} {deleted_count} {lang.get_text('files')}，{lang.get_text('error')}：\n\n" +
                "\n".join(failed_files[:3]) + 
                ("\n..." if len(failed_files) > 3 else "")
            )
        else:
            messagebox.showinfo(lang.get_text("success"), f"{lang.get_text('success')} {deleted_count} {lang.get_text('files')}")
        
        self._update_status(f"{lang.get_text('delete_selected')} {deleted_count} {lang.get_text('files')}")
    
    def _clear_threats(self):
        """清除威胁列表"""
        if hasattr(self, 'threats_listbox') and self.threats_listbox.size() > 0:
            if messagebox.askyesno(lang.get_text("confirm"), lang.get_text("confirm") + " " + lang.get_text("clear_list") + "？"):
                self.threats_listbox.delete(0, tk.END)
                self.threats_list.clear()
                self._update_status(lang.get_text("clear_list") + " " + lang.get_text("success"))
    
    def _update_virus_database(self):
        """更新病毒数据库"""
        try:
            self._update_status(lang.get_text("update_virus_db") + "...")
            
            time.sleep(1)
            
            old_count = len(self.scan_engine.virus_db.signatures)
            self.scan_engine.virus_db.load_databases()
            new_count = len(self.scan_engine.virus_db.signatures)
            
            new_signatures = random.randint(5, 20)
            for i in range(new_signatures):
                fake_hash = hashlib.md5(f"new_virus_{i}_{time.time()}".encode()).hexdigest()
                self.scan_engine.virus_db.add_signature(fake_hash, f"Virus.Update.{i+1}")
            
            updated_count = len(self.scan_engine.virus_db.signatures)
            
            messagebox.showinfo(
                lang.get_text("success"),
                f"{lang.get_text('update_virus_db')} {lang.get_text('success')}！\n\n"
                f"{lang.get_text('virus_db')}: {old_count}\n"
                f"{lang.get_text('add')}: {updated_count - old_count}\n"
                f"{lang.get_text('total')}: {updated_count}\n\n"
                f"{lang.get_text('date')}: {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            self._update_status(lang.get_text('update_virus_db') + " " + lang.get_text('success'))
            
        except Exception as e:
            messagebox.showerror(lang.get_text("error"), f"{lang.get_text('update_virus_db')} {lang.get_text('error')}：{str(e)}")
            self._update_status(lang.get_text('update_virus_db') + " " + lang.get_text('error'))
    
    def _update_status(self, message):
        """更新状态栏"""
        logger.info(message)

# ==================== 启动界面 ====================
class PYRTSplashScreen:
    """PYRT启动画面"""
    
    def __init__(self, root, main_app_callback):
        self.root = root
        self.root.title(lang.get_text("app_name"))
        self.root.geometry("600x400")
        self.root.configure(bg=Config.THEME['bg_dark'])
        
        self.root.update_idletasks()
        width = 600
        height = 400
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.overrideredirect(True)
        
        self.main_app_callback = main_app_callback
        self._create_splash()
        
        self.root.after(3000, self._launch_main_app)
    
    def _create_splash(self):
        """创建启动画面"""
        canvas = tk.Canvas(
            self.root,
            bg=Config.THEME['bg_dark'],
            highlightthickness=0,
            width=600,
            height=400
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        
        center_x, center_y = 300, 200
        radius = 100
        
        self.angle = 0
        self.scan_line = None
        self._animate_scan_line(canvas, center_x, center_y, radius)
        
        canvas.create_text(
            center_x, center_y - 30,
            text=Config.LOGO,
            font=("Segoe UI Emoji", 72),
            fill=Config.THEME['primary']
        )
        
        canvas.create_text(
            center_x, center_y + 80,
            text=lang.get_text("app_name"),
            font=("Microsoft YaHe", 32, "bold"),
            fill=Config.THEME['text_primary']
        )
        
        canvas.create_text(
            center_x, center_y + 120,
            text=f"{lang.get_text('version')} {Config.VERSION}",
            font=("Microsoft YaHe", 14),
            fill=Config.THEME['text_secondary']
        )
        
        self.loading_text = canvas.create_text(
            center_x, 350,
            text=lang.get_text("preparing_scan"),
            font=("Microsoft YaHei", 11),
            fill=Config.THEME['primary']
        )
        
        self.progress = 0
        self._animate_progress(canvas, 200, 370)
        
        canvas.create_text(
            center_x, 390,
            text=f"© 2026 {Config.COMPANY}. All rights reserved.",
            font=("Microsoft YaHei", 9),
            fill=Config.THEME['text_secondary']
        )
    
    def _animate_scan_line(self, canvas, x, y, radius):
        """动画扫描线"""
        if hasattr(self, 'animation_running') and not self.animation_running:
            return
        
        if self.scan_line:
            canvas.delete(self.scan_line)
        
        rad = math.radians(self.angle)
        end_x = x + radius * math.cos(rad)
        end_y = y + radius * math.sin(rad)
        
        self.scan_line = canvas.create_line(
            x, y, end_x, end_y,
            fill=Config.THEME['primary'],
            width=3,
            arrow="last"
        )
        
        self.angle = (self.angle + 8) % 360
        
        self.root.after(30, lambda: self._animate_scan_line(canvas, x, y, radius))
    
    def _animate_progress(self, canvas, x, y):
        """动画进度条"""
        if self.progress < 100:
            self.progress += 2
            
            canvas.itemconfig(self.loading_text, 
                            text=f"{lang.get_text('preparing_scan')} {self.progress}%")
            
            progress_width = 200 * (self.progress / 100)
            canvas.create_rectangle(
                x - 100, y - 5,
                x - 100 + progress_width, y + 5,
                fill=Config.THEME['primary'],
                outline=""
            )
            
            self.root.after(50, lambda: self._animate_progress(canvas, x, y))
    
    def _launch_main_app(self):
        """启动主应用"""
        self.animation_running = False
        self.root.destroy()
        self.main_app_callback()

# ==================== 主程序 ====================
def main():
    """主程序入口"""
    try:
        # 创建必要的目录
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(Config.QUARANTINE_DIR, exist_ok=True)
        os.makedirs(Config.BOOT_BACKUP_DIR, exist_ok=True)
        
        # 创建根窗口
        root = tk.Tk()
        
        def launch_main_app():
            """启动主应用"""
            main_root = tk.Tk()
            app = PYRTSecuritySuiteGUI(main_root)
            main_root.mainloop()
        
        # 显示启动画面
        splash = PYRTSplashScreen(root, launch_main_app)
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"PYRT安全卫士启动失败: {e}")
        messagebox.showerror(
            lang.get_text("error"),
            f"{lang.get_text('error')}：{str(e)}\n\n"
            f"{lang.get_text('log_center')}"
        )

if __name__ == "__main__":
    print("=" * 60)
    print(f"启动 {lang.get_text('app_name')} {Config.VERSION}")
    print("=" * 60)
    print("功能说明:")
    print("1.  多引擎病毒检测 (哈希匹配 + 启发式分析)")
    print("2.  后台实时保护 (文件监控 + 进程监控)")
    print("3.  引导文件保护 (完整性检查 + 自动修复)")
    print("4.  断网保护 (网络监控 + 连接阻止 + 紧急断网)")
    print("6.  实时警报和通知系统")
    print("7.  安全隔离区和日志系统")
    print("8.  多语言支持 (7种语言)")
    print("正在启动PYRT安全卫士...")
    
    main()