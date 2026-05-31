import asyncio
import aiohttp
import time
import os
import sys
from urllib.parse import urlparse
from aiohttp import ClientTimeout, TCPConnector


class OllamaScanner:
    def __init__(self):
        self.proxy = None
        self.targets = []
        self.model_count = 3
        self.max_concurrent = 30  # 更安全的默认并发数
        self.ok_file = 'ok.txt'

    async def read_urls(self, file_path='url.txt'):
        """读取URL文件并验证格式"""
        if not os.path.exists(file_path):
            print(f"[!] 文件 {file_path} 不存在")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            urls = []
            for line in lines:
                parsed = urlparse(line)
                if parsed.scheme not in ['http', 'https']:
                    print(f"[!] 跳过无效URL(协议错误): {line}")
                    continue
                if not parsed.netloc:
                    print(f"[!] 跳过无效URL(域名错误): {line}")
                    continue
                urls.append(line)
            return urls
        except Exception as e:
            print(f"[!] 读取URL文件时发生错误: {str(e)}")
            return []

    def setup_scanner(self):
        """设置扫描参数"""
        print("\n=== Ollama 服务扫描器 ===")

        while True:
            try:
                model_count = int(input("请输入要测试的模型数量 (2-18，默认3): ") or "3")
                if 2 <= model_count <= 38:
                    self.model_count = model_count
                    break
                print("[-] 输入无效，请输入2到8之间的数字")
            except ValueError:
                print("[-] 请输入有效的数字")

        while True:
            try:
                max_concurrent = input(f"请输入最大并发数 (建议10-50，默认{self.max_concurrent}): ").strip()
                if not max_concurrent:
                    break  # 使用默认值
                max_concurrent = int(max_concurrent)
                if max_concurrent > 0:
                    self.max_concurrent = max_concurrent
                    break
                print("[-] 并发数必须大于0")
            except ValueError:
                print("[-] 请输入有效的数字")

        proxy_use = input("是否使用代理 http://127.0.0.1:12334? (y/n, 默认n): ").lower().strip()
        if proxy_use == 'y':
            self.proxy = 'http://127.0.0.1:12334'
            print(f"[+] 已设置代理: {self.proxy}")
        else:
            print("[+] 未使用代理")

        return True

    async def test_model(self, url, model_name, session):
        """测试模型响应（严格按Ollama格式验证并检查回复内容）"""
        start_time = time.time()
        try:
            async with session.post(
                f"{url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        # 基础结构检查
                        if isinstance(data, dict) and data.get("done") is True:
                            # 深度验证：检查是否有实际的回复内容
                            message = data.get("message")
                            if isinstance(message, dict):
                                content = message.get("content", "")
                                # 确保内容不为空，且不仅仅是空白字符
                                if content and content.strip():
                                    duration = time.time() - start_time
                                    return True, duration, content.strip()[:20] # 返回部分内容用于预览
                    except Exception as e:
                        print(f"[-] JSON解析失败 {url} {model_name}: {e}")
                        pass
                return False, 0, ""
        except Exception as e:
            print(f"[-] 模型测试请求异常 {url} {model_name}: {type(e).__name__}: {e}")
            return False, 0, ""

    async def scan_url(self, url, session):
        """扫描单个URL并实时保存成功结果"""
        print(f"[*] 正在扫描目标: {url}")
        try:
            async with session.get(f"{url}/api/tags") as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        if isinstance(data, dict) and 'models' in data:
                            models = data['models']
                            print(f"[+] 在 {url} 发现Ollama API，发现 {len(models)} 个模型")
                            selected_models = models[:min(self.model_count, len(models))]
                            success_count = 0
                            for model in selected_models:
                                model_name = model['name']
                                print(f"[+] 正在测试模型: {model_name}")
                                success, duration, content_preview = await self.test_model(url, model_name, session)
                                if success:
                                    # 增加了回复内容的预览
                                    result_line = f"API: {url.ljust(30)} 模型: {model_name.ljust(30)} \t 耗时: {duration:.2f}s\t  回复预览: {content_preview}..."
                                    print(f"[+] 测试成功 - {result_line}")
                                    try:
                                        with open(self.ok_file, 'a', encoding='utf-8') as f:
                                            f.write(result_line + '\n')
                                        success_count += 1
                                    except Exception as e:
                                        print(f"[-] 写入文件失败: {str(e)}")
                                else:
                                    print(f"[-] 测试失败(无有效回复) - {url} 模型 {model_name}")
                            return success_count > 0
                    except Exception as e:
                        print(f"[-] 解析 /api/tags 响应失败 {url}: {type(e).__name__}: {e}")
                else:
                    print(f"[-] 访问被拒绝或接口不存在 {url} | Status: {response.status}")
        except Exception as e:
            print(f"[-] 请求异常 {url}: {type(e).__name__}: {e}")
        return False

    async def main(self):
        """主函数"""
        print("[*] 开始初始化扫描器...")
        if not self.setup_scanner():
            print("[-] 扫描器初始化失败")
            return

        print(f"[*] 正在从 url.txt 读取目标URL...")
        self.targets = await self.read_urls()
        if not self.targets:
            print("[-] 未找到有效的目标URL，请检查url.txt文件")
            return

        print(f"[+] 成功加载 {len(self.targets)} 个有效目标")

        # 设置严格的超时策略
        timeout = ClientTimeout(
            total=35,           # 整个请求最长35秒
            connect=10,         # 连接建立最多10秒
            sock_read=25,       # 数据读取最多25秒
            sock_connect=10     # TCP握手最多10秒
        )

        # 使用连接池限制并发，避免系统资源耗尽
        connector = TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=5,   # 单一主机最多5连接，防被封
            ssl=False           # 忽略SSL证书错误
        )

        # 自定义Headers模拟浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # 分批处理
        batches = [
            self.targets[i:i + self.max_concurrent]
            for i in range(0, len(self.targets), self.max_concurrent)
        ]
        print(f"[*] 开始扫描，共分为 {len(batches)} 个批次")

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:

            total_success = 0
            for i, batch in enumerate(batches):
                print(f"\n[*] 正在处理第 {i+1}/{len(batches)} 批次 (包含 {len(batch)} 个目标)")
                tasks = [self.scan_url(url, session) for url in batch]
                results = await asyncio.gather(*tasks)
                batch_success = sum(1 for r in results if r)
                total_success += batch_success
                print(f"[✓] 第 {i+1} 批次完成，{batch_success}/{len(batch)} 成功")

        print(f"\n[+] 所有扫描完成！")
        print(f"[+] 共扫描 {len(self.targets)} 个目标，发现 {total_success} 个可用Ollama服务")
        print(f"[+] 成功结果已实时保存至 {os.path.abspath(self.ok_file)}")


if __name__ == "__main__":
    scanner = OllamaScanner()
    try:
        asyncio.run(scanner.main())
    except KeyboardInterrupt:
        print("\n\n[!] 用户中断扫描")
        sys.exit(0)
    except Exception as e:
        print(f"[!] 程序异常终止: {e}")