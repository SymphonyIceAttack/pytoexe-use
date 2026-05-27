#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import sys
from pathlib import Path

def get_input(prompt, default=None):
    try:
        value = input(prompt)
        if not value.strip() and default is not None:
            return default
        return value.strip()
    except EOFError:
        return default

def is_valid_date_part(date_str):
    """检查字符串是否为8位数字并构成合法日期"""
    if not re.match(r'^\d{8}$', date_str):
        return False
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    if year < 1900 or year > 2100:
        return False
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    if month == 2 and day > 29:
        return False
    if month in [4, 6, 9, 11] and day > 30:
        return False
    return True

def process_folder(folder_path, dst_root):
    """处理单个文件夹：提取日期，移动整个文件夹到目标年/月/日下"""
    folder_name = folder_path.name
    # 取文件夹名的前8位字符
    date_part = folder_name[:8]

    if not is_valid_date_part(date_part):
        return f"跳过（文件夹名前8位不是有效日期）: {folder_name}"

    year = date_part[0:4]
    month = date_part[4:6]
    day = date_part[6:8]

    target_dir = dst_root / year / month / day
    # 目标路径下保持原文件夹名，不修改
    target_path = target_dir / folder_name

    try:
        # 创建目标父目录（如果不存在）
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"失败（创建目录错误）: {folder_name} - {e}"

    try:
        # 移动整个文件夹（如果目标位置已存在同名文件夹，则合并或覆盖？为了安全，先检查）
        if target_path.exists():
            # 若目标文件夹已存在，可以选择跳过或合并。这里选择跳过并提示
            return f"跳过（目标已存在）: {folder_name} -> {target_path}"
        shutil.move(str(folder_path), str(target_path))
        return f"成功: {folder_name} -> {year}/{month}/{day}/"
    except Exception as e:
        return f"失败（移动文件夹错误）: {folder_name} - {e}"

def main():
    print("=" * 70)
    print("按文件夹名前8位日期分层整理工具（移动整个文件夹）")
    print("将源文件夹中的子文件夹移动到 目标根路径/年/月/日/原文件夹名")
    print("=" * 70)

    # 获取源文件夹路径（包含需要整理的子文件夹的父文件夹）
    if len(sys.argv) >= 2:
        src = sys.argv[1].strip()
    else:
        src = get_input("请输入源文件夹路径（包含待整理子文件夹的目录）: ")
    if not src:
        print("错误：未提供源文件夹路径。")
        sys.exit(1)

    src_path = Path(src)
    if not src_path.exists() or not src_path.is_dir():
        print(f"错误：源文件夹不存在或不是目录：{src_path}")
        sys.exit(1)

    # 获取目标根路径
    if len(sys.argv) >= 3:
        dst_root = sys.argv[2].strip()
    else:
        dst_root = get_input("请输入目标根路径（支持网络路径，如 \\\\server\\share\\archive）: ")
    if not dst_root:
        print("错误：未提供目标根路径。")
        sys.exit(1)

    dst_root_path = Path(dst_root)
    try:
        dst_root_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"错误：无法创建目标根路径 {dst_root_path}，请检查权限。\n{e}")
        sys.exit(1)

    print(f"\n源文件夹: {src_path}")
    print(f"目标根路径: {dst_root_path}")
    print("开始整理子文件夹...\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    # 遍历源文件夹下的直接子文件夹（不递归子子文件夹，如果需要递归可加参数）
    for item in src_path.iterdir():
        if item.is_dir():
            result = process_folder(item, dst_root_path)
            print(result)
            if result.startswith("成功"):
                success_count += 1
            elif result.startswith("跳过"):
                skip_count += 1
            else:
                error_count += 1

    print("\n" + "=" * 70)
    print(f"整理完成！成功移动: {success_count} 个文件夹")
    print(f"跳过（不符合日期格式或目标已存在）: {skip_count} 个文件夹")
    print(f"失败（权限/其他错误）: {error_count} 个文件夹")
    print("=" * 70)

    input("按 Enter 键退出...")

if __name__ == "__main__":
    main()