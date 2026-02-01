import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import math

class SnowflakeCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("冰与火之舞雪花计算器")
        self.root.geometry("850x800")
        self.root.configure(bg='#f0f0f0')
        
        # 设置窗口最小尺寸
        self.root.minsize(800, 700)
        
        # 创建样式
        self.create_styles()
        
        # 创建选项卡
        self.create_tabs()
        
        # 加载初始数据
        self.load_initial_data()
    
    def create_styles(self):
        """创建样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 按钮样式
        style.configure('TButton', font=('微软雅黑', 10), padding=5)
        style.configure('Title.TLabel', font=('微软雅黑', 16, 'bold'), background='#f0f0f0')
        style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'), background='#f0f0f0')
        
        # 选项卡样式
        style.configure('TNotebook.Tab', font=('微软雅黑', 10))
    
    def create_tabs(self):
        """创建选项卡"""
        # 创建Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建两个标签页
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab1, text="雪花生成器")
        self.notebook.add(self.tab2, text="角度加减器")
        
        # 创建雪花生成器界面
        self.create_snowflake_tab()
        
        # 创建角度加减器界面
        self.create_angle_calculator_tab()
        
        # 创建状态栏
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_snowflake_tab(self):
        """创建雪花生成器标签页"""
        # 标题
        title_frame = ttk.Frame(self.tab1, padding=10)
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(title_frame, text="❄️ 雪花生成器 ❄️", 
                               style='Title.TLabel')
        title_label.pack()
        
        # 第一瓣雪花数据输入区域
        input_frame = ttk.LabelFrame(self.tab1, text="第一步：输入第一瓣雪花的角度数据", padding=15)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(input_frame, text="请输入角度数据（用逗号分隔）：", 
                 font=('微软雅黑', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.angle_entry = tk.Text(input_frame, height=4, width=80, font=('Consolas', 10))
        self.angle_entry.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 雪花配置区域
        config_frame = ttk.LabelFrame(self.tab1, text="第二步：配置雪花参数", padding=15)
        config_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 瓣数选择
        ttk.Label(config_frame, text="雪花瓣数：").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.petal_var = tk.StringVar(value="8")
        petal_combo = ttk.Combobox(config_frame, textvariable=self.petal_var, 
                                   values=["4", "6", "8", "12", "16", "24", "32", "自定义"], 
                                   width=10, state="readonly")
        petal_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 20))
        petal_combo.bind("<<ComboboxSelected>>", self.on_petal_change)
        
        # 自定义瓣数输入
        ttk.Label(config_frame, text="或自定义瓣数：").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        
        self.custom_petal_var = tk.StringVar()
        self.custom_petal_entry = ttk.Entry(config_frame, textvariable=self.custom_petal_var, width=10)
        self.custom_petal_entry.grid(row=0, column=3, sticky=tk.W, pady=5)
        self.custom_petal_entry.configure(state='disabled')
        
        # 旋转方向
        ttk.Label(config_frame, text="旋转方向：").grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.rotation_var = tk.StringVar(value="negative")
        ttk.Radiobutton(config_frame, text="负角度（顺时针）", variable=self.rotation_var, 
                       value="negative").grid(row=1, column=1, sticky=tk.W, padx=(5, 20))
        ttk.Radiobutton(config_frame, text="正角度（逆时针）", variable=self.rotation_var, 
                       value="positive").grid(row=1, column=2, columnspan=2, sticky=tk.W)
        
        # 输出选项
        output_frame = ttk.LabelFrame(self.tab1, text="第三步：生成结果", padding=15)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 生成按钮
        button_frame = ttk.Frame(output_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.generate_btn = ttk.Button(button_frame, text="生成雪花数据", 
                                      command=self.generate_snowflake, style='TButton')
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空", 
                                   command=self.clear_snowflake)
        self.clear_btn.pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = ttk.Frame(output_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(result_frame, text="生成的角度数据：", 
                 font=('微软雅黑', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # 滚动文本框显示结果 - 修复：添加自动换行
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=15, 
            font=('Consolas', 10), 
            wrap=tk.WORD,  # 按单词换行
            spacing1=2,    # 行间距
            spacing2=2,
            spacing3=2
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 操作按钮
        action_frame = ttk.Frame(output_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.copy_btn = ttk.Button(action_frame, text="复制到剪贴板", 
                                  command=self.copy_to_clipboard, state='disabled')
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_btn = ttk.Button(action_frame, text="保存到文件", 
                                  command=self.save_to_file, state='disabled')
        self.save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.transfer_btn = ttk.Button(action_frame, text="传输到角度加减器", 
                                      command=self.transfer_to_calculator, state='disabled')
        self.transfer_btn.pack(side=tk.LEFT)
    
    def create_angle_calculator_tab(self):
        """创建角度加减器标签页"""
        # 标题
        title_frame = ttk.Frame(self.tab2, padding=10)
        title_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(title_frame, text="📐 角度加减器 📐", 
                               style='Title.TLabel')
        title_label.pack()
        
        # 角度数据输入区域
        input_frame = ttk.LabelFrame(self.tab2, text="输入角度数据", padding=15)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(input_frame, text="请输入角度数据（用逗号分隔）：", 
                 font=('微软雅黑', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.calc_angle_entry = tk.Text(input_frame, height=4, width=80, font=('Consolas', 10))
        self.calc_angle_entry.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 操作按钮
        calc_button_frame = ttk.Frame(input_frame)
        calc_button_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Button(calc_button_frame, text="从雪花生成器导入", 
                  command=self.import_from_snowflake).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_button_frame, text="清空", 
                  command=self.clear_calculator).pack(side=tk.LEFT)
        
        # 角度加减配置
        calc_frame = ttk.LabelFrame(self.tab2, text="角度加减配置", padding=15)
        calc_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 加减角度输入
        ttk.Label(calc_frame, text="要加上的角度：").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.add_angle_var = tk.StringVar(value="45")
        add_angle_entry = ttk.Entry(calc_frame, textvariable=self.add_angle_var, width=10)
        add_angle_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 20))
        
        ttk.Label(calc_frame, text="度").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # 角度归一化选项
        self.normalize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(calc_frame, text="将结果归一化到0-360度", 
                       variable=self.normalize_var).grid(row=0, column=3, sticky=tk.W, padx=(20, 5))
        
        # 计算按钮
        calc_btn_frame = ttk.Frame(calc_frame)
        calc_btn_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        self.calc_btn = ttk.Button(calc_btn_frame, text="计算", 
                                  command=self.calculate_angles)
        self.calc_btn.pack(side=tk.LEFT)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(self.tab2, text="计算结果", padding=15)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # 结果统计
        self.calc_stats_label = ttk.Label(result_frame, text="就绪", font=('微软雅黑', 10))
        self.calc_stats_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 滚动文本框显示结果 - 修复：添加自动换行
        self.calc_result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=12, 
            font=('Consolas', 10), 
            wrap=tk.WORD,  # 按单词换行
            spacing1=2,    # 行间距
            spacing2=2,
            spacing3=2
        )
        self.calc_result_text.pack(fill=tk.BOTH, expand=True)
        
        # 操作按钮
        calc_action_frame = ttk.Frame(result_frame)
        calc_action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.calc_copy_btn = ttk.Button(calc_action_frame, text="复制到剪贴板", 
                                       command=self.copy_calc_to_clipboard, state='disabled')
        self.calc_copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.calc_save_btn = ttk.Button(calc_action_frame, text="保存到文件", 
                                       command=self.save_calc_to_file, state='disabled')
        self.calc_save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(calc_action_frame, text="传输到雪花生成器", 
                  command=self.transfer_to_snowflake).pack(side=tk.LEFT)
    
    def load_initial_data(self):
        """加载初始数据"""
        # 雪花生成器初始数据为空
        self.angle_entry.delete(1.0, tk.END)
        self.angle_entry.insert(1.0, "")
        
        # 角度加减器初始数据为空
        self.calc_angle_entry.delete(1.0, tk.END)
        self.calc_angle_entry.insert(1.0, "")
    
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
        self.status_bar.config(text="雪花生成器已清空")
    
    def clear_calculator(self):
        """清空角度加减器内容"""
        self.calc_angle_entry.delete(1.0, tk.END)
        self.calc_result_text.delete(1.0, tk.END)
        self.calc_copy_btn.configure(state='disabled')
        self.calc_save_btn.configure(state='disabled')
        self.status_bar.config(text="角度加减器已清空")
    
    def import_from_snowflake(self):
        """从雪花生成器导入数据"""
        data = self.angle_entry.get(1.0, tk.END).strip()
        if data:
            self.calc_angle_entry.delete(1.0, tk.END)
            self.calc_angle_entry.insert(1.0, data)
            self.status_bar.config(text="已从雪花生成器导入数据")
            self.notebook.select(self.tab2)  # 切换到角度加减器标签页
        else:
            messagebox.showwarning("导入失败", "雪花生成器中没有数据")
    
    def format_angle(self, angle):
        """格式化角度，整数不显示小数部分，小数保留原始形式"""
        # 处理浮点数精度问题
        epsilon = 1e-10
        angle = float(angle)
        
        # 四舍五入到小数点后10位
        angle_rounded = round(angle, 10)
        
        # 检查是否为整数
        if abs(angle_rounded - round(angle_rounded)) < epsilon:
            return str(int(round(angle_rounded)))
        else:
            # 去掉末尾的零
            result = str(angle_rounded).rstrip('0').rstrip('.')
            # 如果结果是空的（比如45.0变成了"45"），返回整数形式
            if not result:
                return str(int(angle_rounded))
            return result
    
    def generate_snowflake(self):
        """生成雪花数据"""
        # 获取角度数据
        angles_input = self.angle_entry.get(1.0, tk.END).strip()
        if not angles_input:
            messagebox.showwarning("输入错误", "请输入角度数据")
            return
        
        # 解析角度数据
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
        
        # 获取瓣数
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
        
        # 计算旋转角度
        rotation_angle = 360 / petals
        
        # 根据选择的旋转方向确定角度符号
        if self.rotation_var.get() == "negative":
            rotation_angle = -rotation_angle
        
        # 生成完整的雪花数据
        all_angles = []
        
        for i in range(petals):
            rotation = i * rotation_angle
            
            # 对每个角度加上旋转角度，并归一化到[0, 360)范围
            for angle in base_angles:
                new_angle = (angle + rotation) % 360
                all_angles.append(new_angle)
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        
        # 添加统计信息
        stats = f"雪花生成完成！\n"
        stats += f"原始角度数: {len(base_angles)}\n"
        stats += f"雪花瓣数: {petals}\n"
        stats += f"旋转角度: {self.format_angle(rotation_angle)}°\n"
        stats += f"总角度数: {len(all_angles)}\n"
        stats += "-" * 40 + "\n\n"
        
        self.result_text.insert(1.0, stats)
        
        # 添加角度数据
        formatted_angles = [self.format_angle(angle) for angle in all_angles]
        angles_str = ", ".join(formatted_angles)
        self.result_text.insert(tk.END, angles_str)
        
        # 启用操作按钮
        self.copy_btn.configure(state='normal')
        self.save_btn.configure(state='normal')
        self.transfer_btn.configure(state='normal')
        
        # 更新状态栏
        self.status_bar.config(text=f"生成完成！总角度数: {len(all_angles)}")
    
    def calculate_angles(self):
        """计算角度加减"""
        # 获取角度数据
        angles_input = self.calc_angle_entry.get(1.0, tk.END).strip()
        if not angles_input:
            messagebox.showwarning("输入错误", "请输入角度数据")
            return
        
        # 获取加减角度
        try:
            add_angle = float(self.add_angle_var.get())
        except ValueError:
            messagebox.showerror("输入错误", "加减角度必须是数字")
            return
        
        # 解析角度数据
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
        
        # 计算结果
        result_angles = []
        for angle in base_angles:
            new_angle = angle + add_angle
            if self.normalize_var.get():
                new_angle = new_angle % 360
            result_angles.append(new_angle)
        
        # 显示结果
        self.calc_result_text.delete(1.0, tk.END)
        
        # 添加统计信息
        stats = f"角度计算完成！\n"
        stats += f"原始角度数: {len(base_angles)}\n"
        stats += f"加减角度: {self.format_angle(add_angle)}°\n"
        stats += f"归一化: {'是' if self.normalize_var.get() else '否'}\n"
        stats += "-" * 40 + "\n\n"
        
        self.calc_result_text.insert(1.0, stats)
        
        # 添加角度数据对比
        self.calc_result_text.insert(tk.END, "原始角度 -> 计算结果\n")
        self.calc_result_text.insert(tk.END, "-" * 30 + "\n")
        
        for i, (orig, result) in enumerate(zip(base_angles, result_angles)):
            self.calc_result_text.insert(tk.END, f"{self.format_angle(orig)}° -> {self.format_angle(result)}°\n")
        
        self.calc_result_text.insert(tk.END, "\n" + "-" * 40 + "\n\n")
        
        # 添加纯结果数据
        formatted_results = [self.format_angle(angle) for angle in result_angles]
        angles_str = ", ".join(formatted_results)
        self.calc_result_text.insert(tk.END, "计算结果：\n")
        self.calc_result_text.insert(tk.END, angles_str)
        
        # 更新统计标签
        self.calc_stats_label.config(text=f"计算完成！共 {len(result_angles)} 个角度")
        
        # 启用操作按钮
        self.calc_copy_btn.configure(state='normal')
        self.calc_save_btn.configure(state='normal')
        
        # 更新状态栏
        self.status_bar.config(text=f"角度计算完成！共 {len(result_angles)} 个角度")
    
    def copy_to_clipboard(self):
        """复制雪花生成器结果到剪贴板（使用tkinter自带的剪贴板功能）"""
        result = self.result_text.get(1.0, tk.END).strip()
        if result:
            try:
                # 只复制角度数据部分
                lines = result.split('\n')
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() and '°' not in lines[i] and ':' not in lines[i]:
                        angles_line = lines[i]
                        break
                else:
                    angles_line = lines[-1]
                
                angle_data = angles_line.strip()
                if angle_data:
                    # 使用tkinter自带的剪贴板功能
                    self.root.clipboard_clear()  # 清空剪贴板
                    self.root.clipboard_append(angle_data)  # 添加文本到剪贴板
                    # 保持剪贴板内容（程序关闭后仍然有效）
                    self.root.update()
                    self.status_bar.config(text="角度数据已复制到剪贴板")
                else:
                    self.status_bar.config(text="没有可复制的角度数据")
            except Exception as e:
                messagebox.showerror("复制失败", f"复制时出错: {str(e)}")
        else:
            messagebox.showwarning("复制失败", "没有可复制的数据")
    
    def copy_calc_to_clipboard(self):
        """复制角度加减器结果到剪贴板（使用tkinter自带的剪贴板功能）"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if result:
            try:
                # 只复制角度数据部分
                lines = result.split('\n')
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip() and '->' not in lines[i] and '：' not in lines[i]:
                        angles_line = lines[i]
                        break
                else:
                    angles_line = lines[-1]
                
                angle_data = angles_line.strip()
                if angle_data and (',' in angle_data or len(angle_data.split()) > 1):
                    # 使用tkinter自带的剪贴板功能
                    self.root.clipboard_clear()  # 清空剪贴板
                    self.root.clipboard_append(angle_data)  # 添加文本到剪贴板
                    # 保持剪贴板内容（程序关闭后仍然有效）
                    self.root.update()
                    self.status_bar.config(text="角度数据已复制到剪贴板")
                else:
                    self.status_bar.config(text="没有可复制的角度数据")
            except Exception as e:
                messagebox.showerror("复制失败", f"复制时出错: {str(e)}")
        else:
            messagebox.showwarning("复制失败", "没有可复制的数据")
    
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
            # 提取角度数据部分
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
                self.notebook.select(self.tab2)  # 切换到角度加减器标签页
                self.status_bar.config(text="数据已传输到角度加减器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "雪花生成器中没有数据")
    
    def transfer_to_snowflake(self):
        """传输角度加减器结果到雪花生成器"""
        result = self.calc_result_text.get(1.0, tk.END).strip()
        if result:
            # 提取角度数据部分
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
                self.notebook.select(self.tab1)  # 切换到雪花生成器标签页
                self.status_bar.config(text="数据已传输到雪花生成器")
            else:
                messagebox.showwarning("传输失败", "没有可传输的角度数据")
        else:
            messagebox.showwarning("传输失败", "角度加减器中没有数据")

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = SnowflakeCalculator(root)
    root.mainloop()