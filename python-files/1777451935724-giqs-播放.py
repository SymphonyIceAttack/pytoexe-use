#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻听音乐 - 多平台音乐播放器 (终极版)
- 网易云/QQ/酷狗全量搜索，无VIP过滤
- 独立桌面歌词窗口：呼吸动画，已播/未播歌词颜色分区，透明度/字号调节
- 四套皮肤一键切换（深邃深空、素白极简、暮光暖橙、护眼墨绿）
- 系统托盘：关闭窗口隐藏到托盘，右键菜单可显示、开关歌词、退出
- 进度条拖动、封面显示、播放列表管理
"""

import subprocess, sys, os, json, time, threading, tempfile, re, hashlib, math
from pathlib import Path
from io import BytesIO

# ================= 自动安装依赖 =================
def install_dependencies():
    packages = {
        'requests': 'requests',
        'pygame': 'pygame',
        'PIL': 'Pillow',
        'pystray': 'pystray'
    }
    missing = {}
    for imp_name, pip_name in packages.items():
        try:
            __import__(imp_name)
        except ImportError:
            missing[imp_name] = pip_name

    if missing:
        print("缺少依赖，正在使用清华镜像安装...")
        for imp, pip in missing.items():
            print(f"  安装 {pip} ...")
            cmd = [sys.executable, '-m', 'pip', 'install', pip, '-q',
                   '--disable-pip-version-check',
                   '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple/']
            try:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  {pip} 安装成功")
            except Exception as e:
                print(f"  {pip} 安装失败: {e}")
                print(f"  请手动执行: pip install {pip}")
                if imp == 'pystray':
                    print("  pystray 为托盘图标所需，不影响播放功能，可忽略。")
    print("依赖检查完成。\n")

install_dependencies()

import requests
import pygame
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import warnings
warnings.filterwarnings('ignore')

try:
    import pystray
    from pystray import MenuItem as Item
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("pystray 未安装，托盘功能关闭（不影响播放）。")

# ================= 全局配置 =================
TEMP_DIR = Path(tempfile.gettempdir()) / 'lightmusic_cache'
TEMP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = Path(tempfile.gettempdir()) / 'lightmusic_config.json'

THEMES = {
    "深邃深空": {
        'bg': '#1e1e2f', 'fg': '#cdd6f4', 'primary': '#89b4fa',
        'card_bg': '#313244', 'border': '#45475a', 'text_secondary': '#a6adc8',
        'progress_bg': '#45475a', 'progress_fill': '#89b4fa',
        'control_bar': '#181825', 'hover_row': '#45475a', 'selected_row': '#585b70',
        'lyric_bg': '#11111b', 'lyric_current': '#f9e2af', 'lyric_normal': '#a6adc8',
        'button_text': '#1e1e2f',
    },
    "素白极简": {
        'bg': '#f8f9fa', 'fg': '#2c3e50', 'primary': '#3498db',
        'card_bg': '#ffffff', 'border': '#e9ecef', 'text_secondary': '#7f8c8d',
        'progress_bg': '#e9ecef', 'progress_fill': '#3498db',
        'control_bar': '#ffffff', 'hover_row': '#f1f9ff', 'selected_row': '#d6eaf8',
        'lyric_bg': '#ffffff', 'lyric_current': '#e74c3c', 'lyric_normal': '#bdc3c7',
        'button_text': '#ffffff',
    },
    "暮光暖橙": {
        'bg': '#2b1e16', 'fg': '#fdedd6', 'primary': '#e67e22',
        'card_bg': '#3e2a1f', 'border': '#5a4233', 'text_secondary': '#c9a87c',
        'progress_bg': '#5a4233', 'progress_fill': '#e67e22',
        'control_bar': '#1f1510', 'hover_row': '#4d3528', 'selected_row': '#6e4c3a',
        'lyric_bg': '#1f1510', 'lyric_current': '#f1c40f', 'lyric_normal': '#bdc3c7',
        'button_text': '#2b1e16',
    },
    "护眼墨绿": {
        'bg': '#1e2e24', 'fg': '#d8f0e0', 'primary': '#2ecc71',
        'card_bg': '#2d3d32', 'border': '#4a5e4f', 'text_secondary': '#a3c9b2',
        'progress_bg': '#4a5e4f', 'progress_fill': '#2ecc71',
        'control_bar': '#16211a', 'hover_row': '#3b4d41', 'selected_row': '#51685a',
        'lyric_bg': '#121a15', 'lyric_current': '#f1c40f', 'lyric_normal': '#bdc3c7',
        'button_text': '#1e2e24',
    }
}
DEFAULT_THEME = "深邃深空"

DEFAULT_CONFIG = {
    "theme": DEFAULT_THEME,
    "lyrics_settings": {
        "font_size": 16,
        "bg_color": THEMES[DEFAULT_THEME]['lyric_bg'],
        "current_color": THEMES[DEFAULT_THEME]['lyric_current'],
        "played_color": "#8e8e8e",
        "unplayed_color": "#ffffff",
        "normal_color": THEMES[DEFAULT_THEME]['lyric_normal'],
        "width": 600,
        "height": 180,
        "alpha": 0.9,
    }
}

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

# ================= 音乐API（无VIP过滤） =================
class MusicAPI:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://music.163.com/',
    }

    @staticmethod
    def search_netease(keyword, limit=30):
        results = []
        try:
            url = 'https://music.163.com/api/search/get'
            params = {'s': keyword, 'type': 1, 'limit': limit, 'offset': 0}
            resp = requests.get(url, params=params, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('code') == 200:
                for song in data.get('result', {}).get('songs', []):
                    artists = ', '.join([a.get('name', '') for a in song.get('artists', [])])
                    results.append({
                        'id': str(song.get('id')),
                        'name': song.get('name', '未知'),
                        'artist': artists or '未知',
                        'album': song.get('album', {}).get('name', ''),
                        'platform': 'netease',
                        'duration': song.get('duration', 0) // 1000,
                        'cover': song.get('album', {}).get('picUrl', ''),
                    })
        except Exception as e:
            print(f"网易云搜索错误: {e}")
        return results

    @staticmethod
    def search_qq(keyword, limit=30):
        results = []
        try:
            url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp'
            params = {'w': keyword, 'n': limit, 'p': 1, 'format': 'json', 't': 0, 'aggr': 1, 'lossless': 0, 'cr': 1}
            resp = requests.get(url, params=params, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                for song in data.get('data', {}).get('song', {}).get('list', []):
                    artists = ', '.join([s.get('name', '') for s in song.get('singer', [])])
                    results.append({
                        'id': str(song.get('songmid', '')),
                        'name': song.get('songname', '未知'),
                        'artist': artists or '未知',
                        'album': song.get('albumname', ''),
                        'platform': 'qq',
                        'duration': song.get('interval', 0),
                        'cover': f"https://y.qq.com/music/photo_new/T002R300x300M000{song.get('albummid', '')}.jpg",
                    })
        except Exception as e:
            print(f"QQ音乐搜索错误: {e}")
        return results

    @staticmethod
    def search_kugou(keyword, limit=30):
        results = []
        try:
            url = 'http://mobilecdn.kugou.com/api/v3/search/song'
            params = {'format': 'json', 'keyword': keyword, 'page': 1, 'pagesize': limit, 'showtype': 1}
            resp = requests.get(url, params=params, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('status') == 1:
                for song in data.get('data', {}).get('info', []):
                    results.append({
                        'id': song.get('hash', ''),
                        'name': song.get('songname', '未知'),
                        'artist': song.get('singername', '未知'),
                        'album': song.get('album_name', ''),
                        'platform': 'kugou',
                        'duration': song.get('duration', 0),
                        'cover': song.get('album_img', '').replace('{size}', '400') if song.get('album_img') else '',
                        'extra_hash': song.get('hash', ''),
                    })
        except Exception as e:
            print(f"酷狗搜索错误: {e}")
        return results

    @staticmethod
    def get_netease_url(song_id):
        try:
            url = f'https://music.163.com/api/song/enhance/player/url?id={song_id}&ids=[{song_id}]&br=320000'
            resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('code') == 200:
                songs = data.get('data', [])
                if songs and songs[0].get('url'):
                    return songs[0]['url'], songs[0].get('br', 320000)
        except: pass
        return None, None

    @staticmethod
    def get_qq_url(song_mid):
        try:
            payload = {
                "req_0": {
                    "module": "vkey.GetVkeyServer",
                    "method": "CgiGetVkey",
                    "param": {"guid": "10000", "songmid": [song_mid], "songtype": [0], "uin": "0", "loginflag": 1, "platform": "20"}
                }
            }
            resp = requests.post('https://u.y.qq.com/cgi-bin/musicu.fcg', json=payload, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            midurlinfo = data.get('req_0', {}).get('data', {}).get('midurlinfo', [])
            sip = data.get('req_0', {}).get('data', {}).get('sip', [])
            if midurlinfo and midurlinfo[0].get('purl') and sip:
                return sip[0] + midurlinfo[0]['purl'], 128000
        except: pass
        return None, None

    @staticmethod
    def get_kugou_url(song_hash):
        try:
            url = f'http://mobilecdn.kugou.com/api/v3/track/info?format=json&hash={song_hash}'
            resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('status') == 1:
                info = data.get('data', {})
                play_url = info.get('play_url') or info.get('url', '')
                if play_url:
                    return play_url, info.get('bitrate', 128000)
        except: pass
        return None, None

    @staticmethod
    def get_netease_lyric(song_id):
        try:
            url = f'https://music.163.com/api/song/lyric?id={song_id}&lv=1&kv=1&tv=-1'
            resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('code') == 200:
                return data.get('lrc', {}).get('lyric', '')
        except: pass
        return ''

    @staticmethod
    def get_qq_lyric(song_mid):
        try:
            url = f'https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid={song_mid}&format=json&nobase64=1'
            headers = {**MusicAPI.HEADERS, 'Referer': 'https://y.qq.com/'}
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            if data.get('code') == 0:
                lyric = data.get('lyric', '')
                if lyric and '[' in lyric: return lyric
        except: pass
        return ''

    @staticmethod
    def get_kugou_lyric(song_hash, duration):
        try:
            url = f'http://krcs.kugou.com/search?ver=1&man=yes&client=mobi&keyword=&duration={duration}&hash={song_hash}'
            resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=10)
            data = resp.json()
            if data.get('status') == 200 and data.get('candidates'):
                lyric_id = data['candidates'][0].get('id')
                if lyric_id:
                    lrc_url = f'http://lyrics.kugou.com/download?ver=1&client=pc&id={lyric_id}&accesskey=&fmt=lrc&charset=utf8'
                    lrc_resp = requests.get(lrc_url, headers=MusicAPI.HEADERS, timeout=10)
                    lrc_data = lrc_resp.json()
                    if lrc_data.get('status') == 200:
                        return lrc_data.get('content', '')
        except: pass
        return ''

# ================= 歌词解析 =================
class LyricParser:
    @staticmethod
    def parse(lrc_text):
        if not lrc_text: return []
        lines = lrc_text.strip().split('\n')
        result = []
        time_pat = re.compile(r'\[(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\]')
        for line in lines:
            matches = time_pat.findall(line)
            if not matches: continue
            text = time_pat.sub('', line).strip()
            if not text: continue
            for m in matches:
                min = int(m[0])
                sec = int(m[1])
                ms = int(m[2])*10 if m[2] else 0
                total = min*60000 + sec*1000 + ms
                result.append((total, text))
        result.sort(key=lambda x: x[0])
        seen = set()
        unique = []
        for t, txt in result:
            if t not in seen:
                seen.add(t)
                unique.append((t, txt))
        return unique

    @staticmethod
    def get_current_line(lyric_data, pos_ms):
        if not lyric_data: return -1
        for i in range(len(lyric_data)-1, -1, -1):
            if lyric_data[i][0] <= pos_ms:
                return i
        return -1

# ================= 音乐播放器 =================
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.7)
        self._current_song = None
        self._is_playing = False
        self._is_paused = False
        self._volume = 0.7
        self._on_song_end_cb = None
        self._check_timer = None
        self._start_time = 0
        self._pause_pos = 0
        self._total_dur = 0
        self._temp_files = []
        self._current_file = None
        self._root = None

    def set_on_song_end(self, cb): self._on_song_end_cb = cb

    def play(self, url, song_info, total_dur=None, start_sec=0.0):
        self.stop()
        try:
            resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=30, stream=True)
            if resp.status_code != 200: return False
            temp = TEMP_DIR / f"song_{hashlib.md5(url.encode()).hexdigest()[:12]}.mp3"
            with open(temp, 'wb') as f:
                for chunk in resp.iter_content(8192): f.write(chunk)
            self._temp_files.append(temp)
            if len(self._temp_files) > 20:
                old = self._temp_files.pop(0)
                try: os.remove(old)
                except: pass
            pygame.mixer.music.load(str(temp))
            pygame.mixer.music.play(start=start_sec)
            pygame.mixer.music.set_volume(self._volume)
            self._current_song = song_info
            self._is_playing = True
            self._is_paused = False
            self._start_time = time.time() - start_sec
            self._pause_pos = 0
            self._total_dur = total_dur or song_info.get('duration', 0)
            self._current_file = str(temp)
            self._start_check_timer()
            return True
        except Exception as e:
            print(f"播放错误: {e}")
            self._is_playing = False
            return False

    def seek(self, seconds):
        if not self._is_playing or not self._current_file: return
        try:
            was_paused = self._is_paused
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self._current_file)
            pygame.mixer.music.play(start=seconds)
            pygame.mixer.music.set_volume(self._volume)
            self._start_time = time.time() - seconds
            self._pause_pos = 0
            if was_paused: pygame.mixer.music.pause()
            self._is_paused = was_paused
        except: pass

    def _start_check_timer(self):
        if self._check_timer: return
        def check():
            while self._is_playing:
                if not pygame.mixer.music.get_busy() and not self._is_paused and self._is_playing:
                    self._is_playing = False
                    if self._on_song_end_cb:
                        if self._root: self._root.after(100, self._on_song_end_cb)
                        else: self._on_song_end_cb()
                    break
                time.sleep(0.3)
        self._check_timer = threading.Thread(target=check, daemon=True)
        self._check_timer.start()

    def pause(self):
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            self._pause_pos += (time.time() - self._start_time)*1000

    def resume(self):
        if self._is_playing and self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            self._start_time = time.time()

    def stop(self):
        self._is_playing = False
        self._is_paused = False
        self._pause_pos = 0
        self._start_time = 0
        self._current_file = None
        try: pygame.mixer.music.stop(); pygame.mixer.music.unload()
        except: pass

    def set_volume(self, v): self._volume = max(0, min(1, v)); pygame.mixer.music.set_volume(self._volume)
    def get_position(self):
        if not self._is_playing: return 0
        if self._is_paused: return int(self._pause_pos)
        return int(self._pause_pos + (time.time() - self._start_time)*1000)
    def get_duration(self): return self._total_dur*1000 if self._total_dur else 0
    @property
    def is_playing(self): return self._is_playing
    @property
    def is_paused(self): return self._is_paused
    @property
    def current_song(self): return self._current_song
    @property
    def volume(self): return self._volume
    def cleanup(self):
        self.stop()
        for f in self._temp_files:
            try: os.remove(f)
            except: pass
        self._temp_files.clear()

# ================= 桌面歌词窗口（独立窗口） =================
class DesktopLyricsWindow:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.lyric_data = []
        self.current_index = -1
        self.is_visible = False
        self.drag_x = self.drag_y = 0
        self._update_job = None
        self._anim_job = None
        self.player = None
        self.anim_start = 0
        self.settings = {
            'font_size': 16, 'bg_color': '#11111b', 'current_color': '#f9e2af',
            'played_color': '#8e8e8e', 'unplayed_color': '#ffffff',
            'normal_color': '#a6adc8', 'width': 600, 'height': 180, 'alpha': 0.9
        }

    def set_player(self, p): self.player = p

    def apply_settings(self):
        if self.window and self.window.winfo_exists():
            self.window.configure(bg=self.settings['bg_color'])
            self.window.attributes('-alpha', self.settings['alpha'])
            for child in self.window.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self.settings['bg_color'])
            self._update_colors()

    def _update_colors(self):
        if not self.lyric_data: return
        idx = self.current_index
        self.prev_label.configure(fg=self.settings['played_color'] if idx>0 else self.settings['normal_color'])
        self.current_label.configure(fg=self.settings['current_color'])
        self.next_label.configure(fg=self.settings['unplayed_color'] if idx+1<len(self.lyric_data) else self.settings['normal_color'])

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.deiconify()
            self.is_visible = True
            self.apply_settings()
            self._start_animation()
            self._start_update_loop()
            return
        self.window = tk.Toplevel(self.root)
        self.window.title('桌面歌词')
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', self.settings['alpha'])
        w, h = self.settings['width'], self.settings['height']
        x = (self.window.winfo_screenwidth()-w)//2
        y = self.window.winfo_screenheight()-h-80
        self.window.geometry(f'{w}x{h}+{x}+{y}')
        self.window.configure(bg=self.settings['bg_color'])
        main = tk.Frame(self.window, bg=self.settings['bg_color'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        self.prev_label = tk.Label(main, text='', font=('微软雅黑',11), fg=self.settings['played_color'],
                                   bg=self.settings['bg_color'], anchor='center')
        self.prev_label.pack(fill=tk.X, pady=3)
        self.current_label = tk.Label(main, text='等待播放...', font=('微软雅黑', self.settings['font_size'], 'bold'),
                                      fg=self.settings['current_color'], bg=self.settings['bg_color'], anchor='center')
        self.current_label.pack(fill=tk.X, pady=5)
        self.next_label = tk.Label(main, text='', font=('微软雅黑',11), fg=self.settings['unplayed_color'],
                                   bg=self.settings['bg_color'], anchor='center')
        self.next_label.pack(fill=tk.X, pady=3)
        self.song_info_label = tk.Label(main, text='', font=('微软雅黑',9), fg='#888',
                                        bg=self.settings['bg_color'], anchor='center')
        self.song_info_label.pack(fill=tk.X, pady=2)
        for wgt in [self.window, main, self.prev_label, self.current_label, self.next_label, self.song_info_label]:
            wgt.bind('<ButtonPress-1>', self._drag_start)
            wgt.bind('<B1-Motion>', self._drag_move)
            wgt.bind('<Button-3>', self._right_click)
        close_btn = tk.Label(self.window, text='✕', font=('Arial',10), fg='#666',
                             bg=self.settings['bg_color'], cursor='hand2')
        close_btn.place(x=w-25, y=2)
        close_btn.bind('<Button-1>', lambda e: self.hide())
        close_btn.bind('<Enter>', lambda e: close_btn.configure(fg='#fff'))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(fg='#666'))
        self.is_visible = True
        self._start_animation()
        self._start_update_loop()

    def hide(self):
        if self.window: self.window.withdraw()
        self.is_visible = False
        if self._update_job: self.root.after_cancel(self._update_job); self._update_job=None
        if self._anim_job: self.root.after_cancel(self._anim_job); self._anim_job=None

    def toggle(self):
        if self.is_visible: self.hide()
        else: self.show()

    def set_lyric_data(self, data):
        self.lyric_data = data
        self.current_index = -1

    def update_song_info(self, song):
        if self.window and song:
            text = f"{song.get('name','')} - {song.get('artist','')}"
            self.song_info_label.configure(text=text[:60])

    def _start_update_loop(self):
        def update():
            if not self.is_visible or not self.window: return
            if self.player and self.player.is_playing and self.lyric_data:
                pos = self.player.get_position()
                new_idx = LyricParser.get_current_line(self.lyric_data, pos)
                if new_idx != self.current_index:
                    self.current_index = new_idx
                    self._update_display()
            self._update_job = self.root.after(200, update)
        self._update_job = self.root.after(200, update)

    def _start_animation(self):
        self.anim_start = time.time()
        def animate():
            if not self.is_visible or not self.window: return
            base = self.settings['font_size']
            offset = int(2 * math.sin(4*(time.time()-self.anim_start)))
            new_size = max(base+offset, 8)
            self.current_label.configure(font=('微软雅黑', new_size, 'bold'))
            self._anim_job = self.root.after(80, animate)
        self._anim_job = self.root.after(80, animate)

    def _update_display(self):
        if not self.lyric_data: return
        idx = self.current_index
        if idx < 0:
            self.prev_label.configure(text='')
            self.current_label.configure(text='♪ 前奏... ♪')
            self.next_label.configure(text=self.lyric_data[0][1] if self.lyric_data else '')
        else:
            self.current_label.configure(text=self.lyric_data[idx][1] if idx<len(self.lyric_data) else '')
            self.prev_label.configure(text=self.lyric_data[idx-1][1] if idx>0 else '')
            self.next_label.configure(text=self.lyric_data[idx+1][1] if idx+1<len(self.lyric_data) else '')
        self._update_colors()

    def _drag_start(self, event):
        self.drag_x, self.drag_y = event.x_root, event.y_root

    def _drag_move(self, event):
        dx = event.x_root - self.drag_x; dy = event.y_root - self.drag_y
        x = self.window.winfo_x() + dx; y = self.window.winfo_y() + dy
        self.window.geometry(f'+{x}+{y}')
        self.drag_x, self.drag_y = event.x_root, event.y_root

    def _right_click(self, event):
        menu = tk.Menu(self.window, tearoff=0, bg='#333', fg='#fff')
        menu.add_command(label='隐藏歌词', command=self.hide)
        menu.add_separator()
        menu.add_command(label='歌词设置...', command=lambda: self.root.event_generate('<<OpenSettings>>'))
        menu.add_separator()
        menu.add_command(label='关闭', command=self.hide)
        menu.post(event.x_root, event.y_root)

    def destroy(self):
        self.hide()
        if self.window: self.window.destroy(); self.window = None

# ================= 设置面板 =================
class SettingsWindow:
    def __init__(self, master, config, on_apply):
        self.win = tk.Toplevel(master)
        self.win.title('⚙ 设置')
        self.win.geometry('400x500')
        self.win.configure(bg='#2d2d2d')
        self.config = config
        self.on_apply = on_apply
        self._create_widgets()

    def _create_widgets(self):
        nb = ttk.Notebook(self.win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 皮肤页
        skin = tk.Frame(nb, bg='#2d2d2d')
        nb.add(skin, text='皮肤')
        tk.Label(skin, text='选择主题', fg='white', bg='#2d2d2d').pack(pady=10)
        self.theme_var = tk.StringVar(value=self.config.get('theme', DEFAULT_THEME))
        for name in THEMES:
            tk.Radiobutton(skin, text=name, variable=self.theme_var, value=name,
                           bg='#2d2d2d', fg='white', selectcolor='#555', activebackground='#444').pack(anchor=tk.W)

        # 歌词页
        ly = tk.Frame(nb, bg='#2d2d2d')
        nb.add(ly, text='歌词效果')
        ls = self.config.get('lyrics_settings', {})
        self.ly_vars = {}

        tk.Label(ly, text='字体大小', fg='white', bg='#2d2d2d').pack(pady=2)
        self.ly_vars['font_size'] = tk.IntVar(value=ls.get('font_size',16))
        tk.Scale(ly, from_=10, to=30, variable=self.ly_vars['font_size'], bg='#2d2d2d', fg='white').pack(pady=2)

        tk.Label(ly, text='窗口透明度 (%)', fg='white', bg='#2d2d2d').pack(pady=2)
        self.ly_vars['alpha'] = tk.IntVar(value=int(ls.get('alpha',0.9)*100))
        tk.Scale(ly, from_=30, to=100, variable=self.ly_vars['alpha'], bg='#2d2d2d', fg='white').pack(pady=2)

        colors = ['current_color', 'played_color', 'unplayed_color', 'bg_color']
        labels = ['当前歌词', '已播歌词', '未播歌词', '背景颜色']
        for key, label in zip(colors, labels):
            frame = tk.Frame(ly, bg='#2d2d2d')
            frame.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(frame, text=label, fg='white', bg='#2d2d2d').pack(side=tk.LEFT)
            var = tk.StringVar(value=ls.get(key, '#ffffff'))
            self.ly_vars[key] = var
            entry = tk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT, padx=5)
            btn = tk.Button(frame, text='选色', bg='#555', fg='white', command=lambda v=var: self._pick_color(v))
            btn.pack(side=tk.LEFT)

        # 按钮
        btn_frame = tk.Frame(self.win, bg='#2d2d2d')
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='应用', bg='#89b4fa', fg='black', width=10, command=self._apply).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='确定', bg='#89b4fa', fg='black', width=10, command=self._ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='取消', bg='#555', fg='white', width=10, command=self.win.destroy).pack(side=tk.LEFT, padx=5)

    def _pick_color(self, var):
        color = colorchooser.askcolor(color=var.get())
        if color[1]: var.set(color[1])

    def _apply(self):
        new_config = self.config.copy()
        new_config['theme'] = self.theme_var.get()
        ls = {}
        for k, v in self.ly_vars.items():
            if k == 'alpha': ls[k] = v.get()/100.0
            elif k == 'font_size': ls[k] = v.get()
            else: ls[k] = v.get()
        new_config['lyrics_settings'] = ls
        save_config(new_config)
        self.on_apply(new_config)

    def _ok(self):
        self._apply()
        self.win.destroy()

# ================= 主应用 =================
class MusicApp:
    def __init__(self):
        self.config = load_config()
        self.theme = THEMES.get(self.config.get('theme', DEFAULT_THEME), THEMES[DEFAULT_THEME])
        self.lyric_settings = self.config.get('lyrics_settings', {})

        self.root = tk.Tk()
        self.root.title('轻听音乐')
        self.root.geometry('1000x680')
        self.root.minsize(800, 550)
        self.root.configure(bg=self.theme['bg'])

        self.player = MusicPlayer()
        self.player.set_on_song_end(self._on_song_end)
        self.player._root = self.root

        self.lyrics_window = DesktopLyricsWindow(self.root)
        self.lyrics_window.set_player(self.player)
        self._apply_lyric_settings()

        self.search_results = []
        self.playlist = []
        self.current_playlist_index = -1
        self.current_lyric_data = []
        self.is_searching = False
        self.cover_image_ref = None

        self._create_widgets()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._start_progress_update()
        self.root.bind('<<OpenSettings>>', self._open_settings)
        if TRAY_AVAILABLE:
            self._create_tray_icon()

    def _apply_lyric_settings(self):
        self.lyrics_window.settings.update(self.lyric_settings)
        if self.lyrics_window.is_visible:
            self.lyrics_window.apply_settings()

    def _on_close(self):
        if TRAY_AVAILABLE:
            self.root.withdraw()  # 隐藏到托盘
        else:
            self._quit_app()

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()

    def _quit_app(self):
        self.player.cleanup()
        self.lyrics_window.destroy()
        if TRAY_AVAILABLE and hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.destroy()
        try:
            for f in TEMP_DIR.glob('*'): os.remove(f)
            TEMP_DIR.rmdir()
        except: pass

    def _create_tray_icon(self):
        img = Image.new('RGB', (64,64), color='#89b4fa')
        menu = pystray.Menu(
            Item('显示主窗口', self._show_window, default=True),
            Item('桌面歌词', self.lyrics_window.toggle, checked=lambda item: self.lyrics_window.is_visible),
            pystray.Menu.SEPARATOR,
            Item('退出程序', self._quit_app)
        )
        self.tray_icon = pystray.Icon("lightmusic", img, "轻听音乐", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _open_settings(self, event=None):
        SettingsWindow(self.root, self.config, self._on_config_changed)

    def _on_config_changed(self, new_config):
        self.config = new_config
        old_theme = self.theme
        self.theme = THEMES.get(new_config['theme'], THEMES[DEFAULT_THEME])
        self.lyric_settings = new_config.get('lyrics_settings', {})
        self._apply_lyric_settings()
        if self.theme != old_theme:
            self.root.configure(bg=self.theme['bg'])
            messagebox.showinfo('提示', '主题已应用，建议重启获得最佳效果。')

    # ---------- UI 构建（使用self.theme） ----------
    def _create_widgets(self):
        t = self.theme
        top = tk.Frame(self.root, bg=t['card_bg'], height=70)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        inner_top = tk.Frame(top, bg=t['card_bg'])
        inner_top.pack(fill=tk.X, padx=20, pady=12)
        tk.Label(inner_top, text='🎵 轻听', font=('微软雅黑',16,'bold'), fg=t['primary'], bg=t['card_bg']).pack(side=tk.LEFT, padx=(0,15))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(inner_top, textvariable=self.search_var, font=('微软雅黑',11),
                                bg=t['border'], fg=t['fg'], relief=tk.FLAT, bd=0, insertbackground=t['fg'])
        search_entry.pack(side=tk.LEFT, padx=5, ipady=6, fill=tk.X, expand=True)
        search_entry.bind('<Return>', lambda e: self._do_search())
        tk.Button(inner_top, text='🔍 搜索', font=('微软雅黑',10,'bold'), bg=t['primary'], fg=t['button_text'],
                  relief=tk.FLAT, cursor='hand2', padx=15, pady=5, command=self._do_search).pack(side=tk.LEFT, padx=5)
        self.platform_var = tk.StringVar(value='all')
        pf_frame = tk.Frame(inner_top, bg=t['card_bg'])
        pf_frame.pack(side=tk.LEFT, padx=10)
        platforms = {'netease': '🎵 网易', 'qq': '🎶 QQ', 'kugou': '🎧 酷狗', 'all': '🌐 全部'}
        for key, text in platforms.items():
            tk.Radiobutton(pf_frame, text=text, variable=self.platform_var, value=key,
                           font=('微软雅黑',9), bg=t['card_bg'], fg=t['fg'], activebackground=t['card_bg'],
                           selectcolor=t['card_bg'], cursor='hand2', relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(inner_top, text='⚙', font=('Arial',12), bg=t['card_bg'], fg=t['fg'], relief=tk.FLAT,
                  cursor='hand2', padx=5, command=self._open_settings).pack(side=tk.LEFT, padx=10)

        tk.Frame(self.root, bg=t['border'], height=1).pack(fill=tk.X)

        content = tk.Frame(self.root, bg=t['bg'])
        content.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(content, bg=t['bg'])
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20,10), pady=15)
        res_header = tk.Frame(left, bg=t['bg'])
        res_header.pack(fill=tk.X)
        self.result_label = tk.Label(res_header, text='搜索结果', font=('微软雅黑',12,'bold'), fg=t['fg'], bg=t['bg'])
        self.result_label.pack(side=tk.LEFT)
        self.result_count = tk.Label(res_header, text='', font=('微软雅黑',9), fg=t['text_secondary'], bg=t['bg'])
        self.result_count.pack(side=tk.LEFT, padx=10)

        tree_frame = tk.Frame(left, bg=t['card_bg'], highlightbackground=t['border'], highlightthickness=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        columns = ('name','artist','duration','platform')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15, selectmode='browse')
        self.tree.heading('name', text='歌曲'); self.tree.heading('artist', text='艺术家')
        self.tree.heading('duration', text='时长'); self.tree.heading('platform', text='平台')
        self.tree.column('name', width=240); self.tree.column('artist', width=160)
        self.tree.column('duration', width=60, anchor='center'); self.tree.column('platform', width=70, anchor='center')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background=t['card_bg'], foreground=t['fg'], fieldbackground=t['card_bg'])
        style.map('Treeview', background=[('selected', t['selected_row'])])
        style.configure('Treeview.Heading', background=t['card_bg'], foreground=t['fg'], borderwidth=0, font=('微软雅黑',9,'bold'))
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<Double-1>', self._on_tree_dbl)

        right = tk.Frame(content, bg=t['bg'], width=280)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,20), pady=15)
        right.pack_propagate(False)
        pl_header = tk.Frame(right, bg=t['bg'])
        pl_header.pack(fill=tk.X)
        tk.Label(pl_header, text='播放列表', font=('微软雅黑',12,'bold'), fg=t['fg'], bg=t['bg']).pack(side=tk.LEFT)
        clear_btn = tk.Label(pl_header, text='清空', fg=t['primary'], bg=t['bg'], cursor='hand2', font=('微软雅黑',9))
        clear_btn.pack(side=tk.RIGHT)
        clear_btn.bind('<Button-1>', lambda e: self._clear_playlist())
        list_frame = tk.Frame(right, bg=t['card_bg'], highlightbackground=t['border'], highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        self.playlist_box = tk.Listbox(list_frame, font=('微软雅黑',9), bg=t['card_bg'], fg=t['fg'],
                                       selectbackground=t['selected_row'], selectforeground=t['fg'],
                                       relief=tk.FLAT, bd=0, highlightthickness=0, selectmode=tk.SINGLE, activestyle='none')
        pl_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.playlist_box.yview)
        self.playlist_box.configure(yscrollcommand=pl_scroll.set)
        self.playlist_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        pl_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        self.playlist_box.bind('<Double-1>', self._on_plist_dbl)
        tk.Button(right, text='📝 桌面歌词', font=('微软雅黑',9), bg=t['primary'], fg=t['button_text'],
                  relief=tk.FLAT, cursor='hand2', padx=12, pady=5, command=self.lyrics_window.toggle).pack(fill=tk.X, pady=(10,5))
        tk.Button(right, text='➕ 添加到列表', font=('微软雅黑',9), bg=t['card_bg'], fg=t['fg'],
                  relief=tk.FLAT, cursor='hand2', padx=12, pady=5, command=self._add_to_playlist).pack(fill=tk.X)

        control = tk.Frame(self.root, bg=t['control_bar'], height=80)
        control.pack(fill=tk.X, side=tk.BOTTOM)
        control.pack_propagate(False)
        tk.Frame(control, bg=t['border'], height=1).pack(fill=tk.X)
        inner_ctrl = tk.Frame(control, bg=t['control_bar'])
        inner_ctrl.pack(fill=tk.X, padx=20, pady=10)
        self.cover_label = tk.Label(inner_ctrl, bg=t['control_bar'])
        self.cover_label.pack(side=tk.LEFT, padx=(0,10))
        self._set_default_cover()
        info_frame = tk.Frame(inner_ctrl, bg=t['control_bar'])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.now_playing_label = tk.Label(info_frame, text='未播放歌曲', font=('微软雅黑',11,'bold'), fg=t['fg'], bg=t['control_bar'])
        self.now_playing_label.pack(fill=tk.X)
        prog_frame = tk.Frame(info_frame, bg=t['control_bar'])
        prog_frame.pack(fill=tk.X, pady=(2,0))
        self.time_label = tk.Label(prog_frame, text='00:00 / 00:00', font=('Consolas',9), fg=t['text_secondary'], bg=t['control_bar'])
        self.time_label.pack(side=tk.LEFT, padx=(0,8))
        self.progress_canvas = tk.Canvas(prog_frame, height=6, bg=t['progress_bg'], highlightthickness=0, cursor='hand2')
        self.progress_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress_canvas.bind('<Button-1>', self._on_progress_click)
        btn_area = tk.Frame(inner_ctrl, bg=t['control_bar'])
        btn_area.pack(side=tk.RIGHT, padx=(15,0))
        self.prev_btn = tk.Button(btn_area, text='⏮', font=('Arial',14), bg=t['control_bar'], fg=t['fg'],
                                  relief=tk.FLAT, cursor='hand2', bd=0, padx=3, command=self._play_prev)
        self.prev_btn.pack(side=tk.LEFT, padx=2)
        self.play_pause_btn = tk.Button(btn_area, text='▶', font=('Arial',16), bg=t['primary'],
                                        fg=t['button_text'], relief=tk.FLAT, cursor='hand2', bd=0, padx=10, pady=3,
                                        command=self._toggle_play_pause)
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)
        self.next_btn = tk.Button(btn_area, text='⏭', font=('Arial',14), bg=t['control_bar'], fg=t['fg'],
                                  relief=tk.FLAT, cursor='hand2', bd=0, padx=3, command=self._play_next)
        self.next_btn.pack(side=tk.LEFT, padx=2)
        vol_frame = tk.Frame(btn_area, bg=t['control_bar'])
        vol_frame.pack(side=tk.LEFT, padx=(15,0))
        tk.Label(vol_frame, text='🔊', bg=t['control_bar']).pack(side=tk.LEFT)
        self.volume_scale = tk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=80,
                                     showvalue=0, bg=t['control_bar'], fg=t['fg'], troughcolor=t['progress_bg'],
                                     highlightthickness=0, bd=0, command=self._on_vol_change, cursor='hand2')
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT)

    def _set_default_cover(self):
        try:
            img = Image.new('RGB', (40,40), color=self.theme['progress_bg'])
            photo = ImageTk.PhotoImage(img)
            self.cover_label.configure(image=photo)
            self.cover_label.image = photo
        except: pass

    def _load_cover_async(self, url):
        if not url:
            self.root.after(0, self._set_default_cover)
            return
        def load():
            try:
                resp = requests.get(url, headers=MusicAPI.HEADERS, timeout=5)
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content)).resize((40,40), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.root.after(0, lambda: self._update_cover(photo))
                else:
                    self.root.after(0, self._set_default_cover)
            except:
                self.root.after(0, self._set_default_cover)
        threading.Thread(target=load, daemon=True).start()

    def _update_cover(self, photo):
        self.cover_label.configure(image=photo)
        self.cover_label.image = photo

    def _do_search(self):
        kw = self.search_var.get().strip()
        if not kw or self.is_searching: return
        self.is_searching = True
        self.result_label.configure(text='搜索中...')
        self.result_count.configure(text='')
        for item in self.tree.get_children(): self.tree.delete(item)
        def thread():
            plat = self.platform_var.get()
            results = []
            if plat in ('all','netease'): results.extend(MusicAPI.search_netease(kw))
            if plat in ('all','qq'): results.extend(MusicAPI.search_qq(kw))
            if plat in ('all','kugou'): results.extend(MusicAPI.search_kugou(kw))
            seen = set()
            unique = []
            for r in results:
                key = (r['name'].lower(), r['artist'].lower())
                if key not in seen:
                    seen.add(key)
                    unique.append(r)
            self.search_results = unique
            self.root.after(0, lambda: self._update_results(unique, kw))
        threading.Thread(target=thread, daemon=True).start()

    def _update_results(self, results, kw):
        self.is_searching = False
        self.result_label.configure(text='搜索结果')
        self.result_count.configure(text=f'找到 {len(results)} 首')
        for i, song in enumerate(results):
            dur = self._format_time(song.get('duration',0))
            plat = {'netease':'网易云','qq':'QQ音乐','kugou':'酷狗'}.get(song['platform'], song['platform'])
            self.tree.insert('', tk.END, iid=str(i), values=(song['name'][:35], song['artist'][:25], dur, plat))

    def _format_time(self, sec):
        if not sec: return '--:--'
        m, s = divmod(int(sec), 60)
        return f'{m:02d}:{s:02d}'

    def _on_tree_dbl(self, event):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx < len(self.search_results):
                self._add_to_plist_and_play(self.search_results[idx])

    def _on_plist_dbl(self, event):
        sel = self.playlist_box.curselection()
        if sel:
            idx = sel[0]
            if idx < len(self.playlist):
                self.current_playlist_index = idx
                self._play_song(self.playlist[idx])

    def _add_to_playlist(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx < len(self.search_results):
                self.playlist.append(self.search_results[idx])
                self._update_playlist()

    def _add_to_plist_and_play(self, song):
        # 检查是否已在播放列表
        for i, s in enumerate(self.playlist):
            if s['id'] == song['id'] and s['platform'] == song['platform']:
                self.current_playlist_index = i
                self._play_song(song)
                return
        self.playlist.append(song)
        self.current_playlist_index = len(self.playlist)-1
        self._update_playlist()
        self._play_song(song)

    def _play_song(self, song):
        self.now_playing_label.configure(text=f'⏳ {song["name"]} - {song["artist"]}')
        self._load_cover_async(song.get('cover',''))
        def thread():
            url = None
            if song['platform'] == 'netease': url, _ = MusicAPI.get_netease_url(song['id'])
            elif song['platform'] == 'qq': url, _ = MusicAPI.get_qq_url(song['id'])
            elif song['platform'] == 'kugou': url, _ = MusicAPI.get_kugou_url(song.get('extra_hash', song['id']))
            if not url:
                self.root.after(0, lambda: messagebox.showerror('错误', '无法获取播放链接（可能VIP/无版权）'))
                return
            lyric = ''
            if song['platform'] == 'netease': lyric = MusicAPI.get_netease_lyric(song['id'])
            elif song['platform'] == 'qq': lyric = MusicAPI.get_qq_lyric(song['id'])
            elif song['platform'] == 'kugou': lyric = MusicAPI.get_kugou_lyric(song.get('extra_hash', song['id']), song.get('duration',200))
            self.current_lyric_data = LyricParser.parse(lyric)
            success = self.player.play(url, song, song.get('duration',0))
            self.root.after(0, lambda: self._on_play_start(song, success))
        threading.Thread(target=thread, daemon=True).start()

    def _on_play_start(self, song, success):
        if success:
            self.now_playing_label.configure(text=f'🎶 {song["name"]} - {song["artist"]}')
            self.play_pause_btn.configure(text='⏸')
            self.lyrics_window.set_lyric_data(self.current_lyric_data)
            self.lyrics_window.update_song_info(song)
            if self.lyrics_window.is_visible: self.lyrics_window.current_index = -1
            self._highlight_playlist()
        else:
            self.now_playing_label.configure(text=f'❌ 播放失败: {song["name"]}')

    def _on_song_end(self):
        self.root.after(100, self._play_next)

    def _toggle_play_pause(self):
        if not self.player.is_playing:
            if self.playlist:
                if self.current_playlist_index < 0: self.current_playlist_index = 0
                self._play_song(self.playlist[self.current_playlist_index])
            return
        if self.player.is_paused:
            self.player.resume(); self.play_pause_btn.configure(text='⏸')
        else:
            self.player.pause(); self.play_pause_btn.configure(text='▶')

    def _play_next(self):
        if not self.playlist: return
        self.current_playlist_index = (self.current_playlist_index + 1) % len(self.playlist)
        self._play_song(self.playlist[self.current_playlist_index])
        self._update_playlist(); self._highlight_playlist()

    def _play_prev(self):
        if not self.playlist: return
        self.current_playlist_index = (self.current_playlist_index - 1) % len(self.playlist)
        self._play_song(self.playlist[self.current_playlist_index])
        self._update_playlist(); self._highlight_playlist()

    def _update_playlist(self):
        self.playlist_box.delete(0, tk.END)
        for s in self.playlist:
            icon = {'netease':'🎵','qq':'🎶','kugou':'🎧'}.get(s['platform'],'')
            text = f"{icon} {s['name']} - {s['artist']}"
            self.playlist_box.insert(tk.END, text[:45])
        self._highlight_playlist()

    def _clear_playlist(self):
        self.playlist.clear()
        self.current_playlist_index = -1
        self._update_playlist()

    def _highlight_playlist(self):
        if 0 <= self.current_playlist_index < len(self.playlist):
            self.playlist_box.selection_clear(0, tk.END)
            self.playlist_box.selection_set(self.current_playlist_index)
            self.playlist_box.see(self.current_playlist_index)

    def _start_progress_update(self):
        def update():
            if self.player.is_playing and not self.player.is_paused:
                pos = self.player.get_position(); dur = self.player.get_duration()
                if dur > 0:
                    self.time_label.configure(text=f'{self._format_ms(pos)} / {self._format_ms(dur)}')
                    self.progress_canvas.delete('all')
                    w = self.progress_canvas.winfo_width(); h = self.progress_canvas.winfo_height()
                    if w > 0:
                        fill = int((pos/dur)*w)
                        if fill > 0:
                            self._create_rounded(self.progress_canvas, 0, 0, fill, h, radius=3, fill=self.theme['progress_fill'], outline='')
            self.root.after(300, update)
        self.root.after(300, update)

    def _create_rounded(self, canvas, x1, y1, x2, y2, radius=4, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                  x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius,
                  x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
                  x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius,
                  x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _format_ms(self, ms):
        s = int(ms/1000); m, s = divmod(s,60)
        return f'{m:02d}:{s:02d}'

    def _on_progress_click(self, event):
        if not self.player.is_playing: return
        dur = self.player.get_duration()
        if dur <= 0: return
        w = self.progress_canvas.winfo_width()
        if w <= 0: return
        ratio = event.x / w
        self.player.seek(ratio * (dur/1000))

    def _on_vol_change(self, value):
        self.player.set_volume(int(value)/100)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    print("轻听音乐播放器启动中...")
    app = MusicApp()
    app.run()