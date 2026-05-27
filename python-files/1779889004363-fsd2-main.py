# 学生管理系统（OnlineGDB专用纯净版）
stu = []

while True:
    print("====学生管理系统====")
    print("1.添加学生")
    print("2.删除学生")
    print("3.修改学生")
    print("4.查询学生")
    print("5.全部显示")
    print("6.退出")

    try:
        n = int(input("请输入选择："))
    except:
        print("请输入数字！")
        continue

    if n == 1:
        id = input("学号：")
        name = input("姓名：")
        age = input("年龄：")
        stu.append([id, name, age])
        print("添加成功")

    elif n == 2:
        k = input("输入要删除学号：")
        found = False
        for i in stu:
            if i[0] == k:
                stu.remove(i)
                print("删除成功")
                found = True
                break
        if not found:
            print("未找到该学号！")

    elif n == 3:
        k = input("输入要修改学号：")
        found = False
        for i in stu:
            if i[0] == k:
                i[1] = input("新姓名：")
                i[2] = input("新年龄：")
                print("修改成功")
                found = True
                break
        if not found:
            print("未找到该学号！")

    elif n == 4:
        k = input("输入查询学号：")
        found = False
        for i in stu:
            if i[0] == k:
                print(f"学号：{i[0]} 姓名：{i[1]} 年龄：{i[2]}")
                found = True
        if not found:
            print("未找到该学号！")

    elif n == 5:
        if not stu:
            print("暂无学生信息！")
        else:
            for i in stu:
                print(f"学号：{i[0]} 姓名：{i[1]} 年龄：{i[2]}")

    elif n == 6:
        print("退出成功")
        break

    else:
        print("请输入1-6的数字！")