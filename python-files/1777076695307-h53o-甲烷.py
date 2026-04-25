# -*- coding: utf-8 -*-
"""
甲烷数据自动清洗工具
功能：去除整点数据 + 去除甲烷=0数据
适用：所有和你表格结构一样的 Excel 文件
作者：通用工具
"""

import pandas as pd
import os
import sys

def clean_methane_data(input_file):
    try:
        print("=" * 60)
        print("📊 甲烷数据自动清洗工具（通用版）")
        print("=" * 60)

        # 读取 Excel
        df = pd.read_excel(input_file)

        # 自动适配你的表头
        if "非甲烷总烃监测数据" in str(df.columns[0]):
            df = pd.read_excel(input_file, header=1)

        # 检查必须列
        if "监测时间" not in df.columns or "甲烷" not in df.columns:
            print("❌ 错误：表格必须包含【监测时间】和【甲烷】列！")
            return

        # 转换时间
        df["监测时间"] = pd.to_datetime(df["监测时间"], errors="coerce")
        df = df.dropna(subset=["监测时间"])
        df["分钟"] = df["监测时间"].dt.minute

        # 统计
        total_raw = len(df)
        count_hourly = len(df[df["分钟"] == 0])
        count_zero = len(df[df["甲烷"] == 0])
        count_both = len(df[(df["分钟"] == 0) & (df["甲烷"] == 0)])

        # 清洗
        df_clean = df[(df["分钟"] != 0) & (df["甲烷"] != 0)]
        total_clean = len(df_clean)

        # 输出结果
        print(f"✅ 原始数据：{total_raw} 组")
        print(f"❌ 去除整点数据：{count_hourly} 组")
        print(f"❌ 去除甲烷=0数据：{count_zero} 组")
        print(f"🔁 重复去除：{count_both} 组")
        print("-" * 60)
        print(f"🎉 最终有效数据：{total_clean} 组")
        print("-" * 60)

        # 保存文件
        out_name = os.path.splitext(input_file)[0] + "_已清洗.xlsx"
        df_clean.to_excel(out_name, index=False)
        print(f"📁 已保存：{out_name}")

    except Exception as e:
        print(f"❌ 处理失败：{str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            clean_methane_data(file_path)
        else:
            print("❌ 文件不存在")
    else:
        print("请把 Excel 文件拖到本程序图标上运行！")

    input("\n按回车退出...")