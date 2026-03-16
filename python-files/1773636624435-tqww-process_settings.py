import psutil
import os
import sys

def set_process_priority(process_names, priority_level):
    """
    设置指定进程的优先级
    
    Args:
        process_names (list): 进程名称列表
        priority_level (int): 优先级级别，psutil提供的常量
    """
    success_count = 0
    total_count = 0
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] in process_names:
                total_count += 1
                # 设置进程优先级
                proc.nice(priority_level)
                print(f"成功将进程 {proc.info['name']} (PID: {proc.info['pid']}) 优先级设置为低")
                success_count += 1
        except psutil.NoSuchProcess:
            print(f"进程 {proc.info['name']} (PID: {proc.info['pid']}) 已结束")
        except psutil.AccessDenied:
            print(f"权限不足，无法修改进程 {proc.info['name']} (PID: {proc.info['pid']}) 的优先级")
        except Exception as e:
            print(f"修改进程 {proc.info['name']} (PID: {proc.info['pid']}) 优先级时出错: {str(e)}")
    
    return success_count, total_count

def set_process_cpu_affinity(process_name, exclude_cpu=0):
    """
    设置进程的CPU相关性，排除指定CPU
    
    Args:
        process_name (str): 进程名称
        exclude_cpu (int): 要排除的CPU编号
    """
    success_count = 0
    total_count = 0
    
    # 获取所有CPU核心
    cpu_count = os.cpu_count()
    # 生成CPU掩码（排除指定CPU）
    cpu_list = [cpu for cpu in range(cpu_count) if cpu != exclude_cpu]
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == process_name:
                total_count += 1
                # 设置CPU相关性
                proc.cpu_affinity(cpu_list)
                print(f"成功将进程 {proc.info['name']} (PID: {proc.info['pid']}) "
                      f"的CPU相关性设置为: {cpu_list} (已取消CPU {exclude_cpu})")
                success_count += 1
        except psutil.NoSuchProcess:
            print(f"进程 {proc.info['name']} (PID: {proc.info['pid']}) 已结束")
        except psutil.AccessDenied:
            print(f"权限不足，无法修改进程 {proc.info['name']} (PID: {proc.info['pid']}) 的CPU相关性")
        except Exception as e:
            print(f"修改进程 {proc.info['name']} (PID: {proc.info['pid']}) CPU相关性时出错: {str(e)}")
    
    return success_count, total_count

def main():
    # 以管理员身份运行（Windows）
    if sys.platform == 'win32' and not os.environ.get('ADMIN', False):
        try:
            # 重新以管理员身份启动
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, __file__, None, 1
            )
            os.environ['ADMIN'] = 'True'
            return
        except Exception as e:
            print("需要管理员权限才能修改进程优先级和CPU相关性！")
            print(f"错误信息: {e}")
            input("按回车键退出...")
            return
    
    print("=== 进程优先级和CPU相关性设置工具 ===\n")
    
    # 1. 设置SGuard64.exe和SGuardSvc64.exe的优先级为低
    print("1. 正在设置进程优先级...")
    priority_processes = ["SGuard64.exe", "SGuardSvc64.exe"]
    # psutil.IDLE_PRIORITY_CLASS 对应Windows的"低"优先级
    success_prio, total_prio = set_process_priority(priority_processes, psutil.IDLE_PRIORITY_CLASS)
    
    print(f"\n优先级设置完成: 共找到 {total_prio} 个目标进程，成功设置 {success_prio} 个\n")
    
    # 2. 设置DeltaForceClient-Win64-Shipping.exe的CPU相关性（取消CPU 0）
    print("2. 正在设置CPU相关性...")
    affinity_process = "DeltaForceClient-Win64-Shipping.exe"
    success_aff, total_aff = set_process_cpu_affinity(affinity_process, exclude_cpu=0)
    
    print(f"\nCPU相关性设置完成: 共找到 {total_aff} 个目标进程，成功设置 {success_aff} 个\n")
    
    # 最终统计
    print("=== 操作完成 ===")
    print(f"优先级设置: {success_prio}/{total_prio} 成功")
    print(f"CPU相关性设置: {success_aff}/{total_aff} 成功")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        input("按回车键退出...")
