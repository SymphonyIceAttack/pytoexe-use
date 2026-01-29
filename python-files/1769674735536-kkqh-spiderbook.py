import time
import os
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class OptimizedFlowSpider:
    def __init__(self, edge_driver_path=None):
        """
        优化流程爬虫：先爬内容，再滚动点击
        """
        print("🔄 启动优化流程爬虫...")
        print("流程：爬内容 → 滚到底部 → 点下一篇")
        print("=" * 60)
        
        # 设置Edge选项
        self.edge_options = Options()
        self.edge_options.add_argument('--no-sandbox')
        self.edge_options.add_argument('--disable-dev-shm-usage')
        self.edge_options.add_argument('--window-size=1600,1000')
        
        # 显示窗口
        # self.edge_options.add_argument('--headless')
        
        # 绕过检测
        self.edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.edge_options.add_experimental_option('useAutomationExtension', False)
        
        # 用户代理
        self.edge_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            if edge_driver_path:
                service = Service(executable_path=edge_driver_path)
                self.driver = webdriver.Edge(service=service, options=self.edge_options)
            else:
                self.driver = webdriver.Edge(options=self.edge_options)
            
            print("✓ Edge浏览器启动成功")
            
            # 绕过检测
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            
        except Exception as e:
            print(f"✗ 浏览器启动失败: {e}")
            raise
    
    def extract_content_smart(self):
        """
        智能提取文章内容（滚动前提取）- 保持原有排版
        """
        print("  提取文章内容...")
        
        # 方法1：直接查找主要内容区域
        content_selectors = [
            '.reader-content', '.text-content', '.chapter-content',
            '.book-content', 'article', 'main', '.content', '#content'
        ]
        
        for selector in content_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    text = element.text.strip()
                    if len(text) > 100:
                        print(f"    ✓ 从 {selector} 提取: {len(text)} 字符")
                        return text  # 直接返回，保持原有排版
            except:
                continue
        
        # 方法2：获取页面标题和段落
        print("  使用备选提取方法...")
        
        # 获取所有段落
        paragraphs = []
        try:
            p_elements = self.driver.find_elements(By.TAG_NAME, 'p')
            for p in p_elements[:30]:  # 限制数量
                if p.is_displayed():
                    text = p.text.strip()
                    if len(text) > 20:
                        paragraphs.append(text)
        except:
            pass
        
        # 如果段落太少，获取div内容
        if len(paragraphs) < 3:
            try:
                divs = self.driver.find_elements(By.TAG_NAME, 'div')
                for div in divs[:50]:
                    if div.is_displayed():
                        text = div.text.strip()
                        if 50 < len(text) < 1000:
                            paragraphs.append(text)
            except:
                pass
        
        # 合并内容
        if paragraphs:
            # 去重
            unique_paras = []
            seen = set()
            for para in paragraphs:
                if para not in seen:
                    seen.add(para)
                    unique_paras.append(para)
            
            content = '\n'.join(unique_paras[:20])
            print(f"    ✓ 备选提取: {len(content)} 字符")
            return content
        
        print("    ✗ 内容提取失败")
        return ""
    
    def scroll_to_bottom_safely(self):
        """
        安全滚动到底部（提取内容后调用）
        """
        print("  滚动到底部...")
        
        try:
            # 先滚动到顶部（确保从头开始）
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # 分步滚动到底部
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            print(f"    页面高度: {total_height}px, 视口高度: {viewport_height}px")
            
            # 如果页面太长，分步滚动
            if total_height > 2000:
                steps = total_height // viewport_height + 1
                print(f"    需要 {steps} 步滚动")
                
                for step in range(steps):
                    scroll_to = min((step + 1) * viewport_height, total_height)
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                    time.sleep(0.2)
            else:
                # 直接滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            time.sleep(0.5)
            
            # 额外滚动一点，确保按钮完全可见
            self.driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(0.3)
            
            print("    ✓ 滚动完成")
            return True
            
        except Exception as e:
            print(f"    滚动失败: {e}")
            return False
    
    def find_and_click_next_button(self):
        """
        查找并点击下一篇按钮（滚动后调用）
        """
        try:
            print("  查找下一篇按钮...")
            
            # 首先检查是否有"本书内容结束"提示
            try:
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                if "本书内容结束" in page_text:
                    print("    ⚠ 检测到'本书内容结束'，停止爬取")
                    return "end"
            except:
                pass
            
            # 多种方式查找按钮
            button_selectors = [
                ("//button[contains(text(), '下一篇')]", "按钮-文本"),
                ("//a[contains(text(), '下一篇')]", "链接-文本"),
                ("//button[contains(text(), '下一章')]", "按钮-下一章"),
                ("//a[contains(text(), '下一章')]", "链接-下一章"),
                ("//*[contains(@class, 'next')]", "类名-next"),
                ("//*[contains(@id, 'next')]", "ID-next"),
            ]
            
            for xpath, btn_type in button_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            btn_text = element.text.strip()
                            print(f"    找到按钮 [{btn_type}]: '{btn_text}'")
                            
                            # 确保按钮可见
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            
                            # 点击前获取当前URL
                            old_url = self.driver.current_url
                            
                            # 尝试点击
                            try:
                                element.click()
                            except:
                                # 如果普通点击失败，用JavaScript点击
                                self.driver.execute_script("arguments[0].click();", element)
                            
                            time.sleep(2)  # 等待页面加载
                            
                            # 检查是否成功跳转
                            new_url = self.driver.current_url
                            if new_url != old_url:
                                print(f"    ✓ 成功跳转到新页面")
                                return "success"
                            else:
                                print(f"    ⚠ URL未变化，可能按钮无效")
                                return "failed"
                except:
                    continue
            
            print("    ✗ 未找到有效按钮")
            return "failed"
            
        except Exception as e:
            print(f"    按钮操作失败: {e}")
            return "failed"
    
    def crawl_optimized_flow(self, start_url, book_name, max_chapters=200):
        """
        优化流程爬取：先爬内容，再滚动点击
        """
        print(f"\n📚 开始爬取《{book_name}》")
        print(f"目标: {max_chapters} 章")
        print(f"起始: {start_url}")
        print("=" * 60)
        
        # 访问起始页
        print("\n访问起始页面...")
        self.driver.get(start_url)
        time.sleep(3)
        
        # 创建保存目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = f"识典古籍_优化流程/{book_name}_{timestamp}"
        os.makedirs(save_dir, exist_ok=True)
        
        # 记录信息
        log_file = f"{save_dir}/crawl_log.json"
        chapters_data = []
        visited_urls = set()
        
        for chapter_num in range(1, max_chapters + 1):
            print(f"\n{'='*50}")
            print(f"第 {chapter_num} 章")
            
            # 获取当前页面信息
            current_url = self.driver.current_url
            title = self.driver.title
            
            # 检查是否重复访问
            if current_url in visited_urls:
                print(f"  ⚠ 重复URL，可能循环，停止爬取")
                break
            
            visited_urls.add(current_url)
            
            print(f"标题: {title}")
            print(f"URL: {current_url}")
            
            # ========== 第一步：提取文章内容 ==========
            print("\n【第一步】提取文章内容")
            content = self.extract_content_smart()
            
            if content and len(content) > 100:
                # 保存章节到列表
                chapters_data.append({
                    'number': chapter_num,
                    'title': title,
                    'url': current_url,
                    'content': content,  # 保存纯内容
                    'length': len(content)
                })
                
                print(f"  ✓ 提取成功: {len(content)} 字符")
                
                # 实时保存日志
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'book_name': book_name,
                        'current_chapter': chapter_num,
                        'total_chapters': max_chapters,
                        'saved_chapters': len(chapters_data),
                        'chapters': chapters_data
                    }, f, ensure_ascii=False, indent=2)
            else:
                print(f"  ✗ 内容提取失败")
                chapters_data.append({
                    'number': chapter_num,
                    'title': title,
                    'url': current_url,
                    'error': '内容提取失败'
                })
            
            # ========== 第二步：如果不是最后一章，继续 ==========
            if chapter_num < max_chapters:
                print(f"\n【第二步】准备第 {chapter_num + 1} 章")
                
                # 2.1 滚动到底部
                print("  2.1 滚动到底部...")
                scroll_success = self.scroll_to_bottom_safely()
                
                if not scroll_success:
                    print("  ⚠ 滚动失败，尝试继续")
                
                # 2.2 查找并点击下一篇按钮
                print("  2.2 查找下一篇按钮...")
                click_result = self.find_and_click_next_button()
                
                if click_result == "success":
                    print(f"  ✓ 成功进入下一章")
                    time.sleep(2)  # 等待新页面稳定
                    continue
                elif click_result == "end":
                    print(f"  ✓ 检测到书籍结束提示，停止爬取")
                    break
                else:
                    print("  ⚠ 按钮点击失败，尝试URL推测")
                    
                    # 尝试推测下一页URL
                    next_url = self._guess_next_url(current_url, chapter_num)
                    if next_url and next_url != current_url:
                        print(f"    推测URL: {next_url}")
                        self.driver.get(next_url)
                        time.sleep(3)
                    else:
                        print("  ✗ 无法继续，停止爬取")
                        break
            else:
                print(f"\n  ✓ 已完成目标章节数")
        
        # 保存所有章节到单个文件
        if chapters_data:
            print(f"\n{'='*60}")
            print("正在保存所有章节到单个文件...")
            self._save_to_single_file(chapters_data, save_dir, book_name)
        
        # 关闭浏览器
        self.driver.quit()
        
        # 生成最终报告
        self._generate_flow_report(chapters_data, save_dir, book_name)
        
        print(f"\n{'='*60}")
        print(f"爬取完成!")
        successful = len([c for c in chapters_data if 'content' in c])
        print(f"成功章节: {successful}/{len(chapters_data)}")
        
        if successful > 0:
            total_chars = sum(c.get('length', 0) for c in chapters_data if 'content' in c)
            print(f"总字符数: {total_chars:,}")
            print(f"平均每章: {total_chars//successful:,} 字符")
        
        print(f"保存到: {save_dir}")
        print("=" * 60)
    
    def _save_to_single_file(self, chapters_data, save_dir, book_name):
        """将所有章节保存到单个文本文件"""
        if not chapters_data:
            print("  ✗ 没有章节数据可保存")
            return
        
        # 生成单个文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        single_file = f"{save_dir}/{book_name}_全文_{timestamp}.txt"
        
        with open(single_file, 'w', encoding='utf-8') as f:
            # 写入书籍信息
            f.write(f"《{book_name}》\n")
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总章节数: {len(chapters_data)}\n")
            f.write("=" * 60 + "\n\n")
            
            # 写入所有章节内容（只保存内容，保持原有排版）
            total_chars = 0
            successful_chapters = 0
            
            for chapter in chapters_data:
                if 'content' in chapter:
                    content = chapter['content'].strip()
                    if content:
                        f.write(f"第{chapter['number']}章\n")
                        f.write("-" * 40 + "\n")
                        f.write(content + "\n\n")
                        total_chars += len(content)
                        successful_chapters += 1
            
            # 写入统计信息
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"全书结束\n")
            f.write(f"总章节数: {successful_chapters}\n")
            if successful_chapters > 0:
                f.write(f"总字符数: {total_chars:,}\n")
                f.write(f"平均每章: {total_chars//successful_chapters:,} 字符\n")
        
        print(f"✓ 已保存到单个文件: {single_file}")
        print(f"  成功章节数: {successful_chapters}")
        if successful_chapters > 0:
            print(f"  总字符数: {total_chars:,}")
    
    def _guess_next_url(self, current_url, chapter_num):
        """推测下一页URL"""
        try:
            # 尝试识别URL模式
            patterns = [
                (r'chapter/(\d+)', lambda m: re.sub(r'chapter/\d+', f'chapter/{int(m.group(1)) + 1}', current_url)),
                (r'/(\d+)/?$', lambda m: re.sub(r'/(\d+)/?$', f'/{int(m.group(1)) + 1}/', current_url)),
                (r'[?&]page=(\d+)', lambda m: re.sub(r'[?&]page=\d+', f'page={int(m.group(1)) + 1}', current_url)),
            ]
            
            for pattern, repl_func in patterns:
                match = re.search(pattern, current_url)
                if match:
                    return repl_func(match)
            
            return None
            
        except:
            return None
    
    def _generate_flow_report(self, chapters_data, save_dir, book_name):
        """生成流程报告"""
        report_file = f"{save_dir}/流程报告.txt"
        
        successful = [c for c in chapters_data if 'content' in c]
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"《{book_name}》优化流程爬取报告\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("🎯 优化流程说明:\n")
            f.write("1. 先提取当前页面文章内容\n")
            f.write("2. 保存内容到内存\n") 
            f.write("3. 滚动到页面底部\n")
            f.write("4. 查找并点击'下一篇'按钮\n")
            f.write("5. 自动检测'本书内容结束'提示\n")
            f.write("6. 所有章节打包到单个TXT文件\n\n")
            
            f.write("📊 爬取统计:\n")
            f.write(f"  目标章节: {len(chapters_data)}\n")
            f.write(f"  成功章节: {len(successful)}\n")
            f.write(f"  失败章节: {len(chapters_data) - len(successful)}\n\n")
            
            if successful:
                f.write("📈 内容统计:\n")
                total_chars = sum(c.get('length', 0) for c in successful)
                avg_chars = total_chars // len(successful) if successful else 0
                
                f.write(f"  总字符数: {total_chars:,}\n")
                f.write(f"  平均每章: {avg_chars:,} 字符\n\n")
                
                f.write("📝 成功章节列表:\n")
                f.write("-" * 50 + "\n")
                for chapter in successful[:10]:  # 只显示前10个
                    f.write(f"第{chapter['number']:03d}章: {chapter['title'][:40]}\n")
                    f.write(f"  字符数: {chapter.get('length', 0):,}\n\n")
                
                if len(successful) > 10:
                    f.write(f"... 还有 {len(successful)-10} 个章节\n\n")
            
            f.write("💡 注意事项:\n")
            f.write("• 只保存文章纯文本内容\n")
            f.write("• 保持原有排版格式\n")
            f.write("• 自动检测书籍结束提示\n")
            f.write("• 所有章节已打包到单个TXT文件\n")
            f.write("• 实时保存日志，支持中断恢复\n")
        
        print(f"✓ 流程报告已保存: {report_file}")

# ================ 主程序 ================

if __name__ == "__main__":
    print("🔄 识典古籍优化流程爬虫")
    print("流程：爬内容 → 滚到底部 → 点下一篇 → 自动结束 → 打包文件")
    print("=" * 60)
    
    # 获取用户输入
    print("\n请输入以下信息：")
    
    while True:
        start_url = input("请输入第一章节的URL: ").strip()
        if start_url.startswith('http'):
            break
        print("  ⚠ 请输入有效的URL地址")
    
    book_name = input("请输入书籍名称: ").strip()
    if not book_name:
        # 尝试从URL提取书籍名
        match = re.search(r'/book/([^/]+)', start_url)
        if match:
            book_name = match.group(1)
        else:
            book_name = "未命名书籍"
    
    try:
        max_input = input("\n请输入要爬取的章节数（默认50，直接回车使用默认值）: ").strip()
        max_chapters = int(max_input) if max_input else 50
    except:
        max_chapters = 230
    
    # EdgeDriver路径
    driver_path = None
    use_default = input("\nEdgeDriver是否在PATH中？(y/n, 默认y): ").strip().lower() or "y"
    if use_default == 'n':
        driver_path = input("请输入EdgeDriver完整路径: ").strip()
    
    print(f"\n{'='*60}")
    print(f"开始爬取《{book_name}》")
    print(f"目标章节: {max_chapters}")
    print(f"起始URL: {start_url}")
    print("严格按照：提取内容 → 滚动到底 → 点击下一篇 → 检测结束 → 打包文件")
    print("=" * 60)
    
    try:
        spider = OptimizedFlowSpider(edge_driver_path=driver_path)
        spider.crawl_optimized_flow(start_url, book_name, max_chapters)
        
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()