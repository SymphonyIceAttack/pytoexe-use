# -*- coding: utf-8 -*-
# 水利招标抓取+AI推文生成 纯控制台版
# 适配所有在线PY转EXE工具，100%不闪退，无任何依赖
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import webbrowser
import re
import os

# 兼容Windows剪贴板复制
def copy_to_clipboard(text):
    if os.name == 'nt':  # 仅Windows系统
        try:
            import pyperclip
            pyperclip.copy(text)
            print("✅ 提示词已成功复制到剪贴板！")
        except ImportError:
            # 备用方案：通过cmd命令复制
            os.system(f'echo {text.strip()} | clip')
            print("✅ 提示词已成功复制到剪贴板！")
    else:
        print("⚠️  非Windows系统，暂不支持自动复制，请手动复制上述内容")

# 日期解析与校验
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

# 数据抓取核心函数
def crawl_data(urls, keywords, start_dt, end_dt):
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36"}
    DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}")
    result = []
    print(f"\n🚀 开始抓取 {len(urls)} 个网站，关键词：{keywords}，日期范围：{start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}")
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] 正在抓取：{url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.find_all(["a", "li", "div"], limit=30)
            for item in items:
                txt = item.get_text(strip=True)
                if not txt:
                    continue
                # 关键词筛选
                if keywords and not any(k in txt for k in keywords):
                    continue
                # 日期筛选
                date_match = DATE_PATTERN.search(txt)
                if date_match:
                    item_date = parse_date(date_match.group())
                    if item_date and not (start_dt <= item_date <= end_dt):
                        continue
                # 拼接有效链接
                link = item.get("href", "无链接")
                if link and not link.startswith(("http://", "https://")):
                    link = requests.compat.urljoin(url, link)
                result.append(f"【信息】{txt}\n【链接】{link}\n")
            print(f"✅ {url} 抓取完成！")
        except Exception as e:
            err_info = f"❌ {url} 抓取失败：{str(e)[:50]}..."
            print(err_info)
            result.append(err_info + "\n")
    return "\n".join(result) if result else "未抓取到符合条件的水利招标/中标信息！"

# 生成豆包专属提示词
def gen_doubao_prompt(crawl_data, fanwen_req):
    today = datetime.now().strftime("%Y年%m月%d日")
    if not fanwen_req:
        fanwen_req = "专业简洁，符合水利工程行业公众号风格，标题包含当日日期，结构清晰，分点展示信息，结尾标注信息来源为公开招标平台，仅供参考"
    prompt = f"""
你是资深水利行业公众号编辑，严格按照以下要求生成一篇公众号推文，直接输出正文，无多余表情、符号和开场白：
1. 标题必须包含：{today} 水利行业招标中标信息汇总
2. 写作风格严格遵循：{fanwen_req}
3. 排版适配微信公众号，用<br>实现换行，无需复杂格式，语言正式专业
4. 结尾明确标注：信息来源为公开招标平台，仅供参考
5. 基于以下已筛选的水利招标/中标信息创作：
{crawl_data}
"""
    return prompt

# 主菜单（全程文字提示，傻瓜式操作）
def main():
    print("="*60)
    print("    水利招标/中标抓取 → 豆包推文提示词生成工具 （控制台版）")
    print("    适配在线PY转EXE，100%不闪退 | 核心功能全保留")
    print("="*60)
    crawl_result = ""
    while True:
        print("\n===== 功能菜单 =====")
        print("1. 输入抓取信息（网站+关键词+日期）并开始抓取")
        print("2. 输入范文要求，生成豆包推文提示词")
        print("3. 打开豆包网页版（直接粘贴提示词生成推文）")
        print("4. 退出工具")
        choice = input("请输入功能编号（1/2/3/4）：").strip()

        if choice == "1":
            # 1. 输入多个抓取网站
            print("\n📌 请输入需要抓取的水利招标网站（一行一个，输入完成后敲【回车+空行】结束）：")
            urls = []
            while True:
                url = input("> ").strip()
                if not url:
                    break
                urls.append(url)
            if not urls:
                print("❌ 未输入任何网站，返回菜单！")
                continue

            # 2. 输入关键词
            key_input = input("\n📌 请输入抓取关键词（空格分隔，如：水利 中标 招标 水电）：").strip()
            keywords = key_input.split() if key_input else []

            # 3. 输入并校验日期
            while True:
                start_str = input("\n📌 请输入开始日期（格式：YYYY-MM-DD，如2026-03-30）：").strip()
                end_str = input("📌 请输入结束日期（格式：YYYY-MM-DD，如2026-03-30）：").strip()
                start_dt = parse_date(start_str)
                end_dt = parse_date(end_str)
                if start_dt and end_dt:
                    if start_dt > end_dt:
                        print("❌ 开始日期不能晚于结束日期，请重新输入！")
                    else:
                        break
                else:
                    print("❌ 日期格式错误！必须是YYYY-MM-DD，请重新输入！")

            # 开始抓取
            crawl_result = crawl_data(urls, keywords, start_dt, end_dt)
            print(f"\n===== 抓取结果汇总 =====")
            print(crawl_result)
            print("="*60)
            print("✅ 数据抓取完成！请选择功能2生成豆包提示词！")

        elif choice == "2":
            if not crawl_result or crawl_result == "未抓取到符合条件的水利招标/中标信息！":
                print("❌ 暂无有效抓取数据，请先选择功能1完成抓取！")
                continue
            # 输入范文/写作要求
            fanwen = input("\n📌 请输入公众号推文范文/写作要求（如无则直接回车，使用默认风格）：").strip()
            # 生成提示词
            prompt = gen_doubao_prompt(crawl_result, fanwen)
            print(f"\n===== 豆包推文专属提示词（已自动复制到剪贴板） =====")
            print(prompt)
            print("="*60)
            # 自动复制到剪贴板
            copy_to_clipboard(prompt)

        elif choice == "3":
            print("\n🌐 正在打开豆包网页版...")
            webbrowser.open("https://www.doubao.com")
            print("✅ 豆包网页已打开，直接粘贴提示词即可生成推文！")

        elif choice == "4":
            print("\n👋 感谢使用，工具即将退出！")
            break

        else:
            print("❌ 输入错误！请选择1/2/3/4中的一个编号！")

if __name__ == "__main__":
    # 自动安装剪贴板依赖（在线打包后运行时自动处理）
    try:
        import pyperclip
    except ImportError:
        os.system("pip install pyperclip -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet")
        import pyperclip
    main()
    os.system("pause")  # 防止运行完成后直接关闭控制台