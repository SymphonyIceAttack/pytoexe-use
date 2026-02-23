import winreg
import time
import msvcrt
import sys

def check_ipv6_status():
    """检测IPv6当前状态"""
    try:
        # 尝试打开注册表键
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters")
        value, _ = winreg.QueryValueEx(key, "DisabledComponents")
        winreg.CloseKey(key)
        
        # 检查值是否为0xffffffff（禁用状态）
        if value == 0xffffffff:
            return "已关闭"
        else:
            return "已开启"
            
    except FileNotFoundError:
        # 注册表键值不存在，表示IPv6是默认开启状态
        return "已开启"
    except Exception as e:
        return f"检测失败: {str(e)}"

def enable_ipv6():
    """开启IPv6"""
    try:
        # 尝试打开注册表键
        key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters"
        
        try:
            # 尝试打开现有键
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE)
            try:
                # 尝试删除DisableComponents值（完全启用IPv6）
                winreg.DeleteValue(key, "DisabledComponents")
                print("已删除IPv6禁用标志，IPv6已完全启用。")
            except FileNotFoundError:
                # 如果值不存在，说明IPv6已经是启用状态
                print("IPv6已处于启用状态，无需更改。")
            winreg.CloseKey(key)
            
        except FileNotFoundError:
            # 如果键不存在，则创建它并确保没有禁用标志
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            winreg.CloseKey(key)
            print("已创建IPv6相关注册表项，IPv6已启用。")
        
        return True
        
    except Exception as e:
        print(f"开启IPv6时出错: {e}")
        return False

def disable_ipv6():
    """禁用IPv6"""
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters")
        winreg.SetValueEx(key, "DisabledComponents", 0, winreg.REG_DWORD, 0xffffffff)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"禁用IPv6时出错: {e}")
        return False

def wait_for_exit():
    """等待用户选择是否退出"""
    print("\n程序运行完成！")
    print("按 'f' 键取消自动退出，程序将保持运行并返回主菜单")
    print("否则程序将在10秒后自动退出...")
    
    # 设置10秒倒计时
    for i in range(10, 0, -1):
        print(f"\r剩余时间: {i}秒 (按'f'取消退出)", end="", flush=True)
        
        # 检查是否有按键输入（非阻塞方式）
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            if key == 'f':
                print(f"\n\n已取消自动退出，返回主菜单...")
                # 不等待任意键，直接返回True表示继续
                return True  # 表示用户取消了退出，并想要继续
        
        time.sleep(1)
    
    print("\n\n时间到，程序即将退出...")
    return False  # 表示将自动退出

def main():
    # 第一行声明 - 居左显示
    print("本软件由抖音@爱玩电脑的mini2se制作       无偿分享使用")
    
    # 第二行声明 - 居左显示
    print("本软件最高售价为人民币0.01元，使用本软件售卖圈钱狗死全家！！！")
    
    # 空三行
    print()
    print()
    print()
    
    # 检测IPv6状态
    print("正在检测IPv6状态...")
    status = check_ipv6_status()
    print(f"前 IPv6 状态: {status}")
    
    while True:
        # 显示操作选项
        print("\n请选择操作:")
        print("   开启IPv6")
        print("   关闭IPv6")
        choice = input("请输入数字1或2: ")
        
        # 根据选择和当前状态执行操作
        if choice == '1':
            if status == "已开启":
                print("IPv6已处于开启状态，无需操作。")
            else:
                print("正在执行IPv6开启操作...")
                if enable_ipv6():
                    print("IPv6已成功开启或确认已开启。")
                    print("请注意：更改可能需要重启计算机才能生效。")
                    # 更新状态
                    status = "已开启"
                else:
                    print("错误：无法开启IPv6。请确保以管理员身份运行此脚本，并检查注册表权限。")
        elif choice == '2':
            if status == "已关闭":
                print("IPv6已处于关闭状态，无需操作。")
            else:
                print("正在执行IPv6关闭操作...")
                if disable_ipv6():
                    print("IPv6已成功关闭。")
                    print("请注意：更改可能需要重启计算机才能生效。")
                    # 更新状态
                    status = "已关闭"
                else:
                    print("错误：无法关闭IPv6。请确保以管理员身份运行此脚本，并检查注册表权限。")
        else:
            print("无效输入，请输入1或2。")
            # 无效输入后直接重新循环，不进入退出等待
            continue
        
        # 等待用户选择是否退出或继续
        if not wait_for_exit():
            break  # 如果wait_for_exit返回False，则退出循环；如果返回True，则继续循环

if __name__ == "__main__":
    main()