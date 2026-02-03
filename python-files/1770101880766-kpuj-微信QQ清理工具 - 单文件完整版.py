#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信QQ清理工具 - 单文件完整版
直接复制此代码保存为 WeChatQQCleaner.py
然后使用在线工具打包为exe
"""

import os
import sys
import ctypes
import json
import time
import stat
from datetime import datetime, timedelta

class WeChatQQCleaner:
    def __init__(self):
        self.version = "2.1"
        self.is_admin = self.check_admin()
        self.setup()
        
    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def setup(self):
        # 创建工作目录
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.create_dir("logs")
        self.create_dir("reports")
        
        # 配置
        self.config = {
            'preserve_days': 7,
            'clean_ext': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', 
                         '.mp4', '.avi', '.mov', '.wmv',
                         '.tmp', '.temp', '.log', '.cache'],
            'target_folders': ['WeChat Files', 'Tencent Files', 'QQ', 
                              'xwechat_files', 'FileStorage', 'WeChatCache',
                              'QQTemp', 'QQDownload', 'ImageCache']
        }
        
        self.stats = {'cleaned': 0, 'size': 0, 'errors': 0}
    
    def create_dir(self, name):
        path = os.path.join(self.base_dir, name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def scan_system(self):
        found = []
        drives = ['C:', 'D:', 'E:', 'F:']
        
        for drive in drives:
            if os.path.exists(drive):
                # 用户目录
                users_path = os.path.join(drive, 'Users')
                if os.path.exists(users_path):
                    for user in os.listdir(users_path):
                        user_path = os.path.join(users_path, user)
                        if os.path.isdir(user_path):
                            self.scan_user(found, user_path)
        
        return found
    
    def scan_user(self, found, user_path):
        # 扫描Documents
        docs = os.path.join(user_path, 'Documents')
        if os.path.exists(docs):
            self.scan_folder(found, docs)
        
        # 扫描Desktop
        desktop = os.path.join(user_path, 'Desktop')
        if os.path.exists(desktop):
            self.scan_folder(found, desktop)
        
        # 扫描AppData
        for sub in ['Local', 'Roaming']:
            appdata = os.path.join(user_path, 'AppData', sub)
            if os.path.exists(appdata):
                self.scan_folder(found, appdata)
    
    def scan_folder(self, found, folder):
        try:
            for root, dirs, _ in os.walk(folder):
                for dir_name in dirs:
                    for target in self.config['target_folders']:
                        if target.lower() in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            if os.path.exists(full_path):
                                size = self.get_size(full_path)
                                found.append({
                                    'path': full_path,
                                    'size': size,
                                    'type': '微信' if 'wechat' in dir_name.lower() else 'QQ'
                                })
        except:
            pass
    
    def get_size(self, path):
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    try:
                        total += os.path.getsize(os.path.join(root, file))
                    except:
                        continue
        except:
            pass
        return total
    
    def clean_folder(self, folder_path, folder_type):
        cleaned = 0
        size = 0
        cutoff = datetime.now() - timedelta(days=self.config['preserve_days'])
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # 检查扩展名
                        ext = os.path.splitext(file)[1].lower()
                        if ext in self.config['clean_ext']:
                            # 检查修改时间
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if mtime < cutoff:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned += 1
                                size += file_size
                    except:
                        continue
        except:
            pass
        
        return cleaned, size
    
    def show_banner(self):
        print("=" * 60)
        print("       微信QQ清理工具 v{}".format(self.version))
        print("=" * 60)
        print("功能：自动清理微信QQ缓存文件")
        print("特点：保留{}天内文件，只删缓存不删记录".format(self.config['preserve_days']))
        if not self.is_admin:
            print("提示：建议以管理员身份运行（右键->以管理员身份运行）")
        print("=" * 60)
    
    def run(self):
        self.show_banner()
        
        input("按回车键开始扫描（或按Ctrl+C取消）...")
        
        print("\n正在扫描系统，请稍候...")
        print("正在查找微信QQ缓存文件夹...")
        
        found = self.scan_system()
        
        if not found:
            print("\n✅ 未发现需要清理的缓存文件夹")
            input("\n按回车键退出...")
            return
        
        # 显示结果
        print(f"\n📊 发现 {len(found)} 个缓存文件夹：")
        total_size = sum(f['size'] for f in found)
        print(f"总大小: {self.format_size(total_size)}")
        
        for i, f in enumerate(found, 1):
            print(f"{i}. {f['type']}: {f['path']}")
            print(f"   大小: {self.format_size(f['size'])}")
        
        # 确认清理
        print("\n" + "=" * 60)
        print("注意：将清理7天前的图片、视频、临时文件等缓存")
        print("不会删除聊天记录等重要数据")
        print("=" * 60)
        
        choice = input("\n是否开始清理？(y/n): ").lower()
        if choice != 'y':
            print("清理已取消")
            return
        
        # 执行清理
        print("\n🧹 开始清理...")
        print("=" * 60)
        
        for f in found:
            print(f"清理 {f['type']}...")
            cleaned, size = self.clean_folder(f['path'], f['type'])
            if cleaned > 0:
                self.stats['cleaned'] += cleaned
                self.stats['size'] += size
                print(f"  已清理 {cleaned} 个文件，释放 {self.format_size(size)}")
            else:
                print("  无需清理")
        
        # 显示结果
        print("\n" + "=" * 60)
        print("清理完成！")
        print("=" * 60)
        
        if self.stats['cleaned'] > 0:
            print(f"✅ 总共清理: {self.stats['cleaned']} 个文件")
            print(f"💾 释放空间: {self.format_size(self.stats['size'])}")
        else:
            print("📝 没有需要清理的缓存文件")
        
        print("\n💡 提示：建议每月清理一次以保持系统流畅")
        print("=" * 60)
        
        input("\n按回车键退出...")

def main():
    try:
        app = WeChatQQCleaner()
        app.run()
    except KeyboardInterrupt:
        print("\n\n程序已取消")
    except Exception as e:
        print(f"\n错误：{e}")
        input("\n按回车键退出...")

if __name__ == "__main__":
    # 设置控制台编码为UTF-8
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    
    main()