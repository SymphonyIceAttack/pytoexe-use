import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import math
import os
from datetime import datetime, timedelta

# ---------------------- 核心计算函数 ----------------------
def xy2az(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    az = math.degrees(math.atan2(dx, dy))
    az = 90 - az
    if az < 0:
        az += 360
    return az

def deg2dms(deg):
    d = int(deg)
    m = int((deg - d)*60)
    s = ((deg - d)*60 - m)*60
    return f"{d:03d}{m:02d}{s:06.3f}"

def deg2tsiyuan(deg):
    deg = deg % 360
    d = int(deg)
    m = int((deg - d)*60)
    s = ((deg - d)*60 - m)*60
    return d + m/100 + s/10000

def add_seconds_to_datetime(date_str, time_str, seconds):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    dt += timedelta(seconds=seconds)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")

def calculate_move_time(prev_target_count, move_min, move_max):
    if prev_target_count < 8:
        return random.randint((move_min - 1) * 60, move_min * 60)
    else:
        return random.randint(move_min * 60, move_max * 60)

def rand_sec(base, err=2):
    """
    生成带有随机误差的角度值
    :param base: 基准角度（度）
    :param err: 误差范围（秒），默认为±2秒
    :return: 带有误差的角度值（度）
    """
    return base + random.uniform(-err, err)/3600

def rand_distance(base, err_mm=0.5):
    """
    生成带有随机误差的距离值
    :param base: 基准距离（米）
    :param err_mm: 误差范围（毫米），默认为±0.5毫米
    :return: 带有误差的距离值（米）
    """
    return base + random.uniform(-err_mm, err_mm) / 1000

# ---------------------- 球气差改正相关函数 ----------------------
# 地球平均半径（米）
EARTH_RADIUS = 6371000.0

def calculate_curvature_correction(horizontal_distance):
    """
    计算球差（地球曲率改正）
    Δh_球 = D² / (2R)
    :param horizontal_distance: 水平距离（米）
    :return: 球差改正值（米）
    """
    return horizontal_distance ** 2 / (2 * EARTH_RADIUS)

def calculate_refraction_correction(horizontal_distance, refraction_coefficient=0.14):
    """
    计算气差（大气折光改正）
    Δh_气 = -k * D² / (2R)
    :param horizontal_distance: 水平距离（米）
    :param refraction_coefficient: 折光系数，通常取0.14
    :return: 气差改正值（米）
    """
    return -refraction_coefficient * horizontal_distance ** 2 / (2 * EARTH_RADIUS)

def calculate_combined_correction(horizontal_distance, refraction_coefficient=0.14):
    """
    计算球气差综合改正
    Δh = Δh_球 + Δh_气 = (1 - k) * D² / (2R)
    :param horizontal_distance: 水平距离（米）
    :param refraction_coefficient: 折光系数，通常取0.14
    :return: 球气差综合改正值（米）
    """
    curvature = calculate_curvature_correction(horizontal_distance)
    refraction = calculate_refraction_correction(horizontal_distance, refraction_coefficient)
    return curvature + refraction

def horizontal_to_slant_distance(horizontal_distance, vertical_angle_deg, apply_curvature=True, apply_refraction=True, refraction_coefficient=0.14):
    """
    从平距反算斜距，可选择是否添加球气差改正
    :param horizontal_distance: 水平距离（米）
    :param vertical_angle_deg: 竖直角（度），仰角为正，俯角为负
    :param apply_curvature: 是否应用球差改正
    :param apply_refraction: 是否应用气差改正
    :param refraction_coefficient: 折光系数
    :return: 斜距（米）
    """
    vertical_angle_rad = math.radians(vertical_angle_deg)
    
    # 计算球气差改正
    correction = 0.0
    if apply_curvature:
        correction += calculate_curvature_correction(horizontal_distance)
    if apply_refraction:
        correction += calculate_refraction_correction(horizontal_distance, refraction_coefficient)
    
    # 原始高差
    dh_raw = horizontal_distance * math.tan(vertical_angle_rad)
    
    # 考虑球气差后的高差
    dh_corrected = dh_raw + correction
    
    # 反算斜距
    slant_distance = horizontal_distance / math.cos(vertical_angle_rad)
    
    return slant_distance, dh_corrected

def generate_vertical_with_i(zenith_true, i_limit):
    valid = False
    attempts = 0
    v_l = 0.0
    v_r = 0.0
    while not valid and attempts < 100:
        v_l = rand_sec(zenith_true)
        v_r = rand_sec(360 - zenith_true)
        i = ((v_l + v_r - 360) / 2) * 3600
        if abs(i) <= i_limit:
            valid = True
        attempts += 1
    if not valid:
        return v_l, v_r, False
    return v_l, v_r, True

def generate_obs_limited(az_true, dis, zenith_true, two_c_limit, i_limit):
    valid = False
    attempts = 0
    az_l = 0.0
    az_r = 0.0
    v_l = 0.0
    v_r = 0.0
    while not valid and attempts < 100:
        az_l = rand_sec(az_true)
        az_r = rand_sec(az_true + 180)
        two_c = (az_l - (az_r - 180)) * 3600
        if abs(two_c) > two_c_limit:
            attempts += 1
            continue
        v_l = rand_sec(zenith_true)
        v_r = rand_sec(360 - zenith_true)
        i = ((v_l + v_r - 360) / 2) * 3600
        if abs(i) <= i_limit:
            valid = True
        attempts += 1
    if not valid:
        return az_l, az_r, v_l, v_r, False
    return az_l, az_r, v_l, v_r, True

# ---------------------- 生成SUC主函数（铁四院格式-全圆观测法-归零观测） ----------------------
def generate_suc():
    try:
        n_set = int(ent_set.get())
        hi = float(ent_hi.get())
        hr = float(ent_hr.get())
        prism_corr = int(ent_prism.get())
        zero_limit = float(ent_zero.get())
        two_c_limit = float(ent_2c.get())
        two_c_diff_limit = float(ent_2c_diff.get())
        i_limit = float(ent_i.get())
        i_diff_limit = float(ent_i_diff.get())
        
        # 测回间限差
        two_c_inter_limit = float(ent_2c_inter.get())
        i_inter_limit = float(ent_i_inter.get())
        h_diff_limit = float(ent_h_diff.get())
        v_diff_limit = float(ent_v_diff.get())
        
        obs_time_min = int(ent_obs_min.get())
        obs_time_max = int(ent_obs_max.get())
        move_time_min = int(ent_move_min.get())
        move_time_max = int(ent_move_max.get())
        pts_text = txt_points.get("1.0", tk.END).strip()
        
        # 球气差改正参数
        apply_curvature = curvature_correction_var.get()
        apply_refraction = refraction_correction_var.get()
        refraction_k = float(ent_refraction_k.get())


        # 按空行分割测站数据
        station_blocks = []
        current_block = []
        for line in pts_text.splitlines():
            line = line.strip()
            if line:
                current_block.append(line)
            else:
                if current_block:
                    station_blocks.append(current_block)
                    current_block = []
        if current_block:
            station_blocks.append(current_block)

        if not station_blocks:
            messagebox.showerror("错误", "未找到测站数据！")
            return

        # 处理每个测站数据块
        all_points = []
        sta_list = []
        station_targets = {}  # 保存每个测站对应的目标点
        for block in station_blocks:
            if not block:
                continue
            # 第一行是测站坐标
            sta_name, x, y, h = block[0].split()
            all_points.append([sta_name, float(x), float(y), float(h)])
            sta_list.append(sta_name)
            # 后续行是目标点
            targets = []
            for line in block[1:]:
                if line:
                    name, x, y, h = line.split()
                    all_points.append([name, float(x), float(y), float(h)])
                    targets.append(name)
            station_targets[sta_name] = targets

        pt_dict = {p[0]:(p[1],p[2],p[3]) for p in all_points}
        
        current_date = ent_date.get().strip()
        current_time = ent_time_start.get().strip()
        sort_by_azimuth = sort_by_azimuth_var.get()
        prev_target_count = None

        for idx_sta, sta_name in enumerate(sta_list):
            if sta_name not in pt_dict:
                messagebox.showerror("错误", f"测站点 {sta_name} 未在坐标表中！")
                return
            x_sta, y_sta, h_sta = pt_dict[sta_name]

            # 只使用当前测站数据块中的目标点
            target_names = station_targets[sta_name]
            target_list = []
            for name in target_names:
                x, y, h = pt_dict[name]
                target_list.append((name, x, y, h))
            n_target = len(target_list)

            obs_data = []
            for target_name, x_t, y_t, h_t in target_list:
                az = xy2az(x_sta, y_sta, x_t, y_t)
                horizontal_distance = math.hypot(x_t - x_sta, y_t - y_sta)
                
                # 添加距离随机误差（±0.5毫米）
                horizontal_distance = rand_distance(horizontal_distance, err_mm=0.5)
                
                dh = (h_t + hr) - (h_sta + hi)
                
                # 计算球气差改正
                correction = 0.0
                if apply_curvature:
                    correction += calculate_curvature_correction(horizontal_distance)
                if apply_refraction:
                    correction += calculate_refraction_correction(horizontal_distance, refraction_k)
                
                # 应用球气差改正后的高差
                dh_corrected = dh + correction
                
                if horizontal_distance > 0:
                    # 根据改正后的高差计算竖直角和天顶距
                    vertical_angle_rad = math.atan2(dh_corrected, horizontal_distance)
                    vertical_angle_deg = math.degrees(vertical_angle_rad)
                    zenith_angle = 90 - vertical_angle_deg
                    
                    # 从平距反算斜距
                    slant_distance = horizontal_distance / math.cos(vertical_angle_rad)
                else:
                    zenith_angle = 90
                    slant_distance = horizontal_distance
                
                obs_data.append((target_name, az, slant_distance, zenith_angle))
            
            if sort_by_azimuth:
                obs_data.sort(key=lambda x: x[1])

            total_observations = n_set * (n_target + 1) * 2
            total_seconds = random.randint(total_observations * obs_time_min, total_observations * obs_time_max)
            end_date, time_end = add_seconds_to_datetime(current_date, current_time, total_seconds)

            suc_lines = []
            
            suc_lines.append(f"{sta_name},{n_set},{n_target},{hi:.1f}")
            suc_lines.append(f"Start,{current_date},{current_time}")

            prev_set_obs_list = None
            
            for set_no in range(1, n_set+1):
                suc_lines.append(f"{set_no}")
                
                set_obs_list = []
                az_l_zero = 0.0
                az_r_zero = 0.0
                v_l_zero = 0.0
                v_r_zero = 0.0
                valid_set = False
                set_attempts = 0
                
                first_target_name, first_az_true, first_dis, first_zenith = obs_data[0]
                
                while not valid_set and set_attempts < 1000:
                    set_obs_list = []
                    all_valid = True
                    
                    for target_name, az_true, dis, zenith_true in obs_data:
                        az_l, az_r, v_l, v_r, ok1 = generate_obs_limited(
                            az_true, dis, zenith_true, two_c_limit, i_limit
                        )
                        if not ok1:
                            all_valid = False
                            break
                        set_obs_list.append((target_name, az_l, az_r, v_l, v_r, dis, zenith_true))
                    
                    if not all_valid:
                        set_attempts += 1
                        continue
                    
                    first_az_l, first_az_r, first_v_l, first_v_r = set_obs_list[0][1], set_obs_list[0][2], set_obs_list[0][3], set_obs_list[0][4]
                    
                    valid_zero_l = False
                    temp_az_l_zero = 0.0
                    attempts_zero = 0
                    while not valid_zero_l and attempts_zero < 100:
                        temp_az_l_zero = rand_sec(first_az_true)
                        zero_diff = abs(temp_az_l_zero - first_az_l) * 3600
                        if zero_diff <= zero_limit:
                            valid_zero_l = True
                        attempts_zero += 1
                    if not valid_zero_l:
                        set_attempts += 1
                        continue
                    
                    valid_zero_r = False
                    temp_az_r_zero = 0.0
                    attempts_zero = 0
                    while not valid_zero_r and attempts_zero < 100:
                        temp_az_r_zero = rand_sec(first_az_true + 180)
                        # 使用统一的误差范围（±1秒），保持与generate_obs_limited一致
                        temp_v_l_zero = rand_sec(first_zenith)
                        temp_v_r_zero = rand_sec(360 - first_zenith)
                        
                        two_c_zero = (temp_az_l_zero - (temp_az_r_zero - 180)) * 3600
                        if abs(two_c_zero) <= two_c_limit:
                            valid_zero_r = True
                        attempts_zero += 1
                    if not valid_zero_r:
                        set_attempts += 1
                        continue
                    
                    all_obs_with_zero = set_obs_list.copy()
                    all_obs_with_zero.append((first_target_name, temp_az_l_zero, temp_az_r_zero, temp_v_l_zero, temp_v_r_zero, first_dis, first_zenith))
                    
                    valid_within = True
                    for i in range(len(all_obs_with_zero)):
                        for j in range(len(all_obs_with_zero)):
                            if i != j:
                                name_i, az_l_i, az_r_i, v_l_i, v_r_i, _, _ = all_obs_with_zero[i]
                                name_j, az_l_j, az_r_j, v_l_j, v_r_j, _, _ = all_obs_with_zero[j]
                                
                                two_c_i = (az_l_i - (az_r_i - 180)) * 3600
                                two_c_j = (az_l_j - (az_r_j - 180)) * 3600
                                two_c_diff = abs(two_c_i - two_c_j)
                                if two_c_diff > two_c_diff_limit:
                                    valid_within = False
                                    break
                                
                                i_i = ((v_l_i + v_r_i - 360) / 2) * 3600
                                i_j = ((v_l_j + v_r_j - 360) / 2) * 3600
                                i_diff = abs(i_i - i_j)
                                if i_diff > i_diff_limit:
                                    valid_within = False
                                    break
                        if not valid_within:
                            break
                    
                    if not valid_within:
                        set_attempts += 1
                        continue
                    
                    if prev_set_obs_list is not None:
                        valid_inter = True
                        for curr_target, curr_az_l, curr_az_r, curr_v_l, curr_v_r, _, _ in set_obs_list:
                            for prev_target, prev_az_l, prev_az_r, prev_v_l, prev_v_r, _, _ in prev_set_obs_list:
                                if curr_target == prev_target:
                                    two_c_curr = (curr_az_l - (curr_az_r - 180)) * 3600
                                    two_c_prev = (prev_az_l - (prev_az_r - 180)) * 3600
                                    two_c_inter_diff = abs(two_c_curr - two_c_prev)
                                    if two_c_inter_diff > two_c_inter_limit:
                                        valid_inter = False
                                        break
                                    
                                    i_curr = ((curr_v_l + curr_v_r - 360) / 2) * 3600
                                    i_prev = ((prev_v_l + prev_v_r - 360) / 2) * 3600
                                    i_inter_diff = abs(i_curr - i_prev)
                                    if i_inter_diff > i_inter_limit:
                                        valid_inter = False
                                        break
                                    
                                    az_mean_curr = (curr_az_l + (curr_az_r - 180)) / 2
                                    az_mean_prev = (prev_az_l + (prev_az_r - 180)) / 2
                                    h_diff_raw = az_mean_curr - az_mean_prev
                                    h_diff_raw = ((h_diff_raw + 180) % 360) - 180
                                    h_diff = abs(h_diff_raw) * 3600
                                    if h_diff > h_diff_limit:
                                        valid_inter = False
                                        break
                                    
                                    v_mean_curr = (curr_v_l + curr_v_r) / 2
                                    v_mean_prev = (prev_v_l + prev_v_r) / 2
                                    v_diff = abs(v_mean_curr - v_mean_prev) * 3600
                                    if v_diff > v_diff_limit:
                                        valid_inter = False
                                        break
                            if not valid_inter:
                                break
                        
                        if not valid_inter:
                            set_attempts += 1
                            continue
                    
                    az_l_zero = temp_az_l_zero
                    az_r_zero = temp_az_r_zero
                    v_l_zero = temp_v_l_zero
                    v_r_zero = temp_v_r_zero
                    valid_set = True
                    set_attempts += 1
                
                if not valid_set:
                    messagebox.showwarning("警告", f"测站{sta_name}测回{set_no}限差难以满足！")
                
                prev_set_obs_list = set_obs_list.copy()
                prev_set_obs_list.append((first_target_name, az_l_zero, az_r_zero, v_l_zero, v_r_zero, first_dis, first_zenith))
                
                for target_name, az_l, az_r, v_l, v_r, dis, zenith_true in set_obs_list:
                    az_l_tsy = deg2tsiyuan(az_l)
                    v_l_tsy = deg2tsiyuan(v_l)
                    line_l = f"{target_name:12s},{az_l_tsy:11.7f},{v_l_tsy:11.7f},{dis:11.5f},   0.0000,      0.0"
                    suc_lines.append(line_l)
                
                az_l_zero_tsy = deg2tsiyuan(az_l_zero)
                v_l_zero_tsy = deg2tsiyuan(v_l_zero)
                line_l_zero = f"{first_target_name:12s},{az_l_zero_tsy:11.7f},{v_l_zero_tsy:11.7f},{first_dis:11.5f},   0.0000,      0.0"
                suc_lines.append(line_l_zero)
                
                az_r_zero_tsy = deg2tsiyuan(az_r_zero)
                v_r_zero_tsy = deg2tsiyuan(v_r_zero)
                line_r_zero = f"{first_target_name:12s},{az_r_zero_tsy:11.7f},{v_r_zero_tsy:11.7f},{first_dis:11.5f},   0.0000,      0.0"
                suc_lines.append(line_r_zero)
                
                for target_name, az_l, az_r, v_l, v_r, dis, zenith_true in reversed(set_obs_list[1:]):
                    az_r_tsy = deg2tsiyuan(az_r)
                    v_r_tsy = deg2tsiyuan(v_r)
                    line_r = f"{target_name:12s},{az_r_tsy:11.7f},{v_r_tsy:11.7f},{dis:11.5f},   0.0000,      0.0"
                    suc_lines.append(line_r)
                
                valid_zero_r2 = False
                attempts = 0
                az_r_zero2 = 0.0
                while not valid_zero_r2 and attempts < 100:
                    az_r_zero2 = rand_sec(first_az_true + 180)
                    if True:
                        valid_zero_r2 = True
                    attempts += 1
                
                # 使用统一的误差范围（±1秒）
                v_r_zero2 = rand_sec(360 - first_zenith)
                az_r_zero2_tsy = deg2tsiyuan(az_r_zero2)
                v_r_zero2_tsy = deg2tsiyuan(v_r_zero2)
                line_r_zero2 = f"{first_target_name:12s},{az_r_zero2_tsy:11.7f},{v_r_zero2_tsy:11.7f},{first_dis:11.5f},   0.0000,      0.0"
                suc_lines.append(line_r_zero2)

            suc_lines.append(f"End,{end_date},{time_end}")

            filename = f"{sta_name}.SUC"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(suc_lines))

            # 修改文件修改时间为测量结束时间
            if end_date and time_end:
                try:
                    dt_str = f"{end_date} {time_end}"
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    timestamp = dt.timestamp()
                    os.utime(filename, (timestamp, timestamp))
                except:
                    pass

            if idx_sta < len(sta_list) - 1:
                move_time = calculate_move_time(n_target, move_time_min, move_time_max)
                current_date, current_time = add_seconds_to_datetime(end_date, time_end, move_time)
            
            prev_target_count = n_target

        messagebox.showinfo("完成", f"已生成{len(sta_list)}个SUC文件（铁四院格式-全圆观测法-归零观测）\n文件名格式：测站名.SUC")

    except Exception as e:
        messagebox.showerror("异常", str(e))

# ---------------------- 窗体界面布局 ----------------------
root = tk.Tk()
root.title("多测回导线SUC生成工具")
root.geometry("850x1050")
root.configure(bg="#ffffff")
root.update_idletasks()

sort_by_azimuth_var = tk.BooleanVar(value=True)


style = ttk.Style()
style.theme_use('clam')

style.configure('TFrame', background='#ffffff')
style.configure('TLabel', background='#ffffff', font=('微软雅黑', 10), foreground='#1e293b')
style.configure('TLabelFrame', background='#ffffff', foreground='#334155', font=('微软雅黑', 11, 'bold'), borderwidth=1, relief='solid', bordercolor='#e2e8f0')
style.configure('TLabelFrame.Label', background='#ffffff', foreground='#334155', padding=(8, 4))
style.configure('TLabelFrame.TFrame', background='#ffffff')
style.configure('TButton', font=('微软雅黑', 11, 'bold'), padding=(16, 8))
style.configure('TEntry', fieldbackground='white', font=('微软雅黑', 10), borderwidth=1)
style.map('TButton', 
          background=[('active', '#059669'), ('!active', '#10b981'), ('disabled', '#d1d5db')],
          foreground=[('active', 'white'), ('!active', 'white'), ('disabled', '#9ca3af')],
          relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
style.map('TEntry', 
          fieldbackground=[('focus', '#ffffff'), ('!focus', '#ffffff')],
          bordercolor=[('focus', '#10b981'), ('!focus', '#e2e8f0')])
style.map('TCheckbutton', 
          background=[('active', '#ffffff'), ('!active', '#ffffff')],
          foreground=[('active', '#10b981'), ('!active', '#1e293b')])
style.configure('Header.TFrame', background='#1e40af')
style.configure('Header.TLabel', background='#1e40af', font=('微软雅黑', 18, 'bold'), foreground='#ffffff')
style.configure('Card.TFrame', background='#ffffff', borderwidth=0, relief='solid')
style.configure('Section.TFrame', background='#ffffff', borderwidth=1, relief='solid', bordercolor='#e2e8f0')

# 球气差改正相关变量
curvature_correction_var = tk.BooleanVar(value=True)
refraction_correction_var = tk.BooleanVar(value=True)

frm_header = ttk.Frame(root, style='Header.TFrame', padding=(20, 15, 20, 15))
frm_header.pack(fill="x")
title_label = tk.Label(frm_header, text="多测回导线SUC生成工具", font=('微软雅黑', 18, 'bold'), bg='#1e40af', fg='#ffffff')
title_label.pack(side="left")
pro_label = tk.Label(frm_header, text="PRO", font=('微软雅黑', 10, 'bold'), bg='#3b82f6', fg='#ffffff', padx=8, pady=2)
pro_label.pack(side="left", padx=10)

frm_main = ttk.Frame(root, padding=15)
frm_main.pack(fill="both", expand=True, padx=20, pady=10)

frm_params = ttk.Frame(frm_main, padding=15)
frm_params.pack(fill="x", pady=5)
frm_params.configure(style='Card.TFrame')

ttk.Label(frm_params, text="测回数：").grid(row=0,column=0,padx=8,pady=5)
ent_set = ttk.Entry(frm_params, width=8)
ent_set.insert(0,"2")
ent_set.grid(row=0,column=1,padx=8,pady=5)

ttk.Label(frm_params, text="仪器高(m)：").grid(row=0,column=2,padx=8,pady=5)
ent_hi = ttk.Entry(frm_params, width=10)
ent_hi.insert(0,"1.6")
ent_hi.grid(row=0,column=3,padx=8,pady=5)

ttk.Label(frm_params, text="棱镜高(m)：").grid(row=0,column=4,padx=8,pady=5)
ent_hr = ttk.Entry(frm_params, width=10)
ent_hr.insert(0,"0")
ent_hr.grid(row=0,column=5,padx=8,pady=5)

ttk.Label(frm_params, text="棱镜常数(mm)：").grid(row=0,column=6,padx=8,pady=5)
ent_prism = ttk.Entry(frm_params, width=8)
ent_prism.insert(0,"0")
ent_prism.grid(row=0,column=7,padx=8,pady=5)

frm_settings = ttk.Frame(frm_main)
frm_settings.pack(fill="x", pady=5)

frm_limits = ttk.LabelFrame(frm_settings, text=" 测回内限差设置 ", padding=15)
frm_limits.pack(side="left", fill="both", expand=True, padx=5)

ttk.Label(frm_limits, text="半测回归零差：").grid(row=0,column=0,padx=5,pady=6,sticky="e")
ent_zero = ttk.Entry(frm_limits, width=8)
ent_zero.insert(0,"6")
ent_zero.grid(row=0,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(秒)").grid(row=0,column=2,padx=2,pady=6)

ttk.Label(frm_limits, text="2C值限差：").grid(row=1,column=0,padx=5,pady=6,sticky="e")
ent_2c = ttk.Entry(frm_limits, width=8)
ent_2c.insert(0,"12")
ent_2c.grid(row=1,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(秒)").grid(row=1,column=2,padx=2,pady=6)

ttk.Label(frm_limits, text="不同方向2C互差：").grid(row=2,column=0,padx=5,pady=6,sticky="e")
ent_2c_diff = ttk.Entry(frm_limits, width=8)
ent_2c_diff.insert(0,"9")
ent_2c_diff.grid(row=2,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(秒)").grid(row=2,column=2,padx=2,pady=6)

ttk.Label(frm_limits, text="竖盘指标差i值：").grid(row=3,column=0,padx=5,pady=6,sticky="e")
ent_i = ttk.Entry(frm_limits, width=8)
ent_i.insert(0,"12")
ent_i.grid(row=3,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(秒)").grid(row=3,column=2,padx=2,pady=6)

ttk.Label(frm_limits, text="i值互差：").grid(row=4,column=0,padx=5,pady=6,sticky="e")
ent_i_diff = ttk.Entry(frm_limits, width=8)
ent_i_diff.insert(0,"12")
ent_i_diff.grid(row=4,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(秒)").grid(row=4,column=2,padx=2,pady=6)

ttk.Label(frm_limits, text="正倒镜距离较差：").grid(row=5,column=0,padx=5,pady=6,sticky="e")
ent_dist_diff = ttk.Entry(frm_limits, width=8)
ent_dist_diff.insert(0,"1")
ent_dist_diff.grid(row=5,column=1,padx=5,pady=6)
ttk.Label(frm_limits, text="(mm)").grid(row=5,column=2,padx=2,pady=6)

frm_limits_inter = ttk.LabelFrame(frm_settings, text=" 测回间限差设置 ", padding=15)
frm_limits_inter.pack(side="right", fill="both", expand=True, padx=5)

ttk.Label(frm_limits_inter, text="同方向2C互差：").grid(row=0,column=0,padx=5,pady=6,sticky="e")
ent_2c_inter = ttk.Entry(frm_limits_inter, width=8)
ent_2c_inter.insert(0,"9")
ent_2c_inter.grid(row=0,column=1,padx=5,pady=6)
ttk.Label(frm_limits_inter, text="(秒)").grid(row=0,column=2,padx=2,pady=6)

ttk.Label(frm_limits_inter, text="同方向i互差：").grid(row=1,column=0,padx=5,pady=6,sticky="e")
ent_i_inter = ttk.Entry(frm_limits_inter, width=8)
ent_i_inter.insert(0,"12")
ent_i_inter.grid(row=1,column=1,padx=5,pady=6)
ttk.Label(frm_limits_inter, text="(秒)").grid(row=1,column=2,padx=2,pady=6)

ttk.Label(frm_limits_inter, text="水平方向值互差：").grid(row=2,column=0,padx=5,pady=6,sticky="e")
ent_h_diff = ttk.Entry(frm_limits_inter, width=8)
ent_h_diff.insert(0,"6")
ent_h_diff.grid(row=2,column=1,padx=5,pady=6)
ttk.Label(frm_limits_inter, text="(秒)").grid(row=2,column=2,padx=2,pady=6)

ttk.Label(frm_limits_inter, text="竖直角值互差：").grid(row=3,column=0,padx=5,pady=6,sticky="e")
ent_v_diff = ttk.Entry(frm_limits_inter, width=8)
ent_v_diff.insert(0,"9")
ent_v_diff.grid(row=3,column=1,padx=5,pady=6)
ttk.Label(frm_limits_inter, text="(秒)").grid(row=3,column=2,padx=2,pady=6)

ttk.Label(frm_limits_inter, text="距离较差：").grid(row=4,column=0,padx=5,pady=6,sticky="e")
ent_dist_inter = ttk.Entry(frm_limits_inter, width=8)
ent_dist_inter.insert(0,"1")
ent_dist_inter.grid(row=4,column=1,padx=5,pady=6)
ttk.Label(frm_limits_inter, text="(mm)").grid(row=4,column=2,padx=2,pady=6)

frm_time_options = ttk.LabelFrame(frm_main, text=" 时间设置与选项 ", padding=15)
frm_time_options.pack(fill="x", pady=5)

frm_time = ttk.Frame(frm_time_options)
frm_time.pack(side="left", padx=20)

ttk.Label(frm_time, text="日期(YYYY-MM-DD)：").grid(row=0,column=0,padx=5,pady=6,sticky="e")
ent_date = ttk.Entry(frm_time, width=14)
ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
ent_date.grid(row=0,column=1,padx=5,pady=6)

ttk.Label(frm_time, text="开始时间(HH:MM:SS)：").grid(row=1,column=0,padx=5,pady=6,sticky="e")
ent_time_start = ttk.Entry(frm_time, width=14)
ent_time_start.insert(0, datetime.now().strftime("%H:%M:%S"))
ent_time_start.grid(row=1,column=1,padx=5,pady=6)

ttk.Label(frm_time, text="棱镜测量时间(秒)：").grid(row=2,column=0,padx=5,pady=6,sticky="e")
ent_obs_min = ttk.Entry(frm_time, width=6)
ent_obs_min.insert(0,"7")
ent_obs_min.grid(row=2,column=1,padx=2,pady=6)
ttk.Label(frm_time, text="-").grid(row=2,column=2,pady=6)
ent_obs_max = ttk.Entry(frm_time, width=6)
ent_obs_max.insert(0,"10")
ent_obs_max.grid(row=2,column=3,padx=2,pady=6)

ttk.Label(frm_time, text="搬站时间(分钟)：").grid(row=3,column=0,padx=5,pady=6,sticky="e")
ent_move_min = ttk.Entry(frm_time, width=6)
ent_move_min.insert(0,"5")
ent_move_min.grid(row=3,column=1,padx=2,pady=6)
ttk.Label(frm_time, text="-").grid(row=3,column=2,pady=6)
ent_move_max = ttk.Entry(frm_time, width=6)
ent_move_max.insert(0,"7")
ent_move_max.grid(row=3,column=3,padx=2,pady=6)

frm_options = ttk.Frame(frm_time_options)
frm_options.pack(side="right", padx=40)

chk_sort = ttk.Checkbutton(
    frm_options, 
    text="按方位角排序（否则按粘贴顺序）", 
    variable=sort_by_azimuth_var
)
chk_sort.grid(row=1,column=0,pady=8, sticky="w")

ttk.Label(frm_options, text="提示：按空行分隔测站数据").grid(row=2,column=0,pady=8, sticky="w")
ttk.Label(frm_options, text="每段首行为测站坐标").grid(row=3,column=0, sticky="w")

# 球气差改正设置
frm_correction = ttk.LabelFrame(frm_main, text=" 球气差改正设置 ", padding=15)
frm_correction.pack(fill="x", pady=5)

chk_curvature = ttk.Checkbutton(
    frm_correction,
    text="球差改正",
    variable=curvature_correction_var
)
chk_curvature.grid(row=0, column=0, padx=20, pady=5, sticky="w")

chk_refraction = ttk.Checkbutton(
    frm_correction,
    text="气差改正",
    variable=refraction_correction_var
)
chk_refraction.grid(row=0, column=1, padx=20, pady=5, sticky="w")

ttk.Label(frm_correction, text="折光系数k：").grid(row=0, column=2, padx=5, pady=5, sticky="e")
ent_refraction_k = ttk.Entry(frm_correction, width=10)
ent_refraction_k.insert(0, "0.14")
ent_refraction_k.grid(row=0, column=3, padx=5, pady=5)

frm_pts = ttk.LabelFrame(frm_main, text=" 坐标输入 ", padding=12)
frm_pts.pack(fill="both", expand=True, pady=5)

txt_points = scrolledtext.ScrolledText(frm_pts, height=10, font=('Consolas', 10), bg='#ffffff', fg='#2c3e50')
txt_points.pack(fill="both", expand=True)
sample = """测站1 1000.000 2000.000 50.000
目标1 1050.000 2020.000 51.000
目标2 1030.000 2080.000 49.500

测站2 1100.000 2100.000 52.000
目标A 1150.000 2120.000 53.000
目标B 1130.000 2180.000 51.500
"""
txt_points.insert("1.0", sample)

frm_btn = ttk.Frame(frm_main, padding=15)
frm_btn.pack(fill="x", pady=5)
frm_btn.configure(style='Card.TFrame')
btn_gen = ttk.Button(frm_btn, text="一键生成SUC文件", command=generate_suc)
btn_gen.pack()

root.mainloop()
