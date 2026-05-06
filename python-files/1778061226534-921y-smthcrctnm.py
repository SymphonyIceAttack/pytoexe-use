import random

# 猜数字
# 可以更改随机数范围，增大难度哦
# 修改范围时，记得提示字符串也要更改
the_number = random.randint(1, 10)
print('Hi，训练师！我们来玩一个猜数字游戏吧！')
guess = int(input('请猜一个1到10之间的秘密数字（包括1和10）: '))
while (guess != the_number):
    if (guess > the_number):
        print(guess,'猜大了，请再来一次！')
    if (guess < the_number):
        print(guess,'猜小了，请再来一次！')
    guess = int(input('再来一次：'))
print(guess,'就是秘密数字！恭喜你猜对了！')
