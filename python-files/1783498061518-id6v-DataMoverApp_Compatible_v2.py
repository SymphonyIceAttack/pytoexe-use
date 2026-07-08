import os
import re
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import win32com.client as win32
import pythoncom


# ==========================================
# 辅助函数：自然排序 (与 Windows 资源管理器一致)
# ==========================================
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(s))]


# ==========================================
# 核心业务逻辑类 1：多对多迁移
# ==========================================
class ExcelMigrator:
    def __init__(self, source_dir, target_dir, mapping_list, global_rules, log_queue, progress_queue):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.mapping_list = mapping_list
        self.rules = global_rules
        self.log_queue = log_queue
        self.progress_queue = progress_queue
        self.excel_app = None

    def log(self, msg, level="INFO"):
        self.log_queue.put(f"[{level}] {msg}")

    def run(self):
        pythoncom.CoInitialize()
        try:
            total_tasks = len(self.mapping_list)
            if total_tasks == 0:
                self.log("没有需要执行的任务！", "WARNING")
                return

            self.log("正在启动后台 Excel 进程...")
            self.excel_app = win32.Dispatch('Excel.Application')
            self.excel_app.Visible = False
            self.excel_app.DisplayAlerts = False

            self.log(f"[模式1] 共发现 {total_tasks} 个迁移任务。开始执行...")

            for index, pair in enumerate(self.mapping_list):
                try:
                    self.process_pair(pair)
                except Exception as e:
                    self.log(f"处理 [{pair['src']}] 时出错: {str(e)}", "ERROR")
                self.progress_queue.put((index + 1) / total_tasks * 100)

            self.log("=== [模式1] 所有任务执行完毕！ ===", "SUCCESS")
        except Exception as e:
            self.log(f"程序运行发生严重错误: {str(e)}", "ERROR")
        finally:
            if self.excel_app:
                try:
                    self.excel_app.Quit()
                except:
                    pass
            pythoncom.CoUninitialize()
            self.progress_queue.put(100)

    def process_pair(self, pair):
        src_file = os.path.abspath(os.path.join(self.source_dir, pair['src']))
        tgt_file = os.path.abspath(os.path.join(self.target_dir, pair['tgt']))

        if not os.path.exists(src_file): raise FileNotFoundError(f"找不到源文件: {src_file}")
        if not os.path.exists(tgt_file): raise FileNotFoundError(f"找不到目标文件: {tgt_file}")

        self.log(f"处理: {pair['src']} -> {pair['tgt']}")
        src_wb, tgt_wb = None, None
        try:
            src_wb = self.excel_app.Workbooks.Open(src_file, ReadOnly=True)
            tgt_wb = self.excel_app.Workbooks.Open(tgt_file)
            src_wb.Application.Calculate()

            src_ws = src_wb.Sheets(self.rules['src_sheet'])
            tgt_ws = tgt_wb.Sheets(self.rules['tgt_sheet'])

            src_range = src_ws.Range(self.rules['src_range'])
            tgt_range = tgt_ws.Range(self.rules['tgt_range'])

            src_range.Copy()
            tgt_range.PasteSpecial(Paste=-4163, Operation=-4142, SkipBlanks=False, Transpose=False)
            self.excel_app.CutCopyMode = False

            tgt_wb.Save()
            self.log(f"  -> 成功粘贴(仅值)并保存。")
        finally:
            if src_wb:
                try:
                    src_wb.Close(SaveChanges=False)
                except:
                    pass
            if tgt_wb:
                try:
                    tgt_wb.Close(SaveChanges=True)
                except:
                    pass


# ==========================================
# 核心业务逻辑类 2：单源列分发
# ==========================================
class ColumnDistributor:
    @staticmethod
    def read_source_column(src_file, src_sheet, src_start_cell, tgt_dir, log_queue, result_queue):
        pythoncom.CoInitialize()
        excel = None
        try:
            log_queue.put("[INFO] 正在启动 Excel 读取源列数据...")
            excel = win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False

            wb = excel.Workbooks.Open(os.path.abspath(src_file))
            ws = wb.Sheets(src_sheet)

            start_rng = ws.Range(src_start_cell)
            col = start_rng.Column
            row = start_rng.Row

            last_row = ws.Cells(ws.Rows.Count, col).End(-4162).Row
            if last_row < row: last_row = row

            read_range = ws.Range(ws.Cells(row, col), ws.Cells(last_row, col))
            values = read_range.Value

            data = []
            if not isinstance(values, tuple):
                if values is not None: data.append(values)
            else:
                for r in values:
                    val = r[0] if isinstance(r, tuple) else r
                    if val is not None:
                        data.append(val)
                    else:
                        break

            wb.Close(False)
            log_queue.put(f"[INFO] 成功从上到下读取 {len(data)} 个有效源数据。")

            tgt_files = sorted([f for f in os.listdir(tgt_dir) if f.lower().endswith(('.xlsx', '.xls'))],
                               key=natural_sort_key)

            mapping = []
            min_len = min(len(data), len(tgt_files))
            for i in range(min_len):
                mapping.append({'value': data[i], 'tgt': tgt_files[i]})

            if len(data) != len(tgt_files):
                log_queue.put(
                    f"[WARNING] 数量不一致! 源数据:{len(data)}个, 目标文件:{len(tgt_files)}个。已按顺序匹配前 {min_len} 对。")

            result_queue.put(mapping)
        except Exception as e:
            log_queue.put(f"[ERROR] 读取源数据失败: {str(e)}")
        finally:
            if excel:
                try:
                    excel.Quit()
                except:
                    pass
            pythoncom.CoUninitialize()

    @staticmethod
    def distribute_data(tgt_dir, tgt_sheet, tgt_cell, mapping_list, log_queue, progress_queue):
        pythoncom.CoInitialize()
        excel = None
        try:
            total = len(mapping_list)
            log_queue.put(f"[INFO] [模式2] 开始分发数据到 {total} 个目标文件...")
            excel = win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False

            for i, item in enumerate(mapping_list):
                tgt_path = os.path.abspath(os.path.join(tgt_dir, item['tgt']))
                wb = excel.Workbooks.Open(tgt_path)
                ws = wb.Sheets(tgt_sheet)

                ws.Range(tgt_cell).Value = item['value']

                wb.Save()
                wb.Close(True)
                progress_queue.put((i + 1) / total * 100)

            log_queue.put("=== [模式2] 单源列分发任务全部完成！ ===", "SUCCESS")
        except Exception as e:
            log_queue.put(f"[ERROR] 分发执行出错: {str(e)}")
        finally:
            if excel:
                try:
                    excel.Quit()
                except:
                    pass
            pythoncom.CoUninitialize()
            progress_queue.put(100)


# ==========================================
# GUI 界面类
# ==========================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("年度统计数据自动化迁移工具 v5.3 (完美兼容xls版)")
        self.root.geometry("1000x800")

        self.log_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        self.tab2_mapping_queue = queue.Queue()
        self.is_running = False

        self.setup_ui()
        self.process_queues()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text=" 模式1: 多对多批量迁移 (文件夹对文件夹) ")
        self.notebook.add(self.tab2, text=" 模式2: 单源列分发迁移 (单列对多文件) ")

        self.setup_ui_tab1()
        self.setup_ui_tab2()
        self.setup_ui_common()

    # ---------------- 【修复点】获取工作表名称辅助方法 (改用 win32com 兼容 xls) ----------------
    def fetch_sheets(self, path_var, combobox):
        path = path_var.get() if hasattr(path_var, 'get') else path_var
        if not path or not os.path.exists(path):
            messagebox.showwarning("提示", "请先选择有效的Excel文件或包含Excel文件的目录！")
            return

        target_file = path
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if f.lower().endswith(('.xlsx', '.xls'))]
            if not files:
                messagebox.showwarning("提示", "目录下没有找到Excel文件！")
                return
            target_file = os.path.join(path, sorted(files, key=natural_sort_key)[0])

        excel = None
        try:
            # 使用 win32com 读取，完美兼容 .xls 和 .xlsx
            pythoncom.CoInitialize()
            excel = win32.Dispatch('Excel.Application')
            excel.Visible = False
            excel.DisplayAlerts = False

            wb = excel.Workbooks.Open(os.path.abspath(target_file), ReadOnly=True)
            sheets = [sheet.Name for sheet in wb.Sheets]
            wb.Close(False)

            combobox['values'] = sheets
            if sheets:
                combobox.current(0)
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, f"[INFO] 成功从 {os.path.basename(target_file)} 获取工作表: {sheets}\n")
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            else:
                messagebox.showwarning("提示", "未读取到任何工作表！")
        except Exception as e:
            messagebox.showerror("错误", f"读取工作表失败:\n{str(e)}\n\n请确保文件未被其他程序打开。")
        finally:
            if excel:
                try:
                    excel.Quit()
                except:
                    pass
            pythoncom.CoUninitialize()

    # ---------------- Tab 1 UI ----------------
    def setup_ui_tab1(self):
        frame_settings = ttk.LabelFrame(self.tab1, text="1. 路径与全局规则设置", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        self.source_dir = self.create_path_row(frame_settings, "源文件目录 (旧一年):", 0, is_dir=True)
        self.target_dir = self.create_path_row(frame_settings, "目标文件目录 (新一年):", 1, is_dir=True)

        rule_frame = ttk.Frame(frame_settings)
        rule_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Label(rule_frame, text="源工作表:").grid(row=0, column=0, padx=5, sticky="w")
        self.src_sheet = ttk.Combobox(rule_frame, width=15, state="readonly")
        self.src_sheet.grid(row=0, column=1, padx=5)
        ttk.Button(rule_frame, text="获取", width=5,
                   command=lambda: self.fetch_sheets(self.source_dir, self.src_sheet)).grid(row=0, column=2, padx=2)

        ttk.Label(rule_frame, text="源区域(如B2:D10):").grid(row=0, column=3, padx=5, sticky="w")
        self.src_range = tk.StringVar(value="B2:D10")
        ttk.Entry(rule_frame, textvariable=self.src_range, width=15).grid(row=0, column=4, padx=5)

        ttk.Label(rule_frame, text="目标工作表:").grid(row=1, column=0, padx=5, sticky="w", pady=5)
        self.tgt_sheet = ttk.Combobox(rule_frame, width=15, state="readonly")
        self.tgt_sheet.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(rule_frame, text="获取", width=5,
                   command=lambda: self.fetch_sheets(self.target_dir, self.tgt_sheet)).grid(row=1, column=2, padx=2,
                                                                                            pady=5)

        ttk.Label(rule_frame, text="目标起点(如C5):").grid(row=1, column=3, padx=5, sticky="w", pady=5)
        self.tgt_range = tk.StringVar(value="C5")
        ttk.Entry(rule_frame, textvariable=self.tgt_range, width=15).grid(row=1, column=4, padx=5, pady=5)

        self.btn_refresh_t1 = ttk.Button(rule_frame, text="刷新并自动匹配", command=self.refresh_mapping_t1)
        self.btn_refresh_t1.grid(row=0, column=5, rowspan=2, padx=20)

        frame_mapping = ttk.LabelFrame(self.tab1, text="2. 文件映射关系 (按Windows名称自然排序，可剔除)", padding=10)
        frame_mapping.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "src_file", "tgt_file")
        self.tree_t1 = ttk.Treeview(frame_mapping, columns=columns, show="headings", selectmode="extended")
        self.tree_t1.heading("id", text="序号")
        self.tree_t1.heading("src_file", text="源文件 (旧)")
        self.tree_t1.heading("tgt_file", text="目标文件 (新)")
        self.tree_t1.column("id", width=50, anchor="center")
        self.tree_t1.column("src_file", width=350)
        self.tree_t1.column("tgt_file", width=350)

        scrollbar = ttk.Scrollbar(frame_mapping, orient="vertical", command=self.tree_t1.yview)
        self.tree_t1.configure(yscrollcommand=scrollbar.set)
        self.tree_t1.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_map_frame = ttk.Frame(frame_mapping)
        btn_map_frame.pack(side="bottom", fill="x", pady=(5, 0))
        ttk.Button(btn_map_frame, text="剔除选中项", command=lambda: self.remove_selected(self.tree_t1)).pack(
            side="left", padx=5)
        ttk.Button(btn_map_frame, text="清空列表", command=lambda: self.clear_mapping(self.tree_t1)).pack(side="left",
                                                                                                          padx=5)

        self.btn_start_t1 = ttk.Button(self.tab1, text="[开始] 执行多对多数据迁移", command=self.start_migration_t1)
        self.btn_start_t1.pack(pady=10)

    # ---------------- Tab 2 UI ----------------
    def setup_ui_tab2(self):
        frame_settings = ttk.LabelFrame(self.tab2, text="1. 单源文件与目标规则设置", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        self.t2_src_file = self.create_path_row(frame_settings, "源Excel文件 (单文件):", 0, is_dir=False)
        self.t2_tgt_dir = self.create_path_row(frame_settings, "目标文件目录 (多文件):", 1, is_dir=True)

        rule_frame = ttk.Frame(frame_settings)
        rule_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Label(rule_frame, text="源工作表:").grid(row=0, column=0, padx=5, sticky="w")
        self.t2_src_sheet = ttk.Combobox(rule_frame, width=15, state="readonly")
        self.t2_src_sheet.grid(row=0, column=1, padx=5)
        ttk.Button(rule_frame, text="获取", width=5,
                   command=lambda: self.fetch_sheets(self.t2_src_file, self.t2_src_sheet)).grid(row=0, column=2, padx=2)

        ttk.Label(rule_frame, text="源起始单元格(如A2):").grid(row=0, column=3, padx=5, sticky="w")
        self.t2_src_start = tk.StringVar(value="A2")
        ttk.Entry(rule_frame, textvariable=self.t2_src_start, width=15).grid(row=0, column=4, padx=5)

        ttk.Label(rule_frame, text="目标工作表:").grid(row=1, column=0, padx=5, sticky="w", pady=5)
        self.t2_tgt_sheet = ttk.Combobox(rule_frame, width=15, state="readonly")
        self.t2_tgt_sheet.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(rule_frame, text="获取", width=5,
                   command=lambda: self.fetch_sheets(self.t2_tgt_dir, self.t2_tgt_sheet)).grid(row=1, column=2, padx=2,
                                                                                               pady=5)

        ttk.Label(rule_frame, text="目标单元格(如C5):").grid(row=1, column=3, padx=5, sticky="w", pady=5)
        self.t2_tgt_cell = tk.StringVar(value="C5")
        ttk.Entry(rule_frame, textvariable=self.t2_tgt_cell, width=15).grid(row=1, column=4, padx=5, pady=5)

        self.btn_refresh_t2 = ttk.Button(rule_frame, text="读取源列并匹配", command=self.refresh_mapping_t2)
        self.btn_refresh_t2.grid(row=0, column=5, rowspan=2, padx=20)

        frame_mapping = ttk.LabelFrame(self.tab2,
                                       text="2. 分发映射关系 (源数据从上到下，目标文件按Windows自然排序，可剔除)",
                                       padding=10)
        frame_mapping.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("id", "src_val", "tgt_file")
        self.tree_t2 = ttk.Treeview(frame_mapping, columns=columns, show="headings", selectmode="extended")
        self.tree_t2.heading("id", text="序号")
        self.tree_t2.heading("src_val", text="源单元格数据 (将粘贴的值)")
        self.tree_t2.heading("tgt_file", text="目标文件 (接收该值的文件)")
        self.tree_t2.column("id", width=50, anchor="center")
        self.tree_t2.column("src_val", width=350)
        self.tree_t2.column("tgt_file", width=350)

        scrollbar = ttk.Scrollbar(frame_mapping, orient="vertical", command=self.tree_t2.yview)
        self.tree_t2.configure(yscrollcommand=scrollbar.set)
        self.tree_t2.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_map_frame = ttk.Frame(frame_mapping)
        btn_map_frame.pack(side="bottom", fill="x", pady=(5, 0))
        ttk.Button(btn_map_frame, text="剔除选中项", command=lambda: self.remove_selected(self.tree_t2)).pack(
            side="left", padx=5)
        ttk.Button(btn_map_frame, text="清空列表", command=lambda: self.clear_mapping(self.tree_t2)).pack(side="left",
                                                                                                          padx=5)

        self.btn_start_t2 = ttk.Button(self.tab2, text="[开始] 执行单列分发迁移", command=self.start_migration_t2)
        self.btn_start_t2.pack(pady=10)

    # ---------------- 公共 UI ----------------
    def setup_ui_common(self):
        frame_log = ttk.LabelFrame(self.root, text="运行控制与日志", padding=10)
        frame_log.pack(fill="x", padx=10, pady=5)

        self.progress = ttk.Progressbar(frame_log, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, state="disabled", height=8,
                                                  font=("Consolas", 9))
        self.log_text.pack(fill="x")

    # ---------------- 辅助方法 ----------------
    def create_path_row(self, parent, label_text, row, is_dir):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=3)
        var = tk.StringVar()
        entry = ttk.Entry(parent, textvariable=var, width=50)
        entry.grid(row=row, column=1, padx=5, pady=3)

        def browse():
            path = filedialog.askdirectory() if is_dir else filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx *.xls")])
            if path: var.set(path)

        ttk.Button(parent, text="浏览...", command=browse).grid(row=row, column=2, pady=3)
        return var

    def remove_selected(self, tree):
        for item in tree.selection(): tree.delete(item)
        for i, item in enumerate(tree.get_children()): tree.set(item, "id", i + 1)

    def clear_mapping(self, tree):
        for item in tree.get_children(): tree.delete(item)

    # ---------------- Tab 1 逻辑 ----------------
    def refresh_mapping_t1(self):
        src_dir, tgt_dir = self.source_dir.get(), self.target_dir.get()
        if not os.path.isdir(src_dir) or not os.path.isdir(tgt_dir):
            return messagebox.showwarning("警告", "请先正确选择源和目标文件夹！")

        src_files = sorted([f for f in os.listdir(src_dir) if f.lower().endswith(('.xlsx', '.xls'))],
                           key=natural_sort_key)
        tgt_files = sorted([f for f in os.listdir(tgt_dir) if f.lower().endswith(('.xlsx', '.xls'))],
                           key=natural_sort_key)

        self.clear_mapping(self.tree_t1)
        for i in range(min(len(src_files), len(tgt_files))):
            self.tree_t1.insert("", "end", values=(i + 1, src_files[i], tgt_files[i]))

    def start_migration_t1(self):
        if self.is_running: return
        rules = {'src_sheet': self.src_sheet.get(), 'tgt_sheet': self.tgt_sheet.get(),
                 'src_range': self.src_range.get().strip(), 'tgt_range': self.tgt_range.get().strip()}
        if not all(rules.values()): return messagebox.showwarning("警告", "请确保已获取并选择工作表，且区域填写完整！")

        mapping = [{'src': self.tree_t1.item(i, 'values')[1], 'tgt': self.tree_t1.item(i, 'values')[2]} for i in
                   self.tree_t1.get_children()]
        if not mapping: return messagebox.showwarning("警告", "映射列表为空！")

        self.set_running_state(True)
        threading.Thread(target=self.run_t1_worker, args=(self.source_dir.get(), self.target_dir.get(), mapping, rules),
                         daemon=True).start()

    def run_t1_worker(self, src, tgt, mapping, rules):
        ExcelMigrator(src, tgt, mapping, rules, self.log_queue, self.progress_queue).run()
        self.set_running_state(False)

    # ---------------- Tab 2 逻辑 ----------------
    def refresh_mapping_t2(self):
        if self.is_running: return
        src_file, tgt_dir = self.t2_src_file.get(), self.t2_tgt_dir.get()
        if not os.path.isfile(src_file) or not os.path.isdir(tgt_dir):
            return messagebox.showwarning("警告", "请先正确选择源文件和目标文件夹！")

        self.set_running_state(True, disable_buttons=[self.btn_refresh_t2, self.btn_start_t2, self.btn_refresh_t1,
                                                      self.btn_start_t1])
        threading.Thread(target=self.run_t2_refresh_worker,
                         args=(src_file, self.t2_src_sheet.get(), self.t2_src_start.get().strip(), tgt_dir),
                         daemon=True).start()

    def run_t2_refresh_worker(self, src_file, src_sheet, src_start, tgt_dir):
        ColumnDistributor.read_source_column(src_file, src_sheet, src_start, tgt_dir, self.log_queue,
                                             self.tab2_mapping_queue)
        self.set_running_state(False, enable_buttons=[self.btn_refresh_t2, self.btn_start_t2, self.btn_refresh_t1,
                                                      self.btn_start_t1])

    def start_migration_t2(self):
        if self.is_running: return
        tgt_sheet, tgt_cell = self.t2_tgt_sheet.get(), self.t2_tgt_cell.get().strip()
        if not tgt_sheet or not tgt_cell: return messagebox.showwarning("警告",
                                                                        "请确保已获取并选择目标工作表，且单元格填写完整！")

        mapping = [{'value': self.tree_t2.item(i, 'values')[1], 'tgt': self.tree_t2.item(i, 'values')[2]} for i in
                   self.tree_t2.get_children()]
        if not mapping: return messagebox.showwarning("警告", "映射列表为空，请先读取源列！")

        self.set_running_state(True)
        threading.Thread(target=self.run_t2_distribute_worker,
                         args=(self.t2_tgt_dir.get(), tgt_sheet, tgt_cell, mapping), daemon=True).start()

    def run_t2_distribute_worker(self, tgt_dir, tgt_sheet, tgt_cell, mapping):
        ColumnDistributor.distribute_data(tgt_dir, tgt_sheet, tgt_cell, mapping, self.log_queue, self.progress_queue)
        self.set_running_state(False)

    # ---------------- 状态与队列控制 ----------------
    def set_running_state(self, is_running, disable_buttons=None, enable_buttons=None):
        self.is_running = is_running
        if is_running:
            self.progress["value"] = 0
            self.log_text.config(state="normal");
            self.log_text.delete(1.0, tk.END);
            self.log_text.config(state="disabled")
            btns = disable_buttons or [self.btn_start_t1, self.btn_refresh_t1, self.btn_start_t2, self.btn_refresh_t2]
            for btn in btns: btn.config(state="disabled")
        else:
            btns = enable_buttons or [self.btn_start_t1, self.btn_refresh_t1, self.btn_start_t2, self.btn_refresh_t2]
            for btn in btns: btn.config(state="normal")
            if not self.is_running:
                self.root.after(0, lambda: messagebox.showinfo("完成", "当前任务执行完毕！"))

    def process_queues(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

        while not self.progress_queue.empty():
            self.progress["value"] = self.progress_queue.get()

        while not self.tab2_mapping_queue.empty():
            mapping = self.tab2_mapping_queue.get()
            self.clear_mapping(self.tree_t2)
            for i, item in enumerate(mapping):
                self.tree_t2.insert("", "end", values=(i + 1, item['value'], item['tgt']))

        self.root.after(100, self.process_queues)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    elif 'clam' in style.theme_names():
        style.theme_use('clam')
    app = App(root)
    root.mainloop()
