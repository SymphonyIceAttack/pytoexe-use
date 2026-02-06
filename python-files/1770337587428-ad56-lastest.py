import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import math
import json

class SnowflakeCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("冰与火之舞雪花计算器 - 综合版")
        
        # 设置 Windows 11 风格背景色
        self.windows_bg = '#F0F0F0'
        self.root.configure(bg=self.windows_bg)
        
        # 设置窗口大小和位置
        window_width = 900
        window_height = 750
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(850, 650)
        
        # 创建 Windows 11 风格样式
        self.create_win11_styles()
        
        # 创建主界面
        self.create_main_frame()
        
        # 创建选项卡
        self.create_tabs()
        
        # 加载初始数据
        self.load_initial_data()
    
    def create_win11_styles(self):
        """创建 Windows 11 风格样式"""
        style = ttk.Style()
        
        # 使用系统默认主题
        try:
            style.theme_use('vista')
        except:
            try:
                style.theme_use('winnative')
            except:
                style.theme_use('clam')
        
        # 配置 Windows 11 风格按钮样式
        style.configure('Win11.TButton',
                       font=('微软雅黑', 9),
                       padding=5,
                       relief='flat',
                       borderwidth=1,
                       background=self.windows_bg,
                       foreground='black',
                       bordercolor='#E1DFDD')
        
        style.map('Win11.TButton',
                 background=[('active', '#F3F2F1'), ('disabled', '#F8F8F8')],
                 relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Windows 11 风格标签样式
        style.configure('Win11.TLabel',
                       font=('微软雅黑', 9),
                       background=self.windows_bg,
                       foreground='black')
        
        style.configure('Win11.Title.TLabel',
                       font=('微软雅黑', 16, 'bold'),
                       background=self.windows_bg,
                       foreground='black')
        
        style.configure('Win11.Header.TLabel',
                       font=('微软雅黑', 11, 'bold'),
                       background=self.windows_bg,
                       foreground='black')
        
        # Windows 11 风格框架样式
        style.configure('Win11.TFrame',
                       background=self.windows_bg)
        
        style.configure('Win11.TLabelframe',
                       background=self.windows_bg,
                       relief='solid',
                       borderwidth=1,
                       bordercolor='#E1DFDD')
        
        style.configure('Win11.TLabelframe.Label',
                       background=self.windows_bg,
                       foreground='black',
                       font=('微软雅黑', 10, 'bold'))
        
        # 选项卡样式
        style.configure('Win11.TNotebook',
                       background=self.windows_bg)
        
        style.configure('Win11.TNotebook.Tab',
                       font=('微软雅黑', 9),
                       background=self.windows_bg,
                       padding=(6, 2))
        
        style.map('Win11.TNotebook.Tab',
                 background=[('selected', self.windows_bg)])
    
    def create_main_frame(self):
        """创建主框架"""
        self.main_frame = ttk.Frame(self.root, style='Win11.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题栏
        self.create_title_bar()
    
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = ttk.Frame(self.main_frame, style='Win11.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 主标题
        title_label = tk.Label(title_frame, 
                              text="❄️ 冰与火之舞雪花计算器 - 综合版 ❄️",
                              font=('微软雅黑', 16, 'bold'),
                              bg=self.windows_bg,
                              fg='black')
        title_label.pack(anchor=tk.W)
        
        # 制作信息
        subtitle_label = tk.Label(title_frame,
                                 text="程序由 iDQhonefully 制作",
                                 font=('微软雅黑', 9),
                                 bg=self.windows_bg,
                                 fg='#605E5C')
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 分隔线
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 5))
    
    def create_tabs(self):
        """创建选项卡"""
        self.notebook = ttk.Notebook(self.main_frame, style='Win11.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 创建三个标签页
        self.tab1 = ttk.Frame(self.notebook, style='Win11.TFrame')
        self.tab2 = ttk.Frame(self.notebook, style='Win11.TFrame')
        self.tab3 = ttk.Frame(self.notebook, style='Win11.TFrame')
        
        self.notebook.add(self.tab1, text="雪花生成器")
        self.notebook.add(self.tab2, text="角度加减器")
        self.notebook.add(self.tab3, text="角度-BPM转换器")
        
        # 创建各个标签页界面
        self.create_snowflake_tab()
        self.create_angle_calculator_tab()
        self.create_angle_bpm_converter_tab()
        
        # 创建状态栏
        self.create_status_bar()
    
    def create_snowflake_tab(self):
        """创建雪花生成器标签页"""
        container = ttk.Frame(self.tab1, style='Win11.TFrame')
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        input_frame = ttk.LabelFrame(container, text="第一步：输入第一瓣雪花的角度数据", 
                                    style='Win11.TLabelframe')
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(input_frame, text="请输入角度数据（用逗号分隔）：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        
        self.angle_entry = tk.Text(input_frame, height=3, font=('Consolas', 9),
                                  bg='white', fg='black',
                                  insertbackground='black',
                                  selectbackground='#E1DFDD')
        self.angle_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        config_frame = ttk.LabelFrame(container, text="第二步：配置雪花参数", 
                                     style='Win11.TLabelframe')
        config_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        petals_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        petals_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(petals_frame, text="雪花瓣数：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.petal_var = tk.StringVar(value="8")
        petal_combo = ttk.Combobox(petals_frame, textvariable=self.petal_var, 
                                   values=["4", "6", "8", "12", "16", "24", "32", "自定义"], 
                                   width=8, state="readonly")
        petal_combo.pack(side=tk.LEFT, padx=(0, 15))
        petal_combo.bind("<<ComboboxSelected>>", self.on_petal_change)
        
        tk.Label(petals_frame, text="或自定义瓣数：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.custom_petal_var = tk.StringVar()
        self.custom_petal_entry = ttk.Entry(petals_frame, textvariable=self.custom_petal_var, width=8)
        self.custom_petal_entry.pack(side=tk.LEFT)
        self.custom_petal_entry.configure(state='disabled')
        
        rotation_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        rotation_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        tk.Label(rotation_frame, text="旋转方向：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.rotation_var = tk.StringVar(value="negative")
        ttk.Radiobutton(rotation_frame, text="负角度（顺时针）", 
                       variable=self.rotation_var, value="negative").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(rotation_frame, text="正角度（逆时针）",
                       variable=self.rotation_var, value="positive",).pack(side=tk.LEFT)
        
        output_frame = ttk.LabelFrame(container, text="第三步：生成结果", 
                                     style='Win11.TLabelframe')
        output_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        button_frame = ttk.Frame(output_frame, style='Win11.TFrame')
        button_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.generate_btn = ttk.Button(button_frame, text="生成雪花数据", 
                                      style='Win11.TButton',
                                      command=self.generate_snowflake)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空", 
                                   style='Win11.TButton',
                                   command=self.clear_snowflake)
        self.clear_btn.pack(side=tk.LEFT)
        
        result_frame = ttk.Frame(output_frame, style='Win11.TFrame')
        result_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(result_frame, text="生成的角度数据：", 
                font=('微软雅黑', 10, 'bold'),
                bg=self.windows_bg,
                fg='black').grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=10,
            font=('Consolas', 9), 
            wrap=tk.WORD,
            bg='white',
            fg='black',
            insertbackground='black',
            selectbackground='#E1DFDD'
        )
        self.result_text.grid(row=1, column=0, sticky="nsew")
        
        action_frame = ttk.Frame(output_frame, style='Win11.TFrame')
        action_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.copy_btn = ttk.Button(action_frame, text="复制到剪贴板", 
                                  style='Win11.TButton',
                                  command=self.copy_to_clipboard, 
                                  state='disabled')
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(action_frame, text="保存到文件", 
                                  style='Win11.TButton',
                                  command=self.save_to_file, 
                                  state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.transfer_btn = ttk.Button(action_frame, text="传输到角度加减器", 
                                      style='Win11.TButton',
                                      command=self.transfer_to_calculator, 
                                      state='disabled')
        self.transfer_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.transfer_to_converter_btn = ttk.Button(action_frame, text="传输到角度-BPM转换器", 
                                                  style='Win11.TButton',
                                                  command=self.transfer_to_converter, 
                                                  state='disabled')
        self.transfer_to_converter_btn.pack(side=tk.LEFT)
    
    def create_angle_calculator_tab(self):
        """创建角度加减器标签页"""
        container = ttk.Frame(self.tab2, style='Win11.TFrame')
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        input_frame = ttk.LabelFrame(container, text="输入角度数据", 
                                    style='Win11.TLabelframe')
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(input_frame, text="请输入角度数据（用逗号分隔）：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        
        self.calc_angle_entry = tk.Text(input_frame, height=3, font=('Consolas', 9),
                                       bg='white', fg='black',
                                       insertbackground='black',
                                       selectbackground='#E1DFDD')
        self.calc_angle_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        calc_button_frame = ttk.Frame(input_frame, style='Win11.TFrame')
        calc_button_frame.grid(row=2, column=0, sticky="w", pady=(0, 5), padx=5)
        
        ttk.Button(calc_button_frame, text="从雪花生成器导入", 
                  style='Win11.TButton',
                  command=self.import_from_snowflake).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_button_frame, text="从角度-BPM转换器导入", 
                  style='Win11.TButton',
                  command=self.import_from_converter).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_button_frame, text="清空", 
                  style='Win11.TButton',
                  command=self.clear_calculator).pack(side=tk.LEFT)
        
        calc_frame = ttk.LabelFrame(container, text="角度加减配置", 
                                   style='Win11.TLabelframe')
        calc_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        add_frame = ttk.Frame(calc_frame, style='Win11.TFrame')
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(add_frame, text="要加上的角度：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_angle_var = tk.StringVar(value="45")
        add_angle_entry = ttk.Entry(add_frame, textvariable=self.add_angle_var, width=8)
        add_angle_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Label(add_frame, text="度",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 10))
        
        self.normalize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(add_frame, text="将结果归一化到0-360度", 
                       variable=self.normalize_var).pack(side=tk.LEFT)
        
        calc_btn_frame = ttk.Frame(calc_frame, style='Win11.TFrame')
        calc_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.calc_btn = ttk.Button(calc_btn_frame, text="计算", 
                                  style='Win11.TButton',
                                  command=self.calculate_angles)
        self.calc_btn.pack(side=tk.LEFT)
        
        result_frame = ttk.LabelFrame(container, text="计算结果", 
                                     style='Win11.TLabelframe')
        result_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        self.calc_stats_label = tk.Label(result_frame, text="就绪", 
                                        font=('微软雅黑', 9),
                                        bg=self.windows_bg,
                                        fg='black')
        self.calc_stats_label.grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        
        self.calc_result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=8,
            font=('Consolas', 9), 
            wrap=tk.WORD,
            bg='white',
            fg='black',
            insertbackground='black',
            selectbackground='#E1DFDD'
        )
        self.calc_result_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        calc_action_frame = ttk.Frame(result_frame, style='Win11.TFrame')
        calc_action_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.calc_copy_btn = ttk.Button(calc_action_frame, text="复制到剪贴板", 
                                       style='Win11.TButton',
                                       command=self.copy_calc_to_clipboard, 
                                       state='disabled')
        self.calc_copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.calc_save_btn = ttk.Button(calc_action_frame, text="保存到文件", 
                                       style='Win11.TButton',
                                       command=self.save_calc_to_file, 
                                       state='disabled')
        self.calc_save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_action_frame, text="传输到雪花生成器", 
                  style='Win11.TButton',
                  command=self.transfer_to_snowflake).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_action_frame, text="传输到角度-BPM转换器", 
                  style='Win11.TButton',
                  command=self.transfer_calc_to_converter).pack(side=tk.LEFT)
    
    def create_angle_bpm_converter_tab(self):
        """创建角度-BPM转换器标签页"""
        container = ttk.Frame(self.tab3, style='Win11.TFrame')
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        input_frame = ttk.LabelFrame(container, text="第一步：输入角度数据", 
                                    style='Win11.TLabelframe')
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(input_frame, text="请输入角度数据（用逗号分隔）：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        
        self.converter_angle_entry = tk.Text(input_frame, height=3, font=('Consolas', 9),
                                           bg='white', fg='black',
                                           insertbackground='black',
                                           selectbackground='#E1DFDD')
        self.converter_angle_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        converter_button_frame = ttk.Frame(input_frame, style='Win11.TFrame')
        converter_button_frame.grid(row=2, column=0, sticky="w", pady=(0, 5), padx=5)
        
        ttk.Button(converter_button_frame, text="从雪花生成器导入", 
                  style='Win11.TButton',
                  command=self.import_to_converter_from_snowflake).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(converter_button_frame, text="从角度加减器导入", 
                  style='Win11.TButton',
                  command=self.import_to_converter_from_calculator).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(converter_button_frame, text="清空", 
                  style='Win11.TButton',
                  command=self.clear_converter).pack(side=tk.LEFT)
        
        config_frame = ttk.LabelFrame(container, text="第二步：配置BPM和内外圈", 
                                     style='Win11.TLabelframe')
        config_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # 第一行：BPM设置
        bpm_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        bpm_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(bpm_frame, text="BPM（每分钟节拍数）：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.bpm_var = tk.StringVar(value="100")
        bpm_entry = ttk.Entry(bpm_frame, textvariable=self.bpm_var, width=10)
        bpm_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        # 第二行：起始floor设置
        start_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        start_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(start_frame, text="起始floor值（默认1）：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_floor_var = tk.StringVar(value="1")
        start_floor_entry = ttk.Entry(start_frame, textvariable=self.start_floor_var, width=10)
        start_floor_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        # 第三行：内外圈选择
        circle_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        circle_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        tk.Label(circle_frame, text="轨道类型：",
                font=('微软雅黑', 9),
                bg=self.windows_bg,
                fg='black').pack(side=tk.LEFT, padx=(0, 5))
        
        self.circle_var = tk.StringVar(value="0")
        ttk.Radiobutton(circle_frame, text="内圈（0）", 
                       variable=self.circle_var, value="0").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(circle_frame, text="外圈（1）", 
                       variable=self.circle_var, value="1").pack(side=tk.LEFT)
        
        convert_btn_frame = ttk.Frame(config_frame, style='Win11.TFrame')
        convert_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        self.convert_btn = ttk.Button(convert_btn_frame, text="转换为BPM事件数据", 
                                     style='Win11.TButton',
                                     command=self.convert_to_bpm_events)
        self.convert_btn.pack(side=tk.LEFT)
        
        output_frame = ttk.LabelFrame(container, text="第三步：生成BPM事件数据", 
                                     style='Win11.TLabelframe')
        output_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        output_frame.grid_rowconfigure(1, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.converter_stats_label = tk.Label(output_frame, text="就绪", 
                                             font=('微软雅黑', 9),
                                             bg=self.windows_bg,
                                             fg='black')
        self.converter_stats_label.grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        
        self.converter_result_text = scrolledtext.ScrolledText(
            output_frame, 
            height=10,
            font=('Consolas', 9), 
            wrap=tk.WORD,
            bg='white',
            fg='black',
            insertbackground='black',
            selectbackground='#E1DFDD'
        )
        self.converter_result_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        converter_action_frame = ttk.Frame(output_frame, style='Win11.TFrame')
        converter_action_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.converter_copy_btn = ttk.Button(converter_action_frame, text="复制到剪贴板", 
                                           style='Win11.TButton',
                                           command=self.copy_converter_to_clipboard, 
                                           state='disabled')
        self.converter_copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(converter_action_frame, text="传输到雪花生成器", 
                  style='Win11.TButton',
                  command=self.transfer_converter_to_snowflake).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(converter_action_frame, text="传输到角度加减器", 
                  style='Win11.TButton',
                  command=self.transfer_converter_to_calculator).pack(side=tk.LEFT)
    
    def create_status_bar(self):
        """创建 Windows 11 风格状态栏"""
        status_frame = ttk.Frame(self.main_frame, style='Win11.TFrame', borderwidth=1, relief=tk.SOLID)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.status_bar = tk.Label(status_frame, text="就绪", 
                                  font=('微软雅黑', 8),
                                  anchor=tk.W,
                                  bg=self.windows_bg,
                                  fg='black')
        self.status_bar.pack(side=tk.LEFT, padx=5)
        
        tk.Label(status_frame, bg=self.windows_bg).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        tk.Label(status_frame, text="作者: iDQhonefully", 
                font=('微软雅黑', 8),
                bg=self.windows_bg,
                fg='#605E5C').pack(side=tk.RIGHT, padx=5)
    
    def load_initial_data(self):
        """加载初始数据"""
        self.angle_entry.delete(1.0, tk.END)
        self.angle_entry.insert(1.0, "")
        
        self.calc_angle_entry.delete(1.0, tk.END)
        self.calc_angle_entry.insert(1.0, "")
        
        self.converter_angle_entry.delete(1.0, tk.END)
        self.converter_angle_entry.insert(1.0, "")
    
    def on_petal_change(self, event):
        """瓣数选择变化事件"""
        if self.petal_var.get() == "自定义":
            self.custom_petal_entry.configure(state='normal')
        else:
            self.custom_petal_entry.configure(state='disabled')
    
    def clear_snowflake(self):
        """清空雪花生成器内容"""
        self.angle_entry.delete(1.0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.copy_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled')
        self.transfer_btn.configure(state='disabled')
        self.transfer_to_converter_btn.configure(state='disabled')
        self.status_bar.config(text="雪花生成器已清空")
    
    def clear_calculator(self):
        """清空角度加减器内容"""
        self.calc_angle_entry.delete(1.0, tk.END)
        self.calc_result_text.delete(1.0, tk.END)
        self.calc_copy_btn.configure(state='disabled')
        self.calc_save_btn.configure(state='disabled')
        self.status_bar.config(text="角度加减器已清空")
    
    def clear_converter(self):
        """清空角度-BPM转换器内容"""
        self.converter_angle_entry.delete(1.0, tk.END)
        self.converter_result_text.delete(1.0, tk.END)
        self.converter_copy_btn.configure(state='disabled')
        self.status_bar.config(text="角度-BPM转换器已清空")
    
    def import_from_snowflake(self):
        """从雪花生成器导入数据到角度加减器"""
        data = self.angle_entry.get(1.0, tk.END).strip()
        if data:
            self.calc_angle_entry.delete(1.0, tk.END)
            self.calc_angle_entry.insert(1.0, data)
            self.status_bar.config(text="已从雪花生成器导入数据到角度加减器")
            self.notebook.select(self.tab2)
        else:
            messagebox.showwarning("导入失败", "雪花生成器中没有数据")
    
    def import_from_converter(self):
        """从角度-BPM转换器导入数据到角度加减器"""
        data = self.converter_angle_entry.get(1.0, tk.END).strip()
        if data:
            self.calc_angle_entry.delete(1.0, tk.END)
            self.calc_angle_entry.insert(1.0, data)
            self.status_bar.config(text="已从角度-BPM转换器导入数据到角度加减器")
            self.notebook.select(self.tab2)
        else:
            messagebox.showwarning("导入失败", "角度-BPM转换器中没有数据")
    
    def import_to_converter_from_snowflake(self):
        """从雪花生成器导入数据到角度-BPM转换器"""
        data = self.angle_entry.get(1.0, tk.END).strip()
        if data:
            self.converter_angle_entry.delete(1.0, tk.END)
            self.converter_angle_entry.insert(1.0, data)
            self.status_bar.config(text="已从雪花生成器导入数据到角度-BPM转换器")
            self.notebook.select(self.tab3)
        else:
            messagebox.showwarning("导入失败", "雪花生成器中没有数据")
    
    def import_to_converter_from_calculator(self):
        """从角度加减器导入数据到角度-BPM转换器"""
        data = self.calc_angle_entry.get(1.0, tk.END).strip()
        if data:
            self.converter_angle_entry.delete(1.0, tk.END)
            self.converter_angle_entry.insert(1.0, data)
            self.status_bar.config(text="已从角度加减器导入数据到角度-BPM转换器")
            self.notebook.select(self.tab3)
        else:
            messagebox.showwarning("导入失败", "角度加减器中没有数据")
    
    def format_angle(self, angle):
        """格式化角度，整数不显示小数部分，小数保留原始形式"""
        epsilon = 1e-10
        angle = float(angle)
        angle_rounded = round(angle, 10)
        
        if abs(angle_rounded - round(angle_rounded)) < epsilon:
            return str(int(round(angle_rounded)))
        else:
            result = str(angle_rounded).rstrip('0').rstrip('.')
            if not result:
                return str(int(angle_rounded))
            return result
    
    def generate_snowflake(self):
        """生成雪花数据"""
        angles_input = self.angle_entry.get(1.0, tk.END).strip()
        if not angles_input:
            messagebox.showwarning("输入错误", "请输入角度数据")
            return
        
        try:
            base_angles = []
            for angle_str in angles_input.split(','):
                angle_str = angle_str.strip()
                if angle_str:
                    base_angles.append(float(angle_str))
            
            if not base_angles:
                messagebox.showwarning("输入错误", "未找到有效的角度数据")
                return
                
        except ValueError:
            messagebox.showerror("输入错误", "角度数据格式不正确，请确保输入的是数字")
            return
        
        try:
            if self.petal_var.get() == "自定义":
                if not self.custom_petal_var.get():
                    messagebox.showwarning("输入错误", "请输入自定义瓣数")
                    return
                petals = int(self.custom_petal_var.get())
            else:
                petals = int(self.petal_var.get())
            
            if petals <= 0:
                messagebox.showwarning("输入错误", "瓣数必须为正整数")
                return
                
        except ValueError:
            messagebox.showerror("输入错误", "瓣数必须为整数")
            return
        
        rotation_angle = 360 / petals
        
        if self.rotation_var.get() == "negative":
            rotation_angle = -rotation_angle
        
        all_angles = []
        
        for i in range(petals):
            rotation = i * rotation_angle
            
            for angle in base_angles:
                new_angle = (angle + rotation) % 360
                all_angles.append(new_angle)
        
        self.result_text.delete(1.0, tk.END)
        
        stats = f"雪花生成完成！\n"
        stats += f"原始角度数: {len(base_angles)}\n"
        stats += f"雪花瓣数: {petals}\n"
        stats += f"旋转角度: {self.format_angle(rotation_angle)}°\n"
        stats += f"总角度数: {len(all_angles)}\n"
        stats += "-" * 40 + "\n\n"
        
        self.result_text.insert(1.0, stats)
        
        formatted_angles = [self.format_angle(angle) for angle in all_angles]
        angles_str = ", ".join(formatted_angles)
        self.result_text.insert(tk.END, angles_str)
        
        self.copy_btn.configure(state='normal')
        self.save_btn.configure(state='normal')
        self.transfer_btn.configure(state='normal')
        self.transfer_to_converter_btn.configure(state='normal')
        
        self.status_bar.config(text=f"生成完成！总角度数: {len(all_angles)}")
    
    def calculate_angles(self):
        """计算角度加减"""
        angles_input = self.calc_angle_entry.get(1.0, tk.END).strip()
        if not angles_input:
            messagebox.showwarning("输入错误", "请输入角度数据")
            return
        
        try:
            add_angle = float(self.add_angle_var.get())
        except ValueError:
            messagebox.showerror("输入错误", "加减角度必须是数字")
            return
        
        try:
            base_angles = []
            for angle_str in angles_input.split(','):
                angle_str = angle_str.strip()
                if angle_str:
                    base_angles.append(float(angle_str))
            
            if not base_angles:
                messagebox.showwarning("输入错误", "未找到有效的角度数据")
                return
                
        except ValueError:
            messagebox.showerror("输入错误", "角度数据格式不正确，请确保输入的是数字")
            return
        
        result_angles = []
        for angle in base_angles:
            new_angle = angle + add_angle
            if self.normalize_var.get():
                new_angle = new_angle % 360
            result_angles.append(new_angle)
        
        self.calc_result_text.delete(1.0, tk.END)
        
        stats = f"角度计算完成！\n"
        stats += f"原始角度数: {len(base_angles)}\n"
        stats += f"加减角度: {self.format_angle(add_angle)}°\n"
        stats += f"归一化: {'是' if self.normalize_var.get() else '否'}\n"
        stats += "-" * 40 + "\n\n"
        
        self.calc_result_text.insert(1.0, stats)
        
        self.calc_result_text.insert(tk.END, "原始角度 -> 计算结果\n")
        self.calc_result_text.insert(tk.END, "-" * 30 + "\n")
        
        for i, (orig, result) in enumerate(zip(base_angles, result_angles)):
            self.calc_result_text.insert(tk.END, f"{self.format_angle(orig)}° -> {self.format_angle(result)}°\n")
        
        self.calc_result_text.insert(tk.END, "\n" + "-" * 40 + "\n\n")
        
        formatted_results = [self.format_angle(angle) for angle in result_angles]
        angles_str = ", ".join(formatted_results)
        self.calc_result_text.insert(tk.END, "计算结果：\n")
        self.calc_result_text.insert(tk.END, angles_str)
        
        self.calc_stats_label.config(text=f"计算完成！共 {len(result_angles)} 个角度")
        
        self.calc_copy_btn.configure(state='normal')
        self.calc_save_btn.configure(state='normal')
        
        self.status_bar.config(text=f"角度计算完成！共 {len(result_angles)} 个角度")
    
    def parse_angle_string(self, angle_str):
        """解析角度字符串，处理C++代码中的特殊逻辑"""
        numbers = []
        current_num = 0
        num_started = False
        
        for ch in angle_str:
            if ch.isdigit():
                current_num = current_num * 10 + int(ch)
                num_started = True
            elif ch == ',':
                if num_started:
                    numbers.append(current_num)
                    current_num = 0
                    num_started = False
            elif ch == '-':
                if num_started:
                    numbers.append(current_num)
                    current_num = 0
                    num_started = False
        
        if num_started:
            numbers.append(current_num)
        
        return numbers
    
    def convert_angles_logic(self, angles):
        """角度转换的核心逻辑（来自C++代码）"""
        w = len(angles)
        transformed_angles = angles.copy()
        u = 0
        
        for z in range(w):
            v = angles[z]
            
            if transformed_angles[z] == u:
                transformed_angles[z] = 180
            else:
                if transformed_angles[z] > u:
                    if u == 0:
                        if transformed_angles[z] < 180:
                            transformed_angles[z] = 180 - transformed_angles[z]
                        else:
                            transformed_angles[z] = 360 - (transformed_angles[z] - 180)
                    else:
                        if u == 180:
                            transformed_angles[z] = 360 - transformed_angles[z]
                        else:
                            if u < 180:
                                if (transformed_angles[z] - 180) > u:
                                    transformed_angles[z] = u + 180 + (360 - transformed_angles[z])
                                else:
                                    transformed_angles[z] = (360 - transformed_angles[z]) - (180 - u)
                            else:
                                transformed_angles[z] = 360 - transformed_angles[z] + (u - 180)
                else:
                    if u == 180:
                        transformed_angles[z] = 180 + (180 - transformed_angles[z])
                    else:
                        if u < 180:
                            transformed_angles[z] = 180 + (u - transformed_angles[z])
                        else:
                            if (u - 180) > transformed_angles[z]:
                                transformed_angles[z] = u - 180 - transformed_angles[z]
                            else:
                                transformed_angles[z] = 360 - transformed_angles[z] + (u - 180)
            
            u = v
        
        return transformed_angles
    
    def convert_to_bpm_events(self):
        """转换为BPM事件数据"""
        angles_input = self.converter_angle_entry.get(1.0, tk.END).strip()
        if not angles_input:
            messagebox.showwarning("输入错误", "请输入角度数据")
            return
        
        try:
            bpm = float(self.bpm_var.get())
            if bpm <= 0:
                messagebox.showwarning("输入错误", "BPM必须为正数")
                return
        except ValueError:
            messagebox.showerror("输入错误", "BPM必须是数字")
            return
        
        try:
            circle = int(self.circle_var.get())
            if circle not in [0, 1]:
                messagebox.showwarning("输入错误", "内外圈必须为0或1")
                return
        except ValueError:
            messagebox.showerror("输入错误", "内外圈必须为0或1")
            return
        
        # 获取起始floor值
        try:
            start_floor_str = self.start_floor_var.get().strip()
            if start_floor_str == "":
                start_floor = 1  # 默认值
            else:
                start_floor = int(start_floor_str)
                if start_floor < 0:
                    messagebox.showwarning("输入错误", "起始floor值不能为负数")
                    return
        except ValueError:
            messagebox.showerror("输入错误", "起始floor值必须是整数")
            return
        
        # 解析角度数据
        try:
            # 先尝试常规解析（逗号分隔的数字）
            base_angles = []
            for angle_str in angles_input.split(','):
                angle_str = angle_str.strip()
                if angle_str:
                    base_angles.append(float(angle_str))
            
            if not base_angles:
                messagebox.showwarning("输入错误", "未找到有效的角度数据")
                return
                
        except ValueError:
            # 如果常规解析失败，尝试C++代码的解析方式
            try:
                base_angles = self.parse_angle_string(angles_input)
                if not base_angles:
                    messagebox.showerror("输入错误", "无法解析角度数据")
                    return
            except:
                messagebox.showerror("输入错误", "角度数据格式不正确")
                return
        
        # 应用角度转换逻辑
        transformed_angles = self.convert_angles_logic(base_angles)
        
        # 生成事件数据
        events = []
        twirl = False
        
        if circle == 0:  # 内圈
            for b in range(1, len(transformed_angles)):  # 从第二个角度开始
                current_floor = start_floor + (b - 1)
                
                if transformed_angles[b] < 180:
                    if twirl == True:
                        events.append({
                            "floor": current_floor,
                            "eventType": "Twirl"
                        })
                        twirl = False
                    bpm_value = transformed_angles[b] / 180 * bpm
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": round(bpm_value, 2),
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
                
                elif transformed_angles[b] > 180:
                    if twirl == False:
                        events.append({
                            "floor": current_floor,
                            "eventType": "Twirl"
                        })
                        twirl = True
                    bpm_value = (360 - transformed_angles[b]) / 180 * bpm
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": round(bpm_value, 2),
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
                
                else:  # transformed_angles[b] == 180
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": bpm,
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
        
        elif circle == 1:  # 外圈
            for b in range(1, len(transformed_angles)):
                current_floor = start_floor + (b - 1)
                
                if transformed_angles[b] < 180:
                    if twirl == False:
                        events.append({
                            "floor": current_floor,
                            "eventType": "Twirl"
                        })
                        twirl = True
                    bpm_value = (360 - transformed_angles[b]) / 180 * bpm
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": round(bpm_value, 2),
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
                
                elif transformed_angles[b] > 180:
                    if twirl == True:
                        events.append({
                            "floor": current_floor,
                            "eventType": "Twirl"
                        })
                        twirl = False
                    bpm_value = transformed_angles[b] / 180 * bpm
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": round(bpm_value, 2),
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
                
                else:  # transformed_angles[b] == 180
                    events.append({
                        "floor": current_floor,
                        "eventType": "SetSpeed",
                        "speedType": "Bpm",
                        "beatsPerMinute": bpm,
                        "bpmMultiplier": 1,
                        "angleOffset": 0
                    })
        
        # 显示结果
        self.converter_result_text.delete(1.0, tk.END)
        
        stats = f"角度-BPM转换完成！\n"
        stats += f"原始角度数: {len(base_angles)}\n"
        stats += f"转换后角度数: {len(transformed_angles)}\n"
        stats += f"BPM: {bpm}\n"
        stats += f"起始floor值: {start_floor}\n"
        stats += f"轨道类型: {'内圈' if circle == 0 else '外圈'}\n"
        stats += f"生成事件数: {len(events)}\n"
        stats += "-" * 50 + "\n\n"
        
        self.converter_result_text.insert(1.0, stats)
        
        # 显示角度转换对比
        self.converter_result_text.insert(tk.END, "角度转换对比：\n")
        self.converter_result_text.insert(tk.END, "-" * 40 + "\n")
        for i, (orig, trans) in enumerate(zip(base_angles, transformed_angles)):
            self.converter_result_text.insert(tk.END, f"角度[{i}]: {orig}° -> {trans}°\n")
        
        self.converter_result_text.insert(tk.END, "\n" + "-" * 50 + "\n\n")
        
        # 显示事件数据 - 每个事件在同一行
        self.converter_result_text.insert(tk.END, "生成的事件数据（每个事件在同一行）：\n")
        self.converter_result_text.insert(tk.END, "[\n")
        
        for i, event in enumerate(events):
            # 将事件转换为JSON格式，但保持在一行
            event_str = json.dumps(event, separators=(',', ':'))
            if i < len(events) - 1:
                event_str += ","
            self.converter_result_text.insert(tk.END, f"  {event_str}\n")
        
        self.converter_result_text.insert(tk.END, "]")
        
        # 保存当前事件数据用于复制
        self.current_events_json = events
        
        self.converter_stats_label.config(text=f"转换完成！共生成 {len(events)} 个事件，起始floor: {start_floor}")
        
        self.converter_copy_btn.configure(state='normal')
        
        self.status_bar.config(text=f"角度-BPM转换完成！生成 {len(events)} 个事件，起始floor: {start_floor}")
    
    def copy_to_clipboard(self):
        """复制雪花生成器结果到剪贴板"""
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            try:
                lines = result.split('\n')
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() and '°' not in lines[i] and ':' not in lines[i]:
                        angles_line = lines[i]
                        break
                else:
                    angles_line = lines[-1]
                
                angle_data = angles_line.strip()
                if angle_data:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(angle_data)
                    self.root.update()
                    self.status_bar.config(text="角度数据已复制到剪贴板")
                else:
                    self.status_bar.config(text="没有可复制的角度数据")
            except Exception as e:
                messagebox.showerror("复制失败", f"复制时出错: {str(e)}")
        else:
            messagebox.showwarning("复制失败", "没有可复制的数据")
    
    def copy_calc_to_clipboard(self):
        """复制角度加减器结果到剪贴板"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if result:
            try:
                lines = result.split('\n')
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() and '->' not in lines[i] and '：' not in lines[i]:
                        angles_line = lines[i]
                        break
                else:
                    angles_line = lines[-1]
                
                angle_data = angles_line.strip()
                if angle_data and (',' in angle_data or len(angle_data.split()) > 1):
                    self.root.clipboard_clear()
                    self.root.clipboard_append(angle_data)
                    self.root.update()
                    self.status_bar.config(text="角度数据已复制到剪贴板")
                else:
                    self.status_bar.config(text="没有可复制的角度数据")
            except Exception as e:
                messagebox.showerror("复制失败", f"复制时出错: {str(e)}")
        else:
            messagebox.showwarning("复制失败", "没有可复制的数据")
    
    def copy_converter_to_clipboard(self):
        """复制角度-BPM转换器结果到剪贴板"""
        if hasattr(self, 'current_events_json') and self.current_events_json:
            try:
                # 生成格式化的JSON字符串
                json_str = "[\n"
                for i, event in enumerate(self.current_events_json):
                    event_str = json.dumps(event, separators=(',', ':'))
                    if i < len(self.current_events_json) - 1:
                        event_str += ","
                    json_str += f"  {event_str}\n"
                json_str += "]"
                
                self.root.clipboard_clear()
                self.root.clipboard_append(json_str)
                self.root.update()
                self.status_bar.config(text="事件数据已复制到剪贴板")
            except Exception as e:
                messagebox.showerror("复制失败", f"复制时出错: {str(e)}")
        else:
            messagebox.showwarning("复制失败", "没有可复制的事件数据")
    
    def save_to_file(self):
        """保存雪花生成器结果到文件"""
        result = self.result_text.get(1.0, tk.END).strip()
        if not result:
            messagebox.showwarning("保存失败", "没有可保存的数据")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile="snowflake_angles.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("冰与火之舞雪花数据\n")
                    f.write("=" * 50 + "\n")
                    f.write(result)
                
                self.status_bar.config(text=f"数据已保存到: {file_path}")
                messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存文件时出错: {str(e)}")
    
    def save_calc_to_file(self):
        """保存角度加减器结果到文件"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if not result:
            messagebox.showwarning("保存失败", "没有可保存的数据")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile="calculated_angles.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("冰与火之舞角度计算数据\n")
                    f.write("=" * 50 + "\n")
                    f.write(result)
                
                self.status_bar.config(text=f"数据已保存到: {file_path}")
                messagebox.showinfo("保存成功", f"数据已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存文件时出错: {str(e)}")
    
    def transfer_to_calculator(self):
        """传输雪花生成器结果到角度加减器"""
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            lines = result.split('\n')
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip() and '°' not in lines[i] and ':' not in lines[i]:
                    angles_line = lines[i]
                    break
            else:
                angles_line = lines[-1]
            
            angle_data = angles_line.strip()
            if angle_data:
                self.calc_angle_entry.delete(1.0, tk.END)
                self.calc_angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab2)
                self.status_bar.config(text="数据已传输到角度加减器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "雪花生成器中没有数据")
    
    def transfer_to_converter(self):
        """传输雪花生成器结果到角度-BPM转换器"""
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            lines = result.split('\n')
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip() and '°' not in lines[i] and ':' not in lines[i]:
                    angles_line = lines[i]
                    break
            else:
                angles_line = lines[-1]
            
            angle_data = angles_line.strip()
            if angle_data:
                self.converter_angle_entry.delete(1.0, tk.END)
                self.converter_angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab3)
                self.status_bar.config(text="数据已传输到角度-BPM转换器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "雪花生成器中没有数据")
    
    def transfer_to_snowflake(self):
        """传输角度加减器结果到雪花生成器"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if result:
            lines = result.split('\n')
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip() and '->' not in lines[i] and '：' not in lines[i]:
                    angles_line = lines[i]
                    break
            else:
                angles_line = lines[-1]
            
            angle_data = angles_line.strip()
            if angle_data:
                self.angle_entry.delete(1.0, tk.END)
                self.angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab1)
                self.status_bar.config(text="数据已传输到雪花生成器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "角度加减器中没有数据")
    
    def transfer_calc_to_converter(self):
        """传输角度加减器结果到角度-BPM转换器"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if result:
            lines = result.split('\n')
            for i in range(len(lines)-1, -1, -1):
                if lines[i].strip() and '->' not in lines[i] and '：' not in lines[i]:
                    angles_line = lines[i]
                    break
            else:
                angles_line = lines[-1]
            
            angle_data = angles_line.strip()
            if angle_data:
                self.converter_angle_entry.delete(1.0, tk.END)
                self.converter_angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab3)
                self.status_bar.config(text="数据已传输到角度-BPM转换器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "角度加减器中没有数据")
    
    def transfer_converter_to_snowflake(self):
        """传输角度-BPM转换器结果到雪花生成器"""
        result = self.converter_result_text.get(1.0, tk.END).strip()
        if result:
            # 尝试从结果中提取原始角度数据
            lines = result.split('\n')
            angle_data = ""
            for line in lines:
                if "角度[" in line and "->" in line:
                    # 提取原始角度部分
                    parts = line.split("->")
                    if len(parts) > 0:
                        angle_part = parts[0].split(":")[-1].strip().replace("°", "")
                        if angle_data:
                            angle_data += ", " + angle_part
                        else:
                            angle_data = angle_part
            
            if angle_data:
                self.angle_entry.delete(1.0, tk.END)
                self.angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab1)
                self.status_bar.config(text="原始角度数据已传输到雪花生成器")
            else:
                messagebox.showwarning("传输失败", "无法从结果中提取原始角度数据")
        else:
            messagebox.showwarning("传输失败", "角度-BPM转换器中没有数据")
    
    def transfer_converter_to_calculator(self):
        """传输角度-BPM转换器结果到角度加减器"""
        result = self.converter_result_text.get(1.0, tk.END).strip()
        if result:
            # 尝试从结果中提取原始角度数据
            lines = result.split('\n')
            angle_data = ""
            for line in lines:
                if "角度[" in line and "->" in line:
                    # 提取原始角度部分
                    parts = line.split("->")
                    if len(parts) > 0:
                        angle_part = parts[0].split(":")[-1].strip().replace("°", "")
                        if angle_data:
                            angle_data += ", " + angle_part
                        else:
                            angle_data = angle_part
            
            if angle_data:
                self.calc_angle_entry.delete(1.0, tk.END)
                self.calc_angle_entry.insert(1.0, angle_data)
                self.notebook.select(self.tab2)
                self.status_bar.config(text="原始角度数据已传输到角度加减器")
            else:
                messagebox.showwarning("传输失败", "无法从结果中提取原始角度数据")
        else:
            messagebox.showwarning("传输失败", "角度-BPM转换器中没有数据")

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = SnowflakeCalculator(root)
    root.mainloop()