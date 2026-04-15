import hashlib
SECRET = "Ultimate_2026_99_MONTHLY"

def make_code(mid, expire):
    s = f"{mid}|{expire}|{SECRET}"
    return hashlib.md5(s.encode()).hexdigest()[:16].upper()

if __name__ == "__main__":
    print("===== 至尊版 99元/月 授权生成器 =====")
    mid = input("输入用户机器码：").strip().upper()
    expire = input("到期日期(YYYY-MM-DD)：").strip()
    print("授权码：", make_code(mid, expire))
    input("按回车退出")