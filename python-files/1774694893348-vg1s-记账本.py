账本 = []
print('-----家庭记账本-----')


while True : 
    项目 = input('您想记什么\^o^/?   (收入/支出/查看/结束)')
    if 项目 == '结束': 
        break


    elif 项目 == '查看' :
            print('----账本记录----')
            for 一条 in 账本: 
                print(一条)

            总收入 = 0
            总支出 = 0

            for 一条 in 账本 :
                 if'收入' in 一条 :
                    总收入 = 总收入 + int(一条.split('+')[1])               
                 elif '支出' in 一条 :
                       总支出 = 总支出 + int(一条.split('-')[1])


            print('总收入：' + str(总收入) + '元') 
            print('总支出：' + str(总支出) + "元")   
            print('结余：' + str(总收入 - 总支出) + '元')
            print('----   \n') 


    elif 项目 == '收入' : 
            金额 = int(input('多少钱'))
            说明 = input('什么收入？')
            账本.append(说明 + "+" + str(金额) + "元")
            print('记好啦OvO  \n')



    elif 项目 == '支出' :
        金额 = int(input('多少钱？'))
        说明 = input('买了什么呢-O-?')
        账本.append(说明 + '-' + str(金额) + '元')
        print('记好啦OvO   \n')



    else :
            print('我看不懂噢T^T, 请输入 : 收入/支出/查看/结束   \n')


print("感谢使用(●'v'●)")
