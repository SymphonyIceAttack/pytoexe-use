import csv
import time
import threading
import json
import os
import queue
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import pyperclip

pyautogui.PAUSE = 0.02

class CSVSender:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 MAC TMS 輔助工具")
        
        # DPI 適應性 (Windows)
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 設定視窗大小
        self.root.geometry("720x820")
        self.root.resizable(True, True)
        
        # 設定視窗背景色
        self.root.configure(bg="#F5F7FA")
        
        # 設定檔
        self.settings_file = "mac_tms_settings.json"
        self.settings = self.load_settings()
        
        # -------------------------
        # state
        # -------------------------
        self.rows = []
        self.index = 0
        self.saved_pos = None
        self.running = False
        self.stop_flag = False
        self.pause_flag = False
        self.processing = False
        
        # 記憶位置變數
        self.mem_var = tk.BooleanVar(value=self.settings.get('mem_pos', False))
        
        # 非阻塞更新隊列
        self.update_queue = queue.Queue()
        
        # 建立主要框架
        self.create_widgets()
        
        # 初始化設定
        self.apply_initial_settings()
        
        # 啟動隊列檢查
        self.check_update_queue()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """建立所有介面元件"""
        # 主框架 - 使用Grid佈局
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 設定Grid權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # -------------------------
        # 標題和時間區域
        # -------------------------
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 左側：標題
        title_container = ttk.Frame(title_frame)
        title_container.pack(side=tk.LEFT, fill=tk.Y)
        
        # 主標題
        title = tk.Label(title_container, text="MAC TMS 輔助工具", 
                        font=("Microsoft JhengHei", 18, "bold"), 
                        foreground="#2C3E50", bg="#F5F7FA")
        title.pack(side=tk.LEFT)
        
        # 版本標籤
        version_label = tk.Label(title_container, text="v4.0", 
                                font=("Consolas", 10), 
                                foreground="#7F8C8D", bg="#F5F7FA")
        version_label.pack(side=tk.LEFT, padx=(8, 0), pady=(5, 0))
        
        # 分隔線
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        # 右側：時間顯示
        time_container = ttk.Frame(title_frame)
        time_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.clock_label = tk.Label(time_container, text="", 
                                   font=("Consolas", 10), 
                                   foreground="#7F8C8D", bg="#F5F7FA")
        self.clock_label.pack()
        self.update_clock()
        
        # -------------------------
        # CSV 預覽區域
        # -------------------------
        preview_frame = ttk.LabelFrame(main_frame, text=" 📄 CSV 預覽", 
                                      padding="12", style="Title.TLabelframe")
        preview_frame.grid(row=1, column=0, columnspan=2, 
                          sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # 設定預覽框架的Grid權重
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # 文字預覽區域
        self.preview_text = tk.Text(preview_frame, height=10, 
                                   font=("Consolas", 10), 
                                   bg="#FFFFFF", fg="#2C3E50", 
                                   wrap=tk.NONE, relief=tk.FLAT, 
                                   borderwidth=1, highlightthickness=1,
                                   highlightbackground="#D1D8E0", 
                                   highlightcolor="#4A90E2")
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        self.preview_text.config(state="disabled")
        
        # 綁定滑鼠事件（複製功能）
        self.preview_text.bind("<Button-1>", self.on_preview_click)
        self.preview_text.bind("<Button-3>", self.on_right_click)  # 右鍵選單
        
        # 垂直捲軸
        v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", 
                                   command=self.preview_text.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_text['yscrollcommand'] = v_scrollbar.set
        
        # 水平捲軸
        h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", 
                                   command=self.preview_text.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.preview_text['xscrollcommand'] = h_scrollbar.set
        
        # -------------------------
        # 輸入 CSV 區域
        # -------------------------
        csv_frame = ttk.LabelFrame(main_frame, text=" 📂 輸入 CSV 檔案", 
                                  padding="12", style="Title.TLabelframe")
        csv_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 載入按鈕和資訊
        self.load_csv_btn = ttk.Button(csv_frame, text="📂 載入 CSV", width=14, 
                                      command=self.load_csv_dialog_thread,
                                      style="Accent.TButton")
        self.load_csv_btn.grid(row=0, column=0, sticky=tk.W, padx=(0, 12))
        
        self.csv_path_label = tk.Label(csv_frame, text="尚未載入任何檔案", 
                                      font=("Microsoft JhengHei", 9),
                                      foreground="#34495E", bg="#F5F7FA", 
                                      anchor="w", width=25)
        self.csv_path_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 資訊標籤框架
        info_frame = ttk.Frame(csv_frame)
        info_frame.grid(row=0, column=2, columnspan=4, sticky=tk.W)
        
        # 總筆數
        ttk.Label(info_frame, text="總筆數:").pack(side=tk.LEFT, padx=(0, 5))
        self.total_label = tk.Label(info_frame, text="0", 
                                   font=("Consolas", 10, "bold"),
                                   foreground="#2980B9", bg="#F5F7FA")
        self.total_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 當前筆數
        ttk.Label(info_frame, text="當前筆:").pack(side=tk.LEFT, padx=(0, 5))
        self.current_label = tk.Label(info_frame, text="0", 
                                     font=("Consolas", 10, "bold"),
                                     foreground="#E74C3C", bg="#F5F7FA")
        self.current_label.pack(side=tk.LEFT)
        
        # -------------------------
        # 設定區域（分左右兩欄）
        # -------------------------
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=3, column=0, columnspan=2, 
                           sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        
        # 左側：位置與熱鍵設定
        left_frame = ttk.Frame(settings_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        
        # 輸出位置設定框架
        pos_frame = ttk.LabelFrame(left_frame, text=" 🎯 輸出位置設定", 
                                  padding="15", style="Title.TLabelframe")
        pos_frame.pack(fill=tk.BOTH, expand=True)
        
        # 記憶位置選項
        ttk.Checkbutton(pos_frame, text="記憶輸出位置", variable=self.mem_var, 
                       command=self.update_pos_label).pack(anchor=tk.W, pady=(0, 12))
        
        # 位置設定按鈕組
        pos_btn_frame = ttk.Frame(pos_frame)
        pos_btn_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Button(pos_btn_frame, text="設定位置", width=10, 
                  command=self.set_position_thread, 
                  style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(pos_btn_frame, text="重置位置", width=10, 
                  command=self.reset_pos).pack(side=tk.LEFT)
        
        # 工作位置顯示
        self.pos_label = tk.Label(pos_frame, text="📍 工作窗位置: 未定義", 
                                 font=("Microsoft JhengHei", 9),
                                 fg="#8E44AD", bg="#F5F7FA", anchor="w")
        self.pos_label.pack(fill=tk.X, pady=(0, 15))
        
        # 分隔線
        ttk.Separator(pos_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 12))
        
        # 熱鍵設定
        hotkey_label = tk.Label(pos_frame, text="⌨️ 快速熱鍵設定", 
                               font=("Microsoft JhengHei", 10, "bold"),
                               fg="#2C3E50", bg="#F5F7FA", anchor="w")
        hotkey_label.pack(fill=tk.X, pady=(0, 8))
        
        # 送出熱鍵
        hotkey_row1 = ttk.Frame(pos_frame)
        hotkey_row1.pack(fill=tk.X, pady=3)
        ttk.Label(hotkey_row1, text="送出當前:").pack(side=tk.LEFT)
        self.send_hotkey = tk.StringVar(value=self.settings.get('send_hotkey', "F8"))
        self.send_entry = ttk.Entry(hotkey_row1, textvariable=self.send_hotkey, 
                                   width=6, font=("Consolas", 9), justify="center")
        self.send_entry.pack(side=tk.LEFT, padx=(8, 15))
        self.send_entry.bind("<Key>", lambda e: self.capture_hotkey(e, self.send_hotkey))
        
        # 停止熱鍵
        hotkey_row2 = ttk.Frame(pos_frame)
        hotkey_row2.pack(fill=tk.X, pady=3)
        ttk.Label(hotkey_row2, text="停止執行:").pack(side=tk.LEFT)
        self.stop_hotkey = tk.StringVar(value=self.settings.get('stop_hotkey', "F7"))
        self.stop_entry = ttk.Entry(hotkey_row2, textvariable=self.stop_hotkey, 
                                   width=6, font=("Consolas", 9), justify="center")
        self.stop_entry.pack(side=tk.LEFT, padx=(8, 15))
        self.stop_entry.bind("<Key>", lambda e: self.capture_hotkey(e, self.stop_hotkey))
        
        # 全部送出熱鍵
        hotkey_row3 = ttk.Frame(pos_frame)
        hotkey_row3.pack(fill=tk.X, pady=3)
        ttk.Label(hotkey_row3, text="全部送出:").pack(side=tk.LEFT)
        self.send_all_hotkey = tk.StringVar(value=self.settings.get('send_all_hotkey', "F9"))
        self.send_all_entry = ttk.Entry(hotkey_row3, textvariable=self.send_all_hotkey, 
                                       width=6, font=("Consolas", 9), justify="center")
        self.send_all_entry.pack(side=tk.LEFT, padx=(8, 15))
        self.send_all_entry.bind("<Key>", lambda e: self.capture_hotkey(e, self.send_all_hotkey))
        
        # 套用熱鍵按鈕
        ttk.Button(pos_frame, text="套用熱鍵設定", width=14, 
                  command=self.apply_hotkeys, 
                  style="Primary.TButton").pack(pady=(12, 0))
        
        # 右側：輸出模式設定
        right_frame = ttk.Frame(settings_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 模式設定框架
        mode_frame = ttk.LabelFrame(right_frame, text=" ⚙️ 輸出模式設定", 
                                   padding="15", style="Title.TLabelframe")
        mode_frame.pack(fill=tk.BOTH, expand=True)
        
        # 輸出模式選擇
        mode_label = tk.Label(mode_frame, text="📤 輸出模式:", 
                             font=("Microsoft JhengHei", 10, "bold"),
                             fg="#2C3E50", bg="#F5F7FA", anchor="w")
        mode_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.mode_var = tk.StringVar(value=self.settings.get('mode', "筆"))
        mode_radio_frame = ttk.Frame(mode_frame)
        mode_radio_frame.grid(row=0, column=1, sticky=tk.W, pady=(0, 8))
        
        ttk.Radiobutton(mode_radio_frame, text="筆輸出 (整筆發送)", 
                       variable=self.mode_var, value="筆", 
                       command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(mode_radio_frame, text="欄輸出 (逐欄發送)", 
                       variable=self.mode_var, value="欄", 
                       command=self.on_mode_change).pack(side=tk.LEFT)
        
        # 輸出送出分隔符號
        sep_label = tk.Label(mode_frame, text="🔤 輸出分隔:", 
                            font=("Microsoft JhengHei", 10, "bold"),
                            fg="#2C3E50", bg="#F5F7FA", anchor="w")
        sep_label.grid(row=1, column=0, sticky=tk.W, pady=8)
        
        self.sep_var = tk.StringVar(value=self.settings.get('separator', "Enter"))
        sep_radio_frame = ttk.Frame(mode_frame)
        sep_radio_frame.grid(row=1, column=1, sticky=tk.W, pady=8)
        
        # 分隔符號選項（使用網格佈局）
        separators = [("Tab", 0, 0), ("Enter", 0, 1), 
                     ("Space", 1, 0), ("Comma", 1, 1)]
        
        for text, row, col in separators:
            ttk.Radiobutton(sep_radio_frame, text=text, variable=self.sep_var, 
                           value=text).grid(row=row, column=col, sticky=tk.W, padx=8, pady=3)
        
        # 定位延時設定
        delay_label = tk.Label(mode_frame, text="⏱️ 定位延時 (毫秒):", 
                              font=("Microsoft JhengHei", 10, "bold"),
                              fg="#2C3E50", bg="#F5F7FA", anchor="w")
        delay_label.grid(row=2, column=0, sticky=tk.W, pady=8)
        
        self.delay_var = tk.IntVar(value=self.settings.get('delay', 3000))
        self.delay_spin = ttk.Spinbox(mode_frame, from_=150, to=15000, increment=50, 
                                     textvariable=self.delay_var, width=10, 
                                     font=("Consolas", 9))
        self.delay_spin.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        # 欄位模式設定框架
        col_frame = ttk.LabelFrame(mode_frame, text=" 📝 欄位模式設定", padding="10")
        col_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 自動化送出選項
        self.auto_col_var = tk.BooleanVar(value=self.settings.get('auto_col', False))
        self.auto_col_check = ttk.Checkbutton(col_frame, text="完全自動化送出", 
                                            variable=self.auto_col_var)
        self.auto_col_check.pack(anchor=tk.W, pady=(0, 8))
        
        # 每欄位延時設定
        col_delay_frame = ttk.Frame(col_frame)
        col_delay_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(col_delay_frame, text="每欄位延時 (ms):").pack(side=tk.LEFT, padx=(0, 8))
        self.col_delay_var = tk.IntVar(value=self.settings.get('col_delay', 500))
        self.col_delay_spin = ttk.Spinbox(col_delay_frame, from_=200, to=10000, increment=50, 
                                         textvariable=self.col_delay_var, width=8,
                                         font=("Consolas", 9))
        self.col_delay_spin.pack(side=tk.LEFT)
        
        # 視窗設定
        window_label = tk.Label(mode_frame, text="🖥️ 視窗設定:", 
                               font=("Microsoft JhengHei", 10, "bold"),
                               fg="#2C3E50", bg="#F5F7FA", anchor="w")
        window_label.grid(row=4, column=0, sticky=tk.W, pady=8)
        
        window_frame = ttk.Frame(mode_frame)
        window_frame.grid(row=4, column=1, sticky=tk.W, pady=8)
        
        # 透明度設定
        alpha_frame = ttk.Frame(window_frame)
        alpha_frame.pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(alpha_frame, text="透明度:").pack(side=tk.LEFT, padx=(0, 8))
        
        self.alpha_var = tk.DoubleVar(value=self.settings.get('alpha', 1.0))
        alpha_slider = ttk.Scale(alpha_frame, from_=0.3, to=1.0, orient="horizontal", 
                               variable=self.alpha_var, command=self.update_alpha, 
                               length=100)
        alpha_slider.pack(side=tk.LEFT, padx=(0, 8))
        
        self.alpha_label = tk.Label(alpha_frame, text="100%", 
                                   font=("Consolas", 9), bg="#F5F7FA")
        self.alpha_label.pack(side=tk.LEFT)
        
        # 保持置頂選項
        self.topmost_var = tk.BooleanVar(value=self.settings.get('topmost', True))
        ttk.Checkbutton(window_frame, text="保持置頂", variable=self.topmost_var, 
                       command=self.update_topmost).pack(side=tk.LEFT)
        
        # -------------------------
        # 進度條區域
        # -------------------------
        progress_frame = ttk.LabelFrame(main_frame, text=" 📊 進度顯示", 
                                       padding="12", style="Title.TLabelframe")
        progress_frame.grid(row=4, column=0, columnspan=2, 
                           sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=680, mode='determinate',
                                          style="Progress.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        
        # 進度百分比標籤
        self.progress_label = tk.Label(progress_frame, text="0%", 
                                      font=("Consolas", 10, "bold"), 
                                      foreground="#2C3E50", bg="#F5F7FA", width=5)
        self.progress_label.pack(side=tk.LEFT)
        
        # -------------------------
        # 控制按鈕區域
        # -------------------------
        ctrl_frame = ttk.LabelFrame(main_frame, text=" 🎮 控制面板", 
                                   padding="15", style="Title.TLabelframe")
        ctrl_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 導航按鈕組
        nav_frame = ttk.Frame(ctrl_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.prev_btn = ttk.Button(nav_frame, text="◀ 上一筆", width=10,
                                  command=self.prev_row, 
                                  style="Nav.TButton")
        self.prev_btn.pack(side=tk.LEFT, padx=3)
        
        self.preview_btn = ttk.Button(nav_frame, text="🔍 詳細預覽", width=11,
                                     command=self.preview_data,
                                     style="Nav.TButton")
        self.preview_btn.pack(side=tk.LEFT, padx=3)
        
        self.next_btn = ttk.Button(nav_frame, text="下一筆 ▶", width=10,
                                  command=self.next_row,
                                  style="Nav.TButton")
        self.next_btn.pack(side=tk.LEFT, padx=3)
        
        # 主要操作按鈕組
        op_frame = ttk.Frame(ctrl_frame)
        op_frame.pack(fill=tk.X, pady=10)
        
        self.send_btn = ttk.Button(op_frame, text="🚀 送出當前筆", width=14,
                                  command=self.send_current_thread,
                                  style="Primary.TButton")
        self.send_btn.pack(side=tk.LEFT, padx=3)
        
        self.send_all_btn = ttk.Button(op_frame, text="⚡ 全部送出", width=14,
                                      command=self.send_all_thread,
                                      style="Accent.TButton")
        self.send_all_btn.pack(side=tk.LEFT, padx=3)
        
        # 控制按鈕組
        control_frame = ttk.Frame(ctrl_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸️ 暫停", width=10,
                                   command=self.toggle_pause,
                                   style="Control.TButton")
        self.pause_btn.pack(side=tk.LEFT, padx=3)
        
        self.stop_btn = ttk.Button(control_frame, text="🛑 停止執行", width=10,
                                  command=self.stop_execution,
                                  style="Danger.TButton")
        self.stop_btn.pack(side=tk.LEFT, padx=3)
        
        self.clear_btn = ttk.Button(control_frame, text="🗑️ 清除資料", width=10,
                                   command=self.clear_data,
                                   style="Control.TButton")
        self.clear_btn.pack(side=tk.LEFT, padx=3)
        
        # -------------------------
        # 狀態列
        # -------------------------
        self.status_bar = tk.Label(main_frame, text="🟢 就緒", 
                                  font=("Microsoft JhengHei", 9),
                                  relief=tk.SUNKEN, anchor=tk.W, 
                                  bg="#E8F4FD", fg="#2C3E50",
                                  padx=10, pady=4)
        self.status_bar.grid(row=6, column=0, columnspan=2, 
                            sticky=(tk.W, tk.E), pady=(0, 0))
        
        # 設定行和列的權重
        main_frame.rowconfigure(1, weight=1)  # CSV預覽區域可伸展
        main_frame.rowconfigure(3, weight=0)  # 設定區域固定高度
        main_frame.columnconfigure(0, weight=1)  # 左側框架
        main_frame.columnconfigure(1, weight=1)  # 右側框架
        
        # 建立自訂樣式
        self.create_styles()
    
    def create_styles(self):
        """建立自訂樣式"""
        style = ttk.Style()
        
        # 設定主題
        style.theme_use('clam')
        
        # 標題框架樣式
        style.configure("Title.TLabelframe", 
                       background="#F5F7FA",
                       bordercolor="#D1D8E0",
                       relief="solid",
                       borderwidth=1)
        style.configure("Title.TLabelframe.Label",
                       font=("Microsoft JhengHei", 10, "bold"),
                       foreground="#2C3E50",
                       background="#F5F7FA")
        
        # 按鈕樣式
        style.configure("Primary.TButton",
                       font=("Microsoft JhengHei", 9),
                       padding=6,
                       background="#4A90E2",
                       foreground="white",
                       bordercolor="#4A90E2")
        style.map("Primary.TButton",
                 background=[('active', '#3A80D2'), ('disabled', '#B0C4DE')],
                 foreground=[('disabled', '#7F8C8D')])
        
        style.configure("Accent.TButton",
                       font=("Microsoft JhengHei", 9),
                       padding=6,
                       background="#2ECC71",
                       foreground="white",
                       bordercolor="#2ECC71")
        style.map("Accent.TButton",
                 background=[('active', '#27AE60'), ('disabled', '#B0C4DE')],
                 foreground=[('disabled', '#7F8C8D')])
        
        style.configure("Danger.TButton",
                       font=("Microsoft JhengHei", 9),
                       padding=6,
                       background="#E74C3C",
                       foreground="white",
                       bordercolor="#E74C3C")
        style.map("Danger.TButton",
                 background=[('active', '#C0392B'), ('disabled', '#B0C4DE')],
                 foreground=[('disabled', '#7F8C8D')])
        
        style.configure("Nav.TButton",
                       font=("Microsoft JhengHei", 9),
                       padding=5,
                       background="#ECF0F1",
                       foreground="#2C3E50")
        style.map("Nav.TButton",
                 background=[('active', '#D5DBDB'), ('disabled', '#ECF0F1')],
                 foreground=[('disabled', '#BDC3C7')])
        
        style.configure("Control.TButton",
                       font=("Microsoft JhengHei", 9),
                       padding=5,
                       background="#F8F9FA",
                       foreground="#2C3E50")
        style.map("Control.TButton",
                 background=[('active', '#E9ECEF'), ('disabled', '#F8F9FA')],
                 foreground=[('disabled', '#BDC3C7')])
        
        # 進度條樣式
        style.configure("Progress.Horizontal.TProgressbar",
                       background="#4A90E2",
                       troughcolor="#ECF0F1",
                       bordercolor="#D1D8E0",
                       lightcolor="#4A90E2",
                       darkcolor="#4A90E2")
    
    def on_mode_change(self):
        """模式變更時更新UI狀態"""
        mode = self.mode_var.get()
        if mode == "筆":
            # 筆輸出模式，自動化送出選項無效
            self.auto_col_var.set(False)
            self.auto_col_check.config(state=tk.DISABLED)
        else:
            # 欄輸出模式，自動化送出選項有效
            self.auto_col_check.config(state=tk.NORMAL)
    
    def apply_initial_settings(self):
        """套用初始設定"""
        self.update_topmost()
        self.update_alpha(None)
        self.apply_hotkeys()
        self.update_status("🟢 就緒")
        self.update_ui_state(False)
        self.update_progress(0)
        
        # 根據當前模式設定自動化送出選項狀態
        self.on_mode_change()
    
    # ==================== 設定檔管理 ====================
    
    def load_settings(self):
        """載入設定檔"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def save_settings(self):
        """儲存設定"""
        settings = {
            'mode': self.mode_var.get(),
            'separator': self.sep_var.get(),
            'delay': self.delay_var.get(),
            'send_hotkey': self.send_hotkey.get(),
            'stop_hotkey': self.stop_hotkey.get(),
            'send_all_hotkey': self.send_all_hotkey.get(),
            'topmost': self.topmost_var.get(),
            'alpha': self.alpha_var.get(),
            'mem_pos': self.mem_var.get(),
            'auto_col': self.auto_col_var.get(),
            'col_delay': self.col_delay_var.get()
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.log_message("✅ 設定已儲存")
        except Exception as e:
            self.update_from_queue(lambda: messagebox.showerror("錯誤", f"儲存設定失敗: {e}"))
    
    # ==================== UI更新隊列 ====================
    
    def check_update_queue(self):
        """定期檢查並處理更新隊列"""
        try:
            while True:
                task = self.update_queue.get_nowait()
                if callable(task):
                    task()
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_update_queue)
    
    def update_from_queue(self, func, *args, **kwargs):
        """將UI更新任務放入隊列"""
        if args or kwargs:
            self.update_queue.put(lambda: func(*args, **kwargs))
        else:
            self.update_queue.put(func)
    
    def log_message(self, message):
        """記錄訊息到狀態列"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.update_status(f"[{timestamp}] {message}")
    
    # ==================== UI輔助方法 ====================
    
    def update_alpha(self, val):
        """更新透明度"""
        alpha = self.alpha_var.get()
        self.root.attributes("-alpha", alpha)
        self.alpha_label.config(text=f"{int(alpha*100)}%")
    
    def update_topmost(self):
        """更新置頂狀態"""
        self.root.attributes("-topmost", self.topmost_var.get())
    
    def update_clock(self):
        """更新時鐘顯示"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=f"🕒 {now}")
        self.root.after(1000, self.update_clock)
    
    def update_pos_label(self):
        """更新位置標籤"""
        if self.saved_pos:
            self.pos_label.config(text=f"📍 工作窗位置: ({self.saved_pos[0]}, {self.saved_pos[1]})")
        else:
            self.pos_label.config(text="📍 工作窗位置: 未定義")
    
    def update_status(self, message):
        """更新狀態列"""
        # 根據訊息類型設定不同的顏色和圖示
        if "錯誤" in message or "失敗" in message:
            icon = "🔴"
            bg_color = "#FDEDEC"
            fg_color = "#C0392B"
        elif "成功" in message or "完成" in message:
            icon = "🟢"
            bg_color = "#E8F6F3"
            fg_color = "#27AE60"
        elif "警告" in message or "注意" in message:
            icon = "🟡"
            bg_color = "#FEF9E7"
            fg_color = "#F39C12"
        elif "載入" in message or "就緒" in message:
            icon = "🔵"
            bg_color = "#E8F4FD"
            fg_color = "#2980B9"
        else:
            icon = "⚪"
            bg_color = "#F8F9FA"
            fg_color = "#2C3E50"
        
        # 如果訊息已經有表情符號，則不添加
        if not any(emoji in message for emoji in ["🟢", "🔴", "🟡", "🔵", "⚪"]):
            message = f"{icon} {message}"
        
        self.status_bar.config(text=message, bg=bg_color, fg=fg_color)
    
    def update_ui_state(self, data_loaded=False):
        """更新UI元件狀態"""
        state = tk.NORMAL if data_loaded else tk.DISABLED
        
        self.prev_btn.config(state=state)
        self.next_btn.config(state=state)
        self.preview_btn.config(state=state)
        self.send_btn.config(state=state)
        self.send_all_btn.config(state=state)
        self.pause_btn.config(state=state)
        self.stop_btn.config(state=state)
        self.clear_btn.config(state=state)
    
    def update_progress(self, value):
        """更新進度條"""
        self.progress_var.set(value)
        percent = int(value)
        self.progress_label.config(text=f"{percent}%")
        
        # 根據進度更新顏色
        if percent < 30:
            color = "#E74C3C"  # 紅色
        elif percent < 70:
            color = "#F39C12"  # 橙色
        else:
            color = "#27AE60"  # 綠色
        
        self.progress_label.config(fg=color)
    
    # ==================== CSV載入 ====================
    
    def load_csv_dialog_thread(self):
        """使用線程載入CSV檔案"""
        path = filedialog.askopenfilename(
            filetypes=[("CSV檔案", "*.csv"), ("所有檔案", "*.*")],
            title="選擇 CSV 檔案"
        )
        if not path:
            return
        
        # 顯示載入中狀態
        self.csv_path_label.config(text="載入中...", fg="#F39C12")
        self.update_status("🟡 正在載入CSV檔案...")
        
        # 在新線程中載入
        t = threading.Thread(target=self.load_csv_file_with_encodings, args=(path,), daemon=True)
        t.start()
    
    def load_csv_file_with_encodings(self, path):
        """嘗試多種編碼載入CSV檔案"""
        # 繁體中文常用編碼列表
        encodings = [
            'utf-8-sig',  # UTF-8 with BOM
            'big5',       # 繁體中文 (台灣、香港)
            'cp950',      # 繁體中文 Windows
            'gbk',        # 簡體中文，有時包含繁體
            'gb18030',    # 中文標準
            'utf-16',     # UTF-16
            'latin1',     # 西歐語言，有時能解
            'iso-8859-1', # ISO 拉丁文
            'shift_jis',  # 日文
            'euc-kr'      # 韓文
        ]
        
        rows = []
        used_encoding = None
        
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    # 嘗試讀取前幾行來確認編碼
                    sample = f.read(1024)
                    f.seek(0)
                    
                    # 檢查是否包含常見的繁體中文字
                    if self.contains_chinese(sample) or encoding in ['utf-8-sig', 'utf-16']:
                        reader = csv.reader(f)
                        rows = [r for r in reader if r]
                        
                        # 檢查是否成功讀取到數據
                        if rows and len(rows) > 0:
                            used_encoding = encoding
                            break
            except (UnicodeDecodeError, UnicodeError) as e:
                continue
            except Exception as e:
                continue
        
        if rows and used_encoding:
            self.update_from_queue(self._finish_csv_loading, path, rows, used_encoding)
        else:
            self.update_from_queue(self._csv_load_error, "無法讀取 CSV 檔案，請確認檔案編碼")
    
    def contains_chinese(self, text):
        """檢查文本是否包含中文字符"""
        # 常見的繁體中文字符範圍
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # 基本漢字
                return True
        return False
    
    def _finish_csv_loading(self, path, rows, encoding):
        """完成CSV載入"""
        self.rows = rows
        self.index = 0
        filename = os.path.basename(path)
        if len(filename) > 20:
            filename = filename[:17] + "..."
        self.csv_path_label.config(text=filename, fg="#2980B9")
        
        # 編碼顯示
        encoding_map = {
            'utf-8-sig': 'UTF-8',
            'big5': 'BIG5',
            'cp950': 'CP950',
            'gbk': 'GBK',
            'gb18030': 'GB18030'
        }
        encoding_display = encoding_map.get(encoding, encoding)
        
        self.total_label.config(text=str(len(self.rows)))
        self.current_label.config(text="1")
        self.update_progress(0)
        self.update_preview()
        self.log_message(f"✅ 已載入 {len(self.rows)} 筆資料 (編碼: {encoding_display})")
        self.update_ui_state(True)
    
    def _csv_load_error(self, error_msg):
        """CSV載入錯誤處理"""
        self.csv_path_label.config(text="載入失敗", fg="#E74C3C")
        self.update_from_queue(lambda: messagebox.showerror("錯誤", error_msg))
        self.update_status("🔴 CSV載入失敗")
    
    def update_preview(self):
        """更新預覽視窗"""
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        
        if not self.rows:
            self.preview_text.insert(tk.END, "尚未載入 CSV 或 CSV 無資料")
        else:
            # 計算當前進度
            progress = (self.index + 1) / len(self.rows) * 100
            self.update_progress(progress)
            
            # 儲存顯示的起始索引
            self.preview_start_idx = max(0, self.index - 10)
            self.preview_end_idx = min(len(self.rows), self.preview_start_idx + 30)
            
            for i in range(self.preview_start_idx, self.preview_end_idx):
                row = self.rows[i]
                # 顯示完整內容，不截斷
                row_text = " | ".join(str(cell) for cell in row)
                
                # 標記當前筆
                if i == self.index:
                    prefix = "▶ "
                    self.preview_text.insert(tk.END, prefix, "current_row")
                else:
                    prefix = "   "
                
                # 添加行號
                line_text = f"{prefix}{i+1:3d}: {row_text}\n"
                self.preview_text.insert(tk.END, line_text)
                
                # 設置當前行的標籤
                if i == self.index:
                    self.preview_text.tag_config("current_row", 
                                                background="#E3F2FD", 
                                                foreground="#0D47A1",
                                                font=("Consolas", 10, "bold"))
            
            if len(self.rows) > self.preview_end_idx:
                self.preview_text.insert(tk.END, f"\n... 還有 {len(self.rows)-self.preview_end_idx} 筆資料 ...")
        
        self.preview_text.config(state="disabled")
        
        # 滾動到當前行
        if self.rows and hasattr(self, 'preview_start_idx'):
            line_num = min(30, self.index - self.preview_start_idx + 1)
            self.preview_text.see(f"{line_num}.0")
    
    # ==================== 導航 ====================
    
    def prev_row(self):
        """上一筆"""
        if self.index > 0:
            self.index -= 1
            self.current_label.config(text=str(self.index + 1))
            self.update_preview()
    
    def next_row(self):
        """下一筆"""
        if self.index < len(self.rows) - 1:
            self.index += 1
            self.current_label.config(text=str(self.index + 1))
            self.update_preview()
    
    def preview_data(self):
        """預覽當前資料"""
        if not self.rows:
            return
        
        row = self.rows[self.index]
        preview_text = "\n".join([f"欄位 {i+1}: {value}" for i, value in enumerate(row)])
        
        # 建立預覽視窗
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"預覽第 {self.index + 1} 筆資料")
        preview_window.geometry("600x400")
        preview_window.transient(self.root)
        preview_window.configure(bg="#F5F7FA")
        
        # 置中顯示
        preview_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (preview_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
        
        # 標題
        title_label = tk.Label(preview_window, text=f"📋 第 {self.index + 1} 筆資料預覽",
                              font=("Microsoft JhengHei", 12, "bold"),
                              fg="#2C3E50", bg="#F5F7FA")
        title_label.pack(pady=(10, 5))
        
        # 文字框框架
        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # 文字框
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10),
                             bg="#FFFFFF", fg="#2C3E50", relief=tk.FLAT,
                             borderwidth=1, highlightthickness=1,
                             highlightbackground="#D1D8E0", 
                             highlightcolor="#4A90E2")
        text_widget.insert(1.0, preview_text)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按鈕框架
        button_frame = ttk.Frame(preview_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="📋 複製整筆", 
                  command=lambda: self.copy_row_to_clipboard(row),
                  style="Primary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ 關閉", 
                  command=preview_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_preview_click(self, event):
        """點擊預覽區域時複製該欄資料"""
        if not self.rows:
            return
        
        # 獲取點擊位置的行數
        index = self.preview_text.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        
        # 計算對應的資料索引
        if hasattr(self, 'preview_start_idx'):
            data_idx = self.preview_start_idx + (line_num - 1)
        else:
            data_idx = line_num - 1
        
        if 0 <= data_idx < len(self.rows):
            row = self.rows[data_idx]
            
            # 複製整行資料
            self.copy_row_to_clipboard(row)
            
            # 如果是點擊其他行，跳到該行
            if data_idx != self.index:
                self.index = data_idx
                self.current_label.config(text=str(self.index + 1))
                self.update_preview()
    
    def on_right_click(self, event):
        """右鍵點擊顯示選單"""
        if not self.rows:
            return
        
        # 獲取點擊位置的行數
        index = self.preview_text.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        
        # 計算對應的資料索引
        if hasattr(self, 'preview_start_idx'):
            data_idx = self.preview_start_idx + (line_num - 1)
        else:
            data_idx = line_num - 1
        
        if 0 <= data_idx < len(self.rows):
            row = self.rows[data_idx]
            
            # 建立右鍵選單
            menu = tk.Menu(self.root, tearoff=0, bg="#FFFFFF", fg="#2C3E50",
                          activebackground="#4A90E2", activeforeground="#FFFFFF",
                          font=("Microsoft JhengHei", 9))
            menu.add_command(label="📋 複製整筆資料", 
                           command=lambda: self.copy_row_to_clipboard(row))
            menu.add_separator()
            
            # 添加每個欄位的複製選項
            for i, cell in enumerate(row):
                cell_text = str(cell)
                if len(cell_text) > 30:
                    display_text = cell_text[:27] + "..."
                else:
                    display_text = cell_text
                
                menu.add_command(label=f#️⃣ 複製欄位 {i+1}: {display_text}", 
                               command=lambda idx=i: self.copy_specific_cell(row, idx, data_idx))
            
            # 顯示選單
            menu.tk_popup(event.x_root, event.y_root)
    
    def copy_specific_cell(self, row, column_idx, data_idx):
        """複製指定欄位的資料"""
        if 0 <= column_idx < len(row):
            cell_value = str(row[column_idx])
            self.root.clipboard_clear()
            self.root.clipboard_append(cell_value)
            self.log_message(f"✅ 已複製第 {data_idx + 1} 筆資料的欄位 {column_idx + 1}")
    
    def copy_row_to_clipboard(self, row):
        """複製整行資料到剪貼簿"""
        row_text = "\t".join(str(cell) for cell in row)
        self.root.clipboard_clear()
        self.root.clipboard_append(row_text)
        self.log_message("✅ 已複製整筆資料到剪貼簿")
    
    def clear_data(self):
        """清除資料"""
        if self.rows:
            if messagebox.askyesno("確認", "確定要清除所有資料嗎？"):
                self.rows = []
                self.index = 0
                self.csv_path_label.config(text="尚未載入任何檔案", fg="#34495E")
                self.total_label.config(text="0")
                self.current_label.config(text="0")
                self.update_progress(0)
                self.update_preview()
                self.log_message("🗑️ 資料已清除")
                self.update_ui_state(False)
    
    # ==================== 位置管理 ====================
    
    def set_position_thread(self):
        """使用線程設定位置"""
        t = threading.Thread(target=self.set_position, daemon=True)
        t.start()
    
    def set_position(self):
        """設定位置"""
        delay = max(150, min(15000, self.delay_var.get()))
        
        def get_position():
            self.update_from_queue(lambda: self.update_status(f"🟡 請將滑鼠移到目標位置，{delay//1000}秒後自動抓取"))
            time.sleep(delay / 1000.0)
            pos = pyautogui.position()
            self.update_from_queue(self._set_position_callback, (pos.x, pos.y))
        
        t = threading.Thread(target=get_position, daemon=True)
        t.start()
    
    def _set_position_callback(self, pos):
        """位置設定回調"""
        self.saved_pos = pos
        self.update_pos_label()
        self.log_message(f"✅ 位置已設定：({pos[0]}, {pos[1]})")
    
    def reset_pos(self):
        """重置位置"""
        self.saved_pos = None
        self.update_pos_label()
        self.log_message("🗑️ 輸出位置已重置")
    
    def get_target_pos(self):
        """取得目標位置（同步）"""
        delay = max(150, min(15000, self.delay_var.get()))
        
        if self.mem_var.get() and self.saved_pos:
            return self.saved_pos
        
        self.update_status(f"🟡 請選擇輸出位置，{delay//1000}秒後自動定位")
        self.root.update()
        time.sleep(delay / 1000.0)
        pos = pyautogui.position()
        
        if self.mem_var.get():
            self.saved_pos = (pos.x, pos.y)
            self.update_pos_label()
        
        return (pos.x, pos.y)
    
    # ==================== 熱鍵處理 ====================
    
    def capture_hotkey(self, event, hotkey_var):
        """捕獲熱鍵並進行驗證"""
        k = event.keysym
        
        # 驗證熱鍵有效性
        if self.validate_hotkey(k):
            hotkey_var.set(k)
            self.log_message(f"✅ 已設定熱鍵: {k}")
        else:
            self.log_message(f"⚠️ 無效的熱鍵: {k}")
        
        return "break"
    
    def validate_hotkey(self, key):
        """驗證熱鍵是否有效"""
        valid_keys = [
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            'Escape', 'Tab', 'Caps_Lock', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R',
            'Alt_L', 'Alt_R', 'space', 'Return', 'BackSpace', 'Delete', 'Insert',
            'Home', 'End', 'Page_Up', 'Page_Down', 'Up', 'Down', 'Left', 'Right'
        ]
        
        return key in valid_keys
    
    def apply_hotkeys(self):
        """套用熱鍵設定"""
        # 驗證所有熱鍵
        hotkeys = [
            (self.send_hotkey.get(), "送出"),
            (self.stop_hotkey.get(), "停止"),
            (self.send_all_hotkey.get(), "全部送出")
        ]
        
        invalid_keys = []
        for key, name in hotkeys:
            if not self.validate_hotkey(key):
                invalid_keys.append(f"{name}: {key}")
        
        if invalid_keys:
            self.update_from_queue(lambda: messagebox.showwarning(
                "無效熱鍵", 
                f"以下熱鍵無效，請重新設定：\n" + "\n".join(invalid_keys)
            ))
            return
        
        # 解除綁定所有舊熱鍵
        try:
            self.root.unbind_all(f"<{self.send_hotkey.get()}>")
            self.root.unbind_all(f"<{self.stop_hotkey.get()}>")
            self.root.unbind_all(f"<{self.send_all_hotkey.get()}>")
        except Exception:
            pass
        
        try:
            # 綁定送出當前熱鍵
            self.root.bind_all(f"<{self.send_hotkey.get()}>", 
                             lambda e: self.send_current_thread())
            
            # 綁定停止熱鍵
            self.root.bind_all(f"<{self.stop_hotkey.get()}>", 
                             lambda e: self.stop_execution())
            
            # 綁定全部送出熱鍵
            self.root.bind_all(f"<{self.send_all_hotkey.get()}>", 
                             lambda e: self.send_all_thread())
            
            self.log_message(f"✅ 已套用熱鍵：送出={self.send_hotkey.get()}，停止={self.stop_hotkey.get()}，全部送出={self.send_all_hotkey.get()}")
        except Exception as e:
            messagebox.showwarning("熱鍵綁定失敗", 
                                 f"無法綁定熱鍵：{e}")
    
    # ==================== 控制方法 ====================
    
    def toggle_pause(self):
        """切換暫停狀態"""
        self.pause_flag = not self.pause_flag
        if self.pause_flag:
            self.pause_btn.config(text="▶️ 繼續")
            self.log_message("⏸️ 已暫停")
        else:
            self.pause_btn.config(text="⏸️ 暫停")
            self.log_message("▶️ 已恢復")
    
    def stop_execution(self, *args):
        """停止執行"""
        if self.running or self.processing:
            self.stop_flag = True
            self.log_message("🛑 已停止執行")
        else:
            self.log_message("ℹ️ 沒有正在執行的任務")
    
    # ==================== 發送方法 ====================
    
    def send_current_thread(self):
        """發送當前筆（線程封裝）"""
        if self.running:
            self.log_message("⚠️ 已有任務正在執行")
            return
        
        if not self.rows:
            messagebox.showinfo("提示", "尚未載入任何 CSV")
            return
        
        self.running = True
        self.stop_flag = False
        self.update_ui_state(True)
        
        t = threading.Thread(target=self.send_current, daemon=True)
        t.start()
    
    def send_current(self):
        """發送當前筆（核心邏輯）"""
        row = self.rows[self.index]
        sep = self.get_separator()
        mode = self.mode_var.get()
        
        try:
            if mode == "筆":
                # 整筆輸出
                pos = self.get_target_pos()
                if self.stop_flag:
                    self.running = False
                    return
                
                # 記錄使用的分隔符號
                separator_text = self.get_separator_display_name()
                self.log_message(f"📤 筆輸出模式，使用分隔符號: {separator_text}")
                
                # 將整筆資料用選擇的分隔符號連接
                content = sep.join(str(cell) for cell in row)
                
                pyautogui.click(pos)
                pyautogui.write(content, interval=0.01)
                self.log_message(f"✅ 已送出第 {self.index + 1} 筆資料")
                
            else:
                # 欄位輸出 - 根據設定選擇模式
                if self.auto_col_var.get():
                    # 完全自動化模式
                    for i, col in enumerate(row):
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(str(col), interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                        
                        self.log_message(f"✅ 已送出欄位 {i+1}")
                else:
                    # 手動確認模式
                    for i, col in enumerate(row):
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        # 顯示確認對話框
                        result = messagebox.askyesno(
                            "欄位確認",
                            f"欄位 {i+1}：\n\n{col}\n\n按「是」繼續發送，按「否」停止任務"
                        )
                        
                        if not result:
                            self.stop_flag = True
                            self.log_message("❌ 使用者取消發送")
                            break
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(str(col), interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                        
                        self.log_message(f"✅ 已送出欄位 {i+1}")
            
            # 完成處理
            if not self.stop_flag:
                self.update_from_queue(self._finish_current_row)
            else:
                self.log_message("🛑 發送已中斷")
                self.update_status("🛑 發送已中斷")
                
        except Exception as e:
            self.update_from_queue(lambda: messagebox.showerror("執行錯誤", f"執行時發生錯誤：{e}"))
            self.log_message(f"🔴 執行錯誤: {e}")
        finally:
            self.running = False
    
    def get_separator(self):
        """根據設定返回分隔符號"""
        separator = self.sep_var.get()
        if separator == "Tab":
            return "\t"
        elif separator == "Enter":
            return "\n"
        elif separator == "Space":
            return " "
        elif separator == "Comma":
            return ","
        else:
            return "\n"
    
    def get_separator_display_name(self):
        """獲取分隔符號的顯示名稱"""
        separator = self.sep_var.get()
        if separator == "Tab":
            return "Tab鍵"
        elif separator == "Enter":
            return "Enter鍵"
        elif separator == "Space":
            return "空格"
        elif separator == "Comma":
            return "逗號"
        else:
            return "Enter鍵"
    
    def _finish_current_row(self):
        """完成當前筆處理"""
        if not self.stop_flag and self.index < len(self.rows) - 1:
            self.index += 1
            self.current_label.config(text=str(self.index + 1))
            self.update_preview()
            self.update_status("✅ 已送出本筆，自動跳至下一筆")
        else:
            self.update_status("✅ 發送完成")
    
    def send_all_thread(self):
        """發送全部（線程封裝）"""
        if not self.rows:
            self.log_message("⚠️ 尚未載入CSV資料")
            return
        
        if self.running or self.processing:
            self.log_message("⚠️ 已有任務正在執行")
            return
        
        # 確認對話
        remaining = len(self.rows) - self.index
        mode = self.mode_var.get()
        
        if mode == "欄" and not self.auto_col_var.get():
            confirm_msg = f"將從第 {self.index+1} 筆開始，發送所有剩餘的 {remaining} 筆資料。\n\n"
            confirm_msg += "⚠️ 注意：欄位模式下，每筆資料的每個欄位都需要手動確認！\n"
            confirm_msg += "這會非常耗時。建議啟用「完全自動化送出」選項以跳過確認。\n\n"
            confirm_msg += "是否要繼續使用手動確認模式？"
            
            if not messagebox.askyesno("確認", confirm_msg):
                return
            
            if not messagebox.askyesno("再次確認", 
                                      "您確定要使用手動確認模式發送所有資料嗎？\n這可能需要很多次點擊確認！"):
                return
        else:
            if not messagebox.askyesno("確認", 
                                      f"將從第 {self.index+1} 筆開始，發送所有剩餘的 {remaining} 筆資料。是否繼續？"):
                return
        
        self.processing = True
        self.stop_flag = False
        self.update_ui_state(True)
        
        t = threading.Thread(target=self.send_all, daemon=True)
        t.start()
    
    def send_all(self):
        """發送全部資料"""
        total_rows = len(self.rows)
        sep = self.get_separator()
        mode = self.mode_var.get()
        separator_text = self.get_separator_display_name()
        
        self.log_message(f"📤 全部送出，使用分隔符號: {separator_text}")
        
        for i in range(self.index, total_rows):
            if self.stop_flag:
                break
            
            while self.pause_flag and not self.stop_flag:
                time.sleep(0.1)
            
            self.index = i
            progress = (i + 1) / total_rows * 100
            self.update_from_queue(lambda idx=i, prog=progress: (
                self.current_label.config(text=str(idx + 1)),
                self.update_progress(prog),
                self.update_preview()
            ))
            
            self._send_current_sync()
            
            if self.stop_flag:
                break
            
            if i < total_rows - 1:
                time.sleep(0.15)
        
        self.processing = False
        self.update_progress(100)
        self.log_message("✅ 所有資料已發送完成")
        self.update_status("✅ 所有資料已發送完成")
        self.update_ui_state(True)
    
    def _send_current_sync(self):
        """同步發送當前筆（用於send_all）"""
        row = self.rows[self.index]
        sep = self.get_separator()
        mode = self.mode_var.get()
        
        try:
            if mode == "筆":
                pos = self.get_target_pos()
                if not self.stop_flag:
                    content = sep.join(str(cell) for cell in row)
                    pyautogui.click(pos)
                    pyautogui.write(content, interval=0.01)
                    self.log_message(f"✅ 已送出第 {self.index + 1} 筆")
            else:
                if self.auto_col_var.get():
                    for col in row:
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(str(col), interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                else:
                    for col in row:
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(str(col), interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
        except Exception as e:
            self.log_message(f"🔴 發送錯誤（第 {self.index + 1} 筆）: {e}")
    
    # ==================== 關閉處理 ====================
    
    def on_closing(self):
        """視窗關閉事件處理"""
        if self.running or self.processing:
            if not messagebox.askyesno("確認", 
                                      "有任務正在執行，確定要關閉程式嗎？"):
                return
            
            self.stop_flag = True
            self.running = False
            self.processing = False
            time.sleep(0.5)
        
        self.save_settings()
        self.root.destroy()


# -------------------------
# main
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVSender(root)
    root.mainloop()