#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 转等宽对齐文本（只读预览，不改原文件）
用法：python csv_to_mono.py input.csv [output.txt]
"""

import csv
import sys
import os

def csv_to_monospaced(input_file, output_file=None):
    # 自动检测编码（优先 UTF-8，失败则 GBK）
    encodings = ['utf-8-sig', 'gbk', 'utf-8', 'gb18030']
    
    for enc in encodings:
        try:
            with open(input_file, 'r', encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            detected_enc = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        print("❌ 无法识别文件编码，请手动指定")
        return False
    
    if not rows:
        print("⚠️ 空文件")
        return False
    
    # 计算每列最大宽度（考虑中英文混合）
    col_widths = []
    for row in rows:
        # 补齐短行，避免索引越界
        while len(row) > len(col_widths):
            col_widths.append(0)
        for i, cell in enumerate(row):
            # 中文字符算2个英文字符宽度
            width = sum(2 if ord(c) > 127 else 1 for c in cell)
            if width > col_widths[i]:
                col_widths[i] = width
    
    # 构建对齐后的文本
    output_lines = []
    separator_line = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    
    for row_idx, row in enumerate(rows):
        # 补齐短行
        while len(row) < len(col_widths):
            row.append('')
        
        # 对齐每个单元格
        aligned_cells = []
        for i, cell in enumerate(row):
            # 计算实际显示宽度
            display_width = sum(2 if ord(c) > 127 else 1 for c in cell)
            padding = col_widths[i] - display_width
            aligned_cells.append(' ' + cell + ' ' * padding + ' ')
        
        line = '|' + '|'.join(aligned_cells) + '|'
        output_lines.append(line)
        
        # 表头下方加分隔线
        if row_idx == 0:
            output_lines.append(separator_line)
    
    # 顶部加分隔线
    output_lines.insert(0, separator_line)
    # 底部加分隔线
    output_lines.append(separator_line)
    
    result = '\n'.join(output_lines)
    
    # 输出
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"✅ 已保存到：{output_file}")
    else:
        print(result)
    
    # 打印统计信息
    print(f"\n📊 统计：{len(rows)} 行 × {len(col_widths)} 列")
    print(f"🔤 编码：{detected_enc}")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python csv_to_mono.py <输入CSV> [输出文件]")
        print("示例：python csv_to_mono.py data.csv preview.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在：{input_file}")
        sys.exit(1)
    
    csv_to_monospaced(input_file, output_file)