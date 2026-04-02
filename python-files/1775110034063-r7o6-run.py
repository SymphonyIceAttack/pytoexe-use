# 纯Python 打卡数据提取（单次打卡默认2小时+空格区间）
from datetime import datetime, timedelta
import re

# ====================== 配置 ======================
INPUT_FILE = "云帆工作室_打卡时间_20260301-20260331.xlsx"  # 你的打卡表文件名
OUTPUT_FILE = "打卡数据_最终版.csv"                          # 输出结果文件名
DATE_HEADER_ROW = 3  # 日期表头在第4行（Python索引0开始）
NAME_START_ROW = 4   # 姓名数据从第5行开始（索引4）
SINGLE_CHECKIN_DURATION = 2.0  # 单次打卡默认上课时长（2小时）
# ==================================================

# 1. 完整读取Excel所有行
def read_excel_complete(file_path):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        full_data = []
        for row in ws.iter_rows(values_only=True):
            full_data.append(list(row))
        print(f"✅ 读取Excel成功：共{len(full_data)}行，{len(full_data[0]) if full_data else 0}列")
        return full_data
    except ImportError:
        print("⚠️  请先安装openpyxl：打开cmd输入 → pip install openpyxl")
        exit()
    except Exception as e:
        print(f"❌ 读取Excel出错：{str(e)}")
        exit()

# 2. 解析日期表头（列索引→标准日期）
def parse_date_headers(header_row_data):
    date_map = {}
    base_year, base_month = 2026, 3  # 固定统计月份
    
    for col_idx, header_val in enumerate(header_row_data):
        if header_val is None:
            continue
        header_str = str(header_val).strip()
        
        # 数字日期（如2、3、4）→ 直接转换
        if header_str.isdigit():
            day = int(header_str)
            if 1 <= day <= 31:
                try:
                    date_obj = datetime(base_year, base_month, day)
                    date_map[col_idx] = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    continue
        
        # 星期日期（如"日"、"六"）→ 推算
        elif header_str in ["日", "一", "二", "三", "四", "五", "六"]:
            for prev_col in range(col_idx - 1, -1, -1):
                if prev_col in date_map:
                    prev_date = datetime.strptime(date_map[prev_col], "%Y-%m-%d")
                    current_date = prev_date + timedelta(days=col_idx - prev_col)
                    if current_date.month == base_month:
                        date_map[col_idx] = current_date.strftime("%Y-%m-%d")
                    break
    return date_map

# 3. 计算上课时长（区分单次/多次打卡）
def calculate_class_duration(valid_times, date_str):
    if len(valid_times) == 1:
        # 单次打卡：默认2小时
        return SINGLE_CHECKIN_DURATION
    else:
        # 多次打卡：按规则折算（接近1/1.5/2小时）
        valid_times_sorted = sorted(valid_times, key=lambda x: datetime.strptime(x, "%H:%M:%S"))
        checkin = valid_times_sorted[0][:5]  # 截取HH:MM
        checkout = valid_times_sorted[-1][:5]
        
        try:
            time_format = "%Y-%m-%d %H:%M"
            checkin_dt = datetime.strptime(f"{date_str} {checkin}", time_format)
            checkout_dt = datetime.strptime(f"{date_str} {checkout}", time_format)
            
            actual_duration = (checkout_dt - checkin_dt).total_seconds() / 3600
            
            # 误差±15分钟（0.25小时）内折算
            target_rules = [(1.0, 0.25), (1.5, 0.25), (2.0, 0.25)]
            for target, tolerance in target_rules:
                if abs(actual_duration - target) <= tolerance:
                    return target
            
            # 不在规则内则返回实际时长（保留1位小数）
            return round(actual_duration, 1)
        except:
            return 0.0

# 4. 提取数据+生成空格区间
def extract_attendance_final(full_data):
    all_attendance = []
    
    # 解析日期表头
    if len(full_data) <= DATE_HEADER_ROW:
        print("❌ 表格缺少日期表头行")
        return all_attendance
    date_map = parse_date_headers(full_data[DATE_HEADER_ROW])
    if not date_map:
        print("❌ 未解析到任何日期")
        return all_attendance
    
    # 处理所有人员数据行
    data_rows = full_data[NAME_START_ROW:]
    if not data_rows:
        print("❌ 未找到打卡数据行")
        return all_attendance
    
    # 逐行提取每个人的打卡记录
    for row_idx, row_data in enumerate(data_rows, start=NAME_START_ROW + 1):
        # 提取姓名（第1列）
        name = row_data[0] if (row_data and row_data[0] is not None) else f"未知人员_{row_idx}"
        name = str(name).strip() or f"未知人员_{row_idx}"
        
        # 逐列处理每个日期的打卡时间
        for col_idx, date_str in date_map.items():
            # 确保列索引在当前行范围内（避免列数不足）
            if col_idx >= len(row_data):
                continue
            
            time_val = row_data[col_idx]
            if time_val is None:
                continue
            
            time_str = str(time_val).strip()
            if not time_str:
                continue
            
            # 筛选有效时间（格式：HH:MM → 补全为HH:MM:SS）
            valid_times = []
            for t in re.split(r"\n|\r|\s+", time_str):
                t_clean = t.strip()
                if re.match(r"^\d{2}:\d{2}$", t_clean):
                    valid_times.append(f"{t_clean}:00")  # 统一格式为HH:MM:SS
            
            if not valid_times:
                continue
            
            # 生成时间区间（单次打卡后半段留空格）
            if len(valid_times) == 1:
                # 单次打卡：格式 "HH:MM:SS- "（-后加空格）
                duration_range = f"{valid_times[0]}- "
            else:
                # 多次打卡：格式 "最早时间-最晚时间"
                valid_times_sorted = sorted(valid_times, key=lambda x: datetime.strptime(x, "%H:%M:%S"))
                duration_range = f"{valid_times_sorted[0]}-{valid_times_sorted[-1]}"
            
            # 计算上课时长（单次默认2小时，多次按规则）
            class_duration = calculate_class_duration(valid_times, date_str)
            
            # 每条日期生成1条记录（去重）
            all_attendance.append([
                name,
                date_str,
                duration_range,  # 打卡时长（空格区间）
                class_duration   # 上课时长（单次默认2小时）
            ])
    
    print(f"✅ 共提取到{len(all_attendance)}条打卡记录（涵盖{len(data_rows)}行人员）")
    return all_attendance

# 5. 保存最终结果
def save_final_result(data, output_file):
    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        # 表头：姓名、打卡日期、打卡时长、上课时长（小时）
        f.write("姓名,打卡日期,打卡时长,上课时长（小时）\n")
        for row in data:
            f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")

# 主程序：一键运行
if __name__ == "__main__":
    print("=" * 60)
    print("1/4 正在读取Excel所有数据...")
    full_excel_data = read_excel_complete(INPUT_FILE)
    
    print("2/4 正在解析日期表头...")
    _ = parse_date_headers(full_excel_data[DATE_HEADER_ROW]) if len(full_excel_data) > DATE_HEADER_ROW else None
    
    print("3/4 正在提取打卡数据+计算时长...")
    final_result = extract_attendance_final(full_excel_data)
    
    if final_result:
        print("4/4 正在保存最终结果...")
        save_final_result(final_result, OUTPUT_FILE)
        print("=" * 60)
        print(f"🎉 处理完成！")
        print(f"📊 统计：共{len(final_result)}条有效打卡记录")
        print(f"📁 结果文件：{OUTPUT_FILE}")
        print("\n【结果预览（前5条）】")
        print(f"{'姓名':<8}{'打卡日期':<12}{'打卡时长':<22}{'上课时长（小时）':<10}")
        print("-" * 60)
        for i, row in enumerate(final_result[:5]):
            print(f"{row[0]:<8}{row[1]:<12}{row[2]:<22}{row[3]:<10}")
        if len(final_result) > 5:
            print(f"... 还有{len(final_result)-5}条记录未显示")
    else:
        print("=" * 60)
        print("❌ 未提取到任何有效打卡数据")