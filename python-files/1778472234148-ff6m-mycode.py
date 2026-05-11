import sys
import pandas as pd

def main():
    # ---------------------- 配置区 ----------------------
    age_col = "年龄"        # 你的名单里 年龄 列的列名
    phone_col = "电话"      # 你的名单里 电话 列的列名
    # ----------------------------------------------------

    # 检查是否拖入文件
    if len(sys.argv) < 2:
        print("❌ 请把客户名单Excel文件拖到这个程序图标上运行！")
        input("按回车退出...")
        return

    # 读取拖入的文件
    file_path = sys.argv[1]
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"❌ 读取文件失败：{e}")
        input("按回车退出...")
        return

    # 检查必须列是否存在
    if age_col not in df.columns or phone_col not in df.columns:
        print(f"❌ 表格必须包含列：{age_col}、{phone_col}")
        input("按回车退出...")
        return

    # 去掉空行、空年龄
    df = df.dropna(subset=[age_col]).copy()
    df[age_col] = pd.to_numeric(df[age_col], errors="coerce")
    df = df.dropna(subset=[age_col])

    # 规则：最后一个人不写入，电话统一用最后一个电话
    if len(df) < 1:
        print("❌ 名单里没有有效数据")
        return

    # 最后一个人排除
    df_process = df.iloc[:-1].copy()
    # 最后一个电话
    last_phone = df[phone_col].iloc[-1]
    # 所有电话替换为最后一个电话
    df_process[phone_col] = last_phone

    # 分类
    adult_under_60 = df_process[df_process[age_col] < 60]
    age_60_64 = df_process[(df_process[age_col] >= 60) & (df_process[age_col] <= 64)]
    age_65_up = df_process[df_process[age_col] >= 65]

    # 保存文件
    try:
        adult_under_60.to_excel("帕米尔成人票区间车.xls", index=False, engine="xlwt")
        age_60_64.to_excel("帕米尔区间车（60-64）.xlsx", index=False, engine="openpyxl")
        age_65_up.to_excel("帕米尔65以上.xls", index=False, engine="xlwt")

        print("✅ 分类完成！生成以下3个文件：")
        print("1. 帕米尔成人票区间车.xls（60岁以下）")
        print("2. 帕米尔区间车（60-64）.xlsx（60-64岁）")
        print("3. 帕米尔65以上.xls（65岁及以上）")
        print(f"\📞 所有电话统一为：{last_phone}")
        print(f"\👤 已排除最后1人，不写入任何文件")

    except Exception as e:
        print(f"❌ 保存失败：{e}")

    input("\n按回车键退出...")

if __name__ == "__main__":
    main()