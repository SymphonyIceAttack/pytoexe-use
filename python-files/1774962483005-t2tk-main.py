import time
while True:
    print('>>>>>>>>>>>>>>>>>>>>>>>>')
    print('请输入卡密')
    print('<<<<<<<<<<<<<<<<<<<<<<<<')
    yz = input()
    if yz == 'bf473556' or yz == '91780p8j' or yz == 'long430p':
        time.sleep(1)
        print('验证完成')
        print('91一键root')
        print('是否root(y/n)')
        yz = input()
        if yz == 'y':
            print('正在加载资源库')
            time.sleep(10)
            print('完成')
            time.sleep(1)
            print('开始root')
            root = 0
            for i in range(100):
                time.sleep(1)
                root = root + 1
                print('root进度 ' + str(root) + '%')
            print('root完成')
            break
        elif yz == 'n':
            break
    else:
        time.sleep(1)
        print('验证失败')