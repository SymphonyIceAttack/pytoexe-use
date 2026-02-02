import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import warnings
warnings.filterwarnings('ignore')
import openpyxl

# 核心规则：机器6600元优先，刀片仅5个(38元/个，190元)、10个(36元/个，360元)固定组合
def calculate_invoice_data(file_path):
    # 1. 读取Excel，自动排除最后2个工作表，仅保留已用列
    excel_file = pd.ExcelFile(file_path)
    use_sheets = excel_file.sheet_names[:-2] if len(excel_file.sheet_names) >= 2 else excel_file.sheet_names
    df = pd.concat([pd.read_excel(file_path, sheet_name=s, engine='openpyxl') for s in use_sheets], ignore_index=True)
    
    # 2. 计算待开票金额（订单金额-已开票金额），过滤负数/空行异常
    if '订单金额' not in df.columns or '已开票金额' not in df.columns:
        raise Exception('未找到"订单金额"或"已开票金额"列，请核对文件！')
    df['订单金额'] = pd.to_numeric(df['订单金额'], errors='coerce').fillna(0)
    df['已开票金额'] = pd.to_numeric(df['已开票金额'], errors='coerce').fillna(0)
    df['待开票金额'] = df['订单金额'] - df['已开票金额']
    df = df[df['待开票金额'] >= 0].reset_index(drop=True)  # 仅保留有效待开票数据
    
    # 3. 金额自动拆解逻辑（6600机器→10个刀片→5个刀片，仅固定组合）
    def split_amount(amount):
        # 优先匹配新款机器6600元（整数倍）
        machine_6600 = int(amount // 6600)
        remaining = amount % 6600  # 扣减机器后剩余金额
        
        # 剩余金额匹配刀片：10个（360元）优先→5个（190元）
        blade_10 = int(remaining // 360)
        remaining = remaining % 360
        blade_5 = int(remaining // 190)
        remaining = round(remaining % 190, 2)  # 最终未匹配的异常差额
        
        return pd.Series([machine_6600, blade_10, blade_5, remaining])
    
    # 应用拆解，生成开票明细列
    df[['机器(6600元/台)', '刀片(10个/360元)', '刀片(5个/190元)', '未匹配异常差额(元)']] = df['待开票金额'].apply(split_amount)
    
    # 4. 生成汇总数据（对账用）
    total_order = round(df['订单金额'].sum(), 2)
    total_invoiced = round(df['已开票金额'].sum(), 2)
    total_to_invoice = round(df['待开票金额'].sum(), 2)
    abnormal_rows = len(df[df['未匹配异常差额(元)'] != 0])
    valid_rows = len(df)
    summary = {
        '有效数据行数': valid_rows,
        '订单金额总计(元)': total_order,
        '已开票金额总计(元)': total_invoiced,
        '待开票金额总计(元)': total_to_invoice,
        '异常差额行数(需核对)': abnormal_rows
    }
    return df, summary

# 可视化操作界面（简单易懂，仅3个核心操作）
def main():
    root = tk.Tk()
    root.title('批量开票金额拆解工具')
    root.geometry('550x320')
    root.resizable(False, False)
    
    # 界面文字/按钮布局
    tk.Label(root, text='阿里巴巴履约表→开票明细工具', font=('微软雅黑', 14, 'bold')).pack(pady=15)
    tk.Label(root, text='规则：自动算待开票金额→6600机器优先→刀片仅5/10个固定组合', font=('微软雅黑', 9), fg='gray').pack(pady=5)
    tk.Label(root, text='自动排除最后2页丨仅保留有效列丨异常差额提醒', font=('微软雅黑', 9), fg='gray').pack(pady=2)
    
    # 核心功能按钮：选择文件→处理→导出
    def select_and_process():
        try:
            # 选择履约表Excel文件
            file_path = filedialog.askopenfilename(
                title='选择阿里巴巴订单履约管理表',
                filetypes=[('Excel文件', '*.xlsx *.xls'), ('所有文件', '*.*')]
            )
            if not file_path:
                return
            # 处理数据
            df, summary = calculate_invoice_data(file_path)
            # 选择保存位置并导出
            save_path = filedialog.asksaveasfilename(
                title='保存开票明细',
                defaultextension='.xlsx',
                filetypes=[('Excel文件', '*.xlsx'), ('所有文件', '*.*')]
            )
            if save_path:
                df.to_excel(save_path, index=False, engine='openpyxl')
                # 弹窗展示汇总结果+提醒
                summary_msg = '\n'.join([f'{k}：{v}' for k, v in summary.items()])
                messagebox.showinfo('处理成功！', f'开票明细已导出！\n\n【金额汇总】\n{summary_msg}\n\n提示：异常差额行需手动核对！')
        except Exception as e:
            messagebox.showerror('处理失败', f'错误原因：{str(e)}\n请核对文件后重试！')
    
    # 主操作按钮（醒目易点）
    tk.Button(
        root, text='选择履约Excel文件 → 开始处理',
        command=select_and_process,
        font=('微软雅黑', 12, 'bold'),
        bg='#4CAF50', fg='white',
        width=35, height=2
    ).pack(pady=40)
    
    # 底部提示
    tk.Label(root, text='注：仅支持.xlsx/.xls格式，文件列名需包含"订单金额""已开票金额"', font=('微软雅黑', 8), fg='red').pack()
    
    root.mainloop()

if __name__ == '__main__':
    main()
