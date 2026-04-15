import sys
import pandas as pd
import os
from pathlib import Path

def process_excel(filename):
    """
    处理Excel文件：删除第一行，按产品代号汇总数量，输出新文件。
    """
    try:
        # 1. 读取Excel文件
        # header=None 表示原始数据没有列名，我们需要手动处理
        df = pd.read_excel(filename, header=None, dtype=str) 
        
        # 2. 删除第一行（标题行）
        # iloc[1:] 表示从第2行开始取所有行
        data_df = df.iloc[1:].copy()
        
        # 3. 检查是否有足够的数据
        if data_df.empty:
            print("错误：文件中没有数据可供处理。")
            return

        # 4. 定义列名（基于你的文档格式）
        # 根据你上传的文档，B列是产品代号（索引1），E是期初（4），F是入库（5），G是出库（6），H是期末（7）
        # 其他列保持原样，我们只汇总数值列
        col_names = [
            '產品描述', '產品代號', '產品名稱', '單位',
            '期初數量', '入庫數量', '出庫數量', '期末數量',
            '產品單重', '商品名稱', '條碼代號', '類別'
            # ... 如果有更多列，可以继续添加，或者保持默认数字索引
        ]
        
        # 如果列数超过我们定义的名称，用数字填充剩余列名以避免报错
        while len(col_names) < data_df.shape[1]:
            col_names.append(f'Column_{len(col_names)}')
            
        data_df.columns = col_names

        # 5. 数据类型转换（将数量列转为数值型以便计算）
        # 将非数字的字符串（如空字符串）强制转为 NaN，然后填 0
        numeric_cols = ['期初數量', '入庫數量', '出庫數量', '期末數量']
        
        for col in numeric_cols:
            # errors='coerce' 表示遇到无法转换的值设为 NaN
            data_df[col] = pd.to_numeric(data_df[col], errors='coerce').fillna(0).astype(int)

        # 6. 核心逻辑：分组汇总
        # groupby('產品代號')：依据产品代号分组
        # agg：定义聚合规则
        # 对于数量列，使用 sum 进行求和
        # 对于非数量列，使用 first() 取该组的第一笔数据（保持信息不变）
        
        # 准备聚合字典
        agg_dict = {}
        for col in data_df.columns:
            if col in numeric_cols:
                agg_dict[col] = 'sum'
            else:
                agg_dict[col] = 'first' # 保持该组第一行的信息

        # 执行分组汇总
        result_df = data_df.groupby('產品代號', as_index=False).agg(agg_dict)

        # 7. 生成输出文件名
        # 使用 pathlib 处理路径和后缀
        input_path = Path(filename)
        output_filename = f"{input_path.stem}_sum{input_path.suffix}"
        
        # 8. 写入Excel
        result_df.to_excel(output_filename, index=False)
        print(f"成功！已生成文件：{output_filename}")
        
    except Exception as e:
        print(f"处理失败！错误信息：{e}")

if __name__ == "__main__":
    # 检查是否传入了参数
    if len(sys.argv) != 2:
        print("使用方法：python excel_summarizer.py <Excel文件名>")
        print("或者直接拖拽Excel文件到此程序上。")
        input("按回车键退出...")
    else:
        input_file = sys.argv[1]
        # 检查文件是否存在
        if os.path.exists(input_file):
            process_excel(input_file)
            input("处理完成，按回车键退出...")
        else:
            print(f"错误：找不到文件 '{input_file}'。")
            input("按回车键退出...")