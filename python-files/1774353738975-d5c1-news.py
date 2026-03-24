import requests
import random
import datetime
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from bs4 import BeautifulSoup  # 用于解析文章原文

# 加载环境变量
load_dotenv()

# NewsAPI配置
NEWS_API_KEY = "35551d756db24bbab6c8a3c6f9c0af36"
TOP_HEADLINES_URL = 'https://newsapi.org/v2/top-headlines'
EVERYTHING_URL = 'https://newsapi.org/v2/everything'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


# ==================== 新增：翻译功能 ====================
def translate_text(text, from_lang='en', to_lang='zh'):
    """免费翻译接口（英汉互译）"""
    if not text or len(text.strip()) == 0:
        return "无内容可翻译"

    try:
        # 使用免费公共翻译API
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": f"{from_lang}|{to_lang}"
        }
        response = requests.get(url, params=params, timeout=10)
        result = response.json()

        if result.get("responseStatus") == 200:
            return result["responseData"]["translatedText"]
        else:
            return "翻译失败，请重试"
    except:
        return "翻译服务异常，请检查网络"


def get_random_english_article():
    """获取随机英文文章"""
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'pageSize': 100,
        }
        response = requests.get(TOP_HEADLINES_URL, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        articles = []
        if data['status'] == 'ok':
            articles = data.get('articles', [])

        if not articles:
            today = datetime.date.today()
            params_everything = {
                'apiKey': NEWS_API_KEY,
                'q': 'general',
                'language': 'en',
                'from': (today - datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
                'pageSize': 100,
            }
            response2 = requests.get(EVERYTHING_URL, params=params_everything, headers=HEADERS)
            response2.raise_for_status()
            data2 = response2.json()
            if data2['status'] == 'ok':
                articles = data2.get('articles', [])

        if not articles:
            return None

        random_article = random.choice(articles)
        return {
            'title': random_article.get('title', 'No Title'),
            'source': random_article.get('source', {}).get('name', 'Unknown Source'),
            'published_at': random_article.get('publishedAt', 'Unknown Time'),
            'url': random_article.get('url', ''),
            'description': random_article.get('description', 'No Description')
        }

    except requests.exceptions.HTTPError as e:
        if '401' in str(e):
            messagebox.showerror("错误", "401未授权：API密钥无效/过期")
        elif '429' in str(e):
            messagebox.showerror("错误", "429请求超限：免费版今日请求次数已用完")
        else:
            messagebox.showerror("错误", f"HTTP错误：{e}")
    except Exception as e:
        messagebox.showerror("错误", f"获取文章失败：{str(e)}")
    return None


def get_article_content(url):
    """爬取文章原文"""
    if not url:
        return "No article URL available."

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content_tags = soup.find_all(
            ['p', 'article'],
            class_=['story-content', 'article-body', 'content__article-body', 'main-content', 'body-content']
        )

        if not content_tags:
            content_tags = soup.find_all('p')

        content = []
        for tag in content_tags:
            text = tag.get_text(strip=True)
            if text and len(text) > 50:
                content.append(text)

        if content:
            return '\n\n'.join(content)
        else:
            return "Failed to extract article content. Please open the link in browser:\n" + url

    except Exception as e:
        return f"Error fetching article content: {str(e)}\n\nPlease open the link in browser:\n{url}"


class EnglishReadingApp:
    """英语阅读助手GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("每日英语阅读助手（带翻译）")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)

        self.current_article = None
        self.original_content = ""  # 保存原文
        self.translated_content = ""  # 保存译文

        self.create_widgets()
        self.get_new_article()

    def create_widgets(self):
        """创建界面"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        # 功能按钮
        self.refresh_btn = ttk.Button(control_frame, text="🔄 获取新文章", command=self.get_new_article)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        self.translate_selected_btn = ttk.Button(control_frame, text="📝 翻译选中内容", command=self.translate_selected)
        self.translate_selected_btn.pack(side=tk.LEFT, padx=5)

        self.translate_all_btn = ttk.Button(control_frame, text="🌐 全文翻译/还原", command=self.toggle_translate)
        self.translate_all_btn.pack(side=tk.LEFT, padx=5)

        # 文章信息区
        info_frame = ttk.LabelFrame(self.root, text="文章信息", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.title_label = ttk.Label(info_frame, text="标题: ", font=("Arial", 12, "bold"), wraplength=1000)
        self.title_label.pack(anchor=tk.W, pady=2)

        self.meta_label = ttk.Label(info_frame, text="来源 / 时间: ", font=("Arial", 10))
        self.meta_label.pack(anchor=tk.W, pady=2)

        self.desc_label = ttk.Label(info_frame, text="摘要: ", font=("Arial", 10), wraplength=1000)
        self.desc_label.pack(anchor=tk.W, pady=2)

        # 文章内容区
        content_frame = ttk.LabelFrame(self.root, text="文章内容", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.content_text = scrolledtext.ScrolledText(
            content_frame, font=("Arial", 11), wrap=tk.WORD, bg="white", fg="black"
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.config(state=tk.DISABLED)

    def translate_selected(self):
        """翻译选中的文本"""
        try:
            # 获取选中内容
            selected_text = self.content_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if not selected_text.strip():
                messagebox.showinfo("提示", "请先选中需要翻译的文字！")
                return

            # 翻译
            translation = translate_text(selected_text)
            messagebox.showinfo("选中内容翻译", f"原文：\n{selected_text}\n\n译文：\n{translation}")
        except tk.TclError:
            messagebox.showinfo("提示", "请先选中需要翻译的文字！")

    def toggle_translate(self):
        """切换：全文翻译 / 显示原文"""
        if not self.original_content:
            messagebox.showinfo("提示", "暂无文章内容可翻译！")
            return

        self.content_text.config(state=tk.NORMAL)
        current = self.content_text.get(1.0, tk.END).strip()

        if current == self.original_content.strip():
            # 显示译文
            if not self.translated_content:
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, "正在翻译中，请稍候...")
                self.root.update()
                self.translated_content = translate_text(self.original_content)
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, self.translated_content)
        else:
            # 显示原文
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, self.original_content)

        self.content_text.config(state=tk.DISABLED)
        self.content_text.see(1.0)

    def get_new_article(self):
        """获取新文章"""
        self.refresh_btn.config(state=tk.DISABLED)
        self.root.update()
        self.clear_article_info()

        self.current_article = get_random_english_article()
        if self.current_article:
            self.update_article_info()
            self.load_article_content()
            self.translated_content = ""  # 重置译文
        else:
            messagebox.showinfo("提示", "暂无可用文章")

        self.refresh_btn.config(state=tk.NORMAL)

    def clear_article_info(self):
        """清空内容"""
        self.title_label.config(text="标题: 加载中...")
        self.meta_label.config(text="来源 / 时间: 加载中...")
        self.desc_label.config(text="摘要: 加载中...")
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, "加载文章内容中...")
        self.content_text.config(state=tk.DISABLED)
        self.original_content = ""

    def update_article_info(self):
        """更新文章信息"""
        self.title_label.config(text=f"标题: {self.current_article['title']}")
        self.meta_label.config(
            text=f"来源 / 时间: {self.current_article['source']} | {self.current_article['published_at']}")
        self.desc_label.config(text=f"摘要: {self.current_article['description']}")

    def load_article_content(self):
        """异步加载原文"""
        self.root.after(100, self._load_content_async)

    def _load_content_async(self):
        content = get_article_content(self.current_article['url'])
        self.original_content = content  # 保存原文

        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, content)
        self.content_text.config(state=tk.DISABLED)
        self.content_text.see(1.0)


if __name__ == '__main__':
    # 自动安装依赖
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        os.system("pip install beautifulsoup4")
        from bs4 import BeautifulSoup

    root = tk.Tk()
    app = EnglishReadingApp(root)
    root.mainloop()