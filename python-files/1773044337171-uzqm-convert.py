#!/usr/bin/env python
# -*- coding: utf-8 -*-

import binascii
import os
import sys

def convert_binary_to_hex(input_file, output_file=None):
    """
    将二进制文件转换为十六进制文本格式（每两个字符一组，空格分隔）
    """
    try:
        # 如果未指定输出文件，自动生成输出文件名
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_hex.txt"
        
        # 读取二进制文件
        print(f"正在读取文件: {input_file}")
        with open(input_file, 'rb') as f:
            binary_data = f.read()
        
        print(f"文件大小: {len(binary_data)} 字节")
        
        # 转换为十六进制文本
        print("正在转换...")
        hex_str = binascii.hexlify(binary_data).decode('utf-8')
        
        # 每两个字符一组，空格分隔
        formatted_hex = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        
        # 保存到新文件
        print(f"正在保存到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_hex)
        
        print(f"转换完成！")
        print(f"输出文件: {output_file}")
        return True
        
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def main():
    print("=" * 50)
    print("二进制转十六进制转换器")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        convert_binary_to_hex(input_file, output_file)
    else:
        # 交互模式
        input_file = input("请输入要转换的文件名: ").strip()
        if not input_file:
            print("未指定文件，退出")
            return
        
        if not os.path.exists(input_file):
            print(f"文件不存在: {input_file}")
            return
        
        output_file = input("请输入输出文件名（直接回车自动生成）: ").strip()
        if not output_file:
            output_file = None
        
        convert_binary_to_hex(input_file, output_file)
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
