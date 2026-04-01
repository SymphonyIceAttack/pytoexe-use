import requests
from urllib.parse import quote
import re
import json
from bs4 import BeautifulSoup
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

# ===================== 日志配置 =====================
def setup_logger():
    # 创建log文件夹
    log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志文件名：按日期生成
    log_file = os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 日志格式
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置根日志
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 文件输出
            logging.FileHandler(log_file, encoding='utf-8'),
            # 控制台输出
            logging.StreamHandler()
        ]
    )

# 初始化日志
setup_logger()
# ====================================================

def get_base_html(token, target):
    url = f"https://api.scrape.do/?token={token}&url={target}"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logging.error(f"请求代理服务失败：{e}")
        return ""

def check_age(data):
    user_info = {}
    if not data:
        return False, "数据为空", user_info

    pattern = r'''<span>Approximate Age:</span>.*<span> (\d+)</span>'''
    match = re.search(pattern, data, re.DOTALL)
    if not match:
        logging.info("未找到年龄信息")
        return False, "未找到年龄信息", user_info

    age = 40
    if int(match.group(1)) < age:
        logging.info(f"年龄小于{age}岁")
        return False, f"年龄小于{age}岁", user_info

    user_info["年龄"] = match.group(1)

    pattern = r'<script type="application/ld\+json">([\s\S]*?)</script>'
    match = re.findall(pattern, data)
    res = json.loads(match[1])

    user_info["姓名"] = res["name"]
    user_info["地址"] = res["address"]

    pattern = r'''href="(/name/[^"]+)"'''
    match = re.search(pattern, data, re.DOTALL)
    if not match:
        return False, "未找到详情链接", user_info

    user_info["详情"] = match.group(1)
    return True, "年龄符合条件", user_info

def get_detail_info(data):
    if not data:
        return False, "数据为空", "", []

    pattern = r'<span[^>]*itemprop="telephone"[^>]*>(.*?)</span>'
    match = re.search(pattern, data, re.DOTALL)
    if not match:
        logging.info("未找到电话号码")
        return False, "未找到电话号码", "", []

    if "Wireless" not in match.group(1):
        logging.info("不是无线号码")
        return False, "不是无线号码", "", []

    soup = BeautifulSoup(data, 'lxml')
    target_p = soup.find('p', string='Possible Associates:')
    if not target_p:
        return False, "未找到关联信息", "", []

    target_div = target_p.find_next_sibling('div', class_='result-full-info-content')
    href_list = []
    for a_tag in target_div.find_all('a'):
        href = a_tag.get('href')
        href_list.append(href)
    return True, "该用户手机号码符合条件", match.group(1), href_list

def get_associates_info(data):
    try:
        if not data:
            return {}
        
        pattern = r'Approximate Age:\s*<span>(\d+)</span>'
        match = re.search(pattern, data)
        age = ""
        if not match:
            logging.info("潜在客户未找到年龄信息，已忽略该用户")
            return {}
        if match:
            age = match.group(1).strip()
            # 修复原代码错误：age() 改为 int(age)
            if int(age) < 40:
                logging.info("潜在客户年龄小于40岁，已忽略该用户")
                return {}
        address = ""
        pattern = r'''Current Address:.*?<span>(.*?)</span>'''
        match = re.search(pattern, data, re.DOTALL)
        if match:
            address = match.group(1).strip()

        pattern = r'<script type="application/ld\+json">([\s\S]*?)</script>'
        match = re.findall(pattern, data)
        res = json.loads(match[1])
        return {
            "姓名": res["name"],
            "年龄": age,
            "手机号码": res.get("telephone", ""),
            "地址": address
        }
    except:
        return {}

def judge_sex(key,name):
    try:
        payload = {
            "name": name,
            "key": key
        }
        u = f"https://api.genderapi.io/api"
        res = requests.post(u, json=payload, timeout=10)
        res_json = json.loads(res.text)
        return res_json["gender"]
    except:
        return "未知"

def crawler(phone,config,current_dir):
    logging.info(f"\n===== 开始处理手机号：{phone} =====")
    target = quote(f"https://www.peoplesearchnow.com/phone/{phone}")
    html = get_base_html(config["scrape_key"], target)

    if not html:
        logging.info("获取主页失败，跳过")
        return

    status, msg, user_info = check_age(html)
    if not status:
        logging.info(f"不符合条件，原因：{msg}")
        return

    logging.info(f"获取用户 {user_info['姓名']} 性别")
    user_info["性别"] = judge_sex(config["genderapi_key"],user_info["姓名"])

    logging.info(f"开始爬取 {user_info['姓名']} 的详情页面")
    target = quote(f"https://www.peoplesearchnow.com{user_info['详情']}")
    html = get_base_html(config["scrape_key"], target)

    if not html:
        logging.info("获取详情失败")
        return

    status, msg, phone_number, href_list = get_detail_info(html)
    if not status:
        logging.info(f"不符合条件，原因：{msg}")
        return

    user_info["手机号码"] = phone_number

    logging.info(f"开始爬取 {user_info['姓名']} 的潜在客户页面")
    associates_infos = []
    for href in href_list:
        target = quote(f"https://www.peoplesearchnow.com{href}")
        html = get_base_html(config["scrape_key"], target)

        if not html:
            logging.info("获取潜在客户页面失败，跳过")
            continue

        associates_info = get_associates_info(html)
        if associates_info:
            logging.info(f"潜在客户信息 {associates_info['姓名']} 爬取完成")
            associates_info["性别"] = judge_sex(config["genderapi_key"],associates_info["姓名"])
            associates_infos.append(associates_info)

    excel_path = os.path.join(current_dir, f"{phone}.xlsx")
    logging.info(f"正在保存 Excel：{excel_path}")

    user_cols = ["姓名", "年龄", "性别", "手机号码", "地址"]
    ass_cols = ["姓名", "年龄", "性别", "手机号码", "地址"]

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        user_df = pd.DataFrame([user_info])
        user_df = user_df.reindex(columns=user_cols)
        user_df.to_excel(writer, sheet_name="用户信息", index=False)

        ass_df = pd.DataFrame(associates_infos)
        ass_df = ass_df.reindex(columns=ass_cols)
        ass_df.to_excel(writer, sheet_name="潜在客户信息", index=False)

    logging.info("保存完成！")

def main():
    with open("config.json", "r") as f:
        config = json.load(f)
    now_path=os.path.dirname(os.path.realpath(__file__))
    current_dir = os.path.join(now_path,"爬取数据")
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)
    pool=ThreadPoolExecutor(max_workers=config["thread_num"])
    with open(os.path.join(now_path,"手机号列表.txt"), "r") as f:
        for line in f:
            phone = line.strip()
            if not phone:
                continue
            if len(phone) == 10 and phone.isdigit():
                phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            elif len(phone) == 11 and phone.startswith("1") and phone[1:].isdigit():
                phone = f"{phone[1:4]}-{phone[4:7]}-{phone[7:]}"
            else:
                logging.info(f"手机号格式不正确，跳过：{phone}")
                continue
            pool.submit(crawler, phone, config, current_dir)
        pool.shutdown(wait=True)

if __name__ == "__main__":
    main()