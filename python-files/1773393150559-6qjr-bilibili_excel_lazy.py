#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili视频发布时间获取工具 - 懒人Excel版
全自动处理Excel文件，一键添加视频发布时间
"""

import urllib.request
import urllib.parse
import json
import re
import time
import random
import os
import sys
from datetime import datetime

# 尝试导入pandas和openpyxl，如果没有安装则提供友好提示
try:
    import pandas as pd
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

class BilibiliExcelLazy:
    """Bilibili Excel懒人处理类"""
    
    def __init__(self):
        """初始化"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
    
    def get_video_info(self, bvid):
        """获取视频信息"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # 尝试API接口
                api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
                req = urllib.request.Request(api_url, headers=self.headers)
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            content = response.read().decode('utf-8')
                            data = json.loads(content)
                            if data.get('code') == 0:
                                publish_time = data['data']['pubdate']
                                readable_time = datetime.fromtimestamp(publish_time).strftime('%Y-%m-%d %H:%M:%S')
                                return readable_time
                except urllib.error.HTTPError as e:
                    pass
                except urllib.error.URLError as e:
                    pass
                
                # 尝试网页解析
                video_url = f'https://www.bilibili.com/video/{bvid}'
                req = urllib.request.Request(video_url, headers=self.headers)
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            html_content = response.read().decode('utf-8')
                            
                            # 查找时间戳
                            time_match = re.search(r'\"pubdate\"\s*:\s*(\d+)', html_content)
                            if time_match:
                                timestamp = int(time_match.group(1))
                                readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                return readable_time
                            
                            # 查找日期文本
                            date_match = re.search(r'<meta property="og:release_date" content="([\d-]+)"', html_content)
                            if date_match:
                                return date_match.group(1)
                except urllib.error.HTTPError as e:
                    pass
                except urllib.error.URLError as e:
                    pass
                
                # 重试延迟
                if retry_count < max_retries - 1:
                    wait_time = (retry_count + 1) * 2
                    time.sleep(wait_time)
                
            except Exception as e:
                pass
            
            retry_count += 1
        
        return "获取失败"
    
    def extract_bvid(self, url):
        """从URL中提取BV号"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            
            # 从路径中提取
            path_parts = parsed_url.path.split('/')
            for part in path_parts:
                if part.startswith('BV'):
                    return part
            
            # 从查询参数中提取
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if 'bvid' in query_params:
                return query_params['bvid'][0]
            
            return None
        except:
            return None
    
    def find_url_column(self, df):
        """自动查找URL列"""
        url_keywords = ['视频URL', '视频链接', '视频地址', 'url', 'link', '视频', 'bilibili']
        
        for col in df.columns:
            col_lower = col.lower()
            for keyword in url_keywords:
                if keyword.lower() in col_lower:
                    return col
        
        # 检查第一行数据，查找包含bilibili.com的列
        if not df.empty:
            first_row = df.iloc[0]
            for col in df.columns:
                value = str(first_row[col])
                if 'bilibili.com' in value and ('BV' in value or 'video' in value):
                    return col
        
        return None
    
    def process_excel_file(self, file_path):
        """处理Excel文件"""
        try:
            print(f"\n📁 正在读取Excel文件: {file_path}")
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            print(f"📊 数据概览:")
            print(f"   总行数: {len(df)}")
            print(f"   总列数: {len(df.columns)}")
            print(f"   列名: {list(df.columns)}")
            
            # 查找URL列
            url_column = self.find_url_column(df)
            
            if not url_column:
                print(f"\n❌ 无法自动识别视频URL列")
                print("请确保Excel文件中包含视频URL列，列名可以是：")
                print("   视频URL、视频链接、视频地址、url、link等")
                return None
            
            print(f"\n✅ 自动识别URL列: '{url_column}'")
            
            # 添加发布时间列
            if '发布时间' not in df.columns:
                df['发布时间'] = ""
            
            # 统计需要处理的行数
            total_rows = len(df)
            url_rows = df[url_column].notna().sum()
            print(f"\n📊 需要处理: {url_rows} 个视频链接 (共 {total_rows} 行)")
            
            # 处理每个视频
            success_count = 0
            failed_count = 0
            
            print(f"\n🚀 开始处理视频链接...")
            print("=" * 50)
            
            for index, row in df.iterrows():
                url = str(row[url_column]) if pd.notna(row[url_column]) else ""
                
                if not url or 'bilibili.com' not in url:
                    continue
                
                print(f"\n第 {index + 1}/{total_rows} 个视频")
                print(f"  URL: {url}")
                
                # 提取BV号
                bvid = self.extract_bvid(url)
                
                if not bvid:
                    print(f"  ❌ 无法提取BV号")
                    df.at[index, '发布时间'] = "无法提取BV号"
                    failed_count += 1
                    continue
                
                print(f"  BV号: {bvid}")
                
                # 获取发布时间
                publish_time = self.get_video_info(bvid)
                
                if publish_time and publish_time != "获取失败":
                    df.at[index, '发布时间'] = publish_time
                    success_count += 1
                    print(f"  ✅ 成功: {publish_time}")
                else:
                    df.at[index, '发布时间'] = publish_time
                    failed_count += 1
                    print(f"  ❌ 失败: {publish_time}")
                
                # 随机延迟
                delay = random.uniform(1, 3)
                print(f"  ⏳ 等待 {delay:.2f} 秒...")
                time.sleep(delay)
            
            # 保存结果
            output_file = file_path.replace('.xlsx', '_with_time.xlsx')
            if output_file == file_path:
                output_file = file_path.replace('.xls', '_with_time.xlsx')
            if output_file == file_path:
                output_file = os.path.splitext(file_path)[0] + '_with_time.xlsx'
            
            # 保存到Excel文件
            df.to_excel(output_file, index=False)
            
            print(f"\n{'=' * 50}")
            print(f"✅ 处理完成！")
            print(f"📊 统计信息:")
            print(f"   总处理: {url_rows} 个视频")
            print(f"   成功: {success_count} 个")
            print(f"   失败: {failed_count} 个")
            print(f"   成功率: {success_count / url_rows * 100:.1f}%")
            print(f"📁 结果保存到: {output_file}")
            
            return output_file
            
        except FileNotFoundError:
            print(f"\n❌ 找不到文件: {file_path}")
            return None
        except PermissionError:
            print(f"\n❌ 没有权限读写文件: {file_path}")
            return None
        except Exception as e:
            print(f"\n❌ 处理Excel文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def install_dependencies(self):
        """安装依赖包"""
        try:
            print("\n🔧 正在安装必要的Python包...")
            print("这可能需要几分钟时间，请耐心等待...")
            
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
            
            print("\n✅ 依赖包安装成功！")
            print("请重新运行程序")
            return True
            
        except Exception as e:
            print(f"\n❌ 安装依赖包时出错: {e}")
            print("\n请手动安装依赖包:")
            print("   pip install pandas openpyxl")
            return False
    
    def list_excel_files(self):
        """列出当前目录的Excel文件"""
        excel_extensions = ['.xlsx', '.xls', '.xlsm']
        excel_files = []
        
        try:
            for file in os.listdir('.'):
                if any(file.lower().endswith(ext) for ext in excel_extensions):
                    excel_files.append(file)
        except Exception as e:
            print(f"列出文件时出错: {e}")
        
        return excel_files

def main():
    """主函数"""
    print("=" * 50)
    print("🎯 Bilibili视频发布时间获取工具 - 懒人Excel版")
    print("=" * 50)
    print("全自动处理Excel文件，一键添加视频发布时间")
    print("支持自动识别URL列，无需手动配置")
    print("=" * 50)
    
    # 检查Excel支持
    if not EXCEL_SUPPORT:
        print("\n⚠️  检测到缺少必要的Python包")
        print("需要安装: pandas 和 openpyxl")
        
        user_input = input("\n是否自动安装依赖包？(y/N): ").strip().lower()
        if user_input == 'y':
            app = BilibiliExcelLazy()
            if app.install_dependencies():
                return
            else:
                print("\n程序将以CSV模式运行...")
        else:
            print("\n程序将以CSV模式运行...")
    
    # 创建应用实例
    app = BilibiliExcelLazy()
    
    # 列出当前目录的Excel文件
    excel_files = app.list_excel_files()
    
    if excel_files:
        print(f"\n📋 当前目录的Excel文件:")
        for i, file in enumerate(excel_files, 1):
            print(f"   {i}. {file}")
        
        # 询问用户选择文件
        user_input = input(f"\n请输入文件编号或文件名（或按Enter使用第一个文件）: ").strip()
        
        if user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(excel_files):
                file_path = excel_files[index]
            else:
                print("无效的文件编号")
                return
        elif user_input:
            file_path = user_input
        else:
            file_path = excel_files[0]
            print(f"使用第一个文件: {file_path}")
    else:
        print(f"\n❌ 当前目录没有找到Excel文件")
        print("请将Excel文件放在程序同一目录下")
        
        # 检查是否有CSV文件
        csv_files = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
        if csv_files:
            print(f"\n📋 找到CSV文件:")
            for i, file in enumerate(csv_files, 1):
                print(f"   {i}. {file}")
            
            user_input = input(f"\n是否处理CSV文件？(y/N): ").strip().lower()
            if user_input == 'y':
                print("\n请使用 bilibili_simple_version.py 处理CSV文件")
                print("运行命令: python bilibili_simple_version.py")
            return
        
        return
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"\n❌ 找不到文件: {file_path}")
        return
    
    # 处理文件
    if file_path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
        if EXCEL_SUPPORT:
            output_file = app.process_excel_file(file_path)
        else:
            print(f"\n❌ 无法处理Excel文件，请先安装依赖包")
            print("运行命令: pip install pandas openpyxl")
            return
    else:
        print(f"\n❌ 不支持的文件格式，请使用Excel文件(.xlsx, .xls)")
        return
    
    if output_file:
        print(f"\n🎉 任务完成！")
        print(f"📁 输入文件: {file_path}")
        print(f"📁 输出文件: {output_file}")
        print(f"\n您可以直接用Excel打开 {output_file} 查看结果")
        
        # 显示文件信息
        file_size = os.path.getsize(output_file) / 1024
        print(f"\n📊 文件信息:")
        print(f"   文件名: {os.path.basename(output_file)}")
        print(f"   文件大小: {file_size:.1f} KB")
        print(f"   保存位置: 当前目录")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已被用户中断")
    except Exception as e:
        print(f"\n❌ 程序发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按Enter键退出程序...")