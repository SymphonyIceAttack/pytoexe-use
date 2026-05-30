import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import time
import threading
from tkinter.scrolledtext import ScrolledText
import csv
import os
from collections import defaultdict

# 数据库文件名
DB_NAME = "daily_tasks.db"

class DailyTaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("每日任务清单")
        self.root.geometry("850x700")
        self.root.minsize(750, 600)
        
        # 当前显示的日期（仅用于当天，但跨天检测用）
        self.current_date = datetime.date.today()
        # 上次刷新日期（用于跨天重置）
        self.last_display_date = self.current_date
        
        # 初始化数据库
        self.init_db()
        
        # 创建UI组件
        self.create_widgets()
        
        # 加载今日任务和笔记
        self.load_today_data()
        
        # 启动倒计时更新
        self.update_countdown()
        
        # 启动日期检查（每分钟检查一次跨天）
        self.check_date_change()
        
        # 确保窗口关闭时释放资源
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 任务模板表（存储固定的任务列表）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                order_id INTEGER DEFAULT 0
            )
        ''')
        
        # 每日任务状态表（存储每天每个任务的完成状态）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_task_status (
                date TEXT NOT NULL,
                task_id INTEGER NOT NULL,
                completed INTEGER DEFAULT 0,
                PRIMARY KEY (date, task_id),
                FOREIGN KEY (task_id) REFERENCES task_templates(id) ON DELETE CASCADE
            )
        ''')
        
        # 每日笔记表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_notes (
                date TEXT PRIMARY KEY,
                note TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        """创建界面组件"""
        # 顶部框架：日期显示和倒计时
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X)
        
        self.date_label = tk.Label(top_frame, text="", font=("微软雅黑", 16, "bold"))
        self.date_label.pack(side=tk.LEFT, padx=20)
        
        self.countdown_label = tk.Label(top_frame, text="距离今晚22点: --:--:--", font=("微软雅黑", 12), fg="blue")
        self.countdown_label.pack(side=tk.RIGHT, padx=20)
        
        # 任务管理区域
        task_frame = tk.LabelFrame(self.root, text="任务清单", font=("微软雅黑", 12), padx=10, pady=5)
        task_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 任务列表（使用Treeview支持更好的显示）
        columns = ("状态", "任务内容")
        self.task_tree = ttk.Treeview(task_frame, columns=columns, show="headings", height=12)
        self.task_tree.heading("状态", text="状态")
        self.task_tree.heading("任务内容", text="任务内容")
        self.task_tree.column("状态", width=60, anchor="center")
        self.task_tree.column("任务内容", width=500)
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # 绑定双击任务切换完成状态
        self.task_tree.bind("<Double-1>", self.toggle_complete)
        
        # 任务操作按钮框架
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(btn_frame, text="新任务:").pack(side=tk.LEFT, padx=5)
        self.new_task_entry = tk.Entry(btn_frame, width=30)
        self.new_task_entry.pack(side=tk.LEFT, padx=5)
        self.new_task_entry.bind("<Return>", lambda e: self.add_task())
        tk.Button(btn_frame, text="添加任务", command=self.add_task).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="修改选中任务", command=self.modify_task).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除选中任务", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="切换完成状态", command=self.toggle_complete).pack(side=tk.LEFT, padx=5)
        
        # 笔记区域
        note_frame = tk.LabelFrame(self.root, text="每日笔记", font=("微软雅黑", 12), padx=5, pady=5)
        note_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.note_text = ScrolledText(note_frame, height=6, font=("微软雅黑", 10))
        self.note_text.pack(fill=tk.BOTH, expand=True)
        
        # 笔记保存按钮和导出按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10, fill=tk.X)
        
        tk.Button(bottom_frame, text="保存今日笔记", command=self.save_note, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="导出一周任务清单", command=self.export_weekly_report, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="重置今日所有任务(清空勾选)", command=self.reset_today_completion, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(bottom_frame, text="刷新", command=self.load_today_data).pack(side=tk.LEFT, padx=10)
    
    def load_today_data(self):
        """加载今日任务和笔记"""
        today_str = self.current_date.isoformat()
        self.date_label.config(text=f"今日日期: {today_str}")
        
        # 确保当天所有任务都有状态记录，并根据跨天重置逻辑决定是否重置完成状态
        self.ensure_today_statuses()
        
        # 加载任务显示
        self.refresh_task_list()
        
        # 加载笔记
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT note FROM daily_notes WHERE date = ?", (today_str,))
        row = cursor.fetchone()
        note_content = row[0] if row else ""
        conn.close()
        
        # 清空并插入笔记
        self.note_text.delete(1.0, tk.END)
        self.note_text.insert(tk.END, note_content)
    
    def ensure_today_statuses(self):
        """确保当天每个任务都有状态记录，并根据日期切换重置完成状态"""
        today_str = self.current_date.isoformat()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 获取所有任务模板
        cursor.execute("SELECT id FROM task_templates ORDER BY order_id, id")
        tasks = cursor.fetchall()
        
        # 日期切换检查（如果上次显示的日期不是今天，则重置今日所有任务的完成状态为未完成）
        is_date_changed = (self.last_display_date != self.current_date)
        if is_date_changed:
            # 将当天所有任务状态重置为未完成
            for (task_id,) in tasks:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_task_status (date, task_id, completed)
                    VALUES (?, ?, 0)
                ''', (today_str, task_id))
            conn.commit()
            self.last_display_date = self.current_date
        else:
            # 确保每个任务都有今日的记录（如果没有则插入未完成）
            for (task_id,) in tasks:
                cursor.execute('''
                    SELECT completed FROM daily_task_status WHERE date = ? AND task_id = ?
                ''', (today_str, task_id))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO daily_task_status (date, task_id, completed)
                        VALUES (?, ?, 0)
                    ''', (today_str, task_id))
            conn.commit()
        conn.close()
    
    def refresh_task_list(self):
        """刷新任务列表显示"""
        # 清空现有项
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        today_str = self.current_date.isoformat()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 获取任务及其今日完成状态
        cursor.execute('''
            SELECT t.id, t.description, COALESCE(d.completed, 0) as completed
            FROM task_templates t
            LEFT JOIN daily_task_status d ON t.id = d.task_id AND d.date = ?
            ORDER BY t.order_id, t.id
        ''', (today_str,))
        
        tasks = cursor.fetchall()
        for task_id, description, completed in tasks:
            status = "✅ 已完成" if completed else "⬜ 未完成"
            # 存储task_id到item以便操作
            item_id = self.task_tree.insert("", tk.END, values=(status, description), iid=str(task_id))
        
        conn.close()
    
    def add_task(self):
        """添加新任务"""
        description = self.new_task_entry.get().strip()
        if not description:
            messagebox.showwarning("警告", "任务描述不能为空")
            return
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # 获取最大order_id
        cursor.execute("SELECT MAX(order_id) FROM task_templates")
        max_order = cursor.fetchone()[0]
        new_order = (max_order + 1) if max_order is not None else 0
        
        cursor.execute('''
            INSERT INTO task_templates (description, order_id) VALUES (?, ?)
        ''', (description, new_order))
        task_id = cursor.lastrowid
        
        # 为今天添加状态（未完成）
        today_str = self.current_date.isoformat()
        cursor.execute('''
            INSERT INTO daily_task_status (date, task_id, completed) VALUES (?, ?, 0)
        ''', (today_str, task_id))
        
        conn.commit()
        conn.close()
        
        self.new_task_entry.delete(0, tk.END)
        self.refresh_task_list()
        messagebox.showinfo("成功", "任务添加成功")
    
    def modify_task(self):
        """修改选中的任务"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要修改的任务")
            return
        
        task_id = int(selected[0])
        # 获取当前描述
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM task_templates WHERE id = ?", (task_id,))
        current_desc = cursor.fetchone()[0]
        conn.close()
        
        # 弹出输入框
        new_desc = tk.simpledialog.askstring("修改任务", "请输入新的任务描述:", initialvalue=current_desc)
        if new_desc and new_desc.strip():
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE task_templates SET description = ? WHERE id = ?", (new_desc.strip(), task_id))
            conn.commit()
            conn.close()
            self.refresh_task_list()
            messagebox.showinfo("成功", "任务修改成功")
    
    def delete_task(self):
        """删除选中的任务"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要删除的任务")
            return
        
        if not messagebox.askyesno("确认删除", "确定要删除这个任务吗？相关历史完成记录也会被删除。"):
            return
        
        task_id = int(selected[0])
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM task_templates WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        self.refresh_task_list()
        messagebox.showinfo("成功", "任务已删除")
    
    def toggle_complete(self, event=None):
        """切换任务的完成状态（打勾/取消打勾）"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要切换状态的任务")
            return
        
        task_id = int(selected[0])
        today_str = self.current_date.isoformat()
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 获取当前完成状态
        cursor.execute('''
            SELECT completed FROM daily_task_status WHERE date = ? AND task_id = ?
        ''', (today_str, task_id))
        row = cursor.fetchone()
        if row:
            new_status = 0 if row[0] else 1
            cursor.execute('''
                UPDATE daily_task_status SET completed = ? WHERE date = ? AND task_id = ?
            ''', (new_status, today_str, task_id))
        else:
            # 如果没有记录，新建一条并设为完成
            new_status = 1
            cursor.execute('''
                INSERT INTO daily_task_status (date, task_id, completed) VALUES (?, ?, ?)
            ''', (today_str, task_id, new_status))
        
        conn.commit()
        conn.close()
        self.refresh_task_list()
    
    def reset_today_completion(self):
        """手动重置今日所有任务的完成状态（清空所有打勾）"""
        if messagebox.askyesno("确认重置", "确定要将今日所有任务重置为未完成状态吗？"):
            today_str = self.current_date.isoformat()
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE daily_task_status SET completed = 0 WHERE date = ?
            ''', (today_str,))
            conn.commit()
            conn.close()
            self.refresh_task_list()
            messagebox.showinfo("完成", "今日所有任务已重置为未完成")
    
    def save_note(self):
        """保存今日笔记"""
        note_content = self.note_text.get(1.0, tk.END).strip()
        today_str = self.current_date.isoformat()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_notes (date, note) VALUES (?, ?)
        ''', (today_str, note_content))
        conn.commit()
        conn.close()
        messagebox.showinfo("保存成功", "笔记已保存")
    
    def export_weekly_report(self):
        """导出最近一周的任务清单（包括任务完成状态和笔记）"""
        # 导出过去7天（包括今天）的数据
        export_dates = []
        for i in range(6, -1, -1):  # 从6天前到今天
            d = self.current_date - datetime.timedelta(days=i)
            export_dates.append(d)
        
        # 准备导出数据
        report_data = []
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 获取所有任务模板（用于列头）
        cursor.execute("SELECT id, description FROM task_templates ORDER BY order_id, id")
        all_tasks = cursor.fetchall()  # [(id, desc), ...]
        
        for date_obj in export_dates:
            date_str = date_obj.isoformat()
            # 获取当天笔记
            cursor.execute("SELECT note FROM daily_notes WHERE date = ?", (date_str,))
            note_row = cursor.fetchone()
            note = note_row[0] if note_row else ""
            
            # 获取当天每个任务的完成状态
            task_status = {}
            cursor.execute("SELECT task_id, completed FROM daily_task_status WHERE date = ?", (date_str,))
            for task_id, completed in cursor.fetchall():
                task_status[task_id] = "已完成" if completed else "未完成"
            
            # 构建一行数据（包含日期、笔记、每个任务的状态）
            row = {"日期": date_str, "笔记": note}
            for task_id, task_desc in all_tasks:
                col_name = task_desc
                status = task_status.get(task_id, "未完成")
                row[col_name] = status
            report_data.append(row)
        
        conn.close()
        
        if not all_tasks:
            messagebox.showwarning("无任务", "当前没有任何任务，请先添加任务后再导出。")
            return
        
        # 生成CSV文件
        file_path = f"weekly_report_{self.current_date.isoformat()}.csv"
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # 构建字段名：日期、笔记 + 每个任务描述
                fieldnames = ["日期", "笔记"] + [desc for _, desc in all_tasks]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in report_data:
                    writer.writerow(row)
            messagebox.showinfo("导出成功", f"一周任务清单已导出到文件:\n{os.path.abspath(file_path)}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出时出错: {str(e)}")
    
    def update_countdown(self):
        """更新距离晚上22点的倒计时"""
        now = datetime.datetime.now()
        today_22 = datetime.datetime(now.year, now.month, now.day, 22, 0, 0)
        
        if now >= today_22:
            # 如果已经过了22点，计算到明天22点的时间
            tomorrow_22 = today_22 + datetime.timedelta(days=1)
            delta = tomorrow_22 - now
            prefix = "距离明晚22点:"
        else:
            delta = today_22 - now
            prefix = "距离今晚22点:"
        
        # 格式化剩余时间
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.countdown_label.config(text=f"{prefix} {time_str}")
        # 每秒更新一次
        self.root.after(1000, self.update_countdown)
    
    def check_date_change(self):
        """定期检查日期是否变化（跨天重置）"""
        today = datetime.date.today()
        if today != self.current_date:
            # 日期发生变化
            self.current_date = today
            # 加载新一天的数据（会自动触发重置逻辑）
            self.load_today_data()
            # 可弹窗提示
            self.root.title(f"每日任务清单 - 新的一天 {today.isoformat()}")
        
        # 每分钟检查一次
        self.root.after(60000, self.check_date_change)
    
    def on_closing(self):
        """关闭程序时保存当前笔记"""
        self.save_note()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = DailyTaskApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()