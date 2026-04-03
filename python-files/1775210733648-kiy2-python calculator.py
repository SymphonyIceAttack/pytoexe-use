print("===== stars计算器(星辰） =====")
print("输入如：1+1  或  1+2+3+4  按回车直接算")
print("输入 t 并按回车可关闭程序\n")

while True:
    exp = input("请输入算式：")
    if exp == "t":
        print("正在关闭程序...")
        break
    try:
        print("结果 =", eval(exp))
    except:
        print("输入有误，请重新输入\n")