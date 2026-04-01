import requests
from urllib.parse import quote
import re
import json
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime
import csv
from threading import Lock

# ===================== 日志配置 =====================
def setup_logger():
    log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d')}.log")
    
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

setup_logger()
# ====================================================

# 全局锁：保证多线程写入CSV不混乱
CSV_LOCK = Lock()
CSV_HEADER_WRITTEN = False  # 新增：标记表头是否已写
# ===================== 号码格式化工具（核心新增） =====================
def clean_phone(phone_str):
    """
    清洗任何格式的号码，返回纯数字
    例如：(615) 707-8616 → 6157078616
    例如：615-707-8616   → 6157078616
    """
    if not phone_str:
        return ""
    return re.sub(r"[^0-9]", "", phone_str)
# ====================================================================

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
    return True, "该用户手机号码符合条件", match.group(1).strip().strip("Wireless").strip(), href_list

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
        
        age = match.group(1).strip()
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
        if not res.get("telephone", "").strip():
            logging.info("潜在客户未找到电话号码，已忽略该用户")
            return {}
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

# ===================== 流式写入CSV（核心改造） =====================
def write_csv_row(csv_filepath, row_data):
    global CSV_HEADER_WRITTEN
    with CSV_LOCK:
        file_exists = os.path.exists(csv_filepath)
        with open(csv_filepath, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "号码", "姓名", "性别", "年龄", "号码类型", "地址", "来源"
            ])
            
            # 只在【文件不存在】或【从未写过表头】时写入
            if not file_exists or not CSV_HEADER_WRITTEN:
                writer.writeheader()
                CSV_HEADER_WRITTEN = True  # 标记已写
            row_data["号码"] = "\t" + str(row_data["号码"])
            row_data["来源"] = "\t" + str(row_data["来源"])
            writer.writerow(row_data)
# =================================================================

def crawler(original_phone, config, current_dir):
    logging.info(f"\n===== 开始处理手机号：{original_phone} =====")
    target = quote(f"https://www.peoplesearchnow.com/phone/{original_phone}")
    html = get_base_html(config["token"], target)

    if not html:
        logging.info("获取主页失败，跳过")
        return

    status, msg, user_info = check_age(html)
    if not status:
        logging.info(f"不符合条件，原因：{msg}")
        return

    logging.info(f"获取用户 {user_info['姓名']} 性别")
    user_info["性别"] = judge_sex(config["genderapi_key"], user_info["姓名"])
    logging.info(f"开始爬取 {user_info['姓名']} 的详情页面")
    target = quote(f"https://www.peoplesearchnow.com{user_info['详情']}")
    html = get_base_html(config["token"], target)

    if not html:
        logging.info("获取详情失败")
        return

    status, msg, phone_number, href_list = get_detail_info(html)
    if not status:
        logging.info(f"不符合条件，原因：{msg}")
        return

    user_info["手机号码"] = phone_number

    # ===================== 写入【普通用户】到CSV =====================
    csv_path = os.path.join(current_dir, "结果.csv")
    user_row = {
        "号码": clean_phone(user_info["手机号码"]),  # 清洗为纯数字
        "姓名": user_info["姓名"],
        "性别": user_info["性别"],
        "年龄": user_info["年龄"],
        "号码类型": "Wireless",
        "地址": user_info["地址"],
        "来源": clean_phone(original_phone)         # 清洗为纯数字
    }
    write_csv_row(csv_path, user_row)
    logging.info(f"已写入主用户信息：{user_info['姓名']}")
    # ================================================================

    logging.info(f"开始爬取 {user_info['姓名']} 的潜在客户页面")
    for href in href_list:
        target = quote(f"https://www.peoplesearchnow.com{href}")
        html = get_base_html(config["token"], target)

        if not html:
            logging.info("获取潜在客户失败，跳过")
            continue

        associates_info = get_associates_info(html)
        if associates_info:
            associates_info["性别"] = judge_sex(config["genderapi_key"], associates_info["姓名"])
            
            # ===================== 写入【潜在客户】到CSV =====================
            associate_row = {
                "号码": clean_phone(associates_info["手机号码"]),  # 纯数字
                "姓名": associates_info["姓名"],
                "性别": associates_info["性别"],
                "年龄": associates_info["年龄"],
                "号码类型": "Wireless",
                "地址": associates_info["地址"],
                "来源": clean_phone(original_phone)                # 纯数字
            }
            write_csv_row(csv_path, associate_row)
            logging.info(f"已写入潜在客户：{associates_info['姓名']}")
            # ================================================================

    logging.info(f"号码 {original_phone} 处理完成！")

def main():
    # ===================== 新增：启动指令功能 =====================
    print("请输入指令start，按回车运行...")
    while True:
        user_input = input(">>> ").strip().lower()
        if user_input == "start":
            print("程序开始运行...\n")
            break
        else:
            print("指令错误，请输入 start 后按回车继续！")
    # ==============================================================

    config={
        "token": "",
        "genderapi_key": "",
        "thread_num": ""
    }
    with open("config.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "TOKEN":
                    config["token"] = value
                elif key == "GENDER_API_KEY":
                    config["genderapi_key"] = value
                elif key == "THREAD_NUM":
                    config["thread_num"] = int(value)

    now_path = os.path.dirname(os.path.realpath(__file__))
    current_dir = os.path.join(now_path, "csv")
    if not os.path.exists(current_dir):
        os.makedirs(current_dir)

    pool = ThreadPoolExecutor(max_workers=config["thread_num"])
    with open(os.path.join(now_path,"import_phone", "import_phone.txt"), "r") as f:
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
    logging.info("===== 全部任务完成 =====")

if __name__ == "__main__":
    main()