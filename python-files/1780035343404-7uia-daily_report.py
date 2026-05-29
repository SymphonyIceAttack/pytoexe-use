import os
import re
from docx import Document


def read_docx(file):
    doc = Document(file)
    return "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])


def find(pattern, text):
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else ""


def extract_sections(text):

    data = {}

    # 日期
    data["date"] = find(r"日期[:：]\s*(\d{4}-\d{2}-\d{2})", text)

    # 基本情况
    data["base"] = find(r"(今日北京市大数据中心信息系统整体运行良好.*?。)", text)

    # 流量
    data["traffic"] = find(r"(今日监测互联网侧流量.*?API.*?异常.*?。)", text)

    # 攻击
    data["attack"] = find(r"(今日监测发现网络安全攻击报警共.*?系统.*?次）。)", text)

    # 日志
    data["log"] = find(r"(今日共收集日志.*?数据库日志.*?万条。)", text)

    # 提权
    data["sudo"] = find(r"(\d+次命令提权.*?正常提权操作。)", text)

    # 邮件
    data["mail"] = find(r"(今日对公务员邮箱进行安全监测.*?封.*?。)", text)

    return data


def build_text(data):

    result = (
        f"{data['date']}：\n"
        f"1、{data['base']}\n"
        f"2、{data['traffic']}\n"
        f"3、{data['attack']}\n"
        f"4、{data['log']}\n"
        f"5、监测发现{data['sudo']}\n"
        f"6、{data['mail']}\n"
    )

    return result

def main():

    folder = "daily_reports"

    files = [f for f in os.listdir(folder) if f.endswith(".docx")]
    files.sort()

    results = []

    for file in files:

        path = os.path.join(folder, file)

        text = read_docx(path)

        data = extract_sections(text)

        report = build_text(data)

        results.append(report)

    final_text = "\n".join(results)

    print(final_text)

    with open("周日报汇总.txt", "w", encoding="utf-8") as f:
        f.write(final_text)

    print("\n已生成文件：周日报汇总.txt")


if __name__ == "__main__":
    main()