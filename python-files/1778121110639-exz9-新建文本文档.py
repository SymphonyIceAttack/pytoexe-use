import random

def generate_question(digit, op):
    """
    根据位数和运算符生成题目
    :param digit: 数字位数（1=个位数，2=两位数...）
    :param op: 运算符 + - * /
    :return: 题目表达式，正确答案
    """
    # 生成对应位数的随机数范围
    min_num = 10 ** (digit - 1) if digit > 1 else 0
    max_num = 10 ** digit - 1

    # 循环生成合法题目（除法必须整除）
    while True:
        a = random.randint(min_num, max_num)
        b = random.randint(min_num, max_num)

        if op == "+":
            ans = a + b
            return f"{a} + {b} = ", ans
        elif op == "-":
            # 保证结果非负
            a, b = (a, b) if a >= b else (b, a)
            ans = a - b
            return f"{a} - {b} = ", ans
        elif op == "*":
            ans = a * b
            return f"{a} × {b} = ", ans
        elif op == "/":
            # 除法保证：整除 + 除数不为0 + 结果为整数
            if b == 0:
                continue
            if a % b == 0:
                ans = a // b
                return f"{a} ÷ {b} = ", ans

def main():
    print("=" * 40)
    print("      小学数学出题器（可调整位数）")
    print("=" * 40)

    # 1. 选择数字位数
    while True:
        try:
            digit = int(input("\n请输入数字位数（1=个位，2=两位...）："))
            if digit >= 1:
                break
            else:
                print("请输入大于0的数字！")
        except ValueError:
            print("输入无效，请输入整数！")

    # 2. 选择运算类型
    print("\n请选择运算类型：")
    print("1. 加法")
    print("2. 减法")
    print("3. 乘法")
    print("4. 除法")
    print("5. 混合运算")

    while True:
        try:
            op_choice = int(input("请输入选项（1-5）："))
            if op_choice in range(1, 6):
                break
            else:
                print("请输入1-5之间的数字！")
        except ValueError:
            print("输入无效，请输入整数！")

    # 3. 选择题目数量
    while True:
        try:
            total = int(input("\n请输入出题数量："))
            if total > 0:
                break
            else:
                print("请输入大于0的数字！")
        except ValueError:
            print("输入无效，请输入整数！")

    # 运算符列表
    op_list = []
    if op_choice == 1:
        op_list = ["+"]
    elif op_choice == 2:
        op_list = ["-"]
    elif op_choice == 3:
        op_list = ["*"]
    elif op_choice == 4:
        op_list = ["/"]
    elif op_choice == 5:
        op_list = ["+", "-", "*", "/"]

    # 开始答题
    correct = 0
    print("\n" + "=" * 40)
    print("开始答题！")
    print("=" * 40)

    for i in range(total):
        op = random.choice(op_list)
        question, ans = generate_question(digit, op)

        # 输入答案
        while True:
            try:
                user_ans = int(input(f"\n第{i+1}题：{question}"))
                break
            except ValueError:
                print("输入无效，请输入整数！")

        # 判断对错
        if user_ans == ans:
            print("✅ 回答正确！")
            correct += 1
        else:
            print(f"❌ 回答错误，正确答案：{ans}")

    # 最终成绩
    print("\n" + "=" * 40)
    print("答题结束！")
    print(f"总题数：{total}")
    print(f"正确数：{correct}")
    print(f"正确率：{correct / total * 100:.1f}%")
    print("=" * 40)

if __name__ == "__main__":
    main()