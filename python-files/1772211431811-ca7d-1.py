import os
import soundfile as sf
import numpy as np

# 定义保留1位小数的函数及向量化版本
r1 = lambda x: round(x, 1)
r1_vec = np.vectorize(r1)

# 创建文件夹的函数
def new_folder(dir_):
    try:
        os.makedirs(dir_)
        print(f'文件夹创建成功: {dir_}')
    except FileExistsError:
        print(f'文件夹已存在: {dir_}')

# 计算几何均值
def geometrical_mean(a, b):
    return (a * b) ** 0.5

# 在列表/数组元素间插入计算值（修复索引错误）
def insert_num_between(lst, func):
    # 处理普通列表
    if isinstance(lst, list):
        new_lst = []
        for i in range(len(lst)):
            new_lst.append(lst[i])
            if i < len(lst) - 1:
                new_lst.append(func(lst[i], lst[i+1]))
        return new_lst
    # 处理numpy数组
    elif isinstance(lst, np.ndarray):
        new_arr = []
        for i in range(len(lst)):
            new_arr.append(lst[i])
            if i < len(lst) - 1:
                new_arr.append(func(lst[i], lst[i+1]))
        return np.array(new_arr)

# 迭代插入函数（修复返回值问题）
def iterization(func, n_iters, to_calculate, fixed_func):
    temp = to_calculate
    for i in range(n_iters):
        temp = func(temp, fixed_func)  # 直接更新temp，避免未定义data
    return temp

# 正弦波生成函数
def func(f, t):
    return 0.5 * np.sin(2 * np.pi * f * t)

# 生成单频率波形数据
def generate_wavesdata_from_list(freq, sample_rate, start, duration_time, func):
    t = np.linspace(start, start + duration_time, int(duration_time * sample_rate), endpoint=False)
    return func(freq, t)

# 保存音频文件（修复路径拼接）
def save_wave_files(dir_, freqs_r1, sample_rate, start, duration_time, func):
    # 确保路径末尾有分隔符
    dir_ = os.path.join(dir_, '')
    for freq_r1 in freqs_r1:
        wavedata = generate_wavesdata_from_list(freq_r1, sample_rate, start, duration_time, func)
        # 处理频率为小数的文件名（如22.5.flac）
        file_name = f"{freq_r1:.1f}".replace('.', '_') + '.flac'  # 替换小数点为下划线，避免系统问题
        dir_file_name = os.path.join(dir_, file_name)
        # 写入音频文件，PCM_24格式
        sf.write(dir_file_name, wavedata, sample_rate, subtype='PCM_24')
        print(f"{dir_file_name} 已写入")
    return dir_

def main():
    # 全局参数定义
    bands_15 = np.array([25,40,63,100,160,250,400,630,1000,1600,2500,4000,6300,10000,16000])
    bands_31 = np.array([20.0,25.0,31.5,40.0,50.0,63.0,80.0,100.0,125.0,160.0,200.0,
                            250.0,315.0,400.0,500.0,630.0,800.0,1000.0,1250.0,1600.0,2000.0,
                            2500.0,3150.0,4000.0,5000.0,6300.0,8000.0,10000.0,12500.0,16000.0,20000.0])
    sample_rate = 192000
    duration_time = 5
    start = 0
    n_depth = 3
    
    # 生成不同密度的频率列表
    freqs_list = [bands_15,bands_31] + [iterization(insert_num_between,i+1,bands_31,geometrical_mean) for i in range(n_depth)]
    freqs_r1_list = [r1_vec(freqs) for freqs in freqs_list]
    
    # 遍历每个频率列表，生成对应文件夹和音频文件
    for freqs_r1 in freqs_r1_list:
        folder_name = f"{freqs_r1.size}段频率正弦波"
        # 使用os.path.join拼接路径，兼容Windows/Linux
        dir_ = os.path.join('分段频率正弦波', folder_name)
        new_folder(dir_)
        save_wave_files(dir_, freqs_r1, sample_rate, start, duration_time, func)
        print(f'{freqs_r1.size}段频率正弦波已生成完毕。')

if __name__ == '__main__':
    # 安装依赖（如果未安装）
    try:
        import soundfile as sf
    except ImportError:
        print("正在安装soundfile依赖...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "soundfile"])
        import soundfile as sf
    
    main()
    input('全部分段频率正弦波文件已生成完毕，请按Enter键退出。')