#!/usr/bin/env python3
"""
SimMC 领地信息获取程序
从 https://map.simmc.cn/tiles/minecraft_overworld/markers.json 获取领地信息
只获取玩家数量 ≤ 21 的领地，并保存为JSON格式。

"""

import json
import re
import os
import time
import socket
import gzip
import urllib.request
import urllib.error
import tempfile
from datetime import datetime

# ============ 配置 ============
MARKERS_URL = "https://map.simmc.cn/tiles/minecraft_overworld/markers.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "lands_data")  # 输出目录
MAX_PLAYERS_PER_LAND = 21  # 最大领地人数（超过则忽略该领地）
PLAYERS_PER_FILE = 2000  # 每个玩家文件包含的玩家数量
# =============================

# 预编译正则
_RE_NAME1 = re.compile(r'font-size:\s*200%;[^>]*>\s*<span[^>]*>\s*(.+?)\s*</span>')
_RE_NAME2 = re.compile(r'font-size:\s*200%[^>]*>(.+?)<')
_RE_HTML = re.compile(r'<[^>]+>')
_RE_LEVEL = re.compile(r'等级[:：]\s*([^<]+)')
_RE_BALANCE = re.compile(r'余额[:：]\s*([^<]+)')
_RE_CHUNKS = re.compile(r'区块[:：]\s*(\d+)')
_RE_PLAYERS = re.compile(r'玩家\((\d+)\)[:：]\s*(.+?)</li>')
_RE_NATION = re.compile(r'属于国家\s*(.+?)</strong>')


def fetch_markers() -> list:
    """从 squaremap API 获取数据，支持 gzip 压缩"""
    tmpfile = os.path.join(tempfile.gettempdir(), f'simc_markers_{os.getpid()}.json')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://map.simmc.cn/',
        'Accept-Encoding': 'gzip',
    }

    print(f"正在连接 map.simmc.cn ...")
    t_start = time.time()

    try:
        req = urllib.request.Request(MARKERS_URL, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)

        content_encoding = resp.headers.get('Content-Encoding', '')
        total = int(resp.headers.get('Content-Length', 0)) or 6_500_000

        print(f"下载中 ({total / 1024:.0f} KB, gzip={content_encoding}) ...")

        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(120)

        downloaded = 0
        try:
            with open(tmpfile, 'wb') as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % 1048576 == 0:  # 每1MB报告一次进度
                        elapsed = time.time() - t_start
                        pct = downloaded * 100 // total
                        print(f"  {downloaded // 1024}/{total // 1024} KB ({pct}%)")
        finally:
            socket.setdefaulttimeout(old_timeout)
        resp.close()

    except Exception as e:
        print()
        if os.path.isfile(tmpfile):
            os.remove(tmpfile)
        raise RuntimeError(f"下载失败: {e}")

    raw_size = os.path.getsize(tmpfile)
    print(f"下载完成: {raw_size / 1024:.0f} KB (耗时 {time.time() - t_start:.0f}s)")

    if raw_size < 10000:
        raise RuntimeError(f"下载文件不完整 ({raw_size} bytes)")

    # gzip 解压
    is_gzip = content_encoding == 'gzip'
    try:
        with open(tmpfile, 'rb') as f:
            magic = f.read(2)
        is_gzip = is_gzip or (magic == b'\x1f\x8b')
    except:
        pass

    print(f"正在解析 JSON...", end='', flush=True)
    if is_gzip:
        with gzip.open(tmpfile, 'rb') as f:
            data = json.loads(f.read().decode('utf-8'))
    else:
        with open(tmpfile, 'r', encoding='utf-8') as f:
            data = json.load(f)
    os.remove(tmpfile)
    print(" 完成")
    return data


def extract_land_name(tooltip: str) -> str:
    """从 tooltip HTML 中提取领地名称"""
    m = _RE_NAME1.search(tooltip)
    if m:
        return m.group(1).strip()
    m = _RE_NAME2.search(tooltip)
    if m:
        return _RE_HTML.sub('', m.group(1)).strip()
    return "未知领地"


def strip_html(text: str) -> str:
    """去除 HTML 标签"""
    return _RE_HTML.sub('', text).strip()


def extract_land_info(tooltip: str) -> dict:
    """从 tooltip HTML 中提取领地详细信息"""
    info = {}

    m = _RE_LEVEL.search(tooltip)
    if m:
        info['level'] = strip_html(m.group(1))

    m = _RE_BALANCE.search(tooltip)
    if m:
        info['balance'] = strip_html(m.group(1))

    m = _RE_CHUNKS.search(tooltip)
    if m:
        info['chunks'] = int(m.group(1))

    m = _RE_PLAYERS.search(tooltip)
    if m:
        info['player_count'] = int(m.group(1))
        # 过滤掉 "..." 和空字符串
        players = [p.strip() for p in m.group(2).split(',')]
        info['players'] = [p for p in players if p and p != '...']
    else:
        info['player_count'] = 0
        info['players'] = []

    m = _RE_NATION.search(tooltip)
    if m:
        info['nation'] = m.group(1).strip().rstrip('：:')

    return info


def get_first_point(polygon_points: list) -> tuple:
    """获取多边形第一个顶点坐标，用作稳定标识"""
    if not polygon_points or not polygon_points[0]:
        return (0, 0)
    points = polygon_points[0]
    if not points:
        return (0, 0)
    return (points[0]['x'], points[0]['z'])


def compute_center(polygon_points: list) -> tuple:
    """计算多边形的中心坐标"""
    if not polygon_points or not polygon_points[0]:
        return (0, 0)
    points = polygon_points[0]
    if not points:
        return (0, 0)
    sum_x = sum(p['x'] for p in points)
    sum_z = sum(p['z'] for p in points)
    n = len(points)
    return (round(sum_x / n), round(sum_z / n))


def make_land_key(name: str, x: int, z: int) -> str:
    """生成领地唯一标识：名称@坐标"""
    return f"{name}@{x},{z}"


def parse_lands(data: list) -> tuple:
    """解析 markers 数据，只获取人数 ≤ MAX_PLAYERS_PER_LAND 的领地
    返回 (领地字典, 玩家集合, 统计信息)"""
    marker_list = None
    for group in data:
        if group.get('id') == 'lands_world':
            marker_list = group.get('markers', [])
            break

    if not marker_list:
        print("未找到领地数据")
        return {}, set(), {'total': 0, 'included': 0, 'excluded': 0}

    total = len(marker_list)
    print(f"正在解析 {total} 个领地（只保留 ≤ {MAX_PLAYERS_PER_LAND} 人的领地）...")

    lands = {}
    all_players = set()
    included_count = 0
    excluded_count = 0

    for i, marker in enumerate(marker_list):
        if i % 500 == 0 and i > 0:
            print(f"  解析进度: {i}/{total} ({i * 100 // total}%) - 已包含 {included_count} 个")

        tooltip = marker.get('tooltip', '')
        info = extract_land_info(tooltip)
        player_count = info.get('player_count', 0)

        # 检查玩家数量，只保留 ≤ MAX_PLAYERS_PER_LAND 的领地
        if player_count > MAX_PLAYERS_PER_LAND:
            excluded_count += 1
            continue

        # 如果玩家数量为 0 但有玩家列表，也跳过
        if player_count == 0 and not info.get('players'):
            excluded_count += 1
            continue

        name = extract_land_name(tooltip)
        stable_x, stable_z = get_first_point(marker.get('points', []))
        center = compute_center(marker.get('points', []))

        # 生成唯一key
        key = make_land_key(name, stable_x, stable_z)

        # 构建领地信息
        land_data = {
            'name': name,
            'x': center[0],
            'z': center[1],
            'level': info.get('level', ''),
            'balance': info.get('balance', ''),
            'chunks': info.get('chunks', 0),
            'player_count': player_count,
            'players': info.get('players', []),
            'nation': info.get('nation', '')
        }

        lands[key] = land_data
        included_count += 1

        # 添加到玩家集合
        if info.get('players'):
            all_players.update(info['players'])

    print(f"解析完成: {total}/{total} (100%)")
    print(f"  包含领地: {included_count}")
    print(f"  排除领地: {excluded_count}")

    stats = {
        'total': total,
        'included': included_count,
        'excluded': excluded_count
    }

    return lands, all_players, stats


def save_players_to_txt(players: set):
    """将玩家名单保存为纯文本文件，每2000人一个文件"""
    if not players:
        print("没有玩家数据需要保存")
        return []

    sorted_players = sorted(list(players))
    total_players = len(sorted_players)
    file_count = (total_players + PLAYERS_PER_FILE - 1) // PLAYERS_PER_FILE  # 向上取整

    saved_files = []

    print(f"\n保存玩家名单（共 {total_players} 个玩家，每 {PLAYERS_PER_FILE} 人一个文件）...")

    for i in range(file_count):
        start_idx = i * PLAYERS_PER_FILE
        end_idx = min((i + 1) * PLAYERS_PER_FILE, total_players)
        chunk = sorted_players[start_idx:end_idx]

        filename = f"testdate{i + 1}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            for name in chunk:
                f.write(name + '\n')

        saved_files.append(filepath)
        print(f"  已保存: {filename} ({len(chunk)} 个玩家)")

    return saved_files


def save_lands_data(lands: dict, stats: dict):
    """保存领地信息到JSON文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 保存领地数据
    lands_filepath = os.path.join(OUTPUT_DIR, "lands_data.json")

    lands_output = {
        "metadata": {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "filter": {
                "max_players_per_land": MAX_PLAYERS_PER_LAND,
                "total_lands_found": stats['total'],
                "included_lands": stats['included'],
                "excluded_lands": stats['excluded']
            },
            "total_lands": len(lands),
            "api_source": MARKERS_URL
        },
        "lands": lands
    }

    with open(lands_filepath, 'w', encoding='utf-8') as f:
        json.dump(lands_output, f, ensure_ascii=False, indent=2)

    print(f"\n领地数据已保存: {os.path.abspath(lands_filepath)}")
    print(f"文件大小: {os.path.getsize(lands_filepath) / 1024:.1f} KB")

    return lands_filepath


def main():
    start_time = time.time()

    print("SimMC 领地信息获取工具")
    print(f"数据来源: {MARKERS_URL}")
    print(f"过滤条件: 只保留玩家数 ≤ {MAX_PLAYERS_PER_LAND} 的领地")
    print(f"玩家名单: 每 {PLAYERS_PER_FILE} 个玩家保存为一个txt文件")
    print("=" * 50)

    try:
        # 1. 获取数据
        data = fetch_markers()

        # 2. 解析领地信息（只保留 ≤ 21 人的领地）
        lands, all_players, stats = parse_lands(data)

        if not lands:
            print("未获取到符合条件的领地数据")
            return

        # 3. 显示统计信息
        print(f"\n统计信息:")
        print(f"  原始领地总数: {stats['total']}")
        print(f"  包含领地 (≤{MAX_PLAYERS_PER_LAND}人): {stats['included']}")
        print(f"  排除领地 (>{MAX_PLAYERS_PER_LAND}人): {stats['excluded']}")
        print(f"  独立玩家总数: {len(all_players)}")

        # 显示一些示例领地
        if lands:
            print(f"\n领地示例（前5个）:")
            for i, (key, land) in enumerate(list(lands.items())[:5], 1):
                players_str = ', '.join(land['players'][:3])
                if len(land['players']) > 3:
                    players_str += f" 等{len(land['players'])}人"
                nation_str = f" [{land['nation']}]" if land['nation'] else ""
                print(f"  {i}. {land['name']}{nation_str}")
                print(f"     坐标: ({land['x']}, {land['z']})")
                print(f"     等级: {land['level']}  区块: {land['chunks']}  余额: {land['balance']}")
                print(f"     玩家({land['player_count']}): {players_str or '无'}")

        # 显示一些示例玩家
        if all_players:
            sample_players = sorted(list(all_players))[:10]
            print(f"\n玩家示例（前10个）:")
            for i, player in enumerate(sample_players, 1):
                # 统计该玩家拥有的领地数量
                land_count = sum(1 for land in lands.values() if player in land['players'])
                print(f"  {i}. {player} (出现在 {land_count} 个领地中)")
            if len(all_players) > 10:
                print(f"  ... 共 {len(all_players)} 个玩家")

        # 4. 保存数据

        # 保存领地JSON数据
        lands_file = save_lands_data(lands, stats)

        # 保存玩家TXT名单（每2000人一个文件）
        player_files = save_players_to_txt(all_players)

        elapsed = time.time() - start_time
        print(f"\n{'=' * 50}")
        print(f"完成！耗时 {elapsed:.0f} 秒")
        print(f"领地数据: {lands_file}")
        print(f"玩家名单: 共 {len(player_files)} 个文件")
        for pf in player_files:
            print(f"  - {pf}")

    except Exception as e:
        print(f"\n错误: {e}")
        print("请检查网络连接或数据格式是否变化。")


if __name__ == '__main__':
    main()