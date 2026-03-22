import sys

def bin_to_bat():
    # 获取当前目录下的input.bin，输出output.bat
    input_file = "input.bin"
    output_file = "output.bat"
    
    try:
        # 1. 读取BIN文件
        with open(input_file, 'rb') as file:
            content = file.read()
        
        if not content:
            print("错误：input.bin 文件为空！")
            input("\n按回车键退出...")
            return
        
        # 2. 解码（兼容常见编码，失败则容错）
        encodings = ['utf-8', 'gbk', 'gb2312', 'ansi', 'latin-1']
        bat_content = None
        for enc in encodings:
            try:
                bat_content = content.decode(enc)
                print(f"使用编码 {enc} 解码成功！")
                break
            except UnicodeDecodeError:
                continue
        
        # 终极容错：忽略无法解码的字符
        if bat_content is None:
            bat_content = content.decode('utf-8', errors='replace')
            print("警告：部分字符无法解码，已替换为占位符（可能有乱码）")
        
        # 3. 写入BAT文件
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(bat_content)
        
        print(f"✅ 转换成功！已生成 {output_file}")
    
    except FileNotFoundError:
        print(f"错误：未找到 input.bin 文件，请确保文件在EXE同目录下！")
    except PermissionError:
        print(f"错误：无权限读写文件，请以管理员身份运行！")
    except Exception as e:
        print(f"转换失败：{str(e)}")
    
    # 防止EXE运行后立即关闭
    input("\n按回车键退出...")

if __name__ == "__main__":
    bin_to_bat()