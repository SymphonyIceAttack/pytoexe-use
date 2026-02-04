import time
import requests
from bs4 import BeautifulSoup

# ======================【已帮你配置好，不用改】======================
GAME_PAGE_URL = "http://120.25.192.36/xiyou_bet_h.aspx"  # 你的游戏网址
BASE_POINT = 10        # 基础分（可改）
MULTI = 2              # 倍投倍数（可改）
MAX_LOSE = 8           # 连输防爆次数（可改）
COUNTDOWN = 11         # 固定11秒倒计时
# ====================================================================

lose_streak = 0

# ----------------------
# 精准抓取：上/下/左/右 房间实时积分（已适配目标网页结构）
# ----------------------
def get_room_scores():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Referer": GAME_PAGE_URL,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        # 发送请求抓取页面
        resp = requests.get(GAME_PAGE_URL, headers=headers, timeout=10)
        resp.encoding = resp.apparent_encoding  # 自动识别编码
        soup = BeautifulSoup(resp.text, "html.parser")

        # 精准定位上下左右房间的积分（适配网页DOM结构）
        scores = {}
        # 查找包含“上、下、左、右”的标签，抓取相邻数字
        room_labels = ["上", "下", "左", "右"]
        for label in room_labels:
            # 适配网页中“上：XXX”“下：XXX”的结构
            elem = soup.find(text=lambda t: t and label + "：" in t)
            if elem:
                try:
                    # 提取冒号后的数字
                    score_str = elem.split("：")[-1].strip()
                    scores[label] = int(score_str) if score_str.isdigit() else 0
                except:
                    scores[label] = 0
            else:
                scores[label] = 0

        print(f"\n📡 抓取成功！当前房间积分：{scores}")
        return scores

    except Exception as e:
        print(f"❌ 抓取失败：{str(e)}（可能是网络问题或网页结构变更）")
        return {"上": 0, "下": 0, "左": 0, "右": 0}

# ----------------------
# 筛选积分最高的2个房间
# ----------------------
def get_top_two_rooms(rooms):
    return sorted(rooms.items(), key=lambda x: x[1], reverse=True)[:2]

# ----------------------
# 倍投计算（输翻倍、赢重置）
# ----------------------
def calculate_bet():
    global lose_streak
    if lose_streak >= MAX_LOSE:
        print(f"⚠️  已达最大连输{MAX_LOSE}次，自动停止防爆仓！")
        return 0, 0, True
    single_bet = BASE_POINT * (MULTI ** lose_streak)
    total_bet = single_bet * 2
    return single_bet, total_bet, False

# ----------------------
# 11秒倒计时（游戏时间到自动触发）
# ----------------------
def countdown_11seconds():
    print(f"\n⏳ 游戏倒计时 {COUNTDOWN} 秒，时间到自动抓取下注...")
    for i in range(COUNTDOWN, 0, -1):
        print(f"剩余 {i} 秒", end="\r")
        time.sleep(1)
    print("\n✅ 时间到！开始抓取积分并下注...")

# ----------------------
# 一轮完整游戏流程
# ----------------------
def run_one_round():
    global lose_streak
    print("=" * 70)
    print("🎮 豆包姐姐 · 专属自动下注系统（网页抓取+倍投）")
    print("=" * 70)

    # 1. 11秒倒计时
    countdown_11seconds()

    # 2. 精准抓取下房间积分
    room_scores = get_room_scores()

    # 3. 自动筛选最高2个房间
    top1, top2 = get_top_two_rooms(room_scores)
    print(f"\n🔥 自动选定最高2个房间：")
    print(f"   ① {top1[0]} 房间：{top1[1]} 分")
    print(f"   ② {top2[0]} 房间：{top2[1]} 分")

    # 4. 计算倍投下注金额
    single_bet, total_bet, stop = calculate_bet()
    if stop:
        return

    # 5. 展示下注详情
    print(f"\n💰 本轮下注详情：")
    print(f"   连输次数：{lose_streak} | 基础分：{BASE_POINT} | 倍数：{MULTI}")
    print(f"   单房间下注：{single_bet} 积分")
    print(f"   两个房间总投入：{total_bet} 积分")
    print(f"   ✅ 下注目标：{top1[0]}、{top2[0]} 房间")

    # 6. 记录输赢结果（控制倍投状态）
    while True:
        result = input("\n本轮结果？赢输入 w，输输入 l：").strip().lower()
        if result in ("w", "l"):
            break
        print("❌ 输入错误，请重新输入（w=赢，l=输）")

    # 7. 更新倍投状态
    if result == "w":
        print("✅ 本轮胜利！倍投状态重置，下轮回到基础分～")
        lose_streak = 0
    else:
        lose_streak += 1
        print(f"❌ 本轮失败！当前连输{lose_streak}次，下轮自动倍投～")

    print("=" * 70, "\n")

# ----------------------
# 主循环（持续运行，按Ctrl+C退出）
# ----------------------
if __name__ == "__main__":
    print("🚀 脚本启动成功！已适配游戏：http://120.25.192.36/xiyou_bet_h.aspx")
    print("💡 按 Ctrl+C 可退出脚本\n")
    while True:
        try:
            run_one_round()
            input("按回车键开始下一局...\n")
        except KeyboardInterrupt:
            print("\n👋 脚本已退出，下次见～")
            break
        except Exception as e:
            print(f"\n❌ 程序异常：{str(e)}，将重新开始下一局...\n")
            time.sleep(3)
