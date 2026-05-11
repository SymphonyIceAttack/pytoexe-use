# 个人记账工具
import datetime

def main():
    records = []
    print("===== 极简记账工具 =====")
    print("功能：记录收入/支出，自动算余额")
    
    while True:
        print("\n请选择操作：")
        print("1. 添加收入")
        print("2. 添加支出")
        print("3. 查看所有记录")
        print("4. 退出")
        
        choice = input("输入选项(1-4): ")
        
        if choice == "1":
            amount = float(input("输入收入金额: "))
            desc = input("输入收入说明: ")
            records.append(("收入", amount, desc, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            print("✅ 收入已记录！")
            
        elif choice == "2":
            amount = float(input("输入支出金额: "))
            desc = input("输入支出说明: ")
            records.append(("支出", amount, desc, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            print("✅ 支出已记录！")
            
        elif choice == "3":
            if not records:
                print("📝 暂无记录")
                continue
                
            print("\n--- 所有记账记录 ---")
            balance = 0
            for idx, (typ, amt, desc, time) in enumerate(records, 1):
                if typ == "收入":
                    balance += amt
                    print(f"{idx}. [{time}] {typ}: +{amt}元 - {desc}")
                else:
                    balance -= amt
                    print(f"{idx}. [{time}] {typ}: -{amt}元 - {desc}")
                    
            print(f"\n💰 当前余额: {balance:.2f}元")
            
        elif choice == "4":
            print("退出记账工具，拜拜~")
            break
            
        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    main()