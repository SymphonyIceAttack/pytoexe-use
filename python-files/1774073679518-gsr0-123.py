import os
import sys
import re
from pathlib import Path

try:
    import pandas as pd
    import pyperclip
except ImportError as e:
    print(f"缺少依赖库: {e}")
    print("请运行以下命令安装: pip install pandas pyperclip")
    sys.exit(1)

def natural_sort_key(s):
    """自然排序的关键函数，用于处理数字和字母混合的文件名"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'([0-9]+)', str(s))]

def main():
    script_dir = Path(__file__).parent.resolve()
    print(f"正在扫描目录: {script_dir}\\n")
    
    all_values = []
    files_processed = 0
    matches_count = 0
    
    # 遍历目录下所有文件，并按文件名自然排序
    file_list = sorted([f for f in script_dir.iterdir() if f.suffix.lower() == '.csv'], 
                       key=natural_sort_key)
    
    total_files = len(file_list)
    if total_files == 0:
        print("未找到任何CSV文件")
        return
    
    print(f"总共找到 {total_files} 个CSV文件，开始处理...")
    
    for i, file_path in enumerate(file_list, 1):
        files_processed += 1
        # 显示进度
        if i % 5 == 0 or i == total_files:
            print(f"处理进度: {i}/{total_files} ({i/total_files*100:.1f}%)")
        
        try:
            # 优先尝试utf-8，如果失败再尝试gbk
            try:
                df = pd.read_csv(file_path, dtype=str, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, dtype=str, encoding='gbk')
            
            if df.empty:
                continue
            
            # 确保至少有 A 列和 B 列 (即第0列和第1列)
            if df.shape[1] < 2:
                print(f"[跳过] {file_path.name}: 列数不足 2 列 (找不到 A 列和 B 列)")
                continue
            
            # 重命名前两列为 'A' 和 'B' 以便操作，防止原表头名称干扰
            col_a = df.iloc[:, 0]
            col_b = df.iloc[:, 1]
            
            # 核心逻辑：
            # 1. 将 A 列转换为字符串 (防止原本是数字类型导致 'in' 判断失效)
            # 2. 查找包含 "600" 的行
            mask = col_a.astype(str).str.contains('600', na=False)
            
            if mask.any():
                # 获取满足条件的行的 B 列数据
                matched_values = col_b[mask].tolist()
                
                # 过滤掉空值或纯空格
                clean_values = [str(v).strip() for v in matched_values if pd.notna(v) and str(v).strip() != '']
                
                if clean_values:
                    all_values.extend(clean_values)
                    matches_count += len(clean_values)
                    print(f"[找到] {file_path.name}: 发现 {len(clean_values)} 个匹配项")
        except Exception as e:
            print(f"[错误] 处理 {file_path.name} 时出错: {e}")
    
    if not all_values:
        print("\\n未在任何 CSV 文件的 A 列中找到包含 '600' 的行，或对应的 B 列为空。")
        print("剪贴板未修改。")
        return
    
    # 格式化结果：每个值单独一行
    result_text = "\\n".join(all_values)
    
    # 复制到剪贴板
    try:
        pyperclip.copy(result_text)
        print("-" * 60)
        print(f"✅ 成功扫描 {files_processed} 个 CSV 文件。")
        print(f"✅ 共提取 {len(all_values)} 个对应的 B 列数值。")
        print("-" * 60)
        print("📋 数据已复制到剪贴板！(每行一个数值)")
        print("\\n前 10 个结果预览:")
        for item in all_values[:10]:
            print(f"  {item}")
        if len(all_values) > 10:
            print(f"  ... (还有 {len(all_values) - 10} 个)")
    except Exception as e:
        print(f"\\n❌ 复制到剪贴板失败: {e}")
        print("\\n以下是提取到的数据 (请手动复制):")
        print(result_text)

if __name__ == "__main__":
    main()
