import msvcrt
import ctypes
import time
import os

#----------功能部分----------

#声明
def home():
    pass

#消息
def tips(message):
    os.system("cls")    
    os.system("color F0")
    print(message)
    os.system("color 0F")

#错误处理
def err_out(err,help):
    print("ERROR:" + err)
    print(help)
    tips("按下任意键回到主界面")
    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            home()
        time.sleep(0.01)

#与home()相同作用，用于home()函数内跳转到自己
def gethome():
    home()

#----------游戏部分----------

#游戏内
def game(playernum,gamehp):
    #初始化变量
    win = False
    currentplayer = 0
    cacheword = ""
    gamenum = []
    gamehps = []
    ongame = []    
    cachebool = True
    isboom = False
    notongames = 0
    for i in range(playernum):
        gamehps.append(gamehp)
        ongame.append(True)
    #游戏循环
    while not win:
        currentplayer %= playernum
        #游戏单次人循环
        for i in range(playernum):
            #判断当前玩家
            while not ongame[currentplayer]:
                currentplayer = currentplayer + 1
                if currentplayer >= playernum:
                    currentplayer = 0
            if currentplayer >= playernum:
                currentplayer = 0
            #游戏交互
            tips("当前：第" + str(currentplayer + 1) + "位玩家")
            print("按任意键开始计时，再次按任意键结束，不能超过一秒")
            print("当前炸弹数字列表：")
            cacheword = ""
            i = 0
            for i in range(len(gamenum)):
                cacheword = cacheword + "  " + str(gamenum[i])
            print(cacheword)
            #计时部分
            cachebool = True
            while cachebool:
                #检测是否开始计时
                if msvcrt.kbhit():
                    start = time.perf_counter()
                    tips("按任意键结束计时")
                    msvcrt.getch()
                    while True:
                        #检测是否结束计时
                        if msvcrt.kbhit():
                            end = time.perf_counter()
                            cost_seconds = end - start
                            if cost_seconds >= 1:
                                #超过1秒，重新计时
                                tips("已超过一秒，请重新按任意键开始计时")
                                break
                            else:
                                #检测列表里的数字
                                i = 0
                                for i in range(len(gamenum)):
                                    if gamenum[i] == round(cost_seconds,2):
                                        #列表里拥有这个数字的处理
                                        tips("你的秒数是：" + str(round(cost_seconds,2)) + "列表里刚好拥有这个数字，你的血量-1")
                                        isboom = True
                                        gamehps[currentplayer] -= 1
                                        gamenum.pop(i)
                                        print("你的剩余血量：" + str(gamehps[currentplayer]))
                                        break
                                if not isboom:
                                    #列表里未拥有这个数字的处理
                                    tips("你的秒数是：" + str(round(cost_seconds,2)) + "秒，列表里没有这个数字")
                                    gamenum.append(round(cost_seconds,2))
                                #通用的变量等其他处理
                                isboom = False
                                cachebool = False
                                msvcrt.getch()
                                time.sleep(2)
                                break
                            msvcrt.getch()
                        time.sleep(0.01)
                time.sleep(0.01)
            i = 0
            currentplayer += 1
            #检测玩家是否死亡
            for i in range(playernum):
                if ongame[i]:
                    if gamehps[i] <= 0:
                        ongame[i] = False
                        notongames = notongames + 1
            #检测是否胜利
            if notongames == playernum - 1:
                win = True
                break
    #游戏结束处理
    i = 0
    while not ongame[i]:
        i += 1
    tips(str(i + 1) + "号玩家获得胜利")
    print("按任意键返回主菜单")
    while True:
        if msvcrt.kbhit():
            msvcrt.getch()
            home()
        time.sleep(0.01)

#主界面
def home():
    #显示游戏名、提示及版本号
    os.system("cls")
    tips("按任意键开始游戏")
    print("\n\n\n     秒表炸弹V1.0")
    #与用户交互确认游玩人数、每人血量后开始游戏
    while True:
        if msvcrt.kbhit():
            os.system("cls")
            msvcrt.getch()
            #用户输入人数及每人血量
            players = input("\n\n\n\n    请输入游玩的人数：")
            os.system("cls")
            hps = input("\n\n\n\n    请输入每人的血量：")
            #判断是否为大于1的整数
            if players.isdigit() and hps.isdigit():
                num = int(players)
                hp_num = int(hps)
                if num > 1 and hp_num > 1:
                    #彩蛋
                    if num == 114514:
                        os.system("start https://www.bilibili.com/video/BV1GJ411x7h7/")
                    #加载游戏
                    tips("加载中...")
                    game(num,hp_num)
                else:
                    tips("请输入大于1的整数")
                    break
            else:
                tips("请输入大于1的整数")
                break
        time.sleep(0.01)
    gethome()

#主函数
if __name__ == '__main__':
    home()