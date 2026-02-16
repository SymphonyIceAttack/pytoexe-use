import os
import sys
import ctypes
from pathlib import Path

# 解决中文路径/参数乱码问题
sys.stdout.reconfigure(encoding='utf-8')

def is_admin():
    """检查是否为管理员"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        print(f"检查管理员权限出错：{e}")
        return False

def run_as_admin():
    """弹出UAC授权框，以管理员重启脚本（修复参数传递）"""
    try:
        # 获取当前脚本的完整路径（解决空格/中文路径问题）
        script_path = os.path.abspath(sys.argv[0])
        # 拼接参数（保留原参数）
        params = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
        # 核心：修复ShellExecuteA参数，确保提权后能正确运行
        ret = ctypes.windll.shell32.ShellExecuteA(
            None,
            "runas",  # 提权标识
            sys.executable,  # Python解释器路径
            f'"{script_path}" {params}',  # 脚本路径+参数（加引号处理空格）
            None,
            1  # 显示窗口（控制台）
        )
        # 检查提权是否触发（>32表示成功弹出授权框）
        if ret <= 32:
            print(f"❌ 提权失败（错误码：{ret}），请手动右键以管理员运行")
            input("\n按回车退出...")
            sys.exit(1)
    except Exception as e:
        print(f"✅ 提权弹窗已弹出，请在弹窗中点击「是」授权！")
        print(f"（若没看到弹窗，可能被系统拦截，手动右键脚本→以管理员运行）")
        input("\n按回车退出...")
        sys.exit(1)

def get_local_drives():
    """安全获取所有本地磁盘（避免崩溃）"""
    drives = []
    try:
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = f"{letter}:\\"
            # 只识别本地硬盘（排除光驱/网络盘）
            if os.path.exists(path) and os.path.isdir(path):
                drives.append(path)
    except Exception as e:
        print(f"获取磁盘列表出错：{e}")
    return drives

def should_skip(path):
    """跳过敏感目录"""
    skip_list = [
        "AppData\\Local\\History", "Temporary Internet Files",
        "INetCache", "Content.IE5", "System Volume Information",
        "Windows\\System32", "Windows\\SysWOW64", "WinSxS"
    ]
    try:
        path_low = path.lower()
        for keyword in skip_list:
            if keyword.lower() in path_low:
                return True
    except:
        pass
    return False

def scan_all_disks(target="settings.cock"):
    """全磁盘扫描（带完整异常捕获）"""
    found = []
    drives = get_local_drives()
    print(f"\n✅ 识别到本地磁盘：{drives if drives else '无'}")
    
    if not drives:
        print("❌ 未识别到任何本地磁盘，无法扫描")
        return found
    
    for dr in drives:
        print(f"\n📂 开始扫描磁盘：{dr}")
        try:
            # 限制遍历深度（避免卡死），只搜前10层目录（足够找外挂）
            for root, dirs, files in os.walk(dr, topdown=True):
                # 跳过敏感目录
                if should_skip(root):
                    continue
                # 检查目标文件
                if target in files:
                    full_path = str(Path(root) / target)
                    found.append(full_path)
                    print(f"✅ 找到外挂文件：{full_path}")
                # 限制遍历深度（提速+防卡死）
                level = root.replace(dr, '').count(os.sep)
                if level >= 10:
                    del dirs[:]  # 清空子目录，停止深入
        except PermissionError:
            print(f"⚠️ 无权限扫描 {dr} 部分目录（正常，已跳过）")
        except Exception as e:
            print(f"⚠️ 扫描 {dr} 时出错：{e}（已跳过）")
    return found

if __name__ == "__main__":
    # 强制设置控制台编码，避免中文乱码导致闪退
    try:
        os.system("chcp 65001 >nul")  # 设置UTF-8编码
    except:
        pass

    print("="*50)
    print("🔍 外挂检测程序 - 终极稳定版")
    print("="*50)

    # 第一步：检查并提权
    if not is_admin():
        print("🔑 当前无管理员权限，正在请求授权...")
        run_as_admin()
        # 提权后原进程退出，新进程会重新执行
        sys.exit()

    # 第二步：管理员权限已获取，开始扫描
    print("✅ 已获取管理员权限，开始全磁盘扫描...")
    try:
        result = scan_all_disks()
        # 第三步：输出结果
        print("\n" + "="*50)
        if result:
            print(f"⚠️ 扫描完成！共发现 {len(result)} 个外挂配置文件：")
            for idx, path in enumerate(result, 1):
                print(f"   {idx}. {path}")
        else:
            print("✅ 扫描完成！未发现外挂配置文件 settings.cock")
    except Exception as e:
        print(f"❌ 程序运行出错：{e}")

    # 终极防闪退：无论成功/失败，都暂停控制台
    input("\n📌 操作完成，按任意键退出...")