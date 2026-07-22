import struct
import numpy as np

SERVO_NUM = 16  # 人形模式固定16个舵机

def parse_hiwonder_rob_full(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # 读取总帧数（前2字节）
    frame_count = struct.unpack('<H', data[:2])[0]
    print(f"检测到总帧数: {frame_count}")
    
    offset = 2  # 跳过头部
    frames = []  # 每行存储 [时间, ID1, ID2, ..., ID16]
    
    for _ in range(frame_count):
        # 1. 读取运行时间 (2字节，小端)
        run_time = struct.unpack('<H', data[offset:offset+2])[0]
        offset += 2
        
        # 2. 读取16个舵机角度 (16 × 2字节)
        angles = []
        for _ in range(SERVO_NUM):
            angle = struct.unpack('<H', data[offset:offset+2])[0]
            angles.append(angle)
            offset += 2
        
        # 组合成一行：[时间, 角度1, 角度2, ...]
        frames.append([run_time] + angles)
    
    # 转为二维numpy数组，形状为 (帧数, 17)
    return np.array(frames)

# ========== 使用示例 ==========
if __name__ == "__main__":
    # 替换成你的 .rob 文件路径
    result = parse_hiwonder_rob_full("C:/你的动作文件.rob")
    
    print(f"\n生成的二维数组形状: {result.shape}")  # 输出 (帧数, 17)
    print("\n第一行数据（时间 + ID1~ID16）:")
    print(result[0])
    
    # 保存为CSV，用Excel打开后完全复现你的截图布局
    header = "Index,Time(ms)," + ",".join([f"ID:{i}" for i in range(1, 17)])
    # 加上行号（Index列），从0开始
    output_with_index = np.column_stack((np.arange(len(result)), result))
    np.savetxt("人形动作_完整数据.csv", output_with_index, 
               delimiter=",", header=header, comments='', fmt='%d')
    print("\n✅ 已保存为 '人形动作_完整数据.csv'，用Excel打开即可看到完整表格。")