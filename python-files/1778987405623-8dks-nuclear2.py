import tkinter as tk
import time

# ======================
# 基础参数
# ======================
WIDTH, HEIGHT = 900, 650

INIT_TEMP = 26.0
BOIL_TEMP = 100.0
BOIL_TIME = 1.0  # 1 秒达到沸点

NEUTRON_DECAY = 0.98
HEAT_INCREASE_RATE = 0.03
PUMP_COOLING = 1.0
NATURAL_COOLING = 0.992
EXPLOSION_THRESHOLD = 300

# ======================
# 主窗口
# ======================
root = tk.Tk()
root.title("核电站模拟器")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="lightgray")
canvas.pack()

# ======================
# 状态变量
# ======================
control_rod_position = 50
neutron_count = 0.0
heat = INIT_TEMP
exploded = False

reactor_started = False
control_rods_enabled = False
pump_on = False
scram_triggered = False

reactor_start_time = 0

# ======================
# UI：发电量显示
# ======================
canvas.create_rectangle(20, 20, 260, 70, fill="black")
power_text = canvas.create_text(
    140, 45, text="发电量: 0 MW", fill="yellow", font=("Arial", 14, "bold")
)

# ======================
# UI：温度显示
# ======================
canvas.create_rectangle(20, 80, 260, 130, fill="#444444")
temperature_text = canvas.create_text(
    140, 105, text=f"当前温度: {int(heat)} °C", fill="cyan", font=("Arial", 14, "bold")
)

# ======================
# UI：控制棒
# ======================
control_rod_scale = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL)
control_rod_scale.set(control_rod_position)
control_rod_scale.place(x=30, y=HEIGHT - 60)

# ======================
# UI：爆炸提示
# ======================
explosion_text = canvas.create_text(
    WIDTH - 140, HEIGHT - 50, text="", fill="red", font=("Arial", 24, "bold")
)

# ======================
# 按钮逻辑
# ======================
def start_reactor():
    global reactor_started, reactor_start_time
    if not reactor_started and not scram_triggered:
        reactor_started = True
        reactor_start_time = time.time()


def enable_control_rods():
    global control_rods_enabled
    control_rods_enabled = True


def toggle_pump():
    global pump_on
    pump_on = not pump_on
    pump_btn.config(text="水泵 ON" if pump_on else "水泵 OFF")


def emergency_scram():
    global scram_triggered, neutron_count, control_rod_position
    scram_triggered = True
    neutron_count = 0
    control_rod_position = 0
    control_rod_scale.set(0)
    scram_btn.config(text="A3-5 已触发", state="disabled")


# ======================
# 控制按钮
# ======================
tk.Button(
    root,
    text="启动反应堆",
    bg="blue",
    fg="white",
    font=("Arial", 12, "bold"),
    command=start_reactor,
).place(x=WIDTH - 180, y=HEIGHT - 190)

tk.Button(
    root,
    text="启用控制棒",
    bg="green",
    fg="white",
    font=("Arial", 12, "bold"),
    command=enable_control_rods,
).place(x=WIDTH - 180, y=HEIGHT - 150)

pump_btn = tk.Button(
    root,
    text="水泵 OFF",
    bg="lightblue",
    fg="black",
    font=("Arial", 12, "bold"),
    command=toggle_pump,
)
pump_btn.place(x=WIDTH - 180, y=HEIGHT - 110)

scram_btn = tk.Button(
    root,
    text="A3-5 紧急停机",
    bg="red",
    fg="white",
    font=("Arial", 14, "bold"),
    command=emergency_scram,
)
scram_btn.place(x=WIDTH - 240, y=20)

# ======================
# 模拟循环
# ======================
def update_simulation():
    global neutron_count, heat, exploded

    if not exploded and reactor_started and not scram_triggered:
        elapsed = time.time() - reactor_start_time

        if elapsed < BOIL_TIME:
            heat = INIT_TEMP + (BOIL_TEMP - INIT_TEMP) * (elapsed / BOIL_TIME)
        else:
            rod_value = control_rod_scale.get()
            rod_effect = (100 - rod_value) / 100 if control_rods_enabled else 0.5

            neutron_count += rod_effect * 2
            neutron_count *= NEUTRON_DECAY

            heat += neutron_count * HEAT_INCREASE_RATE
            heat *= NATURAL_COOLING
            if pump_on:
                heat -= PUMP_COOLING
    elif scram_triggered:
        # 紧急停机后只冷却
        heat *= NATURAL_COOLING
        if pump_on:
            heat -= PUMP_COOLING
    heat = max(0, heat)

    # UI 更新
    power = int(neutron_count * 10)
    canvas.itemconfig(power_text, text=f"发电量: {power} MW")
    canvas.itemconfig(temperature_text, text=f"当前温度: {int(heat)} °C")

    if heat > 120:
        canvas.itemconfig(temperature_text, fill="orange")
    elif heat > 140:
        canvas.itemconfig(temperature_text, fill="red")
    else:
        canvas.itemconfig(temperature_text, fill="cyan")
    if heat >= EXPLOSION_THRESHOLD:
        exploded = True
        canvas.itemconfig(explosion_text, text="爆炸！")
    root.after(40, update_simulation)


# ======================
# 启动
# ======================
update_simulation()
root.mainloop()
