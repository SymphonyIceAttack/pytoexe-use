print("  \033[35m※※CDK激活工具※※\033[0m")#软件名称
print("作者：Serve Peoples"    +"   \033[32mV2.5.3\033[0m") #版本号
print("")   #换行
print("\033[31m声明：本软件著作权及所有权归lucky game tools所有，未经许可不得复制、修改、商用，违者追究法律责任。\033[0m")  #声明
print("")   #换行
print("⌈此程序3分钟后，自动关闭⌋") #提醒语句1
print("")   #换行
a = ""  #赋值游戏ID
while len(a := input("请输入7位纯数字的游戏ID：")) != 7: print("\033[31m输入错误！请输入7位纯数字ID：\033[0m")    #判断游戏ID格式
print("")   #换行
b=input("请粘贴CDK代码⌈粘贴代码⌋：") #输入或粘贴CDK代码
print("")   #换行
print("请复制激活码:"+">>"+"\033[32mdrm"+str(a)+"|"+str(b)+"\033[0m""<<")#输出最终结果
print("软件网址：https://luckygametools.github.io/README_zh.html")   #软件网址
import time #调用time模块
time.sleep(180)  # 窗口保持180秒后自动关闭