# 智能学习助手
# 功能：AI题库、自动判分、学习计时、薄弱点推荐、数据展示
import random
import time
from datetime import datetime

# ===================== 1. 初始化配置 =====================
# 数理化题库（AI自动生成基础数据）
QUESTION_BANK = {
    "数学": ["一元二次方程求解", "函数单调性判断", "几何图形面积计算", "概率统计计算"],
    "物理": ["牛顿运动定律应用", "电路欧姆定律计算", "机械能守恒分析", "光学折射规律"],
    "化学": ["化学方程式配平", "物质的量计算", "氧化还原反应判断", "溶液浓度计算"]
}

# 学习数据存储（模拟数据库，数据处理核心）
LEARNING_DATA = {
    "total_study_time": 0,
    "correct_count": 0,
    "total_questions": 0,
    "weak_points": []
}


# ===================== 2. AI核心功能模块 =====================
# 功能1：AI智能生成题目
def generate_question(subject):
    """根据学科智能生成题目和答案"""
    if subject not in QUESTION_BANK:
        return "科目不存在", 0

    # 随机选择知识点
    point = random.choice(QUESTION_BANK[subject])
    # 生成随机数值题目（AI基础算法：随机数+逻辑组合）
    if subject == "数学":
        a, b = random.randint(1, 20), random.randint(1, 20)
        question = f"【数学】{point}：计算 {a} + {b} × 2 = ?"
        answer = a + b * 2
    elif subject == "物理":
        m, v = random.randint(1, 10), random.randint(1, 5)
        question = f"【物理】{point}：质量{m}kg的物体，速度{v}m/s，动能是多少？(动能=½mv²)"
        answer = 0.5 * m * (v ** 2)
    else:
        n, m = random.randint(1, 10), random.randint(1, 5)
        question = f"【化学】{point}：{n}mol物质溶解在{m}L水中，物质的量浓度是多少？"
        answer = round(n / m, 2)
    return question, answer


# 功能2：自动判分与数据处理
def check_answer(user_ans, real_ans):
    """AI自动判断答案对错，更新学习数据"""
    global LEARNING_DATA
    LEARNING_DATA["total_questions"] += 1

    # 容错处理：支持整数/小数判断
    try:
        if abs(float(user_ans) - real_ans) < 0.01:
            LEARNING_DATA["correct_count"] += 1
            return True, "回答正确！👍"
        else:
            return False, f"回答错误，正确答案是：{real_ans} 💡"
    except:
        return False, f"输入格式错误！正确答案是：{real_ans} 💡"


# 功能3：智能推荐薄弱知识点
def recommend_weak_point():
    """根据正确率AI分析薄弱点，智能推荐"""
    correct_rate = LEARNING_DATA["correct_count"] / max(LEARNING_DATA["total_questions"], 1)
    if correct_rate < 0.6:
        return "⚠️ 正确率较低，推荐加强基础知识点学习！"
    elif correct_rate < 0.8:
        return "📚 正确率中等，推荐强化中等难度题目！"
    else:
        return "✨ 正确率优秀，挑战难题吧！"


# 功能4：智能学习计时（番茄钟）
def study_timer(minutes):
    """学习计时功能，记录总时长"""
    global LEARNING_DATA
    print(f"\n⏰ 开始{minutes}分钟专注学习！")
    for i in range(minutes, 0, -1):
        time.sleep(1)
        print(f"剩余时间：{i} 分钟", end="\r")
    LEARNING_DATA["total_study_time"] += minutes
    print("\n✅ 学习结束！继续加油～")


# 功能5：学习数据展示（纯文本版，无报错）
def show_data():
    """展示学习数据：时长、答题数、正确率"""
    if LEARNING_DATA["total_questions"] == 0:
        print("\n❌ 暂无学习数据！")
        return

    correct_rate = (LEARNING_DATA["correct_count"] / LEARNING_DATA["total_questions"]) * 100
    study_time = LEARNING_DATA["total_study_time"]

    print("\n" + "="*40)
    print("📊 学习数据报告")
    print("="*40)
    print(f"累计学习时长：{study_time} 分钟")
    print(f"总答题数：{LEARNING_DATA['total_questions']} 题")
    print(f"正确题数：{LEARNING_DATA['correct_count']} 题")
    print(f"正确率：{correct_rate:.1f}%")
    print("="*40)


# ===================== 3. 主程序交互 =====================
def main():
    print("=" * 50)
    print("🎓 高中智能学习助手 ")
    print("功能：AI题库 | 自动判分 | 学习计时 | 薄弱点推荐")
    print("=" * 50)

    while True:
        print("\n===== 功能菜单 =====")
        print("1. 📝 AI智能答题")
        print("2. ⏰ 学习计时（番茄钟）")
        print("3. 📊 查看学习数据")
        print("4. 🎯 薄弱点推荐")
        print("0. ❌ 退出程序")

        try:
            choice = int(input("\n请输入功能编号："))
            if choice == 1:
                # 答题模块
                subject = input("请选择科目（数学/物理/化学）：")
                question, ans = generate_question(subject)
                print(f"\n{question}")
                user_input = input("请输入答案：")
                result, tip = check_answer(user_input, ans)
                print(tip)

            elif choice == 2:
                # 计时模块
                t = int(input("请输入学习时长（分钟）："))
                study_timer(t)

            elif choice == 3:
                # 数据展示
                show_data()

            elif choice == 4:
                # 智能推荐
                print("\n" + recommend_weak_point())

            elif choice == 0:
                print("\n👋 感谢使用智能学习助手！")
                break

            else:
                print("❌ 输入错误，请输入有效编号！")

        except ValueError:
            print("❌ 输入错误，请输入数字！")
        except EOFError:
            print("\n❌ 请在终端/命令行中运行此程序！")
            break


# 启动程序
if __name__ == "__main__":
    main()