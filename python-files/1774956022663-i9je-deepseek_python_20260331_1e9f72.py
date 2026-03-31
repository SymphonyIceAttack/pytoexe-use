"""
多国家真实地址生成器
数据源：RandomUser.me API
支持国家：au, br, ca, ch, de, dk, es, fi, fr, gb, ie, in, ir, mx, nl, no, nz, rs, tr, ua, us 等
"""

import csv
import random
import requests
from typing import List, Dict, Optional

# 可用国家列表（根据 RandomUser API 文档）
AVAILABLE_COUNTRIES = {
    'au': '澳大利亚', 'br': '巴西', 'ca': '加拿大', 'ch': '瑞士', 'de': '德国',
    'dk': '丹麦', 'es': '西班牙', 'fi': '芬兰', 'fr': '法国', 'gb': '英国',
    'ie': '爱尔兰', 'in': '印度', 'ir': '伊朗', 'mx': '墨西哥', 'nl': '荷兰',
    'no': '挪威', 'nz': '新西兰', 'rs': '塞尔维亚', 'tr': '土耳其', 'ua': '乌克兰',
    'us': '美国'
}

def fetch_randomuser_data(count: int = 100, country: Optional[str] = None) -> List[Dict]:
    """
    从 RandomUser API 获取地址数据
    :param count: 获取数量（最多500）
    :param country: 国家代码（如 'us'），None 表示随机国家
    """
    if country and country not in AVAILABLE_COUNTRIES:
        print(f"⚠️ 不支持的国家代码 {country}，将使用随机国家。")
        country = None
    
    nat_param = f"&nat={country}" if country else ""
    url = f"https://randomuser.me/api/?results={count}{nat_param}&inc=name,location,phone"
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"❌ API请求失败: {e}")
        return []

    identities = []
    for user in data.get('results', []):
        first = user['name']['first']
        last = user['name']['last']
        
        street_num = user['location']['street']['number']
        street_name = user['location']['street']['name']
        street = f"{street_num} {street_name}"
        
        city = user['location']['city']
        state = user['location']['state']
        postcode = user['location']['postcode']
        phone = user.get('phone', '')
        
        # 提取区号（仅适用于美国/加拿大等格式，其他国家可能不标准）
        import re
        area_code = ''
        match = re.search(r'\(?(\d{3})\)?', phone)
        if match:
            area_code = match.group(1)
        
        identities.append({
            '姓氏': last,
            '名字': first,
            '账单姓氏': last,
            '账单名字': first,
            '街道地址': street,
            '楼号单元': '',
            '城市': city,
            '邮编': str(postcode),
            '省/市': state,
            '区号': area_code,
            '电话': phone,
            '国家': AVAILABLE_COUNTRIES.get(country, '随机') if country else '随机'  # 可选字段
        })
    
    print(f"✅ 成功获取 {len(identities)} 条地址（国家：{country if country else '随机'}）")
    return identities

def save_to_csv(identities: List[Dict], filename: str = "地址输出.csv"):
    """保存为 CSV 模板，前五列留空"""
    fieldnames = [
        '账号', '密码', '答案1', '答案2', '答案3',
        '姓氏', '名字', '账单姓氏', '账单名字',
        '街道地址', '楼号单元', '城市', '邮编', '省/市', '区号', '电话'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in identities:
            row = {k: '' for k in fieldnames[:5]}
            row.update({k: item.get(k, '') for k in fieldnames[5:]})
            writer.writerow(row)
    
    print(f"💾 已保存到 {filename}")

def main():
    print("=" * 60)
    print("🌍 多国家真实地址生成器")
    print("=" * 60)
    
    # 显示可用国家
    print("\n可用国家代码及对应国家：")
    for code, name in AVAILABLE_COUNTRIES.items():
        print(f"  {code}: {name}")
    
    # 选择国家
    country_input = input("\n请输入国家代码（直接回车则随机选择）: ").strip().lower()
    if country_input and country_input in AVAILABLE_COUNTRIES:
        country = country_input
        print(f"已选择：{AVAILABLE_COUNTRIES[country]}")
    else:
        country = None
        print("将随机选择国家")
    
    # 输入数量
    try:
        count = int(input("请输入生成数量（默认100，最多500）: ") or "100")
        count = min(count, 500)
    except ValueError:
        count = 100
    
    # 获取数据
    identities = fetch_randomuser_data(count, country)
    if identities:
        save_to_csv(identities)
        
        # 预览
        print("\n📋 预览前3条：")
        for i, addr in enumerate(identities[:3], 1):
            print(f"  {i}. {addr['名字']} {addr['姓氏']} | {addr['街道地址']} | {addr['城市']}, {addr['省/市']} {addr['邮编']}")
    else:
        print("❌ 未获取到数据，请检查网络后重试。")

if __name__ == "__main__":
    main()