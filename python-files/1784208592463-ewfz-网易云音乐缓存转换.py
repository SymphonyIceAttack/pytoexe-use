import os
import json
import re
import sys
import subprocess
import requests
import sqlite3
import zlib
import argparse
import configparser
import traceback
import io
import base64
from pathlib import Path
from PIL import Image
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TYER
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

# 配置文件路径
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.ncm_converter_config.ini')

# 检查并安装缺失的库
def install_missing_libraries():
    required_libraries = ['requests', 'mutagen', 'pillow']
    missing_libs = []
    
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        print(f"缺少必要的库: {', '.join(missing_libs)}")
        confirm = input("是否尝试自动安装? (y/n): ").lower()
        if confirm == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_libs])
                print("安装成功! 请重新运行脚本")
                sys.exit(0)
            except Exception as e:
                print(f"安装失败: {str(e)}")
                print("请手动安装缺少的库:")
                print(f"pip install {' '.join(missing_libs)}")
                sys.exit(1)
        else:
            print("请手动安装缺少的库:")
            print(f"pip install {' '.join(missing_libs)}")
            sys.exit(1)

# 高效解密方法
def decrypt_uc_file(uc_path, output_path):
    try:
        with open(uc_path, 'rb') as uc_file:
            uc_data = uc_file.read()
        
        # 使用网易云音乐官方解密密钥（XOR 0xA3）
        decrypted_data = bytes([byte ^ 0xA3 for byte in uc_data])
        
        with open(output_path, 'wb') as out_file:
            out_file.write(decrypted_data)
        
        return True
    except Exception as e:
        print(f"转换失败: {uc_path} -> {e}")
        return False

# 清理文件名中的非法字符
def sanitize_filename(name):
    if name is None:
        return "未知"
    return re.sub(r'[\\/*?:"<>|]', "", name)

# 从.idx文件获取歌曲信息
def get_song_info_from_idx(idx_path):
    try:
        with open(idx_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 用户提供的格式: {"size":"7505618","t":true,"zone":["0 7505617"]}
        # 这种格式不包含歌曲信息，返回None
        if 'size' in data and 't' in data and 'zone' in data:
            return None, None, None
            
        # 尝试其他格式的解析
        if 'musicName' in data:
            return data.get('musicName', '未知歌曲'), data.get('singer', '未知歌手'), data.get('coverUrl')
        elif 'song' in data:
            song = data['song']
            title = song.get('name', '未知歌曲')
            artists = '/'.join(ar['name'] for ar in song.get('artists', [])) if 'artists' in song else '未知歌手'
            album = song.get('album', {})
            cover_url = album.get('picUrl') if album else None
            return title, artists, cover_url
        elif 'tracks' in data and data['tracks']:
            track = data['tracks'][0]
            title = track.get('name', '未知歌曲')
            artists = '/'.join(ar['name'] for ar in track.get('ar', [])) if 'ar' in track else '未知歌手'
            album = track.get('al', {})
            cover_url = album.get('picUrl') if album else None
            return title, artists, cover_url
        elif 'name' in data:
            title = data.get('name', '未知歌曲')
            artists = '/'.join(ar['name'] for ar in data.get('artists', [])) if 'artists' in data else '未知歌手'
            album = data.get('album', {})
            cover_url = album.get('picUrl') if album else None
            return title, artists, cover_url
        elif 'title' in data:
            return data.get('title', '未知歌曲'), data.get('artist', '未知歌手'), data.get('coverUrl')
    except Exception as e:
        print(f"解析.idx文件失败: {e}")
    return None, None, None

# 从网易云API获取歌曲信息
def get_song_info_from_api(song_id):
    # 从文件名中提取纯数字ID (例如: 1939948801-320-7a140fd05a39e9fcdbaf40a8f774fd52 → 1939948801)
    pure_id = song_id.split('-')[0]
    if not pure_id.isdigit():
        pure_id = song_id
    
    url = f"http://music.163.com/api/song/detail?ids=[{pure_id}]"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'http://music.163.com/',
        'Cookie': 'os=pc; appver=2.9.7'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        if 'songs' in data and data['songs']:
            song = data['songs'][0]
            title = song.get('name', '未知歌曲')
            
            # 处理艺术家信息
            artists = []
            for artist in song.get('artists', []):
                name = artist.get('name')
                if name:
                    artists.append(name)
            
            # 获取专辑封面URL
            album = song.get('album', {})
            cover_url = album.get('picUrl') if album else None
            
            return title, ' / '.join(artists) if artists else '未知歌手', cover_url
    except Exception as e:
        print(f"API请求失败: {str(e)}")
    return None, None, None

# 解析本地网易云音乐缓存数据库
def parse_netease_db(db_path, song_id):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 尝试从不同表中获取歌曲信息
        tables = ['web_cache', 'local_cache', 'track_info', 'cache', 'music_cache']
        for table in tables:
            try:
                # 尝试精确匹配
                cursor.execute(f"SELECT key, value FROM {table} WHERE key LIKE ?", (f'%{song_id}%',))
                rows = cursor.fetchall()
                
                for row in rows:
                    key, value = row
                    try:
                        # 尝试解析JSON数据
                        if isinstance(value, bytes):
                            # 尝试解压数据
                            try:
                                decompressed = zlib.decompress(value)
                                data = json.loads(decompressed)
                            except:
                                # 尝试直接解码
                                data = json.loads(value.decode('utf-8', errors='ignore'))
                        else:
                            data = json.loads(value)
                        
                        # 尝试提取歌曲信息
                        title = None
                        artist = None
                        cover_url = None
                        
                        # 尝试不同格式
                        if 'title' in data and 'artist' in data:
                            title = data['title']
                            artist = data['artist']
                            cover_url = data.get('coverUrl')
                        elif 'songName' in data:
                            title = data['songName']
                            artist = data.get('artist', '未知歌手')
                            cover_url = data.get('coverUrl')
                        elif 'name' in data:
                            title = data['name']
                            if 'artists' in data:
                                artist = '/'.join(ar.get('name', '') for ar in data['artists'])
                            album = data.get('album', {})
                            cover_url = album.get('picUrl') if album else None
                        elif 'track' in data and 'name' in data['track']:
                            title = data['track']['name']
                            if 'artists' in data['track']:
                                artist = '/'.join(ar.get('name', '') for ar in data['track']['artists'])
                            album = data['track'].get('album', {})
                            cover_url = album.get('picUrl') if album else None
                        elif 'musicName' in data:
                            title = data['musicName']
                            artist = data.get('singer', '未知歌手')
                            cover_url = data.get('coverUrl')
                        
                        if title and title != '未知歌曲':
                            return title, artist or '未知歌手', cover_url
                    except:
                        continue
            except:
                continue
        
    except Exception as e:
        print(f"数据库解析失败: {e}")
    finally:
        if conn:
            conn.close()
    
    return None, None, None

# 下载专辑封面
def download_album_cover(cover_url, max_size=500):
    if not cover_url:
        return None
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(cover_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 优化封面大小
            img = Image.open(io.BytesIO(response.content))
            
            # 计算新尺寸保持宽高比
            width, height = img.size
            if width > max_size or height > max_size:
                ratio = min(max_size/width, max_size/height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            
            # 转换为JPEG格式以减小大小
            optimized_img = io.BytesIO()
            img.convert('RGB').save(optimized_img, format='JPEG', quality=85)
            
            return optimized_img.getvalue()
    except Exception as e:
        print(f"  下载专辑封面失败: {str(e)}")
    
    return None

# 获取歌曲元数据
def get_song_metadata(uc_file_path):
    file_path = Path(uc_file_path)
    filename = file_path.name
    song_id = file_path.stem
    
    # 1. 优先尝试从.idx文件获取
    idx_file = file_path.with_suffix('.idx')
    if idx_file.exists():
        title, artist, cover_url = get_song_info_from_idx(idx_file)
        if title and title != '未知歌曲':
            return title, artist, cover_url
    
    # 2. 尝试从API获取（使用歌曲ID）
    title, artist, cover_url = get_song_info_from_api(song_id)
    if title and title != '未知歌曲':
        return title, artist, cover_url
    
    # 3. 尝试从本地数据库获取
    cache_dir = file_path.parent
    possible_db_paths = [
        cache_dir.parent / 'webdb.dat',
        cache_dir.parent.parent / 'webdb.dat',
        cache_dir / 'webdb.dat',
        cache_dir / 'cloud_music_cache.db',
        cache_dir.parent / 'cloud_music_cache.db',
    ]
    
    for db_path in possible_db_paths:
        if db_path.exists():
            title, artist, cover_url = parse_netease_db(db_path, song_id)
            if title and title != '未知歌曲':
                return title, artist, cover_url
    
    # 4. 使用文件名作为后备
    return f"歌曲_{song_id.split('-')[0]}", "未知歌手", None

# 文件类型检测
def determine_file_type(data):
    """根据文件内容确定文件类型"""
    if len(data) < 1024:
        return 'mp3'
    
    header = data[:1024]
    
    if any(sig in header for sig in [b'ftypM4A', b'ftypmp4', b'\x00\x00\x00 ftyp', b'\x00\x00\x00\x18ftyp']):
        return 'm4a'
    elif b'fLaC' in header:
        return 'flac'
    elif b'OggS' in header:
        # 检测是Vorbis还是Opus
        if b'OpusHead' in header:
            return 'opus'
        return 'ogg'
    elif b'RIFF' in header and b'WAVE' in header:
        return 'wav'
    elif b'ID3' in header or any(b in header for b in [b'\xFF\xFB', b'\xFF\xF3', b'\xFF\xFA']):
        return 'mp3'
    else:
        for i in range(len(header) - 1):
            if header[i] == 0xFF and (header[i+1] & 0xE0) == 0xE0:
                return 'mp3'
        
        return 'mp3'

# 嵌入专辑封面
def embed_album_cover(file_path, title, artist, cover_data):
    if not cover_data:
        return False
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.mp3':
            # 处理MP3文件
            audio = MP3(file_path, ID3=ID3)
            
            # 确保存在ID3标签
            try:
                audio.add_tags()
            except:
                pass
            
            # 添加专辑封面
            audio.tags.add(APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',
                type=3,  # 3 表示封面图片
                desc='Cover',
                data=cover_data
            ))
            
            # 添加其他元数据
            if title:
                audio.tags.add(TIT2(encoding=3, text=title))
            if artist:
                audio.tags.add(TPE1(encoding=3, text=artist))
            
            audio.save()
            return True
        
        elif ext == '.m4a':
            # 处理M4A文件
            audio = MP4(file_path)
            
            # 添加专辑封面
            audio.tags['covr'] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
            
            # 添加其他元数据
            if title:
                audio.tags['\xa9nam'] = [title]
            if artist:
                audio.tags['\xa9ART'] = [artist]
            
            audio.save()
            return True
        
        elif ext == '.flac':
            # 处理FLAC文件
            audio = FLAC(file_path)
            
            # 创建图片对象
            image = Picture()
            image.type = 3  # 封面图片
            image.mime = 'image/jpeg'
            image.data = cover_data
            
            # 添加图片
            audio.add_picture(image)
            
            # 添加其他元数据
            if title:
                audio['title'] = [title]
            if artist:
                audio['artist'] = [artist]
            
            audio.save()
            return True
        
        elif ext in ('.ogg', '.opus'):
            # 处理OGG/Opus文件
            if ext == '.opus':
                audio = OggOpus(file_path)
            else:
                audio = OggVorbis(file_path)
            
            # 添加封面
            audio['metadata_block_picture'] = [
                base64.b64encode(FLAC.Picture(3, 'image/jpeg', '', 0, 0, 0, 0, b'', cover_data).write()).decode('ascii')
            ]
            
            # 添加其他元数据
            if title:
                audio['title'] = [title]
            if artist:
                audio['artist'] = [artist]
            
            audio.save()
            return True
        
        elif ext == '.wav':
            # 处理WAV文件
            # WAV文件通常不支持嵌入封面，但我们可以添加元数据
            audio = WAVE(file_path)
            
            # 添加元数据
            if title:
                audio['title'] = title
            if artist:
                audio['artist'] = artist
            
            audio.save()
            # WAV文件不支持嵌入封面
            return False
    
    except Exception as e:
        print(f"  嵌入专辑封面失败: {str(e)}")
    
    return False

# 主处理函数
def process_files(cache_dir, output_dir, naming_format):
    os.makedirs(output_dir, exist_ok=True)
    success_count = 0
    fail_count = 0
    
    # 获取所有.uc文件（递归搜索）
    uc_files = []
    for root, dirs, files in os.walk(cache_dir):
        for file in files:
            if file.endswith('.uc'):
                uc_files.append(os.path.join(root, file))
    
    total_files = len(uc_files)
    
    if total_files == 0:
        print("\n未找到任何.uc缓存文件!")
        return 0, 0
    
    print(f"\n找到 {total_files} 个缓存文件，开始转换...")
    
    for idx, uc_path in enumerate(uc_files, 1):
        filename = os.path.basename(uc_path)
        print(f"\n处理文件 {idx}/{total_files}: {filename}")
        
        try:
            with open(uc_path, 'rb') as f:
                encrypted_data = f.read()
            file_size = len(encrypted_data)
            print(f"  文件大小: {file_size / 1024:.2f} KB")
        except Exception as e:
            print(f"  读取文件失败: {str(e)}")
            fail_count += 1
            continue
        
        # 获取歌曲元数据
        title, artist, cover_url = get_song_metadata(uc_path)
        print(f"  歌曲信息: {title} - {artist}")
        if cover_url:
            print(f"  专辑封面URL: {cover_url}")
        
        # 清理文件名
        clean_title = sanitize_filename(title)
        clean_artist = sanitize_filename(artist)
        
        # 生成输出文件名
        try:
            song_id = Path(uc_path).stem.split('-')[0]
            output_filename = naming_format.format(
                title=clean_title, 
                artist=clean_artist, 
                id=song_id
            )
        except KeyError as e:
            print(f"  无效的命名格式变量: {str(e)}，使用默认格式")
            output_filename = f"{clean_title}-{clean_artist}"
        
        # 解密文件
        temp_output = os.path.join(output_dir, f"temp_{os.urandom(4).hex()}")
        if not decrypt_uc_file(uc_path, temp_output):
            print("  ⚠️ 解密失败，跳过文件")
            fail_count += 1
            continue
        
        # 读取解密后的文件
        try:
            with open(temp_output, 'rb') as f:
                decrypted_data = f.read()
            print(f"  解密成功，大小: {len(decrypted_data) / 1024:.2f} KB")
        except Exception as e:
            print(f"  读取解密文件失败: {str(e)}")
            fail_count += 1
            if os.path.exists(temp_output):
                os.remove(temp_output)
            continue
        
        # 确定文件类型
        file_ext = determine_file_type(decrypted_data)
        print(f"  检测到文件类型: {file_ext}")
        
        # 生成最终输出路径
        output_filename = re.sub(r'\.(mp3|m4a|flac|ogg|wav|opus)$', '', output_filename, flags=re.IGNORECASE)
        output_path = os.path.join(output_dir, f"{output_filename}.{file_ext}")
        
        # 确保文件名唯一
        counter = 1
        base_output_path = output_path
        while os.path.exists(output_path):
            output_path = f"{os.path.splitext(base_output_path)[0]}_{counter}.{file_ext}"
            counter += 1
        
        # 重命名临时文件
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            os.rename(temp_output, output_path)
            print(f"  文件保存成功: {os.path.basename(output_path)}")
            
            # 下载并嵌入专辑封面
            if cover_url:
                print("  下载专辑封面...")
                cover_data = download_album_cover(cover_url)
                
                if cover_data:
                    print(f"  封面大小: {len(cover_data)/1024:.1f} KB")
                    if embed_album_cover(output_path, title, artist, cover_data):
                        print("  专辑封面嵌入成功")
                    else:
                        print("  专辑封面嵌入失败")
                else:
                    print("  专辑封面下载失败")
            
            success_count += 1
        except Exception as e:
            print(f"  写入文件失败: {str(e)}")
            fail_count += 1
            if os.path.exists(temp_output):
                os.remove(temp_output)
    
    return success_count, fail_count

# 配置管理
def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
    return config

def save_config(cache_dir, output_dir, naming_format):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'cache_dir': cache_dir,
        'output_dir': output_dir,
        'naming_format': naming_format
    }
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)

def get_path(prompt, default=None):
    while True:
        path = input(prompt).strip()
        if default and not path:
            path = default
        
        if not path:
            return path
            
        if os.path.exists(path) or path == "":
            return path
        
        print(f"路径不存在: {path}")
        create = input("是否创建此目录? (y/n): ").lower()
        if create == 'y':
            try:
                os.makedirs(path, exist_ok=True)
                print(f"目录已创建: {path}")
                return path
            except Exception as e:
                print(f"创建目录失败: {str(e)}")

def main():
    install_missing_libraries()
    config = load_config()
    has_config = os.path.exists(CONFIG_PATH)
    
    # 命令行参数
    parser = argparse.ArgumentParser(description='网易云音乐缓存转换工具')
    parser.add_argument('--cache', help='缓存目录路径')
    parser.add_argument('--output', help='输出目录路径')
    parser.add_argument('--format', help='文件名格式')
    parser.add_argument('--auto', action='store_true', help='使用上次配置自动运行')
    args = parser.parse_args()
    
    # 配置处理
    cache_dir_default = config.get('DEFAULT', 'cache_dir', fallback='')
    output_dir_default = config.get('DEFAULT', 'output_dir', fallback='')
    naming_format_default = config.get('DEFAULT', 'naming_format', fallback='{title}-{artist}')
    
    if args.auto and has_config:
        cache_dir = cache_dir_default
        output_dir = output_dir_default
        naming_format = naming_format_default
        print("\n自动模式: 使用上次配置运行")
    else:
        print("\n" + "="*50)
        print("网易云音乐缓存转换工具 - 带封面嵌入版")
        print("="*50 + "\n")
        
        if has_config:
            print(f"检测到上次使用的配置:")
            print(f"  缓存目录: {cache_dir_default}")
            print(f"  输出目录: {output_dir_default}")
            print(f"  命名格式: {naming_format_default}")
            change = input("\n是否使用上次配置? (y/n): ").lower()
            if change == 'y':
                cache_dir = cache_dir_default
                output_dir = output_dir_default
                naming_format = naming_format_default
            else:
                if args.cache:
                    cache_dir = args.cache
                else:
                    prompt = f"请输入缓存目录路径{(' [默认: ' + cache_dir_default + ']' if cache_dir_default else '')}: "
                    cache_dir = get_path(prompt, cache_dir_default)
                
                if args.output:
                    output_dir = args.output
                else:
                    prompt = f"请输入输出目录路径{(' [默认: ' + output_dir_default + ']' if output_dir_default else '')}: "
                    output_dir = get_path(prompt, output_dir_default)
                
                if args.format:
                    naming_format = args.format
                else:
                    naming_format = input(f"请输入文件名格式 [默认: {naming_format_default}] (可用变量: {{title}}, {{artist}}, {{id}}): ") or naming_format_default
        else:
            cache_dir = args.cache or input("请输入缓存目录路径: ").strip()
            output_dir = args.output or input("请输入输出目录路径: ").strip()
            naming_format = args.format or input(f"请输入文件名格式 [默认: {naming_format_default}] (可用变量: {{title}}, {{artist}}, {{id}}): ") or naming_format_default
        
        save_config(cache_dir, output_dir, naming_format)
    
    # 验证文件名格式
    if not re.search(r'\{title\}', naming_format) and not re.search(r'\{artist\}', naming_format):
        print("警告: 文件名格式中至少应包含 {title} 或 {artist}")
    
    # 处理文件
    print("\n开始转换...")
    print(f"缓存目录: {cache_dir}")
    print(f"输出目录: {output_dir}")
    print(f"命名格式: {naming_format}\n")
    
    try:
        success_count, fail_count = process_files(cache_dir, output_dir, naming_format)
        print("\n" + "="*50)
        print(f"转换完成! 成功: {success_count}, 失败: {fail_count}")
        print("="*50)
    except Exception as e:
        print("\n" + "="*50)
        print("转换过程中发生错误:")
        print(str(e))
        print("="*50)
        traceback.print_exc()
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()