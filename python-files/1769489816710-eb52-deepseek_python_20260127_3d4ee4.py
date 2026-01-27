# sector_data_generator.py
import sys

def calculate_sector_data(value):
    """
    根据输入数值计算16字节扇区数据
    
    参数:
        value: 浮点数，范围0.00-655.35，最多两位小数
    
    返回:
        32个字符的十六进制字符串（无空格）
    """
    # 输入验证
    try:
        value = float(value)
    except:
        raise ValueError("请输入有效的数字")
    
    if value < 0 or value > 655.35:
        raise ValueError("数值范围必须在0.00-655.35之间")
    
    # 转换为整型（×100）
    scaled_value = int(round(value * 100))
    
    # 验证是否超出16位范围
    if scaled_value > 0xFFFF:
        raise ValueError("缩放后的值超出16位范围")
    
    # 将数值转换为小端字节序（2字节）
    byte2 = scaled_value & 0xFF  # 低字节
    byte3 = (scaled_value >> 8) & 0xFF  # 高字节
    
    # 计算校验字节1（字节2+字节3的低8位）
    byte1 = (byte2 + byte3) & 0xFF
    
    # 计算校验字节5（字节1的取反）
    byte5 = (~byte1) & 0xFF
    
    # 初始化16字节数组
    bytes_list = [0] * 16
    
    # 设置已知字节
    bytes_list[1] = byte1  # 字节1
    bytes_list[2] = byte2  # 字节2
    bytes_list[3] = byte3  # 字节3
    bytes_list[5] = byte5  # 字节5
    
    # 计算字节0（字节1到字节14的异或值）
    xor_value = 0
    for i in range(1, 15):  # 字节1到字节14
        xor_value ^= bytes_list[i]
    bytes_list[0] = xor_value
    
    # 计算字节15（字节1到字节14的和取反的低8位）
    sum_value = 0
    for i in range(1, 15):  # 字节1到字节14
        sum_value += bytes_list[i]
    sum_low_byte = sum_value & 0xFF  # 取低8位
    bytes_list[15] = (~sum_low_byte) & 0xFF
    
    # 转换为十六进制字符串
    hex_str = ''.join(f'{b:02X}' for b in bytes_list)
    return hex_str

def main():
    """主函数：交互式输入输出"""
    print("扇区数据生成器")
    print("=" * 40)
    print("说明：")
    print("1. 输入数值范围：0.00 - 655.35")
    print("2. 自动计算校验码")
    print("=" * 40)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n请输入数值（输入'q'退出）: ").strip()
            
            if user_input.lower() == 'q':
                print("程序已退出")
                break
            
            # 计算数据
            hex_data = calculate_sector_data(user_input)
            value = float(user_input)
            
            # 显示结果
            print(f"\n【计算结果】")
            print(f"输入数值: {value:.2f}")
            print(f"16进制数据: {hex_data}")
            print(f"字节分布:")
            
            # 分4行显示，每行4个字节
            for i in range(0, 16, 4):
                row = []
                for j in range(4):
                    idx = i + j
                    byte_hex = hex_data[idx*2:idx*2+2]
                    row.append(f"字节{idx:2d}: {byte_hex}")
                print("  ".join(row))
            
            # 显示字节含义
            scaled_value = int(round(value * 100))
            print(f"\n【数据解析】")
            print(f"数值×100: {scaled_value} (0x{scaled_value:04X})")
            print(f"字节2-3: {hex_data[4:8]} (小端存储)")
            
            # 复制提示
            print(f"\n【使用提示】")
            print(f"可直接复制数据: {hex_data}")
            print("-" * 40)
            
        except ValueError as e:
            print(f"错误: {e}")
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()