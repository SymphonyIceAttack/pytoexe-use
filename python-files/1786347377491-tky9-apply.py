#!/usr/bin/env python3
"""
应用补丁 patch.json 到目标文件夹（原 A），只处理文本文件，自动忽略非文本。
用法: python apply_patch.py /path/to/A
"""

import os
import sys
import json
from pathlib import Path

# 复用相同的 is_text_file 函数（或直接内嵌）
def is_text_file(file_path, sample_size=1024):
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(sample_size)
        if b'\x00' in raw:
            return False
        raw.decode('utf-8')
        return True
    except (UnicodeDecodeError, IOError):
        return False

def apply_ed_commands(file_path, commands):
    """
    执行 ed 风格命令修改文件。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 从后往前应用，避免行号偏移
    sorted_cmds = sorted(commands, key=lambda x: x.get('start', 0), reverse=True)

    for cmd in sorted_cmds:
        op = cmd['op']
        if op == 'd':
            start = cmd['start'] - 1
            end = cmd['end']
            del lines[start:end]
        elif op == 'c':
            start = cmd['start'] - 1
            end = cmd['end']
            new_lines = cmd['lines']
            lines[start:end] = new_lines
        elif op == 'a':
            start = cmd['start']
            new_lines = cmd['lines']
            lines[start:start] = new_lines
        elif op == 'i':
            start = cmd['start'] - 1
            new_lines = cmd['lines']
            lines[start:start] = new_lines

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def apply_patch(target_dir):
    target_path = Path(target_dir)
    if not target_path.is_dir():
        print("错误：目标目录不存在或不是目录")
        sys.exit(1)

    patch_file = 'patch.json'
    if not os.path.isfile(patch_file):
        print("错误：未找到补丁文件 patch.json，请确保它在当前目录")
        sys.exit(1)

    with open(patch_file, 'r', encoding='utf-8') as f:
        patch = json.load(f)

    # 1. 删除文件（仅当目标文件存在且为文本）
    for rel in patch.get('deleted', []):
        file_path = target_path / rel
        if file_path.exists():
            if is_text_file(file_path):
                os.remove(file_path)
                print(f"删除文本文件: {rel}")
            else:
                print(f"警告: 目标文件 {rel} 不是文本，跳过删除（保留）")
        else:
            print(f"警告: 文件 {rel} 不存在，跳过删除")

    # 2. 新增文件（补丁中都是文本）
    for item in patch.get('added', []):
        rel = item['path']
        content = item['content']
        file_path = target_path / rel
        # 创建父目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"新增文本文件: {rel}")

    # 3. 修改文件（补丁中都是文本，但目标可能被用户改成了二进制，需保护）
    for rel, commands in patch.get('files', {}).items():
        file_path = target_path / rel
        if not file_path.exists():
            print(f"警告: 文件 {rel} 不存在，无法修改")
            continue
        if not is_text_file(file_path):
            print(f"警告: 目标文件 {rel} 不是文本，跳过修改（保留原样）")
            continue
        apply_ed_commands(file_path, commands)
        print(f"修改文本文件: {rel}")

    print("补丁应用完成！")

if __name__ == '__main__':
    apply_patch('iterationRP Alpha 0.8.26 hotfix')