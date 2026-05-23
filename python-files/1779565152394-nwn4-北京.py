import requests
import hashlib
import base64
import json
import time
import os
import urllib3
import random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from PIL import Image

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

USER_LIST = [
    "账号",
    "账号",
    "账号",
    "账号",
    "账号"
]
PASSWORD = "密码"
CAPTCHA_API = "https://api.vitphp.cn/Yzcode/"
SAVE_FOLDER = "北京"

# 每日上限关键词
DAILY_LIMIT_KEYWORD = "当前用户已达到每日绑定代办人次数上限,请择日再试"

# ====================== 工具函数 ======================
def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def rsa_encrypt(data, pub_key_str) -> str:
    if isinstance(data, dict):
        json_str = json.dumps(data, separators=(',', ':'))
        message = json_str.encode('utf-8')
    else:
        message = str(data).encode('utf-8')

    if '-----BEGIN PUBLIC KEY-----' not in pub_key_str:
        clean_key = pub_key_str.replace(' ', '').replace('\n', '').replace('\r', '')
        key_lines = [clean_key[i:i + 64] for i in range(0, len(clean_key), 64)]
        pem_key = '-----BEGIN PUBLIC KEY-----\n'
        pem_key += '\n'.join(key_lines)
        pem_key += '\n-----END PUBLIC KEY-----'
    else:
        pem_key = pub_key_str

    key = RSA.import_key(pem_key)
    cipher = PKCS1_v1_5.new(key)
    chunk_size = 117
    encrypted_chunks = []
    for i in range(0, len(message), chunk_size):
        chunk = message[i:i + chunk_size]
        encrypted_chunks.append(cipher.encrypt(chunk))
    return base64.b64encode(b''.join(encrypted_chunks)).decode('utf-8')

def recognize_captcha(image_data):
    try:
        if isinstance(image_data, bytes):
            img_base64 = base64.b64encode(image_data).decode('utf-8')
            img_data = f"data:image/jpeg;base64,{img_base64}"
        else:
            img_data = image_data
        response = requests.get(CAPTCHA_API, params={"img": img_data}, timeout=10,
                                proxies={'http': None, 'https': None}, verify=False)
        data = response.json()
        if data.get("code") == 1:
            return data.get("captcha")
        return None
    except Exception as e:
        print(f"验证码识别异常: {e}")
        return None

# ====================== 登录获取Token ======================
def login_get_token(username, password):
    session = requests.Session()
    session.proxies = {'http': None, 'https': None}
    session.trust_env = False
    session.verify = False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    url = "https://bjt.beijing.gov.cn/renzheng/open/login/goUserLogin"
    params = {
        'client_id': '100100000520',
        'redirect_uri': 'http://fuwu.rsj.beijing.gov.cn/bjdkhy/sso/bjt',
        'response_type': 'code',
        'scope': 'user_info',
        'state': 'https://fuwu.rsj.beijing.gov.cn/bjdkhy/ggfwwt/shbzk'
    }
    session.get(url, params=params, headers=headers)

    url = "https://bjt.beijing.gov.cn/renzheng/inner/client/getClientInfo"
    resp = session.get(url, params={'r': str(int(time.time() * 1000))}, headers=headers)
    pub_key = resp.json().get('data', {}).get('pubKey')
    if not pub_key:
        print("获取公钥失败")
        return None

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        resp = session.get("https://bjt.beijing.gov.cn/renzheng/common/generateCaptcha",
                           params={'r': str(int(time.time() * 1000))}, headers=headers)
        captcha = recognize_captcha(resp.content)
        if not captcha:
            print(f"验证码识别失败,重试 {attempt}/{max_retries}")
            time.sleep(0.5)
            continue

        encrypted_pwd = md5_hash(password)
        login_obj = {"userIdentity": username, "encryptedPwd": encrypted_pwd}
        encrypt_data = rsa_encrypt(login_obj, pub_key)

        url = "https://bjt.beijing.gov.cn/renzheng/inner/login/doUserLoginByPwd"
        data = {'encryptData': encrypt_data, 'captcha': captcha}
        resp = session.post(url, data=data, headers=headers)
        result = resp.json()

        if result.get('meta', {}).get('code') == '0':
            print(f"[{username}] 登录成功")
            break
        else:
            msg = result.get('meta', {}).get('message', '登录失败')
            print(f"[{username}] {msg}")

            # 识别每日上限
            if DAILY_LIMIT_KEYWORD in msg:
                return "limit"

            print(f"重试 {attempt}/{max_retries}")
            time.sleep(1)
    else:
        print(f"[{username}] 登录失败")
        return None

    url = "https://bjt.beijing.gov.cn/renzheng/inner/info/getRedirectUri"
    data = {
        'clientId': '100100000520',
        'state': 'https://fuwu.rsj.beijing.gov.cn/bjdkhy/ggfwwt/shbzk',
        'bizType': 'login',
        'authCode': 'login'
    }
    resp = session.post(url, data=data, headers=headers)
    home_page_url = resp.json().get('data', {}).get('homePageUrl')
    if not home_page_url:
        return None

    import urllib.parse
    code = urllib.parse.parse_qs(urllib.parse.urlparse(home_page_url).query).get('code', [None])[0]

    sso_url = "https://fuwu.rsj.beijing.gov.cn/bjdkhy/sso/bjt"
    session.get(sso_url, params={'code': code, 'state': 'https://fuwu.rsj.beijing.gov.cn/bjdkhy/ggfwwt/shbzk'}, headers=headers)
    session.get("https://fuwu.rsj.beijing.gov.cn/zhrs/sso/bjt", params={'code': code}, headers=headers)

    url = "https://fuwu.rsj.beijing.gov.cn/zhrs/api4/api/auth/common/login"
    data = {'type': 'code', 'key1': code, 'key2': ''}
    resp = requests.post(url, data=data, headers=headers, verify=False)
    result = resp.json()
    if result.get('appcode') != '0':
        return None

    return result.get('map', {}).get('Access-Token')
    
def combine_images(image1_path, image2_path, output_path):
    try:
        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)
        max_width = max(image1.width, image2.width)
        image1 = image1.resize((max_width, int(image1.height * max_width / image1.width)))
        image2 = image2.resize((max_width, int(image2.height * max_width / image2.width)))
        combined = Image.new('RGB', (max_width, image1.height + image2.height))
        combined.paste(image1, (0, 0))
        combined.paste(image2, (0, image1.height))
        combined.save(output_path, 'JPEG', quality=95)
        return True
    except Exception as e:
        print(f"合成失败: {e}")
        return False

def get_license(name, card_no, token):
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    url = "https://fuwu.rsj.beijing.gov.cn/bjdkhy/api3/api/ggfw-server-msk/personapply/electronicLicenseQueryLimit"
    headers = {
        "Access-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://fuwu.rsj.beijing.gov.cn/bjdkhy/ggfwwt/Personal/CardByAgent"
    }
    data = {"cardNo": card_no, "name": name}

    try:
        res = requests.post(url, headers=headers, json=data, verify=False, timeout=15)
        res.raise_for_status()
        j = res.json()
        msg = j.get('msg', '')

        # 识别每日上限
        if DAILY_LIMIT_KEYWORD in msg:
            print(f"❌ 接口返回:{msg}")
            return "limit"

        if j.get("appcode") != "0":
            print(f"失败: {msg}")
            return False

        front = j["map"].get("frontBase64", "")
        back = j["map"].get("backBase64", "")
        if not front or not back:
            print("未返回证照图片")
            return False

        tmp_f = os.path.join(SAVE_FOLDER, f"tmp_f_{card_no}.jpg")
        tmp_b = os.path.join(SAVE_FOLDER, f"tmp_b_{card_no}.jpg")
        with open(tmp_f, 'wb') as f:
            f.write(base64.b64decode(front))
        with open(tmp_b, 'wb') as f:
            f.write(base64.b64decode(back))

        out = os.path.join(SAVE_FOLDER, f"{name}_{card_no}.jpg")
        ok = combine_images(tmp_f, tmp_b, out)
        os.remove(tmp_f)
        os.remove(tmp_b)
        if ok:
            print(f"✅ 证照已保存: {out}")
        return ok
    except Exception as e:
        print(f"异常: {e}")
        return False

# ====================== 主程序:随机选号 + 上限自动换号 ======================
if __name__ == "__main__":
    print("===== 北京电子证照查询工具(随机选号 + 上限自动换号)=====")
    print("逻辑:随机登录账号 → 出现每日上限自动换号\n")

    # 可用账号池(会动态移除上限号)
    available_users = USER_LIST.copy()

    while True:
        print("\n请输入查询信息(输入 q 退出)")
        name = input("姓名: ").strip()
        if name.lower() == 'q':
            break
        card = input("身份证号: ").strip()
        if card.lower() == 'q':
            break

        if not name or not card:
            print("❌ 姓名或身份证不能为空")
            continue

        # 循环换号直到成功 or 无号可用
        success = False
        while not success:
            if not available_users:
                print("❌ 所有账号均已达到每日上限,无法继续查询")
                break

            # 随机选一个账号
            user = random.choice(available_users)
            print(f"\n随机选中账号: {user}")

            # 登录
            token = login_get_token(user, PASSWORD)

            # 登录就提示上限
            if token == "limit":
                print(f"❌ 账号 {user} 已达每日上限,移出可用列表")
                available_users.remove(user)
                continue

            # 登录失败
            if not token:
                print(f"❌ 账号 {user} 登录失败,换号重试")
                continue

            # 开始查询
            print(f"\n正在查询: {name} {card}")
            res = get_license(name, card, token)

            if res == "limit":
                # 查询返回上限,标记账号失效
                print(f"❌ 账号 {user} 已达每日上限,移出可用列表")
                available_users.remove(user)
            elif res:
                success = True
            else:
                print("查询失败,继续换号尝试")

    print("\n程序结束")
