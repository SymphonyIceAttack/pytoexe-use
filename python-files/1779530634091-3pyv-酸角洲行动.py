import time
print("欢迎来到酸角洲行动,世界最好玩的游戏\n")
time.sleep(0.5)
print("*你开了把绝密航天*")
renshu = 18
time.sleep(0.2)
print("现在绝密航天有"+str (renshu)+"个人")
time.sleep(0.5)

while True:
    kill = input("威龙干员这次清理了多少个敌人:")
    kill = int(kill)

    xc = renshu - kill
    renshu = xc
    if xc > 1:
        print("航天基地还剩下" + str(xc) + "个人")
    if xc == 1:
        print("你成功单人清图，被封号了")
        break
    if xc > 18:
        print("航天基地人口增加，牢太高兴地笑了")
    if xc > 30:
        print("由于人数众多，琳琅天下的服务器卡爆了，你拯救了世界!")
        break
    if xc ==0:
        print("你杀疯了，最后连自己也要杀。你死于自雷")
        break
    if xc < 0:
        print("你杀疯了，连小兵和策划也不放过，你消灭了琳琅天上，拯救了世界！")
        break