import re

# ============================================
# 把你的 FastPeopleSearch 原始文本放在这里
data = """（把你的原始文本放在这里）"""
# ============================================

# 设置年龄筛选范围
min_age = 50
max_age = 60

# 匹配每个人的信息
person_pattern = re.compile(
    r"Full Name:\s*(?P<name>.*?)\n.*?Age:\s*(?P<age>\d+).*?(?:Phone:.*?\n)(?P<phones>(?:\([0-9]+\).*?\n)+)",
    re.DOTALL
)

# 匹配 Mobile 电话
mobile_pattern = re.compile(r"\(\d+\)\s*\d+-\d+\s*\(Mobile\)")

results = []
seen = set()  # 去重用

for match in person_pattern.finditer(data):
    name = match.group("name").strip()
    age = int(match.group("age").strip())
    phones_block = match.group("phones")
    
    if min_age <= age <= max_age:
        mobile_matches = mobile_pattern.findall(phones_block)
        first_mobile = mobile_matches[0] if mobile_matches else "No Mobile"
        
        # 去重（名字+号码）
        identifier = f"{name}-{first_mobile}"
        if identifier not in seen:
            seen.add(identifier)
            results.append({"Name": name, "Age": age, "First Mobile": first_mobile})

# 生成 HTML 网页
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Filtered People</title>
<style>
    body {{ font-family: Arial, sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    tr:nth-child(even) {{ background-color: #fafafa; }}
</style>
</head>
<body>
<h2>Filtered People (Age {min_age} - {max_age})</h2>
<table>
<tr><th>Name</th><th>Age</th><th>First Mobile</th></tr>
"""

for r in results:
    html_content += f"<tr><td>{r['Name']}</td><td>{r['Age']}</td><td>{r['First Mobile']}</td></tr>\n"

html_content += """
</table>
</body>
</html>
"""

# 保存 HTML 文件
html_filename = "filtered_people.html"
with open(html_filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"筛选完成！网页已生成：{html_filename}")
