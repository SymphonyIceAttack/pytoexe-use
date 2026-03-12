#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书热门话题和笔记抓取程序
用于获取近15天内指定关键词的热门话题和笔记
"""

import time
import json
import csv
import os
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class XiaohongshuScraper:
    def __init__(self, keyword, days=15):
        """
        初始化小红书爬虫
        
        Args:
            keyword (str): 搜索关键词
            days (int): 时间范围，默认15天
        """
        self.keyword = keyword
        self.days = days
        self.driver = None
        self.notes_data = []
        self.topics_data = []
        
    def setup_driver(self):
        """设置Chrome驱动"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            # 使用webdriver-manager自动管理ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            print("浏览器初始化成功")
        except Exception as e:
            print(f"浏览器初始化失败: {e}")
            raise
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
    
    def search_notes(self):
        """搜索笔记"""
        try:
            # 访问小红书首页
            self.driver.get("https://www.xiaohongshu.com")
            time.sleep(3)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 找到搜索框并输入关键词
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='搜索']"))
            )
            search_box.clear()
            search_box.send_keys(self.keyword)
            search_box.send_keys(Keys.RETURN)
            
            print(f"正在搜索关键词: {self.keyword}")
            time.sleep(5)
            
            # 滚动页面加载更多内容
            self.scroll_page()
            
            # 解析笔记数据
            self.parse_notes()
            
        except Exception as e:
            print(f"搜索笔记时出错: {e}")
    
    def scroll_page(self, scroll_times=5):
        """滚动页面加载更多内容"""
        print("正在加载更多内容...")
        for i in range(scroll_times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"第{i+1}次滚动完成")
    
    def parse_notes(self):
        """解析笔记数据"""
        try:
            # 查找笔记元素
            note_elements = self.driver.find_elements(By.CSS_SELECTOR, ".note-item")
            
            print(f"找到 {len(note_elements)} 个笔记")
            
            for element in note_elements:
                try:
                    # 获取笔记标题
                    title_element = element.find_element(By.CSS_SELECTOR, ".title")
                    title = title_element.text.strip() if title_element else "无标题"
                    
                    # 获取笔记链接
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    link = link_element.get_attribute("href") if link_element else ""
                    
                    # 获取作者
                    author_element = element.find_element(By.CSS_SELECTOR, ".author")
                    author = author_element.text.strip() if author_element else "未知作者"
                    
                    # 获取点赞数
                    likes_element = element.find_element(By.CSS_SELECTOR, ".likes")
                    likes = likes_element.text.strip() if likes_element else "0"
                    
                    # 获取发布时间
                    time_element = element.find_element(By.CSS_SELECTOR, ".time")
                    publish_time = time_element.text.strip() if time_element else "未知时间"
                    
                    # 检查是否在指定时间范围内
                    if self.is_within_time_range(publish_time):
                        note_data = {
                            "title": title,
                            "author": author,
                            "likes": likes,
                            "publish_time": publish_time,
                            "link": link,
                            "type": "note"
                        }
                        self.notes_data.append(note_data)
                        print(f"添加笔记: {title}")
                    
                except Exception as e:
                    print(f"解析单个笔记时出错: {e}")
                    continue
                    
        except Exception as e:
            print(f"解析笔记数据时出错: {e}")
    
    def search_topics(self):
        """搜索话题"""
        try:
            # 访问小红书发现页
            self.driver.get("https://www.xiaohongshu.com/explore")
            time.sleep(3)
            
            # 等待页面加载
            wait = WebDriverWait(self.driver, 10)
            
            # 查找热门话题
            topic_elements = self.driver.find_elements(By.CSS_SELECTOR, ".topic-item")
            
            print(f"找到 {len(topic_elements)} 个话题")
            
            for element in topic_elements:
                try:
                    # 获取话题名称
                    name_element = element.find_element(By.CSS_SELECTOR, ".name")
                    name = name_element.text.strip() if name_element else "未知话题"
                    
                    # 获取话题链接
                    link_element = element.find_element(By.CSS_SELECTOR, "a")
                    link = link_element.get_attribute("href") if link_element else ""
                    
                    # 获取参与人数
                    count_element = element.find_element(By.CSS_SELECTOR, ".count")
                    count = count_element.text.strip() if count_element else "0"
                    
                    # 检查话题是否包含关键词
                    if self.keyword.lower() in name.lower():
                        topic_data = {
                            "name": name,
                            "count": count,
                            "link": link,
                            "type": "topic"
                        }
                        self.topics_data.append(topic_data)
                        print(f"添加话题: {name}")
                    
                except Exception as e:
                    print(f"解析单个话题时出错: {e}")
                    continue
                    
        except Exception as e:
            print(f"搜索话题时出错: {e}")
    
    def is_within_time_range(self, time_str):
        """检查时间是否在指定范围内"""
        try:
            # 小红书的时间格式可能是 "1天前", "2小时前" 等
            if "天前" in time_str:
                days_ago = int(re.search(r'(\d+)天前', time_str).group(1))
                return days_ago <= self.days
            elif "小时前" in time_str:
                hours_ago = int(re.search(r'(\d+)小时前', time_str).group(1))
                return hours_ago <= self.days * 24
            elif "分钟前" in time_str:
                minutes_ago = int(re.search(r'(\d+)分钟前', time_str).group(1))
                return minutes_ago <= self.days * 24 * 60
            else:
                # 如果是具体日期，需要解析
                return True
        except:
            return True  # 如果无法解析时间，默认包含
    
    def save_to_csv(self, filename=None):
        """保存数据到CSV文件"""
        if filename is None:
            filename = f"xiaohongshu_{self.keyword}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # 合并数据
        all_data = self.notes_data + self.topics_data
        
        if not all_data:
            print("没有数据可保存")
            return
        
        # 写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['type', 'title/name', 'author', 'likes/count', 'publish_time', 'link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for item in all_data:
                if item['type'] == 'note':
                    writer.writerow({
                        'type': '笔记',
                        'title/name': item['title'],
                        'author': item['author'],
                        'likes/count': item['likes'],
                        'publish_time': item['publish_time'],
                        'link': item['link']
                    })
                else:
                    writer.writerow({
                        'type': '话题',
                        'title/name': item['name'],
                        'author': '',
                        'likes/count': item['count'],
                        'publish_time': '',
                        'link': item['link']
                    })
        
        print(f"数据已保存到: {filename}")
        return filename
    
    def save_to_json(self, filename=None):
        """保存数据到JSON文件"""
        if filename is None:
            filename = f"xiaohongshu_{self.keyword}_{datetime.now().strftime('%Y%m%d')}.json"
        
        # 合并数据
        all_data = {
            "keyword": self.keyword,
            "search_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "time_range_days": self.days,
            "notes": self.notes_data,
            "topics": self.topics_data
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(all_data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filename}")
        return filename
    
    def run(self):
        """运行爬虫"""
        try:
            print("开始运行小红书爬虫...")
            self.setup_driver()
            
            # 搜索笔记
            print("正在搜索笔记...")
            self.search_notes()
            
            # 搜索话题
            print("正在搜索话题...")
            self.search_topics()
            
            print(f"共找到 {len(self.notes_data)} 个笔记和 {len(self.topics_data)} 个话题")
            
            # 保存数据
            csv_file = self.save_to_csv()
            json_file = self.save_to_json()
            
            return {
                "notes_count": len(self.notes_data),
                "topics_count": len(self.topics_data),
                "csv_file": csv_file,
                "json_file": json_file
            }
            
        except Exception as e:
            print(f"运行爬虫时出错: {e}")
            return None
        finally:
            self.close_driver()


def main():
    """主函数"""
    keyword = input("请输入搜索关键词: ").strip()
    if not keyword:
        print("关键词不能为空")
        return
    
    try:
        days = int(input("请输入时间范围(天，默认15天): ") or "15")
    except ValueError:
        days = 15
    
    scraper = XiaohongshuScraper(keyword, days)
    result = scraper.run()
    
    if result:
        print(f"\n爬虫运行完成!")
        print(f"找到 {result['notes_count']} 个笔记")
        print(f"找到 {result['topics_count']} 个话题")
        print(f"CSV文件: {result['csv_file']}")
        print(f"JSON文件: {result['json_file']}")
    else:
        print("爬虫运行失败")


if __name__ == "__main__":
    main()