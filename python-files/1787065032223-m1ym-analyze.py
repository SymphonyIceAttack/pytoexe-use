# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 22:38:28 2026

@author: 23772
"""

import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

def select_file():
    """弹出文件选择对话框，返回选择的文件路径"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    file_path = filedialog.askopenfilename(
        title="请选择 Excel 数据文件",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def calculate_metrics(file_path):
    """执行所有计算，返回结果字典"""
    df = pd.read_excel(file_path, header=1)
    df.columns = df.columns.str.strip()

    # ---------- 反应时 ----------
    def get_rt(columns):
        vals = []
        for col in columns:
            series = df[col]
            valid = series[~series.isna()]
            valid = valid[valid != 0]
            valid = valid[valid != '0']
            valid = pd.to_numeric(valid, errors='coerce').dropna()
            vals.extend(valid.tolist())
        return np.mean(vals) if vals else None

    neutral_rt = get_rt(['ciji1.RT', 'ciji2.RT', 'ciji3.RT'])
    negative_rt = get_rt(['ciji4.RT', 'ciji5.RT', 'ciji6.RT'])

    # ---------- 错误率 ----------
    def extract_error(cresp_col, acc_col, start_row, end_row):
        vals = []
        # 将Excel行号转为pandas索引（行号3 → 索引0）
        for idx in range(start_row - 3, end_row - 2):
            cresp_val = df.iloc[idx][cresp_col]
            if pd.isna(cresp_val) or str(cresp_val).strip() == '':
                acc_val = df.iloc[idx][acc_col]
                if not pd.isna(acc_val):
                    vals.append(acc_val)
        return vals

    neutral_err = []
    neutral_err += extract_error('ciji1.CRESP', 'ciji1.ACC', 15, 58)
    neutral_err += extract_error('ciji2.CRESP', 'ciji2.ACC', 59, 102)
    neutral_err += extract_error('ciji3.CRESP', 'ciji3.ACC', 103, 147)

    negative_err = []
    negative_err += extract_error('ciji4.CRESP', 'ciji4.ACC', 148, 191)
    negative_err += extract_error('ciji5.CRESP', 'ciji5.ACC', 192, 235)
    negative_err += extract_error('ciji6.CRESP', 'ciji6.ACC', 236, 279)

    def calc_rate(vals):
        if not vals:
            return None
        zero_count = sum(1 for v in vals if v == 0 or v == '0')
        return zero_count / len(vals) * 100

    neutral_err_rate = calc_rate(neutral_err)
    negative_err_rate = calc_rate(negative_err)

    return {
        '中性情绪反应时': neutral_rt,
        '负性情绪反应时': negative_rt,
        '中性情绪错误率': neutral_err_rate,
        '负性情绪错误率': negative_err_rate
    }

def save_results(result, file_path):
    """将结果保存到文本文件"""
    base = os.path.splitext(file_path)[0]
    out_file = base + '_结果.txt'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("========== 分析结果 ==========\n")
        for key, val in result.items():
            if val is None:
                f.write(f"{key}：无有效数据无法计算\n")
            else:
                if '率' in key:
                    f.write(f"{key}：{val:.2f}%\n")
                else:
                    f.write(f"{key}：{val:.2f}\n")
    return out_file

def main():
    print("请在弹出的文件选择框中选择 Excel 文件...")
    file_path = select_file()
    if not file_path:
        print("未选择文件，程序退出。")
        return

    try:
        result = calculate_metrics(file_path)
        out_path = save_results(result, file_path)

        # 同时打印到控制台
        print("\n========== 分析结果 ==========")
        for key, val in result.items():
            if val is None:
                print(f"{key}：无有效数据无法计算")
            else:
                if '率' in key:
                    print(f"{key}：{val:.2f}%")
                else:
                    print(f"{key}：{val:.2f}")
        print(f"\n结果已保存至：{out_path}")

        # 弹出提示框
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("完成", f"计算完成！\n结果已保存至：\n{out_path}")
        root.destroy()

    except Exception as e:
        print(f"处理出错：{e}")
        tk.messagebox.showerror("错误", f"处理出错：{e}")

if __name__ == "__main__":
    main()