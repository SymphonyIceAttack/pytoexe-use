def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0

def collatz_odd_step(x):
    val = 3 * x + 1
    while val % 2 == 0:
        val = val // 2
    return val

def get_order(num):
    if num <= 0:
        return "请输入正整数"
    order = 0
    current = num
    while True:
        if is_power_of_two(current):
            return order + 1
        if current % 2 == 1:
            current = collatz_odd_step(current)
            order += 1
        else:
            current = current // 2

if __name__ == "__main__":
    print("=== 考拉兹阶数判断器（你的定义）===")
    print("输入十进制：直接输入数字")
    print("输入二进制：以 0b 开头，例如 0b1010111")
    print("输入 q 退出\n")
    
    while True:
        user_input = input("请输入数字：").strip()
        if user_input.lower() == 'q':
            break
        try:
            if user_input.startswith("0b"):
                number = int(user_input, 2)
            else:
                number = int(user_input)
            
            res = get_order(number)
            print(f"→ 阶数 = {res}\n")
        except:
            print("输入格式错误，请重试\n")