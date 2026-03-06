import calendar
import datetime
import tkinter as tk
from tkinter import ttk
import json
import os

# 数据存储路径（同EXE文件目录下的calendar_data.json）
DATA_FILE = "calendar_data.json"

class CalendarMiao:
    def __init__(self, root):
        self.root = root
        self.root.title("日历喵")
        self.root.geometry("650x500")
        
        # 基础数据
        self.today = datetime.datetime.now()
        self.cur_year = self.today.year
        self.cur_month = self.today.month
        self.today_day = self.today.day
        self.marks = {}  # 自定义标注 {年份: {月份: {日期: 标注}}}
        
        # 加载本地保存的数据
        self.load_data()
        
        # 样式配置
        self.style = ttk.Style()
        self.create_styles()
        
        # 创建界面
        self.create_widgets()
        # 初始化显示
        self.refresh_calendar()
        self.calculate_overtime()

    def create_styles(self):
        """创建自定义样式"""
        self.style.configure("Normal.TLabel", font=("微软雅黑", 10))
        self.style.configure("Weekend.TLabel", font=("微软雅黑", 10), foreground="red")
        self.style.configure("Today.TLabel", font=("微软雅黑", 10, "bold"), foreground="blue")
        self.style.configure("Mark.TLabel", font=("微软雅黑", 9), foreground="gold")
        self.style.configure("Result.TLabel", font=("微软雅黑", 11, "bold"), foreground="darkgreen")
        self.style.configure("Money.TLabel", font=("微软雅黑", 11, "bold"), foreground="red")

    def create_widgets(self):
        """创建界面控件"""
        # 1. 顶部标题栏
        title_frame = ttk.Frame(self.root, padding=8)
        title_frame.pack(fill=tk.X)
        
        self.year_month_label = ttk.Label(
            title_frame, 
            text=f"{self.cur_year}年{self.cur_month}月",
            font=("微软雅黑", 14, "bold")
        )
        self.year_month_label.pack(side=tk.LEFT, padx=15)
        
        # 月份切换按钮
        btn_frame = ttk.Frame(title_frame)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="上月", command=self.prev_month, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="今日", command=self.goto_today, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="下月", command=self.next_month, width=6).pack(side=tk.LEFT, padx=2)

        # 2. 标注编辑区
        edit_frame = ttk.Frame(self.root, padding=8)
        edit_frame.pack(fill=tk.X)
        
        ttk.Label(edit_frame, text="日期：").pack(side=tk.LEFT, padx=2)
        self.day_entry = ttk.Entry(edit_frame, width=5)
        self.day_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(edit_frame, text="标注：").pack(side=tk.LEFT, padx=2)
        self.mark_entry = ttk.Entry(edit_frame, width=8)
        self.mark_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(edit_frame, text="设置标注", command=self.set_mark, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(edit_frame, text="清空标注", command=self.clear_marks, width=8).pack(side=tk.LEFT, padx=5)

        # 3. 计算结果显示区
        result_frame = ttk.Frame(self.root, padding=5)
        result_frame.pack(fill=tk.X, padx=15)
        
        # 加班时长
        ttk.Label(result_frame, text="加班时长：", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=3)
        self.overtime_label = ttk.Label(result_frame, text="0.0 小时", style="Result.TLabel")
        self.overtime_label.pack(side=tk.LEFT, padx=8)
        
        # 加班费
        ttk.Label(result_frame, text="加班费：", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=3)
        self.money_label = ttk.Label(result_frame, text="0 元", style="Money.TLabel")
        self.money_label.pack(side=tk.LEFT, padx=8)
        
        # 不计加班时长
        ttk.Label(result_frame, text="不计加班时长：", font=("微软雅黑", 11)).pack(side=tk.LEFT, padx=3)
        self.remainder_label = ttk.Label(result_frame, text="0.0 小时", style="Result.TLabel")
        self.remainder_label.pack(side=tk.LEFT, padx=3)

        # 4. 日历表头
        week_frame = ttk.Frame(self.root)
        week_frame.pack(fill=tk.X, padx=15)
        
        week_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, name in enumerate(week_names):
            style = "Weekend.TLabel" if i >=5 else "Normal.TLabel"
            lbl = ttk.Label(
                week_frame, 
                text=name, 
                style=style,
                font=("微软雅黑", 10)
            )
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 5. 日历内容区
        self.cal_frame = ttk.Frame(self.root)
        self.cal_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    def load_data(self):
        """加载本地保存的标注数据"""
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.marks = json.load(f)
            else:
                self.marks = {}
        except:
            self.marks = {}

    def save_data(self):
        """保存标注数据到本地"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.marks, f, ensure_ascii=False, indent=2)
        except:
            pass

    def is_weekend(self, year, month, day):
        """判断是否是周末"""
        weekday = datetime.date(year, month, day).weekday()
        return weekday >= 5

    def get_current_month_marks(self):
        """获取当前年月的标注数据"""
        year_key = str(self.cur_year)
        month_key = str(self.cur_month)
        return self.marks.get(year_key, {}).get(month_key, {})

    def calculate_overtime(self):
        """计算加班时长、加班费、余数"""
        # 获取当前月标注
        current_marks = self.get_current_month_marks()
        total_overtime = 0.0
        max_day = calendar.monthrange(self.cur_year, self.cur_month)[1]
        
        for day in range(1, max_day + 1):
            mark_str = current_marks.get(str(day), "")
            if not mark_str or not mark_str.replace(".", "").isdigit():
                continue
            
            mark_num = float(mark_str)
            if self.is_weekend(self.cur_year, self.cur_month, day):
                total_overtime += mark_num
            else:
                work_overtime = mark_num - 8
                if work_overtime > 0:
                    total_overtime += work_overtime
        
        # 计算加班费和余数
        integer_part = int(total_overtime // 4)
        remainder_part = total_overtime % 4
        overtime_money = integer_part * 75
        
        # 更新显示
        self.overtime_label.config(text=f"{total_overtime:.1f} 小时")
        self.money_label.config(text=f"{overtime_money} 元")
        self.remainder_label.config(text=f"{remainder_part:.1f} 小时")

    def refresh_calendar(self):
        """刷新日历显示"""
        self.year_month_label.config(text=f"{self.cur_year}年{self.cur_month}月")
        
        # 清空原有内容
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        # 获取当前月标注
        current_marks = self.get_current_month_marks()
        
        # 生成日历
        calendar.setfirstweekday(calendar.MONDAY)
        month_weeks = calendar.monthcalendar(self.cur_year, self.cur_month)
        
        for week in month_weeks:
            week_frame = ttk.Frame(self.cal_frame)
            week_frame.pack(fill=tk.X, pady=1)
            
            for day in week:
                day_frame = ttk.Frame(week_frame, height=50)
                day_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                day_frame.pack_propagate(False)
                
                if day == 0:
                    ttk.Label(day_frame, text="").pack(expand=True)
                    continue
                
                # 判断日期类型
                is_today = (self.cur_year == self.today.year and 
                            self.cur_month == self.today.month and 
                            day == self.today_day)
                is_weekend = self.is_weekend(self.cur_year, self.cur_month, day)
                
                # 选择样式
                if is_today:
                    style = "Today.TLabel"
                elif is_weekend:
                    style = "Weekend.TLabel"
                else:
                    style = "Normal.TLabel"
                
                # 日期标签
                day_lbl = ttk.Label(
                    day_frame, 
                    text=str(day), 
                    style=style, 
                    font=("微软雅黑", 12, "bold")
                )
                day_lbl.pack(expand=True, pady=(5, 2))
                
                # 标注标签
                mark_text = current_marks.get(str(day), "")
                mark_lbl = ttk.Label(
                    day_frame, 
                    text=mark_text, 
                    style="Mark.TLabel"
                )
                mark_lbl.pack()

    def set_mark(self):
        """设置标注并保存"""
        try:
            day = int(self.day_entry.get().strip())
            mark = self.mark_entry.get().strip()
            max_day = calendar.monthrange(self.cur_year, self.cur_month)[1]
            
            if 1 <= day <= max_day:
                # 层级存储：年份→月份→日期
                year_key = str(self.cur_year)
                month_key = str(self.cur_month)
                day_key = str(day)
                
                if year_key not in self.marks:
                    self.marks[year_key] = {}
                if month_key not in self.marks[year_key]:
                    self.marks[year_key][month_key] = {}
                
                self.marks[year_key][month_key][day_key] = mark
                self.save_data()  # 保存到本地
                self.refresh_calendar()
                self.calculate_overtime()
                self.day_entry.delete(0, tk.END)
                self.mark_entry.delete(0, tk.END)
        except ValueError:
            pass

    def clear_marks(self):
        """清空当前月标注并保存"""
        year_key = str(self.cur_year)
        month_key = str(self.cur_month)
        
        if year_key in self.marks and month_key in self.marks[year_key]:
            del self.marks[year_key][month_key]
            self.save_data()  # 保存到本地
            self.refresh_calendar()
            self.calculate_overtime()

    def prev_month(self):
        """切换到上个月"""
        self.cur_month -= 1
        if self.cur_month < 1:
            self.cur_month = 12
            self.cur_year -= 1
        self.refresh_calendar()
        self.calculate_overtime()

    def next_month(self):
        """切换到下个月"""
        self.cur_month += 1
        if self.cur_month > 12:
            self.cur_month = 1
            self.cur_year += 1
        self.refresh_calendar()
        self.calculate_overtime()

    def goto_today(self):
        """回到今日"""
        self.cur_year = self.today.year
        self.cur_month = self.today.month
        self.refresh_calendar()
        self.calculate_overtime()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarMiao(root)
    # 关闭窗口时自动保存数据
    root.protocol("WM_DELETE_WINDOW", lambda: (app.save_data(), root.destroy()))
    root.mainloop()