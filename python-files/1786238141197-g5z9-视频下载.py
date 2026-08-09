"""
超级音视频下载器 v4.6 - 记住FFmpeg路径版
功能：自动安装依赖、实时进度显示、状态更新、智能FFmpeg检测、记住路径
"""

import os
import re
import json
import time
import uuid
import threading
import queue
import subprocess
import tempfile
import shutil
import sys
import platform
import importlib
from datetime import datetime
from urllib.parse import urlparse, urljoin, parse_qs
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import webbrowser

# 尝试导入requests，如果没有则提示安装
try:
    import requests
except ImportError:
    requests = None

# 尝试导入pkg_resources
try:
    import pkg_resources
except ImportError:
    pkg_resources = None

from concurrent.futures import ThreadPoolExecutor

# 全局变量
YT_DLP_AVAILABLE = False
MOVIEPY_AVAILABLE = False
FFMPEG_AVAILABLE = False

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.video_downloader_config.json')


class ConfigManager:
    """配置管理器 - 用于保存和加载用户设置"""
    
    @staticmethod
    def load_config():
        """加载配置文件"""
        default_config = {
            'ffmpeg_path': '',
            'download_dir': 'downloads',
            'quality': 'best',
            'format': 'mp4',
            'audio_format': 'mp3',
            'last_urls': []
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        return default_config
    
    @staticmethod
    def save_config(config):
        """保存配置文件"""
        try:
            # 确保目录存在
            config_dir = os.path.dirname(CONFIG_FILE)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    @staticmethod
    def get_ffmpeg_path():
        """获取保存的FFmpeg路径"""
        config = ConfigManager.load_config()
        return config.get('ffmpeg_path', '')
    
    @staticmethod
    def save_ffmpeg_path(path):
        """保存FFmpeg路径"""
        config = ConfigManager.load_config()
        config['ffmpeg_path'] = path
        return ConfigManager.save_config(config)
    
    @staticmethod
    def add_recent_url(url):
        """添加最近使用的URL"""
        config = ConfigManager.load_config()
        urls = config.get('last_urls', [])
        
        # 如果已存在，先移除
        if url in urls:
            urls.remove(url)
        
        # 添加到最前面
        urls.insert(0, url)
        
        # 只保留最近10个
        config['last_urls'] = urls[:10]
        ConfigManager.save_config(config)
    
    @staticmethod
    def get_recent_urls():
        """获取最近使用的URL列表"""
        config = ConfigManager.load_config()
        return config.get('last_urls', [])


class FFmpegDetector:
    """FFmpeg增强检测器 - 支持自定义路径"""
    
    # 常见的FFmpeg安装路径
    COMMON_PATHS = [
        # Windows 常见路径
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe',
        'D:\\ffmpeg\\bin\\ffmpeg.exe',
        'D:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        'E:\\ffmpeg\\bin\\ffmpeg.exe',
        # macOS 常见路径
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/opt/homebrew/bin/ffmpeg',
        '/opt/local/bin/ffmpeg',
        # Linux 常见路径
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/bin/ffmpeg',
        '/opt/ffmpeg/bin/ffmpeg',
    ]
    
    @staticmethod
    def find_ffmpeg():
        """查找FFmpeg - 增强版"""
        results = {
            'found': False,
            'paths': [],
            'versions': [],
            'best_path': None,
            'best_version': None,
            'features': {}
        }
        
        # 0. 首先检查配置文件中的路径
        saved_path = ConfigManager.get_ffmpeg_path()
        if saved_path and os.path.exists(saved_path):
            results['paths'].append(saved_path)
            results['found'] = True
            results['best_path'] = saved_path
            # 添加到PATH以便后续检测
            os.environ['PATH'] += os.pathsep + os.path.dirname(saved_path)
        
        # 1. 检查环境变量
        env_path = os.environ.get('FFMPEG_PATH')
        if env_path and os.path.exists(env_path) and env_path not in results['paths']:
            results['paths'].append(env_path)
            results['found'] = True
            if not results['best_path']:
                results['best_path'] = env_path
        
        # 2. 检查PATH环境变量
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for dir_path in path_dirs:
            if not dir_path:
                continue
            for ffmpeg_name in ['ffmpeg.exe', 'ffmpeg']:
                full_path = os.path.join(dir_path, ffmpeg_name)
                if os.path.exists(full_path) and full_path not in results['paths']:
                    results['paths'].append(full_path)
                    results['found'] = True
                    if not results['best_path']:
                        results['best_path'] = full_path
        
        # 3. 检查常见安装路径
        for path in FFmpegDetector.COMMON_PATHS:
            if os.path.exists(path) and path not in results['paths']:
                results['paths'].append(path)
                results['found'] = True
                if not results['best_path']:
                    results['best_path'] = path
        
        # 4. 使用shutil.which检测
        try:
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path and ffmpeg_path not in results['paths']:
                results['paths'].append(ffmpeg_path)
                results['found'] = True
                if not results['best_path']:
                    results['best_path'] = ffmpeg_path
        except:
            pass
        
        # 5. 获取每个找到的FFmpeg的版本信息
        for path in results['paths']:
            version_info = FFmpegDetector.get_ffmpeg_version(path)
            if version_info:
                results['versions'].append({
                    'path': path,
                    'version': version_info['version'],
                    'full_info': version_info['full_info']
                })
                # 选择最新版本
                if (not results['best_version'] or 
                    version_info['version'] > results['best_version']):
                    results['best_version'] = version_info['version']
                    results['best_path'] = path
        
        # 6. 获取最佳FFmpeg的详细功能
        if results['best_path']:
            results['features'] = FFmpegDetector.get_ffmpeg_features(results['best_path'])
        
        return results
    
    @staticmethod
    def get_ffmpeg_version(ffmpeg_path):
        """获取FFmpeg版本信息"""
        try:
            result = subprocess.run(
                [ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                if lines:
                    # 解析版本号
                    version_match = re.search(r'ffmpeg version ([^\s]+)', lines[0])
                    if version_match:
                        version_str = version_match.group(1)
                        # 尝试解析为数字版本
                        try:
                            # 提取数字部分
                            num_match = re.search(r'(\d+)\.(\d+)\.?(\d+)?', version_str)
                            if num_match:
                                groups = num_match.groups()
                                version_tuple = tuple(int(g) if g else 0 for g in groups if g is not None)
                                # 转换为可比较的版本号
                                version_num = 0
                                for i, v in enumerate(version_tuple):
                                    version_num += v * (100 ** (2 - i))
                                return {
                                    'version': version_num,
                                    'version_str': version_str,
                                    'full_info': result.stdout
                                }
                        except:
                            pass
                        return {
                            'version': 0,
                            'version_str': version_str,
                            'full_info': result.stdout
                        }
            return None
        except:
            return None
    
    @staticmethod
    def get_ffmpeg_features(ffmpeg_path):
        """获取FFmpeg支持的功能"""
        features = {
            'h264': False,
            'h265': False,
            'vp9': False,
            'aac': False,
            'mp3': False,
            'opus': False,
            'flac': False,
            'webm': False,
            'mkv': False,
            'mov': False,
            'av1': False,
            'hardware_accel': False,
            'nvenc': False,
            'amf': False,
            'qsv': False,
        }
        
        try:
            # 获取编码器列表
            result = subprocess.run(
                [ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout
                # 检查各种编码器
                features['h264'] = 'libx264' in output or 'h264' in output
                features['h265'] = 'libx265' in output or 'hevc' in output
                features['vp9'] = 'libvpx-vp9' in output
                features['aac'] = 'aac' in output
                features['mp3'] = 'libmp3lame' in output or 'mp3' in output
                features['opus'] = 'libopus' in output
                features['flac'] = 'flac' in output
                
                # 硬件加速
                features['nvenc'] = 'nvenc' in output
                features['amf'] = 'amf' in output
                features['qsv'] = 'qsv' in output
                features['hardware_accel'] = features['nvenc'] or features['amf'] or features['qsv']
            
            # 获取格式支持
            result = subprocess.run(
                [ffmpeg_path, '-formats'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout
                features['webm'] = 'webm' in output
                features['mkv'] = 'matroska' in output or 'mkv' in output
                features['mov'] = 'mov' in output
            
            # 检查AV1支持
            result = subprocess.run(
                [ffmpeg_path, '-encoders', '|', 'grep', 'av1'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            if result.returncode == 0:
                features['av1'] = True
        except:
            pass
        
        return features

    @staticmethod
    def add_custom_path(custom_path):
        """添加自定义FFmpeg路径并保存到配置"""
        if custom_path and os.path.exists(custom_path):
            if custom_path not in FFmpegDetector.COMMON_PATHS:
                FFmpegDetector.COMMON_PATHS.insert(0, custom_path)
            # 保存到配置文件
            ConfigManager.save_ffmpeg_path(custom_path)
            return True
        return False


class DependencyInfo:
    """依赖信息类"""
    def __init__(self, name, display_name, import_name, 
                 min_version=None, required=True):
        self.name = name
        self.display_name = display_name
        self.import_name = import_name
        self.min_version = min_version
        self.required = required
        self.installed = False
        self.version = None
        self.error = None
        self.features = {}
    
    def to_dict(self):
        return {
            'name': self.name,
            'display_name': self.display_name,
            'installed': self.installed,
            'version': self.version,
            'error': self.error,
            'features': self.features,
            'required': self.required
        }


class DependencyManager:
    """依赖管理器 - 增强版"""
    
    # 定义所有依赖
    DEPENDENCIES = {
        'yt_dlp': DependencyInfo(
            name='yt-dlp',
            display_name='yt-dlp (视频下载核心)',
            import_name='yt_dlp',
            min_version='2023.01.01',
            required=True
        ),
        'moviepy': DependencyInfo(
            name='moviepy',
            display_name='moviepy (视频处理)',
            import_name='moviepy',
            min_version='1.0.0',
            required=False
        ),
        'requests': DependencyInfo(
            name='requests',
            display_name='requests (网络请求)',
            import_name='requests',
            min_version='2.25.0',
            required=True
        ),
        'PIL': DependencyInfo(
            name='Pillow',
            display_name='Pillow (图像处理)',
            import_name='PIL',
            min_version='8.0.0',
            required=False
        ),
        'numpy': DependencyInfo(
            name='numpy',
            display_name='NumPy (数值计算)',
            import_name='numpy',
            min_version='1.19.0',
            required=False
        ),
    }
    
    @staticmethod
    def check_package_version(package_name):
        """检查包版本"""
        try:
            # 尝试使用pkg_resources获取版本
            if pkg_resources:
                try:
                    version = pkg_resources.get_distribution(package_name).version
                    return True, version
                except:
                    pass
            
            # 尝试使用importlib
            try:
                module = importlib.import_module(package_name)
                if hasattr(module, '__version__'):
                    return True, module.__version__
                elif hasattr(module, 'version'):
                    return True, module.version
                elif hasattr(module, 'VERSION'):
                    version = module.VERSION
                    if isinstance(version, tuple):
                        return True, '.'.join(map(str, version))
                    return True, str(version)
            except:
                pass
            
            # 尝试使用pip show
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', package_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split(':', 1)[1].strip()
                            return True, version
            except:
                pass
            
            return False, None
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def check_pip_package(package_name):
        """检查pip包是否安装"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_ffmpeg():
        """检查FFmpeg详细信息 - 使用增强检测器"""
        # 使用增强检测器
        ffmpeg_info = FFmpegDetector.find_ffmpeg()
        
        result = {
            'installed': ffmpeg_info['found'],
            'version': ffmpeg_info['best_version'],
            'version_str': None,
            'path': ffmpeg_info['best_path'],
            'all_paths': ffmpeg_info['paths'],
            'features': ffmpeg_info['features'],
            'error': None
        }
        
        # 获取版本字符串
        if ffmpeg_info['best_path']:
            version_info = FFmpegDetector.get_ffmpeg_version(ffmpeg_info['best_path'])
            if version_info:
                result['version_str'] = version_info.get('version_str')
        
        return result
    
    @classmethod
    def check_all_dependencies(cls, progress_callback=None):
        """检查所有依赖"""
        results = {}
        
        # 检查Python包
        for key, dep in cls.DEPENDENCIES.items():
            if progress_callback:
                progress_callback(f"检查 {dep.display_name}...", 0)
            
            try:
                # 尝试导入
                importlib.import_module(dep.import_name)
                dep.installed = True
                
                # 获取版本
                success, version = cls.check_package_version(dep.name)
                if success:
                    dep.version = version
                    
                    # 检查版本是否符合要求
                    if dep.min_version:
                        try:
                            # 尝试使用packaging，如果没有则跳过版本检查
                            try:
                                from packaging import version as pkg_version
                                if pkg_version.parse(version) < pkg_version.parse(dep.min_version):
                                    dep.error = f"版本过低 (需要 {dep.min_version})"
                            except ImportError:
                                pass
                        except:
                            pass
            except ImportError:
                dep.installed = False
                dep.error = "未安装"
            except Exception as e:
                dep.installed = False
                dep.error = str(e)
            
            results[key] = dep.to_dict()
            
            if progress_callback:
                status = "✅" if dep.installed else "❌"
                progress_callback(f"{status} {dep.display_name}: {dep.version or '未安装'}", 50)
        
        # 检查FFmpeg
        if progress_callback:
            progress_callback("检查 FFmpeg...", 0)
        
        ffmpeg_info = cls.check_ffmpeg()
        
        # 构建FFmpeg结果
        ffmpeg_result = {
            'name': 'ffmpeg',
            'display_name': 'FFmpeg (音视频处理)',
            'installed': ffmpeg_info['installed'],
            'version': ffmpeg_info['version_str'] or '未检测到',
            'version_num': ffmpeg_info['version'],
            'path': ffmpeg_info['path'],
            'all_paths': ffmpeg_info.get('all_paths', []),
            'features': ffmpeg_info.get('features', {}),
            'error': ffmpeg_info.get('error'),
            'required': False
        }
        results['ffmpeg'] = ffmpeg_result
        
        if progress_callback:
            status = "✅" if ffmpeg_info['installed'] else "❌"
            version = ffmpeg_info['version_str'] or '未安装'
            path = ffmpeg_info['path'] or ''
            progress_callback(f"{status} FFmpeg: {version} ({path})", 100)
        
        return results
    
    @classmethod
    def install_package(cls, package_name, progress_callback=None):
        """安装Python包"""
        try:
            if progress_callback:
                progress_callback(f"正在安装 {package_name}...", 10)
            
            # 使用pip安装
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                if progress_callback:
                    progress_callback(f"✅ {package_name} 安装成功", 100)
                return True
            else:
                error_msg = result.stderr[:500] if result.stderr else "未知错误"
                if progress_callback:
                    progress_callback(f"❌ {package_name} 安装失败: {error_msg}", 0)
                return False
        except subprocess.TimeoutExpired:
            if progress_callback:
                progress_callback(f"❌ {package_name} 安装超时", 0)
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ {package_name} 安装出错: {str(e)}", 0)
            return False
    
    @classmethod
    def install_dependencies(cls, required_only=True, 
                            progress_callback=None):
        """安装依赖"""
        results = {}
        
        # 先检查当前状态
        current_status = cls.check_all_dependencies(progress_callback=None)
        
        packages_to_install = []
        for key, dep in cls.DEPENDENCIES.items():
            if required_only and not dep.required:
                continue
            if not current_status.get(key, {}).get('installed', False):
                packages_to_install.append(key)
        
        # 检查FFmpeg
        ffmpeg_installed = current_status.get('ffmpeg', {}).get('installed', False)
        
        if packages_to_install:
            if progress_callback:
                progress_callback(f"需要安装 {len(packages_to_install)} 个包...", 0)
            
            for i, key in enumerate(packages_to_install):
                dep = cls.DEPENDENCIES[key]
                progress = (i / len(packages_to_install)) * 80
                if progress_callback:
                    progress_callback(f"安装 {dep.display_name}...", progress)
                
                success = cls.install_package(dep.name, progress_callback=None)
                results[key] = success
                
                if progress_callback:
                    status = "✅" if success else "❌"
                    progress_callback(f"{status} {dep.display_name}", 
                                    80 + (i + 1) / len(packages_to_install) * 20)
        
        # 检查FFmpeg
        if not ffmpeg_installed:
            if progress_callback:
                progress_callback("安装 FFmpeg...", 85)
            
            success = cls.install_ffmpeg(progress_callback)
            results['ffmpeg'] = success
        
        # 重新检查所有依赖
        if progress_callback:
            progress_callback("验证安装...", 95)
        
        final_status = cls.check_all_dependencies(progress_callback)
        
        # 生成报告
        all_installed = all(
            info.get('installed', False) 
            for info in final_status.values() 
            if cls.DEPENDENCIES.get(info.get('name', ''), DependencyInfo('', '', '')).required
        )
        
        if progress_callback:
            if all_installed:
                progress_callback("✅ 所有必需依赖已安装完成", 100)
            else:
                progress_callback("⚠️ 部分依赖安装失败，请手动安装", 100)
        
        return {k: v.get('installed', False) for k, v in final_status.items()}
    
    @staticmethod
    def install_ffmpeg(progress_callback=None):
        """安装FFmpeg - 跨平台"""
        system = platform.system()
        
        if progress_callback:
            progress_callback(f"检测到系统: {system}", 10)
        
        if system == 'Windows':
            return DependencyManager._install_ffmpeg_windows(progress_callback)
        elif system == 'Darwin':
            return DependencyManager._install_ffmpeg_mac(progress_callback)
        elif system == 'Linux':
            return DependencyManager._install_ffmpeg_linux(progress_callback)
        else:
            if progress_callback:
                progress_callback(f"❌ 不支持的系统: {system}", 0)
            return False
    
    @staticmethod
    def _install_ffmpeg_windows(progress_callback=None):
        """Windows安装FFmpeg"""
        # 方法1: winget
        try:
            if progress_callback:
                progress_callback("尝试 winget...", 20)
            result = subprocess.run(
                ['winget', 'install', 'ffmpeg', '--silent'],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                if progress_callback:
                    progress_callback("✅ FFmpeg 安装成功 (winget)", 100)
                return True
        except:
            pass
        
        # 方法2: chocolatey
        try:
            if progress_callback:
                progress_callback("尝试 Chocolatey...", 40)
            result = subprocess.run(
                ['choco', 'install', 'ffmpeg', '-y'],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                if progress_callback:
                    progress_callback("✅ FFmpeg 安装成功 (choco)", 100)
                return True
        except:
            pass
        
        # 方法3: 直接下载
        try:
            if progress_callback:
                progress_callback("下载 FFmpeg...", 60)
            
            import zipfile
            
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            # 下载
            response = requests.get(url, stream=True, timeout=60)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            prog = 60 + (downloaded / total_size) * 30
                            progress_callback(f"下载中... {downloaded//1024}KB", prog)
            
            if progress_callback:
                progress_callback("解压中...", 90)
            
            # 解压
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找并复制ffmpeg.exe
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == 'ffmpeg.exe':
                        src_path = os.path.join(root, file)
                        dest_dir = os.path.join(os.environ['ProgramFiles'], 'ffmpeg', 'bin')
                        os.makedirs(dest_dir, exist_ok=True)
                        shutil.copy2(src_path, dest_dir)
                        
                        # 添加到PATH
                        os.environ['PATH'] += os.pathsep + dest_dir
                        
                        # 保存路径到配置
                        ConfigManager.save_ffmpeg_path(dest_dir + '\\ffmpeg.exe')
                        
                        if progress_callback:
                            progress_callback("✅ FFmpeg 安装成功", 100)
                        return True
            
            return False
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ 下载安装失败: {str(e)}", 0)
            return False
    
    @staticmethod
    def _install_ffmpeg_mac(progress_callback=None):
        """macOS安装FFmpeg"""
        # Homebrew
        try:
            if progress_callback:
                progress_callback("尝试 Homebrew...", 20)
            result = subprocess.run(
                ['brew', 'install', 'ffmpeg'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                # 保存路径到配置
                ffmpeg_path = shutil.which('ffmpeg')
                if ffmpeg_path:
                    ConfigManager.save_ffmpeg_path(ffmpeg_path)
                if progress_callback:
                    progress_callback("✅ FFmpeg 安装成功 (Homebrew)", 100)
                return True
        except:
            pass
        
        # MacPorts
        try:
            if progress_callback:
                progress_callback("尝试 MacPorts...", 40)
            result = subprocess.run(
                ['sudo', 'port', 'install', 'ffmpeg'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                ffmpeg_path = shutil.which('ffmpeg')
                if ffmpeg_path:
                    ConfigManager.save_ffmpeg_path(ffmpeg_path)
                if progress_callback:
                    progress_callback("✅ FFmpeg 安装成功 (MacPorts)", 100)
                return True
        except:
            pass
        
        return False
    
    @staticmethod
    def _install_ffmpeg_linux(progress_callback=None):
        """Linux安装FFmpeg"""
        package_managers = [
            ('apt', ['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', '-y', 'ffmpeg']),
            ('yum', None, ['sudo', 'yum', 'install', '-y', 'ffmpeg']),
            ('dnf', None, ['sudo', 'dnf', 'install', '-y', 'ffmpeg']),
            ('pacman', None, ['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg']),
            ('zypper', None, ['sudo', 'zypper', 'install', '-y', 'ffmpeg']),
        ]
        
        for pm_name, update_cmd, install_cmd in package_managers:
            if shutil.which(pm_name):
                try:
                    if progress_callback:
                        progress_callback(f"使用 {pm_name}...", 20)
                    
                    # 更新包列表 (apt需要)
                    if update_cmd:
                        subprocess.run(update_cmd, capture_output=True, timeout=60)
                        if progress_callback:
                            progress_callback(f"更新完成", 50)
                    
                    # 安装
                    result = subprocess.run(
                        install_cmd,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        ffmpeg_path = shutil.which('ffmpeg')
                        if ffmpeg_path:
                            ConfigManager.save_ffmpeg_path(ffmpeg_path)
                        if progress_callback:
                            progress_callback(f"✅ FFmpeg 安装成功 ({pm_name})", 100)
                        return True
                except:
                    pass
        
        return False


class VideoDownloader:
    """视频下载核心引擎 - 增强版"""
    
    def __init__(self):
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 检查依赖
        self.dependencies = DependencyManager.check_all_dependencies()
        self.ffmpeg_info = self.dependencies.get('ffmpeg', {})
        self.ffmpeg_available = self.ffmpeg_info.get('installed', False)
        self.ffmpeg_path = self.ffmpeg_info.get('path')
        self.yt_dlp_available = self.dependencies.get('yt_dlp', {}).get('installed', False)
        
        # 支持的网站列表
        self.supported_sites = [
            "youtube.com", "youtu.be",
            "bilibili.com", "b23.tv",
            "douyin.com", "iesdouyin.com",
            "kuaishou.com",
            "weibo.com",
            "v.qq.com", "qq.com",
            "iqiyi.com",
            "youku.com",
            "tudou.com",
            "mgtv.com",
            "sohu.com",
            "56.com",
            "acfun.cn",
            "diliang.com",
            "miaopai.com",
            "xiaokaxiu.com",
            "pipipan.com",
            "tiktok.com",
            "instagram.com",
            "facebook.com",
            "twitter.com",
            "x.com"
        ]
        
        # 下载状态
        self.downloading = {}
        self.completed = {}
        self.failed = {}
    
    def set_ffmpeg_path(self, custom_path):
        """设置自定义FFmpeg路径并保存"""
        if custom_path and os.path.exists(custom_path):
            # 添加到检测器
            FFmpegDetector.add_custom_path(custom_path)
            # 保存到配置
            ConfigManager.save_ffmpeg_path(custom_path)
            # 重新检测FFmpeg
            self.dependencies = DependencyManager.check_all_dependencies()
            self.ffmpeg_info = self.dependencies.get('ffmpeg', {})
            self.ffmpeg_available = self.ffmpeg_info.get('installed', False)
            self.ffmpeg_path = self.ffmpeg_info.get('path')
            return True
        return False
    
    def get_dependency_status(self):
        """获取依赖状态"""
        return self.dependencies
    
    def check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        return self.ffmpeg_available
    
    def check_support(self, url):
        """检查URL是否支持"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            for site in self.supported_sites:
                if site in domain or site in url.lower():
                    return True
            return False
        except:
            return False
    
    def get_video_info(self, url):
        """获取视频信息"""
        if not self.yt_dlp_available:
            return {'error': 'yt-dlp未安装，请先安装依赖'}
        
        try:
            import yt_dlp
        except ImportError:
            return {'error': 'yt-dlp未安装，请先安装依赖'}
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'socket_timeout': 30,
                'ignoreerrors': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return {'error': '无法获取视频信息'}
                
                # 提取基本信息
                result = {
                    'title': info.get('title', '未知标题'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'uploader': info.get('uploader', '未知'),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', '')[:200],
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'formats': []
                }
                
                # 提取可用的格式
                formats = info.get('formats', [])
                seen_quality = set()
                for fmt in formats:
                    quality = fmt.get('format_note', '')
                    ext = fmt.get('ext', '')
                    if quality and ext:
                        quality_key = f"{quality}_{ext}"
                        if quality_key not in seen_quality:
                            seen_quality.add(quality_key)
                            result['formats'].append({
                                'format_id': fmt.get('format_id'),
                                'quality': quality,
                                'ext': ext,
                                'filesize': fmt.get('filesize', 0),
                                'acodec': fmt.get('acodec', ''),
                                'vcodec': fmt.get('vcodec', ''),
                                'format_note': fmt.get('format_note', '')
                            })
                
                return result
                
        except Exception as e:
            return {'error': f'获取信息失败: {str(e)}'}
    
    def download_video(self, url, quality='best', 
                      format_type='mp4', download_audio=False,
                      audio_format='mp3', callback=None, 
                      task_id=None):
        """下载视频"""
        if not self.yt_dlp_available:
            return {'error': 'yt-dlp未安装，请先安装依赖'}
        
        try:
            import yt_dlp
        except ImportError:
            return {'error': 'yt-dlp未安装，请先安装依赖'}
        
        try:
            # 构建下载选项
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'socket_timeout': 30,
                'retries': 10,
                'fragment_retries': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            }
            
            # 如果指定了FFmpeg路径，设置环境变量
            if self.ffmpeg_path:
                ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            
            # 设置输出模板
            output_template = os.path.join(self.download_dir, '%(title)s.%(ext)s')
            ydl_opts['outtmpl'] = output_template
            
            # 如果是仅下载音频
            if download_audio:
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '192',
                }]
                ydl_opts['extractaudio'] = True
                ydl_opts['audioformat'] = audio_format
            else:
                # 视频下载
                if self.ffmpeg_available:
                    # 有FFmpeg，下载最佳视频和音频并合并
                    if quality == 'best':
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    elif quality == '1080p':
                        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
                    elif quality == '720p':
                        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
                    elif quality == '480p':
                        ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
                    elif quality == '360p':
                        ydl_opts['format'] = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]'
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    
                    ydl_opts['merge_output_format'] = format_type
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': format_type,
                    }]
                else:
                    # 没有FFmpeg，下载单一格式
                    if quality == 'best':
                        ydl_opts['format'] = 'best[ext=mp4]/best'
                    else:
                        height = quality.replace('p', '')
                        ydl_opts['format'] = f'best[height<={height}][ext=mp4]/best'
            
            # 进度回调
            if callback:
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                        if total > 0:
                            progress = min((downloaded / total) * 100, 100)
                            speed = d.get('speed', 0)
                            if task_id:
                                callback(task_id, progress, speed, d.get('_percent_str', '0%'))
                    elif d['status'] == 'finished':
                        if task_id:
                            callback(task_id, 100, 0, '完成')
                    elif d['status'] == 'error':
                        if task_id:
                            callback(task_id, 0, 0, '错误')
                
                ydl_opts['progress_hooks'] = [progress_hook]
            
            # 开始下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    filename = ydl.prepare_filename(info)
                    
                    if not download_audio and self.ffmpeg_available:
                        merged_file = filename.rsplit('.', 1)[0] + f'.{format_type}'
                        if os.path.exists(merged_file):
                            filename = merged_file
                        elif not os.path.exists(filename):
                            for f in os.listdir(self.download_dir):
                                if info.get('title', '') in f and f.endswith(format_type):
                                    filename = os.path.join(self.download_dir, f)
                                    break
                    
                    return {
                        'success': True,
                        'filename': filename,
                        'title': info.get('title', '未知'),
                        'duration': info.get('duration', 0)
                    }
                else:
                    return {'error': '下载失败'}
                    
        except Exception as e:
            error_msg = str(e)
            if 'ffmpeg' in error_msg.lower() or 'merge' in error_msg.lower():
                error_msg += "\n\n提示: 请安装FFmpeg以支持音视频合并"
            return {'error': f'下载出错: {error_msg}'}


class VideoDownloaderGUI:
    """视频下载器界面 - 增强版"""
    
    def __init__(self, parent):
        self.parent = parent
        self.downloader = VideoDownloader()
        self.window = tk.Toplevel(parent)
        self.window.title("超级音视频下载器 v4.6")
        self.window.geometry("1200x1000")
        self.window.minsize(1000, 800)
        self.window.transient(parent)
        
        self.current_tasks = []
        self.task_progress = {}
        
        self.setup_ui()
        self.is_updating = True
        self.start_update_thread()
        
        # 加载保存的配置
        self.load_saved_config()
        
        # 自动检查依赖
        self.window.after(500, self.auto_check_dependencies)
    
    def load_saved_config(self):
        """加载保存的配置"""
        config = ConfigManager.load_config()
        
        # 设置FFmpeg路径
        saved_path = config.get('ffmpeg_path', '')
        if saved_path:
            self.ffmpeg_path_var.set(saved_path)
            # 如果路径有效，自动设置
            if os.path.exists(saved_path):
                self.downloader.set_ffmpeg_path(saved_path)
        
        # 设置下载选项
        quality = config.get('quality', 'best')
        if quality in ['best', '1080p', '720p', '480p', '360p']:
            self.quality_var.set(quality)
        
        format_type = config.get('format', 'mp4')
        if format_type in ['mp4', 'mkv', 'webm']:
            self.format_var.set(format_type)
        
        audio_format = config.get('audio_format', 'mp3')
        if audio_format in ['mp3', 'm4a', 'aac', 'flac', 'wav']:
            self.audio_format_var.set(audio_format)
        
        # 加载最近的URL（如果有）
        recent_urls = config.get('last_urls', [])
        if recent_urls:
            # 在URL输入框显示提示
            self.url_var.set(recent_urls[0])
    
    def save_current_config(self):
        """保存当前配置"""
        config = {
            'ffmpeg_path': self.ffmpeg_path_var.get(),
            'quality': self.quality_var.get(),
            'format': self.format_var.get(),
            'audio_format': self.audio_format_var.get(),
        }
        ConfigManager.save_config(config)
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== 依赖状态显示 ==========
        deps_frame = ttk.LabelFrame(main_frame, text="📦 依赖状态", padding="10")
        deps_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.deps_frame_inner = ttk.Frame(deps_frame)
        self.deps_frame_inner.pack(fill=tk.X)
        
        # 依赖标签会动态创建
        self.deps_labels = {}
        
        # ========== FFmpeg自定义路径 ==========
        ffmpeg_path_frame = ttk.Frame(deps_frame)
        ffmpeg_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ffmpeg_path_frame, text="FFmpeg路径:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.ffmpeg_path_var = tk.StringVar()
        ffmpeg_path_entry = ttk.Entry(ffmpeg_path_frame, textvariable=self.ffmpeg_path_var, width=50)
        ffmpeg_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(ffmpeg_path_frame, text="📂 浏览", command=self.browse_ffmpeg).pack(side=tk.LEFT, padx=2)
        ttk.Button(ffmpeg_path_frame, text="✅ 设置并记住", command=self.set_ffmpeg_path).pack(side=tk.LEFT, padx=2)
        ttk.Button(ffmpeg_path_frame, text="🔄 重新检测", command=self.manual_check_deps).pack(side=tk.LEFT, padx=2)
        ttk.Button(ffmpeg_path_frame, text="🗑 清除记住", command=self.clear_saved_ffmpeg).pack(side=tk.LEFT, padx=2)
        
        # ========== 顶部控制区域 ==========
        control_frame = ttk.LabelFrame(main_frame, text="📥 下载控制", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # URL输入
        url_frame = ttk.Frame(control_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="视频URL:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 10), width=60)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 按钮行
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="🔍 解析信息", command=self.parse_video).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 下载视频", command=self.download_video).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🎵 下载音频", command=self.download_audio).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 批量下载", command=self.batch_download).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🗑 清除完成", command=self.clear_completed).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 打开目录", command=self.open_download_dir).pack(side=tk.LEFT, padx=2)
        
        # 选项行
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_frame, text="画质:").pack(side=tk.LEFT, padx=5)
        self.quality_var = tk.StringVar(value='best')
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var,
                                    values=['best', '1080p', '720p', '480p', '360p'], width=8)
        quality_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="格式:").pack(side=tk.LEFT, padx=5)
        self.format_var = tk.StringVar(value='mp4')
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var,
                                   values=['mp4', 'mkv', 'webm'], width=8)
        format_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(options_frame, text="音频格式:").pack(side=tk.LEFT, padx=5)
        self.audio_format_var = tk.StringVar(value='mp3')
        audio_combo = ttk.Combobox(options_frame, textvariable=self.audio_format_var,
                                  values=['mp3', 'm4a', 'aac', 'flac', 'wav'], width=8)
        audio_combo.pack(side=tk.LEFT, padx=5)
        
        self.extract_audio_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="仅音频", variable=self.extract_audio_var).pack(side=tk.LEFT, padx=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(control_frame, textvariable=self.status_var, font=('Arial', 9)).pack(anchor=tk.W, pady=5)
        
        # ========== 依赖安装进度区域 ==========
        progress_frame = ttk.LabelFrame(main_frame, text="📦 依赖安装进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 状态文本（滚动显示）
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=4, font=('Consolas', 9))
        self.progress_text.pack(fill=tk.X, pady=5)
        
        # ========== 视频信息显示 ==========
        info_frame = ttk.LabelFrame(main_frame, text="📊 视频信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=5, font=('Arial', 9))
        self.info_text.pack(fill=tk.X)
        
        # ========== 下载任务列表 ==========
        task_frame = ttk.LabelFrame(main_frame, text="📋 下载任务", padding="10")
        task_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('状态', '标题', '进度', '速度', '大小', '格式', '操作')
        self.task_tree = ttk.Treeview(task_frame, columns=columns, show='headings', height=10)
        
        self.task_tree.heading('状态', text='状态')
        self.task_tree.heading('标题', text='标题')
        self.task_tree.heading('进度', text='进度')
        self.task_tree.heading('速度', text='速度')
        self.task_tree.heading('大小', text='大小')
        self.task_tree.heading('格式', text='格式')
        self.task_tree.heading('操作', text='操作')
        
        self.task_tree.column('状态', width=90, anchor='center')
        self.task_tree.column('标题', width=250)
        self.task_tree.column('进度', width=120, anchor='center')
        self.task_tree.column('速度', width=100, anchor='center')
        self.task_tree.column('大小', width=100, anchor='center')
        self.task_tree.column('格式', width=80, anchor='center')
        self.task_tree.column('操作', width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ========== 统计信息 ==========
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_labels = {}
        stats_names = ['总任务', '下载中', '已完成', '失败', '总大小']
        for i, name in enumerate(stats_names):
            frame = ttk.Frame(stats_frame)
            frame.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
            
            ttk.Label(frame, text=f"{name}:", font=('Arial', 9)).pack(side=tk.LEFT)
            self.stats_labels[name] = ttk.Label(frame, text="0", font=('Arial', 9, 'bold'))
            self.stats_labels[name].pack(side=tk.LEFT, padx=3)
        
        # 右键菜单
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="开始", command=self.start_task)
        self.context_menu.add_command(label="暂停", command=self.pause_task)
        self.context_menu.add_command(label="取消", command=self.cancel_task)
        self.context_menu.add_command(label="移除", command=self.remove_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="打开文件", command=self.open_file)
        self.context_menu.add_command(label="打开文件夹", command=self.open_file_location)
        self.task_tree.bind('<Button-3>', self.show_context_menu)
        self.task_tree.bind('<Double-Button-1>', self.open_file)
    
    def browse_ffmpeg(self):
        """浏览选择FFmpeg文件"""
        file_path = filedialog.askopenfilename(
            title="选择FFmpeg可执行文件",
            filetypes=[("FFmpeg", "ffmpeg.exe"), ("所有文件", "*.*")]
        )
        if file_path:
            self.ffmpeg_path_var.set(file_path)
            self.set_ffmpeg_path()
    
    def set_ffmpeg_path(self):
        """设置FFmpeg路径并保存"""
        path = self.ffmpeg_path_var.get().strip()
        if not path:
            messagebox.showwarning("提示", "请输入FFmpeg路径")
            return
        
        if not os.path.exists(path):
            messagebox.showerror("错误", "文件不存在，请检查路径")
            return
        
        if self.downloader.set_ffmpeg_path(path):
            # 保存配置
            self.save_current_config()
            self.status_var.set(f"✅ FFmpeg路径已设置并记住: {path}")
            self.update_dependency_display()
            messagebox.showinfo("成功", f"FFmpeg路径设置成功！\n\n路径: {path}\n\n已保存到配置文件，下次启动自动加载。")
        else:
            messagebox.showerror("错误", "设置FFmpeg路径失败")
    
    def clear_saved_ffmpeg(self):
        """清除保存的FFmpeg路径"""
        result = messagebox.askyesno("确认", "确定要清除保存的FFmpeg路径吗？")
        if result:
            ConfigManager.save_ffmpeg_path('')
            self.ffmpeg_path_var.set('')
            self.status_var.set("已清除保存的FFmpeg路径")
            # 重新检测
            self.manual_check_deps()
            messagebox.showinfo("成功", "已清除保存的FFmpeg路径")
    
    def auto_check_dependencies(self):
        """自动检查依赖"""
        self.status_var.set("正在检查依赖...")
        self.update_dependency_display()
    
    def manual_check_deps(self):
        """手动检查依赖"""
        self.status_var.set("正在重新检查依赖...")
        self.progress_text.insert(tk.END, "🔄 重新检查依赖...\n")
        self.progress_text.see(tk.END)
        
        def check_thread():
            def progress_callback(message, progress):
                self.window.after(0, lambda: self.update_progress(message, progress))
            
            self.downloader.dependencies = DependencyManager.check_all_dependencies(
                progress_callback=progress_callback
            )
            self.downloader.yt_dlp_available = self.downloader.dependencies.get('yt_dlp', {}).get('installed', False)
            self.downloader.ffmpeg_info = self.downloader.dependencies.get('ffmpeg', {})
            self.downloader.ffmpeg_available = self.downloader.ffmpeg_info.get('installed', False)
            self.downloader.ffmpeg_path = self.downloader.ffmpeg_info.get('path')
            
            # 更新路径显示
            if self.downloader.ffmpeg_path:
                self.ffmpeg_path_var.set(self.downloader.ffmpeg_path)
            
            self.window.after(0, self.update_dependency_display)
            self.window.after(0, lambda: self.status_var.set("✅ 依赖检查完成"))
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def update_dependency_display(self):
        """更新依赖显示"""
        # 清除旧标签
        for widget in self.deps_frame_inner.winfo_children():
            widget.destroy()
        
        deps = self.downloader.dependencies
        
        # 创建依赖状态标签
        for key, info in deps.items():
            frame = ttk.Frame(self.deps_frame_inner)
            frame.pack(side=tk.LEFT, padx=10, pady=2)
            
            status = "✅" if info.get('installed', False) else "❌"
            
            display = info.get('display_name', key)
            version = info.get('version', '未安装')
            error = info.get('error', '')
            
            label_text = f"{status} {display}"
            label = ttk.Label(frame, text=label_text, font=('Arial', 9))
            label.pack(anchor=tk.W)
            
            version_label = ttk.Label(frame, text=f"  版本: {version}", font=('Arial', 8), foreground='gray')
            version_label.pack(anchor=tk.W)
            
            # 显示FFmpeg路径
            if key == 'ffmpeg' and info.get('installed', False):
                path = info.get('path', '')
                if path:
                    path_label = ttk.Label(frame, text=f"  路径: {path}", font=('Arial', 8), foreground='blue')
                    path_label.pack(anchor=tk.W)
                
                # 显示FFmpeg功能
                features = info.get('features', {})
                if features:
                    feature_text = "  支持: " + ", ".join([k for k, v in features.items() if v])[:30]
                    feature_label = ttk.Label(frame, text=feature_text, font=('Arial', 8), foreground='green')
                    feature_label.pack(anchor=tk.W)
            
            if error and not info.get('installed', False):
                error_label = ttk.Label(frame, text=f"  错误: {error}", font=('Arial', 8), foreground='red')
                error_label.pack(anchor=tk.W)
            
            # 保存引用以便更新
            self.deps_labels[key] = frame
        
        # 添加安装按钮
        install_btn = ttk.Button(
            self.deps_frame_inner, 
            text="🔧 安装依赖",
            command=self.install_dependencies
        )
        install_btn.pack(side=tk.LEFT, padx=20, pady=5)
    
    def install_dependencies(self):
        """安装依赖"""
        result = messagebox.askyesno(
            "安装依赖",
            "将自动安装以下依赖：\n\n"
            "1. yt-dlp (视频下载核心)\n"
            "2. moviepy (视频处理)\n"
            "3. requests (网络请求)\n"
            "4. FFmpeg (音视频合并，可选)\n\n"
            "此过程可能需要几分钟，是否继续？"
        )
        
        if not result:
            return
        
        self.status_var.set("正在安装依赖...")
        self.progress_text.delete(1.0, tk.END)
        
        def install_thread():
            def progress_callback(message, progress):
                self.window.after(0, lambda: self.update_progress(message, progress))
            
            results = DependencyManager.install_dependencies(
                required_only=True,
                progress_callback=progress_callback
            )
            
            # 更新下载器状态
            self.downloader.dependencies = DependencyManager.check_all_dependencies()
            self.downloader.yt_dlp_available = self.downloader.dependencies.get('yt_dlp', {}).get('installed', False)
            self.downloader.ffmpeg_info = self.downloader.dependencies.get('ffmpeg', {})
            self.downloader.ffmpeg_available = self.downloader.ffmpeg_info.get('installed', False)
            self.downloader.ffmpeg_path = self.downloader.ffmpeg_info.get('path')
            
            # 更新路径显示
            if self.downloader.ffmpeg_path:
                self.ffmpeg_path_var.set(self.downloader.ffmpeg_path)
            
            self.window.after(0, self.update_dependency_display)
            self.window.after(0, lambda: self.status_var.set("✅ 依赖安装完成"))
            
            # 检查是否所有必需依赖都已安装
            all_installed = all(
                info.get('installed', False) 
                for key, info in self.downloader.dependencies.items()
                if key != 'ffmpeg'  # FFmpeg是可选的
            )
            
            if not all_installed:
                self.window.after(0, lambda: self.show_manual_install_guide())
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def update_progress(self, message, progress):
        """更新进度条和状态"""
        self.progress_bar['value'] = progress
        self.progress_text.insert(tk.END, f"{message}\n")
        self.progress_text.see(tk.END)
        self.window.update_idletasks()
    
    def show_manual_install_guide(self):
        """显示手动安装指南"""
        guide = """
📦 手动安装指南

1. yt-dlp (必需):
   pip install yt-dlp

2. moviepy (视频处理):
   pip install moviepy

3. requests (网络请求):
   pip install requests

4. FFmpeg (音视频合并，可选):
   Windows: winget install ffmpeg
   macOS: brew install ffmpeg  
   Linux: sudo apt install ffmpeg

一键安装所有依赖:
   pip install yt-dlp moviepy requests
"""
        self.info_text.insert(tk.END, guide + "\n")
        self.info_text.see(tk.END)
    
    def parse_video(self):
        """解析视频信息"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频URL")
            return
        
        if not self.downloader.yt_dlp_available:
            messagebox.showerror("错误", "yt-dlp未安装，请先安装依赖")
            return
        
        if not self.downloader.check_support(url):
            messagebox.showwarning("提示", 
                f"暂不支持该网站\n支持的网站: {', '.join(self.downloader.supported_sites[:10])}...")
            return
        
        self.status_var.set("正在获取视频信息...")
        self.info_text.delete(1.0, tk.END)
        
        def parse_thread():
            info = self.downloader.get_video_info(url)
            
            def update_info():
                if 'error' in info:
                    self.status_var.set(f"❌ {info['error']}")
                    self.info_text.insert(tk.END, f"错误: {info['error']}\n")
                    return
                
                self.info_text.insert(tk.END, f"📌 标题: {info.get('title', '未知')}\n")
                self.info_text.insert(tk.END, f"👤 上传者: {info.get('uploader', '未知')}\n")
                self.info_text.insert(tk.END, f"⏱ 时长: {self.format_duration(info.get('duration', 0))}\n")
                self.info_text.insert(tk.END, f"👁 观看: {info.get('view_count', 0):,}\n")
                self.info_text.insert(tk.END, f"👍 点赞: {info.get('like_count', 0):,}\n")
                self.info_text.insert(tk.END, f"📅 日期: {info.get('upload_date', '')}\n")
                
                self.info_text.insert(tk.END, f"\n🎬 可用格式:\n")
                for fmt in info.get('formats', [])[:10]:
                    quality = fmt.get('quality', '')
                    ext = fmt.get('ext', '')
                    size = fmt.get('filesize', 0)
                    size_str = self.format_size(size) if size > 0 else '未知'
                    self.info_text.insert(tk.END, f"  - {quality} ({ext}) {size_str}\n")
                
                self.status_var.set(f"✅ 解析完成: {info.get('title', '')[:50]}")
                self.info_text.see(tk.END)
            
            self.window.after(0, update_info)
        
        threading.Thread(target=parse_thread, daemon=True).start()
    
    def download_video(self):
        """下载视频"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入视频URL")
            return
        
        if not self.downloader.yt_dlp_available:
            messagebox.showerror("错误", "yt-dlp未安装，请先安装依赖")
            return
        
        if not self.downloader.check_support(url):
            messagebox.showwarning("提示", "暂不支持该网站")
            return
        
        quality = self.quality_var.get()
        format_type = self.format_var.get()
        download_audio = self.extract_audio_var.get()
        audio_format = self.audio_format_var.get()
        
        if not download_audio and not self.downloader.ffmpeg_available:
            result = messagebox.askyesno(
                "FFmpeg未安装",
                "⚠️ FFmpeg未安装，视频下载后音视频可能会分离！\n\n"
                "建议安装FFmpeg以自动合并音视频。\n\n"
                "是否继续下载？"
            )
            if not result:
                return
        
        # 保存URL到最近使用
        ConfigManager.add_recent_url(url)
        
        # 保存当前配置
        self.save_current_config()
        
        task_id = str(uuid.uuid4())[:8]
        self.task_progress[task_id] = {
            'id': task_id,
            'url': url,
            'status': 'downloading',
            'progress': 0,
            'speed': 0,
            'size': 0,
            'title': '获取中...',
            'format': format_type if not download_audio else audio_format
        }
        
        self.add_task_to_tree(task_id)
        self.status_var.set(f"开始下载: {url}")
        
        def download_thread():
            def progress_callback(tid, progress, speed, status):
                if tid in self.task_progress:
                    self.task_progress[tid]['progress'] = progress
                    self.task_progress[tid]['speed'] = speed
                    if status == '完成':
                        self.task_progress[tid]['status'] = 'completed'
                        self.window.after(0, lambda: self.status_var.set(f"✅ 下载完成: {self.task_progress[tid].get('title', '')}"))
            
            result = self.downloader.download_video(
                url, quality, format_type,
                download_audio, audio_format,
                progress_callback, task_id
            )
            
            if result.get('success'):
                self.task_progress[task_id]['status'] = 'completed'
                self.task_progress[task_id]['progress'] = 100
                self.task_progress[task_id]['title'] = result.get('title', '')
                self.task_progress[task_id]['filename'] = result.get('filename', '')
            else:
                self.task_progress[task_id]['status'] = 'failed'
                error = result.get('error', '未知错误')
                self.task_progress[task_id]['error'] = error
                self.window.after(0, lambda: self.status_var.set(f"❌ 下载失败: {error}"))
                self.window.after(0, lambda: messagebox.showerror("下载失败", error))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_audio(self):
        """下载音频"""
        self.extract_audio_var.set(True)
        self.download_video()
    
    def batch_download(self):
        """批量下载"""
        if not self.downloader.yt_dlp_available:
            messagebox.showerror("错误", "yt-dlp未安装，请先安装依赖")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("批量下载")
        dialog.geometry("600x450")
        dialog.transient(self.window)
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="每行一个URL").pack(anchor=tk.W, pady=5)
        
        text_area = scrolledtext.ScrolledText(frame, height=12, font=('Consolas', 10))
        text_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
        text_area.insert(tk.END, "# 示例：\n")
        text_area.insert(tk.END, "https://www.youtube.com/watch?v=xxx\n")
        text_area.insert(tk.END, "https://www.bilibili.com/video/xxx\n")
        
        def start_batch():
            content = text_area.get(1.0, tk.END).strip()
            if not content:
                messagebox.showwarning("提示", "请输入URL")
                return
            
            urls = [l.strip() for l in content.split('\n') 
                   if l.strip() and not l.startswith('#')]
            
            if not urls:
                messagebox.showwarning("提示", "没有有效的URL")
                return
            
            quality = self.quality_var.get()
            format_type = self.format_var.get()
            download_audio = self.extract_audio_var.get()
            audio_format = self.audio_format_var.get()
            
            dialog.destroy()
            
            self.status_var.set(f"开始批量下载 {len(urls)} 个文件...")
            
            def batch_thread():
                for i, url in enumerate(urls):
                    self.window.after(0, lambda u=url, idx=i: self.status_var.set(f"下载 [{idx+1}/{len(urls)}]: {u}"))
                    self.downloader.download_video(
                        url, quality, format_type,
                        download_audio, audio_format,
                        callback=None, task_id=None
                    )
                
                self.window.after(0, lambda: self.status_var.set("✅ 批量下载完成"))
            
            threading.Thread(target=batch_thread, daemon=True).start()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="开始批量下载", command=start_batch).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=2)
    
    def add_task_to_tree(self, task_id):
        """添加任务到树形列表"""
        task = self.task_progress[task_id]
        values = (
            '📥 下载中',
            task['title'],
            '0%',
            '0 KB/s',
            '未知',
            task['format'],
            '⏸ ❌'
        )
        self.task_tree.insert('', tk.END, values=values, tags=(task_id,))
    
    def clear_completed(self):
        """清除已完成"""
        for item in self.task_tree.get_children():
            tags = self.task_tree.item(item, 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    if self.task_progress[task_id]['status'] == 'completed':
                        self.task_tree.delete(item)
                        del self.task_progress[task_id]
    
    def open_download_dir(self):
        """打开下载目录"""
        if os.path.exists(self.downloader.download_dir):
            try:
                os.startfile(self.downloader.download_dir)
            except:
                pass
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def start_task(self):
        """开始任务"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    self.task_progress[task_id]['status'] = 'downloading'
                    self.status_var.set(f"恢复任务: {task_id}")
    
    def pause_task(self):
        """暂停任务"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    self.task_progress[task_id]['status'] = 'paused'
                    self.status_var.set(f"暂停任务: {task_id}")
    
    def cancel_task(self):
        """取消任务"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    self.task_progress[task_id]['status'] = 'cancelled'
                    self.task_tree.delete(selection[0])
                    self.status_var.set(f"取消任务: {task_id}")
    
    def remove_task(self):
        """移除任务"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    del self.task_progress[task_id]
                self.task_tree.delete(selection[0])
                self.status_var.set("已移除任务")
    
    def open_file(self):
        """打开文件"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    task = self.task_progress[task_id]
                    if task['status'] == 'completed' and 'filename' in task:
                        filename = task['filename']
                        if os.path.exists(filename):
                            try:
                                os.startfile(filename)
                            except:
                                pass
    
    def open_file_location(self):
        """打开文件位置"""
        selection = self.task_tree.selection()
        if selection:
            tags = self.task_tree.item(selection[0], 'tags')
            if tags:
                task_id = tags[0]
                if task_id in self.task_progress:
                    task = self.task_progress[task_id]
                    if 'filename' in task:
                        filepath = task['filename']
                        dirpath = os.path.dirname(filepath)
                        if os.path.exists(dirpath):
                            try:
                                os.startfile(dirpath)
                            except:
                                pass
        else:
            self.open_download_dir()
    
    def start_update_thread(self):
        """启动更新线程"""
        def update_loop():
            while self.is_updating:
                try:
                    self.window.after(0, self.update_task_list)
                except:
                    break
                time.sleep(0.5)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def update_task_list(self):
        """更新任务列表"""
        try:
            for item in self.task_tree.get_children():
                tags = self.task_tree.item(item, 'tags')
                if tags:
                    task_id = tags[0]
                    if task_id in self.task_progress:
                        task = self.task_progress[task_id]
                        
                        status_icons = {
                            'pending': '⏳ 等待',
                            'downloading': '📥 下载中',
                            'paused': '⏸ 暂停',
                            'completed': '✅ 完成',
                            'failed': '❌ 失败',
                            'cancelled': '🚫 取消'
                        }
                        
                        status_text = status_icons.get(task['status'], task['status'])
                        progress = task.get('progress', 0)
                        progress_text = f"{progress:.1f}%" if progress > 0 else "0%"
                        speed = task.get('speed', 0)
                        speed_text = self.format_size(speed) + "/s" if speed > 0 else "0 KB/s"
                        size = task.get('size', 0)
                        size_text = self.format_size(size) if size > 0 else "未知"
                        
                        self.task_tree.item(item, values=(
                            status_text,
                            task.get('title', '未知')[:50],
                            progress_text,
                            speed_text,
                            size_text,
                            task.get('format', ''),
                            '▶ ⏸ ❌'
                        ))
            
            # 更新统计
            total = len(self.task_progress)
            downloading = sum(1 for t in self.task_progress.values() if t['status'] == 'downloading')
            completed = sum(1 for t in self.task_progress.values() if t['status'] == 'completed')
            failed = sum(1 for t in self.task_progress.values() if t['status'] == 'failed')
            
            self.stats_labels['总任务'].config(text=str(total))
            self.stats_labels['下载中'].config(text=str(downloading))
            self.stats_labels['已完成'].config(text=str(completed))
            self.stats_labels['失败'].config(text=str(failed))
            
            total_size = sum(t.get('size', 0) for t in self.task_progress.values() if t['status'] == 'completed')
            self.stats_labels['总大小'].config(text=self.format_size(total_size))
            
        except Exception as e:
            pass
    
    def format_duration(self, seconds):
        """格式化时长"""
        if not seconds:
            return "00:00"
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def format_size(self, size):
        """格式化大小"""
        if size <= 0:
            return '0 B'
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"
    
    def on_close(self):
        """关闭窗口"""
        # 保存配置
        self.save_current_config()
        self.is_updating = False
        self.window.destroy()


class MainApp:
    """主应用 - 增强版"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("超级音视频下载器 v4.6")
        self.root.geometry("500x380")
        self.root.minsize(400, 300)
        
        main_frame = ttk.Frame(root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="🎬 超级音视频下载器 v4.6", 
                         font=('Arial', 18, 'bold'))
        title.pack(pady=10)
        
        subtitle = ttk.Label(main_frame, 
            text="支持 YouTube | B站 | 抖音 | 快手 | 微博 | 腾讯 | 爱奇艺 | 优酷 等", 
            font=('Arial', 9))
        subtitle.pack(pady=5)
        
        # 状态信息
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(pady=10)
        
        self.status_labels = {}
        deps = ['yt-dlp', 'moviepy', 'requests', 'FFmpeg']
        for dep in deps:
            label = ttk.Label(status_frame, text=f"⏳ {dep}: 检查中...")
            label.pack(pady=2)
            self.status_labels[dep] = label
        
        # 检查依赖
        def check_deps():
            results = DependencyManager.check_all_dependencies()
            
            for key, info in results.items():
                if key == 'ffmpeg':
                    dep_name = 'FFmpeg'
                else:
                    dep_name = key
                
                if dep_name in self.status_labels:
                    if info.get('installed', False):
                        version = info.get('version', '')
                        path = info.get('path', '')
                        if path:
                            self.status_labels[dep_name].config(
                                text=f"✅ {dep_name}: {version} ({path})",
                                foreground='green'
                            )
                        else:
                            self.status_labels[dep_name].config(
                                text=f"✅ {dep_name}: {version}",
                                foreground='green'
                            )
                    else:
                        self.status_labels[dep_name].config(
                            text=f"❌ {dep_name}: 未安装",
                            foreground='red'
                        )
        
        threading.Thread(target=check_deps, daemon=True).start()
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="🚀 打开下载器", 
                  command=self.open_downloader, width=20).pack(pady=3)
        
        ttk.Button(btn_frame, text="📂 打开下载目录", 
                  command=self.open_download_dir, width=20).pack(pady=3)
        
        ttk.Button(btn_frame, text="🔧 安装依赖 (带进度)", 
                  command=self.install_deps, width=20).pack(pady=3)
        
        ttk.Label(main_frame, text="v4.6 - 2024", 
                 font=('Arial', 8), foreground='gray').pack(side=tk.BOTTOM, pady=10)
    
    def open_downloader(self):
        """打开下载器"""
        downloader = VideoDownloaderGUI(self.root)
    
    def open_download_dir(self):
        """打开下载目录"""
        if os.path.exists('downloads'):
            try:
                os.startfile('downloads')
            except:
                pass
    
    def install_deps(self):
        """手动安装依赖（带进度）"""
        result = messagebox.askyesno(
            "安装依赖",
            "将自动安装以下依赖：\n\n"
            "1. yt-dlp (视频下载核心)\n"
            "2. moviepy (视频处理)\n"
            "3. requests (网络请求)\n"
            "4. FFmpeg (音视频合并，可选)\n\n"
            "此过程可能需要几分钟，是否继续？"
        )
        
        if result:
            downloader = VideoDownloaderGUI(self.root)
            downloader.install_dependencies()


def main():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()