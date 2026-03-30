import os
import re
import telnetlib
import time
from pathlib import Path

def clean_filename(name):
    """清理文件名中的特殊字符"""
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

def upload_setting(ip):
    """连接设备并上传setting.txt"""
    try:
        # 创建 Telnet 连接
        tn = telnetlib.Telnet(ip, 23, timeout=10)
        
        # 登录过程
        tn.read_until(b'login:', timeout=5)
        tn.write(b'root\n')
        tn.read_until(b'Password:', timeout=5)
        tn.write(b'NRuapc2013++\n')
        tn.read_until(b'#', timeout=5)
        
        # 执行上传命令
        tn.write(b'upload setting.txt\n')
        time.sleep(5)  # 等待文件传输完成
        
        # 读取并保存响应
        response = tn.read_very_eager().decode('utf-8')
        return response
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'tn' in locals():
            tn.close()

def main():
    # 遍历所有.apjp文件
    for apjp_file in Path('.').rglob('*.apjp'):
        try:
            # 读取文件内容获取IP
            with open(apjp_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取IP地址
            ip_match = re.search(r'curip=\"([^\"]+)\"', content)
            if not ip_match:
                continue
                
            ip = ip_match.group(1)
            device_name = clean_filename(apjp_file.stem)
            
            # 连接设备并获取响应
            print(f"[连接] {device_name} ({ip})")
            response = upload_setting(ip)
            
            # 保存响应到文件
            output_file = apjp_file.parent / f"{device_name}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response)
                
            print(f"  -> 成功保存至: {output_file}")
        except Exception as e:
            print(f"  -> 失败: {str(e)}")
    
    print("任务完成")

if __name__ == "__main__":
    main()