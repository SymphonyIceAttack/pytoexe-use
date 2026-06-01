import tkinter as tk
from tkinter import ttk, messagebox

class PaintingCalculatorPlus:
    def __init__(self, root):
        """初始化主窗口"""
        self.root = root
        self.root.title("积分计算器")
        self.root.geometry("950x600")  # 增加宽度和高度以适应新列
        
        # 初始化样式配置
        self.configure_styles()
        
        # 积分计算规则字典（已包含背景积分）
        self.points_rules = {
            "精草（无网点无上色）": {"头像": 4, "半身": 8, "全身": 12, "背景": 8},
            "精草底色/勾线无网点": {"头像": 6, "半身": 12, "全身": 18, "背景": 12},
            "勾线有网点/二分上色": {"头像": 8, "半身": 16, "全身": 24, "背景": 16},
            "厚涂上色": {"头像": 12, "半身": 24, "全身": 36, "背景": 24}
        }

        # 创建界面组件
        self.create_widgets()

    def configure_styles(self):
        """配置全局样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主窗口背景设置
        self.root.configure(background="#FFFFFF")
        
        # 全局默认样式
        style.configure('.', 
                       background="#FFFFFF",
                       foreground="#000000",
                       font=('微软雅黑', 9))
        
        # 标签框架样式
        style.configure('TLabelframe', 
                       background="#FFFFFF",
                       bordercolor="#000000")
        
        # 按钮交互样式
        style.map('TButton',
                foreground=[('active', "#000000"), ('!active', "#000000")],
                background=[('active', "#FFFFFF"), ('!active', "#FFFFFF")])
        
        # 输入框样式配置
        style.configure('TEntry',
                       fieldbackground="#FFFFFF",
                       foreground='#000000')

    def create_widgets(self):
        """创建界面组件"""
        # 控制按钮区域
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=5, fill='x')
        
        ttk.Button(control_frame, text="恢复输入", 
                 command=self.reset_entries).pack(side='left', padx=5)

        # 数量输入区域
        input_frame = ttk.LabelFrame(self.root, text="数量输入")
        input_frame.pack(pady=10, padx=10, fill="x")

        # 创建表格标题（增加背景数量列）
        headers = ["类型", "头像数量", "半身数量", "全身数量", "背景数量"]
        for col, text in enumerate(headers):
            ttk.Label(input_frame, text=text).grid(row=0, column=col, padx=5, pady=5)

        # 动态创建输入框（每行4个数量输入：头像、半身、全身、背景）
        self.entries = {}
        for row, ptype in enumerate(self.points_rules.keys(), 1):
            ttk.Label(input_frame, text=ptype).grid(row=row, column=0, padx=5, sticky="w")
            
            entry_dict = {}
            for col in range(1, 5):  # 1~4 对应头像、半身、全身、背景
                entry = ttk.Entry(input_frame, width=8)
                entry.insert(0, "0")
                entry.grid(row=row, column=col, padx=5)
                # 根据列索引确定键名
                key = headers[col].replace("数量", "")
                entry_dict[key] = entry
            self.entries[ptype] = entry_dict

        # 额外加分输入区域
        bonus_frame = ttk.Frame(self.root)
        bonus_frame.pack(pady=5, fill="x")
        ttk.Label(bonus_frame, text="额外加分：").pack(side="left", padx=5)
        self.bonus_entry = ttk.Entry(bonus_frame, width=10)
        self.bonus_entry.insert(0, "0")
        self.bonus_entry.pack(side="left")
        ttk.Label(bonus_frame, text="积分").pack(side="left", padx=5)

        # 功能按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="计算总积分", command=self.calculate).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result).pack(side="left", padx=5)

        # 结果展示表格（增加背景积分列）
        result_frame = ttk.LabelFrame(self.root, text="计算结果")
        result_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.tree = ttk.Treeview(result_frame, 
                               columns=("type", "avatar", "half", "full", "background", "total"), 
                               show="headings")
        
        # 配置表格样式
        style = ttk.Style()
        style.configure('Treeview',
                      background="#FFFFFF",
                      foreground="#000000",
                      rowheight=25)
        style.configure('Treeview.Heading',
                      background="#FFFFFF",
                      foreground="#000000",
                      font=('微软雅黑', 10, 'bold'))

        # 设置表格列参数
        columns = [
            ("type", "类型", 200),
            ("avatar", "头像积分", 100),
            ("half", "半身积分", 100),
            ("full", "全身积分", 100),
            ("background", "背景积分", 100),
            ("total", "类型总积分", 120)
        ]
        
        for col_id, col_text, width in columns:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=width, anchor="center")

        self.tree.pack(fill="both", expand=True)
        
        # 特殊行样式配置
        self.tree.tag_configure("bonus", background='#0B0F01')
        self.tree.tag_configure("total", 
                              background="#FFFFFF",
                              foreground="#000000")

    def reset_entries(self):
        """恢复所有输入框到初始状态"""
        try:
            # 重置类型输入框（含背景）
            for ptype in self.entries.values():
                for entry in ptype.values():
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
            
            # 重置额外加分输入框
            self.bonus_entry.delete(0, tk.END)
            self.bonus_entry.insert(0, "0")
            
            # 清空结果表格
            for item in self.tree.get_children():
                self.tree.delete(item)
            
        except Exception as e:
            # 静默处理异常
            pass

    def validate_number(self, value):
        """数字验证方法"""
        try:
            return float(value) if value.strip() else 0.0
        except ValueError:
            return None

    def calculate(self):
        """执行积分计算（含背景）"""
        total_points = 0.0
        results = []
        
        # 清空旧数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 验证额外加分输入
        try:
            bonus = float(self.bonus_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "额外加分需要输入数字")
            return

        # 遍历所有类型进行计算
        for ptype, entries in self.entries.items():
            try:
                avatar = float(entries["头像"].get())
                half = float(entries["半身"].get())
                full = float(entries["全身"].get())
                bg = float(entries["背景"].get())   # 读取背景数量
            except ValueError:
                messagebox.showerror("输入错误", "请输入有效的数字")
                return

            rules = self.points_rules[ptype]
            avatar_points = avatar * rules["头像"]
            half_points = half * rules["半身"]
            full_points = full * rules["全身"]
            bg_points = bg * rules["背景"]          # 计算背景积分
            type_total = avatar_points + half_points + full_points + bg_points
            
            results.append((
                ptype,
                f"{avatar}×{rules['头像']}={avatar_points}",
                f"{half}×{rules['半身']}={half_points}",
                f"{full}×{rules['全身']}={full_points}",
                f"{bg}×{rules['背景']}={bg_points}",   # 背景积分显示
                type_total
            ))
            total_points += type_total

        # 插入数据
        for item in results:
            self.tree.insert("", "end", values=item)
        
        # 添加额外加分行
        self.tree.insert("", "end", 
                        values=("额外加分", "", "", "", "", f"{bonus}"),
                        tags=("bonus",))
        
        # 计算最终总积分
        final_total = total_points + bonus
        self.tree.insert("", "end", 
                        values=("最终总积分", "", "", "", "", f"{final_total}"),
                        tags=("total",))

    def copy_result(self):
        """复制最终结果到剪贴板"""
        try:
            items = self.tree.get_children()
            if not items:
                messagebox.showwarning("复制失败", "请先进行计算获取结果")
                return
                
            last_item = items[-1]
            values = self.tree.item(last_item, 'values')
            
            if values and values[0] == "最终总积分":
                result = values[-1]   # 最后一列是最终总积分
                self.root.clipboard_clear()
                self.root.clipboard_append(result)
                self.root.update()
            else:
                pass
        except Exception as e:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintingCalculatorPlus(root)
    root.mainloop()