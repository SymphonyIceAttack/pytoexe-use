import pyautogui     #导入库
import datetime
import keyboard
import time
print('''截图工具：运行后全屏截图按Ctrl键+Tab键截图间隔1S
      区域截图按Shift键+Tab键选第一坐标再按Q键选第二坐标（
      第一坐标要高于第二坐标，第一坐标要在第二作标的左边）''')
print("需要安装pyautogui，datetime，time，keyboard支持库，否则会出现未知错误")
print("开发者：蔡景皓（jayden)")


def qpjt():         #定义函数
    im1 = pyautogui.screenshot()#截图
    dt = datetime.datetime.now()#获取时间
    pyautogui.screenshot(f'C:\\Users\\caija\\Desktop\\程序\\python\\{dt.strftime("%Y-%m-%d %H%M%S")}(QP).jpg')   #路径可改("C:(D:)\......(文件夹名称）\......(文件夹名称)\......(图片名称，默认screen){dt.strftime("%Y-%m-%d %h%M%s")}.jpg")
    print(r"保存路径为：C:\Users\caija\Desktop\程序\python.......jpg")  #可改


def xqjt(x,y,c,k):  #定义函数
    im1 = pyautogui.screenshot(region=(x, y, c, k))#截图
    dt = datetime.datetime.now()                   #获取时间
    im1.save(f'C:\\Users\\caija\\Desktop\\程序\\python\\{dt.strftime("%Y-%m-%d %H%M%S")}(QY).jpg')                     #路径可改("C:(D:)\......(文件夹名称）\......(文件夹名称)\......(图片名称，默认screen){dt.strftime("%Y-%m-%d %h%M%s")}.jpg")
    print(r"保存路径为：C:\Users\caija\Desktop\程序\python.......jpg")  #可改


while True:                    #监听按键
    if keyboard.is_pressed("Ctrl") and keyboard.is_pressed("Tab"):#监听
        qpjt()
    time.sleep(1)

    if keyboard.is_pressed("Shift") and keyboard.is_pressed("Tab"):
        print("第一坐标")
        x1, y1 = pyautogui.position()
        print(x1,y1)
    time.sleep(0.2)
    
    if keyboard.is_pressed("Q"):
            x2, y2 = pyautogui.position()
            print("第二坐标")
            print(x2,y2)
            xqjt(x1,y1,x2,y2)
#HIT开源协议（禁止更改5,6,7，8,9行)