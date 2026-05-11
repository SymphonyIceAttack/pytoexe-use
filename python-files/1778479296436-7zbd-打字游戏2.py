import random
import os

# 防止打包后一闪而过
def pause():
    os.system("pause")

try:
    s = ""
    n = int(input("输入你要挑战的字符个数："))

    # 随机生成小写字母串
    for i in range(n):
        s = s + chr(random.randint(97, 122))

    print("随机生成字符：", s)
    t = input("请完整输入上面的字符：")

    # 防止输入长度不够
    if len(t) < n:
        print("输入字符数量不足！")
        pause()
        exit()

    c = 0
    # 逐字符比对
    for i in range(n):
        if s[i] == t[i]:
            c = c + 1

    # 计算正确率
    rate = round(c / len(s) * 100)
    print("你的正确率为：", rate, "%")

except:
    print("输入有误，请输入合法数字！")

pause()