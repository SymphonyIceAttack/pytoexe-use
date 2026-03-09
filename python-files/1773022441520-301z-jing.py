import requests
import pandas as pd
import time

def test_env():
    baidu = 'https://www.baidu.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    answer_code = requests.get(url=baidu, headers=headers).status_code
    if answer_code == 200:
        print('百度访问测试成功')
    else:
        print(f'百度访问失败，状态码：{answer_code}')

def get_location(address, api_key='your_key_here'):
    """
    根据地址获取经纬度
    注意：需要替换为你的高德地图API key
    """
    base_url = 'https://restapi.amap.com/v3/geocode/geo'
    
    params = {
        'key': api_key,  # 需要替换为你的API key
        'address': address,
        'output': 'JSON'
    }
    
    try:
        answer = requests.get(base_url, params=params)
        data = answer.json()
        
        if data['status'] == '1' and data['geocodes']:
            location = data['geocodes'][0]['location']
            return location
        else:
            print(f"地址 '{address}' 获取失败: {data.get('info', '未知错误')}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def process_excel(input_file, output_file, address_column='地址', api_key='your_key_here'):
    """
    处理Excel文件，获取地址的经纬度
    
    Args:
        input_file: 输入的Excel文件路径
        output_file: 输出的Excel文件路径
        address_column: 地址所在的列名，默认为'地址'
        api_key: 高德地图API key
    """
    # 读取Excel文件
    try:
        df = pd.read_excel(input_file)
        print(f"成功读取Excel文件，共{len(df)}行")
        print(f"列名: {list(df.columns)}")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return
    
    # 检查地址列是否存在
    if address_column not in df.columns:
        print(f"错误：找不到列 '{address_column}'")
        print(f"可用的列名: {list(df.columns)}")
        return
    
    # 创建location列（如果不存在）
    location_column = 'location'
    if location_column not in df.columns:
        df[location_column] = ''
    
    # 遍历每一行获取经纬度
    for index, row in df.iterrows():
        address = row[address_column]
        
        # 跳过空地址
        if pd.isna(address) or str(address).strip() == '':
            print(f"第{index+2}行：地址为空，跳过")
            continue
        
        print(f"正在处理第{index+2}行：{address}")
        # if index>10:
        #     continue
        # 获取经纬度
        location = get_location(address, api_key)
        
        if location:
            df.at[index, location_column] = location
            print(f"  获取成功: {location}")
        else:
            df.at[index, location_column] = '获取失败'
        
        # 添加延时，避免请求过快
        time.sleep(0.5)
    
    # 保存结果到新的Excel文件
    try:
        df.to_excel(output_file, index=False)
        print(f"\n处理完成！结果已保存到: {output_file}")
    except Exception as e:
        print(f"保存Excel文件失败: {e}")

def main():
    # 测试网络环境
    test_env()
    
    # 配置文件路径
    input_file = './地址数据.xlsx'  # 输入的Excel文件
    output_file = './地址数据_带经纬度.xlsx'  # 输出的Excel文件
    with open('./config.txt') as f:
        api_key = f.read().strip()

    #api_key = '40a3475115c7cd0ed0a66e44c1a21a9f'  # 请替换为你的高德地图API key
    
    # 处理Excel文件
    process_excel(input_file, output_file, address_column='集团名称', api_key=api_key)

if __name__ == "__main__":
    main()