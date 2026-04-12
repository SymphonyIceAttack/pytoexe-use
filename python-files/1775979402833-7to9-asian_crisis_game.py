#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚洲金融危机交互式情景剧本
基于1997年真实事件，允许玩家扮演不同角色，在压力下做出决策。
运行方式：python asian_crisis_game.py
"""

import sys
import os
import time

# ========== 全局状态 ==========
class GameState:
    def __init__(self):
        self.role = None          # 当前角色
        self.thai_reserve = 380   # 泰国外汇储备（亿美元）
        self.korea_days_left = 7  # 韩国离外储耗尽天数
        self.indonesia_stability = 80  # 印尼稳定指数(0-100)
        self.step = 0
        self.history = []         # 决策历史记录

state = GameState()

# ========== 辅助函数 ==========
def clear_screen():
    """清屏（跨平台）"""
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_enter():
    """等待用户按回车继续"""
    input("\n按回车键继续...")

def print_story(text, delay=0.02):
    """逐字打印剧情文本（可选延迟效果）"""
    print("\n" + text)
    wait_enter()

def show_status():
    """显示当前状态（仅对相关角色）"""
    print("\n========== 当前状态 ==========")
    if state.role == "thai":
        print(f"泰国外汇储备: {state.thai_reserve} 亿美元")
    elif state.role == "korea":
        print(f"韩国离外储耗尽天数: {state.korea_days_left} 天")
    elif state.role == "indonesia":
        print(f"印尼稳定指数: {state.indonesia_stability}/100")
    print("==============================")

def record_decision(decision_text):
    """记录决策历史"""
    state.history.append(decision_text)

# ========== 泰国央行行长剧本 ==========
def play_thai():
    state.role = "thai"
    clear_screen()
    print_story("1996年冬，曼谷央行行长办公室。\n"
                "你面前堆满报告：短期外债超过600亿美元，外汇储备仅380亿。\n"
                "索罗斯的量子基金正在大规模建立泰铢空头头寸。")

    # 决策点1
    show_status()
    print("【决策1】你的第一反应是什么？")
    print("1. 立即向总理汇报，建议采取资本管制")
    print("2. 秘密动用外汇储备进行市场干预")
    print("3. 联系IMF请求预防性贷款额度")
    print("4. 公开表态“泰铢不会贬值”稳定信心")
    choice = input("请选择 (1-4): ").strip()
    record_decision(f"决策1: {choice}")

    if choice == "1":
        print_story("总理不以为然：“泰国经济很好，不会出问题。”资本管制方案被搁置。")
    elif choice == "2":
        print_story("你命令秘密买入泰铢，消耗20亿美元储备，泰铢暂时企稳。")
        state.thai_reserve -= 20
    elif choice == "3":
        print_story("IMF代表礼貌地表示需要更多时间评估。援助迟迟未到。")
    elif choice == "4":
        print_story("你在发布会上宣称泰铢不会贬值，市场短暂平静。")
    else:
        print_story("你犹豫不决，错过了最佳时机。")

    # 决策点2：1997年5月
    clear_screen()
    print_story("1997年5月，央行危机作战室。\n"
                "连续干预消耗了巨额外汇，储备已降至250亿美元以下。\n"
                "一份来自IMF的电报摆在你面前。")
    show_status()
    print("【决策2】如何应对？")
    print("1. 立即接受IMF援助方案")
    print("2. 尝试自行解决问题")
    print("3. 联系其他亚洲国家联合干预")
    print("4. 建议总理提前放弃固定汇率")
    choice = input("请选择 (1-4): ").strip()
    record_decision(f"决策2: {choice}")

    if choice == "1":
        print_story("你向IMF求援，但谈判缓慢。投机压力未减。")
    elif choice == "4":
        print_story("你建议提前贬值，但总理在电视上保证“泰铢不会贬值”。")
    else:
        print_story("你犹豫不决，储备继续流失。")

    # 决策点3：1997年7月最后时刻
    clear_screen()
    print_story("1997年7月1日，外汇储备仅剩不到100亿美元。\n"
                "你必须做出最后选择。")
    show_status()
    print("【决策3】最后的选择？")
    print("1. 动用最后储备背水一战")
    print("2. 立即宣布放弃固定汇率，实行浮动")
    print("3. 寻求美国财政部干预")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策3: {choice}")

    if choice == "2":
        print_story("1997年7月2日，泰国宣布放弃钉住汇率。\n"
                    "泰铢当日贬值超过30%，亚洲金融危机正式爆发。\n"
                    "你随后辞职，但历史将记住这一天。\n"
                    "【结局：泰铢沦陷 - 历史的必然】")
    else:
        print_story("你孤注一掷，最终耗尽储备。7月2日被迫贬值。\n"
                    "【结局：泰铢沦陷 - 更惨重的损失】")

    print(f"\n你的决策历程: {' -> '.join(state.history)}")

# ========== 对冲基金交易员剧本 ==========
def play_hedge():
    state.role = "hedge"
    clear_screen()
    print_story("1996年12月，苏黎世某酒店套房。\n"
                "你花了6个月实地调研东南亚经济，发现巨大泡沫。\n"
                "你拨通了乔治·索罗斯的电话。")

    print("【决策1】你的作战计划？")
    print("1. 立即大规模建仓")
    print("2. 分三步走：1月试探，2月加码，5月致命一击")
    print("3. 联合其他基金共同行动")
    print("4. 暂时观望")
    choice = input("请选择 (1-4): ").strip()
    record_decision(f"决策1: {choice}")

    if choice == "2":
        print_story("索罗斯说：“Do it.” 你开始分阶段建立沽空仓位。")
    elif choice == "3":
        print_story("你联合了几家对冲基金，分散风险，但利润也摊薄了。")
    else:
        print_story("你错失了最佳建仓时机，收益不如预期。")

    # 决策点2：1997年5月攻击
    clear_screen()
    print_story("1997年5月，你发动试探性攻击，泰国央行奋力抵抗。\n"
                "你看到他们的储备在迅速消耗。")
    print("【决策2】下一步？")
    print("1. 加大抛售力度，逼其耗尽储备")
    print("2. 暂时收手，等待更佳时机")
    print("3. 转战印尼盾")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策2: {choice}")

    if choice == "1":
        print_story("你持续施压，泰国央行最终在7月投降。你大获全胜。")
    elif choice == "3":
        print_story("你转战印尼，同样获利丰厚。")
    else:
        print_story("你保守操作，收益一般。")

    # 决策点3：1998年8月香港
    clear_screen()
    print_story("1998年8月，香港政府入市干预，与国际炒家正面交锋。\n"
                "你面临巨大压力。")
    print("【决策3】如何应对？")
    print("1. 继续攻击，不信港府能赢")
    print("2. 逐步平仓，保住利润")
    print("3. 立即撤退")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策3: {choice}")

    if choice == "1":
        print_story("你坚持攻击，但港府动用外汇基金大量买入股票，恒指回升。\n"
                    "最终你被迫在高位平仓，亏损离场。\n"
                    "【结局：香港逆袭 - 炒家折戟】")
    else:
        print_story("你及时撤退，保住了大部分利润。\n"
                    "【结局：获利了结 - 聪明的投机者】")

    print(f"\n你的决策历程: {' -> '.join(state.history)}")

# ========== 韩国财阀领袖剧本 ==========
def play_korea():
    state.role = "korea"
    clear_screen()
    print_story("1997年11月，首尔某财阀总部。\n"
                "前30大财阀已有6个倒闭，韩元腰斩。\n"
                "外汇储备即将耗尽，政府正与IMF谈判。")
    show_status()

    print("【决策1】如何应对IMF要求的结构改革？")
    print("1. 积极配合，推动企业结构调整")
    print("2. 抵制改革，利用政治关系拖延")
    print("3. 表面接受，暗中规避")
    print("4. 寻求被外资收购以保留品牌")
    choice = input("请选择 (1-4): ").strip()
    record_decision(f"决策1: {choice}")

    if choice == "1":
        print_story("你开始削减负债，出售非核心资产，裁员重组。\n"
                    "短期阵痛剧烈，但为日后复苏打下基础。")
    elif choice == "2":
        print_story("你抵制改革，导致IMF贷款延迟，国家濒临破产。\n"
                    "最终你被迫接受更苛刻的条件。")
    elif choice == "3":
        print_story("你表面配合，私下转移资产，但被媒体曝光，声誉扫地。")
    else:
        print_story("你寻求外资收购，品牌得以保留，但失去了控制权。")

    # 决策点2：黄金捐献运动
    clear_screen()
    print_story("1998年1月，民间发起“黄金捐献运动”，号召国民捐出黄金救国。\n"
                "作为财阀领袖，你面临选择。")
    print("【决策2】你的态度？")
    print("1. 带头捐献，树立榜样")
    print("2. 象征性捐献少量")
    print("3. 拒绝捐献，认为无济于事")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策2: {choice}")

    if choice == "1":
        print_story("你捐出大量黄金制品，全国共捐226吨，价值22亿美元。\n"
                    "此举震撼世界，重建了国家信誉。")
        gold_donated = True
    elif choice == "2":
        print_story("你捐献很少，被民众指责为自私，企业形象受损。")
        gold_donated = False
    else:
        print_story("你拒绝捐献，成为众矢之的，后来被迫退出商界。")
        gold_donated = False

    # 结局
    if choice == "1":
        print_story("数年后，你的企业完成重组，成为全球竞争者。\n"
                    "韩国经济在IMF监督下深刻改革，实现V型复苏。\n"
                    "【结局：悲壮转型 - 浴火重生】")
    else:
        print_story("你的企业未能适应改革，最终被外资收购或破产。\n"
                    "【结局：淘汰者 - 历史的车轮】")

    print(f"\n你的决策历程: {' -> '.join(state.history)}")

# ========== IMF总裁剧本 ==========
def play_imf():
    state.role = "imf"
    clear_screen()
    print_story("1997年12月，IMF华盛顿总部。\n"
                "桌上堆满泰国、印尼、韩国的紧急援助请求。\n"
                "这是IMF历史上最大规模的救援行动。")

    # 印尼问题
    print("【决策1】如何处理印尼的政治改革要求？")
    print("1. 坚持纯经济条件，不附加政治改革")
    print("2. 接受美国建议，要求苏哈托家族放弃特权")
    print("3. 采取灵活方案，针对各国病征差异化")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策1: {choice}")

    if choice == "2":
        print_story("你要求苏哈托放弃家族商业特权，作为援助条件。\n"
                    "苏哈托被迫接受，但国内矛盾激化，最终他在1998年5月辞职。\n"
                    "IMF的干预被批评为过度政治化。")
        state.indonesia_stability = 30
    elif choice == "1":
        print_story("你坚持纯经济条件，但美国强烈反对。\n"
                    "援助迟迟未能批准，印尼局势恶化。")
        state.indonesia_stability = 50
    else:
        print_story("你设计了更灵活的方案，但执行中仍遇到阻力。")

    # 韩国谈判
    clear_screen()
    print_story("韩国代表坐在对面，面色苍白。离外汇储备耗尽只剩7天。\n"
                "他们强烈反对全面开放金融市场的条款。")
    show_status()
    print("【决策2】如何推进韩国援助？")
    print("1. 坚持全部条件，不接受讨价还价")
    print("2. 在核心条件上做部分让步")
    print("3. 请求G7国家提供额外双边援助")
    choice = input("请选择 (1-3): ").strip()
    record_decision(f"决策2: {choice}")

    if choice == "1":
        print_story("1997年12月3日，韩国在巨大压力下签署协议。\n"
                    "许多韩国人视其为“国耻日”。但改革最终推动韩国经济转型。")
    elif choice == "2":
        print_story("你做出让步，韩国接受了修改后的条件。\n"
                    "危机缓解，但IMF的威信受到质疑。")
    else:
        print_story("G7提供了额外援助，韩国压力减轻。\n"
                    "但多边协调暴露了效率低下的问题。")

    # 最终评价
    clear_screen()
    print_story("亚洲金融危机后，IMF进行了改革反思。\n"
                "但批评者认为，救援条件仍然苛刻，发展中国家话语权依然不足。\n"
                "【结局：功过参半 - 国际货币体系的困境】")

    print(f"\n你的决策历程: {' -> '.join(state.history)}")

# ========== 主菜单 ==========
def main():
    clear_screen()
    print("========================================")
    print("   1997 亚洲金融危机 - 交互式情景剧本   ")
    print("========================================")
    print("\n请选择你要扮演的角色：")
    print("1. 泰国央行行长 (伦差·马拉甲)")
    print("2. 对冲基金交易员 (索罗斯基金操盘手)")
    print("3. 韩国财阀领袖 (五大财阀之一)")
    print("4. IMF总裁 (米歇尔·康德苏)")
    print("0. 退出")
    
    role_choice = input("请输入数字 (0-4): ").strip()
    
    if role_choice == "1":
        play_thai()
    elif role_choice == "2":
        play_hedge()
    elif role_choice == "3":
        play_korea()
    elif role_choice == "4":
        play_imf()
    else:
        print("再见！")
        sys.exit(0)

if __name__ == "__main__":
    main()
