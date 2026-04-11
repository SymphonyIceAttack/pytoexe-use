#!/usr/bin/env python3
"""
🎵 音乐下载器 - 输入歌名，下载 MP3
数据源：网易云音乐

用法:
  python3 music_dl.py "晴天"
  python3 music_dl.py -o ~/Music "周杰伦 稻香"
  python3 music_dl.py -y "起风了"       # 跳过选择，直接下载第一个
"""

import subprocess
import sys
import os
import json
import re
import shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "downloads"

HEADERS = {
    "Referer": "https://music.163.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}

QUALITY_MAP = {
    "low": 128000,
    "medium": 192000,
    "high": 320000,
    "lossless": 999000,
}


def api_post(path: str, data: dict) -> dict:
    """POST 请求网易云音乐 API"""
    url = f"https://music.163.com{path}"
    body = urlencode(data).encode("utf-8")
    req = Request(url, data=body, headers=HEADERS, method="POST")
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def search(query: str, limit: int = 8) -> list:
    """搜索歌曲"""
    res = api_post("/api/search/get", {"s": query, "type": 1, "limit": limit})
    if res.get("code") != 200:
        return []
    songs = res.get("result", {}).get("songs", [])
    results = []
    for s in songs:
        artists = ", ".join(a["name"] for a in s.get("artists", []))
        album = s.get("album", {}).get("name", "")
        duration = s.get("duration", 0)
        fee = s.get("fee", 0)
        results.append({
            "id": s["id"],
            "name": s["name"],
            "artists": artists,
            "album": album,
            "duration": duration,
            "fee": fee,
            "alias": s.get("alias", []),
        })
    return results


def get_url(song_id: int, quality: str = "high") -> str | None:
    """获取歌曲下载 URL"""
    br = QUALITY_MAP.get(quality, 320000)
    res = api_post(
        "/api/song/enhance/player/url",
        {"ids": f"[{song_id}]", "br": br}
    )
    if res.get("code") != 200:
        return None
    data_list = res.get("data", [])
    if not data_list:
        return None
    return data_list[0].get("url")


def download_file(url: str, filepath: str) -> bool:
    """下载文件"""
    req = Request(url, headers={
        "User-Agent": HEADERS["User-Agent"],
        "Referer": "https://music.163.com",
    })
    try:
        with urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(filepath, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 // total
                        bar = "█" * (pct // 3) + "░" * (33 - pct // 3)
                        print(f"\r  [{bar}] {pct}%  {downloaded/1024/1024:.1f}/{total/1024/1024:.1f} MB", end="", flush=True)
            print()
        return True
    except Exception as e:
        print(f"\n  ❌ 下载失败: {e}")
        return False


def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def safe_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()


def interactive(query: str, output_dir: str, quality: str):
    """搜索 → 选择 → 下载"""
    print(f"\n🔍 搜索: {query}\n")
    results = search(query)

    if not results:
        print("❌ 没有找到相关结果，换个关键词试试？")
        return

    print(f"{'#':<4} {'歌曲':<25} {'歌手':<18} {'时长':<8} {'专辑'}")
    print("─" * 80)
    for i, s in enumerate(results, 1):
        dur = format_duration(s["duration"])
        title = s["name"]
        if s["alias"]:
            title += f" ({s['alias'][0]})"
        print(f"{i:<4} {title:<25} {s['artists']:<18} {dur:<8} {s['album']}")

    print()
    choice = input("选择序号 (回车=1，q=退出): ").strip()

    if choice.lower() == "q":
        print("已取消")
        return

    if choice == "":
        choice = "1"

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(results):
            raise ValueError
    except ValueError:
        print("❌ 无效选择")
        return

    _do_download(results[idx], output_dir, quality)


def direct(query: str, output_dir: str, quality: str):
    """直接下载第一个结果"""
    print(f"\n🔍 搜索: {query}")
    results = search(query, limit=1)
    if not results:
        print("❌ 没有找到相关结果")
        sys.exit(1)
    s = results[0]
    print(f"🎵 找到: {s['artists']} - {s['name']}")
    _do_download(s, output_dir, quality)


def _do_download(song: dict, output_dir: str, quality: str):
    """执行下载"""
    os.makedirs(output_dir, exist_ok=True)
    filename = safe_filename(f"{song['artists']} - {song['name']}")
    filepath = os.path.join(output_dir, f"{filename}.mp3")

    if os.path.exists(filepath):
        print(f"\n⚠️  文件已存在: {filepath}")
        overwrite = input("覆盖？(y/N): ").strip().lower()
        if overwrite != "y":
            print("已跳过")
            return

    print(f"\n🎵 {song['artists']} - {song['name']}")
    print(f"   专辑: {song['album']}  时长: {format_duration(song['duration'])}")

    url = get_url(song["id"], quality)
    if not url:
        print("❌ 无法获取下载链接（可能需要 VIP）")
        sys.exit(1)

    print(f"   ⬇️  开始下载...\n")
    ok = download_file(url, filepath)

    if ok:
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"\n✅ 下载完成!")
        print(f"📁 {filepath}")
        print(f"📊 {size_mb:.1f} MB")
    else:
        print("\n❌ 下载失败")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="🎵 音乐下载器 - 输入歌名，下载 MP3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "晴天"
  %(prog)s -o ~/Music "周杰伦 稻香"
  %(prog)s -y "起风了"              # 跳过选择
  %(prog)s -q low "告白气球"         # 低音质，更小文件
        """
    )
    parser.add_argument("song", help="歌曲名称或关键词")
    parser.add_argument("-o", "--output", default="./downloads",
                        help="下载目录 (默认: ./downloads)")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="跳过选择，直接下载第一个结果")
    parser.add_argument("-q", "--quality", default="high",
                        choices=["low", "medium", "high", "lossless"],
                        help="音质: low(128k) medium(192k) high(320k) lossless (默认: high)")

    args = parser.parse_args()

    if args.yes:
        direct(args.song, args.output, args.quality)
    else:
        interactive(args.song, args.output, args.quality)


if __name__ == "__main__":
    main()
