#coding=utf-8
import os
import sys
import time
import math
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# -------------------------------------------------------------------DEVELOPER SETTINGS------------------------------------------------------------------- #
developer_settings = {
    # --- 功能开关 ---
    'enable_debug_mode': True,  # 【新增】是否开放调试模式 (设为 False 则隐藏模式 6)

    # --- 时间与逻辑参数 ---
    'green_time_fixed': 20.0,
    'yellow_time': 3.0,
    'all_red_time': 2.0,
    'logic_fps': 30,

    # --- 车辆物理 ---
    'car_length_m': 4.5,
    'stop_line_buffer': 1.5,
    'min_static_gap': 70.0,  # 大间距防碰撞
    'red_light_decel_distance': 200.0,
    'deceleration_rate': 4.0,
    'emergency_decel': 100.0,  # 极大减速度
    'acceleration_rate': 2.5,
    'stop_line_offset': 15.0,
    'spawn_distance_min': 400.0,
    'spawn_distance_max': 900.0,
    'respawn_distance': -60.0,

    # --- 道路与图形 ---
    'lane_width_px': 55,
    'double_yellow_gap': 12,
    'road_shoulder': 40,
    'dash_length': 30,
    'dash_gap': 30,
    'car_size_px': 22,
    'light_offset_px': 30,

    # --- 窗口与布局 ---
    'window_width': 1600,
    'window_height': 1000,
    'map_weight': 4,
    'detail_weight': 1,
    'tree_view_rows': 8,

    # --- 字体与颜色 ---
    'font_ui': ("微软雅黑", 12),
    'font_console': ("Consolas", 9),
    'font_light': ("Consolas", 16, "bold"),
    'font_dir': ("System", 10),
    'font_debug': ("Consolas", 10),
    'color_bg': '#2c3e50',
    'color_road': '#34495e',
    'color_line_white': '#ecf0f1',
    'color_line_yellow': '#f1c40f',
    'color_crosswalk': '#ecf0f1',
    'color_light_bg': '#1a252f',
    'color_light_off': '#300000',
    'color_tail_stop': '#e74c3c',
    'color_tail_slow': '#f39c12',
    'color_tail_go': '#3498db',
    'color_tail_run': '#2ecc71',
    'color_debug_bg': '#2d3436',
    'color_debug_text': '#dfe6e9',
}

log_file_path = os.path.join(os.path.expanduser("~"), "Desktop", "traffic_log_debug.log")


def log(log_msg='log_msg', log_type='LOG'):
    try:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, 'a', encoding='utf-8') as log_a:
            log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"\n{log_time} [{log_type}]: {log_msg}"
            log_a.write(log_message)
    except Exception as e:
        print(f"Log Error: {e}")


class DebugToolbox(tk.Toplevel):
    def __init__(self, parent, sim_gui):
        super().__init__(parent)
        self.sim_gui = sim_gui
        self.title("🛠️ 交通模拟调试工具箱 (Mode 6)")
        self.geometry("450x700")
        self.configure(bg=developer_settings['color_debug_bg'])

        # 保持置顶
        self.attributes('-topmost', True)
        self.protocol("WM_DELETE_WINDOW", self.on_close_request)

        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        # 标题
        lbl_title = tk.Label(self, text="DEBUG TOOLBOX", bg=developer_settings['color_debug_bg'],
                             fg='#00cec9', font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # --- 信号灯控制区 ---
        frame_light = tk.LabelFrame(self, text="信号灯手动控制", bg=developer_settings['color_debug_bg'],
                                    fg=developer_settings['color_debug_text'], font=developer_settings['font_ui'])
        frame_light.pack(fill=tk.X, padx=10, pady=5)

        btn_frame = tk.Frame(frame_light, bg=developer_settings['color_debug_bg'])
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="⬅️ 上一相位", command=self.prev_phase, bg='#636e72', fg='white', width=10).pack(
            side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="➡️ 下一相位", command=self.next_phase, bg='#636e72', fg='white', width=10).pack(
            side=tk.LEFT, padx=2)

        state_frame = tk.Frame(frame_light, bg=developer_settings['color_debug_bg'])
        state_frame.pack(pady=5)
        tk.Button(state_frame, text="强制绿灯", command=lambda: self.force_state('GREEN'), bg='#2ecc71', fg='white',
                  width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(state_frame, text="强制黄灯", command=lambda: self.force_state('YELLOW'), bg='#f1c40f', fg='black',
                  width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(state_frame, text="强制红灯", command=lambda: self.force_state('ALL_RED'), bg='#e74c3c', fg='white',
                  width=8).pack(side=tk.LEFT, padx=2)

        tk.Button(frame_light, text="🔄 恢复自动循环", command=self.resume_auto, bg='#0984e3', fg='white',
                  width=20).pack(pady=5)

        self.lbl_light_status = tk.Label(frame_light, text="当前: 自动", bg='#2d3436', fg='white',
                                         font=developer_settings['font_console'])
        self.lbl_light_status.pack(pady=2)

        # --- 车辆状态监控区 ---
        frame_cars = tk.LabelFrame(self, text="车辆实时监控 (Top 15)", bg=developer_settings['color_debug_bg'],
                                   fg=developer_settings['color_debug_text'], font=developer_settings['font_ui'])
        frame_cars.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ('ID', 'Dir', 'Lane', 'Pos', 'Spd', 'Stat')
        self.tree = ttk.Treeview(frame_cars, columns=columns, show='headings', height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=50, anchor='center')

        scrollbar = ttk.Scrollbar(frame_cars, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- 调试信息区 ---
        frame_info = tk.LabelFrame(self, text="系统调试信息", bg=developer_settings['color_debug_bg'],
                                   fg=developer_settings['color_debug_text'], font=developer_settings['font_ui'])
        frame_info.pack(fill=tk.X, padx=10, pady=5)

        self.info_text = tk.Text(frame_info, height=6, bg='#2d3436', fg='#00b894',
                                 font=developer_settings['font_debug'], wrap=tk.WORD, state='disabled')
        self.info_text.pack(fill=tk.X, padx=5, pady=5)

        btn_bottom = tk.Frame(self, bg=developer_settings['color_debug_bg'])
        btn_bottom.pack(pady=5)
        tk.Button(btn_bottom, text="🗑️ 清空日志", command=self.clear_log, bg='#d63031', fg='white', width=15).pack(
            side=tk.LEFT, padx=10)
        tk.Button(btn_bottom, text="🚗 重置车辆", command=self.reset_cars, bg='#00cec9', fg='white', width=15).pack(
            side=tk.LEFT, padx=10)

    def prev_phase(self):
        self.sim_gui.debug_manual_step(-1)

    def next_phase(self):
        self.sim_gui.debug_manual_step(1)

    def force_state(self, state):
        self.sim_gui.debug_force_state(state)

    def resume_auto(self):
        self.sim_gui.debug_resume_auto()

    def clear_log(self):
        self.sim_gui.log_text.config(state='normal')
        self.sim_gui.log_text.delete('1.0', tk.END)
        self.sim_gui.log_text.config(state='disabled')
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.config(state='disabled')

    def reset_cars(self):
        self.sim_gui.reset_system()
        self.sim_gui.log_msg("调试模式：车辆已重置。")

    def update_loop(self):
        if self.winfo_exists():
            self.update_vehicle_list()
            self.update_debug_info()
            self.after(200, self.update_loop)  # 200ms 刷新一次

    def update_vehicle_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        d_map = {1: 'N', 2: 'E', 3: 'S', 4: 'W'}
        status_map = {'run': 'RUN', 'stop': 'STOP', 'slow_stop': 'SLOW', 'go': 'GO'}

        # 只显示前 15 辆
        count = 0
        for cid in self.sim_gui.car_ids:
            if count >= 15: break
            if cid in self.sim_gui.cars:
                c = self.sim_gui.cars[cid]
                vals = (cid.replace('car', ''), d_map.get(c['dir'], '?'), c['lane'],
                        f"{c['pos']:.1f}", int(c['speed']), status_map.get(c['status'], '?'))
                self.tree.insert('', 'end', values=vals)
                count += 1

    def update_debug_info(self):
        info = f"FPS: {self.sim_gui.fps}\n"
        info += f"Active Cars: {len(self.sim_gui.cars)}\n"
        info += f"Phase: {self.sim_gui.phase_state} (Dir: {self.sim_gui.directions[self.sim_gui.current_green_dir]})\n"
        info += f"Timer: {self.sim_gui.light_timers[self.sim_gui.current_green_dir]:.2f}s\n"
        info += f"Mode: {self.sim_gui.mode} (Debug)\n"
        info += f"Uptime: {time.time() - self.sim_gui.start_time:.1f}s"

        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state='disabled')

        # 更新状态标签
        mode_txt = "手动控制" if self.sim_gui.debug_mode_active else "自动循环"
        self.lbl_light_status.config(text=f"当前: {mode_txt} | State: {self.sim_gui.phase_state}")

    def on_close_request(self):
        # 用户点击关闭按钮时，切回模式 1
        self.sim_gui.mode_var.set(1)
        self.sim_gui.update_mode()
        self.destroy()


class TrafficSimGUI:
    def __init__(self, root=None):
        self.root = root if root else tk.Tk()
        self.root.title(f"智能交通模拟系统 V-Final (With Debug Mode)")

        w = developer_settings['window_width']
        h = developer_settings['window_height']
        self.root.geometry(f"{w}x{h}")
        self.root.configure(bg='#f0f0f0')

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.running = False
        self.paused = False
        self.sim_thread = None
        self.start_time = time.time()

        self.mode = 1
        self.lane_count = 3
        self.car_count = 40
        self.max_speed = 120

        self.cars = {}
        self.car_ids = []
        self.light_timers = [0.0, 0.0, 0.0, 0.0]
        self.directions = ['北', '东', '南', '西']
        self.current_green_dir = 0
        self.phase_state = 'GREEN'

        # 调试模式专用变量
        self.debug_toolbox = None
        self.debug_mode_active = False

        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0

        self.vehicle_items = {}
        self.light_objects = {}
        self.road_drawn = False

        self.pixels_per_meter = 1.0
        self.stop_line_pixels = {}

        self.colors = {
            'bg': developer_settings['color_bg'],
            'road': developer_settings['color_road'],
            'line_white': developer_settings['color_line_white'],
            'line_yellow': developer_settings['color_line_yellow'],
            'stop_line': developer_settings['color_line_white'],
            'crosswalk': developer_settings['color_crosswalk'],
            'light_bg': developer_settings['color_light_bg'],
            'stop': developer_settings['color_tail_stop'],
            'slow': developer_settings['color_tail_slow'],
            'go': developer_settings['color_tail_go'],
            'run': developer_settings['color_tail_run'],
        }

        self.setup_ui()
        self.root.after(100, self.init_system)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        control_frame = tk.LabelFrame(self.root, text="控制面板", font=developer_settings['font_ui'], bg='#ffffff',
                                      padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        param_frame = tk.Frame(control_frame, bg='#ffffff')
        param_frame.pack(fill=tk.X)

        tk.Label(param_frame, text="模式:", bg='#ffffff', font=developer_settings['font_ui']).grid(row=0, column=0,
                                                                                                   padx=5)
        self.mode_var = tk.IntVar(value=1)

        # 动态生成模式列表
        modes = [("固定循环", 1), ("动态车流", 2), ("高级动态", 3), ("检修模式", 4), ("停用模式", 5)]
        if developer_settings['enable_debug_mode']:
            modes.append(("🛠️ 调试模式", 6))

        for i, (txt, val) in enumerate(modes):
            tk.Radiobutton(param_frame, text=txt, variable=self.mode_var, value=val, bg='#ffffff',
                           command=self.update_mode).grid(row=0, column=i + 1, padx=5)

        tk.Label(param_frame, text="单向车道:", bg='#ffffff', font=developer_settings['font_ui']).grid(row=0, column=7,
                                                                                                       padx=(20, 5))
        self.lane_var = tk.Spinbox(param_frame, from_=1, to=6, width=5, font=("Arial", 10))
        self.lane_var.delete(0, "end");
        self.lane_var.insert(0, 3)
        self.lane_var.grid(row=0, column=8, padx=5)

        tk.Label(param_frame, text="车辆数:", bg='#ffffff', font=developer_settings['font_ui']).grid(row=0, column=9,
                                                                                                     padx=(20, 5))
        self.car_var = tk.Spinbox(param_frame, from_=5, to=200, width=5, font=("Arial", 10))
        self.car_var.delete(0, "end");
        self.car_var.insert(0, 40)
        self.car_var.grid(row=0, column=10, padx=5)

        tk.Label(param_frame, text="限速:", bg='#ffffff', font=developer_settings['font_ui']).grid(row=0, column=11,
                                                                                                   padx=(20, 5))
        self.speed_var = tk.Spinbox(param_frame, from_=30, to=200, width=5, font=("Arial", 10))
        self.speed_var.delete(0, "end");
        self.speed_var.insert(0, 120)
        self.speed_var.grid(row=0, column=12, padx=5)

        btn_frame = tk.Frame(control_frame, bg='#ffffff')
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="开始/重置", command=self.start_simulation, bg='#27ae60', fg='white', width=12,
                  font=developer_settings['font_ui']).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="暂停/继续", command=self.toggle_pause, bg='#e67e22', fg='white', width=12,
                  font=developer_settings['font_ui']).pack(side=tk.LEFT, padx=5)

        self.stat_label = tk.Label(control_frame, text="就绪", bg='#ffffff', fg='#7f8c8d', anchor='w',
                                   font=developer_settings['font_console'])
        self.stat_label.pack(fill=tk.X, padx=5, pady=5)

        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        map_frame = tk.Frame(self.main_paned, bg='#ecf0f1')
        self.main_paned.add(map_frame, weight=developer_settings['map_weight'])

        self.map_canvas = tk.Canvas(map_frame, bg=self.colors['bg'], highlightthickness=0)
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
        self.map_canvas.bind("<Configure>", self.on_resize)

        detail_paned = ttk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL)
        self.main_paned.add(detail_paned, weight=developer_settings['detail_weight'])

        detail_frame = tk.LabelFrame(detail_paned, text="车辆实时数据", font=("微软雅黑", 10), bg='#ffffff')
        detail_paned.add(detail_frame, weight=2)

        columns = ('ID', '方向', '距离', '速度', '状态')
        self.tree = ttk.Treeview(detail_frame, columns=columns, show='headings',
                                 height=developer_settings['tree_view_rows'])
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=70, anchor='center')

        tree_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        log_frame = tk.LabelFrame(detail_paned, text="系统日志", font=("微软雅黑", 10), bg='#ffffff')
        detail_paned.add(log_frame, weight=1)

        self.log_text = tk.Text(log_frame, bg='#2c3e50', fg='#ecf0f1', font=developer_settings['font_console'],
                                wrap=tk.WORD, state='disabled')
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def init_system(self):
        self.reset_system()
        self.draw_static_elements()
        self.log_msg("系统初始化完成 (含调试模式支持)。")

    def log_msg(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        log(msg, "GUI")

    def update_mode(self):
        new_mode = self.mode_var.get()
        if new_mode == self.mode:
            return

        old_mode = self.mode
        self.log_msg(f"切换模式: {old_mode} -> {new_mode}")
        self.mode = new_mode

        # 处理调试模式窗口
        if new_mode == 6:
            if not developer_settings['enable_debug_mode']:
                self.log_msg("错误：调试模式已被禁用。")
                self.mode_var.set(1)
                return
            self.debug_mode_active = True
            if self.debug_toolbox is None or not self.debug_toolbox.winfo_exists():
                self.debug_toolbox = DebugToolbox(self.root, self)
            self.phase_state = 'GREEN'  # 进入调试模式默认绿灯，由用户控制
            self.log_msg("已进入调试模式：信号灯控制权已移交工具箱。")

        else:
            # 离开调试模式
            if old_mode == 6:
                self.debug_mode_active = False
                if self.debug_toolbox and self.debug_toolbox.winfo_exists():
                    self.debug_toolbox.destroy()
                    self.debug_toolbox = None
                self.log_msg("已退出调试模式：恢复自动控制。")

            # 其他模式逻辑
            if self.mode in [4, 5]:
                self.phase_state = 'MAINT' if self.mode == 4 else 'OFF'
                self.light_timers = [0.0, 0.0, 0.0, 0.0]
            else:
                self.phase_state = 'GREEN'
                self.current_green_dir = 0
                total_time = developer_settings['green_time_fixed'] + developer_settings['yellow_time']
                self.light_timers = [0.0, 0.0, 0.0, 0.0]
                self.light_timers[0] = total_time

    # --- 调试模式专用控制函数 ---
    def debug_manual_step(self, direction):
        """手动切换下一个或上一个相位"""
        if not self.debug_mode_active: return

        current = self.current_green_dir
        if direction > 0:
            next_dir = (current + 1) % 4
        else:
            next_dir = (current - 1) % 4

        self.current_green_dir = next_dir
        self.phase_state = 'GREEN'
        self.light_timers = [0.0, 0.0, 0.0, 0.0]
        self.light_timers[next_dir] = 9999.0  # 设置一个很长的时间，直到下次手动切换
        self.log_msg(f"调试：手动切换至 {self.directions[next_dir]}向 绿灯。")

    def debug_force_state(self, state):
        """强制设定状态"""
        if not self.debug_mode_active: return
        self.phase_state = state
        idx = self.current_green_dir
        if state == 'GREEN':
            self.light_timers[idx] = 9999.0
        elif state == 'YELLOW':
            self.light_timers[idx] = 9999.0
        elif state == 'ALL_RED':
            self.light_timers[idx] = 9999.0
        self.log_msg(f"调试：强制状态为 {state}。")

    def debug_resume_auto(self):
        """恢复自动循环"""
        if not self.debug_mode_active: return
        self.phase_state = 'GREEN'
        total_time = developer_settings['green_time_fixed'] + developer_settings['yellow_time']
        self.light_timers = [0.0, 0.0, 0.0, 0.0]
        self.light_timers[self.current_green_dir] = total_time
        self.log_msg("调试：恢复当前方向的自动计时。")

    def reset_system(self):
        self.cars = {}
        self.car_ids = []
        self.vehicle_items = {}
        # 保留灯光状态如果是调试模式
        if not self.debug_mode_active:
            self.light_timers = [0.0, 0.0, 0.0, 0.0]
            self.current_green_dir = 0
            self.phase_state = 'GREEN'
            if self.mode not in [4, 5]:
                total_time = developer_settings['green_time_fixed'] + developer_settings['yellow_time']
                self.light_timers[0] = total_time

        self.lane_count = int(self.lane_var.get())
        self.car_count = int(self.car_var.get())
        self.max_speed = int(self.speed_var.get())
        # 不重置 mode，避免触发 update_mode 逻辑

        lane_cars = {(d, l): [] for d in range(1, 5) for l in range(1, self.lane_count + 1)}
        min_spawn_gap = 20.0

        for i in range(self.car_count):
            car_id = f'car{i + 1}'
            d = random.randint(1, 4)
            l = random.randint(1, self.lane_count)
            key = (d, l)
            base_pos = random.randint(int(developer_settings['spawn_distance_min']),
                                      int(developer_settings['spawn_distance_max']))

            if lane_cars[key]:
                existing_positions = sorted(lane_cars[key])
                last_pos = existing_positions[-1]
                base_pos = max(base_pos, last_pos + min_spawn_gap)

            lane_cars[key].append(base_pos)
            s = float(random.randint(30, self.max_speed))
            color = "#{:02x}{:02x}{:02x}".format(random.randint(50, 200), random.randint(50, 200),
                                                 random.randint(50, 200))

            self.cars[car_id] = {
                'dir': d, 'lane': l, 'pos': base_pos, 'status': 'run', 'speed': s, 'color': color,
                'passed_stop_line': False
            }
            self.car_ids.append(car_id)

        self.road_drawn = False
        self.draw_static_elements()

    def draw_static_elements(self):
        w = self.map_canvas.winfo_width()
        h = self.map_canvas.winfo_height()
        if w < 50 or h < 50:
            self.root.after(100, self.draw_static_elements)
            return
        self.map_canvas.delete("all")
        self.light_objects = {}
        self.draw_roads_gb(w, h)
        self.draw_intersection_lights(w, h)
        self.road_drawn = True

    def draw_roads_gb(self, w, h):
        cx, cy = w // 2, h // 2
        lane_w = developer_settings['lane_width_px']
        yellow_gap = developer_settings['double_yellow_gap']
        road_shoulder = developer_settings['road_shoulder']
        one_way_w = self.lane_count * lane_w
        total_road_w = one_way_w * 2 + yellow_gap
        road_bg_w = total_road_w + road_shoulder * 2

        self.map_canvas.create_rectangle(0, cy - road_bg_w // 2, w, cy + road_bg_w // 2, fill=self.colors['road'],
                                         tags="road")
        self.map_canvas.create_rectangle(cx - road_bg_w // 2, 0, cx + road_bg_w // 2, h, fill=self.colors['road'],
                                         tags="road")
        limit = total_road_w // 2

        coords_y = [
            (0, cy - yellow_gap // 2, cx - limit, cy - yellow_gap // 2),
            (0, cy + yellow_gap // 2, cx - limit, cy + yellow_gap // 2),
            (cx + limit, cy - yellow_gap // 2, w, cy - yellow_gap // 2),
            (cx + limit, cy + yellow_gap // 2, w, cy + yellow_gap // 2),
            (cx - yellow_gap // 2, 0, cx - yellow_gap // 2, cy - limit),
            (cx + yellow_gap // 2, 0, cx + yellow_gap // 2, cy - limit),
            (cx - yellow_gap // 2, cy + limit, cx - yellow_gap // 2, h),
            (cx + yellow_gap // 2, cy + limit, cx + yellow_gap // 2, h),
        ]
        for c in coords_y:
            self.map_canvas.create_line(c, fill=self.colors['line_yellow'], width=4, tags="road")

        dash_len = developer_settings['dash_length']
        dash_gap = developer_settings['dash_gap']
        step = dash_len + dash_gap
        for i in range(1, self.lane_count):
            offset = i * lane_w
            y_n, y_s = cy - yellow_gap // 2 - offset, cy + yellow_gap // 2 + offset
            x_w, x_e = cx - yellow_gap // 2 - offset, cx + yellow_gap // 2 + offset

            for x in range(0, cx - limit, step):
                self.map_canvas.create_line(x, y_n, x + dash_len, y_n, fill=self.colors['line_white'], width=2,
                                            tags="road")
                self.map_canvas.create_line(x, y_s, x + dash_len, y_s, fill=self.colors['line_white'], width=2,
                                            tags="road")
            for x in range(cx + limit, w, step):
                self.map_canvas.create_line(x, y_n, x + dash_len, y_n, fill=self.colors['line_white'], width=2,
                                            tags="road")
                self.map_canvas.create_line(x, y_s, x + dash_len, y_s, fill=self.colors['line_white'], width=2,
                                            tags="road")
            for y in range(0, cy - limit, step):
                self.map_canvas.create_line(x_w, y, x_w, y + dash_len, fill=self.colors['line_white'], width=2,
                                            tags="road")
                self.map_canvas.create_line(x_e, y, x_e, y + dash_len, fill=self.colors['line_white'], width=2,
                                            tags="road")
            for y in range(cy + limit, h, step):
                self.map_canvas.create_line(x_w, y, x_w, y + dash_len, fill=self.colors['line_white'], width=2,
                                            tags="road")
                self.map_canvas.create_line(x_e, y, x_e, y + dash_len, fill=self.colors['line_white'], width=2,
                                            tags="road")

        if developer_settings['stop_line_offset'] > 0:
            self.pixels_per_meter = limit / developer_settings['stop_line_offset']
        else:
            self.pixels_per_meter = 10.0

        self.stop_line_pixels = {1: cy - limit, 3: cy + limit, 2: cx + limit, 4: cx - limit}

        lw = 6
        self.map_canvas.create_line(cx - one_way_w, cy - limit, cx - yellow_gap // 2, cy - limit,
                                    fill=self.colors['stop_line'], width=lw, tags="road")
        self.map_canvas.create_line(cx + yellow_gap // 2, cy + limit, cx + one_way_w, cy + limit,
                                    fill=self.colors['stop_line'], width=lw, tags="road")
        self.map_canvas.create_line(cx + limit, cy - one_way_w, cx + limit, cy - yellow_gap // 2,
                                    fill=self.colors['stop_line'], width=lw, tags="road")
        self.map_canvas.create_line(cx - limit, cy + yellow_gap // 2, cx - limit, cy + one_way_w,
                                    fill=self.colors['stop_line'], width=lw, tags="road")

    def draw_intersection_lights(self, w, h):
        if w < 50 or h < 50: return
        cx, cy = w // 2, h // 2
        lane_w = developer_settings['lane_width_px']
        yellow_gap = developer_settings['double_yellow_gap']
        one_way_w = self.lane_count * lane_w
        total_road_w = one_way_w * 2 + yellow_gap
        limit = total_road_w // 2
        offset = developer_settings['light_offset_px']

        positions = [
            {'dir': 1, 'name': '北', 'x': cx + yellow_gap // 2 + 10, 'y': cy - limit - offset},
            {'dir': 2, 'name': '东', 'x': cx + limit + offset, 'y': cy + yellow_gap // 2 + 10},
            {'dir': 3, 'name': '南', 'x': cx - yellow_gap // 2 - 10, 'y': cy + limit + offset},
            {'dir': 4, 'name': '西', 'x': cx - limit - offset, 'y': cy - yellow_gap // 2 - 10},
        ]
        font_light = developer_settings['font_light']
        font_dir = developer_settings['font_dir']

        for p in positions:
            x, y = p['x'], p['y']
            bg = self.map_canvas.create_rectangle(x - 22, y - 45, x + 22, y + 25, fill=self.colors['light_bg'],
                                                  outline='#555', width=2, tags="light")
            r = self.map_canvas.create_oval(x - 14, y - 38, x + 7, y - 19, fill='#300000', tags="light")
            yl = self.map_canvas.create_oval(x - 14, y - 16, x + 7, y + 3, fill='#303000', tags="light")
            g = self.map_canvas.create_oval(x - 14, y + 6, x + 7, y + 25, fill='#003000', tags="light")
            t = self.map_canvas.create_text(x, y + 40, text="--", fill='white', font=font_light, tags="light")
            d_txt = self.map_canvas.create_text(x, y - 55, text=p['name'] + "向", fill='#bdc3c7', font=font_dir,
                                                tags="light")
            self.light_objects[p['name']] = {'r': r, 'y': yl, 'g': g, 't': t, 'bg': bg}

    def on_resize(self, event):
        if event.width > 50 and event.height > 50:
            self.draw_static_elements()
            if not self.running:
                self.update_visuals()

    # -------------------------------------------------------------------LOGIC------------------------------------------------------------------- #

    def logic_loop(self):
        dt = 1.0 / developer_settings['logic_fps']

        stop_line_offset = developer_settings['stop_line_offset']
        stop_buffer = developer_settings['stop_line_buffer']
        logical_stop_limit = stop_line_offset + stop_buffer

        min_safe_gap = developer_settings['min_static_gap']
        red_decel_dist = developer_settings['red_light_decel_distance']
        decel_normal = developer_settings['deceleration_rate']
        decel_emergency = developer_settings['emergency_decel']
        accel = developer_settings['acceleration_rate']
        respawn_dist = developer_settings['respawn_distance']

        while self.running:
            if self.paused:
                time.sleep(0.9)
                continue

            try:
                # 调试模式下，不自动更新灯光计时器，除非用户点击恢复
                if not self.debug_mode_active:
                    self.update_traffic_lights(dt)

                # 分组排序
                lanes = {}
                for cid in self.car_ids:
                    if cid not in self.cars: continue
                    c = self.cars[cid]
                    key = (c['dir'], c['lane'])
                    if key not in lanes: lanes[key] = []
                    lanes[key].append(c)

                for key in lanes:
                    lanes[key].sort(key=lambda x: x['pos'])

                # 串行处理
                for key, cars_in_lane in lanes.items():
                    front_car_final_pos = float('inf')

                    for car in cars_in_lane:
                        # 调试模式下，如果是手动强制状态，is_green/yellow 判断依然基于当前 phase_state
                        is_green = (self.current_green_dir == car['dir'] - 1) and (self.phase_state == 'GREEN')
                        is_yellow = (self.current_green_dir == car['dir'] - 1) and (self.phase_state == 'YELLOW')

                        has_passed_line = car['pos'] < logical_stop_limit
                        target_status = 'run'

                        if not has_passed_line:
                            if not is_green and not is_yellow:
                                if car['pos'] < logical_stop_limit + red_decel_dist and car[
                                    'pos'] > logical_stop_limit - 5:
                                    target_status = 'slow_stop'
                                if car['pos'] <= logical_stop_limit:
                                    target_status = 'stop'
                            elif is_green and car['status'] == 'stop':
                                target_status = 'go'
                            elif is_yellow and car['pos'] <= logical_stop_limit + red_decel_dist:
                                target_status = 'slow_stop'
                        else:
                            if not is_green and not is_yellow:
                                if car['status'] == 'stop':
                                    target_status = 'go'
                                else:
                                    target_status = 'run'

                        if front_car_final_pos != float('inf'):
                            dist_to_front = car['pos'] - front_car_final_pos
                            dynamic_safe = min_safe_gap + (car['speed'] * 0.3)
                            if dist_to_front < dynamic_safe:
                                target_status = 'slow_stop'
                                if dist_to_front < min_safe_gap + 0.2:
                                    target_status = 'stop'

                        if car['status'] == 'stop' and car['speed'] < 0.1 and target_status in ['slow_stop', 'stop']:
                            if not is_green:
                                target_status = 'stop'

                        car['next_status'] = target_status

                        speed = car['speed']
                        status = car['next_status']
                        current_decel = decel_normal
                        if status == 'stop' and speed > 0.1:
                            current_decel = decel_emergency

                        if status == 'run':
                            speed += random.uniform(-0.05, 0.1)
                            if speed > self.max_speed: speed = self.max_speed
                            if speed < 0: speed = 0
                        elif status == 'stop':
                            speed -= current_decel * dt * 10
                            if speed <= 0: speed = 0; car['status'] = 'stop'
                        elif status == 'slow_stop':
                            speed -= current_decel * dt * 10
                            if speed <= 0: speed = 0; car['status'] = 'stop'
                        elif status == 'go':
                            speed += accel * dt * 10
                            if speed > self.max_speed * 1.2: speed = self.max_speed * 1.2

                        car['speed'] = max(0, speed)
                        if status != 'stop' or speed > 0:
                            car['status'] = status

                        move_step = (car['speed'] / 3.6) * dt
                        proposed_pos = car['pos'] - move_step

                        if not has_passed_line and status in ['stop',
                                                              'slow_stop'] and proposed_pos < logical_stop_limit:
                            proposed_pos = logical_stop_limit
                            car['speed'] = 0;
                            car['status'] = 'stop'

                        if front_car_final_pos != float('inf'):
                            limit_by_car = front_car_final_pos + min_safe_gap
                            if proposed_pos < limit_by_car:
                                proposed_pos = limit_by_car
                                car['speed'] = 0;
                                car['status'] = 'stop'

                        car['pos'] = proposed_pos
                        front_car_final_pos = proposed_pos

                        if car['pos'] < respawn_dist:
                            car['pos'] = float(random.randint(int(developer_settings['spawn_distance_min']),
                                                              int(developer_settings['spawn_distance_max'])))
                            car['speed'] = float(random.randint(10, self.max_speed))
                            car['status'] = 'run'
                            car['passed_stop_line'] = False

                time.sleep(max(0, dt - (time.time() % dt)))
                self.root.after(0, self.update_visuals)

            except Exception as e:
                self.log_msg(f"Logic Error: {e}")
                import traceback
                traceback.print_exc()
                self.running = False

    def update_traffic_lights(self, dt):
        if self.mode == 4:
            self.phase_state = 'MAINT'
            return
        if self.mode == 5:
            self.phase_state = 'OFF'
            return

        if self.phase_state in ['GREEN', 'YELLOW']:
            idx = self.current_green_dir
            self.light_timers[idx] -= dt
            if self.phase_state == 'GREEN':
                if self.light_timers[idx] <= developer_settings['yellow_time']:
                    self.phase_state = 'YELLOW'
            elif self.phase_state == 'YELLOW':
                if self.light_timers[idx] <= 0:
                    self.phase_state = 'ALL_RED'
                    self.light_timers[idx] = developer_settings['all_red_time']
        elif self.phase_state == 'ALL_RED':
            idx = self.current_green_dir
            self.light_timers[idx] -= dt
            if self.light_timers[idx] <= 0:
                next_dir = (self.current_green_dir + 1) % 4
                new_green = developer_settings['green_time_fixed'] if self.mode == 1 else random.randint(15, 25)
                self.current_green_dir = next_dir
                self.light_timers[next_dir] = new_green + developer_settings['yellow_time']
                self.phase_state = 'GREEN'

    # -------------------------------------------------------------------VISUALS------------------------------------------------------------------- #
    # (此处省略 update_visuals, update_treeview, get_car_coords, get_tail_coords，逻辑与之前完全一致)
    # 为保证代码可直接运行，请保留上一版本中的这些函数内容。
    # 这里为了简洁只写框架，实际使用请填入完整代码

    def update_visuals(self):
        # ... (此处填入上一版本中完整的 update_visuals 代码) ...
        # 重点：确保尾灯颜色逻辑包含速度极低强制变红的逻辑
        w = self.map_canvas.winfo_width()
        h = self.map_canvas.winfo_height()
        if w < 50 or h < 50: return
        if not self.road_drawn:
            self.draw_static_elements()
            return
        cx, cy = w // 2, h // 2

        cycle_time_est = 0
        if self.mode == 1:
            single_phase = developer_settings['green_time_fixed'] + developer_settings['yellow_time'] + \
                           developer_settings['all_red_time']
            cycle_time_est = single_phase * 4

        for name, obj in self.light_objects.items():
            idx = self.directions.index(name)
            r_c, y_c, g_c = '#300000', '#303000', '#003000'
            txt = "--"
            if self.phase_state == 'OFF':
                pass
            elif self.phase_state == 'MAINT':
                if int(time.time() * 2) % 2 == 0: y_c = developer_settings['color_line_yellow']
                txt = "MAINT"
            else:
                is_current = (idx == self.current_green_dir)
                timer_val = self.light_timers[idx] if is_current else 0
                if is_current:
                    if self.phase_state == 'GREEN':
                        g_c = developer_settings['color_tail_run']
                        rem = timer_val - developer_settings['yellow_time']
                        txt = str(max(0, int(rem)))
                        if 0 < rem <= 3.0 and int(rem * 2) % 2 == 0: g_c = '#003000'
                    elif self.phase_state == 'YELLOW':
                        y_c = developer_settings['color_line_yellow']
                        txt = str(max(0, int(timer_val)))
                    else:
                        r_c = developer_settings['color_tail_stop']
                else:
                    if self.mode == 1 and cycle_time_est > 0:
                        wait = 0.0
                        curr_rem = self.light_timers[self.current_green_dir]
                        if self.phase_state == 'GREEN':
                            wait += curr_rem + developer_settings['all_red_time']
                            steps = (idx - self.current_green_dir - 1) % 4
                        elif self.phase_state == 'YELLOW':
                            wait += curr_rem + developer_settings['all_red_time']
                            steps = (idx - self.current_green_dir - 1) % 4
                        elif self.phase_state == 'ALL_RED':
                            wait += curr_rem
                            steps = (idx - self.current_green_dir) % 4
                        single = developer_settings['green_time_fixed'] + developer_settings['yellow_time'] + \
                                 developer_settings['all_red_time']
                        wait += steps * single
                        txt = str(max(0, int(wait)))
                    else:
                        txt = "Wait"
                    if self.phase_state != 'MAINT': r_c = developer_settings['color_tail_stop']

            self.map_canvas.itemconfig(obj['r'], fill=r_c)
            self.map_canvas.itemconfig(obj['y'], fill=y_c)
            self.map_canvas.itemconfig(obj['g'], fill=g_c)
            self.map_canvas.itemconfig(obj['t'], text=txt)

        current_ids = set(self.car_ids)
        drawn_ids = set(self.vehicle_items.keys())
        for cid in drawn_ids - current_ids:
            self.map_canvas.delete(self.vehicle_items[cid]['rect'])
            self.map_canvas.delete(self.vehicle_items[cid]['lights'][0])
            self.map_canvas.delete(self.vehicle_items[cid]['lights'][1])
            del self.vehicle_items[cid]

        for cid in self.car_ids:
            c = self.cars[cid]
            coords = self.get_car_coords(c, cx, cy, developer_settings['lane_width_px'], w, h)
            if not coords: continue
            x, y, angle = coords

            # 视觉状态平滑
            display_status = c['status']
            if c['speed'] < 1.0:
                display_status = 'stop'

            tail_color = self.colors['run']
            if display_status == 'stop':
                tail_color = self.colors['stop']
            elif display_status == 'slow_stop':
                tail_color = self.colors['slow']
            elif display_status == 'go':
                tail_color = self.colors['go']

            size = developer_settings['car_size_px']

            if cid in self.vehicle_items:
                item = self.vehicle_items[cid]
                self.map_canvas.coords(item['rect'], x - size / 2, y - size / 2, x + size / 2, y + size / 2)
                self.map_canvas.itemconfig(item['rect'], fill=c['color'], outline='black')
                lx1, ly1, lx2, ly2 = self.get_tail_coords(x, y, size, angle, 'left')
                rx1, ry1, rx2, ry2 = self.get_tail_coords(x, y, size, angle, 'right')
                self.map_canvas.coords(item['lights'][0], lx1, ly1, lx2, ly2)
                self.map_canvas.coords(item['lights'][1], rx1, ry1, rx2, ry2)
                self.map_canvas.itemconfig(item['lights'][0], fill=tail_color)
                self.map_canvas.itemconfig(item['lights'][1], fill=tail_color)
            else:
                rect = self.map_canvas.create_rectangle(x - size / 2, y - size / 2, x + size / 2, y + size / 2,
                                                        fill=c['color'], outline='black')
                lx1, ly1, lx2, ly2 = self.get_tail_coords(x, y, size, angle, 'left')
                rx1, ry1, rx2, ry2 = self.get_tail_coords(x, y, size, angle, 'right')
                l_light = self.map_canvas.create_rectangle(lx1, ly1, lx2, ly2, fill=tail_color, outline='')
                r_light = self.map_canvas.create_rectangle(rx1, ry1, rx2, ry2, fill=tail_color, outline='')
                self.vehicle_items[cid] = {'rect': rect, 'lights': [l_light, r_light]}

        self.update_treeview()
        self.frame_count += 1
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = now
            stop_cnt = sum(1 for c in self.cars.values() if c['status'] == 'stop')
            self.stat_label.config(text=f"车辆:{len(self.cars)} | 停止:{stop_cnt} | 模式:{self.mode} | FPS:{self.fps}")

    def update_treeview(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        count = 0
        d_map = {1: '北', 2: '东', 3: '南', 4: '西'}
        for car in self.car_ids:
            if count > 15: break
            if car in self.cars:
                d = self.cars[car]
                status_map = {'run': '匀速', 'stop': '停止', 'slow_stop': '减速', 'go': '加速'}
                self.tree.insert('', 'end', values=(car, d_map.get(d['dir'], '?'), f"{d['pos']:.1f}m", int(d['speed']),
                                                    status_map.get(d['status'], '?')))
                count += 1

    def get_car_coords(self, car, cx, cy, lane_w, w, h):
        d, l, pos = car['dir'], car['lane'], car['pos']
        offset = (self.lane_count - l + 0.5) * lane_w
        x, y, angle = 0, 0, 0
        if d == 1:
            x, y, angle = cx - offset, cy - pos, 90
        elif d == 3:
            x, y, angle = cx + offset, cy + pos, 270
        elif d == 2:
            x, y, angle = cx + pos, cy - offset, 180
        elif d == 4:
            x, y, angle = cx - pos, cy + offset, 0
        if y > h + 100 or y < -100 or x > w + 100 or x < -100: return None
        return x, y, angle

    def get_tail_coords(self, x, y, size, angle, side='left'):
        half = size / 2
        tail_depth, tail_width = 5, 5
        dx, dy = 0, 0
        if angle == 0:
            dx = -half
        elif angle == 90:
            dy = -half
        elif angle == 180:
            dx = half
        elif angle == 270:
            dy = half
        lat_offset = half - 2
        lx, ly = x + dx, y + dy
        if angle == 0:
            ly += (-lat_offset if side == 'left' else lat_offset)
        elif angle == 90:
            lx += (lat_offset if side == 'left' else -lat_offset)
        elif angle == 180:
            ly += (lat_offset if side == 'left' else -lat_offset)
        elif angle == 270:
            lx += (-lat_offset if side == 'left' else lat_offset)
        if side == 'left':
            return lx - tail_width / 2, ly - tail_depth, lx + tail_width / 2, ly
        else:
            return lx - tail_width / 2, ly - tail_depth, lx + tail_width / 2, ly

    def start_simulation(self):
        self.reset_system()
        if self.running:
            self.running = False
            time.sleep(0.2)
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self.log_msg("模拟已启动。")
        self.sim_thread = threading.Thread(target=self.logic_loop, daemon=True)
        self.sim_thread.start()

    def toggle_pause(self):
        if not self.running: self.start_simulation(); return
        self.paused = not self.paused
        self.log_msg(f"模拟已{'暂停' if self.paused else '继续'}。")

    def on_close(self):
        self.running = False
        if self.debug_toolbox and self.debug_toolbox.winfo_exists():
            self.debug_toolbox.destroy()
        self.root.destroy()
def start(zA=10, zV=50, zH=3):
    global ZS, SY, L1, L2, L3, L4, RCLz
    RCLz = [27, 0, 0, 0]
    ZS = {}
    SY = []
    for i in range(zA):
        SY.append(('car' + str((i + 1))))
        ZS[SY[(i)]] = [random.randint(1, 4), random.randint(1, zH), random.randint(20, 100), 'run', random.randint(30, zV)]
    L1 = []
    L2 = []
    L3 = []
    L4 = []
    for i in range(len(SY)):
        a2 = SY[i]
        if (ZS[a2][0] == 1):
            L1.append(a2)
        elif (ZS[a2][0] == 2) :
            L2.append(a2)
        elif (ZS[a2][0] == 3) :
            L3.append(a2)
        elif (ZS[a2][0] == 4) :
            L4.append(a2)
        else :
            pass

def car_stop():
    global a1 #全局变量
    a1 = 0
    a2 = 0
    for i in SY:
        a2 = ZS[i]
        if (RCLz[(a2[0] - 1)] < 5 and a2[3] != 'stop' and a2[2] < 8.001):
            try:
                a2[3] = 'slow_stop'
                ZS[SY[a1]] = a2
            except:
                print('')
        if (RCLz[(a2[0] - 1)] <= 0 and a2[2] < 1.001 and a2[4] > 0):
            a2[3] = 'stop'
            ZS[SY[a1]] = a2
        if (a2[4] < 0):
            a2[4] = 0
            ZS[SY[a1]] = a2
        if car_dontZ(i):
            a2[4] = 0
            ZS[SY[a1]] = a2
        a1 += 1

def car_run():
    global a1 #全局变量
    a1 = 0
    a2 = 0
    for __count in range(len(SY)):
        a2 = ZS[SY[a1]]
        if (RCLz[(a2[0] - 1)] > 5 and a2[3] < 'stop'):
            a2[3] = 'go'
            ZS[SY[a1]] = a2
        if (a2[3] == 'go' and a2[4] > 35):
            a2[3] = 'run'
            ZS[SY[a1]] = a2
        a1 += 1

def ZTzx():
    global a1 #全局变量
    a1 = 0
    for __count in range(len(SY)):
        a2 = ZS[SY[a1]]
        if (a2[3] == 'run'):
            a2[4] = (a2[4] + (round(random.uniform((-3 / 10), (3 / 10)))))
        elif (a2[3] == 'stop') :
            if (RCLz[(a2[0] - 1)] > 5):
                a2[3] = 'go'
            a2[4] = 0
        elif (a2[3] == 'slow_stop' and a2[4] > 8 / 10) :
            a2[4] = (a2[4] - 8 / 10)
        elif (a2[3] == 'go') :
            a2[4] = (a2[4] + 10 / 10)
        else :
            pass
        a2[2] = (a2[2] - (a2[4] / 3.6) / 10)
        ZS[SY[a1]] = a2
        a1 += 1

def del_car():
    global a1 #全局变量
    a1 = 0
    a2 = 0
    for __count in range(len(SY)):
        a2 = ZS[SY[a1]]
        if (a2[2] < -40):
            del ZS[SY[a1]]
            try:
                del L1[L1.index(SY[a1])]
            except:
                pass
            try:
                del L2[L2.index(SY[a1])]
            except:
                pass
            try:
                del L3[L3.index(SY[a1])]
            except:
                pass
            try:
                del L4[L4.index(SY[a1])]
            except:
                pass
            del SY[a1]
            a1 -= 1
        a1 += 1

def car_dontZ(car):
    global a1 #全局变量
    a1 = 0
    a2 = ZS[car]
    a3 = 0
    if (car in L1):
        for __count in range(len(L1)):
            try:
                a3 = ZS[L1[a1]]
            except:
                del L1[a1]
                continue
            if (car != L1[a1]):
                if (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'run'):
                    a2[4] = (a2[4] - 6 / 10)
                    ZS[car] = a2
                elif (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'stop') :
                    return True
                else :
                    pass
            a1 += 1
    elif (car in L2) :
        for __count in range(len(L2)):
            try:
                a3 = ZS[L2[a1]]
            except:
                del L2[a1]
                continue
            if (car != L2[a1]):
                if (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'run'):
                    a2[4] = (a2[4] - 6 / 10)
                    ZS[car] = a2
                elif (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'stop') :
                    return True
                else :
                    pass
            a1 += 1
    elif (car in L3) :
        for __count in range(len(L3)):
            try:
                a3 = ZS[L3[a1]]
            except:
                del L3[a1]
                continue
            if (car != L3[a1]):
                if (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'run'):
                    a2[4] = (a2[4] - 6 / 10)
                    ZS[car] = a2
                elif (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'stop') :
                    return True
                else :
                    pass
            a1 += 1
    elif (car in L4) :
        for __count in range(len(L4)):
            try:
                a3 = ZS[L4[a1]]
            except:
                del L4[a1]
                continue
            if (car != L4[a1]):
                if (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'run'):
                    a2[4] = (a2[4] - 6 / 10)
                    ZS[car] = a2
                elif (a2[2] - 2 < a3[2] and a2[2] + 2 > a3[2] and a3[3] == 'stop') :
                    return True
                else :
                    pass
            a1 += 1
    else :
        pass

def RGL1(RGL):
    global a1 #全局变量
    a1 = 0
    a2 = 0
    for __count in range(4):
        if (RGL[a1] > 0.1):
            RGL[a1] = (RGL[a1] - (1 / 10))
            a2 = a1
        a1 += 1
    if (RGL[a2] < 0.1):
        RGL[a2] = 0
        if (a2 != 3):
            RGL[(a2 + 1)] = 27
        else :
            RGL[0] = 27
    return RGL

def RGL2(t, dc):
    global a2,a5,s1,s2,s3,s4 #全局变量
    a1 = (dc * 3 - 1)
    a2 = 0
    a4 = 0
    a5 = 0
    a6 = 0
    for __count in range(4):
        if (t[a5] > 0.1):
            t[a5] = (t[a5] - (1 / 10))
            a6 = a5
        if (t[a5] < 0.1):
            a2 += 1
        a5 += 1
    if (t[a6] < 0.1):
        t[a6] = 0
    if (a2 == 4):
        s1, s2, s3, s4 = 0, 0, 0, 0
        for i in L1:
            if (ZS[i][3] == 'stop'):
                s1 += 1
        for i in L2:
            if (ZS[i][3] == 'stop'):
                s2 += 1
        for i in L3:
            if (ZS[i][3] == 'stop'):
                s3 += 1
        for i in L4:
            if (ZS[i][3] == 'stop'):
                s4 += 1
        a4 = max(s1,s2,s3,s4)
        if (s1 >= a1 and s1 == a4):
            t[0] = ((s1 / 3) * 6)
        elif (s2 >= a1 and s2 == a4) :
            t[1] = ((s2 / 3) * 6)
        elif (s3 >= a1 and s3 == a4) :
            t[2] = ((s3 / 3) * 6)
        elif (s4 >= a1 and s4 == a4) :
            t[3] = ((s4 / 3) * 6)
        else :
            pass
    return t

def RGL3(t, dc):
    global a2,a5,s1,s2,s3,s4 #全局变量
    a1 = (dc * 3 - 1)
    a2 = 0
    a4 = 0
    a5 = 0
    a6 = 0
    for __count in range(4):
        if (t[a5] > 0.1):
            t[a5] = (t[a5] - (1 / 10))
            a6 = a5
        if (t[a5] < 0.1):
            a2 += 1
        a5 += 1
    if (t[a6] < 0.1):
        t[a6] = 0
    if (a2 == 4):
        s1, s2, s3, s4 = 0, 0, 0, 0
        for i in L1:
            if (ZS[i][3] == 'stop'):
                s1 += 1
        for i in L2:
            if (ZS[i][3] == 'stop'):
                s2 += 1
        for i in L3:
            if (ZS[i][3] == 'stop'):
                s3 += 1
        for i in L4:
            if (ZS[i][3] == 'stop'):
                s4 += 1
        a4 = max(s1,s2,s3,s4)
        if (s1 >= a1 and s1 == a4):
            t[0] = ((s1 / 3) * 6)
        elif (s2 >= a1 and s2 == a4) :
            t[1] = ((s2 / 3) * 6)
        elif (s3 >= a1 and s3 == a4) :
            t[2] = ((s3 / 3) * 6)
        elif (s4 >= a1 and s4 == a4) :
            t[3] = ((s4 / 3) * 6)
        else :
            a5 = [s1, s2, s3, s4]
            for i in a5:
                if (i == a4):
                    t[a5.index(i)] = (i * 4 - 2)
    return t

def PLK(zH):
    a1 = 0
    a2 = 0
    if (zH == 2):
        a3 = [['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱', '  ', '  ', '|', '  ', '  ', '︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱', '  ', '  ', '|', '  ', '  ', '︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '――', '┘', '  ', '  ', '︱', '  ', '  ', '└', '―', '――', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '――', '―', '  ', '  ', ' + ', '  ', '  ', '―', '――', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '――', '┐', '  ', '  ', '|', '  ', '  ', ' ┍', '―', '――', '――', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱', '  ', '  ', '|', '  ', '  ', '︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱', '  ', '  ', '|', '  ', '  ', '︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ']]
        for i in L1:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 20 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[3][a2 + 15] = '车'
                elif (a1[1] == 2) :
                    a3[4][a2 + 15] = '车'
                else :
                    pass
        for i in L2:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 6 and a1[2] > -18):
                if (a1[1] == 1):
                    a3[(a2 + 8)][13] = '车'
                elif (a1[1] == 2) :
                    a3[(a2 + 8)][14] = '车'
                else :
                    pass
        for i in L3:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 20 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[6][abs(a2 - 8)] = '车'
                elif (a1[1] == 2) :
                    a3[7][abs(a2 - 8)] = '车'
                else :
                    pass
        for i in L4:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 6 and a1[2] > -16):
                if (a1[1] == 1):
                    a3[abs((a2 - 2))][11] = '车'
                elif (a1[1] == 2) :
                    a3[abs((a2 - 2))][10] = '车'
                else :
                    pass
    elif (zH == 3) :
        a3 = [['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱ ', '  ', '  ', '  ', '|', '  ', '  ', '  ', ' ︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '┘ ', '  ', '  ', '  ', '|', '  ', '  ', '  ', ' └', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '――', '  ', '  ', '  ', ' + ', '  ', '  ', '  ', '――', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '   ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '┐ ', '  ', '  ', '  ', '|', '  ', '  ', '  ', ' ┍', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '︱ ', '  ', '  ', '  ', '|', '  ', '  ', '  ', '︱', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ']]
        for i in L1:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 18 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[2][a2 + 16] = '车'
                elif (a1[1] == 2) :
                    a3[3][a2 + 16] = '车'
                else :
                    a3[4][a2 + 16] = '车'
        for i in L2:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 4 and a1[2] > -18):
                if (a1[1] == 1):
                    a3[(a2 + 9)][13] = '车'
                elif (a1[1] == 2) :
                    a3[(a2 + 9)][14] = '车'
                else :
                    a3[(a2 + 9)][15] = '车'
        for i in L3:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 20 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[6][abs(a2 - 7)] = '车'
                elif (a1[1] == 2) :
                    a3[7][abs(a2 - 7)] = '车'
                else :
                    a3[8][abs(a2 - 7)] = '车'
        for i in L4:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 4 and a1[2] > -16):
                if (a1[1] == 1):
                    a3[abs((a2 - 1))][11] = '车'
                elif (a1[1] == 2) :
                    a3[abs((a2 - 1))][10] = '车'
                else :
                    a3[abs((a2 - 1))][9] = '车'
    else :
        a3 = [['――', '――', '――', '――', '――', '――', '――', '┘ ', '  ', '  ', '  ', '  ', '|', '  ', '  ', '  ', '  ', ' └', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '――', '', '  ', '  ', '  ', ' + ', '  ', '  ', '  ', '  ', '――', '――', '――', '――', '――', '――', '――', '――'], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '   ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['  ', '  ', '  ', '   ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  '], ['――', '――', '――', '――', '――', '――', '――', '┐ ', '   ', '  ', '  ', '  ', '|', '  ', '  ', '  ', '  ', ' ┍', '――', '――', '――', '――', '――', '――', '――']]
        for i in L1:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 16 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[1][a2 + 17] = '车'
                elif (a1[1] == 2) :
                    a3[2][a2 + 17] = '车'
                elif (a1[1] == 3) :
                    a3[3][a2 + 17] = '车'
                else :
                    a3[4][a2 + 17] = '车'
        for i in L2:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 2 and a1[2] > -18):
                if (a1[1] == 1):
                    a3[(a2 + 10)][13] = '车'
                elif (a1[1] == 2) :
                    a3[(a2 + 10)][14] = '车'
                elif (a1[1] == 3) :
                    a3[(a2 + 10)][15] = '车'
                else :
                    a3[(a2 + 10)][16] = '车'
        for i in L3:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 20 and a1[2] > -30):
                if (a1[1] == 1):
                    a3[6][abs(a2 - 6)] = '车'
                elif (a1[1] == 2) :
                    a3[7][abs(a2 - 6)] = '车'
                elif (a1[1] == 3) :
                    a3[8][abs(a2 - 6)] = '车'
                else :
                    a3[9][abs(a2 - 6)] = '车'
        for i in L4:
            a1 = ZS[i]
            a2 = math.floor(a1[2] / 2)
            if (a1[2] < 2 and a1[2] > -16):
                if (a1[1] == 1):
                    a3[abs(a2)][11] = '车'
                elif (a1[1] == 2) :
                    a3[abs(a2)][10] = '车'
                elif (a1[1] == 3) :
                    a3[abs(a2)][9] = '车'
                else :
                    a3[abs(a2)][8] = '车'
    return a3
def main():
    app = TrafficSimGUI()
    app.root.mainloop()
    time.sleep(0.01)

if (input('界面模式（1.操作台，2.window界面）') == '1'):
     ms = int(input('请输入模式（1-3）：'))
     dc = int(input('请输入最大路宽：（2-4）'))
     start(int(input('请输入模拟汽车数量：（建议大于50）')), int(input('请输入最大速度（大于30）km/h：')), dc)
     time1 = time.ctime()
     while True:
         print(RCLz)
         os.system('cls')
         for i in PLK(dc):
             a2 = ''
             for a1 in i:
                a2 = (a2 + a1)
             print(a2)
         if (ms == 1):
             RCLz = RGL1(RCLz)
         elif (ms == 2) :
            RCLz = RGL2(RCLz, dc)
         else :
             RCLz = RGL3(RCLz, dc)
         car_stop()
         car_run()
         ZTzx()
         for i in SY:
            car_dontZ(i)
         del_car()
         RCLz = RGL1(RCLz)
         time.sleep(0.05)
         if (SY == []):
            break
else :
    if __name__ == "__main__":
        try:
            main()
        except Exception as e:
            log(f"CRITICAL ERROR: {str(e)}", "ERROR")
            print(f"Error: {e}")
            input("Press Enter to exit...")
