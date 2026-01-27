#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版JSON数据转Excel脚本
处理非法字符和编码问题
"""

import json
import pandas as pd
import sys
import os
import argparse
from datetime import datetime
import time
import re

def clean_string(value):
    """
    清理字符串中的非法字符
    """
    if not isinstance(value, str):
        return value
    
    # 移除控制字符和非法Excel字符
    # 保留中文字符、字母、数字、标点符号等
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # 移除其他可能的问题字符
    cleaned = cleaned.replace('\ufeff', '')  # BOM标记
    
    return cleaned

def clean_data(data):
    """
    递归清理数据中的非法字符
    """
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, str):
        return clean_string(data)
    else:
        return data

def read_json_file(file_path, max_lines=None):
    """
    读取JSON文件，支持大文件处理
    """
    try:
        print(f"正在读取文件: {file_path}")
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        print(f"文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
        
        start_time = time.time()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        end_time = time.time()
        print(f"读取完成，耗时: {end_time - start_time:.2f} 秒")
        
        return data
        
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 不存在")
        return None
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {e}")
        print("尝试使用不同的编码...")
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                data = json.load(f)
            print("使用GBK编码成功读取")
            return data
        except:
            print("GBK编码也失败")
            return None
    except MemoryError:
        print(f"错误：内存不足，文件太大")
        print("建议：尝试使用流式处理或增加系统内存")
        return None
    except Exception as e:
        print(f"错误：读取文件时发生错误 - {e}")
        return None

def convert_json_to_excel(json_data, output_file, chunk_size=None):
    """
    将JSON数据转换为Excel，支持大文件分块处理
    """
    try:
        # 检查JSON结构
        if not isinstance(json_data, dict):
            print("错误：JSON数据不是字典格式")
            return False
        
        # 检查是否有rows字段
        if 'rows' not in json_data:
            print("错误：JSON数据中没有'rows'字段")
            return False
        
        rows = json_data['rows']
        
        if not isinstance(rows, list):
            print("错误：'rows'字段不是列表格式")
            return False
        
        if len(rows) == 0:
            print("警告：'rows'列表为空")
            return False
        
        # 添加统计信息
        total_records = json_data.get('total', len(rows))
        records_count = json_data.get('records', len(rows))
        
        print(f"\n数据统计:")
        print(f"  - total字段: {total_records}")
        print(f"  - records字段: {records_count}")
        print(f"  - 实际行数: {len(rows):,}")
        
        # 显示数据结构信息
        if len(rows) > 0:
            sample_row = rows[0]
            print(f"  - 每行字段数: {len(sample_row)}")
        
        # 清理数据中的非法字符
        print(f"\n正在清理数据中的非法字符...")
        start_time = time.time()
        
        cleaned_rows = clean_data(rows)
        
        end_time = time.time()
        print(f"数据清理完成，耗时: {end_time - start_time:.2f} 秒")
        
        # 将数据转换为DataFrame
        print(f"正在转换为DataFrame...")
        start_time = time.time()
        
        df = pd.DataFrame(cleaned_rows)
        
        end_time = time.time()
        print(f"DataFrame转换完成，耗时: {end_time - start_time:.2f} 秒")
        
        # 保存为Excel文件
        print(f"正在保存到Excel文件: {output_file}")
        start_time = time.time()
        
        # 使用openpyxl引擎，设置更多选项
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        end_time = time.time()
        print(f"Excel文件保存完成，耗时: {end_time - start_time:.2f} 秒")
        
        print(f"\n成功将数据保存到: {output_file}")
        print(f"生成列数: {len(df.columns)}")
        print(f"生成行数: {len(df):,}")
        
        # 显示列名
        print("\n生成的Excel列名:")
        columns = list(df.columns)
        for i in range(0, len(columns), 5):
            chunk = columns[i:i+5]
            line = "  ".join([f"{j+1:2d}. {col}" for j, col in enumerate(chunk, i)])
            print(f"  {line}")
        
        return True
        
    except MemoryError:
        print(f"错误：内存不足，数据太大")
        print("建议：")
        print("  1. 增加系统内存")
        print("  2. 使用分块处理（需要修改代码）")
        print("  3. 考虑使用CSV格式而不是Excel")
        return False
    except Exception as e:
        print(f"错误：转换数据时发生错误 - {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试使用CSV作为备选方案
        print("\n尝试使用CSV格式作为备选方案...")
        try:
            csv_file = output_file.replace('.xlsx', '.csv')
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"已成功保存为CSV文件: {csv_file}")
            return True
        except:
            print("CSV格式也失败")
            return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='JSON数据转Excel工具')
    parser.add_argument('input', nargs='?', default='1.txt', help='输入JSON文件路径（默认: 1.txt）')
    parser.add_argument('-o', '--output', help='输出Excel文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式，使用小样本数据')
    parser.add_argument('--csv', action='store_true', help='输出CSV格式而不是Excel')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("JSON数据转Excel/CSV工具")
    print("=" * 70)
    
    # 输入文件
    input_file = args.input
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件 '{input_file}' 不存在")
        print(f"当前目录: {os.getcwd()}")
        print(f"目录内容: {', '.join(os.listdir('.'))}")
        return
    
    # 生成输出文件名
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if args.csv:
            output_file = f"{base_name}_output_{timestamp}.csv"
        else:
            output_file = f"{base_name}_output_{timestamp}.xlsx"
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("-" * 70)
    
    # 测试模式：只处理前几条数据
    if args.test:
        print("测试模式：只处理前10条数据")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'rows' in data and isinstance(data['rows'], list) and len(data['rows']) > 10:
                data['rows'] = data['rows'][:10]
                data['total'] = 10
                data['records'] = 10
                print(f"已截取前10条数据进行测试")
        except Exception as e:
            print(f"测试模式出错: {e}")
    
    # 读取JSON数据
    json_data = read_json_file(input_file)
    
    if json_data is None:
        return
    
    # 转换为Excel或CSV
    if args.csv:
        print("\n输出格式: CSV")
        try:
            rows = json_data.get('rows', [])
            if not rows:
                print("错误：没有数据行")
                return
            
            df = pd.DataFrame(clean_data(rows))
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"成功保存为CSV文件: {output_file}")
            print(f"生成列数: {len(df.columns)}")
            print(f"生成行数: {len(df):,}")
        except Exception as e:
            print(f"CSV转换失败: {e}")
            return
    else:
        success = convert_json_to_excel(json_data, output_file)
        
        if not success:
            print("\nExcel转换失败，尝试使用CSV格式...")
            csv_file = output_file.replace('.xlsx', '.csv')
            try:
                rows = json_data.get('rows', [])
                if rows:
                    df = pd.DataFrame(clean_data(rows))
                    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                    print(f"已成功保存为CSV文件: {csv_file}")
                    success = True
                    output_file = csv_file
            except Exception as e:
                print(f"CSV格式也失败: {e}")
    
    if success:
        print("-" * 70)
        print("转换完成！")
        print(f"文件已生成: {output_file}")
        
        # 显示文件大小
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
            
            # 验证文件
            try:
                if output_file.endswith('.xlsx'):
                    df = pd.read_excel(output_file, engine='openpyxl', nrows=2)
                else:
                    df = pd.read_csv(output_file, nrows=2, encoding='utf-8-sig')
                print(f"\n文件验证成功，可读取前{len(df)}行")
            except Exception as e:
                print(f"\n文件验证警告: {e}")
    else:
        print("转换失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
