import random
import os

def main():
    s = ""
    n = int(input("输入你一分钟挑战的字符个数:"))

    for i in range(n):
        s = s + chr(random.randint(97,122))

    print("随机字母串：", s)
    t = input("请输入:")

    # 长度不够容错
    if len(t) < n:
        print("输入长度不足，无法统计！")
        os.system("pause")
        return

    c = 0
    for i in range(n):
        if s[i] == t[i]:
            c = c + 1

    rate = round(c / len(s) * 100)
    print("你的正确率为:", rate, "%")

if __name__ == "__main__":
    try:
        main()
    except:
        print("请输入正确的整数！")
    os.system("pause")