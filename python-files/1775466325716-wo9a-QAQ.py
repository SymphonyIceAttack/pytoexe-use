import random

def generate_random_numbers():
    print("===== 随机整数生成器 =====")
    try:
        # 1. 获取用户输入的范围
        min_num = int(input("请输入范围的最小值："))
        max_num = int(input("请输入范围的最大值："))

        # 判断范围是否合法
        if min_num >= max_num:
            print("错误：最小值必须小于最大值！")
            return

        # 2. 获取用户需要生成的数字个数
        count = int(input("请输入需要生成的数字个数："))

        # 判断个数是否合法
        total_range = max_num - min_num + 1
        if count <= 0 or count > total_range:
            print(f"错误：个数必须在 1 ~ {total_range} 之间！")
            return

        # 3. 生成不重复的随机数
        random_list = random.sample(range(min_num, max_num + 1), count)

        # 4. 输出结果
        print(f"\n在 [{min_num}, {max_num}] 范围内随机生成 {count} 个不重复数字：")
        print(random_list)

    # 处理非整数输入的异常
    except ValueError:
        print("错误：请输入有效的整数！")

# 运行主函数
if __name__ == "__main__":
    generate_random_numbers()