import requests
from bs4 import BeautifulSoup
import json
import re

class Post:
    def __init__(self, channel, post_id):
        self.channel = channel
        self.post_id = post_id
        self._fetch_post_data()

    def _fetch_post_data(self):
        url = f'https://t.me/{self.channel}/{self.post_id}?embed=1&mode=tme'
        response = requests.get(url)
        self.soup = BeautifulSoup(response.text, 'html.parser')

    @property
    def images(self):
        images = []
        styles = self.soup.find_all('div', style=True)
        for style in styles:
            if 'background-image:url' in style['style'] and 'video_thumb' not in style.get('class', []):
                url = re.search(r"url\('(.+?)'\)", style['style'])
                if url:
                    images.append(url.group(1))
        return json.dumps(images)

    @property
    def videos(self):
        videos = []
        video_tags = self.soup.find_all('video', src=True)
        for video in video_tags:
            videos.append(video['src'])
        return json.dumps(videos)

    @property
    def vid_thumbs(self):
        thumbs = []
        thumb_tags = self.soup.find_all('i', class_='tgme_widget_message_video_thumb')
        for thumb in thumb_tags:
            url = re.search(r"url\('(.+?)'\)", thumb['style'])
            if url:
                thumbs.append(url.group(1))
        return json.dumps(thumbs)

    @property
    def content(self):
        message_div = self.soup.find('div', class_='tgme_widget_message_text')
        return message_div.text if message_div else None

    @property
    def date(self):
        time_elem = self.soup.find('time', class_='datetime')
        return time_elem.text if time_elem else None

    @property
    def views(self):
        views_span = self.soup.find('span', class_='tgme_widget_message_views')
        return views_span.text if views_span else None

class TGView:
    def __init__(self, channel):
        self.channel = channel.replace("@", "") if channel.startswith("@") else channel
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self._fetch_data()
        self._fetch_channel_posts()

    def _fetch_data(self):
        url = f'https://t.me/{self.channel}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        self.soup = BeautifulSoup(response.text, 'html.parser')

    def _fetch_channel_posts(self):
        url = f'https://t.me/s/{self.channel}'
        response = requests.get(url, headers=self.headers)
        self.posts_soup = BeautifulSoup(response.text, 'html.parser')

    @property
    def images(self):
        images = []
        # Find all photo wrap links
        photo_links = self.soup.find_all('a', class_=lambda x: x and 'tgme_widget_message_photo_wrap' in x)
        
        # Extract URLs from style attributes
        for link in photo_links:
            if 'style' in link.attrs:
                url = re.search(r"background-image:url\('(.*?)'\)", link['style'])
                if url:
                    images.append(url.group(1))
        
        # Return as JSON string
        return json.dumps(images, ensure_ascii=False)
        
    @property
    def videos(self):
        videos = []
        video_tags = self.posts_soup.find_all('video', src=True)
        for video in video_tags:
            videos.append(video['src'])
        return json.dumps(videos)

    @property
    def vid_thumbs(self):
        thumbs = []
        thumb_tags = self.posts_soup.find_all('i', class_='tgme_widget_message_video_thumb')
        for thumb in thumb_tags:
            url = re.search(r"url\('(.+?)'\)", thumb['style'])
            if url:
                thumbs.append(url.group(1))
        return json.dumps(thumbs)

    @property
    def channel_name(self):
        meta = self.soup.find('meta', property='og:title')
        return meta['content'] if meta else None

    @property
    def channel_profile(self):
        meta = self.soup.find('meta', property='og:image')
        return meta['content'] if meta else None

    @property
    def channel_description(self):
        meta = self.soup.find('meta', property='og:description')
        return meta['content'] if meta else None

    @property
    def channel_subs(self):
        subscribers_div = self.soup.find('div', class_='tgme_page_extra')
        return subscribers_div.text.strip() if subscribers_div else None

    @property
    def channel_latest_message(self):
        return LatestMessage(self.channel)

    def post(self, post_id):
        return Post(self.channel, post_id)

def channel(channel_username):
    return TGView(channel_username)
