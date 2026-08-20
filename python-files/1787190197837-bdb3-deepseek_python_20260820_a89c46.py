# -*- coding: utf-8 -*-
"""
BMAX 四驱车配置计算器（FMA底盘）
所有数据硬编码，无需外部文件
"""

import math

# ---------- 内置数据库 ----------
motors = {
    "Hyper-Dash 3 PRO": {"KV": 3800, "I_base": 2.5, "torque": 1.2},
    "Sprint-Dash": {"KV": 4200, "I_base": 3.8, "torque": 0.9},
    "Ultra-Dash": {"KV": 4300, "I_base": 5.0, "torque": 0.8},
    "Light-Dash PRO": {"KV": 3200, "I_base": 1.8, "torque": 1.5},
    "Atomic-Tuned": {"KV": 2800, "I_base": 1.3, "torque": 1.8},
}

batteries = {
    "田宫黑电(新)": {"V0": 3.2, "Rint": 120, "weight": 25},
    "松下 Evolta": {"V0": 3.25, "Rint": 70, "weight": 23},
    "富士通": {"V0": 3.2, "Rint": 90, "weight": 24},
    "劲量工业": {"V0": 3.2, "Rint": 100, "weight": 26},
}

gears = {
    "3.5:1": 3.5,
    "3.7:1": 3.7,
    "4.0:1": 4.0,
    "4.2:1": 4.2,
    "5.0:1": 5.0,
}

# 轮胎数据：名称, 编号, 直径(mm), 峰值附着 μ
tires = [
    {"name": "硬胎", "code": "15542", "dia": 30, "mu": 0.65},
    {"name": "超硬胎", "code": "15543", "dia": 30, "mu": 0.72},
    {"name": "软胎", "code": "15379", "dia": 30, "mu": 1.00},
    {"name": "低摩擦胎", "code": "15541", "dia": 30, "mu": 0.55},
    {"name": "大径硬胎", "code": "15544", "dia": 33, "mu": 0.65},
    {"name": "小径硬胎", "code": "15545", "dia": 26, "mu": 0.65},
]

# 轮径映射
wheel_map = {"小径": 26, "中径": 30, "大径": 33}

# ---------- 核心计算函数 ----------
def calculate(motor_name, gear_name, wheel_type, battery_name, W_car):
    # 提取参数
    motor = motors[motor_name]
    batt = batteries[battery_name]
    GR = gears[gear_name]
    D_wheel = wheel_map[wheel_type]

    KV = motor["KV"]
    I_base = motor["I_base"]
    torque_const = motor["torque"] / 1000  # 转为 N·m/A

    V0 = batt["V0"]
    Rint = batt["Rint"]
    W_batt = batt["weight"]

    # 工作电流（齿比修正）
    I_motor = I_base + (4.0 - GR) * 0.3
    I_motor = max(1.0, min(6.0, I_motor))

    # 负载电压
    V_load = V0 - I_motor * (Rint / 1000)
    V_load = max(1.5, V_load)

    # 马达转速
    N_motor = KV * V_load

    # 轮轴转速与极速
    N_wheel = N_motor / GR
    V_max = N_wheel * math.pi * D_wheel * 60 / 1_000_000

    # 轮上驱动力
    T_motor = torque_const * I_motor
    F_drive = T_motor * GR / (D_wheel / 2000)

    # 总重量（不含配重）
    W_total_base = W_car + W_batt

    # 所需最小附着系数（+20%安全余量）
    mu_req = F_drive / ((W_total_base / 1000) * 9.81) * 1.2

    # 轮胎选择
    best_front = 0
    best_rear = 0
    min_diff_f = 9999
    min_diff_r = 9999
    for i, t in enumerate(tires):
        if abs(t["dia"] - D_wheel) <= 2:
            if t["mu"] >= mu_req:
                diff = abs(t["mu"] - mu_req)
                if diff < min_diff_f:
                    min_diff_f = diff
                    best_front = i
            if t["mu"] >= mu_req * 1.1:
                diff = abs(t["mu"] - mu_req * 1.1)
                if diff < min_diff_r:
                    min_diff_r = diff
                    best_rear = i
    # 若未找到，兜底
    if best_front == 0:
        # 选直径最接近的硬胎或超硬胎（索引1,2）
        if abs(tires[1]["dia"] - D_wheel) <= abs(tires[2]["dia"] - D_wheel):
            best_front = 1
        else:
            best_front = 2
    if best_rear == 0:
        if abs(tires[2]["dia"] - D_wheel) <= abs(tires[3]["dia"] - D_wheel):
            best_rear = 2
        else:
            best_rear = 3

    mu_f = tires[best_front]["mu"]
    mu_r = tires[best_rear]["mu"]

    # 有效摩擦系数（考虑载荷转移）
    a_acc = F_drive / (W_total_base / 1000)
    h_cg = 20  # mm
    L_wb = 82   # mm
    Wf_ratio = 0.55 - (a_acc * h_cg) / (9.81 * L_wb)
    Wr_ratio = 0.45 + (a_acc * h_cg) / (9.81 * L_wb)
    Wf_ratio = max(0.3, min(0.7, Wf_ratio))
    Wr_ratio = max(0.3, min(0.7, Wr_ratio))
    mu_eff = (mu_f * Wf_ratio + mu_r * Wr_ratio) / (Wf_ratio + Wr_ratio)

    # 配重推荐
    X_cg_target = 46
    X_cg0 = 45 + (W_car - 140) * 0.1
    X_cg0 = max(42, min(50, X_cg0))
    m_front = 3
    num = X_cg_target * (W_total_base + m_front) - W_total_base * X_cg0 - m_front * 82
    den = -30 - X_cg_target
    if abs(den) > 0.001:
        m_tail = num / den
    else:
        m_tail = 0
    m_tail = max(0, min(20, m_tail))

    W_total_final = W_total_base + m_front + m_tail

    # 打滑验算
    F_traction = mu_eff * (W_total_final / 1000) * 9.81
    safety = "安全" if F_drive <= F_traction else "危险！建议降低齿比或换更软后胎"

    # 构造结果
    result = {
        "V_max": V_max,
        "front_tire": f"{tires[best_front]['name']}（{tires[best_front]['code']}）",
        "rear_tire": f"{tires[best_rear]['name']}（{tires[best_rear]['code']}）",
        "m_front": m_front,
        "m_tail": m_tail,
        "mu_eff": mu_eff,
        "safety": safety,
        "W_total": W_total_final,
    }
    return result

# ---------- 交互界面 ----------
def main():
    print("\n" + "="*50)
    print("      BMAX 四驱车配置计算器（FMA底盘）")
    print("="*50 + "\n")

    # 显示可选列表
    print("可选马达：")
    for i, name in enumerate(motors.keys(), 1):
        print(f"  {i}. {name}")
    motor_choice = input("请输入马达序号或名称：").strip()
    # 若输入数字，则取对应名称
    if motor_choice.isdigit():
        idx = int(motor_choice) - 1
        motor_list = list(motors.keys())
        if 0 <= idx < len(motor_list):
            motor_name = motor_list[idx]
        else:
            print("序号无效！")
            return
    else:
        motor_name = motor_choice
        if motor_name not in motors:
            print("未找到该马达！")
            return

    print("\n可选齿轮比：")
    for i, g in enumerate(gears.keys(), 1):
        print(f"  {i}. {g}")
    gear_choice = input("请输入齿轮序号或代号：").strip()
    if gear_choice.isdigit():
        idx = int(gear_choice) - 1
        gear_list = list(gears.keys())
        if 0 <= idx < len(gear_list):
            gear_name = gear_list[idx]
        else:
            print("序号无效！")
            return
    else:
        gear_name = gear_choice
        if gear_name not in gears:
            print("未找到该齿轮！")
            return

    print("\n可选轮径：小径, 中径, 大径")
    wheel_type = input("请输入轮径类别：").strip()
    if wheel_type not in wheel_map:
        print("轮径类别无效！")
        return

    print("\n可选电池：")
    for i, b in enumerate(batteries.keys(), 1):
        print(f"  {i}. {b}")
    batt_choice = input("请输入电池序号或名称：").strip()
    if batt_choice.isdigit():
        idx = int(batt_choice) - 1
        batt_list = list(batteries.keys())
        if 0 <= idx < len(batt_list):
            battery_name = batt_list[idx]
        else:
            print("序号无效！")
            return
    else:
        battery_name = batt_choice
        if battery_name not in batteries:
            print("未找到该电池！")
            return

    try:
        W_car = float(input("\n请输入不含电池的车重（g）：").strip())
        if W_car <= 0:
            print("车重必须大于0！")
            return
    except ValueError:
        print("请输入有效数字！")
        return

    # 计算
    result = calculate(motor_name, gear_name, wheel_type, battery_name, W_car)

    # 输出结果
    print("\n" + "="*50)
    print("【计算结果】")
    print("="*50)
    print(f"理论极速：{result['V_max']:.1f} km/h")
    print(f"推荐前轮胎：{result['front_tire']}")
    print(f"推荐后轮胎：{result['rear_tire']}")
    print(f"推荐配重：车头 {result['m_front']:.1f}g，尾部 {result['m_tail']:.1f}g")
    print(f"有效摩擦系数：{result['mu_eff']:.3f}")
    print(f"打滑验算：{result['safety']}")
    print(f"最终总重量（含配重）：{result['W_total']:.1f} g")
    print("="*50 + "\n")

    input("按 Enter 键退出...")

if __name__ == "__main__":
    main()