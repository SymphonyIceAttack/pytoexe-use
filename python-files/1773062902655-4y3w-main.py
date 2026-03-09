import platform
import tkinter as tk
import turtle
import os
import random
#import pygame 注意，我写的编辑器没有pygame，记得安装。
import time
import os
import webbrowser
import requests






def countdown(seconds):
    while seconds:
        mins, secs = divmod(seconds, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        seconds -= 1


def youxi01():
    webbrowser.open("surf\index.html")
    print('正在打开···')
    print('按任意键回去···')
    os.system('pause')
    cls()
    menu()
def youxi02():
    print('正在读取您的段位')
    dwjj=0
    with open('段位.txt', 'r+', encoding='utf-8') as f:
        dw = f.read()
    with open('需要升级.txt', 'r+', encoding='utf-8') as ff:
        sj = ff.read()
        sj=int(sj)
    print(f'你的段位是:{dw}')
    if dw=='废铁青铜':
        dwsjjs=10-sj
        print(f'你还要胜利{dwsjjs}聚即可晋级：菜鸟白银')
    print("     猜数游戏(暂时没有完善段位)")
    print('1.我是fw（1~50）')
    print("2.我没实力（1~100）")
    print("3.我有实力（1~100+说谎)")
    aaa=0
    aaa=int(input('输入:'))
    if aaa==1:
        bbbb = random.randint(1, 50)
        while 1:
            aaaa=int(input('键入数字'))
            
            if aaaa==bbbb:
                print('对了')
                break
            else:
                if aaaa>bbbb:
                    print('大了')
                if aaaa<bbbb:
                    print('小了')
        cls()
        menu()
    if aaa == 2:
        bbbb = random.randint(1, 100)
        while 1:
            aaaa = int(input('键入数字'))
            
            if aaaa == bbbb:
                print('对了')
                break
            else:
                if aaaa > bbbb:
                    print('大了')
                if aaaa < bbbb:
                    print('小了')
    cls()
    menu()
    if aaa == 3:
        bbbb = random.randint(1, 100)
        while 1:
            a91=random.randint(1,2)
            aaaa = int(input('键入数字'))
            
            if aaaa == bbbb and a91==1:
                print('对了')
                break
            if aaaa==bbbb and a91!=1:
                print('大了')
            else:
                if aaaa > bbbb and a91==1:
                    print('大了')
                if aaaa < bbbb and a91==1:
                    print('小了')
                if aaaa>bbbb and a91==1:
                    print('小了')
                if aaaa<bbbb and a91==1:
                    print('大了')
        cls()
        menu()


def menu():
    print('[这是公告]  v2.0发布/马里奥已修复无网络不可使用。增加了实用工具')
    print('     实用工具箱')
    print('1.打开冲浪（fw给我爆开）')
    print('2.猜数字')
    print('3.设置')
    print('4.算一卦')
    print("5.极客战记，启动")
    print("6.快点给我打开112.124.61.116")
    print("7.表情包编辑器")
    print("8.击杀国王")
    print("9.关于")
    print("10.迷宫")
    print("11.超级玛丽")
    print('12.马里奥（超级像原版）')
    print('13.我是老师？')
    print("14.快捷更新")
    print('15.新的刷题站点')
    dk = '不道啊'
    dk = int(input('输入序号选择：'))

    if dk == 15:
       webbrowser.open('http://112.11.184.93:5858/uhome')
       cls()
       menu()
    if dk == 1:
        youxi01()
        cls()
    if dk==14:
        a=input("输入您获得的安装密钥:")
        webbrowser.open("https://xuewang.lanzoub.com/"+a)

    if dk==12:
        webbrowser.open("bin\马里奥.html")
        cls()
        menu()
    if dk==13:
        webbrowser.open("bin\教师节，老师辛苦了，我帮他阅卷修改了1次错别字，是不是很棒呢，试试！.html")
        cls()
        menu()
    if dk == 2:
        youxi02()
    if dk==6:
        webbrowser.open("112.124.61.116/loginpage.php")
    if dk==3:
        print('啥也没有~')
        time.sleep(3)
        cls()
        menu()

    if dk==4:
        #初始化
        ssb=0
        print('回车开始')
        input()
        ssb=random.randint(1,4)
        if ssb==1:
            print('大吉')
        if ssb==2:
            print('吉')
        if ssb==3:
            print("末吉")
        if ssb==4:
            print('凶')
        print("回车退出")
        input()
        cls()
        menu()
    if dk==5:
        print('没做')
        time.sleep(3)
        cls()
        menu()
    if dk==7:
        webbrowser.open('bin\HTML5 Emoji自定义表情编辑器DEMO演示.html')
        cls()
        menu()
    if dk==8:
        webbrowser.open('bin\kill-the-king.html')
        cls()
        menu()
    if dk==9:
        print('     关于')
        print('作者：你的爸爸————xw')
        print('QQ:3821748595')
        print('     在这里感谢游戏作者')
        cls()
        menu()
    if dk == 10:
        webbrowser.open('bin\摸鱼小游戏 _ 迷宫 _ 海拥.html')
    if dk==11:
        webbrowser.open('bin\超级玛丽.html')

def cls():
    print("\033[2J\033[H", end='')
os_name = os.name
print(f'系统:{os_name}')
if os_name=='nt':
    print('已查询到内容：windows10')
else:
    print('未知。')
print('程序正在检查完整性')
with open('system.txt', 'r+', encoding='utf-8') as fff:
    jiaoyan=fff.read()
if jiaoyan:
    cls()
    menu()
print('通过！！！')
print('输入密钥：')
aaa=input()
if aaa=='SNOWKING1145919178':
    print('即将进入')
    countdown(3)
    print(1)
    cls()
    menu()
else:
    print('校验不通过！！！')
