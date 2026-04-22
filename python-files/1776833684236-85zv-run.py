import pandas as pd
from tkinter import Tk, filedialog
from openpyxl.styles import Alignment

root = Tk()
root.withdraw()

print("=== 商户码值一对多关联合并工具 ===")
f1 = filedialog.askopenfilename(title="表格1：A小商户号 B商户号", filetypes=[("Excel", "*.xlsx")])
f2 = filedialog.askopenfilename(title="表格2：A商户号 B码值", filetypes=[("Excel", "*.xlsx")])
save = filedialog.asksaveasfilename(title="保存结果", defaultextension=".xlsx", initialfile="最终合并结果.xlsx")

# 读取+去重+分组换行
df1 = pd.read_excel(f1)
df2 = pd.read_excel(f2).drop_duplicates()
df2_group = df2.groupby("商户号")["码值"].apply(lambda s: "\n".join(s.astype(str))).reset_index()

# 左关联匹配
res = pd.merge(df1, df2_group, on="商户号", how="left")

# 写入Excel+自动换行
with pd.ExcelWriter(save, engine="openpyxl") as w:
    res.to_excel(w, index=False)
    ws = w.sheets["Sheet1"]
    wrap = Alignment(wrap_text=True)
    for cell in ws["C"]:
        cell.alignment = wrap

print("\n✅ 全部处理完成！文件已生成")
input("\n按回车关闭窗口")