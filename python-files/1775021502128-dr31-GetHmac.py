import base64
import hashlib
import hmac
from datetime import datetime
import pytz
import requests
import json

requests.packages.urllib3.disable_warnings()


def get_gmt():
    """获取GMT时间字符串"""
    gmt_time = datetime.now(pytz.timezone('GMT'))
    return gmt_time.strftime('%a, %d %b %Y %H:%M:%S GMT')


def encoder_by_md5(content):
    """计算内容的MD5并进行base64编码"""
    if isinstance(content, dict):
        content = json.dumps(content, separators=(',', ':'), ensure_ascii=False)
    md5_hash = hashlib.md5(content.encode('utf-8')).digest()
    base64_str = base64.b64encode(md5_hash).decode('utf-8')
    return base64_str


def get_signature(sign_string, key):
    """计算HMAC-SHA1签名"""
    key_bytes = key.encode('utf-8')
    sign_string_bytes = sign_string.encode('utf-8')

    signature = hmac.new(key_bytes, sign_string_bytes, hashlib.sha1).digest()
    return base64.b64encode(signature).decode('utf-8')


def hmac_signature(ak, sk, body):
    """生成认证headers"""
    date = get_gmt()

    # 计算请求体的MD5
    body_md5 = encoder_by_md5(body)

    # 构建签名字符串 - 注意header名称必须小写且与headers参数一致
    sign_string = f'date: {date}\ncontent-md5: {body_md5}'

    # 计算签名
    signature = get_signature(sign_string, sk)

    # 构建Authorization头
    auth = f'hmac accesskey="{ak}", algorithm="hmac-sha1", headers="date content-md5", signature="{signature}"'

    headers = {
        "Date": date,
        "Content-Md5": body_md5,  # 注意大小写，有些服务器要求严格匹配
        "Authorization": auth,
        "Content-Type": "application/json"
    }

    return headers


if __name__ == '__main__':
    #输入自己项目组的AK和SK
    ak = "19b2fffa3c094867"
    sk = "520eefb2ce664a0eae3e63fcbdec01c3"

    # 请求体
    body = {
        'pageSize': '100',
        'pageNum': '1',
    }

    # 生成headers
    headers = hmac_signature(ak, sk, body)

    print("生成的Headers:")
    for k, v in headers.items():
        print(f"  {k}: {v}")
