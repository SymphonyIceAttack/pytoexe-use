import tkinter as tk
from tkinter import ttk, messagebox
import sys
from datetime import datetime, date

# 解决打包后中文乱码问题
if hasattr(sys, '_MEIPASS'):
    import locale
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

class RefundCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("退差价计算器")
        self.root.geometry("320x360")  # 微调高度容纳单价显示
        self.root.resizable(False, False)
        
        # 绑定回车键触发计算
        self.root.bind('<Return>', self.calc)
        
        # 字体样式（放大20%）
        style = ttk.Style()
        style.configure("TLabel", font=("微软雅黑", 12))
        style.configure("TEntry", font=("微软雅黑", 12))
        style.configure("TButton", font=("微软雅黑", 12))
        
        # 主容器
        main = ttk.Frame(root, padding=12)
        main.pack(expand=True, fill="both")
        
        # 1. 名称输入框（空白）
        self.name = ttk.Entry(main, width=28)
        self.name.pack(pady=(0, 6), fill="x")
        self.name.bind('<Return>', self.calc)
        
        # 2. 核心输入区域（开始日期置顶，无默认内容）
        # 开始日期（原总价位置）
        start_frame = ttk.Frame(main)
        start_frame.pack(fill="x", pady=2)
        ttk.Label(start_frame, text="开始日期：", width=7).pack(side="left")
        self.start_date = ttk.Entry(start_frame, width=9)
        self.start_date.pack(side="left", padx=6)
        self.start_date.bind('<Return>', self.calc)
        
        # 总价（下移）
        price_frame = ttk.Frame(main)
        price_frame.pack(fill="x", pady=2)
        ttk.Label(price_frame, text="总价：", width=7).pack(side="left")
        self.price = ttk.Entry(price_frame, width=9)
        self.price.pack(side="left", padx=6)
        self.price.bind('<Return>', self.calc)
        ttk.Label(price_frame, text="元").pack(side="left")
        
        # 天数（下移）
        days_frame = ttk.Frame(main)
        days_frame.pack(fill="x", pady=2)
        ttk.Label(days_frame, text="天数：", width=7).pack(side="left")
        self.days = ttk.Entry(days_frame, width=9)
        self.days.pack(side="left", padx=6)
        self.days.bind('<Return>', self.calc)
        ttk.Label(days_frame, text="天").pack(side="left")
        
        # 退款日期（下移）
        end_frame = ttk.Frame(main)
        end_frame.pack(fill="x", pady=2)
        ttk.Label(end_frame, text="退款日期：", width=7).pack(side="left")
        self.end_date = ttk.Entry(end_frame, width=9)
        self.end_date.pack(side="left", padx=6)
        self.end_date.bind('<Return>', self.calc)
        
        # 3. 计算按钮
        ttk.Button(main, text="计算应退差价", command=self.calc).pack(fill="x", pady=9)
        
        # 4. 结果显示（加回单价，文字放大）
        result_frame = ttk.Frame(main)
        result_frame.pack(fill="x", pady=(0, 0))
        
        self.used_days = tk.StringVar(value="")
        self.left_days = tk.StringVar(value="")
        self.unit_price = tk.StringVar(value="")  # 恢复单价变量
        self.refund_amount = tk.StringVar(value="")
        
        ttk.Label(result_frame, textvariable=self.used_days, font=("微软雅黑", 14, "bold"), foreground="#e63946").pack(anchor="w", pady=1)
        ttk.Label(result_frame, textvariable=self.left_days, font=("微软雅黑", 14, "bold"), foreground="#e63946").pack(anchor="w", pady=1)
        ttk.Label(result_frame, textvariable=self.unit_price, font=("微软雅黑", 14, "bold"), foreground="#e63946").pack(anchor="w", pady=1)  # 显示单价
        ttk.Label(result_frame, textvariable=self.refund_amount, font=("微软雅黑", 18, "bold"), foreground="#e63946").pack(anchor="w", pady=1)
        
    def parse_date(self, s):
        """解析月.日格式日期"""
        try:
            m, d = s.strip().split('.')
            return datetime(date.today().year, int(m), int(d))
        except:
            return None
        
    def remove_dot_zero(self, num):
        """移除数字末尾的.0"""
        if isinstance(num, float) and num.is_integer():
            return int(num)
        return num
        
    def calc(self, event=None):
        """核心计算逻辑"""
        try:
            # 获取并校验输入
            price_str = self.price.get().strip()
            days_str = self.days.get().strip()
            start_str = self.start_date.get().strip()
            end_str = self.end_date.get().strip()
            
            if not price_str or not days_str or not start_str or not end_str:
                messagebox.showerror("错误", "请填写所有输入项！")
                return
            
            # 类型转换
            price = float(price_str)
            days = float(days_str)
            start = self.parse_date(start_str)
            end = self.parse_date(end_str)
            
            # 数值校验
            if price <= 0 or days <= 0:
                messagebox.showerror("错误", "价格/天数必须大于0！")
                return
            if not start or not end:
                messagebox.showerror("错误", "日期格式：01.26（月.日）")
                return
            if end < start:
                messagebox.showerror("错误", "退款日期不能早于开始日期！")
                return
            
            # 计算差价
            used = round((end - start).days, 1)
            if used > days:
                messagebox.showerror("错误", f"使用天数({used}天)超过总天数({days}天)！")
                return
            
            # 清理.0后缀
            used_clean = self.remove_dot_zero(used)
            left = self.remove_dot_zero(round(days - used, 1))
            unit = round(price / days, 2)
            back = self.remove_dot_zero(round(left * unit, 2))
            
            # 更新结果（加回单价显示）
            self.used_days.set(f"使用天数：{used_clean}天")
            self.left_days.set(f"剩余天数：{left}天")
            self.unit_price.set(f"单价：{unit}元")  # 显示单价
            self.refund_amount.set(f"应退：{back}元")
            
        except ValueError:
            messagebox.showerror("错误", "总价/天数请输入有效数字！")
        except Exception as e:
            messagebox.showerror("错误", f"计算出错：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RefundCalculator(root)
    # 窗口居中
    x = (root.winfo_screenwidth()//2) - 160
    y = (root.winfo_screenheight()//2) - 180
    root.geometry(f"320x360+{x}+{y}")
    root.mainloop()