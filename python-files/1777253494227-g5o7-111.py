import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
import sys


class StudentEvaluationSystem:
    """学生综合素质评价计算系统 - 核心计算类"""
    
    def __init__(self):
        # 定义评分映射
        self.three_level_map = {'不及格': -1, '合格': 0, '优秀': 2}
        self.binary_map = {'有': 1, '无': 0}
        
        # 第一类项目（三档评分）
        self.type1_items = ['思想表现', '文明守纪', '学习态度', 
                           '社会工作', '实践公益', '团队精神']
        # 第二类项目（二档评分）
        self.type2_items = ['创新创业', '文体特长', '技能素质', '特殊经历']
    
    def calculate_type1(self, item1, item2, item3):
        """计算第一类项目：思想表现等"""
        v1 = self.three_level_map.get(str(item1).strip(), 0)
        v2 = self.three_level_map.get(str(item2).strip(), 0)
        v3 = self.three_level_map.get(str(item3).strip(), 0)
        
        total = v1 + v2 + v3
        
        if total <= -2:
            result = '不合格'
        elif total >= 4:
            result = '优秀'
        elif total in [-1, 0, 1, 3]:
            result = '合格'
        elif total == 2:
            # 特殊规则：检查第三项是否为优秀
            if v3 == 2:
                result = '优秀'
            else:
                result = '合格'
        else:
            result = '合格'
            
        return total, result
    
    def calculate_type2(self, item1, item2, item3):
        """计算第二类项目：创新创业等"""
        v1 = self.binary_map.get(str(item1).strip(), 0)
        v2 = self.binary_map.get(str(item2).strip(), 0)
        v3 = self.binary_map.get(str(item3).strip(), 0)
        
        total = v1 + v2 + v3
        
        if total >= 1:
            result = '有'
        else:
            result = '无'
            
        return total, result
    
    def process_dataframe(self, df):
        """处理整个数据框"""
        result_df = pd.DataFrame()
        result_df['姓名'] = df['姓名'] if '姓名' in df.columns else df.iloc[:, 0]
        
        # 处理第一类项目
        for item in self.type1_items:
            col1, col2, col3 = f'{item}1', f'{item}2', f'{item}3'
            if all(col in df.columns for col in [col1, col2, col3]):
                scores = df.apply(lambda row: self.calculate_type1(
                    row[col1], row[col2], row[col3]
                ), axis=1)
                result_df[f'{item}总'] = [s[1] for s in scores]
        
        # 处理第二类项目
        for item in self.type2_items:
            col1, col2, col3 = f'{item}1', f'{item}2', f'{item}3'
            if all(col in df.columns for col in [col1, col2, col3]):
                scores = df.apply(lambda row: self.calculate_type2(
                    row[col1], row[col2], row[col3]
                ), axis=1)
                result_df[f'{item}总'] = [s[1] for s in scores]
        
        return result_df


class EvaluationApp:
    """桌面应用程序类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("学生综合素质评价计算系统 v1.0")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # 设置窗口居中
        self.center_window()
        
        self.evaluator = StudentEvaluationSystem()
        self.input_df = None
        self.result_df = None
        
        self._create_ui()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = 1400
        height = 900
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_ui(self):
        """创建用户界面"""
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 定义颜色
        self.bg_color = '#f0f0f0'
        self.header_color = '#2c3e50'
        self.btn_primary = '#3498db'
        self.btn_success = '#27ae60'
        self.btn_warning = '#f39c12'
        
        self.root.configure(bg=self.bg_color)
        
        # ========== 顶部标题栏 ==========
        header = tk.Frame(self.root, bg=self.header_color, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header, 
            text="📊 学生综合素质评价计算系统", 
            font=('微软雅黑', 24, 'bold'),
            bg=self.header_color,
            fg='white'
        ).pack(pady=20)
        
        # ========== 主内容区 ==========
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 左侧控制面板
        left_frame = tk.LabelFrame(
            main_frame, 
            text=" 控制面板 ", 
            font=('微软雅黑', 12, 'bold'),
            bg=self.bg_color,
            fg='#2c3e50',
            padx=15,
            pady=15
        )
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        # --- 文件操作按钮 ---
        btn_frame = tk.LabelFrame(
            left_frame,
            text=" 文件操作 ",
            font=('微软雅黑', 10, 'bold'),
            bg=self.bg_color,
            fg='#34495e',
            padx=10,
            pady=10
        )
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.btn_import = tk.Button(
            btn_frame,
            text="📥  导入Excel文件",
            font=('微软雅黑', 11),
            bg=self.btn_primary,
            fg='white',
            width=18,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._import_file
        )
        self.btn_import.pack(pady=5)
        self._add_hover_effect(self.btn_import, self.btn_primary, '#2980b9')
        
        self.btn_calc = tk.Button(
            btn_frame,
            text="🧮  开始计算",
            font=('微软雅黑', 11),
            bg=self.btn_success,
            fg='white',
            width=18,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._calculate,
            state=tk.DISABLED
        )
        self.btn_calc.pack(pady=5)
        self._add_hover_effect(self.btn_calc, self.btn_success, '#229954')
        
        self.btn_export = tk.Button(
            btn_frame,
            text="📤  导出结果",
            font=('微软雅黑', 11),
            bg=self.btn_warning,
            fg='white',
            width=18,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            command=self._export_file,
            state=tk.DISABLED
        )
        self.btn_export.pack(pady=5)
        self._add_hover_effect(self.btn_export, self.btn_warning, '#e67e22')
        
        # --- 规则说明 ---
        rule_frame = tk.LabelFrame(
            left_frame,
            text=" 评分规则说明 ",
            font=('微软雅黑', 10, 'bold'),
            bg=self.bg_color,
            fg='#34495e',
            padx=10,
            pady=10
        )
        rule_frame.pack(fill=tk.BOTH, expand=True)
        
        rules_text = """【第一类】思想表现、文明守纪、
学习态度、社会工作、实践公益、
团队精神

评分标准：
• 不及格 = -1 分
• 合格 = 0 分  
• 优秀 = 2 分

总评规则：
• 总分 ≤ -2  →  不合格
• 总分 -1,0,1,3  →  合格
• 总分 ≥ 4  →  优秀
• 总分 = 2 时：
  检查第3项是否为优秀
  是→优秀，否→合格

━━━━━━━━━━━━━━

【第二类】创新创业、文体特长、
技能素质、特殊经历

评分标准：
• 有 = 1 分
• 无 = 0 分

总评规则：
• 总分 ≥ 1  →  有
• 总分 = 0  →  无"""
        
        rule_label = tk.Label(
            rule_frame,
            text=rules_text,
            font=('微软雅黑', 9),
            bg=self.bg_color,
            fg='#2c3e50',
            justify=tk.LEFT,
            anchor=tk.NW
        )
        rule_label.pack(fill=tk.BOTH, expand=True)
        
        # 右侧数据展示区
        right_frame = tk.Frame(main_frame, bg=self.bg_color)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- 输入数据预览 ---
        input_frame = tk.LabelFrame(
            right_frame,
            text=" 输入数据预览 ",
            font=('微软雅黑', 11, 'bold'),
            bg=self.bg_color,
            fg='#2c3e50',
            padx=10,
            pady=10
        )
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建表格
        self.input_tree = self._create_table(input_frame, height=6)
        
        # --- 计算结果 ---
        output_frame = tk.LabelFrame(
            right_frame,
            text=" 计算结果 ",
            font=('微软雅黑', 11, 'bold'),
            bg=self.bg_color,
            fg=self.btn_success,
            padx=10,
            pady=10
        )
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output_tree = self._create_table(output_frame, height=20)
        
        # ========== 底部状态栏 ==========
        self.status_var = tk.StringVar(value="就绪 | 请导入Excel文件")
        status_bar = tk.Frame(self.root, bg='#bdc3c7', height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        status_bar.pack_propagate(False)
        
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=('微软雅黑', 10),
            bg='#bdc3c7',
            fg='#2c3e50',
            anchor=tk.W
        ).pack(side=tk.LEFT, padx=10, pady=3)
    
    def _add_hover_effect(self, widget, normal_color, hover_color):
        """添加鼠标悬停效果"""
        def on_enter(e):
            widget['bg'] = hover_color
        def on_leave(e):
            widget['bg'] = normal_color
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def _create_table(self, parent, height=10):
        """创建数据表格"""
        # 创建框架
        frame = tk.Frame(parent, bg=self.bg_color)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 表格
        tree = ttk.Treeview(
            frame,
            height=height,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # 设置表格样式
        style = ttk.Style()
        style.configure("Treeview", font=('微软雅黑', 9), rowheight=25)
        style.configure("Treeview.Heading", font=('微软雅黑', 9, 'bold'))
        
        return tree
    
    def _import_file(self):
        """导入Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel或CSV文件",
            filetypes=[
                ("Excel文件", "*.xlsx *.xls"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 读取文件
            if file_path.endswith('.csv'):
                self.input_df = pd.read_csv(file_path, encoding='utf-8')
            else:
                self.input_df = pd.read_excel(file_path)
            
            # 显示预览
            self._display_dataframe(self.input_tree, self.input_df.head(10))
            
            # 更新状态
            filename = os.path.basename(file_path)
            self.status_var.set(f"已导入: {filename} | 共 {len(self.input_df)} 行数据")
            
            # 启用计算按钮
            self.btn_calc.config(state=tk.NORMAL)
            
            messagebox.showinfo(
                "导入成功", 
                f"✅ 成功导入文件！\n\n文件名：{filename}\n数据行数：{len(self.input_df)} 行\n\n请点击【开始计算】按钮。"
            )
            
        except Exception as e:
            messagebox.showerror("导入失败", f"❌ 错误信息：\n{str(e)}\n\n请检查文件格式是否正确！")
    
    def _calculate(self):
        """执行计算"""
        if self.input_df is None:
            messagebox.showwarning("提示", "请先导入数据！")
            return
        
        try:
            # 执行计算
            self.result_df = self.evaluator.process_dataframe(self.input_df)
            
            # 显示结果
            self._display_dataframe(self.output_tree, self.result_df)
            
            # 更新状态
            self.status_var.set(f"计算完成 | 共 {len(self.result_df)} 条结果 | 请点击【导出结果】")
            
            # 启用导出按钮
            self.btn_export.config(state=tk.NORMAL)
            
            # 显示完成提示
            msg = "✅ 计算完成！\n\n"
            msg += f"处理记录数：{len(self.result_df)} 条\n"
            msg += f"输出列数：{len(self.result_df.columns)} 列\n\n"
            msg += "包含以下评价项：\n"
            for col in self.result_df.columns[1:]:
                msg += f"  • {col}\n"
            msg += "\n请点击【导出结果】保存文件。"
            
            messagebox.showinfo("计算完成", msg)
            
        except Exception as e:
            messagebox.showerror("计算错误", f"❌ 错误信息：\n{str(e)}\n\n请检查输入数据格式是否符合要求！")
    
    def _export_file(self):
        """导出结果"""
        if self.result_df is None:
            messagebox.showwarning("提示", "请先计算数据！")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存计算结果",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel文件", "*.xlsx"),
                ("CSV文件", "*.csv")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 保存文件
            if file_path.endswith('.csv'):
                self.result_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                self.result_df.to_excel(file_path, index=False)
            
            # 更新状态
            filename = os.path.basename(file_path)
            self.status_var.set(f"已导出: {filename}")
            
            messagebox.showinfo(
                "导出成功",
                f"✅ 结果已保存！\n\n保存路径：\n{file_path}\n\n可以直接打开Excel查看结果。"
            )
            
        except Exception as e:
            messagebox.showerror("导出失败", f"❌ 错误信息：\n{str(e)}")
    
    def _display_dataframe(self, tree, df):
        """在表格中显示DataFrame"""
        # 清空现有内容
        tree.delete(*tree.get_children())
        
        # 设置列
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        
        # 配置列
        for col in df.columns:
            tree.heading(col, text=col)
            # 根据内容长度设置列宽
            max_len = max(
                len(str(col)),
                df[col].astype(str).str.len().max() if len(df) > 0 else 0
            )
            width = min(max(max_len * 10 + 20, 80), 200)
            tree.column(col, width=width, anchor=tk.CENTER)
        
        # 插入数据（交替行颜色）
        for idx, row in df.iterrows():
            values = [str(v) if pd.notna(v) else "" for v in row]
            
            # 交替行颜色
            tag = 'even' if idx % 2 == 0 else 'odd'
            tree.insert("", tk.END, values=values, tags=(tag,))
        
        # 设置交替行颜色
        tree.tag_configure('even', background='#ffffff')
        tree.tag_configure('odd', background='#f8f9fa')


def main():
    """主函数"""
    # 设置DPI感知（解决高分屏模糊）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建窗口
    root = tk.Tk()
    
    # 设置图标（如果有的话）
    # root.iconbitmap('icon.ico')
    
    # 创建应用
    app = EvaluationApp(root)
    
    # 运行
    root.mainloop()


if __name__ == "__main__":
    main()