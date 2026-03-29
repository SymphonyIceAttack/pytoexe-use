# -*- coding: utf-8 -*-
# 水利招标抓取+AI推文生成 【纯标准库版】
# 无任何第三方依赖，在线PY转EXE 100%不闪退
import urllib.request
import urllib.parse
import re
import os
import datetime
import webbrowser

# 复制到剪贴板（Windows 原生命令，无需 pyperclip）
def copy_to_clipboard(text):
    if os.name == 'nt':
        # Windows 下用系统命令复制
        cmd = f'echo {text.strip().replace("^", "^^").replace("&", "^&").replace("<", "^<").replace(">", "^>").replace("|", "^|")} | clip'
        os.system(cmd)
        print("✅ 提示词已复制到剪贴板！")
    else:
        print("⚠️  非Windows系统，请手动复制上述内容")

# 日期解析
def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

# 抓取网页内容（用 urllib 替代 requests，纯标准库）
def fetch_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as f:
            return f.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"【抓取失败】{url}：{str(e)}"

# 提取页面中的文本和链接（用正则替代 BeautifulSoup，纯标准库）
def extract_info(html, base_url, keywords, start_dt, end_dt):
    result = []
    # 匹配 <a> 标签的文本和链接
    pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
    matches = pattern.findall(html)
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}')
    
    for href, text in matches:
        text = text.strip()
        if not text:
            continue
        # 关键词筛选
        if keywords and not any(k in text for k in keywords):
            continue
        # 日期筛选
        date_match = date_pattern.search(text)
        if date_match:
            item_date = parse_date(date_match.group())
            if item_date and not (start_dt <= item_date <= end_dt):
                continue
        # 拼接完整链接
        if not href.startswith(('http://', 'https://')):
            href = urllib.parse.urljoin(base_url, href)
        result.append(f"【信息】{text}\n【链接】{href}\n")
    return "\n".join(result) if result else "未抓取到符合条件的信息！"

# 生成豆包提示词
def gen_prompt(crawl_data, fanwen_req):
    today = datetime.datetime.now().strftime("%Y年%m月%d日")
    if not fanwen_req:
        fanwen_req = "专业简洁，符合水利行业公众号风格，标题含日期，结尾标注信息来源"
    prompt = f"""
你是水利行业公众号编辑，按以下要求生成推文：
【写作要求】
{fanwen_req}
【今日招标信息】
{crawl_data}
【规则】
1. 标题必须包含：{today} 水利招标中标汇总
2. 排版适配公众号，用<br>换行
3. 语言正式专业
4. 结尾标注：信息来源为公开招标平台，仅供参考
5. 直接输出正文，无多余表情
"""
    return prompt

# 主菜单
def main():
    print("="*60)
    print("    水利招标抓取 → 豆包推文生成工具 【纯标准库版】")
    print("    零第三方依赖 | 在线转EXE 100%不闪退")
    print("="*60)
    crawl_result = ""
    while True:
        print("\n===== 功能菜单 =====")
        print("1. 输入网站+关键词+日期，开始抓取数据")
        print("2. 输入范文要求，生成豆包提示词（自动复制）")
        print("3. 打开豆包网页版")
        print("4. 退出")
        choice = input("请输入编号（1/2/3/4）：").strip()

        if choice == "1":
            # 输入多个网站
            print("\n📌 请输入抓取网站（一行一个，空行结束）：")
            urls = []
            while True:
                url = input("> ").strip()
                if not url:
                    break
                urls.append(url)
            if not urls:
                print("❌ 未输入网站！")
                continue
            # 输入关键词
            key_input = input("\n📌 关键词（空格分隔）：").strip()
            keywords = key_input.split() if key_input else []
            # 输入日期
            while True:
                start_str = input("\n📌 开始日期（YYYY-MM-DD）：").strip()
                end_str = input("📌 结束日期（YYYY-MM-DD）：").strip()
                start_dt = parse_date(start_str)
                end_dt = parse_date(end_str)
                if start_dt and end_dt and start_dt <= end_dt:
                    break
                print("❌ 日期格式错误或开始日期晚于结束日期！")
            # 开始抓取
            print("\n🚀 开始抓取...")
            all_data = []
            for url in urls:
                print(f"正在抓取：{url}")
                html = fetch_page(url)
                if "【抓取失败】" in html:
                    all_data.append(html)
                else:
                    all_data.append(extract_info(html, url, keywords, start_dt, end_dt))
            crawl_result = "\n".join(all_data)
            print(f"\n===== 抓取结果 =====")
            print(crawl_result)
            print("✅ 抓取完成！")

        elif choice == "2":
            if not crawl_result or "未抓取到" in crawl_result:
                print("❌ 请先抓取有效数据！")
                continue
            fanwen = input("\n📌 范文要求（直接回车用默认风格）：").strip()
            prompt = gen_prompt(crawl_result, fanwen)
            print(f"\n===== 豆包提示词 =====")
            print(prompt)
            copy_to_clipboard(prompt)

        elif choice == "3":
            webbrowser.open("https://www.doubao.com")
            print("✅ 豆包网页已打开，直接粘贴提示词即可！")

        elif choice == "4":
            print("\n👋 退出工具！")
            break
        else:
            print("❌ 输入错误，请选 1/2/3/4！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 错误：{e}")
    os.system("pause")  # 防止窗口一闪而过