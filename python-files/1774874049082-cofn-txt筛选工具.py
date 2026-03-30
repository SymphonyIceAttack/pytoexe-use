import sys
import os
import re

def process_txt_file(file_path):
    """处理单个TXT文件，按0.5秒间隔规则筛选数据，生成新文件"""
    # 兼容Windows常见编码，解决中文乱码问题
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
    file_content = None
    used_encoding = None
    
    # 尝试读取文件
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                file_content = f.readlines()
            used_encoding = enc
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    
    if file_content is None:
        print(f"错误：无法读取文件 {os.path.basename(file_path)}，请检查文件是否存在或编码格式")
        return False
    
    # 1. 自动识别表头和有效数据（自动跳过表头前的乱码/注释行）
    header_line = None
    header_index = -1
    data_list = []  # 存储格式：(时间浮点数, 原始行内容)
    
    for idx, line in enumerate(file_content):
        stripped_line = line.strip()
        if not stripped_line:
            continue  # 跳过空行
        # 识别表头：必须包含时间、压力、流量、电流四个核心列名
        if '时间' in stripped_line and '压力' in stripped_line and '流量' in stripped_line and '电流' in stripped_line:
            header_line = line
            header_index = idx
            continue
        # 处理表头之后的有效数据行
        if header_index != -1 and idx > header_index:
            # 兼容制表符、多个空格分隔的列格式
            parts = re.split(r'\s+', stripped_line)
            if len(parts) >= 4:
                try:
                    time_val = float(parts[0])
                    data_list.append((time_val, line))
                except ValueError:
                    continue  # 时间格式无效的行直接跳过
    
    # 有效性校验
    if header_line is None:
        print(f"错误：文件 {os.path.basename(file_path)} 未找到有效表头（需包含「时间、压力、流量、电流」）")
        return False
    if len(data_list) == 0:
        print(f"错误：文件 {os.path.basename(file_path)} 未找到有效数据行")
        return False
    
    # 2. 按时间升序排序（兼容原始数据乱序的情况）
    data_list.sort(key=lambda x: x[0])
    max_time = data_list[-1][0]
    
    # 3. 生成目标时间序列：0秒开始，每隔0.5秒一个节点，直到最大时间
    targets = []
    current_target = 0.0
    while current_target <= max_time:
        targets.append(current_target)
        current_target += 0.5
    
    # 4. 核心筛选逻辑：匹配目标时间，无精确匹配取首个大于目标值的行，不重复取行
    result_lines = [header_line]  # 先保留表头
    current_idx = 0
    data_total = len(data_list)
    
    for target in targets:
        # 从当前指针位置向后查找，避免重复遍历
        while current_idx < data_total and data_list[current_idx][0] < target:
            current_idx += 1
        # 找到有效行，加入结果，指针后移避免重复
        if current_idx < data_total:
            result_lines.append(data_list[current_idx][1])
            current_idx += 1
        else:
            break  # 无更多数据，提前退出
    
    # 5. 生成新文件名（原文件名+new）
    file_dir, file_fullname = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_fullname)
    new_file_name = f"{file_name}new{file_ext}"
    new_file_path = os.path.join(file_dir, new_file_name)
    
    # 6. 写入新文件，保持原编码格式
    try:
        with open(new_file_path, 'w', encoding=used_encoding, newline='') as f:
            f.writelines(result_lines)
        print(f"✅ 处理成功！新文件已生成：{new_file_name}")
        print(f"   共保留 {len(result_lines)-1} 行有效数据（不含表头）")
        return True
    except Exception as e:
        print(f"❌ 写入文件失败：{str(e)}")
        return False

def main():
    print("="*40)
    print("      TXT时间序列数据筛选工具")
    print("  功能：按0.5秒间隔筛选数据，无匹配取首个大于目标值的行")
    print("  使用方法：将TXT文件拖拽到本程序图标上即可自动处理")
    print("="*40)
    
    # 获取拖拽的文件路径
    if len(sys.argv) < 2:
        print("\n⚠️  提示：请将需要处理的TXT文件拖拽到本程序图标上运行！")
        input("\n按回车键退出...")
        return
    
    # 批量处理所有拖拽的文件
    success_num = 0
    total_num = len(sys.argv) - 1
    
    for file_path in sys.argv[1:]:
        print(f"\n正在处理：{os.path.basename(file_path)}")
        if process_txt_file(file_path):
            success_num += 1
    
    # 处理结果汇总
    print(f"\n{'='*40}")
    print(f"处理完成！总计：{total_num} 个文件，成功：{success_num} 个，失败：{total_num - success_num} 个")
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()