import os
import sys
import shutil
import time
import platform
import pickle
from pathlib import Path
import threading
import queue
import tempfile
import ctypes
from datetime import datetime, timedelta

class InteractiveDiskCleaner:
    def __init__(self):
        """初始化交互式磁盘清理器"""
        self.system = platform.system()
        self.config_file = "cleaner_config.dat"
        self.is_new_user = True
        self.scanned_items = []
        self.total_scanned = 0
        self.scan_queue = queue.Queue()
        self.scan_complete = False
        self.current_drive = ""
        self.load_config()
        
    def load_config(self):
        """加载用户配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'rb') as f:
                    config = pickle.load(f)
                    self.is_new_user = config.get('is_new_user', True)
        except Exception:
            self.is_new_user = True
    
    def save_config(self):
        """保存用户配置"""
        try:
            config = {'is_new_user': self.is_new_user}
            with open(self.config_file, 'wb') as f:
                pickle.dump(config, f)
        except Exception:
            pass
    
    def show_welcome(self):
        """显示欢迎界面"""
        print("=" * 70)
        print("              智能磁盘清理工具 v3.1")
        print("=" * 70)
        print("\n💡 注意: 本工具可以帮助您安全清理磁盘空间")
        print("    在删除任何文件前都会让您确认")
        print("    您可以随时取消操作")
        
        if self.is_new_user:
            print("\n⚠️  您是第一次使用本工具")
            print("   这个工具可以帮您清理不必要的临时文件")
            print("   但如果您不确定如何使用，可能会有些复杂")
            
            while True:
                response = input("\n您是新手用户吗？(y/n, 输入q退出): ").strip().lower()
                
                if response == 'q':
                    print("程序退出")
                    return False
                elif response == 'y':
                    print("\n由于此操作对新手可能有些复杂")
                    print("如果您需要帮助，可以联系:")
                    print("📧 邮箱: asdfghjkl088769@outlook.com")
                    print("📱 QQ: 3988950698")
                    print("\n您也可以在网上搜索教程学习使用")
                    
                    proceed = input("\n是否继续？(y/n): ").strip().lower()
                    if proceed == 'y':
                        self.is_new_user = False
                        self.save_config()
                        return True
                    else:
                        return False
                elif response == 'n':
                    self.is_new_user = False
                    self.save_config()
                    return True
                else:
                    print("请输入 y, n 或 q")
        else:
            return True
    
    def get_available_drives(self):
        """获取可用磁盘驱动器"""
        drives = []
        
        if self.system == "Windows":
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ["/"]
        
        return drives
    
    def select_drive(self):
        """选择要清理的磁盘"""
        drives = self.get_available_drives()
        
        if not drives:
            print("❌ 未找到可用磁盘")
            return None
        
        print("\n请选择要清理的磁盘:")
        print("-" * 60)
        
        for i, drive in enumerate(drives, 1):
            try:
                total, used, free = shutil.disk_usage(drive)
                used_percent = (used / total) * 100
                free_gb = free / (1024**3)
                total_gb = total / (1024**3)
                used_gb = used / (1024**3)
                
                # 创建使用情况进度条
                bar_length = 20  # 进度条长度
                filled_length = int(bar_length * used_percent / 100)
                empty_length = bar_length - filled_length
                
                # 使用"#"表示已用空间，" "表示可用空间
                used_bar = "#" * filled_length
                free_bar = " " * empty_length
                bar = f"[{used_bar}{free_bar}]"
                
                # 显示磁盘信息和使用情况进度条
                print(f"{i}. {drive}")
                print(f"   总空间: {total_gb:.1f}GB | 已用: {used_gb:.1f}GB ({used_percent:.1f}%) | 可用: {free_gb:.1f}GB")
                print(f"   使用情况: {bar} {used_percent:.1f}%")
                
            except Exception:
                print(f"{i}. {drive} - 无法获取磁盘信息")
            print()  # 空行分隔
        
        print("0. 退出程序")
        print("-" * 60)
        
        while True:
            try:
                choice = input("\n请输入选择 (0-{}): ".format(len(drives))).strip()
                
                if choice == '0':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(drives):
                    return drives[idx]
                else:
                    print("❌ 无效的选择，请重新输入")
            except ValueError:
                print("❌ 请输入数字")
            except KeyboardInterrupt:
                return None
    
    def scan_worker(self, drive_path):
        """扫描工作线程"""
        temp_extensions = ['.tmp', '.temp', '.log', '.cache', '.bak', '.~']
        temp_keywords = ['temp', 'tmp', 'cache', 'log', '回收站']
        cutoff_time = time.time() - (30 * 24 * 3600)  # 30天前
        
        try:
            for root, dirs, files in os.walk(drive_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查是否临时文件
                    is_temp = any(file.lower().endswith(ext) for ext in temp_extensions)
                    is_temp = is_temp or any(keyword in file.lower() for keyword in temp_keywords)
                    
                    if is_temp:
                        try:
                            file_size = os.path.getsize(file_path)
                            file_mtime = os.path.getmtime(file_path)
                            is_old = file_mtime < cutoff_time
                            
                            item = {
                                'path': file_path,
                                'size': file_size,
                                'mtime': file_mtime,
                                'is_old': is_old,
                                'type': '临时文件'
                            }
                            
                            self.scan_queue.put(('item', item))
                        except Exception:
                            pass
                    
                    # 发送进度更新
                    self.total_scanned += 1
                    if self.total_scanned % 100 == 0:  # 每100个文件更新一次进度
                        self.scan_queue.put(('progress', self.total_scanned))
                
        except Exception as e:
            self.scan_queue.put(('error', str(e)))
        
        self.scan_queue.put(('complete', None))
    
    def show_progress_bar(self, duration=0.5):
        """显示进度条（去掉数字的版本）"""
        print("\n🔄 正在扫描磁盘，请稍候...")
        print("[" + " " * 50 + "]", end='')
        
        start_time = time.time()
        last_update = start_time
        dots = 0
        bar_position = 0
        direction = 1  # 1表示向右，-1表示向左
        
        while not self.scan_complete:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # 控制更新频率
            if current_time - last_update >= duration:
                # 创建动态进度效果
                bar_length = 50
                
                # 让进度条来回移动
                bar_position = bar_position + direction
                if bar_position >= bar_length - 3 or bar_position <= 0:
                    direction = -direction
                
                # 创建进度条
                bar = [" "] * bar_length
                for i in range(max(0, bar_position-2), min(bar_length, bar_position+3)):
                    if 0 <= i < bar_length:
                        bar[i] = "="
                
                bar_str = "".join(bar)
                
                # 添加动态点
                dots = (dots + 1) % 4
                spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[dots % 10]
                
                # 只显示进度条和动画，不显示数字
                print(f"\r[{bar_str}] {spinner} 扫描中...", end='', flush=True)
                last_update = current_time
            
            time.sleep(0.1)
        
        # 扫描完成后显示完成状态
        print(f"\r[{'=' * 50}] ✅ 扫描完成！")
    
    def scan_drive(self, drive_path):
        """扫描磁盘"""
        print(f"\n开始扫描磁盘: {drive_path}")
        print("=" * 60)
        
        # 重置扫描数据
        self.scanned_items = []
        self.total_scanned = 0
        self.scan_complete = False
        self.current_drive = drive_path
        
        # 启动扫描线程
        scan_thread = threading.Thread(target=self.scan_worker, args=(drive_path,))
        scan_thread.daemon = True
        scan_thread.start()
        
        # 显示进度条
        progress_thread = threading.Thread(target=self.show_progress_bar)
        progress_thread.start()
        
        # 处理扫描结果
        try:
            while True:
                try:
                    msg_type, data = self.scan_queue.get(timeout=0.1)
                    
                    if msg_type == 'item':
                        self.scanned_items.append(data)
                    elif msg_type == 'progress':
                        pass  # 进度更新已经在进度条中处理
                    elif msg_type == 'error':
                        print(f"\n⚠️ 扫描过程中出错: {data}")
                    elif msg_type == 'complete':
                        break
                        
                except queue.Empty:
                    if not scan_thread.is_alive():
                        break
                    continue
                    
        except KeyboardInterrupt:
            print("\n\n⚠️ 扫描被用户中断")
            return False
        
        self.scan_complete = True
        progress_thread.join()
        
        return True
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def show_scan_results(self):
        """显示扫描结果"""
        if not self.scanned_items:
            print("\n🎉 恭喜！没有找到可以清理的临时文件")
            return False
        
        print(f"\n扫描完成！共找到 {len(self.scanned_items)} 个可清理的文件")
        print("=" * 60)
        
        total_size = sum(item['size'] for item in self.scanned_items)
        old_files = sum(1 for item in self.scanned_items if item['is_old'])
        
        print(f"总大小: {self.format_size(total_size)}")
        print(f"30天前的文件: {old_files} 个")
        print(f"临时文件: {len(self.scanned_items)} 个")
        print("=" * 60)
        
        return True
    
    def show_full_path_list(self):
        """显示完整的文件路径列表"""
        if not self.scanned_items:
            print("没有可显示的文件")
            return
        
        print(f"\n完整的文件路径列表 (共 {len(self.scanned_items)} 个):")
        print("=" * 100)
        
        for i, item in enumerate(self.scanned_items, 1):
            size_str = self.format_size(item['size'])
            file_type = item['type']
            print(f"{i:4d}. [{size_str:>8}] [{file_type:>4}] {item['path']}")
        
        print("=" * 100)
    
    def preview_file(self, file_path):
        """预览文件"""
        try:
            if os.path.getsize(file_path) > 1024 * 1024:  # 大于1MB不预览
                print("文件太大，无法预览完整内容")
                return False
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # 只读取前1000字符
                
            print(f"\n文件内容预览 ({len(content)} 字符):")
            print("-" * 60)
            print(content)
            if len(content) >= 1000:
                print("... (内容截断)")
            print("-" * 60)
            return True
            
        except Exception as e:
            print(f"无法预览文件: {e}")
            return False
    
    def open_file_location(self, file_path):
        """打开文件所在位置"""
        try:
            if self.system == "Windows":
                folder_path = os.path.dirname(file_path)
                os.startfile(folder_path)
                return True
            else:
                print(f"文件位置: {os.path.dirname(file_path)}")
                return True
        except Exception as e:
            print(f"无法打开文件位置: {e}")
            return False
    
    def delete_file(self, file_path):
        """安全删除文件"""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                return True, self.format_size(file_size)
        except PermissionError:
            return False, "文件正在被使用"
        except Exception as e:
            return False, str(e)
        return False, "未知错误"
    
    def interactive_delete_menu(self):
        """交互式删除菜单"""
        if not self.scanned_items:
            return
        
        while True:
            print("\n请选择操作:")
            print("1. 查看完整文件路径列表")
            print("2. 全选并删除 (A)")
            print("3. 按编号选择删除")
            print("4. 预览文件内容")
            print("5. 打开文件位置")
            print("X. 返回主菜单")
            print("0. 退出扫描")
            print("-" * 50)
            
            choice = input("\n请选择操作 (0-5,X): ").strip().upper()
            
            if choice == '0':
                print("退出扫描")
                return
            elif choice == 'X':
                print("返回主菜单")
                return 'main'
            
            elif choice == '1':
                # 显示完整文件列表
                self.show_full_path_list()
                
                # 等待用户输入返回
                while True:
                    back_choice = input("\n输入 'X' 返回操作菜单: ").strip().upper()
                    if back_choice == 'X':
                        break
                    else:
                        print("请输入 'X' 返回")
            
            elif choice == '2' or choice == 'A':
                # 全选删除
                confirm = input(f"\n⚠️  确认要删除所有 {len(self.scanned_items)} 个文件吗？(y/n): ").strip().lower()
                if confirm == 'y':
                    deleted_count = 0
                    deleted_size = 0
                    failed_count = 0
                    
                    print(f"\n开始删除 {len(self.scanned_items)} 个文件...")
                    
                    for i, item in enumerate(self.scanned_items, 1):
                        success, result = self.delete_file(item['path'])
                        if success:
                            deleted_count += 1
                            deleted_size += item['size']
                            print(f"✓ [{i}/{len(self.scanned_items)}] 删除: {item['path']}")
                        else:
                            failed_count += 1
                            print(f"✗ [{i}/{len(self.scanned_items)}] 失败: {item['path']} - {result}")
                    
                    print(f"\n删除完成！")
                    print(f"成功: {deleted_count} 个文件")
                    print(f"失败: {failed_count} 个文件")
                    print(f"释放空间: {self.format_size(deleted_size)}")
                    
                    # 删除完成后清空列表
                    if deleted_count > 0:
                        self.scanned_items = [item for item in self.scanned_items 
                                            if not os.path.exists(item['path'])]
                else:
                    print("删除操作已取消")
            
            elif choice == '3':
                # 按编号选择删除
                if not self.scanned_items:
                    print("没有可删除的文件")
                    continue
                
                # 先显示前20个文件让用户参考
                self.show_full_path_list()
                
                print("\n输入要删除的文件编号 (多个编号用逗号分隔，如: 1,3,5)")
                print("输入 'X' 返回操作菜单")
                print("输入 '0' 取消")
                
                try:
                    selection = input("\n请输入编号: ").strip().upper()
                    
                    if selection == 'X':
                        continue
                    elif selection == '0':
                        print("操作已取消")
                        continue
                    
                    # 解析输入
                    indexes = []
                    for part in selection.split(','):
                        part = part.strip()
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            indexes.extend(range(start, end + 1))
                        else:
                            indexes.append(int(part))
                    
                    indexes = sorted(set(indexes))
                    valid_indexes = [i for i in indexes if 1 <= i <= len(self.scanned_items)]
                    
                    if not valid_indexes:
                        print("❌ 没有有效的编号")
                        continue
                    
                    # 显示要删除的文件
                    print(f"\n将要删除 {len(valid_indexes)} 个文件:")
                    for idx in valid_indexes[:20]:  # 只显示前20个
                        item = self.scanned_items[idx-1]
                        print(f"  {idx}. {item['path']} ({self.format_size(item['size'])})")
                    
                    if len(valid_indexes) > 20:
                        print(f"  ... 还有 {len(valid_indexes) - 20} 个文件")
                    
                    confirm = input(f"\n确认删除这 {len(valid_indexes)} 个文件吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        deleted_count = 0
                        deleted_size = 0
                        
                        for idx in valid_indexes:
                            item = self.scanned_items[idx-1]
                            success, result = self.delete_file(item['path'])
                            if success:
                                deleted_count += 1
                                deleted_size += item['size']
                                print(f"✓ 删除 [{idx}]: {item['path']}")
                            else:
                                print(f"✗ 失败 [{idx}]: {item['path']} - {result}")
                        
                        print(f"\n删除完成！成功删除 {deleted_count} 个文件")
                        print(f"释放空间: {self.format_size(deleted_size)}")
                        
                        # 从列表中移除已删除的文件
                        self.scanned_items = [item for i, item in enumerate(self.scanned_items, 1) 
                                            if i not in valid_indexes or os.path.exists(item['path'])]
                    else:
                        print("删除操作已取消")
                        
                except ValueError:
                    print("❌ 输入格式不正确")
                except Exception as e:
                    print(f"❌ 发生错误: {e}")
            
            elif choice == '4':
                # 预览文件
                if not self.scanned_items:
                    print("没有可预览的文件")
                    continue
                
                # 先显示前20个文件
                self.show_full_path_list()
                
                print("\n输入要预览的文件编号")
                print("输入 'X' 返回操作菜单")
                
                try:
                    selection = input("\n请输入文件编号: ").strip().upper()
                    
                    if selection == 'X':
                        continue
                    
                    idx = int(selection)
                    if 1 <= idx <= len(self.scanned_items):
                        item = self.scanned_items[idx-1]
                        self.preview_file(item['path'])
                    else:
                        print("❌ 编号无效")
                except ValueError:
                    print("❌ 请输入数字")
            
            elif choice == '5':
                # 打开文件位置
                if not self.scanned_items:
                    print("没有文件")
                    continue
                
                # 先显示前20个文件
                self.show_full_path_list()
                
                print("\n输入要打开位置的文件编号")
                print("输入 'X' 返回操作菜单")
                
                try:
                    selection = input("\n请输入文件编号: ").strip().upper()
                    
                    if selection == 'X':
                        continue
                    
                    idx = int(selection)
                    if 1 <= idx <= len(self.scanned_items):
                        item = self.scanned_items[idx-1]
                        if self.open_file_location(item['path']):
                            print("✓ 已打开文件所在位置")
                    else:
                        print("❌ 编号无效")
                except ValueError:
                    print("❌ 请输入数字")
            
            else:
                print("❌ 无效的选择")
    
    def show_rating(self):
        """显示评分界面"""
        print("\n" + "=" * 60)
        print("           感谢您使用智能磁盘清理工具！")
        print("=" * 60)
        
        print("\n您的使用体验对我们非常重要")
        print("请为我们的工具打个分（1-10分）：")
        print("⭐" * 20)
        
        while True:
            try:
                rating = input("请输入评分 (1-10, 输入0跳过): ").strip()
                
                if rating == '0':
                    print("感谢您的使用！")
                    break
                
                rating_num = int(rating)
                if 1 <= rating_num <= 10:
                    stars = "⭐" * rating_num
                    print(f"\n感谢您的 {rating_num} 分评价！{stars}")
                    print("我们会继续改进，为您提供更好的服务！")
                    break
                else:
                    print("❌ 评分必须在 1-10 之间")
            except ValueError:
                print("❌ 请输入数字")
        
        print("\n👋 再见！欢迎再次使用智能磁盘清理工具")
        print("=" * 60)
    
    def main(self):
        """主程序"""
        if not self.show_welcome():
            return
        
        print("\n欢迎使用智能磁盘清理工具！")
        
        while True:
            # 选择磁盘
            drive = self.select_drive()
            if drive is None:
                break
            
            # 扫描磁盘
            if not self.scan_drive(drive):
                continue
            
            # 显示扫描结果
            if not self.show_scan_results():
                continue
            
            # 交互式删除菜单
            result = self.interactive_delete_menu()
            if result == 'main':
                continue
            
            # 询问是否继续清理其他磁盘
            cont = input("\n是否继续清理其他磁盘？(y/n): ").strip().lower()
            if cont != 'y':
                break
        
        # 显示评分
        self.show_rating()

def main():
    """程序入口"""
    try:
        # 设置控制台编码
        if platform.system() == "Windows":
            os.system("chcp 65001 >nul")
        
        cleaner = InteractiveDiskCleaner()
        cleaner.main()
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"程序发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()