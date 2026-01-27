# sector_data_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import struct

class SectorDataConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("扇区数据转换工具")
        self.root.geometry("800x400")
        self.root.resizable(True, True)
        
        # 设置Windows原生风格
        self.style = ttk.Style()
        self.style.theme_use('winnative')
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        
        # 左边：数值输入部分
        left_frame = ttk.LabelFrame(main_frame, text="数值转换", padding="10")
        left_frame.grid(row=0, column=0, padx=(0, 20), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 数值输入
        ttk.Label(left_frame, text="输入数值:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(left_frame, textvariable=self.value_var, width=20)
        self.value_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 数值显示
        ttk.Label(left_frame, text="转换结果:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.hex_result_text = tk.Text(left_frame, height=6, width=30)
        self.hex_result_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 右边：字节码输入部分
        right_frame = ttk.LabelFrame(main_frame, text="字节码转换", padding="10")
        right_frame.grid(row=0, column=2, padx=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 字节码输入
        ttk.Label(right_frame, text="输入字节码:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.hex_var = tk.StringVar()
        self.hex_entry = ttk.Entry(right_frame, textvariable=self.hex_var, width=30)
        self.hex_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 字节码显示
        ttk.Label(right_frame, text="转换结果:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.value_result_text = tk.Text(right_frame, height=6, width=20)
        self.value_result_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 中间：等号和按钮
        center_frame = ttk.Frame(main_frame)
        center_frame.grid(row=0, column=1, padx=20, sticky=(tk.N, tk.S))
        
        # 等号标签
        ttk.Label(center_frame, text="=", font=("Arial", 24)).pack(pady=(40, 20))
        
        # 转换按钮
        self.convert_btn = ttk.Button(center_frame, text="转换", command=self.convert_both_ways)
        self.convert_btn.pack(pady=10)
        
        # 清空按钮
        self.clear_btn = ttk.Button(center_frame, text="清空", command=self.clear_all)
        self.clear_btn.pack(pady=10)
        
        # 绑定事件
        self.value_entry.bind('<Return>', lambda e: self.convert_value_to_hex())
        self.hex_entry.bind('<Return>', lambda e: self.convert_hex_to_value())
        
    def calculate_sector_data(self, value):
        """根据输入数值计算16字节扇区数据"""
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
    
    def parse_sector_data(self, hex_str):
        """解析16字节扇区数据，提取数值并验证校验"""
        # 清理输入
        hex_str = hex_str.strip().replace(' ', '').replace('\n', '').replace('\t', '')
        
        if len(hex_str) != 32:
            raise ValueError("字节码长度必须为32个字符（16字节）")
        
        try:
            # 转换为字节列表
            bytes_list = []
            for i in range(0, 32, 2):
                byte_val = int(hex_str[i:i+2], 16)
                bytes_list.append(byte_val)
        except:
            raise ValueError("字节码必须为有效的十六进制字符串")
        
        # 提取数值（字节2-3，小端格式）
        scaled_value = bytes_list[2] + (bytes_list[3] << 8)
        value = scaled_value / 100.0
        
        # 验证校验字节1
        calc_byte1 = (bytes_list[2] + bytes_list[3]) & 0xFF
        if calc_byte1 != bytes_list[1]:
            raise ValueError(f"校验字节1错误：应为{calc_byte1:02X}，实际为{bytes_list[1]:02X}")
        
        # 验证校验字节5
        calc_byte5 = (~bytes_list[1]) & 0xFF
        if calc_byte5 != bytes_list[5]:
            raise ValueError(f"校验字节5错误：应为{calc_byte5:02X}，实际为{bytes_list[5]:02X}")
        
        # 验证校验字节0
        xor_value = 0
        for i in range(1, 15):  # 字节1到字节14
            xor_value ^= bytes_list[i]
        if xor_value != bytes_list[0]:
            raise ValueError(f"校验字节0错误：应为{xor_value:02X}，实际为{bytes_list[0]:02X}")
        
        # 验证校验字节15
        sum_value = 0
        for i in range(1, 15):  # 字节1到字节14
            sum_value += bytes_list[i]
        sum_low_byte = sum_value & 0xFF
        calc_byte15 = (~sum_low_byte) & 0xFF
        if calc_byte15 != bytes_list[15]:
            raise ValueError(f"校验字节15错误：应为{calc_byte15:02X}，实际为{bytes_list[15]:02X}")
        
        return value
    
    def convert_value_to_hex(self):
        """将数值转换为字节码"""
        try:
            value_str = self.value_var.get().strip()
            if not value_str:
                return
            
            hex_data = self.calculate_sector_data(value_str)
            value = float(value_str)
            
            # 显示结果
            self.hex_result_text.delete(1.0, tk.END)
            self.hex_result_text.insert(1.0, hex_data)
            
            # 添加格式化的字节分布
            self.hex_result_text.insert(tk.END, "\n\n字节分布:\n")
            for i in range(0, 16, 4):
                row = []
                for j in range(4):
                    idx = i + j
                    byte_hex = hex_data[idx*2:idx*2+2]
                    row.append(f"字节{idx:2d}: {byte_hex}")
                self.hex_result_text.insert(tk.END, "  ".join(row) + "\n")
            
        except ValueError as e:
            messagebox.showerror("转换错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {e}")
    
    def convert_hex_to_value(self):
        """将字节码转换为数值"""
        try:
            hex_str = self.hex_var.get().strip()
            if not hex_str:
                return
            
            value = self.parse_sector_data(hex_str)
            
            # 显示结果
            self.value_result_text.delete(1.0, tk.END)
            self.value_result_text.insert(1.0, f"{value:.2f}")
            
            # 添加解析信息
            self.value_result_text.insert(tk.END, f"\n\n解析信息:")
            self.value_result_text.insert(tk.END, f"\n原始值×100: {int(value * 100)}")
            self.value_result_text.insert(tk.END, f"\n十六进制: 0x{int(value * 100):04X}")
            
        except ValueError as e:
            messagebox.showerror("转换错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"发生未知错误: {e}")
    
    def convert_both_ways(self):
        """同时执行两个方向的转换"""
        self.convert_value_to_hex()
        self.convert_hex_to_value()
    
    def clear_all(self):
        """清空所有输入和输出"""
        self.value_var.set("")
        self.hex_var.set("")
        self.hex_result_text.delete(1.0, tk.END)
        self.value_result_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = SectorDataConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()