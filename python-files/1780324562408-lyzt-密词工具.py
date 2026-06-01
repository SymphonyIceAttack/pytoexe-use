import os
import re

class LingiaCipher:
    def __init__(self):
        self.mapping = {}  # 数字到字符的映射
        self.reverse_mapping = {}  # 字符到数字的映射
        self.version = None
    
    def load_mapping_from_file(self, file_path):
        """
        从MD文件加载映射表
        """
        self.mapping = {}
        self.reverse_mapping = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取版本信息
            file_name = os.path.basename(file_path)
            if 'V1' in file_name:
                self.version = 'V1'
            elif 'V2C' in file_name:
                self.version = 'V2C'
            elif 'V2X' in file_name:
                self.version = 'V2X'
            elif 'V3C' in file_name:
                self.version = 'V3C'
            elif 'V4X' in file_name:
                self.version = 'V4X'
            else:
                self.version = 'Unknown'
            
            # 解析映射表：匹配格式如 "1-A" 或 "## 01-a"
            # 支持多种格式：数字-字符 或 ## 数字-字符
            patterns = [
                r'(\d+)-(\S+)',  # 匹配 "数字-字符"
                r'##\s*(\d+)-(\S+)',  # 匹配 "## 数字-字符"
                r'###\s*(\d+)-(\S+)',  # 匹配 "### 数字-字符"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for num_str, char in matches:
                    try:
                        num = int(num_str)
                        # 清理字符（去除可能的空格或特殊字符）
                        char = char.strip()
                        if char:
                            self.mapping[num] = char
                            self.reverse_mapping[char] = num
                    except ValueError:
                        continue
            
            print(f"成功加载映射表 {file_name}")
            print(f"版本: {self.version}")
            print(f"映射条目数: {len(self.mapping)}")
            
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 不存在")
            return False
        except Exception as e:
            print(f"加载文件时发生错误: {e}")
            return False
        
        return True
    
    def encrypt(self, plaintext):
        """
        加密：明文 -> 密文（数字序列）
        """
        if not self.mapping:
            print("错误：请先加载映射表")
            return None
        
        ciphertext = []
        for char in plaintext:
            # 尝试找到字符对应的数字
            if char in self.reverse_mapping:
                ciphertext.append(str(self.reverse_mapping[char]))
            else:
                # 如果字符不在映射表中，使用Unicode码点
                ciphertext.append(str(ord(char)))
        
        return '-'.join(ciphertext)
    
    def decrypt(self, ciphertext):
        """
        解密：密文（数字序列）-> 明文
        """
        if not self.mapping:
            print("错误：请先加载映射表")
            return None
        
        plaintext = []
        numbers = ciphertext.split('-')
        
        for num_str in numbers:
            try:
                num = int(num_str)
                if num in self.mapping:
                    plaintext.append(self.mapping[num])
                else:
                    # 如果数字不在映射表中，尝试转换为Unicode字符
                    try:
                        plaintext.append(chr(num))
                    except ValueError:
                        plaintext.append(f'[{num}]')
            except ValueError:
                plaintext.append(num_str)
        
        return ''.join(plaintext)

def upload_file():
    """
    文件上传功能示例
    """
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    file_path = filedialog.askopenfilename(
        title="选择映射表文件",
        filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")]
    )
    
    if file_path:
        print(f"选择的文件: {file_path}")
        return file_path
    else:
        print("未选择文件")
        return None

def main():
    cipher = LingiaCipher()
    
    while True:
        print("\n=== Lingia 密词加解密工具 ===")
        # 显示当前已加载的版本信息
        if cipher.version:
            print(f"当前版本: {cipher.version} (已加载 {len(cipher.mapping)} 个映射)")
        else:
            print("当前版本: 未加载")
        print("1. 加载/更换映射表")
        print("2. 加密")
        print("3. 解密")
        print("4. 退出")
        
        choice = input("请选择操作 (1-4): ")
        
        if choice == '1':
            # 如果已加载版本，提示用户将更换
            if cipher.version:
                print(f"当前已加载版本: {cipher.version}，将进行更换...")
            
            # 方式1：手动输入路径
            # file_path = input("请输入映射表文件路径: ")
            
            # 方式2：文件选择对话框
            file_path = upload_file()
            
            if file_path:
                cipher.load_mapping_from_file(file_path)
                if cipher.version:
                    print(f"版本更换成功！当前版本: {cipher.version}")
        
        elif choice == '2':
            if not cipher.mapping:
                print("请先加载映射表！")
                continue
            plaintext = input("请输入明文: ")
            result = cipher.encrypt(plaintext)
            print(f"加密结果: {result}")
        
        elif choice == '3':
            if not cipher.mapping:
                print("请先加载映射表！")
                continue
            ciphertext = input("请输入密文（数字用'-'分隔）: ")
            result = cipher.decrypt(ciphertext)
            print(f"解密结果: {result}")
        
        elif choice == '4':
            print("退出程序")
            break
        
        else:
            print("无效选择，请输入1-4")

if __name__ == "__main__":
    main()