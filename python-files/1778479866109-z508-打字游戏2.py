import random

print("====自定义字数打字练习====")
s = ""
n = int(input("输入你一分钟挑战的字符个数:"))

for i in range(n):
    s = s + chr(random.randint(97,122))

print(s)
t = input("输入:")
c = 0

for i in range(n):
    if s[i]==t[i]:
        c = c + 1

print("你的正确率为:",round(c/len(s)*100),"%")
input("按回车关闭窗口")