import requests
import re

def get_live_url(short_link):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        r = requests.get(short_link.strip(), headers=headers, allow_redirects=True, timeout=10)
        match = re.search(r"https://live\.douyin\.com/\d+", r.url + r.text)
        return match.group() if match else None
    except Exception:
        return None


def main():
    print("=====抖音短链(v.douyin.com) → 直播间地址(live.douyin.com)=====")
    print("使用说明：每行一条【链接,主播名】，输入完成后直接回车两次开始解析")
    print("示例：https://v.douyin.com/xxxx/,主播: 猫猫呀")
    print("-" * 60)

    lines = []
    while True:
        line = input()
        if not line.strip():
            break
        lines.append(line.strip())

    print("\n=====解析结果=====\n")
    output_lines = []
    for line in lines:
        if "," not in line:
            out = f"# 格式错误：{line}"
            print(out)
            output_lines.append(out)
            continue
        url_raw, name_raw = line.split(",", 1)
        url_raw = url_raw.strip()
        name_raw = name_raw.strip()

        if url_raw.startswith("https://live.douyin.com"):
            out = f"{url_raw},{name_raw}"
            print(out)
            output_lines.append(out)
            continue

        live_url = get_live_url(url_raw)
        if live_url:
            out = f"{live_url},{name_raw}"
            print(out)
            output_lines.append(out)
        else:
            out = f"# {name_raw}：无有效直播间（下播/作品链接/解析失败）"
            print(out)
            output_lines.append(out)

    # 自动写入 result.txt（和exe同目录）
    with open("result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("\n✅ 解析完成！结果已自动保存到【result.txt】")
    input("按回车键关闭窗口")


if __name__ == "__main__":
    main()
