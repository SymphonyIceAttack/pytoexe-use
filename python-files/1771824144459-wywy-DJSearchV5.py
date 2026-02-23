import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import importlib
import datetime


class DJSearchV5(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJSearch V5")
        self.geometry("1000x700")
        self.resizable(True, True)

        # 设置全局字体为微软雅黑
        self.option_add("*Font", "微软雅黑 10")

        # 车型数据库存储，键是车型名，值是数据库模块
        self.car_type_dbs = {}
        # 加载初始车型数据库
        self.load_initial_dbs()

        # 创建顶部按钮框架，避免按钮被标签页遮挡
        self.top_frame = ttk.Frame(self)
        self.top_frame.pack(side="top", fill="x", padx=10, pady=5)
        self.top_frame.configure(height=60)
        self.top_frame.grid_propagate(False)

        # 创建右上角功能按钮
        self.create_top_buttons()

        # 创建标签页容器
        self.create_notebook()

    def create_top_buttons(self):
        # 导入车型数据库按钮
        import_btn = ttk.Button(self, text="导入车型数据库", command=self.import_car_db)
        import_btn.place(relx=0.85, rely=0.02, anchor="ne")

        # 关于按钮
        about_btn = ttk.Button(self, text="关于", command=self.show_about)
        about_btn.place(relx=0.95, rely=0.02, anchor="ne")

    def show_about(self):
        """显示关于信息弹窗"""
        messagebox.showinfo("关于", "DJSearch V5\n作者：zttcraviation\n严禁复制传播")

    def import_car_db(self):
        """导入外部车型数据库文件"""
        file_path = filedialog.askopenfilename(
            title="选择车型数据库文件",
            filetypes=[("Python文件", "*.py")],
            initialdir=os.getcwd()
        )
        if not file_path:
            return

        # 处理模块导入
        file_name = os.path.basename(file_path)
        module_name = os.path.splitext(file_name)[0]
        try:
            # 添加文件路径到系统路径
            import sys
            sys.path.append(os.path.dirname(file_path))
            # 导入模块
            db_module = importlib.import_module(module_name)
            # 验证数据库模块有效性
            if hasattr(db_module, "car_type") and hasattr(db_module, "get_train_data"):
                self.car_type_dbs[db_module.car_type] = db_module
                self.update_car_type_combobox()
                messagebox.showinfo("导入成功", f"已成功导入车型数据库：{db_module.car_type}")
            else:
                messagebox.showerror("导入失败", "该文件不是有效的车型数据库，请确认文件包含car_type和get_train_data属性")
        except Exception as e:
            messagebox.showerror("导入错误", f"导入数据库时发生错误：{str(e)}")

    def load_initial_dbs(self):
        """加载初始车型数据库"""
        try:
            import crh2c2150
            if hasattr(crh2c2150, "car_type") and hasattr(crh2c2150, "get_train_data"):
                self.car_type_dbs[crh2c2150.car_type] = crh2c2150
        except ImportError:
            messagebox.showwarning("提示", "未找到初始车型数据库crh2c2150.py，请确保该文件与主程序在同一目录")

    def update_car_type_combobox(self):
        """更新车型查询的下拉列表选项"""
        car_types = list(self.car_type_dbs.keys())
        self.car_type_combobox["values"] = car_types
        if car_types:
            self.car_type_combobox.current(0)

    def create_notebook(self):
        """创建功能标签页"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 车次查询标签页
        self.train_query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.train_query_frame, text="车次查询")
        self.create_train_query_ui()

        # 站段查询标签页
        self.station_query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.station_query_frame, text="站段查询")
        self.create_station_query_ui()

        # 车型查询标签页
        self.car_type_query_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.car_type_query_frame, text="车型查询")
        self.create_car_type_query_ui()

    def create_train_query_ui(self):
        """创建车次查询界面"""
        # 车次输入区域
        ttk.Label(self.train_query_frame, text="动检车次号：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.train_id_entry = ttk.Entry(self.train_query_frame, width=30)
        self.train_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        # 查询按钮
        query_btn = ttk.Button(self.train_query_frame, text="查询", command=self.query_train)
        query_btn.grid(row=0, column=2, padx=5, pady=5)

        # 结果显示区域
        ttk.Label(self.train_query_frame, text="查询结果：").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.train_result_text = tk.Text(self.train_query_frame, width=120, height=30, font=("微软雅黑", 10))
        self.train_result_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # 滚动条
        scrollbar = ttk.Scrollbar(self.train_query_frame, orient="vertical", command=self.train_result_text.yview)
        scrollbar.grid(row=2, column=3, sticky="ns")
        self.train_result_text.configure(yscrollcommand=scrollbar.set)

        # 配置网格权重
        self.train_query_frame.grid_rowconfigure(2, weight=1)
        self.train_query_frame.grid_columnconfigure(1, weight=1)

    def query_train(self):
        """执行车次查询"""
        train_id = self.train_id_entry.get().strip().upper()
        if not train_id:
            messagebox.showwarning("提示", "请输入要查询的车次号")
            return

        self.train_result_text.delete(1.0, tk.END)
        # 收集所有数据库中的数据
        all_train_data = []
        for db in self.car_type_dbs.values():
            db_data = db.get_train_data()
            # 遍历数据库中的所有车次数据，提取每个车次的详细信息
            for train_info in db_data.values():
                all_train_data.append(train_info)

        # 匹配车次数据
        matched_trains = []
        same_train_ids = []

        # 处理车次格式，拆分同车次情况
        def parse_train_id(train_str):
            train_str = train_str.upper().strip()
            if "/" in train_str:
                parts = train_str.split("/")
                if len(parts) == 2:
                    part1 = parts[0].strip()
                    part2 = parts[1].strip()
                    # 处理DJxxx/x格式，如DJ71/4指代DJ71和DJ74，DJ462/59指代DJ462和DJ459
                    if part1.startswith("DJ") and part1[2:].isdigit() and part2.isdigit():
                        prefix = part1[:2]  # 提取DJ前缀
                        number_part = part1[2:]  # 提取数字部分
                        if len(part2) <= len(number_part):
                            # 替换最后len(part2)位数字，生成同车次
                            new_number = number_part[:-len(part2)] + part2
                            full_part2 = prefix + new_number
                            return [part1, full_part2]
                        elif len(part2) > len(number_part):
                            # 如果后面数字更长，直接使用后面的数字
                            full_part2 = prefix + part2
                            return [part1, full_part2]
                # 如果不符合特殊格式，直接返回拆分后的部分
                return [p.strip() for p in parts]
            return [train_str]

        # 遍历所有数据匹配车次
        for train_data in all_train_data:
            data_train_ids = parse_train_id(train_data["train_no"])
            # 检查输入车次是否匹配
            if train_id in data_train_ids:
                matched_trains.append(train_data)
                # 收集同车次的其他车次号
                for tid in data_train_ids:
                    if tid != train_id and tid not in same_train_ids:
                        same_train_ids.append(tid)


        # 去重同车次列表
        same_train_ids = list(set(same_train_ids))

        if not matched_trains:
            self.train_result_text.insert(tk.END, f"未找到车次【{train_id}】的相关信息")
            return

        # 显示查询结果
        self.train_result_text.insert(tk.END, f"查询到车次【{train_id}】的相关信息如下：\n")
        if same_train_ids:
            self.train_result_text.insert(tk.END, f"同车次：{', '.join(same_train_ids)}\n")
        self.train_result_text.insert(tk.END, "-" * 100 + "\n")

        for train in matched_trains:
            # 标注回送车次
            return_tag = "（回送车次）" if train["train_no"].startswith("0J") else ""
            self.train_result_text.insert(tk.END, f"车次：{train['train_no']} {return_tag}\n")
            self.train_result_text.insert(tk.END, f"车型：{train['model']}\n")
            # 提取日数并添加当前月份前缀，标注预测
            train_day = int(train["start_date"].split("日")[0])
            current_month = datetime.datetime.now().month
            self.train_result_text.insert(tk.END, f"出发日期：{current_month}月{train_day}日（预测）\n")
            self.train_result_text.insert(tk.END, f"始发站：{train['start_station']}\n")
            self.train_result_text.insert(tk.END, f"终到站：{train['end_station']}\n")
            # 格式化途径站显示
            self.train_result_text.insert(tk.END, f"途径站：{', '.join(train['pass_stations'])}\n")
            self.train_result_text.insert(tk.END, "-" * 100 + "\n")

    def create_station_query_ui(self):
        """创建站段查询界面"""
        # 站段输入区域
        ttk.Label(self.station_query_frame, text="站段名：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.station_entry = ttk.Entry(self.station_query_frame, width=30)
        self.station_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")

        # 日期输入区域
        ttk.Label(self.station_query_frame, text="查询日数（如22）：").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.station_date_entry = ttk.Entry(self.station_query_frame, width=30)
        self.station_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        # 查询按钮
        query_btn = ttk.Button(self.station_query_frame, text="查询", command=self.query_station)
        query_btn.grid(row=1, column=2, padx=5, pady=5)

        # 结果显示区域
        ttk.Label(self.station_query_frame, text="查询结果：").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        self.station_result_text = tk.Text(self.station_query_frame, width=120, height=30, font=("微软雅黑", 10))
        self.station_result_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # 滚动条
        scrollbar = ttk.Scrollbar(self.station_query_frame, orient="vertical", command=self.station_result_text.yview)
        scrollbar.grid(row=3, column=3, sticky="ns")
        self.station_result_text.configure(yscrollcommand=scrollbar.set)

        # 配置网格权重
        self.station_query_frame.grid_rowconfigure(3, weight=1)
        self.station_query_frame.grid_columnconfigure(1, weight=1)

    def query_station(self):
        """执行站段查询"""
        station_name = self.station_entry.get().strip()
        day_str = self.station_date_entry.get().strip()

        if not station_name or not day_str:
            messagebox.showwarning("提示", "请输入站段名和查询日数")
            return

        # 验证日数输入
        try:
            query_day = int(day_str)
            if query_day < 1 or query_day > 31:
                messagebox.showwarning("提示", "日数必须在1-31之间")
                return
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的数字日数")
            return

        # 获取当前年月，验证日期有效性
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        try:
            target_date = datetime.date(current_year, current_month, query_day)
        except ValueError:
            messagebox.showwarning("提示", f"{current_year}年{current_month}月没有{query_day}日")
            return

        # 计算查询日期范围：前后10天
        start_date = target_date - datetime.timedelta(days=10)
        end_date = target_date + datetime.timedelta(days=10)

        # 判断是否为周末
        weekday = target_date.isoweekday()  # 1=周一，7=周日
        is_weekend = weekday in [6, 7]  # 周六、周日为周末

        self.station_result_text.delete(1.0, tk.END)
        self.station_result_text.insert(tk.END, f"查询站段：{station_name}\n")
        min_day = query_day - 10
        max_day = query_day + 10
        self.station_result_text.insert(tk.END, f"查询日数范围：{min_day}日 至 {max_day}日（跨月自动循环）\n")
        if is_weekend:
            # 计算相邻工作日的日数
            prev_workday_day = query_day
            while True:
                prev_workday_day -= 1
                if prev_workday_day < 1:
                    prev_workday_day = 31
                # 判断该日数对应的星期几（假设数据库里的日期是6月，用2026年6月来计算星期）
                test_date = datetime.date(2026, 6, prev_workday_day)
                if test_date.isoweekday() <=5:
                    break
            next_workday_day = query_day
            while True:
                next_workday_day += 1
                if next_workday_day >31:
                    next_workday_day =1
                test_date = datetime.date(2026, 6, next_workday_day)
                if test_date.isoweekday() <=5:
                    break
            self.station_result_text.insert(tk.END, f"注：该日数为周末，同时显示相邻工作日【{prev_workday_day}日、{next_workday_day}日】的计划\n")
        self.station_result_text.insert(tk.END, "-" * 120 + "\n")

        # 收集所有数据库数据
        all_train_data = []
        for db in self.car_type_dbs.values():
            db_data = db.get_train_data()
            for train_info in db_data.values():
                all_train_data.append(train_info)

        # 筛选符合条件的数据
        matched_data = []
        for train in all_train_data:
            # 解析车次日期
            train_date_str = train["start_date"]
            if "日" in train_date_str:
                try:
                    train_day = int(train_date_str.split("日")[0])
                except ValueError:
                    continue

                # 检查日数是否在查询范围内（不考虑月份，处理跨月情况）
                min_day = query_day - 10
                max_day = query_day + 10
                matched = False
                
                # 处理正常范围
                if min_day <= train_day <= max_day:
                    matched = True
                else:
                    # 处理跨月的情况，比如查询日是5日，min_day是-5，对应26日到31日
                    if min_day <= 0:
                        if (31 + min_day <= train_day <= 31) or (1 <= train_day <= max_day):
                            matched = True
                    # 处理超过31日的情况，比如查询日是30日，max_day是40，对应1日到9日
                    elif max_day > 31:
                        if (min_day <= train_day <= 31) or (1 <= train_day <= max_day - 31):
                            matched = True

                if matched:
                    # 检查是否经过目标站段
                    for station_name_sched, arrive, depart in train["station_schedule"]:
                        if station_name_sched == station_name:
                            matched_data.append({
                                "train_id": train["train_no"],
                                "car_type": train["model"],
                                "date": train_date_str,
                                "arrive_time": arrive,
                                "depart_time": depart,
                                "line": train["detect_line"]
                            })
                            break

        # 按日数排序
        matched_data.sort(key=lambda x: int(x["date"].split("日")[0]))

        if not matched_data:
            self.station_result_text.insert(tk.END, "未找到该站段在指定日期范围内的动检计划")
            return

        # 显示查询结果
        for item in matched_data:
            # 提取日数并添加当前月份前缀，标注预测
            train_day = int(item["date"].split("日")[0])
            current_month = datetime.datetime.now().month
            self.station_result_text.insert(tk.END, f"日期：{current_month}月{train_day}日（预测）\n")
            self.station_result_text.insert(tk.END, f"车次：{item['train_id']}\n")
            self.station_result_text.insert(tk.END, f"车型：{item['car_type']}\n")
            self.station_result_text.insert(tk.END, f"到站时间：{item['arrive_time'] if item['arrive_time'] else '无'}\n")
            self.station_result_text.insert(tk.END, f"开车时间：{item['depart_time'] if item['depart_time'] else '无'}\n")
            self.station_result_text.insert(tk.END, f"检测线路：{item['line']}\n")
            self.station_result_text.insert(tk.END, "-" * 120 + "\n")

        # 显示周末相邻工作日的额外计划
        if is_weekend:
            self.station_result_text.insert(tk.END, "\n相邻工作日计划：\n")
            self.station_result_text.insert(tk.END, "-" * 120 + "\n")
            for workday_day in [prev_workday_day, next_workday_day]:
                for train in all_train_data:
                    train_date_str = train["start_date"]
                    if "日" in train_date_str:
                        try:
                            train_day = int(train_date_str.split("日")[0])
                        except ValueError:
                            continue
                        # 只比较日数，不考虑月份
                        if train_day == workday_day:
                            for station_name_sched, arrive, depart in train["station_schedule"]:
                                if station_name_sched == station_name:
                                    # 显示当前月份的该日数，标注预测
                                    current_month = datetime.datetime.now().month
                                    self.station_result_text.insert(tk.END, f"日期：{current_month}月{workday_day}日（预测）\n")
                                    self.station_result_text.insert(tk.END, f"车次：{train['train_no']}\n")
                                    self.station_result_text.insert(tk.END, f"车型：{train['model']}\n")
                                    self.station_result_text.insert(tk.END, f"到站时间：{arrive if arrive else '无'}\n")
                                    self.station_result_text.insert(tk.END, f"开车时间：{depart if depart else '无'}\n")
                                    self.station_result_text.insert(tk.END, f"检测线路：{train['detect_line']}\n")
                                    self.station_result_text.insert(tk.END, "-" * 120 + "\n")
                                    break

    def create_car_type_query_ui(self):
        """创建车型查询界面"""
        # 车型选择区域
        ttk.Label(self.car_type_query_frame, text="选择车型：").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.car_type_combobox = ttk.Combobox(self.car_type_query_frame, width=28, state="readonly")
        self.car_type_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.update_car_type_combobox()

        # 日期输入区域
        ttk.Label(self.car_type_query_frame, text="查询日数（如22）：").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.car_type_date_entry = ttk.Entry(self.car_type_query_frame, width=30)
        self.car_type_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        # 查询按钮
        query_btn = ttk.Button(self.car_type_query_frame, text="查询", command=self.query_car_type)
        query_btn.grid(row=1, column=2, padx=5, pady=5)

        # 结果显示区域
        ttk.Label(self.car_type_query_frame, text="查询结果：").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        self.car_type_result_text = tk.Text(self.car_type_query_frame, width=120, height=30, font=("微软雅黑", 10))
        self.car_type_result_text.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        # 滚动条
        scrollbar = ttk.Scrollbar(self.car_type_query_frame, orient="vertical", command=self.car_type_result_text.yview)
        scrollbar.grid(row=3, column=3, sticky="ns")
        self.car_type_result_text.configure(yscrollcommand=scrollbar.set)

        # 配置网格权重
        self.car_type_query_frame.grid_rowconfigure(3, weight=1)
        self.car_type_query_frame.grid_columnconfigure(1, weight=1)

    def query_car_type(self):
        """执行车型查询"""
        selected_car_type = self.car_type_combobox.get()
        day_str = self.car_type_date_entry.get().strip()

        if not selected_car_type or not day_str:
            messagebox.showwarning("提示", "请选择车型并输入查询日数")
            return

        # 验证日数输入
        try:
            query_day = int(day_str)
            if query_day < 1 or query_day > 31:
                messagebox.showwarning("提示", "日数必须在1-31之间")
                return
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的数字日数")
            return

        # 获取当前年月，验证日期有效性
        now = datetime.datetime.now()
        current_year = now.year
        current_month = now.month

        try:
            target_date = datetime.date(current_year, current_month, query_day)
        except ValueError:
            messagebox.showwarning("提示", f"{current_year}年{current_month}月没有{query_day}日")
            return

        # 计算查询日期范围：前后10天
        start_date = target_date - datetime.timedelta(days=10)
        end_date = target_date + datetime.timedelta(days=10)

        self.car_type_result_text.delete(1.0, tk.END)
        self.car_type_result_text.insert(tk.END, f"查询车型：{selected_car_type}\n")
        min_day = query_day -10
        max_day = query_day +10
        self.car_type_result_text.insert(tk.END, f"查询日数范围：{min_day}日 至 {max_day}日（跨月自动循环）\n")
        self.car_type_result_text.insert(tk.END, "-" * 120 + "\n")

        # 获取对应车型的数据库
        if selected_car_type not in self.car_type_dbs:
            messagebox.showwarning("提示", "未找到该车型的数据库")
            return

        car_db = self.car_type_dbs[selected_car_type]
        db_data = car_db.get_train_data()
        train_data = []
        # 提取该车型的所有车次信息
        for train_info in db_data.values():
            train_data.append(train_info)

        # 筛选符合条件的数据
        matched_data = []
        for train in train_data:
            # 解析车次日期
            train_date_str = train["start_date"]
            if "日" in train_date_str:
                try:
                    train_day = int(train_date_str.split("日")[0])
                except ValueError:
                    continue

                # 检查日数是否在查询范围内（不考虑月份，处理跨月情况）
                min_day = query_day - 10
                max_day = query_day + 10
                matched = False
                
                # 处理正常范围
                if min_day <= train_day <= max_day:
                    matched = True
                else:
                    # 处理跨月的情况，比如查询日是5日，min_day是-5，对应26日到31日
                    if min_day <= 0:
                        if (31 + min_day <= train_day <= 31) or (1 <= train_day <= max_day):
                            matched = True
                    # 处理超过31日的情况，比如查询日是30日，max_day是40，对应1日到9日
                    elif max_day > 31:
                        if (min_day <= train_day <= 31) or (1 <= train_day <= max_day - 31):
                            matched = True

                if matched:
                    matched_data.append(train)

        # 按日数排序
        def get_train_day(train):
            date_str = train["start_date"]
            day = int(date_str.split("日")[0])
            return day

        matched_data.sort(key=get_train_day)

        if not matched_data:
            self.car_type_result_text.insert(tk.END, "未找到该车型在指定日期范围内的动检计划")
            return

        # 显示查询结果
        for train in matched_data:
            # 提取日数并添加当前月份前缀，标注预测
            train_day = int(train["start_date"].split("日")[0])
            current_month = datetime.datetime.now().month
            self.car_type_result_text.insert(tk.END, f"日期：{current_month}月{train_day}日（预测）\n")
            self.car_type_result_text.insert(tk.END, f"车次：{train['train_no']}\n")
            self.car_type_result_text.insert(tk.END, f"始发站：{train['start_station']}\n")
            self.car_type_result_text.insert(tk.END, f"终到站：{train['end_station']}\n")
            self.car_type_result_text.insert(tk.END, f"检测线路：{train['detect_line']}\n")
            # 格式化途径站显示
            self.car_type_result_text.insert(tk.END, f"途径站段：{', '.join(train['pass_stations'])}\n")
            self.car_type_result_text.insert(tk.END, "-" * 120 + "\n")


if __name__ == "__main__":
    app = DJSearchV5()
    app.mainloop()