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

pyautogui.PAUSE = 0.02

class CSVSender:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 MAC. TMS輔助工具")
        
        # 設定視窗大小
        self.root.geometry("680x780")
        self.root.resizable(True, True)
        
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
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 設定Grid權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # -------------------------
        # 標題和時間
        # -------------------------
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 標題
        title = ttk.Label(title_frame, text="MAC TMS輔助工具 v3.0", 
                         font=("Microsoft JhengHei", 14, "bold"), foreground="#2C3E50")
        title.pack(side=tk.LEFT)
        
        # 時間顯示
        self.clock_label = ttk.Label(title_frame, text="", font=("Consolas", 10), foreground="#7F8C8D")
        self.clock_label.pack(side=tk.RIGHT)
        self.update_clock()
        
        # -------------------------
        # CSV 預覽區域
        # -------------------------
        preview_frame = ttk.LabelFrame(main_frame, text="CSV 預覽", padding="10")
        preview_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 設定預覽框架的Grid權重
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # 文字預覽區域
        self.preview_text = tk.Text(preview_frame, height=10, font=("Consolas", 10), fg="blue", wrap=tk.NONE)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        self.preview_text.config(state="disabled")
        
        # 垂直捲軸
        v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_text['yscrollcommand'] = v_scrollbar.set
        
        # 水平捲軸
        h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.preview_text.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.preview_text['xscrollcommand'] = h_scrollbar.set
        
        # -------------------------
        # 輸入 CSV 區域
        # -------------------------
        csv_frame = ttk.LabelFrame(main_frame, text="輸入 CSV", padding="10")
        csv_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 載入按鈕和資訊
        ttk.Button(csv_frame, text="📂 載入 CSV", width=12, 
                  command=self.load_csv_dialog_thread).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.csv_path_label = ttk.Label(csv_frame, text="未載入", foreground="#34495E")
        self.csv_path_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 筆數資訊
        ttk.Label(csv_frame, text="總筆數:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_label = tk.Label(csv_frame, text="0", font=("Consolas", 10, "bold"),
                                   foreground="#2980B9")
        self.total_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(csv_frame, text="當前:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.current_label = tk.Label(csv_frame, text="0", font=("Consolas", 10, "bold"),
                                     foreground="#E74C3C")
        self.current_label.grid(row=0, column=5, sticky=tk.W)
        
        # -------------------------
        # 左側：輸出位置與熱鍵設定
        # -------------------------
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 輸出位置設定框架
        pos_frame = ttk.LabelFrame(left_frame, text="輸出位置與熱鍵設定", padding="10")
        pos_frame.pack(fill=tk.BOTH, expand=True)
        
        # 記憶位置選項
        ttk.Checkbutton(pos_frame, text="記憶輸出位置", variable=self.mem_var, 
                       command=self.update_pos_label).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 位置設定標題
        pos_title = ttk.Label(pos_frame, text="設定輸出位置", font=("Microsoft JhengHei", 10, "bold"))
        pos_title.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 設定位置按鈕
        btn_frame = ttk.Frame(pos_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(btn_frame, text="設定位置", width=10, 
                  command=self.set_position_thread).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="重置位置", width=10, 
                  command=self.reset_pos).pack(side=tk.LEFT)
        
        # 工作位置顯示
        self.pos_label = tk.Label(pos_frame, text="工作窗位置: 未定義", 
                                 fg="purple", anchor="w", font=("Consolas", 9))
        self.pos_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 熱鍵設定框架
        hotkey_frame = ttk.Frame(pos_frame)
        hotkey_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W)
        
        # 送出熱鍵
        ttk.Label(hotkey_frame, text="送出熱鍵:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.send_hotkey = tk.StringVar(value=self.settings.get('send_hotkey', "F8"))
        self.send_entry = ttk.Entry(hotkey_frame, textvariable=self.send_hotkey, width=8)
        self.send_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 15), pady=2)
        self.send_entry.bind("<Key>", self.capture_send_hotkey)
        
        # 停止熱鍵
        ttk.Label(hotkey_frame, text="停止熱鍵:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stop_hotkey = tk.StringVar(value=self.settings.get('stop_hotkey', "F7"))
        self.stop_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=8)
        self.stop_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 15), pady=2)
        self.stop_entry.bind("<Key>", self.capture_stop_hotkey)
        
        # 全部送出熱鍵
        ttk.Label(hotkey_frame, text="全部送出:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.send_all_hotkey = tk.StringVar(value=self.settings.get('send_all_hotkey', "F9"))
        self.send_all_entry = ttk.Entry(hotkey_frame, textvariable=self.send_all_hotkey, width=8)
        self.send_all_entry.grid(row=2, column=1, sticky=tk.W, padx=(5, 15), pady=2)
        self.send_all_entry.bind("<Key>", self.capture_send_all_hotkey)
        
        # 套用熱鍵按鈕
        ttk.Button(pos_frame, text="套用熱鍵", width=10, 
                  command=self.apply_hotkeys).grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # -------------------------
        # 右側：模式與分隔設定
        # -------------------------
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 模式設定框架
        mode_frame = ttk.LabelFrame(right_frame, text="模式與分隔設定", padding="10")
        mode_frame.pack(fill=tk.BOTH, expand=True)
        
        # 輸出模式
        ttk.Label(mode_frame, text="輸出模式:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mode_var = tk.StringVar(value=self.settings.get('mode', "筆"))
        mode_radio_frame = ttk.Frame(mode_frame)
        mode_radio_frame.grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(mode_radio_frame, text="筆輸出", variable=self.mode_var, 
                       value="筆").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_radio_frame, text="欄輸出", variable=self.mode_var, 
                       value="欄").pack(side=tk.LEFT)
        
        # 欄位分隔
        ttk.Label(mode_frame, text="欄位分隔:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.sep_var = tk.StringVar(value=self.settings.get('separator', "Enter"))
        sep_radio_frame = ttk.Frame(mode_frame)
        sep_radio_frame.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(sep_radio_frame, text="Tab", variable=self.sep_var, 
                       value="Tab").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(sep_radio_frame, text="Enter", variable=self.sep_var, 
                       value="Enter").pack(side=tk.LEFT)
        
        # 自動定位延時
        ttk.Label(mode_frame, text="⊙定位延時 (ms):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.delay_var = tk.IntVar(value=self.settings.get('delay', 3000))
        self.delay_spin = ttk.Spinbox(mode_frame, from_=150, to=15000, increment=50, 
                                     textvariable=self.delay_var, width=10)
        self.delay_spin.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 欄位模式完全自動化送出（單獨框架） - 恢復此功能
        auto_frame = ttk.LabelFrame(mode_frame, text="欄位模式設定", padding="5")
        auto_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 自動化送出選項
        self.auto_col_var = tk.BooleanVar(value=self.settings.get('auto_col', False))
        ttk.Checkbutton(auto_frame, text="完全自動化送出", variable=self.auto_col_var).pack(anchor=tk.W, pady=(0, 5))
        
        # 每欄位延時設定
        delay_frame = ttk.Frame(auto_frame)
        delay_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(delay_frame, text="每欄位延時 (ms):").pack(side=tk.LEFT, padx=(0, 5))
        self.col_delay_var = tk.IntVar(value=self.settings.get('col_delay', 500))
        self.col_delay_spin = ttk.Spinbox(delay_frame, from_=200, to=10000, increment=50, 
                                         textvariable=self.col_delay_var, width=8)
        self.col_delay_spin.pack(side=tk.LEFT)
        
        # 透明度
        ttk.Label(mode_frame, text="透明度:").grid(row=4, column=0, sticky=tk.W, pady=2)
        alpha_frame = ttk.Frame(mode_frame)
        alpha_frame.grid(row=4, column=1, sticky=tk.W, pady=2)
        self.alpha_var = tk.DoubleVar(value=self.settings.get('alpha', 1.0))
        alpha_slider = ttk.Scale(alpha_frame, from_=0.3, to=1.0, orient="horizontal", 
                               variable=self.alpha_var, command=self.update_alpha, length=120)
        alpha_slider.pack(side=tk.LEFT, padx=(0, 10))
        self.alpha_label = tk.Label(alpha_frame, text="100%")
        self.alpha_label.pack(side=tk.LEFT)
        
        # 保持置頂
        self.topmost_var = tk.BooleanVar(value=self.settings.get('topmost', True))
        ttk.Checkbutton(mode_frame, text="保持置頂", variable=self.topmost_var, 
                       command=self.update_topmost).grid(row=5, column=0, columnspan=2, 
                                                       sticky=tk.W, pady=2)
        
        # -------------------------
        # 進度條區域（恢復）
        # -------------------------
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        
        ttk.Label(progress_frame, text="進度:").pack(side=tk.LEFT, padx=(0, 10))
        
        # 進度條
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=580, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 進度百分比標籤
        self.progress_label = tk.Label(progress_frame, text="0%", font=("Consolas", 9), 
                                      foreground="#2C3E50", width=5)
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # -------------------------
        # 底部：控制按鈕區域
        # -------------------------
        ctrl_frame = ttk.LabelFrame(main_frame, text="控制按鈕", padding="10")
        ctrl_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 第一排：導航按鈕
        nav_frame = ttk.Frame(ctrl_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.prev_btn = ttk.Button(nav_frame, text="◀ 上一筆", width=10, 
                                  command=self.prev_row)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        
        self.preview_btn = ttk.Button(nav_frame, text="🔍 預覽", width=10,
                                     command=self.preview_data)
        self.preview_btn.pack(side=tk.LEFT, padx=2)
        
        self.next_btn = ttk.Button(nav_frame, text="下一筆 ▶", width=10, 
                                  command=self.next_row)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        
        # 第二排：主要操作按鈕
        op_frame = ttk.Frame(ctrl_frame)
        op_frame.pack(fill=tk.X, pady=5)
        
        self.send_btn = ttk.Button(op_frame, text="🚀送出當前", width=13,
                                  command=self.send_current_thread)
        self.send_btn.pack(side=tk.LEFT, padx=2)
        
        self.send_all_btn = ttk.Button(op_frame, text="⚡全部送出", width=13,
                                      command=self.send_all_thread)
        self.send_all_btn.pack(side=tk.LEFT, padx=2)
        
        # 第三排：控制按鈕
        control_frame = ttk.Frame(ctrl_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸️暫停", width=10,
                                   command=self.toggle_pause)
        self.pause_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(control_frame, text="🛑停止執行", width=10,
                                  command=self.stop_execution)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_btn = ttk.Button(control_frame, text="🗑️清除資料", width=10,
                                   command=self.clear_data)
        self.clear_btn.pack(side=tk.LEFT, padx=2)
        
        # -------------------------
        # 狀態列
        # -------------------------
        self.status_bar = ttk.Label(main_frame, text="就緒", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 設定行和列的權重
        main_frame.rowconfigure(1, weight=1)  # CSV預覽區域可伸展
        main_frame.rowconfigure(3, weight=0)  # 設定區域固定高度
        main_frame.columnconfigure(0, weight=1)  # 左側框架
        main_frame.columnconfigure(1, weight=1)  # 右側框架
    
    def apply_initial_settings(self):
        """套用初始設定"""
        self.update_topmost()
        self.update_alpha(None)
        self.apply_hotkeys()
        self.update_status("就緒")
        self.update_ui_state(False)
        self.update_progress(0)
    
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
            self.log_message("設定已儲存")
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
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)
    
    def update_pos_label(self):
        """更新位置標籤"""
        if self.saved_pos:
            self.pos_label.config(text=f"工作窗位置: ({self.saved_pos[0]}, {self.saved_pos[1]})")
        else:
            self.pos_label.config(text="工作窗位置: 未定義")
    
    def update_status(self, message):
        """更新狀態列"""
        self.status_bar.config(text=message)
    
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
        self.progress_label.config(text=f"{int(value)}%")
    
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
        self.csv_path_label.config(text="載入中...")
        self.update_status("正在載入CSV檔案...")
        
        # 在新線程中載入
        t = threading.Thread(target=self.load_csv_file, args=(path,), daemon=True)
        t.start()
    
    def load_csv_file(self, path):
        """在新線程中載入CSV檔案"""
        try:
            # 嘗試UTF-8編碼
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    rows = [r for r in reader if r]
            except UnicodeDecodeError:
                # 嘗試BIG5編碼
                with open(path, "r", encoding="big5") as f:
                    reader = csv.reader(f)
                    rows = [r for r in reader if r]
            
            self.update_from_queue(self._finish_csv_loading, path, rows)
            
        except Exception as e:
            self.update_from_queue(self._csv_load_error, f"讀取 CSV 發生錯誤：{e}")
    
    def _finish_csv_loading(self, path, rows):
        """完成CSV載入"""
        self.rows = rows
        self.index = 0
        self.csv_path_label.config(text=os.path.basename(path))
        self.total_label.config(text=str(len(self.rows)))
        self.current_label.config(text="1")
        self.update_progress(0)
        self.update_preview()
        self.log_message(f"已載入 {len(self.rows)} 筆資料")
        self.update_ui_state(True)
    
    def _csv_load_error(self, error_msg):
        """CSV載入錯誤處理"""
        self.csv_path_label.config(text="載入失敗")
        self.update_from_queue(lambda: messagebox.showerror("錯誤", error_msg))
        self.update_status("CSV載入失敗")
    
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
            
            # 只顯示前50筆避免過載
            max_display = min(50, len(self.rows))
            
            for i, row in enumerate(self.rows[:max_display]):
                # 限制每行顯示長度
                row_text = " | ".join(row[:8])
                if len(row) > 8 or any(len(cell) > 20 for cell in row):
                    row_text += " ..."
                
                prefix = "▶ " if i == self.index else "   "
                self.preview_text.insert(tk.END, f"{prefix}{i+1}: {row_text}\n")
            
            if len(self.rows) > max_display:
                self.preview_text.insert(tk.END, f"\n... 還有 {len(self.rows)-max_display} 筆資料 ...")
        
        self.preview_text.config(state="disabled")
    
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
        preview_window.geometry("400x300")
        preview_window.transient(self.root)
        
        # 置中顯示
        preview_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (preview_window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (preview_window.winfo_height() // 2)
        preview_window.geometry(f"+{x}+{y}")
        
        # 文字框
        text_widget = tk.Text(preview_window, wrap=tk.WORD, font=("Consolas", 10))
        text_widget.insert(1.0, preview_text)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(preview_window, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        ttk.Button(preview_window, text="關閉", command=preview_window.destroy).pack(pady=5)
    
    def clear_data(self):
        """清除資料"""
        if self.rows:
            if messagebox.askyesno("確認", "確定要清除所有資料嗎？"):
                self.rows = []
                self.index = 0
                self.csv_path_label.config(text="未載入")
                self.total_label.config(text="0")
                self.current_label.config(text="0")
                self.update_progress(0)
                self.update_preview()
                self.log_message("資料已清除")
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
            self.update_from_queue(lambda: self.update_status(f"請將滑鼠移到目標位置，{delay//1000}秒後自動抓取"))
            time.sleep(delay / 1000.0)
            pos = pyautogui.position()
            self.update_from_queue(self._set_position_callback, (pos.x, pos.y))
        
        t = threading.Thread(target=get_position, daemon=True)
        t.start()
    
    def _set_position_callback(self, pos):
        """位置設定回調"""
        self.saved_pos = pos
        self.update_pos_label()
        self.log_message(f"位置已設定：({pos[0]}, {pos[1]})")
    
    def reset_pos(self):
        """重置位置"""
        self.saved_pos = None
        self.update_pos_label()
        self.log_message("輸出位置已重置")
    
    def get_target_pos(self):
        """取得目標位置（同步）"""
        delay = max(150, min(15000, self.delay_var.get()))
        
        if self.mem_var.get() and self.saved_pos:
            return self.saved_pos
        
        self.update_status(f"請選擇輸出位置，{delay//1000}秒後自動定位")
        self.root.update()
        time.sleep(delay / 1000.0)
        pos = pyautogui.position()
        
        if self.mem_var.get():
            self.saved_pos = (pos.x, pos.y)
            self.update_pos_label()
        
        return (pos.x, pos.y)
    
    # ==================== 熱鍵處理 ====================
    
    def capture_send_hotkey(self, event):
        """捕獲送出熱鍵"""
        k = event.keysym
        self.send_hotkey.set(k)
        return "break"
    
    def capture_stop_hotkey(self, event):
        """捕獲停止熱鍵"""
        k = event.keysym
        self.stop_hotkey.set(k)
        return "break"
    
    def capture_send_all_hotkey(self, event):
        """捕獲全部送出熱鍵"""
        k = event.keysym
        self.send_all_hotkey.set(k)
        return "break"
    
    def apply_hotkeys(self):
        """套用熱鍵設定"""
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
            
            self.log_message(f"已套用熱鍵：送出={self.send_hotkey.get()}，停止={self.stop_hotkey.get()}，全部送出={self.send_all_hotkey.get()}")
        except Exception as e:
            messagebox.showwarning("熱鍵綁定失敗", 
                                 f"無法綁定熱鍵：{e}")
    
    # ==================== 控制方法 ====================
    
    def toggle_pause(self):
        """切換暫停狀態"""
        self.pause_flag = not self.pause_flag
        if self.pause_flag:
            self.pause_btn.config(text="▶️ 繼續")
            self.log_message("已暫停")
        else:
            self.pause_btn.config(text="⏸️ 暫停")
            self.log_message("已恢復")
    
    def stop_execution(self, *args):
        """停止執行"""
        if self.running or self.processing:
            self.stop_flag = True
            self.log_message("已停止執行")
        else:
            self.log_message("沒有正在執行的任務")
    
    # ==================== 發送方法 ====================
    
    def send_current_thread(self):
        """發送當前筆（線程封裝）"""
        if self.running:
            self.log_message("已有任務正在執行")
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
        sep = "\t" if self.sep_var.get() == "Tab" else "\n"
        mode = self.mode_var.get()
        
        try:
            if mode == "筆":
                # 整筆輸出
                pos = self.get_target_pos()
                if self.stop_flag:
                    self.running = False
                    return
                
                pyautogui.click(pos)
                pyautogui.write(sep.join(row), interval=0.01)
                self.log_message(f"已送出第 {self.index + 1} 筆資料")
                
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
                        pyautogui.write(col, interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                        
                        self.log_message(f"已送出欄位 {i+1}: {col}")
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
                            self.log_message("使用者取消發送")
                            break
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(col, interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                        
                        self.log_message(f"已送出欄位 {i+1}: {col}")
            
            # 完成處理
            if not self.stop_flag:
                self.update_from_queue(self._finish_current_row)
            else:
                self.log_message("發送已中斷")
                self.update_status("發送已中斷")
                
        except Exception as e:
            self.update_from_queue(lambda: messagebox.showerror("執行錯誤", f"執行時發生錯誤：{e}"))
            self.log_message(f"執行錯誤: {e}")
        finally:
            self.running = False
    
    def _finish_current_row(self):
        """完成當前筆處理"""
        if not self.stop_flag and self.index < len(self.rows) - 1:
            self.index += 1
            self.current_label.config(text=str(self.index + 1))
            self.update_preview()
            self.update_status("已送出本筆，自動跳至下一筆")
        else:
            self.update_status("發送完成")
    
    def send_all_thread(self):
        """發送全部（線程封裝）"""
        if not self.rows:
            self.log_message("尚未載入CSV資料")
            return
        
        if self.running or self.processing:
            self.log_message("已有任務正在執行")
            return
        
        # 確認對話
        remaining = len(self.rows) - self.index
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
        
        for i in range(self.index, total_rows):
            if self.stop_flag:
                break
            
            # 檢查暫停
            while self.pause_flag and not self.stop_flag:
                time.sleep(0.1)
            
            # 更新當前索引
            self.index = i
            progress = (i + 1) / total_rows * 100
            self.update_from_queue(lambda idx=i, prog=progress: (
                self.current_label.config(text=str(idx + 1)),
                self.update_progress(prog),
                self.update_preview()
            ))
            
            # 發送當前筆
            self._send_current_sync()
            
            if self.stop_flag:
                break
            
            # 小暫停
            if i < total_rows - 1:
                time.sleep(0.15)
        
        self.processing = False
        self.update_progress(100)
        self.log_message("所有資料已發送完成")
        self.update_status("所有資料已發送完成")
        self.update_ui_state(True)
    
    def _send_current_sync(self):
        """同步發送當前筆（用於send_all）"""
        row = self.rows[self.index]
        sep = "\t" if self.sep_var.get() == "Tab" else "\n"
        mode = self.mode_var.get()
        
        try:
            if mode == "筆":
                # 整筆輸出
                pos = self.get_target_pos()
                if not self.stop_flag:
                    pyautogui.click(pos)
                    pyautogui.write(sep.join(row), interval=0.01)
                    self.log_message(f"已送出第 {self.index + 1} 筆")
            else:
                # 欄位輸出 - 根據設定選擇模式
                if self.auto_col_var.get():
                    # 完全自動化模式
                    for col in row:
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(col, interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
                else:
                    # 批量模式使用自動化，避免頻繁確認
                    for col in row:
                        if self.stop_flag:
                            break
                        
                        while self.pause_flag and not self.stop_flag:
                            time.sleep(0.1)
                        
                        pos = self.get_target_pos()
                        if self.stop_flag:
                            break
                        
                        pyautogui.click(pos)
                        pyautogui.write(col, interval=0.01)
                        pyautogui.write(sep, interval=0.01)
                        time.sleep(max(0.2, self.col_delay_var.get()/1000))
        except Exception as e:
            self.log_message(f"發送錯誤（第 {self.index + 1} 筆）: {e}")
    
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
            time.sleep(0.5)  # 給線程一點時間停止
        
        self.save_settings()
        self.root.destroy()


# -------------------------
# main
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVSender(root)
    root.mainloop()