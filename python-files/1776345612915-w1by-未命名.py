import hashlib
import random
import string
import time

# 目标 MD5（你自己的，仅自用）
TARGET_MD5 = "B52D77DDA2558E0C0431E9F47588E989".lower()

# 生成随机字符串的字符集（数字 + 大小写字母）
CHAR_SET = string.ascii_letters + string.digits

def md5_hash(text):
    """计算字符串的 MD5 值（自用）"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def random_collision(max_length=8):
    """
    随机碰撞 MD5（仅用于找回你自己的密码）
    max_length：随机字符串最大长度
    """
    count = 0
    start_time = time.time()
    
    print(f"开始随机碰撞，目标 MD5：{TARGET_MD5}")
    print(f"字符集：{CHAR_SET}\n")

    while True:
        # 随机生成 1~max_length 长度的字符串
        length = random.randint(1, max_length)
        rand_str = ''.join(random.choice(CHAR_SET) for _ in range(length))
        
        # 计算 MD5 并比对
        current_md5 = md5_hash(rand_str)
        count += 1

        # 每 10 万次输出一次进度
        if count % 100000 == 0:
            elapsed = time.time() - start_time
            print(f"已尝试 {count:,} 次 | 耗时 {elapsed:.2f}s")

        # 匹配成功
        if current_md5 == TARGET_MD5:
            elapsed = time.time() - start_time
            print("\n" + "="*50)
            print(f"✅ 碰撞成功！")
            print(f"原始字符串：{rand_str}")
            print(f"MD5：{current_md5}")
            print(f"总尝试次数：{count:,}")
            print(f"总耗时：{elapsed:.2f} 秒")
            print("="*50)
            return rand_str

# 启动（仅自用）
if __name__ == "__main__":
    random_collision(max_length=6)
