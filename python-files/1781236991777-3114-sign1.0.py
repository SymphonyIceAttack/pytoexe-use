import hashlib
import time
import random
import uuid
from urllib.parse import urlparse, parse_qs, urlencode, unquote
from datetime import timedelta


def sign_url(origin_url: str, private_key: str, uid: int, valid_duration: timedelta) -> str:
    """
    123云盘直链URL鉴权签名函数（修复鉴权失败问题）

    参数:
        origin_url: 待签名的原始直链URL（从123云盘直链空间复制）
        private_key: 123云盘直链管理中设置的鉴权密钥
        uid: 123云盘个人中心的账号ID（数字）
        valid_duration: 链接有效期（timedelta对象）

    返回:
        签名后的带鉴权URL
    """
    try:
        # 1. 计算有效期时间戳（未来时间，10位Unix秒级）
        ts = int(time.time() + valid_duration.total_seconds())
        # 校验时间戳是否为未来时间（避免有效期设置错误）
        if ts < int(time.time()):
            raise ValueError("有效期设置错误，时间戳需为未来时间")

        # 2. 生成随机字符串（平台推荐UUID无中划线，兼容性更好）
        rand_str = uuid.uuid4().hex  # 32位随机字符串，替代整数更稳定

        # 3. 解析并解码URL路径（关键修复点：必须用解码后的原始路径签名）
        parsed_url = urlparse(origin_url)
        # 解码路径：将%XX还原为中文/原始字符（比如%E7%9B%B4%E9%93%BE → 直链）
        path = unquote(parsed_url.path)

        # 4. 构造待签名字符串（严格按平台格式：路径-时间戳-随机串-UID-密钥）
        sign_raw = f"{path}-{ts}-{rand_str}-{uid}-{private_key}"
        # 5. 计算MD5（小写32位，编码必须为utf-8）
        md5_result = hashlib.md5(sign_raw.encode("utf-8")).hexdigest()

        # 6. 构造auth_key参数（格式：时间戳-随机串-UID-MD5）
        auth_key = f"{ts}-{rand_str}-{uid}-{md5_result}"

        # 7. 拼接最终URL（保留原参数，追加auth_key）
        query_params = parse_qs(parsed_url.query)
        query_params["auth_key"] = [auth_key]  # 覆盖/添加auth_key参数
        new_query = urlencode(query_params, doseq=True)
        # 重新拼接URL（确保路径用编码后的，仅签名时用解码后的）
        new_url = parsed_url._replace(query=new_query).geturl()

        # 调试信息（可选，帮助核对签名参数）
        print("===== 签名调试信息 =====")
        print(f"原始路径（解码后）: {path}")
        print(f"待签名字符串: {sign_raw}")
        print(f"MD5结果: {md5_result}")
        print(f"auth_key: {auth_key}")
        print("========================")

        return new_url
    except Exception as e:
        raise RuntimeError(f"签名失败：{str(e)}") from e


def parse_duration_input(input_str: str) -> timedelta:
    """
    解析用户输入的有效期字符串为timedelta对象
    支持格式：10s(秒)、15m(分)、1h(小时)、2d(天)，例如：15m → 15分钟
    """
    input_str = input_str.strip().lower()
    if not input_str:
        raise ValueError("有效期不能为空")

    try:
        # 提取数字和单位
        num = int(''.join([c for c in input_str if c.isdigit()]))
        unit = ''.join([c for c in input_str if c.isalpha()])

        # 根据单位转换为timedelta
        if unit == 's':
            return timedelta(seconds=num)
        elif unit == 'm':
            return timedelta(minutes=num)
        elif unit == 'h':
            return timedelta(hours=num)
        elif unit == 'd':
            return timedelta(days=num)
        else:
            raise ValueError(f"不支持的时间单位：{unit}，仅支持 s(秒)/m(分)/h(小时)/d(天)")
    except ValueError as e:
        raise ValueError(f"有效期格式错误：{e}，示例格式：15m（15分钟）、1h（1小时）")


def get_user_inputs() -> tuple[str, str, int, timedelta]:
    """
    交互式获取用户输入的配置参数，并做输入验证
    返回：(origin_url, private_key, uid, valid_duration)
    """
    print("===== 123云盘直链签名工具 =====")
    print("请按提示输入以下配置参数（输入完成后按回车确认）\n")

    # 1. 获取原始URL（非空验证）
    while True:
        origin_url = input("1. 请输入原始直链URL（需去掉原有auth_key参数）：").strip()
        if origin_url:
            break
        print("❌ URL不能为空，请重新输入！\n")

    # 2. 获取鉴权密钥（非空验证）
    while True:
        private_key = input("2. 请输入123云盘鉴权密钥：").strip()
        if private_key:
            break
        print("❌ 鉴权密钥不能为空，请重新输入！\n")

    # 3. 获取UID（数字验证）
    while True:
        uid_input = input("3. 请输入123云盘账号ID（纯数字）：").strip()
        try:
            uid = int(uid_input)
            break
        except ValueError:
            print("❌ UID必须是纯数字，请重新输入！\n")

    # 4. 获取有效期（格式验证）
    while True:
        duration_input = input("4. 请输入链接有效期（示例：15m=15分钟，1h=1小时，2d=2天）：").strip()
        try:
            valid_duration = parse_duration_input(duration_input)
            break
        except ValueError as e:
            print(f"❌ {e}，请重新输入！\n")

    print("\n✅ 所有参数输入完成，开始签名...\n")
    return origin_url, private_key, uid, valid_duration


if __name__ == "__main__":
    try:
        # 交互式获取用户输入的参数
        origin_url, private_key, uid, valid_duration = get_user_inputs()

        # 生成签名URL
        signed_url = sign_url(origin_url, private_key, uid, valid_duration)

        # 输出结果
        print("✅ 签名成功，最终URL：")
        print("-" * 80)
        print(signed_url)
        print("-" * 80)
    except Exception as e:
        print(f"\n❌ 签名失败：{e}")