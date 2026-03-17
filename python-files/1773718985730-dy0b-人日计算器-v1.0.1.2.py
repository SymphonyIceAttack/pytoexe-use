import math

# --- Data Tables ---
Q_TABLE = [
    {"min": 0, "max": 15, "days": 2.5}, {"min": 16, "max": 25, "days": 3},
    {"min": 26, "max": 45, "days": 4}, {"min": 46, "max": 65, "days": 5},
    {"min": 66, "max": 85, "days": 6}, {"min": 86, "max": 125, "days": 7},
    {"min": 126, "max": 175, "days": 8}, {"min": 176, "max": 275, "days": 9},
    {"min": 276, "max": 425, "days": 10}, {"min": 426, "max": 625, "days": 11},
    {"min": 626, "max": 875, "days": 12}, {"min": 876, "max": 1175, "days": 13},
    {"min": 1176, "max": 1550, "days": 14}, {"min": 1551, "max": 2025, "days": 15},
    {"min": 2026, "max": 2675, "days": 16}, {"min": 2676, "max": 3450, "days": 17},
    {"min": 3451, "max": 4350, "days": 18}, {"min": 4351, "max": 5450, "days": 19},
    {"min": 5451, "max": 6800, "days": 20}, {"min": 6801, "max": 8500, "days": 21},
    {"min": 8501, "max": 10700, "days": 22}
]

ES_TABLE = [
    {"min": 0, "max": 15, "high": 4.5, "medium": 3.5, "low": 3},
    {"min": 16, "max": 25, "high": 5.5, "medium": 4.5, "low": 3.5},
    {"min": 26, "max": 45, "high": 7, "medium": 5.5, "low": 4},
    {"min": 46, "max": 65, "high": 8, "medium": 6, "low": 4.5},
    {"min": 66, "max": 85, "high": 9, "medium": 7, "low": 5},
    {"min": 86, "max": 125, "high": 11, "medium": 8, "low": 5.5},
    {"min": 126, "max": 175, "high": 12, "medium": 9, "low": 6},
    {"min": 176, "max": 275, "high": 13, "medium": 10, "low": 7},
    {"min": 276, "max": 425, "high": 15, "medium": 11, "low": 8},
    {"min": 426, "max": 625, "high": 16, "medium": 12, "low": 9},
    {"min": 626, "max": 875, "high": 17, "medium": 13, "low": 10},
    {"min": 876, "max": 1175, "high": 19, "medium": 15, "low": 11},
    {"min": 1176, "max": 1550, "high": 20, "medium": 16, "low": 12},
    {"min": 1551, "max": 2025, "high": 21, "medium": 17, "low": 12},
    {"min": 2026, "max": 2675, "high": 23, "medium": 18, "low": 13},
    {"min": 2676, "max": 3450, "high": 25, "medium": 19, "low": 14},
    {"min": 3451, "max": 4350, "high": 27, "medium": 20, "low": 15},
    {"min": 4351, "max": 5450, "high": 28, "medium": 21, "low": 16},
    {"min": 5451, "max": 6800, "high": 30, "medium": 23, "low": 17},
    {"min": 6801, "max": 8500, "high": 32, "medium": 25, "low": 19},
    {"min": 8501, "max": 10700, "high": 34, "medium": 27, "low": 20}
]

# --- Helper Functions ---

def get_base_days(employee_count, system, risk_level):
    """Looks up the base man-days from the tables."""
    table = Q_TABLE if system == 'Q' else ES_TABLE
    for row in table:
        if row['min'] <= employee_count <= row['max']:
            if system == 'Q':
                return row['days']
            else:
                return row[risk_level]
    return 0

def final_round(days):
    """Applies the custom rounding rule."""
    if days == 0:
        return 0
    integer_part = math.floor(days)
    decimal_part = days - integer_part
    if decimal_part >= 0.75:
        return integer_part + 1.0
    elif decimal_part >= 0.25:
        return integer_part + 0.5
    else:
        return integer_part + 0.0

def get_user_input(prompt, valid_options):
    """Generic function to get validated user input."""
    while True:
        try:
            choice = input(prompt)
            if choice in valid_options:
                return choice
            else:
                print(f"输入无效，请输入以下选项之一: {', '.join(valid_options)}")
        except ValueError:
            print("输入无效，请输入一个有效的选项。")

# --- Main Calculation Logic ---

def calculate():
    """Main function to gather inputs and perform calculation."""
    calculation_steps = []

    # 1. Get Company
    company_choice = get_user_input("请选择认证公司 (1: 中鼎, 2: 中衡, 3: 通标): ", ['1', '2', '3'])
    company_map = {'1': '中鼎', '2': '中衡', '3': '通标'}
    company = company_map[company_choice]

    # 2. Get Systems
    while True:
        systems_input = input("请输入审核体系 (例如: QES, QE, S): ").upper()
        if systems_input and all(s in 'QES' for s in systems_input):
            systems = sorted(list(set(systems_input))) # Remove duplicates and sort
            break
        else:
            print("输入无效，请只包含 Q, E, S。")
    is_multi_system = len(systems) > 1

    # 3. Get Risk Levels
    risk_levels = {}
    risk_map = {'1': 'high', '2': 'medium', '3': 'low'}
    risk_text_map = {'high': '高风险', 'medium': '中风险', 'low': '低风险'}
    for s in systems:
        if s in 'ES':
            prompt = f"请选择体系 {s} 的风险等级 (1: 高, 2: 中, 3: 低): "
            risk_choice = get_user_input(prompt, ['1', '2', '3'])
            risk_levels[s] = risk_map[risk_choice]

    # 4. Get Site Info
    sites = []
    while True:
        try:
            hq_employees = int(input("请输入总部有效人数: "))
            if hq_employees > 0:
                sites.append({"name": "总部", "employees": hq_employees})
                break
            else:
                print("人数必须为正数。")
        except ValueError:
            print("输入无效，请输入一个数字。")
            
    while True:
        try:
            num_sub_sites = int(input("请输入其他多场所数量 (0-10): "))
            if 0 <= num_sub_sites <= 10:
                break
            else:
                print("数量必须在0到10之间。")
        except ValueError:
            print("输入无效，请输入一个数字。")

    for i in range(num_sub_sites):
        while True:
            try:
                sub_site_employees = int(input(f"请输入多场所 {i+1} 的有效人数: "))
                if sub_site_employees > 0:
                    sites.append({"name": f"多场所{i+1}", "employees": sub_site_employees})
                    break
                else:
                    print("人数必须为正数。")
            except ValueError:
                print("输入无效，请输入一个数字。")

    # 5. Get Audit Type
    audit_type_choice = get_user_input("请选择审核类型 (1: 初审, 2: 监督, 3: 再认证): ", ['1', '2', '3'])
    audit_type_map = {'1': '初审', '2': '监督', '3': '再认证'}
    audit_type = audit_type_map[audit_type_choice]

    # --- Perform Calculation ---
    doc_review_factor = 0.8
    total_site_days = 0

    for site in sites:
        site_base_days = 0
        site_base_days_str = []
        
        for s in systems:
            risk = risk_levels.get(s, None)
            base_days = get_base_days(site['employees'], s, risk)
            
            day_str = str(base_days)
            # Zhongding high risk rule
            if company == '中鼎' and s in 'ES' and risk == 'high':
                base_days *= 1.1
                base_days = round(base_days, 2)
                day_str += "*1.1"

            site_base_days += base_days
            site_base_days_str.append(day_str)
        
        site_base_days = round(site_base_days, 2)
        base_days_calc_str = f"{site['name']}: {' + '.join(site_base_days_str)} = {site_base_days}"
        
        site_result = 0
        if site['name'] == '总部':
            # Main site calculation
            reduction_factor = 0.75 if company == '中鼎' else (0.7 if company == '中衡' else 1.0)
            site_result = site_base_days * doc_review_factor
            if reduction_factor != 1.0:
                 site_result *= reduction_factor
            
            factor_str = f"*{doc_review_factor}"
            if reduction_factor != 1.0:
                factor_str += f"*{reduction_factor}"
            calculation_steps.append(f"{base_days_calc_str} {factor_str} = {round(site_result, 2)}")

        else:
            # Sub-site calculation
            multi_site_factor = 0.5
            site_result = site_base_days * doc_review_factor * multi_site_factor
            calculation_steps.append(f"{base_days_calc_str} *{doc_review_factor}*{multi_site_factor} = {round(site_result, 2)}")
        
        total_site_days += site_result

    total_site_days = round(total_site_days, 2)
    
    # Integration discount
    final_days = total_site_days
    if is_multi_system:
        if company == '中鼎': integration_factor = 0.8
        elif company == '中衡': integration_factor = 0.8
        else: integration_factor = 0.82
        
        final_days *= integration_factor
        calculation_steps.append(f"合计: ({' + '.join([step.split('=')[-1].strip() for step in calculation_steps if '多场所' in step or '总部' in step])}) * {integration_factor} = {round(final_days, 2)}")

    # Apply minimums for first audit
    if audit_type == '初审':
        if is_multi_system and final_days < 1.5:
            final_days = 1.5
            calculation_steps.append(f"应用多体系最低人日: 1.5")
        elif not is_multi_system and final_days < 1.0:
            final_days = 1.0
            calculation_steps.append(f"应用单体系最低人日: 1.0")
    
    # Adjust for Surveillance or Recertification
    if audit_type == '监督':
        final_days /= 3
        calculation_steps.append(f"监督审核: {round(final_days*3, 2)} * 1/3 = {round(final_days, 2)}")
    elif audit_type == '再认证':
        final_days *= (2/3)
        calculation_steps.append(f"再认证审核: {round(final_days/(2/3), 2)} * 2/3 = {round(final_days, 2)}")

    # Final rounding
    rounded_days = final_round(final_days)

    # --- Display Results ---
    print("\n--- 计算过程 ---")
    for step in calculation_steps:
        print(step)
    print("\n--- 最终结果 ---")
    print(f"最低审核人日: {rounded_days} 人日")


if __name__ == "__main__":
    while True:
        calculate()
        print("-" * 20)
        again = input("是否进行下一次计算? (1: 是, 其他任意键: 否): ")
        if again != '1':
            break