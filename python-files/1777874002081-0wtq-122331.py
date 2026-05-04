import random


# 石头剪刀布
choices = ['石头','布','剪刀']
print('Hi，训练师！我是编程猫！很高兴遇见你！现在我们来玩石头剪刀布的游戏吧！')
print('石头剪刀布！')
player = input('你要出石头呢，还是剪刀呢，还是布？（如输入“退出”，可退出游戏）')
# 直到退出游戏之前，下面的循环都会继续
while (player != '退出'):
    # 验证玩家和电脑各自的选择
    computer = random.choice(choices)
    print((((('你出了' + player) + '，电脑出了') + computer) + '...'))
    if (player == computer) :
        print("平局！")
    elif (player == '石头') :
        if computer == "剪刀":
            print("你赢了！")
        else:
            print("电脑赢了！")
    elif (player == '布') :
        if computer == "石头":
            print("你赢了")
        else:
            print("电脑赢了！")
    elif (player == '剪刀') :
        if computer == "布":
            print("你赢了")
        else:
            print("电脑赢了！")
    else :
        print("出错了哦！只能出“石头”“剪刀”或“布”！")
    # 立即再来一轮，直到退出游戏
    print('石头剪刀布！')
    player = input('你要出石头呢，还是剪刀呢，还是布？（如输入“退出”，可退出游戏）')
