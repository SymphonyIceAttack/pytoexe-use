from tronpy import Tron
import time

print("="*50)
print(" 波场靓号地址生成器 - 自定义最后4位")
print("="*50)
suffix = input("请输入你想要的【最后4位】：").strip()

if len(suffix) != 4:
    print("必须输入4位！")
    exit()

print("\n正在寻找以 " + suffix + " 结尾的地址...\n")

count = 0
start = time.time()

while True:
    wallet = Tron().generate_wallet()
    addr = wallet["base58check_address"]
    
    if addr.endswith(suffix):
        print("\n🎉 找到啦！")
        print("="*50)
        print(f"地址：{addr}")
        print(f"私钥：wallet['private_key']")
        print("="*50)
        print("⚠️ 私钥=钱，绝对不要泄露！")
        break
    
    count += 1
    if count % 500 == 0:
        print(f"已尝试：{count} 次")

print(f"耗时：{round(time.time()-start,2)} 秒")
input("按回车退出")