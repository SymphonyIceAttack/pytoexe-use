"""
长崎AI质检著录软件V2.0
功能：
- 图像质检：空白页检测、页码连续性检查、歪斜检测
- AI著录：根据Excel模板自动著录
- 自动保存：实时保存数据到临时文件
- 批量处理：支持多文件夹、多图片处理
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from PIL import Image, ImageFilter, ImageEnhance
import pandas as pd
from pathlib import Path
import json
import time
from datetime import datetime
import shutil
import atexit

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

import cv2
import numpy as np

import ollama

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class ArchiveQCSystem(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("长崎AI质检著录系统V2.0")
        self.geometry("1500x900")
        self.minsize(1200, 700)
        
        self.image_folder = ""
        self.template_file = ""
        self.images = []
        self.current_index = 0
        self.quality_results = []
        self.catalog_results = []
        self.ollama_model = "qwen2.5:7b"
        
        self.auto_save_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_save.xlsx")
        self.save_backup_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_save_backup.xlsx")
        self.last_save_time = 0
        self.auto_save_interval = 5
        
        self.is_paused = False
        self.is_stopped = False
        self.current_task = None
        self.catalog_thread = None
        self.quality_thread = None
        
        self.template_columns = []
        self.image_rotation = 0
        
        if KEYBOARD_AVAILABLE:
            self.register_shortcuts()
        
        atexit.register(self.on_exit)
        
        self.setup_ui()
        
    def register_shortcuts(self):
        try:
            keyboard.add_hotkey('ctrl+s', self.quick_save)
            keyboard.add_hotkey('ctrl+e', self.quick_export)
            keyboard.add_hotkey('ctrl+q', self.quick_exit)
        except Exception as e:
            pass
    
    def quick_save(self):
        self.auto_save(force=True)
        
    def quick_export(self):
        self.export_report()
        
    def quick_exit(self):
        self.on_exit()
        self.quit()
        
    def setup_ui(self):
        # 标题栏
        title_bar = ctk.CTkFrame(self, height=50, fg_color="#1E3A5F")
        title_bar.pack(fill="x", padx=0, pady=0)
        title_bar.pack_propagate(False)
        
        title_content = ctk.CTkFrame(title_bar, fg_color="transparent")
        title_content.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 左侧标题
        title_left = ctk.CTkFrame(title_content, fg_color="transparent")
        title_left.pack(side="left", fill="y")
        
        title_label = ctk.CTkLabel(
            title_left,
            text="长崎AI质检著录系统V2.0",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=2)
        
        # 右侧状态
        title_right = ctk.CTkFrame(title_content, fg_color="transparent")
        title_right.pack(side="right", fill="y")
        
        self.status_label = ctk.CTkLabel(
            title_right,
            text="✅ 系统就绪",
            font=ctk.CTkFont(size=11),
            text_color="#4CAF50"
        )
        self.status_label.pack(pady=10)
        
        # 主布局 - 三栏式
        main_container = ctk.CTkFrame(self, fg_color="#F5F7FA")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        left_panel = ctk.CTkFrame(main_container, width=280, fg_color="white", corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 8))
        left_panel.pack_propagate(False)
        
        # 左侧滚动区域
        self.left_scroll = ctk.CTkScrollableFrame(left_panel, width=265, label_fg_color="transparent")
        self.left_scroll.pack(fill="both", expand=True, padx=5, pady=8)
        
        # 中间图片预览区
        center_panel = ctk.CTkFrame(main_container, width=400, fg_color="white", corner_radius=10)
        center_panel.pack(side="left", fill="y", padx=(0, 8))
        center_panel.pack_propagate(False)
        
        # 右侧结果区
        right_panel = ctk.CTkFrame(main_container, fg_color="white", corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.setup_left_panel(self.left_scroll)
        self.setup_center_panel(center_panel)
        self.setup_right_panel(right_panel)
        
    def setup_left_panel(self, parent):
        # 1. 数据源配置
        self.add_section(parent, "📂 数据源配置", "#4299E1")
        
        folder_card = self.create_card(parent)
        ctk.CTkButton(
            folder_card,
            text="选择图片文件夹",
            command=self.select_folder,
            height=32,
            fg_color="#4299E1",
            hover_color="#3182CE",
            font=ctk.CTkFont(size=11)
        ).pack(fill="x", padx=10, pady=(10, 6))
        
        self.folder_label = ctk.CTkLabel(folder_card, text="未选择", text_color="#6B7280", font=ctk.CTkFont(size=10))
        self.folder_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        self.subfolder_check = ctk.CTkCheckBox(folder_card, text="包含子文件夹", checkbox_width=16, checkbox_height=16, font=ctk.CTkFont(size=10))
        self.subfolder_check.pack(anchor="w", padx=10, pady=(0, 10))
        self.subfolder_check.select()
        
        # 2. 著录模板
        self.add_section(parent, "📋 著录模板", "#667EEA")
        
        template_card = self.create_card(parent)
        ctk.CTkButton(
            template_card,
            text="选择Excel模板",
            command=self.select_template,
            height=32,
            fg_color="#667EEA",
            hover_color="#5A67D8",
            font=ctk.CTkFont(size=11)
        ).pack(fill="x", padx=10, pady=(10, 6))
        
        self.template_label = ctk.CTkLabel(template_card, text="未选择", text_color="#6B7280", font=ctk.CTkFont(size=10))
        self.template_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        # 识别范围
        ctk.CTkLabel(template_card, text="识别范围:", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=10, pady=(6, 3))
        
        self.radio_var = ctk.StringVar(value="all")
        self.radio_all = ctk.CTkRadioButton(template_card, text="全部图片", variable=self.radio_var, value="all", command=self.update_catalog_options, font=ctk.CTkFont(size=10))
        self.radio_all.pack(anchor="w", padx=20, pady=2)
        self.radio_all.select()
        
        self.radio_first = ctk.CTkRadioButton(template_card, text="前N张图片", variable=self.radio_var, value="first", command=self.update_catalog_options, font=ctk.CTkFont(size=10))
        self.radio_first.pack(anchor="w", padx=20, pady=2)
        
        n_frame = ctk.CTkFrame(template_card, fg_color="transparent")
        n_frame.pack(anchor="w", padx=25, pady=3)
        
        ctk.CTkLabel(n_frame, text="N =", font=ctk.CTkFont(size=10)).pack(side="left")
        self.first_n_entry = ctk.CTkEntry(n_frame, height=24, width=45, font=ctk.CTkFont(size=10))
        self.first_n_entry.insert(0, "3")
        self.first_n_entry.pack(side="left", padx=4)
        self.first_n_entry.configure(state="disabled")
        
        # 编辑提示词按钮
        ctk.CTkButton(
            template_card,
            text="✏️ 编辑字段提示词",
            command=self.edit_field_prompts,
            height=26,
            fg_color="#718096",
            hover_color="#4A5568",
            font=ctk.CTkFont(size=10)
        ).pack(fill="x", padx=10, pady=(8, 10))
        
        self.field_prompts = {}
        
        # 3. 档案模式
        self.add_section(parent, "📁 档案模式", "#ED8936")
        
        mode_card = self.create_card(parent)
        self.archive_mode_var = ctk.StringVar(value="folder")
        
        self.archive_mode_folder = ctk.CTkRadioButton(mode_card, text="每文件夹为一件", variable=self.archive_mode_var, value="folder", command=self.update_archive_mode, font=ctk.CTkFont(size=10))
        self.archive_mode_folder.pack(anchor="w", padx=12, pady=5)
        self.archive_mode_folder.select()
        
        self.archive_mode_image = ctk.CTkRadioButton(mode_card, text="每图片为一件", variable=self.archive_mode_var, value="image", command=self.update_archive_mode, font=ctk.CTkFont(size=10))
        self.archive_mode_image.pack(anchor="w", padx=12, pady=5)
        
        # 4. AI设置
        self.add_section(parent, "🤖 AI模型", "#48BB78")
        
        ai_card = self.create_card(parent)
        
        ctk.CTkLabel(ai_card, text="选择模型:", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=10, pady=(8, 3))
        
        self.model_combo = ctk.CTkComboBox(ai_card, height=28, values=["模拟模型 (测试用)"], font=ctk.CTkFont(size=10))
        self.model_combo.set("模拟模型 (测试用)")
        self.model_combo.pack(fill="x", padx=10, pady=3)
        
        ctk.CTkButton(
            ai_card,
            text="🔗 检查AI连接",
            command=self.check_ollama_connection,
            height=28,
            fg_color="#48BB78",
            hover_color="#38A169",
            font=ctk.CTkFont(size=10)
        ).pack(fill="x", padx=10, pady=(6, 8))
        
        self.ai_status_label = ctk.CTkLabel(ai_card, text="模拟模式", text_color="#48BB78", font=ctk.CTkFont(size=9))
        self.ai_status_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        # 5. 数据管理
        self.add_section(parent, "💾 数据管理", "#63B3ED")
        
        data_card = self.create_card(parent)
        
        ctk.CTkButton(
            data_card,
            text="📥 加载上次数据",
            command=self.load_auto_save,
            height=26,
            fg_color="#63B3ED",
            hover_color="#4299E1",
            font=ctk.CTkFont(size=10)
        ).pack(fill="x", padx=10, pady=(8, 4))
        
        ctk.CTkButton(
            data_card,
            text="🗑️ 清除缓存",
            command=self.clear_cache_data,
            height=26,
            fg_color="#E53935",
            hover_color="#C62828",
            font=ctk.CTkFont(size=10)
        ).pack(fill="x", padx=10, pady=4)
        
        ctk.CTkButton(
            data_card,
            text="📝 清空日志",
            command=self.clear_log,
            height=26,
            fg_color="#718096",
            hover_color="#4A5568",
            font=ctk.CTkFont(size=10)
        ).pack(fill="x", padx=10, pady=(4, 10))
        
        # 6. 执行操作
        self.add_section(parent, "🚀 执行操作", "#9F7AEA")
        
        action_card = self.create_card(parent)
        
        ctk.CTkButton(
            action_card,
            text="🔍 开始质检",
            command=self.start_quality_check,
            height=34,
            fg_color="#ED8936",
            hover_color="#DD6B20",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkButton(
            action_card,
            text="✍️ 开始著录",
            command=self.start_catalog,
            height=34,
            fg_color="#9F7AEA",
            hover_color="#805AD5",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            action_card,
            text="📤 导出报告",
            command=self.export_report,
            height=34,
            fg_color="#48BB78",
            hover_color="#38A169",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(fill="x", padx=10, pady=(5, 10))
        
        # 7. 进度与控制
        self.add_section(parent, "📊 处理进度", "#4A5568")
        
        progress_card = self.create_card(parent)
        
        self.progress_bar = ctk.CTkProgressBar(progress_card, height=12, corner_radius=6)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 3))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_card, text="准备就绪", text_color="#6B7280", font=ctk.CTkFont(size=10))
        self.progress_label.pack(anchor="w", padx=10, pady=(3, 6))
        
        # 控制按钮
        control_frame = ctk.CTkFrame(progress_card, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.pause_btn = ctk.CTkButton(
            control_frame,
            text="⏸️",
            command=self.pause_catalog,
            width=65,
            height=30,
            fg_color="#FB8C00",
            hover_color="#F57C00",
            state="disabled",
            font=ctk.CTkFont(size=12)
        )
        self.pause_btn.pack(side="left", padx=2)
        
        self.resume_btn = ctk.CTkButton(
            control_frame,
            text="▶️",
            command=self.resume_catalog,
            width=65,
            height=30,
            fg_color="#48BB78",
            hover_color="#38A169",
            state="disabled",
            font=ctk.CTkFont(size=12)
        )
        self.resume_btn.pack(side="left", padx=2)
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹️",
            command=self.stop_catalog,
            width=65,
            height=30,
            fg_color="#E53935",
            hover_color="#C62828",
            state="disabled",
            font=ctk.CTkFont(size=12)
        )
        self.stop_btn.pack(side="left", padx=2)
        
    def create_card(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=10)
        frame.pack(fill="x", padx=5, pady=6)
        return frame
        
    def add_section(self, parent, title, color):
        section_frame = ctk.CTkFrame(parent, fg_color="transparent")
        section_frame.pack(fill="x", padx=5, pady=(12, 0))
        
        color_bar = ctk.CTkFrame(section_frame, width=4, height=18, fg_color=color, corner_radius=2)
        color_bar.pack(side="left", padx=(0, 6))
        
        title_label = ctk.CTkLabel(section_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="#1F2937")
        title_label.pack(side="left")
        
    def setup_center_panel(self, parent):
        # 图片预览区
        preview_frame = ctk.CTkFrame(parent, fg_color="#F7FAFC", corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=(10, 6))
        
        self.img_label = ctk.CTkLabel(preview_frame, text="请选择图片文件夹", text_color="#9CA3AF", font=ctk.CTkFont(size=13))
        self.img_label.pack(fill="both", expand=True)
        
        # 工具栏
        toolbar_frame = ctk.CTkFrame(parent, fg_color="#EDF2F7", corner_radius=10)
        toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 导航
        nav_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        nav_frame.pack(side="left", padx=8, pady=6)
        
        ctk.CTkButton(
            nav_frame,
            text="◀",
            command=self.prev_image,
            width=45,
            height=28,
            fg_color="#4A5568",
            hover_color="#2D3748",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=2)
        
        self.page_label = ctk.CTkLabel(nav_frame, text="0 / 0", font=ctk.CTkFont(size=11))
        self.page_label.pack(side="left", padx=10)
        
        ctk.CTkButton(
            nav_frame,
            text="▶",
            command=self.next_image,
            width=45,
            height=28,
            fg_color="#4A5568",
            hover_color="#2D3748",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=2)
        
        # 操作按钮
        action_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        action_frame.pack(side="right", padx=8, pady=6)
        
        ctk.CTkButton(
            action_frame,
            text="↻",
            command=self.rotate_image,
            width=45,
            height=28,
            fg_color="#63B3ED",
            hover_color="#4299E1",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=2)
        
        # 统计信息卡片
        stats_frame = ctk.CTkFrame(parent, fg_color="#F7FAFC", corner_radius=10)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.stats_labels = {}
        
        stats_items = [
            ("🖼️", "总图片", "#4299E1"),
            ("✅", "已质检", "#48BB78"),
            ("⚠️", "空白页", "#ED8936"),
            ("📏", "歪斜", "#F56565"),
            ("✍️", "已著录", "#9F7AEA"),
            ("📂", "文件夹", "#63B3ED")
        ]
        
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=8, pady=8)
        
        for i, (icon, label, color) in enumerate(stats_items):
            stat_card = ctk.CTkFrame(stats_grid, fg_color="white", corner_radius=8, height=55)
            stat_card.grid(row=0, column=i, padx=4, sticky="nsew")
            
            icon_label = ctk.CTkLabel(stat_card, text=icon, font=ctk.CTkFont(size=18))
            icon_label.pack(pady=(4, 1))
            
            value_label = ctk.CTkLabel(stat_card, text="0", font=ctk.CTkFont(size=15, weight="bold"), text_color=color)
            value_label.pack(pady=(0, 1))
            
            name_label = ctk.CTkLabel(stat_card, text=label, font=ctk.CTkFont(size=8), text_color="#6B7280")
            name_label.pack()
            
            self.stats_labels[label] = value_label
        
        stats_grid.grid_columnconfigure(tuple(range(6)), weight=1)
        
    def setup_right_panel(self, parent):
        # 标签页
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)
        
        # 质检结果
        qc_frame = ctk.CTkFrame(self.notebook, fg_color="white")
        self.notebook.add(qc_frame, text="✅ 质检结果")
        
        qc_table_frame = ctk.CTkFrame(qc_frame, fg_color="white")
        qc_table_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        columns = ("文件名", "空白页", "歪斜角度", "页码", "状态")
        self.qc_tree = ttk.Treeview(qc_table_frame, columns=columns, show="headings", height=16)
        
        for col in columns:
            self.qc_tree.heading(col, text=col)
            self.qc_tree.column(col, width=100 if col != "文件名" else 180)
        
        scrollbar = ttk.Scrollbar(qc_table_frame, orient="vertical", command=self.qc_tree.yview)
        self.qc_tree.configure(yscrollcommand=scrollbar.set)
        
        self.qc_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 著录结果
        catalog_frame = ctk.CTkFrame(self.notebook, fg_color="white")
        self.notebook.add(catalog_frame, text="📝 著录结果")
        
        catalog_table_frame = ctk.CTkFrame(catalog_frame, fg_color="white")
        catalog_table_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.catalog_tree = ttk.Treeview(catalog_table_frame, columns=(), show="headings", height=16)
        
        catalog_scrollbar = ttk.Scrollbar(catalog_table_frame, orient="vertical", command=self.catalog_tree.yview)
        self.catalog_tree.configure(yscrollcommand=catalog_scrollbar.set)
        
        self.catalog_tree.pack(side="left", fill="both", expand=True)
        catalog_scrollbar.pack(side="right", fill="y")
        
        # 操作日志
        log_frame = ctk.CTkFrame(self.notebook, fg_color="white")
        self.notebook.add(log_frame, text="📋 操作日志")
        
        log_container = ctk.CTkFrame(log_frame, fg_color="#1A202C", corner_radius=8)
        log_container.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.log_text = ctk.CTkTextbox(log_container, font=("Consolas", 9), fg_color="#1A202C", text_color="#E2E8F0")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        
    def update_stats(self):
        total_images = len(self.images)
        qc_count = len(self.quality_results)
        catalog_count = len(self.catalog_results)
        
        blank_count = sum(1 for r in self.quality_results if r.get('blank', False))
        skew_count = sum(1 for r in self.quality_results if abs(r.get('skew_angle', 0)) > 3)
        
        folder_groups = {}
        for img_path in self.images:
            folder = os.path.dirname(img_path)
            if folder not in folder_groups:
                folder_groups[folder] = []
            folder_groups[folder].append(img_path)
        
        self.stats_labels["总图片"].configure(text=str(total_images))
        self.stats_labels["已质检"].configure(text=str(qc_count))
        self.stats_labels["空白页"].configure(text=str(blank_count))
        self.stats_labels["歪斜"].configure(text=str(skew_count))
        self.stats_labels["已著录"].configure(text=str(catalog_count))
        self.stats_labels["文件夹"].configure(text=str(len(folder_groups)))
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", full_message)
        self.log_text.see("end")
        
        os.makedirs("Log", exist_ok=True)
        log_file = os.path.join("Log", f"log_{datetime.now().strftime('%Y%m%d')}.txt")
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(full_message)
        except Exception as e:
            print(f"保存日志失败: {e}")
        
    def select_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_folder = folder
            self.folder_label.configure(text=os.path.basename(folder))
            self.load_images()
            self.update_stats()
            self.log(f"已选择文件夹: {folder}")
            
    def select_template(self):
        file = filedialog.askopenfilename(
            title="选择著录模板",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file:
            self.template_file = file
            self.template_label.configure(text=os.path.basename(file))
            try:
                df = pd.read_excel(file)
                self.template_columns = df.columns.tolist()
            except Exception as e:
                self.template_columns = []
            self.log(f"已选择模板: {file}")
            
    def update_catalog_options(self):
        if self.radio_var.get() == "first":
            self.first_n_entry.configure(state="normal")
        else:
            self.first_n_entry.configure(state="disabled")
    
    def update_archive_mode(self):
        mode = self.archive_mode_var.get()
        self.log(f"档案模式: {'每文件夹为一件' if mode == 'folder' else '每图片为一件'}")
    
    def edit_field_prompts(self):
        if not self.template_file:
            messagebox.showwarning("警告", "请先选择著录模板")
            return
        
        try:
            df_template = pd.read_excel(self.template_file)
            columns = df_template.columns.tolist()
            
            dialog = ctk.CTkToplevel(self)
            dialog.title("编辑字段提示词")
            dialog.geometry("550x450")
            dialog.grab_set()
            
            scroll_frame = ctk.CTkScrollableFrame(dialog)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            prompt_entries = {}
            
            for col in columns:
                frame = ctk.CTkFrame(scroll_frame, fg_color="#EDF2F7", corner_radius=8)
                frame.pack(fill="x", pady=4)
                
                ctk.CTkLabel(frame, text=col, font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=6)
                
                entry = ctk.CTkEntry(frame, height=32, placeholder_text=f"输入{col}的识别提示词...")
                entry.pack(fill="x", padx=10, pady=4)
                
                if col in self.field_prompts:
                    entry.insert(0, self.field_prompts[col])
                
                prompt_entries[col] = entry
            
            def save_prompts():
                for col, entry in prompt_entries.items():
                    self.field_prompts[col] = entry.get().strip()
                dialog.destroy()
                self.log("字段提示词已更新")
            
            button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            button_frame.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkButton(button_frame, text="保存", command=save_prompts, height=32, fg_color="#48BB78").pack(fill="x")
            
        except Exception as e:
            messagebox.showerror("错误", f"读取模板失败: {e}")
    
    def load_images(self):
        if not self.image_folder:
            return
            
        extensions = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp")
        self.images = []
        
        if self.subfolder_check.get():
            for root, dirs, files in os.walk(self.image_folder):
                for f in sorted(files):
                    if f.lower().endswith(extensions):
                        self.images.append(os.path.join(root, f))
        else:
            for f in sorted(os.listdir(self.image_folder)):
                if f.lower().endswith(extensions):
                    self.images.append(os.path.join(self.image_folder, f))
                
        if self.images:
            self.current_index = 0
            self.image_rotation = 0
            self.display_image()
            self.log(f"已加载 {len(self.images)} 张图片")
            
    def display_image(self):
        if not self.images:
            return
            
        img_path = self.images[self.current_index]
        self.page_label.configure(text=f"{self.current_index + 1} / {len(self.images)}")
        
        try:
            img = Image.open(img_path)
            
            if self.image_rotation != 0:
                img = img.rotate(self.image_rotation, expand=True)
            
            max_size = (360, 520)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            img.save("_temp_display.png")
            
            self.img_label.configure(image=None)
            self.img_label.configure(text="")
            
            self.current_img = ctk.CTkImage(Image.open("_temp_display.png"), size=img.size)
            self.img_label.configure(image=self.current_img)
            
        except Exception as e:
            self.log(f"显示图片失败: {e}")
            
    def rotate_image(self):
        if self.images:
            self.image_rotation += 90
            if self.image_rotation >= 360:
                self.image_rotation = 0
            self.display_image()
            
    def prev_image(self):
        if self.images and self.current_index > 0:
            self.current_index -= 1
            self.image_rotation = 0
            self.display_image()
            
    def next_image(self):
        if self.images and self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.image_rotation = 0
            self.display_image()
            
    def check_ollama_connection(self):
        try:
            models = ollama.list()
            if models and hasattr(models, 'models'):
                model_names = [m.get('name', '') for m in models.models] if isinstance(models.models, list) else []
                if model_names:
                    model_list = ["模拟模型 (测试用)"] + model_names
                    self.model_combo.configure(values=model_list)
                    self.model_combo.set(model_names[0])
                    self.ollama_model = model_names[0]
                    self.ai_status_label.configure(text=f"已连接 ({len(model_names)}个模型)", text_color="green")
                    self.log(f"AI连接成功，可用模型: {', '.join(model_names)}")
                    return
            self.model_combo.configure(values=["模拟模型 (测试用)"])
            self.model_combo.set("模拟模型 (测试用)")
            self.ai_status_label.configure(text="模拟模式", text_color="#48BB78")
            self.log("未检测到Ollama模型，使用模拟模式")
        except Exception as e:
            self.model_combo.configure(values=["模拟模型 (测试用)"])
            self.model_combo.set("模拟模型 (测试用)")
            self.ai_status_label.configure(text="连接失败，模拟模式", text_color="red")
            self.log(f"AI连接失败: {e}")
            
    def auto_save(self, force=False):
        if not self.quality_results and not self.catalog_results:
            return
            
        try:
            if os.path.exists(self.auto_save_file):
                if os.path.exists(self.save_backup_file):
                    os.remove(self.save_backup_file)
                shutil.copy2(self.auto_save_file, self.save_backup_file)
            
            with pd.ExcelWriter(self.auto_save_file, engine="openpyxl") as writer:
                if self.quality_results:
                    df_qc = pd.DataFrame(self.quality_results)
                    df_qc.to_excel(writer, sheet_name="质检结果", index=False)
                    
                if self.catalog_results:
                    df_catalog = pd.DataFrame(self.catalog_results)
                    df_catalog.to_excel(writer, sheet_name="著录结果", index=False)
                
                meta_data = {
                    "保存时间": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "质检数量": [len(self.quality_results)],
                    "著录数量": [len(self.catalog_results)],
                    "模板列": [", ".join(self.template_columns) if self.template_columns else ""]
                }
                df_meta = pd.DataFrame(meta_data)
                df_meta.to_excel(writer, sheet_name="元数据", index=False)
            
            if force:
                self.log(f"✅ 数据已保存")
            
        except Exception as e:
            self.log(f"⚠️ 自动保存失败: {e}")
    
    def load_auto_save(self):
        if not os.path.exists(self.auto_save_file):
            if os.path.exists(self.save_backup_file):
                try:
                    os.rename(self.save_backup_file, self.auto_save_file)
                    self.log("✅ 使用备份文件恢复")
                except Exception as e:
                    self.log(f"无法恢复备份: {e}")
                    return
            else:
                messagebox.showinfo("提示", "没有找到上次保存的数据")
                return
                
        try:
            if "质检结果" in pd.ExcelFile(self.auto_save_file).sheet_names:
                df_qc = pd.read_excel(self.auto_save_file, sheet_name="质检结果")
                self.quality_results = df_qc.to_dict('records')
                self.log(f"✅ 恢复 {len(self.quality_results)} 条质检数据")
                
                self.qc_tree.delete(*self.qc_tree.get_children())
                for result in self.quality_results:
                    self.update_qc_table(result)
            
            if "著录结果" in pd.ExcelFile(self.auto_save_file).sheet_names:
                df_catalog = pd.read_excel(self.auto_save_file, sheet_name="著录结果")
                self.catalog_results = df_catalog.to_dict('records')
                self.log(f"✅ 恢复 {len(self.catalog_results)} 条著录数据")
                
                if self.catalog_results:
                    sample = self.catalog_results[0]
                    columns = list(sample.keys())
                    if "文件夹" not in columns:
                        columns = ["文件夹", "文件名"] + [c for c in columns if c not in ["文件名"]]
                    self.catalog_tree.delete(*self.catalog_tree.get_children())
                    self.catalog_tree["columns"] = columns
                    for col in columns:
                        self.catalog_tree.heading(col, text=col)
                        self.catalog_tree.column(col, width=100 if col not in ["文件名", "文件夹"] else 150)
                    for result in self.catalog_results:
                        row_values = [result.get(col, "") for col in columns]
                        self.catalog_tree.insert("", 0, values=row_values)
            
            if "元数据" in pd.ExcelFile(self.auto_save_file).sheet_names:
                df_meta = pd.read_excel(self.auto_save_file, sheet_name="元数据")
                if not df_meta.empty and "模板列" in df_meta.columns:
                    template_col_str = df_meta.iloc[0]["模板列"]
                    if isinstance(template_col_str, str) and template_col_str:
                        self.template_columns = [c.strip() for c in template_col_str.split(",")]
            
            self.update_stats()
            messagebox.showinfo("成功", f"已恢复数据:\n- 质检: {len(self.quality_results)} 条\n- 著录: {len(self.catalog_results)} 条")
            
        except Exception as e:
            self.log(f"⚠️ 加载失败: {e}")
    
    def on_exit(self):
        if self.quality_results or self.catalog_results:
            try:
                self.auto_save(force=True)
            except:
                pass
    
    def clear_cache_data(self):
        if not self.quality_results and not self.catalog_results:
            messagebox.showinfo("提示", "没有缓存数据需要清除")
            return
            
        result = messagebox.askyesno(
            "确认清除",
            f"确定要删除所有缓存数据吗？\n\n当前数据：\n- 质检: {len(self.quality_results)} 条\n- 著录: {len(self.catalog_results)} 条\n\n此操作不可恢复！"
        )
        
        if result:
            self.quality_results = []
            self.catalog_results = []
            
            self.qc_tree.delete(*self.qc_tree.get_children())
            self.catalog_tree.delete(*self.catalog_tree.get_children())
            
            if os.path.exists(self.auto_save_file):
                os.remove(self.auto_save_file)
            if os.path.exists(self.save_backup_file):
                os.remove(self.save_backup_file)
            
            self.update_stats()
            self.log("✅ 缓存已清除")
            messagebox.showinfo("成功", "缓存数据已清除")
    
    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self.log("日志已清空")
        messagebox.showinfo("成功", "日志已清空")
    
    def start_quality_check(self):
        if not self.images:
            messagebox.showwarning("警告", "请先选择图片文件夹")
            return
            
        self.is_paused = False
        self.is_stopped = False
        self.current_task = "quality"
        
        self.log("=" * 50)
        self.log("开始质检...")
        
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.resume_btn.configure(state="disabled")
        
        self.quality_thread = threading.Thread(target=self.quality_check_worker)
        self.quality_thread.daemon = True
        self.quality_thread.start()
        
    def quality_check_worker(self):
        self.quality_results = []
        total = len(self.images)
        
        for i, img_path in enumerate(self.images):
            if self.is_stopped:
                self.log("质检已停止")
                break
                
            while self.is_paused:
                self.progress_label.configure(text="已暂停...")
                self.update_idletasks()
                time.sleep(0.5)
            
            self.progress_bar.set((i + 1) / total)
            self.progress_label.configure(text=f"质检: {i + 1}/{total}")
            
            result = self.check_single_image(img_path, i + 1)
            self.quality_results.append(result)
            
            self.update_qc_table(result)
            
            if (i + 1) % self.auto_save_interval == 0 or i == total - 1:
                self.auto_save()
            
            if (i + 1) % 10 == 0:
                self.update_idletasks()
                
        if not self.is_stopped:
            self.progress_label.configure(text="质检完成")
            self.log(f"质检完成，共检查 {total} 张图片")
            
            issues = [r for r in self.quality_results if r["status"] != "正常"]
            if issues:
                self.log(f"⚠️ 发现 {len(issues)} 张图片存在问题")
            else:
                self.log("✅ 所有图片均正常")
        else:
            self.progress_label.configure(text="质检已停止")
            self.auto_save(force=True)
            
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.current_task = None
        self.update_stats()
            
    def check_single_image(self, img_path, index):
        filename = os.path.basename(img_path)
        result = {
            "index": index,
            "filename": filename,
            "blank": False,
            "skew_angle": 0,
            "page_num": None,
            "status": "正常"
        }
        
        try:
            img = cv2.imread(img_path)
            if img is None:
                result["status"] = "无法读取"
                return result
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            mean_intensity = np.mean(gray)
            if mean_intensity > 240:
                result["blank"] = True
                result["status"] = "空白页"
                
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            
            if lines is not None and len(lines) > 0:
                angles = []
                for line in lines[:20]:
                    rho, theta = line[0]
                    angle = np.degrees(theta) - 90
                    if -45 <= angle <= 45:
                        angles.append(angle)
                        
                if angles:
                    result["skew_angle"] = round(np.median(angles), 2)
                    if abs(result["skew_angle"]) > 3:
                        result["status"] = "歪斜"
                        
            h, w = gray.shape
            bottom_right = gray[int(h*0.85):, int(w*0.85):]
            _, binary = cv2.threshold(bottom_right, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                x, y, cw, ch = cv2.boundingRect(cnt)
                if 10 < cw < 100 and 15 < ch < 80:
                    result["page_num"] = "检测到数字"
                    break
                    
            if result["blank"]:
                result["status"] = "空白页"
            elif abs(result["skew_angle"]) > 3:
                result["status"] = "歪斜"
                
        except Exception as e:
            result["status"] = f"错误: {e}"
            self.log(f"处理 {filename} 出错: {e}")
            
        return result
        
    def update_qc_table(self, result):
        status_emoji = {
            "正常": "✅",
            "空白页": "⚠️",
            "歪斜": "📏",
            "错误": "❌",
            "无法读取": "❌"
        }
        
        self.qc_tree.insert("", 0, values=(
            result["filename"],
            "是" if result["blank"] else "否",
            f"{result['skew_angle']}°",
            result["page_num"] or "-",
            f"{status_emoji.get(result['status'], '❓')} {result['status']}"
        ))
        
    def start_catalog(self):
        if not self.images:
            messagebox.showwarning("警告", "请先选择图片文件夹")
            return
            
        if not self.template_file:
            messagebox.showwarning("警告", "请先选择著录模板")
            return
            
        self.is_paused = False
        self.is_stopped = False
        
        self.log("=" * 50)
        self.log("开始著录...")
        
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.resume_btn.configure(state="disabled")
        
        self.catalog_thread = threading.Thread(target=self.catalog_worker)
        self.catalog_thread.daemon = True
        self.catalog_thread.start()
        
    def catalog_worker(self):
        try:
            df_template = pd.read_excel(self.template_file)
            columns = df_template.columns.tolist()
            self.template_columns = columns
            
            self.log(f"模板列: {columns}")
            
            self.catalog_tree.delete(*self.catalog_tree.get_children())
            self.catalog_tree["columns"] = ["文件夹", "文件名"] + columns
            for col in ["文件夹", "文件名"] + columns:
                self.catalog_tree.heading(col, text=col)
                self.catalog_tree.column(col, width=100 if col not in ["文件名", "文件夹"] else 150)
                
            folder_groups = {}
            for img_path in self.images:
                folder = os.path.dirname(img_path)
                if folder not in folder_groups:
                    folder_groups[folder] = []
                folder_groups[folder].append(img_path)
            
            self.log(f"共发现 {len(folder_groups)} 个文件夹")
            
            first_n = 0
            if self.radio_var.get() == "first":
                try:
                    first_n = int(self.first_n_entry.get())
                except:
                    first_n = 3
            
            archive_mode = self.archive_mode_var.get()
            self.log(f"档案模式: {'每文件夹为一件' if archive_mode == 'folder' else '每图片为一件'}")
            
            if archive_mode == "folder":
                self.catalog_by_folder(folder_groups, df_template, columns, first_n)
            else:
                self.catalog_by_image(folder_groups, df_template, columns, first_n)
            
        except Exception as e:
            self.log(f"著录失败: {e}")
            messagebox.showerror("错误", f"著录失败: {e}")
            self.auto_save(force=True)
            
            self.pause_btn.configure(state="disabled")
            self.stop_btn.configure(state="disabled")
            self.resume_btn.configure(state="disabled")
    
    def catalog_by_folder(self, folder_groups, df_template, columns, first_n):
        total_folders = len(folder_groups)
        processed_count = 0
        
        for folder, imgs in folder_groups.items():
            if self.is_stopped:
                self.log("著录已停止")
                break
                
            while self.is_paused:
                self.progress_label.configure(text="已暂停...")
                self.update_idletasks()
                time.sleep(0.5)
            
            if first_n > 0:
                imgs_to_process = imgs[:first_n]
            else:
                imgs_to_process = imgs
            
            processed_count += 1
            self.progress_bar.set(processed_count / total_folders)
            self.progress_label.configure(text=f"著录文件夹 {processed_count}/{total_folders}")
            
            folder_name = os.path.basename(folder)
            self.log(f"处理文件夹 {folder_name}: {len(imgs_to_process)} 张")
            
            result = self.catalog_folder_as_one(folder, imgs_to_process, df_template)
            self.catalog_results.append(result)
            
            first_img_name = os.path.basename(imgs_to_process[0]) if imgs_to_process else ""
            row_values = [folder_name, first_img_name] + [result.get(col, "") for col in columns]
            self.catalog_tree.insert("", 0, values=row_values)
            
            if processed_count % self.auto_save_interval == 0 or processed_count == total_folders:
                self.auto_save()
            
            if processed_count % 5 == 0:
                self.update_idletasks()
        
        if not self.is_stopped:
            self.progress_label.configure(text="著录完成")
            self.log(f"著录完成，共处理 {total_folders} 个文件夹")
        else:
            self.progress_label.configure(text="著录已停止")
            self.auto_save(force=True)
            
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.update_stats()
    
    def catalog_by_image(self, folder_groups, df_template, columns, first_n):
        total_images = 0
        for folder, imgs in folder_groups.items():
            if first_n > 0:
                total_images += len(imgs[:first_n])
            else:
                total_images += len(imgs)
        
        processed_count = 0
        
        for folder, imgs in folder_groups.items():
            if self.is_stopped:
                self.log("著录已停止")
                break
                
            if first_n > 0:
                imgs_to_process = imgs[:first_n]
            else:
                imgs_to_process = imgs
            
            folder_name = os.path.basename(folder)
            self.log(f"处理文件夹 {folder_name}: {len(imgs_to_process)} 张")
            
            for img_path in imgs_to_process:
                if self.is_stopped:
                    self.log("著录已停止")
                    break
                    
                while self.is_paused:
                    self.progress_label.configure(text="已暂停...")
                    self.update_idletasks()
                    time.sleep(0.5)
                
                processed_count += 1
                self.progress_bar.set(processed_count / total_images)
                self.progress_label.configure(text=f"著录: {processed_count}/{total_images}")
                
                result = self.catalog_single_image(img_path, df_template, folder)
                self.catalog_results.append(result)
                
                row_values = [folder_name, os.path.basename(img_path)] + [result.get(col, "") for col in columns]
                self.catalog_tree.insert("", 0, values=row_values)
                
                if processed_count % self.auto_save_interval == 0 or processed_count == total_images:
                    self.auto_save()
                
                if processed_count % 5 == 0:
                    self.update_idletasks()
            
            if self.is_stopped:
                break
        
        if not self.is_stopped:
            self.progress_label.configure(text="著录完成")
            self.log(f"著录完成，共处理 {processed_count} 张图片")
        else:
            self.progress_label.configure(text="著录已停止")
            self.auto_save(force=True)
            
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.update_stats()
    
    def catalog_folder_as_one(self, folder, img_paths, template_df):
        folder_name = os.path.basename(folder)
        
        images_base64 = []
        for img_path in img_paths:
            with open(img_path, "rb") as f:
                import base64
                images_base64.append(base64.b64encode(f.read()).decode("utf-8"))
        
        columns = template_df.columns.tolist()
        
        field_descriptions = []
        for col in columns:
            if col in self.field_prompts and self.field_prompts[col]:
                field_descriptions.append(f"- {col}: {self.field_prompts[col]}")
            else:
                field_descriptions.append(f"- {col}: 请从图片中识别该字段内容")
        
        prompt = f"""你是专业档案著录专家，请分析以下档案图片并完成著录。

📁 档案文件夹: {folder_name}
🖼️ 图片数量: {len(img_paths)}张

📋 著录字段及识别要求:
{chr(10).join(field_descriptions)}

💡 识别规则:
1. 标题：通常位于页面顶部居中或居左，字体较大
2. 文号：形如"XX〔YYYY〕XX号"的文件编号
3. 日期：文件签发日期
4. 作者：文件起草单位或个人
5. 页数：文件总页数
6. 密级：秘密/机密/绝密/公开

请输出JSON格式，键为字段名，值为识别结果。如无法识别请填"无法确定"。
"""
        
        result = {"文件夹": folder_name, "文件名": f"{len(img_paths)}张图片"}
        
        try:
            current_model = self.model_combo.get()
            if not current_model or current_model == "请先连接Ollama":
                self.log(f"著录文件夹 {folder_name}: 未选择模型")
                result["状态"] = "未选择模型"
                return result
            
            if current_model == "模拟模型 (测试用)":
                import time
                time.sleep(0.5)
                
                mock_data = {}
                for col in columns:
                    if "标题" in col or "名称" in col:
                        mock_data[col] = f"档案标题_{folder_name}"
                    elif "日期" in col:
                        mock_data[col] = datetime.now().strftime("%Y年%m月%d日")
                    elif "页数" in col:
                        mock_data[col] = str(len(img_paths))
                    elif "作者" in col:
                        mock_data[col] = "未知作者"
                    elif "文号" in col:
                        mock_data[col] = f"文件编号{hash(folder_name) % 10000}"
                    else:
                        mock_data[col] = f"识别内容_{col}"
                
                self.log(f"著录文件夹 {folder_name}: 模拟模式完成")
                result.update(mock_data)
                return result
            
            response = ollama.generate(
                model=current_model,
                prompt=prompt,
                images=images_base64
            )
            
            ai_response = response.get("response", "")
            
            import re
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if json_match:
                try:
                    catalog_data = json.loads(json_match.group())
                    result.update(catalog_data)
                    self.log(f"著录文件夹 {folder_name}: 成功")
                except json.JSONDecodeError:
                    self.log(f"著录文件夹 {folder_name}: JSON解析失败")
                    result["状态"] = "部分完成"
            else:
                self.log(f"著录文件夹 {folder_name}: 未获取到响应")
                result["状态"] = "需人工审核"
                
        except Exception as e:
            self.log(f"著录文件夹 {folder_name} 失败: {e}")
            result["状态"] = f"错误: {e}"
            
        return result
    
    def pause_catalog(self):
        self.is_paused = True
        self.pause_btn.configure(state="disabled")
        self.resume_btn.configure(state="normal")
        self.log("已暂停处理")
    
    def resume_catalog(self):
        self.is_paused = False
        self.pause_btn.configure(state="normal")
        self.resume_btn.configure(state="disabled")
        self.log("已恢复处理")
    
    def stop_catalog(self):
        self.is_stopped = True
        self.is_paused = False
        self.pause_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.log("正在停止...")
        self.auto_save(force=True)
            
    def catalog_single_image(self, img_path, template_df, folder):
        filename = os.path.basename(img_path)
        
        with open(img_path, "rb") as f:
            import base64
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
            
        columns = template_df.columns.tolist()
        
        field_descriptions = []
        for col in columns:
            if col in self.field_prompts and self.field_prompts[col]:
                field_descriptions.append(f"- {col}: {self.field_prompts[col]}")
            else:
                field_descriptions.append(f"- {col}: 请从图片中识别该字段内容")
        
        prompt = f"""你是专业档案著录专家，请分析图片内容并完成著录。

📄 图片文件名: {filename}
📁 所在文件夹: {os.path.basename(folder)}

📋 著录字段及识别要求:
{chr(10).join(field_descriptions)}

💡 识别规则:
1. 标题：通常位于页面顶部，字体较大
2. 文号：形如"XX〔YYYY〕XX号"的文件编号
3. 日期：文件签发日期
4. 作者：文件起草单位或个人
5. 页数：文件页码或总页数
6. 密级：秘密/机密/绝密/公开

请输出JSON格式，键为字段名，值为识别结果。如无法识别请填"无法确定"。
"""
        
        result = {"文件名": filename, "文件夹": os.path.basename(folder)}
        
        try:
            current_model = self.model_combo.get()
            if not current_model or current_model == "请先连接Ollama":
                self.log(f"著录 {filename}: 未选择模型")
                result["状态"] = "未选择模型"
                return result
            
            if current_model == "模拟模型 (测试用)":
                import time
                time.sleep(0.3)
                
                mock_data = {}
                for col in columns:
                    if "标题" in col or "名称" in col:
                        mock_data[col] = f"文档标题_{filename}"
                    elif "日期" in col:
                        mock_data[col] = datetime.now().strftime("%Y年%m月%d日")
                    elif "页数" in col:
                        mock_data[col] = "1"
                    elif "作者" in col:
                        mock_data[col] = "未知作者"
                    elif "文号" in col:
                        mock_data[col] = f"文件编号{hash(filename) % 10000}"
                    else:
                        mock_data[col] = f"识别内容_{col}"
                
                self.log(f"著录 {filename}: 模拟模式完成")
                result.update(mock_data)
                return result
            
            response = ollama.generate(
                model=current_model,
                prompt=prompt,
                images=[img_base64]
            )
            
            ai_response = response.get("response", "")
            
            import re
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if json_match:
                try:
                    catalog_data = json.loads(json_match.group())
                    result.update(catalog_data)
                    self.log(f"著录 {filename}: 成功")
                except json.JSONDecodeError:
                    self.log(f"著录 {filename}: JSON解析失败")
                    result["状态"] = "部分完成"
            else:
                self.log(f"著录 {filename}: 未获取到响应")
                result["状态"] = "需人工审核"
                
        except Exception as e:
            self.log(f"著录 {filename} 失败: {e}")
            result["状态"] = f"错误: {e}"
            
        return result
        
    def export_report(self):
        if not self.quality_results and not self.catalog_results:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
            
        save_path = filedialog.asksaveasfilename(
            title="另存为报告",
            defaultextension=".xlsx",
            initialfile=f"著录报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        
        if save_path:
            try:
                with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                    if self.quality_results:
                        df_qc = pd.DataFrame(self.quality_results)
                        df_qc.to_excel(writer, sheet_name="质检结果", index=False)
                        
                    if self.catalog_results:
                        df_catalog = pd.DataFrame(self.catalog_results)
                        df_catalog.to_excel(writer, sheet_name="著录结果", index=False)
                        
                self.log(f"报告已导出: {save_path}")
                messagebox.showinfo("成功", f"报告已导出:\n{save_path}")
                
            except Exception as e:
                self.log(f"导出失败: {e}")
                messagebox.showerror("错误", f"导出失败: {e}")

if __name__ == "__main__":
    app = ArchiveQCSystem()
    app.mainloop()
