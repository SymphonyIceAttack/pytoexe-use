import os
import shutil
import pandas as pd
from tkinter import Tk, filedialog, messagebox

def organize_images():
    # 初始化界面
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    messagebox.showinfo("提示", "请选择包含编码的Excel表格文件")

    # 1. 选择Excel文件
    excel_path = filedialog.askopenfilename(
        title="选择Excel文件",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )

    if not excel_path:
        return

    # 获取程序当前所在的目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "整理结果")

    # 如果输出文件夹已存在，先清空或保留（这里选择直接复用）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # 2. 读取Excel数据
        # header=0 表示第一行是表头
        df = pd.read_excel(excel_path, header=0)

        # 假设第一列是分类（宽/厚度），后续列是编码
        # iloc[:, 0] 获取第一列的所有值
        categories = df.iloc[:, 0].dropna().astype(str).str.strip()

        total_found = 0
        total_missing = 0

        # 遍历每一行进行分类
        for index, category in enumerate(categories):
            # 获取该行除了第一列以外的所有数据（即所有的编码）
            row_data = df.iloc[index, 1:].dropna()

            # 创建分类文件夹 (例如: ./整理结果/10-20)
            category_folder = os.path.join(output_dir, str(category))
            if not os.path.exists(category_folder):
                os.makedirs(category_folder)

            print(f"正在处理分类: {category} ...")

            # 遍历该行的每一个编码
            for code in row_data:
                code_str = str(code).strip()
                if not code_str or code_str == 'nan':
                    continue

                # 在当前目录下搜索包含该编码的图片文件
                found = False
                for root_dir, dirs, files in os.walk(base_dir):
                    # 跳过我们刚刚创建的输出文件夹，避免死循环
                    if output_dir in root_dir:
                        continue

                    for file in files:
                        # 检查文件名是否包含编码，且后缀是图片格式
                        if code_str in file and file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                            src_path = os.path.join(root_dir, file)
                            dst_path = os.path.join(category_folder, file)

                            # 防止同名文件覆盖，如果存在则重命名
                            if os.path.exists(dst_path):
                                base, ext = os.path.splitext(file)
                                dst_path = os.path.join(category_folder, f"{base}_{index}{ext}")

                            shutil.copy2(src_path, dst_path)
                            total_found += 1
                            found = True
                            break # 找到一个就跳出当前目录循环，继续找下一个编码

                if not found:
                    total_missing += 1
                    print(f"  [未找到] 编码: {code_str}")

        messagebox.showinfo("完成", f"处理完毕！\n成功复制: {total_found} 张\n未找到: {total_missing} 个\n文件保存在: {output_dir}")

    except Exception as e:
        messagebox.showerror("错误", f"发生错误: {str(e)}")

if __name__ == "__main__":
    organize_images()