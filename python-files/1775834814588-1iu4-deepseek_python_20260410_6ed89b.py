import random
from datetime import datetime

# ---------- 基础数据 ----------
GONG_ORDER = ["大安", "留连", "速喜", "赤口", "小吉", "空亡"]
GONG_WUXING = {"大安": "木", "留连": "土", "速喜": "火", "赤口": "金", "小吉": "水", "空亡": "土"}
GONG_YINYANG = {"大安": "阳", "留连": "阴", "速喜": "阳", "赤口": "阴", "小吉": "阳", "空亡": "阴"}

# 地支顺序（用于数地支）
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
DIZHI_YINYANG = {"子": "阳", "丑": "阴", "寅": "阳", "卯": "阴", "辰": "阳", "巳": "阴",
                  "午": "阳", "未": "阴", "申": "阳", "酉": "阴", "戌": "阳", "亥": "阴"}

# 六宫纳支
GONG_NAZHI = {
    "大安": ["寅", "卯"],
    "留连": ["未", "戌"],
    "速喜": ["巳", "午"],
    "赤口": ["申", "酉"],
    "小吉": ["亥", "子"],
    "空亡": ["丑", "辰"]
}

# 六神顺序
LIUSHEN = ["青龙", "朱雀", "勾陈", "白虎", "腾蛇", "玄武"]

# ---------- 六神游行取象字典（简化核心象义）----------
# 格式：{六神: {地支: (状态, 简义)}}
LIUSHEN_YOUXING = {
    "青龙": {
        "子": ("入海", "非常吉利、自在，宴会祝贺尤吉"),
        "亥": ("游江", "非常吉利、自在，宴会祝贺尤吉"),
        "丑": ("蟠泥", "所谋未遂，受阻拖累"),
        "未": ("在陆", "所谋未遂，受阻拖累"),
        "寅": ("乘云", "利于经营，有乘云出入之象"),
        "卯": ("驱雷", "利于经营，得以展布"),
        "巳": ("掩目", "因财有不测之忧，求财有阻力"),
        "午": ("烧身", "因财有不测之忧，自身能力可能不够"),
        "申": ("伤鳞", "宜安静，守住资产，保护自己"),
        "酉": ("摧角", "宜安静，守住资产，保护自己"),
        "辰": ("飞天", "跃跃欲试，君子有为"),
        "戌": ("登魁", "小人争财之象")
    },
    "朱雀": {
        "子": ("损羽", "文书无气，词讼口舌不凶"),
        "丑": ("掩目", "动静得昌，无口舌之忧"),
        "寅": ("安巢", "迟滞沉溺，文书音信迟迟"),
        "卯": ("安巢", "迟滞沉溺，文书音信迟迟"),
        "辰": ("投网", "徒弟错遗忘，多无音信"),
        "戌": ("投网", "徒弟错遗忘，多无音信"),
        "巳": ("昼翔", "音信至，文书起用"),
        "午": ("衔符", "真朱雀，非细之讼，考试则高中"),
        "未": ("临坟", "口舌难宁，担心忧愁"),
        "申": ("励嘴", "怪异经官语讼"),
        "酉": ("夜噪", "官灾起，口舌入门，考试文章为好事"),
        "亥": ("入水", "言辞悲切，文书不得用")
    },
    "勾陈": {
        "子": ("投机", "被辱暗遭毒害，忍而已"),
        "丑": ("受越", "灾祸斗争难免"),
        "寅": ("遭囚", "宜上书，需借助他人之力"),
        "卯": ("入户", "家宅不宁，家不和"),
        "辰": ("升堂", "有狱吏勾连，斗讼"),
        "巳": ("铸印", "有封拜，升迁极速，常人反忧"),
        "午": ("反目", "因他人逆戾，易受人挑拨"),
        "未": ("入驿", "往返词讼稽留"),
        "申": ("趋户", "反得勾连，需立刻返回"),
        "酉": ("披刃", "身遭责，诬陷诽谤暗算"),
        "戌": ("下狱", "往返词讼稽留"),
        "亥": ("褰裳", "反得勾连，麻烦缠身")
    },
    "白虎": {
        "子": ("溺水", "音书不至，道路不通"),
        "亥": ("溺水", "音书不至，道路不通"),
        "丑": ("在野", "损坏牛羊，财物受损"),
        "未": ("在野", "损坏牛羊，财物受损"),
        "寅": ("登山", "掌生杀之权（仕途吉），常人凶"),
        "卯": ("临门", "伤折人口，身边有凶险"),
        "酉": ("临门", "伤折人口，身边有凶险"),
        "辰": ("噬人", "有害，血腥事件"),
        "巳": ("焚身", "祸害反昌，因祸得福"),
        "午": ("焚身", "祸害反昌，因祸得福"),
        "申": ("衔牒", "无凶可持喜信，喜事有困难"),
        "戌": ("落井", "脱桎梏之殃，困境中有脱困机会")
    },
    "腾蛇": {
        "子": ("掩目", "无患无忧，虚惊"),
        "丑": ("蟠龙", "祸消福善，纠缠但福祸俱全"),
        "寅": ("生角", "福，荣旺之极"),
        "卯": ("当门", "成灾，出门即被害"),
        "辰": ("象龙", "释难，可解忧"),
        "巳": ("乘雾", "休祥不辨，需谨慎小心"),
        "午": ("飞空", "休祥不辨，需避之"),
        "未": ("入林", "锋不可砍，小灾祸可规避"),
        "申": ("衔剑", "成灾，退潜避之"),
        "酉": ("露齿", "祸，猖獗凶险"),
        "戌": ("入冢", "释难，可解忧"),
        "亥": ("坠水", "从心无患")
    },
    "玄武": {
        "子": ("散发", "有畏捕之心，担惊受怕"),
        "丑": ("升堂", "有干求之意，于公谋私"),
        "寅": ("入林", "难寻，盗贼凭依"),
        "卯": ("窥户", "盗贼入门"),
        "辰": ("失路", "自制，盗贼消亡"),
        "巳": ("反顾", "虚获惊悸"),
        "午": ("截路", "贼势猖獗"),
        "未": ("不成", "败于酒食之地"),
        "申": ("折足", "失势擒之可得"),
        "酉": ("拔剑", "贼势猖獗，攻之反伤"),
        "戌": ("遭囚", "失势擒之可得"),
        "亥": ("伏藏", "隐于深邃之乡，难获")
    }
}

# 五行生克关系
WUXING_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
WUXING_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# ---------- 工具函数 ----------
def get_gong_index(gong_name):
    return GONG_ORDER.index(gong_name)

def get_next_gong(current_gong, step=1):
    idx = get_gong_index(current_gong)
    return GONG_ORDER[(idx + step) % 6]

def get_dizhi_index(zhi):
    return DIZHI.index(zhi)

def get_zhi_yinyang(zhi):
    return DIZHI_YINYANG[zhi]

def get_gong_yinyang(gong):
    return GONG_YINYANG[gong]

def get_gong_wuxing(gong):
    return GONG_WUXING[gong]

def get_wuxing_relation(wx1, wx2):
    """返回wx1对wx2的生克关系：生、克、同、被生、被克"""
    if wx1 == wx2:
        return "同"
    if WUXING_SHENG.get(wx1) == wx2:
        return "生"
    if WUXING_KE.get(wx1) == wx2:
        return "克"
    if WUXING_SHENG.get(wx2) == wx1:
        return "被生"
    if WUXING_KE.get(wx2) == wx1:
        return "被克"
    return "?"

# ---------- 1. 起三宫（传统月日时）----------
def get_sangong_by_lunar(month, day, hour_zhi):
    """根据农历月、日、时辰地支起三宫（天·月、地·日、人·时）"""
    # 月宫：正月大安起
    month_gong = GONG_ORDER[(month - 1) % 6]
    # 日宫：从月宫起初一，顺数至day
    current = month_gong
    for _ in range(1, day):
        current = get_next_gong(current)
    day_gong = current
    # 时宫：从日宫起子时，顺数至hour_zhi
    hour_idx = DIZHI.index(hour_zhi)
    current = day_gong
    for _ in range(hour_idx):  # 子时占原位，顺数
        current = get_next_gong(current)
    hour_gong = current
    return month_gong, day_gong, hour_gong

# ---------- 2. 纳支规则 ----------
def na_zhi_for_gong(gong, prev_zhi_yinyang):
    """
    根据前一个地支的阴阳和本宫阴阳决定取阴支还是阳支
    规则：同阴阳取阴支，不同阴阳取阳支
    返回地支
    """
    zhi_candidates = GONG_NAZHI[gong]
    gong_yy = get_gong_yinyang(gong)
    # 确定取阴还是阳
    if prev_zhi_yinyang == gong_yy:
        target_yy = "阴"
    else:
        target_yy = "阳"
    # 从候选地支中选出对应阴阳的地支
    for zhi in zhi_candidates:
        if DIZHI_YINYANG[zhi] == target_yy:
            return zhi
    # 若找不到（理论上都有），返回第一个
    return zhi_candidates[0]

def na_zhi_full(ren_gong, di_gong, tian_gong, shichen_zhi):
    """完整纳支流程，返回(人宫地支, 地宫地支, 天宫地支)"""
    # 人宫纳支：由时辰阴阳决定
    shichen_yy = DIZHI_YINYANG[shichen_zhi]
    ren_zhi = na_zhi_for_gong(ren_gong, shichen_yy)
    # 地宫纳支：由人宫地支阴阳决定
    ren_zhi_yy = DIZHI_YINYANG[ren_zhi]
    di_zhi = na_zhi_for_gong(di_gong, ren_zhi_yy)
    # 天宫纳支：由地宫地支阴阳决定
    di_zhi_yy = DIZHI_YINYANG[di_zhi]
    tian_zhi = na_zhi_for_gong(tian_gong, di_zhi_yy)
    return ren_zhi, di_zhi, tian_zhi

# ---------- 3. 排六神 ----------
def pai_liushen(ren_gong, shichen_zhi):
    """
    人宫查时辰，时上起青龙，返回六个宫位对应的六神字典
    """
    # 从人宫开始数地支（子丑寅卯...）至时辰地支，落位为青龙
    start_idx = get_gong_index(ren_gong)
    shichen_idx = DIZHI.index(shichen_zhi)
    # 顺数shichen_idx次（子时数0次）
    qinglong_idx = (start_idx + shichen_idx) % 6
    # 分配六神
    liushen_map = {}
    for i in range(6):
        gong = GONG_ORDER[(qinglong_idx + i) % 6]
        liushen_map[gong] = LIUSHEN[i]
    return liushen_map

# ---------- 4. 六神游行取象 ----------
def get_liushen_state(liushen, dizhi):
    """返回(状态, 简义)，若无记录则返回通用提示"""
    if liushen in LIUSHEN_YOUXING and dizhi in LIUSHEN_YOUXING[liushen]:
        return LIUSHEN_YOUXING[liushen][dizhi]
    return ("游行", "参照六神地支基本象义")

# ---------- 5. 综合断课输出 ----------
def duanke_output(tian_gong, di_gong, ren_gong, shichen_zhi, 
                  tian_zhi, di_zhi, ren_zhi, liushen_map):
    """生成格式化断课结果"""
    lines = []
    lines.append("=" * 50)
    lines.append("《秘传三宫小六壬》起课断课")
    lines.append("=" * 50)
    lines.append(f"时辰：{shichen_zhi}时")
    lines.append("")
    lines.append("【三宫定位】")
    lines.append(f"天宫（客/外部）：{tian_gong} 纳支 {tian_zhi} 五行{get_gong_wuxing(tian_gong)}")
    lines.append(f"地宫（介/过程）：{di_gong} 纳支 {di_zhi} 五行{get_gong_wuxing(di_gong)}")
    lines.append(f"人宫（主/自己）：{ren_gong} 纳支 {ren_zhi} 五行{get_gong_wuxing(ren_gong)}")
    lines.append("")
    
    # 六神
    lines.append("【六神排布】")
    for gong in GONG_ORDER:
        shen = liushen_map[gong]
        # 获取该宫对应的地支（如果三宫之一）
        if gong == tian_gong:
            zhi = tian_zhi
        elif gong == di_gong:
            zhi = di_zhi
        elif gong == ren_gong:
            zhi = ren_zhi
        else:
            # 非三宫的地支可暂不处理，留空
            zhi = "—"
        state, desc = get_liushen_state(shen, zhi) if zhi != "—" else ("—", "—")
        lines.append(f"  {gong}：{shen} {state} ({desc})")
    lines.append("")
    
    # 生克关系
    ren_wx = get_gong_wuxing(ren_gong)
    tian_wx = get_gong_wuxing(tian_gong)
    di_wx = get_gong_wuxing(di_gong)
    rel_ren_tian = get_wuxing_relation(ren_wx, tian_wx)
    rel_di_ren = get_wuxing_relation(di_wx, ren_wx)
    rel_di_tian = get_wuxing_relation(di_wx, tian_wx)
    
    lines.append("【生克大势】")
    lines.append(f"人宫({ren_gong}) vs 天宫({tian_gong})：{rel_ren_tian}")
    lines.append(f"地宫({di_gong}) 助人宫？ {'是' if rel_di_ren in ['生','同'] else '否'}")
    lines.append(f"地宫({di_gong}) 助天宫？ {'是' if rel_di_tian in ['生','同'] else '否'}")
    
    # 吉凶大方向
    if rel_ren_tian in ["生", "克", "同"]:
        direction = "人宫有力，事有可为（若人宫旺相更吉）"
    elif rel_ren_tian in ["被克", "被生"]:
        direction = "人宫受制或依赖外界，需谨慎努力"
    else:
        direction = "需参看地宫与时辰"
    lines.append(f"初步方向：{direction}")
    
    # 时辰助力
    shichen_dizhi = shichen_zhi
    # 时辰地支五行（简略）
    zhi_wx_map = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
                  "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
    shichen_wx = zhi_wx_map[shichen_dizhi]
    rel_shi_ren = get_wuxing_relation(shichen_wx, ren_wx)
    lines.append(f"时辰({shichen_zhi} {shichen_wx}) 对 人宫：{rel_shi_ren}")
    
    lines.append("=" * 50)
    lines.append("注：此为程式化输出，具体占断需结合灵感与事理。")
    return "\n".join(lines)

# ---------- 主程序交互 ----------
def main():
    print("=== 三宫小六壬起课断课程序 ===")
    print("请选择起课方式：")
    print("1. 使用当前时间（自动转换农历月日时，需手动输入时辰地支）")
    print("2. 手动输入农历月、日、时辰地支")
    print("3. 随机起课（随机月日时）")
    print("4. 直接输入三宫与时辰（跳过推算，用于已有课例）")
    choice = input("请输入数字(1/2/3/4)：").strip()
    
    if choice == "1":
        # 当前公历时间，简化处理：要求用户输入农历月日（因为没有内置农历转换）
        print("当前时间仅作参考，请手动输入农历月、日、时辰。")
        month = int(input("农历月份(1-12)："))
        day = int(input("农历日期(1-30)："))
        hour_zhi = input("时辰地支(子丑寅卯辰巳午未申酉戌亥)：").strip()
        if hour_zhi not in DIZHI:
            print("地支错误")
            return
        tian, di, ren = get_sangong_by_lunar(month, day, hour_zhi)
    elif choice == "2":
        month = int(input("农历月份(1-12)："))
        day = int(input("农历日期(1-30)："))
        hour_zhi = input("时辰地支：").strip()
        if hour_zhi not in DIZHI:
            print("地支错误")
            return
        tian, di, ren = get_sangong_by_lunar(month, day, hour_zhi)
    elif choice == "3":
        month = random.randint(1, 12)
        day = random.randint(1, 30)
        hour_zhi = random.choice(DIZHI)
        print(f"随机起课：农历{month}月{day}日 {hour_zhi}时")
        tian, di, ren = get_sangong_by_lunar(month, day, hour_zhi)
    elif choice == "4":
        print("六宫：大安、留连、速喜、赤口、小吉、空亡")
        tian = input("天宫：").strip()
        di = input("地宫：").strip()
        ren = input("人宫：").strip()
        hour_zhi = input("时辰地支：").strip()
        if tian not in GONG_ORDER or di not in GONG_ORDER or ren not in GONG_ORDER or hour_zhi not in DIZHI:
            print("输入有误")
            return
    else:
        print("无效选择")
        return

    # 纳支
    ren_zhi, di_zhi, tian_zhi = na_zhi_full(ren, di, tian, hour_zhi)
    # 排六神
    liushen_map = pai_liushen(ren, hour_zhi)
    # 输出断课
    result = duanke_output(tian, di, ren, hour_zhi, tian_zhi, di_zhi, ren_zhi, liushen_map)
    print(result)

if __name__ == "__main__":
    main()