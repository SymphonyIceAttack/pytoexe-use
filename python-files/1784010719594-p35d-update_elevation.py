import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyodbc
import csv
import os

class ElevationUpdater:
    def __init__(self, root):
        self.root = root
        root.title("高程批量更新工具")
        root.geometry("600x400")

        # 控件
        tk.Label(root, text="数据文件 (.dat)").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.dat_path = tk.StringVar()
        tk.Entry(root, textvariable=self.dat_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="浏览...", command=self.browse_dat).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="目标数据库 (.mdb)").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.mdb_path = tk.StringVar()
        tk.Entry(root, textvariable=self.mdb_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="浏览...", command=self.browse_mdb).grid(row=1, column=2, padx=5, pady=5)

        tk.Label(root, text="目标表名").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.table_name = tk.StringVar(value="点表")
        tk.Entry(root, textvariable=self.table_name, width=20).grid(row=2, column=1, padx=5, pady=5, sticky='w')

        tk.Label(root, text="点号字段名").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.id_field = tk.StringVar(value="点号")
        tk.Entry(root, textvariable=self.id_field, width=20).grid(row=3, column=1, padx=5, pady=5, sticky='w')

        self.update_btn = tk.Button(root, text="开始更新", command=self.run_update, bg='lightblue', font=('Arial', 12))
        self.update_btn.grid(row=4, column=1, pady=15)

        # 日志显示
        self.log_text = tk.Text(root, height=12, width=70)
        self.log_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
        scroll = tk.Scrollbar(root, command=self.log_text.yview)
        scroll.grid(row=5, column=3, sticky='ns')
        self.log_text.config(yscrollcommand=scroll.set)

    def browse_dat(self):
        f = filedialog.askopenfilename(filetypes=[("DAT files", "*.dat"), ("All files", "*.*")])
        if f:
            self.dat_path.set(f)

    def browse_mdb(self):
        f = filedialog.askopenfilename(filetypes=[("Access MDB", "*.mdb"), ("All files", "*.*")])
        if f:
            self.mdb_path.set(f)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def run_update(self):
        dat_file = self.dat_path.get().strip()
        mdb_file = self.mdb_path.get().strip()
        table = self.table_name.get().strip()
        id_col = self.id_field.get().strip()

        if not dat_file or not mdb_file or not table or not id_col:
            messagebox.showerror("错误", "请完整填写所有字段")
            return

        if not os.path.exists(dat_file):
            messagebox.showerror("错误", "数据文件不存在")
            return
        if not os.path.exists(mdb_file):
            messagebox.showerror("错误", "数据库文件不存在")
            return

        # 读取dat数据（无表头，列序：点号,类别,X,Y,高程）
        try:
            with open(dat_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows:
                messagebox.showerror("错误", "数据文件为空")
                return
            # 每行至少5列
            data = []
            for idx, row in enumerate(rows, 1):
                if len(row) < 5:
                    self.log(f"警告：第{idx}行列数不足，跳过")
                    continue
                p_id = row[0].strip()
                category = row[1].strip()
                try:
                    x = float(row[2])
                    y = float(row[3])
                    z = float(row[4])
                except ValueError:
                    self.log(f"警告：第{idx}行坐标/高程格式错误，跳过")
                    continue
                data.append((p_id, category, x, y, z))
            if not data:
                messagebox.showerror("错误", "没有有效数据")
                return
        except Exception as e:
            messagebox.showerror("读取错误", str(e))
            return

        # 连接MDB
        conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            f"DBQ={mdb_file};"
        )
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
        except Exception as e:
            messagebox.showerror("数据库连接错误", f"请确认已安装 Access 数据库引擎\n{str(e)}")
            return

        # 检查表是否存在
        cursor.execute("SELECT name FROM MSysObjects WHERE type=1 AND name=?", (table,))
        if not cursor.fetchone():
            messagebox.showerror("错误", f"表 '{table}' 不存在")
            conn.close()
            return

        # 检查字段是否存在
        try:
            cursor.execute(f"SELECT TOP 1 [{id_col}] FROM [{table}]")
        except Exception:
            messagebox.showerror("错误", f"字段 '{id_col}' 不存在")
            conn.close()
            return

        # 准备更新/插入
        update_sql = f"UPDATE [{table}] SET 高程 = ? WHERE [{id_col}] = ?"
        insert_sql = f"INSERT INTO [{table}] ([{id_col}], 类别, X, Y, 高程) VALUES (?,?,?,?,?)"

        updated = 0
        inserted = 0
        failed = 0

        self.log("开始处理...")
        for p_id, category, x, y, z in data:
            # 先检查是否存在
            cursor.execute(f"SELECT COUNT(*) FROM [{table}] WHERE [{id_col}] = ?", (p_id,))
            exist = cursor.fetchone()[0] > 0
            try:
                if exist:
                    cursor.execute(update_sql, (z, p_id))
                    updated += 1
                else:
                    cursor.execute(insert_sql, (p_id, category, x, y, z))
                    inserted += 1
                conn.commit()
            except Exception as e:
                failed += 1
                self.log(f"错误：点号 {p_id} 处理失败 - {str(e)}")
                conn.rollback()

        conn.close()
        self.log(f"完成！更新 {updated} 条，插入 {inserted} 条，失败 {failed} 条。")
        messagebox.showinfo("完成", f"处理完毕\n更新 {updated} 条\n插入 {inserted} 条\n失败 {failed} 条")

if __name__ == "__main__":
    root = tk.Tk()
    app = ElevationUpdater(root)
    root.mainloop()