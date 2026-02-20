import json
import math
import os
import time
from datetime import datetime

print("本代码由小鱼仔娱乐制作")

# ===== 辅助函数 =====
def input_beat(prompt):
    print(f"\n请输入{prompt}（格式：小节 分子 分母）")
    while True:
        try:
            bar, num, den = map(int, input("例如 '131 0 1' → ").split())
            return [bar, num, den]
        except:
            print("输入错误，请按格式输入三个整数（用空格分隔）")

def input_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("必须输入大于0的整数！")
        except:
            print("请输入有效整数！")

def input_mode():
    while True:
        try:
            mode = int(input("\n请选择模式：\n1. 数值渐变模式\n2. 文本展开模式\n3. 查看教程\n请输入数字 (1-3)："))
            if mode in (1, 2, 3):
                return mode
            print("只能输入1、2或3！")
        except:
            print("请输入有效数字！")

# ===== 教程内容 =====
def show_tutorial():
    tutorial = """
════════════════════════════════════════════
                   教程
════════════════════════════════════════════
本程序支持两种模式：数值渐变和文本展开。
生成完成后会生成一个:时间.txt"的文档
在RPE中选择文字事件编辑，在你输入的起始点哪里拖动一个出来，内容随便输入
复制你输入的内容,"Ctrl+S"保存谱面
点击谱面基本信息，随后点击打开当前文件夹
用记事本打开"数字.json","Ctrl+F"打开查找，输入你复制的内容
假设查找出来的是这个
                {
                  "bezier" : 0,
                  "bezierPoints" : [ 0.0, 0.0, 0.0, 0.0 ],
                  "easingLeft" : 0.0,
                  "easingRight" : 1.0,
                  "easingType" : 1,
                  "end" : "",
                  "endTime" : [ 3, 1, 4 ],
                  "font" : "cmdysj",
                  "linkgroup" : 0,
                  "start" : "鱼仔大大（你复制的内容）",
                  "startTime" : [ 3, 0, 1 ]
                }
把这个全删了，替换成程序复制出来的内容,保存文本,然后返回RPE,打开设置,点击重载谱面
大功告成！
════════════════════════════════════════════
按回车键返回模式选择..."""
    print(tutorial)
    input()  # 等待用户按回车

# ===== 28种缓动函数（按新顺序）=====
easing_functions = [
    # 1 linear
    ("1 linear", lambda t: t),
    # 2 Out Sine
    ("2 Out Sine", lambda t: math.sin(t * math.pi/2)),
    # 3 In Sine
    ("3 In Sine", lambda t: 1 - math.cos(t * math.pi/2)),
    # 4 Out Quad
    ("4 Out Quad", lambda t: t*(2-t)),
    # 5 In Quad
    ("5 In Quad", lambda t: t*t),
    # 6 IO Sine (InOutSine)
    ("6 IO Sine", lambda t: 0.5 * (1 - math.cos(math.pi*t))),
    # 7 IO Quad (InOutQuad)
    ("7 IO Quad", lambda t: 2*t*t if t < 0.5 else -1+(4-2*t)*t),
    # 8 Out Cubic
    ("8 Out Cubic", lambda t: (t-1)**3 + 1),
    # 9 In Cubic
    ("9 In Cubic", lambda t: t**3),
    # 10 Out Quart
    ("10 Out Quart", lambda t: 1 - (t-1)**4),
    # 11 In Quart
    ("11 In Quart", lambda t: t**4),
    # 12 IO Cubic (InOutCubic)
    ("12 IO Cubic", lambda t: 4*t**3 if t < 0.5 else 1 + 4*(t-1)**3),
    # 13 IO Quart (InOutQuart)
    ("13 IO Quart", lambda t: 8*t**4 if t < 0.5 else 1 - 8*(t-1)**4),
    # 14 Out Quint
    ("14 Out Quint", lambda t: 1 - (t-1)**5),
    # 15 In Quint
    ("15 In Quint", lambda t: t**5),
    # 16 Out Expo
    ("16 Out Expo", lambda t: 1 if t>=1 else 1 - 2**(-10*t)),
    # 17 In Expo
    ("17 In Expo", lambda t: 0 if t<=0 else 2**(10*(t-1))),
    # 18 Out Circ
    ("18 Out Circ", lambda t: math.sqrt(1 - (t-1)**2)),
    # 19 In Circ
    ("19 In Circ", lambda t: 1 - math.sqrt(1 - t*t)),
    # 20 Out Back
    ("20 Out Back", lambda t: 1 + (t-1)**2*((1.70158+1)*(t-1) + 1.70158)),
    # 21 In Back
    ("21 In Back", lambda t: t*t*((1.70158+1)*t - 1.70158)),
    # 22 IO Circ (InOutCirc)
    ("22 IO Circ", lambda t: 0.5*(1 - math.sqrt(1 - 4*t*t)) if t < 0.5 else 0.5*(math.sqrt(1 - (2*t-2)**2) + 1)),
    # 23 IO Back (InOutBack)
    ("23 IO Back", lambda t: (0.5*(2*t)**2*((1.70158*1.525+1)*2*t - 1.70158*1.525)) if t < 0.5 else 0.5*((2*t-2)**2*((1.70158*1.525+1)*(2*t-2) + 1.70158*1.525) + 2)),
    # 24 Out Elastic
    ("24 Out Elastic", lambda t: 2**(-10*t) * math.sin((t-0.3/4)*(2*math.pi)/0.3) + 1 if t !=1 else 1),
    # 25 In Elastic
    ("25 In Elastic", lambda t: -(2**(10*(t-1)) * math.sin((t-1-0.3/4)*(2*math.pi)/0.3)) if t !=0 else 0),
    # 26 Out Bounce
    ("26 Out Bounce", lambda t: 7.5625*t*t if t < 1/2.75 else 7.5625*(t-1.5/2.75)**2 + 0.75 if t < 2/2.75 else 7.5625*(t-2.25/2.75)**2 + 0.9375 if t < 2.5/2.75 else 7.5625*(t-2.625/2.75)**2 + 0.984375),
    # 27 In Bounce
    ("27 In Bounce", lambda t: 1 - (lambda t: 7.5625*t*t if t < 1/2.75 else 7.5625*(t-1.5/2.75)**2 + 0.75 if t < 2/2.75 else 7.5625*(t-2.25/2.75)**2 + 0.9375 if t < 2.5/2.75 else 7.5625*(t-2.625/2.75)**2 + 0.984375)(1-t)),
    # 28 IO Bounce (InOutBounce)
    ("28 IO Bounce", lambda t: (1 - (lambda t: 7.5625*t*t if t < 1/2.75 else 7.5625*(t-1.5/2.75)**2 + 0.75 if t < 2/2.75 else 7.5625*(t-2.25/2.75)**2 + 0.9375 if t < 2.5/2.75 else 7.5625*(t-2.625/2.75)**2 + 0.984375)(1-2*t))/2 if t < 0.5 else (1 + (lambda t: 7.5625*t*t if t < 1/2.75 else 7.5625*(t-1.5/2.75)**2 + 0.75 if t < 2/2.75 else 7.5625*(t-2.25/2.75)**2 + 0.9375 if t < 2.5/2.75 else 7.5625*(t-2.625/2.75)**2 + 0.984375)(2*t-1))/2)
]

# ===== 主程序 =====
while True:
    mode = input_mode()
    if mode == 3:
        show_tutorial()
        continue  # 返回模式选择
    # 模式1或2，跳出循环继续后续
    break

# 公共输入：拍信息和间隔分母
start_beat = input_beat("开始拍")
end_beat = input_beat("结束拍")
interval_denominator = input_positive_int("\n请输入间隔分母（例如16表示1/16拍间隔）：")

# ===== 缓动函数选择（两个模式共用）=====
print("\n请选择缓动函数：")
for func in easing_functions:
    print(func[0])
while True:
    try:
        choice = int(input("请输入数字 (1-28)：")) - 1
        if 0 <= choice < len(easing_functions):
            ease_func = easing_functions[choice][1]
            break
        print("输入超出范围！")
    except:
        print("请输入有效数字！")

# ===== 根据模式获取特定参数 =====
if mode == 1:
    # 数值模式
    start_value = int(input("\n请输入起始数值（整数）："))
    end_value = int(input("请输入结束数值（整数）："))
    unit_suffix = input("请输入单位后缀（如 km、m、%）：")
else:
    # 文本模式
    start_text = input("\n请输入起始文本（如“你好世界”）：")

# ===== 计算总事件数 =====
def is_beat_reached(current, target):
    return (current[0] > target[0]) or (current[0] == target[0] and current[1]/current[2] >= target[1]/target[2])

total_events = 0
current_beat = start_beat.copy()
while not is_beat_reached(current_beat, end_beat):
    total_events += 1
    next_beat = [current_beat[0], current_beat[1] + 1, interval_denominator]
    if next_beat[1] >= interval_denominator:
        next_beat[0] += 1
        next_beat[1] = 0
    current_beat = next_beat

# ===== 生成事件 =====
events = []
current_time = start_beat.copy()
current_time[2] = interval_denominator

for i in range(total_events):
    progress = i / (total_events - 1) if total_events > 1 else 1.0
    eased_progress = ease_func(progress)

    if mode == 1:
        # 数值模式：计算缓动后的数值
        current_value = start_value + int((end_value - start_value) * eased_progress)
        value_str = f"{current_value}{unit_suffix}"
    else:
        # 文本模式：根据缓动进度确定当前文本长度
        L = len(start_text)
        if L == 0:
            value_str = ""
        else:
            index = int(eased_progress * (L - 1))  # 索引从0到L-1
            value_str = start_text[:index + 1]

    # 计算下一个时间点
    next_time = [current_time[0], current_time[1] + 1, interval_denominator]
    if next_time[1] >= interval_denominator:
        next_time[0] += 1
        next_time[1] = 0

    event = {
        "bezier": 0,
        "bezierPoints": [0.0,0.0,0.0,0.0],
        "easingLeft": 0.0,
        "easingRight": 1.0,
        "easingType": 1,
        "end": value_str,
        "endTime": next_time.copy(),
        "linkgroup": 0,
        "start": value_str,
        "startTime": current_time.copy()
    }
    events.append(event)
    current_time = next_time.copy()

# 修正最后一个事件的结束时间和结束值
events[-1]["endTime"] = end_beat.copy()
if mode == 1:
    events[-1]["end"] = f"{end_value}{unit_suffix}"
else:
    events[-1]["end"] = start_text if start_text else ""

# ===== 输出 JSON 字符串 =====
json_str = json.dumps(events, indent=3, separators=(',', ' : '), ensure_ascii=False)[1:-1]
json_str = json_str.replace("[\n        ", "[").replace(",\n        ", ",").replace("\n      ]", "]")

print("\n生成结果：")
print(json_str)

# ===== 文件保存（默认当前目录）=====
print("\n请选择文件保存位置：")
default_path = os.getcwd()  # 当前工作目录
save_path = input(f"直接回车使用默认路径 ({default_path})\n或输入自定义完整路径：").strip()
save_path = save_path if save_path else default_path
if not os.path.exists(save_path):
    try:
        os.makedirs(save_path)
        print(f"已自动创建目录：{save_path}")
    except Exception as e:
        print(f"目录创建失败：{str(e)}")
        save_path = default_path
        print(f"将使用默认路径：{save_path}")

filename = datetime.now().strftime("%Y-%m-%d %H-%M-%S") + ".txt"
full_path = os.path.join(save_path, filename)

try:
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(json_str)
    print(f"\n✅ 文件保存成功！路径：{full_path}")
except Exception as e:
    print(f"\n❌ 文件保存失败！错误信息：{str(e)}")
    print("请检查：1.路径是否有效 2.写入权限 3.磁盘空间")

time.sleep(1)  # 等待1秒后退出