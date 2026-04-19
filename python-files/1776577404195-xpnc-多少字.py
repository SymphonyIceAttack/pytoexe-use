import re
text = input("文本？")
chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
char_count = len(chinese_chars)
print(f"正文中文字数：{char_count}字")
