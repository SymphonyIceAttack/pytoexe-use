import pandas as pd
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox

def get_college(row):
    # 逻辑：原表有学院则用原表，否则按学号判断
    original_college = str(row.get('学院', '')).strip()
    if original_college and original_college != 'nan':
        return original_college
    
    sid = str(row.get('学工号', '')).strip()
    # 规则：5开头且第6位（索引5）是0
    if sid.startswith('5') and len(sid) >= 6 and sid[5] == '0':
        return "电子信息与电气工程学院"
    else:
        return "自动化与感知学院"

def process_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if not file_path: return

    try:
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        # 以“处理结果+时间戳”命名总文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_main_dir = f"处理结果_{timestamp}"
        
        # 获取运行前一天的日期，格式化为 M-D (如 4-12)
        yesterday_dt = datetime.now() - timedelta(days=1)
        yesterday_str = f"{yesterday_dt.month}-{yesterday_dt.day}"

        for sheet_name, df in all_sheets.items():
            sheet_dir = os.path.join(output_main_dir, sheet_name)
            os.makedirs(sheet_dir, exist_ok=True)

            # 清洗列名，统一转为字符串并去除空格
            df.columns = [str(c).strip() for c in df.columns]
            
            # 基础数据提取
            processed_data = pd.DataFrame()
            processed_data['姓名'] = df.get('姓名', '')
            # 兼容“学号”或“学工号”列名
            sid_col = '学号' if '学号' in df.columns else '学工号'
            processed_data['学工号'] = df.get(sid_col, '')
            
            # 学院判定逻辑
            processed_data['学院'] = df.apply(get_college, axis=1)
            
            # 录取状态判定 (岗位列非空则录取)
            post_col = '志愿者岗位'
            if post_col in df.columns:
                processed_data['录取状态'] = df[post_col].apply(
                    lambda x: "已录取" if pd.notna(x) and str(x).strip() != "" else "未录取"
                )
            else:
                processed_data['录取状态'] = "未录取"

            # --- 文件1：报名表 (全员) ---
            reg_df = processed_data.copy()
            reg_df['报名时间'] = yesterday_str
            reg_df = reg_df[['姓名', '学工号', '学院', '报名时间', '录取状态']]
            reg_df.to_excel(os.path.join(sheet_dir, f"{sheet_name}_报名表.xlsx"), index=False)

            # --- 文件2：签到表 (仅已录取) ---
            sign_df = processed_data[processed_data['录取状态'] == "已录取"].copy()
            sign_df['签到时间'] = ""
            sign_df['签到状态'] = "是"
            sign_df['参与状态'] = "已参与"
            # 包含要求的7列
            sign_cols = ['姓名', '学工号', '学院', '签到时间', '录取状态', '签到状态', '参与状态']
            sign_df = sign_df[sign_cols]
            sign_df.to_excel(os.path.join(sheet_dir, f"{sheet_name}_签到表.xlsx"), index=False)

        messagebox.showinfo("完成", f"所有Sheet处理成功！\n文件夹：{output_main_dir}")
    except Exception as e:
        messagebox.showerror("错误", f"发生故障：{str(e)}")

# GUI 界面
root = tk.Tk()
root.title("志愿者表一键生成器")
root.geometry("400x200")
tk.Label(root, text="志愿者数据自动化工具", font=("微软雅黑", 12), pady=20).pack()
tk.Button(root, text="选择 Excel 文件并运行", command=process_excel, 
          bg="#0078d4", fg="white", font=("微软雅黑", 10), padx=20, pady=10).pack()
root.mainloop()