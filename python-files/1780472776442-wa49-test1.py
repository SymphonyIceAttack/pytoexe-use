import requests
import re
import sys

TARGET_URL = "https://iot.qyhulian.com"
ADMIN_PATH = "/admin"

PATTERNS = {
    "API_KEY": r"(?i)(api[_-]?key|access[_-]?token)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9]{20,})['\"]",
    "PASSWORD": r"(?i)(password|passwd|pwd)['\"]?\s*[:=]\s*['\"]([^'\"]{6,})['\"]",
    "INTERNAL_IP": r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
}

def scan_leaks():
    print(f"[*] 开始扫描 {TARGET_URL}{ADMIN_PATH} 静态资源...")
    try:
        resp = requests.get(TARGET_URL + ADMIN_PATH, timeout=10)
        js_files = re.findall(r'<script.*?src=["\'](.*?\.js)["\']', resp.text)

        if not js_files:
            print("[!] 未找到 JS 文件，尝试扫描 HTML 本身...")
            js_files = [""]

        for js in js_files[:8]:
            if js:
                js_url = js if js.startswith("http") else TARGET_URL + js
            else:
                js_url = TARGET_URL + ADMIN_PATH

            print(f"[+] 检查: {js_url}")
            js_content = requests.get(js_url).text

            for name, pattern in PATTERNS.items():
                matches = re.findall(pattern, js_content)
                if matches:
                    print(f"[!] 发现疑似 {name} 泄露！")
                    # 打印前50个字符作为证据，避免刷屏
                    snippet = js_content[js_content.find(matches[0][0]):js_content.find(matches[0][0])+50]
                    print(f"    片段: ...{snippet}...")

    except Exception as e:
        print(f"[!] 扫描异常: {e}")

    print("\n[+] 扫描完成。按回车键退出。")
    input()

if __name__ == "__main__":
    scan_leaks()