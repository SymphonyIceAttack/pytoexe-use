import os
import re
import telnetlib
import time
from pathlib import Path

def clean_filename(name):
    """清理文件名中的特殊字符"""
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

def get_setting_via_cat(ip):
    """连接设备并抓取 cat setting.txt 的输出"""
    try:
        # 1. 建立连接
        tn = telnetlib.Telnet(ip, 23, timeout=10)
        
        # 2. 自动登录
        tn.read_until(b'login:', timeout=5)
        tn.write(b'root\n')
        tn.read_until(b'Password:', timeout=5)
        tn.write(b'NRuapc2013++\n')
        tn.read_until(b'#', timeout=5) # 等待提示符
        
        # 3. 关键步骤：发送 cat 命令
        # 注意：这里不再等待设备回应，直接发命令
        tn.write(b'cat setting.txt\n')
        
        # 4. 等待数据传输
        # 因为 cat 命令会直接把内容打印出来，我们需要等几秒让数据跑完
        print("   -> 正在接收数据流...")
        time.sleep(5) 
        
        # 5. 读取所有输出
        # read_very_eager() 会读取缓冲区里所有的东西，正好对应 cat 吐出来的文件内容
        output_data = tn.read_very_eager().decode('utf-8', errors='ignore')
        
        # 6. 数据清洗（可选）
        # 有时候开头会残留命令本身 "cat setting.txt"，结尾会有提示符 "# "
        # 这里简单处理：如果数据量很大，直接保存即可；如果怕有杂质，可以手动裁剪
        # 简单粗暴法：直接保存，因为这就是文件内容
        
        return output_data
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'tn' in locals():
            try:
                tn.write(b'exit\n') # 尝试退出
            except:
                pass
            tn.close()

def main():
    print("开始扫描并抓取配置...")
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
            
            # 执行抓取
            print(f"[连接] {device_name} ({ip})")
            file_content = get_setting_via_cat(ip)
            
            # 如果内容看起来像错误信息（以 Error 开头），则不保存
            if file_content.startswith("Error"):
                print(f"  -> 失败: {file_content}")
                continue

            # 保存文件
            output_file = apjp_file.parent / f"{device_name}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(file_content)
                
            print(f"  -> 成功! 已保存: {output_file}")
            
        except Exception as e:
            print(f"  -> 异常: {str(e)}")
    
    print("\n所有任务处理完毕。")

if __name__ == "__main__":
    main()