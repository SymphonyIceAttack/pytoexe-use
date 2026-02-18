import platform
import sys
import subprocess
import os

def get_cpu_info():
    """获取CPU型号"""
    try:
        if platform.system() == "Windows":
            # Windows: 使用 WMI
            import wmi
            w = wmi.WMI()
            for processor in w.Win32_Processor():
                return processor.Name.strip()
        elif platform.system() == "Linux":
            # Linux: 读取 /proc/cpuinfo
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
        elif platform.system() == "Darwin":
            # macOS: 使用 sysctl
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
    except Exception as e:
        return f"未知 (获取失败: {str(e)})"
    return "未知"

def check_vtx():
    """检查 VT-x/AMD-V (CPU 虚拟化)"""
    status = {
        "supported": False,
        "enabled_in_os": False,
        "details": ""
    }
    
    try:
        if platform.system() == "Windows":
            import wmi
            w = wmi.WMI()
            # 检查 CPU 是否支持
            for proc in w.Win32_Processor():
                # SecondLevelAddressTranslationExtensions, VirtualizationFirmwareEnabled
                if hasattr(proc, 'VirtualizationFirmwareEnabled'):
                    status["supported"] = True
                    if proc.VirtualizationFirmwareEnabled:
                        status["enabled_in_os"] = True
                        status["details"] = "BIOS/UEFI 中已启用"
                    else:
                        status["details"] = "CPU 支持，但未在 BIOS/UEFI 中启用"
            
            # 额外检查：是否被 Hyper-V 占用
            try:
                for comp in w.Win32_ComputerSystem():
                    if comp.HyperVisorPresent:
                        status["details"] += " (注意：检测到 Hyper-V 正在运行，这可能会拦截 VT-x)"
            except:
                pass

        elif platform.system() == "Linux":
            # 检查 CPU flags
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            if "vmx" in cpuinfo or "svm" in cpuinfo:
                status["supported"] = True
                # 检查 KVM 模块是否加载
                if os.path.exists("/dev/kvm"):
                    status["enabled_in_os"] = True
                    status["details"] = "KVM 模块已加载，虚拟化可用"
                else:
                    status["details"] = "CPU 支持，但 KVM 未加载 (或 BIOS 未开启)"
        
        elif platform.system() == "Darwin":
            # macOS: 检查 hv_support
            res = subprocess.check_output(["sysctl", "-n", "kern.hv_support"]).decode().strip()
            if res == "1":
                status["supported"] = True
                status["enabled_in_os"] = True
                status["details"] = "Apple Hypervisor 框架可用"
            else:
                status["details"] = "不支持或未启用"

    except Exception as e:
        status["details"] = f"检测出错: {str(e)}"
        
    return status

def check_vtd():
    """检查 VT-d/AMD IOMMU (I/O 虚拟化)"""
    status = {
        "supported": False,
        "enabled": False,
        "details": ""
    }

    try:
        if platform.system() == "Windows":
            # Windows 检测 VT-d 比较复杂，通常检查是否有 DMA 重映射或通过 WMI
            # 这里提供一个基础检查：查看设备管理器中是否有 PCI 根复合体相关的中断重映射
            # 注意：这需要管理员权限，且并不完全准确，仅供参考
            status["details"] = "Windows 下建议直接查看 BIOS/UEFI 设置，或检查 '设备管理器 -> 系统设备' 中是否有 'Intel VT-d' 或 'DMA 重新映射' 相关设备。"
            
            # 尝试通过注册表粗略判断 (不一定总是存在)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
                # 这只是一个示例键，实际可能不存在，主要依赖上面的文字提示
                status["details"] += " (建议在 BIOS 中确认)"
            except:
                pass

        elif platform.system() == "Linux":
            # 检查内核启动参数和 IOMMU 组
            has_iommu = False
            if os.path.exists("/sys/class/iommu/"):
                dirs = os.listdir("/sys/class/iommu/")
                if dirs:
                    has_iommu = True
            
            # 检查 dmesg (需要 root 可能最好，这里尝试读取)
            dmesg_good = False
            try:
                # 这是一个粗略检查，可能需要 sudo dmesg
                res = subprocess.check_output(["dmesg"], stderr=subprocess.STDOUT).decode()
                if "IOMMU enabled" in res or "DMAR: IOMMU enabled" in res:
                    dmesg_good = True
            except:
                pass

            if has_iommu or dmesg_good:
                status["supported"] = True
                status["enabled"] = True
                status["details"] = "检测到 IOMMU (VT-d/AMD-Vi) 已启用"
            else:
                # 检查 CPU 品牌看是否有硬件支持的可能
                cpu_info = get_cpu_info()
                if "Intel" in cpu_info or "AMD" in cpu_info:
                     status["details"] = "未检测到活动的 IOMMU。请确保 BIOS 已开启，且内核参数添加了 intel_iommu=on 或 amd_iommu=on"
                else:
                     status["details"] = "未检测到 IOMMU"

        elif platform.system() == "Darwin":
            status["details"] = "macOS 对 VT-d 的暴露有限，通常用于内部驱动，用户无需手动配置。"

    except Exception as e:
        status["details"] = f"检测出错: {str(e)}"

    return status

def main():
    print("="*50)
    print("       CPU 与虚拟化检测工具")
    print("="*50)
    
    # 1. CPU 型号
    cpu_model = get_cpu_info()
    print(f"[1/3] CPU 型号:\n  -> {cpu_model}\n")
    
    # 2. VT-x
    print(f"[2/3] CPU 虚拟化 (VT-x/AMD-V):")
    vtx_stat = check_vtx()
    if vtx_stat["supported"]:
        if vtx_stat["enabled_in_os"]:
            print(f"  -> [✅] 状态: 已启用")
        else:
            print(f"  -> [⚠️]  状态: 支持，但未启用 (请检查 BIOS)")
    else:
        print(f"  -> [❌] 状态: 不支持")
    print(f"  -> 详情: {vtx_stat['details']}\n")

    # 3. VT-d
    print(f"[3/3] I/O 虚拟化 (VT-d/AMD IOMMU):")
    vtd_stat = check_vtd()
    if vtd_stat["enabled"]:
        print(f"  -> [✅] 状态: 已启用")
    else:
        print(f"  -> [⚠️]  状态: 未检测到 (需检查 BIOS/内核)")
    print(f"  -> 详情: {vtd_stat['details']}\n")

    print("="*50)
    print("注: 如检测结果异常，请务必重启电脑进入 BIOS/UEFI 界面确认设置。")
    print("="*50)

if __name__ == "__main__":
    main()