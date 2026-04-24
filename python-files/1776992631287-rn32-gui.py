import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import math
from datetime import datetime
import csv
import numpy as np
from scipy.spatial import KDTree


class HoleSpatialIndex:
    """
    气膜孔空间索引结构
    存储孔编号、中心位置、包络盒，并基于KDTree实现快速查询
    """

    def __init__(self):
        self.hole_records = []
        self.kdtree = None
        self.points = None

    def build(self, hole_results):
        self.hole_records = hole_results[:]

        if not hole_results:
            self.points = None
            self.kdtree = None
            return

        self.points = np.array([item["center"] for item in hole_results], dtype=np.float64)
        self.kdtree = KDTree(self.points)

    def query_nearest(self, point, radius):
        if self.kdtree is None:
            return []
        idxs = self.kdtree.query_ball_point(point, radius)
        return [self.hole_records[i] for i in idxs]

    def query_in_box(self, xmin, xmax, ymin, ymax, zmin=-np.inf, zmax=np.inf):
        result = []
        for item in self.hole_records:
            x, y, z = item["center"]
            if xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax:
                result.append(item)
        return result


class BladeMeasurementSystem:
    """
    按论文第5章的软件测量流程做的模拟系统：
    Job读取 -> 位姿采集 -> 超分辨率/深度估计 -> 点云融合 -> 孔识别 -> 参数提取 -> 排序编号 -> KD树索引 -> 报告输出
    """

    def __init__(self):
        self.is_running = False
        self.is_paused = False
        self.cancel_requested = False

        self.platform_pose = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.camera_status = "空闲"
        self.queue_length = 0
        self.current_stage = "待机"
        self.current_pose_index = 0
        self.total_pose_count = 0

        self.measure_results = []
        self.failure_events = []
        self.logs = []

        self.hole_spatial_index = HoleSpatialIndex()

    def reset_runtime_state(self):
        self.is_running = False
        self.is_paused = False
        self.cancel_requested = False
        self.platform_pose = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.camera_status = "空闲"
        self.queue_length = 0
        self.current_stage = "待机"
        self.current_pose_index = 0
        self.total_pose_count = 0
        self.measure_results = []
        self.failure_events = []
        self.logs = []
        self.hole_spatial_index = HoleSpatialIndex()

    def pause(self):
        if self.is_running:
            self.is_paused = True

    def resume(self):
        if self.is_running:
            self.is_paused = False

    def cancel(self):
        if self.is_running:
            self.cancel_requested = True

    def _wait_if_paused(self):
        while self.is_paused and not self.cancel_requested:
            time.sleep(0.2)

    def _log(self, callback, text):
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {text}"
        self.logs.append(line)
        if callback:
            callback("log", line)

    def _update_state(self, callback, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if callback:
            callback("state", kwargs)

    def _generate_unsorted_hole_results(self, hole_count):
        """
        生成未编号、未排序的模拟孔结果
        """
        results = []
        for _ in range(hole_count):
            cx = round(random.uniform(5.0, 45.0), 3)
            cy = round(random.uniform(10.0, 30.0), 3)
            cz = round(random.uniform(12.0, 62.0), 3)

            diameter = round(random.uniform(0.55, 1.45), 3)

            vx = round(random.uniform(-1.0, 1.0), 4)
            vy = round(random.uniform(-1.0, 1.0), 4)
            vz = round(random.uniform(0.1, 1.0), 4)
            norm = math.sqrt(vx * vx + vy * vy + vz * vz)
            vx, vy, vz = round(vx / norm, 4), round(vy / norm, 4), round(vz / norm, 4)

            tilt = round(math.degrees(math.acos(max(min(vz, 1.0), -1.0))), 3)
            residual = round(random.uniform(0.002, 0.035), 4)
            confidence = round(random.uniform(0.86, 0.99), 4)

            half_size = diameter / 2.0
            bbox = {
                "xmin": round(cx - half_size, 3),
                "xmax": round(cx + half_size, 3),
                "ymin": round(cy - half_size, 3),
                "ymax": round(cy + half_size, 3),
                "zmin": round(cz - half_size * 0.3, 3),
                "zmax": round(cz + half_size * 0.3, 3),
            }

            results.append({
                "hole_id": None,
                "center": (cx, cy, cz),
                "diameter": diameter,
                "axis": (vx, vy, vz),
                "tilt": tilt,
                "residual": residual,
                "confidence": confidence,
                "bbox": bbox
            })
        return results

    def _sort_and_number_holes(self, hole_results, x_precision=6):
        """
        按X坐标优先、Y坐标次之排序并编号
        """
        sorted_results = sorted(
            hole_results,
            key=lambda item: (round(item["center"][0], x_precision), round(item["center"][1], x_precision))
        )

        for idx, item in enumerate(sorted_results, start=1):
            item["hole_id"] = f"H-{idx:03d}"

        return sorted_results

    def query_holes_near_position(self, x, y, z, radius):
        return self.hole_spatial_index.query_nearest((x, y, z), radius)

    def query_holes_in_region(self, xmin, xmax, ymin, ymax, zmin=-9999, zmax=9999):
        return self.hole_spatial_index.query_in_box(xmin, xmax, ymin, ymax, zmin, zmax)

    def run_job(self, job, callback=None):
        self.reset_runtime_state()
        self.is_running = True

        try:
            pose_list = job["pose_list"]
            hole_count = job["hole_count"]
            self.total_pose_count = len(pose_list)

            self._log(callback, f"读取任务对象 Job：叶片ID={job['blade_id']}，批次={job['batch_id']}，参数包={job['param_pack']}")
            self._update_state(callback, current_stage="加载任务")
            time.sleep(0.4)

            self._log(callback, "根据参数包版本加载标定参数、算法参数与模型权重")
            self._update_state(callback, current_stage="初始化算法")
            self.queue_length = len(pose_list)
            if callback:
                callback("state", {"queue_length": self.queue_length})
            time.sleep(0.5)

            for idx, pose in enumerate(pose_list, start=1):
                if self.cancel_requested:
                    self._log(callback, "任务已取消")
                    self._update_state(callback, current_stage="已取消", camera_status="空闲")
                    return "cancelled"

                self._wait_if_paused()

                self.current_pose_index = idx
                self.queue_length = len(pose_list) - idx
                self._update_state(
                    callback,
                    current_stage="平台运动",
                    platform_pose=pose,
                    current_pose_index=idx,
                    total_pose_count=len(pose_list),
                    queue_length=self.queue_length
                )
                self._log(callback, f"位姿 {idx}/{len(pose_list)}：平台移动到目标位姿 {pose}")
                time.sleep(0.6)

                self._wait_if_paused()
                self._update_state(callback, current_stage="等待稳定")
                self._log(callback, "等待平台稳定：速度=0，振动幅值低于阈值")
                time.sleep(0.4)

                self._wait_if_paused()
                self._update_state(callback, current_stage="光场采集", camera_status="采集中")
                self._log(callback, "配置曝光参数并触发相机采集光场图像")
                time.sleep(0.5)

                if random.random() < 0.08:
                    event = {
                        "pose_index": idx,
                        "reason": "图像质量评分过低，触发补拍",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.failure_events.append(event)
                    self._log(callback, f"失败事件：位姿 {idx} 补拍，原因：{event['reason']}")
                    time.sleep(0.3)

                self._update_state(callback, camera_status="空闲")

            self._wait_if_paused()
            self._update_state(callback, current_stage="超分辨率重建")
            self._log(callback, "执行光场图像超分辨率重建")
            time.sleep(0.7)

            self._wait_if_paused()
            self._update_state(callback, current_stage="深度估计")
            self._log(callback, "执行深度估计，生成深度图与置信度图")
            time.sleep(0.8)

            self._wait_if_paused()
            self._update_state(callback, current_stage="点云融合")
            self._log(callback, "将各位姿点云统一到平台坐标系并完成配准与滤波")
            time.sleep(0.8)

            self._wait_if_paused()
            self._update_state(callback, current_stage="孔识别与参数拟合")
            self._log(callback, "执行曲率分析、候选区域筛选、边缘提取与椭圆拟合")
            time.sleep(1.0)

            raw_results = self._generate_unsorted_hole_results(hole_count)
            self.measure_results = self._sort_and_number_holes(raw_results)
            self.hole_spatial_index.build(self.measure_results)

            self._log(callback, f"孔参数提取完成，共识别 {len(self.measure_results)} 个气膜孔")
            self._log(callback, "已按孔中心X/Y坐标完成排序编号")
            self._log(callback, "已建立孔编号、中心位置、包络盒的KD树空间索引")

            self._wait_if_paused()
            self._update_state(callback, current_stage="生成报告")
            self._log(callback, "生成孔级结果表、超差清单、可视化截图与版本信息")
            time.sleep(0.6)

            self._update_state(callback, current_stage="完成", camera_status="空闲")
            self._log(callback, "任务执行完成")
            return "finished"

        finally:
            self.is_running = False


class BladeMeasurementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("叶片气膜孔测量系统")
        self.root.geometry("1750x940")
        self.root.minsize(1400, 820)

        self.system = BladeMeasurementSystem()
        self.jobs = []
        self.selected_job_id = None

        self._build_style()
        self._build_demo_jobs()
        self._build_ui()
        self._refresh_job_table()
        self._refresh_status_panel()
        self._set_status("就绪")

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Title.TLabel", font=("Microsoft YaHei", 15, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Accent.TButton", font=("Microsoft YaHei", 10))
        style.configure("Treeview", rowheight=28, font=("Consolas", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))

    def _build_demo_jobs(self):
        for i in range(1, 8):
            self.jobs.append({
                "job_id": f"JOB-2026-{i:03d}",
                "blade_id": f"BLD-{1000+i}",
                "batch_id": f"BATCH-{(i-1)//2+1:02d}",
                "status": random.choice(["待执行", "已完成", "待执行", "暂停"]),
                "created_time": f"2026-03-{10+i:02d} 09:{10+i:02d}",
                "param_pack": f"PKG-v1.{i}",
                "hole_count": random.randint(190, 210),
                "pose_list": [
                    [round(random.uniform(0, 100), 2),
                     round(random.uniform(0, 100), 2),
                     round(random.uniform(0, 100), 2),
                     round(random.uniform(-20, 20), 2),
                     round(random.uniform(-20, 20), 2)]
                    for _ in range(random.randint(6, 10))
                ]
            })

    def _build_ui(self):
        self._build_topbar()
        self._build_filterbar()
        self._build_main_panes()
        self._build_statusbar()

    def _build_topbar(self):
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="基于光场成像的叶片气膜孔三维测量系统", style="Title.TLabel").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="新建任务", command=self._create_job, style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="查看详情", command=self._show_job_detail).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="启动任务", command=self._start_selected_job).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="暂停任务", command=self._pause_job).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="继续任务", command=self._resume_job).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="取消任务", command=self._cancel_job).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="导出CSV", command=self._export_csv).pack(side=tk.LEFT, padx=4)

    def _build_filterbar(self):
        bar = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(bar, text="状态筛选").pack(side=tk.LEFT, padx=(0, 6))
        self.status_filter = ttk.Combobox(
            bar,
            values=["全部", "待执行", "执行中", "暂停", "已完成", "已取消"],
            width=10,
            state="readonly"
        )
        self.status_filter.set("全部")
        self.status_filter.pack(side=tk.LEFT)
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_job_table())

        ttk.Label(bar, text="叶片ID").pack(side=tk.LEFT, padx=(12, 6))
        self.blade_filter_var = tk.StringVar()
        blade_entry = ttk.Entry(bar, textvariable=self.blade_filter_var, width=18)
        blade_entry.pack(side=tk.LEFT)
        blade_entry.bind("<KeyRelease>", lambda e: self._refresh_job_table())

        ttk.Label(bar, text="排序").pack(side=tk.LEFT, padx=(12, 6))
        self.sort_by = ttk.Combobox(
            bar,
            values=["创建时间", "叶片ID", "状态", "批次"],
            width=12,
            state="readonly"
        )
        self.sort_by.set("创建时间")
        self.sort_by.pack(side=tk.LEFT)
        self.sort_by.bind("<<ComboboxSelected>>", lambda e: self._refresh_job_table())

        ttk.Button(bar, text="刷新", command=self._refresh_job_table).pack(side=tk.LEFT, padx=(12, 0))

    def _build_main_panes(self):
        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self.left_panel = ttk.Frame(self.paned)
        self.center_panel = ttk.Frame(self.paned)
        self.right_panel = ttk.Frame(self.paned)

        self.paned.add(self.left_panel, weight=3)
        self.paned.add(self.center_panel, weight=6)
        self.paned.add(self.right_panel, weight=4)

        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        task_frame = ttk.LabelFrame(self.left_panel, text="任务管理区域", style="Section.TLabelframe", padding=8)
        task_frame.pack(fill=tk.BOTH, expand=True)

        info_frame = ttk.Frame(task_frame)
        info_frame.pack(fill=tk.X, pady=(0, 8))

        self.batch_info_var = tk.StringVar(value="批次信息：-")
        self.blade_info_var = tk.StringVar(value="叶片信息：-")
        self.progress_info_var = tk.StringVar(value="位姿进度：0 / 0")

        ttk.Label(info_frame, textvariable=self.batch_info_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.blade_info_var).pack(anchor="w")
        ttk.Label(info_frame, textvariable=self.progress_info_var).pack(anchor="w")

        columns = ("job_id", "blade_id", "batch_id", "status", "created_time")
        self.job_tree = ttk.Treeview(task_frame, columns=columns, show="headings")
        self.job_tree.heading("job_id", text="任务编号")
        self.job_tree.heading("blade_id", text="叶片ID")
        self.job_tree.heading("batch_id", text="批次")
        self.job_tree.heading("status", text="状态")
        self.job_tree.heading("created_time", text="创建时间")

        self.job_tree.column("job_id", width=120, anchor=tk.CENTER)
        self.job_tree.column("blade_id", width=100, anchor=tk.CENTER)
        self.job_tree.column("batch_id", width=80, anchor=tk.CENTER)
        self.job_tree.column("status", width=80, anchor=tk.CENTER)
        self.job_tree.column("created_time", width=130, anchor=tk.CENTER)

        self.job_tree.pack(fill=tk.BOTH, expand=True)
        self.job_tree.bind("<<TreeviewSelect>>", self._on_job_selected)

        y_scroll = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.job_tree.yview)
        self.job_tree.configure(yscrollcommand=y_scroll.set)
        y_scroll.place(relx=1.0, rely=0.18, relheight=0.79, anchor="ne")

    def _build_center_panel(self):
        param_frame = ttk.LabelFrame(self.center_panel, text="孔参数显示区域", style="Section.TLabelframe", padding=8)
        param_frame.pack(fill=tk.BOTH, expand=True)

        columns = (
            "hole_id", "center", "diameter", "axis", "bbox", "tilt", "residual", "confidence"
        )
        self.hole_tree = ttk.Treeview(param_frame, columns=columns, show="headings")

        headers = {
            "hole_id": "孔编号",
            "center": "中心位置",
            "diameter": "孔径(mm)",
            "axis": "孔轴方向",
            "bbox": "包络盒",
            "tilt": "倾角(°)",
            "residual": "拟合残差",
            "confidence": "置信度"
        }

        widths = {
            "hole_id": 90,
            "center": 175,
            "diameter": 90,
            "axis": 180,
            "bbox": 270,
            "tilt": 90,
            "residual": 100,
            "confidence": 95
        }

        for col in columns:
            self.hole_tree.heading(col, text=headers[col])
            self.hole_tree.column(col, width=widths[col], anchor=tk.CENTER)

        self.hole_tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=self.hole_tree.yview)
        self.hole_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0.08, relheight=0.58, anchor="ne")

        summary = ttk.Frame(param_frame)
        summary.pack(fill=tk.X, pady=(8, 8))

        self.result_count_var = tk.StringVar(value="识别孔数量：0")
        self.failure_count_var = tk.StringVar(value="失败事件：0")
        self.report_info_var = tk.StringVar(value="报告状态：未生成")

        ttk.Label(summary, textvariable=self.result_count_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(summary, textvariable=self.failure_count_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(summary, textvariable=self.report_info_var).pack(side=tk.LEFT, padx=8)

        query_frame = ttk.LabelFrame(param_frame, text="空间查询", padding=8)
        query_frame.pack(fill=tk.X, pady=(4, 0))

        row1 = ttk.Frame(query_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="X").pack(side=tk.LEFT)
        self.qx_var = tk.StringVar(value="50")
        ttk.Entry(row1, textvariable=self.qx_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Y").pack(side=tk.LEFT)
        self.qy_var = tk.StringVar(value="40")
        ttk.Entry(row1, textvariable=self.qy_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="Z").pack(side=tk.LEFT)
        self.qz_var = tk.StringVar(value="0")
        ttk.Entry(row1, textvariable=self.qz_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row1, text="半径").pack(side=tk.LEFT)
        self.radius_var = tk.StringVar(value="15")
        ttk.Entry(row1, textvariable=self.radius_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Button(row1, text="查询附近孔", command=self._query_nearby_holes).pack(side=tk.LEFT, padx=8)

        row2 = ttk.Frame(query_frame)
        row2.pack(fill=tk.X, pady=2)

        ttk.Label(row2, text="Xmin").pack(side=tk.LEFT)
        self.xmin_var = tk.StringVar(value="20")
        ttk.Entry(row2, textvariable=self.xmin_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row2, text="Xmax").pack(side=tk.LEFT)
        self.xmax_var = tk.StringVar(value="80")
        ttk.Entry(row2, textvariable=self.xmax_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row2, text="Ymin").pack(side=tk.LEFT)
        self.ymin_var = tk.StringVar(value="20")
        ttk.Entry(row2, textvariable=self.ymin_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(row2, text="Ymax").pack(side=tk.LEFT)
        self.ymax_var = tk.StringVar(value="60")
        ttk.Entry(row2, textvariable=self.ymax_var, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Button(row2, text="查询区域孔", command=self._query_region_holes).pack(side=tk.LEFT, padx=8)
        ttk.Button(row2, text="恢复全部结果", command=self._restore_all_results).pack(side=tk.LEFT, padx=8)

    def _build_right_panel(self):
        monitor_frame = ttk.LabelFrame(self.right_panel, text="系统状态监控区域", style="Section.TLabelframe", padding=8)
        monitor_frame.pack(fill=tk.BOTH, expand=True)

        basic_frame = ttk.LabelFrame(monitor_frame, text="实时状态", padding=8)
        basic_frame.pack(fill=tk.X, pady=(0, 8))

        self.platform_pose_var = tk.StringVar(value="平台位姿：X=0.00 Y=0.00 Z=0.00 A=0.00 B=0.00")
        self.camera_status_var = tk.StringVar(value="相机状态：空闲")
        self.queue_var = tk.StringVar(value="队列长度：0")
        self.stage_var = tk.StringVar(value="当前阶段：待机")

        ttk.Label(basic_frame, textvariable=self.platform_pose_var).pack(anchor="w", pady=2)
        ttk.Label(basic_frame, textvariable=self.camera_status_var).pack(anchor="w", pady=2)
        ttk.Label(basic_frame, textvariable=self.queue_var).pack(anchor="w", pady=2)
        ttk.Label(basic_frame, textvariable=self.stage_var).pack(anchor="w", pady=2)

        trace_frame = ttk.LabelFrame(monitor_frame, text="追溯记录摘要", padding=8)
        trace_frame.pack(fill=tk.X, pady=(0, 8))

        self.trace_var = tk.StringVar(
            value="参数包版本：-\n算法版本：sim-1.0\n模型版本：sim-1.0\n软件版本：gui-1.1"
        )
        ttk.Label(trace_frame, textvariable=self.trace_var, justify=tk.LEFT).pack(anchor="w")

        fail_frame = ttk.LabelFrame(monitor_frame, text="失败事件清单", padding=8)
        fail_frame.pack(fill=tk.X, pady=(0, 8))

        self.fail_listbox = tk.Listbox(fail_frame, height=6, font=("Consolas", 10))
        self.fail_listbox.pack(fill=tk.X, expand=False)

        log_frame = ttk.LabelFrame(monitor_frame, text="运行日志", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _build_statusbar(self):
        bottom = ttk.Frame(self.root, padding=(10, 6))
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="系统状态：就绪")
        ttk.Label(bottom, textvariable=self.status_var).pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(bottom, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))

    def _set_status(self, text):
        self.status_var.set(f"系统状态：{text}")
        self.root.update_idletasks()

    def _filtered_jobs(self):
        jobs = list(self.jobs)
        sf = self.status_filter.get()
        bf = self.blade_filter_var.get().strip().lower()
        sb = self.sort_by.get()

        if sf != "全部":
            jobs = [j for j in jobs if j["status"] == sf]

        if bf:
            jobs = [j for j in jobs if bf in j["blade_id"].lower()]

        if sb == "叶片ID":
            jobs.sort(key=lambda x: x["blade_id"])
        elif sb == "状态":
            jobs.sort(key=lambda x: x["status"])
        elif sb == "批次":
            jobs.sort(key=lambda x: x["batch_id"])
        else:
            jobs.sort(key=lambda x: x["created_time"], reverse=True)

        return jobs

    def _refresh_job_table(self):
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)

        for job in self._filtered_jobs():
            self.job_tree.insert(
                "",
                tk.END,
                iid=job["job_id"],
                values=(
                    job["job_id"],
                    job["blade_id"],
                    job["batch_id"],
                    job["status"],
                    job["created_time"]
                )
            )

    def _on_job_selected(self, event=None):
        selected = self.job_tree.selection()
        if not selected:
            return
        self.selected_job_id = selected[0]
        job = self._get_selected_job()
        if not job:
            return

        self.batch_info_var.set(f"批次信息：{job['batch_id']}")
        self.blade_info_var.set(f"叶片信息：{job['blade_id']}")
        self.progress_info_var.set(f"位姿进度：0 / {len(job['pose_list'])}")
        self.trace_var.set(
            f"参数包版本：{job['param_pack']}\n"
            f"算法版本：sim-1.0\n"
            f"模型版本：sim-1.0\n"
            f"软件版本：gui-1.1"
        )

    def _get_selected_job(self):
        if not self.selected_job_id:
            return None
        for job in self.jobs:
            if job["job_id"] == self.selected_job_id:
                return job
        return None

    def _create_job(self):
        idx = len(self.jobs) + 1
        new_job = {
            "job_id": f"JOB-2026-{idx:03d}",
            "blade_id": f"BLD-{2000+idx}",
            "batch_id": f"BATCH-{random.randint(1, 9):02d}",
            "status": "待执行",
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "param_pack": f"PKG-v2.{random.randint(1, 9)}",
            "hole_count": random.randint(190, 210),
            "pose_list": [
                [round(random.uniform(0, 100), 2),
                 round(random.uniform(0, 100), 2),
                 round(random.uniform(0, 100), 2),
                 round(random.uniform(-20, 20), 2),
                 round(random.uniform(-20, 20), 2)]
                for _ in range(random.randint(6, 12))
            ]
        }
        self.jobs.insert(0, new_job)
        self._refresh_job_table()
        self._set_status("已创建新任务")

    def _show_job_detail(self):
        job = self._get_selected_job()
        if not job:
            messagebox.showinfo("提示", "请先选择任务。")
            return

        pose_preview = "\n".join([str(p) for p in job["pose_list"][:5]])
        detail = (
            f"任务编号：{job['job_id']}\n"
            f"叶片ID：{job['blade_id']}\n"
            f"批次：{job['batch_id']}\n"
            f"状态：{job['status']}\n"
            f"创建时间：{job['created_time']}\n"
            f"参数包：{job['param_pack']}\n"
            f"位姿数量：{len(job['pose_list'])}\n"
            f"预期孔数量：{job['hole_count']}\n\n"
            f"位姿列表示例：\n{pose_preview}"
        )
        messagebox.showinfo("任务详情", detail)

    def _start_selected_job(self):
        job = self._get_selected_job()
        if not job:
            messagebox.showinfo("提示", "请先选择任务。")
            return
        if self.system.is_running:
            messagebox.showwarning("提示", "当前已有任务正在执行。")
            return

        job["status"] = "执行中"
        self._refresh_job_table()
        self._clear_result_table()
        self.log_text.delete("1.0", tk.END)
        self.fail_listbox.delete(0, tk.END)
        self.report_info_var.set("报告状态：生成中")
        self._set_status("任务执行中")
        self.progress_var.set(0)

        t = threading.Thread(target=self._run_job_thread, args=(job,), daemon=True)
        t.start()

    def _run_job_thread(self, job):
        def callback(kind, payload):
            self.root.after(0, self._handle_callback, kind, payload, job)

        result = self.system.run_job(job, callback=callback)
        self.root.after(0, self._job_finished, job, result)

    def _handle_callback(self, kind, payload, job):
        if kind == "log":
            self.log_text.insert(tk.END, payload + "\n")
            self.log_text.see(tk.END)

        elif kind == "state":
            self._refresh_status_panel()
            current = payload.get("current_pose_index", self.system.current_pose_index)
            total = payload.get("total_pose_count", self.system.total_pose_count)

            if total > 0:
                if current <= total:
                    progress = min(60.0, current / total * 60.0)
                    if self.system.current_stage in ["超分辨率重建", "深度估计", "点云融合", "孔识别与参数拟合", "生成报告"]:
                        mapping = {
                            "超分辨率重建": 70,
                            "深度估计": 80,
                            "点云融合": 88,
                            "孔识别与参数拟合": 96,
                            "生成报告": 100
                        }
                        progress = mapping.get(self.system.current_stage, progress)
                    self.progress_var.set(progress)

            self.progress_info_var.set(f"位姿进度：{self.system.current_pose_index} / {self.system.total_pose_count}")
            self._refresh_fail_listbox()

    def _job_finished(self, job, result):
        if result == "finished":
            job["status"] = "已完成"
            self._fill_result_table(self.system.measure_results)
            self.result_count_var.set(f"识别孔数量：{len(self.system.measure_results)}")
            self.failure_count_var.set(f"失败事件：{len(self.system.failure_events)}")
            self.report_info_var.set("报告状态：已生成")
            self.progress_var.set(100)
            self._set_status("任务完成")
        elif result == "cancelled":
            job["status"] = "已取消"
            self.report_info_var.set("报告状态：未生成")
            self._set_status("任务已取消")
        else:
            job["status"] = "待执行"
            self._set_status("任务结束")

        self._refresh_job_table()
        self._refresh_status_panel()
        self._refresh_fail_listbox()

    def _pause_job(self):
        if not self.system.is_running:
            messagebox.showinfo("提示", "当前没有运行中的任务。")
            return
        self.system.pause()
        job = self._get_selected_job()
        if job:
            job["status"] = "暂停"
        self._refresh_job_table()
        self._set_status("任务已暂停")

    def _resume_job(self):
        if not self.system.is_running:
            messagebox.showinfo("提示", "当前没有运行中的任务。")
            return
        self.system.resume()
        job = self._get_selected_job()
        if job:
            job["status"] = "执行中"
        self._refresh_job_table()
        self._set_status("任务已继续")

    def _cancel_job(self):
        if not self.system.is_running:
            messagebox.showinfo("提示", "当前没有运行中的任务。")
            return
        self.system.cancel()
        self._set_status("正在取消任务...")

    def _refresh_status_panel(self):
        x, y, z, a, b = self.system.platform_pose
        self.platform_pose_var.set(
            f"平台位姿：X={x:.2f}  Y={y:.2f}  Z={z:.2f}  A={a:.2f}  B={b:.2f}"
        )
        self.camera_status_var.set(f"相机状态：{self.system.camera_status}")
        self.queue_var.set(f"队列长度：{self.system.queue_length}")
        self.stage_var.set(f"当前阶段：{self.system.current_stage}")

    def _refresh_fail_listbox(self):
        self.fail_listbox.delete(0, tk.END)
        if not self.system.failure_events:
            self.fail_listbox.insert(tk.END, "无失败事件")
            return

        for ev in self.system.failure_events:
            self.fail_listbox.insert(
                tk.END,
                f"位姿{ev['pose_index']} | {ev['reason']}"
            )

    def _clear_result_table(self):
        for item in self.hole_tree.get_children():
            self.hole_tree.delete(item)
        self.result_count_var.set("识别孔数量：0")
        self.failure_count_var.set("失败事件：0")

    def _fill_result_table(self, results):
        self._clear_result_table()
        for row in results:
            center = f"({row['center'][0]:.3f}, {row['center'][1]:.3f}, {row['center'][2]:.3f})"
            axis = f"({row['axis'][0]:.4f}, {row['axis'][1]:.4f}, {row['axis'][2]:.4f})"
            bbox = (
                f"[{row['bbox']['xmin']:.2f},{row['bbox']['xmax']:.2f}] "
                f"[{row['bbox']['ymin']:.2f},{row['bbox']['ymax']:.2f}] "
                f"[{row['bbox']['zmin']:.2f},{row['bbox']['zmax']:.2f}]"
            )

            self.hole_tree.insert(
                "",
                tk.END,
                values=(
                    row["hole_id"],
                    center,
                    f"{row['diameter']:.3f}",
                    axis,
                    bbox,
                    f"{row['tilt']:.3f}",
                    f"{row['residual']:.4f}",
                    f"{row['confidence']:.4f}"
                )
            )

    def _restore_all_results(self):
        if not self.system.measure_results:
            messagebox.showinfo("提示", "当前没有结果可恢复。")
            return
        self._fill_result_table(self.system.measure_results)
        self._set_status("已恢复全部孔结果")

    def _query_nearby_holes(self):
        if not self.system.measure_results:
            messagebox.showinfo("提示", "请先运行任务生成孔结果。")
            return

        try:
            x = float(self.qx_var.get())
            y = float(self.qy_var.get())
            z = float(self.qz_var.get())
            radius = float(self.radius_var.get())
        except ValueError:
            messagebox.showerror("输入错误", "近邻查询参数必须为数值。")
            return

        results = self.system.query_holes_near_position(x, y, z, radius)
        self._fill_result_table(results)
        self.result_count_var.set(f"识别孔数量：{len(results)}")
        self._set_status(f"近邻查询完成，共 {len(results)} 个孔")

    def _query_region_holes(self):
        if not self.system.measure_results:
            messagebox.showinfo("提示", "请先运行任务生成孔结果。")
            return

        try:
            xmin = float(self.xmin_var.get())
            xmax = float(self.xmax_var.get())
            ymin = float(self.ymin_var.get())
            ymax = float(self.ymax_var.get())
        except ValueError:
            messagebox.showerror("输入错误", "区域查询参数必须为数值。")
            return

        results = self.system.query_holes_in_region(xmin, xmax, ymin, ymax)
        self._fill_result_table(results)
        self.result_count_var.set(f"识别孔数量：{len(results)}")
        self._set_status(f"区域查询完成，共 {len(results)} 个孔")

    def _export_csv(self):
        if not self.system.measure_results:
            messagebox.showinfo("提示", "当前没有可导出的孔参数结果。")
            return

        filename = f"hole_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "孔编号", "中心X", "中心Y", "中心Z",
                    "孔径", "孔轴方向X", "孔轴方向Y", "孔轴方向Z",
                    "包络盒Xmin", "包络盒Xmax",
                    "包络盒Ymin", "包络盒Ymax",
                    "包络盒Zmin", "包络盒Zmax",
                    "倾角", "拟合残差", "置信度"
                ])
                for row in self.system.measure_results:
                    writer.writerow([
                        row["hole_id"],
                        row["center"][0], row["center"][1], row["center"][2],
                        row["diameter"],
                        row["axis"][0], row["axis"][1], row["axis"][2],
                        row["bbox"]["xmin"], row["bbox"]["xmax"],
                        row["bbox"]["ymin"], row["bbox"]["ymax"],
                        row["bbox"]["zmin"], row["bbox"]["zmax"],
                        row["tilt"], row["residual"], row["confidence"]
                    ])

            self.report_info_var.set(f"报告状态：CSV已导出（{filename}）")
            self._set_status("已导出CSV")
            messagebox.showinfo("导出成功", f"CSV 已导出到当前目录：\n{filename}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


def main():
    root = tk.Tk()
    app = BladeMeasurementGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
