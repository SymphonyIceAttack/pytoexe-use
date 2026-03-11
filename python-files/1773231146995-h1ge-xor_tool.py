import os
import struct

def xor_cipher():
    print("=== 4字节分组异或加密/解密工具 ===")
    
    # 1. 输入文件路径
    file_path = input("请输入源文件路径: ").strip('"').strip("'")
    if not os.path.exists(file_path):
        print("错误：找不到文件。")
        return

    # 2. 输入8位十六进制密钥 (例如: ABCDE123)
    key_hex = input("请输入8位十六进制密钥 (如 1A2B3C4D): ").strip()
    try:
        if len(key_hex) != 8:
            raise ValueError
        key_bytes = bytes.fromhex(key_hex)
    except ValueError:
        print("错误：请输入有效的8位十六进制字符串。")
        return

    # 3. 选择输出方式
    print("\n1. 覆盖原文件\n2. 另存为新文件")
    choice = input("请选择输出方式 (1/2): ")
    
    if choice == '1':
        save_path = file_path
    else:
        save_path = input("请输入保存路径: ").strip('"').strip("'")

    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        # 4. 执行每4字节异或
        # 将文件数据转为bytearray以便修改
        result = bytearray()
        key_len = len(key_bytes) # 始终为4
        
        for i in range(0, len(data), key_len):
            chunk = data[i:i+key_len]
            # 对当前块的每个字节与密钥对应字节异或
            for j in range(len(chunk)):
                result.append(chunk[j] ^ key_bytes[j])

        # 5. 写入文件
        with open(save_path, 'wb') as f:
            f.write(result)
            
        print(f"\n成功！文件已保存至: {save_path}")
    except Exception as e:
        print(f"发生错误: {e}")

    input("\n按回车键退出...")

if __name__ == "__main__":
    xor_cipher()
