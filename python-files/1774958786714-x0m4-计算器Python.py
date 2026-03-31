import os
import time

def clear_screen():
    """清屏函数，跨平台"""
    os.system('cls' if os.name == 'nt' else 'clear')

def calculator():
    print("简易计算器")
    print("说明：本计算器只能进行 1 步计算（两个数 + 一个运算符）")
    print("输入 o 开始计算，输入 q 退出程序，其他输入会提示重新输入\n")

    while True:
        choice = input("请输入 o 进入计算，或 q 退出：").strip().lower()
        if choice == 'q':
            print("已退出程序，再见～")
            break
        elif choice != 'o':
            print("无效输入，请重新输入！\n")
            continue

        # 进入计算步骤
        try:
            num1 = float(input("请输入第一个数："))
            num2 = float(input("请输入第二个数："))
        except ValueError:
            print("输入有误，必须是数字！程序将重新开始。\n")
            time.sleep(2)
            clear_screen()
            continue

        op = input("请选择运算（加 + / 减 - / 乘 * / 除 /）：").strip()
        if op not in ('+', '-', '*', '/'):
            print("无效运算符，程序将重新开始。\n")
            time.sleep(2)
            clear_screen()
            continue

        # 执行运算
        if op == '+':
            result = num1 + num2
        elif op == '-':
            result = num1 - num2
        elif op == '*':
            result = num1 * num2
        elif op == '/':
            if num2 == 0:
                print("错误：除数不能为 0！\n")
                time.sleep(2)
                clear_screen()
                continue
            result = num1 / num2

        print(f"计算结果：{num1} {op} {num2} = {result}")
        print("将在 10 秒后清屏并重新开始...")
        time.sleep(10)
        clear_screen()

if __name__ == "__main__":
    calculator()
