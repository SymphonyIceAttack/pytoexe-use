while True:
    print:("欢迎使用本软件，请登录")
    user=input("请输入用户名：")
    if user!="cjsj":
        print("没有找到此账户")
    else:
       pwd=input("请输入密码：")
       if pwd!="12345678":
          print("密码有误")
       else:
            break
print("登陆成功，软件启动中....")
print("电子长颈鹿 v1.1.0（design by cjsj）")
print("HI，我是电子长颈鹿")
N=input("请告诉我你的需求：")
if N=="1":
    print("脖子已经伸长至114514m")
elif N=="2":
    print("脖子已缩短至0.00000001mm")
elif N=="3":
    a=float(input("请输入第一个数"))
    b=float(input("请输入第二个数"))
    S=a+b
    print("答案是",S)
elif N=="4":
    c=float(input("请输入第一个数"))
    d=float(input("请输入第二个数"))
    K=c-d
    print("答案是",K)
elif N=="5":
    e=float(input("请输入第一个数"))
    f=float(input("请输入第二个数"))
    Q=e*f
    print("答案是",Q)
elif N=="6":
    g=float(input("请输入第一个数："))
    h=float(input("请输入第二个数："))
    J=g/h
    print("答案是",J)
else:
    print("正在开发中…")



    

    
    
    

 
