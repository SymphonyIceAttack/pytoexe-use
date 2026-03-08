import random
print('Administrator信息发送器：程序已激活')
n=random.randint(100000,999999)
m=random.randint(1, 500)
If=1
name=input('输入用户名：')
print('您好，'+name+'用户，欢迎游玩猜数字游戏')
print('您有10次机会')
print('范围是1~500')
print('Administrator信息发送器：数字已准备')
print('Terminal信息发送器：验证码为',n,sep='')
o=int(input('输入验证码：'))
if(o==n):
    print('验证码正确✅️')
    print('Administrator信息发送器：信息加载完毕')
    print('Administrator信息发送器：🛜网络已连接')
    print('Administrator信息发送器：数字大小为',(m//100)*100,'~',(m//100)*100+100,sep='')
    for i in range(1,10):
        o=int(input(f'第{i}次输入数字：'))
        if o==m:
            print('回答正确✅️')
            If=0
            break
        if o<m:
            print('数字太小了，请修改')
        if o>m:
            print('数字太大了，请修改')
        print('您还有',10-i,'机会',sep='')
    if If==1:
        print('正确答案是'+m)
else:
    print('验证码错误❌')
print('Terminal信息发送器：已退出')
