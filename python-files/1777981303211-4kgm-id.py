import random
ap = str(random.randint(1,100))
id = []
password = []
t = []
mo = []
m = ["sb","傻帽","傻逼","他妈","我艹","我操","爸爸"]
vip_list = []
ctid = "游客"
b = 1
while True:
    print("欢迎来到宋都帖,",ctid)
    print("1=注册，2=登陆，3=搜索，4=钱包，5=发帖，6=注销账户，7=退出账户，8=退出")
    l = input("请选择:")
    if l == "1":
        idz = input("请输入你要注册的id(可以是任何字符，汉字或者是其他都行):") 
        pdz = input("请输入您注册时的密码(请牢记):")
        is_id = True
        for p in id:
            if p == idz:
                is_id = False
        if idz == "admin":
            is_id = False
        if is_id:
            id.append(idz)
            password.append(pdz)
            mo.append(0)
            vip_list.append("普通账号")
            t.append("这是一个新账号哦,暂时没有帖子。")
        else:
            print("用户不能重名")
    elif l == "2":
        d = input("请输入你需要登录的id：")
        b = input("请输入此id的密码:")
        if ctid != "admin":
            if d in id:
                n = id.index(d)
                if password[n] == b:
                    ctid = d
                    print("登陆成功")
                else:
                    print("密码错误")
            elif d == "admin" and b == "root" and ctid == "游客":
                ctid = "admin"
                print("已登录管理员账户，本次清空余额随机数是",ap)
            else:
                print("没有该用户")
        else:
            if d in id:
                print("管理员强制登录成功")
                ctid = d
            else:
                print("因为没有此账户,所以无法登陆")
    elif l == "3":
        s = input("请输入你想搜索的id:")
        if s in id:
            print("成功搜索到")
            n = id.index(s)
            print("他发的最后的帖子是:",t[n])
            print("他是",vip_list[n])
            if ctid == "admin":
                x = input("是否清空账户(输入随机数，不清空直接回车):")
                if x == ap:
                    mo[n] = 0
                    vip_list[n] = "普通账户(被清空)"
                    t[n] = "这是一个新账号哦,暂时没有帖子。"
                    print("清空成功")
        else:
            print("没有搜索到")
    elif l == "4":
        print("1=查看余额")
        print("2=转账")
        print("3=VIP")
        x = input("请选择:")
        if x == "1":
            if ctid != "游客" and ctid != "admin":
                if x == "1":
                    print(mo[id.index(ctid)])
            elif ctid == "游客":
                print("请登录后使用支付功能")
            else:
                print("∞")
        elif x == "2":
            a = input("你要给谁转账:")
            if a in id:
                if vip_list[id.index(a)] != "普通账户(被清空)":
                    v = float(input("请输入给他转账的金额(请勿输入非数):"))
                    if ctid != "admin":
                        if mo[id.index(ctid)] >= v:
                            mo[id.index(ctid)] -= v
                            mo[id.index(a)] += v
                            print("成功转账",v)
                        else:
                            print("金额不足")
                    else:
                        mo[id.index(a)] += v
                        print("成功转账",v)
                else:
                    print("禁止给被清空的账号转账")
            else:
                print("没有该用户")
        elif x == "3":
            if ctid != "admin" and ctid != "游客":
                print("1=CVIP 3元")
                print("2=VIP 6元")
                print("3=SVIP 12元")
                n = input("请选择你要充值的vip:")
                if n == "1":
                    if mo[id.index(ctid)] >= 3:
                        mo[id.index(ctid)] -= 3
                        vip_list[id.index(ctid)] = "CVIP"
                    else:
                        print("账户中没有钱可供支付")
                elif n == "2":
                    if mo[id.index(ctid)] >= 6:
                        mo[id.index(ctid)] -= 6
                        vip_list[id.index(ctid)] = "VIP"
                    else:
                        print("账户中没有钱可供支付")
                elif n == "3":
                    if mo[id.index(ctid)] >= 12:
                        mo[id.index(ctid)] -= 12
                        vip_list[id.index(ctid)] = "SVIP"
                    else:
                        print("账户中没有钱可供支付")
                else:
                    print("选项错误")
            else:
                print("游客或者管理员不能进行vip充值")
    elif l == "5":
        if ctid != "admin" and ctid != "游客":
            w = input("请输入你想发的帖子(仅支持文字):")
            n = id.index(ctid)
            yes = True
            for c in m:
                if c in w:
                    yes = False
                    print("当前有敏感词哦，坚决不发敏感词，共同维护社区环境。")
            if yes:
                t[n] = w
        else:
            if ctid == "admin":
                print("您当前处于管理员账户不能发帖")
            else:
                print("您当前处于游客状态不能发帖")
    elif l == "6":
        i = input("确定？(Y/N):")
        if i == "Y" or i == "y":
            if ctid == "游客":
                print("您当前处于游客状态")
            elif ctid == "admin":
                print("管理员账户禁止注销")
            else:
                n = id.index(ctid)
                password.pop(n)
                id.remove(ctid)
                t.pop(n)
                mo.pop(n)
                vip_list.pop(n)
                ctid = "游客"
    elif l == "7":
        ctid = "游客"
    elif l == "8":
        break
    else:    
        print("您输入的可能有误")
    print("--------------------")
